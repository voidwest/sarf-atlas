from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sarf.cli import entrypoint, main
from sarf.diagnostics import label_diagnostics, split_diagnostics


ROWS = [
    {
        "id": "r1",
        "surface": "كتب",
        "lemma": "كتب",
        "root": "ك ت ب",
        "pos": "VERB",
        "abstract_pattern": "فعل",
        "concrete_pattern": "كتب",
        "gender": None,
        "number": None,
        "features": {},
    },
    {
        "id": "r2",
        "surface": "كاتب",
        "lemma": "كاتب",
        "root": "ك ت ب",
        "pos": "NOUN",
        "abstract_pattern": "فاعل",
        "concrete_pattern": "كاتب",
        "gender": "masc",
        "number": "sg",
        "features": {},
    },
    {
        "id": "r3",
        "surface": "درس",
        "lemma": "درس",
        "root": "د ر س",
        "pos": "VERB",
        "abstract_pattern": "فعل",
        "concrete_pattern": "درس",
        "gender": "",
        "number": None,
        "features": {},
    },
    {
        "id": "r4",
        "surface": "خرج",
        "lemma": "خرج",
        "root": "خ ر ج",
        "pos": "VERB",
        "abstract_pattern": "فعل",
        "concrete_pattern": "خرج",
        "features": {},
    },
]


