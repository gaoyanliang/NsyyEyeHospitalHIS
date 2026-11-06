"""M19 文档交付前自动校验。

用法：
    python3 validate_m19.py M19随访与会员管理

校验项：
  1. 代码围栏配对 / Python 块 ast / JSON 块 json.loads / 表格列数 / 乱码 / 占位词 / MySQL 残留
  2. 详细设计 1~12 章 + 附录 A~F 齐全，第 4 章无表定义
  3. 页面总览树 P0x 与第 5 章 "### 5.x P0x" 双向一致
  4. 接口 API-01 起连续无断号，每一项都有 "#### API-xx" 详述
  5. AC>=35 / PF>=8 / DA>=5 / SC>=4，四类从 01 连续
  6. 错误码 7 位、号段 190N0xxx 不越界
  7. 数据结构：表前缀 m19_、表清单与 "### 4.x 表：" 一致、SQLAlchemy/Pydantic 章节、版本历史
  8. 【M19 专属·铁律2】禁止重造 M03-04 随访计划/任务表（m19_followup_plan / m19_followup_task）
  9. 【M19 专属·铁律2】禁止重造 M03-03 会员等级/权益定义表（m19_member_level / m19_member_benefit）
 10. 【M19 专属】随访任务状态与优先级枚举必须与 M03-04 逐字一致
 11. 【M19 专属·铁律4】积分流水/成长值流水表必须 REVOKE UPDATE, DELETE
 12. 【M19 专属】积分流水必须有 balance_after；金额/比率字段不得使用 FLOAT/DOUBLE/REAL
 13. 【M19 专属】权益核销表必须有幂等唯一键
 14. 【M19 专属·铁律5】触达类接口必须写明黑名单/退订校验
 15. 【M19 专属】P-xx 内部契约路径必须与共享规范 §8 一字不差
 16. 同一错误码在全文多处出现时语义必须与权威定义表一致（共享规范 §11.1）
 17. 模块级文档（总纲 / 汇总 / 共享规范）走独立检查
"""
import ast
import json
import re
import sys
from pathlib import Path

FENCE = chr(96) * 3
BAD_SQL = ("AUTO_INCREMENT", "TINYINT", "DATETIME", "ENGINE=", "VARCHAR2")
PLACEHOLDERS = ("TODO", "待补充", "XXX 表", "略。")
SKIP_TABLES = ("IF", "NOT", "EXISTS", "PARTITION", "SELECT", "AS")

MODULE_DOCS = (
    "00_M19_随访与会员管理_模块设计_共享规范与文档模板.md",
    "M19_随访与会员管理_详细设计.md",
    "M19_随访与会员管理_数据结构设计汇总.md",
)

# ---------------------------------------------------------------- M19 专属常量

# 铁律 2：这些表由 M03-04 / M03-03 拥有，M19 只允许逻辑引用，绝不允许建表。
FORBIDDEN_TABLES = {
    # M03-04 随访：模板 / 计划 / 任务 / 分派规则
    "m19_followup_plan": "随访计划归 M03-04（mpi_followup_plan）",
    "m19_followup_task": "随访任务归 M03-04（mpi_followup_task）",
    "m19_followup_template": "随访模板归 M03-04（mpi_followup_template）",
    "m19_followup_node": "随访节点归 M03-04（mpi_followup_template_node）",
    "m19_followup_assign_rule": "随访分派规则归 M03-04（mpi_followup_assign_rule）",
    # M03-03 会员：等级 / 权益定义 / 标签 / 会员主档
    "m19_member_level": "会员等级归 M03-03（mpi_member_level）",
    "m19_member_benefit": "权益定义归 M03-03（mpi_member_benefit）",
    "m19_member_level_benefit": "等级权益归 M03-03（mpi_member_level_benefit）",
    "m19_member_tag": "会员标签归 M03-03（mpi_member_tag）",
    "m19_member": "会员主档归 M03-03（mpi_member）",
}

