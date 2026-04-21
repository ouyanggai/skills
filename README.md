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

```bash
npx skills add https://github.com/ouyanggai/skills --skill noform-flow-generator
```

安装后，在支持 skills 的客户端里直接调用对应 skill 即可。

## 当前技能

| Skill | 说明 |
| --- | --- |
| `formmaking-json-generator` | 为 rsh-cloud 宿主平台生成、改写、审查和解释 FormMaking 表单 JSON |
| `noform-flow-generator` | 为 rsh-cloud 宿主平台生成、改写、审查和解释无表单流程代码 |

## 目录结构

```text
skills/
  formmaking-json-generator/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
  noform-flow-generator/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
tests/
  formmaking-json-generator/
  noform-flow-generator/
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

分析 Word 表格结构，辅助按原表还原布局：

```bash
python3 skills/formmaking-json-generator/scripts/inspect_docx_tables.py path/to/form.docx
```

分析一批真实 raw 样本的宽度、壳层 class、styleSheets 和审批区模式：

```bash
python3 skills/formmaking-json-generator/scripts/analyze_sample_patterns.py --workspace .
```

盘点宿主项目里的无表单流程组件、配置、API 映射和流程库入口：

```bash
python3 skills/noform-flow-generator/scripts/inspect_noform_host.py --workspace .
```

校验无表单组件是否符合宿主约定：

```bash
python3 skills/noform-flow-generator/scripts/validate_noform_component.py --workspace .
```

## 新环境首次使用

第一次使用时，只需要告诉 `formmaking-json-generator` 三个目录：

- 全过程管理平台的目录（你的开发目录，比如 `rsh-cloud-invest-power-system-test`）
- FormMaking 源码目录
- 生成的 JSON 保存目录

推荐直接这样配置：

```bash
python3 skills/formmaking-json-generator/scripts/discover_context.py \
  --platform-dir /path/to/rsh-cloud-invest-power-system-test \
  --formmaking-dir /path/to/vue-form-making \
  --json-dir /path/to/form-json-output
```

如果这些目录就在当前工作区附近，也可以先让脚本自动找：

```bash
python3 skills/formmaking-json-generator/scripts/discover_context.py --workspace .
```

如果有历史真实表单 JSON 样本目录，可额外加 `--sample-dir /path/to/form-json-samples`，便于生成时参考真实表单规律。
这一项只属于当前使用者本机的本地增强输入，不是安装 skill 后的必填前置；没有它，skill 也应继续依靠宿主源码、FormMaking 源码、用户需求和校验脚本完成生成。
脚本会把本地配置保存到 `.formmaking-json-generator/context.json`，这个文件不会提交。
