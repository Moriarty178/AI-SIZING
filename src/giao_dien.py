"""1.14 — phần logic của giao diện thử, tách khỏi Streamlit để test được offline.

Streamlit không nằm trong nhóm phụ thuộc lõi và không cài trên mọi máy, nên mọi thứ
quyết định được **hành vi** của giao diện phải nằm ở đây: `ui/app.py` chỉ còn việc vẽ.

Ràng buộc thật định hình thiết kế: **hai môi trường tách rời.** Model tự dựng chỉ với
tới được từ máy trong mạng nội bộ, còn phần lớn thời gian làm việc lại ở laptop ngoài.
Nên giao diện phải **chạy có ích khi KHÔNG có model**, và phải nói rõ cái gì đang thiếu
thay vì đổ lỗi mơ hồ hay nổ traceback:

  - đọc tài liệu (C1) và điền checklist (1.17) — **không cần model**, chạy ở đâu cũng được;
  - thẩm định đầy đủ (C3→C7) — **cần model**, chỉ chạy trong mạng nội bộ.

Và **luôn in ước lượng chi phí trước khi cho bấm chạy**. Ngày 2026-09-04 đã mất vài lượt
chạy vì bấm rồi ngồi chờ mù: một hồ sơ 10 phân hệ tốn hàng trăm lượt gọi ≈ hàng chục
phút, không nhìn ra được từ giao diện.
"""
from __future__ import annotations

import pathlib
import tempfile
from dataclasses import dataclass, field

from .extraction.extractor import so_bang_dung_duoc, uoc_tinh_luot_goi
from .ingestion.docx_reader import DocxDocument
from .llm.client import LLMClient, LLMError
from .reporting.dinh_vi_checklist import bang_csv, bang_markdown, dinh_vi
from .validators.qualitative import uoc_tinh_luot_goi_dt
from .validators.rules_loader import RuleSet, load_rules

GIAY_MOI_LUOT = 40          # đo thật 2026-09-04 trên gateway nội bộ

CHE_DO = {
    "doc": "Đọc tài liệu (C1)",
    "checklist": "Điền checklist thẩm định (1.17)",
    "tham_dinh": "Thẩm định đầy đủ (C3 → C7)",
}
CAN_MODEL = {"tham_dinh"}


# --------------------------------------------------------------- giới hạn --
# D3 — nói thẳng công cụ làm được gì và KHÔNG làm được gì, bằng số đã đo.
#
# Demo cho người ngoài mà không nêu những con số này là để họ tự suy ra một công
# cụ khác với công cụ thật. Con số nào cũng phải kèm NGÀY và NGUỒN, để lần sau
# đo lại thì biết sửa ở đâu — và để không ai trích một con số đã cũ.


@dataclass(frozen=True)
class ConSoDoDuoc:
    """Kết quả đo thật, KHÔNG phải mục tiêu hay kỳ vọng. Dải = min–max các lượt."""

    ngay: str
    ho_so: int
    so_luot: int
    recall_chinh: tuple[float, float]       # thước đo hào phóng nhất
    recall_quyet_dinh: tuple[float, float]  # nhóm nhãn đòi TÍNH/SO số
    quyet_dinh_tinh: float                  # …trong đó CODE thật sự tính lại được
    ty_le_chua_doc_duoc: float              # phần báo cáo là "không đọc được"
    phut_moi_tai_lieu: int
    nguon: str


# Nghiệm thu 1.13 ngày 2026-09-11: ba lượt dev độc lập ở nhiệt độ 0,1, xếp nhóm
# theo phán quyết 2026-09-09. Xem `docs/nghiem-thu-1.13-2026-09-11.md`.
DO_LUONG = ConSoDoDuoc(
    ngay="2026-09-11",
    ho_so=14,
    so_luot=3,
    recall_chinh=(0.865, 0.875),
    recall_quyet_dinh=(5 / 71, 6 / 71),
    quyet_dinh_tinh=1 / 71,
    ty_le_chua_doc_duoc=0.949,      # đo trên báo cáo VTracking 2026-09-10
    phut_moi_tai_lieu=16,
    nguon="docs/nghiem-thu-1.13-2026-09-11.md",
)


