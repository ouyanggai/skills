#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require_skill_files() -> None:
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        raise AssertionError("缺少 skills 目录")

    missing: list[str] = []
    for skill_dir in sorted(item for item in skills_dir.iterdir() if item.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            missing.append(str(skill_file.relative_to(ROOT)))

    if missing:
        raise AssertionError("缺少 SKILL.md: " + ", ".join(missing))


def validate_manifest() -> None:
    manifest_path = ROOT / "skills.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in data.get("skills", []):
        skill_path = ROOT / item["path"]
        if not skill_path.exists():
            raise AssertionError(f"manifest 指向不存在的技能目录: {item['path']}")
        if not (skill_path / "SKILL.md").exists():
            raise AssertionError(f"manifest 指向的技能缺少 SKILL.md: {item['path']}")


def run_unittest() -> None:
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)


def run_generated_case_validation() -> None:
    validator = ROOT / "skills" / "formmaking-json-generator" / "scripts" / "validate_form_json.py"
    case_dir = ROOT / "tests" / "formmaking-json-generator" / "generated_cases"
    if not case_dir.exists():
        return

    for case in sorted(case_dir.glob("*.json")):
        subprocess.run(
            [sys.executable, str(validator), "--strict", str(case)],
            cwd=str(ROOT),
            check=True,
        )


def main() -> int:
    require_skill_files()
    validate_manifest()
    run_unittest()
    run_generated_case_validation()
    print("全部校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
