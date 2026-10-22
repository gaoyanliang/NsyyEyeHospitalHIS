# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块：会员（Member）详细设计

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI（子模块编号 M03-03 会员）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M01 主数据管理MDM》《M02 统一权限与安全》《M03 患者服务与EMPI 01 患者主索引与建档》《M03 患者服务与EMPI 02 患者匹配合并与质量》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery / APScheduler
**文档用途：** 作为会员子模块开发、测试、验收依据；作为 01 建档、02 合并、M04/M10/M11/M16/M19 的会员身份与权益基础

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

会员回答一个问题：**“这个患者在会员体系里是什么身份、享有什么权益？”**

01 子模块建立患者身份，02 保证身份唯一；会员是患者身份的**商业扩展**——同一患者可以成为会员，拥有会员号、等级、权益、标签，供消费场景（收费、视光、屈光）与运营场景（随访、营销）使用。

**边界一句话：** 本子模块只管“会员身份与等级/权益定义”——会员存在、等级是什么、享有哪些权益、有哪些标签；**不做**积分、成长值、权益核销、优惠券、营销活动（这些归 M19 会员运营），**不做**消费折扣计算（M16 消费时调用本模块查权益，核销归 M19）。

### 1.2 与 01/02/M19 的分工

| 能力 | 归属 | 说明 |
|---|---|---|
| 患者主档、证件、联系方式 | M03-01 | 本子模块只读引用 |
| 患者合并、主索引重定向 | M03-02 | 合并后会员跟着患者走（`patient_id` 被重定向） |
| **会员主档（会员号、等级、状态、来源）** | **M03-03 本子模块** | — |
| **会员等级定义、升级规则** | **M03-03 本子模块** | — |
| **会员权益定义、等级-权益关联** | **M03-03 本子模块** | — |
| **会员标签、会员-标签关联** | **M03-03 本子模块** | — |
| **会员配置（等级切换策略、会员号规则等）** | **M03-03 本子模块** | — |
| 积分账户、积分流水、成长值 | M19 | 本子模块只存等级，不存成长值 |
| 权益核销记录、优惠券、营销活动 | M19 | 本子模块只定义权益，不核销 |
| 会员消费额统计、复购分析 | M19 | — |
| 会员预约、挂号折扣实际计算 | M04/M16 | 通过本模块“会员权益查询”内部接口取参数 |

### 1.3 模块目标

- **会员身份唯一**：一患者一会员（`patient_id` 唯一），会员号全局唯一。
- **等级体系清晰**：等级定义、升级规则、权益集中配置，避免硬编码。
- **权益可组合**：等级 + 权益关联，支持覆盖值；消费场景通过内部接口一次取全。
- **标签可运营**：手动标签 + 规则标签（规则由 M19 计算后回写），支持颜色与分组。
- **合并友好**：02 合并后，会员跟着 `patient_id` 走，本模块订阅 `mpi.patient.merged` 事件后更新。
- **导入可控**：历史会员批量导入，逐行校验、错误可下载、生成导入任务。
- **强审计**：会员创建、等级调整、状态变更、标签变更全部留痕。

### 1.4 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 导医/客服 | 会员开通、信息维护 | 新建会员、编辑、标签维护 |
| 会员运营（M19） | 等级调整、营销 | 手动升级/降级、标签批量维护 |
| 收费员 | 消费时查会员 | 按手机号/会员号/姓名查会员、查看权益 |
| 视光销售 | 配镜/隐形眼镜销售 | 查会员等级与折扣 |
| 屈光咨询师 | 屈光手术咨询 | 查会员权益 |
| 信息科 | 配置与治理 | 等级、权益、标签、导入、配置 |
| 审计员 | 追溯 | 会员变更日志 |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 会员主档 | 会员号、患者关联、等级、状态、来源、加入时间、生日、备注 |
| 会员状态 | 正常/冻结/过期/注销 |
| 会员等级 | 等级定义、等级序号、升级规则、默认等级、等级切换策略 |
| 等级升级规则 | 成长值门槛、消费额门槛（由 M19 计算后回写，本模块定义规则） |
| 会员权益 | 权益定义、权益类型、权益值、适用范围 |
| 等级-权益关联 | 每个等级享有哪些权益，支持覆盖值 |
| 会员标签 | 标签定义、标签类型、颜色、是否自动 |
| 会员-标签关联 | 手动打标 + M19 规则回写 |
| 会员导入 | Excel 模板、校验、导入任务与明细 |
| 会员变更日志 | 全量留痕 |
| 会员配置 | 会员号规则、默认等级、状态切换策略、权益查询缓存 TTL |
| 会员权益查询 | 内部接口，供 M16/M10/M11/M04 消费时取折扣/积分倍率 |
| 患者合并联动 | 订阅 `mpi.patient.merged`，更新会员 `patient_id` |

### 2.2 范围外

| 范围外内容 | 负责方 |
|---|---|
| 患者主档、证件、联系方式 | M03-01 |
| 患者合并、主索引重定向 | M03-02 |
| 积分账户、积分流水、成长值 | M19 |
| 权益核销记录 | M19 |
| 优惠券、营销活动 | M19 |
| 会员消费额统计、复购分析 | M19 |
| 会员预约、挂号折扣实际计算 | M04 |
| 收费折扣实际计算与账单优惠 | M16 |
| 视光产品会员价 | M01 视光产品 + M10 销售 |
| 屈光手术会员价 | M11 |
| 消息发送 | M03-05 |

### 2.3 与相邻模块分工

```text
M03-01 患者 ◄── patient_id 引用 ── M03-03 会员
   │                                 │
   │                                 ├── 会员权益查询 ──► M16/M10/M11/M04
   │                                 │
   │                                 ├── 等级升级规则 ◄── M19（成长值/消费额回写）
   │                                 │
   │                                 └── 标签回写 ◄── M19（规则标签）
   │
   └── 患者合并 ── mpi.patient.merged ──► M03-03（更新 patient_id）

M03-03 会员 ── 会员事件 ──► M19 会员运营（积分、营销、核销）
```

**关键约定：**
- 会员与患者 1:1，`patient_id` 唯一。
- 会员等级由本模块维护，**升级动作可由 M19 触发**（调用内部接口），本模块记录等级变更日志。
- 权益核销不在本模块，M16/M10/M11 消费时通过 `GET /internal/v1/member/{id}/benefits` 取权益参数，核销记录归 M19。
- 合并时 `patient_id` 重定向由订阅方执行；会员表本身作为订阅方之一，由本模块订阅事件后更新。

### 2.4 依赖清单（对 01/02/M01/M02）

| 依赖方 | 依赖内容 | 用途 |
|---|---|---|
| M03-01 患者 | `mpi_patient` / `mpi_patient_contact` | 会员关联患者、读取姓名/手机号/生日 |
| M03-01 内部接口 | `GET /internal/v1/patient/{id}/brief` | 会员详情展示 |
| M03-02 事件 | `mpi.patient.merged` | 更新会员 `patient_id` |
| M01 字典 | `md_dict_item` / `md_dict_type` | 会员状态、来源、权益类型等枚举 |
| M01 参数 | `md_sys_param` | 会员号前缀、默认等级、缓存 TTL |
| M01 职工/科室 | `mdm_employee` / `mdm_department` | 操作人、审批人、数据权限 |
| M02 账号 | `sys_account` | 操作人 |
| M02 权限 | `mpi:member:*` 权限码 | 页面/接口鉴权 |
| M02 审计 | `sys_audit_log` | 会员关键操作审计 |
| M20 消息 | 短信/站内信 | 会员开通通知、等级变更通知（可降级） |

---

## 3. 业务模型

### 3.1 会员状态机

```text
                    ┌──────────────┐
                    │   ACTIVE     │ 正常
                    └───┬───┬───┬──┘
         冻结            │   │   │ 过期/长期未活跃
         ┌──────────────┘   │   └──────────────┐
         ▼                  │                  ▼
   ┌──────────┐             │            ┌──────────┐
   │  FROZEN  │◄────────────┘            │ EXPIRED  │
   │  已冻结   │  解冻                     │  已过期   │
   └────┬─────┘                           └────┬─────┘
        │                                      │ 续费/重新激活
        │ 注销                                  │
        ▼                                      ▼
   ┌──────────┐                           ┌──────────┐
   │CANCELLED │                           │  ACTIVE  │
   │  已注销   │                           └──────────┘
   └──────────┘
```

| 状态 | 代码 | 说明 | 能否消费享权益 | 恢复 |
|---|---|---|---|---|
| 正常 | `ACTIVE` | 正常会员 | 是 | — |
| 已冻结 | `FROZEN` | 安全原因/欠款/违规 | 否 | 管理员解冻 |
| 已过期 | `EXPIRED` | 未续费/长期未活跃 | 否 | 重新激活 |
| 已注销 | `CANCELLED` | 永久停用 | 否 | 不可恢复（只能新建） |

**状态转换规则：**

