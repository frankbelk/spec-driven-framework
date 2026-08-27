"""AWS Lambda entry point for the spec-driven-framework.

Expected event shapes:
  - API Gateway / Linear webhook: {"issue": "ENG-3"} or {"issue_identifier": "ENG-3"}
  - Direct invocation:            {"issue": "ENG-3", "max_retries": 3}
"""
from __future__ import annotations

import json

from core.pipeline import PipelineRunner


def _parse_event(event: dict) -> dict:
    """Normalize an incoming Lambda event into a flat dict of inputs."""
    payload = dict(event)
    body = event.get("body")
    if isinstance(body, str) and body.strip():
        try:
            parsed = json.loads(body)
            if isinstance(parsed, dict):
                payload.update(parsed)
        except json.JSONDecodeError:
            pass
    return payload


def _api_response(status_code: int, body: str) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": body}),
    }


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    payload = _parse_event(event)
    issue_identifier = (
        payload.get("issue")
        or payload.get("issue_identifier")
        or (payload.get("data", {}).get("issue", {}) or {}).get("identifier")
    )
    if not issue_identifier:
        return _api_response(400, "Missing required field: 'issue' (Linear issue identifier, e.g. ENG-3).")

    try:
        max_retries = int(payload.get("max_retries", 3))
    except (TypeError, ValueError):
        max_retries = 3

    try:
        runner = PipelineRunner()
        result = runner.run(issue_identifier, max_retries=max_retries)
        return _api_response(200, f"Pipeline completed for {issue_identifier}: {result.status}")
    except Exception as e:
        print(f"Lambda handler error: {e}")
        return _api_response(500, f"Pipeline failed for {issue_identifier}: {e}")