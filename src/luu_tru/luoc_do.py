"""Lược đồ CSDL của Giai đoạn 5 — viết MỘT lần cho mọi mục 5.1–5.12.

## Vì sao viết trước cả khi có tính năng dùng tới

`PLAN.md` mục 5.0: mười hai mục mà mỗi mục tự đẻ một định dạng lưu riêng thì câu
"tích hợp vào tool sizing chỉ là đổi lớp kết nối" sẽ sai. Lược đồ này là hợp đồng
chung; các mục sau chỉ thêm HÀM ở `kho.py`, không thêm bảng.

## Chín bảng, và vì sao nhiều hơn năm bảng phác thảo trong PLAN

PLAN phác `phien_tham_dinh → finding_baseline → lan_sua → ghi_chu_admin →
quyet_dinh`. Thêm bốn bảng vì bốn quyết định đã chốt:

- `lan_tham_dinh` + `ket_qua_lan` — baseline ĐÓNG BĂNG (5.1) nhưng mỗi lần thẩm
  định lại ghi trạng thái riêng cho từng dòng. Ghi đè trạng thái lên dòng baseline
  thì mất lịch sử, mà bảng 5.6 cần đủ các cột "Lần sửa 1…n".
- `bao_cao_loi` — nút "Báo lỗi hệ thống" của người dùng (5.4).
- `de_xuat_quy_tac` — Admin sửa quy tắc bằng ĐỀ XUẤT, kiểm rồi mới áp (5.9),
  không ghi thẳng đè `rules.yaml`.

## Cột actor ở MỌI bảng ghi hành động của người (5.0a)

`vai` + `ten`. Demo Streamlit không có đăng nhập, nên đây là danh tính KHÔNG xác
thực — nhưng cột phải có ngay từ đầu: không có nó thì dòng CSDL không có người, và
khi ghép vào tool sizing có đăng nhập thật thì không backfill được.

## Đổi lược đồ

`create_all` chỉ TẠO bảng thiếu, không SỬA bảng đã có. Nên có `PHIEN_BAN_LUOC_DO`:
khởi tạo trên một CSDL mang phiên bản khác thì DỪNG và nói ra (NT4), không chạy
tiếp trên lược đồ lệch. Đổi lược đồ = tăng số này + viết migration.

**Phiên bản 2 (5.1, 2026-09-17)** — thêm `finding_phat_sinh`, và các cột
`lan_tham_dinh.ten_file`, `finding_baseline.computed_evidence` / `nhom_c7`. Bản 1
chưa từng được dựng trên PostgreSQL thật nào nên không có migration; CSDL nào lỡ
mang bản 1 sẽ bị chặn ở `khoi_tao` và phải xoá volume `copilot-db-data`.
"""
from __future__ import annotations

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, ForeignKey,
                        Integer, MetaData, String, Table, Text, UniqueConstraint,
                        false, func)

from .danh_tinh import TEN_TOI_DA, VAI

PHIEN_BAN_LUOC_DO = "2"

# Đặt tên ràng buộc tường minh: PostgreSQL tự sinh tên khác SQLite, và migration
# sau này phải gọi được đúng tên.
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})


def _trong(ten: str, gia_tri: tuple[str, ...]) -> str:
    return f"{ten} IN ({', '.join(repr(g) for g in gia_tri)})"


def _actor() -> list:
    """Ai làm. `he_thong` dành cho dòng do AI sinh (baseline, kết quả lần chạy)."""
    return [
        Column("vai", String(20), nullable=False),
        Column("ten", String(TEN_TOI_DA), nullable=False),
        CheckConstraint(_trong("vai", VAI), name="vai"),
    ]


def _luc() -> Column:
    return Column("tao_luc", DateTime(timezone=True), nullable=False,
                  server_default=func.now())


def _fk(bang: str) -> Column:
    return Column(f"{bang}_id", Integer,
                  ForeignKey(f"{bang}.id", ondelete="CASCADE"), nullable=False,
                  index=True)


thong_tin_luoc_do = Table(
    "thong_tin_luoc_do", metadata,
    Column("khoa", String(50), primary_key=True),
    Column("gia_tri", String(200), nullable=False),
)

# Một hồ sơ = vòng đời một bản sizing: nộp → sửa nhiều lần → gửi duyệt → quyết định.
ho_so = Table(
    "ho_so", metadata,
    Column("id", Integer, primary_key=True),
    Column("ten_file", String(500), nullable=False),
    Column("trang_thai", String(20), nullable=False, server_default="dang_sua"),
    CheckConstraint(_trong("trang_thai",
                           ("dang_sua", "cho_duyet", "da_duyet", "tu_choi")),
                    name="trang_thai"),
    _luc(), *_actor(),
)

