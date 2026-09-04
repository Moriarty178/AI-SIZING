"""Test 1.6 + 1.8 + 1.9 — schema, bộ nạp quy tắc, và C4. Chạy offline.

Dùng bộ quy tắc THẬT (`config/rules.yaml`) chứ không phải bộ giả, vì phần lớn rủi
ro nằm ở chỗ code và dữ liệu quy tắc không khớp nhau.
"""
import pytest

from src.extraction.schema import ExtractedValue, SizingCore, SizingExtension
from src.reporting.finding import Finding, loc_bo_khong_can_cu
from src.validators.quantitative import QuantitativeValidator
from src.validators.rules_loader import Rule, RuleInput, RuleSet, load_rules


@pytest.fixture(scope="module")
def rules() -> RuleSet:
    return load_rules()


# ------------------------------------------------------------ 1.8 loader --
def test_nap_du_151_quy_tac_va_46_hang_so(rules):
    assert len(rules) == 151
    assert rules.globals["cpu_kpi"] == 0.75
    assert rules.globals["ram_kpi"] == 0.9


def test_loc_theo_loai_vong_scope(rules):
    # `select` mặc định BỎ quy tắc đang tắt — phải nói rõ enabled=None mới đủ 101
    assert len(rules.select(type="quantitative", enabled=None)) == 101
    assert len(rules.select(type="quantitative")) == 99   # trừ KPI-15, KPI-16
    assert all(r.round == 1 for r in rules.select(round=1))
    assert all(r.scope == "phan_he" for r in rules.select(scope="phan_he"))


def test_bao_loi_khi_ma_quy_tac_trung():
    with pytest.raises(ValueError, match="trùng"):
        RuleSet({"rules": [{"id": "X-01", "name": "a", "type": "quantitative",
                            "severity": "major", "source_doc": "s"},
                           {"id": "X-01", "name": "b", "type": "quantitative",
                            "severity": "major", "source_doc": "s"}]})


def test_bao_loi_khi_see_also_tro_vao_ma_khong_co_that():
    with pytest.raises(ValueError, match="see_also"):
        RuleSet({"rules": [{"id": "X-01", "name": "a", "type": "quantitative",
                            "severity": "major", "source_doc": "s",
                            "see_also": ["KHONG-CO"]}]})


def test_quy_tac_khong_chay_duoc_deu_co_LY_DO_ro_rang(rules):
    """Im lặng bỏ qua một quy tắc là cách âm thầm làm hụt recall."""
    for r, why in rules.blocked():
        assert why, f"{r.id} bị chặn mà không nêu lý do"


def test_co_khoa_lookup_chi_lam_cong_dieu_kien_thi_KHONG_can_bang_tra(rules):
    """`role: lookup` gánh hai vai; gộp lại sẽ chặn nhầm 8 quy tắc chạy được."""
    fwl = rules["FWL-04"]
    assert fwl.lookup_keys                      # có khoá lookup
    assert not fwl.lookup_keys_can_bang_tra     # nhưng chỉ dùng trong applies_when
    assert "bảng tra" not in fwl.khong_danh_gia_duoc()


def test_quy_tac_thuc_su_can_bang_tra_thi_bi_chan_kem_ly_do(rules):
    sto03 = rules["STO-03"]
    assert [i.name for i in sto03.lookup_keys_can_bang_tra] == ["loai_o"]
    assert "bảng tra" in sto03.khong_danh_gia_duoc()


# ------------------------------------------------------------ 1.6 schema --
def test_gia_tri_thieu_la_None_chu_khong_phai_0():
    ev = ExtractedValue()
    assert ev.missing and ev.value is None


def test_tra_tham_so_uu_tien_phan_he_roi_lui_ve_tai_lieu():
    doc = SizingCore(params={"cpu_95th": ExtractedValue(value=50)},
                     phan_he=[SizingExtension(ten_phan_he="App",
                                              params={"cpu_95th": ExtractedValue(value=80)})])
    assert doc.get("cpu_95th", "App").value == 80     # phân hệ thắng
    assert doc.get("cpu_95th", "DB").value == 50      # lùi về cấp tài liệu
    assert doc.get("cpu_95th").value == 50


def test_scope_keys_theo_tung_pham_vi():
    doc = SizingCore(phan_he=[
        SizingExtension(ten_phan_he="App"),
        SizingExtension(ten_phan_he="DB", cong_nghe_luu_tru="SSD"),
    ])
    assert doc.scope_keys("he_thong") == [""]
    assert doc.scope_keys("phan_he") == ["App", "DB"]
    assert doc.scope_keys("phan_he_x_cong_nghe_luu_tru") == ["DB/SSD"]


# ------------------------------------------------------------ NT2 --------
def test_finding_khong_co_can_cu_thi_bi_loc_bo():
    ok = Finding(id="1", severity="major", category="vuot_nguong",
                 finding="x", rule_ref="KPI-02")
    ev = Finding(id="2", severity="major", category="vuot_nguong",
                 finding="y", computed_evidence="1 > 0")
    bad = Finding(id="3", severity="major", category="vuot_nguong", finding="z")
    keep, drop = loc_bo_khong_can_cu([ok, ev, bad])
    assert [f.id for f in keep] == ["1", "2"]
    assert [f.id for f in drop] == ["3"]


# ------------------------------------------------------------ 1.9 C4 -----
def _doc(**params) -> SizingCore:
    d = SizingCore()
    for k, v in params.items():
        d.set_param(k, v, location="Mục III.4, trang 8")
    return d


