"""M11 文档交付前自动校验（hardened）。

用法：
    python3 validate_m11.py M11屈光手术管理

在共享规范第 16 章原版脚本基础上加固：
  * ast / json 解析异常全部捕获，不让单个坏块中断整轮校验
  * 页面树正则同时支持 "├── P01" 与 "└── P01"
  * 校验 1~12 章标题齐全、API 总览每一项都有 "#### API-xx" 详述
  * 校验 AC/PF/DA/SC 四类验收从 01 起连续
  * 校验错误码号段（自动从正文 "M10-0N" 推断子模块号）
  * 校验表清单与 "### 4.x 表：" 标题一致、第 4 章指引块表数一致
  * 模块级文档（总纲 / 汇总 / 共享规范）走独立检查，不套子模块模板
"""
import ast
import json
import re
import sys
from pathlib import Path

FENCE = chr(96) * 3
BAD_SQL = ("AUTO_INCREMENT", "TINYINT", "DATETIME", "ENGINE=", "VARCHAR2")
PLACEHOLDERS = ("TODO", "待补充", "XXX 表", "略。")

# 模块级文档：不套用子模块模板
MODULE_DOCS = (
    "00_M11_屈光手术管理_模块设计_共享规范与文档模板.md",
    "M11_屈光手术管理_详细设计.md",
    "M11_屈光手术管理_数据结构设计汇总.md",
)


def split_table(t: str):
    """返回 [(start_line, table_text)]。"""
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


def is_sep_row(line: str) -> bool:
    """判断是否为表头分隔行。"""
    s = line.strip().strip("|")
    return bool(s) and all(c in "-: " for c in s) and "-" in s


def count_cols(line: str) -> int:
    """按未转义竖线计算列数。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return len(re.split(r"(?<!\\)\|", s))


def check_common(fp: Path, t: str):
    """通用检查：围栏 / 语法 / 表格 / 占位词 / MySQL 残留。"""
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


def check_module_doc(t: str):
    """模块级文档检查：至少 5 个二级章节。"""
    issues = []
    h2 = re.findall(r"^## (.+)$", t, re.M)
    if len(h2) < 5:
        issues.append((0, "二级章节过少（%d），疑似内容缺失" % len(h2)))
    return issues


def check_design(t: str):
    """详细设计专项。"""
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

    apis = [int(x) for x in re.findall(r"^\|\s*\**API-(\d+)\**\s*\|", t, re.M)]
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

    m = re.search(r"M11-(\d\d)\s", t[:3000])
    sub = m.group(1) if m else None
    for c in sorted(set(re.findall(r'"(\d{7})"', t))):
        if len(c) != 7 or not c.startswith("11"):
            issues.append((0, "错误码格式异常: %s" % c))
        elif sub and c[2:4] not in (sub, "90", "00"):
            issues.append((0, "错误码号段越界: %s（应为 M11-%s）" % (c, sub)))

    return issues


def check_struct(t: str):
    """数据结构专项。"""
    issues = []

    tables = re.findall(r"^### 4\.\d+ 表：`(\w+)`", t, re.M)
    for tb in tables:
        if not tb.startswith("m11_"):
            issues.append((0, "表名前缀错误: %s" % tb))
    if len(tables) != len(set(tables)):
        issues.append((0, "表定义重复"))

    if "SQLAlchemy 2.0 模型定义" not in t:
        issues.append((0, "缺少 SQLAlchemy 模型章节"))
    if "Pydantic Schema 定义" not in t:
        issues.append((0, "缺少 Pydantic Schema 章节"))

    ddl = re.findall(r"CREATE TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_]\w*)", t)
    for tb in ddl:
        if tb in ("IF", "NOT", "EXISTS", "PARTITION", "SELECT", "AS"):
            continue  # 动态分区 DDL 的占位符，跳过
        if not tb.startswith("m11_"):
            issues.append((0, "DDL 表前缀错误: %s" % tb))

    n_tab = len(set(tables))
    m = re.search(r"\*\*表数量：\*\*\s*(\d+)\s*张", t)
    if m and int(m.group(1)) != n_tab:
        issues.append((0, "表数量声明 %s 与实际 %d 不符" % (m.group(1), n_tab)))

    if not re.search(r"^## 版本历史", t, re.M):
        issues.append((0, "缺少版本历史"))

    return issues


def validate(fp: Path):
    """单文件校验，返回 [(line, msg)]。"""
    t = fp.read_text(encoding="utf-8")
    issues = check_common(fp, t)

    if fp.name in MODULE_DOCS or fp.name.startswith("00_"):
        issues += check_module_doc(t)
    elif fp.name.endswith("_数据结构.md"):
        issues += check_struct(t)
    else:
        issues += check_design(t)

    return issues


def main() -> int:
    """入口。"""
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    fails = 0
    total = 0
    for fp in sorted(root.glob("M11_*.md")):
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
