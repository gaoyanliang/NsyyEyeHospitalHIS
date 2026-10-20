# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块数据结构：消息

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 消息（Message Center）
**主数据域：** 患者域（`MPI`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 05 消息 详细设计》《M01 主数据管理MDM》《M02 统一权限与安全》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「消息中心」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[消息详细设计](M03_患者服务与EMPI_05_消息_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [消息详细设计](M03_患者服务与EMPI_05_消息_详细设计.md)
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md)
- [01 患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md)
- [02 患者匹配合并与质量数据结构](M03_患者服务与EMPI_02_患者匹配合并与质量_数据结构.md)
- [03 会员数据结构](M03_患者服务与EMPI_03_会员_数据结构.md)
- [04 随访数据结构](M03_患者服务与EMPI_04_随访_数据结构.md)
- [M01 数据结构设计汇总](../M01主数据管理MDM/M01_主数据管理MDM_数据结构设计汇总.md)
- [M02 账号管理数据结构](../M02统一权限与安全/M02_统一权限与安全_01_账号管理_数据结构.md)
- [M02 审计日志数据结构](../M02统一权限与安全/M02_统一权限与安全_06_审计日志_数据结构.md)

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 12 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_message_config`（消息配置表）](#42-表mpi_message_config消息配置表)
- [4.3 表：`mpi_message_channel`（渠道配置表）](#43-表mpi_message_channel渠道配置表)
- [4.4 表：`mpi_message_template`（消息模板表）](#44-表mpi_message_template消息模板表)
- [4.5 表：`mpi_message_template_version`（模板版本表）](#45-表mpi_message_template_version模板版本表)
- [4.6 表：`mpi_message_task`（发送任务表）](#46-表mpi_message_task发送任务表)
- [4.7 表：`mpi_message_record`（发送记录表）](#47-表mpi_message_record发送记录表)
- [4.8 表：`mpi_message_receipt`（回执表）](#48-表mpi_message_receipt回执表)
- [4.9 表：`mpi_message_retry`（重试队列表）](#49-表mpi_message_retry重试队列表)
- [4.10 表：`mpi_message_blacklist`（黑名单表）](#410-表mpi_message_blacklist黑名单表)
- [4.11 表：`mpi_message_log`（变更日志表）](#411-表mpi_message_log变更日志表)
- [4.12 表：`mpi_message_code_seq`（编码序列表）](#412-表mpi_message_code_seq编码序列表)
- [4.13 表：`mpi_message_unsubscribe`（退订记录表）](#413-表mpi_message_unsubscribe退订记录表)
- [4.14 SQLAlchemy 2.0 模型定义](#414-sqlalchemy-20-模型定义)
- [4.15 Pydantic Schema 定义](#415-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_message_config` | 消息配置表（单行） |
| 4.3 | `mpi_message_channel` | 渠道配置表 |
| 4.4 | `mpi_message_template` | 消息模板表 |
| 4.5 | `mpi_message_template_version` | 模板版本表 |
| 4.6 | `mpi_message_task` | 发送任务表 |
| 4.7 | `mpi_message_record` | 发送记录表 |
| 4.8 | `mpi_message_receipt` | 回执表 |
| 4.9 | `mpi_message_retry` | 重试队列表 |
| 4.10 | `mpi_message_blacklist` | 黑名单表 |
| 4.11 | `mpi_message_log` | 变更日志表 |
| 4.12 | `mpi_message_code_seq` | 编码序列表 |
| 4.13 | `mpi_message_unsubscribe` | 退订记录表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 01/02/03/04 依赖（逻辑引用）                                          │
│ mpi_patient / mpi.patient.merged 事件 / 会员等级 / 随访任务事件       │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ M01/M02/M21 依赖（逻辑引用）                                          │
│ mdm_employee / mdm_department / md_dict_item / md_sys_param         │
│ sys_account / sys_audit_log / M21 网关                               │
└──────────────────────────────────────────────────────────────────────┘

配置与模板：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_message_config           │  │ mpi_message_channel          │
│ （消息配置，单行）             │  │ （渠道配置）                  │
└──────────────────────────────┘  └──────────────────────────────┘
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_message_template         │──►│ mpi_message_template_version │
│ （模板主档）                  │  │ （模板版本，1:N）             │
└──────────┬───────────────────┘  └──────────────────────────────┘
           │ 1:N
           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_message_task             │──►│ mpi_message_record           │
│ （发送任务）                  │  │ （发送记录，1:N）             │
└──────────┬───────────────────┘  └──────────┬───────────────────┘
           │                                  │ 1:N
           ▼                                  ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_message_log              │  │ mpi_message_receipt          │
│ （变更日志，月分区）           │  │ （回执）                      │
└──────────────────────────────┘  └──────────────────────────────┘
                                  ┌──────────────────────────────┐
                                  │ mpi_message_retry            │
                                  │ （重试队列）                  │
                                  └──────────────────────────────┘

黑名单与退订：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_message_blacklist        │◄─│ mpi_message_unsubscribe      │
│ （黑名单）                    │  │ （退订记录，来源）            │
└──────────────────────────────┘  └──────────────────────────────┘

