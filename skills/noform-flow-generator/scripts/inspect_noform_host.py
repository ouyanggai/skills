#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


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

NAME_RE = re.compile(r"name\s*:\s*['\"]([^'\"]+)['\"]")
EXPORT_DEFAULT_NAME_RE = re.compile(
    r"export\s+default\s*\{[\s\S]*?\bname\s*:\s*['\"]([^'\"]+)['\"]",
    re.S,
)
CONFIG_IMPORT_RE = re.compile(r"from\s+['\"]\.\/config\/([^'\"]+)['\"]")
API_REF_RE = re.compile(r"Api\.[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+")
PROP_RE = re.compile(r"prop\s*:\s*['\"]([^'\"]+)['\"]")
TYPE_RE = re.compile(r"type\s*:\s*['\"]([^'\"]+)['\"]")
MIXIN_API_RE = re.compile(
    r"'([^']+)'\s*:\s*\{\s*save\s*:\s*([^,}]+?)\s*,\s*update\s*:\s*([^}]+?)\s*\}",
    re.S,
)


def safe_is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except OSError:
        return False


def safe_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def candidate_search_roots(start: Path) -> list[Path]:
    start = start.resolve()
    roots: list[Path] = []
    for item in [start, *start.parents[:4]]:
        if safe_exists(item) and safe_is_dir(item) and item not in roots:
            roots.append(item)
    for parent in start.parents[:3]:
        try:
            for child in parent.iterdir():
                if safe_is_dir(child) and child.name not in SKIP_DIRS and child not in roots:
                    roots.append(child)
        except OSError:
            continue
    return roots


def walk_limited(root: Path, max_depth: int = 4):
    root = root.resolve()
    if not safe_exists(root) or not safe_is_dir(root):
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


def looks_like_host_project(path: Path) -> bool:
    return (
        safe_exists(path / "src" / "components" / "NoFormFLow" / "mixin" / "mixin.js")
        and safe_exists(path / "src" / "views" / "flowLibrary" / "NoFormMulBranch" / "index.vue")
        and safe_exists(path / "src" / "api" / "index.js")
    )


def discover_host_project(workspace: Path) -> Path | None:
    for root in candidate_search_roots(workspace):
        for path in walk_limited(root):
            if looks_like_host_project(path):
                return path.resolve()
    return None


def parse_name(text: str) -> str:
    match = EXPORT_DEFAULT_NAME_RE.search(text)
    if match:
        return match.group(1)
    match = NAME_RE.search(text)
    return match.group(1) if match else ""


def remove_comments(text: str) -> str:
    text = re.sub(r"<!--[\s\S]*?-->", "", text)
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    text = re.sub(r"(^|\s)//.*?$", "", text, flags=re.M)
    return text


def parse_list_props(text: str) -> list[str]:
    return sorted(set(PROP_RE.findall(text)))


def parse_type_counts(text: str) -> list[list[object]]:
    counter = Counter(TYPE_RE.findall(text))
    return [[key, value] for key, value in counter.most_common()]


def parse_api_refs(text: str) -> list[str]:
    return sorted(set(API_REF_RE.findall(text)))


def parse_mixin_api_map(text: str) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    for key, save_ref, update_ref in MIXIN_API_RE.findall(text):
        mapping[key] = {
            "save": save_ref.strip(),
            "update": update_ref.strip(),
        }
    return mapping


def summarize_config(path: Path) -> dict[str, Any]:
    text = remove_comments(path.read_text(encoding="utf-8"))
    props = parse_list_props(text)
    return {
        "file": str(path),
        "field_props": props,
        "field_prop_count": len(props),
        "type_counts": parse_type_counts(text),
        "rules_count": len(re.findall(r"rules\s*:", text)),
        "slot_count": len(re.findall(r"slot\s*:", text)),
        "children_count": len(re.findall(r"children\s*:", text)),
        "disabled_true_count": len(re.findall(r"disabled\s*:\s*true", text)),
    }


def summarize_component(path: Path, mixin_api_map: dict[str, dict[str, str]]) -> dict[str, Any]:
    text = remove_comments(path.read_text(encoding="utf-8"))
    name = parse_name(text)
    config_imports = [f"{item}.js" for item in CONFIG_IMPORT_RE.findall(text)]
    uses = {
        "mixin": "mixins:[" in text or "mixins: [" in text,
        "flow": "Flow" in text and "ref=\"flow\"" in text,
        "common_form": "CommonForm" in text,
        "simple_table": "SimpleTable" in text,
        "common_footer": "CommonFooter" in text,
        "upload": "elupload" in text or "EleUpload" in text,
    }
    methods = {
        "processData": bool(re.search(r"\bprocessData\s*\(", text)),
        "processSaveData": bool(re.search(r"\bprocessSaveData\s*\(", text)),
        "insertDataToForm": bool(re.search(r"\binsertDataToForm\s*\(", text)),
        "setDisableData": bool(re.search(r"\bsetDisableData\s*\(", text)),
        "getInputPermision": "getInputPermision" in text,
    }
    return {
        "name": name,
        "file": str(path),
        "config_imports": config_imports,
        "api_refs": parse_api_refs(text),
        "uses": uses,
        "methods": methods,
        "has_api_mapping": name in mixin_api_map if name else False,
    }


