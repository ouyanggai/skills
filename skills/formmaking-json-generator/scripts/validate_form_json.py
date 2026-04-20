#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


REQUIRED_CONFIG_KEYS = {
    "labelWidth",
    "labelPosition",
    "size",
    "customClass",
    "ui",
    "layout",
    "width",
    "hideLabel",
    "hideErrorMessage",
}

LIST_CONTAINERS = {"subform", "inline", "dialog", "card", "group"}
TABS_CONTAINERS = {"tabs", "collapse"}


@dataclass
class ValidationResult:
    source: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class FormValidator:
    def __init__(self, source: str, strict: bool = True) -> None:
        self.result = ValidationResult(source=source)
        self.strict = strict
        self._event_keys: set[str] = set()
        self._data_source_refs: set[str] = set()
        self._seen_keys: set[str] = set()
        self._seen_event_keys: set[str] = set()
        self._seen_data_source_keys: set[str] = set()

    def error(self, path: str, message: str) -> None:
        self.result.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.result.warnings.append(f"{path}: {message}")

    def strict_issue(self, path: str, message: str) -> None:
        if self.strict:
            self.error(path, message)
        else:
            self.warn(path, message)

    def validate(self, payload: object) -> ValidationResult:
        if not isinstance(payload, dict):
            self.error("$", "根节点必须是对象")
            return self.result

        form_list = payload.get("list")
        config = payload.get("config")

        if not isinstance(form_list, list):
            self.error("$.list", "`list` 必须是数组")
        if not isinstance(config, dict):
            self.error("$.config", "`config` 必须是对象")
        else:
            self._validate_config(config, "$.config")

        if isinstance(form_list, list):
            for index, node in enumerate(form_list):
                self._validate_node(node, f"$.list[{index}]")
            self._validate_top_level_layout(form_list, "$.list")

        return self.result

    def _validate_config(self, config: dict, path: str) -> None:
        missing = sorted(REQUIRED_CONFIG_KEYS - set(config.keys()))
        if missing:
            self.warn(path, f"缺少常用配置键: {', '.join(missing)}")

        event_script = config.get("eventScript", [])
        if event_script is None:
            event_script = []
        if not isinstance(event_script, list):
            self.error(f"{path}.eventScript", "`eventScript` 必须是数组")
        else:
            for index, item in enumerate(event_script):
                self._validate_event_script(item, f"{path}.eventScript[{index}]")

        data_source = config.get("dataSource", [])
        if data_source is None:
            data_source = []
        if not isinstance(data_source, list):
            self.error(f"{path}.dataSource", "`dataSource` 必须是数组")
        else:
            for index, item in enumerate(data_source):
                self._validate_data_source(item, f"{path}.dataSource[{index}]")

        style_sheets = config.get("styleSheets")
        if style_sheets is not None and not isinstance(style_sheets, str):
            self.warn(f"{path}.styleSheets", "`styleSheets` 通常应为字符串")

    def _validate_event_script(self, item: object, path: str) -> None:
        if not isinstance(item, dict):
            self.error(path, "事件脚本项必须是对象")
            return

        key = item.get("key")
        name = item.get("name")
        script_type = item.get("type")

        if not isinstance(key, str) or not key.strip():
            self.error(f"{path}.key", "事件脚本必须有非空 `key`")
        else:
            if key in self._seen_event_keys:
                self.error(f"{path}.key", f"重复的事件脚本 key: {key}")
            self._seen_event_keys.add(key)
            self._event_keys.add(key)

        if not isinstance(name, str) or not name.strip():
            self.error(f"{path}.name", "事件脚本必须有非空 `name`")

        if script_type == "rule":
            if not isinstance(item.get("rules"), list):
                self.strict_issue(f"{path}.rules", "规则型事件脚本通常应提供 `rules` 数组")
        else:
            if not isinstance(item.get("func"), str):
                self.strict_issue(f"{path}.func", "函数型事件脚本通常应提供 `func` 字符串")

    def _validate_data_source(self, item: object, path: str) -> None:
        if not isinstance(item, dict):
            self.error(path, "数据源项必须是对象")
            return

        key = item.get("key")
        name = item.get("name")

        if not isinstance(key, str) or not key.strip():
            self.error(f"{path}.key", "数据源必须有非空 `key`")
        else:
            if key in self._seen_data_source_keys:
                self.error(f"{path}.key", f"重复的数据源 key: {key}")
            self._seen_data_source_keys.add(key)
            self._data_source_refs.add(key)

        if isinstance(name, str) and name.strip():
            self._data_source_refs.add(name)
        else:
            self.error(f"{path}.name", "数据源必须有非空 `name`")

        for field_name in ("url", "method"):
            value = item.get(field_name)
            if not isinstance(value, str) or not value.strip():
                self.error(f"{path}.{field_name}", f"数据源必须提供非空 `{field_name}`")

        for field_name in ("params", "headers"):
            value = item.get(field_name)
            if value is not None and not isinstance(value, dict):
                self.warn(f"{path}.{field_name}", f"`{field_name}` 通常应为对象")

    def _validate_node(self, node: object, path: str) -> None:
        if not isinstance(node, dict):
            self.error(path, "节点必须是对象")
            return

        node_type = node.get("type")
        if not isinstance(node_type, str) or not node_type.strip():
            self.error(f"{path}.type", "节点必须有非空 `type`")
            return

        key = node.get("key")
        if key is not None:
            if not isinstance(key, str) or not key.strip():
                self.strict_issue(f"{path}.key", "`key` 通常应为非空字符串")
            elif key in self._seen_keys:
                self.warn(f"{path}.key", f"重复的 key: {key}")
            else:
                self._seen_keys.add(key)

        options = node.get("options")
        if options is not None and not isinstance(options, dict):
            self.error(f"{path}.options", "`options` 必须是对象")
            options = None

        name = node.get("name")
        if isinstance(name, str) and name.lstrip().startswith("*"):
            self.warn(
                f"{path}.name",
                "必填标签不建议直接把 `*` 写进文案，优先沿用宿主的 `showRedPot` 样式类",
            )

        events = node.get("events")
        if events is not None and not isinstance(events, dict):
            self.error(f"{path}.events", "`events` 必须是对象")
        elif isinstance(events, dict):
            for event_name, handler in events.items():
                if handler in ("", None):
                    continue
                if not isinstance(handler, str):
                    self.error(f"{path}.events.{event_name}", "事件值必须是字符串")
                elif handler not in self._event_keys:
                    self.strict_issue(
                        f"{path}.events.{event_name}",
                        f"引用了不存在的事件脚本 key: {handler}",
                    )

        rules = node.get("rules", [])
        if rules is None:
            rules = []
        if not isinstance(rules, list):
            self.error(f"{path}.rules", "`rules` 必须是数组")
            rules = []

        if node_type == "custom":
            el = node.get("el")
            if not isinstance(el, str) or not el.strip():
                self.error(f"{path}.el", "`custom` 组件必须提供非空 `el`")

        if node_type == "component":
            template = (options or {}).get("template")
            if not isinstance(template, str) or not template.strip():
                self.warn(f"{path}.options.template", "`component` 一般需要 `template`")

        if options:
            self._validate_options(options, path, node_type)
            self._validate_required_rules(options, rules, path, node_type)

        if node_type == "report":
            self._validate_report(node, path)
        elif node_type == "grid":
            self._validate_grid(node, path)
        elif node_type == "table":
            self._validate_table(node, path)
        elif node_type == "subform":
            self._validate_subform(node, path)
        elif node_type in LIST_CONTAINERS:
            self._validate_list_container(node, path)
        elif node_type in TABS_CONTAINERS:
            self._validate_tabs_container(node, path)

    def _validate_options(self, options: dict, path: str, node_type: str) -> None:
        custom_class = options.get("customClass")
        if isinstance(custom_class, str) and "readonly-highlight" in custom_class.split():
            self.warn(
                f"{path}.options.customClass",
                "回填展示字段不建议用红色高亮，优先使用 `disabled` 置灰并保持与宿主样式一致",
            )

        if options.get("remote") and options.get("remoteType") == "datasource":
            remote_data_source = options.get("remoteDataSource")
            if not isinstance(remote_data_source, str) or not remote_data_source.strip():
                self.strict_issue(
                    f"{path}.options.remoteDataSource",
                    "远程选项字段通常应配置 `remoteDataSource`",
                )
            elif remote_data_source not in self._data_source_refs:
                self.strict_issue(
                    f"{path}.options.remoteDataSource",
                    f"引用了不存在的数据源: {remote_data_source}",
                )

        for option_name in ("tokenDataSource", "dynamicValueDataSource"):
            value = options.get(option_name)
            if value in ("", None):
                continue
            if not isinstance(value, str):
                self.error(f"{path}.options.{option_name}", f"`{option_name}` 必须是字符串")
            elif value not in self._data_source_refs:
                self.strict_issue(
                    f"{path}.options.{option_name}",
                    f"引用了不存在的数据源: {value}",
                )

        if options.get("isDynamicValue"):
            dynamic_type = options.get("dynamicValueType")
            if dynamic_type == "datasource":
                if not options.get("dynamicValueDataSource"):
                    self.strict_issue(
                        f"{path}.options.dynamicValueDataSource",
                        "动态值类型为 datasource 时通常应配置 `dynamicValueDataSource`",
                    )
            elif dynamic_type == "fx":
                if not options.get("dynamicValueFx"):
                    self.strict_issue(
                        f"{path}.options.dynamicValueFx",
                        "动态值类型为 fx 时通常应配置 `dynamicValueFx`",
                    )
            else:
                self.strict_issue(
                    f"{path}.options.dynamicValueType",
                    "开启动态值时通常应把 `dynamicValueType` 设为 datasource 或 fx",
                )

        if node_type == "custom":
            for option_name in ("customProps", "extendProps"):
                value = options.get(option_name)
                if value is not None and not isinstance(value, dict):
                    self.warn(f"{path}.options.{option_name}", f"`{option_name}` 通常应为对象")

    def _validate_required_rules(
        self,
        options: dict,
        rules: list[object],
        path: str,
        node_type: str,
    ) -> None:
        if not options.get("required"):
            return
        if node_type in {"text", "html"}:
            return

        has_runtime_rule = False
        for item in rules:
            if not isinstance(item, dict):
                continue
            if item.get("required") is True or item.get("func"):
                has_runtime_rule = True
                break

        if not has_runtime_rule:
            self.warn(
                f"{path}.rules",
                "`options.required` 为 true 时应同步提供 `rules` 必填规则或自定义校验，否则运行时可能只显示必填状态但不拦截提交",
            )

    def _validate_report(self, node: dict, path: str) -> None:
        options = node.get("options") if isinstance(node.get("options"), dict) else {}
        width = options.get("width")
        if not isinstance(width, str) or not width.strip():
            self.strict_issue(
                f"{path}.options.width",
                "正式表格型 `report` 通常应显式设置 `width`，一般为 `100%`",
            )

        rows = node.get("rows")
        if not isinstance(rows, list):
            self.error(f"{path}.rows", "`report.rows` 必须是数组")
            return

        for row_index, row in enumerate(rows):
            row_path = f"{path}.rows[{row_index}]"
            if not isinstance(row, dict):
                self.error(row_path, "report 行必须是对象")
                continue
            columns = row.get("columns")
            if not isinstance(columns, list):
                self.error(f"{row_path}.columns", "`report.rows[].columns` 必须是数组")
                continue
            for col_index, column in enumerate(columns):
                col_path = f"{row_path}.columns[{col_index}]"
                if not isinstance(column, dict):
                    self.error(col_path, "report 单元格必须是对象")
                    continue
                child_list = column.get("list", [])
                if not isinstance(child_list, list):
                    self.error(f"{col_path}.list", "`td.list` 必须是数组")
                    continue
                for child_index, child in enumerate(child_list):
                    self._validate_node(child, f"{col_path}.list[{child_index}]")

    def _validate_grid(self, node: dict, path: str) -> None:
        columns = node.get("columns")
        if not isinstance(columns, list):
            self.error(f"{path}.columns", "`grid.columns` 必须是数组")
            return

        for col_index, column in enumerate(columns):
            col_path = f"{path}.columns[{col_index}]"
            if not isinstance(column, dict):
                self.error(col_path, "grid 列必须是对象")
                continue
            child_list = column.get("list", [])
            if not isinstance(child_list, list):
                self.error(f"{col_path}.list", "`grid.columns[].list` 必须是数组")
                continue
            for child_index, child in enumerate(child_list):
                self._validate_node(child, f"{col_path}.list[{child_index}]")

    def _validate_table(self, node: dict, path: str) -> None:
        columns = node.get("tableColumns")
        if not isinstance(columns, list):
            self.error(f"{path}.tableColumns", "`table.tableColumns` 必须是数组")
            return
        for col_index, column in enumerate(columns):
            self._validate_node(column, f"{path}.tableColumns[{col_index}]")

    def _validate_subform(self, node: dict, path: str) -> None:
        self._validate_list_container(node, path)

        child_list = node.get("list")
        if not isinstance(child_list, list):
            return

        has_report_child = any(
            isinstance(child, dict) and child.get("type") == "report"
            for child in child_list
        )
        if not has_report_child:
            return

        options = node.get("options") if isinstance(node.get("options"), dict) else {}
        custom_class = options.get("customClass")
        if isinstance(custom_class, str) and "tableNoPadding" in custom_class.split():
            return

        if (
            options.get("showControl")
            or options.get("isAdd")
            or options.get("isDelete")
            or options.get("paging")
        ):
            self.warn(
                path,
                "`subform` 包 `report` 会渲染编号、增删或分页控制；制式 Word/截图固定分区除非明确要求动态多条，否则应改为固定 `report` 结构",
            )
        else:
            self.warn(
                path,
                "`subform` 包 `report` 仍可能引入重复块外壳；只有明确动态重复业务块时才建议使用",
            )

    def _validate_list_container(self, node: dict, path: str) -> None:
        child_list = node.get("list")
        if not isinstance(child_list, list):
            self.error(f"{path}.list", "`list` 容器必须包含数组类型的 `list`")
            return
        for child_index, child in enumerate(child_list):
            self._validate_node(child, f"{path}.list[{child_index}]")

    def _validate_tabs_container(self, node: dict, path: str) -> None:
        tabs = node.get("tabs")
        if not isinstance(tabs, list):
            self.error(f"{path}.tabs", "`tabs/collapse` 容器必须包含数组类型的 `tabs`")
            return
        for tab_index, tab in enumerate(tabs):
            tab_path = f"{path}.tabs[{tab_index}]"
            if not isinstance(tab, dict):
                self.error(tab_path, "tab 项必须是对象")
                continue
            child_list = tab.get("list")
            if not isinstance(child_list, list):
                self.error(f"{tab_path}.list", "`tabs[].list` 必须是数组")
                continue
            for child_index, child in enumerate(child_list):
                self._validate_node(child, f"{tab_path}.list[{child_index}]")

    def _validate_top_level_layout(self, form_list: list[object], path: str) -> None:
        if not form_list:
            return

        first_node = form_list[0]
        if isinstance(first_node, dict):
            first_child = self._extract_single_grid_child(first_node)
            if isinstance(first_child, dict) and first_child.get("type") == "text":
                self.warn(
                    f"{path}[0]",
                    "顶层标题更推荐直接使用 `text`，而不是单列 `grid` 包一层",
                )

        for index, node in enumerate(form_list):
            if not isinstance(node, dict):
                continue
            child = self._extract_single_grid_child(node)
            if isinstance(child, dict) and child.get("type") == "report":
                self.warn(
                    f"{path}[{index}]",
                    "顶层单列 `grid` 只包一个 `report` 时，通常可直接把 `report` 放在顶层",
                )

    def _extract_single_grid_child(self, node: dict) -> dict | None:
        if node.get("type") != "grid":
            return None
        columns = node.get("columns")
        if not isinstance(columns, list) or len(columns) != 1:
            return None
        column = columns[0]
        if not isinstance(column, dict):
            return None
        options = column.get("options")
        if not isinstance(options, dict):
            return None
        if options.get("span") != 24:
            return None
        child_list = column.get("list")
        if not isinstance(child_list, list) or len(child_list) != 1:
            return None
        child = child_list[0]
        if not isinstance(child, dict):
            return None
        return child


