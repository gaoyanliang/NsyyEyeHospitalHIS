# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块数据结构：患者匹配合并与质量

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 患者匹配合并与质量（Patient Matching, Merge & Quality）
**主数据域：** 患者域（`MPI`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 02 患者匹配合并与质量 详细设计》《M01 主数据管理MDM》《M02 统一权限与安全》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「患者匹配合并与质量」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[患者匹配合并与质量详细设计](M03_患者服务与EMPI_02_患者匹配合并与质量_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [患者匹配合并与质量详细设计](M03_患者服务与EMPI_02_患者匹配合并与质量_详细设计.md)
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md)
- [01 患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md) — `mpi_patient` 等
- [M01 数据结构设计汇总](../M01主数据管理MDM/M01_主数据管理MDM_数据结构设计汇总.md) — `mdm_department` / `mdm_employee` / `md_dict_item` / `md_dict_type` / `md_sys_param`
- [M02 账号管理数据结构](../M02统一权限与安全/M02_统一权限与安全_01_账号管理_数据结构.md) — `sys_account`
- [M02 审计日志数据结构](../M02统一权限与安全/M02_统一权限与安全_06_审计日志_数据结构.md) — `sys_audit_log`
- [M02 二次验证数据结构](../M02统一权限与安全/M02_统一权限与安全_05_二次验证_数据结构.md) — `sys_mfa_challenge`

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 13 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_dedup_config`（匹配合并配置表）](#42-表mpi_dedup_config匹配合并配置表)
- [4.3 表：`mpi_match_rule`（匹配规则表）](#43-表mpi_match_rule匹配规则表)
- [4.4 表：`mpi_match_candidate`（候选匹配对表）](#44-表mpi_match_candidate候选匹配对表)
- [4.5 表：`mpi_match_task`（批量匹配任务表）](#45-表mpi_match_task批量匹配任务表)
- [4.6 表：`mpi_merge_request`（合并申请单表）](#46-表mpi_merge_request合并申请单表)
- [4.7 表：`mpi_merge_request_item`（合并申请明细表）](#47-表mpi_merge_request_item合并申请明细表)
- [4.8 表：`mpi_merge_approval`（合并审批节点表）](#48-表mpi_merge_approval合并审批节点表)
- [4.9 表：`mpi_merge_log`（合并执行日志表）](#49-表mpi_merge_log合并执行日志表)
- [4.10 表：`mpi_split_log`（拆分日志表）](#410-表mpi_split_log拆分日志表)
- [4.11 表：`mpi_patient_version`（患者版本快照表）](#411-表mpi_patient_version患者版本快照表)
- [4.12 表：`mpi_quality_rule`（质量规则表）](#412-表mpi_quality_rule质量规则表)
- [4.13 表：`mpi_quality_result`（质量扫描结果表）](#413-表mpi_quality_result质量扫描结果表)
- [4.14 表：`mpi_patient_blocklist`（患者黑名单表）](#414-表mpi_patient_blocklist患者黑名单表)
- [4.15 SQLAlchemy 2.0 模型定义](#415-sqlalchemy-20-模型定义)
- [4.16 Pydantic Schema 定义](#416-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_dedup_config` | 匹配合并配置表（单行） |
| 4.3 | `mpi_match_rule` | 匹配规则表 |
| 4.4 | `mpi_match_candidate` | 候选匹配对表 |
| 4.5 | `mpi_match_task` | 批量匹配任务表 |
| 4.6 | `mpi_merge_request` | 合并申请单表 |
| 4.7 | `mpi_merge_request_item` | 合并申请明细表 |
| 4.8 | `mpi_merge_approval` | 合并审批节点表 |
| 4.9 | `mpi_merge_log` | 合并执行日志表 |
| 4.10 | `mpi_split_log` | 拆分日志表 |
| 4.11 | `mpi_patient_version` | 患者版本快照表 |
| 4.12 | `mpi_quality_rule` | 质量规则表 |
| 4.13 | `mpi_quality_result` | 质量扫描结果表 |
| 4.14 | `mpi_patient_blocklist` | 患者黑名单表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 01 依赖（逻辑引用）                                                  │
│ mpi_patient / mpi_patient_identifier / mpi_patient_contact          │
│ mpi_patient_address / mpi_patient_relation / mpi_patient_consent    │
│ mpi_patient_log                                                     │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ M01/M02 依赖（逻辑引用）                                              │
│ mdm_employee / mdm_department / md_dict_item / md_sys_param         │
│ sys_account / sys_audit_log / sys_mfa_challenge                     │
└──────────────────────────────────────────────────────────────────────┘

配置与规则：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_dedup_config             │  │ mpi_match_rule               │
│ （匹配合并配置，单行）         │  │ （匹配规则，按场景）           │
└──────────────────────────────┘  └──────────────────────────────┘

匹配：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_match_task               │  │ mpi_match_candidate          │
│ （批量匹配任务）              │──►│ （候选匹配对）                 │
└──────────────────────────────┘  └──────────────┬───────────────┘
                                                 │ 确认后
                                                 ▼
合并：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_merge_request            │──►│ mpi_merge_request_item       │
│ （合并申请单）                │  │ （申请明细：主/从/影响）       │
└──────────┬───────────────────┘  └──────────────────────────────┘
           │ 1:N
           ▼
┌──────────────────────────────┐
│ mpi_merge_approval           │
│ （审批节点）                  │
└──────────┬───────────────────┘
           │ 执行合并
           ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_merge_log                │  │ mpi_patient_version          │
│ （合并执行日志 + 重定向清单）  │◄─│ （患者版本快照）              │
└──────────┬───────────────────┘  └──────────────────────────────┘
           │ 拆分
           ▼
┌──────────────────────────────┐
│ mpi_split_log                │
│ （拆分日志）                  │
└──────────────────────────────┘

质量：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_quality_rule             │──►│ mpi_quality_result           │
│ （质量规则）                  │  │ （扫描结果 + 问题明细）        │
└──────────────────────────────┘  └──────────────────────────────┘

