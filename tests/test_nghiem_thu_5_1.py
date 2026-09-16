"""Chấm tiêu chí nghiệm thu 5.1. OFFLINE — script chạy thật trên máy nội bộ tốn
~25 phút, nên phần chấm phải đúng trước khi tốn lượt đó."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.nghiem_thu_5_1 import danh_gia, phat_lai_hoan_toan   # noqa: E402


def _ho_so(n, so_thu_tu, ten="Nguyễn Văn A", **dem):
    d = {"dat": 0, "chua_dat": n, "chua_kiem_duoc": 0, "phat_sinh": 0}
    d.update(dem)
    return {"so_loi_baseline": n, "cac_lan": [{"so_thu_tu": so_thu_tu, "ten": ten,
                                               "dem": d}]}


PHAT_LAI = {"thong_ke_cache": {"bat": True, "ghi_them": 0}}
GOI_THAT = {"thong_ke_cache": {"bat": False, "ghi_them": 0}}


def _cham(ho_so_2, viec_2=PHAT_LAI, ho_so_1=None, so_finding_1=717):
    return {k["ma"]: k["dat"] for k in danh_gia(
        lan1={}, ho_so_1=ho_so_1 or _ho_so(717, 1), so_finding_1=so_finding_1,
        viec_2=viec_2, ho_so_2=ho_so_2, ten="Nguyễn Văn A")}


def test_phat_lai_dung_khong_lech_gi_la_DAT_het():
    assert set(_cham(_ho_so(717, 2)).values()) == {True}


def test_phat_lai_ma_co_mot_dong_dat_la_LOI_CODE():
    """Cùng đầu vào thì không được có dòng «đạt» nào — có là lỗi đường ống."""
    assert _cham(_ho_so(717, 2, dat=1, chua_dat=716))["K6"] is False


def test_goi_that_nhieu_trong_nguong_la_dat():
    kq = _cham(_ho_so(717, 2, dat=10, chua_dat=707, phat_sinh=10), viec_2=GOI_THAT)
    assert kq["K6"] is True


def test_goi_that_nhieu_vuot_3_phan_tram_la_chua_dat():
    kq = _cham(_ho_so(717, 2, dat=30, chua_dat=687), viec_2=GOI_THAT)
    assert kq["K6"] is False


def test_baseline_doi_so_dong_la_hong_K1():
    assert _cham(_ho_so(718, 2))["K1"] is False


def test_co_dong_baseline_khong_co_trang_thai_la_hong_K3():
    """Một «lần 2» thiếu kết quả sẽ bị đọc thành «mọi lỗi đã sửa»."""
    assert _cham(_ho_so(717, 2, chua_dat=700))["K3"] is False


def test_roi_dong_khi_ghi_baseline_la_hong_K4():
    assert _cham(_ho_so(717, 2), so_finding_1=720)["K4"] is False


def test_ten_vo_encoding_la_hong_K5():
    assert _cham(_ho_so(717, 2, ten="Nguyá»…n VÄƒn A"))["K5"] is False


def test_khong_biet_co_goi_model_thi_KHONG_cham_bua():
    assert _cham(_ho_so(717, 2), viec_2={})["K6"] is None


def test_bo_lan_1_thi_cac_tieu_chi_can_lan_1_la_khong_cham():
    kq = {k["ma"]: k["dat"] for k in danh_gia(
        lan1=None, ho_so_1=None, so_finding_1=None, viec_2=PHAT_LAI,
        ho_so_2=_ho_so(717, 3), ten="Nguyễn Văn A")}
    assert kq["K1"] is None and kq["K2"] is None and kq["K4"] is None
    assert kq["K3"] is True


def test_phat_lai_hoan_toan():
    assert phat_lai_hoan_toan(PHAT_LAI) is True
    assert phat_lai_hoan_toan(GOI_THAT) is False
    assert phat_lai_hoan_toan({"thong_ke_cache": {"bat": True, "ghi_them": 5}}) is False
    assert phat_lai_hoan_toan({}) is None
