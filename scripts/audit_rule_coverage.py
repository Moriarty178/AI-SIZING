#!/usr/bin/env python
"""Rà độ phủ: trang nào của Guideline có nhiều câu mang tính quy tắc mà ít quy tắc được bắt.

Bối cảnh
--------
Mục 0.1 rút 100 quy tắc từ Guideline bằng cách đọc tay. Khi làm mục 0.4 phát hiện
trang 9 sót 2 câu (đã bổ sung thành R101, R102). Script này tìm các trang khác có
nguy cơ sót tương tự, thay vì đọc lại tay cả 44 trang.

Cách làm: đếm **câu mang dấu hiệu quy phạm** ("phải", "không vượt quá", "tối thiểu"…)
trên mỗi trang, so với số quy tắc đã bắt ở trang đó. Trang nào chênh lệch lớn thì
đọc lại trang đó.

Đây là công cụ **khoanh vùng**, không phải công cụ kết luận — câu có "phải" chưa
chắc là quy tắc, và một quy tắc có thể trải trên nhiều câu. Luôn phải đọc lại trang
được gắn cờ.

Cách dùng
---------
    uv run python scripts/audit_rule_coverage.py
    uv run python scripts/audit_rule_coverage.py --page 19      # xem chi tiết 1 trang
    uv run python scripts/audit_rule_coverage.py --threshold 3
"""

from __future__ import annotations

import argparse
import collections
import pathlib
import re
import sys
import unicodedata

CLEAN = pathlib.Path('docs/rules/.tmp-lan7/clean.txt')
DRAFT = pathlib.Path('docs/rules/rules-flat-draft.md')

# ĐÃ THỐNG NHẤT SỐ TRANG (2026-08-26, mục 0.5).
# Trước đây hai hệ cùng tồn tại trong rules-flat-draft.md: R01–R100 dùng số trang
# vật lý bản lần 06 (= trang in + 1), R101+ dùng số trang in. Nay toàn bộ đã quy về
# SỐ TRANG IN bằng scripts/unify_page_numbers.py, đối chiếu bằng
# scripts/check_page_consistency.py. Không còn phải bù trừ.
DRAFT_PAGE_OFFSET = 0
FIRST_NEW_ID = None


def page_offset(rule_id: int) -> int:
    return 0 if FIRST_NEW_ID is not None and rule_id >= FIRST_NEW_ID else DRAFT_PAGE_OFFSET

PAGE_RE = re.compile(r'^=====\s*TRANG\s+(\d+)\s*=====$')
RULE_START = re.compile(r'^\s*-\s*\*\*R(\d+)\*\*')
PAGE_REF = re.compile(r'\|\s*trang\s*([\d–\-]+)', re.IGNORECASE)

# Dấu hiệu câu mang tính quy phạm.
NORMATIVE = re.compile(
    r'\b(phải|cần phải|cần chỉ rõ|cần mô tả|không được|không vượt quá|không quá|'
    r'tối thiểu|tối đa|bắt buộc|yêu cầu|đảm bảo|chỉ thực hiện|chỉ sử dụng|'
    r'không áp dụng|khuyến cáo|nên sử dụng|ưu tiên)\b',
    re.IGNORECASE,
)

BOILERPLATE = re.compile(
    r'^(TẬP ĐOÀN CÔNG NGHIỆP|GUIDELINE ĐỊNH CỠ|CẤP PHÁT HẠ TẦNG|CÔNG NGHỆ THÔNG TIN$|'
    r'Ngày (có|hết) hiệu lực|Lần ban hành|Trang:\s*\d+)'
)


def norm(s: str) -> str:
    s = unicodedata.normalize('NFC', s).replace(' ', ' ')
    return re.sub(r'\s+', ' ', s).strip()


def load_pages() -> dict[int, list[str]]:
    """Trả về {số trang: [câu]} — nối dòng thành đoạn rồi tách câu."""
    pages: dict[int, list[str]] = {}
    page, buf = 0, []
    for raw in CLEAN.read_text(encoding='utf-8').splitlines():
        m = PAGE_RE.match(raw.strip())
        if m:
            if page:
                pages[page] = split_sentences(' '.join(buf))
            page, buf = int(m.group(1)), []
            continue
        line = norm(raw)
        if line and not BOILERPLATE.match(line):
            buf.append(line)
    if page:
        pages[page] = split_sentences(' '.join(buf))
    return pages


