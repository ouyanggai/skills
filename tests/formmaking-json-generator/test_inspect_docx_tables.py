import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "skills" / "formmaking-json-generator" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from inspect_docx_tables import parse_docx_tables  # noqa: E402


class InspectDocxTablesTests(unittest.TestCase):
    def test_parse_table_grid_spans_and_fill(self):
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:tbl>
      <w:tblGrid>
        <w:gridCol w:w="1000"/>
        <w:gridCol w:w="2000"/>
      </w:tblGrid>
      <w:tr>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="1000" w:type="dxa"/>
            <w:shd w:fill="EDEDED"/>
          </w:tcPr>
          <w:p><w:r><w:t>标签</w:t></w:r></w:p>
        </w:tc>
        <w:tc>
          <w:tcPr>
            <w:tcW w:w="2000" w:type="dxa"/>
          </w:tcPr>
          <w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:t>内容</w:t></w:r></w:p>
        </w:tc>
      </w:tr>
      <w:tr>
        <w:tc>
          <w:tcPr>
            <w:gridSpan w:val="2"/>
          </w:tcPr>
          <w:p><w:r><w:t>合并分区</w:t></w:r></w:p>
        </w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
        with tempfile.TemporaryDirectory() as tmp:
            docx_path = Path(tmp) / "sample.docx"
            with ZipFile(docx_path, "w") as docx:
                docx.writestr("word/document.xml", document_xml)

            result = parse_docx_tables(docx_path)

        self.assertEqual(result["table_count"], 1)
        table = result["tables"][0]
        self.assertEqual(table["grid_widths_twip"], ["1000", "2000"])
        self.assertEqual(table["rows"][0]["cells"][0]["text"], "标签")
        self.assertEqual(table["rows"][0]["cells"][0]["fill"], "EDEDED")
        self.assertEqual(table["rows"][0]["cells"][1]["text_align"], "center")
        self.assertEqual(table["rows"][1]["cells"][0]["colspan"], 2)


if __name__ == "__main__":
    unittest.main()
