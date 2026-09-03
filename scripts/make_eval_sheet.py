#!/usr/bin/env python
"""Emit the human-fillable sheet for assigning `rule_ref` to PNX labels (0.7).

The parser (`parse_pnx.py`) produces raw labels straight from the reviewer's
words. Turning each one into a gold label needs a decision this tool must not
make: which of the 150 rules the comment corresponds to. That mapping is
reserved for a person — an AI guess here would quietly poison every recall
number computed afterwards.

So this writes a CSV with the mechanical columns pre-filled and the judgment
columns left empty:

    filled by script : label_id, dossier, pyc, round, item_no, trang, muc,
                       noi_dung_nhan_xet (verbatim), phan_hoi_don_vi
    filled by person : rule_ref, checklist_ref, vong, ngoai_pham_vi, ghi_chu

`vong` is 1 (checklist — "is the required part present at all?") or 2
(Guideline — "is the calculation right?"), per the two-round model. Note this is
NOT the "NHẬN XÉT LẦN n" of the PNX, which counts feedback iterations; that is
the `round` column.

Written UTF-8 with BOM so Excel on Windows opens Vietnamese correctly.

Usage
-----
    python scripts/make_eval_sheet.py data/pnx_raw_labels.json -o data/eval_sheet.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys

COLUMNS = [
    "label_id", "dossier", "pyc", "pnx_file", "lan_nhan_xet", "item_no",
    "trang", "muc", "noi_dung_nhan_xet", "phan_hoi_don_vi",
    # --- máy gợi ý (scripts/suggest_rule_refs.py) ---
    "rule_ref_goi_y", "do_tin_cay", "can_cu_goi_y", "ghi_chu_goi_y",
    # --- người nghiệp vụ điền ---
    "da_kiem", "goi_y_dung", "rule_ref", "checklist_ref", "vong",
    "ngoai_pham_vi", "ghi_chu",
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("labels_json")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--include-all", action="store_true",
                    help="also emit anchor/lead rows (default: only kind=request)")
    ap.add_argument("--sample-out",
                    help="ghi thêm PHIẾU LẤY MẪU KIỂM: mẫu ngẫu nhiên phân tầng "
                         "theo do_tin_cay, để ước lượng độ chính xác từng mức")
    ap.add_argument("--sample-per-tier", type=int, default=15)
    ap.add_argument("--seed", type=int, default=20260903)
    ap.add_argument("--sample-ids", default="data/audit_sample_ids.json",
                    help="mẫu ĐÓNG BĂNG: lần đầu ghi label_id đã chọn vào đây, các "
                         "lần sau đọc lại thay vì rút mẫu mới")
    args = ap.parse_args()

    data = json.load(open(args.labels_json, encoding="utf-8"))
    rows = data["labels"]
    if not args.include_all:
        rows = [r for r in rows if r["kind"] == "request"]

    out_rows: list[dict] = []
    for r in rows:
        # a request keeps its opener so the requirement is readable alone
        text = r["text"]
        if r.get("context_lead"):
            text = f'{r["context_lead"]} {text}'
        out_rows.append({
                "label_id": r["label_id"],
                "dossier": r["dossier"],
                "pyc": r["pyc"],
                "pnx_file": r.get("pnx_file", ""),
                "lan_nhan_xet": r["round"],
                "item_no": r["item_no"],
                "trang": ", ".join(str(p) for p in r["pages"]),
                "muc": ", ".join(r["sections"]),
                "noi_dung_nhan_xet": text,
                "phan_hoi_don_vi": r["unit_response"],
                "rule_ref_goi_y": "; ".join(r.get("rule_ref_goi_y") or []),
                "do_tin_cay": r.get("do_tin_cay", ""),
                "can_cu_goi_y": r.get("can_cu_goi_y", ""),
                "ghi_chu_goi_y": r.get("ghi_chu_goi_y", ""),
                # left for the reviewer: da_kiem = row was audited,
                # goi_y_dung = Đ/S verdict on the machine suggestion
                "da_kiem": "", "goi_y_dung": "",
                "rule_ref": "", "checklist_ref": "", "vong": "",
                "ngoai_pham_vi": "", "ghi_chu": "",
        })

    with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(out_rows)

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{len(rows)} nhãn -> {args.out}")
    print("Cột máy gợi ý: rule_ref_goi_y, do_tin_cay, can_cu_goi_y")
    print("Cột người điền: da_kiem, goi_y_dung, rule_ref, checklist_ref, vong, …")

    if args.sample_out:
        # Stratified, not simple random: the tiers have very different accuracy,
        # so a flat sample would tell you little about the weak ones. Sampling a
        # fixed number per tier lets each tier's accuracy be estimated on its own,
        # and the whole-corpus figure be recombined by tier weight afterwards.
        import os
        import random
        by_id = {r["label_id"]: r for r in out_rows}
        picked: list[dict] = []
        # FROZEN SAMPLE. Every re-run of the parser or the classifier shifts the
        # tier populations, and a seeded draw over shifted populations is a new
        # draw — the audited sample was re-drawn twice before this, throwing away
        # verdicts each time. So the chosen ids are written once and reused; rows
        # that no longer exist (e.g. re-classified as headings) simply drop out.
        if os.path.exists(args.sample_ids):
            ids = json.load(open(args.sample_ids, encoding="utf-8"))
            picked = [by_id[i] for i in ids if i in by_id]
            gone = [i for i in ids if i not in by_id]
            print(f"\nPhiếu lấy mẫu: dùng lại {len(picked)} id đã đóng băng ở "
                  f"{args.sample_ids}" + (f" ({len(gone)} id không còn tồn tại)" if gone else ""))
        else:
            rnd = random.Random(args.seed)
            by_tier: dict[str, list[dict]] = {}
            for r in out_rows:
                by_tier.setdefault(r.get("do_tin_cay", ""), []).append(r)
            print(f"\nPhiếu lấy mẫu (seed={args.seed}):")
            for tier in sorted(by_tier):
                pool = by_tier[tier]
                k = min(args.sample_per_tier, len(pool))
                picked += rnd.sample(pool, k)
                print(f"   {tier:<16} lấy {k:>3} / {len(pool):>3}")
            json.dump([r["label_id"] for r in picked],
                      open(args.sample_ids, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"   đã đóng băng {len(picked)} id -> {args.sample_ids}")
        tier_count: dict[str, int] = {}
        for r in picked:
            tier_count[r["do_tin_cay"]] = tier_count.get(r["do_tin_cay"], 0) + 1
        for tier in sorted(tier_count):
            print(f"   {tier:<16} {tier_count[tier]:>3}")
        with open(args.sample_out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(picked)
        print(f"   -> {args.sample_out}  ({len(picked)} dòng)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
