"""Test 1.10 — C7 báo cáo Markdown. Chạy offline, dùng nhãn thật `report_labels.yaml`.

Các test đều là hồi quy cho một yêu cầu cụ thể của mục 1.10:
luật chặn Vòng 2, thứ tự checklist, khử trùng, và cổng NT2 (lọc + ĐẾM).
"""
import pytest

from src.reporting.finding import Finding
from src.reporting.report import (
    MucTruot,
    build_report,
    chan_vong2,
    khu_trung,
    load_labels,
    muc_truot_vong1,
    xu_ly,
)


@pytest.fixture(scope="module")
def labels():
    return load_labels()


def _f(id, *, vong, category, checklist_ref=(), scope_key="", severity="major",
       rule_ref="", computed_evidence="", finding="x") -> Finding:
    # Bảo đảm có căn cứ (NT2) trừ khi test cố tình bỏ.
    if not rule_ref and not computed_evidence:
        rule_ref = id.split("#")[0]
    return Finding(id=id, severity=severity, category=category, finding=finding,
                   rule_ref=rule_ref, computed_evidence=computed_evidence,
                   checklist_ref=list(checklist_ref), vong=vong, scope_key=scope_key)


# ---------------------------------------------------------- NT2: lọc + đếm --
def test_finding_thieu_can_cu_bi_loc_VA_duoc_dem(labels):
    ok = _f("KPI-02", vong=2, category="vuot_nguong", rule_ref="KPI-02")
    bad = Finding(id="X", severity="major", category="vuot_nguong", finding="z")  # không căn cứ
    rep = xu_ly([ok, bad], labels)
    assert rep.so_loc_khong_can_cu == 1          # ĐẾM, không im lặng
    assert bad not in rep.vong2_chua_dat
    assert ok in rep.vong2_chua_dat


# ---------------------------------------------------------- khử trùng ------
def test_khu_trung_gop_finding_lap_va_dem():
    a = _f("KPI-02#App", vong=2, category="vuot_nguong", rule_ref="KPI-02",
           scope_key="App", finding="CPU vượt ngưỡng")
    b = _f("KPI-02#App", vong=2, category="vuot_nguong", rule_ref="KPI-02",
           scope_key="App", finding="CPU vượt ngưỡng")   # trùng hệt
    c = _f("KPI-02#DB", vong=2, category="vuot_nguong", rule_ref="KPI-02",
           scope_key="DB", finding="CPU vượt ngưỡng")    # khác phân hệ -> giữ
    kept, n = khu_trung([a, b, c])
    assert n == 1
    assert len(kept) == 2


# ---------------------------------------------------------- luật chặn ------
def test_truot_vong1_he_thong_chan_moi_pham_vi(labels):
    truot = _f("CL-1", vong=1, category="thieu_thong_tin", checklist_ref=["CL-2.9"],
               scope_key="", rule_ref="PRC-11")
    v2_app = _f("EVD-10#App", vong=2, category="khong_nhat_quan", checklist_ref=["CL-2.9"],
                scope_key="App", rule_ref="EVD-10")
    thong, chan = chan_vong2([v2_app], muc_truot_vong1([truot], labels.vong1_truot))
    assert v2_app in chan and v2_app not in thong


def test_truot_vong1_phan_he_chan_ca_cong_nghe_luu_tru(labels):
    """Trượt ở 'App' phải chặn cả 'App' lẫn 'App/SSD'."""
    truot = _f("CL", vong=1, category="thieu_muc", checklist_ref=["CL-3.x.15"],
               scope_key="App", rule_ref="X-01")
    v2_app = _f("STO#App", vong=2, category="vuot_nguong", checklist_ref=["CL-3.x.15"],
                scope_key="App", rule_ref="STO-01")
    v2_ssd = _f("STO#App/SSD", vong=2, category="vuot_nguong", checklist_ref=["CL-3.x.15"],
                scope_key="App/SSD", rule_ref="STO-01")
    v2_db = _f("STO#DB", vong=2, category="vuot_nguong", checklist_ref=["CL-3.x.15"],
               scope_key="DB", rule_ref="STO-01")
    thong, chan = chan_vong2([v2_app, v2_ssd, v2_db],
                             muc_truot_vong1([truot], labels.vong1_truot))
    assert v2_app in chan and v2_ssd in chan     # App và App/SSD bị chặn
    assert v2_db in thong                          # DB không bị chặn


def test_khong_kiem_chung_duoc_o_vong1_KHONG_chan(labels):
    """Không biết KHÔNG đồng nghĩa với thiếu — không được chặn Vòng 2."""
    mo_ho = _f("CL", vong=1, category="khong_kiem_chung_duoc", checklist_ref=["CL-2.9"],
               scope_key="", rule_ref="X")
    v2 = _f("EVD-10", vong=2, category="khong_nhat_quan", checklist_ref=["CL-2.9"],
            rule_ref="EVD-10")
    truot = muc_truot_vong1([mo_ho], labels.vong1_truot)
    assert truot == []
    thong, chan = chan_vong2([v2], truot)
    assert v2 in thong and chan == []