黑名单：
┌──────────────────────────────┐
│ mpi_patient_blocklist        │
│ （患者黑名单）                │
└──────────────────────────────┘
```

**说明：**

- 所有表统一 `mpi_` 前缀，逻辑删除统一 `is_deleted BOOLEAN DEFAULT FALSE`。
- 状态统一 `VARCHAR(16)`，使用大写英文枚举。
- 跨模块逻辑引用不建物理外键。
- `mpi_merge_log` / `mpi_split_log` / `mpi_quality_result` 按 `created_at` 月度 RANGE 分区。
- 版本快照 `snapshot_json` 使用 JSONB，敏感字段加密后存储。

### 4.2 表：`mpi_dedup_config`（匹配合并配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| instant_match_enabled | BOOLEAN | N | TRUE | 建档即时匹配启用 |
| instant_match_limit | INT | N | 5 | 即时匹配返回上限 |
| instant_match_min_level | VARCHAR(16) | N | 'MEDIUM' | 即时匹配最低等级 |
| batch_match_enabled | BOOLEAN | N | TRUE | 批量匹配启用 |
| batch_match_cron | VARCHAR(32) | N | '0 3 * * *' | 批量匹配 Cron |
| batch_match_max_rows | INT | N | 100000 | 单次批量匹配上限 |
| threshold_high | NUMERIC(5,2) | N | 95.00 | 高候选阈值 |
| threshold_medium | NUMERIC(5,2) | N | 80.00 | 中候选阈值 |
| threshold_low | NUMERIC(5,2) | N | 60.00 | 低候选阈值 |
| candidate_expire_days | INT | N | 90 | 已忽略候选清理天数 |
| merge_second_factor | BOOLEAN | N | TRUE | 执行合并需二次验证 |
| split_second_factor | BOOLEAN | N | TRUE | 执行拆分需二次验证 |
| risk_low_doc_limit | INT | N | 10 | LOW 风险单据上限 |
| risk_low_amount_limit | NUMERIC(14,2) | N | 1000.00 | LOW 风险金额上限 |
| risk_medium_doc_limit | INT | N | 100 | MEDIUM 风险单据上限 |
| risk_medium_amount_limit | NUMERIC(14,2) | N | 50000.00 | MEDIUM 风险金额上限 |
| redirect_max_ids_per_item | INT | N | 1000 | 单条重定向清单上限 |
| redirect_retry_limit | INT | N | 5 | 重定向重试上限 |
| quality_scan_cron | VARCHAR(32) | N | '0 2 * * *' | 质量扫描 Cron |
| quality_sla_days | INT | N | 7 | 整改 SLA 天数 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人（`sys_account.id`） |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_mpi_dedup_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_dedup_config
    ADD CONSTRAINT ck_mpi_dedup_config_single_row CHECK (id = 1);

ALTER TABLE mpi_dedup_config
    ADD CONSTRAINT ck_mpi_dedup_threshold_order
    CHECK (threshold_high > threshold_medium AND threshold_medium > threshold_low);
```

### 4.3 表：`mpi_match_rule`（匹配规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| rule_code | VARCHAR(32) | N | - | 规则编码（如 `REGISTRATION` / `BATCH`） |
| rule_name | VARCHAR(128) | N | - | 规则名称 |
| scene | VARCHAR(32) | N | - | 场景：REGISTRATION/BATCH/MANUAL |
| algorithm | VARCHAR(64) | N | 'WEIGHTED' | 算法：WEIGHTED/EXACT_ONLY |
| field_weights | JSONB | N | - | 字段权重 `{ "name":0.2, "id_hash":0.4, ... }` |
| field_algorithms | JSONB | Y | NULL | 各字段算法 `{ "name":"PINYIN_EDIT", ... }` |
| gender_mismatch_zero | BOOLEAN | N | TRUE | 性别不一致时总分为 0 |
| birth_tolerance_days | INT | N | 1 | 出生日期容差天数 |
| id_exact_shortcut | BOOLEAN | N | TRUE | 证件哈希命中直接 100 分 |
| phone_exact_bonus | NUMERIC(5,2) | N | 0.00 | 手机号命中加分（0~10） |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| is_builtin | BOOLEAN | N | FALSE | 是否内置（不可删） |
| sort_no | INT | N | 999 | 排序 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_match_rule_code(rule_code, is_deleted)` 唯一；`idx_mpi_match_rule_scene(scene, is_enabled)`。

**约束说明**

```sql
ALTER TABLE mpi_match_rule
    ADD CONSTRAINT ck_mpi_match_rule_scene
    CHECK (scene IN ('REGISTRATION', 'BATCH', 'MANUAL'));

ALTER TABLE mpi_match_rule
    ADD CONSTRAINT ck_mpi_match_rule_algorithm
    CHECK (algorithm IN ('WEIGHTED', 'EXACT_ONLY'));
```

**预置规则：**

| rule_code | scene | 说明 |
|---|---|---|
| `REGISTRATION` | REGISTRATION | 建档即时匹配 |
| `BATCH` | BATCH | 批量扫描 |

### 4.4 表：`mpi_match_candidate`（候选匹配对表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_a_id | BIGINT | N | - | 患者 A ID |
| patient_b_id | BIGINT | N | - | 患者 B ID |
| empi_no_a | VARCHAR(32) | Y | NULL | 患者 A EMPI（冗余） |
| empi_no_b | VARCHAR(32) | Y | NULL | 患者 B EMPI（冗余） |
| patient_name_a | VARCHAR(64) | Y | NULL | 患者 A 姓名（冗余） |
| patient_name_b | VARCHAR(64) | Y | NULL | 患者 B 姓名（冗余） |
| total_score | NUMERIC(5,2) | N | 0.00 | 总分 0~100 |
| level | VARCHAR(16) | N | 'NONE' | 等级：HIGH/MEDIUM/LOW/NONE |
| source | VARCHAR(16) | N | 'BATCH' | 来源：REGISTRATION/BATCH/MANUAL |
| task_id | BIGINT | Y | NULL | 来源批量任务 ID |
| field_scores | JSONB | Y | NULL | 字段得分明细 |
| hit_fields | VARCHAR(500) | Y | NULL | 命中字段 |
| status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/CONFIRMED/IGNORED/IN_MERGE/MERGED/DELETED |
| handled_by | BIGINT | Y | NULL | 处理人 |
| handled_at | TIMESTAMP | Y | NULL | 处理时间 |
| handle_note | VARCHAR(500) | Y | NULL | 处理说明 |
| merge_request_id | BIGINT | Y | NULL | 关联合并申请 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 生成时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_match_candidate | PRIMARY | id | 主键 |
| uk_mpi_candidate_pair | UNIQUE | patient_a_id, patient_b_id, is_deleted | 去重 |
| idx_mpi_candidate_level | NORMAL | level, status | 按等级筛选 |
| idx_mpi_candidate_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_candidate_source | NORMAL | source, created_at | 按来源 |
| idx_mpi_candidate_a | NORMAL | patient_a_id | 按患者 A |
| idx_mpi_candidate_b | NORMAL | patient_b_id | 按患者 B |
| idx_mpi_candidate_task | NORMAL | task_id | 按任务 |

**约束说明**

```sql
ALTER TABLE mpi_match_candidate
    ADD CONSTRAINT ck_mpi_candidate_level
    CHECK (level IN ('HIGH', 'MEDIUM', 'LOW', 'NONE'));

ALTER TABLE mpi_match_candidate
    ADD CONSTRAINT ck_mpi_candidate_status
    CHECK (status IN ('PENDING', 'CONFIRMED', 'IGNORED', 'IN_MERGE', 'MERGED', 'DELETED'));

ALTER TABLE mpi_match_candidate
    ADD CONSTRAINT ck_mpi_candidate_pair_order
    CHECK (patient_a_id < patient_b_id);
```

> 约定 `patient_a_id < patient_b_id`，保证同一对患者只生成一条候选记录。

### 4.5 表：`mpi_match_task`（批量匹配任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_no | VARCHAR(32) | N | - | 任务号 `MT+年月日+流水` |
| rule_code | VARCHAR(32) | N | 'BATCH' | 使用的匹配规则 |
| scope_type | VARCHAR(16) | N | 'ALL' | 扫描范围：ALL/RECENT/DEPT/SOURCE |
| scope_value | VARCHAR(255) | Y | NULL | 范围值（如近 90 天、科室 ID） |
| total_patients | INT | N | 0 | 扫描患者总数 |
| candidate_count | INT | N | 0 | 生成的候选数 |
| high_count | INT | N | 0 | 高等级数 |
| medium_count | INT | N | 0 | 中等级数 |
| low_count | INT | N | 0 | 低等级数 |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/RUNNING/SUCCESS/FAILED/CANCELLED |
| started_at | TIMESTAMP | Y | NULL | 开始时间 |
| finished_at | TIMESTAMP | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_match_task_no(task_no, is_deleted)` 唯一；`idx_mpi_match_task_status(status, created_at)`；`idx_mpi_match_task_operator(operator_id, created_at)`。

