#!/usr/bin/env python
"""1.7 — chạy C1 → C3 → C4 trên một bản sizing THẬT. Phải chạy trong mạng công ty.

    python scripts/try_c3_on_dossier.py <đường-dẫn.docx> [--nhom KPI,CPU] [--model X]

Mặc định giới hạn ở vài nhóm quy tắc cho rẻ; bỏ `--nhom` để chạy toàn bộ (31–95 lượt
gọi tuỳ số phân hệ, ~3–8 phút).

**Con số cần nhìn nhất là `không neo được`.** Đó là số giá trị model đưa ra mà code
KHÔNG tìm lại được trong tài liệu — tức model bịa hoặc diễn đạt lại thay vì chép. Trên
dữ liệu giả nó bằng 0; trên tài liệu thật thì chưa ai biết, và nó quyết định cổng chống
bịa của C3 có dùng được hay phải nới.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.extraction.extractor import Extractor, uoc_tinh_luot_goi

# Đo thật trên mạng công ty 2026-09-04: ~40s mỗi lượt, KHÔNG phải 5s như smoke test.
# Chênh vì smoke test chỉ có 3 trường, còn một lượt trích thật có tới 18 trường × 2
# chuỗi — token ĐẦU RA mới là thứ chi phối.
GIAY_MOI_LUOT = 40
from src.ingestion.docx_reader import read_docx
from src.version import PHIEN_BAN_C3, commit_hien_tai, in_phien_ban
from src.llm.client import LLMClient, LLMError
from src.validators.quantitative import QuantitativeValidator


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--nhom", default="KPI,CPU,RAM",
                    help="lọc nhóm quy tắc, phân tách bằng dấu phẩy; rỗng = tất cả")
    ap.add_argument("--model", default=None)
    ap.add_argument("--song-song", type=int, default=6,
                    help="số lời gọi chạy đồng thời (rate limit ở 0.10 rất thoáng)")
    ap.add_argument("--phan-he", type=int, default=0,
                    help="số phân hệ dự kiến, chỉ dùng cho --uoc-tinh")
    ap.add_argument("--uoc-tinh", action="store_true",
                    help="chỉ in ước lượng số lời gọi rồi thoát, không gọi model")
    a = ap.parse_args()

    in_phien_ban()
    doc = read_docx(a.docx)
    print(f"C1: {len(doc.elements)} phần tử · {len(doc.tables())} bảng · "
          f"{len(doc.images())} ảnh · trang: {doc.page_source}")
    for w in doc.warnings:
        print(f"  ⚠ {w}")

    # In ước lượng TRƯỚC khi gọi model. Không có nó thì người chạy ngồi nhìn màn hình
    # đứng im vài phút và tưởng script treo — đã xảy ra thật (2026-09-04).
    nhom0 = [x.strip() for x in a.nhom.split(",") if x.strip()] or None
    for n in ([a.phan_he] if a.phan_he else (1, 5, 13)):
        u = uoc_tinh_luot_goi(chi_nhom=nhom0, so_phan_he=n)
        print(f"  ước lượng nếu {n} phân hệ: {u['tong']} lượt gọi · "
              f"~{u['tong'] * GIAY_MOI_LUOT / 60:.0f} phút tuần tự · "
              f"~{u['tong'] * GIAY_MOI_LUOT / 60 / a.song_song:.0f} phút với "
              f"{a.song_song} luồng")
    if a.uoc_tinh:
        return 0

    try:
        client = LLMClient()
    except (FileNotFoundError, LLMError) as e:
        print(f"Chưa chạy được: {e}")
        return 2

    chi_nhom = [x.strip() for x in a.nhom.split(",") if x.strip()] or None

    def tien_do(i: int, tong: int, nhan: str) -> None:
        print(f"  C3 {i}/{tong} · {nhan}", flush=True)

    ex = Extractor(client, model=a.model, on_tien_do=tien_do,
                   song_song=a.song_song)
    t0 = time.time()
    core = ex.run(doc, chi_nhom=chi_nhom)
    giay = time.time() - t0
    print()

    print(f"\nC3: {ex.tk.tom_tat()}")
    print(f"    {giay:.0f}s · hệ thống: {core.ten_he_thong!r} · "
          f"loại: {core.loai_sizing} · {len(core.phan_he)} phân hệ")
    for ph in core.phan_he:
        print(f"      - {ph.ten_phan_he} ({ph.cong_nghe or '?'}) "
              f"{len(ph.params)} tham số · {ph.location}")
    for e in ex.tk.loi[:5]:
        print(f"  ⚠ {e}")

    outs = QuantitativeValidator().run(core)
    dem: dict[str, int] = {}
    for o in outs:
        dem[o.status] = dem.get(o.status, 0) + 1
    print(f"\nC4: {dem}")

    ra = pathlib.Path("docs/smoke") / f"c3-{time.strftime('%Y%m%d-%H%M')}.json"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "docx": a.docx, "nhom": chi_nhom, "model": a.model, "giay": round(giay),
        "phien_ban": PHIEN_BAN_C3, "commit": commit_hien_tai(),
        "thong_ke": ex.tk.__dict__, "c4": dem,
        "sizing": core.model_dump(),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nĐã ghi {ra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
