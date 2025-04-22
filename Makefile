SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q dokku lnav act localias markdown-extract
PROGRAMS_WITH_SUBCOMMANDS := flowctl nixpacks cody uv launchctl aiautocommit alembic security foreman

# some programs don't have helpful --help output, so we use manpages instead
PROGRAMS_WITH_MANPAGES := entr

DEFAULT_HELP_COMMAND ?= --help

.DEFAULT_GOAL := all_completions

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS) $(PROGRAMS_WITH_MANPAGES))

# when authenticated to cody, use `https://sourcegraph.com/.api/modelconfig/supported-models.json` to get a list of all supported models
completions/_%:
	@if command -v $* >/dev/null 2>&1; then \
		if echo "$(PROGRAMS_WITH_SUBCOMMANDS)" | grep -q "\b$*\b"; then \
			python explore_program.py $* | cody chat --model google::v1::gemini-2.0-pro-exp-02-05 --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
		elif echo "$(PROGRAMS_WITH_MANPAGES)" | grep -q "\b$*\b"; then \
			man $* | cody chat --model anthropic::2024-10-22::claude-3-7-sonnet-latest --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
		else \
			$* $(DEFAULT_HELP_COMMAND) 2>&1 | cody chat --model anthropic::2024-10-22::claude-3-7-sonnet-latest --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
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

update-local:
	zinit update iloveitaly/zsh-ai-completions