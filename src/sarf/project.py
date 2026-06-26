from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import write_json


PROJECT_SCHEMA_VERSION = 1


def init_project(out_dir: str | Path, *, name: str = "sarf-project", force: bool = False) -> dict[str, Any]:
    root = Path(out_dir)
    existing_entries = list(root.iterdir()) if root.exists() else []
    if existing_entries and not force:
        raise ValueError(f"{root} is not empty; pass --force to add Sarf layout files")

    directories = [
        "data/raw",
        "data/processed",
        "prompts",
        "splits",
        "configs",
        "artifacts/imported",
        "runs",
        "reports",
        "docs",
    ]
    for directory in directories:
        (root / directory).mkdir(parents=True, exist_ok=True)

    project = {
        "schema_version": PROJECT_SCHEMA_VERSION,
        "name": name,
        "sarf_version": "1.0",
        "layout": {
            "data_raw": "data/raw",
            "data_processed": "data/processed",
            "prompts": "prompts",
            "splits": "splits",
            "configs": "configs",
            "artifacts": "artifacts/imported",
            "runs": "runs",
            "reports": "reports",
            "docs": "docs",
        },
        "commands": {
            "import_artifacts": "sarf import-artifacts --from files --run-id <run-id> --prompts-path prompts/<file>.jsonl --out artifacts/imported/<run-id>.manifest.json",
            "summarize_run": "sarf summarize-run --manifest artifacts/imported/<run-id>.manifest.json",
        },
        "not_research_output": True,
    }
    write_json(root / "sarf.project.json", project)

    readme = root / "README.md"
    if force or not readme.exists():
        readme.write_text(
            f"# {name}\n\n"
            "Sarf v1.0 project layout for Arabic morphology probing artifacts.\n\n"
            "- Put source datasets in `data/raw/`.\n"
            "- Write normalized records to `data/processed/`.\n"
            "- Store rendered prompt JSONL in `prompts/`.\n"
            "- Keep backend configs in `configs/`.\n"
            "- Import backend outputs into `artifacts/imported/`.\n"
            "- Write summaries and analysis reports to `reports/`.\n",
            encoding="utf-8",
        )

    return project
