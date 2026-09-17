"""Cấu hình và trạng thái CSDL. KHÔNG nhập SQLAlchemy ở cấp module.

## Vì sao tách khỏi `kho.py`

`api/main.py` gọi module này lúc khởi động. Nếu nó nhập SQLAlchemy ngay đầu file thì
một image dựng trước khi có nhóm phụ thuộc `db` sẽ sập ngay lúc import — tức một
lần `git pull` làm hỏng dịch vụ đang chạy tốt. Ở đây SQLAlchemy chỉ được nhập khi
người vận hành thật sự đặt `SIZING_COPILOT_DB_URL`.

## Không đặt URL = chạy y như trước

CSDL là TUỲ CHỌN cho tới khi các mục GĐ 5 dùng tới nó. Chưa đặt biến thì Copilot
chạy đúng như bản trước, `/health` nói rõ là chưa cấu hình (NT4) — không im lặng,
không hỏng.

## KHÔNG kết nối trong `/health`

`/health` bị hỏi mỗi 30 giây bởi healthcheck (timeout 5 giây) và mỗi lần giao diện
vẽ lại. Nếu nó thử kết nối CSDL mà CSDL đang tắt, một lần chờ timeout là container
bị đánh dấu *unhealthy*, và `copilot-ui` — vốn chờ `service_healthy` — không khởi
động được. Tức là CSDL hỏng kéo sập cả phần không cần CSDL. Nên chỉ kiểm MỘT lần
lúc khởi động và ghi lại kết quả.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass

BIEN_URL = "SIZING_COPILOT_DB_URL"


@dataclass
class TrangThaiCSDL:
    cau_hinh: bool
    san_sang: bool
    thong_diep: str

    def as_dict(self) -> dict:
        return asdict(self)


def url_tu_moi_truong() -> str:
    return os.environ.get(BIEN_URL, "").strip()


def an_mat_khau(url: str) -> str:
    """Không bao giờ in mật khẩu CSDL — kể cả trong thông báo lỗi.

    Viết tay thay vì dùng `sqlalchemy.engine.make_url` vì module này cố ý không
    nhập SQLAlchemy (xem docstring đầu file).
    """
    if "://" not in url or "@" not in url:
        return url
    dau, _, sau = url.partition("://")
    xac_thuc, _, may = sau.rpartition("@")
    if ":" in xac_thuc:
        xac_thuc = xac_thuc.split(":", 1)[0] + ":***"
    return f"{dau}://{xac_thuc}@{may}"


def goi_y_sua(loi: str) -> str:
    """Gợi ý hành động cho những lỗi mở CSDL đã gặp thật. Rỗng nếu không nhận ra.

    2026-09-17, máy nội bộ: `password authentication failed for user "copilot"` —
    trong khi cùng image đó vừa ghi hồ sơ thành công. Nguyên nhân hay gặp nhất:
    image `postgres` CHỈ đọc `POSTGRES_PASSWORD` ở LẦN ĐẦU khởi tạo volume. Đổi
    `SIZING_COPILOT_DB_PASSWORD` sau đó không đổi mật khẩu trong CSDL, và không có
    gì báo cả — cho tới khi Copilot khởi động lại.
    """
    t = loi.lower()
    if "password authentication failed" in t:
        return (" → Mật khẩu PostgreSQL CHỈ được đặt ở LẦN ĐẦU tạo volume "
                "`copilot-db-data`; sửa `SIZING_COPILOT_DB_PASSWORD` về sau KHÔNG đổi "
                "mật khẩu trong CSDL. Sửa: đặt lại mật khẩu trong CSDL cho khớp `.env` "
                "(`docker compose exec copilot-db psql -U copilot -c \"ALTER USER "
                "copilot PASSWORD '<mật khẩu trong .env>'\"`). Mật khẩu có ký tự "
                "@ : / # % ? thì phải mã hoá phần trăm trong SIZING_COPILOT_DB_URL.")
    if "could not translate host name" in t or "name or service not known" in t:
        return " → Không thấy máy `copilot-db`: `docker compose up -d copilot-db`."
    if "connection refused" in t or "timeout expired" in t:
        return (" → CSDL chưa nhận kết nối (đang khởi động?). Copilot tự thử lại, "
                "không cần khởi động lại.")
    return ""


def mo_kho_tu_moi_truong():
    """(kho hoặc None, TrangThaiCSDL). KHÔNG BAO GIỜ ném lỗi.

    API khởi động được hay không không được phụ thuộc vào CSDL: phần thẩm định
    hiện có (nộp bài, báo cáo, bảng ghi chú 4.1) không cần nó.
    """
    url = url_tu_moi_truong()
    if not url:
        return None, TrangThaiCSDL(
            False, False,
            f"Chưa cấu hình CSDL ({BIEN_URL} trống) — Copilot chạy như bản trước; "
            "các tính năng Giai đoạn 5 chưa dùng được.")
    try:
        from .kho import KhoCSDL
    except ImportError as e:
        return None, TrangThaiCSDL(
            True, False,
            f"Đã đặt {BIEN_URL} nhưng image chưa cài nhóm phụ thuộc `db` ({e}). "
            "Dựng lại image.")
    try:
        kho = KhoCSDL(url)
        kho.khoi_tao()
    except Exception as e:                   # CSDL hỏng không được giết API
        loi = str(e).replace(url, an_mat_khau(url))
        # Gợi ý đặt TRƯỚC phần lỗi thô, để cắt 600 ký tự không cắt mất nó.
        return None, TrangThaiCSDL(
            True, False,
            (f"Không mở được CSDL tại {an_mat_khau(url)}.{goi_y_sua(loi)} "
             f"Lỗi: {type(e).__name__}: {loi}")[:600])
    return kho, TrangThaiCSDL(True, True, f"Sẵn sàng · {an_mat_khau(url)}")
