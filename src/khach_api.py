"""3.3 — khách gọi API thẩm định. Chỉ thư viện chuẩn, KHÔNG phụ thuộc Streamlit.

Tách khỏi `ui/app.py` cùng lý do `giao_dien.py` tách: test được mà không cần dựng
Streamlit, và sau này còn dùng lại được cho web nội bộ (mục 3.3 bản kế hoạch).

## Vì sao giao diện phải đi qua API thay vì gọi thẳng `pipeline.chay`

Một tài liệu tốn ~16 phút. `ui/app.py` bản cũ gọi thẳng `chay()` và **chặn cả
phiên Streamlit** suốt chừng ấy: đóng tab là mất trắng, tải lại trang là chạy
lại từ đầu, và mỗi người dùng chiếm một tiến trình.

Qua API thì việc chạy nền, người dùng cầm **mã việc** — đóng tab, mở lại, tra
bằng mã vẫn thấy kết quả.

## Ép UTF-8 ở MỌI chỗ đọc

`urllib` trả `bytes`; để Python tự đoán mã là mở đường cho đúng lỗi đã mất một
lượt truy vết ngày 2026-09-09 (`ChÆ°a cÃ³` thay vì `Chưa có`, do đường ống trên
Windows giải mã theo cp1252). Ở đây mọi chỗ `.decode("utf-8")` tường minh.

## KHÔNG có đường lùi "chạy thẳng khi API chết"

Nghe thì tiện, nhưng đường lùi ấy sẽ chặn giao diện 16 phút — đúng cái mà module
này sinh ra để bỏ. API không với tới được thì NÓI RA kèm lệnh khởi động, đừng âm
thầm rơi về lối cũ (NT4).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field

BIEN_DIA_CHI = "SIZING_COPILOT_API"
DIA_CHI_MAC_DINH = "http://localhost:8000"


def dia_chi_mac_dinh() -> str:
    return (os.environ.get(BIEN_DIA_CHI) or DIA_CHI_MAC_DINH).rstrip("/")


class LoiAPI(RuntimeError):
    """Gọi API hỏng. `ma_http` = None nghĩa là không kết nối được."""

    def __init__(self, thong_diep: str, ma_http: int | None = None):
        super().__init__(thong_diep)
        self.ma_http = ma_http


@dataclass
class SucKhoe:
    song: bool
    thong_diep: str = ""
    commit: str = ""
    phien_ban: str = ""
    model_san_sang: bool = False
    ghi_chu_model: str = ""
    dang_cho: int = 0
    tho: dict = field(default_factory=dict)


def _multipart(ten_truong: str, ten_file: str, noi_dung: bytes,
               truong: dict[str, str]) -> tuple[bytes, str]:
    """Gói multipart bằng tay — để không phải thêm một phụ thuộc chỉ vì upload."""
    ranh = "----sizing-copilot-" + uuid.uuid4().hex
    phan: list[bytes] = []
    for k, v in truong.items():
        if v is None or v == "":
            continue
        phan += [f"--{ranh}\r\n".encode(),
                 f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode(),
                 str(v).encode("utf-8"), b"\r\n"]
    phan += [
        f"--{ranh}\r\n".encode(),
        (f'Content-Disposition: form-data; name="{ten_truong}"; '
         f'filename="{ten_file}"\r\n').encode("utf-8"),
        b"Content-Type: application/vnd.openxmlformats-officedocument."
        b"wordprocessingml.document\r\n\r\n",
        noi_dung, b"\r\n", f"--{ranh}--\r\n".encode()]
    return b"".join(phan), f"multipart/form-data; boundary={ranh}"


class KhachAPI:
    def __init__(self, dia_chi: str | None = None, *, timeout: float = 15.0):
        self.dia_chi = (dia_chi or dia_chi_mac_dinh()).rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    def _goi(self, duong: str, *, method: str = "GET", du_lieu: bytes | None = None,
             kieu: str = "", tho: bool = False):
        req = urllib.request.Request(f"{self.dia_chi}{duong}", data=du_lieu,
                                     method=method)
        if kieu:
            req.add_header("Content-Type", kieu)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                van = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            chi_tiet = ""
            try:
                chi_tiet = json.loads(e.read().decode("utf-8")).get("detail", "")
            except Exception:
                pass
            raise LoiAPI(chi_tiet or f"HTTP {e.code}", e.code) from e
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise LoiAPI(f"không kết nối được {self.dia_chi}: {e}", None) from e
        return van if tho else json.loads(van)

    # ------------------------------------------------------------------
    def suc_khoe(self) -> SucKhoe:
        """KHÔNG ném lỗi: giao diện cần vẽ được cả khi API chết."""
        try:
            d = self._goi("/health")
        except LoiAPI as e:
            return SucKhoe(song=False, thong_diep=str(e))
        return SucKhoe(song=True, commit=d.get("commit", ""),
                       phien_ban=d.get("phien_ban", ""),
                       model_san_sang=bool(d.get("model_san_sang")),
                       ghi_chu_model=d.get("ghi_chu_model", ""),
                       dang_cho=int(d.get("dang_cho") or 0), tho=d)

    def nop(self, noi_dung: bytes, ten: str, **tuy_chon) -> dict:
        than, kieu = _multipart("file", ten, noi_dung,
                                {k: v for k, v in tuy_chon.items()})
        return self._goi("/review", method="POST", du_lieu=than, kieu=kieu)

    def viec(self, ma: str) -> dict:
        return self._goi(f"/result/{ma}")

    def bao_cao(self, ma: str) -> str:
        return self._goi(f"/result/{ma}/bao-cao", tho=True)

    def danh_sach(self) -> list[dict]:
        return self._goi("/jobs").get("cong_viec", [])

    def xoa(self, ma: str) -> bool:
        self._goi(f"/result/{ma}", method="DELETE")
        return True
