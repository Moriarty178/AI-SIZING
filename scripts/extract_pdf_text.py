#!/usr/bin/env python
"""Trích text từ PDF Guideline định cỡ, lọc watermark và chữ ký số.

Bối cảnh
--------
Các bản Guideline được ký số nên mỗi trang bị chèn thêm chữ ký, dấu và dòng
sở hữu. Những thứ đó dùng font khác hẳn thân bài, nên lọc theo **font** cho kết
quả sạch hơn nhiều so với lọc theo vị trí hay theo biểu thức chuỗi — text layer
của thân bài giữ nguyên vẹn, không phải dùng tới OCR.

Kết quả trích là nguồn `rule_quote` (trích dẫn nguyên văn) cho các quy tắc định
tính. Theo NT2 đó là căn cứ duy nhất của nhóm quy tắc này, nên script cố ý
KHÔNG sửa chữ: không tự nối dòng, không sửa chính tả, không bỏ dấu.

Cách dùng
---------
    uv run python scripts/extract_pdf_text.py <file.pdf> -o docs/rules/.tmp
    uv run python scripts/extract_pdf_text.py <file.pdf> --probe-fonts

Đầu ra
------
    <outdir>/clean.txt       text đã lọc watermark  — dùng để trích dẫn
    <outdir>/raw-layout.txt  text giữ bố cục gốc    — dùng khi cần đọc bảng

Cả hai file đánh dấu ranh giới trang bằng `===== TRANG n =====`, với `n` là
**số trang vật lý** của PDF. Lưu ý số này thường lệch 1 so với số trang in ở
chân tài liệu (`Trang: n/44`) — khi ghi `source_doc` phải dùng số in trên tài
liệu, xem docs/rules/rules-criteria.md.
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import sys

try:
    import pymupdf
except ImportError:  # pragma: no cover
    sys.exit("Thiếu pymupdf. Cài bằng: uv add pymupdf  (hoặc pip install pymupdf)")

PAGE_MARK = "===== TRANG {} ====="

# Font của chữ ký số / watermark / dòng sở hữu. Thân bài Guideline dùng
# TimesNewRoman (văn xuôi) và CourierNew (khối lệnh, kết quả benchmark).
# Chạy --probe-fonts trên tài liệu mới trước khi tin vào danh sách này.
WATERMARK_FONTS = {"ArialMT", "Arial-BoldMT"}

# Bullet của SymbolMT/Wingdings nằm trong vùng Private Use Area (U+E000-U+F8FF):
# ví dụ U+F0B7 (chấm tròn), U+F0A7 (ô vuông), U+F0FC (dấu tích). Chúng KHÔNG phải
# chữ thật - mỗi bộ đọc PDF ánh xạ một kiểu, nên phải quy về một ký tự thống nhất,
# nếu không hai lần trích cùng một tài liệu sẽ khác nhau ở hàng chục dòng.
PUA_START, PUA_END = 0xE000, 0xF8FF
BULLET = "-"

# CẢNH BÁO: không phải ký tự PUA nào cũng là bullet. Font Symbol dùng chính vùng
# này cho TOÁN TỬ SO SÁNH — U+F0A3 là "≤", U+F0B3 là "≥". Quy tất cả về "-" sẽ
# phá hỏng đúng những ngưỡng mà quy tắc định lượng dựa vào, ví dụ R13
# ("≤ 32 vCPU và ≤ 128GB RAM") và R68 ("≥ 75%"). Vì vậy phải ánh xạ THEO FONT.
#
# Khóa là mã ký tự gốc của font (codepoint - 0xF000), theo bảng mã Adobe Symbol.
SYMBOL_PUA = {
    0x2D: "−",  # minus
    0xA3: "≤",
    0xA5: "∞",
    0xAC: "←",
    0xAE: "→",
    0xB1: "±",
    0xB3: "≥",
    0xB4: "×",
    0xB7: BULLET,  # chấm tròn — dùng làm bullet
    0xB8: "÷",
    0xB9: "≠",
    0xBB: "↔",
    0xD6: "√",
    0xE5: "∑",
}

# Wingdings dùng vùng PUA cho ký hiệu trang trí; tất cả đều đóng vai trò bullet.
WINGDINGS_PUA = {
    0xA7: BULLET,  # ô vuông nhỏ
    0xA8: BULLET,
    0xFC: BULLET,  # dấu tích
    0xFE: BULLET,
}

SYMBOL_FONTS = {"SymbolMT", "Symbol"}
WINGDINGS_FONTS = {"Wingdings-Regular", "Wingdings", "Wingdings2", "Wingdings3"}


def normalize_symbols(
    text: str, font: str | None = None, unmapped: collections.Counter | None = None
) -> str:
    """Quy ký tự PUA của font biểu tượng về Unicode chuẩn.

    `font` là tên font của span. Không truyền font (ví dụ khi trích theo bố cục,
    lúc đó không còn thông tin font) thì dùng bảng gộp — an toàn với tài liệu này
    vì Symbol và Wingdings không dùng trùng mã, nhưng kém chắc chắn hơn.
    """
    if not any(PUA_START <= ord(c) <= PUA_END for c in text):
        return text

    if font in SYMBOL_FONTS:
        table = SYMBOL_PUA
    elif font in WINGDINGS_FONTS:
        table = WINGDINGS_PUA
    else:
        table = {**SYMBOL_PUA, **WINGDINGS_PUA}

    out = []
    for c in text:
        cp = ord(c)
        if not PUA_START <= cp <= PUA_END:
            out.append(c)
            continue
        mapped = table.get(cp - 0xF000)
        if mapped is None:
            # Không đoán bừa: giữ nguyên và ghi nhận để bổ sung bảng ánh xạ.
            if unmapped is not None:
                unmapped[(font or "?", cp)] += 1
            out.append(c)
        else:
            out.append(mapped)
    return "".join(out)


def probe_fonts(doc: pymupdf.Document, limit: int = 25) -> None:
    """In thống kê font để xác định đâu là watermark trước khi lọc."""
    stats: collections.Counter = collections.Counter()
    samples: dict = {}
    for pno in range(doc.page_count):
        for block in doc[pno].get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    if not span["text"].strip():
                        continue
                    key = (span["font"], round(span["size"], 1))
                    stats[key] += 1
                    samples.setdefault(key, (pno + 1, span["text"].strip()[:70]))

    print(f"Số trang: {doc.page_count}\n")
    print(f'{"font":<32} {"size":>6} {"lần":>6}  ví dụ')
    print("-" * 110)
    for (font, size), n in stats.most_common(limit):
        pno, txt = samples[(font, size)]
        flag = "  <-- lọc" if font in WATERMARK_FONTS else ""
        print(f"{font:<32} {size:>6} {n:>6}  tr.{pno} {txt!r}{flag}")


def extract_clean(
    doc: pymupdf.Document,
) -> tuple[str, collections.Counter, collections.Counter]:
    """Trích text đã bỏ span thuộc font watermark, giữ nguyên câu chữ thân bài."""
    dropped: collections.Counter = collections.Counter()
    unmapped: collections.Counter = collections.Counter()
    out: list[str] = []

    for pno in range(doc.page_count):
        out.append(PAGE_MARK.format(pno + 1))
        for block in doc[pno].get_text("dict")["blocks"]:
            if block.get("type") != 0:  # bỏ block ảnh
                continue
            for line in block["lines"]:
                parts = []
                for span in line["spans"]:
                    if span["font"] in WATERMARK_FONTS:
                        if span["text"].strip():
                            dropped[span["font"]] += 1
                        continue
                    parts.append(
                        normalize_symbols(span["text"], span["font"], unmapped)
                    )
                text = "".join(parts)
                if text.strip():
                    out.append(text)
        out.append("")

    return "\n".join(out), dropped, unmapped


def extract_raw(doc: pymupdf.Document) -> str:
    """Trích text giữ bố cục gốc — hữu ích khi cần đọc lại cấu trúc bảng."""
    out: list[str] = []
    for pno in range(doc.page_count):
        out.append(PAGE_MARK.format(pno + 1))
        out.append(normalize_symbols(doc[pno].get_text("text", sort=True)))
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf", type=pathlib.Path)
    ap.add_argument("-o", "--outdir", type=pathlib.Path, default=pathlib.Path("."))
    ap.add_argument(
        "--probe-fonts",
        action="store_true",
        help="chỉ in thống kê font rồi thoát, không ghi file",
    )
    args = ap.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"Không tìm thấy file: {args.pdf}")

    doc = pymupdf.open(args.pdf)

    if args.probe_fonts:
        probe_fonts(doc)
        return 0

    args.outdir.mkdir(parents=True, exist_ok=True)
    clean, dropped, unmapped = extract_clean(doc)
    raw = extract_raw(doc)

    (args.outdir / "clean.txt").write_text(clean, encoding="utf-8")
    (args.outdir / "raw-layout.txt").write_text(raw, encoding="utf-8")

    print(f"{args.pdf.name}: {doc.page_count} trang")
    print(f"  -> {args.outdir / 'clean.txt'}       {len(clean.splitlines()):>6} dòng")
    print(f"  -> {args.outdir / 'raw-layout.txt'}  {len(raw.splitlines()):>6} dòng")
    if dropped:
        print("  Đã lọc (watermark/chữ ký số):")
        for font, n in dropped.most_common():
            print(f"    {font:<24} {n:>5} span")
    else:
        print("  CẢNH BÁO: không lọc được span nào — kiểm tra lại bằng --probe-fonts")

    if unmapped:
        print("  CẢNH BÁO: ký tự PUA chưa có trong bảng ánh xạ (giữ nguyên, KHÔNG đoán):")
        for (font, cp), n in unmapped.most_common():
            print(f"    {font:<22} U+{cp:04X} (0x{cp - 0xF000:02X})  {n:>4} lần")
        print("    -> bổ sung vào SYMBOL_PUA / WINGDINGS_PUA rồi chạy lại.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