**约束说明**

```sql
ALTER TABLE mpi_match_task
    ADD CONSTRAINT ck_mpi_match_task_status
    CHECK (status IN ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED'));
```

### 4.6 表：`mpi_merge_request`（合并申请单表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| merge_no | VARCHAR(32) | N | - | 合并单号 `MG+年月日+流水` |
| primary_patient_id | BIGINT | N | - | 主患者 ID |
| secondary_patient_id | BIGINT | N | - | 从患者 ID |
| primary_empi_no | VARCHAR(32) | Y | NULL | 主患者 EMPI（冗余） |
| secondary_empi_no | VARCHAR(32) | Y | NULL | 从患者 EMPI（冗余） |
| candidate_id | BIGINT | Y | NULL | 来源候选对 ID |
| reason | VARCHAR(500) | N | - | 合并原因 |
| attachment_ids | VARCHAR(500) | Y | NULL | 附件 ID 列表 |
| risk_level | VARCHAR(16) | N | 'LOW' | LOW/MEDIUM/HIGH |
| impact_json | JSONB | Y | NULL | 影响分析结果 |
| approval_chain | VARCHAR(500) | Y | NULL | 审批链（节点名逗号分隔） |
| current_node | VARCHAR(64) | Y | NULL | 当前节点 |
| current_approver_id | BIGINT | Y | NULL | 当前审批人 |
| status | VARCHAR(16) | N | 'DRAFT' | DRAFT/PENDING/APPROVED/REJECTED/WITHDRAWN/EXECUTED/FAILED/SPLIT_PENDING |
| submitted_at | TIMESTAMP | Y | NULL | 提交时间 |
| approved_at | TIMESTAMP | Y | NULL | 审批通过时间 |
| executed_at | TIMESTAMP | Y | NULL | 执行时间 |
| executed_by | BIGINT | Y | NULL | 执行人 |
| merge_log_id | BIGINT | Y | NULL | 合并日志 ID |
| version_no | INT | N | 1 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 申请人 |
| created_by_name | VARCHAR(64) | Y | NULL | 申请人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_merge_request | PRIMARY | id | 主键 |
| uk_mpi_merge_no | UNIQUE | merge_no, is_deleted | 合并单号唯一 |
| idx_mpi_merge_primary | NORMAL | primary_patient_id, status | 主患者 |
| idx_mpi_merge_secondary | NORMAL | secondary_patient_id, status | 从患者 |
| idx_mpi_merge_status | NORMAL | status, created_at | 状态列表 |
| idx_mpi_merge_approver | NORMAL | current_approver_id, status | 待办 |
| idx_mpi_merge_creator | NORMAL | created_by, status | 我申请的 |

**约束说明**

```sql
ALTER TABLE mpi_merge_request
    ADD CONSTRAINT ck_mpi_merge_risk
    CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH'));

ALTER TABLE mpi_merge_request
    ADD CONSTRAINT ck_mpi_merge_status
    CHECK (status IN ('DRAFT', 'PENDING', 'APPROVED', 'REJECTED',
                       'WITHDRAWN', 'EXECUTED', 'FAILED', 'SPLIT_PENDING'));

ALTER TABLE mpi_merge_request
    ADD CONSTRAINT ck_mpi_merge_pair
    CHECK (primary_patient_id <> secondary_patient_id);
```

### 4.7 表：`mpi_merge_request_item`（合并申请明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| merge_request_id | BIGINT | N | - | 合并申请 ID |
| patient_role | VARCHAR(16) | N | - | 角色：PRIMARY/SECONDARY |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| business_summary | JSONB | Y | NULL | 业务汇总（门诊/住院/收费/视光/屈光） |
| impact_detail | JSONB | Y | NULL | 影响明细（业务表 + 条数 + 金额） |
| snapshot_json | JSONB | Y | NULL | 申请时的患者简要快照 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_mpi_merge_item(merge_request_id, patient_role)` 唯一；`idx_mpi_merge_item_patient(patient_id)`。

**约束说明**

```sql
ALTER TABLE mpi_merge_request_item
    ADD CONSTRAINT ck_mpi_merge_item_role
    CHECK (patient_role IN ('PRIMARY', 'SECONDARY'));
```

### 4.8 表：`mpi_merge_approval`（合并审批节点表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| merge_request_id | BIGINT | N | - | 合并申请 ID |
| node_seq | INT | N | - | 节点顺序 |
| node_name | VARCHAR(64) | N | - | 节点名称 |
| approver_id | BIGINT | Y | NULL | 审批人（`sys_account.id`） |
| approver_name | VARCHAR(64) | Y | NULL | 审批人姓名 |
| status | VARCHAR(16) | N | 'WAITING' | WAITING/PENDING/APPROVED/REJECTED/TRANSFERRED/SKIPPED |
| opinion | VARCHAR(500) | Y | NULL | 审批意见 |
| signature_url | VARCHAR(255) | Y | NULL | 电子签名 |
| arrived_at | TIMESTAMP | Y | NULL | 到达时间 |
| handled_at | TIMESTAMP | Y | NULL | 处理时间 |
| wait_hours | NUMERIC(8,2) | Y | NULL | 等待时长 |
| transfer_from | BIGINT | Y | NULL | 转办来源 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `idx_mpi_merge_approval_req(merge_request_id, node_seq)`；`idx_mpi_merge_approval_approver(approver_id, status)`。

**约束说明**

```sql
ALTER TABLE mpi_merge_approval
    ADD CONSTRAINT ck_mpi_merge_approval_status
    CHECK (status IN ('WAITING', 'PENDING', 'APPROVED', 'REJECTED', 'TRANSFERRED', 'SKIPPED'));
```

### 4.9 表：`mpi_merge_log`（合并执行日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| merge_no | VARCHAR(32) | N | - | 合并单号（冗余） |
| merge_request_id | BIGINT | Y | NULL | 合并申请 ID |
| primary_patient_id | BIGINT | N | - | 主患者 ID |
| secondary_patient_id | BIGINT | N | - | 从患者 ID |
| primary_empi_no | VARCHAR(32) | Y | NULL | 主患者 EMPI |
| secondary_empi_no | VARCHAR(32) | Y | NULL | 从患者 EMPI |
| version_snapshot_id | BIGINT | Y | NULL | 版本快照 ID |
| redirect_items_json | JSONB | Y | NULL | 重定向清单 |
| redirect_status | VARCHAR(16) | N | 'PENDING' | PENDING/PARTIAL/COMPLETED/FAILED |
| redirect_success_count | INT | N | 0 | 成功条数 |
| redirect_fail_count | INT | N | 0 | 失败条数 |
| redirect_retry_count | INT | N | 0 | 重试次数 |
| executed_by | BIGINT | Y | NULL | 执行人 |
| executed_by_name | VARCHAR(64) | Y | NULL | 执行人姓名 |
| executed_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 执行时间 |
| result | VARCHAR(16) | N | 'SUCCESS' | SUCCESS/FAILED/PARTIAL |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| detail_json | JSONB | Y | NULL | 其他详情 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_merge_log | PRIMARY | id | 主键 |
| idx_mpi_merge_log_no | NORMAL | merge_no | 合并单号 |
| idx_mpi_merge_log_primary | NORMAL | primary_patient_id, executed_at | 主患者 |
| idx_mpi_merge_log_secondary | NORMAL | secondary_patient_id, executed_at | 从患者 |
| idx_mpi_merge_log_status | NORMAL | redirect_status, created_at | 重定向状态 |
| idx_mpi_merge_log_time | NORMAL | created_at | 时间范围 |

**约束说明**

```sql
ALTER TABLE mpi_merge_log
    ADD CONSTRAINT ck_mpi_merge_log_result
    CHECK (result IN ('SUCCESS', 'FAILED', 'PARTIAL'));

