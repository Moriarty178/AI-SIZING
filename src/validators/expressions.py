"""Đánh giá biểu thức của `rules.yaml` — dùng chung cho C4 (định lượng) và C5 (định tính).

Tách ra khỏi `quantitative.py` khi làm 1.12: **21/50 quy tắc định tính cũng có
`applies_when`**. Không có nó thì bốn quy tắc `MTH` (Dạng I/II/III) cùng chạy một lúc
và sinh finding sai cho mọi bản sizing — đúng lỗi mà `applies_when` được thêm vào lược
đồ ở 0.5 để chặn. Chép đôi phần này sang C5 sẽ tạo hai bản dễ trôi khỏi nhau.

Biểu thức luôn đi qua **asteval**, không bao giờ `eval()`: quy tắc là dữ liệu người
nghiệp vụ sửa được, nên phải coi như đầu vào không tin cậy.
"""
from __future__ import annotations

import math

from asteval import Interpreter

from ..extraction.schema import ExtractedValue, SizingCore

# Hàm số học cho phép trong biểu thức. Cố ý hẹp: quy tắc chỉ cần tính toán, không cần
# đọc file hay gọi hàm hệ thống.
SAFE_FUNCS = {
    "min": min, "max": max, "abs": abs, "round": round, "pow": pow,
    "ceil": math.ceil, "floor": math.floor, "sqrt": math.sqrt, "sum": sum,
}


def danh_gia(expr: str, env: dict) -> tuple[object, str]:
    """(giá trị, lỗi). Không ném exception ra ngoài — lỗi thành finding."""
    a = Interpreter(usersyms=dict(SAFE_FUNCS), no_print=True, no_import=True,
                    no_delete=True, no_raise=True)
    for k, v in env.items():
        a.symtable[k] = v
    try:
        val = a(expr)
    except Exception as e:                # pragma: no cover - asteval nuốt phần lớn
        return None, f"{type(e).__name__}: {e}"
    if a.error:
        return None, "; ".join(str(e.get_error()[1]) for e in a.error)[:200]
    return val, ""


def thu_thap(rule, doc: SizingCore, scope_key: str, globals_: dict
             ) -> tuple[dict, list[str], list[ExtractedValue]]:
    """(môi trường biến, tên đầu vào thiếu, đầu vào lưỡng nghĩa)."""
    env: dict = dict(globals_)
    missing: list[str] = []
    ambiguous: list[ExtractedValue] = []

    for inp in rule.inputs:
        ev = doc.get(inp.name, scope_key)
        if ev is None or ev.missing:
            if inp.default is not None:
                env[inp.name] = inp.default
            elif inp.required:
                missing.append(inp.name)
            continue
        env[inp.name] = ev.value
        if ev.ambiguous:
            ambiguous.append(ev)

    if rule.compare_with:
        ev = doc.get(rule.compare_with, scope_key)
        if ev is None or ev.missing:
            missing.append(rule.compare_with)
        else:
            env[rule.compare_with] = ev.value
            if ev.ambiguous:
                ambiguous.append(ev)
    return env, missing, ambiguous