def test_tam_hoan_gom_theo_phan_he_trong_bao_cao(labels):
    truot = _f("CL", vong=1, category="thieu_thong_tin", checklist_ref=["CL-3.x.13"],
               scope_key="App", rule_ref="X-01")
    v2 = _f("CPU#App", vong=2, category="sai_cong_thuc", checklist_ref=["CL-3.x.13"],
            scope_key="App", rule_ref="CPU-05")
    rep = xu_ly([truot, v2], labels)
    assert v2 in rep.vong2_tam_hoan
    assert v2 not in rep.vong2_chua_dat
    md = build_report([truot, v2], labels=labels)
    assert "Tạm hoãn" in md and "CPU-05" in md


# ---------------------------------------------------------- thứ tự --------
def test_thu_tu_checklist_I_II_III_va_khoi_chung_truoc_DB(labels):
    # Cố tình xáo trộn đầu vào; kỳ vọng sắp lại theo thứ tự checklist.
    a3db = _f("a", vong=1, category="thieu_thong_tin", checklist_ref=["CL-3.2.19"],
              scope_key="DB", rule_ref="BAK-01")
    a3shared = _f("b", vong=1, category="thieu_thong_tin", checklist_ref=["CL-3.x.1"],
                  scope_key="App", rule_ref="EVD-01")
    a1 = _f("c", vong=1, category="thieu_thong_tin", checklist_ref=["CL-1.1"],
            rule_ref="PRC-01")
    a2 = _f("d", vong=1, category="thieu_thong_tin", checklist_ref=["CL-2.2"],
            rule_ref="EVD-02")
    rep = xu_ly([a3db, a3shared, a1, a2], labels)
    order = [f.checklist_ref[0] for f in rep.vong1]
    assert order == ["CL-1.1", "CL-2.2", "CL-3.x.1", "CL-3.2.19"]


def test_severity_xep_nghiem_trong_truoc(labels):
    minor = _f("m", vong=2, category="vuot_nguong", severity="minor", rule_ref="A-01")
    crit = _f("c", vong=2, category="vuot_nguong", severity="critical", rule_ref="B-01")
    major = _f("j", vong=2, category="vuot_nguong", severity="major", rule_ref="C-01")
    rep = xu_ly([minor, crit, major], labels)
    assert [f.severity for f in rep.vong2_chua_dat] == ["critical", "major", "minor"]


# ---------------------------------------------------------- báo cáo -------
def test_bao_cao_mo_dau_bang_cau_co_van(labels):
    md = build_report([], ten_he_thong="Hệ X", labels=labels)
    assert "cố vấn" in md.lower()
    assert "Hệ X" in md


def test_bao_cao_ghi_ro_demo_khi_is_demo(labels):
    md = build_report([], is_demo=True, labels=labels)
    assert "Demo" in md or "demo" in md


def test_bao_cao_rong_van_chay_khong_vo(labels):
    md = build_report([], labels=labels)
    assert md.strip().startswith("# Báo cáo")
    assert "Vòng 1" in md and "Vòng 2" in md


# --- D2: cắt nhiễu báo cáo (2026-09-10) -------------------------------------
def _f_pham_vi(scope, rule="ARC-03", cau="Chưa kiểm được ARC-03 vì thiếu: so_may",
               cat="thieu_thong_tin"):
    from src.reporting.finding import Finding
    return Finding(id=rule, severity="major", category=cat, finding=cau,
                   rule_ref=rule, rule_quote="TIÊU CHÍ DÀI " * 20,
                   scope_key=scope, vong=2, suggestion="Bổ sung so_may.")


class TestGopPhamVi:
    def test_cung_mot_van_de_tren_nhieu_phan_he_noi_MOT_lan(self):
        """Đo trên báo cáo thật VTracking 2026-09-10: 718 finding nhưng chỉ 151
        câu khác nhau — mỗi quy tắc lặp đúng 13 lần cho 13 phân hệ, văn bản y
        hệt. `khu_trung` không đụng được vì khoá của nó có `scope_key`."""
        from src.reporting.report import gop_pham_vi
        fs = [_f_pham_vi(f"phan-he-{i}") for i in range(13)]
        nhom = gop_pham_vi(fs)
        assert len(nhom) == 1
        _, scopes = nhom[0]
        assert len(scopes) == 13

    def test_KHONG_gop_khi_van_de_khac_nhau(self):
        from src.reporting.report import gop_pham_vi
        fs = [_f_pham_vi("A"), _f_pham_vi("B", cau="Chưa kiểm được ARC-09"),
              _f_pham_vi("C", rule="STO-18")]
        assert len(gop_pham_vi(fs)) == 3

    def test_moi_phan_he_van_con_nguyen_trong_bao_cao(self):
        """Gộp KHÔNG phải giấu bớt (NT4): tên từng phân hệ và tổng số đều còn."""
        from src.reporting.report import _render_list, load_labels
        van = "\n".join(_render_list([_f_pham_vi(f"ph{i}") for i in range(5)],
                                     load_labels()))
        for i in range(5):
            assert f"ph{i}" in van
        assert "(5 phân hệ)" in van

    def test_qua_nhieu_phan_he_thi_cat_bot_NHUNG_NOI_RA(self):
        from src.reporting.report import _render_list, load_labels
        van = "\n".join(_render_list([_f_pham_vi(f"ph{i}") for i in range(30)],
                                     load_labels()))
        assert "và 18 phân hệ nữa" in van and "(30 phân hệ)" in van

    def test_trich_dan_quy_tac_chi_con_MOT_lan(self):
        """Dòng «Căn cứ» chiếm 30% báo cáo thật vì trích nguyên tiêu chí 713 lần
        thay vì 99."""
        from src.reporting.report import _render_list, load_labels
        van = "\n".join(_render_list([_f_pham_vi(f"ph{i}") for i in range(13)],
                                     load_labels()))
        assert van.count("TIÊU CHÍ DÀI") == 20      # một lần, không phải 13


