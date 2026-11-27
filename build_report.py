import copy
import subprocess
import sys
import docx
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

lab = sys.argv[1]
d = docx.Document(f"{lab}/template.docx")
body = d.element.body
els = list(body.iterchildren())
paras = {i: docx.text.paragraph.Paragraph(e, d) for i, e in enumerate(els) if e.tag.endswith("}p")}


def set_text(p, text):
    runs = p.runs
    runs[0].text = text
    for r in runs[1:]:
        r.text = ""


# ---------- Нүүр хуудас ----------
set_text(paras[3], "ЛАБОРАТОРИЙН ТАЙЛАН №12")
tbl = d.tables[0]
values = ["Хиймэл оюун", "Ухаалаг шийдвэр: MDP ба утгын давталт", "s22c021b", "Ариунбилэг"]
for row, val in zip(tbl.rows, values):
    cell = row.cells[1]
    p = cell.paragraphs[0]
    ref = row.cells[0].paragraphs[0].runs[0] if row.cells[0].paragraphs[0].runs else None
    r = p.add_run(val)
    if ref is not None:
        r.font.size = ref.font.size
        r.font.name = ref.font.name or "Times New Roman"
set_text(paras[15], "Гүйцэтгэсэн он сар өдөр：2026 он 11 сар 27 өдөр")

# Загварын тайлбар текстүүдийг устгаад "1. Зорилго" гарчгийг үлдээнэ
heading_el = els[16]
for e in els[17:]:
    if not e.tag.endswith("}sectPr"):
        body.remove(e)

FONT = "Times New Roman"


def run_fmt(r, size=12, bold=False, italic=False, mono=False):
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    name = "Courier New" if mono else FONT
    r.font.name = name
    rpr = r._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for k in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(k), name)


def para(text="", bold=False, italic=False, size=12, align=None, indent=True, after=4):
    p = d.add_paragraph(style=paras[16].style)
    if text:
        # **тод** хэсгийг дэмжинэ
        parts = text.split("**")
        for i, part in enumerate(parts):
            if part:
                run_fmt(p.add_run(part), size, bold or i % 2 == 1, italic)
    pf = p.paragraph_format
    pf.space_after = Pt(after)
    pf.space_before = Pt(0)
    pf.line_spacing = 1.15
    if indent and not bold:
        pf.first_line_indent = Cm(1)
    if align:
        p.alignment = align
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return p


def heading(text):
    p = para(text, bold=True, size=12, indent=False, after=6)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def sub(text):
    p = para(text, bold=True, size=12, indent=False, after=3)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def bullet(text):
    p = para("•  " + text, indent=False, after=2)
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    return p


def shade(el, fill):
    pr = el.get_or_add_pPr() if hasattr(el, "get_or_add_pPr") else el
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def code(text):
    for line in text.strip("\n").split("\n"):
        p = d.add_paragraph(style=paras[16].style)
        run_fmt(p.add_run(line if line else " "), size=9.5, mono=True)
        shade(p._p, "F2F2F2")  # бусад pPr тохиргооноос өмнө (schema дараалал)
        pf = p.paragraph_format
        pf.space_after = Pt(0)
        pf.space_before = Pt(0)
        pf.line_spacing = 1.0
        pf.left_indent = Cm(0.5)
        pf.keep_together = True
    d.paragraphs[-1].paragraph_format.space_after = Pt(6)


def cell_borders(table):
    tblPr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "808080")
        borders.append(b)
    succ = [c for c in tblPr if c.tag in (qn("w:shd"), qn("w:tblLayout"), qn("w:tblCellMar"), qn("w:tblLook"))]
    if succ:
        succ[0].addprevious(borders)
    else:
        tblPr.append(borders)


