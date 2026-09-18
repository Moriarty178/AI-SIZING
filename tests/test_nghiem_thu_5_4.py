"""Chấm nghiệm thu 5.4 — thuần hàm, không cần dịch vụ."""
import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "nghiem_thu_5_4.py"
_spec = importlib.util.spec_from_file_location("nghiem_thu_5_4", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)

TEN = "phongnh40"
B = {"id": 1, "khoa": "CPU-01#kafka", "nguon": "baseline",
     "nhat_ky": "đã ghi nhật ký 4.1 (việc abc)"}
P = {"id": 2, "khoa": "ARC-06#tủ rack", "nguon": "phát sinh", "nhat_ky": "đã ghi"}
DOC_LAI = [{"id": 2, "ten": TEN}, {"id": 1, "ten": TEN}]


def _ket(**kw):
    d = dict(luoc_do="3", san_sang=True, so_baseline=719, so_lan=6, so_phat_sinh=174,
             bao_baseline=B, bao_phat_sinh=P, doc_lai=DOC_LAI, ten_gui=TEN,
             ma_khong_danh_tinh=400)
    d.update(kw)
    return {k["ma"]: k for k in nt.cham(**d)}


def test_du_tieu_chi_thi_dat():
    k = _ket()
    assert [m for m in ("B1", "B2", "B3", "B4", "B5", "B6") if k[m]["dat"] is not True] == []


def test_luoc_do_con_o_ban_2_thi_B1_truot():
    """Nâng cấp không chạy = bảng `bao_cao_loi` còn hình dạng cũ."""
    k = _ket(luoc_do="2")
    assert k["B1"]["dat"] is False and "cần '3'" in k["B1"]["chi_tiet"]


def test_ho_so_cu_mat_du_lieu_thi_B2_truot():
    assert _ket(so_baseline=0)["B2"]["dat"] is False


def test_khong_bao_duoc_dong_phat_sinh_thi_B4_truot():
    k = _ket(bao_phat_sinh=None, doc_lai=[{"id": 1, "ten": TEN}])
    assert k["B4"]["dat"] is False and k["B3"]["dat"] is True


def test_ten_luu_sai_thi_B5_truot():
    assert _ket(doc_lai=[{"id": 2, "ten": "ai đó"}, {"id": 1, "ten": TEN}]
                )["B5"]["dat"] is False


def test_khong_ghi_duoc_nhat_ky_4_1_thi_B5_truot():
    k = _ket(bao_baseline={**B, "nhat_ky": "bỏ qua nhật ký 4.1: …"})
    assert k["B5"]["dat"] is False and k["B3"]["dat"] is True


def test_thieu_danh_tinh_khong_bi_chan_thi_B6_truot():
    assert _ket(ma_khong_danh_tinh=201)["B6"]["dat"] is False
