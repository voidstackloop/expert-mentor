# Providers & credentials

`expert-mentor` adapts the request to each provider's real API. Choose one with
`--provider` (aliases in parentheses):

| Provider | Aliases | Default model | Used for |
|----------|---------|---------------|----------|
| `generic` | — | any capable model | prompt text only |
| `anthropic` | `claude` | `claude-sonnet-5` | live sessions + JSON |
| `openai` | `chatgpt`, `gpt`, `oai` | `gpt-5.6` | live sessions + JSON |
| `google` | `gemini` | `gemini-2.5-pro` | prompt JSON |
| `ollama` | `local` | `llama3.1:8b` | live sessions + Modelfile |
| `llamacpp` | — | your loaded GGUF | live sessions |

List what is available with `mentor providers`, and discover live model IDs with
`mentor models --provider claude --refresh`.

## Credentials

Keys are read from the environment, or from a `.env` file in the working
directory or `~/.config/expert-mentor/.env` (existing env vars win):

| Provider | Variables |
|----------|-----------|
| Anthropic | `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY`) |
| OpenAI | `OPENAI_API_KEY` (or `CHATGPT_API_KEY`) |
| llama.cpp / LM Studio | `LLAMACPP_API_KEY` (optional) |
| Ollama | none |

Endpoint overrides: `ANTHROPIC_BASE_URL`, `OPENAI_BASE_URL`, `OLLAMA_HOST`,
`LLAMACPP_HOST`.

## Claude (Anthropic)

- The mentor prompt is sent as a top-level `system` block marked with
  `cache_control: {"type": "ephemeral"}` — **prompt caching**, a large
  cost/latency win for a long, static system prompt. Disable with `--no-cache`.
- The prompt is re-shaped into **XML section tags** (`<identity>`,
  `<the_teaching_contract>`, …). Use `--prompt-format markdown` to opt out.
- **Extended thinking**: `--thinking` (`--thinking-budget` default 4096). When on,
  `temperature` is omitted because the API requires the default.
- Streaming understands `text_delta` and `thinking_delta`, and reports input,
  cache-read, and output tokens per turn.

```bash
mentor run --field "Rust" --provider claude --model claude-sonnet-5 --thinking
mentor --field "Rust" --provider claude --emit json
```

## ChatGPT (OpenAI)

The request shape adapts from the model name:

| Model family | System role | Token limit | Temperature | Reasoning |
|--------------|-------------|-------------|-------------|-----------|
| `gpt-5*`, `gpt-6*`, `o1…o9*` | `developer` | `max_completion_tokens` | omitted | `reasoning_effort` supported |
| `gpt-4o`, `gpt-4.1`, … | `system` | `max_tokens` | sent | not supported |

- `--reasoning-effort` accepts `none|minimal|low|medium|high|xhigh|max`.
- Streaming sets `stream_options.include_usage` and reports token usage.
- Works with any OpenAI-compatible endpoint via `OPENAI_BASE_URL`.

```bash
mentor run --field "Rust" --provider chatgpt --model gpt-5.6 --reasoning-effort high
```

## Gemini (Google)

`--emit json` produces a `systemInstruction` + `contents` payload. Live sessions
are not currently implemented for Gemini.

```bash
mentor --field "macroeconomics" --provider gemini --emit json
```

## Ollama (local)

```bash
mentor run --field "Rust" --provider ollama --model qwen2.5:7b
mentor --field "Rust" --provider ollama --compact --emit modelfile > Modelfile
ollama create expert-rust -f Modelfile
```

Use `--compact` for models under ~8k context or 7B and under. Set the host with
`--host` or `$OLLAMA_HOST`.

## llama.cpp / LM Studio (local)

Both expose an OpenAI-compatible server:

```bash
mentor run --field "music theory" --provider llamacpp --host http://localhost:8080
```

Set `$LLAMACPP_HOST` to avoid `--host`, and `$LLAMACPP_API_KEY` if the server
requires one.

## Reliability

Missing keys, unreachable hosts, and provider errors produce a single clean
`error: …` message. Requests retry automatically with exponential backoff on
rate limits and transient errors (HTTP 408/409/429/500/502/503/504/529),
honoring `Retry-After`.
