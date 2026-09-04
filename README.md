# Sizing Copilot

Trợ lý AI giúp đơn vị xin cấp tài nguyên **tự kiểm bản định cỡ (sizing) trước
khi nộp**. Công cụ đọc file sizing Word, đối chiếu với bộ quy tắc định cỡ của
đơn vị thẩm định, và trả về danh sách điểm chưa đạt kèm căn cứ và gợi ý sửa —
giúp cắt giảm số vòng phản hồi qua lại giữa hai bên.

> Đây là công cụ **cố vấn**. Người thẩm định vẫn là người quyết định cuối cùng.

**Trạng thái:** đang phát triển — xem [`PLAN.md`](./PLAN.md) để biết tiến độ.

## Tài liệu

- [`CLAUDE.md`](./CLAUDE.md) — nguyên tắc thiết kế & quy ước (Claude Code tự nạp)
- [`PLAN.md`](./PLAN.md) — lộ trình theo giai đoạn & bảng theo dõi tiến độ
- [`docs/ke-hoach-trien-khai.md`](./docs/ke-hoach-trien-khai.md) — kế hoạch chi tiết đầy đủ, bối cảnh và lý do

## Kiến trúc

Pipeline có kiểm soát: `Ingest → Extract → Validate → Report`.

| Mã | Thành phần | Vai trò |
|----|-----------|---------|
| C1 | Ingestion | Đọc docx → text / bảng / ảnh |
| C2 | Vision | Vision + OCR cho ảnh, cảnh báo có kiểm soát |
| C3 | Extraction | Trích trường + phân loại dịch vụ |
| C4 | Validators (định lượng) | Kiểm quy tắc tính được — thuần code |
| C5 | Validators (định tính) | RAG + LLM, bắt trích dẫn quy tắc |
| C6 | Retrieval | Tìm bản tương tự + đề xuất scale |
| C7 | Reporting | Gom, xếp ưu tiên, sinh báo cáo |

Bốn nguyên tắc bắt buộc (chi tiết trong `CLAUDE.md`): tính toán bằng code không
bằng LLM; mọi phát hiện phải có căn cứ; quy tắc là dữ liệu không phải prompt;
xuống cấp có kiểm soát khi không chắc.

## Công nghệ

Python 3.11+ · vLLM (OpenAI-compatible) · Pydantic · python-docx · PaddleOCR ·
BGE-M3 · Qdrant · FastAPI · Streamlit · pytest · Docker Compose

## Cấu trúc thư mục

```
sizing-copilot/
├── config/          # rules.yaml, units.yaml, settings.yaml
├── src/
│   ├── ingestion/   # C1
│   ├── vision/      # C2
│   ├── extraction/  # C3
│   ├── validators/  # C4 (quantitative.py), C5 (qualitative.py)
│   ├── retrieval/   # C6
│   ├── reporting/   # C7
│   ├── llm/         # client vLLM, structured output
│   └── pipeline.py  # điều phối
├── data/            # historical/, knowledge_base/, eval_set.json
├── eval/            # run_eval.py, reports/
├── api/             # FastAPI
├── ui/              # Streamlit
├── tests/
└── docker-compose.yml
```

## Cài đặt

```bash
# Yêu cầu: Python 3.11+, uv (https://github.com/astral-sh/uv)
git clone <repo-url>
cd sizing-copilot
uv sync
cp config/settings.example.yaml config/settings.yaml   # rồi điền cấu hình
```

## Cấu hình

Điền `config/settings.yaml` và biến môi trường. KHÔNG commit khóa API.

```yaml
llm:
  base_url: "https://<vllm-endpoint>/v1"   # endpoint vLLM nội bộ
  chat_model: "<tên-model-chat>"
  vision_model: "<tên-model-vision>"
  embedding_model: "bge-m3"
  temperature: 0.1
qdrant:
  url: "http://localhost:6333"
```

```bash
export SIZING_COPILOT_API_KEY="<api-key-được-cấp>"
```

## Chạy

```bash
uv run pytest                          # chạy test
uv run python -m eval.run_eval         # chạy eval set (recall + false positive)
uv run streamlit run ui/app.py         # giao diện thử
uv run uvicorn api.main:app --reload   # API
```

### Chạy được KHI KHÔNG có model

Model tự dựng chỉ với tới được từ máy trong mạng nội bộ. Hai việc dưới đây không gọi
model nên chạy ở đâu cũng được — và chúng cho kết quả lặp lại y hệt giữa hai lần chạy:

```bash
python scripts/fill_checklist.py "<bản-sizing.docx>"   # điền cột tham chiếu checklist
python scripts/make_word_template.py                   # sinh mẫu Word chuẩn
streamlit run ui/app.py                                # 2/3 chế độ vẫn dùng được
```

Danh sách đầy đủ việc cần người làm, chia theo môi trường:
[`docs/viec-cua-nguoi-va-moi-truong.md`](docs/viec-cua-nguoi-va-moi-truong.md).

## Ghi chú

Công cụ nội bộ. Toàn bộ xử lý dùng LLM self-hosted, không gửi dữ liệu ra ngoài.
