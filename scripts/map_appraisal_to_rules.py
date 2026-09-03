#!/usr/bin/env python
"""Đối chiếu vấn đề thẩm định thật (`approved-sizing/`) với 150 quy tắc trong rules.yaml.

Trả lời một câu hỏi mà đến giờ chưa ai trả lời: **bộ quy tắc dựng từ văn bản có khớp
với thứ người thẩm định thật sự bắt không?**

Cách làm — và vì sao làm thế
----------------------------
Không ánh xạ tay từng vấn đề trong 667 vấn đề: vừa lâu vừa không ai kiểm lại được.
Thay vào đó tách làm hai lớp:

  1. **Gán CHỦ ĐỀ bằng từ khóa** — thuần máy, quy tắc gán nằm ngay trong `THEMES`
     dưới đây nên đọc lại và sửa được.
  2. **Ánh xạ CHỦ ĐỀ -> quy tắc** — đây là phần phán đoán nghiệp vụ, ~30 dòng thay vì
     667 dòng, nên người duyệt kiểm được trong vài phút.

Mỗi chủ đề mang sẵn `do_tin_cay` nói ánh xạ đó chắc tới đâu. Chủ đề có `rules: []`
là **khoảng trống** — người thẩm định bắt nhưng không quy tắc nào phủ.

⚠️ Nguồn là tóm tắt do AI khác viết lại, không phải nguyên văn PNX (xem
`scripts/extract_appraisal_issues.py`). Kết quả dùng để **soi lại bộ quy tắc**,
KHÔNG dùng làm nhãn chấm điểm.

Cách dùng
---------
    uv run python scripts/extract_appraisal_issues.py     # chạy trước
    uv run python scripts/map_appraisal_to_rules.py
"""

from __future__ import annotations

import collections
import json
import pathlib
import sys

try:
    import yaml
except ImportError:
    sys.exit('Cần PyYAML:  uv add pyyaml')

ROOT = pathlib.Path(__file__).resolve().parent.parent
ISSUES = ROOT / 'docs/rules/.tmp-appraisal/issues.json'
RULES = ROOT / 'config/rules.yaml'

