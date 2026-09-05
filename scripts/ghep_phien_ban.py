"""In bảng ghép **vòng nhận xét PNX ↔ phiên bản `.docx`** cho mọi hồ sơ có nhãn.

Chạy OFFLINE, không gọi model. Dùng để soi bằng mắt trước khi tin vào cách chọn
bản của `eval/run_eval.py`.

    python scripts/ghep_phien_ban.py            # hồ sơ có nhãn
    python scripts/ghep_phien_ban.py --tat-ca   # cả hồ sơ không có nhãn
"""
from __future__ import annotations

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from eval.matching import nap_nhan                              # noqa: E402
from eval.phien_ban import ghep_phien_ban, so_vong_theo_ho_so   # noqa: E402
from src.ingestion.filenames import find_sizing_docs            # noqa: E402

GOC = pathlib.Path("danh_sach_sizings_da_duyet")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tat-ca", action="store_true",
                    help="in cả hồ sơ không có nhãn PNX")
    a = ap.parse_args()

    labels = nap_nhan("tat_ca")
    so_vong = so_vong_theo_ho_so(labels)
    nhan_theo_vong: dict[tuple[str, int], int] = {}
    for l in labels:
        nhan_theo_vong[(l["dossier"], int(l.get("lan_nhan_xet") or 1))] = \
            nhan_theo_vong.get((l["dossier"], int(l.get("lan_nhan_xet") or 1)), 0) + 1

    ds = sorted(d.name for d in GOC.iterdir() if d.is_dir())
    if not a.tat_ca:
        ds = [d for d in ds if d in so_vong]

    tong_lech = tong_nhan = 0
    khac_cach_cu = 0
    for d in ds:
        kq = ghep_phien_ban(GOC / d, so_vong=so_vong.get(d, 1))
        cu = find_sizing_docs(str(GOC / d))
        ten_cu = cu[0].name if cu else "—"
        moi = kq.ban_vong1.ten if kq.ban_vong1 else "—"
        doi = " ⚠ KHÁC CÁCH CŨ" if moi != ten_cu else ""
        if doi:
            khac_cach_cu += 1
        print(f"\n{d}  ({len(kq.bans)} bản cùng họ, {so_vong.get(d, 1)} vòng, "
              f"độ tin {kq.do_tin}){doi}")
        for i, b in enumerate(kq.bans, 1):
            vong = [str(v) for v, x in kq.theo_vong.items() if x is b]
            danh = f"  ← vòng {', '.join(vong)}" if vong else ""
            print(f"   {i}. {b.sua_cuoi or 'không rõ ngày':19s}  {b.ten[:58]}{danh}")
        for b in kq.bo_ngoai:
            print(f"      (bỏ ra) {b.sua_cuoi or '?':19s}  {b.ten[:58]}")
        for c in kq.canh_bao:
            print(f"   ⚠ {c}")
        if ten_cu != moi:
            print(f"   • cách cũ (theo bảng chữ cái) dùng: {ten_cu[:58]}")
        for vong in range(1, so_vong.get(d, 1) + 1):
            n = nhan_theo_vong.get((d, vong), 0)
            tong_nhan += n
            if vong > len(kq.bans):
                tong_lech += n

    print(f"\n{'='*74}")
    print(f"{khac_cach_cu}/{len(ds)} hồ sơ đổi bản so với cách chọn theo bảng chữ cái.")
    print(f"{tong_lech}/{tong_nhan} nhãn vẫn bị chấm trên bản ĐÃ SỬA vì hồ sơ không "
          f"giữ đủ phiên bản cho từng vòng — đây là phần thiên lệch CÒN LẠI, "
          f"không vá được bằng code.")


if __name__ == "__main__":
    main()
