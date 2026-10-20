# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块数据结构：会员

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 会员（Member）
**主数据域：** 患者域（`MPI`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 03 会员 详细设计》《M01 主数据管理MDM》《M02 统一权限与安全》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「会员」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[会员详细设计](M03_患者服务与EMPI_03_会员_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [会员详细设计](M03_患者服务与EMPI_03_会员_详细设计.md)
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md)
- [01 患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md) — `mpi_patient` 等
- [02 患者匹配合并与质量数据结构](M03_患者服务与EMPI_02_患者匹配合并与质量_数据结构.md)
- [M01 数据结构设计汇总](../M01主数据管理MDM/M01_主数据管理MDM_数据结构设计汇总.md) — `mdm_employee` / `mdm_department` / `md_dict_item` / `md_dict_type` / `md_sys_param`
- [M02 账号管理数据结构](../M02统一权限与安全/M02_统一权限与安全_01_账号管理_数据结构.md) — `sys_account`
- [M02 审计日志数据结构](../M02统一权限与安全/M02_统一权限与安全_06_审计日志_数据结构.md) — `sys_audit_log`

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 11 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_member_config`（会员配置表）](#42-表mpi_member_config会员配置表)
- [4.3 表：`mpi_member_level`（会员等级表）](#43-表mpi_member_level会员等级表)
- [4.4 表：`mpi_member_benefit`（会员权益表）](#44-表mpi_member_benefit会员权益表)
- [4.5 表：`mpi_member_level_benefit`（等级-权益关联表）](#45-表mpi_member_level_benefit等级-权益关联表)
- [4.6 表：`mpi_member_tag`（会员标签表）](#46-表mpi_member_tag会员标签表)
- [4.7 表：`mpi_member`（会员主表）](#47-表mpi_member会员主表)
- [4.8 表：`mpi_member_tag_rel`（会员-标签关联表）](#48-表mpi_member_tag_rel会员-标签关联表)
- [4.9 表：`mpi_member_log`（会员变更日志表）](#49-表mpi_member_log会员变更日志表)
- [4.10 表：`mpi_member_import_task`（会员导入任务表）](#410-表mpi_member_import_task会员导入任务表)
- [4.11 表：`mpi_member_import_detail`（会员导入明细表）](#411-表mpi_member_import_detail会员导入明细表)
- [4.12 表：`mpi_member_code_seq`（会员号序列表）](#412-表mpi_member_code_seq会员号序列表)
- [4.13 SQLAlchemy 2.0 模型定义](#413-sqlalchemy-20-模型定义)
- [4.14 Pydantic Schema 定义](#414-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_member_config` | 会员配置表（单行） |
| 4.3 | `mpi_member_level` | 会员等级表 |
| 4.4 | `mpi_member_benefit` | 会员权益表 |
| 4.5 | `mpi_member_level_benefit` | 等级-权益关联表 |
| 4.6 | `mpi_member_tag` | 会员标签表 |
| 4.7 | `mpi_member` | 会员主表 |
| 4.8 | `mpi_member_tag_rel` | 会员-标签关联表 |
| 4.9 | `mpi_member_log` | 会员变更日志表 |
| 4.10 | `mpi_member_import_task` | 会员导入任务表 |
| 4.11 | `mpi_member_import_detail` | 会员导入明细表 |
| 4.12 | `mpi_member_code_seq` | 会员号序列表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 01 依赖（逻辑引用）                                                  │
│ mpi_patient / mpi_patient_contact                                    │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ M01/M02 依赖（逻辑引用）                                              │
│ mdm_employee / mdm_department / md_dict_item / md_dict_type         │
│ md_sys_param / sys_account / sys_audit_log                          │
└──────────────────────────────────────────────────────────────────────┘

配置与等级：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_member_config            │  │ mpi_member_level             │
│ （会员配置，单行）             │  │ （会员等级）                  │
└──────────────────────────────┘  └──────────┬───────────────────┘
                                             │ 1:N
                                             ▼
                                  ┌──────────────────────────────┐
                                  │ mpi_member_level_benefit     │
                                  │ （等级-权益关联）              │
                                  └──────────┬───────────────────┘
                                             │ N:1
                                             ▼
                                  ┌──────────────────────────────┐
                                  │ mpi_member_benefit           │
                                  │ （会员权益）                  │
                                  └──────────────────────────────┘

会员：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_member                   │──►│ mpi_member_tag_rel           │
│ （会员主表）                  │  │ （会员-标签关联）              │
└──────────┬───────────────────┘  └──────────┬───────────────────┘
           │ N:1                              │ N:1
           ▼                                  ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_member_level             │  │ mpi_member_tag               │
│ （等级，冗余字段 level_code）  │  │ （标签）                      │
└──────────────────────────────┘  └──────────────────────────────┘

