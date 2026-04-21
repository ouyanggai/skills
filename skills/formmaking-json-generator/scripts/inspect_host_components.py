#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from discover_context import discover, merge_context, read_existing


IMPORT_RE = re.compile(r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]")
REGISTRATION_RE = re.compile(
    r"name:\s*'([^']+)'\s*,\s*component:\s*(\w+)",
    re.S,
)

VALUE_TYPE_RE = re.compile(r"\btype\s*:\s*(\[[^\]]+\]|\w+)")

JSON_STRING_HINT_RE = re.compile(
    r"JSON\.parse\((?:this\.)?(?:value|currentInfoObj|val)[^)]*\)|typeof\s+this\.value\s*===\s*'string'",
    re.S,
)

HOST_MODEL_HINTS: list[tuple[str, list[str]]] = [
    (r"包含了?userName|包含userName", ["userName", "depName", "companyName", "dutyName"]),
    (r"singleSelect.*mulSelect|mulSelect.*singleSelect", ["singleSelect", "mulSelect"]),
]

BUSINESS_COMPONENT_NAMES = {
    "request_payout",
    "in-bound-material-select",
    "out-bound-material-select",
    "legal-contract-doctable",
    "contract-seal-review-business",
}


def remove_comments(text: str) -> str:
    chars: list[str] = []
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escape = False
    index = 0

    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
                chars.append(char)
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            if char == "\n":
                chars.append(char)
            index += 1
            continue

        if in_single:
            chars.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_single = False
            index += 1
            continue

        if in_double:
            chars.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_double = False
            index += 1
            continue

        if in_template:
            chars.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "`":
                in_template = False
            index += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue
        if char == "'":
            in_single = True
            chars.append(char)
            index += 1
            continue
        if char == '"':
            in_double = True
            chars.append(char)
            index += 1
            continue
        if char == "`":
            in_template = True
            chars.append(char)
            index += 1
            continue

        chars.append(char)
        index += 1

    return "".join(chars)


