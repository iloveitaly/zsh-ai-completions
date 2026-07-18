set shell := ["zsh", "-cu"]
set script-interpreter := ["zsh", "-eu"]

programs_without_subcommands := "sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q lnav act localias markdown-extract micro difft"
programs_with_subcommands := "flowctl nixpacks uv launchctl aiautocommit alembic security foreman mcpm gemini railpack"
# some programs don't have helpful --help output, so we use manpages instead
programs_with_manpages := "entr"

all_programs := programs_without_subcommands + " " + programs_with_subcommands + " " + programs_with_manpages

# Generate all completions
[default]
[script]
all_completions:
    for program in {{all_programs}}; do
        just completion "$program"
    done

# Generate completion for a single program
[script]
completion program:
    program="{{program}}"
    if ! command -v "$program" >/dev/null 2>&1; then
        echo >&2 "Warning: $program is not installed or not in PATH. Skipping."
        exit 0
    fi

    # Buffer help output to a file to prevent BrokenPipeError if the LLM CLI is
    # slow to read stdin — this decouples help generation from the API call.
    mkdir -p tmp
    if echo "{{programs_with_subcommands}}" | grep -q "\b${program}\b"; then
        python explore_program.py "$program" > "tmp/${program}.help"
        python generate_completion.py "$program" "tmp/${program}.help" > "completions/_${program}"
        rm "tmp/${program}.help"
    elif echo "{{programs_with_manpages}}" | grep -q "\b${program}\b"; then
        man "$program" | python generate_completion.py "$program" > "completions/_${program}"
    else
        "$program" --help 2>&1 | python generate_completion.py "$program" > "completions/_${program}"
    fi

    if [ ! -s "completions/_${program}" ]; then
        rm -f "completions/_${program}"
        echo >&2 "Warning: Generated completion for $program was empty. Removing file."
    else
        if ! ./test_completion.zsh "completions/_${program}"; then
            rm -f "completions/_${program}"
            echo >&2 "Error: Generated completion for $program failed validation. Removing file."
            exit 1
        fi
    fi

# Remove generated completions and temp files
clean:
    rm -f {{prepend("completions/_", all_programs)}}
    rm -rf tmp/

# Update the local zinit installation of this plugin
update-local:
    zinit update iloveitaly/zsh-ai-completions

# Validate existing completion files
[script]
test:
    echo "Testing completions..."
    failed=0
    for file in completions/_*; do
        if [ -f "$file" ]; then
            ./test_completion.zsh "$file" || failed=1
        fi
    done
    if [ $failed -ne 0 ]; then exit 1; fi
