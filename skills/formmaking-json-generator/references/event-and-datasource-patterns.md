# 事件脚本与数据源规律

这份总结基于“当前使用者本机可访问的 `raw` 样本 + FormMaking 源码”的共同结论。
它是本地增强学习材料，不是 skill 分发后的通用前置条件；如果换到没有样本的新环境，应把本文当作启发式参考，优先再结合宿主源码、FormMaking 源码和实际需求落地。

需要重新统计时，运行：

```bash
python3 skills/formmaking-json-generator/scripts/analyze_behavior_patterns.py --workspace .
```

## 1. 全局结论

- 178 份样本里，`eventScript` 是全覆盖，说明行为层不是“可选锦上添花”，而是正式表单的常规组成部分。
- 147 份样本带 `dataSource`，80 份用了 `remoteDataSource`，18 份用了动态值。
- 样本中的事件脚本以函数型为主，规则型脚本有但明显更少。
- 数据源里 `POST` 多于 `GET`，并且 `auto: true` 明显多于 `auto: false`。
- `requestFunc` 和 `responseFunc` 在真实样本里很常见，说明“配置一个 URL 就完事”并不符合现网复杂表单实际。

生成启发：

- 新生成表单如果出现“联动带出字段”“显隐禁用”“远程下拉”“对象回填”“明细合计”，应默认考虑 `eventScript + dataSource`，而不是只靠静态 `defaultValue`。
- `eventScript` 数组建议始终保留；真正无需联动时可以为空，但不要省略这层结构。

## 2. 高频动作组合

真实样本里最常见的动作不是复杂 API 编排，而是以下几组：

- `getValue/getValues + setData`
  最常见。通常用于金额汇总、大写金额回填、关联合同/流程后带出编号、主体、金额、项目等字段。
- `sendRequest + setData`
  用于根据当前字段去查远程数据，再回填其他字段或刷新选项。
- `hide/display/disabled`
  用于枚举切换显隐、切换只读、按条件展示区块。
- `triggerEvent`
  用于把当前事件拆成多个步骤，做二次联动。
- `refresh / refreshDynamicValue / refreshFieldOptionData`
  用于级联刷新、重新拉取远程选项、重算动态值。

生成启发：

- 单字段计算优先 `getValue + setData`。
- 关联系统对象带出一组字段，优先 `getValues + setData`，必要时先解析 JSON 字符串值。
- 联动链较长时，先回填当前字段，再 `triggerEvent` 给下一步，不要在一个脚本里塞满所有逻辑。

## 3. 字段事件绑定习惯

真实样本里最常见的绑定点大致是：

- `number.onChange`
  计算汇总、金额大写、税额回填最常见。
- `input.onFocus`
  常被用来打开选择弹窗，而不是做普通输入框焦点提示。
- `select.onChange` / `radio.onChange` / `cascader.onChange`
  常用于显隐、禁用、清空下游字段、刷新下游选项。
- `custom.onChange`
  常用于合同、流程、人员、公司等宿主组件回填。
- `button.onClick`
  常用于手动触发查询、补齐、导入、打开弹窗。
- `table.onRowAdd` / `table.onRowRemove` / `table.onChange`
  常用于明细汇总、序号重排、联动删改。

生成启发：

- 金额类字段默认优先考虑挂 `onChange`。
- 选择型宿主组件默认优先考虑挂 `onChange`，而“点击打开选择器”这类场景再考虑 `onFocus` 或按钮。
- 表格型明细只要有合计、数量、金额联动，就要考虑 `table.onChange` 或行增删事件。

## 4. 数据源写法规律

真实样本里的数据源有几个共性：

- `POST` 是主流，不要默认全用 `GET`
- `auto: true` 很常见，尤其是公司、部门、基础枚举、项目树这类表单初始化就需要的数据
- `responseFunc` 非常常见，说明接口原始结构和表单字段期望结构经常不一致
- `requestFunc` 也不少，用于补 host、token、companyId、sid、包装请求体

生成启发：

- 远程选项字段如果接口返回不是标准 `[{label,value}]`，优先把转换逻辑写进 `responseFunc`，不要把复杂清洗塞进字段事件里。
- 如果请求依赖 token、companyId、环境 host，优先在 `requestFunc` 处理，而不是每个事件脚本都手写一遍。
- `remoteDataSource` 只是字段到数据源的引用，不负责参数推导；参数变化时仍要结合 `remoteArgs`、事件脚本或刷新动作。

## 5. 远程选项与动态值

样本里 `remoteDataSource` 主要集中在选择型字段，尤其是：

- `select`
- 少量 `radio` / `cascader`

动态值方面：

- `dynamicValueType: "fx"` 比 `datasource` 更常见
- 说明很多动态值只是公式/表达式，不一定需要远程请求

生成启发：

- 只是“由已有字段拼出默认值/描述/计算值”时，优先 `dynamicValueType: "fx"`。
- 只有当值本身依赖远端结果、并且适合初始化或刷新拉取时，才用 `dynamicValueType: "datasource"`。
- “下拉选项远程拉取”和“字段默认值远程拉取”是两套机制，不要混用：
  前者走 `remoteDataSource`，后者走 `dynamicValue*`。

## 6. 规则型脚本与函数型脚本

规则型脚本适合：

- 简单显隐
- 简单禁用
- 简单清空/赋值
- 设计器拼装出来的一步或几步标准动作

函数型脚本适合：

- 解析 JSON 字符串对象
- 处理金额汇总/大写转换
- 多阶段回填
- 远程请求后再带出多字段
- 需要调用宿主或窗口对象能力

生成启发：

- 如果需求只是“满足 A 时显示/隐藏 B”，优先规则型。
- 一旦涉及 JSON 解析、数组遍历、金额计算、复杂对象回填或多步骤串联，直接用函数型更稳。

## 7. 生成时的经验法则

- 不要为了“有联动”就给每个字段都挂事件，优先在真正的数据入口字段上挂。
- 一个字段脚本里如果已经做了 `setData`，通常要想清楚是否还需要 `triggerEvent` 触发下游；缺了会断链，多了会重复覆盖。
- 宿主自定义组件很多值是 JSON 字符串；行为脚本里经常要兼容外层对象和内层 `rowData`。
- 对于表格合计、金额大写这类可复用行为，优先参考真实样本里 `number.onChange` / `table.onChange` 的习惯，不要下意识挂在 `onBlur`。
