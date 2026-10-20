# 二级眼科医院 HIS 系统 — M03 患者服务与 EMPI
# 子模块数据结构：患者门户与自助服务

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 患者门户与自助服务（Patient Portal & Self-Service）
**主数据域：** 患者域（`MPI`），表前缀 `mpi_portal_`
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 06 患者门户与自助服务 详细设计》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「患者门户与自助服务」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[患者门户与自助服务详细设计](M03_患者服务与EMPI_06_患者门户与自助服务_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [患者门户与自助服务详细设计](M03_患者服务与EMPI_06_患者门户与自助服务_详细设计.md) —— 业务模型、页面设计、接口设计、业务规则、验收标准
- [患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md) —— `mpi_patient`、授权记录
- [会员数据结构](M03_患者服务与EMPI_03_会员_数据结构.md) —— 会员等级与权益
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md) —— 跨模块表清单与全局设计约定

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 11 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_portal_account`（门户账号表）](#42-表mpi_portal_account门户账号表)
- [4.3 表：`mpi_portal_binding`（患者绑定表）](#43-表mpi_portal_binding患者绑定表)
- [4.4 表：`mpi_portal_binding_log`（绑定变更日志表）](#44-表mpi_portal_binding_log绑定变更日志表)
- [4.5 表：`mpi_portal_session`（门户会话表）](#45-表mpi_portal_session门户会话表)
- [4.6 表：`mpi_portal_register_task`（自助建档任务表）](#46-表mpi_portal_register_task自助建档任务表)
- [4.7 表：`mpi_portal_agreement`（协议版本表）](#47-表mpi_portal_agreement协议版本表)
- [4.8 表：`mpi_portal_config`（门户配置表）](#48-表mpi_portal_config门户配置表)
- [4.9 表：`mpi_portal_announcement`（公告表）](#49-表mpi_portal_announcement公告表)
- [4.10 表：`mpi_portal_kiosk`（自助机设备表）](#410-表mpi_portal_kiosk自助机设备表)
- [4.11 表：`mpi_portal_statistics`（门户统计表）](#411-表mpi_portal_statistics门户统计表)
- [4.12 表：`mpi_portal_access_log`（门户访问日志表）](#412-表mpi_portal_access_log门户访问日志表)
- [4.13 SQLAlchemy 2.0 模型定义](#413-sqlalchemy-20-模型定义)
- [4.14 Pydantic Schema 定义](#414-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_portal_account` | 门户账号表 |
| 4.3 | `mpi_portal_binding` | 患者绑定表 |
| 4.4 | `mpi_portal_binding_log` | 绑定变更日志表 |
| 4.5 | `mpi_portal_session` | 门户会话表 |
| 4.6 | `mpi_portal_register_task` | 自助建档任务表 |
| 4.7 | `mpi_portal_agreement` | 协议版本表 |
| 4.8 | `mpi_portal_config` | 门户配置表 |
| 4.9 | `mpi_portal_announcement` | 公告表 |
| 4.10 | `mpi_portal_kiosk` | 自助机设备表 |
| 4.11 | `mpi_portal_statistics` | 门户统计表 |
| 4.12 | `mpi_portal_access_log` | 门户访问日志表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```
┌────────────────────────────────────────────────────────────────────────┐
│ mpi_patient（M03-01，患者主索引，本模块只读引用）                       │
└────────────────────────────┬───────────────────────────────────────────┘
                             │ patient_id
                             ▼
┌────────────────────────┐        ┌────────────────────────────────────┐
│ mpi_portal_account     │  1 : N │ mpi_portal_binding                 │
│ （门户账号）            │───────►│ （患者绑定：本人/家属）             │
│  · account_id          │        │  · account_id                      │
│  · openid / unionid    │        │  · patient_id                      │
│  · phone(加密/哈希/掩码)│        │  · relation / verify_level         │
│  · channel / status    │        │  · is_default / status             │
└───────────┬────────────┘        └──────────────┬─────────────────────┘
            │                                     │
            │ 1 : N                               │ 1 : N
            ▼                                     ▼
┌────────────────────────┐        ┌────────────────────────────────────┐
│ mpi_portal_session     │        │ mpi_portal_binding_log             │
│ （门户会话）            │        │ （绑定变更日志，月分区）            │
└────────────────────────┘        └────────────────────────────────────┘

独立配置与运营表：
┌────────────────────────┐  ┌────────────────────────┐
│ mpi_portal_config      │  │ mpi_portal_agreement   │
│ （门户配置，单行）      │  │ （协议版本）            │
└────────────────────────┘  └────────────────────────┘
┌────────────────────────┐  ┌────────────────────────┐
│ mpi_portal_announcement│  │ mpi_portal_kiosk       │
│ （公告）                │  │ （自助机设备）          │
└────────────────────────┘  └────────────────────────┘

任务与统计：
┌────────────────────────┐  ┌────────────────────────┐
│ mpi_portal_register_   │  │ mpi_portal_statistics  │
│ task（自助建档任务）    │  │ （门户统计）            │
└────────────────────────┘  └────────────────────────┘
┌────────────────────────┐
│ mpi_portal_access_log  │
│ （访问日志，月分区）    │
└────────────────────────┘
```

**设计说明：**

- `mpi_portal_account` 是**患者账号主体**，与 M02 的 `sys_account`（职工账号）**完全隔离**
- `mpi_portal_binding` 是账号与患者的 N:M 桥接，承载关系与验证等级
- **`mpi_portal_account` 不存密码**（患者不用密码登录）
- 证件、手机号一律**加密 + 哈希 + 掩码**三列
- `mpi_portal_binding_log` / `mpi_portal_access_log` 按 `created_at` 月度分区
- 跨模块通过 `patient_id` / `empi_no` 逻辑引用，不建跨模块物理外键

### 4.2 表：`mpi_portal_account`（门户账号表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| account_id | VARCHAR(40) | N | - | 账号 ID `pa_` + 12位 hex |
| openid | VARCHAR(64) | Y | NULL | 微信 openid |
| unionid | VARCHAR(64) | Y | NULL | 微信 unionid（跨公众号/小程序） |
| phone | VARCHAR(128) | Y | NULL | 手机号加密值 |
| phone_hash | CHAR(64) | Y | NULL | 手机号 SHA-256 |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码 `138****5678` |
| nickname | VARCHAR(64) | Y | NULL | 微信昵称 |
| avatar_url | VARCHAR(500) | Y | NULL | 微信头像 |
| channel | VARCHAR(16) | N | - | 首次来源渠道：WECHAT_MP/WECHAT_MINI/ALIPAY_MINI/KIOSK/WEB |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/FROZEN/CANCELLED |
| verify_level | VARCHAR(16) | N | 'BASIC' | 账号级最高验证等级：NONE/BASIC/STRONG |
| login_count | INT | N | 0 | 累计登录次数 |
| last_login_at | TIMESTAMP | Y | NULL | 最后登录时间 |
| last_login_ip | VARCHAR(64) | Y | NULL | 最后登录 IP |
| last_login_channel | VARCHAR(16) | Y | NULL | 最后登录渠道 |
| frozen_reason | VARCHAR(255) | Y | NULL | 冻结原因 |
| cancelled_at | TIMESTAMP | Y | NULL | 注销时间 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_portal_account | PRIMARY | id | 主键 |
| uk_mpi_portal_account_id | UNIQUE | account_id | 账号 ID 唯一 |
| uk_mpi_portal_openid | UNIQUE | openid | 微信公众号 openid 唯一（部分） |
| idx_mpi_portal_unionid | NORMAL | unionid | 跨渠道识别 |
| uk_mpi_portal_phone | UNIQUE | phone_hash | 手机号唯一（部分） |
| idx_mpi_portal_channel | NORMAL | channel, created_at | 渠道统计 |
| idx_mpi_portal_status | NORMAL | status, last_login_at | 状态筛选 |

