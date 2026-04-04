import argparse
import json
import logging
import os
import subprocess
import sys

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


def build_llm_cmd(cli, model_flag, model, prompt):
    """Build the LLM CLI command list."""
    cmd = [cli]
    if model:
        cmd.extend([model_flag, model])
    cmd.extend(["-p", prompt])
    return cmd


def get_subcommands(program, args, cli, model_flag, model):
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
    cmd = build_llm_cmd(cli, model_flag, model, llm_prompt)
    try:
        llm_result = subprocess.run(
            cmd,
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


def explore_command(program, cli, model_flag, model, args=None, depth=0):
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

    subcommands = get_subcommands(program, args, cli, model_flag, model)

    for subcommand in subcommands:
        markdown += explore_command(program, cli, model_flag, model, args + [subcommand], depth + 1)

    return markdown


def parse_args():
    parser = argparse.ArgumentParser(
        description="Explore a program's help output and subcommands using an LLM CLI"
    )
    parser.add_argument("program_name", help="Name of the program to explore")
    parser.add_argument("--cli", default=os.environ.get("AI_CLI", "gemini"), help="LLM CLI binary (default: gemini)")
    parser.add_argument("--model", default=os.environ.get("AI_MODEL", ""), help="Model name (omit to use CLI default)")
    args = parser.parse_args()
    args.model_flag = os.environ.get("AI_MODEL_FLAG", "--model")
    return args


def main():
    args = parse_args()
    logging.info(f"Starting exploration of program: {args.program_name}")

    markdown = f"# {args.program_name} Help\n\n"
    markdown += explore_command(args.program_name, args.cli, args.model_flag, args.model)

    print(markdown)
    logging.info("Exploration completed")


if __name__ == "__main__":
    main()
