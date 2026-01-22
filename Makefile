SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q dokku lnav act localias markdown-extract micro difft
PROGRAMS_WITH_SUBCOMMANDS := flowctl nixpacks cody uv launchctl aiautocommit alembic security foreman mcpm gemini railpack

# some programs don't have helpful --help output, so we use manpages instead
PROGRAMS_WITH_MANPAGES := entr

DEFAULT_HELP_COMMAND ?= --help

.DEFAULT_GOAL := all_completions

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS) $(PROGRAMS_WITH_MANPAGES))

completions/_%: completion_prompt.md generate_completion.py
	# Buffer output to a file to prevent BrokenPipeError if gemini is slow to read stdin
	# This decouples the help generation from the API call
	@if command -v $* >/dev/null 2>&1; then \
		mkdir -p tmp; \
		if echo "$(PROGRAMS_WITH_SUBCOMMANDS)" | grep -q "\b$*\b"; then \
			python explore_program.py $* > tmp/$*.help; \
			python generate_completion.py $* tmp/$*.help > completions/_$*; \
			rm tmp/$*.help; \
		elif echo "$(PROGRAMS_WITH_MANPAGES)" | grep -q "\b$*\b"; then \
			man $* | python generate_completion.py $* > completions/_$*; \
		else \
			$* $(DEFAULT_HELP_COMMAND) 2>&1 | python generate_completion.py $* > completions/_$*; \
		fi; \
		if [ ! -s completions/_$* ]; then \
			rm -f completions/_$*; \
			echo >&2 "Warning: Generated completion for $* was empty. Removing file."; \
		fi; \
	else \
		echo >&2 "Warning: $* is not installed or not in PATH. Skipping."; \
	fi

clean:
	rm -f $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS) $(PROGRAMS_WITH_MANPAGES))
	rm -rf tmp/

update-local:
	zinit update iloveitaly/zsh-ai-completions

test:
	@echo "Testing completions..."
	@failed=0; \
	for file in completions/_*; do \
		if [ -f "$$file" ]; then \
			./test_completion.zsh "$$file" || failed=1; \
		fi; \
	done; \
	if [ $$failed -ne 0 ]; then exit 1; fi
