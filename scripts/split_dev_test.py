#!/usr/bin/env python
"""0.8 — Split dossiers into a development set and a HELD-OUT test set.

Split by requesting unit (`Đầu mối yêu cầu`), never at random per label and
never by reviewer: 20 of 23 dossiers share one reviewer (Khanhnd23), so that axis
cannot separate anything, while the requester's writing style is exactly what
must not leak from test into dev (PLAN.md 0.8, decision 2026-09-03).

Method: greedy balancing. Requesters are sorted by label count (largest first,
seeded shuffle for ties) and each is assigned to whichever side is furthest below
its target share of labels. Target: ~2/3 dev, ~1/3 test. Deterministic — same
input, same split.

Output lists dossiers per side; the eval harness (1.13) must filter eval_set.json
by `dossier` and never look at test-side labels while tuning rules or prompts.

Usage
-----
    python scripts/split_dev_test.py data/eval_set.json --raw data/pnx_raw_labels.json \
        -o data/eval_split.json
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('eval_json')
    ap.add_argument('--raw', required=True, help='pnx_raw_labels.json — nguồn Đầu mối yêu cầu')
    ap.add_argument('--test-share', type=float, default=1 / 3)
    ap.add_argument('--seed', type=int, default=20260903)
    ap.add_argument('-o', '--out', required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    labels = json.load(open(args.eval_json, encoding='utf-8'))['labels']
    raw = json.load(open(args.raw, encoding='utf-8'))

    requester: dict[str, str] = {}
    for p in raw['dossiers']:
        who = (p['info'].get('Đầu mối yêu cầu') or '').strip().lower() or '(không rõ)'
        requester.setdefault(p['dossier'], who)

    per_dossier = collections.Counter(l['dossier'] for l in labels)
    per_req: dict[str, list[str]] = collections.defaultdict(list)
    for d in per_dossier:
        per_req[requester.get(d, '(không rõ)')].append(d)
    req_size = {r: sum(per_dossier[d] for d in ds) for r, ds in per_req.items()}

    total = sum(per_dossier.values())
    target_test = total * args.test_share
    rnd = random.Random(args.seed)
    order = sorted(per_req, key=lambda r: (-req_size[r], rnd.random()))

    dev, test = [], []
    n_dev = n_test = 0
    for r in order:
        # put this requester where the deficit against target is larger
        if (target_test - n_test) > ((total - target_test) - n_dev):
            test.append(r); n_test += req_size[r]
        else:
            dev.append(r); n_dev += req_size[r]

    def side(reqs: list[str]) -> list[dict]:
        out = []
        for r in sorted(reqs):
            for d in sorted(per_req[r]):
                out.append({'dossier': d, 'dau_moi_yeu_cau': r, 'labels': per_dossier[d]})
        return out

    result = {
        'method': 'chia theo Đầu mối yêu cầu, cân bằng tham lam theo số nhãn, seed cố định',
        'seed': args.seed,
        'dev': {'dossiers': side(dev), 'labels': n_dev},
        'test': {'dossiers': side(test), 'labels': n_test},
        'rule': 'Tập test GIỮ KÍN: không đọc nhãn test khi chỉnh quy tắc/prompt; '
                'chỉ chạy một lần ở 3.6.',
    }
    json.dump(result, open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f'{len(per_dossier)} hồ sơ · {total} nhãn · {len(per_req)} đầu mối yêu cầu')
    for name, s in (('DEV', result['dev']), ('TEST (giữ kín)', result['test'])):
        print(f'\n{name}: {len(s["dossiers"])} hồ sơ · {s["labels"]} nhãn '
              f'({s["labels"]/total*100:.0f}%)')
        for d in s['dossiers']:
            print(f'   {d["labels"]:>3}  {d["dau_moi_yeu_cau"]:<12} {d["dossier"]}')
    print(f'\n-> {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