| 当前 | 操作 | 目标 | 触发方 | 校验 |
|---|---|---|---|---|
| ACTIVE | 冻结 | FROZEN | 管理员 | 填原因 ≥5 字 |
| FROZEN | 解冻 | ACTIVE | 管理员 | — |
| ACTIVE | 标记过期 | EXPIRED | 系统（定时） | 按过期规则 |
| EXPIRED | 重新激活 | ACTIVE | 管理员/客服 | 校验患者状态 |
| ACTIVE/FROZEN/EXPIRED | 注销 | CANCELLED | 管理员 | **二次确认** + 填原因 |
| CANCELLED | 恢复 | — | — | 不可恢复 |

### 3.2 会员等级体系

#### 3.2.1 默认等级（可配置）

| 序号 | 等级代码 | 等级名称 | 升级门槛（成长值） | 升级门槛（消费额） |
|---|---|---|---|---|
| 1 | `NORMAL` | 普通会员 | 0 | 0 |
| 2 | `SILVER` | 银卡会员 | 1000 | 2000 |
| 3 | `GOLD` | 金卡会员 | 5000 | 10000 |
| 4 | `PLATINUM` | 铂金会员 | 20000 | 40000 |
| 5 | `DIAMOND` | 钻石会员 | 50000 | 100000 |

- **升级规则**：满足成长值门槛 **或** 消费额门槛即升级（可配置为 AND/OR）。
- **降级规则**：由 M19 按年度/季度周期评估后调用本模块降级接口；本模块不主动降级。
- **等级切换策略**：`AUTO`（自动，由 M19 触发）/ `MANUAL`（手动，信息科调整）/ `BOTH`。

#### 3.2.2 等级序号

- `level_seq` 数值越大等级越高。
- 默认等级 `is_default=true`，新会员默认此等级，且系统只允许一个默认等级。

### 3.3 权益模型

#### 3.3.1 权益类型

| 类型 | 代码 | 权益值说明 | 示例 |
|---|---|---|---|
| 折扣 | `DISCOUNT` | 折扣率 0~100 | 9 折 → `90.00` |
| 积分倍率 | `POINTS_RATE` | 倍率 ≥1 | 2 倍积分 → `2.00` |
| 专享服务 | `FREE_SERVICE` | 服务代码 + 次数 | 免费复查 1 次/年 |
| 生日礼 | `BIRTHDAY_GIFT` | 礼品代码 | 生日礼包 |
| 优先预约 | `PRIORITY_BOOKING` | 优先级数值 | 优先 1 级 |
| 专享价 | `EXCLUSIVE_PRICE` | 固定价/折扣价 | 镜片专享价 |
| 储值折扣 | `STORAGE_DISCOUNT` | 折扣率 | 储值 9.5 折 |
| 其他 | `OTHER` | 自由文本 | — |

#### 3.3.2 权益适用范围

| 范围 | 代码 | 说明 |
|---|---|---|
| 全部 | `ALL` | 所有收费项目 |
| 收费类别 | `CHARGE_CLASS` | 如检查费、手术费、药品费 |
| 指定收费项目 | `CHARGE_ITEM` | 指定项目编码列表 |
| 视光产品 | `OPTICAL` | 视光产品品类/品牌 |
| 屈光手术 | `REFRACTIVE` | 屈光手术项目 |
| 会员专享 | `MEMBER_ONLY` | 仅会员可用 |

#### 3.3.3 等级-权益关联

- 每个等级可关联多条权益。
- 同一权益在同一等级可覆盖权益值（如金卡 9 折、钻石 8.5 折）。
- 覆盖值字段 `override_value`，为空时使用权益定义默认值。
- 同一等级同一权益类型同一适用范围只允许一条（避免冲突）。

### 3.4 会员标签模型

#### 3.4.1 标签类型

| 类型 | 代码 | 说明 |
|---|---|---|
| 手动标签 | `MANUAL` | 由客服/运营手动打标 |
| 规则标签 | `RULE` | 由 M19 按规则计算后回写 |
| 系统标签 | `SYSTEM` | 系统自动生成（如"新会员""高价值"） |

#### 3.4.2 标签字段

- 标签编码、标签名称、标签类型、颜色（前端展示）、分组、是否启用、排序。

#### 3.4.3 会员-标签关联

- 一个会员可打多个标签。
- 规则标签由 M19 通过内部接口批量回写。
- 手动标签由客服在会员详情页维护。

### 3.5 会员号规则

- 格式：`M + YYYYMMDD + 6 位流水`，例如 `M20261020000001`。
- 生成：Redis `INCR` + DB 唯一约束兜底。
- 支持手工录入（需唯一）。
- 参数来自 M01 `md_sys_param`：`MPI.MEMBER.PREFIX`（默认 `M`）、`MPI.MEMBER.SEQ_LEN`（默认 6）。

### 3.6 会员来源

| 来源 | 代码 | 说明 |
|---|---|---|
| 门诊 | `OUTPATIENT` | 门诊就诊时开通 |
| 住院 | `INPATIENT` | 住院时开通 |
| 视光 | `OPTOMETRY` | 配镜/隐形眼镜时开通 |
| 屈光 | `REFRACTIVE` | 屈光咨询时开通 |
| 小程序 | `MINIAPP` | 患者端自助开通 |
| 转介绍 | `REFERRAL` | 老会员推荐 |
| 导入 | `IMPORT` | 历史会员批量导入 |
| 员工 | `STAFF` | 院内职工 |
| 其他 | `OTHER` | — |

### 3.7 会员权益查询契约

消费场景（M16/M10/M11/M04）通过内部接口查询会员权益，返回：

```json
{
  "member_id": 20001,
  "member_no": "M20261020000001",
  "level_code": "GOLD",
  "level_name": "金卡会员",
  "benefits": [
    { "benefit_type": "DISCOUNT", "scope": "CHARGE_CLASS", "scope_value": "EXAM", "value": 90.00 },
    { "benefit_type": "POINTS_RATE", "scope": "ALL", "value": 2.00 }
  ]
}
```

**约定：**
- 本接口不记录核销，只返回权益参数。
- 实际核销由 M16/M10/M11 完成后上报 M19。
- 会员状态非 `ACTIVE` 时不返回任何权益（返回空列表 + `status`）。

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [会员数据结构](M03_患者服务与EMPI_03_会员_数据结构.md)

