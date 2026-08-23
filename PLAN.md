# PLAN.md — Lộ trình triển khai Sizing Copilot

> **Cách dùng file này:** đây là bảng công việc sống. Mỗi khi hoàn thành một
> mục, đánh dấu `[x]`. Không chuyển giai đoạn khi chưa đạt **Tiêu chí hoàn thành**
> của giai đoạn hiện tại. Bối cảnh và lý do đầy đủ: `docs/ke-hoach-trien-khai.md`.
> Nguyên tắc thiết kế bắt buộc: `CLAUDE.md`.

## Bảng trạng thái

| GĐ | Tên | Tiến độ | Trạng thái |
|----|-----|---------|------------|
| 0 | Chuẩn bị tri thức & dữ liệu | 0 / 10 | ⬜ Chưa bắt đầu |
| 1 | MVP chỉ xử lý text | 0 / 15 | ⬜ Chưa bắt đầu |
| 2 | Đa phương thức & tái sử dụng | 0 / 13 | ⬜ Chưa bắt đầu |
| 3 | Tích hợp & tinh chỉnh | 0 / 11 | ⬜ Chưa bắt đầu |
| 4 | Vận hành & cải tiến | 0 / 6 | ⬜ Liên tục |

**Đang tập trung:** _(cập nhật mục đang làm ở đây)_

---

## GIAI ĐOẠN 0 — Chuẩn bị tri thức & dữ liệu  (1–1.5 tuần)

> Đây là giai đoạn quyết định trần chất lượng. Phần lớn là việc nghiệp vụ thủ
> công, KHÔNG giao cho AI. **Chưa xong GĐ 0 thì chưa viết code xử lý.**

- [ ] 0.1 — Rà soát tài liệu tiêu chí, liệt kê mọi quy tắc thành danh sách phẳng
- [ ] 0.2 — Phân loại từng quy tắc: định lượng (→C4) hay định tính (→C5); ghi tỷ lệ
- [ ] 0.3 — Với quy tắc định lượng: viết rõ công thức, tham số, ngưỡng, đơn vị
- [ ] 0.4 — Với quy tắc định tính: viết tiêu chí "thế nào là đạt" thật cụ thể
- [ ] 0.5 — Số hóa thành `config/rules.yaml` (cấu trúc ở docs, Phụ lục A); mỗi quy tắc có mã
- [ ] 0.6 — Chuẩn hóa 30 bản sizing lịch sử: đặt tên + metadata (loại, ngày, trạng thái)
- [ ] 0.7 — Với mỗi bản, ghi lại lỗi người thẩm định đã bắt → nhãn cho eval set
- [ ] 0.8 — Chia dữ liệu: ~20 bản tập phát triển, ~10 bản tập kiểm tra GIỮ KÍN
- [ ] 0.9 — Đo baseline: số vòng phản hồi TB + thời gian TB mỗi vòng hiện nay
- [ ] 0.10 — Xác minh hạ tầng: model vision, endpoint embedding, context window, rate limit

**Tiêu chí hoàn thành:** một người thứ hai đọc `rules.yaml` và xác nhận phản ánh
đúng tài liệu gốc; đã có `data/eval_set.json` và báo cáo baseline.

---

## GIAI ĐOẠN 1 — MVP chỉ xử lý text  (2–3 tuần)

> Chạy đầu-cuối trên text + bảng, TẠM BỎ QUA hình ảnh. Chứng minh giá trị sớm.

### Tuần 1 — Nền tảng & bóc tách
- [ ] 1.1 — Khởi tạo dự án, cấu trúc thư mục (docs Phụ lục B), Git, `uv`
- [ ] 1.2 — Kết nối thử vLLM: gọi chat + kiểm tra structured output chạy được
- [ ] 1.3 — C1: đọc `.docx` (text, heading, bảng), giữ vị trí phần tử
- [ ] 1.4 — Module chuẩn hóa đơn vị & số liệu + unit test riêng
- [ ] 1.5 — Chạy C1 trên cả 30 bản lịch sử, ghi nhận ca lỗi định dạng

### Tuần 2 — Trích xuất & kiểm tra định lượng
- [ ] 1.6 — Định nghĩa schema Pydantic (`SizingCore` + `SizingExtension`)
- [ ] 1.7 — C3: trích trường bằng structured output; đo độ chính xác trên tập phát triển
- [ ] 1.8 — Bộ nạp & diễn giải `rules.yaml`
- [ ] 1.9 — C4: thực thi quy tắc định lượng bằng code; unit test cho từng công thức
- [ ] 1.10 — C7 bản đơn giản: xuất báo cáo Markdown

### Tuần 3 — Kiểm tra định tính & giao diện thử
- [ ] 1.11 — Dựng RAG: chia nhỏ tài liệu tiêu chí, sinh embedding, nạp Qdrant
- [ ] 1.12 — C5: kiểm định tính, BẮT BUỘC trích dẫn quy tắc
- [ ] 1.13 — Eval harness: chạy eval set, tính recall + false positive
- [ ] 1.14 — Giao diện Streamlit: tải file → xem báo cáo
- [ ] 1.15 — Demo nội bộ 2–3 đồng nghiệp, thu phản hồi

