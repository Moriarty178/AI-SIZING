"""Nhận biết đâu là BẢN SIZING trong thư mục hồ sơ — một nguồn sự thật duy nhất.

Thư mục hồ sơ thật chứa lẫn lộn: PNX, công văn, phiếu giải trình, biểu mẫu HSTK,
file Excel cấp phát, cả Guideline. Mẫu loại trừ này trước đây bị chép lại ở ba
script khác nhau; gom về đây để thêm một ngoại lệ chỉ phải sửa một chỗ.
"""
from __future__ import annotations

import pathlib
import re

# Không phải bản sizing: phân biệt theo TÊN file, không mở file.
NOT_SIZING = re.compile(
    r"PNX|Phản hồi PNX|Cong van|Phieu giai trinh|PYC |guideline|^GL\.|HSTK|QLTN|"
    r"checklist|yeu_cau_cap_phat|baocaocapphat|excel-list|passwords|Xin_cap_phat|"
    r"mẫu|mau_HSTK|ghichu",
    re.IGNORECASE,
)

# Ngoại lệ theo TÊN CỤ THỂ — tên không gợi ý gì, phải người xác nhận mới biết.
# Ghi rõ lý do để sau này không ai lặng lẽ bỏ nhầm một bản sizing thật.
NOT_SIZING_EXACT: dict[str, str] = {
    # người dùng xác nhận 2026-09-03; liên quan điểm lệch D11 ở 0.6
    "tuanha3.docx": "không phải bản sizing (xác nhận 2026-09-03)",
}


def is_sizing_doc(path: str | pathlib.Path) -> bool:
    name = pathlib.Path(path).name
    if name.startswith("~$"):
        return False
    if name in NOT_SIZING_EXACT:
        return False
    return not NOT_SIZING.search(name)


# Phiếu nhận xét của đơn vị thẩm định. KHÔNG phải: "Phản hồi PNX" (bên xin cấp viết
# trả lời) và công văn xin PNX — hai thứ đó không mang mốc thời gian của một VÒNG
# thẩm định, dùng nhầm sẽ làm lệch việc ghép vòng ↔ phiên bản tài liệu.
PNX_DOC = re.compile(r"PNX", re.IGNORECASE)
NOT_PNX = re.compile(r"phản\s*hồi|phan\s*hoi|cong\s*van|công\s*văn", re.IGNORECASE)


def is_pnx_doc(path: str | pathlib.Path) -> bool:
    name = pathlib.Path(path).name
    if name.startswith("~$"):
        return False
    return bool(PNX_DOC.search(name)) and not NOT_PNX.search(name)


def find_pnx_docs(root: str | pathlib.Path, suffix: str = ".docx") -> list[pathlib.Path]:
    return sorted(p for p in pathlib.Path(root).rglob(f"*{suffix}") if is_pnx_doc(p))


def find_sizing_docs(root: str | pathlib.Path, suffix: str = ".docx") -> list[pathlib.Path]:
    return sorted(p for p in pathlib.Path(root).rglob(f"*{suffix}") if is_sizing_doc(p))
