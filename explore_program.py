import subprocess
import sys
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)


def run_help_command(command):
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.debug(f"Command output: {result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running command {' '.join(command)}: {e}")
        return None


def get_subcommands(program, args):
    command = [program] + args + ["--help"]
    help_output = run_help_command(command)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command)}")
        return []

    cody_prompt = (
        "Analyze this help output and return a JSON object with two keys: "
        "'has_subcommands' (boolean) and 'subcommands' (list of strings). "
        "If there are no subcommands, return an empty list for 'subcommands'. "
        "Only return the JSON object, no other text."
    )

    logging.info("Sending help output to Cody for analysis")
    try:
        cody_result = subprocess.run(
            [
                "cody",
                "chat",
                "--stdin",
                cody_prompt,
            ],
            input=help_output,
            capture_output=True,
            text=True,
            check=True,
        )
        cody_output = cody_result.stdout.strip()
        logging.debug(f"Cody output: {cody_output}")
        subcommand_data = json.loads(cody_output)
        subcommands = subcommand_data.get("subcommands", [])
        logging.info(f"Found subcommands: {subcommands}")
        return subcommands
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logging.error(f"Error processing subcommands: {e}")
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
