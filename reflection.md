# Reflection — Applied AI Music Recommender

---

## 1. What I Built and How It Works

### Where It Started

I started with the Module 3 music recommender — a system that scored songs against a structured user profile using a weighted formula. It worked, but it felt rigid. You had to know exactly what genre you wanted, what your target energy was, whether you liked acoustic music. Nobody talks like that.

### What Changed

The upgrade turns it into something that actually feels natural. You type what you're in the mood for and the system figures out the rest:

- **Gemini** reads your request and converts it into a structured profile
- The **recommender** scores songs from a 114,000-track Spotify dataset against that profile
- **Gemini checks** whether the results actually match what you asked for
- If they don't, it **adjusts and retries** — up to 3 times automatically
- Each song gets a **natural language explanation** grounded in its actual audio features

### The Dataset Challenge

The new Spotify dataset had no mood column. Mood had to be derived from audio features using the **circumplex model of affect** — a psychology model that maps energy and valence to emotions like happy, chill, intense, or melancholic. Mode (major/minor key), tempo, and acousticness were used as refiners. That was one of the more interesting problems because the system had to make a judgment call about how a song *feels*, not just what genre it is.

---

## 2. Which AI Features I Added and Why

I added three of the four possible features:

| Feature | Why I Chose It |
|---|---|
| Agentic Workflow | Made the biggest difference to how the system feels — conversation instead of a form |
| RAG | Raw score numbers mean nothing to a real user — grounded explanations fix that |
| Reliability Testing | Working code is not the same as good logic — I needed to actually verify behavior |

### Agentic Workflow

The loop of **parse → recommend → check → retry** is what makes it feel like the system is thinking, not just calculating. I also liked that it forces the system to be honest — if it can't find a good match after three tries, it tells you that instead of pretending.

### RAG

The key thing I understood from the course is that RAG is not about letting AI guess — it's about giving the AI real data to work with so it can't hallucinate. The song's actual features (energy, valence, mood, genre) are the retrieved context. Gemini uses those to write something meaningful instead of making things up.

### Reliability Testing

The course was clear: working code is not the same as good logic. I wanted to verify the system actually behaves correctly, not just that it runs.

---

## 3. How I Approached Testing

### The Mindset

I started by thinking about what could go wrong rather than what should work. That's something the course emphasized — edge cases are where systems actually fail.

### Unit Tests (No API — Fast)

- Empty genre, unknown genre, rare genre (tango)
- All-0.5 preferences (the "dead center" profile)
- Consistency: same random seed always returns the same top 5
- Precision: at least 40% of top 5 results match the intended mood or genre
- All guardrails: harmful, empty, and nonsensical inputs correctly rejected

### Integration Tests (Real Gemini API)

- **RAG fallback**: simulated Gemini failing — verified the system doesn't crash, just falls back to score-based explanations
- **Agent retry**: gave the system a conflicting input and verified the retry loop triggers without breaking
- **Full end-to-end**: user types a request, agent runs, results come back well-formed with real explanations
- **Guardrail integration**: harmful input never reaches Gemini at all

### What Testing Revealed

The duplicate song title bug — where the same song could appear twice in results under different genre tags — only became obvious when thinking through edge cases. I fixed it before it ever caused a real problem. That's the point of testing.

---

## 4. What Surprised Me

### The API Quota Problem

I didn't expect free tier limits to be hit so quickly. Dealing with that took real time — switching accounts, setting up billing, figuring out which model names were still available. It taught me something practical: any real AI system needs billing and rate limit handling from the start, not as an afterthought.

### The Retry Loop

I assumed Gemini would always return good results on the first try. In reality, for conflicting or vague requests it often needed to retry. Watching the retry logic actually trigger and seeing the results improve was genuinely satisfying — it meant the agentic design was actually working.

---

## 5. What I Would Do Differently

