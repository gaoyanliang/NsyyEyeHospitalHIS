#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M20 移动办公 —— 跨文件/跨章节一致性检查器

它为什么存在
============

`validate_m20.py` 检查的是**单个文件内部的结构是否合法**：章节齐不齐、表格列数对不对、
禁用词有没有、枚举值合不合规、验收编号连不连续。它做得很好，M20 的 18 份文件在它下面
基本全绿。

但它有一个天花板：**它只能看见一份文件、并且只能判断「格式对不对」，判断不了
「同一件事在两处说法一致不一致」。**

真实发生过的四类错误，没有一类能被 `validate_m20.py` 发现：

1. `"2002042"` 在 §6.6 权威表里是「该医生同病区已有进行中的查房」，在附录 C 里却写成
   「查房plan已存在进行中」（还混了英文）。**两张表格式都完全合法**，章章节节齐全，
   校验器逐项通过。发现它靠的是写一个脚本把两张表抽出来逐条比对。
   教训：「唯一权威表」这个说法只说对了一半 —— 真正的问题不是「谁权威」，
   而是**两处文字会分头演化**。

2. M20-07 的附录 A 页面表与附录 B 接口表按印象填写，与 §6.1 总览、§6.3 详述的编号
   **集合全错位**。校验器只检查「接口编号 1..N 连续」，它不关心附录里写的是不是同一批。

3. 正文里写「详见 §10.6」，而全文根本没有 §10.6。**指向不存在的章节和指向存在的章节
   长得一模一样**，任何格式检查都不可能发现，只有拿目标数字去被引用文件里找一遍才行。

4. 同一张表在子模块数据结构 §4.x、子模块详细设计第 4 章、模块级汇总 §1.1 三个地方各写
   一遍表数。**任何一处改了另外两处不跟着改**，三处都各自合法。

所以这个脚本补的就是这五类。它**不追求覆盖率**，只查「一旦出错会真的有人被误导」的地方。
宁可少查几类查得准，也不要多查几类一半误报 —— 误报会让脚本被弃用，那比没有更难挽回。

设计约定
--------

* **只报两种结果**：要么这一项通过（只在 `--verbose` 时打印），要么报出**两边各自的值**
  和**行号**。只报「不一致」没有价值，看的人还得自己去翻。
* **退出码**：全部通过 `0`，有问题 `1`，脚本自身参数错误 `2`。可以直接挂 CI。
* **静默跳过**：某份文件还没写完（比如正在补章节），对应检查在没有可比对象时跳过而
  不报错，避免把一个「还没写到」误判成「写错了」。
* **不做模糊匹配**：含义文本去空白后**精确比对**。宁可漏掉「意思一样但措辞不同」，
  也不要对措辞差异误报。

用法
----

    python3 M20移动办公/check_consistency.py M20移动办公
    python3 M20移动办公/check_consistency.py M20移动办公 --verbose

检查项编号 C-01 ~ C-05，报错里带编号，方便与 `validate_m20.py` 的检查项区分开。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# --------------------------------------------------------------------------
# 数据结构
# --------------------------------------------------------------------------


class Finding:
    """一条检查结果。

    file/line 指向「被检查位置」，detail 里必须同时写出**两边各自的值**。
    """

    __slots__ = ("check", "file", "line", "message", "left", "right")

    def __init__(self, check, file, line, message, left, right):
        # type: (str, str, int, str, str, str) -> None
        self.check = check
        self.file = file
        self.line = line
        self.message = message
        self.left = left
        self.right = right

    def render(self):
        # type: () -> str
        return "{}  {}:{}  {}\n      左: {}\n      右: {}".format(
            self.check, self.file, self.line, self.message, self.left, self.right
        )


def read_text(path):
    # type: (Path) -> str
    return path.read_text(encoding="utf-8")


