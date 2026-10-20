# 二级眼科医院 HIS 系统 — M02 统一权限与安全
# 子模块数据结构：会话与 Token

**文档版本：** V1.0
**所属模块：** M02 统一权限与安全
**子模块：** 会话与 Token（Session & Token）
**主数据域：** 系统域（`SYS`）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M02 统一权限与安全 03 会话与Token 详细设计》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / PyJWT
**文档用途：** 作为「会话与 Token」表结构的独立参考手册与建表依据

---

## 文档说明

本文档由《[会话与Token详细设计](M02_统一权限与安全_03_会话与Token_详细设计.md)》第 4 章「数据结构设计」独立而来。

**相关文档：**

- [会话与Token详细设计](M02_统一权限与安全_03_会话与Token_详细设计.md) —— 业务模型、页面设计、接口设计、业务规则、验收标准
- [账号管理数据结构](M02_统一权限与安全_01_账号管理_数据结构.md) —— 账号主表（本模块依赖）
- [认证与登录数据结构](M02_统一权限与安全_02_认证与登录_数据结构.md) —— 登录配置（本模块依赖）
- [数据结构设计汇总](M02_统一权限与安全_数据结构设计汇总.md) —— 跨模块表清单与全局设计约定

> **章节编号：** 与原文第 4 章一致（`4.M`）。
> **表数量：** 6 张

---

## 目录

