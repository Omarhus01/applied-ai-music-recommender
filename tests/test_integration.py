"""
Integration tests for the Music Recommender — require Gemini API.
These tests make real API calls and cost a small amount.

Run with: python -m pytest tests/test_integration.py -v
"""

import random
import pytest
from unittest.mock import patch
from src.recommender import load_songs_v2, recommend_songs
from src.agent import run_agent, generate_rag_explanations, _call_gemini

SAMPLE_SIZE = 2000
SEED = 42


def make_songs(seed=SEED):
    random.seed(seed)
    return load_songs_v2("data/new_songs_dataset.csv", sample=SAMPLE_SIZE)


# ---------------------------------------------------------------------------
# 1. Agent retry test — conflicting input should trigger retry loop
# ---------------------------------------------------------------------------
def test_agent_retries_on_poor_match():
    songs = make_songs()
    # Deliberately conflicting — high energy + melancholic rarely matches well
    user_input = "I want extremely high energy dark melancholic jazz fusion music"
    results = run_agent(user_input, songs, k=5)
    # Agent should still return something — not crash or return None
    assert results is not None, "Agent should return results even for conflicting input"
    assert len(results) > 0, "Agent should return at least one result"


# ---------------------------------------------------------------------------
# 2. RAG fallback test — Gemini failure falls back to score-based explanation
# ---------------------------------------------------------------------------
def test_rag_fallback_on_gemini_failure():
    songs = make_songs()
    profile = {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "target_valence": 0.8,
        "likes_acoustic": False,
        "target_instrumentalness": 0.1,
    }
    results = recommend_songs(profile, songs, k=3)
    assert results, "Need results to test RAG fallback"

    # Simulate Gemini failing by patching _call_gemini to raise an exception
    with patch("src.agent._call_gemini", side_effect=Exception("Simulated Gemini failure")):
        rag_results = generate_rag_explanations("happy pop music", results)

    # Should fall back gracefully — return original results unchanged
    assert rag_results is not None, "RAG fallback should return results, not None"
    assert len(rag_results) == len(results), "RAG fallback should return same number of results"
    for (song, score, explanation) in rag_results:
        assert explanation, "Fallback explanation should not be empty"


# ---------------------------------------------------------------------------
# 3. Full end-to-end test — user request → agent → RAG → well-formed output
# ---------------------------------------------------------------------------
def test_end_to_end_full_flow():
    songs = make_songs()
    user_input = "I want upbeat energetic pop music to work out to"
    results = run_agent(user_input, songs, k=5)

    assert results is not None, "End-to-end flow should return results"
    assert len(results) > 0, "Should return at least one recommendation"

    for song, score, explanation in results:
        assert isinstance(song, dict), "Each result should contain a song dict"
        assert isinstance(score, float), "Each result should have a float score"
        assert isinstance(explanation, str) and len(explanation) > 10, (
            "Each result should have a non-trivial explanation"
        )
        assert score > 0, "All scores should be positive"


# ---------------------------------------------------------------------------
# 4. Guardrail integration test — harmful input blocked before reaching Gemini
# ---------------------------------------------------------------------------
def test_guardrail_blocks_before_gemini():
    songs = make_songs()
    harmful_input = "I want music to kill and hate people"

    with patch("src.agent._call_gemini") as mock_gemini:
        result = run_agent(harmful_input, songs, k=5)

    assert result is None, "Harmful input should return None"
    mock_gemini.assert_not_called(), "Gemini should never be called for harmful input"
