#!/usr/bin/env python3
"""Lossless dated-history splitting, with verifiable source reconstruction."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def history_blocks(data: bytes) -> list[tuple[str | None, bytes]]:
    """Partition at real H2 headings; never interpret headings in fenced code."""
    starts = []
    fence = None
    offset = 0
    for line in data.splitlines(keepends=True):
        text = line.decode('utf-8').rstrip('\r\n')
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', text)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
        elif text.startswith('## '):
            date = re.match(r'^## (\d{4}-\d{2}-\d{2})(?=$|\D)', text)
            value = date[1] if date else None
            if value:
                dt.date.fromisoformat(value)
            starts.append((offset, value))
        offset += len(line)
    if not starts or starts[0][0] != 0:
        starts.insert(0, (0, None))
    return [(date, data[start:starts[i + 1][0] if i + 1 < len(starts) else len(data)])
            for i, (start, date) in enumerate(starts)]


def relocate_links(data: bytes, source: Path, target: Path) -> tuple[bytes, list[dict]]:
    """Rebase inline local links. Record exact byte edits for lossless verification."""
    import os
    edits = []
    output = bytearray()
    cursor = 0
    # Leave code/path prose unchanged. Reject complex reference links for explicit review.
    if re.search(rb'^ {0,3}\[[^\]]+\]:\s*\S+', data, re.M):
        raise RuntimeError('reference-style links require explicit link migration before splitting')
    for link_target in re.findall(rb'\]\(([^)\n]*)\)', data):
        if any(char in link_target for char in (b' ', b'\t', b'<', b'>', b'(')):
            raise RuntimeError('complex inline links require explicit link migration before splitting')
    for match in re.finditer(rb'\]\(([^\s()]+)\)', data):
        raw = match[1].decode('utf-8')
        if raw.startswith(('#', '/', '<')) or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', raw):
            continue
        path, separator, fragment = raw.partition('#')
        replacement = os.path.relpath(source.parent / path, target.parent) + (separator + fragment)
        start, end = match.span(1)
        output.extend(data[cursor:start])
        encoded = replacement.encode('utf-8')
        edits.append({'offset': len(output), 'length': len(encoded), 'original': raw})
        output.extend(encoded)
        cursor = end
    output.extend(data[cursor:])
    return bytes(output), edits


def restore_links(data: bytes, edits: list[dict]) -> bytes:
    for edit in reversed(edits):
        start = edit['offset']
        data = data[:start] + edit['original'].encode('utf-8') + data[start + edit['length']:]
    return data


def verify_manifest(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text())
    parts = []
    used: dict[Path, list[tuple[int, int]]] = {}
    for piece in manifest['pieces']:
        path = (manifest_path.parent / piece['file']).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()):
            raise RuntimeError('archive manifest target escapes history directory')
        data = path.read_bytes()
        start = piece['offset']
        def available(offset: int) -> bool:
            end = offset + piece['length']
            return not any(offset < b and end > a for a, b in used.get(path, []))
        chunk = data[start:start + piece['length']]
        if digest(chunk) != piece['storedSha256'] or not available(start):
            # New entries may be prepended later; locate the unchanged original fragment.
            anchor = bytes.fromhex(piece['anchorHex'])
            candidate = data.find(anchor)
            while candidate >= 0:
                chunk = data[candidate:candidate + piece['length']]
                if digest(chunk) == piece['storedSha256'] and available(candidate):
                    start = candidate
                    break
                candidate = data.find(anchor, candidate + 1)
            if candidate < 0:
                raise RuntimeError(f'archived fragment changed: {piece["file"]}')
        used.setdefault(path, []).append((start, start + piece['length']))
        original = restore_links(chunk, piece['linkEdits'])
        if digest(original) != piece['originalSha256']:
            raise RuntimeError(f'source fragment mismatch: {piece["file"]}')
        parts.append(original)
    reconstructed = b''.join(parts)
    if digest(reconstructed) != manifest['sourceSha256'] or len(reconstructed) != manifest['sourceBytes']:
        raise RuntimeError('source reconstruction failed')
    return {'sourceBytes': len(reconstructed), 'pieces': len(parts), 'sourceSha256': digest(reconstructed)}


def split_history(source: Path, destination: Path) -> Path:
    """Create a draft; never delete or replace the source or an existing destination."""
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise RuntimeError(f'destination already exists: {destination}')
    data = source.read_bytes()
    blocks = history_blocks(data)
    if not any(date for date, _ in blocks):
        raise RuntimeError('no dated H2 entries; preserve and review the source manually')
    # Prepare everything in memory before creating files.
    files: dict[str, bytearray] = {}
    pieces: list[dict | None] = [None] * len(blocks)
    for i, (date, block) in sorted(enumerate(blocks), key=lambda item: item[1][0] or '', reverse=True):
        rel = f'{date[:4]}/{date[:7]}.md' if date else 'migration-notes.md'
        if rel not in files:
            header = (f'# Work History — {date[:7]}\n\n' if date else
                      '# Historical source notes\n\nPreserved source preamble and undated sections; these are historical, not current instructions.\n\n')
            files[rel] = bytearray(header.encode())
        rebased, edits = relocate_links(block, source, destination / rel)
        # Blank separator is outside the source fragment.
        files[rel].extend(b'\n\n')
        pieces[i] = {'file': rel, 'offset': len(files[rel]), 'length': len(rebased),
                     'storedSha256': digest(rebased), 'originalSha256': digest(block), 'linkEdits': edits, 'anchorHex': rebased[:64].hex()}
        files[rel].extend(rebased)
    months = sorted([rel for rel in files if rel != 'migration-notes.md'], reverse=True)
    index = '# Work History Index\n\n## Current log\n\n' + f'- [{months[0]}]({months[0]})\n'
    index += '\n## Earlier logs\n\n' + ''.join(f'- [{rel}]({rel})\n' for rel in months[1:])
    if 'migration-notes.md' in files:
        index += '- [Historical source notes](migration-notes.md)\n'
    index += '\n## Latest work\n\nReplace this section with a concise current handoff after reviewing the migration.\n'
    index += '\n## Reading rule\n\nRead this index first; search monthly logs with `rg` and open only matching entries.\n'
    files['index.md'] = bytearray(index.encode())
    manifest = {'schemaVersion': 1, 'sourceName': source.name, 'sourceBytes': len(data),
                'sourceSha256': digest(data), 'pieces': pieces}
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.history-draft-', dir=destination.parent))
    try:
        for rel, content in files.items():
            path = temp / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        proof = temp / '.migration-proof.json'
        proof.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        verify_manifest(proof)
        if source.read_bytes() != data:
            raise RuntimeError('source changed during migration; retry from current content')
        temp.rename(destination)
    except Exception:
        shutil.rmtree(temp, ignore_errors=True)
        raise
    return destination / '.migration-proof.json'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    split = sub.add_parser('split')
    split.add_argument('--source', required=True, type=Path)
    split.add_argument('--destination', required=True, type=Path)
    verify = sub.add_parser('verify')
    verify.add_argument('manifest', type=Path)
    args = parser.parse_args()
    if args.command == 'split':
        manifest = split_history(args.source, args.destination)
        print(f'Draft created; source retained. Verify before removing source: {manifest}')
    else:
        print(json.dumps(verify_manifest(args.manifest)))


if __name__ == '__main__':
    main()
