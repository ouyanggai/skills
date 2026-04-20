#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import BadZipFile, ZipFile


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = NS["w"]


def w_attr(node: ET.Element | None, name: str) -> str:
    if node is None:
        return ""
    return node.get(f"{{{W}}}{name}", "") or ""


def find_w(node: ET.Element | None, path: str) -> ET.Element | None:
    if node is None:
        return None
    return node.find(path, NS)


def text_content(node: ET.Element) -> str:
    return "".join(item.text or "" for item in node.findall(".//w:t", NS)).strip()


def parse_cell(cell: ET.Element, index: int) -> dict[str, object]:
    props = find_w(cell, "w:tcPr")
    width_node = find_w(props, "w:tcW")
    shading_node = find_w(props, "w:shd")
    grid_span_node = find_w(props, "w:gridSpan")
    vmerge_node = find_w(props, "w:vMerge")
    valign_node = find_w(props, "w:vAlign")
    first_jc_node = find_w(cell, ".//w:pPr/w:jc")

    colspan = w_attr(grid_span_node, "val")
    return {
        "index": index,
        "text": text_content(cell),
        "colspan": int(colspan) if colspan.isdigit() else 1,
        "vmerge": w_attr(vmerge_node, "val"),
        "width_twip": w_attr(width_node, "w"),
        "fill": w_attr(shading_node, "fill"),
        "vertical_align": w_attr(valign_node, "val"),
        "text_align": w_attr(first_jc_node, "val"),
    }


def parse_docx_tables(path: Path) -> dict[str, object]:
    try:
        with ZipFile(path) as docx:
            document_xml = docx.read("word/document.xml")
    except (BadZipFile, KeyError) as exc:
        raise RuntimeError(f"无法读取 docx 文档结构: {exc}") from exc

    root = ET.fromstring(document_xml)
    tables = []
    for table_index, table in enumerate(root.findall(".//w:tbl", NS)):
        grid_widths = [
            w_attr(grid_col, "w")
            for grid_col in table.findall("./w:tblGrid/w:gridCol", NS)
        ]
        rows = []
        for row_index, row in enumerate(table.findall("./w:tr", NS)):
            cells = [
                parse_cell(cell, cell_index)
                for cell_index, cell in enumerate(row.findall("./w:tc", NS))
            ]
            rows.append({"index": row_index, "cells": cells})

        tables.append(
            {
                "index": table_index,
                "grid_widths_twip": grid_widths,
                "row_count": len(rows),
                "rows": rows,
            }
        )

    return {"source": str(path), "table_count": len(tables), "tables": tables}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="提取 Word docx 表格的行列、合并、宽度和底色信息")
    parser.add_argument("docx", help="docx 文件路径")
    parser.add_argument("--compact", action="store_true", help="输出紧凑 JSON")
    args = parser.parse_args(argv)

    path = Path(args.docx).expanduser().resolve()
    if not path.exists():
        print(f"[ERROR] 文件不存在: {path}", file=sys.stderr)
        return 2

    try:
        result = parse_docx_tables(path)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=None if args.compact else 2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
