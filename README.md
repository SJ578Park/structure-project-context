# Structure Project Context

A Codex skill for keeping repository handoff context fast as projects grow.

It replaces unbounded root-level `session.md`, `memory.md`, and `history.md` files with:

- one bounded current-session file;
- a memory index that routes agents to relevant topic files only;
- a compact history index backed by monthly logs;
- optional ADRs for decisions whose rationale must survive handoffs;
- startup and handoff rules for `AGENTS.md` and `CLAUDE.md`.

## Install globally on macOS

```bash
git clone https://github.com/SJ578Park/structure-project-context.git
cd structure-project-context
./install.sh
```

`install.sh` copies the skill to `${CODEX_HOME:-$HOME/.codex}/skills/structure-project-context`. If a previous installation exists, it is moved to a timestamped backup first.

Restart Codex after installing, then invoke:

```text
Use $structure-project-context to initialize this repository.
```

or:

```text
Use $structure-project-context to migrate the existing session, memory, and history files.
```

## Resulting project layout

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

The startup contract always reads session first, then uses indexes to load only relevant memory and history. Migration copies legacy content before deletion and requires semantic memory routing before validation passes.

## Direct commands

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/structure-project-context"

python3 "$SKILL_DIR/scripts/context_structure.py" init --project /path/to/repository
python3 "$SKILL_DIR/scripts/context_structure.py" migrate --project /path/to/repository
python3 "$SKILL_DIR/scripts/context_structure.py" validate --project /path/to/repository
```

The migration command leaves legacy root files in place intentionally. Let Codex split memory semantically, merge project-specific instructions, validate preservation, and only then remove the legacy files.

## License

MIT
