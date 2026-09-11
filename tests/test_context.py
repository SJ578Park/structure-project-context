import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skill/structure-project-context/scripts'
sys.path.insert(0, str(SCRIPTS))
import context_structure as context
from history_archive import split_history, verify_manifest


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def source(self, text):
        p = self.root / 'docs/HISTORY.md'
        p.parent.mkdir(exist_ok=True)
        p.write_bytes(text.encode())
        return p

    def validate(self, history_only=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = context.validate(self.root, history_only)
        return result, output.getvalue()

    def test_preserves_preamble_undated_notes_authors_and_code_fences(self):
        src = self.source('# History\r\n\r\n## 2026-05-03 / Alice\r\nfirst\r\n```md\r\n## 1999-01-01 fake\r\n```\r\n## Pending\r\nUnverified old claim\r\n## 2026-06-01: Bob\r\nsecond\r\n')
        before = src.read_bytes()
        proof = split_history(src, self.root / 'docs/history')
        self.assertEqual(verify_manifest(proof)['sourceBytes'], len(before))
        self.assertEqual(src.read_bytes(), before)
        self.assertFalse((proof.parent / '1999').exists())
        self.assertIn('Unverified old claim', (proof.parent / 'migration-notes.md').read_text())
        self.assertIn('Alice', (proof.parent / '2026/2026-05.md').read_text())

    def test_sorts_newest_first_without_rewriting_entries(self):
        src = self.source('# H\n## 2026-05-01\nold\n## 2026-05-09\nnew\n## 2026-05-09 — other author\nsame day\n')
        proof = split_history(src, self.root / 'docs/history')
        result = (proof.parent / '2026/2026-05.md').read_text()
        self.assertLess(result.index('05-09\n'), result.index('05-09 —'))
        self.assertLess(result.index('05-09 —'), result.index('05-01'))
        verify_manifest(proof)

    def test_rebases_relative_links_and_reconstructs_original(self):
        src = self.source('# H\n## 2026-05-01\n[Guide](guide.md#section) [Web](https://example.com)\n')
        proof = split_history(src, self.root / 'docs/history')
        result = (proof.parent / '2026/2026-05.md').read_text()
        self.assertIn('](../../guide.md#section)', result)
        self.assertIn('](https://example.com)', result)
        verify_manifest(proof)

    def test_proof_survives_prepend_but_detects_changed_original(self):
        src = self.source('# H\n## 2026-05-01\noriginal fact\n')
        proof = split_history(src, self.root / 'docs/history')
        month = proof.parent / '2026/2026-05.md'
        month.write_text('## 2026-05-02\nnew work\n\n' + month.read_text())
        verify_manifest(proof)
        month.write_text(month.read_text().replace('original fact', 'rewritten fact'))
        with self.assertRaises(RuntimeError):
            verify_manifest(proof)

    def test_proof_detects_removal_of_an_identical_repeated_entry(self):
        entry = '## 2026-05-01\nrepeated fact\n'
        src = self.source('# H\n' + entry + entry)
        proof = split_history(src, self.root / 'docs/history')
        month = proof.parent / '2026/2026-05.md'
        month.write_text(month.read_text().replace(entry, '', 1))
        with self.assertRaises(RuntimeError): verify_manifest(proof)

    def test_complex_links_fail_before_any_destination_write(self):
        src = self.source('## 2026-05-01\n[guide](guide.md "title")\n')
        dest = self.root / 'docs/history'
        with self.assertRaises(RuntimeError): split_history(src, dest)
        self.assertFalse(dest.exists())

    def test_existing_destination_and_undated_source_are_not_overwritten(self):
        src = self.source('# H\nNo known dates\n')
        dest = self.root / 'docs/history'
        with self.assertRaises(RuntimeError): split_history(src, dest)
        self.assertFalse(dest.exists())
        src.write_text('## 2026-05-01\nwork\n')
        dest.mkdir(); (dest / 'kept').write_text('keep')
        with self.assertRaises(RuntimeError): split_history(src, dest)
        self.assertEqual((dest / 'kept').read_text(), 'keep')

    def test_unsupported_reference_links_fail_without_creating_draft(self):
        src = self.source('## 2026-05-01\n[guide][g]\n[g]: guide.md\n')
        dest = self.root / 'docs/history'
        with self.assertRaises(RuntimeError): split_history(src, dest)
        self.assertFalse(dest.exists())

    def test_large_flat_history_fails_and_small_history_passes(self):
        src = self.source('# H\n## 2026-05-01\n' + 'work\n' * 300)
        self.assertEqual(self.validate(True)[0], 1)
        src.write_text('# H\n## 2026-05-01\nshort\n')
        self.assertEqual(self.validate(True)[0], 0)
        src.write_text('# H\n## 2026-05-01\n' + '긴문장' * 5000)
        self.assertEqual(self.validate(True)[0], 1)

    def test_oversized_or_accumulating_index_fails(self):
        context.scaffold(self.root)
        index = self.root / 'docs/project-context/history/index.md'
        self.assertEqual(self.validate()[0], 0)
        original = index.read_text()
        index.write_text(original + '\n'.join(f'### 2026-05-0{i}\n- work\n' for i in range(1, 5)))
        self.assertIn('dated summaries; keep at most 3', self.validate()[1])
        index.write_text(original + 'x' * 8200)
        self.assertEqual(self.validate()[0], 1)

    def test_hybrid_supports_uppercase_memory_and_optional_decisions(self):
        src = self.source('## 2026-05-01\nwork\n')
        split_history(src, self.root / 'docs/history')
        self.assertIn('superseded history', self.validate(True)[1])
        src.unlink()
        (self.root / 'docs/SESSION.md').write_text('# Session\n')
        (self.root / 'docs/MEMORY.md').write_text('# Memory\n' + 'fact\n' * 201)
        (self.root / 'AGENTS.md').write_text('Read docs/SESSION.md docs/MEMORY.md docs/history/index.md\n')
        code, output = self.validate()
        self.assertEqual(code, 0)
        self.assertIn('WARNING', output)

    def test_full_migration_recognizes_docs_sources_and_preserves_undated_text(self):
        src = self.source('# H\n## 2026-05-01 | Alice\nwork\n## Undated\nkeep all\n')
        (self.root / 'docs/MEMORY.md').write_text('durable fact\n')
        with contextlib.redirect_stdout(io.StringIO()): context.migrate(self.root)
        self.assertTrue(src.exists())
        proof = self.root / 'docs/project-context/history/.migration-proof.json'
        verify_manifest(proof)
        self.assertIn('keep all', (proof.parent / 'migration-notes.md').read_text())
        self.assertIn('legacy context', self.validate()[1])

    def test_ambiguous_legacy_sources_fail_before_writes(self):
        self.source('## 2026-05-01\nwork\n')
        (self.root / 'history.md').write_text('## 2026-05-02\nother source\n')
        with self.assertRaises(RuntimeError): context.migrate(self.root)
        self.assertFalse((self.root / 'docs/project-context').exists())


if __name__ == '__main__':
    unittest.main()
