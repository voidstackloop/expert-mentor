#!/usr/bin/env python3
"""expert-mentor generator.

Turns a field name into a professional, provider-aware teaching system prompt.

Examples
--------
    mentor --field "quantum computing" --level beginner
    mentor --field "Rust" --provider ollama --emit modelfile
    mentor --field "contract law" --provider openai --emit json
    mentor fields
    mentor save rustbuddy --field "Rust"
    mentor interactive

No third-party dependencies. Python 3.8+.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional

try:
    import mentor_runtime
    import mentor_memory
    import mentor_cards
except ImportError:  # when imported without scripts/ on sys.path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import mentor_runtime
    import mentor_memory
    import mentor_cards

APP_NAME = "expert-mentor"
__version__ = "0.6.1"


def _resource_dir(*parts: str) -> Path:
    """Locate bundled resources in both repo and installed layouts."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.joinpath(*parts),                       # <repo>/templates
        here.joinpath(*parts),                              # packaged next to module
        Path(sys.prefix) / "share" / APP_NAME / Path(*parts),
        Path(sys.prefix) / "local" / "share" / APP_NAME / Path(*parts),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _resource_file(name: str) -> Path:
    """Locate a single bundled file (e.g. SKILL.md) in both repo and installed layouts."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / name,                        # <repo>/SKILL.md
        here / name,                                # packaged next to module
        Path(sys.prefix) / "share" / APP_NAME / name,
        Path(sys.prefix) / "local" / "share" / APP_NAME / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = _resource_dir("templates")
REFERENCES_DIR = _resource_dir("references")
SKILL_MD = _resource_file("SKILL.md")

CONFIG_DIR = Path(os.environ.get("EXPERT_MENTOR_HOME", str(Path.home() / ".config" / "expert-mentor")))
PROMPTS_DIR = CONFIG_DIR / "prompts"
MODELS_DIR = CONFIG_DIR / "models"

SKILL_LINK_DIRS = (
    Path.home() / ".claude" / "skills" / "expert-mentor",
    Path.home() / ".config" / "opencode" / "skills" / "expert-mentor",
    Path.home() / ".config" / "opencode" / "skill" / "expert-mentor",
)

LEVELS = ("beginner", "intermediate", "advanced", "expert")

CONFIG_KEYS = (
    "provider", "model", "level", "language", "style", "temperature",
    "learner", "prompt_format", "compact", "thinking", "reasoning_effort",
)

TEACHING_STYLES = {
    "socratic": "Socratic — lead with questions and make the learner reason their way to the answer.",
    "coaching": "Coaching — goal-oriented; anchor every lesson to the learner's real project.",
    "direct": "Direct instruction — explain clearly and efficiently, then immediately test.",
    "immersive": "Immersive — teach mostly through realistic problems, simulations, and role-play.",
}


def get_config() -> Dict:
    """Read ~/.config/expert-mentor/config.json (returns {} if absent/invalid)."""
    path = CONFIG_DIR / "config.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _color_enabled() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


_STATUS_COLORS = {"ok": "32", "warn": "33", "FAIL": "31", "info": "36"}


def status_label(status: str) -> str:
    label = f"{status:^4}"
    code = _STATUS_COLORS.get(status)
    if code and _color_enabled():
        return f"\033[{code}m{label}\033[0m"
    return label


# --------------------------------------------------------------------------- #
# Field profiles
# --------------------------------------------------------------------------- #
@dataclass
class FieldProfile:
    key: str
    aliases: List[str]
    mentor_name: str
    notes: str
    concepts: List[str] = dc_field(default_factory=list)
    misconceptions: List[str] = dc_field(default_factory=list)
    resources: List[str] = dc_field(default_factory=list)
    capstone: str = ""


BUILTIN_PROFILES: Dict[str, FieldProfile] = {
    "quantum-computing": FieldProfile(
        key="quantum computing",
        aliases=["quantum computing", "quantum mechanics computing", "quantum algorithms", "quantum information"],
        mentor_name="Dr. Amara Okafor",
        notes=(
            "Quantum computing sits on linear algebra and quantum mechanics. Insist on "
            "Dirac notation and unitary evolution before touching circuits. Separate the "
            "mathematical model (state vectors, density matrices) from the physical "
            "implementation (superconducting, trapped-ion, photonic). Always distinguish "
            "universal fault-tolerant machines from today's noisy intermediate-scale "
            "devices, and never present quantum speedups as magic — every claim should be "
            "tied to a complexity argument. Canonical anchors: Nielsen & Chuang "
            "'Quantum Computation and Quantum Information', Preskill's lecture notes."
        ),
        concepts=["Dirac notation", "qubits and superposition", "entanglement", "quantum gates",
                  "measurement", "Deutsch-Jozsa", "Grover", "Shor", "noise and error correction",
                  "NISQ hardware"],
        misconceptions=[
            "a qubit stores both 0 and 1 at once (it is a probability amplitude, not a value)",
            "quantum computers try all answers in parallel",
            "entanglement allows faster-than-light communication",
            "more qubits automatically means more power",
        ],
        resources=["Nielsen & Chuang, Quantum Computation and Quantum Information",
                   "Preskill, Quantum Computation lecture notes (Caltech)"],
        capstone="Implement Grover's search in Qiskit and measure the quadratic speedup against classical search.",
    ),
    "rust": FieldProfile(
        key="Rust",
        aliases=["rust", "rust programming", "rustlang"],
        mentor_name="Mara Kovacs",
        notes=(
            "Rust's difficulty is ownership, borrowing, and lifetimes — teach those before "
            "generics or async. Reason from the memory model, not from compiler-error "
            "whack-a-mole. Enforce idiomatic habits early: Result/Option over sentinels, "
            "iterators over index loops, newtypes over primitives, clippy-clean code. "
            "Distinguish 'compiles' from 'idiomatic' and hold the learner to the latter. "
            "Canonical anchors: 'The Rust Programming Language' (the Book), the standard "
            "library docs, and the Rustonomicon for unsafe."
        ),
        concepts=["ownership", "borrowing", "lifetimes", "traits and generics", "enums and pattern matching",
                  "error handling", "smart pointers", "concurrency and Send/Sync", "async/await", "unsafe"],
        misconceptions=[
            "Rc and Arc are interchangeable",
            "the borrow checker is just an obstacle to fight with clones",
            "async is a runtime rather than a language feature",
            "unsafe means the code is dangerous rather than that the compiler trusts you",
        ],
        resources=["The Rust Programming Language (the Book)", "Rust by Example", "the Rustonomicon"],
        capstone="Build a small multithreaded CLI that parses a file format, handles errors gracefully, and passes clippy with no warnings.",
    ),
    "organic-chemistry": FieldProfile(
        key="organic chemistry",
        aliases=["organic chemistry", "ochem", "organic chem"],
        mentor_name="Dr. Elena Marchetti",
        notes=(
            "Organic chemistry rewards mechanism over memorisation. For every reaction, "
            "push electrons: identify nucleophile and electrophile, draw curly arrows, and "
            "track stereochemistry. Connect structure to reactivity through electronegativity, "
            "resonance, induction, and sterics. Insist on clean arrow-pushing and correct "
            "3D reasoning; most learner errors are unstated assumptions about geometry or "
            "charge. Anchors: Clayden 'Organic Chemistry', Klein's mechanism practice."
        ),
        concepts=["bonding and hybridisation", "resonance and induction", "acids and bases",
                  "nucleophiles and electrophiles", "substitution and elimination",
                  "addition reactions", "carbonyl chemistry", "aromaticity", "stereochemistry",
                  "retrosynthesis"],
        misconceptions=[
            "reactions are memorised lists rather than electron flows",
            "stereochemistry is optional bookkeeping",
            "resonance structures are in equilibrium with each other",
            "a stronger acid always reacts faster in every context",
        ],
        resources=["Clayden, Greeves & Warren, Organic Chemistry", "Klein, Organic Chemistry as a Second Language"],
        capstone="Devise a retrosynthesis of a given target molecule and defend each disconnection with a mechanism.",
    ),
    "machine-learning": FieldProfile(
        key="machine learning",
        aliases=["machine learning", "ml", "deep learning", "statistical learning", "ai"],
        mentor_name="Dr. Tomas Lindqvist",
        notes=(
            "Ground every method in the bias-variance trade-off and the data-generating "
            "process. Always ask: what is the loss, what is the hypothesis class, how is it "
            "optimised, and how is generalisation measured? Kill the habit of reporting a "
            "single accuracy number; insist on proper splits, baselines, and error analysis. "
            "Separate the mathematics from the engineering, and never let a learner call a "
            "result 'state of the art' without a fair comparison. Anchors: Hastie et al. "
            "'Elements of Statistical Learning', Goodfellow et al. 'Deep Learning'."
        ),
        concepts=["learning theory and bias-variance", "linear and logistic regression",
                  "regularisation", "SVMs and kernels", "neural networks and backpropagation",
                  "CNNs and RNNs", "transformers and attention", "evaluation and cross-validation",
                  "overfitting and data leakage", "optimisation"],
        misconceptions=[
            "more data always fixes a modelling problem",
            "test accuracy alone proves a model is good",
            "neural networks learn like humans do",
            "correlation found by a model implies causation",
        ],
        resources=["Hastie, Tibshirani & Friedman, The Elements of Statistical Learning",
                   "Goodfellow, Bengio & Courville, Deep Learning"],
        capstone="Take a real dataset end to end: baseline, model, honest evaluation, and an error analysis write-up.",
    ),
    "macroeconomics": FieldProfile(
        key="macroeconomics",
        aliases=["macroeconomics", "macro", "macro econ"],
        mentor_name="Prof. Daniel Achebe",
        notes=(
            "Macroeconomics is models with assumptions, not facts. For every claim, force "
            "the learner to name the model (IS-LM, Solow, New Keynesian, etc.), its "
            "assumptions, and what it ignores. Distinguish short-run demand stories from "
            "long-run growth, and positive analysis from normative prescription. Demand "
            "fluency with the data: inflation, unemployment, GDP, interest rates, and what "
            "each does and does not measure. Anchors: Blanchard 'Macroeconomics', Mankiw, "
            "and current central-bank publications."
        ),
        concepts=["GDP and national accounts", "unemployment", "inflation", "monetary policy",
                  "fiscal policy", "IS-LM", "Phillips curve", "Solow growth", "business cycles",
                  "open-economy macro"],
        misconceptions=[
            "the economy is a household writ large",
            "a model's prediction is the same as a fact",
            "printing money always causes proportional inflation immediately",
            "government debt is analogous to personal debt",
        ],
        resources=["Blanchard, Macroeconomics", "Mankiw, Macroeconomics", "IMF and central-bank reports"],
        capstone="Explain a current policy debate using two competing models, stating each model's assumptions and predictions.",
    ),
    "contract-law": FieldProfile(
        key="contract law",
        aliases=["contract law", "contracts", "law of contract"],
        mentor_name="Nadia Rahman, J.D.",
        notes=(
            "Contracts is a doctrinal field: teach the elements, then how courts apply them "
            "to messy facts. Always ask 'what is the rule, what is the authority, and how "
            "does it apply here?'. Use IRAC (Issue, Rule, Application, Conclusion) as the "
            "backbone. Distinguish common law from statutory and UCC regimes, and drill the "
            "difference between formation, performance, breach, and remedies. This is "
            "education, not legal advice — flag that a licensed lawyer is required for real "
            "matters. Anchors: Farnsworth on Contracts, a current casebook, Restatement (Second)."
        ),
        concepts=["offer and acceptance", "consideration", "mutual assent", "defenses",
                  "statute of frauds", "parol evidence", "conditions", "breach",
                  "damages and remedies", "third-party rights"],
        misconceptions=[
            "any agreement is an enforceable contract",
            "a signature is always required",
            "consideration means payment",
            "breach automatically ends the contract",
        ],
        resources=["Farnsworth, Contracts", "Restatement (Second) of Contracts", "UCC Article 2"],
        capstone="Analyse a fact pattern with IRAC and predict the likely holding, citing the governing rule.",
    ),
}

GENERIC_CONCEPTS = [
    "the field's core vocabulary",
    "fundamental models and theories",
    "standard tools and workflows",
    "how experts solve problems",
    "common failure modes",
    "how to evaluate quality",
]


def _generic_profile(name: str) -> FieldProfile:
    return FieldProfile(
        key=name,
        aliases=[name.lower()],
        mentor_name="",
        notes=(
            f"Teach {name} the way a senior practitioner actually works. Establish the "
            "field's foundational vocabulary and models first, then move to standard tools "
            "and workflows, then to applied judgement and problem solving. For every "
            "technique, state when it applies and when it fails. Distinguish settled "
            "consensus from active debate, and point the learner at the field's real "
            "authoritative sources (textbooks, standards bodies, peer-reviewed venues, "
            "primary practitioners). Attack misconceptions directly with evidence, because "
            "in " + name + ", a confidently held wrong model blocks everything built on it."
        ),
        concepts=list(GENERIC_CONCEPTS),
        misconceptions=[
            "knowing terminology is the same as understanding",
            "one method works in every situation",
            "the field can be learned by memorisation alone",
        ],
        resources=[f"the leading textbook(s) and primary sources of {name}"],
        capstone=f"Complete one realistic {name} project end to end and defend the decisions made.",
    )


def load_profiles() -> Dict[str, FieldProfile]:
    profiles = dict(BUILTIN_PROFILES)
    extra = REFERENCES_DIR / "fields.json"
    if extra.exists():
        try:
            data = json.loads(extra.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover
            print(f"warning: could not read {extra}: {exc}", file=sys.stderr)
            data = {}
        for key, raw in data.items():
            profiles[key] = FieldProfile(
                key=raw.get("key", key),
                aliases=raw.get("aliases", [key]),
                mentor_name=raw.get("mentor_name", ""),
                notes=raw.get("notes", ""),
                concepts=raw.get("concepts", []),
                misconceptions=raw.get("misconceptions", []),
                resources=raw.get("resources", []),
                capstone=raw.get("capstone", ""),
            )
    return profiles


def resolve_profile(field_name: str, profiles: Dict[str, FieldProfile]) -> FieldProfile:
    needle = field_name.strip().lower()
    for key, profile in profiles.items():
        if needle == key.lower() or needle == profile.key.lower():
            return profile
        if needle in (a.lower() for a in profile.aliases):
            return profile
    # substring fallback
    for profile in profiles.values():
        if needle and (needle in profile.key.lower() or any(needle in a.lower() for a in profile.aliases)):
            return profile
    return _generic_profile(field_name.strip())


# --------------------------------------------------------------------------- #
# Mentor name
# --------------------------------------------------------------------------- #
_SURNAMES = ["Nakamura", "Silva", "Petrov", "Osei", "Haddad", "Larsen", "Moreau",
             "Ibrahim", "Novak", "Sharma", "Andersen", "Costa", "Weber", "Tanaka"]
_GIVEN = ["Dr. Layla", "Prof. Marcus", "Dr. Sofia", "Prof. Idris", "Dr. Hana",
          "Prof. Viktor", "Dr. Naledi", "Prof. Ana", "Dr. Yusuf", "Prof. Clara"]


def generate_mentor_name(field_name: str) -> str:
    seed = sum(ord(c) for c in field_name)
    return f"{_GIVEN[seed % len(_GIVEN)]} {_SURNAMES[(seed // 7) % len(_SURNAMES)]}"


# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #
@dataclass
class Provider:
    name: str
    temperature: float
    default_model: str
    capability_notes: str
    emit: str  # default emit kind


CLOUD_NOTES = (
    "You have a large context window and strong reasoning. Use it: maintain a detailed, "
    "persistent learner model across the whole session, draw rich cross-domain analogies, "
    "and generate varied practice problems. You may reference specific, real, verifiable "
    "sources — but only when you are confident they exist. Cite editions or versions when "
    "precision matters."
)

LOCAL_NOTES = (
    "You are running as a local model with a limited context window and limited reasoning. "
    "Compensate by being disciplined: follow the session flow exactly, keep replies short "
    "(roughly 200 words unless teaching one full concept), ask exactly one question per "
    "reply, and never produce long unbroken lists. Do not invent citations or precise "
    "facts — say 'I'm not certain' and describe how to verify. At the start of each reply, "
    "restate the learner's goal and current milestone in one line so context is not lost."
)

ANTHROPIC_NOTES = (
    CLOUD_NOTES
    + " You are Claude: favour structured prose and XML-style tags when they make the "
      "reasoning clearer, and separate private deliberation from what you show the learner."
)

OPENAI_NOTES = (
    CLOUD_NOTES
    + " You are ChatGPT: use clear markdown structure, be systematic, and keep the "
      "learner oriented with explicit next steps."
)

PROVIDERS: Dict[str, Provider] = {
    "generic": Provider("generic", 0.6, mentor_runtime.DEFAULT_MODELS["generic"], CLOUD_NOTES, "text"),
    "anthropic": Provider("anthropic", 0.7, mentor_runtime.DEFAULT_MODELS["anthropic"], ANTHROPIC_NOTES, "json"),
    "openai": Provider("openai", 0.7, mentor_runtime.DEFAULT_MODELS["openai"], OPENAI_NOTES, "json"),
    "google": Provider("google", 0.8, mentor_runtime.DEFAULT_MODELS["google"], CLOUD_NOTES, "json"),
    "ollama": Provider("ollama", 0.4, mentor_runtime.DEFAULT_MODELS["ollama"], LOCAL_NOTES, "modelfile"),
    "llamacpp": Provider("llamacpp", 0.4, mentor_runtime.DEFAULT_MODELS["llamacpp"], LOCAL_NOTES, "json"),
}

# Friendly names people actually type.
PROVIDER_ALIASES = {
    "claude": "anthropic",
    "anthropic-api": "anthropic",
    "chatgpt": "openai",
    "gpt": "openai",
    "oai": "openai",
    "openai-api": "openai",
    "gemini": "google",
    "local": "ollama",
}


def canonical_provider(name: str) -> str:
    return PROVIDER_ALIASES.get(name, name)


PROVIDER_CHOICES = sorted(set(PROVIDERS) | set(PROVIDER_ALIASES))


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def build_field_notes(profile: FieldProfile) -> str:
    parts: List[str] = []
    if profile.notes:
        parts.append(profile.notes.strip())
    if profile.concepts:
        parts.append("Core concepts to sequence:\n"
                     + "\n".join(f"- {c}" for c in profile.concepts))
    if profile.misconceptions:
        parts.append("Misconceptions to hunt down and dismantle:\n"
                     + "\n".join(f"- {m}" for m in profile.misconceptions))
    if profile.resources:
        parts.append("Point the learner at real authorities:\n"
                     + "\n".join(f"- {r}" for r in profile.resources))
    if profile.capstone:
        parts.append(f"Capstone evidence of competence: {profile.capstone}")
    return "\n\n".join(parts)


def render(template: str, values: Dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    return out


def build_values(args: argparse.Namespace, profile: FieldProfile) -> Dict[str, str]:
    field_name = profile.key or args.field
    mentor_name = args.mentor_name or profile.mentor_name or generate_mentor_name(field_name)
    style = TEACHING_STYLES.get(args.style, TEACHING_STYLES["socratic"])
    level = args.level or "beginner"
    language = args.language or "the language the learner writes in"
    context = args.context or "Not specified — establish it during intake."
    goal = args.goal or f"Build durable, practical competence in {field_name}."

    if args.compact:
        length_rule = "Be concise: short paragraphs, no filler, under 200 words unless one full concept needs more."
        tone = "warm and direct"
    else:
        length_rule = ("Explain only as much as the concept needs, then stop. Break long explanations into short "
                       "paragraphs; use headings and lists only when they help.")
        tone = "warm, direct, and professional — encouraging without flattery"

    return {
        "MENTOR_NAME": mentor_name,
        "FIELD": field_name,
        "LEVEL": level,
        "LEARNER_CONTEXT": context,
        "SESSION_GOAL": goal,
        "LANGUAGE": language,
        "TEACHING_STYLE": style,
        "FIELD_NOTES": build_field_notes(profile),
        "TONE": tone,
        "LENGTH_RULE": length_rule,
        "CAPABILITY_NOTES": args._provider.capability_notes,
        "DURATION": getattr(args, "duration", None) or "8 weeks at 4-6 hours per week (adjust to fit)",
        "LEARNER_HISTORY": getattr(args, "_learner_history", ""),
    }


def extract_prompt(text: str) -> str:
    """Return only the prompt body, dropping the template's instructional header.

    The template carries an explanation above a banner of '=' lines and the line
    'SYSTEM PROMPT'. Everything after that banner is the real system prompt.
    """
    lines = text.splitlines()
    seps = [i for i, ln in enumerate(lines) if ln.strip().startswith("=====")]
    if len(seps) >= 2:
        body = lines[seps[1] + 1:]
        while body and not body[0].strip():
            body.pop(0)
        return "\n".join(body).rstrip() + "\n"
    return text


def load_template(compact: bool, curriculum: bool = False) -> str:
    if curriculum:
        name = "curriculum_prompt.md"
    elif compact:
        name = "compact_prompt.md"
    else:
        name = "mentor_system_prompt.md"
    path = TEMPLATES_DIR / name
    if path.exists():
        return extract_prompt(path.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"template not found: {path}. Expected {name} inside {TEMPLATES_DIR}."
    )


# --------------------------------------------------------------------------- #
# Emitters
# --------------------------------------------------------------------------- #
def emit_text(prompt: str, args: argparse.Namespace) -> str:
    return prompt


def emit_markdown(prompt: str, args: argparse.Namespace) -> str:
    header = (
        f"# Expert Mentor — {args._profile.key}\n\n"
        f"> Generated for provider **{args._provider.name}** · level **{args.level or 'beginner'}** · "
        f"temperature **{args._provider.temperature}**\n\n"
        f"---\n\n## System prompt\n\n```text\n{prompt.strip()}\n```\n"
    )
    return header


def emit_json(prompt: str, args: argparse.Namespace) -> str:
    provider = args._provider.name
    temp = args._provider.temperature
    model = args.model or args._provider.default_model
    begin = [{"role": "user", "content": "Begin."}]

    if provider == "anthropic":
        payload = mentor_runtime.build_anthropic_payload(
            model, prompt.strip(), begin, temperature=temp, stream=False,
            max_tokens=args.max_tokens,
            thinking_budget=args.thinking_budget if args.thinking else None,
            cache=not args.no_cache)
    elif provider == "openai":
        payload = mentor_runtime.build_openai_payload(
            model, prompt.strip(), begin, temperature=temp, stream=False,
            max_tokens=args.max_tokens, reasoning_effort=args.reasoning_effort)
    elif provider == "google":
        payload = {
            "model": model,
            "generationConfig": {"temperature": temp, "maxOutputTokens": args.max_tokens},
            "systemInstruction": {"parts": [{"text": prompt.strip()}]},
            "contents": [{"role": "user", "parts": [{"text": "Begin."}]}],
        }
    elif provider == "llamacpp":
        payload = {
            "system_prompt": prompt.strip(),
            "temperature": temp,
            "n_ctx": args.num_ctx,
            "max_tokens": args.max_tokens,
        }
    else:
        payload = {
            "model": model,
            "temperature": temp,
            "system": prompt.strip(),
        }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def emit_modelfile(prompt: str, args: argparse.Namespace) -> str:
    base = args.model or args._provider.default_model
    escaped = prompt.strip().replace('"""', '\\"\\"\\"')
    return (
        f"# Ollama Modelfile — generated by expert-mentor\n"
        f"# Build with:  ollama create expert-mentor -f Modelfile\n"
        f"# Run with:    ollama run expert-mentor\n"
        f"FROM {base}\n\n"
        f"PARAMETER temperature {args._provider.temperature}\n"
        f"PARAMETER num_ctx {args.num_ctx}\n"
        f"PARAMETER top_p 0.9\n\n"
        f'SYSTEM """{escaped}"""\n'
    )


