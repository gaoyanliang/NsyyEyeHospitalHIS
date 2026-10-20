# 二级眼科医院 HIS 系统 — M03 患者服务与EMPI
# 子模块数据结构：随访

**文档版本：** V1.0
**所属模块：** M03 患者服务与EMPI
**子模块：** 随访（Follow-up）
**主数据域：** 患者域（`MPI`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M03 患者服务与EMPI 04 随访 详细设计》《M01 主数据管理MDM》《M02 统一权限与安全》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「随访」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[随访详细设计](M03_患者服务与EMPI_04_随访_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [随访详细设计](M03_患者服务与EMPI_04_随访_详细设计.md)
- [数据结构设计汇总](M03_患者服务与EMPI_数据结构设计汇总.md)
- [01 患者主索引与建档数据结构](M03_患者服务与EMPI_01_患者主索引与建档_数据结构.md)
- [02 患者匹配合并与质量数据结构](M03_患者服务与EMPI_02_患者匹配合并与质量_数据结构.md)
- [03 会员数据结构](M03_患者服务与EMPI_03_会员_数据结构.md)
- [M01 数据结构设计汇总](../M01主数据管理MDM/M01_主数据管理MDM_数据结构设计汇总.md)
- [M02 账号管理数据结构](../M02统一权限与安全/M02_统一权限与安全_01_账号管理_数据结构.md)
- [M02 审计日志数据结构](../M02统一权限与安全/M02_统一权限与安全_06_审计日志_数据结构.md)

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 10 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`mpi_followup_config`（随访配置表）](#42-表mpi_followup_config随访配置表)
- [4.3 表：`mpi_followup_template`（随访模板表）](#43-表mpi_followup_template随访模板表)
- [4.4 表：`mpi_followup_template_node`（模板节点表）](#44-表mpi_followup_template_node模板节点表)
- [4.5 表：`mpi_followup_template_log`（模板变更日志表）](#45-表mpi_followup_template_log模板变更日志表)
- [4.6 表：`mpi_followup_plan`（随访计划表）](#46-表mpi_followup_plan随访计划表)
- [4.7 表：`mpi_followup_task`（随访任务表）](#47-表mpi_followup_task随访任务表)
- [4.8 表：`mpi_followup_task_log`（任务状态日志表）](#48-表mpi_followup_task_log任务状态日志表)
- [4.9 表：`mpi_followup_plan_log`（计划变更日志表）](#49-表mpi_followup_plan_log计划变更日志表)
- [4.10 表：`mpi_followup_assign_rule`（分派规则表）](#410-表mpi_followup_assign_rule分派规则表)
- [4.11 表：`mpi_followup_code_seq`（编码序列表）](#411-表mpi_followup_code_seq编码序列表)
- [4.12 SQLAlchemy 2.0 模型定义](#412-sqlalchemy-20-模型定义)
- [4.13 Pydantic Schema 定义](#413-pydantic-schema-定义)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `mpi_followup_config` | 随访配置表（单行） |
| 4.3 | `mpi_followup_template` | 随访模板表 |
| 4.4 | `mpi_followup_template_node` | 模板节点表 |
| 4.5 | `mpi_followup_template_log` | 模板变更日志表 |
| 4.6 | `mpi_followup_plan` | 随访计划表 |
| 4.7 | `mpi_followup_task` | 随访任务表 |
| 4.8 | `mpi_followup_task_log` | 任务状态日志表 |
| 4.9 | `mpi_followup_plan_log` | 计划变更日志表 |
| 4.10 | `mpi_followup_assign_rule` | 分派规则表 |
| 4.11 | `mpi_followup_code_seq` | 编码序列表 |

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

配置与模板：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_followup_config          │  │ mpi_followup_template        │
│ （随访配置，单行）             │  │ （随访模板）                  │
└──────────────────────────────┘  └──────────┬───────────────────┘
                                             │ 1:N
                                             ▼
                                  ┌──────────────────────────────┐
                                  │ mpi_followup_template_node   │
                                  │ （模板节点）                  │
                                  └──────────────────────────────┘

计划与任务：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_followup_plan            │──►│ mpi_followup_task            │
│ （随访计划）                  │  │ （随访任务）                  │
└──────────┬───────────────────┘  └──────────┬───────────────────┘
           │ 1:N                              │ 1:N
           ▼                                  ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_followup_plan_log        │  │ mpi_followup_task_log        │
│ （计划变更日志，月分区）       │  │ （任务状态日志，月分区）       │
└──────────────────────────────┘  └──────────────────────────────┘

模板日志与规则：
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ mpi_followup_template_log    │  │ mpi_followup_assign_rule     │
│ （模板变更日志，月分区）       │  │ （分派规则）                  │
└──────────────────────────────┘  └──────────────────────────────┘

编码：
┌──────────────────────────────┐
│ mpi_followup_code_seq        │
│ （模板/计划/任务编码序列）     │
└──────────────────────────────┘
```

**说明：**

- 所有表统一 `mpi_` 前缀，逻辑删除统一 `is_deleted BOOLEAN DEFAULT FALSE`。
- 状态统一 `VARCHAR(16)`，大写英文枚举。
- 跨模块逻辑引用不建物理外键。
- 日志表按 `created_at` 月度 RANGE 分区。
- 任务表冗余患者姓名、手机号掩码、模板名称，避免 M19 拉取时频繁 JOIN。

### 4.2 表：`mpi_followup_config`（随访配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| template_prefix | VARCHAR(8) | N | 'FT' | 模板编码前缀 |
| plan_prefix | VARCHAR(8) | N | 'FP' | 计划编码前缀 |
| task_prefix | VARCHAR(8) | N | 'FTK' | 任务编码前缀 |
| seq_len | INT | N | 4 | 流水位数 |
| advance_days | INT | N | 30 | 任务提前可执行天数 |
| overdue_days | INT | N | 7 | 逾期判定天数 |
| cycle_max_occurrences | INT | N | 24 | 周期任务最大次数 |
| default_assign_rule_code | VARCHAR(32) | Y | 'BY_DEPT' | 默认分派规则 |
| default_exec_dept_id | BIGINT | Y | NULL | 默认执行科室 |
| notify_on_assign | BOOLEAN | N | TRUE | 分派后通知 |
| notify_channel | VARCHAR(32) | N | 'INBOX,SMS' | 通知渠道 |
| subscribe_patient_merge | BOOLEAN | N | TRUE | 订阅患者合并事件 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人（`sys_account.id`） |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_mpi_followup_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE mpi_followup_config
    ADD CONSTRAINT ck_mpi_followup_config_single_row CHECK (id = 1);
```

### 4.3 表：`mpi_followup_template`（随访模板表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| template_code | VARCHAR(32) | N | - | 模板编码 `FT+场景+流水` |
| template_name | VARCHAR(128) | N | - | 模板名称 |
| scene | VARCHAR(32) | N | - | 适用场景：SURGERY/DISCHARGE/CHRONIC/SATISFACTION/OTHER |
| apply_operation_ids | VARCHAR(1000) | Y | NULL | 适用手术项目 ID 列表 |
| apply_diagnosis_ids | VARCHAR(1000) | Y | NULL | 适用诊断 ID 列表 |
| apply_dept_ids | VARCHAR(1000) | Y | NULL | 适用科室 ID 列表 |
| member_level_limit | VARCHAR(255) | Y | NULL | 会员等级限制（逗号分隔，空=不限） |
| trigger_type | VARCHAR(32) | N | - | 默认触发方式 |
| node_count | INT | N | 0 | 节点数（冗余） |
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
| pk_mpi_followup_template | PRIMARY | id | 主键 |
| uk_mpi_followup_template_code | UNIQUE | template_code, is_deleted | 模板编码唯一 |
| idx_mpi_followup_template_scene | NORMAL | scene, status | 按场景 |
| idx_mpi_followup_template_status | NORMAL | status, created_at | 按状态 |

**约束说明**

```sql
ALTER TABLE mpi_followup_template
    ADD CONSTRAINT ck_mpi_followup_template_scene
    CHECK (scene IN ('SURGERY', 'DISCHARGE', 'CHRONIC', 'SATISFACTION', 'OTHER'));

ALTER TABLE mpi_followup_template
    ADD CONSTRAINT ck_mpi_followup_template_status
    CHECK (status IN ('DRAFT', 'ENABLED', 'DISABLED'));
```

### 4.4 表：`mpi_followup_template_node`（模板节点表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(32) | N | - | 模板编码（冗余） |
| node_seq | INT | N | - | 节点序号 |
| node_name | VARCHAR(64) | N | - | 节点名称 |
| trigger_type | VARCHAR(32) | N | - | 触发方式 |
| offset_days | INT | N | 0 | 偏移天数（可为负） |
| cycle_days | INT | Y | NULL | 周期天数（CYCLE） |
| max_occurrences | INT | Y | NULL | 最大次数（CYCLE） |
| followup_methods | VARCHAR(255) | N | - | 随访方式（逗号分隔） |
| content_json | JSONB | Y | NULL | 随访内容（问卷/检查项/用药提醒） |
| exec_dept_id | BIGINT | N | - | 执行科室 |
| exec_staff_requirement | VARCHAR(32) | Y | NULL | 执行人要求：SURGEON/ATTENDING/ANY |
| assign_rule_code | VARCHAR(32) | Y | NULL | 分派规则编码 |
| priority | VARCHAR(16) | N | 'NORMAL' | HIGH/NORMAL/LOW |
| is_required | BOOLEAN | N | TRUE | 是否必做 |
| advance_days | INT | Y | NULL | 覆盖全局提前天数 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_followup_node(template_id, node_seq, is_deleted)` 唯一；`idx_mpi_followup_node_template(template_id)`；`idx_mpi_followup_node_trigger(trigger_type)`。

**约束说明**

```sql
ALTER TABLE mpi_followup_template_node
    ADD CONSTRAINT ck_mpi_followup_node_trigger
    CHECK (trigger_type IN ('SURGERY_DATE', 'DISCHARGE_DATE', 'REGISTER_DATE',
                             'DIAGNOSIS_DATE', 'FIXED_DATE', 'CYCLE'));

ALTER TABLE mpi_followup_template_node
    ADD CONSTRAINT ck_mpi_followup_node_priority
    CHECK (priority IN ('HIGH', 'NORMAL', 'LOW'));

ALTER TABLE mpi_followup_template_node
    ADD CONSTRAINT ck_mpi_followup_node_cycle
    CHECK (trigger_type <> 'CYCLE' OR (cycle_days IS NOT NULL AND max_occurrences IS NOT NULL));
```

### 4.5 表：`mpi_followup_template_log`（模板变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(32) | Y | NULL | 模板编码 |
| action | VARCHAR(32) | N | - | CREATE/UPDATE/ENABLE/DISABLE/COPY/DELETE |
| before_json | JSONB | Y | NULL | 变更前快照 |
| after_json | JSONB | Y | NULL | 变更后快照 |
| detail | VARCHAR(1000) | Y | NULL | 操作详情 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_mpi_followup_tpl_log_template(template_id, created_at)`；`idx_mpi_followup_tpl_log_action(action, created_at)`；`idx_mpi_followup_tpl_log_time(created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**。

### 4.6 表：`mpi_followup_plan`（随访计划表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| plan_no | VARCHAR(32) | N | - | 计划号 `FP+yyyyMMdd+流水` |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | 患者 EMPI（冗余） |
| patient_name | VARCHAR(64) | Y | NULL | 患者姓名（冗余） |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码（冗余） |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(32) | N | - | 模板编码（冗余） |
| template_name | VARCHAR(128) | Y | NULL | 模板名称（冗余） |
| source | VARCHAR(32) | N | - | 来源：SURGERY/DISCHARGE/REGISTER/DIAGNOSIS/MANUAL/IMPORT |
| trigger_type | VARCHAR(32) | N | - | 触发方式 |
| base_date | DATE | N | - | 基准日期 |
| biz_no | VARCHAR(64) | Y | NULL | 关联业务单号（手术/出院/诊断） |
| status | VARCHAR(16) | N | 'DRAFT' | DRAFT/ACTIVE/COMPLETED/CANCELLED |
| task_count | INT | N | 0 | 任务总数（冗余） |
| completed_count | INT | N | 0 | 已完成任务数（冗余） |
| cancelled_reason | VARCHAR(500) | Y | NULL | 取消原因 |
| cancelled_at | TIMESTAMP | Y | NULL | 取消时间 |
| completed_at | TIMESTAMP | Y | NULL | 完成时间 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| org_id | BIGINT | N | 1 | 院区 ID |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_followup_plan | PRIMARY | id | 主键 |
| uk_mpi_followup_plan_no | UNIQUE | plan_no, is_deleted | 计划号唯一 |
| idx_mpi_followup_plan_patient | NORMAL | patient_id, status | 按患者 |
| idx_mpi_followup_plan_template | NORMAL | template_code, status | 按模板 |
| idx_mpi_followup_plan_status | NORMAL | status, created_at | 按状态 |
| idx_mpi_followup_plan_base | NORMAL | base_date | 按基准日期 |
| idx_mpi_followup_plan_biz | NORMAL | biz_no | 按业务单号 |

**约束说明**

```sql
ALTER TABLE mpi_followup_plan
    ADD CONSTRAINT ck_mpi_followup_plan_status
    CHECK (status IN ('DRAFT', 'ACTIVE', 'COMPLETED', 'CANCELLED'));

ALTER TABLE mpi_followup_plan
    ADD CONSTRAINT ck_mpi_followup_plan_source
    CHECK (source IN ('SURGERY', 'DISCHARGE', 'REGISTER', 'DIAGNOSIS',
                       'MANUAL', 'IMPORT'));
```

### 4.7 表：`mpi_followup_task`（随访任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_no | VARCHAR(32) | N | - | 任务号 `FTK+yyyyMMdd+流水` |
| plan_id | BIGINT | N | - | 计划 ID |
| plan_no | VARCHAR(32) | Y | NULL | 计划号（冗余） |
| patient_id | BIGINT | N | - | 患者 ID |
| empi_no | VARCHAR(32) | Y | NULL | EMPI（冗余） |
| patient_name | VARCHAR(64) | Y | NULL | 患者姓名（冗余） |
| phone_mask | VARCHAR(32) | Y | NULL | 手机号掩码（冗余） |
| template_id | BIGINT | N | - | 模板 ID |
| template_code | VARCHAR(32) | N | - | 模板编码（冗余） |
| node_seq | INT | N | - | 模板节点序号 |
| node_name | VARCHAR(64) | N | - | 节点名称（快照） |
| occurrence | INT | N | 1 | 周期任务第几次 |
| trigger_type | VARCHAR(32) | N | - | 触发方式（快照） |
| offset_days | INT | N | 0 | 偏移天数（快照） |
| plan_date | DATE | N | - | 计划执行日期 |
| followup_methods | VARCHAR(255) | N | - | 随访方式（快照） |
| content_json | JSONB | Y | NULL | 随访内容（快照） |
| exec_dept_id | BIGINT | N | - | 执行科室 |
| exec_dept_name | VARCHAR(128) | Y | NULL | 执行科室名称（冗余） |
| assignee_id | BIGINT | Y | NULL | 分派人 ID |
| assignee_name | VARCHAR(64) | Y | NULL | 分派人姓名 |
| assign_rule_code | VARCHAR(32) | Y | NULL | 分派规则 |
| priority | VARCHAR(16) | N | 'NORMAL' | HIGH/NORMAL/LOW |
| is_required | BOOLEAN | N | TRUE | 是否必做 |
| status | VARCHAR(16) | N | 'PENDING' | PENDING/ASSIGNED/EXECUTING/COMPLETED/CANCELLED/OVERDUE/FAILED |
| assigned_at | TIMESTAMP | Y | NULL | 分派时间 |
| started_at | TIMESTAMP | Y | NULL | 开始执行时间 |
| completed_at | TIMESTAMP | Y | NULL | 完成时间 |
| executed_by | BIGINT | Y | NULL | 执行人（M19 回写） |
| executed_by_name | VARCHAR(64) | Y | NULL | 执行人姓名 |
| result_summary | VARCHAR(1000) | Y | NULL | 结果摘要（M19 回写） |
| fail_reason | VARCHAR(500) | Y | NULL | 失败原因 |
| cancelled_reason | VARCHAR(500) | Y | NULL | 取消原因 |
| version_no | INT | N | 1 | 乐观锁版本号 |
| org_id | BIGINT | N | 1 | 院区 ID |
| remark | VARCHAR(500) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_mpi_followup_task | PRIMARY | id | 主键 |
| uk_mpi_followup_task_no | UNIQUE | task_no, is_deleted | 任务号唯一 |
| idx_mpi_followup_task_plan | NORMAL | plan_id, status | 按计划 |
| idx_mpi_followup_task_patient | NORMAL | patient_id, status | 按患者 |
| idx_mpi_followup_task_dept | NORMAL | exec_dept_id, status, plan_date | 按科室待执行 |
| idx_mpi_followup_task_assignee | NORMAL | assignee_id, status, plan_date | 按分派人 |
| idx_mpi_followup_task_date | NORMAL | plan_date, status | 按日期 |
| idx_mpi_followup_task_status | NORMAL | status, created_at | 按状态 |

**约束说明**

```sql
ALTER TABLE mpi_followup_task
    ADD CONSTRAINT ck_mpi_followup_task_status
    CHECK (status IN ('PENDING', 'ASSIGNED', 'EXECUTING', 'COMPLETED',
                       'CANCELLED', 'OVERDUE', 'FAILED'));

ALTER TABLE mpi_followup_task
    ADD CONSTRAINT ck_mpi_followup_task_priority
    CHECK (priority IN ('HIGH', 'NORMAL', 'LOW'));
```

### 4.8 表：`mpi_followup_task_log`（任务状态日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| task_id | BIGINT | N | - | 任务 ID |
| task_no | VARCHAR(32) | Y | NULL | 任务号（冗余） |
| action | VARCHAR(32) | N | - | CREATE/ASSIGN/START/COMPLETE/FAIL/OVERDUE/CANCEL/MERGE_CONFLICT |
| before_status | VARCHAR(16) | Y | NULL | 变更前状态 |
| after_status | VARCHAR(16) | Y | NULL | 变更后状态 |
| detail | VARCHAR(1000) | Y | NULL | 详情 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_mpi_followup_task_log_task(task_id, created_at)`；`idx_mpi_followup_task_log_action(action, created_at)`；`idx_mpi_followup_task_log_time(created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**。

### 4.9 表：`mpi_followup_plan_log`（计划变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| plan_id | BIGINT | N | - | 计划 ID |
| plan_no | VARCHAR(32) | Y | NULL | 计划号（冗余） |
| action | VARCHAR(32) | N | - | CREATE/ACTIVATE/CANCEL/COMPLETE/MERGE_REDIRECT/UPDATE |
| before_json | JSONB | Y | NULL | 变更前快照 |
| after_json | JSONB | Y | NULL | 变更后快照 |
| detail | VARCHAR(1000) | Y | NULL | 详情 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_mpi_followup_plan_log_plan(plan_id, created_at)`；`idx_mpi_followup_plan_log_action(action, created_at)`；`idx_mpi_followup_plan_log_time(created_at)`。

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **5 年**。

### 4.10 表：`mpi_followup_assign_rule`（分派规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| rule_code | VARCHAR(32) | N | - | 规则编码 |
| rule_name | VARCHAR(128) | N | - | 规则名称 |
| rule_type | VARCHAR(32) | N | - | BY_DEPT/BY_DOCTOR/BY_GROUP/ROUND_ROBIN/MANUAL |
| exec_dept_id | BIGINT | Y | NULL | 执行科室（BY_DEPT/BY_GROUP） |
| group_id | BIGINT | Y | NULL | 用户组 ID（BY_GROUP，M01 `md_user_group`） |
| round_robin_staff_ids | VARCHAR(1000) | Y | NULL | 轮询人员 ID 列表 |
| priority | INT | N | 999 | 优先级 |
| is_enabled | BOOLEAN | N | TRUE | 是否启用 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引：** `uk_mpi_followup_assign_rule_code(rule_code, is_deleted)` 唯一；`idx_mpi_followup_assign_rule_type(rule_type, is_enabled)`；`idx_mpi_followup_assign_rule_priority(priority, is_enabled)`。

**约束说明**

```sql
ALTER TABLE mpi_followup_assign_rule
    ADD CONSTRAINT ck_mpi_followup_assign_rule_type
    CHECK (rule_type IN ('BY_DEPT', 'BY_DOCTOR', 'BY_GROUP', 'ROUND_ROBIN', 'MANUAL'));

ALTER TABLE mpi_followup_assign_rule
    ADD CONSTRAINT ck_mpi_followup_assign_rule_round
    CHECK (rule_type <> 'ROUND_ROBIN' OR round_robin_staff_ids IS NOT NULL);
```

### 4.11 表：`mpi_followup_code_seq`（编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| seq_type | VARCHAR(16) | N | - | TEMPLATE/PLAN/TASK |
| prefix | VARCHAR(8) | N | - | 前缀 |
| period_key | VARCHAR(8) | N | - | 周期键 `yyyyMMdd` |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 4 | 流水位数 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_mpi_followup_code_seq(seq_type, prefix, period_key)` 唯一。

**说明：** Redis `INCR` 为主，DB 表用于每日对账；Redis 丢数据时从 `MAX(current_seq)` 恢复。

### 4.12 SQLAlchemy 2.0 模型定义

```python
# app/models/mpi/followup.py
"""随访 ORM 模型"""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, Date, DateTime,
    JSONB, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MpiFollowupConfig(Base):
    """随访配置（单行）"""
    __tablename__ = "mpi_followup_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_prefix: Mapped[str] = mapped_column(String(8), default="FT", nullable=False)
    plan_prefix: Mapped[str] = mapped_column(String(8), default="FP", nullable=False)
    task_prefix: Mapped[str] = mapped_column(String(8), default="FTK", nullable=False)
    seq_len: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    advance_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    overdue_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    cycle_max_occurrences: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    default_assign_rule_code: Mapped[Optional[str]] = mapped_column(String(32), default="BY_DEPT")
    default_exec_dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    notify_on_assign: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_channel: Mapped[str] = mapped_column(String(32), default="INBOX,SMS", nullable=False)
    subscribe_patient_merge: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "随访配置（单行）"},
    )


class MpiFollowupTemplate(Base, TimestampMixin, SoftDeleteMixin):
    """随访模板"""
    __tablename__ = "mpi_followup_template"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_code: Mapped[str] = mapped_column(String(32), nullable=False)
    template_name: Mapped[str] = mapped_column(String(128), nullable=False)
    scene: Mapped[str] = mapped_column(String(32), nullable=False)
    apply_operation_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    apply_diagnosis_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    apply_dept_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    member_level_limit: Mapped[Optional[str]] = mapped_column(String(255))
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    node_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    nodes: Mapped[List["MpiFollowupTemplateNode"]] = relationship(
        back_populates="template", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("template_code", "is_deleted", name="uk_mpi_followup_template_code"),
        Index("idx_mpi_followup_template_scene", "scene", "status"),
        Index("idx_mpi_followup_template_status", "status", "created_at"),
        {"comment": "随访模板"},
    )


class MpiFollowupTemplateNode(Base, SoftDeleteMixin):
    """模板节点"""
    __tablename__ = "mpi_followup_template_node"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(32), nullable=False)
    node_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    offset_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cycle_days: Mapped[Optional[int]] = mapped_column(Integer)
    max_occurrences: Mapped[Optional[int]] = mapped_column(Integer)
    followup_methods: Mapped[str] = mapped_column(String(255), nullable=False)
    content_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    exec_dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exec_staff_requirement: Mapped[Optional[str]] = mapped_column(String(32))
    assign_rule_code: Mapped[Optional[str]] = mapped_column(String(32))
    priority: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    advance_days: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    template: Mapped["MpiFollowupTemplate"] = relationship(back_populates="nodes")

    __table_args__ = (
        UniqueConstraint("template_id", "node_seq", "is_deleted",
                         name="uk_mpi_followup_node"),
        Index("idx_mpi_followup_node_template", "template_id"),
        Index("idx_mpi_followup_node_trigger", "trigger_type"),
        {"comment": "模板节点"},
    )


class MpiFollowupPlan(Base, TimestampMixin, SoftDeleteMixin):
    """随访计划"""
    __tablename__ = "mpi_followup_plan"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_no: Mapped[str] = mapped_column(String(32), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(32), nullable=False)
    template_name: Mapped[Optional[str]] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_date: Mapped[date] = mapped_column(Date, nullable=False)
    biz_no: Mapped[Optional[str]] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    task_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled_reason: Mapped[Optional[str]] = mapped_column(String(500))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("plan_no", "is_deleted", name="uk_mpi_followup_plan_no"),
        Index("idx_mpi_followup_plan_patient", "patient_id", "status"),
        Index("idx_mpi_followup_plan_template", "template_code", "status"),
        Index("idx_mpi_followup_plan_status", "status", "created_at"),
        Index("idx_mpi_followup_plan_base", "base_date"),
        Index("idx_mpi_followup_plan_biz", "biz_no"),
        {"comment": "随访计划"},
    )


class MpiFollowupTask(Base, SoftDeleteMixin):
    """随访任务"""
    __tablename__ = "mpi_followup_task"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_no: Mapped[str] = mapped_column(String(32), nullable=False)
    plan_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plan_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_name: Mapped[Optional[str]] = mapped_column(String(64))
    phone_mask: Mapped[Optional[str]] = mapped_column(String(32))
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[str] = mapped_column(String(32), nullable=False)
    node_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    occurrence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    offset_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    plan_date: Mapped[date] = mapped_column(Date, nullable=False)
    followup_methods: Mapped[str] = mapped_column(String(255), nullable=False)
    content_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    exec_dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exec_dept_name: Mapped[Optional[str]] = mapped_column(String(128))
    assignee_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    assignee_name: Mapped[Optional[str]] = mapped_column(String(64))
    assign_rule_code: Mapped[Optional[str]] = mapped_column(String(32))
    priority: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", nullable=False)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    executed_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    executed_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    result_summary: Mapped[Optional[str]] = mapped_column(String(1000))
    fail_reason: Mapped[Optional[str]] = mapped_column(String(500))
    cancelled_reason: Mapped[Optional[str]] = mapped_column(String(500))
    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("task_no", "is_deleted", name="uk_mpi_followup_task_no"),
        Index("idx_mpi_followup_task_plan", "plan_id", "status"),
        Index("idx_mpi_followup_task_patient", "patient_id", "status"),
        Index("idx_mpi_followup_task_dept", "exec_dept_id", "status", "plan_date"),
        Index("idx_mpi_followup_task_assignee", "assignee_id", "status", "plan_date"),
        Index("idx_mpi_followup_task_date", "plan_date", "status"),
        Index("idx_mpi_followup_task_status", "status", "created_at"),
        {"comment": "随访任务"},
    )

    STATUS_LABELS = {
        "PENDING": "待分派", "ASSIGNED": "已分派", "EXECUTING": "执行中",
        "COMPLETED": "已完成", "CANCELLED": "已取消",
        "OVERDUE": "逾期", "FAILED": "执行失败",
    }

    @property
    def status_label(self) -> str:
        return self.STATUS_LABELS.get(self.status, self.status)

    def can_write_result(self) -> bool:
        return self.status in ("ASSIGNED", "EXECUTING", "OVERDUE")


class MpiFollowupTaskLog(Base):
    """任务状态日志"""
    __tablename__ = "mpi_followup_task_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    task_no: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_status: Mapped[Optional[str]] = mapped_column(String(16))
    after_status: Mapped[Optional[str]] = mapped_column(String(16))
    detail: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mpi_followup_task_log_task", "task_id", "created_at"),
        Index("idx_mpi_followup_task_log_action", "action", "created_at"),
        Index("idx_mpi_followup_task_log_time", "created_at"),
        {"comment": "任务状态日志（月度分区）"},
    )


class MpiFollowupPlanLog(Base):
    """计划变更日志"""
    __tablename__ = "mpi_followup_plan_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    plan_no: Mapped[Optional[str]] = mapped_column(String(32))
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
        Index("idx_mpi_followup_plan_log_plan", "plan_id", "created_at"),
        Index("idx_mpi_followup_plan_log_action", "action", "created_at"),
        Index("idx_mpi_followup_plan_log_time", "created_at"),
        {"comment": "计划变更日志（月度分区）"},
    )


class MpiFollowupTemplateLog(Base):
    """模板变更日志"""
    __tablename__ = "mpi_followup_template_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    template_code: Mapped[Optional[str]] = mapped_column(String(32))
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
        Index("idx_mpi_followup_tpl_log_template", "template_id", "created_at"),
        Index("idx_mpi_followup_tpl_log_action", "action", "created_at"),
        Index("idx_mpi_followup_tpl_log_time", "created_at"),
        {"comment": "模板变更日志（月度分区）"},
    )


class MpiFollowupAssignRule(Base, TimestampMixin, SoftDeleteMixin):
    """分派规则"""
    __tablename__ = "mpi_followup_assign_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    exec_dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    group_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    round_robin_staff_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    priority: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    __table_args__ = (
        UniqueConstraint("rule_code", "is_deleted", name="uk_mpi_followup_assign_rule_code"),
        Index("idx_mpi_followup_assign_rule_type", "rule_type", "is_enabled"),
        Index("idx_mpi_followup_assign_rule_priority", "priority", "is_enabled"),
        {"comment": "分派规则"},
    )


class MpiFollowupCodeSeq(Base):
    """编码序列（DB 对账）"""
    __tablename__ = "mpi_followup_code_seq"

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
                         name="uk_mpi_followup_code_seq"),
        {"comment": "随访编码序列（Redis 为主，DB 对账）"},
    )
```

### 4.13 Pydantic Schema 定义

```python
# app/schemas/mpi/followup.py
"""随访 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


FOLLOWUP_SCENE = Literal["SURGERY", "DISCHARGE", "CHRONIC", "SATISFACTION", "OTHER"]
TRIGGER_TYPE = Literal["SURGERY_DATE", "DISCHARGE_DATE", "REGISTER_DATE",
                        "DIAGNOSIS_DATE", "FIXED_DATE", "CYCLE"]
FOLLOWUP_METHOD = Literal["PHONE", "WECHAT", "SMS", "OUTPATIENT",
                           "HOME_VISIT", "MIXED", "PATIENT_APP"]
TEMPLATE_STATUS = Literal["DRAFT", "ENABLED", "DISABLED"]
PLAN_STATUS = Literal["DRAFT", "ACTIVE", "COMPLETED", "CANCELLED"]
TASK_STATUS = Literal["PENDING", "ASSIGNED", "EXECUTING", "COMPLETED",
                       "CANCELLED", "OVERDUE", "FAILED"]
TASK_PRIORITY = Literal["HIGH", "NORMAL", "LOW"]
ASSIGN_RULE_TYPE = Literal["BY_DEPT", "BY_DOCTOR", "BY_GROUP", "ROUND_ROBIN", "MANUAL"]


# ==================== 模板 ====================
class FollowupNodeSchema(BaseModel):
    node_seq: int = Field(..., ge=1)
    node_name: str = Field(..., min_length=1, max_length=64)
    trigger_type: TRIGGER_TYPE
    offset_days: int = Field(0, ge=-3650, le=3650)
    cycle_days: Optional[int] = Field(None, ge=1, le=3650)
    max_occurrences: Optional[int] = Field(None, ge=1, le=100)
    followup_methods: List[FOLLOWUP_METHOD] = Field(..., min_length=1)
    content_json: Optional[dict] = None
    exec_dept_id: int
    exec_staff_requirement: Optional[Literal["SURGEON", "ATTENDING", "ANY"]] = None
    assign_rule_code: Optional[str] = Field(None, max_length=32)
    priority: TASK_PRIORITY = "NORMAL"
    is_required: bool = True
    advance_days: Optional[int] = Field(None, ge=0, le=365)
    description: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_cycle(self):
        if self.trigger_type == "CYCLE":
            if not self.cycle_days or not self.max_occurrences:
                raise ValueError("周期节点必须填写周期天数和最大次数")
        return self


class FollowupTemplateBase(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=128)
    scene: FOLLOWUP_SCENE
    apply_operation_ids: Optional[List[int]] = None
    apply_diagnosis_ids: Optional[List[int]] = None
    apply_dept_ids: Optional[List[int]] = None
    member_level_limit: Optional[List[str]] = None
    trigger_type: TRIGGER_TYPE
    description: Optional[str] = Field(None, max_length=500)


class FollowupTemplateCreate(FollowupTemplateBase):
    template_code: str = Field(..., pattern=r"^FT-[A-Z0-9\-]{2,29}$")
    nodes: List[FollowupNodeSchema] = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_nodes(self):
        seqs = [n.node_seq for n in self.nodes]
        if len(seqs) != len(set(seqs)):
            raise ValueError("节点序号重复")
        return self


class FollowupTemplateUpdate(FollowupTemplateBase):
    nodes: Optional[List[FollowupNodeSchema]] = None


class FollowupTemplateItem(FollowupTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_code: str
    node_count: int = 0
    status: str
    updated_at: Optional[datetime] = None


# ==================== 计划 ====================
class FollowupPlanCreate(BaseModel):
    patient_id: int
    template_code: str = Field(..., max_length=32)
    source: Literal["SURGERY", "DISCHARGE", "REGISTER", "DIAGNOSIS", "MANUAL", "IMPORT"] = "MANUAL"
    trigger_type: TRIGGER_TYPE
    base_date: date
    biz_no: Optional[str] = Field(None, max_length=64)
    activate: bool = True
    remark: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_biz(self):
        if self.trigger_type in ("SURGERY_DATE", "DISCHARGE_DATE", "DIAGNOSIS_DATE") and not self.biz_no:
            raise ValueError("该触发方式必须提供业务单号")
        return self


class FollowupPlanItem(BaseModel):
    id: int
    plan_no: str
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    template_code: str
    template_name: Optional[str] = None
    source: str
    status: str
    task_count: int = 0
    completed_count: int = 0
    base_date: date
    created_at: Optional[datetime] = None


class FollowupPlanDetail(FollowupPlanItem):
    phone_mask: Optional[str] = None
    trigger_type: str
    biz_no: Optional[str] = None
    cancelled_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    version_no: int = 1
    remark: Optional[str] = None


# ==================== 任务 ====================
class FollowupTaskItem(BaseModel):
    id: int
    task_no: str
    plan_no: Optional[str] = None
    patient_id: int
    empi_no: Optional[str] = None
    patient_name: Optional[str] = None
    phone_mask: Optional[str] = None
    node_name: str
    plan_date: date
    followup_methods: List[str] = []
    exec_dept_id: int
    exec_dept_name: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    priority: str
    status: str
    completed_at: Optional[datetime] = None


class FollowupTaskAssignRequest(BaseModel):
    assignee_id: int
    exec_dept_id: Optional[int] = None
    reason: Optional[str] = Field(None, max_length=500)


class FollowupTaskBatchAssignRequest(BaseModel):
    task_ids: List[int] = Field(..., min_length=1, max_length=500)
    assignee_id: int
    exec_dept_id: Optional[int] = None
    reason: Optional[str] = Field(None, max_length=500)


class FollowupTaskCancelRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class FollowupTaskResult(BaseModel):
    status: Literal["EXECUTING", "COMPLETED", "FAILED"]
    executed_at: Optional[datetime] = None
    executed_by: Optional[int] = None
    executed_by_name: Optional[str] = Field(None, max_length=64)
    result_summary: Optional[str] = Field(None, max_length=1000)
    fail_reason: Optional[str] = Field(None, max_length=500)
    detail: Optional[dict] = None

    @model_validator(mode="after")
    def validate_result(self):
        if self.status == "COMPLETED" and not self.result_summary:
            raise ValueError("完成状态必须填写结果摘要")
        if self.status == "FAILED" and not self.fail_reason:
            raise ValueError("失败状态必须填写失败原因")
        return self


# ==================== 分派规则 ====================
class FollowupAssignRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=128)
    rule_type: ASSIGN_RULE_TYPE
    exec_dept_id: Optional[int] = None
    group_id: Optional[int] = None
    round_robin_staff_ids: Optional[List[int]] = None
    priority: int = 999
    is_enabled: bool = True
    description: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_rule(self):
        if self.rule_type == "ROUND_ROBIN" and not self.round_robin_staff_ids:
            raise ValueError("轮询规则必须选择人员")
        if self.rule_type == "BY_GROUP" and not self.group_id:
            raise ValueError("按随访组规则必须选择用户组")
        return self


class FollowupAssignRuleCreate(FollowupAssignRuleBase):
    rule_code: str = Field(..., pattern=r"^AR-[A-Z0-9\-]{2,29}$")


class FollowupAssignRuleUpdate(FollowupAssignRuleBase):
    pass


class FollowupAssignRuleItem(FollowupAssignRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_code: str


# ==================== 配置 ====================
class FollowupConfigUpdate(BaseModel):
    template_prefix: str = Field("FT", max_length=8)
    plan_prefix: str = Field("FP", max_length=8)
    task_prefix: str = Field("FTK", max_length=8)
    seq_len: int = Field(4, ge=2, le=10)
    advance_days: int = Field(30, ge=0, le=365)
    overdue_days: int = Field(7, ge=1, le=365)
    cycle_max_occurrences: int = Field(24, ge=1, le=100)
    default_assign_rule_code: Optional[str] = Field("BY_DEPT", max_length=32)
    default_exec_dept_id: Optional[int] = None
    notify_on_assign: bool = True
    notify_channel: str = Field("INBOX,SMS", max_length=32)
    subscribe_patient_merge: bool = True
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_config(self):
        if self.overdue_days >= self.advance_days and self.advance_days > 0:
            # 允许，只提示不阻止
            pass
        return self


class FollowupConfigDetail(FollowupConfigUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: int = 1
    updated_at: Optional[datetime] = None


# ==================== 内部契约 ====================
class TriggerPlanRequest(BaseModel):
    event_type: str = Field(..., max_length=32)
    patient_id: int
    template_code: str = Field(..., max_length=32)
    trigger_type: TRIGGER_TYPE
    base_date: date
    biz_no: Optional[str] = Field(None, max_length=64)
    biz_context: Optional[dict] = None


class TriggerPlanResult(BaseModel):
    plan_id: int
    plan_no: str
    created: bool
    task_count: int


class PendingTaskQuery(BaseModel):
    dept_id: Optional[int] = None
    assignee_id: Optional[int] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(100, ge=1, le=500)


class MergeRedirectRequest(BaseModel):
    merge_id: str = Field(..., max_length=32)
    primary_patient_id: int
    secondary_patient_id: int


class MergeRedirectResult(BaseModel):
    merge_id: str
    secondary_patient_id: int
    plan_count: int = 0
    task_count: int = 0
    redirected: int = 0
    conflict: int = 0
    conflict_task_ids: List[int] = []


# 前向引用
FollowupPlanDetail.model_rebuild()
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-20 | 首次发布：10 张表 | 系统设计组 |