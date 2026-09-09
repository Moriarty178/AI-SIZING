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


def test_moc_toc_do_THAT_khop_voi_so_da_do():
    """649 lượt / 90 phút ở song song 6 = 7,2 lượt/phút (đo 2026-09-09).

    Mốc này là thứ duy nhất chặn script tái phạm lỗi in "0,3 giờ cho lượt dev"
    từ phép đo lời gọi nhỏ — sai 16,6 lần so với thực tế ~7 giờ.
    """
    assert dss.MUC_THAT == 6
    assert abs(dss.TOC_DO_THAT - 649 / 90) < 0.1


def test_khong_quy_gio_tu_loi_goi_nho(capsys):
    """Bảng chỉ được báo TỈ LỆ giữa các mức; phần quy ra giờ phải đi qua
    `TOC_DO_THAT`. Trước đây script nhân thẳng thông lượng lời gọi nhỏ với số
    lượt mỗi tài liệu và in ra như sự thật."""
    nguon = (pathlib.Path(__file__).resolve().parents[1]
             / "scripts" / "do_song_song.py").read_text(encoding="utf-8")
    than = nguon.split("def main(")[1]
    assert "TOC_DO_THAT * ti_le" in than, "phải quy đổi qua tốc độ thật"
    assert "luot_mot_tai_lieu / tot[" not in than, \
        "không được quy giờ thẳng từ thông lượng lời gọi nhỏ"
    assert "trần cổng, KHÔNG phải tốc độ thật" in than
