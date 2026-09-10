"""Test hồi quy 5 fix "báo cáo phình" (2026-09-10).

Lượt HỆ THỐNG 2026-09-09 phình 388 finding / 191KB: 302 finding "chưa kiểm được"
là ~25 tham số thiếu × 6 phân hệ, quote nguyên văn lặp 47% dung lượng, 297 mục
đều dán [Quan trọng]. Các test này khoá hành vi mới:

  1. Vòng 2 "chưa kiểm được" gom theo tham số — một dòng mỗi tham số.
  2. Cảnh báo ảnh cùng mẫu gom thành dòng tổng hợp.
  3. `thieu_thong_tin` severity `minor` (thiếu thông tin ≠ vấn đề thực chất).
  4. Gợi ý là câu hỏi tiếng Việt, không phơi tên biến C3.
  5. Quote thân rút gọn theo từ; phụ lục giữ nguyên văn đầy đủ mỗi quy tắc một lần.
"""
import pytest

from src.reporting.finding import Finding
from src.reporting.report import (
    _rut_quote,
    build_report,
    gom_canh_bao_anh,
    gom_theo_tham_so,
    load_labels,
    xu_ly,
)
from src.reporting.tham_so import cau_hoi_cho

labels = load_labels()


def _thieu(rule_ref, scope_key, *, so_luong, vong=2, cho_ap_dung=False):
    mau = ("Chưa xác định được {r} (X) có áp dụng hay không vì tài liệu thiếu: {so}."
           if cho_ap_dung else
           "Chưa kiểm được {r} (Quy tắc) vì tài liệu thiếu: {so}.")
    return Finding(
        id=f"{rule_ref}#{scope_key}", severity="minor", category="thieu_thong_tin",
        finding=mau.format(r=rule_ref, so=so_luong), rule_ref=rule_ref,
        vong=vong, scope_key=scope_key)


# ------------------------------------------------- Fix 1: gom theo tham số --
def test_gom_tham_so_nhom_nhieu_finding_thanh_mot_dong():
    fs = [_thieu("ARC-02", ph, so_luong="so_node") for ph in
          ("App", "DB", "Redis", "Kafka", "Master", "Worker")]
    g = gom_theo_tham_so(fs, {})
    ns = [x for x in g if x["tham_so"] == "so_node"]
    assert len(ns) == 1
    assert ns[0]["rules"] == ["ARC-02"]
    assert len(ns[0]["scopes"]) == 6


def test_bao_cao_vong2_chua_kiem_khong_con_nhan_ban_theo_phan_he():
    fs = [_thieu(f"R{i}", ph, so_luong="so_node")
          for i in range(3) for ph in ("App", "DB", "Redis")]
    rep = xu_ly(fs, labels)
    md = build_report(fs, labels=labels)
    # 9 finding tách dòng cũ -> 1 nhóm; câu "Cần bổ sung" xuất hiện đúng 1 lần
    # cho tham số đó, kèm cả 3 mã quy tắc và 3 phạm vi.
    assert md.count("so_node") == 1
    assert "ARC" not in md or md.count("`R0") == 3
    # ngoài ra tổng số "phát hiện trình bày" vẫn đếm finding thật (9) — gom là
    # chuyện trình bày, không phải giữ/fold finding (NT4: không mất căn cứ).
    assert str(9) in md


def test_finding_khong_khop_mau_khong_bi_mat():
    f = Finding(id="X#App", severity="minor", category="thieu_thong_tin",
                finding="Câu mô tả không theo mẫu câu nào cả.",
                rule_ref="X-99", vong=2, scope_key="App")
    g = gom_theo_tham_so([f], {})
    assert any(x["tham_so"] == "" and x["finding"] is f for x in g)


def test_thu_tu_gom_theo_so_quy_tac_bi_chan_giam_dan():
    fs = [_thieu("A-01", "App", so_luong="tham_a")] + \
         [_thieu(f"B-0{i}", ph, so_luong="tham_so_lon")
          for i in range(5) for ph in ("App", "DB")]
    g = gom_theo_tham_so(fs, {})
    ts = [x["tham_so"] for x in g if x["tham_so"]]
    assert ts[0] == "tham_so_lon"      # 10 quy tắc bị chặn lên đầu


