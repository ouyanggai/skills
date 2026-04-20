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

from discover_context import context_path, discover, main  # noqa: E402


class DiscoverContextTests(unittest.TestCase):
    def test_discover_finds_expected_local_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)

            host = workspace / "rsh-cloud-invest-power-system-test"
            (host / "src" / "components" / "Custom").mkdir(parents=True)
            (host / "src" / "main.js").write_text("", encoding="utf-8")

            formmaking = workspace / "rsh-cloud-vue-form-making"
            (formmaking / "src" / "components").mkdir(parents=True)
            (formmaking / "src" / "components" / "GenerateForm.vue").write_text("", encoding="utf-8")
            (formmaking / "src" / "components" / "GenerateElementItem.vue").write_text("", encoding="utf-8")

            sample_dir = workspace / "analysis" / "form-proxy-samples" / "raw"
            sample_dir.mkdir(parents=True)
            (sample_dir / "示例_demo.json").write_text("{}", encoding="utf-8")

            context = discover(workspace)

            self.assertEqual(context["host_project"], str(host.resolve()))
            self.assertEqual(context["formmaking_source"], str(formmaking.resolve()))
            self.assertEqual(context["sample_dir"], str(sample_dir.resolve()))

    def test_main_writes_context_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            host = workspace / "host"
            formmaking = workspace / "formmaking"
            sample_dir = workspace / "samples"
            host.mkdir()
            formmaking.mkdir()
            sample_dir.mkdir()

            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "--workspace",
                        str(workspace),
                        "--host-project",
                        str(host),
                        "--formmaking-source",
                        str(formmaking),
                        "--sample-dir",
                        str(sample_dir),
                    ]
                )

            self.assertEqual(exit_code, 0)
            saved = json.loads(context_path(workspace).read_text(encoding="utf-8"))
            self.assertEqual(saved["host_project"], str(host.resolve()))
            self.assertEqual(saved["formmaking_source"], str(formmaking.resolve()))
            self.assertEqual(saved["sample_dir"], str(sample_dir.resolve()))


if __name__ == "__main__":
    unittest.main()
