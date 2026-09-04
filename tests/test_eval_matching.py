"""Test 1.13 — phần so khớp của eval harness. Thuần code, chạy offline."""
import pytest

from eval.matching import KetQuaEval, bang_markdown, doi_chieu, nap_nhan
from src.reporting.finding import Finding


def _f(rule_ref: str) -> Finding:
    return Finding(id=rule_ref, severity="major", category="thieu_thong_tin",
                   finding="x", rule_ref=rule_ref)


def _nhan(lid, dossier, refs, **kw):
    return {"label_id": lid, "dossier": dossier, "rule_ref": refs,
            "khoang_trong": kw.get("khoang_trong", False),
            "khong_neo_duoc": kw.get("khong_neo_duoc", False)}


def test_trung_khi_ma_finding_nam_trong_danh_sach_cua_nhan():
    labels = [_nhan("l1", "HS1", ["PRC-01", "PRC-02"])]
    kq = doi_chieu({"HS1": [_f("PRC-02")]}, labels)
    assert kq.trung == 1 and kq.recall_quy_tac == 1.0


def test_khong_trung_khi_khac_ho_so():
    """Cùng mã nhưng khác hồ sơ thì KHÔNG tính — nếu không recall sẽ ảo."""
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    kq = doi_chieu({"HS2": [_f("PRC-01")]}, labels)
    assert kq.trung == 0


def test_hai_mau_so_tach_roi_theo_scoring_note():
    """`khoang_trong` không có rule_ref -> chỉ vào mẫu số "mọi yêu cầu"."""
    labels = [_nhan("l1", "HS1", ["PRC-01"]),
              _nhan("l2", "HS1", [], khoang_trong=True)]
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, labels)
    assert kq.nhan_co_rule == 1 and kq.nhan_tong == 2
    assert kq.recall_quy_tac == 1.0
    assert kq.recall_moi_yeu_cau == 0.5      # luôn thấp hơn, và đây là số nói với người dùng


def test_ho_so_khong_chay_duoc_VAN_tinh_vao_mau_so():
    """Bỏ hồ sơ hỏng ra khỏi mẫu số sẽ làm recall đẹp lên một cách giả tạo."""
    labels = [_nhan("l1", "HS1", ["PRC-01"]), _nhan("l2", "HS2", ["CPU-03"])]
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, labels)      # HS2 không chạy được
    assert kq.nhan_co_rule == 2 and kq.trung == 1
    assert kq.recall_quy_tac == 0.5
    hs2 = next(h for h in kq.ho_so if h.dossier == "HS2")
    assert "chưa chạy được" in hs2.ghi_chu


def test_mot_nhan_chi_duoc_tinh_MOT_lan_du_khop_nhieu_ma():
    labels = [_nhan("l1", "HS1", ["PRC-01", "PRC-02"])]
    kq = doi_chieu({"HS1": [_f("PRC-01"), _f("PRC-02")]}, labels)
    assert kq.trung == 1


def test_finding_khong_khop_duoc_liet_ke_nhung_KHONG_goi_la_false_positive():
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    kq = doi_chieu({"HS1": [_f("PRC-01"), _f("STO-03")]}, labels)
    h = kq.ho_so[0]
    assert h.finding_khong_khop == ["STO-03"]
    bc = bang_markdown(kq)
    assert "Không đo được false positive" in bc


def test_bao_cao_LUON_kem_han_che(tmp_path):
    bc = bang_markdown(doi_chieu({}, [_nhan("l1", "HS1", ["PRC-01"])]))
    assert "hào phóng hơn thực tế" in bc
    assert "chưa qua kiểm định độc lập" in bc


# --- nối với eval set THẬT --------------------------------------------------
def test_nap_dung_tap_dev_va_khong_lan_sang_test():
    dev = nap_nhan("dev")
    test = nap_nhan("test")
    assert len(dev) == 317 and len(test) == 158
    assert not ({l["dossier"] for l in dev} & {l["dossier"] for l in test})


def test_mau_so_tren_eval_set_that_khop_voi_meta():
    tat_ca = nap_nhan("tat_ca")
    assert len(tat_ca) == 475
    assert sum(1 for l in tat_ca if l.get("rule_ref")) == 469
