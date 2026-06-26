# One-Page Summary

## Title

Leakage-Aware Probing of Arabic Morphology in Small Language Models

## Research Question

Which Arabic morphology probing claims remain defensible when evaluation is
made more leakage-aware, especially under lemma-heldout and root-heldout
splits rather than ordinary random cross-validation?

## Core Claim

Random splits can overstate Arabic morphology probing results. Under stricter
lemma/root-heldout evaluation, POS remains decodable above character baselines
in Qwen3-0.6B and Llama-3.2-1B, while high-cardinality labels such as
root/lemma/pattern require more careful evaluation than ordinary closed-set
probing.

## What I Built

I built a reproducibility-oriented probing workflow for Arabic morphology
experiments. It tracks datasets, label schemas, prompt templates, split
definitions, backend extraction artifacts, baseline comparisons, diagnostics,
and report scaffolding. The public tooling direction is split across Sarf Atlas
for morphology workflow organization, Ember for local extraction, and
gguf-parity-tools for backend parity checks.

## Experiments

The experiments compare Arabic morphology probing behavior across random
cross-validation and stricter lemma/root-heldout split designs. They evaluate
small language models, including Qwen3-0.6B and Llama-3.2-1B, against
character n-gram baselines and include prompt ablations to test whether the
reported signals are robust to prompt formulation.

## Contributions

1. Arabic morphology probing workflow with leakage-aware split design.
2. Comparison of random CV vs lemma/root-heldout splits.
3. Character n-gram baseline comparison.
4. Prompt ablation analysis.
5. Public tooling direction: Sarf Atlas / Ember / gguf-parity-tools.

## Main Findings

POS remains the strongest and most defensible signal under stricter heldout
evaluation. Gender and number show smaller positive lift. Root, lemma, and
pattern results are more vulnerable to closed-set leakage and should not be
overclaimed from ordinary random splits.

## Main Limitation

This does not claim Arabic morphology is "solved." It identifies which signals
survive stricter evaluation and which claims become unsafe.

## Feedback Requested

I want feedback on whether the framing is suitable for journal submission, what
experiments are necessary before submission, whether this should remain Paper 1
or expand to include scaling/tokenizer analysis, and what venue type best fits
the contribution.

## Intended Next Step

The intended next step is professor review of the current Paper 1 framing. The
decision point is whether to prepare a journal submission from this
methodological caution paper, release an arXiv version first, or expand the
study with scaling and tokenizer analysis before submission.
