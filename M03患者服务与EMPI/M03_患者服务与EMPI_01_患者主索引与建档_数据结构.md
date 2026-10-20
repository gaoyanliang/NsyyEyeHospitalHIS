# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块数据结构：患者主索引与建档

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 患者主索引与建档（MPI & Registration）
**主数据域：** 患者域（`MPI`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 01 患者主索引与建档 详细设计》《M01 主数据管理MDM》《M02 统一权限与安全》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「患者主索引与建档」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[患者主索引与建档详细设计](M03_患者服务与EMPI_01_患者主索引与建档_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [患者主索引与建档详细设计](M03_患者服务与EMPI_01_患者主索引与建档_详细设计.md)
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md)
- [M01 数据结构设计汇总](../M01主数据管理MDM/M01_主数据管理MDM_数据结构设计汇总.md) — `mdm_department` / `mdm_employee` / `md_dict_item` / `md_dict_type` / `md_sys_param`
- [M02 账号管理数据结构](../M02统一权限与安全/M02_统一权限与安全_01_账号管理_数据结构.md) — `sys_account`
- [M02 审计日志数据结构](../M02统一权限与安全/M02_统一权限与安全_06_审计日志_数据结构.md) — `sys_audit_log`

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 12 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_patient`（患者主索引主表）](#42-表mpi_patient患者主索引主表)
- [4.3 表：`mpi_patient_identifier`（患者证件标识表）](#43-表mpi_patient_identifier患者证件标识表)
- [4.4 表：`mpi_patient_contact`（患者联系方式表）](#44-表mpi_patient_contact患者联系方式表)
- [4.5 表：`mpi_patient_address`（患者地址表）](#45-表mpi_patient_address患者地址表)
- [4.6 表：`mpi_patient_relation`（患者联系人/监护人表）](#46-表mpi_patient_relation患者联系人监护人表)
- [4.7 表：`mpi_patient_consent`（患者授权同意表）](#47-表mpi_patient_consent患者授权同意表)
- [4.8 表：`mpi_patient_log`（患者建档变更日志表）](#48-表mpi_patient_log患者建档变更日志表)
- [4.9 表：`mpi_patient_import_task`（患者导入任务表）](#49-表mpi_patient_import_task患者导入任务表)
- [4.10 表：`mpi_patient_import_detail`（患者导入明细表）](#410-表mpi_patient_import_detail患者导入明细表)
- [4.11 表：`mpi_patient_sync_log`（患者同步日志表）](#411-表mpi_patient_sync_log患者同步日志表)
- [4.12 表：`mpi_patient_code_seq`（EMPI 编码序列表）](#412-表mpi_patient_code_seqempi-编码序列表)
- [4.13 表：`mpi_config`（患者服务配置表）](#413-表mpi_config患者服务配置表)
- [4.14 SQLAlchemy 2.0 模型定义](#414-sqlalchemy-20-模型定义)
- [4.15 Pydantic Schema 定义](#415-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_patient` | 患者主索引主表 |
| 4.3 | `mpi_patient_identifier` | 患者证件标识表 |
| 4.4 | `mpi_patient_contact` | 患者联系方式表 |
| 4.5 | `mpi_patient_address` | 患者地址表 |
| 4.6 | `mpi_patient_relation` | 患者联系人/监护人表 |
| 4.7 | `mpi_patient_consent` | 患者授权同意表 |
| 4.8 | `mpi_patient_log` | 患者建档变更日志表 |
| 4.9 | `mpi_patient_import_task` | 患者导入任务表 |
| 4.10 | `mpi_patient_import_detail` | 患者导入明细表 |
| 4.11 | `mpi_patient_sync_log` | 患者同步日志表 |
| 4.12 | `mpi_patient_code_seq` | EMPI 编码序列表 |
| 4.13 | `mpi_config` | 患者服务配置表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```text
┌──────────────────────────────────────────────────────────────────────┐
│ M01 依赖（逻辑引用，不建物理外键）                                     │
│ mdm_department / mdm_employee / md_dict_item / md_dict_type           │
│ md_sys_param                                                          │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ M02 依赖（逻辑引用）                                                  │
│ sys_account（操作人、患者端账号）                                      │
│ sys_audit_log（敏感查看审计）                                          │
│ sys_mfa_challenge（证件明文查看二次验证）                              │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│ mpi_patient（患者主索引主表）                                          │
│ id / empi_no / patient_name / primary_id_no_hash / status            │
└───────┬──────────────┬──────────────┬──────────────┬─────────────────┘
        │ 1:N          │ 1:N          │ 1:N          │ 1:N
        ▼              ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ mpi_patient_ │ │ mpi_patient_ │ │ mpi_patient_ │ │ mpi_patient_ │
│ identifier   │ │ contact      │ │ address      │ │ relation     │
│ 证件标识     │ │ 联系方式     │ │ 地址         │ │ 联系人/监护人│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
        │ 1:N
        ▼
┌──────────────┐        ┌──────────────────────────────┐
│ mpi_patient_ │        │ mpi_patient_import_task      │
│ consent      │        │ 1:N → mpi_patient_import_detail│
│ 授权同意     │        └──────────────────────────────┘
└──────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_patient_log              │  │ mpi_patient_sync_log         │
│ （建档变更日志，月分区）      │  │ （M03→M01 推送日志，月分区）  │
└──────────────────────────────┘  └──────────────────────────────┘

┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_patient_code_seq         │  │ mpi_config                   │
│ （EMPI 编码序列）             │  │ （患者服务配置，单行）         │
└──────────────────────────────┘  └──────────────────────────────┘
```

**说明：**

- `mpi_patient.id` 为患者唯一主键；`empi_no` 为全院唯一 EMPI 号。
- `primary_id_type + primary_id_no_hash` 部分唯一，保证一主证件一患者。
- 证件号、手机号、联系人电话均存加密值、哈希、掩码三列。
- `mpi_patient_log` / `mpi_patient_sync_log` 按 `created_at` 月度 RANGE 分区。
- 跨模块通过 `patient_id` / `empi_no` 逻辑引用，不建跨模块物理外键。
- M01 的 `md_patient` 是 M01 侧的只读镜像表，**由本模块单向推送**（`POST /internal/v1/mdm/patients/sync`），`mpi_patient_sync_log` 记录每次推送的结果与重试，M01 不主动拉取。