导入与日志：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_member_import_task       │──►│ mpi_member_import_detail     │
│ （导入任务）                  │  │ （导入明细）                  │
└──────────────────────────────┘  └──────────────────────────────┘
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_member_log               │  │ mpi_member_code_seq          │
│ （变更日志，月分区）           │  │ （会员号序列，DB 对账）       │
└──────────────────────────────┘  └──────────────────────────────┘
```

**说明：**

- 所有表统一 `mpi_` 前缀，逻辑删除统一 `is_deleted BOOLEAN DEFAULT FALSE`。
- 状态统一 `VARCHAR(16)`，大写英文枚举。
- 跨模块逻辑引用不建物理外键。
- `mpi_member_log` / `mpi_member_import_detail` 按 `created_at` 月度 RANGE 分区。
- 会员表冗余 `level_code` / `level_name` / `level_seq`，避免消费场景频繁 JOIN。

### 4.2 表：`mpi_member_config`（会员配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| member_no_prefix | VARCHAR(8) | N | 'M' | 会员号前缀 |
| member_seq_len | INT | N | 6 | 会员号流水位数 |
| allow_manual_member_no | BOOLEAN | N | TRUE | 允许手工录入会员号 |
| default_level_code | VARCHAR(32) | N | 'NORMAL' | 默认等级代码 |
| open_on_registration | BOOLEAN | N | TRUE | 建档时提示开通会员 |
| open_on_charge | BOOLEAN | N | TRUE | 收费时提示开通会员 |
| level_up_by_m19 | BOOLEAN | N | TRUE | 升级由 M19 回写 |
| level_down_by_m19 | BOOLEAN | N | TRUE | 降级由 M19 回写 |
| level_down_need_approval | BOOLEAN | N | TRUE | 降级需审批 |
| benefit_cache_ttl_seconds | INT | N | 300 | 权益查询缓存秒数 |
| auto_expire_enabled | BOOLEAN | N | TRUE | 启用自动过期 |
| auto_expire_days | INT | N | 730 | 长期未活跃天数 |
| expire_remind_days | INT | N | 30 | 过期前提醒天数 |
| subscribe_patient_merge | BOOLEAN | N | TRUE | 订阅患者合并事件 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人（`sys_account.id`） |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_mpi_member_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_member_config
    ADD CONSTRAINT ck_mpi_member_config_single_row CHECK (id = 1);
```

### 4.3 表：`mpi_member_level`（会员等级表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| level_code | VARCHAR(32) | N | - | 等级代码（大写字母+下划线） |
| level_name | VARCHAR(32) | N | - | 等级名称 |
| level_seq | INT | N | - | 等级序号，数值越大等级越高 |
| growth_threshold | NUMERIC(14,2) | N | 0.00 | 成长值门槛 |
| consume_threshold | NUMERIC(14,2) | N | 0.00 | 消费额门槛 |
| upgrade_logic | VARCHAR(8) | N | 'OR' | 升级逻辑：OR/AND |
| is_default | BOOLEAN | N | FALSE | 是否默认等级 |
| switch_policy | VARCHAR(16) | N | 'BOTH' | 等级切换策略：AUTO/MANUAL/BOTH |
| color | VARCHAR(16) | Y | NULL | 前端展示颜色 |
| icon_url | VARCHAR(255) | Y | NULL | 图标 |
| member_count | INT | N | 0 | 会员数（冗余，定时刷新） |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| sort_no | INT | N | 999 | 排序 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_member_level | PRIMARY | id | 主键 |
| uk_mpi_member_level_code | UNIQUE | level_code, is_deleted | 等级代码唯一 |
| uk_mpi_member_level_seq | UNIQUE | level_seq, is_deleted | 等级序号唯一 |
| uk_mpi_member_level_default | UNIQUE(PARTIAL) | is_default | 默认等级唯一 |
| idx_mpi_member_level_enabled | NORMAL | is_enabled, sort_no | 启用等级 |

**约束说明**

```sql
ALTER TABLE mpi_member_level
    ADD CONSTRAINT ck_mpi_member_level_logic
    CHECK (upgrade_logic IN ('OR', 'AND'));

ALTER TABLE mpi_member_level
    ADD CONSTRAINT ck_mpi_member_level_policy
    CHECK (switch_policy IN ('AUTO', 'MANUAL', 'BOTH'));

-- 默认等级唯一
CREATE UNIQUE INDEX uk_mpi_member_level_default
    ON mpi_member_level (is_default)
    WHERE is_default = TRUE AND is_deleted = FALSE;
```

### 4.4 表：`mpi_member_benefit`（会员权益表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| benefit_code | VARCHAR(32) | N | - | 权益代码（`BEN-{类型}-{序号}`） |
| benefit_name | VARCHAR(64) | N | - | 权益名称 |
| benefit_type | VARCHAR(32) | N | - | 类型：DISCOUNT/POINTS_RATE/FREE_SERVICE/BIRTHDAY_GIFT/PRIORITY_BOOKING/EXCLUSIVE_PRICE/STORAGE_DISCOUNT/OTHER |
| scope | VARCHAR(32) | N | 'ALL' | 适用范围：ALL/CHARGE_CLASS/CHARGE_ITEM/OPTICAL/REFRACTIVE/MEMBER_ONLY |
| scope_value | VARCHAR(500) | Y | NULL | 范围值（类别编码/项目编码列表/品类） |
| default_value | VARCHAR(64) | N | - | 默认值 |
| value_unit | VARCHAR(16) | Y | NULL | 单位：%/倍/次/元/— |
| min_value | NUMERIC(14,4) | Y | NULL | 最小值（数值型） |
| max_value | NUMERIC(14,4) | Y | NULL | 最大值（数值型） |
| description | VARCHAR(500) | Y | NULL | 描述 |
| sort_no | INT | N | 999 | 排序 |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_member_benefit_code(benefit_code, is_deleted)` 唯一；`idx_mpi_member_benefit_type(benefit_type, is_enabled)`；`idx_mpi_member_benefit_scope(scope, is_enabled)`。

**约束说明**

```sql
ALTER TABLE mpi_member_benefit
    ADD CONSTRAINT ck_mpi_benefit_type
    CHECK (benefit_type IN (
        'DISCOUNT', 'POINTS_RATE', 'FREE_SERVICE', 'BIRTHDAY_GIFT',
        'PRIORITY_BOOKING', 'EXCLUSIVE_PRICE', 'STORAGE_DISCOUNT', 'OTHER'
    ));

