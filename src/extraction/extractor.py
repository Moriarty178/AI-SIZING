"""C3 (1.7) — trích trường từ bản sizing bằng structured output.

⚠️ **Từ v6, tham số KIỂU SỐ không đi qua đây nữa.** Chúng đi `bang.py`: hỏi từng bảng
*"mỗi cột là tham số nào?"* thay vì hỏi *"tìm 8 tham số này"*. Lý do đầy đủ ở đầu
`bang.py` — tóm tắt: hỏi 98 tham số về một phân hệ chỉ có ~4 con số thì model rải 4 con
số ấy ra, và lượt chạy 19:07 đo được **67% giá trị là điền bừa**. Module này còn lo
enum/bool (thứ tài liệu nói bằng câu chữ), và làm phương án lùi cho tài liệu không có
bảng nào dùng được.

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
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from functools import partial
from typing import Literal

from pydantic import BaseModel, Field, create_model

from ..ingestion.anchor import chuan_hoa as _chuan
from ..ingestion.anchor import neo as _neo_doc
from ..ingestion.docx_reader import DocxDocument, Element
from ..llm.client import ExtractionFailed, LLMClient, LLMError
from ..normalization.numbers import parse_number
from ..normalization.units import UnknownUnit, Units, load_units
from ..validators.rules_loader import RuleSet
from .bang import (KHONG_RO, chu_giai, cot_du_lieu, luoc_do_bang, nhan_dong,
                   phan_vung_bang, tham_so_so)
from .plan import (NhomTrich, ThamSo, ke_hoach_trich,
                   tham_so_cua_bo_quy_tac)
from .schema import ExtractedValue, SizingCore, SizingExtension

KHONG_NEU = "khong_neu"
MAX_KY_TU_NGU_CANH = 60_000     # ngữ cảnh 200k–1M token (0.10) nên không cần cắt gắt
# Dưới ngưỡng này thì mục quá hẹp để tin — lùi về toàn tài liệu.
MIN_KY_TU_NGU_CANH_HEP = 400

# Ngân sách token ĐẦU RA, tính theo số trường thay vì để một hằng số cứng.
# Lượt chạy thật 2026-09-04 18:37: nhóm `KPI/he_thong` **hỏng cả 3 lần thử** với
# `finish_reason=length, max_tokens=4000`. Một lượt 18 trường phải sinh tới 54 chuỗi
# (giá trị + câu chứa + tiêu đề cột), nên 4000 token là không đủ — mà mặc định 4000 vốn
# đặt ra ở 0.10 cho một lời gọi 3 trường.
# Lượt 18:51 vẫn hỏng 7/53 lượt, có lượt 12 trường với ngân sách 4560. Lý do đã biết
# từ 0.10 nhưng tôi chưa tính vào: gateway trả kèm `reasoning_content`, và phần đó ĂN
# VÀO CHÍNH `max_tokens` — nên ngân sách phải phủ cả suy luận lẫn đầu ra.
TOKEN_NEN = 3000
TOKEN_MOI_TRUONG = 450
TOKEN_TOI_DA = 16000        # trần an toàn: model có giới hạn đầu ra riêng


# ---------------------------------------------------------------- lược đồ --
class GiaTriSo(BaseModel):
    gia_tri_nguyen_van: str = Field(
        description="Nguyên văn giá trị trong tài liệu, GIỮ NGUYÊN dấu chấm/phẩy và "
                    "đơn vị, ví dụ '1.500 GB'. CHỈ giá trị, không kèm câu chữ. "
                    "Chuỗi rỗng nếu tài liệu không nêu.")
    cau_chua: str = Field(
        description="Nguyên văn câu hoặc dòng bảng chứa giá trị, chép đúng từng chữ. "
                    "Chuỗi rỗng nếu tài liệu không nêu.")
    # Mặc định rỗng: giá trị lấy từ ĐOẠN VĂN vốn không có tiêu đề cột, nên bắt model
    # phải phát ra chuỗi rỗng cho mọi ca đó chỉ tốn token vô ích.
    tieu_de_cot: str = Field(
        default="",
        description="Nếu giá trị lấy từ BẢNG: tiêu đề cột chứa nó, chép NGUYÊN VĂN từ "
                    "hàng tiêu đề (ví dụ 'CPU (Cint)', 'RAM (GB)'). Rỗng nếu giá trị "
                    "nằm trong đoạn văn chứ không phải bảng.")


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


def _co_ve_la_gia_tri(raw: str, cau_hinh: dict) -> bool:
    """Chuỗi model trả về có trông như MỘT GIÁ TRỊ, hay là cả một câu?

    Lần chạy thật đầu tiên (2026-09-04) cho thấy model hay trả nguyên một ô bảng hoặc
    cả câu vào `gia_tri_nguyen_van`, ví dụ *"Tài nguyên CPU/RAM của 1 node database …
    | 48 | 500 |"*. `parse_number` bắt được số ĐẦU TIÊN trong đó — ra `1` từ "1 node" —
    và đưa cho C4 một con số hoàn toàn bịa mà không cờ nào bật lên.
    """
    r = (raw or "").strip()
    if not r or len(r) > int(cau_hinh.get("dai_toi_da", 30)):
        return False
    vt = next((i for i, c in enumerate(r) if c.isdigit()), -1)
    return 0 <= vt <= int(cau_hinh.get("chu_so_dau_toi_da", 6))


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
    khong_phai_gia_tri: int = 0     # model trả cả một CÂU thay vì một giá trị
    ngoai_khoang_hop_le: int = 0    # 500% cho một trường đơn vị `%`
    gia_tri_khong_co_trong_cau: int = 0
    cot_khong_co_that: int = 0      # model khai tiêu đề cột không tồn tại
    gia_tri_khong_trong_cot: int = 0  # giá trị không nằm trong cột model khai
    o_bi_nhieu_tham_so: int = 0     # cùng một ô được nhiều tham số nhận làm nguồn
    lay_tu_bang: int = 0            # lấy được đúng ô bảng — ca đáng tin nhất
    # --- đường CỘT (v6) ---
    bang_hoi: int = 0               # số bảng đã đưa ra hỏi
    cot_hoi: int = 0                # tổng số cột dữ liệu đã hỏi — TRẦN của số giá trị
    cot_gan_duoc: int = 0           # cột được gán cho một tham số
    cot_khong_ro: int = 0           # model tự nhận không cột nào ứng tham số nào
    cot_trung_tham_so: int = 0      # ≥2 cột cùng bảng nhận cùng tham số ⇒ bỏ cả
    bang_mat_dong: int = 0          # nhãn dòng model trả về không có trong bảng
    mau_thuan_giua_bang: int = 0    # cùng tham số, hai bảng cho hai giá trị khác nhau
    loi: list[str] = field(default_factory=list)

    def tom_tat(self) -> str:
        return (f"{self.luot_goi} lượt gọi ({self.luot_goi_hong} hỏng) · "
                f"{self.truong_co_gia_tri}/{self.truong_hoi} trường có giá trị · "
                f"{self.bang_hoi} bảng · {self.cot_gan_duoc}/{self.cot_hoi} cột gán được · "
                f"{self.cot_khong_ro} cột khong_ro · "
                f"{self.cot_trung_tham_so} cột trùng tham số · "
                f"{self.bang_mat_dong} mất dòng · "
                f"{self.mau_thuan_giua_bang} mâu thuẫn giữa bảng · "
                f"{self.khong_neo_duoc} không neo được · "
                f"{self.khong_doc_duoc_so} không đọc được số · "
                f"{self.khong_quy_doi_duoc} không quy đổi được · "
                f"{self.luong_nghia} lưỡng nghĩa · "
                f"{self.khong_phai_gia_tri} không phải giá trị · "
                f"{self.ngoai_khoang_hop_le} ngoài khoảng hợp lệ · "
                f"{self.gia_tri_khong_co_trong_cau} giá trị không có trong câu · "
                f"{self.lay_tu_bang} lấy từ ô bảng · "
                f"{self.o_bi_nhieu_tham_so} bỏ vì một ô bị nhiều tham số nhận · "
                f"{self.cot_khong_co_that} cột không có thật · "
                f"{self.gia_tri_khong_trong_cot} giá trị không nằm trong cột khai")


class Extractor:
    def __init__(self, client: LLMClient | None = None, *, rules: RuleSet | None = None,
                 units: Units | None = None, model: str | None = None,
                 on_tien_do: Callable[[int, int, str], None] | None = None,
                 song_song: int = 1):
        self.client = client or LLMClient()
        self.rules = rules
        self.units = units or load_units()
        self.model = model
        # Không có tiến trình thì một lượt chạy 31–95 lời gọi × ~5s trông y hệt TREO.
        # Đã làm người dùng tưởng script chết (2026-09-04).
        self.on_tien_do = on_tien_do
        # Chi phí thật đo được: ~40s mỗi lượt gọi, và token ĐẦU RA chi phối (18 trường
        # × 2 chuỗi mỗi lượt), nên cắt ngữ cảnh không cứu được thời gian. Một bản 13
        # phân hệ tốn hàng trăm lượt ⇒ chạy tuần tự là hàng giờ. Rate limit đo ở 0.10
        # rất thoáng (0/10 lần 429) nên gọi song song được; mặc định giữ thấp vì 0.10
        # chỉ đo TUẦN TỰ, chưa đo đồng thời.
        self.song_song = max(1, int(song_song))
        self._khoa = threading.Lock()
        self.tk = ThongKe()

    def _bao(self, tong: int, nhan: str) -> None:
        if self.on_tien_do:
            self.on_tien_do(self.tk.luot_goi, tong, nhan)

    # -------------------------------------------------------------- ngữ cảnh
    def _ve_phan_tu(self, e: Element) -> str:
        """Bảng vẽ lại thành LƯỚI, giữ hàng tiêu đề.

        C1 giữ `rows` cho cả 21/21 bảng của BCCS3, nhưng C3 trước đây chỉ gửi `e.text`
        đã làm phẳng — tức vứt đúng thứ cho biết con số nào là gì. Bảng Database ghi rõ
        `CPU (Cint) | RAM (GB)`; mất cấu trúc đó thì `48` và `500` thành hai con số
        trần, và model gán chúng cho bất kỳ tham số nào được hỏi.
        """
        if e.kind == "table" and e.rows:
            dong = [" | ".join(o or "" for o in h) for h in e.rows]
            return (f"[BẢNG #{e.index} · {e.location}]\n"
                    + "\n".join(f"  | {d} |" for d in dong))
        return f"[{e.location}] {e.text}"

    def ngu_canh(self, doc: DocxDocument, section: str = "",
                 khoang: tuple[int, int] | None = None) -> str:
        els = doc.by_section(section) if section else doc.elements
        if khoang:
            els = [e for e in els if khoang[0] <= e.index < khoang[1]]
        dong = [self._ve_phan_tu(e) for e in els if e.text or e.rows]
        return "\n".join(dong)[:MAX_KY_TU_NGU_CANH]

    def khoang_phan_he(self, core: SizingCore, ph: SizingExtension,
                       het: int) -> tuple[int, int] | None:
        """Khoảng phần tử thuộc về một phân hệ: từ chỗ nó được nhắc tới đến phân hệ kế.

        Cắt theo `section` không đủ — ở BCCS3 cả 13 phân hệ nằm trong mục III, nên
        `Firewall` vẫn nhìn thấy bảng của `Database` và lấy nhầm số của nó.
        """
        if ph.element_index is None:
            return None
        sau = sorted(x.element_index for x in core.phan_he
                     if x.element_index is not None and x.element_index > ph.element_index)
        return (ph.element_index, sau[0] if sau else het)

    # ------------------------------------------------------------------ neo
    def neo(self, doc: DocxDocument, *khoa: str,
            khoang: tuple[int, int] | None = None) -> tuple[Element | None, str]:
        """Tìm lại đoạn model trích trong tài liệu. (phần tử, cách neo)."""
        el, i = _neo_doc(doc, *khoa, khoang=khoang)
        if i < 0:
            return None, ""
        return el, ("câu", "giá trị")[i] if i < 2 else "khoá phụ"

    def o_trong_cot(self, doc: DocxDocument, tieu_de: str, raw: str,
                    khoang: tuple[int, int] | None = None
                    ) -> tuple[Element | None, str]:
        """Tìm bảng có cột `tieu_de` và chứa `raw` trong đúng cột đó.

        Trả `(phần tử bảng, lý do hỏng)`. Đây là đường tin cậy nhất: model chỉ NÓI
        con số nằm ở cột nào, còn code tự đọc ô — nên model không đặt được một con số
        vào một cột nó không thuộc về.
        """
        td, gt = _chuan(tieu_de), _chuan(raw)
        thay_cot = False
        for e in doc.elements:
            if e.kind != "table" or not e.rows or len(e.rows) < 2:
                continue
            if khoang and not (khoang[0] <= e.index < khoang[1]):
                continue
            dau = [_chuan(o or "") for o in e.rows[0]]
            cot = next((i for i, h in enumerate(dau) if h and (h == td or td in h)), None)
            if cot is None:
                continue
            thay_cot = True
            for hang in e.rows[1:]:
                if cot < len(hang) and gt and gt in _chuan(hang[cot] or ""):
                    return e, ""
        return None, ("giá trị không nằm trong cột đã khai" if thay_cot
                      else "không bảng nào có cột đó")

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
        khoang = self.units.khoang_hop_le(t.unit) if t.unit else None
        if khoang and not (khoang[0] <= float(ev.value) <= khoang[1]):
            # 500 cho một trường đơn vị `%`. Con số đó CÓ THẬT trong tài liệu nên cổng
            # neo không chặn được — nó chỉ thuộc về trường khác.
            self.tk.ngoai_khoang_hop_le += 1
            ev.value = None
            ev.note = (f"{pn.value:g} nằm ngoài khoảng hợp lệ "
                       f"[{khoang[0]:g}, {khoang[1]:g}] của đơn vị {t.unit}")
            return ev

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

    def dung_gia_tri(self, doc: DocxDocument, t: ThamSo, o: BaseModel,
                     khoang: tuple[int, int] | None = None) -> ExtractedValue | None:
        """Một trường model trả về → `ExtractedValue`, hoặc None nếu không dùng được."""
        cau = getattr(o, "cau_chua", "") or ""
        tho = getattr(o, "gia_tri_nguyen_van", None)
        gia_tri_enum = getattr(o, "gia_tri", None)
        raw = tho if tho is not None else (gia_tri_enum or "")

        if not raw or raw.startswith(KHONG_NEU[:4]):
            # `khong_neu` và cả biến thể gõ sai (`kho_neu`) — model tự nghĩ ra cách nói
            # "không có" cho trường số, dù lược đồ chỉ cho phép chuỗi rỗng.
            return None                       # tài liệu không nêu -> để C4 báo thiếu

        if t.kieu == "so" and not _co_ve_la_gia_tri(raw, self.units.chuoi_gia_tri):
            self.tk.khong_phai_gia_tri += 1
            return None

        # Đường BẢNG đi trước: số liệu trong hồ sơ thật nằm trong bảng (BCCS3 có 21
        # bảng), và ở đó ta kiểm được con số có đúng cột hay không.
        cot = (getattr(o, "tieu_de_cot", "") or "").strip()
        if t.kieu == "so" and cot:
            el, vi_sao = self.o_trong_cot(doc, cot, raw, khoang)
            if el is None:
                if vi_sao.startswith("không bảng"):
                    self.tk.cot_khong_co_that += 1
                else:
                    self.tk.gia_tri_khong_trong_cot += 1
                return None
            self.tk.lay_tu_bang += 1
            ev = ExtractedValue(raw=raw, location=el.location, element_index=el.index,
                                confidence="cao",
                                # Cột nguồn hiện trong báo cáo để người đọc tự thấy khi
                                # con số đúng thật nhưng trả lời NHẦM câu hỏi — loại lỗi
                                # mà không cổng tự động nào phân biệt được.
                                note=f"lấy từ cột «{cot}» của bảng #{el.index}")
            return self._so(t, raw, ev)

        el, cach = self.neo(doc, cau, raw, khoang=khoang)
        if el is None:
            # Không tìm lại được trong tài liệu ⇒ không có căn cứ (NT2). Bỏ.
            self.tk.khong_neo_duoc += 1
            return None

        # Neo được CÂU thôi thì chưa đủ. Lần chạy thật cho thấy model ghép một câu có
        # thật của phân hệ này với một con số lấy từ bảng của phân hệ KHÁC — ví dụ
        # Firewall nhận `kich_thuoc_ban_ghi_byte = 500` neo vào bảng Database. Giá trị
        # phải có mặt ngay trong phần tử đã neo.
        if t.kieu == "so" and _chuan(raw) not in _chuan(el.text):
            el2, _ = _neo_doc(doc, raw, khoang=khoang)
            if el2 is None:
                self.tk.gia_tri_khong_co_trong_cau += 1
                return None
            el, cach = el2, "giá trị"

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

    # ------------------------------------------------------- đường CỘT (v6) --
    def trich_bang(self, doc: DocxDocument, e: Element,
                   dich: SizingCore | SizingExtension, ung_vien: list[ThamSo],
                   khoang: tuple[int, int] | None = None) -> None:
        """Hỏi MỘT BẢNG: mỗi cột dữ liệu ứng với tham số nào?

        Lược đồ có đúng một trường cho mỗi cột, nên số giá trị sinh ra bị chặn cứng bởi
        số cột — lý do đầy đủ ở `bang.py`. Model chỉ CHỌN TÊN; code định vị ô và đọc.
        """
        cot = cot_du_lieu(e)
        if not cot or not ung_vien:
            return
        du_lieu = e.rows[1:]
        nhan = nhan_dong(e)
        chon_dong = len(du_lieu) > 1
        lop = luoc_do_bang(e, cot, ung_vien, chon_dong)
        with self._khoa:
            self.tk.luot_goi += 1
            self.tk.bang_hoi += 1
            self.tk.cot_hoi += len(cot)
            self.tk.truong_hoi += len(cot)

        # Gửi kèm vùng văn bản quanh bảng: bảng `N | CPU | RAM | Storage` có dòng tổng
        # và dòng cho MỘT node, phân biệt được hai dòng đó chỉ nhờ câu chữ bên cạnh.
        quanh = self.ngu_canh(doc, khoang=khoang) if khoang else self._ve_phan_tu(e)
        try:
            kq = self.client.extract(lop, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    f"Dưới đây là một phần tài liệu định cỡ. Hãy đọc BẢNG #{e.index} và "
                    f"cho biết mỗi CỘT của nó chứa tham số nào.\n"
                    f"{NHAC_NHO_BANG}\n\n=== CÁC THAM SỐ CÓ THỂ CHỌN ===\n"
                    f"{chu_giai(ung_vien)}\n\n=== TÀI LIỆU ===\n{quanh}\n\n"
                    f"=== BẢNG #{e.index} CẦN PHÂN TÍCH ===\n{self._ve_phan_tu(e)}"},
            ], model=self.model,
                max_tokens=min(TOKEN_TOI_DA, TOKEN_NEN + TOKEN_MOI_TRUONG * len(cot)))
        except (ExtractionFailed, LLMError) as ex:
            with self._khoa:
                self.tk.luot_goi_hong += 1
                self.tk.loi.append(f"bảng #{e.index}: {ex}")
            return

        with self._khoa:
            k = self._chon_dong(kq, nhan, len(du_lieu), chon_dong)
            if k is None:
                self.tk.bang_mat_dong += 1
                return
            hang = du_lieu[k]
            nl = (hang[0] if hang else "").strip()
            theo_ten: dict[str, list[tuple[int, str]]] = {}
            for i, td in cot:
                ten = getattr(kq, f"cot_{i}", KHONG_RO)
                if ten == KHONG_RO:
                    self.tk.cot_khong_ro += 1
                    continue
                theo_ten.setdefault(ten, []).append((i, td))

            uv = {t.name: t for t in ung_vien}
            for ten, ds in theo_ten.items():
                if len(ds) > 1:
                    # Hai cột khác nhau không thể cùng là một tham số. Không có căn cứ
                    # chọn cột nào ⇒ bỏ cả — cùng nguyên tắc với cổng một-ô-một-tham-số.
                    self.tk.cot_trung_tham_so += len(ds)
                    continue
                self.tk.cot_gan_duoc += 1
                i, td = ds[0]
                raw = (hang[i] if i < len(hang) else "").strip()
                if not raw:
                    continue
                vt = f"bảng #{e.index}, cột «{td}»" + (f", dòng «{nl}»" if nl else "")
                ev = self._so(uv[ten], raw, ExtractedValue(
                    raw=raw, location=e.location, element_index=e.index,
                    o_nguon=f"r{k}c{i}",
                    confidence="cao", note=f"lấy từ {vt}"))
                self._ghi_nhan(dich, ten, ev, vt)

    @staticmethod
    def _chon_dong(kq: BaseModel, nhan: list[str], so_dong: int,
                   chon_dong: bool) -> int | None:
        """Chỉ số dòng model chỉ tới; None nếu nhãn nó trả về không có trong bảng.

        Trả CHỈ SỐ chứ không trả chính dòng đó: hai dòng có thể trùng nội dung, và toạ
        độ ô (`o_nguon`) phải là toạ độ thật thì cổng một-ô-một-tham-số mới so đúng.
        """
        if not so_dong:
            return None
        if not chon_dong:
            return 0
        d = _chuan(getattr(kq, "dong", "") or "")
        if not d:
            return None
        for k, n in enumerate(nhan[:so_dong]):
            if _chuan(n) == d:
                return k
        for k, n in enumerate(nhan[:so_dong]):
            if n and (_chuan(n) in d or d in _chuan(n)):
                return k
        return None

    def _ghi_nhan(self, dich: SizingCore | SizingExtension, ten: str,
                  ev: ExtractedValue, vt: str) -> None:
        """Ghi một giá trị, xử lý ca hai bảng cùng khai một tham số."""
        cu = dich.params.get(ten)
        if cu is None or cu.value is None:
            dich.params[ten] = ev
            if ev.value is not None:
                self.tk.truong_co_gia_tri += 1
            return
        if ev.value is None:
            return                             # giá trị cũ tốt hơn, giữ nguyên
        if cu.value == ev.value:
            cu.note = "; ".join(x for x in (cu.note, f"xác nhận lại ở {vt}") if x)
            return
        # Hai bảng, hai con số, cùng một tham số. Không có căn cứ chọn ⇒ bỏ cả hai (NT4).
        self.tk.mau_thuan_giua_bang += 1
        self.tk.truong_co_gia_tri -= 1
        cu.value, cu.confidence = None, "thap"
        cu.note = "; ".join(x for x in (cu.note, (
            f"BỎ: {vt} cho giá trị khác ({ev.raw}) cho cùng tham số")) if x)

    # ------------------------------------------- một ô, một tham số ---------
    def loc_o_bi_nhieu_tham_so(self, dich: SizingCore | SizingExtension) -> int:
        """Cùng một ô bảng mà nhiều tham số cùng nhận làm nguồn ⇒ BỎ HẾT.

        Đo trên lượt chạy thật 2026-09-04 18:51: **44/72 giá trị (61%)** đến từ một ô
        mà tham số khác cũng nhận. Kỷ lục là ô `#93 = 16` của DBIN/FTP được **9 tham
        số** cùng nhận, và cột «RAM (GB)» một mình cấp cho 6 tham số khác nhau.

        Đây là chữ ký của việc ĐIỀN BỪA: lược đồ hỏi 8–12 tham số, mà bảng phân hệ chỉ
        có 2–3 con số, nên model rải con số đang có ra khắp các trường được hỏi.

        Bỏ HẾT chứ không giữ lại một cái: khi 9 tham số cùng trỏ vào một ô, ta không có
        căn cứ nào để chọn cái đúng — giữ lại là đoán. Ưu tiên độ chính xác hơn độ phủ.
        """
        theo_o: dict[tuple, list[str]] = {}
        for ten, ev in dich.params.items():
            if ev.value is None or ev.element_index is None or not ev.raw:
                continue
            khoa = ev.o_nguon or _chuan(ev.raw)
            theo_o.setdefault((ev.element_index, khoa), []).append(ten)

        bo = 0
        for _, ds in theo_o.items():
            if len(ds) < 2:
                continue
            for ten in ds:
                ev = dich.params[ten]
                ev.value = None
                ev.confidence = "thap"
                ev.note = "; ".join(x for x in (ev.note, (
                    f"BỎ: ô này còn được {len(ds) - 1} tham số khác nhận làm nguồn "
                    f"({', '.join(t for t in ds if t != ten)}) — không có căn cứ để "
                    f"chọn tham số nào đúng")) if x)
                bo += 1
        return bo

    # ------------------------------------------------------------ một nhóm --
    def trich_nhom(self, doc: DocxDocument, nhom: NhomTrich, dich: SizingCore | SizingExtension,
                   *, section: str = "", ten_phan_he: str = "",
                   khoang: tuple[int, int] | None = None) -> None:
        lop = luoc_do_nhom(nhom)
        with self._khoa:
            self.tk.luot_goi += 1
            self.tk.truong_hoi += len(nhom.tham_so)
        pham_vi = f" của phân hệ «{ten_phan_he}»" if ten_phan_he else " ở cấp toàn hệ thống"
        # Ngữ cảnh HẸP theo mục của phân hệ. Vừa rẻ vừa chính xác hơn: hỏi về phân hệ
        # Database mà đưa cả 13 phân hệ vào ngữ cảnh là mời model lấy nhầm số của phân
        # hệ khác. Mục quá hẹp (tài liệu viết rải, hoặc C1 không nhận ra số mục) thì lùi
        # về toàn tài liệu — thà chậm còn hơn trích thiếu.
        nc = self.ngu_canh(doc, section, khoang)
        if (section or khoang) and len(nc) < MIN_KY_TU_NGU_CANH_HEP:
            nc = self.ngu_canh(doc)
        try:
            kq = self.client.extract(lop, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    f"Trích các thông tin sau{pham_vi} từ tài liệu định cỡ dưới đây.\n"
                    f"{NHAC_NHO}\n\n=== TÀI LIỆU ===\n{nc}"},
            ], model=self.model,
                max_tokens=min(TOKEN_TOI_DA,
                               TOKEN_NEN + TOKEN_MOI_TRUONG * len(nhom.tham_so)))
        except (ExtractionFailed, LLMError) as e:
            # Hết lượt thử vẫn không ra JSON hợp lệ: KHÔNG bịa giá trị (NT4).
            # Để trống, C4 sẽ sinh finding "thiếu thông tin" cho từng tham số.
            with self._khoa:
                self.tk.luot_goi_hong += 1
                self.tk.loi.append(f"{nhom.ten}: {e}")
            return

        # Phần dưới chỉ tính toán, không gọi mạng — giữ khoá suốt cho gọn và an toàn
        # khi chạy song song.
        with self._khoa:
            for t in nhom.tham_so:
                ev = self.dung_gia_tri(doc, t, getattr(kq, t.name), khoang)
                if ev is None:
                    continue
                dich.params[t.name] = ev       # giữ cả note để báo cáo nói được vì sao
                if ev.value is not None:
                    self.tk.truong_co_gia_tri += 1

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
            # Neo theo SỐ HIỆU BẢNG trước, tên sau. Lượt 18:51 mất neo 3/10 phân hệ vì
            # model trả tên mô tả dài (*"Các module vệ tinh, monitor (Birt report, VSA,
            # Oracle GoldenGate MONyog, MariaDB)"*) không có nguyên văn trong tài liệu.
            # Mất neo nghĩa là mất luôn giới hạn khoảng, và phân hệ đó đi lấy số của
            # chỗ khác — đúng thứ khoảng phân hệ sinh ra để chặn.
            el = None
            bang = int(getattr(p, "bang_cau_hinh", 0) or 0)
            if bang:
                el = next((e for e in doc.elements
                           if e.index == bang and e.kind == "table"), None)
            if el is None:
                el, _ = self.neo(doc, p.ten_phan_he, p.cong_nghe or "", p.muc)
            clt = p.cong_nghe_luu_tru.strip()
            if clt == KHONG_NEU:
                clt = ""
            ra.append(SizingExtension(
                ten_phan_he=p.ten_phan_he.strip(),
                cong_nghe=p.cong_nghe.strip() or None,
                cong_nghe_luu_tru=clt or None,
                location=el.location if el else "",
                muc=el.section if el else "",
                element_index=el.index if el else None))
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
        # Tài liệu có bảng số liệu thì tham số KIỂU SỐ đi đường cột (v6, xem `bang.py`);
        # đường hỏi-theo-tham-số chỉ còn lo enum/bool. Tài liệu KHÔNG có bảng nào dùng
        # được thì lùi về cách cũ cho cả ba kiểu — thà kém chính xác còn hơn không trích
        # được gì (NT4).
        co_bang = any(cot_du_lieu(e) for e in doc.elements if e.kind == "table")
        kieu = {"bool", "enum"} if co_bang else None
        nhom_ht = ke_hoach_trich(self.rules, scope="he_thong", chi_nhom=chi_nhom, kieu=kieu)
        nhom_ph = ke_hoach_trich(self.rules, scope="phan_he", chi_nhom=chi_nhom, kieu=kieu)
        nhom_cn = ke_hoach_trich(self.rules, scope="phan_he_x_cong_nghe_luu_tru",
                                 chi_nhom=chi_nhom, kieu=kieu)
        tong = 2 + len(nhom_ht)          # chưa biết số phân hệ, cập nhật sau khi dò

        core = SizingCore()
        self._bao(tong, "thông tin chung")
        self.trich_cap_tai_lieu(doc, core)
        self._bao(tong, "nhận diện phân hệ")
        core.phan_he = self.nhan_dien_phan_he(doc)

        tong += sum(len(nhom_ph) + (len(nhom_cn) if ph.cong_nghe_luu_tru else 0)
                    for ph in core.phan_he)
        het = (max(e.index for e in doc.elements) + 1) if doc.elements else 0

        # `viec` là danh sách (nhãn, việc-không-tham-số). Trước đây là tuple vị trí và
        # đã một lần bị thêm phần tử vào giữa mà quên sửa chỗ giải nén.
        viec: list[tuple[str, Callable[[], None]]] = [
            (nhom.ten, partial(self.trich_nhom, doc, nhom, core)) for nhom in nhom_ht]
        for ph in core.phan_he:
            kh = self.khoang_phan_he(core, ph, het)
            for sc, ds in (("phan_he", nhom_ph), ("phan_he_x_cong_nghe_luu_tru", nhom_cn)):
                if sc == "phan_he_x_cong_nghe_luu_tru" and not ph.cong_nghe_luu_tru:
                    continue
                viec += [(f"{ph.ten_phan_he}/{nhom.ten}",
                          partial(self.trich_nhom, doc, nhom, ph, section=ph.muc,
                                  ten_phan_he=ph.ten_phan_he, khoang=kh))
                         for nhom in ds]

        if co_bang:
            uv_ht = tham_so_so(self.rules, scope="he_thong", chi_nhom=chi_nhom)
            uv_ph = tham_so_so(self.rules, scope="phan_he", chi_nhom=chi_nhom)
            uv_cn = tham_so_so(self.rules, scope="phan_he_x_cong_nghe_luu_tru",
                               chi_nhom=chi_nhom)
            for e, ph, kh in phan_vung_bang(doc, core):
                if not cot_du_lieu(e):
                    continue
                uv = uv_ht if ph is None else (
                    uv_ph + (uv_cn if ph.cong_nghe_luu_tru else []))
                nhan = f"bảng #{e.index}" + (f" · {ph.ten_phan_he}" if ph else "")
                viec.append((nhan, partial(self.trich_bang, doc, e,
                                           ph if ph is not None else core, uv, kh)))
            tong = len(viec) + 2

        self._chay(viec, tong)

        # Chạy SAU khi mọi nhóm đã xong: một ô có thể bị nhiều nhóm khác nhau cùng
        # nhận, nên không kiểm được trong phạm vi một lượt gọi.
        for dich in [core, *core.phan_he]:
            n = self.loc_o_bi_nhieu_tham_so(dich)
            with self._khoa:
                self.tk.o_bi_nhieu_tham_so += n
                self.tk.truong_co_gia_tri -= n
        return core

    def _chay(self, viec: list[tuple[str, Callable[[], None]]], tong: int) -> None:
        if self.song_song <= 1:
            for nhan, lam in viec:
                self._bao(tong, nhan)
                lam()
            return
        with ThreadPoolExecutor(max_workers=self.song_song) as pool:
            fut = {pool.submit(lam): nhan for nhan, lam in viec}
            for f in as_completed(fut):
                self._bao(tong, fut[f])
                f.result()                     # lỗi lạ phải nổ ra, không nuốt


def so_bang_dung_duoc(doc: DocxDocument) -> int:
    """Số bảng có ít nhất một cột số liệu — số lượt gọi của đường cột (v6)."""
    return sum(1 for e in doc.elements if e.kind == "table" and cot_du_lieu(e))


def uoc_tinh_luot_goi(rules: RuleSet | None = None, *, chi_nhom: list[str] | None = None,
                      so_phan_he: int = 3, co_luu_tru: bool = True,
                      so_bang: int = 0) -> dict:
    """Ước lượng số lời gọi TRƯỚC khi chạy — để không ai bấm rồi ngồi chờ mù.

    `so_bang > 0` nghĩa là tài liệu đi đường cột: mỗi bảng một lượt, và đường hỏi-theo-
    tham-số thu về còn enum/bool. Đó là lý do v6 rẻ hơn hẳn v5 (BCCS3: 20 bảng thay cho
    ~80 lượt hỏi tham số số học).
    """
    kieu = {"bool", "enum"} if so_bang else None
    ht = len(ke_hoach_trich(rules, scope="he_thong", chi_nhom=chi_nhom, kieu=kieu))
    ph = len(ke_hoach_trich(rules, scope="phan_he", chi_nhom=chi_nhom, kieu=kieu))
    cn = len(ke_hoach_trich(rules, scope="phan_he_x_cong_nghe_luu_tru",
                            chi_nhom=chi_nhom, kieu=kieu))
    tong = 2 + ht + so_phan_he * (ph + (cn if co_luu_tru else 0)) + so_bang
    return {"he_thong": ht, "moi_phan_he": ph + (cn if co_luu_tru else 0),
            "so_phan_he_gia_dinh": so_phan_he, "bang": so_bang, "tong": tong}


# ------------------------------------------------------------- lược đồ cố định
def _lop_phan_he() -> type[BaseModel]:
    """Lược đồ nhận diện phân hệ, với `cong_nghe_luu_tru` là **Literal**.

    Khai `str` cho trường này đã hỏng đúng hai lần trên tài liệu thật: lần đầu model
    chép nguyên `cong_nghe` sang ("MariaDB Database" làm công nghệ *lưu trữ*), lần sau
    nó điền cả tiêu đề mục ("Mục III - Định cỡ cụm máy chủ cho Database"). Cả hai lần
    giá trị đều khác rỗng, nên **mọi phân hệ đều chạy thêm một vòng scope
    `phan_he_x_cong_nghe_luu_tru`** trên một trường vô nghĩa.

    Đây đúng bài học 1.2 lặp lại: liệt kê giá trị trong `description` là không đủ.
    Danh sách lấy từ tham số `loai_o` trong `rules.yaml` (NT3), không tự nghĩ.
    """
    loai_o = tham_so_cua_bo_quy_tac().get("loai_o")
    opts = tuple(loai_o.options if loai_o else ()) + (KHONG_NEU,)
    return create_model(
        "PhanHeNhanDien",
        ten_phan_he=(str, Field(description="Tên phân hệ đúng như tài liệu gọi")),
        cong_nghe=(str, Field(
            description="MariaDB / Redis / Kafka / K8s… Rỗng nếu không nêu")),
        cong_nghe_luu_tru=(Literal[opts],  # type: ignore[valid-type]
                           Field(description=(
                               "Loại ổ lưu trữ của phân hệ, chọn đúng một trong: "
                               + ", ".join(o for o in opts if o != KHONG_NEU)
                               + f". Chọn {KHONG_NEU} nếu tài liệu không nêu — "
                                 "KHÔNG chép tên công nghệ hay tiêu đề mục vào đây."))),
        muc=(str, Field(
            description="Số mục chứa phân hệ, ví dụ 'IV.2'. Rỗng nếu không có")),
        bang_cau_hinh=(int, Field(
            default=0,
            description="Số hiệu bảng chứa cấu hình của phân hệ này — lấy đúng con số "
                        "sau dấu # trong '[BẢNG #N]'. Để 0 nếu phân hệ không có bảng "
                        "riêng.")),
    )


PhanHeNhanDien = _lop_phan_he()


class DanhSachPhanHe(BaseModel):
    phan_he: list[PhanHeNhanDien]      # type: ignore[valid-type]


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
    "khớp tài liệu sẽ bị loại.\n"
    "- Số liệu thường nằm trong BẢNG, được vẽ dưới dạng lưới kèm hàng tiêu đề. Khi lấy "
    "từ bảng, PHẢI ghi `tieu_de_cot` đúng nguyên văn tiêu đề cột. Giá trị không nằm "
    "trong cột đó sẽ bị loại.\n"
    "- Tiêu đề cột cho biết con số LÀ GÌ. Cột 'CPU (Cint)' là năng lực CPU tính bằng "
    "Cint, KHÔNG phải phần trăm tải CPU. Không có cột nào đúng nghĩa tham số đang hỏi "
    "thì để trống — phần lớn tham số sẽ để trống, đó là điều bình thường."
)

NHAC_NHO_BANG = (
    "Cách làm:\n"
    "- Với MỖI cột, chọn tên tham số mà cột đó chứa, dựa vào TIÊU ĐỀ cột và nghĩa của "
    "tham số trong danh sách bên dưới.\n"
    f"- Tiêu đề cột phải ĐÚNG NGHĨA tham số, không chỉ liên quan: cột 'CPU (Cint)' là "
    f"năng lực CPU đo bằng Cint, KHÔNG phải phần trăm tải CPU cũng KHÔNG phải số nhân. "
    f"Không chắc thì chọn {KHONG_RO} — chọn sai tệ hơn nhiều so với bỏ trống.\n"
    f"- Cột số thứ tự (STT) và cột đánh số dòng luôn là {KHONG_RO}.\n"
    "- Mỗi tham số chỉ được gán cho NHIỀU NHẤT MỘT cột. Hai cột khác nhau thì là hai "
    "tham số khác nhau.\n"
    "- KHÔNG đọc giá trị, KHÔNG tính toán. Chỉ nói cột nào là tham số nào."
)
