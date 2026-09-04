#!/usr/bin/env python
"""Vì sao C1 không nhận ra đề mục trong nhiều file? Xem style và cách đánh số thật."""
from __future__ import annotations

import collections
import pathlib
import sys

from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8")

for path in sys.argv[1:]:
    d = Document(path)
    styles: collections.Counter = collections.Counter()
    numbered = 0
    heading_like = []
    for p in d.paragraphs:
        st = p.style.name if p.style is not None else "?"
        styles[st] += 1
        has_num = p._p.find(".//" + qn("w:numPr")) is not None
        if has_num:
            numbered += 1
        if "head" in st.lower() or "đề" in st.lower() or "title" in st.lower():
            if len(heading_like) < 8 and p.text.strip():
                heading_like.append((st, has_num, p.text.strip()[:70]))

    print(f"\n=== {pathlib.Path(path).name}")
    print(f"  style hay gặp : {', '.join(f'{k}×{v}' for k, v in styles.most_common(6))}")
    print(f"  đoạn có numPr : {numbered}")
    if heading_like:
        print("  đoạn kiểu heading:")
        for st, hn, t in heading_like:
            print(f"     [{st}] numPr={hn}  {t}")
    else:
        print("  KHÔNG có đoạn nào mang style heading/title")