编码：
┌──────────────────────────────┐
│ mpi_message_code_seq         │
│ （任务/记录号序列，DB 对账）   │
└──────────────────────────────┘
```

**说明：**

- 所有表统一 `mpi_` 前缀，逻辑删除统一 `is_deleted BOOLEAN DEFAULT FALSE`。
- 状态统一 `VARCHAR(16)`，大写英文枚举。
- 跨模块逻辑引用不建物理外键。
- 日志表 `mpi_message_log` 与记录 `mpi_message_record` 按 `created_at` 月度 RANGE 分区。
- 接收地址加密存储 + 掩码；内容快照中的敏感变量替换为掩码后再存。
- 模板主档保存 `current_version` 指向当前版本，`mpi_message_template_version` 保存历史版本。

### 4.2 表：`mpi_message_config`（消息配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| task_prefix | VARCHAR(8) | N | 'MT' | 任务号前缀 |
| record_prefix | VARCHAR(8) | N | 'MR' | 记录号前缀 |
| seq_len | INT | N | 4 | 流水位数 |
| retry_max | INT | N | 3 | 最大重试次数 |
| retry_intervals | VARCHAR(64) | N | '5,15,60' | 重试间隔（分钟，逗号分隔） |
| freq_hour | INT | N | 5 | 单接收人每小时上限 |
| freq_day | INT | N | 20 | 单接收人每天上限 |
| freq_task | INT | N | 3 | 单任务单接收人上限 |
| mask_mobile | VARCHAR(16) | N | '3-4' | 手机号掩码规则 |
| mask_email | VARCHAR(16) | N | '1-3' | 邮箱掩码规则 |
| receipt_retry | INT | N | 3 | 回执回调失败重试次数 |
| allow_marketing_unsubscribe | BOOLEAN | N | TRUE | 允许营销退订 |
| auto_blacklist_on_unsubscribe | BOOLEAN | N | TRUE | 退订自动加黑名单 |
| subscribe_patient_merge | BOOLEAN | N | TRUE | 订阅患者合并事件 |
| sensitive_view_ttl | INT | N | 300 | 明文接收地址查看有效期（秒） |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人（`sys_account.id`） |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_mpi_message_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_message_config
    ADD CONSTRAINT ck_mpi_message_config_single_row CHECK (id = 1);
```

### 4.3 表：`mpi_message_channel`（渠道配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| channel_code | VARCHAR(32) | N | - | 渠道代码：SMS/WECHAT/EMAIL/INBOX/APP_PUSH/VOICE |
| channel_name | VARCHAR(64) | N | - | 渠道名称 |
| provider | VARCHAR(64) | Y | NULL | 供应商：ALIYUN/TENCENT/WECHAT/TENCENT_EMAIL/JPUSH/SELF |
| gateway_url | VARCHAR(500) | Y | NULL | M21 网关地址 |
| auth_type | VARCHAR(32) | Y | NULL | API_KEY/OAUTH2/PASSWORD |
| sign_name | VARCHAR(64) | Y | NULL | 签名（短信/邮件） |
| daily_limit | BIGINT | N | 0 | 每日上限（0=不限） |
| hourly_per_receiver | INT | N | 5 | 单接收人每小时上限 |
| daily_per_receiver | INT | N | 20 | 单接收人每天上限 |
| mask_rule | VARCHAR(32) | Y | NULL | 脱敏规则代码 |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| sort_no | INT | N | 999 | 排序 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_message_channel_code(channel_code, is_deleted)` 唯一；`idx_mpi_message_channel_enabled(is_enabled, sort_no)`。

**约束说明**

```sql
ALTER TABLE mpi_message_channel
    ADD CONSTRAINT ck_mpi_message_channel_code
    CHECK (channel_code IN ('SMS', 'WECHAT', 'EMAIL', 'INBOX', 'APP_PUSH', 'VOICE'));
```

**预置渠道：**

| channel_code | channel_name | provider | 默认每日上限 |
|---|---|---|---|
| `SMS` | 短信 | ALIYUN | 50000 |
| `WECHAT` | 微信 | WECHAT | 20000 |
| `EMAIL` | 邮件 | TENCENT_EMAIL | 10000 |
| `INBOX` | 站内信 | SELF | 0（不限） |
| `APP_PUSH` | APP 推送 | JPUSH | 30000 |
| `VOICE` | 语音 | ALIYUN | 1000 |

### 4.4 表：`mpi_message_template`（消息模板表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| template_code | VARCHAR(64) | N | - | 模板编码 |
| template_name | VARCHAR(128) | N | - | 模板名称 |
| channel_code | VARCHAR(32) | N | - | 渠道代码 |
| biz_type | VARCHAR(32) | N | - | 业务类型：VERIFY_CODE/NOTICE/FOLLOWUP/MEMBER/MARKETING/SATISFACTION/SYSTEM |
| title | VARCHAR(255) | Y | NULL | 标题（站内信/邮件/APP 推送用） |
| content | TEXT | N | - | 内容（含变量 `{{var}}`） |
| variables_json | JSONB | Y | NULL | 变量定义列表 |
| provider_template_id | VARCHAR(128) | Y | NULL | 第三方模板 ID |
| sign_name | VARCHAR(64) | Y | NULL | 签名 |
| priority | VARCHAR(16) | N | 'NORMAL' | 优先级：HIGH/NORMAL/LOW |
| need_audit | BOOLEAN | N | TRUE | 是否需要审核 |
| audit_status | VARCHAR(16) | N | 'PENDING' | DRAFT/PENDING/APPROVED/REJECTED |
| audit_by | BIGINT | Y | NULL | 审核人 |
| audit_by_name | VARCHAR(64) | Y | NULL | 审核人姓名 |
| audit_at | TIMESTAMP | Y | NULL | 审核时间 |
| audit_remark | VARCHAR(500) | Y | NULL | 审核备注 |
| current_version | INT | N | 1 | 当前版本号 |
| status | VARCHAR(16) | N | 'DRAFT' | DRAFT/ENABLED/DISABLED |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_message_template | PRIMARY | id | 主键 |
| uk_mpi_message_template_code | UNIQUE | template_code, is_deleted | 模板编码唯一 |
| idx_mpi_message_template_channel | NORMAL | channel_code, status | 按渠道 |
| idx_mpi_message_template_biz | NORMAL | biz_type, status | 按业务类型 |
| idx_mpi_message_template_audit | NORMAL | audit_status, created_at | 按审核状态 |

**约束说明**

```sql
ALTER TABLE mpi_message_template
    ADD CONSTRAINT ck_mpi_message_template_biz
    CHECK (biz_type IN ('VERIFY_CODE', 'NOTICE', 'FOLLOWUP', 'MEMBER',
                         'MARKETING', 'SATISFACTION', 'SYSTEM'));

ALTER TABLE mpi_message_template
    ADD CONSTRAINT ck_mpi_message_template_audit
    CHECK (audit_status IN ('DRAFT', 'PENDING', 'APPROVED', 'REJECTED'));

ALTER TABLE mpi_message_template
    ADD CONSTRAINT ck_mpi_message_template_status
    CHECK (status IN ('DRAFT', 'ENABLED', 'DISABLED'));
