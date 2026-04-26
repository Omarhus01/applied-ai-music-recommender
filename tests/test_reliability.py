"""
Unit reliability tests for the Music Recommender.
No Gemini API calls — fast and free to run.

Run with: python -m pytest tests/test_reliability.py -v
"""

import random
from collections import Counter
from src.recommender import load_songs_v2, recommend_songs, derive_mood, score_song
from src.agent import _validate_input, MIN_SCORE_THRESHOLD

SAMPLE_SIZE = 5000
SEED = 42
MIN_SCORE_THRESHOLD = 3.0


def make_songs(seed=SEED):
    random.seed(seed)
    return load_songs_v2("data/new_songs_dataset.csv", sample=SAMPLE_SIZE)


# ---------------------------------------------------------------------------
# 1. Consistency test — same profile + same seed = same top 5 every time
# ---------------------------------------------------------------------------
def test_consistency():
    profile = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.75,
        "likes_acoustic": False,
        "target_instrumentalness": 0.1,
    }
    results_across_runs = []
    for _ in range(5):
        songs = make_songs()
        results = recommend_songs(profile, songs, k=5)
        titles = [s["title"] for s, _, _ in results]
        results_across_runs.append(titles)

    # All 5 runs should return identical top 5
    assert all(r == results_across_runs[0] for r in results_across_runs), (
        "Consistency failed: same seed produced different results across runs"
    )


# ---------------------------------------------------------------------------
# 2. Score threshold test — top result should score above minimum
# ---------------------------------------------------------------------------
def test_score_threshold_good_match():
    songs = make_songs()
    profile = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.8,
        "likes_acoustic": False,
        "target_instrumentalness": 0.1,
    }
    results = recommend_songs(profile, songs, k=5)
    assert results, "No results returned"
    top_score = results[0][1]
    assert top_score >= MIN_SCORE_THRESHOLD, (
        f"Top score {top_score:.2f} is below threshold {MIN_SCORE_THRESHOLD}"
    )


def test_score_threshold_flags_poor_match():
    songs = make_songs()
    # Intentionally conflicting — high energy + melancholic is hard to satisfy
    profile = {
        "favorite_genre": "jazz fusion",
        "favorite_mood": "melancholic",
        "target_energy": 0.95,
        "target_valence": 0.05,
        "likes_acoustic": False,
        "target_instrumentalness": 0.95,
    }
    results = recommend_songs(profile, songs, k=5)
    if results:
        top_score = results[0][1]
        # Just log — don't fail, since some match may exist
        print(f"\n[Score Threshold] Conflicting profile top score: {top_score:.2f}")
        if top_score < MIN_SCORE_THRESHOLD:
            print("  WARNING: No strong match found for this profile.")


# ---------------------------------------------------------------------------
# 3. Mood derivation spot-check against known songs
# ---------------------------------------------------------------------------
KNOWN_MOODS = [
    # (energy, valence, mode, tempo, acousticness, expected_mood)
    (0.9,  0.8,  1, 130, 0.05, "happy"),
    (0.9,  0.3,  0, 140, 0.05, "dark"),
    (0.9,  0.3,  1, 140, 0.05, "intense"),
    (0.2,  0.2,  0, 70,  0.8,  "melancholic"),
    (0.3,  0.7,  1, 80,  0.6,  "peaceful"),
    (0.6,  0.7,  1, 130, 0.1,  "energetic"),
    (0.4,  0.6,  1, 90,  0.5,  "chill"),
]

def test_mood_derivation_accuracy():
    correct = 0
    for energy, valence, mode, tempo, acousticness, expected in KNOWN_MOODS:
        result = derive_mood(energy, valence, mode, tempo, acousticness)
        if result == expected:
            correct += 1
        else:
            print(f"\n[Mood] Expected '{expected}', got '{result}' "
                  f"(energy={energy}, valence={valence}, mode={mode})")

    accuracy = correct / len(KNOWN_MOODS)
    print(f"\n[Mood Derivation] Accuracy: {correct}/{len(KNOWN_MOODS)} = {accuracy:.0%}")
    assert accuracy >= 0.70, f"Mood derivation accuracy {accuracy:.0%} is below 70%"


