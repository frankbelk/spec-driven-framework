"""CLI entry point for the spec-driven-framework.

Usage:
    python -m cli.main <LINEAR_ISSUE_ID> [max_retries]
"""
from __future__ import annotations

import sys

from core.pipeline import PipelineRunner


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m cli.main <LINEAR_ISSUE_ID> [max_retries]")
        print("Example: python -m cli.main ENG-3")
        return 1

    issue_identifier = sys.argv[1]
    try:
        max_retries = int(sys.argv[2]) if len(sys.argv) > 2 else None
    except ValueError:
        print(f"Error: max_retries must be an integer, got '{sys.argv[2]}'.")
        return 1

    runner = PipelineRunner()
    result = runner.run(issue_identifier, max_retries=max_retries)
    print(f"\nPipeline complete: {result.to_dict()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())