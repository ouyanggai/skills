---
name: noform-flow-generator
description: 为 rsh-cloud 宿主平台生成、改写、审查和解释无表单流程代码。适用于用户要在 `rsh-cloud-invest-power-system*` 宿主项目里新增或修改无表单流程页面、字段配置、表格配置、校验逻辑、节点字段权限、提交流程或重提逻辑的场景。不适用于 FormMaking JSON 或普通有表单流程。
---

# 无表单流程生成

## 适用边界

- 只处理宿主项目里的无表单流程实现。
- 产物通常是 Vue 组件、配置 JS、流程库无表单节点配置，不是 FormMaking JSON。
- 不要把本 skill 和 `formmaking-json-generator` 混用；有表单流程走 FormMaking，无表单流程走本 skill。

## 先读哪里

- 开始前先运行 [scripts/inspect_noform_host.py](scripts/inspect_noform_host.py) 盘点当前宿主里的无表单组件、配置文件、API 映射和警告项：
  `python3 skills/noform-flow-generator/scripts/inspect_noform_host.py --workspace .`
- 需要理解整体骨架时，先读 [references/noform-architecture.md](references/noform-architecture.md)。
- 需要写字段、表格、校验时，再读 [references/noform-field-rules.md](references/noform-field-rules.md)。
- 需要处理字段权限、保存草稿、提交、重提、并行/分支选人时，再读 [references/noform-permission-and-submit.md](references/noform-permission-and-submit.md)。
- 需要新增或修改无表单流程模板、节点字段权限、类型字段树时，再读 [references/noform-flow-library.md](references/noform-flow-library.md)。

## 本地上下文

- 默认只依赖宿主工程；不依赖 `raw` 样本。
- 优先从当前工作区自动寻找 `rsh-cloud-invest-power-system*` 目录。
- 如果自动发现失败，只向使用者询问一项：全过程管理平台的目录（开发目录）。
- 不要把某个人机器上的绝对路径硬写进 skill 文档或生成逻辑。

## 工作流

1. 先定目标。
   明确这次是新增无表单组件、修改现有组件、补字段权限、补提交流程，还是改流程库模板。
2. 找准绑定键。
   无表单组件的 `name`、`mixin.js` 里的 `apiList` key、审批侧 `auditWay/currentComponent`、以及业务 `otherBiz` 通常要保持一致。
3. 先选结构。
   普通字段区优先 `CommonForm`；明细行或嵌套列优先 `SimpleTable`；复杂页面常见“`CommonForm + SimpleTable + 选择弹窗 + Flow`”混合结构。
4. 写字段配置。
   在 `config/*.js` 里定义字段、`rules`、`slot.rules`、`children`、事件钩子占位。
5. 写页面组件。
   统一遵循宿主的 `operaType` 四态：`create / edit / examine / preview`。
   需要包含或明确处理：`Flow`、`CommonFooter`、`mixin`、`processData`、`processSaveData`、`insertDataToForm`、`setDisableData`。
6. 接业务 API。
   新建/编辑页要补 `Api.noForm.*` 查询与保存接口；如果是新类型，要同步补 `mixin.js` 的 `apiList`。
7. 接权限与提交流程。
   审核态字段权限依赖 `findApprovePermission` 返回的 `formFieldTemplateEnglishName`；提交流程走 `Flow.vue` 和 `Api.schedule.saveFlowInstance*`。
8. 验证一致性。
   再跑 `inspect_noform_host.py`，确认组件名、配置、API 映射和警告项符合预期。

## 生成规则

- 组件 `name` 不要随意取名；默认与流程类型编码、`apiList` key、审批侧 `currentComponent` 保持一致，例如 `contract_review`、`buy_plan`。
- 宿主通过 `require.context("@/components/NoFormFLow/", false, /\.vue$/)` 自动注册顶层无表单组件；新组件通常不需要手写 import 清单，但必须放在 `src/components/NoFormFLow/` 顶层。
- `CommonForm` 的字段配置是“二维行列数组”；`SimpleTable` 的配置是对象，列定义走 `column`，可编辑单元格走 `slot`。
- 基础字段校验写在字段 `rules`；表格单元格校验写在 `column[].slot.rules`。
- 动态联动优先挂在配置对象的 `changeEvent` / `inputEvent` / `clickEvent`，并在组件 `created` 中通过 `assignValue` 注入具体方法。
- 审核态和查看态不要直接删字段；优先统一走 `setDisableData`，按 `flowNodeFieldPowerTemplateList` 的字段名启用可编辑项。
- `processData` 负责把页面状态转成提交业务接口所需的 payload；
  `processSaveData` 负责在编辑/重提时把变更合并回原始对象。
- 提交流程前先过 `Flow.checkFlowPermission()`；无权限时要给出中文提示，不要静默失败。
- 无表单发起/重提最终走 `Flow.submitFinal()`：
  `flowInstanceBizRelevanceList` 至少要带 `project` 和当前业务组件名两条关联。
- 草稿与正式提交要分开：
  宿主约定 `submit(0)` 是草稿、`submit(1)` 是提交；重提时 `reSubmit('save'|'submit')` 也要保持同样语义。
- 新流程类型如果要出现在流程库或业务入口，除页面和 API 外，通常还要检查 `src/store/modules/settings.js`、对应业务入口页面以及流程库类型列表的联动。

## 交付前检查

- 检查组件 `name`、`apiList` key、调用侧 `currentComponent/auditWay` 是否一致。
- 检查 `create / edit / examine / preview` 四态是否都明确处理。
- 检查 `rules`、`slot.rules`、中文校验提示是否齐全。
- 检查审核态是否真正按权限禁用字段，而不是整页都能改。
- 检查 `processData/processSaveData/insertDataToForm` 是否闭环，避免查看能回显、保存却丢字段。
- 检查 `Flow` 提交参数是否包含 `project` 关联和业务 `otherBiz` 关联。
- 检查新建组件后宿主是否能通过自动注册加载到。

## 输出要求

- 默认给出需要修改的代码方案并直接落地到文件。
- 如果新增了无表单流程类型，说明还改了哪些映射位。
- 如果流程或字段权限依赖后端类型/字典，明确写出依赖点。

## 禁止事项

- 不要混入 FormMaking JSON 规则。
- 不要假设宿主会自动识别新业务类型；需要的映射项必须显式补齐。
- 不要把审核态字段权限写死成前端常量而绕开流程节点配置。
- 不要跳过 `mixin.js` 和 `Flow.vue` 现有约定，另造一套提交流程。
