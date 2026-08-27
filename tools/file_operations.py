"""File operation tools exposed to agents."""
from __future__ import annotations

import os
import re


def clean_markdown_fences(file_path: str) -> None:
    """Strip markdown code fences (```python ... ```) from output scripts."""
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    lines = content.split("\n")
    if lines and lines[0].strip().startswith("```"):
        lines.pop(0)
    if lines and lines[-1].strip().startswith("```"):
        lines.pop(-1)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip())


def write_source_file(file_path: str, content: str) -> str:
    """Write raw source code content to a local file (any language)."""
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        clean_markdown_fences(file_path)
        return f"SUCCESS: Wrote {file_path}"
    except Exception as e:
        return f"ERROR: Could not write '{file_path}': {str(e)}"


def extract_entry_point(spec_path: str = "spec.md", default: str = "solution.py") -> str:
    """Read the entry point filename declared by the architect in spec.md."""
    if not os.path.exists(spec_path):
        return default
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"Entry Point:\s*`?([\w.\-/]+)`?", content, re.IGNORECASE)
    return match.group(1) if match else default