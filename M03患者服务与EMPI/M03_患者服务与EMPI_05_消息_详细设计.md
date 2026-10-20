# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块：消息（Message Center）详细设计

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI（子模块编号 M03-05 消息）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M01 主数据管理MDM》《M02 统一权限与安全》《M03 患者服务与EMPI 01 患者主索引与建档》《M03 患者服务与EMPI 03 会员》《M03 患者服务与EMPI 04 随访》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / Celery / APScheduler
**文档用途：** 作为消息中心开发、测试、验收依据；作为 M03-04 随访、M03-06 门户、M19 会员运营及各业务模块的统一消息发送能力

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

消息中心回答一个问题：**“给谁、在什么渠道、用什么内容、发一条什么消息，发出去有没有成功？”**

本子模块是全院的**统一消息出口**：所有业务模块（随访、门诊、会员、手术、收费、门户等）需要给患者发短信/微信/邮件/站内信/APP 推送时，都通过本模块的模板 + 发送能力，而不是各业务自建短信网关。这样做的价值：

- **模板统一**：全院消息模板集中治理，避免各模块自造文案、无法审计。
- **渠道统一**：短信/微信/邮件/站内信/APP 推送统一封装，供应商可替换。
- **合规统一**：患者退订、黑名单、脱敏、频控在一处实现。
- **回执统一**：所有渠道的送达/阅读/失败回执落一张表，便于统计与追溯。
- **可追溯**：每条消息对应模板版本、发送时间、内容快照、回执，满足审计。

**边界一句话：** 本子模块只管“消息的生产、发送、回执、重试、退订与脱敏”；**不做**业务事件产生（随访/门诊/收费等业务模块自己产生事件），**不做**网关实际对接（M21 封装短信/微信/邮件网关），**不做**患者端消息展示页面（M03-06），**不做**员工站内信（M20）。

### 1.2 与相邻模块的分工

| 能力 | 归属 | 说明 |
|---|---|---|
| 患者主档、手机号 | M03-01 | 本模块只读引用，加密后存储 |
| 患者合并、主索引重定向 | M03-02 | 合并后接收人 `patient_id` 重定向由本模块订阅事件处理 |
| 会员等级 | M03-03 | 模板可按会员等级差异化（可选） |
| 随访任务待执行/逾期事件 | M03-04 | 本模块订阅后发送提醒 |
| 门户消息中心页面 | M03-06 | 本模块只提供未读数、消息列表内部接口 |
| 业务事件产生 | M04/M09/M16/M19 等 | 各模块调用本模块发送接口 |
| 短信/微信/邮件/APP 推送网关 | M21 集成平台 | 本模块调用 M21 统一网关，收集回执 |
| 员工站内信、审批消息 | M20 | 独立体系，不归本模块 |
| 消息营销运营、活动触达策略 | M19 | 本模块只提供发送能力，运营策略由 M19 决定 |

### 1.3 模块目标

- **模板可配置、可版本化**：模板变更不覆盖历史，发送时按版本号取内容。
- **渠道可插拔**：短信/微信/邮件/站内信/APP 推送统一抽象，新增渠道只改渠道配置。
- **发送可批量、可单条**：任务级统计 + 记录级回执。
- **回执可追溯**：送达/阅读/失败/点击/退订全量落库。
- **失败可重试**：可重试错误自动进重试队列，不可重试错误直接终态。
- **合规可控制**：黑名单、退订、频控、脱敏集中在发送前拦截。
- **合并友好**：患者合并后接收人 `patient_id` 自动重定向，执行中的消息记录冲突日志。

### 1.4 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 信息科 | 渠道配置、模板治理 | 配置渠道、维护模板、配置频控 |
| 业务科室 | 模板申请、发送 | 申请模板、调用发送接口、查看发送记录 |
| 会员运营 | 营销消息发送 | 调用发送接口、查看回执 |
| 客服 | 消息查询与重发 | 查询消息记录、单条重发 |
| 审计员 | 追溯 | 查看模板版本、发送记录、回执 |
| 患者本人 | 退订/订阅 | 通过门户退订营销类消息 |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 渠道配置 | 短信/微信/邮件/站内信/APP 推送，供应商参数、频控、脱敏规则 |
| 消息模板 | 模板主档、模板版本、变量定义、签名、审核状态 |
| 发送任务 | 批量任务主档、任务统计、任务状态 |
| 发送记录 | 单条消息记录、接收人、内容快照、状态 |
| 消息回执 | 送达/阅读/失败/点击/回复/退订 |
| 失败重试 | 可重试错误进重试队列，定时重试，超阈值终态 |
| 消息黑名单 | 接收人 + 渠道 + 业务类型的退订/投诉/异常 |
| 敏感脱敏 | 手机号/邮箱/openid 加密 + 掩码；内容变量脱敏 |
| 频控 | 按接收人/渠道/业务类型/时间窗口限流 |
| 内部契约 | 业务模块调用发送、门户查未读数、M21 回执回调 |
| 变更日志 | 模板/渠道/配置/黑名单变更留痕 |
| 编码序列 | 任务号、消息号序列 |

### 2.2 范围外

| 范围外内容 | 负责方 |
|---|---|
| 业务事件产生（随访/门诊/收费/手术） | M03-04/M04/M09/M16 |
| 短信/微信/邮件/APP 推送网关实际对接 | M21 集成平台 |
| 患者端消息中心页面 | M03-06 |
| 员工站内信、审批消息 | M20 |
| 消息营销策略、活动触达 | M19 |
| 模板内容的医学审核 | 医务科（人工审核） |
| 消息内容的 AI 生成 | 本期不做 |

### 2.3 与相邻模块分工

```text
M03-04 随访 / M04 门诊 / M09 手术 / M16 收费 / M19 会员运营
        │ 调用发送接口
        ▼
M03-05 消息中心 ── 模板 + 渠道 + 发送 + 回执 ──► M21 集成平台
        │                                              │
        │ 回执回调                                     │ 短信/微信/邮件/推送
        ◄──────────────────────────────────────────────┘
        │
        ├── 患者合并事件 ◄── M03-02
        ├── 未读数/消息列表 ──► M03-06 门户
        └── 模板按会员等级差异化 ◄── M03-03（可选）
```

**关键约定：**
- 业务模块不直连短信/微信网关，必须通过本模块发送。
- 业务模块调用发送接口时传“模板编码 + 变量”，不传完整明文内容，避免文案散落。
- 本模块不保存明文手机号，接收人字段加密 + 掩码。
- 网关对接由 M21 封装，本模块只调用 M21 的统一发送接口，并接收 M21 的回执回调。
- 患者合并后，消息记录的 `patient_id` 由本模块订阅 `mpi.patient.merged` 更新；执行中的消息不自动改派。

### 2.4 依赖清单（对 01/02/03/04/M01/M02/M21）

| 依赖方 | 依赖内容 | 用途 |
|---|---|---|
| M03-01 患者 | `mpi_patient` / `mpi_patient_contact` | 接收人手机号加密后存储 |
| M03-01 内部接口 | `GET /internal/v1/patient/{id}/brief` | 接收人姓名/手机号掩码 |
| M03-02 事件 | `mpi.patient.merged` | 更新消息记录 `patient_id` |
| M03-03 会员 | 会员等级（可选） | 模板按等级差异化 |
| M03-04 随访 | `mpi.followup.task.ready` / `mpi.followup.task.overdue` | 随访提醒消息 |
| M01 字典 | `md_dict_item` / `md_dict_type` | 渠道、业务类型、消息状态等枚举 |
| M01 参数 | `md_sys_param` | 频控阈值、重试次数、模板变量上限 |
| M01 职工/科室 | `mdm_employee` / `mdm_department` | 操作人、数据权限 |
| M02 账号 | `sys_account` | 操作人 |
| M02 权限 | `mpi:message:*` 权限码 | 页面/接口鉴权 |
| M02 审计 | `sys_audit_log` | 模板/渠道/配置/黑名单变更审计 |
| M21 集成平台 | 短信/微信/邮件/推送网关 | 实际发送与回执回调 |

---

## 3. 业务模型

### 3.1 渠道模型

| 渠道 | 代码 | 说明 | 典型供应商 |
|---|---|---|---|
| 短信 | `SMS` | 国内短信 | 阿里云/腾讯云/容联云 |
| 微信 | `WECHAT` | 公众号模板消息/企微 | 微信官方 |
| 邮件 | `EMAIL` | SMTP/企业邮箱 | 自建/腾讯企业邮 |
| 站内信 | `INBOX` | 患者端消息中心 | 本模块存储 |
| APP 推送 | `APP_PUSH` | 患者端 APP 推送 | 极光/个推/厂商通道 |
| 语音 | `VOICE` | 语音通知（预留） | 阿里云/腾讯云 |

