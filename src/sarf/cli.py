from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .dataset import validate_dataset_rows
from .ember_config import write_ember_config
from .experiment import (
    make_prompts_from_experiment,
    make_splits_from_experiment,
    render_experiment_markdown,
    write_experiment_scaffold,
)
from .io import read_jsonl, write_json, write_jsonl
from .prompts import make_prompts
from .project import init_project
from .splits import lemma_heldout_split
from .summary import summarize_manifest
from .toy import toy_records
from .validation import validate_run
from .workflow import DEFAULT_TEMPLATE, write_example_workflow
from .artifacts import validate_manifest
from .backends import llama_cpp
from .backends import ember as ember_backend
from .backends.ember import import_ember_run
from .backends.files import import_files


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _print_capabilities(capabilities: dict[str, bool]) -> None:
    print("capabilities:")
    for name in ["tokenization", "logits", "hidden_states", "validate_run"]:
        if name in capabilities:
            print(f"  {name}: {_yes_no(bool(capabilities[name]))}")


def _print_llama_cpp_status(status: dict[str, object]) -> None:
    print("llama.cpp")
    print(f"available: {_yes_no(bool(status['available']))}")
    print("binaries:")
    for name in ["tokenize", "cli", "simple"]:
        binary = status["binaries"][name]  # type: ignore[index]
        path = binary["path"] or "missing"
        source = f" ({binary['source']})" if binary["source"] else ""
        env_path = f", {binary['env_var']}={binary['env_path']}" if binary["env_path"] else ""
        print(f"  {name}: {path}{source}{env_path}")
    missing = status["missing_binaries"]
    print(f"missing binaries: {', '.join(missing) if missing else 'none'}")  # type: ignore[arg-type]
    _print_capabilities(status["capabilities"])  # type: ignore[arg-type]
    print("caveats:")
    for caveat in status["caveats"]:  # type: ignore[union-attr]
        print(f"  - {caveat}")


def _print_ember_status(status: dict[str, object]) -> None:
    print("Ember")
    print(f"available: {_yes_no(bool(status['available']))}")
    binary = status["binary"]  # type: ignore[assignment]
    path = binary["path"] or "missing"
    source = f" ({binary['source']})" if binary["source"] else ""
    env_path = f", {binary['env_var']}={binary['env_path']}" if binary["env_path"] else ""
    print(f"binary: {path}{source}{env_path}")
    missing = status["missing_binaries"]
    print(f"missing binaries: {', '.join(missing) if missing else 'none'}")  # type: ignore[arg-type]
    validate_run = status["validate_run"]  # type: ignore[assignment]
    print(
        "validate-run help: "
        f"{'callable' if validate_run['callable'] else 'not callable'}"
        f"{' (not checked)' if not validate_run['checked'] else ''}"
    )
    if validate_run["error"]:
        print(f"validate-run error: {validate_run['error']}")
    _print_capabilities(status["capabilities"])  # type: ignore[arg-type]
    print("caveats:")
    for caveat in status["caveats"]:  # type: ignore[union-attr]
        print(f"  - {caveat}")


def _print_backends_list() -> None:
    llama_status = llama_cpp.detect()
    ember_status = ember_backend.detect()
    print("Sarf backend availability")
    print(f"llama.cpp: {_yes_no(bool(llama_status['available']))}")
    print(f"Ember: {_yes_no(bool(ember_status['available']))}")
    print()
    _print_llama_cpp_status(llama_status)
    print()
    _print_ember_status(ember_status)