### 4.2 表：`mpi_patient`（患者主索引主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| empi_no | VARCHAR(32) | N | - | 患者主索引号 `P+yyyyMMdd+6位流水` |
| patient_no | VARCHAR(32) | Y | NULL | 患者卡号/病历号（对外展示用） |
| patient_name | VARCHAR(64) | N | - | 患者姓名 |
| name_pinyin | VARCHAR(128) | Y | NULL | 姓名拼音 |
| name_initial | VARCHAR(32) | Y | NULL | 姓名首字母 |
| gender | VARCHAR(16) | N | 'UNKNOWN' | 性别：MALE/FEMALE/UNKNOWN（字典 `GENDER`） |
| birth_date | DATE | Y | NULL | 出生日期 |
| primary_id_type | VARCHAR(32) | Y | NULL | 主证件类型（字典 `ID_TYPE`） |
| primary_id_no_enc | VARCHAR(512) | Y | NULL | 主证件号加密值（AES-256） |
| primary_id_no_hash | VARCHAR(128) | Y | NULL | 主证件号哈希（SHA-256+盐） |
| primary_id_no_mask | VARCHAR(64) | Y | NULL | 主证件号掩码 |
| primary_phone_enc | VARCHAR(512) | Y | NULL | 主手机号加密值 |
| primary_phone_hash | VARCHAR(128) | Y | NULL | 主手机号哈希 |
| primary_phone_mask | VARCHAR(32) | Y | NULL | 主手机号掩码 |
| nation_code | VARCHAR(32) | Y | NULL | 民族代码（字典 `NATION`） |
| marital_status | VARCHAR(32) | Y | NULL | 婚姻状态（字典 `MARITAL_STATUS`） |
| education_code | VARCHAR(32) | Y | NULL | 学历代码（字典 `EDUCATION`） |
| occupation_code | VARCHAR(32) | Y | NULL | 职业代码（字典 `OCCUPATION`） |
| patient_type | VARCHAR(32) | N | 'NORMAL' | 患者类型（字典 `PATIENT_TYPE`） |
| patient_source | VARCHAR(32) | Y | NULL | 患者来源（字典 `PATIENT_SOURCE`） |
| allergy_history | VARCHAR(500) | Y | NULL | 过敏史（供 M04/M07 用药警示） |
| status | VARCHAR(16) | N | 'NORMAL' | 患者状态：NORMAL/FROZEN/DECEASED/MERGED |
| status_reason | VARCHAR(500) | Y | NULL | 状态原因 |
| merge_to_id | BIGINT | Y | NULL | 合并目标患者 ID（M03-02 使用） |
| quality_score | SMALLINT | N | 0 | 基础完整度评分 0~100 |
| first_visit_at | TIMESTAMP | Y | NULL | 首次就诊时间 |
| last_visit_at | TIMESTAMP | Y | NULL | 最后就诊时间 |
| deceased_at | TIMESTAMP | Y | NULL | 死亡时间 |
| sync_version | INT | N | 1 | 同步版本号（M01 据此判新旧，防乱序覆盖） |
| version_no | INT | N | 1 | 乐观锁版本号 |
| org_id | BIGINT | N | 1 | 院区 ID |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT | Y | NULL | 创建人（M02 `sys_account.id`） |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient | PRIMARY | id | 主键 |
| uk_mpi_patient_empi_no | UNIQUE | empi_no | EMPI 唯一 |
| uk_mpi_patient_primary_id_hash | UNIQUE(PARTIAL) | primary_id_type, primary_id_no_hash | 主证件唯一 |
| uk_mpi_patient_no | UNIQUE(PARTIAL) | patient_no | 患者卡号唯一 |
| idx_mpi_patient_name_pinyin | NORMAL | name_pinyin | 拼音检索 |
| idx_mpi_patient_name_birth | NORMAL | patient_name, birth_date | 辅助检索 |
| idx_mpi_patient_phone_hash | NORMAL | primary_phone_hash | 手机号哈希检索 |
| idx_mpi_patient_status | NORMAL | status, created_at | 状态列表 |
| idx_mpi_patient_created | NORMAL | created_at | 建档时间 |
| idx_mpi_patient_last_visit | NORMAL | last_visit_at | 最近就诊 |
| idx_mpi_patient_sync | NORMAL | sync_version | 推送对账 |

**约束说明**

```sql
-- 主证件唯一（仅对非空生效）
CREATE UNIQUE INDEX uk_mpi_patient_primary_id_hash
    ON mpi_patient (primary_id_type, primary_id_no_hash)
    WHERE primary_id_no_hash IS NOT NULL AND is_deleted = FALSE;

-- 患者卡号唯一（仅对非空生效）
CREATE UNIQUE INDEX uk_mpi_patient_no
    ON mpi_patient (patient_no)
    WHERE patient_no IS NOT NULL AND is_deleted = FALSE;

-- 性别
ALTER TABLE mpi_patient
    ADD CONSTRAINT ck_mpi_patient_gender
    CHECK (gender IN ('MALE', 'FEMALE', 'UNKNOWN'));

-- 状态
ALTER TABLE mpi_patient
    ADD CONSTRAINT ck_mpi_patient_status
    CHECK (status IN ('NORMAL', 'FROZEN', 'DECEASED', 'MERGED'));

-- 完整度
ALTER TABLE mpi_patient
    ADD CONSTRAINT ck_mpi_patient_quality
    CHECK (quality_score BETWEEN 0 AND 100);
```

**字段说明补充：**

- `patient_no` 可选，若医院有独立患者卡号可启用；为空时仅用 `empi_no` 对外。
- `primary_id_no_enc` 使用 AES-256-GCM 加密，密钥来自配置中心；`primary_id_no_hash` 为 SHA-256(salt + 证件号)。
- `allergy_history` 冗余在患者主表，供 M04/M07 高频读取；明细由 M18 过敏史模块维护，变更时通过事件更新。
- `sync_version` 每次写操作 +1，本模块推送时随请求带上，M01 据此做 UPSERT 判断，防止乱序覆盖。
- `status=MERGED` 时，所有业务读取应跳转 `merge_to_id`。

**分区：** 不分区（患者总量 ≤ 50 万，索引可支撑）。

### 4.3 表：`mpi_patient_identifier`（患者证件标识表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | N | - | EMPI（冗余） |
| id_type | VARCHAR(32) | N | - | 证件类型（字典 `ID_TYPE`） |
| id_no_enc | VARCHAR(512) | N | - | 证件号加密值 |
| id_no_hash | VARCHAR(128) | N | - | 证件号哈希 |
| id_no_mask | VARCHAR(64) | Y | NULL | 证件号掩码 |
| is_primary | BOOLEAN | N | FALSE | 是否主证件 |
| verified | BOOLEAN | N | FALSE | 是否核验 |
| verified_at | TIMESTAMP | Y | NULL | 核验时间 |
| verified_by | BIGINT | Y | NULL | 核验人（M02 `sys_account.id`） |
| source | VARCHAR(32) | Y | NULL | 来源（字典 `PATIENT_SOURCE`） |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/INACTIVE |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_identifier | PRIMARY | id | 主键 |
| uk_mpi_identifier_type_hash | UNIQUE(PARTIAL) | id_type, id_no_hash | 有效证件唯一 |
| uk_mpi_identifier_primary | UNIQUE(PARTIAL) | patient_id | 每患者仅一个主证件 |
| idx_mpi_identifier_patient | NORMAL | patient_id | 患者证件列表 |
| idx_mpi_identifier_hash | NORMAL | id_no_hash | 哈希检索 |

