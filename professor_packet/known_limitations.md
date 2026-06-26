# Known Limitations

## Scientific Claims

This work does not claim that Arabic morphology is solved. It argues that some
probing claims are more defensible than others once leakage-aware evaluation is
used.

## Evaluation Scope

Random cross-validation can overstate performance when examples share lemmas,
roots, or other lexical structure across train and test splits. The stricter
lemma/root-heldout evaluations are intended to expose that risk, not to exhaust
all possible generalization settings.

## Label Difficulty

POS is comparatively stable under stricter evaluation. Gender and number show
smaller positive lift. High-cardinality labels such as root, lemma, and pattern
are harder to interpret safely under ordinary closed-set probing.

## Model Scope

The current framing focuses on small language models, including Qwen3-0.6B and
Llama-3.2-1B. The results should not be generalized to all model scales,
families, tokenizers, or training regimes without additional experiments.

## Baseline Scope

Character n-gram baselines are important because Arabic morphology has strong
surface-form cues. The paper should be careful when interpreting model lift
over these baselines, especially for labels that may be partially recoverable
from orthographic patterns.

## Tooling Scope

Sarf Atlas is currently workflow and artifact scaffolding. It organizes
experiments and diagnostics, but base Sarf Atlas does not perform hidden-state
extraction, train probes, or run full Paper 1 reproduction end to end.

## Next Study Boundary

Scaling and tokenizer analysis may belong in the expanded study or Paper 2. The
professor review should decide whether those experiments are required before
submission or should remain separate.
