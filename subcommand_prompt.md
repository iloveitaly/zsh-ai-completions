Generate a Zsh completion script for the `<command>` command based on the following `--help` output. **Return only the shell script contents (no explanations or markdown blocks).**

**Requirements:**

- The script must be a Zsh completion script, not Bash.
- Start with `#compdef <command>` to associate it with the `<command>` command.
- Define the completion function as `_<command>`.
- Use `_arguments` with `->state` to handle options and subcommands.
- List subcommands as the first argument with `'1:cmd:(subcmd1 subcmd2 ...)'`, where `subcmd1`, `subcmd2`, etc., are extracted from the `--help` output.
- Capture additional arguments with `'*::args:->args'`.
- Use a `case $state` block to handle subcommands dynamically.
- Within each subcommand case, define specific options using `_arguments`.
- For options that take file paths, use `:file:_files` (e.g., for configuration files).
- For options with specific choices, use `(value1 value2)` or `_values`.
- End with `_<command> "$@"` to invoke the completion function.

**Important:**

- Replace `<command>` with the actual command name (e.g., `git`, `docker`).
- Provide the `--help` output for the command when using this prompt.
