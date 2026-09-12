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

## Reading and handoff by task

Use session when resuming substantive work or when current state could affect the task. Use memory for the relevant domain/principles, and history only when earlier work or evidence is needed. Search old logs before opening matching entries. A local typo or isolated mechanical edit does not need a full document stack or repository map.

Update context when the work changes what the next contributor needs to know: current state/blockers in session, changed durable knowledge in memory, and meaningful work/validation in history. Read-only questions and trivial edits need no ceremonial log entry unless the project or user specifically requires one.

When writing history, add a newest-first dated entry and replace the index's latest summary block within the stated limits. Month rollover follows actual work dates; inactive projects do not need empty monthly logs. Preserve older unique summary text before compacting it.

Run context validation after changes to structure, routing, indexes or substantial context content. For an isolated wording fix, checking the edited text and affected links is sufficient. Re-run after a relevant correction; do not repeat an unchanged passing check. A history-only result must not be presented as a full-context pass.

Project instructions should route agents to documents by relevance and define these update conditions. A global skill installation does not automatically change each project's AGENTS/CLAUDE rules. These rules work across coding models; they do not relax project-specific security, authorship or deployment boundaries.

For commands or content movement, read [migration and preservation](migration.md) only when needed.
