"""C2 · 2.3 — đọc nội dung ảnh bằng model vision. Phần logic; chạy thật cần model.

## Mặc định chỉ đọc `so_do` + `console` (người dùng chốt 2026-09-05)

Gọi vision cho cả 776 ảnh tốn ~8,5 giờ ở ~40 giây/lượt. Hai loại mặc định chọn
theo đúng chỗ giá trị nằm, không theo cảm tính:

- **`console`** là lớp đông nhất (34,1% ảnh) và là nơi đặt **số đo tải làm sở cứ**
  — thứ PNX hay đòi nhất.
- **`so_do`** ít ảnh (7,7%) nhưng là căn cứ cho quy tắc **định tính Vòng 1**, mà
  phép đo 2026-09-04 đã chỉ ra recall nằm ở đó chứ không ở phần định lượng
  (367/475 nhãn không cần một con số nào).

`dashboard`, `anh_van_ban`, `chua_ro` bật bằng tham số `loai=` khi cần.

## Ba ranh giới NT không được vượt

- **NT1 — model KHÔNG tính, và cũng không ra số.** Nó trả về **nguyên văn dòng
  chữ nhìn thấy** trong ảnh; `parse_number` của 1.4 mới quyết định con số. Giống
  hệt quyết định đã chốt cho C3: *"1.500"* là 1500 hay 1,5 là quyết định dưới sự
  mơ hồ, để model chọn là đi vòng qua thang suy luận đã dựng.
- **NT2 — mỗi con số phải có trích dẫn NEO ĐƯỢC.** Không có văn bản gốc để đối
  chiếu như C3/C5, nên cổng ở đây là **tính nhất quán nội tại**: chuỗi giá trị
  model đưa ra phải nằm trong chính đoạn trích dẫn nó nói là đã nhìn thấy. Không
  thoả thì **bỏ giá trị đó** và đếm vào `trich_dan_bia`.
- **NT4 — không đọc được thì nói không đọc được.** Ảnh mờ, ảnh không phải loại
  đã nghĩ, model từ chối, lỗi gọi — tất cả ra một finding `khong_kiem_chung_duoc`
  có căn cứ đếm được, KHÔNG bịa nội dung và KHÔNG im lặng.

## Vì sao TẮT mặc định trong pipeline

Người dùng chốt 2026-09-05: lượt đo recall (B1) chạy **sạch trước**, không kèm
2.3. Trộn hai thay đổi vào một lượt chạy tốn tiền thì không quy được kết quả cho
cái nào. Nên `doc_anh=False` là mặc định của `pipeline.chay()`.
"""
from __future__ import annotations

import base64
import concurrent.futures as cf
import threading
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from ..ingestion.docx_reader import DocxDocument
from ..llm.client import ExtractionFailed, LLMClient, LLMError
from ..normalization.numbers import parse_number
from ..reporting.finding import Finding
from .anh import Anh
from .phan_loai import Loai, phan_loai, tom_tat_anh

# Người dùng chốt 2026-09-05. Đổi mặc định phải hỏi lại, không tự đổi.
LOAI_MAC_DINH: tuple[Loai, ...] = ("so_do", "console")

MAX_CANH = 1600             # thu nhỏ cạnh dài trước khi gửi, nếu có Pillow
MAX_BYTE = 1_500_000        # ảnh lớn hơn mức này mà không thu nhỏ được thì BỎ, có lý do
MIME = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg",
        "gif": "image/gif", "bmp": "image/bmp"}

HE_THONG = (
    "Bạn đọc ảnh chụp trong tài liệu định cỡ hệ thống CNTT. Nguyên tắc bắt buộc:\n"
    "1. CHỈ nói những gì NHÌN THẤY RÕ trong ảnh. Không suy đoán, không bổ sung "
    "kiến thức bên ngoài.\n"
    "2. KHÔNG tính toán. KHÔNG quy đổi đơn vị. Trả về nguyên văn chuỗi ký tự đọc "
    "được, kể cả dấu phân cách và đơn vị.\n"
    "3. Mỗi con số phải kèm đoạn trích NGUYÊN VĂN chứa nó, chép đúng như hiện trên "
    "ảnh.\n"
    "4. Ảnh mờ, bị che, hoặc không phải loại được hỏi thì đặt `doc_duoc=false` và "
    "nêu lý do. Đoán bừa là sai nặng hơn bỏ trống."
)

