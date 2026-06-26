# Sarf v0.4 Evaluation Diagnostics

Sarf v0.4 prepares evaluation scaffolding for Arabic morphology probing. It
does not run model inference, extract hidden states, compile llama.cpp, train
probes, or run heavyweight training pipelines.

## Label Diagnostics

Use `sarf validate-labels` on an experiment TOML or dataset JSONL:

```bash
sarf validate-labels experiment.toml --out diagnostics/labels.json
```

The command reports required and optional label fields, missing/null counts,
label cardinality, top values, and warnings for high-cardinality labels. Root,
lemma, abstract pattern, and concrete pattern often have many values relative to
dataset size. Treating those labels as closed-set classifier targets can produce
misleading results, especially when the split intentionally withholds lemmas or
roots from train.

## Split Diagnostics

Use `sarf summarize-splits` with a dataset JSONL and split metadata:

```bash
sarf summarize-splits data/morphology.jsonl splits/heldout.json --out diagnostics/splits.json
```

The command reports train/test counts, train/test group overlap for lemma and
root when those fields are available, per-label train/test distributions, and
labels seen in test but not train. Overlap warnings indicate possible leakage.
Unseen-label warnings indicate that a closed-set classifier may be asked to
predict a class it never observed in train.

## Heldout Caution

Heldout splits are useful because they test generalization across morphology
groups instead of memorization. They also make some targets inappropriate for a
plain closed-set classifier:

- `lemma` under lemma-heldout is often unseen in train by design.
- `root` under root-heldout is often unseen in train by design.
- `abstract_pattern` and `concrete_pattern` can have high cardinality or sparse
  distributions in small datasets.

For these targets, prefer leakage-aware evaluation design, open-set framing,
retrieval/ranking analysis, or grouped error analysis before interpreting probe
accuracy.

## Config Scaffolds

`sarf make-probe-config` writes a `probe_config.toml` placeholder with target
labels, split strategies, artifact manifest path, position policy, layer
selection placeholder, and probe type placeholder.

`sarf make-baselines` writes configs for a character n-gram baseline and a
majority baseline, plus a README describing expected inputs and outputs. These
configs are stable inputs for the optional lightweight runner:

```bash
sarf run-baseline --config configs/baselines/char_ngram.toml --splits splits/heldout.json --out artifacts/baselines/char_ngram.results.json
sarf summarize-baseline artifacts/baselines/char_ngram.results.json
```

The runner uses only the Python standard library. It emits
`sarf_baseline_results_v0_5` artifacts with per-label accuracy, predictions,
train/test cardinality, and warnings for test labels unseen in train. It does
not run model inference, extract hidden states, or train probes.

Generated configs contain `[dependencies].modules = []`. Keep it empty for the
bundled runners. If a local config declares extra modules, `sarf run-baseline`
checks them before writing output and reports missing optional dependencies
with a concrete install-or-remove hint.

`examples/baseline_runner/` contains a tiny generated character n-gram result
artifact and summary using the bundled paper-style toy data.

## Tokenization Diagnostics

`sarf tokenization-diagnostics` writes `sarf_tokenization_diagnostics_v0_7`
reports for an experiment TOML or dataset JSONL:

```bash
sarf tokenization-diagnostics experiment.toml --out diagnostics/tokenization.json
sarf tokenization-diagnostics experiment.toml --tokenization-artifact artifacts/tokenization.json --out diagnostics/tokenization.with-artifact.json
sarf tokenization-diagnostics experiment.toml --tokenization-artifact artifacts/backend-a-tokenization.json --tokenization-artifact artifacts/backend-b-tokenization.json --out diagnostics/tokenization.compare.json
```

The report surfaces Unicode character counts, whitespace token counts, optional
backend artifact token counts, and Arabic normalization or token-boundary
concerns. When multiple artifacts are supplied, `artifact_comparisons` records
matched rows, mean token counts, and mean deltas versus Unicode character
counts per artifact. It is backend-agnostic by default and does not require
tokenizer-atlas, llama.cpp, Ember, or model files.
