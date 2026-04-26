import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from dotenv import load_dotenv
from google import genai

from src.recommender import load_songs_v2, recommend_songs

load_dotenv()

# --- Logging setup ---
os.makedirs("logs", exist_ok=True)
log_file = f"logs/agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
    ],
)
logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

DEFAULTS = {
    "favorite_genre": "",
    "favorite_mood": "",
    "target_energy": 0.5,
    "target_valence": 0.5,
    "likes_acoustic": False,
    "target_instrumentalness": 0.1,
}

MIN_SCORE_THRESHOLD = 3.0

HARMFUL_KEYWORDS = [
    "kill", "murder", "suicide", "hate", "abuse", "rape", "bomb", "terrorist"
]


def _validate_input(user_input: str) -> tuple[bool, str]:
    """
    Input guardrail. Returns (is_valid, reason).
    Checks: empty, too short, nonsensical (no real words), harmful content.
    """
    if not user_input or not user_input.strip():
        return False, "Input is empty."

    words = user_input.strip().split()
    if len(words) < 3:
        return False, "Please describe what you're looking for in a bit more detail (at least 3 words)."

    # Nonsense check — if fewer than 2 words contain actual letters, reject
    real_words = [w for w in words if any(c.isalpha() for c in w)]
    if len(real_words) < 2:
        return False, "I couldn't understand that. Please describe the music you want in plain words."

    # Harmful content check
    lower = user_input.lower()
    for keyword in HARMFUL_KEYWORDS:
        if keyword in lower:
            return False, "I can only help with music recommendations. Please keep your request music-related."

    return True, ""


def _call_gemini(prompt: str) -> str:
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()


def _parse_profile(user_input: str) -> Dict:
    """Ask Gemini to parse user text into a structured UserProfile dict."""
    prompt = f"""
You are a music preference parser. Given a user's request, extract their music preferences.
Return ONLY a valid JSON object with these exact keys:
- favorite_genre (string, e.g. "pop", "rock", "lofi", "jazz" — use common Spotify genre names, or empty string if unclear)
- favorite_mood (string, one of: happy, chill, intense, melancholic, energetic, peaceful, dark — or empty string if unclear)
- target_energy (float 0.0-1.0, how energetic they want the music)
- target_valence (float 0.0-1.0, how positive/upbeat they want it)
- likes_acoustic (boolean)
- target_instrumentalness (float 0.0-1.0, how instrumental vs vocal)
- confidence (string: "high" if you're confident, "low" if guessing)

User request: "{user_input}"

Return only the JSON, no explanation.
"""
    logger.info(f"Parsing user input: {user_input}")
    raw = _call_gemini(prompt)

    # Strip markdown code fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw)
        logger.info(f"Parsed profile: {parsed}")
        return parsed
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse Gemini response as JSON: {raw}")
        return {}


def _check_quality(user_input: str, results: List[Tuple]) -> str:
    """Ask Gemini if the results match the user's intent. Returns 'good' or 'retry'."""
    songs_summary = "\n".join(
        f"- {song['title']} by {song['artist']} | genre: {song['genre']} | mood: {song['mood']} | energy: {song['energy']:.2f}"
        for song, _, _ in results[:3]
    )
    prompt = f"""
A user asked for music with this request: "{user_input}"

The recommender returned these top songs:
{songs_summary}

Do these results match what the user asked for? Reply with ONLY one word: "good" or "retry".
"""
    logger.info("Checking result quality with Gemini")
    answer = _call_gemini(prompt).lower()
    logger.info(f"Quality check result: {answer}")
    return "good" if "good" in answer else "retry"


def _relax_profile(profile: Dict, attempt: int) -> Dict:
    """Relax constraints on each retry attempt."""
    relaxed = profile.copy()
    if attempt == 1:
        # Widen energy range by adjusting target toward middle
        current = relaxed.get("target_energy", 0.5)
        relaxed["target_energy"] = current * 0.7 + 0.5 * 0.3
        logger.info(f"Retry {attempt}: relaxed energy to {relaxed['target_energy']:.2f}")
    elif attempt == 2:
        # Drop genre requirement
        relaxed["favorite_genre"] = ""
        logger.info(f"Retry {attempt}: dropped genre requirement")
    return relaxed


def generate_rag_explanations(user_input: str, results: List[Tuple]) -> List[Tuple]:
    """
    RAG explanation layer:
    - Retrieves each song's actual feature data (the grounding context)
    - Passes user request + all songs' features to Gemini in one call
    - Returns results with Gemini-generated natural language explanations
    - Falls back to score-based explanation if Gemini fails
    """
    songs_context = ""
    for i, (song, score, fallback_explanation) in enumerate(results, start=1):
        songs_context += f"""
Song {i}: {song['title']} by {song['artist']}
  Genre: {song['genre']} | Mood: {song['mood']}
  Energy: {song['energy']:.2f} | Valence: {song['valence']:.2f}
  Acousticness: {song['acousticness']:.2f} | Instrumentalness: {song['instrumentalness']:.2f}
  Score: {score:.2f}
"""

    prompt = f"""
A user asked for music with this request: "{user_input}"

Here are the top recommended songs with their audio features:
{songs_context}

For each song, write a single natural sentence explaining why it was recommended based on its features and the user's request.
Be specific — mention actual feature values when relevant (e.g. energy, mood, genre).
Return ONLY a JSON array of {len(results)} strings, one explanation per song, in order.
Example format: ["Explanation for song 1.", "Explanation for song 2.", ...]
"""

    logger.info("Generating RAG explanations for recommendations")
    try:
        raw = _call_gemini(prompt)
        raw = raw.replace("```json", "").replace("```", "").strip()
        explanations = json.loads(raw)
        if isinstance(explanations, list) and len(explanations) == len(results):
            logger.info("RAG explanations generated successfully")
            return [
                (song, score, explanations[i])
                for i, (song, score, _) in enumerate(results)
            ]
    except Exception as e:
        logger.warning(f"RAG explanation failed, using fallback: {e}")

    return results


