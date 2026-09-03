#!/usr/bin/env python
"""Parse a PNX (Phiếu Nhận Xét) .docx into structured raw labels for the eval set.

Role in the plan
----------------
Mục 0.7. The original design took gold labels from the web-app DB
(`docs/0.7-nguon-nhan-vang.md`); that DB turned out empty, so the only remaining
grounded source is the reviewer's own words in the PNX. This script does the
MECHANICAL half of building the eval set:

  - reads "Thông tin chung" (PYC, system, purpose, requester, reviewer)  -> 0.6 metadata
  - reads each "NHẬN XÉT LẦN <n>" table                                  -> rounds (0.9)
  - splits every reviewer-comment cell into ATOMS, one per paragraph      -> raw labels (0.7)
  - lifts location anchors ("Trang 7", "Mục IV.1.1") out of each atom

What it deliberately does NOT do
--------------------------------
It does not assign `rule_ref`. Mapping a reviewer comment onto one of the 150
rules is a business decision reserved for a person (decision logged in the
briefing): a wrong mapping here silently invalidates every recall number later.
The emitted records carry `rule_ref: null` for a human to fill.

It also does not paraphrase, translate, fix spelling, or merge wrapped lines —
the atom text is verbatim, because it is the grounding of the label (NT2).

Usage
-----
    python scripts/parse_pnx.py <PNX.docx> [more.docx ...] -o out.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

ROUND_RE = re.compile(r"NH[ẬA]N\s*X[ÉE]T\s*L[ẦA]N\s*(\d+)", re.IGNORECASE)
# Location anchors the reviewer uses. Kept separate so a label can be tied to a
# spot in the sizing document without re-reading the prose.
PAGE_RE = re.compile(r"[Tt]rang\s*([\d]+(?:\s*,\s*\d+)*)")
SECTION_RE = re.compile(r"[Mm]ục\s+([IVX]+(?:\.\d+)*|\d+(?:\.\d+)+)")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def para_text(p: ET.Element) -> str:
    parts: list[str] = []
    for node in p.iter():
        t = local(node.tag)
        if t == "t":
            parts.append(node.text or "")
        elif t == "tab":
            parts.append(" ")
        elif t in ("br", "cr"):
            parts.append("\n")
    return "".join(parts).strip()


def cell_paragraphs(tc: ET.Element) -> list[str]:
    """Paragraphs of one table cell, kept SEPARATE.

    This separation is the whole point: a single comment cell routinely bundles
    several independent requests ("Bổ sung sở cứ ...", "Tính toán lại ...") and
    each maps to a different rule, so they must not be joined into one string.
    """
    out: list[str] = []
    for p in tc.iter():
        if local(p.tag) != "p":
            continue
        txt = para_text(p)
        # a hard line break inside one paragraph also separates points
        for piece in txt.split("\n"):
            piece = piece.strip()
            if piece:
                out.append(piece)
    return out


def table_rows(tbl: ET.Element) -> list[list[list[str]]]:
    """Table as rows -> cells -> paragraphs."""
    rows: list[list[list[str]]] = []
    for tr in tbl:
        if local(tr.tag) != "tr":
            continue
        cells = [cell_paragraphs(tc) for tc in tr if local(tc.tag) == "tc"]
        rows.append(cells)
    return rows


# A cell paragraph is not always a request. Three mechanical kinds:
#   anchor  — a bare pointer ("Trang 1", "Mục IV.1.1: Định cỡ máy chủ BigData")
#   lead    — an opener whose object is in the paragraphs below ("Bổ sung sở cứ:")
#   request — an actual requirement from the reviewer; ONLY these become labels
# Counting anchors and leads as labels would inflate the recall denominator with
# rows the Copilot was never meant to reproduce.
BARE_PAGE_RE = re.compile(r"^[\(\-\s]*[Tt]rang\s*\d+(\s*[,;]\s*\d+)*\s*[\):.]*$")
BARE_SECTION_RE = re.compile(
    r"^[Mm]ục\s*[:.]"                      # "Mục: thông tin đầu vào"
    r"|^[Mm]ục\s+([IVX]+(\.\d+)*|\d+(\.\d+)+)\s*[:.]?\s*.{0,80}$"
    r"|^[Mm]ục\s+\S.{0,60}$"               # "Mục thông tin đầu vào chi tiết"
    r"|^[IVX]+\s*\.\s+\S"                  # "III. THÔNG TIN THIẾT KẾ (trang 9)"
    # "5.1.3 Định cỡ module PostgreSQL" — the word after the number must start
    # with a capital: "2.9 tỉ bản ghi" is a data point, not section 2.9.
    r"|^\d+(\.\d+)+\s+[A-ZÀ-Ỹ].{0,70}$")
# Headings are told apart from requests by the ABSENCE of a strong imperative.
# Deliberately does not contain bare "tính": "2.5 Cơ sở tính toán định cỡ" is a
# heading, and "tính" inside "tính toán" would otherwise keep it as a request.
STRONG_VERB_RE = re.compile(
    r"\b(bổ sung|sửa|làm rõ|lập|bỏ|cập nhật|giải thích|xem lại|không có|chưa có|"
    r"không đúng|sai|tại sao|kiểm tra|đánh giá|áp dụng|trình bày|tính lại|tính toán lại)\b",
    re.IGNORECASE)
# Pure section titles observed in the PNX corpus. Listed explicitly rather than
# inferred from "short line with no verb": that heuristic was tried and dropped —
# it swallowed real requests ("Sở cứ sử dụng ssd", "Lưu ý giá trị N+1") whose
# verbs are nouns. Losing a real reviewer finding is worse than letting a heading
# through, because a missing label is a finding the Copilot can never be credited
# for, while a stray heading gets no rule match and is caught in review.
PURE_HEADING_RE = re.compile(
    r"^(thông tin (hệ thống|đầu vào|thiết kế)( chi tiết| test)?|đề xuất tài nguyên|"
    r"giải pháp thiết kế|yêu cầu bài toán|định cỡ (hệ thống|thiết bị máy chủ))\s*[:.]?$",
    re.IGNORECASE)
GENERIC_LEAD_RE = re.compile(r"^(Nhận xét chung|Nhận xét)\s*:?\s*$", re.IGNORECASE)


VERB_RE = re.compile(
    r"\b(bổ sung|tính|sửa|làm rõ|lập|bỏ|cập nhật|giải thích|đánh giá|áp dụng|"
    r"trình bày|xem lại|không có|chưa có|không đúng|sai|tại sao|kiểm tra)\b",
    re.IGNORECASE)


def classify(text: str) -> str:
    t = text.strip()
    if BARE_PAGE_RE.match(t) or GENERIC_LEAD_RE.match(t):
        return "anchor"
    if PURE_HEADING_RE.match(t):
        return "anchor"
    # "Mục IV.1.1: <tên mục>" / "5.1.3 Định cỡ module PostgreSQL" is a heading
    # only when it carries no strong imperative and asks no question
    if BARE_SECTION_RE.match(t) and not STRONG_VERB_RE.search(t) and "?" not in t:
        return "anchor"
    # Checked AFTER the heading tests but BEFORE anything else: an opener like
    # "Định cỡ máy chủ worker:" carries the context for the atoms beneath it, so
    # it must become a lead, never be discarded as a heading.
    if t.endswith(":"):
        return "lead"
    return "request"


def anchors(text: str) -> dict:
    pages: list[int] = []
    for m in PAGE_RE.finditer(text):
        for num in re.findall(r"\d+", m.group(1)):
            pages.append(int(num))
    sections = SECTION_RE.findall(text)
    return {"pages": sorted(set(pages)), "sections": sections}


def is_comment_table(rows: list[list[list[str]]]) -> bool:
    if not rows:
        return False
    header = " ".join(" ".join(c) for c in rows[0]).lower()
    return "nhận xét" in header and ("stt" in header or "phản hồi" in header)


def is_info_table(rows: list[list[list[str]]]) -> bool:
    if not rows:
        return False
    first = " ".join(" ".join(c) for c in rows[0]).lower()
    return "mã pyc" in first


def parse(path: str) -> dict:
    with zipfile.ZipFile(path) as z:
        tree = ET.parse(z.open("word/document.xml"))
    body = tree.getroot().find(f"{W}body")

    info: dict[str, str] = {}
    rounds: list[dict] = []
    current_round: int | None = None

    for child in body:
        tag = local(child.tag)
        if tag == "p":
            m = ROUND_RE.search(para_text(child))
            if m:
                current_round = int(m.group(1))
        elif tag == "tbl":
            rows = table_rows(child)
            if is_info_table(rows):
                for cells in rows:
                    if len(cells) >= 2:
                        key = " ".join(cells[0]).strip()
                        val = " ".join(cells[1]).strip()
                        if key:
                            info[key] = val
            elif is_comment_table(rows):
                items: list[dict] = []
                for cells in rows[1:]:  # skip header
                    if len(cells) < 2:
                        continue
                    stt = " ".join(cells[0]).strip()
                    atoms = cells[1]
                    response = " ".join(cells[2]).strip() if len(cells) > 2 else ""
                    if not atoms:
                        continue
                    items.append({"stt": stt, "atoms": atoms, "response": response})
                rounds.append({"round": current_round, "items": items})

    return {"file": os.path.basename(path), "info": info, "rounds": rounds}


def to_labels(parsed: dict, dossier: str) -> list[dict]:
    """Flatten into one record per atom — the raw label rows a person will map."""
    labels: list[dict] = []
    pyc = parsed["info"].get("Mã PYC IBM, Jira") or parsed["info"].get("Mã PYC") or ""
    # A dossier often holds several PNX versions (v1..v4), and a later PNX usually
    # REPEATS the earlier rounds' tables. Tagging every label with its source file
    # is what makes de-duplication across versions possible afterwards.
    src = os.path.splitext(parsed["file"])[0]
    for rnd in parsed["rounds"]:
        # A subsystem opener often sits ALONE in its own table row ("Định cỡ máy
        # chủ Redis:") with the requests in the rows beneath it. Carrying it only
        # within a cell lost that context: five "Công thức tính không đúng" rows
        # in Vtag became indistinguishable although each targets a different
        # server. So a row that is nothing but an opener sets the context for the
        # rows that follow, until the next opener or section heading.
        row_lead = ""
        for item_idx, item in enumerate(rnd["items"], start=1):
            kinds = [classify(x) for x in item["atoms"]]
            # first atom is an opener -> it governs the rows below, whether or
            # not more text follows it inside the same cell
            if kinds and kinds[0] == "lead":
                row_lead = item["atoms"][0]
            elif kinds and kinds[0] == "anchor":
                row_lead = ""
            # An atom that is only a heading ("Nhận xét chung:", "Mục IV.1.1: ...")
            # still carries the anchor for the atoms that follow it.
            carried = anchors(" ".join(item["atoms"][:1]))
            lead = row_lead  # nearest opener above, so a request keeps its object
            for atom_idx, atom in enumerate(item["atoms"], start=1):
                a = anchors(atom)
                kind = classify(atom)
                if kind == "lead":
                    lead = atom
                elif kind == "anchor":
                    lead = ""
                labels.append({
                    "label_id": f"{src}|R{rnd['round']}-{item_idx:02d}-{atom_idx:02d}",
                    "dossier": dossier,
                    "pnx_file": parsed["file"],
                    "pyc": pyc,
                    "round": rnd["round"],
                    "item_no": item["stt"] or str(item_idx),
                    "kind": kind,                       # only "request" is a label
                    "text": atom,                       # verbatim, NT2 grounding
                    "context_lead": lead if kind == "request" else "",
                    "pages": a["pages"] or carried["pages"],
                    "sections": a["sections"] or carried["sections"],
                    "unit_response": item["response"],
                    # --- to be filled by a person, never by AI ---
                    "rule_ref": None,
                    "checklist_ref": None,
                    "vong": None,        # 1 = checklist completeness, 2 = Guideline calculation
                    "note": None,
                })
    return labels


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--root", help="thư mục gốc chứa các thư mục hồ sơ; tên hồ sơ "
                                   "lấy ở cấp NGAY DƯỚI root, bỏ qua thư mục lồng "
                                   "(sr/, Ver2/, New folder/, daky/…)")
    args = ap.parse_args()

    all_parsed, all_labels, skipped = [], [], []
    for path in args.docx:
        if args.root:
            rel = os.path.relpath(path, args.root)
            dossier = rel.replace("\\", "/").split("/")[0]
        else:
            dossier = os.path.basename(os.path.dirname(path))
        try:
            p = parse(path)
        except Exception as exc:  # a stray/corrupt .docx must not kill the batch
            skipped.append((path, f"{type(exc).__name__}: {exc}"))
            continue
        if not p["rounds"]:
            # not a PNX (công văn, phiếu giải trình…) or a layout we cannot read —
            # report it rather than silently dropping it (NT4)
            skipped.append((path, "không thấy bảng 'NHẬN XÉT LẦN n'"))
            continue
        p["dossier"] = dossier
        all_parsed.append(p)
        all_labels.extend(to_labels(p, dossier))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"dossiers": all_parsed, "labels": all_labels}, f,
                  ensure_ascii=False, indent=2)

    sys.stdout.reconfigure(encoding="utf-8")
    n_req = sum(1 for l in all_labels if l["kind"] == "request")
    print(f"{len(all_parsed)} PNX -> {len(all_labels)} atoms, "
          f"trong đó {n_req} là NHÃN (kind=request) -> {args.out}")
    for p in all_parsed:
        rows = [l for l in all_labels if l["pnx_file"] == p["file"]
                and l["dossier"] == p["dossier"]]
        req = sum(1 for l in rows if l["kind"] == "request")
        rr = ", ".join(str(r["round"]) for r in p["rounds"])
        print(f"  {p['dossier'][:38]:<38} | {p['file'][:44]:<44} lần [{rr}] nhãn {req:>3}")
    if skipped:
        print(f"\n⚠️  BỎ QUA {len(skipped)} file:")
        for path, why in skipped:
            print(f"  {os.path.basename(path)[:60]:<60} {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
