# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块：患者匹配合并与质量（Patient Matching, Merge & Quality）详细设计

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI（子模块编号 M03-02 患者匹配合并与质量）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M01 主数据管理MDM》《M02 统一权限与安全》《M03 患者服务与EMPI 01 患者主索引与建档》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery / APScheduler
**文档用途：** 作为患者匹配合并与质量子模块开发、测试、验收依据；作为 01 建档、M04/M05/M10/M11/M12/M13/M16/M19 处理重复患者与数据质量的治理入口

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

患者匹配合并与质量回答两个问题：**“两个患者是不是同一个人？”**、**“患者主数据质量达标吗？”**

01 子模块建立患者主索引、保证“一主证件一患者”；但真实世界存在：
- 同一患者用不同证件（身份证/护照/出生证）多次建档；
- 同名同姓不同人，姓名+出生日期相同但证件不同；
- 手机号共用（家属）导致误判；
- 无证件患者仅凭姓名+性别+出生日期建档，极易重复。

本子模块提供：
- **匹配规则引擎**：字段权重、算法、阈值可配置。
- **候选识别**：建档即时匹配 + 批量扫描任务。
- **合并申请与审批**：影响分析、多级审批、留痕。
- **合并执行**：主索引重定向 + 业务订阅方执行重定向 + 合并日志。
- **拆分**：仅恢复主索引 + 提供重定向记录，业务数据回迁走人工工单。
- **质量规则与扫描**：完整性、唯一性、规范性、时效性、引用完整性。
- **患者黑名单**：禁止特定患者被合并/被引用，防误操作。

**边界一句话：** 本子模块只管“判定、申请、审批、执行与留痕”，**不直写其他模块业务表**；重定向由订阅方消费事件后自行执行，本子模块只输出重定向清单与合并日志。

### 1.2 与 01 的分工

| 能力 | 归属 | 说明 |
|---|---|---|
| 患者主档、证件、联系方式、地址、联系人、授权 | M03-01 | 本子模块只读引用 |
| 基础完整度评分（建档时计算） | M03-01 | 本子模块的质量扫描是增强版（规则化、可配置） |
| 状态 `MERGED`、`merge_to_id` 字段 | M03-01 定义，M03-02 写入 | 合并动作由本模块执行 |
| 重复候选识别、相似度 | **M03-02 本子模块** | — |
| 合并申请、审批、执行 | **M03-02 本子模块** | — |
| 拆分 | **M03-02 本子模块** | 仅主索引恢复 + 重定向记录 |
| 质量规则与扫描 | **M03-02 本子模块** | — |
| 患者黑名单 | **M03-02 本子模块** | — |

### 1.3 模块目标

- **可配置的匹配规则**：字段权重、算法、阈值集中配置，避免硬编码。
- **双通道候选识别**：建档即时匹配（同步返回候选）+ 批量扫描（异步任务）。
- **合并可控**：合并必须走申请—影响分析—审批—执行，禁止直接改库。
- **合并可追溯**：患者版本快照 + 重定向清单 + 合并日志，支持事后审计与拆分。
- **拆分边界清晰**：仅恢复主索引，已重定向业务数据通过工单人工回迁，避免自动化拆分造成数据错乱。
- **质量可度量**：规则化扫描 + 问题清单 + 趋势看板。
- **防误操作**：患者黑名单 + 二次验证 + 影响分析确认。

### 1.4 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 信息科 | 匹配合并执行 | 候选审核、发起合并、执行合并、拆分 |
| 医务科 | 合并审批 | 审批合并申请（涉及诊疗数据时） |
| 财务科 | 合并审批 | 审批合并申请（涉及收费数据时） |
| 院领导 | 高危合并审批 | 金额/患者数超阈值时审批 |
| 数据治理专员 | 质量扫描与整改 | 配置质量规则、查看问题清单、发起整改 |
| 审计员 | 追溯 | 查看合并/拆分日志、质量报告 |
| 导医/客服 | 建档时查看候选 | 建档时查看候选提示、选择“确认新建”或“使用已有” |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 匹配配置 | 字段权重、算法、阈值、自动合并开关 |
| 匹配规则 | 按场景（建档/批量/证件）配置规则 |
| 建档即时匹配 | 01 建档时同步返回候选列表 |
| 批量匹配任务 | 按条件扫描全量患者，生成候选对 |
| 候选对管理 | 查看、确认、忽略、合并 |
| 合并申请 | 选择主/从患者、填写原因、影响分析 |
| 合并审批 | 多级审批、SLA 提醒、移动端审批 |
| 合并执行 | 患者版本快照、主索引重定向标记、重定向清单输出、合并日志 |
| 拆分 | 主索引恢复 + 重定向记录查看 + 拆分工单 |
| 患者黑名单 | 禁止合并/禁止引用 |
| 质量规则 | 完整性、唯一性、规范性、时效性、引用完整性 |
| 质量扫描 | 批量扫描、问题清单、趋势看板 |
| 质量报告 | 日/周/月报告、导出 |
| 内部契约 | 候选查询、合并状态查询、重定向清单查询 |

### 2.2 范围外

| 范围外内容 | 负责方 |
|---|---|
| 患者主档、证件、联系方式、地址、联系人、授权的写入 | M03-01 |
| 业务表 `patient_id` 的实际重定向 | M04/M05/M10/M11/M12/M13/M16/M19 等订阅方 |
| 合并后已重定向业务数据的自动回迁 | 本模块不实现，走拆分工单人工处理 |
| 会员权益、积分 | M03-03 / M19 |
| 随访执行、外呼 | M19 |
| 消息发送 | M03-05 |
| 门户页面 | M03-06 |
| 全院数据质量总览 | M01-12 分发同步与质量 |

### 2.3 与相邻模块分工

```text
M03-01 建档 ◄── 即时匹配 ── M03-02 匹配合并
   │                            │
   │                            ├── 合并事件 + 重定向清单
   │                            ▼
   │                     M04/M05/M10/M11/M12/M13/M16/M19
   │                      （订阅方自行重定向 patient_id）
   │
   └── 状态 MERGED / merge_to_id ──► 01 表字段（M03-02 写入）

M03-02 质量扫描 ──► 问题清单 ──► M03-01 建档/编辑整改
                                 └── 或 M03-02 合并

M01-12 质量看板 ◄── 本模块质量结果事件（可选）
```

**关键约定：**
- 合并执行后，从患者 `status=MERGED`、`merge_to_id=目标患者`；本模块写 01 表这两个字段（通过内部接口，不直写）。
- 业务表重定向由订阅方执行；本模块输出 `mpi_merge_log.redirect_items_json` 重定向清单。
- 拆分仅恢复主索引，**不自动回迁业务数据**；拆分工单交信息科处理。
- 质量扫描是增强版，01 的基础完整度仍保留（建档时实时计算）。

### 2.4 依赖清单（对 01/M01/M02）

| 依赖方 | 依赖内容 | 用途 |
|---|---|---|
| M03-01 患者 | `mpi_patient` / `mpi_patient_identifier` / `mpi_patient_contact` / `mpi_patient_address` / `mpi_patient_relation` / `mpi_patient_consent` / `mpi_patient_log` | 读取患者数据、写入合并状态、写合并日志 |
| M03-01 内部接口 | `GET /internal/v1/patient/{id}/brief`、`GET /internal/v1/patient/changes`、合并状态更新接口（新增） | 读取与状态更新 |
| M01 字典 | `md_dict_item` / `md_dict_type` | 匹配算法枚举、质量规则枚举 |
| M01 参数 | `md_sys_param` | 匹配阈值、批量扫描上限、质量阈值 |
| M01 职工/科室 | `mdm_employee` / `mdm_department` | 审批人、操作人、数据权限 |
| M02 账号 | `sys_account` | 操作人、审批人 |
| M02 权限 | `mpi:match:*` / `mpi:merge:*` / `mpi:quality:*` 权限码 | 页面/接口鉴权 |
| M02 审计 | `sys_audit_log` | 合并/拆分/黑名单操作审计 |
| M02 二次验证 | `sys_mfa_challenge` | 合并执行前二次验证 |
| M20 消息 | 短信/站内信 | 审批提醒、合并通知 |

---

## 3. 业务模型

### 3.1 匹配模型

#### 3.1.1 匹配字段与算法

| 字段 | 算法 | 说明 |
|---|---|---|
| 姓名 | 精确 / 拼音全拼 / 拼音首字母 / Jaro-Winkler / 编辑距离 | 中文姓名常用拼音+编辑距离 |
| 性别 | 精确 | 不一致时分数为 0 |
| 出生日期 | 精确 / 容差（±1 天） | 防止录入错误 |
| 证件号哈希 | 精确 | 命中即高度疑似 |
| 手机号哈希 | 精确 | 命中加分，但可共用 |
| 地址 | 分词后 Jaccard | 辅助 |
| 联系人姓名 + 电话 | 精确 / 编辑距离 | 辅助 |

