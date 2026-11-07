#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M18 电子病历与知识库 — 文档校验脚本

用法：
    python3 M18电子病历与知识库/validate_m18.py M18电子病历与知识库

校验项（共 19 项）：
 1. 通用格式：代码围栏配对、python 块 ast.parse、json 块 json.loads、
    表格列数一致、乱码字符、占位词残留、MySQL/Oracle 语法残留
 2. 详细设计：第 1~12 章齐全 + 附录 A~F；第 4 章只有指引块（不得出现表定义标题）
 3. 页面：总览树与第 5 章 ### 5.x PNN 标题双向一致，数量一致
 4. 接口：API-01 起连续无断号；每一项都有 #### API-xx 详述
 5. 验收：AC >= 35、PF >= 8、DA >= 5、SC >= 4，四类各自从 01 连续
 6. 错误码：7 位数字字符串；必须落在 1801001~1808999 或 189001 内
 7. 数据结构：表名必须以 m18_ 前缀（按子模块分配）；表清单与 ### 4.x 表： 数量一致；
    SQLAlchemy 与 Pydantic 章节存在；附录 F 版本历史表存在
 8. 边界：禁止出现 M07/M05/M06/M09/M08/M01 各自拥有的表的重复定义
 9. 病历事实表：m18_emr_record / m18_emr_amendment / m18_emr_seal 不得有 is_deleted，
    且必须有 REVOKE DELETE
10. 病历签署后不可改：m18_emr_record 必须有触发器或 REVOKE UPDATE 落地说明
11. content_hash：必须 VARCHAR(64)；不得出现 MD5
12. 内部契约 P-xx：路径必须与共享规范 §8 一字不差
13. 事件名：emr.record.finalized / m18.record.locked / m18.archive.confirmed 三个
    上游写死的事件名不得被改名（不得出现 m18.record.finalized）
