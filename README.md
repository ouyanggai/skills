# ouyanggai skills

个人 AI skills monorepo，用于统一管理、测试和分发可安装的技能。

## 安装

安装整个技能仓库：

```bash
npx skills add ouyanggai/skills
```

只安装指定技能：

```bash
npx skills add https://github.com/ouyanggai/skills --skill formmaking-json-generator
```

安装后，在支持 skills 的客户端里直接调用 `formmaking-json-generator` 即可。

## 当前技能

| Skill | 说明 |
| --- | --- |
| `formmaking-json-generator` | 为 rsh-cloud 宿主平台生成、改写、审查和解释 FormMaking 表单 JSON |

## 目录结构

```text
skills/
  formmaking-json-generator/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
tests/
  formmaking-json-generator/
scripts/
  check.py
```

## 校验

运行全部仓库校验：

```bash
python3 scripts/check.py
```

单独校验一个生成的 FormMaking JSON：

```bash
python3 skills/formmaking-json-generator/scripts/validate_form_json.py --strict path/to/form.json
```

## 新环境首次使用

`formmaking-json-generator` 需要了解当前使用者本地宿主工程、FormMaking 源码和真实样本目录。首次使用时在工作区运行：

```bash
python3 skills/formmaking-json-generator/scripts/discover_context.py --workspace .
```

如果自动发现失败，可以显式传入路径：

```bash
python3 skills/formmaking-json-generator/scripts/discover_context.py \
  --workspace . \
  --host-project /path/to/host-project \
  --formmaking-source /path/to/vue-form-making \
  --sample-dir /path/to/form-json-samples
```

脚本会把本地配置保存到 `.formmaking-json-generator/context.json`，这个文件不会提交。
