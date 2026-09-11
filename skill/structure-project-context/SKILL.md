---
name: structure-project-context
description: Initialize, audit, migrate, and validate project session, memory, and history across coding agents. Use to standardize handoffs, split growing history, route memory by topic, or repair oversized context indexes while preserving existing records.
---

# Structure Project Context

Keep the entry point small and load only context relevant to the task. Read [the context contract](references/project-context-contract.md) before changing a project's conventions.

## Workflow

1. Read project instructions, session, relevant memory, history index/latest entries, and Git status. Preserve unrelated and uncommitted work.
2. Locate the authoritative context. Check root and `docs/`, case variants, `docs/project-context/`, and paths explicitly named by AGENTS/CLAUDE. Do not create a second source of truth.
3. Choose the smallest useful change: compact files for small projects, topic memory when needed, monthly history when large. Memory and history can grow independently; retain working project-specific paths.
4. Make the requested changes. Update AGENTS/CLAUDE, README, and active links together so the next agent follows the new paths.
5. Validate the resulting layout. At handoff, replace stale session state, update relevant memory, append the dated history entry, and replace the latest index summary instead of accumulating summaries.

## Commands

Run scripts relative to this installed skill's actual directory; do not assume all machines use the same installation root.

```bash
python3 scripts/context_structure.py init --project /path/to/project --layout compact
python3 scripts/context_structure.py init --project /path/to/project --layout routed
python3 scripts/context_structure.py validate --project /path/to/project
```

`validate` recognizes canonical routed context and compact/hybrid root or `docs/` layouts, including uppercase filenames and `project-standards.md` as memory. `--history-only` validates a bounded history-only cleanup without claiming unrelated memory/session work is complete. Other established layouts need equivalent manual checks; do not rename working paths solely to satisfy the validator.

For history-only migration:

```bash
python3 scripts/history_archive.py split --source /path/to/project/docs/HISTORY.md --destination /path/to/project/docs/history
python3 scripts/history_archive.py verify /path/to/project/docs/history/.migration-proof.json
```

The splitter retains the source, preserves dated entries and authors, sorts dates newest first, preserves undated sections separately, and writes a source-reconstruction proof. Review the draft and update the index before removing the superseded source. New archive-relative links are recorded reversibly in the proof. Unsupported link/date formats require explicit review, not silent omission.

`context_structure.py migrate` creates a full routed migration draft from root or `docs/` sources. It leaves memory in `memory/legacy.md` for semantic topic routing. Do not use a full migration when only history needs splitting.

## Essential rules

- Session is current state; memory is current reusable knowledge; history is dated work; ADRs preserve decision rationale.
- Use the contract's size budgets at handoff. Keep history index at most 3 latest dated summaries, 60 lines, and 8 KiB. Replace old summaries; do not prepend forever.
- Before compacting an existing oversized index, preserve unique summary content in history. If equivalence with monthly entries is uncertain, keep a clearly marked archive copy, link it, and verify exact preservation.
- Split memory by meaning, never by date or arbitrary slices. Size warnings request semantic review and do not authorize changing unrelated product principles.
- Historical wording and authorship remain intact. Do not treat old "pending" notes as current facts without verification.
- Back up sources outside the active context; verify every original fragment before removing superseded files. Never silently overwrite destinations.
- Preserve project-specific security and publishing rules. Do not commit or push without existing user authorization.
