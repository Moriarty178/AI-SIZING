"""1.17 — điền hộ cột "Tham chiếu theo tài liệu sizing" của checklist thẩm định.

Với mỗi mục trong 57 mục checklist, tìm xem bản sizing nói tới nó ở **mục nào, trang
nào** — hoặc nói thẳng là **KHÔNG TÌM THẤY**.

**Không gọi LLM.** Đây là việc so khớp từ vựng giữa tên hạng mục và đề mục tài liệu, một
việc xác định; đưa cho model chỉ thêm một nguồn bịa mà không thêm thông tin. Nhờ vậy mục
này chạy được ở bất cứ đâu, không cần mạng nội bộ — và kết quả lặp lại y hệt giữa hai
lần chạy, thứ mà đường LLM không hứa được.

**Vì sao đáng làm sớm, dù C3/C4 còn dở.** Đo ngày 2026-09-04: **367/475 nhãn vàng (77%)
không cần một con số nào** — chúng là "thiếu mục", "chưa nêu sở cứ", tức đúng loại việc
Vòng 1 checklist bắt. Và rủi ro thấp hẳn so với phần định lượng: điền sai vị trí thì
người dùng sửa trong vài giây, khác hẳn một cảnh báo sai về số liệu.

**Ưu tiên độ chính xác hơn độ phủ.** Dưới ngưỡng khớp thì ghi "không tìm thấy" kèm ứng
viên gần nhất **có nhãn rõ là phỏng đoán**, chứ không âm thầm điền ứng viên đó vào cột
tham chiếu (NT4). Một cột tham chiếu điền bừa còn tệ hơn cột để trống: người thẩm định
mở đúng trang đó và không thấy gì.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from ..ingestion.docx_reader import DocxDocument
from .mau_word import MucChecklist, doc_checklist

# Từ chức năng tiếng Việt — có mặt ở mọi câu nên không phân biệt được mục nào với mục
# nào. Giữ lại chúng thì "Mô hình logic của phân hệ" khớp với bất kỳ câu nào có "của".
HU_TU = {
    "của", "và", "các", "cho", "hay", "là", "có", "được", "theo", "từ", "đến", "trong",
    "với", "về", "những", "một", "nếu", "thì", "không", "gồm", "tại", "hoặc", "khi",
    "đối", "này", "đó", "như", "thế", "nào", "phải", "cần", "sẽ", "bao", "chỉ", "ra",
    "mà", "để", "trên", "dưới", "sau", "trước", "còn", "đã", "bị", "do", "vào", "nên",
}
# Điểm khớp là **F1 của hai tập từ khoá**, không phải tỷ lệ phủ một chiều. Lý do đo
# được ngay lần chạy đầu trên BCCS3: tên hạng mục checklist là **câu mô tả tiêu chí**
# ("Mô hình logic tổng quan triển khai thực tế gồm đầy đủ các thành phần" — 13 từ khoá),
# còn đề mục tài liệu là **tên ngắn** ("Mô hình logic" — 3 từ). Đo phủ theo phía hạng mục
# thì đề mục đúng chỉ được 23% và bị loại; đo phủ theo phía tài liệu thì mọi đoạn văn dài
# đều đạt 100%. F1 đòi cả hai phía cùng khớp nên không lệch về bên nào.
NGUONG = 0.55
TOI_THIEU_TU_KHOP = 2       # khớp 1 từ là trùng hợp, không phải bằng chứng

# Đoạn ngắn không phải câu → nhiều khả năng là NHÃN MỤC người viết tự bôi đậm thay cho
# Heading style. BCCS3 chỉ có 7 đề mục thật trên 112 phần tử, còn cấu trúc con nằm cả ở
# đây ("Mô hình logic", "Thông tin đầu vào"). Bỏ qua chúng là bỏ qua phần lớn tài liệu.
DAI_NHAN_MUC = 90
# Nhiều hạng mục checklist là CÂU MÔ TẢ TIÊU CHÍ chứ không phải tên mục: *"Mô hình logic
# tổng quan triển khai thực tế gồm đầy đủ các thành phần"* — 13 từ khoá cho một mục mà
# tài liệu gọi là *"Mô hình logic"*. Tiếng Việt đặt từ chính TRƯỚC, nên vài từ đầu là
# tên của thứ cần tìm, phần đuôi là điều kiện đạt. Chấm thêm theo phần đầu và lấy điểm
# cao hơn; F1 trên cả câu vẫn giữ để không bỏ sót mục có tên dài thật.
TU_DAU_HANG_MUC = 5
# Ưu tiên chỗ neo: đề mục > nhãn mục > văn xuôi. Cột tham chiếu là để người thẩm định MỞ
# ĐÚNG CHỖ mà đọc, nên trỏ vào một đề mục hữu ích hơn trỏ vào một câu giữa đoạn.
TRONG_SO = {"đề mục": 1.0, "nhãn mục": 0.95, "ô bảng": 0.9, "văn xuôi": 0.8}

_KHONG_CHU = re.compile(r"[^\w\s]", re.UNICODE)
_TRONG_NGOAC = re.compile(r"\([^)]*\)")


def bo_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt. Có tài liệu gõ đề mục không dấu, có tài liệu gõ có dấu."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")


def tu_khoa(s: str, *, bo_ngoac: bool = False) -> set[str]:
    """Tập từ khoá của một chuỗi: bỏ hư từ, bỏ dấu câu, còn lại là từ mang nghĩa."""
    if bo_ngoac:
        # Phần trong ngoặc của hạng mục là chú thích điều kiện — "(Nếu là yêu cầu cấp
        # phát, đối với yêu cầu đánh giá thẩm định sizing thì không cần)" — không phải
        # tên của thứ cần tìm trong tài liệu.
        s = _TRONG_NGOAC.sub(" ", s)
    t = _KHONG_CHU.sub(" ", (s or "").lower()).split()
    return {w for w in t if w not in HU_TU and len(w) > 1}


@dataclass
class ViTri:
    """Kết quả định vị MỘT mục checklist."""

    muc: MucChecklist
    element_index: int | None = None
    location: str = ""
    tieu_de_khop: str = ""          # nguyên văn chỗ đã khớp — để người dùng tự kiểm
    diem: float = 0.0
    tu_khop: list[str] = field(default_factory=list)
    nguon: str = ""                 # "đề mục" | "đoạn văn" | "đề mục (không dấu)"
    phong_doan: bool = False        # dưới ngưỡng: gợi ý để soi, KHÔNG điền vào cột

    @property
    def tim_thay(self) -> bool:
        return self.element_index is not None and not self.phong_doan

    @property
    def o_tham_chieu(self) -> str:
        """Nội dung sẽ điền vào cột C."""
        return self.location if self.tim_thay else "KHÔNG TÌM THẤY"


def _f1(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    chung = len(a & b)
    return 0.0 if not chung else 2 * chung / (len(a) + len(b))


def _cham(khoa: set[str], text: str) -> tuple[float, list[str]]:
    co = tu_khoa(text)
    return _f1(khoa, co), sorted(khoa & co)


def _cham_khong_dau(khoa: set[str], text: str) -> tuple[float, list[str]]:
    kd = {bo_dau(w) for w in khoa}
    co = {bo_dau(w) for w in tu_khoa(text)}
    return _f1(kd, co), sorted(kd & co)


def tu_khoa_dau(s: str) -> set[str]:
    """Từ khoá của PHẦN ĐẦU tên hạng mục — xem `TU_DAU_HANG_MUC`."""
    s = _TRONG_NGOAC.sub(" ", s or "")
    t = [w for w in _KHONG_CHU.sub(" ", s.lower()).split()
         if w not in HU_TU and len(w) > 1]
    return set(t[:TU_DAU_HANG_MUC])


@dataclass
class Neo:
    """Một chỗ trong tài liệu có thể là câu trả lời cho một mục checklist."""

    text: str
    index: int
    location: str
    loai: str


def ung_vien_neo(doc: DocxDocument) -> list[Neo]:
    """Mọi chỗ đáng đem ra so khớp, kèm loại để cân trọng số.

    **Nhãn dòng trong bảng là nguồn không thể bỏ.** Bảng đầu của BCCS3 chính là bảng
    "Thông tin hệ thống", mỗi dòng một hạng mục checklist: *Mô tả hệ thống* · *Đầu
    mối/đơn vị phát triển* · *Cơ sở định cỡ* · *Nguyên tắc định cỡ*. Chấm cả bảng như
    một khối văn bản thì bốn nhãn ấy chìm trong hàng trăm từ nội dung và không mục nào
    khớp — đúng lỗi lần chạy đầu mắc phải (2.2, 2.3, 2.4 đều trượt).
    """
    ra: list[Neo] = []
    for e in doc.elements:
        if e.kind == "table" and e.rows:
            for hang in e.rows:
                for o in hang[:2]:             # cột đầu là nhãn; cột 2 khi cột 1 là STT
                    o = (o or "").strip()
                    if o and len(o) <= DAI_NHAN_MUC and not o.replace(".", "").isdigit():
                        ra.append(Neo(o, e.index, e.location, "ô bảng"))
        if not e.text:
            continue
        if e.kind == "heading":
            loai = "đề mục"
        elif (e.kind == "paragraph" and len(e.text) <= DAI_NHAN_MUC
                and not e.text.rstrip().endswith(".")):
            loai = "nhãn mục"
        else:
            loai = "văn xuôi"
        ra.append(Neo(e.text, e.index, e.location, loai))
    return ra


def dinh_vi_mot(doc: DocxDocument, muc: MucChecklist,
                neo: list[Neo] | None = None) -> ViTri:
    """Tìm chỗ trong tài liệu ứng với một mục checklist.

    Ưu tiên ĐỀ MỤC hơn đoạn văn: cột "Tham chiếu theo tài liệu sizing" là để người thẩm
    định mở đúng chỗ mà đọc, nên trỏ vào đề mục hữu ích hơn trỏ vào một câu lẻ. Đoạn văn
    chỉ dùng khi không đề mục nào khớp, và bị đòi ngưỡng cao hơn vì đoạn dài thì càng
    nhiều từ, càng dễ khớp bừa.
    """
    khoa = tu_khoa(muc.hang_muc, bo_ngoac=True)
    dau = tu_khoa_dau(muc.hang_muc)
    kq = ViTri(muc=muc)
    if not khoa:
        return kq

    tot: tuple[float, float, list[str], Neo, str] | None = None
    for n in neo or ung_vien_neo(doc):
        loai = n.loai
        d, khop = _cham(khoa, n.text)
        if dau != khoa:
            d2, khop2 = _cham(dau, n.text)
            if d2 > d:
                d, khop = d2, khop2
        if len(khop) < TOI_THIEU_TU_KHOP:
            # Có tài liệu gõ đề mục KHÔNG DẤU. Chỉ thử khi cách có dấu không ra gì —
            # bỏ dấu làm nhiều từ khác nghĩa trùng nhau nên dễ khớp bừa hơn.
            d, khop = _cham_khong_dau(khoa, n.text)
            loai = loai + " (không dấu)" if len(khop) >= TOI_THIEU_TU_KHOP else loai
        if len(khop) < TOI_THIEU_TU_KHOP:
            continue
        uu = d * TRONG_SO[loai.replace(" (không dấu)", "")]
        if tot is None or uu > tot[0]:
            tot = (uu, d, khop, n, loai)
    if tot is None:
        return kq

    _, d, khop, e, loai = tot
    kq.element_index, kq.location = e.index, e.location
    kq.tieu_de_khop = e.text[:120]
    kq.diem, kq.tu_khop, kq.nguon = d, khop, loai
    # Giữ cả ứng viên DƯỚI ngưỡng nhưng đánh dấu `phong_doan`: người dùng cần thấy
    # "gần khớp ở Mục IV.2" để tự quyết, còn cột tham chiếu vẫn để trống (NT4).
    kq.phong_doan = d < NGUONG
    return kq


def dinh_vi(doc: DocxDocument, mucs: list[MucChecklist] | None = None) -> list[ViTri]:
    """Định vị mọi mục CẦN ĐIỀN. Bỏ tiêu đề chương và tiêu đề khối — chúng không phải
    hạng mục để chấm, chỉ là nhãn phân nhóm trong chính checklist."""
    ds = mucs if mucs is not None else doc_checklist()
    neo = ung_vien_neo(doc)                  # dựng một lần, dùng cho cả 57 mục
    return [dinh_vi_mot(doc, m, neo) for m in ds
            if not (m.la_chuong or m.la_tieu_de_khoi or m.tt == "A")]


# --------------------------------------------------------------------- xuất --
def _thoat_md(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def bang_markdown(kq: list[ViTri], *, ten_tai_lieu: str = "") -> str:
    thay = sum(1 for v in kq if v.tim_thay)
    d = [f"# Checklist thẩm định — cột tham chiếu điền sẵn", ""]
    if ten_tai_lieu:
        d.append(f"**Tài liệu:** `{ten_tai_lieu}`")
    d += [
        f"**Định vị được {thay}/{len(kq)} mục.** Máy điền, người kiểm — cột *Căn cứ* "
        "cho biết chỗ khớp để soi lại trong vài giây.", "",
        "> Đây là công cụ **cố vấn**. Ô ghi `KHÔNG TÌM THẤY` nghĩa là máy không tìm ra "
        "chỗ nào đủ khớp, **không** có nghĩa tài liệu thiếu mục đó — có thể tài liệu đặt "
        "tên đề mục khác. Cột *Ứng viên gần nhất* là phỏng đoán, chưa đủ căn cứ để điền.",
        "",
        "| TT | Hạng mục | Tham chiếu theo tài liệu sizing | Căn cứ | Ứng viên gần nhất |",
        "|---|---|---|---|---|",
    ]
    for v in kq:
        if v.tim_thay:
            can_cu = f"khớp {v.diem:.0%} ở {v.nguon}: *{_thoat_md(v.tieu_de_khop)}*"
            gan = ""
        else:
            can_cu = ""
            gan = (f"{v.location} — *{_thoat_md(v.tieu_de_khop)}* (khớp {v.diem:.0%})"
                   if v.element_index is not None else "—")
        d.append(f"| {v.muc.tt} | {_thoat_md(v.muc.hang_muc)} | {v.o_tham_chieu} | "
                 f"{can_cu} | {gan} |")
    return "\n".join(d) + "\n"


def bang_csv(kq: list[ViTri]) -> str:
    """CSV để mở thẳng bằng Excel — checklist gốc vốn là file Excel."""
    import csv
    import io
    b = io.StringIO()
    w = csv.writer(b)
    w.writerow(["TT", "Hạng mục", "Tham chiếu theo tài liệu sizing",
                "Căn cứ khớp", "Điểm khớp", "Ứng viên gần nhất (phỏng đoán)"])
    for v in kq:
        w.writerow([v.muc.tt, v.muc.hang_muc, v.o_tham_chieu,
                    v.tieu_de_khop if v.tim_thay else "",
                    f"{v.diem:.2f}",
                    "" if v.tim_thay else (v.location or "")])
    return b.getvalue()
