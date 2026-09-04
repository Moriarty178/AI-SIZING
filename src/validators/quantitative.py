"""C4 — kiểm quy tắc định lượng. THUẦN CODE, không gọi LLM (NT1).

Mọi phép tính, so ngưỡng, đối chiếu ở đây do Python làm. LLM chỉ có nhiệm vụ
trích con số ra khỏi tài liệu (C3); nó không bao giờ được hỏi "tính giúp" hay
"con số này có đúng không".

Biểu thức trong `rules.yaml` được đánh giá bằng **asteval**, không bao giờ bằng
`eval()` — quy tắc là dữ liệu người nghiệp vụ sửa được, nên phải coi như đầu vào
không tin cậy.

Bốn tình huống và cách xử lý, đều theo NT4 (xuống cấp có kiểm soát):

  thiếu đầu vào bắt buộc  -> finding `thieu_thong_tin`, KHÔNG lấy giá trị mặc định
  đầu vào lưỡng nghĩa     -> finding `khong_kiem_chung_duoc` (từ tầng 1.4)
  bảng tra chưa số hoá    -> finding `khong_kiem_chung_duoc`, nêu rõ thiếu bảng nào
  biểu thức lỗi           -> finding `khong_kiem_chung_duoc`, KHÔNG nuốt lỗi
"""
from __future__ import annotations

from dataclasses import dataclass

from ..extraction.schema import ExtractedValue, SizingCore
from ..reporting.finding import Finding
from .expressions import SAFE_FUNCS, danh_gia, thu_thap
from .rules_loader import Rule, RuleSet, load_rules


@dataclass
class RuleOutcome:
    """Kết quả chấm MỘT quy tắc trên MỘT lượt (một phân hệ, hoặc cả tài liệu)."""

    rule_id: str
    scope_key: str
    status: str          # dat | vi_pham | khong_ap_dung | khong_danh_gia_duoc
    finding: Finding | None = None
    detail: str = ""


