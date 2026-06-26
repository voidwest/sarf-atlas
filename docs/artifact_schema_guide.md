# Sarf Schema Guide

Sarf Atlas 1.0 uses numeric `schema_version` fields for compatibility checks.
JSON outputs keep their historical string `schema` names where they already
existed.

## Artifact Manifest V1

Produced by `sarf import-artifacts`.

```json
{
  "schema_version": 1,
  "run_id": "paper1-style-demo",
  "backend": {
    "name": "files",
    "adapter": "sarf.backends.files",
    "version": null,
    "source_path": null
  },
  "prompts_path": "prompts.jsonl",
  "tokenization_path": "tokenization.json",
  "positions_path": "positions.json",
  "logits_path": null,
  "hidden_states_path": "hidden_states.json",
  "report_path": "report.json",
  "not_research_output": true
}
```

Required fields: `schema_version`, `run_id`, `backend.name`,
`backend.adapter`, and `prompts_path`. `schema_version` must be `1`; Sarf
manifest validation reports an error for unsupported manifest schema versions.

## Dataset Row V1

Consumed by `sarf validate-dataset`, `sarf make-prompts`, `sarf make-splits`,
and diagnostics commands.

```json
{
  "id": "sample-0001",
  "surface": "كتب",
  "lemma": "كتب",
  "root": "ك ت ب",
  "pos": "VERB",
  "abstract_pattern": "فعل",
  "concrete_pattern": "كتب",
  "gender": null,
  "number": null,
  "features": {
    "aspect": "perf"
  }
}
```

Required fields: `id`, `surface`, `lemma`, `root`, `pos`,
`abstract_pattern`, and `concrete_pattern`. `features` must be an object when
present. `gender` and `number` are optional labels and may be null or empty.

Validation reports use:

```json
{
  "schema": "sarf_morphology_dataset_v0_4",
  "schema_version": 1,
  "dataset_row_schema_version": 1,
  "passed": true,
  "row_count": 1,
  "failed_row_count": 0
}
```

## Split Metadata V1

Produced by `sarf make-splits`.

```json
{
  "schema": "sarf_split_metadata_v0_4",
  "schema_version": 1,
  "strategies": [
    {
      "schema_version": 1,
      "strategy": "lemma_heldout",
      "unit": "lemma",
      "seed": 42,
      "test_fraction": 0.25,
      "counts": {
        "train": 3,
        "test": 1
      },
      "assignments": {
        "كتب": "test"
      },
      "rows": [],
      "not_research_output": true
    }
  ],
  "seed": 42,
  "test_fraction": 0.25,
  "not_research_output": true
}
```

Stable strategy names: `lemma_heldout` and `root_heldout`.

## Tokenization Diagnostics V1

Produced by `sarf tokenization-diagnostics`.

```json
{
  "schema": "sarf_tokenization_diagnostics_v0_7",
  "schema_version": 1,
  "source": {
    "kind": "experiment",
    "path": "experiment.toml",
    "dataset_path": "tiny_morphology.jsonl"
  },
  "row_count": 4,
  "tokenization_artifact": "tokenization.json",
  "tokenization_artifacts": ["tokenization.json"],
  "backend_checks": {
    "required": false,
    "checked": false
  },
  "summary": {
    "mean_unicode_char_count": 4.25,
    "mean_whitespace_token_count": 1.0,
    "mean_artifact_token_count": 2.75,
    "concern_counts": {}
  },
  "artifact_comparisons": [
    {
      "path": "tokenization.json",
      "matched_rows": 4,
      "mean_token_count": 2.75,
      "mean_delta_vs_unicode_chars": -1.5
    }
  ],
  "samples": [],
  "warnings": [],
  "not_research_output": true
}
```

For backward compatibility, `tokenization_artifact` and
`summary.mean_artifact_token_count` refer to the first supplied artifact.

## Baseline Artifacts V1

Produced by `sarf run-baseline` and `sarf summarize-baseline`.

```json
{
  "schema": "sarf_baseline_results_v0_5",
  "schema_version": 1,
  "baseline": "char_ngram",
  "dependency_status": {
    "required": ["python_standard_library"],
    "optional_modules": [],
    "missing_modules": [],
    "available": true
  },
  "target_labels": ["pos"],
  "strategies": [],
  "warnings": [],
  "not_probe_training": true,
  "not_model_inference": true
}
```

Bundled stable baselines: `majority` and `char_ngram`.
