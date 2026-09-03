#!/usr/bin/env python
"""Suggest a `rule_ref` for each PNX label — deterministic, auditable, no LLM.

Standing
--------
Assigning `rule_ref` was originally reserved for a person. The user has since
decided the volume (527 labels) makes that impractical and asked for machine
suggestions plus a random-sample human audit. This script serves that, but keeps
the provenance visible so the audit stays meaningful:

  - suggestions go to `rule_ref_goi_y`, NOT to the authoritative `rule_ref`
  - every suggestion carries `do_tin_cay` and `can_cu_goi_y` (which pattern fired)
  - a label with no grounded match gets NO rule (NT2) — it is left blank and
    counted, never filled with a plausible guess

Why patterns and not an LLM: NT1 (code decides, not the model), the result is
reproducible and reviewable line by line, and 0.10 has not verified any LLM
endpoint yet. The judgment lives in PATTERNS below — ~40 rows a reviewer can read
in a few minutes, instead of 527 opaque decisions.

Ordering: every matching pattern contributes. Confidence is derived from how
specific the match was, not asserted per row.

Usage
-----
    python scripts/suggest_rule_refs.py data/pnx_labels_dedup.json \
        --rules config/rules.yaml -o data/pnx_labels_suggested.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys

import yaml

# --------------------------------------------------------------------------
# BẢNG ÁNH XẠ — phần phán đoán nghiệp vụ. Đọc và sửa được, đây là chỗ để soát.
#
#   muc     : độ đặc hiệu. 2 = chủ đề rõ ràng · 1 = chung chung
#   rules   : mã quy tắc trong config/rules.yaml (được kiểm tồn tại khi chạy)
#   rules=[]: KHOẢNG TRỐNG — người thẩm định bắt nhưng không quy tắc nào phủ
# --------------------------------------------------------------------------
PATTERNS: list[dict] = [
    # ---- hạ tầng mạng / firewall / cân bằng tải ----
    dict(ten='Thông lượng FW / LB', muc=2, rules=['FWL-04', 'FWL-02', 'LBA-01', 'LBA-02'],
         re=r'thông lượng.{0,25}(fw|lb|firewall|cân bằng tải)|(\bfw\b|\blb\b|firewall|cân bằng tải).{0,25}thông lượng|định cỡ (firewall|fw|lb)'),
    dict(ten='Zone / quy hoạch FW-LB', muc=2, rules=['FWL-01', 'FWL-04'],
         re=r'\bzone\b|quy hoạch (fw|lb|firewall)'),
    dict(ten='LAN switch / port', muc=2, rules=['LAN-01', 'LAN-02', 'LAN-03'],
         re=r'lan switch|số port|bandwidth port'),
    dict(ten='SAN switch', muc=2, rules=['SAN-01', 'SAN-02'], re=r'san switch'),
    dict(ten='Rack / RU', muc=2, rules=['RCK-01', 'RCK-02', 'RCK-03'],
         re=r'\brack\b|\bru\b(?! )'),

    # ---- dự phòng / kiến trúc ----
    dict(ten='Dự phòng N+1 / N+M', muc=2, rules=['ARC-03', 'ARC-09', 'ARC-02'],
         re=r'n\s*\+\s*1|n\s*\+\s*m|dự phòng|\bha\b|high avail'),
    dict(ten='DC-DR / mức độ quan trọng', muc=2, rules=['ARC-26', 'ARC-12', 'ARC-13'],
         re=r'đbqt|đặc biệt quan trọng|dc-?dr|\bdr\b|mức độ quan trọng'),
    dict(ten='Kết nối tới hệ thống khác', muc=2, rules=['ARC-15', 'ARC-16'],
         re=r'kết nối|giao thức|\bport\b|vùng mạng'),
    dict(ten='Ảo hóa / overcommit / vCPU', muc=2, rules=['ARC-05', 'CPU-03', 'CPU-04', 'ALC-02'],
         re=r'ảo hóa|overcommit|\bvcpu\b|\bvm\b'),
    dict(ten='Số node / cụm', muc=2, rules=['ARC-08', 'ARC-09'],
         re=r'số (lượng )?(server|máy chủ|node|instance)|số node|trong cụm'),

    # ---- CPU / RAM ----
    dict(ten='Cint / SPEC CPU', muc=2, rules=['CPU-01', 'CPU-02', 'CPU-10'],
         re=r'\bcint\b|spec ?cpu|cpu ?2017|cpu2017|\bcfp\b|spec\.org'),
    dict(ten='CPU sử dụng', muc=2, rules=['CPU-05', 'CPU-06', 'CPU-09'],
         re=r'\bcpu\b'),
    dict(ten='RAM', muc=2, rules=['RAM-01', 'RAM-02'], re=r'\bram\b|bộ nhớ'),
    dict(ten='Ngưỡng KPI', muc=2, rules=['KPI-02', 'KPI-03', 'KPI-04', 'KPI-14'],
         re=r'\bkpi\b|75\s*%|90\s*%|80\s*%'),
    dict(ten='Khoảng đo tải / 95th', muc=2, rules=['KPI-01', 'KPI-10'],
         re=r'95th|đo tải|khoảng thời gian.{0,20}(tuần|tháng)|biến động tải|tải thực tế'),

    # ---- lưu trữ ----
    dict(ten='SSD / loại ổ', muc=2, rules=['STO-14', 'STO-15', 'STO-03', 'KPI-07'],
         re=r'\bssd\b|\bhdd\b|nl-?sas|loại ổ'),
    dict(ten='IOPS / latency', muc=2, rules=['STO-01', 'STO-07', 'STO-08', 'KPI-05'],
         re=r'\biops\b|latency'),
    dict(ten='RAID / dung lượng thô', muc=2, rules=['STO-04', 'STO-05', 'STO-09', 'EVD-01'],
         re=r'\braid\b|dung lượng thô|khả dụng'),
    # (?!...) keeps bandwidth out: "35 Mb/s" is throughput, not stored volume
    dict(ten='Dung lượng lưu trữ', muc=2, rules=['STO-04', 'KPI-06', 'EVD-01'],
         re=r'dung lượng|lưu trữ|\d+\s*(tb|gb|pb|mb)\b(?!\s*(/|p)s)|chỉ lưu|thời gian lưu'),
    dict(ten='Phân vùng /data /log /backup', muc=2, rules=['STO-18'],
         re=r'phân vùng|/data|/log|/backup'),
    dict(ten='Sao lưu / backup', muc=2, rules=['BAK-09', 'BAK-02', 'BAK-01'],
         re=r'\bbackup\b|sao lưu|\btape\b'),

    # ---- công nghệ cụ thể ----
    dict(ten='Kafka', muc=2, rules=['ARC-23', 'ARC-24', 'ARC-25', 'CPU-11', 'STO-21', 'STO-22'],
         re=r'kafka|broker|zookeeper'),
    dict(ten='Redis', muc=2, rules=['ARC-19', 'ARC-20', 'ARC-21', 'ARC-22', 'STO-19', 'STO-20', 'RAM-03'],
         re=r'redis|sentinel'),
    dict(ten='MariaDB', muc=2, rules=['ARC-17', 'ARC-18', 'BAK-10', 'BAK-11'],
         re=r'mariadb|3 master|active-active'),

    # ---- cấu trúc tài liệu (Vòng 1) ----
    dict(ten='Mô hình logic', muc=2, rules=['EVD-13', 'EVD-19'], re=r'mô hình logic'),
    dict(ten='Mô hình vật lý', muc=2, rules=['EVD-14', 'EVD-20'], re=r'mô hình vật lý'),
    dict(ten='Luồng nghiệp vụ', muc=2, rules=['EVD-15'], re=r'luồng nghiệp vụ'),
    dict(ten='Bảng tổng hợp đề xuất', muc=2, rules=['EVD-16', 'EVD-22'],
         re=r'bảng tổng hợp|tổng hợp đề xuất|>=|≥'),
    dict(ten='Mô tả tổng quan hệ thống', muc=2, rules=['EVD-12'],
         re=r'mô tả (tổng quan|hệ thống)|tổng quan hệ thống'),
    dict(ten='Công nghệ sử dụng', muc=2, rules=['EVD-18'], re=r'công nghệ sử dụng'),
    dict(ten='Đầu mối / đơn vị', muc=2, rules=['PRC-09'],
         re=r'đầu mối|đơn vị (phát triển|định cỡ)'),
    dict(ten='Thời gian cam kết / đổ tải', muc=2, rules=['PRC-10'],
         re=r'thời gian cam kết|đổ tải|cam kết hoàn thành'),
    dict(ten='Nguồn tài nguyên cấp phát / QHĐC', muc=2, rules=['PRC-07'],
         re=r'nguồn (tài nguyên|cấp phát)|hạ tầng (idc|cloud)|qh[đd]c|quy hoạch định cỡ',
         ghi_chu='Với "có trong QHĐC (quy hoạch định cỡ) chưa": Copilot chỉ kiểm được '
                 'tài liệu CÓ NÊU nguồn tài nguyên hay không. Đối chiếu thật với bản '
                 'QHĐC là việc của người thẩm định — Copilot không có tài liệu đó.'),

    # ---- phương pháp định cỡ / hệ tham chiếu ----
    dict(ten='Cơ sở định cỡ / hệ tham chiếu', muc=2, rules=['MTH-01', 'MTH-03', 'MTH-04', 'EVD-04'],
         re=r'cơ sở định cỡ|hệ (thống )?tham chiếu|tương (tự|đồng)|nguyên tắc định cỡ|'
            r'dùng để sizing|căn cứ định cỡ'),
    dict(ten='Băng thông / tốc độ truyền', muc=2, rules=['LAN-02', 'LAN-03', 'FWL-02', 'LBA-02'],
         re=r'\d+\s*(k|m|g)b(ps|/s)|băng thông|tốc độ (upload|download|truyền)|gbps|mbps'),

    # ---- tải đầu vào ----
    dict(ten='CCU / TPS / request', muc=2, rules=['EVD-05', 'EVD-11', 'EVD-21'],
         re=r'\bccu\b|\btps\b|\brps\b|request/|bản ghi|giao dịch|đồng thời'),

    # ---- thủ tục / sở cứ ----
    dict(ten='Kiểm thử hiệu năng / biên bản', muc=2, rules=['PRC-02', 'TST-01', 'TST-03'],
         re=r'kiểm thử|biên bản|\bpoc\b|thử nghiệm'),
    dict(ten='Hồ sơ ký duyệt / checklist đính kèm', muc=2, rules=['PRC-05', 'PRC-01'],
         re=r'checklist|ký (duyệt|sizing)|đính kèm|phê duyệt|tờ trình'),
    dict(ten='Cấp phát 06 tháng / hạn ngạch', muc=2, rules=['ALC-01'],
         re=r'06 tháng|6 tháng|1 năm|02 năm|2 năm|bao lâu'),

    # ---- KHOẢNG TRỐNG — không quy tắc nào phủ ----
    dict(ten='Mục đích sizing', muc=2, rules=['PRC-11'],
         re=r'mục đích sizing|mục đích của sizing|bổ sung mục đích|hàng mục đích|'
            r'định cỡ mới|cấp mới để làm gì',
         ghi_chu='PRC-11 được BỔ SUNG 2026-09-03 (người dùng duyệt) đúng để phủ '
                 'chủ đề này — trước đó rules.yaml không có quy tắc nào khớp.'),
    dict(ten='KHOẢNG TRỐNG · Sở cứ tốc độ tăng trưởng', muc=2, rules=[],
         re=r'tăng trưởng',
         ghi_chu='KPI-16 (tăng trưởng 01 năm) đang enabled:false vì mâu thuẫn với '
                 'ALC-01 (06 tháng). Khoảng trống đã biết.'),
    dict(ten='KHOẢNG TRỐNG · Làm tròn / độ chính xác', muc=2, rules=[],
         re=r'làm tròn|độ chính xác|chia 1024|chia 1000',
         ghi_chu='globals.lam_tron mới là quy ước làm tròn kết quả cuối, '
                 'chưa thành quy tắc kiểm. Khoảng trống đã biết.'),
    dict(ten='KHOẢNG TRỐNG · Phải trình bày công thức', muc=2, rules=[],
         re=r'công thức|ghi rõ cách tính|giải thích.{0,15}tính',
         ghi_chu='PNX đòi hiện phép tính, không chỉ kết quả. EVD-09 chỉ yêu cầu '
                 'truy được nguồn số. Khoảng trống đã biết.'),
    dict(ten='KHOẢNG TRỐNG · Định cỡ GPU / tải AI', muc=2, rules=[],
         re=r'\bgpu\b|nvidia|\bcuda\b',
         ghi_chu='Guideline lần 07 không có nội dung GPU. Khoảng trống đã biết.'),
    # Không còn xếp là "khoảng trống": xem NGOAI_PHAM_VI_RE ở dưới.

    # ---- chung chung: chỉ dùng khi không có chủ đề nào cụ thể ----
    # EVD-03 ("thông số chọn phải ảnh hưởng năng lực") used to ride along here. The
    # 88-row audit trimmed it off nearly every time — a request for evidence is
    # PRC-01 alone. Keeping it would hand the Copilot free hits on a rule the
    # reviewer never invoked.
    dict(ten='Sở cứ cho số liệu (chung)', muc=1, rules=['PRC-01'],
         re=r'sở cứ|sở cú|minh chứng|chứng minh|dẫn chứng'),
    dict(ten='Nhất quán / tính lại số liệu (chung)', muc=1, rules=['EVD-10'],
         re=r'tính (toán )?lại|không (đồng nhất|nhất quán)|đang bị sai|sai\b|làm rõ|'
            r'xem lại|nhưng ở đây|mâu thuẫn|cập nhật lại|không hiểu|tại sao'),
]


# NGOÀI PHẠM VI COPILOT — không phải khoảng trống quy tắc.
#
# Người dùng xác nhận 2026-09-03: nhận xét về CHẤT LƯỢNG ảnh sở cứ (mờ, thiếu ip,
# không khớp số liệu, cần khoanh tròn) là do người thẩm định TỰ đánh giá bằng mắt
# rồi yêu cầu đơn vị cung cấp lại — không phải việc AI đánh giá.
#
# Hệ quả quan trọng cho eval: những nhãn này phải bị LOẠI KHỎI MẪU SỐ RECALL. Để
# lại thì Copilot bị trừ điểm vì không tìm ra thứ nó không được giao tìm — sai lệch
# đúng theo hướng làm chỉ số vô nghĩa.
#
# Ranh giới cố ý hẹp: chỉ CHẤT LƯỢNG / TÍNH ĐỌC ĐƯỢC của ảnh đã có, hoặc yêu cầu
# chú thích thêm. Còn "thiếu hẳn sở cứ cho một con số" vẫn là PRC-01 và vẫn trong
# phạm vi, dù sở cứ đó tình cờ ở dạng ảnh.
NGOAI_PHAM_VI: list[dict] = [
    dict(ten='NGOÀI PHẠM VI · Chất lượng / tính đọc được của ảnh sở cứ',
         re=r'ảnh\s*(bị\s*)?mờ|không nhìn rõ|nhìn không rõ|chưa rõ ràng|'
            r'khoanh tròn|(ảnh|hình).{0,40}(không đồng nhất|chưa hiển thị rõ|bị mờ)|'
            r'(ảnh|hình).{0,40}(kèm theo ip|thông tin ip|đường dẫn|chú thích)|'
            r'cập nhật lại .{0,10}(ảnh|anh)\b',
         ghi_chu='Người thẩm định tự soi bằng mắt rồi yêu cầu cung cấp lại ảnh. '
                 'KHÔNG phải việc của Copilot → loại khỏi mẫu số recall.'),
    dict(ten='NGOÀI PHẠM VI · Hướng dẫn thủ tục trả lời PNX',
         re=r'nội dung (phản hồi|chỉnh sửa)|không comment trong file|trình ký|'
            r'^\s*phản hồi ghi rõ|hoàn thiện nhận xét lần|^\s*chính tả\b|'
            r'bổ sung số trang',
         ghi_chu='Hướng dẫn cách phản hồi PNX, không phải yêu cầu với tài liệu sizing.'),
]


# Cross-references, not independent requirements. "Tương tự nhận xét module
# Worker" means "same comment as for module Worker" — matching it on the word
# "tương tự" wrongly pulled in the reference-system rules (MTH-*). These carry no
# rule of their own; the rule lives on the comment they point at.
EXCLUDE_RE = re.compile(
    r'^\s*[-•]?\s*(tương tự|như)( như)? (nhận xét|mục|trên|các mục|phần)|'
    r'tương tự (như )?nhận xét|tương tự (như )?(máy chủ|module|phân hệ|cụm)|'
    r'^\s*[-•]?\s*(tương tự|nt) (module|phân hệ|cụm)|'
    r'^\s*nội dung (phản hồi|chỉnh sửa)', re.IGNORECASE)


def compile_patterns() -> list[dict]:
    for p in PATTERNS + NGOAI_PHAM_VI:
        p['rx'] = re.compile(p['re'], re.IGNORECASE)
    return PATTERNS


def suggest(text: str, pats: list[dict]) -> dict:
    if EXCLUDE_RE.search(text):
        return dict(rules=[], do_tin_cay='tham chiếu chéo', can_cu='', gaps=[],
                    ngoai_pham_vi='x',
                    ghi_chu='Trỏ tới một nhận xét khác, không phải yêu cầu độc lập. '
                            'Quy tắc nằm ở nhận xét được trỏ tới.')
    # Checked before the rule patterns: an out-of-scope comment must not be given a
    # rule at all, and must be excluded from the recall denominator.
    for p in NGOAI_PHAM_VI:
        if p['rx'].search(text):
            return dict(rules=[], do_tin_cay='ngoài phạm vi', can_cu=p['ten'],
                        gaps=[], ngoai_pham_vi='x', ghi_chu=p['ghi_chu'])
    hits = [p for p in pats if p['rx'].search(text)]
    specific = [p for p in hits if p['muc'] == 2]
    generic = [p for p in hits if p['muc'] == 1]

    used = specific or generic
    if not used:
        return dict(rules=[], do_tin_cay='không xác định', can_cu='', gaps=[],
                    ngoai_pham_vi='', ghi_chu='')

    gaps = [p['ten'] for p in used if not p['rules']]
    rules: list[str] = []
    for p in used:
        for r in p['rules']:
            if r not in rules:
                rules.append(r)

    # A generic "bổ sung sở cứ" attached to a specific subject is worth keeping:
    # the reviewer is asking for evidence ABOUT that subject.
    if specific and generic:
        for p in generic:
            for r in p['rules']:
                if r not in rules:
                    rules.append(r)

    # Confidence must reflect whether a SPECIFIC pattern actually produced rules.
    # A gap pattern matches specifically but yields none; if the only rules came
    # from the catch-all, calling that "cao" would hide the fact that no rule
    # covers what the reviewer asked for.
    specific_with_rules = [p for p in specific if p['rules']]
    if not rules:
        conf = 'khoảng trống'
    elif not specific_with_rules:
        conf = 'khoảng trống'  # gap matched; generic rules kept only as context
    elif len(specific_with_rules) == 1:
        conf = 'cao'
    else:
        conf = 'vừa'          # several subjects matched — needs a human eye
    if not specific:
        conf = 'thấp'         # only the catch-all fired

    notes = [p['ghi_chu'] for p in used if p.get('ghi_chu')]
    return dict(rules=rules, do_tin_cay=conf,
                can_cu=' + '.join(p['ten'] for p in used),
                gaps=gaps, ngoai_pham_vi='', ghi_chu=' | '.join(notes))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('labels_json')
    ap.add_argument('--rules', default='config/rules.yaml')
    ap.add_argument('-o', '--out', required=True)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')

    known = {r['id'] for r in yaml.safe_load(open(args.rules, encoding='utf-8'))['rules']}
    bad = sorted({r for p in PATTERNS for r in p['rules'] if r not in known})
    if bad:
        print(f'LỖI: mã quy tắc không có thật trong rules.yaml: {", ".join(bad)}')
        return 1

    pats = compile_patterns()
    labels = json.load(open(args.labels_json, encoding='utf-8'))['labels']

    conf_count: collections.Counter = collections.Counter()
    gap_count: collections.Counter = collections.Counter()
    for l in labels:
        text = (l.get('context_lead', '') + ' ' + l['text']).strip()
        s = suggest(text, pats)
        l['rule_ref_goi_y'] = s['rules']
        l['do_tin_cay'] = s['do_tin_cay']
        l['can_cu_goi_y'] = s['can_cu']
        l['ghi_chu_goi_y'] = s['ghi_chu']
        l['ngoai_pham_vi_goi_y'] = s.get('ngoai_pham_vi', '')
        conf_count[s['do_tin_cay']] += 1
        for g in s['gaps']:
            gap_count[g] += 1

    json.dump({'labels': labels}, open(args.out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)

    print(f'{len(labels)} nhãn -> {args.out}\n')
    print('Độ tin cậy:')
    for k in ('cao', 'vừa', 'thấp', 'khoảng trống', 'tham chiếu chéo', 'không xác định'):
        n = conf_count[k]
        if n:
            print(f'   {k:<16} {n:>4}  ({n/len(labels)*100:.1f}%)')
    have = sum(1 for l in labels if l['rule_ref_goi_y'])
    print(f'\nCó ít nhất 1 mã quy tắc: {have}/{len(labels)} ({have/len(labels)*100:.1f}%)')
    if gap_count:
        print('\nKhoảng trống (người thẩm định bắt, không quy tắc nào phủ):')
        for g, n in gap_count.most_common():
            print(f'   {n:>4}  {g}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
