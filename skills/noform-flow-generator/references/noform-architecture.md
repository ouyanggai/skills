# 无表单流程骨架

## 1. 代码入口

宿主里的无表单流程主要集中在这些位置：

- `src/components/NoFormFLow/`
  业务无表单页面本体，例如 `buy_plan`、`contract_review`、`invoice`
- `src/components/NoFormFLow/config/`
  字段和表格配置
- `src/components/NoFormFLow/mixin/mixin.js`
  通用保存、草稿、重提、权限、附件、人员选择能力
- `src/components/NoFormFLow/components/Flow.vue`
  无表单发起、重提、并行/分支选人、最终提交流程
- `src/views/ApproveManage/components/NoForm.vue`
  审批侧统一加载器，按组件 `name` 自动渲染
- `src/views/flowLibrary/NoFormMulBranch/`
  无表单流程模板设计页

当前宿主实测能识别出 6 个顶层无表单业务组件：

- `buy_demand`
- `buy_order`
- `buy_plan`
- `contract_pay_request`
- `contract_review`
- `invoice`

## 2. 自动注册规则

宿主不是手写 import 清单，而是扫描 `src/components/NoFormFLow/` 顶层 `.vue` 文件自动注册。

结论：

- 新无表单组件默认放在 `src/components/NoFormFLow/` 顶层。
- 组件 `name` 是关键绑定键；审批侧和预览侧都靠它查找组件。
- 如果组件只存在于子目录或 `name` 不对，自动注册链会断。
- `buy_order` 这类页面可以完全不用 `CommonForm`，只走 `SimpleTable + 顶部零散字段`；不要强行所有页面都套成同一种壳。

## 3. 四种运行态

无表单页面基本都围绕 `operaType` 四态展开：

- `create`
  新建，允许录入，底部显示“取消 / 保存 / 提交”
- `edit`
  编辑草稿或业务记录，通常允许全量修改
- `examine`
  审核态，字段是否可编辑由节点字段权限控制
- `preview`
  查看态，通常整页只读

这一点应写进组件本身，不要只靠外层弹窗控制。

## 4. 通用拼装方式

高频页面结构通常是：

- 标题区
- 附件或编号信息区
- `CommonForm` 主字段区
- 可选的 `SimpleTable` 明细区
- `CommonFooter`
- `Flow`

其中：

- `CommonForm` 适合二维表单区块
- `SimpleTable` 适合明细行、多列、可编辑表格
- `Flow` 负责流程提交，不负责业务数据保存
- `mixin` 负责把业务保存和流程提交串起来

## 5. 关键绑定关系

这些值通常需要保持同一语义：

- 组件 `name`
- `mixin.js` 里的 `apiList` key
- 审批侧传入的 `currentComponent` / `auditWay`
- `Flow.submitFinal()` 里 `flowInstanceBizRelevanceList` 的业务 `otherBiz`

如果其中一个改了，其他地方通常也要同步。
