# Sarf Atlas Context

This file records the local prototype work done inside the Ember repository so
future sessions can resume without rediscovering the setup.

## Repository Boundary

- Ember remains the engineering, tooling, instrumentation, backend, and artifact
  layer.
- Sarf Atlas is a local research workspace scaffold under `sarf-atlas/`.
- Sarf Atlas should not implement hidden-state extraction itself.
- External llama.cpp execution should enter through Ember's CLI/backend boundary.
- This prototype is an experimental workspace inside the Ember repository.

## Current Sarf Atlas Layout

Created under `sarf-atlas/`:

- `README.md`
- `ROADMAP.md`
- `context.md`
- `configs/paper1.example.toml`
- `docs/design-notes.md`
- `papers/paper1-leakage-aware-probing/README.md`
- `papers/paper1-leakage-aware-probing/notes.md`
- `papers/paper1-leakage-aware-probing/manifest.template.toml`
- `scripts/README.md`
- `smoke/README.md`
- `smoke/prompts.small.jsonl`
- `smoke/llama_cpp_smoke.example.toml`
- `smoke/llama_cpp_mock_smoke.toml`
- `smoke/mock_llama_ember_extract.py`
- `smoke/fixtures/mock-model.gguf`
- `smoke/llama_cpp_tokenize_extract.py`
- `smoke/export_tokenizer_json_metadata.py`
- `smoke/TOKENIZATION_SMOKE.md`
- `smoke/run_tokenization_parity_smoke.sh`
- `.gitignore`

`sarf-atlas/.gitignore` ignores Python bytecode, local `runs/`, and
`*.local.toml`.

## Ember CLI/Backend Findings

Ember has a Rust CLI in `src/main.rs`.

Relevant commands:

```bash
cargo run -- extract --config <config.toml>
cargo run -- validate-backends --native-run <dir> --external-run <dir>
```

Relevant backend names from `src/extraction.rs`:

- `native`
- `llama-cpp`
- `llama-cpp-external`

Current limitation:

- `llama-cpp-external` exists and dispatches to an external process with
  `--request <llama_cpp_request.json>`.
- It currently rejects hidden-state layer extraction unless `layers = []`.
- It can validate tokenization/positions/artifact skeletons returned by an
  external process.

Artifact contract docs:

- `docs/artifact_contract.md`

## Mock External Backend Smoke

Purpose:

- Exercise Ember's real `extract` CLI and `llama-cpp-external` dispatch.
- Do not run llama.cpp.
- Do not run inference.
- Do not produce research output.

Config:

```bash
sarf-atlas/smoke/llama_cpp_mock_smoke.toml
```

Helper:

```bash
sarf-atlas/smoke/mock_llama_ember_extract.py
```

Run:

```bash
cargo run -- extract --config sarf-atlas/smoke/llama_cpp_mock_smoke.toml
```

Output:

```bash
/tmp/sarf-atlas-ember-smoke/runs/mock-llama-cpp-external
```

The mock output manifest/report include:

- `mock = true`
- `no_inference = true`
- `not_research_output = true`
- `purpose = "backend plumbing smoke test"`

## Real llama.cpp Tokenization Smoke

The real tokenization smoke is documented in
`sarf-atlas/smoke/TOKENIZATION_SMOKE.md` and can be run with:

```bash
MODEL_PATH=/path/to/model.gguf \
TOKENIZER_JSON=/path/to/tokenizer.json \
LLAMA_TOKENIZE_BIN=/path/to/llama-tokenize \
GGUF_PARITY_TOOLS_PATH=/path/to/gguf-parity-tools \
OUT_ROOT=/tmp/sarf-atlas-ember-smoke \
bash sarf-atlas/smoke/run_tokenization_parity_smoke.sh
```

Observed local result:

- Ember dispatched to `llama-cpp-external`.
- The helper called a real llama.cpp tokenizer path.
- 3 smoke prompts were processed.
- `gguf-parity-tools token-audit` passed with matching token IDs for all smoke
  prompts.
- No generation was requested.
- No logits were requested.
- No hidden states were requested.
- The output is not research output.

The report and metadata mark:

- `real_llama_cpp = true`
- `real_tokenization = true`
- `no_generation = true`
- `no_logits = true`
- `no_hidden_states = true`
- `not_research_output = true`

## gguf-parity-tools Integration