渠道配置字段：渠道代码、渠道名称、供应商、网关接口地址（由 M21 封装）、鉴权方式、签名、每日上限、单接收人频率、是否启用、脱敏规则、回执格式。

### 3.2 模板模型

#### 3.2.1 模板字段

- 模板编码、模板名称、渠道、业务类型、标题、内容、变量定义、签名、第三方模板 ID、优先级、状态、是否需要审核、审核人、审核时间。

#### 3.2.2 模板版本

- 每次修改生成新版本，旧版本保留。
- 发送记录保存 `template_version`，保证历史消息可追溯。
- 版本号从 1 递增，`is_current=true` 为当前版本。

#### 3.2.3 模板变量

- 变量格式：`{{变量名}}`。
- 变量定义：变量名、显示名、类型（文本/数字/日期/金额）、是否敏感、默认值。
- 发送时变量必须齐全，缺失拒绝发送。

#### 3.2.4 模板审核

- 短信/微信模板需审核（供应商侧），`audit_status` 记录：DRAFT/PENDING/APPROVED/REJECTED。
- 邮件/站内信/APP 推送可不审核（可配置）。
- 审核通过后才能发送；审核拒绝需修改后重新提交。

### 3.3 业务类型

| 业务类型 | 代码 | 说明 | 是否可退订 |
|---|---|---|---|
| 验证码 | `VERIFY_CODE` | 登录/绑定验证码 | 否 |
| 通知 | `NOTICE` | 就诊通知、报告通知 | 否 |
| 随访 | `FOLLOWUP` | 随访提醒 | 是（可单独退订） |
| 会员 | `MEMBER` | 会员开通、等级变更、生日礼 | 是 |
| 营销 | `MARKETING` | 活动、优惠券、促销 | 是 |
| 满意度 | `SATISFACTION` | 满意度调查 | 是 |
| 系统 | `SYSTEM` | 系统告警、运维 | 否 |

### 3.4 发送模型

#### 3.4.1 任务与记录

- **任务**：一次批量发送的批次，含模板、渠道、接收人数量、状态、统计。
- **记录**：任务内单条消息，含接收人、内容快照、状态、回执、重试次数。
- 单条发送时也创建任务（`total_count=1`），便于统一统计。

#### 3.4.2 发送状态机

```text
PENDING ──提交网关──► SENDING ──回执成功──► SENT ──回执送达──► DELIVERED ──回执阅读──► READ
   │                    │
   │                    ├──回执失败（可重试）──► RETRYING ──重试──► SENDING
   │                    │
   │                    └──回执失败（不可重试）/重试超限──► FAILED
   │
   └──取消/超时──► EXPIRED
```

| 状态 | 代码 | 说明 |
|---|---|---|
| 待发送 | `PENDING` | 记录已创建，未提交网关 |
| 发送中 | `SENDING` | 已提交网关，等待回执 |
| 已发送 | `SENT` | 网关已接受（短信/邮件） |
| 已送达 | `DELIVERED` | 网关确认送达 |
| 已阅读 | `READ` | 接收人已阅读（站内信/微信/APP） |
| 重试中 | `RETRYING` | 可重试失败，进入重试队列 |
| 失败 | `FAILED` | 不可重试或重试超限 |
| 已过期 | `EXPIRED` | 超时未发送（如验证码过期） |
| 已拒绝 | `REJECTED` | 黑名单/退订/频控拦截 |

#### 3.4.3 回执类型

| 回执 | 代码 | 说明 |
|---|---|---|
| 送达 | `DELIVERED` | 网关确认送达 |
| 阅读 | `READ` | 接收人阅读 |
| 失败 | `FAILED` | 网关返回失败 |
| 点击 | `CLICKED` | 接收人点击链接（微信/邮件） |
| 回复 | `REPLIED` | 接收人回复（短信上行） |
| 退订 | `UNSUBSCRIBED` | 接收人退订 |

### 3.5 黑名单模型

| 字段 | 说明 |
|---|---|
| 接收人类型 | PATIENT/STAFF |
| 接收人 ID | 患者 ID/职工 ID |
| 渠道 | 可选，空=全渠道 |
| 业务类型 | 可选，空=全类型 |
| 原因 | 退订/投诉/异常/管理员 |
| 有效期 | 长期/指定日期 |
| 状态 | ACTIVE/RELEASED/EXPIRED |

**规则：**
- 验证码/通知类不可退订。
- 营销类默认允许退订，退订后加黑名单。
- 管理员可手动加/解黑名单。

### 3.6 频控模型

| 维度 | 说明 |
|---|---|
| 单接收人/渠道/业务类型/小时 | 默认 5 条 |
| 单接收人/渠道/业务类型/天 | 默认 20 条 |
| 单渠道/天 | 默认 50000 条 |
| 单任务/接收人 | 默认 3 条（防止重复） |

频控在发送前拦截，超限记录 `REJECTED`，`reject_reason=FREQUENCY_LIMIT`。

### 3.7 脱敏模型

| 字段 | 规则 |
|---|---|
| 手机号 | `138****5678`（保留前 3 后 4） |
| 邮箱 | `w***@example.com`（保留首字符 + 域名） |
| 微信 openid | `o***xyz`（保留首尾） |
| 内容变量 | 按变量定义 `is_sensitive=true` 时替换为掩码 |

### 3.8 患者合并联动

- 订阅 `mpi.patient.merged` 事件。
- 更新 `mpi_message_record.patient_id`（接收人类型为 PATIENT 且接收人 ID 为从患者）。
- 若记录处于 `SENDING` 或 `RETRYING`，记录 `MERGE_CONFLICT` 日志，不自动改派，交人工确认。
- 任务统计不因合并变化（任务按记录统计）。

### 3.9 与 M21 集成平台的契约

- **发送接口**：`POST /internal/v1/gateway/message/send`，本模块调用 M21，传 `channel / receiver_addr(加密) / template_provider_id / content_vars / task_no / record_no`。
- **回执回调**：M21 调用本模块 `POST /internal/v1/message/receipt`，传 `record_no / receipt_type / provider_message_id / error_code / error_msg / raw_data`。
- **回执重试**：M21 回调失败时，本模块提供 `GET /internal/v1/message/pending-receipts` 供 M21 拉取补发。

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [消息数据结构](M03_患者服务与EMPI_05_消息_数据结构.md)

