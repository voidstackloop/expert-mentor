# Getting started

## Install

Pick one:

```bash
# Isolated CLI install (recommended)
pipx install expert-mentor

# Plain pip
pip install expert-mentor

# From source, with the skill linked too
git clone https://github.com/voidstackloop/expert-mentor
cd expert-mentor
./install.sh
```

`install.sh` puts the `mentor` command on your PATH, links the skill into
`~/.claude/skills/` and `~/.config/opencode/skills/`, and runs a health check.
Undo it with `./uninstall.sh`.

You can also run it without installing anything:

```bash
python3 scripts/expert_mentor.py --field "Rust"
./bin/mentor --field "Rust"
```

## First prompt

Generate a reusable teaching system prompt:

```bash
mentor --field "organic chemistry" --level intermediate
```

The output is a complete system prompt. Paste it into any chat as the system
prompt, or hand it to an API. To get a request body you can send directly:

```bash
mentor --field "contract law" --provider claude --emit json
mentor --field "Rust" --provider chatgpt --emit json
mentor --field "Rust" --provider ollama --emit modelfile
```

## First live session

```bash
mentor run --field "Rust" --provider ollama --model qwen2.5:7b
```

Inside a session:

- `/reset` clears the conversation history
- `/exit` (or Ctrl-C) quits
- Token usage is printed after each turn on stderr

To use a cloud provider, set an API key first:

```bash
export ANTHROPIC_API_KEY=...      # for --provider claude
export OPENAI_API_KEY=...         # for --provider chatgpt
mentor run --field "Rust" --provider claude
```

## Make it remember you

```bash
mentor run --field "Rust" --provider claude --remember
```

The learner is named from the field (`rust`). After the session:

```bash
mentor progress rust          # see mastered / shaky / misconceptions
mentor review rust --apply    # let the model update the profile from the transcript
mentor cards rust --generate  # build flashcards
mentor quiz rust              # review them with spaced repetition
```

## Next steps

- [Command reference](commands.md) for every option.
- [Providers](providers.md) to configure Claude, ChatGPT, Gemini, or local models.
- [How the mentor teaches](learning.md) to understand the pedagogy.
