#!/usr/bin/env python
"""So sánh hai lần ban hành Guideline định cỡ để tìm quy tắc bị thêm/sửa/bỏ.

Bối cảnh
--------
Mỗi lần Guideline ra bản mới, 100 quy tắc đã số hóa (docs/rules/) phải được rà
lại. Đọc tay 44 trang để tìm chỗ khác nhau vừa chậm vừa dễ sót, nên script này
lọc bỏ phần lặp lại (đầu trang, chân trang, chữ ký) rồi diff phần thân bài.

Hai bản phải được trích bằng `scripts/extract_pdf_text.py` trước.

Cách dùng
---------
    uv run python scripts/diff_guideline.py <cu/clean.txt> <moi/clean.txt>
    uv run python scripts/diff_guideline.py ... --context 2
    uv run python scripts/diff_guideline.py ... --numbers-only

`--numbers-only` chỉ so các dòng có chứa số — dùng để soát nhanh ngưỡng và hệ
số, là thứ ảnh hưởng trực tiếp tới quy tắc định lượng (C4).

Lưu ý
-----
Script chỉ ra chỗ **khác nhau về câu chữ**. Việc kết luận một thay đổi có làm
đổi quy tắc hay không vẫn là việc của người đọc — xem docs/rules/rules-crossmap.md.
"""

from __future__ import annotations

import argparse
import difflib
import pathlib
import re
import sys
import unicodedata

PAGE_RE = re.compile(r"^=====\s*TRANG\s+(\d+)\s*=====$")

# Dòng lặp lại ở mọi trang: đầu trang, chân trang, dấu vết ký số.
BOILERPLATE = [
    re.compile(r"^TẬP ĐOÀN CÔNG NGHIỆP.*Mã hiệu:"),
    re.compile(r"^GUIDELINE ĐỊNH CỠ"),
    re.compile(r"^CẤP PHÁT HẠ TẦNG"),
    re.compile(r"^CÔNG NGHỆ THÔNG TIN$"),
    re.compile(r"^Ngày (có|hết) hiệu lực:"),
    re.compile(r"^Lần ban hành:"),
    re.compile(r"^Trang:\s*\d+\s*/\s*\d+"),
    re.compile(r"^Tài liệu này thuộc sở hữu của Viettel"),
    re.compile(r"^Số và ký hiệu:"),
    re.compile(r"^Thời gian ký:"),
    re.compile(r"^Ngày ban hành:"),
]

HAS_DIGIT = re.compile(r"\d")

# Hai lần trích biểu diễn bullet khác nhau (SymbolMT/Wingdings ánh xạ khác nhau),
# nên phải bỏ dấu đầu dòng trước khi so — nếu không, diff đầy khác biệt hình thức
# và che mất thay đổi nội dung thật.
# -: bullet Wingdings/Symbol chưa được quy đổi. Bản trích cũ (máy khác)
# đổi U+F0FC thành 'ü', bản trích mới đổi thành '-' — phải bỏ cả hai dạng.
LEAD_PUNCT = re.compile(r"^[\s\-–—•▪◦○§*+·-]+")
# 'o', 'ü', 'v' là bullet của font biểu tượng; chỉ bỏ khi đứng trước chữ HOA để
# không cắt nhầm từ tiếng Việt bắt đầu bằng các chữ đó.
LEAD_BULLET_CHAR = re.compile(r"^[oüv]\s*(?=[A-ZĐÀ-Ỹ])")


def norm(s: str, strip_bullets: bool = True) -> str:
    s = unicodedata.normalize("NFC", s)
    s = s.replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if strip_bullets:
        prev = None
        while prev != s:  # bullet lồng nhau, ví dụ "- o Nội dung"
            prev = s
            s = LEAD_PUNCT.sub("", s)
            s = LEAD_BULLET_CHAR.sub("", s)
    return s


