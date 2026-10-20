# 二级眼科医院 HIS 系统 — M02 统一权限与安全
# 子模块：会话与 Token（Session & Token）详细设计

**文档版本：** V1.0
**所属模块：** M02 统一权限与安全（子模块编号 M02-03 会话与 Token）
**设计依据：** 《二级眼科医院HIS系统总体功能模块设计》《M02-02 认证与登录详细设计》
**技术栈：** Python 3.11+ / FastAPI / SQLAlchemy 2.0 / PostgreSQL 16 / Redis 7 / PyJWT
**文档用途：** 作为会话与 Token 子模块开发、测试、验收依据；作为全院身份传递的运行时基础

---

## 目录

1. [模块概述](#1-模块概述)
2. [业务范围与边界](#2-业务范围与边界)
3. [会话与 Token 模型](#3-会话与-token-模型)
4. [数据结构设计](#4-数据结构设计)
5. [页面设计](#5-页面设计)
6. [后端接口设计](#6-后端接口设计)
7. [缓存与异步任务设计](#7-缓存与异步任务设计)
8. [业务规则与校验](#8-业务规则与校验)
9. [权限与安全](#9-权限与安全)
10. [集成与契约](#10-集成与契约)
11. [异常处理与日志](#11-异常处理与日志)
12. [验收标准](#12-验收标准)

---

## 1. 模块概述

### 1.1 模块定位

会话与 Token 是**身份传递的载体**。M02-02 确认了"你是谁"，本子模块负责"**如何让系统在后续每次请求中都记住你是谁**"。

```
M02-02 认证通过
      ↓
┌────────────────────────────────────────────────┐
│ M02-03 会话与 Token（本文档）                   │
│  1. 创建会话（session_id）                      │
│  2. 签发 Access Token（短期，含身份声明）        │
│  3. 签发 Refresh Token（长期，用于续期）        │
│  4. 维护会话状态与活跃列表                      │
│  5. 提供校验、刷新、吊销能力                    │
└──────────────────┬─────────────────────────────┘
                   │ 每次业务请求携带 Access Token
                   ▼
┌────────────────────────────────────────────────┐
│ M02-04 权限运行时引擎                           │
│  解析 Token → 取身份 → 校验权限                 │
└────────────────────────────────────────────────┘
```

| 职责 | 归属 |
|---|---|
| 确认"你是谁" | M02-02 |
| **签发 Token** | **M02-03 本子模块** |
| **Token 结构、签名、过期** | **M02-03 本子模块** |
| **会话生命周期** | **M02-03 本子模块** |
| **Token 刷新** | **M02-03 本子模块** |
| **Token 吊销（登出/强制下线）** | **M02-03 本子模块** |
| **并发会话控制** | M02-07 定策略，M02-03 执行 |
| **解析 Token、判断权限** | M02-04 |
| **账号状态校验** | M02-01 |

> **一句话边界**：本子模块只管"**发证、验真、作废**"，**不管"能做什么"**（那是 M02-04）。

### 1.2 模块目标

- **无状态与有状态结合**：JWT 自包含身份，会话表支持主动吊销。
- **双 Token 机制**：Access 短期（30 分钟），Refresh 长期（7 天）。
- **可即时吊销**：登出、密码修改、账号停用后 Token 立即失效。
- **多端会话可视**：用户可查看并踢出其他设备。
- **防重放**：Token 含 `jti`，支持黑名单。
- **平滑刷新**：Refresh 时轮换 Token（Refresh Token Rotation）。
- **审计完整**：会话创建、刷新、吊销全部留痕。

### 1.3 关键业务角色

| 角色 | 职责 | 主要操作 |
|---|---|---|
| 全部系统用户 | 使用 | 登录后自动获得会话、查看/踢出其他会话 |
| 系统管理员 | 会话运维 | 查看全部会话、强制下线 |
| 信息科长 | 安全策略 | 配置会话超时、并发上限 |
| 审计员 | 追溯 | 查看会话历史 |

---

## 2. 业务范围与边界

### 2.1 范围内

| 范围 | 说明 |
|---|---|
| 会话创建 | 登录成功后创建 |
| Access Token 签发 | JWT，30 分钟 |
| Refresh Token 签发 | 随机串，7 天 |
| Token 校验 | 签名、过期、状态、黑名单 |
| Token 刷新 | Refresh Token 换新 Access Token |
| Refresh 轮换 | 每次刷新生成新 Refresh Token |
| Token 吊销 | 登出、改密、停用、强制下线 |
| 会话列表 | 用户查看自己的会话 |
| 会话踢出 | 用户踢出其他设备 |
| 并发会话控制 | 超限时踢最旧 |
| 空闲超时 | 无操作自动失效 |
| 会话续期 | 活动时延长空闲计时 |
| Token 黑名单 | 已吊销但未过期的 Token |

### 2.2 范围外（由其他模块负责）

| 范围外内容 | 负责方 | 说明 |
|---|---|---|
| 认证（确认身份） | **M02-02** | 本子模块只接收认证结果 |
| 账号状态 | **M02-01** | 本子模块调用校验 |
| 权限计算与校验 | **M02-04** | 本子模块只提供身份声明 |
| 权限上下文内容 | **M01 权限** | M02-04 拉取 |
| 二次验证 | **M02-05** | — |
| 审计日志存储 | **M02-06** | 本子模块产生事件 |
| IP 白名单、区域限制 | **M02-07** | — |
| 单点登出（SSO） | M21 集成平台 | 预留 |
| 密码管理 | M02-01 | — |

### 2.3 依赖关系

```
        ┌────────────────────────────────────────┐
        │  M02-03 会话与 Token                    │
        └──────────┬─────────────────────────────┘
                   │
    ┌──────────────┼──────────────┬───────────────┐
    │ 上游           │              │ 下游（依赖本模块）
    ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────────────────┐
│M02-02   │  │M02-01    │  │ M02-04 权限引擎（解析Token）│
│登录成功  │  │账号状态   │  │ 全部业务模块（携带Token）   │
│         │  │          │  │ M02-06 审计（会话事件）    │
└─────────┘  └──────────┘  │ M02-07 安全策略（并发/白名单）│
                           └──────────────────────────┘
```

---

## 3. 会话与 Token 模型

### 3.1 双 Token 机制

| 项 | Access Token | Refresh Token |
|---|---|---|
| 格式 | JWT（HS256） | 随机串（64 位 hex） |
| 有效期 | **30 分钟** | **7 天** |
| 存储位置 | 前端内存 / localStorage | 前端 localStorage / HttpOnly Cookie |
| 用途 | 访问业务接口 | 换取新 Access Token |
| 是否可吊销 | 通过黑名单 | 通过数据库状态 |
| 携带信息 | 身份声明（不含量限） | 仅作凭证 |
| 刷新行为 | — | **每次刷新都轮换** |

**为什么这样设计：**

| 决策 | 理由 |
|---|---|
| Access 短期 | 即使泄露，危害窗口仅 30 分钟 |
| Refresh 长期 | 避免频繁重新登录 |
| Access 用 JWT | 业务模块可本地验签，无需每次查库 |
| Refresh 用随机串 | 可随时作废，不依赖过期时间 |
| Refresh 轮换 | 检测 Token 被盗用（旧 Refresh 失效） |

### 3.2 Access Token 结构

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT",
    "kid": "k2026-04"
  },
  "payload": {
    "iss": "m02-auth",
    "sub": "1024",
    "aud": "his-api",
    "exp": 1743500625,
    "iat": 1743498825,
    "nbf": 1743498825,
    "jti": "at_7f3a2b1c9d4e5f6a",
    "sid": "sess_9e8d7c6b5a4f",
    "typ": "access",
    "usr": "wangwu",
    "staff_id": 1024,
    "staff_code": "E24030017",
    "staff_name": "王五",
    "dept_id": 15,
    "dept_name": "白内障科",
    "org_id": 1,
    "acct_type": "EMPLOYEE",
    "auth_level": 2,
    "mfa_passed": true
  },
  "signature": "..."
}
```

**字段说明：**

| 字段 | 说明 | 是否必需 |
|---|---|---|
| `iss` | 签发者（固定 `m02-auth`） | 是 |
| `sub` | 主体（account_id） | 是 |
| `aud` | 受众（`his-api`） | 是 |
| `exp` | 过期时间 | 是 |
| `iat` | 签发时间 | 是 |
| `nbf` | 生效时间 | 是 |
| `jti` | Token 唯一 ID（防重放） | 是 |
| `sid` | 会话 ID | 是 |
| `typ` | Token 类型（`access`） | 是 |
| `usr` | 登录名 | 是 |
| `staff_id` | 职工 ID | 否 |
| `staff_code` | 工号 | 否 |
| `staff_name` | 姓名 | 是 |
| `dept_id` | 科室 ID | 否 |
| `dept_name` | 科室名称 | 否 |
| `org_id` | 院区 ID | 是 |
| `acct_type` | 账号类型 | 是 |
| `auth_level` | 认证级别（0=仅密码，1=密码+手机，2=密码+MFA） | 是 |
| `mfa_passed` | 是否已过二次验证 | 是 |

> **关键设计：Access Token 中不含权限列表**。原因：
> 1. 权限变更频繁，若写入 Token 会导致权限变更后 Token 陈旧（最长 30 分钟）。
> 2. 权限列表可能很大（数百个 perm_code），每次请求携带会显著增加带宽。
> 3. M02-04 通过 `account_id` 从缓存取权限，O(1) 且始终最新。

### 3.3 Refresh Token 结构

```
格式：rt_{64位hex}_{account_id}
示例：rt_7f3a2b1c9d4e5f6a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a_1024
```

**存储：** 数据库 `sys_session.refresh_token_hash`（SHA-256 哈希）。

**轮换机制：**

```
1. 客户端携带 refresh_token 请求刷新
   ↓
2. 服务端计算哈希，查 sys_session
   ├─ 找不到 → 令牌无效（可能被盗用后已被轮换）
   ├─ 已轮换（is_rotated=true）→ **检测到令牌重用** → 吊销整个会话
   └─ 有效 → 继续
   ↓
3. 生成新 Refresh Token，旧 Token 标记 is_rotated=true
   ↓
4. 返回新 Access + 新 Refresh
```

**令牌重用检测：** 若客户端使用了已轮换的 Refresh Token，说明该 Token 可能已泄露（真实用户用的是新 Token），此时**立即吊销整个会话**并要求重新登录。

### 3.4 会话模型

```
┌──────────────────────────────────────────────────────────────┐
│ sys_session                                                  │
│  · session_id     唯一会话标识                                │
│  · account_id     归属账号                                    │
│  · access_jti     当前 Access Token 的 jti                    │
│  · refresh_hash   Refresh Token 哈希                          │
│  · status         ACTIVE/EXPIRED/REVOKED                      │
│  · expire_at      Refresh Token 绝对过期时间                  │
│  · idle_expire_at 空闲过期时间（活动时延长）                   │
│  · last_active_at 最后活动时间                                │
└──────────────────────────────────────────────────────────────┘
```

#### 3.4.1 会话状态

| 状态 | 说明 | 可否使用 Token |
|---|---|---|
| `ACTIVE` | 活跃 | ✅ |
| `EXPIRED` | 已过期 | ❌ |
| `REVOKED` | 已吊销 | ❌ |

#### 3.4.2 过期机制（双保险）

| 机制 | 说明 | 默认值 |
|---|---|---|
| **绝对过期** | 从登录起算，到点必失效 | 7 天 |
| **空闲过期** | 无操作超时 | 2 小时 |

**计算方式：**
- `expire_at = login_at + 7 天`（固定，不因活动延长）
- `idle_expire_at = last_active_at + 2 小时`（每次有请求时刷新）
- 两者任一到期即会话失效

**设计理由：**
- 绝对过期：防止会话永久存在
- 空闲过期：防止终端被遗忘后长期可用（医院公共终端场景）

#### 3.4.3 会话续期

每次业务请求携带有效 Access Token 时：

```
1. 更新 sys_session.last_active_at = now
2. 更新 idle_expire_at = now + 2h
3. 通过 Redis 异步更新（避免每次写库）
4. 每 5 分钟批量落库一次
```

> **性能优化**：会话活动时间是**高频写**操作，不能每次请求都写 DB。采用 Redis 缓冲 + 定时批量落库。

### 3.5 并发会话控制

| 策略 | 参数 | 说明 |
|---|---|---|
| 单账号最大并发会话 | `SYS.SESSION.MAX_PER_ACCOUNT`（默认 5） | 超出时**踢最旧** |
| 同一终端最大会话 | 1 | 相同 device_id 覆盖旧会话 |
| 管理员会话 | 不限制 | — |

**行为：**

```
新登录 → 会话数 > 上限？
   ├─ 否 → 正常创建
   └─ 是 → 找出 last_active_at 最早的会话 → 吊销 → 创建新会话
         → 被踢会话收到通知（通过 WebSocket 或下次请求时返回 401 + 特定码）
```

### 3.6 Token 黑名单

**目的：** 已吊销的 Access Token 在自然过期前仍需拒绝。

| 项 | 方案 |
|---|---|
| 存储 | Redis `sys:token:blacklist:{jti}` → 过期时间戳 |
| TTL | 等于 Access Token 剩余有效期（最长 30 分钟） |
| 查询 | 每次验签后检查（O(1)） |
| 何时加入 | 登出、强制下线、改密、账号停用 |
| 清理 | Redis 自动过期 |

**为什么不用数据库：** 黑名单是高频读、短生命周期数据，Redis 天然适配。

### 3.7 签名密钥管理

| 项 | 方案 |
|---|---|
| 算法 | HS256（HMAC-SHA256） |
| 密钥长度 | 256 位（32 字节随机） |
| 存储 | 配置中心 / 环境变量，**不入代码库** |
| 轮换 | 每季度轮换，`kid` 标识密钥版本 |
| 轮换兼容 | 保留上一个密钥 30 分钟，支持平滑过渡 |
| 密钥列表 | `sys_jwt_key` 表记录版本与状态 |

**轮换流程：**

```
1. 生成新密钥，写入 sys_jwt_key（kid=k2026-07，status=ACTIVE）
2. 旧密钥改为 status=RETIRING（仍可用于验签）
3. 新签发 Token 使用新密钥
4. 30 分钟后旧密钥 status=RETIRED（不再验签）
```

---

## 4. 数据结构设计

> **📌 本章已独立成册：** [会话与Token数据结构](M02_统一权限与安全_03_会话与Token_数据结构.md)

本章原包含 **6 张表**的完整定义（字段、索引、约束、SQLAlchemy 2.0 模型、Pydantic Schema），现已独立至上述文件，本文档不再重复。

**查阅方式：**

| 需求 | 文档 | 章节 |
|---|---|---|
| 会话与Token模块完整数据结构 | [会话与Token数据结构](M02_统一权限与安全_03_会话与Token_数据结构.md) | 第 4 章全文 |
| 跨模块表清单与全局规范 | [数据结构设计汇总](M02_统一权限与安全_数据结构设计汇总.md) | 第 1 章 |

> 表结构变更时，**以独立数据结构文件为准**，并同步更新汇总文档。

---

## 5. 页面设计

### 5.1 页面结构总览

```
会话与 Token
├── P01 我的会话（核心页，用户自助）
├── P02 全部会话（管理员）
├── P03 会话详情
├── P04 会话配置
├── P05 Token 黑名单
├── P06 签名密钥管理
├── P07 会话历史
└── P08 强制下线确认弹窗
```

### 5.2 P01 我的会话

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 我的登录设备                                                                   │
├────────────────────────────────────────────────────────────────────────────────┤
│ 当前在线 3 个设备                                              [全部下线]      │
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────────┐  │
│ │ 💻 当前设备                                            [当前]            │  │
│ │ Chrome 120 / Windows 10                                                  │  │
│ │ IP：192.168.10.55（院内网络）                                            │  │
│ │ 登录时间：2026-04-01 10:23                                               │  │
│ │ 最后活动：刚刚                                                           │  │
│ │ 登录地点：白内障科诊室                                                   │  │
│ └──────────────────────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────────────────────┐  │
│ │ 📱 移动设备                                                    [下线]    │  │
│ │ Safari / iOS 17                                                          │  │
│ │ IP：192.168.10.88（院内网络）                                            │  │
│ │ 登录时间：2026-03-31 09:15                                               │  │
│ │ 最后活动：2 小时前                                                       │  │
│ └──────────────────────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────────────────────┐  │
│ │ 💻 其他设备                                                    [下线]    │  │
│ │ Chrome 119 / macOS 14                                                    │  │
│ │ IP：192.168.10.120（院内网络）                                           │  │
│ │ 登录时间：2026-03-30 08:42                                               │  │
│ │ 最后活动：1 天前                                                         │  │
│ └──────────────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────────┤
│ ⓘ 如发现异常设备，请立即下线并修改密码                                         │
└────────────────────────────────────────────────────────────────────────────────┘
```

**显示规则：**
- 当前设备标记 `[当前]`，不可下线。
- 其他设备显示 `[下线]` 按钮。
- 最后活动时间相对显示（刚刚/5分钟前/2小时前/1天前）。
- 非常用设备（IP 或 UA 首次出现）标黄色警示。

### 5.3 P02 全部会话（管理员）

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会话管理                                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计：                                                                         │
│ ┌──────────┬──────────┬──────────┬──────────┐                                 │
│ │ 活跃会话 │ 今日登录 │ 即将过期 │ 已吊销   │                                 │
│ │   186    │   342    │    12    │   38     │                                 │
│ └──────────┴──────────┴──────────┴──────────┘                                 │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：账号[________] IP[________] 状态[活跃▼] 设备[全部▼] 时间[今日▼]          │
│ 工具栏：[批量下线] [导出]                                                      │
├────────────────────────────────────────────────────────────────────────────────┤
│ ☐ │登录名   │姓名│设备      │IP            │登录时间       │最后活动   │操作   │
│ ☐ │wangwu  │王五│Chrome/Win│192.168.10.55 │04-01 10:23  │刚刚       │[下线] │
│ ☐ │lisi    │李四│Safari/iOS│192.168.10.88 │03-31 09:15  │2小时前    │[下线] │
│ ☐ │zhaoliu │赵六│Chrome/Win│192.168.10.120│03-30 08:42  │1天前      │[下线] │
│ ...                                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ 共 186 条                                                                      │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 P03 会话详情

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会话详情                                     状态：✅ 活跃                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【会话信息】                                                                   │
│ 会话 ID：sess_9e8d7c6b5a4f                                                     │
│ 账号：wangwu（王五）    工号：E24030017    科室：白内障科                       │
│                                                                                │
│ 【终端信息】                                                                   │
│ 设备类型：PC                                                                   │
│ User-Agent：Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0            │
│ IP 地址：192.168.10.55                                                         │
│ IP 归属：院内网络                                                              │
│                                                                                │
│ 【时间信息】                                                                   │
│ 登录时间：2026-04-01 10:23:45                                                  │
│ 最后活动：2026-04-01 14:20:12（5 分钟前）                                      │
│ 绝对过期：2026-04-08 10:23:45（剩余 6 天 20 小时）                             │
│ 空闲过期：2026-04-01 16:20:12（剩余 2 小时）                                   │
│                                                                                │
│ 【Token 信息】                                                                 │
│ 当前 Access jti：at_7f3a2b1c9d4e5f6a                                          │
│ Access 过期：2026-04-01 14:53:45（剩余 33 分钟）                               │
│ Refresh 状态：有效（未轮换）                                                   │
│ 刷新次数：3 次                                                                 │
│                                                                                │
│ 【认证信息】                                                                   │
│ 登录方式：密码登录                                                             │
│ 二次验证：已通过（SMS）                                                        │
│ 认证级别：2                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ [强制下线] [查看该账号全部会话]                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.5 P04 会话配置

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会话配置                                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【Token 有效期】                                                               │
│ Access Token：[30   ] 分钟（建议 15~60）                                       │
│ Refresh Token：[7   ] 天（建议 1~30）                                          │
│                                                                                │
│ 【会话超时】                                                                   │
│ 空闲超时：     [120  ] 分钟（无操作自动失效）                                   │
│ 绝对超时：     [7    ] 天                                                      │
│ ☑ 活动时延长空闲计时                                                           │
│                                                                                │
│ 【并发控制】                                                                   │
│ 单账号最大会话：[5   ] 个                                                      │
│ 超出策略：● 踢出最旧  ○ 拒绝新登录                                             │
│ ☑ 同终端重复登录覆盖旧会话                                                     │
│ 管理员不受限制：☑                                                              │
│                                                                                │
│ 【刷新策略】                                                                   │
│ ☑ Refresh Token 轮换（推荐）                                                   │
│ ☑ 检测到 Token 重用则吊销整个会话                                              │
│ 刷新时是否延长 Refresh 有效期：○ 是  ● 否                                      │
│                                                                                │
│ 【黑名单】                                                                     │
│ ◎ 使用 Redis 黑名单（推荐）                                                    │
│ ○ 仅依赖会话状态检查                                                           │
│                                                                                │
│ 【签名密钥】                                                                   │
│ 算法：HS256    当前密钥版本：k2026-04                                          │
│ 自动轮换周期：[90 ] 天                                                         │
├────────────────────────────────────────────────────────────────────────────────┤
│ ⚠ 修改 Token 有效期将立即影响新签发的 Token，存量 Token 不受影响               │
│                                          [取消] [保存]                         │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.6 P05 Token 黑名单

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Token 黑名单                                                                   │
├────────────────────────────────────────────────────────────────────────────────┤
│ 当前黑名单：38 条（Redis）                                                     │
├────────────────────────────────────────────────────────────────────────────────┤
│ JTI                    │账号  │原因      │加入时间       │自动过期    │操作   │
│ at_7f3a2b1c9d4e5f6a   │wangwu│用户登出  │04-01 14:20   │14:50      │[移除] │
│ at_8a4b3c2d1e0f9a8b   │lisi  │强制下线  │04-01 14:15   │14:45      │[移除] │
│ at_9b5c4d3e2f1a0b9c   │zhaoliu│密码修改 │04-01 14:10   │14:40      │[移除] │
│ ...                                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ 说明：黑名单中的 Token 在自然过期前将被拒绝使用                                │
│ ⚠ 移除黑名单条目意味着该 Token 可继续使用，请谨慎操作                          │
├────────────────────────────────────────────────────────────────────────────────┤
│                                          [刷新] [清空过期条目]                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.7 P06 签名密钥管理

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 签名密钥管理                                                                   │
├────────────────────────────────────────────────────────────────────────────────┤
│ 算法：HS256                                                                    │
├────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────┬──────────────┬──────────┬──────────────┬────────────┬──────────┐│
│ │ 密钥版本  │ 状态          │ 生效时间 │ 停用时间      │ 签发Token数 │ 操作     ││
│ │ k2026-04 │ ✅ 活跃       │ 04-01    │ —            │ 3,246      │ —        ││
│ │ k2026-01 │ ⏳ 过渡中     │ 01-01    │ 04-01        │ 0          │ [停用]   ││
│ │ k2025-10 │ ⛔ 已停用     │ 2025-10  │ 2026-01      │ 0          │ [删除]   ││
│ └──────────┴──────────────┴──────────┴──────────────┴────────────┴──────────┘│
├────────────────────────────────────────────────────────────────────────────────┤
│ [生成新密钥并轮换]                                                             │
│                                                                                │
│ ⚠ 轮换说明：                                                                   │
│ · 新密钥生成后立即用于签发                                                   │
│ · 旧密钥保留 30 分钟用于验签（过渡期）                                         │
│ · 过渡期后旧密钥自动停用                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 【手动验证】                                                                   │
│ 粘贴 Token：[________________________________________]  [验证]                 │
│ 结果：✅ 签名有效，密钥版本 k2026-04，过期时间 2026-04-01 14:53                │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 5.8 P07 会话历史

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ 会话历史                                                                       │
├────────────────────────────────────────────────────────────────────────────────┤
│ 筛选：账号[________] 状态[全部▼] 结束原因[全部▼] 时间[近30天▼]                 │
├────────────────────────────────────────────────────────────────────────────────┤
│ 会话ID        │账号  │登录时间       │结束时间       │时长    │结束原因  │操作│
│ sess_9e8d7c...│wangwu│04-01 10:23   │04-01 14:20   │3h57m   │用户登出  │详情│
│ sess_8d7c6b...│lisi  │03-31 09:15   │03-31 18:30   │9h15m   │空闲超时  │详情│
│ sess_7c6b5a...│zhaoliu│03-30 08:42  │03-30 08:50   │8m      │强制下线  │详情│
│ sess_6b5a4f...│wangwu│03-29 10:00   │03-29 10:00   │0m      │并发超限  │详情│
│ ...                                                                            │
├────────────────────────────────────────────────────────────────────────────────┤
│ 统计：总会话 12,846，平均时长 4.2 小时                                         │
└────────────────────────────────────────────────────────────────────────────────┘
```

**结束原因：**

| 原因 | 说明 |
|---|---|
| `LOGOUT` | 用户主动登出 |
| `IDLE_TIMEOUT` | 空闲超时 |
| `ABSOLUTE_TIMEOUT` | 绝对超时 |
| `PASSWORD_CHANGED` | 密码修改 |
| `ACCOUNT_DISABLED` | 账号停用 |
| `FORCE_LOGOUT` | 管理员强制下线 |
| `CONCURRENCY_LIMIT` | 并发超限被踢 |
| `TOKEN_REUSE` | Refresh Token 重用（安全事件） |
| `SELF_KICK` | 用户踢出自己其他设备 |

### 5.9 P08 强制下线确认弹窗

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  确认强制下线                                                              ✕   │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  ⚠ 即将强制下线以下会话：                                                      │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐ │
│  │ 账号：wangwu（王五）                                                     │ │
│  │ 设备：Chrome 120 / Windows 10                                            │ │
│  │ IP：192.168.10.55（院内网络）                                            │ │
│  │ 登录时间：2026-04-01 10:23                                               │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                │
│  下线原因：[管理员强制下线________________________________]                    │
│                                                                                │
│  ⓘ 该用户将立即失去访问权限，需重新登录                                        │
│                                                                                │
│  ┌────────────────────────┐  ┌────────────────────────┐                       │
│  │       取  消            │  │       确认下线          │                       │
│  └────────────────────────┘  └────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. 后端接口设计

### 6.1 接口总览

| 编号 | 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|---|
| **Token 操作** | | | | |
| API-01 | POST | `/api/v1/auth/token/refresh` | 刷新 Token | 公开（持 Refresh） |
| API-02 | POST | `/api/v1/auth/token/verify` | 校验 Token | 公开 |
| API-03 | GET | `/api/v1/auth/token/me` | 当前 Token 信息 | 登录即可 |
| API-04 | POST | `/api/v1/auth/token/renew` | 续期（access即将过期） | 登录即可 |
| **我的会话** | | | | |
| API-05 | GET | `/api/v1/auth/sessions/me` | 我的会话列表 | 登录即可 |
| API-06 | DELETE | `/api/v1/auth/sessions/me/{session_id}` | 下线指定设备 | 登录即可 |
| API-07 | DELETE | `/api/v1/auth/sessions/me/others` | 下线所有其他设备 | 登录即可 |
| **会话管理** | | | | |
| API-08 | GET | `/api/v1/auth/sessions` | 全部会话列表 | `sys:session:list` |
| API-09 | GET | `/api/v1/auth/sessions/{session_id}` | 会话详情 | `sys:session:list` |
| API-10 | POST | `/api/v1/auth/sessions/{session_id}/revoke` | 强制下线 | `sys:session:revoke` |
| API-11 | POST | `/api/v1/auth/sessions/batch-revoke` | 批量下线 | `sys:session:revoke` |
| API-12 | POST | `/api/v1/auth/sessions/revoke-account` | 下线某账号全部会话 | `sys:session:revoke` |
| API-13 | GET | `/api/v1/auth/sessions/statistics` | 会话统计 | `sys:session:list` |
| **会话历史** | | | | |
| API-14 | GET | `/api/v1/auth/sessions/history` | 会话历史 | `sys:session:audit` |
| API-15 | GET | `/api/v1/auth/sessions/history/export` | 导出历史 | `sys:session:audit` |
| **配置** | | | | |
| API-16 | GET | `/api/v1/auth/session-config` | 会话配置查询 | `sys:session:config` |
| API-17 | PUT | `/api/v1/auth/session-config` | 会话配置修改 | `sys:session:config` |
| **黑名单** | | | | |
| API-18 | GET | `/api/v1/auth/blacklist` | 黑名单列表 | `sys:session:admin` |
| API-19 | DELETE | `/api/v1/auth/blacklist/{jti}` | 移除黑名单 | `sys:session:admin` |
| API-20 | POST | `/api/v1/auth/blacklist/cleanup` | 清理过期条目 | `sys:session:admin` |
| **密钥** | | | | |
| API-21 | GET | `/api/v1/auth/jwt-keys` | 密钥列表 | `sys:session:admin` |
| API-22 | POST | `/api/v1/auth/jwt-keys/rotate` | 轮换密钥 | `sys:session:admin` |
| API-23 | POST | `/api/v1/auth/jwt-keys/verify` | 验证 Token | `sys:session:admin` |
| **内部服务** | | | | |
| API-24 | POST | `/internal/v1/session/create` | **创建会话（M02-02 调用）** | 内部服务 |
| API-25 | GET | `/internal/v1/session/{session_id}` | 查询会话 | 内部服务 |
| API-26 | POST | `/internal/v1/session/{session_id}/revoke` | 吊销会话 | 内部服务 |
| API-27 | POST | `/internal/v1/session/revoke-all` | 吊销账号全部会话 | 内部服务 |
| API-28 | POST | `/internal/v1/session/touch` | 会话活动心跳 | 内部服务 |
| API-29 | POST | `/internal/v1/token/validate` | **校验 Token（M02-04 调用）** | 内部服务 |

### 6.2 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "9f8a7b6c5d4e3f2a"
}
```

**错误码规范（M02-03：53001~53040）**

| 错误码 | 含义 |
|---|---|
| 0 | 成功 |
| 40001 | 参数校验失败 |
| 53001 | Token 缺失 |
| 53002 | Token 格式错误 |
| 53003 | Token 签名无效 |
| 53004 | Token 已过期 |
| 53005 | Token 尚未生效 |
| 53006 | Token 类型错误 |
| 53007 | Token 已被吊销 |
| 53008 | Token 受众不匹配 |
| 53009 | Token 签发者不匹配 |
| 53010 | Token 已加入黑名单 |
| 53011 | 会话不存在 |
| 53012 | 会话已过期 |
| 53013 | 会话已吊销 |
| 53014 | 会话空闲超时 |
| 53015 | 会话绝对超时 |
| 53016 | 会话不属于当前用户 |
| 53017 | 不能下线当前会话 |
| 53018 | Refresh Token 无效 |
| 53019 | Refresh Token 已使用（轮换后） |
| 53020 | **Refresh Token 重用，会话已吊销** |
| 53021 | Refresh Token 已过期 |
| 53022 | 并发会话超限 |
| 53023 | 密钥不存在 |
| 53024 | 密钥已停用 |
| 53025 | 密钥轮换失败 |
| 53026 | 会话配置不存在 |
| 53027 | 会话配置参数非法 |
| 53028 | 黑名单条目不存在 |
| 53029 | 账号状态异常，会话已失效 |
| 53030 | 会话创建失败 |
| 53031 | 会话数量已达上限 |
| 53032 | 该会话已处于非活跃状态 |
| 53033 | 不支持的操作 |
| 53034 | 令牌版本不匹配 |
| 53035 | 令牌已被替换 |
| 50001 | 权限校验失败 |
| 50002 | 依赖服务不可用 |
| 50003 | 数据库异常 |

### 6.3 接口详细设计

#### API-01 刷新 Token

**请求**

```
POST /api/v1/auth/token/refresh
```

```json
{
  "refresh_token": "rt_7f3a2b1c9d4e5f6a_1024",
  "device_id": "dev_abc123"
}
```

**响应（成功）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "rt_9c8d7e6f5a4b3c2d_1024",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_expires_in": 604800,
    "session_id": "sess_9e8d7c6b5a4f"
  },
  "trace_id": "9f8a7b6c"
}
```

**响应（Refresh Token 已轮换 → 重用检测）**

```json
{
  "code": 53020,
  "message": "Refresh Token 已被使用，会话已安全吊销",
  "data": {
    "session_id": "sess_9e8d7c6b5a4f",
    "revoked": true,
    "reason": "TOKEN_REUSE_DETECTED",
    "hint": "如非本人操作，请立即修改密码"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-02 校验 Token

**请求**

```
POST /api/v1/auth/token/verify
```

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应（有效）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": true,
    "session_id": "sess_9e8d7c6b5a4f",
    "account_id": 1024,
    "username": "wangwu",
    "staff_id": 1024,
    "staff_name": "王五",
    "dept_id": 15,
    "acct_type": "EMPLOYEE",
    "auth_level": 2,
    "jti": "at_7f3a2b1c9d4e5f6a",
    "issued_at": "2026-04-01T14:23:45",
    "expires_at": "2026-04-01T14:53:45",
    "remaining_seconds": 1800
  },
  "trace_id": "9f8a7b6c"
}
```

**响应（无效）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": false,
    "error_code": "TOKEN_EXPIRED",
    "error_message": "Token 已过期",
    "expired_at": "2026-04-01T14:53:45"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-05 我的会话列表

**请求**

```
GET /api/v1/auth/sessions/me
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 3,
    "max_allowed": 5,
    "current_session_id": "sess_9e8d7c6b5a4f",
    "items": [
      {
        "session_id": "sess_9e8d7c6b5a4f",
        "is_current": true,
        "device_type": "PC",
        "device_name": "Chrome 120 / Windows 10",
        "login_ip": "192.168.10.55",
        "ip_location": "院内网络",
        "location_detail": "白内障科诊室",
        "login_at": "2026-04-01T10:23:45",
        "last_active_at": "2026-04-01T14:20:12",
        "last_active_text": "刚刚",
        "expire_at": "2026-04-08T10:23:45",
        "idle_expire_at": "2026-04-01T16:20:12",
        "is_abnormal": false
      },
      {
        "session_id": "sess_8d7c6b5a4f3e",
        "is_current": false,
        "device_type": "MOBILE",
        "device_name": "Safari / iOS 17",
        "login_ip": "192.168.10.88",
        "ip_location": "院内网络",
        "login_at": "2026-03-31T09:15:00",
        "last_active_at": "2026-04-01T12:20:00",
        "last_active_text": "2 小时前",
        "expire_at": "2026-04-07T09:15:00",
        "is_abnormal": false
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-06 下线指定设备

**请求**

```
DELETE /api/v1/auth/sessions/me/sess_8d7c6b5a4f3e
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_8d7c6b5a4f3e",
    "revoked": true,
    "message": "该设备已下线"
  },
  "trace_id": "9f8a7b6c"
}
```

**错误（下线当前会话）**

```json
{
  "code": 53017,
  "message": "不能通过此接口下线当前会话，请使用登出功能",
  "data": {},
  "trace_id": "9f8a7b6c"
}
```

#### API-07 下线所有其他设备

**请求**

```
DELETE /api/v1/auth/sessions/me/others
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "revoked_count": 2,
    "current_session_id": "sess_9e8d7c6b5a4f",
    "message": "已下线 2 个其他设备，当前设备保持登录"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-08 全部会话列表

**请求**

```
GET /api/v1/auth/sessions?status=ACTIVE&page=1&page_size=20
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "session_id": "sess_9e8d7c6b5a4f",
        "account_id": 1024,
        "username": "wangwu",
        "staff_name": "王五",
        "dept_name": "白内障科",
        "device_type": "PC",
        "device_name": "Chrome 120 / Windows 10",
        "login_ip": "192.168.10.55",
        "ip_location": "院内网络",
        "login_type": "PASSWORD",
        "status": "ACTIVE",
        "login_at": "2026-04-01T10:23:45",
        "last_active_at": "2026-04-01T14:20:12",
        "expire_at": "2026-04-08T10:23:45",
        "idle_expire_at": "2026-04-01T16:20:12",
        "refresh_count": 3
      }
    ],
    "total": 186,
    "page": 1,
    "page_size": 20,
    "pages": 10
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-10 强制下线

**请求**

```
POST /api/v1/auth/sessions/sess_9e8d7c6b5a4f/revoke
```

```json
{
  "reason": "管理员检测到异常登录，强制下线",
  "notify_user": true
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_9e8d7c6b5a4f",
    "revoked": true,
    "blacklisted_jti": "at_7f3a2b1c9d4e5f6a",
    "notified": true,
    "reason": "管理员检测到异常登录，强制下线"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-12 下线某账号全部会话

**请求**

```
POST /api/v1/auth/sessions/revoke-account
```

```json
{
  "account_id": 1024,
  "reason": "账号密钥疑似泄露，强制所有设备下线",
  "exclude_session_id": null
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "account_id": 1024,
    "username": "wangwu",
    "revoked_count": 3,
    "blacklist_count": 3,
    "reason": "账号密钥疑似泄露，强制所有设备下线"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-16 会话配置查询

**请求**

```
GET /api/v1/auth/session-config
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token_ttl_min": 30,
    "refresh_token_ttl_days": 7,
    "idle_timeout_min": 120,
    "absolute_timeout_days": 7,
    "extend_idle_on_activity": true,
    "max_sessions_per_account": 5,
    "overflow_strategy": "KICK_OLDEST",
    "same_device_overwrite": true,
    "admin_unlimited": true,
    "refresh_rotation": true,
    "detect_token_reuse": true,
    "extend_refresh_on_refresh": false,
    "use_blacklist": true,
    "jwt_algorithm": "HS256",
    "current_key_id": "k2026-04",
    "key_rotate_days": 90,
    "version_no": 3,
    "updated_at": "2026-04-01T09:00:00"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-21 密钥列表

**请求**

```
GET /api/v1/auth/jwt-keys
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "algorithm": "HS256",
    "current_key_id": "k2026-04",
    "items": [
      {
        "kid": "k2026-04",
        "status": "ACTIVE",
        "effective_at": "2026-04-01T00:00:00",
        "retired_at": null,
        "signed_count": 3246,
        "can_sign": true,
        "can_verify": true
      },
      {
        "kid": "k2026-01",
        "status": "RETIRING",
        "effective_at": "2026-01-01T00:00:00",
        "retired_at": "2026-04-01T00:00:00",
        "signed_count": 0,
        "can_sign": false,
        "can_verify": true
      },
      {
        "kid": "k2025-10",
        "status": "RETIRED",
        "effective_at": "2025-10-01T00:00:00",
        "retired_at": "2026-01-01T00:00:00",
        "signed_count": 0,
        "can_sign": false,
        "can_verify": false
      }
    ]
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-22 轮换密钥

**请求**

```
POST /api/v1/auth/jwt-keys/rotate
```

```json
{
  "kid": "k2026-07",
  "transition_minutes": 30
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "new_kid": "k2026-07",
    "old_kid": "k2026-04",
    "old_status": "RETIRING",
    "transition_until": "2026-04-01T15:00:00",
    "message": "密钥已轮换，旧密钥 30 分钟内仍可用于验签"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-24 创建会话（内部，M02-02 调用）

**请求**

```
POST /internal/v1/session/create
```

```json
{
  "account_id": 1024,
  "staff_id": 1024,
  "username": "wangwu",
  "staff_code": "E24030017",
  "staff_name": "王五",
  "dept_id": 15,
  "dept_name": "白内障科",
  "org_id": 1,
  "acct_type": "EMPLOYEE",
  "login_ip": "192.168.10.55",
  "user_agent": "Mozilla/5.0 Chrome/120",
  "device_type": "PC",
  "device_id": "dev_abc123",
  "login_type": "PASSWORD",
  "mfa_passed": true
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_9e8d7c6b5a4f",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "rt_7f3a2b1c9d4e5f6a_1024",
    "token_type": "Bearer",
    "expires_in": 1800,
    "refresh_expires_in": 604800,
    "idle_expire_at": "2026-04-01T16:23:45",
    "kicked_session_ids": []
  },
  "trace_id": "9f8a7b6c"
}
```

**响应（并发超限踢旧）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_new123",
    "access_token": "eyJ...",
    "refresh_token": "rt_new...",
    "expires_in": 1800,
    "refresh_expires_in": 604800,
    "kicked_session_ids": ["sess_old456"],
    "message": "并发会话超限，已踢出最旧会话"
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-26 吊销会话（内部）

**请求**

```
POST /internal/v1/session/sess_9e8d7c6b5a4f/revoke
```

```json
{
  "reason": "PASSWORD_CHANGED",
  "blacklist": true
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_9e8d7c6b5a4f",
    "revoked": true,
    "blacklisted": true
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-27 吊销账号全部会话（内部）

**请求**

```
POST /internal/v1/session/revoke-all
```

```json
{
  "account_id": 1024,
  "reason": "ACCOUNT_DISABLED",
  "exclude_session_id": null
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "account_id": 1024,
    "revoked": 3,
    "blacklisted": 3
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-28 会话活动心跳（内部）

**请求**

```
POST /internal/v1/session/touch
```

```json
{
  "session_id": "sess_9e8d7c6b5a4f",
  "jti": "at_7f3a2b1c9d4e5f6a"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": "sess_9e8d7c6b5a4f",
    "idle_expire_at": "2026-04-01T16:25:00",
    "extended": true
  },
  "trace_id": "9f8a7b6c"
}
```

#### API-29 校验 Token（内部，M02-04 调用）

**请求**

```
POST /internal/v1/token/validate
```

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "check_session": true,
  "check_account_status": true
}
```

**响应（有效）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": true,
    "account_id": 1024,
    "username": "wangwu",
    "staff_id": 1024,
    "staff_code": "E24030017",
    "staff_name": "王五",
    "dept_id": 15,
    "dept_name": "白内障科",
    "org_id": 1,
    "acct_type": "EMPLOYEE",
    "auth_level": 2,
    "mfa_passed": true,
    "session_id": "sess_9e8d7c6b5a4f",
    "jti": "at_7f3a2b1c9d4e5f6a",
    "expires_at": "2026-04-01T14:53:45",
    "remaining_seconds": 1800,
    "need_refresh": false
  },
  "trace_id": "9f8a7b6c"
}
```

**响应（无效）**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "valid": false,
    "error_code": "SESSION_REVOKED",
    "error_message": "会话已被吊销",
    "session_id": "sess_9e8d7c6b5a4f",
    "revoked_reason": "PASSWORD_CHANGED"
  },
  "trace_id": "9f8a7b6c"
}
```

### 6.4 FastAPI 路由实现示例

```python
# app/api/v1/auth/token.py
"""会话与 Token REST 接口"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success_response, PageResult
from app.core.security import get_current_user, require_permission
from app.schemas.auth.token import (
    RefreshRequest, VerifyRequest, RevokeRequest, BatchRevokeRequest,
    RevokeAccountRequest, SessionConfigUpdate, SessionQuery,
    CreateSessionRequest, RotateKeyRequest,
)
from app.services.auth.token_service import TokenService
from app.services.auth.session_service import SessionService
from app.services.auth.session_config_service import SessionConfigService
from app.services.auth.jwt_key_service import JwtKeyService
from app.services.auth.blacklist_service import BlacklistService

router = APIRouter(prefix="/api/v1/auth", tags=["M02-会话与Token"])
internal_router = APIRouter(prefix="/internal/v1", tags=["M02-会话内部接口"])


# ==================== Token 操作 ====================
@router.post("/token/refresh", summary="刷新 Token")
async def refresh_token(
    payload: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    svc = TokenService(db)
    data = await svc.refresh(payload, request)
    return success_response(data)


@router.post("/token/verify", summary="校验 Token")
async def verify_token(
    payload: VerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = TokenService(db)
    data = await svc.verify_public(payload.token)
    return success_response(data)


@router.get("/token/me", summary="当前 Token 信息")
async def token_me(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = TokenService(db)
    data = await svc.get_token_info(authorization)
    return success_response(data)


@router.post("/token/renew", summary="续期")
async def renew_token(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = TokenService(db)
    data = await svc.renew(authorization, user)
    return success_response(data)


# ==================== 我的会话 ====================
@router.get("/sessions/me", summary="我的会话列表")
async def my_sessions(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = SessionService(db)
    data = await svc.list_my_sessions(user, authorization)
    return success_response(data)


@router.delete("/sessions/me/others", summary="下线所有其他设备")
async def kick_others(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = SessionService(db)
    data = await svc.kick_others(user, authorization)
    return success_response(data)


@router.delete("/sessions/me/{session_id}", summary="下线指定设备")
async def kick_one(
    session_id: str,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    svc = SessionService(db)
    data = await svc.kick_one(session_id, user, authorization)
    return success_response(data)


# ==================== 会话管理 ====================
@router.get("/sessions", summary="全部会话列表")
async def list_sessions(
    username: Optional[str] = Query(None),
    account_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    login_ip: Optional[str] = Query(None),
    device_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:list")),
):
    svc = SessionService(db)
    q = SessionQuery(
        username=username, account_id=account_id, status=status,
        login_ip=login_ip, device_type=device_type,
        page=page, page_size=page_size)
    items, total = await svc.list_sessions(q)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size))


@router.get("/sessions/statistics", summary="会话统计")
async def session_statistics(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:list")),
):
    svc = SessionService(db)
    data = await svc.get_statistics()
    return success_response(data)


@router.get("/sessions/history", summary="会话历史")
async def session_history(
    username: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    end_reason: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:audit")),
):
    svc = SessionService(db)
    items, total = await svc.list_history(
        username, status, end_reason, page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size))


@router.post("/sessions/{session_id}/revoke", summary="强制下线")
async def revoke_session(
    session_id: str,
    payload: RevokeRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:revoke")),
):
    svc = SessionService(db)
    data = await svc.admin_revoke(session_id, payload, operator=user)
    return success_response(data)


@router.post("/sessions/batch-revoke", summary="批量下线")
async def batch_revoke(
    payload: BatchRevokeRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:revoke")),
):
    svc = SessionService(db)
    data = await svc.batch_revoke(payload, operator=user)
    return success_response(data)


@router.post("/sessions/revoke-account", summary="下线账号全部会话")
async def revoke_account(
    payload: RevokeAccountRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:revoke")),
):
    svc = SessionService(db)
    data = await svc.revoke_account(payload, operator=user)
    return success_response(data)


# ==================== 配置 ====================
@router.get("/session-config", summary="会话配置查询")
async def get_session_config(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:config")),
):
    svc = SessionConfigService(db)
    data = await svc.get_config()
    return success_response(data)


@router.put("/session-config", summary="会话配置修改")
async def update_session_config(
    payload: SessionConfigUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:config")),
):
    svc = SessionConfigService(db)
    data = await svc.update_config(payload, operator=user)
    return success_response(data)


# ==================== 黑名单 ====================
@router.get("/blacklist", summary="黑名单列表")
async def list_blacklist(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:admin")),
):
    svc = BlacklistService(db)
    items, total = await svc.list_items(page, page_size)
    return success_response(PageResult(
        items=items, total=total, page=page, page_size=page_size,
        pages=(total + page_size - 1) // page_size))


@router.delete("/blacklist/{jti}", summary="移除黑名单")
async def remove_blacklist(
    jti: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:admin")),
):
    svc = BlacklistService(db)
    data = await svc.remove(jti, operator=user)
    return success_response(data)


# ==================== 密钥 ====================
@router.get("/jwt-keys", summary="密钥列表")
async def list_keys(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:admin")),
):
    svc = JwtKeyService(db)
    data = await svc.list_keys()
    return success_response(data)


@router.post("/jwt-keys/rotate", summary="轮换密钥")
async def rotate_keys(
    payload: RotateKeyRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sys:session:admin")),
):
    svc = JwtKeyService(db)
    data = await svc.rotate(payload, operator=user)
    return success_response(data)


# ==================== 内部服务 ====================
@internal_router.post("/session/create", summary="创建会话")
async def internal_create_session(
    payload: CreateSessionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    data = await svc.create_session(payload, request)
    return success_response(data)


@internal_router.get("/session/{session_id}", summary="查询会话")
async def internal_get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    data = await svc.get_session(session_id)
    return success_response(data)


@internal_router.post("/session/{session_id}/revoke", summary="吊销会话")
async def internal_revoke_session(
    session_id: str,
    reason: str = Body(..., embed=True),
    blacklist: bool = Body(True, embed=True),
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    data = await svc.revoke(session_id, reason, blacklist=blacklist)
    return success_response(data)


@internal_router.post("/session/revoke-all", summary="吊销账号全部会话")
async def internal_revoke_all(
    account_id: int = Body(..., embed=True),
    reason: str = Body(..., embed=True),
    exclude_session_id: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    data = await svc.revoke_account_internal(
        account_id, reason, exclude_session_id)
    return success_response(data)


@internal_router.post("/session/touch", summary="会话心跳")
async def internal_touch(
    session_id: str = Body(..., embed=True),
    jti: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
):
    svc = SessionService(db)
    data = await svc.touch(session_id, jti)
    return success_response(data)


@internal_router.post("/token/validate", summary="校验 Token")
async def internal_validate_token(
    token: str = Body(..., embed=True),
    check_session: bool = Body(True, embed=True),
    check_account_status: bool = Body(True, embed=True),
    db: AsyncSession = Depends(get_db),
):
    svc = TokenService(db)
    data = await svc.validate(token, check_session, check_account_status)
    return success_response(data)
```

### 6.5 Service 层核心逻辑示例

```python
# app/services/auth/token_service.py
"""Token 服务（签发、校验、刷新）"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.session import SysSession, SysJwtKey, SysSessionConfig
from app.core.exceptions import BizException
from app.core.redis import redis_client
from app.services.auth.blacklist_service import BlacklistService


class TokenService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.blacklist = BlacklistService(db)

    # ---------- 签发 ----------
    async def issue_tokens(self, session_id: str, account: dict,
                            config: dict) -> dict:
        """签发 Access + Refresh Token"""
        key = await self._get_active_key()
        now = datetime.now(timezone.utc)

        access_ttl = config["access_token_ttl_min"] * 60
        jti = f"at_{uuid.uuid4().hex[:16]}"

        payload = {
            "iss": "m02-auth",
            "sub": str(account["account_id"]),
            "aud": "his-api",
            "exp": int((now + timedelta(seconds=access_ttl)).timestamp()),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "jti": jti,
            "sid": session_id,
            "typ": "access",
            "usr": account["username"],
            "staff_id": account.get("staff_id"),
            "staff_code": account.get("staff_code"),
            "staff_name": account.get("staff_name"),
            "dept_id": account.get("dept_id"),
            "dept_name": account.get("dept_name"),
            "org_id": account.get("org_id", 1),
            "acct_type": account.get("acct_type", "EMPLOYEE"),
            "auth_level": 2 if account.get("mfa_passed") else 0,
            "mfa_passed": bool(account.get("mfa_passed")),
        }

        access_token = jwt.encode(
            payload,
            key["secret"],
            algorithm="HS256",
            headers={"kid": key["kid"], "typ": "JWT"})

        # Refresh Token
        refresh_raw = secrets.token_hex(32)
        refresh_token = f"rt_{refresh_raw}_{account['account_id']}"

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "refresh_hash": self._hash_refresh(refresh_raw),
            "jti": jti,
            "expires_in": access_ttl,
            "refresh_expires_in": config["refresh_token_ttl_days"] * 86400,
            "kid": key["kid"],
        }

    # ---------- 校验 ----------
    async def validate(self, token: str, check_session: bool = True,
                        check_account_status: bool = True) -> dict:
        """校验 Token（M02-04 调用）"""
        # 1. 解析与验签
        try:
            keys = await self._get_verify_keys()
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")

            key = keys.get(kid)
            if not key:
                return {"valid": False, "error_code": "KEY_NOT_FOUND",
                        "error_message": f"密钥 {kid} 不存在或已停用"}

            payload = jwt.decode(
                token,
                key["secret"],
                algorithms=["HS256"],
                audience="his-api",
                issuer="m02-auth",
                options={"require": ["exp", "iat", "sub", "jti", "sid"]})

        except jwt.ExpiredSignatureError:
            return {"valid": False, "error_code": "TOKEN_EXPIRED",
                    "error_message": "Token 已过期"}
        except jwt.InvalidAudienceError:
            return {"valid": False, "error_code": "AUDIENCE_MISMATCH",
                    "error_message": "Token 受众不匹配"}
        except jwt.InvalidIssuerError:
            return {"valid": False, "error_code": "ISSUER_MISMATCH",
                    "error_message": "Token 签发者不匹配"}
        except jwt.InvalidSignatureError:
            return {"valid": False, "error_code": "SIGNATURE_INVALID",
                    "error_message": "Token 签名无效"}
        except jwt.ImmatureSignatureError:
            return {"valid": False, "error_code": "TOKEN_NOT_YET_VALID",
                    "error_message": "Token 尚未生效"}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "error_code": "TOKEN_INVALID",
                    "error_message": f"Token 无效：{str(e)[:50]}"}

        # 2. 类型检查
        if payload.get("typ") != "access":
            return {"valid": False, "error_code": "TOKEN_TYPE_MISMATCH",
                    "error_message": "Token 类型错误"}

        jti = payload["jti"]
        session_id = payload["sid"]

        # 3. 黑名单检查
        if await self.blacklist.is_blacklisted(jti):
            return {"valid": False, "error_code": "TOKEN_BLACKLISTED",
                    "error_message": "Token 已被吊销",
                    "session_id": session_id}

        # 4. 会话状态检查
        if check_session:
            session_check = await self._check_session(session_id)
            if session_check:
                return session_check

        # 5. 账号状态检查
        if check_account_status:
            status_check = await self._check_account_status(
                payload["sub"])
            if status_check:
                return status_check

        # 6. 剩余时长
        exp = payload["exp"]
        now_ts = int(datetime.now(timezone.utc).timestamp())
        remaining = max(0, exp - now_ts)

        return {
            "valid": True,
            "account_id": int(payload["sub"]),
            "username": payload.get("usr"),
            "staff_id": payload.get("staff_id"),
            "staff_code": payload.get("staff_code"),
            "staff_name": payload.get("staff_name"),
            "dept_id": payload.get("dept_id"),
            "dept_name": payload.get("dept_name"),
            "org_id": payload.get("org_id", 1),
            "acct_type": payload.get("acct_type"),
            "auth_level": payload.get("auth_level", 0),
            "mfa_passed": payload.get("mfa_passed", False),
            "session_id": session_id,
            "jti": jti,
            "issued_at": datetime.fromtimestamp(payload["iat"]).isoformat(),
            "expires_at": datetime.fromtimestamp(exp).isoformat(),
            "remaining_seconds": remaining,
            "need_refresh": remaining < 300,
        }

    async def _check_session(self, session_id: str) -> Optional[dict]:
        """检查会话状态"""
        # 先查 Redis
        cache_key = f"sys:session:status:{session_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            status = cached.decode() if isinstance(cached, bytes) else cached
            if status != "ACTIVE":
                return {"valid": False, "error_code": f"SESSION_{status}",
                        "error_message": f"会话已{self._status_text(status)}",
                        "session_id": session_id}

        # 查库
        sess = (await self.db.execute(
            select(SysSession).where(SysSession.session_id == session_id)
        )).scalar_one_or_none()

        if not sess:
            return {"valid": False, "error_code": "SESSION_NOT_FOUND",
                    "error_message": "会话不存在", "session_id": session_id}

        now = datetime.now()

        if sess.status == "REVOKED":
            return {"valid": False, "error_code": "SESSION_REVOKED",
                    "error_message": "会话已被吊销",
                    "session_id": session_id,
                    "revoked_reason": sess.revoke_reason}

        if sess.status == "EXPIRED":
            return {"valid": False, "error_code": "SESSION_EXPIRED",
                    "error_message": "会话已过期", "session_id": session_id}

        if sess.expire_at and sess.expire_at < now:
            return {"valid": False, "error_code": "SESSION_ABSOLUTE_TIMEOUT",
                    "error_message": "会话已超过最长时长", "session_id": session_id}

        if sess.idle_expire_at and sess.idle_expire_at < now:
            return {"valid": False, "error_code": "SESSION_IDLE_TIMEOUT",
                    "error_message": "会话因长时间无操作已失效",
                    "session_id": session_id}

        # 缓存状态
        await redis_client.setex(cache_key, 60, "ACTIVE")
        return None

    async def _check_account_status(self, account_id: str) -> Optional[dict]:
        """检查账号状态"""
        import httpx
        from app.core.config import settings

        cache_key = f"sys:account:status:{account_id}"
        cached = await redis_client.get(cache_key)
        if cached:
            status = cached.decode() if isinstance(cached, bytes) else cached
            if status != "ACTIVE":
                return {"valid": False, "error_code": "ACCOUNT_DISABLED",
                        "error_message": "账号状态异常，请重新登录"}
            return None

        try:
            async with httpx.AsyncClient(timeout=2) as client:
                resp = await client.get(
                    f"{settings.M01_BASE_URL}/internal/v1/account/{account_id}/status")
                data = resp.json().get("data", {})
                status = data.get("status", "ACTIVE")
                await redis_client.setex(cache_key, 60, status)
                if status != "ACTIVE":
                    return {"valid": False,
                            "error_code": f"ACCOUNT_{status}",
                            "error_message": "账号状态异常，请重新登录"}
        except Exception:
            # 依赖不可用时不阻断（降级）
            pass
        return None

    @staticmethod
    def _status_text(status: str) -> str:
        return {"REVOKED": "吊销", "EXPIRED": "过期"}.get(status, status)

    # ---------- 刷新 ----------
    async def refresh(self, req, request) -> dict:
        """刷新 Token（含轮换与重用检测）"""
        config = await self._get_config()

        # 1. 解析 refresh_token
        parts = req.refresh_token.split("_")
        if len(parts) != 3 or parts[0] != "rt":
            raise BizException(53018, "Refresh Token 格式无效")

        refresh_raw = parts[1]
        account_id = int(parts[2])
        refresh_hash = self._hash_refresh(refresh_raw)

        # 2. 查会话
        sess = (await self.db.execute(
            select(SysSession).where(
                SysSession.refresh_hash == refresh_hash,
                SysSession.account_id == account_id)
        )).scalar_one_or_none()

        # 3. 未找到 → 可能已被轮换（重用检测）
        if not sess:
            # 查是否是被轮换过的 Token
            rotated = (await self.db.execute(
                select(SysSession).where(
                    SysSession.old_refresh_hash == refresh_hash,
                    SysSession.account_id == account_id)
            )).scalar_one_or_none()

            if rotated and config["detect_token_reuse"]:
                # 检测到重用 → 吊销整个会话
                await self._revoke_with_blacklist(
                    rotated.session_id, "TOKEN_REUSE")
                raise BizException(53020,
                    "Refresh Token 已被使用，会话已安全吊销",
                    data={"session_id": rotated.session_id,
                          "revoked": True,
                          "reason": "TOKEN_REUSE_DETECTED",
                          "hint": "如非本人操作，请立即修改密码"})

            raise BizException(53018, "Refresh Token 无效")

        # 4. 会话状态
        if sess.status != "ACTIVE":
            raise BizException(53013, f"会话已{sess.status}，请重新登录")

        now = datetime.now()
        if sess.expire_at < now:
            raise BizException(53021, "Refresh Token 已过期，请重新登录")

        # 5. 生成新 Token
        account = {
            "account_id": sess.account_id,
            "username": sess.username,
            "staff_id": sess.staff_id,
            "staff_code": sess.staff_code,
            "staff_name": sess.staff_name,
            "dept_id": sess.dept_id,
            "dept_name": sess.dept_name,
            "org_id": sess.org_id,
            "acct_type": sess.acct_type,
            "mfa_passed": sess.mfa_passed,
        }
        tokens = await self.issue_tokens(sess.session_id, account, config)

        # 6. 更新会话（轮换）
        if config["refresh_rotation"]:
            sess.old_refresh_hash = sess.refresh_hash
            sess.refresh_hash = tokens["refresh_hash"]
            sess.rotated_at = now

        sess.access_jti = tokens["jti"]
        sess.last_active_at = now
        if config["extend_idle_on_activity"]:
            sess.idle_expire_at = now + timedelta(
                minutes=config["idle_timeout_min"])
        sess.refresh_count = (sess.refresh_count or 0) + 1

        # 7. 若不延长，Refresh 过期时间保持登录时 + TTL
        if config["extend_refresh_on_refresh"]:
            sess.expire_at = now + timedelta(
                days=config["refresh_token_ttl_days"])

        await self.db.commit()

        # 8. 清缓存
        await redis_client.delete(f"sys:session:status:{sess.session_id}")

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
            "expires_in": tokens["expires_in"],
            "refresh_expires_in": int(
                (sess.expire_at - now).total_seconds()),
            "session_id": sess.session_id,
        }

    async def _revoke_with_blacklist(self, session_id: str, reason: str) -> None:
        """吊销会话并加入黑名单"""
        sess = (await self.db.execute(
            select(SysSession).where(SysSession.session_id == session_id)
        )).scalar_one_or_none()
        if not sess:
            return

        sess.status = "REVOKED"
        sess.revoked_at = datetime.now()
        sess.revoke_reason = reason
        await self.db.commit()

        if sess.access_jti:
            await self.blacklist.add(
                jti=sess.access_jti,
                session_id=session_id,
                account_id=sess.account_id,
                username=sess.username,
                reason=reason,
                ttl_seconds=1800)

        await redis_client.setex(
            f"sys:session:status:{session_id}", 300, "REVOKED")

    # ---------- 辅助 ----------
    @staticmethod
    def _hash_refresh(raw: str) -> str:
        """Refresh Token 哈希"""
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _get_active_key(self) -> dict:
        """获取当前活跃签名密钥（缓存）"""
        cache_key = "sys:jwt:active_key"
        cached = await redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        key = (await self.db.execute(
            select(SysJwtKey).where(SysJwtKey.status == "ACTIVE")
        )).scalar_one_or_none()

        if not key:
            raise BizException(53023, "无活跃签名密钥")

        data = {"kid": key.kid, "secret": self._decrypt(key.secret_enc)}
        import json
        await redis_client.setex(cache_key, 300, json.dumps(data))
        return data

    async def _get_verify_keys(self) -> dict:
        """获取全部可验签密钥"""
        cache_key = "sys:jwt:verify_keys"
        cached = await redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)

        keys = (await self.db.execute(
            select(SysJwtKey).where(
                SysJwtKey.status.in_(["ACTIVE", "RETIRING"]))
        )).scalars().all()

        data = {
            k.kid: {"kid": k.kid, "secret": self._decrypt(k.secret_enc)}
            for k in keys
        }
        import json
        await redis_client.setex(cache_key, 300, json.dumps(data))
        return data

    @staticmethod
    def _decrypt(enc: str) -> str:
        """解密密钥（生产环境应从 KMS 获取）"""
        from app.core.crypto import aes_decrypt
        return aes_decrypt(enc)

    async def _get_config(self) -> dict:
        """获取会话配置"""
        cfg = (await self.db.execute(
            select(SysSessionConfig).where(SysSessionConfig.id == 1)
        )).scalar_one_or_none()
        if not cfg:
            raise BizException(53026, "会话配置不存在")
        return {
            "access_token_ttl_min": cfg.access_token_ttl_min,
            "refresh_token_ttl_days": cfg.refresh_token_ttl_days,
            "idle_timeout_min": cfg.idle_timeout_min,
            "absolute_timeout_days": cfg.absolute_timeout_days,
            "extend_idle_on_activity": cfg.extend_idle_on_activity,
            "max_sessions_per_account": cfg.max_sessions_per_account,
            "overflow_strategy": cfg.overflow_strategy,
            "refresh_rotation": cfg.refresh_rotation,
            "detect_token_reuse": cfg.detect_token_reuse,
            "extend_refresh_on_refresh": cfg.extend_refresh_on_refresh,
            "use_blacklist": cfg.use_blacklist,
        }

    async def verify_public(self, token: str) -> dict:
        """公开校验（前端可调用）"""
        result = await self.validate(token, check_session=True,
                                       check_account_status=False)
        if result["valid"]:
            return result
        return {
            "valid": False,
            "error_code": result.get("error_code"),
            "error_message": result.get("error_message"),
        }

    async def renew(self, authorization: str, user) -> dict:
        """续期（access 即将过期时）"""
        token = authorization.replace("Bearer ", "").strip()
        result = await self.validate(token, check_session=True,
                                       check_account_status=False)
        if not result["valid"]:
            raise BizException(53004, result.get("error_message", "Token 无效"))

        config = await self._get_config()
        account = {
            "account_id": result["account_id"],
            "username": result["username"],
            "staff_id": result.get("staff_id"),
            "staff_code": result.get("staff_code"),
            "staff_name": result.get("staff_name"),
            "dept_id": result.get("dept_id"),
            "dept_name": result.get("dept_name"),
            "org_id": result.get("org_id"),
            "acct_type": result.get("acct_type"),
            "mfa_passed": result.get("mfa_passed"),
        }
        tokens = await self.issue_tokens(
            result["session_id"], account, config)

        # 旧 jti 加入黑名单
        await self.blacklist.add(
            jti=result["jti"],
            session_id=result["session_id"],
            account_id=result["account_id"],
            username=result["username"],
            reason="RENEW",
            ttl_seconds=result["remaining_seconds"])

        return {
            "access_token": tokens["access_token"],
            "token_type": "Bearer",
            "expires_in": tokens["expires_in"],
            "session_id": result["session_id"],
        }

    async def get_token_info(self, authorization: str) -> dict:
        """当前 Token 信息"""
        token = authorization.replace("Bearer ", "").strip()
        result = await self.validate(token, check_session=True,
                                       check_account_status=False)
        if not result["valid"]:
            raise BizException(53001, "Token 无效")
        return result
```

```python
# app/services/auth/session_service.py
"""会话服务（生命周期管理）"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.session import SysSession, SysSessionConfig
from app.core.exceptions import BizException
from app.core.redis import redis_client
from app.services.auth.token_service import TokenService
from app.services.auth.blacklist_service import BlacklistService


class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_svc = TokenService(db)
        self.blacklist = BlacklistService(db)

    # ---------- 创建 ----------
    async def create_session(self, payload, request) -> dict:
        """创建会话（M02-02 调用）"""
        config = await self.token_svc._get_config()
        now = datetime.now()

        # 1. 并发控制
        kicked = []
        if payload.acct_type != "SUPER_ADMIN" or not config.get("admin_unlimited"):
            existing = (await self.db.execute(
                select(SysSession).where(
                    SysSession.account_id == payload.account_id,
                    SysSession.status == "ACTIVE")
                .order_by(SysSession.last_active_at.asc())
            )).scalars().all()

            max_sessions = config["max_sessions_per_account"]

            # 同终端覆盖
            if config["same_device_overwrite"] and payload.device_id:
                for s in existing:
                    if s.device_id == payload.device_id:
                        await self._revoke_one(s, "SAME_DEVICE_OVERWRITE")
                        existing.remove(s)
                        kicked.append(s.session_id)

            # 并发超限
            if len(existing) >= max_sessions:
                if config["overflow_strategy"] == "REJECT":
                    raise BizException(53022,
                        f"该账号已有 {max_sessions} 个活跃会话，请先下线其他设备")
                # 踢最旧
                to_kick = existing[:len(existing) - max_sessions + 1]
                for s in to_kick:
                    await self._revoke_one(s, "CONCURRENCY_LIMIT")
                    kicked.append(s.session_id)

        # 2. 生成 session_id
        session_id = f"sess_{uuid.uuid4().hex[:12]}"

        # 3. 签发 Token
        account = {
            "account_id": payload.account_id,
            "username": payload.username,
            "staff_id": payload.staff_id,
            "staff_code": payload.staff_code,
            "staff_name": payload.staff_name,
            "dept_id": payload.dept_id,
            "dept_name": payload.dept_name,
            "org_id": payload.org_id,
            "acct_type": payload.acct_type,
            "mfa_passed": payload.mfa_passed,
        }
        tokens = await self.token_svc.issue_tokens(session_id, account, config)

        # 4. 写会话
        sess = SysSession(
            session_id=session_id,
            account_id=payload.account_id,
            username=payload.username,
            staff_id=payload.staff_id,
            staff_code=payload.staff_code,
            staff_name=payload.staff_name,
            dept_id=payload.dept_id,
            dept_name=payload.dept_name,
            org_id=payload.org_id,
            acct_type=payload.acct_type,
            access_jti=tokens["jti"],
            refresh_hash=tokens["refresh_hash"],
            status="ACTIVE",
            login_type=payload.login_type,
            mfa_passed=payload.mfa_passed,
            login_ip=payload.login_ip,
            ip_location=self._ip_location(payload.login_ip),
            user_agent=payload.user_agent,
            device_type=payload.device_type,
            device_id=payload.device_id,
            login_at=now,
            last_active_at=now,
            expire_at=now + timedelta(days=config["refresh_token_ttl_days"]),
            idle_expire_at=now + timedelta(minutes=config["idle_timeout_min"]),
            refresh_count=0,
        )
        self.db.add(sess)
        await self.db.commit()

        # 5. 缓存状态
        await redis_client.setex(
            f"sys:session:status:{session_id}", 300, "ACTIVE")

        return {
            "session_id": session_id,
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": "Bearer",
            "expires_in": tokens["expires_in"],
            "refresh_expires_in": tokens["refresh_expires_in"],
            "idle_expire_at": sess.idle_expire_at.isoformat(),
            "kicked_session_ids": kicked,
        }

    # ---------- 活动心跳 ----------
    async def touch(self, session_id: str,
                     jti: Optional[str] = None) -> dict:
        """会话活动心跳（延长空闲超时）"""
        config = await self.token_svc._get_config()
        now = datetime.now()

        # 写 Redis（高频，不写库）
        await redis_client.setex(
            f"sys:session:active:{session_id}", 600, now.isoformat())

        new_idle = now + timedelta(minutes=config["idle_timeout_min"])
        await redis_client.setex(
            f"sys:session:idle:{session_id}", 600, new_idle.isoformat())

        return {
            "session_id": session_id,
            "idle_expire_at": new_idle.isoformat(),
            "extended": config["extend_idle_on_activity"],
        }

    # ---------- 吊销 ----------
    async def revoke(self, session_id: str, reason: str,
                      blacklist: bool = True) -> dict:
        """吊销单个会话（内部）"""
        sess = (await self.db.execute(
            select(SysSession).where(SysSession.session_id == session_id)
        )).scalar_one_or_none()

        if not sess:
            raise BizException(53011, f"会话 {session_id} 不存在")

        if sess.status != "ACTIVE":
            raise BizException(53032, f"会话状态为 {sess.status}，无需吊销")

        sess.status = "REVOKED"
        sess.revoked_at = datetime.now()
        sess.revoke_reason = reason
        await self.db.commit()

        blacklisted = False
        if blacklist and sess.access_jti:
            await self.blacklist.add(
                jti=sess.access_jti,
                session_id=session_id,
                account_id=sess.account_id,
                username=sess.username,
                reason=reason,
                ttl_seconds=1800)
            blacklisted = True

        await redis_client.setex(
            f"sys:session:status:{session_id}", 300, "REVOKED")

        return {
            "session_id": session_id,
            "revoked": True,
            "blacklisted": blacklisted,
        }

    async def revoke_account_internal(self, account_id: int, reason: str,
                                        exclude_session_id: Optional[str] = None) -> dict:
        """吊销账号全部会话（内部，供 M02-01 调用）"""
        stmt = select(SysSession).where(
            SysSession.account_id == account_id,
            SysSession.status == "ACTIVE")
        if exclude_session_id:
            stmt = stmt.where(SysSession.session_id != exclude_session_id)

        sessions = (await self.db.execute(stmt)).scalars().all()

        revoked, blacklisted = 0, 0
        for s in sessions:
            s.status = "REVOKED"
            s.revoked_at = datetime.now()
            s.revoke_reason = reason
            revoked += 1

            if s.access_jti:
                await self.blacklist.add(
                    jti=s.access_jti, session_id=s.session_id,
                    account_id=account_id, username=s.username,
                    reason=reason, ttl_seconds=1800)
                blacklisted += 1

            await redis_client.setex(
                f"sys:session:status:{s.session_id}", 300, "REVOKED")

        await self.db.commit()
        return {"account_id": account_id, "revoked": revoked,
                "blacklisted": blacklisted}

    # ---------- 用户自助 ----------
    async def list_my_sessions(self, user, authorization: str) -> dict:
        """我的会话列表"""
        sessions = (await self.db.execute(
            select(SysSession).where(
                SysSession.account_id == user.account_id,
                SysSession.status == "ACTIVE")
            .order_by(SysSession.last_active_at.desc())
        )).scalars().all()

        config = await self.token_svc._get_config()
        current_sid = getattr(user, "session_id", None)

        items = []
        for s in sessions:
            items.append({
                "session_id": s.session_id,
                "is_current": s.session_id == current_sid,
                "device_type": s.device_type,
                "device_name": self._device_name(s.user_agent),
                "login_ip": s.login_ip,
                "ip_location": s.ip_location,
                "login_at": s.login_at.isoformat() if s.login_at else None,
                "last_active_at": s.last_active_at.isoformat() if s.last_active_at else None,
                "last_active_text": self._relative_time(s.last_active_at),
                "expire_at": s.expire_at.isoformat() if s.expire_at else None,
                "idle_expire_at": s.idle_expire_at.isoformat() if s.idle_expire_at else None,
                "is_abnormal": self._is_abnormal(s),
            })

        return {
            "total": len(items),
            "max_allowed": config["max_sessions_per_account"],
            "current_session_id": current_sid,
            "items": items,
        }

    async def kick_one(self, session_id: str, user,
                        authorization: str) -> dict:
        """下线指定设备"""
        current_sid = getattr(user, "session_id", None)
        if session_id == current_sid:
            raise BizException(53017,
                "不能通过此接口下线当前会话，请使用登出功能")

        sess = (await self.db.execute(
            select(SysSession).where(SysSession.session_id == session_id)
        )).scalar_one_or_none()

        if not sess:
            raise BizException(53011, "会话不存在")

        if sess.account_id != user.account_id:
            raise BizException(53016, "该会话不属于当前用户")

        result = await self.revoke(session_id, "SELF_KICK")
        return {
            "session_id": session_id,
            "revoked": True,
            "message": "该设备已下线",
        }

    async def kick_others(self, user, authorization: str) -> dict:
        """下线所有其他设备"""
        current_sid = getattr(user, "session_id", None)
        result = await self.revoke_account_internal(
            user.account_id, "SELF_KICK_OTHERS",
            exclude_session_id=current_sid)
        return {
            "revoked_count": result["revoked"],
            "current_session_id": current_sid,
            "message": f"已下线 {result['revoked']} 个其他设备，当前设备保持登录",
        }

    # ---------- 管理 ----------
    async def admin_revoke(self, session_id: str, payload, operator) -> dict:
        """管理员强制下线"""
        sess = (await self.db.execute(
            select(SysSession).where(SysSession.session_id == session_id)
        )).scalar_one_or_none()
        if not sess:
            raise BizException(53011, "会话不存在")

        result = await self.revoke(session_id, "FORCE_LOGOUT")

        # 通知用户
        notified = False
        if payload.notify_user:
            notified = await self._notify_kicked(
                sess, payload.reason)

        return {
            "session_id": session_id,
            "revoked": True,
            "blacklisted_jti": sess.access_jti,
            "notified": notified,
            "reason": payload.reason,
        }

    async def _revoke_one(self, sess: SysSession, reason: str) -> None:
        """内部吊销（不抛异常）"""
        sess.status = "REVOKED"
        sess.revoked_at = datetime.now()
        sess.revoke_reason = reason
        if sess.access_jti:
            await self.blacklist.add(
                jti=sess.access_jti, session_id=sess.session_id,
                account_id=sess.account_id, username=sess.username,
                reason=reason, ttl_seconds=1800)
        await redis_client.setex(
            f"sys:session:status:{sess.session_id}", 300, "REVOKED")

    async def _notify_kicked(self, sess: SysSession, reason: str) -> bool:
        """通知被踢用户"""
        import httpx
        from app.core.config import settings
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                await client.post(
                    f"{settings.M20_BASE_URL}/internal/v1/message/send",
                    json={"staff_id": sess.staff_id,
                          "template": "SESSION_FORCED_LOGOUT",
                          "params": {"device": self._device_name(sess.user_agent),
                                     "reason": reason}})
            return True
        except Exception:
            return False

    # ---------- 状态文本 ----------
    @staticmethod
    def _device_name(ua: Optional[str]) -> str:
        """从 UA 提取设备名"""
        if not ua:
            return "未知设备"
        ua_lower = ua.lower()

        # 浏览器
        browser = "未知浏览器"
        for key, name in [("edg/", "Edge"), ("chrome/", "Chrome"),
                           ("firefox/", "Firefox"), ("safari/", "Safari")]:
            if key in ua_lower:
                browser = name
                break

        # 系统
        os_name = "未知系统"
        for key, name in [("windows nt 10", "Windows 10"),
                           ("windows nt 11", "Windows 11"),
                           ("mac os x", "macOS"),
                           ("android", "Android"),
                           ("iphone", "iOS"),
                           ("ipad", "iPadOS")]:
            if key in ua_lower:
                os_name = name
                break

        return f"{browser} / {os_name}"

    @staticmethod
    def _ip_location(ip: str) -> str:
        """IP 归属地"""
        if ip and ip.startswith(("192.168.", "10.", "172.", "127.")):
            return "院内网络"
        return "外部网络"

    @staticmethod
    def _relative_time(dt: Optional[datetime]) -> str:
        """相对时间文本"""
        if not dt:
            return "—"
        delta = (datetime.now() - dt).total_seconds()
        if delta < 60:
            return "刚刚"
        if delta < 3600:
            return f"{int(delta // 60)} 分钟前"
        if delta < 86400:
            return f"{int(delta // 3600)} 小时前"
        return f"{int(delta // 86400)} 天前"

    @staticmethod
    def _is_abnormal(sess: SysSession) -> bool:
        """是否异常会话"""
        return sess.ip_location == "外部网络"
```

---

## 7. 缓存与异步任务设计

### 7.1 Redis 缓存设计

| Key 模式 | 类型 | TTL | 说明 | 失效时机 |
|---|---|---|---|---|
| `sys:session:status:{sid}` | String | 300s | 会话状态 | 状态变更 |
| `sys:session:active:{sid}` | String | 600s | 最后活动时间 | 心跳更新 |
| `sys:session:idle:{sid}` | String | 600s | 空闲过期时间 | 心跳更新 |
| `sys:token:blacklist:{jti}` | String | 剩余时长 | 黑名单 | 自动过期 |
| `sys:jwt:active_key` | String(JSON) | 300s | 当前签名密钥 | 轮换 |
| `sys:jwt:verify_keys` | String(JSON) | 300s | 可验签密钥集 | 轮换 |
| `sys:session:config` | String(JSON) | 600s | 会话配置 | 配置修改 |
| `sys:account:status:{id}` | String | 60s | 账号状态 | 状态变更 |

**容量估算：**

| 数据 | 单条 | 数量 | 内存 |
|---|---|---|---|
| 会话状态 | 80B | 500 | 0.04 MB |
| 活动时间 | 100B | 500 | 0.05 MB |
| **黑名单** | 120B | 5,000 | **0.6 MB** |
| 密钥 | 500B | 3 | 0.002 MB |
| 配置 | 600B | 1 | 0.001 MB |
| **合计** | | | **约 0.7 MB** |

### 7.2 Celery 异步任务

```python
# app/tasks/auth/session_tasks.py
"""会话相关异步任务"""
from celery import shared_task


@shared_task
def flush_session_activity_task():
    """批量落库会话活动时间（每 5 分钟）"""
    import asyncio
    return asyncio.run(_flush_activity())


async def _flush_activity():
    """将 Redis 中的活动时间批量写回 DB"""
    from datetime import datetime
    from sqlalchemy import select, update
    from app.models.auth.session import SysSession
    from app.core.database import AsyncSessionLocal
    from app.core.redis import redis_client

    async with AsyncSessionLocal() as db:
        keys = await redis_client.keys("sys:session:active:*")
        updated = 0

        for key in keys:
            sid = key.decode().split(":")[-1] if isinstance(key, bytes) else key.split(":")[-1]
            val = await redis_client.get(key)
            if not val:
                continue
            try:
                last_active = datetime.fromisoformat(
                    val.decode() if isinstance(val, bytes) else val)
            except ValueError:
                continue

            await db.execute(
                update(SysSession)
                .where(SysSession.session_id == sid)
                .values(last_active_at=last_active)
            )
            updated += 1

        await db.commit()
        return {"flushed": updated, "keys": len(keys)}


@shared_task
def expire_idle_sessions_task():
    """扫描并过期空闲超时的会话"""
    import asyncio
    return asyncio.run(_expire_idle())


async def _expire_idle():
    """会话空闲超时处理"""
    from datetime import datetime
    from sqlalchemy import select
    from app.models.auth.session import SysSession
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        now = datetime.now()
        rows = (await db.execute(
            select(SysSession).where(
                SysSession.status == "ACTIVE",
                SysSession.idle_expire_at.isnot(None),
                SysSession.idle_expire_at < now)
        )).scalars().all()

        for s in rows:
            s.status = "EXPIRED"
            s.revoked_at = now
            s.revoke_reason = "IDLE_TIMEOUT"

        await db.commit()
        return {"expired": len(rows)}


@shared_task
def expire_absolute_sessions_task():
    """扫描并过期绝对超时的会话"""
    import asyncio
    return asyncio.run(_expire_absolute())


async def _expire_absolute():
    """会话绝对超时处理"""
    from datetime import datetime
    from sqlalchemy import select
    from app.models.auth.session import SysSession
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        now = datetime.now()
        rows = (await db.execute(
            select(SysSession).where(
                SysSession.status == "ACTIVE",
                SysSession.expire_at < now)
        )).scalars().all()

        for s in rows:
            s.status = "EXPIRED"
            s.revoked_at = now
            s.revoke_reason = "ABSOLUTE_TIMEOUT"

        await db.commit()
        return {"expired": len(rows)}


@shared_task
def archive_sessions_task():
    """归档 90 天前的终态会话"""
    import asyncio
    return asyncio.run(_archive())


async def _archive():
    """归档旧会话"""
    from datetime import datetime, timedelta
    from sqlalchemy import delete, select
    from app.models.auth.session import SysSession
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        threshold = datetime.now() - timedelta(days=90)
        rows = (await db.execute(
            select(SysSession).where(
                SysSession.status.in_(["EXPIRED", "REVOKED"]),
                SysSession.revoked_at < threshold)
            .limit(5000)
        )).scalars().all()

        for r in rows:
            await db.delete(r)
        await db.commit()
        return {"archived": len(rows)}
```

### 7.3 APScheduler 定时任务

| 任务名 | Cron | 说明 |
|---|---|---|
| `job_session_flush` | `*/5 * * * *` | 批量落库活动时间 |
| `job_session_expire_idle` | `*/2 * * * *` | 空闲超时扫描 |
| `job_session_expire_absolute` | `*/10 * * * *` | 绝对超时扫描 |
| `job_session_archive` | `0 3 * * *` | 归档旧会话 |
| `job_blacklist_cleanup` | `0 * * * *` | 清理过期黑名单 |
| `job_jwt_key_rotate_check` | `0 2 * * *` | 检查密钥轮换周期 |

```python
# app/tasks/auth/session_jobs.py
"""会话定时任务"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

scheduler.add_job(
    expire_idle,
    CronTrigger(minute="*/2"),
    id="job_session_expire_idle",
    name="空闲会话过期",
    replace_existing=True,
)

scheduler.add_job(
    rotate_keys_if_due,
    CronTrigger(hour=2, minute=0),
    id="job_jwt_key_rotate_check",
    name="密钥轮换检查",
    replace_existing=True,
)


async def rotate_keys_if_due():
    """检查密钥是否到期需轮换"""
    from datetime import datetime, timedelta
    from sqlalchemy import select
    from app.models.auth.session import SysJwtKey, SysSessionConfig
    from app.core.database import AsyncSessionLocal
    from app.services.auth.jwt_key_service import JwtKeyService

    async with AsyncSessionLocal() as db:
        cfg = (await db.execute(
            select(SysSessionConfig).where(SysSessionConfig.id == 1)
        )).scalar_one_or_none()
        if not cfg or not cfg.key_rotate_days:
            return {"skipped": "未配置轮换周期"}

        active = (await db.execute(
            select(SysJwtKey).where(SysJwtKey.status == "ACTIVE")
        )).scalar_one_or_none()
        if not active:
            return {"skipped": "无活跃密钥"}

        due = active.effective_at + timedelta(days=cfg.key_rotate_days)
        if datetime.now() >= due:
            svc = JwtKeyService(db)
            kid = f"k{datetime.now().strftime('%Y-%m')}"
            await svc.rotate_internal(kid)
            return {"rotated": True, "new_kid": kid, "due_at": due.isoformat()}

        return {"rotated": False, "due_at": due.isoformat()}
```

---

## 8. 业务规则与校验

### 8.1 Token 规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 签名必须有效 | HS256 + kid 匹配 | 53003 |
| 必须未过期 | `exp > now` | 53004 |
| 必须已生效 | `nbf <= now` | 53005 |
| 类型必须为 access | `typ=access` | 53006 |
| 受众必须匹配 | `aud=his-api` | 53008 |
| 签发者必须匹配 | `iss=m02-auth` | 53009 |
| 黑名单不可用 | `jti` 不在黑名单 | 53010 |
| 会话必须活跃 | `status=ACTIVE` | 53013 |
| 账号必须正常 | `account.status=ACTIVE` | 53029 |

### 8.2 刷新规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| Refresh 格式 | `rt_{hex32}_{account_id}` | 53018 |
| 必须未轮换 | 已轮换 → 重用检测 | 53020 |
| 必须未过期 | `expire_at > now` | 53021 |
| 会话必须活跃 | — | 53013 |
| 轮换 | 每次刷新生成新 Refresh | — |
| 重用检测 | 吊销整个会话 | 53020 |

### 8.3 会话规则

| 规则 | 说明 | 错误码 |
|---|---|---|
| 空闲超时 | 2 小时无操作 | 53014 |
| 绝对超时 | 7 天 | 53015 |
| 并发上限 | 5 个 | 53022 |
| 超限策略 | 踢最旧 | — |
| 同终端覆盖 | 同 device_id 覆盖 | — |
| 不能下线当前会话 | 用户自助接口 | 53017 |
| 只能下线自己会话 | 用户自助接口 | 53016 |

### 8.4 吊销规则

| 场景 | 是否吊销全部会话 | 是否加黑名单 |
|---|---|---|
| 用户登出 | 仅当前 | 是 |
| 修改密码 | 全部（保留当前） | 是 |
| 管理员重置密码 | 全部 | 是 |
| 账号停用 | 全部 | 是 |
| 账号锁定 | 全部 | 是 |
| 账号注销 | 全部 | 是 |
| 管理员强制下线 | 指定会话 | 是 |
| 并发超限 | 最旧会话 | 是 |
| Token 重用检测 | 整个会话 | 是 |

### 8.5 密钥轮换规则

| 规则 | 说明 |
|---|---|
| 新密钥立即生效 | 用于签发 |
| 旧密钥过渡 30 分钟 | 仍可验签 |
| 过渡后停用 | 不再验签 |
| 不删除历史密钥 | 保留审计 |
| 自动轮换 | 每 90 天 |

---

## 9. 权限与安全

### 9.1 功能权限

| 权限编码 | 说明 | 授予角色 |
|---|---|---|
| `sys:session:list` | 查看全部会话 | 系统管理员、信息科长 |
| `sys:session:revoke` | 强制下线 | 信息科长、系统管理员 |
| `sys:session:audit` | 查看会话历史 | 审计员 |
| `sys:session:config` | 会话配置 | 信息科长 |
| `sys:session:admin` | 黑名单/密钥管理 | 信息科长 |

### 9.2 权限矩阵

| 功能 | 系统管理员 | 信息科长 | 审计员 | 普通用户 |
|---|---|---|---|---|
| 我的会话 | ● | ● | ● | ● |
| 下线自己的设备 | ● | ● | ● | ● |
| 查看全部会话 | △ | ● | △ | — |
| 强制下线他人 | — | ● | — | — |
| 会话配置 | △ | ● | — | — |
| 黑名单管理 | — | ● | — | — |
| 密钥管理 | — | ● | — | — |
| 会话历史 | △ | ● | ● | — |

### 9.3 安全措施

| 措施 | 说明 |
|---|---|
| **Access 短期** | 30 分钟，泄露危害窗口小 |
| **Refresh 轮换** | 每次刷新更换，检测盗用 |
| **重用检测** | 检测到即吊销整个会话 |
| **黑名单** | 已吊销 Token 立即失效 |
| **密钥轮换** | 每 90 天，kid 标识版本 |
| **密钥加密存储** | 数据库中密文 |
| **空闲超时** | 防公共终端被遗忘 |
| **绝对超时** | 防会话永久存在 |
| **并发限制** | 防多设备共享账号 |
| **账号状态联查** | 停用后 Token 立即失效 |
| **不使用对称密钥明文** | 环境下发，不入代码库 |

### 9.4 Token 安全注意事项

| 风险 | 防护 |
|---|---|
| Token 泄露 | 短期 Access + 可吊销 |
| Token 重放 | 黑名单 + jti |
| Refresh 被盗 | 轮换 + 重用检测 |
| 算法混淆攻击 | 固定 `algorithms=["HS256"]` |
| kid 注入 | 白名单校验 kid |
| 密钥泄露 | 定期轮换 + 加密存储 |
| 签名绕过 | 强制验签，不允许 `alg=none` |
| 时钟偏移 | 允许 60 秒 `leeway` |

---

## 10. 集成与契约

### 10.1 与 M02-02 登录的契约

| 接口 | 用途 | SLA |
|---|---|---|
| `POST /internal/v1/session/create` | 创建会话并签发 Token | P95 ≤ 100ms |

**约定：**
- M02-02 认证成功后调用
- 返回 `kicked_session_ids` 供 M02-02 提示用户

### 10.2 与 M02-04 权限引擎的契约

| 接口 | 用途 | SLA |
|---|---|---|
| `POST /internal/v1/token/validate` | 校验 Token 并返回身份 | P95 ≤ 20ms |
| `POST /internal/v1/session/touch` | 会话心跳 | P95 ≤ 10ms |

**约定：**
- M02-04 **每次请求**先调 `validate`
- 校验结果包含 `account_id`，M02-04 据此取权限上下文
- `need_refresh=true` 时前端应主动刷新

### 10.3 与 M02-01 账号管理的契约

| 接口 | 用途 |
|---|---|
| `GET /internal/v1/account/{id}/status` | 查询账号状态（缓存 60s） |

**约定：**
- M02-01 在账号停用/锁定时调 `session/revoke-all`
- M02-03 校验时联查账号状态（降级容忍）

### 10.4 与 M02-07 安全策略的契约

| 接口 | 用途 |
|---|---|
| `GET /internal/v1/session/config` | 读取并发上限、超时配置 |

---

## 11. 异常处理与日志

### 11.1 异常分类

| 类型 | 示例 | 处理 |
|---|---|---|
| Token 格式错 | 缺字段、非 JWT | 53002 |
| 签名无效 | 密钥不匹配 | 53003 |
| Token 过期 | exp 已过 | 53004 |
| 会话异常 | 吊销、过期、超时 | 53012~53015 |
| 刷新异常 | 无效、轮换、重用 | 53018~53020 |
| 依赖异常 | M01 不可用 | 降级放行 |
| 系统异常 | DB 失败 | 50003 |

**降级策略：**

| 依赖 | 不可用时 |
|---|---|
| Redis（黑名单） | 跳过黑名单检查（安全性略降，可用性优先） |
| Redis（会话状态） | 直连 DB |
| M02-01（账号状态） | 放行（Token 本身的身份仍可信） |
| 签名密钥读取 | 使用本地缓存副本 |

### 11.2 日志规范

```json
{
  "timestamp": "2026-04-01T14:23:45.123+08:00",
  "level": "INFO",
  "logger": "app.services.auth.session_service",
  "trace_id": "3f2a1b9c",
  "action": "SESSION_CREATE",
  "session_id": "sess_9e8d7c6b5a4f",
  "account_id": 1024,
  "username": "wangwu",
  "login_ip": "192.168.10.55",
  "device_type": "PC",
  "kicked_count": 0,
  "cost_ms": 45,
  "message": "会话创建成功"
}
```

**禁止记录：**
- 完整 Access Token
- 完整 Refresh Token
- 签名密钥
- 用户密码

### 11.3 监控指标

| 指标 | 说明 | 告警阈值 |
|---|---|---|
| 接口错误率 | 5xx/总请求 | >1% |
| **Token 校验 P95** | 响应时间 | **>20ms** |
| 会话创建 P95 | 响应时间 | >100ms |
| **活跃会话数** | ACTIVE | >1000 |
| **Token 重用事件** | 每小时 | **>0（安全事件）** |
| 黑名单条目数 | — | >10000 |
| 强制下线次数 | 每小时 | >20 |
| 密钥轮换 | 是否按期 | 逾期 >7 天 |

---

## 12. 验收标准

### 12.1 功能验收

| 编号 | 验收项 | 验收方法 | 通过标准 |
|---|---|---|---|
| AC-01 | 创建会话 | 登录成功 | 返回双 Token |
| AC-02 | Token 校验-有效 | 校验 | valid=true |
| AC-03 | Token 校验-过期 | 等待 30 分钟 | TOKEN_EXPIRED |
| AC-04 | Token 校验-签名错 | 篡改 | SIGNATURE_INVALID |
| AC-05 | Token 校验-类型错 | 用 Refresh 访问 | TOKEN_TYPE_MISMATCH |
| AC-06 | Token 校验-受众错 | 改 aud | AUDIENCE_MISMATCH |
| AC-07 | Token 刷新 | 用 Refresh 刷新 | 返回新 Token |
| AC-08 | Refresh 轮换 | 刷新两次 | 旧 Refresh 失效 |
| AC-09 | **Refresh 重用检测** | 用旧 Refresh | **会话被吊销** |
| AC-10 | Refresh 过期 | 等 7 天 | REFRESH_EXPIRED |
| AC-11 | 登出吊销 | 登出后用旧 Token | 拒绝 |
| AC-12 | 黑名单生效 | 登出后校验 | TOKEN_BLACKLISTED |
| AC-13 | 我的会话列表 | 查询 | 显示全部设备 |
| AC-14 | 下线指定设备 | 点击下线 | 该设备 Token 失效 |
| AC-15 | 下线所有其他 | 点击 | 其他设备全部失效 |
| AC-16 | 不能下线当前 | 尝试 | 53017 |
| AC-17 | 不能下线他人 | 尝试 | 53016 |
| AC-18 | 并发超限踢旧 | 第 6 次登录 | 最旧被踢 |
| AC-19 | 同终端覆盖 | 同 device_id | 旧会话失效 |
| AC-20 | 空闲超时 | 2 小时无操作 | SESSION_IDLE_TIMEOUT |
| AC-21 | 活动延长空闲 | 持续操作 | 不超时 |
| AC-22 | 绝对超时 | 7 天 | SESSION_ABSOLUTE_TIMEOUT |
| AC-23 | 账号停用联查 | 停用账号 | Token 失效 |
| AC-24 | 密码修改吊销 | 改密 | 其他会话失效 |
| AC-25 | 管理员强制下线 | 强制下线 | 立即失效 |
| AC-26 | 批量下线 | 多选 | 全部失效 |
| AC-27 | 密钥轮换 | 轮换 | 新 Token 用新密钥 |
| AC-28 | 旧密钥过渡 | 轮换后 10 分钟 | 旧 Token 仍可验 |
| AC-29 | 过渡后旧密钥失效 | 轮换后 40 分钟 | 旧 Token 拒绝 |
| AC-30 | 会话配置修改 | 改超时 | 新会话生效 |
| AC-31 | 会话历史 | 查询 | 数据准确 |
| AC-32 | 黑名单移除 | 移除 | Token 可再用 |
| AC-33 | 权限控制 | 普通用户查全部会话 | 403 |

### 12.2 性能验收

| 编号 | 项 | 标准 |
|---|---|---|
| PF-01 | **Token 校验 P95** | **≤ 20ms** |
| PF-02 | Token 校验 P99 | ≤ 50ms |
| PF-03 | **Token 校验吞吐** | **≥ 5000 QPS** |
| PF-04 | 会话创建 P95 | ≤ 100ms |
| PF-05 | Token 刷新 P95 | ≤ 80ms |
| PF-06 | 我的会话列表 | ≤ 100ms |
| PF-07 | 会话心跳 | ≤ 10ms |
| PF-08 | 长稳测试 | 72 小时无内存泄漏 |

### 12.3 数据验收

| 编号 | 项 | 标准 |
|---|---|---|
| DA-01 | 会话完整率 | 100% |
| DA-02 | Token 不落库（仅哈希） | 100% |
| DA-03 | 密钥加密存储 | 100% |
| DA-04 | 吊销留痕率 | 100% |

### 12.4 安全验收

| 编号 | 项 | 标准 |
|---|---|---|
| SC-01 | Token 明文不入日志 | 0 处 |
| SC-02 | 密钥不入代码库 | 验证通过 |
| SC-03 | 算法固定 HS256 | 不可降级 |
| SC-04 | Refresh 重用检测 | 生效 |
| SC-05 | 黑名单生效 | 生效 |
| SC-06 | 跨账号访问会话 | 53016 |
| SC-07 | 越权强制下线 | 403 + 审计 |

---

## 附录 A：会话状态流转表

| 当前 | 事件 | 目标 | 是否加黑名单 |
|---|---|---|---|
| — | 登录成功 | ACTIVE | — |
| ACTIVE | 用户登出 | REVOKED | ✅ |
| ACTIVE | 空闲超时 | EXPIRED | — |
| ACTIVE | 绝对超时 | EXPIRED | — |
| ACTIVE | 密码修改 | REVOKED | ✅ |
| ACTIVE | 账号停用 | REVOKED | ✅ |
| ACTIVE | 强制下线 | REVOKED | ✅ |
| ACTIVE | 并发超限 | REVOKED | ✅ |
| ACTIVE | Token 重用 | REVOKED | ✅ |

---

## 附录 B：Token 字段对照

| 字段 | Access Token | Refresh Token |
|---|---|---|
| 格式 | JWT | `rt_{hex}_{id}` |
| 签发方 | M02-03 | M02-03 |
| 有效期 | 30 分钟 | 7 天 |
| 可吊销 | 黑名单 | 数据库 |
| 可轮换 | 否 | 是 |
| 含身份 | 是 | 否 |
| 含权限 | **否** | 否 |
| 存储位置 | 客户端 | 客户端 |

---

## 附录 C：吊销原因代码表

| 代码 | 说明 | 是否加黑名单 |
|---|---|---|
| `LOGOUT` | 用户登出 | ✅ |
| `PASSWORD_CHANGED` | 密码修改 | ✅ |
| `PASSWORD_RESET` | 管理员重置密码 | ✅ |
| `ACCOUNT_DISABLED` | 账号停用 | ✅ |
| `ACCOUNT_LOCKED` | 账号锁定 | ✅ |
| `ACCOUNT_TERMINATED` | 账号注销 | ✅ |
| `FORCE_LOGOUT` | 管理员强制下线 | ✅ |
| `CONCURRENCY_LIMIT` | 并发超限 | ✅ |
| `SAME_DEVICE_OVERWRITE` | 同终端覆盖 | ✅ |
| `TOKEN_REUSE` | Token 重用检测 | ✅ |
| `SELF_KICK` | 用户踢出其他设备 | ✅ |
| `SELF_KICK_OTHERS` | 用户踢出所有其他 | ✅ |
| `RENEW` | Access 续期（旧 jti） | ✅ |
| `IDLE_TIMEOUT` | 空闲超时 | — |
| `ABSOLUTE_TIMEOUT` | 绝对超时 | — |

---

## 附录 D：系统参数

| 参数编码 | 名称 | 类型 | 默认值 | 说明 |
|---|---|---|---|---|
| `SYS.SESSION.ACCESS_TTL_MIN` | Access 有效期 | INTEGER | 30 | 分钟 |
| `SYS.SESSION.REFRESH_TTL_DAYS` | Refresh 有效期 | INTEGER | 7 | 天 |
| `SYS.SESSION.IDLE_TIMEOUT_MIN` | 空闲超时 | INTEGER | 120 | 分钟 |
| `SYS.SESSION.ABSOLUTE_DAYS` | 绝对超时 | INTEGER | 7 | 天 |
| `SYS.SESSION.MAX_PER_ACCOUNT` | 最大并发会话 | INTEGER | 5 | 个 |
| `SYS.SESSION.OVERFLOW_STRATEGY` | 超限策略 | STRING | KICK_OLDEST | — |
| `SYS.SESSION.SAME_DEVICE_OVERWRITE` | 同终端覆盖 | BOOLEAN | true | — |
| `SYS.SESSION.ADMIN_UNLIMITED` | 管理员不限 | BOOLEAN | true | — |
| `SYS.SESSION.REFRESH_ROTATION` | Refresh 轮换 | BOOLEAN | true | — |
| `SYS.SESSION.DETECT_TOKEN_REUSE` | 重用检测 | BOOLEAN | true | — |
| `SYS.SESSION.EXTEND_REFRESH` | 刷新延长 | BOOLEAN | false | — |
| `SYS.SESSION.USE_BLACKLIST` | 使用黑名单 | BOOLEAN | true | — |
| `SYS.JWT.ALGORITHM` | 签名算法 | STRING | HS256 | — |
| `SYS.JWT.KEY_ROTATE_DAYS` | 密钥轮换周期 | INTEGER | 90 | 天 |
| `SYS.JWT.TRANSITION_MIN` | 密钥过渡期 | INTEGER | 30 | 分钟 |
| `SYS.JWT.LEEWAY_SECONDS` | 时钟容忍 | INTEGER | 60 | 秒 |

---

## 附录 E：术语表

| 术语 | 说明 |
|---|---|
| Access Token | 访问令牌，短期有效 |
| Refresh Token | 刷新令牌，长期有效 |
| JWT | JSON Web Token |
| jti | JWT 唯一 ID |
| sid | 会话 ID |
| kid | 密钥 ID |
| 轮换 | 每次刷新更换 Refresh Token |
| 重用检测 | 检测已轮换的 Refresh 被再次使用 |
| 黑名单 | 已吊销但未过期的 Token 列表 |
| 空闲超时 | 无操作超时 |
| 绝对超时 | 从登录起算的最大时长 |
| 并发会话 | 同一账号的多个活跃会话 |
| 密钥轮换 | 定期更换签名密钥 |

---

**文档结束**

| 版本 | 日期 | 修订说明 | 修订人 |
|---|---|---|---|
| V1.0 | 2026-10-19 | 首次发布：页面 8 个、数据表 6 张（见数据结构文件）、接口 29 个 | 系统设计组 |