**约束说明**

```sql
-- 有效证件唯一
CREATE UNIQUE INDEX uk_mpi_identifier_type_hash
    ON mpi_patient_identifier (id_type, id_no_hash)
    WHERE status = 'ACTIVE' AND is_deleted = FALSE;

-- 每患者仅一个主证件
CREATE UNIQUE INDEX uk_mpi_identifier_primary
    ON mpi_patient_identifier (patient_id)
    WHERE is_primary = TRUE AND status = 'ACTIVE' AND is_deleted = FALSE;

ALTER TABLE mpi_patient_identifier
    ADD CONSTRAINT ck_mpi_identifier_status
    CHECK (status IN ('ACTIVE', 'INACTIVE'));
```

**分区：** 不分区。

### 4.4 表：`mpi_patient_contact`（患者联系方式表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | N | - | EMPI（冗余） |
| contact_type | VARCHAR(32) | N | - | 类型（字典 `CONTACT_TYPE`）：MOBILE/TEL/EMAIL/WECHAT/OTHER |
| contact_value_enc | VARCHAR(512) | N | - | 联系方式加密值 |
| contact_value_hash | VARCHAR(128) | N | - | 联系方式哈希 |
| contact_value_mask | VARCHAR(64) | Y | NULL | 掩码 |
| is_primary | BOOLEAN | N | FALSE | 是否主联系方式 |
| is_verified | BOOLEAN | N | FALSE | 是否已验证 |
| verified_at | TIMESTAMP | Y | NULL | 验证时间 |
| source | VARCHAR(32) | Y | NULL | 来源 |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/INACTIVE |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_contact | PRIMARY | id | 主键 |
| uk_mpi_contact_primary | UNIQUE(PARTIAL) | patient_id, contact_type | 每类型一个主联系方式 |
| idx_mpi_contact_patient | NORMAL | patient_id | 患者联系方式 |
| idx_mpi_contact_hash | NORMAL | contact_value_hash | 手机号哈希检索 |

**约束说明**

```sql
CREATE UNIQUE INDEX uk_mpi_contact_primary
    ON mpi_patient_contact (patient_id, contact_type)
    WHERE is_primary = TRUE AND status = 'ACTIVE' AND is_deleted = FALSE;

ALTER TABLE mpi_patient_contact
    ADD CONSTRAINT ck_mpi_contact_type
    CHECK (contact_type IN ('MOBILE', 'TEL', 'EMAIL', 'WECHAT', 'OTHER'));

ALTER TABLE mpi_patient_contact
    ADD CONSTRAINT ck_mpi_contact_status
    CHECK (status IN ('ACTIVE', 'INACTIVE'));
```

**分区：** 不分区。

### 4.5 表：`mpi_patient_address`（患者地址表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | N | - | EMPI（冗余） |
| address_type | VARCHAR(32) | N | - | 地址类型（字典 `ADDRESS_TYPE`）：HOME/WORK/BILLING/OTHER |
| province_code | VARCHAR(32) | Y | NULL | 省代码（M01 行政区划字典） |
| city_code | VARCHAR(32) | Y | NULL | 市代码 |
| district_code | VARCHAR(32) | Y | NULL | 区县代码 |
| address_detail | VARCHAR(500) | Y | NULL | 详细地址 |
| postal_code | VARCHAR(16) | Y | NULL | 邮编 |
| is_primary | BOOLEAN | N | FALSE | 是否主地址 |
| source | VARCHAR(32) | Y | NULL | 来源 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_address | PRIMARY | id | 主键 |
| uk_mpi_address_primary | UNIQUE(PARTIAL) | patient_id, address_type | 每类型一个主地址 |
| idx_mpi_address_patient | NORMAL | patient_id | 患者地址列表 |

**约束说明**

```sql
CREATE UNIQUE INDEX uk_mpi_address_primary
    ON mpi_patient_address (patient_id, address_type)
    WHERE is_primary = TRUE AND is_deleted = FALSE;

ALTER TABLE mpi_patient_address
    ADD CONSTRAINT ck_mpi_address_type
    CHECK (address_type IN ('HOME', 'WORK', 'BILLING', 'OTHER'));
```

**分区：** 不分区。

### 4.6 表：`mpi_patient_relation`（患者联系人/监护人表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | N | - | EMPI（冗余） |
| relation_type | VARCHAR(32) | N | - | 关系（字典 `RELATION`）：SELF/SPOUSE/CHILD/PARENT/SIBLING/OTHER |
| relation_name | VARCHAR(64) | N | - | 联系人姓名 |
| relation_phone_enc | VARCHAR(512) | Y | NULL | 联系人电话加密值 |
| relation_phone_hash | VARCHAR(128) | Y | NULL | 联系人电话哈希 |
| relation_phone_mask | VARCHAR(32) | Y | NULL | 联系人电话掩码 |
| is_legal_guardian | BOOLEAN | N | FALSE | 是否法定监护人 |
| is_emergency | BOOLEAN | N | FALSE | 是否紧急联系人 |
| is_primary | BOOLEAN | N | FALSE | 是否主要联系人 |
| source | VARCHAR(32) | Y | NULL | 来源 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_relation | PRIMARY | id | 主键 |
| uk_mpi_relation_primary | UNIQUE(PARTIAL) | patient_id | 每患者仅一个主要联系人 |
| idx_mpi_relation_patient | NORMAL | patient_id | 患者联系人列表 |
| idx_mpi_relation_guardian | NORMAL | patient_id, is_legal_guardian | 监护人查询 |
| idx_mpi_relation_phone | NORMAL | relation_phone_hash | 电话检索 |

**约束说明**

```sql
CREATE UNIQUE INDEX uk_mpi_relation_primary
    ON mpi_patient_relation (patient_id)
    WHERE is_primary = TRUE AND is_deleted = FALSE;

ALTER TABLE mpi_patient_relation
    ADD CONSTRAINT ck_mpi_relation_type
    CHECK (relation_type IN ('SELF', 'SPOUSE', 'CHILD', 'PARENT', 'SIBLING', 'OTHER'));

ALTER TABLE mpi_patient_relation
    ADD CONSTRAINT ck_mpi_relation_guardian
    CHECK (NOT is_legal_guardian OR relation_type <> 'SELF');
```

**说明：** 法定监护人不能是自己；未成年人建档时建议至少有一个 `is_legal_guardian=true` 的联系人。

**分区：** 不分区。