def strip_fences(text):
    """把围栏代码块内容抹成等长空白，保持行号不变。

    代码块里出现 `| API-01 |` 或 `"2002001"` 是正常的（示例 JSON、建表语句），
    不能被当成正文表格行。保留行号对报错定位很重要，所以逐行替换而不是删除。
    """
    out = []
    fence = None
    for line in text.splitlines(True):
        stripped = line.lstrip()
        if fence is None:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = stripped[:3]
                # 抹成同样字符数的空格，但保留「这一行是什么」的痕迹：若整行空白，
                # 下一轮扫描就再也认不出它曾是围栏，会把下面的代码当正文。
                out.append(" " * (len(line.rstrip("\n")) - len(fence)) + fence
                           + ("\n" if line.endswith("\n") else ""))
            else:
                out.append(line)
        else:
            # 围栏的「关闭」必须是独占一行的 ``` 或 ```后面只跟空白。
            # 原来用 startswith(fence)，于是 ```sql 这种带语言的开启行会被判成关闭：
            # 上一块还没收尾，下一块的 ```sql 一来就把围栏状态翻回「正文」，
            # 于是夹在中间的所有章节标题都被当成正文——检查结果看起来是
            # 「文档缺了三张表」，实际是检查器自己错位了。
            if stripped.rstrip() == fence.strip() or (
                    stripped.startswith(fence)
                    and stripped[len(fence):].strip() == ""):
                fence = None
            out.append(" " * len(line.rstrip("\n")) + "\n")
    return "".join(out)


def section_slice(text, start_pat, end_pat):
    """按正则切出某一段，返回 (起始行号, 片段文本)。

    行号从 1 开始。找不到返回 (0, "")。
    """
    lines = text.splitlines()
    start = -1
    end = len(lines)
    for i, line in enumerate(lines):
        if start < 0:
            if re.match(start_pat, line):
                start = i
        else:
            if re.match(end_pat, line):
                end = i
                break
    if start < 0:
        return 0, ""
    return start + 1, "\n".join(lines[start:end])


# 章节标题：## / ### / ####
H2 = r"^##\s+"
ANY_HEADING = r"^#{2,4}\s+"

# --------------------------------------------------------------------------
# 文件分类
# --------------------------------------------------------------------------

DESIGN_RE = re.compile(r"^M20_移动办公_(\d{2})_.+_详细设计\.md$")
STRUCT_RE = re.compile(r"^M20_移动办公_(\d{2})_.+_数据结构\.md$")
SUMMARY_NAME = "M20_移动办公_数据结构设计汇总.md"


def collect(root):
    # type: (Path) -> Tuple[Dict[str, Path], Dict[str, Path], Path]
    designs = {}  # type: Dict[str, Path]
    structs = {}  # type: Dict[str, Path]
    summary = root / SUMMARY_NAME
    for p in sorted(root.glob("M20_*.md")):
        m = DESIGN_RE.match(p.name)
        if m:
            designs[m.group(1)] = p
            continue
        m = STRUCT_RE.match(p.name)
        if m:
            structs[m.group(1)] = p
    return designs, structs, summary


# --------------------------------------------------------------------------
# C-01 同一组表在三个文件里是否一致
# --------------------------------------------------------------------------


TABLE_HEADING = re.compile(r"^###\s+4\.\d+\s*表\s*[：:]\s*`?(m20_[a-z0-9_]+)`?")
BACKTICK_TABLE = re.compile(r"`(m20_(?:base|doc|nur|apr|qry|sal|fol|msg)_[a-z0-9_]+)`")


# 「说明不建这张表」的行：写的是「不许有」，不是「这里有」
NEGATIVE_MARKERS = (
    "不建",
    "只引用不建",
    "禁止",
    "不拥有",
    "不存储",
    "不保存",
    "不得建",
)

# 各子模块的表前缀；不是本子模块前缀的就是跨子模块引用，不参与本文件的集合比对
PREFIX_BY_SUB = {
    "01": "m20_base_",
    "02": "m20_doc_",
    "03": "m20_nur_",
    "04": "m20_apr_",
    "05": "m20_qry_",
    "06": "m20_sal_",
    "07": "m20_fol_",
    "08": "m20_msg_",
}


def _is_negative_context(line):
    # type: (str) -> bool
    """这一行是在说「不建」，而不是在说「有这张表」。

    第 4 章经常有一张「诱惑点 / 会不会建 / 理由」表，逐条列出**明确不建**的表，
    例如 `| m20_nur_task 护理任务副本 | 不建 | ... |`。这些表名当然不会出现在
    数据结构文件里 —— 它们本来就不该存在。把它们当成「引用了未定义的表」是纯误报，
    而且这类误报会成批出现，足以让整个脚本被弃用。
    """
    if "不建" in line or "只引用不建" in line:
        return True
    # 表格行：只有第二列明确写「不建」才算
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) >= 2 and cells[1] in ("不建", "否", "不", "不需要"):
        return True
    return False


