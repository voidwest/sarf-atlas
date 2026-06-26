# Reproducibility Notes

## Current Status

The manuscript is a working draft for professor review. Core experiments and
results are present, but the packet still needs the latest Overleaf PDF export
added as `paper_draft.pdf`.

## What Should Be Traceable

- Repository state used for the packet.
- Data and split definitions.
- Pipeline commands and configuration.
- Exact prompts.
- Backend extraction or imported artifact trail.
- Tables, plots, diagnostics, and report outputs.

## Repository State

Current roadmap/project metadata commit:

```text
fb2635e Update Sarf Atlas roadmap and project metadata
```

The active public package status is `sarf-atlas==0.4.0`.

## Workflow Surface

Sarf Atlas currently provides workflow scaffolding for:

- Dataset validation.
- Prompt generation.
- Label diagnostics.
- Lemma-heldout and root-heldout split diagnostics.
- Tokenization diagnostics.
- Probe config scaffolding.
- Baseline config scaffolding and lightweight standard-library baseline
  artifacts.
- Artifact import.
- Report scaffolding.

Base Sarf Atlas does not itself train probes, run model inference, extract
hidden states, or claim full Paper 1 reproduction.

## Main Demonstration Path

Use `examples/paper1_reproduction/README.md` as the packet demonstration path.
It runs end to end on bundled toy data and committed mock backend artifacts:

- Dataset validation.
- Prompt generation.
- Leakage-aware split diagnostics.
- Tokenization diagnostics against mock token counts.
- Artifact import and validation.
- Probe config generation.
- Character n-gram and majority baseline comparisons.
- Markdown report output.

The mock backend files are deliberately marked `not_research_output`; they
exercise the workflow contract without claiming Qwen3, Llama, Ember, or
llama.cpp results.

## Packet-Level Reproducibility Requirement

Before sending the packet, confirm that the draft PDF, one-page summary,
limitations, repo links, and questions all refer to the same experiment state
and do not mix old results with current wording.
