from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


REQUIRED_FIELDS = ["id", "surface", "lemma", "root", "pos", "abstract_pattern", "concrete_pattern"]
OPTIONAL_LABEL_FIELDS = ["gender", "number"]


def normalize_record(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    if "surface" not in normalized and "word" in normalized:
        normalized["surface"] = normalized["word"]
    if "word" not in normalized and "surface" in normalized:
        normalized["word"] = normalized["surface"]
    if "abstract_pattern" not in normalized and "pattern" in normalized:
        normalized["abstract_pattern"] = normalized["pattern"]
    if "pattern" not in normalized and "abstract_pattern" in normalized:
        normalized["pattern"] = normalized["abstract_pattern"]
    if "concrete_pattern" not in normalized and "surface" in normalized:
        normalized["concrete_pattern"] = normalized["surface"]
    if "features" not in normalized or normalized["features"] is None:
        normalized["features"] = {}
    return normalized


def validate_dataset_rows(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    row_reports = []
    optional_null_counts: Counter[str] = Counter()
    row_count = 0

    for row_count, raw_row in enumerate(rows, start=1):
        row = normalize_record(raw_row)
        missing = [field for field in REQUIRED_FIELDS if row.get(field) in (None, "")]
        for field in OPTIONAL_LABEL_FIELDS:
            if row.get(field) in (None, ""):
                optional_null_counts[field] += 1
        if row.get("features") is not None and not isinstance(row.get("features"), dict):
            missing.append("features<object>")
        row_reports.append(
            {
                "line": row_count,
                "id": row.get("id"),
                "missing": missing,
                "passed": not missing,
            }
        )

    failing = [row for row in row_reports if not row["passed"]]
    return {
        "schema": "sarf_morphology_dataset_v0_3",
        "passed": not failing and row_count > 0,
        "row_count": row_count,
        "failed_row_count": len(failing),
        "required_fields": REQUIRED_FIELDS,
        "optional_label_fields": OPTIONAL_LABEL_FIELDS,
        "optional_null_counts": dict(optional_null_counts),
        "rows": row_reports,
    }

