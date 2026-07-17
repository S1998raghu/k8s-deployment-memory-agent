import json
import os
import boto3

_MODEL_ID = "amazon.titan-embed-text-v2:0"
_DIMENSIONS = 1024


def _client():
    region = os.environ.get("AWS_REGION", "us-west-2")
    return boto3.client("bedrock-runtime", region_name=region)


def embed_text(text):
    body = json.dumps({
        "inputText": text,
        "dimensions": _DIMENSIONS,
        "normalize": True,
    })
    response = _client().invoke_model(
        modelId=_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(response["body"].read())
    return payload["embedding"]