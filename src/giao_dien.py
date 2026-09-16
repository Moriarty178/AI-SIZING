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


def kiem_model_qua_dich_vu(sk) -> TrangThaiModel:
    """Trạng thái model là của DỊCH VỤ THẨM ĐỊNH, không phải của tiến trình vẽ giao diện.

    Từ mục B3 (2026-09-09) giao diện KHÔNG gọi model — nó nộp file cho API rồi
    tra theo mã việc. Nên container `copilot-ui` không có `SIZING_COPILOT_API_KEY`
    và **không nên có**: khoá chỉ cần ở nơi thật sự gọi gateway.

    Hỏi `kiem_model()` ngay trong container giao diện thì luôn nhận
    «Chưa đặt biến môi trường SIZING_COPILOT_API_KEY», và `che_do_kha_dung` GIẤU
    LUÔN chế độ «Thẩm định đầy đủ» — tức giấu đúng thứ người dùng mở giao diện để
    làm, dù API bên cạnh vẫn chạy tốt. Xảy ra thật trên máy nội bộ 2026-09-14.

    `sk` là `src.khach_api.SucKhoe`; nhận kiểu lỏng để `src/giao_dien.py` không
    phải kéo theo mô-đun khách API chỉ vì một chú thích kiểu.
    """
    if not sk.song:
        return TrangThaiModel(False, f"Chưa gọi được dịch vụ thẩm định — {sk.thong_diep}")
    if not sk.model_san_sang:
        return TrangThaiModel(
            False, f"Dịch vụ chạy nhưng chưa gọi được model — {sk.ghi_chu_model}")
    return TrangThaiModel(True, sk.ghi_chu_model or "Dịch vụ thẩm định sẵn sàng")


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


# ------------------------------------------------- bảng ghi chú thẩm định --
# Dữ liệu phản hồi người thẩm định (PLAN.md 4.1): cột đọc-only dựng từ findings
# đã persist, cột ghi_chu + phân loại do người điền. Logic thuần Python ở đây để
# test được offline; `ui/app.py` chỉ vẽ.
PHAN_LOAI = {"": "(chưa phân loại)", "chap_nhan": "Chấp nhận",
             "bao_sai": "Báo sai", "can_ban": "Cần bàn"}
NHAN_PHAN_LOAI = list(PHAN_LOAI.values())
THU_TU_MUC_DO = ["critical", "major", "minor", "info"]
NOI_DUNG_TOI_DA = 200

_NHOM_NHAN = {"vong1": "Vòng 1", "vong2_chua_dat": "Vòng 2 — chưa đạt",
              "vong2_chua_kiem": "Vòng 2 — chưa kiểm được",
              "vong2_tam_hoan": "Vòng 2 — tạm hoãn", "khac": "Khác"}


def chuan_bi_bang(findings: list[dict],
                  phan_hoi_cu: dict[str, dict] | None = None,
                  labels=None) -> list[dict]:
    """1 finding đã persist → 1 dòng bảng. Prefill ghi chú cũ nếu có.

    KHÔNG đưa `rule_quote`/`computed_evidence` vào bảng: tràn cột với hàng trăm
    dòng; nguyên văn vẫn còn đầy đủ trong findings.json và báo cáo.
    """
    from .reporting.report import load_labels
    labels = labels or load_labels()
    phan_hoi_cu = phan_hoi_cu or {}
    rows: list[dict] = []
    for f in findings:
        cu = phan_hoi_cu.get(f["id"]) or {}
        ghi = str(cu.get("ghi_chu") or "")
        loai = str(cu.get("phan_loai") or "")
        noi = " ".join(str(f.get("finding") or "").split())
        if len(noi) > NOI_DUNG_TOI_DA:
            noi = noi[:NOI_DUNG_TOI_DA - 1] + "…"
        rows.append({
            "finding_id": f["id"],
            "mức độ": labels.severity_label(f.get("severity", "")),
            "mã quy tắc": f.get("rule_ref") or "—",
            "nội dung": noi,
            "vị trí": f.get("location") or "—",
            "phân hệ": f.get("scope_key") or "cả hệ thống",
            "nhóm": _NHOM_NHAN.get(f.get("nhom", ""), f.get("nhom", "")),
            "ghi_chu": ghi,
            "phân loại": PHAN_LOAI.get(loai, PHAN_LOAI[""]),
            "xem": False,
        })
    return rows


def loc_bang(rows: list[dict], muc: str, labels=None) -> list[dict]:
    """Lọc theo nhãn mức độ rồi sắp: nghiêm trọng trước, ngang mức thì theo mã
    quy tắc — để dòng cần xử lý nhất luôn trên cùng."""
    from .reporting.report import load_labels
    labels = labels or load_labels()
    if muc != "Tất cả":
        rows = [r for r in rows if r["mức độ"] == muc]
    thu_tu = {k: i for i, k in enumerate(THU_TU_MUC_DO)}

    def khoá(r):
        key = next((k for k in THU_TU_MUC_DO
                    if labels.severity_label(k) == r["mức độ"]), "")
        return (thu_tu.get(key, len(THU_TU_MUC_DO)), r["mã quy tắc"])
    return sorted(rows, key=khoá)


def gom_thay_doi(rows_goc: list[dict], rows_sau: list[dict]) -> list[dict]:
    """So theo finding_id, trả payload POST chỉ gồm dòng THAY ĐỔI.

    Người bấm Lưu hai lần thì lần hai payload rỗng — không nhân bản dòng nhật ký.
    """
    goc = {r["finding_id"]: r for r in rows_goc}
    ds: list[dict] = []
    for r in rows_sau:
        o = goc.get(r["finding_id"])
        if o is None:
            continue
        loai_sau = next((k for k, v in PHAN_LOAI.items() if v == r["phân loại"]), "")
        if o["ghi_chu"] != r["ghi_chu"] or (o["phân loại"] != r["phân loại"]):
            ds.append({"finding_id": r["finding_id"],
                       "ghi_chu": r["ghi_chu"],
                       "phan_loai": loai_sau})
    return ds


