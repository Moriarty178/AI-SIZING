"""Ghép **vòng nhận xét PNX ↔ đúng phiên bản `.docx`** của một hồ sơ. THUẦN CODE.

Nợ từ 0.7 mục 5, và là thiên lệch số 6 trong danh sách hạn chế: PNX nhận xét bản
**trước khi sửa**, mà nhiều hồ sơ giữ nhiều phiên bản. Chạy Copilot trên bản đã sửa
thì lỗi đã được vá — recall **thấp giả tạo**.

## Vì sao không luật nào MỘT MÌNH đủ

Cách chọn cũ là `sorted(find_sizing_docs(...))[0]` — **theo bảng chữ cái**. Đo
trên 23 hồ sơ có nhãn, nó sai ở 2 hồ sơ, và ba luật thay thế "hiển nhiên" đều đã
thử rồi bỏ vì mỗi luật hỏng ở một hồ sơ khác:

- *"lấy bản cũ nhất theo ngày"* — hỏng ở `cap moi PNM 57012`: thư mục lẫn **tài
  liệu sizing của hệ thống KHÁC** (`PL02_Sizing_callbot inbound CSKH…`, 2024-12),
  luật này vớ đúng nó. **Tệ hơn cách cũ.**
- *"gom theo họ tên file rồi lấy bản cũ nhất"* — hỏng ở `cap moi Data Security
  VTT`: hai bản của cùng một tài liệu bị đổi tên tới mức không nhận ra nhau
  (*"Sizing tài nguyên Data Security VTT"* ↔ *"20240710_Sizing DataSec VTTv2"*),
  nên bản vòng 2 bị vứt khỏi họ.
- *"bản gần nhất TRƯỚC ngày của PNX vòng đó"* — hỏng ở `cap bo sung VTracking
  2.0.1`: một file PNX **tích luỹ nhiều vòng** nên `dcterms:modified` của nó là
  ngày vòng CUỐI; neo vòng 1 vào đó lại chọn bản muộn nhất, đúng cái sai đang
  muốn sửa.

**Nên dùng cả ba, mỗi tín hiệu làm đúng việc nó giỏi:**

| Tín hiệu | Việc | Ca thật nó cứu |
|---|---|---|
| từ khoá hệ thống trong tên thư mục | loại tài liệu của HỆ THỐNG KHÁC lạc vào thư mục | `PNM` có 2 file sizing của callbot |
| ngày PNX (làm trần) | loại bản sửa SAU vòng thẩm định cuối | `FMRA` bản `…Training_2025…` 20/11 > PNX 19/11 |
| thứ tự ngày sửa | đánh số vòng | `Data Security` 03/06 → vòng 1, 11/07 → vòng 2 |

## Ngày lấy ở đâu

`docProps/core.xml` → `dcterms:modified`, cho cả bản sizing lẫn PNX. Tên file
không tin được: `…_v1.0v3` sửa 20/11 trong khi `…_v2` sửa 24/10, và PNX `v4` sửa
20/11 trong khi `v3` sửa 22/11 — **số hiệu trong tên không theo thứ tự thời
gian**. File không đọc được ngày thì xếp CUỐI và không được chọn cho vòng 1 —
không đoán.

## Giới hạn còn lại, chưa vá ở đây

Số phiên bản giữ lại thường ÍT hơn số vòng nhận xét (Vtag: 3 bản / 4 vòng). Khi
đó vòng sau ghép vào bản cuối cùng có thật, và `canh_bao` nói rõ. Chạy đủ mọi
phiên bản cho từng vòng sẽ nhân số lời gọi model lên vài lần (~40 giây/lượt), nên
đó là việc của lượt đo đầy đủ ở 3.6, không phải mặc định.
"""
from __future__ import annotations

import pathlib
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field

from src.ingestion.filenames import find_pnx_docs, find_sizing_docs

_DC = "{http://purl.org/dc/terms/}"

# Dấu hiệu phiên bản trong tên file — bỏ đi để lộ ra "họ".
_TIEN_TO_NGAY = re.compile(r"^\d{6,8}[_\-\s]+")
_BAN_SAO = re.compile(r"^(copy[_\-\s]*(of)?|ban[_\s]sao)[_\-\s]*", re.IGNORECASE)
_HAU_TO_BAN = re.compile(
    r"([_\-\s]*(v|ver|version|phien[_\s]?ban)[_\-\s]*\d+(\.\d+)*)+$", re.IGNORECASE)
