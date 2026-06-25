from __future__ import annotations

from collections import defaultdict
import random
from typing import Any, Iterable


def lemma_heldout_split(records: Iterable[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record.get("lemma", record["id"])].append(dict(record))

    split_names = ["train", "dev", "test"]
    split_rows: list[dict[str, Any]] = []
    lemma_to_split = {}
    for index, lemma in enumerate(sorted(grouped)):
        split = split_names[index % len(split_names)]
        lemma_to_split[lemma] = split
        for row in grouped[lemma]:
            row["split"] = split
            split_rows.append(row)

    counts = {name: 0 for name in split_names}
    for row in split_rows:
        counts[row["split"]] += 1

    metadata = {
        "strategy": "lemma_round_robin_heldout",
        "unit": "lemma",
        "toy": True,
        "counts": counts,
        "lemma_to_split": lemma_to_split,
        "not_research_output": True,
    }
    return split_rows, metadata


def heldout_split(
    records: Iterable[dict[str, Any]],
    *,
    strategy: str,
    test_fraction: float = 0.2,
    seed: int = 42,
) -> dict[str, Any]:
    if strategy not in {"lemma_heldout", "root_heldout"}:
        raise ValueError(f"unsupported split strategy: {strategy}")

    unit = "lemma" if strategy == "lemma_heldout" else "root"
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record.get(unit) or record["id"])].append(dict(record))

    units = sorted(grouped)
    rng = random.Random(seed)
    rng.shuffle(units)
    test_count = max(1, round(len(units) * test_fraction)) if units else 0
    test_units = set(units[:test_count])

    assignments = {value: ("test" if value in test_units else "train") for value in sorted(grouped)}
    counts = {"train": 0, "test": 0}
    rows = []
    for value in sorted(grouped):
        split = assignments[value]
        for record in grouped[value]:
            row = dict(record)
            row[f"{strategy}_split"] = split
            rows.append(row)
            counts[split] += 1

    return {
        "strategy": strategy,
        "unit": unit,
        "seed": seed,
        "test_fraction": test_fraction,
        "counts": counts,
        "assignments": assignments,
        "rows": rows,
        "char_baseline_metadata": {
            "status": "placeholder",
            "notes": "Sarf v0.3 records where character-baseline metadata belongs; it does not run baselines.",
        },
        "not_research_output": True,
    }
