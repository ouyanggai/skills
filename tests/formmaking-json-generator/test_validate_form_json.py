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

    def test_style_class_requires_new_form_making_shell(self):
        payload = {
            "list": [
                {
                    "type": "input",
                    "name": "合同名称",
                    "model": "contractName",
                    "key": "contractName",
                    "rules": [
                        {
                            "required": True,
                            "message": "请输入合同名称",
                        }
                    ],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "required": True,
                        "requiredMessage": "请输入合同名称",
                        "customClass": "showRedPot",
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
                "customClass": "bord",
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
        self.assertTrue(any("newFormMaking" in item for item in result.warnings))

    def test_custome_info_select_requires_semantic_model_keyword(self):
        payload = {
            "list": [
                {
                    "type": "custom",
                    "name": "经办人",
                    "model": "handler",
                    "key": "handler",
                    "el": "custome-info-select",
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
                "customClass": "bord newFormMaking",
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
        self.assertTrue(any("依赖字段命名识别类型" in item for item in result.errors))

    def test_json_string_custom_component_default_value_warns(self):
        payload = {
            "list": [
                {
                    "type": "custom",
                    "name": "合同选择",
                    "model": "contractObj",
                    "key": "contractObj",
                    "el": "general-list-select-show",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "defaultValue": {},
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
                "customClass": "bord newFormMaking",
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
        self.assertTrue(any("JSON 字符串" in item for item in result.warnings))

    def test_business_custom_component_requires_extend_props(self):
        payload = {
            "list": [
                {
                    "type": "custom",
                    "name": "合同文件",
                    "model": "legalDocTable",
                    "key": "legalDocTable",
                    "el": "legal-contract-doctable",
                    "rules": [],
                    "options": {
                        "width": "100%",
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "customClass": "",
                        "extendProps": {
                            "isFlowInitiate": False,
                            "businessId": "",
                        },
                    },
                    "events": {"onChange": "", "onFocus": "", "onBlur": ""},
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "bord newFormMaking",
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
        self.assertTrue(any("常用业务参数缺失" in item for item in result.errors))

    def test_table_no_show_table_warns_for_input_table(self):
        payload = {
            "list": [
                {
                    "type": "table",
                    "name": "费用明细",
                    "model": "expenseDetailList",
                    "key": "expenseDetailList",
                    "rules": [],
                    "options": {
                        "defaultValue": [],
                        "customClass": "tableNoPadding",
                        "labelWidth": 100,
                        "isLabelWidth": False,
                        "hidden": False,
                        "dataBind": True,
                        "disabled": False,
                        "required": True,
                        "validatorCheck": False,
                        "validator": "",
                        "paging": False,
                        "pageSize": 5,
                        "isAdd": True,
                        "isAlways": True,
                        "isDelete": True,
                        "showControl": True,
                        "nestedHeader": False,
                        "nestedHeaderName": "",
                        "noShowTable": True,
                        "tip": "",
                    },
                    "events": {
                        "onMounted": "",
                        "onChange": "",
                        "onRowAdd": "",
                        "onRowRemove": "",
                        "onPageChange": "",
                    },
                    "tableColumns": [],
                }
            ],
            "config": {
                "labelWidth": 100,
                "labelPosition": "left",
                "size": "small",
                "customClass": "bord newFormMaking",
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
        self.assertTrue(any("展示型表格" in item for item in result.warnings))

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

    def test_subform_wrapping_report_warns_for_formal_layout(self):
        payload = {
            "list": [
                {
                    "type": "subform",
                    "name": "固定分区",
                    "model": "fixedSections",
                    "key": "fixed_sections",
                    "rules": [],
                    "options": {
                        "hidden": False,
                        "dataBind": True,
                        "showControl": True,
                        "isAdd": True,
                        "isDelete": True,
                    },
                    "events": {},
                    "list": [
                        {
                            "type": "report",
                            "name": "表格布局",
                            "model": "sectionReport",
                            "key": "section_report",
                            "rules": [],
                            "options": {
                                "hidden": False,
                                "borderWidth": 1,
                                "borderColor": "#999",
                                "width": "100%",
                                "customClass": "",
                            },
                            "rows": [
                                {
                                    "columns": [
                                        {
                                            "type": "td",
                                            "key": "section_cell",
                                            "rules": [],
                                            "options": {
                                                "colspan": 1,
                                                "rowspan": 1,
                                                "align": "center",
                                                "valign": "middle",
                                            },
                                            "list": [],
                                        }
                                    ]
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
        self.assertTrue(any("subform" in item and "report" in item for item in result.warnings))


if __name__ == "__main__":
    unittest.main()
