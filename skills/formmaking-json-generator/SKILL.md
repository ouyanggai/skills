---
name: formmaking-json-generator
description: 为 rsh-cloud 宿主平台生成和解释 FormMaking 表单 JSON。适用于用户给出业务需求、字段清单、流程场景、现有模板或参考样例，希望产出可直接写入 `t_form_proxy.template_data` 的 JSON；也适用于需要挑选宿主已注入的自定义组件、补齐事件脚本/数据源/动态联动的新表单搭建场景。不适用于既有 JSON 的 bug 修复/问题排查，也不适用于无表单流程或 NoFormFlow。
---

# FormMaking JSON 生成

## 适用边界

- 只处理“有表单流程”的 FormMaking JSON。
- 面向“新建表单”或“按需求重新生成表单”的场景；既有 JSON 的 bug 修复、联动排查、运行时挑战，交给独立的 repair skill。
- 宿主工程通常是 `rsh-cloud-invest-power-system*` 的某个本地分支或目录，它的作用是提供自定义组件、全局能力、接口鉴权与运行约束。
- `NoFormFlow` 明确排除；不要把两套产物混在同一份 JSON 里。

## 先读哪里

- 首次在一个新工作区使用时，先建立本地上下文。
  运行 [scripts/discover_context.py](scripts/discover_context.py) 自动查找本地目录；找不到时，只向使用者询问三项：全过程管理平台的目录（开发目录）、FormMaking 源码目录、生成的 JSON 保存目录。
- 生成或修 JSON 前，先读 [references/formmaking-json-rules.md](references/formmaking-json-rules.md)。
- 需求来源是 Word、截图、PDF 截图或“照这个表做”时，先读 [references/word-source-conversion.md](references/word-source-conversion.md)；如果是 `.docx`，先运行 [scripts/inspect_docx_tables.py](scripts/inspect_docx_tables.py) 提取表格台账。
- 需求里有明显布局要求、截图仿制、打印式表单或复杂分区时，再读 [references/layout-and-common-patterns.md](references/layout-and-common-patterns.md)。
- 用户觉得“布局像了但样式、宽度、审批区还是不像现网”时，再读 [references/style-and-approval-patterns.md](references/style-and-approval-patterns.md)。
- 需求涉及字段联动、远程下拉、动态值、显隐禁用、回填脚本或“选了 A 自动带出 B/C/D”时，再读 [references/event-and-datasource-patterns.md](references/event-and-datasource-patterns.md)。
  需要先从当前工作区的真实样本重新学习事件脚本和数据源分布时，先运行 [scripts/analyze_behavior_patterns.py](scripts/analyze_behavior_patterns.py)。
- 需求涉及宿主自定义组件时，再读 [references/host-custom-components.md](references/host-custom-components.md)。
  需要先快速盘点“当前这个宿主分支到底注册了哪些组件、值形态是什么、哪些组件有虚拟字段或强业务参数”时，先运行 [scripts/inspect_host_components.py](scripts/inspect_host_components.py)。
  如果这次需求明显依赖宿主组件的值结构、虚拟字段、打印态或业务参数，再对照本地源码里的 `src/main.js`、`src/components/Custom/customJson.js`、对应组件 `index.vue`，以及 FormMaking 的 `src/components/GenerateElementItem.vue`、`componentsConfig.js`、`FormTable/index.vue`、`SubForm/index.vue`。
- 需要找最接近的真实样本时，再读 [references/sample-index.md](references/sample-index.md)。
- 生成完成后，优先用 [scripts/validate_form_json.py](scripts/validate_form_json.py) 校验。
- 需要重新从一批 raw 样本学习壳层/样式/审批区规律时，运行 [scripts/analyze_sample_patterns.py](scripts/analyze_sample_patterns.py)。
- 如果当前机器没有 raw 样本，就跳过样本分析脚本，不要把“跑不了分析脚本”误判成“skill 不能生成表单”。

## 本地上下文