def check_c01_table_sets(root, designs, structs, summary):
    # type: (Path, Dict[str, Path], Dict[str, Path], Path) -> List[Finding]
    """C-01 表集合三处一致：数据结构 §4.x 标题 == 详细设计第 4 章引用 == 汇总 §1.1 声明数。

    三者对应关系：
      * 数据结构文件里的 `### 4.x 表：`m20_xxx`` 是表的**唯一定义处**；
      * 详细设计第 4 章是**指引块**，引用的表名必须与定义处完全一致；
      * 汇总 §1.1 声明每个子模块「设计目标」表数。
    """
    findings = []  # type: List[Finding]

    # 汇总 §1.1 的「实际表数」列
    # 判据：表头里含「实际」二字的列才是要比对的那一列；没有含「实际」的列时
    # （旧版表头「设计目标」是唯一数字列）退回第一列数字。
    # 为什么不一刀切取第一列数字：设计目标是意图，实际是交付结果，两者本来就可以
    # 不相等。拿设计目标去和交付结果比，报出来的每一条都是噪声，而噪声会让人把
    # 这条检查整个关掉。
    targets = {}  # type: Dict[str, Tuple[int, int]]
    if summary.exists():
        text = strip_fences(read_text(summary))
        start, blob = section_slice(text, r"^###\s+1\.1\b", r"^#{2,3}\s+")
        if blob:
            lines = blob.splitlines()
            actual_idx = None  # type: Optional[int]
            for line in lines:
                if not line.lstrip().startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if "实际" in "".join(cells):
                    for idx, cell in enumerate(cells):
                        if "实际" in cell:
                            actual_idx = idx
                            break
                    break
            for offset, line in enumerate(lines):
                if not line.lstrip().startswith("|"):
                    continue
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                m = re.match(r"^M20-(\d{2})$", cells[0]) if cells else None
                if not m:
                    continue
                value = None  # type: Optional[int]
                if actual_idx is not None and actual_idx < len(cells):
                    if re.match(r"^\d+$", cells[actual_idx]):
                        value = int(cells[actual_idx])
                else:
                    for cell in cells[3:] or cells[1:]:
                        if re.match(r"^\d+$", cell):
                            value = int(cell)
                            break
                if value is not None:
                    targets[m.group(1)] = (start + offset, value)

    for sub in sorted(set(designs) | set(structs)):
        defined = set()  # type: Set[str]
        defined_lines = {}  # type: Dict[str, int]

        # --- 定义处：子模块数据结构 §4.x ---
        if sub in structs:
            stext = strip_fences(read_text(structs[sub]))
            for i, line in enumerate(stext.splitlines(), 1):
                m = TABLE_HEADING.match(line)
                if m:
                    defined.add(m.group(1))
                    defined_lines[m.group(1)] = i

        if not defined:
            # 还没写到表定义，跳过而不是报错
            continue

        # --- 汇总 §1.1 声明数 ---
        if sub in targets:
            tline, tcount = targets[sub]
            if tcount != len(defined):
                findings.append(
                    Finding(
                        "C-01",
                        summary.name,
                        tline,
                        "汇总 §1.1 声明的表数与该子模块数据结构里实际定义的表数不符",
                        "汇总 §1.1 写 {} 张".format(tcount),
                        "数据结构文件实际定义 {} 张: {}".format(
                            len(defined), ", ".join(sorted(defined))
                        ),
                    )
                )
        else:
            findings.append(
                Finding(
                    "C-01",
                    summary.name,
                    1,
                    "汇总 §1.1 里没有 M20-{} 这一行（缺子模块登记）".format(sub),
                    "未找到",
                    "数据结构文件定义了 {} 张表".format(len(defined)),
                )
            )

        # --- 详细设计第 4 章引用 ---
        if sub in designs:
            dtext = strip_fences(read_text(designs[sub]))
            dline, dblob = section_slice(dtext, r"^##\s+4\.\s", r"^##\s+5\.")
            if dblob:
                referenced = set()  # type: Set[str]
                ref_lines = {}  # type: Dict[str, int]
                for offset, line in enumerate(dblob.splitlines()):
                    if _is_negative_context(line):
                        continue
                    for m in BACKTICK_TABLE.finditer(line):
                        name = m.group(1)
                        referenced.add(name)
                        ref_lines.setdefault(name, dline + offset)
                # 只比较本子模块前缀的表：跨子模块共用表（m20_base_* / m20_apr_* 等）
                # 本来就不定义在本文件里，指向它们是正常的
                prefix = PREFIX_BY_SUB.get(sub)
                if prefix:
                    referenced = {n for n in referenced if n.startswith(prefix)}
                extra = referenced - defined
                missing = defined - referenced
                for name in sorted(extra):
                    findings.append(
                        Finding(
                            "C-01",
                            designs[sub].name,
                            ref_lines[name],
                            "详细设计第 4 章引用了一张数据结构文件里没有定义的表",
                            "详细设计第 4 章引用 `{}`".format(name),
                            "数据结构文件 {} 只定义了: {}".format(
                                structs[sub].name, ", ".join(sorted(defined))
                            ),
                        )
                    )
                # 只报「少引用」是弱信号：指引块可以不列全，所以不报

    return findings


