# Providers — deployment recipes

The same mentor prompt is adapted per provider because cloud models and local
models have very different capability envelopes. The generator injects the right
**capability notes** and emits a format each provider can consume.

Run `mentor providers` to see defaults, or `mentor models` for the model catalog.

## Capability envelopes

| Provider | Aliases | Temperature | Default model | Capability notes |
|----------|---------|-------------|---------------|------------------|
| `generic` | — | 0.6 | any capable model | cloud notes |
| `anthropic` | `claude` | 0.7 | `claude-sonnet-5` | Claude notes + XML shaping |
| `openai` | `chatgpt`, `gpt`, `oai` | 0.7 | `gpt-5.6` | ChatGPT notes + markdown |
| `google` | `gemini` | 0.8 | `gemini-2.5-pro` | cloud notes |
| `ollama` | `local` | 0.4 | `llama3.1:8b` | local notes |
| `llamacpp` | — | 0.4 | local-gguf | local notes |

- **Cloud notes** tell the model to exploit its large context: maintain a
  detailed learner model, use rich analogies, cite real sources when confident.
- **Claude notes** additionally ask for structured prose / XML tags and a clean
  separation between private deliberation and what the learner sees.
- **ChatGPT notes** additionally ask for clear markdown structure and explicit
  next steps.
- **Local notes** tell the model to compensate for limited context and reasoning:
  follow the flow strictly, keep replies short, one question per reply, never
  invent citations, restate the goal each turn.

Discover the current model line-up any time:

```bash
mentor models                      # built-in catalog for Claude + ChatGPT
mentor models --provider claude --refresh   # live lookup with your API key
```

## Anthropic (Claude)

```bash
mentor --field "quantum computing" --provider claude --emit json
mentor run --field "Rust" --provider claude --model claude-sonnet-5
```

The generator and runtime both produce a correct **Messages API** request:

- the mentor prompt is a top-level `system` **list of blocks** marked with
  `cache_control: {"type": "ephemeral"}` — Anthropic **prompt caching**, a large
  cost/latency win for a long, static system prompt (`--no-cache` disables it);
- the prompt is re-shaped into **XML section tags** (`<identity>`,
  `<the_teaching_contract>`, …) because Claude follows XML structure well
  (`--prompt-format markdown` opts out);
- optional **extended thinking**: `--thinking` (`--thinking-budget` default
  4096). When thinking is on, `temperature` is omitted (the API requires the
  default).
- streaming understands `text_delta` and `thinking_delta`, and reports input,
  **cache-read**, and output tokens per turn.

Recommended: `max_tokens>=2048`. Current models: `claude-sonnet-5`,
`claude-opus-5`, `claude-fable-5-1`, `claude-haiku-4-5`.

## OpenAI (ChatGPT)

```bash
mentor --field "organic chemistry" --provider chatgpt --emit json
mentor run --field "Rust" --provider chatgpt --model gpt-5.6 --reasoning-effort high
```

The request shape is adapted automatically from the model name:

| Model family | System role | Token limit field | Temperature | Reasoning |
|--------------|-------------|-------------------|-------------|-----------|
| `gpt-5*`, `gpt-6*`, `o1…o9*` | `developer` | `max_completion_tokens` | omitted | `reasoning_effort` supported |
| `gpt-4o`, `gpt-4.1`, etc. | `system` | `max_tokens` | sent | not supported |

- `--reasoning-effort` accepts `none|minimal|low|medium|high|xhigh|max` (values
  the model actually supports are a subset).
- Streaming sets `stream_options.include_usage` and reports token usage.
- Works unchanged with any OpenAI-compatible endpoint via `$OPENAI_BASE_URL`
  (vLLM, Together, Groq, LM Studio server, …).

## Google (Gemini)

```bash
mentor --field "macroeconomics" --provider google --emit json
```

Produces a `systemInstruction` + `contents` payload for the Generative Language
API.

## Ollama (local)

```bash
mentor --field "Rust" --level intermediate \
    --provider ollama --emit modelfile --model qwen2.5:7b --compact > Modelfile
ollama create expert-rust -f Modelfile
ollama run expert-rust
```

The Modelfile pins `SYSTEM`, `temperature`, `num_ctx`, and `top_p`. Use
`--compact` for 7B-and-under models and raise `--num-ctx` to match the model.

## llama.cpp / LM Studio (local)

```bash
mentor --field "music theory" --provider llamacpp --emit json --compact
```

Emits a JSON object with `system_prompt`, `temperature`, `n_ctx`, and
`max_tokens`. In LM Studio, paste `system_prompt` into the system-prompt field
and match the parameters. In llama.cpp server, pass it via the chat template's
system slot or your wrapper.

## Choosing `--compact`

Use `--compact` when:

- the model has under ~8k context,
- the model is 7B parameters or smaller,
- the model tends to ignore long system prompts.

The compact template strips the long teaching contract down to numbered rules
and a short flow, which small models follow far more reliably.

## Tuning tips

- **Mentor too passive?** Raise temperature slightly or switch `--style direct`.
- **Mentor gives answers away?** Switch `--style socratic` and say "don't give
  me the answer yet" in your first message.
- **Mentor invents sources?** Append "If you are not certain a source exists,
  say so and tell me how to find it." Local notes already include this.
- **Long-winded local model?** Add your own `num_predict` cap and keep
  `--compact` on.
