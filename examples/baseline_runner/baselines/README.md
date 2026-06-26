# Sarf Baseline Scaffolds

These files describe expected baseline configuration inputs and outputs.
They can be consumed by the optional standard-library Sarf baseline runner.

Expected inputs:

- Morphology dataset JSONL
- Split metadata with train/test assignments
- Target labels from the experiment TOML

Optional dependency guard:

- Leave `[dependencies].modules = []` for bundled standard-library runners.
- Add module names only when a local baseline implementation requires them.
- `sarf run-baseline` fails before writing artifacts if a declared module is missing.

Expected outputs:

- Per-label predictions
- Per-label aggregate metrics
- Warnings for labels unseen in train

Run example:

```bash
sarf run-baseline --config char_ngram.toml --splits ../split_metadata.json --out char_ngram.results.json
sarf summarize-baseline char_ngram.results.json
```

The runner does not run model inference, extract hidden states, train probes, or add heavyweight dependencies.
