# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