EMITTERS = {
    "text": emit_text,
    "markdown": emit_markdown,
    "json": emit_json,
    "modelfile": emit_modelfile,
}


# --------------------------------------------------------------------------- #
# Helpers + subcommands
# --------------------------------------------------------------------------- #
def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", name.strip().lower()).strip("-")
    return slug or "mentor"


def get_memory() -> "mentor_memory.Memory":
    return mentor_memory.Memory(CONFIG_DIR)


def get_card_store() -> "mentor_cards.CardStore":
    return mentor_cards.CardStore(CONFIG_DIR)


def shape_prompt(text: str, provider: str, mode: str = "auto") -> str:
    """Adapt the prompt to the target model's preferred structure.

    ``auto`` uses XML-style section tags for Claude and plain markdown for the
    rest. ``xml`` / ``markdown`` force a specific shape.
    """
    if mode == "auto":
        mode = "xml" if provider == "anthropic" else "markdown"
    if mode != "xml":
        return text

    heading = re.compile(r"^#\s+(.+?)\s*$")
    lines: List[str] = []
    open_tag: Optional[str] = None
    for line in text.splitlines():
        match = heading.match(line)
        if match:
            if open_tag:
                lines.append(f"</{open_tag}>")
            tag = re.sub(r"[^a-z0-9]+", "_", match.group(1).lower()).strip("_") or "section"
            open_tag = tag
            lines.append(f"<{tag}>")
            lines.append(line)
        else:
            lines.append(line)
    if open_tag:
        lines.append(f"</{open_tag}>")
    return "\n".join(lines)