本章原包含 **11 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 会员模块完整数据结构 | [会员数据结构](M03_患者服务与EMPI_03_会员_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```text
患者服务与EMPI
└── 会员
    ├── P01 会员列表（核心页）
    ├── P02 会员详情
    ├── P03 新建/编辑会员
    ├── P04 会员等级管理
    ├── P05 会员权益管理
    ├── P06 会员标签管理
    ├── P07 会员导入
    ├── P08 会员变更日志
    └── P09 会员配置
```

### 5.2 P01 会员列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：患者服务与EMPI / 会员 / 会员列表                     用户：客服01 ▾   │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：会员总数 8,236 | 今日新增 12 | 金卡以上 1,205 | 已冻结 6 | 已过期 320│
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：关键字[会员号/姓名/手机号/EMPI] 等级[全部▼] 状态[全部▼] 来源[全部▼]      │
│ 标签[全部▼]  工具栏：[＋新建会员] [导入] [导出] [批量打标]                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │会员号        │姓名 │手机号     │等级    │状态  │标签           │操作      │
│ ☐ │M202610200001 │王五 │138****5678│金卡    │正常  │高价值、老会员 │···       │
│ ☐ │M202610200002 │李四 │139****2345│银卡    │正常  │新会员         │···       │
│ ☐ │M202610200003 │张三 │—          │普通    │正常  │—              │···       │
│ ☐ │M202610200004 │赵六 │137****8899│钻石    │冻结  │高价值、VIP    │···       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 8,236 条                                       [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**列：** 复选框、会员号、姓名、手机号、等级、状态、标签、加入时间、操作。

**筛选：** 关键字（会员号/姓名/手机号/EMPI）、等级、状态、来源、标签、加入时间区间。

**操作：** 查看详情、编辑、调整等级、冻结/解冻、注销、打标签、查看日志。

### 5.3 P02 会员详情

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员详情：M202610200001  王五                              状态：正常          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【基本信息】                                                                    │
│ 会员号：M202610200001    患者 EMPI：P202610200001                              │
│ 姓名：王五               手机号：138****5678                                    │
│ 性别：男                 出生日期：1980-01-02                                   │
│ 来源：门诊               加入时间：2024-03-01 10:00                             │
│                                                                                │
│ 【等级与权益】                                                                  │
│ 当前等级：金卡会员（成长值 6,200，消费额 12,500）                               │
│ 等级切换：自动                                                                  │
│ 权益：                                                                          │
│  · 检查费 9 折（EXAM）                                                          │
│  · 视光产品 9 折                                                                 │
│  · 积分 2 倍                                                                    │
│  · 生日礼包                                                                     │
│  · 优先预约                                                                     │
│                                                                                │
│ 【标签】                                                                        │
│ 高价值  老会员  屈光术后                                                         │
│ [+ 添加标签]                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [编辑] [调整等级] [冻结] [注销] [查看日志]                                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 P03 新建/编辑会员

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 新建会员                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【关联患者】                                                                    │
│ 患者：[选择患者 ▼]  EMPI：P202610200001  姓名：王五  手机号：138****5678         │
│       ⚠ 该患者已是会员（M202610200001），不能重复开通                            │
│                                                                                │
│ 【会员信息】                                                                    │
│ 会员号：[M202610200099]  （默认自动生成，可手工录入）                            │
│ 会员等级：[金卡会员 ▼]  （默认普通会员）                                        │
│ 会员来源：[门诊 ▼]                                                              │
│ 加入时间：[2026-10-20 10:00]                                                    │
│ 生日：[1980-01-02]  （默认取患者出生日期）                                       │
│ 备注：[________________________________________]                                │
│                                                                                │
│ 【初始标签】                                                                    │
│ [高价值] [新会员]  [+ 添加标签]                                                 │
├────────────────────────────────────────────────────────────────────────────────┤
│                                       [取消] [保存并激活] [保存为待激活]        │
└────────────────────────────────────────────────────────────────────────────────┘
```

**校验：**
- 患者必选，且患者状态必须 `NORMAL`。
- 患者不能已有会员（一患者一会员）。
- 会员号唯一，格式正确。
- 默认等级不能为空。
- 生日不晚于今天。

### 5.5 P04 会员等级管理

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员等级管理                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增等级]                                                                    │
│                                                                                │
│ 序号│等级代码  │等级名称  │成长值门槛│消费额门槛│默认│会员数│操作              │
│ 1   │NORMAL    │普通会员  │0        │0        │是  │5,320│[编辑]            │
│ 2   │SILVER    │银卡会员  │1000     │2000     │否  │1,711│[编辑]            │
│ 3   │GOLD      │金卡会员  │5000     │10000    │否  │  905│[编辑]            │
│ 4   │PLATINUM  │铂金会员  │20000    │40000    │否  │  240│[编辑]            │
│ 5   │DIAMOND   │钻石会员  │50000    │100000   │否  │   60│[编辑]            │
└────────────────────────────────────────────────────────────────────────────────┘
```

**编辑抽屉字段：**

| 字段 | 控件 | 必填 | 说明 |
|---|---|---|---|
| 等级代码 | 文本 | 是 | 大写字母+下划线，唯一 |
| 等级名称 | 文本 | 是 | ≤32 字 |
| 等级序号 | 数字 | 是 | 数值越大等级越高 |
| 成长值门槛 | 数字 | 否 | ≥0 |
| 消费额门槛 | 数字 | 否 | ≥0 |
| 升级逻辑 | 下拉 | 是 | OR（满足任一）/ AND（同时满足） |
| 是否默认 | 开关 | 是 | 只允许一个默认等级 |
| 等级切换策略 | 下拉 | 是 | AUTO/MANUAL/BOTH |
| 权益列表 | 多选 | 否 | 从权益库选择 |
| 颜色 | 颜色选择器 | 否 | 前端展示用 |
| 图标 | 上传 | 否 | — |
| 排序 | 数字 | 否 | — |
| 状态 | 开关 | 是 | 启用/停用 |

**校验：**
- 等级代码唯一。
- 等级序号不能重复。
- 只能有一个默认等级。
- 停用等级前校验是否有会员在该等级。

### 5.6 P05 会员权益管理

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员权益管理                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增权益]                                                                    │
│                                                                                │
│ 权益代码   │权益名称      │类型      │适用范围      │默认值│关联等级│操作      │
│ BEN-DISC-01│检查费 9 折   │折扣      │收费类别 EXAM │90.00 │金卡+   │[编辑]    │
│ BEN-DISC-02│视光 9 折     │折扣      │视光产品      │90.00 │金卡+   │[编辑]    │
│ BEN-PT-01  │积分 2 倍     │积分倍率  │全部          │2.00  │金卡+   │[编辑]    │
│ BEN-SVC-01 │免费复查 1 次 │专享服务  │全部          │1     │铂金+   │[编辑]    │
│ BEN-GIFT-01│生日礼包      │生日礼     │全部          │GIFT01│金卡+   │[编辑]    │
└────────────────────────────────────────────────────────────────────────────────┘
```

**编辑抽屉字段：**

| 字段 | 控件 | 必填 | 说明 |
|---|---|---|---|
| 权益代码 | 文本 | 是 | 唯一 |
| 权益名称 | 文本 | 是 | ≤64 字 |
| 权益类型 | 下拉 | 是 | DISCOUNT/POINTS_RATE/FREE_SERVICE/BIRTHDAY_GIFT/PRIORITY_BOOKING/EXCLUSIVE_PRICE/STORAGE_DISCOUNT/OTHER |
| 适用范围 | 下拉 | 是 | ALL/CHARGE_CLASS/CHARGE_ITEM/OPTICAL/REFRACTIVE/MEMBER_ONLY |
| 范围值 | 文本 | 条件 | CHARGE_CLASS 时填类别编码，CHARGE_ITEM 时填项目编码列表 |
| 默认值 | 文本 | 是 | 按类型：折扣率/倍率/次数/礼品代码/优先级 |
| 默认值单位 | 文本 | 否 | %/倍/次/— |
| 描述 | 文本 | 否 | — |
| 排序 | 数字 | 否 | — |
| 状态 | 开关 | 是 | 启用/停用 |

**等级-权益关联子表：**

| 字段 | 说明 |
|---|---|
| 等级 | 下拉选择 |
| 权益 | 下拉选择 |
| 覆盖值 | 文本，空则用默认值 |
| 启用 | 开关 |

### 5.7 P06 会员标签管理

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员标签管理                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增标签]                                                                    │
│                                                                                │
│ 标签代码  │标签名称  │类型  │颜色  │会员数│状态│操作                          │
│ TAG-HIGH  │高价值    │规则  │#FF6B6B│1,205 │启用│[编辑] [查看会员]            │
│ TAG-NEW   │新会员    │系统  │#4ECDC4│  320 │启用│[编辑] [查看会员]            │
│ TAG-VIP   │VIP       │手动  │#FFD93D│   60 │启用│[编辑] [查看会员]            │
│ TAG-REFR  │屈光术后  │手动  │#A8E6CF│  180 │启用│[编辑] [查看会员]            │
└────────────────────────────────────────────────────────────────────────────────┘
```

**编辑字段：**

| 字段 | 控件 | 必填 | 说明 |
|---|---|---|---|
| 标签代码 | 文本 | 是 | 唯一 |
| 标签名称 | 文本 | 是 | ≤32 字 |
| 标签类型 | 下拉 | 是 | MANUAL/RULE/SYSTEM |
| 颜色 | 颜色选择器 | 是 | 前端展示用 |
| 分组 | 文本 | 否 | — |
| 描述 | 文本 | 否 | — |
| 排序 | 数字 | 否 | — |
| 状态 | 开关 | 是 | 启用/停用 |

### 5.8 P07 会员导入

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员导入                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ ① 下载模板 ─── ② 上传文件 ─── ③ 校验预览 ─── ④ 执行                          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 模板列：姓名* | 性别 | 出生日期 | 手机号 | 证件号 | 等级 | 来源 | 生日 | 备注 │
│                                                                                │
│ 校验结果：总行数 100 | 通过 92 | 警告 5 | 错误 3                                │
│ 错误：行 12 患者不存在或状态异常（EMPI: P202610200999）                         │
│ 错误：行 45 该患者已是会员                                                       │
│ 警告：行 35 手机号格式不规范，将跳过                                            │
│                                                                                │
│ 错误处理：● 跳过错误行继续  ○ 全部校验通过才导入                                │
│                                      [上一步] [取消] [确认导入(92条)]          │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.9 P08 会员变更日志

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员变更日志：M202610200001 王五                                                │
├────────────────────────────────────────────────────────────────────────────────┤
│ 时间                │操作        │操作人│详情                          │IP          │
│ 2024-03-01 10:00:00 │CREATE      │客服01│开通会员，等级普通             │192.168.1.20│
│ 2024-06-15 14:20:00 │LEVEL_UP    │M19   │普通 → 银卡（成长值 1200）     │192.168.1.50│
│ 2024-12-20 09:10:00 │LEVEL_UP    │M19   │银卡 → 金卡（成长值 6200）     │192.168.1.50│
│ 2025-03-01 10:00:00 │TAG_ADD     │客服01│添加标签：老会员               │192.168.1.20│
│ 2026-10-20 10:01:44 │FREEZE      │管理员│安全原因，冻结                 │192.168.1.10│
│ 2026-10-20 11:20:00 │UNFREEZE    │管理员│原因解除，解冻                 │192.168.1.10│
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.10 P09 会员配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会员配置                                        ⚠ 修改影响全院会员业务          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【会员号规则】                                                                  │
│ 前缀：[M]  流水位数：[6]  ☑ 允许手工录入会员号                                  │
│                                                                                │
│ 【默认等级】                                                                    │
│ 默认等级：[普通会员 ▼]                                                          │
│ 新会员自动开通：[☑ 建档时提示开通]  ○ 收费时提示  ○ 不自动提示                   │
│                                                                                │
│ 【等级切换】                                                                    │
│ 升级触发方式：[☑ M19 计算后回写]                                                │
│ 降级触发方式：[☑ M19 计算后回写]                                                │
│ 等级变更需审批：[☑ 降级需审批]  ○ 升级需审批                                   │
│                                                                                │
│ 【权益查询缓存】                                                                │
│ 缓存 TTL：[300 秒]                                                              │
│                                                                                │
│ 【过期规则】                                                                    │
│ ☑ 启用自动过期  长期未活跃天数：[730] 天  提前提醒：[30] 天                    │
│                                                                                │
│ 【合并联动】                                                                    │
│ ☑ 订阅患者合并事件，自动更新会员 patient_id                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│                                         [取消] [保存]                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| **会员 CRUD** | | | | |
| API-01 | GET | `/api/v1/mpi/members` | 会员分页列表 | `mpi:member:list` |
| API-02 | GET | `/api/v1/mpi/members/{id}` | 会员详情 | `mpi:member:list` |
| API-03 | POST | `/api/v1/mpi/members` | 新建会员 | `mpi:member:create` |
| API-04 | PUT | `/api/v1/mpi/members/{id}` | 更新会员 | `mpi:member:update` |
| API-05 | POST | `/api/v1/mpi/members/{id}/freeze` | 冻结会员 | `mpi:member:freeze` |
| API-06 | POST | `/api/v1/mpi/members/{id}/unfreeze` | 解冻会员 | `mpi:member:freeze` |
| API-07 | POST | `/api/v1/mpi/members/{id}/cancel` | 注销会员 | `mpi:member:cancel` |
| API-08 | POST | `/api/v1/mpi/members/{id}/reactivate` | 重新激活 | `mpi:member:update` |
| API-09 | GET | `/api/v1/mpi/members/statistics` | 会员统计 | `mpi:member:list` |
| API-10 | GET | `/api/v1/mpi/members/quick-search` | 快速检索（消费时用） | `mpi:member:list` |
| **等级调整** | | | | |
| API-11 | POST | `/api/v1/mpi/members/{id}/change-level` | 调整会员等级 | `mpi:member:level` |
| API-12 | GET | `/api/v1/mpi/members/{id}/level-history` | 等级变更历史 | `mpi:member:list` |
| **等级管理** | | | | |
| API-13 | GET | `/api/v1/mpi/member-levels` | 等级列表 | `mpi:member:list` |
| API-14 | POST | `/api/v1/mpi/member-levels` | 新增等级 | `mpi:member:level:manage` |
| API-15 | PUT | `/api/v1/mpi/member-levels/{id}` | 修改等级 | `mpi:member:level:manage` |
| API-16 | DELETE | `/api/v1/mpi/member-levels/{id}` | 删除等级 | `mpi:member:level:manage` |
| API-17 | POST | `/api/v1/mpi/member-levels/{id}/set-default` | 设为默认等级 | `mpi:member:level:manage` |
| **权益管理** | | | | |
| API-18 | GET | `/api/v1/mpi/member-benefits` | 权益列表 | `mpi:member:list` |
| API-19 | POST | `/api/v1/mpi/member-benefits` | 新增权益 | `mpi:member:benefit:manage` |
| API-20 | PUT | `/api/v1/mpi/member-benefits/{id}` | 修改权益 | `mpi:member:benefit:manage` |
| API-21 | DELETE | `/api/v1/mpi/member-benefits/{id}` | 删除权益 | `mpi:member:benefit:manage` |
| **等级-权益关联** | | | | |
| API-22 | GET | `/api/v1/mpi/member-levels/{id}/benefits` | 等级权益列表 | `mpi:member:list` |
| API-23 | PUT | `/api/v1/mpi/member-levels/{id}/benefits` | 批量保存等级权益 | `mpi:member:benefit:manage` |
| **标签管理** | | | | |
| API-24 | GET | `/api/v1/mpi/member-tags` | 标签列表 | `mpi:member:list` |
| API-25 | POST | `/api/v1/mpi/member-tags` | 新增标签 | `mpi:member:tag:manage` |
| API-26 | PUT | `/api/v1/mpi/member-tags/{id}` | 修改标签 | `mpi:member:tag:manage` |
| API-27 | DELETE | `/api/v1/mpi/member-tags/{id}` | 删除标签 | `mpi:member:tag:manage` |
| **会员-标签关联** | | | | |
| API-28 | GET | `/api/v1/mpi/members/{id}/tags` | 会员标签列表 | `mpi:member:list` |
| API-29 | POST | `/api/v1/mpi/members/{id}/tags` | 添加标签 | `mpi:member:update` |
| API-30 | DELETE | `/api/v1/mpi/members/{id}/tags/{tag_id}` | 移除标签 | `mpi:member:update` |
| API-31 | POST | `/api/v1/mpi/members/batch-tag` | 批量打标 | `mpi:member:update` |
| **导入导出** | | | | |
| API-32 | GET | `/api/v1/mpi/members/import-template` | 下载导入模板 | `mpi:member:import` |
| API-33 | POST | `/api/v1/mpi/members/import` | 会员导入 | `mpi:member:import` |
| API-34 | GET | `/api/v1/mpi/members/import-tasks/{task_id}` | 导入任务详情 | `mpi:member:import` |
| API-35 | GET | `/api/v1/mpi/members/export` | 导出会员清单 | `mpi:member:export` |
| **日志** | | | | |
| API-36 | GET | `/api/v1/mpi/members/{id}/logs` | 会员变更日志 | `mpi:member:audit` |
| **配置** | | | | |
| API-37 | GET | `/api/v1/mpi/member/config` | 查询会员配置 | `mpi:member:config:list` |
| API-38 | PUT | `/api/v1/mpi/member/config` | 修改会员配置 | `mpi:member:config:update` |
| **内部契约** | | | | |
| API-39 | GET | `/internal/v1/member/by-patient/{patient_id}` | 按患者查会员 | 内部服务 |
| API-40 | GET | `/internal/v1/member/by-no/{member_no}` | 按会员号查 | 内部服务 |
| API-41 | GET | `/internal/v1/member/{id}/benefits` | 会员权益查询（消费场景） | 内部服务 |
| API-42 | POST | `/internal/v1/member/{id}/level-up` | 等级升级（M19 调用） | 内部服务 |
| API-43 | POST | `/internal/v1/member/{id}/level-down` | 等级降级（M19 调用） | 内部服务 |
| API-44 | POST | `/internal/v1/member/{id}/tags/sync` | 规则标签同步（M19 调用） | 内部服务 |
| API-45 | POST | `/internal/v1/member/merge-redirect` | 合并重定向（订阅 02 事件） | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码（M03-03：52201~52240）**

| 错误码 | 含义 |
|---|---|
| "0303001" | 会员不存在 |
| "0303002" | 该患者已是会员 |
| "0303003" | 患者不存在或状态异常 |
| "0303004" | 会员号已存在 |
| "0303005" | 会员号格式不正确 |
| "0303006" | 等级不存在 |
| "0303007" | 等级代码已存在 |
| "0303008" | 等级序号重复 |
| "0303009" | 默认等级只能有一个 |
| "0303010" | 等级下存在会员，不能删除 |
| "0303011" | 会员状态不允许该操作 |
| "0303012" | 冻结必须填写原因 |
| "0303013" | 注销必须二次确认 |
| "0303014" | 会员已注销，不可恢复 |
| "0303015" | 等级调整原因必填 |
| "0303016" | 等级调整审批未通过 |
| "0303017" | 权益不存在 |
| "0303018" | 权益代码已存在 |
| "0303019" | 权益类型与默认值不匹配 |
| "0303020" | 权益适用范围与范围值不匹配 |
| "0303021" | 等级-权益关联重复 |
| "0303022" | 标签不存在 |
| "0303023" | 标签代码已存在 |
| "0303024" | 标签类型非法 |
| "0303025" | 会员已有该标签 |
| "0303026" | 规则标签不允许手动移除 |
| "0303027" | 导入文件格式错误 |
| "0303028" | 导入行数超限 |
| "0303029" | 导入任务不存在 |
| "0303030" | 导入任务状态不允许 |
| "0303031" | 会员号生成失败 |
| "0303032" | 合并重定向失败 |
| "0303033" | 等级升级失败 |
| "0303034" | 等级降级需审批 |
| "0303035" | 配置项非法 |
| "0303036" | 数据已变更，请刷新后重试 |
| "0303037" | M03-01 患者服务不可用 |
| "0303038" | M02 权限服务不可用 |
| "0303039" | 导出数据量超限 |
| "0303040" | 会员状态非正常，无权益 |

### 6.3 关键接口示例

#### API-01 会员分页列表

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 20001,
        "member_no": "M202610200001",
        "patient_id": 10001,
        "empi_no": "P202610200001",
        "member_name": "王五",
        "member_phone_mask": "138****5678",
        "level_code": "GOLD",
        "level_name": "金卡会员",
        "status": "ACTIVE",
        "source": "OUTPATIENT",
        "join_date": "2024-03-01",
        "tags": [
          { "tag_code": "TAG-HIGH", "tag_name": "高价值", "color": "#FF6B6B" }
        ]
      }
    ],
    "total": 8236,
    "page": 1,
    "page_size": 20,
    "pages": 412
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-03 新建会员

