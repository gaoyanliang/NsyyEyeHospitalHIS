# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块：随访（Follow-up）详细设计

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI（子模块编号 M03-04 随访）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M01 主数据管理MDM》《M02 统一权限与安全》《M03 患者服务与EMPI 01 患者主索引与建档》《M03 患者服务与EMPI 02 患者匹配合并与质量》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery / APScheduler
**文档用途：** 作为随访模板、随访计划、任务生成与分派子模块开发、测试、验收依据；作为 M19 随访执行、M03-05 消息、M03-06 门户的随访任务来源

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

随访回答两个问题：**“这类患者应该在什么时间、以什么方式、随访什么内容？”**、**“这个患者当前有哪些待执行随访任务？”**

本子模块建立全院统一的随访模板与随访计划，按模板节点自动生成随访任务，并把任务分派给执行科室/执行人。**任务的执行（电话、微信、门诊、上门）、结果填写、外呼记录、随访运营归 M19**；本模块只负责“计划与任务的生产与分派”，不负责“任务的执行与结果”。

**边界一句话：** 本子模块只管“随访模板、随访计划、任务生成、任务分派规则、任务状态与逾期监控”；**不做**电话外呼、问卷填写、随访结果归档、随访运营分析（这些归 M19），**不做**消息发送（M03-05），**不做**患者门户页面（M03-06）。

### 1.2 与 01/02/03/M19 的分工

| 能力 | 归属 | 说明 |
|---|---|---|
| 患者主档、联系方式 | M03-01 | 本子模块只读引用 |
| 患者合并、主索引重定向 | M03-02 | 合并后计划/任务 `patient_id` 重定向由本模块订阅事件处理 |
| 会员等级、权益 | M03-03 | 随访模板可按会员等级差异化（可选） |
| **随访模板、模板节点** | **M03-04 本子模块** | — |
| **随访计划、计划生成** | **M03-04 本子模块** | — |
| **随访任务生成、分派规则、任务状态** | **M03-04 本子模块** | — |
| 随访任务执行、外呼、结果填写 | M19 | 通过内部接口拉取任务、回写结果 |
| 随访结果归档、随访运营分析 | M19 | — |
| 消息模板、发送、回执 | M03-05 | 本模块只产生“任务待执行”事件 |
| 患者端随访问卷 | M03-06 | 本模块只提供任务与问卷结构 |

### 1.3 模块目标

- **模板可配置**：随访节点、时间偏移、随访方式、随访内容、执行科室集中配置。
- **计划自动生成**：按模板 + 触发事件（手术/出院/建档/诊断）自动生成计划与任务。
- **任务可分派**：按科室、医生、随访组、轮询规则分派；支持手动调整。
- **逾期可监控**：任务到期未执行自动标记逾期，支持升级提醒。
- **合并友好**：患者合并后计划/任务 `patient_id` 自动重定向，执行中的任务记录冲突日志。
- **执行与生产分离**：M19 只消费任务、回写结果，不直写本模块计划表。

### 1.4 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 医务科 | 随访模板治理 | 模板新增/修改/启用停用 |
| 护理部/随访组 | 计划与任务监控 | 查看计划、手动生成计划、调整分派 |
| 信息科 | 配置与治理 | 分派规则、配置、日志审计 |
| M19 随访执行 | 任务执行 | 拉取任务、回写结果、取消任务 |
| 科室负责人 | 本科室任务监控 | 查看本科室任务、逾期任务 |
| 审计员 | 追溯 | 模板/计划/任务变更日志 |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 随访模板 | 模板主档、适用条件、状态 |
| 模板节点 | 节点名称、触发方式、时间偏移、随访方式、随访内容、执行科室、优先级、是否必做 |
| 模板变更日志 | 模板全量变更留痕 |
| 随访计划 | 计划主档、患者关联、来源（手术/出院/建档/诊断/手动）、状态 |
| 计划生成 | 按模板 + 触发事件生成计划与任务；支持手动生成 |
| 随访任务 | 任务主档、计划节点快照、计划执行日期、状态、分派人、执行科室 |
| 任务分派规则 | 按科室/医生/随访组/轮询 |
| 任务状态日志 | 任务状态流转留痕 |
| 计划变更日志 | 计划全量变更留痕 |
| 任务逾期监控 | 到期未执行标记逾期、升级提醒 |
| 内部契约 | M19 拉取任务、回写结果、取消任务；M03-02 合并重定向 |
| 配置 | 任务提前生成天数、逾期判定、分派默认规则、编码规则 |

### 2.2 范围外

| 范围外内容 | 负责方 |
|---|---|
| 电话外呼、微信随访、短信发送 | M19 / M03-05 |
| 随访问卷填写、结果归档 | M19 |
| 随访运营分析、随访率统计 | M19 |
| 患者端随访问卷页面 | M03-06 |
| 手术、出院、诊断业务事件产生 | M09/M05/M07 |
| 患者合并执行 | M03-02 |
| 会员权益 | M03-03 |

### 2.3 与相邻模块分工

```text
M09 手术 / M05 出院 / M07 诊断 / M03-01 建档
        │ 触发事件
        ▼
M03-04 随访 ── 模板 + 计划 + 任务生成 ──► M19 随访执行
        │                                      │
        │ 任务状态回写                           │ 执行结果回写
        ◄──────────────────────────────────────┘
        │
        ├── 任务待执行事件 ──► M03-05 消息
        ├── 患者合并事件 ◄── M03-02
        └── 会员等级（可选）◄── M03-03
```

**关键约定：**
- 计划与任务的 `patient_id` 由 M03-01 提供，合并后由本模块订阅 `mpi.patient.merged` 更新。
- M19 不直写 `mpi_followup_plan` / `mpi_followup_task`，只能通过内部接口拉取与回写。
- 任务执行中的结果字段（如随访结果、外呼记录）不在本模块表结构内，归 M19。
- 本模块只记录任务“状态”，不记录“执行内容”。

### 2.4 依赖清单（对 01/02/03/M01/M02）

| 依赖方 | 依赖内容 | 用途 |
|---|---|---|
| M03-01 患者 | `mpi_patient` / `mpi_patient_contact` | 计划/任务关联患者、读取姓名/手机号掩码 |
| M03-01 内部接口 | `GET /internal/v1/patient/{id}/brief` | 任务详情展示 |
| M03-02 事件 | `mpi.patient.merged` | 更新计划/任务 `patient_id` |
| M03-03 会员 | 会员等级（可选） | 模板按等级差异化 |
| M01 字典 | `md_dict_item` / `md_dict_type` | 随访方式、触发方式、任务状态等枚举 |
| M01 参数 | `md_sys_param` | 任务提前生成天数、逾期天数、编码前缀 |
| M01 职工/科室 | `mdm_employee` / `mdm_department` | 执行科室、执行人、分派规则、数据权限 |
| M02 账号 | `sys_account` | 操作人 |
| M02 权限 | `mpi:followup:*` 权限码 | 页面/接口鉴权 |
| M02 审计 | `sys_audit_log` | 模板/计划/任务关键操作审计 |
| M20 消息 | 短信/站内信 | 逾期提醒（可降级） |

---

## 3. 业务模型

### 3.1 随访模板状态机

```text
DRAFT ──提交/启用──► ENABLED ──停用──► DISABLED
  ▲                    │                 │
  └──────编辑───────────┘                 │
  ▲                                       │
  └──────────────启用─────────────────────┘
```

| 状态 | 代码 | 说明 | 能否生成计划 |
|---|---|---|---|
| 草稿 | `DRAFT` | 编辑中 | 否 |
| 启用 | `ENABLED` | 可生成计划 | 是 |
| 停用 | `DISABLED` | 不再生成新计划，历史计划不受影响 | 否 |

### 3.2 模板节点触发方式

| 触发方式 | 代码 | 基准日期 | 说明 |
|---|---|---|---|
| 相对手术日期 | `SURGERY_DATE` | 手术日期 | 术后随访 |
| 相对出院日期 | `DISCHARGE_DATE` | 出院日期 | 出院后随访 |
| 相对建档日期 | `REGISTER_DATE` | 患者建档日期 | 慢病/长期随访 |
| 相对诊断日期 | `DIAGNOSIS_DATE` | 诊断日期 | 诊断后随访 |
| 固定日期 | `FIXED_DATE` | 指定日期 | 活动/专项随访 |
| 周期 | `CYCLE` | 起始日期 + 周期 | 长期规律随访 |

