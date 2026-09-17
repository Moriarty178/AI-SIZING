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


# ----------------------------------------------------- 5.1: ghi một lần --------
def _fd(fid, **kw):
    d = {"id": fid, "severity": "major", "category": "vuot_nguong",
         "finding": "CPU vượt ngưỡng", "computed_evidence": "", "location": "Mục I",
         "nhom": "vong2_chua_dat", "rule_ref": fid.split("#")[0]}
    d.update(kw)
    return d


def _dt():
    from src.luu_tru.danh_tinh import tao_danh_tinh
    return tao_danh_tinh("nguoi_lam_sizing", "Nguyễn Văn A")


class TestGhiLanThamDinh:
    def test_lan_dau_tao_ho_so_va_dong_bang_baseline(self, kho):
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a.docx", danh_tinh=_dt(),
                                  findings=[_fd("A#x"), _fd("B#y")])
        assert (r["so_thu_tu"], r["so_loi_baseline"], r["phat_sinh"]) == (1, 2, 0)
        d = kho.doc_ho_so(r["ho_so_id"])
        assert d["so_loi_baseline"] == 2
        assert {b["vai"] for b in d["baseline"]} == {"he_thong"}, \
            "baseline do MÁY sinh, không mang danh tính người nộp"
        assert d["cac_lan"][0]["ten"] == "Nguyễn Văn A", "LẦN thì mang người nộp"

    def test_lan_sau_KHONG_doi_so_dong_baseline(self, kho):
        r1 = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a.docx", danh_tinh=_dt(),
                                   findings=[_fd("A#x"), _fd("B#y")])
        r2 = kho.ghi_lan_tham_dinh(ma_viec="m2", ten_file="a_v2.docx", danh_tinh=_dt(),
                                   ho_so_id=r1["ho_so_id"],
                                   findings=[_fd("A#x"), _fd("C#z"), _fd("D#w")])
        assert r2["so_thu_tu"] == 2
        assert r2["so_loi_baseline"] == 2, "số lỗi giữ nguyên"
        assert (r2["dat"], r2["chua_dat"], r2["phat_sinh"]) == (1, 1, 2)
        d = kho.doc_ho_so(r1["ho_so_id"])
        assert len(d["baseline"]) == 2
        assert {b["khoa"]: b["trang_thai"] for b in d["baseline"]} == \
            {"A#x": "chua_dat", "B#y": "dat"}
        assert sorted(p["khoa"] for p in d["phat_sinh"]) == ["C#z", "D#w"]
        assert [l["ten_file"] for l in d["cac_lan"]] == ["a.docx", "a_v2.docx"]
        assert d["cac_lan"][1]["dem"] == {"dat": 1, "chua_dat": 1,
                                          "chua_kiem_duoc": 0, "phat_sinh": 2}

    def test_ro_phat_sinh_tinh_lai_moi_lan_KHONG_ke_thua(self, kho):
        """Lỗi phát sinh ở lần 2 mà lần 3 đã hết thì hết thật, không đọng lại."""
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  findings=[_fd("A#x")])
        h = r["ho_so_id"]
        kho.ghi_lan_tham_dinh(ma_viec="m2", ten_file="a", danh_tinh=_dt(), ho_so_id=h,
                              findings=[_fd("A#x"), _fd("C#z")])
        r3 = kho.ghi_lan_tham_dinh(ma_viec="m3", ten_file="a", danh_tinh=_dt(),
                                   ho_so_id=h, findings=[_fd("A#x")])
        assert r3["phat_sinh"] == 0
        assert kho.doc_ho_so(h)["phat_sinh"] == []

    def test_ho_so_khong_ton_tai_thi_bao_ro(self, kho):
        from src.luu_tru.kho import KhongThamDinhLaiDuoc
        with pytest.raises(KhongThamDinhLaiDuoc, match="#999"):
            kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  ho_so_id=999, findings=[])

    def test_ho_so_da_gui_duyet_thi_KHONG_tham_dinh_lai(self, kho):
        from src.luu_tru.kho import KhongThamDinhLaiDuoc
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  findings=[_fd("A#x")])
        kho.dat_trang_thai_ho_so(r["ho_so_id"], "cho_duyet")
        with pytest.raises(KhongThamDinhLaiDuoc, match="cho_duyet"):
            kho.ghi_lan_tham_dinh(ma_viec="m2", ten_file="a", danh_tinh=_dt(),
                                  ho_so_id=r["ho_so_id"], findings=[])

    def test_hong_giua_chung_KHONG_de_lai_lan_do_dang(self, kho):
        """Một «lần 2» không có kết quả nào sẽ bị bảng Admin đọc thành «mọi lỗi đã
        sửa». Mã việc trùng làm INSERT lần hỏng → cả giao dịch phải lùi."""
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  findings=[_fd("A#x")])
        with pytest.raises(sa.exc.IntegrityError):
            kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  ho_so_id=r["ho_so_id"], findings=[_fd("B#y")])
        d = kho.doc_ho_so(r["ho_so_id"])
        assert len(d["cac_lan"]) == 1 and d["phat_sinh"] == []

    def test_lan_dau_hong_KHONG_de_lai_ho_so_rong(self, kho):
        """Hồ sơ mới được INSERT trước lần 1. Lần 1 hỏng (mã việc trùng) mà hồ sơ
        còn lại thì danh sách hồ sơ có một hồ sơ không lần nào, không baseline."""
        kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                              findings=[_fd("A#x")])
        with pytest.raises(sa.exc.IntegrityError):
            kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="b", danh_tinh=_dt(),
                                  findings=[_fd("B#y")])
        assert [h["ten_file"] for h in kho.ds_ho_so()] == ["a"]

    def test_ds_ho_so_dem_lan_va_loi(self, kho):
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  findings=[_fd("A#x"), _fd("B#y")])
        kho.ghi_lan_tham_dinh(ma_viec="m2", ten_file="a", danh_tinh=_dt(),
                              ho_so_id=r["ho_so_id"], findings=[])
        (h,) = kho.ds_ho_so()
        assert (h["so_lan"], h["so_loi_baseline"]) == (2, 2)

    def test_doc_ho_so_khong_ton_tai_la_None(self, kho):
        assert kho.doc_ho_so(12345) is None

    def test_lan_moi_nhat_cho_5_3(self, kho):
        """5.3 dùng lại câu trả lời model của lần có số thứ tự LỚN NHẤT."""
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a", danh_tinh=_dt(),
                                  findings=[_fd("A#x")])
        h = r["ho_so_id"]
        assert kho.lan_moi_nhat(h)["ma_viec"] == "m1"
        kho.ghi_lan_tham_dinh(ma_viec="m2", ten_file="a", danh_tinh=_dt(), ho_so_id=h,
                              findings=[])
        assert (kho.lan_moi_nhat(h)["ma_viec"], kho.lan_moi_nhat(h)["so_thu_tu"]) == \
            ("m2", 2)
        assert kho.lan_moi_nhat(999) is None

    def test_phien_ban_luoc_do_la_2(self):
        assert ld.PHIEN_BAN_LUOC_DO == "2"


