"""Chạy thật C2/2.3 — đọc ảnh bằng vision — trên MỘT bản sizing. CẦN MODEL.

    py scripts/thu_doc_anh.py "<đường dẫn .docx>" --uoc-tinh     # đếm trước, KHÔNG gọi model
    py scripts/thu_doc_anh.py "<đường dẫn .docx>"                # chạy thật
    py scripts/thu_doc_anh.py "<đường dẫn .docx>" --loai so_do,console,dashboard

Mặc định chỉ đọc `so_do` + `console` (chốt 2026-09-05). `--uoc-tinh` chạy được ở
laptop, không cần model.

**Con số quan trọng nhất cần nhìn: `trich_dan_bia`** — số giá trị bị loại vì không
nằm trong chính đoạn trích dẫn của nó. Cao nghĩa là model đang bịa, cùng loại rủi
ro đã thấy ở C3.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx                 # noqa: E402
from src.llm.client import LLMClient, LLMError                  # noqa: E402
from src.version import commit_hien_tai, in_phien_ban           # noqa: E402
from src.vision.doc_anh import (LOAI_MAC_DINH, DocAnh,          # noqa: E402
                                thanh_finding, uoc_tinh_luot_goi_anh)

GIAY_MOI_LUOT = 40      # đo thật ở 0.10


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("docx")
    ap.add_argument("--loai", default=",".join(LOAI_MAC_DINH),
                    help="các loại ảnh sẽ đọc, ngăn cách bằng dấu phẩy")
    ap.add_argument("--uoc-tinh", action="store_true",
                    help="chỉ đếm số ảnh sẽ đọc rồi thoát (không cần model)")
    ap.add_argument("--song-song", type=int, default=4)
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    loai = tuple(x.strip() for x in a.loai.split(",") if x.strip())
    in_phien_ban("C2/2.3 đọc ảnh")
    doc = read_docx(a.docx)

    u = uoc_tinh_luot_goi_anh(doc, loai)
    phut = u["se_doc"] * GIAY_MOI_LUOT / 60 / max(1, a.song_song)
    print(f"\n{pathlib.Path(a.docx).name}")
    print(f"  {u['tong_anh']} ảnh · phân bố: "
          + " · ".join(f"{k} {v}" for k, v in sorted(u["theo_loai"].items())))
    print(f"  sẽ đọc {u['se_doc']} ảnh thuộc {loai} "
          f"→ ~{phut:.0f} phút với {a.song_song} luồng")
    if a.uoc_tinh:
        return 0
    if not u["se_doc"]:
        print("  không có ảnh nào thuộc loại đã chọn — không gọi model.")
        return 0

    try:
        client = LLMClient()
    except (FileNotFoundError, LLMError) as e:
        print(f"Chưa chạy được: {e}")
        return 2

    def tien_do(i, tong, nhan):
        print(f"    {i}/{tong} · {nhan}", flush=True)

    c2 = DocAnh(client, model=a.model, loai=loai, on_tien_do=tien_do,
                song_song=a.song_song)
    t0 = time.time()
    kq = c2.run(doc)
    giay = time.time() - t0

    print(f"\n{'=' * 74}\nKẾT QUẢ ({giay:.0f}s)\n{'=' * 74}")
    print(f"  {c2.tk.tom_tat()}")
    tkc = client.cache.tk
    if tkc.trung:
        print(f"  ⚠ {tkc.trung} lượt lấy TRONG ĐỆM, không phải gọi model mới. "
              f"Đặt SIZING_COPILOT_KHONG_CACHE=1 để đo lại thật.")

    print("\n--- ảnh ĐỌC ĐƯỢC ---")
    for k in [x for x in kq if x.doc_duoc][:12]:
        if k.loai == "so_do":
            print(f"  [{k.ma_anh}] {k.location} · {len(k.thanh_phan)} thành phần: "
                  f"{', '.join(k.thanh_phan[:6])}")
        else:
            print(f"  [{k.ma_anh}] {k.location} · {len(k.so_lieu)} số liệu")
            for s in k.so_lieu[:4]:
                print(f"       {s.nhan} = {s.raw} {s.don_vi}".rstrip()
                      + (f"  (lưỡng nghĩa, cách khác {s.gia_tri_khac})"
                         if s.luong_nghia else "")
                      + f"   ← «{s.trich_dan[:60]}»")

    xau = [x for x in kq if not x.doc_duoc]
    print(f"\n--- ảnh KHÔNG đọc được ({len(xau)}) ---")
    for k in xau[:10]:
        print(f"  [{k.ma_anh}] {k.location}: {k.ly_do[:90]}")

    ra = pathlib.Path("eval/reports") / (
        f"doc-anh-{pathlib.Path(a.docx).stem[:40]}-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "docx": a.docx, "commit": commit_hien_tai(), "loai": list(loai),
        "giay": round(giay), "thong_ke": {k: v for k, v in c2.tk.__dict__.items()
                                          if not k.startswith("_")},
        "ket_qua": [
            {"ma": k.ma_anh, "loai": k.loai, "location": k.location,
             "doc_duoc": k.doc_duoc, "ly_do": k.ly_do,
             "bo_vi_khong_neo": k.bo_vi_khong_neo,
             "thanh_phan": k.thanh_phan, "luong": k.luong, "mo_ta": k.mo_ta,
             "so_lieu": [s.__dict__ for s in k.so_lieu]} for k in kq],
        "finding": [thanh_finding(k).as_dict() for k in kq],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nĐã ghi {ra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
