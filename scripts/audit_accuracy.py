#!/usr/bin/env python
"""Estimate suggestion accuracy per confidence tier, then extrapolate to the corpus.

This is why the audit sample was stratified rather than flat: each tier is
measured on its own, then recombined by its share of the 517 labels. A flat
sample would have been dominated by the big tiers and said nothing usable about
the weak ones.

"Đúng chủ đề" counts Đ and Thừa: both identified the right subject, and Thừa only
over-listed candidate rules — a reviewer trims those in seconds. Thiếu and S are
real misses: a rule was absent or wrong.

Usage
-----
    python scripts/audit_accuracy.py data/eval_sheet_mau_kiem_daduyet.csv \
        --full data/eval_sheet_moi.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('audited_csv')
    ap.add_argument('--full', required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    aud = list(csv.DictReader(open(args.audited_csv, encoding='utf-8-sig')))
    full = list(csv.DictReader(open(args.full, encoding='utf-8-sig')))
    pop = collections.Counter(r['do_tin_cay'] for r in full)

    by: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in aud:
        by[r['do_tin_cay']][r['goi_y_dung']] += 1

    print(f'Mẫu kiểm: {len(aud)} dòng · Toàn bộ: {len(full)} nhãn\n')
    hdr = f'{"Mức tin cậy":<16}{"mẫu":>5}{"Đ":>4}{"Thừa":>6}{"Thiếu":>7}{"S":>4}' \
          f'{"đúng chủ đề":>13}{"toàn bộ":>9}{"ước tính đúng":>15}'
    print(hdr)
    print('-' * len(hdr))

    tot_est = 0.0
    for tier in sorted(by, key=lambda t: -pop[t]):
        c = by[tier]
        n = sum(c.values())
        ok = c['Đ'] + c['Thừa']
        rate = ok / n if n else 0
        est = rate * pop[tier]
        tot_est += est
        print(f'{tier:<16}{n:>5}{c["Đ"]:>4}{c["Thừa"]:>6}{c["Thiếu"]:>7}{c["S"]:>4}'
              f'{rate*100:>12.0f}%{pop[tier]:>9}{est:>14.0f}')

    print('-' * len(hdr))
    print(f'{"TỔNG":<16}{len(aud):>5}{"":>4}{"":>6}{"":>7}{"":>4}'
          f'{"":>13}{len(full):>9}{tot_est:>14.0f}')
    print(f'\nƯớc tính gợi ý đúng chủ đề trên toàn bộ: '
          f'{tot_est:.0f}/{len(full)} = {tot_est/len(full)*100:.0f}%')
    print('\n⚠️ Mỗi mức chỉ 5–15 mẫu nên sai số còn rộng; con số này để QUYẾT ĐỊNH '
          'mức nào cần soát toàn bộ, không phải để công bố.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
