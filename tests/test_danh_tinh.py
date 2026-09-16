"""5.0a — danh tính demo. OFFLINE, không cần SQLAlchemy lẫn Streamlit."""
import pytest

from src.luu_tru.danh_tinh import (HEADER_TEN, HEADER_VAI, NHAN_VAI, TEN_TOI_DA,
                                   VAI, VAI_NGUOI_CHON, DanhTinh, tao_danh_tinh,
                                   thanh_header, tu_header)


class TestTaoDanhTinh:
    def test_hop_le(self):
        assert tao_danh_tinh("admin", "An") == DanhTinh("admin", "An")

    def test_gop_khoang_trang_de_mot_nguoi_khong_thanh_hai(self):
        """Bảng Admin lọc theo tên sẽ tách «Nguyễn  Văn A» và «Nguyễn Văn A»."""
        assert tao_danh_tinh("admin", "  Nguyễn   Văn\tA ").ten == "Nguyễn Văn A"

    @pytest.mark.parametrize("ten", ["", "   ", None])
    def test_thieu_ten_thi_bao_ro(self, ten):
        with pytest.raises(ValueError, match="Chưa nhập tên"):
            tao_danh_tinh("admin", ten)

    def test_ten_qua_dai_bi_chan_TRUOC_khi_toi_CSDL(self):
        """CSDL chặn thì người dùng nhận `IntegrityError` sau khi đã bấm lưu."""
        with pytest.raises(ValueError, match="tối đa"):
            tao_danh_tinh("admin", "a" * (TEN_TOI_DA + 1))

    def test_vai_la_bi_chan(self):
        with pytest.raises(ValueError, match="không hợp lệ"):
            tao_danh_tinh("sieu_admin", "An")

    def test_nguoi_KHONG_duoc_chon_vai_he_thong(self):
        """`he_thong` dành cho dòng máy ghi. Người chọn được thì dòng người ghi và
        dòng máy ghi lẫn vào nhau trên bảng Admin."""
        assert "he_thong" not in VAI_NGUOI_CHON
        with pytest.raises(ValueError):
            tao_danh_tinh("he_thong", "An")
        assert tao_danh_tinh("he_thong", "copilot", cho_phep_he_thong=True).vai == "he_thong"

    def test_moi_vai_deu_co_nhan_tieng_viet(self):
        assert set(NHAN_VAI) == set(VAI)


class TestHeader:
    @pytest.mark.parametrize("ten", [
        "Nguyễn Thị Ánh Tuyết", "Trần Đức — Đội 2/P3", "O'Brien & Co; a=b",
        "50% tải", "Lê Văn Ước ❤"])
    def test_khu_hoi_nguyen_ven(self, ten):
        dt = tao_danh_tinh("nguoi_lam_sizing", ten)
        h = thanh_header(dt)
        # Header HTTP chỉ chở latin-1 — thực tế chỉ nên là ASCII.
        assert all(v.isascii() for v in h.values()), h
        assert tu_header(h) == dt

    def test_khong_gui_gi_thi_None(self):
        assert tu_header({}) is None

    def test_header_hong_thi_ValueError_khong_im_lang(self):
        """Gửi vai mà thiếu tên là lỗi của bên gọi — nói ra, đừng coi như vô danh."""
        with pytest.raises(ValueError):
            tu_header({HEADER_VAI: "admin"})
        with pytest.raises(ValueError):
            tu_header({HEADER_VAI: "hacker", HEADER_TEN: "x"})

    def test_he_thong_KHONG_gia_mao_duoc_qua_header(self):
        """Giao diện không cho chọn `he_thong`; header cũng không được là cửa sau."""
        with pytest.raises(ValueError):
            tu_header({HEADER_VAI: "he_thong", HEADER_TEN: "copilot"})


def test_VAI_khop_rang_buoc_CHECK_cua_luoc_do():
    """Hai danh sách lệch nhau thì giao diện cho chọn một vai mà CSDL từ chối."""
    pytest.importorskip("sqlalchemy")
    from src.luu_tru import luoc_do as ld
    ck = [c for c in ld.metadata.tables["ho_so"].constraints
          if getattr(c, "name", "") and str(c.name).endswith("vai")]
    assert ck, "không thấy ràng buộc CHECK vai"
    van = str(ck[0].sqltext)
    for v in VAI:
        assert repr(v) in van