ALTER TABLE mpi_merge_log
    ADD CONSTRAINT ck_mpi_merge_log_redirect
    CHECK (redirect_status IN ('PENDING', 'PARTIAL', 'COMPLETED', 'FAILED'));
```

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **10 年**。

### 4.10 表：`mpi_split_log`（拆分日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| split_no | VARCHAR(32) | N | - | 拆分单号 `SP+年月日+流水` |
| merge_log_id | BIGINT | N | - | 关联合并日志 |
| merge_no | VARCHAR(32) | Y | NULL | 合并单号（冗余） |
| patient_id | BIGINT | N | - | 待拆分患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| current_merge_to_id | BIGINT | Y | NULL | 拆分前的 merge_to_id |
| reason_type | VARCHAR(32) | N | - | MISJUDGED/SYSTEM_ERROR/PATIENT_REQUEST/OTHER |
| reason_desc | VARCHAR(500) | N | - | 原因说明 |
| attachment_ids | VARCHAR(500) | Y | NULL | 附件 |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/APPROVING/APPROVED/REJECTED/EXECUTED/FAILED |
| current_approver_id | BIGINT | Y | NULL | 当前审批人 |
| approved_at | TIMESTAMP | Y | NULL | 审批通过时间 |
| executed_by | BIGINT | Y | NULL | 执行人 |
| executed_at | TIMESTAMP | Y | NULL | 执行时间 |
| work_order_no | VARCHAR(32) | Y | NULL | 业务回迁工单号 |
| result | VARCHAR(16) | N | 'SUCCESS' | SUCCESS/FAILED |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 申请人 |
| created_by_name | VARCHAR(64) | Y | NULL | 申请人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_split_no(split_no, is_deleted)` 唯一；`idx_mpi_split_patient(patient_id, created_at)`；`idx_mpi_split_merge(merge_log_id)`；`idx_mpi_split_status(status, created_at)`；`idx_mpi_split_approver(current_approver_id, status)`。

**约束说明**

```sql
ALTER TABLE mpi_split_log
    ADD CONSTRAINT ck_mpi_split_reason
    CHECK (reason_type IN ('MISJUDGED', 'SYSTEM_ERROR', 'PATIENT_REQUEST', 'OTHER'));

ALTER TABLE mpi_split_log
    ADD CONSTRAINT ck_mpi_split_status
    CHECK (status IN ('PENDING', 'APPROVING', 'APPROVED', 'REJECTED',
                       'EXECUTED', 'FAILED'));
```

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **10 年**。

### 4.11 表：`mpi_patient_version`（患者版本快照表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| version_type | VARCHAR(32) | N | - | MERGE_PRE/SPLIT_PRE/UPDATE_PRE |
| version_seq | INT | N | 1 | 同一患者同一类型版本序号 |
| snapshot_json | JSONB | N | - | 完整快照（敏感字段已加密） |
| snapshot_hash | VARCHAR(128) | Y | NULL | 快照哈希（防篡改） |
| source_ref | VARCHAR(64) | Y | NULL | 来源（合并单号/拆分单号） |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_patient_version(patient_id, version_type, version_seq, is_deleted)` 唯一；`idx_mpi_patient_version_patient(patient_id, created_at)`；`idx_mpi_patient_version_source(source_ref)`。

**约束说明**

```sql
ALTER TABLE mpi_patient_version
    ADD CONSTRAINT ck_mpi_patient_version_type
    CHECK (version_type IN ('MERGE_PRE', 'SPLIT_PRE', 'UPDATE_PRE'));
```

**快照 JSON 结构（示例）：**

```json
{
  "patient": { "...": "mpi_patient 行" },
  "identifiers": [],
  "contacts": [],
  "addresses": [],
  "relations": [],
  "consents": [],
  "captured_at": "2026-10-20T11:00:00+08:00"
}
```

**分区：** 不分区（单患者版本数有限，量级可控）。

### 4.12 表：`mpi_quality_rule`（质量规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| rule_code | VARCHAR(32) | N | - | 规则编码（`QR-{维度}-{序号}`） |
| rule_name | VARCHAR(128) | N | - | 规则名称 |
| dimension | VARCHAR(16) | N | - | 维度：COMPLETENESS/UNIQUENESS/FORMAT/TIMELINESS/REFERENCE |
| object_type | VARCHAR(32) | N | 'PATIENT' | 对象：PATIENT/IDENTIFIER/CONTACT/ADDRESS/RELATION |
| severity | VARCHAR(16) | N | 'WARN' | ERROR/WARN/INFO |
| condition_expr | JSONB | N | - | 条件表达式 |
| threshold | VARCHAR(64) | Y | NULL | 阈值（时效类） |
| suggestion | VARCHAR(500) | Y | NULL | 整改建议 |
| auto_fix | BOOLEAN | N | FALSE | 是否支持自动修复（预留，本期不实现） |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| is_builtin | BOOLEAN | N | FALSE | 是否内置 |
| sort_no | INT | N | 999 | 排序 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_quality_rule_code(rule_code, is_deleted)` 唯一；`idx_mpi_quality_rule_dim(dimension, is_enabled)`；`idx_mpi_quality_rule_object(object_type, is_enabled)`。

**约束说明**

```sql
ALTER TABLE mpi_quality_rule
    ADD CONSTRAINT ck_mpi_quality_dim
    CHECK (dimension IN ('COMPLETENESS', 'UNIQUENESS', 'FORMAT', 'TIMELINESS', 'REFERENCE'));

ALTER TABLE mpi_quality_rule
    ADD CONSTRAINT ck_mpi_quality_severity
    CHECK (severity IN ('ERROR', 'WARN', 'INFO'));

ALTER TABLE mpi_quality_rule
    ADD CONSTRAINT ck_mpi_quality_object
    CHECK (object_type IN ('PATIENT', 'IDENTIFIER', 'CONTACT', 'ADDRESS', 'RELATION'));
```

