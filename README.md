# Sarf Atlas

Sarf Atlas is a backend-agnostic workflow framework for Arabic morphology
probing experiments. It organizes datasets, prompts, splits, diagnostics,
backend artifact manifests, baseline comparisons, and report scaffolds.

```text
Sarf organizes.
Backends extract.
Auditors compare.
```

Current package version: `1.0.0`.
Latest previously verified PyPI release: `sarf-atlas==0.4.0`.

## What Sarf Is

- A CLI for preparing Arabic morphology probing workflows.
- A small schema layer for morphology rows, split metadata, diagnostics, and
  imported backend artifact manifests.
- A backend-neutral adapter surface for Ember, llama.cpp-derived files,
  HF/Transformers outputs, or other precomputed artifacts.
- A place to run lightweight standard-library baselines such as majority and
  character n-gram comparisons.

## What Sarf Is Not

- It is not a model inference engine.
- It does not train probes in the base package.
- It does not extract hidden states by itself.
- It does not vendor Ember, llama.cpp, Transformers, or model weights.
- It does not claim Paper 1 reproduction from toy or mock artifacts.

## Quickstart

Install from PyPI once the target release is published:

```bash
pip install sarf-atlas
```

For local development:

```bash
python -m pip install -e .
```

Create a project layout:

```bash
sarf init --out-dir /tmp/sarf-demo --name demo
```

Generate a self-contained toy workflow:

```bash
sarf example-workflow --out-dir /tmp/sarf-example
sarf summarize-run --manifest /tmp/sarf-example/artifacts/imported/sarf_artifact_manifest.placeholder.json
```

When working from a source checkout, run a tiny paper-style workflow:

```bash
sarf validate-dataset examples/paper_style/tiny_morphology.jsonl
sarf make-experiment examples/paper_style/experiment.toml --out /tmp/sarf-demo/run
sarf validate-labels examples/paper_style/experiment.toml --out /tmp/sarf-demo/labels.json
sarf summarize-splits examples/paper_style/tiny_morphology.jsonl /tmp/sarf-demo/run/split_metadata.json --out /tmp/sarf-demo/splits.json
sarf make-baselines examples/paper_style/experiment.toml --out /tmp/sarf-demo/baselines
sarf make-probe-config examples/paper_style/experiment.toml --out /tmp/sarf-demo/probe_config.toml
sarf report /tmp/sarf-demo/run --out /tmp/sarf-demo/report.md
```

Run the fuller mock-backed Paper 1-style example:

```bash
cat examples/paper1_reproduction/README.md
```

That example exercises validation, prompt generation, split diagnostics,
tokenization diagnostics, artifact import, probe config generation, baseline
comparison, and report output with deterministic toy data.

## Stable CLI Surface

The 1.0 command contract classifies the public commands in
`docs/command_contract.md`.

Stable-track commands include:

- `sarf init`
- `sarf example-workflow`
- `sarf validate-dataset`
- `sarf make-prompts`
- `sarf make-splits`
- `sarf make-experiment`
- `sarf import-artifacts`
- `sarf summarize-run`
- `sarf validate-labels`
- `sarf summarize-splits`
- `sarf make-probe-config`
- `sarf make-baselines`
- `sarf run-baseline`
- `sarf summarize-baseline`
- `sarf tokenization-diagnostics`
- `sarf report`

Backend doctor commands are intentionally marked experimental because they
depend on optional local tools.

## Schemas

The schema v1 contract is documented in `docs/artifact_schema_guide.md`.

Stable contracts:

- Artifact manifest schema v1.
- Dataset row schema v1.
- Split metadata schema v1.
- Tokenization diagnostics schema v1.
- Baseline artifact schema v1.

Important JSON outputs include numeric `schema_version` fields. Existing
string `schema` identifiers remain for compatibility where they already
existed.

## Guides

- CLI contract: `docs/command_contract.md`
- Schema guide: `docs/artifact_schema_guide.md`
- Paper-style workflow: `docs/paper_style_workflow.md`
- Backend guide: `docs/backend_guide.md`
- Diagnostics guide: `docs/evaluation_diagnostics.md`
- Examples index: `docs/examples.md`
- Release checklist: `docs/release_checklist.md`
- Changelog: `CHANGELOG.md`

## Optional Backends

Sarf can inspect optional backend availability:

```bash
sarf backends list
sarf backend llama-cpp doctor
sarf backend ember doctor
```

These checks are diagnostic only. Base Sarf stays lightweight and can still
organize workflows and import file-based artifacts when no local backend is
installed.

## Citation

Use `CITATION.cff` for citation metadata. Sarf Atlas is released under the MIT
License; see `LICENSE`.
