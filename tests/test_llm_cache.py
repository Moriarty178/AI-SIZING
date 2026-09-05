"""Test 2.12 — đệm lời gọi model. Chạy offline, không chạm mạng.

Mỗi test gắn với một cách đệm có thể làm HỎNG kết quả nếu làm sai, chứ không phải
chỉ kiểm "ghi rồi đọc lại được".
"""
import json

import pytest

from src.llm.cache import BIEN_TAT, BoNhoDem
from src.llm.client import LLMClient, LLMError


class _Phan:
    def __init__(self, content, finish_reason="stop"):
        self.message = type("M", (), {"content": content})()
        self.finish_reason = finish_reason


class _Resp:
    def __init__(self, content, finish_reason="stop"):
        self.choices = [_Phan(content, finish_reason)]


class _Mang:
    """Thay tầng HTTP: đếm số lần thật sự gọi ra ngoài."""

    def __init__(self, tra_ve):
        self.tra_ve = list(tra_ve)
        self.so_lan = 0
        self.chat = type("C", (), {"completions": self})()

    def create(self, **kw):
        self.so_lan += 1
        r = self.tra_ve.pop(0)
        if isinstance(r, Exception):
            raise r
        return _Resp(r) if isinstance(r, str) else r


class ClientGia(LLMClient):
    """Giữ NGUYÊN `chat()` thật (nơi có đệm), chỉ thay tầng mạng."""

    def __init__(self, tra_ve, cache):
        self.chat_model = "fake"
        self.vision_model = ""
        self.temperature = 0.1
        self.cfg = {}
        self.cache = cache
        self._client = _Mang(tra_ve)

    @property
    def so_lan_goi_mang(self) -> int:
        return self._client.so_lan


@pytest.fixture
def dem(tmp_path):
    return BoNhoDem(tmp_path / "dem")


# --- khoá ------------------------------------------------------------------
def test_khoa_khong_doi_theo_thu_tu_khoa_trong_dict(dem):
    a = dem.khoa({"model": "m", "messages": [{"role": "user", "content": "x"}]})
    b = dem.khoa({"messages": [{"role": "user", "content": "x"}], "model": "m"})
    assert a == b


@pytest.mark.parametrize("doi", [
    {"model": "khac"},
    {"temperature": 0.9},
    {"max_tokens": 8000},
    {"response_format": {"type": "json_schema"}},
])
def test_moi_tham_so_doi_duoc_ket_qua_deu_phai_doi_khoa(dem, doi):
    """Thiếu một tham số trong khoá là đệm SAI: đổi model mà trả kết quả cũ thì
    mọi so sánh model đều vô nghĩa."""
    goc = {"model": "m", "messages": [{"role": "user", "content": "x"}],
           "temperature": 0.1, "max_tokens": 4000}
    assert dem.khoa(goc) != dem.khoa({**goc, **doi})


# --- đọc/ghi ---------------------------------------------------------------
def test_ghi_roi_doc_lai_va_dem_dung_trung_truot(dem):
    k = dem.khoa({"a": 1})
    assert dem.lay(k) is None and dem.tk.truot == 1
    dem.luu(k, "kết quả")
    assert dem.lay(k) == "kết quả"
    assert (dem.tk.trung, dem.tk.truot, dem.tk.luu) == (1, 1, 1)


def test_file_dem_hong_thi_coi_nhu_khong_co_chu_khong_lam_no_luot_chay(dem):
    """Lượt chạy bị ngắt giữa chừng có thể để lại file cụt — nó không được phép
    làm hỏng lượt chạy sau, và phải được ĐẾM chứ không nuốt im lặng."""
    k = dem.khoa({"a": 1})
    dem.luu(k, "x")
    p = dem._duong_dan(k)
    p.write_text("{ khong phai json", encoding="utf-8")
    assert dem.lay(k) is None
    assert dem.tk.loi == 1


def test_tat_dem_bang_bien_moi_truong(tmp_path, monkeypatch):
    monkeypatch.setenv(BIEN_TAT, "1")
    d = BoNhoDem(tmp_path / "dem")
    assert d.bat is False
    k = d.khoa({"a": 1})
    d.luu(k, "x")
    assert d.lay(k) is None
    assert not (tmp_path / "dem").exists()


def test_ghi_nguyen_tu_khong_de_lai_file_tam(dem):
    k = dem.khoa({"a": 1})
    dem.luu(k, "x")
    assert list(dem.thu_muc.rglob("*.tmp")) == []
    assert json.loads(dem._duong_dan(k).read_text(encoding="utf-8"))["noi_dung"] == "x"


# --- nối vào client --------------------------------------------------------
def test_loi_goi_lap_lai_khong_ra_mang_lan_hai(dem):
    c = ClientGia(["kết quả A"], dem)
    tin = [{"role": "user", "content": "cùng một câu hỏi"}]
    assert c.chat(tin) == "kết quả A"
    assert c.chat(tin) == "kết quả A"          # lần hai lấy trong đệm
    assert c.so_lan_goi_mang == 1
    assert dem.tk.trung == 1


def test_doi_max_tokens_thi_van_phai_goi_lai(dem):
    c = ClientGia(["A", "B"], dem)
    tin = [{"role": "user", "content": "x"}]
    assert c.chat(tin, max_tokens=1000) == "A"
    assert c.chat(tin, max_tokens=2000) == "B"
    assert c.so_lan_goi_mang == 2


def test_phan_hoi_rong_KHONG_duoc_dem(dem):
    """Bẫy đã làm hỏng 7/53 rồi 2/94 lượt gọi thật: `content` rỗng vì reasoning ăn
    hết `max_tokens`. Đệm ca này sẽ biến một lỗi tạm thời thành vĩnh viễn."""
    c = ClientGia([_Resp("", "length"), "kết quả thật"], dem)
    tin = [{"role": "user", "content": "x"}]
    with pytest.raises(LLMError):
        c.chat(tin)
    assert dem.so_ban_ghi() == 0
    assert c.chat(tin) == "kết quả thật"       # gọi lại được, không bị đóng băng lỗi
    assert c.so_lan_goi_mang == 2


def test_dem_tat_thi_luon_goi_mang(tmp_path):
    d = BoNhoDem(tmp_path / "dem", bat=False)
    c = ClientGia(["A", "A"], d)
    tin = [{"role": "user", "content": "x"}]
    c.chat(tin)
    c.chat(tin)
    assert c.so_lan_goi_mang == 2


def test_uoc_tinh_thoi_gian_tiet_kiem_theo_so_lan_trung(dem):
    dem.tk.trung = 3
    assert dem.tk.tiet_kiem_giay == 120.0       # ~40 giây/lượt, đo thật ở 0.10