# =============================================================================
# BẢNG CHỦ ĐỀ — phần cần người duyệt đọc kỹ
#
#   tu_khoa    : khớp trên (tiêu đề + ngữ cảnh), đã hạ về chữ thường
#   rules      : mã quy tắc phủ chủ đề này; [] nghĩa là KHOẢNG TRỐNG
#   do_tin_cay : cao  — chủ đề và quy tắc nói đúng một việc
#                vừa  — có phủ nhưng lệch phạm vi, cần người xác nhận
#                thấp — từ khóa khớp rộng, dễ dính nhầm
# =============================================================================
THEMES: dict[str, dict] = {
    'Sở cứ / minh chứng cho số liệu': {
        'tu_khoa': ['sở cứ', 'justif', 'evidence', 'minh chứng', 'screenshot',
                    'ảnh chụp', 'hình ảnh', 'chứng minh', 'link spec', 'dẫn chứng'],
        'rules': ['EVD-09', 'EVD-03', 'PRC-01', 'PRC-02'],
        'do_tin_cay': 'cao',
    },
    'Dự phòng N+1 / HA': {
        'tu_khoa': ['n+1', 'n+2', 'redundan', 'dự phòng', 'high avail',
                    'active-active', 'active-standby', 'failover', 'quorum'],
        'rules': ['ARC-02', 'ARC-03', 'ARC-09', 'ARC-12', 'ARC-27'],
        'do_tin_cay': 'cao',
    },
    'DC-DR cho hệ đặc biệt quan trọng': {
        'tu_khoa': ['dc-dr', 'disaster', 'đbqt', 'đặc biệt quan trọng'],
        'rules': ['ARC-26'],
        'do_tin_cay': 'cao',
    },
    'Ngưỡng KPI 75/90/80': {
        'tu_khoa': ['kpi', 'utilization', '75%', '90%'],
        'rules': ['KPI-02', 'KPI-03', 'KPI-04', 'KPI-14'],
        'do_tin_cay': 'cao',
    },
    'IOPS / latency': {
        'tu_khoa': ['iops', 'latency'],
        'rules': ['KPI-05', 'STO-01', 'STO-08', 'STO-12', 'EVD-07'],
        'do_tin_cay': 'cao',
    },
    'Chọn loại ổ / SSD': {
        'tu_khoa': ['ssd', 'hdd', 'nl-sas', 'loại ổ', 'disk type'],
        'rules': ['STO-02', 'STO-03', 'STO-13', 'STO-14', 'STO-15', 'KPI-07'],
        'do_tin_cay': 'cao',
    },
    'Sao lưu / backup': {
        'tu_khoa': ['backup', 'sao lưu', 'restore', 'tape'],
        'rules': ['BAK-01', 'BAK-02', 'BAK-09', 'STO-06', 'STO-18'],
        'do_tin_cay': 'cao',
    },
    'LB / Firewall / băng thông': {
        'tu_khoa': ['load balancer', 'firewall', 'băng thông', 'bandwidth',
                    'throughput'],
        'rules': ['LBA-01', 'LBA-02', 'FWL-01', 'FWL-02', 'FWL-03', 'FWL-04',
                  'ARC-01'],
        'do_tin_cay': 'cao',
    },
    'Mô hình logic / vật lý': {
        'tu_khoa': ['mô hình logic', 'mô hình vật lý', 'architecture', 'diagram',
                    'sơ đồ', 'logical model', 'physical model'],
        'rules': ['EVD-13', 'EVD-14', 'EVD-19', 'EVD-20'],
        'do_tin_cay': 'cao',
    },
    'Tải đầu vào CCU / TPS / peak': {
        'tu_khoa': ['ccu', 'tps', 'rps', 'request rate', 'concurrent', 'workload',
                    'peak', 'giao dịch đồng thời'],
        'rules': ['EVD-05', 'EVD-11', 'KPI-01', 'KPI-10'],
        'do_tin_cay': 'cao',
    },
    'CPU / SPEC / Cint': {
        'tu_khoa': ['cint', 'spec cpu', 'specrate', 'cpu2017', 'vcpu'],
        'rules': ['CPU-01', 'CPU-02', 'CPU-05', 'CPU-06', 'CPU-09', 'CPU-10'],
        'do_tin_cay': 'cao',
    },
    'Phương pháp định cỡ / hệ tham chiếu': {
        'tu_khoa': ['methodology', 'phương pháp', 'reference system', 'hệ tham chiếu',
                    'scaling factor', 'tương đồng', 'benchmark'],
        'rules': ['MTH-01', 'MTH-02', 'MTH-03', 'MTH-04', 'KPI-12'],
        'do_tin_cay': 'cao',
    },
    'Số node / cấu hình cụm': {
        'tu_khoa': ['số node', 'node count', 'cluster', 'broker', 'master', 'slave',
                    'replica'],
        'rules': ['ARC-08', 'ARC-09', 'ARC-19', 'ARC-20', 'ARC-21', 'ARC-22',
                  'ARC-23', 'ARC-24', 'ARC-25'],
        'do_tin_cay': 'vừa',
    },
    'Nhất quán số liệu giữa các bảng': {
        'tu_khoa': ['inconsistency', 'không nhất quán', 'mâu thuẫn', 'consistency',
                    'load numbers must be consistent'],
        'rules': ['EVD-10', 'ARC-09', 'ARC-22'],
        'do_tin_cay': 'vừa',
    },
    'Mục đích / phạm vi sizing': {
        'tu_khoa': ['mục đích', 'purpose', 'scope', 'phạm vi', 'mới hay bổ sung'],
        'rules': ['MTH-01', 'PRC-09'],
        'do_tin_cay': 'vừa',
    },
    'Dung lượng lưu trữ': {
        'tu_khoa': ['dung lượng', 'storage'],
        'rules': ['STO-04', 'STO-05', 'KPI-06', 'EVD-01'],
        'do_tin_cay': 'vừa',
    },
    'RAM': {
        'tu_khoa': ['ram', 'memory', 'bộ nhớ'],
        'rules': ['RAM-01', 'RAM-02', 'KPI-03'],
        'do_tin_cay': 'thấp',      # từ 'ram' dính cả 'program', 'parameter'
    },
    'Kết nối / port': {
        'tu_khoa': ['connection', 'kết nối', 'port', 'policy table'],
        'rules': ['ARC-16', 'FWL-04'],
        'do_tin_cay': 'vừa',
    },
    'Thủ tục / phê duyệt': {
        # KHÔNG dùng 'mandatory': quá rộng, kéo cả "ĐBQT DR mandatory" vào đây
        # trong khi đó là chủ đề DC-DR.
        'tu_khoa': ['ký duyệt', 'phê duyệt', 'tờ trình', 'biên bản', 'formal approval',
                    'qhđc'],
        'rules': ['PRC-01', 'PRC-02', 'PRC-03', 'PRC-05'],
        'do_tin_cay': 'vừa',
    },

    # ---------------------------------------------------------------------
    # KHOẢNG TRỐNG — người thẩm định bắt, không quy tắc nào phủ
    # ---------------------------------------------------------------------
    'KHOẢNG TRỐNG · Sở cứ cho tốc độ tăng trưởng dữ liệu': {
        'tu_khoa': ['tăng trưởng', 'growth rate', 'historical data', 'trend analysis',
                    'storage projection', 'growth calculation'],
        'rules': [],
        'do_tin_cay': 'cao',
        'ghi_chu': 'PNX hỏi thẳng "sở cứ cho mức tăng trưởng 20%/năm là gì?", đòi log '
                   'history hoặc trend analysis. Guideline không có quy tắc nào về '
                   'tốc độ tăng trưởng. KPI-16 (tăng trưởng 01 năm) đang `enabled: false`.',
    },
    'KHOẢNG TRỐNG · Nhất quán chu kỳ lưu trữ giữa các phân vùng': {
        'tu_khoa': ['timeline', 'retention', 'thời gian lưu', 'multi-timeline'],
        'rules': [],
        'do_tin_cay': 'cao',
        'ghi_chu': 'Ca thật: App 6 tháng · /data 2 năm · /log 6 tháng · /backup 4 ngày, '
                   'không giải thích vì sao khác nhau. Không quy tắc nào bắt được sự '
                   'không nhất quán này. ALC-01 chỉ kiểm mốc 06 tháng của cấp phát.',
    },
    'KHOẢNG TRỐNG · Kiểm tính hợp lý đơn vị số liệu đầu vào': {
        'tu_khoa': ['sanity', 'vô lý', 'đơn vị tính', 'notation', 'unit'],
        'rules': [],
        'do_tin_cay': 'cao',
        'ghi_chu': 'Ca thật: khai "3.000.000 TB cho 1.080 người dùng" = 2,7 PB mỗi '
                   'người. Đây là phép kiểm rẻ và bắt được lỗi nặng, thuần code làm '
                   'được, nhưng không quy tắc nào có.',
    },
    'KHOẢNG TRỐNG · Cấp bổ sung phải tính phần TĂNG THÊM': {
        'tu_khoa': ['expansion delta', 'delta not total', 'greenfield', 'brownfield',
                    'deployment scenario', 'bổ sung hay tổng'],
        'rules': [],
        'do_tin_cay': 'vừa',
        'ghi_chu': 'PNX bắt lỗi khai TỔNG tài nguyên trong khi hồ sơ là cấp BỔ SUNG — '
                   'phải khai phần tăng thêm. CL-2.1 chỉ hỏi "mới hay bổ sung", không '
                   'ràng buộc cách khai con số.',
    },
    'KHOẢNG TRỐNG · Phải trình bày công thức, không chỉ kết quả': {
        'tu_khoa': ['formula is not optional', 'bảng tính toán', 'công thức tính',
                    'giải thích gap'],
        'rules': [],
        'do_tin_cay': 'vừa',
        'ghi_chu': 'PNX đòi bảng tính trung gian để lần được từ đầu vào tới kết quả. '
                   'EVD-09 chỉ yêu cầu mọi con số truy được nguồn, không yêu cầu hiện '
                   'phép tính.',
    },
    'KHOẢNG TRỐNG · Làm tròn và độ chính xác số trung gian': {
        'tu_khoa': ['rounding', 'làm tròn', 'precision', 'độ chính xác'],
        'rules': [],
        'do_tin_cay': 'cao',
        'ghi_chu': 'PNX xếp lỗi làm tròn số trung gian là CRITICAL. `globals.lam_tron` '
                   'mới là quy ước làm tròn kết quả cuối, chưa thành quy tắc kiểm.',
    },
    'KHOẢNG TRỐNG · Sizing phần mềm bên thứ ba / vendor': {
        'tu_khoa': ['vendor', 'bên thứ 3', 'hãng xác nhận', 'third party'],
        'rules': [],
        'do_tin_cay': 'vừa',
        'ghi_chu': 'PNX chấp nhận email hãng xác nhận làm sở cứ khi phần mềm do vendor '
                   'cung cấp. Guideline không nói gì về trường hợp này.',
    },
    'KHOẢNG TRỐNG · Sizing ứng cứu khẩn cấp': {
        'tu_khoa': ['emergency sizing', 'ứng cứu', 'uctt'],
        'rules': [],
        'do_tin_cay': 'vừa',
        'ghi_chu': 'Có luồng riêng (VTNet UCTT) với hệ số dự phòng khác. Bốn dạng định '
                   'cỡ MTH-01..04 không có dạng này.',
    },
    'KHOẢNG TRỐNG · Định cỡ GPU / tải AI': {
        'tu_khoa': ['gpu', 'nvidia', 'cuda', 'ai workload', 'speech processing'],
        'rules': [],
        'do_tin_cay': 'cao',
        'ghi_chu': 'Đã biết trước: Guideline lần 07 không có nội dung GPU nào '
                   '(PLAN.md mục 0.12f). Nay có bằng chứng là thực tế CÓ phát sinh.',
    },
}


