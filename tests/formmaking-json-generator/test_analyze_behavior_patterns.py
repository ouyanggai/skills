import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from analyze_behavior_patterns import analyze_sample_dir  # noqa: E402


class AnalyzeBehaviorPatternsTests(unittest.TestCase):
    def test_analyze_sample_dir_collects_behavior_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample_dir = Path(tmp)

            payload_a = {
                "list": [
                    {
                        "type": "number",
                        "name": "金额",
                        "model": "amount",
                        "key": "amount",
                        "rules": [],
                        "options": {},
                        "events": {"onChange": "onAmountChange", "onBlur": ""},
                    },
                    {
                        "type": "select",
                        "name": "公司",
                        "model": "companyId",
                        "key": "companyId",
                        "rules": [],
                        "options": {
                            "remoteDataSource": "company_ds",
                            "dynamicValueType": "fx",
                        },
                        "events": {"onChange": "onCompanyChange"},
                    },
                ],
                "config": {
                    "eventScript": [
                        {
                            "key": "onAmountChange",
                            "name": "onAmountChange",
                            "func": "const price = this.getValue('amount'); this.setData({amountUpper: price});",
                        },
                        {
                            "key": "onCompanyChange",
                            "name": "onCompanyChange",
                            "func": "const info = await this.sendRequest('company_ds'); this.setData({projectId: ''}); this.display(['projectId']); this.triggerEvent('reloadProject');",
                        },
                        {
                            "key": "rule_toggle",
                            "name": "rule_toggle",
                            "type": "rule",
                            "rules": [],
                        },
                    ],
                    "dataSource": [
                        {
                            "key": "company_ds",
                            "name": "获取公司",
                            "url": "/api/company/list",
                            "method": "POST",
                            "auto": True,
                            "requestFunc": "return config;",
                            "responseFunc": "return res.data;",
                        }
                    ],
                },
            }

            payload_b = {
                "list": [
                    {
                        "type": "custom",
                        "name": "合同",
                        "model": "contractObj",
                        "key": "contractObj",
                        "rules": [],
                        "options": {},
                        "events": {"onChange": "onContractChange", "onFocus": "openContractDialog"},
                    },
                    {
                        "type": "radio",
                        "name": "类型",
                        "model": "type",
                        "key": "type",
                        "rules": [],
                        "options": {
                            "dynamicValueType": "datasource",
                        },
                        "events": {"onChange": "toggleFields"},
                    },
                ],
                "config": {
                    "eventScript": [
                        {
                            "key": "onContractChange",
                            "name": "onContractChange",
                            "func": "const values = this.getValues(); this.setData({contractName: values.contractObj}); this.hide(['legacyField']); this.disabled(['projectId'], true);",
                        },
                        {
                            "key": "openContractDialog",
                            "name": "openContractDialog",
                            "func": "this.$fm.show('orgTree').then(dialog => { dialog.$on('confirmed', (res) => { this.setData({companyId: res.id}) }) })",
                        },
                        {
                            "key": "toggleFields",
                            "name": "toggleFields",
                            "func": "this.refresh(); this.validate(['type']);",
                        },
                    ],
                    "dataSource": [
                        {
                            "key": "project_ds",
                            "name": "获取项目",
                            "url": "/api/project/list",
                            "method": "GET",
                            "auto": False,
                            "responseFunc": "return res.data;",
                        }
                    ],
                },
            }

            (sample_dir / "a.json").write_text(json.dumps(payload_a, ensure_ascii=False), encoding="utf-8")
            (sample_dir / "b.json").write_text(json.dumps(payload_b, ensure_ascii=False), encoding="utf-8")

            result = analyze_sample_dir(sample_dir, top_n=10)

        self.assertEqual(result["sample_count"], 2)
        self.assertEqual(result["forms_with_event_script"], 2)
        self.assertEqual(result["forms_with_data_source"], 2)
        self.assertEqual(result["forms_with_remote_data_source"], 1)
        self.assertEqual(result["forms_with_dynamic_value"], 2)
        self.assertIn(["func", 5], result["event_script_types"])
        self.assertIn(["rule", 1], result["event_script_types"])
        self.assertTrue(any(item[0] == "setData" and item[1] >= 4 for item in result["action_counts"]))
        self.assertTrue(any(item[0] == "sendRequest" and item[1] == 1 for item in result["action_counts"]))
        self.assertTrue(any(item[0] == "远程请求" for item in result["behavior_tag_counts"]))
        self.assertTrue(any(item[0] == "number.onChange" for item in result["event_bindings"]))
        self.assertIn(["POST", 1], result["data_source_methods"])
        self.assertIn(["GET", 1], result["data_source_methods"])
        self.assertIn(["true", 1], result["data_source_auto_flags"])
        self.assertIn(["false", 1], result["data_source_auto_flags"])
        self.assertIn(["select", 1], result["remote_data_source_field_types"])
        self.assertIn(["fx", 1], result["dynamic_value_types"])
        self.assertIn(["datasource", 1], result["dynamic_value_types"])
        self.assertEqual(result["request_func_count"], 1)
        self.assertEqual(result["response_func_count"], 2)
        self.assertTrue(any(item["behavior_tags"] for item in result["behavior_examples"]))


if __name__ == "__main__":
    unittest.main()