本章原包含 **12 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 消息模块完整数据结构 | [消息数据结构](M03_患者服务与EMPI_05_消息_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```text
患者服务与EMPI
└── 消息中心
    ├── P01 消息模板列表
    ├── P02 消息模板编辑
    ├── P03 模板版本历史
    ├── P04 渠道配置
    ├── P05 消息发送任务列表
    ├── P06 消息发送记录
    ├── P07 消息回执统计
    ├── P08 消息黑名单
    ├── P09 消息配置
    └── P10 变更日志
```

### 5.2 P01 消息模板列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 面包屑：患者服务与EMPI / 消息中心 / 消息模板                   用户：信息科01 ▾ │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：模板总数 86 | 已启用 62 | 待审核 6 | 已停用 18                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：关键字[模板编码/名称] 渠道[全部▼] 业务类型[全部▼] 状态[全部▼]              │
│ 工具栏：[＋新建模板] [导入] [导出]                                              │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │模板编码          │模板名称              │渠道  │业务类型│状态    │版本│操作│
│ ☐ │MSG-SMS-APPT-01   │预约成功提醒          │短信  │通知    │已启用  │v3 │··· │
│ ☐ │MSG-WECHAT-FU-01  │术后随访提醒          │微信  │随访    │已启用  │v2 │··· │
│ ☐ │MSG-SMS-MKT-01    │会员生日礼            │短信  │会员    │已启用  │v1 │··· │
│ ☐ │MSG-INBOX-SAT-01  │满意度调查            │站内信│满意度  │待审核  │v1 │··· │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 86 条                                          [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

**操作：** 查看、编辑、复制、提交审核、启用/停用、查看版本历史、查看发送记录。

### 5.3 P02 消息模板编辑

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 编辑消息模板：MSG-SMS-APPT-01 预约成功提醒                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【基本信息】                                                                    │
│ 模板编码：[MSG-SMS-APPT-01]  模板名称：[预约成功提醒________]                    │
│ 渠道：[短信 ▼]  业务类型：[通知 ▼]  优先级：[普通 ▼]                            │
│ 第三方模板 ID：[SMS_202610001]  签名：【眼科医院】                              │
│ 是否需审核：[✓]  审核状态：已通过（2026-09-01）                                  │
│ 是否启用：[✓]  备注：[________________________________]                        │
│                                                                                │
│ 【内容】                                                                        │
│ 标题：[（短信无标题）____________]                                              │
│ 内容：                                                                          │
│ ┌──────────────────────────────────────────────────────────────────────┐       │
│ │ 尊敬的{{patient_name}}，您已成功预约{{doctor_name}}医生{{appt_time}}  │       │
│ │ 的门诊，请提前15分钟到院。如有疑问请致电{{hospital_phone}}。           │       │
│ └──────────────────────────────────────────────────────────────────────┘       │
│ 字符数：82/70（超出 1 条短信，将按 2 条计费）                                     │
│                                                                                │
│ 【变量】                                                                        │
│ 变量名          │显示名      │类型  │敏感│默认值                            │
│ patient_name    │患者姓名    │文本  │否  │—                                  │
│ doctor_name     │医生姓名    │文本  │否  │—                                  │
│ appt_time       │预约时间    │日期  │否  │—                                  │
│ hospital_phone  │医院电话    │文本  │否  │0571-88888888                      │
│ [+ 添加变量]                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [取消] [保存草稿] [提交审核] [启用]                                              │
└────────────────────────────────────────────────────────────────────────────────┘
```

**校验：**
- 模板编码唯一。
- 内容中的变量必须都在变量定义中。
- 短信字符数超出按条数计费，前端提示。
- 微信/短信模板需审核通过才能启用。
- 变量名不能重复。

### 5.4 P03 模板版本历史

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 模板版本历史：MSG-SMS-APPT-01                                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│ 版本│变更时间            │变更人│变更原因          │内容摘要              │操作│
│ v3  │2026-09-01 10:00:00 │信息科│优化文案           │尊敬的{{patient_name}}│[查看][对比]│
│ v2  │2026-08-15 14:00:00 │信息科│增加医院电话变量   │尊敬的{{patient_name}}│[查看][对比]│
│ v1  │2026-08-01 09:00:00 │信息科│首次创建           │尊敬的{{patient_name}}│[查看]│
├────────────────────────────────────────────────────────────────────────────────┤
│ [版本对比]                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 P04 渠道配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 渠道配置                                                                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 渠道  │供应商      │每日上限│单接收人频率      │状态  │操作                      │
│ 短信  │阿里云      │50000   │5 条/小时         │启用  │[编辑] [测试发送]         │
│ 微信  │微信官方    │20000   │3 条/小时         │启用  │[编辑] [测试发送]         │
│ 邮件  │腾讯企业邮  │10000   │10 条/小时        │启用  │[编辑] [测试发送]         │
│ 站内信│本模块      │不限    │不限              │启用  │[编辑]                    │
│ APP   │极光        │30000   │5 条/小时         │启用  │[编辑] [测试发送]         │
│ 语音  │阿里云      │1000    │1 条/小时         │停用  │[编辑] [启用]             │
└────────────────────────────────────────────────────────────────────────────────┘
```

**编辑字段：**

| 字段 | 控件 | 必填 | 说明 |
|---|---|---|---|
| 渠道代码 | 只读 | 是 | — |
| 渠道名称 | 文本 | 是 | — |
| 供应商 | 下拉 | 是 | 阿里云/腾讯云/微信/腾讯企业邮/极光/自建 |
| 网关地址 | 文本 | 是 | M21 封装后的地址 |
| 鉴权方式 | 下拉 | 是 | API_KEY/OAUTH2/账号密码 |
| 签名 | 文本 | 条件 | 短信/邮件必填 |
| 每日上限 | 数字 | 是 | 全局上限 |
| 单接收人每小时 | 数字 | 是 | 频控 |
| 单接收人每天 | 数字 | 是 | 频控 |
| 是否启用 | 开关 | 是 | — |

### 5.6 P05 消息发送任务列表

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息发送任务                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计卡片：今日任务 120 | 成功 98 | 部分失败 18 | 失败 4                        │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：任务号[____] 模板[全部▼] 渠道[全部▼] 业务类型[全部▼] 状态[全部▼]          │
│ 时间[今日/本周/自定义]                                                          │
│ 工具栏：[＋新建发送] [导出]                                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │任务号          │模板              │渠道  │总数│成功│失败│状态    │操作    │
│ ☐ │MT20261020001   │预约成功提醒      │短信  │100 │98  │2   │部分成功│[详情]  │
│ ☐ │MT20261020002   │术后随访提醒      │微信  │50  │50  │0   │成功    │[详情]  │
│ ☐ │MT20261020003   │会员生日礼        │短信  │200 │180 │20  │部分成功│[详情]  │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 120 条                                         [上一页] 1 2 3 ... [下一页]  │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.7 P06 消息发送记录

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息发送记录：MT20261020001  预约成功提醒                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：接收人[____] 状态[全部▼]                                                  │
│                                                                                │
│ 消息号         │接收人        │手机号掩码 │状态  │发送时间        │回执时间     │
│ MR20261020001  │P202610200001 王五│138****5678│已送达│10-20 10:00:00 │10-20 10:00:02│
│ MR20261020002  │P202610200002 李四│139****2345│已阅读│10-20 10:00:00 │10-20 10:05:00│
│ MR20261020003  │P202610200003 张三│137****8899│失败  │10-20 10:00:00 │—            │
│                │              │          │      │失败原因：号码空号          │
├────────────────────────────────────────────────────────────────────────────────┤
│ [导出] [批量重发]                                                               │
└────────────────────────────────────────────────────────────────────────────────┘
```

**记录详情字段：** 消息号、任务号、模板编码、模板版本、渠道、接收人类型、接收人 ID、接收人姓名、接收地址掩码、标题、内容快照、变量快照、状态、发送时间、送达时间、阅读时间、失败原因、重试次数、供应商消息 ID。

### 5.8 P07 消息回执统计

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息回执统计                                       时间范围：2026-10-01 ~ 2026-10-20│
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┬──────────┬──────────┐                       │
│ │ 总发送   │ 已送达   │ 已阅读   │ 失败     │ 退订     │                       │
│ │ 12,500   │ 12,200   │ 8,500    │ 300      │ 20       │                       │
│ └──────────┴──────────┴──────────┴──────────┴──────────┘                       │
│                                                                                │
│ 按渠道：                                                                        │
│ 短信：发送 8,000，送达 7,900（98.75%），失败 100                                 │
│ 微信：发送 3,000，送达 2,950（98.33%），阅读 2,500，失败 50                      │
│ 邮件：发送 1,000，送达 950（95%），失败 50                                       │
│ 站内信：发送 500，阅读 450（90%）                                                │
│                                                                                │
│ 失败原因分布：                                                                  │
│ 空号 120（40%）  关机 80（26.7%）  黑名单 60（20%）  其他 40（13.3%）            │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.9 P08 消息黑名单

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息黑名单                                                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│ [＋新增黑名单]                                                                  │
│                                                                                │
│ 接收人        │类型  │渠道  │业务类型│原因  │有效期  │状态  │操作              │
│ P202610200888 赵六│患者  │全部  │营销    │退订  │长期    │生效  │[解除]            │
│ P202610200999 测试│患者  │短信  │全部    │投诉  │长期    │生效  │[解除]            │
│ E24030017 张三│职工  │邮件  │系统    │异常  │2026-12-31│生效│[解除]            │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.10 P09 消息配置

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息配置                                        ⚠ 修改影响全院消息发送          │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【编码规则】                                                                    │
│ 任务前缀：[MT]  记录前缀：[MR]  流水位数：[4]                                   │
│                                                                                │
│ 【频控】                                                                        │
│ 单接收人每小时：[5] 条                                                          │
│ 单接收人每天：[20] 条                                                           │
│ 单任务单接收人：[3] 条                                                          │
│                                                                                │
│ 【重试】                                                                        │
│ 最大重试次数：[3] 次                                                            │
│ 重试间隔：[5, 15, 60] 分钟（逗号分隔）                                          │
│                                                                                │
│ 【脱敏】                                                                        │
│ 手机号：[3-4] 位掩码                                                            │
│ 邮箱：[1-3] 位掩码                                                              │
│                                                                                │
│ 【合并联动】                                                                    │
│ ☑ 订阅患者合并事件，自动更新消息记录 patient_id                                  │
│                                                                                │
│ 【退订】                                                                        │
│ ☑ 允许患者对营销类退订                                                          │
│ ☑ 退订后自动加黑名单                                                            │
│                                                                                │
│ 【回执】                                                                        │
│ ☑ 接收 M21 回执回调                                                             │
│ 回调失败重试：[3] 次                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│                                         [取消] [保存]                           │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.11 P10 变更日志

```text
┌────────────────────────────────────────────────────────────────────────────────┐
│ 消息变更日志                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：对象类型[模板/渠道/配置/黑名单▼] 对象编码[____] 操作[全部▼] 时间[____ ~ ____]│
├────────────────────────────────────────────────────────────────────────────────┤
│ 时间                │对象类型│对象编码        │操作        │操作人│详情           │
│ 2026-10-20 10:00:00 │模板    │MSG-SMS-APPT-01 │UPDATE      │信息科│新增变量：医院电话│
│ 2026-10-20 10:05:00 │渠道    │SMS             │UPDATE      │信息科│每日上限调整    │
│ 2026-10-20 10:10:00 │黑名单  │P202610200888   │CREATE      │客服  │患者退订营销    │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| **模板** | | | | |
| API-01 | GET | `/api/v1/mpi/messages/templates` | 模板分页列表 | `mpi:message:template:list` |
| API-02 | GET | `/api/v1/mpi/messages/templates/{id}` | 模板详情 | `mpi:message:template:list` |
| API-03 | POST | `/api/v1/mpi/messages/templates` | 新建模板 | `mpi:message:template:create` |
| API-04 | PUT | `/api/v1/mpi/messages/templates/{id}` | 修改模板（生成新版本） | `mpi:message:template:update` |
| API-05 | POST | `/api/v1/mpi/messages/templates/{id}/submit` | 提交审核 | `mpi:message:template:update` |
| API-06 | POST | `/api/v1/mpi/messages/templates/{id}/audit` | 审核（通过/驳回） | `mpi:message:template:audit` |
| API-07 | POST | `/api/v1/mpi/messages/templates/{id}/enable` | 启用模板 | `mpi:message:template:update` |
| API-08 | POST | `/api/v1/mpi/messages/templates/{id}/disable` | 停用模板 | `mpi:message:template:update` |
| API-09 | POST | `/api/v1/mpi/messages/templates/{id}/copy` | 复制模板 | `mpi:message:template:create` |
| API-10 | GET | `/api/v1/mpi/messages/templates/{id}/versions` | 版本历史 | `mpi:message:template:list` |
| API-11 | GET | `/api/v1/mpi/messages/templates/{id}/versions/compare` | 版本对比 | `mpi:message:template:list` |
| **渠道** | | | | |
| API-12 | GET | `/api/v1/mpi/messages/channels` | 渠道列表 | `mpi:message:channel:list` |
| API-13 | PUT | `/api/v1/mpi/messages/channels/{code}` | 修改渠道配置 | `mpi:message:channel:update` |
| API-14 | POST | `/api/v1/mpi/messages/channels/{code}/test` | 测试发送 | `mpi:message:channel:update` |
| **发送** | | | | |
| API-15 | POST | `/api/v1/mpi/messages/send` | 单条/批量发送 | `mpi:message:send` |
| API-16 | GET | `/api/v1/mpi/messages/tasks` | 发送任务列表 | `mpi:message:task:list` |
| API-17 | GET | `/api/v1/mpi/messages/tasks/{id}` | 任务详情 | `mpi:message:task:list` |
| API-18 | GET | `/api/v1/mpi/messages/tasks/{id}/records` | 任务记录列表 | `mpi:message:task:list` |
| API-19 | GET | `/api/v1/mpi/messages/records` | 记录查询（跨任务） | `mpi:message:record:list` |
| API-20 | GET | `/api/v1/mpi/messages/records/{id}` | 记录详情 | `mpi:message:record:list` |
| API-21 | POST | `/api/v1/mpi/messages/records/{id}/resend` | 单条重发 | `mpi:message:send` |
| API-22 | POST | `/api/v1/mpi/messages/tasks/{id}/records/batch-resend` | 批量重发 | `mpi:message:send` |
| API-23 | GET | `/api/v1/mpi/messages/tasks/statistics` | 任务统计 | `mpi:message:task:list` |
| **回执** | | | | |
| API-24 | GET | `/api/v1/mpi/messages/receipts` | 回执查询 | `mpi:message:receipt:list` |
| API-25 | GET | `/api/v1/mpi/messages/receipts/statistics` | 回执统计 | `mpi:message:receipt:list` |
| **黑名单** | | | | |
| API-26 | GET | `/api/v1/mpi/messages/blacklist` | 黑名单列表 | `mpi:message:blacklist:list` |
| API-27 | POST | `/api/v1/mpi/messages/blacklist` | 新增黑名单 | `mpi:message:blacklist:update` |
| API-28 | POST | `/api/v1/mpi/messages/blacklist/{id}/release` | 解除黑名单 | `mpi:message:blacklist:update` |
| **配置** | | | | |
| API-29 | GET | `/api/v1/mpi/messages/config` | 查询配置 | `mpi:message:config:list` |
| API-30 | PUT | `/api/v1/mpi/messages/config` | 修改配置 | `mpi:message:config:update` |
| **日志** | | | | |
| API-31 | GET | `/api/v1/mpi/messages/logs` | 变更日志 | `mpi:message:audit` |
| **内部契约** | | | | |
| API-32 | POST | `/internal/v1/message/send` | 业务模块调用发送 | 内部服务 |
| API-33 | POST | `/internal/v1/message/receipt` | M21 回执回调 | 内部服务 |
| API-34 | GET | `/internal/v1/message/pending-receipts` | M21 拉取待补发回执 | 内部服务 |
| API-35 | GET | `/internal/v1/message/unread-count` | 门户未读数 | 内部服务 |
| API-36 | GET | `/internal/v1/message/list` | 门户消息列表 | 内部服务 |
| API-37 | POST | `/internal/v1/message/merge-redirect` | 患者合并重定向 | 内部服务 |
| API-38 | GET | `/internal/v1/message/template/{code}` | 按编码取模板（供 M19 等） | 内部服务 |
| API-39 | POST | `/internal/v1/message/unsubscribe` | 患者退订 | 内部服务 |
| API-40 | GET | `/internal/v1/message/check-blacklist` | 黑名单校验 | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码（M03-05：52401~52440）**

| 错误码 | 含义 |
|---|---|
| 52401 | 模板不存在 |
| 52402 | 模板编码已存在 |
| 52403 | 模板状态不允许该操作 |
| 52404 | 模板未审核通过，不能启用 |
| 52405 | 模板变量未定义 |
| 52406 | 模板内容缺少变量 |
| 52407 | 模板变量定义重复 |
| 52408 | 模板字符数超限 |
| 52409 | 渠道不存在 |
| 52410 | 渠道未启用 |
| 52411 | 渠道配置非法 |
| 52412 | 渠道测试发送失败 |
| 52413 | 接收人不存在 |
| 52414 | 接收地址为空 |
| 52415 | 接收地址格式错误 |
| 52416 | 接收人在黑名单 |
| 52417 | 接收人已退订该业务类型 |
| 52418 | 触发频控 |
| 52419 | 模板变量缺失 |
| 52420 | 任务不存在 |
| 52421 | 任务状态不允许该操作 |
| 52422 | 记录不存在 |
| 52423 | 记录状态不允许重发 |
| 52424 | 记录已成功，无需重发 |
| 52425 | 重试次数超限 |
| 52426 | 网关调用失败 |
| 52427 | 回执格式非法 |
| 52428 | 回执重复 |
| 52429 | 回执对应记录不存在 |
| 52430 | 黑名单已存在 |
| 52431 | 黑名单不存在 |
| 52432 | 验证码/通知类不可退订 |
| 52433 | 配置项非法 |
| 52434 | 合并重定向失败 |
| 52435 | 合并冲突 |
| 52436 | 数据已变更，请刷新后重试 |
| 52437 | M21 网关服务不可用 |
| 52438 | M02 权限服务不可用 |
| 52439 | 导出数据量超限 |
| 52440 | 批量操作数量超限 |

### 6.3 关键接口示例

#### API-03 新建模板

```json
{
  "template_code": "MSG-SMS-APPT-01",
  "template_name": "预约成功提醒",
  "channel": "SMS",
  "biz_type": "NOTICE",
  "title": null,
  "content": "尊敬的{{patient_name}}，您已成功预约{{doctor_name}}医生{{appt_time}}的门诊，请提前15分钟到院。如有疑问请致电{{hospital_phone}}。",
  "variables": [
    {"name": "patient_name", "display_name": "患者姓名", "type": "TEXT", "sensitive": false},
    {"name": "doctor_name", "display_name": "医生姓名", "type": "TEXT", "sensitive": false},
    {"name": "appt_time", "display_name": "预约时间", "type": "DATETIME", "sensitive": false},
    {"name": "hospital_phone", "display_name": "医院电话", "type": "TEXT", "sensitive": false, "default_value": "0571-88888888"}
  ],
  "provider_template_id": "SMS_202610001",
  "sign_name": "眼科医院",
  "need_audit": true,
  "priority": "NORMAL"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 6001,
    "template_code": "MSG-SMS-APPT-01",
    "version": 1,
    "status": "DRAFT",
    "audit_status": "PENDING"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-04 修改模板（生成新版本）

```json
{
  "template_name": "预约成功提醒",
  "content": "尊敬的{{patient_name}}，您已成功预约{{doctor_name}}医生{{appt_time}}的门诊，请提前15分钟到院。",
  "variables": [
    {"name": "patient_name", "display_name": "患者姓名", "type": "TEXT", "sensitive": false},
    {"name": "doctor_name", "display_name": "医生姓名", "type": "TEXT", "sensitive": false},
    {"name": "appt_time", "display_name": "预约时间", "type": "DATETIME", "sensitive": false}
  ],
  "change_reason": "优化文案，去掉医院电话"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 6001,
    "template_code": "MSG-SMS-APPT-01",
    "version": 2,
    "status": "DRAFT",
    "audit_status": "PENDING"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-15 单条/批量发送

```json
{
  "template_code": "MSG-SMS-APPT-01",
  "channel": "SMS",
  "receivers": [
    {
      "receiver_type": "PATIENT",
      "receiver_id": 10001,
      "receiver_name": "王五",
      "receiver_addr": "13812345678",
      "variables": {
        "patient_name": "王五",
        "doctor_name": "张三",
        "appt_time": "2026-10-21 09:00",
        "hospital_phone": "0571-88888888"
      }
    }
  ],
  "biz_type": "NOTICE",
  "biz_no": "APPT202610200001",
  "scheduled_at": null,
  "priority": "NORMAL"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 5001,
    "task_no": "MT20261020001",
    "total_count": 1,
    "accepted_count": 1,
    "rejected_count": 0,
    "status": "SENDING"
  },
  "trace_id": "9f8a7b6c"
}
```

**接收人被拦截时的响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 5002,
    "task_no": "MT20261020002",
    "total_count": 1,
    "accepted_count": 0,
    "rejected_count": 1,
    "rejected": [
      {"receiver_id": 10001, "reason": "BLACKLIST"}
    ],
    "status": "COMPLETED"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-32 业务模块调用发送（内部）

```json
{
  "template_code": "MSG-WECHAT-FU-01",
  "channel": "WECHAT",
  "receivers": [
    {
      "receiver_type": "PATIENT",
      "receiver_id": 10001,
      "receiver_addr": "oXyz123abc",
      "variables": {
        "patient_name": "王五",
        "surgery_name": "白内障超声乳化+人工晶体植入术",
        "followup_date": "2026-10-21"
      }
    }
  ],
  "biz_type": "FOLLOWUP",
  "biz_no": "FTK20261021001",
  "source_module": "M03-04"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 5003,
    "task_no": "MT20261020003",
    "accepted_count": 1,
    "rejected_count": 0
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-33 M21 回执回调（内部）

```json
{
  "record_no": "MR20261020001",
  "provider_message_id": "ALI_202610200001",
  "receipt_type": "DELIVERED",
  "receipt_at": "2026-10-20T10:00:02",
  "error_code": null,
  "error_msg": null,
  "raw_data": {"status": "DELIVRD", "submit_time": "20261020100000"}
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "record_no": "MR20261020001",
    "receipt_type": "DELIVERED",
    "record_status": "DELIVERED",
    "duplicate": false
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-35 门户未读数（内部）

```
GET /internal/v1/message/unread-count?patient_id=10001&channel=INBOX
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10001,
    "unread_count": 3,
    "by_channel": {"INBOX": 3}
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-37 患者合并重定向（内部）

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
    "record_count": 8,
    "redirected": 7,
    "conflict": 1,
    "conflict_record_ids": [8008]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-39 患者退订（内部）

```json
{
  "patient_id": 10001,
  "channel": "SMS",
  "biz_type": "MARKETING",
  "reason": "患者通过短信回复 TD 退订"
}
```

**响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "patient_id": 10001,
    "channel": "SMS",
    "biz_type": "MARKETING",
    "blacklist_id": 9001,
    "status": "ACTIVE"
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
from app.schemas.mpi.message import (
    MessageReceiptRequest,
    MessageSendRequest,
    MessageTemplateCreate,
    MessageTemplateUpdate,
    MergeRedirectRequest,
    UnsubscribeRequest,
)
from app.services.mpi.message_service import MessageService

router = APIRouter(prefix="/api/v1/mpi/messages", tags=["M03-消息中心"])
internal_router = APIRouter(prefix="/internal/v1/message", tags=["M03-消息内部接口"])


@router.get("/templates")
async def list_templates(
    keyword: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:message:template:list")),
):
    svc = MessageService(db)
    items, total = await svc.list_templates(keyword, channel, page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@router.post("/templates")
async def create_template(
    payload: MessageTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:message:template:create")),
):
    svc = MessageService(db)
    return success_response(await svc.create_template(payload, operator=user))


@router.post("/send")
async def send_message(
    payload: MessageSendRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:message:send")),
):
    svc = MessageService(db)
    return success_response(await svc.send(payload, operator=user))


@router.get("/tasks")
async def list_tasks(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("mpi:message:task:list")),
):
    svc = MessageService(db)
    items, total = await svc.list_tasks(status, page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    ))


@internal_router.post("/send")
async def internal_send(
    payload: MessageSendRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return success_response(await svc.send(payload, operator=None))


@internal_router.post("/receipt")
async def internal_receipt(
    payload: MessageReceiptRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return success_response(await svc.handle_receipt(payload))


@internal_router.get("/unread-count")
async def internal_unread_count(
    patient_id: int = Query(...),
    channel: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return success_response(await svc.unread_count(patient_id, channel))


@internal_router.post("/unsubscribe")
async def internal_unsubscribe(
    payload: UnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return success_response(await svc.unsubscribe(payload))


@internal_router.post("/merge-redirect")
async def internal_merge_redirect(
    payload: MergeRedirectRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MessageService(db)
    return success_response(await svc.merge_redirect(payload))
```

### 6.5 Service 层核心逻辑示例

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crypto import decrypt_value, encrypt_value, mask_value
from app.core.exceptions import BizException
from app.models.mpi.message import (
    MpiMessageBlacklist,
    MpiMessageChannel,
    MpiMessageRecord,
    MpiMessageRetry,
    MpiMessageTask,
    MpiMessageTemplate,
    MpiMessageTemplateVersion,
)


class MessageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send(self, payload, operator=None):
        template = await self._get_template(payload.template_code)
        if template.status != "ENABLED":
            raise BizException(52403, "模板未启用")

        channel = await self._get_channel(payload.channel or template.channel)
        if not channel.is_enabled:
            raise BizException(52410, "渠道未启用")

        task = MpiMessageTask(
            task_no=await self._gen_task_no(),
            template_id=template.id,
            template_code=template.template_code,
            channel=channel.channel_code,
            biz_type=payload.biz_type,
            biz_no=payload.biz_no,
            source_module=payload.source_module,
            total_count=len(payload.receivers),
            status="SENDING",
            scheduled_at=payload.scheduled_at,
            sender_id=getattr(operator, "id", None),
            sender_name=getattr(operator, "name", None),
        )
        self.db.add(task)
        await self.db.flush()

        accepted, rejected = 0, 0
        records = []
        for r in payload.receivers:
            # 1. 黑名单校验
            blocked = await self._check_blacklist(
                r.receiver_type, r.receiver_id, channel.channel_code, payload.biz_type)
            if blocked:
                rejected += 1
                continue

            # 2. 频控
            if await self._check_frequency(
                    r.receiver_type, r.receiver_id, channel.channel_code, payload.biz_type):
                rejected += 1
                continue

            # 3. 变量校验
            content, missing = await self._render_content(template, r.variables)
            if missing:
                raise BizException(52419, f"模板变量缺失：{', '.join(missing)}")

            # 4. 创建记录
            record = MpiMessageRecord(
                record_no=await self._gen_record_no(),
                task_id=task.id,
                task_no=task.task_no,
                template_id=template.id,
                template_code=template.template_code,
                template_version=template.current_version,
                channel=channel.channel_code,
                biz_type=payload.biz_type,
                receiver_type=r.receiver_type,
                receiver_id=r.receiver_id,
                receiver_name=r.receiver_name,
                receiver_addr_enc=encrypt_value(r.receiver_addr),
                receiver_addr_mask=mask_value(r.receiver_addr, channel.channel_code),
                content_snapshot=content,
                content_vars_json=r.variables,
                status="PENDING",
                priority=payload.priority,
            )
            self.db.add(record)
            records.append(record)
            accepted += 1

        task.success_count = 0
        task.fail_count = rejected

        await self.db.flush()

        # 5. 调用网关（异步/同步）
        for record in records:
            await self._submit_to_gateway(record, channel)

        task.status = "COMPLETED" if rejected == 0 else "PARTIAL"
        await self.db.commit()
        return {
            "task_id": task.id,
            "task_no": task.task_no,
            "total_count": len(payload.receivers),
            "accepted_count": accepted,
            "rejected_count": rejected,
            "status": task.status,
        }

    async def handle_receipt(self, payload):
        record = (await self.db.execute(
            select(MpiMessageRecord).where(
                MpiMessageRecord.record_no == payload.record_no,
                MpiMessageRecord.is_deleted == False,
            )
        )).scalar_one_or_none()
        if not record:
            raise BizException(52429, "回执对应记录不存在")

        # 幂等：同类型回执不重复处理
        if payload.receipt_type == "DELIVERED" and record.status in ("DELIVERED", "READ"):
            return {"record_no": payload.record_no, "receipt_type": payload.receipt_type,
                    "record_status": record.status, "duplicate": True}

        if payload.receipt_type == "DELIVERED":
            record.status = "DELIVERED"
            record.delivered_at = payload.receipt_at or datetime.now()
        elif payload.receipt_type == "READ":
            record.status = "READ"
            record.read_at = payload.receipt_at or datetime.now()
        elif payload.receipt_type == "FAILED":
            if self._is_retryable(payload.error_code):
                record.status = "RETRYING"
                self.db.add(MpiMessageRetry(
                    record_id=record.id,
                    record_no=record.record_no,
                    retry_seq=1,
                    next_retry_at=datetime.now(),
                ))
            else:
                record.status = "FAILED"
                record.fail_reason = payload.error_msg
        elif payload.receipt_type == "UNSUBSCRIBED":
            await self._add_blacklist_from_unsubscribe(record)

        await self.db.commit()
        return {"record_no": record.record_no, "receipt_type": payload.receipt_type,
                "record_status": record.status, "duplicate": False}

    async def merge_redirect(self, payload):
        records = (await self.db.execute(
            select(MpiMessageRecord).where(
                MpiMessageRecord.receiver_type == "PATIENT",
                MpiMessageRecord.receiver_id == payload.secondary_patient_id,
                MpiMessageRecord.is_deleted == False,
            )
        )).scalars().all()
        conflict_ids = []
        for r in records:
            if r.status in ("SENDING", "RETRYING"):
                conflict_ids.append(r.id)
                continue
            r.receiver_id = payload.primary_patient_id
        await self.db.commit()
        return {
            "merge_id": payload.merge_id,
            "secondary_patient_id": payload.secondary_patient_id,
            "record_count": len(records),
            "redirected": len(records) - len(conflict_ids),
            "conflict": len(conflict_ids),
            "conflict_record_ids": conflict_ids,
        }

    async def _check_blacklist(self, receiver_type, receiver_id, channel, biz_type):
        stmt = select(MpiMessageBlacklist).where(
            MpiMessageBlacklist.receiver_type == receiver_type,
            MpiMessageBlacklist.receiver_id == receiver_id,
            MpiMessageBlacklist.status == "ACTIVE",
            MpiMessageBlacklist.is_deleted == False,
        )
        rows = (await self.db.execute(stmt)).scalars().all()
        for b in rows:
            if b.channel and b.channel != channel:
                continue
            if b.biz_type and b.biz_type != biz_type:
                continue
            return True
        return False

    async def _check_frequency(self, receiver_type, receiver_id, channel, biz_type):
        # 简化示例：按小时统计
        from datetime import timedelta
        since = datetime.now() - timedelta(hours=1)
        count = (await self.db.execute(
            select(func.count()).select_from(MpiMessageRecord).where(
                MpiMessageRecord.receiver_type == receiver_type,
                MpiMessageRecord.receiver_id == receiver_id,
                MpiMessageRecord.channel == channel,
                MpiMessageRecord.biz_type == biz_type,
                MpiMessageRecord.created_at >= since,
            )
        )).scalar_one()
        return count >= 5

    async def _render_content(self, template, variables):
        content = template.content
        missing = []
        for v in template.variables:
            name = v["name"]
            if name in variables:
                content = content.replace(f"{{{{{name}}}}}", str(variables[name]))
            elif v.get("default_value") is not None:
                content = content.replace(f"{{{{{name}}}}}", str(v["default_value"]))
            else:
                missing.append(name)
        return content, missing
```

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `mpi:msg:config` | String(JSON) | 30min | 消息配置 | 配置变更 |
| `mpi:msg:template:{code}` | String(JSON) | 30min | 模板当前版本 | 模板变更 |
| `mpi:msg:channel:{code}` | String(JSON) | 30min | 渠道配置 | 渠道变更 |
| `mpi:msg:blacklist:{type}:{id}` | Set(String) | 10min | 黑名单（渠道:业务类型） | 黑名单变更 |
| `mpi:msg:freq:{type}:{id}:{channel}:{biz}:{hour}` | String(计数) | 1h | 频控计数 | 自然过期 |
| `mpi:msg:unread:{patient_id}` | String(计数) | 5min | 门户未读数 | 消息变更 |
| `mpi:msg:stats` | String(JSON) | 5min | 统计卡片 | 定时刷新 |

### 7.2 Celery 异步任务

```python
from celery import shared_task


@shared_task
def message_retry_task():
    import asyncio
    return asyncio.run(_run_retry())


async def _run_retry():
    from datetime import datetime
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.message import MpiMessageRetry, MpiMessageRecord

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(MpiMessageRetry).where(
                MpiMessageRetry.status == "PENDING",
                MpiMessageRetry.next_retry_at <= datetime.now(),
            )
        )).scalars().all()
        for r in rows:
            record = (await db.execute(
                select(MpiMessageRecord).where(MpiMessageRecord.id == r.record_id)
            )).scalar_one()
            # 调用网关重发
            # 成功则改 record.status=SENT，否则 retry_seq +1 / FAILED
        await db.commit()
        return {"retried": len(rows)}


@shared_task
def message_pending_receipt_task():
    """拉取网关未回调的记录，主动查询"""
    import asyncio
    return asyncio.run(_query_pending())


async def _query_pending():
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.mpi.message import MpiMessageRecord

    async with AsyncSessionLocal() as db:
        # 发送中超过 5 分钟仍无回执
        threshold = datetime.now() - timedelta(minutes=5)
        rows = (await db.execute(
            select(MpiMessageRecord).where(
                MpiMessageRecord.status == "SENDING",
                MpiMessageRecord.created_at < threshold,
            )
        )).scalars().all()
        for r in rows:
            # 调用 M21 查询接口
            pass
        return {"queried": len(rows)}


@shared_task
def message_stats_refresh_task():
    import asyncio
    return asyncio.run(_refresh_stats())


async def _refresh_stats():
    from sqlalchemy import func, select
    from app.core.database import AsyncSessionLocal
    from app.core.redis import redis_client
    from app.models.mpi.message import MpiMessageRecord

    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(MpiMessageRecord.status, func.count())
            .where(MpiMessageRecord.created_at >= func.current_date())
            .group_by(MpiMessageRecord.status)
        )).all()
        data = {status: count for status, count in rows}
        import json
        await redis_client.setex("mpi:msg:stats", 300, json.dumps(data))
        return data
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_message_retry` | `*/5 * * * *` | 每 5 分钟重试失败消息 |
| `job_message_pending_receipt` | `*/10 * * * *` | 每 10 分钟查询无回执消息 |
| `job_message_stats_refresh` | `*/10 * * * *` | 刷新统计缓存 |
| `job_message_blacklist_expire` | `0 2 * * *` | 黑名单到期自动解除 |
| `job_message_record_partition` | `0 1 1 * *` | 创建记录下月分区 |
| `job_message_template_cache` | `0 6 * * *` | 预热模板缓存 |

---

## 8. 业务规则与校验

### 8.1 模板规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 模板编码唯一 | — | 52402 |
| 内容变量必须在变量定义中 | 正则提取 `{{var}}` 后校验 | 52405 |
| 变量定义不能重复 | — | 52407 |
| 短信字符数 | ≤ 500 字符（超出按多条计费，提示） | 52408 |
| 审核通过才能启用 | 短信/微信需审核 | 52404 |
| 修改生成新版本 | 版本号递增 | — |
| 模板状态 | DRAFT/ENABLED/DISABLED | 52403 |

### 8.2 发送规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 模板必须启用 | — | 52403 |
| 渠道必须启用 | — | 52410 |
| 接收地址必填 | — | 52414 |
| 接收地址格式 | 手机/邮箱/openid 按渠道校验 | 52415 |
| 接收人不能为空 | — | 52413 |
| 变量齐全 | 缺失拒绝发送 | 52419 |
| 黑名单拦截 | 接收人 + 渠道 + 业务类型 | 52416 |
| 退订拦截 | 营销类退订拦截 | 52417 |
| 频控拦截 | 超阈值拦截 | 52418 |

### 8.3 回执规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 回执必须对应记录 | — | 52429 |
| 同类型回执幂等 | 重复回执不重复处理 | 52428 |
| 状态流转合法 | PENDING→SENDING→SENT→DELIVERED→READ | — |
| 可重试错误 | 网络超时/网关限流进重试 | — |
| 不可重试错误 | 空号/关机/黑名单直接 FAILED | — |

### 8.4 黑名单规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 接收人 + 渠道 + 业务类型不能重复 | — | 52430 |
| 验证码/通知类不可退订 | — | 52432 |
| 营销类默认允许退订 | — | — |
| 退订自动加黑名单 | — | — |
| 黑名单到期自动解除 | 定时任务 | — |

### 8.5 并发控制

| 机制 | 说明 |
|---|---|
| 任务号/记录号 | Redis INCR + DB 唯一约束 |
| 回执幂等 | 唯一索引 `(record_no, receipt_type)` |
| 发送互斥 | Redis `mpi:msg:task:lock:{task_no}` |
| 合并重定向互斥 | Redis `mpi:msg:merge:lock:{patient_id}` |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `mpi:message:template:list` | 模板列表/详情 | 信息科、业务科室 |
| `mpi:message:template:create` | 新建/复制模板 | 信息科、业务科室 |
| `mpi:message:template:update` | 修改/启停/提交审核 | 信息科、业务科室 |
| `mpi:message:template:audit` | 模板审核 | 信息科长 |
| `mpi:message:channel:list` | 渠道列表 | 信息科 |
| `mpi:message:channel:update` | 渠道配置/测试 | 信息科长 |
| `mpi:message:send` | 发送消息 | 业务科室、会员运营 |
| `mpi:message:task:list` | 任务/记录列表 | 信息科、业务科室、客服 |
| `mpi:message:record:list` | 记录查询 | 信息科、客服 |
| `mpi:message:receipt:list` | 回执查询/统计 | 信息科、客服 |
| `mpi:message:blacklist:list` | 黑名单列表 | 信息科、客服 |
| `mpi:message:blacklist:update` | 黑名单维护 | 信息科 |
| `mpi:message:config:list` | 查询配置 | 信息科 |
| `mpi:message:config:update` | 修改配置 | 信息科长 |
| `mpi:message:audit` | 变更日志 | 审计员、信息科 |

### 9.2 权限矩阵

`●` 完全控制 `○` 可操作 `△` 只读 `—` 无权限

| 功能 | 信息科长 | 信息科 | 业务科室 | 会员运营 | 客服 | 审计员 |
|---|---|---|---|---|---|---|
| 模板列表 | ● | ● | △ | △ | △ | △ |
| 模板维护 | ● | ● | ○(本科室) | — | — | — |
| 模板审核 | ● | — | — | — | — | △ |
| 渠道配置 | ● | △ | — | — | — | △ |
| 发送消息 | ● | ● | ● | ● | — | — |
| 任务/记录 | ● | ● | △(本科室) | △(营销) | ● | △ |
| 回执统计 | ● | ● | △ | △ | ● | △ |
| 黑名单维护 | ● | ● | — | — | △ | △ |
| 配置维护 | ● | △ | — | — | — | △ |
| 变更日志 | ● | ● | — | — | — | ● |

### 9.3 数据权限

| 项 | 规则 |
|---|---|
| 模板 | 全院共享，业务科室可按业务类型筛选 |
| 任务/记录 | 全院可查，业务科室仅本模块产生的任务 |
| 接收地址 | 所有页面默认掩码，明文需权限 + 二次验证 |
| 内容快照 | 含敏感变量时脱敏展示 |

### 9.4 安全措施

- 接收地址 AES-256 加密存储，列表掩码展示。
- 内容快照中敏感变量替换为掩码后再存。
- 明文接收地址查看需 `mpi:message:sensitive` 权限 + M02-05 二次验证 + 写 `sys_audit_log`。
- 模板/渠道/配置/黑名单关键操作写 `sys_audit_log`。
- 内部接口使用服务令牌，禁止公网暴露。
- 回执回调校验 M21 服务令牌 + 签名。

---

## 10. 主数据分发与集成

### 10.1 分发目标

| 目标 | 分发内容 | 触发时机 | 方式 |
|---|---|---|---|
| M21 集成平台 | 发送请求 | 发送时 | HTTP 内部接口 |
| M03-06 门户 | 未读数、消息列表 | 查询时 | 内部接口 |
| M03-04 随访 | 消息发送结果（可选回执） | 发送后 | 事件（可选） |
| M03-02 合并 | 消息记录重定向结果 | 合并后 | 内部接口回执 |

### 10.2 事件清单

| 事件类型 | 触发时机 | 载荷 |
|---|---|---|
| `mpi.message.task.created` | 任务创建 | task_id, task_no, template_code, channel, total_count |
| `mpi.message.task.completed` | 任务完成 | task_id, success_count, fail_count |
| `mpi.message.record.sent` | 记录已发送 | record_id, record_no, channel |
| `mpi.message.record.delivered` | 记录已送达 | record_id, record_no |
| `mpi.message.record.failed` | 记录失败 | record_id, record_no, error_code |
| `mpi.message.unsubscribed` | 患者退订 | patient_id, channel, biz_type |
| `mpi.message.merge_conflict` | 合并时记录冲突 | record_ids, merge_id |

### 10.3 内部契约

| 接口 | 用途 | 调用方 | SLA |
|---|---|---|---|
| `POST /internal/v1/message/send` | 业务模块发送 | M03-04/M04/M09/M16/M19 | P95 ≤ 300ms |
| `POST /internal/v1/message/receipt` | M21 回执回调 | M21 | P95 ≤ 100ms |
| `GET /internal/v1/message/pending-receipts` | M21 拉取待补发回执 | M21 | P95 ≤ 100ms |
| `GET /internal/v1/message/unread-count` | 门户未读数 | M03-06 | P95 ≤ 50ms |
| `GET /internal/v1/message/list` | 门户消息列表 | M03-06 | P95 ≤ 100ms |
| `POST /internal/v1/message/merge-redirect` | 患者合并重定向 | M03-02 | P95 ≤ 200ms |
| `GET /internal/v1/message/template/{code}` | 按编码取模板 | M19 等 | P95 ≤ 50ms |
| `POST /internal/v1/message/unsubscribe` | 患者退订 | M03-06/M21 | P95 ≤ 100ms |
| `GET /internal/v1/message/check-blacklist` | 黑名单校验 | M19 等 | P95 ≤ 50ms |

**约定：** 内部发送接口不返回完整接收地址，只返回记录号与状态。

### 10.4 与 M21 集成平台的契约

**发送请求（本模块 → M21）：**

```json
{
  "channel": "SMS",
  "provider_template_id": "SMS_202610001",
  "receiver_addr_enc": "encrypted...",
  "content": "尊敬的张三，您已成功预约...",
  "sign_name": "眼科医院",
  "task_no": "MT20261020001",
  "record_no": "MR20261020001",
  "priority": "NORMAL"
}
```

**回执回调（M21 → 本模块）：**

```json
{
  "record_no": "MR20261020001",
  "provider_message_id": "ALI_202610200001",
  "receipt_type": "DELIVERED",
  "receipt_at": "2026-10-20T10:00:02",
  "error_code": null,
  "error_msg": null,
  "raw_data": {"status": "DELIVRD"},
  "signature": "hmac..."
}
```

**回执补发（M21 拉取）：** `GET /internal/v1/message/pending-receipts?since=...` 返回近期未回调成功的记录，M21 主动查询网关后补发。

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| 参数异常 | 模板变量缺失、地址格式 | 40001 + 字段错误 |
| 业务异常 | 黑名单、频控、状态不允许 | 524xx |
| 并发异常 | 回执重复、重定向冲突 | 幂等返回 |
| 依赖异常 | M21 网关不可用 | 记录 PENDING，定时重试 |
| 系统异常 | DB 失败 | 50000 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| M21 网关 | 记录保留 PENDING，定时任务重试；不阻塞业务 |
| M03-01 患者服务 | 接收人地址由调用方提供，不强制查患者 |
| M02 权限服务 | 拒绝访问，不降级放行 |
| Redis | 直连 DB，频控退化为 DB 查询 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-10-20T10:00:00.123+08:00",
  "level": "INFO",
  "logger": "app.services.mpi.message_service",
  "trace_id": "3f2a1b9c",
  "action": "MESSAGE_SENT",
  "task_no": "MT20261020001",
  "record_no": "MR20261020001",
  "template_code": "MSG-SMS-APPT-01",
  "channel": "SMS",
  "biz_type": "NOTICE",
  "receiver_type": "PATIENT",
  "receiver_id": 10001,
  "receiver_mask": "138****5678",
  "result": "SUCCESS"
}
```

