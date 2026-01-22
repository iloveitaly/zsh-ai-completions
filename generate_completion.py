import sys
import subprocess
import os

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
                    return code_block[first_line_end+1:].strip()
            return code_block.strip()
    return output

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_completion.py <program_name> [help_file]", file=sys.stderr)
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

    # Call Gemini
    # We pass the prompt as the "prompt" argument and help_content as stdin (context)
    try:
        # We use the -p flag or positional argument. 
        # Using positional argument is safer for recent gemini CLI versions.
        cmd = ["gemini", "-m", "gemini-3-pro-preview", prompt]
        
        result = subprocess.run(
            cmd,
            input=help_content,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(clean_output(result.stdout))

    except subprocess.CalledProcessError as e:
        print(f"Error calling gemini: {e}", file=sys.stderr)
        print(f"Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