- 不要把某个人机器上的绝对路径写进生成逻辑或 skill 文档。
- `raw` / 历史样本目录只属于当前使用者本机的本地增强输入，不能把它当成分发后的通用前置条件，也不能默认其他同事机器上存在同一批样本。
- 默认从当前工作区开始查找：
  `rsh-cloud-invest-power-system*` 宿主工程、`vue-form-making`/`form-making` 源码、`analysis/form-proxy-samples/raw` 样本目录。
- 自动发现失败时，优先用使用者能理解的话询问必要信息：
  全过程管理平台的目录（你的开发目录）、FormMaking 源码目录、生成的 JSON 保存目录。
- 真实样本目录是增强项，不是第一轮必须项；如果使用者已有历史表单 JSON 样本，再询问样本目录用于学习规律。
- 没有样本目录时，仍然要继续完成生成：优先依据宿主源码、FormMaking 源码、用户给出的字段/截图/Word、以及 `validate_form_json.py` 做闭环，不要因为缺少 raw 就停住。
- 发现结果保存在当前工作区的 `.formmaking-json-generator/context.json`。
  这是使用者本机配置，不应作为 skill 内容传播。
- 生成时优先使用本地上下文中的路径；没有上下文时，仍可只依赖用户给出的字段和本 skill 的通用规则生成基础 JSON，并把产物保存到用户指定的 JSON 保存目录。

## 工作流

1. 先定范围。
   只接受 FormMaking 输出；如果用户说的是无表单流程、纯业务页、页面路由或 BPMN 编排，先说明不在本 skill 范围。
2. 归一化需求。
   至少提炼出：表单名称、业务分区、字段清单、重复明细、校验、显隐/禁用/联动、数据源、是否要用宿主自定义组件。
   如果输入来自 Word/截图，先提炼“源表结构台账”：标题、主表列数、行列合并、分区标题、固定重复段、动态明细段、审批意见区、Word 里的复选/单选符号。
3. 先定布局骨架。
   除极简表单外，不要把字段直接平铺在 `list` 顶层；必须先决定每个分区用 `grid`、`report`、`table`、`subform`、`inline` 哪种容器。
   正式审批表、截图仿制、制式台账类表单，默认优先考虑“顶层 `text` 标题 + 顶层 `report` 分区”；不要下意识先套一层单列 `grid`。
4. 选择组件实现路径。
   优先原生字段；只有当宿主组件明显更合适，或者需求明确指向业务组件时，才使用 `custom` 组件。
   如果需求同时包含字段联动、远程下拉或动态默认值，先决定哪些逻辑放 `eventScript`，哪些放 `dataSource` / `remoteDataSource` / `dynamicValue*`，不要全部硬塞进字段默认值。
5. 组装 JSON。
   保持 `list + config` 结构完整，`model` 用语义化英文名，`key` 保证唯一，事件和数据源引用要对得上。
6. 校验与修正。
   生成到文件后执行：
   `python3 skills/formmaking-json-generator/scripts/validate_form_json.py <json文件>`
   校验历史样本或现网遗留模板时，用：
   `python3 skills/formmaking-json-generator/scripts/validate_form_json.py --relaxed <json文件或目录>`
   如果用户给的是现有目录，也可以直接校验整批文件。
7. 闭环交付。
   校验发现错误必须修到通过；校验发现 warning 时，要判断是历史兼容还是新生成质量问题。新生成 JSON 默认应做到严格校验 `0 errors`，正式交付前尽量做到 `0 warnings`。

## 生成规则

- 默认 `config` 采用宿主真实运行时常见值：
  `ui: "element"`、`layout: "horizontal"`、`size: "small"`、`labelWidth: 100`、`width: "100%"`、`hideLabel: false`、`hideErrorMessage: false`。
- 但正式审批表、合同/法务/制式台账类表单，不要机械沿用 `config.width = "100%"`。
  这类表单优先参考真实样本，用 `850px` 或 `900px` 这类固定宽度配合宿主 `.fm-form { margin: 0 auto; }` 做居中。