14. 事件载荷安全：事件章节不得出现病历正文字段名
15. 金额 / 比率精度：金额 NUMERIC(14,2)、比率 NUMERIC(10,6)；禁 FLOAT/DOUBLE/REAL 用于金额
16. 同意书签署状态：不得出现 m18_ 前缀的签署状态表
17. 错误码语义一致：6.6 权威表 vs 全文引用
18. 分区表：PARTITION BY RANGE 必须带 DEFAULT 分区
19. 重复章节：同名 ### 标题不得出现两次（剔除四反引号代码块后判定）
"""

import ast
import json
import os
import re
import sys

FENCE = chr(96) * 3
BAD_SQL = (
    "AUTO_INCREMENT",
    "TINYINT",
    "DATETIME",
    "ENGINE=",
    "VARCHAR2",
    "MEDIUMINT",
    "LONGTEXT",
    "MEDIUMTEXT",
)
# 只按原样大小写匹配的项（V1.1 修正）。
# 理由：Python 的 datetime 类名、from datetime import datetime、Mapped[datetime]
# 在任何 SQLAlchemy 2.0 模型里都必然出现。若对 DATETIME 也做大小写不敏感匹配，
# 这些全部会被判成 MySQL 的 DATETIME 类型，等于本规范下没人能写出合规的 ORM 章节。
# MySQL 的 DATETIME 类型名在 DDL 里按约定一律大写，所以只认大写即可准确命中。
CASE_SENSITIVE_BAD_SQL = ("DATETIME",)
PLACEHOLDERS = ("TODO", "待补充", "XXX 表", "略。", "待完善", "FIXME", "占位")

SUBSYS_PREFIX = {
    "01": ["m18_tpl_"],
    "02": ["m18_opd_", "m18_emr_"],
    "03": ["m18_ipd_"],
    "04": ["m18_opr_"],
    "05": ["m18_qc_"],
    "06": ["m18_arc_", "m18_emr_"],
    "07": ["m18_idx_"],
    "08": ["m18_kb_"],
}

# 铁律 2：这些表归别的模块，M18 不得重复定义
FORBIDDEN_TABLES = (
    "m18_order",
    "m18_order_item",
    "m18_diagnosis",
    "m18_prescription",
    "m18_prescription_item",
    "m18_document",
    "m18_document_signature",
    "m18_consent_sign",
    "m18_home_page",
    "m18_surgery_record",
    "m18_nursing_record",
    "m18_drug",
    "m18_drug_interaction_master",
)

# 铁律 4：病历事实表不可删除
FACT_TABLES = ("m18_emr_record", "m18_emr_amendment", "m18_emr_seal")

# 共享规范 §8 的内部契约路径（P-01 ~ P-14）
P_CONTRACTS = {
    "P-01": "/internal/v1/emr/record/by-encounter/",
    "P-02": "/internal/v1/emr/record/section",
    "P-03": "/internal/v1/emr/record/",
    "P-04": "/internal/v1/emr/archive/push",
    "P-05": "/internal/v1/emr/consent/",
    "P-06": "/internal/v1/emr/consents/by-apply/",
    "P-07": "/internal/v1/emr/consents/by-patient/",
    "P-08": "/internal/v1/kb/medication-check",
    "P-09": "/internal/v1/kb/drg-weights",
    "P-10": "/internal/v1/m18/emr/document-exists",
    "P-11": "/internal/v1/m18/emr/record/finalize",
    "P-12": "/internal/v1/m18/kb/clinical-path/",
    "P-13": "/internal/v1/m18/kb/rule-reload",
    "P-14": "/internal/v1/m18/emr/seal-status/",
    "P-15": "/internal/v1/m18/kb/triage-rules",
}

# 上游写死的事件名，不得改名
LOCKED_EVENTS = ("emr.record.finalized", "m18.record.locked", "m18.archive.confirmed")
BAD_EVENT_NAMES = ("m18.record.finalized", "m18.archive.confirmed_v2")

# 病历正文字段名（不得出现在事件载荷里）
RECORD_BODY_FIELDS = (
    "chief_complaint",
    "present_illness",
    "past_history",
    "physical_exam",
    "diagnosis_text",
    "treatment_plan",
)

ERR_RE = re.compile(r'"(\d{7})"')
TABLE_RE = re.compile(r"^###\s+4\.\d+\s+表：\s*`([A-Za-z0-9_]+)`", re.M)
PAGE_TREE_RE = re.compile(r"^(?:├──|└──)\s*(P\d{2})\s+(.+)$", re.M)
PAGE_SEC_RE = re.compile(r"^###\s+5\.\d+\s+(P\d{2})\s+(.+)$", re.M)
API_SEC_RE = re.compile(r"^####\s+API-(\d{2})", re.M)


class Report(object):
    def __init__(self):
        self.errors = []
        self.warns = []

    def err(self, path, msg):
        self.errors.append((path, msg))

    def warn(self, path, msg):
        self.warns.append((path, msg))


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def count_cols(s):
    parts = re.split(r"(?<!\\)\|", s)
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return len(parts)


def is_sep_row(s):
    if "|" not in s:
        return False
    cells = [c.strip() for c in re.split(r"(?<!\\)\|", s) if c.strip()]
    if not cells:
        return False
    return all(re.fullmatch(r":?-{2,}:?", c) for c in cells)


def check_common(path, t, rep):
    # a. 代码围栏配对
    fences = re.findall("^" + FENCE + r"(\w*)", t, re.M)
    if len(fences) % 2 != 0:
        rep.err(path, "代码围栏数量为奇数（%d），文件里有未闭合的代码块" % len(fences))

    # b. python 块 ast.parse；json 块 json.loads
    for m in re.finditer("^" + FENCE + r"(\w+)\n(.*?)\n" + FENCE, t, re.M | re.S):
        lang, body = m.group(1), m.group(2)
        lineno = t[: m.start()].count("\n") + 1
        if lang == "python":
            try:
                ast.parse(body)
            except SyntaxError as e:
                rep.err(path, "第 %d 行的 python 代码块无法 ast.parse：%s" % (lineno, e))
        elif lang == "json":
            try:
                json.loads(body)
            except Exception as e:
                rep.err(path, "第 %d 行的 json 代码块无法解析：%s" % (lineno, e))

    # c. 表格列数一致（按连续 | 行分组）
    lines = t.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|"):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                j += 1
            block = lines[i:j]
            if len(block) >= 2 and is_sep_row(block[1]):
                expect = count_cols(block[1])
                for k, row in enumerate(block):
                    if is_sep_row(row):
                        continue
                    c = count_cols(row)
                    if c != expect:
                        rep.err(
                            path,
                            "第 %d 行表格列数为 %d，应为 %d（表头列数）。排查单元格内是否有裸竖线"
                            % (i + k + 1, c, expect),
                        )
            i = j
        else:
            i += 1

    # d. 乱码
    for bad in ("ï¿½", "\ufffd", "â€", "æµ‹"):
        if bad in t:
            rep.err(path, "检测到乱码字符 %r" % bad)

    # e. 占位词（剔除四反引号代码块里的模板说明，只查正文）
    body = re.sub("(?ms)^" + FENCE + FENCE + FENCE + ".*?" + FENCE + FENCE + FENCE, "", t)
    for p in PLACEHOLDERS:
        if p in body:
            idx = body.find(p)
            lineno = body[:idx].count("\n") + 1
            rep.err(path, "第 %d 行附近残留占位词 %r" % (lineno, p))

    # f. MySQL / Oracle 语法
    #    DATETIME 走大小写敏感匹配，放过 Python 的 datetime 类名（见 CASE_SENSITIVE_BAD_SQL）
    for bad in BAD_SQL:
        flags = 0 if bad in CASE_SENSITIVE_BAD_SQL else re.I
        for m in re.finditer(re.escape(bad), t, flags):
            lineno = t[: m.start()].count("\n") + 1
            ln = t.split("\n")[lineno - 1]
            if re.match(r"^\s*[❌禁止不得严禁切勿]", ln) or "❌" in ln:
                continue
            rep.err(path, "第 %d 行出现 MySQL/Oracle 语法 %r" % (lineno, bad))


def check_design(path, t, rep):
    # 1~12 章
    for n in range(1, 13):
        if not re.search(r"^##\s+%d\.\s" % n, t, re.M):
            rep.err(path, "缺少第 %d 章标题（应为 ## %d. xxx）" % (n, n))
    # 附录 A~F
    for letter in "ABCDEF":
        if not re.search(r"^##\s+附录\s*%s" % letter, t, re.M):
            rep.err(path, "缺少附录 %s（应为 ## 附录 %s：xxx）" % (letter, letter))

    # 第 4 章只有指引块
    m = re.search(r"(?ms)^##\s+4\.\s.*?(?=^##\s+5\.\s)", t)
    if m:
        chap4 = m.group(0)
        if re.search(r"^###\s+4\.\d+\s+表：", chap4, re.M) or re.search(
            r"CREATE\s+TABLE", chap4, re.I
        ):
            rep.err(path, "第 4 章出现了表定义，必须只有指引块")

    # 页面总览与 5.x 标题双向一致
    tree = PAGE_TREE_RE.findall(t)
    secs = PAGE_SEC_RE.findall(t)
    tree_ids = [x[0] for x in tree]
    sec_ids = [x[0] for x in secs]
    if tree_ids:
        if tree_ids != sec_ids:
            rep.err(
                path,
                "页面总览树 %s 与第 5 章标题 %s 不一致" % (tree_ids, sec_ids),
            )
        if len(set(tree_ids)) != len(tree_ids):
            rep.err(path, "页面总览树里有重复编号")
        # 连续性
        expect = ["P%02d" % i for i in range(1, len(tree_ids) + 1)]
        if tree_ids != expect:
            rep.err(path, "页面编号不连续，期望 %s，实际 %s" % (expect, tree_ids))
    else:
        rep.warn(path, "未找到页面总览树（├── P01 xxx）")

    # 接口连续 + 逐项详述
    scope = re.search(r"(?ms)^###\s+6\.1\s.*?(?=^###\s+6\.2\s)", t)
    if scope:
        api_ids = sorted(set(int(x) for x in re.findall(r"API-(\d{2})", scope.group(0))))
        if api_ids:
            expect = list(range(1, len(api_ids) + 1))
            if api_ids != expect:
                rep.err(path, "接口总览编号不连续，期望 1~%d，实际 %s" % (len(api_ids), api_ids))
    detail_ids = sorted(set(int(x) for x in API_SEC_RE.findall(t)))
    if scope and api_ids:
        if detail_ids != api_ids:
            miss = sorted(set(api_ids) - set(detail_ids))
            extra = sorted(set(detail_ids) - set(api_ids))
            rep.err(
                path,
                "接口详述与总览不匹配：缺详述 %s，多出详述 %s（若第 6 章尚未写完，此为正常中间态）" % (miss, extra),
            )

    # 验收四类
    for prefix, minimum in (("AC", 35), ("PF", 8), ("DA", 5), ("SC", 4)):
        ids = sorted(set(int(x) for x in re.findall(r"\b%s-(\d{2})\b" % prefix, t)))
        if not ids:
            rep.err(path, "缺少 %s-xx 验收条目（至少 %d 条）" % (prefix, minimum))
            continue
        if len(ids) < minimum:
            rep.err(path, "%s 验收只有 %d 条，要求 >= %d" % (prefix, len(ids), minimum))
        expect = list(range(1, len(ids) + 1))
        if ids != expect:
            rep.err(path, "%s 编号不连续，实际 %s" % (prefix, ids))

    # 错误码
    codes = set(ERR_RE.findall(t))
    for c in codes:
        if c == "189001":
            continue
        n = int(c)
        if not (1801001 <= n <= 1808999):
            rep.err(path, "错误码 %s 不在 M18 号段（1801001~1808999 或 189001）内" % c)

    # 事件名
    for bad in BAD_EVENT_NAMES:
        if bad in t:
            rep.err(path, "出现被禁的事件名 %r（上游写死的是 emr.record.finalized）" % bad)
    if "emr.record.finalized" not in t and "m18.record.locked" not in t:
        rep.warn(path, "未出现任何上游写死的事件名，请确认本子模块确实不发事件")

    # 金额 / 比率
    if re.search(r"(NUMERIC|DECIMAL)\s*\(\s*\d+\s*,\s*2\s*\)", t, re.I) is None:
        rep.warn(path, "未见 NUMERIC(14,2)（金额类型）；若本子模块无金额字段可忽略")
    for m in re.finditer(r"\b(FLOAT|DOUBLE\s+PRECISION|REAL)\b", t):
        lineno = t[: m.start()].count("\n") + 1
        ln = t.split("\n")[lineno - 1]
        if "禁止" in ln or "不得" in ln or "❌" in ln:
            continue
        rep.err(path, "第 %d 行使用浮点类型 %s 描述字段（金额/比率必须用 NUMERIC）" % (lineno, m.group(1)))


def check_struct(path, t, rep, sub):
    allowed = SUBSYS_PREFIX.get(sub, [])

    tables = TABLE_RE.findall(t)
    if not tables:
        rep.err(path, "未找到任何 `### 4.x 表：` 定义")
        return
    if len(set(tables)) != len(tables):
        dup = [x for x in set(tables) if tables.count(x) > 1]
        rep.err(path, "同一文件内重复定义表：%s" % dup)

    for tb in set(tables):
        if not tb.startswith("m18_"):
            rep.err(path, "表名 %r 不是 m18_ 前缀" % tb)
            continue
        if allowed and not any(tb.startswith(p) for p in allowed):
            rep.err(
                path,
                "表名 %r 不符合本子模块前缀 %s（若为跨子模块共用表 m18_emr_*，"
                "请在数据结构汇总标注归属）" % (tb, allowed),
            )

    # 表清单声明数量与实际一致
    decl = re.search(r"\*\*合计：\s*(\d+)\s*张表\*\*", t) or re.search(
        r"\*\*表数量：\*\*\s*(\d+)\s*张", t
    )
    if decl:
        if int(decl.group(1)) != len(tables):
            rep.err(
                path,
                "表清单声明 %s 张，实际定义 %d 张" % (decl.group(1), len(tables)),
            )
    else:
        rep.warn(path, "未找到「**合计：N 张表**」声明")

    # SQLAlchemy + Pydantic 章节
    if not re.search(r"^###\s+4\.\d+\s+SQLAlchemy", t, re.M):
        rep.err(path, "缺少 `### 4.x SQLAlchemy` 模型定义章节")
    if not re.search(r"^###\s+4\.\d+\s+Pydantic", t, re.M):
        rep.err(path, "缺少 `### 4.x Pydantic` Schema 定义章节")

    # 附录 A~F
    for letter in "ABCDEF":
        if not re.search(r"^##\s+附录\s*%s" % letter, t, re.M):
            rep.err(path, "缺少附录 %s" % letter)

    # 版本历史
    if "版本历史" not in t:
        rep.err(path, "附录 F 缺少版本历史表")

    # 铁律 2：禁止的表
    for bad in FORBIDDEN_TABLES:
        if re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?" + re.escape(bad) + r"\b", t, re.I):
            rep.err(path, "出现禁止定义的表 %r（该表归 M07/M05/M09/M08/M01）" % bad)

    # 铁律 4：病历事实表不可删除
    for tb in FACT_TABLES:
        if tb not in tables:
            continue
        seg = re.search(
            r"(?ms)^###\s+4\.\d+\s+表：\s*`" + re.escape(tb) + r"`(.*?)(?=^###\s+|\Z)", t
        )
        if not seg:
            continue
        body = seg.group(1)
        if re.search(r"^\|\s*is_deleted\s*\|", body, re.M):
            rep.err(path, "病历事实表 %r 不得有 is_deleted 字段（不可删除）" % tb)
        if "REVOKE DELETE" not in body:
            rep.err(path, "病历事实表 %r 缺少 REVOKE DELETE 语句" % tb)

    # m18_emr_record 签署后禁改
    if "m18_emr_record" in tables:
        if "REVOKE UPDATE" not in t and "trg_fn" not in t and "触发器" not in t:
            rep.err(path, "m18_emr_record 缺少「签署后禁改」的数据库层落地（REVOKE UPDATE 或触发器）")

    # content_hash
    for m in re.finditer(r"content_hash\s*\|\s*VARCHAR\((\d+)\)", t):
        if m.group(1) != "64":
            rep.err(path, "content_hash 必须是 VARCHAR(64)（SHA-256），实际 VARCHAR(%s)" % m.group(1))
    if re.search(r"content_hash\s*\|\s*MD5", t, re.I):
        rep.err(path, "content_hash 不得使用 MD5")
    if re.search(r"\bmd5\s*\(", t, re.I):
        rep.err(path, "出现 md5()（病历哈希必须 SHA-256）")

    # 同意书签署状态不得落表
    for tb in tables:
        if re.search(r"consent.*sign|sign.*consent", tb) and not tb.endswith("_template"):
            rep.err(path, "出现同意书签署状态表 %r（签署权威在 M07-06，M18 不建签署表）" % tb)

    # 分区表必须带 DEFAULT
    for m in re.finditer(r"CREATE\s+TABLE[^;]*?PARTITION\s+BY\s+RANGE[^;]*;", t, re.I | re.S):
        blob = m.group(0)
        if "DEFAULT" not in blob:
            lineno = t[: m.start()].count("\n") + 1
            rep.err(path, "第 %d 行的分区表缺少 DEFAULT 分区" % lineno)


def check_p_contract(path, t, rep):
    """P-xx 路径必须与共享规范 §8 一字不差。"""
    for m in re.finditer(r"\|\s*\**(P-\d{2})\**\s*\|\s*[A-Z]+\s*\|\s*`(/internal/[^`]+)`", t):
        pid, pathv = m.group(1), m.group(2)
        expect = P_CONTRACTS.get(pid)
        if expect is None:
            rep.err(path, "登记了未知的内部契约编号 %s" % pid)
            continue
        if not pathv.startswith(expect):
            rep.err(
                path,
                "内部契约 %s 的路径 %r 与共享规范不一致，应为 %r 开头" % (pid, pathv, expect),
            )


def check_event_payload(path, t, rep):
    """事件载荷不得出现病历正文字段。

    作用域：只扫**事件定义本身**（10.3 发布 / 10.4 订阅两张表 + 第 10 章中
    `payload` 相关代码块），不扫 10.2「提供接口」表。

    理由（V1.1）：10.2 是**内部接口的字段契约**，P-01 的响应本来就要返回病历正文
    六段（否则 M07-06 拿不到东西去渲染文书）。初版把扫描范围定成整个第 10 章，
    逼得文档在 10.2 里连字段名都不敢写，读者得跳到 §6.3 才知道 P-01 返回什么——
    为了绕开检查而牺牲文档的可读性，是把检查做成了目的。红线的实质是「事件
    广播到 MQ 时不许带正文」，所以只该扫事件定义，不该扫接口契约。
    """
    m = re.search(r"(?ms)^##\s+10\..*?(?=^##\s+11\.)", t)
    if not m:
        return
    chap = m.group(0)
    # 剔除 10.2 提供接口小节（接口字段契约允许出现正文字段名）
    chap = re.sub(r"(?ms)^###\s+10\.2\b.*?(?=^###\s+10\.3\b)", "", chap)
    # V1.3：改用「标识符边界」匹配，不再用裸子串匹配。
    # 红线针对的是「事件载荷里带了正文字段」，而不是「任何包含这串字母的名字」。
    # 裸子串会把 diagnosis_lines（diagnosis_text 的前缀族）、physical_exam_note
    # 这类**新造字段名**判成违规，逼成员给字段改名绕检查——改名绕检查既不改变
    # 事实（该字段仍可能带正文），又会让命名变差。边界匹配同样抓得到真正的违规
    # （`"chief_complaint":`、`payload["physical_exam"]`、表格里的 `| diagnosis_text |`）。
    for f in RECORD_BODY_FIELDS:
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(f) + r"(?![A-Za-z0-9_])", chap):
            lineno = t[: m.start()].count("\n") + chap[: chap.find(f)].count("\n") + 1
            rep.err(
                path,
                "第 %d 行事件章节出现病历正文字段 %r（事件载荷不得含病历正文）" % (lineno, f),
            )


def check_errcode_semantics(path, t, rep):
    """6.6 权威表内 (错误码 -> 含义) 与全文其它引用行比对。"""
    # V1.3：前瞻补 `|\Z`。原来的前瞻只有「6.7 / 第 7 章 / 附录」三个锚点，
    # 文档写到第 6 章还没写第 7 章时三个锚点都不存在，切片会一路吃到文件
    # 末尾；表面能匹配，但报错文案「未找到 6.6 错误码定义表」会让人误以为
    # 文档缺表，实际是章节没写全。M18-03 为此白查了半天文档。
    m = re.search(r"(?ms)^###\s+6\.6\s.*?(?=^###\s+6\.7\s|^##\s+7\.|^##\s+附录|\Z)", t)
    if not m:
        rep.warn(path, "未找到 6.6 错误码定义表（若第 6 章尚未写完，此为正常中间态）")
        return
    auth = {}
    for line in m.group(0).split("\n"):
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line)]
        cells = [c for c in cells if c != ""]
        if len(cells) < 3:
            continue
        mc = re.fullmatch(r'"?(\d{7})"?', cells[0])
        if not mc:
            continue
        auth[mc.group(1)] = cells[2]

    def bigrams(s):
        s = re.sub(r"[\s，。、：；！？（）()【】`\"'—\-]", "", s)
        return set(s[i : i + 2] for i in range(max(0, len(s) - 1)))

    for m2 in re.finditer(r"\|\s*\"?(\d{7})\"?\s*\|\s*([^|\n]{4,})\s*\|", t):
        code, meaning = m2.group(1), m2.group(2).strip()
        if code not in auth or code == m2.group(1) and meaning == auth[code]:
            continue
        if m.start() <= m2.start() < m.end():
            continue
        a, b = bigrams(auth[code]), bigrams(meaning)
        if not b:
            continue
        overlap = len(a & b) / float(len(b))
        if overlap < 0.30:
            lineno = t[: m2.start()].count("\n") + 1
            rep.err(
                path,
                "第 %d 行错误码 %s 的语义 %r 与 6.6 权威表 %r 不一致（重合度 %.2f）"
                % (lineno, code, meaning, auth[code], overlap),
            )


def check_dup_sections(path, t, rep):
    body = re.sub("(?ms)^#{0,2}?\\s*" + FENCE + FENCE + ".*?" + FENCE + FENCE, "", t)
    seen = {}
    for m in re.finditer(r"^(#{2,3})\s+(.+)$", body, re.M):
        title = m.group(2).strip()
        if "附录" in title:
            continue
        key = title
        seen[key] = seen.get(key, 0) + 1
    for k, v in seen.items():
        if v > 1:
            rep.err(path, "章节标题重复 %d 次：%r" % (v, k))


def check_glued_headings(path, t, rep):
    """V1.3 新增：一行内挤了两个标题（追加写作的接缝残留）。

    起因：M18-08 一度出现 `## 11. 异常处理与日志## 11. 异常处理与日志`——
    标题打了两遍粘在同一行。原有的重号检查 check_dup_sections 用
    `^(#{2,3})\s+(.+)$` 前缀匹配，前缀对上了就整行当标题收下，
    后面挂着的第二个标题永远看不见。

    追加型写作（cat >> / 分段 heredoc / 分段写文件）的接缝是校验盲区：
    校验器验证的是「有没有」，不是「有没有多出来」。
    """
    body = re.sub("(?ms)^#{0,2}?\s*" + FENCE + FENCE + ".*?" + FENCE + FENCE, "", t)
    for i, ln in enumerate(body.split("\n"), 1):
        if not ln.startswith("#"):
            continue
        rest = ln.lstrip("#").strip()
        if re.search(r"(?<![`#])#{1,6}\s*[0-9\u4e00-\u9fa5A-Za-z]", rest):
            rep.err(path, "第 %d 行粘连了两个标题：%s" % (i, ln[:60]))


def check_toc(path, t, rep):
    """V1.3 新增：章节目录与正文实际标题的一致性（骨架腐烂）。

    起因：M18-07 的章节目录里附录 A~F 六个名称全部是早期草稿，
    与实际写成的附录标题全部错位——目录写「附录 D 统计指标全集」，
    正文的附录 D 是「接口与页面映射表」。因为目录在文档最前面、
    读者第一眼就看它，却最不被维护（它不影响正文正确性）。
    校验器原来只看「有没有附录 A」，不看「目录里叫的名字和正文对不对」。

    做法：找文档开头的目录区块（`## 目录` / `## 章节目录` / `## 章节索引`），
    在其中收集「附录 X …」的名称，与正文 `## 附录 X：…` 的实际标题双向比对。
    正文没有目录区块的不报错（不是所有文档都写目录）。
    """
    body = re.sub("(?ms)^#{0,2}?\s*" + FENCE + FENCE + ".*?" + FENCE + FENCE, "", t)
    lines = body.split("\n")

    # 正文实际附录标题
    actual = {}
    for m in re.finditer(r"^##\s+附录\s*([A-F])\s*[：:]\s*(.+?)\s*$", body, re.M):
        actual[m.group(1)] = m.group(2).strip()
    # 目录区块
    toc_at = None
    for i, ln in enumerate(lines):
        if re.match(r"^##\s*(目录|章节目录|章节索引|章节索引表)\s*$", ln.strip()):
            toc_at = i
            break
    if toc_at is None or not actual:
        return

    toc = {}
    for ln in lines[toc_at + 1:]:
        if ln.startswith("## ") and not ln.startswith("## 附录"):
            break
        s = ln.strip()
        if not s:
            continue
        # 表格行： | 附录 A | [接口清单](#...) |
        m = re.match(r"^\|\s*附录\s*([A-F])\s*\|\s*\[([^\]]+)\]", s)
        if m:
            toc[m.group(1)] = m.group(2).strip()
            continue
        # 列表/纯文本行： - 附录 A 接口清单  /  附录 A：接口清单
        # 多列表格行 `| 附录 A | 名称 | 说明 |` 单独走一条，只取名称（第二列），
        # 不能让它落进下面的通用分支——通用分支的 group(2) 会连说明一起吃掉。
        m3 = re.match(r"^\|\s*附录\s*([A-F])\s*\|\s*([^|]+?)\s*\|", s)
        if m3:
            nm = m3.group(2).strip()
            nm = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", nm)
            toc[m3.group(1)] = nm
            continue
        m = re.match(r"^(?:[-*+]\s*)?附录\s*([A-F])\s*[：:、\s]\s*(.+?)\s*$", s)
        if m:
            name = m.group(2).strip()
            name = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", name)
            # 多列目录：`| 附录 A | 名称 | 说明 |` 的 group(2) 会吃掉到行尾，
            # 名称是第一段，说明是后面几段。先剥掉行尾竖线再取第一段。
            name = name.rstrip().rstrip("|").strip()
            name = name.split("|")[0].lstrip("|").strip()
            toc[m.group(1)] = name
    if not toc:
        return

    def key(s):
        return re.sub(r"[\s：:、，,。.（）()《》<>\-_/]", "", s)

    for letter in sorted(toc):
        if letter not in actual:
            continue
        a, b = key(toc[letter]), key(actual[letter])
        if a == b:
            continue
        # 允许「目录用简称、正文带后缀」这类前缀关系，但不允许完全不同
        if a and b and (a.startswith(b) or b.startswith(a)):
            continue
        rep.err(path, "章节目录里附录 %s 写作 %r，正文实际标题为 %r"
                % (letter, toc[letter], actual[letter]))


def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate_m18.py <M18电子病历与知识库目录>")
        sys.exit(2)
    root = sys.argv[1]
    rep = Report()

    design_files = sorted(
        f for f in os.listdir(root) if f.endswith("_详细设计.md") and re.search(r"_\d{2}_", f)
    )
    struct_files = sorted(
        f for f in os.listdir(root) if f.endswith("_数据结构.md") and re.search(r"_\d{2}_", f)
    )
    other_files = sorted(
        f
        for f in os.listdir(root)
        if f.endswith(".md") and f not in design_files and f not in struct_files
    )

    for fn in design_files + struct_files:
        path = os.path.join(root, fn)
        t = read(path)
        check_common(path, t, rep)
        sub = re.search(r"_(\d{2})_", fn).group(1)
        if fn in design_files:
            check_design(path, t, rep)
            check_p_contract(path, t, rep)
            check_event_payload(path, t, rep)
            check_errcode_semantics(path, t, rep)
        else:
            check_struct(path, t, rep, sub)
        check_dup_sections(path, t, rep)
        check_glued_headings(path, t, rep)
        check_toc(path, t, rep)

    for fn in other_files:
        path = os.path.join(root, fn)
        t = read(path)
        check_common(path, t, rep)
        check_dup_sections(path, t, rep)
        check_glued_headings(path, t, rep)
        check_toc(path, t, rep)

    for path, msg in rep.warns:
        print("⚠  %s: %s" % (os.path.basename(path), msg))
    for path, msg in rep.errors:
        print("✗  %s: %s" % (os.path.basename(path), msg))

    total = len(design_files) + len(struct_files) + len(other_files)
    print("")
    print("  详细设计 %d 个 / 数据结构 %d 个 / 模块级 %d 个，共 %d 个文件"
          % (len(design_files), len(struct_files), len(other_files), total))
    if rep.errors:
        print("✗ 校验失败：%d 个错误，%d 个告警" % (len(rep.errors), len(rep.warns)))
        sys.exit(1)
    print("✓ 全部通过（%d 个文件）" % total)


if __name__ == "__main__":
    main()
