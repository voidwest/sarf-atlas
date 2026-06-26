from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .dataset import normalize_record, validate_dataset_rows
from .ember_config import write_ember_config
from .io import read_jsonl, write_json, write_jsonl
from .prompts import make_prompts
from .splits import heldout_split


SPLIT_METADATA_SCHEMA_VERSION = 1
EXPERIMENT_SUMMARY_SCHEMA_VERSION = 1


def read_experiment_config(path: str | Path) -> dict[str, Any]:
    return tomllib.loads(Path(path).read_text(encoding="utf-8"))


def dataset_path_from_config(config: dict[str, Any], *, config_path: str | Path) -> Path:
    dataset = config.get("dataset", {})
    path = dataset.get("path") if isinstance(dataset, dict) else None
    if not path:
        raise ValueError("[dataset].path is required")
    dataset_path = Path(path)
    if not dataset_path.is_absolute():
        dataset_path = Path(config_path).parent / dataset_path
    return dataset_path


def normalized_dataset_from_config(config: dict[str, Any], *, config_path: str | Path) -> list[dict[str, Any]]:
    return [normalize_record(row) for row in read_jsonl(dataset_path_from_config(config, config_path=config_path))]


def prompt_template_from_config(config: dict[str, Any]) -> str:
    prompts = config.get("prompts", {})
    if isinstance(prompts, dict) and prompts.get("template"):
        return str(prompts["template"])
    return "حلل صرفيا الكلمة العربية: {surface}."


def label_targets_from_config(config: dict[str, Any]) -> list[str]:
    labels = config.get("labels", {})
    targets = labels.get("targets", []) if isinstance(labels, dict) else []
    return [str(target) for target in targets]


def split_config(config: dict[str, Any]) -> dict[str, Any]:
    splits = config.get("splits", {})
    if not isinstance(splits, dict):
        return {"strategies": ["lemma_heldout"], "test_fraction": 0.2, "seed": 42}
    return {
        "strategies": [str(strategy) for strategy in splits.get("strategies", ["lemma_heldout"])],
        "test_fraction": float(splits.get("test_fraction", 0.2)),
        "seed": int(splits.get("seed", 42)),
    }


def make_prompts_from_experiment(config_path: str | Path) -> list[dict[str, Any]]:
    config = read_experiment_config(config_path)
    return make_prompts(
        normalized_dataset_from_config(config, config_path=config_path),
        prompt_template_from_config(config),
        label_targets=label_targets_from_config(config),
    )


def make_splits_from_experiment(config_path: str | Path) -> dict[str, Any]:
    config = read_experiment_config(config_path)
    rows = normalized_dataset_from_config(config, config_path=config_path)
    options = split_config(config)
    return {
        "schema": "sarf_split_metadata_v0_4",
        "schema_version": SPLIT_METADATA_SCHEMA_VERSION,
        "strategies": [
            heldout_split(rows, strategy=strategy, test_fraction=options["test_fraction"], seed=options["seed"])
            for strategy in options["strategies"]
        ],
        "seed": options["seed"],
        "test_fraction": options["test_fraction"],
        "not_research_output": True,
    }


