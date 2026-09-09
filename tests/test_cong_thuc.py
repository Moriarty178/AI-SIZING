"""Test C3 · đọc công thức tài liệu tự viết. OFFLINE, thuần code.

Dữ liệu lấy nguyên văn từ hồ sơ thật trong `danh_sach_sizings_da_duyet/`.
"""
import pytest

from src.extraction.cong_thuc import CongThucKhai, doc_mot_o


class TestDocMotO:
    def test_cong_thuc_that_cua_VTracking(self):
        ct = doc_mot_o("= (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s")
        assert ct is not None and ct.khop
        assert ct.quy_uoc == ("us",)
        assert ct.gia_tri == 696249.0
        assert ct.don_vi == "KB/s"
        assert ct.co_he_so(1.1) is True
        assert ct.co_he_so(1.2) is False

    def test_khong_co_toan_tu_thi_khong_phai_cong_thuc(self):
        assert doc_mot_o("= 5 = 5") is None
        assert doc_mot_o("696,249 KB/s") is None

    def test_o_co_chu_khong_bao_gio_toi_duoc_bo_tinh(self):
        """Biểu thức bị lọc bằng regex chỉ cho chữ số và toán tử, nên `asteval`
        không nhận tên biến hay lời gọi hàm — `CLAUDE.md` cấm `eval()`."""
        assert doc_mot_o("__import__('os').system('x') = 1") is None
        assert doc_mot_o("Thông lượng = 100 * 2") is None

    def test_so_hoc_SAI_thi_khong_duoc_dung_lam_can_cu(self):
        """Ca thật ở PBH 4.0: «57.2/18 = 1,896» — 57.2/18 = 3.18, không phải
        1,896 theo bất kỳ lối đọc dấu phẩy nào. NT4: nói không kiểm được."""
        ct = doc_mot_o("57.2/18 = 1,896")
        assert ct is not None and not ct.khop and ct.quy_uoc == ()

    def test_ket_qua_ghi_duoi_dang_phan_tram(self):
        """Ca thật ở Vtag: 0,00875 được ghi thành «1%». Cách viết, không phải sai
        số học — đo trên dev: 7/18 ô đơn vị `%` khớp nhờ nhánh này."""
        ct = doc_mot_o("= (3.51 - 3.23)*1,000/32,000 = 1%")
        assert ct is not None and ct.khop

    def test_lan_quy_uoc_GIUA_bieu_thuc_va_ket_qua_thi_khong_ket_luan(self):
        """Ca thật ở PBH: «71.5 / 125 = 57,2 %» — biểu thức dùng `.` làm dấu thập
        phân, kết quả lại dùng `,`. Không một lối đọc thống nhất nào khớp.

        Cố ý KHÔNG thử ghép chéo hai quy ước: mỗi lối đọc thêm vào là một cơ hội
        khớp ngẫu nhiên, mà toàn bộ giá trị của module này nằm ở chỗ số học tự
        chứng minh cách đọc. Thà nói không kiểm được (NT4)."""
        ct = doc_mot_o("71.5 / 125 = 57,2 %")
        assert ct is not None and not ct.khop

    def test_lam_tron_cua_tac_gia_duoc_chap_nhan(self):
        """696,248.4 được tác giả ghi 696,249 — đòi khớp tuyệt đối là đòi hơn
        những gì tác giả viết ra."""
        assert doc_mot_o("= 3*90 = 270").khop
        assert doc_mot_o("= 100000*15*15/1000 = 22500").khop

    def test_ca_hai_loi_doc_cung_khop_thi_giu_ca_hai(self):
        """«17,284 * 6 = 103,704» đúng cho cả hai quy ước vì phép nhân bất biến
        theo thang. Không được chọn bừa một lối rồi kết luận theo nó."""
        ct = doc_mot_o("= 17,284 * 6 = 103,704 KB/s")
        assert ct.khop and set(ct.quy_uoc) == {"us", "vn"}
        assert ct.co_he_so(1.2) is False        # cả hai lối đều không có 1.2

    def test_so_chia_KHONG_bi_coi_la_he_so_nhan(self):
        """`/0.8` là ngưỡng KPI, không phải hệ số dự phòng."""
        ct = doc_mot_o("=125*10602/0.8*1.1 = 1,822,219")
        assert ct.co_he_so(0.8) is False
        assert ct.co_he_so(1.1) is True

    def test_dong_cong_don_duoc_nhan_ra(self):
        ct = doc_mot_o("696,249 + 1,822,219 = 2,518,468 KB/s")
        assert ct.khop and not ct.co_nhan_chia

    def test_so_hang_liet_ke_moi_hang_so(self):
        ct = doc_mot_o("= (125 + 32.5) * 3215/0.8*1.1 = 696,249")
        assert ct.so_hang() == (125.0, 32.5, 3215.0, 0.8, 1.1)


def test_gia_tri_None_thi_khong_khop():
    ct = CongThucKhai(o_goc="x", bieu_thuc="1+1", ket_qua_khai="2")
    assert not ct.khop and ct.co_he_so(1.2) is None
