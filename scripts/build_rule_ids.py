#!/usr/bin/env python
"""Gán mã chính thức <NHÓM>-<số> cho toàn bộ quy tắc — mục 0.5.

Đây là công cụ **dùng một lần** để sinh bảng mã ổn định. Sau khi `config/rules.yaml`
đã có quy tắc thật, mã KHÔNG được đổi nữa (đổi mã làm hỏng liên kết với eval set),
nên script này chỉ còn vai trò tài liệu: nó ghi lại vì sao mỗi quy tắc mang mã đó.

Nguyên tắc gán:
  * Nhóm theo **chủ đề / loại thiết bị**, không theo module phần mềm — module đi vào
    trường `applies_to_module` (quyết định "hai trục", rules-crossmap.md mục 5).
  * Số thứ tự chạy trong từng nhóm, **gán một lượt cho cả bộ** để nhóm chứa lẫn quy
    tắc định lượng và định tính (ARC, STO, BAK, ALC) không phải đánh số hai lần.
  * Thứ tự trong nhóm: quy tắc Guideline trước (theo số Rxx), rồi quy tắc từ checklist,
    rồi quy tắc từ code web app, rồi văn bản khác.

Chạy:  uv run python scripts/build_rule_ids.py         # in bảng + kiểm tra đầy đủ
       uv run python scripts/build_rule_ids.py --write # ghi docs/rules/rules-id-map.md
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent

# =============================================================================
# 1. GUIDELINE R01-R110 -> nhóm
# =============================================================================
# Nhóm của quy tắc ĐỊNH TÍNH lấy nguyên từ rules-criteria.md mục 3 (đã duyệt) —
# không được đổi. Nhóm của quy tắc định lượng gán ở đây.
GUIDELINE_GROUPS: dict[str, list[int]] = {
    # ngưỡng & hệ số chung, áp cho nhiều loại tài nguyên cùng lúc
    # R48/R49 là công thức tổng tài nguyên + hệ số KPI/sai số, dùng chung cho
    # CPU lẫn RAM lẫn ổ cứng -> để ở KPI, không nhét riêng vào CPU.
    'KPI': [1, 2, 3, 4, 5, 6, 7, 8, 19, 36, 38, 40, 48, 49],
    # kiến trúc, dự phòng, hạ tầng, số lượng node
    'ARC': [9, 10, 11, 12, 13, 14, 15, 50, 51, 91, 95, 101, 102, 106],
    # R46 (HĐH 2 core + 4 GB) và R47 (hypervisor 10% CPU + 6 GB) chạm cả CPU lẫn RAM;
    # xếp CPU vì phần CPU là ràng buộc chính, phần RAM ghi trong cùng công thức.
    'CPU': [16, 17, 20, 21, 43, 44, 46, 47, 52, 100],
    'RAM': [22, 45],
    'STO': [18, 54, 55, 56, 57, 58, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69],
    'BAK': [39, 70, 71, 72, 73, 74, 75, 76, 107],
    'SAN': [77, 78],
    'LAN': [79, 80, 81, 82],
    'FWL': [83, 84, 85],
    'LBA': [86, 87],
    'RCK': [88, 89, 90],
    'ALC': [93, 94, 96, 97, 108],
    'TST': [41, 98, 99],
    'PRC': [30, 31, 33, 34, 92, 109],
    # R53, R59 xếp EVD (không phải STO) theo đúng rules-criteria.md mục 3 —
    # chúng là yêu cầu MÔ TẢ về lưu trữ, không phải công thức lưu trữ.
    # R105 (tổng toàn hệ = tổng các module) là kiểm nhất quán SỐ, nhưng chủ đề của
    # nó là cách TRÌNH BÀY kết quả ở hai mức; hai mục checklist neo vào nó
    # (CL-2.9, CL-3.x.20) cũng thuộc EVD -> xếp EVD cho nhất quán.
    'EVD': [23, 25, 35, 37, 42, 53, 59, 103, 104, 105, 110],
    'MTH': [26, 27, 28, 29],
}

# Quy tắc Guideline KHÔNG vào rules.yaml, kèm lý do (ghi rõ, không im lặng bỏ)
GUIDELINE_DROP: dict[int, str] = {
    24: 'Câu tuyên bố ("kết quả định cỡ không chính xác 100%"), không phải yêu cầu — '
        'không nội dung nào có thể vi phạm nên không viết được tiêu chí ĐẠT/KHÔNG ĐẠT. '
        'Xem rules-criteria.md mục 1.3.',
    32: 'Gộp vào R25 (cùng yêu cầu chỉ rõ yếu tố scale up/out). Một quy tắc mang hai '
        '`source_doc` để không bắt lỗi hai lần với hai trích dẫn khác nhau. '
        'Xem rules-criteria.md mục 2.',
}

# =============================================================================
# 2. CHECKLIST — chỉ 19 mục trạng thái M mới thành quy tắc riêng.
#    18 mục trạng thái T chỉ gắn `checklist_ref` vào quy tắc sẵn có.
# =============================================================================
CHECKLIST_GROUPS: dict[str, list[str]] = {
    'EVD': ['CL-2.2', 'CL-2.6', 'CL-2.7', 'CL-2.8', 'CL-2.9',
            'CL-3.x.1', 'CL-3.x.2', 'CL-3.x.4', 'CL-3.x.5', 'CL-3.x.8', 'CL-3.x.20'],
    # CL-1.1 / CL-1.2 là phần I của checklist (SR / ITBrain). CL-1.2 vẫn
    # `[CẦN XÁC NHẬN]` (có nằm trong tài liệu sizing không) -> vẫn gán mã cho ổn
    # định, nhưng đặt `enabled: false` trong rules.yaml cho tới khi có trả lời.
    'PRC': ['CL-1.1', 'CL-1.2', 'CL-2.3', 'CL-2.10a'],
    'ARC': ['CL-3.x.9', 'CL-3.x.10'],
    'STO': ['CL-3.x.18', 'CL-3.2.7a'],
}

# =============================================================================
# 3. CODE WEB APP — 46 quy tắc, ba cách xử lý
# =============================================================================
# (a) TRÙNG: không tạo quy tắc mới, chỉ thêm `code_ref` vào quy tắc Guideline
CODE_MERGE: dict[str, str] = {
    'KPI-01': 'R02', 'KPI-02': 'R03', 'KPI-03': 'R04', 'KPI-05': 'R19',
    'SCL-01': 'R40', 'KFK-01': 'R40',
    'CPU-01': 'R48', 'RAM-01': 'R48', 'DSK-01': 'R48',
    'MDB-03': 'R48', 'MDB-04': 'R48',
    'KFK-08': 'R48', 'KFK-09': 'R48', 'KFK-10': 'R48',
    'RDS-09': 'R48',
    'HA-01': 'R101',
    'SRV-01': 'R50', 'SRV-02': 'R50',
    'RDS-11': 'RDS-03',   # trùng nội bộ trong chính code: "giống RDS-03/05/07"
}

# (b) LOẠI: không thuộc phạm vi Copilot, hoặc là lỗi code
CODE_DROP: dict[str, str] = {
    'PRC-01': 'Ràng buộc vận hành của web app (không duyệt khi còn tab chưa đánh giá), '
              'không phải yêu cầu đối với bản sizing Word. Copilot không kiểm được và '
              'cũng không nên kiểm.',
    'PRC-02': 'Như PRC-01 — ràng buộc của giao diện thẩm định, không phải của tài liệu.',
    'MDB-07': 'Quy ước làm tròn lên (ceil) áp cho mọi kết quả — đưa vào `globals` làm '
              'quy ước chung, không thành một quy tắc riêng.',
    'RDS-04': 'Code SAI (rules-crossmap.md C-01: dùng Kkpi 0.8 cho RAM thay vì 0.9). '
              'Số hóa theo R49 cho đúng, KHÔNG số hóa công thức sai.',
    'RDS-10': 'Code SAI (C-02: áp hệ số KPI và sai số hai lần). R48 quy định áp đúng '
              'một lần trên tổng tài nguyên.',
    'LBF-01': 'Code THIẾU (C-06: không áp Kdph = 1.2). R86/R87 đã có công thức đúng.',
    'LBF-02': 'Như LBF-01 — R87 đã phủ.',
}

# (c) RIÊNG: code có mà Guideline không có -> tạo mới, source_doc "quy ước nội bộ"
CODE_GROUPS: dict[str, list[str]] = {
    'KPI': ['KPI-04', 'GRW-01'],
    'ARC': ['MDB-01', 'MDB-02', 'RDS-03', 'RDS-06', 'RDS-07', 'RDS-08',
            'KFK-05', 'KFK-07', 'KFK-11'],
    'CPU': ['KFK-06'],
    'RAM': ['RDS-02'],
    'STO': ['RDS-01', 'RDS-05', 'KFK-02', 'KFK-03', 'KFK-04'],
    'BAK': ['MDB-05', 'MDB-06'],
}

# =============================================================================
# 4. VĂN BẢN KHÁC
# =============================================================================
OTHER_GROUPS: dict[str, list[str]] = {
    'ARC': ['QD849-01', 'QD849-02'],
    'FWL': ['ZONE-01'],
}


def build() -> tuple[dict[str, str], dict[str, list]]:
    """Trả về (mã nguồn -> mã chính thức, nhóm -> [dòng bảng])."""
    assigned: dict[str, str] = {}
    table: dict[str, list] = collections.defaultdict(list)
    groups = sorted(set(GUIDELINE_GROUPS) | set(CHECKLIST_GROUPS)
                    | set(CODE_GROUPS) | set(OTHER_GROUPS))
    for grp in groups:
        n = 0
        for rid in sorted(GUIDELINE_GROUPS.get(grp, [])):
            n += 1
            legacy = f'R{rid:02d}' + (' + R32' if rid == 25 else '')
            assigned[f'R{rid:02d}'] = f'{grp}-{n:02d}'
            table[grp].append((f'{grp}-{n:02d}', legacy, 'Guideline'))
        for cid in CHECKLIST_GROUPS.get(grp, []):
            n += 1
            assigned[cid] = f'{grp}-{n:02d}'
            table[grp].append((f'{grp}-{n:02d}', cid, 'Checklist'))
        for cid in CODE_GROUPS.get(grp, []):
            n += 1
            assigned[cid] = f'{grp}-{n:02d}'
            table[grp].append((f'{grp}-{n:02d}', cid, 'Code web app'))
        for oid in OTHER_GROUPS.get(grp, []):
            n += 1
            assigned[oid] = f'{grp}-{n:02d}'
            table[grp].append((f'{grp}-{n:02d}', oid, 'Văn bản khác'))
    return assigned, table


def check(assigned: dict[str, str]) -> list[str]:
    """Mọi quy tắc của cả bốn nguồn phải có mã, hoặc có lý do loại/gộp."""
    errs: list[str] = []

    for i in range(1, 111):
        if f'R{i:02d}' not in assigned and i not in GUIDELINE_DROP:
            errs.append(f'Guideline R{i:02d}: chưa gán nhóm và cũng không có lý do loại')
    dup = [g for g, v in collections.Counter(
        i for lst in GUIDELINE_GROUPS.values() for i in lst).items() if v > 1]
    if dup:
        errs.append(f'Guideline gán trùng nhóm: {dup}')

    src = (ROOT / 'docs/0.1-danh-sach-quy-tac.md').read_text(encoding='utf-8')
    code_ids = {m.group(1) for m in re.finditer(r'^\|\s*([A-Z0-9]{2,3}-\d{2})\s*\|', src, re.M)}
    covered = set(CODE_MERGE) | set(CODE_DROP) | {c for v in CODE_GROUPS.values() for c in v}
    for c in sorted(code_ids - covered):
        errs.append(f'Code {c}: chưa xử lý (gộp / loại / gán mã)')
    for c in sorted(covered - code_ids - {'RDS-03'}):
        errs.append(f'Code {c}: có trong registry nhưng KHÔNG có trong tài liệu nguồn')

    src = (ROOT / 'docs/rules/rules-checklist-flat.md').read_text(encoding='utf-8')
    cl_m: set[str] = set()
    for line in src.splitlines():
        cells = line.split('|')
        if not line.startswith('| `CL-') or len(cells) != 10:
            continue
        m = re.match(r'`(CL-[\d\w.]+)`', cells[1].strip())
        if m and cells[5].strip().strip('*').startswith('M'):
            cl_m.add(m.group(1))
    got = {c for v in CHECKLIST_GROUPS.values() for c in v}
    for c in sorted(cl_m - got):
        errs.append(f'Checklist {c} (trạng thái M = mới): chưa gán mã')
    for c in sorted(got - cl_m):
        errs.append(f'Checklist {c}: đã gán mã nhưng KHÔNG phải trạng thái M')
    return errs


def write_map(assigned: dict[str, str], table: dict[str, list]) -> None:
    L: list[str] = []
    A = L.append
    A('# Mục 0.5 — Bảng mã chính thức của bộ quy tắc\n')
    A('> **Sinh bằng `scripts/build_rule_ids.py`** (công cụ dùng một lần).')
    A('>')
    A('> ⚠️ **Mã trong bảng này là CỐ ĐỊNH.** Đổi mã sẽ làm hỏng liên kết với eval set')
    A('> (`PLAN.md` mục 0.7) và với `rule_ref` của mọi finding đã lưu.')
    A('>')
    A('> Quy ước gán: nhóm theo **chủ đề / loại thiết bị**, KHÔNG theo module phần mềm —')
    A('> module đi vào trường `applies_to_module` (quyết định "hai trục",')
    A('> `rules-crossmap.md` mục 5). Số chạy trong từng nhóm, gán **một lượt** cho cả bộ')
    A('> để nhóm chứa lẫn quy tắc định lượng và định tính không phải đánh số hai lần.\n')
    A(f'**Tổng: {len(assigned)} quy tắc** vào `config/rules.yaml`.\n')
    A('| Nhóm | Nghĩa | Số quy tắc | Dải mã |')
    A('|---|---|---:|---|')
    means = {
        'ALC': 'Cấp phát, thu hồi', 'ARC': 'Kiến trúc, dự phòng, hạ tầng',
        'BAK': 'Sao lưu', 'CPU': 'CPU và quy đổi SPEC', 'EVD': 'Sở cứ & mô tả bắt buộc',
        'FWL': 'Firewall', 'KPI': 'Ngưỡng & hệ số chung', 'LAN': 'LAN switch',
        'LBA': 'Cân bằng tải', 'MTH': 'Phương pháp định cỡ (Dạng I/II/III)',
        'PRC': 'Thủ tục & quy trình', 'RAM': 'RAM', 'RCK': 'Tủ Rack',
        'SAN': 'SAN switch', 'STO': 'Lưu trữ', 'TST': 'Kiểm thử hiệu năng',
    }
    for grp in sorted(table):
        ids = [r[0] for r in table[grp]]
        A(f'| `{grp}` | {means.get(grp, "")} | {len(ids)} | `{ids[0]}` … `{ids[-1]}` |')
    A('')
    A('> Nhóm `CHK` đã dự trù ở `rules-crossmap.md` mục 6 nhưng **không dùng đến**:')
    A('> mọi mục checklist đều gắn được vào một nhóm chủ đề có sẵn.\n')
    A('---\n')
    A('## Bảng mã đầy đủ\n')
    for grp in sorted(table):
        A(f'### `{grp}` — {means.get(grp, "")}\n')
        A('| Mã chính thức | `legacy_ref` | Nguồn |')
        A('|---|---|---|')
        for code, legacy, src in table[grp]:
            A(f'| `{code}` | `{legacy}` | {src} |')
        A('')
    A('---\n')
    A('## Quy tắc KHÔNG vào `rules.yaml` — ghi lý do, không im lặng bỏ\n')
    A('### Từ Guideline\n')
    A('| Mã tạm | Lý do |')
    A('|---|---|')
    for rid, why in sorted(GUIDELINE_DROP.items()):
        A(f'| `R{rid:02d}` | {why} |')
    A('')
    A('### Từ code web app\n')
    A('| Mã tạm | Lý do |')
    A('|---|---|')
    for cid, why in sorted(CODE_DROP.items()):
        A(f'| `{cid}` | {why} |')
    A('')
    A('> Bốn dòng `RDS-04`, `RDS-10`, `LBF-01`, `LBF-02` là **lỗi tính toán đang chạy')
    A('> thật trên web app** (`rules-crossmap.md` mục 2). Copilot số hóa theo Guideline')
    A('> cho đúng; việc sửa code là của đội bảo trì web app.\n')
    A('---\n')
    A('## Quy tắc code web app được GỘP vào quy tắc Guideline\n')
    A('Không tạo quy tắc mới — chỉ thêm `code_ref` vào quy tắc Guideline tương ứng, để')
    A('khi code đổi thì còn đối chiếu được.\n')
    A('| Mã code | Gộp vào | Mã chính thức |')
    A('|---|---|---|')
    for cid, target in sorted(CODE_MERGE.items()):
        A(f'| `{cid}` | `{target}` | `{assigned.get(target, "— (gộp nội bộ)")}` |')
    A('')
    (ROOT / 'docs/rules/rules-id-map.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('\n-> đã ghi docs/rules/rules-id-map.md')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--write', action='store_true', help='ghi docs/rules/rules-id-map.md')
    args = ap.parse_args()

    assigned, table = build()
    errs = check(assigned)

    print(f'Đã gán mã cho {len(assigned)} quy tắc.')
    print(f'  Guideline : {sum(len(v) for v in GUIDELINE_GROUPS.values()):>3}'
          f'   (loại/gộp {len(GUIDELINE_DROP)})')
    print(f'  Checklist : {sum(len(v) for v in CHECKLIST_GROUPS.values()):>3}'
          f'   (18 mục trạng thái T chỉ gắn checklist_ref)')
    print(f'  Code web  : {sum(len(v) for v in CODE_GROUPS.values()):>3}'
          f'   (gộp {len(CODE_MERGE)}, loại {len(CODE_DROP)})')
    print(f'  Khác      : {sum(len(v) for v in OTHER_GROUPS.values()):>3}')
    print()
    for grp in sorted(table):
        ids = [r[0] for r in table[grp]]
        print(f'  {grp}: {len(ids):>2} quy tắc   {ids[0]} .. {ids[-1]}')

    if errs:
        print(f'\n❌ {len(errs)} vấn đề:')
        for e in errs:
            print('   ', e)
        return 1
    print('\n✅ Kiểm tra đầy đủ: mọi quy tắc của cả bốn nguồn đều đã có mã '
          'hoặc có lý do loại/gộp.')
    if args.write:
        write_map(assigned, table)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
