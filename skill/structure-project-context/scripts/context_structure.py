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
    heading = re.compile(r"^## (\d{4})-(\d{2})-\d{2}\s+[—-].+$", re.MULTILINE)
    matches = list(heading.finditer(text))
    entries: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append((f"{match.group(1)}-{match.group(2)}", text[match.start():end].strip()))
    return entries


def migrate(project: Path) -> None:
    context = project / CONTEXT_REL
    if context.exists():
        raise RuntimeError(f"destination already exists: {context}")
    legacy = {name: project / name for name in LEGACY if (project / name).exists()}
    if not legacy:
        raise RuntimeError("no root session.md, memory.md, or history.md found; use init")
    scaffold(project)
    if "session.md" in legacy:
        (context / "session.md").write_text(legacy["session.md"].read_text(encoding="utf-8"), encoding="utf-8")
    if "memory.md" in legacy:
        legacy_memory = context / "memory" / "legacy.md"
        legacy_memory.write_text(legacy["memory.md"].read_text(encoding="utf-8"), encoding="utf-8")
        index = context / "memory" / "index.md"
        index.write_text(index.read_text(encoding="utf-8") + "\n- Migration source pending semantic split: [`legacy.md`](legacy.md)\n", encoding="utf-8")
    if "history.md" in legacy:
        source_text = legacy["history.md"].read_text(encoding="utf-8")
        entries = history_entries(source_text)
        if entries:
            grouped: dict[str, list[str]] = {}
            for month, entry in entries:
                grouped.setdefault(month, []).append(entry)
            for month, month_entries in grouped.items():
                year = month[:4]
                target = context / "history" / year / f"{month}.md"
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"# Work History — {month}\n\n" + "\n\n".join(month_entries) + "\n", encoding="utf-8")
        else:
            (context / "history" / "legacy.md").write_text(source_text, encoding="utf-8")
    print(f"Migration draft created at {context}")
    print("Next: semantically split memory, merge AGENTS/CLAUDE rules, update indexes, validate, then delete root legacy files.")


def markdown_targets(index: Path) -> list[Path]:
    targets = []
    for raw in re.findall(r"\[[^\]]+\]\(([^)]+)\)", index.read_text(encoding="utf-8")):
        if "://" in raw or raw.startswith("#"):
            continue
        targets.append((index.parent / raw.split("#", 1)[0]).resolve())
    return targets


def validate(project: Path) -> int:
    context = project / CONTEXT_REL
    errors: list[str] = []
    required = [
        context / "session.md", context / "memory/index.md",
        context / "history/index.md", context / "decisions/index.md",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"missing: {path.relative_to(project)}")
    session = context / "session.md"
    if session.is_file():
        lines = len(session.read_text(encoding="utf-8").splitlines())
        if lines > 60:
            errors.append(f"session exceeds 60 lines: {lines}")
    for relative in ("memory/index.md", "history/index.md", "decisions/index.md"):
        index = context / relative
        if index.is_file():
            for target in markdown_targets(index):
                if not target.exists():
                    errors.append(f"broken link from {index.relative_to(project)}: {target}")
    agents = project / "AGENTS.md"
    if not agents.is_file():
        errors.append("missing: AGENTS.md")
    else:
        instructions = agents.read_text(encoding="utf-8")
        for required_text in ("docs/project-context/session.md", "memory/index.md", "history/index.md"):
            if required_text not in instructions:
                errors.append(f"AGENTS.md does not route to {required_text}")
    for name in LEGACY:
        if (project / name).exists():
            errors.append(f"legacy root file remains: {name}")
    for path in (context / "memory/legacy.md", context / "history/legacy.md"):
        if path.exists():
            errors.append(f"legacy context still needs semantic routing: {path.relative_to(project)}")
    if errors:
        print("Project context validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Project context validation passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "migrate", "validate"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--project", default=".")
    args = parser.parse_args()
    project = Path(args.project).expanduser().resolve()
    if not project.is_dir():
        raise RuntimeError(f"project directory not found: {project}")
    if args.command == "init":
        scaffold(project)
        print(f"Project context initialized at {project / CONTEXT_REL}")
        return 0
    if args.command == "migrate":
        migrate(project)
        return 0
    return validate(project)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
