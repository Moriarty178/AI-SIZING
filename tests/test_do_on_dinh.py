"""5.0b — phép đo độ ổn định. OFFLINE, không cần API lẫn model.

Phép đo này quyết định thiết kế 5.1/5.3/5.6, nên bản thân nó phải đúng: một con
số sai ở đây dẫn tới một tuần code sai hướng.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.do_on_dinh import (_dong_dich_vu, _khoa_goc,   # noqa: E402
                                so_sanh)
from src.khach_api import SucKhoe                           # noqa: E402


def _f(fid, **kw):
    d = {"id": fid, "severity": "cao", "nhom": "vong2_chua_dat",
         "finding": "mô tả", "computed_evidence": "", "location": "Mục I"}
    d.update(kw)
    return d


class TestKhoaGoc:
    def test_bo_hau_to_khu_trung(self):
        assert _khoa_goc("KPI-02#PH1#2") == "KPI-02#PH1"

    def test_KHONG_dung_vao_id_thuong(self):
        """`id` gốc là `{rule}#{scope}` — hai phần. Cắt đi là hỏng khoá."""
        assert _khoa_goc("KPI-02#PH1") == "KPI-02#PH1"
        assert _khoa_goc("KPI-02#he_thong") == "KPI-02#he_thong"

    def test_scope_ket_thuc_bang_so_KHONG_bi_cat(self):
        """Phân hệ tên «PH2» rất thường gặp; cắt nhầm là gộp hai finding làm một."""
        assert _khoa_goc("KPI-02#PH2") == "KPI-02#PH2"


class TestSoSanh:
    def test_hai_luot_giong_het(self):
        ds = [_f("A#x"), _f("B#y")]
        kq = so_sanh(ds, list(ds))
        assert kq["khop"] == 2 and kq["chi_a"] == 0 and kq["chi_b"] == 0

    def test_dem_dung_ben_nao_thieu(self):
        kq = so_sanh([_f("A#x"), _f("B#y")], [_f("A#x"), _f("C#z")])
        assert (kq["khop"], kq["chi_a"], kq["chi_b"]) == (1, 1, 1)

    def test_tach_MAT_KHOP_VI_HAU_TO_khoi_model_doi_y(self):
        """Hai finding trùng `rule#scope`, lượt sau đảo thứ tự → id lệch nhưng
        tập finding KHÔNG đổi. Đây là lỗi khoá, sửa được bằng code — không được
        gộp chung với «model đổi ý»."""
        a = [_f("A#x", finding="một"), _f("A#x#2", finding="hai")]
        b = [_f("A#x", finding="hai"), _f("A#x#2", finding="một")]
        kq = so_sanh(a, b)
        assert kq["khop_theo_khoa_goc"] == 2
        assert kq["mat_khop_do_hau_to"] == 0, "id vẫn khớp, chỉ nội dung đảo chỗ"
        assert kq["doi"]["cau_chu"] == 2

    def test_mat_khop_do_hau_to_khi_so_ban_sao_giu_nguyen_ma_id_lech(self):
        a = [_f("A#x"), _f("A#x#2")]
        b = [_f("A#x"), _f("A#x#3")]
        kq = so_sanh(a, b)
        assert kq["khop"] == 1
        assert kq["khop_theo_khoa_goc"] == 2
        assert kq["mat_khop_do_hau_to"] == 1

    def test_dem_tung_loai_thay_doi_rieng(self):
        a = [_f("A#x", severity="cao", computed_evidence="12")]
        b = [_f("A#x", severity="thap", computed_evidence="13")]
        kq = so_sanh(a, b)
        assert kq["doi"]["muc_do"] == 1 and kq["doi"]["can_cu"] == 1
        assert kq["doi"]["cau_chu"] == 0

    def test_dem_dong_code_tinh_lai_duoc(self):
        """Chỉ dòng có `computed_evidence` mới mang được trạng thái Đạt/Chưa đạt
        một cách chắc chắn — con số này định cỡ cột Trạng thái của 5.6."""
        a = [_f("A#x", computed_evidence="1,2"), _f("B#y"), _f("C#z")]
        kq = so_sanh(a, list(a))
        assert kq["code_tinh_duoc_a"] == 1 and kq["code_tinh_duoc_khop"] == 1

    def test_khoang_trang_KHONG_tinh_la_can_cu(self):
        kq = so_sanh([_f("A#x", computed_evidence="   ")], [_f("A#x")])
        assert kq["code_tinh_duoc_a"] == 0

    def test_dem_dong_chua_kiem_duoc(self):
        a = [_f("A#x", nhom="vong2_chua_kiem"), _f("B#y")]
        assert so_sanh(a, a)["chua_kiem_duoc_a"] == 1

    def test_tap_rong_khong_no(self):
        kq = so_sanh([], [])
        assert kq["khop"] == 0 and kq["so_a"] == 0


class TestDongDichVu:
    """Dòng in ĐẦU TIÊN của script. Nổ ở đây là giết cả phép đo trước khi nó
    chạm tới dữ liệu — đã xảy ra thật 2026-09-16 (`SucKhoe` không có `.ban`)."""

    def test_health_khong_co_nhan_ban_van_in_duoc(self):
        d = _dong_dich_vu(SucKhoe(song=True, commit="abc1234"))
        assert "abc1234" in d and "—" in d

    def test_health_co_nhan_ban_thi_in_ra(self):
        sk = SucKhoe(song=True, commit="abc1234", tho={"ban": "v2"})
        assert "v2" in _dong_dich_vu(sk)

    def test_thieu_ca_commit_lan_nhan_van_khong_no(self):
        assert _dong_dich_vu(SucKhoe(song=True))
