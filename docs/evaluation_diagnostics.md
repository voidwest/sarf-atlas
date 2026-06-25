# Sarf v0.4 Evaluation Diagnostics

Sarf v0.4 prepares evaluation scaffolding for Arabic morphology probing. It
does not run model inference, extract hidden states, compile llama.cpp, train
probes, or train baselines.

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

`sarf make-baselines` writes placeholder configs for a character n-gram baseline
and majority baseline, plus a README describing expected inputs and outputs.
These files are configuration scaffolds only.