### 4.13 表：`mpi_quality_result`（质量扫描结果表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| scan_no | VARCHAR(32) | N | - | 扫描批次号 `QS+年月日+流水` |
| rule_id | BIGINT | N | - | 规则 ID |
| rule_code | VARCHAR(32) | N | - | 规则编码（冗余） |
| rule_name | VARCHAR(128) | Y | NULL | 规则名称 |
| dimension | VARCHAR(16) | N | - | 维度（冗余） |
| severity | VARCHAR(16) | N | - | 严重级别 |
| patient_id | BIGINT | N | - | 问题患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| field_name | VARCHAR(64) | Y | NULL | 问题字段 |
| field_value_mask | VARCHAR(255) | Y | NULL | 字段值掩码 |
| issue_desc | VARCHAR(500) | Y | NULL | 问题描述 |
| status | VARCHAR(16) | N | 'OPEN' | OPEN/ASSIGNED/RESOLVED/IGNORED |
| assignee_id | BIGINT | Y | NULL | 整改人 |
| assignee_name | VARCHAR(64) | Y | NULL | 整改人姓名 |
| assigned_at | TIMESTAMP | Y | NULL | 指派时间 |
| resolved_at | TIMESTAMP | Y | NULL | 整改完成时间 |
| resolve_note | VARCHAR(500) | Y | NULL | 整改说明 |
| scan_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 扫描时间 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_quality_result | PRIMARY | id | 主键 |
| idx_mpi_quality_scan | NORMAL | scan_no, rule_code | 按扫描批次 |
| idx_mpi_quality_patient | NORMAL | patient_id, status | 按患者 |
| idx_mpi_quality_rule | NORMAL | rule_id, status | 按规则 |
| idx_mpi_quality_dim | NORMAL | dimension, status | 按维度 |
| idx_mpi_quality_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_quality_assignee | NORMAL | assignee_id, status | 按整改人 |

**约束说明**

```sql
ALTER TABLE mpi_quality_result
    ADD CONSTRAINT ck_mpi_quality_result_status
    CHECK (status IN ('OPEN', 'ASSIGNED', 'RESOLVED', 'IGNORED'));
```

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **3 年**。

### 4.14 表：`mpi_patient_blocklist`（患者黑名单表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI |
| patient_name | VARCHAR(64) | Y | NULL | 姓名 |
| block_type | VARCHAR(16) | N | - | NO_MERGE/NO_REFERENCE/BOTH |
| reason | VARCHAR(500) | N | - | 原因 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL=长期） |
| status | VARCHAR(16) | N | 'ACTIVE' | ACTIVE/RELEASED/EXPIRED |
| created_by | BIGINT | Y | NULL | 操作人 |
| created_by_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| released_at | TIMESTAMP | Y | NULL | 解除时间 |
| released_by | BIGINT | Y | NULL | 解除人 |
| release_reason | VARCHAR(500) | Y | NULL | 解除原因 |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `idx_mpi_blocklist_patient(patient_id, status)`；`idx_mpi_blocklist_status(status, expire_date)`；`idx_mpi_blocklist_type(block_type, status)`。

**约束说明**

```sql
ALTER TABLE mpi_patient_blocklist
    ADD CONSTRAINT ck_mpi_blocklist_type
    CHECK (block_type IN ('NO_MERGE', 'NO_REFERENCE', 'BOTH'));

ALTER TABLE mpi_patient_blocklist
    ADD CONSTRAINT ck_mpi_blocklist_status
    CHECK (status IN ('ACTIVE', 'RELEASED', 'EXPIRED'));

-- 同一患者同一时间只能有一条 ACTIVE 黑名单
CREATE UNIQUE INDEX uk_mpi_blocklist_active
    ON mpi_patient_blocklist (patient_id)
    WHERE status = 'ACTIVE' AND is_deleted = FALSE;
```

### 4.15 SQLAlchemy 2.0 模型定义

