# Development

## Layout

```
expert-mentor/
├── SKILL.md                     agent skill definition (trigger + workflow)
├── README.md
├── docs/                        user documentation
├── bin/mentor                   symlink-safe launcher
├── install.sh / uninstall.sh    one-command setup / teardown
├── Makefile                     install | test | doctor | fields | demo | dist | clean
├── pyproject.toml               packaging + entry points
├── templates/                   prompt templates (data)
├── references/                  pedagogy, fields, providers (data + skill refs)
├── examples/                    generated samples
└── scripts/
    ├── expert_mentor.py         CLI, generators, commands
    ├── mentor_runtime.py        streaming chat adapters (no deps)
    ├── mentor_memory.py         learner profiles + session transcripts
    ├── mentor_cards.py          spaced-repetition flashcards
    └── selftest.py              test suite
```

## Design

- **Zero runtime dependencies.** HTTP via `urllib`; streaming via SSE / ndjson
  parsing; JSON via the standard library.
- **Pure functions for the tricky parts.** `build_*_payload` in
  `mentor_runtime` and the scheduler in `mentor_cards` are pure and unit-tested.
- **Provider capability inference.** The request shape (system role, token-limit
  field, temperature support, reasoning) is derived from the provider + model
  name so it stays correct as models change.
- **Plain-file state.** Learner profiles, cards, config, and transcripts are
  JSON/markdown under `~/.config/expert-mentor`, easy to inspect and back up.

## Run the tests

```bash
make test          # or: python3 scripts/selftest.py
```

The suite is dependency-free and covers the resolver, all emit formats,
provider-native shaping, the runtime payload builders, dry-runs, learner memory,
review parsing/merging, flashcards, scheduling, and the config system.

```bash
make doctor        # health check
make demo          # sample prompt
make curriculum    # sample curriculum
```

## Build packages locally

```bash
make dist          # sdist + wheel into dist/ (installs `build`)
python3 -m twine check dist/*
```

The wheel bundles `templates/` and `references/` as data files under
`share/expert-mentor/`; the CLI resolves them whether run from the repo or
installed.

## Release

Publishing uses **PyPI Trusted Publishing** (OIDC) — no API tokens.

1. One-time: add a pending publisher at
   <https://pypi.org/manage/account/publishing/> with
   project `expert-mentor`, owner `voidstackloop`, repo `expert-mentor`,
   workflow `release.yml`, environment `pypi`.
2. Bump `__version__` in `scripts/expert_mentor.py`.
3. Tag and push:

```bash
git tag v0.7.0
git push origin v0.7.0
```

The [Release workflow](../.github/workflows/release.yml) builds, checks,
publishes to PyPI, and creates the GitHub Release.

## Style

`ruff` config lives in `pyproject.toml` (line length 120). Keep the code
standard-library only, and add a test for anything non-trivial.