节点字段：`offset_days`（相对基准日期的偏移天数，可为负）、`offset_hours`（可选）、`cycle_days`（周期）、`max_occurrences`（最大次数）。

### 3.3 随访方式

| 方式 | 代码 | 说明 |
|---|---|---|
| 电话 | `PHONE` | 电话外呼 |
| 微信 | `WECHAT` | 公众号/企微 |
| 短信 | `SMS` | 短信 |
| 门诊 | `OUTPATIENT` | 预约门诊复查 |
| 上门 | `HOME_VISIT` | 上门随访 |
| 混合 | `MIXED` | 多种方式组合 |
| 患者端 | `PATIENT_APP` | 患者端问卷 |

### 3.4 随访计划状态机

```text
DRAFT ──激活──► ACTIVE ──完成──► COMPLETED
  │               │
  │               ├──取消──► CANCELLED
  │               └──全部任务完成/终止──► COMPLETED
  └──删除──► (逻辑删除)
```

| 状态 | 代码 | 说明 |
|---|---|---|
| 草稿 | `DRAFT` | 手动生成未激活 |
| 进行中 | `ACTIVE` | 任务可执行 |
| 已完成 | `COMPLETED` | 所有节点已完成或计划终止 |
| 已取消 | `CANCELLED` | 计划取消，未执行任务同步取消 |

### 3.5 随访任务状态机

```text
PENDING ──分派──► ASSIGNED ──M19开始执行──► EXECUTING ──完成──► COMPLETED
   │                  │                         │
   │                  ├──取消──► CANCELLED      ├──失败──► FAILED
   │                  │                         │
   │                  └──逾期──► OVERDUE ──完成──► COMPLETED
   │
   └──计划取消──► CANCELLED
```

| 状态 | 代码 | 说明 | 是否可执行 |
|---|---|---|---|
| 待分派 | `PENDING` | 任务已生成，未分派 | 否 |
| 已分派 | `ASSIGNED` | 已指定执行科室/执行人 | 是 |
| 执行中 | `EXECUTING` | M19 已开始执行 | 是 |
| 已完成 | `COMPLETED` | M19 回写完成 | 否 |
| 已取消 | `CANCELLED` | 计划取消/手动取消 | 否 |
| 逾期 | `OVERDUE` | 超过计划日期未完成 | 是（可补执行） |
| 执行失败 | `FAILED` | M19 回写失败 | 否 |

### 3.6 任务分派规则

| 规则类型 | 代码 | 说明 |
|---|---|---|
| 按科室 | `BY_DEPT` | 分派到指定科室，由科室再分派 |
| 按医生 | `BY_DOCTOR` | 分派到原主刀/主管医生 |
| 按随访组 | `BY_GROUP` | 分派到指定随访组（M01 用户组） |
| 轮询 | `ROUND_ROBIN` | 在指定人员集合中轮询 |
| 手动 | `MANUAL` | 不自动分派，由护士手动分派 |

分派规则可按模板节点配置，未配置时使用全局默认规则。

### 3.7 任务生成时机

- **预生成**：计划创建/激活时，按模板节点预生成全部任务，状态 `PENDING`，`plan_date` 为计划执行日期。
- **可执行窗口**：任务在 `plan_date - advance_days` 天进入可执行（`ASSIGNED` 或 `PENDING` 可被 M19 拉取），`advance_days` 由配置决定。
- **逾期判定**：`plan_date + overdue_days` 天后仍未完成，定时任务标记 `OVERDUE`。
- **周期节点**：按 `cycle_days` 生成多次任务，最多 `max_occurrences` 次。

### 3.8 患者合并联动

- 订阅 `mpi.patient.merged` 事件。
- 更新 `mpi_followup_plan.patient_id` 与 `mpi_followup_task.patient_id`。
- 若任务处于 `EXECUTING`，记录 `MERGE_CONFLICT` 日志，不自动改派，交人工确认。
- 若主患者已有相同模板的进行中计划，记录冲突，交人工合并计划。

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [随访数据结构](M03_患者服务与EMPI_04_随访_数据结构.md)