def table(rows, widths, header=True, center_from=1, size=10.5):
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    cell_borders(t)
    t.alignment = 1
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths[j])
            p = c.paragraphs[0]
            run_fmt(p.add_run(str(val)), size, bold=(header and i == 0))
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            if j >= center_from or (header and i == 0):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if header and i == 0:
                tcPr = c._tc.get_or_add_tcPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "D9E2F3")
                tcPr.append(shd)
    sp = d.add_paragraph(style=paras[16].style)
    sp.paragraph_format.space_after = Pt(2)
    return t


def caption(text):
    p = para(text, italic=True, size=10.5, indent=False, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    return p


def image(path, width_cm):
    p = d.add_paragraph(style=paras[16].style)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(path, width=Cm(width_cm))
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2)


# python-docx add_paragraph нь sectPr-ийн өмнө нэмнэ. "1. Зорилго" гарчиг аль хэдийн бий.
# ================= 1. Зорилго =================
para("Энэхүү лабораторийн ажлаар тодорхой бус нөхцөлд **хүлээгдэж буй ашгийг** тооцож шийдвэр "
     "гаргах, 4×3 тор ертөнцийг Марковын шийдвэрийн процесс (MDP) болгон төлөв, үйлдэл, шилжилт, "
     "шагналаар тодорхойлох, утгын давталтаар (value iteration) төлөв бүрийн утга ба хамгийн сайн "
     "бодлогыг олох зорилготой. Мөн алхмын шагнал r болон хөнгөлөлтийн коэффициент γ өөрчлөгдөхөд "
     "бодлого хэрхэн өөрчлөгдөхийг туршина.")
bullet("Хүлээгдэж буй ашгийг EU = Σ P(үр дүн) × ашиг томьёогоор тооцож, сонголтуудыг харьцуулах;")
bullet("Гулгамтгай хөдөлгөөнийг (0.8 / 0.1 / 0.1) шилжилтийн функцээр илэрхийлэх;")
bullet("Утгын давталтыг хэрэгжүүлж, утга тогтворжихыг ажиглах;")
bullet("Утгаас бодлого гаргаж сумаар дүрслэх, r ба γ-ийн нөлөөг тайлбарлах.")

