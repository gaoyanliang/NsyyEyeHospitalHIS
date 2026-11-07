#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 移动办公模块文档校验器。

用法：
    python3 M20移动办公/validate_m20.py M20移动办公

校验项（19 项，编号与共享规范 §16 对应）：
 1 通用格式：围栏配对 / python 块 ast.parse / json 块 json.loads / 表格列数 / 乱码 / 禁用词 / MySQL 残留
 2 详细设计：第 1~12 章 + 附录 A~F 齐全；第 4 章无表定义
 3 页面树（第 5.1 总览）与第 5 章逐页标题（### 5.x P0x）双向一致
 4 接口：API-01 起连续无断号，且每个都有 #### API-xx 详述
 5 验收：AC / PF / DA / SC 四类各自从 01 连续，且 AC>=35 PF>=8 DA>=5 SC>=4
 6 错误码：7 位数字、落在本子模块号段内、6.6 权威表与正文语义一致
 7 数据结构：表名前缀属于本子模块 / 表清单与合计一致 / SQLAlchemy 与 Pydantic 章节 / 附录 A~F
 8 禁止表：不得自建上游业务表与身份凭据表（铁律 2 与 6）
 9 审批单号格式：SP + yyyyMMdd + 4 位
10 事件名：m20.approval.completed 不得改名，不得出现错误拼写
11 事件载荷：第 10 章不得出现患者姓名 / 手机号 / 身份证明文字段名
12 质量标记：内部契约响应示例必须带四个质量标记
13 只增不删表：无 is_deleted 且有 REVOKE DELETE
14 缓存 TTL：Redis 表中 TTL 不得大于 3600s（推送令牌除外）
15 分区表：PARTITION BY RANGE 必须带 DEFAULT 分区
16 重复章节：同名 ## / ### 不得出现两次
17 粘连标题：一行内挤了两个标题
18 目录一致：章节目录里的附录名称与正文实际标题一致
19 模块级文档独立检查：共享规范 / 总纲 / 数据结构汇总的关键断言
"""
import ast
import io
import json
import os
import re
import sys

FENCE = chr(96) * 3

# ---------------------------------------------------------------- 常量

BAD_SQL = ("AUTO_INCREMENT", "TINYINT", "DATETIME", "ENGINE=", "VARCHAR2",
           "MEDIUMINT", "LONGTEXT", "MEDIUMTEXT")
# 这些词只在一个文件的正文里出现即为脏；坑表要用描述而不是字面
PLACEHOLDERS = ("TODO", "待补充", "XXX 表", "略。", "待完善", "FIXME", "占位")
# 日期时间类型名对 Python 同名类（datetime / Mapped[datetime]）做大小写敏感匹配，
# 否则任何 SQLAlchemy 2.0 模型都会被误判成 MySQL 语法。
CASE_SENSITIVE_BAD_SQL = ("DATETIME",)

GARBLED = ("\ufffd", "\\u00", "\\\\u4e")

# 子模块编号 -> 允许的表前缀
SUBSYS_PREFIX = {
    "01": ["m20_base_"],
    "02": ["m20_doc_"],
    "03": ["m20_nur_"],
    "04": ["m20_apr_"],
    "05": ["m20_qry_"],
    "06": ["m20_sal_"],
    "07": ["m20_fol_"],
    "08": ["m20_msg_"],
}

# 铁律 2 / 6：禁止自建的表（命中 CREATE TABLE 即报错）
FORBIDDEN_TABLES = (
    # 业务数据副本
    "m20_patient", "m20_order", "m20_order_item", "m20_diagnosis",
    "m20_prescription", "m20_prescription_item", "m20_bill", "m20_invoice",
    "m20_report", "m20_emr_record", "m20_admission", "m20_bed",
    "m20_nursing_record", "m20_followup_plan", "m20_drug",
    "m20_metric", "m20_dashboard", "m20_lab_result", "m20_exam_report",
    # 身份凭据副本（铁律 6）
    "m20_token", "m20_session", "m20_device", "m20_user", "m20_role",
    "m20_staff", "m20_credential", "m20_mfa",
)

# 只增不删表：不得有 is_deleted 字段，且必须 REVOKE DELETE
APPEND_ONLY_TABLES = (
    "m20_apr_instance", "m20_apr_node", "m20_apr_action_log",
    "m20_msg_delivery_log", "m20_qry_search_log",
    "m20_qry_sensitive_access",
)

# M20 提供给外部的内部契约（路径一字不差）
P_CONTRACTS = {
    "P-01": "/internal/v1/m20/approval/apply",
    "P-02": "/internal/v1/m20/approval/{",
    "P-03": "/internal/v1/m20/message/unread-count",
    "P-04": "/internal/v1/m20/message/push",
    "P-05": "/internal/v1/m20/todo/list/",
    "P-06": "/internal/v1/m20/device/online",
    "P-07": "/internal/v1/m20/approval/",
}

# 每个 P 契约的实现子模块（编号 -> 子模块号）
P_CONTRACT_OWNER = {
    "P-01": "04",
    "P-02": "04",
    "P-03": "08",
    "P-04": "08",
    "P-05": "08",
    "P-06": "01",
    "P-07": "04",
}

# 上游写死的事件名，不得改名
REQUIRED_EVENT = "m20.approval.completed"
BAD_EVENT_NAMES = ("m20.record.finalized", "m20.approval.complete",
                   "m20.approval.finished", "m20.approval.approved_event")

# 第 10 章不得出现的敏感字段名（事件载荷红线）
SENSITIVE_FIELDS = ("patient_name", "real_name", "id_card", "id_card_no",
                    "phone", "mobile", "mobile_no", "phone_no", "address")

# V1.7：敏感字段只在两个位置才算违规——
#   ① 作为 JSON 键出现：  "mobile": "138..."
#   ② 作为赋值左值或字段表左值出现： mobile = ... | mobile | VARCHAR(20) |
# 裸子串匹配会把事件命名空间 m20.mobile.device_online 判成手机号字段，
# 逼成员去改掉真实存在的事件名——那是让检查去修改事实。
SENSITIVE_PATS = tuple(
    (r'"%s"\s*:' % f,
     r"(?<![A-Za-z0-9_.])%s\s*=(?!=)" % f,
     r"\|\s*%s\s*\|" % f)
    for f in SENSITIVE_FIELDS)

# 质量标记四件套
QUALITY_MARKS = ("degraded", "degraded_sources", "data_quality", "as_of")

# 错误码号段（子模块编号 -> (下界, 上界)，闭区间）
ERR_BANDS = {
    "01": (2001001, 2001999),
    "02": (2002001, 2002999),
    "03": (2003001, 2003999),
    "04": (2004001, 2004999),
    "05": (2005001, 2005999),
    "06": (2006001, 2006999),
    "07": (2007001, 2007999),
    "08": (2008001, 2008999),
}
COMMON_ERR = ("209001",)

CHAPTERS = ["1. 模块概述", "2. 业务范围与边界", "3. 业务模型",
            "4. 数据结构设计", "5. 页面设计", "6. 后端接口设计",
            "7. 缓存与异步任务设计", "8. 业务规则与校验",
            "9. 权限与安全", "10. 集成与契约", "11. 异常处理与日志",
            "12. 验收标准"]
APPENDIX = "ABCDEF"


class Reporter(object):
    def __init__(self):
        self.errors = []
        self.warns = []

    def err(self, path, msg):
        self.errors.append("%s: %s" % (path, msg))

    def warn(self, path, msg):
        self.warns.append("%s: %s" % (path, msg))


# ---------------------------------------------------------------- 工具

def strip_code_fences(text):
    """把围栏代码块内容替换为空行，保留行号对齐。"""
    out = []
    inside = False
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith(FENCE):
            inside = not inside
            out.append("")
            continue
        out.append("" if inside else ln)
    return out


def count_cols(s):
    s = s.strip()
    s = s.replace("\\|", "")
    return len(re.split(r"(?<!\\)\|", s))


def is_sep_row(s):
    s = s.strip()
    if not s.startswith("|"):
        return False
    body = s.strip("|")
    if not body:
        return False
    for cell in body.split("|"):
        c = cell.strip()
        if not c:
            continue
        if not re.match(r"^:?-{2,}:?$", c):
            return False
    return True


def iter_tables(lines):
    """按连续 | 行分组，产出 (起始行号, 行列表)。"""
    grp = []
    for i, ln in enumerate(lines):
        if ln.strip().startswith("|"):
            grp.append((i + 1, ln))
        else:
            if grp:
                yield grp
            grp = []
    if grp:
        yield grp


def find_chapter(text, num, stop_pattern):
    """取 '## num.' 到下一个匹配 stop 的内容。"""
    m = re.search(r"(?ms)^##\s+%d\..*?(?=%s|\Z)" % (num, stop_pattern), text)
    return m.group(0) if m else None


# ---------------------------------------------------------------- 1 通用格式

def check_common(path, t, rep):
    lines = t.split("\n")
    # 围栏配对
    fences = [i + 1 for i, l in enumerate(lines) if l.strip().startswith(FENCE)]
    if len(fences) % 2:
        rep.err(path, "代码围栏不配对：共 %d 个，最后一个在 %d 行"
                % (len(fences), fences[-1] if fences else -1))

    # python / json 围栏可解析
    for m in re.finditer(r"(?ms)^%s\s*(?:python|py)\s*\n(.*?)^%s\s*$"
                         % (re.escape(FENCE), re.escape(FENCE)), t):
        code = m.group(1)
        start = t[:m.start()].count("\n") + 1
        try:
            ast.parse(code)
        except SyntaxError as e:
            rep.err(path, "python 围栏无法 ast.parse（起始第 %d 行）：%s"
                    % (start, e))
    for m in re.finditer(r"(?ms)^%s\s*json\s*\n(.*?)^%s\s*$"
                         % (re.escape(FENCE), re.escape(FENCE)), t):
        code = re.sub(r"(?m)^\s*//.*$", "", m.group(1))
        start = t[:m.start()].count("\n") + 1
        try:
            json.loads(code)
        except Exception as e:
            rep.err(path, "json 围栏无法解析（起始第 %d 行）：%s" % (start, e))

    # 表格列数一致（跳过代码块内）
    body = strip_code_fences(t)
    for grp in iter_tables(body):
        cols = [count_cols(x[1]) for x in grp if not is_sep_row(x[1])]
        if len(set(cols)) > 1:
            rep.err(path, "第 %d 行起的表格列数不一致：%s"
                    % (grp[0][0], sorted(set(cols))))

    # 乱码
    for g in GARBLED:
        if g in t:
            i = t.find(g)
            rep.err(path, "疑似乱码/未转义字符 %r 出现在第 %d 行"
                    % (g, t[:i].count("\n") + 1))

    # 禁用词
    #
    # V1.4：拉丁字母类禁用词（TODO / FIXME / XXX 表）改为标识符边界匹配。
    # 原实现用裸子串匹配，把 TO_DO_COUNT 之外的 "TODO_COUNT"、"TODOIST" 这类
    # 完全正常的业务枚举也判成占位词。中文词仍用子串匹配——中文没有词边界。
    for w in PLACEHOLDERS:
        if re.match(r"[A-Za-z]", w):
            pat = r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])"
        else:
            pat = re.escape(w)
        for m in re.finditer(pat, t):
            rep.err(path, "第 %d 行出现禁用词 %r"
                    % (t[:m.start()].count("\n") + 1, w))

    # MySQL 残留
    for bad in BAD_SQL:
        flags = 0 if bad in CASE_SENSITIVE_BAD_SQL else re.I
        for m in re.finditer(re.escape(bad), t, flags):
            rep.err(path, "第 %d 行出现 MySQL 专有语法 %r"
                    % (t[:m.start()].count("\n") + 1, bad))


# ---------------------------------------------------------------- 2 详细设计骨架

def check_design(path, t, rep):
    heads = {}
    for ln in strip_code_fences(t):
        m = re.match(r"^##\s+(.+?)\s*$", ln)
        if m:
            heads.setdefault(m.group(1), []).append(1)
    for ch in CHAPTERS:
        if ch not in heads:
            rep.err(path, "缺少第 %s 章" % ch)
    for a in APPENDIX:
        pat = re.compile(r"^附录\s*%s\s*[：:]" % a)
        if not any(pat.match(h) for h in heads):
            rep.err(path, "缺少附录 %s" % a)

    # 第 4 章不得有表定义
    m = re.search(r"(?ms)^##\s+4\..*?(?=^##\s+5\.|\Z)", t)
    if m:
        ch4 = m.group(0)
        # 剔除四反引号示例块后再扫
        ch4 = re.sub(r"(?ms)^%s{4}.*?%s{4}" % (FENCE, FENCE), "", ch4)
        if re.search(r"(?i)CREATE\s+TABLE", ch4):
            rep.err(path, "第 4 章出现了表定义（应只放指引块）")


# ---------------------------------------------------------------- 3 页面双向

def check_pages(path, t, rep):
    m = re.search(r"(?ms)^###\s+5\.1\s.*?(?=^###\s+5\.2\b)", t)
    if not m:
        rep.err(path, "未找到 5.1 页面总览")
        return
    overview = set(re.findall(r"\b(P\d{2})\b", m.group(0)))
    # 逐页标题：### 5.x P0x
    detailed = set(re.findall(r"(?m)^###\s+5\.\d+\s+(P\d{2})\b", t))
    if not overview:
        rep.err(path, "5.1 页面总览里没有识别到 P0x 编号")
    if not detailed:
        rep.err(path, "第 5 章没有找到 '### 5.x P0x' 形式的逐页标题")
    miss = sorted(overview - detailed)
    extra = sorted(detailed - overview)
    if miss:
        rep.err(path, "页面总览有、逐页缺：%s" % ", ".join(miss))
    if extra:
        rep.err(path, "逐页有、总览缺：%s" % ", ".join(extra))
    # 编号连续 P01..Pnn
    if overview:
        nums = sorted(int(x[1:]) for x in overview)
        if nums != list(range(1, len(nums) + 1)):
            rep.err(path, "页面编号不连续：%s" % nums)


# ---------------------------------------------------------------- 4 接口

def check_api(path, t, rep):
    m = re.search(r"(?ms)^###\s+6\.1\s.*?(?=^###\s+6\.2\b)", t)
    if not m:
        rep.err(path, "未找到 6.1 接口总览")
        overview = []
    else:
        overview = [int(x) for x in re.findall(r"\bAPI-(\d{2,3})\b", m.group(0))]
        overview = sorted(set(overview))
        if overview and overview != list(range(1, len(overview) + 1)):
            miss = sorted(set(range(1, max(overview) + 1)) - set(overview))
            rep.err(path, "6.1 接口编号不连续，缺：%s" % miss)
    detailed = sorted(set(int(x) for x in
                          re.findall(r"(?m)^####\s+API-(\d{2,3})\b", t)))
    if overview:
        miss = sorted(set(overview) - set(detailed))
        extra = sorted(set(detailed) - set(overview))
        if miss:
            rep.err(path, "接口详述缺失：%s" % miss)
        if extra:
            rep.err(path, "多出未登记的接口详述：%s" % extra)
    return len(overview)


# ---------------------------------------------------------------- 5 验收四类

LIMITS = {"AC": 35, "PF": 8, "DA": 5, "SC": 4}


def check_acceptance(path, t, rep):
    m = re.search(r"(?ms)^##\s+12\..*?(?=^##\s+附录|\Z)", t)
    if not m:
        rep.err(path, "未找到第 12 章验收标准")
        return
    ch = m.group(0)
    for kind, low in LIMITS.items():
        nums = sorted(set(int(x) for x in
                          re.findall(r"\b%s-(\d{2})\b" % kind, ch)))
        if not nums:
            rep.err(path, "第 12 章没有 %s 类验收条目" % kind)
            continue
        if nums != list(range(1, len(nums) + 1)):
            rep.err(path, "%s 类编号不连续：%s" % (kind, nums))
        if len(nums) < low:
            rep.err(path, "%s 类只有 %d 条，要求 >= %d" % (kind, len(nums), low))


# ---------------------------------------------------------------- 6 错误码

def check_errcodes(path, t, rep, subsys):
    lo, hi = ERR_BANDS[subsys]
    codes = set(re.findall(r'"(\d{7})"', t))
    for c in sorted(codes):
        if c in COMMON_ERR:
            continue
        v = int(c)
        if not (lo <= v <= hi):
            rep.err(path, "错误码 %s 越出本子模块号段 %d~%d" % (c, lo, hi))
    # 也不允许出现别的子模块号段（除公共）
    for c in codes:
        if c in COMMON_ERR:
            continue
        for k, (l2, h2) in ERR_BANDS.items():
            if k != subsys and l2 <= int(c) <= h2:
                rep.err(path, "错误码 %s 属于 M20-%s 号段，不得在本子模块使用"
                        % (c, k))

    # 6.6 权威表与正文语义比对
    m = re.search(r"(?ms)^###\s+6\.6\s.*?(?=^###\s+6\.7\s|^##\s+7\.|^##\s+附录|\Z)", t)
    if not m:
        rep.warn(path, "未找到 6.6 错误码定义表（若第 6 章尚未写完，此为正常中间态）")
        return
    _6_6 = m.start()
    _6_6_end = m.start() + len(m.group(0))
    auth = {}
    for ln in m.group(0).split("\n"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 3 and re.match(r'^"?\d{7}"?$', cells[0]):
            code = cells[0].strip('"')
            meaning = cells[2]
            auth[code] = meaning
    if not auth:
        rep.err(path, "6.6 错误码定义表为空或格式不符（首列应是 7 位错误码）")
        return
    for code, meaning in auth.items():
        # 正文其它地方：| "20Nxxx" | 含义 |
        for mm in re.finditer(r'^\|\s*"?' + code + r'"?\s*\|([^|]*)\|',
                              t, re.M):
            other = mm.group(1).strip()
            if other.startswith("HTTP") or other.startswith("`"):
                continue
            # V1.5：跳过 6.6 权威表自身的行。原实现把权威表第二列（HTTP 状态码）
            # 当成「正文含义」去和第三列（含义）比重合度，于是每一条错误码都报
            # 一次语义不一致；而表头是 `| 错误码 | HTTP | 含义 |`，第二列本来就
            # 是状态码不是含义。判据：该行落在 6.6 小节区间内即跳过。
            if _6_6 <= mm.start() < _6_6_end:
                continue
            if re.match(r"^\d{3}$", other):
                continue
            if not other:
                continue
            # 二元组重合度
            a = set(meaning)
            b = set(other)
            if not a or not b:
                continue
            ov = len(a & b) / float(len(a | b))
            if ov < 0.30:
                ln = t[:mm.start()].count("\n") + 1
                rep.warn(path, "错误码 %s 语义可能不一致（第 %d 行）：权威表「%s」vs 正文「%s」"
                         % (code, ln, meaning[:20], other[:20]))


# ---------------------------------------------------------------- 7 数据结构

def check_struct(path, t, rep, subsys):
    prefixes = SUBSYS_PREFIX[subsys]
    tables = re.findall(r"(?m)^###\s+4\.\d+\s+表[：:]\s*`([a-z0-9_]+)`", t)
    if not tables:
        rep.err(path, "没有找到 '### 4.x 表：`m20_xxx`' 形式的表定义标题")
        return
    # 前缀
    for tb in tables:
        if not any(tb.startswith(p) for p in prefixes):
            rep.err(path, "表 %s 的前缀不属于本子模块（应属于 %s）"
                    % (tb, " / ".join(prefixes)))
    # 声明一致
    m1 = re.search(r"\*\*合计[：:]\s*(\d+)\s*张表\*\*", t)
    m2 = re.search(r"\*\*表数量[：:]\*\*\s*(\d+)\s*张", t)
    if m1:
        n = int(m1.group(1))
        if n != len(tables):
            rep.err(path, "合计声明 %d 张，实际 %d 张表定义" % (n, len(tables)))
    elif m2:
        n = int(m2.group(1))
        if n != len(tables):
            rep.err(path, "表数量声明 %d 张，实际 %d 张表定义" % (n, len(tables)))
    else:
        rep.err(path, "缺少 '**合计：N 张表**' 或 '**表数量：** N 张' 声明")
    # 表清单一致性（第 1 章里列出的表名）
    listed = set(re.findall(r"`(m20_[a-z0-9_]+)`", t))
    defined = set(tables)
    # 只要求定义的表都在清单里出现（清单可能多列跨模块引用表的说明）
    for tb in defined:
        if tb not in listed:
            rep.err(path, "表 %s 未在表清单中出现" % tb)
    # SQLAlchemy / Pydantic 章节
    if not re.search(r"(?m)^###\s+4\.\d+\s+SQLAlchemy", t):
        rep.err(path, "缺少 SQLAlchemy 2.0 模型定义章节")
    if not re.search(r"(?m)^###\s+4\.\d+\s+Pydantic", t):
        rep.err(path, "缺少 Pydantic Schema 定义章节")
    # 附录 A~F
    for a in APPENDIX:
        if not re.search(r"(?m)^##\s+附录\s*%s\s*[：:]" % a, t):
            rep.err(path, "缺少附录 %s" % a)


# ---------------------------------------------------------------- 8 禁止表

def check_forbidden(path, t, rep):
    body = strip_code_fences(t)
    # 剔除以禁止性词开头的行，避免「不得建 m20_order」这种说明被误报
    keep = []
    for ln in body:
        s = ln.strip()
        if re.match(r"^[\-\*\d\.\)]*\s*(❌|禁止|不得|严禁|切勿|不要)", s):
            continue
        keep.append(ln)
    scan = "\n".join(keep)
    # 1) 精确表名
    for tb in FORBIDDEN_TABLES:
        for m in re.finditer(r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
                             r"(?:[a-z_]+\.)?%s\b" % re.escape(tb), scan):
            rep.err(path, "禁止自建表 %s（铁律 2 / 铁律 6）" % tb)
    # 2) 改了前缀的绕法：m20_<子模块>_<禁止对象>
    #    「m20_apr_session」与「m20_session」是同一个错误，只是把子模块前缀拼了进去
    bare = sorted(set(tb[len("m20_"):] for tb in FORBIDDEN_TABLES))
    pat = (r"(?i)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:[a-z_]+\.)?"
           r"m20_(?:base|doc|nur|apr|qry|sal|fol|msg)_(%s)\b"
           % "|".join(re.escape(b) for b in bare))
    for m in re.finditer(pat, scan):
        rep.err(path, "禁止自建表（加了子模块前缀的同义表）m20_*_%s（铁律 2 / 铁律 6）"
                % m.group(1))


# ---------------------------------------------------------------- 9 单号格式

def check_codes(path, t, rep):
    # V1.5：原实现是两条互相矛盾的正则——
    #   ① r"\bSP(\d{8})(\d+)\b" 要求 SP 后 12 位数字（8 日期 + 4 流水）；
    #   ② r"\bSP(\d{4,7}|\d{9,})\b" 把「SP 后 9 位及以上」判成日期段不对，
    #      而合法的 SP 单号正好是 SP 后 12 位 → 必然被 ② 吃掉。
    #   于是任何合法单号两头堵死（M20-06 报出，实测 SP202611070001 必被误判）。
    # 改为一条：按 SP 后总位数判定，11 位 = 7 日期 + 4 流水同理不符。
    for m in re.finditer(r"\bSP(\d+)\b", t):
        if len(m.group(1)) != 12:
            rep.err(path, "第 %d 行审批单号 %s 不是 SP + 8 位日期 + 4 位流水（SP 后应为 12 位数字，实际 %d 位）"
                    % (t[:m.start()].count("\n") + 1, m.group(0),
                       len(m.group(1))))


def check_errcode_gaps(path, t, rep, subsys):
    """V1.8 新增：子模块错误码「序列连续性」检查。

    起因（M20-04 报出）：6.6 补写 5 个错误码时顺序插错位置，脚本不报，
    是用一条额外命令人肉查出来的。M18 那轮也踩过同样的空号问题。

    两次改版记录（这是一条「检查器自己难产」的教训，值得留着）：
      第一版：相邻已出现码差 > 1 就报。实测 11 条告警**全是误报**——
        M20 的实际写法是「整段留空给将来」（2001025、2001026 之后直接
        从 2001030 开始新的一组），不是漏写。
      第二版：按十位分组，段内必须连续。实测仍有 10 条误报——
        M20 的分组边界不固定在十位（2001030~2001033、2001034 单列、
        然后 2001040~2001041），十位只是巧合。
      第三版（本版）：**只用无争议的判据**——
        6.6 表的行序必须与码值升序一致。这条在任何分组习惯下都成立：
        漏号、插错位置、复制粘贴时改错一位，都会让行序和码序打架。
        仍留空是合法设计，所以「跳号」本身一律不报，只报「顺序错乱」。

    一句话：**一条会误报的检查比没有检查更糟，因为它逼人把正确的东西改成错的。**
    """
    m = re.search(r"(?ms)^###\s+6\.6\s.*?(?=^###\s+6\.7\s|^##\s+7\.|^##\s+附录|\Z)", t)
    if not m:
        return
    lo, hi = ERR_BANDS.get(subsys, (0, 0))
    seq = []
    for mm in re.finditer(r'(?m)^\|\s*"(\d{7})"\s*\|', m.group(0)):
        v = int(mm.group(1))
        if lo <= v <= hi:
            seq.append(v)
    if len(seq) < 2:
        return
    for a, b in zip(seq, seq[1:]):
        if b <= a:
            rep.err(path, "6.6 错误码行序与码值不升序：%d 之后出现 %d"
                    "（漏号、插错位置、改错一位都会表现为这样）" % (a, b))


# ---------------------------------------------------------------- 10 / 11 事件

def check_events(path, t, rep):
    for bad in BAD_EVENT_NAMES:
        if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(bad) + r"(?![A-Za-z0-9_])", t):
            rep.err(path, "出现错误的事件名 %r（上游写死的是 %s）"
                    % (bad, REQUIRED_EVENT))
    # 若提到审批完成事件语义，则必须是正确名字
    if "审批完成" in t or "审批结果" in t:
        if REQUIRED_EVENT not in t:
            rep.warn(path, "文档提到审批结果但未出现 %s" % REQUIRED_EVENT)


def check_event_payload(path, t, rep):
    m = re.search(r"(?ms)^##\s+10\..*?(?=^##\s+11\.)", t)
    if not m:
        return
    chap = m.group(0)
    # 10.1 事件清单与 10.2 是接口/事件字段契约，允许出现字段名；
    # 只扫 10.3 发布 与 10.4 订阅 两个小节
    payload = ""
    for seg in ("10.3", "10.4"):
        mm = re.search(r"(?ms)^###\s+%s\b.*?(?=^###\s+10\.\d|^##\s+11\.|\Z)"
                       % re.escape(seg), chap)
        if mm:
            payload += mm.group(0)
    if not payload:
        payload = chap
    # V1.8：再剔除「禁止性说明行」——
    #   以 ❌/禁止/不得/严禁/切勿/不许 开头的行，是在写「不许出现什么」，
    #   本身必然包含那个字段名。这类行不是载荷，是约束。
    #   （与 check_boundary 剔除 CREATE TABLE 禁止示例同一个思路）
    kept = []
    for ln in payload.split("\n"):
        s = ln.strip().lstrip(">").strip()
        if s.startswith(("❌", "禁止", "不得", "严禁", "切勿", "不许")):
            continue
        kept.append(ln)
    payload = "\n".join(kept)
    for f, pats in zip(SENSITIVE_FIELDS, SENSITIVE_PATS):
        for pat in pats:
            if re.search(pat, payload):
                rep.err(path, "第 10 章发布/订阅小节出现敏感字段名 %r"
                              "（事件载荷红线）" % f)
                break


# ---------------------------------------------------------------- 12 质量标记

def check_quality(path, t, rep, subsys):
    # 有内部契约（P-xx）的子模块，响应示例必须含四标记
    #
    # V1.5：原实现用 "全文出现 P-0x" 判断本文件是否提供内部契约，误报了两类：
    #   ① 只调用上游 P 契约的子模块（如 M20-07 引 M19 的 P-01/P-11）——
    #      它不提供任何 M20 P 契约，却被要求四标记齐全；
    #   ② 只是在散文里提到「P-01 归 M20-04」这种引用。
    # 改为按归属判：只有本文件真正实现某个 P 契约时才检查。
    owned = [pid for pid, pth in P_CONTRACTS.items()
             if P_CONTRACT_OWNER.get(pid) == subsys
             or ("(m20-%s" % subsys) in pth]
    if owned:
        need = True
    else:
        need = bool(re.search(r"\bP-0\d\b", t))
        if need and not re.search(r"内部契约|本子模块提供", t):
            need = False
    if not need:
        return
    miss = [q for q in QUALITY_MARKS if q not in t]
    if miss:
        rep.err(path, "内部契约响应示例缺少质量标记：%s" % ", ".join(miss))


# ---------------------------------------------------------------- 13 只增不删表

def check_append_only(path, t, rep):
    for tb in APPEND_ONLY_TABLES:
        m = re.search(r"(?ms)^###\s+4\.\d+\s+表[：:]\s*`" + re.escape(tb)
                      + r"`.*?(?=^###\s+4\.\d+|^##\s+附录|\Z)", t)
        if not m:
            continue
        seg = m.group(0)
        # V1.8：说明「本表没有逻辑删除列」的叙述行不算违规——
        # 用几何位置（行）判断，不用"看起来像不像字段定义"判断。
        seg_lines = [ln for ln in seg.split("\n")
                     if not re.search(r"没有|不含|不得|禁止|不设|无\s*`?is_deleted",
                                      ln)]
        if any(re.search(r"(?<![A-Za-z0-9_])is_deleted(?![A-Za-z0-9_])", ln)
               for ln in seg_lines):
            rep.err(path, "只增不删表 %s 不得有 is_deleted 字段" % tb)
        # V1.8：REVOKE UPDATE, DELETE ON x FROM r 不含连续的 "REVOKE DELETE"
        # 子串，但它确实收回了 DELETE 权限。别逼成员多写一行只为被匹配。
        if not re.search(r"REVOKE\s+(?:UPDATE\s*,\s*)?DELETE\b",
                         seg, re.I):
            rep.err(path, "只增不删表 %s 必须 REVOKE DELETE" % tb)


# ---------------------------------------------------------------- 14 缓存 TTL

def check_ttl(path, t, rep):
    for grp in iter_tables(strip_code_fences(t)):
        for lineno, ln in grp:
            if "m20:" not in ln:
                continue
            m = re.search(r"(\d+)\s*s\b", ln)
            if not m:
                continue
            v = int(m.group(1))
            if v > 3600:
                # 推送令牌允许持久
                if "token" in ln.lower() and "msg" in ln.lower():
                    continue
                rep.err(path, "第 %d 行 Redis Key 的 TTL %ds 超过 3600s 上限"
                        % (lineno, v))


# ---------------------------------------------------------------- 15 分区表

def check_partition(path, t, rep):
    """分区表必须带 DEFAULT 分区。

    V1.9 修正（M20-08 / M20-06 先后报出）。这一条检查连改三次才对，
    过程本身是这个项目最值得留档的案例之一：

      第一版：只看 `CREATE TABLE ... PARTITION BY RANGE (...);` 这一条
        语句里有没有 DEFAULT。**对任何正确写法都必然报错**——DEFAULT
        分区在语法上必然是另一条语句（`CREATE TABLE xxx_default
        PARTITION OF xxx DEFAULT;`）。与上一轮 `SP` 双正则死结同型。

      第二版：从 `PARTITION BY RANGE (key)` 取表名，再找
        `PARTITION OF <表名> DEFAULT`。仍有误报，因为正则从一张普通表
        的开头一路吃到后面某张分区表的 `PARTITION BY`，把两段 DDL 当成
        一个块（M20-08 的 `m20_msg_template` 被误指）。

      第三版（本版）：加两层前置判定，让误判**自己消失**而不是靠改文档迁就：
        ① 表名附近的 PRIMARY KEY / UNIQUE 子句里必须出现分区键
           （PostgreSQL 强制要求唯一约束包含分区键，不含则不可能是分区表）；
        ② 同一个 `CREATE TABLE` 块内（按 `;` 切分）必须真的含 `PARTITION BY`。
    重构后给两个文件各自的 DEFAULT 分区都认出来了，误报清零。
    """
    stmts = t.split(";")
    for i, raw in enumerate(stmts):
        if not re.search(r"(?is)CREATE\s+TABLE", raw):
            continue
        if not re.search(r"(?i)PARTITION\s+BY\s+RANGE", raw):
            continue
        mt = re.search(r"(?is)CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-z0-9_]+)", raw)
        if not mt:
            continue
        tbl = mt.group(1)
        mk = re.search(r"(?i)PARTITION\s+BY\s+RANGE\s*\(\s*([a-z0-9_]+)\s*\)", raw)
        key = mk.group(1) if mk else ""
        # ① 唯一约束必须含分区键
        uniques = re.findall(
            r"(?is)(?:PRIMARY\s+KEY|UNIQUE)\s*(?:\(|USING[^(]*\()([^)]*)\)", raw)
        if not uniques or not any(key and key in u for u in uniques):
            continue
        # ② 必须存在 DEFAULT 分区
        pat = (r"(?i)CREATE\s+TABLE\s+[a-z0-9_]+\s+PARTITION\s+OF\s+"
               + re.escape(tbl) + r"\s+DEFAULT")
        if not re.search(pat, t):
            rep.err(path, "分区表 %s 缺少 DEFAULT 分区（新月份 INSERT 会直接失败）" % tbl)


# ---------------------------------------------------------------- 16 重号章节

def check_dup_sections(path, t, rep):
    body = "\n".join(strip_code_fences(t))
    body = re.sub(r"(?ms)^%s{4}.*?%s{4}" % (FENCE, FENCE), "", body)
    seen = {}
    for m in re.finditer(r"(?m)^(#{2,3})\s+(.+?)\s*$", body):
        key = (m.group(1), m.group(2))
        seen.setdefault(key, []).append(body[:m.start()].count("\n") + 1)
    for k, v in seen.items():
        if len(v) > 1:
            rep.err(path, "章节标题重复：%s %s（行 %s）" % (k[0], k[1], v))


# ---------------------------------------------------------------- 17 粘连标题

def check_glued_headings(path, t, rep):
    for i, ln in enumerate(strip_code_fences(t)):
        if not ln.startswith("#"):
            continue
        rest = ln.lstrip("#").strip()
        if re.search(r"(?<![%s#])#{1,6}\s*[0-9\u4e00-\u9fa5A-Za-z]" % FENCE, rest):
            rep.err(path, "第 %d 行粘连了两个标题：%s" % (i + 1, ln[:60]))


# ---------------------------------------------------------------- 18 目录一致

def key(s):
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[：:、，,。\.\(\)（）\-—_]", "", s)
    return s


def check_fence_shadow(path, t, rep):
    """检测「章节标题被围在代码块里」与「小节结束时围栏仍未闭合」。

    为什么需要这一项：V1.10 之前围栏只做「开栏数 == 闭栏数」的字面计数，这个
    判据挡不住一种情况——某几节漏了闭栏、后面某处又多了一个开栏，全文计数依然
    相等、状态机终态也回到「正文」，但那几节的字段表全被渲染成代码块。M20-04
    的数据结构文件出现过 8 个小节连续漏闭栏，阅读上完全看不出来（渲染正常），
    只有逐行跟踪围栏状态才发现。

    两个判据：
      1) 代码块内出现 Markdown 标题行（python/sql 注释里的行首井号不算）；
      2) 出现「长代码块里夹着疑似章节标题」的行（非 python/sql 围栏内的 `# xxx`）。
    """
    lines = t.splitlines()
    fence = None
    ftype = ""
    for i, ln in enumerate(lines, 1):
        s = ln.lstrip()
        if fence is not None:
            if s.startswith(fence) and s[len(fence):].strip() == "":
                fence = None
                ftype = ""
                continue
            # 四反引号围栏里嵌的是「文档模板」，模板本身就有标题层级，是合法的
            if fence == "```":
                continue
            if re.match(r"#{2,3} ", s):
                rep.err(path, "第 %d 行：Markdown 标题被围在代码块里（开栏类型 %r）：%s"
                        % (i, ftype, s[:60]))
            elif ftype not in ("python", "py", "sql") and re.match(
                    r"# +[^(#]", s) and ("：" in s or ":" in s or len(s) > 12):
                rep.err(path, "第 %d 行：疑似标题被围在代码块里（开栏类型 %r）：%s"
                        % (i, ftype, s[:60]))
        else:
            if s.startswith("```") or s.startswith("~~~"):
                fence = s[:3]
                ftype = s.strip()[3:].strip().lower()
    if fence is not None:
        rep.err(path, "文件末尾围栏未闭合（类型 %r）" % (ftype,))


def check_toc(path, t, rep):
    m = re.search(r"(?m)^##\s*(目录|章节目录|章节索引|章节索引表)\s*$", t)
    if not m:
        return
    start = m.end()
    nxt = re.search(r"(?m)^##\s+", t[start:])
    toc = t[start:start + nxt.start()] if nxt else t[start:]
    declared = set()
    for mm in re.finditer(r"附录\s*([A-F])\s*[：:、\s]\s*([^\n|]+?)\s*(?:\||$)",
                          toc):
        declared.add((mm.group(1), key(mm.group(2))))
    for mm in re.finditer(r"(?m)^\|\s*附录\s*([A-F])\s*\|\s*([^|]+?)\s*\|", toc):
        declared.add((mm.group(1), key(mm.group(2))))
    if not declared:
        return
    actual = {}
    for mm in re.finditer(r"(?m)^##\s+附录\s*([A-F])\s*[：:]\s*(.+?)\s*$", t):
        actual[mm.group(1)] = key(mm.group(2))
    for letter, name in declared:
        if letter not in actual:
            continue
        a = actual[letter]
        if a == name or a.startswith(name) or name.startswith(a):
            continue
        rep.err(path, "目录里的附录 %s 名称「%s」与正文「%s」不一致"
                % (letter, name[:30], actual[letter][:30]))


# ---------------------------------------------------------------- 19 模块级

def check_module_docs(path, t, rep):
    base = os.path.basename(path)
    if base.startswith("00_"):
        # 共享规范：八子模块 / 六条铁律 / P-01~P-06 / 错误码号段
        for i in range(1, 9):
            if "M20-0%d" % i not in t:
                rep.err(path, "共享规范缺少子模块 M20-0%d" % i)
        for p in P_CONTRACTS:
            if p not in t:
                rep.err(path, "共享规范缺少内部契约 %s" % p)
        if REQUIRED_EVENT not in t:
            rep.err(path, "共享规范缺少上游写死事件名 %s" % REQUIRED_EVENT)
        for code in ("209001",):
            if code not in t:
                rep.err(path, "共享规范缺少公共错误码 %s" % code)
    if base.startswith("M20_移动办公_详细设计"):
        for i in range(1, 9):
            if "M20-0%d" % i not in t:
                rep.err(path, "总纲缺少子模块 M20-0%d" % i)
        if "M18-CALC" in t:
            rep.err(path, "总纲误抄了 M18 的计算模型编号")
    if base.startswith("M20_移动办公_数据结构设计汇总"):
        if not re.search(r"\*\*合计[：:]", t):
            rep.warn(path, "汇总文档未见合计声明")


# ---------------------------------------------------------------- 主流程

def classify(path):
    base = os.path.basename(path)
    m = re.match(r"M20_移动办公_(\d{2})_", base)
    if m and not base.startswith("M20_移动办公_"):
        pass
    if not m:
        m = re.match(r"M20_移动办公_(\d{2})_", base)
    if m:
        return "sub", m.group(1)
    if base.startswith("M20_移动办公_详细设计"):
        return "design", None
    if base.startswith("M20_移动办公_数据结构设计汇总"):
        return "structall", None
    if base.startswith("00_"):
        return "spec", None
    return "other", None


def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_m20.py <目录>")
        return 2
    root = sys.argv[1]
    if not os.path.isdir(root):
        print("目录不存在: %s" % root)
        return 2

    files = sorted(f for f in os.listdir(root) if f.endswith(".md"))
    rep = Reporter()
    n_design = n_struct = n_mod = 0
    for f in files:
        p = os.path.join(root, f)
        with io.open(p, encoding="utf-8") as fh:
            t = fh.read()
        kind, subsys = classify(p)
        if kind == "sub":
            if "_详细设计" in f:
                n_design += 1
                check_common(p, t, rep)
                check_design(p, t, rep)
                check_pages(p, t, rep)
                check_api(p, t, rep)
                check_acceptance(p, t, rep)
                check_errcodes(p, t, rep, subsys)
                check_errcode_gaps(p, t, rep, subsys)
                check_codes(p, t, rep)
                check_events(p, t, rep)
                check_event_payload(p, t, rep)
                check_quality(p, t, rep, subsys)
            else:
                n_struct += 1
                check_common(p, t, rep)
                check_struct(p, t, rep, subsys)
                check_forbidden(p, t, rep)
                check_ttl(p, t, rep)
                check_partition(p, t, rep)
                check_append_only(p, t, rep)
            check_dup_sections(p, t, rep)
            check_glued_headings(p, t, rep)
            check_fence_shadow(p, t, rep)
            check_toc(p, t, rep)
        else:
            n_mod += 1
            check_common(p, t, rep)
            check_dup_sections(p, t, rep)
            check_glued_headings(p, t, rep)
            check_fence_shadow(p, t, rep)
            check_toc(p, t, rep)
            check_forbidden(p, t, rep)
            check_events(p, t, rep)
            check_module_docs(p, t, rep)

    print("详细设计 %d 个 / 数据结构 %d 个 / 模块级 %d 个，共 %d 个文件"
          % (n_design, n_struct, n_mod, len(files)))
    for w in rep.warns:
        print("  告警: %s" % w)
    if rep.errors:
        print("")
        for e in rep.errors:
            print("  错误: %s" % e)
        print("")
        print("✗ 校验失败：%d 个错误，%d 个告警" % (len(rep.errors), len(rep.warns)))
        return 1
    print("")
    print("✓ 全部通过（%d 个文件）" % len(files))
    if rep.warns:
        print("  （%d 个告警）" % len(rep.warns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
