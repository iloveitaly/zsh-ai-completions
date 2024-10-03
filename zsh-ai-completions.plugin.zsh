#!/usr/bin/env zsh

# date +%H:%M:%S.%N   # profiling info

# Fetch $0 according to plugin standard proposed at:
# http://zdharma.org/Zsh-100-Commits-Club/Zsh-Plugin-Standard.html
0="${${ZERO:-${0:#$ZSH_ARGZERO}}:-${(%):-%N}}"

CURRENT_DIR=${0:A:h}
COMPLETIONS_PATH="$CURRENT_DIR/completions"

fpath+=$ZSH_COMPLETION_GENERATOR_DIR