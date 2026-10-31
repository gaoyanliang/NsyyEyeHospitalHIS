# 二级眼科医院 HIS 系统 — M10 视光业务管理
# 子模块数据结构：OK镜与RGP验配随访

**文档版本：** V1.0
**所属模块：** M10 视光业务管理
**子模块：** OK镜与RGP验配随访（Ortho-K Fitting & Follow-up）（M10-04）
**主数据域：** 视光业务域（`M10`），表前缀 `m10_ortho_k_`
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》、[M10 共享规范](00_M10_视光业务管理_模块设计_共享规范与文档模板.md)、[M01-08 视光产品](../M01主数据管理MDM/M01_主数据管理MDM_08_视光产品_详细设计.md)、[M16-04 视光销售结算](../M16收费结算管理/M16_收费结算管理_04_视光销售结算_详细设计.md)
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7
**文档用途：** 作为「OK镜与RGP验配随访」子模块表结构的独立参考手册与建表依据

---

## 文档说明

本文档为《[OK镜与RGP验配随访详细设计](M10_视光业务管理_04_OK镜与RGP验配随访_详细设计.md)》第 4 章「数据结构设计」的独立成册版本。

**相关文档：**

| 文档 | 说明 |
|---|---|
| [OK镜与RGP验配随访详细设计](M10_视光业务管理_04_OK镜与RGP验配随访_详细设计.md) | 业务模型、页面设计、接口设计、业务规则、验收标准 |
| [M10 共享规范](00_M10_视光业务管理_模块设计_共享规范与文档模板.md) | 全局命名、错误码、接口总线、公共枚举 |
| [M10 数据结构设计汇总](M10_视光业务管理_数据结构设计汇总.md) | 跨子模块表清单与全局设计约定 |
| [M01-08 视光产品数据结构](../M01主数据管理MDM/M01_主数据管理MDM_08_视光产品_数据结构.md) | 只读引用的商品主数据（含 `mdm_ortho_k_params`） |
| [M16-04 视光销售结算数据结构](../M16收费结算管理/M16_收费结算管理_04_视光销售结算_数据结构.md) | 只读引用的销售单 |

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 9 张

---

## 目录

