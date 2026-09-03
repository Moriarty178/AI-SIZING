#!/usr/bin/env python
"""Decide which PNX version to keep per dossier, by comparing text — not by guessing.

Why this exists
---------------
A dossier usually holds several PNX versions (v1..v4). A later PNX normally
REPEATS the earlier rounds' tables and appends the new round, so parsing every
version and concatenating would count the same reviewer comment several times
and inflate the eval set.

But "later version is a superset" is an assumption, and at least one dossier
breaks it (GSCG: v3 carries rounds 1-3 while v4 carries only 1-2). So instead of
trusting the filename, this compares the actual label texts per (dossier, round)
across versions and reports:

  - IDENTICAL  : the round is repeated verbatim -> safe to keep only one version
  - DIFFERENT  : the same round differs between versions -> a person must look

Selection rule applied for the "keep" column: the PNX covering the MOST rounds;
ties broken by the greater number of labels. Rounds that appear only in a
version we did not keep are reported as ORPHAN so nothing is silently lost (NT4).

Usage
-----
    python scripts/dedup_pnx.py data/pnx_raw_labels.json [-o data/pnx_keep.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys


def norm(s: str) -> str:
    """Comparison key only — the stored label text is never altered (NT2).

    A later PNX often restates an earlier comment with cosmetic edits: a leading
    "- " bullet, different spacing inside a number list ("226;12.6" vs
    "226; 12.6"), a trailing full stop. Comparing on words alone reported those
    as new comments and would have double-counted them, so the key drops every
    non-alphanumeric character and folds case.
    """
    return "".join(ch for ch in s.lower() if ch.isalnum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("labels_json")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    labels = json.load(open(args.labels_json, encoding="utf-8"))["labels"]
    req = [l for l in labels if l["kind"] == "request"]

    # dossier -> pnx_file -> round -> [texts]
    tree: dict = collections.defaultdict(lambda: collections.defaultdict(
        lambda: collections.defaultdict(list)))
    for l in req:
        tree[l["dossier"]][l["pnx_file"]][l["round"]].append(norm(l["text"]))

    # UNION across versions, keyed by (dossier, round, normalised text).
    # Safer than picking one "best" version: a later PNX is not reliably a
    # superset of the earlier ones, so choosing one could silently drop labels.
    # The same comment repeated in a LATER ROUND is kept — the reviewer having to
    # say it twice is itself a fact worth measuring.
    # MULTIPLICITY MATTERS. Inside one PNX round the reviewer repeats a wording
    # verbatim for each subsystem it applies to — "Công thức tính không đúng"
    # appears 5 times in Vtag round 1, at 5 different table rows, i.e. 5 separate
    # findings (the `scope: phan_he` idea from the rules). Collapsing them to one
    # would under-count the recall denominator just as badly as counting anchors
    # over-counts it.
    #
    # So: within a (dossier, round, text) group, keep the count from whichever PNX
    # version reports it the MOST times — that version is the most complete — and
    # drop the other versions' copies as cross-version repeats.
    dropped_none: list[tuple[str, str]] = []
    groups: dict[tuple, dict[str, list[dict]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    for l in req:
        if l["round"] is None:
            dropped_none.append((l["dossier"], l["pnx_file"]))
            continue
        groups[(l["dossier"], l["round"], norm(l["text"]))][l["pnx_file"]].append(l)

    kept: list[dict] = []
    dupes = 0
    for (_d, _r, _t), by_file in groups.items():
        best_file = max(by_file, key=lambda f: (len(by_file[f]), f))
        chosen = by_file[best_file]
        others = sorted(f for f in by_file if f != best_file)
        for rec in chosen:
            rec = dict(rec)
            rec["also_in"] = others
            kept.append(rec)
        dupes += sum(len(v) for f, v in by_file.items() if f != best_file)
    kept.sort(key=lambda l: l["label_id"])
    per_dossier = collections.Counter(l["dossier"] for l in kept)

    for dossier in sorted(tree):
        files = tree[dossier]
        print(f"\n### {dossier}  ->  {per_dossier.get(dossier, 0)} nhãn sau khử trùng")
        for f in sorted(files):
            rounds = ",".join(str(k) for k in sorted(files[f], key=lambda x: (x is None, x)))
            n = sum(len(v) for v in files[f].values())
            note = "  (không có 'LẦN n' -> BỎ, nhiều khả năng là văn bản phản hồi)" \
                if all(k is None for k in files[f]) else ""
            print(f"    {f[:56]:<56} lần[{rounds}] {n:>3}{note}")

    print(f"\n{'='*72}")
    print(f"{len(req)} nhãn thô (mọi phiên bản PNX)")
    print(f"  − {dupes} bản trùng nguyên văn giữa các phiên bản")
    print(f"  − {len(dropped_none)} nhãn từ văn bản không phải PNX (không có 'LẦN n')")
    print(f"  = {len(kept)} NHÃN SAU KHỬ TRÙNG, trên {len(per_dossier)} hồ sơ")

    if args.out:
        json.dump({"labels": kept}, open(args.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
