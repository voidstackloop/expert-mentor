# Contributing

Thanks for helping improve expert-mentor. This project is intentionally small,
dependency-free, and easy to run locally.

## Setup

```bash
git clone https://github.com/voidstackloop/expert-mentor
cd expert-mentor
./install.sh          # or run in place with ./bin/mentor
make doctor
```

## Before you open a PR

```bash
make test             # 99+ assertions, no third-party deps
```

- Add a test for any non-trivial change (see `scripts/selftest.py`).
- Keep the code **standard library only** at runtime.
- Follow the existing style; `ruff` config is in `pyproject.toml` (line length 120).
- Update `README.md` / `docs/` when behaviour changes, and add a `CHANGELOG.md`
  entry under `Unreleased`.

## Good first contributions

- **Add a field profile** — see `references/fields.md`; append to
  `references/fields.json`.
- **Add a provider adapter** — streaming backends live in
  `scripts/mentor_runtime.py`; payload builders are pure and unit-tested.
- **Improve a prompt** — `templates/*.md`.
- **Fix an example** — `examples/` is regenerated from the CLI.

## Commit messages

Use a short imperative subject and explain the *why* in the body. Reference an
issue if there is one.

## Pull requests

1. Fork and branch from `main`.
2. Make the change with tests.
3. Ensure `make test` passes and CI is green.
4. Open the PR with a clear description of the change and its motivation.

## Reporting issues

Include your OS, Python version (`mentor version`), the exact command, and the
full output. `mentor doctor` output is helpful too.
