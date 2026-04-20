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

从 178 份 raw 样本继续抽出来的补充结论：

- `custome-info-select`、`general-list-select-show`、`custome-select-project` 这类高频组件，大多不依赖 `customProps` / `extendProps`；先把 `model`、默认值、事件脚本和外层布局配对好更重要。
- 强业务组件里，`legal-contract-doctable` 是少数稳定依赖 `extendProps` 的组件；没有现成业务上下文时不要主动选它。
- 很多高频组件的 `name` 在样本里都很泛，例如“通用信息选择”“通用列表选择”，因此正式表单里的业务语义通常来自外层 `report` 标签或分区标题，而不是组件自身名称。

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

raw 样本补充：

- 145 个节点分布在 63 份样本里，是最稳的通用宿主组件。
- 高频 `model`：
  `handlingDepName`、`handlingUserName`、`handledUserName`、`myCompanyName`、`myUserName`、`contractUserName`、`contractDepName`、`contractCompanyName`
- 高频 `name` 反而很泛：
  “通用信息选择”最多，因此生成时不要照抄组件名当业务标签。
- 常见会挂 `onFocus` / `onChange` 事件脚本；如果联动需求不明确，可以先不挂事件，只保留合法值结构。

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

raw 样本补充：

- 31 个节点分布在 20 份样本里。
- 高频 `model`：
  `contractObj` 最常见，其次是若干业务流程对象字段。
- 组件 `name` 基本都写成“通用列表选择”，说明业务标签通常由外层单元格提供。
- 常见 `onChange` 事件会在选择对象后带出项目、金额、主体等信息；如果需求里出现“关联合同/流程后回填一组字段”，优先考虑它。

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

raw 样本补充：

- 16 个节点，几乎都是 `project` / `projectName` / `selectProject` 这类直白 `model`。
- 如果需求只是“项目名称”而且宿主存在真实项目对象，优先用它，不要退回纯输入框。

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

raw 样本补充：

- 5 个节点里，`singleSelectCompany` 是最常见 `model`。
- 该组件更偏“范围选择”，不是普通单人单岗选择，不要和 `custome-info-select` 混用。

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

raw 样本补充：

- 6 个样本里 `model` 都是 `custom_flow_btn`，说明它更像一个业务按钮入口，不像普通字段。
- 如果用户只是要普通“关联多个流程”，不一定首选它；先判断是不是费用/差旅/还款这类既有业务链条。

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

raw 样本补充：

- 4 个样本里 `model` 都是 `importTemplate`，说明它更像“导入入口”而不是普通上传字段。
- 如果需求只是上传附件，不要误用它，继续用标准 `fileupload`。

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

raw 样本补充：

- 3 个样本全部带 `extendProps`，这是一个明显信号：
  没有现成业务上下文时不要猜它的参数。

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

raw 样本补充：

- 3 个样本里 `model` 固定为 `custom_contractSealField`，并且几乎不靠组件 `name` 表达业务语义。
- 这是典型强业务块，不要当通用组件推广。

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
