#!/usr/bin/env python
"""Nghiệm thu 5.9 bước 2 — đề xuất sửa quy tắc, kiểm tự động, người chốt mới áp.

    py scripts/nghiem_thu_5_9.py --ho-so 1 --api http://localhost:8902 --ten "Tên bạn"

KHÔNG cần model, KHÔNG chạy thẩm định — chỉ vài giây. Script KHÔNG sửa
`config/rules.yaml`: nó chỉ ghi đề xuất vào CSDL rồi đọc lại.

## Tiêu chí (đặt trước)

- **B1** Xem được quy tắc mà hồ sơ đang tham chiếu, kèm NGUYÊN VĂN khối YAML
         (còn chú thích) và lý do C4 không chấm được, nếu có.               (cứng)
- **B2** Sửa hợp lệ → kiểm ĐẠT, nêu đúng số quy tắc / số biểu thức, và nói
         thẳng là CHƯA đo eval.                                             (cứng)
- **B3** Sửa hỏng (đổi mã quy tắc; gõ `&&` thay `and`) → kiểm CHẶN, nói rõ
         vì sao. Đây là thứ giữ cho một lần sửa sai không chạy trên mọi hồ sơ. (cứng)
- **B4** Gửi đề xuất → lưu kèm người đề xuất, lý do, khối cũ và kết quả kiểm. (cứng)
- **B5** Vai «người làm sizing» đề xuất → HTTP 403; không danh tính → 400.   (cứng)
- **B6** Đánh dấu «đã áp» khi file CHƯA đổi → HTTP 409, trạng thái giữ nguyên.
         Công cụ không tự ghi `rules.yaml` nhưng nó ĐỌC được, nên không cho
         ghi một điều sai vào lịch sử quyết định (NT4).                      (cứng)
- **Đ1** `rules.yaml` trong container có phải bản gắn từ máy chủ không: đổi một
         dòng trên máy chủ rồi đọc lại qua API, KHÔNG dựng lại image.        (đo tay)

⚠️ Script GHI hai đề xuất thật vào CSDL (một đạt, một hỏng). Chúng không đụng tới
bộ quy tắc đang chạy.

Kết quả chỉ chứa số đếm, mã quy tắc và mã HTTP — commit được.
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

from src.giao_dien import ma_quy_tac_trong_ho_so, tom_tat_kiem_de_xuat  # noqa: E402
from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh        # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header        # noqa: E402
from src.version import in_phien_ban                                 # noqa: E402

LY_DO = "Nghiệm thu 5.9 bước 2 — đề xuất thử, KHÔNG áp"


def cham(*, q: dict, kiem_dat: dict, kiem_doi_ma: dict, kiem_cu_phap: dict,
         da_luu: dict | None, ma_nguoi_thuong: int | None,
         ma_khong_danh_tinh: int | None, ma_danh_dau_som: int | None,
         trang_thai_sau: str, ten_gui: str) -> list[dict]:
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    khoi = q.get("khoi") or ""
    # Khối phải là NGUYÊN VĂN, không phải `yaml.dump` lại: dump lại là mất hết chú
    # thích, mà chú thích chính là phần người nghiệp vụ đọc để biết quy tắc từ đâu ra.
    ghi("B1", khoi.startswith(f"  - id: {q.get('id')}\n") and len(khoi.splitlines()) > 3
        and bool(q.get("duong_dan")),
        f"khối {len(khoi.splitlines())} dòng cho `{q.get('id')}` · "
        + ("C4 chấm được" if not q.get("khong_danh_gia_duoc")
           else f"không chấm được: {q['khong_danh_gia_duoc'][:60]}"))
    ghi("B2", bool(kiem_dat.get("dat")) and kiem_dat.get("so_bieu_thuc", 0) > 0,
        tom_tat_kiem_de_xuat(kiem_dat))
    ghi("B3",
        not kiem_doi_ma.get("dat") and not kiem_cu_phap.get("dat")
        and any("rule_ref" in x for x in kiem_doi_ma.get("loi") or [])
        and any("phân tích" in x for x in kiem_cu_phap.get("loi") or []),
        f"đổi mã → {(kiem_doi_ma.get('loi') or [''])[0][:70]} | "
        f"sai cú pháp → {(kiem_cu_phap.get('loi') or [''])[0][:70]}")
    d = da_luu or {}
    ghi("B4",
        d.get("ten") == ten_gui and d.get("vai") == "admin"
        and d.get("ly_do") == LY_DO and bool(d.get("noi_dung_cu"))
        and d.get("trang_thai") == "kiem_dat",
        f"đề xuất #{d.get('id')} · {d.get('ten')}/{d.get('vai')} · trạng thái "
        f"{d.get('trang_thai')} · khối cũ {len((d.get('noi_dung_cu') or '').splitlines())} dòng"
        f" · eval: {d.get('bang_chung_eval') or 'chưa ai đo'}")
    ghi("B5", ma_nguoi_thuong == 403 and ma_khong_danh_tinh == 400,
        f"vai người làm sizing → HTTP {ma_nguoi_thuong} · không danh tính → "
        f"HTTP {ma_khong_danh_tinh}")
    ghi("B6", ma_danh_dau_som == 409 and trang_thai_sau == "kiem_dat",
        f"đánh dấu «đã áp» khi file chưa đổi → HTTP {ma_danh_dau_som} · "
        f"trạng thái vẫn là {trang_thai_sau!r}")
    return kq


def _ma_http(dia_chi: str, duong: str, than: dict, header: dict | None) -> int | None:
    req = urllib.request.Request(
        f"{dia_chi}{duong}", method="POST",
        data=json.dumps(than, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8", **(header or {})})
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
    ap.add_argument("--quy-tac", default="",
                    help="mã quy tắc để thử; mặc định lấy quy tắc báo nhiều nhất")
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.9")
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.9 bước 2")

    admin = tao_danh_tinh("admin", a.ten)
    kh = KhachAPI(a.api, timeout=120, danh_tinh=admin)
    sk = kh.suc_khoe()
    csdl = (sk.tho or {}).get("csdl") or {}
    if not sk.song or not csdl.get("san_sang"):
        print(f"✗ Dịch vụ hoặc CSDL chưa sẵn sàng: {sk.thong_diep or csdl}")
        return 2
    print(f"dịch vụ: commit {sk.commit} · lược đồ {csdl.get('luoc_do')!r}")
    if str(csdl.get("luoc_do")) != "4":
        print("  ⚠ lược đồ chưa lên bản 4 — `de_xuat_quy_tac` còn thiếu cột. "
              "Khởi động lại dịch vụ `copilot` để chạy nâng cấp.")

    try:
        ds_ma = ma_quy_tac_trong_ho_so(kh.bang_admin(a.ho_so))
        ma = a.quy_tac or (ds_ma[0] if ds_ma else "")
        if not ma:
            print(f"✗ Hồ sơ #{a.ho_so} không có dòng nào gắn mã quy tắc.")
            return 2
        print(f"quy tắc thử: `{ma}` (hồ sơ tham chiếu {len(ds_ma)} mã khác nhau)")
        q = kh.quy_tac(ma)
        khoi = q["khoi"]

        # B2 — một sửa đổi hợp lệ, không đụng tới ngưỡng: thêm một dòng `note`.
        hop_le = khoi.rstrip("\n") + "\n    confidence_floor: cao\n"
        kiem_dat = kh.kiem_quy_tac(ma, hop_le)
        # B3 — hai kiểu sai khác hẳn nhau.
        doi_ma = khoi.replace(f"- id: {ma}", f"- id: {ma}-moi", 1)
        kiem_doi_ma = kh.kiem_quy_tac(ma, doi_ma)
        cu_phap = khoi.replace(" and ", " && ", 1)
        if cu_phap == khoi:      # quy tắc không có `and`: bẻ ngoặc cho hỏng cú pháp
            cu_phap = khoi.replace("check: \"", "check: \"(", 1)
        kiem_cu_phap = kh.kiem_quy_tac(ma, cu_phap)

        # B4 — gửi thật.
        r = kh.de_xuat_quy_tac(ma, hop_le, ly_do=LY_DO, ho_so_id=a.ho_so)
        dx_id = r["de_xuat"]["id"]
        da_luu = next((x for x in kh.ds_de_xuat(rule_ref=ma) if x["id"] == dx_id), None)

        # B5 / B6.
        nguoi = thanh_header(tao_danh_tinh("nguoi_lam_sizing", a.ten))
        than = {"noi_dung_moi": hop_le, "ly_do": "thử vai"}
        ma_403 = _ma_http(kh.dia_chi, f"/quy-tac/{ma}/de-xuat", than, nguoi)
        ma_400 = _ma_http(kh.dia_chi, f"/quy-tac/{ma}/de-xuat", than, None)
        ma_409 = _ma_http(kh.dia_chi, f"/de-xuat/{dx_id}/trang-thai",
                          {"trang_thai": "da_ap"}, thanh_header(admin))
        sau = next((x["trang_thai"] for x in kh.ds_de_xuat(rule_ref=ma)
                    if x["id"] == dx_id), "")
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = cham(q=q, kiem_dat=kiem_dat, kiem_doi_ma=kiem_doi_ma,
              kiem_cu_phap=kiem_cu_phap, da_luu=da_luu, ma_nguoi_thuong=ma_403,
              ma_khong_danh_tinh=ma_400, ma_danh_dau_som=ma_409,
              trang_thai_sau=sau, ten_gui=admin.ten)
    kq.append({"ma": "Đ1", "dat": None,
               "chi_tiet": f"bộ quy tắc API đang đọc: `{q.get('duong_dan')}` · "
                           f"{kiem_dat.get('so_quy_tac')} quy tắc · "
                           f"{kiem_dat.get('so_bieu_thuc')} biểu thức · C4 chạy được "
                           f"{kiem_dat.get('chay_duoc_truoc')}"})
    print()
    for k in kq:
        print(f"  {({True: '✓', False: '✗', None: '·'})[k['dat']]} {k['ma']}  "
              f"{k['chi_tiet']}")
    hong = [k["ma"] for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.9 bước 2: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.9 bước 2: CHƯA ĐẠT ({', '.join(hong)})"))
    print(f"\nĐã ghi đề xuất #{da_luu and da_luu.get('id')} vào CSDL. Bộ quy tắc "
          "KHÔNG bị đụng tới — kiểm bằng `git diff config/rules.yaml` trên máy chủ.")

    ra = pathlib.Path(f"docs/nghiem-thu-5.9-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "ho_so_id": a.ho_so, "commit": sk.commit, "luoc_do": csdl.get("luoc_do"),
        "quy_tac": ma, "so_ma_quy_tac_trong_ho_so": len(ds_ma),
        "so_quy_tac": kiem_dat.get("so_quy_tac"),
        "so_bieu_thuc": kiem_dat.get("so_bieu_thuc"),
        "chay_duoc": kiem_dat.get("chay_duoc_truoc"),
        "tieu_chi": kq}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Kết quả: {ra} — gửi lại file này.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
