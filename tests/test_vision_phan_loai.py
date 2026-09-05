"""Test C2/2.2 — phân loại ảnh. Chạy offline, không cần Pillow.

Luật phân loại được test bằng cách bơm thẳng `DacTrungAnh` với các giá trị ĐO
ĐƯỢC trên 40 ảnh mẫu (`data/nhan_anh_mau.json`), nên mỗi test là hồi quy cho một
ca thật chứ không phải số bịa.
"""
import pytest

from src.vision import phan_loai as pl
from src.vision.anh import Anh


def _anh(**kw) -> Anh:
    kw.setdefault("ma", "anh#1")
    kw.setdefault("element_index", 1)
    return Anh(**kw)


def _dt(**kw) -> pl.DacTrungAnh:
    return pl.DacTrungAnh(**kw)


@pytest.fixture
def bom(monkeypatch):
    """Thay phép đo pixel bằng số cho trước — test luật, không test Pillow."""
    def _bom(dt):
        monkeypatch.setattr(pl, "do_dac_trung", lambda data: dt)
    return _bom


# --- bốn lớp, mỗi lớp một ca thật ------------------------------------------
def test_nen_toi_chu_day_la_console(bom):
    # số của ảnh "terminal top" trong mẫu
    bom(_dt(sang=0.08, toi=0.90, so_mau=32, xam=1.0, vivid=0.048, tr_tb=17.5, tr_cao=0.58))
    kq = pl.phan_loai(_anh(), b"x")
    assert kq.loai == "console" and kq.do_tin == "cao"
    assert any("chữ dày" in t for t in kq.tin_hieu)


def test_nen_toi_it_chu_la_dashboard(bom):
    # số của ảnh "Grafana chart Kafka"
    bom(_dt(sang=0.12, toi=0.96, so_mau=21, xam=1.0, vivid=0.008, tr_tb=4.7, tr_cao=0.14))
    kq = pl.phan_loai(_anh(), b"x")
    assert kq.loai == "dashboard" and kq.do_tin == "cao"


def test_nen_sang_nhieu_mau_la_so_do(bom):
    # số của ảnh "sơ đồ kiến trúc k8s"
    bom(_dt(sang=0.89, toi=0.00, so_mau=112, xam=0.49, vivid=0.053, tr_tb=7.2, tr_cao=0.25))
    kq = pl.phan_loai(_anh(section_title="MÔ HÌNH HỆ THỐNG"), b"x")
    assert kq.loai == "so_do"
    assert kq.do_tin == "cao"          # có thêm từ khoá ngữ cảnh thì tin hơn


def test_so_do_khong_co_tu_khoa_thi_do_tin_thap_hon(bom):
    bom(_dt(sang=0.93, toi=0.00, so_mau=78, xam=0.93, vivid=0.03, tr_tb=7.0, tr_cao=0.2))
    assert pl.phan_loai(_anh(section_title="TÍNH TOÁN"), b"x").do_tin == "vua"


def test_nen_sang_gan_nhu_khong_mau_la_anh_van_ban(bom):
    # số của ảnh chụp trang kết quả SPEC CINT2006
    bom(_dt(sang=0.94, toi=0.00, so_mau=28, xam=0.99, vivid=0.001, tr_tb=5.9, tr_cao=0.16))
    kq = pl.phan_loai(_anh(), b"x")
    assert kq.loai == "anh_van_ban"


# --- NT4: không chắc thì NÓI KHÔNG CHẮC, không đoán ------------------------
def test_mat_do_chu_nam_giua_hai_nguong_thi_chua_ro(bom):
    bom(_dt(sang=0.15, toi=0.80, so_mau=30, xam=0.9, vivid=0.05, tr_tb=13.0, tr_cao=0.45))
    kq = pl.phan_loai(_anh(), b"x")
    assert kq.loai == "chua_ro" and "mật độ chữ" in kq.ly_do_khong_ro


def test_khong_co_du_lieu_anh_thi_chua_ro_kem_ly_do():
    kq = pl.phan_loai(_anh(), None)
    assert kq.loai == "chua_ro" and kq.ly_do_khong_ro


def test_thieu_pillow_hoac_anh_vector_thi_chua_ro_chu_khong_doan_theo_tu_khoa(bom):
    """Hồi quy cho NT4: không đo được pixel thì KHÔNG được suy ra loại từ chữ."""
    bom(None)
    kq = pl.phan_loai(_anh(section_title="MÔ HÌNH HỆ THỐNG SƠ ĐỒ KIẾN TRÚC",
                           dinh_dang="emf"), b"x")
    assert kq.loai == "chua_ro"
    assert "emf" in kq.ly_do_khong_ro
    assert kq.tin_hieu                      # vẫn ghi lại tín hiệu đã thấy (NT2)


def test_anh_hong_khong_lam_no_do_dac_trung():
    assert pl.do_dac_trung(b"khong phai anh") is None


# --- hồi quy cho vòng cải tiến ĐÃ THỬ VÀ BỎ --------------------------------
def test_tu_khoa_so_do_khong_duoc_TU_QUYET_o_nhanh_nen_sang(bom):
    """Bỏ luật "có từ khoá ⇒ sơ đồ" ngày 2026-09-04: nó kéo 4 ảnh chụp bảng sang
    `so_do` và làm độ chính xác khi kết luận rơi 92% -> 82%."""
    # số của ảnh chụp bảng cấp phát, nằm cạnh chữ "mô hình"
    bom(_dt(sang=0.95, toi=0.00, so_mau=12, xam=0.87, vivid=0.006, tr_tb=13.7, tr_cao=0.28))
    kq = pl.phan_loai(_anh(section_title="Mô hình triển khai", truoc=["Sơ đồ kiến trúc"]),
                      b"x")
    assert kq.loai != "so_do"


def test_moi_ket_luan_deu_kem_tin_hieu_lam_can_cu(bom):
    """NT2: không có tín hiệu thì không được kết luận."""
    for dt in (_dt(sang=0.08, toi=0.90, so_mau=32, xam=1.0, tr_tb=17.5, tr_cao=0.58),
               _dt(sang=0.12, toi=0.96, so_mau=21, xam=1.0, tr_tb=4.7, tr_cao=0.14),
               _dt(sang=0.89, toi=0.00, so_mau=112, xam=0.49, vivid=0.053, tr_tb=7.2)):
        bom(dt)
        kq = pl.phan_loai(_anh(), b"x")
        assert kq.loai != "chua_ro" and kq.tin_hieu
