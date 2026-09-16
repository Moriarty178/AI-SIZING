"""Mọi truy cập CSDL của Giai đoạn 5 đi qua đây.

Bản 5.0 chỉ có phần nền: mở kết nối, khởi tạo lược đồ, và đường đi hồ sơ → lần
thẩm định → finding baseline — đủ để kiểm lược đồ đứng được, khoá ngoại và ràng
buộc thật sự chặn. Hàm cho từng tính năng (5.2 ghi nhận sửa, 5.4 báo lỗi, 5.6
bảng Admin…) thêm vào khi làm tính năng đó, KHÔNG viết trước cho có.

Giao diện và API không viết SQL. Khi ghép vào tool sizing, chỉ lớp này đổi.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event, func, insert, select
from sqlalchemy.engine import Engine

from . import luoc_do as ld
from .cau_hinh import an_mat_khau


class LoiCSDL(RuntimeError):
    """Lỗi có thể hành động được — nói rõ phải làm gì, không trần trụi."""


def _bat_khoa_ngoai_sqlite(engine: Engine) -> None:
    """SQLite mặc định TẮT khoá ngoại. Không bật thì test "xoá hồ sơ kéo theo
    con" qua được trên SQLite mà hỏng trên PostgreSQL — test nói dối."""
    @event.listens_for(engine, "connect")
    def _bat(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


class KhoCSDL:
    def __init__(self, url: str):
        self.url_an = an_mat_khau(url)
        tham_so: dict = {"pool_pre_ping": True}
        if url.startswith("postgresql"):
            # Chờ tối đa 5 giây: CSDL tắt thì lúc khởi động API phải báo lỗi
            # nhanh, không treo cả tiến trình.
            tham_so["connect_args"] = {"connect_timeout": 5}
        self.engine = create_engine(url, **tham_so)
        if url.startswith("sqlite"):
            _bat_khoa_ngoai_sqlite(self.engine)

    # ------------------------------------------------------------------ nền --
    def khoi_tao(self) -> None:
        """Tạo bảng còn thiếu; DỪNG nếu CSDL mang phiên bản lược đồ khác.

        Gọi nhiều lần vẫn an toàn. `create_all` KHÔNG sửa bảng đã có, nên chạy
        tiếp trên lược đồ lệch là để lỗi hiện ra ở một câu SQL nào đó giữa
        chừng, xa chỗ gây ra nó (NT4).
        """
        ld.metadata.create_all(self.engine)
        with self.engine.begin() as c:
            co = c.execute(select(ld.thong_tin_luoc_do.c.gia_tri).where(
                ld.thong_tin_luoc_do.c.khoa == "phien_ban")).scalar()
            if co is None:
                c.execute(insert(ld.thong_tin_luoc_do).values(
                    khoa="phien_ban", gia_tri=ld.PHIEN_BAN_LUOC_DO))
            elif co != ld.PHIEN_BAN_LUOC_DO:
                raise LoiCSDL(
                    f"CSDL {self.url_an} mang lược đồ phiên bản {co}, mã hiện tại "
                    f"cần {ld.PHIEN_BAN_LUOC_DO}. Cần chạy migration trước — KHÔNG "
                    "chạy tiếp trên lược đồ lệch.")

    # ----------------------------------------------------- hồ sơ và baseline --
    def tao_ho_so(self, ten_file: str, *, vai: str, ten: str) -> int:
        with self.engine.begin() as c:
            return c.execute(insert(ld.ho_so).values(
                ten_file=ten_file, vai=vai, ten=ten)).inserted_primary_key[0]

    def them_lan_tham_dinh(self, ho_so_id: int, ma_viec: str, *, vai: str, ten: str,
                           commit: str = "") -> tuple[int, int]:
        """(id, số thứ tự). Lần đầu tiên của một hồ sơ là baseline (5.1)."""
        with self.engine.begin() as c:
            so = (c.execute(select(func.max(ld.lan_tham_dinh.c.so_thu_tu)).where(
                ld.lan_tham_dinh.c.ho_so_id == ho_so_id)).scalar() or 0) + 1
            i = c.execute(insert(ld.lan_tham_dinh).values(
                ho_so_id=ho_so_id, so_thu_tu=so, ma_viec=ma_viec, commit=commit,
                vai=vai, ten=ten)).inserted_primary_key[0]
            return i, so

    def them_finding_baseline(self, ho_so_id: int, dong: list[dict]) -> int:
        """Ghi tập lỗi cố định. Trong MỘT giao dịch: hỏng một dòng là không ghi dòng
        nào, để không bao giờ có baseline dở dang."""
        if not dong:
            return 0
        with self.engine.begin() as c:
            c.execute(insert(ld.finding_baseline),
                      [{**d, "ho_so_id": ho_so_id} for d in dong])
        return len(dong)

    def doc_baseline(self, ho_so_id: int) -> list[dict]:
        t = ld.finding_baseline
        with self.engine.connect() as c:
            return [dict(r._mapping) for r in c.execute(
                select(t).where(t.c.ho_so_id == ho_so_id).order_by(t.c.id))]
