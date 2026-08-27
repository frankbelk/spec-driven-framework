"""Task complexity assessment.

Determines how many coder and tester agents to spin up based on the Linear
issue. Simple issues get 1 coder + 1 tester; complex issues scale up to
MAX_CODERS / MAX_TESTERS.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config import settings


@dataclass
class Complexity:
    """Complexity assessment result."""
    level: str          # "low" | "medium" | "high"
    coders: int
    testers: int
    score: int


# Keywords that hint at a complex task.
_COMPLEXITY_KEYWORDS = [
    "complex", "large", "multi", "multiple", "microservice", "api", "database",
    "integration", "authentication", "scalable", "distributed", "full stack",
    "frontend", "backend", "end-to-end", "e2e", "refactor", "migration",
]


def _score_issue(issue) -> int:
    """Heuristic score based on title + description length and keywords."""
    text = f"{issue.ticket_title} {issue.ticket_description}".lower()
    score = 0
    # Length-based signal.
    if len(text) > 2000:
        score += 3
    elif len(text) > 1000:
        score += 2
    elif len(text) > 500:
        score += 1
    # Keyword-based signal.
    for kw in _COMPLEXITY_KEYWORDS:
        if kw in text:
            score += 1
    return score


def assess_complexity(issue) -> Complexity:
    """Assess complexity and return the number of coders/testers to spin up."""
    score = _has_issue(issue)

    if score >= 6:
        level = "high"
        coders = min(settings.MAX_CODERS, 3)
        testers = min(settings.MAX_TESTERS, 2)
    elif score >= 3:
        level = "medium"
        coders = min(settings.MAX_CODERS, 2)
        testers = min(settings.MAX_TESTERS, 2)
    else:
        level = "low"
        coders = 1
        testers = 1

    return Complexity(level=level, coders=coders, testers=testers, score=score)


def _has_issue(issue) -> int:
    """Compute the complexity score for an issue."""
    return _score_issue(issue)