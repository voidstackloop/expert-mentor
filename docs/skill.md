# Using expert-mentor as an agent skill

The repository root is a valid skill: [`SKILL.md`](../SKILL.md) tells an agent
*when* to use expert-mentor and *how* to run it. That makes the whole thing
usable inside Claude Code and opencode, not just as a CLI.

## Install

`./install.sh` links the skill into the standard locations automatically:

```
~/.claude/skills/expert-mentor       -> <repo>
~/.config/opencode/skills/expert-mentor -> <repo>
```

Manual equivalent:

```bash
ln -sfn ~/projects/expert-mentor ~/.claude/skills/expert-mentor
ln -sfn ~/projects/expert-mentor ~/.config/opencode/skills/expert-mentor
```

Restart the host (opencode loads skills at startup) so it picks up the new skill.

## When it activates

The skill's `description` front-loads the trigger keywords, so an agent loads it
when the user wants to learn, be taught, or be mentored in a field — or wants to
turn a provider or local LLM into a teacher. Examples:

- "teach me quantum computing"
- "be my Rust mentor"
- "explain macroeconomics like a professor"
- "make Claude act as an expert tutor for contract law"

## What the agent does

1. **Collects the essentials** — field (required), plus level, goal, context,
   language, provider (inferred if absent).
2. **Chooses a delivery mode** — teach now inline, produce a reusable prompt,
   configure a provider/local model, or design a curriculum.
3. **Generates with the CLI** — e.g.
   `mentor --field "Rust" --provider claude --emit json`.
4. **Runs the session** following the teaching contract, or hands the prompt off.

## Alternative: project or global registration

Instead of symlinks you can register the skill path in your opencode config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["~/projects"]
  }
}
```

The loader scans for `**/SKILL.md` inside configured paths, so
`~/projects/expert-mentor/SKILL.md` is found as the `expert-mentor` skill.

## Files the agent reads

| File | Role |
|------|------|
| [`SKILL.md`](../SKILL.md) | trigger + workflow |
| [`templates/mentor_system_prompt.md`](../templates/mentor_system_prompt.md) | the master prompt |
| [`templates/compact_prompt.md`](../templates/compact_prompt.md) | small-model variant |
| [`references/pedagogy.md`](../references/pedagogy.md) | teaching methods |
| [`references/fields.md`](../references/fields.md) | field profiles |
| [`references/providers.md`](../references/providers.md) | provider recipes |
