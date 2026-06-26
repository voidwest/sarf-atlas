# Contributing

Sarf Atlas is moving toward a stable 1.0 CLI and artifact contract. Keep
changes small, explicit, and covered by tests when they affect command output
or schemas.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests
```

## Contribution Guidelines

- Preserve stable command names and required arguments listed in
  `docs/command_contract.md`.
- Add optional fields instead of changing the meaning or type of existing
  schema v1 fields.
- Mark backend-specific behavior as optional unless base Sarf directly owns it.
- Keep examples deterministic and small enough for local smoke runs.
- Do not add heavyweight ML dependencies to the base package.

## Schema Changes

Schema v1 changes require:

- A clear compatibility note in `docs/artifact_schema_guide.md`.
- Regression tests covering representative artifacts.
- A changelog entry.

Breaking changes should be held for a new schema version and documented with a
deprecation path.
