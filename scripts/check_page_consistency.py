#!/usr/bin/env python
"""Đối chiếu số trang của cùng một quy tắc giữa ba file, và với nội dung thật.

Sau khi thống nhất số trang ở mục 0.5, ba file phải nói cùng một con số cho cùng
một quy tắc:
    docs/rules/rules-flat-draft.md      '| trang N'
    docs/rules/rules-formulas.md        '- **Trang:** N'
    docs/rules/rules-classification.md  cột cuối của bảng

Script này KHÔNG sửa gì — chỉ báo lệch. Chạy lại sau mỗi lần đụng vào số trang.

    uv run python scripts/check_page_consistency.py
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DASH = '–'
PAGES_TOTAL = 44


def pages_of(raw: str) -> set[int]:
    return {int(x) for x in re.findall(r'\d+', raw)}


def from_flat_draft() -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    cur: int | None = None
    buf: list[str] = []
    for line in (ROOT / 'docs/rules/rules-flat-draft.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^\s*-\s*\*\*R(\d+)\*\*', line)
        if m:
            if cur is not None:
                _flush(out, cur, buf)
            cur, buf = int(m.group(1)), [line]
        elif cur is not None:
            if line.startswith('#') or line.startswith('---'):
                _flush(out, cur, buf)
                cur, buf = None, []
            else:
                buf.append(line)
    if cur is not None:
        _flush(out, cur, buf)
    return out


def _flush(out: dict[int, set[int]], rid: int, buf: list[str]) -> None:
    m = re.search(r'\|\s*trang\s*([\d' + DASH + r'\-]+)', ' '.join(buf), re.I)
    if m:
        out[rid] = pages_of(m.group(1))


def from_formulas() -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    cur: int | None = None
    for line in (ROOT / 'docs/rules/rules-formulas.md').read_text(encoding='utf-8').splitlines():
        m = re.match(r'^#{3,4}\s*R(\d+)\b', line)
        if m:
            cur = int(m.group(1))
            continue
        if cur is not None:
            m = re.match(r'^- \*\*Trang:\*\*\s*([\d' + DASH + r'\-]+)', line)
            if m:
                out[cur] = pages_of(m.group(1))
                cur = None
    return out


def from_classification() -> dict[int, set[int]]:
    out: dict[int, set[int]] = {}
    row = re.compile(r'^\|\s*R(\d+)\s*\|.*\|\s*([\d' + DASH + r'\-]+)\s*\|\s*$')
    for line in (ROOT / 'docs/rules/rules-classification.md').read_text(encoding='utf-8').splitlines():
        m = row.match(line)
        if m:
            out[int(m.group(1))] = pages_of(m.group(2))
    return out


def main() -> int:
    srcs = {
        'flat-draft': from_flat_draft(),
        'formulas': from_formulas(),
        'classification': from_classification(),
    }
    for name, d in srcs.items():
        print(f'{name:16} {len(d)} quy tắc có số trang')

    all_ids = sorted(set().union(*(set(d) for d in srcs.values())))
    mismatch = []
    out_of_range = []
    for rid in all_ids:
        vals = {n: d[rid] for n, d in srcs.items() if rid in d}
        if len({frozenset(v) for v in vals.values()}) > 1:
            mismatch.append((rid, vals))
        for n, v in vals.items():
            bad = [p for p in v if not 1 <= p <= PAGES_TOTAL]
            if bad:
                out_of_range.append((rid, n, bad))

    print()
    if out_of_range:
        print(f'❌ {len(out_of_range)} chỗ có số trang ngoài 1..{PAGES_TOTAL}:')
        for rid, n, bad in out_of_range:
            print(f'   R{rid:03d} [{n}] -> {bad}')
    else:
        print(f'✅ Mọi số trang đều nằm trong 1..{PAGES_TOTAL}')

    if mismatch:
        print(f'\n❌ {len(mismatch)} quy tắc LỆCH giữa các file:')
        for rid, vals in mismatch:
            detail = ' · '.join(f'{n}={sorted(v)}' for n, v in vals.items())
            print(f'   R{rid:03d}: {detail}')
    else:
        print('✅ Không quy tắc nào lệch số trang giữa các file')

    return 1 if (mismatch or out_of_range) else 0


if __name__ == '__main__':
    raise SystemExit(main())
