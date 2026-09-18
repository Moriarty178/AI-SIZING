#!/usr/bin/env python
"""Nghiệm thu 5.3 trên máy nội bộ — thẩm định lại chỉ hỏi model cho phần đã đổi.

    py scripts/nghiem_thu_5_3.py --ho-so 1 "<bản gốc.docx>" "<bản đã sửa.docx>" --api http://localhost:8902 --ten "Tên bạn"

`<bản đã sửa.docx>`: mở bản gốc bằng Word, sửa MỘT con số trong bảng của MỘT phân hệ
(ghi lại phân hệ nào), thêm MỘT câu vào đầu mục của phân hệ đó, rồi «Save As» sang tên
khác. Câu thêm vào làm lệch chỉ số và có thể cả số trang của mọi phần tử phía sau —
đúng ca công cụ phải vẫn dùng lại được cho các phân hệ khác.

Ba lần thẩm định lại liền nhau trên cùng hồ sơ:

- **L1** bản gốc — tạo bản ghi câu trả lời model (lần mới nhất hiện có của hồ sơ chạy
  trước bản 5.3 nên chưa có bản ghi: L1 chạy toàn bộ, đệm lời gọi bật thì vài phút).
- **L2** bản gốc lần nữa — mọi lượt hỏi phải lấy lại từ L1.
- **L3** bản đã sửa — chỉ lượt hỏi đọc tới chỗ sửa mới tới model.

## Tiêu chí (đặt trước)

- **R1** L2 báo tài liệu giống hệt lần trước.                                   (cứng)
- **R2** L2 dùng lại được bản ghi của L1, và không lượt hỏi nào tới model ngoài
         những lượt đã HỎNG ở L1 (lượt hỏng không được ghi, nên phải hỏi lại).  (cứng)
- **R3** L2 không hỏi lại lượt nào ⇒ kết quả trùng L1 TUYỆT ĐỐI: cùng số finding,
         cùng đạt / chưa đạt / chưa kiểm được / phát sinh.                      (cứng)
- **R4** L3 thấy bản sửa khác bản gốc, và nói ra chỗ khác.                       (cứng)
- **R5** L3 dùng lại được MỘT PHẦN C3 — hỏi lại có chọn lọc, không phải hỏi hết. (cứng)
- **R6** L3 dùng lại được C5 của phân hệ KHÔNG bị sửa (chốt 2026-09-18). Chỉ đo
         nếu phần chung đổi — lúc đó mọi quy tắc C5 hỏi lại là đúng.            (cứng)
- **Đ1** Thời gian và số lượt thật sự tới model của từng lần.
- **Đ2** Phân hệ nào có nội dung đổi; phần chung có đổi không.
- **Đ3** C5 dùng lại được bao nhiêu, và những phân hệ nào phải hỏi lại.
- **Đ4** Dòng baseline đổi trạng thái giữa L2 và L3, chia theo nằm trong / ngoài
         phân hệ có nội dung đổi, và theo ai kết luận (C4 / C5 / không rõ).

⚠️ Chạy trên hồ sơ nghiệm thu (vd #1), không trên hồ sơ thật của người dùng: thêm ba
lần thẩm định vào lịch sử hồ sơ.

⚠️ **Rủi ro đã biết, chưa sửa (đo được 2026-09-18):** lượt «nhận diện phân hệ» đọc cả
tài liệu nên L3 phải hỏi lại, và model có thể kể thêm phân hệ không có ở lần trước —
mỗi phân hệ như thế đẻ ra ~58 dòng trong rổ phát sinh. Xem Đ2 (`vung_moi`) trước khi
đọc số lỗi phát sinh của L3.

Kết quả chỉ chứa số đếm, mã quy tắc, tên phân hệ và nhãn vị trí — không có nội dung tài
liệu, commit được.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.extraction.vung import chuan_ten                       # noqa: E402
from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh   # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh                 # noqa: E402
from src.version import in_phien_ban                            # noqa: E402

TOI_DA_VI_DU = 20


def _pl(v: dict) -> dict:
    return (v.get("thong_ke") or {}).get("phat_lai") or {}


def _so(d: dict, *khoa) -> int:
    for k in khoa:
        d = (d or {}).get(k) or {}
    return int(d) if isinstance(d, (int, float)) else 0


def _dem_lan(hs: dict) -> dict:
    return dict((hs.get("cac_lan") or [{}])[-1].get("dem") or {})


def doi_trang_thai(truoc: dict, sau: dict, vung_doi: list[str]) -> dict:
    """Dòng baseline đổi trạng thái giữa hai lần — chia trong/ngoài phân hệ có nội dung
    đổi và theo ai kết luận ở lần sau. `truoc`, `sau` = kết quả `GET /ho-so/{id}`."""
    cu = {b["id"]: b.get("trang_thai") for b in truoc.get("baseline") or []}
    vung = set(vung_doi)
    dem: collections.Counter = collections.Counter()
    vi_du: list[str] = []
    for b in sau.get("baseline") or []:
        if cu.get(b["id"]) == b.get("trang_thai"):
            continue
        trong = chuan_ten(b.get("scope_goc") or "") in vung
        dem[f"{'trong' if trong else 'ngoai'}_vung_doi"] += 1
        dem[f"boi_{b.get('ket_luan_boi') or 'khong_ro'}"] += 1
        if len(vi_du) < TOI_DA_VI_DU:
            vi_du.append(f"{b.get('khoa')}: {cu.get(b['id'])} → {b.get('trang_thai')}"
                         f"{'' if trong else ' (ngoài vùng đổi)'}")
    return {"tong": sum(v for k, v in dem.items() if k.endswith("_vung_doi")),
            **dict(dem), "vi_du": vi_du}


def cham(*, l1: dict, l2: dict, l3: dict, dem_1: dict, dem_2: dict) -> list[dict]:
    """`l1..l3` = bản ghi việc (`GET /result/{ma}`); `dem_1`, `dem_2` = đếm của lần L1, L2."""
    kq: list[dict] = []

    def ghi(ma, dat, chi_tiet):
        kq.append({"ma": ma, "dat": dat, "chi_tiet": chi_tiet})

    td2, td3 = l2.get("thay_doi") or {}, l3.get("thay_doi") or {}
    ghi("R1", td2.get("giong_het") is True,
        f"L2 so với L1: {td2.get('loi') or ('giống hệt' if td2.get('giong_het') else td2)}")

    pl2 = _pl(l2)
    hong_1 = {c: _so(l1, "thong_ke", c, "luot_goi_hong") for c in ("c3", "c5")}
    moi_2 = {c: _so(pl2, c, "goi_moi") for c in ("c3", "c5")}
    dung_duoc = str(l2.get("phat_lai") or "").startswith("dùng lại")
    ghi("R2", dung_duoc and all(moi_2[c] <= hong_1[c] for c in moi_2),
        f"L2: «{l2.get('phat_lai')}» · hỏi lại C3 {moi_2['c3']} (L1 hỏng "
        f"{hong_1['c3']}), C5 {moi_2['c5']} (L1 hỏng {hong_1['c5']})")

    if dung_duoc and not any(moi_2.values()):
        ghi("R3", l1.get("so_finding") == l2.get("so_finding") and dem_1 == dem_2,
            f"finding {l1.get('so_finding')} → {l2.get('so_finding')} · đếm L1 {dem_1} · "
            f"L2 {dem_2}")
    else:
        ghi("R3", None, "L2 có hỏi lại lượt hỏng của L1 — kết quả được phép lệch; "
                        f"đếm L1 {dem_1} · L2 {dem_2}")

    doi = sum(int(td3.get(k) or 0) for k in ("sua", "them", "xoa"))
    ghi("R4", td3.get("giong_het") is False and doi > 0,
        f"L3 so với L2: {td3.get('loi') or ''}{doi} chỗ đổi — "
        f"{'; '.join(td3.get('vi_tri') or [])[:300]}")

    pl3 = _pl(l3)
    c3 = pl3.get("c3") or {}
    ghi("R5", _so(c3, "dung_lai") > 0 and _so(c3, "goi_moi") > 0,
        f"C3 dùng lại {_so(c3, 'dung_lai')}, hỏi lại {_so(c3, 'goi_moi')}")
    c5 = pl3.get("c5") or {}
    chung_doi = bool(pl3.get("chung_doi"))
    ghi("R6", None if chung_doi else (_so(c5, "dung_lai") > 0 and _so(c5, "goi_moi") > 0),
        f"C5 dùng lại {_so(c5, 'dung_lai')}, hỏi lại {_so(c5, 'goi_moi')}"
        + (" · phần CHUNG đổi nên hỏi lại hết là đúng — chỉ đo" if chung_doi else ""))

    for ten, v in (("L1", l1), ("L2", l2), ("L3", l3)):
        p = _pl(v)
        ghi(f"Đ1.{ten}", None,
            f"{v.get('giay_da_chay', 0):.0f} giây · hỏi lại C3 {_so(p, 'c3', 'goi_moi')} / "
            f"C5 {_so(p, 'c5', 'goi_moi')} · dùng lại C3 {_so(p, 'c3', 'dung_lai')} / "
            f"C5 {_so(p, 'c5', 'dung_lai')} · đệm lời gọi ghi thêm "
            f"{_so(v, 'thong_ke_cache', 'ghi_them')}")
    ghi("Đ2", None, f"phân hệ đổi {pl3.get('vung_doi')} · mới {pl3.get('vung_moi')} · "
                    f"phần chung đổi: {pl3.get('chung_doi')}")
    hoi_lai_c5 = sorted({x.split("#", 1)[-1] for x in (c5.get("goi_moi_vi_du") or [])})
    ghi("Đ3", None, f"C5 dùng lại {_so(c5, 'dung_lai')}/"
                    f"{_so(c5, 'dung_lai') + _so(c5, 'goi_moi')} · phạm vi phải hỏi lại: "
                    f"{', '.join(hoi_lai_c5) or '—'}")
    return kq


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


def _tham_dinh_lai(kh: KhachAPI, ho_so: int, p: pathlib.Path, nhan: str) -> dict:
    print(f"\n{nhan}: thẩm định lại hồ sơ #{ho_so} bằng «{p.name}»")
    d = kh.nop(p.read_bytes(), p.name, song_song=12, ho_so_id=ho_so)
    v = _cho(kh, d["ma"])
    print(f"  dùng lại: {v.get('phat_lai') or '—'}")
    print(f"  ghi hồ sơ: {v.get('ghi_ho_so')}")
    if v["trang_thai"] != "xong":
        raise LoiAPI(f"{nhan} không xong: {v.get('loi')}")
    return v


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ban_goc")
    ap.add_argument("ban_sua")
    ap.add_argument("--ho-so", type=int, required=True)
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ten", default="Nghiệm thu 5.3")
    a = ap.parse_args()
    in_phien_ban("nghiệm thu 5.3")

    goc, sua = pathlib.Path(a.ban_goc), pathlib.Path(a.ban_sua)
    if goc.read_bytes() == sua.read_bytes():
        print("✗ Hai tệp giống hệt nhau từng byte — cần một bản ĐÃ SỬA (xem --help).")
        return 2
    kh = KhachAPI(a.api, timeout=120, danh_tinh=tao_danh_tinh("nguoi_lam_sizing", a.ten))
    sk = kh.suc_khoe()
    if not sk.song or not ((sk.tho or {}).get("csdl") or {}).get("san_sang"):
        print(f"✗ Dịch vụ hoặc CSDL chưa sẵn sàng: {sk.thong_diep or (sk.tho or {}).get('csdl')}")
        return 2
    print(f"dịch vụ: commit {sk.commit} · đệm lời gọi bật: {(sk.tho or {}).get('cache_bat')}")

    try:
        l1 = _tham_dinh_lai(kh, a.ho_so, goc, "L1")
        dem_1 = _dem_lan(kh.ho_so(a.ho_so))
        l2 = _tham_dinh_lai(kh, a.ho_so, goc, "L2")
        hs_2 = kh.ho_so(a.ho_so)
        l3 = _tham_dinh_lai(kh, a.ho_so, sua, "L3")
        hs_3 = kh.ho_so(a.ho_so)
    except LoiAPI as e:
        print(f"✗ {e}")
        return 2

    kq = cham(l1=l1, l2=l2, l3=l3, dem_1=dem_1, dem_2=_dem_lan(hs_2))
    d4 = doi_trang_thai(hs_2, hs_3, _pl(l3).get("vung_doi") or [])
    kq.append({"ma": "Đ4", "dat": None,
               "chi_tiet": json.dumps({k: v for k, v in d4.items() if k != "vi_du"},
                                      ensure_ascii=False)})
    print()
    for k in kq:
        print(f"  {({True: '✓', False: '✗', None: '·'})[k['dat']]} {k['ma']}  {k['chi_tiet']}")
    for x in d4["vi_du"]:
        print(f"      {x}")
    hong = [k["ma"] for k in kq if k["dat"] is False]
    print("\n" + ("NGHIỆM THU 5.3: ĐẠT" if not hong else
                  f"NGHIỆM THU 5.3: CHƯA ĐẠT ({', '.join(hong)})"))

    ra = pathlib.Path(f"docs/nghiem-thu-5.3-{time.strftime('%Y%m%d-%H%M%S')}.json")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(json.dumps({
        "ho_so_id": a.ho_so, "commit": sk.commit,
        "ma_viec": [l1["ma"], l2["ma"], l3["ma"]], "tieu_chi": kq,
        "phat_lai_l3": {k: v for k, v in _pl(l3).items()},
        "thay_doi_l3": l3.get("thay_doi"), "doi_trang_thai_l2_l3": d4},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Kết quả: {ra} — gửi lại file này.")
    return 0 if not hong else 1


if __name__ == "__main__":
    raise SystemExit(main())
