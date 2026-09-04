"""C5 (1.12) — kiểm quy tắc định tính, BẮT BUỘC có trích dẫn (NT2).

50 quy tắc định tính: 19 Vòng 1 (*"tài liệu có phần này chưa"*) và 31 Vòng 2
(*"nội dung có đạt tiêu chí không"*). Đây là **nguồn finding Vòng 1 mà C7 (1.10) đang
thiếu** — luật chặn Vòng 2 đã viết xong nhưng chưa có gì nuôi nó.

**Không cần RAG.** Khảo sát khi bắt đầu 1.12: cả 50 quy tắc đã có sẵn `criteria` (thế
nào là đạt) và `source_doc` (trích dẫn kèm số trang) trong `rules.yaml`, 30 quy tắc còn
có `examples` với ca `pass`/`fail`. Căn cứ NT2 vì thế nằm sẵn trong dữ liệu; RAG (1.11)
là để lấy THÊM ngữ cảnh, không phải điều kiện tiên quyết. Ví dụ pass/fail được dùng làm
few-shot **lấy thẳng từ `rules.yaml`** — không tự viết ví dụ trong code (NT3).

**Căn cứ ở đây bất đối xứng, và đó là chủ ý:**

  phía QUY TẮC   — luôn có, lấy từ `rules.yaml` (`criteria` + `source_doc`).
                   Model KHÔNG được phép tự nghĩ ra tiêu chí.
  phía TÀI LIỆU  — model trích, code phải neo lại được.

Nhưng **"không đạt" thường là do THIẾU, mà cái thiếu thì không trích dẫn được.** Nên C5
KHÔNG đòi trích dẫn tài liệu cho một kết luận không đạt — `rule_ref` + `rule_quote` đã
đủ thoả NT2. Ngược lại, nếu model *có* đưa trích dẫn mà code không tìm lại được thì đó
là dấu hiệu bịa: hạ xuống "không xác định" thay vì tin. Đòi trích dẫn cho ca thiếu sẽ
làm C5 bỏ sót đúng loại lỗi mà Vòng 1 sinh ra để bắt.

`applies_when` do **code** đánh giá (dùng chung `expressions` với C4), không hỏi model.
21/50 quy tắc có nó; thiếu đầu vào để biết quy tắc có áp dụng hay không thì báo "không
đánh giá được", KHÔNG đoán là có áp dụng — đoán sai sẽ sinh cảnh báo cho phần người
dùng còn chưa viết tới (rủi ro R6).
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from ..extraction.schema import SizingCore
from ..ingestion.anchor import neo
from ..ingestion.docx_reader import DocxDocument
from ..llm.client import ExtractionFailed, LLMClient, LLMError
from ..reporting.finding import Finding
from .expressions import danh_gia, thu_thap
from .quantitative import RuleOutcome
from .rules_loader import Rule, RuleSet, load_rules

MAX_KY_TU_NGU_CANH = 60_000


class NhanXetDinhTinh(BaseModel):
    ket_luan: Literal["dat", "khong_dat", "khong_xac_dinh"] = Field(
        description="dat = tài liệu thoả tiêu chí · khong_dat = không thoả · "
                    "khong_xac_dinh = không đủ căn cứ để kết luận")
    trich_dan_tai_lieu: str = Field(
        description="Nguyên văn đoạn trong TÀI LIỆU làm bằng chứng, chép đúng từng "
                    "chữ. Để RỖNG nếu tài liệu không có nội dung liên quan — không "
                    "được bịa. Đoạn không khớp tài liệu sẽ bị loại.")
    ly_do: str = Field(description="Một hoặc hai câu tiếng Việt giải thích kết luận.")


@dataclass
class ThongKeDT:
    """Bộ đếm chẩn đoán. Có khoá riêng vì C5 chạy song song — `x += 1` trên thuộc
    tính int KHÔNG nguyên tử, và mất một lượt đếm là mất một dòng chẩn đoán."""

    luot_goi: int = 0
    luot_goi_hong: int = 0
    dat: int = 0
    khong_dat: int = 0
    khong_xac_dinh: int = 0
    khong_ap_dung: int = 0
    trich_dan_bia: int = 0
    loi: list[str] = field(default_factory=list)

    _khoa: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def tang(self, ten: str, n: int = 1) -> None:
        with self._khoa:
            setattr(self, ten, getattr(self, ten) + n)

    def them_loi(self, s: str) -> None:
        with self._khoa:
            self.loi.append(s)

    def tom_tat(self) -> str:
        return (f"{self.luot_goi} lượt gọi ({self.luot_goi_hong} hỏng) · "
                f"{self.dat} đạt · {self.khong_dat} không đạt · "
                f"{self.khong_xac_dinh} không xác định · "
                f"{self.khong_ap_dung} không áp dụng · "
                f"{self.trich_dan_bia} trích dẫn không neo được")


class QualitativeValidator:
    def __init__(self, client: LLMClient | None = None, *, rules: RuleSet | None = None,
                 model: str | None = None,
                 on_tien_do: Callable[[int, int, str], None] | None = None,
                 song_song: int = 1):
        self.client = client or LLMClient()
        self.rules = rules or load_rules()
        self.model = model
        self.on_tien_do = on_tien_do      # không có tiến trình thì trông y hệt treo
        self.song_song = max(1, int(song_song))
        self.tk = ThongKeDT()

    # ------------------------------------------------------------------
    def ngu_canh(self, doc: DocxDocument) -> str:
        return "\n".join(f"[{e.location}] {e.text}"
                         for e in doc.elements if e.text)[:MAX_KY_TU_NGU_CANH]

    def _rule_quote(self, rule: Rule) -> str:
        """Trích dẫn phía QUY TẮC — luôn từ `rules.yaml`, không bao giờ từ model."""
        return (rule.criteria or rule.name)[:600]

    def _finding(self, rule: Rule, scope_key: str, *, category: str, text: str,
                 location: str = "", suggestion: str = "", severity: str | None = None,
                 confidence: str = "cao") -> Finding:
        return Finding(
            id=f"{rule.id}#{scope_key or 'he_thong'}",
            severity=severity or rule.severity,          # type: ignore[arg-type]
            category=category,                           # type: ignore[arg-type]
            finding=text,
            rule_ref=rule.id,
            rule_quote=self._rule_quote(rule),           # NT2: căn cứ phía quy tắc
            location=location,
            suggestion=suggestion,
            confidence=confidence,                       # type: ignore[arg-type]
            checklist_ref=list(rule.checklist_ref),
            vong=rule.round,
            scope_key=scope_key,
            source_doc=rule.source_doc,
        )

    def _loi_nhac(self, rule: Rule, scope_key: str) -> str:
        pham_vi = f"\nPhạm vi đánh giá: phân hệ «{scope_key}»." if scope_key else ""
        vd = ""
        ex = rule.raw.get("examples") or {}
        if ex.get("pass"):
            vd += "\nVí dụ ĐẠT: " + str(ex["pass"][0])[:400]
        if ex.get("fail"):
            vd += "\nVí dụ KHÔNG ĐẠT: " + str(ex["fail"][0])[:400]
        return (f"Quy tắc {rule.id} — {rule.name}\n"
                f"Tiêu chí đạt: {rule.criteria}{vd}{pham_vi}")

    # ------------------------------------------------------------------
    def check_rule(self, rule: Rule, doc: DocxDocument, core: SizingCore,
                   scope_key: str = "") -> RuleOutcome:
        if not rule.criteria:
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                               "quy tắc không có `criteria`")
        if not rule.enabled:
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                               "đang tắt (`enabled: false`)")

        # --- có áp dụng không: CODE quyết định, không hỏi model ---------
        if rule.applies_when:
            env, missing, _ = thu_thap(rule, core, scope_key, self.rules.globals)
            if missing:
                # Không biết quy tắc có áp dụng hay không thì KHÔNG chạy. Đoán là có
                # sẽ cảnh báo về phần người dùng còn chưa viết tới (rủi ro R6).
                f = self._finding(
                    rule, scope_key, category="thieu_thong_tin",
                    text=f"Chưa xác định được {rule.id} ({rule.name}) có áp dụng hay "
                         f"không vì tài liệu thiếu: {', '.join(missing)}.",
                    suggestion=f"Bổ sung {', '.join(missing)} vào bản sizing.",
                    severity="major")
                return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f,
                                   f"thiếu đầu vào cho `applies_when`: {missing}")
            val, err = danh_gia(rule.applies_when, env)
            if err:
                return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                                   f"lỗi `applies_when`: {err}")
            if not val:
                self.tk.tang("khong_ap_dung")
                return RuleOutcome(rule.id, scope_key, "khong_ap_dung")

        # --- hỏi model -------------------------------------------------
        self.tk.tang("luot_goi")
        try:
            nx = self.client.extract(NhanXetDinhTinh, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    f"{self._loi_nhac(rule, scope_key)}\n\n{NHAC_NHO}\n\n"
                    f"=== TÀI LIỆU ===\n{self.ngu_canh(doc)}"},
            ], model=self.model)
        except (ExtractionFailed, LLMError) as e:
            self.tk.tang("luot_goi_hong")
            self.tk.them_loi(f"{rule.id}#{scope_key}: {e}")
            f = self._finding(
                rule, scope_key, category="khong_kiem_chung_duoc",
                text=f"Chưa kiểm được {rule.id} ({rule.name}) vì lỗi gọi mô hình.",
                suggestion="Chạy lại phần kiểm định tính.",
                severity="info")
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f, str(e))

        return self._doc_nhan_xet(rule, doc, scope_key, nx)

    # ------------------------------------------------------------------
    def _doc_nhan_xet(self, rule: Rule, doc: DocxDocument, scope_key: str,
                      nx: NhanXetDinhTinh) -> RuleOutcome:
        el, _ = neo(doc, nx.trich_dan_tai_lieu) if nx.trich_dan_tai_lieu.strip() \
            else (None, -1)
        trich_bia = bool(nx.trich_dan_tai_lieu.strip()) and el is None
        if trich_bia:
            self.tk.tang("trich_dan_bia")

        if nx.ket_luan == "dat":
            # Kết luận ĐẠT không sinh finding, nên trích dẫn bịa ở đây vô hại — chỉ
            # ghi nhận để đếm. Không hạ cấp, vì hạ cấp một ca đạt thành "không xác
            # định" chỉ làm báo cáo dài thêm mà không thêm thông tin.
            self.tk.tang("dat")
            return RuleOutcome(rule.id, scope_key, "dat", None,
                               el.location if el else "")

        if nx.ket_luan == "khong_dat" and trich_bia:
            # Model dẫn một đoạn KHÔNG có trong tài liệu để kết luận không đạt ⇒ nó
            # đang bịa. Không tin kết luận đó.
            self.tk.tang("khong_xac_dinh")
            f = self._finding(
                rule, scope_key, category="khong_kiem_chung_duoc",
                text=f"Chưa kết luận được {rule.id} ({rule.name}): đoạn được dẫn làm "
                     f"bằng chứng không tìm thấy trong tài liệu.",
                suggestion="Kiểm tay mục này.", severity="info", confidence="thap")
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f,
                               "trích dẫn không neo được")

        if nx.ket_luan == "khong_dat":
            # Vòng 1 = thành phần bắt buộc không có -> `thieu_muc`, đúng nhóm mà luật
            # chặn của C7 dựa vào. Vòng 2 = có mục nhưng nội dung chưa đạt tiêu chí.
            cat = "thieu_muc" if rule.round == 1 else "thieu_thong_tin"
            self.tk.tang("khong_dat")
            f = self._finding(
                rule, scope_key, category=cat, text=nx.ly_do.strip() or rule.name,
                location=el.location if el else "",
                suggestion=f"Bổ sung/làm rõ theo tiêu chí: {rule.criteria[:200]}",
                confidence="cao" if el is not None else "vua")
            return RuleOutcome(rule.id, scope_key, "vi_pham", f)

        self.tk.tang("khong_xac_dinh")
        f = self._finding(
            rule, scope_key, category="khong_kiem_chung_duoc",
            text=f"Chưa kết luận được {rule.id} ({rule.name}): "
                 f"{nx.ly_do.strip() or 'không đủ căn cứ trong tài liệu'}.",
            location=el.location if el else "",
            suggestion="Kiểm tay mục này.", severity="info", confidence="thap")
        return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f,
                           "model không kết luận được")

    # ------------------------------------------------------------------
    def run(self, doc: DocxDocument, core: SizingCore, *, chi_vong: int | None = None,
            chi_ma: list[str] | None = None) -> list[RuleOutcome]:
        """Chấm quy tắc định tính. `chi_vong=1` chạy riêng Vòng 1 — rẻ, và đó chính là
        thứ C7 cần để biết mục nào trượt."""
        ds = [r for r in self.rules.select(type="qualitative", round=chi_vong,
                                           enabled=True)
              if not chi_ma or r.id.split("-")[0] in chi_ma]
        tong = sum(len(core.scope_keys(r.scope)) if r.scope != "he_thong" else 1
                   for r in ds)
        out: list[RuleOutcome] = []
        viec: list[tuple] = []
        for rule in ds:
            try:
                keys = core.scope_keys(rule.scope)
            except ValueError as e:
                out.append(RuleOutcome(rule.id, "", "khong_danh_gia_duoc", None, str(e)))
                continue
            viec += [(rule, k) for k in keys]

        if self.song_song <= 1:
            for i, (rule, key) in enumerate(viec, 1):
                self._bao(i, tong, rule, key)
                out.append(self.check_rule(rule, doc, core, key))
            return out

        with ThreadPoolExecutor(max_workers=self.song_song) as pool:
            fut = {pool.submit(self.check_rule, rule, doc, core, key): (rule, key)
                   for rule, key in viec}
            for i, f in enumerate(as_completed(fut), 1):
                rule, key = fut[f]
                self._bao(i, tong, rule, key)
                out.append(f.result())
        return out

    def _bao(self, i: int, tong: int, rule: Rule, key: str) -> None:
        if self.on_tien_do:
            self.on_tien_do(i, tong, f"{rule.id}{'/' + key if key else ''}")


    def findings(self, doc: DocxDocument, core: SizingCore, **kw) -> list[Finding]:
        """Chỉ finding có căn cứ (NT2)."""
        return [o.finding for o in self.run(doc, core, **kw)
                if o.finding is not None and o.finding.co_can_cu()]


def uoc_tinh_luot_goi_dt(rules: RuleSet, so_phan_he: int = 3, *,
                         chi_vong: int | None = None,
                         chi_ma: list[str] | None = None) -> int:
    """Ước lượng lời gọi của C5 TRƯỚC khi chạy. `applies_when` có thể cắt bớt."""
    n = 0
    for r in rules.select(type="qualitative", round=chi_vong, enabled=True):
        if chi_ma and r.id.split("-")[0] not in chi_ma:
            continue
        n += 1 if r.scope == "he_thong" else so_phan_he
    return n


HE_THONG = (
    "Bạn là trợ lý thẩm định tài liệu định cỡ hệ thống CNTT tiếng Việt. Bạn đối chiếu "
    "tài liệu với MỘT tiêu chí được cho sẵn và kết luận đạt hay không đạt. "
    "Bạn KHÔNG tự nghĩ ra tiêu chí khác, KHÔNG tính toán, KHÔNG đánh giá con số đúng "
    "sai. Chỉ trả JSON đúng lược đồ."
)

NHAC_NHO = (
    "Quy tắc bắt buộc:\n"
    "- Chỉ xét ĐÚNG tiêu chí nêu trên, không thêm yêu cầu nào khác.\n"
    "- `trich_dan_tai_lieu` phải chép NGUYÊN VĂN từ tài liệu, đúng từng chữ. "
    "Nếu tài liệu KHÔNG có nội dung liên quan thì để RỖNG — tuyệt đối không bịa, "
    "không diễn đạt lại. Đoạn không khớp tài liệu sẽ bị loại và kết luận bị huỷ.\n"
    "- Không chắc thì chọn `khong_xac_dinh`, đừng đoán.\n"
    "- `ly_do` viết tiếng Việt, ngắn gọn, nói rõ THIẾU GÌ hoặc ĐÃ CÓ GÌ."
)
