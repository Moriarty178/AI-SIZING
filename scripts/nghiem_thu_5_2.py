#!/usr/bin/env python
"""Nghiệm thu 5.2 trên máy nội bộ — hiện chỗ cần sửa + ghi nhận lần sửa.

    py scripts/nghiem_thu_5_2.py --ho-so 1 "<file.docx>" --api http://localhost:8902 --ten "Tên bạn"

1. Thẩm định lại hồ sơ bằng tệp đã cho (đệm bật: vài phút). BẮT BUỘC sau khi dựng
   image 5.2: các lần nộp trước đó để tài liệu ở `/tmp` của container cũ, đã mất
   khi container dựng lại — không còn gì để hiện chỗ sửa.
2. Hỏi `/ho-so/{id}/finding/{fb}` cho MỌI dòng baseline, đếm công cụ định vị được
   tới đâu. Đây là con số KHÔNG đo được trên laptop.
3. Ghi nhận hai lần sửa vào một dòng, đọc lại, kiểm thứ tự + tên tiếng Việt; và
   kiểm thiếu danh tính thì bị từ chối.

## Tiêu chí (đặt trước)

- **S1** Mọi dòng baseline trả được `cho_sua`.                         (cứng)
- **S2** Tài liệu của lần mới nhất còn trên máy chủ.                   (cứng)
- **S3** Ghi nhận 2 lần → `so_lan` = 1 rồi 2, lịch sử đọc lại đủ 2.     (cứng)
- **S4** Tên người ghi nhận lưu nguyên vẹn.                            (cứng)
- **S5** Ghi nhận không kèm danh tính → HTTP 400.                      (cứng)
- **Đ1** Phân bố cách định vị — ĐO, không chấm đạt/không: bao nhiêu dòng tới
         đúng phần tử / mục+trang / chỉ gợi ý theo tên phân hệ / không tìm được.

⚠️ Script GHI hai lần sửa thật vào dòng baseline đầu tiên của hồ sơ. Dùng hồ sơ
nghiệm thu (vd #1 của 5.1), đừng dùng hồ sơ thật của người dùng.

Kết quả chỉ chứa số đếm — không có nội dung tài liệu, commit được.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh   # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh                 # noqa: E402
from src.version import in_phien_ban                            # noqa: E402

CHINH_XAC = ("phan_tu", "muc_trang", "muc", "trang")
TAI_LIEU_MAT = "không còn trên máy chủ"


def cham(*, cach_tim: list[str], ghi_chu_mat: int, so_lan: list[int],
         so_lich_su: int, ten_luu: str, ten_gui: str, ma_khong_danh_tinh: int | None,
         so_dong: int) -> list[dict]:
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    ghi("S1", len(cach_tim) == so_dong and so_dong > 0,
        f"{len(cach_tim)}/{so_dong} dòng trả được chỗ sửa")
    ghi("S2", ghi_chu_mat == 0, f"{ghi_chu_mat} dòng báo tài liệu «{TAI_LIEU_MAT}»")
    ghi("S3", so_lan == [1, 2] and so_lich_su >= 2,
        f"so_lan trả về {so_lan}, lịch sử đọc lại {so_lich_su} dòng")
    ghi("S4", ten_luu == ten_gui, f"tên lưu «{ten_luu}» — gửi «{ten_gui}»")
    ghi("S5", ma_khong_danh_tinh == 400, f"không danh tính → HTTP {ma_khong_danh_tinh}")

    dem = collections.Counter(cach_tim)
    n = len(cach_tim) or 1
    chinh_xac = sum(dem[c] for c in CHINH_XAC)
    ghi("Đ1", None, f"định vị (phần tử/mục/trang) {chinh_xac} = {chinh_xac / n:.1%} · "
                    f"chỉ gợi ý theo tên phân hệ {dem['ten_phan_he']} = "
                    f"{dem['ten_phan_he'] / n:.1%} · không tìm được "
                    f"{dem['khong_tim_duoc']} = {dem['khong_tim_duoc'] / n:.1%} · "
                    f"chi tiết {dict(dem)}")
    return kq


def _ma_http_khong_danh_tinh(dia_chi: str, ho_so: int, fb: int) -> int | None:
    """Gọi thẳng, không qua `KhachAPI` (vốn luôn gắn danh tính)."""
    req = urllib.request.Request(
        f"{dia_chi}/ho-so/{ho_so}/finding/{fb}/lan-sua", method="POST",
        data=json.dumps({"noi_dung_sua": "thử không danh tính"}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    mo = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with mo.open(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return None


def _cho(kh: KhachAPI, ma: str) -> dict:
    truoc = ""
    while True:
        d = kh.viec(ma)
        dong = f"{d['trang_thai']} · {d.get('giai_doan') or '…'} {d.get('giay_da_chay', 0):.0f}s"
        if dong != truoc:
            print("  " + dong)
            truoc = dong
        if d["trang_thai"] in ("xong", "hong", "gian_doan"):
            return d
        time.sleep(15)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx", nargs="?", help="tệp để thẩm định lại trước (khuyên dùng)")
    ap.add_argument("--ho-so", type=int, required=True)
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.2")
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.2")

    dt = tao_danh_tinh("nguoi_lam_sizing", a.ten)
    kh = KhachAPI(a.api, timeout=120, danh_tinh=dt)
    sk = kh.suc_khoe()
    if not sk.song or not ((sk.tho or {}).get("csdl") or {}).get("san_sang"):
        print(f"✗ Dịch vụ hoặc CSDL chưa sẵn sàng: {sk.thong_diep or (sk.tho or {}).get('csdl')}")
        return 2
    print(f"dịch vụ: commit {sk.commit}")

    try:
        if a.docx:
            p = pathlib.Path(a.docx)
            print(f"\nThẩm định lại hồ sơ #{a.ho_so} bằng «{p.name}»")
            d = kh.nop(p.read_bytes(), p.name, song_song=12, ho_so_id=a.ho_so)
            v = _cho(kh, d["ma"])
            print(f"  ghi hồ sơ: {v.get('ghi_ho_so')}")
            if v["trang_thai"] != "xong":
                print(f"✗ Việc không xong: {v.get('loi')}")
                return 2

        hs = kh.ho_so(a.ho_so)
        dong = hs.get("baseline") or []
        print(f"\nHỏi chỗ sửa cho {len(dong)} dòng baseline…")
        cach_tim, mat, t0 = [], 0, time.perf_counter()
        for i, b in enumerate(dong, 1):
            c = kh.finding_ho_so(a.ho_so, b["id"]).get("cho_sua") or {}
            cach_tim.append(c.get("cach_tim", "?"))
            mat += TAI_LIEU_MAT in (c.get("ghi_chu") or "")
            if i % 100 == 0:
                print(f"  {i}/{len(dong)}")
        giay = time.perf_counter() - t0
        if mat:
            print(f"⚠️  {mat} dòng: tài liệu không còn — chạy lại kèm tệp .docx để "
                  "thẩm định lại trước.")

        fb = dong[0]["id"]
        r1 = kh.ghi_lan_sua(a.ho_so, fb, "Nghiệm thu 5.2 — lần sửa thứ nhất")
        r2 = kh.ghi_lan_sua(a.ho_so, fb, "Nghiệm thu 5.2 — lần sửa thứ hai")
        d = kh.finding_ho_so(a.ho_so, fb)
        ls = d.get("lan_sua") or []
        ma_400 = _ma_http_khong_danh_tinh(kh.dia_chi, a.ho_so, fb)
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = cham(cach_tim=cach_tim, ghi_chu_mat=mat, so_lan=[r1["so_lan"], r2["so_lan"]],
              so_lich_su=len(ls), ten_luu=(ls[-1] if ls else {}).get("ten", ""),
              ten_gui=dt.ten, ma_khong_danh_tinh=ma_400, so_dong=len(dong))
    print()
    for k in kq:
        print(f"  {({True: '✓', False: '✗', None: '·'})[k['dat']]} {k['ma']}  {k['chi_tiet']}")
    print(f"  · {len(dong)} lượt hỏi chỗ sửa mất {giay:.1f} giây "
          f"({giay / max(1, len(dong)) * 1000:.0f} ms/dòng)")
    hong = [k["ma"] for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.2: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.2: CHƯA ĐẠT ({', '.join(hong)})"))

    ra = pathlib.Path(f"docs/nghiem-thu-5.2-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "ho_so_id": a.ho_so, "commit": sk.commit, "so_dong": len(dong),
        "cach_tim": dict(collections.Counter(cach_tim)), "giay_hoi_cho_sua": round(giay, 1),
        "tieu_chi": kq}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Kết quả: {ra} — chỉ số đếm, gửi lại file này.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
