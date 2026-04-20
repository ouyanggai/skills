# 样本索引

## 1. 样本位置

- 样本目录以本地上下文为准，先运行 `scripts/discover_context.py` 或读取当前工作区的 `.formmaking-json-generator/context.json`。
- 如果上下文里没有样本目录，向使用者询问“真实表单 JSON 样本目录”或“是否允许从数据库只读导出样本”。
- 曾分析过的样本口径为 `is_delete = 0` 且按 `type_id` 导出；迁移到新环境后不要默认样本数量仍然一致。
- 常见相对路径：
  `analysis/form-proxy-samples/raw/`
- 常见配套文件：
  `analysis/form-proxy-samples/manifest.json`
  `analysis/form-proxy-samples/stats.json`
  `analysis/form-proxy-samples/feature-index.json`

命名规则：

- 推荐文件名格式为 `中文类型名_英文类型名.json`
- 如果存在同名但不同 `type_id` 的流程类型，会追加 `_<type_id>`，避免样本互相覆盖

## 2. 先看哪一类

- 需求比较普通、字段不多：先看“基础表单”
- 需求里有联动、自动计算、远程下拉：先看“事件/数据源密集型”
- 需求里有合同、法务、流程对象选择：先看“自定义组件密集型”
- 需求里有重复明细：先看“表格/子表单型”
- 需求里有打印式制表布局：先看 `report` 重的样本

## 3. 代表性样本

### 布局优先样本

- `analysis/form-proxy-samples/raw/质量报验类型_quality_inspection.json`
  适合参考 `report + table` 的制式表格布局。
- `analysis/form-proxy-samples/raw/OA_general_flow.json`
  适合参考 `report + grid + table` 的复杂混合布局。
- `analysis/form-proxy-samples/raw/运行管理_general_flow.json`
  适合参考 `grid` 很重的普通区块式排版。
- `analysis/form-proxy-samples/raw/公司合同盖章评审_contract_seal_review_b0a2e32f7c464487aa3f4f72f48ab5a4.json`
  适合参考合同类复杂表单的布局与组件混排。

### 基础表单

- `analysis/form-proxy-samples/raw/公司请款单_request_funds.json`
  适合参考普通主表字段和一段明细表。
- `analysis/form-proxy-samples/raw/请假单_ask_for_leave.json`
  适合参考轻量审批单。

### 事件/数据源密集型

- `analysis/form-proxy-samples/raw/公司差旅报销单_travel_expense.json`
  最适合学习复杂联动、远程数据源、多个明细表、附件和流程选择。
- `analysis/form-proxy-samples/raw/费用报销单-无归口_expense_budget_noBelong.json`
  适合学习费用类表单里的事件脚本组织方式。

### 样式/审批区优先

- `analysis/form-proxy-samples/raw/人员招聘审批表_person_recruit_approval.json`
  适合学习 `900px + bord newFormMaking + 5x2 审批意见区 + 分区标题样式`。
- `analysis/form-proxy-samples/raw/员工流动审批表_employee_turnover_approval_form.json`
  适合学习多个顶层 `report` 串联的长审批链、固定壳层宽度和审批角色排布。
- `analysis/form-proxy-samples/raw/干部选拔报名表_enterprise.json`
  适合学习 `900px + newFormMaking` 的较轻壳层、长文本区和标题/副标题控制。
- `analysis/form-proxy-samples/raw/内部选拔实施申请表_enterprise.json`
  适合学习 Word 制式单转 JSON 后最容易踩的坑：固定重复区、审批意见区、选择控件和 styleSheets 微调。

### 自定义组件密集型

- `analysis/form-proxy-samples/raw/公司合同盖章评审_contract_seal_review.json`
  适合学习 `custome-select-project`、`custome-info-select`、`general-list-select-show`、`contract-seal-review-business` 的组合用法。
- `analysis/form-proxy-samples/raw/公司合同合规评审_contract_compliance_review.json`
  适合学习 `legal-contract-doctable` 以及合同合规类字段组织。

### 表格/子表单型

- `analysis/form-proxy-samples/raw/质量报验类型_quality_inspection.json`
  `report` 和 `table` 很重，适合看制式表格布局。
- `analysis/form-proxy-samples/raw/人员增补审批表_personnel_addition_approval_form.json`
  适合学习 `subform` 与组织选择组件组合。
- `analysis/form-proxy-samples/raw/固定资产购置申请表_assets_buy_apply.json`
  适合学习单个顶层大 `report` 里再承载局部明细和复杂事件脚本。

### 文件导入/业务附件型

- `analysis/form-proxy-samples/raw/公司合同开票单类型_contract_invoicing.json`
  适合学习 `custome-file-import`、合同对象选择和开票明细表。

## 4. 从样本反推策略

- 要做费用、差旅、请款类表单：优先比对 `travel_expense`、`request_funds`、`expense_budget_noBelong`
- 要做合同类表单：优先比对 `contract_seal_review`、`contract_compliance_review`、`contract_invoicing`
- 要做组织/人员变动类表单：优先比对 `personnel_addition_approval_form`
- 要做人资/招聘/选拔/员工流动类表单：优先比对 `person_recruit_approval`、`employee_turnover_approval_form`、`enterprise`
- 要做打印式工程或质检单据：优先比对 `quality_inspection`

## 5. 特征索引可直接利用

`feature-index.json` 已按以下维度分组：

- `event_heavy`
- `datasource_heavy`
- `custom_heavy`
- `table_heavy`
- `subform_cases`
- `fileupload_cases`

如果要重新从当前 raw 样本学习“壳层宽度 / class / styleSheets / 审批区”规律，直接运行：

```bash
python3 skills/formmaking-json-generator/scripts/analyze_sample_patterns.py --workspace .
```

生成 JSON 时，如果需求里出现明显特征，优先选同类样本做“近似迁移”，不要从零搭。
