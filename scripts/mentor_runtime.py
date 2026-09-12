#!/usr/bin/env python3
"""Runtime chat adapters for expert-mentor.

Streams a tutoring conversation against any supported backend using only the
standard library (no `pip install` required), and adapts the request shape to
each provider's real API:

- Anthropic (Claude): top-level `system` blocks with prompt caching, optional
  extended thinking, `anthropic-version` header.
- OpenAI (ChatGPT): `developer` role and `max_completion_tokens` for reasoning
  models, `reasoning_effort`, usage reporting, correct temperature handling.
- Ollama / llama.cpp: local backends.

The `build_*_payload` functions are pure and fully unit-testable; the `stream_*`
generators perform network calls and yield events:
`{"type": "text"|"thinking"|"usage", ...}`.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional

DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_LLAMACPP_HOST = os.environ.get("LLAMACPP_HOST", "http://localhost:8080")
OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
ANTHROPIC_BASE = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
ANTHROPIC_VERSION = "2023-06-01"
GOOGLE_BASE = os.environ.get("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com")

RETRY_STATUS = {408, 409, 429, 500, 502, 503, 504, 529}
OPENAI_REASONING = re.compile(r"^(o[1-9]|gpt-5|gpt-6)")
ANTHROPIC_THINKING_MODELS = re.compile(r"claude-(3-7|4|5|fable|opus|sonnet|haiku)")

Event = Dict[str, object]
Message = Dict[str, str]


class MentorRuntimeError(RuntimeError):
    """Raised when a backend is unreachable, unauthenticated, or misconfigured."""


# --------------------------------------------------------------------------- #
# Model catalog + capability inference
# --------------------------------------------------------------------------- #
DEFAULT_MODELS = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-5.6",
    "ollama": "llama3.1:8b",
    "llamacpp": "local-gguf",
    "google": "gemini-flash-latest",
    "generic": "any capable model",
}

MODEL_CATALOG: Dict[str, List[tuple]] = {
    "anthropic": [
        ("claude-sonnet-5", "Best speed/intelligence; 1M ctx; adaptive thinking (default)"),
        ("claude-opus-5", "Most capable for agentic coding and enterprise work"),
        ("claude-fable-5-1", "Frontier long-horizon reasoning and agents"),
        ("claude-haiku-4-5", "Fastest near-frontier; extended thinking"),
        ("claude-sonnet-4-6", "Previous gen, fast"),
        ("claude-opus-4-6", "Previous gen, most intelligent"),
    ],
    "openai": [
        ("gpt-5.6", "Flagship reasoning/coding alias for gpt-5.6-sol (default)"),
        ("gpt-5.6-terra", "Balances intelligence and cost"),
        ("gpt-5.6-luna", "Cost-sensitive high-volume"),
        ("gpt-5.5", "Previous flagship"),
        ("gpt-5.4", "Affordable reasoning"),
        ("gpt-4o", "Legacy non-reasoning model"),
    ],
    "ollama": [
        ("llama3.1:8b", "General local default"),
        ("qwen2.5:7b", "Strong reasoning for its size"),
        ("mistral:7b", "Fast local default"),
    ],
    "llamacpp": [
        ("local-gguf", "Whatever model your llama.cpp / LM Studio server has loaded"),
    ],
    "google": [
        ("gemini-flash-latest", "Fast, current-gen; alias always tracks the latest flash (default)"),
        ("gemini-flash-lite-latest", "Cheapest/fastest, smaller context"),
        ("gemini-pro-latest", "Most capable; needs billing enabled (0 free-tier quota)"),
    ],
}


@dataclass
class Capabilities:
    system_style: str         # "top_level" (anthropic) | "message"
    system_role: str          # "system" | "developer"
    max_tokens_param: str     # "max_tokens" | "max_completion_tokens"
    supports_temperature: bool
    supports_reasoning: bool
    cache_system: bool


def capabilities(provider: str, model: str) -> Capabilities:
    name = (model or "").lower()
    if provider == "anthropic":
        return Capabilities("top_level", "", "max_tokens", True, True, True)
    if provider == "openai":
        reasoning = bool(OPENAI_REASONING.match(name))
        return Capabilities(
            "message",
            "developer" if reasoning else "system",
            "max_completion_tokens" if reasoning else "max_tokens",
            not reasoning,
            reasoning,
            False,
        )
    if provider in ("ollama", "llamacpp"):
        return Capabilities("message", "system", "max_tokens", True, False, False)
    if provider == "google":
        return Capabilities("top_level", "", "max_tokens", True, False, False)
    return Capabilities("message", "system", "max_tokens", True, False, False)


def supports_thinking(provider: str, model: str) -> bool:
    if provider == "anthropic":
        return bool(ANTHROPIC_THINKING_MODELS.search((model or "").lower()))
    if provider == "openai":
        return bool(OPENAI_REASONING.match((model or "").lower()))
    return False


# --------------------------------------------------------------------------- #
# Environment / credentials
# --------------------------------------------------------------------------- #
def load_env() -> None:
    """Load KEY=VALUE pairs from ./.env and ~/.config/expert-mentor/.env.

    Existing environment variables always win.
    """
    candidates = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.expanduser(os.environ.get("EXPERT_MENTOR_HOME", "~/.config/expert-mentor")), ".env"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except OSError:
            continue


def api_key(provider: str) -> Optional[str]:
    load_env()
    if provider == "anthropic":
        return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if provider == "openai":
        return os.environ.get("OPENAI_API_KEY") or os.environ.get("CHATGPT_API_KEY")
    if provider == "llamacpp":
        return os.environ.get("LLAMACPP_API_KEY")
    if provider == "google":
        return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    return None


# --------------------------------------------------------------------------- #
# Pure payload builders (unit-testable, no network)
# --------------------------------------------------------------------------- #
def build_ollama_payload(model: str, system: str, messages: List[Message],
                         temperature: float = 0.4, stream: bool = True,
                         max_tokens: Optional[int] = None) -> Dict:
    chat: List[Message] = []
    if system:
        chat.append({"role": "system", "content": system})
    chat.extend(messages)
    options: Dict = {"temperature": temperature}
    if max_tokens:
        options["num_predict"] = max_tokens
    return {"model": model, "messages": chat, "stream": stream, "options": options}


def build_openai_payload(model: str, system: str, messages: List[Message],
                         temperature: float = 0.7, stream: bool = True,
                         max_tokens: int = 2048, reasoning_effort: Optional[str] = None,
                         include_usage: bool = False) -> Dict:
    caps = capabilities("openai", model)
    chat: List[Message] = []
    if system:
        chat.append({"role": caps.system_role, "content": system})
    chat.extend(messages)
    payload: Dict = {"model": model, "messages": chat, "stream": stream}
    if max_tokens:
        payload[caps.max_tokens_param] = max_tokens
    if caps.supports_temperature:
        payload["temperature"] = temperature
    if reasoning_effort and caps.supports_reasoning:
        payload["reasoning_effort"] = reasoning_effort
    if include_usage and stream:
        payload["stream_options"] = {"include_usage": True}
    return payload


def build_google_payload(model: str, system: str, messages: List[Message],
                         temperature: float = 0.8, max_tokens: int = 2048) -> Dict:
    contents = [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
    ]
    payload: Dict = {"contents": contents,
                     "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens}}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    return payload


def build_anthropic_payload(model: str, system: str, messages: List[Message],
                            temperature: float = 0.7, stream: bool = True,
                            max_tokens: int = 2048, thinking_budget: Optional[int] = None,
                            cache: bool = True) -> Dict:
    payload: Dict = {"model": model, "messages": messages,
                     "max_tokens": max_tokens, "stream": stream}
    if system:
        block: Dict = {"type": "text", "text": system}
        if cache:
            block["cache_control"] = {"type": "ephemeral"}
        payload["system"] = [block]
    if thinking_budget:
        payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        # Extended thinking requires temperature=1, so leave it unset.
    else:
        payload["temperature"] = temperature
    return payload


# --------------------------------------------------------------------------- #
# Network helpers
# --------------------------------------------------------------------------- #
def _open(request: urllib.request.Request, timeout: int):
    """urlopen with exponential backoff on rate limits and transient errors."""
    attempts = 4
    last_reason = "unknown error"
    for attempt in range(attempts):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:500]
            if exc.code in RETRY_STATUS and attempt < attempts - 1:
                retry_after = exc.headers.get("retry-after") if exc.headers else None
                delay = float(retry_after) if (retry_after or "").isdigit() else min(2 ** attempt, 8)
                time.sleep(delay)
                continue
            raise MentorRuntimeError(f"{request.full_url} returned HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            last_reason = str(exc.reason)
            if attempt < attempts - 1:
                time.sleep(min(2 ** attempt, 8))
                continue
            raise MentorRuntimeError(f"cannot reach {request.full_url}: {last_reason}") from exc
    raise MentorRuntimeError(f"{request.full_url}: exhausted retries ({last_reason})")


def _post(url: str, payload: Dict, headers: Dict[str, str], timeout: int = 180):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json", **headers},
                                     method="POST")
    return _open(request, timeout)


def _get(url: str, headers: Dict[str, str], timeout: int = 60):
    request = urllib.request.Request(url, headers=headers, method="GET")
    return _open(request, timeout)


def _iter_sse_data(response) -> Iterator[str]:
    for raw in response:
        line = raw.decode("utf-8", "replace").strip()
        if line.startswith("data:"):
            yield line[5:].strip()


def _text(value: str) -> Event:
    return {"type": "text", "text": value}


def _thinking(value: str) -> Event:
    return {"type": "thinking", "text": value}


def _usage(**kwargs) -> Event:
    return {"type": "usage", "usage": {k: v for k, v in kwargs.items() if v is not None}}


# --------------------------------------------------------------------------- #
# Streaming backends (yield events)
# --------------------------------------------------------------------------- #
def stream_ollama(model: str, system: str, messages: List[Message],
                  host: Optional[str] = None, temperature: float = 0.4,
                  max_tokens: Optional[int] = None) -> Iterator[Event]:
    url = (host or DEFAULT_OLLAMA_HOST).rstrip("/") + "/api/chat"
    payload = build_ollama_payload(model, system, messages, temperature, max_tokens=max_tokens)
    with _post(url, payload, {}) as response:
        for raw in response:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = obj.get("message", {})
            if message.get("content"):
                yield _text(message["content"])
            if obj.get("done"):
                yield _usage(input_tokens=obj.get("prompt_eval_count"),
                             output_tokens=obj.get("eval_count"))
                break


def stream_openai_like(url: str, model: str, system: str, messages: List[Message],
                       temperature: float = 0.7, api_key: Optional[str] = None,
                       max_tokens: int = 2048, reasoning_effort: Optional[str] = None,
                       include_usage: bool = False) -> Iterator[Event]:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    payload = build_openai_payload(model, system, messages, temperature,
                                   max_tokens=max_tokens, reasoning_effort=reasoning_effort,
                                   include_usage=include_usage)
    with _post(url, payload, headers) as response:
        for data in _iter_sse_data(response):
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            if obj.get("usage"):
                usage = obj["usage"]
                yield _usage(input_tokens=usage.get("prompt_tokens"),
                             output_tokens=usage.get("completion_tokens"),
                             total_tokens=usage.get("total_tokens"))
            for choice in obj.get("choices", []):
                delta = choice.get("delta", {})
                if delta.get("content"):
                    yield _text(delta["content"])
                if delta.get("reasoning_content"):
                    yield _thinking(delta["reasoning_content"])


def stream_openai(model: str, system: str, messages: List[Message],
                  temperature: float = 0.7, api_key: Optional[str] = None,
                  max_tokens: int = 2048, reasoning_effort: Optional[str] = None) -> Iterator[Event]:
    key = api_key or api_key_for("openai")
    if not key:
        raise MentorRuntimeError("OPENAI_API_KEY is not set (put it in the env or a .env file)")
    yield from stream_openai_like(f"{OPENAI_BASE.rstrip('/')}/chat/completions", model, system,
                                  messages, temperature, key, max_tokens=max_tokens,
                                  reasoning_effort=reasoning_effort, include_usage=True)


def stream_llamacpp(model: str, system: str, messages: List[Message],
                    temperature: float = 0.4, host: Optional[str] = None,
                    max_tokens: int = 2048) -> Iterator[Event]:
    base = os.environ.get("LLAMACPP_HOST", host or DEFAULT_LLAMACPP_HOST).rstrip("/")
    yield from stream_openai_like(f"{base}/v1/chat/completions", model, system, messages,
                                  temperature, api_key_for("llamacpp"), max_tokens=max_tokens)


def stream_anthropic(model: str, system: str, messages: List[Message],
                     temperature: float = 0.7, api_key: Optional[str] = None,
                     max_tokens: int = 2048, thinking_budget: Optional[int] = None,
                     cache: bool = True) -> Iterator[Event]:
    key = api_key or api_key_for("anthropic")
    if not key:
        raise MentorRuntimeError("ANTHROPIC_API_KEY is not set (put it in the env or a .env file)")
    headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}
    payload = build_anthropic_payload(model, system, messages, temperature,
                                      max_tokens=max_tokens, thinking_budget=thinking_budget,
                                      cache=cache)
    with _post(f"{ANTHROPIC_BASE.rstrip('/')}/v1/messages", payload, headers) as response:
        for data in _iter_sse_data(response):
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            kind = obj.get("type")
            if kind == "message_start":
                usage = obj.get("message", {}).get("usage", {})
                yield _usage(input_tokens=usage.get("input_tokens"),
                             cache_read_tokens=usage.get("cache_read_input_tokens"))
            elif kind == "content_block_delta":
                delta = obj.get("delta", {})
                if delta.get("type") == "text_delta" and delta.get("text"):
                    yield _text(delta["text"])
                elif delta.get("type") == "thinking_delta" and delta.get("thinking"):
                    yield _thinking(delta["thinking"])
            elif kind == "message_delta":
                usage = obj.get("usage", {})
                yield _usage(output_tokens=usage.get("output_tokens"))


def stream_google(model: str, system: str, messages: List[Message],
                  temperature: float = 0.8, api_key: Optional[str] = None,
                  max_tokens: int = 2048) -> Iterator[Event]:
    key = api_key or api_key_for("google")
    if not key:
        raise MentorRuntimeError("GEMINI_API_KEY is not set (put it in the env or a .env file)")
    url = f"{GOOGLE_BASE.rstrip('/')}/v1beta/models/{model}:streamGenerateContent?alt=sse"
    payload = build_google_payload(model, system, messages, temperature, max_tokens)
    headers = {"x-goog-api-key": key}
    with _post(url, payload, headers) as response:
        for data in _iter_sse_data(response):
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            for candidate in obj.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    if part.get("text"):
                        yield _text(part["text"])
            usage = obj.get("usageMetadata")
            if usage:
                yield _usage(input_tokens=usage.get("promptTokenCount"),
                             output_tokens=usage.get("candidatesTokenCount"))


# Late-bound key lookup so tests can monkeypatch without import cycles.
def api_key_for(provider: str) -> Optional[str]:
    return api_key(provider)


def stream(provider: str, model: str, system: str, messages: List[Message],
           **kwargs) -> Iterator[Event]:
    """Dispatch to the right backend. Raises MentorRuntimeError if unsupported."""
    if provider == "ollama":
        return stream_ollama(model, system, messages, **kwargs)
    if provider == "openai":
        return stream_openai(model, system, messages, **kwargs)
    if provider == "anthropic":
        return stream_anthropic(model, system, messages, **kwargs)
    if provider == "llamacpp":
        return stream_llamacpp(model, system, messages, **kwargs)
    if provider == "google":
        return stream_google(model, system, messages, **kwargs)
    raise MentorRuntimeError(
        f"provider '{provider}' has no runtime backend. Use one of: "
        "ollama, llamacpp, openai, anthropic, google."
    )


def complete(provider: str, model: str, system: str, messages: List[Message],
             **kwargs) -> str:
    """Run a backend to completion and return the full text (non-streaming API)."""
    return "".join(
        event["text"] for event in stream(provider, model, system, messages, **kwargs)
        if event.get("type") == "text"
    )


# --------------------------------------------------------------------------- #
# Live model discovery
# --------------------------------------------------------------------------- #
def list_models(provider: str, api_key_value: Optional[str] = None) -> List[str]:
    """Query the provider's /models endpoint. Returns sorted model IDs."""
    key = api_key_value or api_key_for(provider)
    if provider == "anthropic":
        if not key:
            raise MentorRuntimeError("ANTHROPIC_API_KEY is not set")
        headers = {"x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}
        with _get(f"{ANTHROPIC_BASE.rstrip('/')}/v1/models?limit=1000", headers) as response:
            data = json.loads(response.read().decode("utf-8"))
        return [item["id"] for item in data.get("data", []) if item.get("id")]
    if provider == "openai":
        if not key:
            raise MentorRuntimeError("OPENAI_API_KEY is not set")
        headers = {"Authorization": f"Bearer {key}"}
        with _get(f"{OPENAI_BASE.rstrip('/')}/models", headers) as response:
            data = json.loads(response.read().decode("utf-8"))
        return sorted(item["id"] for item in data.get("data", []) if item.get("id"))
    raise MentorRuntimeError(f"model discovery is only available for anthropic and openai")
