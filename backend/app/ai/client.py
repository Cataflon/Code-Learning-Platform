"""Talking to the language model, behind an interface like Runner (decision D25).

``LLMClient`` is the only thing the service knows. ``ClaudeClient`` calls Claude through the
official ``anthropic`` SDK; ``FakeLLMClient`` answers from a script, so no test ever reaches
the network or needs a key.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import anthropic

from app.core.config import get_settings


class LLMError(Exception):
    """The model could not give a usable answer (network, refusal, cut off, bad JSON)."""


class InvalidJSONError(LLMError):
    """The answer was not valid JSON for the schema; the caller may ask once more."""


@dataclass
class LLMResult:
    data: dict[str, Any]
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


class LLMClient(Protocol):
    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> LLMResult: ...


class ClaudeClient:
    """Claude with structured outputs: the answer is constrained to ``schema`` (JSON Schema).

    * Timeout ``AI_TIMEOUT_S``; the SDK retries 408/409/429/5xx and connection errors twice
      with exponential backoff (``max_retries=2``).
    * Server-side refusal fallback is on (``fallbacks: "default"``): if a safety classifier
      declines, the API reruns the request on the model Anthropic recommends for that category.
    * A refusal or an answer cut off at ``max_tokens`` is an error, never half-parsed.
    """

    MAX_TOKENS = 16000

    def __init__(self, api_key: str, model: str, timeout_s: float, effort: str = "high") -> None:
        self.model = model
        self.effort = effort
        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout_s, max_retries=2)

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        try:
            response = self.client.beta.messages.create(
                model=self.model,
                max_tokens=self.MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={
                    "effort": self.effort,
                    "format": {"type": "json_schema", "schema": schema},
                },
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.AuthenticationError as exc:
            raise LLMError("The Anthropic API key was rejected") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError("Claude is rate limited right now; try again later") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Claude returned an error ({exc.status_code})") from exc
        except anthropic.APIConnectionError as exc:  # includes timeouts
            raise LLMError("Could not reach Claude (network error or timeout)") from exc

        if response.stop_reason == "refusal":
            raise LLMError("Claude declined this request")
        if response.stop_reason == "max_tokens":
            raise InvalidJSONError("The answer was cut off before it was complete")
        text = "".join(block.text for block in response.content if block.type == "text")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise InvalidJSONError("The answer was not valid JSON") from exc
        if not isinstance(data, dict):
            raise InvalidJSONError("The answer was not a JSON object")
        return LLMResult(
            data=data,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=response.model,
        )


@dataclass
class FakeLLMClient:
    """Deterministic stand-in: returns the scripted answers in order (or calls a function).

    An item that is an exception is raised instead. Every call is recorded for assertions.
    """

    script: list[dict[str, Any] | Exception] | Callable[[str, str, dict], dict] = field(
        default_factory=list
    )
    calls: list[tuple[str, str, dict]] = field(default_factory=list)
    tokens: int = 100

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        self.calls.append((system, user, schema))
        if callable(self.script):
            answer = self.script(system, user, schema)
        else:
            if len(self.calls) > len(self.script):
                raise LLMError("FakeLLMClient: no scripted answer left")
            answer = self.script[len(self.calls) - 1]
        if isinstance(answer, Exception):
            raise answer
        return LLMResult(
            data=answer, input_tokens=self.tokens, output_tokens=self.tokens, model="fake-model"
        )


@lru_cache
def _claude() -> ClaudeClient:
    settings = get_settings()
    return ClaudeClient(
        api_key=settings.anthropic_api_key.get_secret_value(),
        model=settings.ai_model,
        timeout_s=settings.ai_timeout_s,
        effort=settings.ai_effort,
    )


def get_llm_client() -> LLMClient:
    """FastAPI dependency; tests override it with a FakeLLMClient."""
    return _claude()
