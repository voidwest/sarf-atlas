# Paper-Style Workflow Guide

This guide is the stable 1.0-oriented path for a small Arabic morphology
probing workflow. It prepares inputs and artifacts; it does not run model
inference or train probes.

## Inputs

- A morphology JSONL dataset using dataset row schema v1.
- An experiment TOML with dataset path, prompt template, target labels, and
  split settings.
- Optional backend artifacts from Ember, llama.cpp, HF/Transformers, or files.

## Minimal Flow

```bash
sarf validate-dataset examples/paper_style/tiny_morphology.jsonl

sarf validate-labels examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/label_diagnostics.json

sarf make-prompts examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/prompts.jsonl

sarf make-splits examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/splits.json

sarf summarize-splits examples/paper_style/tiny_morphology.jsonl /tmp/sarf-demo/splits.json \
  --out /tmp/sarf-demo/split_diagnostics.json

sarf tokenization-diagnostics examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/tokenization_diagnostics.json

sarf make-baselines examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/baselines

sarf run-baseline \
  --config /tmp/sarf-demo/baselines/char_ngram.toml \
  --splits /tmp/sarf-demo/splits.json \
  --out /tmp/sarf-demo/char_ngram.results.json

sarf make-probe-config examples/paper_style/experiment.toml \
  --artifact-manifest /tmp/sarf-demo/artifact_manifest.json \
  --out /tmp/sarf-demo/probe_config.toml

sarf make-experiment examples/paper_style/experiment.toml \
  --out /tmp/sarf-demo/run

sarf report /tmp/sarf-demo/run \
  --out /tmp/sarf-demo/report.md
```

## Paper 1-Style Smoke Path

For an end-to-end example with committed mock backend artifacts, use
`examples/paper1_reproduction/README.md`. That path exercises validation,
prompts, splits, diagnostics, artifact import, baseline comparison, and report
generation without claiming paper reproduction.
