---
name: expert-mentor
description: "Use when the user wants to learn, be taught, or be mentored in any field (e.g. 'teach me quantum computing', 'be my Rust mentor', 'explain macroeconomics like a professor'), or wants to turn a cloud AI provider (Claude/Anthropic, ChatGPT/OpenAI, Gemini) or local LLM (Ollama, LM Studio, llama.cpp) into a professional teacher for a given field. Produces a calibrated expert-mentor persona, a learning roadmap, a live tutoring session, or a full curriculum."
---

# Expert Mentor

Turn any capable model — a cloud provider (Anthropic, OpenAI, Google) or a local
LLM (Ollama, LM Studio, llama.cpp) — into a **professional teacher for a
user-specified field**. The mentor teaches to a standard a real senior
practitioner would recognise, and adapts to the learner in real time.

## Setup (one command)

```bash
cd ~/projects/expert-mentor
./install.sh          # or: make install
```

This installs the `mentor` command into `~/.local/bin`, links the skill into
`~/.claude/skills/expert-mentor` and `~/.config/opencode/skills/expert-mentor`,
adds `~/.local/bin` to PATH if needed, and runs a health check. Open a new
terminal (or `source ~/.bashrc`) and run `mentor doctor`.

No install needed? Run it in place with `./bin/mentor ...` or
`python3 scripts/expert_mentor.py ...`. Remove everything with `./uninstall.sh`.

Prefer an isolated, pip-managed install instead:

```bash
pipx install .        # or: pip install --user .
mentor version
```

Defaults can be saved so you stop retyping them:

```bash
mentor config --set provider=claude --set level=intermediate --set style=coaching
```

## When this skill activates

- The user names a field and asks to be taught, tutored, coached, or mentored.
- The user wants a system prompt / persona to make a specific model act as a
  teacher for a field.
- The user wants to configure a local LLM (Modelfile, LM Studio preset) as an
  expert mentor.

## Step 1 — Collect the essentials

You need, at minimum:

| Input | Required | Notes |
|-------|----------|-------|
| `field` | yes | e.g. "distributed systems", "Spanish literature", "day trading" |
| `level` | no | beginner / intermediate / advanced / expert — infer from context if absent |
| `goal` | no | what they want to be able to do |
| `context` | no | background, prior knowledge, time available |
| `language` | no | default: same language the user is writing in |
| `provider` | no | only needed when emitting a prompt/Modelfile for a specific model |

Do not interrogate the user. Infer sensible defaults from the conversation. If
the **field** itself is ambiguous (e.g. "AI" could be theory, engineering, or
policy), ask one clarifying question, then proceed.

## Step 2 — Choose the delivery mode

Pick based on what the user actually wants:

**A. Teach me now (default).** Adopt the persona inline and run the session in
this conversation. Load `templates/mentor_system_prompt.md`, fill the slots, and
follow it exactly. Start with **Phase 1 — Intake**, then build the roadmap.

**B. Give me a reusable prompt.** The user wants to paste a system prompt into
another chat or API. Generate it with the script (Step 3) and hand it over.

**C. Configure a provider or local model.** The user wants a deployable artefact
(system prompt, messages JSON, Ollama Modelfile, LM Studio preset). Generate it
with the script (Step 3).

**D. Build a curriculum.** The user wants a structured multi-week plan rather
than live tutoring. Generate a curriculum-design prompt with `mentor curriculum
--field F --duration "6 weeks, 5h/week"`, then either hand it off or have the
model produce the plan inline. Ground it in `references/pedagogy.md`.

## Step 3 — Generate the mentor prompt

The generator renders `templates/mentor_system_prompt.md` for a field, level,
and target provider, then emits it in the format that provider needs.

```bash
# Print a ready-to-paste system prompt (default: generic text)
mentor --field "quantum computing" --level beginner

# For a local model as an Ollama Modelfile
mentor --field "Rust" --level intermediate --provider ollama --emit modelfile > Modelfile

# Messages JSON for an OpenAI-compatible API
mentor --field "contract law" --provider openai --emit json

# Anthropic Messages API payload
mentor --field "organic chemistry" --provider anthropic --emit json

# Save a reusable mentor and reuse it later
mentor save rustbuddy --field "Rust" --level intermediate
mentor show rustbuddy

# Build and register a local model in one shot (needs ollama installed)
mentor ollama rusttutor --field "Rust" --compact
```

