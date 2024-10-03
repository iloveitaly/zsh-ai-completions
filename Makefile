SHELL := zsh

PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

completions/_%:
	@if command -v $* >/dev/null 2>&1; then \
		$* --help | cody chat --stdin "generate zsh completion. Only output completion script contents without a markdown block. Only include code in your output, no messages or preamble." > completions/_$*; \
	else \
		echo >&2 "Warning: $* is not installed or not in PATH. Skipping."; \
	fi

clean-without-subcommands:
	rm -f $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

PROGRAMS_WITH_SUBCOMMANDS := flowctl