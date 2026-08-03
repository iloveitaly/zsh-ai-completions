"""Single-turn LLM calls via a selectable AI CLI (`ZSH_AI_CLI`).

Supported values for ``ZSH_AI_CLI`` (default: ``grok``):

- ``grok`` — Grok Build CLI (native ``--json-schema``)
- ``agy`` — Antigravity CLI (``--print`` / plan mode; schema enforced in-prompt)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from typing import Any

DEFAULT_CLI = "grok"
SUPPORTED_CLIS = ("grok", "agy")


def get_ai_cli() -> str:
    """Return the configured AI CLI name (lowercased)."""
    raw = (os.environ.get("ZSH_AI_CLI") or DEFAULT_CLI).strip().lower()
    if raw not in SUPPORTED_CLIS:
        supported = ", ".join(SUPPORTED_CLIS)
        raise RuntimeError(
            f"Unsupported ZSH_AI_CLI={raw!r}. Supported values: {supported}."
        )
    return raw


def _compose_prompt(prompt: str, context: str = "") -> str:
    if not context:
        return prompt
    return f"""\
{prompt}

---

{context}
"""


def _extract_json(raw: str) -> Any:
    """Parse JSON from model output, tolerating markdown fences / preamble."""
    text = raw.strip()
    if not text:
        raise RuntimeError("Empty model output; expected JSON.")

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError(f"Could not parse JSON from model output: {raw[:500]}")
        return json.loads(text[start : end + 1])


def _schema_instruction(schema: dict[str, Any]) -> str:
    return f"""\
Respond with ONLY a JSON object matching this JSON Schema (no markdown fences, no commentary):
{json.dumps(schema, indent=2)}
"""


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


def _run_agy(prompt: str) -> str:
    """Run agy headless print mode (plan) and return stdout text."""
    timeout = (os.environ.get("ZSH_AI_PRINT_TIMEOUT") or "5m").strip() or "5m"
    cmd = [
        "agy",
        "--mode",
        "plan",
        "--print-timeout",
        timeout,
        "--print",
        prompt,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"agy failed (exit {e.returncode}): {e.stderr or e.stdout}"
        ) from e

    out = (result.stdout or "").strip()
    if not out:
        err = (result.stderr or "").strip()
        raise RuntimeError(f"agy produced no stdout.{(' stderr: ' + err) if err else ''}")
    return out


def call_llm(prompt: str, context: str = "", *, max_turns: int = 16) -> str:
    """Return plain-text model output for prompt (+ optional context)."""
    if context:
        # Instructions first, context, then a final contract (recency bias).
        full = f"""\
{prompt}

---

{context}

---
Respond with the raw Zsh completion file only.
First line must be #compdef …; no markdown; no commentary.
"""
    else:
        full = prompt

    cli = get_ai_cli()
    if cli == "grok":
        return _run_grok(["--output-format", "plain"], full, max_turns=max_turns).strip()
    if cli == "agy":
        return _run_agy(full).strip()
    raise RuntimeError(f"Unsupported AI CLI: {cli}")


def call_llm_json(
    prompt: str,
    schema: dict[str, Any],
    context: str = "",
    *,
    max_turns: int = 2,
) -> Any:
    """Return structured JSON matching schema."""
    cli = get_ai_cli()
    full = _compose_prompt(prompt, context)

    if cli == "grok":
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

    if cli == "agy":
        # agy has no native JSON-schema mode; embed the schema in the prompt.
        instructed = f"""\
{full}

---

{_schema_instruction(schema)}
"""
        return _extract_json(_run_agy(instructed))

    raise RuntimeError(f"Unsupported AI CLI: {cli}")
