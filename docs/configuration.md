# Configuration

## Saved defaults

Stop retyping the same flags by saving defaults:

```bash
mentor config --set provider=claude --set level=intermediate --set style=coaching
mentor config                       # show effective config
mentor config --unset style
mentor config --reset
```

Stored at `~/.config/expert-mentor/config.json`. Valid keys:

`provider`, `model`, `level`, `language`, `style`, `temperature`, `learner`,
`prompt_format`, `compact`, `thinking`, `reasoning_effort`.

Command-line flags always override saved defaults.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `EXPERT_MENTOR_HOME` | base config/data directory (default `~/.config/expert-mentor`) |
| `ANTHROPIC_API_KEY`, `CLAUDE_API_KEY` | Claude credentials |
| `OPENAI_API_KEY`, `CHATGPT_API_KEY` | OpenAI credentials |
| `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL` | endpoint overrides |
| `OLLAMA_HOST`, `LLAMACPP_HOST`, `LLAMACPP_API_KEY` | local backends |
| `NO_COLOR` | disable colored output |

A `.env` file in the current directory or in `$EXPERT_MENTOR_HOME/.env` is loaded
automatically; existing environment variables win.

```
# ~/.config/expert-mentor/.env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_HOST=http://localhost:11434
```

## File locations

Everything lives under `$EXPERT_MENTOR_HOME` (default
`~/.config/expert-mentor`):

```
config.json                         saved defaults
.env                                optional credentials
prompts/<name>.md                   saved mentors (mentor save)
models/<name>.Modelfile             generated Ollama models
learners/<name>.json                learner profiles
learners/<name>.cards.json          flashcards
sessions/<timestamp>-<name>.md      session transcripts
sessions/<timestamp>-<name>.json    session metadata
```

All of it is plain JSON/markdown — inspect or edit by hand, and commit it to your
own dotfiles if you like.

## Field profiles

Curated field profiles ship in `references/fields.md`. Add your own in
`references/fields.json` (merged over the built-ins):

```json
{
  "my-field": {
    "key": "Human-readable name",
    "aliases": ["my field", "abbreviation"],
    "mentor_name": "Dr. Example",
    "notes": "What professional competence means here: core reasoning, standards, traps, anchors.",
    "concepts": ["concept 1", "concept 2"],
    "misconceptions": ["wrong model A"],
    "resources": ["Author, Title"],
    "capstone": "One realistic project that proves competence."
  }
}
```

See [`references/fields.md`](../references/fields.md) for details.
