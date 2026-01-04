Generate a Zsh completion script for the `<command>` command based on the following `--help` output. **Return only the shell script contents (no explanations or markdown blocks).**

**Requirements:**

- The script must be a Zsh completion script, not Bash.
- Start with `#compdef <command>` to associate it with the `<command>` command.
- Define the main completion function as `_<command>`.
- Within `_<command>`, use `_arguments` with `->args` to handle global options and subcommands.
- Define global options in an array called `base_opts`, where each element is a properly formatted option specification for `_arguments`. For example:
  ```zsh
  base_opts=(
      '-h[show help message]'
      '--version[show version information]'
      '-c[specify config file]:config file:_files'
  )
  ```
- List subcommands as the first argument with `'1:cmd:(subcmd1 subcmd2 ...)'`, where `subcmd1`, `subcmd2`, etc., are extracted from the `--help` output.
- Capture additional arguments with `'*::args:->args'`.
- Use a `case $state in args)` block to call subcommand-specific functions based on the first argument.
- For each subcommand, define a function like `_<command>_<subcmd>` that uses `_arguments` to specify its options.
- In each subcommand function, define options using an array similar to `base_opts`.
- For options that take file paths, use `:file:_files`.
- For options with specific choices, use `(value1 value2)` or `_values`.

**Important:**

- Replace `<command>` with the actual command name (e.g., `git`, `docker`).
- Provide the `--help` output for the command when using this prompt.