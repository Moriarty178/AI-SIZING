#!/usr/bin/env python
"""Extract readable text from a .docx using ONLY the Python standard library.

Why stdlib-only
---------------
The project environment is not set up yet (Phase 1.1). Rather than install
python-docx / uv just to read the historical dossiers, we unzip the .docx
(a ZIP of XML) and walk word/document.xml ourselves. Enough for PNX prose and
sizing tables; not a general-purpose converter.

Output is plain text: paragraphs kept in order, tables rendered as rows with
cells joined by " | ". This is source material for gold labels (0.7), so we do
NOT fix spelling, join wrapped lines, or drop diacritics (NT2).

Usage
-----
    python scripts/extract_docx_text.py <file.docx> [-o out.txt]

If -o is omitted, prints to stdout (set PYTHONIOENCODING=utf-8 on Windows).
"""
from __future__ import annotations

import argparse
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def para_text(p: ET.Element) -> str:
    """Concatenate the visible text of one <w:p>, honoring tabs and breaks."""
    parts: list[str] = []
    for node in p.iter():
        t = local(node.tag)
        if t == "t":
            parts.append(node.text or "")
        elif t == "tab":
            parts.append("\t")
        elif t in ("br", "cr"):
            parts.append("\n")
    return "".join(parts)


def walk(el: ET.Element, out: list[str], depth: int = 0) -> None:
    """Walk body children in document order, emitting paragraphs and tables."""
    for child in el:
        tag = local(child.tag)
        if tag == "p":
            out.append(para_text(child))
        elif tag == "tbl":
            out.append("")  # blank line before a table
            for row in child:
                if local(row.tag) != "tr":
                    continue
                cells: list[str] = []
                for cell in row:
                    if local(cell.tag) != "tc":
                        continue
                    cell_lines: list[str] = []
                    for p in cell.iter():
                        if local(p.tag) == "p":
                            cell_lines.append(para_text(p))
                    cells.append(" ".join(s for s in cell_lines if s).strip())
                out.append("| " + " | ".join(cells) + " |")
            out.append("")  # blank line after a table
        elif tag in ("sdt", "sdtContent", "body"):
            walk(child, out, depth)


def extract(path: str) -> str:
    with zipfile.ZipFile(path) as z:
        with z.open("word/document.xml") as f:
            tree = ET.parse(f)
    root = tree.getroot()
    body = root.find(f"{W}body")
    out: list[str] = []
    walk(body if body is not None else root, out)
    # collapse 3+ blank lines to 2
    lines: list[str] = []
    blanks = 0
    for ln in out:
        if ln.strip() == "":
            blanks += 1
            if blanks <= 1:
                lines.append("")
        else:
            blanks = 0
            lines.append(ln)
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    text = extract(args.docx)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"wrote {len(text)} chars -> {args.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