# --------------------------------------------------------------------------
# C-02 错误码：§6.6 == 附录 C == 正文引用
# --------------------------------------------------------------------------

# §6.6 有 5 列与 3 列两种形态（8 份文件里全出现过），所以按「首列是码，取第 3 列当含义」
# 来抽；3 列时第 3 列就是含义，5 列时第 3 列也是含义，两者都对得上。
# 附录 C 的形态更多（5 列 / 2 列 / 号段分组摘要 / 序号表），无法统一比对，见 check_c02 里的说明。
# 一行「| 码 | ... |」的通用形态：取首列码 + 该行全部单元格
CODE76_ROW = re.compile(r'^\|\s*`?"(\d{7})"`?\s*\|(.*)$')
CODE76_QUOTED = re.compile(r'"(\d{7})"')


def parse_code_row(line):
    # type: (str) -> Optional[Tuple[str, str]]
    """从错误码表格行里抽出 (码, 含义)。2 列取第 2 列，3 列及以上取第 3 列。

    为什么不能用一个正则：§6.6 有 5 列（码/HTTP/含义/场景/建议）与 3 列（码/HTTP/含义）
    两种形态，附录 C 有 5 列（同 §6.6）与 2 列（码/含义）两种形态，
    全部混在一批文档里。固定列位的正则必然在其中一种上失败，
    而失败的表现是「一行都匹配不到」→ 整份附录看起来像空的 → 成批误报。
    """
    m = CODE76_ROW.match(line)
    if not m:
        return None
    code = m.group(1)
    rest = m.group(2)
    cells = [c.strip() for c in rest.split("|")]
    cells = [c for c in cells if c != ""]
    if not cells:
        return None
    if len(cells) >= 2 and re.match(r"^\d{3}$", cells[0]):
        # 形态 A：| 码 | HTTP | 含义 | ... |
        meaning = cells[1]
    else:
        # 形态 B：| 码 | 含义 | ... |
        meaning = cells[0]
    if not meaning or meaning.startswith("---"):
        return None
    return code, meaning


# 号段描述行：写的是「本子模块号段从 X 到 Y」，两端的码是边界值而不是真实错误码
RANGE_DESC = re.compile(r"号段|区间|范围")


def _is_range_bounds_line(line):
    # type: (str) -> bool
    """这一行是在描述号段边界，不是在引用一个具体错误码。

    例如「本子模块号段 `"2001001"` ~ `"2001999"`，公共码 `"209001"`」里的
    `2001999` 是号段上界，它本来就不该出现在 §6.6 的逐码表里 ——
    把它当成「引用了未定义的码」是误报。判据是同一行里出现了 `~` 或 `～`
    且含「号段/区间/范围」字样。
    """
    if not RANGE_DESC.search(line):
        return False
    return "~" in line or "～" in line or "-" in line or "至" in line


