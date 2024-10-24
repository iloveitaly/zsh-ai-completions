Generate zsh completion for all arguments listed in this '--help' output. MOST IMPORTANT: **Only return the shell script contents (no other output) without a markdown block.**

IMPORTANT Follow these instructions:

- Begin the script with `#compdef <command>` to associate the completion function with the command.
- Define the completion function, typically named `_<command>`.
- Use `_arguments` to parse command-line arguments.
- For the first argument, specify the list of subcommands using `'1:cmd:(subcmd1 subcmd2 subcmd3)'`.
- Capture additional arguments with `'*::args:->args'`.
- Use a `case` statement to handle different subcommands based on `$state` or `$words[1]`.
- Within each subcommand case, define specific options using `_arguments`.
- For options that accept files, use `:file:_files` to enable file path completion.
- Provide possible values for options with specific choices using `(value1 value2 value3)`.
- Test the script to ensure subcommands and options autocomplete correctly and that file completions work where appropriate.
- Always use `->state` syntax in `_arguments`
- Use `_values` for enum-like choices
- Test completions with zsh -f for clean environment verification