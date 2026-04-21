# 无表单权限与提交流程

## 1. 字段权限来源

无表单审核态字段权限来自：

- `Api.qualityManage.findApprovePermission`

返回的核心字段是：

- `flowNodeFieldPowerTemplateList[].formFieldTemplateEnglishName`

宿主前端把它视为“当前节点允许编辑的字段名列表”。

## 2. 审核态禁用规则

高频实现方式：

1. 先把所有可录入字段默认 `disabled = true`
2. 再把权限列表中的字段打开

常见代码形态是每个业务组件自己实现一个 `setDisableData(data)` 或递归版本。

结论：

- 权限粒度是字段 `prop`
- 审核态不要手写白名单常量顶替后端配置
- 查看态通常比审核态更简单，直接全禁用

## 3. 业务保存链

`mixin.js` 提供统一业务保存链：

- `saveBiz()`
  走 `processSaveData()` + `saveData(..., 'update')`
- `submit(status)`
  先 `checkFlowPermission()`，再保存业务，再提交流程
- `reSubmit(type)`
  重提场景先更新业务，再通过 `Flow.reSubmit()` 重新提交流程
- `saveData(data, type)`
  根据组件 `name` 去 `apiList` 里找对应接口

结论：

- 新业务组件如果没补 `apiList`，保存和提交都会断
- 组件 `name` 和 `apiList` key 必须一致

## 4. 流程提交链

无表单流程最终由 `Flow.vue` 负责。

关键步骤：

1. `checkFlowPermission()`
   调 `Api.schedule.saveFlowInstance` 做首发权限校验
2. `beforeHandle()`
   决定是否草稿、是否需要选人、是否需要手动分支
3. `submitFinal()`
   真正调用 `saveFlowInstance` / `saveFlowInstanceAgain`

## 5. 无表单提交 payload 重点

`submitFinal()` 的关键参数：

- `data.flowProxyId`
- `data.status = 'draft'`（草稿时）
- `data.id`（重提时）
- `flowInstanceBizRelevanceList`
- `formDataMongoVo.data`
- `nextAuditorList`
- `fixedExecuteNodeId`

其中 `flowInstanceBizRelevanceList` 至少常见两条：

- `project`
- 当前业务组件名，例如 `contract_review`

## 6. 选人、并行、分支

`Flow.vue` 已经实现了这些宿主约定：

- 自选审批人 `run_node_choose`
- 并行节点审批人自选
- 手动分支选择
- 主管 / 分管副总自动带出
- 自动带出失败后降级为人工选择

结论：

- 新无表单流程不要另造一套选人弹窗逻辑
- 业务组件只需正确挂 `Flow` 并传递标准 props

## 7. 附件处理

`mixin.js` 已经封装：

- `saveBatchFile(fileIds, relationId)`
- `getBatchFile(id)`

规则：

- 业务接口保存成功拿到 `bizId` 后，再批量绑附件
- 查看/审核态附件通常 `showOnly`
