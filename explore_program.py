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


def get_subcommands(program, args):
    command = [program] + args + ["--help"]
    help_output = run_help_command(command)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command)}")
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
    command = [program] + args + ["--help"]
    help_output = run_help_command(command)

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
