from __future__ import annotations

from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
from typing import Any
import tomllib

from .experiment import (
    dataset_path_from_config,
    label_targets_from_config,
    read_experiment_config,
)
from .io import read_jsonl, write_json


BASELINE_CONFIG_SCHEMA = "sarf_baseline_config_v0_5"
BASELINE_RESULTS_SCHEMA = "sarf_baseline_results_v0_5"
BASELINE_SUMMARY_SCHEMA = "sarf_baseline_summary_v0_5"
BASELINE_ARTIFACT_SCHEMA_VERSION = 1

SUPPORTED_BASELINES = {
    "char_ngram",
    "char_ngram_placeholder",
    "majority",
    "majority_placeholder",
}


def read_baseline_config(path: str | Path) -> dict[str, Any]:
    config = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    schema = config.get("schema")
    if schema and schema != BASELINE_CONFIG_SCHEMA:
        raise ValueError(f"unsupported baseline config schema '{schema}'. Expected {BASELINE_CONFIG_SCHEMA}")
    baseline = str(config.get("baseline", ""))
    if baseline not in SUPPORTED_BASELINES:
        raise ValueError(
            f"unsupported baseline '{baseline}'. Supported baselines: {', '.join(sorted(SUPPORTED_BASELINES))}"
        )
    if not config.get("experiment"):
        raise ValueError("baseline config requires an experiment path")
    return config


def baseline_dependency_status(config: dict[str, Any]) -> dict[str, Any]:
    dependencies = config.get("dependencies", {})
    modules = dependencies.get("modules", []) if isinstance(dependencies, dict) else []
    optional_modules = [str(module) for module in modules]
    missing_modules = [module for module in optional_modules if importlib.util.find_spec(module) is None]
    return {
        "required": ["python_standard_library"],
        "optional_modules": optional_modules,
        "missing_modules": missing_modules,
        "available": not missing_modules,
        "install_hint": (
            "Install the missing optional Python modules in your environment, or remove them from "
            "[dependencies].modules if this baseline config does not need them."
            if missing_modules
            else None
        ),
    }


def require_baseline_dependencies(config: dict[str, Any]) -> dict[str, Any]:
    status = baseline_dependency_status(config)
    if not status["available"]:
        missing = ", ".join(status["missing_modules"])
        raise RuntimeError(f"missing optional baseline dependencies: {missing}. {status['install_hint']}")
    return status


def _resolve_experiment_path(baseline_config_path: str | Path, config: dict[str, Any]) -> Path:
    experiment_path = Path(str(config["experiment"]))
    if experiment_path.is_absolute():
        return experiment_path
    if experiment_path.exists():
        return experiment_path
    experiment_path = Path(baseline_config_path).parent / experiment_path
    return experiment_path


def _ngrams(text: str, minimum: int, maximum: int) -> set[str]:
    chars = list(text)
    values: set[str] = set()
    for size in range(minimum, maximum + 1):
        if size <= 0:
            continue
        for index in range(0, max(0, len(chars) - size + 1)):
            values.add("".join(chars[index : index + size]))
    return values or {text}


def _majority_label(rows: list[dict[str, Any]], label: str) -> str | None:
    counts = Counter(str(row[label]) for row in rows if row.get(label) not in {None, ""})
    if not counts:
        return None
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def _predict_majority(train_rows: list[dict[str, Any]], label: str, _: dict[str, Any], __: dict[str, Any]) -> str | None:
    return _majority_label(train_rows, label)


def _predict_char_ngram(
    train_rows: list[dict[str, Any]],
    label: str,
    test_row: dict[str, Any],
    options: dict[str, Any],
) -> str | None:
    candidates = [row for row in train_rows if row.get(label) not in {None, ""}]
    if not candidates:
        return None

    minimum = int(options.get("ngram_min", 1))
    maximum = int(options.get("ngram_max", 5))
    test_features = _ngrams(str(test_row.get("surface", "")), minimum, maximum)
    scored = []
    for row in candidates:
        train_features = _ngrams(str(row.get("surface", "")), minimum, maximum)
        union = test_features | train_features
        score = len(test_features & train_features) / len(union) if union else 0.0
        scored.append((score, str(row[label]), str(row.get("id", ""))))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return scored[0][1]


def _rows_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        row_id = row.get("id")
        if row_id is not None:
            result[str(row_id)] = row
    return result


