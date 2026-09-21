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
khởi tạo trên một CSDL mang phiên bản KHÁC thì hoặc nâng cấp được (`nang_cap`), hoặc
DỪNG và nói ra (NT4) — không bao giờ chạy tiếp trên lược đồ lệch.

**Phiên bản 2 (5.1, 2026-09-17)** — thêm `finding_phat_sinh`, và các cột
`lan_tham_dinh.ten_file`, `finding_baseline.computed_evidence` / `nhom_c7`. Bản 1
chưa từng được dựng trên PostgreSQL thật nào nên không có migration; CSDL nào lỡ
mang bản 1 sẽ bị chặn ở `khoi_tao` và phải xoá volume `copilot-db-data`.

**Phiên bản 3 (5.4, 2026-09-18)** — `bao_cao_loi` đổi hình dạng để báo được cả dòng
trong RỔ PHÁT SINH, không chỉ dòng baseline. Từ bản này có migration thật
(`nang_cap`): máy nội bộ đã có hồ sơ thật chạy 6 lần, bắt xoá volume để đổi một bảng
rỗng là mất dữ liệu người dùng vì lý do của chúng ta.

**Phiên bản 4 (5.9 bước 2, 2026-09-21)** — `de_xuat_quy_tac` thêm `ho_so_id`,
`ly_do`, `bang_chung_eval`. Bảng này chưa từng có tính năng nào ghi vào (5.9 bước 1
chỉ làm ba cột Admin), nên nâng cấp = dựng lại; còn dòng thì DỪNG và báo.
"""
from __future__ import annotations

from sqlalchemy import (Boolean, CheckConstraint, Column, DateTime, ForeignKey,
                        Integer, MetaData, String, Table, Text, UniqueConstraint,
                        false, func, text)

from .danh_tinh import TEN_TOI_DA, VAI

PHIEN_BAN_LUOC_DO = "4"

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
#
# Trỏ được vào MỘT trong HAI nguồn: dòng baseline, hoặc dòng trong rổ phát sinh của
# một lần thẩm định. Rổ phát sinh là nơi loại dòng vô lý dễ xuất hiện nhất — nghiệm
# thu 5.3 (2026-09-18) đo được: sửa một ô bảng mà rổ phát sinh có 174 dòng vì C3 kể
# thêm ba phân hệ không có ở lần trước. Không báo được dòng phát sinh thì đúng ca cần
# tiếng nói của người dùng nhất lại không có nút nào.
#
# `ho_so_id` giữ riêng: dòng phát sinh thuộc về một LẦN, nhưng Admin đọc hàng chờ
# theo HỒ SƠ, và câu hỏi "hồ sơ này bị báo mấy lần" không được phụ thuộc vào việc
# join qua lần nào.
bao_cao_loi = Table(
    "bao_cao_loi", metadata,
    Column("id", Integer, primary_key=True),
    _fk("ho_so"),
    Column("finding_baseline_id", Integer,
           ForeignKey("finding_baseline.id", ondelete="CASCADE"), nullable=True,
           index=True),
    Column("finding_phat_sinh_id", Integer,
           ForeignKey("finding_phat_sinh.id", ondelete="CASCADE"), nullable=True,
           index=True),
    # Khoá của dòng bị báo, chép lại lúc báo: rổ phát sinh tính lại theo TỪNG lần
    # (5.1), nên dòng bị báo có thể biến mất ở lần sau — lời báo thì phải còn đọc được.
    Column("khoa", String(400), nullable=False, server_default=""),
    Column("ly_do", Text, nullable=False),
    # `false()` chứ không phải "0": PostgreSQL và SQLite viết hằng boolean khác nhau.
    Column("da_xu_ly", Boolean, nullable=False, server_default=false()),
    CheckConstraint(
        "(finding_baseline_id IS NULL) <> (finding_phat_sinh_id IS NULL)",
        name="mot_nguon"),
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

# 5.9 bước 2 — sửa quy tắc bằng đề xuất: kiểm (nạp được + mọi biểu thức còn phân
# tích được) rồi người chốt mới áp tay vào `config/rules.yaml`. Một lần sửa sai đổi
# mọi lượt thẩm định về sau, cho tất cả mọi người.
#
# `noi_dung_cu`/`noi_dung_moi` là NGUYÊN VĂN khối YAML của quy tắc, không phải cả
# file: cả file 4605 dòng mà phần lớn là chú thích hướng dẫn người nghiệp vụ, chép
# nguyên vào CSDL mỗi lần đề xuất là vô ích. `noi_dung_cu` chụp lại lúc đề xuất — để
# sau này còn đọc được người đề xuất nhìn thấy gì, kể cả khi file đã đổi.
de_xuat_quy_tac = Table(
    "de_xuat_quy_tac", metadata,
    Column("id", Integer, primary_key=True),
    # Hồ sơ làm nảy ra đề xuất. NULL được: Admin mở thẳng một quy tắc để sửa cũng
    # hợp lệ, không nhất thiết phải từ một dòng lỗi.
    Column("ho_so_id", Integer, ForeignKey("ho_so.id", ondelete="SET NULL"),
           nullable=True, index=True),
    Column("rule_ref", String(40), nullable=False),
    Column("noi_dung_cu", Text, nullable=False),
    Column("noi_dung_moi", Text, nullable=False),
    Column("ly_do", Text, nullable=False, server_default=""),
    Column("trang_thai", String(20), nullable=False, server_default="cho_kiem"),
    CheckConstraint(_trong("trang_thai", ("cho_kiem", "kiem_dat", "kiem_hong",
                                          "da_ap", "tu_choi")),
                    name="trang_thai"),
    Column("ket_qua_kiem", Text, nullable=False, server_default=""),
    # Bằng chứng EVAL, người chạy gắn vào sau. Kiểm tự động KHÔNG chạy eval được:
    # cần model và cả kho hồ sơ thật, hàng giờ — không thể là cổng đồng bộ của một
    # lời gọi API. Để trống nghĩa là "chưa ai đo", và giao diện phải nói thế.
    Column("bang_chung_eval", Text, nullable=False, server_default=""),
    _luc(), *_actor(),
)

# Bảng ghi hành động của NGƯỜI — phải có actor. `ket_qua_lan` do máy ghi theo
# `lan_tham_dinh` (đã có actor), `thong_tin_luoc_do` là siêu dữ liệu.
BANG_CO_ACTOR = ("ho_so", "lan_tham_dinh", "finding_baseline", "lan_sua",
                 "bao_cao_loi", "ghi_chu_admin", "quyet_dinh", "de_xuat_quy_tac")


# --------------------------------------------------------------- nâng cấp --
def nang_cap(c, tu: str) -> list[str]:
    """Nâng CSDL từ phiên bản `tu` lên `PHIEN_BAN_LUOC_DO`. Trả danh sách việc đã làm.

    Ném `ValueError` khi không có đường nâng cấp — bên gọi đổi thành lỗi nói rõ phải
    làm gì. KHÔNG bao giờ tự xoá dữ liệu người dùng: bước nào đụng tới bảng còn dòng
    thì dừng và báo, để người vận hành quyết.
    """
    da_lam: list[str] = []
    while tu != PHIEN_BAN_LUOC_DO:
        if tu == "2":
            # 5.4 đổi hình dạng `bao_cao_loi` (thêm hồ sơ + nguồn phát sinh).
            _dung_lai_bang_rong(c, bao_cao_loi, ban="3", muc="5.4")
            da_lam.append("bao_cao_loi: dựng lại theo bản 3 (5.4)")
            tu = "3"
            continue
        if tu == "3":
            # 5.9 bước 2 thêm `ho_so_id`, `ly_do`, `bang_chung_eval`.
            _dung_lai_bang_rong(c, de_xuat_quy_tac, ban="4", muc="5.9 bước 2")
            da_lam.append("de_xuat_quy_tac: dựng lại theo bản 4 (5.9 bước 2)")
            tu = "4"
            continue
        raise ValueError(f"không có đường nâng cấp từ phiên bản lược đồ {tu!r} lên "
                         f"{PHIEN_BAN_LUOC_DO!r}")
    return da_lam


def _dung_lai_bang_rong(c, bang: Table, *, ban: str, muc: str) -> None:
    """Dựng lại một bảng ĐỔI HÌNH DẠNG mà chưa tính năng nào ghi vào.

    Còn dòng thì DỪNG, không xoá: dữ liệu người dùng không bao giờ biến mất vì một
    bước nâng cấp tự động. Người vận hành đọc lời báo rồi quyết.
    """
    n = c.execute(text(f"SELECT COUNT(*) FROM {bang.name}")).scalar() or 0
    if n:
        raise ValueError(
            f"bảng `{bang.name}` đang có {n} dòng nên không dựng lại tự động được — "
            f"cần migration viết tay trước khi nâng lên bản {ban} ({muc})")
    c.execute(text(f"DROP TABLE {bang.name}"))
    bang.create(c)
