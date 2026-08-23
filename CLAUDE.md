# CLAUDE.md — Sizing Copilot

> File này được Claude Code tự động nạp mỗi phiên. Giữ ngắn gọn, chỉ chứa
> nguyên tắc, quy ước và cạm bẫy. Chi tiết công việc nằm ở `PLAN.md`.
> Bối cảnh và lý do đầy đủ nằm ở `docs/ke-hoach-trien-khai.md`.

## Dự án là gì

Trợ lý AI giúp **người xin cấp tài nguyên tự kiểm bản định cỡ (sizing) Word
trước khi nộp**. Công cụ đọc file `.docx`, đối chiếu với bộ quy tắc định cỡ
của đơn vị thẩm định, và trả về danh sách điểm chưa đạt kèm căn cứ và gợi ý sửa.

Đây là công cụ **cố vấn (advisory)**, KHÔNG tự phê duyệt/từ chối. Người thẩm
định vẫn là người quyết định cuối cùng.

## 4 NGUYÊN TẮC BẮT BUỘC — không được vi phạm

Đây là ranh giới thiết kế. Nếu một thay đổi vi phạm bất kỳ nguyên tắc nào,
DỪNG LẠI và báo cho người dùng thay vì tự ý làm.

- **NT1 — Tính toán bằng code, KHÔNG bằng LLM.** LLM chỉ trích xuất con số.
  Mọi phép tính, so ngưỡng, kiểm nhất quán do Python thực hiện. Không bao giờ
  hỏi LLM "tính giúp" hay "con số này có đúng không".
- **NT2 — Mọi phát hiện phải có căn cứ (grounding).** Mỗi finding phải neo vào
  `rule_ref` (mã quy tắc + trích dẫn) HOẶC `computed_evidence` (số do code tính).
  Không có căn cứ thì lọc bỏ, không xuất ra.
- **NT3 — Quy tắc là dữ liệu, không phải prompt/code.** Toàn bộ quy tắc nằm
  trong `config/rules.yaml`. Không hard-code công thức/ngưỡng vào Python, không
  nhét quy tắc vào prompt. Người nghiệp vụ phải sửa được quy tắc mà không cần code.
- **NT4 — Xuống cấp có kiểm soát.** Khi không chắc (điển hình: hình ảnh, sơ đồ),
  xuất cảnh báo "không kiểm chứng được" và đề nghị bổ sung. KHÔNG bịa, KHÔNG im
  lặng bỏ qua.

## Cạm bẫy đã biết (đọc kỹ trước khi code)

- KHÔNG để LLM tự điền giá trị mặc định cho trường thiếu → để `None` và tạo một
  finding nhóm "thiếu thông tin".
- KHÔNG dùng `eval()` cho công thức. Dùng `asteval` / `simpleeval`.
- KHÔNG gộp trích xuất và thẩm định vào một lần gọi LLM. Một nhiệm vụ một lần gọi.
- KHÔNG chạy theo recall bằng mọi giá ở giai đoạn đầu. **Ưu tiên độ chính xác
  hơn độ phủ** — một cảnh báo sai làm mất niềm tin người dùng nặng hơn một lỗi
  bỏ sót. Có thể lọc theo `confidence` và chỉ hiện finding độ tin cậy cao.
- KHÔNG chuyển sang giai đoạn sau khi chưa đạt tiêu chí hoàn thành của giai đoạn
  hiện tại (xem `PLAN.md`). Đặc biệt: chưa có `rules.yaml` + eval set thì CHƯA viết
  code xử lý.

## Kiến trúc — pipeline có kiểm soát (KHÔNG phải agent tự do)

Luồng: `Ingest → Extract → Validate → Report`. 7 thành phần:

| Mã | Thành phần | Vai trò |
|----|-----------|---------|
| C1 | `src/ingestion/` | Đọc docx → text/bảng/ảnh, giữ vị trí |
| C2 | `src/vision/` | Vision + OCR cho ảnh; sinh cảnh báo theo NT4 |
| C3 | `src/extraction/` | Trích trường + phân loại dịch vụ (structured output) |
| C4 | `src/validators/quantitative.py` | Kiểm quy tắc định lượng — THUẦN CODE (NT1) |
| C5 | `src/validators/qualitative.py` | Kiểm định tính — RAG + LLM, bắt trích dẫn (NT2) |
| C6 | `src/retrieval/` | Tìm bản sizing tương tự + đề xuất scale |
| C7 | `src/reporting/` | Gom, khử trùng, xếp ưu tiên, sinh báo cáo |

Điều phối: `src/pipeline.py`. Giai đoạn 1 dùng Python thuần; cân nhắc LangGraph
ở Giai đoạn 2 nếu pipeline đủ phức tạp — không dùng sớm.

## Công nghệ

- Python 3.11+, quản lý bằng `uv`.
- LLM: gọi qua `openai` SDK trỏ vào `base_url` của vLLM (OpenAI-compatible).
  Cấu hình trong `config/settings.yaml` + biến môi trường, KHÔNG hard-code.
- Structured output: `pydantic` + JSON Schema (guided decoding của vLLM).
- Đọc docx: `python-docx`, `docx2python`, `zipfile`. OCR: PaddleOCR/Tesseract.
- Embedding: BGE-M3. Vector DB: Qdrant.
- API: FastAPI. Giao diện thử: Streamlit. Test: pytest.

## Quy ước code

- Toàn bộ text hướng tới người dùng cuối (finding, báo cáo, gợi ý) viết **tiếng
  Việt**. Định danh code, log, commit message viết tiếng Anh.
- Mọi hàm trong `validators/quantitative.py` phải có unit test tương ứng trong
  `tests/`. Đây là phần lõi tin cậy, không được thiếu test.
- Cấu trúc finding tuân theo schema ở `docs/ke-hoach-trien-khai.md` mục C7
  (id, severity, category, location, rule_ref, rule_quote, finding,
  computed_evidence, suggestion, confidence).
- Nhiệt độ LLM 0–0.2 cho cả trích xuất lẫn thẩm định.

## Lệnh thường dùng

```bash
uv sync                          # cài phụ thuộc
uv run pytest                    # chạy toàn bộ test
uv run python -m eval.run_eval   # chạy eval set, in recall + false positive
uv run streamlit run ui/app.py   # mở giao diện thử
uv run uvicorn api.main:app --reload   # chạy API
```

## Cách làm việc trên dự án này

1. Trước khi bắt đầu, đọc `PLAN.md` để biết đang ở giai đoạn nào và mục tiếp theo.
2. Làm theo thứ tự các mục chưa tick trong giai đoạn hiện tại. Không nhảy cóc.
3. Sau khi hoàn thành một mục, cập nhật checkbox trong `PLAN.md` (đánh dấu `[x]`)
   và ghi ngắn gọn kết quả nếu cần.
4. Khi đề xuất thay đổi lớn, đối chiếu với 4 nguyên tắc bắt buộc trước.
5. Nếu phát hiện quy tắc trong tài liệu tiêu chí mơ hồ/mâu thuẫn, KHÔNG tự quyết
   — nêu ra để người dùng xác nhận với người thẩm định.
