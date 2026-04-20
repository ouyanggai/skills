import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_form_json import validate_form, validate_path  # noqa: E402


class ValidateFormJsonTests(unittest.TestCase):
    def test_generated_cases_pass_strict(self):
        case_dir = ROOT / "tests" / "formmaking-json-generator" / "generated_cases"
        case_files = sorted(case_dir.glob("*.json"))

        self.assertGreaterEqual(len(case_files), 1)

        failures = []
        for path in case_files:
            result = validate_path(path, strict=True)
            if not result.ok:
                failures.append(
                    {
                        "file": path.name,
                        "errors": result.errors,
                    }
                )

        self.assertFalse(
            failures,
            msg="生成案例未通过严格校验: "
            + json.dumps(failures, ensure_ascii=False),
        )

    def test_exported_samples_all_pass(self):
        sample_dir = ROOT / "analysis" / "form-proxy-samples" / "raw"
        if not sample_dir.exists():
            self.skipTest("未提供真实样本目录，跳过历史样本宽松校验")
        sample_files = sorted(sample_dir.glob("*.json"))

        self.assertGreaterEqual(len(sample_files), 100)

        failures = []
        for path in sample_files:
            result = validate_path(path, strict=False)
            if not result.ok:
                failures.append(
                    {
                        "file": path.name,
                        "errors": result.errors[:5],
                    }
                )

        self.assertFalse(
            failures,
            msg="导出的真实样本中存在校验失败项: "
            + json.dumps(failures[:3], ensure_ascii=False),
        )

    def test_custom_component_requires_el(self):
        payload = {
            "list": [
                {
                    "type": "custom",
                    "name": "项目选择",
                    "model": "projectObj",
                    "key": "projectObj",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "customProps": {},
                        "extendProps": {},
                    },
                    "events": {"onChange": "", "onFocus": "", "onBlur": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertFalse(result.ok)
        self.assertTrue(any(".el" in item for item in result.errors))

    def test_event_reference_must_exist(self):
        payload = {
            "list": [
                {
                    "type": "input",
                    "name": "标题",
                    "model": "title",
                    "key": "title",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "required": False,
                        "customClass": "",
                        "labelWidth": 100,
                        "isLabelWidth": False,
                    },
                    "events": {"onChange": "missing_handler", "onFocus": "", "onBlur": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertFalse(result.ok)
        self.assertTrue(any("missing_handler" in item for item in result.errors))

    def test_report_requires_explicit_width(self):
        payload = {
            "list": [
                {
                    "type": "report",
                    "name": "表格布局",
                    "model": "report_demo",
                    "key": "report_demo",
                    "rules": [],
                    "options": {
                        "hidden": False,
                        "borderWidth": 1,
                        "borderColor": "#999",
                        "customClass": "",
                    },
                    "rows": [{"columns": []}],
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertFalse(result.ok)
        self.assertTrue(any(".options.width" in item for item in result.errors))

    def test_single_column_grid_wrapping_title_warns(self):
        payload = {
            "list": [
                {
                    "type": "grid",
                    "name": "栅格布局",
                    "model": "grid_title",
                    "key": "grid_title",
                    "rules": [],
                    "options": {
                        "gutter": 0,
                        "justify": "start",
                        "align": "middle",
                        "customClass": "",
                        "hidden": False,
                        "flex": True,
                        "responsive": True,
                    },
                    "columns": [
                        {
                            "type": "col",
                            "key": "col_title",
                            "rules": [],
                            "options": {
                                "span": 24,
                                "offset": 0,
                                "push": 0,
                                "pull": 0,
                                "xs": 24,
                                "sm": 24,
                                "md": 24,
                                "lg": 24,
                                "xl": 24,
                                "customClass": "",
                            },
                            "list": [
                                {
                                    "type": "text",
                                    "name": "合同变更评审表",
                                    "model": "form_title",
                                    "key": "form_title",
                                    "rules": [],
                                    "options": {
                                        "defaultValue": "",
                                        "customClass": "sub-title",
                                        "labelWidth": "100%",
                                        "isLabelWidth": False,
                                        "hidden": False,
                                        "dataBind": True,
                                        "required": False,
                                        "hideLabel": False,
                                    },
                                    "events": {"onChange": ""},
                                }
                            ],
                        }
                    ],
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertTrue(result.ok)
        self.assertTrue(any("顶层标题更推荐直接使用 `text`" in item for item in result.warnings))

    def test_literal_required_star_warns(self):
        payload = {
            "list": [
                {
                    "type": "text",
                    "name": "*合同金额（元）",
                    "model": "amount_label",
                    "key": "amount_label",
                    "rules": [],
                    "options": {
                        "defaultValue": "",
                        "customClass": "cell-label",
                        "labelWidth": "100%",
                        "isLabelWidth": False,
                        "hidden": False,
                        "dataBind": True,
                        "required": False,
                        "hideLabel": False,
                    },
                    "events": {"onChange": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertTrue(result.ok)
        self.assertTrue(any("showRedPot" in item for item in result.warnings))

    def test_readonly_highlight_warns(self):
        payload = {
            "list": [
                {
                    "type": "input",
                    "name": "原合同金额",
                    "model": "originAmount",
                    "key": "origin_amount",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "required": False,
                        "customClass": "readonly-highlight cell-tight",
                        "labelWidth": 100,
                        "isLabelWidth": False,
                    },
                    "events": {"onChange": "", "onFocus": "", "onBlur": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertTrue(result.ok)
        self.assertTrue(any("disabled" in item and "置灰" in item for item in result.warnings))

    def test_required_option_without_rules_warns(self):
        payload = {
            "list": [
                {
                    "type": "input",
                    "name": "合同名称",
                    "model": "contractName",
                    "key": "contract_name",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "required": True,
                        "requiredMessage": "请输入合同名称",
                        "customClass": "",
                        "labelWidth": 100,
                        "isLabelWidth": False,
                    },
                    "events": {"onChange": "", "onFocus": "", "onBlur": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "",
                "ui": "element",
                "layout": "horizontal",
                "width": "100%",
                "hideLabel": False,
                "hideErrorMessage": False,
                "eventScript": [],
                "dataSource": [],
            },
        }

        result = validate_form(payload, source="<memory>", strict=True)
        self.assertTrue(result.ok)
        self.assertTrue(any("options.required" in item and "rules" in item for item in result.warnings))


if __name__ == "__main__":
    unittest.main()
