# Model Card: Applied AI Music Recommender

---

## Applied AI Upgrade — Model Card

### Model Name

**VibeMatch 2.0 — Applied AI Edition**

---

### Intended Users

This system is designed for any music listener who wants personalized recommendations without having to fill in structured forms. The user just describes what they want in plain English. It is built as an educational demonstration of how RAG, agentic workflows, and reliability testing work together in a real AI system. It is not intended for commercial deployment.

---

### What the System Does

VibeMatch 2.0 takes a natural language request from the user, uses Gemini to parse it into a structured music preference profile, scores 10,000+ real Spotify tracks against that profile, checks whether the results actually match the intent, and generates grounded natural language explanations for each recommendation. If the results are not good enough, the agent retries automatically with relaxed constraints — up to 3 times.

---

### Training Data / Dataset

**Spotify Tracks Dataset** — sourced from Kaggle, containing approximately 114,000 real tracks across 125 genres with audio features extracted by the Spotify API.

Key columns used: `track_name`, `artists`, `track_genre`, `energy`, `valence`, `acousticness`, `instrumentalness`, `danceability`, `tempo`, `mode`.

**No mood column exists in the dataset.** Mood is derived using the circumplex model of affect — a psychology model that maps valence + energy to mood labels (happy, chill, intense, melancholic, energetic, peaceful, dark). Mode (major/minor), tempo, and acousticness are used as refiners. Spot-check accuracy is approximately 70-80%.

---

### Precision Over Recall — Design Decision

This system deliberately targets **precision over recall**. We would rather return 3 songs the user will genuinely like than return 10 where half are irrelevant. This design decision is enforced in three ways:

1. The diversity penalty prevents the same artist or song title from dominating results
2. The score guardrail warns the user when no strong match exists (top score below 3.0 / 6.5) rather than silently returning weak results
3. The agent retry loop keeps trying until quality is confirmed — it stops only when Gemini judges the results as good or after 3 attempts

---

### Known Biases

- **Genre imbalance** — the Spotify dataset has uneven genre representation. Some genres have thousands of songs, others have very few. Users with rare genre preferences will consistently receive fewer results.
- **Circumplex model bias** — the mood derivation model is based on Western psychological research. It may not map accurately to non-Western music traditions where the relationship between audio features and emotional experience differs.
- **Language bias** — the Spotify dataset skews heavily toward English-language music. Non-English tracks may be underrepresented in certain genres.
- **Categorical dominance** — genre and mood matches add fixed bonus points. In borderline cases this can outweigh numerical feature alignment, meaning a song may rank highly because its label matches even if its sound does not.

---

### Ethical Considerations

- No personal data is collected. The system does not store user requests, preferences, or session history between runs.
- No behavioral tracking. The system does not track what songs a user plays or skips.
- Mood labels are approximations derived from audio features, not psychological assessments. They should not be interpreted as statements about the emotional content of music for any individual user.
- The system uses a commercial AI API (Gemini). Users should be aware that their natural language requests are sent to Google's servers for processing.
- The Gemini API has a cost. Running this system at scale would incur API charges.

---

### Evaluation Summary

- 19 tests total: 15 unit tests + 4 integration tests
- Consistency test: same seed returns identical top 5 across 5 runs ✅
- Mood derivation accuracy: 70%+ on spot-check against known songs ✅
- Precision: at least 40% of top 5 results match intended mood or genre ✅
- All guardrails verified: harmful input blocked before Gemini, malformed output falls back gracefully ✅

---

### Future Work

- Switch to the full 114,000-song dataset for production
- Add collaborative filtering using simulated user play/skip history
- Fine-tune mood derivation with human-verified mood labels
- Add multi-turn conversation so the user can refine results without starting over
- Add support for language-specific genre preferences

---

*Original Module 3 model card preserved below.*

---

# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeMatch 1.0**

---

## 2. Intended Use

VibeMatch 1.0 is designed to suggest 5 songs from a small catalog based on a user's declared taste preferences — their favorite genre, mood, and energy level. It is built for classroom exploration to demonstrate how content-based recommendation systems work at a basic level. It is not intended for real users or production use. The system assumes the user already knows what genre and mood they are looking for, and that those labels exist in the catalog. It should not be used to make decisions about real people's music taste, and it is not a substitute for a real streaming platform recommender.

---

## 3. How the Model Works

Imagine you walk into a music store and hand the clerk a short description of what you want: "I like alternative rock, I want something epic, high energy, not too acoustic." The clerk then walks through every album in the store and gives each one a score based on how well it matches your description. Albums that match your genre get bonus points. Albums that match your mood get more bonus points. Then the clerk checks how close each album's energy level is to what you described — the closer, the more points. The same check happens for the emotional tone (valence), the acoustic vs electronic feel, and whether the music is mostly instrumental or vocal. Once every album has a score, the clerk hands you the top 5.

That is exactly what VibeMatch 1.0 does. It reads a list of songs from a spreadsheet, scores each one against your profile using a weighted formula, and returns the top 5 sorted from highest to lowest score. Genre and mood are treated as labels that either match or do not. Energy, valence, acousticness, and instrumentalness are treated as numbers — the closer the song is to your target, the higher it scores. The only change made from a basic starter system was reducing the genre weight and increasing the energy weight after testing showed genre was dominating results too heavily.

---

## 4. Data

The catalog contains 29 songs stored in a CSV file. The original dataset had 10 songs and was expanded to 29 to improve genre diversity. Songs were added to represent real artists including Imagine Dragons, Adele, Coldplay, Tom Grennan, Kaleo, 2WEI, Aurora, and Indila, as well as fictional artists covering classical, hip-hop, electronic, country, and r&b.