class QuantitativeValidator:
    def __init__(self, rules: RuleSet | None = None):
        self.rules = rules or load_rules()

    # ------------------------------------------------------------------
    # Hai hàm dưới chỉ còn là vỏ mỏng quanh `expressions` — dùng chung với C5, vì
    # 21/50 quy tắc định tính cũng có `applies_when`.
    def _eval(self, expr: str, env: dict) -> tuple[object, str]:
        return danh_gia(expr, env)

    def _collect(self, rule: Rule, doc: SizingCore, scope_key: str
                 ) -> tuple[dict, list[str], list[ExtractedValue]]:
        return thu_thap(rule, doc, scope_key, self.rules.globals)

    def _location(self, rule: Rule, doc: SizingCore, scope_key: str) -> str:
        for inp in rule.inputs:
            ev = doc.get(inp.name, scope_key)
            if ev is not None and ev.location:
                return ev.location
        for ph in doc.phan_he:
            if ph.scope_key == scope_key and ph.location:
                return ph.location
        return ""

    def _finding(self, rule: Rule, category: str, text: str, *, doc: SizingCore,
                 scope_key: str, computed_evidence: str = "", suggestion: str = "",
                 severity: str | None = None, confidence: str = "cao") -> Finding:
        return Finding(
            id=f"{rule.id}#{scope_key or 'he_thong'}",
            severity=severity or rule.severity,           # type: ignore[arg-type]
            category=category,                            # type: ignore[arg-type]
            finding=text,
            rule_ref=rule.id,
            location=self._location(rule, doc, scope_key),
            computed_evidence=computed_evidence,
            suggestion=suggestion,
            confidence=confidence,                        # type: ignore[arg-type]
            checklist_ref=list(rule.checklist_ref),
            vong=rule.round,
            scope_key=scope_key,
            source_doc=rule.source_doc,
        )

    def _message(self, rule: Rule, env: dict, extra: dict) -> str:
        """Dựng câu tiếng Việt từ `message_template`; thiếu biến thì lùi về `name`."""
        if not rule.message_template:
            return rule.name
        try:
            return rule.message_template.format(**{**env, **extra}).strip()
        except (KeyError, IndexError, ValueError):
            return rule.name

    # ------------------------------------------------------------------
    def check_rule(self, rule: Rule, doc: SizingCore, scope_key: str = "") -> RuleOutcome:
        why = rule.khong_danh_gia_duoc()
        if why:
            # Bảng tra chưa số hoá là ca đáng báo cho người dùng: quy tắc CÓ tồn
            # tại, chỉ là chưa chạy được. Im lặng bỏ qua sẽ làm hụt recall mà
            # không ai biết vì sao.
            if "bảng tra" in why:
                f = self._finding(
                    rule, "khong_kiem_chung_duoc",
                    f"Chưa kiểm được quy tắc {rule.id} ({rule.name}): {why}.",
                    doc=doc, scope_key=scope_key,
                    suggestion="Bổ sung mục `lookup:` cho quy tắc này trong `rules.yaml`.",
                    severity="info", confidence="cao")
                return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f, why)
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None, why)

        env, missing, ambiguous = self._collect(rule, doc, scope_key)

        # --- áp dụng hay không -----------------------------------------
        if rule.applies_when:
            val, err = self._eval(rule.applies_when, env)
            if err:
                return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                                   f"lỗi `applies_when`: {err}")
            if not val:
                return RuleOutcome(rule.id, scope_key, "khong_ap_dung")

        # --- thiếu đầu vào: KHÔNG đoán ---------------------------------
        if missing:
            f = self._finding(
                rule, "thieu_thong_tin",
                f"Chưa kiểm được {rule.id} ({rule.name}) vì tài liệu thiếu: "
                f"{', '.join(missing)}.",
                doc=doc, scope_key=scope_key,
                suggestion=f"Bổ sung {', '.join(missing)} vào bản sizing.",
                severity="major", confidence="cao")
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f,
                               f"thiếu: {', '.join(missing)}")

        # --- đầu vào lưỡng nghĩa: xuống cấp, không kết luận -------------
        if ambiguous:
            names = ", ".join(a.raw or a.note[:40] for a in ambiguous)
            f = self._finding(
                rule, "khong_kiem_chung_duoc",
                f"Không kiểm chắc được {rule.id} vì số liệu đọc được có thể hiểu "
                f"theo hai cách: {names}.",
                doc=doc, scope_key=scope_key,
                computed_evidence="; ".join(a.note for a in ambiguous if a.note),
                suggestion="Ghi rõ đơn vị và dấu phân cách để không còn hiểu hai cách.",
                severity="minor", confidence="vua")
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", f,
                               "đầu vào lưỡng nghĩa")

        # --- check: bất đẳng thức --------------------------------------
        if rule.check:
            val, err = self._eval(rule.check, env)
            if err:
                return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                                   f"lỗi biểu thức `check`: {err}")
            if val:
                return RuleOutcome(rule.id, scope_key, "dat")
            shown = {i.name: env.get(i.name) for i in rule.inputs if i.name in env}
            f = self._finding(
                rule, "vuot_nguong", self._message(rule, env, {}),
                doc=doc, scope_key=scope_key,
                computed_evidence=f"`{rule.check}` sai với {shown}")
            return RuleOutcome(rule.id, scope_key, "vi_pham", f)

        # --- formula: tính lại rồi đối chiếu ----------------------------
        expected, err = self._eval(rule.formula, env)
        if err:
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                               f"lỗi biểu thức `formula`: {err}")
        declared = env.get(rule.compare_with)
        if not isinstance(expected, (int, float)) or not isinstance(declared, (int, float)):
            return RuleOutcome(rule.id, scope_key, "khong_danh_gia_duoc", None,
                               "kết quả tính lại hoặc giá trị khai không phải số")

        diff = abs(expected - declared)
        rel = diff / abs(expected) if expected else (0.0 if diff == 0 else float("inf"))
        if rel <= rule.tolerance:
            return RuleOutcome(rule.id, scope_key, "dat")

        extra = {"expected": _fmt(expected), "declared": _fmt(declared),
                 "diff_pct": f"{rel * 100:.1f}"}
        f = self._finding(
            rule, "sai_cong_thuc", self._message(rule, env, extra),
            doc=doc, scope_key=scope_key,
            computed_evidence=(f"tính lại `{rule.formula}` = {_fmt(expected)}, "
                               f"tài liệu khai {_fmt(declared)}, chênh {rel * 100:.1f}% "
                               f"(dung sai cho phép {rule.tolerance * 100:g}%)"))
        return RuleOutcome(rule.id, scope_key, "vi_pham", f)

    # ------------------------------------------------------------------
    def run(self, doc: SizingCore) -> list[RuleOutcome]:
        """Chấm mọi quy tắc định lượng, mỗi quy tắc theo đúng `scope` của nó."""
        out: list[RuleOutcome] = []
        for rule in self.rules.select(type="quantitative", enabled=True):
            try:
                keys = doc.scope_keys(rule.scope)
            except ValueError as e:
                out.append(RuleOutcome(rule.id, "", "khong_danh_gia_duoc", None, str(e)))
                continue
            for key in keys:
                out.append(self.check_rule(rule, doc, key))
        return out

    def findings(self, doc: SizingCore) -> list[Finding]:
        """Chỉ những finding có căn cứ (NT2)."""
        return [o.finding for o in self.run(doc)
                if o.finding is not None and o.finding.co_can_cu()]


def _fmt(x: float) -> str:
    return f"{x:,.4g}"
