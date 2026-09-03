#!/usr/bin/env python
"""Trích các vấn đề người thẩm định đã bắt, từ kho `approved-sizing/`.

Bối cảnh
--------
`approved-sizing/` chứa 50 file `APPRAISAL_KNOWLEDGE.md` — bản tóm tắt do một AI
khác (Cline) trích từ hồ sơ sizing đã ký, trong đó phần giá trị nhất là **Phiếu
Nhận Xét (PNX)** của Phòng Hệ thống: những chỗ người thẩm định thật sự bắt lỗi.

Bộ 150 quy tắc ở `config/rules.yaml` hiện suy ra hoàn toàn từ **văn bản** (Guideline,
checklist, code web app), chưa lần nào đối chiếu với **hành vi thẩm định thật**.
Script này rút dữ liệu để làm việc đối chiếu đó.

⚠️ GIỚI HẠN CỦA NGUỒN — đọc trước khi tin vào kết quả
-----------------------------------------------------
Đây là **tóm tắt do AI viết lại**, KHÔNG phải nguyên văn PNX. Bản gốc (.docx/.pdf)
không còn (xác nhận 2026-08-26). Trong file có dấu vết lỗi trích xuất rõ ràng:
`sởffff`, `sởFFFF`, `THÔNG SỐ KỨ THUẬT`, `NHẬN XẾT`.

→ Dùng được để **hiểu xu hướng** (người thẩm định hay bắt gì).
→ KHÔNG dùng được làm **nhãn vàng chấm điểm** — vi phạm NT2, và recall tính ra sẽ ảo.

Cách dùng
---------
    uv run python scripts/extract_appraisal_issues.py
    uv run python scripts/extract_appraisal_issues.py --file "cap moi CMP 40562"
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'approved-sizing'
OUT = ROOT / 'docs/rules/.tmp-appraisal'

# Có 1 file lồng hai cấp (cap moi hethong Vtag/hethong Vtag/) — phải dùng '**',
# dùng '*/' sẽ sót đúng file đó.
GLOB = '**/APPRAISAL_KNOWLEDGE.md'

# --- chuẩn hóa tiêu đề -------------------------------------------------------
# Tiêu đề trong 50 file KHÔNG thống nhất: khác emoji, khác dấu, và có lỗi chính tả
# của chính bản trích ("KỨ THUẬT", "NHẬN XẾT"). Chuẩn hóa trước khi phân loại.
TYPO = {
    'KỨ THUẬT': 'KỸ THUẬT',
    'NHẬN XẾT': 'NHẬN XÉT',
}

# Mục chứa VẤN ĐỀ người thẩm định bắt — đây là thứ cần lấy.
ISSUE_HEADS = (
    'LƯU Ý THẨM ĐỊNH', 'PHIẾU NHẬN XÉT', 'TRI THỨC RÚT RA', 'BÀI HỌC',
    'KEY ISSUES', 'CHECK LIST ĐÁNH GIÁ', 'CÁC BÀI HỌC', 'KINH NGHIỆM XỬ LÝ',
    'NHẬN XÉT CHUNG', 'KEY INSIGHTS', 'VẤN ĐỀ',
)
# Mục mô tả hệ thống / kết quả — giữ để tra ngược, không phải vấn đề.
SPEC_HEADS = (
    'THÔNG SỐ', 'QUY MÔ', 'CẤU HÌNH', 'STORAGE', 'NETWORK', 'REQUIREMENTS',
    'SYSTEM TYPE', 'THÔNG TIN', 'TRẠNG THÁI', 'PHÂN LOẠI', 'BEST PRACTICE',
    'KẾT LUẬN', 'TÀI LIỆU THAM KHẢO', 'GHI CHÚ',
)


def norm_head(line: str) -> str:
    t = re.sub(r'^#+\s*', '', line)
    t = re.sub(r'[^\w\sÀ-ỹ]', ' ', t)          # bỏ emoji, dấu câu, **
    t = re.sub(r'\s+', ' ', t).strip().upper()
    for bad, good in TYPO.items():
        t = t.replace(bad, good)
    return t


def kind_of(head: str) -> str:
    for k in ISSUE_HEADS:
        if k in head:
            return 'issue'
    for k in SPEC_HEADS:
        if k in head:
            return 'spec'
    return 'other'


# --- metadata ----------------------------------------------------------------
META_PATTERNS = {
    'du_an':        r'\*\*Dự án:?\*\*\s*(.+)',
    'ma_pyc':       r'\*\*Mã PYC:?\*\*\s*(.+)',
    'nguoi_tham_dinh': r'\*\*(?:Người thẩm định|Thẩm định viên):?\*\*\s*(.+)',
    'dau_moi':      r'\*\*Đầu mối(?:[^:*]*)?:?\*\*\s*(.+)',
    'ngay':         r'\*\*Ngày thẩm định:?\*\*\s*(.+)',
    'muc_dich':     r'\*\*Mục đích sizing:?\*\*\s*(.+)',
}


def clean(v: str) -> str:
    return re.sub(r'\s+', ' ', v.replace('*', '').strip(' -')).strip()


def parse_meta(text: str) -> dict:
    meta: dict[str, str | None] = {}
    for key, pat in META_PATTERNS.items():
        m = re.search(pat, text)
        meta[key] = clean(m.group(1)) if m else None

    up = text.upper()
    if 'TRƯỜNG HỢP A' in up:
        meta['loai_ho_so'] = 'A'          # có PNX, có phản biện
    elif 'TRƯỜNG HỢP B' in up:
        meta['loai_ho_so'] = 'B'          # duyệt thẳng, mẫu chuẩn
    else:
        meta['loai_ho_so'] = None         # KHÔNG đoán (NT4)

    # số vòng phản hồi — lấy con số lớn nhất trong các cách viết đã gặp
    rounds = [int(n) for n in re.findall(r'(\d+)\s*VÒNG', up)]
    rounds += [int(n) for n in re.findall(r'VÒNG\s*(\d+)', up)]
    rounds += [int(n) for n in re.findall(r'PHIẾU NHẬN XÉT LẦN\s*(\d+)', up)]
    meta['so_vong'] = max(rounds) if rounds else None
    return meta


# --- vấn đề ------------------------------------------------------------------
# Vấn đề xuất hiện ở hai dạng (đã đếm: 440 dạng tiêu đề, 427 dạng danh sách):
ISSUE_AS_HEAD = re.compile(r'^#{3,4}\s+(?:[^\w]*)?(\d+)[\.\)]\s*(.+)$')
ISSUE_AS_ITEM = re.compile(r'^(\d+)\.\s+\*\*(.+?)\*\*:?\s*(.*)$')


def strip_md(s: str) -> str:
    s = re.sub(r'[*`#]', '', s)
    s = re.sub(r'[^\w\sÀ-ỹ()/:,.\-–%+]', '', s)
    return re.sub(r'\s+', ' ', s).strip(' :-')


def parse_issues(text: str) -> tuple[list[dict], list[str]]:
    """Trả về (danh sách vấn đề, danh sách mục chứa vấn đề)."""
    issues: list[dict] = []
    sections: list[str] = []
    cur_h2 = cur_h3 = ''
    cur_kind = 'other'
    body: list[str] = []
    pending: dict | None = None

    def flush() -> None:
        nonlocal pending, body
        if pending is not None:
            ctx = ' '.join(strip_md(b) for b in body if b.strip())
            pending['ngu_canh'] = ctx[:400]
            issues.append(pending)
        pending, body = None, []

    for line in text.splitlines():
        if re.match(r'^##\s', line):
            flush()
            cur_h2 = norm_head(line)
            cur_h3 = ''
            cur_kind = kind_of(cur_h2)
            if cur_kind == 'issue':
                sections.append(cur_h2)
            continue

        if cur_kind != 'issue':
            continue

        if re.match(r'^#{3,4}\s', line):
            flush()
            m = ISSUE_AS_HEAD.match(line)
            head = norm_head(line)
            if m:
                pending = {'muc': cur_h2, 'muc_con': cur_h3,
                           'tieu_de': strip_md(m.group(2))}
            else:
                # tiêu đề không đánh số -> coi là mục con, không phải một vấn đề
                cur_h3 = head
            continue

        m = ISSUE_AS_ITEM.match(line)
        if m:
            flush()
            pending = {'muc': cur_h2, 'muc_con': cur_h3,
                       'tieu_de': strip_md(m.group(2))}
            body = [m.group(3)]
            continue

        if pending is not None:
            body.append(line)
    flush()

    # bỏ mục rỗng hoặc quá ngắn để không tạo rác
    issues = [i for i in issues if len(i['tieu_de']) >= 8]
    return issues, sections


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--file', help='chỉ xử lý một hồ sơ (khớp tên thư mục)')
    args = ap.parse_args()

    if not SRC.is_dir():
        sys.exit(f'Không tìm thấy {SRC}')
    files = sorted(SRC.glob(GLOB))
    if args.file:
        files = [f for f in files if args.file.lower() in str(f).lower()]
    if not files:
        sys.exit('Không có file nào khớp.')

    records, hong = [], []
    for f in files:
        try:
            text = f.read_text(encoding='utf-8', errors='replace')
            meta = parse_meta(text)
            issues, sections = parse_issues(text)
        except Exception as e:                        # noqa: BLE001
            hong.append((f, repr(e)))
            continue
        records.append({
            'ho_so': f.parent.name,
            'duong_dan': str(f.relative_to(ROOT)).replace('\\', '/'),
            'so_dong': len(text.splitlines()),
            **meta,
            'muc_chua_van_de': sections,
            'van_de': issues,
        })

    # ---- báo cáo ----
    tong_vd = sum(len(r['van_de']) for r in records)
    loai = collections.Counter(r['loai_ho_so'] for r in records)
    print(f'Đã đọc {len(records)}/{len(files)} hồ sơ · {tong_vd} vấn đề trích được\n')
    print(f"  Trường hợp A (có PNX) : {loai.get('A', 0)}")
    print(f"  Trường hợp B (duyệt thẳng): {loai.get('B', 0)}")
    print(f"  Không xác định        : {loai.get(None, 0)}")

    vong = [r['so_vong'] for r in records if r['so_vong']]
    if vong:
        print(f'\n  Số vòng phản hồi: {len(vong)} hồ sơ ghi rõ · '
              f'trung bình {sum(vong)/len(vong):.2f} · '
              f'phân bố {dict(sorted(collections.Counter(vong).items()))}')

    # Tách hai lý do khác hẳn nhau, đừng gộp làm một:
    #  - hồ sơ B duyệt thẳng thì KHÔNG CÓ vấn đề nào để trích — đúng, không phải lỗi
    #  - hồ sơ A mà trích ra rỗng thì mới đáng ngờ, phải xem tay
    trong = [r for r in records if not r['van_de']]
    binh_thuong = [r['ho_so'] for r in trong if r['loai_ho_so'] == 'B']
    dang_ngo = [r for r in trong if r['loai_ho_so'] != 'B']
    if binh_thuong:
        print(f'\n  {len(binh_thuong)} hồ sơ Trường hợp B không có vấn đề — đúng như '
              f'mong đợi (duyệt thẳng, không có PNX).')
    if dang_ngo:
        print(f'\n  ⚠️  {len(dang_ngo)} hồ sơ CÓ PNX nhưng không trích được vấn đề — '
              f'cần xem tay:')
        for r in dang_ngo:
            print(f"      - {r['ho_so']} ({r['so_dong']} dòng)")
    thieu = [r['ho_so'] for r in trong]
    if hong:
        print(f'\n  ❌ {len(hong)} file lỗi khi đọc:')
        for f, e in hong:
            print(f'      - {f}: {e}')

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'issues.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=1), encoding='utf-8')
    write_md(records, tong_vd, loai, vong, thieu)
    print(f'\n-> {OUT / "issues.json"}\n-> {OUT / "issues.md"}')
    return 0


def write_md(records, tong_vd, loai, vong, thieu) -> None:
    L: list[str] = []
    A = L.append
    A('# Vấn đề người thẩm định đã bắt — trích từ `approved-sizing/`\n')
    A('> Sinh bằng `scripts/extract_appraisal_issues.py`. **Không sửa tay file này** —')
    A('> chạy lại script. Bản ánh xạ sang mã quy tắc nằm ở `appraisal-mapping.md`.\n')
    A('> ⚠️ **Nguồn là tóm tắt do AI khác viết lại, không phải nguyên văn PNX.**')
    A('> Bản gốc (.docx/.pdf) không còn. Dùng để hiểu xu hướng, KHÔNG dùng làm nhãn')
    A('> vàng chấm điểm (vi phạm NT2, recall tính ra sẽ ảo).\n')
    A(f'**{len(records)} hồ sơ · {tong_vd} vấn đề.** '
      f"Trường hợp A {loai.get('A', 0)} · B {loai.get('B', 0)} · "
      f"không rõ {loai.get(None, 0)}.")
    if vong:
        A(f'Số vòng phản hồi trung bình **{sum(vong)/len(vong):.2f}** '
          f'trên {len(vong)} hồ sơ ghi rõ.\n')
    if thieu:
        A(f'\n{len(thieu)} hồ sơ không trích được vấn đề nào: '
          + ', '.join(f'`{h}`' for h in thieu) + '.\n')
    A('\n---\n')
    for r in sorted(records, key=lambda x: -len(x['van_de'])):
        A(f"## {r['ho_so']}\n")
        bits = [f"**PYC:** {r['ma_pyc'] or '—'}",
                f"**Thẩm định:** {r['nguoi_tham_dinh'] or '—'}",
                f"**Loại:** {r['loai_ho_so'] or '—'}",
                f"**Số vòng:** {r['so_vong'] or '—'}"]
        A(' · '.join(bits) + '\n')
        if not r['van_de']:
            A('_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._\n')
            continue
        A('| # | Vấn đề | Mục nguồn |')
        A('|---:|---|---|')
        for i, v in enumerate(r['van_de'], 1):
            td = v['tieu_de'].replace('|', '\\|')
            A(f"| {i} | {td} | {v['muc'][:38]} |")
        A('')
    (OUT / 'issues.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


if __name__ == '__main__':
    raise SystemExit(main())