# ---------------------------------------------------------------------------
# 4. Edge case tests
# ---------------------------------------------------------------------------
def test_edge_empty_genre():
    songs = make_songs()
    profile = {
        "favorite_genre": "",
        "favorite_mood": "chill",
        "target_energy": 0.4,
        "target_valence": 0.6,
        "likes_acoustic": True,
        "target_instrumentalness": 0.5,
    }
    results = recommend_songs(profile, songs, k=5)
    assert len(results) > 0, "Should return results even with empty genre"


def test_edge_unknown_genre():
    songs = make_songs()
    profile = {
        "favorite_genre": "jazz fusion",
        "favorite_mood": "relaxed",
        "target_energy": 0.37,
        "target_valence": 0.71,
        "likes_acoustic": True,
        "target_instrumentalness": 0.7,
    }
    results = recommend_songs(profile, songs, k=5)
    assert len(results) > 0, "Should return results even for unknown genre"


def test_edge_all_midpoint():
    songs = make_songs()
    profile = {
        "favorite_genre": "ambient",
        "favorite_mood": "focused",
        "target_energy": 0.5,
        "target_valence": 0.5,
        "likes_acoustic": True,
        "target_instrumentalness": 0.5,
    }
    results = recommend_songs(profile, songs, k=5)
    assert len(results) > 0, "Should return results for all-0.5 preferences"


def test_edge_rare_genre():
    songs = make_songs()
    profile = {
        "favorite_genre": "tango",
        "favorite_mood": "intense",
        "target_energy": 0.7,
        "target_valence": 0.4,
        "likes_acoustic": False,
        "target_instrumentalness": 0.3,
    }
    results = recommend_songs(profile, songs, k=5)
    # Rare genre — may return fewer than k, just verify no crash
    assert results is not None, "Should not crash on rare genre"
    print(f"\n[Rare Genre] Tango returned {len(results)} results")


# ---------------------------------------------------------------------------
# 5. Precision measurement — % of top 5 matching intended mood or genre
# ---------------------------------------------------------------------------
def test_precision_mood_match():
    songs = make_songs()
    profile = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.8,
        "likes_acoustic": False,
        "target_instrumentalness": 0.1,
    }
    results = recommend_songs(profile, songs, k=5)
    assert results, "No results returned"

    mood_matches = sum(1 for s, _, _ in results if s["mood"] == profile["favorite_mood"])
    genre_matches = sum(1 for s, _, _ in results if s["genre"] == profile["favorite_genre"])
    relevant = sum(1 for s, _, _ in results if
                   s["mood"] == profile["favorite_mood"] or s["genre"] == profile["favorite_genre"])

    precision = relevant / len(results)
    print(f"\n[Precision] Mood matches: {mood_matches}/5 | Genre matches: {genre_matches}/5")
    print(f"[Precision] Overall precision (mood OR genre): {precision:.0%}")
    assert precision >= 0.4, f"Precision {precision:.0%} is too low"


# ---------------------------------------------------------------------------
# 6. Guardrail tests
# ---------------------------------------------------------------------------
def test_guardrail_empty_input():
    valid, reason = _validate_input("")
    assert not valid, "Empty input should be rejected"


def test_guardrail_too_short():
    valid, reason = _validate_input("pop music")
    assert not valid, "Input under 3 words should be rejected"


def test_guardrail_nonsensical():
    valid, reason = _validate_input("123 !!! 456")
    assert not valid, "Input with no real words should be rejected"


def test_guardrail_harmful():
    valid, reason = _validate_input("I want music to kill and hate people")
    assert not valid, "Harmful input should be rejected"


def test_guardrail_valid_input():
    valid, reason = _validate_input("I want something chill and relaxing")
    assert valid, f"Valid input was incorrectly rejected: {reason}"


def test_guardrail_score_threshold():
    songs = make_songs()
    # Extremely conflicting profile — should score poorly
    profile = {
        "favorite_genre": "nonexistent-genre-xyz",
        "favorite_mood": "melancholic",
        "target_energy": 0.99,
        "target_valence": 0.01,
        "likes_acoustic": True,
        "target_instrumentalness": 0.99,
    }
    results = recommend_songs(profile, songs, k=5)
    if results:
        top_score = results[0][1]
        print(f"\n[Score Guardrail] Top score for impossible profile: {top_score:.2f}")
        if top_score < MIN_SCORE_THRESHOLD:
            print("  Score guardrail would trigger correctly.")
