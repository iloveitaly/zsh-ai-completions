SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q dokku lnav act localias markdown-extract micro
PROGRAMS_WITH_SUBCOMMANDS := flowctl nixpacks cody uv launchctl aiautocommit alembic security foreman mcpm

# some programs don't have helpful --help output, so we use manpages instead
PROGRAMS_WITH_MANPAGES := entr

DEFAULT_HELP_COMMAND ?= --help

.DEFAULT_GOAL := all_completions

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS) $(PROGRAMS_WITH_MANPAGES))

completions/_%:
	@if command -v $* >/dev/null 2>&1; then \
		if echo "$(PROGRAMS_WITH_SUBCOMMANDS)" | grep -q "\b$*\b"; then \
			# Buffer output to a file to prevent BrokenPipeError if gemini is slow to read stdin
			# This decouples the help generation from the API call
			python explore_program.py $* > tmp/$*.help; \
			cat tmp/$*.help | gemini -m gemini-3-pro-preview -p $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
			rm tmp/$*.help; \
		elif echo "$(PROGRAMS_WITH_MANPAGES)" | grep -q "\b$*\b"; then \
			man $* | gemini -m gemini-3-pro-preview -p $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
		else \
			$* $(DEFAULT_HELP_COMMAND) 2>&1 | gemini -m gemini-3-pro-preview -p $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
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