def write_experiment_scaffold(config_path: str | Path, out_dir: str | Path) -> dict[str, Any]:
    config = read_experiment_config(config_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    prompts_path = out / "prompts.jsonl"
    splits_path = out / "split_metadata.json"
    backend_config_path = out / "backend.placeholder.toml"
    manifest_path = out / "artifact_manifest.placeholder.json"
    report_path = out / "summary.md"

    prompts = make_prompts_from_experiment(config_path)
    splits = make_splits_from_experiment(config_path)
    validation = validate_dataset_rows(normalized_dataset_from_config(config, config_path=config_path))
    from .diagnostics import label_diagnostics, split_diagnostics

    labels = label_diagnostics(config_path)
    write_jsonl(prompts_path, prompts)
    write_json(splits_path, splits)
    split_summary = split_diagnostics(dataset_path_from_config(config, config_path=config_path), splits_path)

    run = config.get("experiment", {})
    run_id = str(run.get("run_id", out.name)) if isinstance(run, dict) else out.name
    backend = config.get("backend", {})
    write_ember_config(
        backend_config_path,
        run_id=run_id,
        model_path=str(backend.get("model_path", "/path/to/model.gguf")) if isinstance(backend, dict) else "/path/to/model.gguf",
        tokenizer_path=str(backend.get("tokenizer_path", "/path/to/tokenizer.json")) if isinstance(backend, dict) else "/path/to/tokenizer.json",
        prompts_path=str(prompts_path),
        output_dir=str(out / "backend-output"),
        backend=str(backend.get("name", "native")) if isinstance(backend, dict) else "native",
        architecture=str(backend.get("architecture", "qwen3")) if isinstance(backend, dict) else "qwen3",
        write_logits=True,
    )
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "run_id": run_id,
            "backend": {"name": "placeholder", "adapter": "sarf.backends.files"},
            "prompts_path": str(prompts_path),
            "tokenization_path": None,
            "positions_path": None,
            "logits_path": None,
            "hidden_states_path": None,
            "report_path": None,
            "not_research_output": True,
        },
    )

    summary = {
        "schema_version": EXPERIMENT_SUMMARY_SCHEMA_VERSION,
        "run_id": run_id,
        "dataset": str(dataset_path_from_config(config, config_path=config_path)),
        "dataset_validation": validation,
        "label_diagnostics": labels,
        "split_diagnostics": split_summary,
        "prompts_path": str(prompts_path),
        "splits_path": str(splits_path),
        "backend_config_path": str(backend_config_path),
        "artifact_manifest_path": str(manifest_path),
        "report_path": str(report_path),
        "still_out_of_scope": [
            "probe training",
            "model execution",
            "hidden-state extraction",
            "paper reproduction claims",
        ],
    }
    report_path.write_text(render_experiment_markdown(summary), encoding="utf-8")
    write_json(out / "summary.json", summary)
    write_json(out / "experiment.summary.json", summary)
    return summary


def render_experiment_markdown(summary: dict[str, Any]) -> str:
    validation = summary["dataset_validation"]
    lines = [
        f"# Sarf Experiment Summary: {summary['run_id']}",
        "",
        "## Dataset",
        "",
        f"- Path: `{summary['dataset']}`",
        f"- Rows: {validation['row_count']}",
        f"- Validation: {'passed' if validation['passed'] else 'failed'}",
        "",
    ]
    if "label_diagnostics" in summary:
        label_report = summary["label_diagnostics"]
        lines.extend(
            [
                "## Label Diagnostics",
                "",
                f"- Target labels: {', '.join(label_report.get('target_labels', [])) or 'none'}",
                f"- Warnings: {len(label_report.get('warnings', []))}",
            ]
        )
        for warning in label_report.get("warnings", []):
            lines.append(f"  - {warning}")
        lines.append("")
    if "split_diagnostics" in summary:
        split_report = summary["split_diagnostics"]
        lines.extend(["## Split Diagnostics", ""])
        for strategy in split_report.get("strategies", []):
            counts = ", ".join(f"{name}={count}" for name, count in sorted(strategy.get("counts", {}).items()))
            lines.append(f"- {strategy.get('strategy')}: {counts}")
        lines.append(f"- Warnings: {len(split_report.get('warnings', []))}")
        for warning in split_report.get("warnings", []):
            lines.append(f"  - {warning}")
        lines.append("")
    lines.extend(
        [
            "## Generated Files",
            "",
            f"- Prompts: `{summary['prompts_path']}`",
            f"- Splits: `{summary['splits_path']}`",
            f"- Backend config stub: `{summary['backend_config_path']}`",
            f"- Artifact manifest stub: `{summary['artifact_manifest_path']}`",
            "",
            "## What Sarf Still Does Not Do",
            "",
            "Sarf does not train probes, run models, extract hidden states, run model inference, or claim paper reproduction. It prepares and validates the workflow structure around those steps.",
            "",
        ]
    )
    return "\n".join(lines)