def entrypoint(argv: list[str] | None = None) -> int:
    try:
        return main(argv)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sarf",
        description="Backend-agnostic workflow scaffolding for Arabic morphology probing.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create a clean Sarf v0.3 project layout")
    p.add_argument("path", nargs="?", help="project directory to create or update")
    p.add_argument("--out-dir", default=".", help="project directory to create or update")
    p.add_argument("--name", default="sarf-project", help="project name written to sarf.project.json")
    p.add_argument("--force", action="store_true", help="allow adding layout files to a non-empty directory")

    p = sub.add_parser("toy-dataset", help="write the bundled toy morphology dataset")
    p.add_argument("--out", required=True, help="output JSONL path")

    p = sub.add_parser("validate-dataset", help="validate a Paper-style morphology JSONL dataset")
    p.add_argument("input", help="input morphology JSONL")
    p.add_argument("--out", help="optional validation report JSON")

    p = sub.add_parser("make-prompts", help="render prompt JSONL from records or an experiment TOML")
    p.add_argument("experiment", nargs="?", help="experiment TOML")
    p.add_argument("--input", help="input morphology JSONL")
    p.add_argument("--out", required=True, help="output prompt JSONL")
    p.add_argument("--template", default=DEFAULT_TEMPLATE, help="Python format prompt template")

    p = sub.add_parser("make-splits", help="write Paper-style split metadata from an experiment TOML")
    p.add_argument("experiment", help="experiment TOML")
    p.add_argument("--out", required=True, help="output split metadata JSON")

    p = sub.add_parser("make-experiment", help="write a Paper-style experiment scaffold from TOML")
    p.add_argument("experiment", help="experiment TOML")
    p.add_argument("--out", required=True, help="output run directory")

    p = sub.add_parser("report", help="write a readable experiment report")
    p.add_argument("run_dir", help="experiment run directory")
    p.add_argument("--out", required=True, help="output Markdown report path")

    p = sub.add_parser("split-metadata", help="assign toy lemma-heldout splits and metadata")
    p.add_argument("--input", required=True, help="input morphology JSONL")
    p.add_argument("--out-records", required=True, help="output split morphology JSONL")
    p.add_argument("--out-metadata", required=True, help="output split metadata JSON")

    p = sub.add_parser("ember-config", help="write an Ember extraction config placeholder")
    p.add_argument("--out", required=True, help="output TOML path")
    p.add_argument("--run-id", default="sarf-v01-toy-native-logits", help="Ember run_id")
    p.add_argument("--model-path", default="/path/to/model.gguf", help="local GGUF path placeholder")
    p.add_argument("--tokenizer-path", default="/path/to/tokenizer.json", help="local tokenizer JSON path placeholder")
    p.add_argument("--prompts-path", required=True, help="prompt JSONL path")
    p.add_argument("--output-dir", required=True, help="Ember output directory")
    p.add_argument("--backend", default="native", help="Ember backend name")
    p.add_argument("--architecture", default="qwen3", help="model architecture hint")
    p.add_argument("--no-logits", action="store_true", help="set write_logits = false")

    p = sub.add_parser("validate-artifact", help="run Ember validate-run for an artifact directory")
    p.add_argument("--run-dir", required=True, help="Ember artifact run directory")
    p.add_argument("--repo-root", default=".", help="repository root containing Cargo.toml")

    p = sub.add_parser("import-ember", help="import an Ember run as a Sarf artifact manifest")
    p.add_argument("--run-dir", required=True, help="Ember artifact run directory")
    p.add_argument("--out", required=True, help="output Sarf artifact manifest JSON")
    p.add_argument("--run-id", help="override Sarf run id")

    p = sub.add_parser("import-files", help="create a Sarf manifest from precomputed files")
    p.add_argument("--run-id", required=True, help="Sarf run id")
    p.add_argument("--prompts-path", required=True, help="prompt/sample artifact path")
    p.add_argument("--out", required=True, help="output Sarf artifact manifest JSON")
    p.add_argument("--tokenization-path", help="optional tokenization artifact path")
    p.add_argument("--positions-path", help="optional positions artifact path")
    p.add_argument("--logits-path", help="optional logits artifact path")
    p.add_argument("--hidden-states-path", help="optional hidden-state artifact path")
    p.add_argument("--report-path", help="optional report artifact path")

    p = sub.add_parser("import-artifacts", help="import backend artifacts as a Sarf manifest")
    p.add_argument("--from", dest="source", choices=["ember", "files"], required=True, help="artifact source type")
    p.add_argument("--out", required=True, help="output Sarf artifact manifest JSON")
    p.add_argument("--run-id", help="Sarf run id or override")
    p.add_argument("--run-dir", help="Ember artifact run directory when --from ember")
    p.add_argument("--prompts-path", help="prompt/sample artifact path when --from files")
    p.add_argument("--tokenization-path", help="optional tokenization artifact path")
    p.add_argument("--positions-path", help="optional positions artifact path")
    p.add_argument("--logits-path", help="optional logits artifact path")
    p.add_argument("--hidden-states-path", help="optional hidden-state artifact path")
    p.add_argument("--report-path", help="optional report artifact path")

    p = sub.add_parser("validate-manifest", help="validate a Sarf artifact manifest JSON")
    p.add_argument("--manifest", required=True, help="Sarf artifact manifest JSON")
    p.add_argument("--out", help="optional validation report JSON")

    p = sub.add_parser("summarize-run", help="summarize a Sarf artifact manifest")
    p.add_argument("target", nargs="?", help="Sarf artifact manifest JSON or project directory")
    p.add_argument("--manifest", help="Sarf artifact manifest JSON")
    p.add_argument("--out", help="optional summary JSON output path")

    p = sub.add_parser("backends", help="inspect optional local backend availability")
    backends_sub = p.add_subparsers(dest="backends_command", required=True)
    backends_sub.add_parser("list", help="list optional backend detection results")

    p = sub.add_parser("backend", help="inspect one optional local backend")
    backend_sub = p.add_subparsers(dest="backend_name", required=True)
    llama_parser = backend_sub.add_parser("llama-cpp", help="inspect llama.cpp availability")
    llama_sub = llama_parser.add_subparsers(dest="backend_command", required=True)
    llama_sub.add_parser("doctor", help="show llama.cpp detection details")
    ember_parser = backend_sub.add_parser("ember", help="inspect Ember availability")
    ember_sub = ember_parser.add_subparsers(dest="backend_command", required=True)
    ember_sub.add_parser("doctor", help="show Ember detection details")

    p = sub.add_parser("example-workflow", help="write the complete toy workflow scaffold")
    p.add_argument("--out-dir", required=True, help="output workflow directory")

    args = parser.parse_args(argv)
    if args.command == "init":
        init_project(args.path or args.out_dir, name=args.name, force=args.force)
    elif args.command == "toy-dataset":
        write_jsonl(args.out, toy_records())
    elif args.command == "validate-dataset":
        report = validate_dataset_rows(read_jsonl(args.input))
        if args.out:
            write_json(args.out, report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1
    elif args.command == "make-prompts":
        if args.experiment:
            write_jsonl(args.out, make_prompts_from_experiment(args.experiment))
        elif args.input:
            write_jsonl(args.out, make_prompts(read_jsonl(args.input), args.template))
        else:
            raise ValueError("make-prompts requires an experiment TOML or --input")
    elif args.command == "make-splits":
        write_json(args.out, make_splits_from_experiment(args.experiment))
    elif args.command == "make-experiment":
        write_experiment_scaffold(args.experiment, args.out)
    elif args.command == "report":
        summary_path = Path(args.run_dir) / "summary.json"
        if not summary_path.exists():
            summary_path = Path(args.run_dir) / "experiment.summary.json"
        if not summary_path.exists():
            raise ValueError(f"missing experiment summary: {summary_path}")
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(render_experiment_markdown(summary), encoding="utf-8")
    elif args.command == "split-metadata":
        records, metadata = lemma_heldout_split(read_jsonl(args.input))
        write_jsonl(args.out_records, records)
        write_json(args.out_metadata, metadata)
    elif args.command == "ember-config":
        write_ember_config(
            args.out,
            run_id=args.run_id,
            model_path=args.model_path,
            tokenizer_path=args.tokenizer_path,
            prompts_path=args.prompts_path,
            output_dir=args.output_dir,
            backend=args.backend,
            architecture=args.architecture,
            write_logits=not args.no_logits,
        )
    elif args.command == "validate-artifact":
        return validate_run(args.run_dir, repo_root=args.repo_root)
    elif args.command == "import-ember":
        write_json(args.out, import_ember_run(args.run_dir, run_id=args.run_id).to_dict())
    elif args.command == "import-files":
        write_json(
            args.out,
            import_files(
                run_id=args.run_id,
                prompts_path=args.prompts_path,
                tokenization_path=args.tokenization_path,
                positions_path=args.positions_path,
                logits_path=args.logits_path,
                hidden_states_path=args.hidden_states_path,
                report_path=args.report_path,
            ).to_dict(),
        )
    elif args.command == "import-artifacts":
        if args.source == "ember":
            if not args.run_dir:
                raise ValueError("--run-dir is required when --from ember")
            manifest = import_ember_run(args.run_dir, run_id=args.run_id)
        else:
            if not args.run_id:
                raise ValueError("--run-id is required when --from files")
            if not args.prompts_path:
                raise ValueError("--prompts-path is required when --from files")
            manifest = import_files(
                run_id=args.run_id,
                prompts_path=args.prompts_path,
                tokenization_path=args.tokenization_path,
                positions_path=args.positions_path,
                logits_path=args.logits_path,
                hidden_states_path=args.hidden_states_path,
                report_path=args.report_path,
            )
        write_json(args.out, manifest.to_dict())
    elif args.command == "validate-manifest":
        report = validate_manifest(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
        if args.out:
            write_json(args.out, report)
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1
    elif args.command == "summarize-run":
        target = args.manifest or args.target
        if not target:
            raise ValueError("summarize-run requires a manifest path or project directory")
        target_path = Path(target)
        if target_path.is_dir():
            manifests = sorted((target_path / "artifacts" / "imported").glob("*.json"))
            summary = {
                "project_path": str(target_path),
                "manifest_count": len(manifests),
                "runs": [summarize_manifest(path) for path in manifests],
            }
        else:
            summary = summarize_manifest(target_path)
        if args.out:
            write_json(args.out, summary)
        else:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        if "validation" in summary:
            return 0 if summary["validation"]["passed"] else 1
        return 0
    elif args.command == "backends":
        if args.backends_command == "list":
            _print_backends_list()
    elif args.command == "backend":
        if args.backend_name == "llama-cpp" and args.backend_command == "doctor":
            _print_llama_cpp_status(llama_cpp.detect())
        elif args.backend_name == "ember" and args.backend_command == "doctor":
            _print_ember_status(ember_backend.detect())
    elif args.command == "example-workflow":
        write_example_workflow(args.out_dir)
    return 0