def load_rules() -> dict[str, dict]:
    doc = yaml.safe_load(RULES.read_text(encoding='utf-8'))
    return {r['id']: r for r in doc.get('rules') or []}


def assign(issue: dict) -> tuple[list[str], list[str]]:
    """Trả về (chủ đề khớp ở TIÊU ĐỀ, chủ đề chỉ khớp ở NGỮ CẢNH).

    Phải tách hai mức. Dò từ khóa trên cả đoạn ngữ cảnh sinh ra khớp nhầm rõ rệt —
    kiểm tay 5 ca ngẫu nhiên thấy "PNM system sizing best practices" dính chủ đề RAM,
    "Table format" dính chủ đề dự phòng N+1, chỉ vì từ khóa nằm đâu đó trong đoạn văn.

    Khớp ở TIÊU ĐỀ mới tính là bằng chứng chắc. Khớp ở NGỮ CẢNH giữ lại nhưng đếm
    riêng, không đưa vào con số "quy tắc được thực tế xác nhận".
    """
    tieu_de = issue['tieu_de'].lower()
    ngu_canh = issue.get('ngu_canh', '').lower()
    chac, gian_tiep = [], []
    for t, d in THEMES.items():
        if any(k in tieu_de for k in d['tu_khoa']):
            chac.append(t)
        elif any(k in ngu_canh for k in d['tu_khoa']):
            gian_tiep.append(t)
    return chac, gian_tiep