ALTER TABLE mpi_member_benefit
    ADD CONSTRAINT ck_mpi_benefit_scope
    CHECK (scope IN ('ALL', 'CHARGE_CLASS', 'CHARGE_ITEM', 'OPTICAL',
                      'REFRACTIVE', 'MEMBER_ONLY'));
```

### 4.5 表：`mpi_member_level_benefit`（等级-权益关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| level_id | BIGINT | N | - | 等级 ID |
| level_code | VARCHAR(32) | N | - | 等级代码（冗余） |
| benefit_id | BIGINT | N | - | 权益 ID |
| benefit_code | VARCHAR(32) | N | - | 权益代码（冗余） |
| benefit_type | VARCHAR(32) | N | - | 权益类型（冗余） |
| scope | VARCHAR(32) | N | - | 适用范围（冗余） |
| scope_value | VARCHAR(500) | Y | NULL | 范围值（冗余） |
| override_value | VARCHAR(64) | Y | NULL | 覆盖值（为空则用权益默认值） |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| sort_no | INT | N | 999 | 排序 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_level_benefit(level_id, benefit_id, scope, scope_value, is_deleted)` 唯一；`idx_mpi_level_benefit_level(level_id, is_enabled)`；`idx_mpi_level_benefit_benefit(benefit_id)`。

### 4.6 表：`mpi_member_tag`（会员标签表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| tag_code | VARCHAR(32) | N | - | 标签代码 |
| tag_name | VARCHAR(32) | N | - | 标签名称 |
| tag_type | VARCHAR(16) | N | 'MANUAL' | 类型：MANUAL/RULE/SYSTEM |
| color | VARCHAR(16) | N | '#999999' | 颜色（前端展示） |
| tag_group | VARCHAR(32) | Y | NULL | 分组 |
| member_count | INT | N | 0 | 会员数（冗余，定时刷新） |
| description | VARCHAR(500) | Y | NULL | 描述 |
| sort_no | INT | N | 999 | 排序 |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_member_tag_code(tag_code, is_deleted)` 唯一；`idx_mpi_member_tag_type(tag_type, is_enabled)`；`idx_mpi_member_tag_group(tag_group, is_enabled)`。

**约束说明**

```sql
ALTER TABLE mpi_member_tag
    ADD CONSTRAINT ck_mpi_member_tag_type
    CHECK (tag_type IN ('MANUAL', 'RULE', 'SYSTEM'));
```

### 4.7 表：`mpi_member`（会员主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| member_no | VARCHAR(32) | N | - | 会员号 `M+yyyyMMdd+6位流水` |
| patient_id | BIGINT | N | - | 患者 ID（一患者一会员） |
| empi_no | VARCHAR(32) | Y | NULL | 患者 EMPI（冗余） |
| member_name | VARCHAR(64) | N | - | 会员姓名（冗余自患者） |
| member_phone_enc | VARCHAR(512) | Y | NULL | 手机号加密值 |
| member_phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码 |
| gender | VARCHAR(16) | Y | NULL | 性别（冗余） |
| birthday | DATE | Y | NULL | 生日（可覆盖患者出生日期） |
| level_id | BIGINT | N | - | 等级 ID |
| level_code | VARCHAR(32) | N | - | 等级代码（冗余） |
| level_name | VARCHAR(32) | N | - | 等级名称（冗余） |
| level_seq | INT | N | - | 等级序号（冗余） |
| status | VARCHAR(16) | N | 'ACTIVE' | ACTIVE/FROZEN/EXPIRED/CANCELLED |
| status_reason | VARCHAR(500) | Y | NULL | 状态原因 |
| source | VARCHAR(32) | N | - | 来源：OUTPATIENT/INPATIENT/OPTOMETRY/REFRACTIVE/MINIAPP/REFERRAL/IMPORT/STAFF/OTHER |
| join_date | DATE | N | - | 加入日期 |
| last_active_at | TIMESTAMP | Y | NULL | 最后活跃时间 |
| expire_at | DATE | Y | NULL | 过期日期（NULL=长期） |
| frozen_at | TIMESTAMP | Y | NULL | 冻结时间 |
| cancelled_at | TIMESTAMP | Y | NULL | 注销时间 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| org_id | BIGINT | N | 1 | 院区 ID |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_member | PRIMARY | id | 主键 |
| uk_mpi_member_no | UNIQUE | member_no, is_deleted | 会员号唯一 |
| uk_mpi_member_patient | UNIQUE | patient_id, is_deleted | 一患者一会员 |
| idx_mpi_member_level | NORMAL | level_code, status | 按等级 |
| idx_mpi_member_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_member_source | NORMAL | source, created_at | 按来源 |
| idx_mpi_member_name | NORMAL | member_name | 姓名检索 |
| idx_mpi_member_phone | NORMAL | member_phone_mask | 手机号掩码检索（粗筛） |
| idx_mpi_member_join | NORMAL | join_date | 加入日期 |
| idx_mpi_member_expire | NORMAL | expire_at, status | 过期扫描 |

**约束说明**

```sql
ALTER TABLE mpi_member
    ADD CONSTRAINT ck_mpi_member_status
    CHECK (status IN ('ACTIVE', 'FROZEN', 'EXPIRED', 'CANCELLED'));