# Bản trích cũ (làm trên máy khác) ánh xạ ký tự PUA của font Symbol sang Latin-1,
# nên "≤" ra thành "£", "≥" ra thành "³", dấu tích Wingdings ra thành "ü".
# Sửa lại để so đúng — CHỈ áp cho file cũ, tránh phá nội dung file mới.
LEGACY_SYMBOL_FIX = {"£": "≤", "³": "≥", "ü": "-"}


def repair_legacy(line: str) -> str:
    for src, dst in LEGACY_SYMBOL_FIX.items():
        line = line.replace(src, dst)
    return line


def key_of(line: str) -> str:
    """Khóa so khớp: bỏ hết khoảng trắng.

    Hai bản trích ngắt span khác nhau nên chỗ có/không có dấu cách lệch nhau rất
    nhiều ("1. Mục đích" vs "1.Mục đích"). So theo khóa này thì khác biệt thuần
    khoảng trắng biến mất, chỉ còn thay đổi câu chữ thật.
    """
    return re.sub(r"\s+", "", line)


def load(
    path: pathlib.Path, numbers_only: bool = False, legacy: bool = False
) -> list[tuple[int, str]]:
    """Trả về [(số trang, dòng đã chuẩn hóa)], đã bỏ phần lặp lại."""
    out: list[tuple[int, str]] = []
    page = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        m = PAGE_RE.match(raw.strip())
        if m:
            page = int(m.group(1))
            continue
        line = norm(repair_legacy(raw) if legacy else raw)
        if not line:
            continue
        if any(p.match(line) for p in BOILERPLATE):
            continue
        if numbers_only and not HAS_DIGIT.search(line):
            continue
        out.append((page, line))
    return out


def report(old, new, context: int) -> int:
    old_txt = [t for _, t in old]
    new_txt = [t for _, t in new]
    # So khớp theo khóa (đã bỏ khoảng trắng), nhưng in ra nguyên văn để đọc.
    sm = difflib.SequenceMatcher(
        None, [key_of(t) for t in old_txt], [key_of(t) for t in new_txt],
        autojunk=False,
    )

    n_add = n_del = n_chg = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue

        if tag == "replace":
            n_chg += 1
            head = "SỬA"
        elif tag == "delete":
            n_del += 1
            head = "BỎ"
        else:
            n_add += 1
            head = "THÊM"

        pg_old = f"tr.{old[i1][0]}" if i1 < len(old) else "-"
        pg_new = f"tr.{new[j1][0]}" if j1 < len(new) else "-"
        print(f"\n=== {head}  (cũ {pg_old} / mới {pg_new}) ===")

        if context and i1 > 0:
            print(f"    … {old_txt[i1 - 1][:100]}")
        for t in old_txt[i1:i2]:
            print(f"  - {t}")
        for t in new_txt[j1:j2]:
            print(f"  + {t}")
        if context and i2 < len(old_txt):
            print(f"    … {old_txt[i2][:100]}")

    print(
        f"\n---\nTổng: {n_add} khối THÊM · {n_del} khối BỎ · {n_chg} khối SỬA"
        f"  |  cũ {len(old_txt)} dòng, mới {len(new_txt)} dòng"
        f"  |  giống nhau {sm.ratio():.1%}"
    )
    return n_add + n_del + n_chg


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("old", type=pathlib.Path, help="clean.txt bản cũ")
    ap.add_argument("new", type=pathlib.Path, help="clean.txt bản mới")
    ap.add_argument("--context", type=int, default=1)
    ap.add_argument(
        "--numbers-only",
        action="store_true",
        help="chỉ so các dòng có chứa số (ngưỡng, hệ số)",
    )
    args = ap.parse_args()

    for p in (args.old, args.new):
        if not p.is_file():
            sys.exit(f"Không tìm thấy: {p}")

    old = load(args.old, args.numbers_only, legacy=True)
    new = load(args.new, args.numbers_only)
    report(old, new, args.context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