NHAC_CONSOLE = (
    "Ảnh này là ảnh chụp màn hình dòng lệnh (ví dụ `top`, `free`, `lscpu`, "
    "`kubectl top`, `df`). Hãy đọc các số liệu tài nguyên nhìn thấy được: CPU, "
    "RAM, dung lượng, số tiến trình, tải. Với MỖI số liệu, chép lại nguyên văn cả "
    "dòng chứa nó."
)
NHAC_SO_DO = (
    "Ảnh này là sơ đồ (kiến trúc, mô hình triển khai, hoặc topology mạng). Hãy "
    "liệt kê tên các thành phần nhìn thấy và các luồng nối giữa chúng. Chỉ chép "
    "nhãn có chữ thật trong ảnh."
)
NHAC_KHAC = (
    "Ảnh này là ảnh chụp bảng số liệu, biểu đồ giám sát hoặc văn bản. Hãy đọc các "
    "số liệu nhìn thấy rõ. Với đồ thị, CHỈ đọc con số ghi thành chữ (ô KPI, đồng "
    "hồ, nhãn trục); KHÔNG ước lượng giá trị bằng cách nhìn đường biểu diễn."
)


# ---------------------------------------------------------------------------
# Lược đồ — mỗi loại một câu hỏi, không gộp (một nhiệm vụ một lần gọi)
# ---------------------------------------------------------------------------
class SoLieuAnh(BaseModel):
    nhan: str = Field(description="Tên chỉ số, chép theo chữ trong ảnh")
    gia_tri_raw: str = Field(description="Chuỗi chứa con số, NGUYÊN VĂN như trong ảnh")
    don_vi: str = Field(default="", description="Đơn vị nếu ảnh có ghi, để trống nếu không")
    trich_dan: str = Field(description="Nguyên văn cả dòng chứa số liệu này")


class DocConsole(BaseModel):
    doc_duoc: bool
    ly_do_khong_doc_duoc: str = ""
    lenh: str = Field(default="", description="Lệnh nhìn thấy, để trống nếu không rõ")
    so_lieu: list[SoLieuAnh] = Field(default_factory=list)


class DocSoDo(BaseModel):
    doc_duoc: bool
    ly_do_khong_doc_duoc: str = ""
    thanh_phan: list[str] = Field(default_factory=list,
                                  description="Nhãn các khối nhìn thấy trong sơ đồ")
    luong: list[str] = Field(default_factory=list,
                             description="Các nối/mũi tên, dạng 'A -> B'")
    mo_ta: str = Field(default="", description="Một đến hai câu mô tả sơ đồ")


LUOC_DO: dict[str, type[BaseModel]] = {
    "so_do": DocSoDo, "console": DocConsole, "dashboard": DocConsole,
    "anh_van_ban": DocConsole, "chua_ro": DocConsole,
}
NHAC: dict[str, str] = {
    "so_do": NHAC_SO_DO, "console": NHAC_CONSOLE, "dashboard": NHAC_KHAC,
    "anh_van_ban": NHAC_KHAC, "chua_ro": NHAC_KHAC,
}


# ---------------------------------------------------------------------------
@dataclass
class SoDaDoc:
    """Một số liệu đã qua cổng NT2 và được CODE chuyển thành số (NT1)."""

    nhan: str
    raw: str
    gia_tri: float | None
    don_vi: str
    trich_dan: str
    luong_nghia: bool = False       # "1.500" đọc được hai cách — giữ cả hai (1.4)
    gia_tri_khac: float | None = None


@dataclass
class KetQuaDocAnh:
    ma_anh: str
    loai: Loai
    location: str = ""
    doc_duoc: bool = False
    ly_do: str = ""
    so_lieu: list[SoDaDoc] = field(default_factory=list)
    thanh_phan: list[str] = field(default_factory=list)
    luong: list[str] = field(default_factory=list)
    mo_ta: str = ""
    bo_vi_khong_neo: int = 0        # số giá trị bị loại vì trích dẫn không chứa nó


