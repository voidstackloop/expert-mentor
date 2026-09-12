#!/usr/bin/env python3
"""Spaced-repetition flashcards for expert-mentor.

Cards are stored per learner as plain JSON:

    ~/.config/expert-mentor/learners/<name>.cards.json

Scheduling is an SM-2-lite algorithm: each card tracks its interval (days),
ease factor, repetition count, and next due date. Reviewing a card with a grade
of again/hard/good/easy reschedules it.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional

GRADES = ("again", "hard", "good", "easy")
GRADE_SCORES = {"again": 0, "hard": 1, "good": 2, "easy": 3}
STAMP = "%Y-%m-%dT%H:%M:%SZ"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", (name or "").strip().lower()).strip("-")
    return slug or "learner"


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(moment: datetime.datetime) -> str:
    return moment.strftime(STAMP)


def _parse(stamp: str) -> Optional[datetime.datetime]:
    if not stamp:
        return None
    try:
        return datetime.datetime.strptime(stamp, STAMP).replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def make_id(front: str) -> str:
    digest = hashlib.sha1(front.strip().lower().encode("utf-8")).hexdigest()
    return digest[:10]


@dataclass
class Card:
    front: str
    back: str
    id: str = ""
    tags: List[str] = dc_field(default_factory=list)
    created: str = ""
    due: str = ""
    interval: float = 0.0   # days
    ease: float = 2.5
    reps: int = 0
    lapses: int = 0
    reviews: int = 0

    def __post_init__(self) -> None:
        if not self.id:
            self.id = make_id(self.front)
        if not self.created:
            self.created = _iso(_now())
        if not self.due:
            self.due = _iso(_now())

    @classmethod
    def from_dict(cls, data: Dict) -> "Card":
        names = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in names})

    def to_dict(self) -> Dict:
        return asdict(self)

    def is_due(self, now: Optional[datetime.datetime] = None) -> bool:
        due = _parse(self.due)
        if due is None:
            return True
        return due <= (now or _now())


def review(card: Card, grade: str, now: Optional[datetime.datetime] = None) -> Card:
    """Reschedule a card using an SM-2-lite algorithm. Returns the same card."""
    now = now or _now()
    score = GRADE_SCORES.get(grade, 2)
    card.reviews += 1

    if score == 0:  # again — relearn soon, ease penalty
        card.reps = 0
        card.lapses += 1
        card.ease = max(1.3, round(card.ease - 0.20, 2))
        card.interval = 0.0
        card.due = _iso(now + datetime.timedelta(minutes=10))
        return card

    if card.reps == 0:
        card.interval = 1.0
    elif card.reps == 1:
        card.interval = 6.0
    else:
        card.interval = max(1.0, card.interval * card.ease)

    if score == 1:  # hard — shorter interval, small ease penalty
        card.ease = max(1.3, round(card.ease - 0.15, 2))
        card.interval = max(1.0, card.interval * 0.6)
    elif score == 3:  # easy — longer interval, ease bonus
        card.ease = min(3.0, round(card.ease + 0.15, 2))
        card.interval = card.interval * 1.3

    card.reps += 1
    card.due = _iso(now + datetime.timedelta(days=card.interval))
    return card


class CardStore:
    def __init__(self, base: Path):
        self.base = Path(base)
        self.dir = self.base / "learners"

    def _path(self, learner: str) -> Path:
        return self.dir / f"{slugify(learner)}.cards.json"

    def load(self, learner: str) -> List[Card]:
        path = self._path(learner)
        if not path.exists():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        cards = raw.get("cards", raw) if isinstance(raw, dict) else raw
        if not isinstance(cards, list):
            return []
        return [Card.from_dict(item) for item in cards if isinstance(item, dict)]

    def save(self, learner: str, cards: List[Card]) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self._path(learner)
        payload = {"learner": slugify(learner), "cards": [c.to_dict() for c in cards]}
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def add(self, learner: str, front: str, back: str,
            tags: Optional[List[str]] = None) -> Card:
        cards = self.load(learner)
        existing = {c.id for c in cards}
        card = Card(front=front.strip(), back=back.strip(), tags=tags or [])
        if card.id in existing:
            for current in cards:
                if current.id == card.id:
                    current.back = card.back
                    current.tags = sorted(set(current.tags) | set(card.tags))
                    self.save(learner, cards)
                    return current
        cards.append(card)
        self.save(learner, cards)
        return card

    def remove(self, learner: str, card_id: str) -> bool:
        cards = self.load(learner)
        remaining = [c for c in cards if c.id != card_id and not c.front.lower().startswith(card_id.lower())]
        if len(remaining) == len(cards):
            return False
        self.save(learner, remaining)
        return True

    def due(self, learner: str, now: Optional[datetime.datetime] = None) -> List[Card]:
        return [c for c in self.load(learner) if c.is_due(now)]

    def stats(self, learner: str) -> Dict:
        cards = self.load(learner)
        now = _now()
        due = sum(1 for c in cards if c.is_due(now))
        return {
            "total": len(cards),
            "due": due,
            "learned": sum(1 for c in cards if c.reps >= 2),
            "lapses": sum(c.lapses for c in cards),
        }
