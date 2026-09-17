"""Chấm tiêu chí nghiệm thu 5.2. OFFLINE."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.nghiem_thu_5_2 import cham   # noqa: E402


def _cham(**kw):
    d = dict(cach_tim=["phan_tu"] * 5 + ["ten_phan_he"] * 3 + ["khong_tim_duoc"] * 2,
             ghi_chu_mat=0, so_lan=[1, 2], so_lich_su=2, ten_luu="Trần Thị Bình",
             ten_gui="Trần Thị Bình", ma_khong_danh_tinh=400, so_dong=10)
    d.update(kw)
    return {k["ma"]: k for k in cham(**d)}


def test_du_het_la_dat():
    kq = _cham()
    assert all(kq[m]["dat"] is True for m in ("S1", "S2", "S3", "S4", "S5"))


def test_phan_bo_dinh_vi_la_DO_khong_cham():
    """Chưa có số đo nào để đặt ngưỡng — chấm đạt/không lúc này là bịa ngưỡng."""
    d1 = _cham()["Đ1"]
    assert d1["dat"] is None
    assert "50.0%" in d1["chi_tiet"] and "30.0%" in d1["chi_tiet"]


def test_tai_lieu_mat_la_hong_S2():
    assert _cham(ghi_chu_mat=719)["S2"]["dat"] is False


def test_thieu_dong_la_hong_S1():
    assert _cham(so_dong=11)["S1"]["dat"] is False


def test_hoso_rong_KHONG_duoc_tinh_la_dat_S1():
    assert _cham(cach_tim=[], so_dong=0)["S1"]["dat"] is False


def test_so_lan_sai_thu_tu_la_hong_S3():
    assert _cham(so_lan=[3, 4])["S3"]["dat"] is False


def test_ten_vo_la_hong_S4():
    assert _cham(ten_luu="TrÃ¡ÂºÂ§n")["S4"]["dat"] is False


def test_khong_danh_tinh_ma_van_ghi_duoc_la_hong_S5():
    assert _cham(ma_khong_danh_tinh=201)["S5"]["dat"] is False
