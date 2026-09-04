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


def neo(doc: DocxDocument, *khoa: str) -> tuple[Element | None, int]:
    """Tìm phần tử chứa một trong các khoá, theo đúng thứ tự ưu tiên truyền vào.

    Trả `(phần tử, chỉ số khoá đã khớp)`; `(None, -1)` nếu không khoá nào có thật.
    Thứ tự quan trọng: khoá đầu thường là nguyên văn câu (bằng chứng mạnh), khoá sau
    là bản rút gọn (bằng chứng yếu hơn) — bên gọi dùng chỉ số để hạ độ tin cậy.
    """
    for i, k in enumerate(khoa):
        kk = chuan_hoa(k)
        if len(kk) < DAI_TOI_THIEU:
            continue
        for e in doc.elements:
            if kk in chuan_hoa(e.text):
                return e, i
    return None, -1
