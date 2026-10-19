# 二级眼科医院 HIS 系统 — M01 主数据管理 MDM
# 数据结构设计汇总（全子模块）

**文档版本：** V1.0
**所属模块：** M01 主数据管理 MDM
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》及各子模块详细设计文档
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / MySQL 8.0 / Redis 7
**文档用途：** 作为 M01 全部主数据表结构的**独立参考手册**与**建表依据**

---

## 文档说明

本文档是 M01 主数据管理的**统一数据字典与跨模块索引**，汇总全部 7 个子模块共 **121 张表**。

### 文档体系

M01 的每个子模块的数据结构已**独立成册**，本汇总文档提供全局视图与索引：

| 子模块 | 独立数据结构文档 | 主数据域 | 表数 | 本汇总章节 |
|---|---|---|---|---|
| 科室 | [科室数据结构](M01_主数据管理MDM_01_科室_数据结构.md) | 组织人员域 | 6 | 第 01 章 |
| 职工 | [职工数据结构](M01_主数据管理MDM_02_职工_数据结构.md) | 组织人员域 | 9 | 第 02 章 |
| 药品 | [药品数据结构](M01_主数据管理MDM_03_药品_数据结构.md) | 物资域 | 11 | 第 03 章 |
| 耗材 | [耗材数据结构](M01_主数据管理MDM_04_耗材_数据结构.md) | 物资域 | 22 | 第 04 章 |
| 权限 | [权限数据结构](M01_主数据管理MDM_05_权限_数据结构.md) | 权限域 | 26 | 第 05 章 |
| 收费 | [收费数据结构](M01_主数据管理MDM_06_收费_数据结构.md) | 费用域 | 25 | 第 06 章 |
| 手术 | [手术数据结构](M01_主数据管理MDM_07_手术_数据结构.md) | 临床域 | 22 | 第 07 章 |
| **合计** | **7 个文件** | **5 个域** | **121** | — |

> **使用说明**
> 1. **日常查阅建议用独立文件**：[科室数据结构](M01_主数据管理MDM_01_科室_数据结构.md) 等 7 个文件是各子模块的权威表结构定义。
> 2. **本文档用于**：跨模块表清单检索、全局设计约定、编码规则、跨模块关联关系、批量建表脚本生成。
> 3. 本文档第 2 章起保留各模块表结构的完整副本（便于单文件检索），内容与独立文件一致。
> 4. 章节编号 `NN.M` 与独立文件的 `4.M` 一致。例如本文档 `04.8 表：mdm_material_iol` = 《耗材数据结构》4.8 节。
> 5. **表结构变更时**：先改独立文件，再同步本文档；两者若不一致，以独立文件为准。

---

## 目录

- [1. 全局设计约定](#1-全局设计约定)
  - [1.1 数据库与命名规范](#11-数据库与命名规范)
  - [1.2 公共字段规范](#12-公共字段规范)
  - [1.3 主键、索引与约束规范](#13-主键索引与约束规范)
  - [1.4 枚举与状态取值](#14-枚举与状态取值)
  - [1.5 金额、数量与时间精度](#15-金额数量与时间精度)
  - [1.6 分区与归档策略](#16-分区与归档策略)
  - [1.7 编码生成规则汇总](#17-编码生成规则汇总)
  - [1.8 全局表清单与域分布](#18-全局表清单与域分布)
  - [1.9 跨模块关联关系总览](#19-跨模块关联关系总览)
- [01. 科室数据结构](#01-科室数据结构)
- [02. 职工数据结构](#02-职工数据结构)
- [03. 药品数据结构](#03-药品数据结构)
- [04. 耗材数据结构](#04-耗材数据结构)
- [05. 权限数据结构](#05-权限数据结构)
- [06. 收费数据结构](#06-收费数据结构)
- [07. 手术数据结构](#07-手术数据结构)
- [附录 A：表名与子模块速查](#附录-a表名与子模块速查)
- [附录 B：修订记录](#附录-b修订记录)

---

## 1. 全局设计约定

本章约定 M01 全部主数据表必须遵守的统一规范，各子模块表结构在此基础上按需扩展。

### 1.1 数据库与命名规范

| 项 | 约定 |
|---|---|
| 数据库 | MySQL 8.0，字符集 `utf8mb4`，排序规则 `utf8mb4_0900_ai_ci` |
| 存储引擎 | InnoDB（全部业务表） |
| 表名前缀 | 统一 `mdm_`（主数据管理），按子模块区分第二段：`mdm_department_*`、`mdm_employee_*`、`mdm_drug_*`、`mdm_material_*`、`mdm_role_*`/`mdm_menu`、`md_charge_*`/`md_price_*`、`md_operation_*`/`md_anesthesia_*` |
| 字段命名 | 小写下划线（snake_case），见名知意，布尔字段用 `is_` / `has_` / `need_` 前缀 |
| 外键命名 | `<被引用表>_id`，如 `dept_id`、`staff_id`、`charge_item_id` |
| 冗余字段 | 稳定不变或极少变更的名称类字段可冗余（如 `dept_name`），后缀不加特殊标记 |
| 时间字段 | 统一 `DATETIME`（不用 `TIMESTAMP`，规避 2038 问题），由应用层赋值 |
| 注释 | 所有表、字段必须有 `COMMENT`，中文说明业务含义 |

### 1.2 公共字段规范

所有 `mdm_*` / `md_*` 主数据表统一包含下列公共列（各子模块表定义中按此展开）：

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键，仅内部使用 |
| code | VARCHAR(32/64) | N | — | 业务编码，对外展示与引用用 |
| status | VARCHAR/TINYINT | N | — | 业务状态，取值见 1.4 |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL = 长期有效） |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID（多院区扩展） |
| ext_json | JSON | Y | NULL | 扩展字段（避免频繁改表） |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N/Y | — | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | Y | NULL | 更新时间 |
| is_deleted / deleted | TINYINT(1) | N | 0 | 逻辑删除标记 |

> **注意**：各子模块在字段命名上存在历史差异。前 5 个子模块（科室/职工/药品/耗材/权限）使用 `is_deleted`；收费与手术子模块使用 `deleted`；`update` 相关字段在部分表使用 `version`，部分使用 `version_no`。**建表时以各子模块章节中的定义为准**，本文档不做强行统一，以免破坏已实现的代码。

### 1.3 主键、索引与约束规范

| 项 | 约定 |
|---|---|
| 主键 | `id BIGINT UNSIGNED AUTO_INCREMENT`，不使用业务编码作主键 |
| 业务编码唯一 | `UNIQUE KEY uk_<表简称>_code (code, is_deleted/deleted)` |
| 索引命名 | 唯一索引 `uk_*`，普通索引 `idx_*`，全文索引 `ft_*`，主键 `pk_*` |
| 逻辑删除 + 唯一索引 | 唯一索引必须包含 `is_deleted`/`deleted`，保证逻辑删除后可重建同名记录 |
| 条件唯一索引 | MySQL 不支持部分唯一索引，采用「生成列 + 唯一索引」实现（见各子模块说明） |
| 外键约束 | **不建物理外键**，由应用层保证引用完整性（避免锁竞争与运维负担） |
| 名称检索 | 名称类字段建 `idx_*_name`；拼音检索建 `idx_*_pinyin (pinyin_code, pinyin_short)` |
| 中文全文检索 | 使用 `FULLTEXT ... WITH PARSER ngram`（`ngram_token_size=2`） |
| 更新时间索引 | 增量同步依赖 `idx_*_updated (updated_at)` |

### 1.4 枚举与状态取值

| 枚举项 | 取值 |
|---|---|
| `status`（通用状态） | `DRAFT` / `ENABLED` / `DISABLED` / `RECALLED`（少数表用 TINYINT 0/1，见各表定义） |
| `audit_status`（审批状态） | `DRAFT` / `PENDING` / `APPROVING` / `APPROVED` / `REJECTED` |
| `is_deleted` / `deleted` | 0 = 未删除，1 = 已删除 |
| `price_type`（价格类型） | `STANDARD` / `MEMBER` / `INSURANCE` / `INTERNAL` / `DEPT` / `ACTIVITY` |
| `surgery_level`（手术分级） | `LEVEL_1` / `LEVEL_2` / `LEVEL_3` / `LEVEL_4` |
| `pay_category`（支付类别） | `CASH` / `CARD` / `SCAN` / `STORED` / `INSURANCE` / `OTHER` |
| `role_category`（角色分类） | `SYSTEM` / `POSITION` / `DEPT` / `BUSINESS` / `CUSTOM` |
| `product_kind`（视光品类，预留） | `FRAME` / `LENS` / `CONTACT` / `ORTHO_K` / `RGP` / `CARE` / `SUN` / `ACCESSORY` / `SERVICE` |

> 完整字典项见各子模块附录及 M01 主文档 5.34 节。

### 1.5 金额、数量与时间精度

| 数据类型 | 建议精度 | 适用场景 |
|---|---|---|
| 金额（单据级） | `DECIMAL(14,4)` | 调价单合计、优惠金额 |
| 金额（目录级） | `DECIMAL(12,4)` 或 `DECIMAL(10,2)` | 收费项目标准价、药品/耗材零售价 |
| 折扣率/加价率 | `DECIMAL(7,4)` | 百分比数值（如 90.0000 表示 90%） |
| 数量 | `DECIMAL(12,4)` | 药品/耗材数量、计价数量 |
| 球镜/柱镜 | `DECIMAL(6,2)` | 人工晶体度数（D） |
| A 常数 | `DECIMAL(6,2)` | 人工晶体计算参数 |
| 折射率 | `DECIMAL(5,3)` | 镜片/晶体折射率 |
| 时间 | `DATETIME` | 全部时间字段 |
| 日期 | `DATE` | 生效/失效日期 |

**舍入规则：** 金额计算使用 `ROUND_HALF_UP`（四舍五入），保留 2 位小数；单价保留 4 位小数，最终金额保留 2 位。

### 1.6 分区与归档策略

| 表类型 | 分区方式 | 保留期 | 说明 |
|---|---|---|---|
| 变更日志（`*_change_log`） | 按 `created_at` 月度 RANGE 分区 | 10 年 | 审计要求 |
| 同步日志（`*_sync_log`） | 按 `created_at` 月度 RANGE 分区 | 1 年 | 运维数据 |
| 版本快照（`mdm_permission_version`） | 按 `created_at` 月度 RANGE 分区 | 10 年 | — |
| 价格历史（`md_price_history`） | 按 `effective_date` 年度 RANGE 分区 | 10 年（不可删） | 保证历史单据取价 |
| 业务主表 | 不分区 | 永久 | 量级可控 |

### 1.7 编码生成规则汇总

| 对象 | 前缀 | 规则 | 示例 | 来源子模块 |
|---|---|---|---|---|
| 科室 | `D` | `D` + 一级科室码(2) + 流水(4) | `D010001` | 科室 |
| 职工 | `E` | `E` + 入职年月(4) + 流水(4) | `E24030017` | 职工 |
| 药品 | `DR` | `DR` + ATC大类(2) + 流水(5) | `DR1200021` | 药品 |
| 耗材 | `MT` | `MT` + 基础分类码(2) + 流水(5) | `MT0100013` | 耗材 |
| 植入物 | `IMP` | `IMP` + 流水(6) | `IMP000123` | 耗材 |
| 人工晶体 | `IOL` | `IOL` + 流水(6) | `IOL000123` | 耗材 |
| 手术套包 | `KIT` | `KIT` + 流水(4) | `KIT0021` | 耗材 |
| 菜单 | — | `{模块小写}:{资源}[:{动作}]` | `mdm:drug:create` | 权限 |
| 角色 | `R` | `R` + 流水(3) | `R020` | 权限 |
| 数据范围 | `DS` | `DS` + 流水(3) | `DS005` | 权限 |
| 收费项目 | `C` | `C` + 分类段(2) + 流水(5) | `C0300127` | 收费 |
| 价表 | `PL` | `PL` + 流水(3) | `PL001` | 收费 |
| 调价单 | `PA` | `PA` + yyyyMM + 流水(4) | `PA2026040007` | 收费 |
| 优惠方案 | `DP` | `DP` + 流水(4) | `DP0024` | 收费 |
| 收费套餐 | `CM` | `CM` + 流水(4) | `CM0086` | 收费 |
| 手术项目 | `OPR` | `OPR` + 流水(5) | `OPR00086` | 手术 |
| 麻醉方式 | `ANE` | `ANE` + 流水(3) | `ANE008` | 手术 |
| 屈光术式 | `RF` | `RF` + 流水(3) | `RF003` | 手术 |

**生成机制：** Redis `INCR` 原子自增 + 每日 DB 对账。编码**一次生成终身不变**，允许跳号但不允许重号。

### 1.8 全局表清单与域分布

**域划分：**

| 域代码 | 域名称 | 包含子模块 | 表数 |
|---|---|---|---|
| `ORG` | 组织人员域 | 科室、职工 | 15 |
| `MAT` | 物资域 | 药品、耗材 | 33 |
| `AUTH` | 权限域 | 权限 | 26 |
| `FEE` | 费用域 | 收费 | 25 |
| `CLI` | 临床域 | 手术 | 22 |
| **合计** | | **7 个子模块** | **121** |

**全量表清单（121 张）：**

| # | 表名 | 中文名 | 所属子模块 | 主数据域 |
|---|---|---|---|---|
| 1 | `mdm_department` | 科室主表 | 科室 | ORG |
| 2 | `mdm_department_ext` | 科室扩展配置表 | 科室 | ORG |
| 3 | `mdm_department_relation` | 科室关系表 | 科室 | ORG |
| 4 | `mdm_department_change_log` | 变更日志表 | 科室 | ORG |
| 5 | `mdm_department_sync_log` | 同步日志表 | 科室 | ORG |
| 6 | `mdm_department_code_seq` | 编码序列表 | 科室 | ORG |
| 7 | `mdm_employee` | 职工主表 | 职工 | ORG |
| 8 | `mdm_employee_ext` | 职工扩展表 | 职工 | ORG |
| 9 | `mdm_employee_dept` | 职工任职关系表 | 职工 | ORG |
| 10 | `mdm_employee_license` | 执业资格/证书表 | 职工 | ORG |
| 11 | `mdm_employee_account` | 账号绑定表 | 职工 | ORG |
| 12 | `mdm_employee_signature` | 电子签名表 | 职工 | ORG |
| 13 | `mdm_employee_change_log` | 变更日志表 | 职工 | ORG |
| 14 | `mdm_employee_sync_log` | 同步日志表 | 职工 | ORG |
| 15 | `mdm_employee_code_seq` | 工号序列表 | 职工 | ORG |
| 16 | `mdm_drug` | 药品主表 | 药品 | MAT |
| 17 | `mdm_drug_ext` | 药品扩展表 | 药品 | MAT |
| 18 | `mdm_drug_alias` | 药品别名表 | 药品 | MAT |
| 19 | `mdm_drug_barcode` | 药品条码表 | 药品 | MAT |
| 20 | `mdm_drug_price` | 药品价格表 | 药品 | MAT |
| 21 | `mdm_drug_stock_policy` | 药品库存策略表 | 药品 | MAT |
| 22 | `mdm_drug_prescription` | 药品处方规则表 | 药品 | MAT |
| 23 | `mdm_drug_ddi` | 药品相互作用表 | 药品 | MAT |
| 24 | `mdm_drug_change_log` | 变更日志表 | 药品 | MAT |
| 25 | `mdm_drug_sync_log` | 同步日志表 | 药品 | MAT |
| 26 | `mdm_drug_code_seq` | 编码序列表 | 药品 | MAT |
| 27 | `mdm_material` | 耗材主表 | 耗材 | MAT |
| 28 | `mdm_material_ext` | 耗材扩展表 | 耗材 | MAT |
| 29 | `mdm_material_alias` | 耗材别名表 | 耗材 | MAT |
| 30 | `mdm_material_barcode` | 耗材条码 / UDI 表 | 耗材 | MAT |
| 31 | `mdm_material_price` | 耗材价格表 | 耗材 | MAT |
| 32 | `mdm_material_stock_policy` | 库存策略表 | 耗材 | MAT |
| 33 | `mdm_material_iol` | 人工晶体专档表 | 耗材 | MAT |
| 34 | `mdm_material_implant` | 植入物追溯配置表 | 耗材 | MAT |
| 35 | `mdm_material_reagent` | 检验试剂配置表 | 耗材 | MAT |
| 36 | `mdm_material_consumable_attr` | 耗材通用属性表 | 耗材 | MAT |
| 37 | `mdm_material_charge_rel` | 耗材-收费项目关联表 | 耗材 | MAT |
| 38 | `mdm_material_supplier_rel` | 供应商供货关系表 | 耗材 | MAT |
| 39 | `mdm_surgery_kit` | 手术套包主表 | 耗材 | MAT |
| 40 | `mdm_surgery_kit_detail` | 手术套包明细表 | 耗材 | MAT |
| 41 | `mdm_material_registration` | 注册证 / 资质证照表 | 耗材 | MAT |
| 42 | `mdm_material_change_log` | 变更日志表 | 耗材 | MAT |
| 43 | `mdm_material_approval` | 审批记录表 | 耗材 | MAT |
| 44 | `mdm_material_sync_log` | 同步日志表 | 耗材 | MAT |
| 45 | `mdm_material_code_seq` | 编码序列表 | 耗材 | MAT |
| 46 | `mdm_material_import_task` | 导入任务表 | 耗材 | MAT |
| 47 | `mdm_material_recall` | 耗材召回表 | 耗材 | MAT |
| 48 | `mdm_material_recall_detail` | 召回影响明细表 | 耗材 | MAT |
| 49 | `mdm_menu` | 菜单与功能点 | 权限 | AUTH |
| 50 | `mdm_role` | 角色 | 权限 | AUTH |
| 51 | `mdm_role_permission` | 角色权限 | 权限 | AUTH |
| 52 | `mdm_role_inherit` | 角色继承 | 权限 | AUTH |
| 53 | `mdm_role_api` | 角色接口白名单 | 权限 | AUTH |
| 54 | `mdm_role_conflict_rule` | 角色冲突规则 | 权限 | AUTH |
| 55 | `mdm_data_scope` | 数据权限范围 | 权限 | AUTH |
| 56 | `mdm_role_data_scope` | 角色数据权限 | 权限 | AUTH |
| 57 | `mdm_field_def` | 字段定义 / 敏感字段字典 | 权限 | AUTH |
| 58 | `mdm_role_field_perm` | 角色字段权限 | 权限 | AUTH |
| 59 | `mdm_second_factor_policy` | 二次验证策略 | 权限 | AUTH |
| 60 | `mdm_position` | 岗位 | 权限 | AUTH |
| 61 | `mdm_position_role` | 岗位默认角色 | 权限 | AUTH |
| 62 | `mdm_user_group` | 用户组 | 权限 | AUTH |
| 63 | `mdm_user_group_member` | 用户组成员 | 权限 | AUTH |
| 64 | `mdm_user_group_role` | 用户组角色 | 权限 | AUTH |
| 65 | `mdm_role_user` | 角色用户绑定 | 权限 | AUTH |
| 66 | `mdm_user_permission` | 用户直接权限 | 权限 | AUTH |
| 67 | `mdm_permission_template` | 权限模板 | 权限 | AUTH |
| 68 | `mdm_permission_template_item` | 权限模板明细 | 权限 | AUTH |
| 69 | `mdm_permission_apply` | 权限申请单 | 权限 | AUTH |
| 70 | `mdm_permission_apply_detail` | 权限申请明细 | 权限 | AUTH |
| 71 | `mdm_permission_change_log` | 权限变更日志 | 权限 | AUTH |
| 72 | `mdm_permission_version` | 权限版本快照 | 权限 | AUTH |
| 73 | `mdm_permission_sync_log` | 权限同步日志 | 权限 | AUTH |
| 74 | `mdm_permission_cache_task` | 权限缓存刷新任务 | 权限 | AUTH |
| 75 | `md_charge_item` | 收费项目主表 | 收费 | FEE |
| 76 | `md_charge_item_ext` | 收费项目扩展表 | 收费 | FEE |
| 77 | `md_charge_item_alias` | 收费项目别名表 | 收费 | FEE |
| 78 | `md_charge_item_rel` | 收费项目关联表 | 收费 | FEE |
| 79 | `md_charge_item_pricing_rule` | 计价规则表 | 收费 | FEE |
| 80 | `md_charge_item_field` | 收费项目自定义字段 | 收费 | FEE |
| 81 | `md_charge_item_discount_rel` | 项目优惠适用表 | 收费 | FEE |
| 82 | `md_price_list` | 价表主表 | 收费 | FEE |
| 83 | `md_price_item` | 价表明细表 | 收费 | FEE |
| 84 | `md_price_history` | 价格历史表 | 收费 | FEE |
| 85 | `md_price_adjust` | 调价单主表 | 收费 | FEE |
| 86 | `md_price_adjust_detail` | 调价明细表 | 收费 | FEE |
| 87 | `md_discount_policy` | 优惠方案表 | 收费 | FEE |
| 88 | `md_discount_policy_item` | 优惠适用项目表 | 收费 | FEE |
| 89 | `md_discount_policy_log` | 优惠使用记录表 | 收费 | FEE |
| 90 | `md_charge_combo` | 收费组合/套餐主表 | 收费 | FEE |
| 91 | `md_charge_combo_detail` | 套餐明细表 | 收费 | FEE |
| 92 | `md_payment_method` | 支付方式表 | 收费 | FEE |
| 93 | `md_refund_policy` | 退费规则表 | 收费 | FEE |
| 94 | `md_invoice_config` | 发票配置表 | 收费 | FEE |
| 95 | `md_invoice_number_segment` | 发票号码段表 | 收费 | FEE |
| 96 | `md_charge_change_log` | 变更日志表 | 收费 | FEE |
| 97 | `md_charge_sync_log` | 同步日志表 | 收费 | FEE |
| 98 | `md_charge_code_seq` | 编码序列表 | 收费 | FEE |
| 99 | `md_price_cache_task` | 价格缓存刷新任务表 | 收费 | FEE |
| 100 | `md_operation` | 手术项目主表 | 手术 | CLI |
| 101 | `md_operation_ext` | 手术项目扩展表 | 手术 | CLI |
| 102 | `md_operation_alias` | 手术项目别名表 | 手术 | CLI |
| 103 | `md_operation_anesthesia_rel` | 手术-麻醉关联表 | 手术 | CLI |
| 104 | `md_operation_prepare_rule` | 术前准备规则表 | 手术 | CLI |
| 105 | `md_operation_prepare_item` | 术前准备明细表 | 手术 | CLI |
| 106 | `md_operation_exam_item_rel` | 术前检查关联表 | 手术 | CLI |
| 107 | `md_operation_lab_item_rel` | 术前检验关联表 | 手术 | CLI |
| 108 | `md_operation_material_rel` | 手术-耗材关联表 | 手术 | CLI |
| 109 | `md_operation_iol_rel` | 手术-人工晶体关联表 | 手术 | CLI |
| 110 | `md_operation_implant` | 植入物手术配置表 | 手术 | CLI |
| 111 | `md_operation_staff_auth` | 手术医师授权表 | 手术 | CLI |
| 112 | `md_operation_followup_rule` | 术后随访规则表 | 手术 | CLI |
| 113 | `md_operation_charge_rel` | 手术收费关联表 | 手术 | CLI |
| 114 | `md_operation_template_rel` | 手术模板关联表 | 手术 | CLI |
| 115 | `md_anesthesia` | 麻醉方式主表 | 手术 | CLI |
| 116 | `md_anesthesia_drug` | 麻醉默认药品表 | 手术 | CLI |
| 117 | `md_surgery_level_rule` | 手术分级规则表 | 手术 | CLI |
| 118 | `md_operation_change_log` | 变更日志表 | 手术 | CLI |
| 119 | `md_operation_sync_log` | 同步日志表 | 手术 | CLI |
| 120 | `md_operation_code_seq` | 手术编码序列表 | 手术 | CLI |
| 121 | `md_operation_import_task` | 导入任务表 | 手术 | CLI |

---


### 1.9 跨模块关联关系总览

M01 各子模块之间通过**主键 ID 引用**（不建物理外键）建立关联，下图为主要跨子模块依赖：

```
┌─────────────────────┐          ┌─────────────────────┐
│ 科室 (ORG)           │◄─────────│ 职工 (ORG)          │
│ mdm_department      │  1:N     │ mdm_employee        │
└──────────┬──────────┘          └──────────┬──────────┘
           │                                 │
           │ 1:N（执行科室）                  │ 1:N（创建人/授权人）
           ▼                                 ▼
┌─────────────────────┐          ┌─────────────────────┐
│ 药品/耗材 (MAT)      │          │ 权限 (AUTH)          │
│ mdm_drug / material │          │ mdm_role_user       │
└──────────┬──────────┘          └─────────────────────┘
           │ 1:N（收费项关联）
           ▼
┌─────────────────────┐◄─────────┌─────────────────────┐
│ 收费 (FEE)           │  1:N     │ 手术 (CLI)          │
│ md_charge_item      │          │ md_operation        │
└─────────────────────┘          └─────────────────────┘
           ▲                                 │
           │ 手术费/材料费                     │ 手术-耗材/晶体关联
           └─────────────────────────────────┘
```

**关键关联路径：**

| 关联 | 起点表 | 终点表 | 关联字段 | 说明 |
|---|---|---|---|---|
| 科室 → 职工 | `mdm_department` | `mdm_employee` | `main_dept_id` | 职工主科室 |
| 科室 → 药品/耗材 | `mdm_department` | `mdm_drug` / `mdm_material` | `default_dept_id` | 默认执行科室 |
| 职工 → 权限 | `mdm_employee` | `mdm_role_user` | `staff_id` | 用户角色绑定 |
| 药品/耗材 → 收费 | `mdm_drug` / `mdm_material` | `md_charge_item_rel` | `rel_object_id` | 物资对应收费项目 |
| 手术 → 收费 | `md_operation` | `md_operation_charge_rel` | `charge_item_id` | 手术费收费项 |
| 手术 → 耗材 | `md_operation` | `md_operation_material_rel` | `material_id` | 手术必用耗材 |
| 手术 → 晶体 | `md_operation` | `md_operation_iol_rel` | `iol_id` | 适配人工晶体 |
| 手术 → 套包 | `md_operation` | `mdm_surgery_kit` | `operation_id` | 手术套包 |
| 权限 → 菜单 | `mdm_role` | `mdm_role_permission` | `role_id` / `menu_id` | 角色权限 |

> **引用完整性约定**：被引用表执行逻辑删除前，必须通过「引用检查」接口确认无下游引用；引用检查逻辑见各子模块文档（如 `GET /api/v1/mdm/{object}/{id}/references`）。

---

## 01. 科室数据结构

> **来源：** [科室详细设计](M01_主数据管理MDM_01_科室_详细设计.md) · 第 4 章
> **主数据域：** 组织人员域（`ORG`） · **表数：** 6

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 01.2 | `mdm_department` | 科室主表 |
| 01.3 | `mdm_department_ext` | 科室扩展配置表 |
| 01.4 | `mdm_department_relation` | 科室关系表 |
| 01.5 | `mdm_department_change_log` | 变更日志表 |
| 01.6 | `mdm_department_sync_log` | 同步日志表 |
| 01.7 | `mdm_department_code_seq` | 编码序列表 |

---

### 01.1 ER 关系图

```
┌────────────────────────────┐        ┌────────────────────────────┐
│  mdm_department            │ 1   1  │  mdm_department_ext        │
│  （科室主表）               │◄──────►│  （科室扩展配置表）          │
└────────────┬───────────────┘        └────────────────────────────┘
             │
             │ 1
             │
             ├──► N  mdm_department_relation    （科室关系表）
             ├──► N  mdm_department_change_log  （变更日志表）
             ├──► N  mdm_department_sync_log    （同步日志表）
             └──► N  mdm_department_code_seq    （编码序列表）
```

### 01.2 表：`mdm_department`（科室主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| dept_code | VARCHAR(32) | N | - | 科室编码，全局唯一 |
| dept_name | VARCHAR(128) | N | - | 科室名称（全称） |
| dept_short_name | VARCHAR(64) | Y | NULL | 科室简称 |
| dept_alias | VARCHAR(255) | Y | NULL | 别名（多别名逗号分隔，用于搜索） |
| pinyin_code | VARCHAR(64) | N | - | 拼音码（自动生成，如 `bnyk`） |
| wubi_code | VARCHAR(64) | Y | NULL | 五笔码（可选） |
| dept_type | VARCHAR(32) | N | - | 科室业务类型，见 3.1 |
| dept_category | VARCHAR(32) | Y | NULL | 科室分类（细分，取自字典 DEPT_CATEGORY） |
| parent_id | BIGINT UNSIGNED | Y | NULL | 父科室ID，顶级为 NULL |
| dept_level | TINYINT | N | 1 | 层级（1/2/3） |
| dept_path | VARCHAR(255) | N | - | 路径（如 `/1/12/128/`），用于子树查询 |
| sort_order | INT | N | 100 | 同级排序，值越小越靠前 |
| campus_code | VARCHAR(32) | Y | NULL | 院区编码 |
| location | VARCHAR(255) | Y | NULL | 位置描述（如"门诊楼3楼东区"） |
| phone | VARCHAR(32) | Y | NULL | 联系电话 |
| leader_emp_id | BIGINT UNSIGNED | Y | NULL | 科室负责人（职工ID） |
| nurse_leader_emp_id | BIGINT UNSIGNED | Y | NULL | 护理负责人（职工ID） |
| is_outpatient | TINYINT(1) | N | 0 | 门诊属性 |
| is_inpatient | TINYINT(1) | N | 0 | 住院属性 |
| is_surgery | TINYINT(1) | N | 0 | 手术属性 |
| is_medical_tech | TINYINT(1) | N | 0 | 医技属性 |
| is_pharmacy | TINYINT(1) | N | 0 | 药房属性 |
| is_optometry | TINYINT(1) | N | 0 | 视光属性 |
| is_refraction | TINYINT(1) | N | 0 | 屈光属性 |
| is_emergency | TINYINT(1) | N | 0 | 急诊属性 |
| is_registrable | TINYINT(1) | N | 0 | 是否可挂号 |
| is_orderable | TINYINT(1) | N | 0 | 是否可开单 |
| is_leaf | TINYINT(1) | N | 1 | 是否叶子节点 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expiry_date | DATE | Y | NULL | 失效日期 |
| status | VARCHAR(16) | N | 'ENABLED' | 业务状态：ENABLED / DISABLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态：DRAFT / PENDING / APPROVED / REJECTED |
| version | INT | N | 0 | 乐观锁版本号 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_dept | PRIMARY | id | 主键 |
| uk_dept_code | UNIQUE | dept_code, deleted | 编码唯一（考虑逻辑删除） |
| idx_parent | NORMAL | parent_id | 父子查询 |
| idx_path | NORMAL | dept_path | 子树查询 |
| idx_type | NORMAL | dept_type | 类型过滤 |
| idx_status | NORMAL | status | 状态过滤 |
| idx_campus | NORMAL | campus_code | 院区过滤 |
| idx_pinyin | NORMAL | pinyin_code | 拼音搜索 |
| idx_updated | NORMAL | updated_at | 增量同步 |

**DDL 示例（MySQL 8.0）**

```sql
CREATE TABLE `mdm_department` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `dept_code` VARCHAR(32) NOT NULL COMMENT '科室编码',
  `dept_name` VARCHAR(128) NOT NULL COMMENT '科室名称',
  `dept_short_name` VARCHAR(64) DEFAULT NULL COMMENT '科室简称',
  `dept_alias` VARCHAR(255) DEFAULT NULL COMMENT '别名',
  `pinyin_code` VARCHAR(64) NOT NULL COMMENT '拼音码',
  `wubi_code` VARCHAR(64) DEFAULT NULL COMMENT '五笔码',
  `dept_type` VARCHAR(32) NOT NULL COMMENT '科室类型',
  `dept_category` VARCHAR(32) DEFAULT NULL COMMENT '科室分类',
  `parent_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '父科室ID',
  `dept_level` TINYINT NOT NULL DEFAULT 1 COMMENT '层级',
  `dept_path` VARCHAR(255) NOT NULL DEFAULT '/' COMMENT '路径',
  `sort_order` INT NOT NULL DEFAULT 100 COMMENT '排序',
  `campus_code` VARCHAR(32) DEFAULT NULL COMMENT '院区编码',
  `location` VARCHAR(255) DEFAULT NULL COMMENT '位置',
  `phone` VARCHAR(32) DEFAULT NULL COMMENT '电话',
  `leader_emp_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '负责人',
  `nurse_leader_emp_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '护理负责人',
  `is_outpatient` TINYINT(1) NOT NULL DEFAULT 0,
  `is_inpatient` TINYINT(1) NOT NULL DEFAULT 0,
  `is_surgery` TINYINT(1) NOT NULL DEFAULT 0,
  `is_medical_tech` TINYINT(1) NOT NULL DEFAULT 0,
  `is_pharmacy` TINYINT(1) NOT NULL DEFAULT 0,
  `is_optometry` TINYINT(1) NOT NULL DEFAULT 0,
  `is_refraction` TINYINT(1) NOT NULL DEFAULT 0,
  `is_emergency` TINYINT(1) NOT NULL DEFAULT 0,
  `is_registrable` TINYINT(1) NOT NULL DEFAULT 0,
  `is_orderable` TINYINT(1) NOT NULL DEFAULT 0,
  `is_leaf` TINYINT(1) NOT NULL DEFAULT 1,
  `effective_date` DATE DEFAULT NULL,
  `expiry_date` DATE DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ENABLED',
  `audit_status` VARCHAR(16) NOT NULL DEFAULT 'APPROVED',
  `version` INT NOT NULL DEFAULT 0,
  `remark` VARCHAR(512) DEFAULT NULL,
  `created_by` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` BIGINT UNSIGNED DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dept_code` (`dept_code`, `deleted`),
  KEY `idx_parent` (`parent_id`),
  KEY `idx_path` (`dept_path`),
  KEY `idx_type` (`dept_type`),
  KEY `idx_status` (`status`),
  KEY `idx_campus` (`campus_code`),
  KEY `idx_pinyin` (`pinyin_code`),
  KEY `idx_updated` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室主数据表';
```

### 01.3 表：`mdm_department_ext`（科室扩展配置表）

| 字段名 | 类型 | 允许空 | 说明 |
|---|---|---|---|
| dept_id | BIGINT UNSIGNED | N | 主键，与主表 1:1 |
| default_reg_fee_code | VARCHAR(64) | Y | 默认挂号费收费项目编码 |
| default_clinic_fee_code | VARCHAR(64) | Y | 默认诊查费编码 |
| queue_prefix | VARCHAR(8) | Y | 叫号队列前缀（如 A、B、C） |
| print_template_code | VARCHAR(64) | Y | 打印模板编码 |
| default_warehouse_code | VARCHAR(64) | Y | 默认领用仓库（药房/耗材） |
| default_account_code | VARCHAR(64) | Y | 默认会计科目 |
| cost_center_code | VARCHAR(64) | Y | 成本核算中心编码 |
| third_party_codes | JSON | Y | 第三方编码映射：`{"his":"...","insurance":"...","region":"..."}` |
| ext_config | JSON | Y | 其他扩展配置（叫号规则、分诊规则等） |
| created_at | DATETIME | N | 创建时间 |
| updated_at | DATETIME | N | 更新时间 |

```sql
CREATE TABLE `mdm_department_ext` (
  `dept_id` BIGINT UNSIGNED NOT NULL,
  `default_reg_fee_code` VARCHAR(64) DEFAULT NULL,
  `default_clinic_fee_code` VARCHAR(64) DEFAULT NULL,
  `queue_prefix` VARCHAR(8) DEFAULT NULL,
  `print_template_code` VARCHAR(64) DEFAULT NULL,
  `default_warehouse_code` VARCHAR(64) DEFAULT NULL,
  `default_account_code` VARCHAR(64) DEFAULT NULL,
  `cost_center_code` VARCHAR(64) DEFAULT NULL,
  `third_party_codes` JSON DEFAULT NULL,
  `ext_config` JSON DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`dept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室扩展配置';
```

### 01.4 表：`mdm_department_relation`（科室关系表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| dept_id | BIGINT UNSIGNED | 科室ID |
| relation_type | VARCHAR(32) | 关系类型：`OUTPATIENT_TO_INPATIENT`（门诊↔住院）、`CLINIC_TO_WARD`（诊室↔病区）、`SURGERY_TO_OR`（手术科室↔手术室）、`OPTICAL_TO_REFUND` 等 |
| target_dept_id | BIGINT UNSIGNED | 目标科室ID |
| sort_order | INT | 排序 |
| created_at | DATETIME | 创建时间 |

```sql
CREATE TABLE `mdm_department_relation` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `dept_id` BIGINT UNSIGNED NOT NULL,
  `relation_type` VARCHAR(32) NOT NULL,
  `target_dept_id` BIGINT UNSIGNED NOT NULL,
  `sort_order` INT NOT NULL DEFAULT 100,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_relation` (`dept_id`, `relation_type`, `target_dept_id`),
  KEY `idx_target` (`target_dept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室关系表';
```

### 01.5 表：`mdm_department_change_log`（变更日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| dept_id | BIGINT UNSIGNED | 科室ID |
| dept_code | VARCHAR(32) | 科室编码（冗余） |
| action | VARCHAR(32) | 动作：CREATE / UPDATE / DELETE / ENABLE / DISABLE / MOVE / IMPORT / SYNC |
| before_data | JSON | 变更前数据 |
| after_data | JSON | 变更后数据 |
| diff_fields | JSON | 差异字段列表 |
| operator_id | BIGINT UNSIGNED | 操作人 |
| operator_name | VARCHAR(64) | 操作人姓名（冗余） |
| operator_ip | VARCHAR(64) | 操作IP |
| trace_id | VARCHAR(64) | 链路追踪ID |
| created_at | DATETIME | 操作时间 |

```sql
CREATE TABLE `mdm_department_change_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `dept_id` BIGINT UNSIGNED NOT NULL,
  `dept_code` VARCHAR(32) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `before_data` JSON DEFAULT NULL,
  `after_data` JSON DEFAULT NULL,
  `diff_fields` JSON DEFAULT NULL,
  `operator_id` BIGINT UNSIGNED NOT NULL,
  `operator_name` VARCHAR(64) DEFAULT NULL,
  `operator_ip` VARCHAR(64) DEFAULT NULL,
  `trace_id` VARCHAR(64) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_dept` (`dept_id`, `created_at`),
  KEY `idx_code` (`dept_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室变更日志';
```

### 01.6 表：`mdm_department_sync_log`（同步日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| batch_no | VARCHAR(64) | 批次号 |
| dept_id | BIGINT UNSIGNED | 科室ID |
| dept_code | VARCHAR(32) | 科室编码 |
| target_system | VARCHAR(64) | 目标系统：OUTPATIENT / INPATIENT / DOCTOR_STATION / NURSE_STATION / CHARGE / PHARMACY / OPTICAL / REFRACTION / LIS / PACS / MOBILE / REPORT |
| action | VARCHAR(32) | UPSERT / DELETE |
| status | VARCHAR(16) | SUCCESS / FAILED / RETRYING |
| payload | JSON | 推送内容 |
| response | TEXT | 响应内容 |
| retry_count | INT | 重试次数 |
| error_message | VARCHAR(512) | 错误信息 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

```sql
CREATE TABLE `mdm_department_sync_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `batch_no` VARCHAR(64) NOT NULL,
  `dept_id` BIGINT UNSIGNED NOT NULL,
  `dept_code` VARCHAR(32) NOT NULL,
  `target_system` VARCHAR(64) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `status` VARCHAR(16) NOT NULL,
  `payload` JSON DEFAULT NULL,
  `response` TEXT DEFAULT NULL,
  `retry_count` INT NOT NULL DEFAULT 0,
  `error_message` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_batch` (`batch_no`),
  KEY `idx_dept` (`dept_id`),
  KEY `idx_status` (`status`, `target_system`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室同步日志';
```

### 01.7 表：`mdm_department_code_seq`（编码序列表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| prefix | VARCHAR(8) | 前缀（主键） |
| current_value | INT | 当前序号 |
| step | INT | 步长（默认1） |
| updated_at | DATETIME | 更新时间 |

```sql
CREATE TABLE `mdm_department_code_seq` (
  `prefix` VARCHAR(8) NOT NULL,
  `current_value` INT NOT NULL DEFAULT 0,
  `step` INT NOT NULL DEFAULT 1,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科室编码序列';
```

### 01.8 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/department.py
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime,
    Index, UniqueConstraint, JSON, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Department(Base):
    __tablename__ = "mdm_department"
    __table_args__ = (
        UniqueConstraint("dept_code", "deleted", name="uk_dept_code"),
        Index("idx_parent", "parent_id"),
        Index("idx_path", "dept_path"),
        Index("idx_type", "dept_type"),
        Index("idx_status", "status"),
        Index("idx_campus", "campus_code"),
        Index("idx_pinyin", "pinyin_code"),
        Index("idx_updated", "updated_at"),
        {"comment": "科室主数据表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dept_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="科室编码")
    dept_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="科室名称")
    dept_short_name: Mapped[Optional[str]] = mapped_column(String(64))
    dept_alias: Mapped[Optional[str]] = mapped_column(String(255))
    pinyin_code: Mapped[str] = mapped_column(String(64), nullable=False)
    wubi_code: Mapped[Optional[str]] = mapped_column(String(64))

    dept_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dept_category: Mapped[Optional[str]] = mapped_column(String(32))

    parent_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    dept_level: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    dept_path: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    campus_code: Mapped[Optional[str]] = mapped_column(String(32))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    leader_emp_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    nurse_leader_emp_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    is_outpatient: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_inpatient: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_surgery: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_medical_tech: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_pharmacy: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_optometry: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_refraction: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_emergency: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_registrable: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_orderable: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_leaf: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    remark: Mapped[Optional[str]] = mapped_column(String(512))

    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    ext: Mapped[Optional["DepartmentExt"]] = relationship(
        "DepartmentExt", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )


class DepartmentExt(Base):
    __tablename__ = "mdm_department_ext"

    dept_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mdm_department.id"), primary_key=True)
    default_reg_fee_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_clinic_fee_code: Mapped[Optional[str]] = mapped_column(String(64))
    queue_prefix: Mapped[Optional[str]] = mapped_column(String(8))
    print_template_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_warehouse_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_account_code: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center_code: Mapped[Optional[str]] = mapped_column(String(64))
    third_party_codes: Mapped[Optional[dict]] = mapped_column(JSON)
    ext_config: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DepartmentChangeLog(Base):
    __tablename__ = "mdm_department_change_log"
    __table_args__ = (
        Index("idx_dept", "dept_id", "created_at"),
        Index("idx_code", "dept_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dept_code: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_data: Mapped[Optional[dict]] = mapped_column(JSON)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON)
    diff_fields: Mapped[Optional[list]] = mapped_column(JSON)
    operator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DepartmentSyncLog(Base):
    __tablename__ = "mdm_department_sync_log"
    __table_args__ = (
        Index("idx_batch", "batch_no"),
        Index("idx_dept", "dept_id"),
        Index("idx_status", "status", "target_system"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False)
    dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dept_code: Mapped[str] = mapped_column(String(32), nullable=False)
    target_system: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    response: Mapped[Optional[str]] = mapped_column(String)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 01.9 Pydantic Schema 定义

```python
# app/schemas/mdm/department.py
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class DepartmentBase(BaseModel):
    dept_name: str = Field(..., max_length=128, description="科室名称")
    dept_short_name: Optional[str] = Field(None, max_length=64)
    dept_alias: Optional[str] = Field(None, max_length=255)
    dept_type: str = Field(..., description="科室类型")
    dept_category: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 100
    campus_code: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=32)
    leader_emp_id: Optional[int] = None
    nurse_leader_emp_id: Optional[int] = None

    is_outpatient: bool = False
    is_inpatient: bool = False
    is_surgery: bool = False
    is_medical_tech: bool = False
    is_pharmacy: bool = False
    is_optometry: bool = False
    is_refraction: bool = False
    is_emergency: bool = False
    is_registrable: bool = False
    is_orderable: bool = False

    effective_date: Optional[date] = None
    expiry_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)


class DepartmentExtSchema(BaseModel):
    default_reg_fee_code: Optional[str] = None
    default_clinic_fee_code: Optional[str] = None
    queue_prefix: Optional[str] = Field(None, max_length=8)
    print_template_code: Optional[str] = None
    default_warehouse_code: Optional[str] = None
    default_account_code: Optional[str] = None
    cost_center_code: Optional[str] = None
    third_party_codes: Optional[Dict[str, str]] = None
    ext_config: Optional[Dict[str, Any]] = None


class DepartmentCreate(DepartmentBase):
    dept_code: Optional[str] = Field(None, description="科室编码，为空则自动生成")
    ext: Optional[DepartmentExtSchema] = None

    @field_validator("expiry_date")
    @classmethod
    def validate_dates(cls, v, info):
        eff = info.data.get("effective_date")
        if v and eff and v < eff:
            raise ValueError("失效日期不能早于生效日期")
        return v


class DepartmentUpdate(DepartmentBase):
    version: int = Field(..., description="乐观锁版本号")
    ext: Optional[DepartmentExtSchema] = None


class DepartmentStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(ENABLED|DISABLED)$")
    reason: Optional[str] = Field(None, max_length=255)


class DepartmentMoveRequest(BaseModel):
    target_parent_id: Optional[int] = None
    sort_order: int = 100
    version: int


class DepartmentQuery(BaseModel):
    keyword: Optional[str] = None
    dept_type: Optional[str] = None
    dept_category: Optional[str] = None
    parent_id: Optional[int] = None
    campus_code: Optional[str] = None
    status: Optional[str] = None
    is_outpatient: Optional[bool] = None
    is_inpatient: Optional[bool] = None
    is_registrable: Optional[bool] = None
    include_children: bool = False
    page: int = 1
    page_size: int = 20
    sort_by: str = "sort_order"
    sort_dir: str = "asc"


class DepartmentTreeQuery(BaseModel):
    campus_code: Optional[str] = None
    dept_type: Optional[str] = None
    status: Optional[str] = "ENABLED"
    max_level: int = 3
    only_leaf: bool = False


class DepartmentVO(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dept_code: str
    pinyin_code: str
    dept_level: int
    dept_path: str
    is_leaf: bool
    status: str
    audit_status: str
    version: int
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    ext: Optional[DepartmentExtSchema] = None
    children: Optional[List["DepartmentVO"]] = None


class DepartmentSimpleVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    dept_code: str
    dept_name: str
    dept_short_name: Optional[str]
    dept_type: str
    parent_id: Optional[int]
    pinyin_code: str
    status: str


class PageResult(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int


DepartmentVO.model_rebuild()
```

---

---

## 02. 职工数据结构

> **来源：** [职工详细设计](M01_主数据管理MDM_02_职工_详细设计.md) · 第 4 章
> **主数据域：** 组织人员域（`ORG`） · **表数：** 9

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 02.2 | `mdm_employee` | 职工主表 |
| 02.3 | `mdm_employee_ext` | 职工扩展表 |
| 02.4 | `mdm_employee_dept` | 职工任职关系表 |
| 02.5 | `mdm_employee_license` | 执业资格/证书表 |
| 02.6 | `mdm_employee_account` | 账号绑定表 |
| 02.7 | `mdm_employee_signature` | 电子签名表 |
| 02.8 | `mdm_employee_change_log` | 变更日志表 |
| 02.9 | `mdm_employee_sync_log` | 同步日志表 |
| 02.10 | `mdm_employee_code_seq` | 工号序列表 |

---

### 02.1 ER 关系图

```
┌────────────────────────────┐        ┌────────────────────────────┐
│  mdm_employee              │ 1   1  │  mdm_employee_ext          │
│  （职工主表）               │◄──────►│  （职工扩展表）             │
└────────────┬───────────────┘        └────────────────────────────┘
             │
             │ 1
             │
             ├──► N  mdm_employee_dept        （职工任职关系表）
             ├──► N  mdm_employee_license     （执业资格/证书表）
             ├──► N  mdm_employee_account     （账号绑定表）
             ├──► N  mdm_employee_signature   （电子签名表）
             ├──► N  mdm_employee_change_log  （变更日志表）
             ├──► N  mdm_employee_sync_log    （同步日志表）
             └──► N  mdm_employee_code_seq    （工号序列表）
```

### 02.2 表：`mdm_employee`（职工主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| emp_code | VARCHAR(32) | N | - | 工号，全局唯一 |
| emp_name | VARCHAR(64) | N | - | 姓名 |
| emp_name_pinyin | VARCHAR(128) | N | - | 姓名拼音（全拼） |
| emp_name_pinyin_short | VARCHAR(32) | N | - | 姓名拼音首字母 |
| gender | VARCHAR(8) | N | - | 性别：MALE / FEMALE / UNKNOWN |
| birth_date | DATE | Y | NULL | 出生日期 |
| id_card_type | VARCHAR(16) | Y | NULL | 证件类型：ID_CARD / PASSPORT / ... |
| id_card_no | VARCHAR(128) | Y | NULL | 证件号码（加密存储） |
| id_card_no_hash | CHAR(64) | Y | NULL | 证件号码哈希（用于唯一性校验） |
| phone | VARCHAR(32) | Y | NULL | 手机号（加密存储） |
| phone_hash | CHAR(64) | Y | NULL | 手机号哈希 |
| email | VARCHAR(128) | Y | NULL | 邮箱 |
| nation | VARCHAR(32) | Y | NULL | 民族（字典） |
| native_place | VARCHAR(128) | Y | NULL | 籍贯 |
| marital_status | VARCHAR(16) | Y | NULL | 婚姻状况 |
| education | VARCHAR(32) | Y | NULL | 学历（字典） |
| degree | VARCHAR(32) | Y | NULL | 学位（字典） |
| graduate_school | VARCHAR(128) | Y | NULL | 毕业院校 |
| major | VARCHAR(128) | Y | NULL | 专业 |
| graduation_date | DATE | Y | NULL | 毕业日期 |
| political_status | VARCHAR(32) | Y | NULL | 政治面貌 |
| address | VARCHAR(255) | Y | NULL | 现住址 |
| emergency_contact | VARCHAR(64) | Y | NULL | 紧急联系人 |
| emergency_phone | VARCHAR(32) | Y | NULL | 紧急联系电话 |
| photo_url | VARCHAR(255) | Y | NULL | 照片 URL |
| emp_type | VARCHAR(32) | N | 'REGULAR' | 职工类型 |
| emp_status | VARCHAR(32) | N | 'ACTIVE' | 职工状态 |
| emp_category | VARCHAR(32) | N | - | 岗位类别 |
| primary_dept_id | BIGINT UNSIGNED | Y | NULL | 主科室 ID |
| title | VARCHAR(32) | Y | NULL | 职称 |
| title_level | VARCHAR(16) | Y | NULL | 职称级别 |
| position | VARCHAR(32) | Y | NULL | 职务 |
| position_level | VARCHAR(16) | Y | NULL | 职务级别 |
| employment_date | DATE | Y | NULL | 入职日期 |
| regular_date | DATE | Y | NULL | 转正日期 |
| leave_date | DATE | Y | NULL | 离职日期 |
| retirement_date | DATE | Y | NULL | 退休日期 |
| doctor_level | VARCHAR(32) | Y | NULL | 医生级别（住院/主治/副主任/主任） |
| is_prescriber | TINYINT(1) | N | 0 | 可开处方 |
| is_operator | TINYINT(1) | N | 0 | 可手术 |
| is_anesthetist | TINYINT(1) | N | 0 | 可麻醉 |
| is_report_signer | TINYINT(1) | N | 0 | 可签发报告 |
| is_optometrist | TINYINT(1) | N | 0 | 可验光 |
| is_optical_seller | TINYINT(1) | N | 0 | 可配镜销售 |
| is_refraction_consultant | TINYINT(1) | N | 0 | 可屈光咨询 |
| is_cashier | TINYINT(1) | N | 0 | 可收费 |
| is_dispenser | TINYINT(1) | N | 0 | 可发药 |
| is_prescription_reviewer | TINYINT(1) | N | 0 | 可审核处方 |
| is_nurse_executor | TINYINT(1) | N | 0 | 可护理执行 |
| is_queue_caller | TINYINT(1) | N | 0 | 可叫号 |
| is_mobile_user | TINYINT(1) | N | 0 | 可移动办公 |
| status | VARCHAR(16) | N | 'ENABLED' | 业务状态：ENABLED / DISABLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_emp | PRIMARY | id | 主键 |
| uk_emp_code | UNIQUE | emp_code, deleted | 工号唯一 |
| uk_id_card | UNIQUE | id_card_no_hash, deleted | 证件号唯一 |
| uk_phone | UNIQUE | phone_hash, deleted | 手机号唯一 |
| idx_name | NORMAL | emp_name | 姓名查询 |
| idx_pinyin | NORMAL | emp_name_pinyin, emp_name_pinyin_short | 拼音搜索 |
| idx_category | NORMAL | emp_category | 类别过滤 |
| idx_primary_dept | NORMAL | primary_dept_id | 主科室过滤 |
| idx_status | NORMAL | emp_status, status | 状态过滤 |
| idx_updated | NORMAL | updated_at | 增量同步 |

**DDL 示例**

```sql
CREATE TABLE `mdm_employee` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_code` VARCHAR(32) NOT NULL COMMENT '工号',
  `emp_name` VARCHAR(64) NOT NULL COMMENT '姓名',
  `emp_name_pinyin` VARCHAR(128) NOT NULL COMMENT '姓名全拼',
  `emp_name_pinyin_short` VARCHAR(32) NOT NULL COMMENT '姓名拼音首字母',
  `gender` VARCHAR(8) NOT NULL COMMENT '性别',
  `birth_date` DATE DEFAULT NULL,
  `id_card_type` VARCHAR(16) DEFAULT NULL,
  `id_card_no` VARCHAR(128) DEFAULT NULL COMMENT '证件号（加密）',
  `id_card_no_hash` CHAR(64) DEFAULT NULL COMMENT '证件号哈希',
  `phone` VARCHAR(32) DEFAULT NULL COMMENT '手机号（加密）',
  `phone_hash` CHAR(64) DEFAULT NULL COMMENT '手机号哈希',
  `email` VARCHAR(128) DEFAULT NULL,
  `nation` VARCHAR(32) DEFAULT NULL,
  `native_place` VARCHAR(128) DEFAULT NULL,
  `marital_status` VARCHAR(16) DEFAULT NULL,
  `education` VARCHAR(32) DEFAULT NULL,
  `degree` VARCHAR(32) DEFAULT NULL,
  `graduate_school` VARCHAR(128) DEFAULT NULL,
  `major` VARCHAR(128) DEFAULT NULL,
  `graduation_date` DATE DEFAULT NULL,
  `political_status` VARCHAR(32) DEFAULT NULL,
  `address` VARCHAR(255) DEFAULT NULL,
  `emergency_contact` VARCHAR(64) DEFAULT NULL,
  `emergency_phone` VARCHAR(32) DEFAULT NULL,
  `photo_url` VARCHAR(255) DEFAULT NULL,
  `emp_type` VARCHAR(32) NOT NULL DEFAULT 'REGULAR',
  `emp_status` VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
  `emp_category` VARCHAR(32) NOT NULL,
  `primary_dept_id` BIGINT UNSIGNED DEFAULT NULL,
  `title` VARCHAR(32) DEFAULT NULL,
  `title_level` VARCHAR(16) DEFAULT NULL,
  `position` VARCHAR(32) DEFAULT NULL,
  `position_level` VARCHAR(16) DEFAULT NULL,
  `employment_date` DATE DEFAULT NULL,
  `regular_date` DATE DEFAULT NULL,
  `leave_date` DATE DEFAULT NULL,
  `retirement_date` DATE DEFAULT NULL,
  `doctor_level` VARCHAR(32) DEFAULT NULL,
  `is_prescriber` TINYINT(1) NOT NULL DEFAULT 0,
  `is_operator` TINYINT(1) NOT NULL DEFAULT 0,
  `is_anesthetist` TINYINT(1) NOT NULL DEFAULT 0,
  `is_report_signer` TINYINT(1) NOT NULL DEFAULT 0,
  `is_optometrist` TINYINT(1) NOT NULL DEFAULT 0,
  `is_optical_seller` TINYINT(1) NOT NULL DEFAULT 0,
  `is_refraction_consultant` TINYINT(1) NOT NULL DEFAULT 0,
  `is_cashier` TINYINT(1) NOT NULL DEFAULT 0,
  `is_dispenser` TINYINT(1) NOT NULL DEFAULT 0,
  `is_prescription_reviewer` TINYINT(1) NOT NULL DEFAULT 0,
  `is_nurse_executor` TINYINT(1) NOT NULL DEFAULT 0,
  `is_queue_caller` TINYINT(1) NOT NULL DEFAULT 0,
  `is_mobile_user` TINYINT(1) NOT NULL DEFAULT 0,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ENABLED',
  `audit_status` VARCHAR(16) NOT NULL DEFAULT 'APPROVED',
  `version` INT NOT NULL DEFAULT 0,
  `remark` VARCHAR(512) DEFAULT NULL,
  `created_by` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_by` BIGINT UNSIGNED DEFAULT NULL,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `deleted` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_emp_code` (`emp_code`, `deleted`),
  UNIQUE KEY `uk_id_card` (`id_card_no_hash`, `deleted`),
  UNIQUE KEY `uk_phone` (`phone_hash`, `deleted`),
  KEY `idx_name` (`emp_name`),
  KEY `idx_pinyin` (`emp_name_pinyin`, `emp_name_pinyin_short`),
  KEY `idx_category` (`emp_category`),
  KEY `idx_primary_dept` (`primary_dept_id`),
  KEY `idx_status` (`emp_status`, `status`),
  KEY `idx_updated` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工主数据表';
```

### 02.3 表：`mdm_employee_ext`（职工扩展表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| emp_id | BIGINT UNSIGNED | 主键，1:1 |
| id_card_front_url | VARCHAR(255) | 身份证正面 |
| id_card_back_url | VARCHAR(255) | 身份证反面 |
| bank_name | VARCHAR(128) | 开户行 |
| bank_account | VARCHAR(128) | 银行账号（加密） |
| social_security_no | VARCHAR(64) | 社保号 |
| medical_insurance_no | VARCHAR(64) | 医保号（预留） |
| hukou_address | VARCHAR(255) | 户口地址 |
| hukou_type | VARCHAR(16) | 户口性质 |
| contract_no | VARCHAR(64) | 合同编号 |
| contract_start_date | DATE | 合同开始 |
| contract_end_date | DATE | 合同结束 |
| probation_months | INT | 试用期月数 |
| annual_leave_days | INT | 年假天数 |
| base_salary | DECIMAL(12,2) | 基本工资（加密） |
| performance_config | JSON | 绩效配置 |
| third_party_codes | JSON | 第三方编码映射 |
| ext_config | JSON | 其他扩展 |
| remark | VARCHAR(512) | 备注 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_ext` (
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `id_card_front_url` VARCHAR(255) DEFAULT NULL,
  `id_card_back_url` VARCHAR(255) DEFAULT NULL,
  `bank_name` VARCHAR(128) DEFAULT NULL,
  `bank_account` VARCHAR(128) DEFAULT NULL,
  `social_security_no` VARCHAR(64) DEFAULT NULL,
  `medical_insurance_no` VARCHAR(64) DEFAULT NULL,
  `hukou_address` VARCHAR(255) DEFAULT NULL,
  `hukou_type` VARCHAR(16) DEFAULT NULL,
  `contract_no` VARCHAR(64) DEFAULT NULL,
  `contract_start_date` DATE DEFAULT NULL,
  `contract_end_date` DATE DEFAULT NULL,
  `probation_months` INT DEFAULT NULL,
  `annual_leave_days` INT DEFAULT NULL,
  `base_salary` DECIMAL(12,2) DEFAULT NULL,
  `performance_config` JSON DEFAULT NULL,
  `third_party_codes` JSON DEFAULT NULL,
  `ext_config` JSON DEFAULT NULL,
  `remark` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`emp_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工扩展表';
```

### 02.4 表：`mdm_employee_dept`（职工任职关系表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| dept_id | BIGINT UNSIGNED | 科室ID |
| relation_type | VARCHAR(32) | 任职类型：PRIMARY / SECONDARY / NURSING / CONSULT / SURGERY |
| position | VARCHAR(32) | 在该科室的职务 |
| title | VARCHAR(32) | 在该科室的职称 |
| is_primary | TINYINT(1) | 是否主科室 |
| start_date | DATE | 开始日期 |
| end_date | DATE | 结束日期 |
| status | VARCHAR(16) | 状态：ENABLED / DISABLED |
| sort_order | INT | 排序 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_dept` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `dept_id` BIGINT UNSIGNED NOT NULL,
  `relation_type` VARCHAR(32) NOT NULL DEFAULT 'PRIMARY',
  `position` VARCHAR(32) DEFAULT NULL,
  `title` VARCHAR(32) DEFAULT NULL,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  `start_date` DATE DEFAULT NULL,
  `end_date` DATE DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ENABLED',
  `sort_order` INT NOT NULL DEFAULT 100,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_emp_dept_type` (`emp_id`, `dept_id`, `relation_type`),
  KEY `idx_dept` (`dept_id`),
  KEY `idx_emp` (`emp_id`),
  KEY `idx_primary` (`emp_id`, `is_primary`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工任职关系';
```

### 02.5 表：`mdm_employee_license`（执业资格/证书表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| license_type | VARCHAR(32) | 类型：DOCTOR_QUALIFICATION / DOCTOR_PRACTICE / NURSE_PRACTICE / PHARMACIST / LARGE_EQUIPMENT / TITLE_CERT / DEGREE_CERT / DIPLOMA / OPTOMETRIST / OTHER |
| license_no | VARCHAR(64) | 证书编号 |
| license_name | VARCHAR(128) | 证书名称 |
| issuing_authority | VARCHAR(128) | 发证机关 |
| issue_date | DATE | 发证日期 |
| expiry_date | DATE | 有效期至 |
| scope | VARCHAR(255) | 执业范围 |
| practice_location | VARCHAR(128) | 执业地点 |
| image_url | VARCHAR(255) | 证书图片 |
| status | VARCHAR(16) | 状态：VALID / EXPIRED / REVOKED / PENDING |
| verified | TINYINT(1) | 是否已审核 |
| verified_by | BIGINT UNSIGNED | 审核人 |
| verified_at | DATETIME | 审核时间 |
| remark | VARCHAR(512) | 备注 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_license` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `license_type` VARCHAR(32) NOT NULL,
  `license_no` VARCHAR(64) DEFAULT NULL,
  `license_name` VARCHAR(128) DEFAULT NULL,
  `issuing_authority` VARCHAR(128) DEFAULT NULL,
  `issue_date` DATE DEFAULT NULL,
  `expiry_date` DATE DEFAULT NULL,
  `scope` VARCHAR(255) DEFAULT NULL,
  `practice_location` VARCHAR(128) DEFAULT NULL,
  `image_url` VARCHAR(255) DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'VALID',
  `verified` TINYINT(1) NOT NULL DEFAULT 0,
  `verified_by` BIGINT UNSIGNED DEFAULT NULL,
  `verified_at` DATETIME DEFAULT NULL,
  `remark` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_emp` (`emp_id`),
  KEY `idx_type` (`license_type`),
  KEY `idx_expiry` (`expiry_date`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工执业资格/证书';
```

### 02.6 表：`mdm_employee_account`（账号绑定表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| account_type | VARCHAR(32) | 账号类型：HIS / EMR / MOBILE / THIRD_PARTY |
| account_no | VARCHAR(64) | 账号 |
| password_hash | VARCHAR(128) | 密码哈希 |
| status | VARCHAR(16) | 状态：ENABLED / DISABLED / LOCKED |
| last_login_at | DATETIME | 最后登录时间 |
| last_login_ip | VARCHAR(64) | 最后登录IP |
| failed_attempts | INT | 连续失败次数 |
| locked_until | DATETIME | 锁定至 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_account` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `account_type` VARCHAR(32) NOT NULL,
  `account_no` VARCHAR(64) NOT NULL,
  `password_hash` VARCHAR(128) DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ENABLED',
  `last_login_at` DATETIME DEFAULT NULL,
  `last_login_ip` VARCHAR(64) DEFAULT NULL,
  `failed_attempts` INT NOT NULL DEFAULT 0,
  `locked_until` DATETIME DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_account` (`account_type`, `account_no`),
  KEY `idx_emp` (`emp_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工账号绑定';
```

### 02.7 表：`mdm_employee_signature`（电子签名表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| signature_type | VARCHAR(32) | 类型：CA_CERT / IMAGE / FINGERPRINT / FACE |
| signature_url | VARCHAR(255) | 签名图片URL |
| ca_cert_no | VARCHAR(128) | CA证书编号 |
| ca_issuer | VARCHAR(128) | CA签发机构 |
| ca_serial | VARCHAR(128) | CA序列号 |
| ca_expiry_date | DATE | CA有效期 |
| status | VARCHAR(16) | 状态：ACTIVE / EXPIRED / REVOKED |
| is_default | TINYINT(1) | 是否默认签名 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_signature` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `signature_type` VARCHAR(32) NOT NULL,
  `signature_url` VARCHAR(255) DEFAULT NULL,
  `ca_cert_no` VARCHAR(128) DEFAULT NULL,
  `ca_issuer` VARCHAR(128) DEFAULT NULL,
  `ca_serial` VARCHAR(128) DEFAULT NULL,
  `ca_expiry_date` DATE DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  `is_default` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_emp` (`emp_id`),
  KEY `idx_default` (`emp_id`, `is_default`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工电子签名';
```

### 02.8 表：`mdm_employee_change_log`（变更日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| emp_code | VARCHAR(32) | 工号 |
| action | VARCHAR(32) | CREATE / UPDATE / DELETE / ENABLE / DISABLE / IMPORT / SYNC / LICENSE_UPDATE / DEPT_CHANGE |
| before_data | JSON | 变更前 |
| after_data | JSON | 变更后 |
| diff_fields | JSON | 差异字段 |
| operator_id | BIGINT UNSIGNED | 操作人 |
| operator_name | VARCHAR(64) | 操作人姓名 |
| operator_ip | VARCHAR(64) | 操作IP |
| trace_id | VARCHAR(64) | 链路ID |
| created_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_change_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `emp_code` VARCHAR(32) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `before_data` JSON DEFAULT NULL,
  `after_data` JSON DEFAULT NULL,
  `diff_fields` JSON DEFAULT NULL,
  `operator_id` BIGINT UNSIGNED NOT NULL,
  `operator_name` VARCHAR(64) DEFAULT NULL,
  `operator_ip` VARCHAR(64) DEFAULT NULL,
  `trace_id` VARCHAR(64) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_emp` (`emp_id`, `created_at`),
  KEY `idx_code` (`emp_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工变更日志';
```

### 02.9 表：`mdm_employee_sync_log`（同步日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| batch_no | VARCHAR(64) | 批次号 |
| emp_id | BIGINT UNSIGNED | 职工ID |
| emp_code | VARCHAR(32) | 工号 |
| target_system | VARCHAR(64) | 目标系统 |
| action | VARCHAR(32) | UPSERT / DELETE |
| status | VARCHAR(16) | SUCCESS / FAILED / RETRYING |
| payload | JSON | 推送内容 |
| response | TEXT | 响应 |
| retry_count | INT | 重试次数 |
| error_message | VARCHAR(512) | 错误 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_sync_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `batch_no` VARCHAR(64) NOT NULL,
  `emp_id` BIGINT UNSIGNED NOT NULL,
  `emp_code` VARCHAR(32) NOT NULL,
  `target_system` VARCHAR(64) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `status` VARCHAR(16) NOT NULL,
  `payload` JSON DEFAULT NULL,
  `response` TEXT DEFAULT NULL,
  `retry_count` INT NOT NULL DEFAULT 0,
  `error_message` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_batch` (`batch_no`),
  KEY `idx_emp` (`emp_id`),
  KEY `idx_status` (`status`, `target_system`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工同步日志';
```

### 02.10 表：`mdm_employee_code_seq`（工号序列表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| prefix | VARCHAR(8) | 前缀（主键） |
| current_value | INT | 当前序号 |
| step | INT | 步长 |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_employee_code_seq` (
  `prefix` VARCHAR(8) NOT NULL,
  `current_value` INT NOT NULL DEFAULT 0,
  `step` INT NOT NULL DEFAULT 1,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='职工工号序列';
```

### 02.11 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/employee.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, Numeric,
    Index, UniqueConstraint, JSON, ForeignKey, func, CHAR
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Employee(Base):
    __tablename__ = "mdm_employee"
    __table_args__ = (
        UniqueConstraint("emp_code", "deleted", name="uk_emp_code"),
        UniqueConstraint("id_card_no_hash", "deleted", name="uk_id_card"),
        UniqueConstraint("phone_hash", "deleted", name="uk_phone"),
        Index("idx_name", "emp_name"),
        Index("idx_pinyin", "emp_name_pinyin", "emp_name_pinyin_short"),
        Index("idx_category", "emp_category"),
        Index("idx_primary_dept", "primary_dept_id"),
        Index("idx_status", "emp_status", "status"),
        Index("idx_updated", "updated_at"),
        {"comment": "职工主数据表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_code: Mapped[str] = mapped_column(String(32), nullable=False)
    emp_name: Mapped[str] = mapped_column(String(64), nullable=False)
    emp_name_pinyin: Mapped[str] = mapped_column(String(128), nullable=False)
    emp_name_pinyin_short: Mapped[str] = mapped_column(String(32), nullable=False)
    gender: Mapped[str] = mapped_column(String(8), nullable=False)
    birth_date: Mapped[Optional[date]] = mapped_column(Date)
    id_card_type: Mapped[Optional[str]] = mapped_column(String(16))
    id_card_no: Mapped[Optional[str]] = mapped_column(String(128))
    id_card_no_hash: Mapped[Optional[str]] = mapped_column(CHAR(64))
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    phone_hash: Mapped[Optional[str]] = mapped_column(CHAR(64))
    email: Mapped[Optional[str]] = mapped_column(String(128))
    nation: Mapped[Optional[str]] = mapped_column(String(32))
    native_place: Mapped[Optional[str]] = mapped_column(String(128))
    marital_status: Mapped[Optional[str]] = mapped_column(String(16))
    education: Mapped[Optional[str]] = mapped_column(String(32))
    degree: Mapped[Optional[str]] = mapped_column(String(32))
    graduate_school: Mapped[Optional[str]] = mapped_column(String(128))
    major: Mapped[Optional[str]] = mapped_column(String(128))
    graduation_date: Mapped[Optional[date]] = mapped_column(Date)
    political_status: Mapped[Optional[str]] = mapped_column(String(32))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(64))
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(32))
    photo_url: Mapped[Optional[str]] = mapped_column(String(255))

    emp_type: Mapped[str] = mapped_column(String(32), default="REGULAR", nullable=False)
    emp_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    emp_category: Mapped[str] = mapped_column(String(32), nullable=False)
    primary_dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    title: Mapped[Optional[str]] = mapped_column(String(32))
    title_level: Mapped[Optional[str]] = mapped_column(String(16))
    position: Mapped[Optional[str]] = mapped_column(String(32))
    position_level: Mapped[Optional[str]] = mapped_column(String(16))
    employment_date: Mapped[Optional[date]] = mapped_column(Date)
    regular_date: Mapped[Optional[date]] = mapped_column(Date)
    leave_date: Mapped[Optional[date]] = mapped_column(Date)
    retirement_date: Mapped[Optional[date]] = mapped_column(Date)
    doctor_level: Mapped[Optional[str]] = mapped_column(String(32))

    is_prescriber: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_operator: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_anesthetist: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_report_signer: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_optometrist: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_optical_seller: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_refraction_consultant: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_cashier: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_dispenser: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_prescription_reviewer: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_nurse_executor: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_queue_caller: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_mobile_user: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    ext: Mapped[Optional["EmployeeExt"]] = relationship(
        "EmployeeExt", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    depts: Mapped[List["EmployeeDept"]] = relationship(
        "EmployeeDept", cascade="all, delete-orphan", lazy="selectin"
    )
    licenses: Mapped[List["EmployeeLicense"]] = relationship(
        "EmployeeLicense", cascade="all, delete-orphan", lazy="selectin"
    )
    accounts: Mapped[List["EmployeeAccount"]] = relationship(
        "EmployeeAccount", cascade="all, delete-orphan", lazy="selectin"
    )
    signatures: Mapped[List["EmployeeSignature"]] = relationship(
        "EmployeeSignature", cascade="all, delete-orphan", lazy="selectin"
    )


class EmployeeExt(Base):
    __tablename__ = "mdm_employee_ext"

    emp_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mdm_employee.id"), primary_key=True)
    id_card_front_url: Mapped[Optional[str]] = mapped_column(String(255))
    id_card_back_url: Mapped[Optional[str]] = mapped_column(String(255))
    bank_name: Mapped[Optional[str]] = mapped_column(String(128))
    bank_account: Mapped[Optional[str]] = mapped_column(String(128))
    social_security_no: Mapped[Optional[str]] = mapped_column(String(64))
    medical_insurance_no: Mapped[Optional[str]] = mapped_column(String(64))
    hukou_address: Mapped[Optional[str]] = mapped_column(String(255))
    hukou_type: Mapped[Optional[str]] = mapped_column(String(16))
    contract_no: Mapped[Optional[str]] = mapped_column(String(64))
    contract_start_date: Mapped[Optional[date]] = mapped_column(Date)
    contract_end_date: Mapped[Optional[date]] = mapped_column(Date)
    probation_months: Mapped[Optional[int]] = mapped_column(Integer)
    annual_leave_days: Mapped[Optional[int]] = mapped_column(Integer)
    base_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    performance_config: Mapped[Optional[dict]] = mapped_column(JSON)
    third_party_codes: Mapped[Optional[dict]] = mapped_column(JSON)
    ext_config: Mapped[Optional[dict]] = mapped_column(JSON)
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmployeeDept(Base):
    __tablename__ = "mdm_employee_dept"
    __table_args__ = (
        UniqueConstraint("emp_id", "dept_id", "relation_type", name="uk_emp_dept_type"),
        Index("idx_dept", "dept_id"),
        Index("idx_emp", "emp_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    relation_type: Mapped[str] = mapped_column(String(32), default="PRIMARY", nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(32))
    title: Mapped[Optional[str]] = mapped_column(String(32))
    is_primary: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmployeeLicense(Base):
    __tablename__ = "mdm_employee_license"
    __table_args__ = (
        Index("idx_emp", "emp_id"),
        Index("idx_type", "license_type"),
        Index("idx_expiry", "expiry_date", "status"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    license_type: Mapped[str] = mapped_column(String(32), nullable=False)
    license_no: Mapped[Optional[str]] = mapped_column(String(64))
    license_name: Mapped[Optional[str]] = mapped_column(String(128))
    issuing_authority: Mapped[Optional[str]] = mapped_column(String(128))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    scope: Mapped[Optional[str]] = mapped_column(String(255))
    practice_location: Mapped[Optional[str]] = mapped_column(String(128))
    image_url: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="VALID", nullable=False)
    verified: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmployeeAccount(Base):
    __tablename__ = "mdm_employee_account"
    __table_args__ = (
        UniqueConstraint("account_type", "account_no", name="uk_account"),
        Index("idx_emp", "emp_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    account_no: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(64))
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmployeeSignature(Base):
    __tablename__ = "mdm_employee_signature"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    signature_type: Mapped[str] = mapped_column(String(32), nullable=False)
    signature_url: Mapped[Optional[str]] = mapped_column(String(255))
    ca_cert_no: Mapped[Optional[str]] = mapped_column(String(128))
    ca_issuer: Mapped[Optional[str]] = mapped_column(String(128))
    ca_serial: Mapped[Optional[str]] = mapped_column(String(128))
    ca_expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class EmployeeChangeLog(Base):
    __tablename__ = "mdm_employee_change_log"
    __table_args__ = (
        Index("idx_emp", "emp_id", "created_at"),
        Index("idx_code", "emp_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emp_code: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_data: Mapped[Optional[dict]] = mapped_column(JSON)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON)
    diff_fields: Mapped[Optional[list]] = mapped_column(JSON)
    operator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class EmployeeSyncLog(Base):
    __tablename__ = "mdm_employee_sync_log"
    __table_args__ = (
        Index("idx_batch", "batch_no"),
        Index("idx_emp", "emp_id"),
        Index("idx_status", "status", "target_system"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False)
    emp_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    emp_code: Mapped[str] = mapped_column(String(32), nullable=False)
    target_system: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    response: Mapped[Optional[str]] = mapped_column(String)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 02.12 Pydantic Schema 定义

```python
# app/schemas/mdm/employee.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class EmployeeDeptSchema(BaseModel):
    dept_id: int
    relation_type: str = "PRIMARY"
    position: Optional[str] = None
    title: Optional[str] = None
    is_primary: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sort_order: int = 100


class EmployeeLicenseSchema(BaseModel):
    id: Optional[int] = None
    license_type: str
    license_no: Optional[str] = None
    license_name: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    scope: Optional[str] = None
    practice_location: Optional[str] = None
    image_url: Optional[str] = None
    status: str = "VALID"
    remark: Optional[str] = None


class EmployeeAccountSchema(BaseModel):
    account_type: str
    account_no: str
    status: str = "ENABLED"


class EmployeeSignatureSchema(BaseModel):
    signature_type: str
    signature_url: Optional[str] = None
    ca_cert_no: Optional[str] = None
    ca_issuer: Optional[str] = None
    ca_serial: Optional[str] = None
    ca_expiry_date: Optional[date] = None
    status: str = "ACTIVE"
    is_default: bool = False


class EmployeeExtSchema(BaseModel):
    id_card_front_url: Optional[str] = None
    id_card_back_url: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    social_security_no: Optional[str] = None
    medical_insurance_no: Optional[str] = None
    hukou_address: Optional[str] = None
    hukou_type: Optional[str] = None
    contract_no: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    probation_months: Optional[int] = None
    annual_leave_days: Optional[int] = None
    base_salary: Optional[Decimal] = None
    performance_config: Optional[Dict[str, Any]] = None
    third_party_codes: Optional[Dict[str, str]] = None
    ext_config: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None


class EmployeeBase(BaseModel):
    emp_name: str = Field(..., max_length=64)
    gender: str = Field(..., pattern="^(MALE|FEMALE|UNKNOWN)$")
    birth_date: Optional[date] = None
    id_card_type: Optional[str] = None
    id_card_no: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    nation: Optional[str] = None
    native_place: Optional[str] = None
    marital_status: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    graduate_school: Optional[str] = None
    major: Optional[str] = None
    graduation_date: Optional[date] = None
    political_status: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    photo_url: Optional[str] = None
    emp_type: str = "REGULAR"
    emp_status: str = "ACTIVE"
    emp_category: str
    primary_dept_id: Optional[int] = None
    title: Optional[str] = None
    title_level: Optional[str] = None
    position: Optional[str] = None
    position_level: Optional[str] = None
    employment_date: Optional[date] = None
    regular_date: Optional[date] = None
    doctor_level: Optional[str] = None
    is_prescriber: bool = False
    is_operator: bool = False
    is_anesthetist: bool = False
    is_report_signer: bool = False
    is_optometrist: bool = False
    is_optical_seller: bool = False
    is_refraction_consultant: bool = False
    is_cashier: bool = False
    is_dispenser: bool = False
    is_prescription_reviewer: bool = False
    is_nurse_executor: bool = False
    is_queue_caller: bool = False
    is_mobile_user: bool = False
    remark: Optional[str] = Field(None, max_length=512)


class EmployeeCreate(EmployeeBase):
    emp_code: Optional[str] = None
    ext: Optional[EmployeeExtSchema] = None
    depts: Optional[List[EmployeeDeptSchema]] = None
    licenses: Optional[List[EmployeeLicenseSchema]] = None
    accounts: Optional[List[EmployeeAccountSchema]] = None
    signatures: Optional[List[EmployeeSignatureSchema]] = None


class EmployeeUpdate(EmployeeBase):
    version: int
    ext: Optional[EmployeeExtSchema] = None
    depts: Optional[List[EmployeeDeptSchema]] = None
    licenses: Optional[List[EmployeeLicenseSchema]] = None


class EmployeeStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(ENABLED|DISABLED)$")
    emp_status: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=255)


class EmployeeQuery(BaseModel):
    keyword: Optional[str] = None
    emp_category: Optional[str] = None
    emp_type: Optional[str] = None
    emp_status: Optional[str] = None
    primary_dept_id: Optional[int] = None
    title: Optional[str] = None
    position: Optional[str] = None
    is_prescriber: Optional[bool] = None
    is_operator: Optional[bool] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "emp_code"
    sort_dir: str = "asc"


class EmployeeVO(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    emp_code: str
    emp_name_pinyin: str
    emp_name_pinyin_short: str
    status: str
    audit_status: str
    version: int
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    ext: Optional[EmployeeExtSchema] = None
    depts: Optional[List[EmployeeDeptSchema]] = None
    licenses: Optional[List[EmployeeLicenseSchema]] = None


class EmployeeSimpleVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    emp_code: str
    emp_name: str
    emp_name_pinyin_short: str
    emp_category: str
    primary_dept_id: Optional[int]
    title: Optional[str]
    status: str


class PageResult(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
```

---

---

## 03. 药品数据结构

> **来源：** [药品详细设计](M01_主数据管理MDM_03_药品_详细设计.md) · 第 4 章
> **主数据域：** 物资域（`MAT`） · **表数：** 11

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 03.2 | `mdm_drug` | 药品主表 |
| 03.3 | `mdm_drug_ext` | 药品扩展表 |
| 03.4 | `mdm_drug_alias` | 药品别名表 |
| 03.5 | `mdm_drug_barcode` | 药品条码表 |
| 03.6 | `mdm_drug_price` | 药品价格表 |
| 03.7 | `mdm_drug_stock_policy` | 药品库存策略表 |
| 03.8 | `mdm_drug_prescription` | 药品处方规则表 |
| 03.9 | `mdm_drug_ddi` | 药品相互作用表 |
| 03.10 | `mdm_drug_change_log` | 变更日志表 |
| 03.11 | `mdm_drug_sync_log` | 同步日志表 |
| 03.12 | `mdm_drug_code_seq` | 编码序列表 |

---

### 03.1 ER 关系图

```
┌────────────────────────────┐        ┌────────────────────────────┐
│  mdm_drug                  │ 1   1  │  mdm_drug_ext              │
│  （药品主表）               │◄──────►│  （药品扩展表）             │
└────────────┬───────────────┘        └────────────────────────────┘
             │
             │ 1
             │
             ├──► N  mdm_drug_alias        （药品别名表）
             ├──► N  mdm_drug_barcode      （药品条码表）
             ├──► N  mdm_drug_price        （药品价格表）
             ├──► N  mdm_drug_stock_policy （药品库存策略表）
             ├──► N  mdm_drug_prescription （药品处方规则表）
             ├──► N  mdm_drug_ddi          （药品相互作用表）
             ├──► N  mdm_drug_change_log   （变更日志表）
             ├──► N  mdm_drug_sync_log     （同步日志表）
             └──► N  mdm_drug_code_seq     （编码序列表）
```

### 03.2 表：`mdm_drug`（药品主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| drug_code | VARCHAR(32) | N | - | 药品编码，全局唯一 |
| drug_name | VARCHAR(128) | N | - | 药品通用名（含规格） |
| drug_generic_name | VARCHAR(128) | N | - | 药品通用名（不含规格） |
| drug_trade_name | VARCHAR(128) | Y | NULL | 商品名 |
| drug_english_name | VARCHAR(255) | Y | NULL | 英文名 |
| drug_alias | VARCHAR(255) | Y | NULL | 别名（逗号分隔） |
| pinyin_code | VARCHAR(64) | N | - | 拼音码 |
| pinyin_short | VARCHAR(32) | N | - | 拼音首字母 |
| wubi_code | VARCHAR(64) | Y | NULL | 五笔码 |
| drug_category | VARCHAR(32) | N | - | 药品大类 |
| dosage_form | VARCHAR(32) | N | - | 剂型 |
| pharmacology_class | VARCHAR(64) | Y | NULL | 药理分类 |
| management_class | VARCHAR(32) | Y | NULL | 管理分类 |
| antibiotic_level | VARCHAR(32) | Y | NULL | 抗菌药物分级 |
| ophthalmic_class | VARCHAR(64) | Y | NULL | 眼科专科分类 |
| atc_code | VARCHAR(32) | Y | NULL | ATC 编码 |
| national_drug_code | VARCHAR(64) | Y | NULL | 国家药品编码 |
| medical_insurance_code | VARCHAR(64) | Y | NULL | 医保编码（预留） |
| commercial_insurance_code | VARCHAR(64) | Y | NULL | 商保编码（预留） |
| specification | VARCHAR(128) | N | - | 规格 |
| concentration | VARCHAR(64) | Y | NULL | 浓度（如 0.5%） |
| package_unit | VARCHAR(32) | N | - | 包装单位（盒、瓶、支） |
| package_quantity | DECIMAL(12,4) | Y | NULL | 包装数量 |
| dose_unit | VARCHAR(32) | N | - | 剂量单位（ml、mg、片） |
| min_unit | VARCHAR(32) | N | - | 最小单位（ml、mg、片） |
| conversion_ratio | DECIMAL(12,4) | N | 1 | 包装单位→最小单位转换比 |
| is_split | TINYINT(1) | N | 0 | 是否可拆零 |
| is_batch_managed | TINYINT(1) | N | 1 | 是否批次管理 |
| is_expiry_managed | TINYINT(1) | N | 1 | 是否效期管理 |
| is_cold_chain | TINYINT(1) | N | 0 | 是否冷链 |
| is_high_risk | TINYINT(1) | N | 0 | 是否高危药品 |
| is_essential | TINYINT(1) | N | 0 | 是否基本药物 |
| is_imported | TINYINT(1) | N | 0 | 是否进口 |
| is_otc | TINYINT(1) | N | 0 | 是否非处方药 |
| is_psychotropic | TINYINT(1) | N | 0 | 是否精神药品 |
| is_narcotic | TINYINT(1) | N | 0 | 是否麻醉药品 |
| is_toxic | TINYINT(1) | N | 0 | 是否毒性药品 |
| is_radioactive | TINYINT(1) | N | 0 | 是否放射性药品 |
| is_antibiotic | TINYINT(1) | N | 0 | 是否抗菌药物 |
| is_ophthalmic | TINYINT(1) | N | 1 | 是否眼科用药 |
| manufacturer | VARCHAR(128) | Y | NULL | 生产厂家 |
| manufacturer_code | VARCHAR(64) | Y | NULL | 生产厂家编码 |
| origin_place | VARCHAR(128) | Y | NULL | 产地 |
| approval_number | VARCHAR(64) | Y | NULL | 批准文号 |
| approval_date | DATE | Y | NULL | 批准日期 |
| registration_standard | VARCHAR(64) | Y | NULL | 注册标准 |
| shelf_life_months | INT | Y | NULL | 有效期（月） |
| storage_condition | VARCHAR(32) | Y | NULL | 存储条件：常温/阴凉/冷藏/冷冻 |
| storage_temp_min | DECIMAL(5,2) | Y | NULL | 存储温度下限 |
| storage_temp_max | DECIMAL(5,2) | Y | NULL | 存储温度上限 |
| is_light_protected | TINYINT(1) | N | 0 | 是否避光 |
| is_moisture_protected | TINYINT(1) | N | 0 | 是否防潮 |
| after_open_shelf_life | INT | Y | NULL | 开封后效期（天） |
| is_after_open_managed | TINYINT(1) | N | 0 | 是否管理开封后效期 |
| drug_image_url | VARCHAR(255) | Y | NULL | 药品图片 |
| drug_instruction_url | VARCHAR(255) | Y | NULL | 说明书 URL |
| drug_label_url | VARCHAR(255) | Y | NULL | 标签 URL |
| status | VARCHAR(16) | N | 'ENABLED' | 业务状态：ENABLED / DISABLED / RECALLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_drug | PRIMARY | id | 主键 |
| uk_drug_code | UNIQUE | drug_code, deleted | 编码唯一 |
| idx_name | NORMAL | drug_name | 名称查询 |
| idx_generic | NORMAL | drug_generic_name | 通用名查询 |
| idx_trade | NORMAL | drug_trade_name | 商品名查询 |
| idx_pinyin | NORMAL | pinyin_code, pinyin_short | 拼音搜索 |
| idx_category | NORMAL | drug_category | 大类过滤 |
| idx_dosage_form | NORMAL | dosage_form | 剂型过滤 |
| idx_pharmacology | NORMAL | pharmacology_class | 药理分类 |
| idx_management | NORMAL | management_class | 管理分类 |
| idx_antibiotic | NORMAL | antibiotic_level | 抗菌药物分级 |
| idx_ophthalmic | NORMAL | ophthalmic_class | 眼科分类 |
| idx_status | NORMAL | status | 状态过滤 |
| idx_updated | NORMAL | updated_at | 增量同步 |

**DDL 示例**

```sql
CREATE TABLE `mdm_drug` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `drug_code` VARCHAR(32) NOT NULL COMMENT '药品编码',
  `drug_name` VARCHAR(128) NOT NULL COMMENT '药品通用名（含规格）',
  `drug_generic_name` VARCHAR(128) NOT NULL COMMENT '药品通用名',
  `drug_trade_name` VARCHAR(128) DEFAULT NULL COMMENT '商品名',
  `drug_english_name` VARCHAR(255) DEFAULT NULL COMMENT '英文名',
  `drug_alias` VARCHAR(255) DEFAULT NULL COMMENT '别名',
  `pinyin_code` VARCHAR(64) NOT NULL COMMENT '拼音码',
  `pinyin_short` VARCHAR(32) NOT NULL COMMENT '拼音首字母',
  `wubi_code` VARCHAR(64) DEFAULT NULL COMMENT '五笔码',
  `drug_category` VARCHAR(32) NOT NULL COMMENT '药品大类',
  `dosage_form` VARCHAR(32) NOT NULL COMMENT '剂型',
  `pharmacology_class` VARCHAR(64) DEFAULT NULL COMMENT '药理分类',
  `management_class` VARCHAR(32) DEFAULT NULL COMMENT '管理分类',
  `antibiotic_level` VARCHAR(32) DEFAULT NULL COMMENT '抗菌药物分级',
  `ophthalmic_class` VARCHAR(64) DEFAULT NULL COMMENT '眼科专科分类',
  `atc_code` VARCHAR(32) DEFAULT NULL COMMENT 'ATC编码',
  `national_drug_code` VARCHAR(64) DEFAULT NULL COMMENT '国家药品编码',
  `medical_insurance_code` VARCHAR(64) DEFAULT NULL COMMENT '医保编码',
  `commercial_insurance_code` VARCHAR(64) DEFAULT NULL COMMENT '商保编码',
  `specification` VARCHAR(128) NOT NULL COMMENT '规格',
  `concentration` VARCHAR(64) DEFAULT NULL COMMENT '浓度',
  `package_unit` VARCHAR(32) NOT NULL COMMENT '包装单位',
  `package_quantity` DECIMAL(12,4) DEFAULT NULL COMMENT '包装数量',
  `dose_unit` VARCHAR(32) NOT NULL COMMENT '剂量单位',
  `min_unit` VARCHAR(32) NOT NULL COMMENT '最小单位',
  `conversion_ratio` DECIMAL(12,4) NOT NULL DEFAULT 1 COMMENT '转换比',
  `is_split` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否可拆零',
  `is_batch_managed` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否批次管理',
  `is_expiry_managed` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否效期管理',
  `is_cold_chain` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否冷链',
  `is_high_risk` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否高危药品',
  `is_essential` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否基本药物',
  `is_imported` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否进口',
  `is_otc` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否非处方药',
  `is_psychotropic` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否精神药品',
  `is_narcotic` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否麻醉药品',
  `is_toxic` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否毒性药品',
  `is_radioactive` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否放射性药品',
  `is_antibiotic` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否抗菌药物',
  `is_ophthalmic` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否眼科用药',
  `manufacturer` VARCHAR(128) DEFAULT NULL COMMENT '生产厂家',
  `manufacturer_code` VARCHAR(64) DEFAULT NULL COMMENT '生产厂家编码',
  `origin_place` VARCHAR(128) DEFAULT NULL COMMENT '产地',
  `approval_number` VARCHAR(64) DEFAULT NULL COMMENT '批准文号',
  `approval_date` DATE DEFAULT NULL COMMENT '批准日期',
  `registration_standard` VARCHAR(64) DEFAULT NULL COMMENT '注册标准',
  `shelf_life_months` INT DEFAULT NULL COMMENT '有效期（月）',
  `storage_condition` VARCHAR(32) DEFAULT NULL COMMENT '存储条件',
  `storage_temp_min` DECIMAL(5,2) DEFAULT NULL COMMENT '存储温度下限',
  `storage_temp_max` DECIMAL(5,2) DEFAULT NULL COMMENT '存储温度上限',
  `is_light_protected` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否避光',
  `is_moisture_protected` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否防潮',
  `after_open_shelf_life` INT DEFAULT NULL COMMENT '开封后效期（天）',
  `is_after_open_managed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否管理开封后效期',
  `drug_image_url` VARCHAR(255) DEFAULT NULL COMMENT '药品图片',
  `drug_instruction_url` VARCHAR(255) DEFAULT NULL COMMENT '说明书URL',
  `drug_label_url` VARCHAR(255) DEFAULT NULL COMMENT '标签URL',
  `status` VARCHAR(16) NOT NULL DEFAULT 'ENABLED' COMMENT '业务状态',
  `audit_status` VARCHAR(16) NOT NULL DEFAULT 'APPROVED' COMMENT '审批状态',
  `version` INT NOT NULL DEFAULT 0 COMMENT '乐观锁版本号',
  `remark` VARCHAR(512) DEFAULT NULL COMMENT '备注',
  `created_by` BIGINT UNSIGNED NOT NULL COMMENT '创建人',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_by` BIGINT UNSIGNED DEFAULT NULL COMMENT '更新人',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `deleted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '逻辑删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_drug_code` (`drug_code`, `deleted`),
  KEY `idx_name` (`drug_name`),
  KEY `idx_generic` (`drug_generic_name`),
  KEY `idx_trade` (`drug_trade_name`),
  KEY `idx_pinyin` (`pinyin_code`, `pinyin_short`),
  KEY `idx_category` (`drug_category`),
  KEY `idx_dosage_form` (`dosage_form`),
  KEY `idx_pharmacology` (`pharmacology_class`),
  KEY `idx_management` (`management_class`),
  KEY `idx_antibiotic` (`antibiotic_level`),
  KEY `idx_ophthalmic` (`ophthalmic_class`),
  KEY `idx_status` (`status`),
  KEY `idx_updated` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品主数据表';
```

### 03.3 表：`mdm_drug_ext`（药品扩展表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| drug_id | BIGINT UNSIGNED | 主键，1:1 |
| default_supplier_id | BIGINT UNSIGNED | 默认供应商 |
| default_warehouse_code | VARCHAR(64) | 默认仓库 |
| default_location_code | VARCHAR(64) | 默认库位 |
| default_charge_item_code | VARCHAR(64) | 默认收费项目编码 |
| default_account_code | VARCHAR(64) | 默认会计科目 |
| cost_center_code | VARCHAR(64) | 成本核算中心 |
| therapeutic_effect | TEXT | 适应症/功效 |
| adverse_reaction | TEXT | 不良反应 |
| contraindication | TEXT | 禁忌症 |
| precaution | TEXT | 注意事项 |
| drug_interaction | TEXT | 药物相互作用 |
| dosage_adult | TEXT | 成人剂量 |
| dosage_child | TEXT | 儿童剂量 |
| dosage_elderly | TEXT | 老年剂量 |
| dosage_renal | TEXT | 肾功能不全剂量 |
| dosage_hepatic | TEXT | 肝功能不全剂量 |
| pregnancy_category | VARCHAR(8) | 妊娠分级（A/B/C/D/X） |
| lactation_safety | VARCHAR(16) | 哺乳期安全性 |
| pediatric_use | VARCHAR(16) | 儿童用药（可用/慎用/禁用） |
| elderly_use | VARCHAR(16) | 老年用药 |
| max_single_dose | DECIMAL(12,4) | 单次最大剂量 |
| max_daily_dose | DECIMAL(12,4) | 每日最大剂量 |
| max_course_days | INT | 最大疗程（天） |
| third_party_codes | JSON | 第三方编码映射 |
| ext_config | JSON | 其他扩展 |
| remark | VARCHAR(512) | 备注 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_ext` (
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `default_supplier_id` BIGINT UNSIGNED DEFAULT NULL,
  `default_warehouse_code` VARCHAR(64) DEFAULT NULL,
  `default_location_code` VARCHAR(64) DEFAULT NULL,
  `default_charge_item_code` VARCHAR(64) DEFAULT NULL,
  `default_account_code` VARCHAR(64) DEFAULT NULL,
  `cost_center_code` VARCHAR(64) DEFAULT NULL,
  `therapeutic_effect` TEXT DEFAULT NULL,
  `adverse_reaction` TEXT DEFAULT NULL,
  `contraindication` TEXT DEFAULT NULL,
  `precaution` TEXT DEFAULT NULL,
  `drug_interaction` TEXT DEFAULT NULL,
  `dosage_adult` TEXT DEFAULT NULL,
  `dosage_child` TEXT DEFAULT NULL,
  `dosage_elderly` TEXT DEFAULT NULL,
  `dosage_renal` TEXT DEFAULT NULL,
  `dosage_hepatic` TEXT DEFAULT NULL,
  `pregnancy_category` VARCHAR(8) DEFAULT NULL,
  `lactation_safety` VARCHAR(16) DEFAULT NULL,
  `pediatric_use` VARCHAR(16) DEFAULT NULL,
  `elderly_use` VARCHAR(16) DEFAULT NULL,
  `max_single_dose` DECIMAL(12,4) DEFAULT NULL,
  `max_daily_dose` DECIMAL(12,4) DEFAULT NULL,
  `max_course_days` INT DEFAULT NULL,
  `third_party_codes` JSON DEFAULT NULL,
  `ext_config` JSON DEFAULT NULL,
  `remark` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`drug_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品扩展表';
```

### 03.4 表：`mdm_drug_alias`（药品别名表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| alias_name | VARCHAR(128) | 别名 |
| alias_type | VARCHAR(32) | 类型：TRADE / COMMON / OLD / ABROAD / OTHER |
| pinyin_code | VARCHAR(64) | 拼音码 |
| pinyin_short | VARCHAR(32) | 拼音首字母 |
| sort_order | INT | 排序 |
| created_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_alias` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `alias_name` VARCHAR(128) NOT NULL,
  `alias_type` VARCHAR(32) NOT NULL DEFAULT 'COMMON',
  `pinyin_code` VARCHAR(64) DEFAULT NULL,
  `pinyin_short` VARCHAR(32) DEFAULT NULL,
  `sort_order` INT NOT NULL DEFAULT 100,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_drug` (`drug_id`),
  KEY `idx_alias` (`alias_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品别名';
```

### 03.5 表：`mdm_drug_barcode`（药品条码表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| barcode | VARCHAR(64) | 条码 |
| barcode_type | VARCHAR(32) | 类型：GTIN / EAN13 / CODE128 / QR / OTHER |
| package_level | VARCHAR(32) | 包装级别：MIN / PACKAGE / CASE |
| is_default | TINYINT(1) | 是否默认 |
| created_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_barcode` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `barcode` VARCHAR(64) NOT NULL,
  `barcode_type` VARCHAR(32) NOT NULL DEFAULT 'GTIN',
  `package_level` VARCHAR(32) NOT NULL DEFAULT 'PACKAGE',
  `is_default` TINYINT(1) NOT NULL DEFAULT 0,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_barcode` (`barcode`),
  KEY `idx_drug` (`drug_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品条码';
```

### 03.6 表：`mdm_drug_price`（药品价格表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| price_type | VARCHAR(32) | 类型：PURCHASE / RETAIL / SPLIT_RETAIL / MAX_RETAIL / MEMBER / INSURANCE |
| price | DECIMAL(12,4) | 价格 |
| unit | VARCHAR(32) | 价格单位 |
| effective_date | DATE | 生效日期 |
| expiry_date | DATE | 失效日期 |
| approval_no | VARCHAR(64) | 物价批文号 |
| approval_date | DATE | 批文日期 |
| status | VARCHAR(16) | 状态：ACTIVE / EXPIRED / PENDING |
| is_current | TINYINT(1) | 是否当前价格 |
| change_reason | VARCHAR(255) | 调价原因 |
| created_by | BIGINT UNSIGNED | 创建人 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_price` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `price_type` VARCHAR(32) NOT NULL,
  `price` DECIMAL(12,4) NOT NULL,
  `unit` VARCHAR(32) NOT NULL,
  `effective_date` DATE NOT NULL,
  `expiry_date` DATE DEFAULT NULL,
  `approval_no` VARCHAR(64) DEFAULT NULL,
  `approval_date` DATE DEFAULT NULL,
  `status` VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  `is_current` TINYINT(1) NOT NULL DEFAULT 0,
  `change_reason` VARCHAR(255) DEFAULT NULL,
  `created_by` BIGINT UNSIGNED NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_drug` (`drug_id`, `price_type`, `is_current`),
  KEY `idx_effective` (`effective_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品价格';
```

### 03.7 表：`mdm_drug_stock_policy`（药品库存策略表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| drug_id | BIGINT UNSIGNED | 主键，1:1 |
| warehouse_code | VARCHAR(64) | 仓库编码 |
| safety_stock | DECIMAL(12,4) | 安全库存 |
| min_stock | DECIMAL(12,4) | 低限库存 |
| max_stock | DECIMAL(12,4) | 高限库存 |
| reorder_point | DECIMAL(12,4) | 补货点 |
| reorder_quantity | DECIMAL(12,4) | 补货量 |
| lead_time_days | INT | 采购提前期（天） |
| default_location_code | VARCHAR(64) | 默认库位 |
| is_auto_reorder | TINYINT(1) | 是否自动补货 |
| expiry_alert_days | INT | 效期预警天数（默认 90） |
| expiry_warning_days | INT | 效期警告天数（默认 30） |
| stock_alert_enabled | TINYINT(1) | 是否启用库存预警 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_stock_policy` (
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `warehouse_code` VARCHAR(64) DEFAULT NULL,
  `safety_stock` DECIMAL(12,4) DEFAULT NULL,
  `min_stock` DECIMAL(12,4) DEFAULT NULL,
  `max_stock` DECIMAL(12,4) DEFAULT NULL,
  `reorder_point` DECIMAL(12,4) DEFAULT NULL,
  `reorder_quantity` DECIMAL(12,4) DEFAULT NULL,
  `lead_time_days` INT DEFAULT NULL,
  `default_location_code` VARCHAR(64) DEFAULT NULL,
  `is_auto_reorder` TINYINT(1) NOT NULL DEFAULT 0,
  `expiry_alert_days` INT NOT NULL DEFAULT 90,
  `expiry_warning_days` INT NOT NULL DEFAULT 30,
  `stock_alert_enabled` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`drug_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品库存策略';
```

### 03.8 表：`mdm_drug_prescription`（药品处方规则表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| route | VARCHAR(32) | 给药途径：ORAL / TOPICAL_EYE / INJECTION / ... |
| default_frequency | VARCHAR(32) | 默认频次 |
| default_dose | DECIMAL(12,4) | 默认单次剂量 |
| default_dose_unit | VARCHAR(32) | 默认剂量单位 |
| default_duration_days | INT | 默认疗程（天） |
| max_single_dose | DECIMAL(12,4) | 单次最大剂量 |
| max_daily_dose | DECIMAL(12,4) | 每日最大剂量 |
| max_duration_days | INT | 最大疗程（天） |
| requires_prescription_level | VARCHAR(32) | 需要的处方权等级：RESIDENT / ATTENDING / ASSOCIATE_CHIEF / CHIEF / SPECIAL |
| requires_consultation | TINYINT(1) | 是否需要会诊 |
| requires_special_approval | TINYINT(1) | 是否需要特殊审批 |
| is_restricted | TINYINT(1) | 是否限制使用 |
| restriction_note | VARCHAR(255) | 限制说明 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_prescription` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `route` VARCHAR(32) NOT NULL DEFAULT 'ORAL',
  `default_frequency` VARCHAR(32) DEFAULT NULL,
  `default_dose` DECIMAL(12,4) DEFAULT NULL,
  `default_dose_unit` VARCHAR(32) DEFAULT NULL,
  `default_duration_days` INT DEFAULT NULL,
  `max_single_dose` DECIMAL(12,4) DEFAULT NULL,
  `max_daily_dose` DECIMAL(12,4) DEFAULT NULL,
  `max_duration_days` INT DEFAULT NULL,
  `requires_prescription_level` VARCHAR(32) DEFAULT NULL,
  `requires_consultation` TINYINT(1) NOT NULL DEFAULT 0,
  `requires_special_approval` TINYINT(1) NOT NULL DEFAULT 0,
  `is_restricted` TINYINT(1) NOT NULL DEFAULT 0,
  `restriction_note` VARCHAR(255) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_drug` (`drug_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品处方规则';
```

### 03.9 表：`mdm_drug_ddi`（药品相互作用表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| interact_drug_id | BIGINT UNSIGNED | 相互作用药品ID |
| interact_drug_name | VARCHAR(128) | 相互作用药品名称（冗余） |
| severity | VARCHAR(16) | 严重程度：CONTRAINDICATED / MAJOR / MODERATE / MINOR |
| mechanism | TEXT | 机制 |
| description | TEXT | 描述 |
| management | TEXT | 处理建议 |
| evidence_level | VARCHAR(16) | 证据等级 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_ddi` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `interact_drug_id` BIGINT UNSIGNED DEFAULT NULL,
  `interact_drug_name` VARCHAR(128) NOT NULL,
  `severity` VARCHAR(16) NOT NULL,
  `mechanism` TEXT DEFAULT NULL,
  `description` TEXT DEFAULT NULL,
  `management` TEXT DEFAULT NULL,
  `evidence_level` VARCHAR(16) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_ddi` (`drug_id`, `interact_drug_id`),
  KEY `idx_drug` (`drug_id`),
  KEY `idx_severity` (`severity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品相互作用';
```

### 03.10 表：`mdm_drug_change_log`（变更日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| drug_code | VARCHAR(32) | 药品编码 |
| action | VARCHAR(32) | CREATE / UPDATE / DELETE / ENABLE / DISABLE / RECALL / PRICE_CHANGE / IMPORT / SYNC |
| before_data | JSON | 变更前 |
| after_data | JSON | 变更后 |
| diff_fields | JSON | 差异字段 |
| operator_id | BIGINT UNSIGNED | 操作人 |
| operator_name | VARCHAR(64) | 操作人姓名 |
| operator_ip | VARCHAR(64) | 操作IP |
| trace_id | VARCHAR(64) | 链路ID |
| created_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_change_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `drug_code` VARCHAR(32) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `before_data` JSON DEFAULT NULL,
  `after_data` JSON DEFAULT NULL,
  `diff_fields` JSON DEFAULT NULL,
  `operator_id` BIGINT UNSIGNED NOT NULL,
  `operator_name` VARCHAR(64) DEFAULT NULL,
  `operator_ip` VARCHAR(64) DEFAULT NULL,
  `trace_id` VARCHAR(64) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_drug` (`drug_id`, `created_at`),
  KEY `idx_code` (`drug_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品变更日志';
```

### 03.11 表：`mdm_drug_sync_log`（同步日志表）

| 字段名 | 类型 | 说明 |
|---|---|---|
| id | BIGINT UNSIGNED | 主键 |
| batch_no | VARCHAR(64) | 批次号 |
| drug_id | BIGINT UNSIGNED | 药品ID |
| drug_code | VARCHAR(32) | 药品编码 |
| target_system | VARCHAR(64) | 目标系统 |
| action | VARCHAR(32) | UPSERT / DELETE |
| status | VARCHAR(16) | SUCCESS / FAILED / RETRYING |
| payload | JSON | 推送内容 |
| response | TEXT | 响应 |
| retry_count | INT | 重试次数 |
| error_message | VARCHAR(512) | 错误信息 |
| created_at | DATETIME | - |
| updated_at | DATETIME | - |

```sql
CREATE TABLE `mdm_drug_sync_log` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `batch_no` VARCHAR(64) NOT NULL,
  `drug_id` BIGINT UNSIGNED NOT NULL,
  `drug_code` VARCHAR(32) NOT NULL,
  `target_system` VARCHAR(64) NOT NULL,
  `action` VARCHAR(32) NOT NULL,
  `status` VARCHAR(16) NOT NULL,
  `payload` JSON DEFAULT NULL,
  `response` TEXT DEFAULT NULL,
  `retry_count` INT NOT NULL DEFAULT 0,
  `error_message` VARCHAR(512) DEFAULT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_batch` (`batch_no`),
  KEY `idx_drug` (`drug_id`),
  KEY `idx_status` (`status`, `target_system`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品同步日志';
```

### 03.12 表：`mdm_drug_code_seq`（编码序列表）

```sql
CREATE TABLE `mdm_drug_code_seq` (
  `prefix` VARCHAR(8) NOT NULL,
  `current_value` INT NOT NULL DEFAULT 0,
  `step` INT NOT NULL DEFAULT 1,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='药品编码序列';
```

### 03.13 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/drug.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, Numeric, Text,
    Index, UniqueConstraint, JSON, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Drug(Base):
    __tablename__ = "mdm_drug"
    __table_args__ = (
        UniqueConstraint("drug_code", "deleted", name="uk_drug_code"),
        Index("idx_name", "drug_name"),
        Index("idx_generic", "drug_generic_name"),
        Index("idx_pinyin", "pinyin_code", "pinyin_short"),
        Index("idx_category", "drug_category"),
        Index("idx_dosage_form", "dosage_form"),
        Index("idx_pharmacology", "pharmacology_class"),
        Index("idx_management", "management_class"),
        Index("idx_antibiotic", "antibiotic_level"),
        Index("idx_ophthalmic", "ophthalmic_class"),
        Index("idx_status", "status"),
        Index("idx_updated", "updated_at"),
        {"comment": "药品主数据表"},
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_code: Mapped[str] = mapped_column(String(32), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(128), nullable=False)
    drug_generic_name: Mapped[str] = mapped_column(String(128), nullable=False)
    drug_trade_name: Mapped[Optional[str]] = mapped_column(String(128))
    drug_english_name: Mapped[Optional[str]] = mapped_column(String(255))
    drug_alias: Mapped[Optional[str]] = mapped_column(String(255))
    pinyin_code: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin_short: Mapped[str] = mapped_column(String(32), nullable=False)
    wubi_code: Mapped[Optional[str]] = mapped_column(String(64))
    drug_category: Mapped[str] = mapped_column(String(32), nullable=False)
    dosage_form: Mapped[str] = mapped_column(String(32), nullable=False)
    pharmacology_class: Mapped[Optional[str]] = mapped_column(String(64))
    management_class: Mapped[Optional[str]] = mapped_column(String(32))
    antibiotic_level: Mapped[Optional[str]] = mapped_column(String(32))
    ophthalmic_class: Mapped[Optional[str]] = mapped_column(String(64))
    atc_code: Mapped[Optional[str]] = mapped_column(String(32))
    national_drug_code: Mapped[Optional[str]] = mapped_column(String(64))
    medical_insurance_code: Mapped[Optional[str]] = mapped_column(String(64))
    commercial_insurance_code: Mapped[Optional[str]] = mapped_column(String(64))
    specification: Mapped[str] = mapped_column(String(128), nullable=False)
    concentration: Mapped[Optional[str]] = mapped_column(String(64))
    package_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    package_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    dose_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    min_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    conversion_ratio: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=1, nullable=False)
    is_split: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_batch_managed: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_expiry_managed: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_cold_chain: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_high_risk: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_essential: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_imported: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_otc: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_psychotropic: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_narcotic: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_toxic: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_radioactive: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_antibiotic: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_ophthalmic: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(128))
    manufacturer_code: Mapped[Optional[str]] = mapped_column(String(64))
    origin_place: Mapped[Optional[str]] = mapped_column(String(128))
    approval_number: Mapped[Optional[str]] = mapped_column(String(64))
    approval_date: Mapped[Optional[date]] = mapped_column(Date)
    registration_standard: Mapped[Optional[str]] = mapped_column(String(64))
    shelf_life_months: Mapped[Optional[int]] = mapped_column(Integer)
    storage_condition: Mapped[Optional[str]] = mapped_column(String(32))
    storage_temp_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    storage_temp_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    is_light_protected: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_moisture_protected: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    after_open_shelf_life: Mapped[Optional[int]] = mapped_column(Integer)
    is_after_open_managed: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    drug_image_url: Mapped[Optional[str]] = mapped_column(String(255))
    drug_instruction_url: Mapped[Optional[str]] = mapped_column(String(255))
    drug_label_url: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    ext: Mapped[Optional["DrugExt"]] = relationship(
        "DrugExt", uselist=False, cascade="all, delete-orphan", lazy="selectin"
    )
    aliases: Mapped[List["DrugAlias"]] = relationship(
        "DrugAlias", cascade="all, delete-orphan", lazy="selectin"
    )
    barcodes: Mapped[List["DrugBarcode"]] = relationship(
        "DrugBarcode", cascade="all, delete-orphan", lazy="selectin"
    )
    prices: Mapped[List["DrugPrice"]] = relationship(
        "DrugPrice", cascade="all, delete-orphan", lazy="selectin"
    )


class DrugExt(Base):
    __tablename__ = "mdm_drug_ext"

    drug_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mdm_drug.id"), primary_key=True)
    default_supplier_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    default_warehouse_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_location_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_charge_item_code: Mapped[Optional[str]] = mapped_column(String(64))
    default_account_code: Mapped[Optional[str]] = mapped_column(String(64))
    cost_center_code: Mapped[Optional[str]] = mapped_column(String(64))
    therapeutic_effect: Mapped[Optional[str]] = mapped_column(Text)
    adverse_reaction: Mapped[Optional[str]] = mapped_column(Text)
    contraindication: Mapped[Optional[str]] = mapped_column(Text)
    precaution: Mapped[Optional[str]] = mapped_column(Text)
    drug_interaction: Mapped[Optional[str]] = mapped_column(Text)
    dosage_adult: Mapped[Optional[str]] = mapped_column(Text)
    dosage_child: Mapped[Optional[str]] = mapped_column(Text)
    dosage_elderly: Mapped[Optional[str]] = mapped_column(Text)
    dosage_renal: Mapped[Optional[str]] = mapped_column(Text)
    dosage_hepatic: Mapped[Optional[str]] = mapped_column(Text)
    pregnancy_category: Mapped[Optional[str]] = mapped_column(String(8))
    lactation_safety: Mapped[Optional[str]] = mapped_column(String(16))
    pediatric_use: Mapped[Optional[str]] = mapped_column(String(16))
    elderly_use: Mapped[Optional[str]] = mapped_column(String(16))
    max_single_dose: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    max_daily_dose: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    max_course_days: Mapped[Optional[int]] = mapped_column(Integer)
    third_party_codes: Mapped[Optional[dict]] = mapped_column(JSON)
    ext_config: Mapped[Optional[dict]] = mapped_column(JSON)
    remark: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DrugAlias(Base):
    __tablename__ = "mdm_drug_alias"
    __table_args__ = (Index("idx_drug", "drug_id"), Index("idx_alias", "alias_name"))

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    alias_name: Mapped[str] = mapped_column(String(128), nullable=False)
    alias_type: Mapped[str] = mapped_column(String(32), default="COMMON", nullable=False)
    pinyin_code: Mapped[Optional[str]] = mapped_column(String(64))
    pinyin_short: Mapped[Optional[str]] = mapped_column(String(32))
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DrugBarcode(Base):
    __tablename__ = "mdm_drug_barcode"
    __table_args__ = (
        UniqueConstraint("barcode", name="uk_barcode"),
        Index("idx_drug", "drug_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    barcode: Mapped[str] = mapped_column(String(64), nullable=False)
    barcode_type: Mapped[str] = mapped_column(String(32), default="GTIN", nullable=False)
    package_level: Mapped[str] = mapped_column(String(32), default="PACKAGE", nullable=False)
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DrugPrice(Base):
    __tablename__ = "mdm_drug_price"
    __table_args__ = (
        Index("idx_drug", "drug_id", "price_type", "is_current"),
        Index("idx_effective", "effective_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_type: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    approval_no: Mapped[Optional[str]] = mapped_column(String(64))
    approval_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    is_current: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    change_reason: Mapped[Optional[str]] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DrugStockPolicy(Base):
    __tablename__ = "mdm_drug_stock_policy"

    drug_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("mdm_drug.id"), primary_key=True)
    warehouse_code: Mapped[Optional[str]] = mapped_column(String(64))
    safety_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    min_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    max_stock: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    reorder_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer)
    default_location_code: Mapped[Optional[str]] = mapped_column(String(64))
    is_auto_reorder: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    expiry_alert_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    expiry_warning_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    stock_alert_enabled: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DrugPrescription(Base):
    __tablename__ = "mdm_drug_prescription"
    __table_args__ = (Index("idx_drug", "drug_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    route: Mapped[str] = mapped_column(String(32), default="ORAL", nullable=False)
    default_frequency: Mapped[Optional[str]] = mapped_column(String(32))
    default_dose: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    default_dose_unit: Mapped[Optional[str]] = mapped_column(String(32))
    default_duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    max_single_dose: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    max_daily_dose: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    max_duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    requires_prescription_level: Mapped[Optional[str]] = mapped_column(String(32))
    requires_consultation: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    requires_special_approval: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_restricted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    restriction_note: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DrugDdi(Base):
    __tablename__ = "mdm_drug_ddi"
    __table_args__ = (
        UniqueConstraint("drug_id", "interact_drug_id", name="uk_ddi"),
        Index("idx_drug", "drug_id"),
        Index("idx_severity", "severity"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    interact_drug_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    interact_drug_name: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    mechanism: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    management: Mapped[Optional[str]] = mapped_column(Text)
    evidence_level: Mapped[Optional[str]] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class DrugChangeLog(Base):
    __tablename__ = "mdm_drug_change_log"
    __table_args__ = (
        Index("idx_drug", "drug_id", "created_at"),
        Index("idx_code", "drug_code"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    drug_code: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_data: Mapped[Optional[dict]] = mapped_column(JSON)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON)
    diff_fields: Mapped[Optional[list]] = mapped_column(JSON)
    operator_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    operator_ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DrugSyncLog(Base):
    __tablename__ = "mdm_drug_sync_log"
    __table_args__ = (
        Index("idx_batch", "batch_no"),
        Index("idx_drug", "drug_id"),
        Index("idx_status", "status", "target_system"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_no: Mapped[str] = mapped_column(String(64), nullable=False)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    drug_code: Mapped[str] = mapped_column(String(32), nullable=False)
    target_system: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    response: Mapped[Optional[str]] = mapped_column(String)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 03.14 Pydantic Schema 定义

```python
# app/schemas/mdm/drug.py
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class DrugAliasSchema(BaseModel):
    alias_name: str = Field(..., max_length=128)
    alias_type: str = "COMMON"
    sort_order: int = 100


class DrugBarcodeSchema(BaseModel):
    barcode: str = Field(..., max_length=64)
    barcode_type: str = "GTIN"
    package_level: str = "PACKAGE"
    is_default: bool = False


class DrugPriceSchema(BaseModel):
    price_type: str
    price: Decimal
    unit: str
    effective_date: date
    expiry_date: Optional[date] = None
    approval_no: Optional[str] = None
    approval_date: Optional[date] = None
    change_reason: Optional[str] = None


class DrugStockPolicySchema(BaseModel):
    warehouse_code: Optional[str] = None
    safety_stock: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    max_stock: Optional[Decimal] = None
    reorder_point: Optional[Decimal] = None
    reorder_quantity: Optional[Decimal] = None
    lead_time_days: Optional[int] = None
    default_location_code: Optional[str] = None
    is_auto_reorder: bool = False
    expiry_alert_days: int = 90
    expiry_warning_days: int = 30
    stock_alert_enabled: bool = True


class DrugPrescriptionSchema(BaseModel):
    route: str = "ORAL"
    default_frequency: Optional[str] = None
    default_dose: Optional[Decimal] = None
    default_dose_unit: Optional[str] = None
    default_duration_days: Optional[int] = None
    max_single_dose: Optional[Decimal] = None
    max_daily_dose: Optional[Decimal] = None
    max_duration_days: Optional[int] = None
    requires_prescription_level: Optional[str] = None
    requires_consultation: bool = False
    requires_special_approval: bool = False
    is_restricted: bool = False
    restriction_note: Optional[str] = None


class DrugDdiSchema(BaseModel):
    interact_drug_id: Optional[int] = None
    interact_drug_name: str
    severity: str
    mechanism: Optional[str] = None
    description: Optional[str] = None
    management: Optional[str] = None
    evidence_level: Optional[str] = None


class DrugExtSchema(BaseModel):
    default_supplier_id: Optional[int] = None
    default_warehouse_code: Optional[str] = None
    default_location_code: Optional[str] = None
    default_charge_item_code: Optional[str] = None
    default_account_code: Optional[str] = None
    cost_center_code: Optional[str] = None
    therapeutic_effect: Optional[str] = None
    adverse_reaction: Optional[str] = None
    contraindication: Optional[str] = None
    precaution: Optional[str] = None
    drug_interaction: Optional[str] = None
    dosage_adult: Optional[str] = None
    dosage_child: Optional[str] = None
    dosage_elderly: Optional[str] = None
    dosage_renal: Optional[str] = None
    dosage_hepatic: Optional[str] = None
    pregnancy_category: Optional[str] = None
    lactation_safety: Optional[str] = None
    pediatric_use: Optional[str] = None
    elderly_use: Optional[str] = None
    max_single_dose: Optional[Decimal] = None
    max_daily_dose: Optional[Decimal] = None
    max_course_days: Optional[int] = None
    third_party_codes: Optional[Dict[str, str]] = None
    ext_config: Optional[Dict[str, Any]] = None
    remark: Optional[str] = None


class DrugBase(BaseModel):
    drug_name: str = Field(..., max_length=128)
    drug_generic_name: str = Field(..., max_length=128)
    drug_trade_name: Optional[str] = None
    drug_english_name: Optional[str] = None
    drug_alias: Optional[str] = None
    drug_category: str
    dosage_form: str
    pharmacology_class: Optional[str] = None
    management_class: Optional[str] = None
    antibiotic_level: Optional[str] = None
    ophthalmic_class: Optional[str] = None
    atc_code: Optional[str] = None
    national_drug_code: Optional[str] = None
    medical_insurance_code: Optional[str] = None
    commercial_insurance_code: Optional[str] = None
    specification: str = Field(..., max_length=128)
    concentration: Optional[str] = None
    package_unit: str
    package_quantity: Optional[Decimal] = None
    dose_unit: str
    min_unit: str
    conversion_ratio: Decimal = Decimal("1")
    is_split: bool = False
    is_batch_managed: bool = True
    is_expiry_managed: bool = True
    is_cold_chain: bool = False
    is_high_risk: bool = False
    is_essential: bool = False
    is_imported: bool = False
    is_otc: bool = False
    is_psychotropic: bool = False
    is_narcotic: bool = False
    is_toxic: bool = False
    is_radioactive: bool = False
    is_antibiotic: bool = False
    is_ophthalmic: bool = True
    manufacturer: Optional[str] = None
    manufacturer_code: Optional[str] = None
    origin_place: Optional[str] = None
    approval_number: Optional[str] = None
    approval_date: Optional[date] = None
    registration_standard: Optional[str] = None
    shelf_life_months: Optional[int] = None
    storage_condition: Optional[str] = None
    storage_temp_min: Optional[Decimal] = None
    storage_temp_max: Optional[Decimal] = None
    is_light_protected: bool = False
    is_moisture_protected: bool = False
    after_open_shelf_life: Optional[int] = None
    is_after_open_managed: bool = False
    drug_image_url: Optional[str] = None
    drug_instruction_url: Optional[str] = None
    drug_label_url: Optional[str] = None
    remark: Optional[str] = Field(None, max_length=512)

    @field_validator("conversion_ratio")
    @classmethod
    def validate_ratio(cls, v):
        if v <= 0:
            raise ValueError("转换比必须大于 0")
        return v


class DrugCreate(DrugBase):
    drug_code: Optional[str] = None
    ext: Optional[DrugExtSchema] = None
    aliases: Optional[List[DrugAliasSchema]] = None
    barcodes: Optional[List[DrugBarcodeSchema]] = None
    prices: Optional[List[DrugPriceSchema]] = None
    stock_policy: Optional[DrugStockPolicySchema] = None
    prescriptions: Optional[List[DrugPrescriptionSchema]] = None
    ddis: Optional[List[DrugDdiSchema]] = None


class DrugUpdate(DrugBase):
    version: int
    ext: Optional[DrugExtSchema] = None
    aliases: Optional[List[DrugAliasSchema]] = None
    barcodes: Optional[List[DrugBarcodeSchema]] = None
    stock_policy: Optional[DrugStockPolicySchema] = None
    prescriptions: Optional[List[DrugPrescriptionSchema]] = None
    ddis: Optional[List[DrugDdiSchema]] = None


class DrugStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(ENABLED|DISABLED|RECALLED)$")
    reason: Optional[str] = Field(None, max_length=255)


class DrugPriceAdjust(BaseModel):
    price_type: str
    new_price: Decimal
    unit: str
    effective_date: date
    approval_no: Optional[str] = None
    change_reason: Optional[str] = None


class DrugQuery(BaseModel):
    keyword: Optional[str] = None
    drug_category: Optional[str] = None
    dosage_form: Optional[str] = None
    pharmacology_class: Optional[str] = None
    management_class: Optional[str] = None
    antibiotic_level: Optional[str] = None
    ophthalmic_class: Optional[str] = None
    is_ophthalmic: Optional[bool] = None
    is_essential: Optional[bool] = None
    is_high_risk: Optional[bool] = None
    is_cold_chain: Optional[bool] = None
    is_narcotic: Optional[bool] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "drug_code"
    sort_dir: str = "asc"


class DrugVO(DrugBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drug_code: str
    pinyin_code: str
    pinyin_short: str
    status: str
    audit_status: str
    version: int
    created_by: int
    created_at: datetime
    updated_by: Optional[int]
    updated_at: datetime
    ext: Optional[DrugExtSchema] = None
    aliases: Optional[List[DrugAliasSchema]] = None
    barcodes: Optional[List[DrugBarcodeSchema]] = None
    prices: Optional[List[DrugPriceSchema]] = None
    stock_policy: Optional[DrugStockPolicySchema] = None
    prescriptions: Optional[List[DrugPrescriptionSchema]] = None


class DrugSimpleVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    drug_code: str
    drug_name: str
    drug_generic_name: str
    specification: str
    dosage_form: str
    package_unit: str
    min_unit: str
    pinyin_short: str
    is_otc: bool
    is_high_risk: bool
    status: str
    retail_price: Optional[Decimal] = None


class PageResult(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
```

---

---

## 04. 耗材数据结构

> **来源：** [耗材详细设计](M01_主数据管理MDM_04_耗材_详细设计.md) · 第 4 章
> **主数据域：** 物资域（`MAT`） · **表数：** 22

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 04.2 | `mdm_material` | 耗材主表 |
| 04.3 | `mdm_material_ext` | 耗材扩展表 |
| 04.4 | `mdm_material_alias` | 耗材别名表 |
| 04.5 | `mdm_material_barcode` | 耗材条码 / UDI 表 |
| 04.6 | `mdm_material_price` | 耗材价格表 |
| 04.7 | `mdm_material_stock_policy` | 库存策略表 |
| 04.8 | `mdm_material_iol` | 人工晶体专档表 |
| 04.9 | `mdm_material_implant` | 植入物追溯配置表 |
| 04.10 | `mdm_material_reagent` | 检验试剂配置表 |
| 04.11 | `mdm_material_consumable_attr` | 耗材通用属性表 |
| 04.12 | `mdm_material_charge_rel` | 耗材-收费项目关联表 |
| 04.13 | `mdm_material_supplier_rel` | 供应商供货关系表 |
| 04.14 | `mdm_surgery_kit` | 手术套包主表 |
| 04.15 | `mdm_surgery_kit_detail` | 手术套包明细表 |
| 04.16 | `mdm_material_registration` | 注册证 / 资质证照表 |
| 04.17 | `mdm_material_change_log` | 变更日志表 |
| 04.18 | `mdm_material_approval` | 审批记录表 |
| 04.19 | `mdm_material_sync_log` | 同步日志表 |
| 04.20 | `mdm_material_code_seq` | 编码序列表 |
| 04.21 | `mdm_material_import_task` | 导入任务表 |
| 04.22 | `mdm_material_recall` | 耗材召回表 |
| 04.23 | `mdm_material_recall_detail` | 召回影响明细表 |

---

### 04.1 ER 关系图

```
                          ┌──────────────────────────┐
                          │  mdm_material            │
                          │  （耗材主表）             │
                          └────────────┬─────────────┘
                                       │ 1
          ┌────────────────────────────┼────────────────────────────┐
          │              │             │             │              │
          │ 1:1          │ 1:N         │ 1:N         │ 1:N          │ 1:N
          ▼              ▼             ▼             ▼              ▼
┌──────────────────┐ ┌──────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────┐
│ mdm_material_ext │ │ ..._alias│ │..._barcode│ │..._price   │ │..._stock_    │
│ （扩展表）        │ │（别名）   │ │（条码/UDI）│ │（价格表）   │ │  policy（策略）│
└──────────────────┘ └──────────┘ └───────────┘ └────────────┘ └──────────────┘
          │
          │ 1:1（按分类条件分支）
          ├──────────────────┬──────────────────┬──────────────────┐
          ▼                  ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ mdm_material_iol │ │..._implant（植入）│ │..._reagent（试剂）│ │..._consumable    │
│ （人工晶体专档）  │ │（植入物追溯配置） │ │（检验试剂配置）   │ │ _attr（通用属性） │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
          │
          │ N:M（套包与收费关联）
          ├──────────────────┬──────────────────┬──────────────────┐
          ▼                  ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ mdm_surgery_kit  │ │..._kit_detail    │ │..._charge_rel    │ │..._supplier_rel  │
│ （手术套包）      │ │（套包明细）       │ │（收费项目关联）   │ │（供应商供货关系） │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
          │
          │ 1:N（治理）
          ├──────────────────┬──────────────────┬──────────────────┐
          ▼                  ▼                  ▼                  ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│..._change_log    │ │..._sync_log      │ │..._code_seq      │ │..._registration  │
│（变更日志）       │ │（同步日志）       │ │（编码序列）       │ │（注册证）         │
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘
```

**表清单（共 22 张）：**

| 序号 | 表名 | 中文名 | 关系 | 预估量级 |
|---|---|---|---|---|
| 1 | `mdm_material` | 耗材主表 | 主表 | 5,000 |
| 2 | `mdm_material_ext` | 耗材扩展表 | 1:1 | 5,000 |
| 3 | `mdm_material_alias` | 耗材别名表 | 1:N | 6,000 |
| 4 | `mdm_material_barcode` | 耗材条码/UDI 表 | 1:N | 20,000 |
| 5 | `mdm_material_price` | 耗材价格表 | 1:N | 25,000 |
| 6 | `mdm_material_stock_policy` | 库存策略表 | 1:N | 8,000 |
| 7 | `mdm_material_iol` | 人工晶体专档表 | 1:1 | 3,000 |
| 8 | `mdm_material_implant` | 植入物追溯配置表 | 1:1 | 1,500 |
| 9 | `mdm_material_reagent` | 检验试剂配置表 | 1:1 | 500 |
| 10 | `mdm_material_consumable_attr` | 耗材通用属性表 | 1:1 | 5,000 |
| 11 | `mdm_material_charge_rel` | 收费项目关联表 | 1:N | 6,000 |
| 12 | `mdm_material_supplier_rel` | 供应商供货关系表 | 1:N | 12,000 |
| 13 | `mdm_surgery_kit` | 手术套包主表 | 主表 | 100 |
| 14 | `mdm_surgery_kit_detail` | 手术套包明细表 | 1:N | 1,500 |
| 15 | `mdm_material_registration` | 注册证/资质证照表 | 1:N | 8,000 |
| 16 | `mdm_material_change_log` | 变更日志表 | 1:N | 60,000/年 |
| 17 | `mdm_material_approval` | 审批记录表 | 1:N | 6,000/年 |
| 18 | `mdm_material_sync_log` | 同步日志表 | 1:N | 200,000/年 |
| 19 | `mdm_material_code_seq` | 编码序列表 | 独立 | 200 |
| 20 | `mdm_material_import_task` | 导入任务表 | 独立 | 2,000/年 |
| 21 | `mdm_material_recall` | 耗材召回表 | 主表 | 100/年 |
| 22 | `mdm_material_recall_detail` | 召回影响明细表 | 1:N | 5,000/年 |

### 04.2 表：`mdm_material`（耗材主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_code | VARCHAR(32) | N | - | 耗材编码，全局唯一 |
| material_name | VARCHAR(200) | N | - | 耗材名称（通用名） |
| material_short_name | VARCHAR(64) | Y | NULL | 耗材简称（单据打印用） |
| material_english_name | VARCHAR(255) | Y | NULL | 英文名 |
| spec | VARCHAR(200) | N | - | 规格 |
| model | VARCHAR(128) | Y | NULL | 型号 |
| pinyin_code | VARCHAR(64) | N | - | 拼音码（全拼） |
| pinyin_short | VARCHAR(32) | N | - | 拼音首字母 |
| wubi_code | VARCHAR(64) | Y | NULL | 五笔码 |
| material_category | VARCHAR(32) | N | - | 基础分类（3.2） |
| finance_category | VARCHAR(32) | Y | NULL | 财务分类（3.3） |
| management_level | VARCHAR(32) | N | 'NORMAL' | 管理分类（3.4） |
| clinical_usage | VARCHAR(512) | Y | NULL | 临床用途（多选，逗号分隔） |
| ophthalmic_category | VARCHAR(64) | Y | NULL | 眼科专科分类（3.6） |
| insurance_category | VARCHAR(16) | N | 'NA' | 医保分类（预留） |
| brand | VARCHAR(128) | Y | NULL | 品牌 |
| manufacturer_id | BIGINT UNSIGNED | Y | NULL | 生产厂商 ID（关联 M01 生产厂商） |
| manufacturer_name | VARCHAR(200) | Y | NULL | 生产厂商名称（冗余） |
| origin_place | VARCHAR(32) | Y | NULL | 产地：IMPORTED/DOMESTIC/JOINT_VENTURE |
| origin_country | VARCHAR(64) | Y | NULL | 原产国（进口耗材） |
| agent_supplier_id | BIGINT UNSIGNED | Y | NULL | 代理供应商 ID |
| min_unit | VARCHAR(32) | N | - | 最小单位（个、支、根、片、包） |
| pack_unit | VARCHAR(32) | Y | NULL | 包装单位（盒、箱、件） |
| pack_factor | DECIMAL(12,4) | N | 1 | 包装系数（1包装单位 = N 最小单位） |
| charge_unit | VARCHAR(32) | Y | NULL | 收费单位（可与最小单位不同） |
| charge_factor | DECIMAL(12,4) | N | 1 | 收费换算系数（1 收费单位 = N 最小单位） |
| weight | DECIMAL(12,4) | Y | NULL | 重量（克） |
| volume | DECIMAL(12,4) | Y | NULL | 体积（毫升） |
| material_texture | VARCHAR(64) | Y | NULL | 材质（如硅胶、钛合金、PMMA、尼龙） |
| is_sterile | TINYINT(1) | N | 0 | 是否无菌 |
| sterile_method | VARCHAR(32) | Y | NULL | 灭菌方式：EO/IRRADIATION/STEAM/PLASMA/NONE |
| is_single_use | TINYINT(1) | N | 1 | 是否一次性使用 |
| reuse_times | INT | Y | NULL | 可复用次数（可复用耗材） |
| is_implant | TINYINT(1) | N | 0 | 是否植入物 |
| is_high_value | TINYINT(1) | N | 0 | 是否高值耗材 |
| is_chargeable | TINYINT(1) | N | 1 | 是否收费耗材 |
| is_batch_managed | TINYINT(1) | N | 1 | 是否批次管理 |
| is_expiry_managed | TINYINT(1) | N | 1 | 是否效期管理 |
| is_serial_managed | TINYINT(1) | N | 0 | 是否序列号管理 |
| is_udi_managed | TINYINT(1) | N | 0 | 是否 UDI 管理 |
| is_cold_chain | TINYINT(1) | N | 0 | 是否冷链 |
| is_high_risk | TINYINT(1) | N | 0 | 是否高危耗材（院感重点） |
| is_centralized | TINYINT(1) | N | 0 | 是否集采中选 |
| centralized_batch | VARCHAR(64) | Y | NULL | 集采批次/标期 |
| is_consignment | TINYINT(1) | N | 0 | 是否寄售 |
| is_borrowable | TINYINT(1) | N | 0 | 是否可借用 |
| registration_no | VARCHAR(128) | Y | NULL | 医疗器械注册证号 |
| registration_expire_date | DATE | Y | NULL | 注册证有效期至 |
| registration_class | VARCHAR(8) | Y | NULL | 器械管理类别：I / II / III |
| national_material_code | VARCHAR(64) | Y | NULL | 国家医保耗材编码（预留） |
| commercial_insurance_code | VARCHAR(64) | Y | NULL | 商保编码（预留） |
| his_external_code | VARCHAR(64) | Y | NULL | 外部系统编码（预留） |
| default_warehouse_id | BIGINT UNSIGNED | Y | NULL | 默认仓库 |
| default_dept_id | BIGINT UNSIGNED | Y | NULL | 默认使用科室 |
| storage_condition | VARCHAR(32) | Y | NULL | 存储条件：NORMAL/COOL/COLD/FREEZE |
| storage_temp_min | DECIMAL(5,2) | Y | NULL | 存储温度下限（℃） |
| storage_temp_max | DECIMAL(5,2) | Y | NULL | 存储温度上限（℃） |
| storage_humidity_max | DECIMAL(5,2) | Y | NULL | 湿度上限（%） |
| is_light_protected | TINYINT(1) | N | 0 | 是否避光 |
| is_moisture_protected | TINYINT(1) | N | 0 | 是否防潮 |
| shelf_life_months | INT | Y | NULL | 有效期（月） |
| after_open_shelf_life | INT | Y | NULL | 开封后效期（小时/天，配合单位） |
| after_open_unit | VARCHAR(8) | Y | NULL | 开封后效期单位：HOUR/DAY |
| image_url | VARCHAR(500) | Y | NULL | 耗材图片 URL |
| instruction_url | VARCHAR(500) | Y | NULL | 说明书 URL |
| account_subject | VARCHAR(64) | Y | NULL | 会计科目 |
| cost_method | VARCHAR(32) | Y | NULL | 成本核算方法：FIFO/WEIGHTED/SPECIFIC |
| dept_accounting | TINYINT(1) | N | 1 | 是否参与科室核算 |
| status | VARCHAR(16) | N | 'DRAFT' | 业务状态：DRAFT/ENABLED/DISABLED/RECALLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态：DRAFT/PENDING/APPROVED/REJECTED |
| version | INT | N | 0 | 乐观锁版本号 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| ext_json | JSON | Y | NULL | 扩展字段 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_material | PRIMARY | id | 主键 |
| uk_material_code | UNIQUE | material_code, deleted | 编码唯一 |
| uk_name_spec_mfr | UNIQUE | material_name, spec, manufacturer_id, deleted | 名称+规格+厂商唯一 |
| idx_name | NORMAL | material_name | 名称查询 |
| idx_short_name | NORMAL | material_short_name | 简称查询 |
| idx_pinyin | NORMAL | pinyin_code, pinyin_short | 拼音搜索 |
| idx_category | NORMAL | material_category | 分类过滤 |
| idx_finance | NORMAL | finance_category | 财务分类 |
| idx_management | NORMAL | management_level | 管理分类 |
| idx_ophthalmic | NORMAL | ophthalmic_category | 眼科分类 |
| idx_brand | NORMAL | brand | 品牌查询 |
| idx_manufacturer | NORMAL | manufacturer_id | 厂商查询 |
| idx_registration_expire | NORMAL | registration_expire_date | 证照到期预警 |
| idx_status | NORMAL | status, audit_status | 状态过滤 |
| idx_implant | NORMAL | is_implant, is_high_value | 植入物/高值筛选 |
| idx_updated | NORMAL | updated_at | 增量同步 |
| ft_name | FULLTEXT | material_name, material_short_name, material_english_name | 中文分词检索 |

> **中文全文索引说明**：MySQL 8.0 需 `WITH PARSER ngram`，`ngram_token_size=2`。

### 04.3 表：`mdm_material_ext`（耗材扩展表）

用于承载使用频率低、数量多的扩展属性，避免主表过宽。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码（冗余） |
| procurement_type | VARCHAR(32) | Y | NULL | 采购类型：CENTRALIZED/LOCAL/EMERGENCY |
| procurement_cycle_days | INT | Y | NULL | 采购周期（天） |
| lead_time_days | INT | Y | NULL | 到货周期（天） |
| min_order_qty | DECIMAL(12,4) | Y | NULL | 最小起订量 |
| economic_order_qty | DECIMAL(12,4) | Y | NULL | 经济订货量 |
| is_kit_component | TINYINT(1) | N | 0 | 是否套包组件 |
| is_loanable | TINYINT(1) | N | 0 | 是否可借用（跟台） |
| is_returnable | TINYINT(1) | N | 1 | 是否可退货 |
| return_days | INT | Y | NULL | 退货期限（天） |
| is_consignment_settle_by_usage | TINYINT(1) | N | 0 | 寄售按使用结算 |
| barcode_rule | VARCHAR(64) | Y | NULL | 院内条码规则 |
| label_template | VARCHAR(64) | Y | NULL | 标签模板 |
| qc_required | TINYINT(1) | N | 0 | 是否需要到货质检 |
| qc_items | VARCHAR(1000) | Y | NULL | 质检项目（JSON 数组字符串） |
| trace_direction | VARCHAR(32) | Y | NULL | 追溯方向：FORWARD/BACKWARD/BOTH |
| trace_required | TINYINT(1) | N | 0 | 是否强制追溯 |
| trace_fields | VARCHAR(1000) | Y | NULL | 追溯必填字段（JSON 数组字符串） |
| recall_status | VARCHAR(16) | N | 'NORMAL' | 召回状态：NORMAL/RECALLING/RECALLED |
| risk_level | VARCHAR(16) | Y | NULL | 风险等级：HIGH/MEDIUM/LOW |
| adverse_event_report | TINYINT(1) | N | 0 | 是否需不良事件上报 |
| custom_fields | JSON | Y | NULL | 自定义字段值 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material (material_id, deleted)` 唯一；`idx_trace (trace_required)`；`idx_recall (recall_status)`。

### 04.4 表：`mdm_material_alias`（耗材别名表）

用于支持同一耗材的多种叫法（临床习惯名、供应商名、旧系统名），提升检索命中率。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| alias_name | VARCHAR(200) | N | - | 别名 |
| alias_type | VARCHAR(32) | N | 'CLINICAL' | 别名类型：CLINICAL/SUPPLIER/HISTORICAL/ABBREVIATION |
| pinyin_code | VARCHAR(64) | Y | NULL | 别名拼音码 |
| pinyin_short | VARCHAR(32) | Y | NULL | 别名拼音首字母 |
| sort_no | INT | N | 999 | 排序 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_alias (material_id, alias_name, deleted)` 唯一；`idx_alias_name (alias_name)`；`idx_alias_pinyin (pinyin_short)`。

### 04.5 表：`mdm_material_barcode`（耗材条码 / UDI 表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| barcode | VARCHAR(128) | N | - | 条码（院内码/厂商码） |
| barcode_type | VARCHAR(32) | N | 'INTERNAL' | 条码类型：INTERNAL/GS1/HIBC/UDI/SUPPLIER |
| udi_di | VARCHAR(128) | Y | NULL | UDI-DI（器械标识） |
| udi_pi | VARCHAR(128) | Y | NULL | UDI-PI（生产标识，含批号/效期/序列号） |
| gtin | VARCHAR(64) | Y | NULL | GTIN（全球贸易项目代码） |
| is_primary | TINYINT(1) | N | 0 | 是否主条码 |
| is_udi_carrier | TINYINT(1) | N | 0 | 是否 UDI 载体条码 |
| pack_level | VARCHAR(16) | N | 'UNIT' | 包装层级：UNIT/PACK/CASE |
| pack_qty | DECIMAL(12,4) | Y | NULL | 该条码对应的最小单位数量 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态：ENABLED/DISABLED |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_barcode (barcode, deleted)` 唯一；`idx_udi_di (udi_di)`；`idx_gtin (gtin)`；`idx_material (material_id)`。

> **约束**：同一耗材仅允许一个 `is_primary=1` 的条码；UDI 管理的耗材必须有且仅有一个 `is_udi_carrier=1` 的条码。

### 04.6 表：`mdm_material_price`（耗材价格表）

价格采用**版本化**设计：每次调价新增一条记录，旧记录写入 `expire_date`，历史单据按业务发生时间取价。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| price_type | VARCHAR(32) | N | 'RETAIL' | 价格类型：PURCHASE/RETAIL/CENTRALIZED/MEMBER/CONTRACT |
| price | DECIMAL(14,4) | N | 0 | 价格 |
| currency | VARCHAR(8) | N | 'CNY' | 币种 |
| price_unit | VARCHAR(32) | N | - | 计价单位 |
| markup_rate | DECIMAL(7,4) | Y | NULL | 加价率（%） |
| max_retail_price | DECIMAL(14,4) | Y | NULL | 最高零售限价 |
| min_retail_price | DECIMAL(14,4) | Y | NULL | 最低零售限价 |
| is_one_price_one_item | TINYINT(1) | N | 0 | 是否一物一价 |
| supplier_id | BIGINT UNSIGNED | Y | NULL | 供应商（采购价适用） |
| contract_no | VARCHAR(64) | Y | NULL | 合同号 |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL = 当前有效） |
| is_current | TINYINT(1) | N | 1 | 是否当前有效价 |
| adjust_reason | VARCHAR(255) | Y | NULL | 调价原因 |
| adjust_doc_no | VARCHAR(64) | Y | NULL | 调价文号 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `idx_material_type (material_id, price_type, is_current)`；`idx_effective (effective_date, expire_date)`；`idx_supplier (supplier_id)`。

> **唯一性约束**：同一 `material_id + price_type + supplier_id` 在同一时间区间内只能有一条 `is_current=1` 的记录（由业务层 + 唯一索引 `uk_current (material_id, price_type, supplier_id, is_current, deleted)` 保证，其中 `is_current=0` 时该索引字段取记录 ID 以规避冲突，见 8.6 节实现说明）。

### 04.7 表：`mdm_material_stock_policy`（库存策略表）

一个耗材在不同仓库可有不同策略，故为 1:N。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| warehouse_id | BIGINT UNSIGNED | Y | NULL | 仓库 ID（NULL = 全院默认策略） |
| warehouse_type | VARCHAR(32) | Y | NULL | 仓库类型（二级库/高值柜等） |
| safety_stock | DECIMAL(14,4) | Y | NULL | 安全库存 |
| min_stock | DECIMAL(14,4) | Y | NULL | 最低库存（补货触发点） |
| max_stock | DECIMAL(14,4) | Y | NULL | 最高库存（超储预警） |
| reorder_point | DECIMAL(14,4) | Y | NULL | 再订货点 |
| reorder_qty | DECIMAL(14,4) | Y | NULL | 建议订货量 |
| is_zero_stock | TINYINT(1) | N | 0 | 是否零库存管理（用后补货） |
| is_secondary_stock | TINYINT(1) | N | 0 | 是否二级库管理（手术室） |
| is_consignment | TINYINT(1) | N | 0 | 是否寄售 |
| consignment_supplier_id | BIGINT UNSIGNED | Y | NULL | 寄售供应商 |
| fifo_rule | VARCHAR(32) | N | 'FEFO' | 出库规则：FIFO/FEFO/LIFO |
| expiry_warning_days | INT | Y | 90 | 效期预警天数 |
| expiry_forbid_days | INT | Y | 0 | 近效期禁用天数（0=不禁用） |
| batch_required | TINYINT(1) | N | 1 | 是否必须录入批号 |
| serial_required | TINYINT(1) | N | 0 | 是否必须录入序列号 |
| udi_scan_required | TINYINT(1) | N | 0 | 是否必须扫码（UDI） |
| allow_negative_stock | TINYINT(1) | N | 0 | 是否允许负库存 |
| stock_unit | VARCHAR(32) | Y | NULL | 库存单位 |
| auto_purchase | TINYINT(1) | N | 0 | 是否自动生成采购申请 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material_warehouse (material_id, warehouse_id, deleted)` 唯一；`idx_warehouse (warehouse_id)`；`idx_zero_stock (is_zero_stock)`。

**校验：** `min_stock <= safety_stock <= max_stock`；`reorder_point <= max_stock`。

### 04.8 表：`mdm_material_iol`（人工晶体专档表）

人工晶体是眼科最核心的高值植入物，SKU 按"品牌 × 型号 × 球镜 × 柱镜"细分，需要独立的参数表支撑 IOL 度数计算与手术选型。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| udi_di | VARCHAR(128) | Y | NULL | UDI-DI |
| brand | VARCHAR(128) | N | - | 品牌（Alcon/Abbott/J&J/Zeiss/爱博诺德/昊海等） |
| model | VARCHAR(128) | N | - | 型号（如 SN60WF、ZCB00、AE2UV） |
| product_name | VARCHAR(200) | N | - | 产品名称 |
| iol_type | VARCHAR(32) | N | - | 晶体类型（见下） |
| optic_type | VARCHAR(32) | Y | NULL | 光学类型：SPHERICAL/ASPHERICAL/TORIC/MULTIFOCAL |
| sphere_power | DECIMAL(6,2) | N | - | 球镜度数（D），范围 -30.00 ~ +40.00 |
| cylinder_power | DECIMAL(6,2) | Y | NULL | 柱镜度数（D），Toric 晶体必填 |
| axis_range | VARCHAR(32) | Y | NULL | 轴位范围（如 0~180°） |
| addition_power | DECIMAL(6,2) | Y | NULL | 附加度数（多焦/三焦晶体） |
| a_constant | DECIMAL(6,2) | N | - | A 常数（IOL 度数计算用） |
| a_constant_type | VARCHAR(16) | N | 'SRK_T' | A 常数类型：SRK_T/HOLLADAY/HAIGIS |
| surgeon_factor | DECIMAL(6,3) | Y | NULL | 术者因子 |
| optic_diameter | DECIMAL(5,2) | Y | NULL | 光学区直径（mm） |
| total_diameter | DECIMAL(5,2) | Y | NULL | 总直径（mm） |
| haptic_type | VARCHAR(32) | Y | NULL | 襻型：C_LOOP/PLATE/TRIPLE_LOOP/OPEN_LOOP |
| haptic_angle | VARCHAR(32) | Y | NULL | 襻角度（如 0°/6°） |
| lens_material | VARCHAR(64) | Y | NULL | 晶体材质：HYDROPHOBIC_ACRYLIC/HYDROPHILIC_ACRYLIC/SILICONE/PMMA/COLLAMER |
| refractive_index | DECIMAL(5,3) | Y | NULL | 折射率 |
| is_preloaded | TINYINT(1) | N | 0 | 是否预装式 |
| injector_type | VARCHAR(64) | Y | NULL | 推注器类型 |
| incision_size | VARCHAR(32) | Y | NULL | 推荐切口尺寸（mm） |
| is_toric | TINYINT(1) | N | 0 | 是否散光矫正型 |
| is_multifocal | TINYINT(1) | N | 0 | 是否多焦/三焦 |
| is_edof | TINYINT(1) | N | 0 | 是否连续视程（EDOF） |
| is_blue_light_filter | TINYINT(1) | N | 0 | 是否蓝光滤过 |
| is_uv_filter | TINYINT(1) | N | 1 | 是否防紫外线 |
| aspheric_value | DECIMAL(6,3) | Y | NULL | 非球面系数 |
| suitable_patient | VARCHAR(500) | Y | NULL | 适用患者说明 |
| contraindication | VARCHAR(500) | Y | NULL | 禁忌症 |
| operation_ids | VARCHAR(500) | Y | NULL | 适配手术项目 ID（逗号分隔） |
| need_navigation | TINYINT(1) | N | 0 | 是否需术中导航 |
| need_intraoperative_aberrometry | TINYINT(1) | N | 0 | 是否需术中像差测量 |
| power_range_min | DECIMAL(6,2) | Y | NULL | 该型号度数范围下限 |
| power_range_max | DECIMAL(6,2) | Y | NULL | 该型号度数范围上限 |
| power_step | DECIMAL(5,2) | Y | 0.50 | 度数步进 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**iol_type 取值：**

| 代码 | 名称 | 说明 |
|---|---|---|
| `MONOFOCAL_SPHERICAL` | 单焦球面 | 基础型 |
| `MONOFOCAL_ASPHERICAL` | 单焦非球面 | 主流 |
| `BIFOCAL` | 双焦 | 远近两焦点 |
| `TRIFOCAL` | 三焦 | 远中近三焦点 |
| `TORIC` | 散光矫正型 | 需柱镜与轴位 |
| `EDOF` | 连续视程 | 扩展景深 |
| `ICL` | 有晶体眼后房型人工晶体 | 屈光手术用 |
| `PRL` | 后房型屈光晶体 | 屈光手术用 |
| `PHAKIC_IOL` | 有晶体眼人工晶体 | 通用 |
| `ADD_ON_IOL` | 附加式人工晶体 | 二次植入 |

**索引：** `uk_material (material_id, deleted)` 唯一；`idx_udi (udi_di)`；`idx_brand_model (brand, model)`；`idx_power (sphere_power, cylinder_power)`；`idx_type (iol_type)`；`idx_toric (is_toric)`。

**唯一性约束：** `uk_brand_model_power (brand, model, sphere_power, cylinder_power, deleted)` 唯一，防止同一度数重复建档。

### 04.9 表：`mdm_material_implant`（植入物追溯配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| implant_category | VARCHAR(64) | N | - | 植入物类别（见下） |
| implant_site | VARCHAR(64) | Y | NULL | 植入部位：EYE_ANTERIOR/EYE_POSTERIOR/ORBIT/OCULAR_SURFACE/LACRIMAL |
| is_permanent | TINYINT(1) | N | 1 | 是否永久植入 |
| expected_life_years | INT | Y | NULL | 预期使用年限 |
| trace_required | TINYINT(1) | N | 1 | 是否强制追溯 |
| trace_direction | VARCHAR(32) | N | 'BOTH' | 追溯方向：FORWARD/BACKWARD/BOTH |
| trace_fields | VARCHAR(1000) | Y | NULL | 追溯必填字段（JSON：batch_no/serial_no/udi/expire_date/registration_no） |
| patient_binding_required | TINYINT(1) | N | 1 | 是否强制绑定患者 |
| binding_timing | VARCHAR(32) | N | 'INTRAOPERATIVE' | 绑定时机：PREOPERATIVE/INTRAOPERATIVE/POSTOPERATIVE |
| require_implant_record | TINYINT(1) | N | 1 | 是否生成植入物登记表 |
| require_consent | TINYINT(1) | N | 0 | 是否需要知情同意 |
| require_followup | TINYINT(1) | N | 1 | 是否需要术后随访 |
| followup_days | VARCHAR(128) | Y | NULL | 随访周期（天，逗号分隔） |
| mri_compatible | VARCHAR(16) | Y | NULL | MRI 兼容性：YES/NO/CONDITIONAL |
| mri_condition | VARCHAR(255) | Y | NULL | MRI 兼容条件说明 |
| adverse_event_report | TINYINT(1) | N | 1 | 是否需不良事件上报 |
| recall_level | VARCHAR(16) | Y | NULL | 召回级别：I/II/III |
| registration_no | VARCHAR(128) | Y | NULL | 注册证号 |
| registration_expire_date | DATE | Y | NULL | 注册证有效期 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**implant_category 取值：**

| 代码 | 名称 | 眼科典型产品 |
|---|---|---|
| `IOL` | 人工晶体 | 各类人工晶体 |
| `GLAUCOMA_DEVICE` | 青光眼引流装置 | Ahmed/Baerveldt 引流阀、Ex-PRESS 引流钉 |
| `VITREOUS_SUBSTITUTE` | 玻璃体替代物 | 硅油、重水 |
| `ORBITAL_IMPLANT` | 眼眶植入物 | 义眼台、眼眶修补网片 |
| `OCULAR_SURFACE_IMPLANT` | 眼表植入物 | 生物羊膜、角膜基质 |
| `LACRIMAL_IMPLANT` | 泪道植入物 | 泪道支架、硅胶管 |
| `CORNEA_IMPLANT` | 角膜植入物 | 角膜环、角膜基质环 |
| `SUTURE_IMPLANT` | 缝合固定材料 | 悬吊缝线、固定锚 |
| `OTHER_IMPLANT` | 其他植入物 | — |

**索引：** `uk_material (material_id, deleted)` 唯一；`idx_category (implant_category)`；`idx_trace (trace_required)`。

### 04.10 表：`mdm_material_reagent`（检验试剂配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| reagent_type | VARCHAR(32) | N | - | 试剂类型：REAGENT/CALIBRATOR/CONTROL/CONSUMABLE |
| test_count_per_pack | INT | Y | NULL | 每盒测试数 |
| lab_item_ids | VARCHAR(1000) | Y | NULL | 关联检验项目 ID（逗号分隔） |
| lab_combo_ids | VARCHAR(1000) | Y | NULL | 关联检验组合 ID |
| analyzer_model | VARCHAR(128) | Y | NULL | 适用仪器型号 |
| is_open_vial_managed | TINYINT(1) | N | 1 | 是否管理开瓶效期 |
| open_vial_shelf_life | INT | Y | NULL | 开瓶后效期 |
| open_vial_unit | VARCHAR(8) | Y | NULL | 开瓶效期单位：HOUR/DAY |
| storage_reagent_condition | VARCHAR(64) | Y | NULL | 试剂存储条件 |
| is_calibration_required | TINYINT(1) | N | 0 | 是否需要校准 |
| calibration_interval_days | INT | Y | NULL | 校准周期（天） |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material (material_id, deleted)` 唯一；`idx_reagent_type (reagent_type)`。

### 04.11 表：`mdm_material_consumable_attr`（耗材通用属性表）

承载消毒、护理等耗材的通用属性，避免扩展表过度膨胀。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| color | VARCHAR(32) | Y | NULL | 颜色 |
| size_spec | VARCHAR(64) | Y | NULL | 尺寸规格（如 7.0#、10cm×10cm） |
| thickness | DECIMAL(8,3) | Y | NULL | 厚度（mm） |
| length | DECIMAL(8,2) | Y | NULL | 长度（mm/cm） |
| width | DECIMAL(8,2) | Y | NULL | 宽度（mm/cm） |
| diameter | DECIMAL(8,3) | Y | NULL | 直径（mm） |
| capacity | DECIMAL(10,2) | Y | NULL | 容量（ml） |
| needle_gauge | VARCHAR(16) | Y | NULL | 针头规格（G） |
| needle_length | DECIMAL(6,2) | Y | NULL | 针头长度（mm） |
| suture_size | VARCHAR(16) | Y | NULL | 缝线规格（10-0/8-0） |
| suture_length | DECIMAL(6,2) | Y | NULL | 缝线长度（cm） |
| suture_needle_type | VARCHAR(32) | Y | NULL | 缝针类型（圆针/三角针/铲针） |
| suture_absorbable | TINYINT(1) | N | 0 | 是否可吸收 |
| drainage_type | VARCHAR(32) | Y | NULL | 引流类型 |
| fluid_type | VARCHAR(32) | Y | NULL | 液体类型 |
| device_class | VARCHAR(8) | Y | NULL | 器械类别 |
| electrical_required | TINYINT(1) | N | 0 | 是否需供电 |
| power_spec | VARCHAR(64) | Y | NULL | 电源规格 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

### 04.12 表：`mdm_material_charge_rel`（耗材-收费项目关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费项目编码 |
| charge_item_name | VARCHAR(200) | Y | NULL | 收费项目名称（冗余） |
| rel_type | VARCHAR(32) | N | 'PRIMARY' | 关联类型：PRIMARY/SECONDARY/BUNDLED |
| is_default | TINYINT(1) | N | 0 | 是否默认收费项 |
| charge_qty_factor | DECIMAL(12,4) | N | 1 | 收费数量换算（1 耗材单位 = N 收费数量） |
| auto_charge | TINYINT(1) | N | 1 | 是否自动计费 |
| charge_scene | VARCHAR(64) | Y | NULL | 计费场景（手术/门诊/住院/视光） |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material_charge (material_id, charge_item_id, deleted)` 唯一；`idx_charge_item (charge_item_id)`。

> **约束**：同一耗材可有多个关联收费项，但 `is_default=1` 只能有一个（不同场景可各有一个）。

### 04.13 表：`mdm_material_supplier_rel`（供应商供货关系表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| supplier_id | BIGINT UNSIGNED | N | - | 供应商 ID |
| supplier_name | VARCHAR(200) | Y | NULL | 供应商名称（冗余） |
| is_primary | TINYINT(1) | N | 0 | 是否主供应商 |
| supplier_material_code | VARCHAR(64) | Y | NULL | 供应商物料编码 |
| supplier_material_name | VARCHAR(200) | Y | NULL | 供应商物料名称 |
| supply_type | VARCHAR(32) | N | 'NORMAL' | 供货类型：NORMAL/CONSIGNMENT/FOLLOW_UP/BORROW |
| purchase_price | DECIMAL(14,4) | Y | NULL | 采购价 |
| price_unit | VARCHAR(32) | Y | NULL | 价格单位 |
| currency | VARCHAR(8) | N | 'CNY' | 币种 |
| min_order_qty | DECIMAL(12,4) | Y | NULL | 最小起订量 |
| lead_time_days | INT | Y | NULL | 到货周期（天） |
| contract_no | VARCHAR(64) | Y | NULL | 合同号 |
| contract_start | DATE | Y | NULL | 合同起始 |
| contract_end | DATE | Y | NULL | 合同到期 |
| is_qualified | TINYINT(1) | N | 1 | 是否合格供货 |
| priority | INT | N | 999 | 供货优先级 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material_supplier (material_id, supplier_id, deleted)` 唯一；`idx_supplier (supplier_id)`；`idx_contract_end (contract_end)`。

### 04.14 表：`mdm_surgery_kit`（手术套包主表）

手术套包将某术式常用耗材组合成模板，供 M09 手术申请一键带出，减少漏费与漏备货。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| kit_code | VARCHAR(32) | N | - | 套包编码（KIT+流水） |
| kit_name | VARCHAR(200) | N | - | 套包名称 |
| kit_short_name | VARCHAR(64) | Y | NULL | 套包简称 |
| pinyin_code | VARCHAR(64) | Y | NULL | 拼音码 |
| pinyin_short | VARCHAR(32) | Y | NULL | 拼音首字母 |
| operation_id | BIGINT UNSIGNED | Y | NULL | 关联手术项目 ID |
| operation_code | VARCHAR(32) | Y | NULL | 手术项目编码 |
| ophthalmic_category | VARCHAR(64) | Y | NULL | 眼科专科分类 |
| kit_type | VARCHAR(32) | N | 'STANDARD' | 套包类型：STANDARD/OPTIONAL/EMERGENCY |
| is_implant_kit | TINYINT(1) | N | 0 | 是否含植入物 |
| total_estimate_price | DECIMAL(14,4) | Y | NULL | 预估总价 |
| item_count | INT | N | 0 | 明细项数 |
| dept_id | BIGINT UNSIGNED | Y | NULL | 使用科室 |
| is_default | TINYINT(1) | N | 0 | 是否该术式默认套包 |
| sort_no | INT | N | 999 | 排序 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_kit_code (kit_code, deleted)` 唯一；`idx_operation (operation_id)`；`idx_name (kit_name)`；`idx_ophthalmic (ophthalmic_category)`。

### 04.15 表：`mdm_surgery_kit_detail`（手术套包明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| kit_id | BIGINT UNSIGNED | N | - | 套包 ID |
| kit_code | VARCHAR(32) | N | - | 套包编码 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| material_name | VARCHAR(200) | Y | NULL | 耗材名称（冗余） |
| spec | VARCHAR(200) | Y | NULL | 规格（冗余） |
| default_qty | DECIMAL(12,4) | N | 1 | 默认数量 |
| unit | VARCHAR(32) | Y | NULL | 单位 |
| is_optional | TINYINT(1) | N | 0 | 是否可选（术中按需） |
| is_implant | TINYINT(1) | N | 0 | 是否植入物 |
| estimate_price | DECIMAL(14,4) | Y | NULL | 预估单价 |
| group_name | VARCHAR(64) | Y | NULL | 分组（如"晶体组""灌注组"） |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_kit_material (kit_id, material_id, deleted)` 唯一；`idx_material (material_id)`。

### 04.16 表：`mdm_material_registration`（注册证 / 资质证照表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| cert_type | VARCHAR(32) | N | 'REGISTRATION' | 证照类型：REGISTRATION/PRODUCTION_LICENSE/BUSINESS_LICENSE/IMPORT_CUSTOMS/QUALITY_AGREEMENT |
| cert_no | VARCHAR(128) | N | - | 证照编号 |
| cert_name | VARCHAR(200) | Y | NULL | 证照名称 |
| issuing_authority | VARCHAR(200) | Y | NULL | 发证机关 |
| holder_name | VARCHAR(200) | Y | NULL | 持证单位 |
| issue_date | DATE | Y | NULL | 发证日期 |
| expire_date | DATE | Y | NULL | 有效期至 |
| is_long_term | TINYINT(1) | N | 0 | 是否长期有效 |
| device_class | VARCHAR(8) | Y | NULL | 器械管理类别 |
| product_scope | VARCHAR(1000) | Y | NULL | 产品范围 |
| attachment_url | VARCHAR(500) | Y | NULL | 扫描件 URL |
| cert_status | VARCHAR(16) | N | 'VALID' | 状态：VALID/EXPIRING/EXPIRED/CANCELLED |
| warn_days | INT | N | 90 | 预警提前天数 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_material_cert (material_id, cert_type, cert_no, deleted)` 唯一；`idx_expire (expire_date, cert_status)`；`idx_cert_no (cert_no)`。

### 04.17 表：`mdm_material_change_log`（变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | Y | NULL | 耗材 ID |
| material_code | VARCHAR(32) | Y | NULL | 耗材编码 |
| change_type | VARCHAR(32) | N | - | 变更类型：CREATE/UPDATE/DELETE/ENABLE/DISABLE/RECALL/PRICE_CHANGE/IMPORT/SYNC |
| change_field | VARCHAR(128) | Y | NULL | 变更字段 |
| before_value | TEXT | Y | NULL | 变更前值 |
| after_value | TEXT | Y | NULL | 变更后值 |
| change_summary | VARCHAR(1000) | Y | NULL | 变更摘要 |
| before_snapshot | JSON | Y | NULL | 变更前完整快照 |
| after_snapshot | JSON | Y | NULL | 变更后完整快照 |
| change_reason | VARCHAR(500) | Y | NULL | 变更原因 |
| approval_id | BIGINT UNSIGNED | Y | NULL | 关联审批记录 ID |
| operator_id | BIGINT UNSIGNED | N | - | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| user_agent | VARCHAR(500) | Y | NULL | 客户端 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 操作时间 |

**索引：** `idx_material (material_id, created_at)`；`idx_code (material_code)`；`idx_operator (operator_id, created_at)`；`idx_type (change_type)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 10 年。

### 04.18 表：`mdm_material_approval`（审批记录表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| request_no | VARCHAR(32) | N | - | 审批单号（AP+年月日+流水） |
| material_id | BIGINT UNSIGNED | Y | NULL | 耗材 ID |
| material_code | VARCHAR(32) | Y | NULL | 耗材编码 |
| apply_type | VARCHAR(32) | N | - | 申请类型：CREATE/UPDATE/DISABLE/DELETE/PRICE_ADJUST/RECALL |
| apply_data | JSON | Y | NULL | 申请数据快照 |
| apply_reason | VARCHAR(500) | Y | NULL | 申请原因 |
| apply_by | BIGINT UNSIGNED | N | - | 申请人 |
| apply_at | DATETIME | N | CURRENT_TIMESTAMP | 申请时间 |
| approve_status | VARCHAR(16) | N | 'PENDING' | 审批状态：PENDING/APPROVED/REJECTED/CANCELLED |
| current_node | VARCHAR(64) | Y | NULL | 当前审批节点 |
| current_approver_id | BIGINT UNSIGNED | Y | NULL | 当前审批人 |
| approve_chain | VARCHAR(500) | Y | NULL | 审批链（JSON） |
| approve_by | BIGINT UNSIGNED | Y | NULL | 最终审批人 |
| approve_at | DATETIME | Y | NULL | 审批时间 |
| approve_opinion | VARCHAR(500) | Y | NULL | 审批意见 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_request_no (request_no)` 唯一；`idx_material (material_id)`；`idx_status (approve_status)`；`idx_approver (current_approver_id)`；`idx_apply_by (apply_by)`。

### 04.19 表：`mdm_material_sync_log`（同步日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| material_id | BIGINT UNSIGNED | Y | NULL | 耗材 ID |
| material_code | VARCHAR(32) | Y | NULL | 耗材编码 |
| sync_type | VARCHAR(32) | N | - | 同步类型：FULL/INCREMENTAL/MANUAL/SINGLE |
| target_system | VARCHAR(32) | N | - | 目标系统：M09/M15/M16/M17/M20/M22 |
| sync_batch_no | VARCHAR(64) | Y | NULL | 同步批次号 |
| sync_status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/SUCCESS/FAILED/PARTIAL |
| sync_count | INT | N | 0 | 同步记录数 |
| success_count | INT | N | 0 | 成功数 |
| fail_count | INT | N | 0 | 失败数 |
| request_data | JSON | Y | NULL | 请求数据 |
| response_data | JSON | Y | NULL | 响应数据 |
| error_message | VARCHAR(1000) | Y | NULL | 错误信息 |
| retry_count | INT | N | 0 | 重试次数 |
| cost_ms | INT | Y | NULL | 耗时（毫秒） |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| started_at | DATETIME | Y | NULL | 开始时间 |
| finished_at | DATETIME | Y | NULL | 结束时间 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_material (material_id)`；`idx_batch (sync_batch_no)`；`idx_status (sync_status, created_at)`；`idx_target (target_system, sync_status)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 1 年。

### 04.20 表：`mdm_material_code_seq`（编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| seq_type | VARCHAR(32) | N | - | 序列类型：MATERIAL/IOL/IMPLANT/KIT |
| category_code | VARCHAR(16) | N | '' | 分类码 |
| prefix | VARCHAR(16) | N | - | 前缀 |
| period_key | VARCHAR(16) | N | '' | 周期键（yyyyMM/yyyyMMdd/空） |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 5 | 序号位数 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_seq (seq_type, category_code, period_key)` 唯一。

### 04.21 表：`mdm_material_import_task`（导入任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| batch_no | VARCHAR(64) | N | - | 批次号 |
| import_type | VARCHAR(32) | N | - | 导入类型：MATERIAL/IOL/PRICE/SUPPLIER_REL/KIT |
| file_name | VARCHAR(255) | N | - | 文件名 |
| file_url | VARCHAR(500) | Y | NULL | 文件 URL |
| total_rows | INT | N | 0 | 总行数 |
| success_rows | INT | N | 0 | 成功行数 |
| fail_rows | INT | N | 0 | 失败行数 |
| warn_rows | INT | N | 0 | 警告行数 |
| import_mode | VARCHAR(16) | N | 'UPSERT' | 模式：INSERT/UPDATE/UPSERT |
| task_status | VARCHAR(16) | N | 'PENDING' | 状态：PENDING/VALIDATING/VALIDATED/IMPORTING/SUCCESS/FAILED/CANCELLED |
| error_file_url | VARCHAR(500) | Y | NULL | 错误报告 URL |
| error_summary | JSON | Y | NULL | 错误摘要 |
| dry_run | TINYINT(1) | N | 0 | 是否试运行 |
| started_at | DATETIME | Y | NULL | 开始时间 |
| finished_at | DATETIME | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时（毫秒） |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_batch_no (batch_no)` 唯一；`idx_status (task_status)`；`idx_operator (operator_id)`。

### 04.22 表：`mdm_material_recall`（耗材召回表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| recall_no | VARCHAR(32) | N | - | 召回单号 |
| recall_type | VARCHAR(32) | N | - | 召回类型：QUALITY/DEFECT/REGISTRATION_EXPIRE/SUPPLIER/OTHER |
| recall_level | VARCHAR(16) | N | - | 召回级别：I/II/III |
| material_id | BIGINT UNSIGNED | Y | NULL | 耗材 ID |
| material_code | VARCHAR(32) | Y | NULL | 耗材编码 |
| material_name | VARCHAR(200) | Y | NULL | 耗材名称 |
| batch_no | VARCHAR(64) | Y | NULL | 涉及批号（逗号分隔） |
| serial_nos | VARCHAR(1000) | Y | NULL | 涉及序列号（逗号分隔） |
| udi_di | VARCHAR(128) | Y | NULL | 涉及 UDI-DI |
| recall_reason | VARCHAR(1000) | N | - | 召回原因 |
| source | VARCHAR(128) | Y | NULL | 来源（药监局/厂商/院内） |
| affected_patient_count | INT | N | 0 | 影响患者数 |
| affected_qty | DECIMAL(14,4) | Y | NULL | 影响数量 |
| recall_status | VARCHAR(16) | N | 'DRAFT' | 状态：DRAFT/IN_PROGRESS/COMPLETED/CANCELLED |
| handle_measure | VARCHAR(1000) | Y | NULL | 处理措施 |
| start_date | DATE | Y | NULL | 召回开始日期 |
| complete_date | DATE | Y | NULL | 完成日期 |
| approval_id | BIGINT UNSIGNED | Y | NULL | 审批记录 ID |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_recall_no (recall_no, deleted)` 唯一；`idx_material (material_id)`；`idx_status (recall_status)`。

### 04.23 表：`mdm_material_recall_detail`（召回影响明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| recall_id | BIGINT UNSIGNED | N | - | 召回单 ID |
| recall_no | VARCHAR(32) | N | - | 召回单号 |
| source_system | VARCHAR(32) | N | - | 来源系统：M15/M09/M16 |
| source_bill_no | VARCHAR(64) | Y | NULL | 来源单据号 |
| patient_id | BIGINT UNSIGNED | Y | NULL | 患者 ID |
| patient_name | VARCHAR(64) | Y | NULL | 患者姓名 |
| patient_no | VARCHAR(32) | Y | NULL | 患者卡号 |
| dept_id | BIGINT UNSIGNED | Y | NULL | 使用科室 |
| batch_no | VARCHAR(64) | Y | NULL | 批号 |
| serial_no | VARCHAR(128) | Y | NULL | 序列号 |
| use_date | DATE | Y | NULL | 使用日期 |
| qty | DECIMAL(12,4) | Y | NULL | 数量 |
| handle_status | VARCHAR(16) | N | 'PENDING' | 处理状态：PENDING/NOTIFIED/HANDLED/CLOSED |
| handle_result | VARCHAR(500) | Y | NULL | 处理结果 |
| notified_at | DATETIME | Y | NULL | 通知时间 |
| handled_at | DATETIME | Y | NULL | 处理时间 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_recall (recall_id)`；`idx_patient (patient_id)`；`idx_handle (handle_status)`。

### 04.24 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/material.py
"""耗材主数据 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, DECIMAL,
    JSON, Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class Material(Base, TimestampMixin, SoftDeleteMixin):
    """耗材主表"""
    __tablename__ = "mdm_material"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ---------- 标识 ----------
    material_code: Mapped[str] = mapped_column(String(32), nullable=False, comment="耗材编码")
    material_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="耗材名称")
    material_short_name: Mapped[Optional[str]] = mapped_column(String(64))
    material_english_name: Mapped[Optional[str]] = mapped_column(String(255))
    spec: Mapped[str] = mapped_column(String(200), nullable=False, comment="规格")
    model: Mapped[Optional[str]] = mapped_column(String(128), comment="型号")

    # ---------- 检索 ----------
    pinyin_code: Mapped[str] = mapped_column(String(64), nullable=False)
    pinyin_short: Mapped[str] = mapped_column(String(32), nullable=False)
    wubi_code: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- 分类 ----------
    material_category: Mapped[str] = mapped_column(String(32), nullable=False)
    finance_category: Mapped[Optional[str]] = mapped_column(String(32))
    management_level: Mapped[str] = mapped_column(String(32), default="NORMAL", nullable=False)
    clinical_usage: Mapped[Optional[str]] = mapped_column(String(512))
    ophthalmic_category: Mapped[Optional[str]] = mapped_column(String(64))
    insurance_category: Mapped[str] = mapped_column(String(16), default="NA", nullable=False)

    # ---------- 厂商 ----------
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    manufacturer_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    manufacturer_name: Mapped[Optional[str]] = mapped_column(String(200))
    origin_place: Mapped[Optional[str]] = mapped_column(String(32))
    origin_country: Mapped[Optional[str]] = mapped_column(String(64))
    agent_supplier_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # ---------- 单位与包装 ----------
    min_unit: Mapped[str] = mapped_column(String(32), nullable=False)
    pack_unit: Mapped[Optional[str]] = mapped_column(String(32))
    pack_factor: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=1, nullable=False)
    charge_unit: Mapped[Optional[str]] = mapped_column(String(32))
    charge_factor: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=1, nullable=False)
    weight: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    volume: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))

    # ---------- 物理属性 ----------
    material_texture: Mapped[Optional[str]] = mapped_column(String(64))
    is_sterile: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    sterile_method: Mapped[Optional[str]] = mapped_column(String(32))
    is_single_use: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    reuse_times: Mapped[Optional[int]] = mapped_column(Integer)

    # ---------- 管理标识 ----------
    is_implant: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_high_value: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_chargeable: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_batch_managed: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_expiry_managed: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_serial_managed: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_udi_managed: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_cold_chain: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_high_risk: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_centralized: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    centralized_batch: Mapped[Optional[str]] = mapped_column(String(64))
    is_consignment: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_borrowable: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 合规 ----------
    registration_no: Mapped[Optional[str]] = mapped_column(String(128))
    registration_expire_date: Mapped[Optional[date]] = mapped_column(Date)
    registration_class: Mapped[Optional[str]] = mapped_column(String(8))
    national_material_code: Mapped[Optional[str]] = mapped_column(String(64))
    commercial_insurance_code: Mapped[Optional[str]] = mapped_column(String(64))
    his_external_code: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- 默认归属 ----------
    default_warehouse_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    default_dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # ---------- 存储 ----------
    storage_condition: Mapped[Optional[str]] = mapped_column(String(32))
    storage_temp_min: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    storage_temp_max: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    storage_humidity_max: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    is_light_protected: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_moisture_protected: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    shelf_life_months: Mapped[Optional[int]] = mapped_column(Integer)
    after_open_shelf_life: Mapped[Optional[int]] = mapped_column(Integer)
    after_open_unit: Mapped[Optional[str]] = mapped_column(String(8))

    # ---------- 附件 ----------
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    instruction_url: Mapped[Optional[str]] = mapped_column(String(500))

    # ---------- 核算 ----------
    account_subject: Mapped[Optional[str]] = mapped_column(String(64))
    cost_method: Mapped[Optional[str]] = mapped_column(String(32))
    dept_accounting: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    # ---------- 状态 ----------
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    ext_json: Mapped[Optional[dict]] = mapped_column(JSON)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    # ---------- 关系 ----------
    ext: Mapped[Optional["MaterialExt"]] = relationship(
        back_populates="material", uselist=False, lazy="selectin"
    )
    aliases: Mapped[List["MaterialAlias"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    barcodes: Mapped[List["MaterialBarcode"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    prices: Mapped[List["MaterialPrice"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    stock_policies: Mapped[List["MaterialStockPolicy"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    iol: Mapped[Optional["MaterialIol"]] = relationship(
        back_populates="material", uselist=False, lazy="selectin"
    )
    implant: Mapped[Optional["MaterialImplant"]] = relationship(
        back_populates="material", uselist=False, lazy="selectin"
    )
    reagent: Mapped[Optional["MaterialReagent"]] = relationship(
        back_populates="material", uselist=False, lazy="selectin"
    )
    consumable_attr: Mapped[Optional["MaterialConsumableAttr"]] = relationship(
        back_populates="material", uselist=False, lazy="selectin"
    )
    charge_rels: Mapped[List["MaterialChargeRel"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    supplier_rels: Mapped[List["MaterialSupplierRel"]] = relationship(
        back_populates="material", lazy="selectin"
    )
    registrations: Mapped[List["MaterialRegistration"]] = relationship(
        back_populates="material", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("material_code", "deleted", name="uk_material_code"),
        UniqueConstraint(
            "material_name", "spec", "manufacturer_id", "deleted",
            name="uk_name_spec_mfr",
        ),
        Index("idx_category", "material_category"),
        Index("idx_ophthalmic", "ophthalmic_category"),
        Index("idx_status", "status", "audit_status"),
        Index("idx_updated", "updated_at"),
        {"comment": "耗材主表"},
    )

    # ---------- 领域方法 ----------
    @property
    def is_implant_material(self) -> bool:
        return bool(self.is_implant)

    @property
    def requires_trace(self) -> bool:
        return bool(self.ext and self.ext.trace_required)

    def is_registration_expiring(self, warn_days: int = 90) -> bool:
        """注册证是否即将到期"""
        if not self.registration_expire_date:
            return False
        delta = (self.registration_expire_date - date.today()).days
        return 0 <= delta <= warn_days

    def is_registration_expired(self) -> bool:
        if not self.registration_expire_date:
            return False
        return self.registration_expire_date < date.today()

    def current_retail_price(self) -> Optional[Decimal]:
        for p in self.prices:
            if p.price_type == "RETAIL" and p.is_current:
                return p.price
        return None

    def to_snapshot(self) -> dict:
        """生成变更快照"""
        return {
            "material_code": self.material_code,
            "material_name": self.material_name,
            "spec": self.spec,
            "material_category": self.material_category,
            "management_level": self.management_level,
            "is_implant": self.is_implant,
            "is_high_value": self.is_high_value,
            "registration_no": self.registration_no,
            "status": self.status,
            "version": self.version,
        }
```

```python
# app/models/mdm/material_iol.py
"""人工晶体专档 ORM 模型"""
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Integer, SmallInteger, DECIMAL, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class MaterialIol(Base, TimestampMixin, SoftDeleteMixin):
    """人工晶体专档"""
    __tablename__ = "mdm_material_iol"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    material_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    material_code: Mapped[str] = mapped_column(String(32), nullable=False)
    udi_di: Mapped[Optional[str]] = mapped_column(String(128))

    brand: Mapped[str] = mapped_column(String(128), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    iol_type: Mapped[str] = mapped_column(String(32), nullable=False)
    optic_type: Mapped[Optional[str]] = mapped_column(String(32))

    sphere_power: Mapped[Decimal] = mapped_column(DECIMAL(6, 2), nullable=False)
    cylinder_power: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2))
    axis_range: Mapped[Optional[str]] = mapped_column(String(32))
    addition_power: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2))

    a_constant: Mapped[Decimal] = mapped_column(DECIMAL(6, 2), nullable=False)
    a_constant_type: Mapped[str] = mapped_column(String(16), default="SRK_T", nullable=False)
    surgeon_factor: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 3))

    optic_diameter: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    total_diameter: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    haptic_type: Mapped[Optional[str]] = mapped_column(String(32))
    haptic_angle: Mapped[Optional[str]] = mapped_column(String(32))
    lens_material: Mapped[Optional[str]] = mapped_column(String(64))
    refractive_index: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 3))

    is_preloaded: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    injector_type: Mapped[Optional[str]] = mapped_column(String(64))
    incision_size: Mapped[Optional[str]] = mapped_column(String(32))

    is_toric: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_multifocal: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_edof: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_blue_light_filter: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_uv_filter: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    aspheric_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 3))

    suitable_patient: Mapped[Optional[str]] = mapped_column(String(500))
    contraindication: Mapped[Optional[str]] = mapped_column(String(500))
    operation_ids: Mapped[Optional[str]] = mapped_column(String(500))
    need_navigation: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_intraoperative_aberrometry: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    power_range_min: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2))
    power_range_max: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 2))
    power_step: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), default=Decimal("0.50"))

    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)

    material: Mapped["Material"] = relationship(back_populates="iol")

    __table_args__ = (
        UniqueConstraint("material_id", "deleted", name="uk_iol_material"),
        UniqueConstraint(
            "brand", "model", "sphere_power", "cylinder_power", "deleted",
            name="uk_brand_model_power",
        ),
        Index("idx_iol_power", "sphere_power", "cylinder_power"),
        Index("idx_iol_type", "iol_type"),
        {"comment": "人工晶体专档"},
    )
```

### 04.25 Pydantic Schema 定义

```python
# app/schemas/mdm/material.py
"""耗材主数据 Pydantic Schema"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==================== 公共 ====================
class MaterialAliasSchema(BaseModel):
    id: Optional[int] = None
    alias_name: str = Field(..., max_length=200)
    alias_type: Literal["CLINICAL", "SUPPLIER", "HISTORICAL", "ABBREVIATION"] = "CLINICAL"
    sort_no: int = 999


class MaterialBarcodeSchema(BaseModel):
    id: Optional[int] = None
    barcode: str = Field(..., max_length=128)
    barcode_type: Literal["INTERNAL", "GS1", "HIBC", "UDI", "SUPPLIER"] = "INTERNAL"
    udi_di: Optional[str] = Field(None, max_length=128)
    udi_pi: Optional[str] = Field(None, max_length=128)
    gtin: Optional[str] = Field(None, max_length=64)
    is_primary: bool = False
    is_udi_carrier: bool = False
    pack_level: Literal["UNIT", "PACK", "CASE"] = "UNIT"
    pack_qty: Optional[Decimal] = None


class MaterialPriceSchema(BaseModel):
    id: Optional[int] = None
    price_type: Literal["PURCHASE", "RETAIL", "CENTRALIZED", "MEMBER", "CONTRACT"] = "RETAIL"
    price: Decimal = Field(..., ge=0, decimal_places=4)
    price_unit: str = Field(..., max_length=32)
    markup_rate: Optional[Decimal] = Field(None, ge=-100, le=1000)
    max_retail_price: Optional[Decimal] = Field(None, ge=0)
    min_retail_price: Optional[Decimal] = Field(None, ge=0)
    is_one_price_one_item: bool = False
    supplier_id: Optional[int] = None
    contract_no: Optional[str] = Field(None, max_length=64)
    effective_date: date
    expire_date: Optional[date] = None
    adjust_reason: Optional[str] = Field(None, max_length=255)


class MaterialStockPolicySchema(BaseModel):
    id: Optional[int] = None
    warehouse_id: Optional[int] = None
    warehouse_type: Optional[str] = None
    safety_stock: Optional[Decimal] = Field(None, ge=0)
    min_stock: Optional[Decimal] = Field(None, ge=0)
    max_stock: Optional[Decimal] = Field(None, ge=0)
    reorder_point: Optional[Decimal] = Field(None, ge=0)
    reorder_qty: Optional[Decimal] = Field(None, ge=0)
    is_zero_stock: bool = False
    is_secondary_stock: bool = False
    is_consignment: bool = False
    consignment_supplier_id: Optional[int] = None
    fifo_rule: Literal["FIFO", "FEFO", "LIFO"] = "FEFO"
    expiry_warning_days: int = Field(90, ge=0, le=3650)
    expiry_forbid_days: int = Field(0, ge=0, le=3650)
    batch_required: bool = True
    serial_required: bool = False
    udi_scan_required: bool = False
    allow_negative_stock: bool = False

    @model_validator(mode="after")
    def validate_stock_range(self):
        vals = [self.min_stock, self.safety_stock, self.max_stock]
        present = [v for v in vals if v is not None]
        if len(present) >= 2 and present != sorted(present):
            raise ValueError("库存阈值必须满足 最低库存 <= 安全库存 <= 最高库存")
        if (self.reorder_point is not None and self.max_stock is not None
                and self.reorder_point > self.max_stock):
            raise ValueError("再订货点不能大于最高库存")
        return self


class MaterialChargeRelSchema(BaseModel):
    id: Optional[int] = None
    charge_item_id: int
    charge_item_code: Optional[str] = None
    rel_type: Literal["PRIMARY", "SECONDARY", "BUNDLED"] = "PRIMARY"
    is_default: bool = False
    charge_qty_factor: Decimal = Field(Decimal("1"), gt=0)
    auto_charge: bool = True
    charge_scene: Optional[str] = None


class MaterialSupplierRelSchema(BaseModel):
    id: Optional[int] = None
    supplier_id: int
    is_primary: bool = False
    supplier_material_code: Optional[str] = Field(None, max_length=64)
    supplier_material_name: Optional[str] = Field(None, max_length=200)
    supply_type: Literal["NORMAL", "CONSIGNMENT", "FOLLOW_UP", "BORROW"] = "NORMAL"
    purchase_price: Optional[Decimal] = Field(None, ge=0)
    price_unit: Optional[str] = None
    min_order_qty: Optional[Decimal] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    contract_no: Optional[str] = Field(None, max_length=64)
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    is_qualified: bool = True
    priority: int = 999


class MaterialRegistrationSchema(BaseModel):
    id: Optional[int] = None
    cert_type: Literal[
        "REGISTRATION", "PRODUCTION_LICENSE", "BUSINESS_LICENSE",
        "IMPORT_CUSTOMS", "QUALITY_AGREEMENT",
    ] = "REGISTRATION"
    cert_no: str = Field(..., max_length=128)
    cert_name: Optional[str] = Field(None, max_length=200)
    issuing_authority: Optional[str] = Field(None, max_length=200)
    holder_name: Optional[str] = Field(None, max_length=200)
    issue_date: Optional[date] = None
    expire_date: Optional[date] = None
    is_long_term: bool = False
    device_class: Optional[str] = None
    product_scope: Optional[str] = Field(None, max_length=1000)
    attachment_url: Optional[str] = Field(None, max_length=500)
    warn_days: int = Field(90, ge=0, le=3650)


# ==================== 人工晶体 ====================
class MaterialIolSchema(BaseModel):
    id: Optional[int] = None
    udi_di: Optional[str] = Field(None, max_length=128)
    brand: str = Field(..., max_length=128)
    model: str = Field(..., max_length=128)
    product_name: str = Field(..., max_length=200)
    iol_type: Literal[
        "MONOFOCAL_SPHERICAL", "MONOFOCAL_ASPHERICAL", "BIFOCAL", "TRIFOCAL",
        "TORIC", "EDOF", "ICL", "PRL", "PHAKIC_IOL", "ADD_ON_IOL",
    ]
    optic_type: Optional[str] = None
    sphere_power: Decimal = Field(..., ge=-30, le=40, decimal_places=2)
    cylinder_power: Optional[Decimal] = Field(None, ge=-30, le=30, decimal_places=2)
    axis_range: Optional[str] = Field(None, max_length=32)
    addition_power: Optional[Decimal] = Field(None, ge=0, le=6, decimal_places=2)
    a_constant: Decimal = Field(..., ge=100, le=130, decimal_places=2)
    a_constant_type: Literal["SRK_T", "HOLLADAY", "HAIGIS"] = "SRK_T"
    surgeon_factor: Optional[Decimal] = Field(None, ge=-5, le=5, decimal_places=3)
    optic_diameter: Optional[Decimal] = Field(None, gt=0, le=10, decimal_places=2)
    total_diameter: Optional[Decimal] = Field(None, gt=0, le=20, decimal_places=2)
    haptic_type: Optional[str] = None
    haptic_angle: Optional[str] = None
    lens_material: Optional[str] = None
    refractive_index: Optional[Decimal] = Field(None, gt=0, le=2, decimal_places=3)
    is_preloaded: bool = False
    injector_type: Optional[str] = None
    incision_size: Optional[str] = None
    is_toric: bool = False
    is_multifocal: bool = False
    is_edof: bool = False
    is_blue_light_filter: bool = False
    is_uv_filter: bool = True
    aspheric_value: Optional[Decimal] = None
    suitable_patient: Optional[str] = Field(None, max_length=500)
    contraindication: Optional[str] = Field(None, max_length=500)
    operation_ids: Optional[List[int]] = None
    need_navigation: bool = False
    need_intraoperative_aberrometry: bool = False
    power_range_min: Optional[Decimal] = None
    power_range_max: Optional[Decimal] = None
    power_step: Decimal = Field(Decimal("0.50"), gt=0, le=5)

    @model_validator(mode="after")
    def validate_iol(self):
        # Toric 晶体必须提供柱镜
        if self.iol_type == "TORIC" and self.cylinder_power is None:
            raise ValueError("Toric 散光矫正型人工晶体必须填写柱镜度数")
        # 柱镜度数必须为 0.25 的整数倍
        if self.cylinder_power is not None:
            if (self.cylinder_power * 100) % 25 != 0:
                raise ValueError("柱镜度数必须为 0.25 的整数倍")
        # 球镜度数必须为 0.25 的整数倍（0.5 步进型号除外）
        if (self.sphere_power * 100) % 25 != 0:
            raise ValueError("球镜度数必须为 0.25 的整数倍")
        if self.is_toric and not self.cylinder_power:
            raise ValueError("散光矫正型晶体必须填写柱镜度数")
        if self.is_multifocal and not self.addition_power:
            raise ValueError("多焦/三焦晶体必须填写附加度数")
        return self


# ==================== 植入物 ====================
class MaterialImplantSchema(BaseModel):
    id: Optional[int] = None
    implant_category: Literal[
        "IOL", "GLAUCOMA_DEVICE", "VITREOUS_SUBSTITUTE", "ORBITAL_IMPLANT",
        "OCULAR_SURFACE_IMPLANT", "LACRIMAL_IMPLANT", "CORNEA_IMPLANT",
        "SUTURE_IMPLANT", "OTHER_IMPLANT",
    ]
    implant_site: Optional[str] = None
    is_permanent: bool = True
    expected_life_years: Optional[int] = Field(None, ge=0, le=100)
    trace_required: bool = True
    trace_direction: Literal["FORWARD", "BACKWARD", "BOTH"] = "BOTH"
    trace_fields: Optional[List[str]] = None
    patient_binding_required: bool = True
    binding_timing: Literal["PREOPERATIVE", "INTRAOPERATIVE", "POSTOPERATIVE"] = "INTRAOPERATIVE"
    require_implant_record: bool = True
    require_consent: bool = False
    require_followup: bool = True
    followup_days: Optional[str] = None
    mri_compatible: Optional[Literal["YES", "NO", "CONDITIONAL"]] = None
    mri_condition: Optional[str] = Field(None, max_length=255)
    adverse_event_report: bool = True
    recall_level: Optional[Literal["I", "II", "III"]] = None
    registration_no: Optional[str] = Field(None, max_length=128)
    registration_expire_date: Optional[date] = None


# ==================== 试剂 ====================
class MaterialReagentSchema(BaseModel):
    id: Optional[int] = None
    reagent_type: Literal["REAGENT", "CALIBRATOR", "CONTROL", "CONSUMABLE"]
    test_count_per_pack: Optional[int] = Field(None, ge=0)
    lab_item_ids: Optional[List[int]] = None
    lab_combo_ids: Optional[List[int]] = None
    analyzer_model: Optional[str] = Field(None, max_length=128)
    is_open_vial_managed: bool = True
    open_vial_shelf_life: Optional[int] = Field(None, ge=0)
    open_vial_unit: Optional[Literal["HOUR", "DAY"]] = None
    storage_reagent_condition: Optional[str] = None
    is_calibration_required: bool = False
    calibration_interval_days: Optional[int] = Field(None, ge=0)


# ==================== 主 Schema ====================
class MaterialBase(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=200)
    material_short_name: Optional[str] = Field(None, max_length=64)
    material_english_name: Optional[str] = Field(None, max_length=255)
    spec: str = Field(..., min_length=1, max_length=200)
    model: Optional[str] = Field(None, max_length=128)
    material_category: str
    finance_category: Optional[str] = None
    management_level: str = "NORMAL"
    clinical_usage: Optional[List[str]] = None
    ophthalmic_category: Optional[str] = None
    insurance_category: str = "NA"
    brand: Optional[str] = Field(None, max_length=128)
    manufacturer_id: Optional[int] = None
    origin_place: Optional[Literal["IMPORTED", "DOMESTIC", "JOINT_VENTURE"]] = None
    origin_country: Optional[str] = Field(None, max_length=64)
    agent_supplier_id: Optional[int] = None
    min_unit: str = Field(..., max_length=32)
    pack_unit: Optional[str] = Field(None, max_length=32)
    pack_factor: Decimal = Field(Decimal("1"), gt=0)
    charge_unit: Optional[str] = Field(None, max_length=32)
    charge_factor: Decimal = Field(Decimal("1"), gt=0)
    weight: Optional[Decimal] = Field(None, ge=0)
    volume: Optional[Decimal] = Field(None, ge=0)
    material_texture: Optional[str] = Field(None, max_length=64)
    is_sterile: bool = False
    sterile_method: Optional[Literal["EO", "IRRADIATION", "STEAM", "PLASMA", "NONE"]] = None
    is_single_use: bool = True
    reuse_times: Optional[int] = Field(None, ge=0)
    is_implant: bool = False
    is_high_value: bool = False
    is_chargeable: bool = True
    is_batch_managed: bool = True
    is_expiry_managed: bool = True
    is_serial_managed: bool = False
    is_udi_managed: bool = False
    is_cold_chain: bool = False
    is_high_risk: bool = False
    is_centralized: bool = False
    centralized_batch: Optional[str] = Field(None, max_length=64)
    is_consignment: bool = False
    is_borrowable: bool = False
    registration_no: Optional[str] = Field(None, max_length=128)
    registration_expire_date: Optional[date] = None
    registration_class: Optional[Literal["I", "II", "III"]] = None
    national_material_code: Optional[str] = Field(None, max_length=64)
    default_warehouse_id: Optional[int] = None
    default_dept_id: Optional[int] = None
    storage_condition: Optional[Literal["NORMAL", "COOL", "COLD", "FREEZE"]] = None
    storage_temp_min: Optional[Decimal] = Field(None, ge=-100, le=100)
    storage_temp_max: Optional[Decimal] = Field(None, ge=-100, le=100)
    is_light_protected: bool = False
    is_moisture_protected: bool = False
    shelf_life_months: Optional[int] = Field(None, ge=0, le=1200)
    after_open_shelf_life: Optional[int] = Field(None, ge=0)
    after_open_unit: Optional[Literal["HOUR", "DAY"]] = None
    account_subject: Optional[str] = Field(None, max_length=64)
    cost_method: Optional[Literal["FIFO", "WEIGHTED", "SPECIFIC"]] = None
    dept_accounting: bool = True
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)


class MaterialCreate(MaterialBase):
    """新增耗材"""
    material_code: Optional[str] = Field(None, description="为空则自动生成")
    aliases: List[MaterialAliasSchema] = []
    barcodes: List[MaterialBarcodeSchema] = []
    prices: List[MaterialPriceSchema] = []
    stock_policies: List[MaterialStockPolicySchema] = []
    charge_rels: List[MaterialChargeRelSchema] = []
    supplier_rels: List[MaterialSupplierRelSchema] = []
    registrations: List[MaterialRegistrationSchema] = []
    iol: Optional[MaterialIolSchema] = None
    implant: Optional[MaterialImplantSchema] = None
    reagent: Optional[MaterialReagentSchema] = None
    ext: Optional[dict] = None
    change_reason: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_category_consistency(self):
        # 植入物分类必须提供植入物配置
        if self.is_implant and self.implant is None:
            raise ValueError("标记为植入物的耗材必须填写植入物追溯配置")
        if self.material_category == "IMPLANT" and not self.is_implant:
            raise ValueError("基础分类为植入物时，必须勾选「是否植入物」")
        if self.material_category == "REAGENT" and self.reagent is None:
            raise ValueError("基础分类为检验试剂时必须填写试剂配置")
        # 高值耗材必须填写注册证
        if (self.is_high_value or self.is_implant) and not self.registration_no:
            raise ValueError("高值耗材/植入物必须填写医疗器械注册证号")
        # UDI 管理必须提供 UDI-DI
        if self.is_udi_managed:
            has_udi = any(b.udi_di for b in self.barcodes)
            if not has_udi:
                raise ValueError("启用 UDI 管理时必须提供至少一个 UDI-DI")
        # 冷链必须提供温度范围
        if self.is_cold_chain and self.storage_temp_min is None:
            raise ValueError("冷链耗材必须填写存储温度范围")
        # 价格生效日期
        for p in self.prices:
            if p.expire_date and p.effective_date and p.expire_date <= p.effective_date:
                raise ValueError("价格失效日期必须晚于生效日期")
        # 主条码唯一
        if sum(1 for b in self.barcodes if b.is_primary) > 1:
            raise ValueError("同一耗材仅允许一个主条码")
        # 植入物/高值必须序列号或 UDI 管理
        if self.is_implant and not (self.is_serial_managed or self.is_udi_managed):
            raise ValueError("植入物必须启用序列号管理或 UDI 管理")
        return self


class MaterialUpdate(MaterialCreate):
    """更新耗材"""
    version: int = Field(..., ge=0, description="乐观锁版本号")


class MaterialQuery(BaseModel):
    """耗材查询条件"""
    keyword: Optional[str] = None
    material_category: Optional[List[str]] = None
    finance_category: Optional[str] = None
    management_level: Optional[List[str]] = None
    clinical_usage: Optional[List[str]] = None
    ophthalmic_category: Optional[str] = None
    brand: Optional[str] = None
    manufacturer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    is_implant: Optional[bool] = None
    is_high_value: Optional[bool] = None
    is_chargeable: Optional[bool] = None
    is_cold_chain: Optional[bool] = None
    is_centralized: Optional[bool] = None
    is_consignment: Optional[bool] = None
    registration_status: Optional[Literal["VALID", "EXPIRING", "EXPIRED"]] = None
    status: Optional[List[str]] = None
    audit_status: Optional[str] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    sort_by: str = "updated_at"
    sort_order: Literal["asc", "desc"] = "desc"


class MaterialListItem(BaseModel):
    """耗材列表项"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    material_code: str
    material_name: str
    material_short_name: Optional[str] = None
    spec: str
    model: Optional[str] = None
    brand: Optional[str] = None
    manufacturer_name: Optional[str] = None
    material_category: str
    material_category_name: Optional[str] = None
    management_level: str
    management_level_name: Optional[str] = None
    ophthalmic_category: Optional[str] = None
    min_unit: str
    pack_unit: Optional[str] = None
    is_implant: bool
    is_high_value: bool
    is_chargeable: bool
    is_centralized: bool
    retail_price: Optional[Decimal] = None
    purchase_price: Optional[Decimal] = None
    registration_no: Optional[str] = None
    registration_expire_date: Optional[date] = None
    registration_status: Optional[str] = None
    status: str
    audit_status: str
    updated_at: Optional[datetime] = None


class MaterialDetail(MaterialListItem):
    """耗材详情"""
    material_english_name: Optional[str] = None
    finance_category: Optional[str] = None
    clinical_usage: Optional[List[str]] = None
    insurance_category: str = "NA"
    origin_place: Optional[str] = None
    origin_country: Optional[str] = None
    agent_supplier_id: Optional[int] = None
    charge_unit: Optional[str] = None
    charge_factor: Decimal = Decimal("1")
    pack_factor: Decimal = Decimal("1")
    weight: Optional[Decimal] = None
    volume: Optional[Decimal] = None
    material_texture: Optional[str] = None
    is_sterile: bool = False
    sterile_method: Optional[str] = None
    is_single_use: bool = True
    reuse_times: Optional[int] = None
    is_batch_managed: bool = True
    is_expiry_managed: bool = True
    is_serial_managed: bool = False
    is_udi_managed: bool = False
    is_cold_chain: bool = False
    is_high_risk: bool = False
    is_consignment: bool = False
    is_borrowable: bool = False
    centralized_batch: Optional[str] = None
    registration_class: Optional[str] = None
    national_material_code: Optional[str] = None
    default_warehouse_id: Optional[int] = None
    default_warehouse_name: Optional[str] = None
    default_dept_id: Optional[int] = None
    default_dept_name: Optional[str] = None
    storage_condition: Optional[str] = None
    storage_temp_min: Optional[Decimal] = None
    storage_temp_max: Optional[Decimal] = None
    is_light_protected: bool = False
    is_moisture_protected: bool = False
    shelf_life_months: Optional[int] = None
    after_open_shelf_life: Optional[int] = None
    after_open_unit: Optional[str] = None
    image_url: Optional[str] = None
    instruction_url: Optional[str] = None
    account_subject: Optional[str] = None
    cost_method: Optional[str] = None
    dept_accounting: bool = True
    version: int = 0
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # 子表
    aliases: List[MaterialAliasSchema] = []
    barcodes: List[MaterialBarcodeSchema] = []
    prices: List[MaterialPriceSchema] = []
    stock_policies: List[MaterialStockPolicySchema] = []
    charge_rels: List[MaterialChargeRelSchema] = []
    supplier_rels: List[MaterialSupplierRelSchema] = []
    registrations: List[MaterialRegistrationSchema] = []
    iol: Optional[MaterialIolSchema] = None
    implant: Optional[MaterialImplantSchema] = None
    reagent: Optional[MaterialReagentSchema] = None
    ext: Optional[dict] = None
```

---

---

## 05. 权限数据结构

> **来源：** [权限详细设计](M01_主数据管理MDM_05_权限_详细设计.md) · 第 4 章
> **主数据域：** 权限域（`AUTH`） · **表数：** 26

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 05.2 | `mdm_menu` | 菜单与功能点 |
| 05.3 | `mdm_role` | 角色 |
| 05.4 | `mdm_role_permission` | 角色权限 |
| 05.5 | `mdm_role_inherit` | 角色继承 |
| 05.6 | `mdm_role_api` | 角色接口白名单 |
| 05.7 | `mdm_role_conflict_rule` | 角色冲突规则 |
| 05.8 | `mdm_data_scope` | 数据权限范围 |
| 05.9 | `mdm_role_data_scope` | 角色数据权限 |
| 05.10 | `mdm_field_def` | 字段定义 / 敏感字段字典 |
| 05.11 | `mdm_role_field_perm` | 角色字段权限 |
| 05.12 | `mdm_second_factor_policy` | 二次验证策略 |
| 05.13 | `mdm_position` | 岗位 |
| 05.14 | `mdm_position_role` | 岗位默认角色 |
| 05.15 | `mdm_user_group` | 用户组 |
| 05.16 | `mdm_user_group_member` | 用户组成员 |
| 05.17 | `mdm_user_group_role` | 用户组角色 |
| 05.18 | `mdm_role_user` | 角色用户绑定 |
| 05.19 | `mdm_user_permission` | 用户直接权限 |
| 05.20 | `mdm_permission_template` | 权限模板 |
| 05.21 | `mdm_permission_template_item` | 权限模板明细 |
| 05.22 | `mdm_permission_apply` | 权限申请单 |
| 05.23 | `mdm_permission_apply_detail` | 权限申请明细 |
| 05.24 | `mdm_permission_change_log` | 权限变更日志 |
| 05.25 | `mdm_permission_version` | 权限版本快照 |
| 05.26 | `mdm_permission_sync_log` | 权限同步日志 |
| 05.27 | `mdm_permission_cache_task` | 权限缓存刷新任务 |

---

### 05.1 ER 关系图

```
                    ┌───────────────────────┐
                    │  mdm_menu             │
                    │  （菜单与功能点）      │
                    └───────────┬───────────┘
                                │ 1:N（自关联 parent_id）
                                │
                                │ N:M
                                ▼
┌───────────────┐        ┌─────────────────────┐        ┌──────────────────┐
│  mdm_role     │ 1    N │ mdm_role_permission │ N    1 │  mdm_menu        │
│  （角色）      │◄──────►│ （角色权限）         │◄──────►│                  │
└───────┬───────┘        └─────────────────────┘        └──────────────────┘
        │
        ├── 1:1 ──► mdm_role_inherit        （角色继承）
        ├── 1:N ──► mdm_role_data_scope     （角色数据权限）
        ├── 1:N ──► mdm_role_field_perm     （角色字段权限）
        ├── 1:N ──► mdm_second_factor_policy（二次验证策略，按角色适用范围）
        ├── 1:N ──► mdm_role_api            （角色接口白名单）
        └── 1:N ──► mdm_role_user           （角色用户绑定）
                          │
                          │ N:1
                          ▼
                    ┌───────────────┐
                    │  mdm_staff    │（M01 职工）
                    └───────────────┘

┌───────────────┐        ┌─────────────────────┐
│ mdm_position  │ 1    N │  mdm_position_role  │  N   1  ┌───────────────┐
│ （岗位）       │◄──────►│ （岗位默认角色）     │◄───────►│  mdm_role     │
└───────────────┘        └─────────────────────┘         └───────────────┘

┌───────────────┐        ┌──────────────────────────┐
│mdm_user_group │ 1    N │ mdm_user_group_member    │  N   1  ┌────────────┐
│（用户组）      │◄──────►│ （组成员）                │◄───────►│ mdm_staff  │
└───────┬───────┘        └──────────────────────────┘         └────────────┘
        │ N:M
        ▼
┌───────────────┐
│  mdm_role     │
└───────────────┘

┌───────────────────┐      ┌──────────────────────────┐
│ mdm_data_scope    │ 1  N │ mdm_role_data_scope      │
│ （数据权限范围）   │◄────►│ （角色-数据域-范围）      │
└───────────────────┘      └──────────────────────────┘

┌───────────────────┐      ┌──────────────────────────┐
│ mdm_field_def     │ 1  N │ mdm_role_field_perm      │
│ （字段定义）       │◄────►│ （角色字段权限）          │
└───────────────────┘      └──────────────────────────┘

┌───────────────────────┐  ┌──────────────────────────────┐
│mdm_second_factor_     │  │ mdm_permission_template      │
│policy（二次验证策略）  │  │ （权限模板）                  │
└───────────────────────┘  └───────────┬──────────────────┘
                                       │ 1:N
                                       ▼
                           ┌──────────────────────────┐
                           │ mdm_permission_template_ │
                           │ item（模板明细）          │
                           └──────────────────────────┘

治理相关：
┌────────────────────────┐  ┌────────────────────────┐
│ mdm_permission_apply   │  │ mdm_permission_change_ │
│ （权限申请单）          │  │ log（权限变更日志）     │
└───────────┬────────────┘  └────────────────────────┘
            │ 1:N
            ▼
┌────────────────────────┐  ┌────────────────────────┐
│ mdm_permission_apply_  │  │ mdm_permission_version │
│ detail（申请明细）      │  │ （权限版本快照）        │
└────────────────────────┘  └────────────────────────┘

┌────────────────────────┐  ┌────────────────────────────┐
│ mdm_role_conflict_rule │  │ mdm_permission_sync_log    │
│ （角色冲突规则）        │  │ （权限同步日志）            │
└────────────────────────┘  └────────────────────────────┘

┌────────────────────────────┐  ┌────────────────────────────┐
│ mdm_permission_cache_task  │  │ mdm_field_def              │
│ （权限缓存刷新任务）        │  │ （字段定义/敏感字段字典）   │
└────────────────────────────┘  └────────────────────────────┘
```

**表清单（共 22 张）：**

| 序号 | 表名 | 中文名 | 说明 | 预估量级 |
|---|---|---|---|---|
| 1 | `mdm_menu` | 菜单与功能点 | 三级树 | 1,200 |
| 2 | `mdm_role` | 角色 | 权限集合 | 80 |
| 3 | `mdm_role_permission` | 角色权限 | 角色-菜单关系 | 30,000 |
| 4 | `mdm_role_inherit` | 角色继承 | 角色父子关系 | 50 |
| 5 | `mdm_role_api` | 角色接口白名单 | 特殊接口授权 | 2,000 |
| 6 | `mdm_role_conflict_rule` | 角色冲突规则 | 职责分离 | 30 |
| 7 | `mdm_data_scope` | 数据权限范围 | 范围定义 | 50 |
| 8 | `mdm_role_data_scope` | 角色数据权限 | 角色×数据域×范围 | 500 |
| 9 | `mdm_field_def` | 字段定义 | 敏感字段字典 | 200 |
| 10 | `mdm_role_field_perm` | 角色字段权限 | 角色×字段×动作 | 3,000 |
| 11 | `mdm_second_factor_policy` | 二次验证策略 | 触发规则 | 50 |
| 12 | `mdm_position` | 岗位 | 岗位定义 | 60 |
| 13 | `mdm_position_role` | 岗位默认角色 | 岗位-角色 | 150 |
| 14 | `mdm_user_group` | 用户组 | 分组 | 60 |
| 15 | `mdm_user_group_member` | 用户组成员 | 组成员 | 1,500 |
| 16 | `mdm_user_group_role` | 用户组角色 | 组-角色 | 200 |
| 17 | `mdm_role_user` | 角色用户绑定 | 用户×角色 | 2,000 |
| 18 | `mdm_user_permission` | 用户直接权限 | 直接授权/拒绝 | 500 |
| 19 | `mdm_permission_template` | 权限模板 | 权限包 | 40 |
| 20 | `mdm_permission_template_item` | 权限模板明细 | 模板内容 | 2,000 |
| 21 | `mdm_permission_apply` | 权限申请单 | 申请流程 | 1,000/年 |
| 22 | `mdm_permission_apply_detail` | 权限申请明细 | 申请内容 | 8,000/年 |
| 23 | `mdm_permission_change_log` | 权限变更日志 | 审计留痕 | 30,000/年 |
| 24 | `mdm_permission_version` | 权限版本快照 | 版本管理 | 20,000/年 |
| 25 | `mdm_permission_sync_log` | 权限同步日志 | 分发记录 | 100,000/年 |
| 26 | `mdm_permission_cache_task` | 缓存刷新任务 | 异步刷新 | 5,000/年 |

> 说明：共 26 张表。`mdm_role`、`mdm_menu`、`mdm_role_permission`、`mdm_data_scope`、`mdm_user_group`、`mdm_user_group_member` 在 M01 总文档第 7.9 节已定义基础结构，本子模块在其基础上**扩展字段**并新增其余表，保持向后兼容。

### 05.2 表：`mdm_menu`（菜单与功能点）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(128) | N | - | 菜单/功能点编码，全局唯一 |
| perm_code | VARCHAR(128) | Y | NULL | 权限码 `{模块}:{资源}:{动作}` |
| name | VARCHAR(64) | N | - | 菜单名称 |
| name_en | VARCHAR(64) | Y | NULL | 英文名 |
| module_code | VARCHAR(8) | N | - | 模块编号 M01~M23 |
| parent_id | BIGINT UNSIGNED | Y | NULL | 上级菜单 ID |
| parent_path | VARCHAR(500) | Y | NULL | 层级路径 `/1/5/12/` |
| level_no | TINYINT | N | 1 | 层级 1/2/3 |
| menu_type | VARCHAR(16) | N | - | MODULE/MENU/BUTTON |
| route_path | VARCHAR(255) | Y | NULL | 前端路由 |
| component | VARCHAR(255) | Y | NULL | 前端组件路径 |
| api_pattern | VARCHAR(500) | Y | NULL | 接口匹配正则 |
| http_method | VARCHAR(16) | Y | NULL | GET/POST/PUT/DELETE/PATCH/* |
| icon | VARCHAR(64) | Y | NULL | 图标 |
| sort_no | INT | N | 999 | 排序 |
| visible | TINYINT(1) | N | 1 | 导航中是否显示 |
| cacheable | TINYINT(1) | N | 0 | 是否 keep-alive |
| mobile_visible | TINYINT(1) | N | 1 | 移动端是否显示 |
| is_public | TINYINT(1) | N | 0 | 是否免权限 |
| is_system | TINYINT(1) | N | 0 | 是否系统内置（不可删） |
| badge_rule | VARCHAR(128) | Y | NULL | 角标规则 |
| description | VARCHAR(255) | Y | NULL | 说明 |
| status | TINYINT | N | 1 | 状态 1启用 0停用 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_menu | PRIMARY | id | 主键 |
| uk_menu_code | UNIQUE | code, is_deleted | 编码唯一 |
| uk_perm_code | UNIQUE | perm_code, is_deleted | 权限码唯一 |
| idx_module | NORMAL | module_code | 模块过滤 |
| idx_parent | NORMAL | parent_id | 树查询 |
| idx_path | NORMAL | parent_path | 查下级 |
| idx_type | NORMAL | menu_type | 类型过滤 |
| idx_status | NORMAL | status, is_deleted | 状态过滤 |

**约束：**
- `menu_type=BUTTON` 时必须有 `perm_code`。
- `menu_type=MENU` 时必须有 `route_path`。
- `parent_id` 不能指向自己或自己的子孙（循环校验）。

### 05.3 表：`mdm_role`（角色）— 扩展

在 M01 总文档基础上扩展：

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 角色编码 R+流水 |
| name | VARCHAR(64) | N | - | 角色名称 |
| name_en | VARCHAR(64) | Y | NULL | 英文名 |
| role_category | VARCHAR(32) | N | 'BUSINESS' | SYSTEM/POSITION/DEPT/BUSINESS/CUSTOM |
| role_level | VARCHAR(16) | N | 'NORMAL' | SUPER/HIGH/NORMAL/LOW（用于审批链与互斥判断） |
| parent_role_id | BIGINT UNSIGNED | Y | NULL | 父角色（继承） |
| apply_dept_type | VARCHAR(255) | Y | NULL | 适用科室类型（逗号分隔） |
| apply_dept_ids | VARCHAR(1000) | Y | NULL | 适用科室 ID |
| default_data_scope_id | BIGINT UNSIGNED | Y | NULL | 默认数据范围 |
| max_user_count | INT | Y | NULL | 最大绑定用户数（NULL 不限） |
| is_builtin | TINYINT(1) | N | 0 | 是否内置（不可删） |
| is_assignable | TINYINT(1) | N | 1 | 是否允许分配 |
| need_approval | TINYINT(1) | N | 0 | 分配该角色是否需审批 |
| priority | INT | N | 999 | 优先级（数值越小越高） |
| icon | VARCHAR(64) | Y | NULL | 图标 |
| color | VARCHAR(16) | Y | NULL | 标签颜色 |
| description | VARCHAR(500) | Y | NULL | 角色描述 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_code(code,is_deleted)`、`idx_name`、`idx_category`、`idx_parent(parent_role_id)`、`idx_level`。

### 05.4 表：`mdm_role_permission`（角色权限）— 扩展

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| menu_id | BIGINT UNSIGNED | N | - | 菜单 ID |
| menu_code | VARCHAR(128) | N | - | 菜单编码（冗余） |
| perm_code | VARCHAR(128) | Y | NULL | 权限码（冗余） |
| permission | VARCHAR(255) | N | - | 权限动作集（逗号分隔） |
| grant_type | VARCHAR(16) | N | 'GRANT' | GRANT/DENY |
| is_inherited | TINYINT(1) | N | 0 | 是否继承自父角色 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_role_menu(role_id,menu_id)`、`idx_menu(menu_id)`、`idx_perm(perm_code)`。

### 05.5 表：`mdm_role_inherit`（角色继承）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 子角色 ID |
| parent_role_id | BIGINT UNSIGNED | N | - | 父角色 ID |
| inherit_mode | VARCHAR(16) | N | 'UNION' | UNION（并集）/INTERSECT |
| depth | TINYINT | N | 1 | 继承深度 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_role(role_id)`（单继承）、`idx_parent(parent_role_id)`。

### 05.6 表：`mdm_role_api`（角色接口白名单）

用于菜单未覆盖的接口（如内部接口、特殊业务接口）直接授权。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| api_path | VARCHAR(255) | N | - | 接口路径（支持通配） |
| http_method | VARCHAR(16) | N | 'GET' | 方法 |
| api_name | VARCHAR(128) | Y | NULL | 接口名称 |
| module_code | VARCHAR(8) | Y | NULL | 所属模块 |
| grant_type | VARCHAR(16) | N | 'GRANT' | GRANT/DENY |
| description | VARCHAR(255) | Y | NULL | 说明 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_role_api(role_id,api_path,http_method)`、`idx_path(api_path)`。

### 05.7 表：`mdm_role_conflict_rule`（角色冲突规则）

职责分离（SoD）：某些角色不可同时授予同一用户（如"收费员"与"退费审核人"）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| rule_code | VARCHAR(32) | N | - | 规则编码 |
| rule_name | VARCHAR(128) | N | - | 规则名称 |
| role_a_id | BIGINT UNSIGNED | N | - | 角色 A |
| role_b_id | BIGINT UNSIGNED | N | - | 角色 B |
| conflict_type | VARCHAR(16) | N | 'MUTEX' | MUTEX（互斥）/WARN（告警） |
| reason | VARCHAR(500) | Y | NULL | 冲突原因 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_rule(rule_code)`、`uk_role_pair(role_a_id,role_b_id)`。

**预置规则示例：**

| 规则 | 角色 A | 角色 B | 类型 | 原因 |
|---|---|---|---|---|
| SoD-01 | 收费员 | 退费审核人 | MUTEX | 防止自收自退 |
| SoD-02 | 收费员 | 财务稽核 | MUTEX | 防止自收自核 |
| SoD-03 | 药品采购 | 药品验收 | MUTEX | 防止自采自验 |
| SoD-04 | 权限管理员 | 安全审计员 | MUTEX | 等保要求 |
| SoD-05 | 处方医生 | 处方审核药师 | WARN | 建议分离 |

### 05.8 表：`mdm_data_scope`（数据权限范围）— 扩展

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 范围编码 |
| name | VARCHAR(64) | N | - | 范围名称 |
| scope_type | VARCHAR(32) | N | - | ALL/DEPT/DEPT_TREE/SELF/CUSTOM |
| data_domain | VARCHAR(32) | N | 'DEPT' | 数据域 DEPT/DOCTOR/NURSE/PATIENT/WAREHOUSE/ORG/SELF_CREATED |
| dept_ids | VARCHAR(2000) | Y | NULL | 自定义科室集 |
| org_ids | VARCHAR(255) | Y | NULL | 包含院区 |
| include_stopped_dept | TINYINT(1) | N | 0 | 含停用科室 |
| include_sub_dept | TINYINT(1) | N | 1 | 含下级科室（DEPT_TREE 生效） |
| scope_expression | VARCHAR(1000) | Y | NULL | 高级表达式（自定义 SQL 片段，需白名单） |
| apply_role_ids | VARCHAR(2000) | Y | NULL | 适用角色（反向关联） |
| apply_user_ids | VARCHAR(2000) | Y | NULL | 适用用户 |
| is_builtin | TINYINT(1) | N | 0 | 是否内置 |
| description | VARCHAR(255) | Y | NULL | 说明 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_code(code,is_deleted)`、`idx_type(scope_type)`、`idx_domain(data_domain)`。

### 05.9 表：`mdm_role_data_scope`（角色数据权限）

角色在某数据域上的数据范围（一个角色可有多个数据域）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| data_domain | VARCHAR(32) | N | - | 数据域 |
| data_scope_id | BIGINT UNSIGNED | N | - | 数据范围 ID |
| scope_type | VARCHAR(32) | N | - | 冗余，便于计算 |
| custom_dept_ids | VARCHAR(2000) | Y | NULL | 冗余自定义科室集 |
| priority | INT | N | 999 | 优先级 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_role_domain(role_id,data_domain)`、`idx_scope(data_scope_id)`。

### 05.10 表：`mdm_field_def`（字段定义 / 敏感字段字典）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| field_key | VARCHAR(128) | N | - | 字段键 `module.entity.field` |
| field_name | VARCHAR(128) | N | - | 字段中文名 |
| module_code | VARCHAR(8) | N | - | 所属模块 |
| entity_name | VARCHAR(64) | N | - | 实体名（表名/对象名） |
| field_name_db | VARCHAR(64) | Y | NULL | 数据库字段名 |
| sensitivity_level | VARCHAR(16) | N | 'NORMAL' | PUBLIC/NORMAL/SENSITIVE/HIGHLY_SENSITIVE |
| default_action | VARCHAR(16) | N | 'VISIBLE' | VISIBLE/MASKED/HIDDEN |
| mask_rule | VARCHAR(64) | Y | NULL | 脱敏规则 ID |
| mask_example | VARCHAR(128) | Y | NULL | 脱敏示例 |
| need_second_factor | TINYINT(1) | N | 0 | 查看明文是否需二次验证 |
| encrypt_storage | TINYINT(1) | N | 0 | 是否加密存储 |
| audit_view | TINYINT(1) | N | 0 | 查看是否记审计 |
| description | VARCHAR(255) | Y | NULL | 说明 |
| status | TINYINT | N | 1 | 状态 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_field(field_key)`、`idx_module(module_code)`、`idx_sensitivity(sensitivity_level)`。

### 05.11 表：`mdm_role_field_perm`（角色字段权限）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| field_id | BIGINT UNSIGNED | N | - | 字段 ID |
| field_key | VARCHAR(128) | N | - | 字段键（冗余） |
| field_action | VARCHAR(16) | N | - | VISIBLE/MASKED/HIDDEN/EDITABLE/READONLY |
| mask_rule | VARCHAR(64) | Y | NULL | 覆盖默认脱敏规则 |
| need_second_factor | TINYINT(1) | N | 0 | 覆盖默认二次验证 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_role_field(role_id,field_id)`、`idx_field(field_id)`。

### 05.12 表：`mdm_second_factor_policy`（二次验证策略）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| policy_code | VARCHAR(32) | N | - | 策略编码 |
| policy_name | VARCHAR(128) | N | - | 策略名称 |
| trigger_type | VARCHAR(32) | N | - | OPERATION/PATH/FIELD/RISK |
| trigger_key | VARCHAR(255) | N | - | 触发键（权限码/接口路径/字段键） |
| second_factor_type | VARCHAR(32) | N | 'SMS' | SMS/GESTURE/TOTP/CA/multi |
| verify_ttl_seconds | INT | N | 300 | 验证有效期（秒） |
| apply_role_ids | VARCHAR(2000) | Y | NULL | 适用角色（空=全部） |
| exempt_role_ids | VARCHAR(2000) | Y | NULL | 豁免角色 |
| risk_ip_check | TINYINT(1) | N | 0 | 是否检查非常用 IP |
| risk_time_check | TINYINT(1) | N | 0 | 是否检查非常用时段 |
| risk_freq_check | TINYINT(1) | N | 0 | 是否检查高频操作 |
| risk_freq_threshold | INT | Y | NULL | 高频阈值（次/分钟） |
| priority | INT | N | 999 | 优先级 |
| description | VARCHAR(255) | Y | NULL | 说明 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_policy(policy_code,is_deleted)`、`idx_trigger(trigger_type,trigger_key)`。

**预置策略：**

| 策略 | 触发 | 方式 | 有效期 |
|---|---|---|---|
| SFP-01 | 审批操作（`*:approve`） | SMS | 300s |
| SFP-02 | 批量审批 | SMS | 300s |
| SFP-03 | 明文查看敏感字段 | SMS | 300s |
| SFP-04 | 导出敏感数据 | SMS | 300s |
| SFP-05 | 删除操作（`*:delete`） | GESTURE | 300s |
| SFP-06 | 召回操作 | SMS | 300s |
| SFP-07 | 权限分配（`mdm:role:assign_perm`） | SMS + TOTP | 300s |
| SFP-08 | 全量同步 | SMS | 300s |
| SFP-09 | 退费审批 | SMS | 300s |
| SFP-10 | 折扣审批（>10%） | SMS | 300s |

### 05.13 表：`mdm_position`（岗位）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 岗位编码 |
| name | VARCHAR(64) | N | - | 岗位名称 |
| position_category | VARCHAR(32) | N | - | 岗位类别 |
| dept_type | VARCHAR(255) | Y | NULL | 适用科室类型 |
| is_leader | TINYINT(1) | N | 0 | 是否管理岗 |
| approval_level | INT | N | 0 | 审批级别 |
| sort_no | INT | N | 999 | 排序 |
| description | VARCHAR(255) | Y | NULL | 说明 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_code(code,is_deleted)`、`idx_category`。

### 05.14 表：`mdm_position_role`（岗位默认角色）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| position_id | BIGINT UNSIGNED | N | - | 岗位 ID |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| is_default | TINYINT(1) | N | 1 | 是否默认授予 |
| sort_no | INT | N | 999 | 排序 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_position_role(position_id,role_id)`、`idx_role(role_id)`。

### 05.15 表：`mdm_user_group`（用户组）— 扩展

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 用户组编码 |
| name | VARCHAR(64) | N | - | 用户组名称 |
| group_type | VARCHAR(32) | N | - | DEPT/SCHEDULE/APPROVE/FOLLOWUP/SALES/CUSTOM |
| group_category | VARCHAR(32) | Y | NULL | 细分类型 |
| leader_staff_id | BIGINT UNSIGNED | Y | NULL | 组长 |
| dept_id | BIGINT UNSIGNED | Y | NULL | 所属科室 |
| is_permission_carrier | TINYINT(1) | N | 0 | 是否作为权限主体（承载角色） |
| member_count | INT | N | 0 | 成员数（冗余） |
| purpose | VARCHAR(255) | Y | NULL | 用途说明 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_code(code,is_deleted)`、`idx_type(group_type)`、`idx_dept(dept_id)`。

### 05.16 表：`mdm_user_group_member`（用户组成员）— 扩展

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| group_id | BIGINT UNSIGNED | N | - | 组 ID |
| staff_id | BIGINT UNSIGNED | N | - | 职工 ID |
| member_role | VARCHAR(32) | N | 'MEMBER' | LEADER/MEMBER |
| join_date | DATE | Y | NULL | 加入日期 |
| leave_date | DATE | Y | NULL | 离开日期 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_group_staff(group_id,staff_id)`、`idx_staff(staff_id)`。

### 05.17 表：`mdm_user_group_role`（用户组角色）

用户组作为权限主体时，组内成员继承组角色。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| group_id | BIGINT UNSIGNED | N | - | 组 ID |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| include_sub_group | TINYINT(1) | N | 0 | 是否含子组 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_group_role(group_id,role_id)`、`idx_role(role_id)`。

### 05.18 表：`mdm_role_user`（角色用户绑定）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| role_id | BIGINT UNSIGNED | N | - | 角色 ID |
| staff_id | BIGINT UNSIGNED | N | - | 职工 ID |
| dept_id | BIGINT UNSIGNED | Y | NULL | 角色生效的科室上下文（多科室执业） |
| grant_type | VARCHAR(16) | N | 'DIRECT' | DIRECT/GROUP/POSITION/DUTY/TEMPLATE |
| grant_source_id | BIGINT UNSIGNED | Y | NULL | 来源 ID（组 ID/岗位 ID） |
| source_dept_id | BIGINT UNSIGNED | Y | NULL | 来源科室 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL=长期） |
| is_primary | TINYINT(1) | N | 0 | 是否主岗位角色 |
| status | TINYINT | N | 1 | 状态 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | Y | NULL | 授权人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 授权时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_role_staff(role_id,staff_id,dept_id)`、`idx_staff(staff_id,status)`、`idx_role(role_id)`、`idx_expire(expire_date)`。

### 05.19 表：`mdm_user_permission`（用户直接权限）

用于临时授权/收回单个用户权限，不影响角色。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| staff_id | BIGINT UNSIGNED | N | - | 职工 ID |
| perm_type | VARCHAR(16) | N | 'MENU' | MENU/API/FIELD/DATA_SCOPE |
| target_id | BIGINT UNSIGNED | Y | NULL | 目标 ID（菜单/字段/范围） |
| target_key | VARCHAR(255) | N | - | 目标键（权限码/字段键/范围编码） |
| permission | VARCHAR(255) | Y | NULL | 权限动作 |
| grant_type | VARCHAR(16) | N | 'GRANT' | GRANT/DENY |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| reason | VARCHAR(500) | Y | NULL | 授权原因 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 授权人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_staff_target(staff_id,perm_type,target_key)`、`idx_expire(expire_date)`。

### 05.20 表：`mdm_permission_template`（权限模板）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 模板编码 |
| name | VARCHAR(128) | N | - | 模板名称 |
| template_type | VARCHAR(32) | N | 'ROLE' | ROLE/POSITION/DEPT |
| apply_dept_type | VARCHAR(255) | Y | NULL | 适用科室类型 |
| base_role_id | BIGINT UNSIGNED | Y | NULL | 基于哪个角色 |
| menu_count | INT | N | 0 | 包含菜单数 |
| perm_count | INT | N | 0 | 包含权限数 |
| description | VARCHAR(500) | Y | NULL | 说明 |
| is_builtin | TINYINT(1) | N | 0 | 是否内置 |
| status | TINYINT | N | 1 | 状态 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_code(code,is_deleted)`、`idx_type(template_type)`。

### 05.21 表：`mdm_permission_template_item`（权限模板明细）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| template_id | BIGINT UNSIGNED | N | - | 模板 ID |
| item_type | VARCHAR(16) | N | 'MENU' | MENU/DATA_SCOPE/FIELD |
| menu_id | BIGINT UNSIGNED | Y | NULL | 菜单 ID |
| menu_code | VARCHAR(128) | Y | NULL | 菜单编码 |
| perm_code | VARCHAR(128) | Y | NULL | 权限码 |
| permission | VARCHAR(255) | Y | NULL | 权限动作 |
| data_domain | VARCHAR(32) | Y | NULL | 数据域（DATA_SCOPE 类型） |
| scope_type | VARCHAR(32) | Y | NULL | 范围类型 |
| field_key | VARCHAR(128) | Y | NULL | 字段键（FIELD 类型） |
| field_action | VARCHAR(16) | Y | NULL | 字段动作 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_template(template_id)`、`idx_menu(menu_id)`。

### 05.22 表：`mdm_permission_apply`（权限申请单）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| apply_no | VARCHAR(32) | N | - | 申请单号 PA+年月日+流水 |
| apply_type | VARCHAR(32) | N | - | GRANT_ROLE/REVOKE_ROLE/CREATE_ROLE/MODIFY_ROLE/TEMP_GRANT/FIELD_ACCESS |
| target_staff_id | BIGINT UNSIGNED | Y | NULL | 目标用户（授权类） |
| target_role_id | BIGINT UNSIGNED | Y | NULL | 目标角色 |
| target_dept_id | BIGINT UNSIGNED | Y | NULL | 目标科室 |
| apply_reason | VARCHAR(500) | N | - | 申请原因 |
| effective_date | DATE | Y | NULL | 期望生效日期 |
| expire_date | DATE | Y | NULL | 期望失效日期 |
| urgency | VARCHAR(16) | N | 'NORMAL' | NORMAL/URGENT |
| attachment_ids | VARCHAR(500) | Y | NULL | 附件 |
| apply_status | VARCHAR(16) | N | 'DRAFT' | DRAFT/PENDING/APPROVING/APPROVED/REJECTED/WITHDRAWN/EFFECTIVE |
| current_node | VARCHAR(64) | Y | NULL | 当前节点 |
| current_approver_id | BIGINT UNSIGNED | Y | NULL | 当前审批人 |
| approve_chain | VARCHAR(1000) | Y | NULL | 审批链 JSON |
| apply_by | BIGINT UNSIGNED | N | - | 申请人 |
| apply_at | DATETIME | N | CURRENT_TIMESTAMP | 申请时间 |
| finish_at | DATETIME | Y | NULL | 完成时间 |
| sla_hours | INT | N | 24 | SLA 小时 |
| version | INT | N | 0 | 乐观锁 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_apply_no(apply_no)`、`idx_status(apply_status)`、`idx_staff(target_staff_id)`、`idx_approver(current_approver_id)`、`idx_apply_by(apply_by,apply_status)`。

### 05.23 表：`mdm_permission_apply_detail`（权限申请明细）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| apply_id | BIGINT UNSIGNED | N | - | 申请单 ID |
| item_type | VARCHAR(16) | N | 'MENU' | MENU/ROLE/DATA_SCOPE/FIELD/API |
| item_key | VARCHAR(255) | N | - | 项目键 |
| item_name | VARCHAR(255) | Y | NULL | 项目名称 |
| operation | VARCHAR(16) | N | 'ADD' | ADD/REMOVE |
| permission | VARCHAR(255) | Y | NULL | 权限动作 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_apply(apply_id)`。

### 05.24 表：`mdm_permission_change_log`（权限变更日志）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| change_scope | VARCHAR(32) | N | - | MENU/ROLE/ROLE_PERM/USER_ROLE/DATA_SCOPE/FIELD_PERM/TEMPLATE/APPLY |
| target_id | BIGINT UNSIGNED | Y | NULL | 目标 ID |
| target_key | VARCHAR(255) | Y | NULL | 目标键 |
| target_name | VARCHAR(255) | Y | NULL | 目标名称 |
| change_type | VARCHAR(32) | N | - | CREATE/UPDATE/DELETE/GRANT/REVOKE/ENABLE/DISABLE/IMPORT |
| before_snapshot | JSON | Y | NULL | 变更前快照 |
| after_snapshot | JSON | Y | NULL | 变更后快照 |
| changed_fields | VARCHAR(2000) | Y | NULL | 变更字段 |
| change_summary | VARCHAR(1000) | Y | NULL | 变更摘要 |
| change_reason | VARCHAR(500) | Y | NULL | 变更原因 |
| apply_id | BIGINT UNSIGNED | Y | NULL | 关联申请单 |
| affected_user_count | INT | N | 0 | 影响用户数 |
| operator_id | BIGINT UNSIGNED | N | - | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| user_agent | VARCHAR(500) | Y | NULL | 客户端 |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 操作时间 |

**索引：** `idx_scope(change_scope,created_at)`、`idx_target(target_id)`、`idx_operator(operator_id,created_at)`、`idx_apply(apply_id)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 10 年。

### 05.25 表：`mdm_permission_version`（权限版本快照）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| object_type | VARCHAR(32) | N | - | ROLE/USER/MENU/DATA_SCOPE/FIELD |
| object_id | BIGINT UNSIGNED | N | - | 对象 ID |
| object_key | VARCHAR(128) | Y | NULL | 对象键 |
| version_no | INT | N | - | 版本号 |
| snapshot_json | JSON | N | - | 完整快照 |
| perm_count | INT | N | 0 | 权限项数 |
| change_type | VARCHAR(32) | N | - | 变更类型 |
| apply_id | BIGINT UNSIGNED | Y | NULL | 关联申请单 |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_object(object_type,object_id,version_no)`、`idx_created(created_at)`。

**分区：** 按 `created_at` 月份 RANGE 分区。

### 05.26 表：`mdm_permission_sync_log`（权限同步日志）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| event_id | VARCHAR(64) | N | - | 事件 ID |
| event_type | VARCHAR(64) | N | - | mdm.role.changed 等 |
| change_scope | VARCHAR(32) | N | - | 变更范围 |
| target_key | VARCHAR(255) | Y | NULL | 目标键 |
| subscriber | VARCHAR(32) | N | - | 订阅方 M02/M20/... |
| deliver_mode | VARCHAR(16) | N | 'MQ' | MQ/HTTP/REDIS |
| payload | JSON | Y | NULL | 消息体 |
| sync_status | VARCHAR(16) | N | 'PENDING' | PENDING/SUCCESS/FAILED/IGNORED |
| retry_count | INT | N | 0 | 重试次数 |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| affected_user_count | INT | N | 0 | 影响用户数 |
| cost_ms | INT | Y | NULL | 耗时 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| finished_at | DATETIME | Y | NULL | 完成时间 |

**索引：** `uk_event_sub(event_id,subscriber)`、`idx_status(sync_status,created_at)`、`idx_subscriber(subscriber,sync_status)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 1 年。

### 05.27 表：`mdm_permission_cache_task`（权限缓存刷新任务）

权限变更影响用户多时，异步批量刷新缓存。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| task_no | VARCHAR(32) | N | - | 任务号 |
| trigger_type | VARCHAR(32) | N | - | ROLE_CHANGE/MENU_CHANGE/USER_ROLE_CHANGE/MANUAL/FULL |
| trigger_source | VARCHAR(128) | Y | NULL | 触发源 |
| affected_staff_count | INT | N | 0 | 影响用户数 |
| affected_staff_ids | TEXT | Y | NULL | 用户 ID 列表（大任务） |
| task_status | VARCHAR(16) | N | 'PENDING' | PENDING/RUNNING/SUCCESS/FAILED/PARTIAL |
| success_count | INT | N | 0 | 成功数 |
| fail_count | INT | N | 0 | 失败数 |
| started_at | DATETIME | Y | NULL | 开始时间 |
| finished_at | DATETIME | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_task_no(task_no)`、`idx_status(task_status)`、`idx_created(created_at)`。

### 05.28 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/permission.py
"""权限主数据 ORM 模型"""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, JSON,
    Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class Menu(Base, TimestampMixin, SoftDeleteMixin):
    """菜单与功能点"""
    __tablename__ = "mdm_menu"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), nullable=False, comment="菜单编码")
    perm_code: Mapped[Optional[str]] = mapped_column(String(128), comment="权限码")
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(64))
    module_code: Mapped[str] = mapped_column(String(8), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    parent_path: Mapped[Optional[str]] = mapped_column(String(500))
    level_no: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    menu_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="MODULE/MENU/BUTTON")
    route_path: Mapped[Optional[str]] = mapped_column(String(255))
    component: Mapped[Optional[str]] = mapped_column(String(255))
    api_pattern: Mapped[Optional[str]] = mapped_column(String(500))
    http_method: Mapped[Optional[str]] = mapped_column(String(16))
    icon: Mapped[Optional[str]] = mapped_column(String(64))
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    visible: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    cacheable: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    mobile_visible: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_public: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_system: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    badge_rule: Mapped[Optional[str]] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    children: Mapped[List["Menu"]] = relationship(
        "Menu", back_populates="parent", lazy="selectin",
        primaryjoin="and_(Menu.parent_id==Menu.id, Menu.is_deleted==0)",
    )
    parent: Mapped[Optional["Menu"]] = relationship(
        "Menu", back_populates="children", remote_side=[id],
    )

    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uk_menu_code"),
        UniqueConstraint("perm_code", "is_deleted", name="uk_perm_code"),
        Index("idx_module", "module_code"),
        Index("idx_parent", "parent_id"),
        Index("idx_type", "menu_type"),
        {"comment": "菜单与功能点"},
    )


class Role(Base, TimestampMixin, SoftDeleteMixin):
    """角色"""
    __tablename__ = "mdm_role"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(64))
    role_category: Mapped[str] = mapped_column(String(32), default="BUSINESS", nullable=False)
    role_level: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    parent_role_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    apply_dept_type: Mapped[Optional[str]] = mapped_column(String(255))
    apply_dept_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    default_data_scope_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    max_user_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_builtin: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_assignable: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    need_approval: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    icon: Mapped[Optional[str]] = mapped_column(String(64))
    color: Mapped[Optional[str]] = mapped_column(String(16))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    # 关系
    permissions: Mapped[List["RolePermission"]] = relationship(
        back_populates="role", lazy="selectin", cascade="all, delete-orphan",
    )
    data_scopes: Mapped[List["RoleDataScope"]] = relationship(
        back_populates="role", lazy="selectin", cascade="all, delete-orphan",
    )
    field_perms: Mapped[List["RoleFieldPerm"]] = relationship(
        back_populates="role", lazy="selectin", cascade="all, delete-orphan",
    )
    users: Mapped[List["RoleUser"]] = relationship(
        back_populates="role", lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uk_role_code"),
        Index("idx_role_name", "name"),
        Index("idx_role_category", "role_category"),
        Index("idx_role_parent", "parent_role_id"),
        {"comment": "角色"},
    )

    # ---------- 领域方法 ----------
    @property
    def is_system_role(self) -> bool:
        return self.role_category == "SYSTEM"

    def visible_menu_ids(self) -> List[int]:
        """可见菜单 ID 集合（排除 DENY）"""
        grants = {p.menu_id for p in self.permissions if p.grant_type == "GRANT"}
        denies = {p.menu_id for p in self.permissions if p.grant_type == "DENY"}
        return list(grants - denies)

    def perm_codes(self) -> List[str]:
        """权限码集合"""
        return [p.perm_code for p in self.permissions
                if p.perm_code and p.grant_type == "GRANT"]

    def to_snapshot(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "role_category": self.role_category,
            "parent_role_id": self.parent_role_id,
            "menu_count": len(self.visible_menu_ids()),
            "perm_count": len(self.perm_codes()),
        }


class RolePermission(Base):
    """角色权限"""
    __tablename__ = "mdm_role_permission"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    menu_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    menu_code: Mapped[str] = mapped_column(String(128), nullable=False)
    perm_code: Mapped[Optional[str]] = mapped_column(String(128))
    permission: Mapped[str] = mapped_column(String(255), nullable=False)
    grant_type: Mapped[str] = mapped_column(String(16), default="GRANT", nullable=False)
    is_inherited: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="permissions")

    __table_args__ = (
        UniqueConstraint("role_id", "menu_id", name="uk_role_menu"),
        Index("idx_perm_menu", "menu_id"),
        Index("idx_perm_code", "perm_code"),
        {"comment": "角色权限"},
    )


class RoleDataScope(Base):
    """角色数据权限（角色 × 数据域 × 范围）"""
    __tablename__ = "mdm_role_data_scope"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    data_domain: Mapped[str] = mapped_column(String(32), nullable=False)
    data_scope_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    custom_dept_ids: Mapped[Optional[str]] = mapped_column(String(2000))
    priority: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="data_scopes")

    __table_args__ = (
        UniqueConstraint("role_id", "data_domain", name="uk_role_domain"),
        Index("idx_rds_scope", "data_scope_id"),
        {"comment": "角色数据权限"},
    )


class RoleFieldPerm(Base):
    """角色字段权限"""
    __tablename__ = "mdm_role_field_perm"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    field_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    field_action: Mapped[str] = mapped_column(String(16), nullable=False)
    mask_rule: Mapped[Optional[str]] = mapped_column(String(64))
    need_second_factor: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="field_perms")

    __table_args__ = (
        UniqueConstraint("role_id", "field_id", name="uk_role_field"),
        Index("idx_rfp_field", "field_id"),
        {"comment": "角色字段权限"},
    )


class RoleUser(Base):
    """角色用户绑定"""
    __tablename__ = "mdm_role_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    staff_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    grant_type: Mapped[str] = mapped_column(String(16), default="DIRECT", nullable=False)
    grant_source_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    source_dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    is_primary: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    role: Mapped["Role"] = relationship(back_populates="users")

    __table_args__ = (
        UniqueConstraint("role_id", "staff_id", "dept_id", name="uk_role_staff"),
        Index("idx_ru_staff", "staff_id", "status"),
        Index("idx_ru_role", "role_id"),
        Index("idx_ru_expire", "expire_date"),
        {"comment": "角色用户绑定"},
    )

    def is_valid(self) -> bool:
        """绑定是否在有效期内"""
        today = date.today()
        if self.status != 1:
            return False
        if self.effective_date and self.effective_date > today:
            return False
        if self.expire_date and self.expire_date < today:
            return False
        return True


class DataScope(Base, TimestampMixin, SoftDeleteMixin):
    """数据权限范围"""
    __tablename__ = "mdm_data_scope"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    data_domain: Mapped[str] = mapped_column(String(32), default="DEPT", nullable=False)
    dept_ids: Mapped[Optional[str]] = mapped_column(String(2000))
    org_ids: Mapped[Optional[str]] = mapped_column(String(255))
    include_stopped_dept: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    include_sub_dept: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    scope_expression: Mapped[Optional[str]] = mapped_column(String(1000))
    apply_role_ids: Mapped[Optional[str]] = mapped_column(String(2000))
    apply_user_ids: Mapped[Optional[str]] = mapped_column(String(2000))
    is_builtin: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uk_scope_code"),
        Index("idx_scope_type", "scope_type"),
        Index("idx_scope_domain", "data_domain"),
        {"comment": "数据权限范围"},
    )

    # 范围宽度用于合并时取最宽
    SCOPE_WEIGHT = {"ALL": 100, "CUSTOM": 80, "DEPT_TREE": 60, "DEPT": 40, "SELF": 20}

    @property
    def weight(self) -> int:
        return self.SCOPE_WEIGHT.get(self.scope_type, 0)


class FieldDef(Base, SoftDeleteMixin):
    """字段定义（敏感字段字典）"""
    __tablename__ = "mdm_field_def"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    field_key: Mapped[str] = mapped_column(String(128), nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), nullable=False)
    module_code: Mapped[str] = mapped_column(String(8), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(64), nullable=False)
    field_name_db: Mapped[Optional[str]] = mapped_column(String(64))
    sensitivity_level: Mapped[str] = mapped_column(String(16), default="NORMAL", nullable=False)
    default_action: Mapped[str] = mapped_column(String(16), default="VISIBLE", nullable=False)
    mask_rule: Mapped[Optional[str]] = mapped_column(String(64))
    mask_example: Mapped[Optional[str]] = mapped_column(String(128))
    need_second_factor: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    encrypt_storage: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    audit_view: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("field_key", name="uk_field_key"),
        Index("idx_fd_module", "module_code"),
        Index("idx_fd_sensitivity", "sensitivity_level"),
        {"comment": "字段定义"},
    )
```

### 05.29 Pydantic Schema 定义

```python
# app/schemas/mdm/permission.py
"""权限主数据 Pydantic Schema"""
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==================== 菜单 ====================
class MenuBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    name_en: Optional[str] = Field(None, max_length=64)
    module_code: str = Field(..., pattern=r"^M\d{2}$")
    parent_id: Optional[int] = None
    menu_type: Literal["MODULE", "MENU", "BUTTON"]
    perm_code: Optional[str] = Field(None, max_length=128)
    route_path: Optional[str] = Field(None, max_length=255)
    component: Optional[str] = Field(None, max_length=255)
    api_pattern: Optional[str] = Field(None, max_length=500)
    http_method: Optional[str] = Field(None, max_length=16)
    icon: Optional[str] = Field(None, max_length=64)
    sort_no: int = 999
    visible: bool = True
    cacheable: bool = False
    mobile_visible: bool = True
    is_public: bool = False
    badge_rule: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_menu(self):
        if self.menu_type == "BUTTON" and not self.perm_code:
            raise ValueError("功能点(BUTTON)必须设置权限码")
        if self.menu_type == "MENU" and not self.route_path:
            raise ValueError("菜单(MENU)必须设置前端路由")
        if self.perm_code:
            # 权限码格式 module:resource:action
            parts = self.perm_code.split(":")
            if len(parts) != 3:
                raise ValueError("权限码格式必须为 {模块}:{资源}:{动作}")
            if not all(p.strip() for p in parts):
                raise ValueError("权限码各段不能为空")
        if self.menu_type == "MODULE" and self.parent_id:
            raise ValueError("模块(MODULE)不能有上级菜单")
        return self


class MenuCreate(MenuBase):
    code: Optional[str] = Field(None, description="为空则自动生成")


class MenuUpdate(MenuBase):
    version: Optional[int] = None


class MenuTreeNode(BaseModel):
    """菜单树节点"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    perm_code: Optional[str] = None
    module_code: str
    menu_type: str
    route_path: Optional[str] = None
    icon: Optional[str] = None
    sort_no: int = 999
    visible: bool = True
    is_system: bool = False
    status: int = 1
    children: List["MenuTreeNode"] = []


# ==================== 角色 ====================
class RolePermissionItem(BaseModel):
    menu_id: int
    menu_code: Optional[str] = None
    perm_code: Optional[str] = None
    permission: str = Field(..., description="VIEW,CREATE,EDIT,DELETE,APPROVE,EXPORT,IMPORT")
    grant_type: Literal["GRANT", "DENY"] = "GRANT"


class RoleDataScopeItem(BaseModel):
    data_domain: Literal[
        "DEPT", "DOCTOR", "NURSE", "PATIENT", "WAREHOUSE", "ORG", "SELF_CREATED"
    ]
    scope_type: Literal["ALL", "DEPT", "DEPT_TREE", "SELF", "CUSTOM"]
    data_scope_id: Optional[int] = None
    custom_dept_ids: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope_type == "CUSTOM" and not self.custom_dept_ids:
            raise ValueError("自定义数据范围必须选择至少一个科室")
        return self


class RoleFieldPermItem(BaseModel):
    field_key: str = Field(..., max_length=128)
    field_action: Literal["VISIBLE", "MASKED", "HIDDEN", "EDITABLE", "READONLY"]
    mask_rule: Optional[str] = Field(None, max_length=64)
    need_second_factor: bool = False


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    name_en: Optional[str] = Field(None, max_length=64)
    role_category: Literal["SYSTEM", "POSITION", "DEPT", "BUSINESS", "CUSTOM"] = "BUSINESS"
    role_level: Literal["SUPER", "HIGH", "NORMAL", "LOW"] = "NORMAL"
    parent_role_id: Optional[int] = None
    apply_dept_type: Optional[List[str]] = None
    apply_dept_ids: Optional[List[int]] = None
    default_data_scope_id: Optional[int] = None
    max_user_count: Optional[int] = Field(None, ge=1)
    is_assignable: bool = True
    need_approval: bool = False
    priority: int = 999
    icon: Optional[str] = Field(None, max_length=64)
    color: Optional[str] = Field(None, max_length=16)
    description: Optional[str] = Field(None, max_length=500)


class RoleCreate(RoleBase):
    code: Optional[str] = Field(None, description="为空则自动生成")
    permissions: List[RolePermissionItem] = []
    data_scopes: List[RoleDataScopeItem] = []
    field_perms: List[RoleFieldPermItem] = []
    template_id: Optional[int] = Field(None, description="从模板创建")


class RoleUpdate(RoleBase):
    permissions: Optional[List[RolePermissionItem]] = None
    data_scopes: Optional[List[RoleDataScopeItem]] = None
    field_perms: Optional[List[RoleFieldPermItem]] = None
    version: Optional[int] = None


class RoleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    role_category: str
    role_category_name: Optional[str] = None
    role_level: str
    parent_role_id: Optional[int] = None
    parent_role_name: Optional[str] = None
    is_builtin: bool = False
    menu_count: int = 0
    perm_count: int = 0
    user_count: int = 0
    priority: int = 999
    status: int = 1
    description: Optional[str] = None
    updated_at: Optional[datetime] = None


class RoleDetail(RoleListItem):
    name_en: Optional[str] = None
    apply_dept_type: Optional[List[str]] = None
    apply_dept_ids: Optional[List[int]] = None
    default_data_scope_id: Optional[int] = None
    default_data_scope_name: Optional[str] = None
    max_user_count: Optional[int] = None
    is_assignable: bool = True
    need_approval: bool = False
    icon: Optional[str] = None
    color: Optional[str] = None
    version: Optional[int] = None
    permissions: List[RolePermissionItem] = []
    data_scopes: List[RoleDataScopeItem] = []
    field_perms: List[RoleFieldPermItem] = []
    menu_ids: List[int] = []


# ==================== 权限上下文（核心契约） ====================
class PermissionContext(BaseModel):
    """M01 → M02 的权限上下文契约"""
    staff_id: int
    staff_code: str
    staff_name: str
    dept_id: Optional[int] = None
    dept_name: Optional[str] = None
    dept_path: Optional[str] = None
    org_id: int = 1

    roles: List[dict] = []                    # [{role_id, role_code, role_name, dept_id}]
    menus: List[dict] = []                    # 菜单树（已过滤无权限项）
    perm_codes: List[str] = []                # 权限码列表
    data_scopes: dict = {}                    # {data_domain: {scope_type, dept_ids, ...}}
    field_rules: dict = {}                    # {field_key: {action, mask_rule, need_second_factor}}
    second_factor_ops: List[str] = []         # 需二次验证的权限码
    menu_version: str = ""                    # 权限版本号（用于缓存比对）
    computed_at: str = ""                     # 计算时间


# ==================== 用户角色分配 ====================
class UserRoleAssign(BaseModel):
    staff_id: int
    role_ids: List[int]
    dept_id: Optional[int] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    reason: str = Field(..., max_length=500)
    skip_conflict_check: bool = False

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_date and self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("失效日期必须晚于生效日期")
        return self


class BatchUserRoleAssign(BaseModel):
    staff_ids: List[int] = Field(..., min_length=1, max_length=500)
    role_ids: List[int] = Field(..., min_length=1)
    grant_type: Literal["DIRECT", "TEMPLATE"] = "DIRECT"
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    reason: str = Field(..., max_length=500)


# ==================== 数据范围 ====================
class DataScopeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    scope_type: Literal["ALL", "DEPT", "DEPT_TREE", "SELF", "CUSTOM"]
    data_domain: Literal[
        "DEPT", "DOCTOR", "NURSE", "PATIENT", "WAREHOUSE", "ORG", "SELF_CREATED"
    ] = "DEPT"
    dept_ids: Optional[List[int]] = None
    org_ids: Optional[List[int]] = None
    include_stopped_dept: bool = False
    include_sub_dept: bool = True
    description: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_scope(self):
        if self.scope_type == "CUSTOM" and not self.dept_ids:
            raise ValueError("自定义范围必须选择至少一个科室")
        if self.scope_type != "CUSTOM" and self.dept_ids:
            raise ValueError("非自定义范围不应指定科室列表")
        return self


class DataScopeCreate(DataScopeBase):
    code: Optional[str] = None


class DataScopeUpdate(DataScopeBase):
    pass


# ==================== 字段权限 ====================
class FieldPermBatchItem(BaseModel):
    field_key: str
    field_action: Literal["VISIBLE", "MASKED", "HIDDEN", "EDITABLE", "READONLY"]
    mask_rule: Optional[str] = None
    need_second_factor: bool = False


class FieldPermBatchUpdate(BaseModel):
    role_id: int
    items: List[FieldPermBatchItem]
    reason: Optional[str] = Field(None, max_length=500)


# ==================== 权限申请 ====================
class PermissionApplyCreate(BaseModel):
    apply_type: Literal[
        "GRANT_ROLE", "REVOKE_ROLE", "CREATE_ROLE", "MODIFY_ROLE",
        "TEMP_GRANT", "FIELD_ACCESS",
    ]
    target_staff_id: Optional[int] = None
    target_role_id: Optional[int] = None
    target_dept_id: Optional[int] = None
    apply_reason: str = Field(..., min_length=5, max_length=500)
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    urgency: Literal["NORMAL", "URGENT"] = "NORMAL"
    attachment_ids: Optional[List[int]] = None
    details: List[dict] = []

    @model_validator(mode="after")
    def validate_apply(self):
        if self.apply_type in ("GRANT_ROLE", "REVOKE_ROLE", "TEMP_GRANT"):
            if not self.target_staff_id or not self.target_role_id:
                raise ValueError("授权/收权申请必须指定目标用户与角色")
        if self.apply_type == "TEMP_GRANT" and not self.expire_date:
            raise ValueError("临时授权必须指定失效日期")
        return self


# ==================== 权限模板 ====================
class TemplateItemSchema(BaseModel):
    item_type: Literal["MENU", "DATA_SCOPE", "FIELD"]
    menu_id: Optional[int] = None
    menu_code: Optional[str] = None
    perm_code: Optional[str] = None
    permission: Optional[str] = None
    data_domain: Optional[str] = None
    scope_type: Optional[str] = None
    field_key: Optional[str] = None
    field_action: Optional[str] = None


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    template_type: Literal["ROLE", "POSITION", "DEPT"] = "ROLE"
    apply_dept_type: Optional[List[str]] = None
    base_role_id: Optional[int] = None
    description: Optional[str] = Field(None, max_length=500)
    items: List[TemplateItemSchema] = []


# ==================== 查询 ====================
class RoleQuery(BaseModel):
    keyword: Optional[str] = None
    role_category: Optional[List[str]] = None
    role_level: Optional[str] = None
    apply_dept_type: Optional[str] = None
    is_builtin: Optional[bool] = None
    status: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    sort_by: str = "priority"
    sort_order: Literal["asc", "desc"] = "asc"


class MenuQuery(BaseModel):
    keyword: Optional[str] = None
    module_code: Optional[str] = None
    menu_type: Optional[str] = None
    status: Optional[int] = None
```

---

---

## 06. 收费数据结构

> **来源：** [收费详细设计](M01_主数据管理MDM_06_收费_详细设计.md) · 第 4 章
> **主数据域：** 费用域（`FEE`） · **表数：** 25

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 06.2 | `md_charge_item` | 收费项目主表 |
| 06.3 | `md_charge_item_ext` | 收费项目扩展表 |
| 06.4 | `md_charge_item_alias` | 收费项目别名表 |
| 06.5 | `md_charge_item_rel` | 收费项目关联表 |
| 06.6 | `md_charge_item_pricing_rule` | 计价规则表 |
| 06.7 | `md_charge_item_field` | 收费项目自定义字段 |
| 06.8 | `md_charge_item_discount_rel` | 项目优惠适用表 |
| 06.9 | `md_price_list` | 价表主表 |
| 06.10 | `md_price_item` | 价表明细表 |
| 06.11 | `md_price_history` | 价格历史表 |
| 06.12 | `md_price_adjust` | 调价单主表 |
| 06.13 | `md_price_adjust_detail` | 调价明细表 |
| 06.14 | `md_discount_policy` | 优惠方案表 |
| 06.15 | `md_discount_policy_item` | 优惠适用项目表 |
| 06.16 | `md_discount_policy_log` | 优惠使用记录表 |
| 06.17 | `md_charge_combo` | 收费组合/套餐主表 |
| 06.18 | `md_charge_combo_detail` | 套餐明细表 |
| 06.19 | `md_payment_method` | 支付方式表 |
| 06.20 | `md_refund_policy` | 退费规则表 |
| 06.21 | `md_invoice_config` | 发票配置表 |
| 06.22 | `md_invoice_number_segment` | 发票号码段表 |
| 06.23 | `md_charge_change_log` | 变更日志表 |
| 06.24 | `md_charge_sync_log` | 同步日志表 |
| 06.25 | `md_charge_code_seq` | 编码序列表 |
| 06.26 | `md_price_cache_task` | 价格缓存刷新任务表 |

---

### 06.1 ER 关系图

```
                    ┌──────────────────────────┐
                    │  md_charge_item          │
                    │  （收费项目主表）         │
                    └────────────┬─────────────┘
                                 │ 1
        ┌──────────────┬─────────┼──────────┬──────────────┬──────────────┐
        │ 1:N          │ 1:N     │ N:M      │ 1:N          │ 1:N          │
        ▼              ▼         ▼          ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌──────────────┐
│md_charge_    │ │md_charge_│ │md_charge_│ │md_charge_  │ │md_charge_  │ │md_charge_    │
│item_ext      │ │item_alias│ │item_rel  │ │item_       │ │item_       │ │item_discount │
│（扩展）       │ │（别名）   │ │（关联）   │ │pricing_rule│ │field（扩展 │ │_rel（优惠适用）│
└──────────────┘ └──────────┘ └──────────┘ └────────────┘ └────────────┘ └──────────────┘
                                                                  │
                    ┌─────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  md_price_list        │
        │  （价表主表）          │
        └───────────┬───────────┘
                    │ 1:N
                    ▼
        ┌───────────────────────┐
        │  md_price_item        │
        │  （价表明细）          │
        └───────────┬───────────┘
                    │ 1:N（版本化）
                    ▼
        ┌───────────────────────┐
        │  md_price_history     │
        │  （价格历史，永久）    │
        └───────────┬───────────┘
                    │ N:1
                    ▼
        ┌───────────────────────┐
        │  md_price_adjust      │
        │  （调价单）            │
        └───────────┬───────────┘
                    │ 1:N
                    ▼
        ┌───────────────────────┐
        │ md_price_adjust_detail│
        │ （调价明细）           │
        └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_discount_policy    │ 1:N  │ md_discount_policy_   │
        │ （优惠方案）           │◄────►│ item（适用项目）       │
        └───────────┬───────────┘      └───────────────────────┘
                    │ 1:N
                    ▼
        ┌───────────────────────┐
        │md_discount_policy_log │
        │ （使用记录）           │
        └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_charge_combo       │ 1:N  │ md_charge_combo_detail│
        │ （收费组合/套餐）      │◄────►│ （套餐明细）           │
        └───────────────────────┘      └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_payment_method     │      │ md_refund_policy      │
        │ （支付方式）           │      │ （退费规则）           │
        └───────────────────────┘      └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_invoice_config     │      │ md_invoice_number_    │
        │ （发票配置）           │ 1:N  │ segment（号码段）     │
        └───────────────────────┘      └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_charge_change_log  │      │ md_charge_sync_log    │
        │ （变更日志）           │      │ （同步日志）           │
        └───────────────────────┘      └───────────────────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_charge_code_seq    │      │ md_price_cache_task   │
        │ （编码序列）           │      │ （缓存刷新任务）       │
        └───────────────────────┘      └───────────────────────┘
```

**表清单（共 25 张）：**

| 序号 | 表名 | 中文名 | 说明 | 预估量级 |
|---|---|---|---|---|
| 1 | `md_charge_item` | 收费项目主表 | 核心 | 5,000 |
| 2 | `md_charge_item_ext` | 收费项目扩展表 | 1:1 | 5,000 |
| 3 | `md_charge_item_alias` | 收费项目别名表 | 1:N | 8,000 |
| 4 | `md_charge_item_rel` | 收费项目关联表 | 1:N | 12,000 |
| 5 | `md_charge_item_pricing_rule` | 计价规则表 | 1:N | 6,000 |
| 6 | `md_charge_item_field` | 收费项目自定义字段 | 1:N | 10,000 |
| 7 | `md_charge_item_discount_rel` | 项目优惠适用表 | N:M | 20,000 |
| 8 | `md_price_list` | 价表主表 | 核心 | 30 |
| 9 | `md_price_item` | 价表明细表 | 核心 | 80,000 |
| 10 | `md_price_history` | 价格历史表 | 永久保留 | 200,000 |
| 11 | `md_price_adjust` | 调价单主表 | 治理 | 1,000/年 |
| 12 | `md_price_adjust_detail` | 调价明细表 | 治理 | 30,000/年 |
| 13 | `md_discount_policy` | 优惠方案表 | 核心 | 100 |
| 14 | `md_discount_policy_item` | 优惠适用项目表 | 1:N | 3,000 |
| 15 | `md_discount_policy_log` | 优惠使用记录表 | 统计 | 50,000/年 |
| 16 | `md_charge_combo` | 收费组合/套餐主表 | 核心 | 300 |
| 17 | `md_charge_combo_detail` | 套餐明细表 | 1:N | 3,000 |
| 18 | `md_payment_method` | 支付方式表 | 核心 | 30 |
| 19 | `md_refund_policy` | 退费规则表 | 核心 | 50 |
| 20 | `md_invoice_config` | 发票配置表 | 核心 | 30 |
| 21 | `md_invoice_number_segment` | 发票号码段表 | 核心 | 500/年 |
| 22 | `md_charge_change_log` | 变更日志表 | 审计 | 100,000/年 |
| 23 | `md_charge_sync_log` | 同步日志表 | 运维 | 300,000/年 |
| 24 | `md_charge_code_seq` | 编码序列表 | 运维 | 100 |
| 25 | `md_price_cache_task` | 价格缓存刷新任务表 | 运维 | 5,000/年 |

### 06.2 表：`md_charge_item`（收费项目主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 收费编码 C+大类+流水 |
| name | VARCHAR(128) | N | - | 收费项目名称（与物价公示一致） |
| short_name | VARCHAR(64) | N | - | 收费简称（发票/清单打印） |
| english_name | VARCHAR(255) | Y | NULL | 英文名 |
| pinyin_code | VARCHAR(32) | N | - | 拼音码 |
| pinyin_short | VARCHAR(32) | N | - | 拼音首字母 |
| wb_code | VARCHAR(32) | Y | NULL | 五笔码 |
| charge_class | VARCHAR(32) | N | - | 项目主分类（3.1.1） |
| sub_class | VARCHAR(32) | Y | NULL | 子分类（如检查→眼科影像） |
| account_class | VARCHAR(64) | Y | NULL | 会计科目 |
| income_subject | VARCHAR(64) | Y | NULL | 收入科目 |
| cost_subject | VARCHAR(64) | Y | NULL | 成本项目 |
| spec | VARCHAR(128) | Y | NULL | 规格 |
| unit | VARCHAR(16) | N | - | 计价单位（次/项/天/眼/枚/片/副） |
| price_code | VARCHAR(32) | Y | NULL | 物价局编码 |
| item_content | TEXT | Y | NULL | 项目内涵（物价规定） |
| exclude_content | TEXT | Y | NULL | 除外内容 |
| instruction | TEXT | Y | NULL | 说明 |
| pricing_mode | VARCHAR(32) | N | 'FIXED' | 计价方式（3.1.2） |
| standard_price | DECIMAL(12,4) | N | 0 | 标准价 |
| current_price | DECIMAL(12,4) | N | 0 | 当前价（冗余，生效时更新） |
| cost_price | DECIMAL(12,4) | Y | NULL | 成本价 |
| max_retail_price | DECIMAL(12,4) | Y | NULL | 最高零售限价 |
| min_retail_price | DECIMAL(12,4) | Y | NULL | 最低零售限价 |
| charge_by_eye | TINYINT(1) | N | 0 | 是否按眼别 |
| allow_split_qty | TINYINT(1) | N | 1 | 是否可拆分数量 |
| default_qty | DECIMAL(12,4) | N | 1 | 默认数量 |
| min_qty | DECIMAL(12,4) | Y | NULL | 最小计价单位 |
| max_qty | DECIMAL(12,4) | Y | NULL | 最大计价数量 |
| qty_precision | TINYINT | N | 0 | 数量小数位（0/1/2） |
| allow_discount | TINYINT(1) | N | 1 | 是否可打折 |
| max_discount_rate | DECIMAL(7,4) | Y | NULL | 最高折扣率（%，如 80 表示最低打 8 折） |
| min_discount_rate | DECIMAL(7,4) | Y | NULL | 最低折扣率 |
| discount_need_approve | TINYINT(1) | N | 0 | 折扣是否需要审批 |
| allow_refund | TINYINT(1) | N | 1 | 是否可退费 |
| refund_need_approve | TINYINT(1) | N | 0 | 退费是否需要审批 |
| refund_window_hours | INT | Y | NULL | 退费时间窗口（小时） |
| refund_ratio | DECIMAL(7,4) | N | 100 | 退费比例（%） |
| allow_points | TINYINT(1) | N | 1 | 参与会员积分 |
| points_ratio | DECIMAL(6,2) | N | 1.0 | 积分倍率 |
| default_dept_id | BIGINT UNSIGNED | N | - | 默认执行科室 |
| exec_dept_ids | VARCHAR(1000) | Y | NULL | 可执行科室 |
| need_apply | TINYINT(1) | N | 0 | 是否需申请 |
| link_order | TINYINT(1) | N | 1 | 是否关联医嘱 |
| link_material | TINYINT(1) | N | 0 | 是否关联耗材 |
| material_ids | VARCHAR(1000) | Y | NULL | 关联耗材 |
| dept_accounting | TINYINT(1) | N | 1 | 是否科室核算 |
| account_belong | VARCHAR(32) | Y | NULL | 开单科室/执行科室/分成 |
| share_ratio | DECIMAL(7,4) | Y | NULL | 分成比例（%） |
| finance_category | VARCHAR(32) | Y | NULL | 财务分类 |
| insurance_code | VARCHAR(64) | Y | NULL | 医保编码（预留） |
| insurance_class | VARCHAR(16) | Y | 'NA' | 甲/乙/丙/不适用（预留） |
| self_pay_ratio | DECIMAL(7,4) | N | 100 | 自付比例（预留） |
| commercial_insurance_code | VARCHAR(64) | Y | NULL | 商保编码（预留） |
| is_common | TINYINT(1) | N | 0 | 是否常用（收费界面置顶） |
| hotkey | VARCHAR(16) | Y | NULL | 收费快捷键 |
| sort_no | INT | N | 999 | 排序 |
| is_active_for_new | TINYINT(1) | N | 1 | 新开单可选 |
| status | VARCHAR(16) | N | 'DRAFT' | 状态：DRAFT/ENABLED/DISABLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| ext_json | JSON | Y | NULL | 扩展字段 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_charge_item | PRIMARY | id | 主键 |
| uk_ci_code | UNIQUE | code, deleted | 编码唯一 |
| uk_ci_hotkey | UNIQUE | hotkey, deleted | 快捷键唯一 |
| idx_ci_name | NORMAL | name | 名称查询 |
| idx_ci_short | NORMAL | short_name | 简称查询 |
| idx_ci_pinyin | NORMAL | pinyin_code, pinyin_short | 拼音检索 |
| idx_ci_class | NORMAL | charge_class | 分类过滤 |
| idx_ci_subclass | NORMAL | sub_class | 子分类 |
| idx_ci_dept | NORMAL | default_dept_id | 执行科室 |
| idx_ci_common | NORMAL | is_common, status | 常用项目 |
| idx_ci_status | NORMAL | status, audit_status | 状态过滤 |
| idx_ci_updated | NORMAL | updated_at | 增量同步 |
| ft_ci_name | FULLTEXT | name, short_name, english_name | 中文分词检索 |

### 06.3 表：`md_charge_item_ext`（收费项目扩展表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码（冗余） |
| pricing_unit_group | VARCHAR(64) | Y | NULL | 计价单位组（如"眼"=1，可匹配眼别数） |
| tier_config | JSON | Y | NULL | 阶梯价配置 `[{max_qty, price}]` |
| combo_price | DECIMAL(12,4) | Y | NULL | 套餐打包价 |
| combo_original_price | DECIMAL(12,4) | Y | NULL | 套餐原价合计 |
| combo_discount_rate | DECIMAL(7,4) | Y | NULL | 套餐折扣率 |
| is_combo | TINYINT(1) | N | 0 | 是否套餐 |
| need_patient_confirm | TINYINT(1) | N | 0 | 是否需患者确认（如自费项目） |
| need_informed_consent | TINYINT(1) | N | 0 | 是否需知情同意 |
| is_self_pay_only | TINYINT(1) | N | 1 | 是否仅自费（无医保） |
| is_high_value | TINYINT(1) | N | 0 | 是否高值（需特殊审批） |
| is_special_management | TINYINT(1) | N | 0 | 是否特殊管理（精麻药等） |
| is_oral_liquid | TINYINT(1) | N | 0 | 是否口服液（按毫升计） |
| default_discount_policy_id | BIGINT UNSIGNED | Y | NULL | 默认优惠方案 |
| pricing_desc | VARCHAR(500) | Y | NULL | 计价说明 |
| display_order_in_bill | INT | Y | NULL | 账单显示顺序 |
| bill_group | VARCHAR(32) | Y | NULL | 账单分组 |
| custom_fields | JSON | Y | NULL | 自定义字段值 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ext_item(charge_item_id, deleted)` 唯一；`idx_ext_combo(is_combo)`。

### 06.4 表：`md_charge_item_alias`（收费项目别名表）

支持同一收费项目的多种叫法（物价名、简称、临床习惯名、旧系统名），提升检索命中率。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| alias_name | VARCHAR(200) | N | - | 别名 |
| alias_type | VARCHAR(32) | N | 'CLINICAL' | 别名类型：CLINICAL/OFFICIAL/HISTORICAL/ABBREVIATION |
| pinyin_code | VARCHAR(64) | Y | NULL | 别名拼音 |
| pinyin_short | VARCHAR(32) | Y | NULL | 别名首字母 |
| sort_no | INT | N | 999 | 排序 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_alias(charge_item_id, alias_name, deleted)` 唯一；`idx_alias_name(alias_name)`；`idx_alias_pinyin(pinyin_short)`。

### 06.5 表：`md_charge_item_rel`（收费项目关联表）

收费项目与检查项目、手术项目、药品、耗材、视光产品等的映射。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| rel_object_type | VARCHAR(32) | N | - | 关联类型：EXAM/OPERATION/DRUG/MATERIAL/OPTICAL/LAB |
| rel_object_id | BIGINT UNSIGNED | N | - | 关联对象 ID |
| rel_object_code | VARCHAR(32) | Y | NULL | 关联对象编码 |
| rel_object_name | VARCHAR(200) | Y | NULL | 关联对象名称（冗余） |
| rel_type | VARCHAR(32) | N | 'PRIMARY' | PRIMARY/SECONDARY/BUNDLED |
| qty_factor | DECIMAL(12,4) | N | 1 | 数量换算（1 对象 = N 收费单位） |
| price_source | VARCHAR(32) | N | 'FIXED' | 价格来源：FIXED/OBJECT（从对象取价）/PRICE_LIST |
| auto_charge | TINYINT(1) | N | 1 | 是否自动计费 |
| charge_scene | VARCHAR(64) | Y | NULL | 计费场景（门诊/住院/手术/视光） |
| is_default | TINYINT(1) | N | 0 | 是否默认关联 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_item_rel(charge_item_id, rel_object_type, rel_object_id, deleted)`；`idx_rel_object(rel_object_type, rel_object_id)`。

### 06.6 表：`md_charge_item_pricing_rule`（计价规则表）

用于复杂计价场景（阶梯价、按眼别、按部位、附加费）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| rule_type | VARCHAR(32) | N | - | TIERED/BY_EYE/BY_PART/BY_AREA/EXTRA/SURCHARGE |
| rule_name | VARCHAR(128) | Y | NULL | 规则名称 |
| priority | INT | N | 999 | 优先级 |
| min_qty | DECIMAL(12,4) | Y | NULL | 数量区间起 |
| max_qty | DECIMAL(12,4) | Y | NULL | 数量区间止 |
| unit_price | DECIMAL(12,4) | Y | NULL | 单价 |
| total_price | DECIMAL(12,4) | Y | NULL | 固定总价 |
| extra_amount | DECIMAL(12,4) | Y | NULL | 附加金额 |
| extra_rate | DECIMAL(7,4) | Y | NULL | 附加比例（%） |
| part_code | VARCHAR(32) | Y | NULL | 部位编码（左眼/右眼/双眼） |
| part_qty_factor | DECIMAL(6,2) | Y | NULL | 部位数量换算（如双眼=2） |
| condition_json | JSON | Y | NULL | 适用条件 `{member_level, patient_type, dept_id}` |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `idx_pr_item(charge_item_id)`；`idx_pr_type(rule_type)`。

**计价规则示例：**

| 规则类型 | 配置 | 效果 |
|---|---|---|
| TIERED | min_qty=1, max_qty=5, unit_price=280 | 1~5 次按 280/次 |
| TIERED | min_qty=6, max_qty=10, unit_price=250 | 6~10 次按 250/次 |
| BY_EYE | part_code=LEFT/RIGHT, part_qty_factor=1 | 单眼 1 倍价 |
| BY_EYE | part_code=BOTH, part_qty_factor=2 | 双眼 2 倍价 |
| EXTRA | extra_amount=50 | 加收 50 元（如造影剂） |
| SURCHARGE | extra_rate=20 | 加收 20%（如夜间加急） |

### 06.7 表：`md_charge_item_field`（收费项目自定义字段）

用于不同分类的收费项目展示不同属性（如检查项目需要检查部位、手术项目需要手术级别）。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| field_key | VARCHAR(64) | N | - | 字段键 |
| field_name | VARCHAR(128) | N | - | 字段名称 |
| field_type | VARCHAR(32) | N | 'TEXT' | TEXT/NUMBER/SELECT/DATE/BOOL |
| field_value | VARCHAR(500) | Y | NULL | 字段值 |
| options_json | JSON | Y | NULL | 选项（下拉） |
| unit | VARCHAR(32) | Y | NULL | 单位 |
| sort_no | INT | N | 999 | 排序 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_item_field(charge_item_id, field_key)` 唯一。

### 06.8 表：`md_charge_item_discount_rel`（项目优惠适用表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| discount_policy_id | BIGINT UNSIGNED | N | - | 优惠方案 ID |
| discount_policy_code | VARCHAR(32) | N | - | 优惠方案编码 |
| rel_type | VARCHAR(16) | N | 'INCLUDE' | INCLUDE（适用）/EXCLUDE（排除） |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_item_policy(charge_item_id, discount_policy_id, rel_type)`；`idx_policy(discount_policy_id)`。

### 06.9 表：`md_price_list`（价表主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 价表编码 PL+流水 |
| name | VARCHAR(128) | N | - | 价表名称 |
| price_type | VARCHAR(32) | N | - | STANDARD/MEMBER/INSURANCE/INTERNAL/DEPT/ACTIVITY |
| priority | INT | N | 100 | 取价优先级（数值越小越优先） |
| apply_object | VARCHAR(64) | Y | NULL | 适用对象：ALL/DEPT/MEMBER/INSURANCE |
| apply_dept_ids | VARCHAR(2000) | Y | NULL | 适用科室 |
| apply_member_levels | VARCHAR(500) | Y | NULL | 适用会员等级 |
| apply_patient_types | VARCHAR(255) | Y | NULL | 适用患者类型（门诊/住院/视光/屈光） |
| currency | VARCHAR(8) | N | 'CNY' | 币种 |
| default_markup_rate | DECIMAL(7,4) | Y | NULL | 默认加价率（%） |
| is_default | TINYINT(1) | N | 0 | 是否默认价表 |
| item_count | INT | N | 0 | 明细项数（冗余） |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| status | TINYINT | N | 1 | 状态 |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_pl_code(code,deleted)` 唯一；`idx_pl_type(price_type)`；`idx_pl_priority(priority,status)`；`idx_pl_default(is_default,status)`。

**唯一约束：** 同一 `price_type` 只能有一个 `is_default=1` 的价表（通过生成列 + 唯一索引保证）。

### 06.10 表：`md_price_item`（价表明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| price_list_id | BIGINT UNSIGNED | N | - | 价表 ID |
| price_list_code | VARCHAR(32) | N | - | 价表编码（冗余） |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码（冗余） |
| original_price | DECIMAL(12,4) | N | 0 | 原价（标准价） |
| price | DECIMAL(12,4) | N | 0 | 价表价 |
| markup_rate | DECIMAL(7,4) | Y | NULL | 加价率（%） |
| discount_rate | DECIMAL(7,4) | Y | NULL | 相对标准价折扣率（%） |
| max_retail_price | DECIMAL(12,4) | Y | NULL | 最高零售限价 |
| min_retail_price | DECIMAL(12,4) | Y | NULL | 最低零售限价 |
| cost_price | DECIMAL(12,4) | Y | NULL | 成本价 |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL=当前有效） |
| is_current | TINYINT(1) | N | 1 | 是否当前有效 |
| adjust_id | BIGINT UNSIGNED | Y | NULL | 来源调价单 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_pi_list_item(price_list_id, charge_item_id, effective_date, deleted)`；`idx_pi_item(charge_item_id)`；`idx_pi_current(price_list_id, charge_item_id, is_current)`；`idx_pi_effective(effective_date, expire_date)`。

**当前价唯一性：** 通过生成列保证同一价表同一项目只有一个 `is_current=1`：

```sql
ALTER TABLE md_price_item
  ADD COLUMN current_key VARCHAR(128)
    GENERATED ALWAYS AS (
      CASE WHEN is_current = 1 AND deleted = 0
           THEN CONCAT(price_list_id, ':', charge_item_id)
           ELSE CONCAT('X', id) END
    ) STORED,
  ADD UNIQUE KEY uk_pi_current (current_key);
```

### 06.11 表：`md_price_history`（价格历史表）

**永久保留**，是价格版本化的核心，保证历史单据取价正确。

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| object_type | VARCHAR(32) | N | - | CHARGE_ITEM/PRICE_ITEM/DRUG/MATERIAL/OPTICAL |
| object_id | BIGINT UNSIGNED | N | - | 对象 ID |
| object_code | VARCHAR(32) | N | - | 对象编码 |
| object_name | VARCHAR(200) | Y | NULL | 对象名称（冗余） |
| price_list_id | BIGINT UNSIGNED | Y | NULL | 价表 ID（收费项目适用） |
| price_list_code | VARCHAR(32) | Y | NULL | 价表编码 |
| price_type | VARCHAR(32) | Y | NULL | 价格类型 |
| price | DECIMAL(12,4) | N | 0 | 价格 |
| cost_price | DECIMAL(12,4) | Y | NULL | 成本价 |
| max_retail_price | DECIMAL(12,4) | Y | NULL | 最高零售限价 |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期（NULL=当前有效） |
| adjust_id | BIGINT UNSIGNED | Y | NULL | 来源调价单 |
| adjust_reason | VARCHAR(500) | Y | NULL | 调价原因 |
| adjust_doc_no | VARCHAR(128) | Y | NULL | 调价文号 |
| price_version | INT | N | 1 | 价格版本号（递增） |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_ph_object(object_type, object_id, effective_date)`；`idx_ph_code(object_code)`；`idx_ph_effective(effective_date)`；`idx_ph_current(object_type, object_id, expire_date)`。

**分区：** 按 `effective_date` 年份 RANGE 分区（保留 10 年）。

**取价查询示例：**

```sql
SELECT price, effective_date
FROM md_price_history
WHERE object_type = 'CHARGE_ITEM'
  AND object_code = 'C0300127'
  AND price_list_code = 'PL001'
  AND effective_date <= '2025-06-15'
  AND (expire_date IS NULL OR expire_date >= '2025-06-15')
ORDER BY effective_date DESC
LIMIT 1;
```

### 06.12 表：`md_price_adjust`（调价单主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 调价单号 PA+年月+流水 |
| adjust_type | VARCHAR(32) | N | - | CHARGE/PRICE_LIST/DRUG/MATERIAL/OPTICAL/BATCH |
| adjust_mode | VARCHAR(32) | N | 'MANUAL' | MANUAL/RATE/AMOUNT/UNIFIED/IMPORT |
| reason | VARCHAR(500) | N | - | 调整事由 |
| policy_ref | VARCHAR(128) | Y | NULL | 政策依据/文件号 |
| effective_date | DATE | N | - | 生效日期 |
| apply_scope | VARCHAR(32) | Y | NULL | 适用价表 |
| item_count | INT | N | 0 | 涉及项目数 |
| total_old_amount | DECIMAL(14,4) | Y | NULL | 调整前金额合计（参考） |
| total_new_amount | DECIMAL(14,4) | Y | NULL | 调整后金额合计（参考） |
| change_rate_avg | DECIMAL(7,4) | Y | NULL | 平均涨跌幅 |
| attachment_ids | VARCHAR(500) | Y | NULL | 附件 |
| approver_id | BIGINT UNSIGNED | Y | NULL | 最终审批人 |
| approve_status | VARCHAR(16) | N | 'DRAFT' | DRAFT/PENDING/APPROVING/APPROVED/REJECTED/EFFECTIVE/REVOKED |
| current_node | VARCHAR(64) | Y | NULL | 当前审批节点 |
| current_approver_id | BIGINT UNSIGNED | Y | NULL | 当前审批人 |
| approve_chain | VARCHAR(1000) | Y | NULL | 审批链 JSON |
| approve_at | DATETIME | Y | NULL | 审批时间 |
| approve_opinion | VARCHAR(500) | Y | NULL | 审批意见 |
| effect_at | DATETIME | Y | NULL | 实际生效时间 |
| revoke_reason | VARCHAR(500) | Y | NULL | 撤销原因 |
| version | INT | N | 0 | 乐观锁版本号 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 申请人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 申请时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_pa_code(code,deleted)` 唯一；`idx_pa_status(approve_status)`；`idx_pa_effective(effective_date, approve_status)`；`idx_pa_type(adjust_type)`；`idx_pa_approver(current_approver_id)`。

### 06.13 表：`md_price_adjust_detail`（调价明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| adjust_id | BIGINT UNSIGNED | N | - | 调价单 ID |
| adjust_code | VARCHAR(32) | N | - | 调价单号（冗余） |
| object_type | VARCHAR(32) | N | - | 对象类型 |
| object_id | BIGINT UNSIGNED | N | - | 对象 ID |
| object_code | VARCHAR(32) | N | - | 对象编码 |
| object_name | VARCHAR(200) | N | - | 对象名称 |
| price_list_id | BIGINT UNSIGNED | Y | NULL | 价表 ID |
| old_price | DECIMAL(12,4) | N | 0 | 旧价 |
| new_price | DECIMAL(12,4) | N | 0 | 新价 |
| change_amount | DECIMAL(12,4) | Y | NULL | 涨跌金额 |
| change_rate | DECIMAL(7,4) | Y | NULL | 涨跌幅（%） |
| is_over_limit | TINYINT(1) | N | 0 | 是否超限价 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'VALID' | VALID/SKIPPED |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_pad_adjust(adjust_id)`；`idx_pad_object(object_type, object_id)`。

### 06.14 表：`md_discount_policy`（优惠方案表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 方案编码 DP+流水 |
| name | VARCHAR(128) | N | - | 方案名称 |
| policy_type | VARCHAR(32) | N | - | DISCOUNT/FULL_REDUCE/PACKAGE/GIFT/MEMBER/ACTIVITY |
| apply_scene | VARCHAR(255) | N | - | 适用范围（门诊/住院/视光/屈光） |
| apply_charge_classes | VARCHAR(500) | Y | NULL | 适用收费类别 |
| apply_object_scope | VARCHAR(16) | N | 'ALL' | ALL/INCLUDE/EXCLUDE |
| discount_rate | DECIMAL(7,4) | Y | NULL | 折扣率（%，90 表示 9 折） |
| full_amount | DECIMAL(12,4) | Y | NULL | 满减门槛 |
| reduce_amount | DECIMAL(12,4) | Y | NULL | 减现金额 |
| package_price | DECIMAL(12,4) | Y | NULL | 套餐价 |
| gift_desc | VARCHAR(500) | Y | NULL | 赠品说明 |
| apply_member_levels | VARCHAR(500) | Y | NULL | 适用会员等级 |
| apply_patient_tags | VARCHAR(255) | Y | NULL | 适用患者标签 |
| apply_dept_ids | VARCHAR(2000) | Y | NULL | 适用科室 |
| min_amount | DECIMAL(12,4) | Y | NULL | 最低消费金额 |
| max_reduce_amount | DECIMAL(12,4) | Y | NULL | 最高优惠金额 |
| effective_date | DATE | N | - | 生效日期 |
| expire_date | DATE | N | - | 失效日期 |
| available_time | VARCHAR(255) | Y | NULL | 可用时段（如周一至周五 09:00-17:00） |
| available_weekdays | VARCHAR(32) | Y | NULL | 可用星期 |
| limit_per_person | INT | Y | NULL | 每人限用次数 |
| limit_per_day | INT | Y | NULL | 每日限用次数 |
| total_quota | INT | Y | NULL | 总名额 |
| used_quota | INT | N | 0 | 已用名额 |
| allow_stack | TINYINT(1) | N | 0 | 可与其他优惠叠加 |
| stack_priority | INT | N | 100 | 叠加优先级 |
| need_approve | TINYINT(1) | N | 0 | 使用是否需审批 |
| approve_threshold | DECIMAL(7,4) | Y | NULL | 折扣低于此值需审批 |
| approver_role_id | BIGINT UNSIGNED | Y | NULL | 审批角色 |
| min_discount_rate | DECIMAL(7,4) | N | 100 | 最低折扣底线（%） |
| is_auto_apply | TINYINT(1) | N | 0 | 是否自动应用 |
| status | VARCHAR(16) | N | 'DRAFT' | DRAFT/ENABLED/DISABLED/EXPIRED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_dp_code(code,deleted)` 唯一；`idx_dp_type(policy_type)`；`idx_dp_effective(effective_date, expire_date, status)`；`idx_dp_auto(is_auto_apply, status)`。

### 06.15 表：`md_discount_policy_item`（优惠适用项目表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| discount_policy_id | BIGINT UNSIGNED | N | - | 优惠方案 ID |
| discount_policy_code | VARCHAR(32) | N | - | 方案编码 |
| object_type | VARCHAR(32) | N | 'CHARGE_ITEM' | CHARGE_ITEM/OPTICAL/OPERATION/DRUG |
| object_id | BIGINT UNSIGNED | N | - | 对象 ID |
| object_code | VARCHAR(32) | N | - | 对象编码 |
| object_name | VARCHAR(200) | Y | NULL | 对象名称 |
| rel_type | VARCHAR(16) | N | 'INCLUDE' | INCLUDE/EXCLUDE |
| discount_rate | DECIMAL(7,4) | Y | NULL | 该项目的专属折扣率（覆盖方案级） |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_dpi_policy_object(discount_policy_id, object_type, object_id, rel_type)`。

### 06.16 表：`md_discount_policy_log`（优惠使用记录表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| discount_policy_id | BIGINT UNSIGNED | N | - | 优惠方案 ID |
| discount_policy_code | VARCHAR(32) | N | - | 方案编码 |
| usage_date | DATE | N | - | 使用日期 |
| patient_id | BIGINT UNSIGNED | Y | NULL | 患者 ID |
| patient_no | VARCHAR(32) | Y | NULL | 患者卡号 |
| bill_no | VARCHAR(64) | Y | NULL | 账单号（M16） |
| charge_item_code | VARCHAR(32) | Y | NULL | 收费项目编码 |
| original_amount | DECIMAL(14,4) | N | 0 | 原金额 |
| discount_amount | DECIMAL(14,4) | N | 0 | 优惠金额 |
| final_amount | DECIMAL(14,4) | N | 0 | 最终金额 |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| dept_id | BIGINT UNSIGNED | Y | NULL | 科室 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_dpl_policy(discount_policy_id, usage_date)`；`idx_dpl_date(usage_date)`；`idx_dpl_patient(patient_id)`。

### 06.17 表：`md_charge_combo`（收费组合/套餐主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 套餐编码 CM+流水 |
| name | VARCHAR(128) | N | - | 套餐名称 |
| short_name | VARCHAR(64) | Y | NULL | 简称 |
| pinyin_code | VARCHAR(32) | N | - | 拼音码 |
| pinyin_short | VARCHAR(32) | Y | NULL | 拼音首字母 |
| combo_type | VARCHAR(32) | N | - | EXAM（检查套餐）/OPERATION（手术套餐）/OPTICAL（配镜套餐）/PHYSICAL（体检套餐）/CUSTOM |
| apply_dept_ids | VARCHAR(1000) | Y | NULL | 适用科室 |
| apply_patient_types | VARCHAR(255) | Y | NULL | 适用患者类型 |
| is_eye_side_split | TINYINT(1) | N | 0 | 是否按眼别拆分明细（双眼时明细×2） |
| original_price | DECIMAL(12,4) | N | 0 | 原价合计 |
| package_price | DECIMAL(12,4) | N | 0 | 套餐价 |
| discount_rate | DECIMAL(7,4) | Y | NULL | 折扣率（%） |
| save_amount | DECIMAL(12,4) | Y | NULL | 节省金额 |
| item_count | INT | N | 0 | 明细项数 |
| valid_days | INT | Y | NULL | 有效期（天，从购买日起） |
| allow_partial_refund | TINYINT(1) | N | 0 | 是否允许部分退费 |
| sort_no | INT | N | 999 | 排序 |
| status | VARCHAR(16) | N | 'DRAFT' | 状态 |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_cc_code(code,deleted)` 唯一；`idx_cc_type(combo_type)`；`idx_cc_name(name)`；`idx_cc_pinyin(pinyin_code)`。

### 06.18 表：`md_charge_combo_detail`（套餐明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| combo_id | BIGINT UNSIGNED | N | - | 套餐 ID |
| combo_code | VARCHAR(32) | N | - | 套餐编码 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费编码 |
| charge_item_name | VARCHAR(200) | Y | NULL | 项目名称（冗余） |
| default_qty | DECIMAL(12,4) | N | 1 | 默认数量 |
| unit | VARCHAR(16) | Y | NULL | 单位 |
| unit_price | DECIMAL(12,4) | N | 0 | 单价（原价） |
| original_amount | DECIMAL(12,4) | N | 0 | 小计（原价） |
| package_amount | DECIMAL(12,4) | Y | NULL | 套餐分摊金额 |
| is_optional | TINYINT(1) | N | 0 | 是否可选 |
| is_eye_side | TINYINT(1) | N | 0 | 是否按眼别 |
| group_name | VARCHAR(64) | Y | NULL | 分组（如"双眼检查""术前准备"） |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ccd_item(combo_id, charge_item_id, deleted)`；`idx_ccd_item_id(charge_item_id)`。

### 06.19 表：`md_payment_method`（支付方式表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 支付方式编码 |
| name | VARCHAR(64) | N | - | 支付方式名称 |
| pay_category | VARCHAR(32) | N | - | CASH/CARD/SCAN/STORED/INSURANCE/OTHER |
| need_change | TINYINT(1) | N | 0 | 是否需找零 |
| need_card | TINYINT(1) | N | 0 | 是否需刷卡 |
| need_third_party | TINYINT(1) | N | 0 | 是否第三方支付 |
| need_auth_code | TINYINT(1) | N | 0 | 是否需授权码（储值需密码） |
| channel_code | VARCHAR(64) | Y | NULL | 渠道编码（商户号/appid） |
| channel_name | VARCHAR(64) | Y | NULL | 渠道名称（微信/支付宝） |
| need_reconcile | TINYINT(1) | N | 0 | 是否需对账 |
| reconcile_type | VARCHAR(32) | Y | NULL | 对账类型（API/文件/手工） |
| reconcile_file_format | VARCHAR(128) | Y | NULL | 对账文件格式 |
| fee_rate | DECIMAL(6,4) | Y | NULL | 手续费率（%） |
| settlement_days | INT | N | 0 | 结算周期（天，T+N） |
| account_subject | VARCHAR(64) | Y | NULL | 对应会计科目 |
| apply_scene | VARCHAR(255) | Y | NULL | 适用场景（门诊/住院/视光） |
| is_default | TINYINT(1) | N | 0 | 是否默认 |
| sort_no | INT | N | 999 | 排序 |
| status | INTEGER | N | 1 | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_pm_code(code,deleted)` 唯一；`idx_pm_category(pay_category)`；`idx_pm_reconcile(need_reconcile,status)`。

### 06.20 表：`md_refund_policy`（退费规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 规则编码 RF+流水 |
| name | VARCHAR(128) | N | - | 规则名称 |
| apply_charge_classes | VARCHAR(500) | Y | NULL | 适用收费类别（空=全部） |
| apply_scene | VARCHAR(255) | Y | NULL | 适用场景 |
| allow_refund | TINYINT(1) | N | 1 | 是否可退 |
| refund_window_hours | INT | Y | NULL | 退费时间窗口（小时，NULL=不限） |
| refund_window_type | VARCHAR(32) | Y | 'SAME_DAY' | SAME_DAY/WITHIN_HOURS/WITHIN_DAYS/UNLIMITED |
| refund_ratio | DECIMAL(7,4) | N | 100 | 退费比例（%） |
| fee_ratio | DECIMAL(7,4) | N | 0 | 手续费比例（%） |
| allow_partial | TINYINT(1) | N | 1 | 是否允许部分退 |
| allow_executed_refund | TINYINT(1) | N | 0 | 已执行是否可退 |
| allow_dispensed_refund | TINYINT(1) | N | 0 | 已发药是否可退（需退药） |
| need_approve | TINYINT(1) | N | 0 | 是否需审批 |
| approve_threshold_amount | DECIMAL(12,4) | Y | NULL | 审批金额阈值 |
| approve_threshold_rate | DECIMAL(7,4) | Y | NULL | 审批比例阈值（%） |
| approve_chain | VARCHAR(1000) | Y | NULL | 审批链 JSON |
| rollback_points | TINYINT(1) | N | 1 | 是否扣回积分 |
| refund_method | VARCHAR(32) | N | 'ORIGINAL' | 退费方式：ORIGINAL（原路退回）/ANY/CASH |
| allow_negative_stored | TINYINT(1) | N | 0 | 储值余额是否允许负 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| priority | INT | N | 100 | 优先级 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_rf_code(code,deleted)` 唯一；`idx_rf_priority(priority,status)`。

### 06.21 表：`md_invoice_config`（发票配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 配置编码 |
| name | VARCHAR(128) | N | - | 配置名称 |
| invoice_type | VARCHAR(32) | N | - | ELECTRONIC（电子普票）/PAPER（纸质普票）/SPECIAL（专票，预留） |
| invoice_point | VARCHAR(64) | N | - | 开票点（门诊收费/住院/视光） |
| title_type | VARCHAR(16) | N | 'PERSONAL' | PERSONAL/ENTERPRISE/BOTH |
| default_title | VARCHAR(128) | Y | NULL | 默认抬头 |
| tax_rate | DECIMAL(7,4) | N | 0 | 税率（%） |
| is_tax_free | TINYINT(1) | N | 0 | 是否免税（医疗服务） |
| taxrate_by_class | JSON | Y | NULL | 按类别设置税率 |
| number_precision | TINYINT | N | 2 | 金额精度 |
| is_merge_allowed | TINYINT(1) | N | 1 | 是否允许合并开票 |
| print_template | VARCHAR(128) | Y | NULL | 打印模板 |
| invoice_item_format | VARCHAR(32) | N | 'SUMMARY' | DETAIL（明细）/SUMMARY（汇总） |
| open_timing | VARCHAR(32) | N | 'AFTER_PAY' | AFTER_PAY/AFTER_SETTLE/ON_DEMAND |
| red_invoice_rule | VARCHAR(32) | N | 'RED_FLUSH' | RED_FLUSH（红冲）/RETURN | 
| tax_control_type | VARCHAR(32) | Y | NULL | 税控类型（百旺/航天/第三方） |
| tax_control_dev_no | VARCHAR(64) | Y | NULL | 税控设备编号 |
| is_default | TINYINT(1) | N | 0 | 是否默认 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ic_code(code,deleted)` 唯一；`idx_ic_point(invoice_point,status)`。

### 06.22 表：`md_invoice_number_segment`（发票号码段表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| config_id | BIGINT UNSIGNED | N | - | 发票配置 ID |
| invoice_type | VARCHAR(32) | N | - | 票种 |
| invoice_point | VARCHAR(64) | N | - | 开票点 |
| prefix | VARCHAR(16) | Y | NULL | 前缀 |
| start_no | BIGINT | N | - | 起始号 |
| end_no | BIGINT | N | - | 终止号 |
| current_no | BIGINT | N | 0 | 当前号 |
| used_count | BIGINT | N | 0 | 已用数 |
| total_count | BIGINT | N | 0 | 本段总数量 |
| assign_date | DATE | Y | NULL | 领用日期 |
| writer_name | VARCHAR(64) | Y | NULL | 领用人 |
| status | VARCHAR(16) | N | 'ACTIVE' | ACTIVE/EXHAUSTED/VOID/EXPIRED |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ins_segment(config_id, prefix, start_no, end_no)`；`idx_ins_status(status)`；`idx_ins_point(invoice_point)`。

### 06.23 表：`md_charge_change_log`（变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| change_scope | VARCHAR(32) | N | - | CHARGE_ITEM/PRICE_LIST/PRICE_ITEM/DISCOUNT/PAYMENT/REFUND/INVOICE/COMBO |
| target_id | BIGINT UNSIGNED | Y | NULL | 目标 ID |
| target_key | VARCHAR(64) | Y | NULL | 目标编码 |
| target_name | VARCHAR(200) | Y | NULL | 目标名称 |
| change_type | VARCHAR(32) | N | - | CREATE/UPDATE/DELETE/ENABLE/DISABLE/PRICE_CHANGE/IMPORT/SYNC |
| before_snapshot | JSON | Y | NULL | 变更前快照 |
| after_snapshot | JSON | Y | NULL | 变更后快照 |
| changed_fields | VARCHAR(2000) | Y | NULL | 变更字段 |
| change_summary | VARCHAR(1000) | Y | NULL | 变更摘要 |
| change_reason | VARCHAR(500) | Y | NULL | 变更原因 |
| adjust_id | BIGINT UNSIGNED | Y | NULL | 关联调价单 |
| affected_item_count | INT | N | 0 | 影响项目数 |
| operator_id | BIGINT UNSIGNED | N | - | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 操作时间 |

**索引：** `idx_ccl_scope(change_scope, created_at)`；`idx_ccl_target(target_id)`；`idx_ccl_operator(operator_id, created_at)`；`idx_ccl_adjust(adjust_id)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 10 年。

### 06.24 表：`md_charge_sync_log`（同步日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| event_id | VARCHAR(64) | N | - | 事件 ID |
| event_type | VARCHAR(64) | N | - | mdm.charge.changed 等 |
| object_type | VARCHAR(32) | N | - | 对象类型 |
| object_code | VARCHAR(32) | Y | NULL | 对象编码 |
| subscriber | VARCHAR(32) | N | - | 订阅方（M04/M10/M16/...） |
| deliver_mode | VARCHAR(16) | N | 'MQ' | MQ/HTTP/REDIS |
| payload | JSON | Y | NULL | 消息体 |
| sync_status | VARCHAR(16) | N | 'PENDING' | PENDING/SUCCESS/FAILED/IGNORED |
| retry_count | INT | N | 0 | 重试次数 |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| affected_count | INT | N | 0 | 影响记录数 |
| cost_ms | INT | Y | NULL | 耗时 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| finished_at | DATETIME | Y | NULL | 完成时间 |

**索引：** `uk_csl_event_sub(event_id, subscriber)`；`idx_csl_status(sync_status, created_at)`；`idx_csl_subscriber(subscriber, sync_status)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 1 年。

### 06.25 表：`md_charge_code_seq`（编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| seq_type | VARCHAR(32) | N | - | CHARGE_ITEM/PRICE_LIST/PRICE_ADJUST/DISCOUNT/COMBO |
| category_code | VARCHAR(16) | N | '' | 分类码 |
| prefix | VARCHAR(16) | N | - | 前缀 |
| period_key | VARCHAR(16) | N | '' | 周期键（yyyyMM/空） |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 5 | 序号位数 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_cs_seq(seq_type, category_code, period_key)` 唯一。

### 06.26 表：`md_price_cache_task`（价格缓存刷新任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| task_no | VARCHAR(32) | N | - | 任务号 PCT+日期+流水 |
| trigger_type | VARCHAR(32) | N | - | PRICE_CHANGE/PRICE_LIST_CHANGE/FULL/MANUAL |
| trigger_source | VARCHAR(128) | Y | NULL | 触发源 |
| affected_item_count | INT | N | 0 | 影响项目数 |
| affected_price_list_ids | VARCHAR(1000) | Y | NULL | 受影响价表 |
| task_status | VARCHAR(16) | N | 'PENDING' | PENDING/RUNNING/SUCCESS/FAILED |
| success_count | INT | N | 0 | 成功数 |
| fail_count | INT | N | 0 | 失败数 |
| started_at | DATETIME | Y | NULL | 开始时间 |
| finished_at | DATETIME | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_pct_no(task_no)` 唯一；`idx_pct_status(task_status)`。

### 06.27 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/charge.py
"""收费与价格主数据 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, DECIMAL,
    JSON, Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class ChargeItem(Base, TimestampMixin, SoftDeleteMixin):
    """收费项目主表"""
    __tablename__ = "md_charge_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ---------- 标识 ----------
    code: Mapped[str] = mapped_column(String(32), nullable=False, comment="收费编码")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="项目名称")
    short_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="简称")
    english_name: Mapped[Optional[str]] = mapped_column(String(255))
    pinyin_code: Mapped[str] = mapped_column(String(32), nullable=False)
    pinyin_short: Mapped[str] = mapped_column(String(32), nullable=False)
    wb_code: Mapped[Optional[str]] = mapped_column(String(32))

    # ---------- 分类 ----------
    charge_class: Mapped[str] = mapped_column(String(32), nullable=False)
    sub_class: Mapped[Optional[str]] = mapped_column(String(32))
    account_class: Mapped[Optional[str]] = mapped_column(String(64))
    income_subject: Mapped[Optional[str]] = mapped_column(String(64))
    cost_subject: Mapped[Optional[str]] = mapped_column(String(64))
    finance_category: Mapped[Optional[str]] = mapped_column(String(32))

    # ---------- 物价信息 ----------
    spec: Mapped[Optional[str]] = mapped_column(String(128))
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    price_code: Mapped[Optional[str]] = mapped_column(String(32), comment="物价编码")
    item_content: Mapped[Optional[str]] = mapped_column(Text, comment="项目内涵")
    exclude_content: Mapped[Optional[str]] = mapped_column(Text)
    instruction: Mapped[Optional[str]] = mapped_column(Text)

    # ---------- 计价 ----------
    pricing_mode: Mapped[str] = mapped_column(String(32), default="FIXED", nullable=False)
    standard_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    current_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    max_retail_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    min_retail_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    charge_by_eye: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    allow_split_qty: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    default_qty: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=1, nullable=False)
    min_qty: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    max_qty: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    qty_precision: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 折扣 ----------
    allow_discount: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    max_discount_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    min_discount_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    discount_need_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 退费 ----------
    allow_refund: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    refund_need_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    refund_window_hours: Mapped[Optional[int]] = mapped_column(Integer)
    refund_ratio: Mapped[Decimal] = mapped_column(DECIMAL(7, 4), default=100, nullable=False)

    # ---------- 积分 ----------
    allow_points: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    points_ratio: Mapped[Decimal] = mapped_column(DECIMAL(6, 2), default=1.0, nullable=False)

    # ---------- 执行 ----------
    default_dept_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exec_dept_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    need_apply: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    link_order: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    link_material: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    material_ids: Mapped[Optional[str]] = mapped_column(String(1000))

    # ---------- 核算 ----------
    dept_accounting: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    account_belong: Mapped[Optional[str]] = mapped_column(String(32))
    share_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))

    # ---------- 医保（预留） ----------
    insurance_code: Mapped[Optional[str]] = mapped_column(String(64))
    insurance_class: Mapped[str] = mapped_column(String(16), default="NA", nullable=False)
    self_pay_ratio: Mapped[Decimal] = mapped_column(DECIMAL(7, 4), default=100, nullable=False)
    commercial_insurance_code: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- 收费界面 ----------
    is_common: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    hotkey: Mapped[Optional[str]] = mapped_column(String(16))
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    is_active_for_new: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)

    # ---------- 状态 ----------
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    ext_json: Mapped[Optional[dict]] = mapped_column(JSON)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    # ---------- 关系 ----------
    ext: Mapped[Optional["ChargeItemExt"]] = relationship(
        back_populates="charge_item", uselist=False, lazy="selectin"
    )
    aliases: Mapped[List["ChargeItemAlias"]] = relationship(
        back_populates="charge_item", lazy="selectin"
    )
    relations: Mapped[List["ChargeItemRel"]] = relationship(
        back_populates="charge_item", lazy="selectin"
    )
    pricing_rules: Mapped[List["ChargeItemPricingRule"]] = relationship(
        back_populates="charge_item", lazy="selectin"
    )
    fields: Mapped[List["ChargeItemField"]] = relationship(
        back_populates="charge_item", lazy="selectin"
    )
    price_items: Mapped[List["PriceItem"]] = relationship(
        back_populates="charge_item", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("code", "deleted", name="uk_ci_code"),
        UniqueConstraint("hotkey", "deleted", name="uk_ci_hotkey"),
        Index("idx_ci_name", "name"),
        Index("idx_ci_pinyin", "pinyin_code", "pinyin_short"),
        Index("idx_ci_class", "charge_class"),
        Index("idx_ci_dept", "default_dept_id"),
        Index("idx_ci_common", "is_common", "status"),
        Index("idx_ci_status", "status", "audit_status"),
        Index("idx_ci_updated", "updated_at"),
        {"comment": "收费项目主表"},
    )

    # ---------- 领域方法 ----------
    @property
    def is_by_eye(self) -> bool:
        return self.pricing_mode == "BY_EYE" or bool(self.charge_by_eye)

    def price_for(self, mode: str = "FIXED", qty: Decimal = Decimal("1")) -> Decimal:
        """按计价方式计算金额（不含折扣与优惠）"""
        base = self.current_price or self.standard_price
        if mode == "BY_QTY":
            return (base * qty).quantize(Decimal("0.01"))
        if mode == "BY_EYE":
            return (base * qty).quantize(Decimal("0.01"))
        if mode == "BY_DAY":
            return (base * qty).quantize(Decimal("0.01"))
        return base.quantize(Decimal("0.01"))

    def min_discount_price(self) -> Optional[Decimal]:
        """最低可打折后的价格"""
        if not self.allow_discount or self.min_discount_rate is None:
            return None
        return (self.current_price * self.min_discount_rate / 100).quantize(Decimal("0.01"))

    def is_refundable(self, charge_time: Optional[datetime] = None) -> bool:
        """是否在退费窗口内"""
        if not self.allow_refund:
            return False
        if not self.refund_window_hours:
            return True
        if charge_time is None:
            return True
        return (datetime.now() - charge_time).total_seconds() <= self.refund_window_hours * 3600

    def to_snapshot(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "charge_class": self.charge_class,
            "pricing_mode": self.pricing_mode,
            "standard_price": str(self.standard_price),
            "current_price": str(self.current_price),
            "unit": self.unit,
            "status": self.status,
            "version": self.version,
        }


class PriceList(Base, TimestampMixin, SoftDeleteMixin):
    """价表"""
    __tablename__ = "md_price_list"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    price_type: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    apply_object: Mapped[Optional[str]] = mapped_column(String(64))
    apply_dept_ids: Mapped[Optional[str]] = mapped_column(String(2000))
    apply_member_levels: Mapped[Optional[str]] = mapped_column(String(500))
    apply_patient_types: Mapped[Optional[str]] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(8), default="CNY", nullable=False)
    default_markup_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    is_default: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    items: Mapped[List["PriceItem"]] = relationship(
        back_populates="price_list", lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("code", "deleted", name="uk_pl_code"),
        Index("idx_pl_type", "price_type"),
        Index("idx_pl_priority", "priority", "status"),
        Index("idx_pl_default", "is_default", "status"),
        {"comment": "价表"},
    )

    @property
    def is_active(self) -> bool:
        today = date.today()
        if self.status != 1 or self.deleted:
            return False
        if self.effective_date > today:
            return False
        if self.expire_date and self.expire_date < today:
            return False
        return True


class PriceItem(Base, TimestampMixin, SoftDeleteMixin):
    """价表明细（版本化）"""
    __tablename__ = "md_price_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    price_list_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_list_code: Mapped[str] = mapped_column(String(32), nullable=False)
    charge_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    charge_item_code: Mapped[str] = mapped_column(String(32), nullable=False)
    original_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    markup_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    discount_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    max_retail_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    min_retail_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    cost_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    is_current: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    adjust_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(16), default="ENABLED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    price_list: Mapped["PriceList"] = relationship(back_populates="items")
    charge_item: Mapped["ChargeItem"] = relationship(back_populates="price_items")

    __table_args__ = (
        UniqueConstraint(
            "price_list_id", "charge_item_id", "effective_date", "deleted",
            name="uk_pi_list_item",
        ),
        Index("idx_pi_item", "charge_item_id"),
        Index("idx_pi_current", "price_list_id", "charge_item_id", "is_current"),
        Index("idx_pi_effective", "effective_date", "expire_date"),
        {"comment": "价表明细"},
    )

    def is_effective_at(self, biz_time: datetime) -> bool:
        d = biz_time.date() if isinstance(biz_time, datetime) else biz_time
        if d < self.effective_date:
            return False
        if self.expire_date and d > self.expire_date:
            return False
        return True


class PriceHistory(Base):
    """价格历史（永久保留，不可修改）"""
    __tablename__ = "md_price_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    object_code: Mapped[str] = mapped_column(String(32), nullable=False)
    object_name: Mapped[Optional[str]] = mapped_column(String(200))
    price_list_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    price_list_code: Mapped[Optional[str]] = mapped_column(String(32))
    price_type: Mapped[Optional[str]] = mapped_column(String(32))
    price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    cost_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    max_retail_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    adjust_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    adjust_reason: Mapped[Optional[str]] = mapped_column(String(500))
    adjust_doc_no: Mapped[Optional[str]] = mapped_column(String(128))
    price_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_ph_object", "object_type", "object_id", "effective_date"),
        Index("idx_ph_code", "object_code"),
        Index("idx_ph_effective", "effective_date"),
        Index("idx_ph_current", "object_type", "object_id", "expire_date"),
        {"comment": "价格历史"},
    )


class PriceAdjust(Base, TimestampMixin, SoftDeleteMixin):
    """调价单"""
    __tablename__ = "md_price_adjust"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    adjust_type: Mapped[str] = mapped_column(String(32), nullable=False)
    adjust_mode: Mapped[str] = mapped_column(String(32), default="MANUAL", nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    policy_ref: Mapped[Optional[str]] = mapped_column(String(128))
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    apply_scope: Mapped[Optional[str]] = mapped_column(String(32))
    item_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_old_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(14, 4))
    total_new_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(14, 4))
    change_rate_avg: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    attachment_ids: Mapped[Optional[str]] = mapped_column(String(500))
    approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    approve_status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    current_node: Mapped[Optional[str]] = mapped_column(String(64))
    current_approver_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    approve_chain: Mapped[Optional[str]] = mapped_column(String(1000))
    approve_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    approve_opinion: Mapped[Optional[str]] = mapped_column(String(500))
    effect_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(500))
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    details: Mapped[List["PriceAdjustDetail"]] = relationship(
        back_populates="adjust", lazy="selectin",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("code", "deleted", name="uk_pa_code"),
        Index("idx_pa_status", "approve_status"),
        Index("idx_pa_effective", "effective_date", "approve_status"),
        Index("idx_pa_type", "adjust_type"),
        {"comment": "调价单"},
    )


class PriceAdjustDetail(Base):
    """调价明细"""
    __tablename__ = "md_price_adjust_detail"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    adjust_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    adjust_code: Mapped[str] = mapped_column(String(32), nullable=False)
    object_type: Mapped[str] = mapped_column(String(32), nullable=False)
    object_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    object_code: Mapped[str] = mapped_column(String(32), nullable=False)
    object_name: Mapped[str] = mapped_column(String(200), nullable=False)
    price_list_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    old_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    new_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 4), default=0, nullable=False)
    change_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(12, 4))
    change_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(7, 4))
    is_over_limit: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16), default="VALID", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    adjust: Mapped["PriceAdjust"] = relationship(back_populates="details")

    __table_args__ = (
        Index("idx_pad_adjust", "adjust_id"),
        Index("idx_pad_object", "object_type", "object_id"),
        {"comment": "调价明细"},
    )
```

### 06.28 Pydantic Schema 定义

```python
# app/schemas/mdm/charge.py
"""收费与价格主数据 Pydantic Schema"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==================== 公共 ====================
class ChargeItemAliasSchema(BaseModel):
    id: Optional[int] = None
    alias_name: str = Field(..., max_length=200)
    alias_type: Literal["CLINICAL", "OFFICIAL", "HISTORICAL", "ABBREVIATION"] = "CLINICAL"
    sort_no: int = 999


class ChargeItemRelSchema(BaseModel):
    id: Optional[int] = None
    rel_object_type: Literal["EXAM", "OPERATION", "DRUG", "MATERIAL", "OPTICAL", "LAB"]
    rel_object_id: int
    rel_object_code: Optional[str] = None
    rel_type: Literal["PRIMARY", "SECONDARY", "BUNDLED"] = "PRIMARY"
    qty_factor: Decimal = Field(Decimal("1"), gt=0)
    price_source: Literal["FIXED", "OBJECT", "PRICE_LIST"] = "FIXED"
    auto_charge: bool = True
    charge_scene: Optional[str] = None
    is_default: bool = False


class PricingRuleSchema(BaseModel):
    id: Optional[int] = None
    rule_type: Literal[
        "TIERED", "BY_EYE", "BY_PART", "BY_AREA", "EXTRA", "SURCHARGE"
    ]
    rule_name: Optional[str] = Field(None, max_length=128)
    priority: int = 999
    min_qty: Optional[Decimal] = Field(None, ge=0)
    max_qty: Optional[Decimal] = Field(None, ge=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    extra_amount: Optional[Decimal] = Field(None, ge=0)
    extra_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    part_code: Optional[Literal["LEFT", "RIGHT", "BOTH", "BOTH_EYES"]] = None
    part_qty_factor: Optional[Decimal] = Field(None, gt=0)
    condition_json: Optional[dict] = None
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_rule(self):
        if self.rule_type == "TIERED":
            if self.unit_price is None and self.total_price is None:
                raise ValueError("阶梯价规则必须设置单价或固定总价")
            if self.min_qty is not None and self.max_qty is not None and self.min_qty > self.max_qty:
                raise ValueError("阶梯价数量区间起不能大于止")
        if self.rule_type == "BY_EYE" and not self.part_code:
            raise ValueError("按眼别计价必须设置部位编码")
        if self.rule_type in ("EXTRA", "SURCHARGE") and self.extra_amount is None and self.extra_rate is None:
            raise ValueError("附加费规则必须设置附加金额或附加比例")
        return self


class ChargeItemFieldSchema(BaseModel):
    id: Optional[int] = None
    field_key: str = Field(..., max_length=64)
    field_name: str = Field(..., max_length=128)
    field_type: Literal["TEXT", "NUMBER", "SELECT", "DATE", "BOOL"] = "TEXT"
    field_value: Optional[str] = Field(None, max_length=500)
    options_json: Optional[list] = None
    unit: Optional[str] = None
    sort_no: int = 999


# ==================== 收费项目 ====================
class ChargeItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    short_name: Optional[str] = Field(None, max_length=64)
    english_name: Optional[str] = Field(None, max_length=255)
    charge_class: str
    sub_class: Optional[str] = None
    account_class: Optional[str] = Field(None, max_length=64)
    income_subject: Optional[str] = Field(None, max_length=64)
    cost_subject: Optional[str] = Field(None, max_length=64)
    finance_category: Optional[str] = None
    spec: Optional[str] = Field(None, max_length=128)
    unit: str = Field(..., max_length=16)
    price_code: Optional[str] = Field(None, max_length=32)
    item_content: Optional[str] = None
    exclude_content: Optional[str] = None
    instruction: Optional[str] = None
    pricing_mode: Literal[
        "FIXED", "BY_EYE", "BY_QTY", "BY_DAY", "BY_HOUR",
        "BY_AREA", "BY_PART", "TIERED", "COMBO", "FREE",
    ] = "FIXED"
    standard_price: Decimal = Field(Decimal("0"), ge=0, decimal_places=4)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    max_retail_price: Optional[Decimal] = Field(None, ge=0)
    min_retail_price: Optional[Decimal] = Field(None, ge=0)
    charge_by_eye: bool = False
    allow_split_qty: bool = True
    default_qty: Decimal = Field(Decimal("1"), gt=0)
    min_qty: Optional[Decimal] = Field(None, ge=0)
    max_qty: Optional[Decimal] = Field(None, ge=0)
    qty_precision: int = Field(0, ge=0, le=2)
    allow_discount: bool = True
    max_discount_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="最高折扣率(%)")
    min_discount_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_need_approve: bool = False
    allow_refund: bool = True
    refund_need_approve: bool = False
    refund_window_hours: Optional[int] = Field(None, ge=0)
    refund_ratio: Decimal = Field(Decimal("100"), ge=0, le=100)
    allow_points: bool = True
    points_ratio: Decimal = Field(Decimal("1.0"), ge=0, le=10)
    default_dept_id: int
    exec_dept_ids: Optional[List[int]] = None
    need_apply: bool = False
    link_order: bool = True
    link_material: bool = False
    material_ids: Optional[List[int]] = None
    dept_accounting: bool = True
    account_belong: Optional[Literal["ORDER_DEPT", "EXEC_DEPT", "SHARE"]] = None
    share_ratio: Optional[Decimal] = Field(None, ge=0, le=100)
    insurance_code: Optional[str] = Field(None, max_length=64)
    insurance_class: Literal["A", "B", "C", "NA"] = "NA"
    self_pay_ratio: Decimal = Field(Decimal("100"), ge=0, le=100)
    is_common: bool = False
    hotkey: Optional[str] = Field(None, max_length=16)
    sort_no: int = 999
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_item(self):
        # 折扣率顺序
        if (self.max_discount_rate is not None and self.min_discount_rate is not None
                and self.min_discount_rate > self.max_discount_rate):
            raise ValueError("最低折扣率不能大于最高折扣率")
        # 限价顺序
        if (self.max_retail_price is not None and self.standard_price > self.max_retail_price):
            raise ValueError(f"标准价 {self.standard_price} 超过最高零售限价 {self.max_retail_price}")
        if (self.min_retail_price is not None and self.standard_price < self.min_retail_price):
            raise ValueError(f"标准价 {self.standard_price} 低于最低零售限价 {self.min_retail_price}")
        # 数量区间
        if self.min_qty is not None and self.max_qty is not None and self.min_qty > self.max_qty:
            raise ValueError("最小计价数量不能大于最大计价数量")
        # 按眼别一致性
        if self.pricing_mode == "BY_EYE" and not self.charge_by_eye:
            self.charge_by_eye = True  # 自动纠正
        # 分成比例
        if self.account_belong == "SHARE" and self.share_ratio is None:
            raise ValueError("核算归属为分成时必须填写分成比例")
        # 日期
        if self.effective_date and self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("失效日期必须晚于生效日期")
        return self


class ChargeItemCreate(ChargeItemBase):
    code: Optional[str] = Field(None, description="为空则自动生成")
    aliases: List[ChargeItemAliasSchema] = []
    relations: List[ChargeItemRelSchema] = []
    pricing_rules: List[PricingRuleSchema] = []
    fields: List[ChargeItemFieldSchema] = []
    ext: Optional[dict] = None
    prices: List["PriceItemSchema"] = []
    change_reason: Optional[str] = Field(None, max_length=500)


class ChargeItemUpdate(ChargeItemBase):
    version: int = Field(..., ge=0)
    aliases: Optional[List[ChargeItemAliasSchema]] = None
    relations: Optional[List[ChargeItemRelSchema]] = None
    pricing_rules: Optional[List[PricingRuleSchema]] = None
    fields: Optional[List[ChargeItemFieldSchema]] = None
    ext: Optional[dict] = None
    change_reason: Optional[str] = Field(None, max_length=500)


class ChargeItemListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    short_name: str
    spec: Optional[str] = None
    charge_class: str
    charge_class_name: Optional[str] = None
    sub_class: Optional[str] = None
    unit: str
    pricing_mode: str
    pricing_mode_name: Optional[str] = None
    standard_price: Decimal
    current_price: Decimal
    max_retail_price: Optional[Decimal] = None
    allow_discount: bool = True
    allow_refund: bool = True
    default_dept_id: int
    default_dept_name: Optional[str] = None
    is_common: bool = False
    hotkey: Optional[str] = None
    status: str
    audit_status: str
    effective_date: Optional[date] = None
    updated_at: Optional[datetime] = None


class ChargeItemDetail(ChargeItemListItem):
    english_name: Optional[str] = None
    account_class: Optional[str] = None
    income_subject: Optional[str] = None
    cost_subject: Optional[str] = None
    finance_category: Optional[str] = None
    price_code: Optional[str] = None
    item_content: Optional[str] = None
    exclude_content: Optional[str] = None
    instruction: Optional[str] = None
    cost_price: Optional[Decimal] = None
    min_retail_price: Optional[Decimal] = None
    charge_by_eye: bool = False
    allow_split_qty: bool = True
    default_qty: Decimal = Decimal("1")
    min_qty: Optional[Decimal] = None
    max_qty: Optional[Decimal] = None
    qty_precision: int = 0
    max_discount_rate: Optional[Decimal] = None
    min_discount_rate: Optional[Decimal] = None
    discount_need_approve: bool = False
    refund_need_approve: bool = False
    refund_window_hours: Optional[int] = None
    refund_ratio: Decimal = Decimal("100")
    allow_points: bool = True
    points_ratio: Decimal = Decimal("1.0")
    exec_dept_ids: Optional[List[int]] = None
    need_apply: bool = False
    link_order: bool = True
    link_material: bool = False
    material_ids: Optional[List[int]] = None
    dept_accounting: bool = True
    account_belong: Optional[str] = None
    share_ratio: Optional[Decimal] = None
    insurance_code: Optional[str] = None
    insurance_class: str = "NA"
    self_pay_ratio: Decimal = Decimal("100")
    sort_no: int = 999
    version: int = 0
    expire_date: Optional[date] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    # 子表
    aliases: List[ChargeItemAliasSchema] = []
    relations: List[ChargeItemRelSchema] = []
    pricing_rules: List[PricingRuleSchema] = []
    fields: List[ChargeItemFieldSchema] = []
    ext: Optional[dict] = None
    prices: List["PriceItemSchema"] = []


# ==================== 价表 ====================
class PriceListBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    price_type: Literal["STANDARD", "MEMBER", "INSURANCE", "INTERNAL", "DEPT", "ACTIVITY"]
    priority: int = Field(100, ge=1, le=999)
    apply_object: Optional[Literal["ALL", "DEPT", "MEMBER", "INSURANCE"]] = None
    apply_dept_ids: Optional[List[int]] = None
    apply_member_levels: Optional[List[str]] = None
    apply_patient_types: Optional[List[str]] = None
    currency: str = "CNY"
    default_markup_rate: Optional[Decimal] = Field(None, ge=-100, le=1000)
    is_default: bool = False
    effective_date: date
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_list(self):
        if self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("失效日期必须晚于生效日期")
        if self.price_type == "DEPT" and not self.apply_dept_ids:
            raise ValueError("科室差异价表必须指定适用科室")
        if self.price_type == "MEMBER" and not self.apply_member_levels:
            raise ValueError("会员价表必须指定适用会员等级")
        if self.apply_object == "DEPT" and not self.apply_dept_ids:
            raise ValueError("适用对象为科室时必须指定科室")
        return self


class PriceListCreate(PriceListBase):
    code: Optional[str] = None


class PriceListUpdate(PriceListBase):
    version: Optional[int] = None


class PriceItemSchema(BaseModel):
    id: Optional[int] = None
    price_list_id: Optional[int] = None
    charge_item_id: int
    charge_item_code: Optional[str] = None
    original_price: Decimal = Field(Decimal("0"), ge=0, decimal_places=4)
    price: Decimal = Field(..., ge=0, decimal_places=4)
    markup_rate: Optional[Decimal] = Field(None, ge=-100, le=1000)
    max_retail_price: Optional[Decimal] = Field(None, ge=0)
    min_retail_price: Optional[Decimal] = Field(None, ge=0)
    effective_date: date
    expire_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_price(self):
        if self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("价格失效日期必须晚于生效日期")
        if self.max_retail_price is not None and self.price > self.max_retail_price:
            raise ValueError(f"价格 {self.price} 超过最高零售限价 {self.max_retail_price}")
        if self.min_retail_price is not None and self.price < self.min_retail_price:
            raise ValueError(f"价格 {self.price} 低于最低零售限价 {self.min_retail_price}")
        return self


# ==================== 调价 ====================
class PriceAdjustDetailSchema(BaseModel):
    object_type: Literal["CHARGE_ITEM", "PRICE_ITEM", "DRUG", "MATERIAL", "OPTICAL"]
    object_id: int
    object_code: Optional[str] = None
    object_name: Optional[str] = None
    price_list_id: Optional[int] = None
    old_price: Optional[Decimal] = None
    new_price: Decimal = Field(..., ge=0, decimal_places=4)
    remark: Optional[str] = Field(None, max_length=255)


class PriceAdjustCreate(BaseModel):
    adjust_type: Literal["CHARGE", "PRICE_LIST", "DRUG", "MATERIAL", "OPTICAL", "BATCH"]
    adjust_mode: Literal["MANUAL", "RATE", "AMOUNT", "UNIFIED", "IMPORT"] = "MANUAL"
    reason: str = Field(..., min_length=5, max_length=500)
    policy_ref: Optional[str] = Field(None, max_length=128)
    effective_date: date
    apply_scope: Optional[str] = None
    attachment_ids: Optional[List[int]] = None
    details: List[PriceAdjustDetailSchema] = Field(..., min_length=1)
    change_rate_threshold: Optional[Decimal] = Field(None, ge=0, le=1000,
                                                     description="涨跌幅告警阈值(%)")

    @model_validator(mode="after")
    def validate_adjust(self):
        if not self.details:
            raise ValueError("调价单必须包含至少一条明细")
        for d in self.details:
            if d.old_price is not None and d.old_price == d.new_price:
                raise ValueError(f"项目 {d.object_name or d.object_code} 的新旧价格相同，无需调整")
        # 重复校验
        keys = [(d.object_type, d.object_id, d.price_list_id) for d in self.details]
        if len(keys) != len(set(keys)):
            raise ValueError("调价明细中存在重复的项目")
        return self


# ==================== 优惠方案 ====================
class DiscountPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    policy_type: Literal["DISCOUNT", "FULL_REDUCE", "PACKAGE", "GIFT", "MEMBER", "ACTIVITY"]
    apply_scene: List[str] = Field(..., min_length=1)
    apply_charge_classes: Optional[List[str]] = None
    apply_object_scope: Literal["ALL", "INCLUDE", "EXCLUDE"] = "ALL"
    discount_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    full_amount: Optional[Decimal] = Field(None, ge=0)
    reduce_amount: Optional[Decimal] = Field(None, ge=0)
    package_price: Optional[Decimal] = Field(None, ge=0)
    gift_desc: Optional[str] = Field(None, max_length=500)
    apply_member_levels: Optional[List[str]] = None
    apply_patient_tags: Optional[List[str]] = None
    apply_dept_ids: Optional[List[int]] = None
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_reduce_amount: Optional[Decimal] = Field(None, ge=0)
    effective_date: date
    expire_date: date
    available_time: Optional[str] = Field(None, max_length=255)
    available_weekdays: Optional[str] = Field(None, max_length=32)
    limit_per_person: Optional[int] = Field(None, ge=1)
    limit_per_day: Optional[int] = Field(None, ge=1)
    total_quota: Optional[int] = Field(None, ge=1)
    allow_stack: bool = False
    stack_priority: int = 100
    need_approve: bool = False
    approve_threshold: Optional[Decimal] = Field(None, ge=0, le=100)
    min_discount_rate: Decimal = Field(Decimal("100"), ge=0, le=100)
    is_auto_apply: bool = False
    items: List[dict] = []
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_policy(self):
        # 日期
        if self.expire_date < self.effective_date:
            raise ValueError("失效日期不能早于生效日期")
        # 按类型必填校验
        if self.policy_type in ("DISCOUNT", "MEMBER", "ACTIVITY"):
            if self.discount_rate is None:
                raise ValueError("折扣类方案必须设置折扣率")
        if self.policy_type == "FULL_REDUCE":
            if self.full_amount is None or self.reduce_amount is None:
                raise ValueError("满减类方案必须设置门槛金额与减免金额")
            if self.reduce_amount > self.full_amount:
                raise ValueError("减免金额不能大于门槛金额")
        if self.policy_type == "PACKAGE" and self.package_price is None:
            raise ValueError("套餐类方案必须设置套餐价")
        if self.policy_type == "GIFT" and not self.gift_desc:
            raise ValueError("买赠类方案必须填写赠品说明")
        # 折扣底线
        if self.discount_rate is not None and self.discount_rate < self.min_discount_rate:
            raise ValueError(
                f"折扣率 {self.discount_rate}% 低于最低折扣底线 {self.min_discount_rate}%"
            )
        # 审批阈值
        if self.need_approve and self.approve_threshold is None and self.discount_rate is None:
            raise ValueError("需要审批时请设置审批阈值")
        return self


class DiscountPolicyCreate(DiscountPolicyBase):
    code: Optional[str] = None


class DiscountPolicyUpdate(DiscountPolicyBase):
    version: Optional[int] = None


# ==================== 套餐 ====================
class ComboDetailSchema(BaseModel):
    charge_item_id: int
    charge_item_code: Optional[str] = None
    default_qty: Decimal = Field(Decimal("1"), gt=0)
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    package_amount: Optional[Decimal] = Field(None, ge=0)
    is_optional: bool = False
    is_eye_side: bool = False
    group_name: Optional[str] = Field(None, max_length=64)
    sort_no: int = 999


class ComboCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    short_name: Optional[str] = Field(None, max_length=64)
    combo_type: Literal["EXAM", "OPERATION", "OPTICAL", "PHYSICAL", "CUSTOM"]
    apply_dept_ids: Optional[List[int]] = None
    apply_patient_types: Optional[List[str]] = None
    is_eye_side_split: bool = False
    package_price: Decimal = Field(..., ge=0)
    valid_days: Optional[int] = Field(None, ge=0)
    allow_partial_refund: bool = False
    details: List[ComboDetailSchema] = Field(..., min_length=1)
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_combo(self):
        if not self.details:
            raise ValueError("套餐必须包含至少一个收费项目")
        ids = [d.charge_item_id for d in self.details]
        if len(ids) != len(set(ids)):
            raise ValueError("套餐明细中存在重复的收费项目")
        return self


# ==================== 支付方式 ====================
class PaymentMethodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    pay_category: Literal["CASH", "CARD", "SCAN", "STORED", "INSURANCE", "OTHER"]
    need_change: bool = False
    need_card: bool = False
    need_third_party: bool = False
    need_auth_code: bool = False
    channel_code: Optional[str] = Field(None, max_length=64)
    channel_name: Optional[str] = Field(None, max_length=64)
    need_reconcile: bool = False
    reconcile_type: Optional[Literal["API", "FILE", "MANUAL"]] = None
    reconcile_file_format: Optional[str] = Field(None, max_length=128)
    fee_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    settlement_days: int = Field(0, ge=0, le=365)
    account_subject: Optional[str] = Field(None, max_length=64)
    apply_scene: Optional[List[str]] = None
    is_default: bool = False
    sort_no: int = 999

    @model_validator(mode="after")
    def validate_payment(self):
        if self.need_reconcile and not self.reconcile_type:
            raise ValueError("需要对账的支付方式必须设置对账类型")
        if self.pay_category == "SCAN" and not self.channel_code:
            raise ValueError("扫码支付必须设置渠道编码")
        return self


class PaymentMethodCreate(PaymentMethodBase):
    code: Optional[str] = None


class PaymentMethodUpdate(PaymentMethodBase):
    pass


# ==================== 退费规则 ====================
class RefundPolicyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    apply_charge_classes: Optional[List[str]] = None
    apply_scene: Optional[List[str]] = None
    allow_refund: bool = True
    refund_window_type: Literal["SAME_DAY", "WITHIN_HOURS", "WITHIN_DAYS", "UNLIMITED"] = "SAME_DAY"
    refund_window_hours: Optional[int] = Field(None, ge=1)
    refund_ratio: Decimal = Field(Decimal("100"), ge=0, le=100)
    fee_ratio: Decimal = Field(Decimal("0"), ge=0, le=100)
    allow_partial: bool = True
    allow_executed_refund: bool = False
    allow_dispensed_refund: bool = False
    need_approve: bool = False
    approve_threshold_amount: Optional[Decimal] = Field(None, ge=0)
    approve_threshold_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    rollback_points: bool = True
    refund_method: Literal["ORIGINAL", "ANY", "CASH"] = "ORIGINAL"
    allow_negative_stored: bool = False
    priority: int = 100
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_refund(self):
        if self.refund_window_type == "WITHIN_HOURS" and not self.refund_window_hours:
            raise ValueError("按小时限制退费窗口时必须设置小时数")
        if self.refund_ratio + self.fee_ratio > 100:
            raise ValueError("退费比例与手续费比例之和不能超过 100%")
        return self


class RefundPolicyCreate(RefundPolicyBase):
    code: Optional[str] = None


class RefundPolicyUpdate(RefundPolicyBase):
    pass


# ==================== 取价/试算（内部契约） ====================
class EffectivePriceQuery(BaseModel):
    charge_item_codes: List[str] = Field(..., min_length=1, max_length=500)
    biz_time: str = Field(..., description="业务发生时间 yyyy-MM-ddTHH:mm:ss")
    price_list_code: Optional[str] = None
    patient_id: Optional[int] = None
    dept_id: Optional[int] = None
    member_level: Optional[str] = None


class EffectivePriceItem(BaseModel):
    charge_item_code: str
    charge_item_name: str
    price_list_code: str
    price: Decimal
    original_price: Decimal
    unit: str
    effective_date: date
    expire_date: Optional[date] = None
    price_id: int


class DiscountCalcRequest(BaseModel):
    """优惠试算请求"""
    charge_items: List[dict] = Field(..., description="[{code, qty, amount, eye_side}]")
    patient_id: Optional[int] = None
    member_level: Optional[str] = None
    dept_id: Optional[int] = None
    discount_policy_codes: List[str] = []
    manual_discount_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    biz_time: Optional[str] = None


class DiscountCalcResult(BaseModel):
    original_amount: Decimal
    item_details: List[dict]
    policy_details: List[dict]
    discount_amount: Decimal
    final_amount: Decimal
    need_approve: bool = False
    warnings: List[str] = []


# ==================== 查询 ====================
class ChargeItemQuery(BaseModel):
    keyword: Optional[str] = None
    charge_class: Optional[List[str]] = None
    sub_class: Optional[str] = None
    pricing_mode: Optional[str] = None
    default_dept_id: Optional[int] = None
    allow_discount: Optional[bool] = None
    allow_refund: Optional[bool] = None
    is_common: Optional[bool] = None
    status: Optional[List[str]] = None
    audit_status: Optional[str] = None
    price_min: Optional[Decimal] = None
    price_max: Optional[Decimal] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    sort_by: str = "sort_no"
    sort_order: Literal["asc", "desc"] = "asc"


# 前向引用解析
ChargeItemCreate.model_rebuild()
ChargeItemDetail.model_rebuild()
```

---

---

## 07. 手术数据结构

> **来源：** [手术详细设计](M01_主数据管理MDM_07_手术_详细设计.md) · 第 4 章
> **主数据域：** 临床域（`CLI`） · **表数：** 22

**本模块表清单：**

| 序号 | 表名 | 中文名 |
|---|---|---|
| 07.2 | `md_operation` | 手术项目主表 |
| 07.3 | `md_operation_ext` | 手术项目扩展表 |
| 07.4 | `md_operation_alias` | 手术项目别名表 |
| 07.5 | `md_operation_anesthesia_rel` | 手术-麻醉关联表 |
| 07.6 | `md_operation_prepare_rule` | 术前准备规则表 |
| 07.7 | `md_operation_prepare_item` | 术前准备明细表 |
| 07.8 | `md_operation_exam_item_rel` | 术前检查关联表 |
| 07.9 | `md_operation_lab_item_rel` | 术前检验关联表 |
| 07.10 | `md_operation_material_rel` | 手术-耗材关联表 |
| 07.11 | `md_operation_iol_rel` | 手术-人工晶体关联表 |
| 07.12 | `md_operation_implant` | 植入物手术配置表 |
| 07.13 | `md_operation_staff_auth` | 手术医师授权表 |
| 07.14 | `md_operation_followup_rule` | 术后随访规则表 |
| 07.15 | `md_operation_charge_rel` | 手术收费关联表 |
| 07.16 | `md_operation_template_rel` | 手术模板关联表 |
| 07.17 | `md_anesthesia` | 麻醉方式主表 |
| 07.18 | `md_anesthesia_drug` | 麻醉默认药品表 |
| 07.19 | `md_surgery_level_rule` | 手术分级规则表 |
| 07.20 | `md_operation_change_log` | 变更日志表 |
| 07.21 | `md_operation_sync_log` | 同步日志表 |
| 07.22 | `md_operation_code_seq` | 手术编码序列表 |
| 07.23 | `md_operation_import_task` | 导入任务表 |

---

### 07.1 ER 关系图

```
                    ┌──────────────────────────┐
                    │  md_operation            │
                    │  （手术项目主表）         │
                    └────────────┬─────────────┘
                                 │ 1
        ┌──────────┬─────────┬───┴──────┬──────────┬──────────┬──────────┐
        │ 1:N      │ 1:N     │ 1:1      │ 1:N      │ 1:N      │ 1:N      │
        ▼          ▼         ▼          ▼          ▼          ▼          ▼
┌────────────┐┌─────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│md_operation││..._alias││..._ext   ││..._      ││..._      ││..._      ││..._      │
│_ext        ││         ││          ││anesthesia││prepare_  ││material_ ││exam_     │
│（扩展）     ││（别名）  ││          ││_rel      ││rule      ││rel       ││item_rel  │
└────────────┘└─────────┘└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘
                                            │
                                            │ 1:N
                                            ▼
                                  ┌──────────────────┐
                                  │ md_operation_    │
                                  │ prepare_item     │
                                  │（术前准备明细）   │
                                  └──────────────────┘

        ┌──────────┬─────────┬──────────┬──────────┬──────────┬──────────┐
        │ 1:N      │ 1:N     │ 1:N      │ 1:N      │ 1:N      │ 1:N      │
        ▼          ▼         ▼          ▼          ▼          ▼          ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│..._lab_  ││..._      ││..._      ││..._      ││..._      ││..._      ││..._      │
│item_rel  ││staff_auth││implant   ││iol_rel   ││followup_ ││charge_rel││tpl_rel   │
│          ││（授权）   ││（植入物） ││（晶体）   ││rule      ││（收费）   ││（模板）   │
└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘└──────────┘

        ┌───────────────────────┐      ┌───────────────────────┐
        │ md_anesthesia         │ 1:N  │ md_anesthesia_drug    │
        │ （麻醉方式）           │◄────►│ （默认药品）           │
        └───────────────────────┘      └───────────────────────┘

治理相关：
┌───────────────────────┐  ┌───────────────────────┐
│md_operation_change_log│  │md_operation_sync_log  │
│（变更日志）            │  │（同步日志）            │
└───────────────────────┘  └───────────────────────┘
┌───────────────────────┐  ┌───────────────────────┐
│md_operation_code_seq  │  │md_surgery_level_rule  │
│（编码序列）            │  │（分级规则）            │
└───────────────────────┘  └───────────────────────┘
```

**表清单（共 22 张）：**

| 序号 | 表名 | 中文名 | 说明 | 预估量级 |
|---|---|---|---|---|
| 1 | `md_operation` | 手术项目主表 | 核心 | 1,500 |
| 2 | `md_operation_ext` | 手术项目扩展表 | 1:1 | 1,500 |
| 3 | `md_operation_alias` | 手术项目别名表 | 1:N | 3,000 |
| 4 | `md_operation_anesthesia_rel` | 手术-麻醉关联表 | 1:N | 6,000 |
| 5 | `md_operation_prepare_rule` | 术前准备规则表 | 1:N | 2,000 |
| 6 | `md_operation_prepare_item` | 术前准备明细表 | 1:N | 8,000 |
| 7 | `md_operation_exam_item_rel` | 术前检查关联表 | 1:N | 15,000 |
| 8 | `md_operation_lab_item_rel` | 术前检验关联表 | 1:N | 12,000 |
| 9 | `md_operation_material_rel` | 手术-耗材关联表 | 1:N | 10,000 |
| 10 | `md_operation_iol_rel` | 手术-人工晶体关联表 | 1:N | 5,000 |
| 11 | `md_operation_implant` | 植入物手术配置表 | 1:1 | 600 |
| 12 | `md_operation_staff_auth` | 手术医师授权表 | 1:N | 8,000 |
| 13 | `md_operation_followup_rule` | 术后随访规则表 | 1:1 | 1,500 |
| 14 | `md_operation_charge_rel` | 手术收费关联表 | 1:N | 2,500 |
| 15 | `md_operation_template_rel` | 手术模板关联表 | 1:N | 5,000 |
| 16 | `md_anesthesia` | 麻醉方式主表 | 核心 | 60 |
| 17 | `md_anesthesia_drug` | 麻醉默认药品表 | 1:N | 300 |
| 18 | `md_surgery_level_rule` | 手术分级规则表 | 核心 | 20 |
| 19 | `md_operation_change_log` | 变更日志表 | 审计 | 50,000/年 |
| 20 | `md_operation_sync_log` | 同步日志表 | 运维 | 200,000/年 |
| 21 | `md_operation_code_seq` | 手术编码序列表 | 运维 | 50 |
| 22 | `md_operation_import_task` | 导入任务表 | 运维 | 1,000/年 |

> **说明**：`md_operation`、`md_anesthesia` 在 M01 总文档第 7.7 节已定义基础结构，本子模块在其基础上**扩展字段**并新增其余表，保持向后兼容。

### 07.2 表：`md_operation`（手术项目主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 手术编码 OPR+流水 |
| name | VARCHAR(200) | N | - | 手术名称（规范全称） |
| short_name | VARCHAR(64) | N | - | 手术简称 |
| english_name | VARCHAR(255) | Y | NULL | 英文名 |
| pinyin_code | VARCHAR(32) | N | - | 拼音码 |
| pinyin_short | VARCHAR(32) | N | - | 拼音首字母 |
| wb_code | VARCHAR(32) | Y | NULL | 五笔码 |
| icd9_code | VARCHAR(20) | Y | NULL | ICD-9-CM-3 编码 |
| operation_category | VARCHAR(32) | N | - | 手术类别（3.1.1） |
| surgery_level | VARCHAR(32) | N | - | 手术分级（3.1.3） |
| eye_specialty | VARCHAR(500) | N | - | 眼科亚专科（多选，逗号分隔） |
| body_position | VARCHAR(32) | Y | NULL | 手术体位 |
| laterality_required | TINYINT(1) | N | 1 | 是否需指定眼别 |
| allow_bilateral | TINYINT(1) | N | 0 | 是否可双眼同时手术 |
| is_day_surgery | TINYINT(1) | N | 0 | 是否日间手术 |
| is_outpatient_surgery | TINYINT(1) | N | 0 | 是否门诊手术 |
| is_inpatient_surgery | TINYINT(1) | N | 1 | 是否住院手术 |
| is_emergency | TINYINT(1) | N | 0 | 是否急诊手术 |
| is_minimally_invasive | TINYINT(1) | N | 0 | 是否微创 |
| duration_minutes | INT | N | 60 | 标准手术时长（分钟） |
| duration_minutes_max | INT | Y | NULL | 最长手术时长 |
| anesthesia_duration | INT | Y | NULL | 麻醉时长（分钟） |
| prepare_hours | INT | Y | NULL | 术前准备时长（小时） |
| recovery_minutes | INT | Y | NULL | 术后复苏时长（分钟） |
| room_type_req | VARCHAR(255) | Y | NULL | 手术间类型要求（多选） |
| equipment_ids | VARCHAR(1000) | Y | NULL | 所需设备 |
| is_refractive | TINYINT(1) | N | 0 | 是否屈光手术 |
| refractive_type | VARCHAR(64) | Y | NULL | 屈光术式（3.1.4） |
| need_refractive_record | TINYINT(1) | N | 0 | 需术前屈光档案 |
| need_navigation | TINYINT(1) | N | 0 | 需术中导航 |
| is_implant_surgery | TINYINT(1) | N | 0 | 是否植入物手术 |
| default_implant_types | VARCHAR(255) | Y | NULL | 默认植入物类别 |
| need_followup | TINYINT(1) | N | 1 | 需术后随访 |
| followup_days | VARCHAR(64) | Y | NULL | 随访周期（天，逗号分隔） |
| order_template_id | BIGINT UNSIGNED | Y | NULL | 默认医嘱模板 |
| nursing_template_id | BIGINT UNSIGNED | Y | NULL | 术后护理模板 |
| consent_template_id | BIGINT UNSIGNED | Y | NULL | 手术同意书模板 |
| anesthesia_consent_template_id | BIGINT UNSIGNED | Y | NULL | 麻醉同意书模板 |
| implant_consent_template_id | BIGINT UNSIGNED | Y | NULL | 植入物同意书模板 |
| charge_item_id | BIGINT UNSIGNED | N | - | 手术费收费项目 |
| include_material | TINYINT(1) | N | 1 | 是否含材料费 |
| extra_charge_ids | VARCHAR(1000) | Y | NULL | 加收项目 |
| allow_discount | TINYINT(1) | N | 1 | 是否可打折 |
| cost_subject | VARCHAR(64) | Y | NULL | 成本核算项目 |
| income_subject | VARCHAR(64) | Y | NULL | 收入科目 |
| min_surgery_level | VARCHAR(32) | N | 'LEVEL_1' | 最低手术权限级别 |
| need_chief_approve | TINYINT(1) | N | 0 | 需科主任审批 |
| need_medical_affairs_approve | TINYINT(1) | N | 0 | 需医务科审批 |
| need_director_approve | TINYINT(1) | N | 0 | 需院长审批 |
| auth_scope_type | VARCHAR(16) | N | 'LEVEL' | 授权方式：LEVEL（按级别）/WHITELIST（白名单）/BOTH |
| is_high_risk | TINYINT(1) | N | 0 | 是否高风险手术 |
| risk_desc | VARCHAR(500) | Y | NULL | 风险说明 |
| sort_no | INT | N | 999 | 排序 |
| is_common | TINYINT(1) | N | 0 | 是否常用 |
| hotkey | VARCHAR(16) | Y | NULL | 快捷键 |
| status | VARCHAR(16) | N | 'DRAFT' | 状态：DRAFT/ENABLED/DISABLED |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| effective_date | DATE | Y | NULL | 生效日期 |
| expire_date | DATE | Y | NULL | 失效日期 |
| org_id | BIGINT UNSIGNED | N | 1 | 院区 ID |
| ext_json | JSON | Y | NULL | 扩展字段 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | N | - | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_operation | PRIMARY | id | 主键 |
| uk_op_code | UNIQUE | code, deleted | 编码唯一 |
| uk_op_hotkey | UNIQUE | hotkey, deleted | 快捷键唯一 |
| idx_op_name | NORMAL | name | 名称查询 |
| idx_op_short | NORMAL | short_name | 简称查询 |
| idx_op_pinyin | NORMAL | pinyin_code, pinyin_short | 拼音检索 |
| idx_op_icd9 | NORMAL | icd9_code | ICD-9 编码 |
| idx_op_level | NORMAL | surgery_level | 分级过滤 |
| idx_op_category | NORMAL | operation_category | 类别过滤 |
| idx_op_refractive | NORMAL | is_refractive, status | 屈光手术 |
| idx_op_day | NORMAL | is_day_surgery | 日间手术 |
| idx_op_implant | NORMAL | is_implant_surgery | 植入物手术 |
| idx_op_common | NORMAL | is_common, status | 常用手术 |
| idx_op_status | NORMAL | status, audit_status | 状态过滤 |
| idx_op_updated | NORMAL | updated_at | 增量同步 |
| ft_op_name | FULLTEXT | name, short_name, english_name | 中文分词检索 |

### 07.3 表：`md_operation_ext`（手术项目扩展表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| navigation_type | VARCHAR(64) | Y | NULL | 导航类型（OCT 导航/像差导航） |
| microscope_required | TINYINT(1) | N | 0 | 是否需显微镜 |
| microscope_type | VARCHAR(64) | Y | NULL | 显微镜类型 |
| laser_type | VARCHAR(64) | Y | NULL | 激光类型 |
| photon_type | VARCHAR(32) | Y | NULL | 光子类型 |
| surgical_approach | VARCHAR(32) | Y | NULL | 手术入路（经角膜/经巩膜/经结膜） |
| incision_size | VARCHAR(32) | Y | NULL | 切口尺寸（mm） |
| incision_position | VARCHAR(64) | Y | NULL | 切口位置（透明角膜缘/巩膜） |
| suture_required | TINYINT(1) | N | 0 | 是否需缝合 |
| suture_type | VARCHAR(64) | Y | NULL | 缝线类型 |
| viscoelastic_required | TINYINT(1) | N | 0 | 是否需粘弹剂 |
| peribulbar_required | TINYINT(1) | N | 0 | 是否需球后麻醉 |
| icu_required | TINYINT(1) | N | 0 | 是否需 ICU 监护 |
| observation_hours | INT | Y | NULL | 术后观察时长（小时） |
| bed_required_days | INT | Y | NULL | 预计住院天数 |
| blood_preparation | VARCHAR(32) | Y | NULL | 备血要求（无/备血1单位等） |
| antibiotic_prophylaxis | TINYINT(1) | N | 0 | 是否预防性使用抗菌药物 |
| antibiotic_type | VARCHAR(64) | Y | NULL | 抗菌药物类型 |
| dilate_pupil | TINYINT(1) | N | 0 | 是否需散瞳 |
| constrict_pupil | TINYINT(1) | N | 0 | 是否需缩瞳 |
| mark_eye | TINYINT(1) | N | 1 | 是否需标记术眼 |
| skin_prep | TINYINT(1) | N | 0 | 是否需备皮 |
| consent_required | TINYINT(1) | N | 1 | 是否需知情同意 |
| anesthesia_visit_required | TINYINT(1) | N | 0 | 是否需麻醉访视 |
| surgeon_visit_required | TINYINT(1) | N | 0 | 是否需手术医生访视 |
| family_education | VARCHAR(500) | Y | NULL | 家属宣教要点 |
| post_op_note | VARCHAR(1000) | Y | NULL | 术后注意事项 |
| display_order | INT | Y | NULL | 显示顺序 |
| level_override_reason | VARCHAR(500) | Y | NULL | 分级调整理由 |
| custom_fields | JSON | Y | NULL | 自定义字段值 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ext_op(operation_id, deleted)` 唯一；`idx_ext_icu(icu_required)`。

### 07.4 表：`md_operation_alias`（手术项目别名表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| alias_name | VARCHAR(200) | N | - | 别名 |
| alias_type | VARCHAR(32) | N | 'CLINICAL' | 别名类型：CLINICAL/OFFICIAL/HISTORICAL/ABBREVIATION |
| pinyin_code | VARCHAR(64) | Y | NULL | 别名拼音 |
| pinyin_short | VARCHAR(32) | Y | NULL | 别名首字母 |
| sort_no | INT | N | 999 | 排序 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_alias(op_id, alias_name, deleted)` 唯一；`idx_alias_name(alias_name)`；`idx_alias_pinyin(pinyin_short)`。

### 07.5 表：`md_operation_anesthesia_rel`（手术-麻醉关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| anesthesia_id | BIGINT UNSIGNED | N | - | 麻醉方式 ID |
| anesthesia_code | VARCHAR(32) | N | - | 麻醉编码 |
| anesthesia_name | VARCHAR(64) | Y | NULL | 麻醉名称（冗余） |
| is_default | TINYINT(1) | N | 0 | 是否默认麻醉方式 |
| is_required | TINYINT(1) | N | 0 | 是否必须（不可选其他） |
| priority | INT | N | 999 | 优先级 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_op_anes(operation_id, anesthesia_id, deleted)` 唯一；`idx_anes(anesthesia_id)`；`idx_default(is_default)`。

**约束：** 同一手术仅允许一个 `is_default=1` 的麻醉方式。

### 07.6 表：`md_operation_prepare_rule`（术前准备规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| rule_type | VARCHAR(32) | N | 'GENERAL' | GENERAL（通用）/ANESTHESIA_SPECIFIC（麻醉专用） |
| fasting_required | TINYINT(1) | N | 0 | 是否需禁食 |
| fasting_solid_hours | INT | Y | NULL | 禁食固体时间（小时） |
| fasting_liquid_hours | INT | Y | NULL | 禁清饮时间（小时） |
| fasting_note | VARCHAR(500) | Y | NULL | 禁食说明 |
| skin_prep_required | TINYINT(1) | N | 0 | 是否需备皮 |
| skin_prep_desc | VARCHAR(255) | Y | NULL | 备皮说明 |
| eye_mark_required | TINYINT(1) | N | 1 | 是否需标记术眼 |
| dilate_pupil_required | TINYINT(1) | N | 0 | 是否需散瞳 |
| dilate_drop_type | VARCHAR(64) | Y | NULL | 散瞳药类型 |
| dilate_minutes | INT | Y | NULL | 散瞳提前时间（分钟） |
| antibiotic_prophylaxis | TINYINT(1) | N | 0 | 是否预防性使用抗菌药物 |
| antibiotic_timing | VARCHAR(64) | Y | NULL | 使用时机（术前0.5-1小时） |
| antibiotic_type | VARCHAR(64) | Y | NULL | 抗菌药物类型 |
| consent_required | TINYINT(1) | N | 1 | 是否需知情同意 |
| consent_types | VARCHAR(255) | Y | NULL | 同意书类型（手术/麻醉/植入物/输血） |
| anesthesia_visit | TINYINT(1) | N | 0 | 是否需麻醉访视 |
| surgeon_visit | TINYINT(1) | N | 0 | 是否需手术医生访视 |
| pre_op_checklist | VARCHAR(1000) | Y | NULL | 术前核对清单（JSON 数组） |
| post_op_care | VARCHAR(1000) | Y | NULL | 术后护理要点 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_prep_op(operation_id, rule_type, deleted)` 唯一。

### 07.7 表：`md_operation_prepare_item`（术前准备明细表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| rule_id | BIGINT UNSIGNED | N | - | 规则 ID |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| item_type | VARCHAR(32) | N | - | 类型：CHECK/DRUG/NURSING/PREP |
| item_id | BIGINT UNSIGNED | Y | NULL | 关联对象 ID（检查/药品/护理项目） |
| item_code | VARCHAR(32) | Y | NULL | 关联对象编码 |
| item_name | VARCHAR(200) | N | - | 项目名称 |
| is_required | TINYINT(1) | N | 1 | 是否必做 |
| default_qty | DECIMAL(10,2) | Y | NULL | 默认数量 |
| unit | VARCHAR(16) | Y | NULL | 单位 |
| timing | VARCHAR(64) | Y | NULL | 执行时机（术前1天/术前2小时） |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_prep_item(rule_id)`；`idx_prep_item_type(item_type)`。

### 07.8 表：`md_operation_exam_item_rel`（术前检查关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| exam_item_id | BIGINT UNSIGNED | N | - | 检查项目 ID |
| exam_item_code | VARCHAR(32) | N | - | 检查项目编码 |
| exam_item_name | VARCHAR(200) | Y | NULL | 检查项目名称 |
| is_required | TINYINT(1) | N | 1 | 是否必做 |
| category | VARCHAR(32) | Y | NULL | 分类（眼科专科/术前常规/其他） |
| laterality | VARCHAR(16) | Y | NULL | 眼别要求（LEFT/RIGHT/BOTH/NA） |
| timing | VARCHAR(64) | Y | NULL | 检查时机（术前1天/术前1周） |
| valid_days | INT | Y | NULL | 检查结果有效天数 |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_op_exam(operation_id, exam_item_id, deleted)` 唯一；`idx_exam(exam_item_id)`；`idx_exam_required(is_required)`。

### 07.9 表：`md_operation_lab_item_rel`（术前检验关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| lab_item_id | BIGINT UNSIGNED | N | - | 检验项目 ID |
| lab_item_code | VARCHAR(32) | N | - | 检验项目编码 |
| lab_item_name | VARCHAR(200) | Y | NULL | 检验项目名称 |
| is_required | TINYINT(1) | N | 1 | 是否必做 |
| category | VARCHAR(32) | Y | NULL | 分类（血常规/凝血/生化/传染病/其他） |
| timing | VARCHAR(64) | Y | NULL | 检验时机 |
| valid_days | INT | Y | NULL | 检验结果有效天数 |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_op_lab(operation_id, lab_item_id, deleted)` 唯一；`idx_lab(lab_item_id)`。

### 07.10 表：`md_operation_material_rel`（手术-耗材关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| material_id | BIGINT UNSIGNED | N | - | 耗材 ID |
| material_code | VARCHAR(32) | N | - | 耗材编码 |
| material_name | VARCHAR(200) | Y | NULL | 耗材名称 |
| spec | VARCHAR(200) | Y | NULL | 规格 |
| is_required | TINYINT(1) | N | 1 | 是否必用 |
| default_qty | DECIMAL(12,4) | N | 1 | 默认数量 |
| unit | VARCHAR(16) | Y | NULL | 单位 |
| usage_scene | VARCHAR(32) | Y | NULL | 使用场景（术中/术后/灌洗） |
| is_implant | TINYINT(1) | N | 0 | 是否植入物 |
| trace_required | TINYINT(1) | N | 0 | 是否需追溯 |
| group_name | VARCHAR(64) | Y | NULL | 分组（晶体组/灌注组/缝线组） |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_op_mat(operation_id, material_id, deleted)` 唯一；`idx_mat(material_id)`；`idx_mat_implant(is_implant)`。

### 07.11 表：`md_operation_iol_rel`（手术-人工晶体关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| iol_id | BIGINT UNSIGNED | Y | NULL | 具体晶体 ID（为空表示按类型/品牌范围选） |
| iol_code | VARCHAR(32) | Y | NULL | 晶体编码 |
| iol_brand | VARCHAR(128) | Y | NULL | 晶体品牌 |
| iol_model | VARCHAR(128) | Y | NULL | 晶体型号 |
| iol_type | VARCHAR(32) | Y | NULL | 晶体类型 |
| brand_scope | VARCHAR(500) | Y | NULL | 允许品牌范围（逗号分隔，空=不限） |
| type_scope | VARCHAR(255) | Y | NULL | 允许类型范围（逗号分隔，空=不限） |
| sphere_min | DECIMAL(6,2) | Y | NULL | 球镜下限 |
| sphere_max | DECIMAL(6,2) | Y | NULL | 球镜上限 |
| cylinder_min | DECIMAL(6,2) | Y | NULL | 柱镜下限 |
| cylinder_max | DECIMAL(6,2) | Y | NULL | 柱镜上限 |
| is_default | TINYINT(1) | N | 0 | 是否默认晶体 |
| is_required | TINYINT(1) | N | 0 | 是否必须植入晶体 |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_op_iol(operation_id)`；`idx_iol(iol_id)`；`idx_iol_type(iol_type)`。

> **说明**：当 `iol_id` 为空时，表示"该手术允许从 `brand_scope` + `type_scope` 范围内选择晶体"（如白内障手术可选单焦或多焦），由 M09 手术申请时按患者情况选型；当 `iol_id` 有值时表示"指定使用该晶体"。

### 07.12 表：`md_operation_implant`（植入物手术配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| is_implant_surgery | TINYINT(1) | N | 1 | 是否植入物手术 |
| implant_required | TINYINT(1) | N | 1 | 是否强制使用植入物 |
| implant_categories | VARCHAR(500) | Y | NULL | 允许的植入物类别（多选） |
| trace_required | TINYINT(1) | N | 1 | 是否强制 UDI 追溯 |
| trace_fields | VARCHAR(500) | Y | NULL | 追溯必填字段 |
| binding_timing | VARCHAR(32) | N | 'INTRAOPERATIVE' | 绑定时机 |
| require_implant_record | TINYINT(1) | N | 1 | 是否生成植入物登记表 |
| require_consent | TINYINT(1) | N | 1 | 是否需植入物知情同意 |
| require_followup | TINYINT(1) | N | 1 | 是否需随访 |
| mri_compatible | VARCHAR(16) | Y | NULL | MRI 兼容性 |
| adverse_event_report | TINYINT(1) | N | 1 | 是否需不良事件上报 |
| iol_power_calculation | TINYINT(1) | N | 0 | 是否需 IOL 度数计算 |
| iol_formula | VARCHAR(64) | Y | NULL | IOL 计算公式（SRK-T/Holladay/Haigis） |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_implant_op(operation_id, deleted)` 唯一；`idx_implant_trace(trace_required)`。

### 07.13 表：`md_operation_staff_auth`（手术医师授权表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| staff_id | BIGINT UNSIGNED | N | - | 医师 ID |
| staff_code | VARCHAR(32) | Y | NULL | 工号 |
| staff_name | VARCHAR(64) | Y | NULL | 姓名 |
| dept_id | BIGINT UNSIGNED | Y | NULL | 医师科室 |
| auth_level | VARCHAR(32) | N | 'FULL' | 授权级别：FULL（独立主刀）/ASSIST（助手）/SUPERVISED（带教） |
| auth_date | DATE | Y | NULL | 授权日期 |
| auth_by | BIGINT UNSIGNED | Y | NULL | 授权人 |
| expire_date | DATE | Y | NULL | 授权有效期 |
| review_status | VARCHAR(16) | N | 'APPROVED' | 审核状态 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_op_staff(operation_id, staff_id, deleted)` 唯一；`idx_staff(staff_id)`；`idx_auth_level(auth_level)`；`idx_expire(expire_date)`。

### 07.14 表：`md_operation_followup_rule`（术后随访规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| need_followup | TINYINT(1) | N | 1 | 是否需随访 |
| followup_days | VARCHAR(128) | Y | NULL | 随访周期（天，逗号分隔） |
| followup_mode | VARCHAR(32) | N | 'OUTPATIENT' | 随访方式：OUTPATIENT（门诊）/PHONE（电话）/WECHAT（微信）/MIXED |
| followup_dept_id | BIGINT UNSIGNED | Y | NULL | 随访科室 |
| followup_doctor_required | TINYINT(1) | N | 1 | 是否需原主刀医生随访 |
| followup_items | VARCHAR(500) | Y | NULL | 随访检查项（视力/眼压/裂隙灯等） |
| followup_template_id | BIGINT UNSIGNED | Y | NULL | 随访模板 ID（M19） |
| reminder_days_before | INT | Y | NULL | 提前提醒天数 |
| auto_create_task | TINYINT(1) | N | 1 | 是否自动创建随访任务 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_fu_op(operation_id, deleted)` 唯一。

### 07.15 表：`md_operation_charge_rel`（手术收费关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| charge_item_id | BIGINT UNSIGNED | N | - | 收费项目 ID |
| charge_item_code | VARCHAR(32) | N | - | 收费项目编码 |
| charge_item_name | VARCHAR(200) | Y | NULL | 收费项目名称 |
| rel_type | VARCHAR(32) | N | 'PRIMARY' | PRIMARY（主手术费）/SECONDARY（加收）/BUNDLED（打包） |
| charge_scene | VARCHAR(64) | Y | NULL | 计费场景（住院/日间/门诊） |
| qty_factor | DECIMAL(12,4) | N | 1 | 数量换算 |
| is_auto_charge | TINYINT(1) | N | 1 | 是否自动计费 |
| is_eye_side | TINYINT(1) | N | 1 | 是否按眼别 |
| sort_no | INT | N | 999 | 排序 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_op_charge(operation_id, charge_item_id, deleted)` 唯一；`idx_charge_item(charge_item_id)`。

### 07.16 表：`md_operation_template_rel`（手术模板关联表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| operation_id | BIGINT UNSIGNED | N | - | 手术项目 ID |
| operation_code | VARCHAR(32) | N | - | 手术编码 |
| template_type | VARCHAR(32) | N | - | ORDER（医嘱模板）/NURSING（护理模板）/CONSENT（同意书模板）/EMR（病历模板） |
| template_id | BIGINT UNSIGNED | N | - | 模板 ID |
| template_code | VARCHAR(64) | Y | NULL | 模板编码 |
| template_name | VARCHAR(200) | Y | NULL | 模板名称 |
| apply_scene | VARCHAR(32) | Y | NULL | 应用场景（术前/术中/术后） |
| is_default | TINYINT(1) | N | 0 | 是否默认 |
| sort_no | INT | N | 999 | 排序 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `idx_op_tpl(operation_id, template_type)`；`idx_tpl(template_id)`。

### 07.17 表：`md_anesthesia`（麻醉方式主表）— 扩展

在 M01 总文档基础上扩展：

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| code | VARCHAR(32) | N | - | 麻醉编码 ANE+流水 |
| name | VARCHAR(64) | N | - | 麻醉名称 |
| english_name | VARCHAR(128) | Y | NULL | 英文名 |
| anesthesia_type | VARCHAR(32) | N | - | 麻醉分类（3.2.1） |
| anesthesia_level | VARCHAR(16) | N | 'LOCAL' | 麻醉级别：LOCAL/REGIONAL/GENERAL |
| is_eye_special | TINYINT(1) | N | 0 | 是否眼科专用 |
| need_anesthetist | TINYINT(1) | N | 1 | 是否需麻醉医生 |
| need_previsit | TINYINT(1) | N | 0 | 是否需术前访视 |
| need_monitor | TINYINT(1) | N | 1 | 是否需监护 |
| need_fasting | TINYINT(1) | N | 0 | 是否需禁食 |
| fasting_solid_hours | INT | Y | NULL | 禁食固体时间（小时） |
| fasting_liquid_hours | INT | Y | NULL | 禁清饮时间（小时） |
| injection_site | VARCHAR(64) | Y | NULL | 注射部位 |
| injection_depth | VARCHAR(32) | Y | NULL | 注射深度 |
| default_drug_ids | VARCHAR(1000) | Y | NULL | 默认麻醉药品 |
| base_charge_item_id | BIGINT UNSIGNED | Y | NULL | 基础麻醉费项目 |
| monitor_charge_item_id | BIGINT UNSIGNED | Y | NULL | 监测费项目 |
| extra_charge_ids | VARCHAR(500) | Y | NULL | 其他加收项目 |
| anesthesia_record_template_id | BIGINT UNSIGNED | Y | NULL | 麻醉记录模板 |
| anesthesia_consent_template_id | BIGINT UNSIGNED | Y | NULL | 麻醉同意书模板 |
| sort_no | INT | N | 999 | 排序 |
| status | TINYINT | N | 1 | 状态 |
| audit_status | VARCHAR(16) | N | 'APPROVED' | 审批状态 |
| version | INT | N | 0 | 乐观锁版本号 |
| remark | VARCHAR(512) | Y | NULL | 备注 |
| created_by | BIGINT UNSIGNED | Y | NULL | 创建人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_by | BIGINT UNSIGNED | Y | NULL | 更新人 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |
| is_deleted | TINYINT(1) | N | 0 | 逻辑删除 |

**索引：** `uk_anes_code(code, is_deleted)` 唯一；`idx_anes_type(anesthesia_type)`；`idx_anes_level(anesthesia_level)`；`idx_anes_special(is_eye_special)`。

### 07.18 表：`md_anesthesia_drug`（麻醉默认药品表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| anesthesia_id | BIGINT UNSIGNED | N | - | 麻醉方式 ID |
| anesthesia_code | VARCHAR(32) | N | - | 麻醉编码 |
| drug_id | BIGINT UNSIGNED | N | - | 药品 ID |
| drug_code | VARCHAR(32) | N | - | 药品编码 |
| drug_name | VARCHAR(200) | Y | NULL | 药品名称 |
| spec | VARCHAR(128) | Y | NULL | 规格 |
| default_dose | DECIMAL(10,4) | Y | NULL | 默认剂量 |
| dose_unit | VARCHAR(16) | Y | NULL | 剂量单位 |
| route_code | VARCHAR(32) | Y | NULL | 给药途径 |
| is_required | TINYINT(1) | N | 0 | 是否必用 |
| sort_no | INT | N | 999 | 排序 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_anes_drug(anesthesia_id, drug_id, deleted)` 唯一；`idx_drug(drug_id)`。

### 07.19 表：`md_surgery_level_rule`（手术分级规则表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| level_code | VARCHAR(32) | N | - | 级别编码 LEVEL_1~LEVEL_4 |
| level_name | VARCHAR(32) | N | - | 级别名称（一/二/三/四级） |
| risk_level | VARCHAR(16) | N | - | 风险等级（LOW/MEDIUM/HIGH/EXTREME） |
| min_title_code | VARCHAR(32) | N | - | 最低职称要求 |
| need_chief_approve | TINYINT(1) | N | 0 | 是否需科主任审批 |
| need_medical_affairs_approve | TINYINT(1) | N | 0 | 是否需医务科审批 |
| need_director_approve | TINYINT(1) | N | 0 | 是否需院长审批 |
| need_case_discussion | TINYINT(1) | N | 0 | 是否需术前讨论 |
| need_report_to_authority | TINYINT(1) | N | 0 | 是否需上报卫生行政部门 |
| approval_sla_hours | INT | N | 24 | 审批 SLA（小时） |
| effective_date | DATE | Y | NULL | 生效日期 |
| status | VARCHAR(16) | N | 'ENABLED' | 状态 |
| deleted | TINYINT(1) | N | 0 | 逻辑删除 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_level(level_code, deleted)` 唯一。

**预置数据：**

| 级别 | 风险 | 最低职称 | 科主任 | 医务科 | 院长 | 术前讨论 |
|---|---|---|---|---|---|---|
| 一级 | LOW | 住院医师 | 否 | 否 | 否 | 否 |
| 二级 | MEDIUM | 主治医师 | 否 | 否 | 否 | 否 |
| 三级 | HIGH | 副主任医师 | 是 | 否 | 否 | 是 |
| 四级 | EXTREME | 主任医师 | 是 | 是 | 是 | 是 |

### 07.20 表：`md_operation_change_log`（变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| change_scope | VARCHAR(32) | N | - | OPERATION/ANESTHESIA/LEVEL_RULE/AUTH |
| target_id | BIGINT UNSIGNED | Y | NULL | 目标 ID |
| target_key | VARCHAR(64) | Y | NULL | 目标编码 |
| target_name | VARCHAR(200) | Y | NULL | 目标名称 |
| change_type | VARCHAR(32) | N | - | CREATE/UPDATE/DELETE/ENABLE/DISABLE/IMPORT/AUTH |
| before_snapshot | JSON | Y | NULL | 变更前快照 |
| after_snapshot | JSON | Y | NULL | 变更后快照 |
| changed_fields | VARCHAR(2000) | Y | NULL | 变更字段 |
| change_summary | VARCHAR(1000) | Y | NULL | 变更摘要 |
| change_reason | VARCHAR(500) | Y | NULL | 变更原因 |
| affected_operation_count | INT | N | 0 | 影响手术数 |
| operator_id | BIGINT UNSIGNED | N | - | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| operator_ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 操作时间 |

**索引：** `idx_ocl_scope(change_scope, created_at)`；`idx_ocl_target(target_id)`；`idx_ocl_operator(operator_id, created_at)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 10 年。

### 07.21 表：`md_operation_sync_log`（同步日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| event_id | VARCHAR(64) | N | - | 事件 ID |
| event_type | VARCHAR(64) | N | - | mdm.operation.changed 等 |
| object_type | VARCHAR(32) | N | - | OPERATION/ANESTHESIA |
| object_code | VARCHAR(32) | Y | NULL | 对象编码 |
| subscriber | VARCHAR(32) | N | - | 订阅方（M06/M09/M11/M15/M16） |
| deliver_mode | VARCHAR(16) | N | 'MQ' | MQ/HTTP/REDIS |
| payload | JSON | Y | NULL | 消息体 |
| sync_status | VARCHAR(16) | N | 'PENDING' | PENDING/SUCCESS/FAILED/IGNORED |
| retry_count | INT | N | 0 | 重试次数 |
| error_msg | VARCHAR(1000) | Y | NULL | 错误信息 |
| affected_count | INT | N | 0 | 影响记录数 |
| cost_ms | INT | Y | NULL | 耗时 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| finished_at | DATETIME | Y | NULL | 完成时间 |

**索引：** `uk_osl_event_sub(event_id, subscriber)`；`idx_osl_status(sync_status, created_at)`；`idx_osl_subscriber(subscriber, sync_status)`。

**分区：** 按 `created_at` 月份 RANGE 分区，保留 1 年。

### 07.22 表：`md_operation_code_seq`（手术编码序列表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| seq_type | VARCHAR(32) | N | - | OPERATION/ANESTHESIA |
| category_code | VARCHAR(16) | N | '' | 分类码 |
| prefix | VARCHAR(16) | N | - | 前缀 |
| period_key | VARCHAR(16) | N | '' | 周期键 |
| current_seq | BIGINT | N | 0 | 当前序号 |
| seq_width | INT | N | 5 | 序号位数 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_ocs_seq(seq_type, category_code, period_key)` 唯一。

### 07.23 表：`md_operation_import_task`（导入任务表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT UNSIGNED | N | AUTO_INCREMENT | 主键 |
| batch_no | VARCHAR(64) | N | - | 批次号 |
| import_type | VARCHAR(32) | N | - | OPERATION/ANESTHESIA/PREP_ITEM/AUTH |
| file_name | VARCHAR(255) | N | - | 文件名 |
| file_url | VARCHAR(500) | Y | NULL | 文件 URL |
| total_rows | INT | N | 0 | 总行数 |
| success_rows | INT | N | 0 | 成功行数 |
| fail_rows | INT | N | 0 | 失败行数 |
| warn_rows | INT | N | 0 | 警告行数 |
| import_mode | VARCHAR(16) | N | 'UPSERT' | INSERT/UPDATE/UPSERT |
| task_status | VARCHAR(16) | N | 'PENDING' | PENDING/VALIDATING/VALIDATED/IMPORTING/SUCCESS/FAILED/CANCELLED |
| error_file_url | VARCHAR(500) | Y | NULL | 错误报告 URL |
| error_summary | JSON | Y | NULL | 错误摘要 |
| dry_run | TINYINT(1) | N | 0 | 是否试运行 |
| started_at | DATETIME | Y | NULL | 开始时间 |
| finished_at | DATETIME | Y | NULL | 结束时间 |
| cost_ms | BIGINT | Y | NULL | 耗时 |
| operator_id | BIGINT UNSIGNED | Y | NULL | 操作人 |
| created_at | DATETIME | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | N | CURRENT_TIMESTAMP ON UPDATE | 更新时间 |

**索引：** `uk_oit_batch(batch_no)` 唯一；`idx_oit_status(task_status)`。

### 07.24 SQLAlchemy 2.0 模型定义

```python
# app/models/mdm/surgery.py
"""手术与麻醉主数据 ORM 模型"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, SmallInteger, Date, DateTime, DECIMAL,
    JSON, Text, Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin


class Operation(Base, TimestampMixin, SoftDeleteMixin):
    """手术项目主表"""
    __tablename__ = "md_operation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # ---------- 标识 ----------
    code: Mapped[str] = mapped_column(String(32), nullable=False, comment="手术编码")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="手术名称")
    short_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="简称")
    english_name: Mapped[Optional[str]] = mapped_column(String(255))
    pinyin_code: Mapped[str] = mapped_column(String(32), nullable=False)
    pinyin_short: Mapped[str] = mapped_column(String(32), nullable=False)
    wb_code: Mapped[Optional[str]] = mapped_column(String(32))

    # ---------- 分类 ----------
    icd9_code: Mapped[Optional[str]] = mapped_column(String(20))
    operation_category: Mapped[str] = mapped_column(String(32), nullable=False)
    surgery_level: Mapped[str] = mapped_column(String(32), nullable=False)
    eye_specialty: Mapped[str] = mapped_column(String(500), nullable=False)
    body_position: Mapped[Optional[str]] = mapped_column(String(32))
    laterality_required: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    allow_bilateral: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 手术场景 ----------
    is_day_surgery: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_outpatient_surgery: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_inpatient_surgery: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    is_emergency: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    is_minimally_invasive: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 时长 ----------
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    duration_minutes_max: Mapped[Optional[int]] = mapped_column(Integer)
    anesthesia_duration: Mapped[Optional[int]] = mapped_column(Integer)
    prepare_hours: Mapped[Optional[int]] = mapped_column(Integer)
    recovery_minutes: Mapped[Optional[int]] = mapped_column(Integer)

    # ---------- 资源 ----------
    room_type_req: Mapped[Optional[str]] = mapped_column(String(255))
    equipment_ids: Mapped[Optional[str]] = mapped_column(String(1000))

    # ---------- 屈光 ----------
    is_refractive: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    refractive_type: Mapped[Optional[str]] = mapped_column(String(64))
    need_refractive_record: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_navigation: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # ---------- 植入物 ----------
    is_implant_surgery: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    default_implant_types: Mapped[Optional[str]] = mapped_column(String(255))

    # ---------- 随访 ----------
    need_followup: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    followup_days: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- 模板 ----------
    order_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    nursing_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    consent_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    anesthesia_consent_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    implant_consent_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    # ---------- 收费 ----------
    charge_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    include_material: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    extra_charge_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    allow_discount: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    cost_subject: Mapped[Optional[str]] = mapped_column(String(64))
    income_subject: Mapped[Optional[str]] = mapped_column(String(64))

    # ---------- 权限 ----------
    min_surgery_level: Mapped[str] = mapped_column(String(32), default="LEVEL_1", nullable=False)
    need_chief_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_medical_affairs_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_director_approve: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    auth_scope_type: Mapped[str] = mapped_column(String(16), default="LEVEL", nullable=False)
    is_high_risk: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    risk_desc: Mapped[Optional[str]] = mapped_column(String(500))

    # ---------- 展示 ----------
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    is_common: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    hotkey: Mapped[Optional[str]] = mapped_column(String(16))

    # ---------- 状态 ----------
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    effective_date: Mapped[Optional[date]] = mapped_column(Date)
    expire_date: Mapped[Optional[date]] = mapped_column(Date)
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    ext_json: Mapped[Optional[dict]] = mapped_column(JSON)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    # ---------- 关系 ----------
    ext: Mapped[Optional["OperationExt"]] = relationship(
        back_populates="operation", uselist=False, lazy="selectin"
    )
    aliases: Mapped[List["OperationAlias"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    anesthesia_rels: Mapped[List["OperationAnesthesiaRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    prepare_rules: Mapped[List["OperationPrepareRule"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    exam_rels: Mapped[List["OperationExamItemRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    lab_rels: Mapped[List["OperationLabItemRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    material_rels: Mapped[List["OperationMaterialRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    iol_rels: Mapped[List["OperationIolRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    implant: Mapped[Optional["OperationImplant"]] = relationship(
        back_populates="operation", uselist=False, lazy="selectin"
    )
    staff_auths: Mapped[List["OperationStaffAuth"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    followup_rule: Mapped[Optional["OperationFollowupRule"]] = relationship(
        back_populates="operation", uselist=False, lazy="selectin"
    )
    charge_rels: Mapped[List["OperationChargeRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )
    template_rels: Mapped[List["OperationTemplateRel"]] = relationship(
        back_populates="operation", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint("code", "deleted", name="uk_op_code"),
        UniqueConstraint("hotkey", "deleted", name="uk_op_hotkey"),
        Index("idx_op_name", "name"),
        Index("idx_op_pinyin", "pinyin_code", "pinyin_short"),
        Index("idx_op_icd9", "icd9_code"),
        Index("idx_op_level", "surgery_level"),
        Index("idx_op_refractive", "is_refractive", "status"),
        Index("idx_op_day", "is_day_surgery"),
        Index("idx_op_implant", "is_implant_surgery"),
        Index("idx_op_status", "status", "audit_status"),
        Index("idx_op_updated", "updated_at"),
        {"comment": "手术项目主表"},
    )

    # ---------- 领域方法 ----------
    LEVEL_ORDER = {"LEVEL_1": 1, "LEVEL_2": 2, "LEVEL_3": 3, "LEVEL_4": 4}

    @property
    def level_rank(self) -> int:
        return self.LEVEL_ORDER.get(self.surgery_level, 0)

    def specialty_list(self) -> List[str]:
        return (self.eye_specialty or "").split(",") if self.eye_specialty else []

    def followup_day_list(self) -> List[int]:
        if not self.followup_days:
            return []
        return [int(d) for d in self.followup_days.split(",") if d.strip().isdigit()]

    def requires_approval(self) -> bool:
        return bool(
            self.need_chief_approve
            or self.need_medical_affairs_approve
            or self.need_director_approve
        )

    def to_snapshot(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "operation_category": self.operation_category,
            "surgery_level": self.surgery_level,
            "eye_specialty": self.eye_specialty,
            "duration_minutes": self.duration_minutes,
            "is_refractive": self.is_refractive,
            "refractive_type": self.refractive_type,
            "is_implant_surgery": self.is_implant_surgery,
            "status": self.status,
            "version": self.version,
        }


class Anesthesia(Base, TimestampMixin, SoftDeleteMixin):
    """麻醉方式主表"""
    __tablename__ = "md_anesthesia"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    english_name: Mapped[Optional[str]] = mapped_column(String(128))
    anesthesia_type: Mapped[str] = mapped_column(String(32), nullable=False)
    anesthesia_level: Mapped[str] = mapped_column(String(16), default="LOCAL", nullable=False)
    is_eye_special: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_anesthetist: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    need_previsit: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    need_monitor: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    need_fasting: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    fasting_solid_hours: Mapped[Optional[int]] = mapped_column(Integer)
    fasting_liquid_hours: Mapped[Optional[int]] = mapped_column(Integer)
    injection_site: Mapped[Optional[str]] = mapped_column(String(64))
    injection_depth: Mapped[Optional[str]] = mapped_column(String(32))
    default_drug_ids: Mapped[Optional[str]] = mapped_column(String(1000))
    base_charge_item_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    monitor_charge_item_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    extra_charge_ids: Mapped[Optional[str]] = mapped_column(String(500))
    anesthesia_record_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    anesthesia_consent_template_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    audit_status: Mapped[str] = mapped_column(String(16), default="APPROVED", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(512))

    drugs: Mapped[List["AnesthesiaDrug"]] = relationship(
        back_populates="anesthesia", lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("code", "is_deleted", name="uk_anes_code"),
        Index("idx_anes_type", "anesthesia_type"),
        Index("idx_anes_level", "anesthesia_level"),
        {"comment": "麻醉方式主表"},
    )

    @property
    def requires_anesthesiologist(self) -> bool:
        return bool(self.need_anesthetist)


class AnesthesiaDrug(Base):
    """麻醉默认药品"""
    __tablename__ = "md_anesthesia_drug"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    anesthesia_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    anesthesia_code: Mapped[str] = mapped_column(String(32), nullable=False)
    drug_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    drug_code: Mapped[str] = mapped_column(String(32), nullable=False)
    drug_name: Mapped[Optional[str]] = mapped_column(String(200))
    spec: Mapped[Optional[str]] = mapped_column(String(128))
    default_dose: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    dose_unit: Mapped[Optional[str]] = mapped_column(String(16))
    route_code: Mapped[Optional[str]] = mapped_column(String(32))
    is_required: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    sort_no: Mapped[int] = mapped_column(Integer, default=999, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    deleted: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    anesthesia: Mapped["Anesthesia"] = relationship(back_populates="drugs")

    __table_args__ = (
        UniqueConstraint("anesthesia_id", "drug_id", "deleted", name="uk_anes_drug"),
        {"comment": "麻醉默认药品"},
    )
```

### 07.25 Pydantic Schema 定义

```python
# app/schemas/mdm/surgery.py
"""手术与麻醉主数据 Pydantic Schema"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ==================== 公共 ====================
class OperationAliasSchema(BaseModel):
    id: Optional[int] = None
    alias_name: str = Field(..., max_length=200)
    alias_type: Literal["CLINICAL", "OFFICIAL", "HISTORICAL", "ABBREVIATION"] = "CLINICAL"
    sort_no: int = 999


class AnesthesiaRelSchema(BaseModel):
    id: Optional[int] = None
    anesthesia_id: int
    anesthesia_code: Optional[str] = None
    is_default: bool = False
    is_required: bool = False
    priority: int = 999
    remark: Optional[str] = Field(None, max_length=255)


class PrepareItemSchema(BaseModel):
    id: Optional[int] = None
    item_type: Literal["CHECK", "DRUG", "NURSING", "PREP"]
    item_id: Optional[int] = None
    item_code: Optional[str] = None
    item_name: str = Field(..., max_length=200)
    is_required: bool = True
    default_qty: Optional[Decimal] = Field(None, ge=0)
    unit: Optional[str] = None
    timing: Optional[str] = Field(None, max_length=64)
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=255)


class PrepareRuleSchema(BaseModel):
    id: Optional[int] = None
    rule_type: Literal["GENERAL", "ANESTHESIA_SPECIFIC"] = "GENERAL"
    fasting_required: bool = False
    fasting_solid_hours: Optional[int] = Field(None, ge=0, le=48)
    fasting_liquid_hours: Optional[int] = Field(None, ge=0, le=24)
    fasting_note: Optional[str] = Field(None, max_length=500)
    skin_prep_required: bool = False
    skin_prep_desc: Optional[str] = Field(None, max_length=255)
    eye_mark_required: bool = True
    dilate_pupil_required: bool = False
    dilate_drop_type: Optional[str] = Field(None, max_length=64)
    dilate_minutes: Optional[int] = Field(None, ge=0)
    antibiotic_prophylaxis: bool = False
    antibiotic_timing: Optional[str] = Field(None, max_length=64)
    antibiotic_type: Optional[str] = Field(None, max_length=64)
    consent_required: bool = True
    consent_types: Optional[List[str]] = None
    anesthesia_visit: bool = False
    surgeon_visit: bool = False
    pre_op_checklist: Optional[List[str]] = None
    post_op_care: Optional[str] = Field(None, max_length=1000)
    items: List[PrepareItemSchema] = []

    @model_validator(mode="after")
    def validate_prepare(self):
        if self.fasting_required:
            if self.fasting_solid_hours is None:
                raise ValueError("需禁食时必须设置禁食固体时间")
        if self.antibiotic_prophylaxis and not self.antibiotic_timing:
            raise ValueError("预防性使用抗菌药物时必须设置使用时机")
        if self.dilate_pupil_required and self.dilate_minutes is None:
            raise ValueError("需散瞳时必须设置散瞳提前时间")
        return self


class ExamItemRelSchema(BaseModel):
    id: Optional[int] = None
    exam_item_id: int
    exam_item_code: Optional[str] = None
    is_required: bool = True
    category: Optional[Literal["OPHTHALMIC", "PRE_OP_ROUTINE", "OTHER"]] = None
    laterality: Optional[Literal["LEFT", "RIGHT", "BOTH", "NA"]] = None
    timing: Optional[str] = Field(None, max_length=64)
    valid_days: Optional[int] = Field(None, ge=0, le=365)
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=255)


class LabItemRelSchema(BaseModel):
    id: Optional[int] = None
    lab_item_id: int
    lab_item_code: Optional[str] = None
    is_required: bool = True
    category: Optional[Literal[
        "ROUTINE_BLOOD", "COAGULATION", "BIOCHEMISTRY", "INFECTIOUS", "OTHER"
    ]] = None
    timing: Optional[str] = Field(None, max_length=64)
    valid_days: Optional[int] = Field(None, ge=0, le=365)
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=255)


class MaterialRelSchema(BaseModel):
    id: Optional[int] = None
    material_id: int
    material_code: Optional[str] = None
    is_required: bool = True
    default_qty: Decimal = Field(Decimal("1"), gt=0)
    unit: Optional[str] = None
    usage_scene: Optional[Literal["INTRAOPERATIVE", "POSTOPERATIVE", "IRRIGATION"]] = None
    is_implant: bool = False
    trace_required: bool = False
    group_name: Optional[str] = Field(None, max_length=64)
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=255)


class IolRelSchema(BaseModel):
    id: Optional[int] = None
    iol_id: Optional[int] = None
    iol_code: Optional[str] = None
    brand_scope: Optional[List[str]] = None
    type_scope: Optional[List[str]] = None
    sphere_min: Optional[Decimal] = Field(None, ge=-30, le=40)
    sphere_max: Optional[Decimal] = Field(None, ge=-30, le=40)
    cylinder_min: Optional[Decimal] = Field(None, ge=-30, le=30)
    cylinder_max: Optional[Decimal] = Field(None, ge=-30, le=30)
    is_default: bool = False
    is_required: bool = False
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=255)

    @model_validator(mode="after")
    def validate_iol_rel(self):
        if self.sphere_min is not None and self.sphere_max is not None:
            if self.sphere_min > self.sphere_max:
                raise ValueError("球镜下限不能大于上限")
        if self.cylinder_min is not None and self.cylinder_max is not None:
            if self.cylinder_min > self.cylinder_max:
                raise ValueError("柱镜下限不能大于上限")
        if not self.iol_id and not self.brand_scope and not self.type_scope:
            raise ValueError("必须指定具体晶体，或至少限制品牌/类型范围")
        return self


class ImplantConfigSchema(BaseModel):
    id: Optional[int] = None
    is_implant_surgery: bool = True
    implant_required: bool = True
    implant_categories: Optional[List[str]] = None
    trace_required: bool = True
    trace_fields: Optional[List[str]] = None
    binding_timing: Literal["PREOPERATIVE", "INTRAOPERATIVE", "POSTOPERATIVE"] = "INTRAOPERATIVE"
    require_implant_record: bool = True
    require_consent: bool = True
    require_followup: bool = True
    mri_compatible: Optional[Literal["YES", "NO", "CONDITIONAL"]] = None
    adverse_event_report: bool = True
    iol_power_calculation: bool = False
    iol_formula: Optional[Literal["SRK_T", "HOLLADAY", "HAIGIS"]] = None

    @model_validator(mode="after")
    def validate_implant(self):
        if self.trace_required and not self.trace_fields:
            raise ValueError("强制追溯时必须选择追溯字段")
        if self.iol_power_calculation and not self.iol_formula:
            raise ValueError("需 IOL 度数计算时必须选择计算公式")
        return self


class StaffAuthSchema(BaseModel):
    id: Optional[int] = None
    staff_id: int
    staff_code: Optional[str] = None
    auth_level: Literal["FULL", "ASSIST", "SUPERVISED"] = "FULL"
    auth_date: Optional[date] = None
    auth_by: Optional[int] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=255)


class FollowupRuleSchema(BaseModel):
    id: Optional[int] = None
    need_followup: bool = True
    followup_days: Optional[str] = Field(None, pattern=r"^\d+(,\d+)*$")
    followup_mode: Literal["OUTPATIENT", "PHONE", "WECHAT", "MIXED"] = "OUTPATIENT"
    followup_dept_id: Optional[int] = None
    followup_doctor_required: bool = True
    followup_items: Optional[List[str]] = None
    followup_template_id: Optional[int] = None
    reminder_days_before: Optional[int] = Field(None, ge=0, le=30)
    auto_create_task: bool = True


class ChargeRelSchema(BaseModel):
    id: Optional[int] = None
    charge_item_id: int
    charge_item_code: Optional[str] = None
    rel_type: Literal["PRIMARY", "SECONDARY", "BUNDLED"] = "PRIMARY"
    charge_scene: Optional[str] = None
    qty_factor: Decimal = Field(Decimal("1"), gt=0)
    is_auto_charge: bool = True
    is_eye_side: bool = True
    sort_no: int = 999


class TemplateRelSchema(BaseModel):
    id: Optional[int] = None
    template_type: Literal["ORDER", "NURSING", "CONSENT", "EMR"]
    template_id: int
    template_code: Optional[str] = None
    apply_scene: Optional[Literal["PRE_OP", "INTRA_OP", "POST_OP"]] = None
    is_default: bool = False
    sort_no: int = 999


# ==================== 手术项目 ====================
class OperationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    short_name: Optional[str] = Field(None, max_length=64)
    english_name: Optional[str] = Field(None, max_length=255)
    icd9_code: Optional[str] = Field(None, max_length=20, pattern=r"^\d{2}\.\d{1,2}$")
    operation_category: Literal["THERAPEUTIC", "DIAGNOSTIC", "EXPLORATORY", "COSMETIC"]
    surgery_level: Literal["LEVEL_1", "LEVEL_2", "LEVEL_3", "LEVEL_4"]
    eye_specialty: List[str] = Field(..., min_length=1)
    body_position: Optional[Literal[
        "SUPINE", "SEMI_SUPINE", "LATERAL", "SITTING"
    ]] = None
    laterality_required: bool = True
    allow_bilateral: bool = False
    is_day_surgery: bool = False
    is_outpatient_surgery: bool = False
    is_inpatient_surgery: bool = True
    is_emergency: bool = False
    is_minimally_invasive: bool = False
    duration_minutes: int = Field(60, ge=5, le=1440)
    duration_minutes_max: Optional[int] = Field(None, ge=5, le=1440)
    anesthesia_duration: Optional[int] = Field(None, ge=0, le=600)
    prepare_hours: Optional[int] = Field(None, ge=0, le=168)
    recovery_minutes: Optional[int] = Field(None, ge=0, le=1440)
    room_type_req: Optional[List[str]] = None
    equipment_ids: Optional[List[int]] = None
    is_refractive: bool = False
    refractive_type: Optional[Literal[
        "SMILE", "FS_LASIK", "TRANSPRK", "SMART", "ICL",
        "PRL", "CXL", "PIOL", "RK", "OTHER_REFRACTIVE",
    ]] = None
    need_refractive_record: bool = False
    need_navigation: bool = False
    is_implant_surgery: bool = False
    default_implant_types: Optional[List[str]] = None
    need_followup: bool = True
    followup_days: Optional[str] = Field(None, pattern=r"^\d+(,\d+)*$")
    order_template_id: Optional[int] = None
    nursing_template_id: Optional[int] = None
    consent_template_id: Optional[int] = None
    anesthesia_consent_template_id: Optional[int] = None
    implant_consent_template_id: Optional[int] = None
    charge_item_id: int
    include_material: bool = True
    extra_charge_ids: Optional[List[int]] = None
    allow_discount: bool = True
    cost_subject: Optional[str] = Field(None, max_length=64)
    income_subject: Optional[str] = Field(None, max_length=64)
    min_surgery_level: Literal["LEVEL_1", "LEVEL_2", "LEVEL_3", "LEVEL_4"] = "LEVEL_1"
    need_chief_approve: bool = False
    need_medical_affairs_approve: bool = False
    need_director_approve: bool = False
    auth_scope_type: Literal["LEVEL", "WHITELIST", "BOTH"] = "LEVEL"
    is_high_risk: bool = False
    risk_desc: Optional[str] = Field(None, max_length=500)
    sort_no: int = 999
    is_common: bool = False
    hotkey: Optional[str] = Field(None, max_length=16)
    effective_date: Optional[date] = None
    expire_date: Optional[date] = None
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_operation(self):
        # 屈光手术必须有术式
        if self.is_refractive and not self.refractive_type:
            raise ValueError("屈光手术必须指定屈光术式")
        if self.refractive_type and not self.is_refractive:
            raise ValueError("已指定屈光术式，必须勾选「是否屈光手术」")
        # 植入物手术必须有默认类别
        if self.is_implant_surgery and not self.default_implant_types:
            raise ValueError("植入物手术必须指定默认植入物类别")
        # 级别与审批一致性
        if self.surgery_level == "LEVEL_3" and not self.need_chief_approve:
            raise ValueError("三级手术必须需科主任审批")
        if self.surgery_level == "LEVEL_4":
            if not self.need_chief_approve:
                raise ValueError("四级手术必须需科主任审批")
            if not self.need_medical_affairs_approve:
                raise ValueError("四级手术必须需医务科审批")
        # 时长
        if (self.duration_minutes_max is not None
                and self.duration_minutes_max < self.duration_minutes):
            raise ValueError("最长时长不能小于标准时长")
        # 随访
        if self.need_followup and not self.followup_days:
            raise ValueError("需术后随访时必须设置随访周期")
        # 日期
        if self.effective_date and self.expire_date and self.expire_date <= self.effective_date:
            raise ValueError("失效日期必须晚于生效日期")
        # 手术间要求
        if self.surgery_level in ("LEVEL_3", "LEVEL_4") and not self.room_type_req:
            raise ValueError("三级/四级手术必须指定手术间类型要求")
        return self


class OperationCreate(OperationBase):
    code: Optional[str] = Field(None, description="为空则自动生成")
    aliases: List[OperationAliasSchema] = []
    anesthesia_rels: List[AnesthesiaRelSchema] = []
    prepare_rules: List[PrepareRuleSchema] = []
    exam_rels: List[ExamItemRelSchema] = []
    lab_rels: List[LabItemRelSchema] = []
    material_rels: List[MaterialRelSchema] = []
    iol_rels: List[IolRelSchema] = []
    implant: Optional[ImplantConfigSchema] = None
    staff_auths: List[StaffAuthSchema] = []
    followup_rule: Optional[FollowupRuleSchema] = None
    charge_rels: List[ChargeRelSchema] = []
    template_rels: List[TemplateRelSchema] = []
    ext: Optional[dict] = None
    change_reason: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_consistency(self):
        # 植入物手术必须有植入物配置
        if self.is_implant_surgery and self.implant is None:
            raise ValueError("植入物手术必须填写植入物配置")
        # 麻醉：最多一个默认
        defaults = [a for a in self.anesthesia_rels if a.is_default]
        if len(defaults) > 1:
            raise ValueError("同一手术仅允许一个默认麻醉方式")
        # 必须至少一个麻醉方式
        if not self.anesthesia_rels:
            raise ValueError("手术必须至少配置一个麻醉方式")
        # 收费：必须有一个主收费项目
        primaries = [c for c in self.charge_rels if c.rel_type == "PRIMARY"]
        if len(primaries) > 1:
            raise ValueError("仅允许一个主收费项目")
        # 晶体：最多一个默认
        iol_defaults = [i for i in self.iol_rels if i.is_default]
        if len(iol_defaults) > 1:
            raise ValueError("仅允许一个默认晶体")
        # 级别与最低权限一致性
        level_rank = {"LEVEL_1": 1, "LEVEL_2": 2, "LEVEL_3": 3, "LEVEL_4": 4}
        if level_rank[self.min_surgery_level] > level_rank[self.surgery_level]:
            raise ValueError("最低手术权限级别不能高于手术本身级别")
        return self


class OperationUpdate(OperationBase):
    version: int = Field(..., ge=0)
    aliases: Optional[List[OperationAliasSchema]] = None
    anesthesia_rels: Optional[List[AnesthesiaRelSchema]] = None
    prepare_rules: Optional[List[PrepareRuleSchema]] = None
    exam_rels: Optional[List[ExamItemRelSchema]] = None
    lab_rels: Optional[List[LabItemRelSchema]] = None
    material_rels: Optional[List[MaterialRelSchema]] = None
    iol_rels: Optional[List[IolRelSchema]] = None
    implant: Optional[ImplantConfigSchema] = None
    staff_auths: Optional[List[StaffAuthSchema]] = None
    followup_rule: Optional[FollowupRuleSchema] = None
    charge_rels: Optional[List[ChargeRelSchema]] = None
    template_rels: Optional[List[TemplateRelSchema]] = None
    ext: Optional[dict] = None
    change_reason: Optional[str] = Field(None, max_length=500)


class OperationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    short_name: str
    icd9_code: Optional[str] = None
    operation_category: str
    operation_category_name: Optional[str] = None
    surgery_level: str
    surgery_level_name: Optional[str] = None
    eye_specialty: List[str] = []
    eye_specialty_names: List[str] = []
    duration_minutes: int
    is_refractive: bool = False
    refractive_type: Optional[str] = None
    is_day_surgery: bool = False
    is_outpatient_surgery: bool = False
    is_implant_surgery: bool = False
    need_chief_approve: bool = False
    need_followup: bool = True
    is_common: bool = False
    hotkey: Optional[str] = None
    status: str
    audit_status: str
    effective_date: Optional[date] = None
    updated_at: Optional[datetime] = None


class OperationDetail(OperationListItem):
    english_name: Optional[str] = None
    body_position: Optional[str] = None
    laterality_required: bool = True
    allow_bilateral: bool = False
    is_inpatient_surgery: bool = True
    is_emergency: bool = False
    is_minimally_invasive: bool = False
    duration_minutes_max: Optional[int] = None
    anesthesia_duration: Optional[int] = None
    prepare_hours: Optional[int] = None
    recovery_minutes: Optional[int] = None
    room_type_req: Optional[List[str]] = None
    equipment_ids: Optional[List[int]] = None
    need_refractive_record: bool = False
    need_navigation: bool = False
    default_implant_types: Optional[List[str]] = None
    followup_days: Optional[str] = None
    order_template_id: Optional[int] = None
    nursing_template_id: Optional[int] = None
    consent_template_id: Optional[int] = None
    charge_item_id: int
    include_material: bool = True
    allow_discount: bool = True
    min_surgery_level: str = "LEVEL_1"
    need_medical_affairs_approve: bool = False
    need_director_approve: bool = False
    auth_scope_type: str = "LEVEL"
    is_high_risk: bool = False
    risk_desc: Optional[str] = None
    sort_no: int = 999
    version: int = 0
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    # 子表
    aliases: List[OperationAliasSchema] = []
    anesthesia_rels: List[AnesthesiaRelSchema] = []
    prepare_rules: List[PrepareRuleSchema] = []
    exam_rels: List[ExamItemRelSchema] = []
    lab_rels: List[LabItemRelSchema] = []
    material_rels: List[MaterialRelSchema] = []
    iol_rels: List[IolRelSchema] = []
    implant: Optional[ImplantConfigSchema] = None
    staff_auths: List[StaffAuthSchema] = []
    followup_rule: Optional[FollowupRuleSchema] = None
    charge_rels: List[ChargeRelSchema] = []
    template_rels: List[TemplateRelSchema] = []
    ext: Optional[dict] = None


# ==================== 麻醉方式 ====================
class AnesthesiaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    english_name: Optional[str] = Field(None, max_length=128)
    anesthesia_type: Literal[
        "SURFACE", "LOCAL_INFILTRATION", "PERIBULBAR", "RETROBULBAR",
        "SUBTENON", "NERVE_BLOCK", "SEDATION", "SPINAL", "GENERAL", "COMBINED",
    ]
    anesthesia_level: Literal["LOCAL", "REGIONAL", "GENERAL"] = "LOCAL"
    is_eye_special: bool = False
    need_anesthetist: bool = True
    need_previsit: bool = False
    need_monitor: bool = True
    need_fasting: bool = False
    fasting_solid_hours: Optional[int] = Field(None, ge=0, le=48)
    fasting_liquid_hours: Optional[int] = Field(None, ge=0, le=24)
    injection_site: Optional[str] = Field(None, max_length=64)
    injection_depth: Optional[str] = Field(None, max_length=32)
    default_drug_ids: Optional[List[int]] = None
    base_charge_item_id: Optional[int] = None
    monitor_charge_item_id: Optional[int] = None
    extra_charge_ids: Optional[List[int]] = None
    anesthesia_record_template_id: Optional[int] = None
    anesthesia_consent_template_id: Optional[int] = None
    sort_no: int = 999
    remark: Optional[str] = Field(None, max_length=512)

    @model_validator(mode="after")
    def validate_anesthesia(self):
        if self.need_fasting:
            if self.fasting_solid_hours is None:
                raise ValueError("需禁食时必须设置禁食固体时间")
        # 表面麻醉通常不需要麻醉医生
        if self.anesthesia_type == "SURFACE" and self.need_anesthetist:
            # 警告级别，不阻止
            pass
        # 全麻必须需麻醉医生
        if self.anesthesia_type == "GENERAL" and not self.need_anesthetist:
            raise ValueError("全身麻醉必须需要麻醉医生")
        return self


class AnesthesiaCreate(AnesthesiaBase):
    code: Optional[str] = None
    drugs: List[dict] = []


class AnesthesiaUpdate(AnesthesiaBase):
    drugs: Optional[List[dict]] = None


# ==================== 手术权限校验（内部契约） ====================
class SurgeryAuthCheckRequest(BaseModel):
    operation_code: str
    surgeon_id: int
    assistant_ids: Optional[List[int]] = None
    anesthesia_code: Optional[str] = None
    laterality: Optional[Literal["LEFT", "RIGHT", "BOTH"]] = None


class SurgeryAuthCheckResult(BaseModel):
    allowed: bool
    operation_code: str
    operation_name: str
    surgeon_id: int
    surgeon_name: Optional[str] = None
    required_level: str
    surgeon_level: Optional[str] = None
    auth_scope_type: str = "LEVEL"
    in_whitelist: bool = False
    need_chief_approve: bool = False
    need_medical_affairs_approve: bool = False
    need_director_approve: bool = False
    reason: Optional[str] = None
    checks: List[dict] = []


# ==================== 手术完整配置（内部契约） ====================
class OperationFullConfig(BaseModel):
    """M01 → M09 的手术完整配置契约"""
    operation: dict
    anesthesia_options: List[dict] = []
    default_anesthesia: Optional[dict] = None
    prepare_rule: Optional[dict] = None
    exam_items: List[dict] = []
    lab_items: List[dict] = []
    materials: List[dict] = []
    iol_options: List[dict] = []
    implant_config: Optional[dict] = None
    auth_rule: dict = {}
    followup_rule: Optional[dict] = None
    charge_items: List[dict] = []
    templates: List[dict] = []
    version: str = ""
    computed_at: str = ""


# ==================== 查询 ====================
class OperationQuery(BaseModel):
    keyword: Optional[str] = None
    operation_category: Optional[List[str]] = None
    surgery_level: Optional[List[str]] = None
    eye_specialty: Optional[str] = None
    is_refractive: Optional[bool] = None
    refractive_type: Optional[str] = None
    is_day_surgery: Optional[bool] = None
    is_implant_surgery: Optional[bool] = None
    needs_approval: Optional[bool] = None
    is_common: Optional[bool] = None
    status: Optional[List[str]] = None
    audit_status: Optional[str] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)
    sort_by: str = "sort_no"
    sort_order: Literal["asc", "desc"] = "asc"
```

---

---

## 附录 A：表名与子模块速查

| 表名前缀 | 所属子模块 | 表数 |
|---|---|---|
| `md_anesthesia*` | 手术 | 2 |
| `md_charge_change/sync/code_*` | 收费 | 3 |
| `md_charge_combo*` | 收费 | 2 |
| `md_charge_item*` | 收费 | 7 |
| `md_discount_*` | 收费 | 3 |
| `md_invoice_*` | 收费 | 2 |
| `md_operation_*` | 手术 | 19 |
| `md_payment_*` | 收费 | 1 |
| `md_price_*` | 收费 | 6 |
| `md_refund_*` | 收费 | 1 |
| `md_surgery_level_rule` | 手术 | 1 |
| `mdm_department_*` | 科室 | 6 |
| `mdm_drug_*` | 药品 | 11 |
| `mdm_employee_*` | 职工 | 9 |
| `mdm_material_*` | 耗材 | 20 |
| `mdm_role_* / mdm_menu / mdm_permission_*` | 权限 | 26 |
| `mdm_surgery_kit*` | 耗材 | 2 |

---

## 附录 B：修订记录

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-19 | 首次汇总：合并 7 个子模块数据结构章节，共 121 张表 | 系统设计组 |
