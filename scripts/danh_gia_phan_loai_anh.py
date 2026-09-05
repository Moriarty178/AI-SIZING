"""Đo độ chính xác của C2/2.2 trên bộ nhãn tay `data/nhan_anh_mau.json`.

Chạy hoàn toàn OFFLINE — không gọi model. Đây là con số nghiệm thu của mục 2.2.

    python scripts/danh_gia_phan_loai_anh.py            # 40 ảnh có nhãn
    python scripts/danh_gia_phan_loai_anh.py --toan-bo  # thêm phân bố trên cả 776 ảnh

Đọc kỹ phần `han_che` in ra ở cuối: nhãn do một tác nhân AI gán, n=40.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx           # noqa: E402
from src.ingestion.filenames import find_sizing_docs      # noqa: E402
from src.vision.anh import byte_anh, trich_anh            # noqa: E402
from src.vision.phan_loai import phan_loai                # noqa: E402

FIXTURE = pathlib.Path("data/nhan_anh_mau.json")
LOAI = ["so_do", "console", "dashboard", "anh_van_ban", "chua_ro"]


def _doc_nhan() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def do_tren_nhan() -> None:
    bo = _doc_nhan()
    theo_file: dict[str, list[dict]] = collections.defaultdict(list)
    for n in bo["nhan"]:
        theo_file[n["docx"]].append(n)

    nham: collections.Counter = collections.Counter()   # (thật, máy đoán)
    chi_tiet: list[tuple] = []
    for duong_dan, ds in sorted(theo_file.items()):
        doc = read_docx(duong_dan)
        kq = trich_anh(doc)
        theo_ma = {a.ma: a for a in kq.anh}
        for n in ds:
            a = theo_ma.get(n["ma"])
            if a is None:
                nham[(n["loai"], "KHONG_TIM_THAY")] += 1
                continue
            r = phan_loai(a, byte_anh(doc, a))
            nham[(n["loai"], r.loai)] += 1
            chi_tiet.append((n["loai"], r.loai, r.do_tin, n["mo_ta"],
                             "; ".join(r.tin_hieu) or r.ly_do_khong_ro))

    tong = sum(nham.values())
    dung = sum(v for (t, m), v in nham.items() if t == m)
    bo_ngo = sum(v for (t, m), v in nham.items() if m == "chua_ro")
    quyet = tong - bo_ngo
    dung_khi_quyet = sum(v for (t, m), v in nham.items() if t == m and m != "chua_ro")

    print(f"\n{'='*74}\nĐỘ CHÍNH XÁC C2/2.2 trên {tong} ảnh có nhãn tay\n{'='*74}")
    print(f"  Đúng            : {dung}/{tong} ({dung/tong:.0%})")
    print(f"  Trả 'chưa rõ'   : {bo_ngo}/{tong} ({bo_ngo/tong:.0%})  ← không sai, chỉ là không kết luận")
    if quyet:
        print(f"  Đúng KHI dám kết luận: {dung_khi_quyet}/{quyet} ({dung_khi_quyet/quyet:.0%})"
              "  ← con số quan trọng nhất: ưu tiên chính xác hơn độ phủ")

    print("\nMa trận nhầm lẫn (hàng = nhãn tay, cột = máy đoán):")
    cot = LOAI + ["KHONG_TIM_THAY"]
    print(f"{'':14s}" + "".join(f"{c[:11]:>13s}" for c in cot))
    for t in LOAI:
        if not any(nham[(t, m)] for m in cot):
            continue
        print(f"{t:14s}" + "".join(f"{nham[(t, m)]:13d}" for m in cot))

    sai = [c for c in chi_tiet if c[0] != c[1]]
    if sai:
        print(f"\n{len(sai)} ca máy đoán khác nhãn tay:")
        for that, may, tin, mo_ta, vi_sao in sai:
            print(f"  thật={that:12s} máy={may:12s} ({tin}) {mo_ta}")
            print(f"      vì: {vi_sao}")

    print("\nHạn chế phải nêu kèm mọi con số ở trên:")
    for h in bo["han_che"]:
        print(f"  - {h}")


def do_toan_bo() -> None:
    """Phân bố loại trên toàn bộ ảnh của 47 bản — KHÔNG có nhãn, chỉ để xem hình dạng."""
    dem: collections.Counter = collections.Counter()
    tin: collections.Counter = collections.Counter()
    ly_do: collections.Counter = collections.Counter()
    files = find_sizing_docs("danh_sach_sizings_da_duyet")
    for i, f in enumerate(files, 1):
        doc = read_docx(str(f))
        kq = trich_anh(doc)
        for a in kq.anh:
            r = phan_loai(a, byte_anh(doc, a))
            dem[r.loai] += 1
            tin[(r.loai, r.do_tin)] += 1
            if r.loai == "chua_ro":
                ly_do[r.ly_do_khong_ro.split("(")[0].strip()] += 1
        print(f"\r  {i}/{len(files)} bản…", end="", flush=True)
    tong = sum(dem.values())
    print(f"\r{'='*74}\nPHÂN BỐ trên toàn bộ {tong} ảnh của {len(files)} bản (KHÔNG có nhãn)\n{'='*74}")
    for k, v in dem.most_common():
        print(f"  {k:14s} {v:4d}  ({v/tong:5.1%})")
    print("\n  Theo độ tin:")
    for (k, d), v in sorted(tin.items()):
        print(f"    {k:14s} {d:5s} {v:4d}")
    if ly_do:
        print("\n  Vì sao 'chưa rõ':")
        for k, v in ly_do.most_common():
            print(f"    {v:4d}  {k}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--toan-bo", action="store_true",
                    help="đo thêm phân bố trên toàn bộ ảnh của 47 bản")
    args = ap.parse_args()
    do_tren_nhan()
    if args.toan_bo:
        do_toan_bo()
