# Sarf v0.3 Paper-Style Workflow

Sarf Atlas v0.3 prepares Paper-style Arabic morphology experiments. It validates
dataset rows, renders prompts, creates heldout split metadata, writes backend
config stubs, imports artifacts, and produces report summaries.

Sarf v0.3 does not train probes, run models, extract hidden states, or claim
paper reproduction. It prepares and validates the workflow structure around
those steps.

## Dataset Schema

Rows are JSONL objects. Required fields:

- `id`
- `surface`
- `lemma`
- `root`
- `pos`
- `abstract_pattern`
- `concrete_pattern`

Optional label fields may be null or missing:

- `gender`
- `number`
- `features`

Example:

```json
{
  "id": "sample-0001",
  "surface": "كتب",
  "lemma": "كتب",
  "root": "ك ت ب",
  "pos": "VERB",
  "abstract_pattern": "فعل",
  "concrete_pattern": "كتب",
  "gender": null,
  "number": null,
  "features": {
    "aspect": "perf",
    "person": "3"
  }
}
```

Validate a dataset:

```bash
sarf validate-dataset data/morphology.jsonl
```

## Prompt Templates

Prompt templates use Python format fields from each normalized dataset row:

```toml
[prompts]
template = "حلل صرفيا الكلمة العربية: {surface}."
position_policy = "prompt_final"

[labels]
targets = ["pos", "gender", "number", "root", "lemma", "abstract_pattern"]
```

Render prompts from an experiment config:

```bash
sarf make-prompts experiment.toml --out prompts/morph_prompts.jsonl
```

## Split Strategies

v0.3 supports:

- `lemma_heldout`
- `root_heldout`

Split config:

```toml
[splits]
strategies = ["lemma_heldout", "root_heldout"]
test_fraction = 0.2
seed = 42
```

Write split metadata:

```bash
sarf make-splits experiment.toml --out splits/heldout.json
```

Split metadata includes deterministic unit assignments, counts, seed/config, and
a character-baseline metadata placeholder. Sarf records where that metadata
belongs; it does not run baselines.

## Paper-Style Example

The repository includes:

- `examples/paper_style_morphology.jsonl`
- `examples/paper_style_experiment.toml`

Run:

```bash
sarf validate-dataset examples/paper_style_morphology.jsonl
sarf make-prompts examples/paper_style_experiment.toml --out /tmp/sarf-v03/prompts.jsonl
sarf make-splits examples/paper_style_experiment.toml --out /tmp/sarf-v03/splits.json
sarf make-experiment examples/paper_style_experiment.toml --out /tmp/sarf-v03/run
sarf report /tmp/sarf-v03/run --out /tmp/sarf-v03/report.md
```

The generated run directory contains prompt JSONL, split metadata, backend config
stub, artifact manifest stub, JSON summary, and Markdown report.

## Artifact Imports

Artifacts still come from external backends:

```bash
sarf import-artifacts \
  --from files \
  --run-id paper-style-demo \
  --prompts-path /tmp/sarf-v03/run/prompts.jsonl \
  --hidden-states-path backend-output/hidden_states.npy \
  --out /tmp/sarf-v03/run/artifact_manifest.json
```

`sarf validate-manifest` and `sarf summarize-run` report which artifact paths are
present, placeholders, or missing. Missing optional backend outputs are not
silently treated as supported capabilities.

## What Sarf Still Does Not Do

Sarf v0.3 does not:

- Train probes
- Run models
- Extract hidden states
- Compile llama.cpp
- Claim Paper 1 reproduction

