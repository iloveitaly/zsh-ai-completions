import argparse
import os
import subprocess
import sys


def clean_output(output):
    """
    Cleans the LLM output to extract just the code.
    Removes markdown code blocks if present.
    """
    output = output.strip()
    if "```" in output:
        parts = output.split("```")
        if len(parts) >= 3:
            code_block = parts[1]
            if "\n" in code_block:
                first_line_end = code_block.find("\n")
                first_line = code_block[:first_line_end].strip()
                if not first_line or "zsh" in first_line or "sh" in first_line:
                    return code_block[first_line_end+1:].strip()
            return code_block.strip()
    return output


def read_prompt(program_name):
    """Read and prepare the completion prompt template."""
    try:
        with open("completion_prompt.md", "r") as f:
            return f.read().replace("<command>", program_name)
    except FileNotFoundError:
        print("Error: completion_prompt.md not found.", file=sys.stderr)
        sys.exit(1)


def read_help_content(help_file):
    """Read help content from file or stdin."""
    if help_file:
        try:
            with open(help_file, "r") as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Help file {help_file} not found.", file=sys.stderr)
            sys.exit(1)
    return sys.stdin.read()


def build_cmd(cli, model_flag, model, prompt):
    """Build the CLI command list."""
    cmd = [cli]
    if model:
        cmd.extend([model_flag, model])
    cmd.append(prompt)
    return cmd


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a Zsh completion script using an LLM CLI"
    )
    parser.add_argument("program_name", help="Name of the program to generate completions for")
    parser.add_argument("help_file", nargs="?", default=None, help="Path to help file (reads stdin if omitted)")
    parser.add_argument("--cli", default=os.environ.get("AI_CLI", "gemini"), help="LLM CLI binary (default: gemini)")
    parser.add_argument("--model", default=os.environ.get("AI_MODEL", ""), help="Model name (omit to use CLI default)")
    parser.add_argument("--model-flag", default=os.environ.get("AI_MODEL_FLAG", "-m"), help="Flag syntax for model selection (default: -m)")
    return parser.parse_args()


def main():
    args = parse_args()
    prompt = read_prompt(args.program_name)
    help_content = read_help_content(args.help_file)
    cmd = build_cmd(args.cli, args.model_flag, args.model, prompt)

    try:
        result = subprocess.run(
            cmd,
            input=help_content,
            capture_output=True,
            text=True,
            check=True,
        )
        print(clean_output(result.stdout))
    except subprocess.CalledProcessError as e:
        print(f"Error calling {args.cli}: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
