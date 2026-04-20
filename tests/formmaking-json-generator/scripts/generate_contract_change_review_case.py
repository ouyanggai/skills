#!/usr/bin/env python3
from __future__ import annotations

import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "test" / "formmaking_skill" / "generated_cases" / "contract_change_review_form.json"
TD_COUNTER = itertools.count(1)
GRID_COUNTER = itertools.count(1)


def required_rules(required: bool, required_message: str) -> list[dict]:
    if not required:
        return []
    return [{"required": True, "message": required_message or "请填写"}]


def base_field(
    field_type: str,
    key: str,
    model: str,
    name: str = "",
    options: dict | None = None,
    events: dict | None = None,
    rules: list | None = None,
    **extra: object,
) -> dict:
    return {
        "type": field_type,
        "name": name,
        "key": key,
        "model": model,
        "rules": rules or [],
        "options": options or {},
        "events": events or {"onChange": ""},
        **extra,
    }


def static_text(
    text: str,
    key: str,
    custom_class: str = "cell-label",
    *,
    required: bool = False,
) -> dict:
    label_class = custom_class
    if required and "showRedPot" not in label_class.split():
        label_class = f"{label_class} showRedPot".strip()
    return base_field(
        "text",
        key=key,
        model=key,
        name=text,
        options={
            "defaultValue": "",
            "customClass": label_class,
            "labelWidth": "100%",
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "required": False,
            "hideLabel": False,
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": False,
            "subform": False,
        },
        events={"onChange": ""},
    )


def input_field(
    key: str,
    model: str,
    *,
    placeholder: str = "",
    required: bool = False,
    required_message: str = "",
    readonly: bool = False,
    disabled: bool = False,
    custom_class: str = "cell-tight",
    default_value: str = "",
    table_column: bool = False,
    subform: bool = False,
    hidden: bool = False,
) -> dict:
    rules = required_rules(required, required_message)
    return base_field(
        "input",
        key=key,
        model=model,
        name="单行文本",
        options={
            "width": "100%",
            "defaultValue": default_value,
            "required": required,
            "requiredMessage": required_message,
            "dataType": "",
            "dataTypeCheck": False,
            "dataTypeMessage": "",
            "pattern": "",
            "patternCheck": False,
            "patternMessage": "",
            "validatorCheck": False,
            "validator": "",
            "placeholder": placeholder,
            "customClass": custom_class,
            "hideLabel": True,
            "disabled": disabled,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": hidden,
            "dataBind": True,
            "showPassword": False,
            "clearable": False,
            "maxlength": "",
            "showWordLimit": False,
            "customProps": {},
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": table_column,
            "subform": subform,
            "readonly": readonly,
        },
        events={"onChange": "", "onFocus": "", "onBlur": ""},
        rules=rules,
    )


def textarea_field(
    key: str,
    model: str,
    *,
    placeholder: str = "",
    required: bool = False,
    required_message: str = "",
    rows: int = 4,
    readonly: bool = False,
    disabled: bool = False,
    custom_class: str = "cell-tight",
) -> dict:
    rules = required_rules(required, required_message)
    return base_field(
        "textarea",
        key=key,
        model=model,
        name="多行文本",
        options={
            "width": "100%",
            "defaultValue": "",
            "required": required,
            "requiredMessage": required_message,
            "disabled": disabled,
            "pattern": "",
            "patternMessage": "",
            "validatorCheck": False,
            "validator": "",
            "placeholder": placeholder,
            "customClass": custom_class,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "clearable": False,
            "maxlength": 1000,
            "showWordLimit": True,
            "rows": rows,
            "autosize": False,
            "customProps": {},
            "hideLabel": True,
            "readonly": readonly,
            "tableColumn": False,
        },
        events={"onChange": "", "onFocus": "", "onBlur": ""},
        rules=rules,
    )


def number_field(
    key: str,
    model: str,
    *,
    placeholder: str = "",
    required: bool = False,
    required_message: str = "",
    custom_class: str = "cell-tight",
    on_change: str = "",
    disabled: bool = False,
) -> dict:
    rules = required_rules(required, required_message)
    return base_field(
        "number",
        key=key,
        model=model,
        name="计数器",
        options={
            "defaultValue": "",
            "min": 0,
            "max": 999999999,
            "precision": 2,
            "step": 1,
            "controls": True,
            "controlsPosition": "",
            "disabled": disabled,
            "required": required,
            "requiredMessage": required_message,
            "width": "100%",
            "customClass": custom_class,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "hideLabel": True,
            "placeholder": placeholder,
            "tableColumn": False,
        },
        events={"onChange": on_change, "onFocus": "", "onBlur": ""},
        rules=rules,
    )


