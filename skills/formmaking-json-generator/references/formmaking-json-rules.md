# FormMaking JSON 规则

## 1. 产物边界

- 表单 JSON 通常来自流程中心数据库的表单模板字段，例如 `template_data`；具体库表以使用者环境为准。
- 目标是产出宿主平台可直接消费的 FormMaking JSON，不是页面路由、不是真实后端表结构、也不是 NoFormFlow。
- 宿主工程运行时可能加载本地表单库打包产物，规则以当前工作区中实际运行的 FormMaking 源码、宿主注册组件和本地样本为准。

## 2. 顶层结构

源码默认骨架来自 `Container.vue`：

```json
{
  "list": [],
  "config": {
    "labelWidth": 100,
    "labelPosition": "right",
    "size": "default",
    "customClass": "",
    "ui": "element",
    "layout": "horizontal",
    "width": "100%",
    "hideLabel": false,
    "hideErrorMessage": false
  }
}
```

结合宿主真实样本，建议生成时统一补成：

```json
{
  "list": [],
  "config": {
    "labelWidth": 100,
    "labelPosition": "left",
    "size": "small",
    "customClass": "",
    "ui": "element",
    "layout": "horizontal",
    "width": "100%",
    "hideLabel": false,
    "hideErrorMessage": false,
    "eventScript": [],
    "dataSource": []
  }
}
```

说明：

- `eventScript` 建议始终保留数组，便于后续追加联动。
- `dataSource`、`styleSheets` 可按需补充。
- 一旦需求涉及字段联动、远程下拉、动态值、显隐禁用或对象回填，先同时参考 [event-and-datasource-patterns.md](event-and-datasource-patterns.md)，不要把行为层逻辑偷换成静态 `defaultValue`。
- `platform` 在个别样本中出现，例如 `pad`，只有需求明确时再加。
- 上面这套骨架更适合通用表单，不是所有正式审批表都用 `config.width = "100%"`。
- 对合同、法务、制式审批单这类“表格主骨架”表单，真实样本更常见的是：

```json
{
  "config": {
    "labelWidth": 100,
    "labelPosition": "right",
    "size": "small",
    "customClass": "bord newFormMaking",
    "ui": "element",
    "layout": "horizontal",
    "labelCol": 3,
    "width": "850px",
    "hideLabel": false,
    "hideErrorMessage": false
  }
}
```

说明：

- 宿主运行时 `.fm-form` 本身带 `margin: 0 auto`，所以固定宽度更容易得到“整体居中、轮廓完整”的正式审批表效果。
- 如果这类表单错误地使用 `config.width = "100%"`，常见结果是表单过宽、视觉重心发散，或和截图样式不一致。
- 如果用户给的是蓝湖或截图，图上的红字默认先按“批注/提示”理解，不要直接把正式表单标签或回填值渲染成红色。
- 宿主现网页面里很多正式表单样式依赖 `config.customClass` 带 `newFormMaking`。
  如果字段上用了 `showRedPot`、`tableNoPadding`、`approvalOpinion`、`autoAuditInfoField` 这类宿主 class，而外层壳层没有 `newFormMaking`，最终效果通常会偏离现网。

## 3. 高频组件类型

参考样本中的高频类型如下。迁移到新环境后，应优先以本地 `.formmaking-json-generator/context.json` 指向的样本目录重新统计；如果没有样本，则把下面数据作为启发式参考，不要当成硬约束。

- `text`（5994）
- `report`（1199）
- `textarea`（1163）
- `input`（1087）
- `number`（551）
- `select`（345）
- `grid`（280）
- `fileupload`（278）
- `date`（265）
- `custom`（252）
- `component`（99）
- `table`（94）
- `radio`（89）
- `inline`（76）
- `checkbox`（71）
- `subform`（10）

生成时优先参考高频类型，不要先发明冷门结构。

## 4. 字段与容器的基础协议

绝大多数字段/容器都至少包含以下键：

