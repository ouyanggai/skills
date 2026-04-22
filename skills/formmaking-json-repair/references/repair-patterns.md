# FormMaking JSON 修复模式

## 1. 必填失效

检查顺序：

1. 字段本身是否有 `options.required`
2. 是否同步写了 `rules`
3. `rules[].message` / `requiredMessage` 是否为中文
4. 事件脚本是否把值改空了却没触发重验
5. `beforeSubmitAndDraft` 是否需要业务兜底

结论：

- 红色星号不等于运行时真的会拦截提交。
- 现网遗留 JSON 里，经常出现“界面必填、运行时不拦”的问题，本质通常是 `rules` 缺失或联动陈旧值没有清掉。

## 2. 表格联动后的陈旧值

典型症状：

- 明细表里切换上游字段后，下游下拉/级联看起来空了
- 提交却没拦截“类型必填”
- 或者提交带了上一条旧值

最小修复模式：

1. 上游字段 `onChange`
2. 清空当前行下游值
3. 刷新当前行下游选项
4. 必要时 `validate()`
5. `beforeSubmitAndDraft` 补兜底

示意：

```js
const expenseBudgetList = this.getComponent('expenseBudgetList')
expenseBudgetList.setData(rowIndex, { departmentId: [] })
this.setOptionData([`${group}.${rowIndex}.departmentId`], options)
this.$nextTick(() => this.validate())
```

## 3. 显隐/禁用导致的校验偏差

- 被隐藏的字段如果仍参与提交，先确认是否需要同步清空。
- 被禁用但仍是事实回填字段时，一般应保留值并置灰；不要因为禁用就误清空。
- “条件显示”的字段如果只在某个请款类型下有效，提交前映射也要同步按类型裁剪。

## 4. 提交流程兜底

以下场景建议在 `beforeSubmitAndDraft` 增加业务兜底：

- 明细表行内必填项可能受联动影响
- 宿主在某些页面态下前端校验顺序不稳定
- 提交前还要做字段转换、拆分或组装

要求：

- 报错提示必须中文
- 优先指明哪一行、哪一个字段缺失
- 兜底只做业务阻断，不要顺手重写整段提交逻辑
