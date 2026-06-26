from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from .experiment import dataset_path_from_config, read_experiment_config
from .io import read_jsonl, write_json


DIACRITIC_RANGES = (
    (0x0610, 0x061A),
    (0x064B, 0x065F),
    (0x0670, 0x0670),
    (0x06D6, 0x06ED),
)
ALEF_VARIANTS = {"أ", "إ", "آ", "ٱ"}
MORPH_BOUNDARY_CHARS = {"و", "ف", "ب", "ك", "ل", "س"}
TOKENIZATION_DIAGNOSTICS_SCHEMA_VERSION = 1


def _is_diacritic(char: str) -> bool:
    codepoint = ord(char)
    return any(start <= codepoint <= end for start, end in DIACRITIC_RANGES)


def _load_rows(path: str | Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source = Path(path)
    if source.suffix.lower() == ".toml":
        config = read_experiment_config(source)
        dataset = dataset_path_from_config(config, config_path=source)
        return read_jsonl(dataset), {"kind": "experiment", "path": str(source), "dataset_path": str(dataset)}
    return read_jsonl(source), {"kind": "dataset", "path": str(source), "dataset_path": str(source)}


def _load_artifact_counts(path: str | Path) -> dict[str, int]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    samples = payload.get("samples", [])
    counts: dict[str, int] = {}
    for sample in samples:
        if not isinstance(sample, dict) or sample.get("id") is None:
            continue
        if sample.get("token_count") is not None:
            counts[str(sample["id"])] = int(sample["token_count"])
        elif isinstance(sample.get("token_ids"), list):
            counts[str(sample["id"])] = len(sample["token_ids"])
        elif isinstance(sample.get("tokens"), list):
            counts[str(sample["id"])] = len(sample["tokens"])
    return counts


def _mean(values: list[int]) -> float | None:
    return sum(values) / len(values) if values else None


def _artifact_paths(value: str | Path | list[str | Path] | tuple[str | Path, ...] | None) -> list[str | Path]:
    if value is None:
        return []
    if isinstance(value, (str, Path)):
        return [value]
    return list(value)


def tokenization_diagnostics(
    input_path: str | Path,
    *,
    tokenization_artifact: str | Path | list[str | Path] | tuple[str | Path, ...] | None = None,
) -> dict[str, Any]:
    rows, source = _load_rows(input_path)
    artifact_paths = _artifact_paths(tokenization_artifact)
    artifacts = [
        {
            "path": str(path),
            "counts": _load_artifact_counts(path),
        }
        for path in artifact_paths
    ]
    primary_artifact = artifacts[0] if artifacts else None
    primary_counts = primary_artifact["counts"] if primary_artifact else {}
    samples = []
    warnings = []
    char_counts = []
    whitespace_counts = []
    primary_artifact_values = []
    artifact_values_by_path: dict[str, list[int]] = {artifact["path"]: [] for artifact in artifacts}
    concern_counts: Counter[str] = Counter()

    for row in rows:
        row_id = str(row.get("id", ""))
        surface = str(row.get("surface", ""))
        chars = list(surface)
        nonspace_chars = [char for char in chars if not char.isspace()]
        whitespace_tokens = surface.split()
        concerns = []
        if any(_is_diacritic(char) for char in chars):
            concerns.append("contains_diacritics")
        if "ـ" in surface:
            concerns.append("contains_tatweel")
        if any(char in ALEF_VARIANTS for char in chars):
            concerns.append("contains_alef_variant")
        if "ة" in surface:
            concerns.append("contains_ta_marbuta")
        if surface and surface[0] in MORPH_BOUNDARY_CHARS and len(surface) > 1:
            concerns.append("possible_prefix_boundary")
        if any(char.isdigit() for char in chars):
            concerns.append("contains_digit")
        concern_counts.update(concerns)

        artifact_counts = {
            artifact["path"]: artifact["counts"].get(row_id)
            for artifact in artifacts
            if artifact["counts"].get(row_id) is not None
        }
        artifact_count = primary_counts.get(row_id)
        if artifact_count is not None:
            primary_artifact_values.append(artifact_count)
        for artifact_path, count in artifact_counts.items():
            artifact_values_by_path[artifact_path].append(count)
        char_count = len(nonspace_chars)
        whitespace_count = len(whitespace_tokens)
        char_counts.append(char_count)
        whitespace_counts.append(whitespace_count)
        sample = {
            "id": row_id,
            "surface": surface,
            "unicode_char_count": char_count,
            "whitespace_token_count": whitespace_count,
            "artifact_token_count": artifact_count,
            "artifact_token_counts": artifact_counts,
            "artifact_vs_char_delta": artifact_count - char_count if artifact_count is not None else None,
            "concerns": concerns,
        }
        samples.append(sample)

    artifact_comparisons = []
    for artifact in artifacts:
        path = artifact["path"]
        counts = artifact["counts"]
        values = artifact_values_by_path[path]
        artifact_comparisons.append(
            {
                "path": path,
                "matched_rows": len(values),
                "mean_token_count": _mean(values),
                "mean_delta_vs_unicode_chars": (
                    sum(counts[str(row.get("id", ""))] - len([char for char in str(row.get("surface", "")) if not char.isspace()])
                        for row in rows
                        if str(row.get("id", "")) in counts)
                    / len(values)
                    if values
                    else None
                ),
            }
        )
        if len(counts) != len(rows):
            warnings.append(f"tokenization artifact {path} has counts for {len(counts)} rows but dataset has {len(rows)} rows")
    if concern_counts:
        warnings.append(
            "Arabic normalization or token-boundary concerns present: "
            + ", ".join(f"{name}={count}" for name, count in sorted(concern_counts.items()))
        )
    if not artifacts:
        warnings.append("no backend tokenization artifact supplied; diagnostics use built-in surface heuristics only")

    return {
        "schema": "sarf_tokenization_diagnostics_v0_7",
        "schema_version": TOKENIZATION_DIAGNOSTICS_SCHEMA_VERSION,
        "source": source,
        "row_count": len(rows),
        "tokenization_artifact": primary_artifact["path"] if primary_artifact else None,
        "tokenization_artifacts": [artifact["path"] for artifact in artifacts],
        "backend_checks": {
            "required": False,
            "checked": False,
            "notes": "Backend-specific tokenizer availability remains optional; pass an artifact to compare emitted token counts.",
        },
        "summary": {
            "mean_unicode_char_count": _mean(char_counts),
            "mean_whitespace_token_count": _mean(whitespace_counts),
            "mean_artifact_token_count": _mean(primary_artifact_values),
            "concern_counts": dict(sorted(concern_counts.items())),
        },
        "artifact_comparisons": artifact_comparisons,
        "samples": samples,
        "warnings": warnings,
        "not_research_output": True,
    }


def format_tokenization_diagnostics(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "Tokenization diagnostics",
        f"source: {report['source']['path']}",
        f"rows: {report['row_count']}",
        f"artifact: {report['tokenization_artifact'] or 'none'}",
        f"mean unicode chars: {summary['mean_unicode_char_count']}",
        f"mean whitespace tokens: {summary['mean_whitespace_token_count']}",
        f"mean artifact tokens: {summary['mean_artifact_token_count']}",
        "concerns:",
    ]
    if summary["concern_counts"]:
        lines.extend(f"  {name}: {count}" for name, count in summary["concern_counts"].items())
    else:
        lines.append("  none")
    if report["warnings"]:
        lines.append("warnings:")
        lines.extend(f"  - {warning}" for warning in report["warnings"])
    else:
        lines.append("warnings: none")
    return "\n".join(lines)


def write_tokenization_diagnostics(
    input_path: str | Path,
    out_path: str | Path,
    *,
    tokenization_artifact: str | Path | None = None,
) -> dict[str, Any]:
    report = tokenization_diagnostics(input_path, tokenization_artifact=tokenization_artifact)
    write_json(out_path, report)
    return report
