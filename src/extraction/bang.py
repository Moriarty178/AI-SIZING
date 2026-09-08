"""C3 v6 — trích số liệu bằng cách hỏi NGƯỢC: mỗi CỘT của bảng là tham số nào?

**Vì sao đảo chiều câu hỏi.** Ba vòng v3→v5 đều hỏi cùng một kiểu: *"tìm 8 tham số
này trong tài liệu"*. Mọi vòng đều thêm một cổng lọc, và mọi vòng đều đo ra cùng một
chế độ hỏng. Lượt chạy thật 2026-09-04 19:07 (v5) khép lại tranh luận bằng con số:
trong 98 giá trị model đưa ra, **66 (67%) đến từ một ô mà tham số khác cũng nhận** —
cổng "một ô một tham số" phải bỏ cả 66.

Đọc thẳng tài liệu thì thấy vì sao, và đây không phải lỗi của model. Mỗi phân hệ của
BCCS3 có đúng **hai bảng**:

    [BẢNG #93]  STT | Nội dung                    | CPU (Cint) | RAM (GB) | Ghi chú
                1   | Tài nguyên cài đặt 1 node…  | 16         | 16       |
    [BẢNG #98]  N   | CPU                         | RAM        | Storage (TB)
                1   | 64                          | 64         | 4
                4   | 16                          | 16         | 1

Tức khoảng **4 con số cho cả phân hệ**. Lược đồ cũ hỏi 8–12 tham số mỗi lượt, 98 tham
số số học ở `scope: phan_he`. Bảo một model điền 98 trường từ 4 con số thì nó rải 4 con
số đó ra — hành vi hợp lý trước một câu hỏi vô lý.

**Đảo chiều làm việc điền bừa trở thành BẤT KHẢ, không phải bị lọc sau.** Lược đồ ở đây
có **đúng một trường cho mỗi cột dữ liệu của bảng**, giá trị là tên tham số (hoặc
`khong_ro`). Bảng 3 cột sinh tối đa 3 gán ghép. Không có chỗ nào để rải thêm.

Kèm theo, ba tính chất có được miễn phí:

- **Neo tuyệt đối (NT2).** Model chỉ NÓI cột nào là tham số nào; `(bảng, dòng, cột)` do
  code định vị và code tự đọc ô. Không còn khâu "tìm lại câu model trích" — khâu đã làm
  rơi 73/94 lượt ở v5.
- **Code ra số (NT1).** Ô đọc được đưa thẳng qua `parse_number` + quy đổi đơn vị của 1.4,
  y như trước.
- **Rẻ hơn nhiều.** BCCS3: 21 bảng thay cho 94 lượt gọi tham số.

Cột nào KHÔNG phải cột dữ liệu thì không bao giờ được hỏi tới: `cot_du_lieu` chỉ giữ cột
mà mọi ô dữ liệu đều trông như một con số. Điều đó một mình đã loại cột «Nội dung» và
«Ghi chú» — hai nguồn giả đã lọt qua v5 (`he_so_sai_so_khai = 1.1` lấy từ cột «Nội dung»).
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, create_model

from ..ingestion.docx_reader import DocxDocument, Element
from ..validators.rules_loader import RuleSet
from .plan import ThamSo, tham_so_cua_bo_quy_tac
from .schema import SizingCore, SizingExtension

KHONG_RO = "khong_ro"

# Ô "trông như một con số": vài chữ số, có thể kèm dấu phân cách và một đơn vị ngắn.
# Cố ý CHẶT: mục đích là loại cột văn xuôi, mà văn xuôi tiếng Việt luôn dài hơn thế.
_O_SO = re.compile(r"[\s\d.,]{1,12}[%A-Za-zÀ-ỹ/()\s]{0,10}")

MAX_MAU_MOI_COT = 4         # số ô ví dụ gửi kèm mỗi cột


# Cột số thứ tự: KHÔNG BAO GIỜ là tham số, nhưng vẫn lọt qua `la_o_so` vì toàn số.
# Đo ở lượt B1 2026-09-07: 25/91 cột số (27%) là cột này, và chúng chiếm 42% trong
# tổng số lần model trả `khong_ro`. Prompt vốn đã dặn model bỏ chúng và model làm
# ĐÚNG — nhưng mỗi cột như vậy vẫn tốn một trường lược đồ và một phần token, lại
# làm loãng chỗ model cần chú ý. Việc code quyết được thì không đem hỏi model (NT1).
# Khớp CẢ tiêu đề, không khớp một phần: «TT» là số thứ tự, «TT máy chủ» thì không.
_COT_SO_THU_TU = re.compile(
    r"^\s*(stt|tt|s[ốo]\s*(tt|th[ứu]\s*t[ựu])|#|no\.?|num(ber)?|index)\s*\.?\s*$",
    re.IGNORECASE)


def la_o_so(s: str) -> bool:
    s = (s or "").strip()
    return bool(s) and any(c.isdigit() for c in s) and bool(_O_SO.fullmatch(s))


MAX_DONG_TIEU_DE = 3        # trần an toàn: bảng toàn chữ không được nuốt hết thành tiêu đề


def so_dong_tieu_de(rows: list[list[str]]) -> int:
    """Số dòng đầu bảng là TIÊU ĐỀ — dòng chưa có ô nào trông như số liệu.

    Bảng định cỡ thật hay có tiêu đề hai tầng, tầng trên là ô gộp ngang:

        |    | CPU Intel(R) Xeon(R) Gold …            | Ghi chú |
        |    | Số cores | % Tiêu thụ | Cint           |         |
        | Worker | Tổng |    8       |   20%  |  25.1 |         |

    Coi mỗi bảng chỉ có MỘT dòng tiêu đề thì tầng hai bị tính là dữ liệu, mà nó toàn
    chữ nên `cot_du_lieu` loại sạch cột. Trên bản Vtag đó là gần như toàn bộ bảng chứa
    số cores / RAM / % tiêu thụ của từng module — 9 bảng, đúng chỗ số liệu nằm.

    Luôn trả ít nhất 1: bảng mà dòng đầu đã có số thì giữ nguyên hành vi cũ.
    """
    n = 0
    for r in rows[:MAX_DONG_TIEU_DE]:
        if any(la_o_so(c) for c in r if (c or "").strip()):
            break
        n += 1
    return max(1, min(n, len(rows) - 1)) if len(rows) > 1 else 1


MAX_DAI_TIEU_DE = 80        # tiêu đề ghép dài quá thì làm loãng phần model cần đọc


def _tang(rows: list[list[str]], n_td: int, i: int, bo: int) -> str:
    """Ghép các tầng tiêu đề của cột `i`, bỏ `bo` tầng trên cùng, khử phần lặp."""
    phan: list[str] = []
    for r in rows[bo:n_td]:
        c = (r[i] if i < len(r) else "").strip()
        if c and c not in phan:
            phan.append(c)
    return " / ".join(phan)


def so_tang_bo(rows: list[list[str]], n_td: int, rong: int) -> int:
    """Bỏ bao nhiêu tầng tiêu đề TRÊN CÙNG để mọi nhãn của bảng đủ ngắn.

    Quyết định theo CẢ BẢNG, không theo từng cột: cắt riêng lẻ thì cùng một bảng có
    cột mang tiền tố dài, cột thì không — model nhận một bộ nhãn không nhất quán và
    người đọc báo cáo cũng vậy.

    Tầng dưới cùng mô tả cột chính xác hơn tầng trên, nên khi phải bỏ thì bỏ từ trên:
    ở bảng #55 bản Vtag tầng trên là tên con CPU dài 71 ký tự lặp trên mọi cột — bỏ đi
    còn «Số cores» / «% Tiêu thụ» / «Cint». Nhưng tầng trên KHÔNG phải lúc nào cũng là
    rác: ở bảng #56 nó là «RAM», mà thiếu nó thì «% Tiêu thụ» không rõ của CPU hay RAM
    — nên chỉ bỏ khi thật sự quá dài, không bỏ vì nó lặp lại.
    """
    for bo in range(n_td):
        if all(len(_tang(rows, n_td, i, bo)) <= MAX_DAI_TIEU_DE for i in range(rong)):
            return bo
    return n_td - 1


def tieu_de_cot(rows: list[list[str]], n_td: int, i: int,
                bo_tang: int | None = None) -> str:
    """Tiêu đề cột `i`. `bo_tang` mặc định tính theo cả bảng (xem `so_tang_bo`)."""
    if bo_tang is None:
        bo_tang = so_tang_bo(rows, n_td, max((len(r) for r in rows), default=0))
    return _tang(rows, n_td, i, bo_tang)[:MAX_DAI_TIEU_DE].strip()


def cot_du_lieu(e: Element) -> list[tuple[int, str]]:
    """`(chỉ số cột, tiêu đề)` của các cột CHỨA SỐ LIỆU.

    Điều kiện: có tiêu đề, KHÔNG phải cột số thứ tự, có ít nhất một ô số, và **không
    ô dữ liệu nào là văn xuôi**.
    Một cột lẫn văn xuôi thì con số trong đó là con số nằm trong câu, không phải một
    trường dữ liệu — gán nó cho tham số là đúng loại lỗi v5 mắc phải.
    """
    if not e.rows or len(e.rows) < 2:
        return []
    n_td = so_dong_tieu_de(e.rows)
    rong = max(len(r) for r in e.rows)
    bo = so_tang_bo(e.rows, n_td, rong)
    ra: list[tuple[int, str]] = []
    da_co: set[str] = set()
    for i in range(rong):
        td = tieu_de_cot(e.rows, n_td, i, bo)
        if not td or _COT_SO_THU_TU.match(td):
            continue
        # Hai cột TRÙNG TIÊU ĐỀ thì không mô tả tách bạch được cho model, mà hỏi cả
        # hai lại mời gọi chúng nhận cùng một tham số — và khi ấy `cot_trung_tham_so`
        # bỏ CẢ HAI, mất luôn cột đúng. Giữ cột đầu là kết cục tốt hơn hẳn.
        #
        # Sinh ra từ ô gộp lệch của chính tài liệu: ở bảng #55 bản Vtag, ô «20%» của
        # dòng dữ liệu vắt qua ranh giới giữa «Số cores» và «% Tiêu thụ», nên cột 3
        # mang nhãn «Số cores» nhưng chứa 20%. Cột 2 («Số cores» → 8) mới là cột thật.
        if td in da_co:
            continue
        o = [(h[i] if i < len(h) else "") for h in e.rows[n_td:]]
        co_chu = [x for x in o if (x or "").strip()]
        if not co_chu or not all(la_o_so(x) for x in co_chu):
            continue
        da_co.add(td)
        ra.append((i, td))
    return ra


def nhan_dong(e: Element) -> list[str]:
    """Nhãn của từng dòng dữ liệu — ô đầu tiên, dùng để model chỉ đúng dòng."""
    if not e.rows:
        return []
    return [(h[0] if h else "").strip() for h in e.rows[so_dong_tieu_de(e.rows):]]


# ------------------------------------------------------------------ lược đồ --
def luoc_do_bang(e: Element, cot: list[tuple[int, str]], ung_vien: list[ThamSo],
                 chon_dong: bool) -> type[BaseModel]:
    """Một trường cho mỗi CỘT. Đây là chỗ chặn điền bừa về mặt cấu trúc."""
    opts = tuple(t.name for t in ung_vien) + (KHONG_RO,)
    truong: dict = {}
    if chon_dong:
        nhan = nhan_dong(e)
        truong["dong"] = (str, Field(description=(
            "Bảng có nhiều dòng dữ liệu. Chép NGUYÊN VĂN ô đầu tiên của dòng chứa số "
            "liệu cần lấy, chọn đúng một trong: "
            + " / ".join(f"«{x}»" for x in nhan if x))))
    for i, td in cot:
        mau = [(h[i] if i < len(h) else "").strip()
               for h in e.rows[so_dong_tieu_de(e.rows):]]
        mau = [x for x in mau if x][:MAX_MAU_MOI_COT]
        truong[f"cot_{i}"] = (Literal[opts], Field(  # type: ignore[valid-type]
            description=(f"Cột «{td}» (các ô: {', '.join(mau)}) chứa tham số nào? "
                         f"Chọn {KHONG_RO} nếu không tham số nào đúng NGHĨA của cột "
                         f"này — cột số thứ tự, số hiệu dòng đều là {KHONG_RO}.")))
    return create_model(f"GanBang{e.index}", **truong)


def chu_giai(ung_vien: list[ThamSo]) -> str:
    """Bảng nghĩa của các tham số ứng viên, gửi kèm lời nhắc."""
    dong = []
    for t in ung_vien:
        dv = f" [{t.unit}]" if t.unit else ""
        mt = f" — {t.mo_ta}" if t.mo_ta else ""
        dong.append(f"- {t.name}{dv}{mt}")
    return "\n".join(dong)


# ------------------------------------------------------------- ứng viên -----
def tham_so_so(rules: RuleSet | None = None, *, scope: str,
               chi_nhom: list[str] | None = None) -> list[ThamSo]:
    """Tham số KIỂU SỐ của một phạm vi — tập ứng viên cho một cột."""
    ra = []
    for t in tham_so_cua_bo_quy_tac(rules).values():
        if t.kieu != "so" or t.scope != scope:
            continue
        ma = t.rule_ids[0].split("-")[0] if t.rule_ids else "KHAC"
        if chi_nhom and ma not in chi_nhom:
            continue
        ra.append(t)
    ra.sort(key=lambda t: t.name)
    return ra


# ------------------------------------------------------------ phân vùng -----
def _muc_goc(s: str) -> str:
    return (s or "").split(".")[0].strip().upper()


def phan_vung_bang(doc: DocxDocument, core: SizingCore
                   ) -> list[tuple[Element, SizingExtension | None, tuple[int, int] | None]]:
    """Gán mỗi bảng cho phân hệ chứa nó; không phân hệ nào chứa thì thuộc cấp hệ thống.

    Chặn theo CẢ khoảng phần tử lẫn mục gốc. Chỉ theo khoảng là không đủ: phân hệ cuối
    (Firewall, phần tử #105) sẽ nuốt luôn bảng tổng hợp thiết bị #111 nằm ở Mục IV —
    một bảng của cả hệ thống, không của riêng nó.
    """
    het = (max(e.index for e in doc.elements) + 1) if doc.elements else 0
    # `key=` chứ không sắp thẳng tuple: hai phân hệ CÓ THỂ trùng `element_index`
    # (được nhắc trong cùng một phần tử), và khi đó sắp tuple sẽ rơi xuống so sánh
    # chính `SizingExtension` — một model không có thứ tự — nên nổ `TypeError` và
    # làm hỏng cả hồ sơ. Gặp thật ở lượt B1 2026-09-07: bản Vtag chết ở đây, 38/160
    # nhãn bị tính trượt oan. Sắp ổn định nên phân hệ trùng chỉ số giữ nguyên thứ
    # tự xuất hiện trong tài liệu.
    moc = sorted(((p.element_index, p) for p in core.phan_he
                  if p.element_index is not None), key=lambda t: t[0])
    ra = []
    for e in doc.elements:
        if e.kind != "table" or not e.rows:
            continue
        chu: SizingExtension | None = None
        kh: tuple[int, int] | None = None
        for k, (idx, p) in enumerate(moc):
            # Mốc kết là chỉ số LỚN HƠN HẲN kế tiếp. Lấy `moc[k+1][0]` thì phân hệ
            # đầu của một cặp trùng chỉ số nhận khoảng rỗng `(idx, idx)` và im lặng
            # không nhận bảng nào.
            ket = next((j for j, _ in moc[k + 1:] if j > idx), het)
            if idx <= e.index < ket and _muc_goc(e.section) == _muc_goc(p.muc):
                chu, kh = p, (idx, ket)
                break
        ra.append((e, chu, kh))
    return ra