_HAU_TO_KHAC = re.compile(
    r"[_\-\s]*(final|new|update[d]?|daky|da[_\s]ky|clean|edit)[_\-\s]*\d*$",
    re.IGNORECASE)
_TACH_TU = re.compile(r"[^0-9a-zA-ZÀ-ỹ]+")

NGUONG_CUNG_HO = 0.6        # Jaccard trên tập từ; dưới mức này coi là hai tài liệu khác


@dataclass
class Ban:
    """Một bản `.docx` ứng viên của hồ sơ."""

    duong_dan: str
    ten: str
    sua_cuoi: str = ""          # ISO, "" = không đọc được (KHÔNG suy ra từ tên file)
    ho: str = ""                # tên đã bỏ dấu hiệu phiên bản

    @property
    def khoa_sap_xep(self) -> tuple[str, str]:
        # Không có ngày thì xếp cuối, để không bị chọn nhầm làm bản vòng 1.
        return (self.sua_cuoi or "9999-99-99", self.ten)


@dataclass
class KetQuaGhep:
    dossier: str
    bans: list[Ban] = field(default_factory=list)        # mốc đã chọn, theo thứ tự vòng
    bo_ngoai: list[Ban] = field(default_factory=list)    # có trong thư mục, không dùng
    theo_vong: dict[int, Ban] = field(default_factory=dict)
    canh_bao: list[str] = field(default_factory=list)
    do_tin: str = "cao"         # cao | vua | thap
    cach_ghep: str = "tu_khoa+tran_pnx"   # +tran_pnx | tu_khoa | khong_ghep_duoc

    @property
    def ban_vong1(self) -> Ban | None:
        return self.theo_vong.get(1)


