#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


ROW_OPTION_TARGET_RE = re.compile(
    r"setOptionData\(\s*\[\s*`[^`]*\$\{group\}\.\$\{rowIndex\}\.([A-Za-z0-9_]+)[^`]*`\s*\]"
)


@dataclass
class RepairCheckResult:
    source: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class RepairChecker:
    def __init__(self, source: str) -> None:
        self.result = RepairCheckResult(source=source)

    def error(self, path: str, message: str) -> None:
        self.result.errors.append(f"{path}: {message}")

    def warn(self, path: str, message: str) -> None:
        self.result.warnings.append(f"{path}: {message}")

    def check(self, payload: object) -> RepairCheckResult:
        if not isinstance(payload, dict):
            self.error("$", "根节点必须是对象")
            return self.result

        config = payload.get("config")
        if not isinstance(config, dict):
            self.error("$.config", "`config` 必须是对象")
            return self.result

        event_scripts = config.get("eventScript", [])
        if event_scripts is None:
            event_scripts = []
        if not isinstance(event_scripts, list):
            self.error("$.config.eventScript", "`eventScript` 必须是数组")
        else:
            for index, item in enumerate(event_scripts):
                self._check_event_script(item, f"$.config.eventScript[{index}]")

        form_list = payload.get("list", [])
        if not isinstance(form_list, list):
            self.error("$.list", "`list` 必须是数组")
            return self.result

        for index, node in enumerate(form_list):
            self._check_node(node, f"$.list[{index}]")

        return self.result

    def _check_event_script(self, item: object, path: str) -> None:
        if not isinstance(item, dict):
            self.error(path, "事件脚本项必须是对象")
            return

        if item.get("type") == "rule" and not isinstance(item.get("rules"), list):
            self.error(f"{path}.rules", "规则型事件脚本缺少 `rules` 数组")

        func = item.get("func")
        if not isinstance(func, str) or not func.strip():
            return

        for field in sorted(set(ROW_OPTION_TARGET_RE.findall(func))):
            if not self._has_row_field_clear(func, field):
                self.warn(
                    path,
                    f"表格行内联动刷新了 `{field}` 的选项，但没有同步清空旧值；这会导致切换上游字段后界面看似为空、提交仍可能带旧值或绕过必填",
                )

    def _has_row_field_clear(self, func: str, field: str) -> bool:
        escaped = re.escape(field)
        patterns = (
            rf"\.setData\(\s*rowIndex\s*,\s*\{{[^}}]*\b{escaped}\s*:",
            rf"\.setData\(\s*arg\.rowIndex\s*,\s*\{{[^}}]*\b{escaped}\s*:",
            rf"setData\(\s*\{{[^}}]*\[\s*`[^`]*\$\{{group\}}\.\$\{{rowIndex\}}\.{escaped}[^`]*`\s*\]\s*:",
        )
        return any(re.search(pattern, func, re.S) for pattern in patterns)

    def _check_node(self, node: object, path: str) -> None:
        if not isinstance(node, dict):
            self.error(path, "节点必须是对象")
            return

        options = node.get("options")
        if isinstance(options, dict):
            self._check_required_rules(node, options, path)

        node_type = node.get("type")
        if node_type == "report":
            for row_index, row in enumerate(node.get("rows", []) or []):
                if not isinstance(row, dict):
                    continue
                for col_index, column in enumerate(row.get("columns", []) or []):
                    if not isinstance(column, dict):
                        continue
                    for child_index, child in enumerate(column.get("list", []) or []):
                        self._check_node(child, f"{path}.rows[{row_index}].columns[{col_index}].list[{child_index}]")
        elif node_type == "grid":
            for col_index, column in enumerate(node.get("columns", []) or []):
                if not isinstance(column, dict):
                    continue
                for child_index, child in enumerate(column.get("list", []) or []):
                    self._check_node(child, f"{path}.columns[{col_index}].list[{child_index}]")
        elif node_type == "table":
            for col_index, column in enumerate(node.get("tableColumns", []) or []):
                self._check_node(column, f"{path}.tableColumns[{col_index}]")
        elif node_type in {"subform", "inline", "dialog", "card", "group"}:
            for child_index, child in enumerate(node.get("list", []) or []):
                self._check_node(child, f"{path}.list[{child_index}]")

    def _check_required_rules(self, node: dict, options: dict, path: str) -> None:
        if not options.get("required"):
            return
        if node.get("type") in {"text", "html"}:
            return

        rules = node.get("rules", [])
        if not isinstance(rules, list):
            self.warn(f"{path}.rules", "必填字段的 `rules` 应为数组")
            return

        has_runtime_rule = False
        for item in rules:
            if isinstance(item, dict) and (item.get("required") is True or item.get("func")):
                has_runtime_rule = True
                break

        if not has_runtime_rule:
            self.warn(
                f"{path}.rules",
                "字段标记为必填，但没有真正的运行时 `rules`；这类遗留问题常表现为红星存在、提交不拦截",
            )


def check_form(payload: object, source: str) -> RepairCheckResult:
    return RepairChecker(source).check(payload)


def check_path(path: Path) -> RepairCheckResult:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return check_form(payload, source=str(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查 FormMaking JSON 的修复型风险")
    parser.add_argument("paths", nargs="+", help="JSON 文件路径")
    args = parser.parse_args(argv)

    error_count = 0
    warning_count = 0

    for raw_path in args.paths:
        path = Path(raw_path)
        result = check_path(path)
        if result.ok:
            print(f"[OK] {path}")
        else:
            print(f"[FAIL] {path}")
        for item in result.errors:
            print(f"  ERROR {item}")
        for item in result.warnings:
            print(f"  WARN  {item}")
        error_count += len(result.errors)
        warning_count += len(result.warnings)

    print(
        f"Summary: files={len(args.paths)} errors={error_count} warnings={warning_count}"
    )
    return 1 if error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
