"""5.1 — khoá baseline và đối chiếu một lần thẩm định với baseline. THUẦN PYTHON.

Không nhập SQLAlchemy, không gọi CSDL: đầu vào là tập finding ĐÃ QUA C7 (đúng tập
`xuat_findings` ghi ra và người dùng đọc trong báo cáo), đầu ra là các dòng để
`kho.py` ghi. Tách ra để test được bằng id thật đo ở 5.0b mà không cần máy chủ.

## Khoá = mã quy tắc + tên phân hệ ĐÃ CHUẨN HOÁ

Đo 5.0b (2026-09-16, cùng tài liệu, không sửa gì, 268/272 lời gọi model thật):
`finding_id` gốc khớp 91,6%; bỏ phần mô tả trong ngoặc cuối tên phân hệ thì khớp
98,6%. 50 dòng lệch chỉ vì C3 viết `Master (K8s Master node)` ở lượt này và
`Master (K8s Control plane)` ở lượt kia.

## Chặn gộp nhầm

Hồ sơ sizing hay có `DB (Primary)` / `DB (Replica)`, `App (DC)` / `App (DR)` — hai
phân hệ THẬT chỉ khác nhau phần trong ngoặc. Nếu trong CÙNG một lần chạy có hai
tên gốc khác nhau rút về cùng một khoá thì những dòng đó giữ tên gốc làm khoá.
Chuẩn hoá mà gộp hai phân hệ thật là để lỗi của bên này che lỗi của bên kia.

**Giới hạn đã biết:** chặn gộp chỉ nhìn TRONG một lần chạy. Lần 1 có cả Primary và
Replica (giữ tên gốc), lần 2 C3 đổi `DB (Primary)` thành `DB (Chính)` → dòng
baseline không khớp, bị tính «đã sửa» và lỗi mới vào rổ phát sinh. Hiếm, và hiện
ra rõ ràng ở cả hai rổ chứ không mất.

## «Đã sửa» = không còn xuất hiện

Luật 5.3 người dùng chốt 2026-09-16. Giá đã đo và chấp nhận: ~1,4% finding tự biến
mất giữa hai lượt không ai sửa gì ⇒ trên tài liệu ~700 finding, mỗi lần thẩm định
lại có khoảng 10 dòng «đã sửa» mà thực ra chưa ai động vào.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HE_THONG = "he_thong"

# Nhóm C7 (xem `report.xuat_findings`) mà công cụ KHÔNG kết luận được gì.
NHOM_CHUA_KIEM = ("vong2_chua_kiem", "vong2_tam_hoan")
CATEGORY_CHUA_KIEM = ("khong_kiem_chung_duoc",)

_NGOAC_CUOI = re.compile(r"\s*\(.*\)\s*$")


def _tach_hau_to(fid: str) -> tuple[str, str]:
    """(id gốc, hậu tố khử trùng). `report.xuat_findings` gắn `#2`, `#3` khi hai
    finding trùng `rule#scope`. `KPI-02#PH2` là tên phân hệ «PH2», KHÔNG phải hậu
    tố — chỉ cắt khi có từ ba phần trở lên."""
    phan = fid.split("#")
    if len(phan) >= 3 and phan[-1].isdigit():
        return "#".join(phan[:-1]), phan[-1]
    return fid, ""


def _chuan_hoa_scope(scope: str) -> str:
    return " ".join(_NGOAC_CUOI.sub("", scope).split()).casefold()


def _goc_chuan_hoa(id_goc: str) -> str:
    rule, co, scope = id_goc.partition("#")
    if not co:
        return id_goc
    return f"{rule}#{_chuan_hoa_scope(scope)}"


def gan_khoa(findings: list[dict]) -> list[tuple[str, dict]]:
    """[(khoá, finding)] theo đúng thứ tự vào. Khoá DUY NHẤT trong một lần chạy.

    Tất định: cùng tập id thì cùng khoá, không phụ thuộc thứ tự duyệt.
    """
    tach = [_tach_hau_to(str(f.get("id", ""))) for f in findings]

    # Chặn gộp nhầm: khoá chuẩn hoá nào ứng với ≥2 id gốc KHÁC NHAU thì mọi dòng
    # của nó giữ id gốc.
    goc_theo_khoa: dict[str, set[str]] = {}
    for id_goc, _ in tach:
        goc_theo_khoa.setdefault(_goc_chuan_hoa(id_goc), set()).add(id_goc)
    bi_gop = {k for k, goc in goc_theo_khoa.items() if len(goc) > 1}

    ra: list[tuple[str, dict]] = []
    da_dung: set[str] = set()
    for (id_goc, hau_to), f in zip(tach, findings):
        k = _goc_chuan_hoa(id_goc)
        khoa = id_goc if k in bi_gop else k
        if hau_to:
            khoa = f"{khoa}#{hau_to}"
        # Lưới an toàn: ràng buộc UNIQUE(ho_so_id, khoa) trong CSDL sẽ làm hỏng cả
        # baseline vì một dòng. Về lý thuyết không tới được đây (id đã duy nhất).
        goc, n = khoa, 2
        while khoa in da_dung:
            khoa, n = f"{goc}~{n}", n + 1
        da_dung.add(khoa)
        ra.append((khoa, f))
    return ra


def scope_goc(f: dict) -> str:
    """Tên phân hệ GỐC để hiển thị — khoá chuẩn hoá chỉ để nối các lần."""
    id_goc, _ = _tach_hau_to(str(f.get("id", "")))
    _, co, scope = id_goc.partition("#")
    return scope if co else (f.get("scope_key") or "")


def trang_thai_khi_con(f: dict) -> str:
    """Finding VẪN xuất hiện: chưa đạt, hay công cụ chưa kiểm được."""
    if f.get("nhom") in NHOM_CHUA_KIEM or f.get("category") in CATEGORY_CHUA_KIEM:
        return "chua_kiem_duoc"
    return "chua_dat"


def ket_luan_boi(f: dict) -> str:
    """Ai kết luận (5.6). Có con số do code tính → C4; công cụ chưa kiểm được hoặc
    cảnh báo NT4 → không rõ; còn lại là C5 (định tính)."""
    if str(f.get("computed_evidence") or "").strip() and \
            not str(f.get("id", "")).startswith("NT4"):
        return "c4"
    if trang_thai_khi_con(f) == "chua_kiem_duoc":
        return "khong_ro"
    return "c5"


def dong_finding(khoa: str, f: dict) -> dict:
    """Các cột chung của `finding_baseline` và `finding_phat_sinh`."""
    return {
        "khoa": khoa,
        "finding_id_goc": str(f.get("id", ""))[:400],
        "rule_ref": str(f.get("rule_ref") or "")[:40],
        "scope_goc": scope_goc(f)[:300],
        "muc_do": str(f.get("severity") or "info")[:20],
        "nhom_loi": str(f.get("category") or "")[:60],
        "nhom_c7": str(f.get("nhom") or "")[:30],
        "noi_dung": str(f.get("finding") or ""),
        "vi_tri": str(f.get("location") or "")[:300],
        "computed_evidence": str(f.get("computed_evidence") or ""),
    }


@dataclass
class DoiChieu:
    """Kết quả so một lần thẩm định với baseline."""
    # {finding_baseline_id: dòng ket_qua_lan (chưa có lan_tham_dinh_id)}
    ket_qua: dict[int, dict] = field(default_factory=dict)
    phat_sinh: list[dict] = field(default_factory=list)

    def dem(self) -> dict[str, int]:
        d = {"dat": 0, "chua_dat": 0, "chua_kiem_duoc": 0}
        for r in self.ket_qua.values():
            d[r["trang_thai"]] += 1
        d["phat_sinh"] = len(self.phat_sinh)
        return d


def ket_qua_lan_dau(khoa_findings: list[tuple[str, dict]],
                    id_theo_khoa: dict[str, int]) -> DoiChieu:
    """Lần 1: mọi dòng baseline đều đang «còn». Không có phát sinh."""
    dc = DoiChieu()
    for khoa, f in khoa_findings:
        dc.ket_qua[id_theo_khoa[khoa]] = _dong_ket_qua(f, None)
    return dc


def doi_chieu(baseline: list[dict], findings: list[dict]) -> DoiChieu:
    """So lần N với baseline. `baseline` = các dòng `finding_baseline` (có `id`,
    `khoa`, `muc_do`). KHÔNG thêm bớt dòng baseline — chỉ gán trạng thái."""
    dc = DoiChieu()
    moi = dict(gan_khoa(findings))
    theo_khoa = {b["khoa"]: b for b in baseline}
    for b in baseline:
        f = moi.get(b["khoa"])
        if f is None:
            dc.ket_qua[b["id"]] = {"trang_thai": "dat", "ket_luan_boi": "khong_ro",
                                   "muc_do_lan": None, "computed_evidence": "",
                                   "dau_vao": ""}
        else:
            dc.ket_qua[b["id"]] = _dong_ket_qua(f, b.get("muc_do"))
    for khoa, f in moi.items():
        if khoa not in theo_khoa:
            dc.phat_sinh.append(dong_finding(khoa, f))
    return dc


def _dong_ket_qua(f: dict, muc_do_baseline: str | None) -> dict:
    muc = str(f.get("severity") or "")
    return {
        "trang_thai": trang_thai_khi_con(f),
        "ket_luan_boi": ket_luan_boi(f),
        # Mức độ ĐÓNG BĂNG theo baseline (5.6); chỉ ghi lại khi lần này khác, để
        # hiện chú thích nhỏ bên cạnh chứ không đổi cột chính.
        "muc_do_lan": muc if muc_do_baseline and muc != muc_do_baseline else None,
        "computed_evidence": str(f.get("computed_evidence") or ""),
        # 5.6 — giá trị đầu vào C4 đã dùng cho LẦN NÀY. Trống với dòng của C5 hoặc
        # cảnh báo NT4: chúng không có đầu vào nào do code đọc.
        "dau_vao": str(f.get("dau_vao") or ""),
    }
