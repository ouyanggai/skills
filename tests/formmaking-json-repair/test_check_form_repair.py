import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-repair" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from check_form_repair import check_form  # noqa: E402


BASE_CONFIG = {
    "labelWidth": 100,
    "labelPosition": "left",
    "size": "small",
    "customClass": "",
    "ui": "element",
    "layout": "horizontal",
    "width": "100%",
    "hideLabel": False,
    "hideErrorMessage": False,
    "dataSource": [],
}


class CheckFormRepairTests(unittest.TestCase):
    def test_rule_event_without_rules_errors(self):
        payload = {
            "list": [],
            "config": {
                **BASE_CONFIG,
                "eventScript": [
                    {
                        "key": "onFormChange",
                        "name": "onFormChange",
                        "type": "rule",
                    }
                ],
            },
        }

        result = check_form(payload, source="<memory>")
        self.assertFalse(result.ok)
        self.assertTrue(any("缺少 `rules` 数组" in item for item in result.errors))

    def test_table_option_refresh_without_clear_warns(self):
        payload = {
            "list": [],
            "config": {
                **BASE_CONFIG,
                "eventScript": [
                    {
                        "key": "refreshBudgetType",
                        "name": "刷新预算类型",
                        "type": "js",
                        "func": (
                            "const { group, rowIndex } = arguments[0];\n"
                            "this.sendRequest('获取费用预算类型').then(res => {\n"
                            "  this.setOptionData([`${group}.${rowIndex}.departmentId`], res)\n"
                            "})"
                        ),
                    }
                ],
            },
        }

        result = check_form(payload, source="<memory>")
        self.assertTrue(result.ok)
        self.assertTrue(any("没有同步清空旧值" in item for item in result.warnings))

    def test_table_option_refresh_with_clear_does_not_warn(self):
        payload = {
            "list": [],
            "config": {
                **BASE_CONFIG,
                "eventScript": [
                    {
                        "key": "refreshBudgetType",
                        "name": "刷新预算类型",
                        "type": "js",
                        "func": (
                            "const { group, rowIndex } = arguments[0];\n"
                            "const expenseBudgetList = this.getComponent('expenseBudgetList')\n"
                            "expenseBudgetList.setData(rowIndex, { departmentId: [] })\n"
                            "this.sendRequest('获取费用预算类型').then(res => {\n"
                            "  this.setOptionData([`${group}.${rowIndex}.departmentId`], res)\n"
                            "})\n"
                            "this.$nextTick(() => this.validate())"
                        ),
                    }
                ],
            },
        }

        result = check_form(payload, source="<memory>")
        self.assertTrue(result.ok)
        self.assertFalse(any("没有同步清空旧值" in item for item in result.warnings))

    def test_required_field_without_rules_warns(self):
        payload = {
            "list": [
                {
                    "type": "input",
                    "name": "合同编号",
                    "model": "contractNo",
                    "key": "contractNo",
                    "rules": [],
                    "options": {
                        "required": True,
                        "requiredMessage": "请输入合同编号",
                    },
                }
            ],
            "config": {
                **BASE_CONFIG,
                "eventScript": [],
            },
        }

        result = check_form(payload, source="<memory>")
        self.assertTrue(result.ok)
        self.assertTrue(any("运行时 `rules`" in item for item in result.warnings))
