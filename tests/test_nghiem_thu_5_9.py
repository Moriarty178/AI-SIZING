"""Chấm nghiệm thu 5.9 bước 2 — thuần hàm, không cần dịch vụ.

Cái được gác ở đây: thang chấm phải ĐỎ khi thứ nó đo hỏng. Một script nghiệm thu
luôn xanh còn tệ hơn không có script, vì nó tạo bằng chứng giả.
"""
import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "nghiem_thu_5_9.py"
_spec = importlib.util.spec_from_file_location("nghiem_thu_5_9", _p)
nt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nt)

TEN = "phongnh40"
KHOI = ('  - id: STO-02\n    name: "Ổ NL-SAS nên dùng RAID 6"\n'
        '    type: quantitative\n    check: "cap_raid == 6"\n')


def _ket(**kw):
    d = dict(
        q={"id": "STO-02", "khoi": KHOI, "duong_dan": "config/rules.yaml",
           "khong_danh_gia_duoc": "cần bảng tra cho loai_o"},
        kiem_dat={"dat": True, "so_quy_tac": 151, "so_bieu_thuc": 137,
                  "chay_duoc_truoc": 77, "chay_duoc_sau": 77, "canh_bao": []},
        kiem_doi_ma={"dat": False, "loi": ["`id` đổi … nằm trong `rule_ref` của …"]},
        kiem_cu_phap={"dat": False, "loi": ["2 biểu thức không phân tích được: …"]},
        da_luu={"id": 7, "ten": TEN, "vai": "admin", "ly_do": nt.LY_DO,
                "noi_dung_cu": KHOI, "trang_thai": "kiem_dat", "bang_chung_eval": ""},
        ma_nguoi_thuong=403, ma_khong_danh_tinh=400, ma_danh_dau_som=409,
        trang_thai_sau="kiem_dat", ten_gui=TEN)
    d.update(kw)
    return {k["ma"]: k for k in nt.cham(**d)}


def test_du_tieu_chi_thi_dat():
    k = _ket()
    assert all(k[m]["dat"] for m in ("B1", "B2", "B3", "B4", "B5", "B6"))
    assert "CHƯA đo eval" in k["B2"]["chi_tiet"], "không được ngụ ý đã đo chất lượng"
    assert "chưa ai đo" in k["B4"]["chi_tiet"]


def test_khoi_bi_dump_lai_mat_chu_thich_thi_B1_do():
    """`yaml.dump` ra `- id: STO-02` không thụt và không còn chú thích."""
    assert _ket(q={"id": "STO-02", "khoi": "- id: STO-02\n", "duong_dan": "x"}
                )["B1"]["dat"] is False


def test_kiem_khong_dat_thi_B2_do():
    assert _ket(kiem_dat={"dat": False, "loi": ["hỏng"]})["B2"]["dat"] is False
    assert _ket(kiem_dat={"dat": True, "so_bieu_thuc": 0})["B2"]["dat"] is False


def test_sua_HONG_ma_van_lot_thi_B3_do():
    """Đây là tiêu chí quan trọng nhất: nếu cổng chặn không chặn, một lần sửa sai
    chạy trên mọi hồ sơ về sau."""
    assert _ket(kiem_doi_ma={"dat": True})["B3"]["dat"] is False
    assert _ket(kiem_cu_phap={"dat": True})["B3"]["dat"] is False
    # Chặn nhưng nói sai lý do cũng không đạt — người đọc phải sửa được.
    assert _ket(kiem_cu_phap={"dat": False, "loi": ["lỗi gì đó"]})["B3"]["dat"] is False


DA_LUU = {"id": 7, "ten": TEN, "vai": "admin", "ly_do": nt.LY_DO,
          "noi_dung_cu": KHOI, "trang_thai": "kiem_dat", "bang_chung_eval": ""}


def test_de_xuat_mat_nguoi_hoac_khoi_cu_thi_B4_do():
    for kw in ({"ten": "ai đó"}, {"vai": "nguoi_lam_sizing"}, {"noi_dung_cu": ""},
               {"ly_do": ""}, {"trang_thai": "kiem_hong"}):
        assert _ket(da_luu={**DA_LUU, **kw})["B4"]["dat"] is False, kw
    assert _ket(da_luu=None)["B4"]["dat"] is False


def test_vai_khong_bi_chan_thi_B5_do():
    assert _ket(ma_nguoi_thuong=201)["B5"]["dat"] is False
    assert _ket(ma_khong_danh_tinh=201)["B5"]["dat"] is False


def test_danh_dau_da_ap_khi_file_chua_doi_ma_VAN_qua_thi_B6_do():
    """Công cụ không sửa `rules.yaml`. Cho đánh dấu «đã áp» khi file chưa đổi là ghi
    một điều SAI vào lịch sử quyết định — đúng thứ NT4 cấm."""
    assert _ket(ma_danh_dau_som=200, trang_thai_sau="da_ap")["B6"]["dat"] is False
    assert _ket(ma_danh_dau_som=409, trang_thai_sau="da_ap")["B6"]["dat"] is False
