"""Đọc số trong tài liệu tiếng Việt — và nói rõ khi không chắc.

Cạm bẫy trung tâm: **"1.500" là 1500 hay 1,5?** Dấu chấm vừa là phân nhóm nghìn
(kiểu Việt) vừa là dấu thập phân (kiểu Anh), và tài liệu sizing thật dùng lẫn cả
hai — đôi khi trong cùng một bảng. Đọc sai một lần là lệch 1000 lần, đúng loại
lỗi khiến người dùng mất niềm tin ngay lập tức.

Cách xử lý ở đây, theo NT4: đoán theo quy ước, nhưng khi vẫn còn lưỡng nghĩa thì
trả `ambiguous=True` kèm cả hai cách đọc, để C4 xuất cảnh báo "không kiểm chứng
được" thay vì lặng lẽ chọn một cách rồi tính tiếp.

Suy luận (khớp `config/units.yaml` mục `so`):
  - có CẢ "." và ","   -> dấu xuất hiện SAU cùng là dấu thập phân. Chắc chắn.
  - chỉ một loại dấu, mỗi nhóm đúng 3 chữ số, có ≥2 nhóm ("3.000.000")
                       -> phân nhóm nghìn. Chắc chắn.
  - chỉ một dấu, sau nó KHÔNG phải 3 chữ số ("6,72", "0.75")
                       -> thập phân. Chắc chắn.
  - chỉ một dấu, sau nó đúng 3 chữ số ("1.500")
                       -> LƯỠNG NGHĨA. Theo kiểu mặc định của tài liệu, nhưng
                          đánh dấu ambiguous.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# số có thể mang dấu âm, dấu phân cách, và phần thập phân
_NUMBER = re.compile(r"[-+]?\d[\d.,\s]*\d|\d")


@dataclass
class ParsedNumber:
    value: float
    raw: str
    ambiguous: bool = False
    alt_value: float | None = None      # cách đọc còn lại, khi lưỡng nghĩa
    note: str = ""

    def __repr__(self) -> str:  # pragma: no cover - chỉ để đọc log
        a = f" (hoặc {self.alt_value}?)" if self.ambiguous else ""
        return f"ParsedNumber({self.value}{a} từ {self.raw!r})"


def parse_number(text: str, *, style: str = "vi", group_len: int = 3) -> ParsedNumber | None:
    """Đọc số đầu tiên trong `text`. Trả None nếu không có số nào."""
    m = _NUMBER.search(text or "")
    if not m:
        return None
    raw = m.group(0)
    body = raw.replace(" ", "")
    sign = -1.0 if body.startswith("-") else 1.0
    body = body.lstrip("+-")

    n_dot, n_com = body.count("."), body.count(",")

    # --- cả hai dấu: dấu sau cùng là thập phân, không còn nghi ngờ -------
    if n_dot and n_com:
        dec = "." if body.rfind(".") > body.rfind(",") else ","
        grp = "," if dec == "." else "."
        val = float(body.replace(grp, "").replace(dec, "."))
        return ParsedNumber(sign * val, raw)

    if not n_dot and not n_com:
        return ParsedNumber(sign * float(body), raw)

    sep = "." if n_dot else ","
    parts = body.split(sep)
    tail = parts[-1]

    # --- nhiều dấu cùng loại: chắc chắn là phân nhóm nghìn ---------------
    if len(parts) > 2:
        if all(len(p) == group_len for p in parts[1:]):
            return ParsedNumber(sign * float(body.replace(sep, "")), raw)
        # nhóm không đều -> không đọc bừa
        return ParsedNumber(sign * float(body.replace(sep, "")), raw, ambiguous=True,
                            note=f"nhiều dấu {sep!r} nhưng nhóm không đều {parts}")

    # --- đúng một dấu ----------------------------------------------------
    as_thousand = float(body.replace(sep, ""))
    as_decimal = float(body.replace(sep, "."))

    if len(tail) != group_len:
        # "6,72" · "0.75" · "12,3456" -> chỉ có thể là thập phân
        return ParsedNumber(sign * as_decimal, raw)

    # "0,042" — phân nhóm nghìn không bao giờ cho nhóm đầu là "0" hay có số 0
    # đứng đầu, nên chỉ còn cách đọc thập phân. Không đánh dấu lưỡng nghĩa ở đây,
    # nếu không hầu hết tỷ lệ nhỏ trong tài liệu đều bị gắn cờ vô ích.
    if parts[0] == "0" or (len(parts[0]) > 1 and parts[0].startswith("0")):
        return ParsedNumber(sign * as_decimal, raw)

    # "1.500" — đúng 3 chữ số phía sau: cả hai cách đọc đều hợp lệ.
    vi = (style == "vi") == (sep == ".")
    chosen, other = (as_thousand, as_decimal) if vi else (as_decimal, as_thousand)
    return ParsedNumber(
        sign * chosen, raw, ambiguous=True, alt_value=sign * other,
        note=f"{raw!r} có thể là {chosen:g} (phân nhóm nghìn) hoặc "
             f"{other:g} (thập phân); đang đọc theo kiểu {style!r}",
    )


def parse_all_numbers(text: str, **kw) -> list[ParsedNumber]:
    """Mọi số trong chuỗi, giữ nguyên thứ tự xuất hiện."""
    out: list[ParsedNumber] = []
    for m in _NUMBER.finditer(text or ""):
        p = parse_number(m.group(0), **kw)
        if p is not None:
            out.append(p)
    return out


def parse_percent(text: str, **kw) -> ParsedNumber | None:
    """Đọc phần trăm về dạng tỷ lệ 0–1. "75%" -> 0.75 · "0,75" -> 0.75.

    Không nhân/chia bừa: chỉ chia 100 khi có dấu %. Một con số trần như "75"
    có thể là 75% mà cũng có thể là 75 đơn vị gì đó, nên trả nguyên và để quy
    tắc quyết định.
    """
    p = parse_number(text, **kw)
    if p is None:
        return None
    if "%" in (text or ""):
        return ParsedNumber(p.value / 100, p.raw, p.ambiguous,
                            None if p.alt_value is None else p.alt_value / 100,
                            p.note)
    return p