COT_DOC_ONLY = ["finding_id", "mức độ", "mã quy tắc", "nội dung", "vị trí",
                "phân hệ", "nhóm"]
COT_RONG = ["nội dung", "ghi_chu"]        # cột cho phép rộng — text dài
COT_TUY_CHON = ["phân loại"]
COT_XEM = "xem"                           # checkbox tạm xem chi tiết dưới bảng


def noi_dung_day_du(f: dict) -> str:
    """Markdown chi tiết ĐẦY ĐỦ của một finding cho khung xem dưới bảng.

    Bảng cắt «nội dung» ở 200 ký tự để vừa cột; khung này trả nguyên văn kèm
    căn cứ (quote/evidence) và gợi ý sửa — người thẩm định không phải lăn ngược
    lên báo cáo để đọc chi tiết.
    """
    cac_phan = [str(f.get("finding") or "").strip() or "(không có nội dung)"]
    if f.get("rule_quote"):
        cac_phan.append(f"**Nguyên văn quy tắc:** {f['rule_quote']}")
    if f.get("computed_evidence"):
        cac_phan.append(f"**Căn cứ tính toán:** {f['computed_evidence']}")
    if f.get("suggestion"):
        cac_phan.append(f"**Gợi ý sửa:** {f['suggestion']}")
    return "\n\n".join(cac_phan)


def spec_cot_bang() -> dict:
    """Cấu hình cột cho `st.data_editor`. Tách hàm vì nó cần module streamlit
    (chỉ cài cùng giao diện) — ui/app.py gọi, test offline bỏ qua."""
    import streamlit as st
    return {
        c: st.column_config.TextColumn(width="medium") for c in COT_DOC_ONLY
    } | {
        "nội dung": st.column_config.TextColumn(width="large"),
        "ghi_chu": st.column_config.TextColumn(width="large"),
        "phân loại": st.column_config.SelectboxColumn(options=NHAN_PHAN_LOAI),
        COT_XEM: st.column_config.CheckboxColumn(
            "🔍 Xem chi tiết", help="Tick để hiện nguyên văn đầy đủ + căn cứ + "
            "gợi ý sửa ngay dưới bảng.", default=False),
    }


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


# ------------------------------------------------------ 5.1 — hồ sơ ------
NHAN_TRANG_THAI_HO_SO = {
    "dat": "✅ Đạt (không còn xuất hiện)",
    "chua_dat": "❌ Chưa đạt",
    "chua_kiem_duoc": "❔ Chưa kiểm được",
    None: "—",
}
NHAN_KET_LUAN_BOI = {"c4": "Code (C4)", "c5": "Model (C5)", "khong_ro": "—", None: "—"}


def csdl_san_sang(tho_health: dict) -> bool:
    """Giao diện chỉ hiện phần hồ sơ khi DỊCH VỤ báo CSDL sẵn sàng."""
    return bool(((tho_health or {}).get("csdl") or {}).get("san_sang"))


def nhan_ho_so(h: dict) -> str:
    return (f"#{h['id']} · {h['ten_file']} · {h.get('so_lan', 0)} lần · "
            f"{h.get('so_loi_baseline', 0)} lỗi · {h.get('ten', '')}")


def tom_tat_ho_so(d: dict) -> dict:
    """Số liệu của LẦN MỚI NHẤT, kèm số thứ tự lần — để tiêu đề rổ phát sinh nói
    đúng «sau lần sửa N»."""
    lan = (d.get("cac_lan") or [{}])[-1]
    dem = lan.get("dem") or {}
    return {"so_loi_baseline": d.get("so_loi_baseline", 0),
            "so_thu_tu": lan.get("so_thu_tu", 0),
            "dat": dem.get("dat", 0), "chua_dat": dem.get("chua_dat", 0),
            "chua_kiem_duoc": dem.get("chua_kiem_duoc", 0),
            "phat_sinh": dem.get("phat_sinh", 0)}


def bang_baseline(d: dict) -> list[dict]:
    """Dòng bảng baseline. Mức độ ĐÓNG BĂNG theo baseline (5.6); lần này khác thì
    ghi chú trong ngoặc, không thay cột chính."""
    ra = []
    for b in d.get("baseline") or []:
        muc = b.get("muc_do", "")
        if b.get("muc_do_lan"):
            muc = f"{muc} (lần này: {b['muc_do_lan']})"
        ra.append({
            "Quy tắc": b.get("rule_ref", ""),
            "Phân hệ": b.get("scope_goc", ""),
            "Mức độ": muc,
            "Trạng thái": NHAN_TRANG_THAI_HO_SO.get(b.get("trang_thai"), "—"),
            "Ai kết luận": NHAN_KET_LUAN_BOI.get(b.get("ket_luan_boi"), "—"),
            "Nội dung (lần đầu)": b.get("noi_dung", ""),
            "Căn cứ lần đầu": b.get("computed_evidence", ""),
            "Căn cứ lần này": b.get("computed_evidence_lan", ""),
            "Vị trí": b.get("vi_tri", ""),
        })
    return ra


def bang_phat_sinh(d: dict) -> list[dict]:
    return [{"Quy tắc": p.get("rule_ref", ""), "Phân hệ": p.get("scope_goc", ""),
             "Mức độ": p.get("muc_do", ""), "Nội dung": p.get("noi_dung", ""),
             "Căn cứ": p.get("computed_evidence", ""), "Vị trí": p.get("vi_tri", "")}
            for p in d.get("phat_sinh") or []]
