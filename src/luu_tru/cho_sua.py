"""5.2 — tìm CHỖ trong bản sizing mà một lỗi đang nói tới. KHÔNG nhập SQLAlchemy.

## Tìm được tới đâu — và nói thật khi không tìm được (NT4)

Finding chỉ mang `location`, sinh từ `Element.location` của C1, nên chỉ có ba dạng:

- `phần tử #N`         → đúng MỘT phần tử;
- `Mục X, trang Y`     → mọi phần tử của mục X ở trang Y;
- `Mục X` / `trang Y`  → mọi phần tử của mục (hoặc trang) đó;
- rỗng                 → C3/C5 không neo được vào đâu.

Không có câu trích nào đi kèm, nên với hai dạng giữa công cụ chỉ khoanh được một
NHÓM phần tử, không phải một câu. Trong nhóm, phần tử nhắc tới tên phân hệ của lỗi
được đưa lên đầu. Không định vị được thì lùi về «các đoạn nhắc tới phân hệ» và NÓI
RÕ đó là gợi ý, không phải vị trí; không có cả tên phân hệ thì nói không tìm được.

## Công cụ KHÔNG sửa file Word

Hoãn khỏi Giai đoạn 5 (chốt 2026-09-15). Chỗ hiện ra ở đây để người dùng biết mở
Word ra sửa ở đâu; sửa xong thì nộp lại để thẩm định lại.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

TOI_DA_DOAN = 5
TOI_DA_KY_TU = 1200
TOI_DA_DONG_BANG = 25
TOI_DA_KY_TU_O = 200

_PHAN_TU = re.compile(r"^phần tử #(\d+)$")
_MUC_TRANG = re.compile(r"^Mục (?P<muc>[^,]+?)(?:, trang (?P<trang>\d+))?$")
_TRANG = re.compile(r"^trang (\d+)$")
_NGOAC_CUOI = re.compile(r"\s*\(.*\)\s*$")

# `he_thong` là scope của lỗi cấp toàn hệ thống — không phải tên để tìm trong văn bản.
KHONG_PHAI_TEN = ("", "he_thong")


@dataclass
class Doan:
    index: int
    kind: str
    location: str
    text: str = ""
    rows: list[list[str]] | None = None
    cat_bot: bool = False


@dataclass
class ChoSua:
    # phan_tu · muc_trang · muc · trang · ten_phan_he · khong_tim_duoc
    cach_tim: str
    ghi_chu: str
    doan: list[Doan] = field(default_factory=list)
    con_nua: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def _ten_de_tim(scope_goc: str) -> str:
    """«Master (K8s Master node)» → «master»: phần trong ngoặc là mô tả C3 tự viết
    lại giữa các lần (5.0b), không chắc có nguyên văn trong tài liệu."""
    ten = _NGOAC_CUOI.sub("", scope_goc or "").strip()
    return "" if ten in KHONG_PHAI_TEN else ten.casefold()


def _nhac_toi(el, ten: str) -> bool:
    if not ten:
        return False
    if (el.text or "").casefold().find(ten) >= 0:
        return True
    return any(ten in (o or "").casefold() for r in (el.rows or []) for o in r)


def _doan(el) -> Doan:
    text = el.text or ""
    cat = len(text) > TOI_DA_KY_TU
    rows = None
    if el.kind == "table" and el.rows:
        cat = cat or len(el.rows) > TOI_DA_DONG_BANG
        rows = [[(o or "")[:TOI_DA_KY_TU_O] for o in r]
                for r in el.rows[:TOI_DA_DONG_BANG]]
        text = ""          # bảng hiện bằng `rows`; bản làm phẳng chỉ để tìm kiếm
    return Doan(index=el.index, kind=el.kind, location=el.location,
                text=text[:TOI_DA_KY_TU], rows=rows, cat_bot=cat)


def _chon(ung_vien: list, ten: str) -> tuple[list[Doan], int]:
    # Ảnh không có chữ để hiện; đã có cảnh báo NT4 riêng về ảnh.
    ung_vien = [e for e in ung_vien if e.kind != "image"]
    uu_tien = sorted(ung_vien, key=lambda e: (not _nhac_toi(e, ten), e.index))
    return [_doan(e) for e in uu_tien[:TOI_DA_DOAN]], max(0, len(uu_tien) - TOI_DA_DOAN)


def tim_cho_sua(doc, location: str, scope_goc: str = "") -> ChoSua:
    """`doc` là `DocxDocument` của bản ĐANG xét (thường là bản nộp gần nhất)."""
    loc = (location or "").strip()
    ten = _ten_de_tim(scope_goc)
    els = list(getattr(doc, "elements", []) or [])

    m = _PHAN_TU.match(loc)
    if m:
        n = int(m.group(1))
        chon = [e for e in els if e.index == n]
        if chon:
            return ChoSua("phan_tu", "Đúng phần tử lỗi đang nói tới.", [_doan(chon[0])])

    m = _MUC_TRANG.match(loc)
    if m:
        muc, trang = m.group("muc").strip(), m.group("trang")
        chon = [e for e in els if e.section == muc
                and (trang is None or e.page == int(trang))]
        if chon:
            doan, con = _chon(chon, ten)
            pham_vi = f"mục {muc}" + (f", trang {trang}" if trang else "")
            return ChoSua("muc_trang" if trang else "muc",
                          f"Lỗi chỉ neo được tới {pham_vi} — dưới đây là các đoạn trong "
                          "phạm vi đó" + (f", đoạn nhắc «{scope_goc}» xếp trước."
                                          if ten else "."), doan, con)

    m = _TRANG.match(loc)
    if m:
        chon = [e for e in els if e.page == int(m.group(1))]
        if chon:
            doan, con = _chon(chon, ten)
            return ChoSua("trang", f"Lỗi chỉ neo được tới trang {m.group(1)}.", doan, con)

    # Không định vị được — nói rõ là gợi ý, không giả làm vị trí.
    if ten:
        chon = [e for e in els if _nhac_toi(e, ten)]
        if chon:
            doan, con = _chon(chon, ten)
            ly_do = (f"Vị trí «{loc}» không còn khớp phần tử nào trong bản này"
                     if loc else "Lỗi không có vị trí")
            return ChoSua("ten_phan_he",
                          f"{ly_do} — dưới đây chỉ là các đoạn NHẮC TỚI «{scope_goc}», "
                          "KHÔNG phải vị trí chính xác của lỗi.", doan, con)
    return ChoSua("khong_tim_duoc",
                  "Không xác định được chỗ trong tài liệu"
                  + (f" (vị trí «{loc}» không khớp phần tử nào)" if loc else "")
                  + ". Đọc nội dung lỗi và căn cứ quy tắc để tìm tay.")
