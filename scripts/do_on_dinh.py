#!/usr/bin/env python
"""5.0b — hai lượt thẩm định CÙNG một tài liệu, KHÔNG sửa gì, có cho cùng kết quả không?

    py scripts/do_on_dinh.py <ma_A> <ma_B> --api http://localhost:8902

## Vì sao phải đo trước khi viết 5.3 và 5.6

Cả GĐ 5 đứng trên một giả định chưa ai kiểm: *chạy lại một tài liệu chưa sửa gì
thì tập finding giữ nguyên*. Nếu giả định sai thì:

- **5.1** — dòng baseline không nối được sang lượt sau, bảng lịch sử mất hàng;
- **5.3** — "lỗi đã sửa" và "lỗi tự biến mất" lẫn vào nhau, không phân biệt được;
- **5.6** — cột Trạng thái nhấp nháy, Admin thấy "đã sửa xong" cho thứ chưa ai
  động vào.

Dữ kiện đã có: 3 lượt độc lập trên 14 hồ sơ (2026-09-11) cho recall 86,5–87,5%
— tập finding TỰ dao động khi không ai sửa gì. Chưa biết mức dao động ở cấp
MỘT tài liệu, mà đó mới là cấp người dùng nhìn thấy.

## ⚠️ Đệm lời gọi phải TẮT ở lượt B

`src/llm/cache.py` đệm theo nội dung lời gọi và **bật mặc định**. Không tắt thì
lượt B chỉ phát lại lượt A, script này in 100% ổn định, và con số đó vô nghĩa.
Đặt `SIZING_COPILOT_KHONG_CACHE=1` cho dịch vụ API trước khi chạy lượt B.

Lượt A thì KHÔNG cần tắt: một lượt lấy từ đệm vẫn tái hiện đúng đầu ra model
gốc, nên so A với B vẫn là so hai lượt model độc lập.

## Nếu việc demo KHÔNG có `findings.json`

Tập finding chỉ được lưu từ bản 2026-09-14 (`KhoCongViec.luu_findings`). Việc
chạy bằng image cũ hơn chỉ còn báo cáo Markdown — trong đó không có `finding_id`,
nên không dựng lại được và không so được. Đừng cố phân tích cú pháp báo cáo.

Cách rẻ: **nộp lại chính tài liệu ấy với đệm BẬT**. Lượt demo đã nạp đệm, nên
gần như mọi lời gọi đều trúng — lượt này xong trong vài phút thay vì ~16, và tái
hiện đúng đầu ra model của buổi demo, lần này có ghi `findings.json`. Đó là lượt A.
Rồi tắt đệm và chạy lượt B như trên.

Điều kiện: volume `copilot-cache` chưa bị xoá (`docker compose down -v` là xoá),
và phần sinh lời gọi của C3/C5 chưa đổi — đổi thì khoá đệm đổi, lượt A sẽ gọi
model thật và mất ~16 phút. Vẫn dùng được, chỉ lâu hơn.

Điều KHÔNG quan trọng: lượt A đến từ đệm hay từ model. Phép đo cần **hai lượt
model độc lập**; chỉ cần lượt B không được phát ra từ đệm của lượt A.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh   # noqa: E402
from src.version import in_phien_ban                            # noqa: E402

# Nhóm mà C7 xếp vào "công cụ chưa đọc được chỗ này" — với những dòng này không
# có gì để kết luận "đã fix chưa", nên chúng là trạng thái thứ ba của 5.6.
NHOM_CHUA_KIEM = "vong2_chua_kiem"


def _khoa_goc(fid: str) -> str:
    """Bỏ hậu tố khử trùng `#2`, `#3` mà `report.py` gắn THEO THỨ TỰ DUYỆT.

    `id` gốc là `"{rule_ref}#{scope_key}"` — tất định. Nhưng khi hai finding
    trùng cặp đó, `xuat_findings` gắn thêm `#N` theo thứ tự gặp, nên đổi thứ tự
    giữa hai lượt là dòng baseline trỏ sang finding khác. Tách hai chuyện ra:
    "khoá không ổn định" khác với "finding thật sự khác nhau".
    """
    phan = fid.split("#")
    if len(phan) >= 3 and phan[-1].isdigit():
        return "#".join(phan[:-1])
    return fid


def _scope_chuan_hoa(fid: str) -> str:
    """`rule#scope` với scope bỏ phần diễn giải trong ngoặc, không phân biệt hoa thường.

    Đo 2026-09-16 (717 vs 718 finding, 268/272 lời gọi thật): phần lớn id lệch có
    dạng `ARC-02#Master (K8s Master node)` ở lượt A và `ARC-02#Master (K8s
    Control plane)` ở lượt B — CÙNG một phân hệ, chỉ phần mô tả trong ngoặc do
    C3 diễn đạt lại. Một phân hệ đổi tên là mọi quy tắc gắn với nó mất khớp.

    Hàm này đo xem chuẩn hoá cứu được bao nhiêu, để 5.1 chọn khoá bằng số chứ
    không bằng đoán.
    """
    import re
    goc = _khoa_goc(fid)
    rule, _, scope = goc.partition("#")
    scope = re.sub(r"\s*\(.*\)\s*$", "", scope).strip().casefold()
    return f"{rule}#{scope}"


def _khop_da_tap(a: list[str], b: list[str]) -> int:
    """Số cặp khớp khi coi hai danh sách là ĐA TẬP (khoá lặp được)."""
    da: dict[str, int] = {}
    for k in a:
        da[k] = da.get(k, 0) + 1
    db: dict[str, int] = {}
    for k in b:
        db[k] = db.get(k, 0) + 1
    return sum(min(n, db.get(k, 0)) for k, n in da.items())


# Các giai đoạn có gọi model. C4 là Python thuần nên không có mặt ở đây.
GIAI_DOAN_GOI = ("c2", "c3", "c5")


def so_luot_goi(v: dict) -> int | None:
    """Tổng lời gọi model của một lượt chạy. None = lượt chạy không ghi lại.

    Đây mới là bằng chứng. `cache.bat=False` chỉ nói lượt này KHÔNG phát lại từ
    đệm — nó không nói lượt này có gọi model hay không, mà hai mệnh đề đó khác
    nhau đúng ở chỗ làm hỏng phép đo: một lượt gọi 0 lần thì trùng khớp 100% với
    bất kỳ lượt nào khác, và con số 100% ấy không nói gì về model cả.
    """
    tk = v.get("thong_ke") or {}
    if not tk:
        return None
    co = [tk[g] for g in GIAI_DOAN_GOI if isinstance(tk.get(g), dict)]
    if not co:
        return None
    return sum(int(x.get("luot_goi") or 0) for x in co)


def gia_tri_do(va: dict, vb: dict) -> tuple[bool, list[str]]:
    """Phép đo này có dùng được không? (dùng_được, các dòng giải thích)

    Trả lời bằng DỮ LIỆU của chính hai lượt chạy, không bằng trí nhớ người chạy.
    `thong_ke_cache` = {bat, ban_ghi_truoc, ban_ghi_sau, ghi_them} do
    `pipeline.chay` ghi lại.

    Vì sao cần: ngày 2026-09-16 hai lượt cho 61/61 khớp, và không ai chứng minh
    được lượt sau đã gọi model hay chỉ phát lại từ đệm — mất trọn phép đo. Chỗ
    lệch duy nhất hoá ra là một đường dẫn tạm, đổi ở mọi lượt bất kể có gọi model.
    """
    ly: list[str] = []
    dung = True
    for ten, v in (("A", va), ("B", vb)):
        n = so_luot_goi(v)
        if n is None:
            ly.append(f"Lượt {ten}: KHÔNG ghi lại số lời gọi model — image cũ hơn "
                      "bản này, không chứng minh được pipeline đã chạy đủ.")
            dung = False
        elif n == 0:
            ly.append(f"Lượt {ten}: **0 lời gọi model**. Trùng khớp 100% là đương "
                      "nhiên và không nói gì về độ ổn định của model. ✗")
            dung = False
        else:
            ly.append(f"Lượt {ten}: {n} lời gọi model. ✓")
        tk = v.get("thong_ke_cache") or {}
        if not tk:
            ly.append(f"Lượt {ten}: KHÔNG có số liệu đệm — chạy bằng image cũ hơn "
                      "bản 2026-09-16, không chứng minh được đã gọi model.")
            dung = False
            continue
        if not tk.get("bat"):
            ly.append(f"Lượt {ten}: đệm TẮT → không lời gọi nào được phát lại.")
            continue
        them = int(tk.get("ghi_them") or 0)
        if them > 0:
            ly.append(f"Lượt {ten}: đệm bật nhưng ghi thêm {them} bản ghi → "
                      f"{them} lời gọi thật. ✓")
        else:
            ly.append(f"Lượt {ten}: đệm BẬT và không ghi thêm bản ghi nào → "
                      "phát lại hoàn toàn từ đệm, KHÔNG gọi model. ✗")
            dung = False
    if (va.get("tuy_chon") or {}).get("chi_nhom"):
        ly.append("Có lọc `chi_nhom` → kết luận chỉ đúng cho nhóm quy tắc đã lọc, "
                  "không phải cho một lượt thẩm định đầy đủ.")
        dung = False
    return dung, ly


def _dong_dich_vu(sk) -> str:
    """Một dòng nhận dạng dịch vụ đang hỏi.

    Đọc các trường phụ qua `sk.tho` — bản ghi THÔ của `/health` — chứ không qua
    thuộc tính của `SucKhoe`: trường `ban` (nhãn thể hiện) có ở bản này nhưng
    không có ở bản kia, và một `AttributeError` ở dòng in đầu tiên thì giết cả
    phép đo trước khi nó chạm tới dữ liệu.
    """
    ban = (sk.tho or {}).get("ban") or "—"
    return f"dịch vụ: SỐNG · bản {ban} · commit {sk.commit or '?'}"


def _lay(kh: KhachAPI, ma: str, ten: str) -> tuple[dict, list[dict]]:
    try:
        viec = kh.viec(ma)
    except LoiAPI as e:
        sys.exit(f"✗ Không tra được {ten} «{ma}»: {e}")
    if viec["trang_thai"] != "xong":
        sys.exit(f"✗ {ten} «{ma}» đang ở trạng thái «{viec['trang_thai']}», "
                 "chưa có tập finding để so.")
    try:
        d = kh.findings(ma)
    except LoiAPI as e:
        sys.exit(
            f"✗ {ten} «{ma}» không có tập finding để so: {e}\n"
            "\n  Việc chạy bằng image trước 2026-09-14 chỉ còn báo cáo Markdown,\n"
            "  mà báo cáo không mang `finding_id` nên không dựng lại được.\n"
            "\n  Cách lấy lại lượt A mà không mất 16 phút — nộp lại ĐÚNG tài liệu ấy\n"
            "  với đệm BẬT (buổi demo đã nạp đệm, nên hầu hết lời gọi sẽ trúng):\n"
            f"    docker compose exec copilot printenv SIZING_COPILOT_KHONG_CACHE  # phải TRỐNG\n"
            f"    py scripts/nop_bai.py <file.docx> --giong-nhu {ma}\n"
            "  Xong trong vài phút là đệm trúng; ~16 phút là đệm trượt — vẫn dùng được.")
    return viec, list(d.get("findings", []))


def _dem_theo(ds: list[dict], khoa: str) -> dict[str, int]:
    ra: dict[str, int] = {}
    for f in ds:
        ra[str(f.get(khoa, ""))] = ra.get(str(f.get(khoa, "")), 0) + 1
    return ra


def _pt(tu: int, mau: int) -> str:
    return "—" if not mau else f"{tu / mau:.1%}".replace(".", ",")


def so_sanh(fa: list[dict], fb: list[dict]) -> dict:
    """Mọi con số của phép đo. Không in gì — để test gọi được."""
    ia = {f["id"]: f for f in fa}
    ib = {f["id"]: f for f in fb}
    khop = sorted(set(ia) & set(ib))
    chi_a = sorted(set(ia) - set(ib))
    chi_b = sorted(set(ib) - set(ia))

    # Khớp theo khoá đã bỏ hậu tố: phần chênh với `khop` là số dòng mất khớp
    # CHỈ vì thứ tự duyệt, tức là lỗi khoá chứ không phải model đổi ý.
    ga, gb = _dem_theo([{"k": _khoa_goc(i)} for i in ia], "k"), \
        _dem_theo([{"k": _khoa_goc(i)} for i in ib], "k")
    khop_goc = sum(min(ga[k], gb.get(k, 0)) for k in ga)

    doi: dict[str, list[str]] = {"muc_do": [], "nhom": [], "cau_chu": [],
                                 "can_cu": [], "vi_tri": []}
    for i in khop:
        a, b = ia[i], ib[i]
        if a.get("severity") != b.get("severity"):
            doi["muc_do"].append(i)
        if a.get("nhom") != b.get("nhom"):
            doi["nhom"].append(i)
        if (a.get("finding") or "").strip() != (b.get("finding") or "").strip():
            doi["cau_chu"].append(i)
        if (a.get("computed_evidence") or "") != (b.get("computed_evidence") or ""):
            doi["can_cu"].append(i)
        if (a.get("location") or "") != (b.get("location") or ""):
            doi["vi_tri"].append(i)

    def _co_can_cu(ds):
        return {f["id"] for f in ds if (f.get("computed_evidence") or "").strip()}

    ca, cb = _co_can_cu(fa), _co_can_cu(fb)
    chua_kiem_a = {f["id"] for f in fa if f.get("nhom") == NHOM_CHUA_KIEM}

    khop_chuan_hoa = _khop_da_tap([_scope_chuan_hoa(i) for i in ia],
                                  [_scope_chuan_hoa(i) for i in ib])
    # Hợp các tập đổi, không cộng dồn: một dòng đổi cả mức độ lẫn căn cứ chỉ là
    # MỘT dòng không bền. Bản trước trừ thẳng từng loại nên đếm trùng.
    khong_ben = set(doi["muc_do"]) | set(doi["nhom"]) | set(doi["can_cu"])

    return {
        "so_a": len(fa), "so_b": len(fb),
        "khop": len(khop), "chi_a": len(chi_a), "chi_b": len(chi_b),
        "khop_theo_khoa_goc": khop_goc,
        "mat_khop_do_hau_to": max(0, khop_goc - len(khop)),
        "khop_scope_chuan_hoa": khop_chuan_hoa,
        "mat_khop_do_ten_scope": max(0, khop_chuan_hoa - khop_goc),
        "ben_vung": len(khop) - len(khong_ben),
        "doi": {k: len(v) for k, v in doi.items()},
        "code_tinh_duoc_a": len(ca), "code_tinh_duoc_b": len(cb),
        "code_tinh_duoc_khop": len(ca & cb),
        "chua_kiem_duoc_a": len(chua_kiem_a),
        "vi_du_chi_a": chi_a[:10], "vi_du_chi_b": chi_b[:10],
        "vi_du_doi_muc_do": doi["muc_do"][:10],
        "vi_du_doi_can_cu": doi["can_cu"][:10],
        # Danh sách ĐẦY ĐỦ — bản trước chỉ giữ 10 ví dụ, nên muốn phân tích thêm
        # là phải chạy lại. Chỉ là mã quy tắc + tên phân hệ, không có nội dung
        # tài liệu.
        "ds_chi_a": chi_a, "ds_chi_b": chi_b,
        "ds_doi_muc_do": doi["muc_do"], "ds_doi_nhom": doi["nhom"],
        "ds_doi_can_cu": doi["can_cu"],
    }


def dung_bao_cao(kq: dict, va: dict, vb: dict, ma_a: str, ma_b: str) -> str:
    n = max(kq["so_a"], kq["so_b"])
    d = kq["doi"]
    ben_vung = kq["ben_vung"]
    dung_duoc, ly_do = gia_tri_do(va, vb)
    dong = [
        "# 5.0b — đo độ ổn định giữa hai lượt thẩm định",
        "",
        # Đặt NGAY ĐẦU: một phép đo không dùng được mà người đọc lướt tới bảng
        # số trước là một tuần code sai hướng.
        ("> ✅ **Phép đo dùng được.**" if dung_duoc
         else "> ⛔ **Phép đo CHƯA dùng được — đừng chốt thiết kế theo số bên dưới.**"),
        "",
    ] + [f"> - {x}" for x in ly_do] + [
        "",
        f"Đo lúc {time.strftime('%Y-%m-%d %H:%M')}. Cùng một tài liệu, **không sửa gì**.",
        "",
        "| | Lượt A | Lượt B |",
        "|---|---|---|",
        f"| Mã việc | `{ma_a}` | `{ma_b}` |",
        f"| Tài liệu | `{va['ten_file']}` | `{vb['ten_file']}` |",
        f"| Tuỳ chọn | `{va.get('tuy_chon')}` | `{vb.get('tuy_chon')}` |",
        f"| Số finding | {kq['so_a']} | {kq['so_b']} |",
        f"| Phút chạy | {va['giay_da_chay'] / 60:.1f} | {vb['giay_da_chay'] / 60:.1f} |",
        f"| **Lời gọi model** | {so_luot_goi(va)} | {so_luot_goi(vb)} |",
        f"| Đệm | `{va.get('thong_ke_cache') or 'không có số liệu'}` | "
        f"`{vb.get('thong_ke_cache') or 'không có số liệu'}` |",
        "",
        "## Khoá nối giữa hai lượt  → quyết định 5.1",
        "",
        "| Số đo | Giá trị | Tỉ lệ |",
        "|---|---|---|",
        f"| Khớp theo `finding_id` | {kq['khop']} | {_pt(kq['khop'], n)} |",
        f"| Chỉ có ở lượt A | {kq['chi_a']} | {_pt(kq['chi_a'], n)} |",
        f"| Chỉ có ở lượt B | {kq['chi_b']} | {_pt(kq['chi_b'], n)} |",
        f"| Khớp khi BỎ hậu tố `#N` | {kq['khop_theo_khoa_goc']} | "
        f"{_pt(kq['khop_theo_khoa_goc'], n)} |",
        f"| → mất khớp CHỈ vì hậu tố thứ tự | **{kq['mat_khop_do_hau_to']}** | "
        f"{_pt(kq['mat_khop_do_hau_to'], n)} |",
        f"| Khớp khi CHUẨN HOÁ tên phân hệ (bỏ phần trong ngoặc) | "
        f"{kq['khop_scope_chuan_hoa']} | {_pt(kq['khop_scope_chuan_hoa'], n)} |",
        f"| → mất khớp CHỈ vì C3 diễn đạt lại tên phân hệ | "
        f"**{kq['mat_khop_do_ten_scope']}** | {_pt(kq['mat_khop_do_ten_scope'], n)} |",
        "",
        "Hai dòng «→ mất khớp CHỈ vì…» là lỗi KHOÁ, sửa được bằng code: hậu tố thứ "
        "tự của `report.py`, và tên phân hệ do C3 diễn đạt lại. Phần không khớp còn "
        "lại sau chuẩn hoá mới là model thật sự đổi ý — không sửa bằng code được.",
        "",
        "## Trong số dòng khớp, có gì đổi  → quyết định 5.6",
        "",
        "| Đổi | Số dòng | Tỉ lệ trên số khớp |",
        "|---|---|---|",
        f"| Mức độ (severity) | {d['muc_do']} | {_pt(d['muc_do'], kq['khop'])} |",
        f"| Nhóm (vòng / chưa kiểm được) | {d['nhom']} | {_pt(d['nhom'], kq['khop'])} |",
        f"| `computed_evidence` (con số code tính) | {d['can_cu']} | "
        f"{_pt(d['can_cu'], kq['khop'])} |",
        f"| Vị trí | {d['vi_tri']} | {_pt(d['vi_tri'], kq['khop'])} |",
        f"| Câu chữ mô tả | {d['cau_chu']} | {_pt(d['cau_chu'], kq['khop'])} |",
        "",
        f"**Bền hoàn toàn** (khớp id, không đổi mức độ / nhóm / căn cứ): "
        f"**{ben_vung}** dòng — {_pt(ben_vung, n)} của lượt lớn hơn.",
        "",
        "Đổi *câu chữ* không đáng lo: bảng 5.6 khoá theo `finding_id`, không theo câu. "
        "Đổi *mức độ*, *nhóm* hay *căn cứ* mới đáng lo — đó là những thứ Admin đọc.",
        "",
        "## Bao nhiêu dòng code KẾT LUẬN được  → cột Trạng thái của 5.6",
        "",
        "| Số đo | Lượt A | Lượt B |",
        "|---|---|---|",
        f"| Có `computed_evidence` (C4 tính lại được) | {kq['code_tinh_duoc_a']} | "
        f"{kq['code_tinh_duoc_b']} |",
        f"| …trong đó khớp cả hai lượt | {kq['code_tinh_duoc_khop']} | |",
        f"| Xếp nhóm «chưa kiểm được» | {kq['chua_kiem_duoc_a']} | |",
        "",
        f"Chỉ {_pt(kq['code_tinh_duoc_a'], kq['so_a'])} số finding có con số do code "
        "tính — chỉ những dòng đó mới có thể mang trạng thái *Đạt* / *Chưa đạt* một "
        "cách chắc chắn. Phần còn lại là *Chưa kiểm được*, và đó là sự thật cần cho "
        "Admin thấy chứ không phải chỗ để đoán.",
        "",
        "## Đọc số này để quyết định gì",
        "",
        "- Khớp `finding_id` **≥ 95%** → 5.1 dùng thẳng `finding_id` làm khoá baseline.",
        "- **85–95%** → phải vá hậu tố `#N` và neo `scope_key` trước khi viết 5.1.",
        "- **< 85%** → khoá theo `(rule_ref, vị trí trong tài liệu)` chứ không theo "
        "`scope_key` do C3 trích; và 5.3 phải coi «finding biến mất» là *chưa kết luận* "
        "chứ không phải *đã sửa xong*.",
        "- Dòng đổi mức độ/nhóm **> 10%** số khớp → cột Trạng thái của 5.6 bắt buộc "
        "phải hiện cả «lượt nào kết luận», không chỉ kết luận cuối.",
        "",
        "## Lượt nào gọi model thật",
        "",
        f"Lượt A chạy {va['giay_da_chay'] / 60:.1f} phút, lượt B "
        f"{vb['giay_da_chay'] / 60:.1f} phút. Một tài liệu gọi model thật tốn "
        "**~16–23 phút** (đo 2026-09-16: 21,7 và 22,6 phút, 268 và 272 lời gọi); "
        "xong trong vài phút nghĩa là lượt đó lấy từ đệm hoặc lời gọi đang hỏng.",
        "",
        "Lượt A lấy từ đệm thì KHÔNG sao — nó tái hiện đúng đầu ra model của lượt "
        "gốc. **Lượt B lấy từ đệm mới là hỏng**: khi đó nó chỉ phát lại lượt A và "
        "mọi tỉ lệ trên đây đều là 100% giả.",
        "",
        "## Cảnh báo về chính phép đo",
        "",
        "- Script KHÔNG kiểm được hai lượt có chạy cùng một commit hay không — kho việc "
        "không lưu phiên bản mã theo từng việc. Tự đối chiếu trước khi tin con số.",
        "- Nếu lượt B chạy khi đệm lời gọi còn bật, nó chỉ phát lại lượt A và mọi tỉ lệ "
        "trên đây sẽ là 100%. Con số 100% ở đây nên bị nghi ngờ trước khi được mừng.",
        "",
    ]
    if kq["vi_du_chi_a"]:
        dong += ["## Ví dụ finding chỉ có ở một lượt", "",
                 "Chỉ ở A: " + ", ".join(f"`{x}`" for x in kq["vi_du_chi_a"]), "",
                 "Chỉ ở B: " + ", ".join(f"`{x}`" for x in kq["vi_du_chi_b"]), ""]
    return "\n".join(dong)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ma_a", help="mã việc lượt A (lượt đã chạy trước)")
    ap.add_argument("ma_b", help="mã việc lượt B (lượt chạy lại, đệm ĐÃ TẮT)")
    ap.add_argument("--api", default=dia_chi_mac_dinh())
    ap.add_argument("--ra", default="", help="ghi báo cáo .md (mặc định vào docs/)")
    a = ap.parse_args()
    in_phien_ban("đo độ ổn định 5.0b")

    kh = KhachAPI(a.api, timeout=60)
    sk = kh.suc_khoe()
    if not sk.song:
        print(f"\n✗ Không gọi được dịch vụ tại {kh.dia_chi}\n  {sk.thong_diep}")
        return 2
    print(_dong_dich_vu(sk))

    va, fa = _lay(kh, a.ma_a, "lượt A")
    vb, fb = _lay(kh, a.ma_b, "lượt B")
    if va["ten_file"] != vb["ten_file"]:
        print(f"\n⚠️  HAI TÀI LIỆU KHÁC NHAU: «{va['ten_file']}» vs «{vb['ten_file']}»."
              "\n   Phép đo này chỉ có nghĩa trên CÙNG một tài liệu.")
    if va.get("tuy_chon") != vb.get("tuy_chon"):
        print(f"\n⚠️  Tuỳ chọn khác nhau: {va.get('tuy_chon')} vs {vb.get('tuy_chon')}."
              "\n   Lọc nhóm/vòng khác nhau thì tập finding khác nhau là đương nhiên.")

    dung_duoc, ly_do = gia_tri_do(va, vb)
    print("\nPHÉP ĐO NÀY " + ("DÙNG ĐƯỢC" if dung_duoc else "CHƯA DÙNG ĐƯỢC:"))
    for d in ly_do:
        print("  " + d)

    kq = so_sanh(fa, fb)
    n = max(kq["so_a"], kq["so_b"])
    print(f"\nA: {kq['so_a']} finding · B: {kq['so_b']} finding")
    print(f"  khớp id          {kq['khop']:>4}  ({_pt(kq['khop'], n)})")
    print(f"  chỉ ở A          {kq['chi_a']:>4}  ({_pt(kq['chi_a'], n)})")
    print(f"  chỉ ở B          {kq['chi_b']:>4}  ({_pt(kq['chi_b'], n)})")
    print(f"  mất khớp vì hậu tố thứ tự: {kq['mat_khop_do_hau_to']}")
    print(f"  trong số khớp — đổi mức độ {kq['doi']['muc_do']} · "
          f"đổi nhóm {kq['doi']['nhom']} · đổi căn cứ {kq['doi']['can_cu']} · "
          f"đổi câu chữ {kq['doi']['cau_chu']}")
    print(f"  code tính lại được: A {kq['code_tinh_duoc_a']} · B {kq['code_tinh_duoc_b']} "
          f"· khớp {kq['code_tinh_duoc_khop']}")
    cung_tap = kq["khop"] == n and kq["chi_a"] == kq["chi_b"] == 0
    so_khac = sum(kq["doi"].values())
    if cung_tap and so_khac == 0:
        # Phát lại từ đệm là GIỐNG TỪNG BYTE. Chỉ khi không một trường nào lệch
        # thì mới đáng nghi — lệch dù một chỗ đã đủ chứng minh có hai lượt gọi.
        print("\n⚠️  GIỐNG TỪNG TRƯỜNG, không lệch một chỗ nào. Kiểm lượt B có"
              "\n   thật sự gọi model không — đệm còn bật thì nó phát lại lượt A:"
              "\n   docker compose exec copilot printenv SIZING_COPILOT_KHONG_CACHE")
    elif cung_tap:
        print(f"\nCùng tập finding, lệch {so_khac} chỗ:")
        for ten, ds in (("mức độ", kq["vi_du_doi_muc_do"]),
                        ("căn cứ", kq["vi_du_doi_can_cu"])):
            if ds:
                print(f"    {ten}: " + ", ".join(ds))
        # KHÔNG kết luận "hai lượt độc lập" từ chỗ lệch: một trường có thể
        # lệch vì CẤU TRÚC chứ không vì model. NT4-C1 từng mang đường dẫn
        # tạm của máy chủ, đổi ở mọi lượt chạy — 2026-09-16 nó là chỗ lệch
        # duy nhất, và suýt bị đọc thành bằng chứng model đã chạy hai lần.
        print("\n  Kiểm từng chỗ lệch: lệch vì MODEL hay vì cấu trúc (đường dẫn,"
              "\n  thời gian, số ngẫu nhiên)? Chỉ loại đầu mới nói lên điều gì.")

    ra = pathlib.Path(a.ra) if a.ra else pathlib.Path(
        f"docs/do-on-dinh-{time.strftime('%Y%m%d-%H%M%S')}.md")
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(dung_bao_cao(kq, va, vb, a.ma_a, a.ma_b), encoding="utf-8")
    ra.with_suffix(".json").write_text(
        json.dumps({"ma_a": a.ma_a, "ma_b": a.ma_b, "ket_qua": kq},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Báo cáo: {ra}\n  Số liệu thô: {ra.with_suffix('.json')}")
    print("  Gửi CẢ HAI file lại để chốt thiết kế 5.1 / 5.3 / 5.6.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