Each song has 11 attributes: id, title, artist, genre, mood, energy, tempo_bpm, valence, danceability, acousticness, and instrumentalness. The numerical features (energy, valence, etc.) are on a 0.0 to 1.0 scale and were assigned manually based on how each song sounds, not computed from actual audio. This means the data reflects one person's judgment of each song's vibe, not an objective measurement. The catalog is heavily weighted toward alternative rock (4 songs), lofi (3 songs), and pop (2 songs), while genres like rock and country have only 1 song each.

---

## 5. Strengths

The system works best when the user's declared genre and mood clearly match songs in the catalog. For the Deep Intense Rock profile, Storm Runner scored 5.45 out of 6.5 — a near-perfect result that matched the expectation completely. For the Chill Lofi profile, Library Rain and Midnight Coding came first exactly as expected. The scoring logic is fully transparent — every recommendation comes with a plain-language explanation of why each song was chosen, which makes it easy to understand and debug. The system also degrades gracefully when a genre does not exist in the catalog: instead of breaking, it falls back to numerical feature matching and still returns reasonable results.

---

## 6. Limitations and Bias

The most significant weakness discovered during testing is categorical score dominance. Even after reducing the genre weight from 2.0 to 1.0, the combined genre and mood match still adds up to +2.0 points out of a maximum of 6.5, which consistently overrides numerical feature alignment. In the conflicting profile test — a user wanting high energy (0.90) with a melancholic mood — Hello by Adele ranked #1 despite having an energy of only 0.45, because the genre and mood match outweighed the large energy mismatch entirely. This means the system effectively ignores how a song actually sounds in favor of how it is labeled, which could frustrate users whose emotional state does not align neatly with a single genre or mood tag. A second limitation is catalog imbalance — genres like rock and country have only one or two songs, so users with those preferences receive almost no variety in their results. Finally, because this is a pure content-based system with no collaborative filtering, it creates a filter bubble where users are never exposed to songs outside their declared preferences, removing any chance of serendipitous discovery.

---

## 7. Evaluation

Seven user profiles were tested to evaluate how the recommender behaves across a range of preferences. Three were standard profiles — High-Energy Pop, Chill Lofi, and Deep Intense Rock — designed to match songs that clearly exist in the catalog. Four were adversarial profiles designed to expose weaknesses: a conflicting profile (high energy + melancholic mood), a missing genre profile (jazz fusion which does not exist in the catalog), a profile that wants instrumental music but declares pop as its genre, and a dead center profile where all numerical targets were set to 0.5.

The standard profiles all produced intuitive results. Storm Runner scored 5.45 out of 6.5 for the rock profile — nearly perfect — and Library Rain topped the lofi profile as expected. What was surprising was the conflicting profile: Hello by Adele ranked first despite the user wanting energy of 0.90, because the genre and mood label match (soul pop + melancholic) outweighed the large energy gap. This confirmed the categorical dominance bias. The missing genre profile degraded gracefully — no song scored above 3.44 — but still returned acoustically similar songs, which showed the numerical features work independently. A weight shift experiment was also run, doubling energy importance and halving genre importance, which improved diversity and pushed high-energy songs into the conflicting profile results.

---

## 8. Future Work

- **Add a diversity penalty** — prevent the same artist or genre from appearing more than twice in the top 5. Right now all 4 alternative rock songs can dominate the list for a rock user with no variety.
- **Replace single mood label with a mood range** — instead of one fixed mood, let users specify a range like "somewhere between chill and focused." This would reduce the filter bubble effect and better reflect how real listening sessions feel.
- **Add collaborative filtering** — track which songs users actually play or skip and use that behavior to update recommendations over time. Right now the system only knows what users say they want, not what they actually respond to when they hear it.

---

## 9. Personal Reflection

The biggest learning moment in this project was understanding how real platforms like Spotify actually work under the hood. Before this, recommendations felt like magic — now they feel like math with labels. Learning the difference between collaborative filtering and content-based filtering made it clear why Spotify can recommend a Spanish song to an English speaker (collaborative filtering does not care about language, only behavior patterns) while also being able to suggest something that sounds sonically similar to what you just played (content-based filtering). Seeing both approaches laid out made the real complexity of hybrid systems much more concrete.

What stood out most was how quickly bias shows up even in the simplest model. With only 29 songs and a basic scoring formula, the system already demonstrated a filter bubble, catalog imbalance, and categorical dominance — the same problems that billion-dollar platforms are still trying to solve. The conflicting profile test was the clearest example: a user wanting high-energy melancholic music got a quiet Adele ballad at the top because the genre label matched, not the sound. That was a genuinely surprising result that showed how easy it is for a system to feel confident while being wrong.

AI tools were used throughout this project for gathering background research on how platforms like Spotify and TikTok work, critiquing the design decisions at each step, planning the algorithm recipe, and analyzing each profile's output. The most valuable use was having each decision challenged before implementation — asking whether the weights were balanced, whether the profile was too narrow, whether the scoring formula rewarded closeness correctly. That kind of step-by-step critique made the final system more thoughtful than it would have been otherwise.

What surprised me most was how a formula this simple — six weighted checks — can still produce results that genuinely feel like recommendations. When Library Rain came first for the chill lofi profile or Believer topped the alternative rock list, it felt right in a way that was satisfying. That feeling is the illusion that makes real recommenders so powerful, and it only takes a few intentional rules to create it.

The next step would be adding collaborative filtering by simulating multiple users with different play and skip histories. Right now the system only knows what a user says they want — not what they actually respond to when they hear it. Combining both filtering systems would make the simulator dramatically more powerful and more realistic, showing how the two approaches complement each other. That requires real user behavior data, which takes time to build, but it would be the most meaningful extension to this project.
