"""Chuẩn hóa đại lượng có đơn vị, theo bảng trong `config/units.yaml` (NT3).

Hai điều KHÔNG làm, cố ý:

1. **Không quy đổi vCPU ↔ Cint.** Tỷ lệ phụ thuộc đời CPU và mức overcommit, đã
   là quy tắc riêng (`CPU-03`, `CPU-09`). Đặt một hằng số ở đây sẽ lặng lẽ ghi đè
   quy tắc — vi phạm NT3.
2. **Không quy đổi CCU ↔ tổng người dùng.** Tỷ lệ đồng thời là dữ liệu đầu vào của
   từng hệ thống, phải lấy từ tài liệu chứ không giả định.

Cơ sở luỹ thừa khác nhau giữa các nhóm là có chủ đích: dung lượng dùng **1024**
(PNX bắt lỗi thật: *"Đổi từ GB ra TB phải chia 1024 chứ không phải 1000"*), băng
thông dùng **1000** theo quy ước viễn thông. Trộn hai cơ sở gây lệch ~10%, rất
khó thấy khi đọc bằng mắt.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

import yaml

from .numbers import ParsedNumber, parse_number

DEFAULT_UNITS_PATH = "config/units.yaml"


class UnknownUnit(ValueError):
    """Đơn vị không có trong bảng — báo ra, không đoán (NT4)."""


@dataclass(frozen=True)
class Quantity:
    """Một đại lượng đã chuẩn hóa về đơn vị gốc của nhóm."""

    value: float            # giá trị theo đơn vị người viết dùng
    unit: str               # đơn vị chuẩn hoá, vd "gbyte"
    group: str              # nhóm, vd "dung_luong"
    base_value: float       # giá trị quy về đơn vị gốc
    base_unit: str          # đơn vị gốc, vd "byte"
    raw: str = ""
    ambiguous: bool = False
    note: str = ""

    def to(self, unit: str, units: "Units | None" = None) -> float:
        u = units or load_units()
        return u.convert(self.base_value, self.base_unit, unit)


class Units:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.so = cfg.get("so", {})
        self._alias: dict[str, tuple[str, str]] = {}      # thường hoá -> (nhóm, đv)
        self._alias_cs: dict[str, tuple[str, str]] = {}   # giữ nguyên hoa/thường
        self._case_groups: set[str] = set()
        self._factor: dict[tuple[str, str], float] = {}

        for group, g in cfg.get("nhom", {}).items():
            base = g["don_vi_goc"]
            explicit = g.get("he_so", {})
            prefixes = g.get("tien_to")
            co_so = g.get("co_so")
            if g.get("phan_biet_hoa_thuong"):
                self._case_groups.add(group)
                for unit, names in g.get("ten_hoa_thuong", {}).items():
                    for n in names:
                        self._alias_cs[n.strip()] = (group, unit)
            for unit, names in g.get("ten", {}).items():
                for n in list(names) + [unit]:
                    self._alias[_key(n)] = (group, unit)
                if unit in explicit:
                    f = float(explicit[unit])
                elif prefixes is not None and co_so:
                    # "gbyte" -> tiền tố "g" -> co_so ** 3
                    p = unit[0] if unit != base else ""
                    if p not in prefixes:
                        p = ""
                    f = float(co_so) ** prefixes[p]
                else:
                    # KHÔNG mặc định 1.0. Đơn vị không khai hệ số là đơn vị CỐ Ý
                    # không quy đổi được (vcpu<->cint, ccu<->user): tỷ lệ phụ
                    # thuộc dữ liệu từng hệ thống và đã là quy tắc riêng. Mặc
                    # định 1.0 sẽ lặng lẽ coi 1 vCPU = 1 Cint — đúng loại lỗi im
                    # lặng mà module này sinh ra để chặn.
                    f = None
                self._factor[(group, unit)] = f
            self._factor.setdefault((group, base), 1.0)

    # ------------------------------------------------------------------
    def resolve(self, unit_text: str) -> tuple[str, str]:
        """Tên đơn vị người viết dùng -> (nhóm, đơn vị chuẩn).

        So khớp CÓ phân biệt hoa/thường trước: "KB/s" (kilobyte) và "kb/s"
        (kilobit) khác nhau đúng 8 lần, hạ về chữ thường là lặng lẽ sai 8 lần.
        """
        exact = (unit_text or "").strip()
        if exact in self._alias_cs:
            return self._alias_cs[exact]
        k = _key(unit_text)
        if k not in self._alias:
            raise UnknownUnit(f"không biết đơn vị {unit_text!r}")
        return self._alias[k]

    def is_case_ambiguous(self, unit_text: str) -> bool:
        """Đơn vị thuộc nhóm phân biệt hoa/thường nhưng viết không khớp dạng nào."""
        exact = (unit_text or "").strip()
        if exact in self._alias_cs:
            return False
        try:
            group, _ = self.resolve(unit_text)
        except UnknownUnit:
            return False
        return group in self._case_groups

    def base_unit(self, group: str) -> str:
        return self.cfg["nhom"][group]["don_vi_goc"]

    def factor(self, group: str, unit: str) -> float:
        if (group, unit) not in self._factor:
            raise UnknownUnit(f"không biết đơn vị {unit!r} trong nhóm {group!r}")
        f = self._factor[(group, unit)]
        if f is None:
            raise UnknownUnit(
                f"{unit!r} cố ý KHÔNG có hệ số quy đổi trong nhóm {group!r} — "
                f"tỷ lệ phụ thuộc dữ liệu từng hệ thống, phải lấy từ tài liệu "
                f"hoặc từ quy tắc trong rules.yaml, không giả định ở đây")
        return f

    def is_convertible(self, unit_text: str) -> bool:
        try:
            self.factor(*self.resolve(unit_text))
            return True
        except UnknownUnit:
            return False

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        gf, uf = self.resolve(from_unit)
        gt, ut = self.resolve(to_unit)
        if gf != gt:
            raise UnknownUnit(
                f"không quy đổi giữa hai nhóm khác nhau: {uf!r} ({gf}) và {ut!r} ({gt})")
        return value * self.factor(gf, uf) / self.factor(gt, ut)

    # ------------------------------------------------------------------
    def parse_quantity(self, text: str) -> Quantity | None:
        """Đọc "2,9 TB" / "35.000 KB/s" / "176GB" thành Quantity đã chuẩn hoá."""
        num = parse_number(text, style=self.so.get("kieu_mac_dinh", "vi"),
                           group_len=int(self.so.get("do_dai_nhom_nghin", 3)))
        if num is None:
            return None
        tail = text[text.find(num.raw) + len(num.raw):].strip()
        m = re.match(r"[^\w%]*([A-Za-zÀ-ỹ/][\w/À-ỹ]*(?:\s*/\s*[A-Za-zÀ-ỹ]+)?)", tail)
        if not m:
            raise UnknownUnit(f"không thấy đơn vị sau số trong {text!r}")
        unit_text = m.group(1)
        group, unit = self.resolve(unit_text)
        amb, note = num.ambiguous, num.note
        try:
            f = self.factor(group, unit)
            base_unit = self.base_unit(group)
        except UnknownUnit:
            # Đơn vị nhận ra được nhưng cố ý không quy đổi: giữ nguyên giá trị,
            # đơn vị gốc chính là nó, và nói rõ trong note thay vì bịa hệ số.
            f, base_unit = 1.0, unit
            note = (note + " | " if note else "") + (
                f"{unit!r} không quy đổi sang đơn vị gốc của nhóm {group!r} — "
                f"tỷ lệ phải lấy từ tài liệu hoặc quy tắc")
        if self.is_case_ambiguous(unit_text):
            amb = True
            note = (note + " | " if note else "") + (
                f"{unit_text!r} viết không rõ byte hay bit — chênh 8 lần; "
                f"đang hiểu là {unit!r}")
        return Quantity(
            value=num.value, unit=unit, group=group,
            base_value=num.value * f, base_unit=base_unit,
            raw=text.strip(), ambiguous=amb, note=note,
        )


def _key(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


@lru_cache(maxsize=4)
def load_units(path: str = DEFAULT_UNITS_PATH) -> Units:
    with open(path, encoding="utf-8") as f:
        return Units(yaml.safe_load(f))