- `type`
- `name`
- `model`
- `key`
- `options`
- `rules`

常见可选键：

- `icon`
- `events`
- `el`
- `tableColumns`
- `list`
- `columns`
- `rows`
- `tabs`
- `novalid`

建议：

- `model` 用业务语义英文名，例如 `expenseCompanyId`、`contractObj`、`travelPersonnelVoList`。
- `key` 保持唯一；容器 key 可以随机短串，业务字段 `model` 不建议随机命名。
- 普通字段的 `rules` 常为空数组；很多校验实际上写在 `options.required`、`patternCheck`、`validatorCheck` 里。

## 5. 容器递归规则

### `report`

适合打印式表格、合并单元格布局。

结构：

```json
{
  "type": "report",
  "options": {
    "width": "100%"
  },
  "rows": [
    {
      "columns": [
        {
          "type": "td",
          "options": {},
          "list": []
        }
      ]
    }
  ]
}
```

经验：

- 正式审批表里的 `report` 通常都显式带 `options.width = "100%"`。
- 漏掉宽度常见后果是表格整体左缩、只按内容宽度渲染、外轮廓不完整。
- 如果是整张表单的主骨架，`report` 通常直接放在顶层，不需要再包一层只有单列的 `grid`。

### `grid`

适合普通栅格布局。

结构：

```json
{
  "type": "grid",
  "columns": [
    {
      "span": 12,
      "list": []
    }
  ]
}
```

### `table`

适合明细行、多行重复字段。

结构：

```json
{
  "type": "table",
  "model": "expenseDetailList",
  "tableColumns": []
}
```

源码默认项（`componentsConfig.js`）：

- `showControl: true`
- `isAdd: true`
- `isDelete: true`
- `paging: false`
- `nestedHeader: false`
- `nestedHeaderName: ""`
- `noShowTable: false`

运行时启发（`FormTable/index.vue`）：

- `showControl` 会额外渲染控制列、删除按钮和标识位，不适合截图仿制型制式表单
- `nestedHeader: true` 时应同步提供 `nestedHeaderName`
- `noShowTable: true` 只适合“有值才展示”的显示型表格；录入型/必填型表格默认不要开

### `subform`

适合重复块，不只是“表格行”。

结构：

```json
{
  "type": "subform",
  "model": "mainBodySubform",
  "list": []
}
```

源码默认项（`componentsConfig.js`）：

- `showControl: true`
- `isAdd: true`
- `isDelete: true`
- `paging: false`

运行时启发（`SubForm/index.vue`）：

- `showControl` 会渲染蓝色编号 tag、删除按钮和新增入口
- 所以固定的 Word 分区、固定“一、二、三”业务段，不要因为内容长得像重复块就套 `subform`

### 其他递归容器

- `inline` / `dialog` / `card` / `group`：子节点走 `list`
- `tabs` / `collapse`：子节点走 `tabs[].list`

### 布局选择原则

- 非演示级极简表单，不要把字段直接平铺在顶层 `list`；先选布局容器。
- 需要打印式、制式表格、合并单元格、截图仿制：优先 `report`
- 需要普通两列/三列响应式分区：优先 `grid`
- 需要同行排布 2 到 4 个轻量控件：优先 `inline`
- 需要多行重复明细：优先 `table`
- 需要重复业务块且每块内部字段结构较复杂：优先 `subform`
- 复杂审批表推荐“`grid` 分区 + `report` 制表区”的混合结构，既清楚又便于后续调整
- 但“`grid` 分区 + `report` 制表区”不是机械套模板：
  如果一个区块只有一个全宽 `report`，通常直接把 `report` 放顶层即可，不必为了“有布局容器”再包一层单列 `grid`
- 正式表格型表单的标题，优先直接用顶层 `text`，沿用真实样本的 `title` / `sub-title` 做法

更细的布局经验见 [layout-and-common-patterns.md](layout-and-common-patterns.md)。

### 常见失败布局反模式

