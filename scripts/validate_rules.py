#!/usr/bin/env python
"""Kiểm tra `config/rules.yaml` — chạy sau mỗi lần sửa bộ quy tắc.

Kiểm những thứ mà một lỗi âm thầm sẽ đi thẳng vào báo cáo gửi người dùng:

  * Lược đồ: trường bắt buộc, giá trị enum hợp lệ, mã đúng định dạng.
  * NT2 (grounding): mọi quy tắc phải có `source_doc` — không có căn cứ thì
    finding sinh ra phải bị lọc bỏ, nên không cho phép quy tắc thiếu nó.
  * NT1 (tính bằng code): `formula` chỉ được dùng tham số đã khai trong `inputs`,
    hằng số trong `globals`, và hàm số học an toàn. Bắt tên lạ ngay tại đây thay
    vì để C4 nổ lúc chạy.
  * NT3 (quy tắc là dữ liệu): mã phải nằm trong bảng mã chính thức
    `docs/rules/rules-id-map.md` — không ai được tự chế mã mới.
  * Tiêu chí định tính không được mơ hồ ("hợp lý", "đầy đủ", "phù hợp" đứng một
    mình) — đó là nguồn gốc kết quả thiếu nhất quán của C5.

Chạy:  uv run python scripts/validate_rules.py
       uv run python scripts/validate_rules.py --coverage  # thêm bảng tiến độ số hóa
"""
from __future__ import annotations

import argparse
import ast
import collections
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit('Cần PyYAML:  uv add pyyaml')

ROOT = pathlib.Path(__file__).resolve().parent.parent
RULES = ROOT / 'config/rules.yaml'
ID_MAP = ROOT / 'docs/rules/rules-id-map.md'

ID_RE = re.compile(r'^[A-Z]{3}-\d{2}$')
SEVERITIES = {'critical', 'major', 'minor', 'info'}
TYPES = {'quantitative', 'qualitative'}
CONFIDENCE = {'high', 'medium', 'low'}
SAFE_FUNCS = {'pow', 'min', 'max', 'ceil', 'floor', 'round', 'abs', 'sum'}
REQUIRED = ('id', 'name', 'type', 'applies_to_equipment', 'severity', 'source_doc')

# Từ mơ hồ: nếu tiêu chí ngắn mà chỉ có mấy từ này thì C5 sẽ tự chế tiêu chuẩn.
VAGUE = ('hợp lý', 'đầy đủ', 'phù hợp', 'chính xác', 'rõ ràng')


def official_ids() -> set[str]:
    """Chỉ lấy mã trong mục "Bảng mã đầy đủ".

    Các mục sau đó (gộp / loại) cũng có ô đầu dòng dạng `MDB-07`, nhưng đó là **mã
    tạm của code web app**, không phải mã chính thức — nhặt nhầm sẽ báo tiến độ sai.
    """
    if not ID_MAP.is_file():
        return set()
    txt = ID_MAP.read_text(encoding='utf-8')
    start = txt.find('## Bảng mã đầy đủ')
    if start < 0:
        return set()
    end = txt.find('\n## ', start + 1)
    body = txt[start:end if end > 0 else len(txt)]
    return {m.group(1) for m in re.finditer(r'^\|\s*`([A-Z]{3}-\d{2})`\s*\|', body, re.M)}


