#!/usr/bin/env python
"""Generate the dossier metadata table for 0.6 — regenerable, never hand-typed.

Reads the parser output and the folder tree, writes a Markdown table. Kept as a
separate generated file so re-running after a new batch of dossiers cannot
introduce transcription errors into the hand-written analysis.

Usage
-----
    python scripts/make_dossier_report.py --root danh_sach_sizings_da_duyet \
        --raw data/pnx_raw_labels.json --dedup data/pnx_labels_dedup.json \
        -o docs/0.6-bang-metadata.md
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

# files that are not the sizing document itself
NOT_SIZING = re.compile(
    r"PNX|Phản hồi PNX|Cong van|Phieu giai trinh|PYC |guideline|^GL\.|HSTK|QLTN|"
    r"checklist|yeu_cau_cap_phat|baocaocapphat|excel-list|passwords|Xin_cap_phat|"
    r"mẫu|mau_HSTK|ghichu", re.I)


def sizing_files(folder: str) -> list[str]:
    out = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.startswith("~$") or not f.lower().endswith((".docx", ".pdf")):
                continue
            if NOT_SIZING.search(f):
                continue
            out.append(os.path.relpath(os.path.join(root, f), folder).replace("\\", "/"))
    return sorted(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--dedup", required=True)
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    raw = json.load(open(args.raw, encoding="utf-8"))
    kept = json.load(open(args.dedup, encoding="utf-8"))["labels"]

    n_lab = collections.Counter(l["dossier"] for l in kept)
    rounds = collections.defaultdict(set)
    for l in kept:
        rounds[l["dossier"]].add(l["round"])

    info: dict[str, dict] = {}
    npnx: collections.Counter = collections.Counter()
    for p in raw["dossiers"]:
        npnx[p["dossier"]] += 1
        if p["dossier"] not in info or len(p["info"]) > len(info[p["dossier"]]):
            info[p["dossier"]] = p["info"]

    folders = sorted(d for d in os.listdir(args.root)
                     if os.path.isdir(os.path.join(args.root, d)))

    lines: list[str] = []
    lines.append("# 0.6 — Bảng metadata hồ sơ (TỰ SINH)\n")
    lines.append("> ⚠️ File này do `scripts/make_dossier_report.py` sinh ra. "
                 "**Không sửa tay** — sửa sẽ mất khi chạy lại.\n")
    lines.append(f"> Nguồn: `{args.root}/` · {len(folders)} hồ sơ · "
                 f"{sum(n_lab.values())} nhãn sau khử trùng.\n")

    lines.append("\n## Hồ sơ có nhãn\n")
    lines.append("| Hồ sơ | Mã PYC (theo PNX) | Tên hệ thống | Đầu mối yêu cầu | "
                 "Đầu mối thẩm định | Lần NX | Nhãn | Số PNX | Bản sizing |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    total = 0
    for d in folders:
        if not n_lab.get(d):
            continue
        i = info.get(d, {})
        pyc = i.get("Mã PYC IBM, Jira") or i.get("Mã PYC") or "—"
        name = i.get("Tên hệ thống") or "—"
        yc = i.get("Đầu mối yêu cầu") or "—"
        td = i.get("Đầu mối thẩm định") or "—"
        td = td.split(":")[-1].strip() if ":" in td else td
        rr = ", ".join(str(x) for x in sorted(rounds[d]))
        nsz = len(sizing_files(os.path.join(args.root, d)))
        total += n_lab[d]
        lines.append(f"| `{d}` | {pyc} | {name} | {yc} | {td} | {rr} | "
                     f"**{n_lab[d]}** | {npnx[d]} | {nsz} |")
    lines.append(f"| **TỔNG** | | | | | | **{total}** | | |")

    missing = [d for d in folders if not n_lab.get(d)]
    if missing:
        lines.append("\n## Hồ sơ KHÔNG có nhãn — cần bổ sung\n")
        lines.append("| Hồ sơ | Vì sao | File đang có |")
        lines.append("|---|---|---|")
        for d in missing:
            files = []
            for root, _, fs in os.walk(os.path.join(args.root, d)):
                files += [f for f in fs if f.lower().endswith((".docx", ".pdf"))]
            has_pnx_pdf = any(re.search("PNX", f, re.I) and f.lower().endswith(".pdf")
                              for f in files)
            has_pnx_docx = any(re.search("PNX", f, re.I) and f.lower().endswith(".docx")
                               for f in files)
            if has_pnx_docx:
                why = "PNX `.docx` có nhưng không đọc được bảng 'NHẬN XÉT LẦN n'"
            elif has_pnx_pdf:
                why = "**PNX chỉ có bản PDF** — bộ phân tích chỉ đọc `.docx`"
            else:
                why = "**không có PNX**"
            lines.append(f"| `{d}` | {why} | {', '.join(sorted(files)[:4])} |")

    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"{len(folders)} hồ sơ, {total} nhãn -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
