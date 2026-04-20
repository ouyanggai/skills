#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


CONFIG_DIR = ".formmaking-json-generator"
CONFIG_NAME = "context.json"


def read_context_sample_dir(workspace: Path) -> Path | None:
    config_path = workspace.resolve() / CONFIG_DIR / CONFIG_NAME
    if not config_path.exists():
        return None
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    sample_dir = payload.get("sample_dir")
    if not isinstance(sample_dir, str) or not sample_dir.strip():
        return None
    path = Path(sample_dir).expanduser().resolve()
    return path if path.exists() else None


def discover_sample_dir(workspace: Path) -> Path | None:
    workspace = workspace.resolve()
    for candidate in [workspace, *workspace.parents[:5]]:
        sample_dir = read_context_sample_dir(candidate)
        if sample_dir is not None:
            return sample_dir

        fallback = candidate / "analysis" / "form-proxy-samples" / "raw"
        if fallback.exists():
            return fallback.resolve()

    return None


def walk_nodes(nodes: list[object] | None) -> Iterable[dict]:
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        yield node
        node_type = node.get("type")
        if node_type == "report":
            for row in node.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                for column in row.get("columns") or []:
                    if not isinstance(column, dict):
                        continue
                    yield from walk_nodes(column.get("list"))
        elif node_type == "grid":
            for column in node.get("columns") or []:
                if not isinstance(column, dict):
                    continue
                yield from walk_nodes(column.get("list"))
        elif node_type == "table":
            yield from walk_nodes(node.get("tableColumns"))
        elif node_type in {"subform", "inline", "dialog", "card", "group"}:
            yield from walk_nodes(node.get("list"))
        elif node_type in {"tabs", "collapse"}:
            for tab in node.get("tabs") or []:
                if not isinstance(tab, dict):
                    continue
                yield from walk_nodes(tab.get("list"))


def text_names_from_report(report: dict) -> list[str]:
    names: list[str] = []
    for row in report.get("rows") or []:
        if not isinstance(row, dict):
            continue
        for column in row.get("columns") or []:
            if not isinstance(column, dict):
                continue
            for child in column.get("list") or []:
                if (
                    isinstance(child, dict)
                    and child.get("type") == "text"
                    and isinstance(child.get("name"), str)
                    and child.get("name").strip()
                ):
                    names.append(child["name"])
    return names


def top_items(counter: Counter, limit: int) -> list[list[object]]:
    return [[key, value] for key, value in counter.most_common(limit)]


def analyze_sample_dir(sample_dir: Path, top_n: int = 20) -> dict[str, object]:
    sample_files = sorted(sample_dir.glob("*.json"))

    config_widths: Counter[str] = Counter()
    config_custom_classes: Counter[str] = Counter()
    label_positions: Counter[str] = Counter()
    label_cols: Counter[str] = Counter()
    form_shell_patterns: Counter[str] = Counter()
    style_classes: Counter[str] = Counter()
    style_snippets: Counter[str] = Counter()
    top_level_patterns: Counter[str] = Counter()
    text_custom_classes: Counter[str] = Counter()
    report_border_colors: Counter[str] = Counter()
    report_widths: Counter[str] = Counter()
    approval_shapes: Counter[str] = Counter()
    approval_examples: list[dict[str, object]] = []

    for sample_file in sample_files:
        payload = json.loads(sample_file.read_text(encoding="utf-8"))
        config = payload.get("config") or {}
        config_width = str(config.get("width", ""))
        config_custom_class = str(config.get("customClass", ""))
        label_position = str(config.get("labelPosition", ""))
        label_col = str(config.get("labelCol", ""))

        config_widths[config_width] += 1
        config_custom_classes[config_custom_class] += 1
        label_positions[label_position] += 1
        label_cols[label_col] += 1
        form_shell_patterns[
            f"width={config_width} | class={config_custom_class} | labelPosition={label_position} | labelCol={label_col}"
        ] += 1

        style_sheets = config.get("styleSheets") or ""
        if isinstance(style_sheets, str) and style_sheets.strip():
            for css_class in re.findall(r"\.([A-Za-z0-9_-]+)", style_sheets):
                style_classes[css_class] += 1
            for line in [item.strip() for item in style_sheets.splitlines() if item.strip()][:4]:
                style_snippets[line] += 1

        top_level_pattern = " -> ".join(
            node.get("type", "?")
            for node in payload.get("list") or []
            if isinstance(node, dict)
        )
        top_level_patterns[top_level_pattern] += 1

        for node in walk_nodes(payload.get("list")):
            if node.get("type") == "text":
                custom_class = (node.get("options") or {}).get("customClass")
                if isinstance(custom_class, str) and custom_class.strip():
                    text_custom_classes[custom_class] += 1

            if node.get("type") != "report":
                continue

            options = node.get("options") or {}
            report_border_colors[str(options.get("borderColor", ""))] += 1
            report_widths[str(options.get("width", ""))] += 1

            text_names = text_names_from_report(node)
            if not text_names:
                continue
            if (
                any("审批意见" in item for item in text_names)
                or sum("意见" in item for item in text_names) >= 2
                or sum("签字" in item for item in text_names) >= 2
            ):
                row_lengths = tuple(
                    len((row or {}).get("columns") or [])
                    for row in node.get("rows") or []
                )
                approval_shapes[f"rows={len(node.get('rows') or [])} | cols={row_lengths}"] += 1
                if len(approval_examples) < top_n:
                    approval_examples.append(
                        {
                            "file": sample_file.name,
                            "model": node.get("model"),
                            "rows": len(node.get("rows") or []),
                            "row_columns": list(row_lengths[:8]),
                            "titles": text_names[:12],
                        }
                    )

    return {
        "sample_count": len(sample_files),
        "config_widths": top_items(config_widths, top_n),
        "config_custom_classes": top_items(config_custom_classes, top_n),
        "label_positions": top_items(label_positions, top_n),
        "label_cols": top_items(label_cols, top_n),
        "form_shell_patterns": top_items(form_shell_patterns, top_n),
        "style_classes": top_items(style_classes, top_n),
        "style_snippets": top_items(style_snippets, top_n),
        "top_level_patterns": top_items(top_level_patterns, top_n),
        "text_custom_classes": top_items(text_custom_classes, top_n),
        "report_border_colors": top_items(report_border_colors, top_n),
        "report_widths": top_items(report_widths, top_n),
        "approval_shapes": top_items(approval_shapes, top_n),
        "approval_examples": approval_examples,
    }


def resolve_sample_dir(args: argparse.Namespace) -> Path | None:
    if args.sample_dir:
        return Path(args.sample_dir).expanduser().resolve()
    return discover_sample_dir(Path(args.workspace).expanduser().resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="分析真实 FormMaking 样本的布局、样式和审批区规律")
    parser.add_argument("--sample-dir", default="", help="样本 JSON 目录")
    parser.add_argument("--workspace", default=".", help="工作区目录，用于从 context.json 读取 sample_dir")
    parser.add_argument("--top", type=int, default=20, help="每个分布返回前 N 项")
    args = parser.parse_args(argv)

    sample_dir = resolve_sample_dir(args)
    if sample_dir is None:
        print("[ERROR] 未找到样本目录，请传入 --sample-dir 或先配置 context.json", file=sys.stderr)
        return 2
    if not sample_dir.exists():
        print(f"[ERROR] 样本目录不存在: {sample_dir}", file=sys.stderr)
        return 2

    result = analyze_sample_dir(sample_dir, top_n=args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
