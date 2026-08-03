import re
import subprocess
import sys
import json
import logging
import os

from llm import call_llm_json

# Set up logging
logging.basicConfig(
    level=getattr(logging, (os.environ.get("LOG_LEVEL") or "INFO").upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)

# How long to wait for any single help probe before killing it.
# Interactive CLIs (bubbletea/TUI) can block forever on /dev/tty without this.
HELP_TIMEOUT_SECS = float(os.environ.get("EXPLORE_HELP_TIMEOUT", "10"))

# Cap recursion so large CLIs / LLM hallucinations cannot explode the tree.
MAX_DEPTH = int(os.environ.get("EXPLORE_MAX_DEPTH", "3"))

# Subcommand names that are never worth recursing into.
SKIP_SUBCOMMANDS = frozenset(
    {
        "help",
        "completion",
        "completions",
        "version",
        "--help",
        "-h",
        "--version",
    }
)


def _help_env():
    """Environment that steers CLIs away from pagers and interactive UIs."""
    env = os.environ.copy()
    env.setdefault("CI", "1")
    env.setdefault("NO_COLOR", "1")
    env.setdefault("TERM", "dumb")
    env.setdefault("PAGER", "cat")
    env.setdefault("MANPAGER", "cat")
    env.setdefault("GIT_PAGER", "cat")
    env.setdefault("GLAMOUR_STYLE", "notty")
    return env


def run_help_command(command):
    logging.info(f"Running command: {' '.join(command)}")
    try:
        # start_new_session so timeout can kill the whole process group (pagers,
        # TUI children, etc.), not just the parent.
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=HELP_TIMEOUT_SECS,
            stdin=subprocess.DEVNULL,
            env=_help_env(),
            start_new_session=True,
        )
        output = result.stdout + result.stderr if result.stderr else result.stdout
        logging.debug(f"Command output: {output}")
        if not output:
            logging.warning(f"No output from command: {' '.join(command)}")
            return None
        return output
    except subprocess.TimeoutExpired as e:
        logging.warning(
            f"Command timed out after {HELP_TIMEOUT_SECS}s (likely interactive/TUI): "
            f"{' '.join(command)}"
        )
        # Best-effort: reap any leftover process group members.
        if e.stdout or e.stderr:
            partial = (e.stdout or "") + (e.stderr or "")
            if isinstance(partial, bytes):
                partial = partial.decode("utf-8", errors="replace")
            if partial.strip():
                return partial
        return None
    except OSError as e:
        logging.error(f"Error running command {' '.join(command)}: {e}")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running command {' '.join(command)}: {e}")
        output = e.stdout + e.stderr if e.stderr else e.stdout
        if not output:
            logging.warning(f"No output from failed command: {' '.join(command)}")
            return None
        return output


HELP_MARKERS = (
    "usage:",
    "usage of ",
    "commands:",
    "options:",
    "additional commands:",
    "help for",
    "flags:",
    "arguments:",
    "subcommands:",
    "available subcommands",
    "describe available commands",
    "manage ",
)

ERROR_MARKERS = (
    "no such file or directory",
    "failed to execute",
    "error:",
    "unknown subcommand",
    "unexpected arguments",
    "could not open tty",
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
    """Yield help invocations to try, from safest to riskiest.

    Prefer ``--help`` / ``-h`` first: many CLIs treat a trailing ``help`` token
    as a positional argument and run the real command (e.g. ``agy install help``
    actually runs the installer). Colon-form ``ns:help`` is last because some
    tools (e.g. agy) treat unknown tokens as interactive session input.
    """
    yield [program] + args + ["--help"]
    yield [program] + args + ["-h"]
    yield [program] + args + ["help"]
    if len(args) == 1:
        # Some CLIs expose namespace help via `<namespace>:help` instead of flags.
        yield [program, f"{args[0]}:help"]


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


def normalize_subcommands(subcommands):
    """Drop empties, help/version noise, and duplicates while preserving order."""
    seen = set()
    cleaned = []
    for raw in subcommands or []:
        if not isinstance(raw, str):
            continue
        name = raw.strip()
        if not name or name in SKIP_SUBCOMMANDS:
            continue
        # Reject multi-word / path-like hallucinations that aren't real argv tokens.
        if any(ch.isspace() for ch in name) or "/" in name:
            logging.warning(f"Skipping non-token subcommand from LLM: {name!r}")
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
    return cleaned


def get_subcommands(program, args):
    help_output, command = get_help_output(program, args)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command or [program] + args)}")
        return []

    if not looks_like_help(help_output):
        logging.info(
            "Help output does not look like help text; not asking LLM for subcommands"
        )
        return []

    if not should_recurse_into_subcommands(help_output):
        logging.info("Help output already lists colon-qualified subcommands; not recursing")
        return []

    llm_prompt = """\
Analyze this help output and identify subcommands.
Ignore any `help` subcommands.
Only list immediate subcommands of this command level, not nested ones.
Do not invent subcommands that are not explicitly listed in the help text.
Return an empty list if there are no subcommands.
"""
    schema = {
        "type": "object",
        "properties": {
            "has_subcommands": {"type": "boolean"},
            "subcommands": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["has_subcommands", "subcommands"],
    }

    logging.info("Sending help output to LLM for analysis")
    try:
        subcommand_data = call_llm_json(llm_prompt, schema, context=help_output)
        logging.debug(f"LLM output: {subcommand_data}")
        subcommands = normalize_subcommands(subcommand_data.get("subcommands", []))
        logging.info(f"Found subcommands: {subcommands}")
        return subcommands
    except (RuntimeError, json.JSONDecodeError, TypeError, AttributeError) as e:
        logging.error(f"Error processing subcommands: {e}")
        return []


def explore_command(program, args=None, depth=0):
    if args is None:
        args = []

    if depth > MAX_DEPTH:
        logging.info(f"Max depth {MAX_DEPTH} reached at: {program} {' '.join(args)}")
        return ""

    logging.info(f"Exploring command: {program} {' '.join(args)} (depth={depth})")
    help_output, command = get_help_output(program, args)

    if help_output is None:
        logging.warning(f"No help output for command: {' '.join(command or [program] + args)}")
        return ""

    markdown = f"{'#' * (depth + 2)} {' '.join([program] + args)}\n\n"
    markdown += "```\n" + help_output.strip() + "\n```\n\n"

    # Only recurse when we actually got help text — never on fallback command output
    # (e.g. installers/updaters that ignore a trailing "help" token).
    if not looks_like_help(help_output):
        logging.info("Skipping subcommand recursion; output does not look like help")
        return markdown

    if depth >= MAX_DEPTH:
        logging.info(f"Not recursing further (at max depth {MAX_DEPTH})")
        return markdown

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
