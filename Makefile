SHELL := zsh

NO_SUBCOMMAND_PROMPT := "Generate zsh completion for all arguments listed in this '--help' output. Only return the shell script contents (no other output) without a markdown block."
PROGRAMS_WITHOUT_SUBCOMMANDS := sops ncdu tre vitest eslint fastmod ipython fzf zq pytest q dokku lnav act localias markdown-extract micro difft
PROGRAMS_WITH_SUBCOMMANDS := flowctl nixpacks cody uv launchctl aiautocommit alembic security foreman mcpm gemini railpack

# some programs don't have helpful --help output, so we use manpages instead
PROGRAMS_WITH_MANPAGES := entr

DEFAULT_HELP_COMMAND ?= --help
PYTHON ?= python3
AI_CLI ?= gemini
AI_MODEL ?=
AI_MODEL_FLAG ?= -m

AI_ARGS := --cli $(AI_CLI)
ifneq ($(AI_MODEL),)
AI_ARGS += --model $(AI_MODEL) --model-flag $(AI_MODEL_FLAG)
endif

.DEFAULT_GOAL := all_completions

all_completions: $(addprefix completions/_,$(PROGRAMS_WITHOUT_SUBCOMMANDS) $(PROGRAMS_WITH_SUBCOMMANDS) $(PROGRAMS_WITH_MANPAGES))

completions/_%: completion_prompt.md generate_completion.py
	@# Buffer output to a file to prevent BrokenPipeError if gemini is slow to read stdin
	@# This decouples the help generation from the API call
	@if command -v $* >/dev/null 2>&1; then \
		binary_path=$$(command -v $*); \
		echo "Generating completion for $* ($$binary_path) using $(AI_CLI)$${AI_MODEL:+ model $(AI_MODEL)}..."; \
		mkdir -p tmp; \
		if echo "$(PROGRAMS_WITH_SUBCOMMANDS)" | grep -q "\b$*\b"; then \
			echo "  Exploring subcommands..."; \
			$(PYTHON) explore_program.py $(AI_ARGS) $* > tmp/$*.help; \
			echo "  Generating completion from explored help..."; \
			$(PYTHON) generate_completion.py $(AI_ARGS) $* tmp/$*.help > completions/_$*; \
			rm tmp/$*.help; \
		elif echo "$(PROGRAMS_WITH_MANPAGES)" | grep -q "\b$*\b"; then \
			echo "  Generating completion from manpage..."; \
			man $* | $(PYTHON) generate_completion.py $(AI_ARGS) $* > completions/_$*; \
		else \
			echo "  Generating completion from --help output..."; \
			$* $(DEFAULT_HELP_COMMAND) 2>&1 | $(PYTHON) generate_completion.py $(AI_ARGS) $* > completions/_$*; \
		fi; \
		if [ ! -s completions/_$* ]; then \
			rm -f completions/_$*; \
			echo >&2 "Warning: Generated completion for $* was empty. Removing file."; \
		else \
			if ! ./test_completion.zsh completions/_$*; then \
				rm -f completions/_$*; \
				echo >&2 "Error: Generated completion for $* failed validation. Removing file."; \
				exit 1; \
			fi; \
			tool_version=$$($* --version 2>/dev/null | head -1 || echo "unknown"); \
			gen_date=$$(date +%Y-%m-%d); \
			{ echo "#compdef $*"; \
			  echo "# Generated from: $$tool_version ($$binary_path)"; \
			  echo "# Generated on: $$gen_date"; \
			  echo "# AI: $(AI_CLI)$${AI_MODEL:+ ($(AI_MODEL))}"; \
			  tail -n +2 completions/_$*; } > completions/_$*.tmp && \
			mv completions/_$*.tmp completions/_$*; \
			echo "  Written to completions/_$*"; \
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