def prepare(args: argparse.Namespace) -> tuple:
    """Fill provider/profile, render the template, and emit the chosen format."""
    profiles = load_profiles()
    args.provider = canonical_provider(args.provider)
    args._provider = PROVIDERS[args.provider]
    args._profile = resolve_profile(args.field, profiles)
    args._learner_history = ""
    learner_name = getattr(args, "learner", None)
    if learner_name:
        existing = get_memory().load(learner_name)
        if existing and existing.has_history():
            args._learner_history = mentor_memory.render_learner_section(existing)
    template = load_template(args.compact, curriculum=getattr(args, "_curriculum", False))
    prompt = render(template, build_values(args, args._profile))
    prompt = shape_prompt(prompt, args.provider, args.prompt_format)
    emit_kind = args.emit or args._provider.emit
    return EMITTERS[emit_kind](prompt, args), emit_kind


def run_doctor() -> int:
    healthy = True
    print(f"{APP_NAME} doctor — v{__version__}\n")

    def line(status: str, msg: str) -> None:
        print(f"  [{status_label(status)}] {msg}")

    if sys.version_info >= (3, 8):
        line("ok", f"python {sys.version.split()[0]}")
    else:
        line("FAIL", f"python {sys.version.split()[0]} (need >= 3.8)")
        healthy = False

    for name in ("mentor_system_prompt.md", "compact_prompt.md"):
        present = (TEMPLATES_DIR / name).exists()
        line("ok" if present else "FAIL", f"template: {name}")
        healthy = healthy and present

    line("ok" if REFERENCES_DIR.exists() else "warn", f"references: {REFERENCES_DIR}")

    if shutil.which("ollama"):
        line("ok", "ollama found — local model deployment available")
    else:
        line("warn", "ollama not found — optional, install from https://ollama.com")

    bin_dir = Path.home() / ".local" / "bin"
    on_path = str(bin_dir) in os.environ.get("PATH", "").split(os.pathsep)
    line("ok" if on_path else "warn", f"{bin_dir} on PATH")

    linked = next((p for p in SKILL_LINK_DIRS if p.exists()), None)
    line("ok" if linked else "warn",
         f"skill linked: {linked}" if linked else "skill not installed yet — run 'mentor skill'")

    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        line("ok", f"config dir writable: {CONFIG_DIR}")
    except OSError as exc:
        line("FAIL", f"config dir not writable: {exc}")
        healthy = False

    mentor_runtime.load_env()
    for prov in ("anthropic", "openai"):
        key = mentor_runtime.api_key(prov)
        line("ok" if key else "warn",
             f"{prov} API key {'set' if key else 'not set'} · default model {mentor_runtime.DEFAULT_MODELS[prov]}")

    memory = get_memory()
    try:
        line("ok", f"learners: {len(memory.list_learners())} · "
                   f"sessions: {len(memory.list_sessions())}")
    except OSError:
        line("warn", "could not read the learner store")

    print()
    print("healthy" if healthy else "problems found — fix the FAIL lines above")
    return 0 if healthy else 1


