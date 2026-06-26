from __future__ import annotations

from pathlib import Path
from typing import Any

from .experiment import (
    label_targets_from_config,
    read_experiment_config,
    split_config,
)


def _toml_list(values: list[str]) -> str:
    return "[" + ", ".join(f'"{value}"' for value in values) + "]"


def write_probe_config(
    experiment_path: str | Path,
    out_path: str | Path,
    *,
    artifact_manifest: str | None = None,
) -> dict[str, Any]:
    config = read_experiment_config(experiment_path)
    targets = label_targets_from_config(config)
    prompts = config.get("prompts", {})
    position_policy = prompts.get("position_policy", "prompt_final") if isinstance(prompts, dict) else "prompt_final"
    splits = split_config(config)
    manifest_value = artifact_manifest or "/path/to/artifact_manifest.json"

    payload = {
        "schema": "sarf_probe_config_v0_4",
        "experiment": str(experiment_path),
        "target_labels": targets,
        "split_strategies": splits["strategies"],
        "artifact_manifest": artifact_manifest,
        "position_policy": str(position_policy),
        "not_probe_training": True,
    }
    text = "\n".join(
        [
            '# Sarf probe config scaffold only. This file does not train probes.',
            'schema = "sarf_probe_config_v0_4"',
            f'experiment = "{experiment_path}"',
            f"target_labels = {_toml_list(targets)}",
            f"split_strategies = {_toml_list(splits['strategies'])}",
            f'artifact_manifest = "{manifest_value}"',
            f'position_policy = "{position_policy}"',
            "",
            "[layers]",
            '# Replace with concrete layer indices after an external backend has produced artifacts.',
            "selection = []",
            "",
            "[probe]",
            '# Placeholder only. Base Sarf does not train probes.',
            'type = "linear_probe_placeholder"',
            'input_artifact = "hidden_states_placeholder"',
            "",
            "[notes]",
            'scope = "configuration scaffolding only"',
            'does_not = "run model inference, extract hidden states, or train probes"',
            "",
        ]
    )
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return payload


def write_baseline_scaffolds(experiment_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = read_experiment_config(experiment_path)
    targets = label_targets_from_config(config)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "char_ngram.toml").write_text(
        "\n".join(
            [
                '# Sarf baseline config. Use with `sarf run-baseline --config char_ngram.toml --splits split_metadata.json --out char_ngram.results.json`.',
                'schema = "sarf_baseline_config_v0_5"',
                'baseline = "char_ngram"',
                f'experiment = "{experiment_path}"',
                f"target_labels = {_toml_list(targets)}",
                "",
                "[features]",
                "ngram_min = 1",
                "ngram_max = 5",
                "",
                "[dependencies]",
                "# Optional Python modules this baseline needs beyond base Sarf.",
                "modules = []",
                "",
                "[notes]",
                'status = "runnable_optional_baseline"',
                'does_not = "run model inference, extract hidden states, or train probes"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "majority.toml").write_text(
        "\n".join(
            [
                '# Sarf majority baseline config. Use with `sarf run-baseline --config majority.toml --splits split_metadata.json --out majority.results.json`.',
                'schema = "sarf_baseline_config_v0_5"',
                'baseline = "majority"',
                f'experiment = "{experiment_path}"',
                f"target_labels = {_toml_list(targets)}",
                "",
                "[dependencies]",
                "# Optional Python modules this baseline needs beyond base Sarf.",
                "modules = []",
                "",
                "[notes]",
                'status = "runnable_optional_baseline"',
                'prediction_policy = "use the most frequent training label"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "# Sarf Baseline Scaffolds",
                "",
                "These files describe expected baseline configuration inputs and outputs.",
                "They can be consumed by the optional standard-library Sarf baseline runner.",
                "",
                "Expected inputs:",
                "",
                "- Morphology dataset JSONL",
                "- Split metadata with train/test assignments",
                "- Target labels from the experiment TOML",
                "",
                "Optional dependency guard:",
                "",
                "- Leave `[dependencies].modules = []` for bundled standard-library runners.",
                "- Add module names only when a local baseline implementation requires them.",
                "- `sarf run-baseline` fails before writing artifacts if a declared module is missing.",
                "",
                "Expected outputs:",
                "",
                "- Per-label predictions",
                "- Per-label aggregate metrics",
                "- Warnings for labels unseen in train",
                "",
                "Run example:",
                "",
                "```bash",
                "sarf run-baseline --config char_ngram.toml --splits ../split_metadata.json --out char_ngram.results.json",
                "sarf summarize-baseline char_ngram.results.json",
                "```",
                "",
                "The runner does not run model inference, extract hidden states, train probes, or add heavyweight dependencies.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "schema": "sarf_baseline_scaffolds_v0_5",
        "experiment": str(experiment_path),
        "out_dir": str(out),
        "files": ["char_ngram.toml", "majority.toml", "README.md"],
        "optional_baseline_runner": True,
    }
