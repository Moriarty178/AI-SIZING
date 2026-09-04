#!/usr/bin/env python
"""Chạy C1 trên mọi bản sizing .docx thật và báo cáo mức độ đọc được.

Đây là phép kiểm quan trọng hơn unit test: tài liệu thật do người viết tay, mỗi
bản một kiểu. Con số cần nhìn là **tỉ lệ file suy được số trang** và **tỉ lệ file
nhận ra đề mục** — hai thứ quyết định có neo được finding vào nhãn PNX hay không.

    python scripts/try_c1_on_dossiers.py [--root danh_sach_sizings_da_duyet]
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx  # noqa: E402
from src.ingestion.filenames import find_sizing_docs, is_sizing_doc  # noqa: E402



def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="danh_sach_sizings_da_duyet")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    files = find_sizing_docs(args.root)
    print(f"{len(files)} bản sizing .docx\n")

    src_count: collections.Counter = collections.Counter()
    fails: list[tuple[str, str]] = []
    no_section: list[str] = []
    tot_el = tot_tbl = tot_img = 0
    print(f'{"file":<52}{"phần tử":>8}{"bảng":>6}{"ảnh":>5}{"trang":>7}  nguồn trang')
    print("-" * 92)

    for f in files:
        try:
            d = read_docx(str(f))
        except Exception as e:
            fails.append((f.name, f"{type(e).__name__}: {e}"))
            if args.verbose:
                traceback.print_exc()
            continue
        src_count[d.page_source] += 1
        tot_el += len(d.elements)
        tot_tbl += len(d.tables())
        tot_img += len(d.images())
        if not any(e.section for e in d.elements):
            no_section.append(f.name)
        print(f"{f.name[:51]:<52}{len(d.elements):>8}{len(d.tables()):>6}"
              f"{len(d.images()):>5}{str(d.n_pages or '—'):>7}  {d.page_source}")

    ok = len(files) - len(fails)
    print("\n" + "=" * 92)
    print(f"Đọc được          : {ok}/{len(files)}")
    print(f"Tổng phần tử      : {tot_el:,} · bảng {tot_tbl:,} · ảnh {tot_img:,}")
    print(f"Nguồn số trang    : " + " · ".join(f"{k}={v}" for k, v in src_count.most_common()))
    n_page = src_count["rendered"] + src_count["manual"]
    print(f"Suy được số trang : {n_page}/{ok}"
          + (f"  ({n_page/ok*100:.0f}%)" if ok else ""))
    print(f"Nhận ra đề mục    : {ok - len(no_section)}/{ok}")
    if no_section:
        print("\n⚠️ KHÔNG nhận ra đề mục nào (finding sẽ khó neo vào nhãn PNX):")
        for n in no_section:
            print("   " + n[:80])
    if fails:
        print(f"\n❌ {len(fails)} file lỗi:")
        for n, e in fails:
            print(f"   {n[:60]:<60} {e[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
