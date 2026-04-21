#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from inspect_noform_host import (
    discover_host_project,
    inspect_host_project,
    looks_like_host_project,
    remove_comments,
)


MESSAGE_RE = re.compile(r"message\s*:\s*['\"]([^'\"]+)['\"]")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")
OPERA_TYPE_RE = re.compile(r"operaType\s*==\s*['\"](create|edit|examine|preview)['\"]")


def contains_chinese(text: str) -> bool:
    return bool(CHINESE_RE.search(text))


def collect_component_text(path: Path) -> str:
    return remove_comments(path.read_text(encoding="utf-8"))


def collect_config_text(path: Path) -> str:
    return remove_comments(path.read_text(encoding="utf-8"))


def validate_component(summary: dict[str, Any], component_name: str) -> dict[str, Any]:
    component = next((item for item in summary["business_components"] if item["name"] == component_name), None)
    if component is None:
        raise KeyError(component_name)

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    component_path = Path(component["file"])
    component_text = collect_component_text(component_path)

    if not component["name"]:
        errors.append({"file": str(component_path), "message": "缺少组件 name"})

    if not component["has_api_mapping"]:
        errors.append({"file": str(component_path), "message": "未在 mixin.js 的 apiList 中注册保存/更新接口"})

    if not component["uses"]["flow"]:
        errors.append({"file": str(component_path), "message": "未挂载标准 Flow 提交流程"})

    if not component["uses"]["common_footer"]:
        warnings.append({"file": str(component_path), "message": "未检测到 CommonFooter；请确认 create/edit 场景是否仍有统一底部操作区"})

    if not component["methods"]["processData"]:
        errors.append({"file": str(component_path), "message": "缺少 processData()，无法形成标准业务提交流程"})

    if not component["methods"]["processSaveData"]:
        warnings.append({"file": str(component_path), "message": "缺少 processSaveData()；编辑或重提场景可能无法合并原始数据"})

    if not component["methods"]["insertDataToForm"]:
        warnings.append({"file": str(component_path), "message": "缺少 insertDataToForm()；查看或审核态回显可能不完整"})

    if not component["methods"]["setDisableData"]:
        warnings.append({"file": str(component_path), "message": "缺少 setDisableData()；审核态字段权限可能无法按节点控制"})

    if "getInputPermision" not in component_text:
        warnings.append({"file": str(component_path), "message": "未检测到 getInputPermision 调用；请确认 examine 态是否按流程节点权限裁剪"})

    seen_modes = sorted(set(OPERA_TYPE_RE.findall(component_text)))
    missing_modes = [mode for mode in ["create", "edit", "examine", "preview"] if mode not in seen_modes]
    if len(missing_modes) >= 2:
        warnings.append(
            {
                "file": str(component_path),
                "message": f"未明显处理这些 operaType 分支: {', '.join(missing_modes)}",
            }
        )

    config_lookup = {Path(item["file"]).name: item for item in summary["config_summaries"]}
    for config_name in component["config_imports"]:
        config_item = config_lookup.get(config_name)
        if config_item is None:
            errors.append({"file": str(component_path), "message": f"引用的配置文件不存在: {config_name}"})
            continue
        config_path = Path(config_item["file"])
        config_text = collect_config_text(config_path)
        messages = MESSAGE_RE.findall(config_text)
        for message in messages:
            if not contains_chinese(message):
                warnings.append({"file": str(config_path), "message": f"存在非中文校验提示: {message}"})
        if config_item["field_prop_count"] == 0:
            warnings.append({"file": str(config_path), "message": "未检测到任何 prop 字段；请确认配置是否真的承载业务字段"})
        if config_item["rules_count"] == 0 and config_item["slot_count"] == 0:
            warnings.append({"file": str(config_path), "message": "未检测到 rules 或表格 slot；请确认页面是否真的不需要前端校验"})

    return {
        "component": component_name,
        "file": str(component_path),
        "errors": errors,
        "warnings": warnings,
    }


def validate_host_project(host_project: Path, component_filter: str = "") -> dict[str, Any]:
    summary = inspect_host_project(host_project)
    component_names = [item["name"] for item in summary["business_components"] if item["name"]]
    if component_filter:
        component_names = [name for name in component_names if name == component_filter]

    if component_filter and not component_names:
        raise KeyError(component_filter)

    reports = [validate_component(summary, name) for name in component_names]
    return {
        "host_project": str(host_project.resolve()),
        "component_count": len(reports),
        "reports": reports,
        "error_count": sum(len(item["errors"]) for item in reports),
        "warning_count": sum(len(item["warnings"]) for item in reports),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验宿主项目中的无表单流程组件是否符合约定")
    parser.add_argument("--workspace", default=".", help="工作区目录，用于自动发现宿主项目")
    parser.add_argument("--host-project", default="", help="显式指定宿主项目目录")
    parser.add_argument("--component", default="", help="只校验指定组件名")
    parser.add_argument("--strict", action="store_true", help="warning 也作为失败返回")
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

    try:
        result = validate_host_project(host_project, component_filter=args.component)
    except KeyError:
        print(f"[ERROR] 未找到无表单组件: {args.component}", file=sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["error_count"] > 0:
        return 1
    if args.strict and result["warning_count"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
