#!/usr/bin/env python
"""Fill the audit sample: verdict on each machine suggestion + final rule_ref.

Keyed by `label_id`, not by row number. The first version keyed verdicts to the
row index and broke the moment the tier populations shifted (adding the "ngoài
phạm vi" tier re-drew the stratified sample). Keying by label lets earlier
judgments survive a re-draw.

Verdicts already recorded in a previous audited file are carried over
automatically; OVERRIDES corrects the ones whose classification later changed;
NEW_VERDICTS holds the rows judged in this pass.

Everything derivable is derived, not typed:
  - `checklist_ref` comes from the chosen rules in config/rules.yaml
  - `vong` comes from those rules' `round` field (1 = checklist completeness,
    2 = Guideline calculation)

`goi_y_dung`: Đ correct · Thừa right subject but over-listed · Thiếu missed an
applicable rule · S wrong. A row with no applicable rule keeps `rule_ref` EMPTY
(NT2) — it is a gap, a heading, or outside the Copilot's scope.

Usage
-----
    python scripts/fill_audit_sample.py data/eval_sheet_mau_kiem.csv \
        --carry data/eval_sheet_mau_kiem_daduyet.csv \
        --rules config/rules.yaml -o data/eval_sheet_mau_kiem_daduyet.csv
"""
from __future__ import annotations

import argparse
import collections
import csv
import sys

import yaml

# Rows whose classification changed after the 2026-09-03 scope clarification:
# image legibility is the reviewer's own visual judgement, not the Copilot's job.
OVERRIDES: dict[str, tuple] = {
    'PNX_Mykid 2.0 v2|R1-07-02': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: ảnh sở cứ mờ, không nhìn rõ — người thẩm định tự soi bằng mắt.'),
    'PNX_PL07_Sizing_Mybox_update_20251803|R1-05-03': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: ảnh tải cụm ELK bị mờ, thiếu ip.'),
    'PNX_PL07_Sizing_Mybox_update_20251803|R2-04-03': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: như lần 1, ảnh vẫn chưa đạt.'),
    'PNX_Data Security VTTv2|R2-03-03': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: đòi ảnh thể hiện thêm ip của hệ tham chiếu.'),
    'PNX_PBH 4.0v2|R1-01-05': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: yêu cầu ảnh chụp kèm ip, đường dẫn, chú thích.'),
}