def resolve_import_path(main_js: Path, import_value: str) -> Path:
    if import_value.startswith("@/"):
        base = main_js.parent / import_value[2:]
    else:
        base = (main_js.parent / import_value).resolve()

    if base.exists() and base.is_file():
        return base.resolve()

    candidates = [
        base.with_suffix(".vue"),
        base.with_suffix(".js"),
        base / "index.vue",
        base / "index.js",
        base,
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def find_marker_array(text: str, marker: str) -> str:
    marker_index = text.find(marker)
    if marker_index < 0:
        return ""
    array_start = text.find("[", marker_index)
    if array_start < 0:
        return ""
    array_end = find_matching_bracket(text, array_start, "[", "]")
    if array_end < 0:
        return ""
    return text[array_start : array_end + 1]


def find_matching_bracket(text: str, start: int, open_char: str, close_char: str) -> int:
    depth = 0
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escape = False

    for index in range(start, len(text)):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
            continue

        if in_single:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_single = False
            continue

        if in_double:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_double = False
            continue

        if in_template:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "`":
                in_template = False
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            continue
        if char == "'":
            in_single = True
            continue
        if char == '"':
            in_double = True
            continue
        if char == "`":
            in_template = True
            continue

        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index

    return -1


def extract_top_level_objects(array_text: str) -> list[str]:
    objects: list[str] = []
    if not array_text:
        return objects

    depth = 0
    start = -1
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escape = False

    for index, char in enumerate(array_text):
        next_char = array_text[index + 1] if index + 1 < len(array_text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
            continue

        if in_single:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_single = False
            continue

        if in_double:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_double = False
            continue

        if in_template:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "`":
                in_template = False
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            continue
        if char == "'":
            in_single = True
            continue
        if char == '"':
            in_double = True
            continue
        if char == "`":
            in_template = True
            continue

        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                objects.append(array_text[start : index + 1])
                start = -1

    return objects


def extract_named_object_literal(text: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*\{{", text)
    if not match:
        return ""
    start = match.end() - 1
    end = find_matching_bracket(text, start, "{", "}")
    if end < 0:
        return ""
    return text[start : end + 1]


def extract_named_string(text: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*['\"]([^'\"]*)['\"]", text)
    return match.group(1).strip() if match else ""


def extract_top_level_keys(object_text: str) -> list[str]:
    keys: list[str] = []
    if not object_text:
        return keys

    depth = 0
    in_single = False
    in_double = False
    in_template = False
    in_line_comment = False
    in_block_comment = False
    escape = False
    index = 0

    while index < len(object_text):
        char = object_text[index]
        next_char = object_text[index + 1] if index + 1 < len(object_text) else ""

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if in_single:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "'":
                in_single = False
            index += 1
            continue

        if in_double:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_double = False
            index += 1
            continue

        if in_template:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "`":
                in_template = False
            index += 1
            continue

        if char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue
        if char == "'":
            in_single = True
            index += 1
            continue
        if char == '"':
            in_double = True
            index += 1
            continue
        if char == "`":
            in_template = True
            index += 1
            continue

        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            index += 1
            continue

        if depth == 1 and (char.isalpha() or char == "_"):
            start = index
            index += 1
            while index < len(object_text) and (
                object_text[index].isalnum() or object_text[index] == "_"
            ):
                index += 1
            key = object_text[start:index]
            while index < len(object_text) and object_text[index].isspace():
                index += 1
            if index < len(object_text) and object_text[index] == ":":
                keys.append(key)
            continue

        index += 1

    return keys


def parse_main_registry(host_project: Path) -> dict[str, dict[str, str]]:
    main_js = host_project / "src" / "main.js"
    text = remove_comments(main_js.read_text(encoding="utf-8"))
    imports = {
        name: str(resolve_import_path(main_js, import_path))
        for name, import_path in IMPORT_RE.findall(text)
    }
    registry: dict[str, dict[str, str]] = {}
    for el, import_name in REGISTRATION_RE.findall(text):
        if el in registry:
            continue
        registry[el] = {
            "import_name": import_name,
            "source_file": imports.get(import_name, ""),
        }
    return registry


def parse_custom_json(host_project: Path) -> dict[str, dict[str, Any]]:
    path = host_project / "src" / "components" / "Custom" / "customJson.js"
    text = remove_comments(path.read_text(encoding="utf-8"))
    array_text = find_marker_array(text, "const customJson")
    components: dict[str, dict[str, Any]] = {}
    for obj in extract_top_level_objects(array_text):
        if extract_named_string(obj, "type") != "custom":
            continue
        el = extract_named_string(obj, "el")
        if not el:
            continue
        options_block = extract_named_object_literal(obj, "options")
        extend_props_block = extract_named_object_literal(options_block, "extendProps")
        custom_props_block = extract_named_object_literal(options_block, "customProps")
        events_block = extract_named_object_literal(obj, "events")
        components[el] = {
            "name": extract_named_string(obj, "name"),
            "option_keys": extract_top_level_keys(options_block),
            "extend_prop_keys": extract_top_level_keys(extend_props_block),
            "custom_prop_keys": extract_top_level_keys(custom_props_block),
            "event_names": extract_top_level_keys(events_block),
            "custom_class": extract_named_string(options_block, "customClass"),
        }
    return components


def parse_prop_types(props_block: str, prop_name: str) -> list[str]:
    prop_block = extract_named_object_literal(props_block, prop_name)
    if not prop_block:
        return []
    match = VALUE_TYPE_RE.search(prop_block)
    if not match:
        return []
    raw = match.group(1).strip()
    if raw.startswith("[") and raw.endswith("]"):
        return [item.strip() for item in raw[1:-1].split(",") if item.strip()]
    return [raw]


def detect_model_hints(text: str) -> list[str]:
    hints: list[str] = []
    for pattern, items in HOST_MODEL_HINTS:
        if re.search(pattern, text, re.I | re.S):
            for item in items:
                if item not in hints:
                    hints.append(item)
    return hints


def inspect_component_source(source_file: str) -> dict[str, Any]:
    path = Path(source_file)
    if not source_file or not path.exists():
        return {
            "component_name": "",
            "prop_names": [],
            "value_prop_types": [],
            "tags": [],
            "model_hints": [],
            "comment_hints": [],
        }

    raw_text = path.read_text(encoding="utf-8")
    text = remove_comments(raw_text)
    props_block = extract_named_object_literal(text, "props")
    prop_names = extract_top_level_keys(props_block)
    value_prop_types = parse_prop_types(props_block, "value")

    tags: list[str] = []
    if JSON_STRING_HINT_RE.search(raw_text):
        tags.append("json-string-value")
    if "printRead" in prop_names or "printRead" in text:
        tags.append("supports-print-read")
    if "__condition" in raw_text:
        tags.append("writes-virtual-condition")
    if "__formPersonId" in raw_text:
        tags.append("writes-virtual-form-person-id")
    if "$parent.$parent.validate()" in raw_text:
        tags.append("calls-parent-validate")
    if re.search(r"\$emit\(\s*['\"]onChange['\"]", raw_text):
        tags.append("emits-onChange")
    if "/Business/" in source_file or "\\Business\\" in source_file:
        tags.append("business-component")

    model_hints = detect_model_hints(raw_text)
    if model_hints:
        tags.append("semantic-model-required")

    comment_hints = [
        line.strip(" /")
        for line in raw_text.splitlines()
        if "字段" in line or "printRead" in line or "根据后端要求" in line
    ][:5]

    return {
        "component_name": extract_named_string(text, "name"),
        "prop_names": prop_names,
        "value_prop_types": value_prop_types,
        "tags": sorted(set(tags)),
        "model_hints": model_hints,
        "comment_hints": comment_hints,
    }


def collect_sample_counts(sample_dir: Path | None) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not sample_dir or not sample_dir.exists():
        return counts
    for path in sorted(sample_dir.glob("*.json")):
        text = path.read_text(encoding="utf-8")
        counts.update(re.findall(r'"el"\s*:\s*"([^"]+)"', text))
    return counts


def classify_risk(el: str, tags: list[str], extend_prop_keys: list[str]) -> str:
    if el in BUSINESS_COMPONENT_NAMES or "business-component" in tags or extend_prop_keys:
        return "业务专用"
    if any(
        tag in tags
        for tag in (
            "json-string-value",
            "semantic-model-required",
            "calls-parent-validate",
            "emits-onChange",
            "writes-virtual-condition",
            "writes-virtual-form-person-id",
        )
    ):
        return "宿主约束型"
    return "通用"


def value_shape(value_prop_types: list[str], tags: list[str]) -> str:
    lowered = {item.lower() for item in value_prop_types}
    if "json-string-value" in tags and "string" in lowered:
        return "JSON字符串"
    if "string" in lowered:
        return "字符串"
    if "array" in lowered:
        return "数组"
    if "object" in lowered:
        return "对象"
    if not value_prop_types:
        return "未知"
    return "/".join(value_prop_types)


def resolve_context(workspace: Path, host_project: str, sample_dir: str) -> dict[str, str]:
    config_file = workspace / ".formmaking-json-generator" / "context.json"
    existing = read_existing(config_file)
    discovered = discover(workspace)
    return merge_context(
        discovered,
        existing,
        {
            "host_project": host_project,
            "sample_dir": sample_dir,
        },
    )


def inspect_host_project(host_project: Path, sample_dir: Path | None = None) -> dict[str, Any]:
    registry = parse_main_registry(host_project)
    custom_json = parse_custom_json(host_project)
    sample_counts = collect_sample_counts(sample_dir)

    component_names = sorted(set(registry) | set(custom_json))
    components: list[dict[str, Any]] = []
    for el in component_names:
        registry_info = registry.get(el, {})
        custom_info = custom_json.get(el, {})
        source_info = inspect_component_source(registry_info.get("source_file", ""))
        tags = sorted(
            set(source_info["tags"])
            | (
                {"has-extend-props"}
                if custom_info.get("extend_prop_keys")
                else set()
            )
        )
        components.append(
            {
                "el": el,
                "label": custom_info.get("name", ""),
                "source_file": registry_info.get("source_file", ""),
                "source_component_name": source_info.get("component_name", ""),
                "sample_count": sample_counts.get(el, 0),
                "option_keys": custom_info.get("option_keys", []),
                "extend_prop_keys": custom_info.get("extend_prop_keys", []),
                "custom_prop_keys": custom_info.get("custom_prop_keys", []),
                "event_names": custom_info.get("event_names", []),
                "custom_class": custom_info.get("custom_class", ""),
                "prop_names": source_info.get("prop_names", []),
                "value_prop_types": source_info.get("value_prop_types", []),
                "value_shape": value_shape(
                    source_info.get("value_prop_types", []),
                    tags,
                ),
                "tags": tags,
                "model_hints": source_info.get("model_hints", []),
                "comment_hints": source_info.get("comment_hints", []),
                "risk_level": classify_risk(
                    el,
                    tags,
                    custom_info.get("extend_prop_keys", []),
                ),
            }
        )

    components.sort(key=lambda item: (-item["sample_count"], item["el"]))
    return {
        "host_project": str(host_project.resolve()),
        "sample_dir": str(sample_dir.resolve()) if sample_dir and sample_dir.exists() else "",
        "component_count": len(components),
        "components": components,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# 宿主自定义组件盘点",
        "",
        f"- 宿主工程：`{summary['host_project']}`",
        f"- 样本目录：`{summary['sample_dir'] or '未提供'}`",
        f"- 组件数量：`{summary['component_count']}`",
        "",
        "| 组件名 | 标签 | 样本数 | 值形态 | 风险级别 | 关键标签 |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in summary["components"]:
        tags = ", ".join(item["tags"][:4]) if item["tags"] else "-"
        label = item["label"] or "-"
        lines.append(
            f"| `{item['el']}` | {label} | {item['sample_count']} | {item['value_shape']} | {item['risk_level']} | {tags} |"
        )

    lines.extend(["", "## 组件细节", ""])
    for item in summary["components"]:
        lines.append(f"### `{item['el']}`")
        lines.append("")
        lines.append(f"- 标签：`{item['label'] or '-'}`")
        lines.append(f"- 源码文件：`{item['source_file'] or '-'}`")
        lines.append(f"- 样本数：`{item['sample_count']}`")
        lines.append(f"- 值形态：`{item['value_shape']}`")
        lines.append(f"- 风险级别：`{item['risk_level']}`")
        if item["prop_names"]:
            lines.append(f"- Props：`{', '.join(item['prop_names'])}`")
        if item["option_keys"]:
            lines.append(f"- 默认 option 键：`{', '.join(item['option_keys'])}`")
        if item["extend_prop_keys"]:
            lines.append(f"- extendProps 键：`{', '.join(item['extend_prop_keys'])}`")
        if item["event_names"]:
            lines.append(f"- 默认事件键：`{', '.join(item['event_names'])}`")
        if item["model_hints"]:
            lines.append(f"- model 命名线索：`{', '.join(item['model_hints'])}`")
        if item["tags"]:
            lines.append(f"- 自动识别标签：`{', '.join(item['tags'])}`")
        if item["comment_hints"]:
            lines.append(f"- 注释线索：`{' | '.join(item['comment_hints'])}`")
        lines.append("")
    return "\n".join(lines).replace("`-`", "-")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="盘点宿主工程里的 FormMaking 自定义组件契约")
    parser.add_argument("--workspace", default=".", help="当前工作区目录")
    parser.add_argument("--host-project", default="", help="宿主工程目录")
    parser.add_argument("--sample-dir", default="", help="可选：真实样本目录")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="输出格式",
    )
    parser.add_argument("--output", default="", help="可选：输出文件路径")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve()
    context = resolve_context(workspace, args.host_project, args.sample_dir)
    host_project = context.get("host_project", "")
    if not host_project:
        raise SystemExit("缺少宿主工程目录，请先运行 discover_context.py 或显式传入 --host-project")

    sample_dir = Path(context["sample_dir"]).resolve() if context.get("sample_dir") else None
    summary = inspect_host_project(Path(host_project), sample_dir)
    output_text = (
        json.dumps(summary, ensure_ascii=False, indent=2)
        if args.format == "json"
        else render_markdown(summary)
    )

    if args.output:
        output_path = Path(args.output).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text + "\n", encoding="utf-8")

    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