def _require_field(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if not args.field:
        parser.error("--field is required")


def run_save_command(rest: List[str]) -> int:
    if not rest:
        print("usage: mentor save <name> --field <field> [--level ...] [--provider ...]", file=sys.stderr)
        return 2
    name, rest = rest[0], rest[1:]
    parser = build_parser()
    args = parser.parse_args(rest)
    _require_field(parser, args)
    args.emit = "text"
    prompt_text, _ = prepare(args)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(name)
    prompt_path = PROMPTS_DIR / f"{slug}.md"
    meta_path = PROMPTS_DIR / f"{slug}.json"
    prompt_path.write_text(
        f"<!-- expert-mentor: {slug} · field={args._profile.key} · level={args.level or 'beginner'} · "
        f"provider={args.provider} · style={args.style} -->\n\n{prompt_text}",
        encoding="utf-8",
    )
    meta_path.write_text(json.dumps({
        "name": slug,
        "field": args._profile.key,
        "level": args.level or "beginner",
        "provider": args.provider,
        "model": args._provider.default_model,
        "style": args.style,
        "temperature": args._provider.temperature,
        "compact": bool(args.compact),
    }, indent=2), encoding="utf-8")
    print(f"saved mentor: {prompt_path}")
    print(f"show it:      mentor show {slug}")
    print(f"reuse it:     paste {prompt_path} as the system prompt, or run 'mentor show {slug}'")
    return 0


def run_show_command(rest: List[str]) -> int:
    if not rest:
        print("usage: mentor show <name>", file=sys.stderr)
        return 2
    path = PROMPTS_DIR / f"{slugify(rest[0])}.md"
    if not path.exists():
        print(f"no saved mentor named '{rest[0]}' (try 'mentor saved')", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def run_saved_command(_: List[str]) -> int:
    if not PROMPTS_DIR.exists() or not any(PROMPTS_DIR.glob("*.md")):
        print("no saved mentors yet. create one: mentor save mytutor --field \"...\"")
        return 0
    print(f"saved mentors in {PROMPTS_DIR}:\n")
    for path in sorted(PROMPTS_DIR.glob("*.md")):
        meta = path.with_suffix(".json")
        detail = ""
        if meta.exists():
            try:
                data = json.loads(meta.read_text(encoding="utf-8"))
                detail = f"  ({data.get('field')}, {data.get('level')}, {data.get('provider')})"
            except json.JSONDecodeError:
                pass
        print(f"  {path.stem}{detail}")
    return 0


def run_ollama_command(rest: List[str]) -> int:
    if not rest:
        print("usage: mentor ollama <name> --field <field> [--level ...] [--compact] [--model ...]",
              file=sys.stderr)
        return 2
    name, rest = rest[0], rest[1:]
    parser = build_parser()
    args = parser.parse_args(rest)
    _require_field(parser, args)
    args.provider = "ollama"
    args.emit = "modelfile"
    modelfile_text, _ = prepare(args)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(name)
    path = MODELS_DIR / f"{slug}.Modelfile"
    path.write_text(modelfile_text, encoding="utf-8")
    print(f"wrote {path}")

    if shutil.which("ollama"):
        print(f"creating ollama model '{slug}' ...")
        result = subprocess.run(["ollama", "create", slug, "-f", str(path)])
        if result.returncode == 0:
            print(f"\ndone. run it with:  ollama run {slug}")
            return 0
        print(f"\nollama create failed (exit {result.returncode}); Modelfile kept at {path}")
        return result.returncode
    print(f"\nollama is not installed. Install it, then run:\n  ollama create {slug} -f {path}")
    return 0


def run_skill_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="mentor skill", add_help=True,
                                     description="Install the Claude Code / opencode agent skill "
                                                 "(works for pip/pipx installs, not just git checkouts).")
    parser.add_argument("--dir", action="append", metavar="PATH",
                        help="install into PATH/expert-mentor instead of the default locations "
                             "(repeatable)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing skill directory that isn't already ours")
    opts = parser.parse_args(rest)

    if not SKILL_MD.exists():
        print(f"SKILL.md not found (looked near {SKILL_MD}); nothing to install", file=sys.stderr)
        return 1

    # Git checkout: symlink the whole repo, same as install.sh (stays live as the repo changes).
    # Installed package (pip/pipx): no repo to point at, so copy the bundled files instead.
    is_checkout = (ROOT / "install.sh").exists()
    targets = ([Path(d).expanduser() / "expert-mentor" for d in opts.dir] if opts.dir
               else list(SKILL_LINK_DIRS[:2]))

    installed = 0
    for target in targets:
        already_ours = target.is_symlink() or (target / "SKILL.md").exists()
        if target.exists() or target.is_symlink():
            if not already_ours and not opts.force:
                print(f"skip {target} (exists; pass --force to overwrite)", file=sys.stderr)
                continue
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)

        if is_checkout:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(ROOT, target_is_directory=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SKILL_MD, target / "SKILL.md")
            for name, resolved in (("templates", TEMPLATES_DIR), ("references", REFERENCES_DIR)):
                if resolved.exists():
                    shutil.copytree(resolved, target / name, dirs_exist_ok=True)
        print(f"installed skill: {target}")
        installed += 1

    if not installed:
        return 1
    print("\nRestart Claude Code / opencode (or start a new session) to pick it up.")
    return 0


