"""C2 · 2.2 — phân loại ảnh, THUẦN CODE, không gọi model.

Vì sao phải phân loại trước khi gọi vision: 767 ảnh × ~40 giây/lượt ≈ 8,5 giờ máy.
Biết trước ảnh thuộc loại nào thì 2.3 hỏi đúng câu cho từng loại thay vì hỏi một
câu chung cho mọi thứ.

## Năm loại này lấy từ đâu

KHÔNG lấy từ suy đoán. Lấy từ **40 ảnh mẫu phân tầng theo hồ sơ, được xem tận
mắt và gán nhãn tay** (`data/nhan_anh_mau.json`). Phân bố đo được khác
hẳn giả định ban đầu của PLAN mục 2.2 (*"sơ đồ / biểu đồ-dashboard / khác"*):

| Loại | Mẫu | Vì sao tách riêng |
|---|---|---|
| `console` | 14/40 | **Lớp đông nhất.** Ảnh chụp `top`, `free`, `lscpu`, `kubectl` — chứa số đo thật, chữ dày, OCR đọc tốt |
| `dashboard` | 11/40 | Grafana/APM: số nằm trong ô KPI và đồng hồ, đồ thị thì chỉ đọc được xu hướng |
| `so_do` | 9/40 | Sơ đồ kiến trúc/topology — không có số để đối chiếu, nhưng là căn cứ cho quy tắc định tính Vòng 1 |
| `anh_van_ban` | 6/40 | Ảnh chụp bảng, email, trang kết quả SPEC CINT2006 — đọc như văn bản |
| `chua_ro` | — | Tín hiệu mâu thuẫn hoặc thiếu (NT4) |

Gộp `console` vào "khác" như PLAN viết ban đầu sẽ vứt đi đúng cái lớp mà PNX hay
nhận xét nhất — ảnh sở cứ đo tải.

## Tín hiệu nào dùng được, và tín hiệu nào ĐÃ ĐO LÀ HỎNG

Đo trên chính 40 ảnh đó:

- ❌ **Từ khoá quanh ảnh KHÔNG tách được `console` ↔ `dashboard`**: bắt được 4/14
  và 2/11. Lý do có thể thấy bằng mắt: cả hai đều nằm dưới cùng một đề mục
  *"TÍNH TOÁN CẤU HÌNH PHẦN CỨNG"*, vì chúng là sở cứ cho cùng một phép tính.
- ❌ **Alt text và tên shape**: 6/777 tên có nghĩa (đo ở `anh.py`). Tín hiệu chết.
- ✅ **Nền tối / nền sáng**: tách được nhóm "ảnh chụp công cụ" khỏi nhóm "hình vẽ".
  24/25 ảnh nền tối là console hoặc dashboard.
- ✅ **Mật độ dòng chữ** (`tr_tb`, `tr_cao`): trên mẫu, console ≥ 15,8 và dashboard
  ≤ 11,0 — không chồng lấn. Đây là tín hiệu mạnh nhất.
- ✅ **Số màu + độ rực**: sơ đồ nhiều màu phẳng, ảnh chụp văn bản gần như xám hết.
- 🟡 **Từ khoá nhóm `sơ đồ`** phủ 9/9 sơ đồ nhưng cũng nổ ở 4/11 dashboard, nên chỉ
  dùng làm tín hiệu PHỤ, không bao giờ tự nó quyết định.

## Ba giới hạn phải nói ra khi công bố số

1. **n = 40**, năm lớp — mẫu nhỏ. Ngưỡng ở đây khớp mẫu này, chưa chắc khớp kho.
2. **Nhãn do một tác nhân AI nhìn ảnh mà gán**, không phải người thẩm định xác
   nhận — cùng hạn chế đã ghi cho eval set (`docs/0.7-nhan-vang-tu-pnx.md`).
3. Không có Pillow thì KHÔNG có tín hiệu pixel; khi đó module trả `chua_ro` kèm
   lý do chứ không đoán theo mỗi từ khoá (NT4).
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from typing import Literal

from ..ingestion.docx_reader import DocxDocument
from .anh import Anh, trich_anh

Loai = Literal["so_do", "console", "dashboard", "anh_van_ban", "chua_ro"]
DoTin = Literal["cao", "vua", "thap"]

# --- Ngưỡng, đặt tên và ghi rõ nguồn số. Sửa thì phải chạy lại eval 2.2. -----
NGUONG_TOI = 0.60          # tỷ lệ điểm ảnh tối; console 0,74–0,93 · dashboard 0,41–0,97
NGUONG_SANG = 0.75         # sơ đồ 0,89–0,96 · ảnh chụp văn bản 0,91–0,98
TR_TB_CHU_DAY = 15.0       # console min đo được 15,8
TR_TB_IT_CHU = 11.5        # dashboard max đo được 11,0
TR_CAO_CHU_DAY = 0.40      # console min 0,44 · dashboard 10/11 dưới 0,26
SO_MAU_NHIEU = 45          # sơ đồ trung bình 71 màu · ảnh chụp văn bản 26–37
VIVID_SO_DO = 0.02         # sơ đồ 0,053 · ảnh chụp văn bản 0,006–0,017
MAU_MEM = 96               # cạnh ảnh thu nhỏ khi đếm màu
MAU_QUET = 900             # cạnh tối đa khi quét mật độ chữ

_TU_SO_DO = re.compile(
    r"sơ\s*đồ|so\s*do|mô\s*hình|mo\s*hinh|kiến\s*trúc|kien\s*truc|topology|"
    r"mô\s*hình\s*logic|vật\s*lý|luồng\s*(dữ\s*liệu|xử\s*lý)|triển\s*khai",
    re.IGNORECASE)


@dataclass
class DacTrungAnh:
    """Số đo thuần code của một ảnh. Mọi trường ở đây là bằng chứng cho NT2."""

    sang: float = 0.0          # độ sáng trung bình 0–1
    toi: float = 0.0           # tỷ lệ điểm ảnh tối
    bao_hoa: float = 0.0
    so_mau: int = 0            # số màu khác nhau sau khi lượng tử hoá 3 bit/kênh
    nen: float = 0.0           # tỷ lệ của màu phổ biến nhất
    xam: float = 0.0           # tỷ lệ điểm gần như không màu
    vivid: float = 0.0         # tỷ lệ điểm màu rực
    tr_tb: float = 0.0         # số lần đổi sáng/tối trung bình trên một hàng quét
    tr_cao: float = 0.0        # tỷ lệ hàng quét có ≥12 lần đổi — dấu của chữ dày

    def as_dict(self) -> dict:
        return dict(self.__dict__)


@dataclass
class KetQuaPhanLoai:
    loai: Loai = "chua_ro"
    do_tin: DoTin = "thap"
    tin_hieu: list[str] = field(default_factory=list)   # căn cứ, NT2
    dac_trung: DacTrungAnh | None = None
    ly_do_khong_ro: str = ""


# ---------------------------------------------------------------------------
def do_dac_trung(data: bytes) -> DacTrungAnh | None:
    """Đo đặc trưng pixel. Trả `None` khi không đọc được ảnh — KHÔNG đoán."""
    try:
        from PIL import Image                      # noqa: PLC0415 — phụ thuộc tuỳ chọn
    except ImportError:
        return None
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception:                              # ảnh hỏng, định dạng lạ (emf/wmf)
        return None

    dt = DacTrungAnh()
    nho = im.resize((MAU_MEM, MAU_MEM))
    # `tobytes()` chứ không `getdata()`: getdata bị bỏ ở Pillow 14, mà `pyproject`
    # chỉ ghim `pillow>=10.0` nên bản mới sẽ vào đây mà không ai để ý.
    tho = nho.tobytes()
    px = [(tho[i], tho[i + 1], tho[i + 2]) for i in range(0, len(tho), 3)]
    n = len(px)
    lum = [(0.299 * r + 0.587 * g + 0.114 * b) / 255 for r, g, b in px]
    dt.sang = sum(lum) / n
    dt.toi = sum(1 for x in lum if x < 0.25) / n
    dt.bao_hoa = sum((max(c) - min(c)) / max(1, max(c)) for c in px) / n
    dt.xam = sum(1 for c in px if max(c) - min(c) < 25) / n
    dem: dict[tuple[int, int, int], int] = {}
    for r, g, b in px:
        k = (r >> 5, g >> 5, b >> 5)
        dem[k] = dem.get(k, 0) + 1
    dt.so_mau = len(dem)
    dt.nen = max(dem.values()) / n

    # Mật độ chữ: quét ngang, đếm số lần đổi sáng/tối. Chữ đơn sắc trên nền tối
    # cho rất nhiều lần đổi mỗi hàng; đồ thị và hình vẽ thì ít.
    w, h = im.size
    k = min(1.0, MAU_QUET / max(w, h))
    if k < 1:
        im = im.resize((max(1, int(w * k)), max(1, int(h * k))))
    W, H = im.size
    lay = im.load()
    buoc_y, buoc_x = max(1, H // 120), max(1, W // 200)
    cot = range(0, W, buoc_x)
    vivid = 0
    tong_diem = 0
    hang: list[int] = []
    for y in range(0, H, buoc_y):
        truoc = None
        doi = 0
        for x in cot:
            r, g, b = lay[x, y]
            mx, mn = max(r, g, b), min(r, g, b)
            tong_diem += 1
            if mx and (mx - mn) / mx >= 0.35 and mx >= 80:
                vivid += 1
            nay = (0.299 * r + 0.587 * g + 0.114 * b) > 110
            if truoc is not None and nay != truoc:
                doi += 1
            truoc = nay
        hang.append(doi)
    dt.vivid = vivid / max(1, tong_diem)
    dt.tr_tb = sum(hang) / max(1, len(hang))
    dt.tr_cao = sum(1 for t in hang if t >= 12) / max(1, len(hang))
    return dt


# ---------------------------------------------------------------------------
def _co_tu_so_do(anh: Anh) -> bool:
    return bool(_TU_SO_DO.search(anh.ngu_canh()))


def phan_loai(anh: Anh, data: bytes | None) -> KetQuaPhanLoai:
    """Phân loại một ảnh từ pixel + ngữ cảnh. Không chắc thì trả `chua_ro`.

    Thứ tự có chủ ý: **pixel quyết định, chữ chỉ xác nhận**. Ngược lại sẽ dẫn tới
    gán nhãn theo đề mục, mà đề mục đã đo là không tách được console/dashboard.
    """
    kq = KetQuaPhanLoai()
    if not data:
        kq.ly_do_khong_ro = "không đọc được nội dung ảnh"
        return kq

    dt = do_dac_trung(data)
    kq.dac_trung = dt
    if dt is None:
        # Thiếu Pillow, hoặc ảnh vector (emf/wmf) Pillow không mở được.
        kq.ly_do_khong_ro = ("không đo được đặc trưng ảnh (thiếu Pillow hoặc định "
                             f"dạng không đọc được: {anh.dinh_dang})")
        if _co_tu_so_do(anh):
            kq.tin_hieu.append("ngữ cảnh có từ khoá sơ đồ/kiến trúc")
        return kq

    nen_toi = dt.toi >= NGUONG_TOI
    nen_sang = dt.sang >= NGUONG_SANG and dt.toi <= 0.15
    chu_day = dt.tr_tb >= TR_TB_CHU_DAY and dt.tr_cao >= TR_CAO_CHU_DAY
    it_chu = dt.tr_tb <= TR_TB_IT_CHU

    if nen_toi:
        kq.tin_hieu.append(f"nền tối ({dt.toi:.0%} điểm ảnh tối)")
        if chu_day:
            kq.loai, kq.do_tin = "console", "cao"
            kq.tin_hieu.append(f"chữ dày ({dt.tr_tb:.0f} lần đổi/hàng, "
                               f"{dt.tr_cao:.0%} hàng dày chữ)")
        elif it_chu:
            kq.loai, kq.do_tin = "dashboard", "cao"
            kq.tin_hieu.append(f"ít chữ, nhiều mảng màu ({dt.tr_tb:.0f} lần đổi/hàng, "
                               f"{dt.vivid:.1%} điểm màu rực)")
        else:
            kq.ly_do_khong_ro = (f"nền tối nhưng mật độ chữ nằm giữa hai ngưỡng "
                                 f"({dt.tr_tb:.1f})")
        return kq

    if nen_sang:
        kq.tin_hieu.append(f"nền sáng (độ sáng {dt.sang:.2f})")
        nhieu_mau = dt.so_mau >= SO_MAU_NHIEU and dt.vivid >= VIVID_SO_DO
        # ĐÃ THỬ VÀ BỎ (2026-09-04): cho từ khoá `sơ đồ` tự quyết ở nhánh này —
        # nó vá được 2 sơ đồ nét phẳng bị bỏ ngỏ, nhưng kéo 4 ảnh chụp bảng sang
        # `so_do`, độ chính xác khi kết luận rơi 92% -> 82%. Đúng như precision
        # 9/16 của nhóm từ đó đã báo trước. Từ khoá chỉ được NÂNG độ tin.
        if nhieu_mau and not chu_day:
            kq.loai, kq.do_tin = "so_do", "cao" if _co_tu_so_do(anh) else "vua"
            kq.tin_hieu.append(f"{dt.so_mau} màu, {dt.vivid:.1%} điểm màu rực, ít chữ")
            if _co_tu_so_do(anh):
                kq.tin_hieu.append("ngữ cảnh có từ khoá sơ đồ/kiến trúc")
        elif dt.xam >= 0.85 and dt.vivid < VIVID_SO_DO:
            kq.loai, kq.do_tin = "anh_van_ban", "vua"
            kq.tin_hieu.append(f"gần như không màu ({dt.xam:.0%} điểm xám), "
                               f"{dt.vivid:.1%} điểm màu rực")
        else:
            kq.ly_do_khong_ro = (f"nền sáng nhưng màu sắc không đủ tách sơ đồ khỏi "
                                 f"ảnh chụp văn bản ({dt.so_mau} màu, "
                                 f"{dt.vivid:.1%} rực)")
        return kq

    kq.ly_do_khong_ro = (f"nền không rõ tối hay sáng (sáng {dt.sang:.2f}, "
                         f"tối {dt.toi:.0%})")
    if _co_tu_so_do(anh):
        kq.tin_hieu.append("ngữ cảnh có từ khoá sơ đồ/kiến trúc")
    return kq


# ---------------------------------------------------------------------------
# 2.4 — tóm tắt cho cảnh báo NT4 của pipeline
# ---------------------------------------------------------------------------
MAX_VI_TRI = 5          # cảnh báo chỉ nêu vài vị trí đầu, không đổ cả 58 dòng


@dataclass
class NhomAnh:
    loai: Loai
    so_luong: int = 0
    vi_tri: list[str] = field(default_factory=list)


@dataclass
class TomTatAnh:
    """Ảnh của một tài liệu, đã đếm theo loại. Đầu vào cho cảnh báo NT4."""

    tong: int = 0
    nhom: list[NhomAnh] = field(default_factory=list)
    canh_bao: list[str] = field(default_factory=list)
    da_phan_loai: bool = False      # False = không đo được pixel, chỉ có tổng số


def tom_tat_anh(doc: DocxDocument) -> TomTatAnh:
    """Đếm ảnh theo loại. THUẦN CODE, không gọi model — dùng được cả ở laptop.

    Xuống cấp có kiểm soát (NT4): đọc được file thì phân loại; không đọc được
    (thiếu Pillow, ảnh vector, file hỏng) thì vẫn trả TỔNG SỐ ảnh kèm lý do, chứ
    không im lặng bỏ và cũng không đoán loại.
    """
    ra = TomTatAnh()
    kq = trich_anh(doc)
    ra.canh_bao = list(kq.canh_bao)
    ra.tong = len(kq.anh)
    if not kq.anh:
        return ra

    theo_loai: dict[str, NhomAnh] = {}
    # Mở gói .docx MỘT lần cho cả tài liệu. `byte_anh` mở lại cho từng ảnh, mà một
    # bản sizing thật có tới 58 ảnh.
    try:
        goi = zipfile.ZipFile(doc.path)
    except (OSError, zipfile.BadZipFile) as e:
        ra.canh_bao.append(f"không mở được file để đọc ảnh: {e}")
        return ra
    with goi:
        ten_co = set(goi.namelist())
        for a in kq.anh:
            data = goi.read(a.duong_dan_media) if a.duong_dan_media in ten_co else None
            r = phan_loai(a, data)
            if r.loai != "chua_ro":
                ra.da_phan_loai = True
            n = theo_loai.setdefault(r.loai, NhomAnh(loai=r.loai))
            n.so_luong += 1
            if len(n.vi_tri) < MAX_VI_TRI:
                n.vi_tri.append(a.location)

    # Thứ tự trình bày: loại nào nhiều khả năng chứa SỐ ĐO nhất đứng trước, vì đó
    # là phần người thẩm định hay đòi sở cứ nhất.
    uu_tien = ["console", "dashboard", "anh_van_ban", "so_do", "chua_ro"]
    ra.nhom = sorted(theo_loai.values(),
                     key=lambda n: (uu_tien.index(n.loai) if n.loai in uu_tien
                                    else len(uu_tien), -n.so_luong))
    return ra