def check_c02_errcodes(root, designs, structs):
    # type: (Path, Dict[str, Path], Dict[str, Path]) -> List[Finding]
    """C-02 错误码三处一致：§6.6 权威表 == 附录 C 索引 == 正文引用是否都存在。

    这是 `"2002042"` 那个错误的检查方式。三件事：
      1. 附录 C 里每个码的含义必须与 §6.6 **逐字一致**（去空白后精确比对）；
      2. 全文引用的每个 7 位码必须能在 §6.6 里找到（引用了不存在的码是高频错）；
      3. §6.6 定义的码如果附录 C 没收录，也报出来（索引不全）。
    """
    findings = []  # type: List[Finding]
    for sub in sorted(designs):
        path = designs[sub]
        text = read_text(path)
        plain = strip_fences(text)

        s66, blob66 = section_slice(plain, r"^###\s+6\.6\b", r"^#{2,3}\s+")
        if not blob66:
            continue  # §6.6 还没写，跳过
        authoritative = {}  # type: Dict[str, Tuple[int, str]]
        for offset, line in enumerate(blob66.splitlines()):
            parsed = parse_code_row(line)
            if parsed:
                authoritative[parsed[0]] = (s66 + offset, parsed[1])
        if not authoritative:
            continue

        # --- 附录 C ---
        sa, blob_a = section_slice(
            plain, r"^##\s+附录\s*C\b", r"^##\s+(附录\s*D|7\.)"
        )
        # 附录 C 有两种写法：逐码清单（可比对）与号段/分类摘要（无可比对象）。
        # 摘要式附录 C 只说明「号段怎么分」，本来就不逐码列出，
        # 拿它跟 §6.6 做集合比对会成批误报（01 的附录 C 就是号段摘要）。
        # 判据：附录 C 里解析出的逐码行数 ≥ §6.6 码数的 80% 才认为它是「清单式」。
        appendix_codes = []  # type: List[Tuple[int, str, str]]
        if blob_a:
            for offset, line in enumerate(blob_a.splitlines()):
                parsed = parse_code_row(line)
                if parsed:
                    appendix_codes.append((offset, parsed[0], parsed[1]))
        is_code_listing = len(appendix_codes) >= len(authoritative) * 0.8

        if blob_a and is_code_listing:
            seen_in_appendix = set()  # type: Set[str]
            for offset, code, meaning in appendix_codes:
                seen_in_appendix.add(code)
                if code not in authoritative:
                    findings.append(
                        Finding(
                            "C-02",
                            path.name,
                            sa + offset,
                            "附录 C 收录了一个 §6.6 里不存在的错误码",
                            "附录 C: {} = {}".format(code, meaning),
                            "§6.6 权威表中共 {} 个码，无此码".format(
                                len(authoritative)
                            ),
                        )
                    )
                elif meaning != authoritative[code][1]:
                    findings.append(
                        Finding(
                            "C-02",
                            path.name,
                            sa + offset,
                            "附录 C 与 §6.6 对同一错误码的含义不一致",
                            "附录 C: {}".format(meaning),
                            "§6.6:{} {}".format(
                                authoritative[code][0], authoritative[code][1]
                            ),
                        )
                    )
            for code in sorted(set(authoritative) - seen_in_appendix):
                findings.append(
                    Finding(
                        "C-02",
                        path.name,
                        authoritative[code][0],
                        "§6.6 定义了该错误码，但附录 C 未收录（索引不全）",
                        "§6.6: {}".format(code),
                        "附录 C 未收录",
                    )
                )

        # --- 正文引用 ---（只扫剥掉围栏后的正文，避免示例 JSON 里的码被误判）
        for i, line in enumerate(plain.splitlines(), 1):
            if parse_code_row(line):
                continue  # 表格里的码由上面两张表负责
            if _is_range_bounds_line(line):
                continue  # 号段边界描述，不是真实错误码引用
            for m in CODE76_QUOTED.finditer(line):
                code = m.group(1)
                if code not in authoritative:
                    findings.append(
                        Finding(
                            "C-02",
                            path.name,
                            i,
                            "正文引用了 §6.6 里不存在的错误码",
                            "正文引用: \"{}\"".format(code),
                            "§6.6 权威表 {} 个码里没有它".format(
                                len(authoritative)
                            ),
                        )
                    )
    return findings


# --------------------------------------------------------------------------
# C-03 接口编号：§6.1 总览 == §6.3 详述标题 == 附录（接口清单）
# --------------------------------------------------------------------------

API_ROW = re.compile(r"^\|\s*\**\s*(API-\d+)\s*\**\s*\|")
API_HEADING = re.compile(r"^####\s+(API-\d+)")