```

### 4.5 表：`mpi_message_template_version`（模板版本表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(64) | N | - | 模板编码（冗余） |
| version | INT | N | - | 版本号（从 1 递增） |
| title | VARCHAR(255) | Y | NULL | 标题 |
| content | TEXT | N | - | 内容 |
| variables_json | JSONB | Y | NULL | 变量定义快照 |
| change_reason | VARCHAR(500) | Y | NULL | 变更原因 |
| is_current | BOOLEAN | N | FALSE | 是否当前版本 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_mpi_message_template_version(template_id, version)` 唯一；`uk_mpi_message_template_current(template_id, is_current)` 部分唯一（`WHERE is_current=TRUE`）；`idx_mpi_message_template_version_time(created_at)`。

**约束说明**

```sql
CREATE UNIQUE INDEX uk_mpi_message_template_current
    ON mpi_message_template_version (template_id)
    WHERE is_current = TRUE;
```

### 4.6 表：`mpi_message_task`（发送任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_no | VARCHAR(32) | N | - | 任务号 `MT+yyyyMMdd+流水` |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(64) | N | - | 模板编码（冗余） |
| channel_code | VARCHAR(32) | N | - | 渠道代码 |
| biz_type | VARCHAR(32) | N | - | 业务类型 |
| biz_no | VARCHAR(64) | Y | NULL | 关联业务单号 |
| source_module | VARCHAR(16) | Y | NULL | 来源模块（M03-04/M04/M09/M16/M19 等） |
| total_count | INT | N | 0 | 总接收人数 |
| accepted_count | INT | N | 0 | 受理数（进入网关） |
| rejected_count | INT | N | 0 | 拦截数（黑名单/频控/退订） |
| success_count | INT | N | 0 | 成功数（送达/阅读） |
| fail_count | INT | N | 0 | 失败数 |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/SENDING/COMPLETED/PARTIAL/FAILED/CANCELLED |
| scheduled_at | TIMESTAMP | Y | NULL | 计划发送时间（NULL=立即） |
| started_at | TIMESTAMP | Y | NULL | 开始时间 |
| finished_at | TIMESTAMP | Y | NULL | 结束时间 |
| sender_id | BIGINT | Y | NULL | 发送人 |
| sender_name | VARCHAR(64) | Y | NULL | 发送人姓名 |
| priority | VARCHAR(16) | N | 'NORMAL' | 优先级 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_message_task | PRIMARY | id | 主键 |
| uk_mpi_message_task_no | UNIQUE | task_no, is_deleted | 任务号唯一 |
| idx_mpi_message_task_template | NORMAL | template_code, status | 按模板 |
| idx_mpi_message_task_channel | NORMAL | channel_code, status | 按渠道 |
| idx_mpi_message_task_biz | NORMAL | biz_type, status | 按业务类型 |
| idx_mpi_message_task_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_message_task_source | NORMAL | source_module, created_at | 按来源模块 |

**约束说明**

```sql
ALTER TABLE mpi_message_task
    ADD CONSTRAINT ck_mpi_message_task_status
    CHECK (status IN ('PENDING', 'SENDING', 'COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED'));
```

### 4.7 表：`mpi_message_record`（发送记录表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| record_no | VARCHAR(32) | N | - | 消息号 `MR+yyyyMMdd+流水` |
| task_id | BIGINT | N | - | 任务 ID |
| task_no | VARCHAR(32) | Y | NULL | 任务号（冗余） |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(64) | N | - | 模板编码（冗余） |
| template_version | INT | N | - | 模板版本 |
| channel_code | VARCHAR(32) | N | - | 渠道代码 |
| biz_type | VARCHAR(32) | N | - | 业务类型 |
| biz_no | VARCHAR(64) | Y | NULL | 关联业务单号 |
| receiver_type | VARCHAR(16) | N | - | 接收人类型：PATIENT/STAFF |
| receiver_id | BIGINT | N | - | 接收人 ID |
| receiver_name | VARCHAR(64) | Y | NULL | 接收人姓名 |
| receiver_addr_enc | VARCHAR(512) | N | - | 接收地址加密值（手机号/邮箱/openid） |
| receiver_addr_mask | VARCHAR(64) | Y | NULL | 接收地址掩码 |
| title | VARCHAR(255) | Y | NULL | 标题快照 |
| content_snapshot | TEXT | N | - | 内容快照（敏感变量已脱敏） |
| content_vars_json | JSONB | Y | NULL | 变量快照（敏感变量已脱敏） |
| provider_message_id | VARCHAR(128) | Y | NULL | 网关返回的消息 ID |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/SENDING/SENT/DELIVERED/READ/RETRYING/FAILED/EXPIRED/REJECTED |
| send_at | TIMESTAMP | Y | NULL | 发送时间 |
| delivered_at | TIMESTAMP | Y | NULL | 送达时间 |
| read_at | TIMESTAMP | Y | NULL | 阅读时间 |
| fail_code | VARCHAR(64) | Y | NULL | 失败代码 |
| fail_reason | VARCHAR(500) | Y | NULL | 失败原因 |
| reject_reason | VARCHAR(64) | Y | NULL | 拦截原因：BLACKLIST/UNSUBSCRIBE/FREQUENCY_LIMIT |
| retry_count | INT | N | 0 | 重试次数 |
| priority | VARCHAR(16) | N | 'NORMAL' | 优先级 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_message_record | PRIMARY | id | 主键 |
| uk_mpi_message_record_no | UNIQUE | record_no, is_deleted | 消息号唯一 |
| idx_mpi_message_record_task | NORMAL | task_id, status | 按任务 |
| idx_mpi_message_record_receiver | NORMAL | receiver_type, receiver_id, status | 按接收人 |
| idx_mpi_message_record_channel | NORMAL | channel_code, status | 按渠道 |
| idx_mpi_message_record_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_message_record_freq | NORMAL | receiver_type, receiver_id, channel_code, biz_type, created_at | 频控查询 |
| idx_mpi_message_record_unread | NORMAL | receiver_id, status | 未读数查询 |

**约束说明**