class V04CliTests(unittest.TestCase):
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
        path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in ROWS) + "\n", encoding="utf-8")
        return path

    def write_config(self, root: Path, dataset: Path) -> Path:
        path = root / "experiment.toml"
        path.write_text(
            "\n".join(
                [
                    "[experiment]",
                    'run_id = "v04-test"',
                    "",
                    "[dataset]",
                    f'path = "{dataset.name}"',
                    "",
                    "[prompts]",
                    'position_policy = "prompt_final"',
                    "",
                    "[labels]",
                    'targets = ["pos", "root", "lemma", "abstract_pattern", "gender"]',
                    "",
                    "[splits]",
                    'strategies = ["lemma_heldout", "root_heldout"]',
                    "test_fraction = 0.5",
                    "seed = 3",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return path

    def test_label_cardinality_nulls_and_high_cardinality_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            report = label_diagnostics(dataset)
            self.assertEqual(report["labels"]["lemma"]["cardinality"], 4)
            self.assertEqual(report["labels"]["gender"]["missing_or_null"], 3)
            self.assertTrue(any("high-cardinality label 'lemma'" in warning for warning in report["warnings"]))

    def test_experiment_labels_warn_for_heldout_closed_set_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            config = self.write_config(root, dataset)
            report = label_diagnostics(config)
            self.assertTrue(any("closed-set classifier probing for 'root'" in warning for warning in report["warnings"]))

    def test_split_summary_and_overlap_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            split_rows = [
                {**ROWS[0], "split": "train"},
                {**ROWS[1], "split": "test"},
                {**ROWS[2], "split": "test"},
            ]
            splits = root / "splits.jsonl"
            splits.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in split_rows) + "\n", encoding="utf-8")
            report = split_diagnostics(dataset, splits)
            self.assertEqual(report["strategies"][0]["counts"], {"train": 1, "test": 2})
            self.assertEqual(report["strategies"][0]["group_overlap"]["root"], ["ك ت ب"])
            self.assertTrue(any("possible leakage" in warning for warning in report["warnings"]))

    def test_cli_smoke_for_v04_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            config = self.write_config(root, dataset)
            splits = root / "splits.json"
            labels_json = root / "labels.json"
            split_json = root / "split_summary.json"
            token_json = root / "tokenization_summary.json"
            probe_config = root / "probe_config.toml"
            baseline_dir = root / "baselines"
            baseline_results = root / "char_ngram.results.json"
            baseline_summary = root / "char_ngram.summary.json"

            output = self.run_cli(["validate-labels", str(config), "--out", str(labels_json)])
            self.assertIn("Label diagnostics", output)
            self.assertTrue(labels_json.is_file())

            self.run_cli(["make-splits", str(config), "--out", str(splits)])
            output = self.run_cli(["summarize-splits", str(dataset), str(splits), "--out", str(split_json)])
            self.assertIn("Split diagnostics", output)
            self.assertTrue(split_json.is_file())

            output = self.run_cli(["tokenization-diagnostics", str(config), "--out", str(token_json)])
            self.assertIn("Tokenization diagnostics", output)
            token_payload = json.loads(token_json.read_text(encoding="utf-8"))
            self.assertEqual(token_payload["schema"], "sarf_tokenization_diagnostics_v0_7")
            self.assertTrue(
                any("no backend tokenization artifact supplied" in warning for warning in token_payload["warnings"])
            )

            output = self.run_cli(
                [
                    "make-probe-config",
                    str(config),
                    "--artifact-manifest",
                    "artifact_manifest.json",
                    "--out",
                    str(probe_config),
                ]
            )
            self.assertIn("wrote", output)
            self.assertIn("does_not", probe_config.read_text(encoding="utf-8"))

            output = self.run_cli(["make-baselines", str(config), "--out", str(baseline_dir)])
            self.assertIn("wrote", output)
            self.assertTrue((baseline_dir / "char_ngram.toml").is_file())
            self.assertIn("run-baseline", (baseline_dir / "README.md").read_text(encoding="utf-8"))

            output = self.run_cli(
                [
                    "run-baseline",
                    "--config",
                    str(baseline_dir / "char_ngram.toml"),
                    "--splits",
                    str(splits),
                    "--out",
                    str(baseline_results),
                ]
            )
            self.assertIn("wrote", output)
            baseline_payload = json.loads(baseline_results.read_text(encoding="utf-8"))
            self.assertEqual(baseline_payload["schema"], "sarf_baseline_results_v0_5")
            self.assertEqual(baseline_payload["baseline"], "char_ngram")
            self.assertEqual(baseline_payload["dependency_status"]["optional_modules"], [])
            self.assertIn("lemma_heldout", [item["strategy"] for item in baseline_payload["strategies"]])

            output = self.run_cli(["summarize-baseline", str(baseline_results), "--out", str(baseline_summary)])
            self.assertEqual(output, "")
            summary_payload = json.loads(baseline_summary.read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["schema"], "sarf_baseline_summary_v0_5")
            self.assertTrue(summary_payload["dependency_status"]["available"])
            self.assertIn("pos", summary_payload["target_labels"])

    def test_run_baseline_fails_before_output_when_declared_dependency_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            config = self.write_config(root, dataset)
            splits = root / "splits.json"
            baseline_dir = root / "baselines"
            baseline_config = baseline_dir / "char_ngram.toml"
            output_path = root / "missing_dep.results.json"

            self.run_cli(["make-splits", str(config), "--out", str(splits)])
            self.run_cli(["make-baselines", str(config), "--out", str(baseline_dir)])
            baseline_config.write_text(
                baseline_config.read_text(encoding="utf-8").replace(
                    "modules = []",
                    'modules = ["sarf_atlas_missing_optional_baseline_dependency"]',
                ),
                encoding="utf-8",
            )

            error_buffer = io.StringIO()
            with patch.dict("os.environ", {"PATH": ""}, clear=True), redirect_stderr(error_buffer):
                exit_code = entrypoint(
                    [
                        "run-baseline",
                        "--config",
                        str(baseline_config),
                        "--splits",
                        str(splits),
                        "--out",
                        str(output_path),
                    ]
                )
            self.assertEqual(exit_code, 1)
            self.assertIn("missing optional baseline dependencies", error_buffer.getvalue())
            self.assertFalse(output_path.exists())

    def test_report_includes_diagnostics_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dataset = self.write_dataset(root)
            config = self.write_config(root, dataset)
            run_dir = root / "run"
            report = root / "report.md"
            self.run_cli(["make-experiment", str(config), "--out", str(run_dir)])
            self.run_cli(["report", str(run_dir), "--out", str(report)])
            text = report.read_text(encoding="utf-8")
            self.assertIn("Label Diagnostics", text)
            self.assertIn("Split Diagnostics", text)
            self.assertIn("does not train probes", text)


if __name__ == "__main__":
    unittest.main()