def run_models_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="mentor models", add_help=True)
    parser.add_argument("--provider", choices=sorted(set(PROVIDERS) | set(PROVIDER_ALIASES)))
    parser.add_argument("--refresh", action="store_true",
                        help="query the provider's API for live model IDs (needs an API key)")
    opts = parser.parse_args(rest)
    providers = [canonical_provider(opts.provider)] if opts.provider else ["anthropic", "openai"]

    for provider in providers:
        print(f"{provider}:")
        if opts.refresh:
            try:
                ids = mentor_runtime.list_models(provider)
                for model_id in ids:
                    print(f"  {model_id}")
                continue
            except mentor_runtime.MentorRuntimeError as exc:
                print(f"  (live lookup failed: {exc})")
                print("  falling back to the built-in catalog:")
        for model_id, note in mentor_runtime.MODEL_CATALOG.get(provider, []):
            default = " (default)" if model_id == mentor_runtime.DEFAULT_MODELS.get(provider) else ""
            print(f"  {model_id}{default} — {note}")
        print()
    print("Use --refresh with an API key set to list the models your account can actually call.")
    return 0


def _coerce_config_value(value: str):
    low = value.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("none", "null", ""):
        return None
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def run_config_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="mentor config", add_help=True,
        description="View or edit ~/.config/expert-mentor/config.json defaults.")
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--unset", action="append", default=[], metavar="KEY")
    parser.add_argument("--reset", action="store_true")
    opts = parser.parse_args(rest)

    data = get_config()
    changed = False
    if opts.reset:
        data = {}
        changed = True
    for pair in opts.set:
        if "=" not in pair:
            print(f"ignoring '{pair}' (expected KEY=VALUE)", file=sys.stderr)
            continue
        key, _, value = pair.partition("=")
        key = key.strip()
        if key not in CONFIG_KEYS:
            print(f"warning: '{key}' is not a known key ({', '.join(CONFIG_KEYS)})", file=sys.stderr)
        data[key] = _coerce_config_value(value)
        changed = True
    for key in opts.unset:
        if data.pop(key.strip(), None) is not None:
            changed = True

    if changed:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        (CONFIG_DIR / "config.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"saved {CONFIG_DIR / 'config.json'}\n")

    print(f"config: {CONFIG_DIR / 'config.json'}")
    if data:
        for key in sorted(data):
            print(f"  {key} = {data[key]}")
    else:
        print("  (empty — defaults are used)")
    print(f"\nknown keys: {', '.join(CONFIG_KEYS)}")
    return 0


def _print_learner(learner: "mentor_memory.Learner") -> None:
    print(f"{learner.name}")
    print(f"  field:        {learner.field or '—'}")
    print(f"  level:        {learner.level or '—'}")
    print(f"  goal:         {learner.goal or '—'}")
    print(f"  sessions:     {learner.sessions}")
    print(f"  mastered:     {', '.join(learner.mastered) or '—'}")
    print(f"  shaky:        {', '.join(learner.shaky) or '—'}")
    print(f"  misconceptions: {'; '.join(learner.misconceptions) or '—'}")
    print(f"  open questions: {'; '.join(learner.open_questions) or '—'}")
    print(f"  notes:        {learner.notes or '—'}")
    print(f"  updated:      {learner.updated or '—'}")


def run_learners_command(_: List[str]) -> int:
    learners = get_memory().list_learners()
    if not learners:
        print("no learners yet. Start one with:")
        print("  mentor run --field 'Rust' --remember")
        return 0
    print("learners:\n")
    for learner in learners:
        print(f"  {learner.name:<22} {learner.field:<26} level={learner.level:<12} sessions={learner.sessions}")
    print("\nInspect one with: mentor progress <name>")
    return 0


def run_progress_command(rest: List[str]) -> int:
    if not rest:
        print("usage: mentor progress <name> [--field F] [--level L] [--goal G] [--note N]\n"
              "       [--add-mastered X] [--add-shaky X] [--add-misconception X] [--add-question X] [--reset]",
              file=sys.stderr)
        return 2
    name, rest = rest[0], rest[1:]
    parser = argparse.ArgumentParser(prog="mentor progress", add_help=True)
    parser.add_argument("--field")
    parser.add_argument("--level")
    parser.add_argument("--goal")
    parser.add_argument("--note")
    parser.add_argument("--add-mastered", action="append", default=[])
    parser.add_argument("--add-shaky", action="append", default=[])
    parser.add_argument("--add-misconception", action="append", default=[])
    parser.add_argument("--add-question", action="append", default=[])
    parser.add_argument("--reset", action="store_true")
    opts = parser.parse_args(rest)

    memory = get_memory()
    learner = memory.load(name)
    if learner is None:
        learner = memory.load_or_create(name, field_name=opts.field or "",
                                        level=opts.level or "", goal=opts.goal or "")

    changed = False
    if opts.reset:
        learner.mastered, learner.shaky, learner.misconceptions, learner.open_questions = [], [], [], []
        changed = True
    for attr, values in (("mastered", opts.add_mastered), ("shaky", opts.add_shaky),
                         ("misconceptions", opts.add_misconception),
                         ("open_questions", opts.add_question)):
        bucket = getattr(learner, attr)
        for value in values:
            if value and value not in bucket:
                bucket.append(value)
                changed = True
    for attr in ("field", "level", "goal", "note"):
        value = getattr(opts, attr)
        if value:
            setattr(learner, "notes" if attr == "note" else attr, value)
            changed = True

    if changed or not memory.exists(name):
        memory.save(learner)
    _print_learner(learner)
    return 0


def run_sessions_command(rest: List[str]) -> int:
    name = rest[0] if rest else None
    sessions = get_memory().list_sessions(name)
    if not sessions:
        print("no sessions recorded yet.")
        return 0
    print("sessions:\n")
    for session in sessions:
        print(f"  {session.get('id'):<34} {session.get('field',''):<24} "
              f"turns={session.get('turns',0):<3} {session.get('provider','')}/{session.get('model','')}")
    print("\nRead one with: mentor transcript <id>")
    return 0


def run_transcript_command(rest: List[str]) -> int:
    if not rest:
        print("usage: mentor transcript <session-id>", file=sys.stderr)
        return 2
    path = get_memory().transcript_path(rest[0])
    if path is None:
        print(f"no transcript matching '{rest[0]}' (try 'mentor sessions')", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def _review_system_prompt(field_name: str, provider: str) -> str:
    path = TEMPLATES_DIR / "review_prompt.md"
    text = extract_prompt(path.read_text(encoding="utf-8"))
    profile = resolve_profile(field_name, load_profiles()) if field_name else None
    values = {
        "MENTOR_NAME": (profile.mentor_name if profile and profile.mentor_name
                        else (generate_mentor_name(field_name) if field_name else "the assessor")),
        "FIELD": field_name or "the subject",
        "CAPABILITY_NOTES": PROVIDERS[provider].capability_notes,
    }
    return render(text, values)


def run_review_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="mentor review", add_help=True,
        description="Assess a session transcript and update the learner profile.")
    parser.add_argument("learner", nargs="?", help="learner profile to review")
    parser.add_argument("--session", help="specific session id (default: latest for the learner)")
    parser.add_argument("--apply", action="store_true", help="write the updates to the profile")
    parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    parser.add_argument("--model")
    parser.add_argument("--host")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--dry-run", action="store_true", help="print the review prompt, call nothing")
    opts = parser.parse_args(rest)

    memory = get_memory()
    if opts.session:
        path = memory.transcript_path(opts.session)
        if path is None:
            print(f"no transcript matching '{opts.session}'", file=sys.stderr)
            return 1
        learner_name = opts.learner
    elif opts.learner:
        sessions = memory.list_sessions(opts.learner)
        if not sessions:
            print(f"no sessions recorded for '{opts.learner}'", file=sys.stderr)
            return 1
        path = memory.transcript_path(sessions[-1]["id"])
        learner_name = opts.learner
    else:
        parser.error("give a learner name or --session <id>")

    meta: Dict = {}
    meta_path = path.with_suffix(".json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}

    learner = None
    if learner_name:
        learner = memory.load(learner_name) or memory.load_or_create(learner_name)
    field_name = (learner.field if learner else "") or meta.get("field", "")

    provider = canonical_provider(opts.provider or meta.get("provider") or "ollama")
    if provider not in ("ollama", "llamacpp", "openai", "anthropic", "google"):
        print(f"provider '{provider}' has no runtime backend; pass --provider", file=sys.stderr)
        return 2
    model = opts.model or meta.get("model") or mentor_runtime.DEFAULT_MODELS.get(provider, "")
    temperature = opts.temperature if opts.temperature is not None else 0.2

    transcript = path.read_text(encoding="utf-8")
    system = _review_system_prompt(field_name, provider)

    if opts.dry_run:
        print("=== system ===")
        print(system)
        print("\n=== user (transcript) ===")
        print(transcript)
        return 0

    kwargs: Dict = {}
    if provider in ("ollama", "llamacpp") and opts.host:
        kwargs["host"] = opts.host
    try:
        raw = mentor_runtime.complete(provider, model, system,
                                      [{"role": "user", "content": transcript}],
                                      temperature=temperature, **kwargs)
    except mentor_runtime.MentorRuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    data = mentor_memory.extract_json(raw)
    if data is None:
        print("could not parse the model's assessment as JSON. Raw output:\n")
        print(raw)
        return 1

    print(f"review of {path.name}")
    if data.get("summary"):
        print(f"\nsummary: {data['summary']}")
    if data.get("next_lesson"):
        print(f"next lesson: {data['next_lesson']}")

    if learner is None:
        print("\n(no learner profile — pass a learner name with --apply to save these)")
        return 0

    changes = mentor_memory.apply_updates(learner, data)
    print("\nproposed changes:")
    print("\n".join(f"  {line}" for line in changes) if changes else "  (no changes)")
    if opts.apply:
        memory.save(learner)
        print(f"\napplied to learner '{learner.name}'")
    else:
        print("\n(run with --apply to save)")
    return 0


def _cards_system_prompt(field_name: str, provider: str) -> str:
    path = TEMPLATES_DIR / "cards_prompt.md"
    text = extract_prompt(path.read_text(encoding="utf-8"))
    profile = resolve_profile(field_name, load_profiles()) if field_name else None
    values = {
        "MENTOR_NAME": (profile.mentor_name if profile and profile.mentor_name
                        else (generate_mentor_name(field_name) if field_name else "the teacher")),
        "FIELD": field_name or "the subject",
        "CAPABILITY_NOTES": PROVIDERS[provider].capability_notes,
    }
    return render(text, values)


def run_cards_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="mentor cards", add_help=True,
        description="Manage spaced-repetition flashcards for a learner.")
    parser.add_argument("learner")
    parser.add_argument("--add", metavar="FRONT :: BACK", help="add a card manually")
    parser.add_argument("--tags", default="", help="comma-separated tags for --add")
    parser.add_argument("--generate", action="store_true", help="build cards from the latest session")
    parser.add_argument("--session", help="specific session id for --generate")
    parser.add_argument("--remove", metavar="ID", help="remove a card by id")
    parser.add_argument("--reset", action="store_true", help="delete all cards for the learner")
    parser.add_argument("--provider", choices=PROVIDER_CHOICES)
    parser.add_argument("--model")
    parser.add_argument("--host")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--dry-run", action="store_true", help="show the generation prompt, call nothing")
    opts = parser.parse_args(rest)
    store = get_card_store()

    if opts.reset:
        store.save(opts.learner, [])
        print(f"cleared cards for '{opts.learner}'")
        return 0
    if opts.remove:
        print("removed" if store.remove(opts.learner, opts.remove) else "no such card")
        return 0
    if opts.add:
        if "::" not in opts.add:
            print('expected: --add "FRONT :: BACK"', file=sys.stderr)
            return 2
        front, _, back = opts.add.partition("::")
        tags = [t.strip() for t in opts.tags.split(",") if t.strip()]
        card = store.add(opts.learner, front, back, tags)
        print(f"added card {card.id}: {card.front}")
        return 0
    if opts.generate:
        return _generate_cards(opts, store)

    cards = store.load(opts.learner)
    stats = store.stats(opts.learner)
    if not cards:
        print(f"no cards for '{opts.learner}' yet. Try:")
        print(f'  mentor cards {opts.learner} --add "What is ownership? :: ..."')
        print(f"  mentor cards {opts.learner} --generate")
        return 0
    print(f"{opts.learner}: {stats['total']} cards · {stats['due']} due · {stats['learned']} learned"
          f" · {stats['lapses']} lapses\n")
    for card in cards:
        mark = "*" if card.is_due() else " "
        done = f"due {card.due[:10]}"
        print(f"  [{mark}] {card.id}  {card.front}  (reps={card.reps}, {done})")
    print("\n* = due now. Review with: mentor quiz " + opts.learner)
    return 0


def _generate_cards(opts: argparse.Namespace, store: "mentor_cards.CardStore") -> int:
    memory = get_memory()
    if opts.session:
        path = memory.transcript_path(opts.session)
    else:
        sessions = memory.list_sessions(opts.learner)
        if not sessions:
            print(f"no sessions recorded for '{opts.learner}' — run a session first", file=sys.stderr)
            return 1
        path = memory.transcript_path(sessions[-1]["id"])
    if path is None:
        print("could not find a transcript to generate from", file=sys.stderr)
        return 1

    meta: Dict = {}
    meta_path = path.with_suffix(".json")
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}
    learner = memory.load(opts.learner)
    field_name = (learner.field if learner else "") or meta.get("field", "")

    provider = canonical_provider(opts.provider or meta.get("provider") or "ollama")
    if provider not in ("ollama", "llamacpp", "openai", "anthropic", "google"):
        print(f"provider '{provider}' has no runtime backend; pass --provider", file=sys.stderr)
        return 2
    model = opts.model or meta.get("model") or mentor_runtime.DEFAULT_MODELS.get(provider, "")
    temperature = opts.temperature if opts.temperature is not None else 0.3
    system = _cards_system_prompt(field_name, provider)
    transcript = path.read_text(encoding="utf-8")

    if opts.dry_run:
        print("=== system ===")
        print(system)
        print("\n=== user (transcript) ===")
        print(transcript)
        return 0

    kwargs: Dict = {}
    if provider in ("ollama", "llamacpp") and opts.host:
        kwargs["host"] = opts.host
    try:
        raw = mentor_runtime.complete(provider, model, system,
                                      [{"role": "user", "content": transcript}],
                                      temperature=temperature, **kwargs)
    except mentor_runtime.MentorRuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    data = mentor_memory.extract_json(raw)
    if not data or not isinstance(data.get("cards"), list):
        print("could not parse flashcards from the model output. Raw output:\n")
        print(raw)
        return 1

    added = 0
    for item in data["cards"]:
        if not isinstance(item, dict):
            continue
        front = str(item.get("front", "")).strip()
        back = str(item.get("back", "")).strip()
        if front and back:
            store.add(opts.learner, front, back, item.get("tags") or [])
            added += 1
    print(f"generated {added} card(s) for '{opts.learner}' (from {path.name})")
    print(f"review with: mentor quiz {opts.learner}")
    return 0


