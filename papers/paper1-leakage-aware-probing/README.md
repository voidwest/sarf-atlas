# Leakage-Aware Probing of Arabic Morphology in Small Language Models

Current status: core experiments and results are present. The manuscript is a
working draft for possible journal development.

Paper 1 is framed as a methodological caution paper. It studies which Arabic
morphology probing claims remain defensible when evaluation is made more
leakage-aware.

Main finding: POS survives stricter heldout evaluation. Gender and number show
smaller positive lift. Root, lemma, and pattern should not be overclaimed under
ordinary closed-set heldout classification.

Reproducibility assets should remain explicit and traceable:

- Repository state.
- Data and split definitions.
- Pipeline commands and configuration.
- Exact prompts.
- Artifact trail for outputs, tables, and plots.

Professor-packet demonstration path:

- `examples/paper1_reproduction/README.md`
- `examples/paper1_reproduction/experiment.toml`
- `examples/paper1_reproduction/mock_backend/`

This path demonstrates the workflow contract with tiny bundled data and mock
backend artifacts. It does not claim full Paper 1 reproduction.