**Tiêu chí hoàn thành:** recall ≥ 50% trên tập phát triển; KHÔNG finding nào
thiếu căn cứ (mọi mục đều có `rule_ref` hoặc `computed_evidence`).

---

## GIAI ĐOẠN 2 — Đa phương thức & tái sử dụng  (2–3 tuần)

### Tuần 4 — Xử lý hình ảnh
- [ ] 2.1 — Trích ảnh từ `.docx` kèm ngữ cảnh văn bản trước/sau
- [ ] 2.2 — Phân loại ảnh (sơ đồ / biểu đồ-dashboard / khác)
- [ ] 2.3 — C2: vision + OCR, sinh mô tả và trích số
- [ ] 2.4 — Cơ chế xuống cấp có kiểm soát: cảnh báo khi không kiểm chứng được (NT4)
- [ ] 2.5 — Kiểm tra chéo: số trong ảnh biểu đồ vs số trong bảng sizing

### Tuần 5 — Truy hồi & scale
- [ ] 2.6 — Nạp 30 bản lịch sử đã trích trường vào vector DB
- [ ] 2.7 — C6: tìm bản tương tự, hiển thị độ tương đồng + điểm khác biệt
- [ ] 2.8 — Logic scale kèm phân loại tuyến tính / phi tuyến (bảng ở docs mục C6)
- [ ] 2.9 — Sinh bản nháp đã scale kèm cảnh báo rõ cho từng tham số cần xem lại

### Tuần 6 — Củng cố
- [ ] 2.10 — Chuyển điều phối sang LangGraph nếu pipeline đã đủ phức tạp (không bắt buộc)
- [ ] 2.11 — Xử lý lỗi & timeout khi gọi LLM; cơ chế retry
- [ ] 2.12 — Cache kết quả trích xuất theo hash file
- [ ] 2.13 — Chạy lại eval set đầy đủ, so sánh với GĐ 1

**Tiêu chí hoàn thành:** recall ≥ 65% trên tập phát triển; tính năng scale được
≥ 3 người dùng thử xác nhận hữu ích.

---

## GIAI ĐOẠN 3 — Tích hợp & tinh chỉnh  (2 tuần)

### Tuần 7 — Tích hợp
- [ ] 3.1 — Bọc pipeline thành REST API FastAPI (`POST /review`, `GET /result/{id}`)
- [ ] 3.2 — Xử lý bất đồng bộ (job queue) vì thời gian chạy có thể vài phút
- [ ] 3.3 — Phối hợp thêm nút "Kiểm tra sizing" vào web nội bộ sẵn có
- [ ] 3.4 — Thiết kế hiển thị báo cáo trên web: nhóm theo mức độ, hiện trích dẫn quy tắc
- [ ] 3.5 — Đóng gói Docker Compose, triển khai môi trường nội bộ

### Tuần 8 — Tinh chỉnh & bàn giao
- [ ] 3.6 — Chạy trên tập kiểm tra GIỮ KÍN — đây mới là con số thật
- [ ] 3.7 — Phân tích false positive; siết prompt/quy tắc cho mẫu sai lặp lại
- [ ] 3.8 — Cân chỉnh ngưỡng mức độ nghiêm trọng theo phản hồi người thẩm định
- [ ] 3.9 — Tài liệu hướng dẫn sử dụng (1–2 trang, cho người không chuyên)
- [ ] 3.10 — Tài liệu vận hành: cách cập nhật `rules.yaml`, cách bổ sung bản mới
- [ ] 3.11 — Thử nghiệm thật với 3–5 đơn vị, thu phản hồi

**Tiêu chí hoàn thành:** recall ≥ 70% và false positive ≤ 20% trên tập kiểm tra
giữ kín; người thẩm định xác nhận báo cáo phù hợp cách họ đánh giá.

---

## GIAI ĐOẠN 4 — Vận hành & cải tiến  (liên tục)

- [ ] 4.1 — Vòng phản hồi: người dùng đánh dấu finding đúng/sai trên giao diện
- [ ] 4.2 — Hằng tháng: rà finding bị đánh dấu sai, điều chỉnh quy tắc/prompt
- [ ] 4.3 — Bổ sung bản sizing mới đã ký vào kho lịch sử + eval set
- [ ] 4.4 — Cập nhật `rules.yaml` khi tài liệu tiêu chí đổi; CHẠY LẠI eval set sau mỗi lần
- [ ] 4.5 — Hằng quý: báo cáo chỉ số so với baseline
- [ ] 4.6 — Khi kho đạt ~100+ bản có nhãn: cân nhắc fine-tune model trích xuất (chưa làm với 30 bản)

---

## Nhật ký quyết định

> Ghi lại các quyết định quan trọng và lý do, để không lặp lại tranh luận cũ.

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| | | |
