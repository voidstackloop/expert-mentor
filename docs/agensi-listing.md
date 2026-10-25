# Agensi listing copy

## Title

Expert Mentor

## Summary (card one-liner, 115 chars)

Turn Claude, ChatGPT, Gemini or a local LLM into a professional tutor that remembers your progress and quizzes you.

## Full description

**Most "AI tutor" prompts are a persona and a vibe.** Ask a generic chatbot to
teach you something and you get a friendly tone with none of the substance —
no check for understanding, no memory of what you covered yesterday, and a
real risk it just makes something up with total confidence.

Expert Mentor is different because it isn't a persona, it's a teaching
**system**. Every session runs on a contract built from actual learning
science — retrieval practice, spaced repetition, scaffolding — the same
principles behind how real senior practitioners train juniors. The mentor
doesn't lecture at you. It checks you understood the last concept before it
gives you the next one, and it is instructed, explicitly, to flag uncertainty
instead of fabricating a source, a formula, or an API.

Here's the part most tutor prompts can't do at all: **it remembers.** Run a
session today, close your laptop, come back next week — the mentor still
knows what you've mastered, what's still shaky, and what you got wrong last
time. Nothing to re-explain, no starting over. Left unreviewed, most of what
you "learned" this week is gone within days; Expert Mentor's SM-2-lite
flashcard scheduler exists specifically to catch that before it happens.

**What you actually get:**

- A calibrated mentor persona for *any* field — "quantum computing,"
  "contract law," "Rust," whatever you need, at beginner through expert level
- Live tutoring sessions, run directly, against Claude, ChatGPT, Gemini, or a
  fully offline local model (Ollama / llama.cpp) — your choice, your data stays
  where you put it
- A persistent learner profile that tracks mastered topics, shaky ones,
  misconceptions, and open questions across every session
- Automatic post-session review that updates that profile for you — no manual
  bookkeeping
- Spaced-repetition flashcards generated straight from your transcripts
- A full multi-week curriculum generator when you want a structured plan
  instead of an open-ended chat
- Provider-native prompt engineering under the hood: XML-shaped, cached system
  blocks for Claude; correct `developer`-role handling for ChatGPT reasoning
  models; proper treatment for Gemini and local runtimes — so quality doesn't
  degrade depending on which model you point it at

**What's inside:** `SKILL.md` (agent instructions) plus a dependency-free
Python CLI (`scripts/`), prompt templates (`templates/`), teaching-method and
provider references (`references/`), and ready-made examples (`examples/`).
No terminal needed — on Agensi it just works in the default agent app, free.
Power users can also run the CLI locally with one command (Python 3.8+, zero
runtime dependencies); the terminal examples only demonstrate that path.

You already know the alternative: open a chat, type "teach me X," get a
decent first answer, and lose all of it the moment the context resets. Install
the mentor once, and every session after the first one starts smarter than
the last.

## Tags

education, tutoring, mentoring, prompt-engineering, curriculum, flashcards

## Price

Free.
