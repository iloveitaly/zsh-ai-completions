**Dynamic values:** Complete `--model` from `agy models 2>/dev/null` (one model id per line). Do not invent a `-m` short flag — help only documents `--model`. Complete `--agent` from `agy agent 2>/dev/null` when that command lists agent names.

**Enums from help:** `--effort` is `(low medium high)`. `--mode` is `(accept-edits plan)`. `plugin import` source is `(gemini claude)`.

**Repeatable:** `--add-dir` is repeatable; complete with directories (`_files -/`).

**Aliases:** `agents` is an alias of `agent`; `plugins` is an alias of `plugin`. Share the same completion helpers.

**Plugin subcommands:** Under `plugin`/`plugins`, complete nested commands (`list`, `import`, `install`, `uninstall`, `enable`, `disable`, `validate`, `link`, `help`). Use `_files -/` for `install`/`validate` path args where appropriate.
