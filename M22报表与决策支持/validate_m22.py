"""M22 文档交付前自动校验。

用法：
    python3 validate_m22.py M22报表与决策支持

校验项：
  1. 代码围栏配对 / Python 块 ast / JSON 块 json.loads / 表格列数 / 乱码 / 占位词 / MySQL 残留
  2. 详细设计 1~12 章 + 附录 A~F 齐全，第 4 章无表定义
  3. 页面总览树 P0x 与第 5 章 "### 5.x P0x" 双向一致
  4. 接口 API-01 起连续无断号，每一项都有 "#### API-xx" 详述
  5. AC>=35 / PF>=8 / DA>=5 / SC>=4，四类从 01 连续
  6. 错误码 7 位、前缀 17、号段 170Nxxx 不越界
  7. 数据结构：表前缀 m17_、表清单与 "### 4.x 表：" 一致、SQLAlchemy/Pydantic 章节、版本历史
  8. 【M22 专属】指标值字段不得使用 FLOAT/DOUBLE/REAL
  9. 【M22 专属】指标定义表必须有 (metric_code, version) 唯一约束
 10. 【M22 专属】指标事实表必须有采集幂等唯一键与溯源字段
 12. 模块级文档（总纲 / 汇总 / 共享规范）走独立检查
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
    "00_M22_报表与决策支持_模块设计_共享规范与文档模板.md",
    "M22_报表与决策支持_详细设计.md",
    "M22_报表与决策支持_数据结构设计汇总.md",
)


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


def check_metric_invariants(t, fp_name):
    """M22 专属：指标数值精度与指标表约束。"""
    issues = []

    if fp_name.endswith("_数据结构.md"):
        # 8. 指标值字段不得用浮点
        for m in re.finditer(
            r"`(\w*(?:value|rate|amount|ratio|score|index|target|actual|pct|percent)\w*)`"
            r"\s*\|\s*(FLOAT|DOUBLE|REAL)", t, re.I):
            issues.append((0, "指标值字段 %s 使用了浮点类型 %s，应为 NUMERIC"
                           % (m.group(1), m.group(2))))

        # 9. 指标定义表必须有 (metric_code, version) 唯一约束
        #    仅当本文件自己定义（`### 4.x 表：m22_metric_def`）时才校验。
        #    M22-01 是 m22_metric_def 的唯一定义方，其他子模块只是逻辑引用
        #    metric_code，不应被要求重复给出该表的唯一约束。
        if re.search(r"^### 4\.\d+ 表：\s*`?m22_metric_def\b", t, re.M):
            if not re.search(r"UNIQUE[^;]*metric_code[^;]*version|"
                             r"uk_\w*metric_def\w*", t, re.I):
                issues.append((0, "指标定义表 m22_metric_def 缺少 (metric_code, version) 唯一约束"))
            if not re.search(r"uk_\w*metric_def_active[^\n]*|"
                             r"UNIQUE INDEX[^;]*metric_code[^;]*WHERE", t, re.I):
                issues.append((0, "指标定义表 m22_metric_def 缺少 \"同编码仅一个 ACTIVE\" 部分唯一索引"))

        # 10. 指标事实表必须有采集幂等唯一键与溯源字段
        #    判定：表名含 fact，或表的中文名含「事实」。
        #    注意「批次明细」这类表只是采集过程的记录，不是指标事实表，
        #    不应被要求带 source_module/source_api（它的来源就是调用方自己）。
        for blk in re.split(r"^### 4\.\d+ 表：", t, flags=re.M)[1:]:
            head = blk.split("\n", 1)[0]
            title = head.strip()
            is_fact = bool(re.search(r"\bfact\b", title, re.I)) or bool(
                re.search(r"[（(][^）)]*事实[^）)]*[）)]", title))
            if not is_fact:
                continue
            for fld, label in (("metric_code", "指标编码"), ("period", "统计期间"),
                               ("source_module", "来源模块"), ("source_api", "来源接口"),
                               ("collect_batch_no", "采集批次"), ("source_status", "数据完整性")):
                if fld not in blk:
                    issues.append((0, "指标事实表 %s 缺少溯源字段 %s(%s)" % (head, fld, label)))

    return issues


def check_no_duplicate_sections(t, fp_name):
    """M17 专属：关键章节必须唯一（多人并行补同一文件时极易产生重复）。"""
    issues = []
    # 模板内嵌的四反引号代码块（共享规范用）不算正文
    body = re.sub(r"(?ms)^#{0,2}?\s*`{4}.*?`{4}", "", t)

    must_once = [
        (r"^## 附录 F", "附录 F"),
        (r"^\*\*文档结束\*\*", "文档结束"),
    ]
    if fp_name.endswith("_数据结构.md"):
        # 版本历史块：取「最小命中数」，标题与表头都可作为标志
        n_h = len(re.findall(r"^## 版本历史", body, re.M))
        n_t = len(re.findall(r"^\| 版本 \| 日期 \|", body, re.M))
        if max(n_h, n_t) > 1:
            issues.append((0, "版本历史 出现 %d 次（应为 1 次，疑似重复）" % max(n_h, n_t)))
        must_once.append((r"^### 4\.\d+ Pydantic Schema 定义", "Pydantic Schema 章节"))

    for pat, label in must_once:
        n = len(re.findall(pat, body, re.M))
        if n > 1:
            issues.append((0, "%s 出现 %d 次（应为 1 次，疑似多人并行写入产生重复）" % (label, n)))

    # 附录 A~F 各自唯一
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

    # 接口总览只在第 6.1 节内统计。附录 B 等处的 "| API-xx | ..." 行是对照表，
    # 不是接口定义；若全文件扫描会被当成第二份接口表而误报「编号重复」。
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

    m = re.search(r"M22-(\d\d)\s", t[:3000])
    sub = m.group(1) if m else None
    for c in sorted(set(re.findall(r'"(\d{7})"', t))):
        if len(c) != 7 or not c.startswith("22"):
            issues.append((0, "错误码格式异常: %s" % c))
        elif sub and c[2:4] not in (sub, "90", "00"):
            issues.append((0, "错误码号段越界: %s（应为 M22-%s）" % (c, sub)))

    return issues


def check_struct(t):
    issues = []

    tables = re.findall(r"^### 4\.\d+ 表：`(\w+)`", t, re.M)
    for tb in tables:
        if not tb.startswith("m22_"):
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
        if not tb.startswith("m22_"):
            issues.append((0, "DDL 表前缀错误: %s" % tb))

    n_tab = len(set(tables))
    for pat in (r"\*\*表数量：\*\*\s*(\d+)\s*张", r"\*\*合计：\s*(\d+)\s*张表\*\*"):
        m = re.search(pat, t)
        if m and int(m.group(1)) != n_tab:
            issues.append((0, "表数量声明 %s 与实际 %d 不符" % (m.group(1), n_tab)))

    if not re.search(r"^\| 版本 \|", t, re.M) and not re.search(r"^## 版本历史", t, re.M):
        issues.append((0, "缺少版本历史"))

    return issues


def validate(fp):
    t = fp.read_text(encoding="utf-8")
    issues = check_common(fp, t)
    issues += check_metric_invariants(t, fp.name)
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
    for fp in sorted(root.glob("M22_*.md")):
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