```python
# app/models/mpi/dedup.py
"""患者匹配合并与质量 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Boolean, Date, DateTime,
    Numeric, JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MpiDedupConfig(Base):
    """匹配合并配置（单行）"""
    __tablename__ = "mpi_dedup_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    instant_match_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    instant_match_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    instant_match_min_level: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)

    batch_match_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    batch_match_cron: Mapped[str] = mapped_column(String(32), default="0 3 * * *", nullable=False)
    batch_match_max_rows: Mapped[int] = mapped_column(Integer, default=100000, nullable=False)

    threshold_high: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("95.00"), nullable=False)
    threshold_medium: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("80.00"), nullable=False)
    threshold_low: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("60.00"), nullable=False)
    candidate_expire_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)

    merge_second_factor: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    split_second_factor: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    risk_low_doc_limit: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    risk_low_amount_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("1000.00"), nullable=False)
    risk_medium_doc_limit: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    risk_medium_amount_limit: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("50000.00"), nullable=False)

    redirect_max_ids_per_item: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    redirect_retry_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    quality_scan_cron: Mapped[str] = mapped_column(String(32), default="0 2 * * *", nullable=False)
    quality_sla_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)

    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "匹配合并配置（单行）"},
    )


class MpiMatchRule(Base, TimestampMixin, SoftDeleteMixin):
    """匹配规则"""
    __tablename__ = "mpi_match_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    scene: Mapped[str] = mapped_column(String(32), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), default="WEIGHTED", nullable=False)
    field_weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    field_algorithms: Mapped[Optional[dict]] = mapped_column(JSONB)
    gender_mismatch_zero: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    birth_tolerance_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    id_exact_shortcut: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    phone_exact_bonus: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.00"), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("rule_code", "is_deleted", name="uk_mpi_match_rule_code"),
        Index("idx_mpi_match_rule_scene", "scene", "is_enabled"),
        {"comment": "匹配规则"},
    )

    def weight_sum(self) -> Decimal:
        return Decimal(str(sum(self.field_weights.values())))

    def is_weight_valid(self) -> bool:
        return abs(self.weight_sum() - Decimal("1.0")) <= Decimal("0.01")


class MpiMatchCandidate(Base):
    """候选匹配对"""
    __tablename__ = "mpi_match_candidate"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_a_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_b_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no_a: Mapped[Optional[str]] = mapped_column(String(32))
    empi_no_b: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name_a: Mapped[Optional[str]] = mapped_column(String(64))
    patient_name_b: Mapped[Optional[str]] = mapped_column(String(64))
    total_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="NONE", nullable=False)
    source: Mapped[str] = mapped_column(String(16), default="BATCH", nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    field_scores: Mapped[Optional[dict]] = mapped_column(JSONB)
    hit_fields: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    handled_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    handle_note: Mapped[Optional[str]] = mapped_column(String(500))
    merge_request_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_a_id", "patient_b_id", "is_deleted",
                         name="uk_mpi_candidate_pair"),
        Index("idx_mpi_candidate_level", "level", "status"),
        Index("idx_mpi_candidate_status", "status", "created_at"),
        Index("idx_mpi_candidate_source", "source", "created_at"),
        Index("idx_mpi_candidate_a", "patient_a_id"),
        Index("idx_mpi_candidate_b", "patient_b_id"),
        Index("idx_mpi_candidate_task", "task_id"),
        {"comment": "候选匹配对"},
    )

    LEVEL_LABELS = {"HIGH": "高", "MEDIUM": "中", "LOW": "低", "NONE": "无"}

    @property
    def level_label(self) -> str:
        return self.LEVEL_LABELS.get(self.level, self.level)


class MpiMatchTask(Base):
    """批量匹配任务"""
    __tablename__ = "mpi_match_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(32), default="BATCH", nullable=False)
    scope_type: Mapped[str] = mapped_column(String(16), default="ALL", nullable=False)
    scope_value: Mapped[Optional[str]] = mapped_column(String(255))
    total_patients: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    high_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    medium_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    low_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cost_ms: Mapped[Optional[int]] = mapped_column(BigInteger)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("task_no", "is_deleted", name="uk_mpi_match_task_no"),
        Index("idx_mpi_match_task_status", "status", "created_at"),
        Index("idx_mpi_match_task_operator", "operator_id", "created_at"),
        {"comment": "批量匹配任务"},
    )


class MpiMergeRequest(Base, TimestampMixin, SoftDeleteMixin):
    """合并申请单"""
    __tablename__ = "mpi_merge_request"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merge_no: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    secondary_patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    primary_empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    secondary_empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    candidate_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    attachment_ids: Mapped[Optional[str]] = mapped_column(String(500))
    risk_level: Mapped[str] = mapped_column(String(16), default="LOW", nullable=False)
    impact_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    approval_chain: Mapped[Optional[str]] = mapped_column(String(500))
    current_node: Mapped[Optional[str]] = mapped_column(String(64))
    current_approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    executed_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    merge_log_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    items: Mapped[List["MpiMergeRequestItem"]] = relationship(
        back_populates="request", lazy="selectin")
    approvals: Mapped[List["MpiMergeApproval"]] = relationship(
        back_populates="request", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("merge_no", "is_deleted", name="uk_mpi_merge_no"),
        Index("idx_mpi_merge_primary", "primary_patient_id", "status"),
        Index("idx_mpi_merge_secondary", "secondary_patient_id", "status"),
        Index("idx_mpi_merge_status", "status", "created_at"),
        Index("idx_mpi_merge_approver", "current_approver_id", "status"),
        Index("idx_mpi_merge_creator", "created_by", "status"),
        {"comment": "合并申请单"},
    )

    STATUS_LABELS = {
        "DRAFT": "草稿", "PENDING": "审批中", "APPROVED": "已批准",
        "REJECTED": "已驳回", "WITHDRAWN": "已撤回",
        "EXECUTED": "已执行", "FAILED": "执行失败",
        "SPLIT_PENDING": "待拆分",
    }
    RISK_LABELS = {"LOW": "低", "MEDIUM": "中", "HIGH": "高"}


class MpiMergeRequestItem(Base):
    """合并申请明细"""
    __tablename__ = "mpi_merge_request_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merge_request_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_role: Mapped[str] = mapped_column(String(16), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    business_summary: Mapped[Optional[dict]] = mapped_column(JSONB)
    impact_detail: Mapped[Optional[dict]] = mapped_column(JSONB)
    snapshot_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    request: Mapped["MpiMergeRequest"] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("merge_request_id", "patient_role",
                         name="uk_mpi_merge_item"),
        Index("idx_mpi_merge_item_patient", "patient_id"),
        {"comment": "合并申请明细"},
    )


class MpiMergeApproval(Base):
    """合并审批节点"""
    __tablename__ = "mpi_merge_approval"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merge_request_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    node_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    approver_name: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="WAITING", nullable=False)
    opinion: Mapped[Optional[str]] = mapped_column(String(500))
    signature_url: Mapped[Optional[str]] = mapped_column(String(255))
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    wait_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    transfer_from: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    request: Mapped["MpiMergeRequest"] = relationship(back_populates="approvals")

    __table_args__ = (
        Index("idx_mpi_merge_approval_req", "merge_request_id", "node_seq"),
        Index("idx_mpi_merge_approval_approver", "approver_id", "status"),
        {"comment": "合并审批节点"},
    )


class MpiMergeLog(Base):
    """合并执行日志"""
    __tablename__ = "mpi_merge_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merge_no: Mapped[str] = mapped_column(String(32), nullable=False)
    merge_request_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    primary_patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    secondary_patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    primary_empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    secondary_empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    version_snapshot_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    redirect_items_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    redirect_status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    redirect_success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    redirect_fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    redirect_retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    executed_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    executed_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    executed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    result: Mapped[str] = mapped_column(String(16), default="SUCCESS", nullable=False)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    detail_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_mpi_merge_log_no", "merge_no"),
        Index("idx_mpi_merge_log_primary", "primary_patient_id", "executed_at"),
        Index("idx_mpi_merge_log_secondary", "secondary_patient_id", "executed_at"),
        Index("idx_mpi_merge_log_status", "redirect_status", "created_at"),
        Index("idx_mpi_merge_log_time", "created_at"),
        {"comment": "合并执行日志（月度分区）"},
    )


class MpiSplitLog(Base):
    """拆分日志"""
    __tablename__ = "mpi_split_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    split_no: Mapped[str] = mapped_column(String(32), nullable=False)
    merge_log_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    merge_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    current_merge_to_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    reason_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reason_desc: Mapped[str] = mapped_column(String(500), nullable=False)
    attachment_ids: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    current_approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    executed_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    work_order_no: Mapped[Optional[str]] = mapped_column(String(32))
    result: Mapped[str] = mapped_column(String(16), default="SUCCESS", nullable=False)
    error_msg: Mapped[Optional[str]] = mapped_column(String(1000))
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("split_no", "is_deleted", name="uk_mpi_split_no"),
        Index("idx_mpi_split_patient", "patient_id", "created_at"),
        Index("idx_mpi_split_merge", "merge_log_id"),
        Index("idx_mpi_split_status", "status", "created_at"),
        Index("idx_mpi_split_approver", "current_approver_id", "status"),
        {"comment": "拆分日志（月度分区）"},
    )


class MpiPatientVersion(Base):
    """患者版本快照"""
    __tablename__ = "mpi_patient_version"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    version_type: Mapped[str] = mapped_column(String(32), nullable=False)
    version_seq: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    snapshot_hash: Mapped[Optional[str]] = mapped_column(String(128))
    source_ref: Mapped[Optional[str]] = mapped_column(String(64))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_id", "version_type", "version_seq", "is_deleted",
                         name="uk_mpi_patient_version"),
        Index("idx_mpi_patient_version_patient", "patient_id", "created_at"),
        Index("idx_mpi_patient_version_source", "source_ref"),
        {"comment": "患者版本快照"},
    )


class MpiQualityRule(Base, TimestampMixin, SoftDeleteMixin):
    """质量规则"""
    __tablename__ = "mpi_quality_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dimension: Mapped[str] = mapped_column(String(16), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), default="PATIENT", nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="WARN", nullable=False)
    condition_expr: Mapped[dict] = mapped_column(JSONB, nullable=False)
    threshold: Mapped[Optional[str]] = mapped_column(String(64))
    suggestion: Mapped[Optional[str]] = mapped_column(String(500))
    auto_fix: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("rule_code", "is_deleted", name="uk_mpi_quality_rule_code"),
        Index("idx_mpi_quality_rule_dim", "dimension", "is_enabled"),
        Index("idx_mpi_quality_rule_object", "object_type", "is_enabled"),
        {"comment": "质量规则"},
    )


class MpiQualityResult(Base):
    """质量扫描结果"""
    __tablename__ = "mpi_quality_result"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    scan_no: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rule_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_name: Mapped[Optional[str]] = mapped_column(String(128))
    dimension: Mapped[str] = mapped_column(String(16), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    field_name: Mapped[Optional[str]] = mapped_column(String(64))
    field_value_mask: Mapped[Optional[str]] = mapped_column(String(255))
    issue_desc: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(16), default="OPEN", nullable=False)
    assignee_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    assignee_name: Mapped[Optional[str]] = mapped_column(String(64))
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolve_note: Mapped[Optional[str]] = mapped_column(String(500))
    scan_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_mpi_quality_scan", "scan_no", "rule_code"),
        Index("idx_mpi_quality_patient", "patient_id", "status"),
        Index("idx_mpi_quality_rule", "rule_id", "status"),
        Index("idx_mpi_quality_dim", "dimension", "status"),
        Index("idx_mpi_quality_status", "status", "created_at"),
        Index("idx_mpi_quality_assignee", "assignee_id", "status"),
        {"comment": "质量扫描结果（月度分区）"},
    )


class MpiPatientBlocklist(Base):
    """患者黑名单"""
    __tablename__ = "mpi_patient_blocklist"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    block_type: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    release_reason: Mapped[Optional[str]] = mapped_column(String(500))
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_mpi_blocklist_patient", "patient_id", "status"),
        Index("idx_mpi_blocklist_status", "status", "expire_date"),
        Index("idx_mpi_blocklist_type", "block_type", "status"),
        {"comment": "患者黑名单"},
    )

    TYPE_LABELS = {"NO_MERGE": "禁止合并", "NO_REFERENCE": "禁止引用", "BOTH": "均禁止"}

    @property
    def type_label(self) -> str:
        return self.TYPE_LABELS.get(self.block_type, self.block_type)
```

