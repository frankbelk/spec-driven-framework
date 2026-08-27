#!/usr/bin/env bash
# test_hello_world.sh
#
# Creates a Linear issue for a "hello world" page and runs the spec-driven
# pipeline against it. Verifies the pipeline produces a hello world page.
#
# Usage:
#   ./scripts/test_hello_world.sh
set -euo pipefail

# Load .env if present.
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

: "${LINEAR_API_KEY:?LINEAR_API_KEY is required}"
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY is required}"

LINEAR_URL="https://api.linear.app/graphql"
# The team to create the issue in. Override with LINEAR_TEAM_ID if needed.
LINEAR_TEAM_ID="${LINEAR_TEAM_ID:-88ce3c8a-0cfb-419a-b07e-7c86397f086b}"

echo "=== Creating Linear issue for hello world page ==="

# Create the issue via Linear GraphQL API.
CREATE_RESPONSE=$(curl -s -X POST "$LINEAR_URL" \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mutation IssueCreate(\$title: String!, \$description: String!) { issueCreate(input: { teamId: \\\"$LINEAR_TEAM_ID\\\", title: \$title, description: \$description }) { success issue { id identifier title } } }\",
    \"variables\": {
      \"title\": \"Create a hello world web page\",
      \"description\": \"Create a simple static HTML page that displays 'Hello, World!'. Entry Point: index.html\"
    }
  }")

echo "Create response: $CREATE_RESPONSE"

ISSUE_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['issueCreate']['issue']['identifier'])" 2>/dev/null || echo "")

if [ -z "$ISSUE_ID" ]; then
  echo "ERROR: Failed to create Linear issue."
  exit 1
fi

echo "Created Linear issue: $ISSUE_ID"

echo "== Running spec-driven pipeline for $ISSUE_ID =="
python3 -m cli.main "$ISSUE_ID"

echo "== Verifying hello world page was produced =="
if [ -f index.html ]; then
  echo "SUCCESS: index.html was produced."
  grep -qi "hello" index.html && echo "SUCCESS: index.html contains 'hello'." || echo "WARNING: index.html does not contain 'hello'."
else
  echo "FAILURE: index.html was not produced."
  exit 1
fi

echo "== Done =="