# 无表单字段与校验规则

## 1. `CommonForm` 配置 DSL

`CommonForm` 的 `formConfig` 是二维数组，外层代表行，内层代表同一行里的列。

按当前宿主代码盘点，高频字段类型大致是：

- `label`
- `input`
- `select`
- `textarea`
- `radio`
- `date`
- `inputNum`

常见字段对象：

- `type: 'label'`
  纯标签单元格
- `type: 'input' | 'textarea' | 'inputNum' | 'select' | 'date' | 'checkbox' | 'radio'`
  真实录入字段
- `type: 'button'`
  区域内动作按钮
- `type: 'table'`
  直接嵌入 `SimpleTable`
- `children`
  嵌套子布局

高频键：

- `prop`
- `span`
- `title`
- `value`
- `placeholder`
- `disabled`
- `maxlength`
- `options`
- `rules`
- `changeEvent` / `inputEvent` / `clickEvent`

当前宿主里高频 `prop` 还能看到这些复用字段：

- `contractNumber`
- `handledBy`
- `modelNumber`
- `remark`
- `unit`
- `reviewId`
- `paymentAccount`
- `bank`
- `lineNumber`

## 2. 校验放置规则

基础字段校验写在字段自身的 `rules`：

```js
rules: [
  { required: true, message: '请选择合同', trigger: 'change' }
]
```

建议：

- 输入框默认 `blur`
- 选择框默认 `change`
- 校验提示统一中文

## 3. `SimpleTable` 配置 DSL

`SimpleTable` 的配置对象常见结构：

- `isSelection`
- `isIndex`
- `isRadio`
- `align`
- `border`
- `column`
- `action`

可编辑列通过 `slot` 描述：

```js
{
  label: '采购量',
  prop: 'purchaseAmount',
  slot: {
    type: 'number',
    rules: [
      { required: true, message: '请输入采购量' }
    ]
  }
}
```

高频 `slot.type`：

- `input`
- `text`
- `number`
- `date`
- `select`

## 4. 表格校验规则

`SimpleTable.vue` 会把表格包在 `el-form` 里，单元格校验走：

- `prop: 'tableData.<index>.<prop>'`
- `rules: col.slot.rules`

结论：

- 需要校验的表格列，必须放在 `slot.rules`
- 只在组件里手写 `if (!value)` 不够，会失去统一校验体验

## 5. 动态事件写法

无表单页面里不常把函数直接写死进配置文件，而是：

1. 配置文件先留占位函数
2. 页面 `created` 中通过 `assignValue` 注入真实方法

常见用途：

- 选择合同后回填其他字段
- 数字输入后联动金额或剩余量
- 点击按钮打开列表弹窗
- 根据单选/下拉切换禁用态

## 6. 初始化与回显

高频做法：

- `initForm = initFormList(formMainConfig)`
  从配置里生成初始表单对象
- `insertDataToForm(data)`
  把后端详情回填进页面状态
- `processData()`
  把页面状态整理成提交 payload
- `processSaveData()`
  在编辑/重提时把新值合并回原业务对象

规则：

- 不要把回显和提交流程揉成一个方法
- 查看态和审核态都需要可靠回显
- 草稿编辑时不能丢原对象里页面上没展示的字段
