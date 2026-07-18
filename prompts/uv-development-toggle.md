**MODULE argument:** If `uv.lock` exists (and `uv` is available), complete package names dynamically with:

`uv tree --all-groups --depth 1`

Parse **direct** dependency names from that output (all `pyproject.toml` groups; not the full transitive tree). Tree lines use both `├──` and `└──` prefixes followed by `name version` — extract the package name from every branch line. Do not hardcode package names.

Bare TAB on the first argument must offer these packages (flags still complete after `-`/`--` only).
