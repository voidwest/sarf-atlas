# Sarf CLI Contract Prep

This document records the v0.8 command-surface decision before the v1.0
contract freeze. A stable command means Sarf should not casually rename it,
remove required arguments, or change output schemas after 1.0.

## Stable For 1.0

| Command | Required arguments | Stable output |
| --- | --- | --- |
| `sarf init` | `--out-dir`, optional `--name` | `sarf.project.json` schema v1 |
| `sarf example-workflow` | `--out-dir` | Toy project scaffold and manifest examples |
| `sarf validate-dataset` | `input` | Dataset validation report schema v1 |
| `sarf make-prompts` | `experiment` or `--input`, `--out` | Prompt JSONL records |
| `sarf make-splits` | `experiment`, `--out` | Split metadata schema v1 |
| `sarf make-experiment` | `experiment`, `--out` | Paper-style run scaffold |
| `sarf import-artifacts` | `--from`, `--out`, source-specific args | Artifact manifest schema v1 |
| `sarf summarize-run` | `target` or `--manifest` | Run summary report |
| `sarf validate-labels` | `input` | Label diagnostics report |
| `sarf summarize-splits` | `dataset`, `splits` | Split diagnostics report |
| `sarf make-probe-config` | `experiment`, `--out` | Probe config scaffold |
| `sarf make-baselines` | `experiment`, `--out` | Baseline config schema v1 inputs |
| `sarf run-baseline` | `--config`, `--splits`, `--out` | Baseline result schema v1 |
| `sarf summarize-baseline` | `artifact` | Baseline summary schema v1 |
| `sarf tokenization-diagnostics` | `input` | Tokenization diagnostics schema v1 |
| `sarf report` | `run_dir`, `--out` | Markdown report |

## Experimental

These commands are supported for local inspection but are not part of the
1.0-stable contract yet:

| Command | Reason |
| --- | --- |
| `sarf backends list` | Backend inventory will evolve as adapters are added. |
| `sarf backend llama-cpp doctor` | llama.cpp binary names and capabilities vary by build. |
| `sarf backend ember doctor` | Ember integration is optional and external to base Sarf. |

## Deprecated Or Legacy

These commands remain for compatibility but should not anchor new docs:

| Command | Replacement |
| --- | --- |
| `sarf import-ember` | `sarf import-artifacts --from ember` |
| `sarf import-files` | `sarf import-artifacts --from files` |
| `sarf validate-artifact` | `sarf validate-manifest` for Sarf manifests; Ember validation remains backend-specific. |
| `sarf split-metadata` | `sarf make-splits` |
| `sarf ember-config` | backend-specific docs or external Ember config templates |
| `sarf toy-dataset` | `sarf example-workflow` or committed `examples/` data |

## Rename Decisions

No listed v1.0 command needs a pre-1.0 rename. The names are explicit and
script-friendly. The only consolidation is already done through
`import-artifacts`, which supersedes older source-specific import commands.

## Compatibility Policy

- Patch releases may add optional fields to JSON outputs.
- Minor releases may add commands, optional arguments, or new schema versions.
- Stable v1 fields may not change type or meaning without a deprecation window.
- Deprecated commands should remain callable for at least one minor release
  after a replacement is documented.
- Experimental commands may change with release notes, but should fail with
  actionable messages when local dependencies are absent.
