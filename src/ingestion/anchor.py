"""Tìm lại một đoạn văn bản trong `DocxDocument` — cổng chống bịa dùng chung.

C3 (1.7) và C5 (1.12) đều nhận từ model một đoạn *"trích từ tài liệu"* và đều phải trả
lời cùng một câu: **đoạn này có thật trong tài liệu không?** Không tìm lại được nghĩa là
model diễn đạt lại hoặc bịa, và mọi thứ dựng trên nó đều mất căn cứ (NT2) — finding sẽ
dẫn người dùng tới một chỗ không tồn tại.

Đặt ở `ingestion` vì đây là việc *"định vị trong tài liệu"*, cùng nhà với `DocxDocument`,
chứ không phải việc của riêng bên trích xuất hay bên thẩm định.
"""
from __future__ import annotations

import re

from .docx_reader import DocxDocument, Element

# Ngữ cảnh gửi cho model có tiền tố vị trí "[Mục IV.1, trang 8] ...". Model hay chép cả
# tiền tố đó vào đoạn trích, và khi ấy nó không khớp `Element.text` nào — tự mình làm
# hỏng cổng neo của chính mình. Cắt tiền tố trước khi so.
_TIEN_TO_VI_TRI = re.compile(r"^\s*\[[^\]]{0,80}\]\s*")

DAI_TOI_THIEU = 3       # chuỗi ngắn hơn thì khớp bừa, vô nghĩa


def chuan_hoa(s: str) -> str:
    return re.sub(r"\s+", " ", _TIEN_TO_VI_TRI.sub("", s or "").strip().lower())


def neo(doc: DocxDocument, *khoa: str,
        khoang: tuple[int, int] | None = None,
        uu_tien_kind: str | None = None) -> tuple[Element | None, int]:
    """Tìm phần tử chứa một trong các khoá, theo đúng thứ tự ưu tiên truyền vào.

    Trả `(phần tử, chỉ số khoá đã khớp)`; `(None, -1)` nếu không khoá nào có thật.

    `uu_tien_kind` xét một loại phần tử trước phần còn lại. Sinh ra cho việc định vị
    MỤC của phân hệ: quét theo thứ tự tài liệu thì tên phân hệ khớp trúng bảng thuật
    ngữ ở đầu tài liệu chứ không phải heading mở đầu mục của nó. Đo trên bản Vtag
    2026-09-07: 5/6 phân hệ cùng khớp phần tử #30 (bảng «# | Tên | Mô tả»), trong khi
    heading thật nằm ở #49/#59/#74/#93/#105/#111. Hỏng theo hai kiểu cùng lúc — phân
    hệ sớm nhất nhận khoảng không chứa nội dung của nó, còn các phân hệ trùng chỉ số
    thì mất hẳn tác dụng tách khoảng.
    Thứ tự quan trọng: khoá đầu thường là nguyên văn câu (bằng chứng mạnh), khoá sau
    là bản rút gọn (bằng chứng yếu hơn) — bên gọi dùng chỉ số để hạ độ tin cậy.

    `khoang` giới hạn vùng tìm về `[đầu, cuối)` theo `Element.index`. Không giới hạn thì
    một giá trị hỏi cho phân hệ này neo được vào phần tử của phân hệ khác: lượt chạy
    19:07 có 6/32 giá trị neo ra ngoài phân hệ đang hỏi — GoldenGate (#69–83) lấy
    `chuan_spec` ở #28, «Các module vệ tinh» (#67–69) lấy `dung_luong_ram_gb` ở #77.
    Chính là thứ `khoang_phan_he` sinh ra để chặn, nhưng đường neo lại bỏ qua nó.
    """
    els = ([e for e in doc.elements if khoang[0] <= e.index < khoang[1]]
           if khoang else doc.elements)
    # `uu_tien_kind`: xét loại phần tử này TRƯỚC, rồi mới tới phần còn lại. Thứ tự
    # khoá vẫn thắng — khoá mạnh hơn tìm hết cả hai vòng trước khi xét khoá yếu hơn.
    vong = ([e for e in els if e.kind == uu_tien_kind], els) if uu_tien_kind else (els,)
    for i, k in enumerate(khoa):
        kk = chuan_hoa(k)
        if len(kk) < DAI_TOI_THIEU:
            continue
        for tap in vong:
            for e in tap:
                if kk in chuan_hoa(e.text):
                    return e, i
    return None, -1
