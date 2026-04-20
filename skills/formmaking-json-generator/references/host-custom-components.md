# 宿主自定义组件

## 1. 注册总览

宿主自定义组件以当前工作区的宿主工程为准。首次使用时先通过 `scripts/discover_context.py` 定位宿主工程；然后检查 `{host_project}/src/main.js`、`{host_project}/src/components/Custom/customJson.js` 和 `{host_project}/src/components/Custom/components/`。

下面清单来自一组已分析样本，括号内是样本节点出现次数。迁移到新环境后，如果宿主注册组件或样本不同，应以本地源码和样本重新确认。

- `custom-upload-excel`（1）
- `out-bound-material-select`（2）
- `in-bound-material-select`（1）
- `custom-weather`（2）
- `custome-select-project`（16）
- `custome-expense-budgetType`（0）
- `general-list-select-show`（31）
- `person-mulSelect`（0）
- `general-flow-list-mulSelect`（1）
- `custome-info-select`（145）
- `ltd-or-dep-select`（5）
- `custome-file-view`（0）
- `custome-file-import`（4）
- `legal-contract-doctable`（3）
- `contract-seal-review-business`（3）
- `flow-list-mul-select`（6）
- `request_payout`（1）

使用原则：

- 高频且语义稳定的组件，可以直接纳入默认生成策略
- 强业务组件，只在需求明确对齐时才用
- 零样本或极低频组件，不要主动发明用法
- 这类选择组件大多把 `value` 当成 JSON 字符串处理；生成时优先给合法 JSON 默认值，不要直接留空字符串

## 2. 选择顺序

- 人员、部门、公司、岗位：先看 `custome-info-select`
- 公司/部门范围单选或多选：先看 `ltd-or-dep-select`
- 单个合同、单个流程、单个业务对象：先看 `general-list-select-show`
- 多个流程对象：再区分 `flow-list-mul-select` 和 `general-flow-list-mulSelect`
- 项目：先看 `custome-select-project`
- 模板导入类附件：先看 `custome-file-import`

## 3. 高频通用组件

### `custome-info-select`

用途：

- 选择人员、部门、公司、岗位

源码约束：

- 组件通过字段名识别选择类型
- `model` 必须包含以下关键字之一：
  `userName`、`depName`、`companyName`、`dutyName`
- 不要求完全等于，包含即可，例如：
  `handlingUserName`、`myDepName`、`contractCompanyName`

值形态：

- `value` 是 JSON 字符串
- 组件运行时会读取其中的 `name`、`id`

额外副作用：

- 会向表单数据里写入两个虚拟字段：
  - `<model>__condition`
  - `<model>__formPersonId`

适合场景：

- 经办人
- 经办部门
- 经办公司
- 审批人
- 合同主体公司

参考源码：

- `{host_project}/src/components/Custom/components/CustomeInfoSelect/index.vue`

### `general-list-select-show`

用途：

- 单选一个已有合同、流程或业务对象，并支持查看详情

值形态：

- `value` 是 JSON 字符串
- 常见字段：
  `name`、`rowData`、`formType`、`selectCompanyId`

隐含逻辑：

- 某些表单需要先在 `refresh` 中注入上下文，例如：
  `this.setData({ contractObj: JSON.stringify({ initiatorCompanyId }) })`
- 当 `formType == 'contract_receipt_form'` 时，组件会先检查是否已选收款单位

适合场景：

- 合同选择
- 手续文件选择
- 单个流程对象关联

参考源码：

- `{host_project}/src/components/Custom/components/GeneralListSelectShow/index.vue`

### `custome-select-project`

用途：

- 选择项目

适合场景：

- 所属项目
- 立项关联项目
- 合同或请款的项目归属

参考样本：

- `analysis/form-proxy-samples/raw/公司合同合规评审_contract_compliance_review.json`
- `analysis/form-proxy-samples/raw/公司合同付款申请表类型_contract_payment_form_c44d202f6d3f4b659372ced254d6da4b.json`