def radio_field(
    key: str,
    model: str,
    options_list: list[dict],
    *,
    default_value: str,
    on_change: str = "",
    custom_class: str = "cell-tight",
    required: bool = False,
    required_message: str = "",
    validator: str = "",
) -> dict:
    rules = required_rules(required, required_message)
    if validator:
        rules.append({"func": validator})
    return base_field(
        "radio",
        key=key,
        model=model,
        name="单选框组",
        options={
            "inline": True,
            "defaultValue": default_value,
            "showLabel": False,
            "options": options_list,
            "required": required,
            "requiredMessage": required_message,
            "validatorCheck": bool(validator),
            "validator": validator,
            "width": "",
            "remote": False,
            "remoteType": "datasource",
            "remoteOption": f"option_{key}",
            "remoteOptions": [],
            "props": {"value": "value", "label": "label"},
            "remoteFunc": f"func_{key}",
            "customClass": custom_class,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "disabled": False,
            "customProps": {},
            "tableColumn": False,
            "hideLabel": True,
            "subform": False,
        },
        events={"onChange": on_change},
        rules=rules,
    )


def select_field(
    key: str,
    model: str,
    options_list: list[dict],
    *,
    placeholder: str = "",
    required: bool = False,
    required_message: str = "",
    custom_class: str = "cell-tight",
    table_column: bool = False,
    subform: bool = False,
    clearable: bool = False,
    default_value: str = "",
    validator: str = "",
    on_change: str = "",
    remote_data_source: str = "",
    props: dict | None = None,
) -> dict:
    rules = required_rules(required, required_message)
    if validator:
        rules.append({"func": validator})
    options = {
        "defaultValue": default_value,
        "multiple": False,
        "disabled": False,
        "clearable": clearable,
        "placeholder": placeholder,
        "required": required,
        "requiredMessage": required_message,
        "validatorCheck": bool(validator),
        "validator": validator,
        "showLabel": False,
        "width": "100%",
        "options": options_list,
        "remote": bool(remote_data_source),
        "remoteType": "datasource",
        "remoteOption": f"option_{key}",
        "filterable": False,
        "remoteOptions": [],
        "props": props or {"value": "value", "label": "label"},
        "remoteFunc": f"func_{key}",
        "customClass": custom_class,
        "labelWidth": 100,
        "isLabelWidth": False,
        "hidden": False,
        "dataBind": True,
        "customProps": {},
        "tableColumn": table_column,
        "hideLabel": True,
        "subform": subform,
    }
    if remote_data_source:
        options["remoteDataSource"] = remote_data_source
        options["remoteArgs"] = {}
    return base_field(
        "select",
        key=key,
        model=model,
        name="下拉选择框",
        options=options,
        events={"onChange": on_change, "onFocus": "", "onBlur": ""},
        rules=rules,
    )


def custom_field(
    key: str,
    model: str,
    el: str,
    *,
    placeholder: str = "",
    required: bool = False,
    required_message: str = "",
    custom_class: str = "cell-tight",
    default_value: str = "",
    validator: str = "",
    on_change: str = "",
    extend_props: dict | None = None,
) -> dict:
    rules = required_rules(required, required_message)
    if validator:
        rules.append({"func": validator})
    return base_field(
        "custom",
        key=key,
        model=model,
        el=el,
        name="自定义组件",
        options={
            "width": "100%",
            "defaultValue": default_value,
            "required": required,
            "requiredMessage": required_message,
            "dataType": "",
            "dataTypeCheck": False,
            "dataTypeMessage": "",
            "pattern": "",
            "patternCheck": False,
            "patternMessage": "",
            "validatorCheck": bool(validator),
            "validator": validator,
            "placeholder": placeholder,
            "customClass": custom_class,
            "hideLabel": True,
            "disabled": False,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "showPassword": False,
            "clearable": False,
            "maxlength": "",
            "showWordLimit": False,
            "customProps": {},
            "extendProps": extend_props or {},
            "isCustome": True,
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": False,
            "subform": False,
        },
        events={"onChange": on_change, "onFocus": "", "onBlur": ""},
        rules=rules,
    )