ALTER TABLE mpi_member
    ADD CONSTRAINT ck_mpi_member_source
    CHECK (source IN ('OUTPATIENT', 'INPATIENT', 'OPTOMETRY', 'REFRACTIVE',
                       'MINIAPP', 'REFERRAL', 'IMPORT', 'STAFF', 'OTHER'));

-- 一患者一会员
CREATE UNIQUE INDEX uk_mpi_member_patient
    ON mpi_member (patient_id)
    WHERE is_deleted = FALSE;
```

**字段说明补充：**

- `level_code` / `level_name` / `level_seq` 冗余自 `mpi_member_level`，避免消费场景高频 JOIN。
- `member_name` / `member_phone_enc` / `member_phone_mask` / `gender` 冗余自 `mpi_patient`，患者信息变更时由 M03-01 事件触发本模块更新。
- `birthday` 允许覆盖患者出生日期（用于生日礼权益）。
- `last_active_at` 由 M16/M10/M11 消费时上报更新（预留内部接口），用于自动过期判断。
- `expire_at` 为 NULL 表示长期有效。

**分区：** 不分区（会员总量 ≤ 50 万）。

### 4.8 表：`mpi_member_tag_rel`（会员-标签关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| member_id | BIGINT | N | - | 会员 ID |
| tag_id | BIGINT | N | - | 标签 ID |
| tag_code | VARCHAR(32) | N | - | 标签代码（冗余） |
| tag_type | VARCHAR(16) | N | - | 标签类型（冗余） |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_member_tag_rel(member_id, tag_id, is_deleted)` 唯一；`idx_mpi_member_tag_rel_member(member_id)`；`idx_mpi_member_tag_rel_tag(tag_id)`；`idx_mpi_member_tag_rel_code(tag_code)`。

