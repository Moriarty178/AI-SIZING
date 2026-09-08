"""C2 · 2.5 — đối chiếu số đọc từ ẢNH với số KHAI BÁO trong BẢNG.

## Vấn đề thật, sau khi đo lại (2026-09-08)

Bản bàn giao đặt bài toán là *"phân biệt số của hệ thống được định cỡ với số của
một máy bất kỳ trong ảnh"*, lấy PBH 4.0 làm ca âm vì `lscpu` ở đó ra
`AMD Ryzen 9 7950X` còn `df -h` ra `/run/user/1000`, `/boot/efi`, `/run/qemu`.

**Đọc bảng khai báo của chính hồ sơ đó thì tiền đề sụp:**

    Mục 2, tr.4   AMD Ryzen 9 7950x @ 4.50GHz 20 cores | 80 GB | Cint 109.375 | SSD 1024 GB
    Mục 2, tr.5   AMD Ryzen 9 7950x | Cint_rate2017 = 175
    Mục 3, tr.9   Test | RAM 125 | SSD 1024 | Tải CPU 31.2% | Tải Ram 71Gb | cint 109.375

Máy Ryzen ấy **là máy chuẩn đo mà tài liệu khai báo**, không phải máy cá nhân lạc
vào. `anh#79` (`top`) đọc ra `31.2 us`, `RAM total 128010 MiB` = 125,0 GiB — khớp
đúng ba giá trị khai báo. Và `109.375 = 175 × 20/32`: người viết lấy Cint cả chip
rồi nhân tỉ lệ 20 trên 32 CPU, nên «20 cores» khai báo vs «32 CPU(s)» trong ảnh là
**cố ý**, không phải lỗi.

Hai hệ quả, cả hai đều là lý do module này KHÔNG làm cái đã được gợi ý:

- Bộ lọc dấu vân tay máy cá nhân (`/run/user/1000`, tên CPU desktop…) sẽ vứt đúng
  bộ số neo tốt nhất trong kho. Thêm nữa `/run/user/1000` có mặt ở **cả hai** hồ
  sơ, kể cả Vtag, nên nó không phân biệt được gì.
- So «số trong ảnh khác số khai báo ⇒ cảnh báo» sẽ bắn nhầm ngay ở 20 vs 32 —
  đúng thứ `CLAUDE.md` xếp nặng hơn bỏ sót.

## Vì thế: NEO HAI PHÍA, không phải phân loại nguồn

Câu hỏi *"máy này có phải máy của hệ thống không"* không trả lời được từ pixel.
Câu trả lời được là: **số trong ảnh chỉ dùng được khi CHÍNH tài liệu nói ra con số
đó ở gần đó**. Trùng khớp ấy vừa là chứng cứ quy kết, vừa là `computed_evidence`
cho NT2.

Bốn cổng, đều thuần code (NT1) — model không tham gia bước này:

1. **Cùng loại đại lượng** — `%` chỉ khớp `%`, byte chỉ khớp byte. Suy từ hậu tố
   của `raw`, phân biệt HOA/thường: `162m` là millicore, `504M` là megabyte.
2. **Khớp giá trị CHÍNH XÁC** (`dung_sai=0` mặc định).
3. **Gần trang** — mặc định ±3.
4. **Quy kết không va chạm** — nếu cùng một giá trị khớp nhiều ô khai báo mang
   nhãn dòng KHÁC nhau thì không biết nó thuộc phân hệ nào ⇒ bỏ (NT4).

### Vì sao dung sai phải là 0, và vì sao mặc định chỉ nhận `%`

Đo trên đúng hai lượt chạy vision đã có (`eval/reports/`, 2026-09-08):

| Biến thể                                   |  PBH   |  Vtag   | khớp sai   |
|--------------------------------------------|-------:|--------:|-----------:|
| khớp giá trị, dung sai 2%, toàn tài liệu    | 22/54  | 124/228 | gần như hết|
| bốn cổng trên, chỉ `%`                      |  1/15  |  10/24  | **0**      |

Biến thể lỏng là rác: `1%` khớp `1`, `126G` (đĩa) khớp `125.48` (số bản ghi ở bảng
khác), `706` khớp `715`. Biến thể chặt cho 11 khớp và **cả 11 đều đúng nghĩa**:
`31.2` ↔ `Tải CPU 31.2%` dòng `Test`; `node4/5: 20%, 66%` ↔ dòng `Worker`;
`node1/2: 59%` ↔ dòng `Master`.

`byte` TẮT mặc định vì «GB» trong bảng khai báo không nói rõ là 10⁹ hay 2³⁰, mà
`df -h`/`du -h` thì luôn nhị phân. Đoán một trong hai là vi phạm NT4; bật bằng
`loai_nhan=` khi đã có người xác nhận quy ước.

## Số thật cho C4 đến từ đâu

Cổng chỉ nhận số tài liệu ĐÃ nói, nên tự nó không bắt được lỗi. Giá trị nằm ở
bước kế: khi một số trong ảnh neo được, **các số cùng DÒNG NGUỒN với nó** (cùng
`trich_dan` — trong ảnh console một dòng là một bản ghi) thừa hưởng quy kết đó.
Đấy mới là số bảng KHÔNG có:

    node4   1403m   20%   10393Mi   66%      ← `20%`/`66%` neo vào «Worker»
            ~~~~~         ~~~~~~~              nên `1403m` và `10393Mi` dùng được

## NT4 — ảnh không neo được thì nói ra, không đoán

Người dùng chốt 2026-09-08: làm **chặt**. Ảnh đọc được số nhưng không neo được ô
nào ⇒ một finding `khong_kiem_chung_duoc` và **không số nào** đi tiếp sang C4.
Đổi hành vi này phải hỏi lại, đừng tự nới.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from ..extraction.bang import so_dong_tieu_de
from ..ingestion.docx_reader import DocxDocument, Element
from ..normalization.numbers import parse_number
from ..reporting.finding import Finding
from .doc_anh import KetQuaDocAnh, SoDaDoc

LoaiDaiLuong = Literal["phan_tram", "byte", "milli_core", "dem"]

# Mặc định chỉ nhận phần trăm — xem bảng đo ở docstring module. Nới ra phải đo lại.
LOAI_NHAN_MAC_DINH: tuple[LoaiDaiLuong, ...] = ("phan_tram",)

GAN_TRANG_MAC_DINH = 3
DUNG_SAI_MAC_DINH = 0.0

# Bội số về BYTE. `df -h`, `du -h`, `kubectl top` đều dùng nhị phân kể cả khi chỉ
# in "G"/"M", nên không có bảng thập phân ở đây — và cũng vì thế mà phía khai báo
# ghi "GB" là ô không quy đổi được, xem docstring.
_BOI_BYTE: dict[str, int] = {
    "k": 1024, "ki": 1024, "m": 1024**2, "mi": 1024**2,
    "g": 1024**3, "gi": 1024**3, "t": 1024**4, "ti": 1024**4,
    "p": 1024**5, "pi": 1024**5,
}
# Hậu tố byte, PHÂN BIỆT HOA/THƯỜNG ở chữ cái đầu: "504M" là megabyte, "162m" là
# millicore. Ca thật: Vtag `kubectl top nodes` có cả hai trên cùng một dòng.
_HAU_TO_BYTE = re.compile(r"^\s*[\d.,]+\s*(K|Ki|M|Mi|G|Gi|T|Ti|P|Pi)B?\s*$")
_MILLI_CORE = re.compile(r"^\s*[\d.,]+\s*m\s*$")
_PHAN_TRAM = re.compile(r"^\s*([\d.,]+)\s*%\s*$")
_CHI_SO = re.compile(r"^\s*[\d.,]+\s*$")

# Ô khai báo có dấu % — bắt cả "31.2%" lẫn "57,2 %".
_O_PHAN_TRAM = re.compile(r"([\d]+(?:[.,][\d]+)?)\s*%")

# Model vision đôi khi gộp CẢ DÒNG vào `raw` thay vì một ô: `df -h` trả
# `"983G  586G  335G  63%"`. Bỏ hết những chuỗi ấy thì mất 16/18 ảnh của Vtag,
# trong đó có `63%` khớp đúng dòng «Postgres · DISK». Nhưng chỉ tách khi trong
# chuỗi có ĐÚNG MỘT dấu %: hai dấu trở lên thì không biết cái nào là cái đang
# nói tới, và NT4 bảo nói không biết chứ đừng chọn bừa.
_PHAN_TRAM_TRONG = re.compile(r"([\d]+(?:[.,][\d]+)?)\s*%")

# Nhãn dòng: bỏ ô chỉ là số thứ tự, lấy ô CHỮ đầu tiên. Bảng PBH tr.9 mở đầu bằng
# "1" rồi mới tới "Test"; bảng Vtag tr.9 mở đầu thẳng bằng "Master"/"Worker".
_CHI_LA_SO = re.compile(r"^\s*\d+([.,]\d+)?\s*$")

MAX_DAI_NHAN = 60


# ---------------------------------------------------------------------------
# Loại đại lượng
# ---------------------------------------------------------------------------
def loai_dai_luong(raw: str, don_vi: str = "") -> LoaiDaiLuong | None:
    """Đại lượng của một chuỗi đọc từ ảnh. `None` = không xếp được loại.

    Phân biệt HOA/thường là bắt buộc, không phải chi tiết làm đẹp: trên cùng một
    dòng `kubectl top nodes` có `1403m` (millicore) và `10393Mi` (mebibyte), còn
    `du -h` cho `504M` (megabyte). Gộp chúng lại là so nhầm đơn vị.
    """
    r = (raw or "").strip()
    dv = (don_vi or "").strip()
    if not r:
        return None
    if _PHAN_TRAM.match(r) or (dv == "%" and _CHI_SO.match(r)):
        return "phan_tram"
    if _MILLI_CORE.match(r):
        return "milli_core"
    if _HAU_TO_BYTE.match(r):
        return "byte"
    if _CHI_SO.match(r):
        # Đơn vị nằm ở trường riêng, không ở trong chuỗi. Ca thật: PBH `top` trả
        # raw="128010.0" với don_vi="MiB".
        if dv and _HAU_TO_BYTE.match("1" + dv.rstrip("B") + "B"):
            return "byte"
        return "dem"
    return None


def gia_tri_chuan(raw: str, don_vi: str = "") -> float | None:
    """Giá trị quy về đơn vị gốc của loại: điểm % · byte · millicore · đơn vị đếm.

    NT1: quy đổi do CODE làm, model chỉ đưa chuỗi nguyên văn.
    """
    loai = loai_dai_luong(raw, don_vi)
    if loai is None:
        return None
    r = (raw or "").strip()
    p = parse_number(r)
    if p is None:
        return None
    if loai == "byte":
        m = _HAU_TO_BYTE.match(r)
        hau_to = (m.group(1) if m else (don_vi or "").rstrip("B")).lower()
        boi = _BOI_BYTE.get(hau_to)
        return None if boi is None else p.value * boi
    return p.value


def ung_vien_gia_tri(raw: str, don_vi: str = "", *, tach_phan_tram: bool = True
                     ) -> tuple[LoaiDaiLuong, float] | None:
    """Đại lượng + giá trị của một `SoDaDoc`, kể cả khi `raw` gộp cả dòng.

    Trả `None` nghĩa là *không xếp được loại* — phải đếm chứ không im lặng bỏ.
    """
    loai = loai_dai_luong(raw, don_vi)
    if loai is not None:
        gt = gia_tri_chuan(raw, don_vi)
        return None if gt is None else (loai, gt)
    if not tach_phan_tram:
        return None
    pt = _PHAN_TRAM_TRONG.findall(raw or "")
    if len(pt) != 1:
        return None
    return ("phan_tram", float(pt[0].replace(",", ".")))


# ---------------------------------------------------------------------------
# Phía KHAI BÁO — các ô số trong bảng của tài liệu
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OKhaiBao:
    """Một giá trị tài liệu tự khai, kèm đủ thứ để neo một finding vào."""

    gia_tri: float                  # đã quy về đơn vị gốc của `loai`
    loai: LoaiDaiLuong
    raw: str                        # nguyên văn ô
    page: int | None
    location: str
    nhan_dong: str = ""             # "Worker", "Test" — quy kết phân hệ
    tieu_de_cot: str = ""
    bang_con: str = ""              # "RAM" / "DISK" — dải trong bảng xếp chồng
    bang_index: int = -1

    def mo_ta_o(self) -> str:
        """Ô này là gì, nói cho người đọc finding. Không có thì bỏ, không bịa."""
        phan = [f"dòng «{self.nhan_dong}»"] if self.nhan_dong else []
        if self.bang_con:
            phan.append(f"dải «{self.bang_con}»")
        if self.tieu_de_cot:
            phan.append(f"cột «{self.tieu_de_cot}»")
        return " · ".join(phan)


def _nhan_dong(row: list[str]) -> str:
    for c in row:
        s = (c or "").strip()
        if s and not _CHI_LA_SO.match(s):
            return s[:MAX_DAI_NHAN]
    return ""


def _tieu_de_cot(tieu_de: list[list[str]], dong: list[str], i: int) -> str:
    """Tiêu đề cột, ghép từ các tầng. Rỗng khi KHÔNG kiểm được là thẳng hàng.

    Hai cái bẫy, cả hai đã gặp thật ở lượt chạy đầu của 2.5:

    - Cắt đuôi làm mất đúng phần phân biệt được cột. Tầng dưới cùng mới là tầng
      cụ thể («% Tiêu thụ», «Cint»), tầng trên chỉ là tên chung dài dòng. Nên cắt
      ở ĐẦU.
    - Bảng có ô gộp thì dòng tiêu đề và dòng dữ liệu KHÁC số ô, nên cùng chỉ số
      `i` không trỏ cùng một cột. Bảng Vtag tr.11: tiêu đề 7 ô, dữ liệu 8 ô ⇒ ô
      «20%» bị chú thích thành cột «Số cores». Không kiểm được thẳng hàng thì
      **không nói gì về cột** — thà thiếu chứng cứ còn hơn chứng cứ sai (NT2).
    """
    if not tieu_de or any(len(r) != len(dong) for r in tieu_de):
        return ""
    phan: list[str] = []
    for r in tieu_de:
        c = (r[i] if i < len(r) else "").strip()
        if c and c not in phan:
            phan.append(c)
    s = " / ".join(phan)
    return s if len(s) <= MAX_DAI_NHAN else "…" + s[-MAX_DAI_NHAN:]


def _la_dong_du_lieu(row: list[str]) -> bool:
    return any(re.search(r"\d", c or "") for c in row)


def _bang_con(rows: list[list[str]], n_td: int, vt: int) -> tuple[str, int]:
    """Nhãn dải của bảng XẾP CHỒNG — dòng toàn ô giống nhau nằm trên dòng dữ liệu.

    Bảng định cỡ Vtag nhét ba bảng con vào một bảng Word: một dòng «RAM|RAM|…»,
    rồi tiêu đề riêng của nó, rồi dữ liệu; sau đó «DISK|DISK|…» và lặp lại. Tiêu
    đề tính một lần ở đầu bảng KHÔNG mô tả các dòng phía dưới, nên nếu chỉ có
    `tieu_de_cot` thì ô «Postgres · DISK · 63%» bị chú thích nhầm thành một cột
    CPU — chứng cứ NT2 mô tả sai chính nó, tệ hơn là không có chứng cứ.
    """
    for j in range(vt - 1, n_td - 1, -1):
        o = [(c or "").strip() for c in rows[j]]
        co = [c for c in o if c]
        if len(co) >= 2 and len(set(co)) == 1 and not _CHI_LA_SO.match(co[0]):
            return co[0][:MAX_DAI_NHAN], j
    return "", -1


def _dong_tieu_de_hieu_luc(rows: list[list[str]], n_td: int, vt: int,
                           vt_dai: int) -> list[list[str]]:
    """Các dòng thực sự làm tiêu đề cho dòng dữ liệu `vt`.

    Trong bảng xếp chồng, mỗi dải có tiêu đề riêng ngay dưới dòng nhãn dải; tiêu
    đề ở đầu bảng không còn hiệu lực. Ca thật: ô «Postgres · DISK · 63%» lấy theo
    tiêu đề đầu bảng thì thành «cột RAM».
    """
    if vt_dai >= 0:
        ra = [r for r in rows[vt_dai + 1:vt] if not _la_dong_du_lieu(r)]
        if ra:
            return ra
    return rows[:n_td]


def thu_thap_khai_bao(doc: DocxDocument) -> list[OKhaiBao]:
    """Mọi giá trị có đại lượng xác định trong mọi bảng của tài liệu.

    Chỉ lấy từ BẢNG, không lấy từ văn xuôi: bảng cho sẵn nhãn dòng và tiêu đề cột,
    tức là cho sẵn quy kết. Một con số nằm giữa câu văn thì neo được về giá trị
    nhưng không neo được về phân hệ, mà quy kết mới là thứ 2.5 cần.
    """
    ra: list[OKhaiBao] = []
    for el in doc.tables():
        rows = el.rows or []
        if not rows:
            continue
        n_td = so_dong_tieu_de(rows)
        for vt in range(n_td, len(rows)):
            r = rows[vt]
            nhan = _nhan_dong(r)
            bc, vt_dai = _bang_con(rows, n_td, vt)
            td_rows = _dong_tieu_de_hieu_luc(rows, n_td, vt, vt_dai)
            for i, c in enumerate(r):
                txt = (c or "").strip()
                if not txt:
                    continue
                td = _tieu_de_cot(td_rows, r, i)
                for m in _O_PHAN_TRAM.finditer(txt):
                    ra.append(OKhaiBao(
                        gia_tri=float(m.group(1).replace(",", ".")),
                        loai="phan_tram", raw=m.group(0), page=el.page,
                        location=el.location, nhan_dong=nhan,
                        tieu_de_cot=td, bang_con=bc, bang_index=el.index))
                if _O_PHAN_TRAM.search(txt):
                    continue        # ô % rồi thì không đọc lại thành số trần
                loai = loai_dai_luong(txt)
                if loai is None:
                    continue
                gt = gia_tri_chuan(txt)
                if gt is None:
                    continue
                ra.append(OKhaiBao(gia_tri=gt, loai=loai, raw=txt, page=el.page,
                                   location=el.location, nhan_dong=nhan,
                                   tieu_de_cot=td, bang_con=bc,
                                   bang_index=el.index))
    return ra


# ---------------------------------------------------------------------------
# Neo
# ---------------------------------------------------------------------------
@dataclass
class Neo:
    """Một số trong ảnh đã khớp một ô khai báo — hoặc thừa hưởng từ số cùng dòng."""

    so: SoDaDoc
    loai: LoaiDaiLuong
    gia_tri: float                  # đơn vị gốc của loại
    scope_key: str                  # phân hệ / máy chủ quy kết được
    o: OKhaiBao | None = None       # None ⇒ thừa hưởng theo dòng nguồn
    thua_huong_tu: str = ""         # `trich_dan` của dòng đã neo
    khoang_cach_trang: int | None = None

    @property
    def truc_tiep(self) -> bool:
        return self.o is not None

    def can_cu(self) -> str:
        """`computed_evidence` cho NT2 — vì sao số này được coi là của hệ thống."""
        if self.o is not None:
            mo_ta = self.o.mo_ta_o()
            return (f"ảnh đọc «{self.so.raw}» ({self.so.nhan}); tài liệu khai "
                    f"«{self.o.raw}» tại {self.o.location}"
                    + (f" · {mo_ta}" if mo_ta else ""))
        return (f"ảnh đọc «{self.so.raw}» ({self.so.nhan}) cùng dòng nguồn "
                f"«{self.thua_huong_tu}» với một số đã neo về «{self.scope_key}»")


@dataclass
class KetQuaNeoAnh:
    ma_anh: str
    location: str = ""
    neo: list[Neo] = field(default_factory=list)
    so_da_doc: int = 0              # số liệu ảnh đọc được
    so_khong_xep_loai: int = 0      # không suy được đại lượng
    so_ngoai_loai_nhan: int = 0     # xếp được loại nhưng loại đó đang không nhận
    so_khong_neo: int = 0           # có đại lượng nhưng không ô khai báo nào khớp
    va_cham: int = 0                # khớp nhiều nhãn dòng khác nhau ⇒ bỏ (NT4)

    @property
    def neo_duoc(self) -> bool:
        return bool(self.neo)

    @property
    def scope_keys(self) -> list[str]:
        return sorted({n.scope_key for n in self.neo})


@dataclass
class ThongKeNeo:
    anh_co_so: int = 0
    anh_neo_duoc: int = 0
    so_da_doc: int = 0
    so_xep_duoc_loai: int = 0
    neo_truc_tiep: int = 0
    neo_thua_huong: int = 0
    va_cham: int = 0
    o_khai_bao: int = 0
    khong_co_so_trang: bool = False     # C1 không suy được trang ⇒ đã tắt cổng trang

    def tom_tat(self) -> str:
        dung = self.neo_truc_tiep + self.neo_thua_huong
        return (f"{self.o_khai_bao} ô khai báo · {self.anh_co_so} ảnh có số liệu "
                f"({self.anh_neo_duoc} neo được) · {self.so_da_doc} số đọc được → "
                f"{dung} số dùng được cho C4 "
                f"({self.neo_truc_tiep} khớp trực tiếp + {self.neo_thua_huong} "
                f"thừa hưởng theo dòng) · {self.va_cham} bỏ vì quy kết va chạm"
                + (" · ⚠ tài liệu KHÔNG có số trang, đã tắt cổng gần-trang"
                   if self.khong_co_so_trang else ""))


def _khop(gt: float, gt_kb: float, dung_sai: float) -> bool:
    if gt == gt_kb:
        return True
    if dung_sai <= 0:
        return False
    return abs(gt - gt_kb) / max(abs(gt_kb), 1e-12) <= dung_sai


_HEADER_PHAN_TRAM = re.compile(r"%|tiêu\s*thụ|tải|sử\s*dụng", re.IGNORECASE)


def _o_mo_ta_ro_nhat(tang: list[OKhaiBao], loai: LoaiDaiLuong) -> OKhaiBao:
    """Trong cùng một tầng khoảng cách, chọn ô CHÚ THÍCH ĐƯỢC RÕ NHẤT.

    Không đổi quy kết (cả tầng đã cùng một `nhan_dong`), chỉ đổi ô đem ra làm
    chứng cứ. Bảng Vtag tr.11 có `20%` ở hai cột liền nhau vì ô gộp: một cột chú
    thích được là «% Tiêu thụ», cột kia rơi vào tầng «Số cores». Trỏ vào cột nói
    đúng đại lượng thì người thẩm định kiểm lại được ngay.
    """
    def diem(o: OKhaiBao) -> tuple[int, int, int]:
        khop_loai = (loai == "phan_tram"
                     and bool(_HEADER_PHAN_TRAM.search(o.tieu_de_cot)))
        return (int(khop_loai), int(bool(o.tieu_de_cot)), int(bool(o.bang_con)))

    return max(tang, key=diem)


def _trang(location: str) -> int | None:
    m = re.search(r"trang (\d+)", location or "")
    return int(m.group(1)) if m else None


def neo_mot_anh(kq: KetQuaDocAnh, khai_bao: list[OKhaiBao], *,
                loai_nhan: tuple[LoaiDaiLuong, ...] = LOAI_NHAN_MAC_DINH,
                gan_trang: int | None = GAN_TRANG_MAC_DINH,
                dung_sai: float = DUNG_SAI_MAC_DINH,
                tach_phan_tram: bool = True,
                ca_anh: bool = False) -> KetQuaNeoAnh:
    """Neo các số của MỘT ảnh vào bảng khai báo. Thuần code, không gọi model."""
    ra = KetQuaNeoAnh(ma_anh=kq.ma_anh, location=kq.location,
                      so_da_doc=len(kq.so_lieu))
    pg = _trang(kq.location)

    truc_tiep: list[Neo] = []
    for s in kq.so_lieu:
        uv = ung_vien_gia_tri(s.raw, s.don_vi, tach_phan_tram=tach_phan_tram)
        if uv is None:
            ra.so_khong_xep_loai += 1
            continue
        loai, gt = uv
        if loai not in loai_nhan:
            ra.so_ngoai_loai_nhan += 1
            continue

        ung_vien = []
        for o in khai_bao:
            if o.loai != loai or not _khop(gt, o.gia_tri, dung_sai):
                continue
            if pg is None or o.page is None:
                kc = None
                if gan_trang is not None:
                    continue
            else:
                kc = abs(o.page - pg)
                if gan_trang is not None and kc > gan_trang:
                    continue
            ung_vien.append((kc, o))
        if not ung_vien:
            ra.so_khong_neo += 1
            continue

        # Trang gần nhất THẮNG, rồi mới xét va chạm trong đúng tầng ấy. Bảng nằm
        # cùng trang với ảnh là bảng mà ảnh minh hoạ; bảng cách vài trang chỉ là
        # trùng số. Ca thật (Vtag `anh#53`, tr.11): `20%` khớp «Worker» ở tr.11
        # VÀ khớp «Tỷ lệ online» ở tr.10 — cùng con số, khác hẳn đại lượng. Xét
        # va chạm trên cả cửa sổ thì mất luôn một neo đúng; xét theo tầng gần
        # nhất thì tr.11 thắng và tr.10 không còn quyền phủ quyết.
        gan_nhat = min(kc for kc, _ in ung_vien if kc is not None) \
            if any(kc is not None for kc, _ in ung_vien) else None
        tang = [o for kc, o in ung_vien if kc == gan_nhat]

        nhan = {o.nhan_dong for o in tang if o.nhan_dong}
        if len(nhan) != 1:
            # 0 nhãn ⇒ không quy kết được về phân hệ nào; >1 ⇒ mâu thuẫn. Cả hai
            # đều là "không biết", và NT4 bảo nói không biết chứ đừng chọn bừa.
            ra.va_cham += 1
            continue
        scope = next(iter(nhan))
        truc_tiep.append(Neo(so=s, loai=loai, gia_tri=gt, scope_key=scope,
                             o=_o_mo_ta_ro_nhat(tang, loai),
                             khoang_cach_trang=gan_nhat))

    ra.neo = list(truc_tiep)

    # --- thừa hưởng theo DÒNG NGUỒN -------------------------------------
    # Trong ảnh console một `trich_dan` là một dòng, tức một bản ghi. Neo được một
    # ô trên dòng thì cả dòng thuộc về cùng một máy — đây là chỗ C4 lấy được số mà
    # bảng KHÔNG khai (`1403m`, `10393Mi`).
    theo_dong: dict[str, set[str]] = {}
    for n in truc_tiep:
        theo_dong.setdefault(n.so.trich_dan, set()).add(n.scope_key)

    # `ca_anh`: suy rộng ra TOÀN ảnh khi cả ảnh chỉ quy về một phân hệ. Đúng cho
    # `top`/`free`/`lscpu` — một ảnh một máy, mà `top` để RAM ở dòng khác dòng CPU
    # nên suy theo dòng bỏ sót `RAM total`/`RAM used` của PBH.
    #
    # ĐÃ ĐO LÀ SAI cho `kubectl top nodes`, không phải phỏng đoán. Vtag `anh#134`
    # (tr.22) chỉ neo được node4/node5 ⇒ tập phân hệ = {Worker} ⇒ điều kiện "đúng
    # một phân hệ" THOẢ, và cả ảnh bị gán «Worker» — kể cả `node1 4385Mi / 59%`
    # vốn là **Master** (chính tr.9 khai «Master · RAM · 59%»). Một ảnh nhiều máy
    # mà chỉ neo được vài máy thì suy rộng là gán sai. Vì thế MẶC ĐỊNH TẮT; bật
    # để đo, và chỉ nên bật khi `KetQuaDocAnh.lenh` xác nhận lệnh một-máy.
    ca_anh_scope = ""
    if ca_anh:
        moi = {n.scope_key for n in truc_tiep}
        if len(moi) == 1:
            ca_anh_scope = next(iter(moi))

    da_neo = {id(n.so) for n in truc_tiep}
    for s in kq.so_lieu:
        if id(s) in da_neo:
            continue
        scopes = theo_dong.get(s.trich_dan)
        if (not scopes or len(scopes) != 1) and ca_anh_scope:
            scopes = {ca_anh_scope}
        if not scopes or len(scopes) != 1:
            continue
        uv = ung_vien_gia_tri(s.raw, s.don_vi, tach_phan_tram=tach_phan_tram)
        if uv is None:
            continue
        ra.neo.append(Neo(so=s, loai=uv[0], gia_tri=uv[1],
                          scope_key=next(iter(scopes)),
                          thua_huong_tu=s.trich_dan))
    return ra


def neo_tai_lieu(doc: DocxDocument, ket_qua: list[KetQuaDocAnh], *,
                 loai_nhan: tuple[LoaiDaiLuong, ...] = LOAI_NHAN_MAC_DINH,
                 gan_trang: int | None = GAN_TRANG_MAC_DINH,
                 dung_sai: float = DUNG_SAI_MAC_DINH,
                 tach_phan_tram: bool = True,
                 ca_anh: bool = False,
                 ) -> tuple[list[KetQuaNeoAnh], ThongKeNeo]:
    """Neo toàn bộ ảnh của một tài liệu. Không cần model."""
    khai_bao = thu_thap_khai_bao(doc)
    tk = ThongKeNeo(o_khai_bao=len(khai_bao))

    # Bẫy im lặng: `read_docx` chỉ suy được số trang khi tài liệu có sẵn thông tin
    # phân trang (`page_source != "none"`). Không có trang thì cổng gần-trang không
    # bao giờ thoả và 2.5 trả về 0 neo mà KHÔNG có lỗi nào — đúng khuôn của vụ
    # thiếu Pillow và vụ thiếu `vision_model`. Tắt cổng và NÓI RA, đừng im lặng.
    if gan_trang is not None and not any(o.page is not None for o in khai_bao):
        tk.khong_co_so_trang = True
        gan_trang = None

    ra: list[KetQuaNeoAnh] = []
    for kq in ket_qua:
        if not kq.so_lieu:
            continue
        tk.anh_co_so += 1
        r = neo_mot_anh(kq, khai_bao, loai_nhan=loai_nhan,
                        gan_trang=gan_trang, dung_sai=dung_sai,
                        tach_phan_tram=tach_phan_tram, ca_anh=ca_anh)
        tk.so_da_doc += r.so_da_doc
        tk.so_xep_duoc_loai += r.so_da_doc - r.so_khong_xep_loai
        tk.va_cham += r.va_cham
        tk.neo_truc_tiep += sum(1 for n in r.neo if n.truc_tiep)
        tk.neo_thua_huong += sum(1 for n in r.neo if not n.truc_tiep)
        if r.neo_duoc:
            tk.anh_neo_duoc += 1
        ra.append(r)
    return ra, tk


# ---------------------------------------------------------------------------
# NT4 — ảnh không neo được
# ---------------------------------------------------------------------------
def thanh_finding(r: KetQuaNeoAnh, *, source_doc: str = "") -> Finding | None:
    """Ảnh đọc được số nhưng không quy kết được ⇒ nói ra, không đoán (NT4).

    Neo được thì KHÔNG sinh finding ở đây: số đã dùng được, việc kết luận đạt/trượt
    là của C4.
    """
    if r.neo_duoc or not r.so_da_doc:
        return None
    # Mọi số đọc được phải rơi vào đúng một lý do. Bộ đếm bị nuốt là mù — lượt
    # chạy đầu của 2.5 in ra ba dòng NT4 RỖNG vì các số bị loại ở nhánh
    # `loai not in loai_nhan` không được đếm ở đâu cả.
    ly = []
    if r.so_khong_neo:
        ly.append(f"{r.so_khong_neo} số không khớp giá trị nào tài liệu tự khai gần đó")
    if r.va_cham:
        ly.append(f"{r.va_cham} số khớp nhiều dòng khai báo khác nhau nên không rõ "
                  f"thuộc phân hệ nào")
    if r.so_ngoai_loai_nhan:
        ly.append(f"{r.so_ngoai_loai_nhan} số thuộc đại lượng chưa nhận đối chiếu "
                  f"(đơn vị dung lượng trong bảng không nói rõ 10⁹ hay 2³⁰)")
    if r.so_khong_xep_loai:
        ly.append(f"{r.so_khong_xep_loai} số không suy được đơn vị")
    return Finding(
        id=f"neo-so-{r.ma_anh}",
        severity="minor",
        category="khong_kiem_chung_duoc",
        location=r.location,
        finding=(f"Ảnh {r.ma_anh} đọc được {r.so_da_doc} số liệu nhưng không đối "
                 f"chiếu được với số nào trong bảng khai báo, nên chưa xác định được "
                 f"các số này thuộc phân hệ/máy chủ nào. Chúng KHÔNG được dùng để "
                 f"kiểm quy tắc."),
        computed_evidence="; ".join(ly),
        suggestion=("Bổ sung vào bảng định cỡ một dòng nêu rõ máy chủ trong ảnh và "
                    "ít nhất một chỉ số trùng với ảnh (ví dụ % tải CPU hoặc % dùng "
                    "RAM), để đối chiếu được ảnh với phân hệ tương ứng."),
        confidence="cao",
        source_doc=source_doc,
    )