- 同类正式表单的 `config` 也优先参考真实样本：
  `labelPosition: "right"`、`customClass: "bord"` 或 `customClass: "bord newFormMaking"`、必要时带 `labelCol`。
- 新生成的正式表单，默认至少使用一种布局容器；复杂表单优先显式分区，不要几十个字段裸堆在顶层 `list`。
- 普通业务区优先 `grid`；打印式审批单、制式台账、截图仿制型表单优先 `report`；重复明细优先 `table`；重复块优先 `subform`。
- Word/截图里的固定“一、二、三”分区默认不是动态明细，不要自动改成 `subform`；只有用户明确要求新增/删除/任意多个时才用 `subform` 或 `table`。
- Word 里的 `□`、`☑`、`○`、`●` 默认映射为 `checkbox` 或 `radio`，不要为了省事改成 `select`。
- 底部审批意见/签字区默认按流程意见展示或静态签批占位处理；除非用户明确要求发起人填写，不要过度生成可编辑 `textarea` / `input`。
- 正式表格型表单的标题，优先直接用顶层 `text`，样式类名沿用真实样本里的 `title` / `sub-title` 思路；不要为了标题再包一层没有实际列意义的 `grid`。
- `report` 默认必须显式写 `options.width = "100%"`；漏掉宽度常导致表格左缩、轮廓不完整。
- 如果一个顶层 `grid` 只有 1 个 `span: 24` 列，而且这个列里只放了 1 个 `report`，通常应直接把 `report` 放到顶层，减少无意义布局层级。
- `report` 单元格里优先放字段、`inline`、轻量 `grid` 或必要的 `custom` 组件；除非设计明确需要嵌套表格，否则不要把带边框的 `report` / `table` 一层套一层，避免双重轮廓。
- 截图里的红字批注默认视为“设计说明”，不是最终表单文字样式；不要因为截图标红就把正式表单的回填值、标签或正文做成红色。
- 原合同信息、系统回填值、自动计算结果这类“展示但不可编辑”的字段，优先用 `disabled: true` 做宿主一致的置灰效果，不要只设 `readonly` 也不要再额外做红色强调。
- 正式表格式表单的必填标签，优先沿用宿主的 `showRedPot` 思路显示红色星号；不要把 `*` 直接写进标签文案里。
- 必填不能只配 `options.required` 和红色星号；基础字段必须同步写入 `rules` 必填规则或自定义校验，否则运行时可能不真正拦截提交。
- 业务枚举字段如果已有成熟样本，例如“合同谈判方式”，优先复用原有交互和选项集；不要为了挤进同一行而硬塞进不合理的并列排布。
- 关联合同这类宿主组件返回值通常是“外层选择对象 + 内层 rowData”，回填字段要同时兼容两层字段；如果业务字段可能有编码值和中文值两种形态，要先归一化再写入表单。
- 从原合同回显到可编辑字段时，只在原合同变化时覆盖默认值；用户手动修改后，不能被同一原合同的后续刷新再次覆盖。
- `eventScript`、`dataSource`、`styleSheets` 只在确实需要时补充，但 `eventScript` 建议始终保留数组结构。
- `events` 里填的是事件脚本的 `key`，不是 `name`。
- `custom` 组件必须带 `el`，必要时再补 `options.customProps`、`options.extendProps`、`events`。
- 宿主运行时会把 `custom` 组件的 `options.customProps` 和 `options.extendProps` 一起透传给组件；通用展示参数如 `width`、`height`、`placeholder`、`readonly`、`disabled`、`editable`、`clearable`、`print-read` 由 FormMaking 统一透传。业务上下文参数不要误塞到错误层级。
- 宿主高频自定义组件很多把 `value` 当 JSON 字符串处理，不是对象：
  例如 `custome-info-select`、`general-list-select-show`、`general-flow-list-mulSelect`、`person-mulSelect`、`ltd-or-dep-select`。
  给这些组件写默认值时，优先留空字符串或合法 JSON 字符串，不要直接塞对象/数组。