### 4.9 表：`mpi_member_log`（会员变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| member_id | BIGINT | N | - | 会员 ID |
| member_no | VARCHAR(32) | Y | NULL | 会员号（冗余） |
| action | VARCHAR(32) | N | - | 动作（见附录 E） |
| before_json | JSONB | Y | NULL | 变更前快照 |
| after_json | JSONB | Y | NULL | 变更后快照 |
| detail | VARCHAR(1000) | Y | NULL | 操作详情/原因 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| user_agent | VARCHAR(255) | Y | NULL | 终端 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_mpi_member_log_member(member_id, created_at)`；`idx_mpi_member_log_no(member_no, created_at)`；`idx_mpi_member_log_action(action, created_at)`；`idx_mpi_member_log_operator(operator_id, created_at)`；`idx_mpi_member_log_time(created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**。

### 4.10 表：`mpi_member_import_task`（会员导入任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| code | VARCHAR(32) | N | - | 任务号 `MI+年月日+流水` |
| file_name | VARCHAR(255) | N | - | 文件名 |
| file_url | VARCHAR(500) | Y | NULL | 文件 URL |
| file_size | BIGINT | Y | NULL | 文件大小 |
| total_rows | INT | N | 0 | 总行数 |
| valid_rows | INT | N | 0 | 校验通过行数 |
| warn_rows | INT | N | 0 | 警告行数 |
| error_rows | INT | N | 0 | 错误行数 |
| success_rows | INT | N | 0 | 成功导入行数 |
| fail_rows | INT | N | 0 | 失败行数 |
| error_strategy | VARCHAR(16) | N | 'SKIP' | SKIP/ABORT |
| task_status | VARCHAR(16) | N | 'VALIDATING' | VALIDATING/VALIDATED/IMPORTING/SUCCESS/PARTIAL/FAILED/CANCELLED |
| validate_result | JSONB | Y | NULL | 校验结果摘要 |
| error_file_url | VARCHAR(500) | Y | NULL | 错误报告 URL |
| started_at | TIMESTAMP | Y | NULL | 开始时间 |
| finished_at | TIMESTAMP | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_member_import_code(code)` 唯一；`idx_mpi_member_import_status(task_status, created_at)`；`idx_mpi_member_import_operator(operator_id, created_at)`。

### 4.11 表：`mpi_member_import_detail`（会员导入明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_id | BIGINT | N | - | 任务 ID |
| row_no | INT | N | - | Excel 行号 |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| gender | VARCHAR(16) | Y | NULL | 性别 |
| birth_date | DATE | Y | NULL | 出生日期 |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码 |
| id_no_mask | VARCHAR(64) | Y | NULL | 证件号掩码 |
| id_no_hash | VARCHAR(128) | Y | NULL | 证件号哈希（用于查患者） |
| level_code | VARCHAR(32) | Y | NULL | 等级代码 |
| source | VARCHAR(32) | Y | NULL | 来源 |
| birthday | DATE | Y | NULL | 生日 |
| row_status | VARCHAR(16) | N | 'PENDING' | PENDING/VALID/WARN/ERROR/SUCCESS/FAILED |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| warn_msg | VARCHAR(1000) | Y | NULL | 警告信息 |
| patient_id | BIGINT | Y | NULL | 匹配到的患者 ID |
| member_id | BIGINT | Y | NULL | 生成的会员 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_mpi_member_import_detail_task(task_id, row_no)`；`idx_mpi_member_import_detail_status(task_id, row_status)`；`idx_mpi_member_import_detail_hash(id_no_hash)`。

### 4.12 表：`mpi_member_code_seq`（会员号序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| prefix | VARCHAR(8) | N | - | 前缀（默认 `M`） |
| period_key | VARCHAR(8) | N | - | 周期键 `yyyyMMdd` |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 6 | 流水位数 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_member_code_seq(prefix, period_key)` 唯一。

**说明：** Redis `INCR` 为主，DB 表用于每日对账；Redis 丢数据时从 `MAX(current_seq)` 恢复。

### 4.13 SQLAlchemy 2.0 模型定义

```python
# app/models/mpi/member.py
"""会员 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Boolean, Date, DateTime,
    Numeric, JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MpiMemberConfig(Base):
    """会员配置（单行）"""
    __tablename__ = "mpi_member_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_no_prefix: Mapped[str] = mapped_column(String(8), default="M", nullable=False)
    member_seq_len: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    allow_manual_member_no: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_level_code: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    open_on_registration: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    open_on_charge: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    level_up_by_m19: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    level_down_by_m19: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    level_down_need_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    benefit_cache_ttl_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    auto_expire_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_expire_days: Mapped[int] = mapped_column(Integer, default=730, nullable=False)
    expire_remind_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    subscribe_patient_merge: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "会员配置（单行）"},
    )


class MpiMemberLevel(Base, TimestampMixin, SoftDeleteMixin):
    """会员等级"""
    __tablename__ = "mpi_member_level"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    level_code: Mapped[str] = mapped_column(String(32), nullable=False)
    level_name: Mapped[str] = mapped_column(String(32), nullable=False)
    level_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    growth_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    consume_threshold: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0, nullable=False)
    upgrade_logic: Mapped[str] = mapped_column(String(8), default="OR", nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    switch_policy: Mapped[str] = mapped_column(String(16), default="BOTH", nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(16))
    icon_url: Mapped[Optional[str]] = mapped_column(String(255))
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    benefits: Mapped[List["MpiMemberLevelBenefit"]] = relationship(
        back_populates="level", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("level_code", "is_deleted", name="uk_mpi_member_level_code"),
        UniqueConstraint("level_seq", "is_deleted", name="uk_mpi_member_level_seq"),
        Index("idx_mpi_member_level_enabled", "is_enabled", "sort_no"),
        {"comment": "会员等级"},
    )

    def meets_upgrade(self, growth_value: Decimal, consume_amount: Decimal) -> bool:
        if self.upgrade_logic == "AND":
            return (growth_value >= self.growth_threshold
                    and consume_amount >= self.consume_threshold)
        return (growth_value >= self.growth_threshold
                or consume_amount >= self.consume_threshold)


class MpiMemberBenefit(Base, TimestampMixin, SoftDeleteMixin):
    """会员权益"""
    __tablename__ = "mpi_member_benefit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    benefit_code: Mapped[str] = mapped_column(String(32), nullable=False)
    benefit_name: Mapped[str] = mapped_column(String(64), nullable=False)
    benefit_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), default="ALL", nullable=False)
    scope_value: Mapped[Optional[str]] = mapped_column(String(500))
    default_value: Mapped[str] = mapped_column(String(64), nullable=False)
    value_unit: Mapped[Optional[str]] = mapped_column(String(16))
    min_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    max_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 4))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("benefit_code", "is_deleted", name="uk_mpi_member_benefit_code"),
        Index("idx_mpi_member_benefit_type", "benefit_type", "is_enabled"),
        Index("idx_mpi_member_benefit_scope", "scope", "is_enabled"),
        {"comment": "会员权益"},
    )


class MpiMemberLevelBenefit(Base):
    """等级-权益关联"""
    __tablename__ = "mpi_member_level_benefit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    level_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    level_code: Mapped[str] = mapped_column(String(32), nullable=False)
    benefit_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    benefit_code: Mapped[str] = mapped_column(String(32), nullable=False)
    benefit_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_value: Mapped[Optional[str]] = mapped_column(String(500))
    override_value: Mapped[Optional[str]] = mapped_column(String(64))
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    level: Mapped["MpiMemberLevel"] = relationship(back_populates="benefits")

    __table_args__ = (
        UniqueConstraint("level_id", "benefit_id", "scope", "scope_value", "is_deleted",
                         name="uk_mpi_level_benefit"),
        Index("idx_mpi_level_benefit_level", "level_id", "is_enabled"),
        Index("idx_mpi_level_benefit_benefit", "benefit_id"),
        {"comment": "等级-权益关联"},
    )


class MpiMemberTag(Base, TimestampMixin, SoftDeleteMixin):
    """会员标签"""
    __tablename__ = "mpi_member_tag"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tag_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_name: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(16), default="MANUAL", nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#999999", nullable=False)
    tag_group: Mapped[Optional[str]] = mapped_column(String(32))
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("tag_code", "is_deleted", name="uk_mpi_member_tag_code"),
        Index("idx_mpi_member_tag_type", "tag_type", "is_enabled"),
        Index("idx_mpi_member_tag_group", "tag_group", "is_enabled"),
        {"comment": "会员标签"},
    )


class MpiMember(Base, TimestampMixin, SoftDeleteMixin):
    """会员主表"""
    __tablename__ = "mpi_member"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_no: Mapped[str] = mapped_column(String(32), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    member_name: Mapped[str] = mapped_column(String(64), nullable=False)
    member_phone_enc: Mapped[Optional[str]] = mapped_column(String(512))
    member_phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    level_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    level_code: Mapped[str] = mapped_column(String(32), nullable=False)
    level_name: Mapped[str] = mapped_column(String(32), nullable=False)
    level_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    status_reason: Mapped[Optional[str]] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_at: Mapped[Optional[date]] = mapped_column(Date)
    frozen_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    tags: Mapped[List["MpiMemberTagRel"]] = relationship(
        back_populates="member", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("member_no", "is_deleted", name="uk_mpi_member_no"),
        Index("idx_mpi_member_level", "level_code", "status"),
        Index("idx_mpi_member_status", "status", "created_at"),
        Index("idx_mpi_member_source", "source", "created_at"),
        Index("idx_mpi_member_name", "member_name"),
        Index("idx_mpi_member_phone", "member_phone_mask"),
        Index("idx_mpi_member_join", "join_date"),
        Index("idx_mpi_member_expire", "expire_at", "status"),
        {"comment": "会员主表"},
    )

    STATUS_LABELS = {
        "ACTIVE": "正常", "FROZEN": "已冻结",
        "EXPIRED": "已过期", "CANCELLED": "已注销",
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def is_benefit_available(self) -> bool:
        return self.status == "ACTIVE"

    def bump_version(self) -> None:
        self.version_no = (self.version_no or 0) + 1


class MpiMemberTagRel(Base):
    """会员-标签关联"""
    __tablename__ = "mpi_member_tag_rel"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tag_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tag_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tag_type: Mapped[str] = mapped_column(String(16), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    member: Mapped["MpiMember"] = relationship(back_populates="tags")

    __table_args__ = (
        UniqueConstraint("member_id", "tag_id", "is_deleted",
                         name="uk_mpi_member_tag_rel"),
        Index("idx_mpi_member_tag_rel_member", "member_id"),
        Index("idx_mpi_member_tag_rel_tag", "tag_id"),
        Index("idx_mpi_member_tag_rel_code", "tag_code"),
        {"comment": "会员-标签关联"},
    )


class MpiMemberLog(Base):
    """会员变更日志"""
    __tablename__ = "mpi_member_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    member_no: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    detail: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_member_log_member", "member_id", "created_at"),
        Index("idx_mpi_member_log_no", "member_no", "created_at"),
        Index("idx_mpi_member_log_action", "action", "created_at"),
        Index("idx_mpi_member_log_operator", "operator_id", "created_at"),
        Index("idx_mpi_member_log_time", "created_at"),
        {"comment": "会员变更日志（月度分区）"},
    )


class MpiMemberImportTask(Base):
    """会员导入任务"""
    __tablename__ = "mpi_member_import_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warn_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_strategy: Mapped[str] = mapped_column(String(16), default="SKIP", nullable=False)
    task_status: Mapped[str] = mapped_column(String(16), default="VALIDATING", nullable=False)
    validate_result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_file_url: Mapped[Optional[str]] = mapped_column(String(500))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cost_ms: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    details: Mapped[List["MpiMemberImportDetail"]] = relationship(
        back_populates="task", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("code", name="uk_mpi_member_import_code"),
        Index("idx_mpi_member_import_status", "task_status", "created_at"),
        Index("idx_mpi_member_import_operator", "operator_id", "created_at"),
        {"comment": "会员导入任务"},
    )


class MpiMemberImportDetail(Base):
    """会员导入明细"""
    __tablename__ = "mpi_member_import_detail"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_no: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    id_no_mask: Mapped[Optional[str]] = mapped_column(String(64))
    id_no_hash: Mapped[Optional[str]] = mapped_column(String(128))
    level_code: Mapped[Optional[str]] = mapped_column(String(32))
    source: Mapped[Optional[str]] = mapped_column(String(32))
    birthday: Mapped[Optional[date]] = mapped_column(Date)
    row_status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    warn_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    patient_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    member_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["MpiMemberImportTask"] = relationship(back_populates="details")

    __table_args__ = (
        Index("idx_mpi_member_import_detail_task", "task_id", "row_no"),
        Index("idx_mpi_member_import_detail_status", "task_id", "row_status"),
        Index("idx_mpi_member_import_detail_hash", "id_no_hash"),
        {"comment": "会员导入明细"},
    )


class MpiMemberCodeSeq(Base):
    """会员号序列（DB 对账）"""
    __tablename__ = "mpi_member_code_seq"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    period_key: Mapped[str] = mapped_column(String(8), nullable=False)
    current_seq: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    seq_width: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("prefix", "period_key", name="uk_mpi_member_code_seq"),
        {"comment": "会员号序列（Redis 为主，DB 对账）"},
    )
```

### 4.14 Pydantic Schema 定义

```python
# app/schemas/mpi/member.py
"""会员 Pydantic Schema"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


MEMBER_STATUS = Literal["ACTIVE", "FROZEN", "EXPIRED", "CANCELLED"]
MEMBER_SOURCE = Literal["OUTPATIENT", "INPATIENT", "OPTOMETRY", "REFRACTIVE",
                          "MINIAPP", "REFERRAL", "IMPORT", "STAFF", "OTHER"]
LEVEL_POLICY = Literal["AUTO", "MANUAL", "BOTH"]
BENEFIT_TYPE = Literal["DISCOUNT", "POINTS_RATE", "FREE_SERVICE",
                        "BIRTHDAY_GIFT", "PRIORITY_BOOKING",
                        "EXCLUSIVE_PRICE", "STORAGE_DISCOUNT", "OTHER"]
BENEFIT_SCOPE = Literal["ALL", "CHARGE_CLASS", "CHARGE_ITEM",
                         "OPTICAL", "REFRACTIVE", "MEMBER_ONLY"]
TAG_TYPE = Literal["MANUAL", "RULE", "SYSTEM"]
CHANGE_OPERATE = Literal["MANUAL", "AUTO"]


# ==================== 查询 ====================
class MemberQuery(BaseModel):
    keyword: Optional[str] = None
    level_code: Optional[List[str]] = None
    status: Optional[List[MEMBER_STATUS]] = None
    source: Optional[List[MEMBER_SOURCE]] = None
    tag_code: Optional[List[str]] = None
    join_from: Optional[date] = None
    join_to: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class MemberTagSchema(BaseModel):
    tag_code: str
    tag_name: str
    color: Optional[str] = None


class MemberListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_no: str
    patient_id: int
    empi_no: Optional[str] = None
    member_name: str
    member_phone_mask: Optional[str] = None
    level_code: str
    level_name: str
    status: str
    source: str
    join_date: date
    tags: List[MemberTagSchema] = []


class MemberBenefitItem(BaseModel):
    benefit_code: str
    benefit_type: str
    scope: str
    scope_value: Optional[str] = None
    value: str
    unit: Optional[str] = None
    description: Optional[str] = None


class MemberDetail(MemberListItem):
    gender: Optional[str] = None
    birthday: Optional[date] = None
    level_id: int
    level_seq: int
    status_reason: Optional[str] = None
    last_active_at: Optional[datetime] = None
    expire_at: Optional[date] = None
    frozen_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    version_no: int = 1
    remark: Optional[str] = None
    benefits: List[MemberBenefitItem] = []


# ==================== 创建/更新 ====================
class MemberCreate(BaseModel):
    patient_id: int
    member_no: Optional[str] = Field(None, max_length=32)
    level_code: str = Field(..., max_length=32)
    source: MEMBER_SOURCE
    join_date: Optional[date] = None
    birthday: Optional[date] = None
    tag_codes: Optional[List[str]] = None
    remark: Optional[str] = Field(None, max_length=500)

    @field_validator("birthday")
    @classmethod
    def validate_birthday(cls, v):
        if v and v > date.today():
            raise ValueError("生日不能晚于今天")
        return v


class MemberUpdate(BaseModel):
    level_code: Optional[str] = Field(None, max_length=32)
    birthday: Optional[date] = None
    expire_at: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=500)
    version_no: int = Field(..., ge=1)


