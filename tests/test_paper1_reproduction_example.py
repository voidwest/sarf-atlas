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


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET = REPO_ROOT / "examples/paper_style/tiny_morphology.jsonl"
EXPERIMENT = REPO_ROOT / "examples/paper1_reproduction/experiment.toml"
MOCK_BACKEND = REPO_ROOT / "examples/paper1_reproduction/mock_backend"


class Paper1ReproductionExampleTests(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> str:
        buffer = io.StringIO()
        with patch.dict("os.environ", {"PATH": ""}, clear=True), redirect_stdout(buffer):
            try:
                exit_code = main(argv)
            except SystemExit as exc:
                exit_code = int(exc.code)
        self.assertEqual(exit_code, 0)
        return buffer.getvalue()

    def test_paper1_style_example_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            dataset_validation = out / "dataset_validation.json"
            label_diagnostics = out / "label_diagnostics.json"
            prompts = out / "prompts.jsonl"
            splits = out / "splits.json"
            split_diagnostics = out / "split_diagnostics.json"
            tokenization_diagnostics = out / "tokenization_diagnostics.json"
            artifact_manifest = out / "artifact_manifest.json"
            artifact_validation = out / "artifact_validation.json"
            artifact_summary = out / "artifact_summary.json"
            probe_config = out / "probe_config.toml"
            baselines = out / "baselines"
            char_results = out / "char_ngram.results.json"
            majority_results = out / "majority.results.json"
            char_summary = out / "char_ngram.summary.json"
            run_dir = out / "run"
            report = out / "report.md"
            alternate_tokenization = out / "alternate_tokenization.json"
            alternate_tokenization.write_text(
                json.dumps(
                    {
                        "schema": "sarf_mock_tokenization_v0_6",
                        "run_id": "paper1-style-demo-alt",
                        "not_research_output": True,
                        "samples": [
                            {"id": "sample-0001", "token_count": 1},
                            {"id": "sample-0002", "token_count": 2},
                            {"id": "sample-0003", "token_count": 3},
                            {"id": "sample-0004", "token_count": 1},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            self.run_cli(["validate-dataset", str(DATASET), "--out", str(dataset_validation)])
            self.run_cli(["validate-labels", str(EXPERIMENT), "--out", str(label_diagnostics)])
            self.run_cli(["make-prompts", str(EXPERIMENT), "--out", str(prompts)])
            self.run_cli(["make-splits", str(EXPERIMENT), "--out", str(splits)])
            self.run_cli(["summarize-splits", str(DATASET), str(splits), "--out", str(split_diagnostics)])
            self.run_cli(
                [
                    "tokenization-diagnostics",
                    str(EXPERIMENT),
                    "--tokenization-artifact",
                    str(MOCK_BACKEND / "tokenization.json"),
                    "--tokenization-artifact",
                    str(alternate_tokenization),
                    "--out",
                    str(tokenization_diagnostics),
                ]
            )
            self.run_cli(
                [
                    "import-artifacts",
                    "--from",
                    "files",
                    "--run-id",
                    "paper1-style-demo",
                    "--prompts-path",
                    str(prompts),
                    "--tokenization-path",
                    str(MOCK_BACKEND / "tokenization.json"),
                    "--positions-path",
                    str(MOCK_BACKEND / "positions.json"),
                    "--hidden-states-path",
                    str(MOCK_BACKEND / "hidden_states.json"),
                    "--report-path",
                    str(MOCK_BACKEND / "report.json"),
                    "--out",
                    str(artifact_manifest),
                ]
            )
            self.run_cli(["validate-manifest", "--manifest", str(artifact_manifest), "--out", str(artifact_validation)])
            self.run_cli(["summarize-run", "--manifest", str(artifact_manifest), "--out", str(artifact_summary)])
            self.run_cli(
                [
                    "make-probe-config",
                    str(EXPERIMENT),
                    "--artifact-manifest",
                    str(artifact_manifest),
                    "--out",
                    str(probe_config),
                ]
            )
            self.run_cli(["make-baselines", str(EXPERIMENT), "--out", str(baselines)])
            self.run_cli(
                [
                    "run-baseline",
                    "--config",
                    str(baselines / "char_ngram.toml"),
                    "--splits",
                    str(splits),
                    "--out",
                    str(char_results),
                ]
            )
            self.run_cli(
                [
                    "run-baseline",
                    "--config",
                    str(baselines / "majority.toml"),
                    "--splits",
                    str(splits),
                    "--out",
                    str(majority_results),
                ]
            )
            self.run_cli(["summarize-baseline", str(char_results), "--out", str(char_summary)])
            self.run_cli(["make-experiment", str(EXPERIMENT), "--out", str(run_dir)])
            self.run_cli(["report", str(run_dir), "--out", str(report)])

            validation_payload = json.loads(dataset_validation.read_text(encoding="utf-8"))
            self.assertTrue(validation_payload["passed"])

            split_payload = json.loads(split_diagnostics.read_text(encoding="utf-8"))
            self.assertTrue(any("possible leakage" in warning for warning in split_payload["warnings"]))
            self.assertTrue(any("test contains unseen" in warning for warning in split_payload["warnings"]))

            tokenization_payload = json.loads(tokenization_diagnostics.read_text(encoding="utf-8"))
            self.assertEqual(tokenization_payload["schema"], "sarf_tokenization_diagnostics_v0_7")
            self.assertEqual(tokenization_payload["schema_version"], 1)
            self.assertEqual(tokenization_payload["summary"]["mean_artifact_token_count"], 2.75)
            self.assertEqual(len(tokenization_payload["artifact_comparisons"]), 2)
            self.assertFalse(tokenization_payload["backend_checks"]["checked"])

            artifact_payload = json.loads(artifact_summary.read_text(encoding="utf-8"))
            self.assertEqual(artifact_payload["schema_version"], 1)
            self.assertTrue(artifact_payload["capabilities"]["has_hidden_states"])
            self.assertTrue(artifact_payload["validation"]["artifact_paths"]["hidden_states_path"]["exists"])

            char_payload = json.loads(char_results.read_text(encoding="utf-8"))
            majority_payload = json.loads(majority_results.read_text(encoding="utf-8"))
            self.assertEqual(char_payload["schema"], "sarf_baseline_results_v0_5")
            self.assertEqual(majority_payload["baseline"], "majority")

            summary_payload = json.loads(char_summary.read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["schema"], "sarf_baseline_summary_v0_5")

            report_text = report.read_text(encoding="utf-8")
            self.assertIn("Sarf Experiment Summary", report_text)
            self.assertIn("does not train probes", report_text)


if __name__ == "__main__":
    unittest.main()
