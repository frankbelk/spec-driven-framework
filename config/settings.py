"""Centralized configuration for the spec-driven-framework.

All environment variables are read here and exposed as module-level constants.
Secrets are loaded from AWS Secrets Manager in production (see
integrations/aws/secrets.py) or from a local .env file during development.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Load local .env (no-op in production where secrets come from Secrets Manager).
load_dotenv()

# ---------------------------------------------------------------------------
# Core paths
# ---------------------------------------------------------------------------
# Working directory where pipeline artifacts (spec.md, solution.py,
# test_results.txt, audit_report.txt) are written. Defaults to the current
# directory for local CLI use; override in Lambda/ECS (e.g. /tmp).
WORKDIR = Path(os.getenv("SDD_WORKDIR", os.getcwd()))
WORKDIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
MODEL_NAME = os.getenv("SDD_MODEL", "openrouter/nvidia/nemotron-3-super-120b-a12b:free")
LLM_BASE_URL = os.getenv("SDD_LLM_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ---------------------------------------------------------------------------
# Integrations
# ---------------------------------------------------------------------------
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "")
LINEAR_API_URL = os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql")

GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")  # e.g. "frankbelk/spec-driven-framework"

# ---------------------------------------------------------------------------
# AWS
# ---------------------------------------------------------------------------
S3_BUCKET = os.getenv("SDD_S3_BUCKET", "")
SECRETS_ARN = os.getenv("SDD_SECRETS_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

# ---------------------------------------------------------------------------
# Pipeline behaviour
# ---------------------------------------------------------------------------
DEFAULT_MAX_RETRIES = int(os.getenv("SDD_MAX_RETRIES", "3"))
# Maximum number of coder/testers to spin up for a single task.
MAX_CODERS = int(os.getenv("SDD_MAX_CODERS", "5"))
MAX_TESTERS = int(os.getenv("SDD_MAX_TESTERS", "5"))