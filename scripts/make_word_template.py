#!/usr/bin/env python
"""1.16 — sinh mẫu Word chuẩn từ 57 mục checklist. Thuần code, không cần model.

    python scripts/make_word_template.py --ten "MyKid 2.0" --phan-he Redis,Kafka
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx
from src.reporting.mau_word import doc_checklist, dung_mau


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ten", default="<TÊN HỆ THỐNG>")
    ap.add_argument("--phan-he", default="", help="phân hệ thêm, vd Redis,Kafka")
    ap.add_argument("--ra", default="data/knowledge_base/mau-sizing-chuan.docx")
    a = ap.parse_args()

    mucs = doc_checklist()
    them = [x.strip() for x in a.phan_he.split(",") if x.strip()]
    d = dung_mau(mucs, phan_he_them=them, ten_he_thong=a.ten)

    ra = pathlib.Path(a.ra)
    ra.parent.mkdir(parents=True, exist_ok=True)
    d.save(str(ra))
    print(f"Đã sinh {ra} từ {len(mucs)} dòng checklist"
          + (f", thêm {len(them)} phân hệ: {', '.join(them)}" if them else ""))

    # Đọc lại bằng chính C1: mẫu ta phát ra mà C1 không đọc được thì vô nghĩa.
    doc = read_docx(str(ra))
    muc_so = len({e.section for e in doc.elements if e.section})
    print(f"C1 đọc lại: {len(doc.elements)} phần tử · {muc_so} số mục nhận ra")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
