"""Client cho gateway OpenAI-compatible nội bộ.

Vì sao KHÔNG tin structured output của máy chủ (xem docs/0.10-...):
phép dò cho thấy `guided_json` được nhận nhưng **bỏ qua** — output vẫn bọc trong
fence ```json, mà guided decoding thật thì token đầu bắt buộc là `{`. Không phân
biệt được `response_format` là ràng buộc thật hay chỉ là model tuân lệnh, nên
đường an toàn duy nhất là: gửi kèm schema (được thì tốt) rồi **luôn** strip fence,
**luôn** validate bằng chính model Pydantic, sai thì retry.

Hai bẫy đã gặp thật, đều xử lý ở đây:
  - `max_tokens` nhỏ làm `content` RỖNG mà vẫn HTTP 200 (model trả kèm
    `reasoning_content`). Rỗng phải coi là LỖI, không phải kết quả hợp lệ.
  - Output bọc trong fence ```json ... ```.

Không bao giờ trả giá trị bịa: hết số lần thử thì ném ExtractionFailed để tầng
trên tạo finding nhóm "thiếu thông tin" (NT4).
"""
from __future__ import annotations

import json
import os
import re
from typing import TypeVar

import yaml
from openai import OpenAI
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

KEY_ENV = "SIZING_COPILOT_API_KEY"
DEFAULT_MAX_TOKENS = 4000  # ≥2000: dưới ngưỡng này `content` có thể rỗng (0.10)
_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class LLMError(RuntimeError):
    """Lỗi gọi model — mạng, khóa, hoặc phản hồi rỗng."""


class ExtractionFailed(LLMError):
    """Hết số lần thử mà vẫn không ra JSON hợp lệ. KHÔNG được nuốt lỗi này."""

    def __init__(self, attempts: int, last_error: str, last_raw: str = ""):
        super().__init__(f"thất bại sau {attempts} lần thử: {last_error}")
        self.attempts = attempts
        self.last_error = last_error
        self.last_raw = last_raw


def strip_fence(text: str) -> str:
    """Bỏ fence ```json ... ``` nếu có. Nội dung bên trong giữ nguyên vẹn."""
    t = text.strip()
    if t.startswith("```"):
        t = _FENCE.sub("", t)
    return t.strip()


def extract_json_block(text: str) -> str:
    """Lấy object JSON ngoài cùng, chịu được vài dòng văn xuôi kèm theo."""
    t = strip_fence(text)
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("không tìm thấy object JSON trong phản hồi")
    return t[start:end + 1]


def load_settings(path: str = "config/settings.yaml") -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Chưa có {path}. Copy từ config/settings.example.yaml rồi điền."
        )
    return yaml.safe_load(open(path, encoding="utf-8"))


class LLMClient:
    def __init__(self, settings: dict | None = None, settings_path: str = "config/settings.yaml"):
        cfg = (settings or load_settings(settings_path))["llm"]
        key = os.environ.get(KEY_ENV)
        if not key:
            raise LLMError(f"Chưa đặt biến môi trường {KEY_ENV}.")
        self.cfg = cfg
        self.chat_model = cfg["chat_model"]
        self.vision_model = cfg.get("vision_model") or ""
        self.temperature = float(cfg.get("temperature", 0.1))
        self._client = OpenAI(base_url=cfg["base_url"], api_key=key,
                              timeout=float(cfg.get("timeout_s", 120)))

    # ------------------------------------------------------------------
    def chat(self, messages: list[dict], *, model: str | None = None,
             max_tokens: int = DEFAULT_MAX_TOKENS, **extra) -> str:
        """Một lời gọi chat. Phản hồi rỗng là LỖI, không phải chuỗi rỗng hợp lệ."""
        resp = self._client.chat.completions.create(
            model=model or self.chat_model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=max_tokens,
            **extra,
        )
        content = (resp.choices[0].message.content or "").strip()
        if not content:
            # Đã gặp thật: model dồn hết ngân sách token vào reasoning_content.
            raise LLMError(
                f"phản hồi rỗng (finish_reason={resp.choices[0].finish_reason}, "
                f"max_tokens={max_tokens}) — thử tăng max_tokens"
            )
        return content

    # ------------------------------------------------------------------
    def extract(self, schema: type[T], messages: list[dict], *,
                model: str | None = None, max_retries: int = 3,
                max_tokens: int = DEFAULT_MAX_TOKENS) -> T:
        """Gọi model và ép kết quả về `schema`. Ném ExtractionFailed nếu không được.

        `response_format` chỉ là tối ưu hoá — kết quả vẫn phải qua strip fence và
        validate. Mỗi lần thử lại có nhắc lại lỗi trước để model tự sửa.
        """
        json_schema = schema.model_json_schema()
        convo = list(messages)
        last_err, last_raw = "", ""

        for attempt in range(1, max_retries + 1):
            try:
                raw = self.chat(
                    convo, model=model, max_tokens=max_tokens,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {"name": schema.__name__, "strict": True,
                                        "schema": json_schema},
                    },
                )
            except TypeError:
                # gateway không nhận response_format -> đi đường prompt thuần
                raw = self.chat(convo, model=model, max_tokens=max_tokens)
            except LLMError as e:
                last_err, last_raw = str(e), ""
                continue

            last_raw = raw
            try:
                return schema.model_validate_json(extract_json_block(raw))
            except (ValueError, ValidationError) as e:
                last_err = str(e)[:400]

            if attempt < max_retries:
                convo = list(messages) + [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content":
                        f"Kết quả trên KHÔNG hợp lệ: {last_err}\n"
                        f"Trả lại JSON đúng lược đồ sau, chỉ JSON, không giải thích, "
                        f"không dùng ```:\n{json.dumps(json_schema, ensure_ascii=False)}"},
                ]

        raise ExtractionFailed(max_retries, last_err, last_raw)
