from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any, Iterable

from .dataset import OPTIONAL_LABEL_FIELDS, REQUIRED_FIELDS, normalize_record
from .experiment import (
    dataset_path_from_config,
    label_targets_from_config,
    read_experiment_config,
    split_config,
)
from .io import read_jsonl


CAUTION_LABELS = {"root", "lemma", "abstract_pattern", "concrete_pattern"}
CLOSED_SET_LABELS = {"pos", "gender", "number", "abstract_pattern"}
DEFAULT_LABELS = ["pos", "gender", "number", "root", "lemma", "abstract_pattern", "concrete_pattern"]


def _is_missing(value: Any) -> bool:
    return value is None or value == ""


def _load_label_input(path: str | Path) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".toml":
        config = read_experiment_config(source)
        rows = [normalize_record(row) for row in read_jsonl(dataset_path_from_config(config, config_path=source))]
        targets = label_targets_from_config(config) or DEFAULT_LABELS
        return rows, targets, {"kind": "experiment", "path": str(source), "splits": split_config(config)}
    rows = [normalize_record(row) for row in read_jsonl(source)]
    return rows, DEFAULT_LABELS, {"kind": "dataset", "path": str(source)}


def label_diagnostics(path: str | Path) -> dict[str, Any]:
    rows, targets, source = _load_label_input(path)
    labels = sorted(set(DEFAULT_LABELS) | set(targets) | set(REQUIRED_FIELDS) | set(OPTIONAL_LABEL_FIELDS))
    per_label: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for label in labels:
        values = [row.get(label) for row in rows]
        missing_count = sum(1 for value in values if _is_missing(value))
        present = [str(value) for value in values if not _is_missing(value)]
        counts = Counter(present)
        cardinality = len(counts)
        ratio = (cardinality / len(present)) if present else 0.0
        per_label[label] = {
            "cardinality": cardinality,
            "missing_or_null": missing_count,
            "present_count": len(present),
            "top_values": dict(counts.most_common(10)),
        }
        if label in CAUTION_LABELS and cardinality >= 3 and ratio >= 0.5:
            warnings.append(
                f"high-cardinality label '{label}' has {cardinality} values across {len(present)} present rows"
            )

    splits = source.get("splits", {})
    strategies = set(splits.get("strategies", [])) if isinstance(splits, dict) else set()
    for label in targets:
        if label in {"root", "lemma"} and any(strategy.endswith("_heldout") for strategy in strategies):
            warnings.append(
                f"closed-set classifier probing for '{label}' is likely inappropriate with heldout split strategies"
            )
        if label in {"abstract_pattern", "concrete_pattern"} and per_label.get(label, {}).get("cardinality", 0) >= 3:
            warnings.append(
                f"pattern label '{label}' may require careful open-set or grouped evaluation under heldout splits"
            )

    return {
        "schema": "sarf_label_diagnostics_v0_4",
        "source": source,
        "row_count": len(rows),
        "target_labels": targets,
        "required_fields": REQUIRED_FIELDS,
        "optional_label_fields": OPTIONAL_LABEL_FIELDS,
        "labels": per_label,
        "warnings": warnings,
    }


def _read_split_payload(path: str | Path) -> Any:
    text = Path(path).read_text(encoding="utf-8")
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _strategy_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and isinstance(payload.get("strategies"), list):
        strategies = []
        for strategy in payload["strategies"]:
            if isinstance(strategy, dict) and isinstance(strategy.get("rows"), list):
                split_field = f"{strategy.get('strategy')}_split"
                strategies.append(
                    {
                        "name": str(strategy.get("strategy", "split")),
                        "unit": strategy.get("unit"),
                        "split_field": split_field,
                        "rows": strategy["rows"],
                    }
                )
        return strategies
    if isinstance(payload, list):
        return [{"name": "split", "unit": None, "split_field": "split", "rows": payload}]
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return [{"name": str(payload.get("strategy", "split")), "unit": payload.get("unit"), "split_field": "split", "rows": payload["rows"]}]
    raise ValueError("unsupported split metadata shape")


