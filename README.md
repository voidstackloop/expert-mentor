# expert-mentor

**Turn any LLM — Claude, ChatGPT, Gemini, or a local Ollama / llama.cpp model — into a professional teacher for any field.**

`expert-mentor` generates a calibrated expert-mentor system prompt for a field and
level, runs the tutoring session directly, remembers what you've mastered across
sessions, and reviews your progress from the transcript.

[![CI](https://github.com/voidstackloop/expert-mentor/actions/workflows/ci.yml/badge.svg)](https://github.com/voidstackloop/expert-mentor/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/expert-mentor.svg)](https://pypi.org/project/expert-mentor/)
[![Python versions](https://img.shields.io/pypi/pyversions/expert-mentor.svg)](https://pypi.org/project/expert-mentor/)
[![License: MIT](https://img.shields.io/github/license/voidstackloop/expert-mentor.svg)](LICENSE)

---

## Why

Most "tutor" prompts are a persona and a vibe. This one is a system: a teaching
contract grounded in learning science (retrieval practice, spacing,
scaffolding), provider-native request handling, and a persistent learner model.
The mentor teaches to the standard a real senior practitioner would recognise —
one concept at a time, checking understanding, and never fabricating sources.

## Highlights

- **Provider-native prompts** — XML-shaped, prompt-cached system blocks for
  Claude; `developer` role, `max_completion_tokens`, and `reasoning_effort` for
  ChatGPT reasoning models; correct handling for Gemini, Ollama, and llama.cpp.
- **Live tutoring sessions** over Anthropic, OpenAI, Ollama, and llama.cpp —
  standard library only, no runtime dependencies.
- **Persistent learner memory** — mastered / shaky / misconceptions / open
  questions, injected into every future session.
- **Model-assisted review** — turn a session transcript into an updated profile.
- **Spaced repetition** — generate flashcards from a session and review them with
  an SM-2-lite scheduler (`mentor cards` / `mentor quiz`).
- **Curriculum design** — a structured, sequenced multi-week plan for any field.
- **Usable as an agent skill** — ships with `SKILL.md` for Claude Code / opencode.

## Install

```bash
# from PyPI (once published)
pipx install expert-mentor        # or: pip install expert-mentor

# from source
git clone https://github.com/voidstackloop/expert-mentor
cd expert-mentor
./install.sh                      # installs `mentor` + links the skill, or:
pipx install .
```

No install needed: run it in place with `./bin/mentor ...` or
`python3 scripts/expert_mentor.py ...`.

## Quick start

```bash
# Generate a system prompt for a field
mentor --field "quantum computing" --level beginner

# Run a live tutoring session (local model)
mentor run --field "Rust" --provider ollama --model qwen2.5:7b

# Run with Claude, remembering progress between sessions
mentor run --field "Rust" --provider claude --remember

# Build a curriculum
mentor curriculum --field "Rust" --duration "6 weeks, 5h/week"
```

## Live sessions

```bash
# Claude — system prompt is cached and XML-shaped; optional extended thinking
mentor run --field "contract law" --provider claude --model claude-sonnet-5 --thinking

# ChatGPT — reasoning effort, developer role, usage reported per turn
mentor run --field "Rust" --provider chatgpt --model gpt-5.6 --reasoning-effort high

# Local — Ollama or a llama.cpp / LM Studio server
mentor run --field "music theory" --provider ollama --host http://localhost:11434
```

Credentials come from the environment or a `.env` file
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`). See
[docs/providers.md](docs/providers.md).

## Remembering a learner

```bash
# Persist progress automatically (named from the field)
mentor run --field "Rust" --provider claude --remember

# Inspect or curate the profile
mentor learners
mentor progress rust --add-mastered ownership --add-shaky lifetimes --goal "ship idiomatic Rust"

# Assess the last session and update the profile
mentor review rust --apply

# Turn the session into flashcards and review them over time
mentor cards rust --generate
mentor quiz rust
```

Profiles, transcripts, prompts, and cards live under
`~/.config/expert-mentor/` as plain JSON/markdown you can read and edit.

## Commands

| Command | Purpose |
|---------|---------|
| `mentor --field F [...]` | generate a teaching prompt |
| `mentor run [NAME]` | live tutoring session (cloud or local) |
| `mentor save/show/saved` | store and reuse mentor prompts |
| `mentor curriculum` | sequenced multi-week curriculum prompt |
| `mentor models` | list / discover Claude & ChatGPT models |
| `mentor fields` / `providers` | curated field profiles / providers |
| `mentor learners` / `progress` / `sessions` / `transcript` / `review` | learner memory & assessment |
| `mentor cards` / `quiz` | spaced-repetition flashcards |
| `mentor config` | saved defaults |
| `mentor doctor` | health check |
| `mentor skill` | install the Claude Code / opencode skill (pip/pipx installs included) |
| `mentor interactive` | build a profile by answering prompts |

Full reference: [docs/commands.md](docs/commands.md).

## Documentation

- [Getting started](docs/getting-started.md)
- [Command reference](docs/commands.md)
- [Providers & credentials](docs/providers.md)
- [How the mentor teaches](docs/learning.md)
- [Configuration](docs/configuration.md)
- [Using it as an agent skill](docs/skill.md)
- [Development](docs/development.md)

## Requirements

Python 3.8+. No third-party runtime dependencies. A local [Ollama](https://ollama.com)
or llama.cpp server is optional (for offline use).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Run `make test` before opening a PR.

## License

[MIT](LICENSE) © expert-mentor contributors.