# label_id -> (goi_y_dung, rule_ref, ngoai_pham_vi, ghi_chu)
NEW_VERDICTS: dict[str, tuple] = {
    'PNX_hethongVtag_v4|R1-04-02': ('Thiếu', 'CPU-01; PRC-01', '',
        'Đường link SPEC không mở được → lỗi SỞ CỨ, máy chỉ thấy nhóm Cint.'),
    'PNX_PBH 4.0v2|R1-09-06': ('Thừa', 'ALC-01', '',
        'Hỏi tài nguyên test đã được cấp chưa — thuộc hạn ngạch cấp phát.'),
    'PNX_Data Security VTTv2|R2-08-01': ('Đ', 'ARC-15; ARC-16', '', ''),
    'PNX_Sizing_APIGW-Meta_2024v4|R3-01-02': ('Thiếu', 'PRC-01; LAN-02', '',
        'Cốt lõi là đòi sở cứ cho con số băng thông — máy bỏ sót PRC-01.'),
    'PNX_hethongVtag_v4|R1-09-01': ('Thiếu', 'PRC-01; STO-04', '',
        'Đòi sở cứ cho dung lượng 100GB.'),
    'PNX_PHONE NUMBER MASKING2|R1-03-01': ('Thừa', 'STO-14; PRC-01', '',
        'Hỏi CĂN CỨ chọn SSD.'),
    'PNX_MNP|R1-07-02': ('Thiếu', 'EVD-04; PRC-01', '',
        'Là cấu hình máy chủ dùng để ĐO TẢI → EVD-04 (nêu đủ cấu hình hệ tham chiếu).'),
    'PNX_Data Security VTTv2|R2-03-04': ('Thừa', 'PRC-01; STO-04', '', ''),
    'PNX_PBH 4.0v2|R1-02-05': ('Thừa', 'PRC-01; STO-04', '', ''),
    'PNX_MNP|R1-04-01': ('Đ', 'ARC-15; ARC-16', '', ''),
    'PNX_PL07_Sizing_Mybox_update_20251803|R1-06-01': ('Đ', 'ARC-15; ARC-16', '', ''),
    'PNX_giam sat cuoc goi CSKH_bosung2022v3|R3-04-01': ('Thừa', 'PRC-05; PRC-01', '',
        'Đòi đính kèm bản sizing cũ ĐÃ KÝ làm sở cứ cho định cỡ bổ sung.'),
    'PNX_hethongVtag_v4|R1-17-01': ('S', '', '',
        'Là "công thức tính SAI" (lỗi Vòng 2), KHÔNG phải "thiếu trình bày công thức". '
        'Quy tắc tuỳ phân hệ đang nói tới — cần ngữ cảnh dòng trên.'),
    'PNX_Data Security VTTv2|R1-06-03': ('Đ', '', '',
        'KHOẢNG TRỐNG "phải trình bày công thức" — máy nhận đúng là không có quy tắc phủ.'),
    'PNX_hethongVtag_v4|R1-26-01': ('S', '', '', 'Như R1-17-01.'),
    'PNX_callbot inbound CSKH_bosung videobot XMKH_v1.2v2|R1-05-03': ('Thiếu',
        'PRC-01; EVD-05', '',
        'Chạm KHOẢNG TRỐNG "định cỡ GPU / tải AI": 8 card GPU cho 16CCU, '
        'Guideline lần 07 không có nội dung GPU.'),
    'PNX_hethongVtag_v4|R1-10-02': ('S', '', '', 'Như R1-17-01.'),
    'PNX_hethongVtag_v4|R1-21-01': ('S', '', '', 'Như R1-17-01.'),
    'PNX_MNP|R1-09-02': ('Đ', 'PRC-01', '',
        'Chạm KHOẢNG TRỐNG "sở cứ tốc độ tăng trưởng" — KPI-16 đang enabled:false.'),
    'PNX_He thong CMP_Phan hoi NX lan 2|R1-09-01': ('Đ', '', 'x', 'Tiêu đề mục.'),
    'PNX_Sizing_APIGW-Meta_2024v4|R1-04-05': ('Thiếu', 'EVD-10', '',
        'Số liệu trên và dưới khác nhau — đúng việc của EVD-10.'),
    'PNX_SSO 2.0_v3|R2-01-01': ('Đ', '', 'x',
        'Nhắc hoàn thiện nhận xét lần 1 — thủ tục, không phải yêu cầu với tài liệu.'),
    'PNX_PBH 4.0v2|R2-02-01': ('Đ', '', 'x', 'Tiêu đề mục.'),
    'PNX_hethongVtag_v4|R1-16-01': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: ảnh chưa rõ ràng, không thể hiện % chiếm dụng.'),
    'PNX_PL07_Sizing_Mybox_update_20251803|R2-01-01': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: ảnh chưa hiển thị rõ thông tin.'),
    'PNX_FMRA_Sizing_server_Backup_2024_Final_New|R1-03-02': ('Đ', '', 'x',
        '⚠️ RANH GIỚI: vừa là "bổ sung ảnh sở cứ" vừa là "ảnh phải hiện ip". '
        'Xếp ngoài phạm vi theo vế thứ hai — cần bạn xác nhận cách xử lý ca hỗn hợp.'),
    'PNX_PL07_Sizing_Mybox_update_20251803|R2-07-01': ('Đ', '', 'x',
        'NGOÀI PHẠM VI: ảnh và bảng số liệu không đồng nhất.'),
    # Mixed "sở cứ + ảnh mờ" rows: user decided 2026-09-03 to drop the whole row.
    'PNX_SSO 2.0_v3|R1-05-03': ('Đ', '', 'x',
        'CA HỖN HỢP (sở cứ + ảnh phải hiện ip) — người dùng quyết: LOẠI HẲN cả dòng.'),
    'PNX_Mykid 2.0 v2|R1-01-02': ('Đ', '', 'x',
        'CA HỖN HỢP (sở cứ + ảnh mờ) — người dùng quyết: LOẠI HẲN cả dòng.'),
    'PNX_PBH 4.0v2|R1-01-03': ('S', '', '',
        '"Tính toán lại số liệu" quá chung, không neo được vào quy tắc nào.'),
    'PNX_vTracking 2.0_v2|R1-03-06': ('Đ', 'PRC-01', '',
        'Sở cứ chỉ đo 1,5 tháng nhưng khai lưu 24 tháng — sở cứ không đỡ được kết luận.'),
    'PNX_callbot inbound CSKH_bosung videobot XMKH_v1.2v2|R1-01-02': ('Đ', 'PRC-01', '', ''),
    'PNX_callbot inbound CSKH_bosung videobot XMKH_v1.2v2|R2-01-03': ('Đ', 'PRC-01', '', ''),
    'PNX_CALLBASE|R1-01-02': ('Thừa', 'PRC-01', '', 'Bỏ EVD-10.'),
    'PNX_giam sat cuoc goi CSKH_bosung2022v4|R2-02-07': ('Đ', 'PRC-01', '', ''),
    'PNX_giam sat cuoc goi CSKH_bosung2022v3|R3-01-01': ('Đ', 'PRC-01', '', ''),
    'PNX_Sizing_APIGW-Meta_2024v4|R1-06-02': ('Đ', 'PRC-01', '', ''),
    'PNX_Data Security VTTv2|R1-01-03': ('S', '', '', 'Như "Tính toán lại số liệu".'),
    'PNX_callbot inbound CSKH_bosung videobot XMKH_v1.2v2|R2-01-02': ('Đ', 'PRC-01', '', ''),
    'PNX_hethongVtag_v4|R1-01-02': ('Đ', 'PRC-01', '',
        'Khớp rất đúng: đòi sở cứ BẰNG VĂN BẢN, email BGĐ — đúng nguyên văn PRC-01.'),
    'PNX_vTracking 2.0_v2|R1-05-03': ('Đ', 'PRC-01', '', ''),
    'PNX_PBH 4.0v2|R1-01-02': ('Đ', 'PRC-01', '', ''),
    'PNX_Mykid 2.0 v2|R1-04-02': ('Thiếu', 'PRC-01; EVD-11', '',
        'Là tải theo loại nghiệp vụ (10 phút/lần gửi vị trí) → EVD-11.'),
    'PNX_giam sat cuoc goi CSKH_bosung2022v2|R2-02-04': ('Thừa', 'PRC-01; CPU-01', '',
        'Không liên quan bảng tổng hợp đề xuất — máy khớp nhầm vì dấu ">=".'),
    'PNX_hethongVtag_v4|R2-03-02': ('Thừa', 'STO-21; STO-04; KPI-04', '',
        'Dung lượng Kafka theo mức dùng thực tế và áp KPI ổ cứng 80%.'),
    'PNX_Data Security VTTv2|R1-03-03': ('Thừa', 'PRC-01; CPU-01; RAM-02', '', ''),
    'PNX_Data Security VTTv2|R1-04-04': ('Thừa', 'KPI-02; KPI-14', '',
        'Chất vấn con số dự phòng theo KPI 75% — không phải dự phòng N+M.'),
    'PNX_SSO 2.0_v3|R1-05-05': ('S', 'EVD-16; EVD-22', '',
        'Đòi LẬP BẢNG giá trị sau khi tính → bảng tổng hợp đề xuất. '
        'Máy gán nhóm ảo hóa/RAM/dung lượng là sai việc.'),
    'PNX_CAMPAIGN_MANAGEMENT_v3|R2-02-02': ('Thừa', 'CPU-01; PRC-01', '', ''),
    'PNX_C360_Public|R1-03-03': ('Thiếu', 'KPI-12; KPI-13; EVD-05', '',
        'Lỗi quy đổi tỷ lệ: tính cho 1000 CCU rồi nhân 300 → sai hệ số so sánh Ksosánh.'),
    'PNX_PL07_Sizing_Mybox_update_20251803|R1-11-07': ('Thừa', 'PRC-01; STO-04', '', ''),
    'PNX_Sizing_APIGW-Meta_2024v4|R3-02-03': ('S', 'ARC-08; EVD-16', '',
        'Chất vấn phép chia tổng tài nguyên cho 4 máy → ARC-08. Máy gán CPU/RAM/SSD là sai việc.'),
    'PNX_hethongVtag|R1-08-02': ('S', '', 'x',
        '⚠️ Tham chiếu chéo ("Tương tự như nhận xét máy chủ Redis") mà bộ loại trừ '
        'không bắt được — đã sửa EXCLUDE_RE sau khi phát hiện ca này.'),
    'PNX_MySign_v2|R1-01-03': ('Thừa', 'EVD-10', '',
        'Ca thật của KHOẢNG TRỐNG "làm tròn": làm tròn quá nhiều làm cint/ram sai lệch.'),
    'PNX_CAMPAIGN_MANAGEMENT_v3|R2-03-02': ('Thừa', 'CPU-01; PRC-01', '', ''),
    'PNX_vTracking 2.0_v2|R1-03-02': ('Thừa', 'CPU-05; RAM-02', '',
        'Đòi tính theo giá trị tuyệt đối thay vì % đã làm tròn — ca thật của '
        'KHOẢNG TRỐNG "làm tròn / độ chính xác số trung gian".'),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('sample_csv')
    ap.add_argument('--carry', help='phiếu đã chấm trước đó, để tái dùng phán quyết')
    ap.add_argument('--rules', default='config/rules.yaml')
    ap.add_argument('-o', '--out', required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    rules = {r['id']: r for r in
             yaml.safe_load(open(args.rules, encoding='utf-8'))['rules']}

    verdicts: dict[str, tuple] = {}
    n_carry = 0
    if args.carry:
        try:
            for r in csv.DictReader(open(args.carry, encoding='utf-8-sig')):
                if r.get('goi_y_dung'):
                    verdicts[r['label_id']] = (r['goi_y_dung'], r['rule_ref'],
                                               r['ngoai_pham_vi'], r['ghi_chu'])
                    n_carry += 1
        except FileNotFoundError:
            pass
    verdicts.update(NEW_VERDICTS)
    verdicts.update(OVERRIDES)

    rows = list(csv.DictReader(open(args.sample_csv, encoding='utf-8-sig')))
    ids = {r['label_id'] for r in rows}

    # A verdict keyed to a label that is not in the sample is silently useless —
    # it happened once (label_ids typed from memory instead of looked up, so five
    # stale verdicts survived a re-classification unnoticed). Fail loudly instead.
    # Since the sample is frozen (data/audit_sample_ids.json) an id can only be
    # missing here because the parser re-classified that row as a heading. Still
    # printed loudly — a typo would look exactly the same — but no longer fatal.
    for name, table in (('OVERRIDES', OVERRIDES), ('NEW_VERDICTS', NEW_VERDICTS)):
        stray = sorted(set(table) - ids)
        if stray:
            print(f'⚠️  {len(stray)} mục trong {name} không còn trong phiếu mẫu '
                  f'(nhãn đã thành tiêu đề?) — KIỂM LẠI nếu không mong đợi:')
            for s in stray:
                print('   ' + s)

    missing = [r['label_id'] for r in rows if r['label_id'] not in verdicts]
    if missing:
        print(f'LỖI: {len(missing)} dòng chưa có phán quyết:')
        for m in missing[:10]:
            print('   ' + m)
        return 1

    unknown = sorted({x.strip() for _, rr, _, _ in verdicts.values()
                      for x in rr.split(';') if x.strip()} - set(rules))
    if unknown:
        print(f'LỖI: mã quy tắc không có thật: {", ".join(unknown)}')
        return 1

    tally: collections.Counter = collections.Counter()
    for row in rows:
        verdict, rule_ref, ngoai, note = verdicts[row['label_id']]
        ids = [x.strip() for x in rule_ref.split(';') if x.strip()]
        row['goi_y_dung'] = verdict
        row['rule_ref'] = '; '.join(ids)
        row['ngoai_pham_vi'] = ngoai
        row['ghi_chu'] = note
        row['da_kiem'] = 'x'
        cl: list[str] = []
        for rid in ids:
            for c in (rules[rid].get('checklist_ref') or []):
                if c not in cl:
                    cl.append(c)
        row['checklist_ref'] = '; '.join(cl)
        rounds = sorted({rules[rid].get('round') for rid in ids}) if ids else []
        row['vong'] = '/'.join(str(x) for x in rounds)
        tally[verdict] += 1

    with open(args.out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f'{len(rows)} dòng đã điền -> {args.out}')
    print(f'   tái dùng {n_carry} phán quyết cũ · {len(NEW_VERDICTS)} chấm mới · '
          f'{len(OVERRIDES)} sửa lại do đổi phạm vi\n')
    print('Phán quyết trên gợi ý của máy:')
    for k in ('Đ', 'Thừa', 'Thiếu', 'S'):
        n = tally[k]
        print(f'   {k:<6} {n:>3}  ({n/len(rows)*100:.1f}%)')
    ok = tally['Đ'] + tally['Thừa']
    print(f'\nĐúng chủ đề (Đ + Thừa): {ok}/{len(rows)} = {ok/len(rows)*100:.1f}%')
    print(f'Có mã quy tắc cuối cùng: {sum(1 for r in rows if r["rule_ref"])}/{len(rows)}')
    print(f'Ngoài phạm vi:           {sum(1 for r in rows if r["ngoai_pham_vi"])}/{len(rows)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
