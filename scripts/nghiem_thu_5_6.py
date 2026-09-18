#!/usr/bin/env python
"""Nghiệm thu 5.6 + 5.9 (bước 1) — bảng lịch sử sửa lỗi và ba cột Admin.

    py scripts/nghiem_thu_5_6.py --ho-so 1 "<bản sizing.docx>" --api http://localhost:8902 --ten "Tên bạn"

Tệp `.docx` là TUỲ CHỌN nhưng nên có ở lần chạy đầu: cột «đầu vào code đã dùng» chỉ có
từ lần thẩm định chạy trên bản 5.6 trở đi (các lần cũ ghi cột đó rỗng). Thẩm định lại
bằng chính tệp đã nộp lần trước thì 5.3 dùng lại toàn bộ câu trả lời model — vài phút,
không tốn lượt gọi nào.

## Tiêu chí (đặt trước)

- **A1** Bảng đọc được: mỗi dòng baseline một dòng, có cột «Lần sửa 1…n».     (cứng)
- **A2** Dòng do C4 kết luận có GIÁ TRỊ ĐẦU VÀO đã dùng.                      (cứng
         nếu có thẩm định lại ở bước trên; không thì chỉ đo)
- **A3** Admin ghi ba cột → đọc lại đúng, kèm tên và vai người ghi.            (cứng)
- **A4** Vai «người làm sizing» ghi ba cột → HTTP 403; thiếu danh tính → 400.  (cứng)
- **A5** Lưu lại y nguyên → không thêm dòng lịch sử nào (CHỈ THÊM, không nhân bản).(cứng)
- **Đ1** Phân bố trạng thái, số dòng bộ lọc mặc định ẩn đi, số dòng có đầu vào code.

⚠️ Script GHI ghi chú Admin thật vào hai dòng đầu của hồ sơ. Dùng hồ sơ nghiệm thu.

Kết quả chỉ chứa số đếm và mã quy tắc — commit được.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.giao_dien import bang_admin, loc_bang_admin                 # noqa: E402
from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh        # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header        # noqa: E402
from src.version import in_phien_ban                                 # noqa: E402

GHI_CHU = "Nghiệm thu 5.6 — ghi chú thử của Admin"


def cham(*, so_dong: int, so_baseline: int, so_lan_sua_max: int, co_dau_vao: int,
         so_c4: int, da_tham_dinh_lai: bool, doc_lai: list[dict],
         luu_lai: dict | None, ma_nguoi_thuong: int | None,
         ma_khong_danh_tinh: int | None, ten_gui: str) -> list[dict]:
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    ghi("A1", so_dong == so_baseline and so_dong > 0,
        f"{so_dong} dòng bảng / {so_baseline} dòng baseline · cột «Lần sửa 1…"
        f"{so_lan_sua_max}»")
    ghi("A2", (co_dau_vao > 0) if da_tham_dinh_lai else None,
        f"{co_dau_vao}/{so_c4} dòng do C4 kết luận có giá trị đầu vào"
        + ("" if da_tham_dinh_lai else " (chưa thẩm định lại trên bản 5.6 — chỉ đo)"))

    ok = [x for x in doc_lai if (x.get("ghi_chu_admin") or {}).get("ghi_chu") == GHI_CHU]
    dung = all((x["ghi_chu_admin"].get("ten") == ten_gui
                and x["ghi_chu_admin"].get("vai") == "admin"
                and x["ghi_chu_admin"].get("danh_gia") == "can_ban"
                and x["ghi_chu_admin"].get("loi_o_phia") == "he_thong_ai") for x in ok)
    ghi("A3", len(ok) == 2 and dung,
        f"{len(ok)}/2 dòng đọc lại đúng ghi chú, tên+vai+hai cột chọn đúng: {dung}")
    ghi("A4", ma_nguoi_thuong == 403 and ma_khong_danh_tinh == 400,
        f"vai người làm sizing → HTTP {ma_nguoi_thuong} · không danh tính → "
        f"HTTP {ma_khong_danh_tinh}")
    ghi("A5", (luu_lai or {}).get("da_luu") == 0 and (luu_lai or {}).get("bo_qua") == 2,
        f"lưu lại y nguyên → {luu_lai}")
    return kq


def _ma_http(dia_chi: str, ho_so: int, fb: int, header: dict | None) -> int | None:
    import urllib.error
    import urllib.request
    than = json.dumps({"muc": [{"finding_baseline_id": fb, "ghi_chu": "thử"}]})
    req = urllib.request.Request(
        f"{dia_chi}/ho-so/{ho_so}/ghi-chu-admin", method="POST",
        data=than.encode("utf-8"),
        headers={"Content-Type": "application/json", **(header or {})})
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
    ap.add_argument("docx", nargs="?", help="thẩm định lại trước để có cột đầu vào code")
    ap.add_argument("--ho-so", type=int, required=True)
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.6")
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.6")

    admin = tao_danh_tinh("admin", a.ten)
    kh = KhachAPI(a.api, timeout=120, danh_tinh=admin)
    sk = kh.suc_khoe()
    csdl = (sk.tho or {}).get("csdl") or {}
    if not sk.song or not csdl.get("san_sang"):
        print(f"✗ Dịch vụ hoặc CSDL chưa sẵn sàng: {sk.thong_diep or csdl}")
        return 2
    print(f"dịch vụ: commit {sk.commit} · lược đồ {csdl.get('luoc_do')!r}")

    try:
        if a.docx:
            p = pathlib.Path(a.docx)
            print(f"\nThẩm định lại hồ sơ #{a.ho_so} bằng «{p.name}» (dùng lại câu trả "
                  "lời model của lần trước)")
            v = _cho(kh, kh.nop(p.read_bytes(), p.name, song_song=12,
                                ho_so_id=a.ho_so)["ma"])
            print(f"  dùng lại: {v.get('phat_lai') or '—'}")
            if v["trang_thai"] != "xong":
                print(f"✗ Việc không xong: {v.get('loi')}")
                return 2

        d = kh.bang_admin(a.ho_so)
        dong = d.get("baseline") or []
        rows = bang_admin(d)
        c4 = [b for b in dong if b.get("ket_luan_boi") == "c4"]
        co_dau_vao = [b for b in c4 if (b.get("dau_vao_lan") or "").strip()]
        muc = [{"finding_baseline_id": b["id"], "ghi_chu": GHI_CHU,
                "danh_gia": "can_ban", "loi_o_phia": "he_thong_ai"}
               for b in dong[:2]]
        lan_1 = kh.ghi_chu_admin(a.ho_so, muc)
        print(f"  ghi ba cột: {lan_1}")
        lan_2 = kh.ghi_chu_admin(a.ho_so, muc)
        doc_lai = (kh.bang_admin(a.ho_so).get("baseline") or [])[:2]
        nguoi = thanh_header(tao_danh_tinh("nguoi_lam_sizing", a.ten))
        ma_403 = _ma_http(kh.dia_chi, a.ho_so, dong[0]["id"], nguoi)
        ma_400 = _ma_http(kh.dia_chi, a.ho_so, dong[0]["id"], None)
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = cham(so_dong=len(rows), so_baseline=len(dong),
              so_lan_sua_max=int(d.get("so_lan_sua_max") or 0),
              co_dau_vao=len(co_dau_vao), so_c4=len(c4), da_tham_dinh_lai=bool(a.docx),
              doc_lai=doc_lai, luu_lai=lan_2, ma_nguoi_thuong=ma_403,
              ma_khong_danh_tinh=ma_400, ten_gui=admin.ten)

    tt = collections.Counter(b.get("trang_thai") for b in dong)
    _, an = loc_bang_admin(rows)
    kq.append({"ma": "Đ1", "dat": None,
               "chi_tiet": f"trạng thái {dict(tt)} · bộ lọc mặc định ẩn {an}/{len(rows)} "
                           f"dòng · {len(co_dau_vao)}/{len(c4)} dòng C4 có đầu vào"})
    print()
    for k in kq:
        print(f"  {({True: '✓', False: '✗', None: '·'})[k['dat']]} {k['ma']}  {k['chi_tiet']}")
    hong = [k["ma"] for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.6/5.9: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.6/5.9: CHƯA ĐẠT ({', '.join(hong)})"))

    ra = pathlib.Path(f"docs/nghiem-thu-5.6-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "ho_so_id": a.ho_so, "commit": sk.commit, "so_dong": len(rows),
        "so_lan_sua_max": d.get("so_lan_sua_max"), "trang_thai": dict(tt),
        "so_dong_an_mac_dinh": an, "tieu_chi": kq}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"\n✓ Kết quả: {ra} — gửi lại file này.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
