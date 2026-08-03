#!/usr/bin/env zsh

# Usage: ./test_completion.zsh path/to/_completion_file
# Fails on any syntax / load error in the completion file.

if [[ -z "$1" ]]; then
  echo "Usage: $0 <completion_file>"
  exit 1
fi

COMP_FILE="$1"
COMP_NAME="${COMP_FILE##*/}" # Extract filename (e.g., _micro)

if [[ ! -f "$COMP_FILE" ]]; then
  echo "❌ $COMP_NAME: File not found: $COMP_FILE"
  exit 1
fi

# Create a temporary directory for fpath to isolate this test
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Copy the completion file to the temp dir (autoload looks up by name on fpath)
cp "$COMP_FILE" "$TMP_DIR/$COMP_NAME"

fail() {
  echo "❌ $COMP_NAME: $1"
  [[ -n "$2" ]] && print -r -- "$2"
  exit 1
}

# 1. Strict syntax check (entire file). Catches unmatched quotes, parse errors, etc.
SYNTAX_OUTPUT=$(zsh -n "$COMP_FILE" 2>&1)
SYNTAX_STATUS=$?
if (( SYNTAX_STATUS != 0 )); then
  fail "Syntax Error (zsh -n exited $SYNTAX_STATUS)" "$SYNTAX_OUTPUT"
fi

# 2. Force-load the function definition (parse + define; does not execute the body).
#    Surfaces autoload/definition failures that pure -n might not report the same way.
#    Prepend TMP_DIR so we never pick up a same-named completion from the user fpath
#    (e.g. a broken install of this plugin via zinit).
LOAD_OUTPUT=$(
  zsh -c "
    fpath=($TMP_DIR)
    autoload -Uz compinit
    compinit -u -C -d $TMP_DIR/zcompdump
    autoload -Uz $COMP_NAME
    autoload +X $COMP_NAME
  " 2>&1
)
LOAD_STATUS=$?
if (( LOAD_STATUS != 0 )); then
  fail "Load Error (autoload +X exited $LOAD_STATUS)" "$LOAD_OUTPUT"
fi

# 3. Belt-and-suspenders: flag known syntax-ish diagnostics even if exit status was 0.
#    (Should not happen after the checks above, but keep failures loud.)
COMBINED="$SYNTAX_OUTPUT"$'\n'"$LOAD_OUTPUT"
if print -r -- "$COMBINED" | grep -Eiq \
  'parse error|unmatched |parse error near|command not found: |syntax error'; then
  # "command not found" during load is a hard failure (missing function/helper).
  # Soft-pass only applies if we ever execute completion bodies (we don't here).
  fail "Syntax/load diagnostic in output" "$COMBINED"
fi

echo "✅ $COMP_NAME: Syntax OK"
exit 0