The tokenization smoke expects an existing local `gguf-parity-tools` checkout
or installation path, supplied as `GGUF_PARITY_TOOLS_PATH`. It does not download
or install that dependency.

Relevant command shape:

```bash
python3 -m parity_tools token-audit \
  --candidate-metadata <candidate.json> \
  --reference-metadata <reference.json> \
  --out <report.json>
```

Metadata shape:

```json
{
  "prompts": [
    {
      "index": 0,
      "prompt": "...",
      "token_ids": [1, 2, 3]
    }
  ]
}
```

The real llama.cpp helper now writes:

```bash
/tmp/sarf-atlas-ember-smoke/runs/tokenization-parity-smoke/metadata.llamacpp.json
```

The tokenizer JSON metadata exporter is:

```bash
sarf-atlas/smoke/export_tokenizer_json_metadata.py
```

Export tokenizer JSON metadata:

```bash
python3 sarf-atlas/smoke/export_tokenizer_json_metadata.py \
  --tokenizer /path/to/tokenizer.json \
  --prompts sarf-atlas/smoke/prompts.small.jsonl \
  --out /tmp/sarf-atlas-ember-smoke/runs/tokenizer-json/metadata.tokenizer-json.json
```

Run parity token audit:

```bash
PYTHONPATH=/path/to/gguf-parity-tools \
  python3 -m parity_tools token-audit \
  --candidate-metadata /tmp/sarf-atlas-ember-smoke/runs/tokenizer-json/metadata.tokenizer-json.json \
  --reference-metadata /tmp/sarf-atlas-ember-smoke/runs/tokenization-parity-smoke/metadata.llamacpp.json \
  --out /tmp/sarf-atlas-ember-smoke/runs/tokenization-parity-smoke/token-audit.json
```

Observed token audit result:

- status: `pass`
- candidate prompt count: 3
- reference prompt count: 3
- all token IDs match: true
- row token counts: `11`, `17`, `17`

## Checks Run

Repeated lightweight checks used during the session:

```bash
python3 -c 'import pathlib, tomllib; [tomllib.loads(p.read_text()) for p in pathlib.Path("sarf-atlas").rglob("*.toml")]; print("toml ok")'
bash -n sarf-atlas/smoke/run_smoke_dry_run.sh
python3 -m py_compile sarf-atlas/smoke/*.py
cargo check
git status --short sarf-atlas
```

All passed at the end of the session.

## Important Limitations

- `llama-cpp-external` hidden-state extraction is not implemented yet.
- Real llama.cpp integration currently covers tokenization through Ember's
  external backend contract, not generation, logits, or hidden states.
- Private `*.local.toml` files are machine-local and ignored by
  `sarf-atlas/.gitignore`.
- `/tmp/sarf-atlas-ember-smoke` is scratch output only.

## Suggested Next Steps

1. Add an Ember CLI-visible `validate-run` command for standalone artifact
   validation without native-vs-external comparison.
2. Decide whether to keep `llama_cpp_tokenize_extract.py` as a Sarf Atlas smoke
   helper or move/adapt the adapter into Ember proper.
3. Add a logits-only external llama.cpp smoke, if a
   stable llama.cpp CLI/API path can write logits without patching.
4. Only then implement or adopt a patched/custom llama.cpp hidden-state
   extractor that writes Ember's artifact contract for layer shards.

## 2026-06-25 Current State

The original next steps above have mostly advanced. Current committed local
state:

- Sarf Atlas tokenization smoke is committed.
- Ember `validate-run` is committed.
- Validation layer docs are committed.
- The llama.cpp tokenization adapter has been promoted into `scripts/`.
- Experimental llama-cpp-python/libllama logits smoke exists and passes
  `validate-run`.
- A native Ember logits reference smoke exists and passes `validate-run`.
- Sarf v0.1 workflow scaffold is committed.
- Sarf package metadata cleanup is committed as
  `b849879 Prepare Sarf Atlas package metadata`.

Sarf v0.1 scope:

- Package/distribution name: `sarf-atlas`.
- Import/CLI package name: `sarf`.
- Console script: `sarf`.
- Sarf organizes datasets, tasks, prompts, splits, labels, positions, runs,
  manifests, reports, and backend-agnostic validation scaffolding.
- Backends extract. Auditors compare.
- Ember is a strong backend, not the parent framework.

Packaging readiness result:

