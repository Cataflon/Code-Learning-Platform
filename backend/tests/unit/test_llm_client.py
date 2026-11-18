"""The model clients, without the network: the SDK object is replaced by a scripted stand-in."""

from types import SimpleNamespace

import httpx
import openai
import pytest
from pydantic import SecretStr

from app.ai.client import (
    ClaudeClient,
    InvalidJSONError,
    LLMError,
    OpenAICompatibleClient,
    build_llm_client,
    parse_json_object,
)
from app.core.config import get_settings

REQUEST = httpx.Request("POST", "http://unused")


def test_parse_json_object_tolerates_fences_and_text_around_it():
    assert parse_json_object('{"tests": []}') == {"tests": []}
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Here it is:\n{"a": {"b": 2}}\nDone.') == {"a": {"b": 2}}


@pytest.mark.parametrize("text", ["", "no json here", "[1, 2]", '{"a": 1', "{not json}"])
def test_parse_json_object_rejects_what_is_not_an_object(text):
    with pytest.raises(InvalidJSONError):
        parse_json_object(text)


class ScriptedCompletions:
    """Answers (or raises) the outcomes in order and records every request."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def completion(content, finish_reason="stop", model="gemini-3.5-flash"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))
        ],
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=45),
        model=model,
    )


def status_error(cls, code):
    return cls("error", response=httpx.Response(code, request=REQUEST), body=None)


def client_with(*outcomes, structured=False, models=("gemini-3.5-flash",)):
    pauses = []
    client = OpenAICompatibleClient(
        "test-key",
        list(models),
        "http://unused",
        5,
        label="Gemini",
        structured=structured,
        sleep=pauses.append,
    )
    completions = ScriptedCompletions(*outcomes)
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions, pauses


def test_without_structured_output_the_schema_goes_into_the_system_message():
    client, completions, _ = client_with(completion('```json\n{"tests": [{"name": "x"}]}\n```'))

    result = client.complete_json("SYSTEM RULES", "the task", {"type": "object"})

    assert result.data == {"tests": [{"name": "x"}]}
    assert (result.input_tokens, result.output_tokens) == (120, 45)
    request = completions.requests[0]
    system, user = request["messages"]
    assert "SYSTEM RULES" in system["content"] and '{"type": "object"}' in system["content"]
    assert user == {"role": "user", "content": "the task"}
    assert "response_format" not in request


def test_with_structured_output_the_schema_constrains_the_answer():
    client, completions, _ = client_with(completion('{"solution": "print(1)"}'), structured=True)

    client.complete_json("rules", "task", {"type": "object"})

    response_format = completions.requests[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["schema"] == {"type": "object"}


def test_a_busy_model_moves_on_to_the_next_one():
    client, completions, pauses = client_with(
        status_error(openai.InternalServerError, 503),
        status_error(openai.RateLimitError, 429),
        openai.APITimeoutError(request=REQUEST),
        completion('{"ok": true}', model="models/gemini-3.1-flash-lite"),
        models=("gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"),
    )

    result = client.complete_json("s", "u", {})

    assert result.data == {"ok": True}
    assert result.model == "gemini-3.1-flash-lite"
    assert [request["model"] for request in completions.requests] == [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ]
    assert pauses == [1, 2, 4]


def test_when_every_attempt_is_busy_the_error_says_so():
    busy = [status_error(openai.InternalServerError, 503) for _ in range(6)]
    client, completions, _ = client_with(*busy)

    with pytest.raises(LLMError, match="busy right now"):
        client.complete_json("s", "u", {})
    assert len(completions.requests) == OpenAICompatibleClient.MAX_ATTEMPTS


def test_a_rejected_key_or_a_cut_off_answer_stops_at_once():
    client, completions, _ = client_with(status_error(openai.AuthenticationError, 401))
    with pytest.raises(LLMError, match="key was rejected"):
        client.complete_json("s", "u", {})
    assert len(completions.requests) == 1

    client, _, _ = client_with(completion('{"tests": [', finish_reason="length"))
    with pytest.raises(InvalidJSONError):
        client.complete_json("s", "u", {})


def test_a_retired_model_is_skipped_when_there_is_another():
    client, completions, _ = client_with(
        status_error(openai.NotFoundError, 404),
        completion('{"ok": 1}'),
        models=("gemini-old", "gemini-3.5-flash"),
    )

    assert client.complete_json("s", "u", {}).data == {"ok": 1}
    assert [request["model"] for request in completions.requests] == [
        "gemini-old",
        "gemini-3.5-flash",
    ]


def test_the_provider_setting_picks_the_client_its_key_and_its_models(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("g-key"))

    client = build_llm_client()
    assert isinstance(client, OpenAICompatibleClient) and client.structured
    assert settings.ai_models == [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    assert settings.ai_available

    monkeypatch.setattr(settings, "ai_model", "gemini-3.8-flash")
    assert settings.ai_models == ["gemini-3.8-flash"]  # a chosen model has no default fallbacks
    monkeypatch.setattr(settings, "ai_fallback_models", "gemini-3.5-flash-lite, gemini-3.8-flash")
    assert settings.ai_models == ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

    monkeypatch.setattr(settings, "ai_provider", "nvidia")
    assert not settings.ai_available  # the NVIDIA key is empty
    monkeypatch.setattr(settings, "nvidia_api_key", SecretStr("nv-key"))
    nvidia = build_llm_client()
    assert isinstance(nvidia, OpenAICompatibleClient) and not nvidia.structured

    monkeypatch.setattr(settings, "ai_provider", "anthropic")
    monkeypatch.setattr(settings, "ai_model", "")
    monkeypatch.setattr(settings, "ai_fallback_models", "")
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("ant-key"))
    assert isinstance(build_llm_client(), ClaudeClient)
    assert settings.ai_models == ["claude-sonnet-5-5"]