def check_c03_api_sets(root, designs, structs):
    # type: (Path, Dict[str, Path], Dict[str, Path]) -> List[Finding]
    """C-03 接口编号三处一致：§6.1 总览 == §6.3 详述 == 附录里的接口表。

    M20-07 就栽在这里：附录按印象填，与总览、详述的编号集合全错位。
    校验器只检查「1..N 连续」，不检查附录里写的是不是同一批。
    """
    findings = []  # type: List[Finding]
    for sub in sorted(designs):
        path = designs[sub]
        plain = strip_fences(read_text(path))

        s61, blob61 = section_slice(plain, r"^###\s+6\.1\b", r"^###\s+6\.2\b")
        if not blob61:
            continue
        overview = {}  # type: Dict[str, int]
        for offset, line in enumerate(blob61.splitlines()):
            m = API_ROW.match(line)
            if m:
                overview.setdefault(m.group(1), s61 + offset)
        if not overview:
            continue

        # --- §6.3 详述标题 ---
        detailed = {}  # type: Dict[str, int]
        for i, line in enumerate(plain.splitlines(), 1):
            m = API_HEADING.match(line)
            if m:
                detailed.setdefault(m.group(1), i)

        for api in sorted(set(overview) - set(detailed), key=_api_key):
            findings.append(
                Finding(
                    "C-03",
                    path.name,
                    overview[api],
                    "§6.1 总览列了该接口，但 §6.3 没有对应的 `#### {}` 详述".format(api),
                    "§6.1 总览有 {}".format(api),
                    "全文 `#### API-` 标题 {} 个，无此项".format(len(detailed)),
                )
            )
        for api in sorted(set(detailed) - set(overview), key=_api_key):
            findings.append(
                Finding(
                    "C-03",
                    path.name,
                    detailed[api],
                    "§6.3 详述了该接口，但 §6.1 总览没有列",
                    "§6.3 标题 {} 在第 {} 行".format(api, detailed[api]),
                    "§6.1 总览 {} 个编号里没有它".format(len(overview)),
                )
            )

        # --- 附录里的接口表（A/B/D 任一含 `| API-xx |` 行的附录）---
        appendix_rows = {}  # type: Dict[str, Tuple[int, str]]
        for m in re.finditer(r"(?m)^##\s+附录\s+([A-F])\b.*$", plain):
            letter = m.group(1)
            start = m.start()
            nxt = re.search(r"(?m)^##\s+(?:附录\s+[A-F]\b|\S)", plain[start + 1:])
            end = start + 1 + (nxt.start() if nxt else len(plain) - start - 1)
            blob = plain[start:end]
            if "| API" not in blob:
                continue
            base_line = plain[:start].count("\n") + 1
            for offset, line in enumerate(blob.splitlines()):
                if not re.match(r"^\|\s*API-\d+", line):
                    continue
                for am in re.finditer(r"API-\d+", line):
                    appendix_rows.setdefault(am.group(0), (base_line + offset, letter))

        for api in sorted(set(appendix_rows) - set(overview), key=_api_key):
            line_no, letter = appendix_rows[api]
            findings.append(
                Finding(
                    "C-03",
                    path.name,
                    line_no,
                    "附录 {} 里出现了 §6.1 总览没有的接口编号".format(letter),
                    "附录 {} 第 {} 行写 {}".format(letter, line_no, api),
                    "§6.1 总览共 {} 个编号: {}".format(
                        len(overview), _api_range(overview)
                    ),
                )
            )
    return findings


def _api_key(name):
    # type: (str) -> int
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else 0


def _api_range(names):
    # type: (Dict[str, int]) -> str
    nums = sorted(_api_key(n) for n in names)
    if not nums:
        return "（空）"
    return "API-{:02d}..API-{:02d}".format(nums[0], nums[-1])


# --------------------------------------------------------------------------
# C-04 目录条目 vs 正文实际标题
# --------------------------------------------------------------------------


def _norm_title(s):
    # type: (str) -> str
    """归一化标题：去掉编号、标点、空白，用于比较名称部分。"""
    s = re.sub(r"^\s*(第\s*)?\d+(\.\d+)*\s*(章|节)?\s*[.．、:：]?\s*", "", s.strip())
    s = re.sub(r"^[A-F]\s*[.．、:：]?\s*", "", s)
    s = re.sub(r"[\s　`*_—\-、，,。.()（）【】\[\]:：]", "", s)
    return s


