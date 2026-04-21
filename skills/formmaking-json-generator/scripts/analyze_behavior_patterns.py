#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

from analyze_sample_patterns import discover_sample_dir, walk_nodes


TRACKED_ACTIONS = [
    "getValue",
    "getValues",
    "getData",
    "setData",
    "sendRequest",
    "refresh",
    "refreshDynamicValue",
    "refreshDynamicValueAll",
    "refreshFieldOptionData",
    "hide",
    "display",
    "disabled",
    "validate",
    "triggerEvent",
    "openDialog",
    "closeDialog",
    "setOptions",
    "setRules",
]


def top_items(counter: Counter, limit: int) -> list[list[object]]:
    return [[key, value] for key, value in counter.most_common(limit)]


def detect_actions(func: str) -> list[str]:
    found: list[str] = []
    for action in TRACKED_ACTIONS:
        if action in func:
            found.append(action)
    if "$fm.show" in func and "openDialog" not in found:
        found.append("openDialog")
    return found


def classify_behavior(actions: list[str], func: str) -> list[str]:
    tags: list[str] = []
    action_set = set(actions)

    if "sendRequest" in action_set:
        tags.append("远程请求")
    if "setData" in action_set and ("getValue" in action_set or "getValues" in action_set):
        tags.append("计算回填")
    elif "setData" in action_set:
        tags.append("直接回填")
    if {"hide", "display", "disabled"} & action_set:
        tags.append("显隐禁用")
    if {"refresh", "refreshDynamicValue", "refreshDynamicValueAll", "refreshFieldOptionData"} & action_set:
        tags.append("刷新联动")
    if "triggerEvent" in action_set:
        tags.append("事件串联")
    if "validate" in action_set:
        tags.append("校验触发")
    if {"openDialog", "closeDialog"} & action_set or "$fm.show" in func:
        tags.append("弹窗交互")
    if not tags:
        tags.append("其他函数")
    return tags


def iter_event_scripts(payload: dict) -> Iterable[dict]:
    config = payload.get("config") or {}
    for item in config.get("eventScript") or []:
        if isinstance(item, dict):
            yield item