def _step(tag: str, message: str) -> None:
    """Print an observable reasoning step to the user."""
    print(f"  {tag:<22} {message}")


def run_agent(user_input: str, songs: List[Dict], k: int = 5) -> Optional[List[Tuple]]:
    """
    Main agentic loop with observable intermediate steps:
    1. Validate input
    2. Parse into UserProfile
    3. Ask follow-up if critical fields missing
    4. Run recommender
    5. Check quality, retry up to 3 times
    6. Generate RAG explanations
    """
    # --- Input guardrail ---
    is_valid, reason = _validate_input(user_input)
    if not is_valid:
        print(f"\n{reason}")
        logger.warning(f"Input rejected: '{user_input}' — {reason}")
        return None

    logger.info(f"Agent started with input: '{user_input}'")
    print()

    # --- Parse profile ---
    profile = _parse_profile(user_input)
    if not profile:
        print("\nSorry, I couldn't understand your request. Try describing the mood or genre you want.")
        return None

    confidence = profile.get("confidence", "unknown")
    genre = profile.get("favorite_genre") or "(none)"
    mood = profile.get("favorite_mood") or "(none)"
    energy = profile.get("target_energy", 0.5)
    instrumentalness = profile.get("target_instrumentalness", 0.1)
    _step("[Step 1 — Parse]", f"Confidence: {confidence} | Genre: {genre} | Mood: {mood} | Energy: {energy:.2f} | Instrumentalness: {instrumentalness:.2f}")

    # --- Follow-up if critical fields missing ---
    if not profile.get("favorite_genre") and not profile.get("favorite_mood"):
        _step("[Step 1 — Follow-up]", "Confidence too low — asking for clarification...")
        followup = input("\nCould you tell me the genre or mood you're looking for? (e.g. 'rock' or 'chill'): ").strip()
        logger.info(f"Follow-up answer: '{followup}'")
        extra = _parse_profile(followup)
        if extra.get("favorite_genre"):
            profile["favorite_genre"] = extra["favorite_genre"]
        if extra.get("favorite_mood"):
            profile["favorite_mood"] = extra["favorite_mood"]
        genre = profile.get("favorite_genre") or "(none)"
        mood = profile.get("favorite_mood") or "(none)"
        _step("[Step 1 — Parse]", f"Updated | Genre: {genre} | Mood: {mood}")

    # Fill in defaults for missing fields
    for key, default in DEFAULTS.items():
        if key not in profile or profile[key] == "" and key not in ("favorite_genre", "favorite_mood"):
            profile.setdefault(key, default)

    # --- Agentic retry loop ---
    best_results = None
    for attempt in range(3):
        logger.info(f"Attempt {attempt + 1} with profile: {profile}")
        results = recommend_songs(profile, songs, k=k, mode="default")

        if not results:
            logger.warning("No results returned")
            profile = _relax_profile(profile, attempt)
            continue

        if best_results is None:
            best_results = results

        top_score = results[0][1] if results else 0.0
        _step("[Step 2 — Retrieve]", f"Scored {len(songs):,} songs | Top result: {top_score:.2f} / 6.5")

        quality = _check_quality(user_input, results)
        if quality == "good":
            logger.info(f"Good results found on attempt {attempt + 1}")
            _step("[Step 3 — Evaluate]", f"Attempt {attempt + 1} → GOOD")
            _step("[Step 4 — Explain]", f"Generating grounded explanations via RAG ({k} songs)")
            final = generate_rag_explanations(user_input, results)
            _score_guardrail(final)
            print()
            return final

        logger.info(f"Results not satisfactory on attempt {attempt + 1}, retrying...")
        best_results = results

        if attempt == 0:
            relaxed_energy = profile.get("target_energy", 0.5) * 0.7 + 0.5 * 0.3
            _step("[Step 3 — Evaluate]", f"Attempt {attempt + 1} → RETRY (quality check failed)")
            _step("[Step 3 — Evaluate]", f"Relaxing: widening energy range to {relaxed_energy:.2f}")
        elif attempt == 1:
            _step("[Step 3 — Evaluate]", f"Attempt {attempt + 1} → RETRY (quality check failed)")
            _step("[Step 3 — Evaluate]", "Relaxing: dropping genre requirement")
        else:
            _step("[Step 3 — Evaluate]", f"Attempt {attempt + 1} → RETRY (quality check failed)")

        profile = _relax_profile(profile, attempt)

    logger.info("Max retries reached, returning best results found")
    _step("[Step 3 — Evaluate]", "Max attempts reached — returning best results found")
    _step("[Step 4 — Explain]", f"Generating grounded explanations via RAG ({k} songs)")
    print("\nI couldn't find a perfect match, but here's the closest I found:")
    final = generate_rag_explanations(user_input, best_results)
    _score_guardrail(final)
    print()
    return final


def _score_guardrail(results: Optional[List[Tuple]]) -> None:
    """Warn the user if the top result scores below the minimum threshold."""
    if not results:
        return
    top_score = results[0][1]
    if top_score < MIN_SCORE_THRESHOLD:
        print(f"\n⚠ Warning: The best match found scored {top_score:.2f} / 6.5, "
              f"which is below our quality threshold ({MIN_SCORE_THRESHOLD}). "
              f"Try being more specific about genre or mood.")
        logger.warning(f"Score guardrail triggered: top score {top_score:.2f} below threshold {MIN_SCORE_THRESHOLD}")