Without the installer, replace `mentor` with `python3 scripts/expert_mentor.py`.

Commands:

| Command | Purpose |
|---------|---------|
| `mentor --field F [...]` | generate a prompt (default text for the provider) |
| `mentor prompt --field F` | same, explicit form |
| `mentor save NAME --field F` | save a reusable system prompt under `~/.config/expert-mentor/prompts/` |
| `mentor show NAME` | print a saved mentor |
| `mentor saved` | list saved mentors |
| `mentor ollama NAME --field F` | write a Modelfile and run `ollama create NAME` |
| `mentor run [NAME] --field F` | start a live tutoring session (local or cloud) |
| `mentor curriculum --field F` | generate a full sequenced curriculum prompt |
| `mentor models [--provider P] [--refresh]` | list Claude/ChatGPT models (live lookup with a key) |
| `mentor config [--set K=V] [--unset K] [--reset]` | view/edit saved defaults |
| `mentor learners` | list persisted learner profiles |
| `mentor progress NAME [...]` | view/update a learner's mastered/shaky/misconception lists |
| `mentor review NAME [--apply]` | assess the latest transcript and update the learner profile |
| `mentor sessions [NAME]` | list recorded sessions |
| `mentor transcript ID` | print a session transcript |
| `mentor fields` | list curated field profiles |
| `mentor providers` | list providers and their defaults |
| `mentor doctor` | check the local setup |
| `mentor version` | print the version |
| `mentor interactive` | build a profile by answering prompts |

Useful flags:

| Flag | Purpose |
|------|---------|
| `--field` | the field to teach (quoted) |
| `--level` | beginner \| intermediate \| advanced \| expert |
| `--goal` | the learner's objective |
| `--context` | the learner's background |
| `--language` | teaching language |
| `--style` | socratic \| coaching \| direct \| immersive |
| `--mentor-name` | override the generated mentor name |
| `--provider` | generic \| anthropic \| openai \| google \| ollama \| llamacpp (aliases: `claude`, `chatgpt`, `gpt`, `gemini`) |
| `--emit` | text \| json \| modelfile \| markdown |
| `--compact` | short prompt for small-context local models |
| `--out FILE` | write to a file instead of stdout |
| `--prompt-format` | auto \| markdown \| xml (auto = XML for Claude, markdown otherwise) |
| `--thinking` / `--thinking-budget N` | Claude extended thinking |
| `--reasoning-effort` | OpenAI reasoning models: none \| minimal \| low \| medium \| high \| xhigh \| max |
| `--no-cache` | Claude: disable system-prompt caching |
| `--show-thinking` | `run`: stream the model's reasoning (dimmed, stderr) |

For **local models**, always use `--compact` if the model has under ~8k context,
and prefer the `ollama` or `llamacpp` provider so the capability notes match the
model's real constraints.

### Live sessions (`mentor run`)

Run the mentor directly against a backend — no copy-paste needed:

```bash
mentor run --field "Rust" --provider ollama --model qwen2.5:7b        # local
mentor run rustbuddy                                                  # saved mentor
mentor run --field "contract law" --provider claude --model claude-sonnet-5
mentor run --field "Rust" --provider chatgpt --model gpt-5.6 --reasoning-effort high
mentor run --field "Rust" --provider claude --thinking --show-thinking
mentor run --field "Rust" --provider ollama --once "I'm ready"        # one turn
mentor run --field "Rust" --provider chatgpt --dry-run                # show payload, send nothing
```

- **Claude** (`--provider claude`): the system prompt is sent as a cached
  `system` block (prompt caching), shaped with XML section tags, with optional
  extended thinking (`--thinking`, `--thinking-budget`).
- **ChatGPT** (`--provider chatgpt`): reasoning models automatically use the
  `developer` role and `max_completion_tokens`, drop unsupported `temperature`,
  and accept `--reasoning-effort`; token usage is reported per turn.
