"""Core pipeline orchestration for the spec-driven-framework.

This module defines the main pipeline that:
  1. Fetches a Linear issue (source of truth)
  2. Assesses task complexity and scales agents accordingly
  3. Runs the Architect -> Coder(s) <-> Tester(s) -> Auditor phases
  4. Commits artifacts to a feature branch and raises a PR
  5. Posts the execution report back to Linear
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from config import settings
from agents.factory import AgentFactory
from agents.manager.complexity import assess_complexity
from integrations.linear.client import LinearClient
from integrations.github.git_ops import GitOps
from storage.artifact_store import ArtifactStore

logger = logging.getLogger(__name__)


class PipelineResult:
    """Result object returned by the pipeline."""

    def __init__(self, ticket_id: str, status: str, branch: Optional[str] = None,
                 pr_url: Optional[str] = None, artifacts: Optional[List[str]] = None):
        self.ticket_id = ticket_id
        self.status = status
        self.branch = branch
        self.pr_url = pr_url
        self.artifacts = artifacts or []

    def to_dict(self) -> Dict:
        return {
            "ticket_id": self.ticket_id,
            "status": self.status,
            "branch": self.branch,
            "pr_url": self.pr_url,
            "artifacts": self.artifacts,
        }


class PipelineRunner:
    """Runs the spec-driven pipeline for a given Linear issue."""

    def __init__(self, linear_client: Optional[LinearClient] = None,
                 github_ops: Optional[GitOps] = None,
                 artifact_store: Optional[ArtifactStore] = None,
                 agent_factory: Optional[AgentFactory] = None):
        self.linear = linear_client or LinearClient()
        self.github = github_ops or GitOps()
        self.artifacts = artifact_store or ArtifactStore()
        self.factory = agent_factory or AgentFactory()

    def run(self, issue_identifier: str, max_retries: int = None) -> PipelineResult:
        """Run the full pipeline for a Linear issue."""
        max_retries = max_retries or settings.DEFAULT_MAX_RETRIES

        # 1. Fetch the issue (source of truth).
        issue = self.linear.fetch_issue(issue_identifier)
        logger.info("Loaded [%s] %s", issue.ticket_id, issue.ticket_title)

        # 2. Assess complexity to decide how many agents to spin up.
        complexity = assess_complexity(issue)
        logger.info("Complexity: %s (coders=%d, testers=%d)",
                    complexity.level, complexity.coders, complexity.testers)

        # 3. Create a feature branch for this issue.
        branch = self.github.create_feature_branch(issue.ticket_id)
        logger.info("Created feature branch: %s", branch)

        # 4. Build the crew (agents + tasks) based on complexity.
        crew = self.factory.build_crew(issue, complexity, max_retries)

        # 5. Run the crew.
        result = crew.kickoff()

        # 6. Persist artifacts.
        artifact_names = self.artifacts.persist_all()
        logger.info("Persisted artifacts: %s", artifact_names)

        # 7. Commit and raise a PR.
        self.github.commit_artifacts(branch, artifact_names)
        pr_url = self.github.create_pull_request(branch, issue.ticket_id, issue.ticket_title)

        # 8. Post report back to Linear.
        self.linear.post_report(issue.internal_id, result, artifact_names)

        return PipelineResult(
            ticket_id=issue.ticket_id,
            status="PASSED" if result.passed else "FAILED",
            branch=branch,
            pr_url=pr_url,
            artifacts=artifact_names,
        )