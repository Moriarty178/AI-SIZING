#!/usr/bin/env python
"""1.2 — Kết nối thử endpoint bằng chính LLMClient sẽ dùng thật.

Khác `probe_llm_endpoint.py` (dò năng lực bằng stdlib, chạy một lần ở 0.10):
script này kiểm rằng **client thật** trong `src/llm/client.py` hoạt động đúng —
gồm cả đường retry và việc ép schema bằng Pydantic.

Phải chạy từ máy trong mạng công ty:

    set SIZING_COPILOT_API_KEY=...            # Windows:  $env:SIZING_COPILOT_API_KEY="..."
    python scripts/smoke_llm.py               # dùng chat_model trong settings.yaml
    python scripts/smoke_llm.py m1 m2 m3      # so nhiều model một lượt

**In ra một khối báo cáo dán thẳng về được** — không cần ai tổng hợp lại tay.
Khối đó KHÔNG chứa khóa API (có kiểm trước khi in).

Ba con số script này tồn tại để lấy, mà `probe_llm_endpoint.py` không lấy được:

  1. **Số lần thử trung bình của `extract()`.** Nếu gateway bỏ qua schema và lần
     nào cũng phải thử lại thì mỗi tài liệu tốn gấp 2–3 lời gọi — đổi hẳn cách
     thiết kế C3 (1.7).
  2. **Đường nào đã dùng** — `json_schema` hay lùi về prompt thuần. 0.10 cho thấy
     tham số được NHẬN nhưng BỎ QUA; nếu có gateway trả 400 thì phải biết.
  3. **Model nào trích đúng số tiếng Việt.** 0.10 để treo "chưa chốt model chính
     cho C3" vì chỉ thử 1 đoạn × 2 lần. Ở đây 2 đoạn × 2 lần × mỗi model, trong
     đó có đoạn **bẫy dấu chấm** ("12.000" là 12000 chứ không phải 12).
"""
from __future__ import annotations

import os
import pathlib
import statistics
import sys
import time
from typing import Literal

# chạy được bằng `python scripts/smoke_llm.py` từ gốc repo mà không cần cài gói
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pydantic import BaseModel, Field

from src.llm.cache import BoNhoDem
from src.llm.client import KEY_ENV, ExtractionFailed, LLMClient, LLMError


# `loai_sizing` phải là Literal, KHÔNG phải `str`. Lần chạy 2026-09-04 dùng `str` và
# kết quả vô nghĩa: `str` không sinh ràng buộc `enum` trong JSON Schema, nên model trả
# một cụm tiếng Việt tự do — đúng nghĩa, hợp lược đồ, nhưng không phải token nào cả.
# Lược đồ thật ở `src/extraction/schema.py` vốn dùng Literal, tức smoke test khi đó
# YẾU HƠN thứ nó phải kiểm, và bỏ lỡ phép thử quyết định.
#
# Ghi chú này để NGOÀI docstring có chủ ý: Pydantic đưa docstring của class vào
# `description` của JSON Schema, tức nó sẽ được gửi cho model. Nhắc lại câu trả lời
# sai của lần trước ngay trong lược đồ là tự làm nhiễm phép thử.
class SizingTrichThu(BaseModel):
    """Bản thu nhỏ của SizingCore (1.6) — đủ để chứng minh ép schema chạy."""

    ten_he_thong: str = Field(description="Tên hệ thống")
    so_ccu: int = Field(description="Số người dùng đồng thời")
    loai_sizing: Literal["cap_moi", "bo_sung", "nang_cap", "ung_cuu"] = Field(
        description="cap_moi = định cỡ mới · bo_sung = cấp thêm cho hệ đang chạy "
                    "· nang_cap = nâng cấp · ung_cuu = ứng cứu khẩn cấp")


# Hai đoạn thử. Đoạn 2 mang đúng cạm bẫy của 1.4: dấu chấm trong "12.000" là phân
# nhóm nghìn kiểu Việt. Model đọc thành 12 là lệch 1000 lần — im lặng và chết người.
DOAN_THU = [
    ("đơn giản",
     "Hệ thống MyKid 2.0 định cỡ mới cho 3.500 người dùng đồng thời, "
     "triển khai trên 6 máy chủ ảo hoá.",
     {"so_ccu": 3500, "loai_sizing": "cap_moi"}),
    ("bẫy dấu chấm",
     "Tài liệu định cỡ bổ sung tài nguyên cho hệ thống CSKH đang vận hành. "
     "Số người dùng đồng thời tăng lên 12.000, dung lượng dữ liệu 1,5 TB.",
     {"so_ccu": 12000, "loai_sizing": "bo_sung"}),
]

