# AI Generated ZSH Completions

I love zsh completions. Everyone hates generating them.

AI is perfect for doing this for us.

## Installation

```shell
zinit light iloveitaly/zsh-ai-completions
```

## What Completions Are Included?

Check out the [completions](completions) directory.

## How Well Does This Work?

My main goal was replacing [zsh-completion-generator](https://github.com/RobSis/zsh-completion-generator) which is abandoned and does not work with usage information that is not generated by a specific python CLI library.

I've checked the AI generated completions against this tool and it works quite well! I haven't yet found any errors in the generated completions.

## Development

### Additional Completions

Just modify the `Makefile` run `make` and test the output. Then, please submit a PR!

To focus on building a single completion run `make completions/_aiautocommit`

Note that [Cody](http://cody.dev) is used for generating the completions since they have a nice CLI tool.

### Local Testing

Want to test out a completion locally?

```shell
fpath+=./completions
autoload -Uz compinit && compinit
```

## TODO

- [ ] the company behind sqlc has a way to run code securely in the cloud, should try this for subcommands