### 4.16 Pydantic Schema 定义

```python
# app/schemas/mpi/dedup.py
"""患者匹配合并与质量 Pydantic Schema"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal, Any

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


MATCH_LEVEL = Literal["HIGH", "MEDIUM", "LOW", "NONE"]
MATCH_SOURCE = Literal["REGISTRATION", "BATCH", "MANUAL"]
CANDIDATE_STATUS = Literal["PENDING", "CONFIRMED", "IGNORED", "IN_MERGE", "MERGED", "DELETED"]
MERGE_RISK = Literal["LOW", "MEDIUM", "HIGH"]
MERGE_STATUS = Literal["DRAFT", "PENDING", "APPROVED", "REJECTED", "WITHDRAWN",
                        "EXECUTED", "FAILED", "SPLIT_PENDING"]
SPLIT_REASON = Literal["MISJUDGED", "SYSTEM_ERROR", "PATIENT_REQUEST", "OTHER"]
QUALITY_DIM = Literal["COMPLETENESS", "UNIQUENESS", "FORMAT", "TIMELINESS", "REFERENCE"]
QUALITY_SEVERITY = Literal["ERROR", "WARN", "INFO"]
QUALITY_OBJ = Literal["PATIENT", "IDENTIFIER", "CONTACT", "ADDRESS", "RELATION"]
QUALITY_STATUS = Literal["OPEN", "ASSIGNED", "RESOLVED", "IGNORED"]
BLOCK_TYPE = Literal["NO_MERGE", "NO_REFERENCE", "BOTH"]


# ==================== 候选 ====================
class CandidateQuery(BaseModel):
    keyword: Optional[str] = None
    level: Optional[List[MATCH_LEVEL]] = None
    status: Optional[List[CANDIDATE_STATUS]] = None
    source: Optional[List[MATCH_SOURCE]] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class CandidatePatientItem(BaseModel):
    id: int
    empi_no: str
    patient_name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None


class CandidateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_a: CandidatePatientItem
    patient_b: CandidatePatientItem
    total_score: Decimal
    level: str
    source: str
    status: str
    created_at: Optional[datetime] = None


class FieldScoreItem(BaseModel):
    field: str
    score: float
    weight: float
    contribution: float
    algorithm: Optional[str] = None


class ImpactSummary(BaseModel):
    outpatient_count: int = 0
    inpatient_count: int = 0
    charge_count: int = 0
    charge_amount: Decimal = Decimal("0.00")
    optometry_count: int = 0
    refractive_count: int = 0


class CandidateDetail(CandidateListItem):
    field_scores: List[FieldScoreItem] = []
    hit_fields: List[str] = []
    handle_note: Optional[str] = None
    handled_at: Optional[datetime] = None
    impact: Optional[dict] = None


class CandidateHandleRequest(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


class BatchMatchRequest(BaseModel):
    rule_code: str = Field("BATCH", max_length=32)
    scope_type: Literal["ALL", "RECENT", "DEPT", "SOURCE"] = "ALL"
    scope_value: Optional[str] = Field(None, max_length=255)
    max_rows: Optional[int] = Field(None, ge=1, le=1000000)


# ==================== 合并申请 ====================
class MergeRequestCreate(BaseModel):
    primary_patient_id: int
    secondary_patient_id: int
    candidate_id: Optional[int] = None
    reason: str = Field(..., min_length=10, max_length=500)
    attachment_ids: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_pair(self):
        if self.primary_patient_id == self.secondary_patient_id:
            raise ValueError("主从患者不能相同")
        return self


class MergeExecuteRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    second_factor_token: Optional[str] = Field(None, max_length=32)


class MergeApprovalRequest(BaseModel):
    opinion: Optional[str] = Field(None, max_length=500)
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_opinion(self):
        # 驳回意见必填，此处只做建议校验，具体由接口层判断
        return self


class MergeRequestItem(BaseModel):
    id: int
    merge_no: str
    primary_patient_id: int
    secondary_patient_id: int
    primary_empi_no: Optional[str] = None
    secondary_empi_no: Optional[str] = None
    risk_level: str
    status: str
    current_node: Optional[str] = None
    current_approver_id: Optional[int] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class MergeApprovalNode(BaseModel):
    node_seq: int
    node_name: str
    approver_name: Optional[str] = None
    status: str
    opinion: Optional[str] = None
    handled_at: Optional[datetime] = None
    wait_hours: Optional[Decimal] = None


class MergeRequestDetail(MergeRequestItem):
    reason: str
    attachment_ids: List[int] = []
    impact_json: Optional[dict] = None
    approval_chain: List[str] = []
    items: List[dict] = []
    approvals: List[MergeApprovalNode] = []
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    executed_by: Optional[int] = None
    merge_log_id: Optional[int] = None
    version_no: int = 1


# ==================== 合并记录 ====================
class RedirectItem(BaseModel):
    table_name: str
    subscriber: Optional[str] = None
    count: int = 0
    ids: List[int] = []
    id_field: str = "id"
    patient_field: str = "patient_id"
    status: Optional[str] = None
    fail_ids: List[int] = []
    fail_reason: Optional[str] = None
    finished_at: Optional[datetime] = None


class MergeLogItem(BaseModel):
    id: int
    merge_no: str
    primary_patient_id: int
    secondary_patient_id: int
    result: str
    redirect_status: str
    executed_by_name: Optional[str] = None
    executed_at: Optional[datetime] = None


class MergeLogDetail(MergeLogItem):
    version_snapshot_id: Optional[int] = None
    redirect_items: List[RedirectItem] = []
    redirect_success_count: int = 0
    redirect_fail_count: int = 0
    redirect_retry_count: int = 0
    error_msg: Optional[str] = None


class RedirectReportRequest(BaseModel):
    subscriber: str = Field(..., max_length=32)
    table_name: str = Field(..., max_length=128)
    status: Literal["COMPLETED", "PARTIAL", "FAILED"]
    success_ids: List[int] = []
    fail_ids: List[int] = []
    fail_reason: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_report(self):
        if self.status == "PARTIAL" and not self.fail_ids:
            raise ValueError("部分完成必须提供失败 ID")
        if self.status == "FAILED" and not self.fail_reason:
            raise ValueError("失败必须提供原因")
        return self


# ==================== 拆分 ====================
class SplitCreateRequest(BaseModel):
    merge_log_id: int
    reason_type: SPLIT_REASON
    reason_desc: str = Field(..., min_length=10, max_length=500)
    attachment_ids: Optional[List[int]] = None


class SplitExecuteRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    second_factor_token: Optional[str] = Field(None, max_length=32)


class SplitRequestItem(BaseModel):
    id: int
    split_no: str
    merge_log_id: int
    patient_id: int
    empi_no: Optional[str] = None
    reason_type: str
    status: str
    current_approver_id: Optional[int] = None
    created_at: Optional[datetime] = None


# ==================== 质量 ====================
class QualityRuleCreate(BaseModel):
    rule_code: str = Field(..., max_length=32)
    rule_name: str = Field(..., min_length=1, max_length=128)
    dimension: QUALITY_DIM
    object_type: QUALITY_OBJ = "PATIENT"
    severity: QUALITY_SEVERITY = "WARN"
    condition_expr: dict
    threshold: Optional[str] = Field(None, max_length=64)
    suggestion: Optional[str] = Field(None, max_length=500)
    sort_no: int = 999
    description: Optional[str] = Field(None, max_length=500)


class QualityRuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=128)
    severity: Optional[QUALITY_SEVERITY] = None
    condition_expr: Optional[dict] = None
    threshold: Optional[str] = Field(None, max_length=64)
    suggestion: Optional[str] = Field(None, max_length=500)
    is_enabled: Optional[bool] = None
    sort_no: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)


class QualityScanRequest(BaseModel):
    rule_codes: Optional[List[str]] = None
    scope_type: Literal["ALL", "RECENT", "DEPT"] = "ALL"
    scope_value: Optional[str] = Field(None, max_length=255)


class QualityIssueQuery(BaseModel):
    dimension: Optional[List[QUALITY_DIM]] = None
    severity: Optional[List[QUALITY_SEVERITY]] = None
    status: Optional[List[QUALITY_STATUS]] = None
    rule_code: Optional[str] = None
    assignee_id: Optional[int] = None
    patient_keyword: Optional[str] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class QualityIssueItem(BaseModel):
    id: int
    scan_no: str
    rule_code: str
    rule_name: Optional[str] = None
    dimension: str
    severity: str
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    field_name: Optional[str] = None
    issue_desc: Optional[str] = None
    status: str
    assignee_name: Optional[str] = None
    created_at: Optional[datetime] = None


class QualityIssueAssign(BaseModel):
    issue_ids: List[int] = Field(..., min_length=1, max_length=1000)
    assignee_id: int
    note: Optional[str] = Field(None, max_length=500)


class QualityIssueResolve(BaseModel):
    resolve_note: Optional[str] = Field(None, max_length=500)


class QualityDashboard(BaseModel):
    scan_time: Optional[datetime] = None
    total_patients: int = 0
    issue_patients: int = 0
    issue_rate: Decimal = Decimal("0.00")
    open_issues: int = 0
    resolved_issues: int = 0
    by_dimension: dict = {}
    trend: List[dict] = []
    top_issues: List[dict] = []


# ==================== 黑名单 ====================
class BlocklistCreate(BaseModel):
    patient_id: int
    block_type: BLOCK_TYPE = "NO_MERGE"
    reason: str = Field(..., min_length=10, max_length=500)
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_date and self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("失效日期必须晚于生效日期")
        return self


class BlocklistRelease(BaseModel):
    release_reason: str = Field(..., min_length=5, max_length=500)


class BlocklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    block_type: str
    reason: str
    status: str
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


# ==================== 配置 ====================
class DedupConfigUpdate(BaseModel):
    instant_match_enabled: bool = True
    instant_match_limit: int = Field(5, ge=1, le=20)
    instant_match_min_level: Literal["HIGH", "MEDIUM"] = "MEDIUM"
    batch_match_enabled: bool = True
    batch_match_cron: str = Field("0 3 * * *", max_length=32)
    batch_match_max_rows: int = Field(100000, ge=1, le=1000000)
    threshold_high: Decimal = Field(Decimal("95.00"), ge=0, le=100)
    threshold_medium: Decimal = Field(Decimal("80.00"), ge=0, le=100)
    threshold_low: Decimal = Field(Decimal("60.00"), ge=0, le=100)
    candidate_expire_days: int = Field(90, ge=1, le=3650)
    merge_second_factor: bool = True
    split_second_factor: bool = True
    risk_low_doc_limit: int = Field(10, ge=0)
    risk_low_amount_limit: Decimal = Field(Decimal("1000.00"), ge=0)
    risk_medium_doc_limit: int = Field(100, ge=0)
    risk_medium_amount_limit: Decimal = Field(Decimal("50000.00"), ge=0)
    redirect_max_ids_per_item: int = Field(1000, ge=1, le=10000)
    redirect_retry_limit: int = Field(5, ge=0, le=20)
    quality_scan_cron: str = Field("0 2 * * *", max_length=32)
    quality_sla_days: int = Field(7, ge=1, le=90)
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_config(self):
        if not (self.threshold_high > self.threshold_medium > self.threshold_low):
            raise ValueError("阈值必须满足 高 > 中 > 低")
        if self.risk_low_doc_limit >= self.risk_medium_doc_limit:
            raise ValueError("LOW 风险单据上限应小于 MEDIUM")
        if self.risk_low_amount_limit >= self.risk_medium_amount_limit:
            raise ValueError("LOW 风险金额上限应小于 MEDIUM")
        return self


class DedupConfigDetail(DedupConfigUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int = 1
    updated_at: Optional[datetime] = None


# ==================== 内部契约 ====================
class InstantMatchRequest(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=64)
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    id_type: Optional[str] = None
    id_no: Optional[str] = Field(None, max_length=64)
    phone: Optional[str] = Field(None, max_length=20)
    limit: int = Field(5, ge=1, le=20)


class InstantMatchCandidate(BaseModel):
    patient_id: int
    empi_no: str
    patient_name: str
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    primary_id_mask: Optional[str] = None
    primary_phone_mask: Optional[str] = None
    total_score: Decimal
    level: str
    hit_fields: List[str] = []


class InstantMatchResult(BaseModel):
    candidates: List[InstantMatchCandidate] = []


class MergeStatusResult(BaseModel):
    patient_id: int
    empi_no: Optional[str] = None
    status: str
    merge_to_id: Optional[int] = None
    merge_to_empi_no: Optional[str] = None
    merged_at: Optional[datetime] = None
    merge_log_id: Optional[int] = None


class BlocklistCheckResult(BaseModel):
    patient_id: int
    blocked: bool
    block_type: Optional[str] = None
    reason: Optional[str] = None


class QualityIssueSummary(BaseModel):
    scan_time: Optional[datetime] = None
    total_patients: int = 0
    issue_patients: int = 0
    issue_rate: Decimal = Decimal("0.00")
    open_issues: int = 0
    resolved_issues: int = 0
    by_dimension: dict = {}


# 前向引用
CandidateDetail.model_rebuild()
MergeRequestDetail.model_rebuild()
MergeLogDetail.model_rebuild()
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：13 张表 | 系统设计组 |