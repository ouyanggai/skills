---
name: formmaking-json-repair
description: 为 rsh-cloud 宿主平台修复、改写、排查和挑战已有 FormMaking 表单 JSON。适用于用户给出已有 JSON、现网页面异常、提交流程异常、字段校验失效、布局走样或联动错乱，希望在保留原表基础上定位并修正。不适用于从零生成新表单，也不适用于无表单流程或 NoFormFlow。
---

# FormMaking JSON 修复

## 适用边界

- 只处理“已有 FormMaking JSON”的修复、局部改造、运行时排查和 challenge。
- 如果目标是从零搭一个新表单，交给 `formmaking-json-generator`。
- `NoFormFlow` 明确排除；不要把无表单流程代码和 FormMaking JSON 混在一起。

## 先读哪里

- 先运行 [scripts/check_form_repair.py](scripts/check_form_repair.py) 做修复型检查：
  `python3 skills/formmaking-json-repair/scripts/check_form_repair.py <json文件>`
- 如果同一仓库里也有 `formmaking-json-generator`，再补跑它的结构校验：
  `python3 skills/formmaking-json-generator/scripts/validate_form_json.py --strict <json文件>`
- 修“字段联动、远程下拉、提交前转换、必填失效”时，读 [references/repair-patterns.md](references/repair-patterns.md)。
- 如果 bug 牵涉宿主自定义组件、布局壳层或运行时样式，再去对照：
  `skills/formmaking-json-generator/references/host-custom-components.md`
  `skills/formmaking-json-generator/references/formmaking-json-rules.md`

## 工作流

1. 先定症状。
   归一化为“预期行为、实际行为、触发动作、影响字段、是否只在某种流程态出现”。
2. 再定落点。
   不要先重做整张表；先在现有 JSON 里定位具体分区、字段、`eventScript`、`dataSource`、`beforeSubmitAndDraft`。
3. 给 bug 分类。
   常见是：必填不拦截、联动后陈旧值残留、显隐/禁用状态不对、回填覆盖用户输入、提交映射错误、布局多套一层。
4. 做最小修复。
   优先改最直接的字段、脚本和提交流程，不要无关重排 key/model/结构。
5. 做闭环验证。
   至少跑 repair 检查脚本；有条件再跑结构校验。需要提交流程兜底时，同时检查 `beforeSubmitAndDraft`。

## 修复规则

- 必填问题不能只看红星或 `options.required`；必须检查 `rules` 是否真的存在、提示是否中文、提交流程是否会绕过前端校验。
- 明细表/子表单里，如果上游字段切换后会刷新下游选项，必须同步清空当前行下游旧值；只刷新 `setOptionData(...)` 不够。
- 上游切换会让下游字段重新必填时，清空旧值后最好立刻 `validate()`，避免界面看起来空了但底层还保留旧值。
- 如果运行时顺序不稳定，或者平台可能在某些场景绕过前端校验，`beforeSubmitAndDraft` 里要补业务兜底，并给中文错误提示。
- 回填展示字段应优先 `disabled: true` 置灰；不要只改成不可输入但样式仍像正常可编辑字段。
- 布局修复优先删冗余容器、消双重边框、补齐壳层宽度，不要为修一个局部问题重做整张表。

## 输出要求

- 默认直接给修后的 JSON 或补丁。
- 额外说明只写“改了什么、为什么能解决问题、还有什么假设”。
- 如果发现问题不止一处，要把同类风险一起指出，但不要顺手改无关逻辑。