- `custome-info-select` 依赖字段命名识别类型，`model` 应包含 `userName` / `depName` / `companyName` / `dutyName` 之一；
  `ltd-or-dep-select` 依赖 `singleSelect` / `mulSelect` 识别单多选。
  这类组件的 `model` 不能随便换成无语义英文。
- 宿主高频选择类自定义组件往往会在选择后手动触发父表单 `validate()`，但这不等于可以省略 `rules`；
  必填仍要配好 `options.required`、中文 `requiredMessage` 和 `rules`。
- `table` / `subform` 的源码默认 `showControl: true`，会带出序号、控制列、删除按钮或新增入口。
  正式制式表单、截图仿制、Word 固定分区如果不需要动态增删，优先不用它们，或者显式关掉 `showControl` / `isAdd` / `isDelete`。
- `table.options.noShowTable` 只适合“无数据时整块隐藏”的展示型表格；需要用户主动录入、多行新增或必填校验的表格，默认不要开这个选项。
- 宿主现网样式里 `showRedPot`、`tableNoPadding`、`approvalOpinion`、`autoAuditInfoField` 等类名主要在 `config.customClass` 包含 `newFormMaking` 时稳定生效。
  如果要用这些宿主样式类，外层壳层优先带 `newFormMaking`，正式审批表通常是 `bord newFormMaking`。
- 多附件上传不能只写“必填”；如果需求是“允许多个”，必须同时设置 `options.multiple = true` 和合适的 `options.limit`。
- 当前运行时标准 `fileupload` 不透传文件类型限制，不能假设 `customProps.accept` 一定生效；需要扩展名强约束时，优先写校验说明或改用业务专属组件。
- 需要表达式时使用 `{{ ... }}` 语法，不要把普通字符串和表达式混写成无法执行的值。

## 交付前检查

- 检查正式表格型表单是否整体居中、轮廓完整，不应出现左侧塌缩。
- 检查是否存在“单列 `grid` 纯包一层”的冗余容器。
- 检查是否把 Word 固定重复分区误生成为 `subform`，尤其是出现蓝色新增按钮、编号列、删除按钮、分页控件时要回退为固定 `report` 结构。
- 检查 Word 复选/单选符号是否被误生成为下拉框。
- 检查审批意见区是否被过度字段化；没有明确录入要求时，不要生成一堆可编辑意见/签字输入框。
- 检查是否存在不必要的双重边框，尤其是 `report` 套 `report`、`report` 套 `table` 的场景。
- 检查标题、标签、分区文字是否和真实样本的视觉重心一致，避免标题很正、主体却偏左。
- 检查回填展示字段是否真正置灰不可编辑，而不是只有“不可输入”但视觉上仍像普通输入框。
- 检查必填标签的红色星号、字段 `required`、`requiredMessage` 和实际校验是否一致，不能只显示星号不校验，也不能能校验却没有必填提示。
- 检查所有校验提示是否为中文，尤其是脚本里的 `callback(...)`、`rules[].message`、`requiredMessage`。
- 检查“源数据字段”和“本次填写字段”是否分清：源数据带出的事实字段应置灰不可改；本次需要用户确认或变更的字段，可以默认回显源值，但必须允许修改，且不能被刷新事件反复覆盖。

## 输出要求

- 默认先给最终 JSON。
- 若用了宿主自定义组件、业务专属 `extendProps`、远程数据源或事件脚本，在 JSON 后补一小段“依赖/假设”说明。
- 若用户只要纯 JSON，就只返回 JSON，不加讲解。

## 禁止事项

- 不要混入 NoFormFlow 规则。
- 不要凭空发明宿主没有注册的自定义组件名。
- 不要引用不存在的 `eventScript.key`、`dataSource.key` 或业务字段。
- 不要把业务极强的组件当通用组件滥用，例如 `legal-contract-doctable`、`contract-seal-review-business`。