### 4.7 表：`mpi_patient_consent`（患者授权同意表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | N | - | EMPI（冗余） |
| consent_type | VARCHAR(32) | N | - | 授权类型（字典 `CONSENT_TYPE`）：PRIVACY/TREATMENT/MARKETING/DATA_SHARE |
| consent_version | VARCHAR(32) | N | - | 授权版本（如 v1.0） |
| consent_status | VARCHAR(16) | N | - | 状态：GRANTED/REFUSED/WITHDRAWN |
| consent_text | VARCHAR(2000) | Y | NULL | 授权文本快照（可选） |
| signed_at | TIMESTAMP | Y | NULL | 签署时间 |
| signed_by | BIGINT | Y | NULL | 签署人（M02 `sys_account.id`） |
| signed_channel | VARCHAR(32) | Y | NULL | 渠道（门诊/住院/门户/自助机） |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL=长期） |
| withdraw_at | TIMESTAMP | Y | NULL | 撤回时间 |
| withdraw_by | BIGINT | Y | NULL | 撤回人 |
| withdraw_reason | VARCHAR(500) | Y | NULL | 撤回原因 |
| evidence_url | VARCHAR(500) | Y | NULL | 证据文件 URL |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_consent | PRIMARY | id | 主键 |
| idx_mpi_consent_patient | NORMAL | patient_id, consent_type | 患者授权列表 |
| idx_mpi_consent_status | NORMAL | patient_id, consent_type, consent_status | 按状态查 |
| idx_mpi_consent_current | NORMAL | patient_id, consent_type, signed_at | 最新授权 |

**约束说明**

```sql
ALTER TABLE mpi_patient_consent
    ADD CONSTRAINT ck_mpi_consent_type
    CHECK (consent_type IN ('PRIVACY', 'TREATMENT', 'MARKETING', 'DATA_SHARE'));

ALTER TABLE mpi_patient_consent
    ADD CONSTRAINT ck_mpi_consent_status
    CHECK (consent_status IN ('GRANTED', 'REFUSED', 'WITHDRAWN'));

-- 撤回必须有时间和原因
ALTER TABLE mpi_patient_consent
    ADD CONSTRAINT ck_mpi_consent_withdraw
    CHECK (consent_status <> 'WITHDRAWN' OR (withdraw_at IS NOT NULL));
```

**说明：**

- 同一 `patient_id + consent_type` 每次签署/撤回都**新增一条记录**，不覆盖历史。
- 读取“当前授权状态”取 `signed_at DESC` 第一条且未撤回的记录。
- `MARKETING` 未签署时按“拒绝”处理（M01 参数 `MPI.CONSENT.MARKETING_DEFAULT`）。

**分区：** 不分区。

### 4.8 表：`mpi_patient_log`（患者建档变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI（冗余） |
| action | VARCHAR(32) | N | - | 动作（见下表） |
| before_json | JSONB | Y | NULL | 变更前快照 |
| after_json | JSONB | Y | NULL | 变更后快照 |
| diff_fields | VARCHAR(2000) | Y | NULL | 变更字段列表 |
| detail | VARCHAR(1000) | Y | NULL | 操作详情/原因 |
| operator_id | BIGINT | Y | NULL | 操作人（M02 `sys_account.id`） |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| user_agent | VARCHAR(255) | Y | NULL | 终端 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_patient_log | PRIMARY | id | 主键 |
| idx_mpi_log_patient | NORMAL | patient_id, created_at | 按患者 |
| idx_mpi_log_empi | NORMAL | empi_no, created_at | 按 EMPI |
| idx_mpi_log_action | NORMAL | action, created_at | 按动作 |
| idx_mpi_log_operator | NORMAL | operator_id, created_at | 按操作人 |
| idx_mpi_log_time | NORMAL | created_at | 时间范围 |

**动作类型（`action`）：**

| 代码 | 说明 |
|---|---|
| `CREATE` | 创建患者 |
| `UPDATE` | 修改主档 |
| `IDENTIFIER_ADD` | 添加证件 |
| `IDENTIFIER_UPDATE` | 修改证件 |
| `IDENTIFIER_DELETE` | 删除证件 |
| `CONTACT_ADD` | 添加联系方式 |
| `CONTACT_UPDATE` | 修改联系方式 |
| `CONTACT_DELETE` | 删除联系方式 |
| `ADDRESS_ADD` | 添加地址 |
| `ADDRESS_UPDATE` | 修改地址 |
| `ADDRESS_DELETE` | 删除地址 |
| `RELATION_ADD` | 添加联系人 |
| `RELATION_UPDATE` | 修改联系人 |
| `RELATION_DELETE` | 删除联系人 |
| `CONSENT_GRANT` | 签署授权 |
| `CONSENT_WITHDRAW` | 撤回授权 |
| `FREEZE` | 冻结 |
| `UNFREEZE` | 解冻 |
| `DECEASED` | 死亡登记 |
| `MERGE` | 合并（M03-02） |
| `SPLIT` | 拆分（M03-02） |
| `IMPORT` | 批量导入 |
| `SENSITIVE_VIEW` | 敏感字段查看 |

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**（符合病历档案管理要求）。

### 4.9 表：`mpi_patient_import_task`（患者导入任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| code | VARCHAR(32) | N | - | 任务号 `PI+年月日+流水` |
| file_name | VARCHAR(255) | N | - | 文件名 |
| file_url | VARCHAR(500) | Y | NULL | 文件 URL |
| file_size | BIGINT | Y | NULL | 文件大小 |
| total_rows | INT | N | 0 | 总行数 |
| valid_rows | INT | N | 0 | 校验通过行数 |
| warn_rows | INT | N | 0 | 警告行数 |
| error_rows | INT | N | 0 | 错误行数 |
| success_rows | INT | N | 0 | 成功导入行数 |
| fail_rows | INT | N | 0 | 失败行数 |
| error_strategy | VARCHAR(16) | N | 'SKIP' | 错误策略：SKIP/ABORT |
| task_status | VARCHAR(16) | N | 'VALIDATING' | 状态：VALIDATING/VALIDATED/IMPORTING/SUCCESS/PARTIAL/FAILED/CANCELLED |
| validate_result | JSONB | Y | NULL | 校验结果摘要 |
| error_file_url | VARCHAR(500) | Y | NULL | 错误报告 URL |
| started_at | TIMESTAMP | Y | NULL | 开始时间 |
| finished_at | TIMESTAMP | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_import_code(code)` 唯一；`idx_mpi_import_status(task_status, created_at)`；`idx_mpi_import_operator(operator_id, created_at)`。

### 4.10 表：`mpi_patient_import_detail`（患者导入明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_id | BIGINT | N | - | 任务 ID |
| row_no | INT | N | - | Excel 行号 |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| gender | VARCHAR(16) | Y | NULL | 性别 |
| birth_date | DATE | Y | NULL | 出生日期 |
| id_type | VARCHAR(32) | Y | NULL | 证件类型 |
| id_no_mask | VARCHAR(64) | Y | NULL | 证件号掩码 |
| id_no_hash | VARCHAR(128) | Y | NULL | 证件号哈希（用于查重） |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码 |
| patient_type | VARCHAR(32) | Y | NULL | 患者类型 |
| patient_source | VARCHAR(32) | Y | NULL | 来源 |
| row_status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/VALID/WARN/ERROR/SUCCESS/FAILED |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| warn_msg | VARCHAR(1000) | Y | NULL | 警告信息 |
| patient_id | BIGINT | Y | NULL | 生成的患者 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_mpi_import_detail_task(task_id, row_no)`；`idx_mpi_import_detail_status(task_id, row_status)`；`idx_mpi_import_detail_hash(id_no_hash)`。

