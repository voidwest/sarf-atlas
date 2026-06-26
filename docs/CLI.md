# Sarf CLI

Sarf keeps the workflow skeleton and adds evaluation-preparation commands
for label diagnostics, leakage-aware split summaries, probe config scaffolds,
baseline config scaffolds, optional lightweight baseline runners, and Markdown
reports.

For the v0.8 contract-freeze decision table, see
`docs/command_contract.md`. For JSON artifact examples and schema v1 notes, see
`docs/artifact_schema_guide.md`.

## Paper-Style Commands

```bash
sarf validate-dataset data/morphology.jsonl
sarf validate-labels experiment.toml --out diagnostics/labels.json

sarf make-prompts experiment.toml \
  --out prompts/morph_prompts.jsonl

sarf make-splits experiment.toml \
  --out splits/lemma_root_heldout.json

sarf summarize-splits data/morphology.jsonl splits/lemma_root_heldout.json \
  --out diagnostics/splits.json

sarf tokenization-diagnostics experiment.toml \
  --tokenization-artifact artifacts/imported/tokenization.json \
  --tokenization-artifact artifacts/imported/alternate-tokenization.json \
  --out diagnostics/tokenization.json

sarf make-probe-config experiment.toml \
  --artifact-manifest artifacts/imported/run.manifest.json \
  --out configs/probe_config.toml

sarf make-baselines experiment.toml \
  --out configs/baselines

sarf run-baseline \
  --config configs/baselines/char_ngram.toml \
  --splits splits/lemma_root_heldout.json \
  --out artifacts/baselines/char_ngram.results.json

sarf summarize-baseline artifacts/baselines/char_ngram.results.json \
  --out reports/char_ngram.summary.json

sarf make-experiment experiment.toml \
  --out runs/paper_style/

sarf report runs/paper_style/ \
  --out reports/summary.md
```

These commands prepare the shape of an evaluation workflow. Base Sarf still
does not run models, extract hidden states, train probes, or claim paper
reproduction. The baseline runner is a lightweight standard-library path for
majority and character n-gram baselines only.

## Baseline Artifact Contract

`sarf run-baseline` consumes a TOML config from `sarf make-baselines` and split
metadata from `sarf make-splits` or `sarf make-experiment`. It writes a JSON
artifact with schema `sarf_baseline_results_v0_5`:

- `baseline`: `majority` or `char_ngram`.
- `target_labels`: labels evaluated from the experiment.
- `dependency_status`: explicit marker that the bundled runner requires only
  the Python standard library unless the config declares optional modules.
- `strategies`: per-split train/test counts, per-label accuracy, and
  predictions.
- `warnings`: labels whose test values were unseen in train.
- `not_probe_training` and `not_model_inference`: explicit scope markers.

`sarf summarize-baseline` writes a compact
`sarf_baseline_summary_v0_5` JSON view with mean accuracy by label and warning
counts. No heavyweight ML dependencies are installed or required.

Generated baseline configs include:

```toml
[dependencies]
modules = []
```

Leave this list empty for bundled `majority` and `char_ngram` runs. If a local
baseline config declares extra Python modules, `sarf run-baseline` checks them
before reading splits or writing output and fails with an actionable missing
dependency message.

A tiny generated example lives in `examples/baseline_runner/` and includes a
`char_ngram.results.json` artifact plus `char_ngram.summary.json`.

## Tokenization Diagnostics

`sarf tokenization-diagnostics` runs on an experiment TOML or morphology JSONL.
Without backend artifacts, it reports built-in surface heuristics: Unicode
character counts, whitespace token counts, and Arabic normalization or
token-boundary concerns such as diacritics, tatweel, alef variants, ta marbuta,
digits, and common prefix-boundary characters.

With one or more `--tokenization-artifact` values, it also reads
backend-emitted token counts from JSON artifacts shaped like:

```json
{
  "samples": [
    {"id": "sample-0001", "token_count": 2}
  ]
}
```

The output schema is `sarf_tokenization_diagnostics_v0_7`. Backend-specific
tokenizer availability checks remain optional; the command compares supplied
artifacts in `artifact_comparisons` and otherwise records that only built-in
heuristics were used. For compatibility, `tokenization_artifact` and
`summary.mean_artifact_token_count` refer to the first supplied artifact.

## Paper 1-Style Example

`examples/paper1_reproduction/README.md` documents a tiny end-to-end
demonstration path for Paper 1 review. It uses bundled morphology rows and mock
backend artifacts to exercise validation, prompt generation, split diagnostics,
artifact import, probe config generation, baseline comparison, and report
output. It is a workflow example, not a full Paper 1 reproduction claim.

## Project Commands

```bash
sarf init --out-dir my-sarf-project --name my-sarf-project
sarf example-workflow --out-dir /tmp/sarf-atlas-example
```

`sarf init` creates a clean project layout:

```text
data/raw/
data/processed/
prompts/
splits/
configs/
artifacts/imported/
runs/
reports/
docs/
sarf.project.json
README.md
```

`sarf example-workflow` writes the toy scaffold into that layout. For
diagnostic guidance, see `docs/evaluation_diagnostics.md`; for historical v0.3
Paper-style examples, see `docs/v0_3_paper_workflow.md`.

## Artifact Commands

Import an Ember run:

```bash
sarf import-artifacts --from ember --run-dir runs/ember-run --out artifacts/imported/ember-run.manifest.json
```

Import precomputed files:

```bash
sarf import-artifacts \
  --from files \
  --run-id local-logits-run \
  --prompts-path prompts/toy_prompts.jsonl \
  --logits-path runs/local-logits/logits.npy \
  --report-path runs/local-logits/report.json \
  --out artifacts/imported/local-logits-run.manifest.json
```

Summarize and validate a manifest:

```bash
sarf summarize-run --manifest artifacts/imported/local-logits-run.manifest.json
sarf summarize-run --manifest artifacts/imported/local-logits-run.manifest.json --out reports/local-logits-run.summary.json
```

Compatibility commands remain available:

- `sarf import-ember`
- `sarf import-files`
- `sarf validate-manifest`

## Backend Capability Matrix

| Backend/source | Detection command | Tokenization | Logits | Hidden states | Sarf artifact import | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Ember | `sarf backend ember doctor` | yes, when installed | yes, when configured | yes, when configured | `sarf import-artifacts --from ember` | Optional backend; Sarf does not vendor Ember. |
| llama.cpp default binaries | `sarf backend llama-cpp doctor` | yes, when tokenizer binary is available | yes, when CLI/simple path is available | no | via files only | Default llama.cpp does not emit Sarf-compatible hidden-state artifacts. |
| Precomputed files | none | if provided | if provided | if provided | `sarf import-artifacts --from files` | Useful for HF/Transformers, patched llama.cpp, or external pipelines. |
| Base Sarf | `sarf backends list` | no extraction | no extraction | no extraction | yes | Base package organizes workflows and validates/imports manifests. |

## Compatibility Commands

These lower-level commands remain available:

- `sarf toy-dataset`
- `sarf split-metadata`
- `sarf ember-config`
- `sarf validate-artifact`
- `sarf backends list`
- `sarf backend llama-cpp doctor`
- `sarf backend ember doctor`
