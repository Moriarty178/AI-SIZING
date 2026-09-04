#!/usr/bin/env python
"""1.2 — Kết nối thử endpoint bằng chính LLMClient sẽ dùng thật.

Khác `probe_llm_endpoint.py` (dò năng lực bằng stdlib, chạy một lần ở 0.10):
script này kiểm rằng **client thật** trong `src/llm/client.py` hoạt động đúng —
gồm cả đường retry và việc ép schema bằng Pydantic.

Phải chạy từ máy trong mạng công ty.

    export SIZING_COPILOT_API_KEY=...
    python scripts/smoke_llm.py
"""
from __future__ import annotations

import pathlib
import sys
import time

# chạy được bằng `python scripts/smoke_llm.py` từ gốc repo mà không cần cài gói
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field

from src.llm.client import ExtractionFailed, LLMClient


class SizingTrichThu(BaseModel):
    """Bản thu nhỏ của SizingCore (1.6) — đủ để chứng minh ép schema chạy."""
    ten_he_thong: str = Field(description="Tên hệ thống")
    so_ccu: int = Field(description="Số người dùng đồng thời")
    loai_sizing: str = Field(description="cap_moi | bo_sung | nang_cap")


DOAN_THU = (
    "Hệ thống MyKid 2.0 định cỡ mới cho 3.500 người dùng đồng thời, "
    "triển khai trên 6 máy chủ ảo hoá."
)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    c = LLMClient()
    print(f"base_url = {c.cfg['base_url']}\nchat_model = {c.chat_model}\n")

    t0 = time.time()
    print("1) chat cơ bản ...", end=" ", flush=True)
    print(f"ĐẠT ({time.time()-t0:.1f}s) — {c.chat([{'role':'user','content':'Trả lời đúng một từ: OK'}])!r}")

    t0 = time.time()
    print("2) trích xuất có schema ...", end=" ", flush=True)
    try:
        out = c.extract(SizingTrichThu, [
            {"role": "system", "content": "Bạn trích thông tin định cỡ. Chỉ trả JSON."},
            {"role": "user", "content": f"Trích từ đoạn sau:\n{DOAN_THU}"},
        ])
    except ExtractionFailed as e:
        print(f"KHÔNG — {e}\n  phản hồi cuối: {e.last_raw[:200]}")
        return 1
    print(f"ĐẠT ({time.time()-t0:.1f}s) — {out.model_dump()}")

    ok = out.so_ccu == 3500 and out.loai_sizing == "cap_moi"
    print(f"3) giá trị đúng? {'ĐẠT' if ok else 'SAI — xem lại prompt/model'}")

    print("\nClient chạy được. 1.2 xong.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
