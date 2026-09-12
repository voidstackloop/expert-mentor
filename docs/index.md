# expert-mentor documentation

`expert-mentor` turns any capable LLM into a professional teacher for a field
you choose. It generates the teaching prompt, runs the session, remembers the
learner across sessions, and helps them retain what they learned.

## Contents

| Document | What it covers |
|----------|----------------|
| [Getting started](getting-started.md) | install, first prompt, first session |
| [Command reference](commands.md) | every command and flag |
| [Providers & credentials](providers.md) | Claude, ChatGPT, Gemini, Ollama, llama.cpp |
| [How the mentor teaches](learning.md) | pedagogy, learner memory, review, flashcards |
| [Configuration](configuration.md) | config file, environment variables, file locations |
| [Agent skill](skill.md) | using it with Claude Code / opencode |
| [Development](development.md) | architecture, tests, packaging, releases |

## The 60-second tour

```bash
# 1. Generate a teaching prompt for a field
mentor --field "quantum computing" --level beginner

# 2. Run the tutor live (local or cloud)
mentor run --field "Rust" --provider claude --remember

# 3. Check in on progress later
mentor progress rust
mentor quiz rust
```

## Concepts

- **Field profile** — what professional competence looks like in a subject:
  concepts, misconceptions, canonical resources, capstone. See
  [`references/fields.md`](../references/fields.md).
- **Mentor prompt** — the system prompt that defines the teaching contract. See
  [`templates/mentor_system_prompt.md`](../templates/mentor_system_prompt.md).
- **Learner** — a named profile that persists mastered / shaky / misconception /
  open-question state across sessions.
- **Session** — a transcript of a live `mentor run`, stored under
  `~/.config/expert-mentor/sessions/`.
- **Cards** — spaced-repetition flashcards generated from a session.

## Getting help

```bash
mentor --help
mentor doctor
```