def split_sentences(text: str) -> list[str]:
    # tách theo dấu chấm câu và theo gạch đầu dòng (tài liệu dùng bullet rất nhiều)
    parts = re.split(r'(?<=[.;:])\s+|\s+(?=-[A-ZĐÀ-Ỹ])|\s+(?=o[A-ZĐÀ-Ỹ])', text)
    return [p.strip() for p in parts if len(p.strip()) > 25]


def load_rules_per_page() -> dict[int, list[int]]:
    """Trả về {số trang (đã quy về hệ clean.txt): [mã số quy tắc]}.

    Một quy tắc trong `rules-flat-draft.md` trải trên nhiều dòng, phần `| trang N`
    thường nằm ở dòng cuối của khối — nên phải gom theo KHỐI, không theo dòng.
    """
    out: dict[int, list[int]] = collections.defaultdict(list)
    blocks: list[tuple[int, list[str]]] = []
    cur_id: int | None = None
    cur: list[str] = []

    for line in DRAFT.read_text(encoding='utf-8').splitlines():
        m = RULE_START.match(line)
        if m:
            if cur_id is not None:
                blocks.append((cur_id, cur))
            cur_id, cur = int(m.group(1)), [line]
        elif cur_id is not None:
            if line.startswith('#') or line.startswith('---'):
                blocks.append((cur_id, cur))
                cur_id, cur = None, []
            else:
                cur.append(line)
    if cur_id is not None:
        blocks.append((cur_id, cur))

    for rid, lines in blocks:
        m = PAGE_REF.search(' '.join(lines))
        if not m:
            continue
        for pg in re.split(r'[–\-]', m.group(1)):
            if pg.strip().isdigit():
                out[int(pg) + page_offset(rid)].append(rid)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--page', type=int, help='in mọi câu quy phạm của một trang')
    ap.add_argument('--threshold', type=int, default=4,
                    help='chênh lệch từ bao nhiêu thì gắn cờ (mặc định 4)')
    args = ap.parse_args()

    for f in (CLEAN, DRAFT):
        if not f.is_file():
            sys.exit(f'Không tìm thấy: {f}')

    pages = load_pages()
    rules = load_rules_per_page()

    if args.page:
        print(f'=== TRANG {args.page} — câu mang dấu hiệu quy phạm ===')
        print(f'Quy tắc đã bắt: {sorted(rules.get(args.page, [])) or "(không có)"}\n')
        for s in pages.get(args.page, []):
            if NORMATIVE.search(s):
                print(f'  • {s[:150]}')
        return 0

    print(f'{"trang":>5} {"câu quy phạm":>13} {"quy tắc bắt":>12} {"chênh":>6}  cờ')
    print('-' * 62)
    flagged = []
    tot_sent = tot_rule = 0
    for pg in sorted(pages):
        n_sent = sum(1 for s in pages[pg] if NORMATIVE.search(s))
        n_rule = len(rules.get(pg, []))
        tot_sent += n_sent
        tot_rule += n_rule
        gap = n_sent - n_rule
        flag = ''
        if gap >= args.threshold and n_sent >= 3:
            flag = '<-- ĐỌC LẠI'
            flagged.append((pg, gap))
        print(f'{pg:>5} {n_sent:>13} {n_rule:>12} {gap:>6}  {flag}')

    print(f'\nTổng: {tot_sent} câu quy phạm · {tot_rule} lượt quy tắc gắn trang')
    if flagged:
        flagged.sort(key=lambda x: -x[1])
        print(f'\n{len(flagged)} trang cần đọc lại, ưu tiên từ trên xuống:')
        for pg, gap in flagged:
            print(f'   trang {pg:>2} (chênh {gap})  →  --page {pg}')
    else:
        print('\nKhông trang nào vượt ngưỡng.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
