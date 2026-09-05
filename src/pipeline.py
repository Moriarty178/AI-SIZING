"""Điều phối `Ingest → Extract → Validate → Report`.

Python thuần, KHÔNG phải agent tự do và chưa dùng LangGraph — thứ tự các bước là cố
định và biết trước, nên một hàm gọi tuần tự là đủ; cân nhắc LangGraph ở Giai đoạn 2 nếu
pipeline phức tạp lên.

    C1 đọc .docx ──► C3 trích trường ──┬──► C4 định lượng (thuần code) ──┐
                                       └──► C5 định tính (LLM + trích dẫn) ──┴──► C7 báo cáo

**C5 chạy SAU C3 và cần kết quả của C3**, không phải vì nội dung mà vì `applies_when`:
21/50 quy tắc định tính chỉ áp dụng trong một số trường hợp, và điều kiện đó tính từ
tham số C3 trích ra. Chạy C5 trước sẽ khiến 4 quy tắc `MTH` cùng nổ trên mọi tài liệu.

**Cảnh báo NT4 về hình ảnh nằm ở đây**, không ở C1. Giai đoạn 1 cố ý bỏ qua ảnh (C2
thuộc Giai đoạn 2), nhưng "bỏ qua" không được phép có nghĩa là **im lặng**: 767 ảnh trên
47 bản sizing thật, và PNX liên tục nhận xét về ảnh sở cứ. Nên pipeline sinh một cảnh
báo "không kiểm chứng được" có căn cứ đếm được (NT2) để người dùng biết phần nào chưa
được máy nhìn tới.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .extraction.extractor import Extractor
from .extraction.schema import SizingCore
from .ingestion.docx_reader import DocxDocument, read_docx
from .llm.client import LLMClient
from .reporting.finding import Finding
from .reporting.report import build_report, load_labels
from .validators.qualitative import QualitativeValidator
from .validators.quantitative import QuantitativeValidator, RuleOutcome
from .validators.rules_loader import RuleSet, load_rules
from .vision.phan_loai import tom_tat_anh

MAX_VI_TRI_LIET_KE = 5      # cảnh báo ảnh chỉ nêu vài vị trí đầu, không đổ cả 767 dòng


def _bao(giai_doan: str, hook):
    """Gắn tên giai đoạn vào tiến trình của từng thành phần."""
    if hook is None:
        return None
    return lambda i, tong, nhan: hook(giai_doan, i, tong, nhan)


@dataclass
class KetQuaChay:
    doc: DocxDocument
    sizing: SizingCore
    ket_qua_dl: list[RuleOutcome] = field(default_factory=list)
    ket_qua_dt: list[RuleOutcome] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    thong_ke: dict = field(default_factory=dict)

    def bao_cao(self) -> str:
        return build_report(self.findings, ten_he_thong=self.sizing.ten_he_thong,
                            ma_pyc=self.sizing.ma_pyc)


def _canh_bao_anh(doc: DocxDocument, anh: list) -> list[Finding]:
    """Cảnh báo NT4 về ảnh, TÁCH THEO LOẠI khi phân loại được (2.2).

    Trước 2.4, cảnh báo này chỉ nói *"tài liệu có 767 hình ảnh chưa đọc được"* —
    đúng nhưng không hành động được. Với 2.2 nó nói được phần nào đáng lo: ảnh
    chụp dòng lệnh là nơi đặt số đo tải làm sở cứ, còn sơ đồ thì không có số nào
    để đối chiếu. Cùng một sự thật, khác hẳn về việc người dùng phải làm.

    Vẫn là cảnh báo `info` chứ không nâng mức: quy tắc và mức độ là dữ liệu
    (NT3), không được tự đặt thêm ở đây. Đây chỉ là mô tả chính xác hơn về phần
    máy CHƯA nhìn tới.
    """
    tt = tom_tat_anh(doc)
    nhan = load_labels().anh_loai

    if not tt.da_phan_loai or not tt.nhom:
        # Không đo được pixel (thiếu Pillow, ảnh vector, file không mở được):
        # vẫn phải nói ra tổng số, và nói rõ vì sao không chia được loại.
        vt = [e.location for e in anh[:MAX_VI_TRI_LIET_KE]]
        them = f" và {len(anh) - len(vt)} ảnh khác" if len(anh) > len(vt) else ""
        ly_do = ("; ".join(tt.canh_bao[:2]) if tt.canh_bao
                 else "không đo được đặc trưng ảnh")
        return [Finding(
            id="NT4-ANH", severity="info", category="khong_kiem_chung_duoc",
            finding=f"Tài liệu có {len(anh)} hình ảnh mà bản này chưa đọc được nội "
                    f"dung. Nếu sở cứ hoặc số liệu nằm trong ảnh thì phần đó CHƯA "
                    f"được kiểm.",
            computed_evidence=f"{len(anh)} ảnh tại: {'; '.join(vt)}{them} "
                              f"(chưa chia được theo loại: {ly_do})",
            suggestion="Đưa số liệu trong ảnh ra thành bảng hoặc văn bản để kiểm được.",
            confidence="cao")]

    ra: list[Finding] = []
    for n in tt.nhom:
        nh = nhan.get(n.loai, {})
        ten = nh.get("ten", n.loai)
        mo_ta = str(nh.get("mo_ta", "")).strip()
        them = (f" và {n.so_luong - len(n.vi_tri)} ảnh khác"
                if n.so_luong > len(n.vi_tri) else "")
        ra.append(Finding(
            id=f"NT4-ANH-{n.loai.upper()}", severity="info",
            category="khong_kiem_chung_duoc",
            finding=f"Tài liệu có {n.so_luong} {ten}"
                    + (f" ({mo_ta})" if mo_ta else "")
                    + ". Bản này chưa đọc được nội dung ảnh, nên phần nằm trong "
                      "chúng CHƯA được kiểm.",
            computed_evidence=f"{n.so_luong}/{tt.tong} ảnh, phân loại bằng đặc trưng "
                              f"ảnh (C2 mục 2.2), tại: {'; '.join(n.vi_tri)}{them}",
            suggestion=str(nh.get("goi_y", "")).strip(),
            confidence="cao"))
    return ra


def canh_bao_nt4(doc: DocxDocument) -> list[Finding]:
    """Những gì Giai đoạn 1 KHÔNG nhìn tới — nói ra, không im lặng bỏ qua (NT4).

    Căn cứ ở đây là `computed_evidence` do code đếm, nên vẫn thoả NT2 dù không gắn
    được vào mã quy tắc nào.
    """
    ra: list[Finding] = []

    anh = doc.images()
    if anh:
        ra += _canh_bao_anh(doc, anh)

    if doc.page_source == "none":
        ra.append(Finding(
            id="NT4-TRANG", severity="info", category="khong_kiem_chung_duoc",
            finding="Không suy được số trang của tài liệu, nên các vị trí trong báo "
                    "cáo chỉ có số mục.",
            computed_evidence=f"page_source={doc.page_source}, "
                              f"{len(doc.elements)} phần tử",
            suggestion="Mở và lưu lại file bằng Word để sinh thông tin phân trang.",
            confidence="cao"))

    for w in doc.warnings:
        ra.append(Finding(
            id="NT4-C1", severity="info", category="khong_kiem_chung_duoc",
            finding=f"Cảnh báo khi đọc tài liệu: {w}",
            computed_evidence=f"nguồn: C1 đọc {doc.path}", confidence="cao"))
    return ra


def chay(path: str, *, client: LLMClient | None = None, rules: RuleSet | None = None,
         model: str | None = None, chi_nhom: list[str] | None = None,
         chi_vong: int | None = None, chi_ma_dt: list[str] | None = None,
         bo_qua_dinh_tinh: bool = False, bo_qua_trich_xuat: bool = False,
         on_tien_do=None, song_song: int = 1) -> KetQuaChay:
    """Chạy trọn pipeline trên một file `.docx`.

    `chi_nhom` / `chi_vong` để giới hạn chi phí khi thử: một tài liệu 5 phân hệ tốn
    95 lượt gọi cho C3 cộng 120 lượt cho C5.
    `bo_qua_trich_xuat=True` chạy C4/C5 trên tài liệu rỗng — chỉ dùng để xem bộ quy
    tắc hỏi những gì, không phải để thẩm định thật.
    """
    rs = rules or load_rules()
    doc = read_docx(path)

    core = SizingCore()
    tk: dict = {"c1_phan_tu": len(doc.elements), "c1_bang": len(doc.tables()),
                "c1_anh": len(doc.images()), "c1_trang": doc.page_source}

    if not bo_qua_trich_xuat:
        c3 = Extractor(client or LLMClient(), rules=rs, model=model,
                       on_tien_do=_bao("C3", on_tien_do), song_song=song_song)
        core = c3.run(doc, chi_nhom=chi_nhom)
        tk["c3"] = dict(c3.tk.__dict__)

    kq_dl = QuantitativeValidator(rs).run(core)
    findings = [o.finding for o in kq_dl if o.finding is not None]

    kq_dt: list[RuleOutcome] = []
    if not bo_qua_dinh_tinh:
        c5 = QualitativeValidator(client or LLMClient(), rules=rs, model=model,
                                  on_tien_do=_bao("C5", on_tien_do),
                                  song_song=song_song)
        kq_dt = c5.run(doc, core, chi_vong=chi_vong, chi_ma=chi_ma_dt)
        findings += [o.finding for o in kq_dt if o.finding is not None]
        tk["c5"] = dict(c5.tk.__dict__)

    findings += canh_bao_nt4(doc)
    # KHÔNG lọc NT2 ở đây — C7 lọc và ĐẾM số bị loại; lọc sớm sẽ giấu mất con số đó.
    return KetQuaChay(doc=doc, sizing=core, ket_qua_dl=kq_dl, ket_qua_dt=kq_dt,
                      findings=findings, thong_ke=tk)
