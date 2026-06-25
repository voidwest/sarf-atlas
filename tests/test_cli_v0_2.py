from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sarf.cli import main


class V02CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> str:
        buffer = io.StringIO()
        with patch.dict("os.environ", {"PATH": ""}, clear=True), redirect_stdout(buffer):
            try:
                exit_code = main(argv)
            except SystemExit as exc:
                exit_code = int(exc.code)
        self.assertEqual(exit_code, 0)
        return buffer.getvalue()

    def test_help_lists_v0_2_commands(self) -> None:
        output = self.run_cli(["--help"])

        self.assertIn("init", output)
        self.assertIn("import-artifacts", output)
        self.assertIn("summarize-run", output)

    def test_init_writes_clean_project_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "project"
            self.run_cli(["init", str(project_dir), "--name", "paper1"])

            for relative in [
                "data/raw",
                "data/processed",
                "prompts",
                "splits",
                "configs",
                "artifacts/imported",
                "runs",
                "reports",
                "docs",
            ]:
                self.assertTrue((project_dir / relative).is_dir(), relative)

            project = json.loads((project_dir / "sarf.project.json").read_text(encoding="utf-8"))
            self.assertEqual(project["name"], "paper1")
            self.assertEqual(project["sarf_version"], "0.4")

    def test_summarize_run_accepts_project_directory_without_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "project"
            self.run_cli(["init", str(project_dir)])

            output = self.run_cli(["summarize-run", str(project_dir)])
            summary = json.loads(output)
            self.assertEqual(summary["project_path"], str(project_dir))
            self.assertEqual(summary["manifest_count"], 0)
            self.assertEqual(summary["runs"], [])

    def test_import_artifacts_from_files_and_summarize_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = root / "prompts.jsonl"
            prompts.write_text('{"id":"p1","prompt":"x"}\n', encoding="utf-8")
            manifest = root / "manifest.json"
            summary = root / "summary.json"

            self.run_cli(
                [
                    "import-artifacts",
                    "--from",
                    "files",
                    "--run-id",
                    "run-1",
                    "--prompts-path",
                    str(prompts),
                    "--logits-path",
                    "logits.npy",
                    "--out",
                    str(manifest),
                ]
            )

            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["run_id"], "run-1")
            self.assertEqual(payload["backend"]["adapter"], "sarf.backends.files")
            self.assertEqual(payload["logits_path"], "logits.npy")

            self.run_cli(["summarize-run", "--manifest", str(manifest), "--out", str(summary)])
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["run_id"], "run-1")
            self.assertTrue(summary_payload["validation"]["passed"])
            self.assertTrue(summary_payload["capabilities"]["has_logits"])
            self.assertFalse(summary_payload["capabilities"]["has_hidden_states"])

    def test_example_workflow_uses_v0_2_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.run_cli(["example-workflow", "--out-dir", tmp])
            root = Path(tmp)

            self.assertTrue((root / "sarf.project.json").is_file())
            self.assertTrue((root / "data/processed/toy_morphology.jsonl").is_file())
            self.assertTrue((root / "prompts/toy_prompts.jsonl").is_file())
            self.assertTrue((root / "splits/toy_split_metadata.json").is_file())
            self.assertTrue((root / "configs/ember_native_logits.placeholder.toml").is_file())
            self.assertTrue((root / "artifacts/imported/sarf_artifact_manifest.placeholder.json").is_file())


if __name__ == "__main__":
    unittest.main()
