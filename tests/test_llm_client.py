"""Test phần lõi của client — chạy offline, không gọi mạng.

Ba hành vi ở đây đều bắt nguồn từ lỗi THẬT quan sát khi dò endpoint (0.10),
nên chúng là hồi quy, không phải test cho vui.
"""
import pytest
from pydantic import BaseModel

from src.llm.client import (
    ExtractionFailed, LLMClient, LLMError, extract_json_block, strip_fence,
)


class Sizing(BaseModel):
    ten_he_thong: str
    so_ccu: int


# --- strip fence: output THẬT của gateway bọc trong ```json (phép thử D) -----
@pytest.mark.parametrize("raw, expect", [
    ('```json\n{"a": 1}\n```', '{"a": 1}'),
    ('```\n{"a": 1}\n```', '{"a": 1}'),
    ('{"a": 1}', '{"a": 1}'),
    ('  ```JSON\n{"a": 1}```  ', '{"a": 1}'),
])
def test_strip_fence(raw, expect):
    assert strip_fence(raw) == expect


def test_extract_json_block_bo_qua_van_xuoi_kem_theo():
    raw = 'Đây là kết quả:\n```json\n{"ten_he_thong": "MNP", "so_ccu": 300}\n```\nHết.'
    assert extract_json_block(raw) == '{"ten_he_thong": "MNP", "so_ccu": 300}'


def test_extract_json_block_khong_co_json_thi_bao_loi():
    with pytest.raises(ValueError):
        extract_json_block("model từ chối trả lời")


# --- client với transport giả --------------------------------------------
class FakeClient(LLMClient):
    """Thay nguyên phần gọi mạng bằng danh sách phản hồi định sẵn."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []
        self.chat_model = "fake"
        self.vision_model = ""
        self.temperature = 0.1
        self.cfg = {}

    def chat(self, messages, *, model=None, max_tokens=4000, **extra):
        self.calls.append(messages)
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_extract_thanh_cong_ngay_lan_dau():
    c = FakeClient(['{"ten_he_thong": "MNP", "so_ccu": 300}'])
    out = c.extract(Sizing, [{"role": "user", "content": "x"}])
    assert out.so_ccu == 300
    assert len(c.calls) == 1


def test_extract_go_duoc_fence():
    c = FakeClient(['```json\n{"ten_he_thong": "MNP", "so_ccu": 300}\n```'])
    assert c.extract(Sizing, [{"role": "user", "content": "x"}]).ten_he_thong == "MNP"


def test_extract_retry_khi_sai_lieu_do_va_nhac_lai_loi():
    c = FakeClient([
        '{"ten_he_thong": "MNP"}',                       # thiếu so_ccu
        '{"ten_he_thong": "MNP", "so_ccu": 300}',
    ])
    out = c.extract(Sizing, [{"role": "user", "content": "x"}])
    assert out.so_ccu == 300
    assert len(c.calls) == 2
    # lần thử 2 phải mang theo lỗi để model tự sửa, không hỏi lại y nguyên
    assert any("KHÔNG hợp lệ" in m["content"] for m in c.calls[1])


def test_extract_het_luot_thi_NEM_LOI_chu_khong_bia():
    c = FakeClient(['nope'] * 3)
    with pytest.raises(ExtractionFailed) as e:
        c.extract(Sizing, [{"role": "user", "content": "x"}], max_retries=3)
    assert e.value.attempts == 3


def test_phan_hoi_rong_la_LOI_khong_phai_ket_qua_hop_le():
    """Bẫy thật: max_tokens nhỏ -> content rỗng nhưng vẫn HTTP 200."""
    c = FakeClient([LLMError("phản hồi rỗng"), LLMError("phản hồi rỗng"),
                    LLMError("phản hồi rỗng")])
    with pytest.raises(ExtractionFailed):
        c.extract(Sizing, [{"role": "user", "content": "x"}], max_retries=3)


# --- chẩn đoán cho smoke test: số lần thử và đường schema đã dùng ----------
def test_ghi_lai_so_lan_thu_de_bao_cao_noi_duoc_chi_phi_that():
    """Nếu lần nào cũng phải thử lại thì C3 tốn gấp 2-3 lời gọi — phải đo được."""
    c = FakeClient(['{"ten_he_thong": "MNP"}',                # thiếu so_ccu
                    '{"ten_he_thong": "MNP", "so_ccu": 300}'])
    c.extract(Sizing, [{"role": "user", "content": "x"}])
    assert c.last_attempts == 2

    c2 = FakeClient(['{"ten_he_thong": "MNP", "so_ccu": 300}'])
    c2.extract(Sizing, [{"role": "user", "content": "x"}])
    assert c2.last_attempts == 1


def test_gateway_tu_choi_response_format_thi_lui_ve_prompt_VA_GHI_LAI():
    """Gateway trả 400 cho tham số lạ — không được coi là hỏng, nhưng phải báo.

    Trước đây chỉ bắt `TypeError`, mà SDK ném lỗi HTTP chứ không phải TypeError,
    nên ca này sẽ vỡ ra ngoài thành traceback khó hiểu ngay trong mạng công ty.
    """
    from openai import BadRequestError

    # Dựng ngoại lệ KHÔNG qua `__init__` của SDK: nó đòi một đối tượng response
    # httpx thật, mà tên module đó còn đổi giữa các bản openai (`httpx` ->
    # `httpx2` ở 3.7). Test này nói về LOẠI ngoại lệ, không về cách SDK dựng nó.
    loi = BadRequestError.__new__(BadRequestError)
    Exception.__init__(loi, "unknown parameter: response_format")

    class TuChoiSchema(FakeClient):
        def chat(self, messages, *, model=None, max_tokens=4000, **extra):
            if "response_format" in extra:
                raise loi
            return super().chat(messages, model=model, max_tokens=max_tokens)

    c = TuChoiSchema(['{"ten_he_thong": "MNP", "so_ccu": 300}'])
    out = c.extract(Sizing, [{"role": "user", "content": "x"}])
    assert out.so_ccu == 300
    assert c.last_schema_path == "prompt"
    assert "response_format" in c.last_schema_error
