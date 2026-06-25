from __future__ import annotations

from typing import Any, Iterable

from .schemas import PromptRecord


def make_prompts(
    records: Iterable[dict[str, Any]],
    template: str,
    *,
    label_targets: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    rows = []
    targets = list(label_targets or [])
    for record in records:
        prompt = template.format(**record)
        row = PromptRecord(
            id=record["id"],
            word=record.get("word", record.get("surface", "")),
            prompt=prompt,
            target_pos=record.get("pos", ""),
            target_root=record.get("root", ""),
            target_pattern=record.get("pattern", record.get("abstract_pattern", "")),
            source_lemma=record.get("lemma", ""),
        ).to_dict()
        row["surface"] = record.get("surface", row["word"])
        if targets:
            row["labels"] = {target: record.get(target) for target in targets}
        rows.append(row)
    return rows