def main() -> int:
    if not ISSUES.is_file():
        sys.exit('Chưa có issues.json — chạy scripts/extract_appraisal_issues.py trước.')
    recs = json.loads(ISSUES.read_text(encoding='utf-8'))
    rules = load_rules()

    # mã quy tắc trong THEMES phải có thật, nếu không báo cáo sẽ trỏ vào hư không
    bad = sorted({r for d in THEMES.values() for r in d['rules'] if r not in rules})
    if bad:
        sys.exit(f'THEMES trỏ tới mã quy tắc không tồn tại: {bad}')

    theme_count: collections.Counter = collections.Counter()
    theme_docs: dict[str, set] = collections.defaultdict(set)
    rule_count: collections.Counter = collections.Counter()
    rule_docs: dict[str, set] = collections.defaultdict(set)
    chua_phan_loai: list[tuple[str, str]] = []
    rows: list[tuple] = []

    gt_count: collections.Counter = collections.Counter()
    for r in recs:
        for v in r['van_de']:
            themes, gian_tiep = assign(v)
            if not themes and not gian_tiep:
                chua_phan_loai.append((r['ho_so'], v['tieu_de']))
            for t in themes:
                theme_count[t] += 1
                theme_docs[t].add(r['ho_so'])
                for rid in THEMES[t]['rules']:
                    rule_count[rid] += 1
                    rule_docs[rid].add(r['ho_so'])
            for t in gian_tiep:
                gt_count[t] += 1
            rows.append((r['ho_so'], v['tieu_de'], themes))

    tong = sum(len(r['van_de']) for r in recs)
    print(f'{tong} vấn đề · {len(recs)} hồ sơ')
    print(f'  khớp ở TIÊU ĐỀ (tính là bằng chứng) : {sum(theme_count.values()):>4} lượt')
    print(f'  khớp ở NGỮ CẢNH (đếm riêng, KHÔNG tính): {sum(gt_count.values()):>4} lượt')
    print(f'  không khớp chủ đề nào                 : {len(chua_phan_loai):>4} vấn đề\n')

    gaps = [t for t in THEMES if not THEMES[t]['rules'] and theme_count[t]]
    print(f'KHOẢNG TRỐNG — {len(gaps)} chủ đề bị bắt mà không quy tắc nào phủ:')
    for t in sorted(gaps, key=lambda x: -theme_count[x]):
        print(f'  {theme_count[t]:>4} lần / {len(theme_docs[t]):>2} hồ sơ  {t}')

    da_bat = [rid for rid in rules if rule_count[rid]]
    chua_bat = [rid for rid in rules if not rule_count[rid]]
    print(f'\nQuy tắc: {len(da_bat)}/{len(rules)} có ít nhất một vấn đề khớp · '
          f'{len(chua_bat)} chưa lần nào')

    write_reports(recs, rules, theme_count, theme_docs, rule_count, rule_docs,
                  chua_phan_loai, rows, tong, gt_count)
    print('\n-> docs/rules/appraisal-mapping.md')
    print('-> docs/rules/rules-doi-chieu-thuc-te.md')
    return 0


