# Paper 1-Style Reproduction Example

This tiny example demonstrates the intended Paper 1 workflow without claiming
full paper reproduction. It is designed for CI, professor-packet review, and
local smoke tests.

The example uses the bundled tiny morphology dataset and committed mock backend
artifacts. The mock artifacts exercise Sarf's import and reporting paths; they
are not hidden states from Qwen3-0.6B, Llama-3.2-1B, Ember, llama.cpp, or any
other model run.

## Command Sequence

Run from the repository root:

```bash
OUT=/tmp/sarf-paper1-example
mkdir -p "$OUT"

sarf validate-dataset examples/paper_style/tiny_morphology.jsonl \
  --out "$OUT/dataset_validation.json"

sarf validate-labels examples/paper1_reproduction/experiment.toml \
  --out "$OUT/label_diagnostics.json"

sarf make-prompts examples/paper1_reproduction/experiment.toml \
  --out "$OUT/prompts.jsonl"

sarf make-splits examples/paper1_reproduction/experiment.toml \
  --out "$OUT/splits.json"

sarf summarize-splits examples/paper_style/tiny_morphology.jsonl "$OUT/splits.json" \
  --out "$OUT/split_diagnostics.json"

sarf tokenization-diagnostics examples/paper1_reproduction/experiment.toml \
  --tokenization-artifact examples/paper1_reproduction/mock_backend/tokenization.json \
  --out "$OUT/tokenization_diagnostics.json"

sarf import-artifacts \
  --from files \
  --run-id paper1-style-demo \
  --prompts-path "$OUT/prompts.jsonl" \
  --tokenization-path examples/paper1_reproduction/mock_backend/tokenization.json \
  --positions-path examples/paper1_reproduction/mock_backend/positions.json \
  --hidden-states-path examples/paper1_reproduction/mock_backend/hidden_states.json \
  --report-path examples/paper1_reproduction/mock_backend/report.json \
  --out "$OUT/artifact_manifest.json"

sarf validate-manifest --manifest "$OUT/artifact_manifest.json" \
  --out "$OUT/artifact_validation.json"

sarf summarize-run --manifest "$OUT/artifact_manifest.json" \
  --out "$OUT/artifact_summary.json"

sarf make-probe-config examples/paper1_reproduction/experiment.toml \
  --artifact-manifest "$OUT/artifact_manifest.json" \
  --out "$OUT/probe_config.toml"

sarf make-baselines examples/paper1_reproduction/experiment.toml \
  --out "$OUT/baselines"

sarf run-baseline \
  --config "$OUT/baselines/char_ngram.toml" \
  --splits "$OUT/splits.json" \
  --out "$OUT/char_ngram.results.json"

sarf run-baseline \
  --config "$OUT/baselines/majority.toml" \
  --splits "$OUT/splits.json" \
  --out "$OUT/majority.results.json"

sarf summarize-baseline "$OUT/char_ngram.results.json" \
  --out "$OUT/char_ngram.summary.json"

sarf make-experiment examples/paper1_reproduction/experiment.toml \
  --out "$OUT/run"

sarf report "$OUT/run" \
  --out "$OUT/report.md"
```

## What This Demonstrates

- Dataset validation for Arabic morphology rows.
- Prompt rendering from a Paper 1-style experiment config.
- Lemma-heldout and root-heldout split metadata.
- Label and split diagnostics that expose leakage and unseen-label risks.
- Tokenization diagnostics for surface counts, artifact token counts, and
  Arabic normalization/token-boundary concerns. The CLI accepts repeated
  `--tokenization-artifact` flags when comparing multiple backend tokenization
  outputs.
- Artifact import from mock backend files.
- Probe config generation against an imported artifact manifest.
- Character n-gram and majority baseline artifact generation.
- Markdown report output.

## What This Does Not Claim

This example does not run model inference, extract hidden states, train probes,
or reproduce the Paper 1 results. It demonstrates the workflow contract around
those steps so the real Paper 1 artifacts can be plugged in explicitly.
