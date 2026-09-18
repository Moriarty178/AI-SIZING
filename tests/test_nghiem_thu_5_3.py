"""Chấm nghiệm thu 5.3 — thuần hàm, không cần dịch vụ."""
import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "nghiem_thu_5_3.py"
_spec = importlib.util.spec_from_file_location("nghiem_thu_5_3", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)

DEM = {"dat": 1, "chua_dat": 54, "chua_kiem_duoc": 664, "phat_sinh": 0}


def _viec(*, phat_lai="dùng lại 268/268 lượt hỏi", c3=(0, 0), c5=(0, 0), hong=(0, 0),
          thay_doi=None, so_finding=719, **pl):
    return {"ma": "x", "so_finding": so_finding, "giay_da_chay": 60.0,
            "phat_lai": phat_lai, "thay_doi": thay_doi or {},
            "thong_ke_cache": {"ghi_them": 0},
            "thong_ke": {"c3": {"luot_goi_hong": hong[0]}, "c5": {"luot_goi_hong": hong[1]},
                         "phat_lai": {"c3": {"dung_lai": c3[0], "goi_moi": c3[1]},
                                      "c5": {"dung_lai": c5[0], "goi_moi": c5[1]}, **pl}}}


def _ket(**kw):
    l1 = kw.pop("l1", _viec(phat_lai="không dùng lại được — …", c3=(0, 121), c5=(0, 147)))
    l2 = kw.pop("l2", _viec(c3=(121, 0), c5=(147, 0), thay_doi={"giong_het": True}))
    l3 = kw.pop("l3", _viec(c3=(100, 21), c5=(90, 57),
                            thay_doi={"giong_het": False, "sua": 1, "them": 1, "xoa": 0,
                                      "vi_tri": ["Mục 1.1, trang 18 · bảng · sửa"]},
                            vung_doi=["frontend"], chung_doi=False))
    return {k["ma"]: k for k in nt.cham(l1=l1, l2=l2, l3=l3, dem_1=kw.pop("dem_1", DEM),
                                         dem_2=kw.pop("dem_2", DEM))}


def test_du_tieu_chi_thi_dat():
    k = _ket()
    assert [m for m in ("R1", "R2", "R3", "R4", "R5", "R6") if k[m]["dat"] is not True] == []
    assert "frontend" in k["Đ2"]["chi_tiet"]


def test_L2_hoi_lai_luot_KHONG_hong_o_L1_thi_R2_truot():
    k = _ket(l2=_viec(c3=(120, 1), c5=(147, 0), thay_doi={"giong_het": True}))
    assert k["R2"]["dat"] is False and k["R3"]["dat"] is None


def test_L2_hoi_lai_dung_luot_hong_cua_L1_thi_R2_dat_va_R3_chi_do():
    k = _ket(l1=_viec(phat_lai="không dùng lại được", c3=(0, 121), c5=(0, 147), hong=(2, 0)),
             l2=_viec(c3=(119, 2), c5=(147, 0), thay_doi={"giong_het": True}))
    assert k["R2"]["dat"] is True and k["R3"]["dat"] is None


def test_L2_khong_tim_thay_ban_ghi_L1_thi_R2_truot():
    k = _ket(l2=_viec(phat_lai="không dùng lại được — …", c3=(0, 121), c5=(0, 147),
                      thay_doi={"giong_het": True}))
    assert k["R2"]["dat"] is False


def test_L2_ket_qua_lech_du_khong_hoi_lai_thi_R3_truot():
    k = _ket(dem_2={**DEM, "dat": 11, "chua_dat": 44})
    assert k["R3"]["dat"] is False


def test_L3_hoi_lai_het_C3_thi_R5_truot():
    k = _ket(l3=_viec(c3=(0, 121), c5=(0, 147), thay_doi={"giong_het": False, "sua": 1}))
    assert k["R5"]["dat"] is False


def test_L3_hoi_lai_HET_C5_du_phan_chung_khong_doi_thi_R6_truot():
    k = _ket(l3=_viec(c3=(100, 21), c5=(0, 147), chung_doi=False,
                      thay_doi={"giong_het": False, "sua": 1}))
    assert k["R6"]["dat"] is False


def test_phan_CHUNG_doi_thi_R6_chi_do():
    k = _ket(l3=_viec(c3=(100, 21), c5=(0, 147), chung_doi=True,
                      thay_doi={"giong_het": False, "sua": 1}))
    assert k["R6"]["dat"] is None and "phần CHUNG đổi" in k["R6"]["chi_tiet"]


def test_nop_nham_ban_goc_o_L3_thi_R4_truot():
    k = _ket(l3=_viec(c3=(121, 0), c5=(147, 0), thay_doi={"giong_het": True}))
    assert k["R4"]["dat"] is False


def test_doi_trang_thai_chia_trong_ngoai_vung_doi():
    truoc = {"baseline": [
        {"id": 1, "khoa": "CPU-01#frontend", "scope_goc": "FrontEnd", "trang_thai": "chua_dat"},
        {"id": 2, "khoa": "EVD-19#mongo", "scope_goc": "Mongo", "trang_thai": "chua_dat"},
        {"id": 3, "khoa": "PRC-11#he_thong", "scope_goc": "", "trang_thai": "chua_dat"}]}
    sau = {"baseline": [
        {"id": 1, "khoa": "CPU-01#frontend", "scope_goc": "FrontEnd (Web)",
         "trang_thai": "dat", "ket_luan_boi": "khong_ro"},
        {"id": 2, "khoa": "EVD-19#mongo", "scope_goc": "Mongo", "trang_thai": "dat",
         "ket_luan_boi": "khong_ro"},
        {"id": 3, "khoa": "PRC-11#he_thong", "scope_goc": "", "trang_thai": "chua_dat",
         "ket_luan_boi": "c5"}]}
    d = nt.doi_trang_thai(truoc, sau, ["frontend"])
    assert (d["tong"], d["trong_vung_doi"], d["ngoai_vung_doi"]) == (2, 1, 1)
    assert d["vi_du"][1] == "EVD-19#mongo: chua_dat → dat (ngoài vùng đổi)"
