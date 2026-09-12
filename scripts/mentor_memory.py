#!/usr/bin/env python3
"""Persistent learner profiles and session transcripts for expert-mentor.

A *learner* is a named profile keyed to a field. It records what the learner has
mastered, what is still shaky, known misconceptions, and open questions, so the
mentor can adapt across sessions instead of starting from zero every time.

Everything is stored as plain JSON/markdown under the expert-mentor config dir:

    ~/.config/expert-mentor/learners/<name>.json
    ~/.config/expert-mentor/sessions/<timestamp>-<name>.md
    ~/.config/expert-mentor/sessions/<timestamp>-<name>.json
"""
from __future__ import annotations

import datetime
import json
import re
from dataclasses import asdict, dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional

LEARNER_HISTORY_MARKER = "<!-- expert-mentor:learner-history -->"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "learner"


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Learner:
    name: str
    field: str = ""
    level: str = "beginner"
    goal: str = ""
    created: str = ""
    updated: str = ""
    sessions: int = 0
    mastered: List[str] = dc_field(default_factory=list)
    shaky: List[str] = dc_field(default_factory=list)
    misconceptions: List[str] = dc_field(default_factory=list)
    open_questions: List[str] = dc_field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict) -> "Learner":
        known = {f: data.get(f) for f in cls.__dataclass_fields__ if f in data}
        learner = cls(name=data.get("name", "learner"))
        for key, value in known.items():
            if value is not None:
                setattr(learner, key, value)
        return learner

    def to_dict(self) -> Dict:
        return asdict(self)

    def has_history(self) -> bool:
        return bool(self.mastered or self.shaky or self.misconceptions
                    or self.open_questions or self.notes or self.sessions)


