#!/usr/bin/env python3
"""Self-test for the expert-mentor generator.

Run:  python3 scripts/selftest.py
Exits non-zero on any failure. No third-party dependencies.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import expert_mentor as em  # noqa: E402

PASS = 0
FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ok   {label}")
    else:
        FAIL += 1
        print(f"FAIL   {label}")


def generate(field: str, provider: str, emit: str, compact: bool = False, **kw):
    argv = ["--field", field, "--provider", provider, "--emit", emit]
    if compact:
        argv.append("--compact")
    for key, val in kw.items():
        flag = "--" + key.replace("_", "-")
        if isinstance(val, bool):
            if val:
                argv.append(flag)
        else:
            argv += [flag, str(val)]
    parser = em.build_parser()
    # mimic main() without printing
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = em.main(argv)
    return code, buf.getvalue()


def main() -> int:
    import io
    from contextlib import redirect_stdout as _rso
    print("expert-mentor self-test\n")

    print("resolver:")
    profiles = em.load_profiles()
    check("exact alias match", em.resolve_profile("ochem", profiles).key == "organic chemistry")
    check("rust alias", em.resolve_profile("rustlang", profiles).key == "Rust")
    check("ml alias", em.resolve_profile("deep learning", profiles).key == "machine learning")
    check("unknown -> generic", em.resolve_profile("interpretive dance", profiles).key == "interpretive dance")

    print("\ntext/markdown:")
    code, out = generate("quantum computing", "generic", "markdown", level="beginner")
    check("exit 0", code == 0)
    check("has system prompt", "TEACHING CONTRACT" in out)
    check("mentor named", "Dr. Amara Okafor" in out)
    check("field notes present", "Nielsen & Chuang" in out)
    check("no unfilled placeholders", "{{" not in out and "}}" not in out)

    print("\ncompact:")
    code, out = generate("Rust", "ollama", "text", compact=True, level="intermediate")
    check("exit 0", code == 0)
    check("compact marker", "RULES (follow every reply)" in out)
    check("local capability notes", "limited context window" in out)
    check("no long contract", "PHASE" not in out.upper().replace("FLOW", ""))

    print("\njson providers:")
    for provider, required in (
        ("anthropic", {"model", "system", "messages", "temperature"}),
        ("openai", {"model", "messages"}),
        ("google", {"model", "systemInstruction", "contents"}),
        ("llamacpp", {"system_prompt", "temperature", "n_ctx"}),
    ):
        code, out = generate("contract law", provider, "json")
        try:
            payload = json.loads(out)
            ok = required.issubset(payload.keys())
            check(f"{provider}: valid json + keys", code == 0 and ok)
        except json.JSONDecodeError as exc:
            check(f"{provider}: valid json ({exc})", False)

    print("\nprovider-native shaping:")
    import mentor_runtime as mr
    _, anth = generate("contract law", "anthropic", "json")
    anth_payload = json.loads(anth)
    check("claude: system is cached block",
          isinstance(anth_payload.get("system"), list)
          and anth_payload["system"][0].get("cache_control", {}).get("type") == "ephemeral")
    check("claude: xml prompt shaping",
          "<the_teaching_contract>" in json.dumps(anth_payload))
    _, openai_reasoning = generate("contract law", "openai", "json", model="gpt-5.6")
    rp = json.loads(openai_reasoning)
    check("chatgpt reasoning: developer role", rp["messages"][0]["role"] == "developer")
    check("chatgpt reasoning: max_completion_tokens", "max_completion_tokens" in rp)
    check("chatgpt reasoning: no temperature", "temperature" not in rp)
    _, openai_legacy = generate("contract law", "openai", "json", model="gpt-4o")
    lp = json.loads(openai_legacy)
    check("chatgpt legacy: system role", lp["messages"][0]["role"] == "system")
    check("chatgpt legacy: max_tokens", "max_tokens" in lp and "temperature" in lp)
    _, thinking = generate("contract law", "claude", "json", thinking=True)
    check("claude: thinking block", json.loads(thinking).get("thinking", {}).get("type") == "enabled")

    print("\ncapabilities:")
    check("gpt-5.6 is reasoning",
          mr.capabilities("openai", "gpt-5.6").system_role == "developer")
    check("gpt-4o is not reasoning",
          mr.capabilities("openai", "gpt-4o").system_role == "system")
    check("claude caches system", mr.capabilities("anthropic", "claude-sonnet-5").cache_system)
    check("openai reasoning detects", mr.supports_thinking("openai", "o3-mini"))
    check("anthropic thinking detects", mr.supports_thinking("anthropic", "claude-haiku-4-5"))
    check("shape_prompt xml", "<identity>" in em.shape_prompt("# IDENTITY\nhi", "anthropic"))
    check("shape_prompt markdown passthrough",
          em.shape_prompt("# IDENTITY\nhi", "openai") == "# IDENTITY\nhi")
    check("provider alias claude", em.canonical_provider("claude") == "anthropic")
    check("provider alias chatgpt", em.canonical_provider("chatgpt") == "openai")
    with _rso(io.StringIO()):
        check("models command", em.main(["models", "--provider", "claude"]) == 0)

    print("\nmodelfile:")
    code, out = generate("organic chemistry", "ollama", "modelfile", model="qwen2.5:7b")
    check("exit 0", code == 0)
    check("FROM line", "FROM qwen2.5:7b" in out)
    check("SYSTEM block", 'SYSTEM """' in out)
    check("temperature pinned", "PARAMETER temperature 0.4" in out)

    print("\ngeneric fallback:")
    code, out = generate("interpretive dance", "generic", "text", level="advanced")
    check("exit 0", code == 0)
    check("mentions field", "interpretive dance" in out)
    check("no placeholder leak", "{{" not in out)

    print("\nedge cases:")
    code, out = generate("contract law", "anthropic", "json", level="expert",
                         mentor_name="Prof. Test", language="Turkish")
    check("custom mentor name", "Prof. Test" in out)
    check("custom language", "Turkish" in out)
    try:
        em.main(["--field", "x", "--level", "nonsense"])
        check("rejects bad level", False)
    except SystemExit as exc:
        check("rejects bad level", exc.code != 0)

    print("\ncommands:")
    import io
    from contextlib import redirect_stdout as _rso
    with _rso(io.StringIO()):
        check("version", em.main(["version"]) == 0)
    with _rso(io.StringIO()):
        check("doctor healthy", em.main(["doctor"]) == 0)
    check("slugify", em.slugify("My Tutor!!") == "my-tutor")

    old_prompts, old_config = em.PROMPTS_DIR, em.CONFIG_DIR
    with tempfile.TemporaryDirectory() as tmp:
        em.PROMPTS_DIR = Path(tmp) / "prompts"
        em.CONFIG_DIR = Path(tmp)
        try:
            with _rso(io.StringIO()):
                code = em.main(["save", "rustbuddy", "--field", "Rust", "--level", "intermediate"])
            check("save returns 0", code == 0)
            check("save wrote .md", (em.PROMPTS_DIR / "rustbuddy.md").exists())
            check("save wrote meta", (em.PROMPTS_DIR / "rustbuddy.json").exists())
            buf = io.StringIO()
            with _rso(buf):
                code = em.main(["show", "rustbuddy"])
            check("show returns 0", code == 0 and "TEACHING CONTRACT" in buf.getvalue())
            with _rso(io.StringIO()):
                code = em.main(["saved"])
            check("saved lists mentor", code == 0)
        finally:
            em.PROMPTS_DIR, em.CONFIG_DIR = old_prompts, old_config

    print("\ncurriculum:")
    with _rso(io.StringIO()):
        code = em.main(["curriculum", "--field", "Rust", "--duration", "6 weeks"])
    check("curriculum exit 0", code == 0)
    buf = io.StringIO()
    with _rso(buf):
        em.main(["curriculum", "--field", "Rust", "--emit", "text"])
    out = buf.getvalue()
    check("curriculum has workable prompt", "Outcome statement" in out and "curriculum" in out.lower())

    print("\nruntime payloads:")
    import mentor_runtime as mr
    check("ollama payload order",
          [m["role"] for m in mr.build_ollama_payload("m", "sys", [{"role": "user", "content": "hi"}])["messages"]]
          == ["system", "user"])
    check("anthropic separates system", "system" in mr.build_anthropic_payload("m", "sys", []))
    check("openai carries max_tokens", mr.build_openai_payload("m", "sys", [])["max_tokens"] == 2048)

    print("\nrun dry-run:")
    for provider in ("ollama", "openai", "anthropic"):
        buf = io.StringIO()
        with _rso(buf):
            code = em.main(["run", "--field", "Rust", "--provider", provider, "--dry-run", "--once", "hi"])
        try:
            payload = json.loads(buf.getvalue())
            check(f"{provider} dry-run valid json", code == 0 and "model" in payload)
        except json.JSONDecodeError:
            check(f"{provider} dry-run valid json", False)
    with _rso(io.StringIO()):
        code = em.main(["run", "--field", "Rust"])
    check("generic run refused", code == 2)

    print("\nlearner memory:")
    import mentor_memory as mm
    old_config = em.CONFIG_DIR
    with tempfile.TemporaryDirectory() as tmp:
        em.CONFIG_DIR = Path(tmp)
        try:
            mem = em.get_memory()
            learner = mem.load_or_create("rusty", field_name="Rust", level="intermediate", goal="ship code")
            learner.mastered.append("ownership")
            learner.misconceptions.append("Rc == Arc")
            mem.save(learner)
            loaded = mem.load("rusty")
            check("memory roundtrip", loaded is not None and loaded.mastered == ["ownership"])
            section = mm.render_learner_section(loaded)
            check("section mentions misconception", "Rc == Arc" in section)
            injected = mm.inject_learner_history("Rules.\n\nBegin now with Phase 1.", section)
            check("inject before Begin now",
                  injected.index("LEARNER HISTORY") < injected.index("Begin now"))
            check("session written",
                  mem.add_session(loaded, [{"role": "user", "content": "hi"}], "ollama", "test", "Rust") is not None)
            check("session listed", len(mem.list_sessions("rusty")) == 1)
            with _rso(io.StringIO()):
                code = em.main(["progress", "rusty", "--add-shaky", "lifetimes"])
            check("progress command", code == 0)
            check("progress persisted", "lifetimes" in em.get_memory().load("rusty").shaky)
            buf = io.StringIO()
            with _rso(buf):
                em.main(["--field", "Rust", "--learner", "rusty", "--emit", "text"])
            check("prompt carries learner history", "LEARNER HISTORY" in buf.getvalue())
            buf = io.StringIO()
            with _rso(buf):
                em.main(["learners"])
            check("learners lists profile", "rusty" in buf.getvalue())

            check("extract_json fenced",
                  mm.extract_json('```json\n{"mastered": ["ownership"]}\n```') == {"mastered": ["ownership"]})
            check("extract_json raw", mm.extract_json('noise {"level": "advanced"} tail')["level"] == "advanced")
            check("extract_json invalid", mm.extract_json("not json at all") is None)
            probe = mm.Learner(name="x")
            probe.shaky = ["ownership", "lifetimes"]
            changes = mm.apply_updates(probe, {"mastered": ["ownership"], "shaky": ["traits"],
                                               "level": "advanced", "notes": "solid basics"})
            check("apply adds mastered", "ownership" in probe.mastered)
            check("apply clears shaky on mastery", "ownership" not in probe.shaky)
            check("apply adds new shaky", "traits" in probe.shaky)
            check("apply sets level", probe.level == "advanced")
            check("apply stores notes", "solid basics" in probe.notes)
            check("apply reports a diff", any("mastered" in c for c in changes))
            with _rso(io.StringIO()):
                code = em.main(["review", "rusty", "--dry-run"])
            check("review dry-run", code == 0)
        finally:
            em.CONFIG_DIR = old_config

    print("\nconfig:")
    old_config = em.CONFIG_DIR
    with tempfile.TemporaryDirectory() as tmp:
        em.CONFIG_DIR = Path(tmp)
        try:
            with _rso(io.StringIO()):
                code = em.main(["config", "--set", "provider=claude", "--set", "level=advanced"])
            check("config set", code == 0)
            check("config file written", (em.CONFIG_DIR / "config.json").exists())
            parsed = em.build_parser().parse_args([])
            check("config default provider", parsed.provider == "claude")
            check("config default level", parsed.level == "advanced")
            buf = io.StringIO()
            with _rso(buf):
                em.main(["--field", "Rust", "--emit", "markdown"])
            check("config applied to output", "provider **anthropic**" in buf.getvalue())
            with _rso(io.StringIO()):
                code = em.main(["config", "--reset"])
            check("config reset", code == 0 and em.get_config() == {})
        finally:
            em.CONFIG_DIR = old_config

    print("\ncards & spaced repetition:")
    import mentor_cards as mc
    old_config = em.CONFIG_DIR
    with tempfile.TemporaryDirectory() as tmp:
        em.CONFIG_DIR = Path(tmp)
        try:
            store = em.get_card_store()
            card = store.add("rusty", "What is ownership?", "Each value has one owner.")
            check("card added", bool(card.id) and store.stats("rusty")["total"] == 1)
            check("new card is due", store.stats("rusty")["due"] == 1)
            mc.review(card, "good")
            check("good sets interval", card.reps == 1 and card.interval == 1.0)
            check("card no longer due", not card.is_due())
            mc.review(card, "again")
            check("again resets reps + lapse", card.reps == 0 and card.lapses == 1)
            check("again relearns soon", card.interval == 0.0)
            store.save("rusty", [card])
            check("card store roundtrip", len(store.load("rusty")) == 1)
            with _rso(io.StringIO()):
                code = em.main(["cards", "rusty", "--add", "What is a borrow? :: A reference."])
            check("cards --add", code == 0)
            buf = io.StringIO()
            with _rso(buf):
                em.main(["cards", "rusty"])
            check("cards list", "What is a borrow?" in buf.getvalue())
            old_stdin = sys.stdin
            sys.stdin = io.StringIO("\ngood\n")
            try:
                with _rso(io.StringIO()):
                    code = em.main(["quiz", "rusty", "--all", "--n", "1"])
                check("quiz runs", code == 0)
            finally:
                sys.stdin = old_stdin
            check("remove missing card is a no-op", store.remove("rusty", "zzzzz") is False)
            check("replace updates back", store.add("rusty", "What is a borrow?", "An alias.").back == "An alias.")
        finally:
            em.CONFIG_DIR = old_config

    print(f"\n{PASS} passed, {FAIL} failed")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
