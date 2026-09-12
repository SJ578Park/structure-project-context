# Migration and commands

Resolve scripts from the installed skill directory; do not assume every machine uses the same home path. Commands below are relative to that directory.

## Audit or initialize

```bash
python3 scripts/context_structure.py validate --project /path/to/project
python3 scripts/context_structure.py validate --project /path/to/project --history-only
python3 scripts/context_structure.py init --project /path/to/project --layout compact
python3 scripts/context_structure.py init --project /path/to/project --layout routed
```

Validation is read-only. It recognizes root/`docs/` compact and hybrid layouts, canonical `docs/project-context/`, uppercase filenames, and `project-standards.md` as memory. `--history-only` limits the check; it does not certify unrelated memory/session work. Other established layouts need equivalent checks, not a forced rename. Existing context is never replaced by `init`; choose the layout explicitly for a new project.

## Split history only

```bash
python3 scripts/history_archive.py split --source /path/to/project/docs/HISTORY.md --destination /path/to/project/docs/history
python3 scripts/history_archive.py verify /path/to/project/docs/history/.migration-proof.json
```

The splitter retains the source, sorts dated H2 entries newest first, preserves undated sections separately, and writes a source-reconstruction proof. Review the index and update active callers before retiring the old file. The proof reconstructs source bytes, including reversibly rebased simple inline links. Complex links and other date formats need an equivalent explicit transformation; they must not be silently omitted.

For a full routed migration, use `context_structure.py migrate --project ...`. It discovers root/`docs/` sources and leaves `memory/legacy.md` for semantic topic routing. Read project instructions to resolve ambiguous duplicate sources; do not choose by modification time alone.

## Preserve while moving

- Back up sources outside active context; include uncommitted content. Copy first, verify, retire superseded sources last, checking for concurrent edits.
- Preserve every historical entry, preamble, undated section and author. Old pending notes are historical unless independently verified as current.
- Split memory by meaning. Complete topic routing before retiring a memory source; `memory/legacy.md` is a draft, not the final state.
- Before shortening an index, preserve unique content. If equivalence with monthly logs is uncertain, keep a dated sibling archive with the same relative-link base and mark it as historical summaries.
- Update AGENTS/CLAUDE, README and other active callers only where their routing changes. Rebase moved Markdown links. Old path mentions inside historical prose remain historical.
- Verify the proof after final edits. Use old-path stubs only for an actual compatibility requirement; otherwise keep one authoritative entry point.
