#!/usr/bin/env python3
"""Package the repo as a marketplace-ready SKILL.md zip (e.g. for Agensi).

Zips exactly what an agent needs to run the skill: SKILL.md at the root of a
single top-level folder, plus templates/, references/, scripts/, examples/,
docs (markdown only), README, and LICENSE. Leaves out the pip-packaging and
installer files (pyproject.toml, bin/, install.sh, Makefile, .github) and any
binary assets, since marketplace security scans flag unexpected binaries and
those files aren't needed for an agent to use the skill (SKILL.md already
documents the `python3 scripts/expert_mentor.py ...` fallback).
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "expert-mentor"

INCLUDE_FILES = ["SKILL.md", "README.md", "LICENSE"]
INCLUDE_DIRS = ["scripts", "templates", "references", "examples"]
# docs/ has screenshots too; only take the markdown + the text-based SVG diagrams.
INCLUDE_GLOBS = ["docs/*.md", "docs/*.svg"]
# maintainer-only (PyPI/release process) — not relevant to someone using the skill.
EXCLUDE_DOCS = {"docs/development.md"}

EXCLUDE_SUFFIXES = {".pyc"}
EXCLUDE_NAMES = {"__pycache__"}
EXCLUDE_FILENAMES = {"build_skill_zip.py"}


def iter_members():
    for name in INCLUDE_FILES:
        p = ROOT / name
        if p.is_file():
            yield p
    for d in INCLUDE_DIRS:
        for p in sorted((ROOT / d).rglob("*")):
            if (
                p.is_file()
                and p.suffix not in EXCLUDE_SUFFIXES
                and p.parent.name not in EXCLUDE_NAMES
                and p.name not in EXCLUDE_FILENAMES
            ):
                yield p
    for pattern in INCLUDE_GLOBS:
        for p in sorted(ROOT.glob(pattern)):
            if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDE_DOCS:
                yield p


def main() -> int:
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"{SKILL_NAME}-skill.zip"

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in iter_members():
            arcname = f"{SKILL_NAME}/{p.relative_to(ROOT).as_posix()}"
            zf.write(p, arcname)

    names = zipfile.ZipFile(out_path).namelist()
    print(f"wrote {out_path} ({len(names)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
