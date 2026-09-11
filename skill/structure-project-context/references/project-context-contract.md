# Project context contract

## Responsibilities and layouts

- Session: current branch/state, blockers, next actions, verification. Replace stale state, never accumulate chronology.
- Memory: current reusable facts, invariants, boundaries and operational knowledge. Group by topic, not by date.
- History: dated work, validation, remaining work and original authorship. Preserve historical facts.
- ADR: optional long-lived rationale, alternatives and consequences.

Small projects may use `docs/session.md`, `docs/memory.md`, and `docs/history.md`. Existing root paths, uppercase filenames and `project-standards.md` can remain authoritative when project instructions route to them.

Grow each part independently. A hybrid layout such as `docs/session.md`, `docs/memory.md`, and `docs/history/index.md` plus `history/YYYY/YYYY-MM.md` is valid. Do not force a small memory file into many empty topic files because history has grown.

For projects needing full routing:

```text
AGENTS.md
docs/project-context/
├── session.md
├── memory/
│   ├── index.md
│   └── <topic>.md
├── history/
│   ├── index.md
│   └── YYYY/YYYY-MM.md
└── decisions/                 optional
    ├── index.md
    └── NNNN-<decision>.md
```

## Default handoff budgets

These are operational defaults, not model token estimates. Respect an explicitly documented project-specific convention and report unsupported exceptions rather than silently overriding it.

| File | Budget | Action |
|---|---|---|
| Session | 60 lines and 12 KiB | Replace stale state; move completed detail to history. |
| Single history | 300 lines and 32 KiB | If either is exceeded, split by month. |
| History index | 60 lines, 8 KiB, at most 3 dated summaries | Replace latest summaries; preserve older content in logs/archives. |
| Memory index | 60 lines and 8 KiB | Keep links/routing only; move prose to topics. |
| Memory file/topic | Review above 200 lines or 24 KiB | Semantic review warning; split coherent topics if useful, not mechanically. |

Memory review warnings are separate from validation failures so a history-only task does not silently rewrite unrelated knowledge. Do not claim warnings were resolved without reviewing them. A few stable topics are preferable to many tiny documents; there is no required topic count.

Monthly history is an archive, not startup context. It may exceed the single-history budget. If finding an entry becomes cumbersome (for example over 1,000 lines or 128 KiB), consider day/week files with a month router. Use actual retrieval needs, preserve entries, and keep the top-level index bounded. Old month links can be grouped into year indexes when the top-level router grows.

## Startup and handoff

1. Always read session.
2. Read memory index and relevant topics, or relevant sections of a small memory file.
3. Read history index/latest compact summary. Search archives with `rg` before opening only relevant entries; do not read every monthly log.
4. Read Git status and README for execution/verification. Preserve other work.
5. At handoff, run proportional validation, refresh current session and relevant memory, and append a newest-first dated entry to the current monthly history.
6. Replace the latest summary block, retaining at most 3 short summaries. Refresh the current-log link. Month rollover follows actual work dates; an inactive project does not need empty logs every month.
7. Run the installed `context_structure.py validate --project ...` when available. Otherwise check these budgets, routing and links manually. Installation alone does not change project instructions; keep this handoff rule in AGENTS/CLAUDE.

## Migration and preservation

- Read existing instructions before changing paths. Detect both root and `docs/` sources and case variants. Ambiguous duplicate sources require explicit resolution.
- Copy first, verify, remove superseded sources last. Preserve dirty working-tree content, not merely the committed version.
- Preserve every historical entry, undated section, preamble and author. Never silently drop text that does not match a date parser.
- Split memory semantically; do not retain `memory/legacy.md` as the final routed state.
- Preserve index-only information before compacting it. If uniqueness is uncertain, archive the entire old index alongside the new one with a dated name, retain its relative link base, and mark it as historical summaries rather than an active router.
- For a moved history document, update active callers and rebase relative Markdown links. Historical prose mentioning old paths remains historical, not a live write instruction.
- The split helper's proof reconstructs the original source from exact fragments; re-check after final edits. New entries should not modify historical fragments.
- Do not create pointer stubs at old paths unless an actual external caller requires compatibility. Do not rewrite unrelated instructions or historical facts while repairing routing.