# --- 2026-09-17: lỗi mở CSDL phải nói cách sửa ----------------------------------
class TestGoiYSua:
    # Nguyên văn `/health` trên máy nội bộ sau nghiệm thu 5.1.
    LOI_THAT = ('(psycopg.OperationalError) connection failed: connection to server at '
                '"172.18.0.4", port 5432 failed: FATAL:  password authentication '
                'failed for user "copilot"')

    def test_sai_mat_khau_chi_ra_nguyen_nhan_hay_gap_va_lenh_sua(self):
        from src.luu_tru.cau_hinh import goi_y_sua
        g = goi_y_sua(self.LOI_THAT)
        assert "LẦN ĐẦU" in g and "ALTER USER" in g
        assert "mã hoá phần trăm" in g

    def test_goi_y_nam_TRUOC_loi_tho_de_khong_bi_cat_mat(self, monkeypatch):
        """Thông điệp bị cắt 600 ký tự; lỗi thô của psycopg dài và kèm link."""
        from src.luu_tru import cau_hinh

        class _Hong:
            def __init__(self, url):
                raise RuntimeError(self_loi)

        self_loi = self.LOI_THAT + " x" * 500
        import src.luu_tru.kho as kho_mod
        monkeypatch.setattr(kho_mod, "KhoCSDL", _Hong)
        monkeypatch.setenv(BIEN_URL, "postgresql+psycopg://copilot:bi-mat@copilot-db/c")
        _, tt = cau_hinh.mo_kho_tu_moi_truong()
        assert "ALTER USER" in tt.thong_diep
        assert "bi-mat" not in tt.thong_diep

    def test_loi_khong_nhan_ra_thi_khong_bia_goi_y(self):
        from src.luu_tru.cau_hinh import goi_y_sua
        assert goi_y_sua("một lỗi lạ") == ""

    def test_csdl_chua_len_thi_noi_se_tu_thu_lai(self):
        from src.luu_tru.cau_hinh import goi_y_sua
        assert "tự thử lại" in goi_y_sua("connection refused")


