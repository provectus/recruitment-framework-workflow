import json
import time

import boto3

from shared import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = boto3.client("bedrock-runtime", region_name=config.AWS_REGION)
    return _client


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

    retries = 3
    delay = 1.0
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            response = client.invoke_model(
                modelId=config.BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
            return payload["content"][0]["text"]
        except client.exceptions.ThrottlingException as exc:
            last_error = exc
        except client.exceptions.ModelTimeoutException as exc:
            last_error = exc

        if attempt < retries - 1:
            time.sleep(delay * (2**attempt))

    raise RuntimeError(
        f"Bedrock invocation failed after {retries} attempts"
    ) from last_error