def split_diagnostics(dataset_path: str | Path, split_path: str | Path) -> dict[str, Any]:
    dataset_rows = [normalize_record(row) for row in read_jsonl(dataset_path)]
    payload = _read_split_payload(split_path)
    warnings: list[str] = []
    strategies = []

    for strategy in _strategy_rows(payload):
        rows = [normalize_record(row) for row in strategy["rows"]]
        split_field = strategy["split_field"]
        if rows and split_field not in rows[0] and "split" in rows[0]:
            split_field = "split"
        counts = Counter(str(row.get(split_field, "unassigned")) for row in rows)
        train_rows = [row for row in rows if row.get(split_field) == "train"]
        test_rows = [row for row in rows if row.get(split_field) == "test"]

        group_overlap: dict[str, list[str]] = {}
        for field in ["lemma", "root"]:
            train_values = {str(row[field]) for row in train_rows if not _is_missing(row.get(field))}
            test_values = {str(row[field]) for row in test_rows if not _is_missing(row.get(field))}
            overlap = sorted(train_values & test_values)
            group_overlap[field] = overlap
            if overlap:
                warnings.append(f"possible leakage in {strategy['name']}: {field} overlaps train/test")

        label_distributions: dict[str, dict[str, dict[str, int]]] = {}
        unseen_in_train: dict[str, list[str]] = {}
        for label in DEFAULT_LABELS:
            train_counts = Counter(str(row[label]) for row in train_rows if not _is_missing(row.get(label)))
            test_counts = Counter(str(row[label]) for row in test_rows if not _is_missing(row.get(label)))
            label_distributions[label] = {"train": dict(train_counts), "test": dict(test_counts)}
            unseen = sorted(set(test_counts) - set(train_counts))
            if unseen:
                unseen_in_train[label] = unseen
                if label in CLOSED_SET_LABELS:
                    warnings.append(f"test contains unseen '{label}' values in {strategy['name']}: {', '.join(unseen)}")

        strategies.append(
            {
                "strategy": strategy["name"],
                "unit": strategy["unit"],
                "split_field": split_field,
                "counts": dict(counts),
                "group_overlap": group_overlap,
                "label_distributions": label_distributions,
                "unseen_in_train": unseen_in_train,
            }
        )

    return {
        "schema": "sarf_split_diagnostics_v0_4",
        "dataset_path": str(dataset_path),
        "split_path": str(split_path),
        "dataset_row_count": len(dataset_rows),
        "strategies": strategies,
        "warnings": warnings,
    }


def format_label_diagnostics(report: dict[str, Any]) -> str:
    lines = [
        "Label diagnostics",
        f"source: {report['source']['path']}",
        f"rows: {report['row_count']}",
        f"targets: {', '.join(report['target_labels']) if report['target_labels'] else 'none'}",
        "labels:",
    ]
    for label, info in report["labels"].items():
        lines.append(
            f"  {label}: cardinality={info['cardinality']} missing_or_null={info['missing_or_null']} present={info['present_count']}"
        )
    if report["warnings"]:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in report["warnings"])
    else:
        lines.append("warnings: none")
    return "\n".join(lines)


def format_split_diagnostics(report: dict[str, Any]) -> str:
    lines = [
        "Split diagnostics",
        f"dataset: {report['dataset_path']}",
        f"splits: {report['split_path']}",
        f"dataset rows: {report['dataset_row_count']}",
    ]
    for strategy in report["strategies"]:
        counts = ", ".join(f"{name}={count}" for name, count in sorted(strategy["counts"].items()))
        lines.append(f"strategy {strategy['strategy']}: {counts}")
        for field, overlap in strategy["group_overlap"].items():
            lines.append(f"  {field} overlap: {len(overlap)}")
    if report["warnings"]:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in report["warnings"])
    else:
        lines.append("warnings: none")
    return "\n".join(lines)
