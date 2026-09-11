# AGENTS.md

## Start work

1. Read `docs/project-context/session.md` first.
2. Use `docs/project-context/memory/index.md` to select only relevant memory topics.
3. Read the latest summary in `docs/project-context/history/index.md`; open monthly logs only when needed and search old logs with `rg` first.
4. Run `git status` and preserve unrelated changes.
5. Follow README for execution and verification.

## Finish work

1. Run proportional validation.
2. Refresh session and keep it at or below 60 lines.
3. Update only relevant memory topics; add an ADR for durable decisions.
4. Add a dated entry to the current monthly history log.
5. Replace the latest summary in history index; keep at most 3 dated summaries, 60 lines and 8 KiB.

Current state wins from session, current principles from memory, rationale from ADRs, and past facts from history.

At handoff, validate project context with the installed structure-project-context skill when available; otherwise check the bounds and links manually. Preserve unique older summaries in history before replacing them.
