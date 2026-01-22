Generate a Zsh completion script for the command based on the provided help output.

**IMPORTANT: Return ONLY the raw Zsh code. Do NOT wrap it in markdown code blocks (e.g. ```zsh ... ```). Do NOT include any explanations.**

**Requirements:**

- Start with `#compdef <command>`
- Use `_arguments` to define options.
- **Do NOT use the `-s` flag** with `_arguments` (e.g. `_arguments -s`) unless strictly necessary and verified. Defaults to omitting it.
- **Always use the `-S` flag** with `_arguments` (e.g. `_arguments -S ...`) to properly handle the `--` end-of-options delimiter.
- **Special Flag Handling:**
    - If a flag starts with `+` (e.g., `+LINE`, `+/REGEX`), do NOT define it as a standard option (like `'+[...]'`) in `_arguments`. These are often position-dependent or attached arguments that `_arguments` handles poorly as named options. Treat them as `*:...` matches or ignore them.
    - **Repeatable Flags:** If a flag is described as "repeatable" or "multiple":
        - Prepend `*` to the definition (e.g., `'*--verbose'`).
        - **Do NOT** include the flag itself in the exclusion list (the parentheses at the start). e.g., Use `'*-v'` instead of `'*(-v)-v'`.
- **Subcommands (if present in help output):**
    - If the help output clearly defines subcommands (e.g., `git commit`, `docker run`), structure the completion using `_arguments` with `1: :_subcommands` and `*:: :->args`, and define helper functions for each subcommand.
- **Syntax:**
    - Ensure all quotes are properly escaped.
    - Use `_files` for file arguments.

