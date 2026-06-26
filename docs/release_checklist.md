# Release Checklist

Use this checklist for the final v1.0 release prep and publication pass.

## Required Before Publishing

- Run `python -m unittest discover -s tests`.
- Run a fresh virtualenv install test with `python -m pip install .`.
- Run `sarf --help` and the documented quickstart commands.
- Confirm `pyproject.toml` version matches `src/sarf/__init__.py`.
- Confirm `README.md`, `CHANGELOG.md`, and docs mention the same release.
- Confirm the MIT `LICENSE` file is present before publishing distributions.
- Confirm `CITATION.cff` metadata is current if the release should be cited.
- Confirm the GitHub release workflow uses PyPI Trusted Publishing.

## Trusted Publishing

The workflow in `.github/workflows/ci.yml` includes a `publish` job using
`pypa/gh-action-pypi-publish`. Configure the PyPI project to trust this GitHub
repository and the release environment before cutting a tag.

## Full User Journey

```bash
python -m venv /tmp/sarf-install-test
. /tmp/sarf-install-test/bin/activate
python -m pip install .

sarf init --out-dir /tmp/sarf-demo --name demo
sarf validate-dataset examples/paper_style/tiny_morphology.jsonl
sarf make-experiment examples/paper_style/experiment.toml --out /tmp/sarf-demo/run
sarf validate-labels examples/paper_style/experiment.toml --out /tmp/sarf-demo/labels.json
sarf summarize-splits examples/paper_style/tiny_morphology.jsonl /tmp/sarf-demo/run/split_metadata.json --out /tmp/sarf-demo/splits.json
sarf make-baselines examples/paper_style/experiment.toml --out /tmp/sarf-demo/baselines
sarf make-probe-config examples/paper_style/experiment.toml --out /tmp/sarf-demo/probe_config.toml
sarf report /tmp/sarf-demo/run --out /tmp/sarf-demo/report.md
```