**约束说明**

```sql
-- 账号 ID 格式：pa_ + 12 位 hex
ALTER TABLE mpi_portal_account
    ADD CONSTRAINT ck_portal_account_id
    CHECK (account_id ~ '^pa_[0-9a-f]{12}$');

-- 渠道枚举
ALTER TABLE mpi_portal_account
    ADD CONSTRAINT ck_portal_channel
    CHECK (channel IN ('WECHAT_MP', 'WECHAT_MINI', 'ALIPAY_MINI', 'KIOSK', 'WEB'));

-- 状态枚举
ALTER TABLE mpi_portal_account
    ADD CONSTRAINT ck_portal_status
    CHECK (status IN ('ACTIVE', 'FROZEN', 'CANCELLED'));

-- 验证等级
ALTER TABLE mpi_portal_account
    ADD CONSTRAINT ck_portal_verify_level
    CHECK (verify_level IN ('NONE', 'BASIC', 'STRONG'));

-- 必须有 openid 或手机号之一
ALTER TABLE mpi_portal_account
    ADD CONSTRAINT ck_portal_account_identity
    CHECK (openid IS NOT NULL OR phone_hash IS NOT NULL);

-- 部分唯一索引：只对未注销账号生效
CREATE UNIQUE INDEX uk_mpi_portal_openid
    ON mpi_portal_account (openid)
    WHERE openid IS NOT NULL AND status <> 'CANCELLED';

CREATE UNIQUE INDEX uk_mpi_portal_phone
    ON mpi_portal_account (phone_hash)
    WHERE phone_hash IS NOT NULL AND status <> 'CANCELLED';
```

**账号状态流转**

```
        ┌──────────┐
   ┌───►│  ACTIVE  │◄──┐
   │    └────┬─────┘   │ 解冻
   │         │ 冻结      │
   │         ▼          │
   │    ┌──────────┐    │
   │    │  FROZEN  │────┘
   │    └────┬─────┘
   │         │ 注销
   │         ▼
   │    ┌────────────┐
   └────│ CANCELLED  │（终态，不可恢复）
        └────────────┘
```

### 4.3 表：`mpi_portal_binding`（患者绑定表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（binding_id） |
| account_id | VARCHAR(40) | N | - | 门户账号 ID |
| patient_id | BIGINT | N | - | 患者 ID（引用 `mpi_patient`） |
| empi_no | VARCHAR(32) | Y | NULL | EMPI 号（冗余） |
| patient_name | VARCHAR(64) | Y | NULL | 患者姓名（冗余） |
| relation | VARCHAR(16) | N | 'SELF' | 关系：SELF/SPOUSE/CHILD/PARENT/OTHER |
| guardian_id | BIGINT | Y | NULL | 监护人患者 ID（未成年人时） |
| verify_level | VARCHAR(16) | N | 'BASIC' | 验证等级：BASIC/STRONG/FAMILY |
| verify_method | VARCHAR(32) | Y | NULL | 验证方式：WECHAT_OAUTH/SMS_CODE/ID_CARD/ID_CARD_PHONE/FACE/CARD_PASSWORD/MANUAL |
| verified_at | TIMESTAMP | Y | NULL | 验证时间 |
| is_default | BOOLEAN | N | FALSE | 是否默认就诊人 |
| status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/ACTIVE/REJECTED/UNBOUND/MERGED |
| merged_to_binding_id | BIGINT | Y | NULL | 合并后指向的绑定 ID |
| bound_at | TIMESTAMP | Y | NULL | 绑定时间 |
| bound_ip | VARCHAR(64) | Y | NULL | 绑定 IP |
| unbound_at | TIMESTAMP | Y | NULL | 解绑时间 |
| unbind_reason | VARCHAR(255) | Y | NULL | 解绑原因 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_portal_binding | PRIMARY | id | 主键 |
| uk_mpi_portal_binding | UNIQUE | account_id, patient_id | 同账号不重复绑定 |
| uk_mpi_portal_patient_active | UNIQUE（部分） | patient_id | 一个患者只绑一个活跃账号 |
| idx_mpi_portal_bind_account | NORMAL | account_id, status | 按账号查 |
| idx_mpi_portal_bind_patient | NORMAL | patient_id, status | 按患者查 |
| idx_mpi_portal_bind_default | NORMAL | account_id, is_default | 默认就诊人 |

**约束说明**

```sql
-- 关系枚举
ALTER TABLE mpi_portal_binding
    ADD CONSTRAINT ck_portal_relation
    CHECK (relation IN ('SELF', 'SPOUSE', 'CHILD', 'PARENT', 'OTHER'));

-- 验证等级
ALTER TABLE mpi_portal_binding
    ADD CONSTRAINT ck_portal_bind_verify
    CHECK (verify_level IN ('BASIC', 'STRONG', 'FAMILY'));

-- 绑定状态
ALTER TABLE mpi_portal_binding
    ADD CONSTRAINT ck_portal_bind_status
    CHECK (status IN ('PENDING', 'ACTIVE', 'REJECTED', 'UNBOUND', 'MERGED'));

-- 同一账号同一患者唯一
ALTER TABLE mpi_portal_binding
    ADD CONSTRAINT uk_mpi_portal_binding UNIQUE (account_id, patient_id);

-- 关键：一个患者只能被一个活跃账号绑定
CREATE UNIQUE INDEX uk_mpi_portal_patient_active
    ON mpi_portal_binding (patient_id)
    WHERE status = 'ACTIVE';

-- 关键：同一账号只能有一个默认就诊人
CREATE UNIQUE INDEX uk_mpi_portal_default
    ON mpi_portal_binding (account_id)
    WHERE is_default = TRUE AND status = 'ACTIVE';

-- 关键：同一账号只能有一个本人绑定
CREATE UNIQUE INDEX uk_mpi_portal_self
    ON mpi_portal_binding (account_id)
    WHERE relation = 'SELF' AND status = 'ACTIVE';

-- 未成年人必须有监护人
ALTER TABLE mpi_portal_binding
    ADD CONSTRAINT ck_portal_guardian
    CHECK (relation <> 'CHILD' OR guardian_id IS NOT NULL OR status <> 'ACTIVE');
```

**绑定状态流转**

```
       ┌───────────┐
       │  PENDING  │
       └─────┬─────┘
             │
      ┌──────┼──────┐
      ▼      ▼      ▼
 ┌────────┐ ┌──────────┐
 │ ACTIVE │ │ REJECTED │
 └────┬───┘ └──────────┘
      │
  ┌───┼───────┐
  ▼   ▼       ▼
┌────────┐ ┌────────┐
│UNBOUND │ │ MERGED │
└────────┘ └────────┘
```

