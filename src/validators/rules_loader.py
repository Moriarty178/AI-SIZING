"""1.8 — Nạp và diễn giải `config/rules.yaml`.

Chỉ ĐỌC quy tắc, không đánh giá (việc đó là C4/C5). Nhiệm vụ: biến YAML thành đối
tượng có kiểu, kiểm những bất biến mà C4 dựa vào, và **báo ra** những quy tắc
không thể đánh giá được thay vì để chúng lặng lẽ trượt qua.

Điểm đáng lưu ý nhất — **bảng tra chưa số hoá**: vài quy tắc có tham số
`role: lookup` (`loai_o`, `cap_raid`, `the_he_lto`…) và bảng tra tương ứng chỉ
nằm trong `note` dạng **văn xuôi**, ví dụ STO-03 (*"NL-SAS 100 · SAS 10k 140 ·
SSD từ 5000"*) hay STO-09 (*"RAID 5 = 5 · RAID 6 = 6"*). C4 không đọc được văn
xuôi, nên các quy tắc đó **không đánh giá được**. Chép bảng vào Python sẽ vi phạm
NT3 (quy tắc là dữ liệu), nên ở đây chỉ **đánh dấu và liệt kê** để người nghiệp
vụ bổ sung mục `lookup:` vào `rules.yaml`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

DEFAULT_RULES_PATH = "config/rules.yaml"


@dataclass
class RuleInput:
    name: str
    unit: str = ""
    required: bool = True
    default: Any = None
    role: str = ""      # "lookup" = khoá tra bảng, không xuất hiện trong biểu thức

    @property
    def is_lookup_key(self) -> bool:
        return self.role == "lookup"


@dataclass
class Rule:
    id: str
    name: str
    type: str                       # quantitative | qualitative
    severity: str
    source_doc: str
    round: int = 2
    scope: str = "he_thong"
    enabled: bool = True
    applies_to_equipment: list[str] = field(default_factory=list)
    applies_to_module: list[str] = field(default_factory=list)
    checklist_ref: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    confidence_floor: str = ""
    note: str = ""
    message_template: str = ""

    # định lượng
    check: str = ""
    formula: str = ""
    compare_with: str = ""
    tolerance: float = 0.0
    inputs: list[RuleInput] = field(default_factory=list)
    applies_when: str = ""
    lookup: dict[str, dict] = field(default_factory=dict)   # chưa dùng trong rules.yaml

    # định tính
    criteria: str = ""

    raw: dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    @property
    def is_quantitative(self) -> bool:
        return self.type == "quantitative"

    @property
    def lookup_keys(self) -> list[RuleInput]:
        return [i for i in self.inputs if i.is_lookup_key]

    @property
    def lookup_keys_can_bang_tra(self) -> list[RuleInput]:
        """Khoá tra THỰC SỰ cần bảng — không tính các khoá chỉ làm cổng điều kiện.

        `role: lookup` đang gánh hai vai khác nhau trong `rules.yaml`:
        (a) khoá suy ra một HẰNG SỐ của Guideline không có trong tài liệu
            (`loai_o` -> `iops_toi_da_loai_o`) — cái này cần bảng;
        (b) cờ bật/tắt quy tắc, dùng trong `applies_when` (`co_duong_ra_public`,
            `co_kiem_thu_hieu_nang`) — chỉ là một giá trị trích từ tài liệu,
            KHÔNG cần bảng nào.
        Gộp hai vai lại sẽ chặn nhầm 8 quy tắc vốn chạy được.
        """
        aw = self.applies_when
        return [i for i in self.lookup_keys if i.name not in aw]

    @property
    def expression(self) -> str:
        return self.check or self.formula

    def khong_danh_gia_duoc(self) -> str:
        """Lý do C4 không chạy được quy tắc này, hoặc "" nếu chạy được.

        Trả về CHUỖI LÝ DO chứ không phải bool, để báo cáo nói được vì sao —
        im lặng bỏ qua một quy tắc là cách âm thầm làm hụt recall.
        """
        if not self.is_quantitative:
            return "quy tắc định tính, do C5 xử lý"
        if not self.enabled:
            return "đang tắt (`enabled: false`)"
        if not self.expression:
            return "không có `check` lẫn `formula` — là quy ước xử lý dữ liệu"
        if self.formula and not self.compare_with:
            return "có `formula` nhưng thiếu `compare_with`"
        missing = [i.name for i in self.lookup_keys_can_bang_tra if i.name not in self.lookup]
        if missing:
            return (f"cần bảng tra cho {', '.join(missing)} nhưng `rules.yaml` chưa "
                    f"số hoá (bảng đang nằm trong `note` dạng văn xuôi)")
        return ""


class RuleSet:
    def __init__(self, doc: dict):
        self.version = doc.get("version", "")
        self.globals: dict[str, Any] = dict(doc.get("globals") or {})
        self.sources = {s["key"]: s for s in (doc.get("sources") or []) if "key" in s}
        self.scopes = list(doc.get("evaluation_scopes") or [])
        self.rules: list[Rule] = [_to_rule(r) for r in (doc.get("rules") or [])]
        self._by_id = {r.id: r for r in self.rules}

        dup = len(self.rules) - len(self._by_id)
        if dup:
            raise ValueError(f"{dup} mã quy tắc bị trùng trong rules.yaml")

        # `see_also` trỏ vào mã không có thật thì báo cáo C7 sẽ gom nhầm nhóm.
        bad = sorted({s for r in self.rules for s in r.see_also if s not in self._by_id})
        if bad:
            raise ValueError(f"`see_also` trỏ tới mã không tồn tại: {', '.join(bad)}")

    # ------------------------------------------------------------------
    def __len__(self) -> int:
        return len(self.rules)

    def __getitem__(self, rule_id: str) -> Rule:
        return self._by_id[rule_id]

    def get(self, rule_id: str) -> Rule | None:
        return self._by_id.get(rule_id)

    def select(self, *, type: str | None = None, round: int | None = None,
               scope: str | None = None, enabled: bool | None = True,
               equipment: str | None = None) -> list[Rule]:
        out = self.rules
        if type is not None:
            out = [r for r in out if r.type == type]
        if round is not None:
            out = [r for r in out if r.round == round]
        if scope is not None:
            out = [r for r in out if r.scope == scope]
        if enabled is not None:
            out = [r for r in out if r.enabled is enabled]
        if equipment is not None:
            out = [r for r in out
                   if equipment in r.applies_to_equipment or "tat_ca" in r.applies_to_equipment]
        return out

    def runnable(self) -> list[Rule]:
        """Quy tắc định lượng C4 chạy được ngay."""
        return [r for r in self.rules if r.is_quantitative and not r.khong_danh_gia_duoc()]

    def blocked(self) -> list[tuple[Rule, str]]:
        """Quy tắc định lượng KHÔNG chạy được, kèm lý do — để báo cáo, không giấu."""
        out = []
        for r in self.rules:
            if not r.is_quantitative:
                continue
            why = r.khong_danh_gia_duoc()
            if why:
                out.append((r, why))
        return out


def _to_rule(d: dict) -> Rule:
    inputs = [RuleInput(name=i["name"], unit=i.get("unit", ""),
                        required=bool(i.get("required", True)),
                        default=i.get("default"), role=i.get("role", ""))
              for i in (d.get("inputs") or [])]
    return Rule(
        id=d["id"], name=d.get("name", ""), type=d.get("type", ""),
        severity=d.get("severity", "major"), source_doc=d.get("source_doc", ""),
        round=int(d.get("round", 2)), scope=d.get("scope", "he_thong"),
        enabled=bool(d.get("enabled", True)),
        applies_to_equipment=list(d.get("applies_to_equipment") or []),
        applies_to_module=list(d.get("applies_to_module") or []),
        checklist_ref=list(d.get("checklist_ref") or []),
        see_also=list(d.get("see_also") or []),
        confidence_floor=d.get("confidence_floor", ""),
        note=d.get("note", ""), message_template=d.get("message_template", ""),
        check=(d.get("check") or "").strip(),
        formula=(d.get("formula") or "").strip(),
        compare_with=d.get("compare_with", ""),
        tolerance=float(d.get("tolerance") or 0.0),
        inputs=inputs, applies_when=(d.get("applies_when") or "").strip(),
        lookup=dict(d.get("lookup") or {}),
        criteria=d.get("criteria", ""), raw=d,
    )


def load_rules(path: str = DEFAULT_RULES_PATH) -> RuleSet:
    with open(path, encoding="utf-8") as f:
        return RuleSet(yaml.safe_load(f))
