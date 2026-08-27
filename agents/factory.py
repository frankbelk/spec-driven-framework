"""Agent factory: builds a crewAI crew with dynamically scaled agents.

Based on the assessed complexity, the factory spins up 1..N coder agents and
1..N tester agents. All agents share a single LLM configuration.
"""
from __future__ import annotations

import logging
from typing import List

from config import settings

logger = logging.getLogger(__name__)

# Lazy cache for the crewai module (importing crewai is expensive ~10s).
_crewai = None


def _get_crewai():
    """Import crewai lazily (first call only)."""
    global _crewai
    if _crewai is None:
        from crewai import Agent, Crew, Process, Task  # noqa: F401
        from crewai.tools import tool  # noqa: F401
        from crewai import LLM  # noqa: F401
        _crewai = (Agent, Crew, Process, Task, tool, LLM)
    return _crewai


class AgentFactory:
    """Builds crews with a dynamic number of agents based on complexity."""

    def __init__(self, model: str = None, base_url: str = None, api_key: str = None):
        self.model = model or settings.MODEL_NAME
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set.")

    def _build_llm(self):
        Agent, Crew, Process, Task, tool, LLM = _get_crewai()
        return LLM(model=self.model, base_url=self.base_url, api_key=self.api_key)

    def build_crew(self, issue, complexity, max_retries: int):
        """Build a crewai Crew with agents scaled to the task complexity."""
        Agent, Crew, Process, Task, tool, LLM = _get_crewai()
        llm = self._build_llm()

        # Wrap the plain tool functions with crewai's @tool decorator.
        from tools.file_operations import write_source_file
        from tools.execution import execute_script
        write_tool = tool("Write Source File")(write_source_file)
        execute_tool = tool("Execute Local Script")(execute_script)

        # Architect agent (always 1).
        architect = Agent(
            role="Principal System Architect",
            goal="Translate raw Linear tickets into concrete OpenSpec specifications.",
            backstory="You analyze requirements from Linear tickets and produce OpenSpec markdown docs.",
            llm=llm,
            verbose=True,
        )

        # Coder agents (1..N based on complexity).
        coders = []
        for i in range(complexity.coders):
            coders.append(Agent(
                role=f"Senior Full Stack Engineer #{i + 1}",
                goal="Implement executable, production-quality code in whatever tech stack the OpenSpec dictates.",
                backstory="You are a seasoned full stack engineer comfortable across frontend, backend, and tooling.",
                tools=[write_tool],
                llm=llm,
                verbose=True,
            ))

        # Tester agents (1..N based on complexity).
        testers = []
        for i in range(complexity.testers):
            testers.append(Agent(
                role=f"Senior QA Engineer #{i + 1}",
                goal="Run or validate generated source files end-to-end and capture execution outputs.",
                backstory="You are a senior QA engineer who executes or validates code in any language.",
                tools=[execute_tool],
                llm=llm,
                verbose=True,
            ))

        # Auditor agent (always 1).
        auditor = Agent(
            role="Code Quality & Spec Compliance Auditor",
            goal="Verify that final code meets spec requirements and passed testing.",
            backstory="You issue final compliance verification reports.",
            llm=llm,
            verbose=True,
        )

        # Build tasks.
        architect_task = Task(
            description=(
                "Review Linear Ticket [{ticket_id}]: {ticket_title}\n\n"
                "Description:\n{ticket_description}\n\n"
                "Choose the most appropriate tech stack and create an OpenSpec markdown file "
                "(`spec.md`) with Context, Tech Stack, Dependencies, Functions/Components, "
                "CLI or UI Contract, and Criteria.\n"
                "MANDATORY: Include a line formatted exactly as `Entry Point: <filename>`."
            ),
            expected_output="OpenSpec markdown file saved to spec.md with an `Entry Point:` declaration.",
            agent=architect,
            output_file="spec.md",
        )

        coder_tasks = []
        tester_tasks = []
        for i, coder in enumerate(coders):
            coder_task = Task(
                description=(
                    "Read `spec.md` from context and implement the solution.\n"
                    "Write the complete source code for the entry point file declared in the spec.\n"
                    "STRICT FORMATTING: Your final answer must be ONLY the raw source code with "
                    "ZERO markdown backticks."
                ),
                expected_output="Complete source code saved to the entry point file.",
                agent=coder,
                context=[architect_task],
                output_file=f"solution_{i}.py",
            )
            coder_tasks.append(coder_task)

        for i, tester in enumerate(testers):
            tester_task = Task(
                description=(
                    "Use `Execute Local Script` to run or validate the generated source file.\n"
                    "If it runs cleanly, output 'STATUS: SUCCESS'. Otherwise output 'STATUS: FAILED' "
                    "followed by the full error log."
                ),
                expected_output="Test report with STATUS: SUCCESS or STATUS: FAILED.",
                agent=tester,
                context=coder_tasks,
                output_file=f"test_results_{i}.txt",
            )
            tester_tasks.append(tester_task)

        auditor_task = Task(
            description=(
                "Review `spec.md`, the generated source files, and test results.\n"
                "Document final PASS/FAIL status for each requirement."
            ),
            expected_output="Final audit report saved to audit_report.txt.",
            agent=auditor,
            context=[architect_task] + coder_tasks + tester_tasks,
            output_file="audit_report.txt",
        )

        all_agents = [architect] + coders + testers + [auditor]
        all_tasks = [architect_task] + coder_tasks + tester_tasks + [auditor_task]

        return Crew(
            agents=all_agents,
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True,
        )