def analyze_sample_dir(sample_dir: Path, top_n: int = 20) -> dict[str, object]:
    sample_files = sorted(sample_dir.glob("*.json"))

    forms_with_event_script = 0
    forms_with_data_source = 0
    forms_with_remote_data_source = 0
    forms_with_dynamic_value = 0

    event_script_types: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    behavior_tag_counts: Counter[str] = Counter()
    behavior_pattern_counts: Counter[str] = Counter()
    event_bindings: Counter[str] = Counter()
    data_source_methods: Counter[str] = Counter()
    data_source_auto_flags: Counter[str] = Counter()
    remote_data_source_field_types: Counter[str] = Counter()
    dynamic_value_types: Counter[str] = Counter()
    data_source_reference_counts: Counter[str] = Counter()

    request_func_count = 0
    response_func_count = 0
    behavior_examples: list[dict[str, object]] = []

    for sample_file in sample_files:
        payload = json.loads(sample_file.read_text(encoding="utf-8"))
        config = payload.get("config") or {}
        event_scripts = list(iter_event_scripts(payload))
        data_sources = list((config.get("dataSource") or []))

        if event_scripts:
            forms_with_event_script += 1
        if data_sources:
            forms_with_data_source += 1

        sample_has_remote = False
        sample_has_dynamic = False

        for event in event_scripts:
            script_type = "rule" if event.get("type") == "rule" else "func"
            event_script_types[script_type] += 1

            func = event.get("func")
            if isinstance(func, str) and func.strip():
                actions = detect_actions(func)
                for action in actions:
                    action_counts[action] += 1
                tags = classify_behavior(actions, func)
                for tag in tags:
                    behavior_tag_counts[tag] += 1
                behavior_pattern_counts[" + ".join(tags)] += 1
                if len(behavior_examples) < top_n:
                    behavior_examples.append(
                        {
                            "file": sample_file.name,
                            "key": event.get("key"),
                            "name": event.get("name"),
                            "actions": actions,
                            "behavior_tags": tags,
                            "func_preview": func[:320],
                        }
                    )

        for data_source in data_sources:
            if not isinstance(data_source, dict):
                continue
            method = str(data_source.get("method", "")).upper()
            if method:
                data_source_methods[method] += 1

            auto_value = data_source.get("auto")
            if auto_value is True:
                data_source_auto_flags["true"] += 1
            elif auto_value is False:
                data_source_auto_flags["false"] += 1
            else:
                data_source_auto_flags["missing"] += 1

            if data_source.get("requestFunc"):
                request_func_count += 1
            if data_source.get("responseFunc"):
                response_func_count += 1

        for node in walk_nodes(payload.get("list")):
            events = node.get("events")
            if isinstance(events, dict):
                for event_name, script_key in events.items():
                    if script_key:
                        event_bindings[f"{node.get('type', '?')}.{event_name}"] += 1

            options = node.get("options") or {}
            if not isinstance(options, dict):
                continue
            remote_ref = options.get("remoteDataSource")
            if isinstance(remote_ref, str) and remote_ref.strip():
                sample_has_remote = True
                remote_data_source_field_types[node.get("type", "?")] += 1
                data_source_reference_counts[remote_ref] += 1

            dynamic_type = options.get("dynamicValueType")
            if isinstance(dynamic_type, str) and dynamic_type.strip():
                sample_has_dynamic = True
                dynamic_value_types[dynamic_type] += 1

        if sample_has_remote:
            forms_with_remote_data_source += 1
        if sample_has_dynamic:
            forms_with_dynamic_value += 1

    return {
        "sample_count": len(sample_files),
        "forms_with_event_script": forms_with_event_script,
        "forms_with_data_source": forms_with_data_source,
        "forms_with_remote_data_source": forms_with_remote_data_source,
        "forms_with_dynamic_value": forms_with_dynamic_value,
        "event_script_types": top_items(event_script_types, top_n),
        "action_counts": top_items(action_counts, top_n),
        "behavior_tag_counts": top_items(behavior_tag_counts, top_n),
        "behavior_pattern_counts": top_items(behavior_pattern_counts, top_n),
        "event_bindings": top_items(event_bindings, top_n),
        "data_source_methods": top_items(data_source_methods, top_n),
        "data_source_auto_flags": top_items(data_source_auto_flags, top_n),
        "remote_data_source_field_types": top_items(remote_data_source_field_types, top_n),
        "dynamic_value_types": top_items(dynamic_value_types, top_n),
        "data_source_reference_counts": top_items(data_source_reference_counts, top_n),
        "request_func_count": request_func_count,
        "response_func_count": response_func_count,
        "behavior_examples": behavior_examples,
    }


def resolve_sample_dir(args: argparse.Namespace) -> Path | None:
    if args.sample_dir:
        return Path(args.sample_dir).expanduser().resolve()
    return discover_sample_dir(Path(args.workspace).expanduser().resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="分析真实 FormMaking 样本中的事件脚本、联动与数据源规律")
    parser.add_argument("--sample-dir", default="", help="样本 JSON 目录")
    parser.add_argument("--workspace", default=".", help="工作区目录，用于从 context.json 读取 sample_dir")
    parser.add_argument("--top", type=int, default=20, help="每个分布返回前 N 项")
    args = parser.parse_args(argv)

    sample_dir = resolve_sample_dir(args)
    if sample_dir is None:
        print(
            "[ERROR] 未找到样本目录；raw 样本仅用于当前使用者本机的本地增强学习。"
            "如果你只是要生成或校验表单，可以跳过这个分析脚本。",
            file=sys.stderr,
        )
        return 2
    if not sample_dir.exists():
        print(f"[ERROR] 样本目录不存在: {sample_dir}", file=sys.stderr)
        return 2

    result = analyze_sample_dir(sample_dir, top_n=args.top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
