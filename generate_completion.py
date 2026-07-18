import sys

from llm import call_llm


def clean_output(output):
    """
    Cleans the LLM output to extract just the code.
    Removes markdown code blocks if present.
    """
    output = output.strip()
    if "```" in output:
        parts = output.split("```")
        # Usually the code is in the second part (index 1)
        if len(parts) >= 3:
            code_block = parts[1]
            # Remove language identifier line if it exists (e.g. "zsh")
            if "\n" in code_block:
                first_line_end = code_block.find("\n")
                first_line = code_block[:first_line_end].strip()
                # If the first line is just a language name or empty, skip it
                if not first_line or "zsh" in first_line or "sh" in first_line:
                    return code_block[first_line_end + 1 :].strip()
            return code_block.strip()
    return output


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_completion.py <program_name> [help_file]",
            file=sys.stderr,
        )
        sys.exit(1)

    program_name = sys.argv[1]
    help_file = sys.argv[2] if len(sys.argv) > 2 else None

    # Read the prompt
    try:
        with open("completion_prompt.md", "r") as f:
            prompt = f.read()
    except FileNotFoundError:
        print("Error: completion_prompt.md not found.", file=sys.stderr)
        sys.exit(1)

    # Replace placeholder if any (though currently the prompt is generic)
    prompt = prompt.replace("<command>", program_name)

    # Check for command-specific prompt
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

    # Read help content
    if help_file:
        try:
            with open(help_file, "r") as f:
                help_content = f.read()
        except FileNotFoundError:
            print(f"Error: Help file {help_file} not found.", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        help_content = sys.stdin.read()

    try:
        output = call_llm(prompt, context=help_content)
        print(clean_output(output))
    except RuntimeError as e:
        print(f"Error calling grok: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