```json
{
  "patient_id": 10001,
  "member_no": "M202610200099",
  "level_code": "GOLD",
  "source": "OUTPATIENT",
  "join_date": "2026-10-20",
  "birthday": "1980-01-02",
  "tag_codes": ["TAG-HIGH", "TAG-NEW"],
  "remark": "老客户推荐"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 20099,
    "member_no": "M202610200099",
    "patient_id": 10001,
    "empi_no": "P202610200001",
    "member_name": "王五",
    "level_code": "GOLD",
    "level_name": "金卡会员",
    "status": "ACTIVE",
    "join_date": "2026-10-20"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-11 调整会员等级

```json
{
  "target_level_code": "PLATINUM",
  "reason": "客户消费累计达到铂金门槛",
  "operate_type": "MANUAL"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "member_id": 20001,
    "old_level_code": "GOLD",
    "new_level_code": "PLATINUM",
    "changed_at": "2026-10-20T10:30:00",
    "log_id": 90001
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-41 会员权益查询（消费场景）

```
GET /internal/v1/member/20001/benefits?scope=CHARGE_CLASS&scope_value=EXAM
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "member_id": 20001,
    "member_no": "M202610200001",
    "level_code": "GOLD",
    "level_name": "金卡会员",
    "status": "ACTIVE",
    "benefits": [
      {
        "benefit_code": "BEN-DISC-01",
        "benefit_type": "DISCOUNT",
        "scope": "CHARGE_CLASS",
        "scope_value": "EXAM",
        "value": "90.00",
        "unit": "%",
        "description": "检查费 9 折"
      },
      {
        "benefit_code": "BEN-PT-01",
        "benefit_type": "POINTS_RATE",
        "scope": "ALL",
        "value": "2.00",
        "unit": "倍",
        "description": "积分 2 倍"
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

> 会员状态非 `ACTIVE` 时 `benefits` 返回空数组，`status` 返回实际状态。

#### API-42 等级升级（M19 调用）

```json
{
  "target_level_code": "GOLD",
  "reason": "成长值达到金卡门槛",
  "growth_value": 6200,
  "consume_amount": 12500
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "member_id": 20001,
    "old_level_code": "SILVER",
    "new_level_code": "GOLD",
    "changed_at": "2026-10-20T10:30:00",
    "log_id": 90002
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-45 合并重定向（订阅 02 事件）

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
    "member_id": 20112,
    "old_patient_id": 10112,
    "new_patient_id": 10001,
    "status": "REDIRECTED",
    "conflict": false
  },
  "trace_id": "9f8a7b6c"
}
```

> 若从患者会员与主患者会员同时存在，`conflict=true`，需人工处理（合并会员/注销从会员）。

### 6.4 FastAPI 路由实现示例

```python
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import PageResult, success_response
from app.core.security import get_current_user, require_permission
from app.schemas.mpi.member import (
    MemberChangeLevelRequest,
    MemberCreate,
    MemberQuery,
    MemberUpdate,
    MergeRedirectRequest,
)
from app.services.mpi.member_service import MemberService
from app.services.mpi.member_level_service import MemberLevelService

