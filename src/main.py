"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs_v2
from src.agent import run_agent
from tabulate import tabulate


PROFILES = [
    ("High-Energy Pop", {
        "favorite_genre":          "pop",
        "favorite_mood":           "happy",
        "target_energy":           0.90,
        "target_valence":          0.80,
        "likes_acoustic":          False,
        "target_instrumentalness": 0.05,
    }),
    ("Chill Lofi", {
        "favorite_genre":          "lofi",
        "favorite_mood":           "chill",
        "target_energy":           0.38,
        "target_valence":          0.58,
        "likes_acoustic":          True,
        "target_instrumentalness": 0.50,
    }),
    ("Deep Intense Rock", {
        "favorite_genre":          "rock",
        "favorite_mood":           "intense",
        "target_energy":           0.91,
        "target_valence":          0.48,
        "likes_acoustic":          False,
        "target_instrumentalness": 0.04,
    }),
    # --- Adversarial profiles ---
    ("Conflicting: High Energy + Melancholic", {
        "favorite_genre":          "soul pop",
        "favorite_mood":           "melancholic",
        "target_energy":           0.90,
        "target_valence":          0.20,
        "likes_acoustic":          False,
        "target_instrumentalness": 0.05,
    }),
    ("Missing Genre: Jazz Fusion", {
        "favorite_genre":          "jazz fusion",
        "favorite_mood":           "relaxed",
        "target_energy":           0.37,
        "target_valence":          0.71,
        "likes_acoustic":          True,
        "target_instrumentalness": 0.70,
    }),
    ("Wants Instrumental but Likes Pop", {
        "favorite_genre":          "pop",
        "favorite_mood":           "happy",
        "target_energy":           0.80,
        "target_valence":          0.80,
        "likes_acoustic":          False,
        "target_instrumentalness": 0.95,
    }),
    ("Dead Center: All 0.5", {
        "favorite_genre":          "ambient",
        "favorite_mood":           "focused",
        "target_energy":           0.50,
        "target_valence":          0.50,
        "likes_acoustic":          True,
        "target_instrumentalness": 0.50,
    }),
]


def print_recommendations(profile_name: str, recommendations: list) -> None:
    """Prints a formatted table of recommendations for a given profile."""
    print("\n" + "=" * 60)
    print(f"  Profile: {profile_name}")
    print("=" * 60 + "\n")

    table_rows = []
    reasons_rows = []

    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        table_rows.append([
            f"#{i}",
            song["title"],
            song["artist"],
            song["genre"],
            song["mood"],
            f"{score:.2f} / 6.5",
        ])
        reasons_rows.append((f"#{i} {song['title']}", explanation))

    print(tabulate(
        table_rows,
        headers=["Rank", "Title", "Artist", "Genre", "Mood", "Score"],
        tablefmt="outline"
    ))

    print("\n" + "-" * 60)
    print("  Why each song was recommended:")
    print("-" * 60)
    for title, reason in reasons_rows:
        print(f"\n{title}")
        print(f"  {reason}")


def main() -> None:
    print("Loading songs dataset...")
    songs = load_songs_v2("data/new_songs_dataset.csv")
    print(f"Loaded {len(songs)} songs.\n")

    print("=" * 60)
    print("  MUSIC RECOMMENDER — Conversational Mode")
    print("=" * 60)
    print("Describe what kind of music you want and I'll find it for you.")
    print("Type 'quit' to exit.\n")

    while True:
        user_input = input("What are you in the mood for? ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        results = run_agent(user_input, songs, k=5)
        if results:
            print_recommendations("Your Recommendations", results)

        print()


if __name__ == "__main__":
    main()
