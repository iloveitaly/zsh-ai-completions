"""Single-turn LLM calls via the grok CLI."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any


def _run_grok(args: list[str], prompt: str) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_path = f.name

    try:
        cmd = [
            "grok",
            "--prompt-file",
            prompt_path,
            "--max-turns",
            "1",
            "--no-subagents",
            "--disable-web-search",
            *args,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"grok failed (exit {e.returncode}): {e.stderr or e.stdout}"
        ) from e
    finally:
        os.unlink(prompt_path)


def call_llm(prompt: str, context: str = "") -> str:
    """Return plain-text model output for prompt (+ optional context)."""
    full = prompt if not context else f"{prompt}\n\n---\n\n{context}"
    return _run_grok(["--output-format", "plain"], full).strip()


def call_llm_json(prompt: str, schema: dict[str, Any], context: str = "") -> Any:
    """Return structured JSON matching schema (via grok --json-schema)."""
    full = prompt if not context else f"{prompt}\n\n---\n\n{context}"
    raw = _run_grok(["--json-schema", json.dumps(schema)], full)
    data = json.loads(raw)
    if "structuredOutput" in data:
        return data["structuredOutput"]
    # Fallback: model put JSON in text
    if "text" in data:
        return json.loads(data["text"])
    return data