class MemberChangeLevelRequest(BaseModel):
    target_level_code: str = Field(..., max_length=32)
    reason: str = Field(..., min_length=5, max_length=500)
    operate_type: CHANGE_OPERATE = "MANUAL"
    growth_value: Optional[Decimal] = Field(None, ge=0)
    consume_amount: Optional[Decimal] = Field(None, ge=0)


class MemberStatusRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class MemberCancelRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    confirm: bool = False

    @model_validator(mode="after")
    def validate_cancel(self):
        if not self.confirm:
            raise ValueError("注销必须二次确认")
        return self


# ==================== 等级 ====================
class MemberLevelBase(BaseModel):
    level_name: str = Field(..., min_length=1, max_length=32)
    level_seq: int = Field(..., ge=1)
    growth_threshold: Decimal = Field(Decimal("0.00"), ge=0)
    consume_threshold: Decimal = Field(Decimal("0.00"), ge=0)
    upgrade_logic: Literal["OR", "AND"] = "OR"
    is_default: bool = False
    switch_policy: LEVEL_POLICY = "BOTH"
    color: Optional[str] = Field(None, max_length=16)
    icon_url: Optional[str] = Field(None, max_length=255)
    sort_no: int = 999
    description: Optional[str] = Field(None, max_length=500)


