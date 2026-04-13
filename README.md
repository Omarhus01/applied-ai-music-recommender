# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world platforms like Spotify combine two approaches: **collaborative filtering** (recommending based on what similar users listened to) and **content-based filtering** (recommending based on the song's own attributes like energy or mood). They also layer in context signals like time of day and device type. This simulation focuses purely on **content-based filtering** — no other users, no context, just matching a user's taste profile against each song's features using a weighted scoring formula.

For every song in the catalog, the system computes a score by asking: how well does this song match what the user wants? Songs that match on genre, mood, and energy level score higher. The full catalog is then ranked by score and the top K songs are returned as recommendations.

**Song features used:**

- `genre` — categorical (pop, lofi, rock, ambient, jazz, synthwave, indie pop)
- `mood` — categorical (happy, chill, intense, relaxed, focused, moody)
- `energy` — numerical 0.0–1.0 (intensity/loudness feel)
- `valence` — numerical 0.0–1.0 (how sad vs happy the song sounds)
- `acousticness` — numerical 0.0–1.0 (organic vs electronic feel)
- `tempo_bpm` — numerical (speed of the track in beats per minute)
- `danceability` — numerical 0.0–1.0 (how strong the groove/beat is)

**UserProfile stores:**

- `favorite_genre` — the genre the user most identifies with
- `favorite_mood` — the mood they are looking for right now
- `target_energy` — the energy level they want (0.0–1.0)
- `target_valence` — emotional tone target (0.0 sad → 1.0 happy)
- `likes_acoustic` — boolean, whether they prefer organic/acoustic sound
- `target_instrumentalness` — preference for instrumental vs vocal songs (0.0–1.0)

---

## Algorithm Recipe

For each song in the catalog the system computes a score as follows:

```
+ 2.0   if genre matches favorite_genre
+ 1.0   if mood matches favorite_mood
+ 1.0 × (1 - |song.energy - target_energy|)
+ 0.5 × (1 - |song.valence - target_valence|)
+ 0.5 × song.acousticness        (if likes_acoustic is True)
  or
  0.5 × (1 - song.acousticness)  (if likes_acoustic is False)
+ 0.5 × (1 - |song.instrumentalness - target_instrumentalness|)
─────────────────────────────────────────────
  Max possible score: 5.5
```

All songs are then sorted by score descending and the top K are returned.

---

## Expected Biases

- **Genre dominance** — genre is worth +2.0 points, more than any other feature. A wrong-genre song can never outscore a right-genre song even if it matches perfectly on every other dimension.
- **Filter bubble** — because this is a pure content-based system with no collaborative filtering, it only recommends songs similar to what the user already declared they like. There is no serendipity or cross-genre discovery.
- **Catalog imbalance** — some genres have more songs than others (alternative rock has 4, lofi has 3, country has 1). Users with niche preferences get far less variety in their results.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance.
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

