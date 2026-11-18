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
    NvidiaClient,
    build_llm_client,
    parse_json_object,
)
from app.core.config import get_settings


def test_parse_json_object_tolerates_fences_and_text_around_it():
    assert parse_json_object('{"tests": []}') == {"tests": []}
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Here it is:\n{"a": {"b": 2}}\nDone.') == {"a": {"b": 2}}


@pytest.mark.parametrize("text", ["", "no json here", "[1, 2]", '{"a": 1', "{not json}"])
def test_parse_json_object_rejects_what_is_not_an_object(text):
    with pytest.raises(InvalidJSONError):
        parse_json_object(text)


class ScriptedCompletions:
    def __init__(self, outcome):
        self.outcome = outcome
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def completion(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(finish_reason=finish_reason, message=SimpleNamespace(content=content))
        ],
        usage=SimpleNamespace(prompt_tokens=120, completion_tokens=45),
        model="qwen/qwen3-next-80b-a3b-instruct",
    )


def nvidia_with(outcome):
    client = NvidiaClient("test-key", "qwen/qwen3-next-80b-a3b-instruct", "http://unused", 5)
    completions = ScriptedCompletions(outcome)
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    return client, completions


def test_nvidia_client_puts_the_schema_in_the_system_message_and_parses_the_answer():
    client, completions = nvidia_with(completion('```json\n{"tests": [{"name": "x"}]}\n```'))

    result = client.complete_json("SYSTEM RULES", "the task", {"type": "object"})

    assert result.data == {"tests": [{"name": "x"}]}
    assert (result.input_tokens, result.output_tokens) == (120, 45)
    system, user = completions.kwargs["messages"]
    assert system["role"] == "system" and "SYSTEM RULES" in system["content"]
    assert '{"type": "object"}' in system["content"]
    assert user == {"role": "user", "content": "the task"}


def test_nvidia_client_treats_a_cut_off_answer_as_invalid_json():
    client, _ = nvidia_with(completion('{"tests": [', finish_reason="length"))

    with pytest.raises(InvalidJSONError):
        client.complete_json("s", "u", {})


def test_nvidia_client_turns_sdk_errors_into_llm_errors():
    request = httpx.Request("POST", "http://unused")
    rejected = openai.AuthenticationError(
        "bad key", response=httpx.Response(401, request=request), body=None
    )
    client, _ = nvidia_with(rejected)

    with pytest.raises(LLMError, match="key was rejected"):
        client.complete_json("s", "u", {})

    client, _ = nvidia_with(openai.APIConnectionError(request=request))
    with pytest.raises(LLMError, match="Could not reach"):
        client.complete_json("s", "u", {})


def test_the_provider_setting_picks_the_client_and_its_key(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "nvidia_api_key", SecretStr("nv-key"))
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr(""))

    assert isinstance(build_llm_client(), NvidiaClient)
    assert settings.ai_available

    monkeypatch.setattr(settings, "ai_provider", "anthropic")
    assert not settings.ai_available  # the Anthropic key is empty
    monkeypatch.setattr(settings, "anthropic_api_key", SecretStr("ant-key"))
    assert isinstance(build_llm_client(), ClaudeClient)
    assert settings.ai_available
