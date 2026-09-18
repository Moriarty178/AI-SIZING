"""Chấm nghiệm thu 5.6/5.9 — thuần hàm, không cần dịch vụ."""
import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "nghiem_thu_5_6.py"
_spec = importlib.util.spec_from_file_location("nghiem_thu_5_6", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)

TEN = "phongnh40"


def _ga(**kw):
    d = {"ghi_chu": nt.GHI_CHU, "ten": TEN, "vai": "admin", "danh_gia": "can_ban",
         "loi_o_phia": "he_thong_ai"}
    d.update(kw)
    return {"ghi_chu_admin": d}


def _ket(**kw):
    d = dict(so_dong=719, so_baseline=719, so_lan_sua_max=2, co_dau_vao=9, so_c4=11,
             da_tham_dinh_lai=True, doc_lai=[_ga(), _ga()],
             luu_lai={"da_luu": 0, "bo_qua": 2}, ma_nguoi_thuong=403,
             ma_khong_danh_tinh=400, ten_gui=TEN)
    d.update(kw)
    return {k["ma"]: k for k in nt.cham(**d)}


def test_du_tieu_chi_thi_dat():
    k = _ket()
    assert [m for m in ("A1", "A2", "A3", "A4", "A5") if k[m]["dat"] is not True] == []


def test_thieu_dong_thi_A1_truot():
    assert _ket(so_dong=700)["A1"]["dat"] is False


def test_chua_tham_dinh_lai_thi_A2_chi_do():
    k = _ket(da_tham_dinh_lai=False, co_dau_vao=0)
    assert k["A2"]["dat"] is None and "chỉ đo" in k["A2"]["chi_tiet"]


def test_tham_dinh_lai_ma_khong_co_dau_vao_nao_thi_A2_truot():
    assert _ket(co_dau_vao=0)["A2"]["dat"] is False


def test_ghi_chu_luu_nham_vai_thi_A3_truot():
    assert _ket(doc_lai=[_ga(), _ga(vai="nguoi_lam_sizing")])["A3"]["dat"] is False


def test_khong_chan_vai_thuong_thi_A4_truot():
    assert _ket(ma_nguoi_thuong=200)["A4"]["dat"] is False


def test_luu_lai_ma_them_dong_lich_su_thi_A5_truot():
    assert _ket(luu_lai={"da_luu": 2, "bo_qua": 0})["A5"]["dat"] is False