def test_check_dat_thi_khong_sinh_finding(rules):
    v = QuantitativeValidator(rules)
    out = v.check_rule(rules["KPI-02"], _doc(cpu_95th=60))
    assert out.status == "dat" and out.finding is None


def test_check_vi_pham_thi_sinh_finding_co_can_cu_tinh_duoc(rules):
    v = QuantitativeValidator(rules)
    out = v.check_rule(rules["KPI-02"], _doc(cpu_95th=92))
    assert out.status == "vi_pham"
    f = out.finding
    assert f.category == "vuot_nguong"
    assert f.rule_ref == "KPI-02" and f.severity == "critical"
    assert "92" in f.computed_evidence          # NT2
    assert f.location == "Mục III.4, trang 8"
    assert f.vong == 2 and f.source_doc


def test_hang_so_globals_duoc_dua_vao_bieu_thuc(rules):
    """`cpu_kpi` không có trong tài liệu — nó là hằng số Guideline."""
    v = QuantitativeValidator(rules)
    assert v.check_rule(rules["KPI-02"], _doc(cpu_95th=75)).status == "dat"
    assert v.check_rule(rules["KPI-02"], _doc(cpu_95th=75.1)).status == "vi_pham"


def test_thieu_dau_vao_thi_KHONG_doan_ma_bao_thieu_thong_tin(rules):
    """NT4 + cạm bẫy đã ghi: không tự điền mặc định cho trường thiếu."""
    v = QuantitativeValidator(rules)
    out = v.check_rule(rules["KPI-03"], _doc(ram_su_dung_gb=100))   # thiếu ram_cau_hinh_gb
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "thieu_thong_tin"
    assert "ram_cau_hinh_gb" in out.finding.finding


def test_dau_vao_luong_nghia_thi_xuong_cap_chu_khong_ket_luan(rules):
    """Nối với 1.4: số đọc được hai cách thì không được phán vi phạm."""
    doc = SizingCore()
    doc.params["cpu_95th"] = ExtractedValue(value=92, ambiguous=True, raw="9.2",
                                            note="'9.2' có thể là 92 hoặc 9,2")
    out = QuantitativeValidator(rules).check_rule(rules["KPI-02"], doc)
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "khong_kiem_chung_duoc"
    assert out.finding.severity == "minor"


def test_formula_khop_trong_dung_sai_thi_dat(rules):
    v = QuantitativeValidator(rules)
    doc = _doc(thong_so_he_moi=1000, thong_so_he_tham_chieu=500,
               he_so_so_sanh_khai=2.0)
    assert v.check_rule(rules["KPI-12"], doc).status == "dat"


def test_formula_lech_qua_dung_sai_thi_bao_sai_cong_thuc(rules):
    v = QuantitativeValidator(rules)
    doc = _doc(thong_so_he_moi=1000, thong_so_he_tham_chieu=500,
               he_so_so_sanh_khai=3.0)
    out = v.check_rule(rules["KPI-12"], doc)
    assert out.status == "vi_pham"
    assert out.finding.category == "sai_cong_thuc"
    ev = out.finding.computed_evidence
    assert "2" in ev and "3" in ev and "%" in ev      # NT2: nêu cả hai số và độ lệch


def test_applies_when_sai_thi_khong_ap_dung_va_khong_tinh_vao_recall(rules):
    v = QuantitativeValidator(rules)
    doc = _doc(co_duong_ra_public=False, co_dinh_co_firewall=False, co_dinh_co_lb=False)
    out = v.check_rule(rules["FWL-04"], doc)
    assert out.status == "khong_ap_dung" and out.finding is None


def test_applies_when_dung_thi_van_cham_binh_thuong(rules):
    v = QuantitativeValidator(rules)
    doc = _doc(co_duong_ra_public=True, co_dinh_co_firewall=False, co_dinh_co_lb=False)
    assert v.check_rule(rules["FWL-04"], doc).status == "vi_pham"


def test_quy_tac_thieu_bang_tra_bao_ro_chu_khong_im_lang(rules):
    out = QuantitativeValidator(rules).check_rule(rules["STO-03"], _doc(loai_o="ssd"))
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "khong_kiem_chung_duoc"
    assert out.finding.severity == "info"
    assert "lookup" in out.finding.suggestion


def test_bieu_thuc_KHONG_duoc_chay_lenh_he_thong():
    """Quy tắc là dữ liệu người nghiệp vụ sửa -> phải coi như đầu vào không tin cậy."""
    v = QuantitativeValidator(load_rules())
    val, err = v._eval("__import__('os').system('echo hack')", {})
    assert val is None or err


def test_run_cham_moi_phan_he_cho_quy_tac_scope_phan_he(rules):
    doc = SizingCore(phan_he=[
        SizingExtension(ten_phan_he="App", params={"cpu_95th": ExtractedValue(value=92)}),
        SizingExtension(ten_phan_he="DB", params={"cpu_95th": ExtractedValue(value=50)}),
    ])
    outs = [o for o in QuantitativeValidator(rules).run(doc) if o.rule_id == "KPI-02"]
    by_key = {o.scope_key: o.status for o in outs}
    assert by_key.get("App") == "vi_pham"
    assert by_key.get("DB") == "dat"


def test_findings_chi_tra_ve_cai_co_can_cu(rules):
    doc = SizingCore(phan_he=[SizingExtension(
        ten_phan_he="App", params={"cpu_95th": ExtractedValue(value=92)})])
    for f in QuantitativeValidator(rules).findings(doc):
        assert f.co_can_cu()