def fileupload_field(
    key: str,
    model: str,
    *,
    required_message: str,
    tip: str = "",
) -> dict:
    validator = (
        f"if (!value || value.length === 0) {{ callback('{required_message}'); }} "
        "else { callback(); }"
    )
    return base_field(
        "fileupload",
        key=key,
        model=model,
        name="文件上传",
        options={
            "defaultValue": [],
            "width": "",
            "tokenFunc": "funcGetToken",
            "token": "",
            "tokenType": "datasource",
            "domain": "",
            "disabled": False,
            "tip": tip,
            "action": "/api/web/file/api/file/uploadFile",
            "customClass": "cell-tight upload-cell",
            "limit": 9,
            "multiple": True,
            "isQiniu": False,
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "headers": [],
            "required": True,
            "requiredMessage": required_message,
            "validatorCheck": True,
            "validator": validator,
            "withCredentials": False,
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": False,
            "hideLabel": True,
            "subform": False,
            "customProps": {},
        },
        events={
            "onChange": "",
            "onSelect": "",
            "onUploadSuccess": "",
            "onUploadError": "",
            "onRemove": "",
        },
        rules=[{"func": validator}],
    )


def subform_field(
    key: str,
    model: str,
    inner_list: list[dict],
    *,
    validator: str = "",
    on_row_add: str = "",
    on_row_remove: str = "",
    default_value: list[dict] | None = None,
) -> dict:
    rules = []
    if validator:
        rules.append({"func": validator})
    return base_field(
        "subform",
        key=key,
        model=model,
        name="子表单+",
        options={
            "defaultValue": default_value or [{"partyType": "甲方", "partyName": ""}],
            "customClass": "tableNoPadding",
            "labelWidth": 100,
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "disabled": False,
            "required": False,
            "validatorCheck": bool(validator),
            "validator": validator,
            "paging": False,
            "pageSize": 5,
            "showControl": True,
            "isAdd": True,
            "isDelete": True,
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": False,
            "hideLabel": True,
            "subform": False,
            "requiredMessage": "请输入",
        },
        events={
            "onChange": "",
            "onRowAdd": on_row_add,
            "onRowRemove": on_row_remove,
            "onPageChange": "",
        },
        list=inner_list,
        rules=rules,
    )


def col(children: list[dict], *, span: int = 24, custom_class: str = "") -> dict:
    return {
        "type": "col",
        "options": {
            "span": span,
            "offset": 0,
            "push": 0,
            "pull": 0,
            "xs": span,
            "sm": span,
            "md": span,
            "lg": span,
            "xl": span,
            "customClass": custom_class,
        },
        "list": children,
        "key": f"col_{next(GRID_COUNTER)}",
        "rules": [],
    }


def grid(key: str, columns: list[dict], *, custom_class: str = "section-grid") -> dict:
    return {
        "type": "grid",
        "name": "栅格布局",
        "key": key,
        "model": f"grid_{key}",
        "rules": [],
        "options": {
            "gutter": 0,
            "justify": "start",
            "align": "middle",
            "customClass": custom_class,
            "hidden": False,
            "flex": True,
            "responsive": True,
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
            "tableColumn": False,
        },
        "columns": columns,
    }


def full_width_grid(key: str, children: list[dict], *, custom_class: str = "section-grid") -> dict:
    return grid(key, [col(children)], custom_class=custom_class)


def td(
    children: list[dict],
    *,
    colspan: int = 1,
    rowspan: int = 1,
    custom_class: str = "",
    width: str = "",
    align: str = "left",
) -> dict:
    return {
        "key": f"td_{next(TD_COUNTER)}",
        "list": children,
        "type": "td",
        "options": {
            "align": align,
            "width": width,
            "height": "",
            "valign": "top",
            "colspan": colspan,
            "rowspan": rowspan,
            "customClass": custom_class,
        },
        "rules": [],
    }


def report(
    key: str,
    rows: list[list[dict]],
    *,
    hidden: bool = False,
    header_widths: list[str] | None = None,
) -> dict:
    payload = {
        "type": "report",
        "name": "表格布局",
        "key": key,
        "model": key,
        "rules": [],
        "options": {
            "hidden": hidden,
            "borderWidth": 1,
            "borderColor": "#999",
            "width": "100%",
            "customClass": "report-block",
            "remoteFunc": f"func_{key}",
            "remoteOption": f"option_{key}",
        },
        "rows": [{"columns": columns} for columns in rows],
    }
    if header_widths:
        payload["headerRow"] = [
            {
                "type": "th",
                "options": {"width": width},
                "key": f"th_{key}_{index}",
                "rules": [],
            }
            for index, width in enumerate(header_widths, start=1)
        ]
    return payload


