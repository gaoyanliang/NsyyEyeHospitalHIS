# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块：患者主索引与建档（MPI & Registration）详细设计

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI（子模块编号 M03-01 患者主索引与建档）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M01 主数据管理MDM》《M02 统一权限与安全 01 账号管理》《M02 统一权限与安全 06 审计日志》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery / APScheduler
**文档用途：** 作为患者主索引与建档子模块开发、测试、验收依据；作为 M03 会员、随访、消息、门户子模块及 M04/M05/M07/M09/M10/M11/M12/M13/M16/M19 的患者身份基础

---

## 目录

1. [模块概述](#1-模块概述)
2. [业务范围与边界](#2-业务范围与边界)
3. [业务模型](#3-业务模型)
4. [数据结构设计](#4-数据结构设计)
5. [页面设计](#5-页面设计)
6. [后端接口设计](#6-后端接口设计)
7. [缓存与异步任务设计](#7-缓存与异步任务设计)
8. [业务规则与校验](#8-业务规则与校验)
9. [权限与安全](#9-权限与安全)
10. [主数据分发与集成](#10-主数据分发与集成)
11. [异常处理与日志](#11-异常处理与日志)
12. [验收标准](#12-验收标准)

---

## 1. 模块概述

### 1.1 模块定位

患者主索引与建档回答一个前置问题：**“患者是谁”**。

本子模块建立全院统一患者主索引（EMPI），维护患者主档、证件标识、联系方式、地址、联系人/监护人、授权同意、建档变更日志、批量导入与同步日志。所有临床、收费、视光、屈光、检查检验、随访、会员、门户业务必须通过 `patient_id` / `empi_no` 引用患者身份，不允许各自重复建档。

**边界一句话：** 本子模块只管“患者身份这个主数据容器本身”——存在、唯一、可识别、可联系、授权可追溯；**不做**重复患者匹配合并审批（M03-02），**不做**会员权益（M03-03/M19），**不做**随访执行（M03-04/M19），**不做**消息发送（M03-05），**不做**挂号收费病历（M04/M16/M18）。

### 1.2 与 M01 职工、M02 账号的区别

| 对象 | 归属 | 表 | 说明 |
|---|---|---|---|
| 职工 | M01 | `mdm_employee` | 人事意义上的“人”，有工号、职称、科室、执业证书 |
| 账号 | M02 | `sys_account` | 系统使用者凭据，有登录名、密码、状态 |
| 患者 | **M03 本子模块** | `mpi_patient` | 医疗服务对象，有 EMPI 号、证件、联系方式、授权 |

### 1.3 模块目标

- **统一 EMPI**：全院唯一患者主索引号 `empi_no`，不可变。
- **一主证件一患者**：主证件类型 + 证件号哈希唯一；附加证件可多条。
- **多联系方式**：手机、座机、邮箱、微信标识等，支持主联系方式与验证状态。
- **授权可追溯**：隐私、诊疗、营销、数据共享授权按版本留痕。
- **全院共享**：通过内部接口 + 事件向门诊、住院、视光、屈光、检查检验、收费、随访、会员提供患者身份。
- **敏感数据安全**：证件号、手机号加密存储，哈希检索，掩码展示。
- **可批量**：支持 Excel 导入建档、导出脱敏清单。
- **强审计**：建档、修改、冻结、解冻、死亡登记、授权变更全部留痕；敏感字段查看走 M02 审计。

### 1.4 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 导医/客服 | 首次建档、信息补全 | 新建患者、查询、修改联系方式 |
| 收费员 | 挂号收费前查患者 | 快速检索、查看患者简要 |
| 门诊/住院医生 | 查看患者身份 | 患者详情、授权查看 |
| 护士 | 核对患者身份 | 查询、联系方式核对 |
| 患者本人 | 患者端自助 | 查看/更新本人联系方式、授权 |
| 信息科 | 数据治理 | 导入、导出、日志审计 |
| 审计员 | 追溯 | 查看建档变更日志与敏感访问审计 |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 患者主索引 | `empi_no` 生成、唯一性、状态管理 |
| 患者主档 | 姓名、性别、出生日期、民族、婚姻、学历、职业、患者类型、来源、过敏史 |
| 证件标识 | 主证件 + 附加证件，加密存储、哈希检索、掩码展示 |
| 联系方式 | 手机、座机、邮箱、微信标识，主联系方式 |
| 地址 | 家庭、工作、账单地址 |
| 联系人/监护人 | 紧急联系人、法定监护人、家属 |
| 授权同意 | 隐私、诊疗、营销、数据共享授权及撤回 |
| 建档日志 | 全量变更留痕 |
| 批量导入 | Excel 模板、校验、导入任务与明细 |
| 患者快速检索 | 供挂号、收费、门诊、住院、视光、屈光、检查检验调用 |
| 患者端“我的信息” | 查看本人主档、更新联系方式、查看授权 |
| 同步推送 | 建档/修改/合并后**主动推送**患者简要至 M01 `md_patient`（`POST /internal/v1/mdm/patients/sync`），失败自动重试 |
| 内部接口 | 按 ID/EMPI/证件哈希/手机号哈希返回患者简要 |

### 2.2 范围外

| 范围外内容 | 负责方 |
|---|---|
| 重复患者匹配、候选识别、合并审批、拆分、质量评分规则 | M03-02 患者匹配合并与质量 |
| 会员等级、权益、积分、营销 | M03-03 会员主档 / M19 会员运营 |
| 随访计划模板 | M03-04 随访（模板部分） |
| 随访任务执行、外呼 | M19 随访执行 |
| 消息模板、发送、回执 | M03-05 消息中心 |
| 公众号/小程序门户页面 | M03-06 患者门户与自助服务 |
| 挂号、分诊、叫号 | M04 门诊管理 |
| 收费、结算、发票 | M16 收费结算 |
| 病历、诊断、医嘱 | M07/M18 |
| 检查检验申请与报告 | M12/M13 |
| 职工、科室、字典主数据 | M01 |
| 账号、权限、审计存储 | M02 |

### 2.3 与相邻模块分工

```text
M01 字典/职工/科室 ──► M03-01 患者主索引与建档 ◄── M02 账号/权限/审计
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
M03-02 匹配合并        M03-03 会员主档        M03-04 随访模板
        │                     │                     │
        └──────────────► patient_id / empi_no ◄────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
M01 患者同步表  M04 门诊  M05 住院  M10 视光  M11 屈光  M12/M13 检查检验  M16 收费  M19 随访执行
```

**关键约定：**
- `mpi_patient` 是全院患者身份**唯一主表与唯一写入方**；M01 的 `md_patient` 是 M01 侧的**只读镜像**，只能由本模块推送更新，M01 内部任何业务都不得直接写该表。
- 跨模块只传 `patient_id`、`empi_no`、患者简要，不传完整证件号/手机号明文。
- 合并动作由 M03-02 执行；本子模块只保留 `status=MERGED` 与 `merge_to_id` 字段。
- 敏感字段明文查看走 M02-05 二次验证，事件写 M02-06 审计日志。

### 2.4 依赖清单（对 M01/M02）

| 依赖方 | 依赖内容 | 用途 | 使用点 |
|---|---|---|---|
| M01 职工 | `mdm_employee.id/code/name/dept_id/title` | 操作人、医生、护士、客服身份 | `created_by`、`updated_by`、`operator_id`、日志冗余 |
| M01 科室 | `mdm_department.id/code/name` | 操作人科室、数据权限、患者来源科室 | 权限过滤、日志 |
| M01 字典 | `md_dict_type` / `md_dict_item` | 性别、证件类型、民族、婚姻、学历、职业、关系、地址类型、联系方式类型、患者类型、来源、授权类型 | 枚举校验与展示 |
| M01 参数 | `md_sys_param` | EMPI 前缀、导入上限、导出上限、完整度阈值、日志保留 | 业务规则 |
| M02 账号 | `sys_account.id` / 账号状态 | 操作人、患者端账号 | `created_by`、`operator_id`、患者端 `me` 接口 |
| M02 权限 | `mpi:patient:*` 权限码、数据权限 | 页面/接口鉴权 | 第 9 章 |
| M02 审计 | `sys_audit_log` | 敏感字段查看审计 | 第 9/11 章 |
| M02 二次验证 | `sys_mfa_challenge` | 查看证件号明文前验证 | 第 9 章 |
| M20 消息 | 短信发送 | 患者端验证码、导入结果通知（可降级） | 第 7/10 章 |

---

## 3. 业务模型

### 3.1 患者状态机

```text
                    ┌──────────────┐
                    │   NORMAL     │ 正常
                    └───┬───┬───┬──┘
         冻结            │   │   │ 死亡登记
         ┌──────────────┘   │   └──────────────┐
         ▼                  │                  ▼
   ┌──────────┐             │            ┌──────────┐
   │  FROZEN  │◄────────────┘            │ DECEASED │
   │  已冻结   │  解冻                     │  已死亡   │
   └────┬─────┘                           └──────────┘
        │
        │ M03-02 合并
        ▼
   ┌──────────┐
   │  MERGED  │ 已合并（不可直接编辑，指向 merge_to_id）
   └──────────┘
```

| 状态 | 代码 | 说明 | 能否业务引用 | 恢复 |
|---|---|---|---|---|
| 正常 | `NORMAL` | 正常患者 | 是 | — |
| 已冻结 | `FROZEN` | 信息争议/安全原因 | 仅查看 | 管理员解冻 |
| 已死亡 | `DECEASED` | 死亡登记 | 可查看历史 | 不可逆（误操作需 M03-02/信息科审批） |
| 已合并 | `MERGED` | 被合并到目标患者 | 只读，跳转目标 | 由 M03-02 拆分 |

**状态转换规则：**

| 当前 | 操作 | 目标 | 触发方 | 校验 |
|---|---|---|---|---|
| NORMAL | 冻结 | FROZEN | 管理员 | 填原因 ≥5 字 |
| FROZEN | 解冻 | NORMAL | 管理员 | — |
| NORMAL/FROZEN | 死亡登记 | DECEASED | 管理员/护士 | 填死亡时间、原因 |
| NORMAL | 合并 | MERGED | M03-02 | 合并审批通过 |
| MERGED | 拆分 | NORMAL | M03-02 | 拆分审批通过 |

### 3.2 患者类型与来源（字典由 M01 维护）

| 患者类型 | 代码 | 说明 |
|---|---|---|
| 普通 | `NORMAL` | 默认 |
| VIP | `VIP` | 会员/高价值患者，权益由 M03-03/M19 管理 |
| 外部/转诊 | `EXTERNAL` | 外院转诊、合作单位 |
| 员工/家属 | `STAFF_FAMILY` | 院内职工及家属 |

| 来源 | 代码 |
|---|---|
| 门诊 | `OUTPATIENT` |
| 住院 | `INPATIENT` |
| 视光 | `OPTOMETRY` |
| 屈光 | `REFRACTIVE` |
| 公众号/小程序 | `MINIAPP` |
| 自助机 | `SELF_MACHINE` |
| 转诊 | `REFERRAL` |
| 导入 | `IMPORT` |

### 3.3 EMPI 号规则

- 格式：`P + YYYYMMDD + 6 位流水`，例如 `P20261020000001`。
- 生成：每日流水，Redis `INCR` + DB 唯一约束兜底；高并发下允许重试。
- 特性：**全局唯一、不可修改、合并后保留**。
- 展示：患者列表、详情、内部接口均返回 `empi_no`。
- 参数来自 M01 `md_sys_param`：`MPI.EMPI.PREFIX`（默认 `P`）、`MPI.EMPI.DAILY_SEQ_LEN`（默认 6）。

### 3.4 证件模型

| 项 | 规则 |
|---|---|
| 主证件 | `mpi_patient.primary_id_type` + `primary_id_no_hash` 部分唯一 |
| 附加证件 | `mpi_patient_identifier` 可多条 |
| 证件类型（字典 `ID_TYPE`，M01 维护） | 身份证、护照、港澳台通行证、军官证、出生证、监护人证件、无证件 |
| 存储 | `id_no_enc` 加密，`id_no_hash` 检索，`id_no_mask` 展示 |
| 无证件 | 允许主证件为空，但必须姓名 + 性别 + 出生日期 + 联系方式至少两项，标记来源 |
| 证件唯一 | 同一证件类型 + 证件号哈希在全院只能对应一个有效患者 |

### 3.5 联系方式模型

| 类型（字典 `CONTACT_TYPE`） | 代码 | 说明 |
|---|---|---|
| 手机 | `MOBILE` | 主联系方式常用 |
| 座机 | `TEL` | 含区号 |
| 邮箱 | `EMAIL` | — |
| 微信标识 | `WECHAT` | 门户绑定标识，不存 openid 明文，存哈希 + 掩码 |
| 其他 | `OTHER` | — |

- 手机号可被家属共用，**不强制唯一**；建档时若命中其他患者手机号，提示但不阻断。
- 每种联系方式可有一个主联系方式。

### 3.6 授权同意模型（字典 `CONSENT_TYPE`）

| 授权类型 | 代码 | 说明 |
|---|---|---|
| 隐私政策 | `PRIVACY` | 患者隐私授权 |
| 诊疗同意 | `TREATMENT` | 一般诊疗授权 |
| 营销通知 | `MARKETING` | 会员/随访营销，可拒绝 |
| 数据共享 | `DATA_SHARE` | 商保/转诊共享 |

| 状态 | 代码 |
|---|---|
| 已授权 | `GRANTED` |
| 已拒绝 | `REFUSED` |
| 已撤回 | `WITHDRAWN` |

授权按 `consent_version` 留痕，撤回不删除历史。

### 3.7 基础质量评分

本子模块只计算基础完整性评分（0~100）：姓名、性别、出生日期、主证件、手机号、地址、联系人等字段完整度。重复候选、相似度、合并建议由 M03-02 负责。

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md)

本章原包含 **12 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 患者主索引与建档完整数据结构 | [患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```text
患者服务与EMPI
└── 患者主索引与建档
    ├── P01 患者列表（核心页）
    ├── P02 患者详情（360 基础视图）
    ├── P03 新建/编辑患者
    ├── P04 证件与联系方式
    ├── P05 地址与联系人
    ├── P06 授权同意
    ├── P07 患者导入
    └── P08 患者变更日志
```

### 5.2 P01 患者列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：患者服务与EMPI / 患者主索引与建档                     用户：导医01 ▾   │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：患者总数 12,386 | 今日新建 36 | 已冻结 8 | 已死亡 12 | 待补全 45      │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：关键字[姓名/EMPI/证件号/手机号] 状态[全部▼] 类型[全部▼] 来源[全部▼]      │
│ 工具栏：[＋新建患者] [导入] [导出] [批量补全]                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │EMPI          │姓名 │性别│出生日期  │主证件    │手机号     │状态  │操作│
│ ☐ │P202610200001 │王五 │男  │1980-01-02│身份证*** │138****5678│正常  │···│
│ ☐ │P202610200002 │李四 │女  │1992-05-11│身份证*** │139****2345│正常  │···│
│ ☐ │P202610200003 │张三 │男  │2018-09-20│出生证*** │—          │正常  │···│
│ ☐ │P202610200004 │赵六 │女  │1970-12-01│护照***   │137****8899│已冻结│···│
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 12,386 条                                      [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**列：** EMPI、姓名、性别、出生日期、主证件掩码、手机号掩码、患者类型、来源、状态、最后就诊、操作。

**筛选：** 关键字（姓名/拼音/EMPI/证件号哈希后检索/手机号哈希）、状态、类型、来源、是否有主证件、创建时间。

**操作：** 查看详情、编辑、证件与联系方式、地址与联系人、授权同意、冻结/解冻、死亡登记、查看日志。

### 5.3 P02 患者详情

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 患者详情：P202610200001  王五                              状态：正常          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【基本信息】                                                                    │
│ 姓名：王五        性别：男        出生日期：1980-01-02（46 岁）                 │
│ 民族：汉族        婚姻：已婚      学历：本科      职业：教师                     │
│ 患者类型：普通    来源：门诊      基础完整度：85 分                             │
│ 过敏史：青霉素过敏                                                              │
│                                                                                │
│ 【证件】                                                                        │
│ 主证件：身份证 110***********1234（未核验）  [查看全部证件]                     │
│                                                                                │
│ 【联系方式】                                                                    │
│ 手机：138****5678（主，未验证）   邮箱：w***@example.com                        │
│                                                                                │
│ 【地址】                                                                        │
│ 家庭：北京市朝阳区******                                                        │
│                                                                                │
│ 【联系人/监护人】                                                               │
│ 紧急联系人：王小明（子） 139****1234                                            │
│                                                                                │
│ 【授权同意】                                                                    │
│ 隐私政策：已授权 v1.0  2026-10-20   诊疗同意：已授权 v1.0                       │
│ 营销通知：已拒绝      数据共享：未签署                                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 最近业务：门诊 2026-10-20 | 视光 2026-09-12 | 屈光 未就诊                       │
│ [编辑] [证件与联系方式] [地址与联系人] [授权同意] [冻结] [死亡登记] [日志]       │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 P03 新建/编辑患者

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 新建患者                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【必填】                                                                        │
│ 姓名：[王五________]  性别：●男 ○女 ○未知  出生日期：[1980-01-02]               │
│ 证件类型：[身份证 ▼]  证件号：[110101198001021234]  ☐ 无证件                   │
│ 手机号：[13812345678]                                                           │
│ 患者类型：[普通 ▼]    来源：[门诊 ▼]                                            │
│                                                                                │
│ 【选填】                                                                        │
│ 拼音：[wangwu]  民族：[汉族 ▼]  婚姻：[已婚 ▼]  学历：[本科 ▼]  职业：[教师 ▼]   │
│ 过敏史：[青霉素过敏________________________]                                     │
│ 备注：[________________________________________________]                        │
│                                                                                │
│ ⚠ 系统将按“证件类型+证件号”检查是否已建档；若已存在，将提示跳转已有患者。        │
├────────────────────────────────────────────────────────────────────────────────┤
│                                           [取消] [保存并继续补全] [保存]        │
└────────────────────────────────────────────────────────────────────────────────┘
```

**校验：** 姓名必填；性别必填；出生日期不得晚于今天；证件类型与证件号同时填写或同时为空；手机号格式；主证件哈希唯一；证件号掩码展示。

### 5.5 P04 证件与联系方式

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 证件与联系方式：王五（P202610200001）                                           │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【证件】                                                                        │
│ 类型    │证件号掩码          │主证件│核验│来源│操作                         │
│ 身份证  │110***********1234  │是    │否  │门诊│[编辑] [设为主证件] [删除]   │
│ 护照    │E12****89           │否    │是  │导入│[编辑] [设为主证件] [删除]   │
│ [+ 添加证件]                                                                    │
│                                                                                │
│ 【联系方式】                                                                    │
│ 类型  │号码/账号掩码       │主  │验证│来源│操作                              │
│ 手机  │138****5678         │是  │否  │门诊│[编辑] [设为主] [验证] [删除]    │
│ 邮箱  │w***@example.com    │否  │是  │门户│[编辑] [设为主] [删除]            │
│ [+ 添加联系方式]                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

> 查看证件号明文需 `mpi:patient:sensitive` 权限，且触发 M02-05 二次验证，写 M02-06 审计日志。

### 5.6 P05 地址与联系人

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 地址与联系人：王五（P202610200001）                                             │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【地址】                                                                        │
│ 类型  │省市区        │详细地址              │主  │操作                       │
│ 家庭  │北京市/朝阳区 │******                │是  │[编辑] [设为主] [删除]      │
│ 工作  │北京市/海淀区 │******                │否  │[编辑] [设为主] [删除]      │
│ [+ 添加地址]                                                                    │
│                                                                                │
│ 【联系人/监护人】                                                               │
│ 关系  │姓名  │电话掩码     │法定监护人│紧急│操作                              │
│ 子    │王小明│139****1234  │否        │是  │[编辑] [删除]                     │
│ [+ 添加联系人]                                                                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.7 P06 授权同意

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 授权同意：王五（P202610200001）                                                 │
├────────────────────────────────────────────────────────────────────────────────┤
│ 授权类型   │状态    │版本│签署时间          │渠道  │有效期    │操作          │
│ 隐私政策   │已授权  │v1.0│2026-10-20 09:10  │门诊  │长期      │[撤回] [查看] │
│ 诊疗同意   │已授权  │v1.0│2026-10-20 09:10  │门诊  │长期      │[撤回] [查看] │
│ 营销通知   │已拒绝  │v1.0│2026-10-20 09:11  │门诊  │—         │[重新签署]    │
│ 数据共享   │未签署  │—   │—                 │—     │—         │[签署]        │
├────────────────────────────────────────────────────────────────────────────────┤
│ [新增授权]                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.8 P07 患者导入

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 患者导入                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ ① 下载模板 ─── ② 上传文件 ─── ③ 校验预览 ─── ④ 执行                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 模板列：姓名* | 性别* | 出生日期 | 证件类型 | 证件号 | 手机号 | 患者类型 | 来源 │
│                                                                                │
│ 校验结果：总行数 100 | 通过 92 | 警告 5 | 错误 3                                │
│ 错误：行 12 证件号已存在（P202610200001 王五）                                  │
│ 警告：行 35 手机号已存在于其他患者，请核对                                       │
│                                                                                │
│ 错误处理：● 跳过错误行继续  ○ 全部校验通过才导入                                │
│                                      [上一步] [取消] [确认导入(92条)]          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.9 P08 患者变更日志

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 患者变更日志：王五（P202610200001）                                             │
├────────────────────────────────────────────────────────────────────────────────┤
│ 时间                │操作    │操作人│详情                         │IP          │
│ 2026-10-20 09:10:12 │CREATE  │导医01│创建患者主索引               │192.168.1.20│
│ 2026-10-20 09:15:33 │UPDATE  │导医01│补充民族、婚姻               │192.168.1.20│
│ 2026-10-20 09:20:01 │CONSENT │导医01│签署隐私政策 v1.0            │192.168.1.20│
│ 2026-10-20 10:01:44 │FREEZE  │管理员│信息争议，冻结                │192.168.1.10│
│ 2026-10-20 11:20:00 │UNFREEZE│管理员│争议解决，解冻                │192.168.1.10│
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| API-01 | GET | `/api/v1/mpi/patients` | 患者分页列表 | `mpi:patient:list` |
| API-02 | GET | `/api/v1/mpi/patients/{id}` | 患者详情 | `mpi:patient:list` |
| API-03 | POST | `/api/v1/mpi/patients` | 新建患者 | `mpi:patient:create` |
| API-04 | PUT | `/api/v1/mpi/patients/{id}` | 更新患者 | `mpi:patient:update` |
| API-05 | POST | `/api/v1/mpi/patients/{id}/freeze` | 冻结患者 | `mpi:patient:freeze` |
| API-06 | POST | `/api/v1/mpi/patients/{id}/unfreeze` | 解冻患者 | `mpi:patient:freeze` |
| API-07 | POST | `/api/v1/mpi/patients/{id}/mark-deceased` | 死亡登记 | `mpi:patient:update` |
| API-08 | GET | `/api/v1/mpi/patients/statistics` | 患者统计 | `mpi:patient:list` |
| API-09 | GET | `/api/v1/mpi/patients/quick-search` | 患者快速检索 | `mpi:patient:list` |
| API-10 | GET | `/api/v1/mpi/patients/export` | 导出脱敏清单 | `mpi:patient:export` |
| API-11 | GET | `/api/v1/mpi/patients/import-template` | 下载导入模板 | `mpi:patient:import` |
| API-12 | POST | `/api/v1/mpi/patients/import` | 患者导入 | `mpi:patient:import` |
| API-13 | GET | `/api/v1/mpi/patients/import-tasks/{task_id}` | 导入任务详情 | `mpi:patient:import` |
| API-14 | GET | `/api/v1/mpi/patients/{id}/identifiers` | 证件列表 | `mpi:patient:list` |
| API-15 | POST | `/api/v1/mpi/patients/{id}/identifiers` | 添加证件 | `mpi:patient:update` |
| API-16 | PUT | `/api/v1/mpi/patients/{id}/identifiers/{identifier_id}` | 修改证件 | `mpi:patient:update` |
| API-17 | DELETE | `/api/v1/mpi/patients/{id}/identifiers/{identifier_id}` | 删除证件 | `mpi:patient:update` |
| API-18 | GET | `/api/v1/mpi/patients/{id}/contacts` | 联系方式列表 | `mpi:patient:list` |
| API-19 | POST | `/api/v1/mpi/patients/{id}/contacts` | 添加联系方式 | `mpi:patient:update` |
| API-20 | PUT | `/api/v1/mpi/patients/{id}/contacts/{contact_id}` | 修改联系方式 | `mpi:patient:update` |
| API-21 | DELETE | `/api/v1/mpi/patients/{id}/contacts/{contact_id}` | 删除联系方式 | `mpi:patient:update` |
| API-22 | GET | `/api/v1/mpi/patients/{id}/addresses` | 地址列表 | `mpi:patient:list` |
| API-23 | POST | `/api/v1/mpi/patients/{id}/addresses` | 添加地址 | `mpi:patient:update` |
| API-24 | PUT | `/api/v1/mpi/patients/{id}/addresses/{address_id}` | 修改地址 | `mpi:patient:update` |
| API-25 | DELETE | `/api/v1/mpi/patients/{id}/addresses/{address_id}` | 删除地址 | `mpi:patient:update` |
| API-26 | GET | `/api/v1/mpi/patients/{id}/relations` | 联系人列表 | `mpi:patient:list` |
| API-27 | POST | `/api/v1/mpi/patients/{id}/relations` | 添加联系人 | `mpi:patient:update` |
| API-28 | PUT | `/api/v1/mpi/patients/{id}/relations/{relation_id}` | 修改联系人 | `mpi:patient:update` |
| API-29 | DELETE | `/api/v1/mpi/patients/{id}/relations/{relation_id}` | 删除联系人 | `mpi:patient:update` |
| API-30 | GET | `/api/v1/mpi/patients/{id}/consents` | 授权列表 | `mpi:patient:consent` |
| API-31 | POST | `/api/v1/mpi/patients/{id}/consents` | 签署授权 | `mpi:patient:consent` |
| API-32 | POST | `/api/v1/mpi/patients/{id}/consents/{consent_id}/withdraw` | 撤回授权 | `mpi:patient:consent` |
| API-33 | GET | `/api/v1/mpi/patients/{id}/logs` | 变更日志 | `mpi:patient:audit` |
| API-34 | GET | `/api/v1/mpi/patients/me` | 患者端我的信息 | 患者端登录 |
| API-35 | PUT | `/api/v1/mpi/patients/me/contacts` | 患者端更新联系方式 | 患者端登录 |
| API-36 | POST | `/api/v1/mpi/patients/{id}/reveal-id` | 查看证件号明文 | `mpi:patient:sensitive` + MFA |
| API-37 | GET | `/internal/v1/patient/{id}/brief` | 患者简要（内部） | 内部服务 |
| API-38 | GET | `/internal/v1/patient/by-empi/{empi_no}` | 按 EMPI 查患者 | 内部服务 |
| API-39 | GET | `/internal/v1/patient/by-id-hash` | 按证件哈希查患者 | 内部服务 |
| API-40 | POST | `/internal/v1/patient/ensure` | 确保患者存在（供挂号等） | 内部服务 |
| API-41 | GET | `/internal/v1/patient/{id}/primary-contact` | 主联系方式（内部） | 内部服务 |
| API-42 | GET | `/internal/v1/patient/changes` | 增量变更（**故障补推对账**用，非主链路） | 内部服务 |
| API-43 | POST | `/internal/v1/patient/sync/push` | 手动触发全量/指定患者重推 | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码（M03-01：52001~52040）**

| 错误码 | 含义 |
|---|---|
| "0301001" | 患者不存在 |
| "0301002" | 该证件已建档 |
| "0301003" | 证件类型与证件号不匹配 |
| "0301004" | 主证件不能为空时为空 |
| "0301005" | 证件号格式不正确 |
| "0301006" | 手机号格式不正确 |
| "0301007" | 姓名不能为空 |
| "0301008" | 性别不合法 |
| "0301009" | 出生日期不能晚于今天 |
| "0301010" | 患者状态不允许该操作 |
| "0301011" | 患者已冻结 |
| "0301012" | 患者已死亡 |
| "0301013" | 患者已合并，请跳转目标患者 |
| "0301014" | 冻结必须填写原因 |
| "0301015" | 解冻失败 |
| "0301016" | 死亡登记必须填写时间 |
| "0301017" | 证件已被其他患者使用 |
| "0301018" | 主证件已存在 |
| "0301019" | 联系方式已存在 |
| "0301020" | 主联系方式重复 |
| "0301021" | 地址不存在 |
| "0301022" | 联系人不存在 |
| "0301023" | 授权记录不存在 |
| "0301024" | 授权已撤回 |
| "0301025" | 授权版本非法 |
| "0301026" | 导入文件格式错误 |
| "0301027" | 导入行数超限 |
| "0301028" | 导入任务不存在 |
| "0301029" | 导入任务状态不允许 |
| "0301030" | EMPI 号生成失败 |
| "0301031" | 患者端账号未绑定患者 |
| "0301032" | 患者端无权修改该字段 |
| "0301033" | 导出数据量超限 |
| "0301034" | 加密服务不可用 |
| "0301035" | M01 字典服务不可用 |
| "0301036" | M02 权限服务不可用 |
| "0301037" | 数据已变更，请刷新后重试 |
| "0301038" | 并发建档冲突 |
| "0301039" | 证件核验失败 |
| "0301040" | 患者信息不完整 |

### 6.3 关键接口示例

#### API-01 患者分页列表

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 10001,
        "empi_no": "P202610200001",
        "patient_name": "王五",
        "gender": "MALE",
        "birth_date": "1980-01-02",
        "primary_id_type": "ID_CARD",
        "primary_id_mask": "110***********1234",
        "primary_phone_mask": "138****5678",
        "patient_type": "NORMAL",
        "patient_source": "OUTPATIENT",
        "status": "NORMAL",
        "quality_score": 85,
        "last_visit_at": "2026-10-20T09:30:00"
      }
    ],
    "total": 12386,
    "page": 1,
    "page_size": 20,
    "pages": 620
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-03 新建患者

```json
{
  "patient_name": "王五",
  "gender": "MALE",
  "birth_date": "1980-01-02",
  "id_type": "ID_CARD",
  "id_no": "110101198001021234",
  "phone": "13812345678",
  "patient_type": "NORMAL",
  "patient_source": "OUTPATIENT",
  "nation_code": "01",
  "marital_status": "MARRIED",
  "education_code": "BACHELOR",
  "occupation_code": "TEACHER",
  "allergy_history": "青霉素过敏"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10001,
    "empi_no": "P202610200001",
    "patient_name": "王五",
    "status": "NORMAL",
    "quality_score": 85,
    "duplicate_hint": null
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-12 患者导入

```json
{
  "file_url": "https://files.example.com/import/patient_20261020.xlsx",
  "file_name": "patient_20261020.xlsx",
  "error_strategy": "SKIP"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 301,
    "code": "PI202610200001",
    "task_status": "VALIDATING",
    "total_rows": 100
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-36 查看证件号明文

```json
{
  "reason": "核对患者身份，患者本人出示身份证"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10001,
    "id_type": "ID_CARD",
    "id_no_plain": "110101198001021234",
    "expire_in_seconds": 300,
    "audit_id": "AUD20261020112000123"
  },
  "trace_id": "9f8a7b6c"
}
```

> 该接口需 `mpi:patient:sensitive` 权限，且通过 M02-05 二次验证（短信/TOTP），事件写 `sys_audit_log`（`SENSITIVE_VIEW`）。

#### API-37 患者简要（内部）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10001,
    "empi_no": "P202610200001",
    "patient_name": "王五",
    "gender": "MALE",
    "birth_date": "1980-01-02",
    "age": 46,
    "primary_id_type": "ID_CARD",
    "primary_id_mask": "110***********1234",
    "primary_phone_mask": "138****5678",
    "patient_type": "NORMAL",
    "status": "NORMAL",
    "allergy_history": "青霉素过敏",
    "consent_marketing": false,
    "consent_data_share": false
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-40 确保患者存在（内部）

```json
{
  "patient_name": "王五",
  "gender": "MALE",
  "birth_date": "1980-01-02",
  "id_type": "ID_CARD",
  "id_no": "110101198001021234",
  "phone": "13812345678",
  "source": "OUTPATIENT"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10001,
    "empi_no": "P202610200001",
    "created": false,
    "status": "NORMAL",
    "duplicate_hint": "已存在相同证件患者，已直接返回"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-42 增量变更（故障补推对账，非主链路）

> **说明：** 正常链路是 M03 建档后**主动推送**到 M01 `POST /internal/v1/mdm/patients/sync`。本接口仅在推送失败、或需人工核对时使用，由运维/管理员触发分页拉取后重推，**不是 M01 的常规拉取通道**。

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "since_version": 1580,
    "current_version": 2103,
    "total": 523,
    "page": 1,
    "page_size": 500,
    "items": [
      {
        "patient_id": 10001,
        "empi_no": "P202610200001",
        "patient_no": "MZ202610200001",
        "patient_name": "王五",
        "name_pinyin": "wangwu",
        "gender": "MALE",
        "birth_date": "1980-01-02",
        "id_card_no_mask": "110***********1234",
        "id_card_hash": "8f3a...",
        "phone": "13812345678",
        "address": "北京市朝阳区******",
        "patient_type": "NORMAL",
        "allergy_history": "青霉素过敏",
        "status": "NORMAL",
        "sync_version": 2103,
        "updated_at": "2026-10-20T09:15:33"
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-43 手动触发患者重推

**说明：** 推送失败或数据不一致时，由信息科手动触发重推。正常业务链路不调用此接口。

**请求**

```
POST /internal/v1/patient/sync/push
```

```json
{
  "push_scope": "FAILED",
  "patient_ids": [10001, 10024],
  "since_version": null,
  "batch_size": 500,
  "force_overwrite": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| push_scope | STRING | 是 | `FAILED` 仅重推失败记录 / `PATIENTS` 指定患者 / `VERSION` 按版本区间 / `ALL` 全量 |
| patient_ids | ARRAY | 条件 | `push_scope=PATIENTS` 时必填，单次上限 1000 |
| since_version | INT | 条件 | `push_scope=VERSION` 时必填 |
| batch_size | INT | 否 | 每批条数，默认 500，上限 1000 |
| force_overwrite | BOOLEAN | 否 | `true` 时忽略 M01 侧 `sync_version` 比较强制覆盖，默认 `false` |

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "push_task_id": "PSH20261020101533001",
    "push_scope": "FAILED",
    "total": 23,
    "success": 21,
    "failed": 2,
    "failed_items": [
      {
        "patient_id": 10088,
        "empi_no": "P202610200088",
        "retry_count": 3,
        "error_msg": "M01 返回：证件号哈希冲突（同证件已存在其他 EMPI）"
      }
    ],
    "duration_ms": 1842
  },
  "trace_id": "9f8a7b6c"
}
```

### 6.4 FastAPI 路由实现示例

```python
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import PageResult, success_response
from app.core.security import get_current_user, require_permission
from app.schemas.mpi.patient import (
    PatientCreate,
    PatientEnsureRequest,
    PatientQuery,
    PatientUpdate,
    RevealIdRequest,
)
from app.services.mpi.patient_service import PatientService

router = APIRouter(prefix="/api/v1/mpi/patients", tags=["M03-患者主索引"])
internal_router = APIRouter(prefix="/internal/v1/patient", tags=["M03-患者内部接口"])


@router.get("")
async def list_patients(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:list")),
):
    svc = PatientService(db)
    q = PatientQuery(keyword=keyword, status=status, page=page, page_size=page_size)
    items, total = await svc.list_patients(q)
    return success_response(PageResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("")
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:create")),
):
    svc = PatientService(db)
    return success_response(await svc.create(payload, operator=user))


@router.get("/{patient_id}")
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:list")),
):
    svc = PatientService(db)
    return success_response(await svc.get_detail(patient_id))


@router.put("/{patient_id}")
async def update_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:update")),
):
    svc = PatientService(db)
    return success_response(await svc.update(patient_id, payload, operator=user))


@router.post("/{patient_id}/freeze")
async def freeze_patient(
    patient_id: int,
    reason: str = Body(..., embed=True, min_length=5, max_length=500),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:freeze")),
):
    svc = PatientService(db)
    return success_response(await svc.freeze(patient_id, reason, operator=user))


@router.post("/{patient_id}/reveal-id")
async def reveal_patient_id(
    patient_id: int,
    payload: RevealIdRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:patient:sensitive")),
):
    svc = PatientService(db)
    return success_response(await svc.reveal_id(patient_id, payload, operator=user))


@internal_router.get("/{patient_id}/brief")
async def internal_patient_brief(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
):
    svc = PatientService(db)
    return success_response(await svc.get_brief(patient_id))


@internal_router.post("/ensure")
async def internal_ensure_patient(
    payload: PatientEnsureRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = PatientService(db)
    return success_response(await svc.ensure(payload))


@internal_router.get("/changes")
async def internal_patient_changes(
    since_version: int = Query(0, ge=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    svc = PatientService(db)
    return success_response(await svc.get_changes(since_version, page, page_size))
```

### 6.5 Service 层核心逻辑示例

```python
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import encrypt_value, hash_value, mask_value
from app.core.exceptions import BizException
from app.models.mpi.patient import (
    MpiPatient,
    MpiPatientContact,
    MpiPatientIdentifier,
    MpiPatientLog,
    MpiPatientSyncLog,
)
from app.services.mpi.empi_service import EmpiNoService


class PatientService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_patients(self, q):
        stmt = select(MpiPatient).where(MpiPatient.is_deleted == False)
        if q.keyword:
            kw = f"%{q.keyword}%"
            conditions = [
                MpiPatient.empi_no.ilike(kw),
                MpiPatient.patient_name.ilike(kw),
                MpiPatient.name_pinyin.ilike(kw),
            ]
            if q.keyword.isdigit() and len(q.keyword) >= 6:
                conditions.append(MpiPatient.primary_phone_hash == hash_value(q.keyword))
            stmt = stmt.where(or_(*conditions))
        if q.status:
            stmt = stmt.where(MpiPatient.status == q.status)
        total = (await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        rows = (await self.db.execute(
            stmt.order_by(MpiPatient.created_at.desc())
            .offset((q.page - 1) * q.page_size)
            .limit(q.page_size)
        )).scalars().all()
        return [self._to_list_item(row) for row in rows], total

    async def create(self, payload, operator=None):
        id_hash = hash_value(payload.id_no) if payload.id_no else None
        if id_hash:
            exist = (await self.db.execute(
                select(MpiPatient).where(
                    MpiPatient.primary_id_no_hash == id_hash,
                    MpiPatient.is_deleted == False,
                )
            )).scalar_one_or_none()
            if exist:
                raise BizException("0301002", "该证件已建档", data={
                    "patient_id": exist.id,
                    "empi_no": exist.empi_no,
                })

        empi_no = await EmpiNoService(self.db).next_no()
        patient = MpiPatient(
            empi_no=empi_no,
            patient_name=payload.patient_name.strip(),
            name_pinyin=payload.name_pinyin,
            gender=payload.gender,
            birth_date=payload.birth_date,
            primary_id_type=payload.id_type,
            primary_id_no_enc=encrypt_value(payload.id_no) if payload.id_no else None,
            primary_id_no_hash=id_hash,
            primary_id_no_mask=mask_value(payload.id_no) if payload.id_no else None,
            primary_phone_enc=encrypt_value(payload.phone) if payload.phone else None,
            primary_phone_hash=hash_value(payload.phone) if payload.phone else None,
            primary_phone_mask=mask_value(payload.phone) if payload.phone else None,
            patient_type=payload.patient_type,
            patient_source=payload.patient_source,
            nation_code=payload.nation_code,
            marital_status=payload.marital_status,
            education_code=payload.education_code,
            occupation_code=payload.occupation_code,
            allergy_history=payload.allergy_history,
            status="NORMAL",
            quality_score=self._score(payload),
            created_by=getattr(operator, "id", None),
        )
        self.db.add(patient)
        await self.db.flush()

        if payload.id_no:
            self.db.add(MpiPatientIdentifier(
                patient_id=patient.id,
                id_type=payload.id_type,
                id_no_enc=encrypt_value(payload.id_no),
                id_no_hash=id_hash,
                id_no_mask=mask_value(payload.id_no),
                is_primary=True,
                verified=False,
                source=payload.patient_source,
                status="ACTIVE",
            ))
        if payload.phone:
            self.db.add(MpiPatientContact(
                patient_id=patient.id,
                contact_type="MOBILE",
                contact_value_enc=encrypt_value(payload.phone),
                contact_value_hash=hash_value(payload.phone),
                contact_value_mask=mask_value(payload.phone),
                is_primary=True,
                is_verified=False,
                source=payload.patient_source,
                status="ACTIVE",
            ))
        self.db.add(MpiPatientLog(
            patient_id=patient.id,
            empi_no=patient.empi_no,
            action="CREATE",
            detail="创建患者主索引",
            operator_id=getattr(operator, "id", None),
            operator_name=getattr(operator, "name", None),
        ))
        self.db.add(MpiPatientSyncLog(
            patient_id=patient.id,
            empi_no=patient.empi_no,
            sync_action="CREATE",
            sync_version=1,
            target_system="M01",
        ))
        await self.db.commit()
        return {
            "id": patient.id,
            "empi_no": patient.empi_no,
            "patient_name": patient.patient_name,
            "status": patient.status,
            "quality_score": patient.quality_score,
            "duplicate_hint": None,
        }

    async def ensure(self, payload):
        id_hash = hash_value(payload.id_no) if payload.id_no else None
        if id_hash:
            exist = (await self.db.execute(
                select(MpiPatient).where(
                    MpiPatient.primary_id_no_hash == id_hash,
                    MpiPatient.is_deleted == False,
                )
            )).scalar_one_or_none()
            if exist:
                return {
                    "patient_id": exist.id,
                    "empi_no": exist.empi_no,
                    "created": False,
                    "status": exist.status,
                    "duplicate_hint": "已存在相同证件患者，已直接返回",
                }
        create_payload = PatientCreate(
            patient_name=payload.patient_name,
            gender=payload.gender,
            birth_date=payload.birth_date,
            id_type=payload.id_type,
            id_no=payload.id_no,
            phone=payload.phone,
            patient_type="NORMAL",
            patient_source=payload.source or "OUTPATIENT",
        )
        created = await self.create(create_payload)
        return {
            "patient_id": created["id"],
            "empi_no": created["empi_no"],
            "created": True,
            "status": created["status"],
            "duplicate_hint": None,
        }

    async def get_brief(self, patient_id: int):
        patient = (await self.db.execute(
            select(MpiPatient).where(
                MpiPatient.id == patient_id,
                MpiPatient.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not patient:
            raise BizException("0301001", "患者不存在")
        age = None
        if patient.birth_date:
            today = date.today()
            age = today.year - patient.birth_date.year - (
                (today.month, today.day) < (patient.birth_date.month, patient.birth_date.day)
            )
        return {
            "patient_id": patient.id,
            "empi_no": patient.empi_no,
            "patient_name": patient.patient_name,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "age": age,
            "primary_id_type": patient.primary_id_type,
            "primary_id_mask": patient.primary_id_no_mask,
            "primary_phone_mask": patient.primary_phone_mask,
            "patient_type": patient.patient_type,
            "status": patient.status,
            "allergy_history": patient.allergy_history,
            "consent_marketing": False,
            "consent_data_share": False,
        }

    async def get_changes(self, since_version: int, page: int, page_size: int):
        stmt = (
            select(MpiPatient)
            .where(
                MpiPatient.sync_version > since_version,
                MpiPatient.is_deleted == False,
            )
            .order_by(MpiPatient.sync_version.asc())
        )
        total = (await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        rows = (await self.db.execute(
            stmt.offset((page - 1) * page_size).limit(page_size)
        )).scalars().all()
        current_version = rows[-1].sync_version if rows else since_version
        return {
            "since_version": since_version,
            "current_version": current_version,
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._to_sync_item(r) for r in rows],
        }

    @staticmethod
    def _score(payload) -> int:
        score = 0
        if payload.patient_name:
            score += 20
        if payload.gender:
            score += 10
        if payload.birth_date:
            score += 15
        if payload.id_no:
            score += 25
        if payload.phone:
            score += 20
        if payload.nation_code:
            score += 5
        if payload.marital_status:
            score += 5
        return min(score, 100)

    @staticmethod
    def _to_list_item(row):
        return {
            "id": row.id,
            "empi_no": row.empi_no,
            "patient_name": row.patient_name,
            "gender": row.gender,
            "birth_date": row.birth_date.isoformat() if row.birth_date else None,
            "primary_id_type": row.primary_id_type,
            "primary_id_mask": row.primary_id_no_mask,
            "primary_phone_mask": row.primary_phone_mask,
            "patient_type": row.patient_type,
            "patient_source": row.patient_source,
            "status": row.status,
            "quality_score": row.quality_score,
            "last_visit_at": row.last_visit_at.isoformat() if row.last_visit_at else None,
        }

    @staticmethod
    def _to_sync_item(row):
        return {
            "patient_id": row.id,
            "empi_no": row.empi_no,
            "patient_no": row.patient_no,
            "patient_name": row.patient_name,
            "name_pinyin": row.name_pinyin,
            "gender": row.gender,
            "birth_date": row.birth_date.isoformat() if row.birth_date else None,
            "id_card_no_mask": row.primary_id_no_mask,
            "id_card_hash": row.primary_id_no_hash,
            "phone": row.primary_phone_mask,
            "address": None,
            "patient_type": row.patient_type,
            "allergy_history": row.allergy_history,
            "status": row.status,
            "sync_version": row.sync_version,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
```

```python
# app/services/mpi/sync_service.py
"""患者数据推送服务（M03 → M01 单向推送）

架构约定：
  · mpi_patient 是全院患者身份的**唯一主表与唯一写入方**
  · M01 的 md_patient 是 M01 侧只读镜像，只能由本服务推送更新
  · 推送入口：POST /internal/v1/mdm/patients/sync（M01 提供）
  · 失败重试：指数退避，最多 5 次
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mpi.patient import MpiPatient, MpiPatientSyncLog
from app.core.config import settings


class PatientSyncService:
    """患者推送服务"""

    MAX_RETRY = 5
    BATCH_SIZE = 500
    PUSH_URL = f"{settings.MDM_BASE_URL}/internal/v1/mdm/patients/sync"

    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------- 入队 ----------
    async def enqueue_sync(self, patient: MpiPatient,
                            action: str) -> MpiPatientSyncLog:
        """建档/修改/合并后调用：写同步日志，由异步任务投递"""
        log = MpiPatientSyncLog(
            patient_id=patient.id,
            empi_no=patient.empi_no,
            sync_action=action,                 # CREATE / UPDATE / DELETE
            sync_version=patient.sync_version,
            target_system="M01",
            payload_json=self._build_payload(patient),
            sync_status="PENDING",
            retry_count=0,
        )
        self.db.add(log)
        await self.db.flush()
        return log

    @staticmethod
    def _build_payload(patient: MpiPatient) -> dict:
        """构造推送载荷（字段与 M01 API-47 对齐）"""
        return {
            "empi_id": patient.empi_no,          # M01 侧字段名
            "patient_no": patient.patient_no,
            "name": patient.patient_name,
            "pinyin_code": patient.name_pinyin,
            "pinyin_short": patient.name_pinyin_short,
            "gender": patient.gender,
            "birth_date": patient.birth_date.isoformat() if patient.birth_date else None,
            "age": patient.age,
            "id_card_no_mask": patient.primary_id_no_mask,
            "id_card_hash": patient.primary_id_no_hash,
            "phone": patient.phone,
            "patient_type": patient.patient_type,
            "member_level": patient.member_level,
            "allergy_history": patient.allergy_history,
            "sync_version": patient.sync_version,
        }

    # ---------- 投递 ----------
    async def push_batch(self, log_ids: List[int]) -> dict:
        """批量推送（由 Celery 任务调用）"""
        logs = (await self.db.execute(
            select(MpiPatientSyncLog).where(
                MpiPatientSyncLog.id.in_(log_ids),
                MpiPatientSyncLog.sync_status.in_(("PENDING", "FAILED")),
            )
        )).scalars().all()

        if not logs:
            return {"total": 0, "success": 0, "failed": 0}

        # 同患者只推最新版本，避免乱序
        latest: dict = {}
        for log in logs:
            key = log.patient_id
            if key not in latest or log.sync_version > latest[key].sync_version:
                latest[key] = log

        patients = [log.payload_json for log in latest.values()]
        actions = {log.patient_id: log.sync_action for log in latest.values()}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.PUSH_URL,
                    json={
                        "sync_mode": "BATCH",
                        "action": "UPSERT",
                        "patients": patients,
                    },
                    headers={"X-Service-Token": settings.INTERNAL_TOKEN},
                )
                resp.raise_for_status()
                result = resp.json()

            if result.get("code") != 0:
                raise RuntimeError(f"M01 返回错误：{result.get('message')}")

            # 成功
            now = datetime.now()
            for log in logs:
                log.sync_status = "SUCCESS"
                log.delivered_at = now
                log.error_msg = None

        except Exception as e:
            # 失败：累加重试次数，超过上限标记终态
            now = datetime.now()
            for log in logs:
                log.retry_count += 1
                log.error_msg = str(e)[:1000]
                if log.retry_count >= self.MAX_RETRY:
                    log.sync_status = "FAILED"
                else:
                    log.sync_status = "PENDING"
                    # 指数退避：2^n 分钟后可重试
                    log.delivered_at = now + timedelta(
                        minutes=2 ** log.retry_count)

            await self.db.commit()
            return {
                "total": len(logs),
                "success": 0,
                "failed": len(logs),
                "error": str(e)[:200],
            }

        await self.db.commit()
        return {"total": len(logs), "success": len(logs), "failed": 0}

    # ---------- 补偿 ----------
    async def retry_failed(self, limit: int = 1000) -> dict:
        """重推失败记录（定时任务调用）"""
        now = datetime.now()
        logs = (await self.db.execute(
            select(MpiPatientSyncLog).where(
                and_(
                    MpiPatientSyncLog.sync_status.in_(("PENDING", "FAILED")),
                    MpiPatientSyncLog.retry_count < self.MAX_RETRY,
                    MpiPatientSyncLog.delivered_at <= now,
                )
            ).limit(limit)
        )).scalars().all()

        if not logs:
            return {"retried": 0}

        return await self.push_batch([log.id for log in logs])

    async def reconcile(self, since_version: int,
                          page_size: int = 500) -> dict:
        """对账：拉本模块增量，对比 M01 侧版本，不一致则重推"""
        from app.clients.mdm_client import MdmClient

        client = MdmClient()
        mismatch = []

        offset = 0
        while True:
            rows = (await self.db.execute(
                select(MpiPatient).where(
                    MpiPatient.sync_version > since_version,
                    MpiPatient.is_deleted == False,
                ).order_by(MpiPatient.sync_version.asc())
                .offset(offset).limit(page_size)
            )).scalars().all()

            if not rows:
                break

            remote = await client.batch_get_patients(
                [r.empi_no for r in rows])

            for local in rows:
                r = remote.get(local.empi_no)
                if not r or r.get("sync_version", 0) < local.sync_version:
                    mismatch.append(local.id)

            offset += page_size

        if mismatch:
            await self.enqueue_reconcile(mismatch)

        return {
            "checked": offset,
            "mismatch": len(mismatch),
            "requeued": len(mismatch),
        }

    async def enqueue_reconcile(self, patient_ids: List[int]) -> None:
        """对账发现差异后重新入队"""
        patients = (await self.db.execute(
            select(MpiPatient).where(MpiPatient.id.in_(patient_ids))
        )).scalars().all()

        for p in patients:
            await self.enqueue_sync(p, "UPDATE")

        await self.db.commit()
```

**推送时序说明：**

```
业务事务（建档/修改）
   ├─ 写 mpi_patient（sync_version +1）
   ├─ 写 mpi_patient_log
   └─ 写 mpi_patient_sync_log（PENDING）
        ↓ 事务提交后发 Celery 任务
PatientSyncService.push_batch()
   ├─ 成功 → sync_status = SUCCESS
   └─ 失败 → retry_count +1，指数退避重试（2/4/8/16 分钟）
              ≥5 次 → FAILED（人工介入，走 API-43）
        ↓
每 10 分钟兜底任务 retry_failed() 扫一遍未成功的记录
        ↓
每日 03:00 对账任务 reconcile() 比对版本，差异自动重推
```

> **关键设计：** 推送与业务事务解耦。业务事务只负责落 `sync_log`（PENDING），推送在事务提交后异步进行；即使 M01 不可用也不影响建档，恢复后自动补推。

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `mpi:patient:{id}` | String(JSON) | 30min | 患者简要缓存 | 患者变更 |
| `mpi:patient:empi:{empi_no}` | String(整数) | 30min | EMPI→ID | 患者变更 |
| `mpi:patient:idhash:{type}:{hash}` | String(整数) | 30min | 证件→患者 ID | 证件变更 |
| `mpi:patient:phonehash:{hash}` | Set(整数) | 30min | 手机号→患者 ID 集合 | 联系方式变更 |
| `mpi:patient:stats` | String(JSON) | 5min | 统计卡片 | 定时刷新 |
| `mpi:empi:seq:{yyyyMMdd}` | String | 2d | 当日 EMPI 流水 | 自然过期 |
| `mpi:import:lock` | String | 30s | 导入互斥 | 主动释放 |
| `mpi:patient:version:{id}` | String | 30min | 版本号 | 更新递增 |

### 7.2 Celery 异步任务

```python
from celery import shared_task


@shared_task
def cleanup_patient_import_detail_task():
    import asyncio
    return asyncio.run(_cleanup_import_detail())


async def _cleanup_import_detail():
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.patient import MpiPatientImportDetail

    async with AsyncSessionLocal() as db:
        threshold = datetime.now() - timedelta(days=30)
        result = await db.execute(
            delete(MpiPatientImportDetail).where(
                MpiPatientImportDetail.created_at < threshold
            )
        )
        await db.commit()
        return {"deleted": result.rowcount or 0}


@shared_task
def refresh_patient_stats_task():
    import asyncio
    return asyncio.run(_refresh_stats())


async def _refresh_stats():
    from sqlalchemy import func, select
    from app.core.database import AsyncSessionLocal
    from app.core.redis import redis_client
    from app.models.mpi.patient import MpiPatient

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(MpiPatient.status, func.count())
            .where(MpiPatient.is_deleted == False)
            .group_by(MpiPatient.status)
        )).all()
        data = {status: count for status, count in rows}
        import json
        await redis_client.setex("mpi:patient:stats", 300, json.dumps(data))
        return data
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_patient_stats_refresh` | `*/10 * * * *` | 刷新患者统计缓存 |
| `job_patient_log_partition` | `0 1 1 * *` | 创建患者日志下月分区 |
| `job_patient_import_cleanup` | `0 3 * * *` | 清理 30 天前导入明细 |
| `job_patient_sync_version_bump` | `*/5 * * * *` | 批量递增 sync_version（减少锁竞争） |
| `job_patient_quality_rescore` | `0 4 * * *` | 基础完整度重算 |

---

## 8. 业务规则与校验

### 8.1 建档规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 姓名必填 | 去空格后非空 | 52007 |
| 性别合法 | MALE/FEMALE/UNKNOWN | 52008 |
| 出生日期 | 不得晚于今天 | 52009 |
| 证件类型+号 | 同时为空或同时填写 | 52003 |
| 主证件唯一 | 类型+哈希部分唯一 | 52002 |
| EMPI 唯一 | `empi_no` 唯一 | 52030 |
| 手机号格式 | 中国大陆手机正则 | 52006 |
| 无证件患者 | 姓名+性别+出生日期+手机号至少两项 | 52040 |

### 8.2 状态规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| FROZEN 可查看不可业务引用 | 业务侧需提示 | 52011 |
| DECEASED 不可新建业务 | 仅历史查看 | 52012 |
| MERGED 只读 | 跳转 `merge_to_id` | 52013 |
| 冻结必填原因 | ≥5 字 | 52014 |
| 死亡登记必填时间 | — | 52016 |
| 合并/拆分 | 仅 M03-02 可操作 | 52010 |

### 8.3 证件与联系方式规则

| 规则 | 说明 |
|---|---|
| 证件号加密 | `id_no_enc` AES-256 |
| 检索哈希 | `id_no_hash` SHA-256 + 盐 |
| 展示掩码 | 身份证保留前 3 后 4 |
| 主证件唯一 | 每患者仅一个 `is_primary=true` 有效证件 |
| 主联系方式 | 每患者每类型仅一个主联系方式 |
| 手机号可重复 | 家属共用，命中提示不阻断 |

### 8.4 授权规则

| 规则 | 说明 |
|---|---|
| 营销授权默认拒绝 | 未签署视为拒绝 |
| 撤回不删除 | 新增 WITHDRAWN 记录 |
| 版本必填 | `consent_version` |
| 数据共享需单独签署 | 不随隐私政策默认勾选 |

### 8.5 并发控制

| 机制 | 说明 |
|---|---|
| 证件唯一约束 | DB 部分唯一索引兜底 |
| EMPI 流水 | Redis INCR + DB 唯一重试 |
| 乐观锁 | `version_no` |
| 导入互斥 | Redis `mpi:import:lock` |
| 幂等 ensure | 证件哈希命中直接返回 |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `mpi:patient:list` | 查看列表/详情/快速检索 | 导医、收费、医生、护士、客服 |
| `mpi:patient:create` | 新建患者 | 导医、客服、收费 |
| `mpi:patient:update` | 编辑、证件、联系方式、地址、联系人 | 导医、客服、信息科 |
| `mpi:patient:freeze` | 冻结/解冻 | 信息科、管理员 |
| `mpi:patient:export` | 导出脱敏清单 | 信息科 |
| `mpi:patient:import` | 导入 | 信息科 |
| `mpi:patient:consent` | 授权签署/撤回 | 导医、客服、护士 |
| `mpi:patient:audit` | 变更日志 | 审计员、信息科 |
| `mpi:patient:sensitive` | 查看证件号明文 | 信息科、管理员（需 MFA） |

### 9.2 权限矩阵

`●` 完全控制 `○` 可操作 `△` 只读 `—` 无权限

| 功能 | 系统管理员 | 信息科 | 导医/客服 | 收费员 | 医生 | 护士 | 审计员 | 患者本人 |
|---|---|---|---|---|---|---|---|---|
| 患者列表 | ● | ● | ● | △ | △ | △ | △ | — |
| 新建患者 | ● | ● | ● | ○ | — | — | — | ○(门户) |
| 编辑主档 | ● | ● | ○ | — | — | — | — | — |
| 证件/联系方式 | ● | ● | ○ | — | — | △ | — | ○(本人联系方式) |
| 冻结/解冻 | ● | ● | — | — | — | — | — | — |
| 授权同意 | ● | ● | ○ | — | △ | ○ | △ | ○ |
| 导入/导出 | ● | ● | — | — | — | — | — | — |
| 变更日志 | ● | ● | — | — | — | — | ● | — |
| 查看证件明文 | ● | ● | — | — | — | — | — | — |

### 9.3 数据权限与脱敏

| 项 | 规则 |
|---|---|
| 证件号 | 所有页面默认掩码；查看明文需 `mpi:patient:sensitive` + M02-05 二次验证 + `sys_audit_log` 审计 |
| 手机号 | 默认掩码；本人患者端可看完整 |
| 导出 | 证件号/手机号脱敏 |
| 跨科室 | 患者全院共享，但敏感字段按角色控制 |
| 内部接口 | 不返回完整证件号/手机号，只返回掩码 |
| 患者端 | 只能访问本人 `patient_id` 绑定记录 |

### 9.4 安全措施

- 证件号、手机号、联系人电话 **AES-256 加密存储**。
- 检索使用 **SHA-256 哈希 + 盐**，不可逆。
- 明文不写日志、不返前端、不进缓存。
- 敏感字段查看写 `sys_audit_log`（`SENSITIVE_VIEW`）。
- 导出需二次确认并记录操作人。
- 患者端 Token 与 `patient_id` 绑定，越权返回 403。
- 内部接口使用服务令牌，禁止公网暴露。

---

## 10. 主数据分发与集成

### 10.1 分发目标

| 目标 | 分发内容 | 触发时机 | 方式 |
|---|---|---|---|
| M01 患者同步表 | 患者简要、EMPI、证件哈希、手机号掩码 | 建档/更新/冻结/死亡 | 事件 + 内部接口 |
| M03-02 | 患者主档、证件哈希、联系方式哈希 | 建档/更新 | 事件 + 内部接口 |
| M03-03 会员 | `patient_id`、`empi_no`、姓名、手机掩码 | 建档/更新 | 事件 |
| M03-04 随访模板 | `patient_id`、`empi_no` | 建档 | 内部接口 |
| M03-05 消息 | 患者联系方式（脱敏/加密） | 发送时 | 内部接口 |
| M03-06 门户 | 患者简要、授权状态 | 登录/查询 | 内部接口 |
| M04 门诊 | 患者简要、状态、过敏史 | 挂号/就诊 | 内部接口 |
| M05 住院 | 患者简要 | 入院 | 内部接口 |
| M10 视光 | 患者简要、会员标识 | 验光/配镜 | 内部接口 |
| M11 屈光 | 患者简要 | 咨询/术前 | 内部接口 |
| M12/M13 | 患者简要 | 申请/报告 | 内部接口 |
| M16 收费 | 患者简要、状态 | 收费 | 内部接口 |
| M19 随访执行/会员运营 | 患者简要、授权 | 随访/营销 | 事件 + 内部接口 |

### 10.2 事件清单

| 事件类型 | 触发时机 | 载荷 |
|---|---|---|
| `mpi.patient.created` | 建档 | patient_id, empi_no, patient_name, gender, birth_date, status |
| `mpi.patient.updated` | 主档更新 | patient_id, empi_no, changed_fields |
| `mpi.patient.frozen` | 冻结 | patient_id, reason |
| `mpi.patient.unfrozen` | 解冻 | patient_id |
| `mpi.patient.deceased` | 死亡登记 | patient_id, deceased_at |
| `mpi.patient.merged` | M03-02 合并 | source_patient_id, target_patient_id |
| `mpi.patient.consent_changed` | 授权变更 | patient_id, consent_type, status, version |
| `mpi.patient.contact_changed` | 联系方式变更 | patient_id, contact_type, mask |

### 10.3 内部契约

| 接口 | 用途 | 调用方 | SLA |
|---|---|---|---|
| `GET /internal/v1/patient/{id}/brief` | 患者简要 | 全院业务 | P95 ≤ 50ms |
| `GET /internal/v1/patient/by-empi/{empi_no}` | 按 EMPI 查 | 全院业务 | P95 ≤ 30ms |
| `GET /internal/v1/patient/by-id-hash` | 按证件哈希查 | M04/M16/M03-02 | P95 ≤ 50ms |
| `POST /internal/v1/patient/ensure` | 确保患者存在 | M04 挂号、M10 视光 | P95 ≤ 200ms |
| `GET /internal/v1/patient/{id}/primary-contact` | 主联系方式 | M03-05/M19 | P95 ≤ 30ms |
| `GET /internal/v1/patient/changes` | 增量变更 | M01 同步 | P95 ≤ 200ms |

**约定：** 内部接口不返回完整证件号/手机号；如需加密值，走独立高权限接口并审计。

### 10.4 M01/M02 联动

| 场景 | 联动 |
|---|---|
| M01 字典变更 | 订阅 `mdm.dict.changed`，刷新本地枚举缓存 |
| M01 职工停用 | 操作人历史保留，账号由 M02 处理 |
| M02 权限变更 | 实时生效，无需本模块缓存权限 |
| M02 审计 | 本模块敏感访问事件推送 `sys_audit_log` |
| M02 二次验证 | 查看证件明文前调用 `sys_mfa_challenge` |

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| 参数异常 | 姓名空、手机号格式 | 40001 + 字段错误 |
| 业务异常 | 证件已建档、状态不允许 | 520xx |
| 并发异常 | 唯一约束冲突 | 重试或 52038 |
| 依赖异常 | 加密服务/M01 字典不可用 | 降级或提示 |
| 系统异常 | DB 失败 | 50000 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| 加密服务 | 禁止写入敏感字段，提示稍后重试 |
| M01 字典 | 使用本地缓存，缓存无则只允许基础字段 |
| M20 短信 | 导入成功但不发通知，记录 `sms_sent=false` |
| Redis | 直连 DB，EMPI 流水改用 DB 序列兜底 |
| M02 权限 | 拒绝访问，不降级放行 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-10-20T09:10:12.123+08:00",
  "level": "INFO",
  "logger": "app.services.mpi.patient_service",
  "trace_id": "3f2a1b9c",
  "action": "PATIENT_CREATE",
  "patient_id": 10001,
  "empi_no": "P202610200001",
  "operator_id": 1,
  "operator_name": "导医01",
  "ip": "192.168.1.20",
  "result": "SUCCESS"
}
```

**禁止记录：** 完整证件号、完整手机号、加密密钥、明文授权证据内容。

### 11.3 监控指标

| 指标 | 告警阈值 |
|---|---|
| 接口错误率 | >1% |
| 患者简要 P95 | >50ms |
| ensure P95 | >200ms |
| 每日新建患者数 | 异常突增 >300% |
| 证件重复拦截数 | 突增 |
| 导入失败率 | >10% |
| 敏感字段查看次数 | 异常突增 |
| 冻结患者数 | >20 |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 新建患者 | 成功，生成 EMPI |
| AC-02 | EMPI 唯一 | 并发建号不重复 |
| AC-03 | 主证件唯一 | 同证件二次建档返回 "0301002" |
| AC-04 | 证件类型+号同时为空/填写 | 校验通过 |
| AC-05 | 姓名必填 | 空返回 "0301007" |
| AC-06 | 性别合法 | 非法返回 "0301008" |
| AC-07 | 出生日期未来 | 返回 "0301009" |
| AC-08 | 手机号格式 | 非法返回 "0301006" |
| AC-09 | 无证件患者 | 满足两项可保存 |
| AC-10 | 证件加密存储 | DB 无明文 |
| AC-11 | 证件哈希检索 | 可按哈希命中 |
| AC-12 | 证件掩码展示 | 列表/详情掩码 |
| AC-13 | 手机号加密存储 | DB 无明文 |
| AC-14 | 手机号可重复 | 命中提示不阻断 |
| AC-15 | 主联系方式唯一 | 同类型仅一个主 |
| AC-16 | 多证件 | 可添加护照等 |
| AC-17 | 设为主证件 | 旧主证件自动取消 |
| AC-18 | 删除证件 | 逻辑删除，日志留痕 |
| AC-19 | 地址新增/编辑/删除 | 成功 |
| AC-20 | 联系人新增/编辑/删除 | 成功 |
| AC-21 | 法定监护人 | 可标记 |
| AC-22 | 授权签署 | 成功，版本记录 |
| AC-23 | 授权撤回 | 新增 WITHDRAWN，不删历史 |
| AC-24 | 营销默认拒绝 | 未签署返回 false |
| AC-25 | 冻结 | 填原因成功，状态 FROZEN |
| AC-26 | 冻结必填原因 | 空返回 "0301014" |
| AC-27 | 解冻 | 成功回 NORMAL |
| AC-28 | 死亡登记 | 状态 DECEASED |
| AC-29 | MERGED 只读 | 编辑返回 "0301013" |
| AC-30 | 快速检索 | 姓名/EMPI/手机号哈希命中 |
| AC-31 | 患者详情 | 展示主档、证件、联系方式、授权 |
| AC-32 | 变更日志 | 全量留痕 |
| AC-33 | 导入模板 | 可下载 |
| AC-34 | 导入校验 | 错误行号准确 |
| AC-35 | 导入执行 | 成功生成患者 |
| AC-36 | 导入任务查询 | 状态/明细可查 |
| AC-37 | 导出脱敏 | 证件/手机号掩码 |
| AC-38 | 患者端我的信息 | 仅本人 |
| AC-39 | 患者端更新联系方式 | 仅本人联系方式 |
| AC-40 | 内部简要接口 | 返回掩码，不返明文 |
| AC-41 | ensure 幂等 | 同证件返回已有 |
| AC-42 | 权限控制 | 无权限 403 |
| AC-43 | 查看证件明文 | 需 MFA + 审计 |
| AC-44 | 字典校验 | 非法枚举拒绝 |
| AC-45 | 乐观锁 | 版本冲突返回 "0301037" |
| AC-46 | 导入互斥 | 并发导入第二个被拒 |
| AC-47 | 日志分区 | 月度分区创建 |
| AC-48 | 统计缓存 | 5 分钟内可接受 |
| AC-49 | M03-02 合并预留 | 字段可写，接口不实现合并 |
| AC-50 | M01 同步接口 | 按 sync_version 增量返回 |
| AC-51 | 数据脱敏导出 | 无明文 |
| AC-52 | 事件发布 | 建档后 M01/M04 收到事件 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | 患者列表 | 50 并发 P95 ≤ 500ms |
| PF-02 | 患者详情 | 50 并发 P95 ≤ 200ms |
| PF-03 | 快速检索 | 100 并发 P95 ≤ 200ms |
| PF-04 | 患者简要内部接口 | 500 并发 P95 ≤ 50ms |
| PF-05 | 新建患者 | 50 并发 P95 ≤ 300ms |
| PF-06 | ensure | 100 并发 P95 ≤ 200ms |
| PF-07 | 导入 500 行 | ≤ 30s |
| PF-08 | 增量同步 500 条 | P95 ≤ 200ms |
| PF-09 | 长稳 72h | 无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | EMPI 唯一率 | 100% |
| DA-02 | 主证件哈希唯一 | 100% |
| DA-03 | 敏感字段加密率 | 100% |
| DA-04 | 建档日志留痕 | 100% |
| DA-05 | 授权版本完整 | 100% |
| DA-06 | 导入错误可定位 | 100% |
| DA-07 | 同步日志完整 | 100% |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | 明文证件号泄漏 | 0 处 |
| SC-02 | 明文手机号泄漏 | 0 处 |
| SC-03 | 未授权查看敏感字段 | 403 + 审计 |
| SC-04 | 患者端越权 | 403 |
| SC-05 | 内部接口公网暴露 | 禁止 |
| SC-06 | 导出脱敏 | 通过 |
| SC-07 | 加密算法 | AES-256 |
| SC-08 | 哈希算法 | SHA-256 + 盐 |
| SC-09 | 敏感查看二次验证 | 必须通过 M02-05 |

---

## 附录 A：患者状态流转表

| 当前 | 操作 | 目标 | 触发方 | 是否留痕 |
|---|---|---|---|---|
| NORMAL | 冻结 | FROZEN | 管理员 | 是 |
| FROZEN | 解冻 | NORMAL | 管理员 | 是 |
| NORMAL/FROZEN | 死亡登记 | DECEASED | 管理员/护士 | 是 |
| NORMAL | 合并 | MERGED | M03-02 | 是 |
| MERGED | 拆分 | NORMAL | M03-02 | 是 |

## 附录 B：证件类型字典（M01 `md_dict_type` = `ID_TYPE`）

| 代码 | 名称 |
|---|---|
| `ID_CARD` | 居民身份证 |
| `PASSPORT` | 护照 |
| `HK_MO_TW` | 港澳台通行证 |
| `MILITARY` | 军官证 |
| `BIRTH_CERT` | 出生医学证明 |
| `GUARDIAN_ID` | 监护人证件 |
| `NO_ID` | 无证件 |

## 附录 C：授权类型与状态字典（M01 `md_dict_type` = `CONSENT_TYPE` / `CONSENT_STATUS`）

| 类型代码 | 名称 | 默认 |
|---|---|---|
| `PRIVACY` | 隐私政策 | 需签署 |
| `TREATMENT` | 诊疗同意 | 需签署 |
| `MARKETING` | 营销通知 | 默认拒绝 |
| `DATA_SHARE` | 数据共享 | 单独签署 |

| 状态代码 | 名称 |
|---|---|
| `GRANTED` | 已授权 |
| `REFUSED` | 已拒绝 |
| `WITHDRAWN` | 已撤回 |

## 附录 D：系统参数（M01 `md_sys_param`）

| 参数编码 | 默认值 | 说明 |
|---|---|---|
| `MPI.EMPI.PREFIX` | `P` | EMPI 前缀 |
| `MPI.EMPI.DAILY_SEQ_LEN` | `6` | 日流水长度 |
| `MPI.IMPORT.MAX_ROWS` | `500` | 导入最大行数 |
| `MPI.EXPORT.MAX_ROWS` | `5000` | 导出最大行数 |
| `MPI.SENSITIVE.VIEW_AUDIT` | `true` | 敏感查看审计 |
| `MPI.PATIENT.MIN_QUALITY_SCORE` | `60` | 最低完整度提醒 |
| `MPI.CONSENT.MARKETING_DEFAULT` | `REFUSED` | 营销默认拒绝 |
| `MPI.LOG.RETAIN_YEARS` | `5` | 日志保留年数 |
| `MPI.SYNC.BATCH_SIZE` | `500` | 同步批次大小 |

## 附录 E：术语表

| 术语 | 说明 |
|---|---|
| EMPI | 企业级患者主索引 |
| 患者主档 | 患者身份核心信息 |
| 主证件 | 用于唯一识别患者的主要证件 |
| 证件哈希 | 用于检索的不可逆摘要 |
| 掩码 | 脱敏展示形式 |
| 授权同意 | 患者对隐私、诊疗、营销、共享的授权 |
| 冻结 | 临时禁止业务引用 |
| 合并 | M03-02 将重复患者归并到目标患者 |
| sync_version | 患者变更版本号，推送时带给 M01 用于判定新旧、防乱序覆盖 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：页面 8 个、数据表 12 张、接口 43 个 | 系统设计组 |