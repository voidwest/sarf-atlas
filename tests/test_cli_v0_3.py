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


DATASET = [
    {
        "id": "sample-0001",
        "surface": "كتب",
        "lemma": "كتب",
        "root": "ك ت ب",
        "pos": "VERB",
        "abstract_pattern": "فعل",
        "concrete_pattern": "كتب",
        "gender": None,
        "number": None,
        "features": {"aspect": "perf"},
    },
    {
        "id": "sample-0002",
        "surface": "كاتبة",
        "lemma": "كاتب",
        "root": "ك ت ب",
        "pos": "NOUN",
        "abstract_pattern": "فاعل",
        "concrete_pattern": "كاتبة",
        "gender": "fem",
        "number": "sg",
        "features": {},
    },
    {
        "id": "sample-0003",
        "surface": "درس",
        "lemma": "درس",
        "root": "د ر س",
        "pos": "VERB",
        "abstract_pattern": "فعل",
        "concrete_pattern": "درس",
        "gender": None,
        "number": None,
        "features": {},
    },
]


class V03CliTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> str:
        buffer = io.StringIO()
        with patch.dict("os.environ", {"PATH": ""}, clear=True), redirect_stdout(buffer):
            try:
                exit_code = main(argv)
            except SystemExit as exc:
                exit_code = int(exc.code)
        self.assertEqual(exit_code, 0)
        return buffer.getvalue()

    def write_dataset(self, root: Path) -> Path:
        path = root / "morphology.jsonl"
        path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in DATASET) + "\n",
            encoding="utf-8",
        )
        return path

    def write_config(self, root: Path, dataset_path: Path) -> Path:
        path = root / "experiment.toml"
        path.write_text(
            "\n".join(
                [
                    "[experiment]",
                    'run_id = "paper-style-test"',
                    "",
                    "[dataset]",
                    f'path = "{dataset_path.name}"',
                    "",
                    "[prompts]",
                    'template = "حلل صرفيا الكلمة العربية: {surface}."',
                    'position_policy = "prompt_final"',
                    "",
                    "[labels]",
                    'targets = ["pos", "gender", "number", "root", "lemma", "abstract_pattern"]',
                    "",
                    "[splits]",
                    'strategies = ["lemma_heldout", "root_heldout"]',
                    "test_fraction = 0.34",
                    "seed = 7",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_validate_dataset_accepts_paper_style_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dataset = self.write_dataset(Path(tmp))

            output = self.run_cli(["validate-dataset", str(dataset)])
            report = json.loads(output)
            self.assertTrue(report["passed"])
            self.assertEqual(report["row_count"], 3)
            self.assertIn("abstract_pattern", report["required_fields"])
            self.assertEqual(report["optional_null_counts"]["gender"], 2)

    def test_config_driven_prompts_splits_experiment_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            config = self.write_config(root, dataset)
            prompts = root / "prompts.jsonl"
            splits = root / "splits.json"
            run_dir = root / "run"
            report = root / "report.md"

            self.run_cli(["make-prompts", str(config), "--out", str(prompts)])
            prompt_rows = [json.loads(line) for line in prompts.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(prompt_rows[0]["surface"], "كتب")
            self.assertEqual(prompt_rows[0]["labels"]["root"], "ك ت ب")

            self.run_cli(["make-splits", str(config), "--out", str(splits)])
            split_payload = json.loads(splits.read_text(encoding="utf-8"))
            self.assertEqual([item["strategy"] for item in split_payload["strategies"]], ["lemma_heldout", "root_heldout"])
            self.assertEqual(split_payload["seed"], 7)
            self.assertEqual(split_payload["strategies"][0]["char_baseline_metadata"]["status"], "placeholder")

            self.run_cli(["make-experiment", str(config), "--out", str(run_dir)])
            self.assertTrue((run_dir / "prompts.jsonl").is_file())
            self.assertTrue((run_dir / "split_metadata.json").is_file())
            self.assertTrue((run_dir / "backend.placeholder.toml").is_file())
            self.assertTrue((run_dir / "artifact_manifest.placeholder.json").is_file())
            self.assertTrue((run_dir / "experiment.summary.json").is_file())

            self.run_cli(["report", str(run_dir), "--out", str(report)])
            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Sarf Experiment Summary", report_text)
            self.assertIn("does not train probes", report_text)

    def test_manifest_validation_reports_partial_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prompts = root / "prompts.jsonl"
            prompts.write_text('{"id":"p1","prompt":"x"}\n', encoding="utf-8")
            manifest = root / "manifest.json"

            self.run_cli(
                [
                    "import-artifacts",
                    "--from",
                    "files",
                    "--run-id",
                    "partial",
                    "--prompts-path",
                    str(prompts),
                    "--out",
                    str(manifest),
                ]
            )
            output = self.run_cli(["validate-manifest", "--manifest", str(manifest)])
            report = json.loads(output)
            self.assertTrue(report["passed"])
            self.assertTrue(report["artifact_paths"]["prompts_path"]["exists"])
            self.assertFalse(report["artifact_paths"]["hidden_states_path"]["present"])


if __name__ == "__main__":
    unittest.main()

