#!/usr/bin/env python
"""Nghiệm thu 5.1 trên máy nội bộ — baseline cố định + rổ lỗi phát sinh.

    py scripts/nghiem_thu_5_1.py "<file.docx>" --api http://localhost:8902 --ten "Tên bạn"
    py scripts/nghiem_thu_5_1.py "<file.docx>" --ho-so 3 ...   # bỏ lần 1, dùng hồ sơ có sẵn

Nộp CÙNG một tài liệu hai lần qua API: lần 1 tạo hồ sơ và đóng băng baseline, lần
2 thẩm định lại hồ sơ đó. Rồi kiểm các tiêu chí ĐẶT TRƯỚC dưới đây và ghi kết quả
ra `docs/nghiem-thu-5.1-<thời gian>.md` + `.json`.

## Tiêu chí (đặt trước khi chạy — không chỉnh sau khi thấy số)

- **K1** Số lỗi baseline sau lần 2 BẰNG sau lần 1.                       (cứng)
- **K2** Lần 2 có số thứ tự 2.                                          (cứng)
- **K3** Mọi dòng baseline có trạng thái ở lần 2: đạt + chưa đạt +
         chưa kiểm được = số lỗi baseline.                              (cứng)
- **K4** Số dòng baseline = số finding lần 1 xuất ra (không rơi dòng).  (cứng)
- **K5** Tên người nộp lưu nguyên vẹn (tiếng Việt qua header).          (cứng)
- **K6** Nhiễu nền — tuỳ lần 2 có gọi model thật hay không:
         · lần 2 PHÁT LẠI hoàn toàn từ đệm → đạt = 0 VÀ phát sinh = 0, chính xác;
         · lần 2 gọi model thật → đạt ≤ 3% VÀ phát sinh ≤ 3% số lỗi baseline
           (5.0b đo ~1,4% mỗi phía; 3% là biên gấp đôi).

## Nên để đệm BẬT (mặc định)

Lần 1 gọi model thật (~22 phút) và nạp đệm; lần 2 phát lại (vài phút). K6 khi đó là
phép kiểm CHÍNH XÁC của đường ống: cùng đầu vào thì không được có dòng «đạt» hay
«phát sinh» nào — có là lỗi code, không phải nhiễu model. Muốn đo cả nhiễu thật thì
tắt đệm (`SIZING_COPILOT_KHONG_CACHE=1`) trước lần 2, tốn thêm ~22 phút.

Kết quả chỉ chứa SỐ ĐẾM và mã quy tắc + tên phân hệ — không có nội dung tài liệu,
commit được.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh   # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh                 # noqa: E402
from src.version import in_phien_ban                            # noqa: E402

NGUONG_NHIEU = 0.03


def phat_lai_hoan_toan(viec: dict) -> bool | None:
    """True = không gọi model lần nào (đệm bật, không ghi thêm bản ghi đệm nào).
    None = không biết (image cũ không ghi `thong_ke_cache`)."""
    tk = viec.get("thong_ke_cache") or {}
    if not tk:
        return None
    return bool(tk.get("bat")) and int(tk.get("ghi_them") or 0) == 0


def danh_gia(*, lan1: dict | None, ho_so_1: dict | None, so_finding_1: int | None,
             viec_2: dict, ho_so_2: dict, ten: str) -> list[dict]:
    """Chấm các tiêu chí. `lan1`/`ho_so_1`/`so_finding_1` = None khi bỏ lần 1."""
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    n2 = ho_so_2.get("so_loi_baseline", 0)
    lan2 = (ho_so_2.get("cac_lan") or [{}])[-1]
    dem = lan2.get("dem") or {}

    if ho_so_1 is not None:
        n1 = ho_so_1.get("so_loi_baseline", 0)
        ghi("K1", n1 == n2, f"baseline lần 1 = {n1}, sau lần 2 = {n2}")
    else:
        ghi("K1", None, "bỏ lần 1 (--ho-so) — không so được")

    so = lan2.get("so_thu_tu")
    ghi("K2", so == 2 if ho_so_1 is not None else None, f"số thứ tự lần mới nhất = {so}")

    tong = dem.get("dat", 0) + dem.get("chua_dat", 0) + dem.get("chua_kiem_duoc", 0)
    ghi("K3", tong == n2, f"đạt {dem.get('dat', 0)} + chưa đạt {dem.get('chua_dat', 0)}"
                          f" + chưa kiểm được {dem.get('chua_kiem_duoc', 0)} = {tong}"
                          f" / baseline {n2}")

    if so_finding_1 is not None and ho_so_1 is not None:
        ghi("K4", so_finding_1 == ho_so_1.get("so_loi_baseline"),
            f"lần 1 xuất {so_finding_1} finding, baseline có "
            f"{ho_so_1.get('so_loi_baseline')} dòng")
    else:
        ghi("K4", None, "bỏ lần 1 — không so được")

    ghi("K5", lan2.get("ten") == ten, f"tên lưu: «{lan2.get('ten')}» — gửi: «{ten}»")

    dat, ps = dem.get("dat", 0), dem.get("phat_sinh", 0)
    replay = phat_lai_hoan_toan(viec_2)
    if replay is None:
        ghi("K6", None, "không biết lần 2 có gọi model không (thiếu thong_ke_cache)")
    elif replay:
        ghi("K6", dat == 0 and ps == 0,
            f"lần 2 PHÁT LẠI từ đệm → phải đạt = 0 và phát sinh = 0; thực tế đạt {dat},"
            f" phát sinh {ps}")
    else:
        tl_dat, tl_ps = (dat / n2, ps / n2) if n2 else (0.0, 0.0)
        ghi("K6", tl_dat <= NGUONG_NHIEU and tl_ps <= NGUONG_NHIEU,
            f"lần 2 gọi model thật → đạt {dat} ({tl_dat:.1%}), phát sinh {ps} "
            f"({tl_ps:.1%}); ngưỡng {NGUONG_NHIEU:.0%} mỗi phía")
    return kq


def _cho(kh: KhachAPI, ma: str, giay_hoi: int) -> dict:
    truoc = ""
    while True:
        d = kh.viec(ma)
        dong = (f"{d['trang_thai']} · {d.get('giai_doan') or '…'} "
                f"{d.get('da_xong', 0)}/{d.get('tong', 0)} · {d.get('giay_da_chay', 0):.0f}s")
        if dong != truoc:
            print("  " + dong)
            truoc = dong
        if d["trang_thai"] in ("xong", "hong", "gian_doan"):
            return d
        time.sleep(giay_hoi)


def _nop(kh: KhachAPI, p: pathlib.Path, ho_so_id: int | None, giay_hoi: int) -> dict:
    d = kh.nop(p.read_bytes(), p.name, song_song=12,
               ho_so_id="" if ho_so_id is None else ho_so_id)
    print(f"  mã việc {d['ma']}")
    v = _cho(kh, d["ma"], giay_hoi)
    if v["trang_thai"] != "xong":
        sys.exit(f"✗ Việc {d['ma']} không xong: {v.get('loi')}")
    print(f"  ghi hồ sơ: {v.get('ghi_ho_so') or '(trống)'}")
    if not v.get("ho_so_id"):
        sys.exit("✗ Việc xong nhưng KHÔNG ghi được hồ sơ — xem dòng «ghi hồ sơ» ở trên.")
    return v


def _vi_du(ho_so: dict) -> dict:
    return {
        "dat": [f"{b.get('rule_ref')}#{b.get('scope_goc')}"
                for b in ho_so.get("baseline") or [] if b.get("trang_thai") == "dat"][:15],
        "phat_sinh": [f"{p.get('rule_ref')}#{p.get('scope_goc')}"
                      for p in ho_so.get("phat_sinh") or []][:15],
    }


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docx")
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.1")
    ap.add_argument("--vai", default="nguoi_lam_sizing")
    ap.add_argument("--ho-so", type=int, default=None, help="bỏ lần 1, dùng hồ sơ này")
    ap.add_argument("--giay-hoi", type=int, default=15)
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.1")

    p = pathlib.Path(a.docx)
    if not p.is_file():
        print(f"✗ Không thấy file: {p}")
        return 2
    dt = tao_danh_tinh(a.vai, a.ten)
    kh = KhachAPI(a.api, timeout=60, danh_tinh=dt)

    sk = kh.suc_khoe()
    if not sk.song:
        print(f"✗ Không gọi được dịch vụ tại {kh.dia_chi}: {sk.thong_diep}")
        return 2
    csdl = (sk.tho or {}).get("csdl") or {}
    print(f"dịch vụ: commit {sk.commit} · model {'CÓ' if sk.model_san_sang else 'CHƯA'} · "
          f"đệm {'BẬT' if (sk.tho or {}).get('cache_bat') else 'TẮT'} · "
          f"CSDL {'SẴN SÀNG' if csdl.get('san_sang') else 'CHƯA'}")
    if not csdl.get("san_sang"):
        print(f"✗ CSDL chưa sẵn sàng: {csdl.get('thong_diep') or 'image cũ, không có khoá csdl'}")
        print("  Bật theo 3 bước trong .env.example, rồi: docker compose up -d copilot")
        return 2
    if not sk.model_san_sang:
        print(f"✗ Model chưa sẵn sàng: {sk.ghi_chu_model}")
        return 2

    ho_so_1 = so_finding_1 = viec_1 = None
    ho_so_id = a.ho_so
    try:
        if ho_so_id is None:
            print("\nLần 1 — hồ sơ mới (đệm bật: ~22 phút gọi model thật)")
            viec_1 = _nop(kh, p, None, a.giay_hoi)
            ho_so_id = viec_1["ho_so_id"]
            ho_so_1 = kh.ho_so(ho_so_id)
            so_finding_1 = len(kh.findings(viec_1["ma"]).get("findings") or [])
            print(f"  hồ sơ #{ho_so_id}: baseline {ho_so_1['so_loi_baseline']} lỗi · "
                  f"finding xuất ra {so_finding_1}")

        print(f"\nLần 2 — thẩm định lại hồ sơ #{ho_so_id}")
        viec_2 = _nop(kh, p, ho_so_id, a.giay_hoi)
        ho_so_2 = kh.ho_so(ho_so_id)
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = danh_gia(lan1=viec_1, ho_so_1=ho_so_1, so_finding_1=so_finding_1,
                  viec_2=viec_2, ho_so_2=ho_so_2, ten=dt.ten)
    print()
    for k in kq:
        dau = {True: "✓", False: "✗", None: "–"}[k["dat"]]
        print(f"  {dau} {k['ma']}  {k['chi_tiet']}")
    hong = [k for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.1: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.1: CHƯA ĐẠT ({', '.join(k['ma'] for k in hong)})"))

    ra = pathlib.Path(f"docs/nghiem-thu-5.1-{time.strftime('%Y%m%d-%H%M%S')}.md")
    ra.parent.mkdir(parents=True, exist_ok=True)
    vd = _vi_du(ho_so_2)
    dong = [f"# Nghiệm thu 5.1 — {time.strftime('%Y-%m-%d %H:%M')}", "",
            f"**{'ĐẠT' if not hong else 'CHƯA ĐẠT'}** · dịch vụ commit `{sk.commit}` · "
            f"hồ sơ #{ho_so_id} · tệp `{p.name}`", "",
            "| Tiêu chí | Kết quả | Chi tiết |", "|---|---|---|"]
    dong += [f"| {k['ma']} | {({True: '✓', False: '✗', None: '–'})[k['dat']]} | "
             f"{k['chi_tiet']} |" for k in kq]
    dong += ["", "| | Lần 1 | Lần 2 |", "|---|---|---|",
             f"| Mã việc | `{(viec_1 or {}).get('ma', '—')}` | `{viec_2['ma']}` |",
             f"| Phút | {((viec_1 or {}).get('giay_da_chay') or 0) / 60:.1f} | "
             f"{(viec_2.get('giay_da_chay') or 0) / 60:.1f} |",
             f"| Đệm | `{(viec_1 or {}).get('thong_ke_cache')}` | "
             f"`{viec_2.get('thong_ke_cache')}` |", "",
             f"Ví dụ «đạt»: {', '.join(vd['dat']) or '—'}", "",
             f"Ví dụ «phát sinh»: {', '.join(vd['phat_sinh']) or '—'}", ""]
    ra.write_text("\n".join(dong), encoding="utf-8")
    ra.with_suffix(".json").write_text(json.dumps({
        "ho_so_id": ho_so_id, "tieu_chi": kq,
        "lan_2": (ho_so_2.get("cac_lan") or [{}])[-1].get("dem"),
        "so_loi_baseline": ho_so_2.get("so_loi_baseline"),
        "dem_1": (ho_so_1 or {}).get("so_loi_baseline"),
        "cache_lan_2": viec_2.get("thong_ke_cache"), "vi_du": vd,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Kết quả: {ra}  (+ .json) — chỉ số đếm và mã quy tắc, gửi cả hai file.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