@dataclass
class ThongKeAnh:
    luot_goi: int = 0
    luot_goi_hong: int = 0
    doc_duoc: int = 0
    khong_doc_duoc: int = 0
    so_lieu: int = 0
    trich_dan_bia: int = 0
    bo_qua_qua_lon: int = 0
    bo_qua_dinh_dang: int = 0
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
                f"{self.doc_duoc} ảnh đọc được · {self.khong_doc_duoc} không đọc được · "
                f"{self.so_lieu} số liệu lấy được · "
                f"{self.trich_dan_bia} giá trị bị loại vì trích dẫn không chứa nó · "
                f"{self.bo_qua_qua_lon} ảnh bỏ qua vì quá lớn · "
                f"{self.bo_qua_dinh_dang} ảnh bỏ qua vì định dạng")


# ---------------------------------------------------------------------------
# Đóng gói ảnh
# ---------------------------------------------------------------------------
def thu_nho(data: bytes, dinh_dang: str, *, canh: int = MAX_CANH) -> tuple[bytes, str]:
    """Thu nhỏ ảnh nếu có Pillow. Không có thì trả nguyên — KHÔNG ném lỗi."""
    try:
        import io as _io

        from PIL import Image                      # noqa: PLC0415 — phụ thuộc tuỳ chọn
    except ImportError:
        return data, dinh_dang
    try:
        im = Image.open(_io.BytesIO(data))
        if max(im.size) <= canh:
            return data, dinh_dang
        im = im.convert("RGB")
        ty = canh / max(im.size)
        im = im.resize((max(1, int(im.width * ty)), max(1, int(im.height * ty))))
        buf = _io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue(), "png"
    except Exception:                              # ảnh hỏng thì cứ gửi nguyên bản
        return data, dinh_dang


def dong_goi(data: bytes, dinh_dang: str) -> str | None:
    """Data URL cho `image_url`. Trả `None` khi ảnh quá lớn — KHÔNG cắt bừa.

    Dạng thông điệp lấy đúng theo lượt dò 0.10 đã xác nhận chạy được với gateway
    (`{"type": "image_url", "image_url": {"url": "data:image/png;base64,…"}}`).
    """
    data, dinh_dang = thu_nho(data, dinh_dang)
    if len(data) > MAX_BYTE:
        return None
    mime = MIME.get(dinh_dang, "image/png")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


# ---------------------------------------------------------------------------
# Cổng NT2 + chuyển số NT1
# ---------------------------------------------------------------------------
def _chuan(s: str) -> str:
    return " ".join((s or "").lower().replace(",", ",").split())


def neo_duoc(gia_tri_raw: str, trich_dan: str) -> bool:
    """Giá trị model đưa ra có thật sự nằm trong đoạn nó nói đã nhìn thấy không.

    Không có văn bản gốc để đối chiếu như C3/C5, nên đây là cổng chống bịa DUY
    NHẤT kiểm được bằng code: một con số không xuất hiện trong chính đoạn trích
    dẫn của nó là dấu hiệu model tự nghĩ ra.
    """
    g, t = _chuan(gia_tri_raw), _chuan(trich_dan)
    if not g or not t:
        return False
    return g in t


def _thanh_so(s: SoLieuAnh) -> SoDaDoc:
    """CODE ra số, không phải model (NT1). Lưỡng nghĩa thì giữ cả hai cách đọc."""
    pn = parse_number(s.gia_tri_raw)
    return SoDaDoc(
        nhan=s.nhan.strip(), raw=s.gia_tri_raw.strip(),
        gia_tri=pn.value if pn else None,
        don_vi=s.don_vi.strip(), trich_dan=s.trich_dan.strip(),
        luong_nghia=bool(pn and pn.ambiguous),
        gia_tri_khac=pn.alt_value if pn else None)


