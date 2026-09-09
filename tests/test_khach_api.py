"""Test 3.3 — khách gọi API. OFFLINE: dựng một máy chủ HTTP thật bằng thư viện chuẩn.

Dùng máy chủ thật chứ không giả `urllib`: phần dễ sai nhất của module này là gói
multipart bằng tay và việc ép UTF-8, mà cả hai chỉ lộ ra khi có byte đi qua dây.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from src.khach_api import (BIEN_DIA_CHI, DIA_CHI_MAC_DINH, KhachAPI, LoiAPI,
                           dia_chi_mac_dinh)

NHAN_DUOC: dict = {}


class _Tay(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _tra(self, ma: int, than: bytes, kieu="application/json"):
        self.send_response(ma)
        self.send_header("Content-Type", f"{kieu}; charset=utf-8")
        self.send_header("Content-Length", str(len(than)))
        self.end_headers()
        self.wfile.write(than)

    def _json(self, ma, d):
        self._tra(ma, json.dumps(d, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"song": True, "commit": "abc1234",
                                    "model_san_sang": False,
                                    "ghi_chu_model": "Chưa có settings.yaml",
                                    "dang_cho": 2})
        if self.path.endswith("/bao-cao"):
            return self._tra(200, "# Báo cáo\n\nCPU vượt ngưỡng ở phân hệ Lõi."
                             .encode("utf-8"), "text/plain")
        if self.path == "/jobs":
            return self._json(200, {"cong_viec": [{"ma": "m1"}, {"ma": "m2"}]})
        if self.path == "/result/khongco":
            return self._json(404, {"detail": "Không có việc nào mã «khongco»"})
        return self._json(200, {"ma": "m1", "trang_thai": "xong", "loi": "Chưa có"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        NHAN_DUOC["than"] = self.rfile.read(n)
        NHAN_DUOC["kieu"] = self.headers.get("Content-Type", "")
        self._json(202, {"ma": "moi123", "trang_thai": "cho"})

    def do_DELETE(self):
        self._json(200, {"da_xoa": "m1"})


@pytest.fixture
def kh():
    NHAN_DUOC.clear()
    sv = HTTPServer(("127.0.0.1", 0), _Tay)
    t = threading.Thread(target=sv.serve_forever, daemon=True)
    t.start()
    try:
        yield KhachAPI(f"http://127.0.0.1:{sv.server_address[1]}", timeout=5)
    finally:
        sv.shutdown()
        sv.server_close()


def test_suc_khoe_doc_duoc_tieng_viet(kh):
    sk = kh.suc_khoe()
    assert sk.song and sk.commit == "abc1234"
    assert sk.model_san_sang is False
    assert sk.ghi_chu_model == "Chưa có settings.yaml"
    assert sk.dang_cho == 2


def test_API_chet_thi_KHONG_nem_loi_ma_bao_song_False():
    """Giao diện phải vẽ được cả khi dịch vụ chết — nếu `suc_khoe` ném lỗi thì
    trang trắng, và người dùng không biết vì sao."""
    sk = KhachAPI("http://127.0.0.1:1", timeout=1).suc_khoe()
    assert sk.song is False and "không kết nối được" in sk.thong_diep


def test_nop_goi_multipart_dung_va_kem_tuy_chon(kh):
    d = kh.nop(b"PK\x03\x04noi dung docx", "Định cỡ hệ thống.docx",
               nhom="KPI,CPU", vong=2, song_song=12)
    assert d["ma"] == "moi123"
    than, kieu = NHAN_DUOC["than"], NHAN_DUOC["kieu"]
    assert kieu.startswith("multipart/form-data; boundary=")
    assert b'name="file"; filename="' in than
    assert "Định cỡ hệ thống.docx".encode("utf-8") in than, "tên file phải là UTF-8"
    assert b"PK\x03\x04noi dung docx" in than
    for k, v in ((b"nhom", b"KPI,CPU"), (b"vong", b"2"), (b"song_song", b"12")):
        assert k in than and v in than


def test_truong_rong_KHONG_duoc_gui(kh):
    """Gửi `vong=` rỗng thì FastAPI cố ép sang int và trả 422 — hỏng ở chỗ khó
    đoán. Bỏ hẳn trường rỗng ngay từ phía khách."""
    kh.nop(b"x", "a.docx", nhom="", vong="", song_song=12)
    assert b'name="nhom"' not in NHAN_DUOC["than"]
    assert b'name="vong"' not in NHAN_DUOC["than"]
    assert b'name="song_song"' in NHAN_DUOC["than"]


def test_bao_cao_tra_van_ban_tho_dung_ma(kh):
    bc = kh.bao_cao("m1")
    assert bc.startswith("# Báo cáo")
    assert "vượt ngưỡng" in bc, "ép UTF-8, không để Python tự đoán mã"


def test_loi_HTTP_mang_theo_thong_diep_cua_may_chu(kh):
    with pytest.raises(LoiAPI) as e:
        kh.viec("khongco")
    assert e.value.ma_http == 404
    assert "khongco" in str(e.value)


def test_khong_ket_noi_duoc_thi_ma_http_la_None():
    """Phân biệt «dịch vụ chưa chạy» với «dịch vụ trả lỗi» — hai chuyện cần hai
    lời khuyên khác nhau cho người dùng."""
    with pytest.raises(LoiAPI) as e:
        KhachAPI("http://127.0.0.1:1", timeout=1).viec("m1")
    assert e.value.ma_http is None


def test_danh_sach_va_xoa(kh):
    assert [c["ma"] for c in kh.danh_sach()] == ["m1", "m2"]
    assert kh.xoa("m1") is True


def test_dia_chi_lay_tu_bien_moi_truong(monkeypatch):
    monkeypatch.delenv(BIEN_DIA_CHI, raising=False)
    assert dia_chi_mac_dinh() == DIA_CHI_MAC_DINH
    monkeypatch.setenv(BIEN_DIA_CHI, "http://may-noi-bo:8000/")
    assert dia_chi_mac_dinh() == "http://may-noi-bo:8000"
    assert KhachAPI().dia_chi == "http://may-noi-bo:8000"
