# Structure Project Context

A Codex skill for keeping repository handoff context fast as projects grow.

It supports compact files for small projects and grows memory and history independently. Larger projects use:

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

The migration command detects root or `docs/` sources (including uppercase filenames) and leaves those sources in place intentionally. Let Codex split memory semantically, merge project-specific instructions, validate preservation, and only then remove the legacy files.


## Keep context bounded

Small projects can start with `init --layout compact`; the existing `init` default remains `routed`. Established compact and hybrid `docs/` layouts can be validated without renaming their files.

- Split single history above 300 lines or 32 KiB into `history/YYYY/YYYY-MM.md`.
- Keep history index at most 3 latest dated summaries, 60 lines and 8 KiB; replace the summary block at handoff.
- Review memory above 200 lines or 24 KiB for semantic topic splitting. This is reported as a warning, separately from history failures.
- Run context validation at handoff; global installation does not automatically update each project's AGENTS/CLAUDE rules.

History-only migration retains the original and includes a source-reconstruction proof:

```bash
python3 "$SKILL_DIR/scripts/history_archive.py" split --source /path/to/project/docs/HISTORY.md --destination /path/to/project/docs/history
python3 "$SKILL_DIR/scripts/history_archive.py" verify /path/to/project/docs/history/.migration-proof.json
python3 "$SKILL_DIR/scripts/context_structure.py" validate --project /path/to/project --history-only
```

Review the new index, update active links and instructions, verify the proof, and only then remove the superseded source. Existing index-only summaries can be preserved in a dated sibling archive before shortening the active index.

## Development checks

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
