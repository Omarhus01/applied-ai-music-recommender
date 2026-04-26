# Applied AI Music Recommender

This project started as a simple music recommender from Module 3 — you give it your preferences, it scores every song and returns the top 5. That version worked, but it was rigid. You had to fill in exact fields like favorite genre and target energy as numbers. There was no real AI involved, just math.

This upgrade turns it into something that actually feels like a system you'd want to use. You describe what you want in plain English, and the system figures out the rest.

---

## System Architecture

### Before — Module 3 (Simple Recommender)

![System Before](assets/system-before.png)

### After — Applied AI Upgrade

![System After](assets/system-after.png)

### Where AI Results Are Checked

The system has three explicit checkpoints where AI output is verified — not just generated:

1. **Gemini Quality Check** — after the recommender returns results, Gemini re-reads the user's original request and the top 3 songs and judges whether they actually match. If not, it triggers a retry with relaxed constraints.
2. **Score Guardrail** — after all retries, if the top result still scores below 3.0 / 6.5, the system warns the user explicitly instead of presenting weak results as if they were good.
3. **Test Suite (21 tests)** — the reliability and integration tests verify that the system behaves correctly across edge cases, guardrail inputs, and full end-to-end flows. This is where a human (the developer) checks AI behavior systematically, not just by running it once.

---

## What It Does Now

You type something like:

```
I want something chill and relaxing to study to
```

The system understands that, finds songs that match, explains why each one was recommended in plain language, and if the results aren't good enough, it tries again with adjusted preferences — all automatically.

---

## What Was Added and Why

### 1. Real Dataset — 114,000 Spotify Tracks

The original dataset had 50 hand-crafted songs. That's enough to test logic but not enough to feel like a real system. We replaced it with a real Spotify dataset from Kaggle containing 114,000 tracks across 125 genres.

One problem: the new dataset has no mood column. Mood had to be derived from the audio features using the **circumplex model of affect** — a psychology model that maps valence (how positive a song sounds) and energy (how intense it is) to mood labels like happy, chill, intense, or melancholic. Mode (major vs minor key), tempo, and acousticness are used as refiners.

### 2. Agentic Workflow — The System Thinks for Itself

Instead of filling in a form, you just describe what you want. Gemini reads your request and converts it into a structured profile with genre, mood, energy target, and other preferences.

After the recommender runs, Gemini checks if the results actually match what you asked for. If they don't, the system automatically relaxes the constraints and tries again — up to 3 times. On the first retry it widens the energy range. On the second it drops the genre requirement entirely. If it still can't find a strong match after 3 tries, it tells you honestly and returns the best it found.

This loop — plan, act, check, adjust — is what makes it agentic.

### 3. RAG Explanation Layer — Grounded in Real Data

The original system explained recommendations using raw score numbers like `mood match (+1.0) | energy closeness (+1.77)`. That's accurate but not human-friendly.

The RAG layer fixes this. For each recommended song, the system retrieves the song's actual audio features (energy, valence, mood, genre, acousticness, instrumentalness) and passes them to Gemini along with what the user originally asked for. Gemini uses that retrieved data as context to write a real explanation — something like:

> "This song was recommended because its chill mood and high instrumentalness of 0.85 make it ideal for focused studying, and its low energy of 0.31 matches your preference for something relaxed."

The key word is **grounded** — Gemini isn't guessing or hallucinating. It's explaining based on the actual numbers retrieved from the dataset.

### 4. Guardrails — The System Knows Its Limits

Four guardrails were added to prevent the system from behaving badly:

- **Input guardrail** — rejects empty input, input with no real words (like `"123 !!!"`) and harmful content before anything reaches Gemini
- **Output guardrail** — if Gemini returns a malformed profile (broken JSON or missing fields), the system catches it and uses safe defaults instead of crashing
- **Execution guardrail** — the retry loop is hard-capped at 3 iterations so it can never run forever
- **Score guardrail** — if the top result scores below 3.0 out of 6.5, the system warns you that no strong match was found rather than pretending the results are good

### 5. Reliability and Testing — 19 Tests

The system is tested at two levels:

**Unit tests** (fast, no API calls):
- Consistency: same seed always returns the same results
- Score threshold: good profiles score above minimum, bad ones are flagged
- Mood derivation accuracy: spot-checked against known song types
- Edge cases: empty genre, unknown genre, all-0.5 preferences, rare genres
- Precision: at least 40% of top 5 results match the intended mood or genre
- Guardrail validation: harmful, empty, and nonsensical inputs are correctly rejected

**Integration tests** (use real Gemini API):
- Agent retry: conflicting input triggers the retry loop without crashing
- RAG fallback: if Gemini fails, explanations fall back to score-based text gracefully
- Full end-to-end: user types a request, agent runs, results come back well-formed

---

## How to Run It

### Prerequisites

- Python 3.10 or higher
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Installation

```bash
# Clone the repo
git clone https://github.com/Omarhus01/applied-ai-music-recommender.git
cd applied-ai-music-recommender

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac / Linux

# Install dependencies
pip install -r requirements.txt

# Create your .env file (use Python to avoid encoding issues on Windows)
python -c "open('.env','w',encoding='utf-8').write('GEMINI_API_KEY=your_key_here\n')"
```

### Run the System

```bash
python -m src.main
```

Type what you're in the mood for and hit Enter. Type `quit` to exit.

### Run Tests

Unit tests only (no API needed):
```bash
python -m pytest tests/test_recommender.py tests/test_reliability.py -v
```

Integration tests (requires Gemini API):
```bash
python -m pytest tests/test_integration.py -v
```

All tests:
```bash
python -m pytest tests/ -v
```

---

## Project Structure

```
├── assets/
│   ├── system-before.png       # Architecture diagram — Module 3 version
│   └── system-after.png        # Architecture diagram — upgraded version
├── data/
│   ├── songs.csv               # Original 50-song dataset (Module 3)
│   └── new_songs_dataset.csv   # Spotify 114k dataset (this version)
├── logs/                       # Auto-generated logs from each run
├── src/
│   ├── agent.py                # Agentic workflow, RAG, and guardrails
│   ├── main.py                 # Entry point — conversational interface
│   └── recommender.py          # Core scoring, loading, and mood derivation
├── tests/
│   ├── test_recommender.py     # Original Module 3 unit tests
│   ├── test_reliability.py     # Reliability and guardrail tests
│   └── test_integration.py     # End-to-end integration tests
├── APPLIED_AI_README.md        # This file
├── README.md                   # Original Module 3 README
├── model_card.md               # Model card for the upgraded system
└── reflection.md               # Personal reflection
```

---

## Known Limitations

- Mood labels are approximations derived from audio features, not verified by humans. The circumplex model has about 70-80% accuracy on spot-checks.
- Genre representation in the Spotify dataset is uneven. Rare genres like tango or jazz fusion may return fewer than 5 results.
- The system targets precision over recall by design — it would rather return 3 strong matches than 5 weak ones.
- Each request makes 2-3 Gemini API calls, adding roughly 5-10 seconds of latency.
- The system uses a 10,000-song sample during development. Switch to the full 114k dataset for production by removing the `sample` parameter in `main.py`.

See `model_card.md` for the full breakdown of biases and ethical considerations.
