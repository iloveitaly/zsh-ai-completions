import re
import subprocess
import sys
import json
import logging
import os

# Set up logging
logging.basicConfig(
    level=getattr(logging, (os.environ.get("LOG_LEVEL") or "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)


def run_help_command(command):
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        output = result.stdout + result.stderr if result.stderr else result.stdout
        logging.debug(f"Command output: {output}")
        if not output:
            logging.warning(f"No output from command: {' '.join(command)}")
            return None
        return output
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running command {' '.join(command)}: {e}")
        output = e.stdout + e.stderr if e.stderr else e.stdout
        if not output:
            logging.warning(f"No output from failed command: {' '.join(command)}")
            return None
        return output


HELP_MARKERS = (
    "usage:",
    "commands:",
    "options:",
    "additional commands:",
    "help for",
    "flags:",
    "arguments:",
    "subcommands:",
    "describe available commands",
    "manage ",
)


ERROR_MARKERS = (
    "no such file or directory",
    "failed to execute",
    "error:",
)


def looks_like_help(output):
    """Heuristic to tell help text apart from normal command output."""
    if not output:
        return False
    lower = output.lower()
    if any(marker in lower for marker in ERROR_MARKERS):
        return False
    return any(marker in lower for marker in HELP_MARKERS)


def help_command_candidates(program, args):
    """Yield help invocations to try, from most to least specific."""
    yield [program] + args + ["help"]
    if len(args) == 1:
        # Some CLIs expose namespace help via `<namespace>:help` instead of flags.
        yield [program, f"{args[0]}:help"]
    yield [program] + args + ["--help"]


def get_help_output(program, args):
    """Return (help_output, command) using the first strategy that looks like help."""
    command = None
    fallback_output = None
    fallback_command = None

    for command in help_command_candidates(program, args):
        output = run_help_command(command)
        if not output:
            continue
        if looks_like_help(output):
            return output, command
        if fallback_output is None and not any(
            marker in output.lower() for marker in ERROR_MARKERS
        ):
            fallback_output = output
            fallback_command = command

    if fallback_output is not None:
        logging.info(
            f"No help markers found; using output from: {' '.join(fallback_command)}"
        )
        return fallback_output, fallback_command

    return None, command


def should_recurse_into_subcommands(help_output):
    """Skip recursion when help already lists fully qualified colon commands."""
    colon_commands = re.findall(
        r"^\s+([\w-]+:[\w-]+(?::[\w-]+)?)",
        help_output,
        re.MULTILINE,
    )
    return len(colon_commands) < 2


def get_subcommands(program, args):
    help_output, command = get_help_output(program, args)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command)}")
        return []

    if not should_recurse_into_subcommands(help_output):
        logging.info("Help output already lists colon-qualified subcommands; not recursing")
        return []

    llm_prompt = (
        "Analyze this help output and return a JSON object with two keys: "
        "'has_subcommands' (boolean) and 'subcommands' (list of strings). "
        "If there are no subcommands, return an empty list for 'subcommands'. "
        "Ignore any `help` subcommands. "
        "Respond with a single JSON object and nothing else. Do not use markdown formatting (i.e. ```).\n\n"
        "For example, for a tool with 'init' and 'clone' subcommands, the output should be:\n"
        '{"has_subcommands": true, "subcommands": ["init", "clone"]}\n\n'
        "If no subcommands are found, the output should be:\n"
        '{"has_subcommands": false, "subcommands": []}\n\n'
    )

    logging.info("Sending help output to LLM for analysis")
    try:
        llm_result = subprocess.run(
            [
                "gemini",
                "-m",
                "gemini-3-pro-preview",
                "-p",
                llm_prompt,
            ],
            input=help_output,
            capture_output=True,
            text=True,
            check=True,
        )
        llm_output = llm_result.stdout.strip()
        logging.debug(f"LLM output: {llm_output}")
        subcommand_data = json.loads(llm_output)
        subcommands = subcommand_data.get("subcommands", [])
        logging.info(f"Found subcommands: {subcommands}")
        return subcommands
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Error processing subcommands: {e}")

        if isinstance(e, subprocess.CalledProcessError):
            logging.error(f"stderr: {e.stderr}")
            logging.error(f"stdout: {e.stdout}")
        return []


def explore_command(program, args=None, depth=0):
    if args is None:
        args = []

    logging.info(f"Exploring command: {program} {' '.join(args)}")
    help_output, command = get_help_output(program, args)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command)}")
        return ""

    markdown = f"{'#' * (depth + 2)} {' '.join([program] + args)}\n\n"
    markdown += "```\n" + help_output.strip() + "\n```\n\n"

    subcommands = get_subcommands(program, args)

    for subcommand in subcommands:
        markdown += explore_command(program, args + [subcommand], depth + 1)

    return markdown


def main():
    if len(sys.argv) != 2:
        logging.error("Invalid number of arguments")
        print("Usage: python explore_program.py <program_name>", file=sys.stderr)
        sys.exit(1)

    program = sys.argv[1]
    logging.info(f"Starting exploration of program: {program}")
    markdown = f"# {program} Help\n\n"
    markdown += explore_command(program)

    print(markdown)
    logging.info("Exploration completed")


if __name__ == "__main__":
    main()
