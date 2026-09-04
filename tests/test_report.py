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