# ------------------------------------------------ 5.2: ghi nhận lần sửa -----------
class TestLanSua:
    def _ho_so(self, kho):
        r = kho.ghi_lan_tham_dinh(ma_viec="m1", ten_file="a.docx", danh_tinh=_dt(),
                                  findings=[_fd("A#x"), _fd("B#y")])
        d = kho.doc_ho_so(r["ho_so_id"])
        return r["ho_so_id"], [b["id"] for b in d["baseline"]]

    def test_so_lan_tang_theo_tung_dong(self, kho):
        h, (a, b) = self._ho_so(kho)
        assert kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="32→64 GB")["so_lan"] == 1
        assert kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="64→48 GB")["so_lan"] == 2
        assert kho.them_lan_sua(h, b, danh_tinh=_dt(), noi_dung_sua="x")["so_lan"] == 1

    def test_doc_finding_co_lich_su_trang_thai_va_lan_moi_nhat(self, kho):
        h, (a, _) = self._ho_so(kho)
        kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="Đã tăng RAM Redis",
                         noi_dung_goc="Redis dùng 32 GB")
        d = kho.doc_finding(h, a)
        assert d["trang_thai"] == "chua_dat"
        assert d["lan_moi_nhat"]["ma_viec"] == "m1"
        assert [(x["so_lan"], x["noi_dung_sua"], x["ten"]) for x in d["lan_sua"]] == \
            [(1, "Đã tăng RAM Redis", "Nguyễn Văn A")]
        assert d["lan_sua"][0]["noi_dung_goc"] == "Redis dùng 32 GB"

    def test_bang_ho_so_dem_so_lan_sua_moi_dong(self, kho):
        h, (a, b) = self._ho_so(kho)
        kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="1")
        kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="2")
        so = {x["id"]: x["so_lan_sua"] for x in kho.doc_ho_so(h)["baseline"]}
        assert so == {a: 2, b: 0}

    def test_finding_cua_ho_so_khac_thi_KHONG_ghi_duoc(self, kho):
        """Chặn ghi nhầm sang hồ sơ khác qua một id đoán mò."""
        from src.luu_tru.kho import KhongCoFinding
        h1, (a, _) = self._ho_so(kho)
        r2 = kho.ghi_lan_tham_dinh(ma_viec="m9", ten_file="b", danh_tinh=_dt(),
                                   findings=[_fd("C#z")])
        with pytest.raises(KhongCoFinding):
            kho.them_lan_sua(r2["ho_so_id"], a, danh_tinh=_dt(), noi_dung_sua="x")
        assert kho.doc_finding(r2["ho_so_id"], a) is None

    def test_ho_so_da_gui_duyet_thi_KHONG_ghi_nhan_sua(self, kho):
        from src.luu_tru.kho import HoSoKhongDangSua
        h, (a, _) = self._ho_so(kho)
        kho.dat_trang_thai_ho_so(h, "cho_duyet")
        with pytest.raises(HoSoKhongDangSua):
            kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua="x")

    @pytest.mark.parametrize("nd", ["", "   ", "x" * 10_001])
    def test_noi_dung_rong_hoac_qua_dai_bi_chan(self, kho, nd):
        h, (a, _) = self._ho_so(kho)
        with pytest.raises(ValueError):
            kho.them_lan_sua(h, a, danh_tinh=_dt(), noi_dung_sua=nd)
