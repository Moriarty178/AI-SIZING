#!/usr/bin/env python
"""0.10 — Probe the company's OpenAI-compatible (vLLM) endpoint for what the plan needs.

Standard library only (urllib + json; pyyaml for settings) so it runs before the
project environment (1.1, `uv`) exists. Nine independent checks; none aborts the
run. The result is a table — ĐẠT / KHÔNG / LỖI — plus a Markdown report, with the
API key never written anywhere.

What each check decides
-----------------------
  A  /v1/models            → which models exist (vision? embedding?), max_model_len
  B  chat                  → endpoint alive, key valid
  C  response_format json_schema   → structured output, OpenAI-style
  D  extra_body guided_json        → structured output, vLLM-style
  E  prompt-only JSON + validate   → fallback path for 1.7 if C and D both fail
  F  embeddings            → RAG (C5/C6) can use the cluster, or needs local BGE-M3
  G  vision                → C2 can use a vision model, or degrades to OCR-only
  H  context window        → how sizing documents must be chunked in C1
  I  rate limit            → whether a queue (3.2) is needed early

Usage
-----
    export SIZING_COPILOT_API_KEY=...
    python scripts/probe_llm_endpoint.py [--settings config/settings.yaml]
                                         [-o docs/0.10-ket-qua-xac-minh-endpoint.md]
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

import yaml

KEY_ENV = "SIZING_COPILOT_API_KEY"

# Small schema standing in for the real SizingCore (1.6): three fields, one nested,
# one enum — enough to prove the server actually constrains output, not merely
# that the model happened to answer in JSON.
SCHEMA = {
    "type": "object",
    "properties": {
        "ten_he_thong": {"type": "string"},
        "so_ccu": {"type": "integer"},
        "loai_sizing": {"type": "string", "enum": ["cap_moi", "bo_sung", "nang_cap"]},
    },
    "required": ["ten_he_thong", "so_ccu", "loai_sizing"],
    "additionalProperties": False,
}
EXTRACT_PROMPT = (
    "Trích thông tin từ đoạn sau và trả về đúng JSON theo lược đồ, không thêm chữ nào khác.\n"
    "Đoạn: 'Hệ thống MyKid 2.0 định cỡ mới cho 3.500 người dùng đồng thời.'\n"
    f"Lược đồ JSON: {json.dumps(SCHEMA, ensure_ascii=False)}"
)
# 1x1 PNG, red pixel — enough to prove the endpoint accepts image input at all.
TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)


class Endpoint:
    def __init__(self, base_url: str, key: str, timeout: int):
        self.base = base_url.rstrip("/")
        self.key = key
        self.timeout = timeout

    def _req(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict | str]:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.key}")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode("utf-8")
                try:
                    return r.status, json.loads(raw)
                except json.JSONDecodeError:
                    return r.status, raw
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                return e.code, json.loads(raw)
            except json.JSONDecodeError:
                return e.code, raw
        except Exception as e:  # DNS, TLS, timeout — report, never raise
            return -1, f"{type(e).__name__}: {e}"

    def chat(self, model: str, messages: list, **extra) -> tuple[int, dict | str]:
        body = {"model": model, "messages": messages, "temperature": 0.1, "max_tokens": 200}
        body.update(extra)
        return self._req("POST", "/chat/completions", body)


def content_of(resp) -> str:
    try:
        return resp["choices"][0]["message"]["content"] or ""
    except Exception:
        return ""


def validate(obj) -> str:
    """Manual check against SCHEMA (no pydantic in this environment). '' = valid."""
    if not isinstance(obj, dict):
        return "không phải object"
    for k in SCHEMA["required"]:
        if k not in obj:
            return f"thiếu trường {k}"
    if not isinstance(obj["ten_he_thong"], str):
        return "ten_he_thong không phải string"
    if not isinstance(obj["so_ccu"], int) or isinstance(obj["so_ccu"], bool):
        return "so_ccu không phải integer"
    if obj["loai_sizing"] not in SCHEMA["properties"]["loai_sizing"]["enum"]:
        return f"loai_sizing ngoài enum: {obj['loai_sizing']!r}"
    extra = set(obj) - set(SCHEMA["properties"])
    if extra:
        return f"trường thừa: {sorted(extra)}"
    return ""


def parse_json_loose(text: str):
    """Model output may wrap JSON in ``` fences or prose; take the outermost {...}."""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        if t.lower().startswith("json"):
            t = t[4:]
    s, e = t.find("{"), t.rfind("}")
    if s == -1 or e == -1:
        raise ValueError("không thấy JSON")
    return json.loads(t[s:e + 1])


def err_text(resp) -> str:
    if isinstance(resp, dict):
        m = resp.get("error") or resp.get("message") or resp
        return json.dumps(m, ensure_ascii=False)[:300]
    return str(resp)[:300]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--settings", default="config/settings.yaml")
    ap.add_argument("-o", "--out", default="docs/0.10-ket-qua-xac-minh-endpoint.md")
    ap.add_argument("--skip-rate", action="store_true", help="bỏ phép thử I (10 lời gọi)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if not os.path.exists(args.settings):
        print(f"Chưa có {args.settings} — copy từ config/settings.example.yaml rồi điền.")
        return 1
    cfg = yaml.safe_load(open(args.settings, encoding="utf-8"))["llm"]
    key = os.environ.get(KEY_ENV, "")
    if not key:
        print(f"Chưa đặt biến môi trường {KEY_ENV}.")
        return 1
    ep = Endpoint(cfg["base_url"], key, int(cfg.get("timeout_s", 120)))
    chat_model = cfg["chat_model"]
    vision_model = cfg.get("vision_model") or ""
    embed_model = cfg.get("embedding_model") or ""

    results: list[tuple[str, str, str, str]] = []  # (id, tên, kết quả, chi tiết)

    def rec(i, name, ok, detail):
        results.append((i, name, ok, detail))
        print(f"  {i}  {ok:<6} {name:<34} {detail[:110]}")

    print(f"Endpoint: {cfg['base_url']}   chat_model: {chat_model}\n")

    # ---- A: models -------------------------------------------------------
    st, resp = ep._req("GET", "/models")
    models: list[dict] = []
    max_len = None
    if st == 200 and isinstance(resp, dict) and "data" in resp:
        models = resp["data"]
        names = [m.get("id", "?") for m in models]
        for m in models:
            if m.get("id") == chat_model:
                max_len = m.get("max_model_len")
        rec("A", "/v1/models", "ĐẠT", f"{len(names)} model: {', '.join(names)[:200]}"
            + (f" · max_model_len={max_len}" if max_len else ""))
    else:
        rec("A", "/v1/models", "KHÔNG" if st > 0 else "LỖI", f"HTTP {st} {err_text(resp)}")

    # ---- B: chat ---------------------------------------------------------
    t0 = time.time()
    st, resp = ep.chat(chat_model, [{"role": "user", "content": "Trả lời đúng một từ: OK"}])
    dt = time.time() - t0
    if st == 200 and content_of(resp):
        rec("B", "chat cơ bản", "ĐẠT", f"{dt:.1f}s · '{content_of(resp).strip()[:40]}'")
    else:
        rec("B", "chat cơ bản", "KHÔNG" if st > 0 else "LỖI", f"HTTP {st} {err_text(resp)}")
        print("\nChat cơ bản không chạy — các phép thử sau chỉ để ghi nhận lỗi.")

    # ---- C: response_format json_schema ----------------------------------
    st, resp = ep.chat(chat_model, [{"role": "user", "content": EXTRACT_PROMPT}],
                       response_format={"type": "json_schema",
                                        "json_schema": {"name": "sizing", "strict": True,
                                                        "schema": SCHEMA}})
    if st == 200:
        try:
            obj = json.loads(content_of(resp))
            v = validate(obj)
            rec("C", "structured: response_format", "ĐẠT" if not v else "KHÔNG",
                json.dumps(obj, ensure_ascii=False)[:80] if not v else f"JSON nhưng {v}")
        except Exception as e:
            rec("C", "structured: response_format", "KHÔNG", f"không parse được: {e}")
    else:
        rec("C", "structured: response_format", "KHÔNG" if st > 0 else "LỖI",
            f"HTTP {st} {err_text(resp)}")

    # ---- D: guided_json (vLLM extra) --------------------------------------
    st, resp = ep.chat(chat_model, [{"role": "user", "content": EXTRACT_PROMPT}],
                       guided_json=SCHEMA)
    if st == 200:
        try:
            obj = json.loads(content_of(resp))
            v = validate(obj)
            rec("D", "structured: guided_json", "ĐẠT" if not v else "KHÔNG",
                json.dumps(obj, ensure_ascii=False)[:80] if not v else f"JSON nhưng {v}")
        except Exception as e:
            rec("D", "structured: guided_json", "KHÔNG", f"không parse được: {e}")
    else:
        rec("D", "structured: guided_json", "KHÔNG" if st > 0 else "LỖI",
            f"HTTP {st} {err_text(resp)}")

    # ---- E: prompt-only + validate, 3 tries -------------------------------
    got = None
    last = ""
    for attempt in range(3):
        st, resp = ep.chat(chat_model, [
            {"role": "system", "content": "Bạn chỉ trả về JSON hợp lệ, không giải thích, không markdown."},
            {"role": "user", "content": EXTRACT_PROMPT}])
        if st != 200:
            last = f"HTTP {st} {err_text(resp)}"
            continue
        try:
            obj = parse_json_loose(content_of(resp))
            v = validate(obj)
            if not v:
                got = (attempt + 1, obj)
                break
            last = f"JSON nhưng {v}"
        except Exception as e:
            last = f"không parse được: {e}"
    if got:
        rec("E", "structured: prompt + validate", "ĐẠT",
            f"lần thử {got[0]}/3 · {json.dumps(got[1], ensure_ascii=False)[:70]}")
    else:
        rec("E", "structured: prompt + validate", "KHÔNG", f"3/3 thất bại · {last}")

    # ---- F: embeddings ---------------------------------------------------
    if embed_model:
        st, resp = ep._req("POST", "/embeddings", {"model": embed_model, "input": "định cỡ máy chủ"})
        if st == 200 and isinstance(resp, dict) and resp.get("data"):
            dim = len(resp["data"][0].get("embedding", []))
            rec("F", "embeddings", "ĐẠT", f"model={embed_model} · dim={dim}")
        else:
            rec("F", "embeddings", "KHÔNG" if st > 0 else "LỖI", f"HTTP {st} {err_text(resp)}")
    else:
        rec("F", "embeddings", "BỎ QUA", "embedding_model để trống trong settings")

    # ---- G: vision -------------------------------------------------------
    if vision_model:
        st, resp = ep.chat(vision_model, [{"role": "user", "content": [
            {"type": "text", "text": "Ảnh này màu gì? Trả lời một từ."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{TINY_PNG_B64}"}}]}])
        if st == 200 and content_of(resp):
            rec("G", "vision", "ĐẠT", f"model={vision_model} · '{content_of(resp).strip()[:40]}'")
        else:
            rec("G", "vision", "KHÔNG" if st > 0 else "LỖI", f"HTTP {st} {err_text(resp)}")
    else:
        rec("G", "vision", "BỎ QUA", "vision_model để trống trong settings")

    # ---- H: context window -----------------------------------------------
    if max_len:
        rec("H", "context window", "ĐẠT", f"max_model_len={max_len} (từ /v1/models)")
    else:
        # Probe by size. ~4 chars ≈ 1 token for Vietnamese-heavy text is optimistic;
        # we send Latin filler so the estimate is conservative.
        found = None
        for k in (4000, 8000, 16000, 32000, 64000):
            filler = ("số liệu " * (k * 4 // 8))[: k * 4]
            st, resp = ep.chat(chat_model, [{"role": "user", "content": filler + "\nTrả lời: OK"}])
            if st == 200:
                found = k
            else:
                break
        rec("H", "context window", "ĐẠT" if found else "KHÔNG",
            f"chấp nhận tới ~{found} token (ước lượng thô)" if found else "kể cả 4k cũng lỗi")

    # ---- I: rate limit ---------------------------------------------------
    if args.skip_rate:
        rec("I", "rate limit", "BỎ QUA", "--skip-rate")
    else:
        codes, lat = [], []
        for _ in range(10):
            t0 = time.time()
            st, _r = ep.chat(chat_model, [{"role": "user", "content": "OK?"}])
            lat.append(time.time() - t0)
            codes.append(st)
        n429 = codes.count(429)
        rec("I", "rate limit (10 lời gọi liên tiếp)", "ĐẠT" if n429 == 0 else "KHÔNG",
            f"429: {n429}/10 · độ trễ TB {sum(lat)/len(lat):.1f}s · max {max(lat):.1f}s")

    # ---- report ----------------------------------------------------------
    lines = ["# 0.10 — Kết quả xác minh endpoint LLM (TỰ SINH)", "",
             "> Sinh bởi `scripts/probe_llm_endpoint.py`. Không chứa khóa API.",
             f"> Endpoint: `{cfg['base_url']}` · chat_model: `{chat_model}`"
             + (f" · vision_model: `{vision_model}`" if vision_model else "")
             + (f" · embedding_model: `{embed_model}`" if embed_model else ""), "",
             "| # | Phép thử | Kết quả | Chi tiết |", "|---|---|---|---|"]
    for i, name, ok, detail in results:
        lines.append(f"| {i} | {name} | **{ok}** | {detail.replace('|', '¦')} |")
    if models:
        lines += ["", "## Model trên cụm", ""]
        for m in models:
            lines.append(f"- `{m.get('id')}`" + (f" — max_model_len {m['max_model_len']}"
                                                 if m.get("max_model_len") else ""))
    open(args.out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    assert key not in open(args.out, encoding="utf-8").read()
    print(f"\n-> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
