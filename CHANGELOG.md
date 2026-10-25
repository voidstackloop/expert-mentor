# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Keyless `agent` provider (`mentor run --provider agent`, aliases `manual` /
  `own` / `byom`): no API key, no network. Paste the system prompt into your
  agent's own app (Claude/ChatGPT/Gemini app, Claude Code, opencode) and relay
  the turns in the terminal so transcripts, learner memory, review (`--dry-run`
  + `mentor progress`), and cards keep working. `mentor review` / `mentor cards
  --generate` with `--provider agent` print a paste-into-your-app prompt via
  `--dry-run` instead of calling a backend.
- `mentor doctor` reports the keyless relay first, covers the Gemini key, never
  prints key values, and warns when a `.env` file is group/other-readable
  (`chmod 600`).
- `mentor skill --bundle DIR` builds upload-ready zips for ChatGPT, Claude,
  opencode, Agensi (agensi.io marketplace), and a generic host (`SKILL.md` +
  `templates/` + `references/` + per-host install notes) — no terminal or API
  key needed on the host.
- `mentor skill --validate` checks the package against the Agent Skills spec
  (frontmatter, name/dir match, description length, body size, file refs).
- Stronger Phase 4 consolidation in the master prompt: corrected learner
  self-summary, 3 banked retrieval questions (easy→hard), a misconception
  watchlist with defeating evidence, and practice with a done-criterion; the
  agent relay prints the keyless review/cards follow-ups when a session ends.
- Session reviews now return `retrieval_questions` (answerable from that
  session alone, easiest first) and `mentor review` prints them banked for the
  next session; the compact prompt closes the same way for small local models.
- Flashcard generation now turns each revealed misconception into a
  discrimination card (wrong belief → why it fails → correct model + evidence).
- `examples/rust.agent.json` — the exact keyless relay payload a hosted/
  no-terminal user works with (system prompt + how-to-use, no keys).
- Live sessions for Google/Gemini (`mentor run --provider google`), on par with
  Anthropic, OpenAI, Ollama, and llama.cpp.
- `mentor skill` — install the Claude Code / opencode skill from the CLI
  itself, so a `pip`/`pipx` install gets it too, not just a git checkout.
- `examples/cpp.google.transcript.md` — a live Gemini tutoring transcript.

### Fixed
- `google`'s default model was the retired `gemini-2.5-pro`; now the rolling
  `gemini-flash-latest` alias.

### Changed
- `install.sh` now calls `mentor skill` instead of duplicating its symlink logic.

## [0.6.1] - 2026-09-12

### Changed
- Package the README as the PyPI long description and ship `docs/` in the sdist.
- Add a `MANIFEST.in` so documentation is included in source distributions.

## [0.6.0] - 2026-09-12

### Added
- Spaced-repetition flashcards: `mentor cards` (add / generate / list / remove)
  and `mentor quiz` with an SM-2-lite scheduler (`scripts/mentor_cards.py`,
  `templates/cards_prompt.md`).
- `mentor run --history-turns N` caps how many past turns are kept in context.

### Fixed
- Include `mentor_cards` in the packaged modules so the installed wheel runs.

## [0.5.0] - 2026-09-12

### Added
- Persistent learner memory and session transcripts (`mentor learners`,
  `mentor progress`, `mentor sessions`, `mentor transcript`).
- Model-assisted progress review: `mentor review [--apply]`.
- Packaging (`pyproject.toml`, console entry points), CI, and a
  Trusted-Publishing release workflow.
- Config file: `mentor config`.
- Colored, TTY-aware health output and `--quiet`.

### Changed
- Provider-native handling for Claude (prompt caching, extended thinking, XML
  shaping) and ChatGPT (developer role, `max_completion_tokens`,
  `reasoning_effort`, usage reporting).
- Live sessions for Anthropic, OpenAI, Ollama, and llama.cpp with retry/backoff.
- Model catalog and live discovery: `mentor models --refresh`.

## [0.1.0] - 2026-09-11

### Added
- Initial release: provider-aware expert-mentor prompt generation, curated field
  profiles, curriculum and compact templates, one-command installer, and the
  `SKILL.md` agent skill.

[Unreleased]: https://github.com/voidstackloop/expert-mentor/compare/v0.6.1...HEAD
[0.6.1]: https://github.com/voidstackloop/expert-mentor/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/voidstackloop/expert-mentor/releases/tag/v0.6.0
[0.5.0]: https://github.com/voidstackloop/expert-mentor/releases
[0.1.0]: https://github.com/voidstackloop/expert-mentor/releases