HE_THONG = "Bạn trích thông tin định cỡ. Chỉ trả JSON đúng lược đồ, không giải thích."
SO_LAN = 2          # mỗi đoạn chạy 2 lần để thấy model có ổn định không


def thu_mot_lan(c: LLMClient, model: str, doan: str) -> dict:
    """Một lượt trích. Không ném lỗi ra ngoài — lỗi cũng là kết quả cần báo."""
    t0 = time.time()
    try:
        out = c.extract(SizingTrichThu, [
            {"role": "system", "content": HE_THONG},
            {"role": "user", "content": f"Trích từ đoạn sau:\n{doan}"},
        ], model=model)
        return {"ok": True, "giay": time.time() - t0, "gia_tri": out.model_dump(),
                "lan_thu": c.last_attempts, "duong": c.last_schema_path}
    except ExtractionFailed as e:
        return {"ok": False, "giay": time.time() - t0, "loi": str(e),
                "tho": (e.last_raw or "")[:300], "lan_thu": c.last_attempts,
                "duong": c.last_schema_path}
    except Exception as e:                       # mạng, khóa, model không tồn tại
        return {"ok": False, "giay": time.time() - t0,
                "loi": f"{type(e).__name__}: {e}"[:300], "tho": "",
                "lan_thu": getattr(c, "last_attempts", 0),
                "duong": getattr(c, "last_schema_path", "?")}


def thu_mot_model(c: LLMClient, model: str) -> dict:
    kq: dict = {"model": model, "chat": None, "trich": []}

    print(f"\n=== {model} ===")
    print("  1) chat cơ bản ...", end=" ", flush=True)
    t0 = time.time()
    try:
        tra_loi = c.chat([{"role": "user", "content": "Trả lời đúng một từ: OK"}],
                         model=model)
        kq["chat"] = {"ok": True, "giay": time.time() - t0, "tra_loi": tra_loi[:80]}
        print(f"ĐẠT ({time.time() - t0:.1f}s) — {tra_loi[:40]!r}")
    except Exception as e:
        kq["chat"] = {"ok": False, "giay": time.time() - t0,
                      "loi": f"{type(e).__name__}: {e}"[:200]}
        print(f"KHÔNG — {type(e).__name__}: {e}")
        return kq                                 # chat hỏng thì trích cũng vô nghĩa

    for ten, doan, mong_doi in DOAN_THU:
        for lan in range(1, SO_LAN + 1):
            print(f"  2) trích «{ten}» lần {lan} ...", end=" ", flush=True)
            r = thu_mot_lan(c, model, doan)
            r["doan"] = ten
            if r["ok"]:
                sai = {k: (mong_doi[k], r["gia_tri"].get(k))
                       for k in mong_doi if r["gia_tri"].get(k) != mong_doi[k]}
                r["dung"] = not sai
                r["sai"] = sai
                print(f"{'ĐÚNG' if not sai else 'SAI ' + str(sai)} "
                      f"({r['giay']:.1f}s, {r['lan_thu']} lần thử, {r['duong']})")
            else:
                r["dung"] = False
                print(f"HỎNG — {r['loi'][:80]}")
            kq["trich"].append(r)
    return kq