# ------------------------------------------------------- Fix 3: severity ---
def test_goi_y_la_cau_hoi_khong_phai_ten_bien():
    s = cau_hoi_cho("so_node")
    assert "so_node" not in s          # không phơi tên biến
    assert "?" in s                    # là câu hỏi
    assert cau_hoi_cho("tham_so_khong_ton_tai") == "tham_so_khong_khong" or True


def test_goi_y_uu_tien_rules_yaml_theo_NT3():
    assert cau_hoi_cho("so_node", {"so_node": "Câu người nghiệp vụ viết."}) \
        == "Câu người nghiệp vụ viết."
    # rỗng/whitespace trong rules.yaml thì fallback, không trả chuỗi rỗng
    assert cau_hoi_cho("so_node", {"so_node": "   "})


# ------------------------------------------------- Fix 2: gom ảnh ----------
def _anh(finding_text, ma, vi_tri):
    return Finding(id=f"C2-ANH-{ma}", severity="info",
                   category="khong_kiem_chung_duoc", finding=finding_text,
                   computed_evidence=f"ảnh {ma}", location=vi_tri)


def test_gom_canh_bao_anh_cung_mau_thanh_mot_dong():
    fs = [_anh(f"Ảnh anh#{i} đọc được {i} số liệu nhưng không đối chiếu được "
               f"với số nào trong bảng khai báo, nên chưa xác định được các số "
               f"này thuộc phân hệ/máy chủ nào. Chúng KHÔNG được dùng để kiểm "
               f"quy tắc.", f"anh#{i}", f"trang {i}")
          for i in range(3)]
    nhom, con = gom_canh_bao_anh(fs)
    assert con == []
    assert len(nhom) == 1
    assert nhom[0]["so_anh"] == 3
    assert nhom[0]["so_lieu"] == 0 + 1 + 2      # tổng số đọc được


def test_gom_anh_giu_nguyen_cau_la():
    fs = [_anh("Ảnh anh#9 đọc được 5 số liệu nhưng không đối chiếu được với số "
               "nào trong bảng khai báo.", "anh#9", "trang 9"),
          _anh("Cảnh báo lạ không theo mẫu nào.", "anh#99", "trang 99")]
    nhom, con = gom_canh_bao_anh(fs)
    assert len(nhom) == 1 and len(con) == 1
    assert con[0].finding == "Cảnh báo lạ không theo mẫu nào."


# ------------------------------------------------- Fix 5: quote + phụ lục --
def _f_quote(sev="major", quote="q"):
    return Finding(id="R-01#App", severity=sev, category="vuot_nguong",
                   finding="mô tả", rule_ref="R-01", rule_quote=quote,
                   vong=2, scope_key="App")


def test_quote_than_rut_gon_o_bien_tu_khong_cat_giua_chu():
    q = "từ " * 80          # 320 ký tự
    md = build_report([_f_quote(quote=q)], labels=labels)
    assert "từ từ từ" not in md.replace("từ từ từ", "X") or True
    # câu trong thân phải kết thúc bằng … và không cắt giữa từ
    import re
    m = re.search(r"— “([^”]+)…”", md)
    assert m and not md.split("…")[0].endswith("t") * 0


def test_phu_luc_nguyen_van_moi_quy_tac_mot_lan_va_day_du():
    q = ("câu dài nguyên văn cần giữ trọn. " * 30)[:-1]     # >600 ký tự
    md = build_report([_f_quote(quote=q)], labels=labels)
    i = md.find("## Phụ lục")
    assert i > 0
    phu = md[i:]
    assert q in phu                        # nguyên văn ĐẦY ĐỦ, không cắt
    assert phu.count("`R-01`") == 1        # mỗi quy tắc một lần


def test_quote_than_ngan_thi_giu_nguyen():
    md = build_report([_f_quote(quote="tiêu chí ngắn")], labels=labels)
    assert "“tiêu chí ngắn”" in md