### 4.11 表：`mpi_patient_sync_log`（患者同步日志表）

用于记录本模块向 M01 `md_patient` 的**推送**结果：每次建档/修改/合并后由推送任务投递到 `POST /internal/v1/mdm/patients/sync`，本表留存投递状态、重试次数与失败原因，供问题排查与失败重投。M01 不主动拉取。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| sync_action | VARCHAR(16) | N | - | CREATE/UPDATE/DELETE |
| sync_version | INT | N | - | 变更时的 sync_version |
| target_system | VARCHAR(32) | N | 'M01' | 目标系统 |
| changed_fields | VARCHAR(2000) | Y | NULL | 变更字段 |
| payload_json | JSONB | Y | NULL | 推送内容摘要 |
| sync_status | VARCHAR(16) | N | 'PENDING' | PENDING/SUCCESS/FAILED |
| retry_count | INT | N | 0 | 重试次数 |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| delivered_at | TIMESTAMP | Y | NULL | 投递时间 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_mpi_sync_patient(patient_id, created_at)`；`idx_mpi_sync_version(sync_version)`；`idx_mpi_sync_status(sync_status, created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **1 年**。

### 4.12 表：`mpi_patient_code_seq`（EMPI 编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| prefix | VARCHAR(8) | N | - | 前缀（默认 `P`） |
| period_key | VARCHAR(8) | N | - | 周期键 `yyyyMMdd` |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 6 | 流水位数 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_code_seq(prefix, period_key)` 唯一。

**说明：** Redis `INCR` 为主，DB 表用于每日对账；Redis 丢数据时从 `MAX(current_seq)` 恢复。

### 4.13 表：`mpi_config`（患者服务配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| empi_prefix | VARCHAR(8) | N | 'P' | EMPI 前缀（覆盖 M01 参数） |
| empi_seq_width | INT | N | 6 | EMPI 流水位数 |
| import_max_rows | INT | N | 500 | 导入最大行数 |
| export_max_rows | INT | N | 5000 | 导出最大行数 |
| sensitive_view_ttl_seconds | INT | N | 300 | 证件明文查看有效期 |
| min_quality_score | SMALLINT | N | 60 | 最低完整度提醒阈值 |
| marketing_default | VARCHAR(16) | N | 'REFUSED' | 营销默认状态 |
| patient_no_enabled | BOOLEAN | N | FALSE | 是否启用独立患者卡号 |
| log_retain_years | INT | N | 5 | 日志保留年数 |
| sync_batch_size | INT | N | 500 | 同步批次大小 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_mpi_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_config
    ADD CONSTRAINT ck_mpi_config_single_row CHECK (id = 1);

ALTER TABLE mpi_config
    ADD CONSTRAINT ck_mpi_marketing_default
    CHECK (marketing_default IN ('GRANTED', 'REFUSED'));
```

### 4.14 SQLAlchemy 2.0 模型定义

```python
# app/models/mpi/patient.py
"""患者主索引与建档 ORM 模型"""
from datetime import date, datetime
from typing import Optional, List
import hashlib

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Boolean, Date, DateTime,
    JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MpiPatient(Base, TimestampMixin, SoftDeleteMixin):
    """患者主索引主表"""
    __tablename__ = "mpi_patient"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False, comment="患者主索引号")
    patient_no: Mapped[Optional[str]] = mapped_column(String(32), comment="患者卡号/病历号")

    patient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    name_pinyin: Mapped[Optional[str]] = mapped_column(String(128))
    name_initial: Mapped[Optional[str]] = mapped_column(String(32))
    gender: Mapped[str] = mapped_column(String(16), default="UNKNOWN", nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)

    primary_id_type: Mapped[Optional[str]] = mapped_column(String(32))
    primary_id_no_enc: Mapped[Optional[str]] = mapped_column(String(512), comment="加密存储")
    primary_id_no_hash: Mapped[Optional[str]] = mapped_column(String(128))
    primary_id_no_mask: Mapped[Optional[str]] = mapped_column(String(64))

    primary_phone_enc: Mapped[Optional[str]] = mapped_column(String(512))
    primary_phone_hash: Mapped[Optional[str]] = mapped_column(String(128))
    primary_phone_mask: Mapped[Optional[str]] = mapped_column(String(32))

    nation_code: Mapped[Optional[str]] = mapped_column(String(32))
    marital_status: Mapped[Optional[str]] = mapped_column(String(32))
    education_code: Mapped[Optional[str]] = mapped_column(String(32))
    occupation_code: Mapped[Optional[str]] = mapped_column(String(32))

    patient_type: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    patient_source: Mapped[Optional[str]] = mapped_column(String(32))
    allergy_history: Mapped[Optional[str]] = mapped_column(String(500))

    status: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    status_reason: Mapped[Optional[str]] = mapped_column(String(500))
    merge_to_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="M03-02 合并目标")

    quality_score: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    first_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_visit_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deceased_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    sync_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    identifiers: Mapped[List["MpiPatientIdentifier"]] = relationship(
        back_populates="patient", lazy="selectin")
    contacts: Mapped[List["MpiPatientContact"]] = relationship(
        back_populates="patient", lazy="selectin")
    addresses: Mapped[List["MpiPatientAddress"]] = relationship(
        back_populates="patient", lazy="selectin")
    relations: Mapped[List["MpiPatientRelation"]] = relationship(
        back_populates="patient", lazy="selectin")
    consents: Mapped[List["MpiPatientConsent"]] = relationship(
        back_populates="patient", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("empi_no", name="uk_mpi_patient_empi_no"),
        Index("idx_mpi_patient_name_pinyin", "name_pinyin"),
        Index("idx_mpi_patient_name_birth", "patient_name", "birth_date"),
        Index("idx_mpi_patient_phone_hash", "primary_phone_hash"),
        Index("idx_mpi_patient_status", "status", "created_at"),
        Index("idx_mpi_patient_created", "created_at"),
        Index("idx_mpi_patient_last_visit", "last_visit_at"),
        Index("idx_mpi_patient_sync", "sync_version"),
        {"comment": "患者主索引主表"},
    )

    STATUS_LABELS = {
        "NORMAL": "正常", "FROZEN": "已冻结",
        "DECEASED": "已死亡", "MERGED": "已合并",
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def is_business_usable(self) -> bool:
        """是否可被业务引用"""
        return self.status == "NORMAL"

    def bump_sync_version(self) -> None:
        self.sync_version = (self.sync_version or 0) + 1

    def to_brief(self) -> dict:
        age = None
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return {
            "patient_id": self.id,
            "empi_no": self.empi_no,
            "patient_name": self.patient_name,
            "gender": self.gender,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "age": age,
            "primary_id_type": self.primary_id_type,
            "primary_id_mask": self.primary_id_no_mask,
            "primary_phone_mask": self.primary_phone_mask,
            "patient_type": self.patient_type,
            "status": self.status,
            "allergy_history": self.allergy_history,
        }


class MpiPatientIdentifier(Base, SoftDeleteMixin):
    """患者证件标识"""
    __tablename__ = "mpi_patient_identifier"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False)
    id_type: Mapped[str] = mapped_column(String(32), nullable=False)
    id_no_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    id_no_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    id_no_mask: Mapped[Optional[str]] = mapped_column(String(64))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    source: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["MpiPatient"] = relationship(back_populates="identifiers")

    __table_args__ = (
        Index("idx_mpi_identifier_patient", "patient_id"),
        Index("idx_mpi_identifier_hash", "id_no_hash"),
        {"comment": "患者证件标识"},
    )


class MpiPatientContact(Base, SoftDeleteMixin):
    """患者联系方式"""
    __tablename__ = "mpi_patient_contact"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False)
    contact_type: Mapped[str] = mapped_column(String(32), nullable=False)
    contact_value_enc: Mapped[str] = mapped_column(String(512), nullable=False)
    contact_value_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_value_mask: Mapped[Optional[str]] = mapped_column(String(64))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["MpiPatient"] = relationship(back_populates="contacts")

    __table_args__ = (
        Index("idx_mpi_contact_patient", "patient_id"),
        Index("idx_mpi_contact_hash", "contact_value_hash"),
        {"comment": "患者联系方式"},
    )


class MpiPatientAddress(Base, SoftDeleteMixin):
    """患者地址"""
    __tablename__ = "mpi_patient_address"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False)
    address_type: Mapped[str] = mapped_column(String(32), nullable=False)
    province_code: Mapped[Optional[str]] = mapped_column(String(32))
    city_code: Mapped[Optional[str]] = mapped_column(String(32))
    district_code: Mapped[Optional[str]] = mapped_column(String(32))
    address_detail: Mapped[Optional[str]] = mapped_column(String(500))
    postal_code: Mapped[Optional[str]] = mapped_column(String(16))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(32))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["MpiPatient"] = relationship(back_populates="addresses")

    __table_args__ = (
        Index("idx_mpi_address_patient", "patient_id"),
        {"comment": "患者地址"},
    )


class MpiPatientRelation(Base, SoftDeleteMixin):
    """患者联系人/监护人"""
    __tablename__ = "mpi_patient_relation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    relation_name: Mapped[str] = mapped_column(String(64), nullable=False)
    relation_phone_enc: Mapped[Optional[str]] = mapped_column(String(512))
    relation_phone_hash: Mapped[Optional[str]] = mapped_column(String(128))
    relation_phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    is_legal_guardian: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(32))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["MpiPatient"] = relationship(back_populates="relations")

    __table_args__ = (
        Index("idx_mpi_relation_patient", "patient_id"),
        Index("idx_mpi_relation_guardian", "patient_id", "is_legal_guardian"),
        Index("idx_mpi_relation_phone", "relation_phone_hash"),
        {"comment": "患者联系人/监护人"},
    )


class MpiPatientConsent(Base, SoftDeleteMixin):
    """患者授权同意"""
    __tablename__ = "mpi_patient_consent"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=False)
    consent_status: Mapped[str] = mapped_column(String(16), nullable=False)
    consent_text: Mapped[Optional[str]] = mapped_column(String(2000))
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    signed_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    signed_channel: Mapped[Optional[str]] = mapped_column(String(32))
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    withdraw_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    withdraw_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    withdraw_reason: Mapped[Optional[str]] = mapped_column(String(500))
    evidence_url: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["MpiPatient"] = relationship(back_populates="consents")

    __table_args__ = (
        Index("idx_mpi_consent_patient", "patient_id", "consent_type"),
        Index("idx_mpi_consent_status", "patient_id", "consent_type", "consent_status"),
        Index("idx_mpi_consent_current", "patient_id", "consent_type", "signed_at"),
        {"comment": "患者授权同意"},
    )

    @property
    def is_active(self) -> bool:
        return self.consent_status == "GRANTED" and self.withdraw_at is None


class MpiPatientLog(Base):
    """患者建档变更日志"""
    __tablename__ = "mpi_patient_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    after_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    diff_fields: Mapped[Optional[str]] = mapped_column(String(2000))
    detail: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_log_patient", "patient_id", "created_at"),
        Index("idx_mpi_log_empi", "empi_no", "created_at"),
        Index("idx_mpi_log_action", "action", "created_at"),
        Index("idx_mpi_log_operator", "operator_id", "created_at"),
        Index("idx_mpi_log_time", "created_at"),
        {"comment": "患者建档变更日志（月度分区）"},
    )


class MpiPatientSyncLog(Base):
    """患者同步日志（M03 → M01 推送结果）"""
    __tablename__ = "mpi_patient_sync_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    sync_action: Mapped[str] = mapped_column(String(16), nullable=False)
    sync_version: Mapped[int] = mapped_column(Integer, nullable=False)
    target_system: Mapped[str] = mapped_column(String(32), default="M01", nullable=False)
    changed_fields: Mapped[Optional[str]] = mapped_column(String(2000))
    payload_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    sync_status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_sync_patient", "patient_id", "created_at"),
        Index("idx_mpi_sync_version", "sync_version"),
        Index("idx_mpi_sync_status", "sync_status", "created_at"),
        {"comment": "患者同步日志（月度分区）"},
    )


class MpiPatientImportTask(Base):
    """患者导入任务"""
    __tablename__ = "mpi_patient_import_task"

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

    details: Mapped[List["MpiPatientImportDetail"]] = relationship(
        back_populates="task", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("code", name="uk_mpi_import_code"),
        Index("idx_mpi_import_status", "task_status", "created_at"),
        Index("idx_mpi_import_operator", "operator_id", "created_at"),
        {"comment": "患者导入任务"},
    )


class MpiPatientImportDetail(Base):
    """患者导入明细"""
    __tablename__ = "mpi_patient_import_detail"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_no: Mapped[int] = mapped_column(Integer, nullable=False)
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    gender: Mapped[Optional[str]] = mapped_column(String(16))
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    id_type: Mapped[Optional[str]] = mapped_column(String(32))
    id_no_mask: Mapped[Optional[str]] = mapped_column(String(64))
    id_no_hash: Mapped[Optional[str]] = mapped_column(String(128))
    phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    patient_type: Mapped[Optional[str]] = mapped_column(String(32))
    patient_source: Mapped[Optional[str]] = mapped_column(String(32))
    row_status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    warn_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    patient_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    task: Mapped["MpiPatientImportTask"] = relationship(back_populates="details")

    __table_args__ = (
        Index("idx_mpi_import_detail_task", "task_id", "row_no"),
        Index("idx_mpi_import_detail_status", "task_id", "row_status"),
        Index("idx_mpi_import_detail_hash", "id_no_hash"),
        {"comment": "患者导入明细"},
    )


class MpiPatientCodeSeq(Base):
    """EMPI 编码序列（DB 对账）"""
    __tablename__ = "mpi_patient_code_seq"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    prefix: Mapped[str] = mapped_column(String(8), nullable=False)
    period_key: Mapped[str] = mapped_column(String(8), nullable=False)
    current_seq: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    seq_width: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("prefix", "period_key", name="uk_mpi_code_seq"),
        {"comment": "EMPI 编码序列（Redis 为主，DB 对账）"},
    )


class MpiConfig(Base):
    """患者服务配置（单行）"""
    __tablename__ = "mpi_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    empi_prefix: Mapped[str] = mapped_column(String(8), default="P", nullable=False)
    empi_seq_width: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    import_max_rows: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    export_max_rows: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
    sensitive_view_ttl_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    min_quality_score: Mapped[int] = mapped_column(SmallInteger, default=60, nullable=False)
    marketing_default: Mapped[str] = mapped_column(String(16), default="REFUSED", nullable=False)
    patient_no_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    log_retain_years: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    sync_batch_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "患者服务配置（单行）"},
    )
```

### 4.15 Pydantic Schema 定义

```python
# app/schemas/mpi/patient.py
"""患者主索引与建档 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional, List, Literal
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


GENDER = Literal["MALE", "FEMALE", "UNKNOWN"]
PATIENT_STATUS = Literal["NORMAL", "FROZEN", "DECEASED", "MERGED"]
PATIENT_TYPE = Literal["NORMAL", "VIP", "EXTERNAL", "STAFF_FAMILY"]
PATIENT_SOURCE = Literal["OUTPATIENT", "INPATIENT", "OPTOMETRY", "REFRACTIVE",
                          "MINIAPP", "SELF_MACHINE", "REFERRAL", "IMPORT"]
ID_TYPE = Literal["ID_CARD", "PASSPORT", "HK_MO_TW", "MILITARY",
                    "BIRTH_CERT", "GUARDIAN_ID", "NO_ID"]
CONTACT_TYPE = Literal["MOBILE", "TEL", "EMAIL", "WECHAT", "OTHER"]
ADDRESS_TYPE = Literal["HOME", "WORK", "BILLING", "OTHER"]
RELATION_TYPE = Literal["SELF", "SPOUSE", "CHILD", "PARENT", "SIBLING", "OTHER"]
CONSENT_TYPE = Literal["PRIVACY", "TREATMENT", "MARKETING", "DATA_SHARE"]
CONSENT_STATUS = Literal["GRANTED", "REFUSED", "WITHDRAWN"]


# ==================== 查询 ====================
class PatientQuery(BaseModel):
    keyword: Optional[str] = None
    status: Optional[List[str]] = None
    patient_type: Optional[List[str]] = None
    patient_source: Optional[str] = None
    has_primary_id: Optional[bool] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class PatientListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empi_no: str
    patient_no: Optional[str] = None
    patient_name: str
    gender: str
    birth_date: Optional[date] = None
    primary_id_type: Optional[str] = None
    primary_id_mask: Optional[str] = None
    primary_phone_mask: Optional[str] = None
    patient_type: str
    patient_source: Optional[str] = None
    status: str
    quality_score: int = 0
    last_visit_at: Optional[datetime] = None


class PatientDetail(PatientListItem):
    nation_code: Optional[str] = None
    marital_status: Optional[str] = None
    education_code: Optional[str] = None
    occupation_code: Optional[str] = None
    allergy_history: Optional[str] = None
    status_reason: Optional[str] = None
    merge_to_id: Optional[int] = None
    first_visit_at: Optional[datetime] = None
    deceased_at: Optional[datetime] = None
    version_no: int = 1
    remark: Optional[str] = None
    identifiers: List["IdentifierSchema"] = []
    contacts: List["ContactSchema"] = []
    addresses: List["AddressSchema"] = []
    relations: List["RelationSchema"] = []
    consents: List["ConsentSchema"] = []


# ==================== 创建/更新 ====================
class PatientBase(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=64)
    name_pinyin: Optional[str] = Field(None, max_length=128)
    gender: GENDER = "UNKNOWN"
    birth_date: Optional[date] = None
    nation_code: Optional[str] = Field(None, max_length=32)
    marital_status: Optional[str] = Field(None, max_length=32)
    education_code: Optional[str] = Field(None, max_length=32)
    occupation_code: Optional[str] = Field(None, max_length=32)
    patient_type: PATIENT_TYPE = "NORMAL"
    patient_source: Optional[PATIENT_SOURCE] = None
    allergy_history: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = Field(None, max_length=512)

    @field_validator("birth_date")
    @classmethod
    def validate_birth(cls, v):
        if v and v > date.today():
            raise ValueError("出生日期不能晚于今天")
        return v


class PatientCreate(PatientBase):
    id_type: Optional[ID_TYPE] = None
    id_no: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

    @model_validator(mode="after")
    def validate_create(self):
        if bool(self.id_type) != bool(self.id_no):
            raise ValueError("证件类型与证件号必须同时填写或同时为空")
        if not self.id_no and not self.phone:
            # 无证件患者：姓名 + 性别 + 出生日期 + 手机号至少两项
            provided = sum([
                bool(self.patient_name), self.gender != "UNKNOWN",
                bool(self.birth_date), bool(self.phone),
            ])
            if provided < 2:
                raise ValueError("无证件患者至少需提供姓名/性别/出生日期/手机号中的两项")
        return self


class PatientUpdate(BaseModel):
    patient_name: Optional[str] = Field(None, max_length=64)
    name_pinyin: Optional[str] = Field(None, max_length=128)
    gender: Optional[GENDER] = None
    birth_date: Optional[date] = None
    nation_code: Optional[str] = None
    marital_status: Optional[str] = None
    education_code: Optional[str] = None
    occupation_code: Optional[str] = None
    patient_type: Optional[PATIENT_TYPE] = None
    patient_source: Optional[PATIENT_SOURCE] = None
    allergy_history: Optional[str] = Field(None, max_length=500)
    remark: Optional[str] = Field(None, max_length=512)
    version_no: int = Field(..., ge=1)


class PatientStatusRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    deceased_at: Optional[datetime] = None
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_status(self):
        if self.deceased_at and self.deceased_at > datetime.now():
            raise ValueError("死亡时间不能晚于当前时间")
        return self


# ==================== 证件 ====================
class IdentifierSchema(BaseModel):
    id: Optional[int] = None
    id_type: ID_TYPE
    id_no: Optional[str] = Field(None, max_length=64, description="新增/修改时传明文，查询时不返回")
    id_no_mask: Optional[str] = None
    is_primary: bool = False
    verified: bool = False
    source: Optional[str] = None

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.id_no and not self.id_no_mask:
            raise ValueError("必须提供证件号或掩码")
        return self


class IdentifierCreate(BaseModel):
    id_type: ID_TYPE
    id_no: str = Field(..., max_length=64)
    is_primary: bool = False
    source: Optional[str] = None


class IdentifierUpdate(BaseModel):
    id_no: Optional[str] = Field(None, max_length=64)
    is_primary: Optional[bool] = None
    verified: Optional[bool] = None


# ==================== 联系方式 ====================
class ContactSchema(BaseModel):
    id: Optional[int] = None
    contact_type: CONTACT_TYPE
    contact_value: Optional[str] = Field(None, max_length=128)
    contact_value_mask: Optional[str] = None
    is_primary: bool = False
    is_verified: bool = False
    source: Optional[str] = None


class ContactCreate(BaseModel):
    contact_type: CONTACT_TYPE
    contact_value: str = Field(..., max_length=128)
    is_primary: bool = False
    source: Optional[str] = None

    @field_validator("contact_value")
    @classmethod
    def validate_value(cls, v, info):
        t = info.data.get("contact_type")
        if t == "MOBILE" and not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        if t == "EMAIL" and not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
            raise ValueError("邮箱格式不正确")
        return v


class ContactUpdate(BaseModel):
    contact_value: Optional[str] = Field(None, max_length=128)
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None


# ==================== 地址 ====================
class AddressSchema(BaseModel):
    id: Optional[int] = None
    address_type: ADDRESS_TYPE
    province_code: Optional[str] = None
    city_code: Optional[str] = None
    district_code: Optional[str] = None
    address_detail: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = None
    is_primary: bool = False
    source: Optional[str] = None


class AddressCreate(AddressSchema):
    pass


class AddressUpdate(BaseModel):
    address_detail: Optional[str] = Field(None, max_length=500)
    postal_code: Optional[str] = None
    is_primary: Optional[bool] = None


# ==================== 联系人 ====================
class RelationSchema(BaseModel):
    id: Optional[int] = None
    relation_type: RELATION_TYPE
    relation_name: str = Field(..., max_length=64)
    relation_phone: Optional[str] = Field(None, max_length=20)
    relation_phone_mask: Optional[str] = None
    is_legal_guardian: bool = False
    is_emergency: bool = False
    is_primary: bool = False
    source: Optional[str] = None

    @model_validator(mode="after")
    def validate_relation(self):
        if self.is_legal_guardian and self.relation_type == "SELF":
            raise ValueError("法定监护人不能是本人")
        return self


class RelationCreate(RelationSchema):
    pass


class RelationUpdate(BaseModel):
    relation_name: Optional[str] = Field(None, max_length=64)
    relation_phone: Optional[str] = Field(None, max_length=20)
    is_legal_guardian: Optional[bool] = None
    is_emergency: Optional[bool] = None
    is_primary: Optional[bool] = None


# ==================== 授权 ====================
class ConsentSchema(BaseModel):
    id: Optional[int] = None
    consent_type: CONSENT_TYPE
    consent_version: str = Field(..., max_length=32)
    consent_status: CONSENT_STATUS
    signed_at: Optional[datetime] = None
    signed_channel: Optional[str] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    withdraw_at: Optional[datetime] = None
    withdraw_reason: Optional[str] = None


class ConsentCreate(BaseModel):
    consent_type: CONSENT_TYPE
    consent_version: str = Field(..., max_length=32)
    consent_status: CONSENT_STATUS = "GRANTED"
    signed_channel: Optional[str] = Field(None, max_length=32)
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    evidence_url: Optional[str] = Field(None, max_length=500)


class ConsentWithdraw(BaseModel):
    withdraw_reason: str = Field(..., min_length=5, max_length=500)


# ==================== 内部契约 ====================
class PatientEnsureRequest(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=64)
    gender: GENDER = "UNKNOWN"
    birth_date: Optional[date] = None
    id_type: Optional[ID_TYPE] = None
    id_no: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=20)
    source: Optional[PATIENT_SOURCE] = "OUTPATIENT"


class PatientEnsureResult(BaseModel):
    patient_id: int
    empi_no: str
    created: bool
    status: str
    duplicate_hint: Optional[str] = None


class RevealIdRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class RevealIdResult(BaseModel):
    patient_id: int
    id_type: str
    id_no_plain: str
    expire_in_seconds: int
    audit_id: Optional[str] = None


class PatientSyncItem(BaseModel):
    patient_id: int
    empi_no: str
    patient_no: Optional[str] = None
    patient_name: str
    name_pinyin: Optional[str] = None
    gender: str
    birth_date: Optional[date] = None
    id_card_no_mask: Optional[str] = None
    id_card_hash: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    patient_type: str
    allergy_history: Optional[str] = None
    status: str
    sync_version: int
    updated_at: Optional[datetime] = None


class PatientChangesResult(BaseModel):
    since_version: int
    current_version: int
    total: int
    page: int
    page_size: int
    items: List[PatientSyncItem]


# ==================== 配置 ====================
class MpiConfigUpdate(BaseModel):
    empi_prefix: str = Field("P", max_length=8)
    empi_seq_width: int = Field(6, ge=4, le=10)
    import_max_rows: int = Field(500, ge=10, le=5000)
    export_max_rows: int = Field(5000, ge=100, le=50000)
    sensitive_view_ttl_seconds: int = Field(300, ge=60, le=1800)
    min_quality_score: int = Field(60, ge=0, le=100)
    marketing_default: Literal["GRANTED", "REFUSED"] = "REFUSED"
    patient_no_enabled: bool = False
    log_retain_years: int = Field(5, ge=1, le=30)
    sync_batch_size: int = Field(500, ge=50, le=2000)
    version_no: int = Field(..., ge=1)


# 前向引用
PatientDetail.model_rebuild()
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：12 张表 | 系统设计组 |