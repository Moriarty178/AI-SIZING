"""C2 · 2.1 — trích ảnh khỏi `.docx` KÈM NGỮ CẢNH, không gọi model.

Một ảnh trần không dùng được: 767 ảnh trong 47 bản sizing thật, gửi hết cho model
vision là ~8,5 giờ máy ở tốc độ ~40 giây/lượt. Muốn hỏi ít mà trúng thì phải biết
trước ảnh nằm ở đâu và quanh nó viết gì.

**Bốn phép đo trên chính 47 bản đó, làm cơ sở cho mọi lựa chọn ở đây** (đo bằng
code, không phải ước lượng):

| Tín hiệu | Độ phủ | Kết luận |
|---|---|---|
| `wp:docPr/@descr` (alt text) | 154/953, nội dung là `IMG_256`, `cid:…`, đường dẫn máy người viết | gần như vô dụng, vẫn giữ vì rẻ |
| `pic:cNvPr/@name` (tên file lúc dán) | **6/777 có nghĩa** | tín hiệu chết |
| Caption kiểu "Hình 3. …" | **107/767 (14%)**, phần lớn nằm NGAY SAU ảnh | dùng được nhưng không thể phụ thuộc |
| Đoạn văn liền trước ảnh | 762/767 (99%) | **đây mới là ngữ cảnh chính** |

Nên module này lấy ngữ cảnh theo thứ tự ngược với trực giác: **văn bản xung quanh
trước, caption sau, alt text cuối**. Ai định sửa theo hướng "đọc alt text cho
nhanh" thì xem lại bảng trên.

Ranh giới: ở đây KHÔNG có suy đoán nội dung ảnh. Phân loại là việc của
`phan_loai.py` (2.2), đọc ảnh là việc của 2.3. Module này chỉ nhặt sự kiện đọc
được từ file, và **nói ra phần nó không nhặt được** (NT4): ảnh trong ô bảng, ảnh
ở header/footer và file `media` không đoạn nào tham chiếu tới đều được đếm và
báo, không im lặng bỏ qua.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field

from ..ingestion.docx_reader import AnhRef, DocxDocument

# Số đoạn văn bản lấy mỗi phía. 3 là đủ để bọc trọn cụm "câu dẫn + ảnh + caption"
# thường gặp, mà chưa kéo sang phân hệ kế bên.
SO_DOAN_NGU_CANH = 3
MAX_KY_TU_MOI_DOAN = 400        # bảng làm phẳng có thể rất dài, cắt cho gọn
KHOANG_CACH_CAPTION = 2         # caption phải sát ảnh, cách xa hơn là đoạn khác

# "Hình 3.", "Hình 1.2.5:", "Figure 4 -", "Sơ đồ 2", "Bảng 1." (ảnh chụp bảng).
# Đo trên 47 bản: 76/107 caption nằm ngay SAU ảnh, chỉ 5 nằm trước.
_CAPTION = re.compile(
    r"^\s*(?P<nhan>hình|hinh|figure|fig|ảnh|anh|sơ\s*đồ|so\s*do|biểu\s*đồ|bieu\s*do|bảng|bang|table)"
    r"\s*(?P<so>[0-9IVXivx]+(?:\.[0-9]+)*)?\s*[.:)\-–]?\s+(?P<mo_ta>\S.*)$",
    re.IGNORECASE,
)

_DINH_DANG = {b"\x89PNG\r\n\x1a\n": "png", b"\xff\xd8\xff": "jpeg",
              b"GIF87a": "gif", b"GIF89a": "gif", b"BM": "bmp",
              b"\x01\x00\x00\x00": "emf", b"\xd7\xcd\xc6\x9a": "wmf"}


@dataclass
class Anh:
    """Một ảnh đã trích, kèm mọi thứ đọc được mà KHÔNG cần nhìn vào ảnh."""

    ma: str                          # "anh#12" — ổn định giữa các lần đọc cùng file
    element_index: int               # phần tử C1 chứa ảnh, để neo lại vào tài liệu
    thu_tu_trong_doan: int = 0       # một đoạn có thể chứa nhiều ảnh
    rid: str = ""
    duong_dan_media: str = ""        # "word/media/image7.png"
    dinh_dang: str = ""              # png | jpeg | emf | wmf | gif | bmp | khong_ro
    so_byte: int = 0
    rong_px: int | None = None       # None với ảnh vector (emf/wmf) — không có pixel
    cao_px: int | None = None
    emu_rong: int | None = None      # kích thước HIỂN THỊ trong Word
    emu_cao: int | None = None
    neo: str = "inline"
    alt: str = ""
    ten_shape: str = ""
    page: int | None = None
    section: str = ""
    section_title: str = ""
    caption: str = ""
    caption_nguon: str = ""          # sau | truoc | chinh_doan | "" (không có)
    truoc: list[str] = field(default_factory=list)
    sau: list[str] = field(default_factory=list)

    @property
    def location(self) -> str:
        parts = []
        if self.section:
            parts.append(f"Mục {self.section}")
        if self.page is not None:
            parts.append(f"trang {self.page}")
        return ", ".join(parts) or f"phần tử #{self.element_index}"

    @property
    def ty_le(self) -> float | None:
        """Tỷ lệ rộng/cao. Ưu tiên pixel thật; ảnh vector thì lấy cỡ hiển thị."""
        for r, c in ((self.rong_px, self.cao_px), (self.emu_rong, self.emu_cao)):
            if r and c:
                return r / c
        return None

    def ngu_canh(self) -> str:
        """Toàn bộ chữ quanh ảnh, gộp thành một khối để dò từ khoá hoặc gửi model."""
        phan = [self.section_title, *self.truoc, self.caption, *self.sau,
                self.alt if not _alt_rac(self.alt) else ""]
        return "\n".join(p.strip() for p in phan if p and p.strip())


@dataclass
class KetQuaTrichAnh:
    anh: list[Anh] = field(default_factory=list)
    canh_bao: list[str] = field(default_factory=list)
    media_khong_dung: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Đọc thuộc tính file ảnh — tự phân tích header, KHÔNG thêm phụ thuộc
# ---------------------------------------------------------------------------
def _dinh_dang(data: bytes) -> str:
    for magic, ten in _DINH_DANG.items():
        if data.startswith(magic):
            return ten
    return "khong_ro"


def _kich_thuoc_px(data: bytes, dinh_dang: str) -> tuple[int | None, int | None]:
    """(rộng, cao) theo pixel. Vector và file hỏng trả `(None, None)` — KHÔNG đoán.

    Tự đọc header thay vì gọi Pillow: `pyproject.toml` chỉ khai phụ thuộc lõi tối
    thiểu cho Giai đoạn 1, và một hàm 30 dòng rẻ hơn việc buộc mọi người cài thêm
    thư viện ảnh chỉ để biết chiều rộng.
    """
    try:
        if dinh_dang == "png" and len(data) >= 24:
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if dinh_dang == "gif" and len(data) >= 10:
            return (int.from_bytes(data[6:8], "little"),
                    int.from_bytes(data[8:10], "little"))
        if dinh_dang == "bmp" and len(data) >= 26:
            return (int.from_bytes(data[18:22], "little", signed=True),
                    int.from_bytes(data[22:26], "little", signed=True))
        if dinh_dang == "jpeg":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                seg = int.from_bytes(data[i + 2:i + 4], "big")
                # SOF0..SOF15 trừ DHT(C4)/JPG(C8)/DAC(CC) — nơi ghi kích thước thật
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    return (int.from_bytes(data[i + 7:i + 9], "big"),
                            int.from_bytes(data[i + 5:i + 7], "big"))
                i += 2 + seg
    except (ValueError, IndexError):
        return None, None
    return None, None


def _alt_rac(alt: str) -> bool:
    """Alt text vô nghĩa. Đo thật: `IMG_256`, `cid:…`, `C:\\Users\\…\\987.png`."""
    a = alt.strip().lower()
    if not a:
        return True
    return bool(re.fullmatch(r"(img_?\d+|image\d*|picture\s*\d*|anh\d*|\d+)"
                             r"(\.(png|jpe?g|gif|emf|wmf|bmp))?", a)
                or a.startswith("cid:") or re.match(r"^[a-z]:[\\/]", a))


# ---------------------------------------------------------------------------
# Ngữ cảnh quanh ảnh
# ---------------------------------------------------------------------------
def _text_hien(el) -> str:
    """Chữ dùng được của một phần tử; bảng thì cắt bớt cho khỏi ngập ngữ cảnh."""
    t = (el.text or "").strip()
    return t[:MAX_KY_TU_MOI_DOAN]


def _lan_can(elements: list, i: int, buoc: int, so: int) -> list[str]:
    """`so` phần tử CÓ CHỮ gần nhất về một phía. Ảnh xen giữa thì nhảy qua."""
    ra: list[str] = []
    j = i + buoc
    while 0 <= j < len(elements) and len(ra) < so:
        t = _text_hien(elements[j])
        if t:
            ra.append(t)
        j += buoc
    return ra if buoc > 0 else list(reversed(ra))


def tach_caption(text: str) -> str:
    """Trả phần mô tả nếu `text` trông như một caption, ngược lại chuỗi rỗng."""
    m = _CAPTION.match(text.strip())
    if not m:
        return ""
    # "Hình" đứng một mình trong câu văn xuôi dài không phải caption.
    if len(text.strip()) > 200:
        return ""
    return text.strip()


def _tim_caption(elements: list, i: int, el_text: str) -> tuple[str, str]:
    """(caption, nguồn). Thứ tự ưu tiên theo số đo: ngay sau > chính đoạn > trước."""
    if (c := tach_caption(el_text)):
        return c, "chinh_doan"
    for buoc, nhan in ((1, "sau"), (-1, "truoc")):
        j = i + buoc
        buoc_da_di = 0
        while 0 <= j < len(elements) and buoc_da_di < KHOANG_CACH_CAPTION:
            t = _text_hien(elements[j])
            if t:
                buoc_da_di += 1
                if (c := tach_caption(t)):
                    return c, nhan
                break       # đoạn có chữ đầu tiên không phải caption thì thôi
            j += buoc
    return "", ""


# ---------------------------------------------------------------------------
def trich_anh(doc: DocxDocument, *, so_doan: int = SO_DOAN_NGU_CANH) -> KetQuaTrichAnh:
    """Trích mọi ảnh của một tài liệu đã đọc bằng C1, kèm ngữ cảnh và cảnh báo NT4."""
    ra = KetQuaTrichAnh()
    els = doc.elements
    da_dung: set[str] = set()

    try:
        z = zipfile.ZipFile(doc.path)
    except (OSError, zipfile.BadZipFile) as e:
        ra.canh_bao.append(f"Không mở được file để lấy ảnh: {e}")
        return ra

    with z:
        ten_trong_goi = set(z.namelist())
        for i, el in enumerate(els):
            if el.kind != "image":
                continue
            caption, nguon = _tim_caption(els, i, el.text or "")
            truoc = _lan_can(els, i, -1, so_doan)
            sau = _lan_can(els, i, 1, so_doan)
            refs: list[AnhRef] = el.anh_refs or []
            if not refs:
                ra.canh_bao.append(
                    f"Phần tử #{el.index} có ảnh nhưng không lần ra được file ảnh "
                    f"(thiếu quan hệ r:embed) — C2 sẽ không đọc được ảnh này.")
                continue
            for k, r in enumerate(refs):
                duong_dan = doc.rels.get(r.rid, "")
                data = b""
                if duong_dan and duong_dan in ten_trong_goi:
                    da_dung.add(duong_dan)
                    data = z.read(duong_dan)
                else:
                    ra.canh_bao.append(
                        f"Phần tử #{el.index}: rid {r.rid} không trỏ tới file ảnh nào "
                        f"trong gói — bỏ qua ảnh này.")
                    continue
                dd = _dinh_dang(data)
                rong, cao = _kich_thuoc_px(data, dd)
                ra.anh.append(Anh(
                    ma=f"anh#{el.index}" + (f".{k}" if len(refs) > 1 else ""),
                    element_index=el.index, thu_tu_trong_doan=k, rid=r.rid,
                    duong_dan_media=duong_dan, dinh_dang=dd, so_byte=len(data),
                    rong_px=rong, cao_px=cao, emu_rong=r.emu_rong, emu_cao=r.emu_cao,
                    neo=r.neo, alt=r.alt, ten_shape=r.ten_shape, page=el.page,
                    section=el.section, section_title=el.section_title,
                    caption=caption, caption_nguon=nguon, truoc=truoc, sau=sau))

    ra.media_khong_dung = [m for m in doc.media if m not in da_dung]
    if ra.media_khong_dung:
        # Thường là ảnh trong ô bảng hoặc ở header/footer — C1 không duyệt tới.
        # Đây là phần C2 CHƯA nhìn thấy, phải nói ra chứ không lặng lẽ bỏ (NT4).
        ra.canh_bao.append(
            f"{len(ra.media_khong_dung)} file ảnh trong gói không đoạn văn nào tham "
            f"chiếu tới (thường là ảnh trong ô bảng hoặc header/footer) — chưa trích "
            f"được ngữ cảnh cho chúng: "
            f"{', '.join(m.rsplit('/', 1)[-1] for m in ra.media_khong_dung[:5])}"
            + ("…" if len(ra.media_khong_dung) > 5 else ""))
    return ra


def byte_anh(doc: DocxDocument, anh: Anh) -> bytes:
    """Nội dung nhị phân của một ảnh — tách riêng để `Anh` không ôm dữ liệu nặng."""
    with zipfile.ZipFile(doc.path) as z:
        return z.read(anh.duong_dan_media)
