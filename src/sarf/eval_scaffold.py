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
            '# Sarf v0.4 probe config scaffold only. This file does not train probes.',
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
            '# Placeholder only. Base Sarf v0.4 does not train probes.',
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
                '# Sarf v0.4 baseline config scaffold only. This does not train a baseline.',
                'schema = "sarf_baseline_config_v0_4"',
                'baseline = "char_ngram_placeholder"',
                f'experiment = "{experiment_path}"',
                f"target_labels = {_toml_list(targets)}",
                "",
                "[features]",
                "ngram_min = 1",
                "ngram_max = 5",
                "",
                "[notes]",
                'status = "placeholder"',
                'does_not = "fit classifiers or run evaluation"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "majority.toml").write_text(
        "\n".join(
            [
                '# Sarf v0.4 majority baseline config scaffold only. This does not train a baseline.',
                'schema = "sarf_baseline_config_v0_4"',
                'baseline = "majority_placeholder"',
                f'experiment = "{experiment_path}"',
                f"target_labels = {_toml_list(targets)}",
                "",
                "[notes]",
                'status = "placeholder"',
                'prediction_policy = "use the most frequent training label after an external runner computes it"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (out / "README.md").write_text(
        "\n".join(
            [
                "# Sarf v0.4 Baseline Scaffolds",
                "",
                "These files describe expected baseline configuration inputs and outputs.",
                "They are placeholders for external or future lightweight runners.",
                "",
                "Expected inputs:",
                "",
                "- Morphology dataset JSONL",
                "- Split metadata with train/test assignments",
                "- Target labels from the experiment TOML",
                "",
                "Expected outputs:",
                "",
                "- Per-label predictions",
                "- Per-label aggregate metrics",
                "- Warnings for labels unseen in train",
                "",
                "Sarf v0.4 does not train baselines unless a separate lightweight implementation is added.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "schema": "sarf_baseline_scaffolds_v0_4",
        "experiment": str(experiment_path),
        "out_dir": str(out),
        "files": ["char_ngram.toml", "majority.toml", "README.md"],
        "not_baseline_training": True,
    }
