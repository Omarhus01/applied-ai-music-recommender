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