### `ltd-or-dep-select`

用途：

- 集团公司或部门单选/多选

源码约束：

- `model` 包含 `singleSelect` 表示单选
- `model` 包含 `mulSelect` 表示多选

值形态：

- `value` 通常是 JSON 字符串数组

适合场景：

- 会签公司范围
- 部门范围
- 多公司通知范围

参考源码：

- `{host_project}/src/components/Custom/components/LtdOrDepSelect/index.vue`

### `flow-list-mul-select`

用途：

- 多选流程对象，偏业务流程型

隐含逻辑：

- 差旅等场景会先检查某些字段是否已选，例如报销单位
- 选择完成后会触发变更并重新校验表单

适合场景：

- 关联多个差旅流程
- 关联多个还款或费用流程

参考源码：

- `{host_project}/src/components/Custom/components/FlowListMulSelect/index.vue`

### `general-flow-list-mulSelect`

用途：

- 多选流程对象，偏通用型

隐含逻辑：

- 通常先在 `refresh` 中写入：
  `this.setData({ flowObj: JSON.stringify({ flowType: 'xxx' }) })`
- 组件内部展示 `flowList`
- 每条已选流程都可查看详情

适合场景：

- 关联合同前序流程
- 关联多个固定流程类型单据

参考源码：

- `{host_project}/src/components/Custom/components/GeneralFlowListMulSelect/index.vue`

### `custome-file-import`

用途：

- 导入模板或上传 Excel 给业务接口解析

特点：

- 不是普通附件上传
- 组件内部走固定业务接口，不要当成通用附件组件

参考源码：

- `{host_project}/src/components/Custom/components/CustomeFileImport/index.vue`

## 4. 强业务组件

### `legal-contract-doctable`

用途：

- 合同合规评审中的法务手续文件表格

适用边界：

- 只在合同合规、法务手续类业务使用

已确认 `extendProps` 方向：

- `businessId`
- `companyId`
- `isFlowInitiate`
- `isExamine`
- `isReInitiate`
- `isTranspondFlow`

优先参考：

- `analysis/form-proxy-samples/raw/公司合同合规评审_contract_compliance_review.json`

### `contract-seal-review-business`

用途：

- 合同盖章评审业务块

适用边界：

- 只在合同盖章评审或高度相似业务里使用

已确认 `extendProps` 方向：

- `businessId`
- `isFlowInitiate`

优先参考：

- `analysis/form-proxy-samples/raw/公司合同盖章评审_contract_seal_review.json`

## 5. 低频或谨慎使用组件

- `custom-upload-excel`
  宿主已注册，但样本很少；需要明确“上传 Excel 并解析”时才用
- `out-bound-material-select`
  仅材料出库类场景考虑
- `in-bound-material-select`
  仅材料入库类场景考虑
- `person-mulSelect`
  当前样本中未出现，不要主动选
- `custome-file-view`
  当前样本中未出现，不要主动选
- `custome-expense-budgetType`
  当前样本中未出现，不要主动选

## 6. 自定义组件 JSON 写法

通用写法：

```json
{
  "type": "custom",
  "name": "项目选择",
  "model": "projectObj",
  "key": "projectObj",
  "el": "custome-select-project",
  "rules": [],
  "options": {
    "width": "100%",
    "hidden": false,
    "dataBind": true,
    "disabled": false,
    "placeholder": "请选择项目",
    "customClass": "",
    "labelWidth": 100,
    "isLabelWidth": false,
    "customProps": {},
    "extendProps": {}
  },
  "events": {
    "onChange": "",
    "onFocus": "",
    "onBlur": ""
  }
}
```

注意：

- `extendProps` 更适合放宿主业务参数，例如 `businessId`、`companyId`、`isFlowInitiate`
- 若组件源码依赖字段命名约定，`model` 不能随便换成无语义名字
- 自定义组件如果会触发表单联动，记得补 `events.onChange`
