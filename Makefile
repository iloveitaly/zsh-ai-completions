SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

completions/_%:
	@if command -v $* >/dev/null 2>&1; then \
		$* --help | cody chat --stdin $(NO_SUBCOMMAND_PROMPT) > completions/_$*; \
	else \
		echo >&2 "Warning: $* is not installed or not in PATH. Skipping."; \
	fi

clean-without-subcommands:
	rm -f $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

PROGRAMS_WITH_SUBCOMMANDS := flowctl