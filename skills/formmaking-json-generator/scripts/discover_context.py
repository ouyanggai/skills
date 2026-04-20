#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable


CONFIG_DIR = ".formmaking-json-generator"
CONFIG_NAME = "context.json"
SKIP_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}


def resolve_path(value: str | None) -> str:
    if not value:
        return ""
    return str(Path(value).expanduser().resolve())


def walk_limited(root: Path, max_depth: int = 5) -> Iterable[Path]:
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        return

    root_depth = len(root.parts)
    for current, dirs, _files in os.walk(root):
        current_path = Path(current)
        depth = len(current_path.parts) - root_depth
        dirs[:] = [
            item
            for item in dirs
            if item not in SKIP_DIRS and not item.startswith(".")
        ]
        if depth > max_depth:
            dirs[:] = []
            continue
        yield current_path


def candidate_search_roots(start: Path) -> list[Path]:
    start = start.resolve()
    roots: list[Path] = []

    for item in [start, *start.parents[:4]]:
        if item.exists() and item.is_dir() and item not in roots:
            roots.append(item)

    for parent in start.parents[:3]:
        try:
            for child in parent.iterdir():
                if child.is_dir() and child.name not in SKIP_DIRS and child not in roots:
                    roots.append(child)
        except OSError:
            continue

    return roots


def looks_like_host_project(path: Path) -> bool:
    return (
        (path / "src" / "main.js").exists()
        and (path / "src" / "components" / "Custom").exists()
    )


def looks_like_formmaking_source(path: Path) -> bool:
    return (
        (path / "src" / "components" / "GenerateForm.vue").exists()
        and (path / "src" / "components" / "GenerateElementItem.vue").exists()
    )


def looks_like_sample_root(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any(path.glob("*.json"))


def discover(start: Path) -> dict[str, str]:
    context = {
        "workspace_root": str(start.resolve()),
        "host_project": "",
        "formmaking_source": "",
        "sample_dir": "",
    }

    for root in candidate_search_roots(start):
        for path in walk_limited(root):
            if not context["host_project"] and looks_like_host_project(path):
                context["host_project"] = str(path.resolve())
            if not context["formmaking_source"] and looks_like_formmaking_source(path):
                context["formmaking_source"] = str(path.resolve())

            sample_candidate = path / "analysis" / "form-proxy-samples" / "raw"
            if not context["sample_dir"] and looks_like_sample_root(sample_candidate):
                context["sample_dir"] = str(sample_candidate.resolve())

            if all(context.values()):
                return context

    return context


def context_path(workspace: Path) -> Path:
    return workspace.resolve() / CONFIG_DIR / CONFIG_NAME


def read_existing(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def merge_context(
    discovered: dict[str, str],
    existing: dict[str, str],
    overrides: dict[str, str],
) -> dict[str, str]:
    result = {**discovered, **{k: v for k, v in existing.items() if v}}
    for key, value in overrides.items():
        if value:
            result[key] = resolve_path(value)
    return result


def missing_items(context: dict[str, str]) -> list[str]:
    labels = {
        "host_project": "宿主工程路径",
        "formmaking_source": "FormMaking 源码路径",
        "sample_dir": "真实表单 JSON 样本目录",
    }
    return [label for key, label in labels.items() if not context.get(key)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="发现并保存 FormMaking skill 的本地上下文")
    parser.add_argument("--workspace", default=".", help="当前工作区目录")
    parser.add_argument("--host-project", default="", help="宿主工程路径")
    parser.add_argument("--formmaking-source", default="", help="FormMaking 源码路径")
    parser.add_argument("--sample-dir", default="", help="真实表单 JSON 样本目录")
    parser.add_argument("--print-only", action="store_true", help="只输出发现结果，不写入 context.json")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    config_file = context_path(workspace)
    discovered = discover(workspace)
    existing = read_existing(config_file)
    context = merge_context(
        discovered,
        existing,
        {
            "host_project": args.host_project,
            "formmaking_source": args.formmaking_source,
            "sample_dir": args.sample_dir,
        },
    )

    payload = {
        "context_file": str(config_file),
        "context": context,
        "missing": missing_items(context),
    }

    if not args.print_only:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(context, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
