"""Dựng lại số đề mục mà Word TỰ SINH khi hiển thị.

Vì sao cần: tài liệu sizing thật dùng Heading style với đánh số tự động
(`w:numPr`), nên số mục **không nằm trong text** — `paragraph.text` chỉ trả về
"YÊU CẦU BÀI TOÁN", không có "I.". Không dựng lại được số thì 28/48 bản sizing
không neo được finding vào mục, mà nhãn vàng từ PNX lại neo đúng theo
*"Mục IV.1.1"* (xem `docs/0.7-nhan-vang-tu-pnx.md`).

Không tự bịa "1.1.1": phải đọc `w:numFmt` và `w:lvlText` trong `word/numbering.xml`
thì mới ra đúng thứ người thẩm định nhìn thấy — cấp 1 của các bản này là **số La
Mã**, nên đoán bừa số Ả Rập sẽ lệch với mọi trích dẫn trong PNX.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from docx.oxml.ns import qn

_ROMAN = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
          (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def _roman(n: int) -> str:
    out = []
    for v, s in _ROMAN:
        while n >= v:
            out.append(s)
            n -= v
    return "".join(out)


def _letter(n: int) -> str:
    out = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        out = chr(ord("a") + r) + out
    return out


def _fmt(n: int, num_fmt: str) -> str:
    if num_fmt == "upperRoman":
        return _roman(n).upper()
    if num_fmt == "lowerRoman":
        return _roman(n)
    if num_fmt == "upperLetter":
        return _letter(n).upper()
    if num_fmt == "lowerLetter":
        return _letter(n)
    if num_fmt == "none":
        return ""
    return str(n)          # decimal và mọi kiểu chưa hỗ trợ


@dataclass
class _Level:
    num_fmt: str = "decimal"
    lvl_text: str = "%1."
    start: int = 1


@dataclass
class Numbering:
    """Bảng tra định dạng đánh số + bộ đếm đang chạy khi duyệt tài liệu."""

    levels: dict[int, dict[int, _Level]] = field(default_factory=dict)  # numId -> ilvl
    _counters: dict[tuple[int, int], int] = field(default_factory=dict)

    def label(self, num_id: int, ilvl: int) -> str:
        """Tăng bộ đếm rồi trả ĐƯỜNG DẪN đầy đủ của mục, ví dụ "IV.1.2".

        Cố ý KHÔNG dùng nguyên `w:lvlText` mà Word hiển thị: trong các bản sizing
        thật, lvlText của cấp 2 chỉ là "%2." nên Word hiện "1." — con số này lặp
        lại dưới mọi chương, khiến hai mục khác nhau có cùng `section` và finding
        không neo được. Ghép từ cấp 1 xuống thì ra đúng dạng người thẩm định trích
        dẫn trong PNX ("Mục IV.1.1"), và duy nhất trong toàn tài liệu.
        """
        lvls = self.levels.get(num_id)
        if not lvls or ilvl not in lvls:
            return ""

        key = (num_id, ilvl)
        self._counters[key] = self._counters.get(key, lvls[ilvl].start - 1) + 1
        # Sang mục mới ở cấp trên thì mọi cấp dưới quay về đầu, đúng như Word.
        for (n, l) in list(self._counters):
            if n == num_id and l > ilvl:
                del self._counters[(n, l)]

        parts = []
        for i in range(ilvl + 1):
            lv = lvls.get(i, _Level())
            cnt = self._counters.get((num_id, i), lv.start)
            piece = _fmt(cnt, lv.num_fmt)
            if piece:
                parts.append(piece)
        return ".".join(parts)


def load_numbering(doc) -> Numbering:
    """Đọc word/numbering.xml. Không có phần đó thì trả bảng rỗng, không lỗi."""
    num = Numbering()
    try:
        part = doc.part.numbering_part
    except (KeyError, AttributeError, NotImplementedError):
        return num
    root = part.element

    abstract: dict[int, dict[int, _Level]] = {}
    for an in root.findall(qn("w:abstractNum")):
        aid = an.get(qn("w:abstractNumId"))
        if aid is None:
            continue
        lv: dict[int, _Level] = {}
        for l in an.findall(qn("w:lvl")):
            ilvl = l.get(qn("w:ilvl"))
            if ilvl is None:
                continue
            f = l.find(qn("w:numFmt"))
            t = l.find(qn("w:lvlText"))
            s = l.find(qn("w:start"))
            lv[int(ilvl)] = _Level(
                num_fmt=(f.get(qn("w:val")) if f is not None else "decimal"),
                lvl_text=(t.get(qn("w:val")) if t is not None else "%1."),
                start=int(s.get(qn("w:val"))) if s is not None else 1,
            )
        abstract[int(aid)] = lv

    for n in root.findall(qn("w:num")):
        nid = n.get(qn("w:numId"))
        a = n.find(qn("w:abstractNumId"))
        if nid is None or a is None:
            continue
        aid = a.get(qn("w:val"))
        if aid is not None and int(aid) in abstract:
            num.levels[int(nid)] = abstract[int(aid)]
    return num


def para_num_ref(p_el) -> tuple[int, int] | None:
    """(numId, ilvl) của một đoạn, hoặc None nếu đoạn không đánh số tự động."""
    npr = p_el.find(".//" + qn("w:numPr"))
    if npr is None:
        return None
    nid = npr.find(qn("w:numId"))
    ilv = npr.find(qn("w:ilvl"))
    if nid is None or nid.get(qn("w:val")) is None:
        return None
    return int(nid.get(qn("w:val"))), int(ilv.get(qn("w:val"))) if ilv is not None else 0
