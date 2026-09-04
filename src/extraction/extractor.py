"""C3 (1.7) — trích trường từ bản sizing bằng structured output.

Ba quyết định thiết kế, mỗi cái đều bắt nguồn từ một ràng buộc hoặc một phép đo thật.

**1. Model trả NGUYÊN VĂN, code mới ra số.**
Không hỏi model "cpu_95th bằng bao nhiêu" rồi nhận `85.0`. Hỏi *"trong tài liệu ghi
nguyên văn là gì"* rồi nhận `"85%"`, và `src/normalization/numbers.py` mới quyết định
đó là số mấy. Lý do: `"1.500"` là 1500 hay 1,5 là một **quyết định dưới sự mơ hồ**,
và 1.4 đã dựng cả một thang suy luận có cờ `ambiguous` cho đúng việc đó. Để model trả
thẳng số là đi vòng qua thang ấy và **âm thầm chọn một cách đọc** — sai một lần lệch
1000 lần. Lần dò 1.2 cho thấy model đọc đúng 12/12, nhưng 12 mẫu không phải căn cứ để
giao việc; NT1 nói code quyết định.
Đổi lại còn được `raw` cho `ExtractedValue` — thứ NT2 cần để dẫn nguồn.

**2. Trích dẫn phải NEO ĐƯỢC vào tài liệu, nếu không thì vứt.**
Model phải trả kèm câu chứa giá trị. Code tìm lại câu đó trong `DocxDocument`; không
thấy thì **không dùng giá trị**, ghi lý do. Đây là cổng chống bịa: một con số không tìm
lại được trong văn bản thì không có căn cứ (NT2), và một finding dựng trên nó sẽ dẫn
người dùng tới một chỗ không tồn tại. Thà thiếu còn hơn sai.

**3. Trường enum chỉ lấy khi tài liệu NÊU RÕ.**
Đo ở 1.2: khi mục đích sizing được nêu tường minh, cả 3 model đúng **6/6**; khi phải
suy ra thì chỉ **3/6** và ba model phân kỳ. `loai_sizing` lại quyết định `applies_when`
của `MTH-01..04`, nên đọc sai nó làm **chạy nhầm cả nhóm quy tắc phương pháp** cho toàn
tài liệu. Nên mọi enum đều có giá trị hợp lệ `khong_neu`, và code **bắt buộc** phải neo
được câu dẫn thì mới nhận — suy đoán thì thành `None` + finding "thiếu thông tin" (NT4).

KHÔNG tính toán gì ở đây (NT1). Quy đổi đơn vị là chuẩn hoá xác định của 1.4, không
phải phép tính nghiệp vụ; và khi không quy đổi được thì để `None` chứ không đoán.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, create_model

from ..ingestion.anchor import neo as _neo_doc
from ..ingestion.docx_reader import DocxDocument, Element
from ..llm.client import ExtractionFailed, LLMClient, LLMError
from ..normalization.numbers import parse_number
from ..normalization.units import UnknownUnit, Units, load_units
from ..validators.rules_loader import RuleSet
from .plan import NhomTrich, ThamSo, ke_hoach_trich
from .schema import ExtractedValue, SizingCore, SizingExtension

KHONG_NEU = "khong_neu"
MAX_KY_TU_NGU_CANH = 60_000     # ngữ cảnh 200k–1M token (0.10) nên không cần cắt gắt


# ---------------------------------------------------------------- lược đồ --
class GiaTriSo(BaseModel):
    gia_tri_nguyen_van: str = Field(
        description="Nguyên văn giá trị trong tài liệu, GIỮ NGUYÊN dấu chấm/phẩy và "
                    "đơn vị, ví dụ '1.500 GB'. Chuỗi rỗng nếu tài liệu không nêu.")
    cau_chua: str = Field(
        description="Nguyên văn câu hoặc dòng bảng chứa giá trị, chép đúng từng chữ. "
                    "Chuỗi rỗng nếu tài liệu không nêu.")


class GiaTriBool(BaseModel):
    gia_tri: Literal["dung", "sai", KHONG_NEU] = Field(
        description="dung / sai theo tài liệu; khong_neu nếu tài liệu không đề cập.")
    cau_chua: str = Field(description="Nguyên văn câu chứa căn cứ. Rỗng nếu không có.")


def _lop_enum(t: ThamSo) -> type[BaseModel]:
    """Lớp riêng cho một tham số enum — `Literal` để lược đồ có ràng buộc `enum`.

    Bài học 1.2: khai `str` rồi liệt kê giá trị trong `description` là không đủ —
    model trả cụm tiếng Việt tự do, hợp lược đồ nhưng vô dụng, và chuỗi đó còn khác
    nhau giữa hai lần chạy.
    """
    opts = tuple(t.options) + (KHONG_NEU,)
    return create_model(
        f"GiaTri_{t.name}",
        gia_tri=(Literal[opts],  # type: ignore[valid-type]
                 Field(description=f"Một trong: {', '.join(t.options)}. "
                                   f"Chọn {KHONG_NEU} nếu tài liệu KHÔNG nêu rõ — "
                                   f"không được suy đoán.")),
        cau_chua=(str, Field(description="Nguyên văn câu chứa căn cứ.")),
    )


def luoc_do_nhom(nhom: NhomTrich) -> type[BaseModel]:
    """Lược đồ Pydantic cho một lượt gọi, dựng từ kế hoạch (NT3)."""
    truong: dict = {}
    for t in nhom.tham_so:
        if t.kieu == "bool":
            lop: type[BaseModel] = GiaTriBool
        elif t.kieu == "enum":
            lop = _lop_enum(t)
        else:
            lop = GiaTriSo
        don_vi = f" (đơn vị quy tắc dùng: {t.unit})" if t.unit else ""
        truong[t.name] = (lop, Field(description=f"{t.mo_ta}{don_vi}"))
    return create_model(f"Trich{nhom.ma_nhom}{nhom.phan}", **truong)


# ------------------------------------------------------------------ neo ----
@dataclass
class ThongKe:
    """Chẩn đoán một lần chạy C3. Cái gì rơi rụng thì phải đếm, không im lặng."""

    luot_goi: int = 0
    luot_goi_hong: int = 0
    truong_hoi: int = 0
    truong_co_gia_tri: int = 0
    khong_neo_duoc: int = 0
    khong_doc_duoc_so: int = 0
    khong_quy_doi_duoc: int = 0
    luong_nghia: int = 0
    loi: list[str] = field(default_factory=list)

    def tom_tat(self) -> str:
        return (f"{self.luot_goi} lượt gọi ({self.luot_goi_hong} hỏng) · "
                f"{self.truong_co_gia_tri}/{self.truong_hoi} trường có giá trị · "
                f"{self.khong_neo_duoc} không neo được · "
                f"{self.khong_doc_duoc_so} không đọc được số · "
                f"{self.khong_quy_doi_duoc} không quy đổi được · "
                f"{self.luong_nghia} lưỡng nghĩa")


class Extractor:
    def __init__(self, client: LLMClient | None = None, *, rules: RuleSet | None = None,
                 units: Units | None = None, model: str | None = None):
        self.client = client or LLMClient()
        self.rules = rules
        self.units = units or load_units()
        self.model = model
        self.tk = ThongKe()

    # -------------------------------------------------------------- ngữ cảnh
    def ngu_canh(self, doc: DocxDocument, section: str = "") -> str:
        els = doc.by_section(section) if section else doc.elements
        dong = [f"[{e.location}] {e.text}" for e in els if e.text]
        s = "\n".join(dong)
        return s[:MAX_KY_TU_NGU_CANH]

    # ------------------------------------------------------------------ neo
    def neo(self, doc: DocxDocument, cau: str, gia_tri: str
            ) -> tuple[Element | None, str]:
        """Tìm lại câu model trích trong tài liệu. (phần tử, cách neo)."""
        el, i = _neo_doc(doc, cau, gia_tri)
        return el, ("câu", "giá trị")[i] if i >= 0 else ""

    # ------------------------------------------------------- dựng giá trị --
    def _so(self, t: ThamSo, raw: str, ev: ExtractedValue) -> ExtractedValue | None:
        pn = parse_number(raw)
        if pn is None:
            self.tk.khong_doc_duoc_so += 1
            ev.note = f"không đọc được số từ {raw!r}"
            ev.value = None
            return ev

        ev.value, ev.ambiguous = pn.value, pn.ambiguous
        if pn.ambiguous:
            self.tk.luong_nghia += 1
            ev.note = pn.note
            ev.confidence = "vua"

        # `parse_quantity` NÉM UnknownUnit khi sau số không có đơn vị — mà "92%",
        # "12 máy", "1,2" là những ca hoàn toàn bình thường. Không có đơn vị nghĩa là
        # không có gì để quy đổi, không phải lỗi.
        try:
            q = self.units.parse_quantity(raw)
        except UnknownUnit:
            q = None
        ev.unit = q.unit if q else (t.unit or None)
        if q and q.ambiguous:
            ev.ambiguous = True
            ev.note = "; ".join(x for x in (ev.note, q.note) if x)

        # Quy đổi về ĐÚNG đơn vị quy tắc dùng. Bỏ bước này thì "1,5 TB" đi vào một
        # biểu thức tính bằng GB sẽ lệch 1024 lần mà không ai thấy.
        #
        # Nhiều đơn vị trong `rules.yaml` cố ý KHÔNG có trong `units.yaml` (`IOPS`,
        # `máy`, `core`, `points`, `hệ số`, `%`) — chúng là đơn vị đếm, không quy đổi
        # và cũng không cần. Đó là lý do `UnknownUnit` ở đây là chuyện bình thường,
        # khác hẳn ca "biết đơn vị nhưng khác nhóm" ngay dưới.
        if not (t.unit and q):
            return ev
        try:
            nhom_qt, dv_qt = self.units.resolve(t.unit)
        except UnknownUnit:
            return ev                          # đơn vị đếm — giữ nguyên số

        if q.group != nhom_qt:
            # Biết cả hai đơn vị nhưng khác nhóm (khai `GB` mà tài liệu ghi `Mbps`).
            # KHÔNG đưa cho C4 một con số sai đơn vị — thà nói không kiểm được (NT4).
            self.tk.khong_quy_doi_duoc += 1
            ev.value = None
            ev.note = "; ".join(x for x in (
                ev.note, f"đơn vị tài liệu ({q.unit}, nhóm {q.group}) khác nhóm đơn vị "
                         f"quy tắc dùng ({t.unit}, nhóm {nhom_qt})") if x)
        elif q.unit != dv_qt:
            ev.value = self.units.convert(pn.value, q.unit, dv_qt)
            ev.unit = dv_qt
            ev.note = "; ".join(x for x in (
                ev.note, f"quy đổi {pn.value:g} {q.unit} → {ev.value:g} {dv_qt}") if x)
        return ev

    def dung_gia_tri(self, doc: DocxDocument, t: ThamSo, o: BaseModel
                     ) -> ExtractedValue | None:
        """Một trường model trả về → `ExtractedValue`, hoặc None nếu không dùng được."""
        cau = getattr(o, "cau_chua", "") or ""
        tho = getattr(o, "gia_tri_nguyen_van", None)
        gia_tri_enum = getattr(o, "gia_tri", None)
        raw = tho if tho is not None else (gia_tri_enum or "")

        if not raw or raw == KHONG_NEU:
            return None                       # tài liệu không nêu -> để C4 báo thiếu

        el, cach = self.neo(doc, cau, raw)
        if el is None:
            # Không tìm lại được trong tài liệu ⇒ không có căn cứ (NT2). Bỏ.
            self.tk.khong_neo_duoc += 1
            return None

        ev = ExtractedValue(raw=raw, location=el.location, element_index=el.index,
                            confidence="cao" if cach == "câu" else "vua")
        if cach != "câu":
            ev.note = "chỉ neo được theo giá trị, không tìm thấy nguyên văn câu model trích"

        if t.kieu == "bool":
            ev.value = (gia_tri_enum == "dung")
        elif t.kieu == "enum":
            ev.value = gia_tri_enum
        else:
            ev = self._so(t, raw, ev)          # type: ignore[assignment]
        return ev

    # ------------------------------------------------------------ một nhóm --
    def trich_nhom(self, doc: DocxDocument, nhom: NhomTrich, dich: SizingCore | SizingExtension,
                   *, section: str = "", ten_phan_he: str = "") -> None:
        lop = luoc_do_nhom(nhom)
        self.tk.luot_goi += 1
        self.tk.truong_hoi += len(nhom.tham_so)
        pham_vi = f" của phân hệ «{ten_phan_he}»" if ten_phan_he else " ở cấp toàn hệ thống"
        try:
            kq = self.client.extract(lop, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    f"Trích các thông tin sau{pham_vi} từ tài liệu định cỡ dưới đây.\n"
                    f"{NHAC_NHO}\n\n=== TÀI LIỆU ===\n{self.ngu_canh(doc, section)}"},
            ], model=self.model)
        except (ExtractionFailed, LLMError) as e:
            # Hết lượt thử vẫn không ra JSON hợp lệ: KHÔNG bịa giá trị (NT4).
            # Để trống, C4 sẽ sinh finding "thiếu thông tin" cho từng tham số.
            self.tk.luot_goi_hong += 1
            self.tk.loi.append(f"{nhom.ten}: {e}")
            return

        for t in nhom.tham_so:
            ev = self.dung_gia_tri(doc, t, getattr(kq, t.name))
            if ev is not None and ev.value is not None:
                dich.params[t.name] = ev
                self.tk.truong_co_gia_tri += 1
            elif ev is not None:
                dich.params[t.name] = ev       # giữ note để báo cáo nói được vì sao

    # ------------------------------------------------------ nhận diện phân hệ
    def nhan_dien_phan_he(self, doc: DocxDocument) -> list[SizingExtension]:
        self.tk.luot_goi += 1
        try:
            kq = self.client.extract(DanhSachPhanHe, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    "Liệt kê các PHÂN HỆ được định cỡ trong tài liệu dưới đây "
                    "(Application, Database, Redis, Kafka, K8s, LB/FW…). "
                    "Chỉ liệt kê phân hệ tài liệu thực sự có mục riêng; không suy đoán."
                    f"\n\n=== TÀI LIỆU ===\n{self.ngu_canh(doc)}"},
            ], model=self.model)
        except (ExtractionFailed, LLMError) as e:
            self.tk.luot_goi_hong += 1
            self.tk.loi.append(f"nhận diện phân hệ: {e}")
            return []

        ra = []
        for p in kq.phan_he:
            if not p.ten_phan_he.strip():
                continue
            el, _ = self.neo(doc, p.muc, p.ten_phan_he)
            ra.append(SizingExtension(
                ten_phan_he=p.ten_phan_he.strip(),
                cong_nghe=p.cong_nghe.strip() or None,
                cong_nghe_luu_tru=p.cong_nghe_luu_tru.strip() or None,
                location=el.location if el else ""))
        return ra

    # ------------------------------------------------------ cấp tài liệu ----
    def trich_cap_tai_lieu(self, doc: DocxDocument, core: SizingCore) -> None:
        self.tk.luot_goi += 1
        try:
            kq = self.client.extract(ThongTinChung, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    "Trích thông tin chung của bản định cỡ dưới đây.\n" + NHAC_NHO +
                    f"\n\n=== TÀI LIỆU ===\n{self.ngu_canh(doc)}"},
            ], model=self.model)
        except (ExtractionFailed, LLMError) as e:
            self.tk.luot_goi_hong += 1
            self.tk.loi.append(f"thông tin chung: {e}")
            return

        core.ten_he_thong = kq.ten_he_thong.strip() or None
        core.ma_pyc = kq.ma_pyc.strip() or None
        core.dau_moi_yeu_cau = kq.dau_moi_yeu_cau.strip() or None
        core.don_vi_phat_trien = kq.don_vi_phat_trien.strip() or None
        core.don_vi_dinh_co = kq.don_vi_dinh_co.strip() or None
        core.thoi_gian_cam_ket = kq.thoi_gian_cam_ket.strip() or None

        # `loai_sizing` chỉ nhận khi model chọn một giá trị cụ thể VÀ câu dẫn tìm lại
        # được trong tài liệu. Xem quyết định 3 ở đầu module.
        if kq.loai_sizing != KHONG_NEU:
            el, _ = self.neo(doc, kq.cau_chua_muc_dich, kq.muc_dich_sizing)
            if el is not None:
                core.loai_sizing = kq.loai_sizing       # type: ignore[assignment]
                core.muc_dich_sizing = kq.muc_dich_sizing.strip() or None
            else:
                self.tk.khong_neo_duoc += 1
        if kq.muc_do_quan_trong != KHONG_NEU:
            core.muc_do_quan_trong = kq.muc_do_quan_trong   # type: ignore[assignment]

    # ------------------------------------------------------------------ run
    def run(self, doc: DocxDocument, *, chi_nhom: list[str] | None = None) -> SizingCore:
        core = SizingCore()
        self.trich_cap_tai_lieu(doc, core)
        core.phan_he = self.nhan_dien_phan_he(doc)

        for nhom in ke_hoach_trich(self.rules, scope="he_thong", chi_nhom=chi_nhom):
            self.trich_nhom(doc, nhom, core)

        for ph in core.phan_he:
            for sc in ("phan_he", "phan_he_x_cong_nghe_luu_tru"):
                if sc == "phan_he_x_cong_nghe_luu_tru" and not ph.cong_nghe_luu_tru:
                    continue
                for nhom in ke_hoach_trich(self.rules, scope=sc, chi_nhom=chi_nhom):
                    self.trich_nhom(doc, nhom, ph, ten_phan_he=ph.ten_phan_he)
        return core


# ------------------------------------------------------------- lược đồ cố định
class PhanHeNhanDien(BaseModel):
    ten_phan_he: str = Field(description="Tên phân hệ đúng như tài liệu gọi")
    cong_nghe: str = Field(description="MariaDB / Redis / Kafka / K8s… Rỗng nếu không nêu")
    cong_nghe_luu_tru: str = Field(description="SSD / SAS / NAS… Rỗng nếu không nêu")
    muc: str = Field(description="Số mục chứa phân hệ, ví dụ 'IV.2'. Rỗng nếu không có")


class DanhSachPhanHe(BaseModel):
    phan_he: list[PhanHeNhanDien]


class ThongTinChung(BaseModel):
    ten_he_thong: str = Field(description="Tên hệ thống. Rỗng nếu không nêu")
    ma_pyc: str = Field(description="Mã phiếu yêu cầu. Rỗng nếu không nêu")
    muc_dich_sizing: str = Field(description="Nguyên văn câu nêu mục đích định cỡ")
    cau_chua_muc_dich: str = Field(
        description="Nguyên văn câu trong tài liệu nêu mục đích định cỡ, chép đúng "
                    "từng chữ. Rỗng nếu tài liệu không nêu.")
    loai_sizing: Literal["cap_moi", "bo_sung", "nang_cap", "ung_cuu", KHONG_NEU] = Field(
        description="Chỉ chọn khi tài liệu NÊU RÕ. Tên hệ thống có hậu tố phiên bản "
                    "(vd '2.0') KHÔNG phải căn cứ để kết luận nâng cấp. Không rõ thì "
                    f"chọn {KHONG_NEU}.")
    muc_do_quan_trong: Literal["dac_biet_quan_trong", "rat_quan_trong", "quan_trong",
                               "binh_thuong", KHONG_NEU] = Field(
        description=f"Mức độ quan trọng của hệ thống. Không nêu thì {KHONG_NEU}.")
    dau_moi_yeu_cau: str = Field(description="Đầu mối yêu cầu. Rỗng nếu không nêu")
    don_vi_phat_trien: str = Field(description="Đơn vị phát triển. Rỗng nếu không nêu")
    don_vi_dinh_co: str = Field(description="Đơn vị định cỡ. Rỗng nếu không nêu")
    thoi_gian_cam_ket: str = Field(description="Thời gian cam kết. Rỗng nếu không nêu")


HE_THONG = (
    "Bạn là công cụ TRÍCH THÔNG TIN từ tài liệu định cỡ hệ thống CNTT tiếng Việt. "
    "Bạn chỉ ĐỌC và CHÉP LẠI, tuyệt đối không tính toán, không quy đổi đơn vị, "
    "không đánh giá đúng sai. Chỉ trả JSON đúng lược đồ."
)

NHAC_NHO = (
    "Quy tắc bắt buộc:\n"
    "- Chép NGUYÊN VĂN, giữ đúng dấu chấm và dấu phẩy trong số "
    "(ví dụ tài liệu ghi '1.500' thì trả '1.500', KHÔNG đổi thành 1500 hay 1,5).\n"
    "- Giữ nguyên đơn vị như tài liệu viết, KHÔNG tự quy đổi.\n"
    "- Trường nào tài liệu không nêu thì để chuỗi rỗng. TUYỆT ĐỐI không suy đoán, "
    "không lấy giá trị mặc định, không tính từ trường khác.\n"
    "- `cau_chua` phải là câu có THẬT trong tài liệu, chép đúng từng chữ; câu không "
    "khớp tài liệu sẽ bị loại bỏ."
)