- Editable install passed in a temporary virtual environment.
- Built wheel and sdist under `/tmp/sarf-dist-check/`.
- `twine check` passed for both built artifacts.
- Wheel install smoke passed from a clean temporary directory.
- Toy example workflow and manifest validation ran from a clean temporary
  directory.
- Built artifacts contain only package code and metadata; local smoke configs
  and private paths were not included.

TestPyPI status:

- `sarf-atlas==0.1.0` is live on TestPyPI.
- TestPyPI JSON metadata confirmed both artifacts:
  - `sarf_atlas-0.1.0-py3-none-any.whl`
  - `sarf_atlas-0.1.0.tar.gz`
- Fresh virtualenv install from TestPyPI passed.
- Installed CLI checks passed without `PYTHONPATH`:
  - `sarf --help`
  - `sarf backends list`
  - `python -m sarf backend llama-cpp doctor`
  - `python -m sarf backend ember doctor`

The successful TestPyPI upload used artifacts built under:

```bash
/tmp/sarf-atlas-dist/
```

- No real PyPI upload was attempted.
- No push or tag was made.

Important current truth:

- Tokenization smoke is real backend plumbing and token metadata validation,
  not research output.
- Logits smokes are tiny local engineering checks, not research output.
- No generation is run by these smokes.
- No hidden states are run by these smokes.
- Hidden-state extraction remains planned work, not implemented support.

Suggested next action after this checkpoint:

1. Polish package README wording so PyPI reads like an installed package, not a
   repository-local scaffold.
2. Rebuild, run `twine check`, and install the wheel in a clean environment.
3. Publish `sarf-atlas==0.1.0` to real PyPI if that version is unused there.

## 2026-06-25 v0.2 and v0.3 Release Checkpoint

Sarf Atlas moved from the v0.1 installable scaffold to published v0.2 and v0.3
packages.

Release progression:

- v0.1: installable scaffold.
- v0.2: usable workflow skeleton.
- v0.3: Paper-style Arabic morphology experiment preparation.

### v0.2.0

Implemented and released:

- `sarf init`
- `sarf import-artifacts`
- `sarf summarize-run`
- Cleaner example workflow layout.
- Backend capability matrix docs in `docs/CLI.md`.
- GitHub Actions CI in `.github/workflows/ci.yml`.
- `MANIFEST.in` so sdists include docs/examples/configs/tests and exclude
  smoke artifacts and bytecode.

v0.2 commit and release state:

- Commit: `1fe50dc Add Sarf Atlas v0.2 workflow commands`
- Git tag: `sarf-atlas-v0.2.0`
- Pushed to GitHub `main`.
- Published to PyPI:
  `https://pypi.org/project/sarf-atlas/0.2.0/`

