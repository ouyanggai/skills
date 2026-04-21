import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from inspect_host_components import inspect_host_project, main, parse_main_registry  # noqa: E402


MAIN_JS = """
import MyInfoSelect from '@/components/Custom/components/MyInfoSelect/index.vue';
import MyBusiness from '@/components/Custom/components/Business/MyBusiness.vue';

Vue.use(FormMaking, {
  components: [
    {
      name: 'my-info-select',
      component: MyInfoSelect
    },
    {
      name: 'my-business',
      component: MyBusiness
    }
  ]
});
"""


CUSTOM_JSON = """
const customJson = [
  {
    type: 'custom',
    el: 'my-info-select',
    name: '信息选择',
    options: {
      width: '',
      customClass: '',
      extendProps: {},
      customProps: {}
    },
    events: {
      onChange: '',
      onFocus: ''
    }
  },
  {
    type: 'custom',
    el: 'my-business',
    name: '业务块',
    options: {
      width: '',
      customClass: 'tableNoPadding',
      extendProps: {
        businessId: '',
        isFlowInitiate: false
      }
    },
    events: {
      onChange: ''
    }
  }
]
"""


INFO_SELECT_VUE = """
<script>
export default {
  name: 'MyInfoSelect',
  props: {
    value: {
      type: String,
      default: ''
    },
    disabled: {
      type: Boolean,
      default: false
    },
    printRead: {
      type: Boolean,
      default: false
    }
  },
  watch: {
    value(val) {
      this.currentInfoObj = val
    },
    currentInfoObj(val) {
      this.$parent.$set(this.$parent.dataModels, this.$parent.modelName + '__condition', JSON.parse(val).name)
      this.$parent.$set(this.$parent.dataModels, this.$parent.modelName + '__formPersonId', JSON.parse(val).id)
      this.$nextTick(() => {
        this.$parent.$parent.validate()
      })
      this.$emit('input', val)
    }
  }
}
</script>
<!-- 字段可以是newUserName、userName2等包含userName -->
"""


BUSINESS_VUE = """
<script>
export default {
  name: 'MyBusiness',
  props: {
    isFlowInitiate: {
      type: Boolean,
      default: false
    },
    businessId: {
      type: String,
      default: ''
    }
  }
}
</script>
"""


class InspectHostComponentsTests(unittest.TestCase):
    def create_host_project(self, root: Path) -> tuple[Path, Path]:
        host = root / "host-project"
        (host / "src" / "components" / "Custom" / "components" / "MyInfoSelect").mkdir(parents=True)
        (host / "src" / "components" / "Custom" / "components" / "Business").mkdir(parents=True)
        (host / "src" / "main.js").write_text(MAIN_JS, encoding="utf-8")
        (host / "src" / "components" / "Custom" / "customJson.js").write_text(CUSTOM_JSON, encoding="utf-8")
        (host / "src" / "components" / "Custom" / "components" / "MyInfoSelect" / "index.vue").write_text(
            INFO_SELECT_VUE,
            encoding="utf-8",
        )
        (host / "src" / "components" / "Custom" / "components" / "Business" / "MyBusiness.vue").write_text(
            BUSINESS_VUE,
            encoding="utf-8",
        )

        sample_dir = root / "analysis" / "form-proxy-samples" / "raw"
        sample_dir.mkdir(parents=True)
        (sample_dir / "sample_1.json").write_text(
            json.dumps({"list": [{"type": "custom", "el": "my-info-select"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        (sample_dir / "sample_2.json").write_text(
            json.dumps({"list": [{"type": "custom", "el": "my-info-select"}, {"type": "custom", "el": "my-business"}]}, ensure_ascii=False),
            encoding="utf-8",
        )
        return host, sample_dir

    def test_parse_main_registry_resolves_source_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, _sample_dir = self.create_host_project(root)
            registry = parse_main_registry(host)

            self.assertEqual(registry["my-info-select"]["import_name"], "MyInfoSelect")
            self.assertTrue(registry["my-info-select"]["source_file"].endswith("MyInfoSelect/index.vue"))
            self.assertTrue(registry["my-business"]["source_file"].endswith("Business/MyBusiness.vue"))
            self.assertTrue(Path(registry["my-info-select"]["source_file"]).exists())
            self.assertTrue(Path(registry["my-business"]["source_file"]).exists())

    def test_inspect_host_project_collects_tags_and_sample_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, sample_dir = self.create_host_project(root)
            summary = inspect_host_project(host, sample_dir)

            self.assertEqual(summary["component_count"], 2)
            info_select = next(item for item in summary["components"] if item["el"] == "my-info-select")
            business = next(item for item in summary["components"] if item["el"] == "my-business")

            self.assertEqual(info_select["sample_count"], 2)
            self.assertEqual(info_select["value_shape"], "JSON字符串")
            self.assertIn("writes-virtual-condition", info_select["tags"])
            self.assertIn("writes-virtual-form-person-id", info_select["tags"])
            self.assertIn("calls-parent-validate", info_select["tags"])
            self.assertIn("semantic-model-required", info_select["tags"])
            self.assertEqual(info_select["risk_level"], "宿主约束型")

            self.assertEqual(business["sample_count"], 1)
            self.assertIn("has-extend-props", business["tags"])
            self.assertEqual(business["risk_level"], "业务专用")

    def test_main_outputs_json_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, sample_dir = self.create_host_project(root)
            with redirect_stdout(StringIO()) as stdout:
                exit_code = main(
                    [
                        "--workspace",
                        str(root),
                        "--host-project",
                        str(host),
                        "--sample-dir",
                        str(sample_dir),
                        "--format",
                        "json",
                    ]
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["component_count"], 2)
            self.assertEqual(payload["components"][0]["el"], "my-info-select")


if __name__ == "__main__":
    unittest.main()
