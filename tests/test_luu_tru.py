"""5.0 — lớp lưu trữ Giai đoạn 5. OFFLINE: SQLite trong bộ nhớ, CÙNG lược đồ.

Máy thật chạy PostgreSQL. Ở đây kiểm những thứ phải đúng trên CẢ HAI: bảng tạo
được, khoá ngoại và ràng buộc thật sự chặn, không bao giờ in mật khẩu, và — quan
trọng nhất với máy nội bộ — không cấu hình CSDL thì mọi thứ chạy y như trước.
"""
import pytest

from src.luu_tru.cau_hinh import (BIEN_URL, TrangThaiCSDL, an_mat_khau,
                                  mo_kho_tu_moi_truong)

sa = pytest.importorskip("sqlalchemy", reason="cài với: pip install '.[db]'")

from src.luu_tru import luoc_do as ld        # noqa: E402
from src.luu_tru.kho import KhoCSDL, LoiCSDL  # noqa: E402

URL_BO_NHO = "sqlite+pysqlite:///:memory:"


@pytest.fixture
def kho():
    k = KhoCSDL(URL_BO_NHO)
    k.khoi_tao()
    return k


def _dong(khoa="CPU-01#kafka", **kw):
    d = {"khoa": khoa, "finding_id_goc": "CPU-01#Kafka", "rule_ref": "CPU-01",
         "scope_goc": "Kafka", "muc_do": "major", "noi_dung": "CPU vượt ngưỡng",
         "nguon": "ai", "vai": "he_thong", "ten": "copilot"}
    d.update(kw)
    return d


# ------------------------------------------------ không cấu hình = như cũ --
class TestKhongCauHinh:
    def test_khong_dat_url_thi_KHONG_mo_gi_va_noi_ro(self, monkeypatch):
        """Máy nội bộ `git pull` về mà chưa đặt biến: Copilot phải chạy y như trước."""
        monkeypatch.delenv(BIEN_URL, raising=False)
        k, tt = mo_kho_tu_moi_truong()
        assert k is None
        assert (tt.cau_hinh, tt.san_sang) == (False, False)
        assert BIEN_URL in tt.thong_diep, "phải nói rõ thiếu biến nào (NT4)"

    def test_url_hong_KHONG_nem_loi(self, monkeypatch):
        """CSDL hỏng không được giết API — nộp bài và báo cáo không cần CSDL."""
        monkeypatch.setenv(BIEN_URL, "khong-phai-url://x")
        k, tt = mo_kho_tu_moi_truong()
        assert k is None and tt.cau_hinh is True and tt.san_sang is False

    def test_url_dung_thi_san_sang(self, monkeypatch):
        monkeypatch.setenv(BIEN_URL, URL_BO_NHO)
        k, tt = mo_kho_tu_moi_truong()
        assert k is not None and tt.san_sang is True


class TestAnMatKhau:
    def test_an_mat_khau_trong_url(self):
        u = an_mat_khau("postgresql+psycopg://copilot:bi-mat-123@copilot-db:5432/copilot")
        assert "bi-mat-123" not in u
        assert "copilot@copilot-db:5432" in u.replace(":***", "")

    def test_url_khong_co_mat_khau_giu_nguyen(self):
        assert an_mat_khau(URL_BO_NHO) == URL_BO_NHO

    def test_thong_bao_loi_KHONG_lo_mat_khau(self, monkeypatch):
        """Thông báo lỗi đi thẳng vào `/health`, mà `/health` thì ai cũng gọi được."""
        monkeypatch.setenv(
            BIEN_URL, "postgresql+psycopg://copilot:bi-mat-123@127.0.0.1:1/copilot")
        _, tt = mo_kho_tu_moi_truong()
        assert tt.san_sang is False
        assert "bi-mat-123" not in tt.thong_diep


# ------------------------------------------------------------- lược đồ ----
class TestLuocDo:
    def test_khoi_tao_goi_nhieu_lan_van_an_toan(self):
        k = KhoCSDL(URL_BO_NHO)
        k.khoi_tao()
        k.khoi_tao()

    def test_lech_phien_ban_luoc_do_thi_DUNG(self, kho):
        """`create_all` không sửa bảng đã có. Chạy tiếp trên lược đồ lệch là để lỗi
        hiện ra ở một câu SQL nào đó, xa chỗ gây ra nó."""
        with kho.engine.begin() as c:
            c.execute(sa.update(ld.thong_tin_luoc_do).values(gia_tri="0"))
        with pytest.raises(LoiCSDL, match="migration"):
            kho.khoi_tao()

    @pytest.mark.parametrize("bang", ld.BANG_CO_ACTOR)
    def test_moi_bang_ghi_hanh_dong_cua_nguoi_deu_co_actor(self, bang):
        """5.0a: không có cột actor thì dòng CSDL không có người, và khi ghép vào
        tool sizing có đăng nhập thật thì không backfill được."""
        cot = ld.metadata.tables[bang].c
        assert "vai" in cot and "ten" in cot

    def test_du_chin_bang_nghiep_vu(self):
        assert set(ld.metadata.tables) >= {
            "ho_so", "lan_tham_dinh", "finding_baseline", "ket_qua_lan", "lan_sua",
            "bao_cao_loi", "ghi_chu_admin", "quyet_dinh", "de_xuat_quy_tac"}