def inspect_host_project(host_project: Path) -> dict[str, Any]:
    noform_root = host_project / "src" / "components" / "NoFormFLow"
    config_root = noform_root / "config"
    mixin_path = noform_root / "mixin" / "mixin.js"
    flow_library_root = host_project / "src" / "views" / "flowLibrary" / "NoFormMulBranch"

    mixin_text = mixin_path.read_text(encoding="utf-8")
    mixin_api_map = parse_mixin_api_map(mixin_text)

    config_summaries = [
        summarize_config(path)
        for path in sorted(config_root.glob("*.js"))
    ]
    components = [
        summarize_component(path, mixin_api_map)
        for path in sorted(noform_root.glob("*.vue"))
    ]

    config_names = {item["file"].split("/")[-1] for item in config_summaries}
    component_names = {item["name"] for item in components if item["name"]}
    warnings: list[str] = []

    for component in components:
        if not component["name"]:
            warnings.append(f"{Path(component['file']).name} 缺少组件 name")
            continue
        if not component["has_api_mapping"]:
            warnings.append(f"{component['name']} 未在 mixin.js 的 apiList 中注册保存/更新接口")
        for config_name in component["config_imports"]:
            if config_name not in config_names:
                warnings.append(f"{component['name']} 引用了不存在的配置文件 {config_name}")
        if not component["uses"]["flow"]:
            warnings.append(f"{component['name']} 未检测到标准 Flow 提交流程挂载")

    for api_key in sorted(mixin_api_map):
        if api_key not in component_names:
            warnings.append(f"mixin.js 中的 apiList key `{api_key}` 没有对应的无表单组件文件")

    all_props = Counter()
    all_types = Counter()
    for item in config_summaries:
        for prop in item["field_props"]:
            all_props[prop] += 1
        for type_name, count in item["type_counts"]:
            all_types[type_name] += int(count)

    flow_library_files = sorted(flow_library_root.rglob("*.vue"))
    return {
        "host_project": str(host_project.resolve()),
        "noform_root": str(noform_root.resolve()),
        "flow_library_root": str(flow_library_root.resolve()),
        "business_component_count": len(components),
        "business_components": components,
        "mixin_api_map": mixin_api_map,
        "config_count": len(config_summaries),
        "config_summaries": config_summaries,
        "common_field_props": [[key, value] for key, value in all_props.most_common(20)],
        "common_type_counts": [[key, value] for key, value in all_types.most_common()],
        "flow_library_files": [str(path) for path in flow_library_files],
        "warnings": warnings,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# 无表单宿主盘点",
        "",
        f"- 宿主目录：`{summary['host_project']}`",
        f"- 业务组件数：`{summary['business_component_count']}`",
        f"- 配置文件数：`{summary['config_count']}`",
        "",
        "## 业务组件",
        "",
    ]
    for item in summary["business_components"]:
        lines.append(f"- `{item['name']}`")
        lines.append(f"  文件：`{item['file']}`")
        lines.append(f"  配置：`{', '.join(item['config_imports']) or '无'}`")
        lines.append(f"  API：`{', '.join(item['api_refs'][:6]) or '无'}`")
    lines.extend(["", "## 警告", ""])
    if summary["warnings"]:
        for warning in summary["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- 未发现明显结构问题")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="盘点宿主项目中的无表单流程实现")
    parser.add_argument("--workspace", default=".", help="工作区目录，用于自动发现宿主项目")
    parser.add_argument("--host-project", default="", help="显式指定宿主项目目录")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="输出格式")
    parser.add_argument("--output", default="", help="输出文件路径")
    args = parser.parse_args(argv)

    host_project = (
        Path(args.host_project).expanduser().resolve()
        if args.host_project
        else discover_host_project(Path(args.workspace).expanduser().resolve())
    )
    if host_project is None:
        print("[ERROR] 未找到宿主项目，请传入 --host-project 或在工作区附近放置 rsh-cloud-invest-power-system* 目录", file=sys.stderr)
        return 2
    if not looks_like_host_project(host_project):
        print(f"[ERROR] 目录不是有效的无表单宿主项目: {host_project}", file=sys.stderr)
        return 2

    summary = inspect_host_project(host_project)
    content = json.dumps(summary, ensure_ascii=False, indent=2)
    if args.format == "markdown":
        content = render_markdown(summary)

    if args.output:
        Path(args.output).expanduser().resolve().write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
