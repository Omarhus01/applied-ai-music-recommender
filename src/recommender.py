from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    instrumentalness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.5
    target_instrumentalness: float = 0.1

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _song_to_dict(self, song: Song) -> Dict:
        return {
            "id":               song.id,
            "title":            song.title,
            "artist":           song.artist,
            "genre":            song.genre,
            "mood":             song.mood,
            "energy":           song.energy,
            "tempo_bpm":        song.tempo_bpm,
            "valence":          song.valence,
            "danceability":     song.danceability,
            "acousticness":     song.acousticness,
            "instrumentalness": song.instrumentalness,
        }

    def _user_to_dict(self, user: UserProfile) -> Dict:
        return {
            "favorite_genre":          user.favorite_genre,
            "favorite_mood":           user.favorite_mood,
            "target_energy":           user.target_energy,
            "target_valence":          user.target_valence,
            "likes_acoustic":          user.likes_acoustic,
            "target_instrumentalness": user.target_instrumentalness,
        }

    def recommend(self, user: UserProfile, k: int = 5, mode: str = "default") -> List[Song]:
        """Returns the top k songs sorted by score for the given user profile."""
        user_dict = self._user_to_dict(user)
        song_dicts = [self._song_to_dict(s) for s in self.songs]
        results = recommend_songs(user_dict, song_dicts, k=k, mode=mode)
        return [Song(**song) for song, _, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns a one-sentence plain-language explanation of why a song was recommended."""
        parts = []

        if song.genre == user.favorite_genre:
            parts.append(f"it matches your {user.favorite_genre} genre preference")

        if song.mood == user.favorite_mood:
            parts.append(f"has your target {user.favorite_mood} mood")

        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.1:
            parts.append(f"closely matches your energy target ({song.energy:.2f} vs {user.target_energy:.2f})")

        valence_diff = abs(song.valence - user.target_valence)
        if valence_diff <= 0.15:
            parts.append(f"aligns with your valence preference ({song.valence:.2f})")

        if user.likes_acoustic and song.acousticness >= 0.5:
            parts.append("has the acoustic quality you like")
        elif not user.likes_acoustic and song.acousticness < 0.3:
            parts.append("fits your preference for non-acoustic sound")

        if not parts:
            parts.append(f"was the closest match available for your preferences")

        return f"{song.title} by {song.artist} was recommended because " + ", and ".join(parts) + "."

def load_songs(csv_path: str) -> List[Dict]:
    """Loads songs from a CSV file and returns them as a list of dicts with correct types."""
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":               int(row["id"]),
                "title":            row["title"],
                "artist":           row["artist"],
                "genre":            row["genre"],
                "mood":             row["mood"],
                "energy":           float(row["energy"]),
                "tempo_bpm":        float(row["tempo_bpm"]),
                "valence":          float(row["valence"]),
                "danceability":     float(row["danceability"]),
                "acousticness":     float(row["acousticness"]),
                "instrumentalness": float(row["instrumentalness"]),
            })
    return songs

SCORING_MODES = {
    "default": {
        "genre":           1.0,
        "mood":            1.0,
        "energy":          2.0,
        "valence":         0.5,
        "acousticness":    0.5,
        "instrumentalness": 0.5,
    },
    "genre-first": {
        "genre":           3.0,
        "mood":            1.0,
        "energy":          1.0,
        "valence":         0.5,
        "acousticness":    0.5,
        "instrumentalness": 0.5,
    },
    "mood-first": {
        "genre":           1.0,
        "mood":            3.0,
        "energy":          1.0,
        "valence":         1.0,
        "acousticness":    0.5,
        "instrumentalness": 0.5,
    },
    "energy-first": {
        "genre":           1.0,
        "mood":            1.0,
        "energy":          4.0,
        "valence":         0.5,
        "acousticness":    0.5,
        "instrumentalness": 0.5,
    },
}


def score_song(user_prefs: Dict, song: Dict, mode: str = "default") -> Tuple[float, str]:
    """Scores a single song against user preferences and returns (score, explanation)."""
    weights = SCORING_MODES.get(mode, SCORING_MODES["default"])
    score = 0.0
    reasons = []

    # Genre match
    if song["genre"] == user_prefs["favorite_genre"]:
        score += weights["genre"]
        reasons.append(f"genre match (+{weights['genre']})")

    # Mood match
    if song["mood"] == user_prefs["favorite_mood"]:
        score += weights["mood"]
        reasons.append(f"mood match (+{weights['mood']})")

    # Energy closeness
    energy_score = weights["energy"] * (1 - abs(song["energy"] - user_prefs["target_energy"]))
    score += energy_score
    reasons.append(f"energy closeness (+{energy_score:.2f})")

    # Valence closeness
    valence_score = weights["valence"] * (1 - abs(song["valence"] - user_prefs["target_valence"]))
    score += valence_score
    reasons.append(f"valence closeness (+{valence_score:.2f})")

    # Acousticness
    if user_prefs["likes_acoustic"]:
        acoustic_score = weights["acousticness"] * song["acousticness"]
    else:
        acoustic_score = weights["acousticness"] * (1 - song["acousticness"])
    score += acoustic_score
    reasons.append(f"acousticness (+{acoustic_score:.2f})")

    # Instrumentalness closeness
    instr_score = weights["instrumentalness"] * (1 - abs(song["instrumentalness"] - user_prefs["target_instrumentalness"]))
    score += instr_score
    reasons.append(f"instrumentalness (+{instr_score:.2f})")

    return score, " | ".join(reasons)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: str = "default") -> List[Tuple[Dict, float, str]]:
    """Scores all songs, applies diversity penalty, and returns top k with no artist or genre appearing more than twice."""
    scored = []
    for song in songs:
        score, explanation = score_song(user_prefs, song, mode=mode)
        scored.append((song, score, explanation))

    ranked = sorted(scored, key=lambda x: x[1], reverse=True)

    results = []
    artist_counts: Dict[str, int] = {}
    genre_counts: Dict[str, int] = {}
    seen_titles: set = set()

    for song, score, explanation in ranked:
        artist = song["artist"]
        genre = song["genre"]
        title_key = (artist, song["title"])

        if title_key in seen_titles:
            continue
        if artist_counts.get(artist, 0) >= 2:
            continue
        if genre_counts.get(genre, 0) >= 2:
            continue

        results.append((song, score, explanation))
        artist_counts[artist] = artist_counts.get(artist, 0) + 1
        genre_counts[genre] = genre_counts.get(genre, 0) + 1
        seen_titles.add(title_key)

        if len(results) == k:
            break

    return results
