# Project context contract

## Canonical layout

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
└── decisions/
    ├── index.md
    └── NNNN-<decision>.md
```

`CLAUDE.md` and README remain optional root integration points.

## Responsibility boundaries

- Session: current branch, active state, blockers, next actions, validation commands. Replace stale state; never accumulate chronology. Maximum 60 lines.
- Memory index: routing table from work type to topic file. No duplicated topic prose.
- Topic memory: only current, reusable facts, invariants, boundaries, and operational knowledge.
- History index: current monthly log link and latest compact handoff summary.
- Monthly history: immutable dated work facts, validation, and remaining work; newest first.
- ADR: long-lived decision, context, chosen option, consequences, and meaningful alternatives.

## Startup contract

1. Always read `docs/project-context/session.md`.
2. Read `memory/index.md`, then only topic files relevant to the request.
3. Read `history/index.md`. Open the current monthly entry only when detail is needed.
4. Search older history with `rg` before opening a monthly archive.
5. Run `git status` and preserve unrelated changes.
6. Read README for execution and verification.

## Handoff contract

1. Run proportional validation.
2. Refresh session and confirm its line limit.
3. Update only the relevant memory topic; add an ADR when rationale must survive.
4. Add a dated entry to the current monthly history file.
5. Refresh the latest summary and current-log link in history index.
6. Preserve repository-specific authorship and publishing rules.

## Migration rules

- Copy first; delete legacy sources last.
- Preserve historical wording and authorship.
- Split memory semantically, not by arbitrary file size.
- Prefer 4–8 stable topic files over many tiny documents.
- Keep links relative and verify every routed target exists.
- Do not create root pointer stubs unless an external tool demonstrably requires the old paths.
