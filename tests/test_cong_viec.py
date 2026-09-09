"""Test 3.2 — hàng đợi công việc. OFFLINE, KHÔNG cần model (pipeline được tiêm)."""
import threading
import time

import pytest

from src.cong_viec import (BoChay, CongViec, GIAN_DOAN, HONG, KhoCongViec,
                           SONG_SONG_MAC_DINH, XONG)
from src.reporting.finding import Finding


class _KetQua:
    def __init__(self, findings):
        self.findings = findings

    def bao_cao(self):
        return "# Báo cáo thử\n\n" + "\n".join(f.finding for f in self.findings)


def _chay_gia(findings=(), *, ngu=0.0, no=None, ghi_tien_do=True):
    def chay(duong_dan, *, on_tien_do=None, song_song=1, **kw):
        if ghi_tien_do and on_tien_do:
            on_tien_do("C3", 1, 2, "nhóm CPU")
        if ngu:
            time.sleep(ngu)
        if no:
            raise no
        if ghi_tien_do and on_tien_do:
            on_tien_do("C5", 2, 2, "ARC-01")
        return _KetQua(list(findings))
    return chay


def _f(sev="major"):
    return Finding(id="x", severity=sev, category="vuot_nguong", finding="lỗi x",
                   rule_ref="KPI-02")


@pytest.fixture
def kho(tmp_path):
    return KhoCongViec(tmp_path / "cv")


class TestChayXong:
    def test_viec_chay_xong_thi_co_bao_cao_va_thong_ke_muc_do(self, kho):
        bo = BoChay(kho, ham_chay=_chay_gia([_f("critical"), _f("major"), _f("major")]))
        bo.bat_dau()
        cv = kho.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        xong = kho.lay(cv.ma)
        assert xong.trang_thai == XONG
        assert xong.so_finding == 3
        assert xong.theo_muc_do == {"critical": 1, "major": 2}
        assert "Báo cáo thử" in kho.bao_cao(cv.ma)
        assert xong.giay_da_chay >= 0

    def test_tien_do_duoc_cap_nhat_theo_giai_doan(self, kho):
        moc = []

        def chay(duong_dan, *, on_tien_do=None, song_song=1, **kw):
            on_tien_do("C3", 1, 4, "CPU")
            moc.append(kho.lay(ma).as_dict())
            on_tien_do("C5", 3, 4, "ARC-01")
            moc.append(kho.lay(ma).as_dict())
            return _KetQua([])

        bo = BoChay(kho, ham_chay=chay)
        bo.bat_dau()
        ma = kho.them("a.docx", "a.docx").ma
        bo.nop(kho.lay(ma))
        assert bo.cho_rong(5)
        bo.dung()
        assert moc[0]["giai_doan"] == "C3" and moc[0]["tien_do"] == 0.25
        assert moc[1]["giai_doan"] == "C5" and moc[1]["tien_do"] == 0.75

    def test_chua_biet_tong_thi_tien_do_la_None_chu_khong_phai_0(self, kho):
        """NT4: 0% và 'chưa rõ' là hai điều khác nhau. Người dùng nhìn 0% suốt
        16 phút sẽ tưởng nó treo."""
        assert CongViec(ma="x", ten_file="a.docx").tien_do() is None