# Lần 1 là baseline (5.1). `ma_viec` nối về kho việc của API.
lan_tham_dinh = Table(
    "lan_tham_dinh", metadata,
    Column("id", Integer, primary_key=True),
    _fk("ho_so"),
    Column("so_thu_tu", Integer, nullable=False),
    Column("ma_viec", String(40), nullable=False, unique=True),
    # Tên tệp của CHÍNH lần này — người dùng sửa xong hay lưu thành «…_v2.docx»,
    # nên tên ở `ho_so` (lần đầu) không đủ để truy lại lần sau nộp tệp nào.
    Column("ten_file", String(500), nullable=False, server_default=""),
    Column("commit", String(80), nullable=False, server_default=""),
    UniqueConstraint("ho_so_id", "so_thu_tu", name="ho_so_so_thu_tu"),
    _luc(), *_actor(),
)

# Tập lỗi CỐ ĐỊNH từ lần 1. `khoa` = mã quy tắc + tên phân hệ đã chuẩn hoá (5.1,
# chốt theo 5.0b: 98,6% khớp so với 91,6% của finding_id gốc). `muc_do` đóng băng
# theo baseline (5.6). `nguon='admin'` cho dòng Admin tự thêm (5.10).
finding_baseline = Table(
    "finding_baseline", metadata,
    Column("id", Integer, primary_key=True),
    _fk("ho_so"),
    Column("khoa", String(400), nullable=False),
    Column("finding_id_goc", String(400), nullable=True),
    Column("rule_ref", String(40), nullable=False, server_default=""),
    Column("scope_goc", String(300), nullable=False, server_default=""),
    Column("muc_do", String(20), nullable=False),
    Column("nhom_loi", String(60), nullable=False, server_default=""),
    Column("noi_dung", Text, nullable=False),
    Column("vi_tri", String(300), nullable=False, server_default=""),
    # Con số code tính ở LẦN ĐẦU — để bảng 5.6 đặt cạnh con số của lần sau.
    Column("computed_evidence", Text, nullable=False, server_default=""),
    # Nhóm C7 lúc baseline: vong1 · vong2_chua_dat · vong2_chua_kiem · …
    Column("nhom_c7", String(30), nullable=False, server_default=""),
    Column("nguon", String(10), nullable=False),
    CheckConstraint(_trong("nguon", ("ai", "admin")), name="nguon"),
    UniqueConstraint("ho_so_id", "khoa", name="ho_so_khoa"),
    _luc(), *_actor(),
)

# Trạng thái từng dòng baseline ở MỖI lần thẩm định (5.3, 5.6).
# `dat` = finding không còn xuất hiện (luật 5.3 người dùng chốt 2026-09-16).
ket_qua_lan = Table(
    "ket_qua_lan", metadata,
    Column("id", Integer, primary_key=True),
    _fk("lan_tham_dinh"),
    _fk("finding_baseline"),
    Column("trang_thai", String(20), nullable=False),
    CheckConstraint(_trong("trang_thai", ("dat", "chua_dat", "chua_kiem_duoc")),
                    name="trang_thai"),
    Column("ket_luan_boi", String(10), nullable=False, server_default="khong_ro"),
    CheckConstraint(_trong("ket_luan_boi", ("c4", "c5", "khong_ro")),
                    name="ket_luan_boi"),
    # Mức độ của LẦN NÀY khi khác baseline — chỉ để ghi chú bên cạnh (5.6).
    Column("muc_do_lan", String(20), nullable=True),
    Column("computed_evidence", Text, nullable=False, server_default=""),
    # Giá trị đầu vào C4 đã dùng: 5.0b đo được chỉ 8/11 dòng do code kết luận
    # trùng cả hai lượt, vì đầu vào do C3 trích và dao động.
    Column("dau_vao", Text, nullable=False, server_default=""),
    UniqueConstraint("lan_tham_dinh_id", "finding_baseline_id", name="lan_finding"),
)