**禁止记录：** 完整手机号/邮箱/openid、完整内容中的敏感变量、加密密钥。

### 11.3 监控指标

| 指标 | 告警阈值 |
|---|---|
| 接口错误率 | >1% |
| 发送接口 P95 | >300ms |
| 回执回调 P95 | >100ms |
| 发送成功率 | <95% |
| 回执回调成功率 | <98% |
| 重试队列积压 | >1000 |
| 黑名单命中次数 | 异常突增 |
| 单渠道每日发送量 | 超过 90% 上限 |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 通过标准 |
|---|---|---|
| AC-01 | 新建模板 | 成功，状态 DRAFT |
| AC-02 | 模板编码唯一 | 重复返回 52402 |
| AC-03 | 模板变量校验 | 内容变量未定义返回 52405 |
| AC-04 | 变量重复 | 返回 52407 |
| AC-05 | 短信字符数 | 超限提示 |
| AC-06 | 模板修改生成新版本 | 版本号 +1 |
| AC-07 | 模板审核 | 通过/驳回状态正确 |
| AC-08 | 未审核启用 | 返回 52404 |
| AC-09 | 模板启停 | 状态流转正确 |
| AC-10 | 版本历史 | 可查看、可对比 |
| AC-11 | 渠道配置 | 增改查正确 |
| AC-12 | 渠道测试发送 | 成功/失败提示 |
| AC-13 | 渠道未启用发送 | 返回 52410 |
| AC-14 | 单条发送 | 成功，任务+记录生成 |
| AC-15 | 批量发送 | 成功，统计正确 |
| AC-16 | 模板变量缺失 | 返回 52419 |
| AC-17 | 接收人黑名单 | 拦截，rejected_count +1 |
| AC-18 | 频控 | 超限拦截 |
| AC-19 | 接收地址格式 | 非法返回 52415 |
| AC-20 | 任务列表 | 按条件筛选正确 |
| AC-21 | 任务详情 | 统计正确 |
| AC-22 | 记录列表 | 按任务/状态筛选正确 |
| AC-23 | 记录详情 | 展示内容快照、回执 |
| AC-24 | 单条重发 | 成功 |
| AC-25 | 批量重发 | 成功 |
| AC-26 | 重试超限 | 返回 52425 |
| AC-27 | 回执回调 | 状态更新正确 |
| AC-28 | 回执幂等 | 重复回执不重复处理 |
| AC-29 | 回执对应记录不存在 | 返回 52429 |
| AC-30 | 可重试错误进重试 | 状态 RETRYING |
| AC-31 | 不可重试错误直接失败 | 状态 FAILED |
| AC-32 | 回执统计 | 数字正确 |
| AC-33 | 黑名单新增 | 成功 |
| AC-34 | 黑名单重复 | 返回 52430 |
| AC-35 | 验证码退订 | 返回 52432 |
| AC-36 | 黑名单解除 | 状态 RELEASED |
| AC-37 | 黑名单到期解除 | 定时任务生效 |
| AC-38 | 消息配置 | 校验通过 |
| AC-39 | 变更日志 | 全量留痕 |
| AC-40 | 门户未读数 | 内部接口正确 |
| AC-41 | 门户消息列表 | 内部接口正确 |
| AC-42 | 患者合并重定向 | 记录 patient_id 更新 |
| AC-43 | 合并冲突 | 执行中记录返回冲突 |
| AC-44 | 权限控制 | 无权限 403 |
| AC-45 | 审计日志 | 关键操作写 `sys_audit_log` |
| AC-46 | 乐观锁 | 版本冲突返回 52436 |
| AC-47 | 任务号唯一 | 并发不重复 |
| AC-48 | 记录号唯一 | 并发不重复 |
| AC-49 | 内容敏感变量脱敏 | 快照中掩码 |
| AC-50 | 接收地址掩码 | 列表/详情掩码 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | 模板列表 | 50 并发 P95 ≤ 500ms |
| PF-02 | 发送接口（100 接收人） | P95 ≤ 300ms |
| PF-03 | 回执回调 | 500 并发 P95 ≤ 100ms |
| PF-04 | 任务列表 | 50 并发 P95 ≤ 500ms |
| PF-05 | 记录列表 | 50 并发 P95 ≤ 500ms |
| PF-06 | 门户未读数 | 200 并发 P95 ≤ 50ms |
| PF-07 | 重试队列 1000 条 | ≤ 5min |
| PF-08 | 长稳 72h | 无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | 接收地址加密率 | 100% |
| DA-02 | 内容快照留存率 | 100% |
| DA-03 | 回执落库率 | 100% |
| DA-04 | 状态流转合法率 | 100% |
| DA-05 | 模板版本完整 | 100% |
| DA-06 | 任务统计准确率 | 100% |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | 明文接收地址泄漏 | 0 处 |
| SC-02 | 未授权查看明文 | 403 + 审计 |
| SC-03 | 内部接口公网暴露 | 禁止 |
| SC-04 | 回执回调签名校验 | 必须通过 |
| SC-05 | 关键操作审计 | 100% 写 `sys_audit_log` |
| SC-06 | 导出脱敏 | 通过 |
| SC-07 | 黑名单绕过 | 拦截 |

