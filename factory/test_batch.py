import json
import tempfile
import unittest
from pathlib import Path

from factory.batch import collect_report, load_targets, write_report


class BatchInventoryTests(unittest.TestCase):
    def test_load_targets_validates_and_normalizes_repository_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "targets.json"
            path.write_text(
                json.dumps([{"owner": "Zopair", "repo": "Sovereign-AI-Arsenal"}]),
                encoding="utf-8",
            )
            self.assertEqual(
                load_targets(path),
                [("Zopair", "Sovereign-AI-Arsenal")],
            )

    def test_load_targets_rejects_invalid_paths_and_duplicate_repositories(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "targets.json"
            path.write_text(
                json.dumps([{"owner": "zopair", "repo": "../secrets"}]),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                load_targets(path)

            path.write_text(
                json.dumps([
                    {"owner": "zopair", "repo": "SINC-OS"},
                    {"owner": "Zopair", "repo": "sinc-os"},
                ]),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_targets(path)

    def test_load_targets_caps_inventory_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "targets.json"
            path.write_text(
                json.dumps([
                    {"owner": "zopair", "repo": f"repo-{index}"}
                    for index in range(26)
                ]),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "1-25"):
                load_targets(path)

    def test_collect_report_continues_after_a_repository_failure(self):
        calls = []

        def inspector(owner, repo):
            calls.append(f"{owner}/{repo}")
            if repo == "broken":
                raise RuntimeError("simulated GitHub API failure")
            return {"repository": f"{owner}/{repo}", "path_count": 3}

        report = collect_report(
            [("zopair", "healthy"), ("zopair", "broken")],
            inspector=inspector,
        )

        self.assertEqual(calls, ["zopair/healthy", "zopair/broken"])
        self.assertEqual(report["summary"], {"total": 2, "succeeded": 1, "failed": 1})
        self.assertTrue(report["results"][0]["ok"])
        self.assertFalse(report["results"][1]["ok"])
        self.assertIn("simulated GitHub API failure", report["results"][1]["error"])

    def test_write_report_creates_parent_and_replaces_output_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "reports" / "inventory.json"
            write_report({"summary": {"total": 1}}, output)

            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                {"summary": {"total": 1}},
            )
            self.assertFalse(output.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
