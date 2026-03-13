import json
import time
from collections.abc import Callable
from typing import Any

import boto3
import botocore.exceptions

from shared import config

_client = None

_RETRIES = 3
_INITIAL_DELAY = 1.0
_RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 529}


def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    return _client


def _is_retriable_client_error(exc: botocore.exceptions.ClientError) -> bool:
    status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
    return status_code in _RETRIABLE_STATUS_CODES


def _invoke_with_retry[T](fn: Callable[[], T]) -> T:
    client = get_client()
    last_error: Exception | None = None

    for attempt in range(_RETRIES):
        try:
            return fn()
        except client.exceptions.ThrottlingException as exc:
            last_error = exc
        except client.exceptions.ModelTimeoutException as exc:
            last_error = exc
        except client.exceptions.ModelNotReadyException as exc:
            last_error = exc
        except client.exceptions.ServiceUnavailableException as exc:
            last_error = exc
        except botocore.exceptions.ClientError as exc:
            if not _is_retriable_client_error(exc):
                raise
            last_error = exc
        except (
            botocore.exceptions.EndpointConnectionError,
            botocore.exceptions.ReadTimeoutError,
        ) as exc:
            last_error = exc

        if attempt < _RETRIES - 1:
            time.sleep(_INITIAL_DELAY * (2**attempt))

    raise RuntimeError(
        f"Bedrock invocation failed after {_RETRIES} attempts"
    ) from last_error


def _parse_invoke_response(response: Any) -> dict[str, Any]:
    return json.loads(response["body"].read())


def invoke_claude(
    prompt: str,
    max_tokens: int = 4096,
    system_prompt: str = "",
    step_type: str = "",
) -> str:
    if config.MOCK_BEDROCK and step_type:
        from shared.mock_bedrock import mock_invoke_claude

        return mock_invoke_claude(step_type)

    client = get_client()
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        body["system"] = system_prompt

    def _call() -> str:
        response = client.invoke_model(
            modelId=config.BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = _parse_invoke_response(response)
        content = payload.get("content", [])
        if not content or "text" not in content[0]:
            raise RuntimeError(f"Unexpected Bedrock response shape: {payload}")
        return content[0]["text"]

    return _invoke_with_retry(_call)


def invoke_claude_structured(
    prompt: str,
    tool_name: str,
    tool_schema: dict[str, Any],
    max_tokens: int = 4096,
    system_prompt: str = "",
    step_type: str = "",
) -> dict[str, Any]:
    if config.MOCK_BEDROCK and step_type:
        from shared.mock_bedrock import mock_invoke_claude_structured

        return mock_invoke_claude_structured(step_type)

    client = get_client()
    body: dict[str, Any] = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {
                "name": tool_name,
                "description": f"Record the structured {tool_name} result.",
                "input_schema": tool_schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": tool_name},
    }
    if system_prompt:
        body["system"] = system_prompt

    def _call() -> dict[str, Any]:
        response = client.invoke_model(
            modelId=config.BEDROCK_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = _parse_invoke_response(response)
        content = payload.get("content", [])
        tool_block = next(
            (b for b in content if b.get("type") == "tool_use"),
            None,
        )
        if tool_block is None:
            raise RuntimeError(
                f"Bedrock response contained no tool_use block: {payload}"
            )
        return tool_block["input"]

    return _invoke_with_retry(_call)