---

## 附录 A：渠道代码与频控默认值

| 渠道 | 代码 | 每日上限 | 单接收人/小时 | 单接收人/天 |
|---|---|---|---|---|
| 短信 | `SMS` | 50,000 | 5 | 20 |
| 微信 | `WECHAT` | 20,000 | 3 | 15 |
| 邮件 | `EMAIL` | 10,000 | 10 | 30 |
| 站内信 | `INBOX` | 不限 | 不限 | 不限 |
| APP 推送 | `APP_PUSH` | 30,000 | 5 | 20 |
| 语音 | `VOICE` | 1,000 | 1 | 3 |

## 附录 B：业务类型与退订策略

| 业务类型 | 代码 | 可退订 | 默认黑名单 |
|---|---|---|---|
| 验证码 | `VERIFY_CODE` | 否 | — |
| 通知 | `NOTICE` | 否 | — |
| 随访 | `FOLLOWUP` | 是 | 否 |
| 会员 | `MEMBER` | 是 | 否 |
| 营销 | `MARKETING` | 是 | 是（退订即加） |
| 满意度 | `SATISFACTION` | 是 | 否 |
| 系统 | `SYSTEM` | 否 | — |

## 附录 C：消息状态流转

| 当前 | 操作 | 目标 | 触发方 |
|---|---|---|---|
| PENDING | 提交网关 | SENDING | 系统 |
| SENDING | 回执已发送 | SENT | M21 |
| SENDING | 回执送达 | DELIVERED | M21 |
| SENT | 回执送达 | DELIVERED | M21 |
| DELIVERED | 回执阅读 | READ | M21 |
| SENDING | 可重试失败 | RETRYING | 系统 |
| RETRYING | 重试提交 | SENDING | 系统 |
| RETRYING | 重试超限 | FAILED | 系统 |
| SENDING | 不可重试失败 | FAILED | 系统 |
| PENDING | 超时 | EXPIRED | 系统 |
| 任意 | 黑名单/频控拦截 | REJECTED | 系统 |

