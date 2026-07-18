---
name: structure-project-context
description: Initialize, migrate, and validate scalable repository context for coding agents using a bounded session file, routed topic memory, monthly history, and optional ADRs. Use when setting up a new project’s session/memory/history convention, reorganizing growing root context files, reducing agent context-loading cost, or standardizing AGENTS.md and CLAUDE.md startup and handoff rules across repositories.
---

# Structure Project Context

Create a predictable entry point while loading only the context relevant to the current task.

## Workflow

1. Read the repository instruction files and `git status` before changing anything.
2. Detect the mode:
   - New repository without context files: initialize.
   - Repository with root `session.md`, `memory.md`, or `history.md`: migrate.
   - Existing `docs/project-context/`: audit and repair.
3. Read [references/project-context-contract.md](references/project-context-contract.md) before merging rules into existing `AGENTS.md` or `CLAUDE.md`.
4. Use `scripts/context_structure.py` for deterministic scaffolding or validation.
5. Perform the semantic work that a script cannot safely infer:
   - Split long-term memory by stable project topics.
   - Keep one fact in one topic file; do not duplicate it in the index.
   - Preserve every historical entry and author exactly.
   - Create an ADR only for decisions whose rationale and alternatives matter later.
6. Update repository instructions so startup follows session → memory index routing → history index routing → `git status` → README.
7. Update README links, validate, and report any remaining legacy files.

## Commands

Initialize a new repository:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/structure-project-context"
python3 "$SKILL_DIR/scripts/context_structure.py" init --project /path/to/repository
```

Create a safe mechanical migration draft from legacy root files:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/structure-project-context"
python3 "$SKILL_DIR/scripts/context_structure.py" migrate --project /path/to/repository
```

The migration command intentionally leaves root legacy files in place. After semantic splitting, instruction updates, and validation, remove them explicitly:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/structure-project-context"
python3 "$SKILL_DIR/scripts/context_structure.py" validate --project /path/to/repository
```

Run validation again after deleting root legacy files. Never delete the legacy sources before checking that session content and all history entries were preserved.

## Required end state

- Keep `AGENTS.md` at the repository root as the stable discovery point.
- Keep `docs/project-context/session.md` at 60 lines or fewer.
- Make `memory/index.md` a router, not a second memory document.
- Keep current principles in topic memory files; keep chronology only in history.
- Make `history/index.md` contain the current log link and only a compact latest summary.
- Store detailed history in `history/YYYY/YYYY-MM.md`, newest entry first.
- Search old history with `rg` before opening archive files.
- Preserve user changes, author names, secrets policy, and existing repository-specific rules.

## Safety

- Do not commit or push unless the user asks.
- Do not overwrite existing context destinations silently.
- Do not convert historical facts into current memory merely because they appear important.
- Do not leave `memory/legacy.md` as the final migration result; route its durable content into topics.
- If instruction files conflict, preserve the stricter repository rule and explain the merge.