#### 3.1.2 权重与总分

```
总分 = Σ(字段得分 × 字段权重) / Σ(字段权重) × 100
字段得分 ∈ [0, 1]
```

默认权重：

| 字段 | 权重 | 说明 |
|---|---|---|
| 证件号哈希 | 0.40 | 命中即视为极高相似 |
| 姓名 | 0.20 | — |
| 出生日期 | 0.15 | — |
| 手机号哈希 | 0.10 | — |
| 性别 | 0.05 | — |
| 地址 | 0.05 | — |
| 联系人 | 0.05 | — |

#### 3.1.3 分级

| 总分区间 | 等级 | 处置 |
|---|---|---|
| ≥ 95 | `HIGH` | 强候选，建档时高亮 |
| 80~94 | `MEDIUM` | 中候选，提示用户确认 |
| 60~79 | `LOW` | 弱候选，仅后台可见 |
| < 60 | `NONE` | 不生成候选 |

阈值通过 `mpi_dedup_config` 配置，可按场景覆盖（建档/批量）。

### 3.2 合并模型

#### 3.2.1 合并流程

```
① 候选审核（候选对页面）
   ├─ 确认非同一人 → 标记 IGNORED，不再提示
   └─ 确认同一人 → 发起合并申请
② 发起合并申请（选择主/从患者、填写原因）
   ├─ 系统做影响分析（业务单据数量、金额、患者标签）
   ├─ 评估风险等级（LOW/MEDIUM/HIGH）
   └─ 生成审批链
③ 审批（多级）
   ├─ LOW：信息科长
   ├─ MEDIUM：信息科长 → 医务科长
   └─ HIGH：信息科长 → 医务科长 → 财务科长 → 院领导
④ 执行合并
   ├─ 二次验证
   ├─ 保存患者版本快照
   ├─ 调用 01 更新从患者 status=MERGED、merge_to_id
   ├─ 生成重定向清单（业务表名 + 主键列表）
   ├─ 写合并日志
   └─ 发布 mpi.patient.merged 事件（订阅方自行重定向）
⑤ 订阅方重定向
   ├─ 消费事件 + 拉取重定向清单
   ├─ 批量 UPDATE 业务表 patient_id
   ├─ 上报执行结果（成功/失败/部分）
   └─ 失败项进入重试队列，超阈值告警
```

#### 3.2.2 风险等级规则

| 等级 | 条件 |
|---|---|
| `LOW` | 无业务单据 或 业务单据 ≤ 10 且金额 ≤ 1000 |
| `MEDIUM` | 业务单据 11~100 或 金额 1001~50000 |
| `HIGH` | 业务单据 > 100 或 金额 > 50000 或 涉及住院/手术/屈光记录 |

#### 3.2.3 合并约束

| 约束 | 说明 |
|---|---|
| 主从患者状态 | 主患者必须 `NORMAL`；从患者必须 `NORMAL` 或 `FROZEN`（`FROZEN` 需先解冻） |
| 黑名单 | 主/从患者均不能在黑名单 |
| 已在申请中 | 主/从患者不能有未完成的合并申请 |
| 同院区 | 主从患者 `org_id` 必须一致 |
| 二次验证 | 执行合并必须通过 M02-05 二次验证 |

### 3.3 拆分模型

#### 3.3.1 拆分边界

| 项 | 行为 |
|---|---|
| 主索引 | 从患者恢复 `status=NORMAL`、`merge_to_id=NULL` |
| 业务数据 | **不自动回迁**；输出拆分工单，交信息科人工处理 |
| 重定向记录 | 展示合并时记录的业务表/主键清单，供人工核对 |
| 审批 | 拆分必须走申请—审批，且需院领导审批 |

#### 3.3.2 拆分原因

| 原因 | 说明 |
|---|---|
| `MISJUDGED` | 误判为同一人 |
| `SYSTEM_ERROR` | 系统错误合并 |
| `PATIENT_REQUEST` | 患者要求拆分 |
| `OTHER` | 其他 |

### 3.4 质量模型

#### 3.4.1 质量维度

| 维度 | 规则示例 |
|---|---|
| 完整性 | 姓名必填、性别必填、出生日期必填、主证件必填（有证件类型时）、手机号必填（VIP）、地址必填（住院患者） |
| 唯一性 | 主证件哈希唯一、手机号哈希 + 姓名拼音组合疑似重复 |
| 规范性 | 手机号格式、证件号格式、出生日期合理范围、姓名不含特殊字符 |
| 时效性 | 超过 N 年未就诊、超过 N 年未更新 |
| 引用完整性 | 业务引用存在性（可选，调用订阅方接口） |

#### 3.4.2 规则字段

每条规则包含：维度、对象（患者/证件/联系方式）、条件表达式、严重级别（ERROR/WARN/INFO）、是否启用、阈值、整改建议。

#### 3.4.3 扫描与整改

- **定时扫描**：每日 02:00 全量（可配置增量）。
- **手动扫描**：按条件（科室、建档时间、来源）触发。
- **问题清单**：按维度/严重级别分组，支持下钻、指派整改人、标记已整改。
- **整改闭环**：整改动作在 01 建档/编辑完成，本模块只记录状态（待整改/已整改/已忽略）。

### 3.5 患者黑名单模型

| 字段 | 说明 |
|---|---|
| 患者 ID | 黑名单对象 |
| 原因 | 说明 |
| 类型 | `NO_MERGE`（禁止合并）/ `NO_REFERENCE`（禁止业务引用）/ `BOTH` |
| 有效期 | 可为长期 |
| 操作人 | 信息科 |
| 解除 | 信息科解除并留痕 |

**用途：**
- 争议患者、法务患者禁止合并；
- 患者本人明确要求不被合并；
- 测试患者禁止被业务引用。

### 3.6 患者版本快照

每次合并/拆分/关键字段变更前，保存患者主索引 + 全部子表的完整快照，用于审计与回滚（只回滚主索引，不回滚业务表）。

快照包含：
- `mpi_patient` 一行
- `mpi_patient_identifier` 全部有效行
- `mpi_patient_contact` 全部有效行
- `mpi_patient_address` 全部有效行
- `mpi_patient_relation` 全部有效行
- `mpi_patient_consent` 全部行

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [患者匹配合并与质量数据结构](M03_患者服务与EMPI_02_患者匹配合并与质量_数据结构.md)

