SHELL := zsh

PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

completions/_%:
	@command -v $* >/dev/null 2>&1 || { echo >&2 "Error: $* is not installed or not in PATH. Aborting."; exit 1; }
	$* --help | cody chat --stdin "generate zsh completion. Only output completion script contents (no other output!) without a markdown block." > completions/_$*

clean-without-subcommands:
	rm -f $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS))

PROGRAMS_WITH_SUBCOMMANDS := flowctl