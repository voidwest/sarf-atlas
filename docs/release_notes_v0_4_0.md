# Sarf Atlas v0.4.0 Release Notes

Sarf Atlas v0.4.0 adds evaluation-preparation scaffolding for Arabic
morphology probing workflows. It remains backend-agnostic and lightweight:
Sarf organizes, backends extract, auditors compare.

## Added

- `sarf validate-labels` for label cardinality, missing/null counts, and
  high-cardinality warnings.
- `sarf summarize-splits` for train/test counts, group overlap checks,
  per-label distributions, leakage warnings, and unseen test-label warnings.
- `sarf make-probe-config` for `probe_config.toml` scaffolds with target
  labels, split paths, artifact manifest path, position policy, layer
  placeholders, and probe type placeholders.
- `sarf make-baselines` for character n-gram and majority baseline config
  placeholders plus a README describing expected inputs and outputs.
- Report sections for label and split diagnostics when those diagnostics are
  available in the experiment summary.
- Documentation for evaluation diagnostics, label cardinality, leakage-aware
  split checks, and heldout-split caution for root, lemma, and pattern labels.

## Changed

- Package version is now `0.4.0`.
- Generated schemas and scaffold metadata now use v0.4 identifiers where
  applicable.
- Project and example workflow scaffolds now identify as Sarf v0.4.

## Non-Goals

Sarf Atlas v0.4.0 does not:

- Run model inference.
- Extract hidden states.
- Compile or download llama.cpp.
- Train probes.
- Train baselines.
- Add heavy ML dependencies.
- Claim paper reproduction.

## Validation

The release candidate was checked with:

- `python3 -m unittest discover -s tests`
- `python3 -m compileall -q src`
- sdist and wheel build into `/tmp/sarf-atlas-0.4-dist`
- `twine check /tmp/sarf-atlas-0.4-dist/*`
- Clean wheel install in a temporary venv
- Installed CLI smoke tests for the new v0.4 commands