def title_block() -> dict:
    return base_field(
        "text",
        key="contract_change_review_title",
        model="contract_change_review_title",
        name="合同变更评审表",
        options={
            "defaultValue": "",
            "customClass": "sub-title",
            "labelWidth": "100%",
            "isLabelWidth": False,
            "hidden": False,
            "dataBind": True,
            "required": False,
            "hideLabel": False,
            "remoteFunc": "func_contract_change_review_title",
            "remoteOption": "option_contract_change_review_title",
            "tableColumn": False,
        },
        events={"onChange": ""},
    )


def build_main_body_subform() -> dict:
    validator = (
        "let currentMode = this.getValue('mainBodyRadio');\n"
        "if (currentMode !== '手动填写') { callback(); return; }\n"
        "if (!Array.isArray(value) || value.length === 0) { callback('请填写合同主体'); return; }\n"
        "for (let index = 0; index < value.length; index += 1) {\n"
        "  let row = value[index] || {};\n"
        "  if (!row.partyType || !row.partyName) {\n"
        "    callback('请填写完整的合同主体信息');\n"
        "    return;\n"
        "  }\n"
        "}\n"
        "callback();"
    )
    inner_report = report(
        "report_main_body_subform",
        [
            [
                td(
                    [
                        select_field(
                            "main_body_party_type",
                            "partyType",
                            [
                                {"value": "甲方", "label": "甲方"},
                                {"value": "乙方", "label": "乙方"},
                                {"value": "丙方", "label": "丙方"},
                                {"value": "丁方", "label": "丁方"},
                            ],
                            default_value="甲方",
                            clearable=False,
                            subform=True,
                        )
                    ],
                    width="140px",
                ),
                td(
                    [
                        input_field(
                            "main_body_party_name",
                            "partyName",
                            placeholder="请输入合同主体名称",
                            subform=True,
                        )
                    ]
                ),
            ]
        ],
        header_widths=["140px", ""],
    )
    return subform_field(
        "main_body_subform",
        "mainBodySubform",
        [inner_report],
        validator=validator,
        default_value=[{"partyType": "甲方", "partyName": ""}, {"partyType": "乙方", "partyName": ""}],
    )


def build_related_party_report() -> dict:
    relate_validator = (
        "let currentMode = this.getValue('mainBodyRadio');\n"
        "if (currentMode !== '相关方') { callback(); return; }\n"
        "if (!value) { callback('请选择相关方'); return; }\n"
        "callback();"
    )
    return report(
        "relatePartyReport",
        [
            [
                td([static_text("甲方", "label_relate_party_a", "cell-label left-label")], width="140px"),
                td(
                    [
                        select_field(
                            "main_body_relate_a",
                            "mainBodyRelateA",
                            [],
                            validator=relate_validator,
                            remote_data_source="related_party_data_source",
                            props={"value": "id", "label": "name"},
                        )
                    ]
                ),
            ],
            [
                td([static_text("乙方", "label_relate_party_b", "cell-label left-label")], width="140px"),
                td(
                    [
                        select_field(
                            "main_body_relate_b",
                            "mainBodyRelateB",
                            [],
                            validator=relate_validator,
                            remote_data_source="related_party_data_source",
                            props={"value": "id", "label": "name"},
                        )
                    ]
                ),
            ],
        ],
        hidden=True,
        header_widths=["140px", ""],
    )


