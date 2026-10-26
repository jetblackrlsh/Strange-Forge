import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from strange_forge.reference import build_index, load_index, search_index


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "fictional.txt"
        self.source.write_text("Fictional trial. Copper clock.\fCopper clock clock. Action cost.\f", encoding="utf-8")
        self.output = self.root / "private-index.json"

    def test_pages_fingerprint_and_cited_search(self):
        index = build_index(self.source, self.output, "Fictional Rules", "Test")
        self.assertEqual(len(index["pages"]), 2)
        self.assertEqual(index, load_index(self.output))
        results = search_index(index, "clock")
        self.assertEqual([r["page"] for r in results], [2, 1])
        self.assertEqual(results[0]["citation"], "Fictional Rules Test, PDF p. 2")
        self.assertEqual(len(index["source_sha256"]), 64)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_search_is_all_terms_and_bounded(self):
        index = build_index(self.source, self.output)
        self.assertEqual(len(search_index(index, "action clock")), 1)
        self.assertEqual(search_index(index, "missing"), [])
        self.assertEqual(search_index(index, ""), [])
        for limit in (0, 21, True):
            with self.assertRaises(ValueError):
                search_index(index, "clock", limit)
        with self.assertRaises(ValueError):
            search_index(index, "x" * 501)

    def test_reject_empty_and_overwrite_and_wrong_format(self):
        with self.assertRaises(ValueError):
            build_index(self.source, self.source)
        self.source.write_text(" \f ")
        with self.assertRaises(ValueError):
            build_index(self.source, self.output)
        source = self.root / "unsupported.json"
        source.write_text("{}")
        with self.assertRaises(ValueError):
            build_index(source, self.output)

    def test_malformed_index_rejected(self):
        index = build_index(self.source, self.output)
        for key, value in [("version", 2), ("source_sha256", "invalid"), ("pages", [{"page": 9, "text": "bad"}])]:
            damaged = dict(index, **{key: value})
            self.output.write_text(json.dumps(damaged))
            with self.assertRaises(ValueError):
                load_index(self.output)

    def test_missing_pdf_extractor_is_actionable(self):
        pdf = self.root / "test.pdf"
        pdf.write_bytes(b"%PDF-test")
        with patch("strange_forge.reference.subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(ValueError, "Poppler"):
                build_index(pdf, self.output)


if __name__ == "__main__":
    unittest.main()