- `report` 不写 `options.width`
  常导致表格不占满可用宽度，视觉上偏左、边框残缺
- 顶层 `grid(span=24)` 只包一个 `report`
  这类容器往往没有真实布局价值，只会增加一层包裹和样式不确定性
- 顶层标题用单列 `grid` 包一个 `text`
  真实样本里更常见的是直接顶层 `text`
- `report` 单元格里再套带边框的 `report/table`
  除非明确需要嵌套表格，否则容易出现双重轮廓、输入框周围视觉层级过重
- 为了“像表格”而把所有区块都做成多层容器
  最终常见结果是轮廓太多、重点不清、字段显得挤
- 把截图批注中的红字提示当成真实表单样式
  常见结果是“项目名称/合同主体/合同分类”等回填字段被错误渲染成红字
- 必填项把 `*` 直接写进标签文案
  容易和宿主统一样式脱节，也容易出现“星号显示了但校验没配齐”的问题
- 回填字段只设 `readonly`
  交互上虽然不能改，但视觉上不置灰，和宿主现有正式表单不一致

## 6. `options` 常用键

高频公共键：

- `width`
- `hidden`
- `dataBind`
- `disabled`
- `required`
- `requiredMessage`
- `customClass`
- `placeholder`
- `defaultValue`
- `labelWidth`
- `isLabelWidth`
- `readonly`
- `tableColumn`

常见校验相关键：

- `required`
- `requiredMessage`
- `pattern`
- `patternCheck`
- `patternMessage`
- `dataType`
- `dataTypeCheck`
- `dataTypeMessage`
- `validator`
- `validatorCheck`

注意：

- 样本里很多字段把“必填”“数据类型”“正则”“自定义校验”都写在 `options` 中，而不是 `rules` 中。
- `hidden`、`disabled`、`remoteArgs`、`headers`、`params` 等都可能是表达式。
- 在 `report` 单元格里的普通字段，保留控件自身边框即可；不要再额外包一层没有必要的边框容器。
- 系统回填值、原合同/原流程带出值、自动计算结果，优先用 `disabled: true`，让宿主按灰底灰字渲染。
- 不要为了强调这些回填字段而额外写红色高亮样式；正式表单正文、标签、回填值默认都应保持宿主常规配色。
- 正式表格型表单的必填标签，优先用宿主现成的 `showRedPot` 样式思路显示红色星号，不建议把 `*` 手写进标签文本。
- 如果使用 `showRedPot`、`approvalOpinion`、`tableNoPadding`、`autoAuditInfoField` 等宿主样式类，外层 `config.customClass` 也要带 `newFormMaking`，否则类名可能挂上了但页面效果不对。
- 运行时实际使用节点的 `rules` 生成 Element 表单校验；新生成字段时，`options.required = true` 必须同步配 `rules: [{"required": true, "message": "中文提示"}]` 或 `rules[].func` 自定义校验。
- 所有校验提示必须是中文，包括 `requiredMessage`、`rules[].message`、自定义校验里的 `callback("...")`。

通用回填与可编辑字段规则：

- 从已有流程、合同、项目、台账或主数据带出的“事实字段”，通常应置灰不可编辑，例如名称、编号、分类、主体、原金额、历史金额、自动计算结果。
- 本次流程需要用户确认或变更的字段，即使默认来自源数据，也应保持可编辑。例如“当前方式”“变更后金额”“本次负责人”等。
- 不要把同一业务含义的源字段和目标字段都可见地摆在同一区域里，除非需求明确要做“变更前/变更后”对照。
- 从源对象回填到可编辑字段时，只在源对象变化时覆盖默认值；同一源对象下，用户手动修改后不要被刷新、校验或联动事件再次覆盖。
- 源对象返回值经常有外层选择对象和内层 `rowData` 两层。生成事件脚本时要同时兼容两层字段，并对编码值/中文值做归一化。

示例：

