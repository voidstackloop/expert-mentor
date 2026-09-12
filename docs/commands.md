# Command reference

Run `mentor <command> --help` for any command's own help. Without a command,
`mentor` generates a prompt from the flags you pass.

## Global options

| Flag | Description |
|------|-------------|
| `--field TEXT` | the field to teach (required to generate a prompt) |
| `--level {beginner,intermediate,advanced,expert}` | learner level (default: beginner) |
| `--goal TEXT` | the learner's objective |
| `--context TEXT` | the learner's background / prior knowledge |
| `--language TEXT` | teaching language |
| `--style {socratic,coaching,direct,immersive}` | teaching style (default: socratic) |
| `--mentor-name TEXT` | override the generated mentor name |
| `--provider NAME` | `generic`, `anthropic`/`claude`, `openai`/`chatgpt`/`gpt`, `google`/`gemini`, `ollama`/`local`, `llamacpp` |
| `--model TEXT` | target model id (defaults per provider) |
| `--emit {text,json,modelfile,markdown}` | output format (default depends on provider) |
| `--compact` | short prompt for small-context local models |
| `--out FILE` | write output to a file |
| `-q`, `--quiet` | suppress usage/save notices |
| `--prompt-format {auto,markdown,xml}` | prompt shape (auto = XML for Claude) |
| `--thinking` / `--thinking-budget N` | Anthropic extended thinking |
| `--reasoning-effort {none,minimal,low,medium,high,xhigh,max}` | OpenAI reasoning models |
| `--no-cache` | disable Anthropic system-prompt caching |
| `--learner NAME` | load/update a persisted learner profile |
| `--remember` | auto-name the learner from `--field` and persist progress |
| `--history-turns N` | `run`: max past turns kept in context (default 40) |

---

## `mentor` — generate a prompt

```bash
mentor --field "quantum computing" --level beginner
mentor --field "Rust" --provider claude --emit json > request.json
mentor --field "Rust" --provider ollama --compact --emit modelfile > Modelfile
mentor prompt --field "Rust" --provider chatgpt    # equivalent explicit form
```

## `mentor run [NAME]` — live tutoring session

```bash
mentor run --field "Rust" --provider ollama --model qwen2.5:7b
mentor run rustbuddy                       # load a saved mentor
mentor run --field "Rust" --provider claude --remember
mentor run --field "Rust" --provider chatgpt --reasoning-effort high
mentor run --field "Rust" --provider claude --thinking --show-thinking
```

Session options:

| Flag | Description |
|------|-------------|
| `--once "message"` | send a single message and exit |
| `--dry-run` | print the request payload; send nothing |
| `--host URL` | backend host for Ollama / llama.cpp |
| `--temperature F` | sampling temperature (defaults per provider) |
| `--show-thinking` | stream model reasoning, dimmed, on stderr |
| `--learner NAME` / `--remember` | persist the learner profile |

## `mentor save` / `show` / `saved`

```bash
mentor save rustbuddy --field "Rust" --level intermediate
mentor show rustbuddy
mentor saved
```

## `mentor curriculum`

```bash
mentor curriculum --field "Rust" --duration "6 weeks, 5h/week"
```

Produces a curriculum-designer prompt (outcome statement, prerequisite check,
module plan, assessments, week-by-week schedule, failure modes).

## `mentor models`

```bash
mentor models                       # built-in catalog for Claude & ChatGPT
mentor models --provider claude --refresh   # live list with your API key
```

## `mentor fields` / `mentor providers`

```bash
mentor fields        # curated field profiles
mentor providers     # providers, default models, temperatures
```

## Learner memory

```bash
mentor learners
mentor progress rust --add-mastered ownership --add-shaky lifetimes \
    --add-misconception "Rc == Arc" --add-question "Rc vs Box?" --goal "ship idiomatic Rust"
mentor sessions rust
mentor transcript <session-id>
mentor review rust [--apply] [--dry-run]
```

`progress` flags: `--field`, `--level`, `--goal`, `--note`, `--add-mastered`,
`--add-shaky`, `--add-misconception`, `--add-question`, `--reset`.

## Flashcards & quiz

```bash
mentor cards rust --add "What is ownership? :: Each value has one owner."
mentor cards rust --generate            # from the latest session
mentor cards rust                       # list with due counts
mentor cards rust --remove <id>
mentor cards rust --reset
mentor quiz rust [--all] [--n 10] [--shuffle]
```

Grades during a quiz: `again`, `hard`, `good`, `easy` (Enter = good, `q` = quit).

## Configuration & utilities

```bash
mentor config                                   # show effective config
mentor config --set provider=claude --set level=intermediate --set style=coaching
mentor config --unset style
mentor config --reset
mentor doctor
mentor skill [--dir PATH] [--force]    # install the Claude Code / opencode skill
mentor version
mentor interactive
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | success |
| 1 | runtime error (e.g. provider unreachable) |
| 2 | usage error / unsupported provider |
| 130 | interrupted (Ctrl-C) |