# M03-04 已冻结的枚举，M19 必须逐字一致
M03_TASK_STATUS = ("PENDING", "ASSIGNED", "EXECUTING", "COMPLETED",
                   "CANCELLED", "OVERDUE", "FAILED")
M03_TASK_PRIORITY = ("HIGH", "NORMAL", "LOW")

# 铁律 4：只增不改的流水表
APPEND_ONLY_TABLES = ("m19_points_ledger", "m19_points_growth_ledger")

# 凡含这些词的接口/页面描述，必须同时出现黑名单/退订校验说明（铁律 5）
TOUCH_KEYWORDS = ("发送短信", "发送微信", "外呼", "触达", "关怀消息", "拨打",
                  "推送", "营销短信", "提醒发送")
GATE_KEYWORDS = ("退订", "黑名单", "check-blacklist", "免打扰", "频次")

# ---------------------------------------------------------------- 内部契约总线
# 与共享规范 §8 表格逐字一致；M19-04 的 P-05 是 M03-03 已预留的路径，
# 写错会导致会员详情页积分展示全空，故单独校验。
CONTRACTS = {
    "P-01": ("GET", "/internal/v1/m19/followup/pending-tasks", "M19-01"),
    "P-02": ("GET", "/internal/v1/m19/followup/adherence/{patient_id}", "M19-08"),
    "P-03": ("POST", "/internal/v1/m19/points/grant", "M19-04"),
    "P-04": ("POST", "/internal/v1/m19/points/deduct", "M19-04"),
    "P-05": ("GET", "/internal/v1/member/{id}/points", "M19-04"),
    "P-06": ("POST", "/internal/v1/m19/benefits/redeem", "M19-05"),
    "P-07": ("POST", "/internal/v1/m19/benefits/revoke", "M19-05"),
    "P-08": ("GET", "/internal/v1/m19/benefits/available", "M19-05"),
    "P-09": ("POST", "/internal/v1/m19/care/trigger", "M19-03"),
    "P-10": ("GET", "/internal/v1/m19/member/value-segment/{member_id}", "M19-06"),
    "P-11": ("GET", "/internal/v1/m19/followup/exec-status/{task_id}", "M19-02"),
    "P-12": ("POST", "/internal/v1/m19/followup/export-result", "M19-08"),
}

# 上游已存在的契约（用于「不得臆造路径」的粗查）——只登记 M19 必须实现/调用的核心路径
# 避免误报：这里只做「P-xx 路径」精确校验，上游路径由人工核对。


def split_table(t):
    out, buf, start = [], [], 0
    for i, line in enumerate(t.split("\n"), 1):
        if line.startswith("|"):
            if not buf:
                start = i
            buf.append(line)
        elif buf:
            out.append((start, "\n".join(buf)))
            buf = []
    if buf:
        out.append((start, "\n".join(buf)))
    return out


def is_sep_row(line):
    s = line.strip().strip("|")
    return bool(s) and all(c in "-: " for c in s) and "-" in s


