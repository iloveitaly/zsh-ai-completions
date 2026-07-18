**Revision arguments:** Any subcommand/option that takes a revision (or range)—including `upgrade`, `downgrade`, `stamp`, `show`, `edit`, `merge`, `history --rev-range`, and `revision --head` / `--depends-on`—must complete dynamically. Do not hardcode revision ids.

When `alembic` is on PATH, list available revisions with:

`alembic history 2>/dev/null`

Parse revision identifiers from that output into a shared helper (e.g. `_alembic_revisions`) and use it for every revision argument. Also offer relative tokens: `head`, `heads`, `base`, `current`.