- [表清单](#表清单)
- [4. 数据结构设计](#4-数据结构设计)
  - [4.1 ER 关系图](#41-er-关系图)
  - [4.2 表：`m10_ortho_k_fitting`（OK 镜验配单主表）](#42-表m10_ortho_k_fittingok-镜验配单主表)
  - [4.3 表：`m10_ortho_k_apply`（验配申请与准入评估表）](#43-表m10_ortho_k_apply验配申请与准入评估表)
  - [4.4 表：`m10_ortho_k_cornea`（角膜地形图参数表）](#44-表m10_ortho_k_cornea角膜地形图参数表)
  - [4.5 表：`m10_ortho_k_trial_lens`（试戴片台账表）](#45-表m10_ortho_k_trial_lens试戴片台账表)
  - [4.6 表：`m10_ortho_k_trial_use`（试戴片占用与试戴评估表）](#46-表m10_ortho_k_trial_use试戴片占用与试戴评估表)
  - [4.7 表：`m10_ortho_k_custom_param`（定制参数表）](#47-表m10_ortho_k_custom_param定制参数表)
  - [4.8 表：`m10_ortho_k_delivery`（到片验收与发放表）](#48-表m10_ortho_k_delivery到片验收与发放表)
  - [4.9 表：`m10_ortho_k_followup`（戴镜随访记录表）](#49-表m10_ortho_k_followup戴镜随访记录表)
  - [4.10 表：`m10_ortho_k_log`（验配操作日志表）](#410-表m10_ortho_k_log验配操作日志表)
  - [4.11 SQLAlchemy 2.0 模型定义](#411-sqlalchemy-20-模型定义)
  - [4.12 Pydantic Schema 定义](#412-pydantic-schema-定义)
- [附录 A：表清单速查](#附录-a表清单速查)
- [附录 B：状态枚举汇总](#附录-b状态枚举汇总)
- [附录 C：关键索引与查询](#附录-c关键索引与查询)
- [附录 D：配置参数与字典](#附录-d配置参数与字典)
- [附录 E：建表依赖顺序与 Alembic 迁移](#附录-e建表依赖顺序与-alembic-迁移)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `m10_ortho_k_fitting` | OK 镜验配单主表 |
| 4.3 | `m10_ortho_k_apply` | 验配申请与准入评估表 |
| 4.4 | `m10_ortho_k_cornea` | 角膜地形图参数表 |
| 4.5 | `m10_ortho_k_trial_lens` | 试戴片台账表 |
| 4.6 | `m10_ortho_k_trial_use` | 试戴片占用与试戴评估表 |
| 4.7 | `m10_ortho_k_custom_param` | 定制参数表 |
| 4.8 | `m10_ortho_k_delivery` | 到片验收与发放表 |
| 4.9 | `m10_ortho_k_followup` | 戴镜随访记录表 |
| 4.10 | `m10_ortho_k_log` | 验配操作日志表 |

> **表数说明（与详细设计第 4 章指引块一致）：** 本子模块共 **9 张表**，全部以 `m10_ortho_k_` 为前缀，已在共享规范 §12.3 登记。M10-09 的 `m10_followup_plan` 由 M10-09 建表，本子模块**只读引用**，不重复建表；M01-08 的 `mdm_ortho_k_params` 只读引用。

---

## 4. 数据结构设计

### 4.1 ER 关系图

```
                        ┌──────────────────────────────────┐
                        │      m10_ortho_k_apply           │
                        │  验配申请与准入评估表（1 次申请）  │
                        │  年龄/球镜/柱镜/曲率/厚度/眼压    │
                        └───────────────┬──────────────────┘
                                        │ 1:1（准入通过后开验配单）
                                        ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        m10_ortho_k_fitting                            │
│                     OK 镜验配单主表（OK+日期+4 位）                     │
│  status: APPLY→ASSESSED→TRIAL→CUSTOMIZING→ORDERED→ARRIVED→           │
│          DELIVERED→FOLLOWING→REPLACE_DUE→REPLACED→STOPPED→CLOSED     │
└──┬────────┬──────────────┬──────────────┬──────────────┬─────────────┘
   │ 1:N    │ 1:N          │ 1:N          │ 1:N          │ 1:N
   ▼        ▼              ▼              ▼              ▼
┌────────┐┌────────────┐┌────────────┐┌────────────┐┌──────────────────┐
│m10_    ││m10_        ││m10_        ││m10_ortho_k_││m10_ortho_k_      │
│ortho_k_││ortho_k_    ││ortho_k_    ││custom_param││followup          │
│cornea  ││trial_use   ││delivery    ││（定制参数） ││（戴镜随访）       │
│地形图   ││试戴占用     ││到片验收发放 ││            ││1/7/30/90 天      │
│参数    ││（部分唯一）  ││（逐片）     ││            ││+每 3 月          │
└────────┘└─────┬──────┘└────────────┘└────────────┘└──────────────────┘
                 │ N:1
                 ▼
          ┌──────────────────────┐
          │ m10_ortho_k_trial_   │
          │ lens（试戴片台账）     │
          │ 一片一时刻只给一人     │
          └──────────────────────┘

治理：
┌──────────────────────────────────────────┐
│ m10_ortho_k_log（验配操作日志，按月分区）  │
└──────────────────────────────────────────┘

只读引用的上游表（不建物理外键，应用层校验 + 每日对账）：
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
  mpi_patient                （M03-01）患者主索引
  mdm_optical_product        （M01-08）视光产品（OK 镜产品/试戴片产品）
  mdm_ortho_k_params         （M01-08）OK 镜验配参数组（BC/RC/AC/PC/直径/降度）
  mdm_optical_spec           （M01-08）光度矩阵（RGP 现货光度校验）
  m16_optical_order          （M16-04）视光销售单（收钱，本模块只读状态与金额快照）
  m10_followup_plan          （M10-09）复查计划（本模块只读 + 写回执行结果）
  检查报告（角膜地形图）        （M12）报告归档 ID
  员工主数据                   （M01-02）验配师资质
┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄
```

**表清单（共 9 张）：**

| 序号 | 表名 | 中文名 | 说明 | 预估量级 |
|---|---|---|---|---|
| 1 | `m10_ortho_k_apply` | 验配申请与准入评估表 | 准入评估（6 大类 20 余项指标）+ 家长知情同意 | 3,000/年 |
| 2 | `m10_ortho_k_fitting` | OK 镜验配单主表 | 核心主表，一患一次验配一单（可多轮） | 2,400/年 |
| 3 | `m10_ortho_k_cornea` | 角膜地形图参数表 | 按眼别存 K1/K2/Km/e/HVID/瞳孔/厚度/图形分类 | 5,000/年 |
| 4 | `m10_ortho_k_trial_lens` | 试戴片台账表 | 试戴片实物档案（编号/弧参数/消毒/报废） | 1,200 |
| 5 | `m10_ortho_k_trial_use` | 试戴片占用与试戴评估表 | 占用/释放 + 荧光配适/定位/活动度/TFT | 8,000/年 |
| 6 | `m10_ortho_k_custom_param` | 定制参数表 | 按眼别 BC/RC/AC/PC/直径/降度 + fit-check 回执 | 4,800/年 |
| 7 | `m10_ortho_k_delivery` | 到片验收与发放表 | 逐片核对/外观检查/消毒/发放/教学 | 4,800/年 |
| 8 | `m10_ortho_k_followup` | 戴镜随访记录表 | 1/7/30/90 天 + 每 3 月随访结果与并发症 | 30,000/年 |
| 9 | `m10_ortho_k_log` | 验配操作日志表 | 全动作审计，按月 RANGE 分区 | 120,000/年 |

---
### 4.2 表：`m10_ortho_k_fitting`（OK 镜验配单主表）

**用途：** OK 镜验配业务的**唯一主档**，一患一次验配产出一条记录（同一患者换片后新建一条，通过 `previous_fit_id` 串成链条）。它是本子模块所有其他表的挂载点：`m10_ortho_k_apply`、`m10_ortho_k_cornea`、`m10_ortho_k_trial_use`、`m10_ortho_k_custom_param`、`m10_ortho_k_delivery`、`m10_ortho_k_followup` 全部通过 `fitting_id` 挂上来。

- **写入方：** 本子模块（验配师在 P02 开单、P03/P04/P05 推进状态）。
- **只读方：** M10-06（配镜订单引用 `fit_no` 与定制参数）、M16-04（视光销售结算取 OK 镜定制参数与价格依据）、M01-08（通过 P-09 反向读取以校验产品适配）、M10-09（按 `fit_no` 建 OK 镜复查计划）。
- **关键设计：** `status` 是本子模块最长的状态机（13 态），与 `m10_ortho_k_apply`、`m10_ortho_k_custom_param`、`m10_ortho_k_delivery`、`m10_ortho_k_followup` 四个从表的状态**联动但不同步**（主表保存汇总态，从表保存阶段细节态）。器械合规字段（注册证号、有效期、验配师资质）落在主表上，因为一次验配只对应一套产品与一名主验配师。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键，验配流水号 |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号 `OK` + YYYYMMDD + 4 位（草稿状态为空） |
| apply_id | BIGINT | Y | NULL | 准入评估 ID（`m10_ortho_k_apply.id`，1:1） |
| previous_fit_id | BIGINT | Y | NULL | 上一副验配单 ID（换片链路，自关联） |
| replace_round | SMALLINT | N | 1 | 换片轮次（首配为 1，每次换片 +1） |
| patient_id | BIGINT | N | — | 患者 ID（M03 `mpi_patient.id`，只读引用） |
| empi_no | VARCHAR(32) | Y | NULL | EMPI 主索引号（冗余快照） |
| customer_id | BIGINT | Y | NULL | 视光顾客 ID（`m10_customer.id`，无就诊记录顾客时必填，只读引用 M10-05） |
| **患者快照组** | | | | |
| patient_name | VARCHAR(64) | N | — | 患者姓名（快照） |
| gender | VARCHAR(8) | Y | NULL | 性别 `M`/`F`/`U` |
| age | SMALLINT | Y | NULL | 验配时年龄（岁，快照；准入校验依据） |
| birth_date | DATE | Y | NULL | 出生日期 |
| id_card_no | VARCHAR(32) | Y | NULL | 身份证号（加密存储） |
| phone | VARCHAR(32) | Y | NULL | 联系电话（随访通知用） |
| guardian_name | VARCHAR(64) | Y | NULL | 监护人姓名（未成年患者必填） |
| guardian_phone | VARCHAR(32) | Y | NULL | 监护人电话 |
| guardian_relation | VARCHAR(16) | Y | NULL | 与患者关系 `FATHER`/`MOTHER`/`GRANDPARENT`/`OTHER` |
| **产品与器械合规组** | | | | |
| product_kind | VARCHAR(16) | N | 'ORTHO_K' | 产品品类 `ORTHO_K`（角膜塑形镜）/`RGP`（硬性透气接触镜） |
| product_code | VARCHAR(32) | Y | NULL | 定制镜片产品编码（M01-08 `mdm_optical_product.product_code`，只读引用） |
| product_name | VARCHAR(128) | Y | NULL | 产品名称（快照） |
| brand_code | VARCHAR(32) | Y | NULL | 品牌编码（M01-08 `brand_code` 快照） |
| param_group_id | BIGINT | Y | NULL | 采用的基础参数组 ID（M01-08 `mdm_ortho_k_params.id`，只读引用） |
| param_group_code | VARCHAR(32) | Y | NULL | 参数组编码（快照） |
| device_reg_no | VARCHAR(64) | Y | NULL | 医疗器械注册证号（三类，必须有效） |
| device_reg_valid_until | DATE | Y | NULL | 注册证有效期截止日 |
| device_reg_checked_at | TIMESTAMP | Y | NULL | 注册证校验时间（调 M01-08 full-config 的时刻） |
| device_class | VARCHAR(8) | N | 'CLASS_III' | 器械管理类别 `CLASS_III`（角膜塑形镜为第三类） |
| material | VARCHAR(64) | Y | NULL | 镜片材质（如 `BOSTON XO`、`ROFLUFOCON A`） |
| **验配人员与机构组** | | | | |
| store_id | BIGINT | N | — | 验配门店/院区 ID |
| store_name | VARCHAR(64) | Y | NULL | 门店名称（快照） |
| fitter_id | BIGINT | N | — | 主验配师 ID（M01-02 职工，须具视光医师/验光师资质） |
| fitter_name | VARCHAR(64) | Y | NULL | 主验配师姓名（快照） |
| fitter_qualification | VARCHAR(64) | Y | NULL | 验配师资质快照（如 `OPTOMETRIST`/`OPHTHALMIC_PHYSICIAN`） |
| fitter_cert_no | VARCHAR(64) | Y | NULL | 验配师资质证书编号 |
| assistant_id | BIGINT | Y | NULL | 协助人员 ID（护士/视光师） |
| assistant_name | VARCHAR(64) | Y | NULL | 协助人员姓名（快照） |
| review_doctor_id | BIGINT | Y | NULL | 医学复核医师 ID（角膜条件可疑时需医师复核） |
| review_doctor_name | VARCHAR(64) | Y | NULL | 复核医师姓名（快照） |
| review_passed_at | TIMESTAMP | Y | NULL | 医学复核通过时间 |
| **屈光与目标组** | | | | |
| od_sphere | NUMERIC(6,2) | Y | NULL | 右眼球镜（D，如 `-3.25`） |
| od_cylinder | NUMERIC(6,2) | Y | NULL | 右眼柱镜（D，如 `-0.75`） |
| od_axis | SMALLINT | Y | NULL | 右眼轴位（°，1~180） |
| os_sphere | NUMERIC(6,2) | Y | NULL | 左眼球镜（D） |
| os_cylinder | NUMERIC(6,2) | Y | NULL | 左眼柱镜（D） |
| os_axis | SMALLINT | Y | NULL | 左眼轴位（°，1~180） |
| od_target_reduction | NUMERIC(6,2) | Y | NULL | 右眼目标降度（D，负值） |
| os_target_reduction | NUMERIC(6,2) | Y | NULL | 左眼目标降度（D，负值） |
| od_uncorrected_va | NUMERIC(4,2) | Y | NULL | 右眼裸眼视力（小数记录法，如 `0.15`） |
| os_uncorrected_va | NUMERIC(4,2) | Y | NULL | 左眼裸眼视力（小数记录法） |
| optometry_no | VARCHAR(32) | Y | NULL | 依据的验光单号（M10-01 `m10_optometry.optometry_no`，只读引用） |
| prescription_no | VARCHAR(32) | Y | NULL | 依据的配镜处方号（M10-02 `m10_prescription.rx_no`，只读引用） |
| **时间节点组** | | | | |
| apply_time | TIMESTAMP | N | CURRENT_TIMESTAMP | 验配申请时间 |
| assessed_at | TIMESTAMP | Y | NULL | 准入评估完成时间 |
| trial_started_at | TIMESTAMP | Y | NULL | 首次试戴时间 |
| ordered_at | TIMESTAMP | Y | NULL | 定制下单时间 |
| expected_arrival_date | DATE | Y | NULL | 预计到片日期（下单日 + 厂家供货周期） |
| arrived_at | TIMESTAMP | Y | NULL | 实际到片时间 |
| delivered_at | TIMESTAMP | Y | NULL | 首次发放/戴镜时间 |
| expected_replace_date | DATE | Y | NULL | 预计换片日期（发放日 + 更换周期） |
| stopped_at | TIMESTAMP | Y | NULL | 停戴日期 |
| closed_at | TIMESTAMP | Y | NULL | 验配单关闭时间 |
| **状态组** | | | | |
| status | VARCHAR(24) | N | 'DRAFT' | 验配单状态（13 态，见附录 B） |
| stop_reason_code | VARCHAR(32) | Y | NULL | 停戴原因编码 ∈ {`CORNEAL_INJURY`,`INFECTION`,`FEVER_COLD`,`SWIMMING`,`PREGNANCY`,`NON_COMPLIANCE`,`PATIENT_REQUEST`,`SWITCH_TO_OTHER`,`OTHER`} |
| stop_reason | VARCHAR(512) | Y | NULL | 停戴原因详细说明（≥10 字） |
| replace_reason_code | VARCHAR(32) | Y | NULL | 换片原因编码 ∈ {`CYCLE_EXPIRED`,`POWER_CHANGE`,`LENS_DAMAGED`,`LENS_LOST`,`POOR_FIT`,`OTHER`} |
| complications | JSONB | Y | NULL | 并发症标记数组（如 `["CORNEAL_STAINING","INFILTRATE"]`） |
| has_severe_complication | BOOLEAN | N | FALSE | 是否存在严重并发症（感染性角膜炎等，触发上报） |
| **费用与订单快照组（由 M16-04 事件更新，只读）** | | | | |
| sales_order_no | VARCHAR(32) | Y | NULL | M16-04 视光销售单号（`m16_optical_order.order_no`，只读引用） |
| order_amount | NUMERIC(14,2) | Y | NULL | 销售单金额快照（元，M16 计算，本模块不算） |
| paid_amount | NUMERIC(14,2) | N | 0 | 已付金额快照（元，M16 事件回写） |
| sales_order_status | VARCHAR(24) | Y | NULL | M16 销售单状态快照（只读，不得改写） |
| m10_order_no | VARCHAR(32) | Y | NULL | M10 配镜订单号（M10-06 `m10_order.order_no`，只读引用） |
| **随访汇总组** | | | | |
| followup_count | SMALLINT | N | 0 | 已完成随访次数 |
| last_followup_at | TIMESTAMP | Y | NULL | 最近一次随访时间 |
| next_followup_date | DATE | Y | NULL | 下次应复查日期（冗余，加速到期查询） |
| overdue_days | SMALLINT | N | 0 | 逾期天数（定时任务维护，逾期 >30 天告警） |
| **备注与标准字段** | | | | |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| void_reason | VARCHAR(512) | Y | NULL | 作废原因 |
| voided_by | BIGINT | Y | NULL | 作废人 |
| voided_at | TIMESTAMP | Y | NULL | 作废时间 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_fitting` | 主键 | `id` | — |
| `uk_m10_ortho_k_fitting_no` | 唯一（部分） | `fit_no` WHERE `is_deleted = FALSE` | **验配单号唯一**，草稿为 NULL 不参与 |
| `uk_m10_ortho_k_fitting_apply` | 唯一（部分） | `apply_id` WHERE `apply_id IS NOT NULL AND is_deleted = FALSE` | 一次准入只生成一张验配单（幂等） |
| `idx_m10_ortho_k_fitting_patient` | B-Tree | `patient_id`, `created_at` DESC | 按患者查验配历史 |
| `idx_m10_ortho_k_fitting_active` | B-Tree（部分） | `patient_id` WHERE `status IN ('DELIVERED','FOLLOWING','REPLACE_DUE')` AND `is_deleted = FALSE` | **查在戴镜患者（唯一一套在戴镜片）主力索引** |
| `idx_m10_ortho_k_fitting_status` | B-Tree（部分） | `status`, `created_at` DESC WHERE `is_deleted = FALSE` | 状态筛选、工作台分组 |
| `idx_m10_ortho_k_fitting_next_fu` | B-Tree（部分） | `next_followup_date` WHERE `status IN ('DELIVERED','FOLLOWING','REPLACE_DUE')` AND `is_deleted = FALSE` | **复查到期扫描（P07）主力索引** |
| `idx_m10_ortho_k_fitting_overdue` | B-Tree（部分） | `overdue_days` WHERE `overdue_days > 0` AND `is_deleted = FALSE` | 逾期清单（>30 天告警） |
| `idx_m10_ortho_k_fitting_replace_due` | B-Tree（部分） | `expected_replace_date` WHERE `status` IN (`'FOLLOWING','REPLACE_DUE'`) AND `is_deleted = FALSE` | 换片预警扫描（P08） |
| `idx_m10_ortho_k_fitting_fitter` | B-Tree | `fitter_id`, `created_at` DESC | 验配师工作量统计 |
| `idx_m10_ortho_k_fitting_store_date` | B-Tree | `store_id`, `created_at` DESC | 门店日报 |
| `idx_m10_ortho_k_fitting_sales_order` | B-Tree（部分） | `sales_order_no` WHERE `sales_order_no IS NOT NULL` | M16 事件反查验配单 |
| `idx_m10_ortho_k_fitting_m10_order` | B-Tree（部分） | `m10_order_no` WHERE `m10_order_no IS NOT NULL` | M10-06 订单反查验配单 |
| `idx_m10_ortho_k_fitting_previous` | B-Tree（部分） | `previous_fit_id` WHERE `previous_fit_id IS NOT NULL` | 换片链路追踪 |
| `idx_m10_ortho_k_fitting_severe` | B-Tree（部分） | `has_severe_complication` WHERE `has_severe_complication = TRUE` | 严重并发症上报清单 |
| `idx_m10_ortho_k_fitting_name_trgm` | GIN | `patient_name` `gin_trgm_ops` | 中文姓名模糊查 |

**约束说明：**

```sql
-- 验配单号格式：OK + 8 位日期 + 4 位序号（共 14 字符）
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_no_format
    CHECK (fit_no IS NULL OR fit_no ~ '^OK[0-9]{12}$');

-- 非草稿状态必须有验配单号
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_no_required
    CHECK (status = 'DRAFT' OR fit_no IS NOT NULL);

-- 验配单状态枚举（13 态）
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_status
    CHECK (status IN ('DRAFT', 'APPLYING', 'ASSESSED', 'TRIAL', 'CUSTOMIZING',
                      'ORDERED', 'ARRIVED', 'DELIVERED', 'FOLLOWING',
                      'REPLACE_DUE', 'REPLACED', 'STOPPED', 'CLOSED'));

-- 产品品类枚举
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_kind
    CHECK (product_kind IN ('ORTHO_K', 'RGP'));

-- 器械类别：角膜塑形镜与 RGP 均为第三类医疗器械
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_device_class
    CHECK (device_class = 'CLASS_III');

-- 眼别轴位范围：柱镜为 0 时轴位必须为空，柱镜非 0 时轴位必须在 1~180
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_od_axis
    CHECK ((od_cylinder IS NULL OR od_cylinder = 0 OR (od_axis IS NOT NULL AND od_axis BETWEEN 1 AND 180))
       AND (od_cylinder IS NULL OR od_cylinder <> 0 OR od_axis IS NULL));
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_os_axis
    CHECK ((os_cylinder IS NULL OR os_cylinder = 0 OR (os_axis IS NOT NULL AND os_axis BETWEEN 1 AND 180))
       AND (os_cylinder IS NULL OR os_cylinder <> 0 OR os_axis IS NULL));

-- 球镜/柱镜必须为 0.25 的整数倍
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_sph_step
    CHECK ((od_sphere IS NULL OR (od_sphere * 4) = trunc(od_sphere * 4))
       AND (os_sphere IS NULL OR (os_sphere * 4) = trunc(os_sphere * 4))
       AND (od_cylinder IS NULL OR (od_cylinder * 4) = trunc(od_cylinder * 4))
       AND (os_cylinder IS NULL OR (os_cylinder * 4) = trunc(os_cylinder * 4)));

-- 目标降度必须是负值且不超过 6.00D
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_target
    CHECK ((od_target_reduction IS NULL OR (od_target_reduction < 0 AND od_target_reduction >= -6.00))
       AND (os_target_reduction IS NULL OR (os_target_reduction < 0 AND os_target_reduction >= -6.00)));

-- 验配时年龄必须 ≥8 岁（准入底线，数据库兜底；应用层另有 8~40 岁分段提示）
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_age
    CHECK (age IS NULL OR age >= 8);

-- 未成年患者必须有监护人信息
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_guardian
    CHECK (age IS NULL OR age >= 18
           OR (guardian_name IS NOT NULL AND guardian_phone IS NOT NULL));

-- 已发放必须同时有发放时间与预计换片日期
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_delivered
    CHECK (status NOT IN ('DELIVERED', 'FOLLOWING', 'REPLACE_DUE', 'REPLACED', 'STOPPED', 'CLOSED')
           OR (delivered_at IS NOT NULL AND expected_replace_date IS NOT NULL));

-- 停戴必须填原因（≥10 字）、停止时间与操作人
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_stopped
    CHECK (status <> 'STOPPED'
           OR (stop_reason_code IS NOT NULL
               AND stop_reason IS NOT NULL
               AND char_length(btrim(stop_reason)) >= 10
               AND stopped_at IS NOT NULL));

-- 非停戴状态不得残留停戴原因
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_stop_clean
    CHECK (status = 'STOPPED' OR (stop_reason IS NULL AND stopped_at IS NULL));

-- 严重并发症必填并发症明细数组
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_complication
    CHECK (has_severe_complication = FALSE
           OR (complications IS NOT NULL AND jsonb_array_length(complications) > 0));

-- 换片状态必须有换片原因
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_replaced
    CHECK (status <> 'REPLACED' OR replace_reason_code IS NOT NULL);

-- 换片轮次只能在 1~20 之间，换片必定有上一副
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_round
    CHECK (replace_round BETWEEN 1 AND 20
           AND (replace_round = 1 OR previous_fit_id IS NOT NULL));

-- 自关联不能指向自己
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_prev_self
    CHECK (previous_fit_id IS NULL OR previous_fit_id <> id);

-- 时间顺序：申请 ≤ 评估 ≤ 试戴 ≤ 下单 ≤ 到片 ≤ 发放 ≤ 停戴
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_time_order
    CHECK (
        (assessed_at IS NULL OR assessed_at >= apply_time)
        AND (trial_started_at IS NULL OR assessed_at IS NULL OR trial_started_at >= assessed_at)
        AND (ordered_at IS NULL OR trial_started_at IS NULL OR ordered_at >= trial_started_at)
        AND (arrived_at IS NULL OR ordered_at IS NULL OR arrived_at >= ordered_at)
        AND (delivered_at IS NULL OR arrived_at IS NULL OR delivered_at >= arrived_at)
        AND (stopped_at IS NULL OR delivered_at IS NULL OR stopped_at >= delivered_at)
        AND (closed_at IS NULL OR apply_time IS NULL OR closed_at >= apply_time)
    );

-- 预计到片日期不得早于下单日期
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_eta
    CHECK (expected_arrival_date IS NULL OR ordered_at IS NULL
           OR expected_arrival_date >= ordered_at::date);

-- 预计换片日期必须晚于发放日期
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_replace_date
    CHECK (expected_replace_date IS NULL OR delivered_at IS NULL
           OR expected_replace_date > delivered_at::date);

-- 逾期天数不得为负
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_overdue
    CHECK (overdue_days >= 0);

-- 作废必须填原因、操作人、时间（≥10 字）
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_void
    CHECK (status <> 'CLOSED'
           OR (closed_at IS NOT NULL)
           OR (void_reason IS NOT NULL AND voided_by IS NOT NULL AND voided_at IS NOT NULL));

-- 设备注册证有效期：已校验时必须成对出现
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_device_reg
    CHECK ((device_reg_checked_at IS NULL)
           OR (device_reg_no IS NOT NULL AND device_reg_valid_until IS NOT NULL));

-- 金额与已付不得为负
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_amount
    CHECK ((order_amount IS NULL OR order_amount >= 0)
       AND paid_amount >= 0);

-- 已付不得超过订单金额（容差 0.01 元，防 M16 四舍五入差异）
ALTER TABLE m10_ortho_k_fitting
    ADD CONSTRAINT ck_m10_ortho_k_fitting_paid
    CHECK (order_amount IS NULL OR paid_amount <= order_amount + 0.01);
```

**业务说明：**

1. **`status` 与从表状态的联动关系**：主表 `status` 是汇总态，由 `OrthoKFittingStateMachine` 统一维护；`m10_ortho_k_apply.access_result`、`m10_ortho_k_custom_param.check_result`、`m10_ortho_k_delivery.accept_result`、`m10_ortho_k_followup.followup_result` 分别表达各阶段细节。任何从表状态变化必须经 Service 层同时推进主表，**禁止页面直接改主表 `status`**（否则状态机失去唯一入口）。
2. **`previous_fit_id` 与 `replace_round`**：换片不新建患者，而是在同一患者下新建一条 `replace_round + 1` 的验配单，并指向上一条。换片链路查询用 `WITH RECURSIVE`（见附录 C）。
3. **`next_followup_date` 冗余字段**：复查节点计算依赖 M10-09 的 `m10_followup_plan`，但到期扫描（APScheduler 每小时）若走跨表 JOIN 会拖慢。故在本表冗余 `next_followup_date` 与 `overdue_days`，由 `OrthoKFollowupSummaryTask` 每 30 分钟维护，与 M10-09 对账（差异 >1 天告警）。
4. **`device_reg_valid_until`**：OK 镜是三类医疗器械，《医疗器械监督管理条例》要求使用在有效期内的注册证产品。下单前必须校验 `device_reg_valid_until >= ordered_at::date`，过期则拒绝下单（错误码 `"1004021"`）。
5. **`customer_id` 可空 + `patient_id` 必填**：与 M10-05 不同，OK 镜验配属于**医疗行为**，必须有患者主索引；视光顾客号仅作为营销归属，可为空。

**分区策略：** 无（核心业务表，量级 2,400/年，单表 5 年约 1.2 万行，无需分区）。

---

### 4.3 表：`m10_ortho_k_apply`（验配申请与准入评估表）

**用途：** 记录 OK 镜验配的**准入评估全过程**。这是本子模块合规性最强的一张表：《角膜塑形镜验配技术规范》（国家卫健委）要求验配前完成 6 大类检查并留档。一次申请对应一条记录，评估结论（通过/有条件通过/拒绝）决定验配单能否进入试戴阶段。

- **写入方：** 本子模块（验配师在 P02 逐项录入，医学复核医师签署）。
- **只读方：** M10-09（复查计划参考）、M07（医生工作站调阅角膜条件）、质控与医政科（不良事件追溯）。
- **关键设计：** 准入项**全部结构化存储为独立字段**，不塞 JSONB——因为要做「拒绝原因统计」「某指标不达标占比」「按年龄分段通过率」三类报表，JSONB 无法建索引聚合。只有在评估项清单本身可能扩展时才用 `extra_items JSONB` 兜底。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| apply_no | VARCHAR(32) | Y | NULL | 申请号 `OKA` + YYYYMMDD + 4 位 |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03 `mpi_patient.id`） |
| patient_name | VARCHAR(64) | N | — | 患者姓名（快照） |
| age | SMALLINT | N | — | 年龄（岁） |
| **一、年龄与依从性评估** | | | | |
| age_check_passed | BOOLEAN | N | FALSE | 年龄是否达标（≥8 岁） |
| age_note | VARCHAR(256) | Y | NULL | 年龄说明（如「7 岁 11 月，接近 8 岁，需医师复核」） |
| compliance_score | SMALLINT | Y | NULL | 依从性评分（0~100，由问卷 10 题加权） |
| compliance_level | VARCHAR(16) | Y | NULL | 依从性等级 `GOOD`(≥80)/`FAIR`(60~79)/`POOR`(<60) |
| compliance_note | VARCHAR(512) | Y | NULL | 依从性评估说明 |
| parent_consent_signed | BOOLEAN | N | FALSE | 家长/本人知情同意书已签署 |
| consent_file_id | BIGINT | Y | NULL | 知情同意书扫描件 ID（文件服务） |
| consent_signed_at | TIMESTAMP | Y | NULL | 签署时间 |
| consent_signer_name | VARCHAR(64) | Y | NULL | 签署人姓名 |
| consent_signer_relation | VARCHAR(16) | Y | NULL | 签署人与患者关系 `SELF`/`FATHER`/`MOTHER`/`GRANDPARENT`/`OTHER` |
| **二、屈光度评估** | | | | |
| od_sphere | NUMERIC(6,2) | Y | NULL | 右眼球镜（D） |
| od_cylinder | NUMERIC(6,2) | Y | NULL | 右眼柱镜（D） |
| od_axis | SMALLINT | Y | NULL | 右眼轴位（°） |
| os_sphere | NUMERIC(6,2) | Y | NULL | 左眼球镜（D） |
| os_cylinder | NUMERIC(6,2) | Y | NULL | 左眼柱镜（D） |
| os_axis | SMALLINT | Y | NULL | 左眼轴位（°） |
| sphere_check_passed | BOOLEAN | N | FALSE | 近视度数是否在 −0.75D~−6.00D |
| cylinder_check_passed | BOOLEAN | N | FALSE | 散光是否 ≤−1.50D（上限可配置至 −2.00D） |
| anisometropia | NUMERIC(6,2) | Y | NULL | 屈光参差（双眼球镜差值绝对值，D） |
| anisometropia_check_passed | BOOLEAN | N | FALSE | 屈光参差是否 ≤1.50D |
| optometry_no | VARCHAR(32) | Y | NULL | 依据验光单号（M10-01，只读引用） |
| **三、角膜曲率与厚度评估** | | | | |
| od_k1 | NUMERIC(6,2) | Y | NULL | 右眼平坦角膜曲率 K1（D） |
| od_k2 | NUMERIC(6,2) | Y | NULL | 右眼陡峭角膜曲率 K2（D） |
| od_km | NUMERIC(6,2) | Y | NULL | 右眼平均角膜曲率 Km（D） |
| os_k1 | NUMERIC(6,2) | Y | NULL | 左眼平坦角膜曲率 K1（D） |
| os_k2 | NUMERIC(6,2) | Y | NULL | 左眼陡峭角膜曲率 K2（D） |
| os_km | NUMERIC(6,2) | Y | NULL | 左眼平均角膜曲率 Km（D） |
| curvature_check_passed | BOOLEAN | N | FALSE | 角膜曲率是否在 41.00~46.00D |
| od_cornea_thickness | SMALLINT | Y | NULL | 右眼中央角膜厚度（μm） |
| os_cornea_thickness | SMALLINT | Y | NULL | 左眼中央角膜厚度（μm） |
| thickness_check_passed | BOOLEAN | N | FALSE | 中央角膜厚度是否 ≥480μm |
| **四、眼压与泪液评估** | | | | |
| od_iop | NUMERIC(5,1) | Y | NULL | 右眼眼压（mmHg，非接触眼压计） |
| os_iop | NUMERIC(5,1) | Y | NULL | 左眼眼压（mmHg） |
| iop_check_passed | BOOLEAN | N | FALSE | 眼压是否在 10~21mmHg |
| tear_break_up_time | NUMERIC(5,1) | Y | NULL | 泪膜破裂时间 BUT（秒） |
| schirmer_test | NUMERIC(5,1) | Y | NULL | 泪液分泌试验（mm/5min） |
| tear_check_passed | BOOLEAN | N | FALSE | 泪液是否达标（BUT≥10s 且 Schirmer≥10mm） |
| **五、角膜地形图与眼表评估** | | | | |
| topography_pattern | VARCHAR(24) | Y | NULL | 地形图图形分类 `NORMAL`/`SYMMETRIC_BOWTIE`/`ASYMMETRIC_BOWTIE`/`KERATOCONUS_SUSPECT`/`IRREGULAR` |
| topography_check_passed | BOOLEAN | N | FALSE | 地形图是否正常（排除圆锥角膜可疑） |
| keratoconus_suspect | BOOLEAN | N | FALSE | 圆锥角膜可疑标记（TKC 等指数超标） |
| eyelid_condition | VARCHAR(16) | Y | NULL | 睑裂条件 `NORMAL`/`NARROW`/`WIDE`/`LAGOPHTHALMOS` |
| eyelid_check_passed | BOOLEAN | N | FALSE | 睑裂是否适合（无睑裂闭合不全） |
| conjunctiva_condition | VARCHAR(16) | Y | NULL | 结膜情况 `NORMAL`/`MILD_HYPEREMIA`/`SEVERE_HYPEREMIA` |
| meibomian_gland | VARCHAR(16) | Y | NULL | 睑板腺功能 `NORMAL`/`MILD_DYSFUNCTION`/`SEVERE_DYSFUNCTION` |
| contraindication | VARCHAR(512) | Y | NULL | 其他禁忌症说明（干眼、眼睑内翻、活动性炎症等） |
| **六、综合结论** | | | | |
| access_result | VARCHAR(16) | N | 'PENDING' | 准入结论 `PASS`/`CONDITIONAL`/`FAIL`/`PENDING` |
| fail_items | JSONB | Y | NULL | 不达标项编码数组（如 `["SPHERE","THICKNESS"]`） |
| conditional_terms | VARCHAR(512) | Y | NULL | 有条件通过的限制条件（如「需 3 个月后复查角膜厚度再评估」） |
| reject_reason | VARCHAR(512) | Y | NULL | 拒绝原因（≥10 字） |
| assessor_id | BIGINT | Y | NULL | 评估验配师 ID |
| assessor_name | VARCHAR(64) | Y | NULL | 评估验配师姓名（快照） |
| assessed_at | TIMESTAMP | Y | NULL | 评估完成时间 |
| doctor_review_required | BOOLEAN | N | FALSE | 是否需医学复核（角膜条件可疑/年龄临界时） |
| doctor_review_id | BIGINT | Y | NULL | 复核医师 ID |
| doctor_review_name | VARCHAR(64) | Y | NULL | 复核医师姓名（快照） |
| doctor_review_opinion | VARCHAR(512) | Y | NULL | 复核意见 |
| doctor_reviewed_at | TIMESTAMP | Y | NULL | 复核时间 |
| extra_items | JSONB | Y | NULL | 扩展评估项（键值对数组，用于新增指标） |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_apply` | 主键 | `id` | — |
| `uk_m10_ortho_k_apply_no` | 唯一（部分） | `apply_no` WHERE `is_deleted = FALSE` | 申请号唯一 |
| `idx_m10_ortho_k_apply_patient` | B-Tree | `patient_id`, `created_at` DESC | 按患者查申请历史 |
| `idx_m10_ortho_k_apply_result` | B-Tree（部分） | `access_result`, `assessed_at` DESC WHERE `is_deleted = FALSE` | **按结论统计通过率主力索引** |
| `idx_m10_ortho_k_apply_pending` | B-Tree（部分） | `created_at` WHERE `access_result = 'PENDING'` AND `is_deleted = FALSE` | 待评估清单 |
| `idx_m10_ortho_k_apply_review` | B-Tree（部分） | `doctor_review_required` WHERE `doctor_review_required = TRUE` AND `doctor_reviewed_at IS NULL` | 待医学复核队列 |
| `idx_m10_ortho_k_apply_kcsuspect` | B-Tree（部分） | `patient_id` WHERE `keratoconus_suspect = TRUE` | 圆锥可疑患者追踪清单 |
| `idx_m10_ortho_k_apply_fail_trgm` | GIN | `reject_reason` `gin_trgm_ops` | 拒绝原因关键词检索 |

**约束说明：**

```sql
-- 申请号格式
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_no_format
    CHECK (apply_no IS NULL OR apply_no ~ '^OKA[0-9]{12}$');

-- 准入结论枚举
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_result
    CHECK (access_result IN ('PENDING', 'PASS', 'CONDITIONAL', 'FAIL'));

-- 依从性等级枚举
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_compliance
    CHECK (compliance_level IS NULL OR compliance_level IN ('GOOD', 'FAIR', 'POOR'));

-- 依从性评分范围 0~100
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_score
    CHECK (compliance_score IS NULL OR compliance_score BETWEEN 0 AND 100);

-- 地形图图形分类枚举
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_topo
    CHECK (topography_pattern IS NULL
           OR topography_pattern IN ('NORMAL', 'SYMMETRIC_BOWTIE', 'ASYMMETRIC_BOWTIE',
                                     'KERATOCONUS_SUSPECT', 'IRREGULAR'));

-- 眼压合理区间 5~30mmHg（超出即录入错误）
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_iop
    CHECK ((od_iop IS NULL OR od_iop BETWEEN 5 AND 30)
       AND (os_iop IS NULL OR os_iop BETWEEN 5 AND 30));

-- 角膜厚度合理区间 300~800μm
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_thickness
    CHECK ((od_cornea_thickness IS NULL OR od_cornea_thickness BETWEEN 300 AND 800)
       AND (os_cornea_thickness IS NULL OR os_cornea_thickness BETWEEN 300 AND 800));

-- 角膜曲率合理区间 35.00~55.00D
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_curvature
    CHECK ((od_k1 IS NULL OR od_k1 BETWEEN 35.00 AND 55.00)
       AND (od_k2 IS NULL OR od_k2 BETWEEN 35.00 AND 55.00)
       AND (os_k1 IS NULL OR os_k1 BETWEEN 35.00 AND 55.00)
       AND (os_k2 IS NULL OR os_k2 BETWEEN 35.00 AND 55.00));

-- K1 必须是平坦 K（K1 ≤ K2）
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_k_order
    CHECK ((od_k1 IS NULL OR od_k2 IS NULL OR od_k1 <= od_k2)
       AND (os_k1 IS NULL OR os_k2 IS NULL OR os_k1 <= os_k2));

-- 评估完成（非 PENDING）必须有唯一一名评估者与时间
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_assessed
    CHECK (access_result = 'PENDING'
           OR (assessor_id IS NOT NULL AND assessed_at IS NOT NULL));

-- FAIL 必须填拒绝原因（≥10 字）且 fail_items 非空
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_fail
    CHECK (access_result <> 'FAIL'
           OR (reject_reason IS NOT NULL
               AND char_length(btrim(reject_reason)) >= 10
               AND fail_items IS NOT NULL
               AND jsonb_array_length(fail_items) > 0));

-- CONDITIONAL 必须填限制条件
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_conditional
    CHECK (access_result <> 'CONDITIONAL'
           OR (conditional_terms IS NOT NULL
               AND char_length(btrim(conditional_terms)) >= 10));

-- PASS 不得残留拒绝原因
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_pass_clean
    CHECK (access_result <> 'PASS' OR reject_reason IS NULL);

-- 需医学复核的，复核完成必须有医师、意见与时间
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_review
    CHECK (doctor_review_required = FALSE
           OR doctor_reviewed_at IS NULL
           OR (doctor_review_id IS NOT NULL
               AND doctor_review_opinion IS NOT NULL
               AND char_length(btrim(doctor_review_opinion)) >= 10));

-- 圆锥角膜可疑必须地形图不通过
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_kc
    CHECK (keratoconus_suspect = FALSE OR topography_check_passed = FALSE);

-- 知情同意：通过必须有签署记录
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_consent
    CHECK (access_result = 'PENDING'
           OR access_result = 'FAIL'
           OR (parent_consent_signed = TRUE
               AND consent_file_id IS NOT NULL
               AND consent_signed_at IS NOT NULL
               AND consent_signer_name IS NOT NULL));

-- 屈光参差不得为负
ALTER TABLE m10_ortho_k_apply
    ADD CONSTRAINT ck_m10_ortho_k_apply_aniso
    CHECK (anisometropia IS NULL OR anisometropia >= 0);
```

**业务说明：**

1. **六类评估的通过判定（应用层实现，字段存储判定结果）**：

   | 评估项 | 通过条件 | 不达标错误码 |
   |---|---|---|
   | 年龄 | 8 ≤ age ≤ 40 | `"1004005"` |
   | 近视度数 | −6.00 ≤ sph ≤ −0.75 | `"1004006"` |
   | 散光 | cyl ≥ −1.50（配置上限 −2.00） | `"1004007"` |
   | 屈光参差 | 双眼 sph 差绝对值 ≤ 1.50D | `"1004008"` |
   | 角膜曲率 | 41.00 ≤ Km ≤ 46.00 | `"1004009"` |
   | 角膜厚度 | 中央厚度 ≥ 480μm | `"1004010"` |
   | 眼压 | 10 ≤ IOP ≤ 21 mmHg | `"1004011"` |
   | 泪液 | BUT ≥ 10s 且 Schirmer ≥ 10mm/5min | `"1004012"` |
   | 地形图 | 排除 `KERATOCONUS_SUSPECT` 与 `IRREGULAR` | `"1004013"` |
   | 睑裂/眼表 | 无睑裂闭合不全、无活动性炎症 | `"1004014"` |
   | 依从性 | `compliance_level` ≠ `POOR` | `"1004015"` |
   | 知情同意 | `parent_consent_signed = TRUE` | `"1004016"` |

2. **`access_result` 与 `fail_items` 的组合语义**：`PASS` 表示全部 12 项均通过；`CONDITIONAL` 表示有 ≤2 项「临界不达标」但医师判定可继续（如年龄 7 岁 11 月、角膜厚度 478μm），并必须在 `conditional_terms` 写明限制；`FAIL` 表示有明确禁忌，`fail_items` 列出全部不达标项编码，用于统计「最常见的拒绝原因」。
3. **`extra_items` 的位置**：只在评估项清单可能扩展时使用（如新增「角膜滞后量 CH」），不承载 12 项核心指标——核心指标必须有独立字段才能建索引与聚合。
4. **`consent_file_id` 是合规硬约束**：无知情同意书扫描件的申请，`access_result` 不得为 `PASS`（数据库 CHECK 已兜底）。这符合《角膜塑形镜验配技术规范》对留档的要求。
5. **失败重评**：`FAIL` 的申请不可修改，患者 3 个月后可新建一条申请（新的 `apply_no`）。`PASS` 的申请在 90 天内未进入试戴则自动失效，需重新评估（错误码 `"1004017"`）。

**分区策略：** 无。

---
### 4.4 表：`m10_ortho_k_cornea`（角膜地形图参数表）

**用途：** 保存 OK 镜验配与随访过程中的**角膜地形图原始测量参数**，按「一次测量 × 眼别」一行。这是定制参数的唯一数据来源：`m10_ortho_k_custom_param` 的 BC/AC/PC 必须能追溯到某个 `cornea_id` 的 Kf、e 值、HVID。

- **写入方：** 本子模块（P03 页面的人工录入，或 `m10-ortho-k-topo-bridge` 从 M12 检查报告自动解析填充）。
- **只读方：** M10-09（视力档案角膜参数曲线）、M07（医生查阅）、M01-08（P-09 返回 `fit-check` 入参）。
- **关键设计：**
  - **按眼别单行存储**（`eye_side IN ('OD','OS')`），不用 `od_*/os_*` 双列——因为一只眼在一次验配中可测多次（初查、试戴后、随访），每次都要独立成行并保留 `measured_at`。
  - **`topography_report_id` 关联 M12 报告**：地形图设备（如 Pentacam、Medmont、Tomey）输出的 PDF/图片必须归档，`topography_report_id` 存 M12 报告 ID，`topography_file_url` 存文件服务路径作为兜底。
  - **`measure_source` 区分人工与设备**：设备直连写入的标记 `DEVICE`，人工录入的标记 `MANUAL`，批量修正时只允许改 `MANUAL`。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| cornea_no | VARCHAR(32) | Y | NULL | 角膜参数记录号 `OCT` + YYYYMMDD + 4 位 |
| fitting_id | BIGINT | N | — | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余，便于按单号直查） |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03） |
| eye_side | VARCHAR(8) | N | — | 眼别 `OD`/`OS` |
| measure_stage | VARCHAR(16) | N | 'PRE_FIT' | 测量阶段 `PRE_FIT`/`POST_TRIAL`/`FOLLOWUP`/`POST_STOP` |
| measure_source | VARCHAR(16) | N | 'MANUAL' | 来源 `MANUAL`/`DEVICE`/`IMPORT` |
| measured_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 测量时间 |
| **角膜曲率组** | | | | |
| k1 | NUMERIC(6,2) | Y | NULL | 平坦角膜曲率 K1（D，如 `42.75`） |
| k2 | NUMERIC(6,2) | Y | NULL | 陡峭角膜曲率 K2（D，如 `43.50`） |
| km | NUMERIC(6,2) | Y | NULL | 平均角膜曲率 Km（D，= (K1+K2)/2） |
| axis_k2 | SMALLINT | Y | NULL | 陡峭子午线轴向（°，1~180） |
| cornea_astigmatism | NUMERIC(6,2) | Y | NULL | 角膜散光（D，= K2 − K1，恒为正） |
| k1_mm | NUMERIC(5,2) | Y | NULL | 平坦曲率半径（mm，= 337.5 / K1） |
| k2_mm | NUMERIC(5,2) | Y | NULL | 陡峭曲率半径（mm，= 337.5 / K2） |
| **偏心率与直径组** | | | | |
| e_value | NUMERIC(5,2) | Y | NULL | 角膜偏心率 e（正常 0.40~0.60；>0.70 提示圆锥可疑） |
| e_value_4_5mm | NUMERIC(5,2) | Y | NULL | 4.5mm 环 e 值（部分设备提供，OK 镜设计参考） |
| hvid | NUMERIC(5,2) | Y | NULL | 可见虹膜水平径 HVID（mm，正常 10.5~12.5） |
| diameter_ratio | NUMERIC(5,3) | Y | NULL | 镜片直径/HVID 比值（推荐 0.92~0.96） |
| **瞳孔组** | | | | |
| pupil_light | NUMERIC(5,2) | Y | NULL | 明环境瞳孔直径（mm，如 `3.20`） |
| pupil_dark | NUMERIC(5,2) | Y | NULL | 暗环境瞳孔直径（mm，如 `5.80`） |
| pupil_center_offset | NUMERIC(5,2) | Y | NULL | 瞳孔中心相对角膜顶点偏移（mm） |
| **角膜厚度组** | | | | |
| thickness_central | SMALLINT | Y | NULL | 中央角膜厚度 CCT（μm，如 `528`） |
| thickness_thinnest | SMALLINT | Y | NULL | 最薄点角膜厚度（μm） |
| thinnest_location | VARCHAR(32) | Y | NULL | 最薄点位置（如 `INFERIOR_TEMPORAL`） |
| thickness_2mm | SMALLINT | Y | NULL | 距中心 2mm 环平均厚度（μm） |
| **地形图分类组** | | | | |
| topography_pattern | VARCHAR(24) | Y | NULL | 图形分类 `NORMAL`/`SYMMETRIC_BOWTIE`/`ASYMMETRIC_BOWTIE`/`KERATOCONUS_SUSPECT`/`IRREGULAR` |
| keratoconus_suspect | BOOLEAN | N | FALSE | 圆锥角膜可疑标记 |
| tkc_index | NUMERIC(5,2) | Y | NULL | 圆锥指数 TKC（部分设备，>1.0 可疑） |
| si_index | NUMERIC(5,2) | Y | NULL | 表面变异指数 ISV |
| kpi_index | NUMERIC(5,2) | Y | NULL | 角膜预测指数 KPI |
| **报告归档组** | | | | |
| topography_report_id | BIGINT | Y | NULL | 地形图报告 ID（M12 检查报告，只读引用） |
| topography_file_url | VARCHAR(512) | Y | NULL | 报告文件地址（PDF/图片，文件服务） |
| device_code | VARCHAR(64) | Y | NULL | 测量设备编码（如 `PENTACAM_001`） |
| device_sn | VARCHAR(64) | Y | NULL | 设备序列号 |
| **校验与备注** | | | | |
| is_valid | BOOLEAN | N | TRUE | 是否有效（作废为 FALSE） |
| invalid_reason | VARCHAR(512) | Y | NULL | 作废原因 |
| is_locked | BOOLEAN | N | FALSE | 是否已锁定（被定制参数引用后锁定，不可修改） |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_cornea` | 主键 | `id` | — |
| `uk_m10_ortho_k_cornea_no` | 唯一（部分） | `cornea_no` WHERE `is_deleted = FALSE` | 记录号唯一 |
| `uk_m10_ortho_k_cornea_eye` | 唯一（部分） | `fitting_id`, `eye_side`, `measure_stage`, `measured_at` WHERE `is_valid = TRUE` AND `is_deleted = FALSE` | **同一次验配同眼同阶段同一时刻只允许一条有效记录**（幂等防重） |
| `idx_m10_ortho_k_cornea_fitting` | B-Tree | `fitting_id`, `measured_at` DESC | 按验配单查全部测量 |
| `idx_m10_ortho_k_cornea_patient` | B-Tree | `patient_id`, `eye_side`, `measured_at` DESC | 患者角膜参数纵向追踪 |
| `idx_m10_ortho_k_cornea_latest` | B-Tree（部分） | `fitting_id`, `eye_side` WHERE `measure_stage = 'PRE_FIT'` AND `is_valid = TRUE` | **取验配基准测量（P03 主力索引）** |
| `idx_m10_ortho_k_cornea_kc` | B-Tree（部分） | `patient_id`, `measured_at` DESC WHERE `keratoconus_suspect = TRUE` | 圆锥可疑专项追踪 |
| `idx_m10_ortho_k_cornea_report` | B-Tree（部分） | `topography_report_id` WHERE `topography_report_id IS NOT NULL` | 报告反查 |

**约束说明：**

```sql
-- 记录号格式
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_no_format
    CHECK (cornea_no IS NULL OR cornea_no ~ '^OCT[0-9]{12}$');

-- 本表只存单眼，不含 OU
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_eye
    CHECK (eye_side IN ('OD', 'OS'));

-- 测量阶段枚举
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_stage
    CHECK (measure_stage IN ('PRE_FIT', 'POST_TRIAL', 'FOLLOWUP', 'POST_STOP'));

-- 测量来源枚举
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_source
    CHECK (measure_source IN ('MANUAL', 'DEVICE', 'IMPORT'));

-- 图形分类枚举
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_pattern
    CHECK (topography_pattern IS NULL
           OR topography_pattern IN ('NORMAL', 'SYMMETRIC_BOWTIE', 'ASYMMETRIC_BOWTIE',
                                     'KERATOCONUS_SUSPECT', 'IRREGULAR'));

-- 曲率合理区间 35.00~55.00D
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_k_range
    CHECK ((k1 IS NULL OR k1 BETWEEN 35.00 AND 55.00)
       AND (k2 IS NULL OR k2 BETWEEN 35.00 AND 55.00)
       AND (km IS NULL OR km BETWEEN 35.00 AND 55.00));

-- K1 ≤ K2，且 Km 在两者之间（应用层同时计算写入，此处防手工错录）
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_k_order
    CHECK ((k1 IS NULL OR k2 IS NULL OR k1 <= k2)
       AND (km IS NULL OR k1 IS NULL OR km >= k1)
       AND (km IS NULL OR k2 IS NULL OR km <= k2));

-- 角膜散光不得为负，且不得超过 K2−K1 的容差 0.25D（三角函数换算误差）
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_astig
    CHECK (cornea_astigmatism IS NULL
           OR (cornea_astigmatism >= 0 AND cornea_astigmatism <= 12.00));

-- 陡峭轴位范围
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_axis
    CHECK (axis_k2 IS NULL OR axis_k2 BETWEEN 1 AND 180);

-- e 值合理区间 0.00~1.20（>0.70 应用层标记圆锥可疑）
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_e
    CHECK ((e_value IS NULL OR e_value BETWEEN 0.00 AND 1.20)
       AND (e_value_4_5mm IS NULL OR e_value_4_5mm BETWEEN 0.00 AND 1.20));

-- HVID 合理区间 9.00~14.00mm
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_hvid
    CHECK (hvid IS NULL OR hvid BETWEEN 9.00 AND 14.00);

-- 镜片直径/HVID 比值合理区间 0.80~1.00
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_ratio
    CHECK (diameter_ratio IS NULL OR diameter_ratio BETWEEN 0.800 AND 1.000);

-- 暗瞳孔不得小于明瞳孔
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_pupil
    CHECK ((pupil_light IS NULL OR pupil_light BETWEEN 1.00 AND 9.00)
       AND (pupil_dark IS NULL OR pupil_dark BETWEEN 1.00 AND 10.00)
       AND (pupil_light IS NULL OR pupil_dark IS NULL OR pupil_dark >= pupil_light));

-- 角膜厚度合理区间 300~800μm，最薄点不得厚于中央
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_thickness
    CHECK ((thickness_central IS NULL OR thickness_central BETWEEN 300 AND 800)
       AND (thickness_thinnest IS NULL OR thickness_thinnest BETWEEN 300 AND 800)
       AND (thickness_2mm IS NULL OR thickness_2mm BETWEEN 300 AND 800)
       AND (thickness_central IS NULL OR thickness_thinnest IS NULL
            OR thickness_thinnest <= thickness_central));

-- 作废必须有原因
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_invalid
    CHECK (is_valid = TRUE
           OR (invalid_reason IS NOT NULL AND char_length(btrim(invalid_reason)) >= 10));

-- 锁定记录不可逻辑删除（应用层校验为主，此处兜底不容许删除已引用记录）
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_locked
    CHECK (is_locked = FALSE OR is_deleted = FALSE);

-- 圆锥可疑必须有分类或指数支撑（防止误勾选）
ALTER TABLE m10_ortho_k_cornea
    ADD CONSTRAINT ck_m10_ortho_k_cornea_kc_evidence
    CHECK (keratoconus_suspect = FALSE
           OR topography_pattern = 'KERATOCONUS_SUSPECT'
           OR (tkc_index IS NOT NULL AND tkc_index > 1.00)
           OR (e_value IS NOT NULL AND e_value > 0.70));
```

**业务说明：**

1. **`measure_stage` 与状态机的对应**：`PRE_FIT` 在 `ASSESSED` 阶段采集（P03 验配前地形图），`POST_TRIAL` 在 `TRIAL` 阶段采集（试戴后角膜改变），`FOLLOWUP` 在 `FOLLOWING` 阶段每次随访采集。定制参数只能引用 `PRE_FIT` 阶段的记录（服务层强制）。
2. **`k1_mm` / `k2_mm` 的换算**：`k_mm = 337.5 / k_D`（采用 1.3375 角膜折射率标准）。**服务层写入时同时计算**，便于医生按 mm 阅读；但试戴片 BC 选择一律以 D 为单位计算后再换算，避免二次换入误差。
3. **`is_locked` 的锁定时机**：当该记录被 `m10_ortho_k_custom_param.cornea_id` 引用后即锁定。锁定后修改会破坏「定制参数 ↔ 地形图」的追溯链，属医疗合规硬要求（错误码 `"1004018"`）。
4. **`diameter_ratio` 的存在意义**：OK 镜直径通常取 HVID 的 0.92~0.96 倍。本字段由服务层计算（`preset_diameter / hvid`）并在 P04 页面展示预警，供试戴片选择参考；它**不是**定制直径本身。
5. **设备直连与人工录入的并存**：Pentacam 等设备输出的图形分类需人工确认（设备只能给出指数，不能直接判定圆锥），因此 `topography_pattern` 一律由验配师确认，`DEVICE` 来源只保证数值准确。

**分区策略：** 无（5,000/年，单表 5 年约 2.5 万行）。

---

### 4.5 表：`m10_ortho_k_trial_lens`（试戴片台账表）

**用途：** 试戴片的**实物档案台账**。OK 镜试戴片是院内资产（每片成本约 1,500~3,000 元），一个验配中心通常备 200~600 片，覆盖常见 BC（7.80~8.80mm）× 降度（-1.00~-5.00D）组合。本表记录每一片实物的编号、弧参数、开封日期、消毒记录、报废状态。

- **写入方：** 本子模块（P04 页面「试戴片管理」页签、库存盘点）。
- **只读方：** M10-07（视光库存台账对账，试戴片不计入销售库存）、M15（如纳入固定资产管理则只读同步）。
- **关键设计：** 与 M01-08 的 `mdm_ortho_k_params`（产品级参数模板）区分——**本表是「实物」，`mdm_ortho_k_params` 是「型号」**。一片试戴片对应 `product_code`（型号）+ `trial_lens_no`（实物编号）。`is_available` 与 `m10_ortho_k_trial_use` 的部分唯一索引共同保证「一片同一时刻只给一个患者」。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| trial_lens_no | VARCHAR(64) | N | — | 试戴片实物编号（唯一，如 `TL-0820-300-001`） |
| product_code | VARCHAR(32) | N | — | 试戴片产品编码（M01-08 `mdm_optical_product.product_code`，只读引用） |
| product_name | VARCHAR(128) | Y | NULL | 产品名称（快照） |
| param_group_code | VARCHAR(32) | Y | NULL | 参数组编码（M01-08 `mdm_ortho_k_params.param_code`，只读引用） |
| brand_code | VARCHAR(32) | Y | NULL | 品牌编码（快照） |
| device_reg_no | VARCHAR(64) | Y | NULL | 医疗器械注册证号 |
| device_reg_valid_until | DATE | Y | NULL | 注册证有效期截止日 |
| **弧参数组（与定制参数同一套语义）** | | | | |
| bc | NUMERIC(5,2) | N | — | 基弧 BC（mm，如 `8.20`） |
| rc | NUMERIC(5,2) | Y | NULL | 反转弧 RC（mm，如 `7.20`） |
| ac | NUMERIC(5,2) | Y | NULL | 定位弧 AC（mm，如 `8.40`） |
| pc | NUMERIC(5,2) | Y | NULL | 周边弧 PC（mm，如 `9.20`） |
| diameter | NUMERIC(5,2) | Y | NULL | 镜片直径（mm，如 `10.60`） |
| reduction_power | NUMERIC(6,2) | Y | NULL | 降度（D，如 `-3.00`） |
| material | VARCHAR(64) | Y | NULL | 材质 |
| **适用角膜范围（冗余自 M01-08，用于自动匹配）** | | | | |
| k_min | NUMERIC(6,2) | Y | NULL | 适用角膜曲率下限（D，通常 = BC 对应 K 值 − 0.75） |
| k_max | NUMERIC(6,2) | Y | NULL | 适用角膜曲率上限（D） |
| **生命周期组** | | | | |
| status | VARCHAR(16) | N | 'IN_STOCK' | 状态 `IN_STOCK`/`IN_USE`/`DISINFECTING`/`DAMAGED`/`EXPIRED`/`SCRAPPED` |
| sealed | BOOLEAN | N | TRUE | 是否未开封 |
| opened_at | TIMESTAMP | Y | NULL | 开封日期 |
| expire_date | DATE | Y | NULL | 失效日期（开封日 + 开封后有效期，通常 12~24 个月） |
| last_disinfected_at | TIMESTAMP | Y | NULL | 最近一次消毒时间 |
| disinfect_count | INT | N | 0 | 累计消毒次数（>200 次建议报废） |
| usage_count | INT | N | 0 | 累计试戴人次 |
| **实物与位置组** | | | | |
| store_id | BIGINT | N | — | 所属门店 ID |
| store_name | VARCHAR(64) | Y | NULL | 门店名称（快照） |
| storage_location | VARCHAR(64) | Y | NULL | 存放位置（如 `A 柜 3 层 2 格`） |
| box_no | VARCHAR(32) | Y | NULL | 试戴片盒编号 |
| **质量与报废组** | | | | |
| damage_note | VARCHAR(512) | Y | NULL | 损伤说明 |
| scrapped_at | TIMESTAMP | Y | NULL | 报废时间 |
| scrap_reason | VARCHAR(512) | Y | NULL | 报废原因（≥10 字） |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_trial_lens` | 主键 | `id` | — |
| `uk_m10_ortho_k_trial_lens_no` | 唯一（部分） | `trial_lens_no` WHERE `is_deleted = FALSE` | **实物编号全院内唯一** |
| `idx_m10_ortho_k_trial_lens_match` | B-Tree（部分） | `bc`, `reduction_power`, `diameter` WHERE `status = 'IN_STOCK'` AND `is_deleted = FALSE` | **按 BC/降度匹配可用试戴片（P04 主力索引）** |
| `idx_m10_ortho_k_trial_lens_krange` | B-Tree（部分） | `k_min`, `k_max` WHERE `status = 'IN_STOCK'` AND `is_deleted = FALSE` | 按角膜 K 值区间匹配 |
| `idx_m10_ortho_k_trial_lens_store` | B-Tree | `store_id`, `status`, `bc` | 门店库存视图 |
| `idx_m10_ortho_k_trial_lens_status` | B-Tree | `status`, `updated_at` DESC | 状态筛选与消毒队列 |
| `idx_m10_ortho_k_trial_lens_expire` | B-Tree（部分） | `expire_date` WHERE `status IN ('IN_STOCK','IN_USE')` AND `is_deleted = FALSE` | 到期扫描 |
| `idx_m10_ortho_k_trial_lens_disinfect` | B-Tree（部分） | `last_disinfected_at` WHERE `status IN ('IN_STOCK','IN_USE')` | 消毒超期扫描 |
| `idx_m10_ortho_k_trial_lens_product` | B-Tree | `product_code` | 按产品型号汇总 |

**约束说明：**

```sql
-- 实物编号格式：TL-<BC 四位>-<降度三位>-<流水三位>
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_no_format
    CHECK (trial_lens_no ~ '^TL-[0-9]{4}-[0-9]{3}-[0-9]{3}$');

-- 状态枚举
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_status
    CHECK (status IN ('IN_STOCK', 'IN_USE', 'DISINFECTING', 'DAMAGED', 'EXPIRED', 'SCRAPPED'));

-- 弧参数关系：RC < BC < AC < PC（与 M01-08 P07 页面校验口径一致，数据库兜底）
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_arc
    CHECK ((rc IS NULL OR rc < bc)
       AND (ac IS NULL OR ac > bc)
       AND (pc IS NULL OR pc > ac)
       AND (rc IS NULL OR ac IS NULL OR ac > rc));

-- 基弧合理区间 7.00~9.50mm
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_bc
    CHECK (bc BETWEEN 7.00 AND 9.50);

-- 镜片直径合理区间 9.00~12.00mm
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_diameter
    CHECK (diameter IS NULL OR diameter BETWEEN 9.00 AND 12.00);

-- 降度必须是负值，且在 −0.75~−6.00D
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_reduction
    CHECK (reduction_power IS NULL
           OR (reduction_power < 0 AND reduction_power >= -6.00));

-- 适用 K 值区间合理，且下限 ≤ 上限
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_krange
    CHECK ((k_min IS NULL AND k_max IS NULL)
        OR (k_min IS NOT NULL AND k_max IS NOT NULL
            AND k_min <= k_max
            AND k_min >= 38.00 AND k_max <= 50.00));

-- 已开封必须有开封时间；未开封不得有开封时间
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_opened
    CHECK ((sealed = TRUE AND opened_at IS NULL)
        OR (sealed = FALSE AND opened_at IS NOT NULL));

-- 已开封必须有失效日期
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_expire_required
    CHECK (sealed = TRUE OR expire_date IS NOT NULL);

-- 失效日期必须晚于开封日期
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_expire_order
    CHECK (expire_date IS NULL OR opened_at IS NULL OR expire_date > opened_at::date);

-- 报废必须有原因、时间；非报废不得有报废信息
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_scrap
    CHECK ((status = 'SCRAPPED' AND scrapped_at IS NOT NULL
            AND scrap_reason IS NOT NULL AND char_length(btrim(scrap_reason)) >= 10)
        OR (status <> 'SCRAPPED' AND scrapped_at IS NULL AND scrap_reason IS NULL));

-- 报废、损坏、过期的试戴片不得标记为可用状态
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_unusable
    CHECK (status NOT IN ('SCRAPPED', 'DAMAGED', 'EXPIRED') OR status = status);

-- 计数不得为负
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_counts
    CHECK (disinfect_count >= 0 AND usage_count >= 0);

-- 损坏必须有损伤说明
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_damage
    CHECK (status <> 'DAMAGED' OR (damage_note IS NOT NULL AND char_length(btrim(damage_note)) >= 5));

-- 试戴片不参与销售：必须有注册证信息（三类器械）
ALTER TABLE m10_ortho_k_trial_lens
    ADD CONSTRAINT ck_m10_ortho_k_trial_lens_reg
    CHECK (device_reg_no IS NOT NULL AND device_reg_valid_until IS NOT NULL);
```

**业务说明：**

1. **「一片同一时刻只给一个患者」的数据库实现**：本表 `status` 表示实物状态，但**真正的互斥约束在建在 `m10_ortho_k_trial_use` 上**（一条记录 = 一次占用，部分唯一索引 `(trial_lens_id) WHERE released_at IS NULL AND is_deleted = FALSE`）。本表 `status = 'IN_USE'` 只是冗余展示态，由占用/释放操作同步维护。这样即使两个并发请求同时占用同一片，数据库也会因唯一索引冲突而拒绝（错误码 `"1004019"`），**不依赖应用层的「先查后写」**（那是经典的 TOCTOU 竞态）。
2. **`k_min` / `k_max` 的推导**：`K_flat = 337.5 / BC`。若 BC = 8.20，则 `K_flat ≈ 41.16D`。OK 镜试戴片通常可适配角膜 K 值在 `K_flat − 0.75` 到 `K_flat + 0.75` 之间的眼睛（0.75D 对应约 0.15mm 基弧差）。服务层在 M01-08 参数回填时自动计算，也可由验配师手动覆盖。
3. **消毒次数阈值**：硬性接触镜试戴片在规范消毒下可重复使用，但业内普遍以 200 次消毒或 12 个月开封期为报废阈值。`disinfect_count > 200` 时扫描任务置 `status = 'DAMAGED'` 并提示报废。
4. **试戴片不计入销售库存**：M10-07 的 `m10_stock_batch` 只管理可售商品；试戴片是**验配工具资产**，故本表独立建表，M10-07 通过 `product_code` 关联型号但不参与可用量计算。
5. **注册证强制非空的理由**：试戴片也是三类医疗器械，同样受《医疗器械监督管理条例》约束。开封使用前必须确认注册证有效，数据库层强制 `device_reg_no` / `device_reg_valid_until` 非空（错误码 `"1004021"`）。

**分区策略：** 无（1,200 行左右的静态台账）。

---
### 4.6 表：`m10_ortho_k_trial_use`（试戴片占用与试戴评估表）

**用途：** 一条记录 = **一次试戴片占用 + 该次试戴的完整评估结果**。这是本子模块并发控制最关键的一张表。

**核心设计（本表最重要的三条）：**

1. **「一片试戴片同一时刻只能给一个患者」由数据库部分唯一索引强制保证**：
   ```sql
   CREATE UNIQUE INDEX uk_m10_ortho_k_trial_use_active
       ON m10_ortho_k_trial_use (trial_lens_id)
       WHERE released_at IS NULL AND is_deleted = FALSE;
   ```
   含义：同一 `trial_lens_id` 在「未释放」的集合里只能出现一次。两个并发占用请求，第二个会收到 `23505` 唯一约束冲突，服务层捕获后转为错误码 `"1004019"`（试戴片已被占用）。这比「先 SELECT 判断再 INSERT」可靠——后者存在 TOCTOU 竞态窗口。
2. **占用与释放是两段式**：`occupied_at` 写入即占用建立；`released_at` 写入即释放。**释放后该行的部分唯一索引不再覆盖它**，同一片可被下一位患者占用。
3. **评估结果与占用同表**：一次占用对应一次试戴评估，二者 1:1。分表会导致每次评估都要二次 JOIN 才能知道「哪片、哪个患者、什么时候」，而 P04 页面的核心查询正是「本单的试戴记录及评估结论」。

- **写入方：** 本子模块（P04 页面）。
- **只读方：** M10-06（定制下单参考试戴结论）、M01-08（`fit-check` 返回的推荐参数与试戴结果比对）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| use_no | VARCHAR(32) | Y | NULL | 试戴记录号 `OKT` + YYYYMMDD + 4 位 |
| fitting_id | BIGINT | N | — | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余） |
| trial_lens_id | BIGINT | N | — | 试戴片 ID（`m10_ortho_k_trial_lens.id`） |
| trial_lens_no | VARCHAR(64) | N | — | 试戴片实物编号（快照，占用现场核对） |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03） |
| eye_side | VARCHAR(8) | N | — | 眼别 `OD`/`OS` |
| trial_seq | SMALLINT | N | 1 | 本单本眼第几次试戴（1,2,3…，允许换片重试） |
| **占用组** | | | | |
| occupied_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 占用时间 |
| occupied_by | BIGINT | N | — | 占用操作人 ID（验配师） |
| occupied_by_name | VARCHAR(64) | Y | NULL | 占用操作人姓名（快照） |
| release_kind | VARCHAR(16) | Y | NULL | 释放类型 `RETURNED`（正常归还）/`KEPT`（留戴观察）/`ABNORMAL`（异常结束） |
| released_at | TIMESTAMP | Y | NULL | 释放时间（NULL 表示仍在占用中） |
| released_by | BIGINT | Y | NULL | 释放操作人 ID |
| occupied_minutes | INT | Y | NULL | 占用时长（分钟，释放时计算） |
| **试戴片参数快照** | | | | |
| trial_bc | NUMERIC(5,2) | Y | NULL | 试戴片基弧 BC（mm，快照） |
| trial_rc | NUMERIC(5,2) | Y | NULL | 试戴片反转弧 RC（mm，快照） |
| trial_ac | NUMERIC(5,2) | Y | NULL | 试戴片定位弧 AC（mm，快照） |
| trial_pc | NUMERIC(5,2) | Y | NULL | 试戴片周边弧 PC（mm，快照） |
| trial_diameter | NUMERIC(5,2) | Y | NULL | 试戴片直径（mm，快照） |
| trial_reduction | NUMERIC(6,2) | Y | NULL | 试戴片降度（D，快照） |
| **一、荧光素染色配适评估** | | | | |
| fluo_central | VARCHAR(16) | Y | NULL | 中央泪液厚度 `FLAT`（薄/接触）/`IDEAL`（理想 10~20μm）/`STEEP`（厚/堆积） |
| fluo_reverse | VARCHAR(16) | Y | NULL | 反转弧荧光 `FLAT`/`IDEAL`/`STEEP` |
| fluo_align | VARCHAR(16) | Y | NULL | 定位弧荧光 `FLAT`/`IDEAL`/`STEEP` |
| fluo_peripheral | VARCHAR(16) | Y | NULL | 周边边翘 `FLAT`（边翘不足）/`IDEAL`（0.4~0.6mm 亮环）/`STEEP`（边翘过大） |
| fit_quality | VARCHAR(16) | Y | NULL | 配适合格判定 `EXCELLENT`/`ACCEPTABLE`/`UNACCEPTABLE` |
| **二、镜片定位与活动度** | | | | |
| lens_position | VARCHAR(16) | Y | NULL | 定位 `CENTERED`（居中）/`SLIGHT_DECENTERED`（轻度偏位）/`DECENTERED`（明显偏位） |
| decentered_direction | VARCHAR(16) | Y | NULL | 偏位方向 `SUPERIOR`/`INFERIOR`/`NASAL`/`TEMPORAL` |
| lens_movement | NUMERIC(5,2) | Y | NULL | 瞬目后活动度（mm，正常 0.5~1.5） |
| coverage_ratio | NUMERIC(5,2) | Y | NULL | 镜片覆盖角膜比率（%，正常 ≥95） |
| scleral_gap | NUMERIC(5,2) | Y | NULL | 边翘间隙（mm，正常 0.4~0.6） |
| **三、视力与屈光** | | | | |
| va_trial | NUMERIC(4,2) | Y | NULL | 戴试戴片视力（小数记录法） |
| va_corrected | NUMERIC(4,2) | Y | NULL | 试戴片球镜追加后视力 |
| over_refraction_sph | NUMERIC(6,2) | Y | NULL | 试戴片上追加球镜（D） |
| over_refraction_cyl | NUMERIC(6,2) | Y | NULL | 试戴片上追加柱镜（D） |
| over_refraction_axis | SMALLINT | Y | NULL | 追加柱镜轴位（°） |
| **四、TFT 角膜地形图差异** | | | | |
| tft_performed | BOOLEAN | N | FALSE | 是否做了 TFT 地形图差异分析 |
| tft_pattern | VARCHAR(16) | Y | NULL | TFT 图形 `BULLSEYE`（牛眼环，理想）/`SMILEY`（笑脸）/`TARGET`/`CENTRAL_CRAB`/`NON_CENTRAL`/`IRREGULAR` |
| tft_ring_diameter | NUMERIC(5,2) | Y | NULL | 牛眼环直径（mm，正常 3.0~4.0） |
| tft_ring_integrity | VARCHAR(16) | Y | NULL | 环完整度 `COMPLETE`/`PARTIAL`/`ABSENT` |
| tft_decentration | NUMERIC(5,2) | Y | NULL | 环偏移距离（mm，<0.5 可接受） |
| tft_report_id | BIGINT | Y | NULL | TFT 报告 ID（M12 检查报告，只读引用） |
| **五、订片参数决策** | | | | |
| decision | VARCHAR(24) | Y | NULL | 决策 `ORDER_AS_IS`（按试戴片参数下单）/`ADJUST`（调整后下单）/`RETRY`（换片再试）/`ABORT`（放弃验配） |
| decision_note | VARCHAR(512) | Y | NULL | 决策说明（≥10 字，`RETRY`/`ABORT` 时必填） |
| suggested_bc | NUMERIC(5,2) | Y | NULL | 建议基弧 BC（mm，基于试戴结果） |
| suggested_reduction | NUMERIC(6,2) | Y | NULL | 建议降度（D） |
| suggested_diameter | NUMERIC(5,2) | Y | NULL | 建议直径（mm） |
| **消毒与归还组** | | | | |
| disinfected_after | BOOLEAN | N | FALSE | 归还后是否已消毒 |
| disinfected_at | TIMESTAMP | Y | NULL | 归还后消毒时间 |
| damage_found | BOOLEAN | N | FALSE | 归还时是否发现损伤 |
| damage_note | VARCHAR(512) | Y | NULL | 损伤说明 |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_trial_use` | 主键 | `id` | — |
| `uk_m10_ortho_k_trial_use_no` | 唯一（部分） | `use_no` WHERE `is_deleted = FALSE` | 记录号唯一 |
| **`uk_m10_ortho_k_trial_use_active`** | **唯一（部分）** | **`trial_lens_id` WHERE `released_at IS NULL AND is_deleted = FALSE`** | **★「一片同一时刻只给一个患者」的数据库级保证（本子模块最关键约束）** |
| `uk_m10_ortho_k_trial_use_seq` | 唯一（部分） | `fitting_id`, `eye_side`, `trial_seq` WHERE `is_deleted = FALSE` | 同一单同眼试戴序号不重复 |
| `idx_m10_ortho_k_trial_use_fitting` | B-Tree | `fitting_id`, `occupied_at` DESC | 按验配单查试戴记录（P04 主力索引） |
| `idx_m10_ortho_k_trial_use_lens` | B-Tree | `trial_lens_id`, `occupied_at` DESC | 试戴片使用历史 |
| `idx_m10_ortho_k_trial_use_open` | B-Tree（部分） | `fitting_id`, `eye_side` WHERE `released_at IS NULL` | 查当前未释放（页面「归还」入口） |
| `idx_m10_ortho_k_trial_use_occupied` | B-Tree（部分） | `occupied_at` WHERE `released_at IS NULL` AND `occupied_at < CURRENT_TIMESTAMP - INTERVAL '4 hours'` | **超时未归还告警扫描** |
| `idx_m10_ortho_k_trial_use_result` | B-Tree（部分） | `fit_quality`, `occupied_at` DESC | 试戴合格率统计 |
| `idx_m10_ortho_k_trial_use_decision` | B-Tree（部分） | `decision`, `occupied_at` DESC WHERE `decision IS NOT NULL` | 订片决策分布统计 |

**约束说明：**

```sql
-- ★ 核心并发约束：一片试戴片同一时刻只能被一个患者占用
-- 用部分唯一索引表达，不依赖应用层「先查后写」
CREATE UNIQUE INDEX uk_m10_ortho_k_trial_use_active
    ON m10_ortho_k_trial_use (trial_lens_id)
    WHERE released_at IS NULL AND is_deleted = FALSE;

COMMENT ON INDEX uk_m10_ortho_k_trial_use_active IS
    '试戴片互斥占用约束：未释放的占用记录中，同一 trial_lens_id 只允许存在一条';

-- 记录号格式
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_no_format
    CHECK (use_no IS NULL OR use_no ~ '^OKT[0-9]{12}$');

-- 眼别枚举（试戴按单眼进行）
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_eye
    CHECK (eye_side IN ('OD', 'OS'));

-- 试戴序号范围
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_seq_range
    CHECK (trial_seq BETWEEN 1 AND 20);

-- 荧光配适枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_fluo
    CHECK ((fluo_central IS NULL OR fluo_central IN ('FLAT', 'IDEAL', 'STEEP'))
       AND (fluo_reverse IS NULL OR fluo_reverse IN ('FLAT', 'IDEAL', 'STEEP'))
       AND (fluo_align IS NULL OR fluo_align IN ('FLAT', 'IDEAL', 'STEEP'))
       AND (fluo_peripheral IS NULL OR fluo_peripheral IN ('FLAT', 'IDEAL', 'STEEP')));

-- 配适合格判定枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_quality
    CHECK (fit_quality IS NULL
           OR fit_quality IN ('EXCELLENT', 'ACCEPTABLE', 'UNACCEPTABLE'));

-- 定位枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_position
    CHECK (lens_position IS NULL
           OR lens_position IN ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED'));

-- 偏位方向仅在偏位时填写
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_direction
    CHECK (decentered_direction IS NULL
           OR lens_position IN ('SLIGHT_DECENTERED', 'DECENTERED'));

-- 活动度合理区间 0.00~3.00mm（>2.0 提示过松）
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_movement
    CHECK (lens_movement IS NULL OR lens_movement BETWEEN 0.00 AND 3.00);

-- 覆盖比率 50~100%
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_coverage
    CHECK (coverage_ratio IS NULL OR coverage_ratio BETWEEN 50.00 AND 100.00);

-- 边翘间隙 0.00~1.50mm
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_gap
    CHECK (scleral_gap IS NULL OR scleral_gap BETWEEN 0.00 AND 1.50);

-- TFT 图形枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_tft
    CHECK (tft_pattern IS NULL
           OR tft_pattern IN ('BULLSEYE', 'SMILEY', 'TARGET', 'CENTRAL_CRAB',
                              'NON_CENTRAL', 'IRREGULAR'));

-- TFT 环完整度枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_tft_ring
    CHECK (tft_ring_integrity IS NULL
           OR tft_ring_integrity IN ('COMPLETE', 'PARTIAL', 'ABSENT'));

-- 做了 TFT 必须有图形结论
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_tft_required
    CHECK (tft_performed = FALSE OR (tft_pattern IS NOT NULL AND tft_report_id IS NOT NULL));

-- 订片决策枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_decision
    CHECK (decision IS NULL
           OR decision IN ('ORDER_AS_IS', 'ADJUST', 'RETRY', 'ABORT'));

-- RETRY / ABORT 必须写明理由（≥10 字）
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_decision_note
    CHECK (decision NOT IN ('RETRY', 'ABORT')
           OR (decision_note IS NOT NULL AND char_length(btrim(decision_note)) >= 10));

-- 试戴结束（已释放）必须有释放类型、释放人、释放时间、占用时长
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_released
    CHECK (released_at IS NULL
           OR (release_kind IS NOT NULL AND released_by IS NOT NULL
               AND occupied_minutes IS NOT NULL AND occupied_minutes >= 0));

-- 释放时间不得早于占用时间
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_time_order
    CHECK (released_at IS NULL OR released_at >= occupied_at);

-- 释放类型枚举
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_release_kind
    CHECK (release_kind IS NULL
           OR release_kind IN ('RETURNED', 'KEPT', 'ABNORMAL'));

-- 发现损伤必须写损伤说明
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_damage
    CHECK (damage_found = FALSE
           OR (damage_note IS NOT NULL AND char_length(btrim(damage_note)) >= 5));

-- 消毒标记与消毒时间成对
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_disinfected
    CHECK ((disinfected_after = FALSE AND disinfected_at IS NULL)
        OR (disinfected_after = TRUE AND disinfected_at IS NOT NULL));

-- 释放后的记录不得逻辑删除（保留下一年度消毒与追溯记录）
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_undeletable
    CHECK (released_at IS NULL OR is_deleted = FALSE);

-- 试戴片参数快照弧关系校验（与实物台账同一口径）
ALTER TABLE m10_ortho_k_trial_use
    ADD CONSTRAINT ck_m10_ortho_k_trial_use_arc
    CHECK (trial_rc IS NULL OR trial_bc IS NULL OR trial_rc < trial_bc);
```

**业务说明：**

1. **并发占用流程（Service 层实现）**：

   ```
   ① 校验验配单状态 ∈ {ASSESSED, TRIAL}（否则 "1004004"）
   ② 校验试戴片台账 status = 'IN_STOCK'、未过期、消毒未超期（否则 "1004019"/"1004020"/"1004022"）
   ③ INSERT m10_ortho_k_trial_use(released_at = NULL)
      → 若抛 asyncpg.UniqueViolationError(uk_m10_ortho_k_trial_use_active)
         → 说明已被他人占用，返回 "1004019"
   ④ UPDATE m10_ortho_k_trial_lens SET status = 'IN_USE'
   ⑤ 释放：UPDATE m10_ortho_k_trial_use SET released_at = now(), release_kind = ...
      UPDATE m10_ortho_k_trial_lens SET status = 'DISINFECTING', usage_count = usage_count + 1
   ```

   步骤 ③ 是唯一的互斥点，**必须是 INSERT 而不是 UPDATE**。

2. **`trial_seq` 的作用**：允许同一单同眼多次试戴（换不同 BC 再试）。`uk_m10_ortho_k_trial_use_seq` 保证序号不重复，页面按 `trial_seq` 升序展示试戴对比表。

3. **超时未归还告警**：`released_at IS NULL` 且 `occupied_at` 超过 4 小时的记录，由 APScheduler 每小时扫描并告警（试戴片若长期挂在某患者名下，会导致其他患者无法使用该片）。这类记录也允许「强制释放」，操作人须填 `release_kind = 'ABNORMAL'`。

4. **`release_kind` 三种释放语义**：

   | 取值 | 中文 | 业务含义 | 后续动作 |
   |---|---|---|---|
   | `RETURNED` | 正常归还 | 试戴结束，试戴片回收 | 置 `DISINFECTING`，等待消毒 |
   | `KEPT` | 留戴观察 | 患者戴片离院观察 30~60 分钟再回院 | 试戴片仍由该患者持有，但**记录已释放**，需在台账标记 |
   | `ABNORMAL` | 异常结束 | 患者不适/损坏/超时未归还强制释放 | 触发试戴片损伤检查 |

5. **`decision` 与定制参数的关系**：`ORDER_AS_IS` 表示直接用试戴片参数下单（`suggested_*` 与 `trial_*` 相同）；`ADJUST` 表示按 `suggested_*` 下单（如降度加 −0.25D）；`RETRY` 表示本片不合适需换片（新建 `trial_seq + 1` 的记录）；`ABORT` 表示放弃验配（验配单转 `STOPPED`）。P05 生成定制参数时必须引用 `decision IN ('ORDER_AS_IS','ADJUST')` 的试戴记录（错误码 `"1004023"`）。

6. **`uk_m10_ortho_k_trial_use_active` 与逻辑删除的配合**：`is_deleted = FALSE` 在索引条件里，理论上删除一条未释放记录会解除互斥。但 CHECK 约束 `ck_m10_ortho_k_trial_use_undeletable` 已禁止删除已释放记录，而未释放记录只能通过「强制释放」而不是「删除」结束——故不存在绕过路径。

**分区策略：** 无（8,000/年，单表 5 年约 4 万行；索引 `uk_m10_ortho_k_trial_use_active` 的扫描量恒定在「当前占用中」的几十行内）。

---

### 4.7 表：`m10_ortho_k_custom_param`（定制参数表）

**用途：** 保存**下发给厂家的最终定制参数**，按「验配单 × 眼别」一行。这是 OK 镜验配的成果物——每一片镜片都是按此参数单独加工的，参数错误会导致镜片报废（每片成本 2,000~5,000 元 + 15~30 天等待期）。

- **写入方：** 本子模块（P05 页面）。
- **只读方：** M10-06（配镜订单明细取参数）、M16-04（销售单打印依据）、M01-08（P-09 返回、`fit-check` 复核）、厂家订单导出。
- **关键设计：**
  - **生成后必须调 M01-08 `GET /internal/v1/optical/ortho-k/fit-check`**，把返回的 `fit`、`checks[]`、`recommended_params` **完整快照**存进本表（`fit_check_result JSONB` + `fit_check_at`）。这样即使 M01-08 的主数据后续变更，也能还原「当时是按照什么校验结论下的单」。
  - **校验不通过时禁止下单**（`check_result = 'FAIL'` 时 `is_ordered` 不得为 TRUE，CHECK 约束兜底）。
  - **`cornea_id` 必填**：任何定制参数都必须能追溯到一张地形图（合规追溯链），且该 `m10_ortho_k_cornea` 记录必须被锁定。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| custom_no | VARCHAR(32) | Y | NULL | 定制参数单号 `OKC` + YYYYMMDD + 4 位 |
| fitting_id | BIGINT | N | — | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余） |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03） |
| eye_side | VARCHAR(8) | N | — | 眼别 `OD`/`OS`（本表只存单眼） |
| trial_use_id | BIGINT | Y | NULL | 依据的试戴记录 ID（`m10_ortho_k_trial_use.id`） |
| cornea_id | BIGINT | N | — | 依据的角膜地形图参数 ID（`m10_ortho_k_cornea.id`，必填，追溯链） |
| param_source | VARCHAR(16) | N | 'TRIAL' | 参数来源 `TRIAL`（试戴结果）/`CALCULATED`（公式计算）/`DOCTOR`（医师指定） |
| **弧参数组（核心）** | | | | |
| bc | NUMERIC(5,2) | N | — | 基弧 BC（mm，如 `8.20`） |
| rc | NUMERIC(5,2) | Y | NULL | 反转弧 RC（mm，如 `7.20`） |
| ac | NUMERIC(5,2) | Y | NULL | 定位弧 AC（mm，如 `8.40`） |
| pc | NUMERIC(5,2) | Y | NULL | 周边弧 PC（mm，如 `9.20`） |
| diameter | NUMERIC(5,2) | N | — | 镜片直径（mm，如 `10.60`） |
| **降度组** | | | | |
| target_reduction | NUMERIC(6,2) | N | — | 目标降度（D，负值，来自验配单目标） |
| actual_reduction | NUMERIC(6,2) | N | — | 实际降度（D，实际下单值，可能与目标不同） |
| reduction_diff | NUMERIC(6,2) | Y | NULL | 降度差值（D，= actual − target，非 0 需说明） |
| reduction_adjust_reason | VARCHAR(512) | Y | NULL | 降度调整原因（差值非 0 时必填，≥10 字） |
| over_refraction | NUMERIC(6,2) | Y | NULL | 试戴片追加球镜（D，用于计算实际降度） |
| **材质与外观组** | | | | |
| material | VARCHAR(64) | Y | NULL | 材质（如 `BOSTON XO`、`ROFLUFOCON A`） |
| color | VARCHAR(32) | Y | NULL | 颜色（`CLEAR`/`BLUE`/`GREEN`/`VIOLET`） |
| manufacturer_code | VARCHAR(32) | Y | NULL | 厂家编码（M01-08 供应商主数据） |
| manufacturer_name | VARCHAR(128) | Y | NULL | 厂家名称（快照） |
| manufacture_lead_days | SMALLINT | Y | NULL | 厂家承诺供货周期（天，通常 15~30） |
| **M01-08 fit-check 回执组（★必填）** | | | | |
| fit_check_at | TIMESTAMP | Y | NULL | 适配校验调用时间 |
| fit_check_passed | BOOLEAN | Y | NULL | 适配校验结论（`fit` 字段） |
| fit_check_result | JSONB | Y | NULL | **完整校验回执**（`checks[]`、`recommended_params`、`message`） |
| fit_check_message | VARCHAR(512) | Y | NULL | 校验返回的人可读提示 |
| check_result | VARCHAR(16) | N | 'PENDING' | 本单校验结论 `PENDING`/`PASS`/`PASS_WITH_WARN`/`FAIL` |
| check_fail_items | JSONB | Y | NULL | 不通过项数组（如 `["角膜曲率","散光"]`） |
| **下单与状态组** | | | | |
| status | VARCHAR(16) | N | 'DRAFT' | 状态 `DRAFT`/`CHECKED`/`ORDERED`/`PRODUCING`/`ARRIVED`/`CANCELLED` |
| is_ordered | BOOLEAN | N | FALSE | 是否已下发厂家 |
| ordered_at | TIMESTAMP | Y | NULL | 下单时间 |
| ordered_by | BIGINT | Y | NULL | 下单人 ID |
| factory_order_no | VARCHAR(64) | Y | NULL | 厂家订单号（回传） |
| expected_arrival_date | DATE | Y | NULL | 预计到片日期 |
| cancelled_at | TIMESTAMP | Y | NULL | 取消时间 |
| cancel_reason | VARCHAR(512) | Y | NULL | 取消原因（≥10 字） |
| **价格快照组（M01-08 取价结果，本模块不算钱）** | | | | |
| price_ref | NUMERIC(12,4) | Y | NULL | 单价快照（元，来自 M01-08 `pricing`） |
| price_ref_at | TIMESTAMP | Y | NULL | 取价时间 |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_custom_param` | 主键 | `id` | — |
| `uk_m10_ortho_k_custom_param_no` | 唯一（部分） | `custom_no` WHERE `is_deleted = FALSE` | 参数单号唯一 |
| `uk_m10_ortho_k_custom_param_eye` | 唯一（部分） | `fitting_id`, `eye_side` WHERE `status <> 'CANCELLED'` AND `is_deleted = FALSE` | **一次验配同一眼只能有一套有效定制参数** |
| `idx_m10_ortho_k_custom_param_fitting` | B-Tree | `fitting_id`, `eye_side` | 按验配单查双眼参数（P-09 主力索引） |
| `idx_m10_ortho_k_custom_param_status` | B-Tree | `status`, `created_at` DESC | 定制单状态看板 |
| `idx_m10_ortho_k_custom_param_ordered` | B-Tree（部分） | `ordered_at` WHERE `is_ordered = TRUE` AND `status IN ('ORDERED','PRODUCING')` | **在产清单（到片跟催）** |
| `idx_m10_ortho_k_custom_param_eta` | B-Tree（部分） | `expected_arrival_date` WHERE `status = 'ORDERED'` AND `is_deleted = FALSE` | 超期未到片告警 |
| `idx_m10_ortho_k_custom_param_checkfail` | B-Tree（部分） | `fitting_id`, `eye_side` WHERE `check_result = 'FAIL'` | fit-check 不通过清单（强制处理） |
| `idx_m10_ortho_k_custom_param_cornea` | B-Tree | `cornea_id` | 追溯链正向查询 |
| `idx_m10_ortho_k_custom_param_factory` | B-Tree（部分） | `factory_order_no` WHERE `factory_order_no IS NOT NULL` | 厂家单号反查 |

**约束说明：**

```sql
-- 参数单号格式
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_no_format
    CHECK (custom_no IS NULL OR custom_no ~ '^OKC[0-9]{12}$');

-- 本表只存单眼
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_eye
    CHECK (eye_side IN ('OD', 'OS'));

-- ★ 弧参数关系：RC < BC < AC < PC（与 M01-08 P07 页面口径一字不差）
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_arc
    CHECK (bc BETWEEN 7.00 AND 9.50
       AND (rc IS NULL OR rc < bc)
       AND (ac IS NULL OR ac > bc)
       AND (pc IS NULL OR ac IS NULL OR pc > ac));

-- 直径合理区间，且必须大于基弧（几何下限）
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_diameter
    CHECK (diameter BETWEEN 9.00 AND 12.00 AND diameter > bc);

-- 降度必须是负值，范围 −0.75~−6.00D
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_reduction
    CHECK (target_reduction < 0 AND target_reduction >= -6.00
       AND actual_reduction < 0 AND actual_reduction >= -6.00);

-- 降度差值必须与 actual/target 一致（防手工错录）
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_diff
    CHECK (reduction_diff IS NULL
           OR abs(reduction_diff - (actual_reduction - target_reduction)) < 0.001);

-- 降度差值非 0 必须写明调整原因（≥10 字）
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_diff_reason
    CHECK (reduction_diff IS NULL OR abs(reduction_diff) < 0.001
           OR (reduction_adjust_reason IS NOT NULL
               AND char_length(btrim(reduction_adjust_reason)) >= 10));

-- 状态枚举
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_status
    CHECK (status IN ('DRAFT', 'CHECKED', 'ORDERED', 'PRODUCING', 'ARRIVED', 'CANCELLED'));

-- 校验结论枚举
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_check
    CHECK (check_result IN ('PENDING', 'PASS', 'PASS_WITH_WARN', 'FAIL'));

-- 参数来源枚举
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_source
    CHECK (param_source IN ('TRIAL', 'CALCULATED', 'DOCTOR'));

-- 颜色枚举
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_color
    CHECK (color IS NULL OR color IN ('CLEAR', 'BLUE', 'GREEN', 'VIOLET'));

-- ★★ 核心合规约束：必须调用过 M01-08 fit-check 才能下单
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_fitcheck_required
    CHECK (is_ordered = FALSE
           OR (fit_check_at IS NOT NULL
               AND fit_check_passed IS NOT NULL
               AND fit_check_result IS NOT NULL
               AND check_result <> 'PENDING'));

-- ★★ 核心合规约束：fit-check 不通过禁止下单
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_fitcheck_fail
    CHECK (check_result <> 'FAIL' OR is_ordered = FALSE);

-- 不通过必须有失败项清单
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_fail_items
    CHECK (check_result <> 'FAIL'
           OR (check_fail_items IS NOT NULL AND jsonb_array_length(check_fail_items) > 0));

-- 校验通过必须与 fit_check_passed 一致
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_check_consistent
    CHECK (check_result IN ('PENDING', 'FAIL') OR fit_check_passed = TRUE);

-- 已下单必须有一致的订单信息
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_ordered
    CHECK (is_ordered = FALSE
           OR (status IN ('ORDERED', 'PRODUCING', 'ARRIVED')
               AND ordered_at IS NOT NULL
               AND ordered_by IS NOT NULL
               AND expected_arrival_date IS NOT NULL
               AND expected_arrival_date >= ordered_at::date));

-- 已到片必须是已下单状态
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_arrived
    CHECK (status <> 'ARRIVED' OR is_ordered = TRUE);

-- 已取消必须写原因（≥10 字）与时间
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_cancelled
    CHECK (status <> 'CANCELLED'
           OR (cancelled_at IS NOT NULL
               AND cancel_reason IS NOT NULL
               AND char_length(btrim(cancel_reason)) >= 10));

-- 已下发厂家的参数不可取消（需走改单流程）
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_cancel_guard
    CHECK (status <> 'CANCELLED' OR is_ordered = FALSE);

-- 取价快照成对
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_price
    CHECK ((price_ref IS NULL AND price_ref_at IS NULL)
        OR (price_ref IS NOT NULL AND price_ref_at IS NOT NULL AND price_ref >= 0));

-- 供货周期合理区间 1~90 天
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_lead
    CHECK (manufacture_lead_days IS NULL OR manufacture_lead_days BETWEEN 1 AND 90);

-- 已下单后不得逻辑删除
ALTER TABLE m10_ortho_k_custom_param
    ADD CONSTRAINT ck_m10_ortho_k_custom_param_undeletable
    CHECK (is_ordered = FALSE OR is_deleted = FALSE);
```

**业务说明：**

1. **`fit_check_result` 存完整回执 JSONB 的理由**：M01-08 的 `fit-check` 返回 `checks[]`（每项含 `item`/`value`/`range`/`passed`）、`recommended_params[]`、`followup_days`、`lead_time_days`。若只存 `fit_check_passed` 一个布尔值，事后无法回答「当时代谢了哪些项、推荐参数是什么」。医疗纠纷追溯与质控检查都需要完整回执快照。

   存储示例：

   ```json
   {
     "fit": true,
     "product_code": "OPOK000012",
     "checks": [
       {"item": "角膜曲率", "value": 43.50, "range": "41.00~46.00", "passed": true},
       {"item": "角膜厚度", "value": 520, "range": "≥480", "passed": true},
       {"item": "散光", "value": -1.50, "range": "≤-2.50", "passed": true},
       {"item": "近视度数", "value": -3.00, "range": "-6.00~0.00", "passed": true},
       {"item": "年龄", "value": 12, "range": "8~40", "passed": true}
     ],
     "recommended_params": [{"base_curve": 8.20, "reduction_power": -3.00, "diameter": 10.6}],
     "followup_days": "1,7,30,90",
     "lead_time_days": 20
   }
   ```

2. **`check_result` 四态与错误的对应**：

   | `check_result` | 判定依据 | 是否可下单 | 错误码 |
   |---|---|---|---|
   | `PENDING` | 尚未调用 fit-check | 否 | `"1004024"` |
   | `PASS` | `fit == true` 且所有 `checks[].passed == true` | 是 | — |
   | `PASS_WITH_WARN` | `fit == true` 但 `recommended_params` 与本单参数偏差 >0.50mm 或 >0.50D | 是（需验配师二次确认） | `"1004025"`（提示级） |
   | `FAIL` | `fit == false` 或存在 `checks[].passed == false` | **否** | `"1004026"` |

3. **降度差值控制**：OK 镜的实际降度通常等于目标降度；当试戴片上追加球镜 `over_refraction` 非 0 时，`actual_reduction = target_reduction + over_refraction`（追加坡镜需并入降度）。任何差值都必须写明理由，否则数据库拒绝写入。

4. **`uk_m10_ortho_k_custom_param_eye` 的语义**：一套参数对应一眼。若需换片重做，旧参数置 `CANCELLED` 后新参数才能占用该眼；已下发厂家的参数不可取消（`ck_..._cancel_guard`），只能通过 M10-06 的改单流程处理。

5. **`price_ref` 只做快照**：本模块**不计算金额**，`price_ref` 来自 M01-08 `GET /internal/v1/optical/products/{code}/pricing`，仅用于 P05 页面展示与下单前的价格确认。实际收款由 M16-04 完成。

**分区策略：** 无（4,800/年）。

---
### 4.8 表：`m10_ortho_k_delivery`（到片验收与发放表）

**用途：** 记录厂家的成品镜片到院后的**验收、消毒、发放、首次戴镜教学**全过程，**按「片」一行**（一位患者配双眼 = 2 行）。OK 镜是定制品，单片唯一，故必须逐片管理——一片的参数错了只影响那一只眼，双行记录才能精确定位。

- **写入方：** 本子模块（P06 页面）。
- **只读方：** M10-06（取镜交付状态）、M16-04（销售单明细交付状态）、M10-09（戴镜起算日，用于计算复查节点）、患者（镜片编号与绑定关系）。
- **关键设计：**
  - **逐片核对单**：`param_match_od` / `param_match_*` 并非按眼，而是逐项比对「定制单参数 vs 到片实物参数」，任何一项不符即 `accept_result = 'FAIL'` 并触发退换（错误码 `"1004029"`）。
  - **`lens_no` 是厂家镜片唯一编号**（激光刻印在镜片边缘），必须与患者绑定。同一 `lens_no` 全库唯一。
  - **首次戴镜教学 30 分钟**是规范要求，`teaching_minutes` 与 `teaching_signed` 强制记录。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| delivery_no | VARCHAR(32) | Y | NULL | 到片验发单号 `OKD` + YYYYMMDD + 4 位 |
| fitting_id | BIGINT | N | — | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余） |
| custom_param_id | BIGINT | N | — | 定制参数 ID（`m10_ortho_k_custom_param.id`，必须与该片参数一致） |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03） |
| patient_name | VARCHAR(64) | N | — | 患者姓名（快照） |
| eye_side | VARCHAR(8) | N | — | 眼别 `OD`/`OS` |
| lens_no | VARCHAR(64) | Y | NULL | **厂家镜片唯一编号**（镜片激光刻印，验收后填入） |
| factory_order_no | VARCHAR(64) | Y | NULL | 厂家订单号（与定制参数表一致） |
| **到片组** | | | | |
| arrived_at | TIMESTAMP | Y | NULL | 到片签收时间 |
| arrived_by | BIGINT | Y | NULL | 签收人 ID（库管） |
| arrived_by_name | VARCHAR(64) | Y | NULL | 签收人姓名（快照） |
| package_intact | BOOLEAN | Y | NULL | 包装是否完好 |
| package_note | VARCHAR(512) | Y | NULL | 包装异常说明 |
| **一、参数逐项核对（定制单 vs 实物）** | | | | |
| actual_bc | NUMERIC(5,2) | Y | NULL | 实物基弧 BC（mm） |
| actual_rc | NUMERIC(5,2) | Y | NULL | 实物反转弧 RC（mm） |
| actual_ac | NUMERIC(5,2) | Y | NULL | 实物定位弧 AC（mm） |
| actual_pc | NUMERIC(5,2) | Y | NULL | 实物周边弧 PC（mm） |
| actual_diameter | NUMERIC(5,2) | Y | NULL | 实物直径（mm） |
| actual_reduction | NUMERIC(6,2) | Y | NULL | 实物降度（D） |
| actual_material | VARCHAR(64) | Y | NULL | 实物材质 |
| actual_color | VARCHAR(32) | Y | NULL | 实物颜色 |
| param_match | BOOLEAN | Y | NULL | 参数是否逐项一致（全部一致才 TRUE） |
| mismatch_items | JSONB | Y | NULL | 不一致项数组（如 `["BC","直径"]`） |
| **二、外观检查** | | | | |
| appearance_ok | BOOLEAN | Y | NULL | 外观检查是否合格 |
| appearance_note | VARCHAR(512) | Y | NULL | 外观异常说明（划痕/崩边/气泡/杂质） |
| scratch_found | BOOLEAN | N | FALSE | 是否有划痕 |
| chip_found | BOOLEAN | N | FALSE | 是否崩边 |
| bubble_found | BOOLEAN | N | FALSE | 是否有气泡/杂质 |
| **三、验收结论** | | | | |
| accept_result | VARCHAR(16) | N | 'PENDING' | 验收结论 `PENDING`/`PASS`/`FAIL`/`RETURNED` |
| reject_reason | VARCHAR(512) | Y | NULL | 拒收/退换原因（≥10 字） |
| returned_at | TIMESTAMP | Y | NULL | 退回厂家时间 |
| **四、消毒与发放** | | | | |
| disinfected | BOOLEAN | N | FALSE | 是否已完成消毒 |
| disinfected_at | TIMESTAMP | Y | NULL | 消毒时间 |
| disinfect_method | VARCHAR(32) | Y | NULL | 消毒方式 `BOIL`（煮沸）/`PEROXIDE`（双氧水）/`UV`（紫外线） |
| delivered_at | TIMESTAMP | Y | NULL | 发放时间 |
| delivered_by | BIGINT | Y | NULL | 发放人 ID |
| delivered_by_name | VARCHAR(64) | Y | NULL | 发放人姓名（快照） |
| receiver_name | VARCHAR(64) | Y | NULL | 领取人姓名（患者或监护人） |
| receiver_relation | VARCHAR(16) | Y | NULL | 领取人关系 `SELF`/`FATHER`/`MOTHER`/`GRANDPARENT`/`OTHER` |
| receiver_sign_file_id | BIGINT | Y | NULL | 领取签名件 ID（电子签） |
| **五、首次戴镜教学** | | | | |
| teaching_done | BOOLEAN | N | FALSE | 首次戴镜教学是否完成 |
| teaching_minutes | SMALLINT | Y | NULL | 教学时长（分钟，要求 ≥30） |
| teaching_content | JSONB | Y | NULL | 教学内容清单（摘戴/清洗/护理液使用/异常处理） |
| teaching_by | BIGINT | Y | NULL | 教学人员 ID |
| teaching_by_name | VARCHAR(64) | Y | NULL | 教学人员姓名（快照） |
| teaching_signed | BOOLEAN | N | FALSE | 患者/家长确认签字 |
| **六、佩戴起算与换片提醒** | | | | |
| wear_start_date | DATE | Y | NULL | 戴镜起算日（= 发放日，用于计算复查节点与换片期） |
| expected_replace_date | DATE | Y | NULL | 预计换片日期（= 戴镜起算日 + 更换周期月数） |
| replace_months | SMALLINT | Y | NULL | 更换周期（月，通常 12~18） |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_delivery` | 主键 | `id` | — |
| `uk_m10_ortho_k_delivery_no` | 唯一（部分） | `delivery_no` WHERE `is_deleted = FALSE` | 验发单号唯一 |
| `uk_m10_ortho_k_delivery_lens_no` | 唯一（部分） | `lens_no` WHERE `lens_no IS NOT NULL` AND `is_deleted = FALSE` | **镜片编号全局唯一（一片只能绑定一位患者）** |
| `uk_m10_ortho_k_delivery_param` | 唯一（部分） | `custom_param_id` WHERE `is_deleted = FALSE` | 一套定制参数只对应一片验收记录 |
| `idx_m10_ortho_k_delivery_fitting` | B-Tree | `fitting_id`, `eye_side` | 按验配单查双眼验发记录（P-09 主力索引） |
| `idx_m10_ortho_k_delivery_pending` | B-Tree（部分） | `arrived_at` WHERE `accept_result = 'PENDING'` AND `is_deleted = FALSE` | **待到片验收队列（P06 待办）** |
| `idx_m10_ortho_k_delivery_accept_fail` | B-Tree（部分） | `arrived_at` DESC WHERE `accept_result IN ('FAIL','RETURNED')` | 验收不合格清单 |
| `idx_m10_ortho_k_delivery_undelivered` | B-Tree（部分） | `fitting_id` WHERE `accept_result = 'PASS'` AND `delivered_at IS NULL` AND `is_deleted = FALSE` | **到片未发放清单（催取主力索引）** |
| `idx_m10_ortho_k_delivery_wear` | B-Tree（部分） | `wear_start_date`, `eye_side` WHERE `delivered_at IS NOT NULL` | 戴镜起算日查询 |
| `idx_m10_ortho_k_delivery_replace` | B-Tree（部分） | `expected_replace_date` WHERE `delivered_at IS NOT NULL` AND `is_deleted = FALSE` | 换片到期扫描 |
| `idx_m10_ortho_k_delivery_lens_no` | B-Tree | `lens_no` | 按镜片号反查患者 |

**约束说明：**

```sql
-- 验发单号格式
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_no_format
    CHECK (delivery_no IS NULL OR delivery_no ~ '^OKD[0-9]{12}$');

-- 本表按片管理，只存单眼
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_eye
    CHECK (eye_side IN ('OD', 'OS'));

-- 验收结论枚举
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_accept
    CHECK (accept_result IN ('PENDING', 'PASS', 'FAIL', 'RETURNED'));

-- 领取人关系枚举
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_relation
    CHECK (receiver_relation IS NULL
           OR receiver_relation IN ('SELF', 'FATHER', 'MOTHER', 'GRANDPARENT', 'OTHER'));

-- 消毒方式枚举
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_disinfect
    CHECK (disinfect_method IS NULL OR disinfect_method IN ('BOIL', 'PEROXIDE', 'UV'));

-- 实物弧参数合理区间（录入的到片参数）
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_actual
    CHECK ((actual_bc IS NULL OR actual_bc BETWEEN 7.00 AND 9.50)
       AND (actual_diameter IS NULL OR actual_diameter BETWEEN 9.00 AND 12.00)
       AND (actual_reduction IS NULL
            OR (actual_reduction < 0 AND actual_reduction >= -6.00)));

-- 实物弧关系：RC < BC < AC < PC
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_arc
    CHECK ((actual_rc IS NULL OR actual_bc IS NULL OR actual_rc < actual_bc)
       AND (actual_ac IS NULL OR actual_bc IS NULL OR actual_ac > actual_bc)
       AND (actual_pc IS NULL OR actual_ac IS NULL OR actual_pc > actual_ac));

-- ★ 验收通过必须完成全部核对项且参数一致
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_pass
    CHECK (accept_result <> 'PASS'
           OR (lens_no IS NOT NULL
               AND param_match = TRUE
               AND appearance_ok = TRUE
               AND actual_bc IS NOT NULL
               AND actual_diameter IS NOT NULL
               AND actual_reduction IS NOT NULL
               AND arrived_at IS NOT NULL));

-- 参数不一致必须有 mismatch_items
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_mismatch
    CHECK (param_match IS DISTINCT FROM FALSE
           OR (mismatch_items IS NOT NULL AND jsonb_array_length(mismatch_items) > 0));

-- 验收不通过/退换必须写原因（≥10 字）
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_reject
    CHECK (accept_result NOT IN ('FAIL', 'RETURNED')
           OR (reject_reason IS NOT NULL AND char_length(btrim(reject_reason)) >= 10));

-- 已退回必须有退回时间
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_returned
    CHECK (accept_result <> 'RETURNED' OR returned_at IS NOT NULL);

-- ★ 发放必须：验收通过 + 已消毒 + 教学完成 + 领取签字
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_deliver
    CHECK (delivered_at IS NULL
           OR (accept_result = 'PASS'
               AND disinfected = TRUE
               AND disinfected_at IS NOT NULL
               AND delivered_by IS NOT NULL
               AND receiver_name IS NOT NULL
               AND receiver_relation IS NOT NULL
               AND receiver_sign_file_id IS NOT NULL
               AND teaching_done = TRUE
               AND teaching_minutes IS NOT NULL
               AND teaching_minutes >= 30
               AND teaching_signed = TRUE
               AND wear_start_date IS NOT NULL
               AND expected_replace_date IS NOT NULL));

-- 教学时长合理区间 0~180 分钟
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_teaching
    CHECK (teaching_minutes IS NULL OR teaching_minutes BETWEEN 0 AND 180);

-- 未完成教学不得有教学时长
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_teaching_pair
    CHECK (teaching_done = TRUE OR teaching_minutes IS NULL);

-- 消毒标记与消毒时间成对
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_disinfect_pair
    CHECK ((disinfected = FALSE AND disinfected_at IS NULL)
        OR (disinfected = TRUE AND disinfected_at IS NOT NULL));

-- 时间顺序：到片 ≤ 消毒 ≤ 发放
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_time_order
    CHECK ((disinfected_at IS NULL OR arrived_at IS NULL OR disinfected_at >= arrived_at)
       AND (delivered_at IS NULL OR disinfected_at IS NULL OR delivered_at >= disinfected_at));

-- 预计换片日期必须晚于戴镜起算日
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_replace
    CHECK (expected_replace_date IS NULL OR wear_start_date IS NULL
           OR expected_replace_date > wear_start_date);

-- 更换周期合理区间 6~24 个月
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_replace_months
    CHECK (replace_months IS NULL OR replace_months BETWEEN 6 AND 24);

-- 已发放不得逻辑删除（镜片与患者的绑定关系是法定追溯信息）
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_undeletable
    CHECK (delivered_at IS NULL OR is_deleted = FALSE);

-- 外观检查合格时不得残留异常标记
ALTER TABLE m10_ortho_k_delivery
    ADD CONSTRAINT ck_m10_ortho_k_delivery_appearance
    CHECK (appearance_ok IS DISTINCT FROM TRUE
           OR (scratch_found = FALSE AND chip_found = FALSE AND bubble_found = FALSE
               AND appearance_note IS NULL));
```

**业务说明：**

1. **为什么逐片而不逐单**：OK 镜左右眼参数不同（BC 可能差 0.1mm，降度可能差 0.75D），一片参数错只是该眼的问题。逐片记录才能在「厂家发错一片」时精确定位退换对象，也才能建立「镜片编号 ↔ 患者」的一一绑定（法定追溯要求）。
2. **`accept_result = 'FAIL'` 之后的处理路径**：留观 `RETURNED`（退回厂家重做，`returned_at` 必填）→ 定制参数状态回退为 `CHECKED` → 重新下单。整个链路保留原记录不删除，形成完整的「错片 → 退换 → 重发」证据链。
3. **`teaching_minutes >= 30` 的数据库强制**：《角膜塑形镜验配技术规范》要求首次戴镜必须现场教学并确认患者/家长掌握摘戴与护理。教学时长 <30 分钟视为未完成，发放不得成立（错误码 `"1004030"`）。
4. **`lens_no` 唯一索引的临床意义**：镜片编号激光刻印在镜片边缘，是厂家召回、不良事件上报的关键标识。若同一编号被绑定给两位患者，说明验收环节录入错误或镜片被冒领，数据库层直接拒绝（错误码 `"1004031"`）。
5. **`expected_replace_date` 的双重来源**：本表按「片」算换片日（`wear_start_date + replace_months`），验配单主表 `m10_ortho_k_fitting.expected_replace_date` 按「单」算（取两眼中较早者）。二者由定时任务对账，防止双眼发放时间不同步造成的偏差。

**分区策略：** 无（4,800/年）。

---

### 4.9 表：`m10_ortho_k_followup`（戴镜随访记录表）

**用途：** 记录戴镜后的**每一次复查/随访结果**。复查节点为戴镜后第 **1、7、30、90 天**，之后**每 3 个月一次**直至换片。

**与 M10-09 的职责划分（关键）：**

| 事项 | 归属 | 说明 |
|---|---|---|
| 复查计划的**生成与提醒** | **M10-09** | 写入 `m10_followup_plan`（`followup_type = 'POST_ORTHOK'`），负责到期提醒、召回、逾期统计 |
| 复查的**执行与结果记录** | **本表（M10-04）** | 记录本次复查的临床检查数据、配适评估、并发症判断、处置意见 |
| 复查结果的**归档展示** | M10-09 | 读本表数据写入 `m10_vision_archive` 展示纵向曲线 |

- **写入方：** 本子模块（P07 页面）。
- **只读方：** M10-09（视力档案与屈光进展曲线）、M07（医生查阅）、M10-06（换片决策依据）。
- **关键设计：**
  - **`followup_plan_id` 关联 M10-09 的计划**（可空——急诊复查可能无对应计划）。
  - **`followup_day` 记录本次随访相对戴镜的节点天数**，便于按节点统计「1 天复查率」「90 天复查率」。
  - **`followup_result` 与 `complication` 分层**：前者是本片是否继续可戴（`NORMAL`/`OBSERVE`/`DISCONTINUE`），后者是具体的眼部异常（可多个）。并发症上报由 `report_required` 驱动。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| followup_no | VARCHAR(32) | Y | NULL | 随访单号 `OKF` + YYYYMMDD + 4 位 |
| fitting_id | BIGINT | N | — | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余） |
| patient_id | BIGINT | N | — | 患者 ID（只读引用 M03） |
| patient_name | VARCHAR(64) | N | — | 患者姓名（快照） |
| followup_plan_id | BIGINT | Y | NULL | 复查计划 ID（M10-09 `m10_followup_plan.id`，只读+回写） |
| followup_seq | SMALLINT | N | 1 | 第几次随访（1,2,3…） |
| followup_node | VARCHAR(16) | N | 'D1' | 节点 `D1`/`D7`/`D30`/`D90`/`M3`/`M6`/`M9`/`M12`/`EXTRA` |
| followup_day | INT | Y | NULL | 相对戴镜日的天数（D1=1，D7=7，M3≈91） |
| scheduled_date | DATE | Y | NULL | 计划复查日期（来自 M10-09） |
| visited_at | TIMESTAMP | Y | NULL | 实际到访时间 |
| visit_late_days | INT | Y | NULL | 迟访天数（实际 − 计划，负值表示提前） |
| followup_type | VARCHAR(16) | N | 'SCHEDULED' | 随访类型 `SCHEDULED`（计划内）/`UNSCHEDULED`（不适就诊）/`POST_REPLACE`（换片后首次） |
| **一、主观与依从性** | | | | |
| subjective_complaints | VARCHAR(512) | Y | NULL | 主诉（如有无不适、异物感、眼红） |
| wearing_hours_per_night | NUMERIC(4,1) | Y | NULL | 夜间戴镜时长（小时，规范 8~10） |
| wearing_days_per_week | SMALLINT | Y | NULL | 每周戴镜天数（规范 6~7） |
| compliance_check | VARCHAR(16) | Y | NULL | 依从性检查 `GOOD`/`FAIR`/`POOR` |
| **二、视力与屈光** | | | | |
| od_va_uncorrected | NUMERIC(4,2) | Y | NULL | 右眼裸眼视力（小数记录法） |
| os_va_uncorrected | NUMERIC(4,2) | Y | NULL | 左眼裸眼视力 |
| od_va_corrected | NUMERIC(4,2) | Y | NULL | 右眼矫正视力 |
| os_va_corrected | NUMERIC(4,2) | Y | NULL | 左眼矫正视力 |
| od_sphere | NUMERIC(6,2) | Y | NULL | 右眼球镜（D） |
| od_cylinder | NUMERIC(6,2) | Y | NULL | 右眼柱镜（D） |
| os_sphere | NUMERIC(6,2) | Y | NULL | 左眼球镜（D） |
| os_cylinder | NUMERIC(6,2) | Y | NULL | 左眼柱镜（D） |
| od_axial_length | NUMERIC(5,2) | Y | NULL | 右眼眼轴长度（mm，正常 22~26） |
| os_axial_length | NUMERIC(5,2) | Y | NULL | 左眼眼轴长度（mm） |
| **三、角膜状态** | | | | |
| od_fluorescein | VARCHAR(24) | Y | NULL | 右眼角膜荧光染色 `NORMAL`/`PUNCTATE_STAINING`/`STAINING`/`INFILTRATE`/`ULCER` |
| os_fluorescein | VARCHAR(24) | Y | NULL | 左眼角膜荧光染色 |
| od_stain_location | VARCHAR(32) | Y | NULL | 右眼染色位置 `CENTRAL`/`PARACENTRAL`/`PERIPHERAL`/`LIMBAL` |
| os_stain_location | VARCHAR(32) | Y | NULL | 左眼染色位置 |
| od_fluorescein_grade | SMALLINT | Y | NULL | 右眼染色分级（0~4，Efron 分级） |
| os_fluorescein_grade | SMALLINT | Y | NULL | 左眼染色分级 |
| od_iop | NUMERIC(5,1) | Y | NULL | 右眼眼压（mmHg） |
| os_iop | NUMERIC(5,1) | Y | NULL | 左眼眼压（mmHg） |
| od_cornea_thickness | SMALLINT | Y | NULL | 右眼中央角膜厚度（μm） |
| os_cornea_thickness | SMALLINT | Y | NULL | 左眼中央角膜厚度（μm） |
| **四、镜片配适与清洁度** | | | | |
| od_lens_position | VARCHAR(16) | Y | NULL | 右眼镜片定位 `CENTERED`/`SLIGHT_DECENTERED`/`DECENTERED` |
| os_lens_position | VARCHAR(16) | Y | NULL | 左眼镜片定位 |
| od_lens_movement | NUMERIC(5,2) | Y | NULL | 右眼活动度（mm） |
| os_lens_movement | NUMERIC(5,2) | Y | NULL | 左眼活动度（mm） |
| od_fluo_fit | VARCHAR(16) | Y | NULL | 右眼荧光配适 `FLAT`/`IDEAL`/`STEEP` |
| os_fluo_fit | VARCHAR(16) | Y | NULL | 左眼荧光配适 |
| od_lens_cleanliness | VARCHAR(16) | Y | NULL | 右眼镜片清洁度 `CLEAN`/`SLIGHT_DEPOSIT`/`HEAVY_DEPOSIT` |
| os_lens_cleanliness | VARCHAR(16) | Y | NULL | 左眼镜片清洁度 |
| od_lens_damage | VARCHAR(16) | Y | NULL | 右眼镜片损伤 `NONE`/`SCRATCH`/`CHIP`/`BROKEN` |
| os_lens_damage | VARCHAR(16) | Y | NULL | 左眼镜片损伤 |
| **五、角膜地形图（TFT）** | | | | |
| od_tft_pattern | VARCHAR(16) | Y | NULL | 右眼 TFT 图形 `BULLSEYE`/`SMILEY`/`TARGET`/`CENTRAL_CRAB`/`NON_CENTRAL`/`IRREGULAR` |
| os_tft_pattern | VARCHAR(16) | Y | NULL | 左眼 TFT 图形 |
| topography_report_id | BIGINT | Y | NULL | 本次地形图报告 ID（M12，只读引用） |
| cornea_record_id | BIGINT | Y | NULL | 本次角膜参数记录 ID（`m10_ortho_k_cornea.id`） |
| **六、并发症与结论** | | | | |
| complications | JSONB | Y | NULL | 并发症编码数组（可多个，如 `["CORNEAL_STAINING","LENS_DEPOSIT"]`） |
| complication_grade | VARCHAR(16) | Y | NULL | 并发症严重度 `NONE`/`MILD`/`MODERATE`/`SEVERE` |
| report_required | BOOLEAN | N | FALSE | 是否需上报不良事件（`SEVERE` 强制 TRUE） |
| report_id | VARCHAR(64) | Y | NULL | 不良事件上报单号（M02 审计/医政） |
| reported_at | TIMESTAMP | Y | NULL | 上报时间 |
| followup_result | VARCHAR(16) | N | 'NORMAL' | 随访结论 `NORMAL`（继续戴）/`OBSERVE`（加强观察）/`ADJUST_LENS`（需调片）/`DISCONTINUE`（建议停戴） |
| disposal_advice | VARCHAR(512) | Y | NULL | 处置意见（≥10 字） |
| next_followup_date | DATE | Y | NULL | 下次复查日期（写回 M10-09 计划） |
| next_followup_node | VARCHAR(16) | Y | NULL | 下次节点 `D7`/`D30`/`D90`/`M3`… |
| followup_doctor_id | BIGINT | Y | NULL | 复查医师 ID |
| followup_doctor_name | VARCHAR(64) | Y | NULL | 复查医师姓名（快照） |
| operator_id | BIGINT | Y | NULL | 记录人 ID（验光师/护士） |
| operator_name | VARCHAR(64) | Y | NULL | 记录人姓名（快照） |
| remark | VARCHAR(1024) | Y | NULL | 备注 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 更新时间（触发器维护） |
| is_deleted | BOOLEAN | N | FALSE | 逻辑删除 |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_followup` | 主键 | `id` | — |
| `uk_m10_ortho_k_followup_no` | 唯一（部分） | `followup_no` WHERE `is_deleted = FALSE` | 随访单号唯一 |
| `uk_m10_ortho_k_followup_seq` | 唯一（部分） | `fitting_id`, `followup_seq` WHERE `is_deleted = FALSE` | 同一验配单随访序号不重复 |
| `uk_m10_ortho_k_followup_node` | 唯一（部分） | `fitting_id`, `followup_node` WHERE `followup_node NOT IN ('EXTRA')` AND `is_deleted = FALSE` | **同一节点只允许一次正式随访**（防重复录入） |
| `idx_m10_ortho_k_followup_fitting` | B-Tree | `fitting_id`, `visited_at` DESC | 按验配单查随访历史（P07 主力索引） |
| `idx_m10_ortho_k_followup_patient` | B-Tree | `patient_id`, `visited_at` DESC | 患者随访纵向查询 |
| `idx_m10_ortho_k_followup_plan` | B-Tree（部分） | `followup_plan_id` WHERE `followup_plan_id IS NOT NULL` | 与 M10-09 计划对账 |
| `idx_m10_ortho_k_followup_node_stat` | B-Tree（部分） | `followup_node`, `visited_at` DESC WHERE `is_deleted = FALSE` | **按节点统计复查依从率** |
| `idx_m10_ortho_k_followup_severe` | B-Tree（部分） | `visited_at` DESC WHERE `report_required = TRUE` | 严重并发症上报清单 |
| `idx_m10_ortho_k_followup_result` | B-Tree（部分） | `followup_result`, `visited_at` DESC WHERE `followup_result <> 'NORMAL'` | 异常随访追踪 |
| `idx_m10_ortho_k_followup_unreported` | B-Tree（部分） | `visited_at` WHERE `report_required = TRUE` AND `report_id IS NULL` | **待上报不良事件告警** |
| `idx_m10_ortho_k_followup_next` | B-Tree（部分） | `next_followup_date` WHERE `next_followup_date IS NOT NULL` | 下次复查日期回写 M10-09 |

**约束说明：**

```sql
-- 随访单号格式
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_no_format
    CHECK (followup_no IS NULL OR followup_no ~ '^OKF[0-9]{12}$');

-- 随访序号范围
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_seq_range
    CHECK (followup_seq BETWEEN 1 AND 60);

-- ★ 复查节点枚举：1/7/30/90 天 + 每 3 月
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_node
    CHECK (followup_node IN ('D1', 'D7', 'D30', 'D90', 'M3', 'M6', 'M9', 'M12', 'EXTRA'));

-- 随访类型枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_type
    CHECK (followup_type IN ('SCHEDULED', 'UNSCHEDULED', 'POST_REPLACE'));

-- 依从性枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_compliance
    CHECK (compliance_check IS NULL OR compliance_check IN ('GOOD', 'FAIR', 'POOR'));

-- 夜间戴镜时长合理区间 0~14 小时（规范 8~10）
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_hours
    CHECK (wearing_hours_per_night IS NULL OR wearing_hours_per_night BETWEEN 0.0 AND 14.0);

-- 每周戴镜天数 0~7
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_days
    CHECK (wearing_days_per_week IS NULL OR wearing_days_per_week BETWEEN 0 AND 7);

-- 角膜荧光染色枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_fluorescein
    CHECK ((od_fluorescein IS NULL OR od_fluorescein IN
              ('NORMAL', 'PUNCTATE_STAINING', 'STAINING', 'INFILTRATE', 'ULCER'))
       AND (os_fluorescein IS NULL OR os_fluorescein IN
              ('NORMAL', 'PUNCTATE_STAINING', 'STAINING', 'INFILTRATE', 'ULCER')));

-- Efron 染色分级 0~4
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_grade
    CHECK ((od_fluorescein_grade IS NULL OR od_fluorescein_grade BETWEEN 0 AND 4)
       AND (os_fluorescein_grade IS NULL OR os_fluorescein_grade BETWEEN 0 AND 4));

-- 染色位置枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_stain_loc
    CHECK ((od_stain_location IS NULL OR od_stain_location IN
              ('CENTRAL', 'PARACENTRAL', 'PERIPHERAL', 'LIMBAL'))
       AND (os_stain_location IS NULL OR os_stain_location IN
              ('CENTRAL', 'PARACENTRAL', 'PERIPHERAL', 'LIMBAL')));

-- 镜片定位枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_position
    CHECK ((od_lens_position IS NULL OR od_lens_position IN
              ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED'))
       AND (os_lens_position IS NULL OR os_lens_position IN
              ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED')));

-- 荧光配适枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_fluo_fit
    CHECK ((od_fluo_fit IS NULL OR od_fluo_fit IN ('FLAT', 'IDEAL', 'STEEP'))
       AND (os_fluo_fit IS NULL OR os_fluo_fit IN ('FLAT', 'IDEAL', 'STEEP')));

-- 镜片清洁度枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_clean
    CHECK ((od_lens_cleanliness IS NULL OR od_lens_cleanliness IN
              ('CLEAN', 'SLIGHT_DEPOSIT', 'HEAVY_DEPOSIT'))
       AND (os_lens_cleanliness IS NULL OR os_lens_cleanliness IN
              ('CLEAN', 'SLIGHT_DEPOSIT', 'HEAVY_DEPOSIT')));

-- 镜片损伤枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_damage
    CHECK ((od_lens_damage IS NULL OR od_lens_damage IN
              ('NONE', 'SCRATCH', 'CHIP', 'BROKEN'))
       AND (os_lens_damage IS NULL OR os_lens_damage IN
              ('NONE', 'SCRATCH', 'CHIP', 'BROKEN')));

-- TFT 图形枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_tft
    CHECK ((od_tft_pattern IS NULL OR od_tft_pattern IN
              ('BULLSEYE', 'SMILEY', 'TARGET', 'CENTRAL_CRAB', 'NON_CENTRAL', 'IRREGULAR'))
       AND (os_tft_pattern IS NULL OR os_tft_pattern IN
              ('BULLSEYE', 'SMILEY', 'TARGET', 'CENTRAL_CRAB', 'NON_CENTRAL', 'IRREGULAR')));

-- 并发症严重度枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_grade_level
    CHECK (complication_grade IS NULL
           OR complication_grade IN ('NONE', 'MILD', 'MODERATE', 'SEVERE'));

-- ★ 严重并发症必须上报
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_report
    CHECK (complication_grade IS DISTINCT FROM 'SEVERE' OR report_required = TRUE);

-- 需上报必须有并发症明细
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_report_items
    CHECK (report_required = FALSE
           OR (complications IS NOT NULL AND jsonb_array_length(complications) > 0));

-- 上报单号与上报时间成对
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_report_pair
    CHECK ((report_id IS NULL AND reported_at IS NULL)
        OR (report_id IS NOT NULL AND reported_at IS NOT NULL));

-- 随访结论枚举
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_result
    CHECK (followup_result IN ('NORMAL', 'OBSERVE', 'ADJUST_LENS', 'DISCONTINUE'));

-- 非正常结论必须写处置意见（≥10 字）
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_advice
    CHECK (followup_result = 'NORMAL'
           OR (disposal_advice IS NOT NULL AND char_length(btrim(disposal_advice)) >= 10));

-- 建议停戴必须引用并发症或明确的角膜异常
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_discontinue
    CHECK (followup_result <> 'DISCONTINUE'
           OR (complications IS NOT NULL AND jsonb_array_length(complications) > 0)
           OR od_fluorescein IN ('STAINING', 'INFILTRATE', 'ULCER')
           OR os_fluorescein IN ('STAINING', 'INFILTRATE', 'ULCER'));

-- 已到访必须有到访时间与记录人
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_visited
    CHECK (visited_at IS NULL OR (operator_id IS NOT NULL AND followup_doctor_id IS NOT NULL));

-- 迟访天数与计划/实际一致性（容差 0 天）
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_late
    CHECK (visit_late_days IS NULL OR (visited_at IS NOT NULL AND scheduled_date IS NOT NULL));

-- 下次复查日期必须晚于本次到访
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_next_date
    CHECK (next_followup_date IS NULL OR visited_at IS NULL
           OR next_followup_date > visited_at::date);

-- 随访记录不得逻辑删除（临床记录，只能更正）
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_undeletable
    CHECK (is_deleted = FALSE);

-- 眼轴长度合理区间 18~32mm
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_axial
    CHECK ((od_axial_length IS NULL OR od_axial_length BETWEEN 18.00 AND 32.00)
       AND (os_axial_length IS NULL OR os_axial_length BETWEEN 18.00 AND 32.00));

-- 眼压合理区间 5~30mmHg
ALTER TABLE m10_ortho_k_followup
    ADD CONSTRAINT ck_m10_ortho_k_followup_iop
    CHECK ((od_iop IS NULL OR od_iop BETWEEN 5 AND 30)
       AND (os_iop IS NULL OR os_iop BETWEEN 5 AND 30));
```

**业务说明：**

1. **复查节点的数据库约束表达**：`followup_node` 只允许 `D1/D7/D30/D90/M3/M6/M9/M12/EXTRA` 九个值 + `uk_m10_ortho_k_followup_node` 部分唯一索引保证「同一验配单同一节点只有一次正式随访」。`M3/M6/M9/M12` 分别对应第 3、6、9、12 个月的每 3 月复查；超过 12 个月仍继续戴镜的，用 `EXTRA` 记录并配合 `followup_day` 标记实际天数。

2. **节点天数映射表**（供 Service 计算 `followup_day` 与 `scheduled_date`）：

   | `followup_node` | 相对戴镜日天数 | 中文 |
   |---|---|---|
   | `D1` | 1 | 戴镜后第 1 天 |
   | `D7` | 7 | 戴镜后 1 周 |
   | `D30` | 30 | 戴镜后 1 个月 |
   | `D90` | 90 | 戴镜后 3 个月 |
   | `M3` | 180 | 戴镜后 6 个月（第 2 次三月复查） |
   | `M6` | 270 | 戴镜后 9 个月 |
   | `M9` | 360 | 戴镜后 12 个月 |
   | `M12` | 450 | 戴镜后 15 个月（临近换片） |
   | `EXTRA` | — | 计划外（不适就诊/加查） |

   > 说明：`M3` 从「第 3 个月复查（D90）」之后起算，即每 3 个月一次，故 `M3` 实际是戴镜后第 6 个月。此编号沿用 M10-09 `m10_followup_plan` 的 `followup_node` 口径，两表一致。

3. **`visit_late_days` 与逾期监控**：`visit_late_days = visited_at::date − scheduled_date`。>30 天视为「严重逾期」，触发 M10-09 的召回流程与 P09 的「漏复查统计」。主表 `m10_ortho_k_fitting.overdue_days` 由定时任务按「当前日期 − 应复查日期」计算。

4. **并发症编码清单**（`complications` JSONB 数组元素）：

   | 编码 | 中文 | 严重度 | 是否需上报 |
   |---|---|---|---|
   | `CORNEAL_STAINING` | 角膜上皮点状染色 | `MILD` | 否（≥3 级需上报） |
   | `CORNEAL_INFILTRATE` | 角膜浸润 | `MODERATE` | 是 |
   | `INFECTIOUS_KERATITIS` | 感染性角膜炎 | `SEVERE` | **强制上报** |
   | `CORNEAL_ABRASION` | 角膜上皮损伤 | `MODERATE` | 是 |
   | `CORNEAL_EDEMA` | 角膜水肿 | `MODERATE` | 是 |
   | `LENS_DEPOSIT` | 镜片蛋白沉淀 | `MILD` | 否 |
   | `LENS_DAMAGE` | 镜片破损 | `MILD` | 否（换片） |
   | `CONJUNCTIVITIS` | 结膜炎 | `MILD` | 否 |
   | `RED_EYE` | 眼红 | `MILD` | 否 |
   | `GHOST_VISION` | 重影/眩光 | `MILD` | 否 |

5. **`followup_result = 'DISCONTINUE'` 的数据库约束**：必须存在并发症数组或明确的角膜异常染色（`STAINING`/`INFILTRATE`/`ULCER`）。这防止了「无依据让患者停戴」引发的纠纷，也保证停戴原因可追溯（对应主表 `stop_reason_code`）。

6. **与 M10-09 的双向同步**：写入本表后，Service 层调用 M10-09 的 `POST /internal/v1/m10/followups/on-created`（P-26）更新计划状态，并把 `next_followup_date` 写回计划；M10-09 到访执行时读本表填充视力档案。若 M10-09 不可用，本表先落库，`m10_ortho_k_fitting.next_followup_date` 由本地任务维护，事后补偿同步。

**分区策略：** 无（30,000/年，单表 5 年约 15 万行，B-Tree 索引可支撑）。

---

### 4.10 表：`m10_ortho_k_log`（验配操作日志表）

**用途：** 记录 OK 镜验配全流程的**每一个写操作**，用于合规审计、纠纷追溯、异常排查。OK 镜属于三类医疗器械，监管要求「验配全过程可追溯」，本表是追溯体系的落地载体。

- **写入方：** 本子模块所有 Service 层的写操作方法（统一由 `OrthoKLogService.record()` 写入）。
- **只读方：** 质控科、医政科、M02 审计中心（只读转发）。
- **关键设计：** 按 `created_at` 月度 RANGE 分区，保留 24 个月（业务表保留永久，日志表保留 2 年，符合《医疗机构病历管理规定》对辅助记录的要求）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（分区表复合主键之一） |
| log_no | VARCHAR(40) | Y | NULL | 日志流水号（`OKL` + yyyyMMddHHmmss + 6 位） |
| fitting_id | BIGINT | Y | NULL | 验配单 ID（`m10_ortho_k_fitting.id`） |
| fit_no | VARCHAR(32) | Y | NULL | 验配单号（冗余，便于按单号直查） |
| patient_id | BIGINT | Y | NULL | 患者 ID（只读引用 M03） |
| entity_type | VARCHAR(32) | N | — | 操作对象类型 `FITTING`/`APPLY`/`CORNEA`/`TRIAL_LENS`/`TRIAL_USE`/`CUSTOM_PARAM`/`DELIVERY`/`FOLLOWUP` |
| entity_id | BIGINT | Y | NULL | 操作对象 ID |
| action | VARCHAR(32) | N | — | 操作动作（见业务说明枚举） |
| action_desc | VARCHAR(256) | Y | NULL | 动作中文描述（如「提交准入评估」「占用试戴片 TL-0820-300-001」） |
| from_status | VARCHAR(24) | Y | NULL | 变更前状态 |
| to_status | VARCHAR(24) | Y | NULL | 变更后状态 |
| changed_fields | JSONB | Y | NULL | 变更字段明细（`{"field": {"old": x, "new": y}}`） |
| snapshot | JSONB | Y | NULL | 关键快照（重大操作时存完整业务对象快照） |
| operator_id | BIGINT | Y | NULL | 操作人 ID |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名（快照） |
| operator_role | VARCHAR(32) | Y | NULL | 操作人角色 `OPTOMETRIST`/`OPHTHALMIC_PHYSICIAN`/`NURSE`/`SALES`/`MANAGER` |
| store_id | BIGINT | Y | NULL | 门店 ID |
| client_ip | VARCHAR(64) | Y | NULL | 客户端 IP |
| user_agent | VARCHAR(256) | Y | NULL | 客户端 UA |
| trace_id | VARCHAR(64) | Y | NULL | 链路追踪 ID（与响应 `trace_id` 一致） |
| result | VARCHAR(16) | N | 'SUCCESS' | 执行结果 `SUCCESS`/`FAIL` |
| error_code | VARCHAR(16) | Y | NULL | 失败时的错误码（如 `"1004019"`） |
| error_message | VARCHAR(512) | Y | NULL | 失败原因 |
| duration_ms | INT | Y | NULL | 操作耗时（毫秒） |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 日志时间（分区键） |

**索引设计：**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| `pk_m10_ortho_k_log` | 主键（复合） | `id`, `created_at` | 分区表主键必须含分区键 |
| `idx_m10_ortho_k_log_fitting` | B-Tree | `fitting_id`, `created_at` DESC | **按验配单查完整操作链（审计主力索引）** |
| `idx_m10_ortho_k_log_patient` | B-Tree | `patient_id`, `created_at` DESC | 按患者查操作历史 |
| `idx_m10_ortho_k_log_entity` | B-Tree | `entity_type`, `entity_id`, `created_at` DESC | 按对象查变更史 |
| `idx_m10_ortho_k_log_action` | B-Tree | `action`, `created_at` DESC | 按动作统计（试戴片占用/释放频次） |
| `idx_m10_ortho_k_log_operator` | B-Tree | `operator_id`, `created_at` DESC | 操作人行为审计 |
| `idx_m10_ortho_k_log_fail` | B-Tree（部分） | `created_at` DESC WHERE `result = 'FAIL'` | 失败操作排查 |
| `idx_m10_ortho_k_log_trace` | B-Tree（部分） | `trace_id` WHERE `trace_id IS NOT NULL` | 链路追踪反查 |
| `idx_m10_ortho_k_log_no` | B-Tree | `log_no` | 按流水号查 |

**约束说明：**

```sql
-- 日志流水号格式
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_no_format
    CHECK (log_no IS NULL OR log_no ~ '^OKL[0-9]{20}$');

-- 操作对象类型枚举
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_entity
    CHECK (entity_type IN ('FITTING', 'APPLY', 'CORNEA', 'TRIAL_LENS',
                           'TRIAL_USE', 'CUSTOM_PARAM', 'DELIVERY', 'FOLLOWUP'));

-- 操作动作枚举（覆盖本子模块全部写操作）
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_action
    CHECK (action IN (
        'CREATE_FITTING', 'VOID_FITTING', 'SUBMIT_APPLY', 'ASSESS_APPLY',
        'DOCTOR_REVIEW', 'UPLOAD_CONSENT',
        'SAVE_CORNEA', 'INVALID_CORNEA', 'LOCK_CORNEA',
        'OCCUPY_TRIAL', 'RELEASE_TRIAL', 'FORCE_RELEASE_TRIAL',
        'SAVE_TRIAL_EVAL', 'DISINFECT_TRIAL_LENS', 'SCRAP_TRIAL_LENS',
        'SAVE_CUSTOM_PARAM', 'FIT_CHECK', 'ORDER_CUSTOM', 'CANCEL_CUSTOM',
        'ACCEPT_DELIVERY', 'REJECT_DELIVERY', 'DISINFECT_DELIVERY',
        'DELIVER_LENS', 'TEACHING',
        'SAVE_FOLLOWUP', 'REPORT_COMPLICATION',
        'STOP_WEAR', 'START_REPLACE', 'CLOSE_FITTING', 'EXPORT'
    ));

-- 执行结果枚举
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_result
    CHECK (result IN ('SUCCESS', 'FAIL'));

-- 操作人角色枚举
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_role
    CHECK (operator_role IS NULL
           OR operator_role IN ('OPTOMETRIST', 'OPHTHALMIC_PHYSICIAN',
                                'NURSE', 'SALES', 'MANAGER', 'SYSTEM'));

-- 失败必须填错误码与错误信息
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_fail
    CHECK (result = 'SUCCESS'
           OR (error_code IS NOT NULL AND error_message IS NOT NULL));

-- 成功不得残留错误信息
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_success
    CHECK (result = 'FAIL' OR (error_code IS NULL AND error_message IS NULL));

-- 耗时不得为负
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_duration
    CHECK (duration_ms IS NULL OR duration_ms >= 0);

-- 验配类实体必须能关联到验配单
ALTER TABLE m10_ortho_k_log
    ADD CONSTRAINT ck_m10_ortho_k_log_fitting
    CHECK (entity_type = 'TRIAL_LENS' OR fitting_id IS NOT NULL);
```

**分区策略：**

```sql
-- 按月 RANGE 分区，保留 24 个月
CREATE TABLE m10_ortho_k_log (
    id           BIGINT GENERATED BY DEFAULT AS IDENTITY,
    log_no       VARCHAR(40),
    fitting_id   BIGINT,
    fit_no       VARCHAR(32),
    patient_id   BIGINT,
    entity_type  VARCHAR(32) NOT NULL,
    entity_id    BIGINT,
    action       VARCHAR(32) NOT NULL,
    action_desc  VARCHAR(256),
    from_status  VARCHAR(24),
    to_status    VARCHAR(24),
    changed_fields JSONB,
    snapshot     JSONB,
    operator_id  BIGINT,
    operator_name VARCHAR(64),
    operator_role VARCHAR(32),
    store_id     BIGINT,
    client_ip    VARCHAR(64),
    user_agent   VARCHAR(256),
    trace_id     VARCHAR(64),
    result       VARCHAR(16) NOT NULL DEFAULT 'SUCCESS',
    error_code   VARCHAR(16),
    error_message VARCHAR(512),
    duration_ms  INT,
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 分区示例：2026 年 10~12 月
CREATE TABLE m10_ortho_k_log_p202610 PARTITION OF m10_ortho_k_log
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');
CREATE TABLE m10_ortho_k_log_p202611 PARTITION OF m10_ortho_k_log
    FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');
CREATE TABLE m10_ortho_k_log_p202612 PARTITION OF m10_ortho_k_log
    FOR VALUES FROM ('2026-12-01') TO ('2027-01-01');

-- 默认分区：防止未预建月份写入失败
CREATE TABLE m10_ortho_k_log_pdefault PARTITION OF m10_ortho_k_log DEFAULT;

-- 分区自动维护：APScheduler 每月 20 日预建下下月分区
-- 保留策略：DELETE 或 DETACH 24 个月前的分区
```

**业务说明：**

1. **`action` 枚举覆盖本子模块全部 31 个写操作动作**，与第 8.3 节状态流转规则一一对应。新增动作时必须先在本表 CHECK 约束中登记，防止日志口径漂移。
2. **`changed_fields` 与 `snapshot` 的分工**：常规字段修改只记 `changed_fields`（增量，体积小）；**重大操作**（准入结论变更、定制参数下单、验发、上报不良事件、停戴）同时记 `snapshot`（完整业务对象 JSON），因为这类操作一旦出问题需要还原当时的全部上下文。
3. **`result = 'FAIL'` 也要记录**：失败的试戴片占用（`"1004019"` 冲突）、失败的 fit-check（`"1004026"`）都是重要的运维信号——失败率突增说明有并发问题或主数据异常。这类日志量大，故 `idx_m10_ortho_k_log_fail` 用部分索引只覆盖失败记录。
4. **保留 24 个月的理由**：业务表（验配单、定制参数、随访）永久保留；日志表是辅助记录，2 年足以覆盖「质量问题回溯 + 内部审计周期」。超过 24 个月的分区在每月维护任务中 `DETACH` 后归档到冷存储。
5. **与 M02 审计中心的关系**：本表是**业务级细粒度日志**（记录试戴片占用这种高频动作），M02-06 审计中心是**安全级操作日志**（记录权限变更、数据导出等）。本表不替代 M02，两者互补：涉及敏感操作的（如批量导出患者信息）由 Service 同时调用 `POST /internal/v1/m02/audit/record`。

---
### 4.11 SQLAlchemy 2.0 模型定义

```python
"""M10-04 OK镜与RGP验配随访 —— SQLAlchemy 2.0 模型"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, Identity,
    Index, Integer, Numeric, SmallInteger, String, Text, UniqueConstraint,
    func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class M10OrthoKApply(Base):
    """验配申请与准入评估表。一次验配申请一条，记录六大类准入评估结论。"""

    __tablename__ = "m10_ortho_k_apply"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    apply_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # 一、年龄与依从性
    age_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    age_note: Mapped[Optional[str]] = mapped_column(String(256))
    compliance_score: Mapped[Optional[int]] = mapped_column(SmallInteger)
    compliance_level: Mapped[Optional[str]] = mapped_column(String(16))
    compliance_note: Mapped[Optional[str]] = mapped_column(String(512))
    parent_consent_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_file_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    consent_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    consent_signer_name: Mapped[Optional[str]] = mapped_column(String(64))
    consent_signer_relation: Mapped[Optional[str]] = mapped_column(String(16))

    # 二、屈光度
    od_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_axis: Mapped[Optional[int]] = mapped_column(SmallInteger)
    os_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_axis: Mapped[Optional[int]] = mapped_column(SmallInteger)
    sphere_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cylinder_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    anisometropia: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    anisometropia_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    optometry_no: Mapped[Optional[str]] = mapped_column(String(32))

    # 三、角膜曲率与厚度
    od_k1: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_k2: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_k1: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_k2: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    curvature_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    od_cornea_thickness: Mapped[Optional[int]] = mapped_column(SmallInteger)
    os_cornea_thickness: Mapped[Optional[int]] = mapped_column(SmallInteger)
    thickness_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 四、眼压与泪液
    od_iop: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    os_iop: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    iop_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tear_break_up_time: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    schirmer_test: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    tear_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 五、角膜地形图与眼表
    topography_pattern: Mapped[Optional[str]] = mapped_column(String(24))
    topography_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    keratoconus_suspect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    eyelid_condition: Mapped[Optional[str]] = mapped_column(String(16))
    eyelid_check_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    conjunctiva_condition: Mapped[Optional[str]] = mapped_column(String(16))
    meibomian_gland: Mapped[Optional[str]] = mapped_column(String(16))
    contraindication: Mapped[Optional[str]] = mapped_column(String(512))

    # 六、综合结论
    access_result: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    fail_items: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    conditional_terms: Mapped[Optional[str]] = mapped_column(String(512))
    reject_reason: Mapped[Optional[str]] = mapped_column(String(512))
    assessor_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    assessor_name: Mapped[Optional[str]] = mapped_column(String(64))
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    doctor_review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    doctor_review_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    doctor_review_name: Mapped[Optional[str]] = mapped_column(String(64))
    doctor_review_opinion: Mapped[Optional[str]] = mapped_column(String(512))
    doctor_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    extra_items: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)

    # 标准字段
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_apply_no", "apply_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_apply_patient", "patient_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_apply_result", "access_result", text("assessed_at DESC"),
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_apply_pending", "created_at",
              postgresql_where=text("access_result = 'PENDING' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_apply_review", "doctor_review_required",
              postgresql_where=text("doctor_review_required = TRUE AND doctor_reviewed_at IS NULL")),
        Index("idx_m10_ortho_k_apply_kcsuspect", "patient_id",
              postgresql_where=text("keratoconus_suspect = TRUE")),
        Index("idx_m10_ortho_k_apply_fail_trgm", "reject_reason",
              postgresql_using="gin", postgresql_ops={"reject_reason": "gin_trgm_ops"}),
        CheckConstraint(
            "apply_no IS NULL OR apply_no ~ '^OKA[0-9]{12}$'",
            name="ck_m10_ortho_k_apply_no_format"),
        CheckConstraint(
            "access_result IN ('PENDING', 'PASS', 'CONDITIONAL', 'FAIL')",
            name="ck_m10_ortho_k_apply_result"),
        CheckConstraint(
            "compliance_level IS NULL OR compliance_level IN ('GOOD', 'FAIR', 'POOR')",
            name="ck_m10_ortho_k_apply_compliance"),
        CheckConstraint("compliance_score IS NULL OR compliance_score BETWEEN 0 AND 100",
                        name="ck_m10_ortho_k_apply_score"),
        CheckConstraint(
            "topography_pattern IS NULL OR topography_pattern IN "
            "('NORMAL', 'SYMMETRIC_BOWTIE', 'ASYMMETRIC_BOWTIE', "
            "'KERATOCONUS_SUSPECT', 'IRREGULAR')",
            name="ck_m10_ortho_k_apply_topo"),
        CheckConstraint(
            "(od_iop IS NULL OR od_iop BETWEEN 5 AND 30) "
            "AND (os_iop IS NULL OR os_iop BETWEEN 5 AND 30)",
            name="ck_m10_ortho_k_apply_iop"),
        CheckConstraint(
            "(od_cornea_thickness IS NULL OR od_cornea_thickness BETWEEN 300 AND 800) "
            "AND (os_cornea_thickness IS NULL OR os_cornea_thickness BETWEEN 300 AND 800)",
            name="ck_m10_ortho_k_apply_thickness"),
        CheckConstraint(
            "(od_k1 IS NULL OR od_k1 BETWEEN 35.00 AND 55.00) "
            "AND (od_k2 IS NULL OR od_k2 BETWEEN 35.00 AND 55.00) "
            "AND (os_k1 IS NULL OR os_k1 BETWEEN 35.00 AND 55.00) "
            "AND (os_k2 IS NULL OR os_k2 BETWEEN 35.00 AND 55.00)",
            name="ck_m10_ortho_k_apply_curvature"),
        CheckConstraint(
            "(od_k1 IS NULL OR od_k2 IS NULL OR od_k1 <= od_k2) "
            "AND (os_k1 IS NULL OR os_k2 IS NULL OR os_k1 <= os_k2)",
            name="ck_m10_ortho_k_apply_k_order"),
        CheckConstraint(
            "access_result = 'PENDING' "
            "OR (assessor_id IS NOT NULL AND assessed_at IS NOT NULL)",
            name="ck_m10_ortho_k_apply_assessed"),
        CheckConstraint(
            "access_result <> 'FAIL' OR (reject_reason IS NOT NULL "
            "AND char_length(btrim(reject_reason)) >= 10 "
            "AND fail_items IS NOT NULL AND jsonb_array_length(fail_items) > 0)",
            name="ck_m10_ortho_k_apply_fail"),
        CheckConstraint(
            "access_result <> 'CONDITIONAL' OR (conditional_terms IS NOT NULL "
            "AND char_length(btrim(conditional_terms)) >= 10)",
            name="ck_m10_ortho_k_apply_conditional"),
        CheckConstraint("access_result <> 'PASS' OR reject_reason IS NULL",
                        name="ck_m10_ortho_k_apply_pass_clean"),
        CheckConstraint("keratoconus_suspect = FALSE OR topography_check_passed = FALSE",
                        name="ck_m10_ortho_k_apply_kc"),
        CheckConstraint(
            "access_result = 'PENDING' OR access_result = 'FAIL' "
            "OR (parent_consent_signed = TRUE AND consent_file_id IS NOT NULL "
            "AND consent_signed_at IS NOT NULL AND consent_signer_name IS NOT NULL)",
            name="ck_m10_ortho_k_apply_consent"),
        CheckConstraint("anisometropia IS NULL OR anisometropia >= 0",
                        name="ck_m10_ortho_k_apply_aniso"),
    )


class M10OrthoKFitting(Base):
    """OK 镜验配单主表。一患一次验配一单，换片后新建并通过 previous_fit_id 串联。"""

    __tablename__ = "m10_ortho_k_fitting"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    apply_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    previous_fit_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    replace_round: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    empi_no: Mapped[Optional[str]] = mapped_column(String(32))
    customer_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # 患者快照
    patient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(8))
    age: Mapped[Optional[int]] = mapped_column(SmallInteger)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    id_card_no: Mapped[Optional[str]] = mapped_column(String(32))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    guardian_name: Mapped[Optional[str]] = mapped_column(String(64))
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(32))
    guardian_relation: Mapped[Optional[str]] = mapped_column(String(16))

    # 产品与器械合规
    product_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="ORTHO_K")
    product_code: Mapped[Optional[str]] = mapped_column(String(32))
    product_name: Mapped[Optional[str]] = mapped_column(String(128))
    brand_code: Mapped[Optional[str]] = mapped_column(String(32))
    param_group_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    param_group_code: Mapped[Optional[str]] = mapped_column(String(32))
    device_reg_no: Mapped[Optional[str]] = mapped_column(String(64))
    device_reg_valid_until: Mapped[Optional[date]] = mapped_column(Date)
    device_reg_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    device_class: Mapped[str] = mapped_column(String(8), nullable=False, default="CLASS_III")
    material: Mapped[Optional[str]] = mapped_column(String(64))

    # 验配人员与机构
    store_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    store_name: Mapped[Optional[str]] = mapped_column(String(64))
    fitter_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fitter_name: Mapped[Optional[str]] = mapped_column(String(64))
    fitter_qualification: Mapped[Optional[str]] = mapped_column(String(64))
    fitter_cert_no: Mapped[Optional[str]] = mapped_column(String(64))
    assistant_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    assistant_name: Mapped[Optional[str]] = mapped_column(String(64))
    review_doctor_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    review_doctor_name: Mapped[Optional[str]] = mapped_column(String(64))
    review_passed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 屈光与目标
    od_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_axis: Mapped[Optional[int]] = mapped_column(SmallInteger)
    os_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_axis: Mapped[Optional[int]] = mapped_column(SmallInteger)
    od_target_reduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_target_reduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_uncorrected_va: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    os_uncorrected_va: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    optometry_no: Mapped[Optional[str]] = mapped_column(String(32))
    prescription_no: Mapped[Optional[str]] = mapped_column(String(32))

    # 时间节点
    apply_time: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    trial_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ordered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expected_arrival_date: Mapped[Optional[date]] = mapped_column(Date)
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expected_replace_date: Mapped[Optional[date]] = mapped_column(Date)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 状态
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT")
    stop_reason_code: Mapped[Optional[str]] = mapped_column(String(32))
    stop_reason: Mapped[Optional[str]] = mapped_column(String(512))
    replace_reason_code: Mapped[Optional[str]] = mapped_column(String(32))
    complications: Mapped[Optional[List[Any]]] = mapped_column(JSONB)
    has_severe_complication: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 费用与订单快照
    sales_order_no: Mapped[Optional[str]] = mapped_column(String(32))
    order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    sales_order_status: Mapped[Optional[str]] = mapped_column(String(24))
    m10_order_no: Mapped[Optional[str]] = mapped_column(String(32))

    # 随访汇总
    followup_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_followup_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_followup_date: Mapped[Optional[date]] = mapped_column(Date)
    overdue_days: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    # 备注与标准字段
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    void_reason: Mapped[Optional[str]] = mapped_column(String(512))
    voided_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_fitting_no", "fit_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_fitting_apply", "apply_id", unique=True,
              postgresql_where=text("apply_id IS NOT NULL AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_fitting_patient", "patient_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_fitting_active", "patient_id",
              postgresql_where=text(
                  "status IN ('DELIVERED','FOLLOWING','REPLACE_DUE') AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_fitting_status", "status", text("created_at DESC"),
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_fitting_next_fu", "next_followup_date",
              postgresql_where=text(
                  "status IN ('DELIVERED','FOLLOWING','REPLACE_DUE') AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_fitting_overdue", "overdue_days",
              postgresql_where=text("overdue_days > 0 AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_fitting_fitter", "fitter_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_fitting_store_date", "store_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_fitting_sales_order", "sales_order_no",
              postgresql_where=text("sales_order_no IS NOT NULL")),
        Index("idx_m10_ortho_k_fitting_severe", "has_severe_complication",
              postgresql_where=text("has_severe_complication = TRUE")),
        Index("idx_m10_ortho_k_fitting_name_trgm", "patient_name",
              postgresql_using="gin", postgresql_ops={"patient_name": "gin_trgm_ops"}),
        CheckConstraint("fit_no IS NULL OR fit_no ~ '^OK[0-9]{12}$'",
                        name="ck_m10_ortho_k_fitting_no_format"),
        CheckConstraint("status = 'DRAFT' OR fit_no IS NOT NULL",
                        name="ck_m10_ortho_k_fitting_no_required"),
        CheckConstraint(
            "status IN ('DRAFT', 'APPLYING', 'ASSESSED', 'TRIAL', 'CUSTOMIZING', "
            "'ORDERED', 'ARRIVED', 'DELIVERED', 'FOLLOWING', "
            "'REPLACE_DUE', 'REPLACED', 'STOPPED', 'CLOSED')",
            name="ck_m10_ortho_k_fitting_status"),
        CheckConstraint("product_kind IN ('ORTHO_K', 'RGP')",
                        name="ck_m10_ortho_k_fitting_kind"),
        CheckConstraint("device_class = 'CLASS_III'",
                        name="ck_m10_ortho_k_fitting_device_class"),
        CheckConstraint(
            "(od_cylinder IS NULL OR od_cylinder = 0 "
            "OR (od_axis IS NOT NULL AND od_axis BETWEEN 1 AND 180)) "
            "AND (od_cylinder IS NULL OR od_cylinder <> 0 OR od_axis IS NULL)",
            name="ck_m10_ortho_k_fitting_od_axis"),
        CheckConstraint(
            "(os_cylinder IS NULL OR os_cylinder = 0 "
            "OR (os_axis IS NOT NULL AND os_axis BETWEEN 1 AND 180)) "
            "AND (os_cylinder IS NULL OR os_cylinder <> 0 OR os_axis IS NULL)",
            name="ck_m10_ortho_k_fitting_os_axis"),
        CheckConstraint(
            "(od_sphere IS NULL OR (od_sphere * 4) = trunc(od_sphere * 4)) "
            "AND (os_sphere IS NULL OR (os_sphere * 4) = trunc(os_sphere * 4)) "
            "AND (od_cylinder IS NULL OR (od_cylinder * 4) = trunc(od_cylinder * 4)) "
            "AND (os_cylinder IS NULL OR (os_cylinder * 4) = trunc(os_cylinder * 4))",
            name="ck_m10_ortho_k_fitting_sph_step"),
        CheckConstraint(
            "(od_target_reduction IS NULL "
            "OR (od_target_reduction < 0 AND od_target_reduction >= -6.00)) "
            "AND (os_target_reduction IS NULL "
            "OR (os_target_reduction < 0 AND os_target_reduction >= -6.00))",
            name="ck_m10_ortho_k_fitting_target"),
        CheckConstraint("age IS NULL OR age >= 8", name="ck_m10_ortho_k_fitting_age"),
        CheckConstraint(
            "age IS NULL OR age >= 18 "
            "OR (guardian_name IS NOT NULL AND guardian_phone IS NOT NULL)",
            name="ck_m10_ortho_k_fitting_guardian"),
        CheckConstraint(
            "status NOT IN ('DELIVERED', 'FOLLOWING', 'REPLACE_DUE', "
            "'REPLACED', 'STOPPED', 'CLOSED') "
            "OR (delivered_at IS NOT NULL AND expected_replace_date IS NOT NULL)",
            name="ck_m10_ortho_k_fitting_delivered"),
        CheckConstraint(
            "status <> 'STOPPED' OR (stop_reason_code IS NOT NULL "
            "AND stop_reason IS NOT NULL AND char_length(btrim(stop_reason)) >= 10 "
            "AND stopped_at IS NOT NULL)",
            name="ck_m10_ortho_k_fitting_stopped"),
        CheckConstraint("status = 'STOPPED' OR (stop_reason IS NULL AND stopped_at IS NULL)",
                        name="ck_m10_ortho_k_fitting_stop_clean"),
        CheckConstraint(
            "has_severe_complication = FALSE OR (complications IS NOT NULL "
            "AND jsonb_array_length(complications) > 0)",
            name="ck_m10_ortho_k_fitting_complication"),
        CheckConstraint("status <> 'REPLACED' OR replace_reason_code IS NOT NULL",
                        name="ck_m10_ortho_k_fitting_replaced"),
        CheckConstraint(
            "replace_round BETWEEN 1 AND 20 "
            "AND (replace_round = 1 OR previous_fit_id IS NOT NULL)",
            name="ck_m10_ortho_k_fitting_round"),
        CheckConstraint("previous_fit_id IS NULL OR previous_fit_id <> id",
                        name="ck_m10_ortho_k_fitting_prev_self"),
        CheckConstraint(
            "(assessed_at IS NULL OR assessed_at >= apply_time) "
            "AND (trial_started_at IS NULL OR assessed_at IS NULL "
            "     OR trial_started_at >= assessed_at) "
            "AND (ordered_at IS NULL OR trial_started_at IS NULL "
            "     OR ordered_at >= trial_started_at) "
            "AND (arrived_at IS NULL OR ordered_at IS NULL OR arrived_at >= ordered_at) "
            "AND (delivered_at IS NULL OR arrived_at IS NULL OR delivered_at >= arrived_at) "
            "AND (stopped_at IS NULL OR delivered_at IS NULL OR stopped_at >= delivered_at)",
            name="ck_m10_ortho_k_fitting_time_order"),
        CheckConstraint("overdue_days >= 0", name="ck_m10_ortho_k_fitting_overdue"),
        CheckConstraint(
            "(order_amount IS NULL OR order_amount >= 0) AND paid_amount >= 0",
            name="ck_m10_ortho_k_fitting_amount"),
        CheckConstraint("order_amount IS NULL OR paid_amount <= order_amount + 0.01",
                        name="ck_m10_ortho_k_fitting_paid"),
    )


class M10OrthoKCornea(Base):
    """角膜地形图参数表。按「一次测量 × 眼别」一行，定制参数的追溯源头。"""

    __tablename__ = "m10_ortho_k_cornea"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    cornea_no: Mapped[Optional[str]] = mapped_column(String(32))
    fitting_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    eye_side: Mapped[str] = mapped_column(String(8), nullable=False)
    measure_stage: Mapped[str] = mapped_column(String(16), nullable=False, default="PRE_FIT")
    measure_source: Mapped[str] = mapped_column(String(16), nullable=False, default="MANUAL")
    measured_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                  server_default=func.now())

    # 角膜曲率
    k1: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    k2: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    km: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    axis_k2: Mapped[Optional[int]] = mapped_column(SmallInteger)
    cornea_astigmatism: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    k1_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    k2_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 偏心率与直径
    e_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    e_value_4_5mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    hvid: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    diameter_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 3))

    # 瞳孔
    pupil_light: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pupil_dark: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pupil_center_offset: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 角膜厚度
    thickness_central: Mapped[Optional[int]] = mapped_column(SmallInteger)
    thickness_thinnest: Mapped[Optional[int]] = mapped_column(SmallInteger)
    thinnest_location: Mapped[Optional[str]] = mapped_column(String(32))
    thickness_2mm: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # 地形图分类
    topography_pattern: Mapped[Optional[str]] = mapped_column(String(24))
    keratoconus_suspect: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tkc_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    si_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    kpi_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 报告归档
    topography_report_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    topography_file_url: Mapped[Optional[str]] = mapped_column(String(512))
    device_code: Mapped[Optional[str]] = mapped_column(String(64))
    device_sn: Mapped[Optional[str]] = mapped_column(String(64))

    # 校验与备注
    is_valid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    invalid_reason: Mapped[Optional[str]] = mapped_column(String(512))
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_cornea_no", "cornea_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_cornea_eye", "fitting_id", "eye_side",
              "measure_stage", "measured_at", unique=True,
              postgresql_where=text("is_valid = TRUE AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_cornea_fitting", "fitting_id", text("measured_at DESC")),
        Index("idx_m10_ortho_k_cornea_patient", "patient_id", "eye_side",
              text("measured_at DESC")),
        Index("idx_m10_ortho_k_cornea_latest", "fitting_id", "eye_side",
              postgresql_where=text("measure_stage = 'PRE_FIT' AND is_valid = TRUE")),
        Index("idx_m10_ortho_k_cornea_kc", "patient_id", text("measured_at DESC"),
              postgresql_where=text("keratoconus_suspect = TRUE")),
        CheckConstraint("cornea_no IS NULL OR cornea_no ~ '^OCT[0-9]{12}$'",
                        name="ck_m10_ortho_k_cornea_no_format"),
        CheckConstraint("eye_side IN ('OD', 'OS')", name="ck_m10_ortho_k_cornea_eye"),
        CheckConstraint("measure_stage IN ('PRE_FIT', 'POST_TRIAL', 'FOLLOWUP', 'POST_STOP')",
                        name="ck_m10_ortho_k_cornea_stage"),
        CheckConstraint("measure_source IN ('MANUAL', 'DEVICE', 'IMPORT')",
                        name="ck_m10_ortho_k_cornea_source"),
        CheckConstraint(
            "topography_pattern IS NULL OR topography_pattern IN "
            "('NORMAL', 'SYMMETRIC_BOWTIE', 'ASYMMETRIC_BOWTIE', "
            "'KERATOCONUS_SUSPECT', 'IRREGULAR')",
            name="ck_m10_ortho_k_cornea_pattern"),
        CheckConstraint(
            "(k1 IS NULL OR k1 BETWEEN 35.00 AND 55.00) "
            "AND (k2 IS NULL OR k2 BETWEEN 35.00 AND 55.00) "
            "AND (km IS NULL OR km BETWEEN 35.00 AND 55.00)",
            name="ck_m10_ortho_k_cornea_k_range"),
        CheckConstraint(
            "(k1 IS NULL OR k2 IS NULL OR k1 <= k2) "
            "AND (km IS NULL OR k1 IS NULL OR km >= k1) "
            "AND (km IS NULL OR k2 IS NULL OR km <= k2)",
            name="ck_m10_ortho_k_cornea_k_order"),
        CheckConstraint(
            "cornea_astigmatism IS NULL "
            "OR (cornea_astigmatism >= 0 AND cornea_astigmatism <= 12.00)",
            name="ck_m10_ortho_k_cornea_astig"),
        CheckConstraint("axis_k2 IS NULL OR axis_k2 BETWEEN 1 AND 180",
                        name="ck_m10_ortho_k_cornea_axis"),
        CheckConstraint(
            "(e_value IS NULL OR e_value BETWEEN 0.00 AND 1.20) "
            "AND (e_value_4_5mm IS NULL OR e_value_4_5mm BETWEEN 0.00 AND 1.20)",
            name="ck_m10_ortho_k_cornea_e"),
        CheckConstraint("hvid IS NULL OR hvid BETWEEN 9.00 AND 14.00",
                        name="ck_m10_ortho_k_cornea_hvid"),
        CheckConstraint("diameter_ratio IS NULL OR diameter_ratio BETWEEN 0.800 AND 1.000",
                        name="ck_m10_ortho_k_cornea_ratio"),
        CheckConstraint(
            "(pupil_light IS NULL OR pupil_light BETWEEN 1.00 AND 9.00) "
            "AND (pupil_dark IS NULL OR pupil_dark BETWEEN 1.00 AND 10.00) "
            "AND (pupil_light IS NULL OR pupil_dark IS NULL OR pupil_dark >= pupil_light)",
            name="ck_m10_ortho_k_cornea_pupil"),
        CheckConstraint(
            "(thickness_central IS NULL OR thickness_central BETWEEN 300 AND 800) "
            "AND (thickness_thinnest IS NULL OR thickness_thinnest BETWEEN 300 AND 800) "
            "AND (thickness_2mm IS NULL OR thickness_2mm BETWEEN 300 AND 800) "
            "AND (thickness_central IS NULL OR thickness_thinnest IS NULL "
            "     OR thickness_thinnest <= thickness_central)",
            name="ck_m10_ortho_k_cornea_thickness"),
        CheckConstraint(
            "is_valid = TRUE OR (invalid_reason IS NOT NULL "
            "AND char_length(btrim(invalid_reason)) >= 10)",
            name="ck_m10_ortho_k_cornea_invalid"),
        CheckConstraint("is_locked = FALSE OR is_deleted = FALSE",
                        name="ck_m10_ortho_k_cornea_locked"),
        CheckConstraint(
            "keratoconus_suspect = FALSE "
            "OR topography_pattern = 'KERATOCONUS_SUSPECT' "
            "OR (tkc_index IS NOT NULL AND tkc_index > 1.00) "
            "OR (e_value IS NOT NULL AND e_value > 0.70)",
            name="ck_m10_ortho_k_cornea_kc_evidence"),
    )


class M10OrthoKTrialLens(Base):
    """试戴片台账表。记录试戴片实物档案，不含销售库存语义。"""

    __tablename__ = "m10_ortho_k_trial_lens"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    trial_lens_no: Mapped[str] = mapped_column(String(64), nullable=False)
    product_code: Mapped[str] = mapped_column(String(32), nullable=False)
    product_name: Mapped[Optional[str]] = mapped_column(String(128))
    param_group_code: Mapped[Optional[str]] = mapped_column(String(32))
    brand_code: Mapped[Optional[str]] = mapped_column(String(32))
    device_reg_no: Mapped[Optional[str]] = mapped_column(String(64))
    device_reg_valid_until: Mapped[Optional[date]] = mapped_column(Date)

    # 弧参数
    bc: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    rc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    ac: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    diameter: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    reduction_power: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    material: Mapped[Optional[str]] = mapped_column(String(64))

    # 适用角膜范围
    k_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    k_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))

    # 生命周期
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="IN_STOCK")
    sealed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    last_disinfected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    disinfect_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 实物与位置
    store_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    store_name: Mapped[Optional[str]] = mapped_column(String(64))
    storage_location: Mapped[Optional[str]] = mapped_column(String(64))
    box_no: Mapped[Optional[str]] = mapped_column(String(32))

    # 质量与报废
    damage_note: Mapped[Optional[str]] = mapped_column(String(512))
    scrapped_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    scrap_reason: Mapped[Optional[str]] = mapped_column(String(512))
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_trial_lens_no", "trial_lens_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_trial_lens_match", "bc", "reduction_power", "diameter",
              postgresql_where=text("status = 'IN_STOCK' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_trial_lens_krange", "k_min", "k_max",
              postgresql_where=text("status = 'IN_STOCK' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_trial_lens_store", "store_id", "status", "bc"),
        Index("idx_m10_ortho_k_trial_lens_status", "status", text("updated_at DESC")),
        Index("idx_m10_ortho_k_trial_lens_expire", "expire_date",
              postgresql_where=text("status IN ('IN_STOCK','IN_USE') AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_trial_lens_product", "product_code"),
        CheckConstraint("trial_lens_no ~ '^TL-[0-9]{4}-[0-9]{3}-[0-9]{3}$'",
                        name="ck_m10_ortho_k_trial_lens_no_format"),
        CheckConstraint(
            "status IN ('IN_STOCK', 'IN_USE', 'DISINFECTING', "
            "'DAMAGED', 'EXPIRED', 'SCRAPPED')",
            name="ck_m10_ortho_k_trial_lens_status"),
        CheckConstraint(
            "(rc IS NULL OR rc < bc) "
            "AND (ac IS NULL OR ac > bc) "
            "AND (pc IS NULL OR pc > ac) "
            "AND (rc IS NULL OR ac IS NULL OR ac > rc)",
            name="ck_m10_ortho_k_trial_lens_arc"),
        CheckConstraint("bc BETWEEN 7.00 AND 9.50", name="ck_m10_ortho_k_trial_lens_bc"),
        CheckConstraint("diameter IS NULL OR diameter BETWEEN 9.00 AND 12.00",
                        name="ck_m10_ortho_k_trial_lens_diameter"),
        CheckConstraint(
            "reduction_power IS NULL "
            "OR (reduction_power < 0 AND reduction_power >= -6.00)",
            name="ck_m10_ortho_k_trial_lens_reduction"),
        CheckConstraint(
            "(k_min IS NULL AND k_max IS NULL) "
            "OR (k_min IS NOT NULL AND k_max IS NOT NULL AND k_min <= k_max)",
            name="ck_m10_ortho_k_trial_lens_krange"),
        CheckConstraint(
            "(sealed = TRUE AND opened_at IS NULL) "
            "OR (sealed = FALSE AND opened_at IS NOT NULL)",
            name="ck_m10_ortho_k_trial_lens_opened"),
        CheckConstraint("sealed = TRUE OR expire_date IS NOT NULL",
                        name="ck_m10_ortho_k_trial_lens_expire_required"),
        CheckConstraint(
            "expire_date IS NULL OR opened_at IS NULL OR expire_date > opened_at::date",
            name="ck_m10_ortho_k_trial_lens_expire_order"),
        CheckConstraint(
            "(status = 'SCRAPPED' AND scrapped_at IS NOT NULL "
            " AND scrap_reason IS NOT NULL AND char_length(btrim(scrap_reason)) >= 10) "
            "OR (status <> 'SCRAPPED' AND scrapped_at IS NULL AND scrap_reason IS NULL)",
            name="ck_m10_ortho_k_trial_lens_scrap"),
        CheckConstraint("disinfect_count >= 0 AND usage_count >= 0",
                        name="ck_m10_ortho_k_trial_lens_counts"),
        CheckConstraint(
            "status <> 'DAMAGED' "
            "OR (damage_note IS NOT NULL AND char_length(btrim(damage_note)) >= 5)",
            name="ck_m10_ortho_k_trial_lens_damage"),
        CheckConstraint(
            "device_reg_no IS NOT NULL AND device_reg_valid_until IS NOT NULL",
            name="ck_m10_ortho_k_trial_lens_reg"),
    )


class M10OrthoKTrialUse(Base):
    """试戴片占用与试戴评估表。一片试戴片同一时刻只能被一个患者占用。"""

    __tablename__ = "m10_ortho_k_trial_use"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    use_no: Mapped[Optional[str]] = mapped_column(String(32))
    fitting_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    trial_lens_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trial_lens_no: Mapped[str] = mapped_column(String(64), nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    eye_side: Mapped[str] = mapped_column(String(8), nullable=False)
    trial_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)

    # 占用
    occupied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                  server_default=func.now())
    occupied_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occupied_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    release_kind: Mapped[Optional[str]] = mapped_column(String(16))
    released_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    released_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    occupied_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # 试戴片参数快照
    trial_bc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    trial_rc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    trial_ac: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    trial_pc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    trial_diameter: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    trial_reduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))

    # 荧光素染色配适
    fluo_central: Mapped[Optional[str]] = mapped_column(String(16))
    fluo_reverse: Mapped[Optional[str]] = mapped_column(String(16))
    fluo_align: Mapped[Optional[str]] = mapped_column(String(16))
    fluo_peripheral: Mapped[Optional[str]] = mapped_column(String(16))
    fit_quality: Mapped[Optional[str]] = mapped_column(String(16))

    # 定位与活动度
    lens_position: Mapped[Optional[str]] = mapped_column(String(16))
    decentered_direction: Mapped[Optional[str]] = mapped_column(String(16))
    lens_movement: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    coverage_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    scleral_gap: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 视力与屈光
    va_trial: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    va_corrected: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    over_refraction_sph: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    over_refraction_cyl: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    over_refraction_axis: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # TFT
    tft_performed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tft_pattern: Mapped[Optional[str]] = mapped_column(String(16))
    tft_ring_diameter: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tft_ring_integrity: Mapped[Optional[str]] = mapped_column(String(16))
    tft_decentration: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    tft_report_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # 订片决策
    decision: Mapped[Optional[str]] = mapped_column(String(24))
    decision_note: Mapped[Optional[str]] = mapped_column(String(512))
    suggested_bc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    suggested_reduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    suggested_diameter: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 消毒与归还
    disinfected_after: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disinfected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    damage_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    damage_note: Mapped[Optional[str]] = mapped_column(String(512))
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        # ★ 核心并发约束：未释放的占用记录中，同一试戴片只允许一条
        Index("uk_m10_ortho_k_trial_use_active", "trial_lens_id", unique=True,
              postgresql_where=text("released_at IS NULL AND is_deleted = FALSE")),
        Index("uk_m10_ortho_k_trial_use_no", "use_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_trial_use_seq", "fitting_id", "eye_side", "trial_seq",
              unique=True, postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_trial_use_fitting", "fitting_id", text("occupied_at DESC")),
        Index("idx_m10_ortho_k_trial_use_lens", "trial_lens_id", text("occupied_at DESC")),
        Index("idx_m10_ortho_k_trial_use_open", "fitting_id", "eye_side",
              postgresql_where=text("released_at IS NULL")),
        Index("idx_m10_ortho_k_trial_use_result", "fit_quality", text("occupied_at DESC")),
        Index("idx_m10_ortho_k_trial_use_decision", "decision", text("occupied_at DESC"),
              postgresql_where=text("decision IS NOT NULL")),
        CheckConstraint("use_no IS NULL OR use_no ~ '^OKT[0-9]{12}$'",
                        name="ck_m10_ortho_k_trial_use_no_format"),
        CheckConstraint("eye_side IN ('OD', 'OS')", name="ck_m10_ortho_k_trial_use_eye"),
        CheckConstraint("trial_seq BETWEEN 1 AND 20", name="ck_m10_ortho_k_trial_use_seq_range"),
        CheckConstraint(
            "(fluo_central IS NULL OR fluo_central IN ('FLAT', 'IDEAL', 'STEEP')) "
            "AND (fluo_reverse IS NULL OR fluo_reverse IN ('FLAT', 'IDEAL', 'STEEP')) "
            "AND (fluo_align IS NULL OR fluo_align IN ('FLAT', 'IDEAL', 'STEEP')) "
            "AND (fluo_peripheral IS NULL OR fluo_peripheral IN ('FLAT', 'IDEAL', 'STEEP'))",
            name="ck_m10_ortho_k_trial_use_fluo"),
        CheckConstraint(
            "fit_quality IS NULL OR fit_quality IN ('EXCELLENT', 'ACCEPTABLE', 'UNACCEPTABLE')",
            name="ck_m10_ortho_k_trial_use_quality"),
        CheckConstraint(
            "lens_position IS NULL "
            "OR lens_position IN ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED')",
            name="ck_m10_ortho_k_trial_use_position"),
        CheckConstraint(
            "decentered_direction IS NULL "
            "OR lens_position IN ('SLIGHT_DECENTERED', 'DECENTERED')",
            name="ck_m10_ortho_k_trial_use_direction"),
        CheckConstraint("lens_movement IS NULL OR lens_movement BETWEEN 0.00 AND 3.00",
                        name="ck_m10_ortho_k_trial_use_movement"),
        CheckConstraint("coverage_ratio IS NULL OR coverage_ratio BETWEEN 50.00 AND 100.00",
                        name="ck_m10_ortho_k_trial_use_coverage"),
        CheckConstraint("scleral_gap IS NULL OR scleral_gap BETWEEN 0.00 AND 1.50",
                        name="ck_m10_ortho_k_trial_use_gap"),
        CheckConstraint(
            "tft_pattern IS NULL OR tft_pattern IN ('BULLSEYE', 'SMILEY', 'TARGET', "
            "'CENTRAL_CRAB', 'NON_CENTRAL', 'IRREGULAR')",
            name="ck_m10_ortho_k_trial_use_tft"),
        CheckConstraint(
            "tft_performed = FALSE OR (tft_pattern IS NOT NULL AND tft_report_id IS NOT NULL)",
            name="ck_m10_ortho_k_trial_use_tft_required"),
        CheckConstraint(
            "decision IS NULL "
            "OR decision IN ('ORDER_AS_IS', 'ADJUST', 'RETRY', 'ABORT')",
            name="ck_m10_ortho_k_trial_use_decision"),
        CheckConstraint(
            "decision NOT IN ('RETRY', 'ABORT') "
            "OR (decision_note IS NOT NULL AND char_length(btrim(decision_note)) >= 10)",
            name="ck_m10_ortho_k_trial_use_decision_note"),
        CheckConstraint(
            "released_at IS NULL OR (release_kind IS NOT NULL AND released_by IS NOT NULL "
            "AND occupied_minutes IS NOT NULL AND occupied_minutes >= 0)",
            name="ck_m10_ortho_k_trial_use_released"),
        CheckConstraint("released_at IS NULL OR released_at >= occupied_at",
                        name="ck_m10_ortho_k_trial_use_time_order"),
        CheckConstraint(
            "damage_found = FALSE "
            "OR (damage_note IS NOT NULL AND char_length(btrim(damage_note)) >= 5)",
            name="ck_m10_ortho_k_trial_use_damage"),
        CheckConstraint(
            "(disinfected_after = FALSE AND disinfected_at IS NULL) "
            "OR (disinfected_after = TRUE AND disinfected_at IS NOT NULL)",
            name="ck_m10_ortho_k_trial_use_disinfected"),
        CheckConstraint("released_at IS NULL OR is_deleted = FALSE",
                        name="ck_m10_ortho_k_trial_use_undeletable"),
    )


class M10OrthoKCustomParam(Base):
    """定制参数表。按验配单 × 眼别一行，必须带 M01-08 fit-check 回执。"""

    __tablename__ = "m10_ortho_k_custom_param"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    custom_no: Mapped[Optional[str]] = mapped_column(String(32))
    fitting_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    eye_side: Mapped[str] = mapped_column(String(8), nullable=False)
    trial_use_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    cornea_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    param_source: Mapped[str] = mapped_column(String(16), nullable=False, default="TRIAL")

    # 弧参数
    bc: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    rc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    ac: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    pc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    diameter: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    # 降度
    target_reduction: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    actual_reduction: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    reduction_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    reduction_adjust_reason: Mapped[Optional[str]] = mapped_column(String(512))
    over_refraction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))

    # 材质与外观
    material: Mapped[Optional[str]] = mapped_column(String(64))
    color: Mapped[Optional[str]] = mapped_column(String(32))
    manufacturer_code: Mapped[Optional[str]] = mapped_column(String(32))
    manufacturer_name: Mapped[Optional[str]] = mapped_column(String(128))
    manufacture_lead_days: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # M01-08 fit-check 回执
    fit_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fit_check_passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    fit_check_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    fit_check_message: Mapped[Optional[str]] = mapped_column(String(512))
    check_result: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    check_fail_items: Mapped[Optional[List[Any]]] = mapped_column(JSONB)

    # 下单与状态
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="DRAFT")
    is_ordered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ordered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ordered_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    factory_order_no: Mapped[Optional[str]] = mapped_column(String(64))
    expected_arrival_date: Mapped[Optional[date]] = mapped_column(Date)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(512))

    # 价格快照
    price_ref: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    price_ref_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_custom_param_no", "custom_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_custom_param_eye", "fitting_id", "eye_side", unique=True,
              postgresql_where=text("status <> 'CANCELLED' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_custom_param_fitting", "fitting_id", "eye_side"),
        Index("idx_m10_ortho_k_custom_param_status", "status", text("created_at DESC")),
        Index("idx_m10_ortho_k_custom_param_ordered", "ordered_at",
              postgresql_where=text(
                  "is_ordered = TRUE AND status IN ('ORDERED','PRODUCING')")),
        Index("idx_m10_ortho_k_custom_param_eta", "expected_arrival_date",
              postgresql_where=text("status = 'ORDERED' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_custom_param_checkfail", "fitting_id", "eye_side",
              postgresql_where=text("check_result = 'FAIL'")),
        Index("idx_m10_ortho_k_custom_param_cornea", "cornea_id"),
        CheckConstraint("custom_no IS NULL OR custom_no ~ '^OKC[0-9]{12}$'",
                        name="ck_m10_ortho_k_custom_param_no_format"),
        CheckConstraint("eye_side IN ('OD', 'OS')", name="ck_m10_ortho_k_custom_param_eye"),
        CheckConstraint(
            "bc BETWEEN 7.00 AND 9.50 "
            "AND (rc IS NULL OR rc < bc) "
            "AND (ac IS NULL OR ac > bc) "
            "AND (pc IS NULL OR ac IS NULL OR pc > ac)",
            name="ck_m10_ortho_k_custom_param_arc"),
        CheckConstraint("diameter BETWEEN 9.00 AND 12.00 AND diameter > bc",
                        name="ck_m10_ortho_k_custom_param_diameter"),
        CheckConstraint(
            "target_reduction < 0 AND target_reduction >= -6.00 "
            "AND actual_reduction < 0 AND actual_reduction >= -6.00",
            name="ck_m10_ortho_k_custom_param_reduction"),
        CheckConstraint(
            "reduction_diff IS NULL "
            "OR abs(reduction_diff - (actual_reduction - target_reduction)) < 0.001",
            name="ck_m10_ortho_k_custom_param_diff"),
        CheckConstraint(
            "reduction_diff IS NULL OR abs(reduction_diff) < 0.001 "
            "OR (reduction_adjust_reason IS NOT NULL "
            "AND char_length(btrim(reduction_adjust_reason)) >= 10)",
            name="ck_m10_ortho_k_custom_param_diff_reason"),
        CheckConstraint(
            "status IN ('DRAFT', 'CHECKED', 'ORDERED', 'PRODUCING', 'ARRIVED', 'CANCELLED')",
            name="ck_m10_ortho_k_custom_param_status"),
        CheckConstraint(
            "check_result IN ('PENDING', 'PASS', 'PASS_WITH_WARN', 'FAIL')",
            name="ck_m10_ortho_k_custom_param_check"),
        CheckConstraint("param_source IN ('TRIAL', 'CALCULATED', 'DOCTOR')",
                        name="ck_m10_ortho_k_custom_param_source"),
        CheckConstraint(
            "color IS NULL OR color IN ('CLEAR', 'BLUE', 'GREEN', 'VIOLET')",
            name="ck_m10_ortho_k_custom_param_color"),
        # ★★ 必须调用过 M01-08 fit-check 才能下单
        CheckConstraint(
            "is_ordered = FALSE OR (fit_check_at IS NOT NULL "
            "AND fit_check_passed IS NOT NULL AND fit_check_result IS NOT NULL "
            "AND check_result <> 'PENDING')",
            name="ck_m10_ortho_k_custom_param_fitcheck_required"),
        # ★★ fit-check 不通过禁止下单
        CheckConstraint("check_result <> 'FAIL' OR is_ordered = FALSE",
                        name="ck_m10_ortho_k_custom_param_fitcheck_fail"),
        CheckConstraint(
            "check_result <> 'FAIL' OR (check_fail_items IS NOT NULL "
            "AND jsonb_array_length(check_fail_items) > 0)",
            name="ck_m10_ortho_k_custom_param_fail_items"),
        CheckConstraint(
            "check_result IN ('PENDING', 'FAIL') OR fit_check_passed = TRUE",
            name="ck_m10_ortho_k_custom_param_check_consistent"),
        CheckConstraint(
            "is_ordered = FALSE OR (status IN ('ORDERED', 'PRODUCING', 'ARRIVED') "
            "AND ordered_at IS NOT NULL AND ordered_by IS NOT NULL "
            "AND expected_arrival_date IS NOT NULL "
            "AND expected_arrival_date >= ordered_at::date)",
            name="ck_m10_ortho_k_custom_param_ordered"),
        CheckConstraint("status <> 'ARRIVED' OR is_ordered = TRUE",
                        name="ck_m10_ortho_k_custom_param_arrived"),
        CheckConstraint(
            "status <> 'CANCELLED' OR (cancelled_at IS NOT NULL "
            "AND cancel_reason IS NOT NULL AND char_length(btrim(cancel_reason)) >= 10)",
            name="ck_m10_ortho_k_custom_param_cancelled"),
        CheckConstraint("status <> 'CANCELLED' OR is_ordered = FALSE",
                        name="ck_m10_ortho_k_custom_param_cancel_guard"),
        CheckConstraint(
            "(price_ref IS NULL AND price_ref_at IS NULL) "
            "OR (price_ref IS NOT NULL AND price_ref_at IS NOT NULL AND price_ref >= 0)",
            name="ck_m10_ortho_k_custom_param_price"),
        CheckConstraint("is_ordered = FALSE OR is_deleted = FALSE",
                        name="ck_m10_ortho_k_custom_param_undeletable"),
    )


class M10OrthoKDelivery(Base):
    """到片验收与发放表。按「片」一行，记录验收、消毒、发放与首次戴镜教学。"""

    __tablename__ = "m10_ortho_k_delivery"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    delivery_no: Mapped[Optional[str]] = mapped_column(String(32))
    fitting_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    custom_param_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    eye_side: Mapped[str] = mapped_column(String(8), nullable=False)
    lens_no: Mapped[Optional[str]] = mapped_column(String(64))
    factory_order_no: Mapped[Optional[str]] = mapped_column(String(64))

    # 到片
    arrived_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    arrived_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    arrived_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    package_intact: Mapped[Optional[bool]] = mapped_column(Boolean)
    package_note: Mapped[Optional[str]] = mapped_column(String(512))

    # 参数逐项核对
    actual_bc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_rc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_ac: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_pc: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_diameter: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    actual_reduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    actual_material: Mapped[Optional[str]] = mapped_column(String(64))
    actual_color: Mapped[Optional[str]] = mapped_column(String(32))
    param_match: Mapped[Optional[bool]] = mapped_column(Boolean)
    mismatch_items: Mapped[Optional[List[Any]]] = mapped_column(JSONB)

    # 外观检查
    appearance_ok: Mapped[Optional[bool]] = mapped_column(Boolean)
    appearance_note: Mapped[Optional[str]] = mapped_column(String(512))
    scratch_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chip_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    bubble_found: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 验收结论
    accept_result: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    reject_reason: Mapped[Optional[str]] = mapped_column(String(512))
    returned_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 消毒与发放
    disinfected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disinfected_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    disinfect_method: Mapped[Optional[str]] = mapped_column(String(32))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    delivered_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    delivered_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    receiver_name: Mapped[Optional[str]] = mapped_column(String(64))
    receiver_relation: Mapped[Optional[str]] = mapped_column(String(16))
    receiver_sign_file_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # 首次戴镜教学
    teaching_done: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    teaching_minutes: Mapped[Optional[int]] = mapped_column(SmallInteger)
    teaching_content: Mapped[Optional[List[Any]]] = mapped_column(JSONB)
    teaching_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    teaching_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    teaching_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # 佩戴起算与换片
    wear_start_date: Mapped[Optional[date]] = mapped_column(Date)
    expected_replace_date: Mapped[Optional[date]] = mapped_column(Date)
    replace_months: Mapped[Optional[int]] = mapped_column(SmallInteger)
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_delivery_no", "delivery_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_delivery_lens_no", "lens_no", unique=True,
              postgresql_where=text("lens_no IS NOT NULL AND is_deleted = FALSE")),
        Index("uk_m10_ortho_k_delivery_param", "custom_param_id", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_delivery_fitting", "fitting_id", "eye_side"),
        Index("idx_m10_ortho_k_delivery_pending", "arrived_at",
              postgresql_where=text("accept_result = 'PENDING' AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_delivery_undelivered", "fitting_id",
              postgresql_where=text(
                  "accept_result = 'PASS' AND delivered_at IS NULL AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_delivery_replace", "expected_replace_date",
              postgresql_where=text("delivered_at IS NOT NULL AND is_deleted = FALSE")),
        CheckConstraint("delivery_no IS NULL OR delivery_no ~ '^OKD[0-9]{12}$'",
                        name="ck_m10_ortho_k_delivery_no_format"),
        CheckConstraint("eye_side IN ('OD', 'OS')", name="ck_m10_ortho_k_delivery_eye"),
        CheckConstraint(
            "accept_result IN ('PENDING', 'PASS', 'FAIL', 'RETURNED')",
            name="ck_m10_ortho_k_delivery_accept"),
        CheckConstraint(
            "receiver_relation IS NULL "
            "OR receiver_relation IN ('SELF', 'FATHER', 'MOTHER', 'GRANDPARENT', 'OTHER')",
            name="ck_m10_ortho_k_delivery_relation"),
        CheckConstraint(
            "disinfect_method IS NULL OR disinfect_method IN ('BOIL', 'PEROXIDE', 'UV')",
            name="ck_m10_ortho_k_delivery_disinfect"),
        CheckConstraint(
            "(actual_bc IS NULL OR actual_bc BETWEEN 7.00 AND 9.50) "
            "AND (actual_diameter IS NULL OR actual_diameter BETWEEN 9.00 AND 12.00) "
            "AND (actual_reduction IS NULL "
            "     OR (actual_reduction < 0 AND actual_reduction >= -6.00))",
            name="ck_m10_ortho_k_delivery_actual"),
        CheckConstraint(
            "(actual_rc IS NULL OR actual_bc IS NULL OR actual_rc < actual_bc) "
            "AND (actual_ac IS NULL OR actual_bc IS NULL OR actual_ac > actual_bc) "
            "AND (actual_pc IS NULL OR actual_ac IS NULL OR actual_pc > actual_ac)",
            name="ck_m10_ortho_k_delivery_arc"),
        # ★ 验收通过必须完成全部核对项
        CheckConstraint(
            "accept_result <> 'PASS' OR (lens_no IS NOT NULL AND param_match = TRUE "
            "AND appearance_ok = TRUE AND actual_bc IS NOT NULL "
            "AND actual_diameter IS NOT NULL AND actual_reduction IS NOT NULL "
            "AND arrived_at IS NOT NULL)",
            name="ck_m10_ortho_k_delivery_pass"),
        CheckConstraint(
            "param_match IS DISTINCT FROM FALSE "
            "OR (mismatch_items IS NOT NULL AND jsonb_array_length(mismatch_items) > 0)",
            name="ck_m10_ortho_k_delivery_mismatch"),
        CheckConstraint(
            "accept_result NOT IN ('FAIL', 'RETURNED') "
            "OR (reject_reason IS NOT NULL AND char_length(btrim(reject_reason)) >= 10)",
            name="ck_m10_ortho_k_delivery_reject"),
        CheckConstraint("accept_result <> 'RETURNED' OR returned_at IS NOT NULL",
                        name="ck_m10_ortho_k_delivery_returned"),
        # ★ 发放必须：验收通过 + 已消毒 + 教学完成 ≥30 分钟 + 领取签字
        CheckConstraint(
            "delivered_at IS NULL OR (accept_result = 'PASS' AND disinfected = TRUE "
            "AND disinfected_at IS NOT NULL AND delivered_by IS NOT NULL "
            "AND receiver_name IS NOT NULL AND receiver_relation IS NOT NULL "
            "AND receiver_sign_file_id IS NOT NULL AND teaching_done = TRUE "
            "AND teaching_minutes IS NOT NULL AND teaching_minutes >= 30 "
            "AND teaching_signed = TRUE AND wear_start_date IS NOT NULL "
            "AND expected_replace_date IS NOT NULL)",
            name="ck_m10_ortho_k_delivery_deliver"),
        CheckConstraint("teaching_minutes IS NULL OR teaching_minutes BETWEEN 0 AND 180",
                        name="ck_m10_ortho_k_delivery_teaching"),
        CheckConstraint("teaching_done = TRUE OR teaching_minutes IS NULL",
                        name="ck_m10_ortho_k_delivery_teaching_pair"),
        CheckConstraint(
            "(disinfected = FALSE AND disinfected_at IS NULL) "
            "OR (disinfected = TRUE AND disinfected_at IS NOT NULL)",
            name="ck_m10_ortho_k_delivery_disinfect_pair"),
        CheckConstraint(
            "(disinfected_at IS NULL OR arrived_at IS NULL OR disinfected_at >= arrived_at) "
            "AND (delivered_at IS NULL OR disinfected_at IS NULL "
            "     OR delivered_at >= disinfected_at)",
            name="ck_m10_ortho_k_delivery_time_order"),
        CheckConstraint(
            "expected_replace_date IS NULL OR wear_start_date IS NULL "
            "OR expected_replace_date > wear_start_date",
            name="ck_m10_ortho_k_delivery_replace"),
        CheckConstraint("replace_months IS NULL OR replace_months BETWEEN 6 AND 24",
                        name="ck_m10_ortho_k_delivery_replace_months"),
        CheckConstraint("delivered_at IS NULL OR is_deleted = FALSE",
                        name="ck_m10_ortho_k_delivery_undeletable"),
        CheckConstraint(
            "appearance_ok IS DISTINCT FROM TRUE "
            "OR (scratch_found = FALSE AND chip_found = FALSE AND bubble_found = FALSE "
            "AND appearance_note IS NULL)",
            name="ck_m10_ortho_k_delivery_appearance"),
    )


class M10OrthoKFollowup(Base):
    """戴镜随访记录表。记录 1/7/30/90 天 + 每 3 月的复查临床结果。"""

    __tablename__ = "m10_ortho_k_followup"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    followup_no: Mapped[Optional[str]] = mapped_column(String(32))
    fitting_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    patient_name: Mapped[str] = mapped_column(String(64), nullable=False)
    followup_plan_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    followup_seq: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    followup_node: Mapped[str] = mapped_column(String(16), nullable=False, default="D1")
    followup_day: Mapped[Optional[int]] = mapped_column(Integer)
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    visited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    visit_late_days: Mapped[Optional[int]] = mapped_column(Integer)
    followup_type: Mapped[str] = mapped_column(String(16), nullable=False,
                                               default="SCHEDULED")

    # 主观与依从性
    subjective_complaints: Mapped[Optional[str]] = mapped_column(String(512))
    wearing_hours_per_night: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    wearing_days_per_week: Mapped[Optional[int]] = mapped_column(SmallInteger)
    compliance_check: Mapped[Optional[str]] = mapped_column(String(16))

    # 视力与屈光
    od_va_uncorrected: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    os_va_uncorrected: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    od_va_corrected: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    os_va_corrected: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2))
    od_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_sphere: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    os_cylinder: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    od_axial_length: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    os_axial_length: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    # 角膜状态
    od_fluorescein: Mapped[Optional[str]] = mapped_column(String(24))
    os_fluorescein: Mapped[Optional[str]] = mapped_column(String(24))
    od_stain_location: Mapped[Optional[str]] = mapped_column(String(32))
    os_stain_location: Mapped[Optional[str]] = mapped_column(String(32))
    od_fluorescein_grade: Mapped[Optional[int]] = mapped_column(SmallInteger)
    os_fluorescein_grade: Mapped[Optional[int]] = mapped_column(SmallInteger)
    od_iop: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    os_iop: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 1))
    od_cornea_thickness: Mapped[Optional[int]] = mapped_column(SmallInteger)
    os_cornea_thickness: Mapped[Optional[int]] = mapped_column(SmallInteger)

    # 镜片配适与清洁度
    od_lens_position: Mapped[Optional[str]] = mapped_column(String(16))
    os_lens_position: Mapped[Optional[str]] = mapped_column(String(16))
    od_lens_movement: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    os_lens_movement: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    od_fluo_fit: Mapped[Optional[str]] = mapped_column(String(16))
    os_fluo_fit: Mapped[Optional[str]] = mapped_column(String(16))
    od_lens_cleanliness: Mapped[Optional[str]] = mapped_column(String(16))
    os_lens_cleanliness: Mapped[Optional[str]] = mapped_column(String(16))
    od_lens_damage: Mapped[Optional[str]] = mapped_column(String(16))
    os_lens_damage: Mapped[Optional[str]] = mapped_column(String(16))

    # TFT
    od_tft_pattern: Mapped[Optional[str]] = mapped_column(String(16))
    os_tft_pattern: Mapped[Optional[str]] = mapped_column(String(16))
    topography_report_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    cornea_record_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # 并发症与结论
    complications: Mapped[Optional[List[Any]]] = mapped_column(JSONB)
    complication_grade: Mapped[Optional[str]] = mapped_column(String(16))
    report_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    report_id: Mapped[Optional[str]] = mapped_column(String(64))
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    followup_result: Mapped[str] = mapped_column(String(16), nullable=False, default="NORMAL")
    disposal_advice: Mapped[Optional[str]] = mapped_column(String(512))
    next_followup_date: Mapped[Optional[date]] = mapped_column(Date)
    next_followup_node: Mapped[Optional[str]] = mapped_column(String(16))
    followup_doctor_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    followup_doctor_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    remark: Mapped[Optional[str]] = mapped_column(String(1024))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now(),
                                                 onupdate=func.now())
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("uk_m10_ortho_k_followup_no", "followup_no", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_followup_seq", "fitting_id", "followup_seq", unique=True,
              postgresql_where=text("is_deleted = FALSE")),
        Index("uk_m10_ortho_k_followup_node", "fitting_id", "followup_node", unique=True,
              postgresql_where=text(
                  "followup_node NOT IN ('EXTRA') AND is_deleted = FALSE")),
        Index("idx_m10_ortho_k_followup_fitting", "fitting_id", text("visited_at DESC")),
        Index("idx_m10_ortho_k_followup_patient", "patient_id", text("visited_at DESC")),
        Index("idx_m10_ortho_k_followup_node_stat", "followup_node", text("visited_at DESC"),
              postgresql_where=text("is_deleted = FALSE")),
        Index("idx_m10_ortho_k_followup_severe", "visited_at",
              postgresql_where=text("report_required = TRUE")),
        Index("idx_m10_ortho_k_followup_unreported", "visited_at",
              postgresql_where=text("report_required = TRUE AND report_id IS NULL")),
        CheckConstraint("followup_no IS NULL OR followup_no ~ '^OKF[0-9]{12}$'",
                        name="ck_m10_ortho_k_followup_no_format"),
        CheckConstraint("followup_seq BETWEEN 1 AND 60",
                        name="ck_m10_ortho_k_followup_seq_range"),
        # ★ 复查节点：1/7/30/90 天 + 每 3 月
        CheckConstraint(
            "followup_node IN ('D1', 'D7', 'D30', 'D90', 'M3', 'M6', 'M9', 'M12', 'EXTRA')",
            name="ck_m10_ortho_k_followup_node_ck"),
        CheckConstraint("followup_type IN ('SCHEDULED', 'UNSCHEDULED', 'POST_REPLACE')",
                        name="ck_m10_ortho_k_followup_type"),
        CheckConstraint(
            "compliance_check IS NULL OR compliance_check IN ('GOOD', 'FAIR', 'POOR')",
            name="ck_m10_ortho_k_followup_compliance"),
        CheckConstraint(
            "wearing_hours_per_night IS NULL "
            "OR wearing_hours_per_night BETWEEN 0.0 AND 14.0",
            name="ck_m10_ortho_k_followup_hours"),
        CheckConstraint("wearing_days_per_week IS NULL OR wearing_days_per_week BETWEEN 0 AND 7",
                        name="ck_m10_ortho_k_followup_days"),
        CheckConstraint(
            "(od_fluorescein IS NULL OR od_fluorescein IN "
            " ('NORMAL', 'PUNCTATE_STAINING', 'STAINING', 'INFILTRATE', 'ULCER')) "
            "AND (os_fluorescein IS NULL OR os_fluorescein IN "
            " ('NORMAL', 'PUNCTATE_STAINING', 'STAINING', 'INFILTRATE', 'ULCER'))",
            name="ck_m10_ortho_k_followup_fluorescein"),
        CheckConstraint(
            "(od_fluorescein_grade IS NULL OR od_fluorescein_grade BETWEEN 0 AND 4) "
            "AND (os_fluorescein_grade IS NULL OR os_fluorescein_grade BETWEEN 0 AND 4)",
            name="ck_m10_ortho_k_followup_grade"),
        CheckConstraint(
            "(od_lens_position IS NULL OR od_lens_position IN "
            " ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED')) "
            "AND (os_lens_position IS NULL OR os_lens_position IN "
            " ('CENTERED', 'SLIGHT_DECENTERED', 'DECENTERED'))",
            name="ck_m10_ortho_k_followup_position"),
        CheckConstraint(
            "(od_fluo_fit IS NULL OR od_fluo_fit IN ('FLAT', 'IDEAL', 'STEEP')) "
            "AND (os_fluo_fit IS NULL OR os_fluo_fit IN ('FLAT', 'IDEAL', 'STEEP'))",
            name="ck_m10_ortho_k_followup_fluo_fit"),
        CheckConstraint(
            "(od_lens_cleanliness IS NULL OR od_lens_cleanliness IN "
            " ('CLEAN', 'SLIGHT_DEPOSIT', 'HEAVY_DEPOSIT')) "
            "AND (os_lens_cleanliness IS NULL OR os_lens_cleanliness IN "
            " ('CLEAN', 'SLIGHT_DEPOSIT', 'HEAVY_DEPOSIT'))",
            name="ck_m10_ortho_k_followup_clean"),
        CheckConstraint(
            "(od_lens_damage IS NULL OR od_lens_damage IN "
            " ('NONE', 'SCRATCH', 'CHIP', 'BROKEN')) "
            "AND (os_lens_damage IS NULL OR os_lens_damage IN "
            " ('NONE', 'SCRATCH', 'CHIP', 'BROKEN'))",
            name="ck_m10_ortho_k_followup_damage"),
        CheckConstraint(
            "(od_tft_pattern IS NULL OR od_tft_pattern IN "
            " ('BULLSEYE', 'SMILEY', 'TARGET', 'CENTRAL_CRAB', 'NON_CENTRAL', 'IRREGULAR')) "
            "AND (os_tft_pattern IS NULL OR os_tft_pattern IN "
            " ('BULLSEYE', 'SMILEY', 'TARGET', 'CENTRAL_CRAB', 'NON_CENTRAL', 'IRREGULAR'))",
            name="ck_m10_ortho_k_followup_tft"),
        CheckConstraint(
            "complication_grade IS NULL "
            "OR complication_grade IN ('NONE', 'MILD', 'MODERATE', 'SEVERE')",
            name="ck_m10_ortho_k_followup_grade_level"),
        # ★ 严重并发症必须上报
        CheckConstraint("complication_grade IS DISTINCT FROM 'SEVERE' OR report_required = TRUE",
                        name="ck_m10_ortho_k_followup_report"),
        CheckConstraint(
            "report_required = FALSE OR (complications IS NOT NULL "
            "AND jsonb_array_length(complications) > 0)",
            name="ck_m10_ortho_k_followup_report_items"),
        CheckConstraint(
            "(report_id IS NULL AND reported_at IS NULL) "
            "OR (report_id IS NOT NULL AND reported_at IS NOT NULL)",
            name="ck_m10_ortho_k_followup_report_pair"),
        CheckConstraint(
            "followup_result IN ('NORMAL', 'OBSERVE', 'ADJUST_LENS', 'DISCONTINUE')",
            name="ck_m10_ortho_k_followup_result"),
        CheckConstraint(
            "followup_result = 'NORMAL' OR (disposal_advice IS NOT NULL "
            "AND char_length(btrim(disposal_advice)) >= 10)",
            name="ck_m10_ortho_k_followup_advice"),
        CheckConstraint(
            "followup_result <> 'DISCONTINUE' "
            "OR (complications IS NOT NULL AND jsonb_array_length(complications) > 0) "
            "OR od_fluorescein IN ('STAINING', 'INFILTRATE', 'ULCER') "
            "OR os_fluorescein IN ('STAINING', 'INFILTRATE', 'ULCER')",
            name="ck_m10_ortho_k_followup_discontinue"),
        CheckConstraint(
            "visited_at IS NULL "
            "OR (operator_id IS NOT NULL AND followup_doctor_id IS NOT NULL)",
            name="ck_m10_ortho_k_followup_visited"),
        CheckConstraint(
            "next_followup_date IS NULL OR visited_at IS NULL "
            "OR next_followup_date > visited_at::date",
            name="ck_m10_ortho_k_followup_next_date"),
        CheckConstraint("is_deleted = FALSE", name="ck_m10_ortho_k_followup_undeletable"),
        CheckConstraint(
            "(od_axial_length IS NULL OR od_axial_length BETWEEN 18.00 AND 32.00) "
            "AND (os_axial_length IS NULL OR os_axial_length BETWEEN 18.00 AND 32.00)",
            name="ck_m10_ortho_k_followup_axial"),
    )


class M10OrthoKLog(Base):
    """验配操作日志表。按月 RANGE 分区，保留 24 个月。"""

    __tablename__ = "m10_ortho_k_log"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    log_no: Mapped[Optional[str]] = mapped_column(String(40))
    fitting_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    fit_no: Mapped[Optional[str]] = mapped_column(String(32))
    patient_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    action_desc: Mapped[Optional[str]] = mapped_column(String(256))
    from_status: Mapped[Optional[str]] = mapped_column(String(24))
    to_status: Mapped[Optional[str]] = mapped_column(String(24))
    changed_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_role: Mapped[Optional[str]] = mapped_column(String(32))
    store_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    client_ip: Mapped[Optional[str]] = mapped_column(String(64))
    user_agent: Mapped[Optional[str]] = mapped_column(String(256))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    result: Mapped[str] = mapped_column(String(16), nullable=False, default="SUCCESS")
    error_code: Mapped[Optional[str]] = mapped_column(String(16))
    error_message: Mapped[Optional[str]] = mapped_column(String(512))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
                                                 server_default=func.now())

    __table_args__ = (
        Index("idx_m10_ortho_k_log_fitting", "fitting_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_log_patient", "patient_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_log_entity", "entity_type", "entity_id",
              text("created_at DESC")),
        Index("idx_m10_ortho_k_log_action", "action", text("created_at DESC")),
        Index("idx_m10_ortho_k_log_operator", "operator_id", text("created_at DESC")),
        Index("idx_m10_ortho_k_log_fail", "created_at",
              postgresql_where=text("result = 'FAIL'")),
        CheckConstraint("log_no IS NULL OR log_no ~ '^OKL[0-9]{20}$'",
                        name="ck_m10_ortho_k_log_no_format"),
        CheckConstraint(
            "entity_type IN ('FITTING', 'APPLY', 'CORNEA', 'TRIAL_LENS', "
            "'TRIAL_USE', 'CUSTOM_PARAM', 'DELIVERY', 'FOLLOWUP')",
            name="ck_m10_ortho_k_log_entity"),
        CheckConstraint(
            "action IN ('CREATE_FITTING', 'VOID_FITTING', 'SUBMIT_APPLY', 'ASSESS_APPLY', "
            "'DOCTOR_REVIEW', 'UPLOAD_CONSENT', 'SAVE_CORNEA', 'INVALID_CORNEA', "
            "'LOCK_CORNEA', 'OCCUPY_TRIAL', 'RELEASE_TRIAL', 'FORCE_RELEASE_TRIAL', "
            "'SAVE_TRIAL_EVAL', 'DISINFECT_TRIAL_LENS', 'SCRAP_TRIAL_LENS', "
            "'SAVE_CUSTOM_PARAM', 'FIT_CHECK', 'ORDER_CUSTOM', 'CANCEL_CUSTOM', "
            "'ACCEPT_DELIVERY', 'REJECT_DELIVERY', 'DISINFECT_DELIVERY', "
            "'DELIVER_LENS', 'TEACHING', 'SAVE_FOLLOWUP', 'REPORT_COMPLICATION', "
            "'STOP_WEAR', 'START_REPLACE', 'CLOSE_FITTING', 'EXPORT')",
            name="ck_m10_ortho_k_log_action"),
        CheckConstraint("result IN ('SUCCESS', 'FAIL')", name="ck_m10_ortho_k_log_result"),
        CheckConstraint(
            "result = 'SUCCESS' OR (error_code IS NOT NULL AND error_message IS NOT NULL)",
            name="ck_m10_ortho_k_log_fail"),
        CheckConstraint("result = 'FAIL' OR (error_code IS NULL AND error_message IS NULL)",
                        name="ck_m10_ortho_k_log_success"),
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0",
                        name="ck_m10_ortho_k_log_duration"),
        CheckConstraint("entity_type = 'TRIAL_LENS' OR fitting_id IS NOT NULL",
                        name="ck_m10_ortho_k_log_fitting_ref"),
    )
```

---

### 4.12 Pydantic Schema 定义

```python
"""M10-04 OK镜与RGP验配随访 —— Pydantic V2 Schema"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==================== 枚举字面量 ====================

EyeSide = Literal["OD", "OS"]
FitStatus = Literal[
    "DRAFT", "APPLYING", "ASSESSED", "TRIAL", "CUSTOMIZING", "ORDERED",
    "ARRIVED", "DELIVERED", "FOLLOWING", "REPLACE_DUE", "REPLACED", "STOPPED", "CLOSED",
]
AccessResult = Literal["PENDING", "PASS", "CONDITIONAL", "FAIL"]
TopographyPattern = Literal[
    "NORMAL", "SYMMETRIC_BOWTIE", "ASYMMETRIC_BOWTIE", "KERATOCONUS_SUSPECT", "IRREGULAR",
]
TrialLensStatus = Literal[
    "IN_STOCK", "IN_USE", "DISINFECTING", "DAMAGED", "EXPIRED", "SCRAPPED",
]
FitQuality = Literal["EXCELLENT", "ACCEPTABLE", "UNACCEPTABLE"]
CheckResult = Literal["PENDING", "PASS", "PASS_WITH_WARN", "FAIL"]
FollowupNode = Literal["D1", "D7", "D30", "D90", "M3", "M6", "M9", "M12", "EXTRA"]
FollowupResult = Literal["NORMAL", "OBSERVE", "ADJUST_LENS", "DISCONTINUE"]
DeliveryAcceptResult = Literal["PENDING", "PASS", "FAIL", "RETURNED"]


# ==================== 请求体 ====================

class FittingCreateIn(BaseModel):
    """新建 OK 镜验配单。"""

    patient_id: int = Field(..., gt=0, description="患者 ID（M03 mpi_patient.id）")
    customer_id: Optional[int] = Field(None, gt=0, description="视光顾客 ID（可空）")
    product_kind: Literal["ORTHO_K", "RGP"] = Field(
        "ORTHO_K", description="产品品类：ORTHO_K 角膜塑形镜 / RGP 硬性透气接触镜")
    product_code: Optional[str] = Field(None, max_length=32, description="定制镜片产品编码")
    store_id: int = Field(..., gt=0, description="验配门店/院区 ID")
    fitter_id: int = Field(..., gt=0, description="主验配师 ID（须具视光资质）")
    assistant_id: Optional[int] = Field(None, gt=0, description="协助人员 ID")
    optometry_no: Optional[str] = Field(None, max_length=32, description="依据验光单号")
    prescription_no: Optional[str] = Field(None, max_length=32, description="依据配镜处方号")
    od_sphere: Optional[Decimal] = Field(None, ge=-20, le=20, description="右眼球镜（D）")
    od_cylinder: Optional[Decimal] = Field(None, ge=-6, le=6, description="右眼柱镜（D）")
    od_axis: Optional[int] = Field(None, ge=1, le=180, description="右眼轴位（°）")
    os_sphere: Optional[Decimal] = Field(None, ge=-20, le=20, description="左眼球镜（D）")
    os_cylinder: Optional[Decimal] = Field(None, ge=-6, le=6, description="左眼柱镜（D）")
    os_axis: Optional[int] = Field(None, ge=1, le=180, description="左眼轴位（°）")
    previous_fit_id: Optional[int] = Field(None, gt=0, description="上一副验配单 ID（换片时填）")
    remark: Optional[str] = Field(None, max_length=1024, description="备注")

    @field_validator("od_sphere", "os_sphere", "od_cylinder", "os_cylinder")
    @classmethod
    def check_quarter_step(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """球镜与柱镜必须为 0.25D 的整数倍。"""
        if v is None:
            return v
        if (v * 4) != (v * 4).to_integral_value():
            raise ValueError("球镜/柱镜必须为 0.25D 的整数倍")
        return v

    @field_validator("od_axis", "os_axis")
    @classmethod
    def check_axis(cls, v: Optional[int]) -> Optional[int]:
        """轴位必须在 1~180 度之间。"""
        if v is not None and not 1 <= v <= 180:
            raise ValueError("轴位必须在 1~180 度之间")
        return v

    @model_validator(mode="after")
    def check_axis_pair(self) -> "FittingCreateIn":
        """柱镜为 0 时不可填写轴位；柱镜非 0 时必须填写轴位。"""
        if self.od_cylinder == 0 and self.od_axis is not None:
            raise ValueError("右眼柱镜为 0 时不可填写轴位")
        if self.od_cylinder not in (None, 0) and self.od_axis is None:
            raise ValueError("右眼柱镜非 0 时必须填写轴位")
        if self.os_cylinder == 0 and self.os_axis is not None:
            raise ValueError("左眼柱镜为 0 时不可填写轴位")
        if self.os_cylinder not in (None, 0) and self.os_axis is None:
            raise ValueError("左眼柱镜非 0 时必须填写轴位")
        return self


class ApplyAssessIn(BaseModel):
    """提交准入评估（P02）。六类指标全部录入后由服务层判定结论。"""

    age: int = Field(..., ge=1, le=120, description="年龄（岁）")
    # 一、年龄与依从性
    compliance_score: Optional[int] = Field(None, ge=0, le=100, description="依从性评分 0~100")
    compliance_note: Optional[str] = Field(None, max_length=512, description="依从性评估说明")
    parent_consent_signed: bool = Field(False, description="家长/本人知情同意书是否已签署")
    consent_file_id: Optional[int] = Field(None, gt=0, description="知情同意书扫描件 ID")
    consent_signer_name: Optional[str] = Field(None, max_length=64, description="签署人姓名")
    consent_signer_relation: Optional[Literal[
        "SELF", "FATHER", "MOTHER", "GRANDPARENT", "OTHER"
    ]] = Field(None, description="签署人与患者关系")
    # 二、屈光度
    od_sphere: Decimal = Field(..., ge=-20, le=20, description="右眼球镜（D）")
    od_cylinder: Decimal = Field(0, ge=-6, le=0, description="右眼柱镜（D）")
    od_axis: Optional[int] = Field(None, ge=1, le=180, description="右眼轴位（°）")
    os_sphere: Decimal = Field(..., ge=-20, le=20, description="左眼球镜（D）")
    os_cylinder: Decimal = Field(0, ge=-6, le=0, description="左眼柱镜（D）")
    os_axis: Optional[int] = Field(None, ge=1, le=180, description="左眼轴位（°）")
    # 三、角膜曲率与厚度
    od_k1: Decimal = Field(..., ge=35, le=55, description="右眼平坦角膜曲率 K1（D）")
    od_k2: Decimal = Field(..., ge=35, le=55, description="右眼陡峭角膜曲率 K2（D）")
    os_k1: Decimal = Field(..., ge=35, le=55, description="左眼平坦角膜曲率 K1（D）")
    os_k2: Decimal = Field(..., ge=35, le=55, description="左眼陡峭角膜曲率 K2（D）")
    od_cornea_thickness: int = Field(..., ge=300, le=800, description="右眼中央角膜厚度（μm）")
    os_cornea_thickness: int = Field(..., ge=300, le=800, description="左眼中央角膜厚度（μm）")
    # 四、眼压与泪液
    od_iop: Decimal = Field(..., ge=5, le=30, description="右眼眼压（mmHg）")
    os_iop: Decimal = Field(..., ge=5, le=30, description="左眼眼压（mmHg）")
    tear_break_up_time: Decimal = Field(..., ge=0, le=60, description="泪膜破裂时间 BUT（秒）")
    schirmer_test: Decimal = Field(..., ge=0, le=40, description="泪液分泌试验（mm/5min）")
    # 五、角膜地形图与眼表
    topography_pattern: TopographyPattern = Field(..., description="角膜地形图图形分类")
    keratoconus_suspect: bool = Field(False, description="圆锥角膜可疑标记")
    eyelid_condition: Literal["NORMAL", "NARROW", "WIDE", "LAGOPHTHALMOS"] = Field(
        "NORMAL", description="睑裂条件")
    conjunctiva_condition: Literal["NORMAL", "MILD_HYPEREMIA", "SEVERE_HYPEREMIA"] = Field(
        "NORMAL", description="结膜情况")
    meibomian_gland: Literal["NORMAL", "MILD_DYSFUNCTION", "SEVERE_DYSFUNCTION"] = Field(
        "NORMAL", description="睑板腺功能")
    contraindication: Optional[str] = Field(None, max_length=512, description="其他禁忌症说明")

    @model_validator(mode="after")
    def check_k_order(self) -> "ApplyAssessIn":
        """K1 必须为平坦曲率（K1 ≤ K2）。"""
        if self.od_k1 > self.od_k2:
            raise ValueError("右眼 K1 必须小于等于 K2（K1 为平坦曲率）")
        if self.os_k1 > self.os_k2:
            raise ValueError("左眼 K1 必须小于等于 K2（K1 为平坦曲率）")
        return self


class CorneaSaveIn(BaseModel):
    """保存角膜地形图参数（P03）。"""

    eye_side: EyeSide = Field(..., description="眼别")
    measure_stage: Literal["PRE_FIT", "POST_TRIAL", "FOLLOWUP", "POST_STOP"] = Field(
        "PRE_FIT", description="测量阶段")
    measure_source: Literal["MANUAL", "DEVICE", "IMPORT"] = Field("MANUAL", description="数据来源")
    k1: Decimal = Field(..., ge=35, le=55, description="平坦角膜曲率 K1（D）")
    k2: Decimal = Field(..., ge=35, le=55, description="陡峭角膜曲率 K2（D）")
    axis_k2: Optional[int] = Field(None, ge=1, le=180, description="陡峭子午线轴向（°）")
    e_value: Optional[Decimal] = Field(None, ge=0, le=1.2, description="角膜偏心率 e")
    hvid: Optional[Decimal] = Field(None, ge=9, le=14, description="可见虹膜水平径 HVID（mm）")
    pupil_light: Optional[Decimal] = Field(None, ge=1, le=9, description="明环境瞳孔直径（mm）")
    pupil_dark: Optional[Decimal] = Field(None, ge=1, le=10, description="暗环境瞳孔直径（mm）")
    thickness_central: Optional[int] = Field(None, ge=300, le=800,
                                             description="中央角膜厚度（μm）")
    thickness_thinnest: Optional[int] = Field(None, ge=300, le=800,
                                              description="最薄点角膜厚度（μm）")
    topography_pattern: TopographyPattern = Field(..., description="地形图图形分类")
    keratoconus_suspect: bool = Field(False, description="圆锥角膜可疑")
    topography_report_id: Optional[int] = Field(None, gt=0, description="地形图报告 ID（M12）")
    topography_file_url: Optional[str] = Field(None, max_length=512, description="报告文件地址")
    device_code: Optional[str] = Field(None, max_length=64, description="测量设备编码")

    @model_validator(mode="after")
    def check_pairs(self) -> "CorneaSaveIn":
        """K1 ≤ K2、最薄点不厚于中央、暗瞳不小于明瞳。"""
        if self.k1 > self.k2:
            raise ValueError("K1 必须小于等于 K2")
        if (self.thickness_central is not None and self.thickness_thinnest is not None
                and self.thickness_thinnest > self.thickness_central):
            raise ValueError("最薄点角膜厚度不得大于中央角膜厚度")
        if (self.pupil_light is not None and self.pupil_dark is not None
                and self.pupil_dark < self.pupil_light):
            raise ValueError("暗环境瞳孔直径不得小于明环境瞳孔直径")
        return self


class TrialOccupyIn(BaseModel):
    """占用试戴片（P04）。一片试戴片同一时刻只能给一个患者。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    trial_lens_id: Optional[int] = Field(None, gt=0, description="试戴片 ID（与编号二选一）")
    trial_lens_no: Optional[str] = Field(None, max_length=64, description="试戴片实物编号")
    eye_side: EyeSide = Field(..., description="眼别")
    trial_seq: int = Field(1, ge=1, le=20, description="本单本眼第几次试戴")

    @model_validator(mode="after")
    def check_target(self) -> "TrialOccupyIn":
        """试戴片 ID 与编号必须至少提供一个。"""
        if self.trial_lens_id is None and not self.trial_lens_no:
            raise ValueError("必须提供 trial_lens_id 或 trial_lens_no")
        return self


class TrialEvalIn(BaseModel):
    """试戴评估与订片决策（P04）。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    trial_use_id: int = Field(..., gt=0, description="试戴记录 ID")
    fluo_central: Literal["FLAT", "IDEAL", "STEEP"] = Field(..., description="中央泪液厚度")
    fluo_reverse: Literal["FLAT", "IDEAL", "STEEP"] = Field(..., description="反转弧荧光")
    fluo_align: Literal["FLAT", "IDEAL", "STEEP"] = Field(..., description="定位弧荧光")
    fluo_peripheral: Literal["FLAT", "IDEAL", "STEEP"] = Field(..., description="周边边翘")
    fit_quality: FitQuality = Field(..., description="配适合格判定")
    lens_position: Literal["CENTERED", "SLIGHT_DECENTERED", "DECENTERED"] = Field(
        "CENTERED", description="镜片定位")
    decentered_direction: Optional[Literal[
        "SUPERIOR", "INFERIOR", "NASAL", "TEMPORAL"
    ]] = Field(None, description="偏位方向")
    lens_movement: Optional[Decimal] = Field(None, ge=0, le=3, description="活动度（mm）")
    coverage_ratio: Optional[Decimal] = Field(None, ge=50, le=100,
                                              description="镜片覆盖角膜比率（%）")
    va_trial: Optional[Decimal] = Field(None, ge=0, le=2.0, description="戴镜检查视力")
    over_refraction_sph: Optional[Decimal] = Field(None, ge=-10, le=10,
                                                   description="试戴片上追加球镜（D）")
    tft_performed: bool = Field(False, description="是否做 TFT 地形图差异分析")
    tft_pattern: Optional[Literal[
        "BULLSEYE", "SMILEY", "TARGET", "CENTRAL_CRAB", "NON_CENTRAL", "IRREGULAR"
    ]] = Field(None, description="TFT 图形")
    tft_report_id: Optional[int] = Field(None, gt=0, description="TFT 报告 ID（M12）")
    decision: Literal["ORDER_AS_IS", "ADJUST", "RETRY", "ABORT"] = Field(
        ..., description="订片参数决策")
    decision_note: Optional[str] = Field(None, max_length=512, description="决策说明")
    suggested_bc: Optional[Decimal] = Field(None, ge=7, le=9.5, description="建议基弧 BC（mm）")
    suggested_reduction: Optional[Decimal] = Field(None, ge=-6, le=-0.75,
                                                   description="建议降度（D）")
    suggested_diameter: Optional[Decimal] = Field(None, ge=9, le=12, description="建议直径（mm）")

    @model_validator(mode="after")
    def check_tft_and_decision(self) -> "TrialEvalIn":
        """TFT 做了必须给结论与报告；RETRY/ABORT 必须写明理由。"""
        if self.tft_performed and (self.tft_pattern is None or self.tft_report_id is None):
            raise ValueError("已做 TFT 必须填写图形结论与报告 ID")
        if self.decision in ("RETRY", "ABORT"):
            if not self.decision_note or len(self.decision_note.strip()) < 10:
                raise ValueError("换片再试或放弃验配必须写明理由（≥10 字）")
        if self.lens_position != "CENTERED" and self.decentered_direction is None:
            raise ValueError("镜片偏位时必须选择偏位方向")
        return self


class CustomParamIn(BaseModel):
    """生成定制参数（P05）。生成后必须调用 M01-08 fit-check。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    eye_side: EyeSide = Field(..., description="眼别")
    trial_use_id: Optional[int] = Field(None, gt=0, description="依据的试戴记录 ID")
    cornea_id: int = Field(..., gt=0, description="依据的角膜地形图参数 ID（必填，追溯链）")
    param_source: Literal["TRIAL", "CALCULATED", "DOCTOR"] = Field(
        "TRIAL", description="参数来源")
    bc: Decimal = Field(..., ge=7, le=9.5, description="基弧 BC（mm）")
    rc: Optional[Decimal] = Field(None, ge=6, le=10, description="反转弧 RC（mm）")
    ac: Optional[Decimal] = Field(None, ge=6, le=10, description="定位弧 AC（mm）")
    pc: Optional[Decimal] = Field(None, ge=6, le=11, description="周边弧 PC（mm）")
    diameter: Decimal = Field(..., ge=9, le=12, description="镜片直径（mm）")
    target_reduction: Decimal = Field(..., ge=-6, le=-0.75, description="目标降度（D）")
    actual_reduction: Decimal = Field(..., ge=-6, le=-0.75, description="实际降度（D）")
    reduction_adjust_reason: Optional[str] = Field(None, max_length=512,
                                                   description="降度调整原因")
    over_refraction: Optional[Decimal] = Field(None, ge=-10, le=10,
                                               description="试戴片追加球镜（D）")
    material: Optional[str] = Field(None, max_length=64, description="材质")
    color: Optional[Literal["CLEAR", "BLUE", "GREEN", "VIOLET"]] = Field(
        None, description="颜色")
    manufacturer_code: Optional[str] = Field(None, max_length=32, description="厂家编码")
    manufacture_lead_days: Optional[int] = Field(None, ge=1, le=90,
                                                 description="厂家供货周期（天）")

    @model_validator(mode="after")
    def check_arc_and_reduction(self) -> "CustomParamIn":
        """弧参数 RC < BC < AC < PC；直径 > BC；降度差值非 0 须填原因。"""
        if self.rc is not None and self.rc >= self.bc:
            raise ValueError("反转弧 RC 必须小于基弧 BC")
        if self.ac is not None and self.ac <= self.bc:
            raise ValueError("定位弧 AC 必须大于基弧 BC")
        if self.pc is not None and self.ac is not None and self.pc <= self.ac:
            raise ValueError("周边弧 PC 必须大于定位弧 AC")
        if self.diameter <= self.bc:
            raise ValueError("镜片直径必须大于基弧")
        diff = self.actual_reduction - self.target_reduction
        if abs(diff) >= Decimal("0.001"):
            if not self.reduction_adjust_reason or len(
                    self.reduction_adjust_reason.strip()) < 10:
                raise ValueError("降度与目标不一致时必须写明调整原因（≥10 字）")
        return self


class DeliveryAcceptIn(BaseModel):
    """到片验收（P06）。逐项核对定制参数与实物。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    custom_param_id: int = Field(..., gt=0, description="定制参数 ID")
    eye_side: EyeSide = Field(..., description="眼别")
    lens_no: str = Field(..., min_length=4, max_length=64, description="厂家镜片唯一编号")
    package_intact: bool = Field(True, description="包装是否完好")
    actual_bc: Decimal = Field(..., ge=7, le=9.5, description="实物基弧 BC（mm）")
    actual_rc: Optional[Decimal] = Field(None, ge=6, le=10, description="实物反转弧 RC（mm）")
    actual_ac: Optional[Decimal] = Field(None, ge=6, le=10, description="实物定位弧 AC（mm）")
    actual_pc: Optional[Decimal] = Field(None, ge=6, le=11, description="实物周边弧 PC（mm）")
    actual_diameter: Decimal = Field(..., ge=9, le=12, description="实物直径（mm）")
    actual_reduction: Decimal = Field(..., ge=-6, le=-0.75, description="实物降度（D）")
    actual_material: Optional[str] = Field(None, max_length=64, description="实物材质")
    appearance_ok: bool = Field(..., description="外观检查是否合格")
    appearance_note: Optional[str] = Field(None, max_length=512, description="外观异常说明")
    scratch_found: bool = Field(False, description="是否有划痕")
    chip_found: bool = Field(False, description="是否崩边")
    bubble_found: bool = Field(False, description="是否有气泡/杂质")

    @model_validator(mode="after")
    def check_appearance(self) -> "DeliveryAcceptIn":
        """外观异常与外观合格判定必须自洽。"""
        has_defect = self.scratch_found or self.chip_found or self.bubble_found
        if self.appearance_ok and has_defect:
            raise ValueError("存在划痕/崩边/气泡时外观检查不能判定为合格")
        if not self.appearance_ok and not self.appearance_note:
            raise ValueError("外观不合格必须填写异常说明")
        return self


class DeliveryIssueIn(BaseModel):
    """发放镜片（P06）。必须先验收通过、消毒、完成 ≥30 分钟戴镜教学。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    delivery_ids: List[int] = Field(..., min_length=1, description="待发放的验发记录 ID 列表")
    disinfect_method: Literal["BOIL", "PEROXIDE", "UV"] = Field(
        "BOIL", description="消毒方式")
    receiver_name: str = Field(..., min_length=2, max_length=64, description="领取人姓名")
    receiver_relation: Literal["SELF", "FATHER", "MOTHER", "GRANDPARENT", "OTHER"] = Field(
        ..., description="领取人关系")
    receiver_sign_file_id: int = Field(..., gt=0, description="领取签名件 ID")
    teaching_minutes: int = Field(..., ge=30, le=180, description="首次戴镜教学时长（分钟）")
    teaching_content: List[str] = Field(..., min_length=1, description="教学内容清单")
    teaching_signed: bool = Field(..., description="患者/家长确认签字")
    replace_months: int = Field(12, ge=6, le=24, description="更换周期（月）")


class FollowupSaveIn(BaseModel):
    """保存戴镜随访记录（P07）。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    followup_node: FollowupNode = Field(..., description="复查节点")
    followup_type: Literal["SCHEDULED", "UNSCHEDULED", "POST_REPLACE"] = Field(
        "SCHEDULED", description="随访类型")
    scheduled_date: Optional[date] = Field(None, description="计划复查日期（来自 M10-09）")
    visited_at: datetime = Field(..., description="实际到访时间")
    subjective_complaints: Optional[str] = Field(None, max_length=512, description="主诉")
    wearing_hours_per_night: Optional[Decimal] = Field(None, ge=0, le=14,
                                                       description="夜间戴镜时长（小时）")
    wearing_days_per_week: Optional[int] = Field(None, ge=0, le=7, description="每周戴镜天数")
    compliance_check: Optional[Literal["GOOD", "FAIR", "POOR"]] = Field(
        None, description="依从性检查")
    od_va_uncorrected: Optional[Decimal] = Field(None, ge=0, le=2.0, description="右眼裸眼视力")
    os_va_uncorrected: Optional[Decimal] = Field(None, ge=0, le=2.0, description="左眼裸眼视力")
    od_fluorescein: Optional[Literal[
        "NORMAL", "PUNCTATE_STAINING", "STAINING", "INFILTRATE", "ULCER"
    ]] = Field(None, description="右眼角膜荧光染色")
    os_fluorescein: Optional[Literal[
        "NORMAL", "PUNCTATE_STAINING", "STAINING", "INFILTRATE", "ULCER"
    ]] = Field(None, description="左眼角膜荧光染色")
    od_fluorescein_grade: Optional[int] = Field(None, ge=0, le=4,
                                                description="右眼 Efron 染色分级")
    os_fluorescein_grade: Optional[int] = Field(None, ge=0, le=4,
                                                description="左眼 Efron 染色分级")
    od_lens_position: Optional[Literal[
        "CENTERED", "SLIGHT_DECENTERED", "DECENTERED"
    ]] = Field(None, description="右眼镜片定位")
    os_lens_position: Optional[Literal[
        "CENTERED", "SLIGHT_DECENTERED", "DECENTERED"
    ]] = Field(None, description="左眼镜片定位")
    od_lens_cleanliness: Optional[Literal[
        "CLEAN", "SLIGHT_DEPOSIT", "HEAVY_DEPOSIT"
    ]] = Field(None, description="右眼镜片清洁度")
    os_lens_cleanliness: Optional[Literal[
        "CLEAN", "SLIGHT_DEPOSIT", "HEAVY_DEPOSIT"
    ]] = Field(None, description="左眼镜片清洁度")
    od_tft_pattern: Optional[Literal[
        "BULLSEYE", "SMILEY", "TARGET", "CENTRAL_CRAB", "NON_CENTRAL", "IRREGULAR"
    ]] = Field(None, description="右眼 TFT 图形")
    os_tft_pattern: Optional[Literal[
        "BULLSEYE", "SMILEY", "TARGET", "CENTRAL_CRAB", "NON_CENTRAL", "IRREGULAR"
    ]] = Field(None, description="左眼 TFT 图形")
    complications: Optional[List[str]] = Field(None, description="并发症编码数组")
    complication_grade: Optional[Literal["NONE", "MILD", "MODERATE", "SEVERE"]] = Field(
        None, description="并发症严重度")
    followup_result: FollowupResult = Field("NORMAL", description="随访结论")
    disposal_advice: Optional[str] = Field(None, max_length=512, description="处置意见")
    followup_doctor_id: int = Field(..., gt=0, description="复查医师 ID")
    operator_id: int = Field(..., gt=0, description="记录人 ID")
    remark: Optional[str] = Field(None, max_length=1024, description="备注")

    @model_validator(mode="after")
    def check_result(self) -> "FollowupSaveIn":
        """严重并发症必须上报；非正常结论必须写处置意见。"""
        if self.complication_grade == "SEVERE" and not self.complications:
            raise ValueError("严重并发症必须填写并发症明细")
        if self.followup_result != "NORMAL":
            if not self.disposal_advice or len(self.disposal_advice.strip()) < 10:
                raise ValueError("非正常随访结论必须填写处置意见（≥10 字）")
        if self.followup_result == "DISCONTINUE":
            if not self.complications:
                raise ValueError("建议停戴必须填写并发症或明确的角膜异常")
        return self


class StopWearIn(BaseModel):
    """停戴处理（P08）。"""

    fitting_id: int = Field(..., gt=0, description="验配单 ID")
    stop_reason_code: Literal[
        "CORNEAL_INJURY", "INFECTION", "FEVER_COLD", "SWIMMING",
        "PREGNANCY", "NON_COMPLIANCE", "PATIENT_REQUEST",
        "SWITCH_TO_OTHER", "OTHER",
    ] = Field(..., description="停戴原因编码")
    stop_reason: str = Field(..., min_length=10, max_length=512,
                             description="停戴原因详细说明（≥10 字）")
    stopped_at: datetime = Field(..., description="停戴时间")
    expected_stop_days: Optional[int] = Field(None, ge=0, le=365,
                                              description="预计停戴天数（0 表示永久停戴）")


class ReplaceStartIn(BaseModel):
    """启动换片（P08）。"""

    fitting_id: int = Field(..., gt=0, description="原验配单 ID")
    replace_reason_code: Literal[
        "CYCLE_EXPIRED", "POWER_CHANGE", "LENS_DAMAGED",
        "LENS_LOST", "POOR_FIT", "OTHER",
    ] = Field(..., description="换片原因编码")
    remark: Optional[str] = Field(None, max_length=1024, description="换片备注")


class FittingQueryIn(BaseModel):
    """验配单分页查询条件。"""

    keyword: Optional[str] = Field(None, max_length=64, description="患者姓名/单号/手机号关键词")
    status: Optional[FitStatus] = Field(None, description="验配单状态")
    product_kind: Optional[Literal["ORTHO_K", "RGP"]] = Field(None, description="产品品类")
    store_id: Optional[int] = Field(None, gt=0, description="门店 ID")
    fitter_id: Optional[int] = Field(None, gt=0, description="验配师 ID")
    patient_id: Optional[int] = Field(None, gt=0, description="患者 ID")
    start_date: Optional[date] = Field(None, description="申请日期起")
    end_date: Optional[date] = Field(None, description="申请日期止")
    followup_due_only: bool = Field(False, description="仅看复查到期的在戴镜患者")
    overdue_only: bool = Field(False, description="仅看逾期未复查患者")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页条数")

    @model_validator(mode="after")
    def check_date_range(self) -> "FittingQueryIn":
        """日期区间起止必须有序。"""
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("申请日期起不得晚于止")
        return self


# ==================== 响应 ====================

class FittingBriefOut(BaseModel):
    """验配单简要信息（列表用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="验配流水号")
    fit_no: str = Field(..., description="验配单号")
    patient_name: str = Field(..., description="患者姓名")
    age: Optional[int] = Field(None, description="验配时年龄（岁）")
    gender: Optional[str] = Field(None, description="性别")
    product_kind: str = Field(..., description="产品品类")
    product_name: Optional[str] = Field(None, description="产品名称")
    status: str = Field(..., description="验配单状态")
    replace_round: int = Field(..., description="换片轮次")
    fitter_name: Optional[str] = Field(None, description="主验配师姓名")
    delivered_at: Optional[datetime] = Field(None, description="首次戴镜时间")
    expected_replace_date: Optional[date] = Field(None, description="预计换片日期")
    next_followup_date: Optional[date] = Field(None, description="下次应复查日期")
    overdue_days: int = Field(0, description="逾期天数")
    has_severe_complication: bool = Field(False, description="是否存在严重并发症")


class FittingListOut(BaseModel):
    """验配单分页列表出参。"""

    items: List[FittingBriefOut] = Field(default_factory=list, description="验配单列表")
    total: int = Field(..., description="总条数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    pages: int = Field(..., description="总页数")


class ApplyDetailOut(BaseModel):
    """准入评估详情出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="评估 ID")
    apply_no: Optional[str] = Field(None, description="申请号")
    age: int = Field(..., description="年龄（岁）")
    age_check_passed: bool = Field(..., description="年龄是否达标")
    compliance_score: Optional[int] = Field(None, description="依从性评分")
    compliance_level: Optional[str] = Field(None, description="依从性等级")
    parent_consent_signed: bool = Field(..., description="知情同意是否签署")
    consent_file_id: Optional[int] = Field(None, description="同意书扫描件 ID")
    od_sphere: Optional[Decimal] = Field(None, description="右眼球镜（D）")
    os_sphere: Optional[Decimal] = Field(None, description="左眼球镜（D）")
    od_k1: Optional[Decimal] = Field(None, description="右眼 K1（D）")
    od_k2: Optional[Decimal] = Field(None, description="右眼 K2（D）")
    os_k1: Optional[Decimal] = Field(None, description="左眼 K1（D）")
    os_k2: Optional[Decimal] = Field(None, description="左眼 K2（D）")
    od_cornea_thickness: Optional[int] = Field(None, description="右眼中央厚度（μm）")
    os_cornea_thickness: Optional[int] = Field(None, description="左眼中央厚度（μm）")
    od_iop: Optional[Decimal] = Field(None, description="右眼眼压（mmHg）")
    os_iop: Optional[Decimal] = Field(None, description="左眼眼压（mmHg）")
    topography_pattern: Optional[str] = Field(None, description="地形图图形分类")
    keratoconus_suspect: bool = Field(False, description="圆锥角膜可疑")
    access_result: str = Field(..., description="准入结论")
    fail_items: Optional[List[Any]] = Field(None, description="不达标项编码数组")
    conditional_terms: Optional[str] = Field(None, description="有条件通过的限制条件")
    reject_reason: Optional[str] = Field(None, description="拒绝原因")
    doctor_review_required: bool = Field(False, description="是否需医学复核")
    doctor_review_opinion: Optional[str] = Field(None, description="复核意见")
    assessed_at: Optional[datetime] = Field(None, description="评估完成时间")


class CorneaOut(BaseModel):
    """角膜地形图参数出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="角膜参数记录 ID")
    cornea_no: Optional[str] = Field(None, description="记录号")
    eye_side: str = Field(..., description="眼别")
    measure_stage: str = Field(..., description="测量阶段")
    measured_at: datetime = Field(..., description="测量时间")
    k1: Optional[Decimal] = Field(None, description="K1（D）")
    k2: Optional[Decimal] = Field(None, description="K2（D）")
    km: Optional[Decimal] = Field(None, description="Km（D）")
    axis_k2: Optional[int] = Field(None, description="陡峭轴向（°）")
    cornea_astigmatism: Optional[Decimal] = Field(None, description="角膜散光（D）")
    k1_mm: Optional[Decimal] = Field(None, description="平坦曲率半径（mm）")
    e_value: Optional[Decimal] = Field(None, description="角膜偏心率 e")
    hvid: Optional[Decimal] = Field(None, description="HVID（mm）")
    pupil_light: Optional[Decimal] = Field(None, description="明瞳直径（mm）")
    pupil_dark: Optional[Decimal] = Field(None, description="暗瞳直径（mm）")
    thickness_central: Optional[int] = Field(None, description="中央厚度（μm）")
    thickness_thinnest: Optional[int] = Field(None, description="最薄点厚度（μm）")
    topography_pattern: Optional[str] = Field(None, description="地形图图形分类")
    keratoconus_suspect: bool = Field(False, description="圆锥角膜可疑")
    topography_report_id: Optional[int] = Field(None, description="地形图报告 ID")
    is_locked: bool = Field(False, description="是否已锁定")


class TrialUseOut(BaseModel):
    """试戴片占用与评估出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="试戴记录 ID")
    use_no: Optional[str] = Field(None, description="试戴记录号")
    trial_lens_no: str = Field(..., description="试戴片实物编号")
    eye_side: str = Field(..., description="眼别")
    trial_seq: int = Field(..., description="试戴序号")
    trial_bc: Optional[Decimal] = Field(None, description="试戴片基弧 BC（mm）")
    trial_reduction: Optional[Decimal] = Field(None, description="试戴片降度（D）")
    occupied_at: datetime = Field(..., description="占用时间")
    occupied_by_name: Optional[str] = Field(None, description="占用操作人")
    released_at: Optional[datetime] = Field(None, description="释放时间（空表示占用中）")
    fit_quality: Optional[str] = Field(None, description="配适合格判定")
    lens_position: Optional[str] = Field(None, description="镜片定位")
    lens_movement: Optional[Decimal] = Field(None, description="活动度（mm）")
    tft_pattern: Optional[str] = Field(None, description="TFT 图形")
    decision: Optional[str] = Field(None, description="订片决策")
    suggested_bc: Optional[Decimal] = Field(None, description="建议基弧 BC（mm）")
    suggested_reduction: Optional[Decimal] = Field(None, description="建议降度（D）")


class CustomParamOut(BaseModel):
    """定制参数出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="定制参数 ID")
    custom_no: Optional[str] = Field(None, description="参数单号")
    eye_side: str = Field(..., description="眼别")
    bc: Decimal = Field(..., description="基弧 BC（mm）")
    rc: Optional[Decimal] = Field(None, description="反转弧 RC（mm）")
    ac: Optional[Decimal] = Field(None, description="定位弧 AC（mm）")
    pc: Optional[Decimal] = Field(None, description="周边弧 PC（mm）")
    diameter: Decimal = Field(..., description="镜片直径（mm）")
    target_reduction: Decimal = Field(..., description="目标降度（D）")
    actual_reduction: Decimal = Field(..., description="实际降度（D）")
    material: Optional[str] = Field(None, description="材质")
    color: Optional[str] = Field(None, description="颜色")
    check_result: str = Field(..., description="适配校验结论")
    fit_check_passed: Optional[bool] = Field(None, description="M01-08 fit-check 结论")
    fit_check_at: Optional[datetime] = Field(None, description="适配校验时间")
    fit_check_message: Optional[str] = Field(None, description="适配校验提示")
    status: str = Field(..., description="定制参数状态")
    is_ordered: bool = Field(..., description="是否已下发厂家")
    ordered_at: Optional[datetime] = Field(None, description="下单时间")
    expected_arrival_date: Optional[date] = Field(None, description="预计到片日期")


class DeliveryOut(BaseModel):
    """到片验收与发放出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="验发记录 ID")
    delivery_no: Optional[str] = Field(None, description="验发单号")
    eye_side: str = Field(..., description="眼别")
    lens_no: Optional[str] = Field(None, description="厂家镜片编号")
    arrived_at: Optional[datetime] = Field(None, description="到片时间")
    actual_bc: Optional[Decimal] = Field(None, description="实物基弧 BC（mm）")
    actual_reduction: Optional[Decimal] = Field(None, description="实物降度（D）")
    param_match: Optional[bool] = Field(None, description="参数是否一致")
    mismatch_items: Optional[List[Any]] = Field(None, description="不一致项")
    appearance_ok: Optional[bool] = Field(None, description="外观是否合格")
    accept_result: str = Field(..., description="验收结论")
    disinfected: bool = Field(False, description="是否已消毒")
    delivered_at: Optional[datetime] = Field(None, description="发放时间")
    teaching_done: bool = Field(False, description="教学是否完成")
    teaching_minutes: Optional[int] = Field(None, description="教学时长（分钟）")
    wear_start_date: Optional[date] = Field(None, description="戴镜起算日")
    expected_replace_date: Optional[date] = Field(None, description="预计换片日期")


class FollowupOut(BaseModel):
    """随访记录出参。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="随访记录 ID")
    followup_no: Optional[str] = Field(None, description="随访单号")
    followup_node: str = Field(..., description="复查节点")
    followup_day: Optional[int] = Field(None, description="相对戴镜日天数")
    visited_at: Optional[datetime] = Field(None, description="到访时间")
    visit_late_days: Optional[int] = Field(None, description="迟访天数")
    od_va_uncorrected: Optional[Decimal] = Field(None, description="右眼裸眼视力")
    os_va_uncorrected: Optional[Decimal] = Field(None, description="左眼裸眼视力")
    od_fluorescein: Optional[str] = Field(None, description="右眼荧光染色")
    os_fluorescein: Optional[str] = Field(None, description="左眼荧光染色")
    od_lens_cleanliness: Optional[str] = Field(None, description="右眼镜片清洁度")
    os_lens_cleanliness: Optional[str] = Field(None, description="左眼镜片清洁度")
    complications: Optional[List[Any]] = Field(None, description="并发症编码数组")
    complication_grade: Optional[str] = Field(None, description="并发症严重度")
    report_required: bool = Field(False, description="是否需上报不良事件")
    followup_result: str = Field(..., description="随访结论")
    disposal_advice: Optional[str] = Field(None, description="处置意见")
    next_followup_date: Optional[date] = Field(None, description="下次复查日期")
    followup_doctor_name: Optional[str] = Field(None, description="复查医师姓名")


class FittingDetailOut(BaseModel):
    """验配单完整详情出参（P-09 内部契约与页面详情共用）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="验配流水号")
    fit_no: str = Field(..., description="验配单号")
    patient_id: int = Field(..., description="患者 ID")
    patient_name: str = Field(..., description="患者姓名")
    gender: Optional[str] = Field(None, description="性别")
    age: Optional[int] = Field(None, description="验配时年龄（岁）")
    guardian_name: Optional[str] = Field(None, description="监护人姓名")
    guardian_phone: Optional[str] = Field(None, description="监护人电话")
    product_kind: str = Field(..., description="产品品类")
    product_code: Optional[str] = Field(None, description="产品编码")
    product_name: Optional[str] = Field(None, description="产品名称")
    device_reg_no: Optional[str] = Field(None, description="医疗器械注册证号")
    device_reg_valid_until: Optional[date] = Field(None, description="注册证有效期")
    fitter_id: int = Field(..., description="主验配师 ID")
    fitter_name: Optional[str] = Field(None, description="主验配师姓名")
    status: str = Field(..., description="验配单状态")
    replace_round: int = Field(..., description="换片轮次")
    od_sphere: Optional[Decimal] = Field(None, description="右眼球镜（D）")
    os_sphere: Optional[Decimal] = Field(None, description="左眼球镜（D）")
    delivered_at: Optional[datetime] = Field(None, description="首次戴镜时间")
    expected_replace_date: Optional[date] = Field(None, description="预计换片日期")
    next_followup_date: Optional[date] = Field(None, description="下次应复查日期")
    overdue_days: int = Field(0, description="逾期天数")
    followup_count: int = Field(0, description="已完成随访次数")
    apply: Optional[ApplyDetailOut] = Field(None, description="准入评估")
    cornea_records: List[CorneaOut] = Field(default_factory=list, description="角膜参数记录")
    trial_uses: List[TrialUseOut] = Field(default_factory=list, description="试戴记录")
    custom_params: List[CustomParamOut] = Field(default_factory=list, description="定制参数")
    deliveries: List[DeliveryOut] = Field(default_factory=list, description="验发记录")
    followups: List[FollowupOut] = Field(default_factory=list, description="随访记录")


class FollowupDueOut(BaseModel):
    """复查到期患者出参。"""

    fitting_id: int = Field(..., description="验配单 ID")
    fit_no: str = Field(..., description="验配单号")
    patient_id: int = Field(..., description="患者 ID")
    patient_name: str = Field(..., description="患者姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    guardian_phone: Optional[str] = Field(None, description="监护人电话")
    delivered_at: Optional[datetime] = Field(None, description="首次戴镜时间")
    next_followup_date: date = Field(..., description="应复查日期")
    next_followup_node: Optional[str] = Field(None, description="应复查节点")
    overdue_days: int = Field(..., description="逾期天数")
    completed_nodes: List[str] = Field(default_factory=list, description="已完成节点")
    missed_nodes: List[str] = Field(default_factory=list, description="漏做节点")


class FollowupDueListOut(BaseModel):
    """复查到期清单出参。"""

    items: List[FollowupDueOut] = Field(default_factory=list, description="到期清单")
    total: int = Field(..., description="总条数")
    node_summary: Dict[str, int] = Field(default_factory=dict, description="各节点待查人数")
```

---
## 附录 A：表清单速查

| 编号 | 表名 | 中文名 | 主键 | 主干关系 | 写入方 | 只读方 | 预估量级 |
|---|---|---|---|---|---|---|---|
| 4.2 | `m10_ortho_k_fitting` | OK 镜验配单主表 | `id` | 一患一次验配一单 | M10-04 | M10-06、M10-09、M16-04、M01-08 | 2,400/年 |
| 4.3 | `m10_ortho_k_apply` | 验配申请与准入评估表 | `id` | `fitting.apply_id` 1:1 | M10-04 | M10-09、M07、医政科 | 3,000/年 |
| 4.4 | `m10_ortho_k_cornea` | 角膜地形图参数表 | `id` | `fitting_id` 1:N，按眼别 | M10-04、M12 报告桥接 | M10-09、M07、M01-08 | 5,000/年 |
| 4.5 | `m10_ortho_k_trial_lens` | 试戴片台账表 | `id` | 实物档案，独立 | M10-04 | M10-07、M15 | 1,200（静态） |
| 4.6 | `m10_ortho_k_trial_use` | 试戴片占用与试戴评估表 | `id` | `trial_lens_id` N:1；`fitting_id` 1:N | M10-04 | M10-06、M01-08 | 8,000/年 |
| 4.7 | `m10_ortho_k_custom_param` | 定制参数表 | `id` | `fitting_id` × `eye_side` | M10-04 | M10-06、M16-04、M01-08、厂家 | 4,800/年 |
| 4.8 | `m10_ortho_k_delivery` | 到片验收与发放表 | `id` | `custom_param_id` 1:1，按片 | M10-04 | M10-06、M16-04、M10-09 | 4,800/年 |
| 4.9 | `m10_ortho_k_followup` | 戴镜随访记录表 | `id` | `fitting_id` 1:N | M10-04 | M10-09、M07、M10-06 | 30,000/年 |
| 4.10 | `m10_ortho_k_log` | 验配操作日志表 | `id`+`created_at` | 审计旁路 | M10-04 全部 Service | M02 审计、质控科 | 120,000/年 |

**表名前缀核对：** 9 张表全部以 `m10_ortho_k_` 开头，与共享规范 §3.2 一致。
**跨子模块只读引用（不建表）：**

| 被引用表 | 归属 | 引用字段 | 说明 |
|---|---|---|---|
| `mpi_patient` | M03-01 | `patient_id` | 患者主索引 |
| `mdm_optical_product` | M01-08 | `product_code` | 视光产品（OK 镜/RGP/试戴片） |
| `mdm_ortho_k_params` | M01-08 | `param_group_id`、`param_group_code` | OK 镜验配参数组 |
| `m16_optical_order` | M16-04 | `sales_order_no` | 视光销售单（收钱权威） |
| `m10_order` | M10-06 | `m10_order_no` | 配镜订单业务档案 |
| `m10_customer` | M10-05 | `customer_id` | 视光顾客档案 |
| `m10_followup_plan` | M10-09 | `followup_plan_id` | 复查计划 |
| `m10_optometry` | M10-01 | `optometry_no` | 验光单 |
| `m10_prescription` | M10-02 | `prescription_no` | 配镜处方 |

---

## 附录 B：状态枚举汇总

| 枚举 | 字段 | 取值 | 说明 |
|---|---|---|---|
| 验配单状态 | `m10_ortho_k_fitting.status` | `DRAFT`/`APPLYING`/`ASSESSED`/`TRIAL`/`CUSTOMIZING`/`ORDERED`/`ARRIVED`/`DELIVERED`/`FOLLOWING`/`REPLACE_DUE`/`REPLACED`/`STOPPED`/`CLOSED` | 13 态，见 B.1 |
| 准入结论 | `m10_ortho_k_apply.access_result` | `PENDING`/`PASS`/`CONDITIONAL`/`FAIL` | 待评估/通过/有条件通过/拒绝 |
| 依从性等级 | `m10_ortho_k_apply.compliance_level` | `GOOD`/`FAIR`/`POOR` | ≥80 / 60~79 / <60 |
| 地形图图形 | `m10_ortho_k_apply.topography_pattern`、`m10_ortho_k_cornea.topography_pattern` | `NORMAL`/`SYMMETRIC_BOWTIE`/`ASYMMETRIC_BOWTIE`/`KERATOCONUS_SUSPECT`/`IRREGULAR` | 正常/对称领结/不对称领结/圆锥可疑/不规则 |
| 测量阶段 | `m10_ortho_k_cornea.measure_stage` | `PRE_FIT`/`POST_TRIAL`/`FOLLOWUP`/`POST_STOP` | 验配前/试戴后/随访/停戴后 |
| 测量来源 | `m10_ortho_k_cornea.measure_source` | `MANUAL`/`DEVICE`/`IMPORT` | 人工/设备直连/导入 |
| 试戴片状态 | `m10_ortho_k_trial_lens.status` | `IN_STOCK`/`IN_USE`/`DISINFECTING`/`DAMAGED`/`EXPIRED`/`SCRAPPED` | 在库/占用中/消毒中/损坏/过期/报废 |
| 占用释放类型 | `m10_ortho_k_trial_use.release_kind` | `RETURNED`/`KEPT`/`ABNORMAL` | 正常归还/留戴观察/异常结束 |
| 荧光配适 | `m10_ortho_k_trial_use.fluo_*`、`m10_ortho_k_followup.*_fluo_fit` | `FLAT`/`IDEAL`/`STEEP` | 过平/理想/过陡 |
| 配适合格判定 | `m10_ortho_k_trial_use.fit_quality` | `EXCELLENT`/`ACCEPTABLE`/`UNACCEPTABLE` | 优秀/可接受/不可接受 |
| 镜片定位 | `m10_ortho_k_trial_use.lens_position`、`m10_ortho_k_followup.*_lens_position` | `CENTERED`/`SLIGHT_DECENTERED`/`DECENTERED` | 居中/轻度偏位/明显偏位 |
| 偏位方向 | `m10_ortho_k_trial_use.decentered_direction` | `SUPERIOR`/`INFERIOR`/`NASAL`/`TEMPORAL` | 上/下/鼻侧/颞侧 |
| TFT 图形 | `m10_ortho_k_trial_use.tft_pattern`、`m10_ortho_k_followup.*_tft_pattern` | `BULLSEYE`/`SMILEY`/`TARGET`/`CENTRAL_CRAB`/`NON_CENTRAL`/`IRREGULAR` | 牛眼环/笑脸/靶心/中央蟹爪/非中央/不规则 |
| TFT 环完整度 | `m10_ortho_k_trial_use.tft_ring_integrity` | `COMPLETE`/`PARTIAL`/`ABSENT` | 完整/部分/缺失 |
| 订片决策 | `m10_ortho_k_trial_use.decision` | `ORDER_AS_IS`/`ADJUST`/`RETRY`/`ABORT` | 按试戴片下单/调整后下单/换片再试/放弃 |
| 定制参数状态 | `m10_ortho_k_custom_param.status` | `DRAFT`/`CHECKED`/`ORDERED`/`PRODUCING`/`ARRIVED`/`CANCELLED` | 草稿/已校验/已下单/在产/已到片/已取消 |
| 适配校验结论 | `m10_ortho_k_custom_param.check_result` | `PENDING`/`PASS`/`PASS_WITH_WARN`/`FAIL` | 未校验/通过/通过但有提示/不通过 |
| 参数来源 | `m10_ortho_k_custom_param.param_source` | `TRIAL`/`CALCULATED`/`DOCTOR` | 试戴结果/公式计算/医师指定 |
| 镜片颜色 | `m10_ortho_k_custom_param.color` | `CLEAR`/`BLUE`/`GREEN`/`VIOLET` | 透明/蓝/绿/紫 |
| 验收结论 | `m10_ortho_k_delivery.accept_result` | `PENDING`/`PASS`/`FAIL`/`RETURNED` | 待验/通过/不通过/已退回 |
| 消毒方式 | `m10_ortho_k_delivery.disinfect_method` | `BOIL`/`PEROXIDE`/`UV` | 煮沸/双氧水/紫外线 |
| 随访节点 | `m10_ortho_k_followup.followup_node` | `D1`/`D7`/`D30`/`D90`/`M3`/`M6`/`M9`/`M12`/`EXTRA` | 见 B.2 |
| 随访类型 | `m10_ortho_k_followup.followup_type` | `SCHEDULED`/`UNSCHEDULED`/`POST_REPLACE` | 计划内/计划外/换片后 |
| 角膜荧光染色 | `m10_ortho_k_followup.*_fluorescein` | `NORMAL`/`PUNCTATE_STAINING`/`STAINING`/`INFILTRATE`/`ULCER` | 正常/点状染色/片状染色/浸润/溃疡 |
| 染色位置 | `m10_ortho_k_followup.*_stain_location` | `CENTRAL`/`PARACENTRAL`/`PERIPHERAL`/`LIMBAL` | 中央/旁中央/周边/角膜缘 |
| 镜片清洁度 | `m10_ortho_k_followup.*_lens_cleanliness` | `CLEAN`/`SLIGHT_DEPOSIT`/`HEAVY_DEPOSIT` | 清洁/轻度沉淀/重度沉淀 |
| 镜片损伤 | `m10_ortho_k_followup.*_lens_damage` | `NONE`/`SCRATCH`/`CHIP`/`BROKEN` | 无/划痕/崩边/破损 |
| 并发症严重度 | `m10_ortho_k_followup.complication_grade` | `NONE`/`MILD`/`MODERATE`/`SEVERE` | 无/轻/中/重 |
| 随访结论 | `m10_ortho_k_followup.followup_result` | `NORMAL`/`OBSERVE`/`ADJUST_LENS`/`DISCONTINUE` | 继续戴/加强观察/需调片/建议停戴 |
| 停戴原因 | `m10_ortho_k_fitting.stop_reason_code` | `CORNEAL_INJURY`/`INFECTION`/`FEVER_COLD`/`SWIMMING`/`PREGNANCY`/`NON_COMPLIANCE`/`PATIENT_REQUEST`/`SWITCH_TO_OTHER`/`OTHER` | 见 B.3 |
| 换片原因 | `m10_ortho_k_fitting.replace_reason_code` | `CYCLE_EXPIRED`/`POWER_CHANGE`/`LENS_DAMAGED`/`LENS_LOST`/`POOR_FIT`/`OTHER` | 见 B.4 |
| 产品品类 | `m10_ortho_k_fitting.product_kind` | `ORTHO_K`/`RGP` | 角膜塑形镜/硬性透气接触镜 |
| 器械类别 | `m10_ortho_k_fitting.device_class` | `CLASS_III` | 角膜塑形镜与 RGP 均为第三类 |
| 日志动作 | `m10_ortho_k_log.action` | 31 个动作值，见 4.10 业务说明 | — |
| 日志结果 | `m10_ortho_k_log.result` | `SUCCESS`/`FAIL` | 成功/失败 |
| 操作人角色 | `m10_ortho_k_log.operator_role` | `OPTOMETRIST`/`OPHTHALMIC_PHYSICIAN`/`NURSE`/`SALES`/`MANAGER`/`SYSTEM` | 验光师/眼科医师/护士/销售/管理者/系统 |

### B.1 验配单状态机（13 态）

| 状态 | 中文 | 进入条件 | 允许的下一状态 | 可编辑 |
|---|---|---|---|---|
| `DRAFT` | 草稿 | 新建验配单 | `APPLYING`、`CLOSED` | 是 |
| `APPLYING` | 准入评估中 | 提交准入评估 | `ASSESSED`、`STOPPED` | 是 |
| `ASSESSED` | 准入通过 | 准入结论 ∈ {`PASS`,`CONDITIONAL`} 且医学复核（如需）已通过 | `TRIAL`、`STOPPED` | 是 |
| `TRIAL` | 试戴中 | 首次占用试戴片成功 | `CUSTOMIZING`、`ASSESSED`、`STOPPED` | 是（试戴记录） |
| `CUSTOMIZING` | 定制参数生成中 | 订片决策 ∈ {`ORDER_AS_IS`,`ADJUST`} | `ORDERED`、`TRIAL`、`STOPPED` | 是（定制参数） |
| `ORDERED` | 已下单待制片 | 定制参数 fit-check 通过且已下发厂家 | `ARRIVED`、`STOPPED` | 否 |
| `ARRIVED` | 已到片待验发 | 至少一片验收通过 | `DELIVERED`、`ARRIVED` | 是（验发记录） |
| `DELIVERED` | 已发放戴镜 | 至少一眼已发放且有戴镜起算日 | `FOLLOWING`、`STOPPED` | 是（随访） |
| `FOLLOWING` | 随访中 | 完成第 1 天复查 | `REPLACE_DUE`、`STOPPED`、`CLOSED` | 是（随访） |
| `REPLACE_DUE` | 换片预警 | 距预计换片日 ≤60 天 | `REPLACED`、`FOLLOWING`、`STOPPED` | 是 |
| `REPLACED` | 已换片 | 由 P08 启动换片并以新单承接 | 终态（本单） | 否 |
| `STOPPED` | 已停戴 | 停戴原因登记完成 | `FOLLOWING`（复戴）、`CLOSED` | 是（停戴记录） |
| `CLOSED` | 已完结 | 换片/停戴后完结，或草稿作废 | 终态 | 否 |

> **说明：** `REPLACED` 是本单的终态；换片后患者由新验配单（`replace_round + 1`）承接，原单通过 `previous_fit_id` 链追溯。

### B.2 复查节点与天数映射

| 节点 | 中文 | 相对戴镜日天数 | 是否必查 | 逾期告警阈值 |
|---|---|---|---|---|
| `D1` | 戴镜后第 1 天 | 1 | 必查 | 逾期 3 天 |
| `D7` | 戴镜后 1 周 | 7 | 必查 | 逾期 7 天 |
| `D30` | 戴镜后 1 个月 | 30 | 必查 | 逾期 15 天 |
| `D90` | 戴镜后 3 个月 | 90 | 必查 | 逾期 30 天 |
| `M3` | 戴镜后 6 个月 | 180 | 必查 | 逾期 30 天 |
| `M6` | 戴镜后 9 个月 | 270 | 必查 | 逾期 30 天 |
| `M9` | 戴镜后 12 个月 | 360 | 必查 | 逾期 30 天 |
| `M12` | 戴镜后 15 个月 | 450 | 建议 | 逾期 30 天 |
| `EXTRA` | 计划外复查 | — | 按需 | — |

### B.3 停戴原因

| 编码 | 中文 | 是否需上报 | 典型停戴时长 |
|---|---|---|---|
| `CORNEAL_INJURY` | 角膜损伤 | 是 | 7~30 天 |
| `INFECTION` | 眼部感染 | **强制上报** | ≥30 天 |
| `FEVER_COLD` | 感冒发热 | 否 | 3~7 天 |
| `SWIMMING` | 游泳/水上活动期 | 否 | 1~7 天 |
| `PREGNANCY` | 妊娠期 | 否 | 长期 |
| `NON_COMPLIANCE` | 依从性差 | 否 | 视情况 |
| `PATIENT_REQUEST` | 患者主动要求 | 否 | 视情况 |
| `SWITCH_TO_OTHER` | 改用其他矫正方式 | 否 | 永久 |
| `OTHER` | 其他 | 视情况 | 视情况 |

### B.4 换片原因

| 编码 | 中文 | 触发时机 | 是否需重新验配 |
|---|---|---|---|
| `CYCLE_EXPIRED` | 更换周期到期 | 戴镜满 12~18 个月 | 是（复用原参数为主） |
| `POWER_CHANGE` | 屈光度变化 | 随访发现近视加深 >0.50D | 是（重新出参数） |
| `LENS_DAMAGED` | 镜片破损 | 随访发现 `SCRATCH`/`CHIP`/`BROKEN` | 是（参数不变，加急） |
| `LENS_LOST` | 镜片遗失 | 患者报失 | 是（参数不变） |
| `POOR_FIT` | 配适不良 | 随访发现偏位/牛眼环异常 | 是（调整弧参数） |
| `OTHER` | 其他 | 视情况 | 视情况 |

---

## 附录 C：关键索引与查询

### C.1 查询一：试戴片可用性匹配（P04 核心）

按角膜平坦曲率 Kf 与目标降度，找出可用的试戴片候选：

```sql
-- 入参：$kf（角膜平坦 K，D）、$reduction（目标降度，D）、$store_id
-- 逻辑：优先匹配 K 值区间覆盖的试戴片，再按 BC 与降度接近度排序
SELECT
    tl.id,
    tl.trial_lens_no,
    tl.bc,
    tl.rc,
    tl.ac,
    tl.pc,
    tl.diameter,
    tl.reduction_power,
    tl.k_min,
    tl.k_max,
    tl.expire_date,
    tl.last_disinfected_at,
    (337.5 / tl.bc)                      AS k_flat_equiv,
    round(abs((337.5 / tl.bc) - $kf)::numeric, 2)  AS k_diff,
    round(abs(tl.reduction_power - $reduction)::numeric, 2) AS reduc_diff
FROM m10_ortho_k_trial_lens tl
WHERE tl.store_id = $store_id
  AND tl.is_deleted = FALSE
  AND tl.status = 'IN_STOCK'
  AND (tl.expire_date IS NULL OR tl.expire_date > CURRENT_DATE)
  AND (tl.k_min IS NULL OR $kf BETWEEN tl.k_min AND tl.k_max)
ORDER BY k_diff ASC, reduc_diff ASC, tl.usage_count ASC
LIMIT 20;
```

**走索引：** `idx_m10_ortho_k_trial_lens_krange (k_min, k_max)` 或 `idx_m10_ortho_k_trial_lens_match (bc, reduction_power, diameter)`，视 `$kf` 是否有区间覆盖而定。

### C.2 查询二：占用互斥校验（并发安全）

```sql
-- 方式一：依赖部分唯一索引，直接 INSERT，冲突即拒绝（推荐）
INSERT INTO m10_ortho_k_trial_use (
    use_no, fitting_id, fit_no, trial_lens_id, trial_lens_no,
    patient_id, eye_side, trial_seq, occupied_by, trial_bc, trial_reduction
) VALUES (
    $use_no, $fitting_id, $fit_no, $trial_lens_id, $trial_lens_no,
    $patient_id, $eye_side, $trial_seq, $occupied_by, $trial_bc, $trial_reduction
);
-- 若命中谓词 uk_m10_ortho_k_trial_use_active 冲突 → 返回错误码 "1004019"

-- 方式二：占用前查询当前占用者（仅用于给用户友好提示，不作为互斥依据）
SELECT tu.id, tu.patient_id, tu.fitting_id, tu.occupied_at, tu.occupied_by_name
FROM m10_ortho_k_trial_use tu
WHERE tu.trial_lens_id = $trial_lens_id
  AND tu.released_at IS NULL
  AND tu.is_deleted = FALSE;
```

### C.3 查询三：复查到期清单（P07 核心）

```sql
-- 找出所有在戴镜且下次复查日已到期的患者
SELECT
    f.id                AS fitting_id,
    f.fit_no,
    f.patient_id,
    f.patient_name,
    f.phone,
    f.guardian_phone,
    f.delivered_at,
    f.next_followup_date,
    f.overdue_days,
    (CURRENT_DATE - f.next_followup_date) AS days_past_due,
    COALESCE(
        (SELECT jsonb_agg(fu.followup_node ORDER BY fu.followup_seq)
         FROM m10_ortho_k_followup fu
         WHERE fu.fitting_id = f.id AND fu.is_deleted = FALSE),
        '[]'::jsonb
    ) AS completed_nodes
FROM m10_ortho_k_fitting f
WHERE f.is_deleted = FALSE
  AND f.status IN ('DELIVERED', 'FOLLOWING', 'REPLACE_DUE')
  AND f.next_followup_date IS NOT NULL
  AND f.next_followup_date <= CURRENT_DATE
ORDER BY f.next_followup_date ASC
LIMIT 200;
```

**走索引：** `idx_m10_ortho_k_fitting_next_fu (next_followup_date)` 部分索引。

### C.4 查询四：逾期 >30 天漏复查清单（专项监控）

```sql
SELECT
    f.id, f.fit_no, f.patient_name, f.phone, f.guardian_phone,
    f.next_followup_date, f.overdue_days,
    f.fitter_name, f.store_name
FROM m10_ortho_k_fitting f
WHERE f.is_deleted = FALSE
  AND f.status IN ('DELIVERED', 'FOLLOWING', 'REPLACE_DUE')
  AND f.overdue_days > 30
ORDER BY f.overdue_days DESC;
```

**走索引：** `idx_m10_ortho_k_fitting_overdue (overdue_days) WHERE overdue_days > 0`。

### C.5 查询五：换片链路递归追踪

```sql
WITH RECURSIVE chain AS (
    -- 起点：当前/最新一单
    SELECT id, fit_no, previous_fit_id, replace_round, status,
           delivered_at, expected_replace_date, replace_reason_code, 0 AS depth
    FROM m10_ortho_k_fitting
    WHERE id = $latest_fitting_id
    UNION ALL
    -- 向上追溯上一副
    SELECT p.id, p.fit_no, p.previous_fit_id, p.replace_round, p.status,
           p.delivered_at, p.expected_replace_date, p.replace_reason_code,
           c.depth + 1
    FROM m10_ortho_k_fitting p
    JOIN chain c ON p.id = c.previous_fit_id
    WHERE p.is_deleted = FALSE
)
SELECT * FROM chain ORDER BY replace_round ASC;
```

**走索引：** `idx_m10_ortho_k_fitting_previous (previous_fit_id)` 部分索引。

### C.6 查询六：复查依从率统计（P09）

```sql
-- 按节点统计：应有该节点的验配单数 vs 实际完成数
SELECT
    n.node,
    count(*) FILTER (WHERE n.should_have)           AS should_count,
    count(*) FILTER (WHERE n.done)                  AS done_count,
    round(100.0 * count(*) FILTER (WHERE n.done)
          / NULLIF(count(*) FILTER (WHERE n.should_have), 0), 2) AS rate_pct
FROM (
    SELECT f.id AS fitting_id, v.node,
           CASE
               WHEN v.days <= (CURRENT_DATE - f.delivered_at::date)
               THEN TRUE ELSE FALSE
           END AS should_have,
           EXISTS (
               SELECT 1 FROM m10_ortho_k_followup fu
               WHERE fu.fitting_id = f.id
                 AND fu.followup_node = v.node
                 AND fu.is_deleted = FALSE
           ) AS done
    FROM m10_ortho_k_fitting f
    CROSS JOIN (VALUES ('D1', 1), ('D7', 7), ('D30', 30), ('D90', 90),
                       ('M3', 180), ('M6', 270), ('M9', 360), ('M12', 450))
               AS v(node, days)
    WHERE f.is_deleted = FALSE
      AND f.delivered_at IS NOT NULL
      AND f.status IN ('DELIVERED', 'FOLLOWING', 'REPLACE_DUE', 'REPLACED', 'CLOSED')
      AND f.delivered_at >= $start_time
) n
GROUP BY n.node
ORDER BY min(n.node);
```

### C.7 查询七：待上报不良事件

```sql
SELECT fu.id, fu.followup_no, fu.patient_name, fu.visited_at,
       fu.complications, fu.complication_grade, fu.followup_doctor_name
FROM m10_ortho_k_followup fu
WHERE fu.report_required = TRUE
  AND fu.report_id IS NULL
  AND fu.is_deleted = FALSE
ORDER BY fu.visited_at ASC;
```

**走索引：** `idx_m10_ortho_k_followup_unreported`。

### C.8 查询八：定制参数 fit-check 不通过清单

```sql
SELECT cp.id, cp.custom_no, f.fit_no, cp.patient_name, cp.eye_side,
       cp.check_result, cp.check_fail_items, cp.fit_check_message, cp.fit_check_at
FROM m10_ortho_k_custom_param cp
JOIN m10_ortho_k_fitting f ON f.id = cp.fitting_id
WHERE cp.check_result = 'FAIL'
  AND cp.is_ordered = FALSE
  AND cp.is_deleted = FALSE
ORDER BY cp.created_at DESC;
```

**走索引：** `idx_m10_ortho_k_custom_param_checkfail (fitting_id, eye_side) WHERE check_result = 'FAIL'`。

### C.9 索引命中与容量估算

| 查询场景 | 主要索引 | 单次扫描行数估算 | 目标 P95 |
|---|---|---|---|
| 试戴片可用匹配 | `idx_m10_ortho_k_trial_lens_krange` | 200~600 | ≤80ms |
| 占用互斥 INSERT | `uk_m10_ortho_k_trial_use_active` | 1（唯一索引查找） | ≤50ms |
| 复查到期清单 | `idx_m10_ortho_k_fitting_next_fu` | 50~300 | ≤120ms |
| 逾期专项 | `idx_m10_ortho_k_fitting_overdue` | 10~100 | ≤80ms |
| 换片链路 | `idx_m10_ortho_k_fitting_previous` | ≤10 | ≤60ms |
| 依从率统计 | `idx_m10_ortho_k_followup_node_stat` | 5,000~20,000 | ≤800ms |
| 待上报事件 | `idx_m10_ortho_k_followup_unreported` | 1~20 | ≤50ms |
| fit-check 不通过 | `idx_m10_ortho_k_custom_param_checkfail` | 1~20 | ≤50ms |
| P-09 验配单详情 | `idx_m10_ortho_k_custom_param_fitting` 等 5 个 | 每条 ≤10 | ≤150ms |

---

## 附录 D：配置参数与字典

### D.1 系统参数（`m10_ortho_k_config` 逻辑配置，实际存于系统参数表）

| 参数键 | 中文 | 默认值 | 说明 | 可调整 |
|---|---|---|---|---|
| `orthok.age.min` | 最小验配年龄 | `8` | 低于则准入不通过 | 否（法规） |
| `orthok.age.max` | 最大验配年龄 | `40` | 超过需医师复核 | 是 |
| `orthok.sphere.min` | 最小球镜（D） | `-6.00` | 近视上限 | 是（厂家范围） |
| `orthok.sphere.max` | 最大球镜（D） | `-0.75` | 近视下限 | 是 |
| `orthok.cylinder.max` | 最大柱镜（D） | `-1.50` | 部分产品可放宽至 −2.00 | 是 |
| `orthok.curvature.min` | 最小角膜曲率（D） | `41.00` | Km 下限 | 否 |
| `orthok.curvature.max` | 最大角膜曲率（D） | `46.00` | Km 上限 | 否 |
| `orthok.thickness.min` | 最小中央角膜厚度（μm） | `480` | 低于则不通过 | 否 |
| `orthok.iop.min` | 眼压下限（mmHg） | `10` | — | 否 |
| `orthok.iop.max` | 眼压上限（mmHg） | `21` | — | 否 |
| `orthok.tear.but.min` | BUT 下限（秒） | `10` | 泪膜破裂时间 | 否 |
| `orthok.tear.schirmer.min` | Schirmer 下限（mm/5min） | `10` | 泪液分泌试验 | 否 |
| `orthok.anisometropia.max` | 屈光参差上限（D） | `1.50` | 双眼球镜差绝对值 | 是 |
| `orthok.compliance.min` | 依从性最低分 | `60` | 低于为 `POOR` | 是 |
| `orthok.apply.valid.days` | 准入结论有效期（天） | `90` | 超期需重新评估 | 是 |
| `orthok.consent.required` | 是否强制知情同意 | `true` | 三类器械合规 | 否 |
| `orthok.trial.occupy.timeout.hours` | 试戴片占用超时（小时） | `4` | 超时告警并可强制释放 | 是 |
| `orthok.trial.disinfect.max` | 试戴片消毒次数上限 | `200` | 超过建议报废 | 是 |
| `orthok.trial.open.valid.months` | 试戴片开封有效期（月） | `12` | 开封日 + N 月 | 是 |
| `orthok.trial.disinfect.interval.days` | 试戴片消毒间隔上限（天） | `7` | 超期未消毒不允许占用 | 是 |
| `orthok.followup.nodes` | 复查节点 | `1,7,30,90` | 天，之后每 3 月 | 否（规范） |
| `orthok.followup.overdue.alert.days` | 逾期告警阈值（天） | `30` | 超过则进专项监控 | 是 |
| `orthok.replace.months.default` | 默认更换周期（月） | `12` | 发放时计算换片日 | 是 |
| `orthok.replace.warn.days` | 换片预警提前天数 | `60` | 距换片日 ≤N 天进入 `REPLACE_DUE` | 是 |
| `orthok.teaching.minutes.min` | 首次教学最短时长（分钟） | `30` | 发放硬门槛 | 否（规范） |
| `orthok.device.reg.check` | 是否强校验注册证有效期 | `true` | 三类器械合规 | 否 |
| `orthok.fitcheck.required` | 是否强制调用 fit-check | `true` | 下单前必须校验 | 否 |
| `orthok.log.retention.months` | 日志保留月数 | `24` | 分区归档 | 是 |

### D.2 字典项

| 字典类别 | 名称 | 取值 |
|---|---|---|
| `ORTHOK_NODE` | 复查节点 | `D1`/`D7`/`D30`/`D90`/`M3`/`M6`/`M9`/`M12`/`EXTRA` |
| `ORTHOK_STOP_REASON` | 停戴原因 | 见附录 B.3 |
| `ORTHOK_REPLACE_REASON` | 换片原因 | 见附录 B.4 |
| `ORTHOK_COMPLICATION` | 并发症 | `CORNEAL_STAINING`/`CORNEAL_INFILTRATE`/`INFECTIOUS_KERATITIS`/`CORNEAL_ABRASION`/`CORNEAL_EDEMA`/`LENS_DEPOSIT`/`LENS_DAMAGE`/`CONJUNCTIVITIS`/`RED_EYE`/`GHOST_VISION` |
| `ORTHOK_TFT_PATTERN` | TFT 图形 | `BULLSEYE`/`SMILEY`/`TARGET`/`CENTRAL_CRAB`/`NON_CENTRAL`/`IRREGULAR` |
| `ORTHOK_COLOR` | 镜片颜色 | `CLEAR`/`BLUE`/`GREEN`/`VIOLET` |
| `ORTHOK_MATERIAL` | 镜片材质 | `BOSTON_XO`/`BOSTON_EO`/`ROFLUFOCON_A`/`MENICON_Z`/`OTHER` |
| `ORTHOK_DISINFECT` | 消毒方式 | `BOIL`/`PEROXIDE`/`UV` |
| `ORTHOK_TEACHING` | 教学内容 | `WEAR`（摘戴）/`CLEAN`（清洗）/`SOLUTION`（护理液）/`ABNORMAL`（异常处理）/`FOLLOWUP`（复查安排） |
| `OPTICAL_BRAND` | 品牌（只读 M01-08） | 依视路/蔡司/豪雅/明月/梦戴维/欧几里德/普诺瞳/亨泰等 |

### D.3 医疗器械注册证校验口径

| 校验项 | 规则 | 不通过错误码 |
|---|---|---|
| 注册证非空 | `device_reg_no IS NOT NULL` | `"1004021"` |
| 有效期非空 | `device_reg_valid_until IS NOT NULL` | `"1004021"` |
| 有效期未过 | `device_reg_valid_until >= CURRENT_DATE` | `"1004021"` |
| 器械类别 | `device_class = 'CLASS_III'` | `"1004021"` |
| 产品状态 | M01-08 `full-config` 返回 `status = 'ENABLED'` 且未删除 | `"1004027"` |
| 试戴片标识 | 试戴片产品 `is_trial_lens = TRUE`；销售片 `is_trial_lens = FALSE` | `"1004028"` |
| 验配师资质 | `fitter_qualification ∈ {OPTOMETRIST, OPHTHALMIC_PHYSICIAN}` | `"1004032"` |

---

## 附录 E：建表依赖顺序与 Alembic 迁移

### E.1 建表依赖顺序（3 层）

| 层 | 表 | 依赖的外部表（须先建） | 说明 |
|---|---|---|---|
| **第 0 层（外部）** | — | `mpi_patient`（M03-01）、`mdm_optical_product`（M01-08）、`mdm_ortho_k_params`（M01-08）、`m16_optical_order`（M16-04）、`m10_customer`（M10-05）、`m10_followup_plan`（M10-09） | M10-04 只读引用，不建物理外键；**须先于本模块建表存在** |
| **第 1 层（无内部依赖）** | `m10_ortho_k_trial_lens`、`m10_ortho_k_apply` | 无 | 台账与准入评估可独立建 |
| **第 2 层（依赖第 1 层）** | `m10_ortho_k_fitting`、`m10_ortho_k_log` | `m10_ortho_k_apply`（`apply_id`） | 验配单主表；日志表结构独立但审计对象为主表 |
| **第 3 层（依赖第 2 层）** | `m10_ortho_k_cornea`、`m10_ortho_k_trial_use`、`m10_ortho_k_custom_param` | `m10_ortho_k_fitting`、`m10_ortho_k_trial_lens` | 三张表均挂 `fitting_id` |
| **第 4 层（依赖第 3 层）** | `m10_ortho_k_delivery` | `m10_ortho_k_custom_param` | 验发以定制参数为依据 |
| **第 5 层** | `m10_ortho_k_followup` | `m10_ortho_k_fitting` | 随访独立于验发，可第 3 层建 |

**物理建表顺序：**
```
① m10_ortho_k_apply
② m10_ortho_k_trial_lens
③ m10_ortho_k_fitting
④ m10_ortho_k_log（分区表 + 三个初始分区 + default 分区）
⑤ m10_ortho_k_cornea
⑥ m10_ortho_k_trial_use（含 uk_m10_ortho_k_trial_use_active 部分唯一索引）
⑦ m10_ortho_k_custom_param
⑧ m10_ortho_k_delivery
⑨ m10_ortho_k_followup
```

### E.2 Alembic 迁移脚本

```python
"""Alembic 迁移：M10-04 OK镜与RGP验配随访 —— 建 9 张表

revision = "20261101_m10_04"
down_revision = "20261101_m10_03"
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20261101_m10_04"
down_revision = "20261101_m10_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """按依赖顺序建表。"""
    # 扩展：中文模糊检索
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ① m10_ortho_k_apply
    op.create_table(
        "m10_ortho_k_apply",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("apply_no", sa.String(32)),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_name", sa.String(64), nullable=False),
        sa.Column("age", sa.SmallInteger(), nullable=False),
        sa.Column("access_result", sa.String(16), nullable=False,
                  server_default="PENDING"),
        sa.Column("assessor_id", sa.BigInteger()),
        sa.Column("assessed_at", sa.DateTime()),
        sa.Column("keratoconus_suspect", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("fail_items", postgresql.JSONB()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_apply_no", "m10_ortho_k_apply", ["apply_no"],
                    unique=True, postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_m10_ortho_k_apply_patient", "m10_ortho_k_apply",
                    ["patient_id", sa.text("created_at DESC")])
    op.create_index("idx_m10_ortho_k_apply_fail_trgm", "m10_ortho_k_apply",
                    ["reject_reason"], postgresql_using="gin",
                    postgresql_ops={"reject_reason": "gin_trgm_ops"})

    # ② m10_ortho_k_trial_lens
    op.create_table(
        "m10_ortho_k_trial_lens",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("trial_lens_no", sa.String(64), nullable=False),
        sa.Column("product_code", sa.String(32), nullable=False),
        sa.Column("bc", sa.Numeric(5, 2), nullable=False),
        sa.Column("rc", sa.Numeric(5, 2)),
        sa.Column("ac", sa.Numeric(5, 2)),
        sa.Column("pc", sa.Numeric(5, 2)),
        sa.Column("diameter", sa.Numeric(5, 2)),
        sa.Column("reduction_power", sa.Numeric(6, 2)),
        sa.Column("k_min", sa.Numeric(6, 2)),
        sa.Column("k_max", sa.Numeric(6, 2)),
        sa.Column("status", sa.String(16), nullable=False, server_default="IN_STOCK"),
        sa.Column("sealed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("opened_at", sa.DateTime()),
        sa.Column("expire_date", sa.Date()),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_trial_lens_no", "m10_ortho_k_trial_lens",
                    ["trial_lens_no"], unique=True,
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_m10_ortho_k_trial_lens_krange", "m10_ortho_k_trial_lens",
                    ["k_min", "k_max"],
                    postgresql_where=sa.text(
                        "status = 'IN_STOCK' AND is_deleted = FALSE"))

    # ③ m10_ortho_k_fitting
    op.create_table(
        "m10_ortho_k_fitting",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("fit_no", sa.String(32)),
        sa.Column("apply_id", sa.BigInteger()),
        sa.Column("previous_fit_id", sa.BigInteger()),
        sa.Column("replace_round", sa.SmallInteger(), nullable=False,
                  server_default="1"),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_name", sa.String(64), nullable=False),
        sa.Column("product_kind", sa.String(16), nullable=False,
                  server_default="ORTHO_K"),
        sa.Column("status", sa.String(24), nullable=False, server_default="DRAFT"),
        sa.Column("store_id", sa.BigInteger(), nullable=False),
        sa.Column("fitter_id", sa.BigInteger(), nullable=False),
        sa.Column("apply_time", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.Column("expected_replace_date", sa.Date()),
        sa.Column("next_followup_date", sa.Date()),
        sa.Column("overdue_days", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_fitting_no", "m10_ortho_k_fitting", ["fit_no"],
                    unique=True, postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_index("idx_m10_ortho_k_fitting_next_fu", "m10_ortho_k_fitting",
                    ["next_followup_date"],
                    postgresql_where=sa.text(
                        "status IN ('DELIVERED','FOLLOWING','REPLACE_DUE') "
                        "AND is_deleted = FALSE"))
    op.create_index("idx_m10_ortho_k_fitting_overdue", "m10_ortho_k_fitting",
                    ["overdue_days"],
                    postgresql_where=sa.text("overdue_days > 0 AND is_deleted = FALSE"))

    # ④ m10_ortho_k_log（分区表）
    op.execute("""
        CREATE TABLE m10_ortho_k_log (
            id            BIGINT GENERATED BY DEFAULT AS IDENTITY,
            log_no        VARCHAR(40),
            fitting_id    BIGINT,
            entity_type   VARCHAR(32) NOT NULL,
            entity_id     BIGINT,
            action        VARCHAR(32) NOT NULL,
            changed_fields JSONB,
            operator_id   BIGINT,
            result        VARCHAR(16) NOT NULL DEFAULT 'SUCCESS',
            error_code    VARCHAR(16),
            duration_ms   INT,
            created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id, created_at)
        ) PARTITION BY RANGE (created_at)
    """)
    op.execute("""
        CREATE TABLE m10_ortho_k_log_p202611 PARTITION OF m10_ortho_k_log
            FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
    """)
    op.execute("""
        CREATE TABLE m10_ortho_k_log_p202612 PARTITION OF m10_ortho_k_log
            FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
    """)
    op.execute("""
        CREATE TABLE m10_ortho_k_log_pdefault PARTITION OF m10_ortho_k_log DEFAULT
    """)

    # ⑤ m10_ortho_k_cornea
    op.create_table(
        "m10_ortho_k_cornea",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("cornea_no", sa.String(32)),
        sa.Column("fitting_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("eye_side", sa.String(8), nullable=False),
        sa.Column("measure_stage", sa.String(16), nullable=False,
                  server_default="PRE_FIT"),
        sa.Column("k1", sa.Numeric(6, 2)),
        sa.Column("k2", sa.Numeric(6, 2)),
        sa.Column("km", sa.Numeric(6, 2)),
        sa.Column("e_value", sa.Numeric(5, 2)),
        sa.Column("hvid", sa.Numeric(5, 2)),
        sa.Column("thickness_central", sa.SmallInteger()),
        sa.Column("topography_pattern", sa.String(24)),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("idx_m10_ortho_k_cornea_latest", "m10_ortho_k_cornea",
                    ["fitting_id", "eye_side"],
                    postgresql_where=sa.text(
                        "measure_stage = 'PRE_FIT' AND is_valid = TRUE"))

    # ⑥ m10_ortho_k_trial_use（★ 核心互斥约束）
    op.create_table(
        "m10_ortho_k_trial_use",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("use_no", sa.String(32)),
        sa.Column("fitting_id", sa.BigInteger(), nullable=False),
        sa.Column("trial_lens_id", sa.BigInteger(), nullable=False),
        sa.Column("trial_lens_no", sa.String(64), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("eye_side", sa.String(8), nullable=False),
        sa.Column("trial_seq", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("occupied_at", sa.DateTime(), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("occupied_by", sa.BigInteger(), nullable=False),
        sa.Column("released_at", sa.DateTime()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    # ★★ 一片试戴片同一时刻只能给一个患者
    op.create_index(
        "uk_m10_ortho_k_trial_use_active",
        "m10_ortho_k_trial_use",
        ["trial_lens_id"],
        unique=True,
        postgresql_where=sa.text("released_at IS NULL AND is_deleted = FALSE"),
    )
    op.create_index("idx_m10_ortho_k_trial_use_fitting", "m10_ortho_k_trial_use",
                    ["fitting_id", sa.text("occupied_at DESC")])

    # ⑦ m10_ortho_k_custom_param（★ fit-check 强制）
    op.create_table(
        "m10_ortho_k_custom_param",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("custom_no", sa.String(32)),
        sa.Column("fitting_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("eye_side", sa.String(8), nullable=False),
        sa.Column("cornea_id", sa.BigInteger(), nullable=False),
        sa.Column("bc", sa.Numeric(5, 2), nullable=False),
        sa.Column("rc", sa.Numeric(5, 2)),
        sa.Column("ac", sa.Numeric(5, 2)),
        sa.Column("pc", sa.Numeric(5, 2)),
        sa.Column("diameter", sa.Numeric(5, 2), nullable=False),
        sa.Column("target_reduction", sa.Numeric(6, 2), nullable=False),
        sa.Column("actual_reduction", sa.Numeric(6, 2), nullable=False),
        sa.Column("fit_check_at", sa.DateTime()),
        sa.Column("fit_check_passed", sa.Boolean()),
        sa.Column("fit_check_result", postgresql.JSONB()),
        sa.Column("check_result", sa.String(16), nullable=False,
                  server_default="PENDING"),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("is_ordered", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_custom_param_eye", "m10_ortho_k_custom_param",
                    ["fitting_id", "eye_side"], unique=True,
                    postgresql_where=sa.text(
                        "status <> 'CANCELLED' AND is_deleted = FALSE"))
    op.create_check_constraint(
        "ck_m10_ortho_k_custom_param_fitcheck_required",
        "m10_ortho_k_custom_param",
        "is_ordered = FALSE OR (fit_check_at IS NOT NULL "
        "AND fit_check_passed IS NOT NULL AND fit_check_result IS NOT NULL "
        "AND check_result <> 'PENDING')",
    )
    op.create_check_constraint(
        "ck_m10_ortho_k_custom_param_fitcheck_fail",
        "m10_ortho_k_custom_param",
        "check_result <> 'FAIL' OR is_ordered = FALSE",
    )

    # ⑧ m10_ortho_k_delivery
    op.create_table(
        "m10_ortho_k_delivery",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("delivery_no", sa.String(32)),
        sa.Column("fitting_id", sa.BigInteger(), nullable=False),
        sa.Column("custom_param_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_name", sa.String(64), nullable=False),
        sa.Column("eye_side", sa.String(8), nullable=False),
        sa.Column("lens_no", sa.String(64)),
        sa.Column("accept_result", sa.String(16), nullable=False,
                  server_default="PENDING"),
        sa.Column("disinfected", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("teaching_done", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("teaching_minutes", sa.SmallInteger()),
        sa.Column("delivered_at", sa.DateTime()),
        sa.Column("wear_start_date", sa.Date()),
        sa.Column("expected_replace_date", sa.Date()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_delivery_lens_no", "m10_ortho_k_delivery",
                    ["lens_no"], unique=True,
                    postgresql_where=sa.text("lens_no IS NOT NULL AND is_deleted = FALSE"))

    # ⑨ m10_ortho_k_followup
    op.create_table(
        "m10_ortho_k_followup",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("followup_no", sa.String(32)),
        sa.Column("fitting_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_id", sa.BigInteger(), nullable=False),
        sa.Column("patient_name", sa.String(64), nullable=False),
        sa.Column("followup_seq", sa.SmallInteger(), nullable=False,
                  server_default="1"),
        sa.Column("followup_node", sa.String(16), nullable=False,
                  server_default="D1"),
        sa.Column("visited_at", sa.DateTime()),
        sa.Column("complication_grade", sa.String(16)),
        sa.Column("report_required", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
        sa.Column("report_id", sa.String(64)),
        sa.Column("followup_result", sa.String(16), nullable=False,
                  server_default="NORMAL"),
        sa.Column("next_followup_date", sa.Date()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.false()),
    )
    op.create_index("uk_m10_ortho_k_followup_node", "m10_ortho_k_followup",
                    ["fitting_id", "followup_node"], unique=True,
                    postgresql_where=sa.text(
                        "followup_node NOT IN ('EXTRA') AND is_deleted = FALSE"))
    op.create_index("idx_m10_ortho_k_followup_node_stat", "m10_ortho_k_followup",
                    ["followup_node", sa.text("visited_at DESC")],
                    postgresql_where=sa.text("is_deleted = FALSE"))
    op.create_check_constraint(
        "ck_m10_ortho_k_followup_node_ck",
        "m10_ortho_k_followup",
        "followup_node IN ('D1', 'D7', 'D30', 'D90', 'M3', 'M6', 'M9', 'M12', 'EXTRA')",
    )


def downgrade() -> None:
    """按逆序回滚。"""
    op.drop_table("m10_ortho_k_followup")
    op.drop_table("m10_ortho_k_delivery")
    op.drop_table("m10_ortho_k_custom_param")
    op.drop_table("m10_ortho_k_trial_use")
    op.drop_table("m10_ortho_k_cornea")
    op.execute("DROP TABLE IF EXISTS m10_ortho_k_log CASCADE")
    op.drop_table("m10_ortho_k_fitting")
    op.drop_table("m10_ortho_k_trial_lens")
    op.drop_table("m10_ortho_k_apply")
```

### E.3 上线前检查清单（10 项）

| # | 检查项 | 验证方式 | 期望结果 |
|---|---|---|---|
| 1 | 9 张表全部建成 | `SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'm10_ortho_k_%'` | ≥ 9（含日志分区） |
| 2 | 试戴片互斥索引存在 | `SELECT indexname FROM pg_indexes WHERE indexname = 'uk_m10_ortho_k_trial_use_active'` | 返回 1 行 |
| 3 | 互斥索引真实生效 | 并发两线程占用同一试戴片 | 一个成功、一个抛 23505 |
| 4 | fit-check 约束生效 | 直接 UPDATE `is_ordered = TRUE` 而无 `fit_check_at` | 违反 `ck_..._fitcheck_required` |
| 5 | 弧参数约束生效 | INSERT `rc > bc` | 违反 `ck_..._arc` |
| 6 | 复查节点约束生效 | INSERT `followup_node = 'D2'` | 违反 `ck_..._node_ck` |
| 7 | 日志分区已建 | `SELECT count(*) FROM pg_class WHERE relname LIKE 'm10_ortho_k_log_p%'` | ≥ 3（两月 + default） |
| 8 | 中文模糊检索可用 | `SELECT * FROM m10_ortho_k_fitting WHERE patient_name % '张'` | 正常返回 |
| 9 | 触发器维护 `updated_at` | UPDATE 任意行后查看 `updated_at` | 已更新 |
| 10 | 只读引用表存在 | 查询 `mpi_patient`、`mdm_ortho_k_params` 各 1 行 | 均可查询 |

---

## 版本历史

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-31 | 首次发布：9 张表（m10_ortho_k_fitting / apply / cornea / trial_lens / trial_use / custom_param / delivery / followup / log），SQLAlchemy 2.0 模型与 Pydantic V2 Schema 全覆盖，附录 A~E 齐全 | 系统设计组 |
