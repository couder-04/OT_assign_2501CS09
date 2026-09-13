"""Build OT_Assignment_Report.pdf  (theory + code screenshots + program output)."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT_PDF = ROOT / "OT_Assignment_Report.pdf"

DPI = 150
W = int(8.27 * DPI)   # A4
H = int(11.69 * DPI)
MARGIN = 70
NAVY = (20, 45, 85)
NAVY2 = (32, 67, 120)
GOLD = (196, 149, 58)
INK = (28, 32, 38)
MUTED = (90, 96, 108)
RULE = (210, 216, 224)
WHITE = (255, 255, 255)
CODE_BG = (30, 30, 30)
CODE_FG = (212, 212, 212)
CODE_LN = (110, 110, 110)
CODE_CMT = (106, 153, 85)
CODE_KW = (86, 156, 214)
CODE_STR = (206, 145, 120)
TERM_BG = (12, 16, 22)
TERM_FG = (210, 232, 210)
TERM_DIM = (120, 160, 120)
RED, YEL, GRN = (255, 95, 86), (255, 189, 46), (39, 201, 63)

KEYWORDS = {
    "def", "class", "return", "if", "else", "elif", "for", "while", "in", "and",
    "or", "not", "import", "from", "as", "None", "True", "False", "with", "try",
    "except", "raise", "assert", "pass", "break", "continue", "lambda", "yield",
    "is", "None", "async", "await", "global", "nonlocal",
}

FONT_SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_SANS_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_MONO = "/System/Library/Fonts/Supplemental/Courier New.ttf"
FONT_MONO_B = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


F_TITLE = font(FONT_SANS_B, 34)
F_H1 = font(FONT_SANS_B, 22)
F_H2 = font(FONT_SANS_B, 16)
F_BODY = font(FONT_SANS, 14)
F_SMALL = font(FONT_SANS, 11)
F_CODE = font(FONT_MONO, 11)
F_CODE_SM = font(FONT_MONO, 10)
F_WIN = font(FONT_SANS, 12)
F_WIN_B = font(FONT_SANS_B, 12)


def new_page() -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, W, 14), fill=NAVY)
    return im, dr


def footer(dr: ImageDraw.ImageDraw, page: int, total: int) -> None:
    dr.rectangle((0, H - 42, W, H), fill=NAVY)
    dr.text((MARGIN, H - 30), "Optimization Techniques  |  Big-M  +  Transportation (VAM / MODI)", font=F_SMALL, fill=WHITE)
    label = f"{page}"
    tw = dr.textlength(label, font=F_SMALL)
    dr.text((W - MARGIN - tw, H - 30), label, font=F_SMALL, fill=WHITE)


def wrap(dr: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> List[str]:
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for w in words[1:]:
        trial = cur + " " + w
        if dr.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def heading_bar(dr, y: int, title: str) -> int:
    dr.rectangle((MARGIN, y, W - MARGIN, y + 40), fill=NAVY)
    dr.text((MARGIN + 14, y + 10), title, font=F_H2, fill=WHITE)
    return y + 56


def section_label(dr, y: int, text: str) -> int:
    dr.text((MARGIN, y), text, font=F_H2, fill=NAVY)
    y += 26
    dr.line((MARGIN, y, W - MARGIN, y), fill=GOLD, width=3)
    return y + 16


def body(dr, y: int, paragraphs: Sequence[str], indent: int = 0) -> int:
    max_w = W - 2 * MARGIN - indent
    for para in paragraphs:
        if para == "":
            y += 8
            continue
        if para.startswith("• "):
            for line in wrap(dr, para, F_BODY, max_w - 12):
                dr.text((MARGIN + indent, y), line, font=F_BODY, fill=INK)
                y += 20
            y += 4
            continue
        for line in wrap(dr, para, F_BODY, max_w):
            dr.text((MARGIN + indent, y), line, font=F_BODY, fill=INK)
            y += 20
        y += 8
    return y


def table(dr, y: int, headers: Sequence[str], rows: Sequence[Sequence[str]], col_w: Sequence[int]) -> int:
    x0 = MARGIN
    row_h = 26
    dr.rectangle((x0, y, x0 + sum(col_w), y + row_h), fill=NAVY)
    x = x0
    for h, w in zip(headers, col_w):
        dr.text((x + 8, y + 6), h, font=F_SMALL, fill=WHITE)
        x += w
    y += row_h
    for i, row in enumerate(rows):
        bg = (244, 247, 251) if i % 2 == 0 else WHITE
        dr.rectangle((x0, y, x0 + sum(col_w), y + row_h), fill=bg)
        dr.rectangle((x0, y, x0 + sum(col_w), y + row_h), outline=RULE)
        x = x0
        for cell, w in zip(row, col_w):
            dr.text((x + 8, y + 6), str(cell), font=F_SMALL, fill=INK)
            x += w
        y += row_h
    return y + 14


def window_chrome(dr, y: int, w: int, h: int, title: str, dark: bool) -> None:
    bar_h = 28
    bg = CODE_BG if dark else TERM_BG
    dr.rounded_rectangle((MARGIN, y, MARGIN + w, y + h), radius=10, fill=bg)
    dr.rounded_rectangle((MARGIN, y, MARGIN + w, y + bar_h), radius=10, fill=(45, 45, 48) if dark else (28, 34, 42))
    dr.rectangle((MARGIN, y + 14, MARGIN + w, y + bar_h), fill=(45, 45, 48) if dark else (28, 34, 42))
    for i, col in enumerate((RED, YEL, GRN)):
        dr.ellipse((MARGIN + 12 + i * 16, y + 8, MARGIN + 22 + i * 16, y + 18), fill=col)
    dr.text((MARGIN + 70, y + 7), title, font=F_WIN, fill=(220, 220, 220))


def paint_code_block(page_dr, origin_y: int, lines: Sequence[str], start_no: int, title: str) -> int:
    """Draw a code screenshot; returns bottom y."""
    inner_w = W - 2 * MARGIN
    line_h = 15
    bar_h = 28
    pad = 10
    n = len(lines)
    box_h = bar_h + pad + n * line_h + pad
    window_chrome(page_dr, origin_y, inner_w, box_h, title, dark=True)
    y = origin_y + bar_h + pad
    ln_w = 42
    for i, raw in enumerate(lines):
        no = start_no + i
        page_dr.text((MARGIN + 12, y), f"{no:4d}", font=F_CODE_SM, fill=CODE_LN)
        draw_python_line(page_dr, MARGIN + 12 + ln_w, y, raw.rstrip("\n"))
        y += line_h
    return origin_y + box_h


def draw_python_line(dr, x: int, y: int, line: str) -> None:
    stripped = line.lstrip()
    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
        dr.text((x, y), line, font=F_CODE_SM, fill=CODE_CMT)
        return
    # crude highlighter
    i = 0
    while i < len(line):
        ch = line[i]
        if ch in "\"'":
            q = ch
            j = i + 1
            while j < len(line) and line[j] != q:
                if line[j] == "\\" and j + 1 < len(line):
                    j += 2
                    continue
                j += 1
            j = min(j + 1, len(line))
            tok = line[i:j]
            dr.text((x, y), tok, font=F_CODE_SM, fill=CODE_STR)
            x += dr.textlength(tok, font=F_CODE_SM)
            i = j
            continue
        if ch == "#" and (i == 0 or line[i - 1].isspace()):
            tok = line[i:]
            dr.text((x, y), tok, font=F_CODE_SM, fill=CODE_CMT)
            return
        if ch.isalnum() or ch == "_":
            j = i + 1
            while j < len(line) and (line[j].isalnum() or line[j] == "_"):
                j += 1
            tok = line[i:j]
            col = CODE_KW if tok in KEYWORDS else CODE_FG
            dr.text((x, y), tok, font=F_CODE_SM, fill=col)
            x += dr.textlength(tok, font=F_CODE_SM)
            i = j
            continue
        dr.text((x, y), ch, font=F_CODE_SM, fill=CODE_FG)
        x += dr.textlength(ch, font=F_CODE_SM)
        i += 1


def paint_term_block(page_dr, origin_y: int, lines: Sequence[str], title: str) -> int:
    inner_w = W - 2 * MARGIN
    line_h = 14
    bar_h = 28
    pad = 10
    n = len(lines)
    box_h = bar_h + pad + n * line_h + pad
    window_chrome(page_dr, origin_y, inner_w, box_h, title, dark=False)
    y = origin_y + bar_h + pad
    for raw in lines:
        page_dr.text((MARGIN + 14, y), raw.rstrip("\n")[:108], font=F_CODE_SM, fill=TERM_FG)
        y += line_h
    return origin_y + box_h


def chunk(seq: Sequence[str], n: int) -> List[List[str]]:
    return [list(seq[i:i + n]) for i in range(0, len(seq), n)]


def add_code_pages(pages: List, source: Path, title: str, cmd_note: str) -> None:
    text = source.read_text().splitlines()
    # keep a little headroom for heading + chrome
    per = 62
    chunks = chunk(text, per)
    start = 1
    for ci, part in enumerate(chunks):
        im, dr = new_page()
        y = 36
        if ci == 0:
            y = section_label(dr, y, title)
            y = body(dr, y, [cmd_note])
        else:
            y = section_label(dr, y, f"{title}  (continued)")
        paint_code_block(dr, y, part, start, f"{source.name}  —  Python source")
        pages.append(im)
        start += len(part)


def add_output_pages(pages: List, output: Path, title: str, term_title: str) -> None:
    lines = output.read_text().splitlines()
    if lines and lines[0] == "":
        lines = lines[1:]
    per = 64
    chunks = chunk(lines, per)
    for ci, part in enumerate(chunks):
        im, dr = new_page()
        y = 36
        lab = title if ci == 0 else f"{title}  (continued)"
        y = section_label(dr, y, lab)
        if ci == 0:
            y = body(dr, y, ["Captured terminal output of the program (screenshot-style)."])
        paint_term_block(dr, y, part, term_title)
        pages.append(im)


def cover() -> Image.Image:
    im = Image.new("RGB", (W, H), WHITE)
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, W, 260), fill=NAVY)
    dr.rectangle((0, 260, W, 268), fill=GOLD)
    dr.text((MARGIN, 70), "OPTIMIZATION TECHNIQUES", font=F_H2, fill=GOLD)
    dr.text((MARGIN, 108), "Assignment Report", font=F_TITLE, fill=WHITE)
    dr.text((MARGIN, 160), "Big-M Simplex Method", font=F_H1, fill=WHITE)
    dr.text((MARGIN, 192), "Transportation Problem  —  VAM and MODI", font=F_H1, fill=WHITE)

    y = 320
    y = section_label(dr, y, "Computational solutions (Python 3)")
    y = body(dr, y, [
        "This report solves two well-known constrained optimization problems computationally. Each method is implemented from first principles (no NumPy / SciPy solver). The submitted PDF includes the Python source and the corresponding program output for Big-M, Vogel's Approximation Method (VAM), and the Modified Distribution (MODI) method.",
        "",
        "Part 1.  Big-M Method.  A mixed-constraint linear program is converted to standard form with slack, surplus and artificial variables, then solved by Big-M simplex. Exact a + bM arithmetic is used throughout.",
        "",
        "Part 2.  Transportation Problem.  A balanced 3-factory / 4-warehouse problem is solved in two stages, one method at a time: (i) VAM constructs an initial basic feasible solution; (ii) MODI tests optimality and improves the allocation until every opportunity cost is non-negative.",
    ])
    y += 10
    y = table(
        dr, y,
        ["Part", "Method", "Program", "Result"],
        [
            ["1", "Big-M simplex", "big_m_method.py", "Z* = 17/5 = 3.4"],
            ["2(i)", "VAM  (IBFS)", "transportation.py --method vam", "cost = 779"],
            ["2(ii)", "MODI  (optimal)", "transportation.py --method modi", "Z* = 743"],
        ],
        [90, 210, 420, 180],
    )
    y += 8
    y = body(dr, y, [
        "How to reproduce:",
        "python3 big_m_method.py",
        "python3 transportation.py --method vam",
        "python3 transportation.py --method modi",
    ])
    dr.rectangle((0, H - 70, W, H), fill=NAVY)
    dr.text((MARGIN, H - 48), "Python 3  |  standard library only", font=F_SMALL, fill=WHITE)
    return im


def page_bigm_theory() -> Image.Image:
    im, dr = new_page()
    y = 36
    y = section_label(dr, y, "Part 1  —  Big-M Simplex Method")
    y = body(dr, y, [
        "Ordinary simplex needs an initial basic feasible solution. That is immediate when every constraint is of type <= (slack variables form the basis). Equality and >= constraints require artificial variables. Big-M places a huge penalty M on each artificial in the objective so simplex drives them to zero whenever the LPP is feasible.",
        "If an artificial remains positive at termination, the original LPP is infeasible.",
    ])
    y = heading_bar(dr, y, "Selected LPP  (Taha / Winston mixed-constraint example)")
    y = body(dr, y, [
        "Minimize   Z = 4 x1 + x2",
        "subject to     3 x1 + x2  =  3",
        "               4 x1 + 3 x2  >=  6",
        "               x1 + 2 x2  <=  4",
        "               x1, x2  >=  0",
        "All three constraint types appear, so slack, surplus and artificial variables are required.",
    ])
    y = heading_bar(dr, y, "Standard form")
    y = body(dr, y, [
        "3 x1 + x2 + a1  =  3",
        "4 x1 + 3 x2 - p1 + a2  =  6",
        "x1 + 2 x2 + s1  =  4",
        "Z  =  4 x1 + x2 + M (a1 + a2)     (minimization: artificials are expensive)",
        "Initial basis: {a1, a2, s1}.  The program stores every tableau entry as a + bM using exact fractions.",
    ])
    y = heading_bar(dr, y, "Simplex rules used")
    y = body(dr, y, [
        "1. Convert to standard form; put artificials / slacks in the basis.",
        "2. Compute reduced costs  cj - zj  after eliminating basic variables from Z.",
        "3. MIN optimality test: stop when every  cj - zj  >= 0.",
        "4. Entering variable: most negative  cj - zj.",
        "5. Leaving variable: minimum-ratio test (smallest non-negative RHS / pivot column).",
        "6. Pivot and repeat.",
    ])
    return im


def page_bigm_result() -> Image.Image:
    im, dr = new_page()
    y = 36
    y = section_label(dr, y, "Part 1  —  Iterations and optimal solution")
    y = table(
        dr, y,
        ["Iter.", "Basis", "Z", "Enter", "Leave"],
        [
            ["0", "a1, a2, s1", "9M", "x1  (4-7M)", "a1"],
            ["1", "x1, a2, s1", "4+2M", "x2  (-1/3-5/3 M)", "a2"],
            ["2", "x1, x2, s1", "18/5", "p1  (-1/5)", "s1"],
            ["3", "x1, x2, p1", "17/5", "—  optimal", "—"],
        ],
        [80, 180, 140, 250, 120],
    )
    y = body(dr, y, ["Both artificials have left the basis, so the solution is feasible for the original LPP."])
    y = heading_bar(dr, y, "Optimal solution")
    y = table(
        dr, y,
        ["Variable", "Value", "Comment"],
        [
            ["x1*", "2/5 = 0.4", "decision"],
            ["x2*", "9/5 = 1.8", "decision"],
            ["p1", "1", "surplus on the >= constraint"],
            ["s1, a1, a2", "0", "artificials must be zero"],
            ["Z*", "17/5 = 3.4", "minimum cost"],
        ],
        [180, 200, 420],
    )
    y = heading_bar(dr, y, "Verification")
    y = body(dr, y, [
        "3(0.4) + 1.8 = 3",
        "4(0.4) + 3(1.8) = 7  >=  6",
        "0.4 + 2(1.8) = 4",
        "Z = 4(0.4) + 1.8 = 3.4",
        "The next pages are screenshots of big_m_method.py and of the terminal output produced by:  python3 big_m_method.py",
    ])
    return im


def page_tp_theory() -> Image.Image:
    im, dr = new_page()
    y = 36
    y = section_label(dr, y, "Part 2  —  Transportation Problem (TP)")
    y = body(dr, y, [
        "A transportation problem ships a homogeneous product from m sources (capacities ai) to n destinations (demands bj) at unit cost cij. Minimize the total shipping cost subject to supply and demand equalities, xij >= 0.",
        "The problem is balanced when total supply equals total demand. A basic feasible solution occupies m + n - 1 independent cells.",
        "The two methods are applied one at a time: VAM builds an initial basic feasible solution; MODI tests optimality and improves the plan.",
    ])
    y = heading_bar(dr, y, "Selected problem  (3 factories, 4 warehouses)")
    y = table(
        dr, y,
        ["", "W1", "W2", "W3", "W4", "Supply"],
        [
            ["F1", "19", "30", "50", "10", "7"],
            ["F2", "70", "30", "40", "60", "9"],
            ["F3", "40", "8", "70", "20", "18"],
            ["Demand", "5", "8", "7", "14", "34 = 34"],
        ],
        [120, 100, 100, 100, 100, 140],
    )
    y = body(dr, y, ["Balanced. Need 3+4-1 = 6 basic cells. Objective: minimize total transportation cost."])
    y = heading_bar(dr, y, "(i) Vogel's Approximation Method (VAM)")
    y = body(dr, y, [
        "Penalty of a row or column = (second-smallest cost) - (smallest cost) among remaining cells. A large penalty means that skipping the cheapest cell in that line is expensive.",
        "At each step: compute penalties; pick the largest; allocate as much as possible to that line's cheapest cell; cross out the exhausted row or column; repeat.",
    ])
    return im


def page_tp_vam_result() -> Image.Image:
    im, dr = new_page()
    y = 36
    y = section_label(dr, y, "Part 2(i)  —  VAM initial solution")
    y = table(
        dr, y,
        ["Step", "Max penalty", "Cell", "Qty", "Cross out"],
        [
            ["1", "col W2 = 22", "F3 -> W2", "8", "W2"],
            ["2", "col W1 = 21", "F1 -> W1", "5", "W1"],
            ["3", "row F3 = 50", "F3 -> W4", "10", "F3"],
            ["4", "col W4 = 50", "F1 -> W4", "2", "F1"],
            ["5", "col W4 = 60", "F2 -> W4", "2", "W4"],
            ["final", "—", "F2 -> W3", "7", "—"],
        ],
        [90, 200, 180, 90, 140],
    )
    y = heading_bar(dr, y, "IBFS  (6 basic cells)   cost = 779")
    y = table(
        dr, y,
        ["", "W1", "W2", "W3", "W4"],
        [
            ["F1", "5", "—", "—", "2"],
            ["F2", "—", "—", "7", "2"],
            ["F3", "—", "8", "—", "10"],
        ],
        [80, 120, 120, 120, 120],
    )
    y = body(dr, y, [
        "Z_VAM = 5*19 + 2*10 + 7*40 + 2*60 + 8*8 + 10*20 = 779",
        "This IBFS is not guaranteed optimal. MODI (next) tests and improves it.",
        "Command:  python3 transportation.py --method vam",
    ])
    return im


def page_tp_modi_result() -> Image.Image:
    im, dr = new_page()
    y = 36
    y = section_label(dr, y, "Part 2(ii)  —  MODI optimality and improvement")
    y = body(dr, y, [
        "For every basic cell:  ui + vj = cij   (set u1 = 0).",
        "For every non-basic cell:  dij = cij - ui - vj.",
        "A minimization problem is optimal iff every dij >= 0. If some dij < 0, enter the most negative cell, form a closed +/- loop with basic cells, and shift theta = min of the (-) allocations.",
    ])
    y = heading_bar(dr, y, "Iteration 1  (from VAM)")
    y = body(dr, y, [
        "Duals:  u = (0, 50, 10),   v = (19, -2, -10, 10).",
        "Most negative opportunity cost:  d(F2, W2) = -18.",
        "Closed loop:  (F2,W2)+  ->  (F2,W4)-  ->  (F3,W4)+  ->  (F3,W2)-",
        "theta = min(2, 8) = 2.   New cost = 779 - 18*2 = 743.",
    ])
    y = heading_bar(dr, y, "Iteration 2  —  all dij >= 0, optimal")
    y = table(
        dr, y,
        ["", "W1", "W2", "W3", "W4", "Supply"],
        [
            ["F1", "5", "—", "—", "2", "7"],
            ["F2", "—", "2", "7", "—", "9"],
            ["F3", "—", "6", "—", "12", "18"],
            ["Demand", "5", "8", "7", "14", "34"],
        ],
        [100, 90, 90, 90, 90, 120],
    )
    y = table(
        dr, y,
        ["Route", "Units", "Unit cost", "Contribution"],
        [
            ["F1 -> W1", "5", "19", "95"],
            ["F1 -> W4", "2", "10", "20"],
            ["F2 -> W2", "2", "30", "60"],
            ["F2 -> W3", "7", "40", "280"],
            ["F3 -> W2", "6", "8", "48"],
            ["F3 -> W4", "12", "20", "240"],
            ["Total Z*", "", "", "743"],
        ],
        [200, 120, 160, 180],
    )
    y = body(dr, y, ["Command:  python3 transportation.py --method modi"])
    return im


def extract_modi_output() -> Path:
    """Write a MODI-only output file so the screenshot matches that method."""
    raw = (ROOT / "outputs" / "modi_output.txt").read_text().splitlines()
    # keep problem header + VAM IBFS summary is useful, but assignment asks MODI output.
    # Start at the MODI banner; prepend a one-line note.
    idx = next(i for i, ln in enumerate(raw) if "MODI METHOD" in ln)
    lines = [
        "ASSIGNMENT  —  MODI METHOD  (starts from the VAM IBFS of cost 779)",
        "",
        *raw[idx:],
    ]
    path = ROOT / "outputs" / "modi_only_output.txt"
    path.write_text("\n".join(lines) + "\n")
    return path


def main() -> None:
    pages: List[Image.Image] = []
    pages.append(cover())
    pages.append(page_bigm_theory())
    pages.append(page_bigm_result())
    add_code_pages(
        pages,
        ROOT / "big_m_method.py",
        "Screenshot  —  Big-M Python code",
        "Source file big_m_method.py  (run with:  python3 big_m_method.py)",
    )
    add_output_pages(
        pages,
        ROOT / "outputs" / "big_m_output.txt",
        "Screenshot  —  Big-M program output",
        "Terminal  —  python3 big_m_method.py",
    )
    pages.append(page_tp_theory())
    pages.append(page_tp_vam_result())
    add_code_pages(
        pages,
        ROOT / "transportation.py",
        "Screenshot  —  Transportation Python code  (VAM + MODI)",
        "Source file transportation.py.  VAM: function vam().  MODI: function modi().  Run one method at a time.",
    )
    add_output_pages(
        pages,
        ROOT / "outputs" / "vam_output.txt",
        "Screenshot  —  VAM program output",
        "Terminal  —  python3 transportation.py --method vam",
    )
    modi_path = extract_modi_output()
    add_output_pages(
        pages,
        modi_path,
        "Screenshot  —  MODI program output",
        "Terminal  —  python3 transportation.py --method modi",
    )

    rgb = [p.convert("RGB") for p in pages]
    for i, im in enumerate(rgb, start=1):
        dr = ImageDraw.Draw(im)
        footer(dr, i, len(rgb))

    rgb[0].save(
        OUT_PDF,
        "PDF",
        resolution=float(DPI),
        save_all=True,
        append_images=rgb[1:],
        title="Optimization Techniques Assignment — Big-M, VAM, MODI",
        author="OT Assignment",
    )
    print(f"Wrote {OUT_PDF}  ({len(rgb)} pages, {OUT_PDF.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
