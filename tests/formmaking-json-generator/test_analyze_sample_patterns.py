import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from analyze_sample_patterns import analyze_sample_dir, discover_sample_dir  # noqa: E402


class AnalyzeSamplePatternsTests(unittest.TestCase):
    def test_analyze_sample_dir_collects_shell_and_style_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample_dir = Path(tmp)

            payload_a = {
                "list": [
                    {
                        "type": "text",
                        "name": "标题",
                        "model": "",
                        "key": "title",
                        "rules": [],
                        "options": {"customClass": "title"},
                    },
                    {
                        "type": "report",
                        "name": "表格布局",
                        "model": "report_a",
                        "key": "report_a",
                        "rules": [],
                        "options": {"width": "100%", "borderColor": "#999"},
                        "rows": [
                            {
                                "columns": [
                                    {
                                        "type": "td",
                                        "key": "cell_1",
                                        "rules": [],
                                        "options": {},
                                        "list": [
                                            {
                                                "type": "text",
                                                "name": "审批意见",
                                                "model": "",
                                                "key": "approval_title",
                                                "rules": [],
                                                "options": {"customClass": "approvalOpinion"},
                                            }
                                        ],
                                    }
                                ]
                            }
                        ],
                    },
                ],
                "config": {
                    "width": "900px",
                    "customClass": "bord newFormMaking",
                    "labelPosition": "right",
                    "labelCol": 3,
                    "styleSheets": ".sub-title .el-form-item__label{\ntext-align: center !important;\n}",
                },
            }

            payload_b = {
                "list": [
                    {
                        "type": "report",
                        "name": "表格布局",
                        "model": "report_b",
                        "key": "report_b",
                        "rules": [],
                        "options": {"width": "100%", "borderColor": "#999"},
                        "rows": [
                            {
                                "columns": [
                                    {
                                        "type": "td",
                                        "key": "cell_2",
                                        "rules": [],
                                        "options": {},
                                        "list": [
                                            {
                                                "type": "text",
                                                "name": "集团总经理意见",
                                                "model": "",
                                                "key": "opinion",
                                                "rules": [],
                                                "options": {"customClass": "txtCenter"},
                                            },
                                            {
                                                "type": "text",
                                                "name": "签字",
                                                "model": "",
                                                "key": "sign",
                                                "rules": [],
                                                "options": {"customClass": "txtCenter"},
                                            },
                                        ],
                                    }
                                ]
                            }
                        ],
                    }
                ],
                "config": {
                    "width": "850px",
                    "customClass": "newFormMaking",
                    "labelPosition": "left",
                    "labelCol": "",
                    "styleSheets": ".remark-font .el-form-item__label{\nfont-size:16px !important;\n}",
                },
            }

            (sample_dir / "a.json").write_text(json.dumps(payload_a, ensure_ascii=False), encoding="utf-8")
            (sample_dir / "b.json").write_text(json.dumps(payload_b, ensure_ascii=False), encoding="utf-8")

            result = analyze_sample_dir(sample_dir, top_n=10)

        self.assertEqual(result["sample_count"], 2)
        self.assertIn(["900px", 1], result["config_widths"])
        self.assertIn(["850px", 1], result["config_widths"])
        self.assertIn(["bord newFormMaking", 1], result["config_custom_classes"])
        self.assertIn(["newFormMaking", 1], result["config_custom_classes"])
        self.assertIn(["right", 1], result["label_positions"])
        self.assertIn(["left", 1], result["label_positions"])
        self.assertTrue(any(item[0] == "sub-title" for item in result["style_classes"]))
        self.assertTrue(any(item[0] == "remark-font" for item in result["style_classes"]))
        self.assertTrue(any(item[0] == "title" for item in result["text_custom_classes"]))
        self.assertTrue(any("审批意见" in item["titles"][0] for item in result["approval_examples"]))

    def test_discover_sample_dir_searches_parent_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_repo = root / "skill-repository"
            skill_repo.mkdir()
            sample_dir = root / "analysis" / "form-proxy-samples" / "raw"
            sample_dir.mkdir(parents=True)

            resolved = discover_sample_dir(skill_repo)

        self.assertEqual(resolved, sample_dir.resolve())


if __name__ == "__main__":
    unittest.main()
