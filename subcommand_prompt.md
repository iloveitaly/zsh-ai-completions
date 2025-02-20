Generate zsh completion for all arguments listed in this '--help' output. MOST IMPORTANT: **Only return the shell script contents (no other output) without a markdown block.**

IMPORTANT: follow these instructions:

- Begin the script with `#compdef <command>` to associate the completion function with the command.
- Define the completion function, typically named `_<command>`.
- Use `_arguments` to parse command-line arguments.
- For the first argument, specify the list of subcommands using `'1:cmd:(subcmd1 subcmd2 subcmd3)'`.
- Capture additional arguments with `'*::args:->args'`.
- Use a `case` statement to handle different subcommands based on `$state` or `$words[1]`.
- Within each subcommand case, define specific options using `_arguments`.
- For options that accept files, use `:file:_files` to enable file path completion.
- Provide possible values for options with specific choices using `(value1 value2 value3)`.
- Always use `->state` syntax in `_arguments`
- Ensure that the state labels used with ->state in _arguments match those in the case `$state` in statement.
- Verify that the `$state` variable is being set correctly after each `_arguments` call.
- Avoid using && return if further processing is needed, as it may exit the function prematurely.
- Check that positional arguments are correctly indexed and specified in `_arguments`.
- Use `_values` for enum-like choices
- Include the completion function invocation at the end of the script by adding: "_commandname "$@" where 'commandname' matches the name of your completion function.