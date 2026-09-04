"""1.7 — Suy KẾ HOẠCH TRÍCH XUẤT từ `rules.yaml`. Không hard-code tham số nào.

NT3 nói quy tắc là dữ liệu: thêm một quy tắc lẽ ra chỉ phải sửa `rules.yaml`. Nếu C3
mang sẵn danh sách trường phải trích trong Python thì mỗi quy tắc mới lại kéo theo một
lần sửa code — đúng thứ NT3 cấm. Nên danh sách 237 tham số ở đây được **đọc ra** từ
`inputs` và `compare_with` của bộ quy tắc.

**`unit` trong `rules.yaml` đang gánh hai vai**, phát hiện khi khảo sát để làm 1.7:

  - đơn vị đo thật:      `GB` · `IOPS` · `%` · `core` · `máy` · `points` · `hệ số`
  - **kiểu dữ liệu**:    `đúng/sai` (34 tham số — boolean)
                         `nl_sas_sata_7k2 | sas_10k | sas_fc_15k | ssd` (enum)

Không tách hai vai này thì C3 sẽ hỏi model "IOPS của `co_duong_ra_public` là bao nhiêu",
một câu vô nghĩa. Tách ra ở đây, ngay tại chỗ đọc dữ liệu, chứ không rải `if` khắp nơi.

Mô tả tham số cho model cũng **lấy từ dữ liệu**: ghép `name` của các quy tắc dùng tham
số đó. Tự nghĩ mô tả là đưa tri thức nghiệp vụ vào code — cũng là vi phạm NT3, và mô tả
sẽ trôi khỏi quy tắc khi quy tắc đổi.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..validators.rules_loader import RuleSet, load_rules

# Số trường tối đa trong MỘT lời gọi. Nhóm `STO` có 55 tham số — nhét cả vào một lược
# đồ vừa làm model loãng chú ý vừa khiến một lỗi validate huỷ cả 55 trường.
# Giảm 18 -> 12 sau lượt chạy 2026-09-04 18:37, rồi 12 -> 8 sau lượt 18:51: vẫn hỏng
# 7/53 lượt vì hết ngân sách token đầu ra, kể cả lượt chỉ 12 trường. Nhóm nhỏ tốn thêm
# token nền nhưng chạy song song nên không đội thời gian, và một lượt hỏng chỉ mất 8
# trường thay vì 18.
MAX_TRUONG_MOI_LUOT = 8

KIEU_BOOL = "đúng/sai"


@dataclass
class ThamSo:
    """Một tham số quy tắc cần lấy từ tài liệu."""

    name: str
    kieu: str                       # so | bool | enum
    unit: str = ""                  # chỉ có nghĩa khi kieu == "so"
    options: list[str] = field(default_factory=list)   # chỉ khi kieu == "enum"
    scope: str = "he_thong"
    rule_ids: list[str] = field(default_factory=list)
    la_khoa_tra_bang: bool = False

    @property
    def mo_ta(self) -> str:
        """Câu mô tả cho model — ghép từ tên quy tắc, không tự nghĩ."""
        return " · ".join(self.ten_quy_tac[:2])

    ten_quy_tac: list[str] = field(default_factory=list)


@dataclass
class NhomTrich:
    """Một lượt gọi model: các tham số cùng nhóm quy tắc và cùng phạm vi."""

    ma_nhom: str                    # CPU | STO | ARC …
    scope: str
    tham_so: list[ThamSo]
    phan: int = 1                   # nhóm to bị cắt làm nhiều phần
    tong_phan: int = 1

    @property
    def ten(self) -> str:
        p = f" phần {self.phan}/{self.tong_phan}" if self.tong_phan > 1 else ""
        return f"{self.ma_nhom}/{self.scope}{p}"


def _kieu_va_options(unit: str) -> tuple[str, str, list[str]]:
    """(kiểu, đơn vị, danh sách giá trị) suy từ trường `unit` của `rules.yaml`."""
    u = (unit or "").strip()
    if u == KIEU_BOOL:
        return "bool", "", []
    if "|" in u:
        opts = [o.strip() for o in u.split("|") if o.strip()]
        return "enum", "", opts
    return "so", u, []


def tham_so_cua_bo_quy_tac(rules: RuleSet | None = None) -> dict[str, ThamSo]:
    """Mọi tham số mà bộ quy tắc cần, kèm kiểu và phạm vi."""
    rs = rules or load_rules()
    out: dict[str, ThamSo] = {}

    def them(name: str, unit: str, rule, is_lookup: bool = False) -> None:
        kieu, u, opts = _kieu_va_options(unit)
        t = out.get(name)
        if t is None:
            t = ThamSo(name=name, kieu=kieu, unit=u, options=opts, scope=rule.scope)
            out[name] = t
        # Một tham số có thể xuất hiện ở nhiều quy tắc. Giữ khai báo GIÀU thông tin
        # nhất: enum/bool cụ thể hơn "so", đơn vị có còn hơn không.
        if t.kieu == "so" and kieu in ("bool", "enum"):
            t.kieu, t.options, t.unit = kieu, opts, ""
        if t.kieu == "so" and not t.unit and u:
            t.unit = u
        t.rule_ids.append(rule.id)
        if rule.name and rule.name not in t.ten_quy_tac:
            t.ten_quy_tac.append(rule.name)
        t.la_khoa_tra_bang = t.la_khoa_tra_bang or is_lookup

    for r in rs.rules:
        for i in r.inputs:
            them(i.name, i.unit, r, i.is_lookup_key)
        if r.compare_with:
            # `compare_with` là giá trị NGƯỜI VIẾT KHAI, C4 so nó với kết quả tính lại.
            # Không trích nó thì mọi quy tắc dạng `formula` đều không chấm được.
            them(r.compare_with, "", r)
    return out


def ke_hoach_trich(rules: RuleSet | None = None, *, scope: str | None = None,
                   chi_nhom: list[str] | None = None,
                   max_truong: int = MAX_TRUONG_MOI_LUOT) -> list[NhomTrich]:
    """Chia tham số thành các lượt gọi model.

    Gom theo **nhóm quy tắc đầu tiên dùng tham số** (`CPU-03` → nhóm `CPU`): tham số
    cùng nhóm thường nằm cùng một mục của tài liệu, nên một lượt gọi đọc một vùng văn
    bản — rẻ hơn và ít nhầm hơn là hỏi rải rác.
    """
    ts = tham_so_cua_bo_quy_tac(rules)
    theo_nhom: dict[tuple[str, str], list[ThamSo]] = {}
    for t in ts.values():
        if scope is not None and t.scope != scope:
            continue
        ma = t.rule_ids[0].split("-")[0] if t.rule_ids else "KHAC"
        if chi_nhom and ma not in chi_nhom:
            continue
        theo_nhom.setdefault((ma, t.scope), []).append(t)

    ra: list[NhomTrich] = []
    for (ma, sc), ds in sorted(theo_nhom.items()):
        ds.sort(key=lambda t: t.name)
        phans = [ds[i:i + max_truong] for i in range(0, len(ds), max_truong)]
        for k, phan in enumerate(phans, 1):
            ra.append(NhomTrich(ma_nhom=ma, scope=sc, tham_so=phan,
                                phan=k, tong_phan=len(phans)))
    return ra