- **Local**: Ollama (`--host` or `$OLLAMA_HOST`) and llama.cpp / LM Studio
  (`--host` or `$LLAMACPP_HOST`, OpenAI-compatible).
- **Credentials**: set `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`, or drop them in
  `./.env` or `~/.config/expert-mentor/.env`. Override endpoints with
  `$OPENAI_BASE_URL` / `$ANTHROPIC_BASE_URL`.
- **Model discovery**: `mentor models --provider claude --refresh` lists the
  models your key can actually call. `mentor models` shows the built-in catalog.
- Interactive commands: `/reset` clears history, `/exit` quits. Requests retry
  automatically on rate limits and transient errors.
- `--dry-run` prints the exact request body (including cache/thinking/reasoning
  fields) and is handy for debugging.

### Persistent learners (`--learner` / `--remember`)

Give a session a memory so the mentor adapts across days instead of starting
over:

```bash
mentor run --field "Rust" --provider ollama --remember        # auto-name from field
mentor run --field "Rust" --provider claude --learner rust    # explicit name
```

- The mentor's system prompt is injected with the learner's **mastered**,
  **shaky**, **misconception**, and **open-question** lists (only once there is
  history to report).
- Each session transcript is written to `~/.config/expert-mentor/sessions/`.
- Curate the model yourself:

```bash
mentor progress rust --add-mastered ownership --add-shaky lifetimes \
    --add-misconception "Rc == Arc" --goal "write idiomatic Rust"
mentor learners
mentor sessions rust
mentor transcript <id>
```

Profiles live in `~/.config/expert-mentor/learners/<name>.json` — plain JSON you
can edit by hand.

**Automatic review.** After a session, let the model assess the transcript and
update the record for you:

```bash
mentor review rust              # show proposed changes (calls the model)
mentor review rust --apply      # write them to the profile
mentor review rust --dry-run    # show the review prompt, call nothing
```

The reviewer reuses the provider the session was run with, extracts a strict
JSON assessment (mastered / shaky / misconceptions / open questions / level /
next lesson), and merges it — promoting anything newly mastered out of *shaky*.
This closes the loop: run → transcript → assessment → updated profile, with no
manual bookkeeping.

## Step 4 — Run the session (or hand off the prompt)

If teaching inline, obey the loaded prompt's **Teaching Contract** without
exception. The non-negotiables:

1. Guide with hints before giving answers.
2. One concept at a time; verify before advancing.
3. After each explanation, ask a retrieval question the learner must answer.
4. Every session leaves the learner having produced something.
5. Never fabricate facts, citations, formulas, or APIs — flag uncertainty.

If handing off, tell the user exactly where to paste the output and how to set
the temperature (the script prints a recommended value).

## Files

- `pyproject.toml` — packaging metadata, console entry points, tooling config.
- `LICENSE` — MIT.
- `.github/workflows/ci.yml` — CI: self-test matrix, health check, package build.
- `install.sh` / `uninstall.sh` — one-command setup and teardown.
- `bin/mentor` — the `mentor` launcher (resolves symlinks, runs the generator).
- `Makefile` — `make install | test | doctor | fields | demo | clean`.
- `templates/mentor_system_prompt.md` — the master mentor prompt (edit to tune).
- `templates/compact_prompt.md` — short variant for small local models.
- `templates/curriculum_prompt.md` — curriculum-designer prompt.
- `templates/review_prompt.md` — session-assessment (progress review) prompt.
- `scripts/expert_mentor.py` — the CLI: provider-aware prompt/Modelfile/JSON generator.
- `scripts/mentor_runtime.py` — dependency-free streaming chat adapters (Ollama, llama.cpp, OpenAI, Anthropic).
- `scripts/mentor_memory.py` — persistent learner profiles and session transcripts.
- `scripts/selftest.py` — dependency-free test suite (`make test`).
- `references/pedagogy.md` — the teaching methods the mentor draws on.
- `references/fields.md` — curated field profiles + how to add your own.
- `references/providers.md` — capability notes and deployment recipes per provider.
- `examples/` — ready-made generated outputs for common cases.