def _strategy_rows(strategy: dict[str, Any], dataset_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dataset_by_id = _rows_by_id(dataset_rows)
    rows = []
    split_key = f"{strategy['strategy']}_split"
    for row in strategy.get("rows", []):
        merged = dict(dataset_by_id.get(str(row.get("id")), {}))
        merged.update(row)
        if "split" not in merged and split_key in merged:
            merged["split"] = merged[split_key]
        rows.append(merged)
    return rows


def run_baseline(
    baseline_config_path: str | Path,
    splits_path: str | Path,
    out_path: str | Path,
) -> dict[str, Any]:
    baseline_config = read_baseline_config(baseline_config_path)
    dependency_status = require_baseline_dependencies(baseline_config)
    experiment_path = _resolve_experiment_path(baseline_config_path, baseline_config)
    experiment_config = read_experiment_config(experiment_path)
    dataset_rows = read_jsonl(dataset_path_from_config(experiment_config, config_path=experiment_path))
    split_metadata = json.loads(Path(splits_path).read_text(encoding="utf-8"))

    baseline_name = str(baseline_config["baseline"]).replace("_placeholder", "")
    targets = [str(target) for target in baseline_config.get("target_labels", [])] or label_targets_from_config(experiment_config)
    features = baseline_config.get("features", {})
    feature_options = features if isinstance(features, dict) else {}
    predictor = _predict_char_ngram if baseline_name == "char_ngram" else _predict_majority

    strategy_results = []
    warnings = []
    for strategy in split_metadata.get("strategies", []):
        rows = _strategy_rows(strategy, dataset_rows)
        train_rows = [row for row in rows if row.get("split") == "train"]
        test_rows = [row for row in rows if row.get("split") == "test"]
        label_results = {}
        predictions = defaultdict(list)
        for label in targets:
            correct = 0
            evaluated = 0
            missing_gold = 0
            missing_prediction = 0
            train_values = {str(row[label]) for row in train_rows if row.get(label) not in {None, ""}}
            test_values = {str(row[label]) for row in test_rows if row.get(label) not in {None, ""}}
            unseen_values = sorted(test_values - train_values)
            if unseen_values:
                warnings.append(
                    f"{strategy.get('strategy')} label '{label}' has test values unseen in train: {', '.join(unseen_values)}"
                )
            for row in test_rows:
                gold = row.get(label)
                if gold in {None, ""}:
                    missing_gold += 1
                    continue
                prediction = predictor(train_rows, label, row, feature_options)
                if prediction is None:
                    missing_prediction += 1
                    continue
                evaluated += 1
                correct += int(str(gold) == prediction)
                predictions[label].append(
                    {
                        "id": row.get("id"),
                        "gold": str(gold),
                        "prediction": prediction,
                    }
                )
            label_results[label] = {
                "correct": correct,
                "evaluated": evaluated,
                "accuracy": correct / evaluated if evaluated else None,
                "missing_gold": missing_gold,
                "missing_prediction": missing_prediction,
                "train_cardinality": len(train_values),
                "test_cardinality": len(test_values),
                "unseen_test_values": unseen_values,
            }
        strategy_results.append(
            {
                "strategy": strategy.get("strategy"),
                "train_count": len(train_rows),
                "test_count": len(test_rows),
                "labels": label_results,
                "predictions": dict(predictions),
            }
        )

    result = {
        "schema": BASELINE_RESULTS_SCHEMA,
        "schema_version": BASELINE_ARTIFACT_SCHEMA_VERSION,
        "baseline": baseline_name,
        "baseline_config": str(baseline_config_path),
        "experiment": str(experiment_path),
        "splits": str(splits_path),
        "dependency_status": dependency_status,
        "target_labels": targets,
        "strategies": strategy_results,
        "warnings": warnings,
        "not_probe_training": True,
        "not_model_inference": True,
    }
    write_json(out_path, result)
    return result


def summarize_baseline(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    labels: dict[str, list[float]] = defaultdict(list)
    for strategy in payload.get("strategies", []):
        for label, metrics in strategy.get("labels", {}).items():
            accuracy = metrics.get("accuracy")
            if accuracy is not None:
                labels[label].append(float(accuracy))
    return {
        "schema": BASELINE_SUMMARY_SCHEMA,
        "schema_version": BASELINE_ARTIFACT_SCHEMA_VERSION,
        "baseline": payload.get("baseline"),
        "dependency_status": payload.get("dependency_status", {}),
        "strategy_count": len(payload.get("strategies", [])),
        "target_labels": payload.get("target_labels", []),
        "mean_accuracy_by_label": {
            label: sum(values) / len(values) for label, values in sorted(labels.items()) if values
        },
        "warning_count": len(payload.get("warnings", [])),
        "warnings": payload.get("warnings", []),
    }