# ---------------------------------------------------------------------------
class DocAnh:
    """Đọc ảnh bằng model vision. Một ảnh một lượt gọi (một nhiệm vụ một lần gọi)."""

    def __init__(self, client: LLMClient | None = None, *, model: str | None = None,
                 loai: tuple[Loai, ...] | list[str] = LOAI_MAC_DINH,
                 on_tien_do=None, song_song: int = 1):
        self.client = client or LLMClient()
        self.model = model or getattr(self.client, "vision_model", "") or None
        self.loai = tuple(loai)
        self.on_tien_do = on_tien_do
        self.song_song = max(1, song_song)
        self.tk = ThongKeAnh()

    # ------------------------------------------------------------------
    def doc_mot(self, anh: Anh, loai: Loai, data: bytes) -> KetQuaDocAnh:
        kq = KetQuaDocAnh(ma_anh=anh.ma, loai=loai, location=anh.location)
        if anh.dinh_dang not in MIME:
            # emf/wmf và định dạng lạ: gateway không nhận, gọi đi là đốt ~40 giây
            # để nhận về một lỗi. Bỏ TRƯỚC khi gọi, kèm lý do (NT4).
            self.tk.tang("bo_qua_dinh_dang")
            kq.ly_do = (f"định dạng `{anh.dinh_dang}` không gửi được cho model "
                        f"vision (chỉ nhận {', '.join(sorted(set(MIME.values())))})")
            return kq
        url = dong_goi(data, anh.dinh_dang)
        if url is None:
            self.tk.tang("bo_qua_qua_lon")
            kq.ly_do = (f"ảnh {len(data) // 1024} KB vượt mức gửi được "
                        f"({MAX_BYTE // 1024} KB) và không thu nhỏ được")
            return kq

        nhac = NHAC.get(loai, NHAC_KHAC)
        ngu_canh = anh.ngu_canh()[:800]
        self.tk.tang("luot_goi")
        try:
            out = self.client.extract(LUOC_DO.get(loai, DocConsole), [
                {"role": "system", "content": HE_THONG},
                {"role": "user", "content": [
                    {"type": "text",
                     "text": f"{nhac}\n\nChữ quanh ảnh trong tài liệu (chỉ để tham "
                             f"khảo ngữ cảnh, KHÔNG được lấy số từ đây):\n{ngu_canh}"},
                    {"type": "image_url", "image_url": {"url": url}},
                ]},
            ], model=self.model)
        except (ExtractionFailed, LLMError) as e:
            self.tk.tang("luot_goi_hong")
            self.tk.them_loi(f"{anh.ma}: {e}")
            kq.ly_do = f"lỗi gọi mô hình: {e}"
            return kq

        return self._doc_ket_qua(kq, out)

    def _doc_ket_qua(self, kq: KetQuaDocAnh, out: BaseModel) -> KetQuaDocAnh:
        if not out.doc_duoc:
            self.tk.tang("khong_doc_duoc")
            kq.ly_do = (out.ly_do_khong_doc_duoc or "").strip() or "model không nêu lý do"
            return kq

        kq.doc_duoc = True
        self.tk.tang("doc_duoc")
        if isinstance(out, DocSoDo):
            kq.thanh_phan = [t.strip() for t in out.thanh_phan if t.strip()]
            kq.luong = [t.strip() for t in out.luong if t.strip()]
            kq.mo_ta = out.mo_ta.strip()
            if not (kq.thanh_phan or kq.luong or kq.mo_ta):
                # "Đọc được" mà không nêu được gì thì coi như không đọc được.
                kq.doc_duoc = False
                kq.ly_do = "model báo đọc được nhưng không nêu thành phần nào"
                self.tk.tang("doc_duoc", -1)
                self.tk.tang("khong_doc_duoc")
            return kq

        for s in out.so_lieu:
            if not neo_duoc(s.gia_tri_raw, s.trich_dan):
                kq.bo_vi_khong_neo += 1
                self.tk.tang("trich_dan_bia")
                continue
            kq.so_lieu.append(_thanh_so(s))
            self.tk.tang("so_lieu")
        if not kq.so_lieu and kq.bo_vi_khong_neo:
            kq.doc_duoc = False
            kq.ly_do = (f"{kq.bo_vi_khong_neo} giá trị model đưa ra đều không nằm "
                        f"trong trích dẫn của chính nó — không dùng được")
            self.tk.tang("doc_duoc", -1)
            self.tk.tang("khong_doc_duoc")
        return kq

    # ------------------------------------------------------------------
    def run(self, doc: DocxDocument) -> list[KetQuaDocAnh]:
        """Đọc mọi ảnh thuộc các loại đã chọn. Ảnh loại khác KHÔNG bị gọi tới."""
        import zipfile

        viec = self._chon_anh(doc)
        ra: list[KetQuaDocAnh] = []
        if not viec:
            return ra
        try:
            goi = zipfile.ZipFile(doc.path)
        except (OSError, zipfile.BadZipFile) as e:
            self.tk.them_loi(f"không mở được {doc.path}: {e}")
            return ra

        with goi:
            co = set(goi.namelist())
            cong_viec = [(a, l, goi.read(a.duong_dan_media))
                         for a, l in viec if a.duong_dan_media in co]

        def _lam(i_ct):
            i, (a, l, data) = i_ct
            kq = self.doc_mot(a, l, data)
            self._bao(i, len(cong_viec), a)
            return kq

        if self.song_song > 1:
            with cf.ThreadPoolExecutor(max_workers=self.song_song) as ex:
                ra = list(ex.map(_lam, enumerate(cong_viec, 1)))
        else:
            ra = [_lam(x) for x in enumerate(cong_viec, 1)]
        return ra

    def _chon_anh(self, doc: DocxDocument) -> list[tuple[Anh, Loai]]:
        """Ảnh nào được đọc: chỉ những loại đã chọn. Phân loại lại bằng 2.2."""
        import zipfile

        from .anh import trich_anh

        kq = trich_anh(doc)
        if not kq.anh:
            return []
        ra: list[tuple[Anh, Loai]] = []
        try:
            with zipfile.ZipFile(doc.path) as goi:
                co = set(goi.namelist())
                for a in kq.anh:
                    data = (goi.read(a.duong_dan_media)
                            if a.duong_dan_media in co else None)
                    r = phan_loai(a, data)
                    if r.loai in self.loai:
                        ra.append((a, r.loai))
        except (OSError, zipfile.BadZipFile):
            return []
        return ra

    def _bao(self, i: int, tong: int, anh: Anh) -> None:
        if self.on_tien_do:
            self.on_tien_do(i, tong, f"{anh.ma} · {anh.location}")