# ------------------------------------------------ hồ sơ → lần → baseline ---
class TestHoSoVaBaseline:
    def test_di_tron_duong(self, kho):
        hs = kho.tao_ho_so("Sizing ABC.docx", vai="nguoi_lam_sizing", ten="An")
        _, so = kho.them_lan_tham_dinh(hs, "36d2314d3826", vai="nguoi_lam_sizing",
                                       ten="An", commit="03361fa")
        assert so == 1, "lần đầu là baseline (5.1)"
        assert kho.them_finding_baseline(hs, [_dong(), _dong("RAM-01#redis")]) == 2
        ds = kho.doc_baseline(hs)
        assert [d["khoa"] for d in ds] == ["CPU-01#kafka", "RAM-01#redis"]
        assert ds[0]["noi_dung"] == "CPU vượt ngưỡng", "tiếng Việt phải còn nguyên"

    def test_so_thu_tu_tang_theo_tung_ho_so(self, kho):
        a = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        b = kho.tao_ho_so("b.docx", vai="admin", ten="x")
        assert kho.them_lan_tham_dinh(a, "m1", vai="admin", ten="x")[1] == 1
        assert kho.them_lan_tham_dinh(a, "m2", vai="admin", ten="x")[1] == 2
        assert kho.them_lan_tham_dinh(b, "m3", vai="admin", ten="x")[1] == 1

    def test_mot_khoa_chi_mot_dong_trong_mot_ho_so(self, kho):
        """Khoá 5.1 là thứ nối các lần thẩm định. Trùng khoá thì một dòng sẽ nối
        nhầm sang dòng kia."""
        hs = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        with pytest.raises(sa.exc.IntegrityError):
            kho.them_finding_baseline(hs, [_dong(), _dong()])

    def test_hong_mot_dong_thi_KHONG_ghi_dong_nao(self, kho):
        """Baseline dở dang còn tệ hơn không có baseline: số lỗi sẽ sai mãi mãi."""
        hs = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        with pytest.raises(sa.exc.IntegrityError):
            kho.them_finding_baseline(hs, [_dong("A#x"), _dong("B#y"), _dong("A#x")])
        assert kho.doc_baseline(hs) == []

    def test_vai_la_bi_chan(self, kho):
        with pytest.raises(sa.exc.IntegrityError):
            kho.tao_ho_so("a.docx", vai="khach_vang_lai", ten="x")

    def test_nguon_chi_nhan_ai_hoac_admin(self, kho):
        hs = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        with pytest.raises(sa.exc.IntegrityError):
            kho.them_finding_baseline(hs, [_dong(nguon="doan_bua")])

    def test_ma_viec_khong_duoc_gan_cho_hai_lan(self, kho):
        hs = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        kho.them_lan_tham_dinh(hs, "m1", vai="admin", ten="x")
        with pytest.raises(sa.exc.IntegrityError):
            kho.them_lan_tham_dinh(hs, "m1", vai="admin", ten="x")

    def test_xoa_ho_so_keo_theo_moi_dong_con(self, kho):
        """Khoá ngoại phải BẬT thật — SQLite mặc định tắt, nên không bật thì test
        này qua trên SQLite mà hỏng trên PostgreSQL."""
        hs = kho.tao_ho_so("a.docx", vai="admin", ten="x")
        kho.them_lan_tham_dinh(hs, "m1", vai="admin", ten="x")
        kho.them_finding_baseline(hs, [_dong()])
        with kho.engine.begin() as c:
            c.execute(sa.delete(ld.ho_so).where(ld.ho_so.c.id == hs))
        assert kho.doc_baseline(hs) == []
        with kho.engine.connect() as c:
            assert c.execute(sa.select(sa.func.count()).select_from(
                ld.lan_tham_dinh)).scalar() == 0

    def test_ho_so_khong_ton_tai_thi_khong_them_duoc_baseline(self, kho):
        with pytest.raises(sa.exc.IntegrityError):
            kho.them_finding_baseline(999, [_dong()])


def test_trang_thai_csdl_ra_json_duoc():
    import json
    json.dumps(TrangThaiCSDL(True, False, "x").as_dict())