- [4.1 ER 关系图](#41-er-关系图)
- [4.2 表：`sys_session`（会话主表）](#42-表sys_session会话主表)
- [4.3 表：`sys_session_config`（会话配置表）](#43-表sys_session_config会话配置表)
- [4.4 表：`sys_jwt_key`（JWT 签名密钥表）](#44-表sys_jwt_keyjwt-签名密钥表)
- [4.5 表：`sys_token_blacklist`（Token 黑名单表）](#45-表sys_token_blacklisttoken-黑名单表)
- [4.6 表：`sys_session_log`（会话变更日志表）](#46-表sys_session_log会话变更日志表)
- [4.7 表：`sys_session_statistics`（会话统计表）](#47-表sys_session_statistics会话统计表)

---

## 表清单

| 编号 | 表名 | 中文名 |
|---|---|---|
| 4.2 | `sys_session` | 会话主表 |
| 4.3 | `sys_session_config` | 会话配置表 |
| 4.4 | `sys_jwt_key` | JWT 签名密钥表 |
| 4.5 | `sys_token_blacklist` | Token 黑名单表 |
| 4.6 | `sys_session_log` | 会话变更日志表 |
| 4.7 | `sys_session_statistics` | 会话统计表 |

---

## 4. 数据结构设计

### 4.1 ER 关系图

```
                    ┌──────────────────────────────────┐
                    │ sys_account（M02-01，账号主表）   │
                    └──────────┬───────────────────────┘
                               │ 1:N
                               ▼
        ┌──────────────────────────────────────────────┐
        │ sys_session（会话主表）                       │
        │  · session_id 唯一                            │
        │  · access_jti 当前 Access Token ID            │
        │  · refresh_hash Refresh Token 哈希            │
        │  · old_refresh_hash 上一版（重用检测）         │
        │  · status ACTIVE/EXPIRED/REVOKED              │
        └──────────┬───────────────────────────────────┘
                   │ 1:N
                   ▼
        ┌──────────────────────────────┐
        │ sys_session_log              │
        │ （会话变更日志）              │
        └──────────────────────────────┘

独立配置与支撑：
┌──────────────────────────────┐   ┌──────────────────────────────┐
│ sys_session_config           │   │ sys_jwt_key                  │
│ （会话配置，单行）             │   │ （签名密钥）                  │
└──────────────────────────────┘   └──────────────────────────────┘

┌──────────────────────────────┐   ┌──────────────────────────────┐
│ sys_token_blacklist          │   │ sys_session_statistics       │
│ （Token 黑名单，DB 兜底）      │   │ （会话统计，按日聚合）         │
└──────────────────────────────┘   └──────────────────────────────┘
```

**设计说明：**

- `sys_session.session_id` 为业务主键（Redis 与 DB 共用）
- `refresh_hash` 存 SHA-256，**不存明文**
- `old_refresh_hash` 用于**Refresh Token 重用检测**
- `sys_token_blacklist` 以 Redis 为主，DB 为持久化兜底
- `sys_jwt_key.secret_enc` 为**加密存储**，密钥来自 KMS/配置中心

### 4.2 表：`sys_session`（会话主表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| session_id | VARCHAR(64) | N | - | 会话唯一标识 `sess_{12hex}` |
| account_id | BIGINT | N | - | 账号 ID |
| username | VARCHAR(32) | N | - | 登录名（冗余） |
| staff_id | BIGINT | Y | NULL | 职工 ID（冗余） |
| staff_code | VARCHAR(32) | Y | NULL | 工号（冗余） |
| staff_name | VARCHAR(64) | Y | NULL | 姓名（冗余） |
| dept_id | BIGINT | Y | NULL | 科室 ID（冗余） |
| dept_name | VARCHAR(128) | Y | NULL | 科室名称（冗余） |
| org_id | BIGINT | N | 1 | 院区 ID |
| acct_type | VARCHAR(32) | N | 'EMPLOYEE' | 账号类型（冗余） |
| access_jti | VARCHAR(64) | Y | NULL | 当前 Access Token 的 jti |
| refresh_hash | VARCHAR(128) | N | - | Refresh Token SHA-256 |
| old_refresh_hash | VARCHAR(128) | Y | NULL | 上一版 Refresh 哈希（重用检测） |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/EXPIRED/REVOKED |
| login_type | VARCHAR(32) | N | 'PASSWORD' | 登录方式 |
| mfa_passed | BOOLEAN | N | FALSE | 是否通过二次验证 |
| mfa_method | VARCHAR(16) | Y | NULL | 二次验证方式：SMS/TOTP |
| login_ip | VARCHAR(64) | Y | NULL | 登录 IP |
| ip_location | VARCHAR(128) | Y | NULL | IP 归属地 |
| user_agent | VARCHAR(255) | Y | NULL | User-Agent |
| device_type | VARCHAR(16) | Y | NULL | 设备类型：PC/MOBILE/TABLET/API |
| device_id | VARCHAR(64) | Y | NULL | 设备指纹（同终端覆盖） |
| device_name | VARCHAR(128) | Y | NULL | 设备名称（解析后） |
| login_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 登录时间 |
| last_active_at | TIMESTAMP | Y | NULL | 最后活动时间 |
| expire_at | TIMESTAMP | N | - | 绝对过期时间 |
| idle_expire_at | TIMESTAMP | Y | NULL | 空闲过期时间 |
| refresh_count | INT | N | 0 | 刷新次数 |
| rotated_at | TIMESTAMP | Y | NULL | 最后轮换时间 |
| revoked_at | TIMESTAMP | Y | NULL | 吊销时间 |
| revoke_reason | VARCHAR(64) | Y | NULL | 吊销原因代码 |
| revoke_note | VARCHAR(500) | Y | NULL | 吊销说明 |
| revoked_by | BIGINT | Y | NULL | 吊销操作人（管理员时） |
| is_abnormal | BOOLEAN | N | FALSE | 是否异常会话 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引设计**

| 索引名 | 类型 | 字段 | 说明 |
|---|---|---|---|
| pk_sys_session | PRIMARY | id | 主键 |
| uk_session_id | UNIQUE | session_id | 会话 ID 唯一 |
| idx_session_account | NORMAL | account_id, status, last_active_at | 账号会话列表 |
| idx_session_refresh | NORMAL | refresh_hash | 刷新时查找 |
| idx_session_old_refresh | NORMAL | old_refresh_hash | 重用检测 |
| idx_session_jti | NORMAL | access_jti | 按 jti 查会话 |
| idx_session_status | NORMAL | status, expire_at | 过期扫描 |
| idx_session_idle | NORMAL | status, idle_expire_at | 空闲扫描 |
| idx_session_device | NORMAL | account_id, device_id, status | 同终端覆盖 |

**约束与设计说明**

```sql
-- 会话 ID 唯一
CREATE UNIQUE INDEX uk_session_id ON sys_session (session_id);

-- Refresh 哈希唯一（防止重复）
CREATE UNIQUE INDEX uk_session_refresh ON sys_session (refresh_hash)
    WHERE refresh_hash IS NOT NULL;

-- 只允许有状态
ALTER TABLE sys_session
    ADD CONSTRAINT ck_session_status
    CHECK (status IN ('ACTIVE', 'EXPIRED', 'REVOKED'));
```

**说明：**

- `refresh_hash` 存 **SHA-256**，不可逆
- `old_refresh_hash` 保存上一版哈希，用于**检测 Token 重用**
- `access_jti` 只保存**当前** Access Token 的 jti（历史 jti 进黑名单）
- `last_active_at` 高频更新，先写 Redis 后批量落库
- `device_id` 用于同终端重复登录覆盖判断

**分区：** 不分区（活跃会话 <2000，历史归档至冷表）

### 4.3 表：`sys_session_config`（会话配置表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键（固定 1） |
| access_token_ttl_min | INT | N | 30 | Access Token 有效期（分钟） |
| refresh_token_ttl_days | INT | N | 7 | Refresh Token 有效期（天） |
| idle_timeout_min | INT | N | 120 | 空闲超时（分钟） |
| absolute_timeout_days | INT | N | 7 | 绝对超时（天） |
| extend_idle_on_activity | BOOLEAN | N | TRUE | 活动时延长空闲计时 |
| max_sessions_per_account | INT | N | 5 | 单账号最大并发会话 |
| overflow_strategy | VARCHAR(16) | N | 'KICK_OLDEST' | 超限策略：KICK_OLDEST/REJECT |
| same_device_overwrite | BOOLEAN | N | TRUE | 同终端覆盖旧会话 |
| admin_unlimited | BOOLEAN | N | TRUE | 管理员不受并发限制 |
| refresh_rotation | BOOLEAN | N | TRUE | Refresh Token 轮换 |
| detect_token_reuse | BOOLEAN | N | TRUE | 检测 Token 重用 |
| extend_refresh_on_refresh | BOOLEAN | N | FALSE | 刷新时延长 Refresh 有效期 |
| use_blacklist | BOOLEAN | N | TRUE | 使用黑名单 |
| jwt_algorithm | VARCHAR(16) | N | 'HS256' | 签名算法 |
| current_key_id | VARCHAR(32) | Y | NULL | 当前签名密钥 ID |
| key_rotate_days | INT | N | 90 | 密钥轮换周期（天） |
| key_transition_min | INT | N | 30 | 密钥过渡期（分钟） |
| clock_leeway_seconds | INT | N | 60 | 时钟容忍（秒） |
| version_no | INT | N | 1 | 乐观锁版本号 |
| updated_by | BIGINT | Y | NULL | 更新人 |
| updated_by_name | VARCHAR(64) | Y | NULL | 更新人姓名 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `pk_session_config(id)` 主键。

**约束说明**

```sql
ALTER TABLE sys_session_config
    ADD CONSTRAINT ck_session_config_single_row CHECK (id = 1);

ALTER TABLE sys_session_config
    ADD CONSTRAINT ck_session_overflow
    CHECK (overflow_strategy IN ('KICK_OLDEST', 'REJECT'));
```

### 4.4 表：`sys_jwt_key`（JWT 签名密钥表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| kid | VARCHAR(32) | N | - | 密钥 ID（如 `k2026-04`） |
| secret_enc | VARCHAR(512) | N | - | 密钥密文（AES-256 加密） |
| algorithm | VARCHAR(16) | N | 'HS256' | 算法 |
| status | VARCHAR(16) | N | 'ACTIVE' | 状态：ACTIVE/RETIRING/RETIRED |
| effective_at | TIMESTAMP | N | - | 生效时间 |
| retiring_at | TIMESTAMP | Y | NULL | 进入过渡时间 |
| retired_at | TIMESTAMP | Y | NULL | 完全停用时间 |
| signed_count | BIGINT | N | 0 | 已签发 Token 数 |
| verify_count | BIGINT | N | 0 | 已验签次数 |
| created_by | BIGINT | Y | NULL | 创建人 |
| created_by_name | VARCHAR(64) | Y | NULL | 创建人姓名 |
| remark | VARCHAR(255) | Y | NULL | 备注 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | N | CURRENT_TIMESTAMP（触发器维护） | 更新时间 |

**索引：** `uk_jwt_kid(kid)` 唯一；`idx_jwt_status(status, effective_at)`。

**状态说明：**

| 状态 | 说明 | 可签发 | 可验签 |
|---|---|---|---|
| `ACTIVE` | 当前使用 | ✅ | ✅ |
| `RETIRING` | 过渡期（已停签，仍可验） | ❌ | ✅ |
| `RETIRED` | 完全停用 | ❌ | ❌ |

**唯一活跃约束：**

```sql
-- 同时只能有一个 ACTIVE 密钥
CREATE UNIQUE INDEX uk_jwt_active ON sys_jwt_key (status)
    WHERE status = 'ACTIVE';
```

### 4.5 表：`sys_token_blacklist`（Token 黑名单表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| jti | VARCHAR(64) | N | - | Token 唯一 ID |
| session_id | VARCHAR(64) | Y | NULL | 所属会话 |
| account_id | BIGINT | Y | NULL | 账号 ID |
| username | VARCHAR(32) | Y | NULL | 登录名 |
| reason | VARCHAR(64) | N | - | 加入原因（见 3.6/附录 C） |
| note | VARCHAR(500) | Y | NULL | 说明 |
| token_exp_at | TIMESTAMP | Y | NULL | Token 自然过期时间 |
| expire_at | TIMESTAMP | N | - | 黑名单失效时间 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| ip | VARCHAR(64) | Y | NULL | 操作 IP |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 加入时间 |

**索引：** `uk_blacklist_jti(jti)` 唯一；`idx_blacklist_expire(expire_at)`；`idx_blacklist_account(account_id, created_at)`；`idx_blacklist_session(session_id)`。

**说明：**
- **Redis 为第一查询源**，本表为持久化与重启恢复
- 记录保留 24 小时（TTL 超过 Token 有效期）
- 定时任务清理过期记录

### 4.6 表：`sys_session_log`（会话变更日志表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| session_id | VARCHAR(64) | N | - | 会话 ID |
| account_id | BIGINT | Y | NULL | 账号 ID |
| username | VARCHAR(32) | Y | NULL | 登录名 |
| action | VARCHAR(32) | N | - | 动作（见下表） |
| before_status | VARCHAR(16) | Y | NULL | 变更前状态 |
| after_status | VARCHAR(16) | Y | NULL | 变更后状态 |
| detail | VARCHAR(1000) | Y | NULL | 详情 |
| operator_id | BIGINT | Y | NULL | 操作人 |
| operator_name | VARCHAR(64) | Y | NULL | 操作人姓名 |
| ip | VARCHAR(64) | Y | NULL | 操作 IP |
| trace_id | VARCHAR(64) | Y | NULL | 链路 ID |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 记录时间 |

**索引：** `idx_session_log_sid(session_id, created_at)`；`idx_session_log_account(account_id, created_at)`；`idx_session_log_action(action, created_at)`。

**动作类型（`action`）：**

| 代码 | 说明 |
|---|---|
| `CREATE` | 创建会话 |
| `REFRESH` | 刷新 Token |
| `ROTATE` | Refresh 轮换 |
| `TOUCH` | 活动心跳 |
| `EXPIRE_IDLE` | 空闲超时 |
| `EXPIRE_ABSOLUTE` | 绝对超时 |
| `REVOKE_LOGOUT` | 主动登出 |
| `REVOKE_FORCE` | 强制下线 |
| `REVOKE_CONCURRENCY` | 并发超限 |
| `REVOKE_PASSWORD` | 密码修改 |
| `REVOKE_DISABLED` | 账号停用 |
| `REVOKE_REUSE` | Token 重用 |
| `BLACKLIST_ADD` | 加入黑名单 |
| `BLACKLIST_REMOVE` | 移除黑名单 |

**分区：** 按 `created_at` 月度 RANGE 分区，保留 **1 年**。

### 4.7 表：`sys_session_statistics`（会话统计表）

| 字段名 | 类型 | 允许空 | 默认 | 说明 |
|---|---|---|---|---|
| id | BIGINT | N | IDENTITY | 主键 |
| stat_date | DATE | N | - | 统计日期 |
| dimension | VARCHAR(16) | N | 'GLOBAL' | 维度：GLOBAL/ACCOUNT/DEPT/DEVICE |
| dimension_key | VARCHAR(128) | Y | NULL | 维度值 |
| session_count | INT | N | 0 | 会话总数 |
| active_count | INT | N | 0 | 活跃会话数 |
| peak_concurrent | INT | N | 0 | 峰值并发 |
| avg_duration_sec | INT | Y | NULL | 平均时长（秒） |
| total_refresh | INT | N | 0 | 刷新总次数 |
| revoke_logout | INT | N | 0 | 主动登出数 |
| revoke_idle | INT | N | 0 | 空闲超时数 |
| revoke_absolute | INT | N | 0 | 绝对超时数 |
| revoke_force | INT | N | 0 | 强制下线数 |
| revoke_concurrency | INT | N | 0 | 并发超限数 |
| revoke_reuse | INT | N | 0 | Token 重用数 |
| created_at | TIMESTAMP | N | CURRENT_TIMESTAMP | 创建时间 |

**索引：** `uk_session_stat(stat_date, dimension, dimension_key)` 唯一；`idx_session_stat_date(stat_date, dimension)`。

**说明：** 每日 01:30 从 `sys_session` 与 `sys_session_log` 聚合。

### 4.8 SQLAlchemy 2.0 模型定义

```python
# app/models/auth/session.py
"""会话与 Token ORM 模型"""
import hashlib
import secrets
from datetime import date, datetime, timedelta
from typing import Optional, List

from sqlalchemy import (
    BigInteger, String, Integer, Boolean, Date, DateTime,
    Index, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SysSession(Base, TimestampMixin):
    """会话主表"""
    __tablename__ = "sys_session"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="会话标识")

    # 账号信息（冗余，避免每次查 M02-01）
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(32), nullable=False)
    staff_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    staff_code: Mapped[Optional[str]] = mapped_column(String(32))
    staff_name: Mapped[Optional[str]] = mapped_column(String(64))
    dept_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    dept_name: Mapped[Optional[str]] = mapped_column(String(128))
    org_id: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    acct_type: Mapped[str] = mapped_column(String(32), default="EMPLOYEE", nullable=False)

    # Token
    access_jti: Mapped[Optional[str]] = mapped_column(String(64), comment="当前 Access jti")
    refresh_hash: Mapped[str] = mapped_column(String(128), nullable=False, comment="Refresh SHA-256")
    old_refresh_hash: Mapped[Optional[str]] = mapped_column(String(128), comment="上一版（重用检测）")

    # 状态
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)
    login_type: Mapped[str] = mapped_column(String(32), default="PASSWORD", nullable=False)
    mfa_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_method: Mapped[Optional[str]] = mapped_column(String(16))

    # 登录环境
    login_ip: Mapped[Optional[str]] = mapped_column(String(64))
    ip_location: Mapped[Optional[str]] = mapped_column(String(128))
    user_agent: Mapped[Optional[str]] = mapped_column(String(255))
    device_type: Mapped[Optional[str]] = mapped_column(String(16))
    device_id: Mapped[Optional[str]] = mapped_column(String(64))
    device_name: Mapped[Optional[str]] = mapped_column(String(128))

    # 时间
    login_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="绝对过期")
    idle_expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="空闲过期")

    # 刷新
    refresh_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 吊销
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    revoke_reason: Mapped[Optional[str]] = mapped_column(String(64))
    revoke_note: Mapped[Optional[str]] = mapped_column(String(500))
    revoked_by: Mapped[Optional[int]] = mapped_column(BigInteger)

    is_abnormal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("session_id", name="uk_session_id"),
        Index("idx_session_account", "account_id", "status", "last_active_at"),
        Index("idx_session_refresh", "refresh_hash"),
        Index("idx_session_old_refresh", "old_refresh_hash"),
        Index("idx_session_jti", "access_jti"),
        Index("idx_session_status", "status", "expire_at"),
        Index("idx_session_idle", "status", "idle_expire_at"),
        Index("idx_session_device", "account_id", "device_id", "status"),
        {"comment": "会话主表"},
    )

    STATUS_LABELS = {"ACTIVE": "活跃", "EXPIRED": "已过期", "REVOKED": "已吊销"}

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """会话是否有效"""
        now = now or datetime.now()
        if self.status != "ACTIVE":
            return False
        if self.expire_at <= now:
            return False
        if self.idle_expire_at and self.idle_expire_at <= now:
            return False
        return True

    def remaining_seconds(self, now: Optional[datetime] = None) -> int:
        """剩余秒数"""
        now = now or datetime.now()
        return max(0, int((self.expire_at - now).total_seconds()))

    def idle_remaining_seconds(self, now: Optional[datetime] = None) -> int:
        """空闲剩余秒数"""
        if not self.idle_expire_at:
            return -1
        now = now or datetime.now()
        return max(0, int((self.idle_expire_at - now).total_seconds()))

    @staticmethod
    def hash_refresh(raw: str) -> str:
        """计算 Refresh Token 哈希"""
        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def new_refresh_token(account_id: int) -> tuple:
        """生成新 Refresh Token，返回 (明文, 哈希)"""
        raw = secrets.token_hex(32)
        return f"rt_{raw}_{account_id}", hashlib.sha256(raw.encode()).hexdigest()


class SysSessionConfig(Base):
    """会话配置（单行）"""
    __tablename__ = "sys_session_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    access_token_ttl_min: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    refresh_token_ttl_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    idle_timeout_min: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    absolute_timeout_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    extend_idle_on_activity: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    max_sessions_per_account: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    overflow_strategy: Mapped[str] = mapped_column(
        String(16), default="KICK_OLDEST", nullable=False)
    same_device_overwrite: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin_unlimited: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    refresh_rotation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    detect_token_reuse: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    extend_refresh_on_refresh: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    use_blacklist: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    jwt_algorithm: Mapped[str] = mapped_column(String(16), default="HS256", nullable=False)
    current_key_id: Mapped[Optional[str]] = mapped_column(String(32))
    key_rotate_days: Mapped[int] = mapped_column(Integer, default=90, nullable=False)
    key_transition_min: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    clock_leeway_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    version_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    updated_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        {"comment": "会话配置（单行）"},
    )


class SysJwtKey(Base):
    """JWT 签名密钥"""
    __tablename__ = "sys_jwt_key"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kid: Mapped[str] = mapped_column(String(32), nullable=False)
    secret_enc: Mapped[str] = mapped_column(String(512), nullable=False, comment="AES-256 加密")
    algorithm: Mapped[str] = mapped_column(String(16), default="HS256", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", nullable=False)

    effective_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    retiring_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    retired_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    signed_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    verify_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    created_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_by_name: Mapped[Optional[str]] = mapped_column(String(64))
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("kid", name="uk_jwt_kid"),
        Index("idx_jwt_status", "status", "effective_at"),
        {"comment": "JWT 签名密钥"},
    )

    def can_sign(self) -> bool:
        return self.status == "ACTIVE"

    def can_verify(self) -> bool:
        return self.status in ("ACTIVE", "RETIRING")


class SysTokenBlacklist(Base):
    """Token 黑名单"""
    __tablename__ = "sys_token_blacklist"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[Optional[str]] = mapped_column(String(64))
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    username: Mapped[Optional[str]] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(500))
    token_exp_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    expire_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    ip: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("jti", name="uk_blacklist_jti"),
        Index("idx_blacklist_expire", "expire_at"),
        Index("idx_blacklist_account", "account_id", "created_at"),
        Index("idx_blacklist_session", "session_id"),
        {"comment": "Token 黑名单（Redis 为主，DB 兜底）"},
    )

    def is_expired(self) -> bool:
        return self.expire_at <= datetime.now()


class SysSessionLog(Base):
    """会话变更日志"""
    __tablename__ = "sys_session_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    username: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before_status: Mapped[Optional[str]] = mapped_column(String(16))
    after_status: Mapped[Optional[str]] = mapped_column(String(16))
    detail: Mapped[Optional[str]] = mapped_column(String(1000))
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    operator_name: Mapped[Optional[str]] = mapped_column(String(64))
    ip: Mapped[Optional[str]] = mapped_column(String(64))
    trace_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_session_log_sid", "session_id", "created_at"),
        Index("idx_session_log_account", "account_id", "created_at"),
        Index("idx_session_log_action", "action", "created_at"),
        {"comment": "会话变更日志"},
    )


class SysSessionStatistics(Base):
    """会话统计"""
    __tablename__ = "sys_session_statistics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    dimension: Mapped[str] = mapped_column(String(16), default="GLOBAL", nullable=False)
    dimension_key: Mapped[Optional[str]] = mapped_column(String(128))
    session_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peak_concurrent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration_sec: Mapped[Optional[int]] = mapped_column(Integer)
    total_refresh: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_logout: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_idle: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_absolute: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_force: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_concurrency: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    revoke_reuse: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("stat_date", "dimension", "dimension_key",
                         name="uk_session_stat"),
        Index("idx_session_stat_date", "stat_date", "dimension"),
        {"comment": "会话统计（按日聚合）"},
    )

    def total_revoke(self) -> int:
        return (self.revoke_logout + self.revoke_idle + self.revoke_absolute
                + self.revoke_force + self.revoke_concurrency + self.revoke_reuse)
```

### 4.9 Pydantic Schema 定义

```python
# app/schemas/auth/token.py
"""会话与 Token Pydantic Schema"""
from datetime import date, datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


SESSION_STATUS = Literal["ACTIVE", "EXPIRED", "REVOKED"]


# ==================== Token 操作 ====================
class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10, max_length=200)
    device_id: Optional[str] = Field(None, max_length=64)

    @field_validator("refresh_token")
    @classmethod
    def validate_format(cls, v):
        parts = v.split("_")
        if len(parts) != 3 or parts[0] != "rt":
            raise ValueError("Refresh Token 格式无效")
        return v


class VerifyRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=4096)


class RevokeRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    notify_user: bool = True


class BatchRevokeRequest(BaseModel):
    session_ids: List[str] = Field(..., min_length=1, max_length=200)
    reason: str = Field(..., min_length=5, max_length=500)
    notify_user: bool = True


class RevokeAccountRequest(BaseModel):
    account_id: int
    reason: str = Field(..., min_length=5, max_length=500)
    exclude_session_id: Optional[str] = None
    notify_user: bool = True


# ==================== 会话查询 ====================
class SessionQuery(BaseModel):
    username: Optional[str] = None
    account_id: Optional[int] = None
    status: Optional[List[str]] = None
    login_ip: Optional[str] = None
    device_type: Optional[str] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=200)


class SessionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    account_id: int
    username: str
    staff_name: Optional[str] = None
    dept_name: Optional[str] = None
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    login_ip: Optional[str] = None
    ip_location: Optional[str] = None
    login_type: str = "PASSWORD"
    status: str
    login_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    expire_at: Optional[datetime] = None
    idle_expire_at: Optional[datetime] = None
    refresh_count: int = 0


class MySessionItem(BaseModel):
    session_id: str
    is_current: bool = False
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    login_ip: Optional[str] = None
    ip_location: Optional[str] = None
    login_at: Optional[datetime] = None
    last_active_at: Optional[datetime] = None
    last_active_text: Optional[str] = None
    expire_at: Optional[datetime] = None
    idle_expire_at: Optional[datetime] = None
    is_abnormal: bool = False


class SessionDetail(SessionItem):
    staff_id: Optional[int] = None
    staff_code: Optional[str] = None
    dept_id: Optional[int] = None
    org_id: int = 1
    acct_type: str = "EMPLOYEE"
    mfa_passed: bool = False
    mfa_method: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    access_jti: Optional[str] = None
    remaining_seconds: int = 0
    idle_remaining_seconds: int = 0
    rotated_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    revoke_note: Optional[str] = None
    is_abnormal: bool = False


# ==================== Token 响应 ====================
class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_expires_in: int
    session_id: str


class TokenValidateResult(BaseModel):
    valid: bool
    account_id: Optional[int] = None
    username: Optional[str] = None
    staff_id: Optional[int] = None
    staff_code: Optional[str] = None
    staff_name: Optional[str] = None
    dept_id: Optional[int] = None
    dept_name: Optional[str] = None
    org_id: Optional[int] = None
    acct_type: Optional[str] = None
    auth_level: int = 0
    mfa_passed: bool = False
    session_id: Optional[str] = None
    jti: Optional[str] = None
    issued_at: Optional[str] = None
    expires_at: Optional[str] = None
    remaining_seconds: int = 0
    need_refresh: bool = False
    # 失败时
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    revoked_reason: Optional[str] = None


# ==================== 配置 ====================
class SessionConfigUpdate(BaseModel):
    access_token_ttl_min: int = Field(30, ge=5, le=120)
    refresh_token_ttl_days: int = Field(7, ge=1, le=30)
    idle_timeout_min: int = Field(120, ge=15, le=1440)
    absolute_timeout_days: int = Field(7, ge=1, le=90)
    extend_idle_on_activity: bool = True
    max_sessions_per_account: int = Field(5, ge=1, le=50)
    overflow_strategy: Literal["KICK_OLDEST", "REJECT"] = "KICK_OLDEST"
    same_device_overwrite: bool = True
    admin_unlimited: bool = True
    refresh_rotation: bool = True
    detect_token_reuse: bool = True
    extend_refresh_on_refresh: bool = False
    use_blacklist: bool = True
    key_rotate_days: int = Field(90, ge=30, le=365)
    key_transition_min: int = Field(30, ge=5, le=120)
    clock_leeway_seconds: int = Field(60, ge=0, le=300)
    version_no: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_config(self):
        # 绝对超时不应短于空闲超时
        if self.absolute_timeout_days * 1440 < self.idle_timeout_min:
            raise ValueError("绝对超时时长不能短于空闲超时时长")
        # Refresh 不应短于 Access 的 10 倍
        if self.refresh_token_ttl_days * 1440 < self.access_token_ttl_min * 10:
            raise ValueError("Refresh 有效期过短，应至少为 Access 的 10 倍")
        return self


class SessionConfigDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = 1
    access_token_ttl_min: int = 30
    refresh_token_ttl_days: int = 7
    idle_timeout_min: int = 120
    absolute_timeout_days: int = 7
    extend_idle_on_activity: bool = True
    max_sessions_per_account: int = 5
    overflow_strategy: str = "KICK_OLDEST"
    same_device_overwrite: bool = True
    admin_unlimited: bool = True
    refresh_rotation: bool = True
    detect_token_reuse: bool = True
    extend_refresh_on_refresh: bool = False
    use_blacklist: bool = True
    jwt_algorithm: str = "HS256"
    current_key_id: Optional[str] = None
    key_rotate_days: int = 90
    key_transition_min: int = 30
    clock_leeway_seconds: int = 60
    version_no: int = 1
    updated_at: Optional[datetime] = None


# ==================== 密钥 ====================
class RotateKeyRequest(BaseModel):
    kid: Optional[str] = Field(None, max_length=32)
    transition_minutes: int = Field(30, ge=5, le=120)

    @field_validator("kid")
    @classmethod
    def validate_kid(cls, v):
        if v is None:
            return v
        import re
        if not re.match(r"^k\d{4}-\d{2}$", v):
            raise ValueError("密钥 ID 格式应为 kYYYY-MM")
        return v


class JwtKeyItem(BaseModel):
    kid: str
    status: str
    effective_at: Optional[datetime] = None
    retiring_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
    signed_count: int = 0
    verify_count: int = 0
    can_sign: bool = False
    can_verify: bool = False


# ==================== 黑名单 ====================
class BlacklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    jti: str
    session_id: Optional[str] = None
    account_id: Optional[int] = None
    username: Optional[str] = None
    reason: str
    note: Optional[str] = None
    expire_at: datetime
    operator_name: Optional[str] = None
    created_at: Optional[datetime] = None


# ==================== 内部契约 ====================
class CreateSessionRequest(BaseModel):
    account_id: int
    staff_id: Optional[int] = None
    username: str = Field(..., max_length=32)
    staff_code: Optional[str] = Field(None, max_length=32)
    staff_name: Optional[str] = Field(None, max_length=64)
    dept_id: Optional[int] = None
    dept_name: Optional[str] = Field(None, max_length=128)
    org_id: int = 1
    acct_type: str = "EMPLOYEE"
    login_ip: Optional[str] = Field(None, max_length=64)
    user_agent: Optional[str] = Field(None, max_length=255)
    device_type: Optional[Literal["PC", "MOBILE", "TABLET", "API"]] = None
    device_id: Optional[str] = Field(None, max_length=64)
    login_type: Literal["PASSWORD", "SMS", "QRCODE", "SSO", "CA"] = "PASSWORD"
    mfa_passed: bool = False


class CreateSessionResult(BaseModel):
    session_id: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_expires_in: int
    idle_expire_at: Optional[datetime] = None
    kicked_session_ids: List[str] = []
```

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-19 | 首次发布：6 张表 | 系统设计组 |