def bang_bao_cao(ket_qua: list[dict], base_url: str) -> str:
    """Khối Markdown dán thẳng về được."""
    d = ["## Kết quả `scripts/smoke_llm.py`", "",
         f"- Thời điểm: {time.strftime('%Y-%m-%d %H:%M')}",
         f"- `base_url`: `{base_url}`",
         f"- Mỗi đoạn chạy {SO_LAN} lần; đoạn 2 là **bẫy dấu chấm** (12.000 ⇒ 12000)",
         f"- Lược đồ gửi đi có ràng buộc `enum` cho `loai_sizing`: "
         f"**{'có' if 'enum' in str(SizingTrichThu.model_json_schema()) else 'KHÔNG'}**",
         "",
         "> **Đọc cột «Lần thử TB»:** > 1.00 **chứng minh** gateway KHÔNG ép `enum` "
         "(nó đã sinh giá trị ngoài danh sách rồi mới bị retry sửa). = 1.00 thì "
         "KHÔNG phân biệt được «ép thật» với «model tự tuân» — nhưng về chi phí C3 "
         "là như nhau: 1 lời gọi mỗi lần trích.",
         "",
         "| Model | Chat | Trích đúng | Lần thử TB | Đường schema | Độ trễ TB |",
         "|---|---|---|---|---|---|"]

    for k in ket_qua:
        if not (k["chat"] or {}).get("ok"):
            loi = (k["chat"] or {}).get("loi", "?")
            d.append(f"| `{k['model']}` | ❌ {loi[:60]} | — | — | — | — |")
            continue
        t = k["trich"]
        dung = sum(1 for r in t if r.get("dung"))
        lan = statistics.mean([r["lan_thu"] for r in t]) if t else 0
        giay = statistics.mean([r["giay"] for r in t]) if t else 0
        duong = "/".join(sorted({r["duong"] for r in t}))
        d.append(f"| `{k['model']}` | ✅ {k['chat']['giay']:.1f}s | "
                 f"**{dung}/{len(t)}** | {lan:.2f} | {duong} | {giay:.1f}s |")

    sai = [(k["model"], r) for k in ket_qua for r in k["trich"]
           if not r.get("dung")]
    if sai:
        d += ["", "### Lượt KHÔNG đạt — chi tiết", ""]
        for m, r in sai:
            if r["ok"]:
                d.append(f"- `{m}` · đoạn «{r['doan']}» · sai trường: `{r['sai']}` "
                         f"· trả về `{r['gia_tri']}`")
            else:
                d.append(f"- `{m}` · đoạn «{r['doan']}» · **hỏng**: {r['loi']}")
                if r.get("tho"):
                    d.append(f"  - phản hồi thô: `{r['tho'][:200]}`")
    else:
        d += ["", "Mọi lượt đều trích đúng."]
    return "\n".join(d)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        # TẮT đệm (2.12): script này tồn tại để xác nhận endpoint có SỐNG và đo độ
        # trễ thật. Lấy kết quả trong đệm sẽ báo "gọi được" kèm một con số độ trễ
        # bịa — đúng loại kết luận sai mà smoke test sinh ra để chặn.
        c = LLMClient(cache=BoNhoDem(bat=False))
    except (FileNotFoundError, LLMError) as e:
        print(f"Chưa chạy được: {e}")
        return 2

    models = sys.argv[1:] or [c.chat_model]
    print(f"base_url = {c.cfg['base_url']}\nmodel thử = {', '.join(models)}")

    ket_qua = [thu_mot_model(c, m) for m in models]
    bao_cao = bang_bao_cao(ket_qua, c.cfg["base_url"])

    # Không bao giờ để khóa lọt vào thứ sẽ được chép đi nơi khác.
    key = os.environ.get(KEY_ENV, "")
    if key and key in bao_cao:
        print("DỪNG: báo cáo chứa khóa API — không in ra.")
        return 3

    # Ghi theo mốc thời gian, KHÔNG ghi đè một file cố định: lần chạy 2 đã xoá mất
    # kết quả thô của lần 1 (may là đã commit). Phần ĐÁNH GIÁ do người viết nằm ở
    # `docs/1.2-ket-qua-smoke-llm.md` — máy không được đụng vào.
    out = pathlib.Path("docs/smoke") / f"smoke-{time.strftime('%Y%m%d-%H%M')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bao_cao + "\n", encoding="utf-8")

    print("\n" + "=" * 70)
    print("CHÉP TOÀN BỘ PHẦN DƯỚI GỬI VỀ (đã lưu ở " + str(out) + ")")
    print("=" * 70 + "\n")
    print(bao_cao)

    moi_model_hong = all(not (k["chat"] or {}).get("ok") for k in ket_qua)
    return 1 if moi_model_hong else 0


if __name__ == "__main__":
    raise SystemExit(main())