def write_reports(recs, rules, theme_count, theme_docs, rule_count, rule_docs,
                  chua_phan_loai, rows, tong, gt_count) -> None:
    warn = [
        '> ⚠️ **Nguồn là tóm tắt do một AI khác (Cline) viết lại từ hồ sơ đã ký, KHÔNG',
        '> phải nguyên văn Phiếu Nhận Xét.** Bản gốc `.docx`/`.pdf` không còn (xác nhận',
        '> 2026-08-26). Dùng để **soi lại bộ quy tắc**; KHÔNG dùng làm nhãn chấm điểm —',
        '> làm vậy sẽ cho recall ảo và vi phạm NT2.', '']

    # ---------- 1. appraisal-mapping.md ----------
    L = ['# Ánh xạ vấn đề thẩm định thật → quy tắc\n',
         '> Sinh bằng `scripts/map_appraisal_to_rules.py`. **Không sửa tay** — sửa bảng',
         '> `THEMES` trong script rồi chạy lại.\n', *warn,
         '## Cách đọc\n',
         'Ánh xạ đi qua hai lớp: vấn đề → **chủ đề** (máy gán bằng từ khóa) → **quy tắc**',
         '(người gán). Nhờ vậy phần cần duyệt chỉ là ~30 dòng bảng chủ đề dưới đây, thay',
         f'vì {tong} dòng vấn đề.\n',
         '`độ tin cậy`: **cao** = chủ đề và quy tắc nói đúng một việc · **vừa** = có phủ',
         'nhưng lệch phạm vi · **thấp** = từ khóa khớp rộng, dễ dính nhầm.\n',
         '**Chỉ đếm khớp ở TIÊU ĐỀ.** Bản đầu dò từ khóa trên cả đoạn ngữ cảnh và sinh',
         'khớp nhầm rõ rệt — kiểm tay 5 ca ngẫu nhiên thấy *"PNM system sizing best',
         'practices"* dính chủ đề RAM, *"Table format"* dính chủ đề dự phòng N+1. Nay',
         f'khớp-ở-ngữ-cảnh ({sum(gt_count.values())} lượt) vẫn dò nhưng **không** tính vào',
         'số liệu, để con số ở đây không bị thổi phồng.\n',
         '## Bảng chủ đề → quy tắc\n',
         '| Chủ đề | Số lần | Hồ sơ | Quy tắc phủ | Độ tin cậy |',
         '|---|---:|---:|---|:--:|']
    for t, d in sorted(THEMES.items(), key=lambda x: -theme_count[x[0]]):
        if not theme_count[t]:
            continue
        rl = ' '.join(f'`{r}`' for r in d['rules']) or '**— không có —**'
        L.append(f"| {t} | {theme_count[t]} | {len(theme_docs[t])} | {rl} "
                 f"| {d['do_tin_cay']} |")
    L.append('')
    ghi = [(t, d) for t, d in THEMES.items() if d.get('ghi_chu') and theme_count[t]]
    if ghi:
        L += ['### Ghi chú từng chủ đề khoảng trống\n']
        for t, d in ghi:
            L += [f"**{t}** — {theme_count[t]} lần, {len(theme_docs[t])} hồ sơ  ",
                  f"{d['ghi_chu']}\n"]
    thap = [t for t, d in THEMES.items() if d['do_tin_cay'] == 'thấp' and theme_count[t]]
    if thap:
        L += ['### ⚠️ Chủ đề độ tin cậy THẤP — cần người duyệt xem lại\n']
        for t in thap:
            L.append(f'- **{t}** ({theme_count[t]} lần) — từ khóa khớp rộng, '
                     f'số liệu này có thể bị thổi phồng.')
        L.append('')
    if chua_phan_loai:
        L += [f'### Chưa phân loại — {len(chua_phan_loai)} vấn đề\n',
              'Không khớp chủ đề nào. Có thể là nhãn mục (không phải vấn đề), hoặc là',
              'khoảng trống chưa nhận ra. Cần đọc tay.\n',
              '| Hồ sơ | Vấn đề |', '|---|---|']
        for ho, td in chua_phan_loai:
            L.append(f"| {ho[:34]} | {td.replace('|', chr(92) + '|')[:78]} |")
        L.append('')
    (ROOT / 'docs/rules/appraisal-mapping.md').write_text('\n'.join(L) + '\n',
                                                          encoding='utf-8')

    # ---------- 2. rules-doi-chieu-thuc-te.md ----------
    gaps = [t for t in THEMES if not THEMES[t]['rules'] and theme_count[t]]
    da_bat = sorted((rid for rid in rules if rule_count[rid]),
                    key=lambda r: -rule_count[r])
    chua_bat = sorted(rid for rid in rules if not rule_count[rid])
    vong = [r['so_vong'] for r in recs if r['so_vong']]

    R = ['# Đối chiếu 150 quy tắc với hành vi thẩm định thật\n',
         '> Sinh bằng `scripts/map_appraisal_to_rules.py`. Chi tiết ánh xạ:',
         '> [`appraisal-mapping.md`](appraisal-mapping.md). Dữ liệu thô:',
         '> `.tmp-appraisal/issues.md`.\n', *warn,
         '## Vì sao cần việc này\n',
         'Toàn bộ 150 quy tắc suy ra từ **văn bản** — Guideline, checklist thẩm định,',
         'code web app. Chưa lần nào đối chiếu với **hành vi**: người thẩm định thật sự',
         f'bắt gì. Kho `approved-sizing/` cho {tong} vấn đề trên {len(recs)} hồ sơ đã ký,',
         'là dịp duy nhất đang có để kiểm điều đó.\n',
         '## Số liệu\n',
         f'- **{len(recs)} hồ sơ** · {sum(1 for r in recs if r["loai_ho_so"] == "A")} '
         f'có phản biện (PNX) · {sum(1 for r in recs if r["loai_ho_so"] == "B")} duyệt thẳng',
         f'- **{tong} vấn đề** trích được · {sum(theme_count.values())} lượt khớp chủ đề **ở tiêu đề**',
         f'  (khớp trong đoạn ngữ cảnh: {sum(gt_count.values())} lượt — dò nhưng KHÔNG tính, xem lý do',
         '  ở `appraisal-mapping.md`)',
         f'- **{len(da_bat)}/{len(rules)} quy tắc** có ít nhất một vấn đề thực tế khớp',
         f'- **{len(gaps)} khoảng trống** — chủ đề bị bắt mà không quy tắc nào phủ']
    if vong:
        R.append(f'- Số vòng phản hồi trung bình **{sum(vong)/len(vong):.2f}** '
                 f'({len(vong)} hồ sơ ghi rõ, phân bố '
                 f'{dict(sorted(collections.Counter(vong).items()))})')
    R += ['', '---\n',
          '## 1. Khoảng trống — kết quả quan trọng nhất\n',
          'Người thẩm định bắt những thứ này, `rules.yaml` không có quy tắc nào phủ.\n',
          '| Chủ đề | Số lần | Hồ sơ | Vì sao chưa phủ |', '|---|---:|---:|---|']
    for t in sorted(gaps, key=lambda x: -theme_count[x]):
        R.append(f"| **{t.replace('KHOẢNG TRỐNG · ', '')}** | {theme_count[t]} | "
                 f"{len(theme_docs[t])} | {THEMES[t].get('ghi_chu', '')} |")
    R += ['', '> **Không tự thêm quy tắc nào từ bảng này.** Thêm quy tắc là mở lại',
          '> 0.1–0.4 và phải có người duyệt. Bộ 150 quy tắc giữ nguyên cho tới lúc đó.\n',
          '---\n',
          '## 2. Quy tắc được thực tế xác nhận\n',
          'Xếp theo số lần vấn đề thực tế khớp. Đây là phần đáng tin nhất của bộ quy tắc —',
          'có căn cứ văn bản **và** có bằng chứng người thẩm định thật sự soi.\n',
          '| Quy tắc | Tên | Số lần | Hồ sơ | Mức hiện tại |', '|---|---|---:|---:|:--:|']
    for rid in da_bat[:40]:
        R.append(f"| `{rid}` | {rules[rid]['name'][:52]} | {rule_count[rid]} | "
                 f"{len(rule_docs[rid])} | {rules[rid]['severity']} |")
    if len(da_bat) > 40:
        R.append(f'\n_(còn {len(da_bat) - 40} quy tắc nữa, xem `appraisal-mapping.md`)_')
    R += ['', '---\n',
          f'## 3. Quy tắc chưa lần nào khớp — {len(chua_bat)} quy tắc\n',
          '**Không có nghĩa là quy tắc sai.** Ba lý do có thể, phải phân biệt:\n',
          '1. Quy tắc đúng nhưng **hiếm gặp** (SAN switch, tủ Rack, tape) — giữ nguyên.',
          '2. Vấn đề **có bị bắt** nhưng bản tóm tắt của AI không ghi lại đủ chi tiết',
          '   để từ khóa nhận ra — lỗi của nguồn, không phải của quy tắc.',
          '3. Quy tắc thật sự **không ai soi** — mới là ứng viên xem lại.\n',
          'Với nguồn gián tiếp như thế này, **không đủ căn cứ để bỏ quy tắc nào**.\n']
    by_g: dict[str, list[str]] = collections.defaultdict(list)
    for rid in chua_bat:
        by_g[rid.split('-')[0]].append(rid)
    R += ['| Nhóm | Chưa khớp | Mã |', '|---|---:|---|']
    for g in sorted(by_g):
        R.append(f"| `{g}` | {len(by_g[g])} | {' '.join(f'`{x}`' for x in by_g[g])} |")
    R += ['', '---\n', '## 4. Khuyến nghị — nêu ra, KHÔNG tự áp dụng\n',
          '1. **Quyết định về 9 khoảng trống ở mục 1.** Ít nhất ba chỗ đáng thành quy tắc',
          '   định lượng vì thuần code kiểm được: kiểm hợp lý đơn vị số liệu đầu vào,',
          '   nhất quán chu kỳ lưu trữ giữa các phân vùng, và làm tròn số trung gian.',
          '2. **Xem lại `KPI-16`** (tăng trưởng) đang `enabled: false` — thực tế cho thấy',
          '   tốc độ tăng trưởng bị hỏi sở cứ thường xuyên. Nhưng bật lên thì phải giải',
          '   quyết mâu thuẫn 01 năm ↔ 06 tháng với `ALC-01` trước.',
          '3. **Chưa đủ căn cứ điều chỉnh `severity`** theo tần suất. Nguồn là tóm tắt',
          '   gián tiếp, tần suất ở đây phản ánh cả cách AI kia viết lẫn hành vi thật.\n']
    (ROOT / 'docs/rules/rules-doi-chieu-thuc-te.md').write_text('\n'.join(R) + '\n',
                                                                encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