- **Switch to the full 114k dataset earlier in development** — I used a 10,000-song sample during development and switched to the full dataset before final submission, but testing on the full scale earlier would have caught any scale-related issues sooner
- **Add multi-turn conversation** — right now every request is independent. A real system would let you say "give me something more upbeat" without starting over
- **Add human-verified mood labels** — the circumplex model is a good approximation but a small labeled dataset would make mood derivation much more accurate

---

## 6. What This Taught Me About Real AI Systems

### System Design Matters More Than the Model

AI features are only as good as the system design around them. Gemini is powerful, but without guardrails, structured prompts, and a clear retry strategy it produces inconsistent results. The course framed this well — **agency is repeated decision-making, not intelligence**. The agentic loop isn't smart, it's systematic. That distinction matters.

### Bias Shows Up Even in Simple Systems

- Genre imbalance in the Spotify dataset
- The circumplex model's limitations for non-Western music
- Categorical labels overriding numerical features in borderline cases

These are real problems, not hypothetical ones. Documenting them in the model card wasn't just an assignment requirement — it was the honest thing to do.

### What "Applied AI" Actually Means

Building something that runs, handles failures gracefully, and produces results you can explain — that's what the applied AI framing means. Not just calling an API, but thinking through the whole system: the data, the logic, the guardrails, the tests, and the honest documentation of what it can and can't do.

---

*Original Module 3 profile comparisons preserved below.*

---

# Profile Comparisons and Reflections

---

## Pair 1: High-Energy Pop vs Chill Lofi

The High-Energy Pop profile returned Sunrise City and Gym Hero at the top — both fast, upbeat pop songs. The Chill Lofi profile returned Library Rain and Midnight Coding — slow, quiet, study-music type tracks. These two profiles produced completely opposite results, which makes sense. One user is looking for something to pump them up, the other wants background music to focus or relax. The system correctly separated them because genre, mood, and energy all pointed in opposite directions. This is the clearest example of the recommender working exactly as intended.

---

## Pair 2: Deep Intense Rock vs Conflicting (High Energy + Melancholic)

The Deep Intense Rock profile returned Storm Runner at #1 with a near-perfect score — high energy, intense mood, rock genre, everything aligned. The Conflicting profile — which wanted high energy but a melancholic mood — returned Hello by Adele at #1. This is where the system gets tricky. Adele is melancholic and matches the genre (soul pop), but her songs are not high-energy at all. The system chose the emotional label over the actual sound. For a real user who wants something that feels like an intense Adele-style emotional punch — think Rolling in the Deep — the system partially gets it right, but it still leans toward quiet ballads because "melancholic" and "soul pop" are the dominant signals. High-energy rock songs like Believer only appear lower in the list.

---

## Pair 3: Missing Genre (Jazz Fusion) vs Dead Center (All 0.5)

The Missing Genre profile asked for jazz fusion which does not exist in the catalog. The system still returned reasonable results — Coffee Shop Stories (jazz, relaxed) came first because its energy and mood were closest to what the user wanted. No song scored above 3.44, meaning the system clearly struggled but did not break. The Dead Center profile set all preferences to the middle (0.5). This exposed an interesting behavior — with no strong numerical preference, the genre match became the deciding factor again, and Spacewalk Thoughts won just from being the only ambient song. After the weight shift experiment, Focus Flow took over because energy alignment mattered more. This pair shows that when users have vague preferences, the system defaults to whatever categorical label matches rather than finding a truly average-sounding song.

---

## Pair 4: Wants Instrumental but Likes Pop vs High-Energy Pop

Both profiles declared pop as their favorite genre and happy as their mood. The only difference was that one wanted highly instrumental music (target_instrumentalness = 0.95) while the other just wanted energetic pop. Both returned Sunrise City at #1. This shows a weakness — the instrumentalness preference was essentially ignored because pop songs in the catalog are all vocal. The genre weight pulled pop songs to the top regardless of how instrumental the user wanted their music to be. Vivaldi appeared at #5 in the instrumental profile, which is the one moment the system responded to the instrumentalness preference. In a real app, wanting instrumental music should probably override genre entirely, but our scoring does not currently support that kind of priority logic.
