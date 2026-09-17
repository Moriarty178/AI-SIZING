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

import pathlib
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
    ket_qua_anh: list = field(default_factory=list)      # C2 mục 2.3, khi bật
    findings: list[Finding] = field(default_factory=list)
    thong_ke: dict = field(default_factory=dict)
    rules: RuleSet | None = None

    def bao_cao(self) -> str:
        return build_report(self.findings, ten_he_thong=self.sizing.ten_he_thong,
                            ma_pyc=self.sizing.ma_pyc, rules=self.rules)


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
    for i, n in enumerate(tt.nhom, 1):
        nh = nhan.get(n.loai, {})
        ten = nh.get("ten", n.loai)
        mo_ta = str(nh.get("mo_ta", "")).strip()
        them = (f" và {n.so_luong - len(n.vi_tri)} ảnh khác"
                if n.so_luong > len(n.vi_tri) else "")
        ra.append(Finding(
            # Số thứ tự nằm TRONG mã: C7 xếp finding cùng mức độ theo `id`, nên
            # không có nó thì thứ tự ưu tiên dựng ở 2.2 bị xếp lại theo bảng chữ
            # cái — `chua_ro` chạy lên trước `console`. Đã gặp thật khi dựng báo
            # cáo trên bản Vtag.
            id=f"NT4-ANH-{i}-{n.loai.upper()}", severity="info",
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


def _canh_bao_moi_loi_goi_deu_hong(tk: dict) -> list[Finding]:
    """NT4 — lượt chạy mà mọi lời gọi model đều hỏng KHÔNG được trông như bình thường.

    2026-09-16: proxy công ty trả trang lỗi Squid cho từng lời gọi, 43/43 lượt
    C3 và 16/16 lượt C5 hỏng, `truong_co_gia_tri` bằng 0 — và việc vẫn báo
    «xong» với 61 finding, mức độ đủ cả critical/minor/info. Ba lượt chạy và hai
    vòng phân tích đã đổ vào một báo cáo không có một con số nào được trích ra.

    Một báo cáo như thế không phải kết quả thẩm định, và nó phải tự nói điều đó.
    """
    ra: list[Finding] = []
    for ma, ten in (("c3", "trích xuất (C3)"), ("c5", "thẩm định định tính (C5)")):
        d = tk.get(ma)
        if not isinstance(d, dict):
            continue
        goi = int(d.get("luot_goi") or 0)
        hong = int(d.get("luot_goi_hong") or 0)
        if goi and hong >= goi:
            vi_du = "; ".join(str(x) for x in (d.get("loi") or [])[:1])[:200]
            ra.append(Finding(
                id=f"NT4-MODEL-{ma.upper()}", severity="critical",
                category="khong_kiem_chung_duoc",
                finding=f"TOÀN BỘ {goi} lượt gọi model ở bước {ten} đều hỏng. "
                        "Báo cáo này KHÔNG phải kết quả thẩm định — những gì còn "
                        "lại chỉ là phần kiểm được bằng code, và mọi mục cần model "
                        "đang bị bỏ trống chứ không phải đã đạt.",
                computed_evidence=f"{ma}: luot_goi={goi}, luot_goi_hong={hong}"
                                  + (f", ví dụ lỗi: {vi_du}" if vi_du else ""),
                suggestion="Kiểm đường ra tới gateway model: biến HTTP_PROXY/"
                           "HTTPS_PROXY lúc CHẠY phải TRỐNG (xem docker-compose.yml). "
                           "Lỗi trả về là trang HTML của proxy thì lời gọi chưa tới model.",
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
            # TÊN tệp, KHÔNG phải đường dẫn: mỗi lần tải lên, API ghi tệp vào
            # một thư mục `tempfile.mkdtemp()` mới, nên đường dẫn đổi ở MỌI lượt
            # chạy dù tài liệu y nguyên. Hệ quả đo được 2026-09-16: đây là trường
            # DUY NHẤT lệch giữa hai lượt, và nó lệch vì cấu trúc chứ không vì
            # model — đủ để làm hỏng phép đo độ ổn định 5.0b và, sau này, việc
            # đối chiếu baseline của 5.1. Đường dẫn tạm cũng chẳng nói gì với
            # người đọc báo cáo.
            computed_evidence=f"nguồn: C1 đọc {pathlib.Path(doc.path).name}",
            confidence="cao"))
    return ra


def chay(path: str, *, client: LLMClient | None = None, rules: RuleSet | None = None,
         model: str | None = None, chi_nhom: list[str] | None = None,
         chi_vong: int | None = None, chi_ma_dt: list[str] | None = None,
         bo_qua_dinh_tinh: bool = False, bo_qua_trich_xuat: bool = False,
         doc_anh: bool = False, loai_anh=None,
         on_tien_do=None, song_song: int = 1, phat_lai=None) -> KetQuaChay:
    """Chạy trọn pipeline trên một file `.docx`.

    `chi_nhom` / `chi_vong` để giới hạn chi phí khi thử: một tài liệu 5 phân hệ tốn
    95 lượt gọi cho C3 cộng 120 lượt cho C5.
    `bo_qua_trich_xuat=True` chạy C4/C5 trên tài liệu rỗng — chỉ dùng để xem bộ quy
    tắc hỏi những gì, không phải để thẩm định thật.

    `doc_anh` (C2 mục 2.3) **mặc định TẮT**. Người dùng chốt 2026-09-05: lượt đo
    recall chạy sạch trước, không kèm 2.3 — trộn hai thay đổi vào một lượt chạy tốn
    tiền thì không quy được kết quả cho cái nào. Bật lên thì mỗi ảnh thuộc loại đã
    chọn tốn thêm một lượt gọi (~40 giây).

    `phat_lai` (5.3, `src/llm/phat_lai.py`): dùng lại câu trả lời của lần thẩm định
    trước cho lượt hỏi C3/C5 có nội dung không đổi, và ghi lại câu trả lời của lượt
    này. Pipeline vẫn chạy TRỌN — C4 và mọi bước kiểm bằng code chạy lại toàn bộ.
    C2 (đọc ảnh, mặc định tắt) KHÔNG đi qua đây: bật lên thì ảnh được đọc lại mỗi lần.
    """
    rs = rules or load_rules()
    doc = read_docx(path)

    core = SizingCore()
    # Đệm bật hay tắt, và lượt này ghi thêm bao nhiêu bản ghi — bằng chứng
    # NẰM TRONG dữ liệu chứ không nằm ở trí nhớ người chạy. Đo 5.0b ngày
    # 2026-09-16 tốn hai lượt chạy rồi vẫn không kết luận được, chỉ vì không ai
    # chứng minh được lượt sau có thật sự gọi model hay chỉ phát lại từ đệm.
    from .llm.cache import BoNhoDem
    _dem = BoNhoDem()
    tk: dict = {"cache": {"bat": _dem.bat, "ban_ghi_truoc": _dem.so_ban_ghi()},
                "c1_phan_tu": len(doc.elements), "c1_bang": len(doc.tables()),
                "c1_anh": len(doc.images()), "c1_trang": doc.page_source}

    if not bo_qua_trich_xuat:
        c3 = Extractor(client or LLMClient(), rules=rs, model=model,
                       on_tien_do=_bao("C3", on_tien_do), song_song=song_song,
                       phat_lai=phat_lai)
        core = c3.run(doc, chi_nhom=chi_nhom)
        tk["c3"] = dict(c3.tk.__dict__)

    if phat_lai is not None:
        # Vân tay nội dung từng vùng phân hệ — để BÁO phân hệ nào đổi so với lần trước,
        # không để chọn lượt gọi. Hỏng thì chỉ mất dòng báo đó (NT4: nói ra).
        try:
            from .extraction.vung import chuan_ten, van_tay, vung_phan_he
            theo_ten, chung = vung_phan_he(doc, core)
            phat_lai.ghi_vung({"": van_tay(doc, chung),
                               **{chuan_ten(t): van_tay(doc, v)
                                  for t, v in theo_ten.items()}})
        except Exception as e:                      # pragma: no cover — phòng thủ
            tk["phat_lai_loi_vung"] = f"{type(e).__name__}: {e}"[:200]

    # C2 (2.3 đọc ảnh + 2.5 neo số) chạy TRƯỚC C4, không sau như trước 2026-09-09.
    # Thứ tự cũ khiến số 2.5 lấy được không bao giờ kịp vào phép tính của C4 —
    # `scripts/thu_neo_vao_c4.py` đo ra `cpu_95th`/`ram_95th` mà C3 bỏ trống.
    kq_anh: list = []
    findings: list[Finding] = []
    if doc_anh:
        from .vision.doc_anh import LOAI_MAC_DINH, DocAnh
        from .vision.doc_anh import thanh_finding as _finding_anh
        from .vision.neo_so import neo_tai_lieu
        from .vision.tham_so_anh import gan_vao_core
        c2 = DocAnh(client or LLMClient(), model=model,
                    loai=tuple(loai_anh or LOAI_MAC_DINH),
                    on_tien_do=_bao("C2", on_tien_do), song_song=song_song)
        kq_anh = c2.run(doc)
        findings += [_finding_anh(k) for k in kq_anh]
        tk["c2"] = dict(c2.tk.__dict__)
        tk["c2"].pop("_khoa", None)

        ket_neo, tk_neo = neo_tai_lieu(doc, kq_anh)
        tk_gan = gan_vao_core(core, ket_neo)
        tk["c2_neo"] = {k: v for k, v in tk_neo.__dict__.items()}
        tk["c2_gan"] = {k: v for k, v in tk_gan.__dict__.items()}
        from .vision.neo_so import thanh_finding as _finding_neo
        findings += [f for f in (_finding_neo(r) for r in ket_neo) if f is not None]

    kq_dl = QuantitativeValidator(rs).run(core)
    findings += [o.finding for o in kq_dl if o.finding is not None]

    # Hệ số dự phòng thông lượng FW/LB. Đọc thẳng công thức tài liệu tự viết ra,
    # nên chạy được cả khi C3 không trích được tham số nào — đó chính là tình
    # trạng của FWL-02/LBA-01 hiện nay. 0 lượt gọi model.
    from .validators.he_so_du_phong import kiem_he_so_du_phong
    f_hsdp, tk_hsdp = kiem_he_so_du_phong(doc, rs)
    findings += f_hsdp
    tk["c4_he_so_du_phong"] = dict(tk_hsdp.__dict__)

    kq_dt: list[RuleOutcome] = []
    if not bo_qua_dinh_tinh:
        c5 = QualitativeValidator(client or LLMClient(), rules=rs, model=model,
                                  on_tien_do=_bao("C5", on_tien_do),
                                  song_song=song_song, phat_lai=phat_lai)
        kq_dt = c5.run(doc, core, chi_vong=chi_vong, chi_ma=chi_ma_dt)
        findings += [o.finding for o in kq_dt if o.finding is not None]
        tk["c5"] = dict(c5.tk.__dict__)
        tk["c5"].pop("_khoa", None)     # threading.Lock — không serialize được JSON

    findings += _canh_bao_moi_loi_goi_deu_hong(tk)
    if phat_lai is not None:
        tk["phat_lai"] = phat_lai.thong_ke()

    tk["cache"]["ban_ghi_sau"] = _dem.so_ban_ghi()
    tk["cache"]["ghi_them"] = (tk["cache"]["ban_ghi_sau"]
                               - tk["cache"]["ban_ghi_truoc"])

    findings += canh_bao_nt4(doc)
    # KHÔNG lọc NT2 ở đây — C7 lọc và ĐẾM số bị loại; lọc sớm sẽ giấu mất con số đó.
    return KetQuaChay(doc=doc, sizing=core, ket_qua_dl=kq_dl, ket_qua_dt=kq_dt,
                      ket_qua_anh=kq_anh, findings=findings, thong_ke=tk, rules=rs)