```json
{
  "type": "input",
  "model": "contractName",
  "options": {
    "required": true,
    "requiredMessage": "请输入合同名称"
  },
  "rules": [
    {
      "required": true,
      "message": "请输入合同名称"
    }
  ]
}
```

## 7. 表达式语法

表达式格式来自 `util/expression.js`：

```js
{{ ... }}
```

运行时会提取花括号内部代码并执行。

适用位置：

- `options.hidden`
- `options.disabled`
- `options.remoteArgs`
- `dataSource.headers`
- `dataSource.params`
- `dynamicValueArgs`
- `extendProps` / `customProps` 中的动态值

生成时避免：

- 把纯文本误包成表达式
- 写出不能执行的 JS
- 在不支持表达式的位置滥用 `{{ ... }}`

## 8. 事件脚本

`config.eventScript` 是表单动作中枢。运行时加载逻辑在 `GenerateForm.vue`。

### 结构 1：直接函数

```json
{
  "key": "onChange_companyId",
  "name": "onChange_companyId",
  "func": "const { value } = arguments[0]\nif (value) { this.setData({ depId: '' }) }"
}
```

### 结构 2：规则型脚本

```json
{
  "key": "rule_xxx",
  "name": "rule_xxx",
  "type": "rule",
  "rules": []
}
```

规则型脚本最终会转成函数执行。

### 字段事件绑定

字段上的 `events` 存的是事件脚本 `key`：

```json
{
  "events": {
    "onChange": "onChange_companyId",
    "onFocus": "",
    "onBlur": ""
  }
}
```

### 可用动作

来自 `EventPanel/actions.js` 和 `rule-funcs.js`：

- `hide`
- `display`
- `disabled`
- `refresh`
- `reset`
- `setData`
- `validate`
- `sendRequest`
- `refreshDynamicValue`
- `refreshDynamicValueAll`
- `refreshFieldOptionData`
- `getOptionData`
- `openDialog`
- `closeDialog`
- `triggerEvent`
- `js`

### 运行时可直接调用的方法

来自 `GenerateForm.vue`：

- `validate`
- `getData`
- `getValues`
- `getValue`
- `setData`
- `setRules`
- `setOptions`
- `getOptions`
- `hide`
- `display`
- `disabled`
- `refresh`
- `refreshFieldOptionData`
- `refreshFieldDataSource`
- `getFieldDataSource`
- `sendRequest`
- `triggerEvent`

## 9. 数据源协议

`config.dataSource` 中每一项通常包含：

```json
{
  "key": "expenseCompanyDataSource",
  "name": "getExpenseCompanyList",
  "url": "/api/xxx",
  "method": "GET",
  "auto": false,
  "params": {},
  "headers": {},
  "responseFunc": "return res.data;",
  "requestFunc": "return config;",
  "args": []
}
```

说明：

- 运行时 `sendRequest` 既支持按 `name` 查，也支持按 `key` 查。
- `auto: true` 时表单初始化就会请求。
- 字段远程选项常通过 `options.remoteDataSource` 关联数据源。
- `params` / `headers` 可以用表达式。

## 10. 动态值与动态选项

字段支持两类动态值：

- `dynamicValueType: "datasource"`
- `dynamicValueType: "fx"`

常见键：

- `isDynamicValue`
- `dynamicValueType`
- `dynamicValueDataSource`
- `dynamicValueArgs`
- `dynamicValueStruct`
- `dynamicValueFx`

远程选项联动常用键：

- `remote: true`
- `remoteType: "datasource"`
- `remoteDataSource`
- `remoteArgs`
- `props`

## 11. 自定义组件协议

运行态渲染规则来自 `GenerateElementItem.vue`：

```json
{
  "type": "custom",
  "name": "项目选择",
  "model": "projectObj",
  "key": "projectObj",
  "el": "custome-select-project",
  "options": {
    "width": "100%",
    "customProps": {},
    "extendProps": {}
  },
  "events": {}
}
```

注意：

