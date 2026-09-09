"""Test A4 — script đo trần song song. OFFLINE, dùng client giả.

Lượt chạy thật 2026-09-09 hỏng hai chỗ cùng lúc: ngân sách token quá nhỏ nên MỌI
lời gọi trả `PhanHoiRong`, rồi script `ZeroDivisionError` ngay sau khi in xong ba
dòng chẩn đoán — làm mất luôn kết luận, đúng lúc người chạy cần nó nhất.
"""
import importlib.util
import pathlib

from src.llm.client import PhanHoiRong

_spec = importlib.util.spec_from_file_location(
    "do_song_song", pathlib.Path(__file__).resolve().parents[1]
    / "scripts" / "do_song_song.py")
dss = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dss)


class _ClientRong:
    """Model tiêu hết ngân sách vào reasoning rồi trả `content` rỗng."""

    def chat(self, messages, **kw):
        raise PhanHoiRong("length", kw.get("max_tokens", 0))


class _ClientTot:
    def chat(self, messages, **kw):
        return "OK"


def test_moi_loi_goi_hong_thi_KHONG_duoc_sap():
    r = dss.do_mot_muc(_ClientRong(), muc=4, n=4, model=None, max_tokens=8)
    assert r["thanh_cong"] == 0
    assert r["luot_moi_phut"] == 0.0
    assert list(r["loi"]) == ["PhanHoiRong[length]"], \
        "phải ghi kèm finish_reason, đừng bắt người đọc log đoán"


def test_loi_ngan_sach_duoc_tach_khoi_loi_tai():
    """`PhanHoiRong` có cách chữa xác định (tăng token); gộp nó vào lỗi mạng sẽ
    khiến người chạy đi nâng/hạ mức song song vô ích."""
    _, _, vi_sao = dss._mot_luot(_ClientRong(), None, 8)
    assert vi_sao.startswith("PhanHoiRong[")


def test_duong_chay_binh_thuong_van_ra_so():
    r = dss.do_mot_muc(_ClientTot(), muc=2, n=4, model=None, max_tokens=4000)
    assert r["thanh_cong"] == 4 and r["luot_moi_phut"] > 0 and r["loi"] == {}


def test_ngan_sach_mac_dinh_bang_muc_dung_that():
    """Đặt 8 token là lỗi đã xảy ra. Mặc định phải bám `DEFAULT_MAX_TOKENS`."""
    from src.llm.client import DEFAULT_MAX_TOKENS
    assert dss.DEFAULT_MAX_TOKENS == DEFAULT_MAX_TOKENS >= 1000
