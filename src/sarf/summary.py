from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import validate_manifest


ARTIFACT_FIELDS = [
    "prompts_path",
    "tokenization_path",
    "positions_path",
    "logits_path",
    "hidden_states_path",
    "report_path",
]


def summarize_manifest(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    backend = manifest.get("backend") if isinstance(manifest.get("backend"), dict) else {}
    artifacts = {
        field: {
            "present": bool(manifest.get(field)),
            "path": manifest.get(field),
        }
        for field in ARTIFACT_FIELDS
    }
    return {
        "manifest_path": str(path),
        "run_id": manifest.get("run_id"),
        "schema_version": manifest.get("schema_version"),
        "backend": {
            "name": backend.get("name"),
            "adapter": backend.get("adapter"),
            "version": backend.get("version"),
        },
        "artifacts": artifacts,
        "capabilities": {
            "has_tokenization": artifacts["tokenization_path"]["present"],
            "has_logits": artifacts["logits_path"]["present"],
            "has_hidden_states": artifacts["hidden_states_path"]["present"],
            "has_report": artifacts["report_path"]["present"],
        },
        "validation": validate_manifest(manifest),
        "not_research_output": manifest.get("not_research_output"),
    }

