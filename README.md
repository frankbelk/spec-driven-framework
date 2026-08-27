# spec-driven-framework

A spec-driven, multi-agent SDLC framework built on **crewAI**, with **Linear** as
the source of truth and **GitHub** for version control. Agents (Architect,
Coder(s), Tester(s), Auditor) collaborate to turn a Linear issue into a
feature branch and a pull request, ready for human review.

## Architecture

```
Linear (source of truth)
   │  webhook / CLI
   ▼
PipelineRunner
   │  assess complexity
   ▼
AgentFactory ──► crewAI Crew (Architect, N×Coder, N×Tester, Auditor)
   │
   ▼
ArtifactStore ──► local / S3
   │
   ▼
GitOps ──► feature branch + Pull Request
   │
   ▼
LinearClient ──► post execution report comment
```

## Directory layout

```
config/            Centralized settings
core/              Pipeline orchestration
agents/            Agent definitions + factory + complexity
tools/             Agent tools (file ops, execution)
integrations/      Linear, GitHub, AWS, LLM clients
storage/           Artifact persistence
orchestration/     K8s, message queue, workflow (scaling)
cli/               CLI entry point
lambda_handler/    AWS Lambda entry point
tests/             Unit + integration tests
k8s/               Kubernetes manifests for agent scaling
```

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment (copy .env.example to .env)
cp .env.example .env
#   - OPENROUTER_API_KEY
#   - LINEAR_API_KEY
#   - GITHUB_API_KEY
#   - GITHUB_REPO=frankbelk/spec-driven-framework

# 3. Run the pipeline for a Linear issue
python -m cli.main ENG-3
```

## Dynamic agent scaling

The framework assesses task complexity from the Linear issue (title + description
length and keywords) and spins up 1..N coder and tester agents accordingly:

- **Low complexity** → 1 coder + 1 tester
- **Medium complexity** → 2 coders + 2 testers
- **High complexity** → 3 coders + 2 testers

See [`agents/manager/complexity.py`](agents/manager/complexity.py).

## CI/CD (decoupled)

The agentic workflow is decoupled from CI/CD. Once a PR is raised, a separate
CI/CD pipeline (GitHub Actions / AWS CodePipeline) runs SAST, DAST, linting, and
tests against the PR — independent of how the code was generated.

## Testing

```bash
# Create a Linear issue for a "hello world" page and run the pipeline
./scripts/test_hello_world.sh