# ---------------------------------------------------------------------------
def ngay_sua(duong_dan: str | pathlib.Path) -> str:
    """`dcterms:modified` của file .docx. Chuỗi rỗng khi không đọc được."""
    try:
        with zipfile.ZipFile(duong_dan) as z:
            root = ET.fromstring(z.read("docProps/core.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError):
        return ""
    node = root.find(_DC + "modified")
    return (node.text or "")[:19] if node is not None else ""


def ho_cua(ten: str) -> str:
    """Tên file bỏ hết dấu hiệu phiên bản — phần còn lại nhận dạng "cùng tài liệu"."""
    t = pathlib.Path(ten).stem
    t = _TIEN_TO_NGAY.sub("", t)
    t = _BAN_SAO.sub("", t)
    for _ in range(3):          # "…_v1.0v3" có hai lớp hậu tố
        t2 = _HAU_TO_KHAC.sub("", _HAU_TO_BAN.sub("", t))
        if t2 == t:
            break
        t = t2
    return " ".join(_TACH_TU.sub(" ", t).lower().split())


def _tu(s: str) -> set[str]:
    return {w for w in _TACH_TU.sub(" ", s.lower()).split() if len(w) > 1}


def _giong_nhau(a: str, b: str) -> float:
    ta, tb = _tu(a), _tu(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0


def gom_ho(bans: list[Ban]) -> list[list[Ban]]:
    """Gom các bản thành từng nhóm "cùng một tài liệu, khác phiên bản".

    Không so bằng `==` vì tên thật khác nhau nhiều hơn thế: *"Sizing Tài liệu
    thiết kế… vTag"* và *"10112023_Tài liệu thiết kế… vTag_v4"* là cùng một tài
    liệu nhưng khác nhau ở chữ "Sizing" đứng đầu.
    """
    nhom: list[list[Ban]] = []
    for b in bans:
        for n in nhom:
            if _giong_nhau(b.ho, n[0].ho) >= NGUONG_CUNG_HO:
                n.append(b)
                break
        else:
            nhom.append([b])
    return nhom


def _tu_ten_ho_so(dossier: str) -> set[str]:
    """Từ khoá nhận dạng hệ thống, bỏ phần thủ tục và mã số PYC trong tên thư mục."""
    bo = {"cap", "moi", "bo", "sung", "cấp", "mới", "bổ", "hệ", "thống", "he", "thong",
          "sizing", "tai", "nguyen", "tài", "nguyên"}
    return {w for w in _tu(dossier) if w not in bo and not w.isdigit()}


def _loc_theo_he_thong(bans: list[Ban], dossier: str) -> tuple[list[Ban], list[str]]:
    """Giữ các bản có tên dính từ khoá HỆ THỐNG của hồ sơ; không có thì giữ tất.

    Đã thử gom-theo-họ (Jaccard trên tên file) rồi bỏ: hai bản của cùng một tài
    liệu vẫn có thể được đổi tên tới mức không cùng họ — *"Sizing tài nguyên Data
    Security VTT"* và *"20240710_Sizing DataSec VTTv2"* chỉ chung đúng hai từ, nên
    luật gom họ vứt mất bản vòng 2. Lọc theo từ khoá hệ thống thì cả hai đều dính
    (`vtt`), mà tài liệu callbot lạc vào thư mục PNM vẫn bị loại (không có `pnm`).
    """
    tu_ho_so = _tu_ten_ho_so(dossier)
    if not tu_ho_so:
        return bans, [f"tên thư mục `{dossier}` không có từ khoá hệ thống nào dùng "
                      f"được để loại tài liệu lạ"]
    giu = [b for b in bans if _tu(b.ho) & tu_ho_so]
    if not giu:
        return bans, [f"không tên file nào khớp từ khoá hệ thống của `{dossier}` "
                      f"({', '.join(sorted(tu_ho_so))}) — giữ nguyên cả danh sách"]
    bo = [b for b in bans if b not in giu]
    cb = ([f"{len(bo)} file không mang từ khoá hệ thống của hồ sơ nên coi là tài liệu "
           f"của hệ thống khác, đã bỏ ra: "
           + ", ".join(f"`{b.ten[:44]}`" for b in bo[:3])
           + ("…" if len(bo) > 3 else "")] if bo else [])
    return giu, cb


# ---------------------------------------------------------------------------
def _loc_theo_pnx(bans: list[Ban], pnx: list[Ban]) -> tuple[list[Ban], list[str]]:
    """Bỏ các bản sửa SAU vòng thẩm định cuối — chúng không thể là bản được đọc.

    Chỉ dùng ngày PNX làm **trần**, KHÔNG dùng để đánh số vòng. Lý do đo được:
    một file PNX tích luỹ nhiều vòng, nên `dcterms:modified` của nó là ngày vòng
    CUỐI. Neo vòng 1 vào đó sẽ chọn bản muộn nhất — đúng cái sai đang muốn sửa
    (thấy ở `cap bo sung VTracking 2.0.1`: PNX vòng 1 sửa sau cả hai bản sizing).
    """
    tran = max((p.sua_cuoi for p in pnx if p.sua_cuoi), default="")
    if not tran:
        return bans, []
    giu = [b for b in bans if not b.sua_cuoi or b.sua_cuoi <= tran]
    bo = [b for b in bans if b not in giu]
    cb: list[str] = []
    if bo:
        cb.append(
            f"{len(bo)} bản sửa SAU vòng thẩm định cuối ({tran[:10]}) nên không thể là "
            f"bản được đọc, đã bỏ ra: "
            + ", ".join(f"`{b.ten[:44]}`" for b in bo[:3])
            + ("…" if len(bo) > 3 else ""))
    if not giu:
        cb.append(f"mọi bản đều sửa sau vòng thẩm định cuối ({tran[:10]}) — "
                  f"không loại được bản nào, giữ nguyên cả danh sách")
        return bans, cb
    return giu, cb


def ghep_phien_ban(thu_muc: str | pathlib.Path, *, so_vong: int = 1) -> KetQuaGhep:
    """Ghép từng vòng nhận xét với phiên bản `.docx` tương ứng của một hồ sơ.

    `so_vong` là số vòng nhận xét PNX ghi được cho hồ sơ đó (`lan_nhan_xet` lớn
    nhất). Vòng N ghép với mốc thứ N theo thứ tự thời gian; thiếu mốc thì vòng sau
    dùng chung mốc cuối cùng có thật và ghi cảnh báo.
    """
    thu_muc = pathlib.Path(thu_muc)
    kq = KetQuaGhep(dossier=thu_muc.name)
    files = find_sizing_docs(str(thu_muc))
    if not files:
        kq.do_tin, kq.cach_ghep = "thap", "khong_ghep_duoc"
        kq.canh_bao.append("không tìm thấy bản `.docx` nào")
        return kq

    tat_ca = [Ban(duong_dan=str(p), ten=p.name, sua_cuoi=ngay_sua(p), ho=ho_cua(p.name))
              for p in files]
    pnx = [Ban(duong_dan=str(p), ten=p.name, sua_cuoi=ngay_sua(p))
           for p in find_pnx_docs(str(thu_muc))]
    pnx = [p for p in pnx if p.sua_cuoi]

    # Hai tín hiệu, mỗi tín hiệu làm đúng việc nó giỏi:
    #   họ tên file  → loại tài liệu của HỆ THỐNG KHÁC lạc vào thư mục (PNM)
    #   ngày PNX     → loại bản sửa SAU vòng thẩm định cuối (FMRA, CMP, CALLBASE)
    #   thứ tự ngày  → đánh số vòng
    chon, cb = _loc_theo_he_thong(tat_ca, thu_muc.name)
    if pnx:
        kq.cach_ghep = "tu_khoa+tran_pnx"
        chon, cb2 = _loc_theo_pnx(chon, pnx)
        cb += cb2
    else:
        kq.cach_ghep = "tu_khoa"
        cb.append("thư mục không có file PNX nào — không có trần thời gian để loại "
                  "bản sửa sau thẩm định")
    kq.bans = sorted(chon, key=lambda b: b.khoa_sap_xep)
    kq.canh_bao = cb
    kq.bo_ngoai = [b for b in tat_ca if b not in kq.bans]

    if len(gom_ho(kq.bans)) > 1:
        kq.canh_bao.append(
            f"{len(gom_ho(kq.bans))} tên tài liệu khác nhau cùng được giữ lại — "
            f"nếu chúng không phải các phiên bản của MỘT tài liệu thì thứ tự vòng sai")
    cung_ngay = [b for b in kq.bans[:max(1, so_vong)]
                 if sum(1 for x in kq.bans if x.sua_cuoi[:10] == b.sua_cuoi[:10]) > 1]
    if cung_ngay:
        kq.canh_bao.append(
            f"{len(cung_ngay)} bản dùng cho các vòng có CÙNG ngày sửa "
            f"({cung_ngay[0].sua_cuoi[:10]}) — thứ tự vòng giữa chúng chỉ dựa vào tên "
            f"file, không có bằng chứng thời gian")

    khong_ngay = [b for b in kq.bans if not b.sua_cuoi]
    if khong_ngay:
        kq.canh_bao.append(
            f"{len(khong_ngay)} bản không đọc được ngày sửa, đã xếp cuối: "
            + ", ".join(f"`{b.ten}`" for b in khong_ngay))

    for vong in range(1, max(1, so_vong) + 1):
        kq.theo_vong[vong] = kq.bans[min(vong - 1, len(kq.bans) - 1)]

    if so_vong > len(kq.bans):
        kq.canh_bao.append(
            f"hồ sơ có {so_vong} vòng nhận xét nhưng chỉ ghép được {len(kq.bans)} bản — "
            f"các vòng từ {len(kq.bans) + 1} trở đi dùng chung bản cuối "
            f"`{kq.bans[-1].ten}`, nên nhãn của chúng bị chấm trên bản ĐÃ SỬA")
    if kq.canh_bao:
        kq.do_tin = "vua"
    if (so_vong > len(kq.bans) or kq.cach_ghep == "tu_khoa"
            or (len(kq.bans) > 1 and not kq.bans[0].sua_cuoi)):
        kq.do_tin = "thap"
    return kq


def so_vong_theo_ho_so(labels: list[dict]) -> dict[str, int]:
    """Số vòng nhận xét lớn nhất của từng hồ sơ, suy từ nhãn (`lan_nhan_xet`)."""
    ra: dict[str, int] = {}
    for l in labels:
        d = l["dossier"]
        ra[d] = max(ra.get(d, 1), int(l.get("lan_nhan_xet") or 1))
    return ra
