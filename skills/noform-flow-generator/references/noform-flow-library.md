# 无表单流程库规则

## 1. 页面入口

无表单流程模板设计入口在：

- `src/views/flowLibrary/NoFormMulBranch/index.vue`

它本质上是两步：

1. `Steps1` 基础信息
2. `Steps3` 流程设计

`Steps2` 表单设计在无表单模式下被跳过。

## 2. 字段树来源

`Steps1` 里：

- 先选 `typeId`
- 再从类型对象上取 `auditWay`
- 用 `Api.algorithm.getDicCodeTree({ dictCode: auditWay })` 拉字段树

这个字段树会作为：

- 节点字段权限选择源
- 条件分支字段选择源
- 最终 `formTemplateVo.fieldsTemplateList` 的来源

## 3. 节点字段权限结构

无表单流程节点权限核心结构：

```js
flowNodeFieldPowerTemplateList: [
  {
    fieldPower: 'edit',
    formFieldTemplateEnglishName: 'contractNumber'
  }
]
```

当前宿主无表单节点里高频就是 `edit` 权限。

## 4. 节点设计页要点

`nodeWrap.vue` 里：

- 普通审批节点可选择字段权限
- 条件节点可选择条件字段
- 字段权限和条件字段都基于 `fieldTreeList`

结论：

- 无表单流程设计时，字段名必须和业务页里的 `prop` 一致
- 否则审核态开不了权限，条件节点也无法命中

## 5. 保存流程模板 payload

`saveCustomFlowTemplate()` 保存无表单流程时会带：

- `typeId`
- `flowName`
- `groupId`
- `remark`
- `formExist: 'noForm'`
- `formTemplateVo`
- `flowNodeTemplate`

其中 `formTemplateVo.templateData = null`，但 `fieldsTemplateList` 仍然存在。

说明：

- 无表单流程虽然没有 FormMaking JSON，但流程模板仍然会存一份字段元数据
- 这份字段元数据来自 `fieldTreeList`

## 6. 新增或修改无表单类型时的注意点

- 业务页字段 `prop` 要和流程库字段元数据语义一致
- 需要审核字段权限时，流程库里必须能选到这些字段
- 修改类型后，已有节点设计会被清空；宿主已经有对应提示，不要静默更换