def run_quiz_command(rest: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="mentor quiz", add_help=True,
        description="Review due flashcards with spaced repetition.")
    parser.add_argument("learner")
    parser.add_argument("--n", type=int, default=10, help="maximum cards this session (default: 10)")
    parser.add_argument("--all", action="store_true", help="include cards that are not due yet")
    parser.add_argument("--shuffle", action="store_true", help="randomise the order")
    opts = parser.parse_args(rest)

    store = get_card_store()
    cards = store.load(opts.learner)
    queue = cards if opts.all else [c for c in cards if c.is_due()]
    if opts.shuffle:
        random.shuffle(queue)
    queue = queue[:max(0, opts.n)]

    if not queue:
        stats = store.stats(opts.learner)
        if stats["total"] == 0:
            print(f"no cards for '{opts.learner}'. Create some with 'mentor cards {opts.learner} --generate'.")
        else:
            print(f"nothing due for '{opts.learner}' ({stats['total']} cards). Use --all to review anyway.")
        return 0

    print(f"quiz · {opts.learner} · {len(queue)} card(s)\n")
    reviewed = 0
    try:
        for index, card in enumerate(queue, 1):
            print(f"[{index}/{len(queue)}] {card.front}")
            try:
                input("  (Enter to reveal) ")
            except EOFError:
                break
            print(f"  → {card.back}")
            try:
                raw = input("  grade [again/hard/good/easy] (Enter=good, q=quit): ").strip().lower()
            except EOFError:
                raw = "good"
            if raw in ("q", "quit", "exit"):
                break
            grade = raw if raw in mentor_cards.GRADES else "good"
            mentor_cards.review(card, grade)
            reviewed += 1
            print()
    except KeyboardInterrupt:
        print()
    store.save(opts.learner, cards)
    print(f"reviewed {reviewed} card(s). Next due dates updated.")
    return 0


