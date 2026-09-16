"""5.0a — danh tính demo: AI đang thao tác, với VAI gì. KHÔNG nhập SQLAlchemy.

## Đây KHÔNG phải xác thực

Demo Streamlit không có đăng nhập. Ai mở giao diện cũng chọn được vai Admin và gõ
tên bất kỳ. Mục đích duy nhất: cột `vai` + `ten` trong CSDL (5.0) có dữ liệu ngay
từ đầu, để khi ghép vào tool sizing có đăng nhập thật thì CHỈ thay nguồn điền vào
hai cột đó — lược đồ, API, bảng Admin không đổi.

Giao diện phải nói điều này ra, không để người xem tưởng "vai Admin" là quyền thật.

## Đi qua HTTP bằng header MÃ HOÁ PHẦN TRĂM

Giao diện → API → CSDL. Danh tính đi trong hai header `X-Copilot-Vai`,
`X-Copilot-Ten`. Tên phải mã hoá phần trăm vì header HTTP chỉ chở được latin-1:
`urllib` ném `UnicodeEncodeError` với «Nguyễn Văn Á», còn máy chủ ASGI giải mã
header theo latin-1 nên nhận về chuỗi vỡ `Nguyá»…n` — lỗi thứ hai tệ hơn vì nó
KHÔNG báo gì, chỉ ghi tên hỏng vào CSDL.

Không đặt vào thân yêu cầu: `POST /review` là multipart, các endpoint GĐ 5 sẽ là
JSON — header là chỗ duy nhất chung cho mọi kiểu yêu cầu.
"""
from __future__ import annotations

import urllib.parse
from dataclasses import dataclass

# Khớp ràng buộc CHECK `vai` trong `luoc_do.py` (bảng nào cũng có).
VAI = ("nguoi_lam_sizing", "admin", "he_thong")
# `he_thong` dành cho dòng MÁY ghi (baseline do AI sinh, kết quả lần chạy).
# Người không được chọn nó — nếu không, dòng người ghi và dòng máy ghi lẫn nhau.
VAI_NGUOI_CHON = ("nguoi_lam_sizing", "admin")
NHAN_VAI = {"nguoi_lam_sizing": "Người làm sizing", "admin": "Admin (thẩm định)",
            "he_thong": "Hệ thống"}
TEN_TOI_DA = 200    # = String(200) của cột `ten`

HEADER_VAI = "X-Copilot-Vai"
HEADER_TEN = "X-Copilot-Ten"


@dataclass(frozen=True)
class DanhTinh:
    vai: str
    ten: str

    @property
    def nhan(self) -> str:
        return f"{self.ten} · {NHAN_VAI.get(self.vai, self.vai)}"


def tao_danh_tinh(vai: str, ten: str, *, cho_phep_he_thong: bool = False) -> DanhTinh:
    """Chuẩn hoá + kiểm. Ném `ValueError` với thông điệp tiếng Việt đọc được.

    Kiểm Ở ĐÂY chứ không để CSDL chặn: CSDL chặn thì người dùng nhận một
    `IntegrityError` sau khi đã bấm lưu, không biết sai chỗ nào.
    """
    vai = (vai or "").strip()
    hop_le = VAI if cho_phep_he_thong else VAI_NGUOI_CHON
    if vai not in hop_le:
        raise ValueError(f"Vai «{vai}» không hợp lệ — chỉ nhận: {', '.join(hop_le)}")
    # Gộp khoảng trắng: «Nguyễn  Văn A» và «Nguyễn Văn A» là một người, và bảng
    # Admin lọc theo tên sẽ tách họ làm hai nếu không gộp.
    ten = " ".join((ten or "").split())
    if not ten:
        raise ValueError("Chưa nhập tên — cần để biết ai đã sửa, ai đã ghi chú.")
    if len(ten) > TEN_TOI_DA:
        raise ValueError(f"Tên dài {len(ten)} ký tự, tối đa {TEN_TOI_DA}.")
    return DanhTinh(vai, ten)


def thanh_header(dt: DanhTinh) -> dict[str, str]:
    return {HEADER_VAI: dt.vai, HEADER_TEN: urllib.parse.quote(dt.ten, safe="")}


def tu_header(headers) -> DanhTinh | None:
    """Đọc lại từ header yêu cầu. None = không gửi danh tính. Hỏng → `ValueError`.

    `headers` là bất kỳ mapping nào có `.get` không phân biệt hoa thường
    (Starlette `Headers`, `http.client.HTTPMessage`).
    """
    vai = headers.get(HEADER_VAI)
    ten = headers.get(HEADER_TEN)
    if vai is None and ten is None:
        return None
    return tao_danh_tinh(vai or "", urllib.parse.unquote(ten or ""))
