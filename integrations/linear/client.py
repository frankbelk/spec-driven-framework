"""Linear GraphQL API client.

Linear is the source of truth for the spec-driven-framework. This client
fetches issues and posts execution reports back as comments.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import requests

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class LinearIssue:
    """A Linear issue fetched from the API."""
    internal_id: str
    ticket_id: str
    ticket_title: str
    ticket_description: str


class LinearClient:
    """Thin wrapper around Linear's GraphQL API."""

    def __init__(self, api_key: Optional[str] = None, url: Optional[str] = None):
        self.api_key = api_key or settings.LINEAR_API_KEY
        self.url = url or settings.LINEAR_API_URL
        if not self.api_key:
            raise ValueError("LINEAR_API_KEY is not set.")

    def _headers(self) -> dict:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

    def _post(self, query: str, variables: dict) -> dict:
        resp = requests.post(
            self.url,
            json={"query": query, "variables": variables},
            headers=self._headers(),
        )
        if resp.status_code != 200:
            raise Exception(f"Linear API error ({resp.status_code}): {resp.text}")
        data = resp.json()
        if "errors" in data:
            raise Exception(f"GraphQL error: {data['errors']}")
        return data

    def fetch_issue(self, issue_identifier: str) -> LinearIssue:
        """Fetch issue details by identifier (e.g. 'ENG-3')."""
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
            }
        }
        """
        data = self._post(query, {"id": issue_identifier})
        issue = data.get("data", {}).get("issue")
        if not issue:
            raise Exception(f"Issue '{issue_identifier}' not found in Linear.")
        return LinearIssue(
            internal_id=issue["id"],
            ticket_id=issue["identifier"],
            ticket_title=issue["title"],
            ticket_description=issue.get("description") or "No description provided.",
        )

    def post_comment(self, issue_id: str, body: str) -> bool:
        """Post a Markdown comment to a Linear issue."""
        mutation = """
        mutation CreateComment($issueId: String!, $body: String!) {
            commentCreate(input: { issueId: $issueId, body: $body }) {
                success
            }
        }
        """
        data = self._post(mutation, {"issueId": issue_id, "body": body})
        return data.get("data", {}).get("commentCreate", {}).get("success", False)

    def post_report(self, issue_id: str, result, artifact_names) -> bool:
        """Post a formatted execution report to a Linear issue."""
        status = "✅ PASSED" if result.passed else "⚠️ FAILED / MANUAL REVIEW REQUIRED"
        body = (
            "### 🤖 Spec-Driven Framework Execution Report\n\n"
            f"**Status:** {status}\n\n"
            f"**Artifacts:** {', '.join(artifact_names) if artifact_names else 'none'}\n\n"
            "*Generated automatically by spec-driven-framework.*"
        )
        return self.post_comment(issue_id, body)

    def _query(self, query: str, variables: dict) -> dict:
        """Alias for _post to keep call sites readable."""
        return self._post(query, variables)