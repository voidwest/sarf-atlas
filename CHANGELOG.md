# Changelog

## Unreleased

### v0.9.0 Release-Candidate Prep

- Reworked top-level docs around the 1.0 public surface.
- Added command contract, backend guide, schema guide, examples index, and
  release checklist.
- Added citation and contributing metadata.
- Extended CI/release workflow planning for build and PyPI Trusted Publishing.

### v0.8.0 Contract Freeze Prep

- Classified CLI commands as stable, experimental, or deprecated.
- Added numeric `schema_version` fields to important JSON outputs while
  preserving historical string `schema` names.
- Froze artifact manifest schema v1, dataset row schema v1, split metadata
  schema v1, tokenization diagnostics schema v1, and baseline artifact schema
  v1 in documentation.
- Added backward-compatibility and deprecation policy notes.

### v0.7.0 Tokenization Diagnostics

- Added backend-agnostic tokenization diagnostics for Arabic morphology rows.
- Added repeated `--tokenization-artifact` support for comparing emitted token
  counts across backend paths.

### v0.6.0 Paper 1-Style Example

- Added a tiny Paper 1-style end-to-end example with committed mock backend
  artifacts.
- Added regression coverage for the demonstration path.

### v0.5.0 Optional Baseline Runners

- Added lightweight standard-library `majority` and `char_ngram` baseline
  runners.
- Added versioned baseline result and summary artifacts.
- Added optional dependency checks for local baseline configs.

## v0.4.0

- Added evaluation-preparation diagnostics and Paper-style scaffolding.
- Added artifact import and backend availability inspection.