本章原包含 **10 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 随访模块完整数据结构 | [随访数据结构](M03_患者服务与EMPI_04_随访_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```text
患者服务与EMPI
└── 随访
    ├── P01 随访模板列表
    ├── P02 随访模板编辑
    ├── P03 随访计划列表
    ├── P04 随访计划详情/任务列表
    ├── P05 生成随访计划
    ├── P06 随访任务监控
    ├── P07 分派规则配置
    ├── P08 随访配置
    └── P09 变更日志
```

### 5.2 P01 随访模板列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：患者服务与EMPI / 随访 / 随访模板                       用户：医务科01 ▾ │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：模板总数 32 | 启用 18 | 草稿 6 | 停用 8                              │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：关键字[模板编码/名称] 适用场景[全部▼] 状态[全部▼] 科室[全部▼]            │
│ 工具栏：[＋新建模板] [导出]                                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │模板编码      │模板名称          │适用场景    │节点数│状态  │更新时间      │操作│
│ ☐ │FT-OP-CAT-01  │白内障术后随访    │手术        │5    │启用  │2026-10-01    │··· │
│ ☐ │FT-DIS-01     │出院后随访        │出院        │3    │启用  │2026-09-20    │··· │
│ ☐ │FT-CHR-01     │慢病长期随访      │建档/诊断   │12   │启用  │2026-08-15    │··· │
│ ☐ │FT-SAT-01     │满意度调查        │手动        │1    │草稿  │2026-10-10    │··· │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 32 条                                          [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**操作：** 查看、编辑、复制、启用/停用、查看日志。

### 5.3 P02 随访模板编辑

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 编辑随访模板：白内障术后随访（FT-OP-CAT-01）                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【基本信息】                                                                    │
│ 模板编码：[FT-OP-CAT-01]  模板名称：[白内障术后随访________]                    │
│ 适用场景：[手术 ▼]  适用手术：[白内障超声乳化+人工晶体植入术 ▼]                 │
│ 适用科室：[眼科一病区 ▼]  会员等级限制：[不限 ▼]                                │
│ 是否启用：[✓]  备注：[________________________________]                        │
│                                                                                │
│ 【随访节点】                                                                    │
│ [+ 添加节点]                                                                    │
│ ┌────┬──────────┬──────────┬──────┬────────┬──────────┬──────────┬──────┐    │
│ │序号│节点名称  │触发方式  │偏移天│随访方式│执行科室  │分派规则  │操作  │    │
│ ├────┼──────────┼──────────┼──────┼────────┼──────────┼──────────┼──────┤    │
│ │1   │术后1天   │手术日期  │1     │电话    │眼科一病区│按主刀医生│[编辑]│    │
│ │2   │术后1周   │手术日期  │7     │门诊    │白内障科  │按科室    │[编辑]│    │
│ │3   │术后1月   │手术日期  │30    │门诊    │白内障科  │按科室    │[编辑]│    │
│ │4   │术后3月   │手术日期  │90    │门诊    │白内障科  │按科室    │[编辑]│    │
│ │5   │术后6月   │手术日期  │180   │电话/微信│随访组    │按随访组  │[编辑]│    │
│ └────┴──────────┴──────────┴──────┴────────┴──────────┴──────────┴──────┘    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [取消] [保存草稿] [启用模板]                                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

**节点编辑抽屉：**

| 字段 | 控件 | 必填 | 说明 |
|---|---|---|---|
| 节点名称 | 文本 | 是 | ≤64 字 |
| 触发方式 | 下拉 | 是 | SURGERY_DATE/DISCHARGE_DATE/REGISTER_DATE/DIAGNOSIS_DATE/FIXED_DATE/CYCLE |
| 偏移天数 | 数字 | 条件 | 相对触发日期，可为负 |
| 周期天数 | 数字 | 条件 | CYCLE 时必填 |
| 最大次数 | 数字 | 条件 | CYCLE 时必填 |
| 随访方式 | 多选 | 是 | PHONE/WECHAT/SMS/OUTPATIENT/HOME_VISIT/PATIENT_APP |
| 随访内容 | 文本/JSON | 否 | 问卷/检查项/用药提醒 |
| 执行科室 | 科室选择器 | 是 | — |
| 执行人要求 | 下拉 | 否 | 原主刀/主管医生/不限 |
| 分派规则 | 下拉 | 是 | BY_DEPT/BY_DOCTOR/BY_GROUP/ROUND_ROBIN/MANUAL |
| 优先级 | 下拉 | 是 | HIGH/NORMAL/LOW |
| 是否必做 | 开关 | 是 | 否=可选任务 |
| 提前生成天数 | 数字 | 否 | 覆盖全局配置 |
| 备注 | 文本 | 否 | — |

### 5.4 P03 随访计划列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 随访计划                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：进行中 1,205 | 今日待执行 86 | 逾期 12 | 已完成 3,420                 │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：患者[姓名/EMPI/手机号] 模板[全部▼] 状态[全部▼] 来源[手术/出院/手动▼]      │
│ 计划日期[____ ~ ____]  工具栏：[＋手动生成计划] [导出]                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │计划号        │患者          │模板            │来源  │状态  │任务进度│操作│
│ ☐ │FP20261020001 │P202610200001 王五│白内障术后随访│手术  │进行中│2/5    │··· │
│ ☐ │FP20261020002 │P202610200002 李四│出院后随访    │出院  │进行中│0/3    │··· │
│ ☐ │FP20261020003 │P202610200003 张三│慢病长期随访  │建档  │已完成│12/12  │··· │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 1,205 条                                       [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 P04 随访计划详情/任务列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 随访计划：FP20261020001  王五  白内障术后随访              状态：进行中        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【计划信息】                                                                    │
│ 来源：手术（S202610200001）  基准日期：2026-10-20  创建人：系统                 │
│ 患者：P202610200001 王五  手机号：138****5678                                    │
│                                                                                │
│ 【任务列表】                                                                    │
│ 序号│节点名称  │计划日期  │随访方式│执行科室  │分派人│状态    │完成时间  │操作│
│ 1   │术后1天   │2026-10-21│电话    │眼科一病区│张三  │已完成  │10-21 10:00│··· │
│ 2   │术后1周   │2026-10-27│门诊    │白内障科  │李四  │执行中  │—          │··· │
│ 3   │术后1月   │2026-11-19│门诊    │白内障科  │—     │待分派  │—          │··· │
│ 4   │术后3月   │2027-01-18│门诊    │白内障科  │—     │待分派  │—          │··· │
│ 5   │术后6月   │2027-04-18│电话/微信│随访组    │—     │待分派  │—          │··· │
├────────────────────────────────────────────────────────────────────────────────┤
│ [调整分派] [取消计划] [查看日志]                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 P05 生成随访计划

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 手动生成随访计划                                                                │
├────────────────────────────────────────────────────────────────────────────────┤
│ 患者：[选择患者 ▼]  P202610200001 王五  手机号：138****5678                      │
│ 模板：[白内障术后随访 ▼]                                                        │
│ 触发方式：[手术 ▼]  基准日期：[2026-10-20]  关联业务单号：[S202610200001]       │
│ 是否立即激活：[✓]                                                              │
│                                                                                │
│ 预览任务：                                                                      │
│ 1. 术后1天   2026-10-21  电话   眼科一病区                                      │
│ 2. 术后1周   2026-10-27  门诊   白内障科                                        │
│ 3. 术后1月   2026-11-19  门诊   白内障科                                        │
│ 4. 术后3月   2027-01-18  门诊   白内障科                                        │
│ 5. 术后6月   2027-04-18  电话/微信 随访组                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│                                      [取消] [生成计划]                          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.7 P06 随访任务监控

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 随访任务监控                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：待分派 320 | 已分派 860 | 执行中 120 | 逾期 12 | 今日完成 86          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：执行科室[全部▼] 分派人[全部▼] 状态[全部▼] 计划日期[今日/本周/逾期]        │
│ 工具栏：[批量分派] [导出]                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │任务号        │患者          │节点      │计划日期  │执行科室  │分派人│状态  │操作│
│ ☐ │FT20261021001 │P202610200001 王五│术后1天│2026-10-21│眼科一病区│张三  │已完成│··· │
│ ☐ │FT20261027002 │P202610200001 王五│术后1周│2026-10-27│白内障科  │李四  │执行中│··· │
│ ☐ │FT20261119003 │P202610200001 王五│术后1月│2026-11-19│白内障科  │—     │待分派│··· │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 1,312 条                                       [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.8 P07 分派规则配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 分派规则配置                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 默认分派规则：[按科室 ▼]                                                        │
│ 默认执行科室：[随访组 ▼]                                                        │
│ 轮询人员集合：[张三、李四、王五 ▼]                                              │
│ 分派后是否通知：[✓ 站内信]  [✓ 短信]                                            │
│                                                                                │
│ 规则列表：                                                                      │
│ 规则编码│规则名称    │类型      │执行科室/人员      │优先级│启用│操作            │
│ AR-01   │白内障术后  │按医生    │原主刀医生         │10    │是  │[编辑]          │
│ AR-02   │出院随访    │按科室    │随访组             │20    │是  │[编辑]          │
│ AR-03   │慢病随访    │轮询      │张三、李四、王五   │30    │是  │[编辑]          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.9 P08 随访配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 随访配置                                        ⚠ 修改影响全院随访任务生成      │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【任务生成】                                                                    │
│ 任务提前生成天数：[30] 天（任务在计划日期前 N 天进入可执行）                     │
│ 逾期判定天数：[7] 天（计划日期后 N 天未完成标记逾期）                           │
│ 周期任务最大次数：[24] 次                                                       │
│                                                                                │
│ 【分派】                                                                        │
│ 默认分派规则：[按科室 ▼]                                                        │
│ 默认执行科室：[随访组 ▼]                                                        │
│ 分派后通知：[✓ 站内信]  [✓ 短信]                                                │
│                                                                                │
│ 【合并联动】                                                                    │
│ ☑ 订阅患者合并事件，自动更新计划/任务 patient_id                                │
│                                                                                │
│ 【编码规则】                                                                    │
│ 模板前缀：[FT]  计划前缀：[FP]  任务前缀：[FTK]  流水位数：[4]                  │
├────────────────────────────────────────────────────────────────────────────────┤
│                                         [取消] [保存]                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.10 P09 变更日志

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 随访变更日志                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：对象类型[模板/计划/任务▼] 对象编码[____] 操作[全部▼] 时间[____ ~ ____]    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 时间                │对象类型│对象编码      │操作        │操作人│详情            │
│ 2026-10-20 10:00:00 │模板    │FT-OP-CAT-01  │UPDATE      │医务科│修改节点偏移    │
│ 2026-10-20 10:05:00 │计划    │FP20261020001 │CREATE      │系统  │手术触发自动生成│
│ 2026-10-21 10:00:00 │任务    │FT20261021001 │COMPLETE    │M19   │M19 回写完成    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| **模板** | | | | |
| API-01 | GET | `/api/v1/mpi/followup/templates` | 模板分页列表 | `mpi:followup:template:list` |
| API-02 | GET | `/api/v1/mpi/followup/templates/{id}` | 模板详情 | `mpi:followup:template:list` |
| API-03 | POST | `/api/v1/mpi/followup/templates` | 新建模板 | `mpi:followup:template:create` |
| API-04 | PUT | `/api/v1/mpi/followup/templates/{id}` | 修改模板 | `mpi:followup:template:update` |
| API-05 | POST | `/api/v1/mpi/followup/templates/{id}/enable` | 启用模板 | `mpi:followup:template:update` |
| API-06 | POST | `/api/v1/mpi/followup/templates/{id}/disable` | 停用模板 | `mpi:followup:template:update` |
| API-07 | POST | `/api/v1/mpi/followup/templates/{id}/copy` | 复制模板 | `mpi:followup:template:create` |
| API-08 | DELETE | `/api/v1/mpi/followup/templates/{id}` | 删除模板（仅草稿） | `mpi:followup:template:update` |
| API-09 | GET | `/api/v1/mpi/followup/templates/{id}/nodes` | 模板节点列表 | `mpi:followup:template:list` |
| API-10 | PUT | `/api/v1/mpi/followup/templates/{id}/nodes` | 批量保存节点 | `mpi:followup:template:update` |
| **计划** | | | | |
| API-11 | GET | `/api/v1/mpi/followup/plans` | 计划分页列表 | `mpi:followup:plan:list` |
| API-12 | GET | `/api/v1/mpi/followup/plans/{id}` | 计划详情 | `mpi:followup:plan:list` |
| API-13 | POST | `/api/v1/mpi/followup/plans` | 手动生成计划 | `mpi:followup:plan:create` |
| API-14 | POST | `/api/v1/mpi/followup/plans/{id}/cancel` | 取消计划 | `mpi:followup:plan:update` |
| API-15 | GET | `/api/v1/mpi/followup/plans/{id}/tasks` | 计划任务列表 | `mpi:followup:plan:list` |
| API-16 | GET | `/api/v1/mpi/followup/plans/statistics` | 计划统计 | `mpi:followup:plan:list` |
| **任务** | | | | |
| API-17 | GET | `/api/v1/mpi/followup/tasks` | 任务分页列表 | `mpi:followup:task:list` |
| API-18 | GET | `/api/v1/mpi/followup/tasks/{id}` | 任务详情 | `mpi:followup:task:list` |
| API-19 | POST | `/api/v1/mpi/followup/tasks/{id}/assign` | 手动分派 | `mpi:followup:task:assign` |
| API-20 | POST | `/api/v1/mpi/followup/tasks/batch-assign` | 批量分派 | `mpi:followup:task:assign` |
| API-21 | POST | `/api/v1/mpi/followup/tasks/{id}/cancel` | 取消任务 | `mpi:followup:task:update` |
| API-22 | GET | `/api/v1/mpi/followup/tasks/statistics` | 任务统计 | `mpi:followup:task:list` |
| API-23 | GET | `/api/v1/mpi/followup/tasks/overdue` | 逾期任务列表 | `mpi:followup:task:list` |
| **分派规则** | | | | |
| API-24 | GET | `/api/v1/mpi/followup/assign-rules` | 规则列表 | `mpi:followup:rule:list` |
| API-25 | POST | `/api/v1/mpi/followup/assign-rules` | 新增规则 | `mpi:followup:rule:update` |
| API-26 | PUT | `/api/v1/mpi/followup/assign-rules/{id}` | 修改规则 | `mpi:followup:rule:update` |
| API-27 | DELETE | `/api/v1/mpi/followup/assign-rules/{id}` | 删除规则 | `mpi:followup:rule:update` |
| **配置** | | | | |
| API-28 | GET | `/api/v1/mpi/followup/config` | 查询配置 | `mpi:followup:config:list` |
| API-29 | PUT | `/api/v1/mpi/followup/config` | 修改配置 | `mpi:followup:config:update` |
| **日志** | | | | |
| API-30 | GET | `/api/v1/mpi/followup/logs` | 变更日志 | `mpi:followup:audit` |
| **内部契约** | | | | |
| API-31 | POST | `/internal/v1/followup/plans/trigger` | 业务事件触发计划生成 | 内部服务 |
| API-32 | GET | `/internal/v1/followup/tasks/pending` | M19 拉取待执行任务 | 内部服务 |
| API-33 | POST | `/internal/v1/followup/tasks/{id}/result` | M19 回写任务结果 | 内部服务 |
| API-34 | POST | `/internal/v1/followup/tasks/{id}/start` | M19 开始执行 | 内部服务 |
| API-35 | POST | `/internal/v1/followup/merge-redirect` | 患者合并重定向 | 内部服务 |
| API-36 | GET | `/internal/v1/followup/plans/by-patient/{patient_id}` | 按患者查计划 | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码（M03-04：52301~52340）**

| 错误码 | 含义 |
|---|---|
| 52301 | 模板不存在 |
| 52302 | 模板编码已存在 |
| 52303 | 模板状态不允许该操作 |
| 52304 | 模板节点为空 |
| 52305 | 模板节点偏移非法 |
| 52306 | 模板节点周期配置非法 |
| 52307 | 模板已被计划引用，不能删除 |
| 52308 | 计划不存在 |
| 52309 | 计划状态不允许该操作 |
| 52310 | 患者不存在或状态异常 |
| 52311 | 模板未启用，不能生成计划 |
| 52312 | 触发方式与业务单号不匹配 |
| 52313 | 任务不存在 |
| 52314 | 任务状态不允许该操作 |
| 52315 | 执行科室非法 |
| 52316 | 执行人非法 |
| 52317 | 分派规则不存在 |
| 52318 | 分派规则类型非法 |
| 52319 | 分派规则轮询人员为空 |
| 52320 | 配置项非法 |
| 52321 | 任务编码生成失败 |
| 52322 | 计划编码生成失败 |
| 52323 | 合并重定向失败 |
| 52324 | 合并冲突 |
| 52325 | M19 回写状态非法 |
| 52326 | M19 回写结果缺少必填字段 |
| 52327 | 任务已取消，不能回写 |
| 52328 | 任务已完成，不能重复回写 |
| 52329 | 任务未到可执行时间 |
| 52330 | 拉取任务参数非法 |
| 52331 | 数据已变更，请刷新后重试 |
| 52332 | M03-01 患者服务不可用 |
| 52333 | M02 权限服务不可用 |
| 52334 | 任务逾期升级提醒失败 |
| 52335 | 模板复制失败 |
| 52336 | 计划任务预生成失败 |
| 52337 | 分派通知发送失败 |
| 52338 | 导出数据量超限 |
| 52339 | 批量操作数量超限 |
| 52340 | 任务计划日期非法 |

### 6.3 关键接口示例

#### API-01 模板分页列表

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 3001,
        "template_code": "FT-OP-CAT-01",
        "template_name": "白内障术后随访",
        "scene": "SURGERY",
        "node_count": 5,
        "status": "ENABLED",
        "updated_at": "2026-10-01T09:00:00"
      }
    ],
    "total": 32,
    "page": 1,
    "page_size": 20,
    "pages": 2
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-03 新建模板

```json
{
  "template_code": "FT-OP-CAT-01",
  "template_name": "白内障术后随访",
  "scene": "SURGERY",
  "apply_operation_ids": [101, 102],
  "apply_dept_ids": [15],
  "member_level_limit": null,
  "remark": "白内障术后标准随访",
  "nodes": [
    {
      "node_seq": 1,
      "node_name": "术后1天",
      "trigger_type": "SURGERY_DATE",
      "offset_days": 1,
      "followup_methods": ["PHONE"],
      "exec_dept_id": 15,
      "assign_rule_code": "AR-01",
      "priority": "HIGH",
      "is_required": true
    }
  ]
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 3001,
    "template_code": "FT-OP-CAT-01",
    "template_name": "白内障术后随访",
    "status": "DRAFT",
    "node_count": 1
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-13 手动生成计划

```json
{
  "patient_id": 10001,
  "template_code": "FT-OP-CAT-01",
  "trigger_type": "SURGERY_DATE",
  "base_date": "2026-10-20",
  "biz_no": "S202610200001",
  "activate": true
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": 5001,
    "plan_no": "FP20261020001",
    "patient_id": 10001,
    "template_code": "FT-OP-CAT-01",
    "status": "ACTIVE",
    "task_count": 5,
    "first_task_date": "2026-10-21"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-31 业务事件触发计划生成（内部）

```json
{
  "event_type": "SURGERY_COMPLETED",
  "patient_id": 10001,
  "template_code": "FT-OP-CAT-01",
  "trigger_type": "SURGERY_DATE",
  "base_date": "2026-10-20",
  "biz_no": "S202610200001",
  "biz_context": {
    "operation_id": 101,
    "dept_id": 15,
    "surgeon_id": 1024
  }
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "plan_id": 5001,
    "plan_no": "FP20261020001",
    "created": true,
    "task_count": 5
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-32 M19 拉取待执行任务

```
GET /internal/v1/followup/tasks/pending?dept_id=15&assignee_id=1024&date_from=2026-10-20&date_to=2026-10-27&page=1&page_size=100
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "task_id": 7001,
        "task_no": "FTK20261021001",
        "plan_no": "FP20261020001",
        "patient_id": 10001,
        "empi_no": "P202610200001",
        "patient_name": "王五",
        "phone_mask": "138****5678",
        "node_name": "术后1天",
        "followup_methods": ["PHONE"],
        "plan_date": "2026-10-21",
        "exec_dept_id": 15,
        "assignee_id": 1024,
        "priority": "HIGH",
        "status": "ASSIGNED"
      }
    ],
    "total": 86,
    "page": 1,
    "page_size": 100,
    "pages": 1
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-33 M19 回写任务结果

```json
{
  "status": "COMPLETED",
  "executed_at": "2026-10-21T10:00:00",
  "executed_by": 1024,
  "executed_by_name": "张三",
  "result_summary": "患者恢复良好，无不适",
  "detail": {
    "call_duration": 180,
    "questionnaire": {"vision": "良好", "pain": "无"}
  }
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 7001,
    "task_no": "FTK20261021001",
    "status": "COMPLETED",
    "executed_at": "2026-10-21T10:00:00"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-35 患者合并重定向（内部）

```json
{
  "merge_id": "MG2026102000012",
  "primary_patient_id": 10001,
  "secondary_patient_id": 10112
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "merge_id": "MG2026102000012",
    "secondary_patient_id": 10112,
    "plan_count": 2,
    "task_count": 8,
    "redirected": 8,
    "conflict": 1,
    "conflict_task_ids": [7008]
  },
  "trace_id": "9f8a7b6c"
}
```

> 执行中的任务不自动改派，返回 `conflict` 与冲突任务 ID，由人工确认。

### 6.4 FastAPI 路由实现示例

```python
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import PageResult, success_response
from app.core.security import get_current_user, require_permission
from app.schemas.mpi.followup import (
    FollowupPlanCreate,
    FollowupTaskResult,
    FollowupTemplateCreate,
    MergeRedirectRequest,
    TriggerPlanRequest,
)
from app.services.mpi.followup_service import FollowupService

