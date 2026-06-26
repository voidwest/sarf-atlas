# Baseline Runner Example

This directory is a tiny runnable example for the optional Sarf baseline path.
It uses `examples/paper_style/experiment.toml` and the bundled toy morphology
dataset.

Recreate the artifacts:

```bash
PYTHONPATH=src python -m sarf make-splits examples/paper_style/experiment.toml --out examples/baseline_runner/splits.json
PYTHONPATH=src python -m sarf make-baselines examples/paper_style/experiment.toml --out examples/baseline_runner/baselines
PYTHONPATH=src python -m sarf run-baseline --config examples/baseline_runner/baselines/char_ngram.toml --splits examples/baseline_runner/splits.json --out examples/baseline_runner/char_ngram.results.json
PYTHONPATH=src python -m sarf summarize-baseline examples/baseline_runner/char_ngram.results.json --out examples/baseline_runner/char_ngram.summary.json
```

`char_ngram.results.json` uses schema `sarf_baseline_results_v0_5`.
The runner uses only the Python standard library unless a config explicitly
declares optional modules in `[dependencies].modules`.
