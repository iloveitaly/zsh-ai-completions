SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q dokku
PROGRAMS_WITH_SUBCOMMANDS := flowctl nixpacks cody
DEFAULT_HELP_COMMAND ?= --help

.DEFAULT_GOAL := all_completions

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS))

completions/_%:
	@if command -v $* >/dev/null 2>&1; then \
		if echo "$(PROGRAMS_WITH_SUBCOMMANDS)" | grep -q "\b$*\b"; then \
			python explore_program.py $* | cody chat --model google::v1::gemini-1.5-pro --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
		else \
			$* $(DEFAULT_HELP_COMMAND) | cody chat --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
		fi; \
		if [ ! -s completions/_$* ]; then \
			rm -f completions/_$*; \
			echo >&2 "Warning: Generated completion for $* was empty. Removing file."; \
		fi; \
	else \
		echo >&2 "Warning: $* is not installed or not in PATH. Skipping."; \
	fi

clean:
	rm -f $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS))