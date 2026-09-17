"""5.2 — tìm CHỖ trong bản sizing mà một lỗi đang nói tới. KHÔNG nhập SQLAlchemy.

## Tìm được tới đâu — và nói thật khi không tìm được (NT4)

Finding chỉ mang `location`, sinh từ `Element.location` của C1, nên chỉ có ba dạng:

- `phần tử #N`         → đúng MỘT phần tử;
- `Mục X, trang Y`     → mọi phần tử của mục X ở trang Y;
- `Mục X` / `trang Y`  → mọi phần tử của mục (hoặc trang) đó;
- rỗng                 → C3/C5 không neo được vào đâu.

Nghiệm thu 2026-09-17 trên VTracking 2.0.1 (719 dòng): 77,9% tới được mục + trang,
15,6% chỉ gợi ý theo tên phân hệ, 6,5% không tìm được, **0% tới đúng một phần tử**.

## Hiện theo THỨ TỰ TÀI LIỆU trong một mục

Ảnh chụp nghiệm thu: xếp «đoạn nhắc tên phân hệ» lên trước làm năm ô hiển thị bị
các nhãn ngắn («Mức tiêu thụ CPU của FrontEnd») chiếm hết, còn BẢNG SỐ — chỗ cần
sửa — rơi ra ngoài. Trong một mục, nhãn và bảng đi thành cặp; giữ nguyên thứ tự thì
người đọc thấy đúng bố cục mình đã viết. Nâng trần lên 12 phần tử.

## Không định vị được: tìm MỤC nói về phân hệ

Ảnh chụp nghiệm thu: lùi về «mọi phần tử nhắc Mongo» theo thứ tự tài liệu thì hai
bảng đầu trang 3–4 (danh sách máy chủ, bảng CPU) chiếm chỗ, và 25 dòng đầu của
chúng không có dòng Mongo nào — người dùng không thấy vì sao chúng hiện ra. Tiêu đề
«Định cỡ module Mongo (N + 1)» ở trang 14 lại xếp thứ ba.

Nay: có TIÊU ĐỀ nhắc tên phân hệ thì hiện tiêu đề đó cùng nội dung tới tiêu đề kế
tiếp cùng cấp; không có thì hiện các phần tử nhắc tên, đoạn văn trước bảng, và bảng
CHỈ hiện hàng tiêu đề + các dòng nhắc tên. Vẫn ghi rõ đây là GỢI Ý, không phải vị trí.

## Công cụ KHÔNG sửa file Word

Hoãn khỏi Giai đoạn 5 (chốt 2026-09-15). Chỗ hiện ra ở đây để người dùng biết mở
Word ra sửa ở đâu; sửa xong thì nộp lại để thẩm định lại.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

TOI_DA_DOAN = 12            # trong một mục/trang, hoặc một mục tìm theo tiêu đề
TOI_DA_DOAN_GOI_Y = 5       # khi chỉ gom được các phần tử rời nhắc tên phân hệ
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
    # Bảng chỉ hiện hàng tiêu đề + dòng nhắc tên phân hệ: `tong_dong` là số dòng thật.
    loc_theo_ten: bool = False
    tong_dong: int = 0


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


def _co(chuoi: str, ten: str) -> bool:
    return bool(ten) and ten in (chuoi or "").casefold()


def _nhac_toi(el, ten: str) -> bool:
    return _co(el.text, ten) or any(_co(o, ten) for r in (el.rows or []) for o in r)


def _doan(el, ten: str = "", *, loc_dong: bool = False) -> Doan:
    """`loc_dong`: bảng chỉ giữ hàng tiêu đề + dòng nhắc `ten` — chỉ dùng khi gom
    phần tử rời theo tên; trong một mục thì bảng thường CHỈ nói về một phân hệ, mà
    các dòng CPU/RAM của nó không lặp lại tên, lọc là mất đúng con số cần sửa."""
    text = el.text or ""
    if el.kind != "table" or not el.rows:
        return Doan(index=el.index, kind=el.kind, location=el.location,
                    text=text[:TOI_DA_KY_TU], cat_bot=len(text) > TOI_DA_KY_TU)
    rows = el.rows
    loc = False
    if loc_dong and ten and len(rows) > 1:
        khop = [r for r in rows[1:] if any(_co(o, ten) for o in r)]
        if khop:
            rows, loc = [rows[0]] + khop, True
    cat = len(rows) > TOI_DA_DONG_BANG
    return Doan(index=el.index, kind=el.kind, location=el.location,
                rows=[[(o or "")[:TOI_DA_KY_TU_O] for o in r]
                      for r in rows[:TOI_DA_DONG_BANG]],
                cat_bot=cat, loc_theo_ten=loc, tong_dong=len(el.rows))


def _theo_thu_tu(chon: list, ten: str) -> tuple[list[Doan], int]:
    """Giữ THỨ TỰ TÀI LIỆU; ảnh không có chữ để hiện (đã có cảnh báo NT4 riêng)."""
    chon = sorted((e for e in chon if e.kind != "image"), key=lambda e: e.index)
    return ([_doan(e, ten) for e in chon[:TOI_DA_DOAN]],
            max(0, len(chon) - TOI_DA_DOAN))


def _muc_theo_tieu_de(els: list, ten: str) -> list | None:
    """Tiêu đề ĐẦU TIÊN nhắc tên phân hệ + nội dung tới tiêu đề kế tiếp cùng/cao cấp."""
    for i, e in enumerate(els):
        if e.kind == "heading" and _co(e.text, ten):
            cap = e.level
            ra = [e]
            for sau in els[i + 1:]:
                if sau.kind == "heading" and (cap is None or sau.level is None
                                              or sau.level <= cap):
                    break
                ra.append(sau)
            return ra
    return None


def _goi_y_roi(els: list, ten: str) -> tuple[list[Doan], int]:
    """Không có tiêu đề nào nhắc tên: gom phần tử rời, đoạn văn trước bảng."""
    chon = [e for e in els if e.kind != "image" and _nhac_toi(e, ten)]
    chon.sort(key=lambda e: (e.kind == "table", e.index))
    return ([_doan(e, ten, loc_dong=True) for e in chon[:TOI_DA_DOAN_GOI_Y]],
            max(0, len(chon) - TOI_DA_DOAN_GOI_Y))


def tim_cho_sua(doc, location: str, scope_goc: str = "") -> ChoSua:
    """`doc` là `DocxDocument` của bản ĐANG xét (thường là bản nộp gần nhất)."""
    loc = (location or "").strip()
    ten = _ten_de_tim(scope_goc)
    els = sorted(getattr(doc, "elements", []) or [], key=lambda e: e.index)

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
            doan, con = _theo_thu_tu(chon, ten)
            pham_vi = f"mục {muc}" + (f", trang {trang}" if trang else "")
            return ChoSua("muc_trang" if trang else "muc",
                          f"Lỗi chỉ neo được tới {pham_vi} — dưới đây là nội dung phạm "
                          "vi đó theo đúng thứ tự trong tài liệu.", doan, con)

    m = _TRANG.match(loc)
    if m:
        chon = [e for e in els if e.page == int(m.group(1))]
        if chon:
            doan, con = _theo_thu_tu(chon, ten)
            return ChoSua("trang", f"Lỗi chỉ neo được tới trang {m.group(1)} — dưới đây "
                                   "là nội dung trang đó theo thứ tự.", doan, con)

    # Không định vị được — nói rõ là gợi ý, không giả làm vị trí.
    if ten:
        ly_do = (f"Vị trí «{loc}» không còn khớp phần tử nào trong bản này"
                 if loc else "Lỗi không có vị trí")
        muc = _muc_theo_tieu_de(els, ten)
        if muc:
            doan, con = _theo_thu_tu(muc, ten)
            return ChoSua("ten_phan_he",
                          f"{ly_do} — dưới đây là MỤC có tiêu đề nhắc «{scope_goc}», "
                          "KHÔNG phải vị trí chính xác của lỗi.", doan, con)
        doan, con = _goi_y_roi(els, ten)
        if doan:
            return ChoSua("ten_phan_he",
                          f"{ly_do} — dưới đây chỉ là các đoạn NHẮC TỚI «{scope_goc}» "
                          "(bảng chỉ hiện các dòng nhắc tên), KHÔNG phải vị trí chính "
                          "xác của lỗi.", doan, con)
    return ChoSua("khong_tim_duoc",
                  "Không xác định được chỗ trong tài liệu"
                  + (f" (vị trí «{loc}» không khớp phần tử nào)" if loc else "")
                  + ". Đọc nội dung lỗi và căn cứ quy tắc để tìm tay.")