# 5.1 — lỗi xuất hiện ở lần thẩm định lại mà KHÔNG có trong baseline. Rổ riêng,
# luôn hiện, KHÔNG cộng vào tổng baseline. Ghi theo TỪNG lần: lần 3 tự so lại với
# baseline, không kế thừa rổ của lần 2 — một lỗi phát sinh ở lần 2 mà lần 3 hết
# thì đã hết thật, không đọng lại.
finding_phat_sinh = Table(
    "finding_phat_sinh", metadata,
    Column("id", Integer, primary_key=True),
    _fk("lan_tham_dinh"),
    Column("khoa", String(400), nullable=False),
    Column("finding_id_goc", String(400), nullable=False, server_default=""),
    Column("rule_ref", String(40), nullable=False, server_default=""),
    Column("scope_goc", String(300), nullable=False, server_default=""),
    Column("muc_do", String(20), nullable=False),
    Column("nhom_loi", String(60), nullable=False, server_default=""),
    Column("nhom_c7", String(30), nullable=False, server_default=""),
    Column("noi_dung", Text, nullable=False),
    Column("vi_tri", String(300), nullable=False, server_default=""),
    Column("computed_evidence", Text, nullable=False, server_default=""),
    UniqueConstraint("lan_tham_dinh_id", "khoa", name="lan_khoa"),
)

# 5.2 — người dùng ghi nhận đã sửa gì. KHÔNG ghi ngược vào .docx (hoãn khỏi GĐ 5).
lan_sua = Table(
    "lan_sua", metadata,
    Column("id", Integer, primary_key=True),
    _fk("finding_baseline"),
    Column("so_lan", Integer, nullable=False),
    Column("noi_dung_goc", Text, nullable=False, server_default=""),
    Column("noi_dung_sua", Text, nullable=False),
    UniqueConstraint("finding_baseline_id", "so_lan", name="finding_so_lan"),
    _luc(), *_actor(),
)

# 5.4 — người dùng báo "hệ thống báo sai / sửa mãi vẫn bị ping".
bao_cao_loi = Table(
    "bao_cao_loi", metadata,
    Column("id", Integer, primary_key=True),
    _fk("finding_baseline"),
    Column("ly_do", Text, nullable=False),
    # `false()` chứ không phải "0": PostgreSQL và SQLite viết hằng boolean khác nhau.
    Column("da_xu_ly", Boolean, nullable=False, server_default=false()),
    _luc(), *_actor(),
)

# 5.9 — CHỈ THÊM, không sửa: mỗi lần Admin đổi ghi chú là một dòng mới, dòng mới
# nhất có hiệu lực. Admin quyết phê duyệt dựa trên đây, nên lịch sử phải còn.
ghi_chu_admin = Table(
    "ghi_chu_admin", metadata,
    Column("id", Integer, primary_key=True),
    _fk("finding_baseline"),
    Column("ghi_chu", Text, nullable=False, server_default=""),
    Column("danh_gia", String(20), nullable=True),
    CheckConstraint(_trong("danh_gia", ("chap_nhan", "tu_choi", "can_ban")),
                    name="danh_gia"),
    Column("loi_o_phia", String(20), nullable=True),
    CheckConstraint(_trong("loi_o_phia", ("nguoi_lam_sizing", "he_thong_ai")),
                    name="loi_o_phia"),
    _luc(), *_actor(),
)

# 5.8 — làm SAU CÙNG trong GĐ 5, nhưng bảng có ngay để không phải đổi lược đồ.
quyet_dinh = Table(
    "quyet_dinh", metadata,
    Column("id", Integer, primary_key=True),
    _fk("ho_so"),
    Column("quyet_dinh", String(20), nullable=False),
    CheckConstraint(_trong("quyet_dinh", ("phe_duyet", "tu_choi")),
                    name="quyet_dinh"),
    Column("ly_do", Text, nullable=False, server_default=""),
    _luc(), *_actor(),
)

# 5.9 — sửa quy tắc bằng đề xuất: kiểm (schema + công thức còn parse + eval không
# tụt) rồi người chốt mới áp. Một lần sửa sai đổi mọi lượt thẩm định về sau.
de_xuat_quy_tac = Table(
    "de_xuat_quy_tac", metadata,
    Column("id", Integer, primary_key=True),
    Column("rule_ref", String(40), nullable=False),
    Column("noi_dung_cu", Text, nullable=False),
    Column("noi_dung_moi", Text, nullable=False),
    Column("trang_thai", String(20), nullable=False, server_default="cho_kiem"),
    CheckConstraint(_trong("trang_thai", ("cho_kiem", "kiem_dat", "kiem_hong",
                                          "da_ap", "tu_choi")),
                    name="trang_thai"),
    Column("ket_qua_kiem", Text, nullable=False, server_default=""),
    _luc(), *_actor(),
)

# Bảng ghi hành động của NGƯỜI — phải có actor. `ket_qua_lan` do máy ghi theo
# `lan_tham_dinh` (đã có actor), `thong_tin_luoc_do` là siêu dữ liệu.
BANG_CO_ACTOR = ("ho_so", "lan_tham_dinh", "finding_baseline", "lan_sua",
                 "bao_cao_loi", "ghi_chu_admin", "quyet_dinh", "de_xuat_quy_tac")