- `el` 必须是宿主 `Vue.use(FormMaking, { components: [...] })` 已注册的名字。
- 组件最终会收到通用 props：
  `value`、`width`、`height`、`placeholder`、`readonly`、`disabled`、`editable`、`clearable`、`print-read`
- `options.customProps` 和 `extendProps` 会一起透传给组件。
- `events` 会被包装成运行时回调，并调用对应 `eventScript`。
- 宿主高频自定义组件里，很多 `value/defaultValue` 实际上是 JSON 字符串，不是对象：
  `custome-info-select`、`general-list-select-show`、`general-flow-list-mulSelect`、`person-mulSelect`、`ltd-or-dep-select` 都是高频例子。
- 某些宿主组件对 `model` 名称有硬约束：
  `custome-info-select` 需要 `model` 包含 `userName` / `depName` / `companyName` / `dutyName`；
  `ltd-or-dep-select` 需要 `model` 包含 `singleSelect` / `mulSelect`。
- `legal-contract-doctable` 这类强业务组件还依赖 `extendProps`，并且默认建议带 `tableNoPadding`；
  业务上下文不完整时宁可退回普通字段，也不要硬猜。

## 12. 表格、子表单、上传的选择建议

- 明细行、金额分摊、税额拆分：优先 `table`
- 重复块、重复业务片段：优先 `subform`
- 打印式制式单据、复杂合并表头：优先 `report`
- 多数正式审批表建议至少有一个明确布局骨架：`grid` 或 `report`
- 附件上传若要求“允许多个”，必须同时设置 `options.multiple = true` 和足够的 `options.limit`
- 标准 `fileupload` 的默认值来自源码：`multiple: false`、`limit: 100`
- 当前运行时 `fm-file-upload` 只接收 `multiple`、`limit`、`action`、`headers` 等固定参数，不接收文件扩展名限制参数
- 运行时上传控件的 `<input type="file">` 没有 `accept` 属性，因此不能把“仅 PDF/仅 Excel”这种限制完全寄托在标准 `fileupload` 上
- 合同/法务类业务附件：优先先找真实样本，不要从零发明

## 13. 生成时的硬规则

- 不要引用不存在的 `eventScript.key`
- 不要引用不存在的 `dataSource.key` / `dataSource.name`
- `custom` 组件必须带 `el`
- `remoteType: "datasource"` 时必须补 `remoteDataSource`
- `isDynamicValue: true` 时必须补对应 `dynamicValue*` 配置
- 业务组件需要的 `extendProps` 不明确时，优先回退到普通字段，不要硬猜
- 多附件上传必须显式写 `multiple` 和 `limit`，不要只写提示语
- 正式表单必须有明确布局容器，不要把复杂字段区直接散放在顶层 `list`

补充：

- 历史样本里存在少量“设计器残留”配置，例如空 `key`、缺失 `rules` 的 `type: "rule"` 事件、空的 `remoteDataSource`。
- 这些现网遗留问题不应继续复制到新 JSON 中。
- 校验新生成 JSON 时用严格模式；回看历史样本时可用 `--relaxed`。

## 14. 最小可用骨架

```json
{
  "list": [
    {
      "type": "input",
      "name": "申请标题",
      "model": "title",
      "key": "title",
      "rules": [],
      "options": {
        "width": "100%",
        "hidden": false,
        "dataBind": true,
        "disabled": false,
        "required": true,
        "requiredMessage": "请输入申请标题",
        "placeholder": "请输入申请标题",
        "defaultValue": "",
        "customClass": "",
        "labelWidth": 100,
        "isLabelWidth": false
      },
      "events": {
        "onChange": "",
        "onFocus": "",
        "onBlur": ""
      }
    }
  ],
  "config": {
    "labelWidth": 100,
    "labelPosition": "left",
    "size": "small",
    "customClass": "",
    "ui": "element",
    "layout": "horizontal",
    "width": "100%",
    "hideLabel": false,
    "hideErrorMessage": false,
    "eventScript": [],
    "dataSource": []
  }
}
```