def check_c04_toc(root, designs, structs):
    # type: (Path, Dict[str, Path], Dict[str, Path]) -> List[Finding]
    """C-04 目录里的章级条目 vs 正文里真实的 `## N. 标题`。

    `validate_m20.py` 的 `check_toc` 现在只兜附录 A~F，**不兜章节**。
    目录写「第 6 章 接口设计」，正文必须有 `## 6. 接口设计`。
    名称允许前缀关系（目录可以省字），但不能完全不同。
    """
    findings = []  # type: List[Finding]
    for sub in sorted(designs):
        path = designs[sub]
        plain = strip_fences(read_text(path))
        if not re.search(r"(?m)^##\s+目录", plain):
            continue
        s_toc, blob = section_slice(plain, r"^##\s+目录", r"^#{2,3}\s+")
        if not blob:
            continue

        # 正文的 `## N. 标题`（只取章级）
        chapters = {}  # type: Dict[int, Tuple[int, str]]
        for i, line in enumerate(plain.splitlines(), 1):
            m = re.match(r"^##\s+(\d+)\.\s*(.+?)\s*$", line)
            if m:
                chapters[int(m.group(1))] = (i, m.group(2))

        for offset, line in enumerate(blob.splitlines()):
            m = re.match(r"^[-*+]\s*(\d+)\.\s+(.+?)\s*$", line)
            if not m:
                continue
            num = int(m.group(1))
            toc_name = _norm_title(m.group(2))
            line_no = s_toc + offset
            if num not in chapters:
                findings.append(
                    Finding(
                        "C-04",
                        path.name,
                        line_no,
                        "目录列了第 {} 章，正文没有 `## {}. ` 这一章".format(num, num),
                        "目录: 第 {} 章 {}".format(num, m.group(2).strip()),
                        "正文 `## N.` 章级标题: {}".format(
                            ", ".join(str(k) for k in sorted(chapters))
                        ),
                    )
                )
                continue
            real_no, real_name = chapters[num]
            real_norm = _norm_title(real_name)
            if toc_name and real_norm and not (
                toc_name.startswith(real_norm) or real_norm.startswith(toc_name)
            ):
                findings.append(
                    Finding(
                        "C-04",
                        path.name,
                        line_no,
                        "目录与正文对第 {} 章的**名称**不一致".format(num),
                        "目录: {}".format(m.group(2).strip()),
                        "正文第 {} 行: `## {}. {}`".format(real_no, num, real_name),
                    )
                )
    return findings


# --------------------------------------------------------------------------
# C-05 正文里的 `§x.y` 引用是否指向存在的章节
# --------------------------------------------------------------------------

# 只匹配「裸」的 §x.y 引用（前面紧跟中英文标点/行首/空白）。
# 前面若出现「共享规范」「总纲」「§9.1 上游契约」之类的限定词，说明它指向**别的文件**，
# 不是本文档，不应该拿来跟本文档的章节号比对 —— 这是误报的最大来源。
CROSS_REF = re.compile(r"[§＃]\s*(\d+(?:\.\d+)+)")

# 引用之前 30 个字符里出现这些词，就认为指向其他文件
OTHER_FILE_MARKERS = (
    "共享规范",
    "总纲",
    "汇总",
    "数据结构",
    "详细设计",
    "M20-0",
    "M01",
    "M02",
    "M03",
    "M04",
    "M05",
    "M06",
    "M07",
    "M08",
    "M09",
    "M10",
    "M11",
    "M12",
    "M13",
    "M14",
    "M15",
    "M16",
    "M17",
    "M18",
    "M19",
    "M21",
    "M22",
)


def _refers_other_file(line, pos):
    # type: (str, int) -> bool
    """判断这个 §x.y 引用是否指向别的文件。

    「详见共享规范 §2.5」里的 §2.5 是共享规范的第二章第五节，
    拿它去本文档里找 `### 2.5` 必然找不到 —— 这不是错误，是引用别的文件。
    不做这个区分，C-05 会成批误报（实测第一名误报源）。

    另一个高频误报源：**表格行**。详细设计第 4 章的「表清单速览」表里
    第三列就是「§4.4」这种指向本子模块数据结构文件的章节号，
    那张表本来就是在说「这张表定义在数据结构文件的 §4.4」，
    不是「本文档有 §4.4」。所以**表格行整体跳过**。
    """
    window = line[max(0, pos - 40):pos]
    if any(marker in window for marker in OTHER_FILE_MARKERS):
        return True
    if line.lstrip().startswith("|"):
        return True  # 表格内的章节号一律不查
    return False


