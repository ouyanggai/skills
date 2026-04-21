# 样式与审批区规律

下面规律来自“当前使用者本机可访问的 `analysis/form-proxy-samples/raw` 样本”统计。
它属于本地增强学习结果，不代表其他环境也有同一批样本；换一批样本后，或者新环境没有样本时，应把本文当作启发式参考，而不是硬编码约束。

## 1. 表单壳层

### 常见宽度

- `900px`：62 / 178
- `1024px`：24 / 178
- `1100px`：19 / 178
- `850px`：19 / 178
- `1000px`：16 / 178
- `800px`：13 / 178
- `100%`：13 / 178

结论：

- 正式审批表、打印式表格、合同/人事/OA 审批单，优先 `850px` 或 `900px`。
- `1024px`、`1100px`、`1000px` 更常见于内容偏多、阅读型或混合布局表单。
- 不要默认 `100%`。在宿主 `newFormMaking` 体系下，固定宽度更容易得到居中、完整边框和稳定的打印感。

### 常见 `config.customClass`

- `bord newFormMaking`：83 / 178
- 空字符串：40 / 178
- `bord`：29 / 178
- `newFormMaking`：19 / 178

结论：

- 正式表格式表单默认优先 `bord newFormMaking`。
- 只有在不需要整张表格外边框，或样本明确更轻的时候，再考虑 `newFormMaking` 或空 class。

### `labelPosition` / `labelCol`

- `labelPosition: "right"`：129 / 178
- `labelPosition: "left"`：48 / 178
- `labelCol: 3`：121 / 178

结论：

- 通用默认值仍然是 `right + labelCol: 3`。
- 人员、招聘、内部选拔、员工流动这类贴近既有人资表单的场景，`left` 也很常见，尤其是结合 `report` 时。

## 2. 文字 class 规律

高频 `text.options.customClass`：

- `txtCenter`：628
- `approvalOpinion`：436
- `showRedPot`：149
- `txtLeft`：130
- `require`：108
- `txtRight`：107
- `title`：86
- `sub-title`：83
- `bold`：59

结论：

- 单元格文字对齐优先直接复用 `txtCenter` / `txtLeft` / `txtRight`，不要每次都靠 `styleSheets` 重写。
- 审批区标签和说明文字经常使用 `approvalOpinion`。
- 必填标签常见两套思路：
  `showRedPot` 用于宿主已有红星表现；
  `require` 常配合 `styleSheets` 手工补星号。
- 顶部大标题优先 `title`，分区标题优先 `sub-title`。

## 3. `styleSheets` 的实际用途

`styleSheets` 不是拿来“重写整站主题”的，而是拿来补正式表单的几个视觉细节。

高频 class：

- `sub-title`：104
- `remark-font`：98
- `subform`：63
- `center-zxf`：30
- `border-bottom`：28
- `radio-flex`：28
- `print-read-label`：6

高频片段：

```css
.sub-title .el-form-item__label{
  text-align: center !important;
  font-size: 22px !important;
  line-height: 43px;
}
```

```css
.remark-font .el-form-item__label{
  font-size:16px !important;
}
```

结论：

- `styleSheets` 最常见的作用是放大分区标题、微调说明字体、让横向单选/复选更像纸面表格。
- 如果结构本身错了，例如 `subform` 套 `report`、列数不对、边框层级错，CSS 无法真正救回来。
- 只有在出现以下需求时再补 `styleSheets`：
  分区标题字号、注释字号、横向选项排列、打印只读标签、局部边框。

## 4. 审批意见区模式

在 178 份样本里，能识别为审批意见区的 `report` 约 46 个，常见形态包括：

- `rows=1 | cols=(1,)`
  只有一个“审批意见”占位标题，后续多由流程审批层承接。
- `rows=5 | cols=(2, 2, 2, 2, 2)`
  人资/招聘/内部选拔最常见，一行一位审批角色，左列标签右列意见区。
- `rows=2 | cols=(5, 5)`
  适合并排双意见块。
- `rows=1 | cols=(6,)`
  单条宽意见栏。
- `rows=1 | cols=(5,)`
  员工流动等场景常见，一条意见标签 + 多个签批角色并排。

代表性样本：

- `人员招聘审批表_person_recruit_approval.json`
  `5 x 2` 审批意见区，适合人资/招聘/选拔类参考。
- `员工流动审批表_employee_turnover_approval_form.json`
  多个顶层 `report`，每块一个审批节点，适合学习长审批链的静态骨架。
- `干部选拔报名表_enterprise.json`
  以报名信息和长文本说明为主，审批区较轻，适合学习“标题 + 主表 + 长文本表”的组合。

结论：

- 如果用户给的是纸面审批单、Word 制式单，审批意见区优先保留表格骨架。
- 没有明确录入要求时，不要把每一行都生成发起人可编辑字段。
- 需要流程节点展示时，应优先考虑流程层承接，而不是让表单 JSON 假装所有审批意见都由发起人填写。

## 5. 生成策略

- 正式表格优先顺序：
  `config.width`
  `config.customClass`
  `report` 行列结构
  `text.options.customClass`
  `styleSheets`
- 先选壳层再选配色，不要反过来。
- 用户说“现网那个更像表单”时，优先比对：
  `config.width`
  `config.customClass`
  标题/分区 `customClass`
  审批区 `report` 的行列数
  是否使用了 `styleSheets`