def count_cols(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len(re.split(r"(?<!\\)\|", s))


def check_common(fp, t):
    issues = []

    if t.count(FENCE) % 2:
        issues.append((0, "代码围栏未配对"))

    for i, b in enumerate(re.findall(FENCE + r"python\n(.*?)" + FENCE, t, re.S), 1):
        try:
            ast.parse(b)
        except SyntaxError as e:
            issues.append((0, "Python 块 #%d 语法错误: %s" % (i, e.msg)))
        except Exception as e:  # noqa: BLE001
            issues.append((0, "Python 块 #%d 解析异常: %s" % (i, e)))

    for i, j in enumerate(re.findall(FENCE + r"json\n(.*?)" + FENCE, t, re.S), 1):
        try:
            json.loads(j)
        except Exception as e:  # noqa: BLE001
            issues.append((0, "JSON 块 #%d 解析失败: %s" % (i, e)))

    for ln, tb in split_table(t):
        rows = [x for x in tb.split("\n") if x.strip()]
        core = [x for x in rows if not is_sep_row(x)]
        if len(core) >= 2 and len({count_cols(x) for x in core}) > 1:
            issues.append((ln, "表格列数不一致（起始行 %d）" % ln))

    if chr(0xFFFD) in t:
        issues.append((0, "存在乱码字符 U+FFFD"))
    for kw in BAD_SQL:
        if kw in t:
            issues.append((0, "MySQL 残留语法: %s" % kw))
    for kw in PLACEHOLDERS:
        if kw not in t:
            continue
        hit = [t[max(0, i - 8):i + len(kw) + 8]
               for i in [m for m in range(len(t)) if t.startswith(kw, m)]]
        issues.append((0, "存在占位词: %s（上下文: %s）" % (kw, hit[:3])))

    return issues


# ---------------------------------------------------------------- M19 专属校验


def _submodule_no(t):
    """从标题里取子模块编号，如 "M19-04"。"""
    m = re.search(r"M19-(\d\d)[\s_]", t[:2500])
    return m.group(1) if m else None


def check_boundary(t, fp_name):
    """铁律 2：不得重造 M03-04 / M03-03 拥有的表。

    判定只看「建表」动作，不看文字引用：
      - `### 4.x 表：`m19_followup_plan`` 这样的表定义标题
      - `CREATE TABLE m19_followup_plan`
    在正文里写「不建 m19_followup_plan」是合法的（甚至鼓励），不算违规。
    """
    issues = []
    # 禁止性说明（「❌ 禁止：CREATE TABLE m19_followup_plan」这类自检/红线清单）
    # 不是建表动作，不能误报。故剔除以 ❌/禁止/不得/严禁 开头的行再扫描。
    body = "\n".join(ln for ln in t.split("\n")
                     if not re.search(r"❌|禁止|不得|严禁|切勿", ln))
    defined = re.findall(r"^### 4\.\d+ 表：\s*`?(\w+)", body, re.M)
    created = re.findall(
        r"CREATE TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_]\w*)", body)
    for tb in set(defined) | set(c for c in created if c.lower() == c):
        if tb in FORBIDDEN_TABLES:
            issues.append((0, "【铁律2】不得建表 %s —— %s"
                           % (tb, FORBIDDEN_TABLES[tb])))
    return issues


def check_followup_enum(t, fp_name):
    """随访任务状态与优先级必须与 M03-04 逐字一致。

    只在文件确实出现「随访任务状态」概念时校验，避免误伤纯会员子模块。
    """
    issues = []
    if not re.search(r"PENDING", t):
        return issues

    # 自创枚举值检测：M19 里不允许出现的「状态词」
    for bad in ("'DONE'", '"DONE"', "'FINISHED'", '"FINISHED"',
                "'EXECUTED'", '"EXECUTED"'):
        if bad in t:
            issues.append((0, "随访状态枚举自创 %s，M03-04 只有 COMPLETED/FAILED"
                           % bad))

    # 若文件声明了完整状态枚举，则必须与 M03-04 集合完全一致
    for m in re.finditer(r"status\s+(?:IN|=)\s*\(([^)]*)\)", t):
        vals = set(re.findall(r"'([A-Z_]+)'", m.group(1)))
        if not vals:
            continue
        # 只关心「像随访任务状态」的那一组：至少含 PENDING 且不含明显的积分/券词
        if "PENDING" not in vals:
            continue
        if vals & {"UNUSED", "LOCKED", "VOIDED", "AVAILABLE", "REVOKED"}:
            continue
        # V1.2 收窄（M19-03 报的误伤）：原条件「含 EXECUTING/OVERDUE/ASSIGNED
        # 或 >= 5 个值」会把 care_task 六态
        # (PENDING/SENDING/DELIVERED/FAILED/CANCELLED/SUPPRESSED) 强判为随访任务
        # 状态并报「与 M03-04 不一致」。现要求命中下面三种「随访任务独有特征」
        # 之一才判定，其他子模块的任务态（关怀任务、核销任务等）不再误伤：
        #   ① 出现 EXECUTING/OVERDUE/ASSIGNED —— M03-04 七态独有的三个值
        #   ② 恰好 7 个值且同时含 PENDING/COMPLETED/CANCELLED —— 七态特征
        #   ③ 该 status 片段前 200 字内出现 followup 字样
        near = t[max(0, m.start() - 200):m.start()]
        is_followup_like = (
            bool(vals & {"EXECUTING", "OVERDUE", "ASSIGNED"})
            or (len(vals) == 7
                and {"PENDING", "COMPLETED", "CANCELLED"} <= vals)
            or re.search(r"followup", near, re.I) is not None
        )
        if is_followup_like and vals != set(M03_TASK_STATUS):
            issues.append((0, "随访任务状态枚举与 M03-04 不一致：多=%s 少=%s"
                           % (sorted(vals - set(M03_TASK_STATUS)),
                              sorted(set(M03_TASK_STATUS) - vals))))
    return issues


def check_append_only(t, fp_name):
    """铁律 4：积分/成长值流水只增不改。"""
    issues = []
    if not fp_name.endswith("_数据结构.md"):
        return issues
    for tb in APPEND_ONLY_TABLES:
        if not re.search(r"^### 4\.\d+ 表：\s*`?%s\b" % tb, t, re.M):
            continue
        pat = r"REVOKE\s+UPDATE\s*,\s*DELETE\s+ON\s+%s\b" % tb
        if not re.search(pat, t, re.I):
            issues.append((0, "【铁律4】流水表 %s 必须 REVOKE UPDATE, DELETE" % tb))
        if "balance_after" not in t:
            issues.append((0, "流水表 %s 缺少 balance_after（本条流水后余额，对账必需）"
                           % tb))
    return issues


def check_numeric_types(t, fp_name):
    """金额/比率/积分字段不得使用浮点。"""
    issues = []
    if not fp_name.endswith("_数据结构.md"):
        return issues
    pat = (r"`(\w*(?:amount|points|balance|rate|ratio|money|price|growth|score)\w*)`"
           r"\s*\|\s*(FLOAT|DOUBLE|REAL)")
    for m in re.finditer(pat, t, re.I):
        issues.append((0, "数值字段 %s 使用了浮点类型 %s，应为 NUMERIC"
                       % (m.group(1), m.group(2))))
    return issues


def check_redeem_idempotent(t, fp_name):
    """铁律 6：权益核销必须幂等。"""
    issues = []
    if not fp_name.endswith("_数据结构.md"):
        return issues
    if not re.search(r"^### 4\.\d+ 表：\s*`?m19_benefit_redeem\b", t, re.M):
        return issues
    if not re.search(r"uk_\w*redeem", t, re.I):
        issues.append((0, "【铁律6】核销表 m19_benefit_redeem 缺少幂等唯一键 uk_..._redeem"))
    if not re.search(r"FOR\s+UPDATE", t, re.I):
        issues.append((0, "【铁律6】核销必须对权益实例行加 FOR UPDATE 锁"))
    return issues


def check_touch_gates(t, fp_name):
    """铁律 5：触达类接口必须写明退订/黑名单校验。"""
    issues = []
    if not fp_name.endswith("_详细设计.md"):
        return issues
    hit = [k for k in TOUCH_KEYWORDS if k in t]
    if not hit:
        return issues
    if not any(g in t for g in GATE_KEYWORDS):
        issues.append((0, "【铁律5】文件涉及对外触达（%s），但全文没有退订/黑名单/免打扰校验说明"
                       % "/".join(hit[:3])))
    return issues


def check_contract_paths(t, fp_name):
    """P-xx 内部契约路径必须与共享规范 §8 一字不差。

    只校验「本文件声称提供了某个 P-xx」的情形：在 `| P-xx |` 表格行里出现路径时，
    路径必须等于 CONTRACTS 里登记的那一条。
    """
    issues = []
    for m in re.finditer(r"^\|[^|\n]*\b(P-\d\d)\b[^|\n]*\|[^|\n]*\|[^|\n]*"
                         r"(/internal/v1/[^|\s`)]*)", t, re.M):
        pid, path = m.group(1), m.group(2).rstrip("，,、;；")
        if pid not in CONTRACTS:
            continue
        want = CONTRACTS[pid][1]
        if path != want:
            issues.append((0, "内部契约 %s 路径不符：文档=%s 规范=%s"
                           % (pid, path, want)))
    return issues


def check_no_duplicate_sections(t, fp_name):
    """关键章节必须唯一（多人并行补同一文件时极易产生重复）。"""
    issues = []
    body = re.sub(r"(?ms)^#{0,2}?\s*`{4}.*?`{4}", "", t)

    must_once = [
        (r"^## 附录 F", "附录 F"),
        (r"^\*\*文档结束\*\*", "文档结束"),
    ]
    if fp_name.endswith("_数据结构.md"):
        n_h = len(re.findall(r"^## 版本历史", body, re.M))
        n_t = len(re.findall(r"^\| 版本 \| 日期 \|", body, re.M))
        if max(n_h, n_t) > 1:
            issues.append((0, "版本历史 出现 %d 次（应为 1 次，疑似重复）" % max(n_h, n_t)))
        must_once.append((r"^### 4\.\d+ Pydantic Schema 定义", "Pydantic Schema 章节"))

    for pat, label in must_once:
        n = len(re.findall(pat, body, re.M))
        if n > 1:
            issues.append((0, "%s 出现 %d 次（应为 1 次，疑似多人并行写入产生重复）"
                           % (label, n)))

    for lt in "ABCDEF":
        n = len(re.findall(r"^## 附录 %s" % lt, body, re.M))
        if n > 1:
            issues.append((0, "附录 %s 出现 %d 次" % (lt, n)))

    return issues


def check_module_doc(t):
    issues = []
    h2 = re.findall(r"^## (.+)$", t, re.M)
    if len(h2) < 5:
        issues.append((0, "二级章节过少（%d），疑似内容缺失" % len(h2)))
    return issues


def check_design(t):
    issues = []

    if re.search(r"^### 4\.\d+ 表：", t, re.M):
        issues.append((0, "第 4 章残留表定义（应为指引块）"))

    for n in range(1, 13):
        if not re.search(r"^## %d\. " % n, t, re.M):
            issues.append((0, "缺少第 %d 章标题" % n))

    for lt in "ABCDEF":
        if not re.search(r"^## 附录 %s" % lt, t, re.M):
            issues.append((0, "缺少附录 %s" % lt))

    pages_tree = re.findall(r"[├└]──\s*(P\d\d)", t)
    pages_h5 = re.findall(r"^### 5\.\d+\s+(P\d\d)", t, re.M)
    s_tree, s_h5 = set(pages_tree), set(pages_h5)
    if s_tree != s_h5:
        issues.append((0, "页面总览与第 5 章不一致: 仅总览=%s 仅详述=%s"
                       % (sorted(s_tree - s_h5), sorted(s_h5 - s_tree))))

    # 接口总览只在第 6.1 节内统计；附录对照表里的 `| API-xx |` 不是接口定义。
    sec61 = re.search(r"(?ms)^### 6\.1 .*?(?=^### 6\.2 )", t)
    scope = sec61.group(0) if sec61 else t
    apis = [int(x) for x in re.findall(r"^\|\s*\**API-(\d+)\**\s*\|", scope, re.M)]
    if apis:
        expect = list(range(1, max(apis) + 1))
        if sorted(set(apis)) != expect:
            miss = sorted(set(expect) - set(apis))
            issues.append((0, "接口编号不连续，缺失: %s" % miss))
        if len(apis) != len(set(apis)):
            dup = sorted({x for x in apis if apis.count(x) > 1})
            issues.append((0, "接口编号重复: %s" % dup))
        detailed = {int(x) for x in re.findall(r"^#### API-(\d+)", t, re.M)}
        no_detail = sorted(set(expect) - detailed)
        if no_detail:
            issues.append((0, "接口总览有但 6.3 无详述: %s" % no_detail[:20]))

    for kind, low in (("AC", 35), ("PF", 8), ("DA", 5), ("SC", 4)):
        nums = [int(x) for x in re.findall(r"^\|\s*%s-(\d+)\s*\|" % kind, t, re.M)]
        if not nums:
            issues.append((0, "缺少 %s 验收" % kind))
            continue
        if sorted(set(nums)) != list(range(1, max(nums) + 1)):
            issues.append((0, "%s 编号不连续" % kind))
        if len(set(nums)) < low:
            issues.append((0, "%s 数量 %d 少于要求 %d" % (kind, len(set(nums)), low)))

    sub = _submodule_no(t)
    for c in sorted(set(re.findall(r'"(\d{6,7})"', t))):
        if len(c) == 7 and c.startswith("19"):
            if sub and c[2:4] not in (sub, "90", "00"):
                issues.append((0, "错误码号段越界: %s（应为 M19-%s）" % (c, sub)))
        elif c == "199001":
            pass
        else:
            issues.append((0, "错误码格式异常: %s（应为 7 位 190Nxxx 或 199001）" % c))

    return issues


def check_struct(t):
    issues = []

    tables = re.findall(r"^### 4\.\d+ 表：`(\w+)`", t, re.M)
    for tb in tables:
        if not tb.startswith("m19_"):
            issues.append((0, "表名前缀错误: %s" % tb))
    if len(tables) != len(set(tables)):
        issues.append((0, "表定义重复"))

    if "SQLAlchemy 2.0 模型定义" not in t:
        issues.append((0, "缺少 SQLAlchemy 模型章节"))
    if "Pydantic Schema 定义" not in t:
        issues.append((0, "缺少 Pydantic Schema 章节"))

    ddl = re.findall(r"CREATE TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_%]\w*)", t)
    for tb in ddl:
        if tb in SKIP_TABLES or not tb.replace("%", "").replace("I", "").isalnum():
            continue
        if not tb.startswith("m19_"):
            issues.append((0, "DDL 表前缀错误: %s" % tb))

    n_tab = len(set(tables))
    for pat in (r"\*\*表数量：\*\*\s*(\d+)\s*张", r"\*\*合计：\s*(\d+)\s*张表\*\*"):
        m = re.search(pat, t)
        if m and int(m.group(1)) != n_tab:
            issues.append((0, "表数量声明 %s 与实际 %d 不符" % (m.group(1), n_tab)))

    if not re.search(r"^\| 版本 \|", t, re.M) and not re.search(r"^## 版本历史", t, re.M):
        issues.append((0, "缺少版本历史"))

    return issues


# ---------------------------------------------------------------- 错误码语义一致性

def _norm_sem(s):
    s = re.sub(r"[`*_]", "", s)
    s = re.sub(r"\s+", "", s)
    return s.rstrip("。；;,，.")


CODE_RE = re.compile(r"\b(\d{7})\b")


def _cell_code(cell):
    s = re.sub(r"[`*\s\"']", "", cell)
    m = CODE_RE.search(s)
    if not m:
        return None
    rest = s.replace(m.group(1), "", 1)
    return m.group(1) if not rest else None


def _is_fixed_header(h):
    h = _norm_sem(h)
    return any(k in h for k in ("HTTP", "状态码", "触发", "场景", "接口", "分类",
                                "所属", "级别", "是否", "常量", "重试", "码段", "号段"))


CATEGORY_WORDS = ("系统", "参数", "业务", "数据", "安全", "计算", "权限", "网络", "配置")


def _pick_sem_index(hdr, ci):
    cleaned = [_norm_sem(h) for h in hdr]
    for key in ("含义", "错误信息", "消息", "说明", "描述"):
        for i, h in enumerate(cleaned):
            if i != ci and key in h and not _is_fixed_header(h):
                return i
    return None


def _code_semantics(t):
    sec66 = re.search(r"(?ms)^### 6\.6 .*?(?=^### 6\.7 |^## 7\. )", t)
    for scope in ([sec66.group(0)] if sec66 else []) + [t]:
        out = _sem_table(scope)
        if out:
            return out
    return {}


def row_c(cells, i):
    return cells[i] if i < len(cells) else ""


def _sem_table(t):
    out = {}
    hdr = None
    for line in t.split("\n"):
        if not line.startswith("|"):
            hdr = None
            continue
        if is_sep_row(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if hdr is None:
            hdr = cells
            continue
        if len(cells) != len(hdr):
            continue
        ci = next((i for i, h in enumerate(hdr) if "错误码" in _norm_sem(h)), None)
        if ci is None:
            continue
        code = _cell_code(row_c(cells, ci))
        if not code:
            continue
        si = _pick_sem_index(hdr, ci)
        if si is None:
            continue
        sem = _norm_sem(row_c(cells, si))
        if sem:
            out.setdefault(code, sem)
    return out


def _sim(a, b):
    def grams(s):
        s = re.sub(r"[\s，。；、：（）()\[\]【】/\\|]", "", s)
        return {s[i:i + 2] for i in range(len(s) - 1)} if len(s) > 1 else {s}
    ga, gb = grams(a), grams(b)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / min(len(ga), len(gb))


def _sem_like(s):
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def check_errcode_semantics(t, fp_name):
    """同一错误码在全文多处出现时语义必须一致（共享规范 §11.1）。"""
    issues = []
    canon = _code_semantics(t)
    if not canon:
        return issues

    hdr = None
    skip_table = False
    for i, line in enumerate(t.split("\n"), 1):
        if not line.startswith("|"):
            hdr = None
            skip_table = False
            continue
        if is_sep_row(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if hdr is None:
            hdr = cells
            skip_table = any(re.search(r"提示|话术|消息文案", _norm_sem(h)) for h in hdr)
            continue
        if skip_table or len(cells) != len(hdr):
            continue
        for idx in range(len(cells)):
            code = _cell_code(cells[idx])
            if not code or code not in canon:
                continue
            desc = None
            for c in cells[idx + 1:]:
                s = _norm_sem(c)
                if not s or re.fullmatch(r"\d{3}", s):
                    continue
                if s in CATEGORY_WORDS:
                    continue
                if _sem_like(s):
                    desc = s
                    break
            if not desc or desc in ("—", "-", "无"):
                continue
            a, b = canon[code], desc
            if a in b or b in a or _sim(a, b) >= 0.30:
                continue
            issues.append((i, "错误码 %s 语义与权威定义表不一致：定义=「%s」此处=「%s」"
                           % (code, canon[code][:40], desc[:40])))
    return issues


def validate(fp):
    t = fp.read_text(encoding="utf-8")
    issues = check_common(fp, t)
    issues += check_boundary(t, fp.name)
    issues += check_followup_enum(t, fp.name)
    issues += check_append_only(t, fp.name)
    issues += check_numeric_types(t, fp.name)
    issues += check_redeem_idempotent(t, fp.name)
    issues += check_touch_gates(t, fp.name)
    issues += check_contract_paths(t, fp.name)
    issues += check_errcode_semantics(t, fp.name)
    if not fp.name.startswith("00_"):
        issues += check_no_duplicate_sections(t, fp.name)

    if fp.name in MODULE_DOCS or fp.name.startswith("00_"):
        issues += check_module_doc(t)
    elif fp.name.endswith("_数据结构.md"):
        issues += check_struct(t)
    else:
        issues += check_design(t)

    return issues


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    fails = 0
    total = 0
    for fp in sorted(root.glob("M19_*.md")):
        total += 1
        issues = validate(fp)
        if issues:
            fails += 1
            print("✗ %s" % fp.name)
            for ln, msg in issues:
                print("    L%s %s" % (ln, msg))
        else:
            print("✓ %s" % fp.name)
    print("✓ 全部通过（%d 个文件）" % total if fails == 0
          else "✗ %d / %d 个文件存在问题" % (fails, total))
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
