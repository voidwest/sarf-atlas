# Sarf Atlas

Sarf is a backend-agnostic research framework for Arabic morphology probing
experiments. It organizes datasets, prompts, splits, experiment configs,
extraction metadata, and evaluation artifacts, and is designed to let hidden
states or logits come from Ember, llama.cpp, Transformers, or precomputed files.

Architecture slogan:

```text
Sarf organizes.
Backends extract.
Auditors compare.
```

Sarf Atlas is not replacing Ember. Ember is currently the strongest local
backend path, but Sarf should not depend on one inference engine. Sarf owns
Arabic morphology schemas, task definitions, prompt templates, split
strategies, experiment configs, expected artifact schemas, report scaffolding,
backend-agnostic validation, and adapters for importing backend outputs.

Sarf does not own model execution internals, hidden-state extraction
implementation, llama.cpp compilation as a required behavior, or Ember
internals. Base Sarf works without local extraction backends installed.

The current split is:

- `ember`: one validated backend/tooling path for extraction artifacts.
- `sarf-atlas`: Arabic morphology research workspace, paper configs, notes,
  experiment manifests, package skeleton, and backend-agnostic workflow
  planning.
- `gguf-parity-tools`: validation and parity harness.

## Quickstart

Install Sarf Atlas:

```bash
pip install sarf-atlas
```

Create a project layout:

```bash
sarf init --out-dir /tmp/sarf-atlas-project --name sarf-atlas-project
```

Generate the toy workflow scaffold:

```bash
sarf example-workflow --out-dir /tmp/sarf-atlas-example
```

Import and summarize artifacts:

```bash
sarf import-artifacts --from files --run-id toy-run --prompts-path prompts/toy_prompts.jsonl --out artifacts/imported/toy-run.manifest.json
sarf summarize-run --manifest artifacts/imported/toy-run.manifest.json
```

The scaffold writes toy morphology data, prompts, split metadata, Ember config
placeholders, a Sarf artifact manifest, and an example workflow manifest. It is
framework scaffolding only, not hidden-state extraction, Paper 1 reproduction,
or research output. See `docs/CLI.md` for the backend capability matrix.

## Evaluation-Preparation Workflow

Sarf v0.4 adds evaluation-preparation diagnostics on top of the Paper-style
workflow commands:

```bash
sarf validate-dataset examples/paper_style/tiny_morphology.jsonl
sarf validate-labels examples/paper_style/experiment.toml --out /tmp/sarf-v04/label_diagnostics.json
sarf make-prompts examples/paper_style/experiment.toml --out /tmp/sarf-v04/prompts.jsonl
sarf make-splits examples/paper_style/experiment.toml --out /tmp/sarf-v04/splits.json
sarf summarize-splits examples/paper_style/tiny_morphology.jsonl /tmp/sarf-v04/splits.json --out /tmp/sarf-v04/split_diagnostics.json
sarf make-probe-config examples/paper_style/experiment.toml --artifact-manifest /tmp/sarf-v04/artifact_manifest.json --out /tmp/sarf-v04/probe_config.toml
sarf make-baselines examples/paper_style/experiment.toml --out /tmp/sarf-v04/baselines
sarf make-experiment examples/paper_style/experiment.toml --out /tmp/sarf-v04/run
sarf report /tmp/sarf-v04/run --out /tmp/sarf-v04/report.md
```

This supports dataset rows, prompt construction, label fields,
lemma-heldout/root-heldout split metadata, character-baseline metadata
placeholders, backend config stubs, artifact import, label diagnostics, split
diagnostics, probe config scaffolds, baseline config scaffolds, and report
scaffolding. Sarf v0.4 does not train probes or baselines, run models, extract
hidden states, run model inference, or claim paper reproduction. See
`docs/evaluation_diagnostics.md` for leakage and cardinality guidance.

Current adapter namespace:

- `sarf.backends.ember`
- `sarf.backends.files`
- `sarf.backends.llama_cpp`

Future optional adapters may cover Transformers/HF, vLLM, and additional
precomputed hidden-state formats.

## Optional Backends

Sarf v0.4 can inspect local backend availability, but detection is optional and
does not make llama.cpp, Ember, Transformers/HF, or hidden-state extraction part
of the base package:

```bash
sarf backends list
sarf backend llama-cpp doctor
sarf backend ember doctor
```

llama.cpp detection checks `LLAMA_TOKENIZE_BIN`, `LLAMA_CLI_BIN`,
`LLAMA_SIMPLE_BIN`, and common PATH names. Default llama.cpp is useful for some
local tokenization/logits workflows, but it should not be treated as emitting
Sarf-compatible hidden-state artifacts.

Ember detection checks `EMBER_BIN`, PATH `ember`, and whether
`ember validate-run --help` is callable when an Ember binary is found. Ember is
optional; Sarf can still organize workflows and import artifacts from files.

Users may bring artifacts from llama.cpp, Ember, HF/Transformers, or
precomputed files. Hidden-state extraction is not built into base Sarf and
requires an emitting backend such as Ember, patched llama.cpp, HF/Transformers,
or precomputed Sarf-compatible artifacts.