## 附录 D：模板变量类型

| 类型 | 代码 | 说明 |
|---|---|---|
| 文本 | `TEXT` | 普通字符串 |
| 数字 | `NUMBER` | 整数/小数 |
| 日期 | `DATE` | 日期 |
| 日期时间 | `DATETIME` | 日期+时间 |
| 金额 | `AMOUNT` | 金额，两位小数 |
| 布尔 | `BOOL` | 是/否 |

## 附录 E：系统参数（M01 `md_sys_param`）

| 参数编码 | 默认值 | 说明 |
|---|---|---|
| `MPI.MSG.TASK_PREFIX` | `MT` | 任务号前缀 |
| `MPI.MSG.RECORD_PREFIX` | `MR` | 记录号前缀 |
| `MPI.MSG.SEQ_LEN` | `4` | 流水位数 |
| `MPI.MSG.RETRY.MAX` | `3` | 最大重试次数 |
| `MPI.MSG.RETRY.INTERVALS` | `5,15,60` | 重试间隔（分钟） |
| `MPI.MSG.FREQ.HOUR` | `5` | 单接收人每小时上限 |
| `MPI.MSG.FREQ.DAY` | `20` | 单接收人每天上限 |
| `MPI.MSG.FREQ.TASK` | `3` | 单任务单接收人上限 |
| `MPI.MSG.MASK.MOBILE` | `3-4` | 手机号掩码规则 |
| `MPI.MSG.MASK.EMAIL` | `1-3` | 邮箱掩码规则 |
| `MPI.MSG.RECEIPT.RETRY` | `3` | 回执回调失败重试次数 |

## 附录 F：术语表

| 术语 | 说明 |
|---|---|
| 渠道 | 短信/微信/邮件/站内信/APP 推送 |
| 模板 | 消息内容模板，含变量定义 |
| 模板版本 | 模板每次修改生成的版本 |
| 发送任务 | 一次批量发送的批次 |
| 发送记录 | 任务内单条消息 |
| 回执 | 网关返回的送达/阅读/失败等状态 |
| 黑名单 | 禁止发送的接收人 + 渠道 + 业务类型 |
| 频控 | 按接收人/渠道/业务类型/时间窗口限流 |
| 可重试错误 | 网络超时、网关限流等可重试的失败 |
| 不可重试错误 | 空号、关机、黑名单等不可重试的失败 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：页面 10 个、数据表 12 张、接口 40 个 | 系统设计组 |