本章原包含 **13 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 患者匹配合并与质量完整数据结构 | [患者匹配合并与质量数据结构](M03_患者服务与EMPI_02_患者匹配合并与质量_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```text
患者服务与EMPI
└── 患者匹配合并与质量
    ├── P01 候选匹配列表（核心页）
    ├── P02 候选对比详情
    ├── P03 合并申请单
    ├── P04 合并审批
    ├── P05 合并记录与重定向清单
    ├── P06 拆分申请
    ├── P07 质量看板
    ├── P08 质量问题清单
    ├── P09 质量规则配置
    ├── P10 匹配与合并配置
    └── P11 患者黑名单
```

### 5.2 P01 候选匹配列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：患者服务与EMPI / 患者匹配合并与质量 / 候选匹配列表     用户：信息科01 ▾ │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：待处理 128 | 高分 32 | 中分 56 | 低分 40 | 已忽略 1,203              │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：关键字[姓名/EMPI/手机号] 等级[全部▼] 状态[待处理▼] 来源[建档/批量▼]       │
│ 工具栏：[触发批量匹配] [导出] [刷新]                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │患者A           │患者B           │总分│等级│来源│状态   │生成时间       │操作│
│ ☐ │P202610200001 王五│P202610200112 王五│98 │高  │建档│待处理 │2026-10-20 09:15│···│
│ ☐ │P202610200002 李四│P202610200034 李思│88 │中  │批量│待处理 │2026-10-20 03:00│···│
│ ☐ │P202610200003 张三│P202610200055 张三│72 │低  │批量│待处理 │2026-10-20 03:00│···│
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 128 条                                        [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**列：** 复选框、患者 A（EMPI + 姓名）、患者 B（EMPI + 姓名）、总分、等级、来源（建档即时/批量）、状态（待处理/已确认/已忽略/已合并）、生成时间、操作。

**操作：** 对比详情、发起合并、标记忽略、查看患者。

### 5.3 P02 候选对比详情

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 候选对比：P202610200001 王五  vs  P202610200112 王五         总分：98（高）    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 字段            │患者 A                │患者 B                │得分│权重│贡献 │
│ 姓名            │王五                  │王五                  │1.00│0.20│0.200│
│ 性别            │男                    │男                    │1.00│0.05│0.050│
│ 出生日期        │1980-01-02            │1980-01-02            │1.00│0.15│0.150│
│ 证件号哈希      │8f3a...               │8f3a...               │1.00│0.40│0.400│
│ 手机号哈希      │b7c2...               │b7c2...               │1.00│0.10│0.100│
│ 地址            │北京市朝阳区******     │北京市朝阳区******     │0.80│0.05│0.040│
│ 联系人          │王小明（子）          │王小明（子）          │1.00│0.05│0.050│
│                │                      │                      │    │    │98.0 │
├────────────────────────────────────────────────────────────────────────────────┤
│ 业务影响：                                                                     │
│ 患者 A：门诊 3 次、收费 5 笔（合计 ¥1,280）、无住院、无视光                 │
│ 患者 B：门诊 1 次、收费 2 笔（合计 ¥320）、无住院、无视光                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 建议主患者：A（业务单据更多）   [以 B 为主] [发起合并] [标记非同一人]          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 P03 合并申请单

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 合并申请                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 主患者：[P202610200001 王五 ▼]（保留）                                          │
│ 从患者：[P202610200112 王五 ▼]（合并后 status=MERGED）                          │
│ 合并原因：[同一患者两次建档，身份证与出生证为同一人________]（≥10 字）          │
│ 附件：[上传身份证、出生证扫描件]                                                │
│                                                                                │
│ 【影响分析】（系统自动生成）                                                    │
│ 从患者业务数据：门诊 1 次、收费 2 笔（¥320）、无住院、无视光                  │
│ 风险等级：LOW（业务单据 ≤10 且金额 ≤1000）                                     │
│ 审批链：信息科长                                                                │
│                                                                                │
│ ⚠ 合并后从患者不可直接编辑，仅可查看；如需恢复请走拆分流程。                    │
├────────────────────────────────────────────────────────────────────────────────┤
│                                      [取消] [保存草稿] [提交审批]              │
└────────────────────────────────────────────────────────────────────────────────┘
```

**校验：**
- 主从患者不能相同。
- 主从患者均 `NORMAL` 或从患者 `FROZEN`（需先解冻）。
- 主从患者均不在黑名单。
- 主从患者不能有未完成的合并申请。
- 主从患者 `org_id` 一致。
- 合并原因 ≥10 字。

### 5.5 P04 合并审批

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 合并审批：CR-MERGE-2026102000012                          状态：审批中          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 申请信息：信息科01  2026-10-20 10:15  风险等级：LOW                             │
│ 主患者：P202610200001 王五    从患者：P202610200112 王五                        │
│ 合并原因：同一患者两次建档，身份证与出生证为同一人                               │
│ 附件：身份证.jpg、出生证.jpg                                                     │
│                                                                                │
│ 影响分析：                                                                      │
│ · 从患者门诊 1 次、收费 2 笔（¥320）                                            │
│ · 风险等级 LOW，审批链：信息科长                                                │
├────────────────────────────────────────────────────────────────────────────────┤
│ 审批流：                                                                        │
│ ● 提交   信息科01  2026-10-20 10:15                                             │
│ ○ 信息科长 待处理（已等待 0.5 小时）                                             │
├────────────────────────────────────────────────────────────────────────────────┤
│ 审批意见：[________________________________________]                            │
│ [通过] [驳回] [转办]                                                            │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 P05 合并记录与重定向清单

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 合并记录：MG2026102000012                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 主患者：P202610200001 王五    从患者：P202610200112 王五                        │
│ 执行人：信息科01  执行时间：2026-10-20 11:00  二次验证：已通过                  │
│ 审批链：信息科长 2026-10-20 10:30 通过                                          │
│                                                                                │
│ 【重定向清单】                                                                  │
│ 业务表              │重定向条数│订阅方状态          │完成时间                │
│ m04_outpatient_visit│   1     │✅ 已完成            │2026-10-20 11:02        │
│ m16_charge_bill     │   2     │✅ 已完成            │2026-10-20 11:02        │
│ m16_payment         │   2     │⚠ 部分完成（1 失败）│2026-10-20 11:05        │
│ ...                                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ [查看患者版本快照] [导出重定向清单] [发起拆分]                                  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.7 P06 拆分申请

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 拆分申请：基于合并记录 MG2026102000012                                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 待恢复患者：P202610200112 王五（当前 MERGED → 目标 P202610200001）              │
│ 拆分原因：● 误判为同一人  ○ 系统错误  ○ 患者要求  ○ 其他                       │
│ 原因说明：[经核实两人为不同患者，身份证号相似但出生日期不同________]（≥10字）   │
│ 附件：[上传证明材料]                                                            │
│                                                                                │
│ ⚠ 拆分仅恢复患者主索引状态，已重定向的业务数据不会自动回迁，需信息科人工处理。   │
│ ⚠ 拆分需院领导审批。                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│                                      [取消] [保存草稿] [提交审批]              │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.8 P07 质量看板

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 质量看板                                                  扫描时间：2026-10-20 02:00│
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐                       │
│ │ 患者总数 │ 问题患者 │ 问题率   │ 待整改   │ 已整改   │                       │
│ │ 12,386   │ 1,208    │ 9.75%    │ 856      │ 352      │                       │
│ └──────────┴──────────┴──────────┴──────────┴──────────┘                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 按维度：                                                                        │
│ 完整性：问题 620（5.0%）  唯一性：问题 320（2.6%）  规范性：问题 180（1.5%）    │
│ 时效性：问题 88（0.7%）   引用完整性：问题 0                                     │
│                                                                                │
│ 趋势（近 30 天）：问题率 9.75% ↓ 0.3%                                           │
│                                                                                │
│ TOP 问题：                                                                      │
│ 1. 出生日期缺失  - 320 条                                                       │
│ 2. 手机号格式异常 - 180 条                                                      │
│ 3. 主证件缺失    - 300 条                                                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.9 P08 质量问题清单

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 质量问题清单                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：维度[完整性▼] 严重级别[全部▼] 状态[待整改▼] 规则[出生日期必填▼]           │
│ 工具栏：[批量指派] [导出] [重新扫描]                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │EMPI          │姓名 │规则         │字段      │状态  │整改人  │操作         │
│ ☐ │P202610200003 │张三 │出生日期必填 │birth_date│待整改│—       │[查看] [指派]│
│ ☐ │P202610200045 │李四 │手机号格式   │phone     │待整改│客服01  │[查看] [催办]│
│ ☐ │P202610200102 │王五 │主证件缺失   │id_no     │已整改│信息科01│[查看]       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 856 条                                        [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.10 P09 质量规则配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 质量规则配置                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增规则]                                                                    │
│                                                                                │
│ 规则编码  │规则名称      │维度  │严重级别│启用│阈值│更新时间        │操作      │
│ QR-COMP-01│姓名必填      │完整性│ERROR   │是  │—   │2026-10-01 09:00│[编辑]    │
│ QR-COMP-02│出生日期必填  │完整性│WARN    │是  │—   │2026-10-01 09:00│[编辑]    │
│ QR-UNIQ-01│主证件唯一    │唯一性│ERROR   │是  │—   │2026-10-01 09:00│[编辑]    │
│ QR-FORM-01│手机号格式    │规范性│WARN    │是  │—   │2026-10-01 09:00│[编辑]    │
│ QR-TIME-01│超 5 年未就诊 │时效性│INFO    │是  │5 年│2026-10-01 09:00│[编辑]    │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.11 P10 匹配与合并配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 匹配与合并配置                                        ⚠ 修改影响全院匹配结果  │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【匹配阈值】                                                                    │
│ 高候选阈值：[95 ]  中候选阈值：[80 ]  低候选阈值：[60 ]                         │
│                                                                                │
│ 【字段权重】                                                                    │
│ 证件号哈希：[0.40]  姓名：[0.20]  出生日期：[0.15]  手机号：[0.10]              │
│ 性别：[0.05]  地址：[0.05]  联系人：[0.05]  （合计：1.00）                      │
│                                                                                │
│ 【建档即时匹配】                                                                │
│ ☑ 启用  返回候选数：[5 ]  仅返回中高分：[是]                                    │
│                                                                                │
│ 【批量匹配】                                                                    │
│ ☑ 启用  定时扫描：[每日 03:00 ▼]  扫描范围：[全量 / 近 90 天]                   │
│                                                                                │
│ 【合并审批】                                                                    │
│ LOW 审批链：[信息科长]                                                          │
│ MEDIUM 审批链：[信息科长 → 医务科长]                                            │
│ HIGH 审批链：[信息科长 → 医务科长 → 财务科长 → 院领导]                          │
│ 执行合并二次验证：[☑ 必须]                                                      │
│                                                                                │
│ 【质量扫描】                                                                    │
│ ☑ 启用  定时扫描：[每日 02:00]  问题整改 SLA：[7 天]                            │
├────────────────────────────────────────────────────────────────────────────────┤
│                                         [取消] [保存]                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.12 P11 患者黑名单

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 患者黑名单                                                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增黑名单]                                                                  │
│                                                                                │
│ EMPI          │姓名 │类型      │原因              │有效期  │操作人  │操作      │
│ P202610200888 │赵六 │禁止合并  │法务争议          │长期    │信息科01│[解除]    │
│ P202610200999 │测试 │禁止引用  │测试患者          │长期    │信息科01│[解除]    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| **候选匹配** | | | | |
| API-01 | GET | `/api/v1/mpi/match/candidates` | 候选匹配列表 | `mpi:match:list` |
| API-02 | GET | `/api/v1/mpi/match/candidates/{id}` | 候选对比详情 | `mpi:match:list` |
| API-03 | POST | `/api/v1/mpi/match/candidates/{id}/ignore` | 标记非同一人 | `mpi:match:ignore` |
| API-04 | POST | `/api/v1/mpi/match/candidates/{id}/confirm` | 确认同一人（进入合并） | `mpi:merge:create` |
| API-05 | POST | `/api/v1/mpi/match/scan` | 触发批量匹配 | `mpi:match:scan` |
| API-06 | GET | `/api/v1/mpi/match/tasks/{task_id}` | 批量匹配任务详情 | `mpi:match:scan` |
| API-07 | GET | `/api/v1/mpi/match/statistics` | 匹配统计 | `mpi:match:list` |
| **合并** | | | | |
| API-08 | GET | `/api/v1/mpi/merge/requests` | 合并申请列表 | `mpi:merge:list` |
| API-09 | GET | `/api/v1/mpi/merge/requests/{id}` | 合并申请详情 | `mpi:merge:list` |
| API-10 | POST | `/api/v1/mpi/merge/requests` | 发起合并申请 | `mpi:merge:create` |
| API-11 | POST | `/api/v1/mpi/merge/requests/{id}/submit` | 提交审批 | `mpi:merge:create` |
| API-12 | POST | `/api/v1/mpi/merge/requests/{id}/approve` | 审批通过 | `mpi:merge:approve` |
| API-13 | POST | `/api/v1/mpi/merge/requests/{id}/reject` | 审批驳回 | `mpi:merge:approve` |
| API-14 | POST | `/api/v1/mpi/merge/requests/{id}/withdraw` | 撤回 | `mpi:merge:create` |
| API-15 | POST | `/api/v1/mpi/merge/requests/{id}/execute` | 执行合并 | `mpi:merge:execute` |
| API-16 | GET | `/api/v1/mpi/merge/requests/todo` | 我的待办 | `mpi:merge:approve` |
| **合并记录** | | | | |
| API-17 | GET | `/api/v1/mpi/merge/logs` | 合并记录列表 | `mpi:merge:audit` |
| API-18 | GET | `/api/v1/mpi/merge/logs/{id}` | 合并记录详情（含重定向清单） | `mpi:merge:audit` |
| API-19 | GET | `/api/v1/mpi/merge/logs/{id}/redirect-items` | 重定向清单 | `mpi:merge:audit` |
| API-20 | POST | `/api/v1/mpi/merge/logs/{id}/redirect-report` | 订阅方上报重定向结果 | 内部服务 |
| API-21 | GET | `/api/v1/mpi/merge/logs/{id}/versions` | 患者版本快照 | `mpi:merge:audit` |
| **拆分** | | | | |
| API-22 | POST | `/api/v1/mpi/split/requests` | 发起拆分申请 | `mpi:split:create` |
| API-23 | GET | `/api/v1/mpi/split/requests` | 拆分申请列表 | `mpi:split:list` |
| API-24 | GET | `/api/v1/mpi/split/requests/{id}` | 拆分申请详情 | `mpi:split:list` |
| API-25 | POST | `/api/v1/mpi/split/requests/{id}/approve` | 拆分审批 | `mpi:split:approve` |
| API-26 | POST | `/api/v1/mpi/split/requests/{id}/execute` | 执行拆分 | `mpi:split:execute` |
| **质量** | | | | |
| API-27 | GET | `/api/v1/mpi/quality/dashboard` | 质量看板 | `mpi:quality:list` |
| API-28 | GET | `/api/v1/mpi/quality/issues` | 质量问题清单 | `mpi:quality:list` |
| API-29 | POST | `/api/v1/mpi/quality/scan` | 触发质量扫描 | `mpi:quality:scan` |
| API-30 | GET | `/api/v1/mpi/quality/rules` | 质量规则列表 | `mpi:quality:list` |
| API-31 | POST | `/api/v1/mpi/quality/rules` | 新增质量规则 | `mpi:quality:update` |
| API-32 | PUT | `/api/v1/mpi/quality/rules/{id}` | 修改质量规则 | `mpi:quality:update` |
| API-33 | POST | `/api/v1/mpi/quality/issues/batch-assign` | 批量指派整改 | `mpi:quality:assign` |
| API-34 | POST | `/api/v1/mpi/quality/issues/{id}/resolve` | 标记已整改 | `mpi:quality:assign` |
| API-35 | GET | `/api/v1/mpi/quality/report` | 导出质量报告 | `mpi:quality:export` |
| **黑名单** | | | | |
| API-36 | GET | `/api/v1/mpi/blocklist` | 黑名单列表 | `mpi:blocklist:list` |
| API-37 | POST | `/api/v1/mpi/blocklist` | 新增黑名单 | `mpi:blocklist:update` |
| API-38 | POST | `/api/v1/mpi/blocklist/{id}/release` | 解除黑名单 | `mpi:blocklist:update` |
| **配置** | | | | |
| API-39 | GET | `/api/v1/mpi/dedup/config` | 查询匹配与合并配置 | `mpi:dedup:config:list` |
| API-40 | PUT | `/api/v1/mpi/dedup/config` | 修改配置 | `mpi:dedup:config:update` |
| **内部契约** | | | | |
| API-41 | POST | `/internal/v1/mpi/match/instant` | 建档即时匹配（供 01 调用） | 内部服务 |
| API-42 | GET | `/internal/v1/mpi/merge/status/{patient_id}` | 患者合并状态（供全院查询） | 内部服务 |
| API-43 | GET | `/internal/v1/mpi/merge/{merge_id}/redirect-items` | 重定向清单（供订阅方拉取） | 内部服务 |
| API-44 | GET | `/internal/v1/mpi/blocklist/check` | 黑名单校验（供 01 与业务调用） | 内部服务 |
| API-45 | GET | `/internal/v1/mpi/quality/issues/summary` | 质量问题汇总（供 M01-12 看板） | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码（M03-02：52101~52140）**

| 错误码 | 含义 |
|---|---|
| "0302001" | 候选对不存在 |
| "0302002" | 候选对已处理 |
| "0302003" | 主从患者不能相同 |
| "0302004" | 主患者状态不允许合并 |
| "0302005" | 从患者状态不允许合并 |
| "0302006" | 主从患者院区不一致 |
| "0302007" | 主从患者已在合并申请中 |
| "0302008" | 主从患者在黑名单 |
| "0302009" | 合并原因字数不足 |
| "0302010" | 合并申请不存在 |
| "0302011" | 合并申请状态不允许该操作 |
| "0302012" | 当前审批人不是您 |
| "0302013" | 合并执行需二次验证 |
| "0302014" | 合并执行时患者状态已变更 |
| "0302015" | 合并执行失败 |
| "0302016" | 合并记录不存在 |
| "0302017" | 重定向清单不存在 |
| "0302018" | 订阅方上报格式错误 |
| "0302019" | 拆分申请不存在 |
| "0302020" | 拆分原因非法 |
| "0302021" | 拆分执行失败 |
| "0302022" | 拆分审批未通过 |
| "0302023" | 质量规则不存在 |
| "0302024" | 质量规则编码重复 |
| "0302025" | 质量扫描任务进行中 |
| "0302026" | 质量问题不存在 |
| "0302027" | 黑名单已存在 |
| "0302028" | 黑名单不存在 |
| "0302029" | 配置项非法 |
| "0302030" | 批量匹配任务不存在 |
| "0302031" | 即时匹配服务不可用 |
| "0302032" | M03-01 服务不可用 |
| "0302033" | M02 权限服务不可用 |
| "0302034" | 重定向清单输出失败 |
| "0302035" | 患者版本快照保存失败 |
| "0302036" | 数据已变更，请刷新后重试 |
| "0302037" | 合并影响分析超时 |
| "0302038" | 质量报告导出超限 |
| "0302039" | 批量扫描数据量超限 |
| "0302040" | 黑名单校验失败 |

### 6.3 关键接口示例

#### API-01 候选匹配列表

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 5001,
        "patient_a": {
          "id": 10001,
          "empi_no": "P202610200001",
          "patient_name": "王五",
          "gender": "MALE",
          "birth_date": "1980-01-02"
        },
        "patient_b": {
          "id": 10112,
          "empi_no": "P202610200112",
          "patient_name": "王五",
          "gender": "MALE",
          "birth_date": "1980-01-02"
        },
        "total_score": 98.0,
        "level": "HIGH",
        "source": "REGISTRATION",
        "status": "PENDING",
        "created_at": "2026-10-20T09:15:00"
      }
    ],
    "total": 128,
    "page": 1,
    "page_size": 20,
    "pages": 7
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-02 候选对比详情

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 5001,
    "patient_a": { "id": 10001, "empi_no": "P202610200001", "patient_name": "王五" },
    "patient_b": { "id": 10112, "empi_no": "P202610200112", "patient_name": "王五" },
    "total_score": 98.0,
    "level": "HIGH",
    "field_scores": [
      { "field": "name", "score": 1.00, "weight": 0.20, "contribution": 0.200 },
      { "field": "gender", "score": 1.00, "weight": 0.05, "contribution": 0.050 },
      { "field": "birth_date", "score": 1.00, "weight": 0.15, "contribution": 0.150 },
      { "field": "id_hash", "score": 1.00, "weight": 0.40, "contribution": 0.400 },
      { "field": "phone_hash", "score": 1.00, "weight": 0.10, "contribution": 0.100 },
      { "field": "address", "score": 0.80, "weight": 0.05, "contribution": 0.040 },
      { "field": "relation", "score": 1.00, "weight": 0.05, "contribution": 0.050 }
    ],
    "impact": {
      "patient_a": { "outpatient_count": 3, "charge_count": 5, "charge_amount": 1280.00 },
      "patient_b": { "outpatient_count": 1, "charge_count": 2, "charge_amount": 320.00 },
      "suggested_primary": 10001
    }
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-10 发起合并申请

```json
{
  "primary_patient_id": 10001,
  "secondary_patient_id": 10112,
  "reason": "同一患者两次建档，身份证与出生证为同一人",
  "attachment_ids": [771, 772]
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "merge_request_id": 812,
    "merge_no": "MG2026102000012",
    "risk_level": "LOW",
    "approval_chain": ["信息科长"],
    "status": "DRAFT"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-15 执行合并

```json
{
  "reason": "审批通过，执行合并",
  "second_factor_token": "123456"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "merge_id": "MG2026102000012",
    "merge_log_id": 90001,
    "primary_patient_id": 10001,
    "secondary_patient_id": 10112,
    "secondary_status": "MERGED",
    "redirect_items_generated": 3,
    "version_snapshot_id": 70001,
    "event_published": true
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-19 重定向清单

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "merge_id": "MG2026102000012",
    "redirect_items": [
      {
        "table_name": "m04_outpatient_visit",
        "count": 1,
        "ids": [88001],
        "subscriber": "M04",
        "status": "COMPLETED",
        "finished_at": "2026-10-20T11:02:00"
      },
      {
        "table_name": "m16_charge_bill",
        "count": 2,
        "ids": [99001, 99002],
        "subscriber": "M16",
        "status": "COMPLETED",
        "finished_at": "2026-10-20T11:02:00"
      },
      {
        "table_name": "m16_payment",
        "count": 2,
        "ids": [77001, 77002],
        "subscriber": "M16",
        "status": "PARTIAL",
        "finished_at": "2026-10-20T11:05:00",
        "fail_ids": [77002],
        "fail_reason": "记录被锁定"
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-41 建档即时匹配（内部）

```json
{
  "patient_name": "王五",
  "gender": "MALE",
  "birth_date": "1980-01-02",
  "id_type": "ID_CARD",
  "id_no": "110101198001021234",
  "phone": "13812345678",
  "limit": 5
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "candidates": [
      {
        "patient_id": 10001,
        "empi_no": "P202610200001",
        "patient_name": "王五",
        "gender": "MALE",
        "birth_date": "1980-01-02",
        "primary_id_mask": "110***********1234",
        "primary_phone_mask": "138****5678",
        "total_score": 98.0,
        "level": "HIGH",
        "hit_fields": ["name", "gender", "birth_date", "id_hash", "phone_hash"]
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-42 患者合并状态（内部）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10112,
    "empi_no": "P202610200112",
    "status": "MERGED",
    "merge_to_id": 10001,
    "merge_to_empi_no": "P202610200001",
    "merged_at": "2026-10-20T11:00:00",
    "merge_log_id": 90001
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
from app.schemas.mpi.match import (
    CandidateQuery,
    MergeExecuteRequest,
    MergeRequestCreate,
    QualityIssueQuery,
    SplitRequestCreate,
)
from app.services.mpi.match_service import MatchService
from app.services.mpi.merge_service import MergeService
from app.services.mpi.quality_service import QualityService

router = APIRouter(prefix="/api/v1/mpi", tags=["M03-匹配合并与质量"])
internal_router = APIRouter(prefix="/internal/v1/mpi", tags=["M03-内部接口"])


@router.get("/match/candidates")
async def list_candidates(
    level: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:match:list")),
):
    svc = MatchService(db)
    q = CandidateQuery(level=level, status=status, page=page, page_size=page_size)
    items, total = await svc.list_candidates(q)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("/merge/requests")
async def create_merge_request(
    payload: MergeRequestCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:merge:create")),
):
    svc = MergeService(db)
    return success_response(await svc.create_request(payload, operator=user))


@router.post("/merge/requests/{request_id}/execute")
async def execute_merge(
    request_id: int,
    payload: MergeExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:merge:execute")),
):
    svc = MergeService(db)
    return success_response(await svc.execute(request_id, payload, operator=user))


@internal_router.post("/match/instant")
async def internal_instant_match(
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
):
    svc = MatchService(db)
    return success_response(await svc.instant_match(payload))
```

### 6.5 Service 层核心逻辑示例

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.models.mpi.dedup import (
    MpiDedupConfig,
    MpiMatchCandidate,
    MpiMatchRule,
    MpiMatchTask,
    MpiMergeApproval,
    MpiMergeLog,
    MpiMergeRequest,
    MpiMergeRequestItem,
    MpiPatientVersion,
    MpiPatientBlocklist,
)
from app.models.mpi.patient import MpiPatient


class MatchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_candidates(self, q):
        stmt = select(MpiMatchCandidate).where(
            MpiMatchCandidate.is_deleted == False
        )
        if q.level:
            stmt = stmt.where(MpiMatchCandidate.level == q.level)
        if q.status:
            stmt = stmt.where(MpiMatchCandidate.status == q.status)
        total = (await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        rows = (await self.db.execute(
            stmt.order_by(
                MpiMatchCandidate.total_score.desc(),
                MpiMatchCandidate.created_at.desc(),
            ).offset((q.page - 1) * q.page_size).limit(q.page_size)
        )).scalars().all()
        return [self._to_item(r) for r in rows], total

    async def instant_match(self, payload: dict):
        config = await self._load_config()
        if not config.instant_match_enabled:
            return {"candidates": []}
        rule = await self._load_rule("REGISTRATION")
        # 1. 精确命中证件哈希
        id_hash = hash_value(payload.get("id_no")) if payload.get("id_no") else None
        if id_hash:
            rows = (await self.db.execute(
                select(MpiPatient).where(
                    MpiPatient.primary_id_no_hash == id_hash,
                    MpiPatient.status.in_(["NORMAL", "FROZEN"]),
                    MpiPatient.is_deleted == False,
                ).limit(config.instant_match_limit)
            )).scalars().all()
            if rows:
                return {"candidates": [self._to_instant_candidate(r, 100.0, ["id_hash"]) for r in rows]}
        # 2. 模糊匹配：姓名拼音 + 出生日期 + 性别
        candidates = await self._fuzzy_match(payload, rule, config)
        candidates.sort(key=lambda c: c["total_score"], reverse=True)
        return {"candidates": candidates[:config.instant_match_limit]}

    async def _fuzzy_match(self, payload, rule, config):
        # 简化示例：只按姓名拼音+出生日期
        stmt = select(MpiPatient).where(
            MpiPatient.name_pinyin == payload.get("name_pinyin"),
            MpiPatient.is_deleted == False,
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        results = []
        for p in rows:
            score, hits = self._score(rule, payload, p)
            if score >= config.threshold_low:
                results.append(self._to_instant_candidate(p, score, hits))
        return results


class MergeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(self, payload, operator):
        # 校验主从患者
        primary = await self._get_patient(payload.primary_patient_id)
        secondary = await self._get_patient(payload.secondary_patient_id)
        self._validate_pair(primary, secondary)

        # 影响分析
        impact = await self._impact_analysis(secondary.id)
        risk = self._risk_level(impact)
        chain = await self._approval_chain(risk)

        # 建申请单
        req = MpiMergeRequest(
            merge_no=await self._gen_merge_no(),
            primary_patient_id=primary.id,
            secondary_patient_id=secondary.id,
            reason=payload.reason,
            risk_level=risk,
            approval_chain=chain,
            status="DRAFT",
            impact_json=impact,
            created_by=operator.id,
        )
        self.db.add(req)
        await self.db.flush()
        # 明细 + 审批节点
        await self._create_items(req, primary, secondary)
        await self._create_approvals(req, chain)
        await self.db.commit()
        return self._to_request_brief(req)

    async def execute(self, request_id: int, payload, operator):
        req = await self._get_request(request_id)
        if req.status != "APPROVED":
            raise BizException("0302011", "合并申请状态不允许执行")
        # 二次验证
        if not await verify_second_factor(operator, payload.second_factor_token):
            raise BizException("0302013", "合并执行需二次验证")

        primary = await self._get_patient(req.primary_patient_id)
        secondary = await self._get_patient(req.secondary_patient_id)
        if secondary.status != "NORMAL" and secondary.status != "FROZEN":
            raise BizException("0302014", "从患者状态已变更")

        # 版本快照
        snapshot = await self._save_patient_version(secondary, "MERGE_PRE")

        # 更新 01 从患者状态
        await self._update_patient_merged(secondary.id, primary.id, operator)

        # 输出重定向清单（调用订阅方注册表）
        redirect_items = await self._collect_redirect_items(secondary.id)
        merge_log = MpiMergeLog(
            merge_no=req.merge_no,
            primary_patient_id=primary.id,
            secondary_patient_id=secondary.id,
            version_snapshot_id=snapshot.id,
            redirect_items_json=redirect_items,
            executed_by=operator.id,
            executed_at=datetime.now(),
            status="EXECUTED",
        )
        self.db.add(merge_log)
        req.status = "EXECUTED"
        await self.db.commit()

        # 发布事件
        await publish_event("mpi.patient.merged", {
            "merge_id": req.merge_no,
            "primary_patient_id": primary.id,
            "secondary_patient_id": secondary.id,
            "redirect_items": redirect_items,
        })
        return {
            "merge_id": req.merge_no,
            "merge_log_id": merge_log.id,
            "primary_patient_id": primary.id,
            "secondary_patient_id": secondary.id,
            "secondary_status": "MERGED",
            "redirect_items_generated": len(redirect_items),
            "version_snapshot_id": snapshot.id,
            "event_published": True,
        }
```

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `mpi:dedup:config` | String(JSON) | 30min | 匹配与合并配置 | 配置变更 |
| `mpi:match:rule:{scene}` | String(JSON) | 30min | 场景规则 | 规则变更 |
| `mpi:match:candidate:count` | String | 5min | 待处理候选数 | 候选变更 |
| `mpi:merge:todo:{staff_id}` | String | 5min | 审批待办数 | 审批操作 |
| `mpi:quality:latest` | String(JSON) | 1h | 最新质量结果 | 扫描完成 |
| `mpi:blocklist:{patient_id}` | String | 30min | 黑名单校验缓存 | 黑名单变更 |
| `mpi:match:lock` | String | 30min | 批量匹配互斥 | 任务结束 |

### 7.2 Celery 异步任务

```python
from celery import shared_task


@shared_task
def batch_match_task(task_id: int):
    import asyncio
    return asyncio.run(_run_batch_match(task_id))


async def _run_batch_match(task_id: int):
    from app.core.database import AsyncSessionLocal
    from app.services.mpi.match_service import MatchService

    async with AsyncSessionLocal() as db:
        svc = MatchService(db)
        return await svc.run_batch(task_id)


@shared_task
def quality_scan_task(scan_id: int):
    import asyncio
    return asyncio.run(_run_quality_scan(scan_id))


async def _run_quality_scan(scan_id: int):
    from app.core.database import AsyncSessionLocal
    from app.services.mpi.quality_service import QualityService

    async with AsyncSessionLocal() as db:
        svc = QualityService(db)
        return await svc.run_scan(scan_id)


@shared_task
def retry_redirect_task(merge_log_id: int):
    """重试订阅方未完成的重定向"""
    import asyncio
    return asyncio.run(_retry_redirect(merge_log_id))


async def _retry_redirect(merge_log_id: int):
    from app.core.database import AsyncSessionLocal
    from app.services.mpi.merge_service import MergeService

    async with AsyncSessionLocal() as db:
        svc = MergeService(db)
        return await svc.retry_redirect(merge_log_id)
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_batch_match` | `0 3 * * *` | 每日 03:00 批量匹配 |
| `job_quality_scan` | `0 2 * * *` | 每日 02:00 质量扫描 |
| `job_quality_weekly_report` | `0 8 * * 1` | 每周一 08:00 质量周报 |
| `job_merge_sla_remind` | `0 * * * *` | 每小时合并审批 SLA 提醒 |
| `job_redirect_retry` | `*/10 * * * *` | 每 10 分钟重试未完成重定向 |
| `job_candidate_expire` | `0 4 * * *` | 清理 90 天前已忽略候选 |
| `job_blocklist_expire` | `0 5 * * *` | 黑名单到期自动解除 |

---

## 8. 业务规则与校验

### 8.1 匹配规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 阈值顺序 | 高 > 中 > 低 | 52129 |
| 权重合计 | 字段权重之和 = 1.0（容差 ±0.01） | 52129 |
| 规则编码唯一 | — | 52124 |
| 即时匹配返回上限 | ≤ 20 | 52129 |

### 8.2 合并规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 主从不能相同 | — | 52103 |
| 主患者 NORMAL | — | 52104 |
| 从患者 NORMAL/FROZEN | FROZEN 需先解冻 | 52105 |
| 同院区 | `org_id` 一致 | 52106 |
| 无进行中申请 | — | 52107 |
| 黑名单校验 | 主从均不能在黑名单 | 52108 |
| 原因字数 | ≥10 字 | 52109 |
| 执行二次验证 | M02-05 | 52113 |
| 执行时状态复核 | 从患者状态可能已变 | 52114 |
| 版本快照 | 执行前必须保存 | 52135 |

### 8.3 拆分规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 仅 MERGED 患者可拆分 | — | 52119 |
| 拆分原因合法 | MISJUDGED/SYSTEM_ERROR/PATIENT_REQUEST/OTHER | 52120 |
| 原因说明 ≥10 字 | — | 52120 |
| 需院领导审批 | — | 52122 |
| 执行需二次验证 | — | 52113 |
| 不自动回迁业务数据 | 仅恢复主索引 | — |

### 8.4 质量规则

| 规则 | 说明 |
|---|---|
| 规则编码唯一 | `QR-{维度}-{序号}` |
| 条件表达式合法 | JSON 解析通过 |
| 严重级别 | ERROR/WARN/INFO |
| 阈值 | 时效类规则必填 |

### 8.5 黑名单规则

| 规则 | 说明 |
|---|---|
| 患者不能重复加黑名单 | — |
| 类型合法 | NO_MERGE/NO_REFERENCE/BOTH |
| 原因 ≥10 字 | — |
| 解除需填原因 | — |

### 8.6 并发控制

| 机制 | 说明 |
|---|---|
| 合并执行互斥 | Redis `mpi:merge:lock:{request_id}` |
| 批量匹配互斥 | Redis `mpi:match:lock` |
| 版本快照 | 乐观锁 `version_no` |
| 状态机 | 申请状态流转校验 |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `mpi:match:list` | 候选列表/详情 | 信息科、数据治理 |
| `mpi:match:ignore` | 标记非同一人 | 信息科 |
| `mpi:match:scan` | 触发批量匹配 | 信息科 |
| `mpi:merge:list` | 合并申请列表/详情 | 信息科、审批人 |
| `mpi:merge:create` | 发起合并申请 | 信息科 |
| `mpi:merge:approve` | 合并审批 | 信息科长、医务科长、财务科长、院领导 |
| `mpi:merge:execute` | 执行合并 | 信息科长（需二次验证） |
| `mpi:merge:audit` | 合并记录/重定向清单 | 审计员、信息科 |
| `mpi:split:list` | 拆分申请列表 | 信息科 |
| `mpi:split:create` | 发起拆分申请 | 信息科 |
| `mpi:split:approve` | 拆分审批 | 院领导 |
| `mpi:split:execute` | 执行拆分 | 信息科长（需二次验证） |
| `mpi:quality:list` | 质量看板/问题清单/规则列表 | 数据治理、信息科 |
| `mpi:quality:scan` | 触发质量扫描 | 数据治理 |
| `mpi:quality:update` | 质量规则维护 | 数据治理 |
| `mpi:quality:assign` | 整改指派/标记已整改 | 数据治理、科室负责人 |
| `mpi:quality:export` | 导出质量报告 | 数据治理、院领导 |
| `mpi:blocklist:list` | 黑名单列表 | 信息科 |
| `mpi:blocklist:update` | 黑名单维护 | 信息科长 |
| `mpi:dedup:config:list` | 查询配置 | 信息科、数据治理 |
| `mpi:dedup:config:update` | 修改配置 | 信息科长 |

### 9.2 权限矩阵

`●` 完全控制 `○` 可操作 `△` 只读 `—` 无权限

| 功能 | 信息科长 | 信息科 | 医务科长 | 财务科长 | 院领导 | 数据治理 | 审计员 |
|---|---|---|---|---|---|---|---|
| 候选列表 | ● | ● | △ | — | △ | ● | △ |
| 标记忽略 | ● | ● | — | — | — | — | — |
| 发起合并 | ● | ● | — | — | — | — | — |
| 合并审批 | ● | — | ○ | ○ | ○ | — | — |
| 执行合并 | ● | — | — | — | — | — | — |
| 合并记录 | ● | ● | △ | △ | △ | △ | ● |
| 发起拆分 | ● | ● | — | — | — | — | — |
| 拆分审批 | — | — | — | — | ● | — | — |
| 执行拆分 | ● | — | — | — | — | — | — |
| 质量看板 | ● | ● | △ | △ | ● | ● | △ |
| 质量规则 | ● | △ | — | — | — | ● | △ |
| 质量整改指派 | ● | ● | ○ | — | — | ● | — |
| 黑名单维护 | ● | — | — | — | △ | — | △ |
| 配置维护 | ● | △ | — | — | △ | △ | △ |

### 9.3 数据权限

| 项 | 规则 |
|---|---|
| 候选可见范围 | 全院（匹配本身是全院范围） |
| 合并记录 | 全院可查，敏感字段脱敏 |
| 质量清单 | 按数据权限过滤（信息科全院、科室负责人本科室） |
| 黑名单 | 全院可查，原因可脱敏 |

### 9.4 安全措施

- 合并/拆分执行必须二次验证（M02-05）。
- 所有合并/拆分/黑名单操作写 `sys_audit_log`。
- 重定向清单不返回业务表敏感字段，只返回表名 + 主键 + 条数。
- 版本快照加密存储敏感字段，读取需权限。
- 合并事件与重定向清单仅在内部网络传输（服务令牌）。

---

## 10. 主数据分发与集成

### 10.1 分发目标

| 目标 | 分发内容 | 触发时机 | 方式 |
|---|---|---|---|
| M03-01 | 从患者状态更新（MERGED + merge_to_id） | 执行合并 | 内部接口 |
| M04/M05/M10/M11/M12/M13/M16/M19 | 合并事件 + 重定向清单 | 执行合并 | 事件 + 内部接口 |
| M01 患者同步表 | 合并后从患者状态 | 执行合并 | 事件（01 已发布 `mpi.patient.changed`，本模块补充 `mpi.patient.merged`） |
| M19 | 合并后患者关系（会员、随访） | 执行合并 | 事件 |
| M01-12 质量看板 | 质量问题汇总 | 扫描完成 | 内部接口 |
| M02 审计 | 合并/拆分/黑名单事件 | 实时 | 事件 |

### 10.2 事件清单

| 事件类型 | 触发时机 | 载荷 |
|---|---|---|
| `mpi.patient.merged` | 执行合并成功 | merge_id, primary_patient_id, secondary_patient_id, redirect_items |
| `mpi.patient.split` | 执行拆分成功 | split_id, patient_id, merge_id |
| `mpi.patient.merged.redirect_completed` | 订阅方上报重定向完成 | merge_id, subscriber, status |
| `mpi.quality.scan.completed` | 质量扫描完成 | scan_id, issue_count, dimensions |
| `mpi.blocklist.changed` | 黑名单变更 | patient_id, action |

### 10.3 内部契约

| 接口 | 用途 | 调用方 | SLA |
|---|---|---|---|
| `POST /internal/v1/mpi/match/instant` | 建档即时匹配 | M03-01 | P95 ≤ 200ms |
| `GET /internal/v1/mpi/merge/status/{patient_id}` | 患者合并状态 | 全院 | P95 ≤ 30ms |
| `GET /internal/v1/mpi/merge/{merge_id}/redirect-items` | 重定向清单 | 订阅方 | P95 ≤ 100ms |
| `POST /internal/v1/mpi/merge/logs/{id}/redirect-report` | 订阅方上报 | 订阅方 | P95 ≤ 100ms |
| `GET /internal/v1/mpi/blocklist/check` | 黑名单校验 | M03-01、业务 | P95 ≤ 20ms |
| `GET /internal/v1/mpi/quality/issues/summary` | 质量汇总 | M01-12 | P95 ≤ 100ms |

**约定：** 内部接口不返回业务表敏感字段，只返回表名 + 主键 + 状态。

### 10.4 重定向清单格式

```json
[
  {
    "table_name": "m04_outpatient_visit",
    "subscriber": "M04",
    "count": 1,
    "ids": [88001],
    "id_field": "id",
    "patient_field": "patient_id"
  },
  {
    "table_name": "m16_charge_bill",
    "subscriber": "M16",
    "count": 2,
    "ids": [99001, 99002],
    "id_field": "id",
    "patient_field": "patient_id"
  }
]
```

**约定：**
- 订阅方注册表由 M21 集成平台维护（表名 → 订阅方），本模块启动时拉取并缓存。
- 单条重定向清单最多 1000 个 ID；超出时拆分为多条 `redirect_items`。
- 订阅方上报格式：`{merge_id, subscriber, table_name, status, success_ids, fail_ids, fail_reason}`。

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| 参数异常 | 主从相同、原因字数不足 | 40001 + 字段错误 |
| 业务异常 | 状态不允许、黑名单 | 521xx |
| 并发异常 | 合并执行中、批量匹配中 | 52136 |
| 依赖异常 | 01 不可用、订阅方未响应 | 降级或提示 |
| 系统异常 | DB 失败 | 50000 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| M03-01 | 禁止发起合并/拆分，提示稍后重试 |
| M02-05 二次验证 | 禁止执行合并/拆分 |
| M21 订阅方注册表 | 使用本地缓存，缓存无则只输出已知订阅方 |
| 01 即时匹配 | 建档继续，记录"未匹配"，进入批量匹配队列 |
| Redis | 直连 DB，互斥锁退化为 DB 行锁 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-10-20T11:00:00.123+08:00",
  "level": "INFO",
  "logger": "app.services.mpi.merge_service",
  "trace_id": "3f2a1b9c",
  "action": "MERGE_EXECUTED",
  "merge_id": "MG2026102000012",
  "primary_patient_id": 10001,
  "secondary_patient_id": 10112,
  "redirect_items": 3,
  "operator_id": 1,
  "operator_name": "信息科01",
  "result": "SUCCESS"
}
```

**禁止记录：** 完整证件号、完整手机号、版本快照中的敏感字段明文。

### 11.3 监控指标

| 指标 | 告警阈值 |
|---|---|
| 合并执行失败率 | >5% |
| 订阅方重定向失败数 | >10 |
| 重定向重试次数 | >5 |
| 批量匹配任务耗时 | >30min |
| 质量扫描耗时 | >1h |
| 质量问题率 | 突增 >50% |
| 黑名单命中次数 | 异常突增 |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 建档即时匹配 | 返回候选，同证件命中 100 分 |
| AC-02 | 即时匹配返回上限 | ≤20 条 |
| AC-03 | 批量匹配任务 | 生成候选对，任务状态可查 |
| AC-04 | 候选列表筛选 | 按等级/状态/来源筛选正确 |
| AC-05 | 候选对比详情 | 字段得分、权重、贡献正确 |
| AC-06 | 标记忽略 | 状态变 IGNORED，不再提示 |
| AC-07 | 确认同一人 | 进入合并申请 |
| AC-08 | 发起合并 | 校验通过，生成申请单 |
| AC-09 | 主从相同 | 返回 "0302003" |
| AC-10 | 主患者非 NORMAL | 返回 "0302004" |
| AC-11 | 从患者非 NORMAL/FROZEN | 返回 "0302005" |
| AC-12 | 院区不一致 | 返回 "0302006" |
| AC-13 | 已在申请中 | 返回 "0302007" |
| AC-14 | 黑名单 | 返回 "0302008" |
| AC-15 | 原因字数不足 | 返回 "0302009" |
| AC-16 | 风险等级计算 | LOW/MEDIUM/HIGH 正确 |
| AC-17 | 审批链生成 | 按风险等级正确 |
| AC-18 | 审批通过 | 状态 APPROVED |
| AC-19 | 审批驳回 | 状态 REJECTED，可修改重提 |
| AC-20 | 执行合并需二次验证 | 未验证返回 "0302013" |
| AC-21 | 执行合并 | 从患者 MERGED，版本快照保存 |
| AC-22 | 重定向清单生成 | 表名+主键+条数正确 |
| AC-23 | 合并事件发布 | 订阅方收到事件 |
| AC-24 | 订阅方上报 | 状态更新 COMPLETED/PARTIAL |
| AC-25 | 重定向重试 | 失败项自动重试 |
| AC-26 | 拆分申请 | 校验通过，生成申请单 |
| AC-27 | 拆分审批 | 需院领导 |
| AC-28 | 执行拆分 | 从患者恢复 NORMAL，不自动回迁业务数据 |
| AC-29 | 拆分工单 | 生成工单，交信息科人工处理 |
| AC-30 | 质量规则维护 | 新增/修改/启用停用 |
| AC-31 | 质量扫描 | 按规则生成问题清单 |
| AC-32 | 问题清单筛选 | 按维度/级别/状态筛选正确 |
| AC-33 | 批量指派整改 | 指派成功 |
| AC-34 | 标记已整改 | 状态 RESOLVED |
| AC-35 | 质量看板 | 指标计算正确 |
| AC-36 | 质量报告导出 | 文件内容正确 |
| AC-37 | 黑名单新增 | 校验通过 |
| AC-38 | 黑名单校验 | 内部接口命中 |
| AC-39 | 黑名单解除 | 状态 RELEASED |
| AC-40 | 配置维护 | 阈值/权重校验通过 |
| AC-41 | 配置变更影响 | 缓存刷新，下次匹配生效 |
| AC-42 | 权限控制 | 无权限 403 |
| AC-43 | 合并审计日志 | 写 `sys_audit_log` |
| AC-44 | 版本快照 | 可查看，敏感字段脱敏 |
| AC-45 | 重定向清单分页 | 1000 条以上拆分 |
| AC-46 | 订阅方注册表缓存 | 未注册表进入"待人工处理"清单 |
| AC-47 | 互斥控制 | 合并执行中并发请求被拒 |
| AC-48 | 批量匹配互斥 | 同时触发第二个被拒 |
| AC-49 | 候选过期清理 | 90 天前已忽略自动清理 |
| AC-50 | 黑名单到期解除 | 定时任务生效 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | 候选列表 | 50 并发 P95 ≤ 500ms |
| PF-02 | 候选详情 | 50 并发 P95 ≤ 300ms |
| PF-03 | 即时匹配 | 100 并发 P95 ≤ 200ms |
| PF-04 | 发起合并 | 50 并发 P95 ≤ 500ms |
| PF-05 | 执行合并 | 10 并发 P95 ≤ 2s（含版本快照） |
| PF-06 | 重定向清单查询 | 50 并发 P95 ≤ 300ms |
| PF-07 | 质量扫描 1 万患者 | ≤ 10min |
| PF-08 | 批量匹配 1 万患者 | ≤ 30min |
| PF-09 | 长稳 72h | 无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | 合并事件 100% 投递 | — |
| DA-02 | 版本快照 100% 保存 | — |
| DA-03 | 重定向清单 100% 生成 | — |
| DA-04 | 合并日志 100% 留痕 | — |
| DA-05 | 质量问题 100% 可定位 | — |
| DA-06 | 黑名单 100% 生效 | — |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | 未授权合并 | 403 + 审计 |
| SC-02 | 无二次验证执行合并 | 52113 |
| SC-03 | 明文敏感字段泄漏 | 0 处 |
| SC-04 | 版本快照敏感字段 | 加密存储 |
| SC-05 | 重定向清单敏感字段 | 不返回 |
| SC-06 | 内部接口公网暴露 | 禁止 |
| SC-07 | 黑名单绕过 | 校验必命中 |
| SC-08 | 合并/拆分操作审计 | 100% 写 `sys_audit_log` |

---

## 附录 A：候选对状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| PENDING | 标记忽略 | IGNORED | 信息科 |
| PENDING | 确认同一人 | CONFIRMED | 信息科 |
| CONFIRMED | 发起合并 | IN_MERGE | 信息科 |
| IN_MERGE | 合并成功 | MERGED | 系统 |
| IN_MERGE | 合并驳回 | PENDING | 系统 |
| IGNORED | 90 天清理 | DELETED | 定时任务 |

## 附录 B：合并申请状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| DRAFT | 提交审批 | PENDING | 申请人 |
| PENDING | 审批通过 | APPROVED | 审批人 |
| PENDING | 审批驳回 | REJECTED | 审批人 |
| PENDING | 撤回 | WITHDRAWN | 申请人 |
| APPROVED | 执行合并 | EXECUTED | 信息科 |
| APPROVED | 执行失败 | FAILED | 系统 |
| EXECUTED | 发起拆分 | SPLIT_PENDING | 信息科 |

## 附录 C：风险等级与审批链

| 风险 | 条件 | 审批链 |
|---|---|---|
| LOW | 单据 ≤10 且金额 ≤1000 | 信息科长 |
| MEDIUM | 单据 11~100 或 金额 1001~50000 | 信息科长 → 医务科长 |
| HIGH | 单据 >100 或 金额 >50000 或 涉及住院/手术/屈光 | 信息科长 → 医务科长 → 财务科长 → 院领导 |

## 附录 D：质量规则预置

| 编码 | 名称 | 维度 | 级别 | 条件 |
|---|---|---|---|---|
| `QR-COMP-01` | 姓名必填 | 完整性 | ERROR | `patient_name IS NOT NULL` |
| `QR-COMP-02` | 性别必填 | 完整性 | ERROR | `gender IN ('MALE','FEMALE')` |
| `QR-COMP-03` | 出生日期必填 | 完整性 | WARN | `birth_date IS NOT NULL` |
| `QR-COMP-04` | 主证件必填 | 完整性 | ERROR | `primary_id_type IS NOT NULL` |
| `QR-COMP-05` | 手机号必填（VIP） | 完整性 | WARN | `patient_type='VIP' AND primary_phone_hash IS NOT NULL` |
| `QR-UNIQ-01` | 主证件唯一 | 唯一性 | ERROR | 主证件哈希全局唯一 |
| `QR-UNIQ-02` | 姓名+手机疑似重复 | 唯一性 | WARN | 姓名拼音 + 手机号哈希相同 |
| `QR-FORM-01` | 手机号格式 | 规范性 | WARN | `^1[3-9]\d{9}$` |
| `QR-FORM-02` | 证件号格式 | 规范性 | WARN | 按证件类型校验 |
| `QR-FORM-03` | 出生日期合理 | 规范性 | WARN | `birth_date BETWEEN '1900-01-01' AND today` |
| `QR-TIME-01` | 超 5 年未就诊 | 时效性 | INFO | `last_visit_at < now - 5 years` |
| `QR-TIME-02` | 超 1 年未更新 | 时效性 | INFO | `updated_at < now - 1 year` |

## 附录 E：系统参数（M01 `md_sys_param`）

| 参数编码 | 默认值 | 说明 |
|---|---|---|
| `MPI.MATCH.THRESHOLD.HIGH` | `95` | 高候选阈值 |
| `MPI.MATCH.THRESHOLD.MEDIUM` | `80` | 中候选阈值 |
| `MPI.MATCH.THRESHOLD.LOW` | `60` | 低候选阈值 |
| `MPI.MATCH.INSTANT.ENABLED` | `true` | 建档即时匹配 |
| `MPI.MATCH.INSTANT.LIMIT` | `5` | 即时匹配返回上限 |
| `MPI.MATCH.BATCH.CRON` | `0 3 * * *` | 批量匹配 Cron |
| `MPI.MATCH.BATCH.MAX_ROWS` | `100000` | 单次批量匹配上限 |
| `MPI.MERGE.SECOND_FACTOR` | `true` | 执行合并需二次验证 |
| `MPI.SPLIT.SECOND_FACTOR` | `true` | 执行拆分需二次验证 |
| `MPI.QUALITY.SCAN.CRON` | `0 2 * * *` | 质量扫描 Cron |
| `MPI.QUALITY.SLA_DAYS` | `7` | 整改 SLA |
| `MPI.REDIRECT.MAX_IDS_PER_ITEM` | `1000` | 单条重定向清单上限 |

## 附录 F：术语表

| 术语 | 说明 |
|---|---|
| 候选对 | 两个疑似同一患者的组合 |
| 匹配得分 | 0~100 的相似度总分 |
| 主患者 | 合并后保留的患者 |
| 从患者 | 合并后标记 MERGED 的患者 |
| 重定向清单 | 需要订阅方更新的业务表 + 主键列表 |
| 风险等级 | 合并影响评估结果 |
| 患者版本快照 | 合并/拆分前保存的完整数据副本 |
| 黑名单 | 禁止合并/引用的患者列表 |
| 整改工单 | 质量问题指派给责任人的任务 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：页面 11 个、数据表 13 张、接口 45 个 | 系统设计组 |