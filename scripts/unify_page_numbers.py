#!/usr/bin/env python
"""Thống nhất số trang về SỐ TRANG IN của Guideline lần 07 (mục 0.5).

Vấn đề
------
Hai hệ đánh số trang cùng tồn tại trong bộ tài liệu quy tắc:

  * R01–R100  — viết theo bản trích lần 06, có thêm 01 trang chữ ký ở đầu nên
                số trang vật lý = **số trang in + 1**.
  * R101–R110 — viết theo bản lần 07, trang vật lý = trang in.

Đã kiểm chứng offset −1 bằng 12 phép dò độc lập trải từ trang 8 đến trang 45
(xem báo cáo trong PLAN.md mục 0.5). Ví dụ: R09 ghi "trang 10", nội dung thực
nằm ở trang in 9; R98 ghi "trang 44", nội dung ở trang in 43.

Script này trừ 1 vào mọi số trang thuộc hệ cũ, giữ nguyên hệ mới.
CHỈ CHẠY MỘT LẦN — chạy lần hai sẽ trừ tiếp và làm sai.

Cách dùng
---------
    uv run python scripts/unify_page_numbers.py            # xem trước, không ghi
    uv run python scripts/unify_page_numbers.py --apply    # ghi vào file
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OFFSET = -1
LAST_OLD_RULE = 100          # R101 trở đi đã dùng số trang in

DASH = '–'                   # en dash dùng trong tài liệu


def shift(num: str) -> str:
    return str(int(num) + OFFSET)


def shift_range(text: str) -> str:
    """'10', '10–11', '43-44' -> đã trừ 1 ở mọi vế."""
    return re.sub(r'\d+', lambda m: shift(m.group()), text)


# --- 1. rules-flat-draft.md : '| trang N' trong khối R01-R100 --------------
def do_flat_draft(text: str) -> tuple[str, list[str]]:
    log: list[str] = []
    out: list[str] = []
    cur_id: int | None = None
    for line in text.splitlines():
        m = re.match(r'^\s*-\s*\*\*R(\d+)\*\*', line)
        if m:
            cur_id = int(m.group(1))
        elif line.startswith('#') or line.startswith('---'):
            cur_id = None

        if cur_id is not None and cur_id <= LAST_OLD_RULE:
            def repl(mm: re.Match) -> str:
                return mm.group(1) + shift_range(mm.group(2))
            new = re.sub(r'(\|\s*trang\s*)([\d' + DASH + r'\-]+)', repl, line,
                         flags=re.IGNORECASE)
            if new != line:
                log.append(f'  R{cur_id:03d}: {line.strip()[-24:]}  ->  {new.strip()[-24:]}')
                line = new
        out.append(line)
    return '\n'.join(out) + '\n', log


# --- 2. rules-formulas.md --------------------------------------------------
def do_formulas(text: str) -> tuple[str, list[str]]:
    log: list[str] = []
    out: list[str] = []
    in_bosung = False
    for line in text.splitlines():
        if line.startswith('## BỔ SUNG'):
            in_bosung = True
        elif line.startswith('## ') and in_bosung:
            in_bosung = False

        orig = line
        # (a) dong '- **Trang:** N.'  — bo qua dong da ghi '(trang in)'
        m = re.match(r'^(- \*\*Trang:\*\* )([\d' + DASH + r'\-]+)(.*)$', line)
        if m and '(trang in)' not in line and not in_bosung:
            line = m.group(1) + shift_range(m.group(2)) + m.group(3)
        # (b) tieu de muc va bang tong hop: '(trang A–B)'
        elif '/44' not in line and not in_bosung:
            line = re.sub(r'\(trang ([\d' + DASH + r'\-]+)\)',
                          lambda mm: '(trang ' + shift_range(mm.group(1)) + ')', line)

        if line != orig:
            log.append(f'  {orig.strip()[:62]}  ->  {line.strip()[:62]}')
        out.append(line)
    return '\n'.join(out) + '\n', log


# --- 3. rules-classification.md : cot 'Trang' cua bang R01-R100 ------------
def do_classification(text: str) -> tuple[str, list[str]]:
    log: list[str] = []
    out: list[str] = []
    row = re.compile(r'^(\|\s*R(\d+)\s*\|.*\|\s*)([\d' + DASH + r'\-]+)(\s*\|\s*)$')
    for line in text.splitlines():
        # tieu de muc cung mang so trang cua he cu
        if line.startswith('### ') and '(trang ' in line:
            new_line = re.sub(r'\(trang ([\d' + DASH + r'\-]+)\)',
                              lambda mm: '(trang ' + shift_range(mm.group(1)) + ')', line)
            if new_line != line:
                log.append(f'  {line[:52]}  ->  {new_line[:52]}')
                line = new_line
            out.append(line)
            continue
        m = row.match(line)
        if m and int(m.group(2)) <= LAST_OLD_RULE:
            shifted = shift_range(m.group(3))
            log.append(f'  R{int(m.group(2)):03d}: trang {m.group(3)} -> {shifted}')
            line = m.group(1) + shifted + m.group(4)
        out.append(line)
    return '\n'.join(out) + '\n', log


# --- 4. config/rules.yaml : chu thich trong globals ------------------------
def do_yaml(text: str) -> tuple[str, list[str]]:
    log: list[str] = []
    out: list[str] = []
    for line in text.splitlines():
        orig = line
        if line.lstrip().startswith('#'):
            line = re.sub(r'\(trang (\d+)\)',
                          lambda mm: '(trang ' + shift(mm.group(1)) + ')', line)
        if line != orig:
            log.append(f'  {orig.strip()[:70]}  ->  {line.strip()[:70]}')
        out.append(line)
    return '\n'.join(out) + '\n', log


TARGETS = [
    ('docs/rules/rules-flat-draft.md', do_flat_draft),
    ('docs/rules/rules-formulas.md', do_formulas),
    ('docs/rules/rules-classification.md', do_classification),
    ('config/rules.yaml', do_yaml),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--apply', action='store_true', help='ghi vào file (mặc định chỉ xem trước)')
    args = ap.parse_args()

    total = 0
    for rel, fn in TARGETS:
        path = ROOT / rel
        if not path.is_file():
            sys.exit(f'Không tìm thấy: {rel}')
        src = path.read_text(encoding='utf-8')
        new, log = fn(src)
        total += len(log)
        print(f'\n=== {rel} — {len(log)} thay đổi ===')
        for entry in log[:6]:
            print(entry)
        if len(log) > 6:
            print(f'  … và {len(log) - 6} dòng nữa')
        if args.apply and log:
            path.write_text(new, encoding='utf-8')

    print(f'\nTổng: {total} thay đổi.', '(ĐÃ GHI)' if args.apply else '(chưa ghi — thêm --apply)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
