#!/usr/bin/env python
"""Đo BÁO CÁO NGƯỜI DÙNG THẬT NHÌN THẤY — dài bao nhiêu, bao nhiêu là nhiễu.

    py scripts/do_bao_cao.py "danh_sach_sizings_da_duyet/<hồ sơ>/<file>.docx"
    py scripts/do_bao_cao.py <file.docx> --ghi bao-cao-mau.md

Chạy sau một lượt eval thì **gần như miễn phí**: đệm lời gọi (2.12) còn nguyên,
nên hầu hết lượt gọi lấy trong đệm. Script in ra số lượt phải gọi thật để không
ai phải đoán mình vừa tiêu bao nhiêu.

## Vì sao cần đo riêng con số này

Lượt dev 2026-09-09 cho thấy pipeline sinh **200–717 finding cho MỘT tài liệu**,
và **95,5% thuộc nhóm «không tìm thấy / không kiểm chứng được»**. Nhưng đó là số
TRƯỚC C7 — C7 còn khử trùng và hoãn Vòng 2. Cái quyết định demo là con số SAU
C7: người đánh giá mở báo cáo ra và thấy bao nhiêu dòng.

Một báo cáo 700 dòng toàn «không tìm thấy trường này» sẽ khiến người đọc kết
luận công cụ không chạy được — bất kể recall 87,5%. Nên phải đo trước khi demo,
không phải sau.
"""
from __future__ import annotations

import argparse
import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.llm.client import LLMClient                  # noqa: E402
from src.pipeline import chay                         # noqa: E402
from src.reporting.report import load_labels, xu_ly   # noqa: E402
from src.version import in_phien_ban                  # noqa: E402

# Nhóm finding chỉ nói "công cụ không đọc được chỗ này" — chúng hợp lệ theo NT4
# nhưng KHÔNG phải phát hiện về chất lượng bản sizing.
NHIEU = {"thieu_thong_tin", "khong_kiem_chung_duoc"}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--ghi", default="", help="ghi báo cáo Markdown ra file")
    ap.add_argument("--song-song", type=int, default=12)
    a = ap.parse_args()
    in_phien_ban("đo kích thước báo cáo")

    client = LLMClient()
    kq = chay(a.docx, client=client, song_song=a.song_song)
    tk = client.cache.tk
    print(f"\nĐệm: {tk.trung} lượt lấy trong đệm · {tk.truot} lượt phải gọi model")

    rep = xu_ly(kq.findings, load_labels(),
                ten_he_thong=kq.sizing.ten_he_thong, ma_pyc=kq.sizing.ma_pyc)
    bc = kq.bao_cao()

    phan = [("Vòng 1 (checklist)", rep.vong1),
            ("Vòng 2 — chưa đạt", rep.vong2_chua_dat),
            ("Vòng 2 — chưa kiểm được", rep.vong2_chua_kiem),
            ("Vòng 2 — tạm hoãn", rep.vong2_tam_hoan),
            ("Khác (cảnh báo ảnh…)", rep.khac)]
    hien = sum(len(v) for _, v in phan)

    print(f"\n{'':34}{'finding':>9}")
    print("-" * 44)
    for ten, ds in phan:
        print(f"{ten:34}{len(ds):9}")
    print("-" * 44)
    print(f"{'TỔNG HIỆN RA':34}{hien:9}")
    print(f"{'  (trước C7)':34}{len(kq.findings):9}")
    print(f"{'  bị lọc vì không căn cứ (NT2)':34}{rep.so_loc_khong_can_cu:9}")
    print(f"{'  gộp trùng':34}{rep.so_khu_trung:9}")

    c = collections.Counter(f.category for _, ds in phan for f in ds)
    nhieu = sum(v for k, v in c.items() if k in NHIEU)
    print("\nTheo nhóm (chỉ phần HIỆN RA):")
    for k, v in c.most_common():
        print(f"  {v:5}  {k}")
    if hien:
        print(f"\n⚠ {nhieu}/{hien} = {nhieu / hien:.1%} là «không tìm thấy / không "
              "kiểm chứng được» — tức nhiễu với người đọc.")
        print(f"  Còn lại {hien - nhieu} phát hiện thật sự nói về chất lượng bản sizing.")
    print(f"\nBáo cáo Markdown: {len(bc.splitlines())} dòng · {len(bc):,} ký tự")
    if a.ghi:
        pathlib.Path(a.ghi).write_text(bc, encoding="utf-8")
        print(f"Đã ghi {a.ghi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
