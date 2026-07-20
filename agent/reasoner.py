import os
import boto3
import json

_MODEL_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def _client():
    region = os.environ.get("AWS_REGION", "us-west-2")
    return boto3.client("bedrock-runtime", region_name=region)


def _build_prompt(incident_description, similar_incidents):
    if similar_incidents:
        history_lines = []
        for inc in similar_incidents:
            trust = "confirmed working" if inc.get("fix_status") == "confirmed" else "unverified, LLM-suggested"
            history_lines.append(
                f"- [{inc['issue_type']}] {inc['description']}\n"
                f"  Previous fix ({trust}): {inc['suggested_fix'] or 'none recorded'}"
            )
        history_text = "\n".join(history_lines)
    else:
        history_text = "No similar past incidents found."

    return f"""You are a Kubernetes incident diagnosis assistant.

Current incident:
{incident_description}

Similar past incidents f
{history_text}

Based on the current incident and any relevant history above, provide:
1. A likely root cause
2. A concrete suggested fix

Keep your answer under 100 words."""


def suggest_fix(incident_description, similar_incidents):
    prompt = _build_prompt(incident_description, similar_incidents)
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "messages": [{"role": "user", "content": prompt}],
    })
    response = _client().invoke_model(
        modelId=_MODEL_ID,
        body=body,
        contentType="application/json",
        accept="application/json",
    )
    payload = json.loads(response["body"].read())
    return payload["content"][0]["text"]