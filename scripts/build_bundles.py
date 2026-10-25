#!/usr/bin/env python3
"""Build all distributable bundles into bundles/.

One canonical Agent Skills zip covers Claude Code, Claude web, Cursor,
Copilot, OpenCode, Codex, Gemini Skills, and Agensi (all consume a
SKILL.md folder). ChatGPT Custom GPTs and Gemini Gems have no ZIP import,
so this also builds paste-ready GPT/Gem packs (instructions + knowledge
+ import README).

Output (all in bundles/):
  expert-mentor-skill.zip   canonical skill (upload/extract anywhere)
  expert-mentor-agensi.zip  same + docs/agensi-listing.md as LISTING.md
  chatgpt-gpt-pack.zip      paste into GPT Builder
  gemini-gem-pack.zip       paste into Gems -> New Gem
  INSTALL.md                where each zip goes per provider

Stdlib only. Python 3.8+.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "bundles"
SKILL_NAME = "expert-mentor"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_skill_zip  # reuse canonical member list


def skill_members():
    for p in build_skill_zip.iter_members():
        # maintainer-only builders never ship inside the skill
        if p.name in {"build_skill_zip.py", "build_bundles.py"}:
            continue
        yield p


def write_zip(out_path: Path, members, extra=None) -> int:
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in members:
            arcname = SKILL_NAME + "/" + p.relative_to(ROOT).as_posix()
            zf.write(p, arcname)
        for arcname, text in (extra or {}).items():
            zf.writestr(SKILL_NAME + "/" + arcname, text)
    return len(zipfile.ZipFile(out_path).namelist())


def load_prompt_body() -> str:
    """Master prompt minus the maintainer preamble."""
    text = (ROOT / "templates" / "mentor_system_prompt.md").read_text(encoding="utf-8")
    marker = "SYSTEM PROMPT"
    if marker in text:
        text = text.split(marker, 1)[1].lstrip("=\n- ")
    return text.strip() + "\n"


GENERIC_SLOTS = {
    "{{MENTOR_NAME}}": "Expert Mentor",
    "{{FIELD}}": "subject",
    "{{LEVEL}}": "inferred from the conversation (beginner/intermediate/advanced/expert)",
    "{{LEARNER_CONTEXT}}": "ask during intake; if absent, establish it with 2-3 questions",
    "{{SESSION_GOAL}}": "ask during intake; default: durable, practical competence",
    "{{LANGUAGE}}": "the language the learner writes in",
    "{{TEACHING_STYLE}}": "Socratic by default; adapt if the learner asks for direct/coaching/immersive",
    "{{LEARNER_HISTORY}}": "(no history yet - build mastered/shaky/misconceptions lists as you go)",
    "{{FIELD_NOTES}}": "(no field profile loaded - teach to senior-practitioner standard)",
    "{{TONE}}": "warm, direct, encouraging",
    "{{LENGTH_RULE}}": "concise: one concept per reply, concrete example first",
}

CHATGPT_CAPABILITY = (
    "You teach whatever field the learner asks about; wherever the prompt says "
    "subject, substitute the real field everywhere. "
    "You are running as a ChatGPT Custom GPT. Use clear markdown structure "
    "(headings, short lists). End each teaching reply with one retrieval question "
    "or small exercise and an explicit next step. Never fabricate sources, "
    "formulas, or APIs - say you are unsure and how to verify."
)

GEMINI_CAPABILITY = (
    "You teach whatever field the learner asks about; wherever the prompt says "
    "subject, substitute the real field everywhere. "
    "You are running as a Gemini Gem. Use clear markdown structure. Keep replies "
    "focused: one concept at a time, one worked example, then one check question. "
    "Never fabricate sources, formulas, or APIs - say you are unsure and how to verify."
)


def render_instructions(capability: str) -> str:
    body = load_prompt_body()
    for slot, value in GENERIC_SLOTS.items():
        body = body.replace(slot, value)
    body = body.replace("{{CAPABILITY_NOTES}}", capability)
    return body


STARTERS = [
    "Teach me quantum computing (I am a beginner)",
    "Be my Rust mentor - test my level first",
    "Explain macroeconomics like a professor",
    "Design me a 6-week study plan for contract law",
]

GPT_README = """# ChatGPT GPT pack - expert-mentor

Custom GPTs have no ZIP import. Create the GPT by pasting:

1. Go to ChatGPT -> Explore GPTs -> Create (requires an account that can create GPTs;
   on some plans GPT creation is restricted - see OpenAI help).
2. Name: `Expert Mentor`
3. Description: paste `description` from `gpt-config.json`.
4. Instructions: paste the full contents of `instructions.md`.
5. Conversation starters: add each line from `conversation-starters.txt`.
6. Knowledge (optional): upload `knowledge/pedagogy.md` and `knowledge/fields.md`.
7. Save. Start with e.g. "Teach me Rust (I am a beginner)".

To teach a fixed field instead of any field, replace
"subject" in `instructions.md` with that field.
"""

GEM_README = """# Gemini Gem pack - expert-mentor

Gems have no ZIP import. Create the Gem by pasting:

