# AI Generated ZSH Completions

I love zsh completions. Everyone hates generating them.

Let's see if AI can do this for us.

## Installation

```shell
iloveitaly/zsh-ai-completions
```

## Prompt

```
generate zsh completion

write a zsh completion. This content contains subcommand --help output.

write a zsh shell script to execute each subcommand help output and aggregate it so an llm could easily generate a completion from it. Only return the shell script contents (no other output), without a markdown block. Do not use "commands" as a variable name in the script.
```

## TODO

- [ ] the company behind sqlc has a way to run code securely in the cloud, should try this for subcommands