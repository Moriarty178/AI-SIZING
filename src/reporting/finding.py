"""Cấu trúc `Finding` — đơn vị đầu ra duy nhất của mọi thành phần kiểm.

Theo lược đồ ở `docs/ke-hoach-trien-khai.md` mục C7, cộng hai trường sinh ra từ
quyết định "thẩm định hai vòng" (2026-08-25): `checklist_ref` và `vong`.

**NT2 là ràng buộc cứng ở đây**: mỗi finding phải neo vào `rule_ref` (mã quy tắc
có thật) HOẶC `computed_evidence` (con số do code tính). Không có căn cứ thì lọc
bỏ, không xuất ra — `Finding.co_can_cu()` là chỗ kiểm điều đó.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["critical", "major", "minor", "info"]
Confidence = Literal["cao", "vua", "thap"]

# Nhóm finding. "thieu_thong_tin" là nhóm bắt buộc theo NT4: khi không đủ dữ liệu
# thì nói không kiểm được, KHÔNG đoán giá trị rồi kết luận.
Category = Literal[
    "thieu_thong_tin",      # thiếu trường/đầu vào -> không kiểm được
    "sai_cong_thuc",        # tính lại lệch so với khai
    "vuot_nguong",          # vi phạm bất đẳng thức
    "thieu_muc",            # Vòng 1: thành phần bắt buộc không có
    "khong_kiem_chung_duoc",  # số liệu lưỡng nghĩa, ảnh, bảng tra chưa số hóa
    "khong_nhat_quan",
]


@dataclass
class Finding:
    id: str
    severity: Severity
    category: Category
    finding: str                       # câu mô tả cho người dùng, tiếng Việt
    rule_ref: str = ""                 # mã quy tắc, vd "KPI-02"
    rule_quote: str = ""               # trích dẫn nguyên văn tài liệu tiêu chí
    location: str = ""                 # "Mục IV.1.2, trang 8"
    computed_evidence: str = ""        # con số do code tính ra
    suggestion: str = ""
    confidence: Confidence = "cao"
    checklist_ref: list[str] = field(default_factory=list)
    vong: int | None = None            # 1 = checklist · 2 = Guideline
    scope_key: str = ""                # phân hệ nào, khi scope != he_thong
    source_doc: str = ""

    def co_can_cu(self) -> bool:
        """NT2: có `rule_ref` hoặc `computed_evidence` thì mới được xuất."""
        return bool(self.rule_ref or self.computed_evidence)

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


def loc_bo_khong_can_cu(findings: list[Finding]) -> tuple[list[Finding], list[Finding]]:
    """Tách (giữ lại, bị loại). Bị loại = vi phạm NT2, phải đếm chứ không im lặng."""
    keep = [f for f in findings if f.co_can_cu()]
    drop = [f for f in findings if not f.co_can_cu()]
    return keep, drop
