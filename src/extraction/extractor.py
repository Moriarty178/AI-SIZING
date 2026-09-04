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
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, create_model

from ..ingestion.anchor import chuan_hoa as _chuan
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
# Dưới ngưỡng này thì mục quá hẹp để tin — lùi về toàn tài liệu.
MIN_KY_TU_NGU_CANH_HEP = 400


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
    loi: list[str] = field(default_factory=list)

    def tom_tat(self) -> str:
        return (f"{self.luot_goi} lượt gọi ({self.luot_goi_hong} hỏng) · "
                f"{self.truong_co_gia_tri}/{self.truong_hoi} trường có giá trị · "
                f"{self.khong_neo_duoc} không neo được · "
                f"{self.khong_doc_duoc_so} không đọc được số · "
                f"{self.khong_quy_doi_duoc} không quy đổi được · "
                f"{self.luong_nghia} lưỡng nghĩa · "
                f"{self.khong_phai_gia_tri} không phải giá trị · "
                f"{self.ngoai_khoang_hop_le} ngoài khoảng hợp lệ · "
                f"{self.gia_tri_khong_co_trong_cau} giá trị không có trong câu")


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

    def dung_gia_tri(self, doc: DocxDocument, t: ThamSo, o: BaseModel
                     ) -> ExtractedValue | None:
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

        el, cach = self.neo(doc, cau, raw)
        if el is None:
            # Không tìm lại được trong tài liệu ⇒ không có căn cứ (NT2). Bỏ.
            self.tk.khong_neo_duoc += 1
            return None

        # Neo được CÂU thôi thì chưa đủ. Lần chạy thật cho thấy model ghép một câu có
        # thật của phân hệ này với một con số lấy từ bảng của phân hệ KHÁC — ví dụ
        # Firewall nhận `kich_thuoc_ban_ghi_byte = 500` neo vào bảng Database. Giá trị
        # phải có mặt ngay trong phần tử đã neo.
        if t.kieu == "so" and _chuan(raw) not in _chuan(el.text):
            el2, _ = _neo_doc(doc, raw)
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

    # ------------------------------------------------------------ một nhóm --
    def trich_nhom(self, doc: DocxDocument, nhom: NhomTrich, dich: SizingCore | SizingExtension,
                   *, section: str = "", ten_phan_he: str = "") -> None:
        lop = luoc_do_nhom(nhom)
        with self._khoa:
            self.tk.luot_goi += 1
            self.tk.truong_hoi += len(nhom.tham_so)
        pham_vi = f" của phân hệ «{ten_phan_he}»" if ten_phan_he else " ở cấp toàn hệ thống"
        # Ngữ cảnh HẸP theo mục của phân hệ. Vừa rẻ vừa chính xác hơn: hỏi về phân hệ
        # Database mà đưa cả 13 phân hệ vào ngữ cảnh là mời model lấy nhầm số của phân
        # hệ khác. Mục quá hẹp (tài liệu viết rải, hoặc C1 không nhận ra số mục) thì lùi
        # về toàn tài liệu — thà chậm còn hơn trích thiếu.
        nc = self.ngu_canh(doc, section)
        if section and len(nc) < MIN_KY_TU_NGU_CANH_HEP:
            nc = self.ngu_canh(doc)
        try:
            kq = self.client.extract(lop, [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content":
                    f"Trích các thông tin sau{pham_vi} từ tài liệu định cỡ dưới đây.\n"
                    f"{NHAC_NHO}\n\n=== TÀI LIỆU ===\n{nc}"},
            ], model=self.model)
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
                ev = self.dung_gia_tri(doc, t, getattr(kq, t.name))
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
            el, _ = self.neo(doc, p.muc, p.ten_phan_he)
            # Model hay chép nguyên `cong_nghe` sang `cong_nghe_luu_tru` ("MariaDB
            # Database" làm công nghệ LƯU TRỮ). Hậu quả không chỉ là sai nhãn: mọi phân
            # hệ khi đó đều chạy thêm một vòng `phan_he_x_cong_nghe_luu_tru`, nhân đôi
            # chi phí cho một trường vô nghĩa.
            clt = p.cong_nghe_luu_tru.strip()
            if clt and clt.lower() == p.cong_nghe.strip().lower():
                clt = ""
            ra.append(SizingExtension(
                ten_phan_he=p.ten_phan_he.strip(),
                cong_nghe=p.cong_nghe.strip() or None,
                cong_nghe_luu_tru=clt or None,
                location=el.location if el else "",
                muc=el.section if el else ""))
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
        nhom_ht = ke_hoach_trich(self.rules, scope="he_thong", chi_nhom=chi_nhom)
        nhom_ph = ke_hoach_trich(self.rules, scope="phan_he", chi_nhom=chi_nhom)
        nhom_cn = ke_hoach_trich(self.rules, scope="phan_he_x_cong_nghe_luu_tru",
                                 chi_nhom=chi_nhom)
        tong = 2 + len(nhom_ht)          # chưa biết số phân hệ, cập nhật sau khi dò

        core = SizingCore()
        self._bao(tong, "thông tin chung")
        self.trich_cap_tai_lieu(doc, core)
        self._bao(tong, "nhận diện phân hệ")
        core.phan_he = self.nhan_dien_phan_he(doc)

        tong += sum(len(nhom_ph) + (len(nhom_cn) if ph.cong_nghe_luu_tru else 0)
                    for ph in core.phan_he)
        viec: list[tuple] = [(nhom, core, "", "", nhom.ten) for nhom in nhom_ht]
        for ph in core.phan_he:
            for sc, ds in (("phan_he", nhom_ph), ("phan_he_x_cong_nghe_luu_tru", nhom_cn)):
                if sc == "phan_he_x_cong_nghe_luu_tru" and not ph.cong_nghe_luu_tru:
                    continue
                viec += [(nhom, ph, ph.muc, ph.ten_phan_he,
                          f"{ph.ten_phan_he}/{nhom.ten}") for nhom in ds]

        self._chay(doc, viec, tong)
        return core

    def _chay(self, doc: DocxDocument, viec: list[tuple], tong: int) -> None:
        if self.song_song <= 1:
            for nhom, dich, muc, ten, nhan in viec:
                self._bao(tong, nhan)
                self.trich_nhom(doc, nhom, dich, section=muc, ten_phan_he=ten)
            return
        with ThreadPoolExecutor(max_workers=self.song_song) as pool:
            fut = {pool.submit(self.trich_nhom, doc, nhom, dich, section=muc,
                               ten_phan_he=ten): nhan
                   for nhom, dich, muc, ten, nhan in viec}
            for f in as_completed(fut):
                self._bao(tong, fut[f])
                f.result()                     # lỗi lạ phải nổ ra, không nuốt


def uoc_tinh_luot_goi(rules: RuleSet | None = None, *, chi_nhom: list[str] | None = None,
                      so_phan_he: int = 3, co_luu_tru: bool = True) -> dict:
    """Ước lượng số lời gọi TRƯỚC khi chạy — để không ai bấm rồi ngồi chờ mù."""
    ht = len(ke_hoach_trich(rules, scope="he_thong", chi_nhom=chi_nhom))
    ph = len(ke_hoach_trich(rules, scope="phan_he", chi_nhom=chi_nhom))
    cn = len(ke_hoach_trich(rules, scope="phan_he_x_cong_nghe_luu_tru", chi_nhom=chi_nhom))
    tong = 2 + ht + so_phan_he * (ph + (cn if co_luu_tru else 0))
    return {"he_thong": ht, "moi_phan_he": ph + (cn if co_luu_tru else 0),
            "so_phan_he_gia_dinh": so_phan_he, "tong": tong}


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
