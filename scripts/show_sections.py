#!/usr/bin/env python
"""In cây đề mục C1 dựng được — để mắt người đối chiếu với số Word hiển thị."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from src.ingestion.docx_reader import read_docx  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for path in sys.argv[1:]:
    d = read_docx(path)
    print(f"\n=== {pathlib.Path(path).name}  ({d.n_pages} trang, {d.page_source})")
    for w in d.warnings:
        print(f"  ⚠️ {w}")
    for e in d.elements:
        if e.kind == "heading":
            pad = "  " * ((e.level or 1) - 1)
            pg = f"tr.{e.page}" if e.page else "—"
            print(f"  {pg:>6}  {pad}{e.section or '(không số)':<12} {e.text[:58]}")
