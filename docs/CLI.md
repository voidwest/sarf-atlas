# Sarf CLI

Sarf v0.2 keeps the v0.1 scaffolding commands and adds stable project,
artifact-import, and run-summary entry points.

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

`sarf example-workflow` writes the toy scaffold into that layout.

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

## v0.1 Scaffolding Commands

These lower-level commands remain available:

- `sarf toy-dataset`
- `sarf make-prompts`
- `sarf split-metadata`
- `sarf ember-config`
- `sarf validate-artifact`
- `sarf backends list`
- `sarf backend llama-cpp doctor`
- `sarf backend ember doctor`

