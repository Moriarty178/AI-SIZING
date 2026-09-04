#!/usr/bin/env python
"""Đối chiếu số mục C1 dựng được với số mục người thẩm định trích trong PNX.

Đây là phép kiểm quyết định: nếu C1 dựng ra "III.4.1" mà PNX viết "IV.1.1" thì
finding không neo được vào nhãn, và recall không đo được. Chỉ so những nhãn PNX
CÓ ghi số mục (cột `muc` trong eval_sheet.csv).

    python scripts/check_section_match.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from src.ingestion.docx_reader import read_docx  # noqa: E402
from src.ingestion.filenames import find_sizing_docs, is_sizing_doc  # noqa: E402



def norm(sec: str) -> str:
    return sec.strip().upper().strip(".")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="data/eval_sheet.csv")
    ap.add_argument("--root", default="danh_sach_sizings_da_duyet")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    # mục PNX trích dẫn, theo hồ sơ
    want: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in csv.DictReader(open(args.sheet, encoding="utf-8-sig")):
        for m in (x.strip() for x in r["muc"].split(",") if x.strip()):
            want[r["dossier"]][norm(m)] += 1

    print(f"{len(want)} hồ sơ có nhãn ghi số mục\n")
    tot_hit = tot_all = 0
    for dossier in sorted(want):
        folder = pathlib.Path(args.root) / dossier
        if not folder.exists():
            continue
        have: set[str] = set()
        n_doc = 0
        for f in find_sizing_docs(folder):
            try:
                d = read_docx(str(f))
            except Exception:
                continue
            n_doc += 1
            have |= {norm(e.section) for e in d.elements if e.section}

        hits = [m for m in want[dossier] if m in have]
        miss = [m for m in want[dossier] if m not in have]
        n, tot = len(hits), len(want[dossier])
        tot_hit += n
        tot_all += tot
        flag = "✅" if n == tot else ("⚠️" if n else "❌")
        print(f"{flag} {dossier[:44]:<45} {n:>2}/{tot:<3} mục khớp  ({n_doc} bản)")
        if miss:
            print(f"      thiếu: {', '.join(sorted(miss)[:8])}")

    print(f"\n{'='*70}\nTổng: {tot_hit}/{tot_all} số mục PNX tìm thấy trong tài liệu"
          + (f"  ({tot_hit/tot_all*100:.0f}%)" if tot_all else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