router = APIRouter(prefix="/api/v1/mpi/followup", tags=["M03-随访"])
internal_router = APIRouter(prefix="/internal/v1/followup", tags=["M03-随访内部接口"])


@router.get("/templates")
async def list_templates(
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:followup:template:list")),
):
    svc = FollowupService(db)
    items, total = await svc.list_templates(keyword, status, page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("/templates")
async def create_template(
    payload: FollowupTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:followup:template:create")),
):
    svc = FollowupService(db)
    return success_response(await svc.create_template(payload, operator=user))


@router.post("/plans")
async def create_plan(
    payload: FollowupPlanCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:followup:plan:create")),
):
    svc = FollowupService(db)
    return success_response(await svc.create_plan(payload, operator=user))


@router.get("/tasks")
async def list_tasks(
    dept_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:followup:task:list")),
):
    svc = FollowupService(db)
    items, total = await svc.list_tasks(dept_id, assignee_id, status, page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@internal_router.post("/plans/trigger")
async def internal_trigger_plan(
    payload: TriggerPlanRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = FollowupService(db)
    return success_response(await svc.trigger_plan(payload))


@internal_router.get("/tasks/pending")
async def internal_pending_tasks(
    dept_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    svc = FollowupService(db)
    return success_response(await svc.pending_tasks(
        dept_id, assignee_id, date_from, date_to, page, page_size))


@internal_router.post("/tasks/{task_id}/result")
async def internal_task_result(
    task_id: int,
    payload: FollowupTaskResult,
    db: AsyncSession = Depends(get_db),
):
    svc = FollowupService(db)
    return success_response(await svc.write_task_result(task_id, payload))


@internal_router.post("/merge-redirect")
async def internal_merge_redirect(
    payload: MergeRedirectRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = FollowupService(db)
    return success_response(await svc.merge_redirect(payload))
```

### 6.5 Service 层核心逻辑示例

```python
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.models.mpi.followup import (
    MpiFollowupConfig,
    MpiFollowupPlan,
    MpiFollowupTask,
    MpiFollowupTaskLog,
    MpiFollowupTemplate,
    MpiFollowupTemplateNode,
)
from app.models.mpi.patient import MpiPatient


class FollowupService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_plan(self, payload, operator=None):
        patient = await self._get_patient(payload.patient_id)
        template = await self._get_template_by_code(payload.template_code)
        if template.status != "ENABLED":
            raise BizException(52311, "模板未启用，不能生成计划")

        plan = MpiFollowupPlan(
            plan_no=await self._gen_plan_no(),
            patient_id=patient.id,
            empi_no=patient.empi_no,
            patient_name=patient.patient_name,
            phone_mask=patient.primary_phone_mask,
            template_id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            source=payload.source or "MANUAL",
            trigger_type=payload.trigger_type,
            base_date=payload.base_date,
            biz_no=payload.biz_no,
            status="ACTIVE" if payload.activate else "DRAFT",
            created_by=getattr(operator, "id", None),
        )
        self.db.add(plan)
        await self.db.flush()

        # 预生成任务
        tasks = await self._generate_tasks(plan, template, patient)
        await self.db.commit()
        return {
            "plan_id": plan.id,
            "plan_no": plan.plan_no,
            "patient_id": patient.id,
            "template_code": template.template_code,
            "status": plan.status,
            "task_count": len(tasks),
            "first_task_date": min((t.plan_date for t in tasks), default=None),
        }

    async def _generate_tasks(self, plan, template, patient):
        nodes = (await self.db.execute(
            select(MpiFollowupTemplateNode)
            .where(MpiFollowupTemplateNode.template_id == template.id,
                   MpiFollowupTemplateNode.is_deleted == False)
            .order_by(MpiFollowupTemplateNode.node_seq)
        )).scalars().all()
        if not nodes:
            raise BizException(52304, "模板节点为空")

        tasks = []
        for node in nodes:
            plan_dates = self._calc_plan_dates(node, plan.base_date)
            for occurrence, d in enumerate(plan_dates, start=1):
                task = MpiFollowupTask(
                    task_no=await self._gen_task_no(),
                    plan_id=plan.id,
                    plan_no=plan.plan_no,
                    patient_id=patient.id,
                    empi_no=patient.empi_no,
                    patient_name=patient.patient_name,
                    phone_mask=patient.primary_phone_mask,
                    template_id=template.id,
                    template_code=template.template_code,
                    node_seq=node.node_seq,
                    node_name=node.node_name,
                    occurrence=occurrence,
                    trigger_type=node.trigger_type,
                    offset_days=node.offset_days,
                    plan_date=d,
                    followup_methods=node.followup_methods,
                    exec_dept_id=node.exec_dept_id,
                    assign_rule_code=node.assign_rule_code,
                    priority=node.priority,
                    is_required=node.is_required,
                    status="PENDING",
                )
                self.db.add(task)
                tasks.append(task)
        await self.db.flush()
        return tasks

    def _calc_plan_dates(self, node, base_date):
        if node.trigger_type == "CYCLE":
            dates = []
            current = base_date + timedelta(days=node.offset_days or 0)
            for _ in range(node.max_occurrences or 1):
                dates.append(current)
                current = current + timedelta(days=node.cycle_days or 1)
            return dates
        return [base_date + timedelta(days=node.offset_days or 0)]

    async def write_task_result(self, task_id: int, payload):
        task = (await self.db.execute(
            select(MpiFollowupTask).where(
                MpiFollowupTask.id == task_id,
                MpiFollowupTask.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not task:
            raise BizException(52313, "任务不存在")
        if task.status in ("CANCELLED",):
            raise BizException(52327, "任务已取消，不能回写")
        if task.status == "COMPLETED":
            raise BizException(52328, "任务已完成，不能重复回写")
        if payload.status not in ("EXECUTING", "COMPLETED", "FAILED"):
            raise BizException(52325, "回写状态非法")

        old_status = task.status
        task.status = payload.status
        if payload.status == "COMPLETED":
            task.completed_at = payload.executed_at or datetime.now()
            task.executed_by = payload.executed_by
            task.executed_by_name = payload.executed_by_name
            task.result_summary = payload.result_summary
        elif payload.status == "FAILED":
            task.fail_reason = payload.fail_reason
        self.db.add(MpiFollowupTaskLog(
            task_id=task.id,
            task_no=task.task_no,
            action=payload.status,
            before_status=old_status,
            after_status=payload.status,
            detail=payload.result_summary or payload.fail_reason,
            operator_id=payload.executed_by,
            operator_name=payload.executed_by_name,
        ))
        await self.db.commit()
        return {
            "task_id": task.id,
            "task_no": task.task_no,
            "status": task.status,
            "executed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def merge_redirect(self, payload):
        # 计划重定向
        plans = (await self.db.execute(
            select(MpiFollowupPlan).where(
                MpiFollowupPlan.patient_id == payload.secondary_patient_id,
                MpiFollowupPlan.is_deleted == False,
            )
        )).scalars().all()
        for p in plans:
            p.patient_id = payload.primary_patient_id

        # 任务重定向（执行中任务记冲突）
        tasks = (await self.db.execute(
            select(MpiFollowupTask).where(
                MpiFollowupTask.patient_id == payload.secondary_patient_id,
                MpiFollowupTask.is_deleted == False,
            )
        )).scalars().all()
        conflict_ids = []
        for t in tasks:
            if t.status == "EXECUTING":
                conflict_ids.append(t.id)
                self.db.add(MpiFollowupTaskLog(
                    task_id=t.id,
                    task_no=t.task_no,
                    action="MERGE_CONFLICT",
                    detail=f"患者合并时任务执行中，patient_id {payload.secondary_patient_id} → {payload.primary_patient_id} 需人工确认",
                ))
                continue
            t.patient_id = payload.primary_patient_id

        await self.db.commit()
        return {
            "merge_id": payload.merge_id,
            "secondary_patient_id": payload.secondary_patient_id,
            "plan_count": len(plans),
            "task_count": len(tasks),
            "redirected": len(tasks) - len(conflict_ids),
            "conflict": len(conflict_ids),
            "conflict_task_ids": conflict_ids,
        }
```

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `mpi:followup:config` | String(JSON) | 30min | 随访配置 | 配置变更 |
| `mpi:followup:template:{id}` | String(JSON) | 30min | 模板详情 | 模板变更 |
| `mpi:followup:template:enabled` | String(JSON) | 30min | 启用模板列表 | 模板变更 |
| `mpi:followup:assign_rules` | String(JSON) | 30min | 分派规则 | 规则变更 |
| `mpi:followup:stats` | String(JSON) | 5min | 统计卡片 | 定时刷新 |
| `mpi:followup:seq:{type}:{yyyyMMdd}` | String | 2d | 编码流水 | 自然过期 |
| `mpi:followup:task:overdue:count` | String | 5min | 逾期任务数 | 定时刷新 |

### 7.2 Celery 异步任务

```python
from celery import shared_task


@shared_task
def followup_overdue_scan_task():
    """扫描逾期任务，标记 OVERDUE 并通知"""
    import asyncio
    return asyncio.run(_overdue_scan())


async def _overdue_scan():
    from datetime import date, datetime, timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.followup import MpiFollowupConfig, MpiFollowupTask, MpiFollowupTaskLog

    async with AsyncSessionLocal() as db:
        config = (await db.execute(
            select(MpiFollowupConfig).where(MpiFollowupConfig.id == 1)
        )).scalar_one()
        overdue_before = date.today() - timedelta(days=config.overdue_days)
        rows = (await db.execute(
            select(MpiFollowupTask).where(
                MpiFollowupTask.status.in_(["PENDING", "ASSIGNED", "EXECUTING"]),
                MpiFollowupTask.plan_date < overdue_before,
                MpiFollowupTask.is_deleted == False,
            )
        )).scalars().all()
        for t in rows:
            old = t.status
            t.status = "OVERDUE"
            db.add(MpiFollowupTaskLog(
                task_id=t.id,
                task_no=t.task_no,
                action="AUTO_OVERDUE",
                before_status=old,
                after_status="OVERDUE",
                detail=f"超过计划日期 {config.overdue_days} 天未完成",
            ))
        await db.commit()
        return {"overdue": len(rows)}


@shared_task
def followup_task_ready_notify_task():
    """任务进入可执行窗口，通知 M19/执行人"""
    import asyncio
    return asyncio.run(_ready_notify())


async def _ready_notify():
    from datetime import date, timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.followup import MpiFollowupConfig, MpiFollowupTask

    async with AsyncSessionLocal() as db:
        config = (await db.execute(
            select(MpiFollowupConfig).where(MpiFollowupConfig.id == 1)
        )).scalar_one()
        ready_date = date.today() + timedelta(days=config.advance_days)
        rows = (await db.execute(
            select(MpiFollowupTask).where(
                MpiFollowupTask.status == "PENDING",
                MpiFollowupTask.plan_date <= ready_date,
                MpiFollowupTask.is_deleted == False,
            )
        )).scalars().all()
        # 发布事件给 M19/消息中心
        for t in rows:
            await publish_event("mpi.followup.task.ready", {
                "task_id": t.id,
                "task_no": t.task_no,
                "patient_id": t.patient_id,
                "exec_dept_id": t.exec_dept_id,
                "plan_date": t.plan_date.isoformat(),
            })
        return {"notified": len(rows)}
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_followup_overdue_scan` | `0 1 * * *` | 每日 01:00 逾期扫描 |
| `job_followup_ready_notify` | `0 8 * * *` | 每日 08:00 任务可执行通知 |
| `job_followup_stats_refresh` | `*/10 * * * *` | 刷新统计缓存 |
| `job_followup_template_cache` | `0 6 * * *` | 预热模板缓存 |
| `job_followup_task_partition` | `0 1 1 * *` | 创建任务日志下月分区 |

---

## 8. 业务规则与校验

### 8.1 模板规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 模板编码唯一 | — | 52302 |
| 模板启用前必须有节点 | 节点数 ≥1 | 52304 |
| 偏移天数合法 | 相对触发日期可为负，绝对值 ≤3650 | 52305 |
| 周期配置 | CYCLE 需 cycle_days ≥1 且 max_occurrences ≥1 | 52306 |
| 模板被计划引用不可删 | 只能停用 | 52307 |
| 模板状态 | DRAFT/ENABLED/DISABLED | 52303 |

### 8.2 计划规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 患者必须 NORMAL | — | 52310 |
| 模板必须 ENABLED | — | 52311 |
| 触发方式与业务单号匹配 | SURGERY_DATE 需手术单号 | 52312 |
| 计划状态 | DRAFT/ACTIVE/COMPLETED/CANCELLED | 52309 |
| 取消计划同步取消未完成任务 | 已完成任务保留 | — |

### 8.3 任务规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 任务状态流转 | PENDING→ASSIGNED→EXECUTING→COMPLETED；可 OVERDUE/FAILED/CANCELLED | 52314 |
| 分派执行科室合法 | 必须是 M01 启用科室 | 52315 |
| 分派人合法 | 必须是 M01 在职职工 | 52316 |
| 未到可执行时间 | 早于 `plan_date - advance_days` 不能拉取 | 52329 |
| 已取消不可回写 | — | 52327 |
| 已完成不可重复回写 | — | 52328 |
| M19 回写状态合法 | EXECUTING/COMPLETED/FAILED | 52325 |

### 8.4 分派规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 规则类型合法 | BY_DEPT/BY_DOCTOR/BY_GROUP/ROUND_ROBIN/MANUAL | 52318 |
| 轮询人员非空 | ROUND_ROBIN 必填 | 52319 |
| 规则编码唯一 | — | 52317 |

### 8.5 并发控制

| 机制 | 说明 |
|---|---|
| 计划/任务编码 | Redis INCR + DB 唯一约束 |
| 乐观锁 | `version_no` |
| 任务回写互斥 | Redis `mpi:followup:task:lock:{id}` |
| 合并重定向互斥 | Redis `mpi:followup:merge:lock:{patient_id}` |
| 逾期扫描互斥 | Redis `mpi:followup:overdue:lock` |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `mpi:followup:template:list` | 模板列表/详情 | 医务科、护理部、信息科 |
| `mpi:followup:template:create` | 新建/复制模板 | 医务科 |
| `mpi:followup:template:update` | 修改/启停/删除模板 | 医务科 |
| `mpi:followup:plan:list` | 计划列表/详情/任务列表 | 护理部、随访组、科室负责人 |
| `mpi:followup:plan:create` | 手动生成计划 | 护理部、随访组 |
| `mpi:followup:plan:update` | 取消计划 | 护理部、随访组 |
| `mpi:followup:task:list` | 任务列表/详情/统计/逾期 | 护理部、随访组、科室负责人 |
| `mpi:followup:task:assign` | 手动/批量分派 | 护理部、随访组 |
| `mpi:followup:task:update` | 取消任务 | 护理部、随访组 |
| `mpi:followup:rule:list` | 分派规则列表 | 信息科、护理部 |
| `mpi:followup:rule:update` | 分派规则维护 | 信息科 |
| `mpi:followup:config:list` | 查询配置 | 信息科 |
| `mpi:followup:config:update` | 修改配置 | 信息科长 |
| `mpi:followup:audit` | 变更日志 | 审计员、信息科 |

### 9.2 权限矩阵

`●` 完全控制 `○` 可操作 `△` 只读 `—` 无权限

| 功能 | 信息科长 | 信息科 | 医务科 | 护理部/随访组 | 科室负责人 | 审计员 |
|---|---|---|---|---|---|---|
| 模板列表 | ● | ● | ● | △ | △ | △ |
| 模板维护 | ● | ● | ● | — | — | — |
| 计划列表 | ● | ● | △ | ● | △(本科室) | △ |
| 生成计划 | ● | ● | — | ● | — | — |
| 取消计划 | ● | ● | — | ● | — | — |
| 任务列表 | ● | ● | △ | ● | △(本科室) | △ |
| 任务分派 | ● | ● | — | ● | ○(本科室) | — |
| 取消任务 | ● | ● | — | ● | — | — |
| 分派规则 | ● | ● | △ | △ | — | △ |
| 配置维护 | ● | △ | — | — | — | △ |
| 变更日志 | ● | ● | △ | △ | — | ● |

### 9.3 数据权限

| 项 | 规则 |
|---|---|
| 模板 | 全院共享 |
| 计划/任务 | 全院可查；科室负责人仅本科室任务 |
| 患者手机号 | 掩码展示 |
| 导出 | 需二次确认并记审计 |

### 9.4 安全措施

- 模板/计划/任务关键操作写 `sys_audit_log`。
- 内部接口使用服务令牌，禁止公网暴露。
- M19 回写结果只接受状态与摘要，不接收敏感字段。
- 合并重定向执行中任务不自动改派，记录冲突日志。

---

## 10. 主数据分发与集成

### 10.1 分发目标

| 目标 | 分发内容 | 触发时机 | 方式 |
|---|---|---|---|
| M19 随访执行 | 任务待执行、任务取消、任务状态变更 | 实时 | 事件 + 内部接口 |
| M03-05 消息 | 任务待执行、逾期提醒 | 实时/定时 | 事件 |
| M03-06 门户 | 患者待随访任务 | 查询 | 内部接口 |
| M09 手术 | 术后随访计划生成结果 | 手术完成触发后 | 事件（可选回执） |
| M05 出院 | 出院随访计划生成结果 | 出院触发后 | 事件（可选回执） |
| M01 患者同步表 | 随访标识（可选） | 实时 | 事件（可选） |

### 10.2 事件清单

| 事件类型 | 触发时机 | 载荷 |
|---|---|---|
| `mpi.followup.plan.created` | 计划生成 | plan_id, plan_no, patient_id, template_code |
| `mpi.followup.task.created` | 任务生成 | task_ids, plan_id, patient_id |
| `mpi.followup.task.ready` | 任务进入可执行窗口 | task_id, task_no, exec_dept_id, plan_date |
| `mpi.followup.task.updated` | 任务状态变更（M19 回写/分派/取消） | task_id, old_status, new_status |
| `mpi.followup.task.overdue` | 任务逾期 | task_id, task_no, overdue_days |
| `mpi.followup.plan.cancelled` | 计划取消 | plan_id, cancelled_task_ids |
| `mpi.followup.merge_conflict` | 合并时任务冲突 | task_ids, merge_id |

### 10.3 内部契约

| 接口 | 用途 | 调用方 | SLA |
|---|---|---|---|
| `POST /internal/v1/followup/plans/trigger` | 业务事件触发计划生成 | M09/M05/M07/M03-01 | P95 ≤ 300ms |
| `GET /internal/v1/followup/tasks/pending` | 拉取待执行任务 | M19 | P95 ≤ 100ms |
| `POST /internal/v1/followup/tasks/{id}/start` | 开始执行 | M19 | P95 ≤ 50ms |
| `POST /internal/v1/followup/tasks/{id}/result` | 回写结果 | M19 | P95 ≤ 100ms |
| `POST /internal/v1/followup/merge-redirect` | 患者合并重定向 | M03-02 | P95 ≤ 200ms |
| `GET /internal/v1/followup/plans/by-patient/{patient_id}` | 按患者查计划 | M19/M03-06 | P95 ≤ 50ms |

**约定：** 内部接口不返回完整手机号，只返回掩码；M19 拉取任务时按 `exec_dept_id`/`assignee_id`/日期范围过滤。

### 10.4 与 M19 的联动

| 场景 | 联动 |
|---|---|
| 任务进入可执行窗口 | 本模块发布 `mpi.followup.task.ready`，M19 消费后纳入待办 |
| M19 开始执行 | 调用 `POST /internal/v1/followup/tasks/{id}/start`，任务变 `EXECUTING` |
| M19 完成/失败 | 调用 `POST /internal/v1/followup/tasks/{id}/result`，任务变 `COMPLETED`/`FAILED` |
| 计划取消 | 本模块同步取消未完成任务，发布 `mpi.followup.plan.cancelled` |
| 逾期 | 本模块标记 `OVERDUE`，发布 `mpi.followup.task.overdue`，M19 可补执行 |

### 10.5 与 M03-02 合并联动

| 场景 | 联动 |
|---|---|
| 02 执行合并 | 发布 `mpi.patient.merged` |
| 本模块订阅 | 调用 `POST /internal/v1/followup/merge-redirect` 更新计划/任务 `patient_id` |
| 执行中任务 | 不自动改派，返回冲突任务 ID，写 `MERGE_CONFLICT` 日志 |
| 主患者已有同模板计划 | 返回冲突，交人工合并计划 |

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| 参数异常 | 模板编码空、偏移天数非法 | 40001 + 字段错误 |
| 业务异常 | 模板未启用、任务状态不允许 | 523xx |
| 并发异常 | 任务回写冲突、合并重定向冲突 | 52331 |
| 依赖异常 | M03-01 不可用、M19 未响应 | 降级或提示 |
| 系统异常 | DB 失败 | 50000 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| M03-01 患者服务 | 禁止生成计划，提示稍后重试 |
| M02 权限服务 | 拒绝访问，不降级放行 |
| M19 | 任务生成不受影响，任务在 `PENDING/ASSIGNED` 等待 |
| M20 短信 | 逾期提醒失败，记录 `notified=false` |
| Redis | 直连 DB，编码流水改用 DB 序列兜底 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-10-21T10:00:00.123+08:00",
  "level": "INFO",
  "logger": "app.services.mpi.followup_service",
  "trace_id": "3f2a1b9c",
  "action": "FOLLOWUP_TASK_COMPLETED",
  "task_id": 7001,
  "task_no": "FTK20261021001",
  "plan_no": "FP20261020001",
  "patient_id": 10001,
  "old_status": "EXECUTING",
  "new_status": "COMPLETED",
  "operator_id": 1024,
  "operator_name": "张三",
  "result": "SUCCESS"
}
```

**禁止记录：** 完整手机号、完整证件号、随访结果中的敏感内容明文。

### 11.3 监控指标

| 指标 | 告警阈值 |
|---|---|
| 接口错误率 | >1% |
| 任务拉取 P95 | >100ms |
| 任务回写 P95 | >100ms |
| 每日逾期任务数 | 异常突增 >50% |
| 计划生成失败率 | >5% |
| 合并冲突数 | >0 |
| 任务编码生成失败率 | >0.1% |
| 导出任务耗时 | >60s |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 新建模板 | 成功，状态 DRAFT |
| AC-02 | 模板编码唯一 | 重复返回 52302 |
| AC-03 | 模板启用前必须有节点 | 空返回 52304 |
| AC-04 | 偏移天数校验 | 非法返回 52305 |
| AC-05 | 周期节点校验 | 非法返回 52306 |
| AC-06 | 模板被引用不可删 | 返回 52307 |
| AC-07 | 模板启停 | 状态流转正确 |
| AC-08 | 复制模板 | 生成新模板，节点复制 |
| AC-09 | 手动生成计划 | 成功，任务预生成 |
| AC-10 | 患者状态异常 | 返回 52310 |
| AC-11 | 模板未启用 | 返回 52311 |
| AC-12 | 触发方式与单号匹配 | 不匹配返回 52312 |
| AC-13 | 计划任务预生成 | 节点数 = 任务数（非周期） |
| AC-14 | 周期任务生成 | 次数 = max_occurrences |
| AC-15 | 计划取消 | 未完成任务同步取消 |
| AC-16 | 任务列表筛选 | 按科室/分派人/状态正确 |
| AC-17 | 任务分派 | 成功，状态 ASSIGNED |
| AC-18 | 批量分派 | 成功 |
| AC-19 | 分派科室非法 | 返回 52315 |
| AC-20 | 分派人非法 | 返回 52316 |
| AC-21 | M19 拉取任务 | 按条件返回，未到时间不返回 |
| AC-22 | M19 开始执行 | 状态 EXECUTING |
| AC-23 | M19 回写完成 | 状态 COMPLETED |
| AC-24 | M19 回写失败 | 状态 FAILED |
| AC-25 | 已取消任务回写 | 返回 52327 |
| AC-26 | 已完成任务重复回写 | 返回 52328 |
| AC-27 | 逾期扫描 | 超期任务标记 OVERDUE |
| AC-28 | 任务可执行通知 | 发布 `mpi.followup.task.ready` |
| AC-29 | 分派规则维护 | 增删改查正确 |
| AC-30 | 轮询人员为空 | 返回 52319 |
| AC-31 | 配置维护 | 校验通过 |
| AC-32 | 合并重定向 | 计划/任务 patient_id 更新 |
| AC-33 | 合并冲突 | 执行中任务返回冲突 |
| AC-34 | 变更日志 | 全量留痕 |
| AC-35 | 权限控制 | 无权限 403 |
| AC-36 | 审计日志 | 关键操作写 `sys_audit_log` |
| AC-37 | 乐观锁 | 版本冲突返回 52331 |
| AC-38 | 任务回写互斥 | 并发回写第二个被拒 |
| AC-39 | 计划编码唯一 | 并发不重复 |
| AC-40 | 任务编码唯一 | 并发不重复 |
| AC-41 | 内部接口鉴权 | 服务令牌校验 |
| AC-42 | 导出脱敏 | 手机号掩码 |
| AC-43 | 模板按会员等级限制 | 不满足时不生成计划（可选） |
| AC-44 | 任务优先级 | 高优先级排序靠前 |
| AC-45 | 任务逾期升级提醒 | 发布事件/通知 |
| AC-46 | 任务结果摘要 | 保存成功 |
| AC-47 | 任务状态日志 | 每次流转有记录 |
| AC-48 | 计划统计 | 数字正确 |
| AC-49 | 任务统计 | 数字正确 |
| AC-50 | 删除草稿模板 | 成功 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | 模板列表 | 50 并发 P95 ≤ 500ms |
| PF-02 | 计划列表 | 50 并发 P95 ≤ 500ms |
| PF-03 | 任务列表 | 50 并发 P95 ≤ 500ms |
| PF-04 | 生成计划（10 节点） | P95 ≤ 500ms |
| PF-05 | M19 拉取任务 | 200 并发 P95 ≤ 100ms |
| PF-06 | M19 回写结果 | 200 并发 P95 ≤ 100ms |
| PF-07 | 逾期扫描 10 万任务 | ≤ 10min |
| PF-08 | 长稳 72h | 无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | 模板节点 100% 保存 | — |
| DA-02 | 计划任务 100% 预生成 | — |
| DA-03 | 任务状态日志 100% 留痕 | — |
| DA-04 | 合并重定向 100% 处理 | 无冲突时 |
| DA-05 | 编码唯一率 | 100% |
| DA-06 | 逾期标记准确率 | 100% |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | 未授权访问 | 403 + 审计 |
| SC-02 | 内部接口公网暴露 | 禁止 |
| SC-03 | 明文手机号泄漏 | 0 处 |
| SC-04 | 任务回写越权 | 403 |
| SC-05 | 关键操作审计 | 100% 写 `sys_audit_log` |
| SC-06 | 导出脱敏 | 通过 |
| SC-07 | 服务令牌校验 | 必须通过 |

---

## 附录 A：模板状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| DRAFT | 启用 | ENABLED | 医务科 |
| ENABLED | 停用 | DISABLED | 医务科 |
| DISABLED | 启用 | ENABLED | 医务科 |
| DRAFT | 删除 | 逻辑删除 | 医务科 |

## 附录 B：计划状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| DRAFT | 激活 | ACTIVE | 生成人 |
| ACTIVE | 全部任务完成 | COMPLETED | 系统 |
| ACTIVE | 取消 | CANCELLED | 护理部/随访组 |
| DRAFT | 取消 | CANCELLED | 生成人 |

## 附录 C：任务状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| PENDING | 分派 | ASSIGNED | 系统/护理部 |
| ASSIGNED | M19 开始 | EXECUTING | M19 |
| EXECUTING | 完成 | COMPLETED | M19 |
| EXECUTING | 失败 | FAILED | M19 |
| PENDING/ASSIGNED/EXECUTING | 逾期 | OVERDUE | 系统 |
| OVERDUE | 完成 | COMPLETED | M19 |
| PENDING/ASSIGNED | 取消 | CANCELLED | 护理部/计划取消 |

## 附录 D：触发方式与业务单号

| 触发方式 | 业务单号 | 来源模块 |
|---|---|---|
| `SURGERY_DATE` | 手术单号 | M09 |
| `DISCHARGE_DATE` | 出院单号 | M05 |
| `REGISTER_DATE` | 患者 EMPI | M03-01 |
| `DIAGNOSIS_DATE` | 诊断记录号 | M07 |
| `FIXED_DATE` | 手动填写 | — |
| `CYCLE` | 起始日期 | — |

## 附录 E：系统参数（M01 `md_sys_param`）

| 参数编码 | 默认值 | 说明 |
|---|---|---|
| `MPI.FOLLOWUP.TEMPLATE_PREFIX` | `FT` | 模板编码前缀 |
| `MPI.FOLLOWUP.PLAN_PREFIX` | `FP` | 计划编码前缀 |
| `MPI.FOLLOWUP.TASK_PREFIX` | `FTK` | 任务编码前缀 |
| `MPI.FOLLOWUP.SEQ_LEN` | `4` | 流水位数 |
| `MPI.FOLLOWUP.ADVANCE_DAYS` | `30` | 任务提前可执行天数 |
| `MPI.FOLLOWUP.OVERDUE_DAYS` | `7` | 逾期判定天数 |
| `MPI.FOLLOWUP.CYCLE_MAX` | `24` | 周期任务最大次数 |
| `MPI.FOLLOWUP.DEFAULT_ASSIGN_RULE` | `BY_DEPT` | 默认分派规则 |
| `MPI.FOLLOWUP.DEFAULT_EXEC_DEPT` | 随访组 | 默认执行科室 |
| `MPI.FOLLOWUP.EXPORT.MAX_ROWS` | `5000` | 导出最大行数 |

## 附录 F：术语表

| 术语 | 说明 |
|---|---|
| 随访模板 | 一类患者的标准随访节点集合 |
| 模板节点 | 模板中的一个随访时间点与内容 |
| 随访计划 | 为某个患者按模板生成的计划 |
| 随访任务 | 计划中一个可执行的随访节点 |
| 计划日期 | 任务应执行的日期 |
| 可执行窗口 | 计划日期前 N 天进入可执行 |
| 逾期 | 计划日期后 N 天未完成 |
| 分派规则 | 决定任务执行科室/执行人的规则 |
| 合并冲突 | 患者合并时任务执行中，需人工确认 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：页面 9 个、数据表 10 张、接口 36 个 | 系统设计组 |