def _load_saved_prompt(name: str) -> tuple:
    slug = slugify(name)
    path = PROMPTS_DIR / f"{slug}.md"
    if not path.exists():
        return None, {}
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].lstrip().startswith("<!--"):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    meta: Dict = {}
    meta_path = PROMPTS_DIR / f"{slug}.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            meta = {}
    return "\n".join(lines).strip() + "\n", meta


def run_curriculum_command(rest: List[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(rest)
    _require_field(parser, args)
    args._curriculum = True
    if not args.emit:
        args.emit = "markdown"
    output, emit_kind = prepare(args)
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"wrote {args.out} ({len(output)} bytes) · curriculum · emit={emit_kind}")
    else:
        print(output)
    return 0


def _stream_kwargs(provider: str, args: argparse.Namespace) -> Dict:
    kwargs: Dict = {}
    if provider in ("ollama", "llamacpp") and args.host:
        kwargs["host"] = args.host
    if provider == "openai":
        kwargs["reasoning_effort"] = args.reasoning_effort
    if provider == "anthropic":
        kwargs["thinking_budget"] = args.thinking_budget if args.thinking else None
        kwargs["cache"] = not args.no_cache
    return kwargs


def _print_usage(usage: Dict, quiet: bool = False) -> None:
    if not usage or quiet:
        return
    order = ("input_tokens", "cache_read_tokens", "output_tokens", "total_tokens")
    parts = [f"{k}={usage[k]}" for k in order if k in usage]
    parts += [f"{k}={v}" for k, v in usage.items() if k not in order]
    if parts:
        print(f"[usage] {'  '.join(parts)}", file=sys.stderr)


def run_run_command(rest: List[str]) -> int:
    name: Optional[str] = None
    if rest and not rest[0].startswith("-"):
        name, rest = rest[0], rest[1:]
    parser = build_parser()
    args = parser.parse_args(rest)

    meta: Dict = {}
    provider_explicit = any(a == "--provider" or a.startswith("--provider=") for a in rest)
    if name:
        system_prompt, meta = _load_saved_prompt(name)
        if system_prompt is None:
            print(f"no saved mentor named '{name}' (try 'mentor saved')", file=sys.stderr)
            return 1
        provider = canonical_provider(args.provider if provider_explicit else meta.get("provider", "generic"))
        label = name
    else:
        _require_field(parser, args)
        args.emit = "text"
        system_prompt, _ = prepare(args)
        provider = args.provider
        label = args._profile.key

    runtime_providers = {"ollama", "llamacpp", "openai", "anthropic", "google"}
    if provider not in runtime_providers:
        print(
            f"provider '{provider}' cannot run a live session.\n"
            f"Pick one of: {', '.join(sorted(runtime_providers))}.\n"
            f"Example: mentor run {name or '<name>'} --provider ollama --model llama3.1:8b",
            file=sys.stderr,
        )
        return 2

    # --- persistent learner model -------------------------------------- #
    memory = get_memory()
    learner = None
    learner_name = getattr(args, "learner", None)
    if not learner_name and getattr(args, "remember", False):
        target_field = args.field or meta.get("field")
        if not target_field:
            print("--remember needs --field (or pass --learner NAME)", file=sys.stderr)
            return 2
        learner_name = slugify(target_field)
    if learner_name:
        learner = memory.load_or_create(
            learner_name,
            field_name=args.field or meta.get("field", ""),
            level=args.level or "",
            goal=args.goal or "",
        )
        if learner.has_history():
            system_prompt = mentor_memory.inject_learner_history(
                system_prompt, mentor_memory.render_learner_section(learner))

    model = args.model or meta.get("model") or mentor_runtime.DEFAULT_MODELS.get(provider, "")
    temperature = (args.temperature if args.temperature is not None
                   else meta.get("temperature", PROVIDERS[provider].temperature))
    kwargs = _stream_kwargs(provider, args)

    if args.dry_run:
        sample_messages = [{"role": "user", "content": args.once or "Begin."}]
        if provider == "anthropic":
            payload = mentor_runtime.build_anthropic_payload(
                model, system_prompt, sample_messages, temperature, stream=True,
                max_tokens=args.max_tokens, thinking_budget=kwargs.get("thinking_budget"),
                cache=kwargs.get("cache", True))
        elif provider == "openai":
            payload = mentor_runtime.build_openai_payload(
                model, system_prompt, sample_messages, temperature, stream=True,
                max_tokens=args.max_tokens, reasoning_effort=kwargs.get("reasoning_effort"),
                include_usage=True)
        elif provider == "llamacpp":
            payload = mentor_runtime.build_openai_payload(
                model, system_prompt, sample_messages, temperature, stream=True,
                max_tokens=args.max_tokens)
        elif provider == "google":
            payload = mentor_runtime.build_google_payload(
                model, system_prompt, sample_messages, temperature, max_tokens=args.max_tokens)
        else:
            payload = mentor_runtime.build_ollama_payload(
                model, system_prompt, sample_messages, temperature, max_tokens=args.max_tokens)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    def turn(messages: List[Dict]) -> tuple:
        limit = max(2, args.history_turns * 2)
        payload = messages[-limit:] if len(messages) > limit else messages
        chunks: List[str] = []
        usage: Dict = {}
        for event in mentor_runtime.stream(provider, model, system_prompt, payload,
                                           temperature=temperature, max_tokens=args.max_tokens,
                                           **kwargs):
            kind = event.get("type")
            if kind == "text":
                sys.stdout.write(event["text"])
                sys.stdout.flush()
                chunks.append(event["text"])
            elif kind == "thinking" and args.show_thinking:
                sys.stderr.write(f"\033[2m{event['text']}\033[0m")
                sys.stderr.flush()
            elif kind == "usage":
                usage.update(event.get("usage", {}))
        return "".join(chunks), usage

    def save_progress(session_messages: List[Dict]) -> None:
        if learner is None or not session_messages:
            return
        learner.sessions += 1
        path = memory.add_session(learner, session_messages, provider, model,
                                  args.field or learner.field)
        memory.save(learner)
        if path and not args.quiet:
            print(f"[saved] learner '{learner.name}' → {path}", file=sys.stderr)

    if args.once:
        session_messages = [{"role": "user", "content": args.once}]
        print(f"{label} › ", end="")
        try:
            reply, usage = turn(session_messages)
        except mentor_runtime.MentorRuntimeError as exc:
            print(f"\n[error] {exc}", file=sys.stderr)
            return 1
        print()
        _print_usage(usage, args.quiet)
        if reply:
            session_messages.append({"role": "assistant", "content": reply})
        save_progress(session_messages)
        return 0

    header = f"expert-mentor · {label} · provider={provider} · model={model}"
    if learner is not None:
        header += f" · learner={learner.name} (session {learner.sessions + 1})"
    print(header)
    print("Commands: /reset  /exit   (Ctrl-C to quit)\n")
    messages: List[Dict] = []
    try:
        while True:
            try:
                user = input("you › ")
            except EOFError:
                break
            if not user.strip():
                continue
            if user.strip() in ("/exit", "/quit"):
                break
            if user.strip() == "/reset":
                messages = []
                print("(history cleared)")
                continue
            messages.append({"role": "user", "content": user})
            print(f"\n{label} › ", end="")
            try:
                reply, usage = turn(messages)
            except mentor_runtime.MentorRuntimeError as exc:
                print(f"\n[error] {exc}")
                messages.pop()
                continue
            print()
            _print_usage(usage, args.quiet)
            messages.append({"role": "assistant", "content": reply})
    except KeyboardInterrupt:
        print()
    save_progress(messages)
    return 0


COMMANDS = ("version", "fields", "providers", "doctor", "interactive", "prompt",
            "save", "show", "saved", "ollama", "curriculum", "run", "models",
            "learners", "progress", "sessions", "transcript", "review", "config",
            "cards", "quiz", "skill")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    cfg = get_config()
    p = argparse.ArgumentParser(
        prog="mentor",
        description="Generate an expert-mentor system prompt for any LLM provider.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Commands:\n"
               "  mentor --field 'quantum computing' --level beginner   # generate a prompt\n"
               "  mentor prompt --field 'Rust' --provider claude --emit json\n"
               "  mentor save rustbuddy --field 'Rust' --level intermediate\n"
               "  mentor run rustbuddy --reasoning-effort high          # live session\n"
               "  mentor run --field 'Rust' --provider chatgpt --remember\n"
               "  mentor curriculum --field 'Rust' --duration '6 weeks'\n"
               "  mentor models --provider claude --refresh\n"
               "  mentor learners | progress <name> | review <name> | quiz <name>\n"
               "  mentor cards <name> [--add \"Q :: A\"] [--generate]\n"
               "  mentor config | fields | providers | saved | doctor | interactive | version\n",
    )
    p.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    p.add_argument("--field", help="the field to teach")
    p.add_argument("--level", choices=LEVELS, default=cfg.get("level"),
                   help="learner level (default: beginner)")
    p.add_argument("--goal", help="the learner's objective")
    p.add_argument("--context", help="the learner's background / prior knowledge")
    p.add_argument("--language", default=cfg.get("language"), help="teaching language")
    p.add_argument("--style", choices=sorted(TEACHING_STYLES), default=cfg.get("style", "socratic"),
                   help="teaching style")
    p.add_argument("--mentor-name", help="override the generated mentor name")
    p.add_argument("--provider", choices=PROVIDER_CHOICES, default=cfg.get("provider", "generic"),
                   help="target provider (claude/chatgpt are aliases for anthropic/openai)")
    p.add_argument("--model", default=cfg.get("model"), help="override the target model id")
    p.add_argument("--emit", choices=sorted(EMITTERS), help="output format (default depends on provider)")
    p.add_argument("--compact", action="store_true", default=bool(cfg.get("compact", False)),
                   help="short prompt for small-context local models")
    p.add_argument("--max-tokens", type=int, default=2048, help="max_tokens for JSON outputs (default: 2048)")
    p.add_argument("--num-ctx", type=int, default=8192, help="context size for Modelfile/llamacpp (default: 8192)")
    p.add_argument("--out", help="write output to a file instead of stdout")
    p.add_argument("-q", "--quiet", action="store_true", help="suppress usage/save notices")
    p.add_argument("--list-fields", action="store_true", help="list curated field profiles and exit")
    p.add_argument("--list-providers", action="store_true", help="list supported providers and exit")
    p.add_argument("--interactive", action="store_true", help="prompt for the essentials")
    # curriculum
    p.add_argument("--duration", help="study duration for 'curriculum' (e.g. '6 weeks, 5h/week')")
    # live session ('run' command)
    p.add_argument("--once", help="'run': send a single message and exit")
    p.add_argument("--dry-run", action="store_true", help="'run': print the request payload, send nothing")
    p.add_argument("--host", help="'run': backend host for ollama/llamacpp (e.g. http://localhost:11434)")
    p.add_argument("--temperature", type=float, default=cfg.get("temperature"),
                   help="'run': sampling temperature (defaults per provider)")
    # provider-native shaping and reasoning controls
    p.add_argument("--prompt-format", choices=("auto", "markdown", "xml"),
                   default=cfg.get("prompt_format", "auto"),
                   help="prompt shape: auto (xml for Claude), markdown, or xml")
    p.add_argument("--thinking", action="store_true", default=bool(cfg.get("thinking", False)),
                   help="Anthropic: enable extended thinking (uses --thinking-budget)")
    p.add_argument("--thinking-budget", type=int, default=4096,
                   help="Anthropic: extended thinking token budget (default: 4096)")
    p.add_argument("--reasoning-effort", "--effort", dest="reasoning_effort",
                   choices=("none", "minimal", "low", "medium", "high", "xhigh", "max"),
                   default=cfg.get("reasoning_effort"),
                   help="OpenAI reasoning models: reasoning effort")
    p.add_argument("--no-cache", action="store_true",
                   help="Anthropic: do not mark the system prompt for prompt caching")
    p.add_argument("--show-thinking", action="store_true",
                   help="'run': show model reasoning/thinking as it streams (dimmed, stderr)")
    p.add_argument("--history-turns", type=int, default=40,
                   help="'run': max past turns kept in context (default: 40)")
    # persistent learner
    p.add_argument("--learner", default=cfg.get("learner"),
                   help="'run'/'prompt': load and update a named learner profile")
    p.add_argument("--remember", action="store_true",
                   help="'run': auto-name the learner from --field and persist progress")
    return p


def interactive(args: argparse.Namespace) -> None:
    def ask(label: str, default: str = "") -> str:
        suffix = f" [{default}]" if default else ""
        try:
            answer = input(f"{label}{suffix}: ").strip()
        except EOFError:
            answer = ""
        return answer or default

    print("expert-mentor — build a teacher for any field.\n")
    args.field = ask("Field", args.field)
    args.level = ask("Level (beginner/intermediate/advanced/expert)", args.level)
    args.goal = ask("Learner's goal", args.goal or "")
    args.context = ask("Learner's background", args.context or "")
    args.language = ask("Language", args.language or "")
    args.style = ask("Style (socratic/coaching/direct/immersive)", args.style)
    args.provider = ask("Provider (" + "/".join(sorted(PROVIDERS)) + ")", args.provider)


def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] in COMMANDS:
        command, rest = argv[0], argv[1:]
        if command == "version":
            print(f"{APP_NAME} {__version__}")
            return 0
        if command == "fields":
            argv = ["--list-fields"] + rest
        elif command == "providers":
            argv = ["--list-providers"] + rest
        elif command == "interactive":
            argv = ["--interactive"] + rest
        elif command == "doctor":
            return run_doctor()
        elif command == "save":
            return run_save_command(rest)
        elif command == "show":
            return run_show_command(rest)
        elif command == "saved":
            return run_saved_command(rest)
        elif command == "ollama":
            return run_ollama_command(rest)
        elif command == "skill":
            return run_skill_command(rest)
        elif command == "models":
            return run_models_command(rest)
        elif command == "learners":
            return run_learners_command(rest)
        elif command == "progress":
            return run_progress_command(rest)
        elif command == "sessions":
            return run_sessions_command(rest)
        elif command == "transcript":
            return run_transcript_command(rest)
        elif command == "review":
            return run_review_command(rest)
        elif command == "cards":
            return run_cards_command(rest)
        elif command == "quiz":
            return run_quiz_command(rest)
        elif command == "config":
            return run_config_command(rest)
        elif command == "curriculum":
            return run_curriculum_command(rest)
        elif command == "run":
            return run_run_command(rest)
        elif command == "prompt":
            argv = rest

    parser = build_parser()
    args = parser.parse_args(argv)

    profiles = load_profiles()

    if args.list_fields:
        print("Curated field profiles:\n")
        for profile in profiles.values():
            aliases = ", ".join(profile.aliases)
            print(f"  - {profile.key}  ({aliases})")
        print("\nAdd your own in references/fields.json (see references/fields.md).")
        return 0

    if args.list_providers:
        print("Supported providers:\n")
        for prov in PROVIDERS.values():
            print(f"  {prov.name:<10} temperature={prov.temperature}  default_emit={prov.emit}  model={prov.default_model}")
        return 0

    if args.interactive:
        interactive(args)

    if not args.field:
        parser.error("--field is required (or use a command: fields, providers, doctor, save, ollama, interactive)")

    output, emit_kind = prepare(args)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        if not args.quiet:
            print(f"wrote {args.out} ({len(output)} bytes) · provider={args.provider} · emit={emit_kind}")
    else:
        print(output)
    return 0


def cli(argv: Optional[List[str]] = None) -> int:
    """Entry point wrapper: clean handling of interrupts and runtime errors."""
    try:
        return main(argv)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except BrokenPipeError:
        try:
            sys.stdout.close()
        except OSError:
            pass
        return 0
    except mentor_runtime.MentorRuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
