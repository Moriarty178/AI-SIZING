"""5.3 — VÙNG của từng phân hệ trong tài liệu, và vân tay NỘI DUNG của một vùng.

Thuần Python, không gọi model, không nhập `extractor.py` (module đó nạp `rules.yaml`
ngay lúc nhập) — để C5 và phần đo dùng chung được mà không kéo theo C3.

## Khoảng phân hệ (chuyển nguyên từ `Extractor.khoang_phan_he`)

C3 cắt ngữ cảnh của một phân hệ theo khoảng phần tử `[đầu mục của nó, đầu mục của
phân hệ kế)`. Lý do đo được nằm ở docstring `khoang_phan_he` bên dưới — hàm chuyển
sang đây KHÔNG đổi một dòng hành vi nào.

## Vùng — dùng để BÁO và ĐO, không để chọn lượt gọi

Chọn lượt gọi nào dùng lại được KHÔNG dựa vào vùng: nó dựa vào chính nội dung model
được đọc trong lượt đó (`src/llm/phat_lai.py`). Vùng ở đây chỉ để:

- nói cho người dùng phân hệ nào có nội dung đổi so với lần trước;
- ĐO xem nếu C5 cấp phân hệ chỉ chạy lại khi vùng của nó hoặc phần chung đổi thì có
  kết luận nào sai không (người dùng chốt 2026-09-17: làm chặt trước, đo rồi mới quyết).

Vùng của phân hệ = khoảng phần tử của nó, GIỚI HẠN trong mục gốc (`III` của
`III.2.1`) — cùng luật `phan_vung_bang` dùng để gán bảng, để phân hệ cuối không nuốt
luôn Mục IV tổng hợp. Phân hệ không neo được vào đâu có vùng là cả tài liệu.
Phần chung = mọi phần tử không thuộc vùng của phân hệ nào đã neo được.
"""
from __future__ import annotations

import hashlib
import json
import re

_NGOAC_CUOI = re.compile(r"\s*\(.*\)\s*$")


def chuan_ten(ten: str) -> str:
    """«Master (K8s Master node)» → «master». Cùng luật khoá baseline của 5.1: phần
    trong ngoặc cuối là mô tả C3 tự viết lại giữa các lần (đo 5.0b)."""
    return " ".join(_NGOAC_CUOI.sub("", ten or "").split()).casefold()


def _muc_goc(s: str) -> str:
    return (s or "").split(".")[0].strip().upper()


def dau_muc(doc, idx: int, chan_duoi: int) -> int:
    """Heading gần nhất ở TRƯỚC `idx`, không lùi quá `chan_duoi`."""
    if doc is None:
        return idx
    return max((e.index for e in doc.elements
                if e.kind == "heading" and chan_duoi < e.index <= idx),
               default=idx)


def khoang_phan_he(core, ph, het: int, doc=None) -> tuple[int, int] | None:
    """Khoảng phần tử thuộc về một phân hệ: từ đầu MỤC của nó đến phân hệ kế.

    Cắt theo `section` không đủ — ở BCCS3 cả 13 phân hệ nằm trong mục III, nên
    `Firewall` vẫn nhìn thấy bảng của `Database` và lấy nhầm số của nó.

    **Bắt đầu từ đầu mục, không từ chỗ phân hệ được nhắc.** Mốc phân hệ thường là
    bảng cấu hình (`bang_cau_hinh` được tra trước tên), mà bảng cấu hình nằm ở
    CUỐI mục: trên bản Vtag, mục #49–59 có bảng ở #55–57, mục #59–74 có bảng ở #72.
    Lấy mốc làm điểm đầu thì toàn bộ văn xuôi mở đầu mục nằm ngoài cửa sổ — mà
    khoảng này quyết định CẢ ngữ cảnh gửi cho model lẫn vùng neo, nên model không
    được thấy phần đó và giá trị trích từ đó cũng không neo lại được.

    Đo ở lượt B1 2026-09-07: **28/58 lượt mất neo là giá trị CÓ THẬT nằm ngoài cửa
    sổ** (Vtag 18/32) — nguyên nhân đơn lẻ lớn nhất. Cùng lượt đo đó bác bỏ giả
    thuyết "trích vắt qua ranh giới phần tử": 0 lượt trên cả bốn hồ sơ.

    Không lùi quá mốc của phân hệ liền trước, nên phần đất của nó không bị nuốt.
    Không có `doc` hoặc không có heading nào ở giữa thì giữ nguyên hành vi cũ.
    """
    if ph.element_index is None:
        return None
    moc = sorted(x.element_index for x in core.phan_he
                 if x.element_index is not None)
    # Điểm KẾT cũng phải là đầu mục của phân hệ kế, không phải mốc của nó: lấy mốc
    # thì cửa sổ lấn sang phần văn xuôi mở đầu mục sau (Worker thành 49–72, nuốt
    # trọn mục Postgres 59–74) — đúng thứ khoảng này sinh ra để chặn.
    dau = {x: dau_muc(doc, x, max([y for y in moc if y < x], default=-1))
           for x in moc}
    sau = [x for x in moc if x > ph.element_index]
    return (dau[ph.element_index], dau[sau[0]] if sau else het)


def vung_phan_he(doc, core) -> tuple[dict[str, list[int]], list[int]]:
    """({tên phân hệ: [chỉ số phần tử]}, [chỉ số phần tử của phần chung]).

    Khoá là `ten_phan_he` GỐC — hai `scope_key` của cùng một phân hệ (có/không kèm
    công nghệ lưu trữ) dùng chung một vùng.
    """
    tat_ca = [e.index for e in doc.elements]
    het = (max(tat_ca) + 1) if tat_ca else 0
    vung: dict[str, list[int]] = {}
    da_neo: set[int] = set()
    for ph in core.phan_he:
        kh = khoang_phan_he(core, ph, het, doc)
        if kh is None:
            vung[ph.ten_phan_he] = list(tat_ca)
            continue
        goc = _muc_goc(ph.muc)
        chon = [e.index for e in doc.elements
                if kh[0] <= e.index < kh[1] and (not goc or _muc_goc(e.section) == goc)]
        # Hai phân hệ cùng tên (C3 nhận diện trùng): gộp vùng, không để cái sau đè.
        vung[ph.ten_phan_he] = sorted(set(vung.get(ph.ten_phan_he, [])) | set(chon))
        da_neo.update(chon)
    return vung, [i for i in tat_ca if i not in da_neo]


def van_tay(doc, chi_so) -> str:
    """Vân tay NỘI DUNG của một tập phần tử — KHÔNG gồm số trang, số mục, chỉ số.

    Chèn một đoạn ở đầu tài liệu làm mọi chỉ số và số trang phía sau dịch đi, nhưng
    nội dung một phân hệ ở cuối tài liệu thì không đổi; vân tay phải nói đúng điều đó.
    """
    tap = set(chi_so)
    ds = [[e.kind, e.text or "", e.rows or []]
          for e in sorted(doc.elements, key=lambda e: e.index) if e.index in tap]
    return hashlib.sha256(json.dumps(ds, ensure_ascii=False).encode("utf-8")).hexdigest()