def build_form() -> dict:
    contract_validator = (
        "try {\n"
        "  const parsed = value ? JSON.parse(value) : {};\n"
        "  if (parsed && parsed.id) {\n"
        "    callback();\n"
        "  } else {\n"
        "    callback('请选择原合同');\n"
        "  }\n"
        "} catch (error) {\n"
        "  callback('请选择原合同');\n"
        "}"
    )
    contract_talk_validator = (
        "if (!value) {\n"
        "  callback('请选择合同谈判方式');\n"
        "} else {\n"
        "  callback();\n"
        "}"
    )
    capital_money_js = (
        "function capitalMoney(num) {\n"
        "  if (num === undefined || num === null || num === '') return '';\n"
        "  num = String(num).replace(/,/g, '');\n"
        "  if (isNaN(Number(num))) return '';\n"
        "  var strOutput = '';\n"
        "  var strUnit = '仟佰拾亿仟佰拾万仟佰拾元角分';\n"
        "  num += '00';\n"
        "  var intPos = num.indexOf('.');\n"
        "  if (intPos >= 0) {\n"
        "    num = num.substring(0, intPos) + num.substr(intPos + 1, 2);\n"
        "  }\n"
        "  strUnit = strUnit.substr(strUnit.length - num.length);\n"
        "  for (var i = 0; i < num.length; i += 1) {\n"
        "    strOutput += '零壹贰叁肆伍陆柒捌玖'.substr(num.substr(i, 1), 1) + strUnit.substr(i, 1);\n"
        "  }\n"
        "  return strOutput\n"
        "    .replace(/零角零分$/, '整')\n"
        "    .replace(/零[仟佰拾]/g, '零')\n"
        "    .replace(/零{2,}/g, '零')\n"
        "    .replace(/零([亿|万])/g, '$1')\n"
        "    .replace(/零+元/, '元')\n"
        "    .replace(/亿零{0,3}万/, '亿')\n"
        "    .replace(/^元/, '零元');\n"
        "}\n"
    )
    pick_function_js = (
        "function pick() {\n"
        "  for (var i = 0; i < arguments.length; i += 1) {\n"
        "    var item = arguments[i];\n"
        "    if (item !== undefined && item !== null && item !== '') {\n"
        "      return item;\n"
        "    }\n"
        "  }\n"
        "  return '';\n"
        "}\n"
    )
    normalize_contract_talk_js = (
        "function normalizeContractTalk(value) {\n"
        "  if (value === undefined || value === null || value === '') return '';\n"
        "  let raw = String(value).trim();\n"
        "  let map = {\n"
        "    'open': '公开招标',\n"
        "    'openBid': '公开招标',\n"
        "    'publicBidding': '公开招标',\n"
        "    '公开招标': '公开招标',\n"
        "    'invitation': '非公开挂网',\n"
        "    '邀请招标': '非公开挂网',\n"
        "    '非公开挂网': '非公开挂网',\n"
        "    'inquiry': '非挂网方式',\n"
        "    'negotiations': '非挂网方式',\n"
        "    'consult': '非挂网方式',\n"
        "    '询比采购': '非挂网方式',\n"
        "    '竞争性谈判采购': '非挂网方式',\n"
        "    '竞争性磋商采购': '非挂网方式',\n"
        "    '非挂网方式': '非挂网方式',\n"
        "    'direct': '直签',\n"
        "    'directSign': '直签',\n"
        "    '直签': '直签',\n"
        "    'singleSource': '单一来源采购',\n"
        "    'single_source': '单一来源采购',\n"
        "    '单一来源采购': '单一来源采购',\n"
        "    'internal': '内部采购',\n"
        "    'internalPurchase': '内部采购',\n"
        "    '内部采购': '内部采购',\n"
        "    'framework': '框采',\n"
        "    '框架协议采购': '框采',\n"
        "    '框采': '框采',\n"
        "    'other': '其他',\n"
        "    '其他': '其他'\n"
        "  };\n"
        "  return map[raw] || raw;\n"
        "}\n"
    )
    form = {
        "list": [
            title_block(),
            input_field(
                "origin_contract_sync_key",
                "originContractSyncKey",
                disabled=True,
                hidden=True,
            ),
            input_field(
                "origin_contract_talk_way",
                "originContractTalkWay",
                disabled=True,
                hidden=True,
            ),
            report(
                "report_contract_header",
                [
                    [
                        td([static_text("合同名称", "label_contract_name", required=True)], width="140px"),
                        td(
                            [
                                input_field(
                                    "contract_name",
                                    "contractName",
                                    placeholder="请输入合同名称",
                                    required=True,
                                    required_message="请输入合同名称",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同编号", "label_contract_code", required=True)], width="140px"),
                        td(
                            [
                                input_field(
                                    "contract_code",
                                    "contractCode",
                                    placeholder="请输入合同编号",
                                    required=True,
                                    required_message="请输入合同编号",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                ],
                header_widths=["140px", "", "", "", ""],
            ),
            report(
                "report_origin_contract_info",
                [
                    [
                        td([static_text("原合同信息", "label_origin_section", "section-label")], rowspan=4, width="140px", align="center"),
                        td([static_text("关联合同", "label_origin_contract_selector", required=True)], width="140px"),
                        td(
                            [
                                custom_field(
                                    "origin_contract_obj",
                                    "originContractObj",
                                    "general-list-select-show",
                                    placeholder="请选择原合同",
                                    required=True,
                                    required_message="请选择原合同",
                                    default_value="{}",
                                    validator=contract_validator,
                                    on_change="onChange_origin_contract_obj",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("项目名称", "label_origin_project_name")], width="140px"),
                        td(
                            [
                                input_field(
                                    "origin_project_name",
                                    "originProjectName",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同主体", "label_origin_subject")], width="140px"),
                        td(
                            [
                                input_field(
                                    "origin_contract_subject",
                                    "originContractSubject",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同分类", "label_origin_category")], width="140px"),
                        td(
                            [
                                input_field(
                                    "origin_contract_category",
                                    "originContractCategory",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                ],
                header_widths=["140px", "140px", "", "", "", ""],
            ),
            report(
                "report_changed_contract_info",
                [
                    [
                        td([static_text("变更后合同信息", "label_changed_section", "section-label")], rowspan=4, width="140px", align="center"),
                        td([static_text("合同主体", "label_main_body", required=True)], width="140px"),
                        td(
                            [
                                radio_field(
                                    "main_body_radio",
                                    "mainBodyRadio",
                                    [
                                        {"value": "手动填写", "label": "手动填写"},
                                        {"value": "相关方", "label": "相关方"},
                                    ],
                                    default_value="手动填写",
                                    on_change="onChange_main_body_radio",
                                ),
                                build_main_body_subform(),
                                build_related_party_report(),
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同谈判方式", "label_contract_talk", required=True)], width="140px"),
                        td(
                            [
                                radio_field(
                                    "contract_talk",
                                    "contractTalk",
                                    [
                                        {"value": "公开招标", "label": "公开招标"},
                                        {"value": "非公开挂网", "label": "非公开挂网"},
                                        {"value": "非挂网方式", "label": "非挂网方式"},
                                        {"value": "直签", "label": "直签"},
                                        {"value": "单一来源采购", "label": "单一来源采购"},
                                        {"value": "内部采购", "label": "内部采购"},
                                        {"value": "框采", "label": "框采"},
                                        {"value": "其他", "label": "其他"},
                                    ],
                                    default_value="",
                                    required=True,
                                    required_message="请选择合同谈判方式",
                                    validator=contract_talk_validator,
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同变更内容", "label_contract_change_content", required=True)], width="140px"),
                        td(
                            [
                                textarea_field(
                                    "contract_change_content",
                                    "contractChangeContent",
                                    placeholder="请输入合同变更内容",
                                    required=True,
                                    required_message="请输入合同变更内容",
                                    rows=5,
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                    [
                        td([static_text("合同文件", "label_contract_file_list", required=True)], width="140px"),
                        td(
                            [
                                fileupload_field(
                                    "contract_file_list",
                                    "contractFileList",
                                    required_message="请上传合同文件",
                                    tip="允许上传多个文件",
                                )
                            ],
                            colspan=4,
                        ),
                    ],
                ],
                header_widths=["140px", "140px", "", "", "", ""],
            ),
            report(
                "report_change_description",
                [
                    [
                        td([static_text("变更情况说明", "label_change_description")], width="140px"),
                        td(
                            [
                                textarea_field(
                                    "change_description",
                                    "changeDescription",
                                    placeholder="请输入变更情况说明",
                                    rows=4,
                                )
                            ],
                            colspan=4,
                        ),
                    ]
                ],
                header_widths=["140px", "", "", "", ""],
            ),
            report(
                "report_amount_info",
                [
                    [
                        td([static_text("原合同金额（元）", "label_origin_amount")], width="140px"),
                        td(
                            [
                                input_field(
                                    "origin_contract_amount",
                                    "originContractAmount",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ],
                            colspan=2,
                        ),
                        td([static_text("大写", "label_origin_amount_upper")], width="140px"),
                        td(
                            [
                                input_field(
                                    "origin_contract_amount_upper",
                                    "originContractAmountUpper",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ]
                        ),
                    ],
                    [
                        td([static_text("变更后合同金额（元）", "label_changed_amount", required=True)], width="140px"),
                        td(
                            [
                                number_field(
                                    "changed_contract_amount",
                                    "changedContractAmount",
                                    required=True,
                                    required_message="请输入变更后合同金额",
                                    on_change="onChange_changed_contract_amount",
                                )
                            ],
                            colspan=2,
                        ),
                        td([static_text("大写", "label_changed_amount_upper")], width="140px"),
                        td(
                            [
                                input_field(
                                    "changed_contract_amount_upper",
                                    "changedContractAmountUpper",
                                    disabled=True,
                                    custom_class="display-disabled cell-tight",
                                )
                            ]
                        ),
                    ],
                ],
                header_widths=["140px", "", "", "140px", ""],
            ),
        ],
        "config": {
            "labelWidth": 100,
            "labelPosition": "right",
            "size": "small",
            "customClass": "bord newFormMaking",
            "ui": "element",
            "layout": "horizontal",
            "labelCol": 3,
            "width": "850px",
            "hideLabel": False,
            "hideErrorMessage": False,
            "styleSheets": (
                ".sub-title .el-form-item__label{\n"
                "  text-align: center !important;\n"
                "  font-size: 22px !important;\n"
                "}\n"
                ".report-block { margin-bottom: 0 !important; }\n"
                ".report-block .el-form-item { margin-bottom: 0 !important; }\n"
                ".cell-label .el-form-item__label { text-align: center !important; color: #606266; font-weight: 600; }\n"
                ".left-label .el-form-item__label { text-align: left !important; }\n"
                ".section-label .el-form-item__label { text-align: center !important; color: #303133; font-weight: 700; }\n"
                ".display-disabled .el-input.is-disabled .el-input__inner, .display-disabled .el-textarea.is-disabled .el-textarea__inner { color: #909399 !important; background-color: #f5f7fa !important; text-align: center; }\n"
                ".cell-tight { margin-bottom: 0 !important; }\n"
                ".upload-cell .el-upload { display: inline-block; }\n"
                ".tableNoPadding .el-form-item { margin-bottom: 0 !important; }\n"
            ),
            "eventScript": [
                {
                    "key": "refresh",
                    "name": "refresh",
                    "func": (
                        "let winHash = window.location.hash || '';\n"
                        "if (winHash.indexOf('flowLibrary/formFlow') > -1) return;\n"
                        "const initiatorCompanyId = this.getValue('initiatorCompanyId') || window.localStorage.getItem('invest-power-system-companyId') || '';\n"
                        "const companyName = this.getValue('companyName') || window.localStorage.getItem('invest-power-system-companyName') || '';\n"
                        "let currentValue = this.getValue('originContractObj');\n"
                        "let parsedValue = {};\n"
                        "try {\n"
                        "  parsedValue = currentValue ? JSON.parse(currentValue) : {};\n"
                        "} catch (error) {\n"
                        "  parsedValue = {};\n"
                        "}\n"
                        "if (!parsedValue || Array.isArray(parsedValue)) {\n"
                        "  parsedValue = {};\n"
                        "}\n"
                        "if (!parsedValue.initiatorCompanyId || !parsedValue.companyName) {\n"
                        "  this.setData({\n"
                        "    originContractObj: JSON.stringify(Object.assign({}, parsedValue, {\n"
                        "      initiatorCompanyId: initiatorCompanyId,\n"
                        "      companyName: companyName,\n"
                        "    }))\n"
                        "  });\n"
                        "}\n"
                        "this.triggerEvent('syncOriginContractInfo');\n"
                        "this.triggerEvent('toggleMainBodyMode', this.getValue('mainBodyRadio') || '手动填写');\n"
                        "this.triggerEvent('syncChangedAmountUpper');"
                    ),
                },
                {
                    "key": "onChange_origin_contract_obj",
                    "name": "onChange_origin_contract_obj",
                    "func": "this.triggerEvent('syncOriginContractInfo');",
                },
                {
                    "key": "syncOriginContractInfo",
                    "name": "syncOriginContractInfo",
                    "func": (
                        pick_function_js
                        + capital_money_js
                        + normalize_contract_talk_js
                        + "let parsedValue = {};\n"
                        "try {\n"
                        "  parsedValue = JSON.parse(this.getValue('originContractObj') || '{}');\n"
                        "} catch (error) {\n"
                        "  parsedValue = {};\n"
                        "}\n"
                        "let rowData = {};\n"
                        "try {\n"
                        "  rowData = parsedValue.rowData ? JSON.parse(parsedValue.rowData) : {};\n"
                        "} catch (error) {\n"
                        "  rowData = {};\n"
                        "}\n"
                        "let originContractSyncKey = pick(parsedValue.id, parsedValue.contractId, parsedValue.bizId, rowData.id, rowData.contractId, rowData.bizId, rowData.flowProxyId, '');\n"
                        "let cachedSyncKey = this.getValue('originContractSyncKey') || '';\n"
                        "let originAmount = pick(\n"
                        "  rowData.contractSum,\n"
                        "  rowData.contractAmount,\n"
                        "  rowData.contractMoney,\n"
                        "  rowData.amount,\n"
                        "  parsedValue.contractSum,\n"
                        "  ''\n"
                        ");\n"
                        "let originSubject = pick(\n"
                        "  rowData.newContractBody,\n"
                        "  rowData.contractBodyName,\n"
                        "  rowData.contractMainBody,\n"
                        "  rowData.contractBody,\n"
                        "  parsedValue.newContractBody,\n"
                        "  ''\n"
                        ");\n"
                        "let originTalkWay = normalizeContractTalk(pick(\n"
                        "  rowData.contractTalk,\n"
                        "  rowData.contractTalkName,\n"
                        "  rowData.procureWay,\n"
                        "  rowData.procureWayName,\n"
                        "  rowData.negotiationMethod,\n"
                        "  rowData.negotiationWay,\n"
                        "  rowData.contractNegotiationMethod,\n"
                        "  rowData.contractNegotiationWay,\n"
                        "  parsedValue.contractTalk,\n"
                        "  parsedValue.contractTalkName,\n"
                        "  parsedValue.procureWay,\n"
                        "  parsedValue.procureWayName,\n"
                        "  parsedValue.negotiationMethod,\n"
                        "  parsedValue.negotiationWay,\n"
                        "  parsedValue.contractNegotiationMethod,\n"
                        "  parsedValue.contractNegotiationWay,\n"
                        "  ''\n"
                        "));\n"
                        "let nextData = {\n"
                        "  originContractSyncKey: originContractSyncKey,\n"
                        "  originProjectName: pick(rowData.projectName, rowData.contractProjectName, parsedValue.projectName, ''),\n"
                        "  originContractSubject: originSubject,\n"
                        "  originContractCategory: pick(rowData.classificationName, rowData.contractCategoryName, rowData.contractCategory, parsedValue.classificationName, ''),\n"
                        "  originContractTalkWay: originTalkWay,\n"
                        "  originContractAmount: originAmount,\n"
                        "  originContractAmountUpper: capitalMoney(originAmount)\n"
                        "};\n"
                        "if (originContractSyncKey && originContractSyncKey !== cachedSyncKey) {\n"
                        "  nextData.contractTalk = originTalkWay || '';\n"
                        "} else if (!this.getValue('contractTalk') && originTalkWay) {\n"
                        "  nextData.contractTalk = originTalkWay;\n"
                        "}\n"
                        "this.setData(nextData);"
                    ),
                },
                {
                    "key": "onChange_changed_contract_amount",
                    "name": "onChange_changed_contract_amount",
                    "func": "this.triggerEvent('syncChangedAmountUpper');",
                },
                {
                    "key": "syncChangedAmountUpper",
                    "name": "syncChangedAmountUpper",
                    "func": (
                        capital_money_js
                        + "const changedAmount = this.getValue('changedContractAmount');\n"
                        "this.setData({ changedContractAmountUpper: capitalMoney(changedAmount) });"
                    ),
                },
                {
                    "key": "onChange_main_body_radio",
                    "name": "onChange_main_body_radio",
                    "func": "this.triggerEvent('toggleMainBodyMode', arguments[0]);",
                },
                {
                    "key": "toggleMainBodyMode",
                    "name": "toggleMainBodyMode",
                    "func": (
                        "let param = arguments[0];\n"
                        "let currentValue = param && param.value ? param.value : param;\n"
                        "if (currentValue === '相关方') {\n"
                        "  this.display(['relatePartyReport']);\n"
                        "  this.hide(['mainBodySubform']);\n"
                        "  this.setData({ mainBodySubform: [{ partyType: '甲方', partyName: '' }, { partyType: '乙方', partyName: '' }] });\n"
                        "} else {\n"
                        "  this.display(['mainBodySubform']);\n"
                        "  this.hide(['relatePartyReport']);\n"
                        "  this.setData({ mainBodyRelateA: '', mainBodyRelateB: '' });\n"
                        "}"
                    ),
                },
            ],
            "dataSource": [
                {
                    "key": "related_party_data_source",
                    "name": "获取相关方列表",
                    "url": "/api/web/user/api/company/queryCompanyListByNameForRelatedParty?platformCode=200001",
                    "method": "POST",
                    "auto": True,
                    "params": {},
                    "headers": {},
                    "responseFunc": "return res.data;",
                    "requestFunc": (
                        "let WHOST = window.location.host;\n"
                        "let host = '';\n"
                        "if (WHOST.indexOf('bserver') === 0) {\n"
                        "  host = 'https://iserver.runshihua.com';\n"
                        "} else {\n"
                        "  host = 'http://192.168.1.220:8081';\n"
                        "}\n"
                        "let sid = '';\n"
                        "for (const key in window.localStorage) {\n"
                        "  if (key.endsWith('invest-power-system-token')) {\n"
                        "    sid = window.localStorage.getItem(key);\n"
                        "  }\n"
                        "}\n"
                        "config.url = host + config.url + '&sid=' + sid;\n"
                        "config.data = { data: {}, sid: sid };\n"
                        "return config;"
                    ),
                    "args": [],
                }
            ],
        },
    }
    return form


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(build_form(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