v0.2 verification included:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q src
python3 -m build --sdist --wheel --outdir /tmp/sarf-atlas-0.2-dist
python3 -m twine check /tmp/sarf-atlas-0.2-dist/*
```

Because system Python is externally managed, build/twine were installed in a
temporary venv:

```bash
/tmp/sarf-atlas-0.2-buildenv
```

Clean wheel install and CLI smoke passed from:

```bash
/tmp/sarf-atlas-0.2-wheel
```

Archive inspection result:

- Wheel contains only runtime package files.
- sdist includes docs/examples/configs/tests.
- `smoke/`, `__pycache__`, local build dirs, and egg-info are not committed or
  shipped in the wheel.

### v0.3.0

Theme:

```text
Sarf Atlas v0.3: Paper-style morphology experiment workflow
```

Implemented and released:

- `sarf validate-dataset`
- `sarf make-prompts experiment.toml --out ...`
- `sarf make-splits experiment.toml --out ...`
- `sarf make-experiment experiment.toml --out ...`
- `sarf report run_dir --out ...`
- Paper-style dataset validation in `src/sarf/dataset.py`.
- Experiment config/scaffold support in `src/sarf/experiment.py`.
- Label-target prompt rendering.
- Deterministic lemma-heldout and root-heldout split metadata.
- Character-baseline metadata placeholder, explicitly not an implemented
  baseline runner.
- Backend config stub generation.
- Artifact manifest placeholder generation.
- Report summary output.
- Better artifact manifest path validation reporting present, missing, and
  placeholder paths.
- Paper-style docs in `docs/v0_3_paper_workflow.md`.
- Public example files:
  - `examples/paper_style/tiny_morphology.jsonl`
  - `examples/paper_style/experiment.toml`

v0.3 commit and release state:

- Main implementation commit:
  `44f184a Add Sarf Atlas v0.3 paper workflow support`
- Release-path fix commit:
  `a3b7bea Align v0.3 paper style release examples`
- Git tag: `sarf-atlas-v0.3.0`
- Pushed to GitHub `main`.
- Published to TestPyPI:
  `https://test.pypi.org/project/sarf-atlas/0.3.0/`
- Published to PyPI:
  `https://pypi.org/project/sarf-atlas/0.3.0/`

v0.3 verification included:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q src
/tmp/sarf-atlas-0.2-buildenv/bin/python -m build --sdist --wheel --outdir /tmp/sarf-atlas-0.3-dist
/tmp/sarf-atlas-0.2-buildenv/bin/python -m twine check /tmp/sarf-atlas-0.3-dist/*
```

Clean local wheel smoke used:

```bash
python3 -m venv /tmp/sarf-atlas-0.3-test
. /tmp/sarf-atlas-0.3-test/bin/activate
python -m pip install /tmp/sarf-atlas-0.3-dist/sarf_atlas-0.3.0-py3-none-any.whl
sarf --help
sarf validate-dataset examples/paper_style/tiny_morphology.jsonl
sarf make-prompts examples/paper_style/experiment.toml --out /tmp/sarf-0.3/prompts.jsonl
sarf make-splits examples/paper_style/experiment.toml --out /tmp/sarf-0.3/splits.jsonl
sarf make-experiment examples/paper_style/experiment.toml --out /tmp/sarf-0.3/run
sarf report /tmp/sarf-0.3/run --out /tmp/sarf-0.3/report.md
```

Fresh TestPyPI install smoke used:

```bash
python3 -m venv /tmp/sarf-atlas-0.3-testpypi
/tmp/sarf-atlas-0.3-testpypi/bin/python -m pip install \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  sarf-atlas==0.3.0
/tmp/sarf-atlas-0.3-testpypi/bin/sarf validate-dataset examples/paper_style/tiny_morphology.jsonl
/tmp/sarf-atlas-0.3-testpypi/bin/sarf make-prompts examples/paper_style/experiment.toml --out /tmp/sarf-0.3-testpypi/prompts.jsonl
/tmp/sarf-atlas-0.3-testpypi/bin/sarf make-splits examples/paper_style/experiment.toml --out /tmp/sarf-0.3-testpypi/splits.jsonl
/tmp/sarf-atlas-0.3-testpypi/bin/sarf make-experiment examples/paper_style/experiment.toml --out /tmp/sarf-0.3-testpypi/run
/tmp/sarf-atlas-0.3-testpypi/bin/sarf report /tmp/sarf-0.3-testpypi/run --out /tmp/sarf-0.3-testpypi/report.md
```

Generated v0.3 files inspected:

- `/tmp/sarf-0.3/report.md`
- `/tmp/sarf-0.3/run/summary.json`
- `/tmp/sarf-0.3/run/backend.placeholder.toml`
- `/tmp/sarf-0.3/run/artifact_manifest.placeholder.json`
- `/tmp/sarf-0.3/splits.jsonl`

Important v0.3 truths:

- README and docs describe v0.3 behavior.
- The example dataset is tiny demonstration data, not Paper 1 data.
- Reports explicitly state that Sarf v0.3 does not train probes, run models,
  extract hidden states, or claim paper reproduction.
- Backend configs are visibly placeholder stubs and include
  `no_hidden_states = true`.
- Character-baseline metadata is marked `placeholder`.
- Missing optional artifact paths are reported honestly as `present: false`.
- Hidden-state extraction remains backend land.

### Release Commands Used

TestPyPI upload:

```bash
/tmp/sarf-atlas-0.2-buildenv/bin/python -m twine upload \
  --repository testpypi \
  --non-interactive \
  /tmp/sarf-atlas-0.3-dist/*
```

Real PyPI upload:

```bash
/tmp/sarf-atlas-0.2-buildenv/bin/python -m twine upload \
  --non-interactive \
  /tmp/sarf-atlas-0.3-dist/*
```

Git tag/push:

```bash
git tag sarf-atlas-v0.3.0
git push origin main
git push origin sarf-atlas-v0.3.0
```

Current `main` after the v0.3 release:

```text
a3b7bea
```
