"""Single-turn LLM calls via the grok CLI."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from typing import Any

def _run_grok(args: list[str], prompt: str, *, max_turns: int = 1) -> str:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_path = f.name

    try:
        cmd = [
            "grok",
            "--prompt-file",
            prompt_path,
            "--max-turns",
            str(max_turns),
            "--no-subagents",
            "--disable-web-search",
            # Empty allow-list: do not run tools (avoids "I'll inspect the repo…" preambles).
            "--tools",
            "",
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


def call_llm(prompt: str, context: str = "", *, max_turns: int = 16) -> str:
    """Return plain-text model output for prompt (+ optional context)."""
    if context:
        # Instructions first, context, then a final one-line contract (recency).
        full = (
            f"{prompt}\n\n"
            f"---\n\n"
            f"{context}\n\n"
            f"---\n"
            f"Respond with the raw Zsh completion file only. "
            f"First line must be #compdef …; no markdown; no commentary."
        )
    else:
        full = prompt
    return _run_grok(["--output-format", "plain"], full, max_turns=max_turns).strip()


def call_llm_json(
    prompt: str,
    schema: dict[str, Any],
    context: str = "",
    *,
    max_turns: int = 2,
) -> Any:
    """Return structured JSON matching schema (via grok --json-schema)."""
    full = prompt if not context else f"{prompt}\n\n---\n\n{context}"
    raw = _run_grok(
        ["--json-schema", json.dumps(schema)],
        full,
        max_turns=max_turns,
    )
    data = json.loads(raw)
    if isinstance(data, dict):
        if "structuredOutput" in data and data["structuredOutput"] is not None:
            return data["structuredOutput"]
        # Fallback: model put JSON in text field
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
    return data
