import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "noform-flow-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_noform_component import main, validate_host_project  # noqa: E402


class ValidateNoFormComponentTests(unittest.TestCase):
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
              'good_component': { save: Api.noForm.saveGood, update: Api.noForm.updateGood }
            }
            """,
            encoding="utf-8",
        )
        (api_dir / "index.js").write_text("export default {}", encoding="utf-8")
        (flow_library / "index.vue").write_text("<template><div/></template>", encoding="utf-8")

        (config_dir / "GoodConfig.js").write_text(
            """
            export default [
              [
                { type: 'label', title: '名称', span: 4 },
                {
                  type: 'input',
                  prop: 'name',
                  span: 20,
                  rules: [{ required: true, message: '请输入名称', trigger: 'blur' }]
                }
              ]
            ]
            """,
            encoding="utf-8",
        )
        (config_dir / "BadConfig.js").write_text(
            """
            export default [
              [
                {
                  type: 'input',
                  prop: 'code',
                  span: 24,
                  rules: [{ required: true, message: 'Code is required', trigger: 'blur' }]
                }
              ]
            ]
            """,
            encoding="utf-8",
        )

        (noform / "Good.vue").write_text(
            """
            <script>
            import mixin from './mixin/mixin'
            import cfg from './config/GoodConfig'
            export default {
              name: 'good_component',
              mixins: [mixin],
              methods: {
                processData() { return {} },
                processSaveData() { return {} },
                insertDataToForm() {},
                setDisableData() {},
                mountedExamine() {
                  this.getInputPermision()
                }
              }
            }
            </script>
            <template>
              <div>
                <CommonForm />
                <CommonFooter />
                <Flow ref="flow" />
                <div v-if="operaType == 'create' || operaType == 'edit' || operaType == 'examine' || operaType == 'preview'"></div>
              </div>
            </template>
            """,
            encoding="utf-8",
        )
        (noform / "Bad.vue").write_text(
            """
            <script>
            import cfg from './config/BadConfig'
            export default {
              name: 'bad_component',
              methods: {
                processData() { return {} }
              }
            }
            </script>
            <template><div><CommonForm /></div></template>
            """,
            encoding="utf-8",
        )
        return host

    def test_validate_host_project_collects_errors_and_warnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = self.create_host_project(Path(tmp))
            result = validate_host_project(host)

        self.assertEqual(result["component_count"], 2)
        self.assertGreaterEqual(result["error_count"], 2)
        self.assertGreaterEqual(result["warning_count"], 1)
        bad = next(item for item in result["reports"] if item["component"] == "bad_component")
        self.assertTrue(any("apiList" in err["message"] for err in bad["errors"]))
        self.assertTrue(any("非中文校验提示" in warn["message"] for warn in bad["warnings"]))

    def test_main_outputs_json_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            host = self.create_host_project(Path(tmp))
            output = Path(tmp) / "result.json"
            saved_stdout = sys.stdout
            try:
                with output.open("w", encoding="utf-8") as fh:
                    sys.stdout = fh
                    exit_code = main(["--host-project", str(host), "--component", "good_component"])
            finally:
                sys.stdout = saved_stdout

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["component_count"], 1)
            self.assertEqual(payload["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
