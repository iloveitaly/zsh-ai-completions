# Agent guidelines

## Never edit completion scripts directly

Files under `completions/` are **generated output**. Do not hand-fix or rewrite them.

When a completion is wrong or incomplete:

1. Update the shared prompt (`completion_prompt.md`) and/or a tool-specific prompt (`prompts/<program>.md`).
2. Regenerate with `just completion <program>` (or `just` for all).
3. Validate with `./test_completion.zsh completions/_<program>` or `just test`.

If generation fails (missing LLM CLI/auth), fix the **generator / prompts / environment** — still do not patch `completions/_…` by hand.

## Custom prompts

Optional per-command guidance lives in `prompts/<program>.md` and is appended to `completion_prompt.md` at generation time. Prefer tightening these prompts over editing generated zsh.

Keep `prompts/*.md` limited to instructions for the model. Local machine paths and test fixtures belong here (or in the README), not in generation prompts.

## Local fixtures

- **Alembic** (installed + real migrations for testing revision completion):  
  `/Users/mike/Projects/python/python-starter-template`
