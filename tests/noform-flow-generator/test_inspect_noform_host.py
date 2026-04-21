import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "noform-flow-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from inspect_noform_host import discover_host_project, inspect_host_project, main  # noqa: E402


class InspectNoFormHostTests(unittest.TestCase):
    def create_host_project(self, root: Path) -> Path:
        host = root / "rsh-cloud-invest-power-system-test"
        noform = host / "src" / "components" / "NoFormFLow"
        config_dir = noform / "config"
        mixin_dir = noform / "mixin"
        flow_library = host / "src" / "views" / "flowLibrary" / "NoFormMulBranch"
        api_dir = host / "src" / "api"

        config_dir.mkdir(parents=True)
        mixin_dir.mkdir(parents=True)
        flow_library.mkdir(parents=True)
        api_dir.mkdir(parents=True)

        (mixin_dir / "mixin.js").write_text(
            """
            var apiList = {
              'foo_component': { save: Api.noForm.saveFoo, update: Api.noForm.updateFoo }
            }
            """,
            encoding="utf-8",
        )
        (api_dir / "index.js").write_text("export default {}", encoding="utf-8")
        (flow_library / "index.vue").write_text("<template><div/></template>", encoding="utf-8")
        (config_dir / "FooConfig.js").write_text(
            """
            const formMainConfig = [
              [
                { type: 'label', title: '名称', span: 4 },
                {
                  type: 'input',
                  prop: 'name',
                  span: 20,
                  rules: [{ required: true, message: '请输入名称' }]
                }
              ]
            ]
            export default formMainConfig
            """,
            encoding="utf-8",
        )
        (noform / "Foo.vue").write_text(
            """
            <script>
            const TYPE = {
              misleading: { name: '误导名字' }
            }
            import Api from '@/api';
            import config from './config/FooConfig';
            export default {
              name: 'foo_component',
              mixins: [],
              methods: {
                processData() { return { name: 'x' } },
                processSaveData() { return { id: 1 } },
                insertDataToForm() {},
                setDisableData() {}
              }
            }
            </script>
            <template>
              <div>
                <Flow ref="flow" />
                <CommonForm />
                <CommonFooter />
              </div>
            </template>
            """,
            encoding="utf-8",
        )
        (noform / "Bar.vue").write_text(
            """
            <script>
            export default {
              name: 'bar_component'
            }
            </script>
            <template><div>bar</div></template>
            """,
            encoding="utf-8",
        )
        return host

    def test_discover_host_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host = self.create_host_project(root)
            resolved = discover_host_project(root)
        self.assertEqual(resolved, host.resolve())

    def test_inspect_host_project_collects_components_and_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = self.create_host_project(Path(tmp))
            summary = inspect_host_project(host)

        self.assertEqual(summary["business_component_count"], 2)
        self.assertEqual(summary["config_count"], 1)
        self.assertIn("foo_component", summary["mixin_api_map"])
        foo = next(item for item in summary["business_components"] if item["name"] == "foo_component")
        self.assertTrue(foo["has_api_mapping"])
        self.assertIn("FooConfig.js", foo["config_imports"])
        self.assertTrue(foo["methods"]["processData"])
        self.assertTrue(any(item[0] == "name" for item in summary["common_field_props"]))
        self.assertTrue(any("bar_component 未在 mixin.js 的 apiList 中注册" in item for item in summary["warnings"]))

    def test_main_outputs_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = self.create_host_project(Path(tmp))
            output_path = Path(tmp) / "summary.json"
            exit_code = main(["--host-project", str(host), "--output", str(output_path)])

            self.assertEqual(exit_code, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["business_component_count"], 2)


if __name__ == "__main__":
    unittest.main()
