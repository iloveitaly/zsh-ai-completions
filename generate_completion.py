import sys

from llm import call_llm_json

# Force the model to put the script in a JSON string field so it cannot
# prepend conversational preamble (a common failure mode of plain text).
_COMPLETION_SCHEMA = {
    "type": "object",
    "properties": {
        "zsh_completion": {
            "type": "string",
            "description": (
                "Complete Zsh completion script file contents only. "
                "First line must be #compdef <command>. No markdown fences, "
                "no commentary."
            ),
        }
    },
    "required": ["zsh_completion"],
}


def clean_output(output: str) -> str:
    """Normalize model script text (fence strip only; no #compdef search)."""
    output = output.strip()
    if "```" not in output:
        return output

    parts = output.split("```")
    if len(parts) < 3:
        return output

    code_block = parts[1]
    if "\n" in code_block:
        first_line_end = code_block.find("\n")
        first_line = code_block[:first_line_end].strip()
        if not first_line or "zsh" in first_line or "sh" in first_line:
            return code_block[first_line_end + 1 :].strip()
    return code_block.strip()


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_completion.py <program_name> [help_file]",
            file=sys.stderr,
        )
        sys.exit(1)

    program_name = sys.argv[1]
    help_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        with open("completion_prompt.md", "r") as f:
            prompt = f.read()
    except FileNotFoundError:
        print("Error: completion_prompt.md not found.", file=sys.stderr)
        sys.exit(1)

    prompt = prompt.replace("<command>", program_name)

    custom_prompt_file = f"prompts/{program_name}.md"
    try:
        with open(custom_prompt_file, "r") as f:
            prompt += "\n\n" + f.read()
    except FileNotFoundError:
        pass
    except OSError as e:
        print(
            f"Warning: Could not read custom prompt {custom_prompt_file}: {e}",
            file=sys.stderr,
        )

    prompt += (
        "\n\nReturn a JSON object whose `zsh_completion` string is the entire "
        "completion file (starting with #compdef)."
    )

    if help_file:
        try:
            with open(help_file, "r") as f:
                help_content = f.read()
        except FileNotFoundError:
            print(f"Error: Help file {help_file} not found.", file=sys.stderr)
            sys.exit(1)
    else:
        help_content = sys.stdin.read()

    schema = {
        **_COMPLETION_SCHEMA,
        "properties": {
            "zsh_completion": {
                **_COMPLETION_SCHEMA["properties"]["zsh_completion"],
                "description": (
                    f"Complete Zsh completion script for {program_name}. "
                    f"First line must be #compdef {program_name}. "
                    "No markdown fences, no commentary."
                ),
            }
        },
    }

    try:
        data = call_llm_json(prompt, schema, context=help_content, max_turns=16)
        script = data.get("zsh_completion", "") if isinstance(data, dict) else ""
        if not isinstance(script, str) or not script.strip():
            print("Error: model returned empty zsh_completion.", file=sys.stderr)
            sys.exit(1)
        print(clean_output(script))
    except (RuntimeError, TypeError, AttributeError, KeyError) as e:
        print(f"Error calling grok: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