class TestBangChuaKiem:
    def test_muc_chua_kiem_duoc_dung_thanh_BANG(self):
        """586/724 phát hiện của một tài liệu thật nằm ở mục này, mà nó nói
        *công cụ không đọc được*, KHÔNG nói *tài liệu sai*."""
        from src.reporting.report import _bang_chua_kiem, load_labels
        fs = [_f_pham_vi(f"ph{i}", rule=f"ARC-{i:02d}") for i in range(20)]
        van = "\n".join(_bang_chua_kiem(fs, load_labels()))
        assert "| Quy tắc | Mức | Vì sao chưa kiểm được | Phạm vi |" in van
        assert "KHÔNG ĐỌC ĐƯỢC — không phải chỗ bản sizing sai" in van
        assert "TIÊU CHÍ DÀI" not in van, "bảng KHÔNG lặp lại nguyên văn tiêu chí"
        assert "config/rules.yaml" in van, "phải chỉ chỗ tra nguyên văn, không bỏ im"

    def test_dau_gach_dung_trong_van_ban_khong_lam_vo_bang(self):
        from src.reporting.report import _bang_chua_kiem, load_labels
        fs = [_f_pham_vi("A", cau="Thiếu a|b|c")]
        van = "\n".join(_bang_chua_kiem(fs, load_labels()))
        assert r"a\|b\|c" in van

    def test_rong_thi_noi_ro_chu_khong_ra_bang_trong(self):
        from src.reporting.report import _bang_chua_kiem, load_labels
        assert _bang_chua_kiem([], load_labels()) == \
            ["_(không có mục nào thiếu thông tin để kiểm)_"]


def test_tong_quan_noi_ro_da_gop_bao_nhieu():
    from src.reporting.report import build_report
    van = build_report([_f_pham_vi(f"ph{i}") for i in range(13)])
    assert "Tổng số phát hiện: **13**" in van
    assert "trình bày thành **1** mục" in van


class TestTomTatDauBaoCao:
    def test_phat_hien_THAT_duoc_neu_len_dau(self):
        """Đo trên báo cáo thật 2026-09-10: sau khi đã cắt 88% số dòng, ba phát
        hiện nói *"số của anh sai"* vẫn nằm ở dòng 267/418 — chôn ở 60% độ sâu."""
        from src.reporting.finding import Finding
        from src.reporting.report import build_report
        sai = Finding(id="LBA-01", severity="critical", category="sai_cong_thuc",
                      finding="Công thức thông lượng thiếu hệ số 1.2",
                      rule_ref="LBA-01", location="Mục 1.1, trang 18", vong=2)
        van = build_report([sai] + [_f_pham_vi(f"ph{i}") for i in range(30)])
        dau = van.index("Cần xử lý trước khi nộp")
        assert dau < van.index("## Vòng 1"), "tóm tắt phải đứng TRƯỚC Vòng 1"
        assert "1 chỗ số liệu CHƯA ĐẠT" in van
        assert "Công thức thông lượng thiếu hệ số 1.2" in van[dau:van.index("## Vòng 1")]
        assert "Mục 1.1, trang 18" in van

    def test_noi_ro_phan_KHONG_doc_duoc_khong_phai_loi_cua_tai_lieu(self):
        from src.reporting.report import build_report
        van = build_report([_f_pham_vi(f"ph{i}") for i in range(13)])
        assert "13 mục công cụ CHƯA ĐỌC ĐƯỢC" in van
        assert "không phải lỗi của bản sizing" in van

    def test_khong_co_gi_sai_thi_noi_thang_chu_khong_de_trong(self):
        from src.reporting.report import build_report
        van = build_report([_f_pham_vi("A")])
        assert "không tìm thấy chỗ nào tính sai" in van

    def test_KHONG_dao_thu_tu_cac_muc_ben_duoi(self):
        """Vòng 1 đứng trước Vòng 2 là theo trình tự thẩm định (Vòng 1 trượt thì
        chặn Vòng 2). Tóm tắt chỉ NÊU LÊN, không sắp xếp lại."""
        from src.reporting.report import build_report
        van = build_report([_f_pham_vi("A")])
        assert van.index("## Vòng 1") < van.index("## Vòng 2")
