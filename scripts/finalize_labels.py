#!/usr/bin/env python
"""Produce the final rule_ref for EVERY label and write data/eval_set.json.

Precedence per label (highest first):
  1. MANUAL_VERDICTS   — rows reasoned individually in this file (the tiers the
                         machine is weak on: "không xác định", "khoảng trống")
  2. audit verdicts    — rows in the frozen audit sample (fill_audit_sample.py)
  3. machine suggestion — everything else; accepted as-is per the user's decision
                         "máy gán, người kiểm mẫu" (2026-09-03)

Every final row records `nguon_rule_ref` = người | máy, so a later reader can
tell which labels were actually looked at by a person.

Out-of-scope rows ("ngoài phạm vi", "tham chiếu chéo", headings) keep an empty
rule_ref and are EXCLUDED from eval_set.json — they must not sit in the recall
denominator. Gap rows (a real reviewer demand that no rule covers) are kept in
eval_set.json with rule_ref [] and `khoang_trong` set, so recall can be reported
both "vs. current rules" and "vs. everything the reviewer asked".

Usage
-----
    python scripts/finalize_labels.py data/pnx_labels_suggested.json \
        --audit data/eval_sheet_mau_kiem_daduyet.csv --rules config/rules.yaml \
        --sheet-out data/eval_sheet.csv --eval-out data/eval_set.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys

import yaml

# label_id -> (rule_ref, ngoai_pham_vi, ghi_chu)
# Reasoned 2026-09-03 for the rows the machine could not place.
MANUAL_VERDICTS: dict[str, tuple] = {
    # --- tiêu đề mục lọt qua bộ lọc (phần lớn nay đã bị parser xếp là anchor) ---
    'PNX_2025_Sizing_C360_Mariadb_increase_RAM_new|R1-04-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_APIGee Mini Appv2|R1-06-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_Data Security VTTv2|R2-02-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_FMRA_Sizing_server_Backup_2024_Final_New|R1-02-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_FMRA_Sizing_server_Backup_2024_Final_New|R1-03-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-02-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-03-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-04-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-05-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-06-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-07-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-09-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-10-01': ('', 'x', 'Tiêu đề mục đánh số.'),
    'PNX_PBH 4.0v2|R2-02-01': ('', 'x', 'Tiêu đề mục.'),
    'PNX_SSO 2.0_v3|R1-03-01': ('', 'x', 'Tiêu đề "Mục: thông tin cần bổ sung".'),
    'PNX_Sizing_APIGW-Meta_2024v4|R1-02-03': ('', 'x', 'Tiêu đề mục.'),
    'PNX_vTracking 2.0_v2|R1-04-01': ('', 'x', 'Tiêu đề mục kèm số trang.'),

    # --- thủ tục / hình thức — ngoài phạm vi ---
    'PNX_C360_Public|R1-01-07': ('', 'x', 'Lỗi chính tả — không quy tắc nào, ngoài phạm vi.'),
    'PNX_MySign_v2|R2-01-03': ('', 'x', 'Hướng dẫn cách phản hồi PNX.'),
    'PNX_SSO 2.0_v3|R2-01-01': ('', 'x', 'Nhắc hoàn thiện nhận xét lần 1 — thủ tục.'),
    'PNX_PBH 4.0v2|R2-01-01': ('', 'x',
        'Đánh số trang — hình thức trình bày. PRC-04 (mẫu Phụ lục 01) đang tắt.'),
    'PNX_CAMPAIGN_MANAGEMENT_v3|R1-01-07': ('PRC-11', '',
        'Phải nói rõ thay thế TOÀN BỘ hay MỘT PHẦN cụm IDC/Datalake → mục đích/phạm vi '
        'sizing. Chạm khoảng trống "cấp bổ sung phải tính phần TĂNG THÊM".'),

    # --- QHĐC ---
    'PNX_APIGee Mini Appv2|R1-03-01': ('PRC-07', '',
        'QHDC = quy hoạch định cỡ. Copilot chỉ kiểm tài liệu CÓ NÊU nguồn tài nguyên; '
        'đối chiếu thật với bản QHĐC là việc người thẩm định.'),

    # --- lập bảng giá trị → bảng tổng hợp đề xuất (Vòng 1) ---
    'PNX_Data Security VTTv2|R2-04-01': ('EVD-16; EVD-22', '', ''),
    'PNX_MySign_v2|R2-02-05': ('EVD-16; EVD-22', '', '"giá trj" = giá trị (lỗi gõ trong PNX).'),
    'PNX_PBH 4.0v2|R1-09-02': ('EVD-16; EVD-22', '',
        '"Bảng giá trị N" — nhiều khả năng là bảng đề xuất kèm dự phòng N+1 (xem ARC-09).'),
    'PNX_SSO 2.0_v3|R1-03-05': ('EVD-16; EVD-22', '', ''),
    'PNX_SSO 2.0_v3|R1-06-03': ('EVD-16; EVD-22', '', ''),
    'PNX_giam sat cuoc goi CSKH_bosung2022v4|R1-10-01': ('EVD-22; EVD-16', '',
        'Bảng cho TỪNG cụm → EVD-22 là chính.'),

    # --- mô tả chi tiết phân hệ (Vòng 1) ---
    'PNX_Data Security VTTv2|R2-09-02': ('EVD-17', '', 'Module của từng phân hệ.'),
    'PNX_Data Security VTTv2|R2-09-03': ('EVD-17', '', 'IP DCN của từng phân hệ.'),
    'PNX_Data Security VTTv2|R2-09-04': ('EVD-17', '', 'IP Public của từng phân hệ.'),
    'PNX_Data Security VTTv2|R2-09-05': ('EVD-18', '', 'Hệ điều hành = công nghệ sử dụng.'),
    'PNX_Data Security VTTv2|R2-09-06': ('EVD-18', '', 'Thư viện / phần mềm cài thêm = công nghệ sử dụng.'),
    'PNX_MySign_v2|R1-01-06': ('EVD-17; EVD-10', '',
        'Thiếu hẳn phần định cỡ App, chỉ có DB → thiếu phân hệ (EVD-17) và tổng toàn hệ không đủ (EVD-10).'),
    'PNX_vTracking 2.0_v2|R1-02-07': ('PRC-09', '', 'Đơn vị quản lý dịch vụ = đầu mối/đơn vị.'),
    'PNX_SSO 2.0_v3|R1-03-07': ('PRC-11; EVD-22', '',
        'Cấp mới hay nâng cấp (PRC-11) + chi tiết cần làm với từng máy chủ/FW/LB (EVD-22).'),

    # --- sở cứ (PRC-01) ---
    'PNX_CAMPAIGN_MANAGEMENT_v3|R1-01-02': ('PRC-01', '',
        'Chạm khoảng trống "sở cứ tốc độ tăng trưởng" — KPI-16 đang tắt.'),
    'PNX_MNP|R1-09-02': ('PRC-01', '',
        'Chạm khoảng trống "sở cứ tốc độ tăng trưởng" — KPI-16 đang tắt.'),
    'PNX_callbot inbound CSKH_bosung videobot XMKH_v1.2v2|R1-05-03': ('PRC-01; EVD-05', '',
        'Chạm khoảng trống "định cỡ GPU / tải AI".'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-07-03': ('PRC-01', '',
        'Thiếu hẳn ảnh đo đạc thực trạng = thiếu sở cứ (không phải chất lượng ảnh).'),
    'PNX_hethongVtag_v4|R1-05-01': ('PRC-01', '',
        'Thiếu hẳn ảnh tải thực tế = thiếu sở cứ (không phải chất lượng ảnh).'),
    'PNX_vTracking 2.0_v2|R1-03-08': ('EVD-03; PRC-01', '',
        'Con số 10k không rõ dùng vào đâu → thông số phải ảnh hưởng năng lực (EVD-03), và cần sở cứ.'),
    'PNX_PBH 4.0|R1-02-04': ('EVD-01; PRC-01', '',
        '"50% raw" nằm dưới "Bổ sung sở cứ cho số liệu:" — tỷ lệ dung lượng thô/khả dụng cần sở cứ.'),

    # --- tính toán / nhất quán (Vòng 2) ---
    'PNX_C360_Public|R1-03-07': ('ARC-08; RAM-02', '', 'Tài nguyên chia trên 2 node.'),
    'PNX_PBH 4.0v2|R2-02-02': ('CPU-03; CPU-02', '', 'Chất vấn phép quy đổi 175*20/32.'),
    'PNX_Sizing_APIGW-Meta_2024v4|R1-04-05': ('EVD-10', '', 'Số liệu trên/dưới khác nhau.'),
    'PNX_StrongSwan|R1-02-01': ('FWL-02', '', 'Sửa thông lượng đề xuất theo số tính toán.'),
    'PNX_MySign_v2|R1-01-02': ('FWL-04', '', 'Thiếu hẳn định cỡ thiết bị mạng FW/LB.'),

    # --- "Công thức tính không đúng" — Vtag, mỗi dòng một phân hệ (scope: phan_he) ---
    # Gán theo công thức tổng tài nguyên KPI-13; phân hệ lấy từ dòng tiêu đề đứng trước.
    'PNX_hethongVtag_v4|R1-07-01': ('KPI-13', '',
        'Phân hệ: máy chủ worker. Gán theo công thức tổng (KPI-13); kiểm lại khi đọc bản sizing v1.'),
    'PNX_hethongVtag_v4|R1-10-02': ('KPI-13', '', 'Phân hệ: Postgres.'),
    'PNX_hethongVtag_v4|R1-17-01': ('KPI-13', '',
        'Phân hệ: Mongo và Kafka. Với Kafka còn có thể là ARC-23/STO-21.'),
    'PNX_hethongVtag_v4|R1-21-01': ('KPI-13', '',
        'Phân hệ: Redis. Còn có thể là ARC-22/STO-19/RAM-03.'),
    'PNX_hethongVtag_v4|R1-26-01': ('KPI-13', '', 'Phân hệ: MQTT Broker.'),

    # --- khoảng trống thật: yêu cầu có thật, không quy tắc nào phủ ---
    'PNX_Data Security VTTv2|R1-04-03': ('', '', 'KHOẢNG TRỐNG "phải trình bày công thức".'),
    'PNX_Data Security VTTv2|R1-05-03': ('', '', 'KHOẢNG TRỐNG "phải trình bày công thức".'),
    'PNX_Data Security VTTv2|R1-06-03': ('', '', 'KHOẢNG TRỐNG "phải trình bày công thức".'),
}


import re

# A real reviewer finding with NO subject — "Tính toán lại số liệu" and nothing
# else. It cannot be tied to any rule, but it is not a gap in the rule set
# either: some number in that dossier is wrong. Kept in eval_set.json under its
# own flag so the harness can count it in "recall vs. everything the reviewer
# asked" while leaving it out of "recall vs. the rule set".
KHONG_NEO_RE = re.compile(r'^\s*[-•]?\s*(tính toán lại( số liệu)?|xem lại số liệu|'
                          r'cập nhật lại sizi?ng)\.?\s*$', re.IGNORECASE)


def parse_ids(rule_ref: str) -> list[str]:
    return [x.strip() for x in rule_ref.split(';') if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('labels_json')
    ap.add_argument('--audit', required=True)
    ap.add_argument('--rules', default='config/rules.yaml')
    ap.add_argument('--sheet-out', required=True)
    ap.add_argument('--eval-out', required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    rules = {r['id']: r for r in yaml.safe_load(open(args.rules, encoding='utf-8'))['rules']}
    labels = json.load(open(args.labels_json, encoding='utf-8'))['labels']
    by_id = {l['label_id']: l for l in labels}

    audit: dict[str, dict] = {}
    for r in csv.DictReader(open(args.audit, encoding='utf-8-sig')):
        if r.get('goi_y_dung'):
            audit[r['label_id']] = r

    stray = sorted(set(MANUAL_VERDICTS) - set(by_id))
    if stray:
        print(f'⚠️  {len(stray)} phán quyết thủ công trỏ tới nhãn không còn tồn tại '
              f'(đã thành tiêu đề sau khi sửa parser) — bỏ qua:')
        for s in stray:
            print('   ' + s)
    bad = sorted({x for rr, _, _ in MANUAL_VERDICTS.values() for x in parse_ids(rr)} - set(rules))
    if bad:
        print(f'LỖI: mã quy tắc không có thật: {", ".join(bad)}')
        return 1

    src_count: collections.Counter = collections.Counter()
    final_rows: list[dict] = []
    eval_items: list[dict] = []
    for l in labels:
        lid = l['label_id']
        machine = l.get('rule_ref_goi_y') or []
        tier = l.get('do_tin_cay', '')
        auto_out = tier in ('ngoài phạm vi', 'tham chiếu chéo')

        if lid in MANUAL_VERDICTS:
            rr, ngoai, note = MANUAL_VERDICTS[lid]
            ids = parse_ids(rr)
            nguon = 'người'
            goi_y_dung = audit[lid]['goi_y_dung'] if lid in audit else ''
        elif lid in audit:
            a = audit[lid]
            ids = parse_ids(a['rule_ref'])
            ngoai = a['ngoai_pham_vi']
            note = a['ghi_chu']
            nguon = 'người'
            goi_y_dung = a['goi_y_dung']
        else:
            ids = [] if auto_out else list(machine)
            ngoai = 'x' if auto_out else ''
            note = l.get('ghi_chu_goi_y', '')
            nguon = 'máy'
            goi_y_dung = ''
        src_count[nguon] += 1

        text = l['text']
        if l.get('context_lead'):
            text = f'{l["context_lead"]} {text}'
        cl: list[str] = []
        for rid in ids:
            for c in (rules[rid].get('checklist_ref') or []):
                if c not in cl:
                    cl.append(c)
        rounds = sorted({rules[rid].get('round') for rid in ids}) if ids else []
        khong_neo = (not ids) and (not ngoai) and bool(KHONG_NEO_RE.match(l['text']))
        khoang_trong = (not ids) and (not ngoai) and not khong_neo

        final_rows.append({
            'label_id': lid, 'dossier': l['dossier'], 'pyc': l['pyc'],
            'pnx_file': l.get('pnx_file', ''), 'lan_nhan_xet': l['round'],
            'item_no': l['item_no'],
            'trang': ', '.join(str(p) for p in l['pages']),
            'muc': ', '.join(l['sections']),
            'noi_dung_nhan_xet': text, 'phan_hoi_don_vi': l['unit_response'],
            'rule_ref_goi_y': '; '.join(machine), 'do_tin_cay': tier,
            'can_cu_goi_y': l.get('can_cu_goi_y', ''),
            'ghi_chu_goi_y': l.get('ghi_chu_goi_y', ''),
            'da_kiem': 'x' if nguon == 'người' else '',
            'goi_y_dung': goi_y_dung,
            'rule_ref': '; '.join(ids), 'checklist_ref': '; '.join(cl),
            'vong': '/'.join(str(x) for x in rounds),
            'ngoai_pham_vi': ngoai, 'khoang_trong': 'x' if khoang_trong else '',
            'khong_neo_duoc': 'x' if khong_neo else '',
            'nguon_rule_ref': nguon, 'ghi_chu': note,
        })
        if not ngoai:
            eval_items.append({
                'label_id': lid, 'dossier': l['dossier'], 'pyc': l['pyc'],
                'pnx_file': l.get('pnx_file', ''), 'lan_nhan_xet': l['round'],
                'text': text, 'pages': l['pages'], 'sections': l['sections'],
                'rule_ref': ids, 'checklist_ref': cl, 'vong': rounds,
                'khoang_trong': khoang_trong, 'khong_neo_duoc': khong_neo,
                'nguon_rule_ref': nguon, 'ghi_chu': note,
            })

    cols = list(final_rows[0].keys())
    with open(args.sheet_out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(final_rows)

    n_out = sum(1 for r in final_rows if r['ngoai_pham_vi'])
    n_gap = sum(1 for r in eval_items if r['khoang_trong'])
    n_neo = sum(1 for r in eval_items if r['khong_neo_duoc'])
    n_rule = sum(1 for r in eval_items if r['rule_ref'])
    meta = {
        'generated': '2026-09-03',
        'source': 'PNX của 23 hồ sơ trong danh_sach_sizings_da_duyet/',
        'total_labels': len(labels),
        'excluded_out_of_scope': n_out,
        'eval_labels': len(eval_items),
        'with_rule_ref': n_rule,
        'gap_no_rule': n_gap,
        'unanchorable_no_subject': n_neo,
        'rule_ref_source': dict(src_count),
        'scoring_note': (
            'Một finding của Copilot được tính là TRÚNG nhãn khi rule_ref của finding nằm '
            'trong danh sách rule_ref của nhãn và cùng hồ sơ. Hai loại nhãn không có '
            'rule_ref — khoang_trong (yêu cầu thật, bộ quy tắc chưa phủ) và khong_neo_duoc '
            '(yêu cầu không có chủ ngữ, ví dụ "Tính toán lại số liệu") — chỉ tính vào recall '
            '"so với mọi yêu cầu của người thẩm định", KHÔNG tính vào recall "so với bộ quy '
            'tắc hiện có".'),
        'caveat': (
            'rule_ref do máy gán bằng luật rồi người kiểm mẫu; phần "người" là do cùng '
            'tác nhân với phần gợi ý, chưa phải kiểm định độc lập.'),
    }
    json.dump({'meta': meta, 'labels': eval_items},
              open(args.eval_out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f'{len(labels)} nhãn -> {args.sheet_out}')
    print(f'   nguồn rule_ref: {dict(src_count)}')
    print(f'   ngoài phạm vi (loại khỏi eval): {n_out}')
    print(f'{len(eval_items)} nhãn -> {args.eval_out}')
    print(f'   có rule_ref: {n_rule} · khoảng trống: {n_gap} · không neo được: {n_neo}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