def validate_form(
    payload: object,
    source: str = "<memory>",
    strict: bool = True,
) -> ValidationResult:
    validator = FormValidator(source=source, strict=strict)
    return validator.validate(payload)


def validate_path(path: Path, strict: bool = True) -> ValidationResult:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exercised by CLI
        result = ValidationResult(source=str(path))
        result.errors.append(f"$: JSON 解析失败: {exc}")
        return result
    return validate_form(payload, source=str(path), strict=strict)


def iter_json_files(target: Path) -> Iterable[Path]:
    if target.is_file():
        yield target
        return
    for path in sorted(target.rglob("*.json")):
        if path.is_file():
            yield path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="校验 FormMaking JSON 结构")
    parser.add_argument("target", help="JSON 文件或目录")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        help="严格模式，适合校验新生成的 JSON",
    )
    mode_group.add_argument(
        "--relaxed",
        dest="strict",
        action="store_false",
        help="宽松模式，适合校验历史样本或脏数据",
    )
    parser.set_defaults(strict=True)
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        print(f"[ERROR] 路径不存在: {target}", file=sys.stderr)
        return 2

    files = list(iter_json_files(target))
    if not files:
        print(f"[ERROR] 未找到 JSON 文件: {target}", file=sys.stderr)
        return 2

    total_errors = 0
    total_warnings = 0

    for path in files:
        result = validate_path(path, strict=args.strict)
        status = "OK" if result.ok else "FAIL"
        print(f"[{status}] {path}")
        for warning in result.warnings:
            print(f"  WARN  {warning}")
        for error in result.errors:
            print(f"  ERROR {error}")
        total_errors += len(result.errors)
        total_warnings += len(result.warnings)

    print(
        f"Summary: files={len(files)} errors={total_errors} warnings={total_warnings}"
    )
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