class Memory:
    def __init__(self, base: Path):
        self.base = Path(base)
        self.learners_dir = self.base / "learners"
        self.sessions_dir = self.base / "sessions"

    # -- learners -------------------------------------------------------- #
    def _path(self, name: str) -> Path:
        return self.learners_dir / f"{slugify(name)}.json"

    def exists(self, name: str) -> bool:
        return self._path(name).exists()

    def load(self, name: str) -> Optional[Learner]:
        path = self._path(name)
        if not path.exists():
            return None
        try:
            return Learner.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return None

    def load_or_create(self, name: str, field_name: str = "", level: str = "",
                       goal: str = "") -> Learner:
        learner = self.load(name)
        if learner is None:
            learner = Learner(name=slugify(name), field=field_name,
                              level=level or "beginner", goal=goal, created=_now())
        if field_name:
            learner.field = field_name
        if level:
            learner.level = level
        if goal:
            learner.goal = goal
        return learner

    def save(self, learner: Learner) -> Path:
        self.learners_dir.mkdir(parents=True, exist_ok=True)
        learner.name = slugify(learner.name)
        learner.updated = _now()
        path = self._path(learner.name)
        path.write_text(json.dumps(learner.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def list_learners(self) -> List[Learner]:
        if not self.learners_dir.exists():
            return []
        learners = []
        for path in sorted(self.learners_dir.glob("*.json")):
            try:
                learners.append(Learner.from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, OSError):
                continue
        return learners

    # -- sessions -------------------------------------------------------- #
    def add_session(self, learner: Optional[Learner], messages: List[Dict],
                    provider: str = "", model: str = "", field_name: str = "") -> Optional[Path]:
        if not messages:
            return None
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        who = slugify(learner.name) if learner else "unsaved"
        stem = f"{stamp}-{who}"
        transcript = [
            f"# Session — {learner.name if learner else who} — {stamp}",
            "",
            f"- Field: {field_name or (learner.field if learner else '')}",
            f"- Provider: {provider} · Model: {model}",
            f"- Turns: {sum(1 for m in messages if m.get('role') == 'user')}",
            "",
        ]
        for message in messages:
            role = "you" if message.get("role") == "user" else "mentor"
            transcript.append(f"**{role}:** {message.get('content', '').strip()}")
            transcript.append("")
        text = "\n".join(transcript)
        md_path = self.sessions_dir / f"{stem}.md"
        md_path.write_text(text, encoding="utf-8")
        meta = {
            "id": stem,
            "learner": learner.name if learner else who,
            "field": field_name or (learner.field if learner else ""),
            "provider": provider,
            "model": model,
            "turns": sum(1 for m in messages if m.get("role") == "user"),
            "created": _now(),
        }
        (self.sessions_dir / f"{stem}.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        return md_path

    def list_sessions(self, learner_name: Optional[str] = None) -> List[Dict]:
        if not self.sessions_dir.exists():
            return []
        sessions: List[Dict] = []
        for path in sorted(self.sessions_dir.glob("*.json")):
            try:
                meta = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if learner_name and meta.get("learner") != slugify(learner_name):
                continue
            sessions.append(meta)
        return sessions

    def transcript_path(self, session_id: str) -> Optional[Path]:
        candidate = self.sessions_dir / f"{session_id}.md"
        if candidate.exists():
            return candidate
        matches = list(self.sessions_dir.glob(f"*{session_id}*.md")) if self.sessions_dir.exists() else []
        return matches[0] if matches else None


def render_learner_section(learner: Learner) -> str:
    def join(items: List[str], sep: str = "; ") -> str:
        return sep.join(items) if items else "—"

    return "\n".join([
        "# LEARNER HISTORY (persisted across sessions)",
        "",
        "You have mentored this learner before. Honour this history: do not re-teach",
        "what is already mastered, and deliberately revisit what is shaky or misconceived.",
        "",
        f"- Learner: {learner.name}",
        f"- Field: {learner.field or '—'}",
        f"- Current level: {learner.level or '—'}",
        f"- Goal: {learner.goal or 'not stated'}",
        f"- Sessions so far: {learner.sessions}",
        f"- Mastered: {join(learner.mastered)}",
        f"- Shaky / needs review: {join(learner.shaky)}",
        f"- Known misconceptions: {join(learner.misconceptions)}",
        f"- Open questions: {join(learner.open_questions)}",
        f"- Notes: {learner.notes or '—'}",
    ])


def inject_learner_history(text: str, section: str) -> str:
    """Insert a rendered learner section into an already-rendered prompt."""
    if not section:
        return text
    if LEARNER_HISTORY_MARKER in text:
        return text.replace(LEARNER_HISTORY_MARKER, section)
    index = text.rfind("Begin now")
    if index != -1:
        line_start = text.rfind("\n", 0, index) + 1
        return text[:line_start] + section + "\n\n" + text[line_start:]
    return text.rstrip() + "\n\n" + section + "\n"


LIST_FIELDS = ("mastered", "shaky", "misconceptions", "open_questions")
VALID_LEVELS = ("beginner", "intermediate", "advanced", "expert")


def extract_json(text: str) -> Optional[Dict]:
    """Pull a JSON object out of model output, tolerating markdown fences."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidate = text[start:end + 1]
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def apply_updates(learner: Learner, data: Dict) -> List[str]:
    """Merge an assessment into a learner profile. Returns human-readable diffs."""
    changes: List[str] = []
    for key in LIST_FIELDS:
        incoming = data.get(key)
        if not isinstance(incoming, list):
            continue
        bucket = getattr(learner, key)
        lower = {existing.lower() for existing in bucket}
        for item in incoming:
            item = str(item).strip()
            if item and item.lower() not in lower:
                bucket.append(item)
                lower.add(item.lower())
                changes.append(f"+ {key}: {item}")

    mastered_lower = {m.lower() for m in learner.mastered}
    for item in list(learner.shaky):
        if item.lower() in mastered_lower:
            learner.shaky.remove(item)
            changes.append(f"- shaky: {item} (now mastered)")

    level = data.get("level")
    if isinstance(level, str) and level in VALID_LEVELS and level != learner.level:
        changes.append(f"level: {learner.level} -> {level}")
        learner.level = level

    notes = data.get("notes")
    if isinstance(notes, str) and notes.strip() and notes.strip() not in learner.notes:
        learner.notes = (learner.notes + "\n" + notes.strip()).strip() if learner.notes else notes.strip()
        changes.append("notes updated")

    return changes