def _pt(x: float, le: int = 1) -> str:
    """Phần trăm kiểu Việt: dấu phẩy thập phân, KHÔNG làm tròn mất chữ số.

    `f"{0.875:.0%}"` cho «88%» — làm tròn LÊN đúng con số sắp công bố. 87,5% và
    88% là hai điều khác nhau khi có người trích lại.
    """
    return f"{x * 100:.{le}f}".rstrip("0").rstrip(".").replace(".", ",") + "%"


def _dai(ab: tuple[float, float]) -> str:
    """«86,5–87,5%» — nêu DẢI đo được, không nêu một điểm đẹp nhất."""
    a, b = (_pt(x).rstrip("%") for x in ab)
    return f"{a}%" if a == b else f"{a}–{b}%"


def cau_gioi_han(d: ConSoDoDuoc = DO_LUONG) -> list[str]:
    """Những câu PHẢI hiện cho người dùng. Trả list để test được từng câu."""
    return [
        "Đây là công cụ **cố vấn**. Nó KHÔNG phê duyệt và KHÔNG từ chối — "
        "người thẩm định vẫn quyết định cuối cùng.",

        f"Đo trên **{d.ho_so} hồ sơ thật**, {d.so_luot} lượt độc lập ({d.ngay}): "
        f"công cụ chạm tới **{_dai(d.recall_chinh)}** nhận xét của người thẩm "
        f"định trên thước đo hào phóng nhất — nhưng chỉ "
        f"**{_dai(d.recall_quyet_dinh)}** ở nhóm nhận xét đòi TÍNH hoặc SO số, và "
        f"phần công cụ **thật sự tính lại được con số chỉ {_pt(d.quyet_dinh_tinh)}**. "
        "Nhóm sau mới là chỗ khó, và là chỗ công cụ còn rất yếu.",

        f"Khoảng **{_pt(d.ty_le_chua_doc_duoc, 0)}** số dòng trong báo cáo là "
        "*«công cụ chưa đọc được chỗ này»* — **không phải** lỗi của bản sizing. "
        "Đọc mục «Cần xử lý trước khi nộp» ở đầu báo cáo trước.",

        "**Chưa đo được tỉ lệ báo sai.** Một phát hiện không khớp nhận xét nào "
        "của người thẩm định KHÔNG có nghĩa nó sai — nên đừng coi mọi dòng là "
        "đúng, cũng đừng coi là nhiễu. Kiểm lại từng dòng.",

        f"Một tài liệu tốn khoảng **{d.phut_moi_tai_lieu} phút**.",
    ]


@dataclass
class TrangThaiModel:
    san_sang: bool
    thong_diep: str
    chat_model: str = ""

    @property
    def nhan(self) -> str:
        return f"✅ {self.thong_diep}" if self.san_sang else f"⚠️ {self.thong_diep}"


def kiem_model(settings_path: str = "config/settings.yaml") -> TrangThaiModel:
    """Có gọi được model không? KHÔNG ném lỗi — giao diện phải hiện được trong mọi ca.

    Chỉ dựng client, không gọi mạng: một lời gọi thử tốn ~40s và sẽ làm mỗi lần mở
    giao diện đứng im chừng ấy.
    """
    try:
        c = LLMClient(settings_path=settings_path)
    except FileNotFoundError as e:
        return TrangThaiModel(False, f"Chưa có cấu hình model — {e}")
    except LLMError as e:
        return TrangThaiModel(False, f"Chưa gọi được model — {e}")
    except Exception as e:                      # lỗi lạ của SDK cũng không được sập
        return TrangThaiModel(False, f"Chưa gọi được model — {type(e).__name__}: {e}")
    return TrangThaiModel(True, f"Sẵn sàng, model `{c.chat_model}`", c.chat_model)


def che_do_kha_dung(tt: TrangThaiModel) -> list[str]:
    return [k for k in CHE_DO if k not in CAN_MODEL or tt.san_sang]