def check_c05_section_refs(root, designs, structs):
    # type: (Path, Dict[str, Path], Dict[str, Path]) -> List[Finding]
    """C-05 正文里「见 §10.6」这类引用，目标章节是否真的存在。

    这是**永远不会被任何格式检查发现**的一类错误：指向不存在的章节
    和指向存在的章节，长得一模一样。只有拿编号去被引用文件里找一遍才行。

    只检查不带文件名的裸 `§x.y` 引用（指向本文件）。带文件名的跨文件引用
    措辞多变，做不准，宁可不做。
    """
    findings = []  # type: List[Finding]
    for sub in sorted(set(designs) | set(structs)):
        for path in (designs.get(sub), structs.get(sub)):
            if path is None:
                continue
            plain = strip_fences(read_text(path))
            lines = plain.splitlines()

            # 统计全文出现过的章节号（`## 3.4`、`### 3.4` 都接受）
            present = set()  # type: Set[str]
            for line in lines:
                m = re.match(r"^#{2,4}\s+(\d+(?:\.\d+)+)\b", line)
                if m:
                    present.add(m.group(1))
                m = re.match(r"^##\s+(\d+)\.\s", line)
                if m:
                    present.add(m.group(1))

            seen = set()  # type: Set[Tuple[int, str]]
            for i, line in enumerate(lines, 1):
                for m in CROSS_REF.finditer(line):
                    ref = m.group(1)
                    if _refers_other_file(line, m.start()):
                        continue
                    # 只看一级/二级编号（像 3.4 / 10.6），忽略 2026.11 这种日期
                    head = ref.split(".")[0]
                    if len(head) > 2 or int(head) > 20:
                        continue
                    if ref in present:
                        continue
                    if (i, ref) in seen:
                        continue
                    seen.add((i, ref))
                    findings.append(
                        Finding(
                            "C-05",
                            path.name,
                            i,
                            "正文引用了本文档里不存在的章节 §{}".format(ref),
                            "第 {} 行: {}".format(i, line.strip()[:90]),
                            "本文档 `## N.` / `### N.M` 标题里没有 {}".format(ref),
                        )
                    )
    return findings


# --------------------------------------------------------------------------
# 主流程
# --------------------------------------------------------------------------


def main(argv):
    # type: (List[str]) -> int
    if len(argv) < 2:
        sys.stderr.write(
            "用法: python3 check_consistency.py <M20目录> [--verbose]\n"
        )
        return 2
    root = Path(argv[1])
    verbose = "--verbose" in argv
    if not root.is_dir():
        sys.stderr.write("目录不存在: {}\n".format(root))
        return 2

    designs, structs, summary = collect(root)
    total_files = len(designs) + len(structs) + (1 if summary.exists() else 0)
    print(
        "跨文件一致性检查：详细设计 {} 个 / 数据结构 {} 个 / 汇总 {}，共 {} 个文件".format(
            len(designs), len(structs), 1 if summary.exists() else 0, total_files
        )
    )

    checks = [
        ("C-01", "表集合：数据结构 §4.x vs 详细设计第 4 章 vs 汇总 §1.1", 
         lambda: check_c01_table_sets(root, designs, structs, summary)),
        ("C-02", "错误码：§6.6 权威表 vs 附录 C vs 正文引用",
         lambda: check_c02_errcodes(root, designs, structs)),
        ("C-03", "接口编号：§6.1 总览 vs §6.3 详述 vs 附录接口表",
         lambda: check_c03_api_sets(root, designs, structs)),
        ("C-04", "目录章级条目 vs 正文 `## N.` 实际标题",
         lambda: check_c04_toc(root, designs, structs)),
        ("C-05", "正文 §x.y 引用是否指向存在的章节",
         lambda: check_c05_section_refs(root, designs, structs)),
    ]

    findings = []  # type: List[Finding]
    print("")
    for code, title, fn in checks:
        got = fn()
        findings.extend(got)
        status = "✓" if not got else "✗ {} 条".format(len(got))
        print("  {} {:<6} {}".format(status, code, title))
        if verbose and not got:
            print("         （无问题）")

    print("")
    if findings:
        for f in findings:
            print(f.render())
            print("")
        print("✗ 发现 {} 条不一致".format(len(findings)))
        return 1
    print("✓ 五类检查全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
