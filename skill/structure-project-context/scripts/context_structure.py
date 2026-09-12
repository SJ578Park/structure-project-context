#!/usr/bin/env python3
"""Initialize, draft-migrate, and validate routed project context."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

from history_archive import history_blocks, split_history


SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "project-context"
AGENTS_TEMPLATE = SKILL_DIR / "assets" / "AGENTS.md"
CONTEXT_REL = Path("docs/project-context")
LEGACY = ("session.md", "memory.md", "history.md")


def current_values(project: Path) -> dict[str, str]:
    today = dt.date.today()
    branch = "unknown"
    result = subprocess.run(
        ["git", "branch", "--show-current"], cwd=project, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        branch = result.stdout.strip()
    return {
        "{{DATE}}": today.isoformat(),
        "{{YEAR}}": f"{today.year:04d}",
        "{{YEAR_MONTH}}": f"{today.year:04d}-{today.month:02d}",
        "{{BRANCH}}": branch,
    }


def render(text: str, values: dict[str, str]) -> str:
    for token, value in values.items():
        text = text.replace(token, value)
    return text


def write_missing(source: Path, target: Path, values: dict[str, str]) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(source.read_text(encoding="utf-8"), values), encoding="utf-8")


def scaffold(project: Path) -> None:
    values = current_values(project)
    context = project / CONTEXT_REL
    for source in sorted(TEMPLATE_DIR.rglob("*")):
        if source.is_file():
            write_missing(source, context / source.relative_to(TEMPLATE_DIR), values)
    monthly = context / "history" / values["{{YEAR}}"] / f'{values["{{YEAR_MONTH}}"]}.md'
    if not monthly.exists():
        monthly.parent.mkdir(parents=True, exist_ok=True)
        monthly.write_text(
            f'# Work History — {values["{{YEAR_MONTH}}"]}\n\n'
            'Add new entries at the top and preserve prior authorship.\n',
            encoding="utf-8",
        )
    if not (project / "AGENTS.md").exists():
        shutil.copyfile(AGENTS_TEMPLATE, project / "AGENTS.md")


def history_entries(text: str) -> list[tuple[str, str]]:
    return [(date[:7], block.decode("utf-8").strip())
            for date, block in history_blocks(text.encode("utf-8")) if date]


def named_file(directory: Path, name: str) -> Path | None:
    matches = [p for p in directory.iterdir() if p.is_file() and p.name.lower() == name.lower()] if directory.is_dir() else []
    if len(matches) > 1:
        raise RuntimeError(f"ambiguous case variants for {directory / name}")
    return matches[0] if matches else None


def legacy_sources(project: Path) -> dict[str, Path]:
    found = {}
    for name in LEGACY:
        matches = [p for directory in (project, project / "docs") if (p := named_file(directory, name))]
        if len(matches) > 1:
            raise RuntimeError(f"ambiguous legacy sources for {name}; choose the authoritative source explicitly")
        if matches:
            found[name] = matches[0]
    return found


def migrate(project: Path) -> None:
    context = project / CONTEXT_REL
    if context.exists():
        raise RuntimeError(f"destination already exists: {context}")
    legacy = legacy_sources(project)
    if not legacy:
        raise RuntimeError("no root or docs session/memory/history files found; use init")
    # Parse before writing anything; unknown history formats need human routing.
    if "history.md" in legacy and not any(date for date, _ in history_blocks(legacy["history.md"].read_bytes())):
        raise RuntimeError("history has no dated H2 entries; migrate it explicitly without dropping content")
    if "history.md" in legacy:
        split_history(legacy["history.md"], context / "history")
    scaffold(project)
    if "session.md" in legacy:
        shutil.copyfile(legacy["session.md"], context / "session.md")
    if "memory.md" in legacy:
        shutil.copyfile(legacy["memory.md"], context / "memory/legacy.md")
        index = context / "memory/index.md"
        index.write_text(index.read_text() + "\n- Pending semantic split: [legacy.md](legacy.md)\n")
    print(f"Migration draft created at {context}; every source remains in place.")
    print("Review memory, update instructions/links, verify .migration-proof.json, then remove superseded sources.")


def markdown_targets(index: Path) -> list[Path]:
    targets = []
    for raw in re.findall(r"\[[^\]]+\]\(([^)]+)\)", index.read_text(encoding="utf-8")):
        if "://" in raw or raw.startswith("#"):
            continue
        targets.append((index.parent / raw.split("#", 1)[0]).resolve())
    return targets


# Defaults are review budgets, not universal claims about model token costs.
HISTORY_LINES, HISTORY_BYTES = 300, 32 * 1024
INDEX_LINES, INDEX_BYTES, LATEST_ENTRIES = 60, 8 * 1024, 3
MEMORY_LINES, MEMORY_BYTES = 200, 24 * 1024


def validate(project: Path, history_only: bool = False) -> int:
    context = project / CONTEXT_REL
    canonical = context.is_dir()
    base = context if canonical else project / "docs"
    if not canonical and not any((base / n).exists() for n in ("history", "memory")) and not any(named_file(base, n) for n in LEGACY):
        base = project
    errors, warnings = [], []
    session = named_file(base, "session.md")
    history = base / "history/index.md"
    flat_history = named_file(base, "history.md")
    memory = base / "memory/index.md"
    if not memory.is_file():
        memory = named_file(base, "memory.md") or (base / "project-standards.md")
    if not history.is_file():
        history = flat_history
    elif flat_history:
        errors.append(f"superseded history source remains: {flat_history.relative_to(project)}")

    def budget(path: Path, lines: int, size: int, label: str, findings: list[str]) -> None:
        count = len(path.read_text(encoding="utf-8").splitlines())
        length = path.stat().st_size
        if count > lines or length > size:
            findings.append(f"{label}: {path.relative_to(project)} has {count} lines / {length} bytes; limit {lines} / {size}")

    indexes = []
    if history is None:
        errors.append("missing history file or history/index.md")
    elif history.name == "index.md":
        indexes.append(history)
        budget(history, INDEX_LINES, INDEX_BYTES, "history index must stay compact", errors)
        count = len(re.findall(r"^#{2,6} \d{4}-\d{2}-\d{2}(?=$|\D)", history.read_text(), re.M))
        if count > LATEST_ENTRIES:
            errors.append(f"history index has {count} dated summaries; keep at most {LATEST_ENTRIES}")
        targets = markdown_targets(history)
        if not any(p.is_file() and re.fullmatch(r"\d{4}-\d{2}(?:-\d{2})?\.md", p.name) for p in targets):
            errors.append("history index must link to a current dated log")
    else:
        budget(history, HISTORY_LINES, HISTORY_BYTES, "split single history by month", errors)

    if not history_only:
        if session is None:
            errors.append("missing session.md")
        else:
            budget(session, 60, 12 * 1024, "session must stay bounded", errors)
        if not memory.is_file():
            errors.append("missing memory file or memory/index.md")
        elif memory.name == "index.md":
            indexes.append(memory)
            budget(memory, INDEX_LINES, INDEX_BYTES, "memory index must stay compact", errors)
            for topic in memory.parent.glob("*.md"):
                if topic != memory:
                    budget(topic, MEMORY_LINES, MEMORY_BYTES, "review/split memory topic semantically", warnings)
        else:
            budget(memory, MEMORY_LINES, MEMORY_BYTES, "review/split memory semantically", warnings)
        decisions = base / "decisions/index.md"
        if decisions.is_file():
            indexes.append(decisions)
        agents = project / "AGENTS.md"
        if not agents.is_file():
            errors.append("missing: AGENTS.md")
        else:
            instructions = agents.read_text()
            for path in (session, memory, history):
                if path and path.is_file() and str(path.relative_to(project)) not in instructions:
                    errors.append(f"AGENTS.md does not route to {path.relative_to(project)}")
        if canonical:
            for source in legacy_sources(project).values():
                errors.append(f"superseded context source remains: {source.relative_to(project)}")
            for path in (base / "memory/legacy.md", base / "history/legacy.md"):
                if path.exists():
                    errors.append(f"legacy context needs semantic routing: {path.relative_to(project)}")
    for index in indexes:
        for target in markdown_targets(index):
            if not target.exists():
                errors.append(f"broken link from {index.relative_to(project)}: {target}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        print("Project context validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Project context validation passed" + (" (history only)" if history_only else ""))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "migrate", "validate"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", default=".")
        if command == "validate":
            sub.add_argument("--history-only", action="store_true")
        if command == "init":
            sub.add_argument("--layout", choices=("compact", "routed"), default="routed")
    args = parser.parse_args()
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        raise RuntimeError(f"project directory not found: {project}")
    if args.command == "init":
        if legacy_sources(project) or (project / CONTEXT_REL).exists() or any(
            (directory / part / "index.md").exists()
            for directory in (project, project / "docs") for part in ("history", "memory")
        ):
            raise RuntimeError("context already exists; use validate or an explicit migration instead of creating duplicate context")
        if args.layout == "compact":
            if (project / CONTEXT_REL).exists():
                raise RuntimeError("routed context exists; do not create a second source of truth")
            docs = project / "docs"
            docs.mkdir(exist_ok=True)
            values = current_values(project)
            for name, body in {
                "session.md": "# Session\n\nCurrent state, blockers and next actions. Keep at most 60 lines.\n",
                "memory.md": "# Project Memory\n\nCurrent reusable facts only; no chronological work log.\n",
                "history.md": f'# Work History\n\n## {values["{{DATE}}"]} — Context initialized\n\n- Compact project context created.\n',
            }.items():
                if named_file(docs, name) is None:
                    (docs / name).write_text(body)
            if not (project / "AGENTS.md").exists():
                (project / "AGENTS.md").write_text(
                    "# Agent Guide\n\nUse docs/session.md when resuming substantive work, docs/memory.md for relevant principles, and docs/history.md when earlier work matters.\n"
                    "Update context when current state, durable knowledge or meaningful work changes. Keep session at most 60 lines; trivial edits and read-only questions need no log by default.\n"
                    "Split history by month above 300 lines or 32 KiB. Review memory for topic splitting above 200 lines or 24 KiB.\n"
                    "Validate after structure, routing or substantial context changes with the structure-project-context skill when available; for isolated wording fixes, check affected text and links.\n")
        else:
            scaffold(project)
        print(f"Project context initialized ({args.layout})")
        return 0
    if args.command == "migrate":
        migrate(project)
        return 0
    return validate(project, history_only=args.history_only)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