# ---------------------------------------------------------------------------
def uoc_tinh_luot_goi_anh(doc: DocxDocument, loai=LOAI_MAC_DINH) -> dict:
    """Số lượt gọi vision cho một tài liệu, ĐẾM TRƯỚC khi tiêu tiền."""
    tt = tom_tat_anh(doc)
    theo = {n.loai: n.so_luong for n in tt.nhom}
    chon = sum(v for k, v in theo.items() if k in loai)
    return {"tong_anh": tt.tong, "se_doc": chon, "theo_loai": theo,
            "loai_chon": list(loai)}


def thanh_finding(kq: KetQuaDocAnh) -> Finding:
    """Một kết quả đọc ảnh -> một finding có căn cứ (NT2).

    Đọc được thì căn cứ là chính các trích dẫn model chép từ ảnh; không đọc được
    thì vẫn ra finding `khong_kiem_chung_duoc` kèm lý do — im lặng là vi phạm NT4.
    """
    if not kq.doc_duoc:
        return Finding(
            id=f"C2-ANH-{kq.ma_anh}", severity="info",
            category="khong_kiem_chung_duoc",
            finding=f"Chưa đọc được nội dung ảnh tại {kq.location}: {kq.ly_do}.",
            computed_evidence=f"ảnh {kq.ma_anh}, loại {kq.loai}",
            location=kq.location,
            suggestion="Nêu lại nội dung ảnh bằng chữ trong tài liệu.",
            confidence="cao")

    if kq.loai == "so_do":
        noi_dung = (f"Đọc được sơ đồ tại {kq.location}: "
                    f"{len(kq.thanh_phan)} thành phần, {len(kq.luong)} luồng.")
        can_cu = "; ".join(kq.thanh_phan[:8]) + ("…" if len(kq.thanh_phan) > 8 else "")
    else:
        noi_dung = (f"Đọc được {len(kq.so_lieu)} số liệu trong ảnh tại {kq.location}.")
        can_cu = " · ".join(f"{s.nhan}={s.raw}{(' ' + s.don_vi) if s.don_vi else ''}"
                            for s in kq.so_lieu[:6])
    them = (f" ({kq.bo_vi_khong_neo} giá trị bị loại vì trích dẫn không chứa nó)"
            if kq.bo_vi_khong_neo else "")
    return Finding(
        id=f"C2-ANH-{kq.ma_anh}", severity="info", category="khong_kiem_chung_duoc",
        finding=noi_dung + them + " Nội dung này do model đọc từ ảnh, cần người "
                                  "kiểm chứng lại.",
        computed_evidence=can_cu or kq.mo_ta,
        location=kq.location,
        suggestion="Đối chiếu số liệu trong ảnh với bảng số liệu của tài liệu.",
        confidence="vua")
