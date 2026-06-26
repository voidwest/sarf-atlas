# Backend Guide

Sarf is backend-agnostic. Base Sarf organizes workflow inputs and imports
artifacts; it does not extract hidden states, run model inference, compile
llama.cpp, or vendor Ember.

## Stable Import Path

Use `sarf import-artifacts` for new workflows.

```bash
sarf import-artifacts \
  --from files \
  --run-id local-run \
  --prompts-path prompts.jsonl \
  --tokenization-path tokenization.json \
  --positions-path positions.json \
  --hidden-states-path hidden_states.json \
  --report-path report.json \
  --out artifacts/imported/local-run.manifest.json
```

The output is a Sarf artifact manifest schema v1. Run:

```bash
sarf validate-manifest --manifest artifacts/imported/local-run.manifest.json
sarf summarize-run --manifest artifacts/imported/local-run.manifest.json
```

## Ember

Ember remains optional. Sarf can inspect whether a local Ember binary is
available:

```bash
sarf backend ember doctor
```

This command is experimental because Ember is external to base Sarf. New docs
should prefer `sarf import-artifacts --from ember` after an Ember run exists.

## llama.cpp

Sarf can inspect common llama.cpp binaries:

```bash
sarf backend llama-cpp doctor
```

Default llama.cpp builds can be useful for tokenization or logits workflows,
but they should not be assumed to emit Sarf-compatible hidden-state artifacts.

## File-Based Artifacts

Use `--from files` for HF/Transformers, patched llama.cpp, custom scripts, or
precomputed artifacts. Sarf validates paths and records capabilities; it does
not validate the internal tensor layout beyond the manifest contract.