```sql
ALTER TABLE mpi_message_record
    ADD CONSTRAINT ck_mpi_message_record_status
    CHECK (status IN ('PENDING', 'SENDING', 'SENT', 'DELIVERED', 'READ',
                       'RETRYING', 'FAILED', 'EXPIRED', 'REJECTED'));

ALTER TABLE mpi_message_record
    ADD CONSTRAINT ck_mpi_message_record_receiver
    CHECK (receiver_type IN ('PATIENT', 'STAFF'));
```

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **2 年**（消息记录量大，2 年后归档到冷存储）。

### 4.8 表：`mpi_message_receipt`（回执表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| record_id | BIGINT | N | - | 记录 ID |
| record_no | VARCHAR(32) | N | - | 消息号（冗余） |
| provider_message_id | VARCHAR(128) | Y | NULL | 网关消息 ID |
| receipt_type | VARCHAR(16) | N | - | DELIVERED/READ/FAILED/CLICKED/REPLIED/UNSUBSCRIBED |
| receipt_at | TIMESTAMP | N | - | 回执时间 |
| error_code | VARCHAR(64) | Y | NULL | 错误代码 |
| error_msg | VARCHAR(500) | Y | NULL | 错误信息 |
| raw_data_json | JSONB | Y | NULL | 网关原始回执 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `uk_mpi_message_receipt(record_id, receipt_type)` 唯一（幂等）；`idx_mpi_message_receipt_record(record_id)`；`idx_mpi_message_receipt_type(receipt_type, created_at)`；`idx_mpi_message_receipt_provider(provider_message_id)`。

**约束说明**

```sql
ALTER TABLE mpi_message_receipt
    ADD CONSTRAINT ck_mpi_message_receipt_type
    CHECK (receipt_type IN ('DELIVERED', 'READ', 'FAILED', 'CLICKED',
                             'REPLIED', 'UNSUBSCRIBED'));
```

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **2 年**。

### 4.9 表：`mpi_message_retry`（重试队列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| record_id | BIGINT | N | - | 记录 ID |
| record_no | VARCHAR(32) | N | - | 消息号（冗余） |
| retry_seq | INT | N | 1 | 重试序号 |
| next_retry_at | TIMESTAMP | N | - | 下次重试时间 |
| last_error_code | VARCHAR(64) | Y | NULL | 上次错误代码 |
| last_error_msg | VARCHAR(500) | Y | NULL | 上次错误信息 |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/RUNNING/SUCCESS/FAILED/EXHAUSTED |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_message_retry(record_id, retry_seq)` 唯一；`idx_mpi_message_retry_next(status, next_retry_at)`。

**约束说明**

```sql
ALTER TABLE mpi_message_retry
    ADD CONSTRAINT ck_mpi_message_retry_status
    CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'EXHAUSTED'));
```

### 4.10 表：`mpi_message_blacklist`（黑名单表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| receiver_type | VARCHAR(16) | N | - | PATIENT/STAFF |
| receiver_id | BIGINT | N | - | 接收人 ID |
| receiver_name | VARCHAR(64) | Y | NULL | 接收人姓名 |
| channel_code | VARCHAR(32) | Y | NULL | 渠道（NULL=全渠道） |
| biz_type | VARCHAR(32) | Y | NULL | 业务类型（NULL=全类型） |
| reason | VARCHAR(32) | N | - | UNSUBSCRIBE/COMPLAINT/ABNORMAL/MANUAL |
| reason_desc | VARCHAR(500) | Y | NULL | 原因说明 |
| source | VARCHAR(32) | Y | NULL | 来源：PATIENT_UNSUBSCRIBE/SMS_REPLY/COMPLAINT/MANUAL |
| status | VARCHAR(16) | N | 'ACTIVE' | ACTIVE/RELEASED/EXPIRED |
| effective_at | TIMESTAMP | N | - | 生效时间 |
| expire_at | TIMESTAMP | Y | NULL | 失效时间（NULL=长期） |
| released_at | TIMESTAMP | Y | NULL | 解除时间 |
| released_by | BIGINT | Y | NULL | 解除人 |
| release_reason | VARCHAR(500) | Y | NULL | 解除原因 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_message_blacklist(receiver_type, receiver_id, channel_code, biz_type, is_deleted)` 唯一（NULL 需应用层处理，或使用 COALESCE 表达式索引）；`idx_mpi_message_blacklist_receiver(receiver_type, receiver_id, status)`；`idx_mpi_message_blacklist_status(status, expire_at)`。

**约束说明**

```sql
ALTER TABLE mpi_message_blacklist
    ADD CONSTRAINT ck_mpi_message_blacklist_type
    CHECK (receiver_type IN ('PATIENT', 'STAFF'));

ALTER TABLE mpi_message_blacklist
    ADD CONSTRAINT ck_mpi_message_blacklist_reason
    CHECK (reason IN ('UNSUBSCRIBE', 'COMPLAINT', 'ABNORMAL', 'MANUAL'));

ALTER TABLE mpi_message_blacklist
    ADD CONSTRAINT ck_mpi_message_blacklist_status
    CHECK (status IN ('ACTIVE', 'RELEASED', 'EXPIRED'));
```

**唯一约束（考虑 NULL）：**

```sql
CREATE UNIQUE INDEX uk_mpi_message_blacklist_active
    ON mpi_message_blacklist (
        receiver_type, receiver_id,
        COALESCE(channel_code, 'ALL'),
        COALESCE(biz_type, 'ALL')
    )
    WHERE status = 'ACTIVE' AND is_deleted = FALSE;
```