# ================= 2. Онол =================
heading("2. Онол")
sub("2.1 Хүлээгдэж буй ашиг (Expected Utility)")
para("Сонголт бүрийн боломжит үр дүнгийн ашгийг тухайн үр дүнгийн магадлалаар жигнэж нэмнэ:")
para("EU(a) = Σ P(o | a) × u(o)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
para("Оновчтой (рационал) агент EU нь хамгийн их сонголтыг хийнэ.")

sub("2.2 Марковын шийдвэрийн процесс (MDP)")
para("MDP нь дараах 4 хэсгээс бүрдэнэ:")
bullet("**Төлөв S** – ханаас бусад 11 нүд (x, y). Төгсгөлийн төлөв: (4,3) = +1, (4,2) = −1;")
bullet("**Үйлдэл A** – ↑, ↓, ←, → (дээш, доош, зүүн, баруун);")
bullet("**Шилжилт P(s′ | s, a)** – үйлдлийн үр дүн санамсаргүй боловч зөвхөн одоогийн төлөвөөс хамаарна (Марковын шинж);")
bullet("**Шагнал R(s)** – төгсгөлийн бус нүд бүрт r = −0.04.")
para("**Гулгах загвар:** робот тушаасан чиглэлдээ 0.8 магадлалтай, түүний хажуугийн хоёр "
     "чиглэлд тус бүр 0.1 магадлалтай явна. Жишээ нь «дээш» үйлдлийн хажуу нь «зүүн» ба «баруун». "
     "Хана эсвэл захад мөргөвөл байрандаа үлдэнэ.")

sub("2.3 Беллманы тэгшитгэл ба бодлого")
para("Утга U(s) нь тухайн төлөвөөс эхэлбэл цаашид хүлээгдэж буй нийт шагнал юм:")
para("U(s) = R(s) + γ · max_a Σ P(s′ | s, a) · U(s′)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)
para("Утгын давталт нь бүх утгыг 0-ээр эхлүүлж, дээрх шинэчлэлийг max |U′ − U| < ε болтол давтана. "
     "Төгсгөлийн төлөвийн утга нь шагналтайгаа тэнцүү. Хамгийн сайн бодлого нь төлөв бүрт "
     "хөршийн хүлээгдэж буй утгыг хамгийн их болгох үйлдлийг сонгоно:")
para("π*(s) = argmax_a Σ P(s′ | s, a) · U(s′)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, indent=False)

# ================= 3. Аргачлал =================
heading("3. Аргачлал")
def manual_table(rows, widths, size=11):
    """Зааврын хэв маягтай хүснэгт: хар хөх толгой, цагаан тод бичиг, эхний багана тод."""
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{side}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "8EAADB")
        borders.append(b)
    succ = [c for c in tblPr if c.tag in (qn("w:shd"), qn("w:tblLayout"), qn("w:tblCellMar"), qn("w:tblLook"))]
    succ[0].addprevious(borders) if succ else tblPr.append(borders)
    t.alignment = 1
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.width = Cm(widths[j])
            p = c.paragraphs[0]
            r = p.add_run(str(val))
            run_fmt(r, size, bold=(i == 0 or j == 0))
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.first_line_indent = Cm(0)
            if i == 0:
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                tcPr = c._tc.get_or_add_tcPr()
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "1F3A93")
                tcPr.append(shd)
    sp = d.add_paragraph(style=paras[16].style)
    sp.paragraph_format.space_after = Pt(2)


manual_table([
    ["Сонголт", "Үр дүн (магадлал, ашиг)", "EU"],
    ["Шалгалтад бэлдэх", "(0.9, 80), (0.1, 10)", "73.0"],
    ["Тоглох", "(0.4, 100), (0.6, 0)", "40.0"],
    ["А: шууд мөнгө", "(1.0, 100000)", "100000.0"],
    ["Б: зоос шидэх", "(0.5, 250000), (0.5, 0)", "125000.0"],
], [5, 7, 4])

para("Кодыг Python 3 дээр Lab12_MDP.ipynb файлд алхам бүрийг тусад нь бичиж хэрэгжүүлсэн. "
     "Гол функцууд болон тайлбарыг доор оруулав.")
sub("3.1 Хүлээгдэж буй ашиг – expected_utility")
code('''
# Хүлээгдэж буй ашгийг EU = Σ P(o)·u(o) томьёогоор тооцно.
def expected_utility(outcomes):
    total = sum(p for p, _ in outcomes)
    if abs(total - 1.0) > 1e-9:          # магадлалын нийлбэр 1 эсэх
        raise ValueError(f"Магадлалын нийлбэр 1 биш: {total}")
    return sum(p * u for p, u in outcomes)
''')
para("Эхлээд магадлалын нийлбэрийг шалгаж, буруу бол ValueError өгнө. Жишээ нь "
     "[(0.5, 10), (0.4, 20)] оролтод «нийлбэр 1 биш: 0.9» гэсэн алдаа гарсан.")

sub("3.2 Тор ертөнц")
code('''
W, H = 4, 3
WALL = {(2, 2)}
TERMINALS = {(4, 3): 1.0, (4, 2): -1.0}
STATES = [(x, y) for x in range(1, W+1) for y in range(1, H+1)
          if (x, y) not in WALL]                      # 11 төлөв
ACTIONS = {"^": (0, 1), "v": (0, -1), "<": (-1, 0), ">": (1, 0)}
SIDE = {"^": ("<", ">"), "v": ("<", ">"), "<": ("^", "v"), ">": ("^", "v")}
''')

sub("3.3 Хөдөлгөөн ба шилжилт – move, trans")
code('''
# Хана эсвэл захад мөргөвөл байрандаа үлдэнэ.
def move(s, a):
    dx, dy = ACTIONS[a]
    nx, ny = s[0] + dx, s[1] + dy
    if not (1 <= nx <= W and 1 <= ny <= H) or (nx, ny) in WALL:
        return s
    return (nx, ny)

# Үндсэн чиглэл 0.8, хажуугийн хоёр чиглэл тус бүр 0.1.
def trans(s, a):
    l, r = SIDE[a]
    return [(0.8, move(s, a)), (0.1, move(s, l)), (0.1, move(s, r))]
''')
para("Шалгалт: trans((1,1), \"^\") → [(0.8, (1,2)), (0.1, (1,1)), (0.1, (2,1))]. Зүүн тийш "
     "гулсахад зах руу мөргөж (1,1)-дээ үлдэж байгаа нь зөв.")

sub("3.4 Утгын давталт – value_iteration")
code('''
def value_iteration(r=-0.04, gamma=1.0, eps=1e-6, max_iter=10000):
    U = {s: 0.0 for s in STATES}
    history = []
    for it in range(1, max_iter + 1):
        U2 = {}                                   # шинэ утгыг тусад нь
        for s in STATES:
            if s in TERMINALS:
                U2[s] = TERMINALS[s]              # төгсгөл = шагнал
            else:
                U2[s] = r + gamma * max(sum(p * U[s2] for p, s2 in trans(s, a))
                                        for a in ACTIONS)
        delta = max(abs(U2[s] - U[s]) for s in STATES)
        U = U2
        history.append(U[(1, 1)])
        if delta < eps:
            break
    return U, it, history
''')
para("Шинэ утгыг хуучин U-д шууд бичвэл нэг давталт дотор холилдож, үр дүн 0.705-аас зөрдөг тул "
     "шинэ dict U2 үүсгэж, давталтын төгсгөлд U = U2 болгосон.")

sub("3.5 Бодлого гаргах – extract_policy")
code('''
def extract_policy(U):
    return {s: max(ACTIONS, key=lambda a: sum(p * U[s2] for p, s2 in trans(s, a)))
            for s in STATES if s not in TERMINALS}    # төгсгөлийн нүдийг хасна
''')

# ================= 4. Үр дүн =================
heading("4. Үр дүн")
sub("4.1 Хүлээгдэж буй ашиг (Алхам 2)")
table([
    ["Сонголт", "Үр дүн (магадлал, ашиг)", "EU"],
    ["Шалгалтад бэлдэх", "(0.9, 80), (0.1, 10)", "73.0"],
    ["Тоглох", "(0.4, 100), (0.6, 0)", "40.0"],
    ["А: шууд мөнгө", "(1.0, 100000)", "100 000"],
    ["Б: зоос шидэх", "(0.5, 250000), (0.5, 0)", "125 000"],
], [5, 6.5, 3])
para("Эхний жишээнд «шалгалтад бэлдэх» (73 > 40) нь илүү. Хоёр дахь жишээнд EU-гээр «зоос шидэх» "
     "илүү (125 000 > 100 000) боловч бодит хүмүүс ихэвчлэн баталгаатай 100 000-ыг сонгодог. "
     "Энэ нь мөнгөний ашиг (utility) шугаман биш, эрсдэлээс зайлсхийдэгтэй холбоотой. "
     "Шүхрийн жишээ: авах = 77.0, авахгүй = 70.0 тул шүхэр авах нь зөв.")

sub("4.2 Утгын тор (Алхам 5, r = −0.04, γ = 1)")
para("Утга 30 давталтаар тогтворжиж, U(1, 1) = 0.705 гарсан нь лекцийн утгатай таарч байна.")
table([
    ["", "x = 1", "x = 2", "x = 3", "x = 4"],
    ["y = 3", "0.81", "0.87", "0.92", "+1.00"],
    ["y = 2", "0.76", "хана", "0.66", "−1.00"],
    ["y = 1", "0.71", "0.66", "0.61", "0.39"],
], [2, 2.5, 2.5, 2.5, 2.5])

sub("4.3 Бодлогын тор (Алхам 6)")
table([
    ["", "x = 1", "x = 2", "x = 3", "x = 4"],
    ["y = 3", "→", "→", "→", "+1"],
    ["y = 2", "↑", "хана", "↑", "−1"],
    ["y = 1", "↑", "←", "←", "←"],
], [2, 2.5, 2.5, 2.5, 2.5])
table([
    ["Нүд", "(1,1)", "(1,2)", "(1,3)", "(2,1)", "(2,3)", "(3,1)", "(3,2)", "(3,3)", "(4,1)"],
    ["Үйлдэл", "↑", "↑", "→", "←", "→", "←", "↑", "→", "←"],
], [2.2] + [1.45] * 9)
para("(3,1) ба (4,1) нүдэнд робот −1 гарцын хажуугаар богино замаар явахын оронд «←» сонгож, "
     "зүүн талаар тойрч явж байна. Учир нь (3,2)-оос «↑» хийхэд гулсаж −1 рүү орох эрсдэл бий, "
     "харин алхмын торгууль −0.04 бага тул урт ч аюулгүй замыг сонгож байна. (3,2) нүдэнд «↑» "
     "сонгосон нь −1 рүү 0.1-ийн магадлалтай гулсах ч гэсэн +1 рүү хамгийн ойр зам юм.")

sub("4.4 Алхмын шагналын харьцуулалт (Алхам 7)")
table([
    ["r", "U(1, 1)", "Давталт", "Доод мөр (1,1) (2,1) (3,1) (4,1)", "Тайлбар"],
    ["−0.04", "0.705", "30", "↑  ←  ←  ←", "Аюулгүй урт замаар тойрно"],
    ["−0.4", "−1.600", "24", "↑  →  ↑  ←", "Богино замыг сонгож эхэлнэ"],
    ["−2.0", "−10.815", "23", "→  →  →  ↑", "−1 гарц руу ч хамаагүй хурдан гарна"],
], [1.6, 2, 1.8, 4.6, 5.0], center_from=0)
para("Алхмын торгууль ихсэх тусам удаан амьдрах нь үнэтэй болж, робот эрсдэл гаргаж богино зам "
     "сонгодог. r = −2.0 үед (3,2) ба (4,1) нүднээс −1 гарц руу шууд орох нь (−1) цаашид алхсаар "
     "байхаас (−2 × алхам) дээр тул бодлого бүрэн өөрчлөгдсөн.")

sub("4.5 Графикууд (Алхам 8)")
image(f"{lab}/fig_history.png", 13)
caption("Зураг 1. Давталтын дугаар ба U(1, 1)")
para("Эхний 5 давталтад +1 шагналын мэдээлэл (1,1) хүртэл «хүрээгүй» тул утга зөвхөн −0.04-өөр "
     "буурч, дараа нь огцом өсөөд ~15 давталтын дараа 0.705 дээр тогтворжсон.")
image(f"{lab}/fig_heatmap.png", 10.5)
caption("Зураг 2. 11 нүдний утгын дулааны зураг (cmap=\"Greys\")")

sub("4.6 Хөнгөлөлт γ = 0.9")
table([
    ["", "x = 1", "x = 2", "x = 3", "x = 4"],
    ["y = 3", "0.51  →", "0.65  →", "0.80  →", "+1.00"],
    ["y = 2", "0.40  ↑", "хана", "0.49  ↑", "−1.00"],
    ["y = 1", "0.30  ↑", "0.25  →", "0.34  ↑", "0.13  ←"],
], [2, 2.5, 2.5, 2.5, 2.5])
para("γ = 0.9 үед 22 давталтаар тогтворжиж, U(1, 1) = 0.296 болж буурсан. Ирээдүйн шагнал "
     "хөнгөлөгддөг тул хол замаар тойрох нь ашиггүй болж, (2,1) нүдний бодлого «←»-ээс «→» болж "
     "богино зам руу шилжсэн.")

sub("4.7 Нэмэлт: Гулгалтгүй ба эерэг шагналтай ертөнц (12.8)")
para("trans(s, a) = [(1.0, move(s, a))] болгоход U(1, 1) = 0.8, 7 давталтаар зогссон. Гараар: "
     "(1,1)-ээс +1 хүртэл хамгийн богино зам 5 алхам, 1 − 5 × 0.04 = 0.8. Гулгамтгай ертөнцөд "
     "r = +0.1 болгоход утга тогтворжихгүй: U(1, 1) нь 50, 100, 200 дахь давталтад 5.68, 10.68, "
     "20.68 болж байнга өссөн, max_iter = 200-д хүрч зогссон.")

# ================= 5. Дүгнэлт =================
heading("5. Дүгнэлт")
para("Энэ лабораторийн ажлаар нэг удаагийн шийдвэрийг хүлээгдэж буй ашгаар, дараалсан шийдвэрийг "
     "MDP ба утгын давталтаар шийдсэн. 4×3 тор ертөнцөд утга 30 давталтаар тогтворжиж U(1, 1) = 0.705 "
     "гарсан нь лекцийн хариутай таарсан тул лабораторийн зорилгод хүрсэн гэж үзэж байна.")
para("**Яагаад бодлого өөрчлөгддөг вэ?** Бодлого нь «гарцын шагнал» ба «замд зарцуулах өртөг»-ийн "
     "тэнцвэрээс хамаардаг. Алхмын торгууль бага (−0.04) үед робот тэвчээртэй, −1-ээс хол аюулгүй "
     "замаар тойрдог. Торгууль ихсэхэд (−0.4, −2.0) эрсдэлтэй ч богино замыг сонгож, хэт их үед "
     "−1 гарц руу ч санаатай ордог. γ багасахад ирээдүйн +1 шагнал бага үнэ цэнэтэй болж, мөн "
     "богино зам давуу болдог.")
para("**Эерэг шагналтай үед яагаад гарц руу явдаггүй вэ?** r = +0.1 үед алхам бүр ашигтай тул "
     "робот аль болох удаан ертөнцөд үлдэхийг хүсэж, гарцаас зайлсхийдэг (жишээ нь (3,3)-аас «←», "
     "(4,1)-ээс ханыг мөргөж «↓»). γ = 1 тул нийт шагнал хязгааргүй өсөж, утга нийлдэггүй. Бодит "
     "амьдрал дээр цагаар цалинтай ажилтан ажлаа санаатай удаашруулах нь яг үүнтэй адил – шагналын "
     "бүтэц буруу байвал агент бидний хүссэн зорилгод хүрэхгүй.")
para("**Хэцүү байсан алхам ба шийдэл:** Утгын давталтад шинэ утгыг шууд U-д бичихэд нэг давталт "
     "дотор хуучин, шинэ утга холилдож 0.705-аас өөр гарч байсан. Үүнийг шинэ dict U2 үүсгэж, "
     "давталтын төгсгөлд U = U2 болгож зассан. Мөн imshow-д мөрүүдийг урвуу дарааллаар (y = 3 эхэнд) "
     "өгөхгүй бол зураг хөмөрч байсныг g[H − y, x − 1] индексээр шийдсэн.")

# ================= Хавсралт =================
heading("Хавсралт")
para("**A. Бүрэн код:** Lab12_MDP.ipynb (мөн Lab12_MDP.py), нэмэлт даалгавар 12.8 нь notebook-ийн "
     "төгсгөлд.", indent=False)
para("**B. Git log:**", indent=False)
log = subprocess.run(["git", "-C", lab, "log", "--oneline"], capture_output=True,
                     text=True, encoding="utf-8").stdout
code("* xxxxxxx docs: add report\n" + "\n".join("* " + l for l in log.strip().split("\n")))
import platform
para(f"**C. Туршилтын орчин:** Windows 11 Pro, Python {platform.python_version()}, numpy 2.4.5, "
     "matplotlib 3.11.2, Jupyter Notebook", indent=False)
para("**D. GitHub:** https://github.com/ariunbilegtsetsentungalag-ctrl/lab12", indent=False)

d.save(f"{lab}/Lab12_tailan.docx")
print("saved")
