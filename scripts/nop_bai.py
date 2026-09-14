#!/usr/bin/env python
"""Nộp một bản sizing cho dịch vụ thẩm định rồi chờ kết quả. Dùng ngoài container.

    py scripts/nop_bai.py "D:\\ho so\\Sizing ABC.docx"
    py scripts/nop_bai.py <file.docx> --api http://localhost:8902 --ra bao-cao.md
    py scripts/nop_bai.py --ma 6a15c6ff073b        # tra lại một việc đã nộp

Gọi qua `src/khach_api.py` — đúng module giao diện Streamlit dùng, nên nếu lệnh
này chạy được thì giao diện cũng chạy được, và ngược lại.

## Vì sao không chỉ dùng `curl`

`curl … | python -m json.tool` trên Windows đọc stdin theo cp1252, nên tiếng Việt
trong phản hồi hiện ra như `ChÆ°a cÃ³` — đã mất một lượt truy vết vì chuyện đó
ngày 2026-09-09. Script này ép UTF-8 ở mọi chỗ đọc.

Một tài liệu tốn khoảng **16 phút**. Script in tiến độ theo giai đoạn (C3 → C5)
để phân biệt "đang chạy" với "treo".
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh   # noqa: E402
from src.version import in_phien_ban                            # noqa: E402

NHAN = {"cho": "đang xếp hàng", "dang_chay": "đang chạy", "xong": "XONG",
        "hong": "HỎNG", "gian_doan": "GIÁN ĐOẠN"}


def _tien_do(d: dict) -> str:
    td = d.get("tien_do")
    phan = f"{td:.0%}" if td is not None else "chưa rõ tổng"
    gd = d.get("giai_doan") or "…"
    return (f"{NHAN.get(d['trang_thai'], d['trang_thai'])} · {gd} "
            f"{d.get('da_xong', 0)}/{d.get('tong', 0)} ({phan}) · "
            f"{d.get('giay_da_chay', 0):.0f}s")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx", nargs="?", help="bản sizing .docx cần thẩm định")
    ap.add_argument("--api", default=dia_chi_mac_dinh(),
                    help=f"địa chỉ dịch vụ (mặc định {dia_chi_mac_dinh()})")
    ap.add_argument("--ma", default="", help="tra lại một việc đã nộp trước đó")
    ap.add_argument("--ra", default="", help="ghi báo cáo ra file .md")
    ap.add_argument("--nhom", default="", help="giới hạn nhóm quy tắc, vd KPI,CPU")
    ap.add_argument("--vong", type=int, default=None, choices=[1, 2])
    ap.add_argument("--song-song", type=int, default=None)
    ap.add_argument("--giay-hoi", type=int, default=15, help="nhịp hỏi lại")
    a = ap.parse_args()
    in_phien_ban("nộp bài")

    kh = KhachAPI(a.api, timeout=60)
    sk = kh.suc_khoe()
    if not sk.song:
        print(f"\n✗ Không gọi được dịch vụ tại {kh.dia_chi}\n  {sk.thong_diep}")
        print("  Kiểm: docker compose ps · docker compose logs copilot")
        return 2
    print(f"dịch vụ: SỐNG · commit {sk.commit} · model sẵn sàng: "
          f"{'CÓ' if sk.model_san_sang else 'CHƯA'} · đang chờ {sk.dang_cho} việc")
    if not sk.model_san_sang:
        # Không chặn: người dùng có thể muốn nộp để xem đường chạy. Nhưng phải
        # nói trước, vì việc sẽ hỏng sau vài giây chứ không chạy được.
        print(f"  ⚠ {sk.ghi_chu_model}")

    ma = a.ma
    if not ma:
        if not a.docx:
            print("\n✗ Cần một file .docx, hoặc --ma để tra việc cũ.")
            return 2
        p = pathlib.Path(a.docx)
        if not p.is_file():
            print(f"\n✗ Không thấy file: {p}")
            return 2
        try:
            d = kh.nop(p.read_bytes(), p.name, nhom=a.nhom,
                       vong="" if a.vong is None else a.vong,
                       song_song="" if a.song_song is None else a.song_song)
        except LoiAPI as e:
            print(f"\n✗ Nộp không thành công: {e}")
            return 2
        ma = d["ma"]
        print(f"\nĐã nhận «{p.name}» · MÃ VIỆC: {ma}")
        print("  Ghi lại mã này — đóng cửa sổ rồi vẫn tra được:")
        print(f"    py scripts/nop_bai.py --ma {ma} --api {kh.dia_chi}")

    print("\nMột tài liệu tốn khoảng 16 phút.")
    truoc = ""
    while True:
        try:
            d = kh.viec(ma)
        except LoiAPI as e:
            print(f"\n✗ Không tra được mã «{ma}»: {e}")
            return 2
        dong = _tien_do(d)
        if dong != truoc:
            print("  " + dong)
            truoc = dong
        if d["trang_thai"] in ("xong", "hong", "gian_doan"):
            break
        time.sleep(max(1, a.giay_hoi))

    if d["trang_thai"] != "xong":
        print(f"\n✗ {NHAN.get(d['trang_thai'])}: {d.get('loi') or 'không rõ lý do'}")
        return 1

    bc = kh.bao_cao(ma)
    muc = d.get("theo_muc_do") or {}
    print(f"\n✓ Xong sau {d['giay_da_chay'] / 60:.1f} phút · "
          f"{d.get('so_finding', 0)} phát hiện"
          + (" · " + " · ".join(f"{k} {v}" for k, v in sorted(muc.items())) if muc else ""))
    ra = pathlib.Path(a.ra) if a.ra else pathlib.Path(f"bao-cao-{ma}.md")
    ra.write_text(bc, encoding="utf-8")
    print(f"  Báo cáo: {ra} ({len(bc.splitlines())} dòng)")
    print("\n--- MỤC ĐẦU BÁO CÁO ---")
    for dong in bc.splitlines()[:40]:
        print(dong)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