def formula_names(expr: str) -> tuple[set[str], set[str], list[str]]:
    """Trả về (tên biến, tên hàm, lỗi cú pháp)."""
    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError as e:
        return set(), set(), [f'công thức không phân tích được: {e.msg}']
    names, funcs = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            funcs.add(node.func.id)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    return names - funcs, funcs, []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--coverage', action='store_true',
                    help='in tiến độ số hóa so với bảng mã chính thức')
    args = ap.parse_args()

    if not RULES.is_file():
        sys.exit(f'Không tìm thấy {RULES}')
    doc = yaml.safe_load(RULES.read_text(encoding='utf-8'))

    equip = set(doc.get('equipment_types') or [])
    modules = set(doc.get('module_types') or [])
    scopes = set(doc.get('evaluation_scopes') or [])
    globals_ = set((doc.get('globals') or {}).keys())
    sources = {s['key'] for s in (doc.get('sources') or []) if 'key' in s}
    rules = doc.get('rules') or []

    errs: list[str] = []
    warns: list[str] = []
    seen: dict[str, int] = {}
    official = official_ids()

    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            errs.append(f'rules[{i}]: không phải một ánh xạ (mapping)')
            continue
        rid = r.get('id', f'<rules[{i}] thiếu id>')
        where = f'{rid}'

        for f in REQUIRED:
            if not r.get(f):
                errs.append(f'{where}: thiếu trường bắt buộc `{f}`')

        if 'id' in r:
            if not ID_RE.match(str(r['id'])):
                errs.append(f'{where}: mã sai định dạng, phải là <NHÓM>-<số 2 chữ số>')
            elif official and r['id'] not in official:
                errs.append(f'{where}: mã KHÔNG có trong bảng mã chính thức '
                            f'(docs/rules/rules-id-map.md)')
            if r['id'] in seen:
                errs.append(f'{where}: mã trùng với rules[{seen[r["id"]]}]')
            seen[r['id']] = i

        rtype = r.get('type')
        if rtype and rtype not in TYPES:
            errs.append(f'{where}: `type` phải là {sorted(TYPES)}, đang là {rtype!r}')
        if r.get('severity') and r['severity'] not in SEVERITIES:
            errs.append(f'{where}: `severity` phải là {sorted(SEVERITIES)}')
        if r.get('confidence_floor') and r['confidence_floor'] not in CONFIDENCE:
            errs.append(f'{where}: `confidence_floor` phải là {sorted(CONFIDENCE)}')

        eq = r.get('applies_to_equipment') or []
        if not isinstance(eq, list):
            errs.append(f'{where}: `applies_to_equipment` phải là danh sách')
        else:
            for v in eq:
                if v not in equip:
                    errs.append(f'{where}: `applies_to_equipment` có giá trị lạ {v!r}')
        for v in (r.get('applies_to_module') or []):
            if v not in modules:
                errs.append(f'{where}: `applies_to_module` có giá trị lạ {v!r}')
        if r.get('scope') and r['scope'] not in scopes:
            errs.append(f'{where}: `scope` có giá trị lạ {r["scope"]!r}')
        if r.get('round') not in (None, 1, 2):
            errs.append(f'{where}: `round` phải là 1 hoặc 2')

        # Quy tắc Vòng 1 = mục checklist -> bắt buộc có `checklist_ref`, nếu không
        # thì C7 không biết in nó ra chỗ nào trong báo cáo xếp theo thứ tự checklist.
        if r.get('round') == 1 and not r.get('checklist_ref'):
            errs.append(f'{where}: quy tắc Vòng 1 phải có `checklist_ref`')
        for c in (r.get('checklist_ref') or []):
            if not re.match(r'^CL-[\dx.]+[a-z]?$', str(c)):
                errs.append(f'{where}: `checklist_ref` sai định dạng: {c!r}')

        sd = r.get('source_doc')
        if sd and sources:
            key = str(sd).split(',')[0].strip()
            if key not in sources and not str(sd).startswith(('Quy ước nội bộ',
                                                              'Xác nhận miệng')):
                warns.append(f'{where}: `source_doc` mở đầu bằng {key!r} — '
                             f'không khớp `sources` nào ({sorted(sources)})')

        # `applies_when` dùng được cho cả hai loại; `inputs` cũng vậy (quy tắc định
        # tính khai `inputs` cho các trường mà C3 phải trích để mở/đóng cổng này).
        if r.get('applies_when'):
            declared_aw = {inp['name'] for inp in (r.get('inputs') or [])
                           if isinstance(inp, dict) and 'name' in inp}
            names, funcs, ferr = formula_names(str(r['applies_when']))
            for e in ferr:
                errs.append(f'{where}: `applies_when` {e}')
            unknown = names - declared_aw - globals_
            if unknown:
                errs.append(f'{where}: `applies_when` dùng tên chưa khai: '
                            f'{sorted(unknown)} (khai trong `inputs` hoặc `globals`)')
            bad = funcs - SAFE_FUNCS
            if bad:
                errs.append(f'{where}: `applies_when` gọi hàm không cho phép: {sorted(bad)}')
        for sa in (r.get('see_also') or []):
            if not ID_RE.match(str(sa)):
                errs.append(f'{where}: `see_also` có mã sai định dạng: {sa!r}')
            elif official and sa not in official:
                errs.append(f'{where}: `see_also` trỏ tới mã không có trong bảng mã: {sa}')

        if rtype == 'quantitative':
            if not r.get('formula') and not r.get('check') and not r.get('note'):
                errs.append(f'{where}: quy tắc định lượng phải có `check` (so ngưỡng) '
                            f'hoặc `formula` (tính lại), hoặc `note` giải thích vì sao '
                            f'không có cả hai')
            if r.get('formula') and r.get('check'):
                errs.append(f'{where}: không dùng đồng thời `formula` và `check` — '
                            f'`check` cho bất đẳng thức, `formula` cho phép tính lại')
            if r.get('compare_with') and not r.get('formula'):
                errs.append(f'{where}: `compare_with` chỉ dùng kèm `formula`')
            declared = {inp['name'] for inp in (r.get('inputs') or [])
                        if isinstance(inp, dict) and 'name' in inp}
            for field in ('formula', 'check'):
                if not r.get(field):
                    continue
                names, funcs, ferr = formula_names(str(r[field]))
                for e in ferr:
                    errs.append(f'{where}: `{field}` {e}')
                unknown = names - declared - globals_
                if unknown:
                    errs.append(f'{where}: `{field}` dùng tên chưa khai: '
                                f'{sorted(unknown)} (khai trong `inputs` hoặc `globals`)')
                bad = funcs - SAFE_FUNCS
                if bad:
                    errs.append(f'{where}: `{field}` gọi hàm không cho phép: {sorted(bad)}')
                aw_names = formula_names(str(r.get('applies_when') or '0'))[0]
                lookups = {inp['name'] for inp in (r.get('inputs') or [])
                           if isinstance(inp, dict) and inp.get('role') == 'lookup'}
                unused = declared - names - aw_names - lookups
                if unused:
                    warns.append(f'{where}: input khai nhưng `{field}` không dùng: '
                                 f'{sorted(unused)}')
            for inp in (r.get('inputs') or []):
                if not isinstance(inp, dict) or 'name' not in inp:
                    errs.append(f'{where}: mỗi phần tử `inputs` phải có `name`')
                elif 'unit' not in inp:
                    warns.append(f'{where}: input `{inp["name"]}` chưa ghi `unit`')

        elif rtype == 'qualitative':
            crit = str(r.get('criteria') or '')
            if not crit.strip():
                errs.append(f'{where}: quy tắc định tính phải có `criteria`')
            elif len(crit.strip()) < 80:
                hit = [w for w in VAGUE if w in crit.lower()]
                if hit:
                    errs.append(f'{where}: `criteria` quá ngắn và mơ hồ '
                                f'(chứa {hit}) — C5 sẽ tự chế tiêu chuẩn riêng')
                else:
                    warns.append(f'{where}: `criteria` chỉ {len(crit.strip())} ký tự, '
                                 f'có đủ cụ thể không?')

    print(f'Đã đọc {len(rules)} quy tắc từ config/rules.yaml')
    if rules:
        c = collections.Counter
        print(f"  loại     : {dict(c(r.get('type') for r in rules))}")
        print(f"  vòng     : {dict(c(r.get('round') for r in rules))}")
        print(f"  mức độ   : {dict(c(r.get('severity') for r in rules))}")
        off = [r['id'] for r in rules if r.get('enabled') is False]
        if off:
            print(f"  đang tắt : {len(off)} — {', '.join(sorted(off))}")
        treo = [r['id'] for r in rules
                if 'CHƯA CHẮC' in str(r.get('note', ''))
                or 'CẦN XÁC NHẬN' in str(r.get('note', ''))]
        if treo:
            print(f"  còn treo : {len(treo)} quy tắc mang điểm [CHƯA CHẮC]/[CẦN XÁC NHẬN]")
    if official:
        print(f'Bảng mã chính thức: {len(official)} mã')

    if args.coverage and official:
        done = set(seen)
        by_group: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
        for oid in official:
            g = oid.split('-')[0]
            by_group[g][1] += 1
            if oid in done:
                by_group[g][0] += 1
        print('\nTiến độ số hóa theo nhóm:')
        for g in sorted(by_group):
            d, t = by_group[g]
            bar = '█' * round(d / t * 20) + '·' * (20 - round(d / t * 20))
            print(f'  {g}  {bar}  {d:>3}/{t:<3}')
        print(f'  {"TỔNG":<4} {len(done & official):>3}/{len(official)}')

    for w in warns:
        print(f'  ⚠️  {w}')
    if errs:
        print(f'\n❌ {len(errs)} lỗi:')
        for e in errs:
            print(f'   {e}')
        return 1
    print(f'\n✅ Hợp lệ{" (" + str(len(warns)) + " cảnh báo)" if warns else ""}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