class MemberLevelCreate(MemberLevelBase):
    level_code: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]{1,31}$")


class MemberLevelUpdate(MemberLevelBase):
    is_enabled: Optional[bool] = None


class MemberLevelItem(MemberLevelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    level_code: str
    member_count: int = 0
    is_enabled: bool = True


# ==================== 权益 ====================
class MemberBenefitBase(BaseModel):
    benefit_name: str = Field(..., min_length=1, max_length=64)
    benefit_type: BENEFIT_TYPE
    scope: BENEFIT_SCOPE = "ALL"
    scope_value: Optional[str] = Field(None, max_length=500)
    default_value: str = Field(..., min_length=1, max_length=64)
    value_unit: Optional[str] = Field(None, max_length=16)
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    description: Optional[str] = Field(None, max_length=500)
    sort_no: int = 999

    @model_validator(mode="after")
    def validate_benefit(self):
        if self.benefit_type in ("DISCOUNT", "STORAGE_DISCOUNT"):
            try:
                v = Decimal(self.default_value)
            except Exception:
                raise ValueError("折扣类权益默认值必须为数字")
            if not (Decimal("0") <= v <= Decimal("100")):
                raise ValueError("折扣率必须在 0~100 之间")
        elif self.benefit_type == "POINTS_RATE":
            try:
                v = Decimal(self.default_value)
            except Exception:
                raise ValueError("积分倍率默认值必须为数字")
            if v < Decimal("1"):
                raise ValueError("积分倍率必须 ≥ 1")
        # 范围值一致性
        if self.scope == "CHARGE_CLASS" and not self.scope_value:
            raise ValueError("收费类别范围必须填写类别编码")
        if self.scope == "CHARGE_ITEM" and not self.scope_value:
            raise ValueError("指定项目范围必须填写项目编码列表")
        return self


class MemberBenefitCreate(MemberBenefitBase):
    benefit_code: str = Field(..., pattern=r"^BEN-[A-Z]{3,6}-\d{2,4}$")


class MemberBenefitUpdate(MemberBenefitBase):
    is_enabled: Optional[bool] = None


class MemberBenefitItemOut(MemberBenefitBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    benefit_code: str
    is_enabled: bool = True


# ==================== 等级-权益 ====================
class LevelBenefitItem(BaseModel):
    benefit_code: str
    override_value: Optional[str] = Field(None, max_length=64)
    is_enabled: bool = True
    sort_no: int = 999


class LevelBenefitBatchSave(BaseModel):
    items: List[LevelBenefitItem] = Field(..., min_length=0, max_length=200)

    @model_validator(mode="after")
    def validate_unique(self):
        codes = [i.benefit_code for i in self.items]
        if len(codes) != len(set(codes)):
            raise ValueError("权益代码重复")
        return self


# ==================== 标签 ====================
class MemberTagBase(BaseModel):
    tag_name: str = Field(..., min_length=1, max_length=32)
    tag_type: TAG_TYPE = "MANUAL"
    color: str = Field("#999999", max_length=16)
    tag_group: Optional[str] = Field(None, max_length=32)
    description: Optional[str] = Field(None, max_length=500)
    sort_no: int = 999


class MemberTagCreate(MemberTagBase):
    tag_code: str = Field(..., pattern=r"^TAG-[A-Z0-9_]{2,28}$")


class MemberTagUpdate(MemberTagBase):
    is_enabled: Optional[bool] = None


class MemberTagItemOut(MemberTagBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tag_code: str
    member_count: int = 0
    is_enabled: bool = True


class MemberTagAddRequest(BaseModel):
    tag_codes: List[str] = Field(..., min_length=1, max_length=20)


class MemberBatchTagRequest(BaseModel):
    member_ids: List[int] = Field(..., min_length=1, max_length=1000)
    tag_codes: List[str] = Field(..., min_length=1, max_length=20)


# ==================== 配置 ====================
class MemberConfigUpdate(BaseModel):
    member_no_prefix: str = Field("M", max_length=8)
    member_seq_len: int = Field(6, ge=4, le=10)
    allow_manual_member_no: bool = True
    default_level_code: str = Field("NORMAL", max_length=32)
    open_on_registration: bool = True
    open_on_charge: bool = True
    level_up_by_m19: bool = True
    level_down_by_m19: bool = True
    level_down_need_approval: bool = True
    benefit_cache_ttl_seconds: int = Field(300, ge=10, le=3600)
    auto_expire_enabled: bool = True
    auto_expire_days: int = Field(730, ge=30, le=3650)
    expire_remind_days: int = Field(30, ge=1, le=180)
    subscribe_patient_merge: bool = True
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_config(self):
        if self.expire_remind_days >= self.auto_expire_days:
            raise ValueError("过期提醒天数必须小于过期天数")
        return self


class MemberConfigDetail(MemberConfigUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int = 1
    updated_at: Optional[datetime] = None


# ==================== 内部契约 ====================
class MemberBenefitQuery(BaseModel):
    member_id: int
    scope: Optional[str] = None
    scope_value: Optional[str] = None


class MemberBenefitResult(BaseModel):
    member_id: int
    member_no: str
    level_code: str
    level_name: str
    status: str
    benefits: List[MemberBenefitItem] = []


class MemberLevelChangeRequest(BaseModel):
    target_level_code: str = Field(..., max_length=32)
    reason: str = Field(..., min_length=3, max_length=500)
    growth_value: Optional[Decimal] = None
    consume_amount: Optional[Decimal] = None


class MemberLevelChangeResult(BaseModel):
    member_id: int
    old_level_code: str
    new_level_code: str
    changed_at: datetime
    log_id: int


class MemberTagsSyncRequest(BaseModel):
    tag_codes: List[str] = Field(..., max_length=50)
    replace: bool = False


class MergeRedirectRequest(BaseModel):
    merge_id: str = Field(..., max_length=32)
    primary_patient_id: int
    secondary_patient_id: int


class MergeRedirectResult(BaseModel):
    merge_id: str
    secondary_patient_id: int
    member_id: Optional[int] = None
    old_patient_id: Optional[int] = None
    new_patient_id: Optional[int] = None
    status: Literal["REDIRECTED", "NO_MEMBER", "CONFLICT"]
    conflict: bool = False
    primary_member_no: Optional[str] = None


# 前向引用
MemberDetail.model_rebuild()
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：11 张表 | 系统设计组 |