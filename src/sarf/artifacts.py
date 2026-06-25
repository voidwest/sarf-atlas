from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


SARF_ARTIFACT_CONTRACT_VERSION = 1
ARTIFACT_PATH_FIELDS = [
    "prompts_path",
    "tokenization_path",
    "positions_path",
    "logits_path",
    "hidden_states_path",
    "report_path",
]


@dataclass(frozen=True)
class BackendDescriptor:
    name: str
    adapter: str
    version: str | None = None
    source_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SarfArtifactManifest:
    run_id: str
    backend: BackendDescriptor
    prompts_path: str
    tokenization_path: str | None = None
    positions_path: str | None = None
    logits_path: str | None = None
    hidden_states_path: str | None = None
    report_path: str | None = None
    not_research_output: bool = True

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["schema_version"] = SARF_ARTIFACT_CONTRACT_VERSION
        return payload


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    required = ["schema_version", "run_id", "backend", "prompts_path"]
    missing = [key for key in required if key not in manifest]
    backend = manifest.get("backend")
    if not isinstance(backend, dict):
        missing.append("backend.name")
    else:
        for key in ["name", "adapter"]:
            if key not in backend:
                missing.append(f"backend.{key}")
    artifact_paths = {}
    for key in ARTIFACT_PATH_FIELDS:
        value = manifest.get(key)
        status = {
            "present": bool(value),
            "path": value,
            "exists": None,
            "placeholder": False,
        }
        if isinstance(value, str) and value:
            status["placeholder"] = value.startswith("<") or value.startswith("/path/to/")
            status["exists"] = Path(value).exists() if not status["placeholder"] else False
        artifact_paths[key] = status
    return {
        "passed": not missing,
        "missing": missing,
        "schema_version": manifest.get("schema_version"),
        "not_research_output": manifest.get("not_research_output"),
        "artifact_paths": artifact_paths,
    }
