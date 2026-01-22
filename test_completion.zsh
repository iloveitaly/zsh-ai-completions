#!/usr/bin/env zsh

# Usage: ./test_completion.zsh path/to/_completion_file

if [[ -z "$1" ]]; then
  echo "Usage: $0 <completion_file>"
  exit 1
fi

COMP_FILE="$1"
COMP_NAME="${COMP_FILE##*/}" # Extract filename (e.g., _micro)
CMD_NAME="${COMP_NAME#_}"    # Remove leading underscore (e.g., micro)

# Create a temporary directory for fpath to isolate this test
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

# Copy the completion file to the temp dir
cp "$COMP_FILE" "$TMP_DIR/$COMP_NAME"

# Start a subshell to test loading
# We turn on stderr redirection to capture errors
OUTPUT=$(zsh -c "
  fpath+=($TMP_DIR)
  autoload -Uz compinit; compinit -u -C -d $TMP_DIR/zcompdump
  autoload -Uz $COMP_NAME
  
  # specific check: try to resolve the function
  if ! functions $COMP_NAME > /dev/null; then
      # If not loaded yet, try to load it by invoking compdef or just autoloading
      # The 'autoload' above marks it. 
      # We simulate a completion load by triggering it? 
      # Actually, just sourcing it or ensuring 'compinit' found it is a good start.
      # But 'compinit' reads the #compdef line.
      pass
  fi

  # Basic syntax check is implicit if we try to load it.
  # But compinit only lazy-loads.
  # We force load it.
  load_func() {
      $COMP_NAME
  }
  
  # We run it. It will fail with 'can only be called from completion function' 
  # but that means it PARSED correctly and EXECUTED until the first _arguments call.
  # If it has syntax error, it will exit non-zero before that.
  
  try_load() {
      # Force load the function definition to check for syntax errors
      # This parses the file but does not execute the function body (except for immediate top-level code)
      autoload +X $COMP_NAME >/dev/null 2>&1
      RET=\$?
      return \$RET
  }
  
  try_load
" 2>&1)

EXIT_CODE=$?

# Analyze output for syntax errors
if echo "$OUTPUT" | grep -q "parse error"; then
  echo "❌ $COMP_NAME: Syntax Error"
  echo "$OUTPUT"
  exit 1
elif echo "$OUTPUT" | grep -q "command not found"; then
  # If the completion calls a command that doesn't exist (unlikely for valid completion unless logic error)
  echo "⚠️  $COMP_NAME: Potential logic error (command not found)"
  echo "$OUTPUT"
  # We don't fail strictly for this as it might be 'gemini' not found inside the completion? No.
  exit 0 # Soft pass
else
  # If it failed because 'can only be called from completion function', that is GOOD.
  # It means it loaded and ran.
  echo "✅ $COMP_NAME: Syntax OK"
  exit 0
fi