# ------------------------------------------------------------- ước lượng --
@dataclass
class UocLuong:
    c3: int
    c5: int
    so_phan_he: int
    so_bang: int

    @property
    def tong(self) -> int:
        return self.c3 + self.c5

    def phut(self, song_song: int = 1) -> float:
        return self.tong * GIAY_MOI_LUOT / 60 / max(1, song_song)

    def mo_ta(self, song_song: int = 1) -> str:
        return (f"**{self.tong} lượt gọi** (C3 {self.c3} + C5 {self.c5}) · "
                f"~{self.phut(song_song):.0f} phút với {song_song} luồng · "
                f"giả định {self.so_phan_he} phân hệ, {self.so_bang} bảng dùng được")


def uoc_luong(doc: DocxDocument, *, rules: RuleSet | None = None,
              chi_nhom: list[str] | None = None, chi_vong: int | None = None,
              so_phan_he: int = 5) -> UocLuong:
    """Chi phí dự kiến của chế độ thẩm định đầy đủ, tính TRƯỚC khi gọi model.

    Số bảng đọc thẳng từ tài liệu nên chính xác; số phân hệ thì chưa biết cho tới khi
    C3 chạy, nên để người dùng chỉnh và **nói rõ đó là giả định** — BCCS3 có 13 phân hệ
    trong khi giá trị mặc định cũ là 3, sai số gần 4 lần.
    """
    rs = rules or load_rules()
    sb = so_bang_dung_duoc(doc)
    return UocLuong(
        c3=uoc_tinh_luot_goi(rs, chi_nhom=chi_nhom, so_phan_he=so_phan_he,
                             so_bang=sb)["tong"],
        c5=uoc_tinh_luot_goi_dt(rs, so_phan_he, chi_vong=chi_vong,
                                chi_ma=chi_nhom),
        so_phan_he=so_phan_he, so_bang=sb)


# ------------------------------------------------------------- tài liệu ---
@dataclass
class TomTatTaiLieu:
    phan_tu: int
    de_muc: int
    bang: int
    bang_du_lieu: int
    anh: int
    nguon_trang: str
    canh_bao: list[str] = field(default_factory=list)

    @property
    def dong_tom_tat(self) -> str:
        return (f"{self.phan_tu} phần tử · {self.de_muc} đề mục · {self.bang} bảng "
                f"({self.bang_du_lieu} có số liệu) · {self.anh} ảnh · "
                f"trang: {self.nguon_trang}")


def tom_tat_tai_lieu(doc: DocxDocument) -> TomTatTaiLieu:
    return TomTatTaiLieu(
        phan_tu=len(doc.elements),
        de_muc=sum(1 for e in doc.elements if e.kind == "heading"),
        bang=len(doc.tables()), bang_du_lieu=so_bang_dung_duoc(doc),
        anh=len(doc.images()), nguon_trang=doc.page_source,
        canh_bao=list(doc.warnings))


# ------------------------------------------------------------ checklist ---
@dataclass
class KetQuaChecklist:
    markdown: str
    csv: str
    thay: int
    tong: int

    @property
    def dong_tom_tat(self) -> str:
        return f"Định vị được **{self.thay}/{self.tong}** mục checklist."


def chay_checklist(doc: DocxDocument, ten_tai_lieu: str = "") -> KetQuaChecklist:
    kq = dinh_vi(doc)
    return KetQuaChecklist(
        markdown=bang_markdown(kq, ten_tai_lieu=ten_tai_lieu), csv=bang_csv(kq),
        thay=sum(1 for v in kq if v.tim_thay), tong=len(kq))


# ------------------------------------------------------------ tệp tải lên --
def luu_tam(noi_dung: bytes, ten: str, thu_muc: str | None = None) -> pathlib.Path:
    """Ghi tệp tải lên ra đĩa vì `python-docx` cần đường dẫn thật.

    Giữ nguyên tên gốc: tên hồ sơ mang thông tin (mã PYC, tên hệ thống) và còn hiện
    lại trong báo cáo, nên đổi thành `tmp123.docx` là mất dấu vết.
    """
    d = pathlib.Path(thu_muc or tempfile.mkdtemp(prefix="sizing-copilot-"))
    d.mkdir(parents=True, exist_ok=True)
    p = d / (pathlib.Path(ten).name or "tai-lieu.docx")
    p.write_bytes(noi_dung)
    return p


def ten_file_ket_qua(ten_goc: str, hau_to: str, duoi: str) -> str:
    return f"{pathlib.Path(ten_goc).stem[:60]}-{hau_to}.{duoi}"