### 4.4 表：`mpi_portal_binding_log`（绑定变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| binding_id | BIGINT | N | - | 绑定 ID |
| account_id | VARCHAR(40) | N | - | 门户账号 ID |
| patient_id | BIGINT | N | - | 患者 ID |
| action | VARCHAR(24) | N | - | 动作：BIND/UNBIND/VERIFY_UPGRADE/MERGED/SET_DEFAULT/REJECT |
| verify_method | VARCHAR(32) | Y | NULL | 验证方式 |
| operator_type | VARCHAR(16) | N | 'PATIENT' | 操作人类型：PATIENT/KIOSK/SYSTEM/STAFF |
| operator_id | VARCHAR(64) | Y | NULL | 操作人（账号 ID 或职工 ID） |
| detail | VARCHAR(500) | Y | NULL | 详情 |
| client_ip | VARCHAR(64) | Y | NULL | 客户端 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_portal_bindlog_binding(binding_id, created_at)`；`idx_portal_bindlog_patient(patient_id, created_at)`；`idx_portal_bindlog_account(account_id, created_at)`；`idx_portal_bindlog_action(action, created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **3 年**（绑定属安全事件）。

### 4.5 表：`mpi_portal_session`（门户会话表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| session_id | VARCHAR(64) | N | - | 会话 ID（JWT jti） |
| account_id | VARCHAR(40) | N | - | 门户账号 ID |
| channel | VARCHAR(16) | N | - | 渠道 |
| active_binding | BIGINT | Y | NULL | 当前操作的患者绑定 ID |
| verify_level | VARCHAR(16) | Y | NULL | 会话时的验证等级 |
| client_ip | VARCHAR(64) | Y | NULL | 客户端 IP |
| ip_location | VARCHAR(128) | Y | NULL | IP 归属地 |
| user_agent | VARCHAR(255) | Y | NULL | User-Agent |
| device_info | VARCHAR(255) | Y | NULL | 设备信息 |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/EXPIRED/REVOKED |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| expires_at | TIMESTAMP | N | - | 过期时间 |
| last_active_at | TIMESTAMP | Y | NULL | 最后活跃时间 |
| revoked_at | TIMESTAMP | Y | NULL | 吊销时间 |
| revoke_reason | VARCHAR(255) | Y | NULL | 吊销原因 |

**索引：** `uk_portal_session(session_id)` 唯一；`idx_portal_session_account(account_id, created_at)`；`idx_portal_session_status(status, expires_at)`。

**说明：** 会话表保留 **90 天**，用于安全审计与异常登录排查。

### 4.6 表：`mpi_portal_register_task`（自助建档任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_id | VARCHAR(40) | N | - | 任务号 `RG` + yyyyMMddHHmmss + 3位 |
| account_id | VARCHAR(40) | N | - | 门户账号 ID |
| channel | VARCHAR(16) | Y | NULL | 渠道 |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| id_type | VARCHAR(32) | Y | NULL | 证件类型 |
| id_no_hash | CHAR(64) | Y | NULL | 证件号哈希 |
| id_no_mask | VARCHAR(64) | Y | NULL | 证件号掩码 |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码 |
| ocr_result | JSONB | Y | NULL | OCR 识别结果 |
| check_result | JSONB | Y | NULL | 查重结果（候选患者） |
| verify_result | VARCHAR(16) | Y | NULL | 二要素核验结果：PASS/FAIL |
| status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/VERIFYING/NEED_CONFIRM/SUCCESS/FAILED |
| patient_id | BIGINT | Y | NULL | 建档成功后的患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | 建档成功后的 EMPI |
| error_code | VARCHAR(32) | Y | NULL | 失败错误码 |
| error_msg | VARCHAR(1000) | Y | NULL | 失败原因 |
| submit_payload | JSONB | Y | NULL | 提交的表单数据 |
| client_ip | VARCHAR(64) | Y | NULL | 客户端 IP |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| finished_at | TIMESTAMP | Y | NULL | 完成时间 |

**索引：** `uk_portal_reg_task(task_id)` 唯一；`idx_portal_reg_account(account_id, created_at)`；`idx_portal_reg_status(status, created_at)`；`idx_portal_reg_idhash(id_no_hash)`。

**说明：** 保留 **1 年**；`submit_payload` 存完整表单，便于追溯与问题排查。

### 4.7 表：`mpi_portal_agreement`（协议版本表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| agreement_code | VARCHAR(32) | N | - | 协议代码：SERVICE/PRIVACY/TREATMENT/GUARDIAN/SHARING/MARKETING |
| version | VARCHAR(16) | N | - | 版本号，如 `v2.0` |
| title | VARCHAR(128) | N | - | 标题 |
| content | TEXT | N | - | 协议正文（Markdown/HTML） |
| content_url | VARCHAR(500) | Y | NULL | 正文外链（如 H5 页面） |
| summary | VARCHAR(500) | Y | NULL | 摘要（列表展示） |
| is_required | BOOLEAN | N | TRUE | 是否必签 |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| is_published | BOOLEAN | N | FALSE | 是否已发布 |
| published_at | TIMESTAMP | Y | NULL | 发布时间 |
| published_by | BIGINT | Y | NULL | 发布人 |
| sort_no | INT | N | 999 | 排序 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_portal_agreement(agreement_code, version)` 唯一；`idx_portal_agreement_current(agreement_code, is_published, effective_date)`。

**约束说明**

```sql
ALTER TABLE mpi_portal_agreement
    ADD CONSTRAINT ck_portal_agreement_code
    CHECK (agreement_code IN ('SERVICE', 'PRIVACY', 'TREATMENT',
                               'GUARDIAN', 'SHARING', 'MARKETING'));

ALTER TABLE mpi_portal_agreement
    ADD CONSTRAINT ck_portal_agreement_date
    CHECK (expire_date IS NULL OR expire_date > effective_date);
```

**预置协议：**

| agreement_code | version | 标题 | 必签 |
|---|---|---|---|
| SERVICE | v2.0 | 患者服务协议 | 是 |
| PRIVACY | v1.5 | 隐私政策 | 是 |
| TREATMENT | v1.0 | 就诊授权书 | 是 |
| GUARDIAN | v1.0 | 家属代操作授权书 | 条件 |
| SHARING | v1.0 | 数据共享授权（保险） | 否 |
| MARKETING | v1.0 | 营销信息推送授权 | 否 |

**说明：** 签署记录**不在本表**，落 M03-01 的 `mpi_patient_consent`。

### 4.8 表：`mpi_portal_config`（门户配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| portal_name | VARCHAR(128) | N | '南石眼科患者服务平台' | 平台名称 |
| logo_url | VARCHAR(500) | Y | NULL | Logo |
| service_phone | VARCHAR(32) | Y | NULL | 客服电话 |
| service_time | VARCHAR(64) | Y | NULL | 服务时间 |
| banners | JSONB | Y | NULL | Banner 配置数组 |
| entries | JSONB | Y | NULL | 服务入口配置数组 |
| tabbar | JSONB | Y | NULL | 底部导航配置 |
| browser_title | VARCHAR(128) | Y | NULL | 浏览器标题 |
| icp_number | VARCHAR(64) | Y | NULL | 备案号 |
| token_ttl_seconds | INT | N | 7200 | Token 有效期 |
| sms_interval_seconds | INT | N | 60 | 验证码发送间隔 |
| sms_daily_limit | INT | N | 10 | 单手机号每日上限 |
| sms_ip_daily_limit | INT | N | 30 | 单 IP 每日上限 |
| max_bindings | INT | N | 8 | 单账号绑定上限 |
| verify_max_fail | INT | N | 3 | 二要素失败上限 |
| verify_lock_minutes | INT | N | 60 | 锁定时间 |
| report_rate_per_min | INT | N | 20 | 报告查看频控 |
| require_strong_for_report | BOOLEAN | N | TRUE | 报告是否需强验证 |
| enable_self_register | BOOLEAN | N | TRUE | 是否开放自助建档 |
| enable_family_account | BOOLEAN | N | TRUE | 是否开放家庭账号 |
| enable_kiosk | BOOLEAN | N | TRUE | 是否启用自助机 |
| kiosk_offline_minutes | INT | N | 10 | 自助机离线判定 |
| maintenance_mode | BOOLEAN | N | FALSE | 维护模式（门户显示维护页） |
| maintenance_notice | VARCHAR(500) | Y | NULL | 维护公告 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_portal_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_portal_config
    ADD CONSTRAINT ck_portal_config_single_row CHECK (id = 1);

ALTER TABLE mpi_portal_config
    ADD CONSTRAINT ck_portal_config_limits
    CHECK (max_bindings BETWEEN 1 AND 20
       AND verify_max_fail BETWEEN 1 AND 10
       AND token_ttl_seconds BETWEEN 600 AND 86400);
```

**`banners` 格式：**

```json
[
  {
    "id": 1,
    "image_url": "https://cdn.example.com/banner01.jpg",
    "title": "白内障专家团队",
    "link_type": "PAGE",
    "link_value": "/expert/list",
    "sort_no": 1,
    "enabled": true,
    "start_date": "2026-10-01",
    "end_date": null
  }
]
```

**`entries` 格式：**

```json
[
  { "code": "APPOINTMENT", "name": "预约挂号", "icon": "calendar",
    "path": "/appointment", "enabled": true, "require_verify": "BASIC", "sort_no": 10 },
  { "code": "REPORT", "name": "报告查询", "icon": "file",
    "path": "/report", "enabled": true, "require_verify": "STRONG", "sort_no": 20 }
]
```

### 4.9 表：`mpi_portal_announcement`（公告表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| title | VARCHAR(255) | N | - | 标题 |
| content | TEXT | Y | NULL | 内容 |
| announcement_type | VARCHAR(16) | N | 'NOTICE' | 类型：NOTICE/URGENT/ACTIVITY/MAINTENANCE |
| level | VARCHAR(16) | N | 'NORMAL' | 级别：NORMAL/IMPORTANT/URGENT |
| is_top | BOOLEAN | N | FALSE | 是否置顶 |
| is_scroll | BOOLEAN | N | TRUE | 是否首页滚动 |
| target_channels | VARCHAR(128) | Y | NULL | 目标渠道（逗号分隔，NULL=全部） |
| publish_at | TIMESTAMP | Y | NULL | 发布时间 |
| expire_at | TIMESTAMP | Y | NULL | 过期时间 |
| status | VARCHAR(16) | N | 'DRAFT' | 状态：DRAFT/PUBLISHED/OFFLINE |
| view_count | INT | N | 0 | 浏览次数 |
| operator_id | BIGINT | Y | NULL | 发布人 |
| operator_name | VARCHAR(64) | Y | NULL | 发布人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `idx_portal_ann_publish(status, publish_at, is_top)`；`idx_portal_ann_type(announcement_type, status)`。

**约束说明**

```sql
ALTER TABLE mpi_portal_announcement
    ADD CONSTRAINT ck_portal_ann_status
    CHECK (status IN ('DRAFT', 'PUBLISHED', 'OFFLINE'));

ALTER TABLE mpi_portal_announcement
    ADD CONSTRAINT ck_portal_ann_level
    CHECK (level IN ('NORMAL', 'IMPORTANT', 'URGENT'));

ALTER TABLE mpi_portal_announcement
    ADD CONSTRAINT ck_portal_ann_time
    CHECK (expire_at IS NULL OR expire_at > publish_at);
```

### 4.10 表：`mpi_portal_kiosk`（自助机设备表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| device_code | VARCHAR(64) | N | - | 设备编码，如 `KIOSK-01-001` |
| device_name | VARCHAR(128) | Y | NULL | 设备名称 |
| location | VARCHAR(255) | N | - | 位置描述 |
| dept_id | BIGINT | Y | NULL | 所属科室 |
| dept_name | VARCHAR(128) | Y | NULL | 科室名称 |
| status | VARCHAR(16) | N | 'OFFLINE' | 状态：ONLINE/OFFLINE/FAULT/MAINTENANCE |
| last_heartbeat_at | TIMESTAMP | Y | NULL | 最后心跳时间 |
| firmware_version | VARCHAR(32) | Y | NULL | 固件版本 |
| ip_address | VARCHAR(64) | Y | NULL | 设备 IP |
| mac_address | VARCHAR(32) | Y | NULL | MAC 地址 |
| device_secret | VARCHAR(128) | Y | NULL | 设备密钥（心跳鉴权用，加密存储） |
| capabilities | VARCHAR(128) | Y | NULL | 能力位：IDCARD,FACE,PRINT,SCAN,PAY |
| fault_reason | VARCHAR(255) | Y | NULL | 故障原因 |
| last_maintain_at | TIMESTAMP | Y | NULL | 最后维护时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_portal_kiosk(device_code)` 唯一；`idx_portal_kiosk_status(status, last_heartbeat_at)`；`idx_portal_kiosk_dept(dept_id)`。

**约束说明**

```sql
ALTER TABLE mpi_portal_kiosk
    ADD CONSTRAINT ck_portal_kiosk_status
    CHECK (status IN ('ONLINE', 'OFFLINE', 'FAULT', 'MAINTENANCE'));

ALTER TABLE mpi_portal_kiosk
    ADD CONSTRAINT ck_portal_kiosk_code
    CHECK (device_code ~ '^KIOSK-[0-9]{2}-[0-9]{3}$');
```

### 4.11 表：`mpi_portal_statistics`（门户统计表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| stat_date | DATE | N | - | 统计日期 |
| channel | VARCHAR(16) | N | - | 渠道 |
| visit_count | INT | N | 0 | 访问量（登录次数） |
| uv_count | INT | N | 0 | 独立用户数 |
| new_account_count | INT | N | 0 | 新增账号数 |
| binding_count | INT | N | 0 | 新增绑定数 |
| register_count | INT | N | 0 | 自助建档数 |
| appointment_count | INT | N | 0 | 预约数（转发 M04 数据） |
| report_view_count | INT | N | 0 | 报告查看数 |
| payment_count | INT | N | 0 | 缴费笔数 |
| conversion_rate | NUMERIC(5,2) | N | 0 | 绑定转化率（%） |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_portal_stat(stat_date, channel)` 唯一；`idx_portal_stat_date(stat_date)`。

**说明：** 保留 **3 年**；每日 01:30 由定时任务生成。

### 4.12 表：`mpi_portal_access_log`（门户访问日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| account_id | VARCHAR(40) | Y | NULL | 门户账号 ID（未登录为 NULL） |
| session_id | VARCHAR(64) | Y | NULL | 会话 ID |
| channel | VARCHAR(16) | N | - | 渠道 |
| action | VARCHAR(32) | N | - | 动作：LOGIN/LOGOUT/BIND/UNBIND/REGISTER/VIEW_REPORT/PAY/REVOKE_CONSENT |
| resource_type | VARCHAR(32) | Y | NULL | 资源类型 |
| resource_id | VARCHAR(64) | Y | NULL | 资源 ID |
| patient_id | BIGINT | Y | NULL | 关联患者 ID |
| result | VARCHAR(16) | N | 'SUCCESS' | 结果：SUCCESS/FAILED |
| error_code | VARCHAR(32) | Y | NULL | 错误码 |
| client_ip | VARCHAR(64) | Y | NULL | 客户端 IP |
| ip_location | VARCHAR(128) | Y | NULL | IP 归属地 |
| user_agent | VARCHAR(255) | Y | NULL | User-Agent |
| device_code | VARCHAR(64) | Y | NULL | 自助机编码 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| cost_ms | INT | Y | NULL | 耗时 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_portal_access_account(account_id, created_at)`；`idx_portal_access_action(action, created_at)`；`idx_portal_access_patient(patient_id, created_at)`；`idx_portal_access_ip(client_ip, created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **1 年**。

**说明：** 这是**技术访问日志**，用于运营分析与问题排查。**安全审计事件**（绑定、查看报告、撤回授权）另外写 M02-06 的 `sys_audit_log`。

### 4.13 SQLAlchemy 2.0 模型定义

```python
# app/models/portal/account.py
"""门户账号与会话 ORM 模型"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, DateTime, Index,
    UniqueConstraint, func, Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MpiPortalAccount(Base):
    """门户账号（患者，与 M02 职工账号完全隔离）"""
    __tablename__ = "mpi_portal_account"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(40), nullable=False)

    # 微信身份
    openid: Mapped[Optional[str]] = mapped_column(String(64))
    unionid: Mapped[Optional[str]] = mapped_column(String(64))
    nickname: Mapped[Optional[str]] = mapped_column(String(64))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # 手机号（加密 + 哈希 + 掩码）
    phone: Mapped[Optional[str]] = mapped_column(String(128))
    phone_hash: Mapped[Optional[str]] = mapped_column(String(64))
    phone_mask: Mapped[Optional[str]] = mapped_column(String(32))

    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    verify_level: Mapped[str] = mapped_column(String(16), default="BASIC", nullable=False)

    login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64))
    last_login_channel: Mapped[Optional[str]] = mapped_column(String(16))

    frozen_reason: Mapped[Optional[str]] = mapped_column(String(255))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("account_id", name="uk_mpi_portal_account_id"),
        Index("idx_mpi_portal_unionid", "unionid"),
        Index("idx_mpi_portal_channel", "channel", "created_at"),
        Index("idx_mpi_portal_status", "status", "last_login_at"),
        # 部分唯一索引（PostgreSQL）
        Index("uk_mpi_portal_openid", "openid", unique=True,
              postgresql_where="openid IS NOT NULL AND status <> 'CANCELLED'"),
        Index("uk_mpi_portal_phone", "phone_hash", unique=True,
              postgresql_where="phone_hash IS NOT NULL AND status <> 'CANCELLED'"),
        {"comment": "门户账号（患者）"},
    )

    CHANNELS = {
        "WECHAT_MP": "微信公众号",
        "WECHAT_MINI": "微信小程序",
        "ALIPAY_MINI": "支付宝小程序",
        "KIOSK": "院内自助机",
        "WEB": "网页版",
    }
    STATUS_LABELS = {
        "ACTIVE": "正常", "FROZEN": "已冻结", "CANCELLED": "已注销",
    }
    VERIFY_LABELS = {
        "NONE": "未验证", "BASIC": "基础验证", "STRONG": "强验证",
    }

    def channel_label(self) -> str:
        return self.CHANNELS.get(self.channel, self.channel)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def can_view_sensitive(self) -> bool:
        """是否可查看敏感数据（报告、病历）"""
        return self.verify_level == "STRONG"


class MpiPortalSession(Base):
    """门户会话"""
    __tablename__ = "mpi_portal_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    active_binding: Mapped[Optional[int]] = mapped_column(BigInteger)
    verify_level: Mapped[Optional[str]] = mapped_column(String(16))

    client_ip: Mapped[Optional[str]] = mapped_column(String(64))
    ip_location: Mapped[Optional[str]] = mapped_column(String(128))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    device_info: Mapped[Optional[str]] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint("session_id", name="uk_portal_session"),
        Index("idx_portal_session_account", "account_id", "created_at"),
        Index("idx_portal_session_status", "status", "expires_at"),
        {"comment": "门户会话（保留 90 天）"},
    )

    def is_valid(self) -> bool:
        if self.status != "ACTIVE":
            return False
        return self.expires_at > datetime.now()


class MpiPortalAccessLog(Base):
    """门户访问日志（技术日志，不是安全审计）"""
    __tablename__ = "mpi_portal_access_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[Optional[str]] = mapped_column(String(40))
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    resource_type: Mapped[Optional[str]] = mapped_column(String(32))
    resource_id: Mapped[Optional[str]] = mapped_column(String(64))
    patient_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    result: Mapped[str] = mapped_column(String(16), default="SUCCESS", nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(32))

    client_ip: Mapped[Optional[str]] = mapped_column(String(64))
    ip_location: Mapped[Optional[str]] = mapped_column(String(128))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    device_code: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    cost_ms: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_portal_access_account", "account_id", "created_at"),
        Index("idx_portal_access_action", "action", "created_at"),
        Index("idx_portal_access_patient", "patient_id", "created_at"),
        Index("idx_portal_access_ip", "client_ip", "created_at"),
        {"comment": "门户访问日志（月度分区，保留 1 年）"},
    )

    ACTIONS = {
        "LOGIN": "登录", "LOGOUT": "登出",
        "BIND": "绑定", "UNBIND": "解绑",
        "REGISTER": "自助建档",
        "VIEW_REPORT": "查看报告", "VIEW_EMR": "查看病历",
        "PAY": "缴费", "REVOKE_CONSENT": "撤回授权",
    }

    def action_label(self) -> str:
        return self.ACTIONS.get(self.action, self.action)
```

```python
# app/models/portal/binding.py
"""患者绑定 ORM 模型"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MpiPortalBinding(Base):
    """患者绑定（本人 + 家属）"""
    __tablename__ = "mpi_portal_binding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(String(40), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))

    relation: Mapped[str] = mapped_column(String(16), default="SELF", nullable=False)
    guardian_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    verify_level: Mapped[str] = mapped_column(String(16), default="BASIC", nullable=False)
    verify_method: Mapped[Optional[str]] = mapped_column(String(32))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    merged_to_binding_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    bound_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    bound_ip: Mapped[Optional[str]] = mapped_column(String(64))
    unbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    unbind_reason: Mapped[Optional[str]] = mapped_column(String(255))

    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("account_id", "patient_id", name="uk_mpi_portal_binding"),
        Index("idx_mpi_portal_bind_account", "account_id", "status"),
        Index("idx_mpi_portal_bind_patient", "patient_id", "status"),
        Index("idx_mpi_portal_bind_default", "account_id", "is_default"),
        # 关键约束：一个患者只能被一个活跃账号绑定
        Index("uk_mpi_portal_patient_active", "patient_id", unique=True,
              postgresql_where="status = 'ACTIVE'"),
        # 关键约束：一个账号只能有一个默认就诊人
        Index("uk_mpi_portal_default", "account_id", unique=True,
              postgresql_where="is_default = TRUE AND status = 'ACTIVE'"),
        # 关键约束：一个账号只能有一个本人绑定
        Index("uk_mpi_portal_self", "account_id", unique=True,
              postgresql_where="relation = 'SELF' AND status = 'ACTIVE'"),
        {"comment": "门户患者绑定（本人 + 家属）"},
    )

    RELATIONS = {
        "SELF": "本人", "SPOUSE": "配偶", "CHILD": "子女",
        "PARENT": "父母", "OTHER": "其他",
    }
    VERIFY_LABELS = {
        "BASIC": "基础验证", "STRONG": "强验证", "FAMILY": "家属验证",
    }
    STATUS_LABELS = {
        "PENDING": "待验证", "ACTIVE": "已绑定", "REJECTED": "已拒绝",
        "UNBOUND": "已解绑", "MERGED": "已合并",
    }

    def relation_label(self) -> str:
        return self.RELATIONS.get(self.relation, self.relation)

    def verify_label(self) -> str:
        return self.VERIFY_LABELS.get(self.verify_level, self.verify_level)

    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def is_active(self) -> bool:
        return self.status == "ACTIVE"

    def can_view_sensitive(self) -> bool:
        """是否可查看敏感数据"""
        return self.verify_level in ("STRONG", "FAMILY")

    def is_family(self) -> bool:
        return self.relation != "SELF"


class MpiPortalBindingLog(Base):
    """绑定变更日志"""
    __tablename__ = "mpi_portal_binding_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    binding_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_id: Mapped[str] = mapped_column(String(40), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    verify_method: Mapped[Optional[str]] = mapped_column(String(32))
    operator_type: Mapped[str] = mapped_column(String(16), default="PATIENT", nullable=False)
    operator_id: Mapped[Optional[str]] = mapped_column(String(64))
    detail: Mapped[Optional[str]] = mapped_column(String(500))
    client_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_portal_bindlog_binding", "binding_id", "created_at"),
        Index("idx_portal_bindlog_patient", "patient_id", "created_at"),
        Index("idx_portal_bindlog_account", "account_id", "created_at"),
        Index("idx_portal_bindlog_action", "action", "created_at"),
        {"comment": "门户绑定变更日志（月度分区，保留 3 年）"},
    )

    ACTIONS = {
        "BIND": "绑定", "UNBIND": "解绑",
        "VERIFY_UPGRADE": "提升验证等级",
        "MERGED": "患者合并重定向",
        "SET_DEFAULT": "设为默认",
        "REJECT": "绑定被拒",
    }

    def action_label(self) -> str:
        return self.ACTIONS.get(self.action, self.action)
```

```python
# app/models/portal/config.py
"""门户配置、公告、协议 ORM 模型"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, Date, DateTime, Text,
    JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MpiPortalConfig(Base):
    """门户配置（单行）"""
    __tablename__ = "mpi_portal_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    portal_name: Mapped[str] = mapped_column(
        String(128), default="南石眼科患者服务平台", nullable=False)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    service_phone: Mapped[Optional[str]] = mapped_column(String(32))
    service_time: Mapped[Optional[str]] = mapped_column(String(64))

    banners: Mapped[Optional[dict]] = mapped_column(JSONB)
    entries: Mapped[Optional[dict]] = mapped_column(JSONB)
    tabbar: Mapped[Optional[dict]] = mapped_column(JSONB)

    browser_title: Mapped[Optional[str]] = mapped_column(String(128))
    icp_number: Mapped[Optional[str]] = mapped_column(String(64))

    token_ttl_seconds: Mapped[int] = mapped_column(Integer, default=7200, nullable=False)
    sms_interval_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    sms_daily_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    sms_ip_daily_limit: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    max_bindings: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    verify_max_fail: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    verify_lock_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    report_rate_per_min: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    require_strong_for_report: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False)

    enable_self_register: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_family_account: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_kiosk: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    kiosk_offline_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    maintenance_mode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    maintenance_notice: Mapped[Optional[str]] = mapped_column(String(500))

    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "门户配置（单行）"},
    )

    def get_banners(self) -> list:
        return self.banners or []

    def get_entries(self, verify_level: str = "NONE") -> list:
        """按验证等级过滤可见入口"""
        LEVELS = {"NONE": 0, "BASIC": 1, "STRONG": 2, "FAMILY": 3}
        current = LEVELS.get(verify_level, 0)

        result = []
        for e in (self.entries or []):
            if not e.get("enabled", True):
                continue
            required = LEVELS.get(e.get("require_verify", "NONE"), 0)
            if current >= required:
                result.append(e)

        return sorted(result, key=lambda x: x.get("sort_no", 999))


class MpiPortalAnnouncement(Base):
    """门户公告"""
    __tablename__ = "mpi_portal_announcement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    announcement_type: Mapped[str] = mapped_column(
        String(16), default="NOTICE", nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    is_top: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_scroll: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_channels: Mapped[Optional[str]] = mapped_column(String(128))

    publish_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_portal_ann_publish", "status", "publish_at", "is_top"),
        Index("idx_portal_ann_type", "announcement_type", "status"),
        {"comment": "门户公告"},
    )

    TYPES = {
        "NOTICE": "通知", "URGENT": "紧急",
        "ACTIVITY": "活动", "MAINTENANCE": "维护",
    }
    LEVELS = {"NORMAL": "普通", "IMPORTANT": "重要", "URGENT": "紧急"}

    def type_label(self) -> str:
        return self.TYPES.get(self.announcement_type, self.announcement_type)

    def level_label(self) -> str:
        return self.LEVELS.get(self.level, self.level)

    def is_visible(self, channel: Optional[str] = None) -> bool:
        """当前是否可见"""
        now = datetime.now()
        if self.status != "PUBLISHED":
            return False
        if self.publish_at and self.publish_at > now:
            return False
        if self.expire_at and self.expire_at <= now:
            return False
        if channel and self.target_channels:
            if channel not in self.target_channels.split(","):
                return False
        return True


class MpiPortalAgreement(Base):
    """协议版本"""
    __tablename__ = "mpi_portal_agreement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    agreement_code: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(String(500))
    summary: Mapped[Optional[str]] = mapped_column(String(500))

    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    published_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("agreement_code", "version", name="uk_portal_agreement"),
        Index("idx_portal_agreement_current",
              "agreement_code", "is_published", "effective_date"),
        {"comment": "门户协议版本（签署记录在 mpi_patient_consent）"},
    )

    CODES = {
        "SERVICE": "患者服务协议", "PRIVACY": "隐私政策",
        "TREATMENT": "就诊授权书", "GUARDIAN": "家属代操作授权书",
        "SHARING": "数据共享授权", "MARKETING": "营销信息推送授权",
    }

    def code_label(self) -> str:
        return self.CODES.get(self.agreement_code, self.agreement_code)

    def is_current(self) -> bool:
        """是否为当前生效版本"""
        today = date.today()
        if not self.is_published:
            return False
        if self.effective_date > today:
            return False
        if self.expire_date and self.expire_date <= today:
            return False
        return True
```

```python
# app/models/portal/kiosk.py
"""自助机与统计 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, Date, DateTime, Numeric,
    Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MpiPortalKiosk(Base):
    """自助机设备"""
    __tablename__ = "mpi_portal_kiosk"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    device_code: Mapped[str] = mapped_column(String(64), nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(128))
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    dept_name: Mapped[Optional[str]] = mapped_column(String(128))

    status: Mapped[str] = mapped_column(String(16), default="OFFLINE", nullable=False)
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(32))

    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    mac_address: Mapped[Optional[str]] = mapped_column(String(32))
    device_secret: Mapped[Optional[str]] = mapped_column(String(128))
    capabilities: Mapped[Optional[str]] = mapped_column(String(128))

    fault_reason: Mapped[Optional[str]] = mapped_column(String(255))
    last_maintain_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("device_code", name="uk_portal_kiosk"),
        Index("idx_portal_kiosk_status", "status", "last_heartbeat_at"),
        Index("idx_portal_kiosk_dept", "dept_id"),
        {"comment": "院内自助机设备"},
    )

    STATUS_LABELS = {
        "ONLINE": "在线", "OFFLINE": "离线",
        "FAULT": "故障", "MAINTENANCE": "维护中",
    }

    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def get_capabilities(self) -> list:
        if not self.capabilities:
            return []
        return [c.strip() for c in self.capabilities.split(",") if c.strip()]

    def has_capability(self, cap: str) -> bool:
        return cap in self.get_capabilities()

    def is_online(self) -> bool:
        return self.status == "ONLINE"


class MpiPortalStatistics(Base):
    """门户统计（按日按渠道）"""
    __tablename__ = "mpi_portal_statistics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)

    visit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uv_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_account_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    binding_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    register_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    appointment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    report_view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversion_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("stat_date", "channel", name="uk_portal_stat"),
        Index("idx_portal_stat_date", "stat_date"),
        {"comment": "门户统计（按日按渠道，保留 3 年）"},
    )

    def calc_conversion_rate(self) -> Decimal:
        """计算绑定转化率"""
        if not self.visit_count:
            return Decimal("0.00")
        return round(
            Decimal(self.binding_count) / Decimal(self.visit_count) * 100, 2)
```

### 4.14 Pydantic Schema 定义

```python
# app/schemas/portal/auth.py
"""门户认证 Schema"""
from typing import Optional, List, Literal
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


CHANNEL = Literal["WECHAT_MP", "WECHAT_MINI", "ALIPAY_MINI", "KIOSK", "WEB"]
VERIFY_LEVEL = Literal["NONE", "BASIC", "STRONG"]
RELATION = Literal["SELF", "SPOUSE", "CHILD", "PARENT", "OTHER"]


class WechatLoginRequest(BaseModel):
    channel: CHANNEL = "WECHAT_MINI"
    code: str = Field(..., min_length=4, max_length=128)
    phone_code: Optional[str] = Field(None, max_length=128)
    agree_service: bool
    agree_privacy: bool

    @model_validator(mode="after")
    def validate_agreement(self):
        if not self.agree_service or not self.agree_privacy:
            raise ValueError("必须同意服务协议与隐私政策")
        if self.channel not in ("WECHAT_MP", "WECHAT_MINI"):
            raise ValueError("微信登录仅支持 WECHAT_MP / WECHAT_MINI")
        return self


class SmsLoginRequest(BaseModel):
    phone: str = Field(..., max_length=16)
    sms_code: str = Field(..., min_length=4, max_length=8)
    channel: Optional[CHANNEL] = "WEB"
    agree_service: bool
    agree_privacy: bool

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("sms_code")
    @classmethod
    def validate_code(cls, v):
        if not re.fullmatch(r"\d{4,8}", v):
            raise ValueError("验证码格式不正确")
        return v

    @model_validator(mode="after")
    def validate_agreement(self):
        if not self.agree_service or not self.agree_privacy:
            raise ValueError("必须同意服务协议与隐私政策")
        return self


class SmsSendRequest(BaseModel):
    phone: str = Field(..., max_length=16)
    scene: Literal["LOGIN", "BIND", "REVOKE", "CHANGE_PHONE"] = "LOGIN"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v


class IdCardLoginRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_type: str = Field("ID_CARD", max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)
    channel: CHANNEL = "WEB"
    agree_service: bool
    agree_privacy: bool


class KioskLoginRequest(BaseModel):
    device_code: str = Field(..., max_length=64)
    device_secret: str = Field(..., max_length=128)
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)
    face_image_base64: Optional[str] = None
    agree_service: bool = True
    agree_privacy: bool = True


class BindingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    binding_id: int
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    relation: str
    relation_text: Optional[str] = None
    verify_level: str
    is_default: bool = False


class TokenResponse(BaseModel):
    token: str
    expires_in: int = 7200
    account_id: str
    is_new_account: bool = False
    bindings: List[BindingItem] = []
    need_binding: bool = False
    next_action: Literal["HOME", "BIND_PATIENT", "VERIFY"] = "HOME"
    verify_hint: Optional[str] = None


class PortalAccountInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str
    channel: str
    phone_mask: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    verify_level: str
    login_count: int = 0
    last_login_at: Optional[str] = None
```

```python
# app/schemas/portal/binding.py
"""门户绑定 Schema"""
from typing import Optional, Literal, List
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


RELATION = Literal["SELF", "SPOUSE", "CHILD", "PARENT", "OTHER"]
VERIFY_METHOD = Literal["ID_CARD", "ID_CARD_PHONE", "FACE", "SMS_CODE", "MANUAL"]


def _validate_id_no(v: str) -> str:
    """身份证号校验（含校验位）"""
    if not re.fullmatch(r"\d{17}[\dXx]", v):
        raise ValueError("身份证号格式不正确")

    weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_codes = "10X98765432"
    total = sum(int(v[i]) * weights[i] for i in range(17))

    if check_codes[total % 11] != v[17].upper():
        raise ValueError("身份证号校验位不正确")

    return v.upper()


class BindingCreate(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_type: str = Field("ID_CARD", max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)
    phone: Optional[str] = Field(None, max_length=16)
    sms_code: Optional[str] = Field(None, min_length=4, max_length=8)
    relation: RELATION = "SELF"
    guardian_declare: bool = False

    @field_validator("id_no")
    @classmethod
    def validate_id_no(cls, v, info):
        if info.data.get("id_type", "ID_CARD") == "ID_CARD":
            return _validate_id_no(v)
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v

    @model_validator(mode="after")
    def validate_binding(self):
        if self.relation == "CHILD" and not self.guardian_declare:
            raise ValueError("绑定子女需勾选监护人声明")
        return self


class BindingUpdate(BaseModel):
    is_default: Optional[bool] = None
    relation: Optional[RELATION] = None
    remark: Optional[str] = Field(None, max_length=500)


class VerifyUpgradeRequest(BaseModel):
    method: VERIFY_METHOD
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)
    image_base64: Optional[str] = None

    @field_validator("id_no")
    @classmethod
    def validate_id(cls, v):
        return _validate_id_no(v)

    @model_validator(mode="after")
    def validate_method(self):
        if self.method == "FACE" and not self.image_base64:
            raise ValueError("人脸验证必须上传照片")
        return self


class BindingDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    binding_id: int
    account_id: str
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    relation: str
    relation_text: Optional[str] = None
    guardian_id: Optional[int] = None
    verify_level: str
    verify_method: Optional[str] = None
    is_default: bool = False
    status: str
    status_text: Optional[str] = None
    bound_at: Optional[str] = None
    verified_at: Optional[str] = None


class BindingListResult(BaseModel):
    total: int
    max: int = 8
    items: List[BindingDetail] = []
```

```python
# app/schemas/portal/register.py
"""自助建档 Schema"""
from datetime import date
from typing import Optional, Dict, Literal
import re

from pydantic import BaseModel, Field, field_validator, model_validator


class RegisterCheckRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_type: str = Field("ID_CARD", max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)

    @field_validator("id_no")
    @classmethod
    def validate_id(cls, v, info):
        if info.data.get("id_type", "ID_CARD") == "ID_CARD":
            if not re.fullmatch(r"\d{17}[\dXx]", v):
                raise ValueError("身份证号格式不正确")
        return v.upper()


class OcrRequest(BaseModel):
    image_base64: str = Field(..., min_length=32)
    side: Literal["FRONT", "BACK"] = "FRONT"


class OcrResult(BaseModel):
    patient_name: Optional[str] = None
    gender: Optional[str] = None
    nation: Optional[str] = None
    birth_date: Optional[date] = None
    id_no: Optional[str] = None
    address: Optional[str] = None
    issue_org: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    confidence: Optional[float] = None


class RegisterSubmit(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=32)
    id_type: str = Field("ID_CARD", max_length=32)
    id_no: str = Field(..., min_length=6, max_length=32)
    phone: str = Field(..., max_length=16)
    sms_code: str = Field(..., min_length=4, max_length=8)
    address: Optional[str] = Field(None, max_length=255)
    nation: Optional[str] = Field(None, max_length=32)
    marriages: Optional[str] = Field(None, max_length=32)
    occupation: Optional[str] = Field(None, max_length=64)
    education: Optional[str] = Field(None, max_length=32)
    agreements: Dict[str, str] = Field(..., description="协议代码 → 版本号")
    idcard_verify_token: Optional[str] = Field(None, max_length=64)
    force_create: bool = False

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if not re.fullmatch(r"1[3-9]\d{9}", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("id_no")
    @classmethod
    def validate_id(cls, v, info):
        if info.data.get("id_type", "ID_CARD") == "ID_CARD":
            if not re.fullmatch(r"\d{17}[\dXx]", v):
                raise ValueError("身份证号格式不正确")
        return v.upper()

    @model_validator(mode="after")
    def validate_agreements(self):
        required = {"SERVICE", "PRIVACY", "TREATMENT"}
        missing = required - set(self.agreements.keys())
        if missing:
            raise ValueError(f"缺少必签协议：{', '.join(sorted(missing))}")
        return self


class RegisterCandidate(BaseModel):
    empi_no: str
    patient_name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_card_mask: Optional[str] = None
    match_score: float = 0.0
    match_reason: Optional[str] = None


class RegisterResult(BaseModel):
    task_id: str
    status: Literal["SUCCESS", "NEED_CONFIRM", "FAILED", "PENDING"]
    patient_id: Optional[int] = None
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    binding_id: Optional[int] = None
    verify_level: Optional[str] = None
    candidates: Optional[list] = None
    actions: Optional[list] = None
    next_action: Optional[str] = None
    error_msg: Optional[str] = None
```

```python
# app/schemas/portal/business.py
"""门户业务入口 Schema"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class HomeRequest(BaseModel):
    binding_id: Optional[int] = None


class BannerItem(BaseModel):
    id: int
    image_url: str
    title: Optional[str] = None
    link_type: Optional[str] = None
    link_value: Optional[str] = None
    sort_no: int = 999


class EntryItem(BaseModel):
    code: str
    name: str
    icon: Optional[str] = None
    path: Optional[str] = None
    enabled: bool = True
    sort_no: int = 999


class CurrentPatient(BaseModel):
    binding_id: int
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    relation: str = "SELF"
    verify_level: str = "BASIC"
    member_level: Optional[str] = None


class AnnouncementBrief(BaseModel):
    id: int
    title: str
    publish_at: Optional[str] = None


class TodoItem(BaseModel):
    type: Literal["APPOINTMENT", "FOLLOWUP", "REPORT", "BILL"]
    level: Literal["HIGH", "MEDIUM", "LOW"] = "LOW"
    title: str
    subtitle: Optional[str] = None
    biz_id: Optional[str] = None
    actions: List[str] = []


class HomeResult(BaseModel):
    current_patient: Optional[CurrentPatient] = None
    banners: List[BannerItem] = []
    entries: List[EntryItem] = []
    announcement: Optional[AnnouncementBrief] = None
    todos: List[TodoItem] = []
    todo_count: int = 0
    unread_message_count: int = 0


class ReportQuery(BaseModel):
    binding_id: int
    report_type: Optional[Literal["EXAM", "LIS", "PATHO"]] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=50)


class ReportItem(BaseModel):
    report_id: str
    report_type: str
    report_name: str
    report_date: Optional[str] = None
    dept_name: Optional[str] = None
    doctor_name: Optional[str] = None
    status: Optional[str] = None


class ReportDetail(ReportItem):
    patient_name: Optional[str] = None
    conclusion: Optional[str] = None
    findings: List[dict] = []
    images: List[dict] = []
    report_status: Optional[str] = None
    view_count: int = 0


class PaymentRequest(BaseModel):
    binding_id: int
    bill_ids: List[str] = Field(..., min_length=1, max_length=20)
    pay_method: Literal["WECHAT", "ALIPAY", "UNIONPAY"] = "WECHAT"


class PaymentResult(BaseModel):
    order_no: str
    total_amount: float
    pay_params: dict
    expire_at: Optional[str] = None


class FollowupSubmit(BaseModel):
    task_id: int
    answers: dict
    submit_time: Optional[str] = None


class ConsentItem(BaseModel):
    consent_id: Optional[int] = None
    consent_type: str
    consent_type_text: Optional[str] = None
    consent_version: Optional[str] = None
    consent_value: str
    signed_at: Optional[str] = None
    revoked_at: Optional[str] = None


class ConsentRevokeRequest(BaseModel):
    sms_code: str = Field(..., min_length=4, max_length=8)
    reason: Optional[str] = Field(None, max_length=255)


class AgreementSignRequest(BaseModel):
    agreements: dict
    binding_id: Optional[int] = None
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：11 张表 | 系统设计组 |
