"""C3 · đọc CÔNG THỨC mà tài liệu tự viết ra trong ô bảng — thuần code, không model.

Người viết sizing thường không chỉ ghi kết quả, họ ghi cả phép tính:

    = (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s

Đây là món quà cho NT1: mọi thứ cần để kiểm đều nằm sẵn trong ô, không phải hỏi
model câu nào. Code chỉ cần tính lại và so.

## Dấu phẩy: để SỐ HỌC tự chứng minh, đừng đoán

`696,249` là sáu trăm nghìn hay 696,249 đơn vị? Tài liệu PNX dùng lẫn cả hai lối.
Thay vì chọn bừa một quy ước, module này **thử cả hai và giữ lối nào khớp với kết
quả tác giả tự ghi**. Phép tính của chính tác giả là bằng chứng cho cách đọc số
của tác giả — không cần suy đoán, cũng không cần `ParsedNumber.ambiguous`.

Khi cả hai lối cùng khớp (ví dụ `17,284 * 6 = 103,704`, đúng cho cả hai vì phép
nhân bất biến theo thang), module giữ cả hai và chỉ kết luận những gì ĐÚNG với cả
hai. Khi không lối nào khớp, ô bị xếp `khong_khop` và KHÔNG được dùng làm căn cứ
(NT4) — đếm ra chứ không bỏ im lặng.

## Không dùng `eval()`

`asteval` với bảng ký hiệu rỗng (`CLAUDE.md` cấm `eval()`). Biểu thức còn bị lọc
trước bằng regex chỉ cho phép chữ số và `+-*/().,` — chuỗi có chữ cái không bao
giờ tới được bộ tính.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..ingestion.docx_reader import DocxDocument, Element

# Chỉ chữ số, dấu và toán tử. Cell có chữ cái không lọt qua đây, nên `asteval`
# không bao giờ nhận tên biến hay lời gọi hàm.
_BIEU_THUC = r"[-+*/().,0-9\s]+?"
_SO = r"[0-9][0-9.,]*"
_RE_CONG_THUC = re.compile(
    rf"^=?\s*(?P<bt>{_BIEU_THUC})\s*=\s*(?P<kq>{_SO})\s*(?P<dv>[A-Za-z/%]{{0,12}})\s*$")

# Hằng số nhân đứng ngay sau dấu `*`. Số chia (`/0.8`) KHÔNG phải hệ số dự phòng
# nên cố ý không bắt.
_RE_HE_SO_NHAN = re.compile(rf"\*\s*({_SO})")

# Sai số cho phép khi đối chiếu phép tính của tác giả. Tác giả làm tròn (696,249
# thay vì 696,248.4), nên 0 là quá chặt; 0,5% đủ rộng cho làm tròn mà vẫn đủ chặt
# để phân biệt hai quy ước dấu phẩy (chúng lệch nhau hàng nghìn lần).
DUNG_SAI_LAM_TRON = 0.005


def _theo_quy_uoc(s: str, quy_uoc: str) -> str:
    """`us`: `,` là phân cách nghìn · `vn`: `.` là phân cách nghìn, `,` là thập phân."""
    return s.replace(",", "") if quy_uoc == "us" \
        else s.replace(".", "").replace(",", ".")


def _nua_don_vi(kq_sach: str) -> float:
    """Nửa đơn vị của chữ số cuối mà tác giả ghi ra.

    «= 36» chỉ nói kết quả nằm trong [35,5 · 36,5); đòi khớp tới 0,5% ở những số
    nhỏ là đòi hơn những gì tác giả viết. Dung sai tương đối một mình thì quá
    chặt với số nhỏ và quá lỏng với số lớn, nên lấy cái lớn hơn của hai.
    """
    phan_le = len(kq_sach.split(".")[1]) if "." in kq_sach else 0
    return 0.5 * 10 ** -phan_le


def _tinh(bieu_thuc: str) -> float | None:
    """Tính một biểu thức số học đã làm sạch. None nếu không tính được."""
    from asteval import Interpreter
    it = Interpreter(usersyms={}, no_print=True, minimal=True)
    try:
        gt = it(bieu_thuc, raise_errors=True)
    except Exception:
        return None
    return float(gt) if isinstance(gt, (int, float)) and gt == gt else None


@dataclass
class CongThucKhai:
    """Một ô bảng chứa cả phép tính lẫn kết quả, đã được số học tự xác nhận."""
    o_goc: str                      # nguyên văn ô, để trích dẫn (NT2)
    bieu_thuc: str                  # phần trước dấu `=` cuối
    ket_qua_khai: str               # phần sau, nguyên văn
    don_vi: str = ""
    quy_uoc: tuple[str, ...] = ()   # lối đọc số nào khớp: ('us',) / ('vn',) / cả hai
    gia_tri: float | None = None    # giá trị theo lối đầu tiên khớp
    he_so_nhan: dict[str, tuple[float, ...]] = field(default_factory=dict)
    nhan_dong: str = ""             # nhãn dòng — cái gì đang được tính
    location: str = ""
    page: int | None = None
    section_title: str = ""
    bang_text: str = ""             # toàn văn bảng, dùng để xét ngữ cảnh thiết bị
    bang_idx: int = -1              # bảng thứ mấy — để soi các ô trong CÙNG bảng

    @property
    def khop(self) -> bool:
        return bool(self.quy_uoc)

    @property
    def co_nhan_chia(self) -> bool:
        """Có `*` hoặc `/` — tức là một phép TÍNH, không phải phép cộng dồn.

        Dòng «696,249 + 1,822,219 = 2,518,468» cộng lại các kết quả đã tính ở
        dòng trên; hệ số dự phòng nếu có thì đã nằm trong chúng rồi. Soi hệ số ở
        dòng cộng dồn là báo sai.
        """
        return "*" in self.bieu_thuc or "/" in self.bieu_thuc

    def co_he_so(self, gia_tri: float, dung_sai: float = 1e-9) -> bool | None:
        """Biểu thức có nhân với `gia_tri` không? None = hai lối đọc bất đồng."""
        tra = {any(abs(h - gia_tri) <= dung_sai for h in self.he_so_nhan.get(q, ()))
               for q in self.quy_uoc}
        return tra.pop() if len(tra) == 1 else None

    def can_cu(self) -> str:
        return f"«{self.o_goc.strip()}» ({self.location})"

    def so_hang(self) -> tuple[float, ...]:
        """Mọi hằng số xuất hiện trong biểu thức, theo lối đọc đầu tiên khớp."""
        if not self.quy_uoc:
            return ()
        q = self.quy_uoc[0]
        ra = []
        for s in re.findall(_SO, self.bieu_thuc):
            try:
                ra.append(float(_theo_quy_uoc(s, q)))
            except ValueError:
                pass
        return tuple(ra)


def doc_mot_o(o: str) -> CongThucKhai | None:
    """Phân tích một ô. None nếu ô không có dạng «biểu thức = kết quả»."""
    m = _RE_CONG_THUC.match(" ".join((o or "").split()))
    if not m:
        return None
    bt, kq = m.group("bt").strip(), m.group("kq").strip()
    if not any(c in bt for c in "+-*/"):
        return None                      # «= 5 = 5» không phải phép tính
    ct = CongThucKhai(o_goc=o, bieu_thuc=bt, ket_qua_khai=kq, don_vi=m.group("dv"))

    khop, hs = [], {}
    for quy_uoc in ("us", "vn"):
        gt = _tinh(_theo_quy_uoc(bt, quy_uoc))
        sach = _theo_quy_uoc(kq, quy_uoc)
        try:
            mong = float(sach)
        except ValueError:
            continue
        if gt is None or mong == 0:
            continue
        # «71.5 / 125 = 57,2 %»: tác giả ghi kết quả dưới dạng phần trăm. Đây là
        # cách viết, không phải sai số học — nhận cả hai.
        if ct.don_vi == "%" and abs(gt * 100 - mong) <= abs(mong) * DUNG_SAI_LAM_TRON:
            gt *= 100
        if abs(gt - mong) <= max(abs(mong) * DUNG_SAI_LAM_TRON, _nua_don_vi(sach)):
            khop.append(quy_uoc)
            if ct.gia_tri is None:
                ct.gia_tri = mong
            hs[quy_uoc] = tuple(
                float(_theo_quy_uoc(s, quy_uoc))
                for s in _RE_HE_SO_NHAN.findall(bt)
                if _theo_quy_uoc(s, quy_uoc).replace(".", "").isdigit())
    ct.quy_uoc, ct.he_so_nhan = tuple(khop), hs
    return ct


def _nhan_dong(rows: list[list[str]], i: int, j: int) -> str:
    """Ô đầu tiên bên trái trong cùng dòng có chữ — cái gì đang được tính."""
    for c in reversed(rows[i][:j]):
        t = " ".join((c or "").split())
        if t and any(ch.isalpha() for ch in t):
            return t
    return ""


def doc_cong_thuc(doc: DocxDocument) -> list[CongThucKhai]:
    """Mọi ô bảng có dạng «biểu thức = kết quả» trong tài liệu, kể cả ô không khớp.

    Trả cả ô `khop=False` để bên gọi ĐẾM được số ô không kiểm chứng được (NT4),
    thay vì lặng lẽ chỉ trả phần đẹp.
    """
    ra: list[CongThucKhai] = []
    for idx, b in enumerate(doc.tables()):
        rows = b.rows or []
        for i, dong in enumerate(rows):
            for j, o in enumerate(dong):
                ct = doc_mot_o(o)
                if ct is None:
                    continue
                ct.nhan_dong = _nhan_dong(rows, i, j)
                ct.location = _vi_tri(b)
                ct.page = b.page
                ct.section_title = b.section_title
                ct.bang_text = b.text or ""
                ct.bang_idx = idx
                ra.append(ct)
    return ra


def _vi_tri(b: Element) -> str:
    try:
        return b.location
    except Exception:                              # pragma: no cover - phòng xa
        return f"trang {b.page}" if b.page else ""