class TestHongVaGianDoan:
    def test_mot_tai_lieu_hong_KHONG_giet_hang_doi(self, kho):
        """Việc thứ hai vẫn phải tới lượt — nếu không, một file hỏng làm đứng cả
        máy chủ cho tới lần khởi động lại."""
        bo = BoChay(kho, ham_chay=_chay_gia(no=ValueError("docx hỏng")))
        bo.bat_dau()
        a, b = kho.them("a.docx", "a.docx"), kho.them("b.docx", "b.docx")
        bo.nop(a)
        bo.nop(b)
        assert bo.cho_rong(5)
        bo.dung()
        assert kho.lay(a.ma).trang_thai == HONG
        assert "docx hỏng" in kho.lay(a.ma).loi
        assert kho.lay(b.ma).trang_thai == HONG      # cùng hàm giả, vẫn ĐƯỢC chạy
        assert kho.lay(b.ma).bat_dau is not None

    def test_viec_dang_chay_luc_tien_trinh_chet_thanh_GIAN_DOAN(self, tmp_path):
        """Một việc `dang_chay` mà không còn ai chạy nó là lời nói dối với người
        đang chờ. Nạp lại phải nói thật (NT4)."""
        kho1 = KhoCongViec(tmp_path / "cv")
        cv = kho1.them("a.docx", "a.docx")
        kho1.cap_nhat(cv.ma, trang_thai="dang_chay", bat_dau=time.time())

        kho2 = KhoCongViec(tmp_path / "cv")          # như sau một lần restart
        lai = kho2.lay(cv.ma)
        assert lai.trang_thai == GIAN_DOAN and "dừng giữa chừng" in lai.loi

    def test_ket_qua_song_sot_qua_khoi_dong_lai(self, tmp_path):
        """16 phút đủ dài để container bị restart. Mất kết quả vì thế là điều
        không cần phải xảy ra."""
        kho1 = KhoCongViec(tmp_path / "cv")
        bo = BoChay(kho1, ham_chay=_chay_gia([_f()]))
        bo.bat_dau()
        cv = kho1.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        kho2 = KhoCongViec(tmp_path / "cv")
        assert kho2.lay(cv.ma).trang_thai == XONG
        assert "Báo cáo thử" in kho2.bao_cao(cv.ma)

    def test_file_trang_thai_hong_khong_giet_ca_kho(self, tmp_path):
        d = tmp_path / "cv"
        d.mkdir(parents=True)
        (d / "hong.json").write_text("{ khong phai json", encoding="utf-8")
        kho = KhoCongViec(d)
        cv = kho.them("a.docx", "a.docx")
        assert KhoCongViec(d).lay(cv.ma) is not None


class TestChinhSach:
    def test_mac_dinh_chi_MOT_tai_lieu_mot_luc(self):
        """Pipeline đã chạy 12 lượt gọi song song bên trong. Hai tài liệu cùng
        lúc là 24 lượt đồng thời, mà đo 2026-09-09 cho thấy mức 24 CHẬM HƠN mức
        12 (138,9 so với 221,2 lượt/phút)."""
        bo = BoChay(KhoCongViec(), ham_chay=_chay_gia())
        assert bo.so_viec_song_song == 1
        assert bo.song_song == SONG_SONG_MAC_DINH == 12

    def test_chay_lan_luot_chu_khong_chong_nhau(self, kho):
        dang = []
        cao_nhat = [0]
        khoa = threading.Lock()

        def chay(duong_dan, *, on_tien_do=None, song_song=1, **kw):
            with khoa:
                dang.append(1)
                cao_nhat[0] = max(cao_nhat[0], len(dang))
            time.sleep(0.05)
            with khoa:
                dang.pop()
            return _KetQua([])

        bo = BoChay(kho, ham_chay=chay)
        bo.bat_dau()
        for i in range(4):
            bo.nop(kho.them(f"{i}.docx", f"{i}.docx"))
        assert bo.cho_rong(10)
        bo.dung()
        assert cao_nhat[0] == 1, "không được chạy hai tài liệu cùng lúc"

    def test_xoa_don_ca_TAI_LIEU_da_nop(self, kho, tmp_path):
        """Tài liệu sizing là dữ liệu nội bộ của người nộp; giữ vô thời hạn trên
        máy chủ phải là một lựa chọn có người quyết, không phải mặc định."""
        f = tmp_path / "a.docx"
        f.write_bytes(b"x")
        cv = kho.them("a.docx", str(f))
        kho.luu_bao_cao(cv.ma, "# bc")
        assert kho.xoa(cv.ma) is True
        assert not f.exists()
        assert kho.lay(cv.ma) is None and kho.bao_cao(cv.ma) is None
        assert kho.xoa(cv.ma) is False
