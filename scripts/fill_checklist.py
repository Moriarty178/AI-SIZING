#!/usr/bin/env python
"""1.17 — điền hộ cột tham chiếu của checklist thẩm định cho một bản sizing.

    python scripts/fill_checklist.py "<đường-dẫn.docx>"

KHÔNG gọi model, KHÔNG cần `settings.yaml`, chạy được ngoài mạng nội bộ.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx
from src.reporting.dinh_vi_checklist import bang_csv, bang_markdown, dinh_vi

THU_MUC_RA = "docs/checklist"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--ra", default=THU_MUC_RA, help="thư mục xuất kết quả")
    ap.add_argument("--im", action="store_true", help="không in bảng ra màn hình")
    a = ap.parse_args()

    p = pathlib.Path(a.docx)
    if not p.exists():
        print(f"Không thấy file: {p}")
        return 2

    doc = read_docx(str(p))
    print(f"C1: {len(doc.elements)} phần tử · "
          f"{sum(1 for e in doc.elements if e.kind == 'heading')} đề mục · "
          f"{len(doc.tables())} bảng · trang: {doc.page_source}")
    for w in doc.warnings:
        print(f"  ⚠ {w}")

    kq = dinh_vi(doc)
    thay = sum(1 for v in kq if v.tim_thay)
    print(f"\nĐịnh vị được {thay}/{len(kq)} mục checklist.")
    for v in kq:
        if v.tim_thay:
            print(f"  ✓ {v.muc.tt:<8} {v.location:<22} {v.muc.hang_muc[:52]}")
    print()
    for v in kq:
        if not v.tim_thay:
            gan = (f"  (gần nhất {v.diem:.0%} ở {v.location})"
                   if v.element_index is not None else "")
            print(f"  ✗ {v.muc.tt:<8} {v.muc.hang_muc[:52]}{gan}")

    ra = pathlib.Path(a.ra)
    ra.mkdir(parents=True, exist_ok=True)
    ten = p.stem[:60]
    md, csv = ra / f"checklist-{ten}.md", ra / f"checklist-{ten}.csv"
    md.write_text(bang_markdown(kq, ten_tai_lieu=p.name), encoding="utf-8")
    # `utf-8-sig` để Excel trên Windows không hiển thị tiếng Việt thành ký tự lạ.
    csv.write_text(bang_csv(kq), encoding="utf-8-sig")
    print(f"\nĐã ghi {md}\n         {csv}")
    if not a.im:
        print("\n" + bang_markdown(kq, ten_tai_lieu=p.name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
