"""Talking to the language model, behind an interface like Runner (decision D25).

``LLMClient`` is the only thing the service knows. Two real implementations:

* ``OpenAICompatibleClient``: Gemini (default) or the NVIDIA API catalog, through their
  OpenAI-compatible endpoints, with the official ``openai`` SDK;
* ``ClaudeClient``: Claude through the official ``anthropic`` SDK.

``FakeLLMClient`` answers from a script, so no test ever reaches the network or needs a key.
"""

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Protocol

import anthropic
import openai

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


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_json_object(text: str) -> dict[str, Any]:
    """The JSON object in a model's answer: tolerates a ```json fence or text around it."""
    cleaned = _FENCE.sub("", text.strip())
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end <= start:
        raise InvalidJSONError("The answer did not contain a JSON object")
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise InvalidJSONError("The answer was not valid JSON") from exc
    if not isinstance(data, dict):
        raise InvalidJSONError("The answer was not a JSON object")
    return data


class OpenAICompatibleClient:
    """A model behind an OpenAI-compatible endpoint: Gemini (default) or the NVIDIA catalog.

    * The official ``openai`` SDK is pointed at the provider's base URL.
    * ``structured=True`` (Gemini) asks for the answer constrained to the JSON schema
      (``response_format``); otherwise (NVIDIA, whose endpoint has no such field) the schema
      goes into the system message. Either way the answer is parsed and validated here, and the
      caller asks once more when it is invalid.
    * Free tiers are often busy: a 503, a 429, a timeout or a lost connection moves on to the
      next model of ``models`` after a short pause, up to ``MAX_ATTEMPTS`` tries in all.
    """

    MAX_TOKENS = 8192  # reasoning models spend part of it thinking before the JSON
    MAX_ATTEMPTS = 6

    def __init__(
        self,
        api_key: str,
        models: list[str],
        base_url: str,
        timeout_s: float,
        *,
        label: str,
        structured: bool,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.models = list(models)
        self.model = self.models[0]
        self.label = label
        self.structured = structured
        self.sleep = sleep
        self.client = openai.OpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout_s, max_retries=0
        )

    def complete_json(self, system: str, user: str, schema: dict[str, Any]) -> LLMResult:
        extra: dict[str, Any] = {}
        if self.structured:
            instructions = f"{system}\n\nAnswer with one JSON object that follows the schema."
            extra["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "answer", "schema": schema},
            }
        else:
            instructions = (
                f"{system}\n\nAnswer with ONE JSON object and nothing else (no prose, no code "
                f"fence). It must follow this JSON Schema:\n{json.dumps(schema)}"
            )
        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": user},
        ]
        tried: list[str] = []
        for attempt in range(self.MAX_ATTEMPTS):
            model = self.models[attempt % len(self.models)]
            tried.append(model)
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=self.MAX_TOKENS,
                    **extra,
                )
            except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
                raise LLMError(f"The {self.label} API key was rejected") from exc
            except (
                openai.RateLimitError,
                openai.InternalServerError,
                openai.APIConnectionError,  # includes timeouts
            ):
                self.sleep(min(2**attempt, 8))
                continue
            except openai.NotFoundError as exc:
                if len(self.models) > 1:
                    continue  # this model was retired; the next one may still exist
                raise LLMError(f"{self.label} does not offer the model {model}") from exc
            except openai.APIStatusError as exc:
                raise LLMError(f"{self.label} returned an error ({exc.status_code})") from exc

            choice = response.choices[0]
            if choice.finish_reason == "length":
                raise InvalidJSONError("The answer was cut off before it was complete")
            usage = response.usage
            return LLMResult(
                data=parse_json_object(choice.message.content or ""),
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
                model=(response.model or model).removeprefix("models/"),
            )
        names = ", ".join(dict.fromkeys(tried))
        raise LLMError(
            f"{self.label} is busy right now ({names} did not answer); try again in a few minutes"
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


def build_llm_client() -> LLMClient:
    settings = get_settings()
    key = settings.ai_api_key.get_secret_value()
    if settings.ai_provider == "anthropic":
        return ClaudeClient(
            api_key=key,
            model=settings.ai_models[0],
            timeout_s=settings.ai_attempt_timeout_s,
            effort=settings.ai_effort,
        )
    return OpenAICompatibleClient(
        api_key=key,
        models=settings.ai_models,
        base_url=settings.ai_endpoint,
        timeout_s=settings.ai_attempt_timeout_s,
        label="Gemini" if settings.ai_provider == "gemini" else "The NVIDIA API",
        structured=settings.ai_provider == "gemini",
    )


@lru_cache
def _cached_client() -> LLMClient:
    return build_llm_client()


def get_llm_client() -> LLMClient:
    """FastAPI dependency; tests override it with a FakeLLMClient."""
    return _cached_client()
