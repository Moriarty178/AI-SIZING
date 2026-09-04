"""Demo C7 (mục 1.10): dựng báo cáo Markdown từ finding thật của C4 + Vòng 1 dựng tay.

Vòng 1 ở đây DỰNG TAY vì C5 (mục 1.12) chưa có — dùng cờ `is_demo=True` để báo cáo
tự ghi rõ điều đó. Chạy:  PYTHONPATH=. python scripts/demo_report.py
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.extraction.schema import ExtractedValue, SizingCore, SizingExtension
from src.reporting.finding import Finding
from src.reporting.report import build_report
from src.validators.quantitative import QuantitativeValidator

# Một tài liệu có 2 phân hệ, App khai CPU vượt ngưỡng, DB thiếu nhiều thứ.
doc = SizingCore(
    ten_he_thong="Hệ thống Demo",
    ma_pyc="PYC-2026-DEMO",
    phan_he=[
        SizingExtension(ten_phan_he="App",
                        params={"cpu_95th": ExtractedValue(value=92,
                                                           location="Mục III.1, trang 6")}),
        SizingExtension(ten_phan_he="DB"),
    ],
)

findings: list[Finding] = QuantitativeValidator().findings(doc)

# Vòng 1 dựng tay: DB trượt mục "công nghệ sử dụng" -> mọi kiểm Vòng 2 của DB tạm hoãn;
# cả hệ thống thiếu bảng tổng hợp toàn hệ.
findings += [
    Finding(id="CL-3.x.2#DB", severity="major", category="thieu_thong_tin",
            finding="Phân hệ DB chưa nêu công nghệ sử dụng.",
            rule_ref="EVD-01", checklist_ref=["CL-3.x.2"], vong=1, scope_key="DB",
            suggestion="Bổ sung công nghệ (MariaDB/Redis/…) cho phân hệ DB."),
    Finding(id="CL-2.9#he_thong", severity="major", category="thieu_thong_tin",
            finding="Chưa có bảng tổng hợp đề xuất cấu hình toàn hệ thống.",
            rule_ref="EVD-10", checklist_ref=["CL-2.9"], vong=1, scope_key="",
            suggestion="Bổ sung bảng tổng hợp cấu hình cấp hệ thống."),
]

md = build_report(findings, ten_he_thong=doc.ten_he_thong, ma_pyc=doc.ma_pyc,
                  is_demo=True)
print(md)