router = APIRouter(prefix="/api/v1/mpi", tags=["M03-会员"])
internal_router = APIRouter(prefix="/internal/v1/member", tags=["M03-会员内部接口"])


@router.get("/members")
async def list_members(
    keyword: Optional[str] = Query(None),
    level_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:member:list")),
):
    svc = MemberService(db)
    q = MemberQuery(keyword=keyword, level_code=level_code, status=status,
                    page=page, page_size=page_size)
    items, total = await svc.list_members(q)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("/members")
async def create_member(
    payload: MemberCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:member:create")),
):
    svc = MemberService(db)
    return success_response(await svc.create(payload, operator=user))


@router.post("/members/{member_id}/change-level")
async def change_member_level(
    member_id: int,
    payload: MemberChangeLevelRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:member:level")),
):
    svc = MemberLevelService(db)
    return success_response(await svc.change_level(member_id, payload, operator=user))


@internal_router.get("/{member_id}/benefits")
async def internal_member_benefits(
    member_id: int,
    scope: Optional[str] = Query(None),
    scope_value: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = MemberService(db)
    return success_response(await svc.get_benefits(member_id, scope, scope_value))


@internal_router.post("/merge-redirect")
async def internal_merge_redirect(
    payload: MergeRedirectRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MemberService(db)
    return success_response(await svc.merge_redirect(payload))
```

### 6.5 Service 层核心逻辑示例

```python
from datetime import date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BizException
from app.models.mpi.member import (
    MpiMember,
    MpiMemberBenefit,
    MpiMemberLevel,
    MpiMemberLevelBenefit,
    MpiMemberLog,
    MpiMemberTag,
    MpiMemberTagRel,
)
from app.models.mpi.patient import MpiPatient
from app.services.mpi.member_code_service import MemberNoService


class MemberService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_members(self, q):
        stmt = select(MpiMember).where(MpiMember.is_deleted == False)
        if q.keyword:
            kw = f"%{q.keyword}%"
            stmt = stmt.where(or_(
                MpiMember.member_no.ilike(kw),
                MpiMember.member_name.ilike(kw),
                MpiMember.empi_no.ilike(kw),
            ))
        if q.level_code:
            stmt = stmt.where(MpiMember.level_code == q.level_code)
        if q.status:
            stmt = stmt.where(MpiMember.status == q.status)
        total = (await self.db.execute(
            select(func.count()).select_from(stmt.subquery())
        )).scalar_one()
        rows = (await self.db.execute(
            stmt.order_by(MpiMember.created_at.desc())
            .offset((q.page - 1) * q.page_size)
            .limit(q.page_size)
        )).scalars().all()
        return [self._to_list_item(r) for r in rows], total

    async def create(self, payload, operator=None):
        # 1. 校验患者
        patient = (await self.db.execute(
            select(MpiPatient).where(
                MpiPatient.id == payload.patient_id,
                MpiPatient.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not patient:
            raise BizException("0303003", "患者不存在")
        if patient.status != "NORMAL":
            raise BizException("0303003", "患者状态异常，不能开通会员")

        # 2. 校验一患者一会员
        exist = (await self.db.execute(
            select(MpiMember).where(
                MpiMember.patient_id == payload.patient_id,
                MpiMember.is_deleted == False,
            )
        )).scalar_one_or_none()
        if exist:
            raise BizException("0303002", "该患者已是会员", data={
                "member_id": exist.id,
                "member_no": exist.member_no,
            })

        # 3. 会员号
        member_no = payload.member_no or await MemberNoService(self.db).next_no()
        dup = (await self.db.execute(
            select(MpiMember).where(
                MpiMember.member_no == member_no,
                MpiMember.is_deleted == False,
            )
        )).scalar_one_or_none()
        if dup:
            raise BizException("0303004", "会员号已存在")

        # 4. 等级
        level = await self._get_level_by_code(payload.level_code)
        if not level:
            raise BizException("0303006", "等级不存在")

        member = MpiMember(
            member_no=member_no,
            patient_id=patient.id,
            empi_no=patient.empi_no,
            member_name=patient.patient_name,
            member_phone_enc=patient.primary_phone_enc,
            member_phone_mask=patient.primary_phone_mask,
            gender=patient.gender,
            birthday=payload.birthday or patient.birth_date,
            level_id=level.id,
            level_code=level.level_code,
            level_name=level.level_name,
            level_seq=level.level_seq,
            status="ACTIVE",
            source=payload.source,
            join_date=payload.join_date or date.today(),
            remark=payload.remark,
            created_by=getattr(operator, "id", None),
        )
        self.db.add(member)
        await self.db.flush()

        # 5. 标签
        if payload.tag_codes:
            await self._attach_tags(member.id, payload.tag_codes, operator)

        # 6. 日志
        self.db.add(MpiMemberLog(
            member_id=member.id,
            member_no=member.member_no,
            action="CREATE",
            detail=f"开通会员，等级 {level.level_code}",
            operator_id=getattr(operator, "id", None),
            operator_name=getattr(operator, "name", None),
        ))
        await self.db.commit()
        return self._to_detail(member)

    async def get_benefits(self, member_id: int, scope: Optional[str] = None,
                            scope_value: Optional[str] = None):
        member = await self._get(member_id)
        if member.status != "ACTIVE":
            return {
                "member_id": member.id,
                "member_no": member.member_no,
                "level_code": member.level_code,
                "level_name": member.level_name,
                "status": member.status,
                "benefits": [],
            }

        stmt = (
            select(MpiMemberBenefit, MpiMemberLevelBenefit)
            .join(
                MpiMemberLevelBenefit,
                MpiMemberLevelBenefit.benefit_id == MpiMemberBenefit.id,
            )
            .where(
                MpiMemberLevelBenefit.level_id == member.level_id,
                MpiMemberLevelBenefit.is_enabled == True,
                MpiMemberBenefit.is_enabled == True,
                MpiMemberBenefit.is_deleted == False,
            )
        )
        if scope:
            stmt = stmt.where(MpiMemberBenefit.scope == scope)
        if scope_value:
            stmt = stmt.where(MpiMemberBenefit.scope_value == scope_value)
        rows = (await self.db.execute(stmt)).all()

        benefits = []
        for benefit, rel in rows:
            benefits.append({
                "benefit_code": benefit.benefit_code,
                "benefit_type": benefit.benefit_type,
                "scope": benefit.scope,
                "scope_value": benefit.scope_value,
                "value": rel.override_value or benefit.default_value,
                "unit": benefit.value_unit,
                "description": benefit.benefit_name,
            })
        return {
            "member_id": member.id,
            "member_no": member.member_no,
            "level_code": member.level_code,
            "level_name": member.level_name,
            "status": member.status,
            "benefits": benefits,
        }

    async def merge_redirect(self, payload):
        """订阅 02 合并事件：更新会员 patient_id"""
        secondary = (await self.db.execute(
            select(MpiMember).where(
                MpiMember.patient_id == payload.secondary_patient_id,
                MpiMember.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not secondary:
            return {
                "merge_id": payload.merge_id,
                "secondary_patient_id": payload.secondary_patient_id,
                "status": "NO_MEMBER",
                "conflict": False,
            }

        primary = (await self.db.execute(
            select(MpiMember).where(
                MpiMember.patient_id == payload.primary_patient_id,
                MpiMember.is_deleted == False,
            )
        )).scalar_one_or_none()

        if primary:
            # 冲突：主患者也有会员
            self.db.add(MpiMemberLog(
                member_id=secondary.id,
                member_no=secondary.member_no,
                action="MERGE_CONFLICT",
                detail=f"主患者已有会员 {primary.member_no}，需人工处理",
            ))
            await self.db.commit()
            return {
                "merge_id": payload.merge_id,
                "secondary_patient_id": payload.secondary_patient_id,
                "member_id": secondary.id,
                "old_patient_id": secondary.patient_id,
                "new_patient_id": payload.primary_patient_id,
                "status": "CONFLICT",
                "conflict": True,
                "primary_member_no": primary.member_no,
            }

        # 无冲突：从患者会员重定向到主患者
        old_patient_id = secondary.patient_id
        secondary.patient_id = payload.primary_patient_id
        self.db.add(MpiMemberLog(
            member_id=secondary.id,
            member_no=secondary.member_no,
            action="MERGE_REDIRECT",
            detail=f"patient_id {old_patient_id} → {payload.primary_patient_id}",
        ))
        await self.db.commit()
        return {
            "merge_id": payload.merge_id,
            "secondary_patient_id": payload.secondary_patient_id,
            "member_id": secondary.id,
            "old_patient_id": old_patient_id,
            "new_patient_id": payload.primary_patient_id,
            "status": "REDIRECTED",
            "conflict": False,
        }

    async def _get(self, member_id: int) -> MpiMember:
        m = (await self.db.execute(
            select(MpiMember).where(
                MpiMember.id == member_id,
                MpiMember.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not m:
            raise BizException("0303001", "会员不存在")
        return m

    async def _get_level_by_code(self, level_code: str):
        return (await self.db.execute(
            select(MpiMemberLevel).where(
                MpiMemberLevel.level_code == level_code,
                MpiMemberLevel.is_enabled == True,
                MpiMemberLevel.is_deleted == False,
            )
        )).scalar_one_or_none()

    async def _attach_tags(self, member_id: int, tag_codes, operator):
        tags = (await self.db.execute(
            select(MpiMemberTag).where(
                MpiMemberTag.tag_code.in_(tag_codes),
                MpiMemberTag.is_deleted == False,
            )
        )).scalars().all()
        tag_map = {t.tag_code: t for t in tags}
        for code in tag_codes:
            tag = tag_map.get(code)
            if not tag:
                continue
            self.db.add(MpiMemberTagRel(
                member_id=member_id,
                tag_id=tag.id,
                tag_code=tag.tag_code,
                tag_type=tag.tag_type,
                created_by=getattr(operator, "id", None),
            ))
```

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `mpi:member:config` | String(JSON) | 30min | 会员配置 | 配置变更 |
| `mpi:member:levels` | String(JSON) | 30min | 等级列表 | 等级变更 |
| `mpi:member:benefits:{level_id}` | String(JSON) | 30min | 等级权益 | 等级-权益变更 |
| `mpi:member:{id}` | String(JSON) | 30min | 会员简要 | 会员变更 |
| `mpi:member:patient:{patient_id}` | String(整数) | 30min | 患者→会员 ID | 会员变更 |
| `mpi:member:no:{member_no}` | String(整数) | 30min | 会员号→ID | 会员变更 |
| `mpi:member:benefits:{id}` | String(JSON) | 5min | 权益查询缓存（消费场景） | 会员等级/状态变更 |
| `mpi:member:stats` | String(JSON) | 5min | 统计卡片 | 定时刷新 |
| `mpi:member:seq:{yyyyMMdd}` | String | 2d | 会员号流水 | 自然过期 |
| `mpi:member:tags` | String(JSON) | 30min | 标签列表 | 标签变更 |

**权益查询缓存说明：**
- 消费场景高频调用 `GET /internal/v1/member/{id}/benefits`，缓存 TTL 5 分钟。
- 会员等级调整、状态变更、等级-权益变更时主动清除。

### 7.2 Celery 异步任务

```python
from celery import shared_task


@shared_task
def cleanup_member_import_detail_task():
    import asyncio
    return asyncio.run(_cleanup_import_detail())


async def _cleanup_import_detail():
    from datetime import datetime, timedelta
    from sqlalchemy import delete
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.member import MpiMemberImportDetail

    async with AsyncSessionLocal() as db:
        threshold = datetime.now() - timedelta(days=30)
        result = await db.execute(
            delete(MpiMemberImportDetail).where(
                MpiMemberImportDetail.created_at < threshold
            )
        )
        await db.commit()
        return {"deleted": result.rowcount or 0}


@shared_task
def refresh_member_stats_task():
    import asyncio
    return asyncio.run(_refresh_stats())


async def _refresh_stats():
    from sqlalchemy import func, select
    from app.core.database import AsyncSessionLocal
    from app.core.redis import redis_client
    from app.models.mpi.member import MpiMember

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(MpiMember.status, func.count())
            .where(MpiMember.is_deleted == False)
            .group_by(MpiMember.status)
        )).all()
        data = {status: count for status, count in rows}
        import json
        await redis_client.setex("mpi:member:stats", 300, json.dumps(data))
        return data


@shared_task
def member_expire_scan_task():
    """自动过期扫描：长期未活跃会员"""
    import asyncio
    return asyncio.run(_expire_scan())


async def _expire_scan():
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.member import MpiMember, MpiMemberLog

    async with AsyncSessionLocal() as db:
        # 读取配置
        config = await _load_config()
        threshold = datetime.now() - timedelta(days=config.member_expire_days)
        rows = (await db.execute(
            select(MpiMember).where(
                MpiMember.status == "ACTIVE",
                MpiMember.updated_at < threshold,
                MpiMember.is_deleted == False,
            )
        )).scalars().all()
        for m in rows:
            m.status = "EXPIRED"
            db.add(MpiMemberLog(
                member_id=m.id,
                member_no=m.member_no,
                action="AUTO_EXPIRE",
                detail=f"超过 {config.member_expire_days} 天未活跃，自动过期",
            ))
        await db.commit()
        return {"expired": len(rows)}
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_member_stats_refresh` | `*/10 * * * *` | 刷新会员统计缓存 |
| `job_member_expire_scan` | `0 1 * * *` | 每日 01:00 自动过期扫描 |
| `job_member_expire_remind` | `0 9 * * *` | 每日 09:00 过期前提醒 |
| `job_member_import_cleanup` | `0 3 * * *` | 清理 30 天前导入明细 |
| `job_member_log_partition` | `0 1 1 * *` | 创建会员日志下月分区 |
| `job_member_benefits_cache_warmup` | `0 6 * * *` | 预热权益缓存 |

---

## 8. 业务规则与校验

### 8.1 会员规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 一患者一会员 | `patient_id` 唯一 | 52202 |
| 患者必须 NORMAL | 合并/冻结/死亡不能开通 | 52203 |
| 会员号唯一 | 含已注销 | 52204 |
| 会员号格式 | `^M\d{8}\d{4,10}$` 或手工录入（字母数字） | 52205 |
| 等级必须存在 | — | 52206 |
| 生日不晚于今天 | — | 52205 |

### 8.2 状态规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 只有 FROZEN 可解冻 | — | 52211 |
| 注销需二次确认 | 前端弹窗 + 后端校验 `confirm=true` | 52213 |
| CANCELLED 不可恢复 | — | 52214 |
| 冻结/注销必填原因 | ≥5 字 | 52212 |

### 8.3 等级规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 等级代码唯一 | — | 52207 |
| 等级序号唯一 | — | 52208 |
| 默认等级唯一 | — | 52209 |
| 等级下有会员不可删 | 改为停用 | 52210 |
| 等级调整原因必填 | ≥5 字 | 52215 |
| 降级需审批 | 由 M19 触发，本模块校验审批结果 | 52216/52234 |

### 8.4 权益规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 权益代码唯一 | — | 52218 |
| 权益类型与默认值匹配 | DISCOUNT 需 0~100；POINTS_RATE 需 ≥1 | 52219 |
| 适用范围与范围值匹配 | CHARGE_CLASS 需填类别；CHARGE_ITEM 需填项目列表 | 52220 |
| 等级-权益重复 | 同等级同权益同范围只能一条 | 52221 |

### 8.5 标签规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 标签代码唯一 | — | 52223 |
| 标签类型合法 | MANUAL/RULE/SYSTEM | 52224 |
| 会员已有该标签 | — | 52225 |
| 规则标签不允许手动移除 | 由 M19 回写 | 52226 |

### 8.6 并发控制

| 机制 | 说明 |
|---|---|
| 会员号流水 | Redis INCR + DB 唯一约束 |
| 乐观锁 | `version_no` |
| 等级调整互斥 | Redis `mpi:member:level:lock:{id}` |
| 导入互斥 | Redis `mpi:member:import:lock` |
| 合并重定向互斥 | Redis `mpi:member:merge:lock:{patient_id}` |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `mpi:member:list` | 会员列表/详情/快速检索 | 客服、收费、视光销售、屈光咨询、信息科 |
| `mpi:member:create` | 新建会员 | 客服、收费 |
| `mpi:member:update` | 编辑会员、标签维护 | 客服、会员运营 |
| `mpi:member:freeze` | 冻结/解冻 | 信息科、客服主管 |
| `mpi:member:cancel` | 注销 | 信息科长 |
| `mpi:member:level` | 等级调整 | 信息科、会员运营 |
| `mpi:member:level:manage` | 等级管理 | 信息科 |
| `mpi:member:benefit:manage` | 权益管理 | 信息科、财务科 |
| `mpi:member:tag:manage` | 标签管理 | 信息科、会员运营 |
| `mpi:member:import` | 导入 | 信息科 |
| `mpi:member:export` | 导出 | 信息科、会员运营 |
| `mpi:member:audit` | 变更日志 | 审计员、信息科 |
| `mpi:member:config:list` | 查询配置 | 信息科 |
| `mpi:member:config:update` | 修改配置 | 信息科长 |

### 9.2 权限矩阵

`●` 完全控制 `○` 可操作 `△` 只读 `—` 无权限

| 功能 | 信息科长 | 信息科 | 客服 | 会员运营 | 收费员 | 视光销售 | 审计员 |
|---|---|---|---|---|---|---|---|
| 会员列表 | ● | ● | ● | ● | △ | △ | △ |
| 新建会员 | ● | ● | ● | ● | ○ | — | — |
| 编辑会员 | ● | ● | ● | ● | — | — | — |
| 等级调整 | ● | ● | — | ○ | — | — | — |
| 冻结/解冻 | ● | ● | — | — | — | — | △ |
| 注销 | ● | — | — | — | — | — | △ |
| 等级管理 | ● | ● | — | △ | — | — | △ |
| 权益管理 | ● | ● | — | △ | — | — | △ |
| 标签管理 | ● | ● | △ | ● | — | — | △ |
| 导入/导出 | ● | ● | — | ○ | — | — | △ |
| 变更日志 | ● | ● | — | — | — | — | ● |
| 配置维护 | ● | △ | — | — | — | — | △ |

### 9.3 数据权限

| 项 | 规则 |
|---|---|
| 会员列表 | 全院共享，会员运营可按等级/标签筛选 |
| 会员详情 | 全院共享，但消费记录跳转 M16 受 M16 权限控制 |
| 等级/权益/标签 | 全院 |
| 导入导出 | 导出需二次确认并记审计 |

### 9.4 安全措施

- 会员手机号、生日等敏感字段脱敏展示。
- 注销会员需二次确认 + 填原因。
- 等级调整、权益变更、配置修改写 `sys_audit_log`。
- 内部接口使用服务令牌，禁止公网暴露。
- 权益查询缓存 TTL 短（5 分钟），避免权益变更后长时间不生效。

---

## 10. 主数据分发与集成

### 10.1 分发目标

| 目标 | 分发内容 | 触发时机 | 方式 |
|---|---|---|---|
| M16 收费 | 会员等级、权益（折扣、积分倍率） | 消费时 | 内部接口 |
| M10 视光 | 会员等级、视光权益 | 销售时 | 内部接口 |
| M11 屈光 | 会员等级、屈光权益 | 咨询/手术时 | 内部接口 |
| M04 门诊 | 会员标识、优先预约 | 挂号时 | 内部接口 |
| M19 会员运营 | 会员事件（创建、等级变更、状态变更、标签变更） | 实时 | 事件 |
| M03-05 消息 | 会员开通、等级变更通知 | 实时 | 事件 |
| M03-06 门户 | 会员简要、等级、权益 | 登录/查询 | 内部接口 |
| M01 患者同步表 | 会员标识（可选） | 实时 | 事件（可选） |

### 10.2 事件清单

| 事件类型 | 触发时机 | 载荷 |
|---|---|---|
| `mpi.member.created` | 创建会员 | member_id, member_no, patient_id, level_code |
| `mpi.member.level_changed` | 等级变更 | member_id, old_level_code, new_level_code, operate_type |
| `mpi.member.status_changed` | 状态变更 | member_id, old_status, new_status, reason |
| `mpi.member.tag_changed` | 标签变更 | member_id, action, tag_code |
| `mpi.member.merged` | 合并重定向 | member_id, old_patient_id, new_patient_id |
| `mpi.member.merge_conflict` | 合并冲突 | member_id, primary_member_no |

### 10.3 内部契约

| 接口 | 用途 | 调用方 | SLA |
|---|---|---|---|
| `GET /internal/v1/member/by-patient/{patient_id}` | 按患者查会员 | M04/M10/M11/M16 | P95 ≤ 30ms |
| `GET /internal/v1/member/by-no/{member_no}` | 按会员号查 | M16/M10 | P95 ≤ 30ms |
| `GET /internal/v1/member/{id}/benefits` | 会员权益查询 | M16/M10/M11/M04 | P95 ≤ 50ms |
| `POST /internal/v1/member/{id}/level-up` | 等级升级 | M19 | P95 ≤ 100ms |
| `POST /internal/v1/member/{id}/level-down` | 等级降级 | M19 | P95 ≤ 100ms |
| `POST /internal/v1/member/{id}/tags/sync` | 规则标签同步 | M19 | P95 ≤ 200ms |
| `POST /internal/v1/member/merge-redirect` | 合并重定向 | M03-02 | P95 ≤ 100ms |

**约定：** 内部接口不返回完整手机号/证件号，只返回掩码。

### 10.4 与 M19 的联动

| 场景 | 联动 |
|---|---|
| M19 计算成长值/消费额后升级 | 调用 `POST /internal/v1/member/{id}/level-up` |
| M19 计算后降级 | 调用 `POST /internal/v1/member/{id}/level-down` |
| M19 规则标签计算完成 | 调用 `POST /internal/v1/member/{id}/tags/sync` 批量同步 |
| 会员等级变更 | 本模块发布 `mpi.member.level_changed` 事件，M19 记录到会员运营历史 |
| 会员状态变更 | 本模块发布 `mpi.member.status_changed` 事件，M19 暂停/恢复运营 |

### 10.5 与 M03-02 合并联动

| 场景 | 联动 |
|---|---|
| 02 执行合并 | 发布 `mpi.patient.merged` 事件 |
| 本模块订阅事件 | 调用 `POST /internal/v1/member/merge-redirect` 更新会员 `patient_id` |
| 主患者已有会员 | 返回 `CONFLICT`，本模块写 `MERGE_CONFLICT` 日志，发布 `mpi.member.merge_conflict` 事件供人工处理 |

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| 参数异常 | 会员号格式、等级代码空 | 40001 + 字段错误 |
| 业务异常 | 已是会员、状态不允许 | 522xx |
| 并发异常 | 会员号冲突、等级调整冲突 | 重试或 52236 |
| 依赖异常 | M03-01 患者服务不可用 | 降级或提示 |
| 系统异常 | DB 失败 | 50000 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| M03-01 患者服务 | 禁止新建会员，提示稍后重试 |
| M02 权限服务 | 拒绝访问，不降级放行 |
| M20 短信 | 会员开通成功但通知失败，记录 `notified=false` |
| Redis | 直连 DB，会员号流水改用 DB 序列兜底 |
| M19 | 等级升级/降级由 M19 主动调用，M19 不可用不影响本模块 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-10-20T10:30:00.123+08:00",
  "level": "INFO",
  "logger": "app.services.mpi.member_service",
  "trace_id": "3f2a1b9c",
  "action": "MEMBER_LEVEL_CHANGED",
  "member_id": 20001,
  "member_no": "M202610200001",
  "old_level_code": "SILVER",
  "new_level_code": "GOLD",
  "operate_type": "AUTO",
  "operator_id": null,
  "operator_name": "M19_SYSTEM",
  "result": "SUCCESS"
}
```

**禁止记录：** 完整手机号、完整证件号、加密密钥。

### 11.3 监控指标

| 指标 | 告警阈值 |
|---|---|
| 接口错误率 | >1% |
| 权益查询 P95 | >50ms |
| 会员号生成失败率 | >0.1% |
| 每日新增会员数 | 异常突增 >300% |
| 等级变更次数 | 异常突增 |
| 合并冲突数 | >0 |
| 自动过期数 | 异常突增 |
| 导入失败率 | >10% |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 新建会员 | 成功，会员号自动生成 |
| AC-02 | 一患者一会员 | 二次开通返回 "0303002" |
| AC-03 | 患者不存在 | 返回 "0303003" |
| AC-04 | 患者状态异常 | 返回 "0303003" |
| AC-05 | 会员号手工录入 | 唯一校验通过 |
| AC-06 | 会员号重复 | 返回 "0303004" |
| AC-07 | 会员号格式 | 非法返回 "0303005" |
| AC-08 | 等级不存在 | 返回 "0303006" |
| AC-09 | 会员列表筛选 | 按等级/状态/标签筛选正确 |
| AC-10 | 会员详情 | 展示患者、等级、权益、标签 |
| AC-11 | 会员状态机 | 冻结/解冻/过期/注销流转正确 |
| AC-12 | 冻结必填原因 | 空返回 "0303012" |
| AC-13 | 注销二次确认 | 未确认返回 "0303013" |
| AC-14 | CANCELLED 不可恢复 | 返回 "0303014" |
| AC-15 | 等级调整 | 成功，写日志 |
| AC-16 | 等级调整原因必填 | 空返回 "0303015" |
| AC-17 | 等级代码唯一 | 重复返回 "0303007" |
| AC-18 | 等级序号唯一 | 重复返回 "0303008" |
| AC-19 | 默认等级唯一 | 第二个返回 "0303009" |
| AC-20 | 等级下有会员不可删 | 返回 "0303010" |
| AC-21 | 权益代码唯一 | 重复返回 "0303018" |
| AC-22 | 权益类型与值匹配 | 不匹配返回 "0303019" |
| AC-23 | 权益适用范围 | 不匹配返回 "0303020" |
| AC-24 | 等级-权益重复 | 返回 "0303021" |
| AC-25 | 标签代码唯一 | 重复返回 "0303023" |
| AC-26 | 标签类型合法 | 非法返回 "0303024" |
| AC-27 | 会员已有标签 | 返回 "0303025" |
| AC-28 | 规则标签手动移除 | 返回 "0303026" |
| AC-29 | 批量打标 | 成功 |
| AC-30 | 会员导入模板 | 可下载 |
| AC-31 | 会员导入校验 | 错误行号准确 |
| AC-32 | 会员导入执行 | 成功创建会员 |
| AC-33 | 会员导出 | 脱敏正确 |
| AC-34 | 变更日志 | 全量留痕 |
| AC-35 | 配置修改 | 校验通过 |
| AC-36 | 权益查询内部接口 | 按等级返回权益 |
| AC-37 | 权益查询缓存 | 5 分钟内命中 |
| AC-38 | 会员非 ACTIVE 无权益 | 返回空列表 |
| AC-39 | M19 等级升级 | 成功 |
| AC-40 | M19 等级降级 | 成功 |
| AC-41 | M19 规则标签同步 | 成功 |
| AC-42 | 合并重定向 | 无冲突时更新 patient_id |
| AC-43 | 合并冲突 | 返回 CONFLICT 并写日志 |
| AC-44 | 合并事件订阅 | 收到 `mpi.patient.merged` 后自动重定向 |
| AC-45 | 权限控制 | 无权限 403 |
| AC-46 | 审计日志 | 等级/权益/配置变更写 `sys_audit_log` |
| AC-47 | 乐观锁 | 版本冲突返回 "0303036" |
| AC-48 | 导入互斥 | 并发导入第二个被拒 |
| AC-49 | 自动过期扫描 | 长期未活跃会员自动 EXPIRED |
| AC-50 | 过期提醒 | 过期前 30 天提醒 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | 会员列表 | 50 并发 P95 ≤ 500ms |
| PF-02 | 会员详情 | 50 并发 P95 ≤ 200ms |
| PF-03 | 快速检索 | 100 并发 P95 ≤ 200ms |
| PF-04 | 新建会员 | 50 并发 P95 ≤ 300ms |
| PF-05 | 权益查询内部接口 | 500 并发 P95 ≤ 50ms |
| PF-06 | 等级调整 | 50 并发 P95 ≤ 300ms |
| PF-07 | 导入 500 行 | ≤ 30s |
| PF-08 | 长稳 72h | 无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | 一患者一会员 | 100% |
| DA-02 | 会员号唯一 | 100% |
| DA-03 | 默认等级唯一 | 100% |
| DA-04 | 等级-权益关联无重复 | 100% |
| DA-05 | 变更日志 100% 留痕 | 100% |
| DA-06 | 导入错误可定位 | 100% |
| DA-07 | 合并重定向 100% 处理 | 无冲突时 100% |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | 明文手机号泄漏 | 0 处 |
| SC-02 | 未授权访问 | 403 + 审计 |
| SC-03 | 注销未二次确认 | 52213 |
| SC-04 | 内部接口公网暴露 | 禁止 |
| SC-05 | 敏感操作审计 | 100% 写 `sys_audit_log` |
| SC-06 | 导出脱敏 | 通过 |
| SC-07 | 规则标签手动移除 | 拦截 |

---

## 附录 A：会员状态流转表

| 当前 | 操作 | 目标 | 触发方 | 是否留痕 |
|---|---|---|---|---|
| ACTIVE | 冻结 | FROZEN | 管理员 | 是 |
| FROZEN | 解冻 | ACTIVE | 管理员 | 是 |
| ACTIVE | 标记过期 | EXPIRED | 系统 | 是 |
| EXPIRED | 重新激活 | ACTIVE | 管理员/客服 | 是 |
| ACTIVE/FROZEN/EXPIRED | 注销 | CANCELLED | 信息科长 | 是 |
| CANCELLED | — | — | — | 不可恢复 |

## 附录 B：会员等级预置

| 序号 | 代码 | 名称 | 成长值门槛 | 消费额门槛 | 默认 |
|---|---|---|---|---|---|
| 1 | `NORMAL` | 普通会员 | 0 | 0 | 是 |
| 2 | `SILVER` | 银卡会员 | 1000 | 2000 | 否 |
| 3 | `GOLD` | 金卡会员 | 5000 | 10000 | 否 |
| 4 | `PLATINUM` | 铂金会员 | 20000 | 40000 | 否 |
| 5 | `DIAMOND` | 钻石会员 | 50000 | 100000 | 否 |

## 附录 C：权益类型与值

| 类型代码 | 值范围 | 单位 | 示例 |
|---|---|---|---|
| `DISCOUNT` | 0~100 | % | 90.00 = 9 折 |
| `POINTS_RATE` | ≥1 | 倍 | 2.00 = 2 倍 |
| `FREE_SERVICE` | ≥1 | 次 | 1 = 免费 1 次 |
| `BIRTHDAY_GIFT` | 文本 | — | `GIFT01` |
| `PRIORITY_BOOKING` | ≥1 | 级 | 1 = 优先 1 级 |
| `EXCLUSIVE_PRICE` | ≥0 | 元 | 199.00 |
| `STORAGE_DISCOUNT` | 0~100 | % | 95.00 = 9.5 折 |
| `OTHER` | 文本 | — | — |

## 附录 D：系统参数（M01 `md_sys_param`）

| 参数编码 | 默认值 | 说明 |
|---|---|---|
| `MPI.MEMBER.PREFIX` | `M` | 会员号前缀 |
| `MPI.MEMBER.SEQ_LEN` | `6` | 会员号流水位数 |
| `MPI.MEMBER.DEFAULT_LEVEL` | `NORMAL` | 默认等级代码 |
| `MPI.MEMBER.BENEFIT_CACHE_TTL` | `300` | 权益查询缓存秒数 |
| `MPI.MEMBER.EXPIRE_DAYS` | `730` | 长期未活跃自动过期天数 |
| `MPI.MEMBER.EXPIRE_REMIND_DAYS` | `30` | 过期前提醒天数 |
| `MPI.MEMBER.IMPORT.MAX_ROWS` | `500` | 导入最大行数 |
| `MPI.MEMBER.EXPORT.MAX_ROWS` | `5000` | 导出最大行数 |

## 附录 E：会员变更日志动作

| 代码 | 说明 |
|---|---|
| `CREATE` | 开通会员 |
| `UPDATE` | 修改会员信息 |
| `LEVEL_UP` | 等级升级 |
| `LEVEL_DOWN` | 等级降级 |
| `LEVEL_CHANGE_MANUAL` | 手动调整等级 |
| `FREEZE` | 冻结 |
| `UNFREEZE` | 解冻 |
| `AUTO_EXPIRE` | 自动过期 |
| `REACTIVATE` | 重新激活 |
| `CANCEL` | 注销 |
| `TAG_ADD` | 添加标签 |
| `TAG_REMOVE` | 移除标签 |
| `TAG_SYNC` | 规则标签同步 |
| `MERGE_REDIRECT` | 合并重定向 |
| `MERGE_CONFLICT` | 合并冲突 |

## 附录 F：术语表

| 术语 | 说明 |
|---|---|
| 会员 | 患者在会员体系中的身份 |
| 会员号 | 会员唯一标识 |
| 会员等级 | 会员分层，如普通/银卡/金卡 |
| 成长值 | 由 M19 计算，用于升级判断 |
| 消费额 | 由 M16 统计，用于升级判断 |
| 权益 | 会员享有的折扣/服务/倍率 |
| 标签 | 会员属性标识，如高价值/新会员 |
| 等级切换策略 | AUTO（自动）/ MANUAL（手动）/ BOTH |
| 规则标签 | 由 M19 计算后回写的标签 |
| 合并冲突 | 合并时主患者已有会员 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：页面 9 个、数据表 11 张、接口 45 个 | 系统设计组 |