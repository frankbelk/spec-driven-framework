"""Code execution tools for agents."""
from __future__ import annotations

import os
import subprocess
import sys

from tools.file_operations import clean_markdown_fences

# Maps file extensions to the runtime command used to execute them.
RUNTIME_COMMANDS = {
    ".py": [sys.executable],
    ".js": ["node"],
    ".mjs": ["node"],
    ".cjs": ["node"],
    ".sh": ["bash"],
}


def validate_html_file(file_path: str) -> str:
    """Statically validate an HTML file (parse check + required structural tags)."""
    from html.parser import HTMLParser

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        return "STATUS: FAILED\nERROR: HTML file is empty."

    try:
        parser = HTMLParser()
        parser.feed(content)
        parser.close()
    except Exception as e:
        return f"STATUS: FAILED\nHTML PARSE ERROR: {str(e)}"

    lowered = content.lower()
    missing = [tag for tag in ("<html", "<body") if tag not in lowered]
    if missing:
        return f"STATUS: FAILED\nERROR: HTML is missing required structural tags: {', '.join(missing)}"

    return "STATUS: SUCCESS\nHTML file parsed cleanly and contains required structural tags."


def execute_script(script_path: str) -> str:
    """Execute or validate a local source file based on its extension."""
    if not os.path.exists(script_path):
        return f"ERROR: File '{script_path}' does not exist on disk."

    clean_markdown_fences(script_path)
    ext = os.path.splitext(script_path)[1].lower()

    # Static web entry points are validated, not executed.
    if ext in (".html", ".htm"):
        try:
            return validate_html_file(script_path)
        except Exception as e:
            return f"STATUS: FAILED\nEXCEPTION: {str(e)}"

    if ext not in RUNTIME_COMMANDS:
        supported = sorted(list(RUNTIME_COMMANDS.keys()) + [".html", ".htm"])
        return f"ERROR: Unsupported file type '{ext}'. Supported types: {', '.join(supported)}"

    try:
        result = subprocess.run(
            RUNTIME_COMMANDS[ext] + [script_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return f"STATUS: SUCCESS\nSTDOUT:\n{result.stdout}"
        return f"STATUS: FAILED (Exit Code {result.returncode})\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
    except FileNotFoundError:
        return f"STATUS: FAILED\nEXCEPTION: Runtime for '{ext}' ({RUNTIME_COMMANDS[ext][0]}) is not installed."
    except Exception as e:
        return f"STATUS: FAILED\nEXCEPTION: {str(e)}"