### 4.11 表：`mpi_message_log`（变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| change_scope | VARCHAR(32) | N | - | TEMPLATE/CHANNEL/CONFIG/BLACKLIST |
| target_id | BIGINT | Y | NULL | 目标 ID |
| target_key | VARCHAR(128) | Y | NULL | 目标编码 |
| target_name | VARCHAR(255) | Y | NULL | 目标名称 |
| action | VARCHAR(32) | N | - | CREATE/UPDATE/ENABLE/DISABLE/SUBMIT/AUDIT/RELEASE |
| before_json | JSONB | Y | NULL | 变更前快照 |
| after_json | JSONB | Y | NULL | 变更后快照 |
| detail | VARCHAR(1000) | Y | NULL | 操作详情 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_mpi_message_log_scope(change_scope, created_at)`；`idx_mpi_message_log_target(target_id)`；`idx_mpi_message_log_action(action, created_at)`；`idx_mpi_message_log_time(created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**。

### 4.12 表：`mpi_message_code_seq`（编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| seq_type | VARCHAR(16) | N | - | TASK/RECORD |
| prefix | VARCHAR(8) | N | - | 前缀 |
| period_key | VARCHAR(8) | N | - | 周期键 `yyyyMMdd` |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 4 | 流水位数 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_message_code_seq(seq_type, prefix, period_key)` 唯一。

**说明：** Redis `INCR` 为主，DB 表用于每日对账；Redis 丢数据时从 `MAX(current_seq)` 恢复。

### 4.13 表：`mpi_message_unsubscribe`（退订记录表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| receiver_type | VARCHAR(16) | N | - | PATIENT/STAFF |
| receiver_id | BIGINT | N | - | 接收人 ID |
| receiver_name | VARCHAR(64) | Y | NULL | 接收人姓名 |
| channel_code | VARCHAR(32) | N | - | 渠道 |
| biz_type | VARCHAR(32) | N | - | 业务类型 |
| source | VARCHAR(32) | N | - | PORTAL/SMS_REPLY/WECHAT/MANUAL |
| raw_content | VARCHAR(500) | Y | NULL | 原始退订内容 |
| blacklist_id | BIGINT | Y | NULL | 生成的黑名单 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 退订时间 |

**索引：** `idx_mpi_message_unsubscribe_receiver(receiver_type, receiver_id, created_at)`；`idx_mpi_message_unsubscribe_blacklist(blacklist_id)`。

### 4.14 SQLAlchemy 2.0 模型定义

```python
# app/models/mpi/message.py
"""消息中心 ORM 模型"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime, Text,
    JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MpiMessageConfig(Base):
    """消息配置（单行）"""
    __tablename__ = "mpi_message_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_prefix: Mapped[str] = mapped_column(String(8), default="MT", nullable=False)
    record_prefix: Mapped[str] = mapped_column(String(8), default="MR", nullable=False)
    seq_len: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    retry_max: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    retry_intervals: Mapped[str] = mapped_column(String(64), default="5,15,60", nullable=False)
    freq_hour: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    freq_day: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    freq_task: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    mask_mobile: Mapped[str] = mapped_column(String(16), default="3-4", nullable=False)
    mask_email: Mapped[str] = mapped_column(String(16), default="1-3", nullable=False)
    receipt_retry: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    allow_marketing_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_blacklist_on_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    subscribe_patient_merge: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sensitive_view_ttl: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "消息配置（单行）"},
    )

    def retry_interval_list(self) -> List[int]:
        return [int(x.strip()) for x in self.retry_intervals.split(",") if x.strip().isdigit()]


class MpiMessageChannel(Base, TimestampMixin, SoftDeleteMixin):
    """渠道配置"""
    __tablename__ = "mpi_message_channel"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(64))
    gateway_url: Mapped[Optional[str]] = mapped_column(String(500))
    auth_type: Mapped[Optional[str]] = mapped_column(String(32))
    sign_name: Mapped[Optional[str]] = mapped_column(String(64))
    daily_limit: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    hourly_per_receiver: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    daily_per_receiver: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    mask_rule: Mapped[Optional[str]] = mapped_column(String(32))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("channel_code", "is_deleted", name="uk_mpi_message_channel_code"),
        Index("idx_mpi_message_channel_enabled", "is_enabled", "sort_no"),
        {"comment": "渠道配置"},
    )


class MpiMessageTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """消息模板"""
    __tablename__ = "mpi_message_template"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    template_name: Mapped[str] = mapped_column(String(128), nullable=False)
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[Optional[list]] = mapped_column(JSONB)
    provider_template_id: Mapped[Optional[str]] = mapped_column(String(128))
    sign_name: Mapped[Optional[str]] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    need_audit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    audit_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audit_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    audit_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    audit_remark: Mapped[Optional[str]] = mapped_column(String(500))
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    versions: Mapped[List["MpiMessageTemplateVersion"]] = relationship(
        back_populates="template", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("template_code", "is_deleted", name="uk_mpi_message_template_code"),
        Index("idx_mpi_message_template_channel", "channel_code", "status"),
        Index("idx_mpi_message_template_biz", "biz_type", "status"),
        Index("idx_mpi_message_template_audit", "audit_status", "created_at"),
        {"comment": "消息模板"},
    )

    @property
    def variable_names(self) -> List[str]:
        if not self.variables_json:
            return []
        return [v.get("name") for v in self.variables_json if v.get("name")]


class MpiMessageTemplateVersion(Base):
    """模板版本"""
    __tablename__ = "mpi_message_template_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables_json: Mapped[Optional[list]] = mapped_column(JSONB)
    change_reason: Mapped[Optional[str]] = mapped_column(String(500))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    template: Mapped["MpiMessageTemplate"] = relationship(back_populates="versions")

    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uk_mpi_message_template_version"),
        Index("idx_mpi_message_template_version_time", "created_at"),
        {"comment": "模板版本"},
    )


class MpiMessageTask(Base, TimestampMixin, SoftDeleteMixin):
    """发送任务"""
    __tablename__ = "mpi_message_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(32), nullable=False)
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_no: Mapped[Optional[str]] = mapped_column(String(64))
    source_module: Mapped[Optional[str]] = mapped_column(String(16))
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    sender_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    sender_name: Mapped[Optional[str]] = mapped_column(String(64))
    priority: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("task_no", "is_deleted", name="uk_mpi_message_task_no"),
        Index("idx_mpi_message_task_template", "template_code", "status"),
        Index("idx_mpi_message_task_channel", "channel_code", "status"),
        Index("idx_mpi_message_task_biz", "biz_type", "status"),
        Index("idx_mpi_message_task_status", "status", "created_at"),
        Index("idx_mpi_message_task_source", "source_module", "created_at"),
        {"comment": "发送任务"},
    )

    @property
    def success_rate(self) -> float:
        if not self.total_count:
            return 0.0
        return round((self.success_count or 0) / self.total_count * 100, 2)


class MpiMessageRecord(Base, SoftDeleteMixin):
    """发送记录"""
    __tablename__ = "mpi_message_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_no: Mapped[str] = mapped_column(String(32), nullable=False)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    task_no: Mapped[Optional[str]] = mapped_column(String(32))
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(64), nullable=False)
    template_version: Mapped[int] = mapped_column(Integer, nullable=False)
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_no: Mapped[Optional[str]] = mapped_column(String(64))
    receiver_type: Mapped[str] = mapped_column(String(16), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    receiver_name: Mapped[Optional[str]] = mapped_column(String(64))
    receiver_addr_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    receiver_addr_mask: Mapped[Optional[str]] = mapped_column(String(64))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    content_vars_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    send_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fail_code: Mapped[Optional[str]] = mapped_column(String(64))
    fail_reason: Mapped[Optional[str]] = mapped_column(String(500))
    reject_reason: Mapped[Optional[str]] = mapped_column(String(64))
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("record_no", "is_deleted", name="uk_mpi_message_record_no"),
        Index("idx_mpi_message_record_task", "task_id", "status"),
        Index("idx_mpi_message_record_receiver", "receiver_type", "receiver_id", "status"),
        Index("idx_mpi_message_record_channel", "channel_code", "status"),
        Index("idx_mpi_message_record_status", "status", "created_at"),
        Index("idx_mpi_message_record_freq",
              "receiver_type", "receiver_id", "channel_code", "biz_type", "created_at"),
        Index("idx_mpi_message_record_unread", "receiver_id", "status"),
        {"comment": "发送记录（月度分区）"},
    )

    STATUS_LABELS = {
        "PENDING": "待发送", "SENDING": "发送中", "SENT": "已发送",
        "DELIVERED": "已送达", "READ": "已阅读", "RETRYING": "重试中",
        "FAILED": "失败", "EXPIRED": "已过期", "REJECTED": "已拒绝",
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def is_success(self) -> bool:
        return self.status in ("SENT", "DELIVERED", "READ")


class MpiMessageReceipt(Base):
    """回执"""
    __tablename__ = "mpi_message_receipt"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    record_no: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    receipt_type: Mapped[str] = mapped_column(String(16), nullable=False)
    receipt_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(64))
    error_msg: Mapped[Optional[str]] = mapped_column(String(500))
    raw_data_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("record_id", "receipt_type", name="uk_mpi_message_receipt"),
        Index("idx_mpi_message_receipt_record", "record_id"),
        Index("idx_mpi_message_receipt_type", "receipt_type", "created_at"),
        Index("idx_mpi_message_receipt_provider", "provider_message_id"),
        {"comment": "回执（月度分区）"},
    )


class MpiMessageRetry(Base):
    """重试队列"""
    __tablename__ = "mpi_message_retry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    record_no: Mapped[str] = mapped_column(String(32), nullable=False)
    retry_seq: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    next_retry_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_error_code: Mapped[Optional[str]] = mapped_column(String(64))
    last_error_msg: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("record_id", "retry_seq", name="uk_mpi_message_retry"),
        Index("idx_mpi_message_retry_next", "status", "next_retry_at"),
        {"comment": "重试队列"},
    )


class MpiMessageBlacklist(Base, TimestampMixin, SoftDeleteMixin):
    """黑名单"""
    __tablename__ = "mpi_message_blacklist"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    receiver_type: Mapped[str] = mapped_column(String(16), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    receiver_name: Mapped[Optional[str]] = mapped_column(String(64))
    channel_code: Mapped[Optional[str]] = mapped_column(String(32))
    biz_type: Mapped[Optional[str]] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_desc: Mapped[Optional[str]] = mapped_column(String(500))
    source: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    effective_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    release_reason: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        Index("idx_mpi_message_blacklist_receiver",
              "receiver_type", "receiver_id", "status"),
        Index("idx_mpi_message_blacklist_status", "status", "expire_at"),
        {"comment": "黑名单"},
    )

    REASON_LABELS = {
        "UNSUBSCRIBE": "退订", "COMPLAINT": "投诉",
        "ABNORMAL": "异常", "MANUAL": "手动",
    }

    @property
    def reason_label(self) -> str:
        return self.REASON_LABELS.get(self.reason, self.reason)

    def is_active(self, now: Optional[datetime] = None) -> bool:
        if self.status != "ACTIVE":
            return False
        now = now or datetime.now()
        if self.effective_at and self.effective_at > now:
            return False
        if self.expire_at and self.expire_at <= now:
            return False
        return True


class MpiMessageUnsubscribe(Base):
    """退订记录"""
    __tablename__ = "mpi_message_unsubscribe"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    receiver_type: Mapped[str] = mapped_column(String(16), nullable=False)
    receiver_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    receiver_name: Mapped[Optional[str]] = mapped_column(String(64))
    channel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    biz_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    raw_content: Mapped[Optional[str]] = mapped_column(String(500))
    blacklist_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_message_unsubscribe_receiver",
              "receiver_type", "receiver_id", "created_at"),
        Index("idx_mpi_message_unsubscribe_blacklist", "blacklist_id"),
        {"comment": "退订记录"},
    )


class MpiMessageLog(Base):
    """变更日志"""
    __tablename__ = "mpi_message_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    change_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    target_key: Mapped[Optional[str]] = mapped_column(String(128))
    target_name: Mapped[Optional[str]] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    detail: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_message_log_scope", "change_scope", "created_at"),
        Index("idx_mpi_message_log_target", "target_id"),
        Index("idx_mpi_message_log_action", "action", "created_at"),
        Index("idx_mpi_message_log_time", "created_at"),
        {"comment": "变更日志（月度分区）"},
    )


class MpiMessageCodeSeq(Base):
    """编码序列（DB 对账）"""
    __tablename__ = "mpi_message_code_seq"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    seq_type: Mapped[str] = mapped_column(String(16), nullable=False)
    prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    period_key: Mapped[str] = mapped_column(String(8), nullable=False)
    current_seq: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    seq_width: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("seq_type", "prefix", "period_key",
                         name="uk_mpi_message_code_seq"),
        {"comment": "消息编码序列（Redis 为主，DB 对账）"},
    )
```

### 4.15 Pydantic Schema 定义

```python
# app/schemas/mpi/message.py
"""消息中心 Pydantic Schema"""
from datetime import datetime
from typing import Optional, List, Literal, Any
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


CHANNEL_CODE = Literal["SMS", "WECHAT", "EMAIL", "INBOX", "APP_PUSH", "VOICE"]
BIZ_TYPE = Literal["VERIFY_CODE", "NOTICE", "FOLLOWUP", "MEMBER",
                    "MARKETING", "SATISFACTION", "SYSTEM"]
TEMPLATE_STATUS = Literal["DRAFT", "ENABLED", "DISABLED"]
AUDIT_STATUS = Literal["DRAFT", "PENDING", "APPROVED", "REJECTED"]
TASK_STATUS = Literal["PENDING", "SENDING", "COMPLETED", "PARTIAL", "FAILED", "CANCELLED"]
RECORD_STATUS = Literal["PENDING", "SENDING", "SENT", "DELIVERED", "READ",
                         "RETRYING", "FAILED", "EXPIRED", "REJECTED"]
RECEIPT_TYPE = Literal["DELIVERED", "READ", "FAILED", "CLICKED", "REPLIED", "UNSUBSCRIBED"]
RECEIVER_TYPE = Literal["PATIENT", "STAFF"]
BLACKLIST_REASON = Literal["UNSUBSCRIBE", "COMPLAINT", "ABNORMAL", "MANUAL"]
VARIABLE_TYPE = Literal["TEXT", "NUMBER", "DATE", "DATETIME", "AMOUNT", "BOOL"]


# ==================== 模板 ====================
class TemplateVariable(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")
    display_name: str = Field(..., max_length=64)
    type: VARIABLE_TYPE = "TEXT"
    sensitive: bool = False
    default_value: Optional[str] = Field(None, max_length=255)


class MessageTemplateBase(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=128)
    channel_code: CHANNEL_CODE
    biz_type: BIZ_TYPE
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1, max_length=20000)
    variables: List[TemplateVariable] = []
    provider_template_id: Optional[str] = Field(None, max_length=128)
    sign_name: Optional[str] = Field(None, max_length=64)
    priority: Literal["HIGH", "NORMAL", "LOW"] = "NORMAL"
    need_audit: bool = True
    description: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_template(self):
        # 变量名不能重复
        names = [v.name for v in self.variables]
        if len(names) != len(set(names)):
            raise ValueError("变量名重复")
        # 内容中的变量必须在变量定义中
        used = set(re.findall(r"\{\{(\w+)\}\}", self.content))
        defined = set(names)
        if used - defined:
            raise ValueError(f"内容使用了未定义的变量：{used - defined}")
        return self


class MessageTemplateCreate(MessageTemplateBase):
    template_code: str = Field(..., pattern=r"^MSG-[A-Z0-9\-]{2,60}$")


class MessageTemplateUpdate(MessageTemplateBase):
    change_reason: Optional[str] = Field(None, max_length=500)


class MessageTemplateAuditRequest(BaseModel):
    action: Literal["APPROVE", "REJECT"]
    remark: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_audit(self):
        if self.action == "REJECT" and not self.remark:
            raise ValueError("驳回必须填写原因")
        return self


class MessageTemplateItem(MessageTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_code: str
    audit_status: str = "PENDING"
    current_version: int = 1
    status: str = "DRAFT"
    updated_at: Optional[datetime] = None


class TemplateVersionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: int
    title: Optional[str] = None
    content: str
    change_reason: Optional[str] = None
    is_current: bool = False
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


# ==================== 渠道 ====================
class ChannelUpdate(BaseModel):
    channel_name: Optional[str] = Field(None, max_length=64)
    provider: Optional[str] = Field(None, max_length=64)
    gateway_url: Optional[str] = Field(None, max_length=500)
    auth_type: Optional[Literal["API_KEY", "OAUTH2", "PASSWORD"]] = None
    sign_name: Optional[str] = Field(None, max_length=64)
    daily_limit: int = Field(0, ge=0)
    hourly_per_receiver: int = Field(5, ge=0, le=1000)
    daily_per_receiver: int = Field(20, ge=0, le=10000)
    is_enabled: bool = True
    description: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_channel(self):
        if self.hourly_per_receiver > self.daily_per_receiver and self.daily_per_receiver > 0:
            raise ValueError("每小时上限不能大于每天上限")
        return self


class ChannelItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    channel_code: str
    channel_name: str
    provider: Optional[str] = None
    daily_limit: int = 0
    hourly_per_receiver: int = 5
    daily_per_receiver: int = 20
    is_enabled: bool = True


class ChannelTestRequest(BaseModel):
    receiver_addr: str = Field(..., max_length=255)
    content: str = Field(..., min_length=1, max_length=500)


# ==================== 发送 ====================
class MessageReceiver(BaseModel):
    receiver_type: RECEIVER_TYPE = "PATIENT"
    receiver_id: int
    receiver_name: Optional[str] = Field(None, max_length=64)
    receiver_addr: str = Field(..., min_length=1, max_length=255)
    variables: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_receiver(self):
        if not self.receiver_addr.strip():
            raise ValueError("接收地址不能为空")
        return self


class MessageSendRequest(BaseModel):
    template_code: str = Field(..., max_length=64)
    channel: Optional[CHANNEL_CODE] = None
    receivers: List[MessageReceiver] = Field(..., min_length=1, max_length=5000)
    biz_type: BIZ_TYPE = "NOTICE"
    biz_no: Optional[str] = Field(None, max_length=64)
    source_module: Optional[str] = Field(None, max_length=16)
    scheduled_at: Optional[datetime] = None
    priority: Literal["HIGH", "NORMAL", "LOW"] = "NORMAL"

    @model_validator(mode="after")
    def validate_send(self):
        # 防止单任务重复接收人
        keys = [(r.receiver_type, r.receiver_id) for r in self.receivers]
        if len(keys) != len(set(keys)):
            raise ValueError("接收人重复")
        return self


class MessageSendResult(BaseModel):
    task_id: int
    task_no: str
    total_count: int
    accepted_count: int
    rejected_count: int
    rejected: List[dict] = []
    status: str


class MessageTaskItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_no: str
    template_code: str
    channel_code: str
    biz_type: str
    biz_no: Optional[str] = None
    source_module: Optional[str] = None
    total_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    status: str
    created_at: Optional[datetime] = None


class MessageRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_no: str
    task_no: Optional[str] = None
    template_code: str
    template_version: int
    channel_code: str
    biz_type: str
    receiver_type: str
    receiver_id: int
    receiver_name: Optional[str] = None
    receiver_addr_mask: Optional[str] = None
    status: str
    fail_code: Optional[str] = None
    fail_reason: Optional[str] = None
    reject_reason: Optional[str] = None
    retry_count: int = 0
    send_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class MessageRecordDetail(MessageRecordItem):
    title: Optional[str] = None
    content_snapshot: str
    content_vars_json: Optional[dict] = None
    provider_message_id: Optional[str] = None
    trace_id: Optional[str] = None


# ==================== 回执 ====================
class MessageReceiptRequest(BaseModel):
    record_no: str = Field(..., max_length=32)
    provider_message_id: Optional[str] = Field(None, max_length=128)
    receipt_type: RECEIPT_TYPE
    receipt_at: Optional[datetime] = None
    error_code: Optional[str] = Field(None, max_length=64)
    error_msg: Optional[str] = Field(None, max_length=500)
    raw_data: Optional[dict] = None
    signature: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_receipt(self):
        if self.receipt_type == "FAILED" and not self.error_code and not self.error_msg:
            raise ValueError("失败回执必须提供 error_code 或 error_msg")
        return self


class MessageReceiptResult(BaseModel):
    record_no: str
    receipt_type: str
    record_status: str
    duplicate: bool = False


class ReceiptStatistics(BaseModel):
    total_sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    unsubscribed: int = 0
    by_channel: dict = {}
    fail_reasons: List[dict] = []


# ==================== 黑名单 ====================
class BlacklistCreate(BaseModel):
    receiver_type: RECEIVER_TYPE = "PATIENT"
    receiver_id: int
    channel_code: Optional[CHANNEL_CODE] = None
    biz_type: Optional[BIZ_TYPE] = None
    reason: BLACKLIST_REASON = "MANUAL"
    reason_desc: Optional[str] = Field(None, max_length=500)
    expire_at: Optional[datetime] = None


class BlacklistRelease(BaseModel):
    release_reason: str = Field(..., min_length=5, max_length=500)


class BlacklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receiver_type: str
    receiver_id: int
    receiver_name: Optional[str] = None
    channel_code: Optional[str] = None
    biz_type: Optional[str] = None
    reason: str
    reason_desc: Optional[str] = None
    status: str
    effective_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class UnsubscribeRequest(BaseModel):
    receiver_type: RECEIVER_TYPE = "PATIENT"
    receiver_id: int
    channel_code: CHANNEL_CODE
    biz_type: BIZ_TYPE
    source: Literal["PORTAL", "SMS_REPLY", "WECHAT", "MANUAL"] = "PORTAL"
    raw_content: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_unsubscribe(self):
        if self.biz_type in ("VERIFY_CODE", "NOTICE", "SYSTEM"):
            raise ValueError("验证码/通知/系统类消息不可退订")
        return self


class UnsubscribeResult(BaseModel):
    receiver_type: str
    receiver_id: int
    channel_code: str
    biz_type: str
    blacklist_id: Optional[int] = None
    status: str


# ==================== 配置 ====================
class MessageConfigUpdate(BaseModel):
    task_prefix: str = Field("MT", max_length=8)
    record_prefix: str = Field("MR", max_length=8)
    seq_len: int = Field(4, ge=2, le=10)
    retry_max: int = Field(3, ge=0, le=10)
    retry_intervals: str = Field("5,15,60", max_length=64)
    freq_hour: int = Field(5, ge=1, le=1000)
    freq_day: int = Field(20, ge=1, le=10000)
    freq_task: int = Field(3, ge=1, le=100)
    mask_mobile: str = Field("3-4", max_length=16)
    mask_email: str = Field("1-3", max_length=16)
    receipt_retry: int = Field(3, ge=0, le=10)
    allow_marketing_unsubscribe: bool = True
    auto_blacklist_on_unsubscribe: bool = True
    subscribe_patient_merge: bool = True
    sensitive_view_ttl: int = Field(300, ge=60, le=1800)
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_config(self):
        if self.freq_hour > self.freq_day:
            raise ValueError("每小时上限不能大于每天上限")
        if not all(x.strip().isdigit() for x in self.retry_intervals.split(",") if x.strip()):
            raise ValueError("重试间隔必须为逗号分隔的数字")
        return self


class MessageConfigDetail(MessageConfigUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int = 1
    updated_at: Optional[datetime] = None


# ==================== 内部契约 ====================
class UnreadCountResult(BaseModel):
    receiver_type: str = "PATIENT"
    receiver_id: int
    unread_count: int = 0
    by_channel: dict = {}


class MessageListQuery(BaseModel):
    receiver_type: RECEIVER_TYPE = "PATIENT"
    receiver_id: int
    channel_code: Optional[CHANNEL_CODE] = None
    biz_type: Optional[BIZ_TYPE] = None
    unread_only: bool = False
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class MergeRedirectRequest(BaseModel):
    merge_id: str = Field(..., max_length=32)
    primary_patient_id: int
    secondary_patient_id: int


class MergeRedirectResult(BaseModel):
    merge_id: str
    secondary_patient_id: int
    record_count: int = 0
    redirected: int = 0
    conflict: int = 0
    conflict_record_ids: List[int] = []


class BlacklistCheckResult(BaseModel):
    receiver_type: str
    receiver_id: int
    channel_code: Optional[str] = None
    biz_type: Optional[str] = None
    blocked: bool = False
    reason: Optional[str] = None


# 前向引用
MessageTemplateItem.model_rebuild()
MessageRecordDetail.model_rebuild()
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：12 张表 | 系统设计组 |