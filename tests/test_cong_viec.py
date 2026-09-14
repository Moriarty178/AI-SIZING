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


class TestLuuFindings:
    def test_xong_thi_co_file_findings_doc_lai_duoc(self, kho):
        bo = BoChay(kho, ham_chay=_chay_gia([
            _f("critical"),
            Finding(id="y", severity="major", category="vuot_nguong",
                    finding="lỗi y", rule_ref="CPU-05")]))
        bo.bat_dau()
        cv = kho.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        d = kho.findings(cv.ma)
        assert d is not None
        # 2 finding khác id nên cả hai giữ; khử trùng theo (rule, scope, category,
        # finding) — 2 id khác nhau vẫn 2 dòng
        assert {f["id"] for f in d["findings"]} == {"x", "y"}
        assert d["so_loc_khong_can_cu"] == 0

    def test_findings_song_sot_restart(self, tmp_path):
        kho1 = KhoCongViec(tmp_path / "cv")
        bo = BoChay(kho1, ham_chay=_chay_gia([_f()]))
        bo.bat_dau()
        cv = kho1.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        assert KhoCongViec(tmp_path / "cv").findings(cv.ma) is not None

    def test_finding_khong_can_cu_duoc_dem_khong_xuat_hien(self, kho):
        bad = Finding(id="x", severity="major", category="vuot_nguong",
                      finding="không căn cứ")       # không rule_ref/evidence
        bo = BoChay(kho, ham_chay=_chay_gia([bad]))
        bo.bat_dau()
        cv = kho.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        d = kho.findings(cv.ma)
        assert d["so_loc_khong_can_cu"] == 1
        assert d["findings"] == []

    def test_ham_chay_thieu_sizing_van_khong_no(self, kho):
        """Hàm chạy giả trong test không có `sizing`/`rules` — persist findings
        không được vì thế làm hỏng lượt chạy."""
        bo = BoChay(kho, ham_chay=_chay_gia([_f()]))
        bo.bat_dau()
        cv = kho.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()
        assert kho.lay(cv.ma).trang_thai == XONG

    def test_xoa_viec_don_ca_file_findings(self, kho):
        bo = BoChay(kho, ham_chay=_chay_gia([_f()]))
        bo.bat_dau()
        cv = kho.them("a.docx", "a.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()

        assert kho.xoa(cv.ma) is True
        assert kho.findings(cv.ma) is None


class TestPhanHoi:
    @pytest.fixture
    def kho_co_viec(self, kho):
        bo = BoChay(kho, ham_chay=_chay_gia([Finding(
            id="KPI-02#App", severity="major", category="vuot_nguong",
            finding="CPU vượt ngưỡng 90% so với khai", rule_ref="KPI-02")]))
        bo.bat_dau()
        cv = kho.them("sizing.docx", "sizing.docx")
        bo.nop(cv)
        assert bo.cho_rong(5)
        bo.dung()
        return kho, cv.ma

    def test_luu_2_muc_thi_nhat_ky_co_2_dong(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        kq = kho.luu_phan_hoi(ma, {"KPI-02#App": {
            "ghi_chu": "Con số đúng, quy tắc áp nhầm", "phan_loai": "bao_sai"}})
        assert kq == {"da_luu": 1, "tong": 1}

        log = tmp_path / "phan_hoi" / "nhat-ky.csv"
        dong = log.read_text(encoding="utf-8-sig").strip().splitlines()
        assert len(dong) == 2                        # header + 1
        assert "KPI-02#App" in dong[1] and "bao_sai" in dong[1]
        assert "sizing.docx" in dong[1]

    def test_luu_lai_y_nguyen_KHONG_nhan_ban_log(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        ph = {"KPI-02#App": {"ghi_chu": "ok", "phan_loai": "chap_nhan"}}
        kho.luu_phan_hoi(ma, ph)
        kq = kho.luu_phan_hoi(ma, dict(ph))
        assert kq["da_luu"] == 0
        log = tmp_path / "phan_hoi" / "nhat-ky.csv"
        assert len(log.read_text(encoding="utf-8-sig").strip().splitlines()) == 2

    def test_sua_1_muc_thi_log_tang_1(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        kho.luu_phan_hoi(ma, {"KPI-02#App": {"ghi_chu": "a", "phan_loai": ""}})
        kho.luu_phan_hoi(ma, {"KPI-02#App": {"ghi_chu": "b", "phan_loai": "bao_sai"}})
        log = tmp_path / "phan_hoi" / "nhat-ky.csv"
        assert len(log.read_text(encoding="utf-8-sig").strip().splitlines()) == 3
        assert kho.phan_hoi(ma)["KPI-02#App"]["phan_loai"] == "bao_sai"

    def test_xuong_dong_trong_ghi_chu_la_1_dong_csv(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        kho.luu_phan_hoi(ma, {"KPI-02#App": {
            "ghi_chu": "dong 1\ndong 2", "phan_loai": ""}})
        log = tmp_path / "phan_hoi" / "nhat-ky.csv"
        assert len(log.read_text(encoding="utf-8-sig").strip().splitlines()) == 2
        assert "dong 1 / dong 2" in log.read_text(encoding="utf-8-sig")

    def test_rule_ref_severity_lay_tu_findings_khong_tin_payload(self, kho_co_viec):
        kho, ma = kho_co_viec
        kho.luu_phan_hoi(ma, {"KPI-02#App": {
            "ghi_chu": "x", "phan_loai": "can_ban"}})
        log = kho.doc_nhat_ky()
        # payload KHÔNG gửi severity — phải lấy từ findings.json (major/KPI-02)
        assert "KPI-02" in log and "major" in log and "vuot_nguong" in log

    def test_xoa_viec_KHONG_xoa_nhat_ky(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        kho.luu_phan_hoi(ma, {"KPI-02#App": {"ghi_chu": "x", "phan_loai": ""}})
        kho.xoa(ma)
        log = tmp_path / "phan_hoi" / "nhat-ky.csv"
        assert log.exists(), "nhiệt ký là dataset người thẩm định chủ động lưu"
        assert (tmp_path / "cv" / f"{ma}.findings.json").exists() is False
        assert (tmp_path / "cv" / f"{ma}.phan_hoi.json").exists() is False

    def test_restart_doc_lai_phan_hoi(self, kho_co_viec, tmp_path):
        kho, ma = kho_co_viec
        kho.luu_phan_hoi(ma, {"KPI-02#App": {"ghi_chu": "x", "phan_loai": "bao_sai"}})
        assert KhoCongViec(tmp_path / "cv").phan_hoi(ma) == {
            "KPI-02#App": {"ghi_chu": "x", "phan_loai": "bao_sai"}}

    def test_viec_khong_ton_tai_thi_KeyError(self, kho):
        with pytest.raises(KeyError):
            kho.luu_phan_hoi("khong-co", {"x": {"ghi_chu": "", "phan_loai": ""}})

    def test_chua_co_nhat_ky_thi_doc_tra_None(self, kho):
        assert kho.doc_nhat_ky() is None