1. Go to Gemini -> Gems -> New Gem (account/Workspace permitting).
2. Name: `Expert Mentor`
3. Instructions: paste the full contents of `instructions.md`.
4. Knowledge (optional): upload `knowledge/pedagogy.md` and `knowledge/fields.md`.
5. Save. Start with e.g. "Teach me Rust (I am a beginner)".

Google is migrating Gems to Skills: the canonical
`expert-mentor-skill.zip` can instead be uploaded via the Skills interface
(`SKILL.md` + supporting files) where available.

To teach a fixed field instead of any field, replace
"subject" in `instructions.md` with that field.
"""

INSTALL_MD = """# Bundles - where each file goes

Built by `python3 scripts/build_bundles.py` (`make bundles`).

| File | Providers | Install |
|------|-----------|---------|
| `expert-mentor-skill.zip` | Claude Code, Claude web, Cursor, Copilot, OpenCode, Codex, Gemini Skills | Extract the `expert-mentor/` folder to the skills dir, e.g. `~/.claude/skills/expert-mentor`, `.cursor/skills/expert-mentor`, `.github/skills/expert-mentor`, `.opencode/skills/expert-mentor`, `~/.agents/skills/expert-mentor`. Claude web: upload ZIP via Customize -> Skills. Gemini: upload `SKILL.md` via Skills interface. |
| `expert-mentor-agensi.zip` | Agensi.io | Upload the ZIP in Creator Dashboard (contains `SKILL.md` + `LISTING.md`). Review required. |
| `chatgpt-gpt-pack.zip` | ChatGPT Custom GPTs | No ZIP import - unzip, follow `README.md` (paste `instructions.md`). |
| `gemini-gem-pack.zip` | Gemini Gems | No ZIP import - unzip, follow `README.md` (paste `instructions.md`). |
| Local models (no bundle needed) | Ollama / llama.cpp / LM Studio | `python3 scripts/expert_mentor.py --field "Rust" --provider ollama --emit modelfile --compact > Modelfile` (see `references/providers.md`). |

All skill zips carry `SKILL.md` with `name: expert-mentor` matching the folder name
(Agent Skills spec: https://agentskills.io/specification).
"""


def build_skill(out: Path) -> None:
    n = write_zip(out, skill_members())
    print("wrote %s (%d files)" % (out, n))


def build_agensi(out: Path) -> None:
    listing = ROOT / "docs" / "agensi-listing.md"
    extra = {}
    if listing.is_file():
        extra["LISTING.md"] = listing.read_text(encoding="utf-8")
    n = write_zip(out, skill_members(), extra)
    print("wrote %s (%d files)" % (out, n))


def build_gpt_pack(out: Path) -> None:
    instructions = render_instructions(CHATGPT_CAPABILITY)
    pedagogy = (ROOT / "references" / "pedagogy.md").read_text(encoding="utf-8")
    fields = (ROOT / "references" / "fields.md").read_text(encoding="utf-8")
    config = {
        "name": "Expert Mentor",
        "description": "Turns ChatGPT into a professional teacher for any field - intake, roadmap, tutoring with checks, and practice.",
        "instructions_file": "instructions.md",
        "conversation_starters": STARTERS,
        "knowledge": ["knowledge/pedagogy.md", "knowledge/fields.md"],
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("instructions.md", instructions)
        zf.writestr("conversation-starters.txt", "\n".join(STARTERS) + "\n")
        zf.writestr("gpt-config.json", json.dumps(config, indent=2) + "\n")
        zf.writestr("knowledge/pedagogy.md", pedagogy)
        zf.writestr("knowledge/fields.md", fields)
        zf.writestr("README.md", GPT_README)
    print("wrote %s (6 files)" % out)


def build_gem_pack(out: Path) -> None:
    instructions = render_instructions(GEMINI_CAPABILITY)
    pedagogy = (ROOT / "references" / "pedagogy.md").read_text(encoding="utf-8")
    fields = (ROOT / "references" / "fields.md").read_text(encoding="utf-8")
    config = {
        "name": "Expert Mentor",
        "instructions_file": "instructions.md",
        "conversation_starters": STARTERS,
        "knowledge": ["knowledge/pedagogy.md", "knowledge/fields.md"],
    }
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("instructions.md", instructions)
        zf.writestr("conversation-starters.txt", "\n".join(STARTERS) + "\n")
        zf.writestr("gem-config.json", json.dumps(config, indent=2) + "\n")
        zf.writestr("knowledge/pedagogy.md", pedagogy)
        zf.writestr("knowledge/fields.md", fields)
        zf.writestr("README.md", GEM_README)
    print("wrote %s (6 files)" % out)


def main() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    build_skill(OUT_DIR / "expert-mentor-skill.zip")
    build_agensi(OUT_DIR / "expert-mentor-agensi.zip")
    build_gpt_pack(OUT_DIR / "chatgpt-gpt-pack.zip")
    build_gem_pack(OUT_DIR / "gemini-gem-pack.zip")
    (OUT_DIR / "INSTALL.md").write_text(INSTALL_MD, encoding="utf-8")
    print("wrote %s" % (OUT_DIR / "INSTALL.md"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
