#!/usr/bin/env python
"""Nghiệm thu 5.4 trên máy nội bộ — nút «Báo lỗi hệ thống» + nâng lược đồ lên bản 3.

    py scripts/nghiem_thu_5_4.py --ho-so 1 --api http://localhost:8902 --ten "Tên bạn"

Không gọi model, không nộp tài liệu — chạy vài giây.

Việc đáng lo nhất của mục này KHÔNG phải cái nút, mà là **migration**: máy nội bộ đang
giữ hồ sơ thật (6 lần thẩm định, 719 dòng baseline) trên lược đồ bản 2, và 5.4 đổi hình
dạng bảng `bao_cao_loi`. Copilot tự nâng lên bản 3 lúc khởi động; script kiểm dữ liệu cũ
còn nguyên vẹn sau đó.

## Tiêu chí (đặt trước)

- **B1** `/health` báo CSDL sẵn sàng và lược đồ đã lên bản 3.                   (cứng)
- **B2** Hồ sơ cũ đọc lại được ĐỦ: baseline, các lần, rổ phát sinh.             (cứng)
- **B3** Báo được một dòng BASELINE; đọc lại thấy đúng người báo và lý do.      (cứng)
- **B4** Báo được một dòng trong RỔ PHÁT SINH — chỗ «phân hệ ma» của 5.3 đổ vào. (cứng)
- **B5** Lời báo vào cả nhật ký phản hồi 4.1 (`bao_sai`), một dataset duy nhất.  (cứng)
- **B6** Thiếu danh tính → HTTP 400.                                            (cứng)
- **Đ1** Số lời báo hiện có của hồ sơ, và số dòng hai rổ.

⚠️ Script GHI hai lời báo thật vào hồ sơ. Dùng hồ sơ nghiệm thu (vd #1).

Kết quả chỉ chứa số đếm và mã quy tắc — commit được.
"""
from __future__ import annotations

import argparse
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

LUOC_DO_CAN = "3"


def cham(*, luoc_do: str, san_sang: bool, so_baseline: int, so_lan: int,
         so_phat_sinh: int, bao_baseline: dict | None, bao_phat_sinh: dict | None,
         doc_lai: list[dict], ten_gui: str, ma_khong_danh_tinh: int | None) -> list[dict]:
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    ghi("B1", san_sang and luoc_do == LUOC_DO_CAN,
        f"CSDL sẵn sàng: {san_sang} · lược đồ trong CSDL: {luoc_do!r} (cần {LUOC_DO_CAN!r})")
    ghi("B2", so_baseline > 0 and so_lan > 0,
        f"hồ sơ cũ: {so_baseline} dòng baseline · {so_lan} lần · {so_phat_sinh} dòng "
        "phát sinh ở lần mới nhất")

    b = bao_baseline or {}
    ghi("B3", bool(b.get("id")) and b.get("nguon") == "baseline",
        f"báo dòng baseline → {b or 'KHÔNG gửi được'}")
    p = bao_phat_sinh or {}
    ghi("B4", bool(p.get("id")) and p.get("nguon") == "phát sinh",
        f"báo dòng phát sinh → {p or 'KHÔNG gửi được (hồ sơ không có dòng phát sinh?)'}")

    cua_ta = [x for x in doc_lai if x.get("id") in {b.get("id"), p.get("id")}]
    dung_ten = all(x.get("ten") == ten_gui for x in cua_ta)
    ghi("B5", len(cua_ta) == len([x for x in (b, p) if x.get("id")]) and dung_ten
        and str(b.get("nhat_ky", "")).startswith("đã ghi"),
        f"đọc lại {len(cua_ta)} lời báo, tên lưu đúng: {dung_ten} · nhật ký 4.1: "
        f"«{b.get('nhat_ky')}»")
    ghi("B6", ma_khong_danh_tinh == 400, f"không danh tính → HTTP {ma_khong_danh_tinh}")
    ghi("Đ1", None, f"hồ sơ có {len(doc_lai)} lời báo sau lượt nghiệm thu này")
    return kq


def _ma_http_khong_danh_tinh(dia_chi: str, ho_so: int, fb: int) -> int | None:
    """Gọi thẳng, không qua `KhachAPI` (vốn luôn gắn danh tính)."""
    req = urllib.request.Request(
        f"{dia_chi}/ho-so/{ho_so}/bao-loi", method="POST",
        data=json.dumps({"ly_do": "thử không danh tính",
                         "finding_baseline_id": fb}).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    mo = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with mo.open(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ho-so", type=int, required=True)
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.4")
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.4")

    dt = tao_danh_tinh("nguoi_lam_sizing", a.ten)
    kh = KhachAPI(a.api, timeout=60, danh_tinh=dt)
    sk = kh.suc_khoe()
    csdl = (sk.tho or {}).get("csdl") or {}
    if not sk.song:
        print(f"✗ Dịch vụ chưa sẵn sàng: {sk.thong_diep}")
        return 2
    print(f"dịch vụ: commit {sk.commit} · lược đồ CSDL: {csdl.get('luoc_do')!r}")

    try:
        hs = kh.ho_so(a.ho_so)
        baseline = hs.get("baseline") or []
        phat_sinh = hs.get("phat_sinh") or []
        b = p = None
        if baseline:
            b = kh.bao_loi(a.ho_so, "Nghiệm thu 5.4 — dòng này sửa rồi vẫn bị báo",
                           finding_baseline_id=baseline[0]["id"])
            print(f"  báo baseline: {b}")
        if phat_sinh:
            p = kh.bao_loi(a.ho_so, "Nghiệm thu 5.4 — dòng phát sinh này vô lý",
                           finding_phat_sinh_id=phat_sinh[0]["id"])
            print(f"  báo phát sinh: {p}")
        doc_lai = kh.ds_bao_loi(a.ho_so)
        ma_400 = _ma_http_khong_danh_tinh(kh.dia_chi, a.ho_so,
                                          baseline[0]["id"] if baseline else 1)
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = cham(luoc_do=str(csdl.get("luoc_do") or ""), san_sang=bool(csdl.get("san_sang")),
              so_baseline=len(baseline), so_lan=len(hs.get("cac_lan") or []),
              so_phat_sinh=len(phat_sinh), bao_baseline=b, bao_phat_sinh=p,
              doc_lai=doc_lai, ten_gui=dt.ten, ma_khong_danh_tinh=ma_400)
    print()
    for k in kq:
        print(f"  {({True: '✓', False: '✗', None: '·'})[k['dat']]} {k['ma']}  {k['chi_tiet']}")
    hong = [k["ma"] for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.4: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.4: CHƯA ĐẠT ({', '.join(hong)})"))

    ra = pathlib.Path(f"docs/nghiem-thu-5.4-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "ho_so_id": a.ho_so, "commit": sk.commit, "luoc_do": csdl.get("luoc_do"),
        "so_baseline": len(baseline), "so_lan": len(hs.get("cac_lan") or []),
        "so_phat_sinh": len(phat_sinh), "tieu_chi": kq},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Kết quả: {ra} — gửi lại file này.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
