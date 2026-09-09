# Kịch bản demo cho sếp — Sizing Copilot chạy trên Docker, máy nội bộ

> Ngày dựng: 2026-09-09 · branch `dev-isolate` · commit `cf9e49b` (image)
> Service: `docker compose` — container `sizing-copilot`, port **8902**
> Bản báo cáo mẫu đã chạy sẵn: `data/tai_len/demo-bccs3-bao-cao.md` (hồ sơ BCCS 3.0, thị trường Lào)

---

## 1. Trạng thái đang chạy (không cần làm gì trước buổi demo)

```bash
docker compose ps copilot        # phải thấy "Up (healthy)"
curl http://localhost:8902/health
```

Phản hồi `/health` mẫu:

```json
{"trang_thai":"sống","model":true,"chat_model":"claude-opus-4-6",
 "phien_ban":"C3-v6 (hỏi theo CỘT bảng…)","commit":"cf9e49b (image)"}
```

- `model: true` = máy với tới được model AI nội bộ (10.221.58.70:8401)
- `commit (image)` = báo cáo luôn ghi rõ mã nguồn nào sinh ra nó (bài học từ
  những lượt chạy bằng mã cũ ngày 04-09)

Docker Desktop đã cấu hình **tự khởi động cùng Windows** và container có
`restart: always` — sau khi khởi động lại máy, chỉ cần chờ ~1 phút là service
tự sống lại. Kiểm lại trước demo: `docker compose ps copilot`.

## 2. Lộ trình demo (≈ 10 phút)

### Bước 1 — Ý tưởng (1 phút)

Một câu thôi: *"Người xin cấp tài nguyên tự kiểm bản định cỡ Word trước khi nộp
bằng đúng bộ quy tắc mà người thẩm định sẽ dùng — 151 quy tắc số hoá từ Guideline,
checklist 57 mục và code web app. Công cụ chỉ CỐ VẤN, không phê duyệt."*

### Bước 2 — Nộp một bản thật qua API (3 phút)

Dùng hồ sơ BCCS 3.0 (thị trường Lào) đã có sẵn:

```bash
curl -X POST http://localhost:8902/review \
  -F "f=@<đường dẫn đến Sizing_BCCS3_thị_trường_Lào_23072024.docx>" \
  -F "chi_nhom=KPI" -F "chi_vong=1"
```

Chỉ trả ngay:

```json
{"id_job":"20260909-…","trang_thai":"cho","hỏi_kết_quả":"GET /result/20260909-…"}
```

**Điểm nói với sếp:** nộp xong là thoát — lượt chạy dài 15–30 phút chạy nền
trong container, client không phải chờ. Đây chính là mô hình tích hợp sau này
với web nội bộ (mục 3.3 trong kế hoạch).

### Bước 3 — Theo tiến độ từng lượt gọi (1 phút)

```bash
curl http://localhost:8902/result/<id_job>
```

Trường `tien_do` chạy theo từng lượt gọi model: `C3 20/21 · bảng #93 · Kafka`,
rồi `C5 19/99 · ARC-15/…` — người xem thấy công cụ đang làm gì từng giây, không
phải hộp đen.

### Bước 4 — Báo cáo (3 phút)

```bash
curl "http://localhost:8902/result/<id_job>?chi_bao_cao=true"
```

Hoặc mở sẵn bản mẫu: `data/tai_len/demo-bccs3-bao-cao.md` (lượt đã chạy thật:
**497 phát hiện** cho BCCS 3.0, Vòng 1: 71 mục chưa đạt).

Ba thứ phải chỉ trong báo cáo:

1. **Mỗi finding có căn cứ** — mã quy tắc + trích dẫn nguyên văn từ Guideline,
   hoặc con số do code tự tính (khung "Căn cứ: quy tắc …"). Không finding nào
   "cảm giác rằng".
2. **Xếp theo đúng thứ tự checklist thẩm định** — người thẩm định đối chiếu 1:1
   với chính công cụ họ đang dùng để chấm.
3. **Nói rõ phần CHƯA kiểm được** ("chưa kiểm được", "tạm hoãn") — công cụ không
   biết thì nói không biết, không bịa (nguyên tắc NT4). Phần Vòng 2 "chưa kiểm
   được" còn lớn vì **hồ sơ không nêu đủ tham số** — đó là phát hiện có hệ thống
   của dự án: 101 quy tắc định lượng cần 191 tham số riêng, trung vị một hồ sơ
   chỉ có 23 cột số liệu.

### Bước 5 — Số liệu và con đường tiếp theo (2 phút)

- Eval thật 09-09: 3 hồ sơ dev đầu — recall công bố **87,1%**, nhưng con số
  phải đọc là **nhóm "đòi tính/so số" 12%** (nhóm phân biệt được công cụ thật
  với công cụ sinh bừa). Nút thắt đã định vị: **trích xuất (C3)**, và đã có kế
  hoạch nhắm đúng 5 tham số gánh 19/57 nhãn nhóm này.
- Đường tới server thật: image đã build thành công trong mạng nội bộ với đủ ba
  cấu hình đặc thù (proxy, CA MITM, .commit) — chỉ còn chép qua server.

## 3. Câu hỏi có thể bị hỏi — và câu trả lời

| Câu hỏi | Trả lời |
|---|---|
| "Số 87,1% nghĩa là gì?" | Recall hào phóng (397/475 nhãn nhận gợi ý máy dư mã). Con số trung thực là nhóm "đòi tính/so số" — 12% lượt đầu, đang nhắm nâng lên ~37% bằng 5 tham số đã xác định. |
| "Báo sao có false positive?" | Chưa đo được — bản "đã ký" trong kho không sạch (lỗi còn nguyên). Cần người thẩm định chấm lại finding của Copilot trên 3–5 hồ sơ. |
| "Tại sao vòng 2 toàn 'chưa kiểm được'?" | Vì hồ sơ thật không nêu đủ tham số cho quy tắc (trung vị 23 cột số/hồ sơ so với 191 tham số cần) — `thieu_thong_tin` chính là giá trị cố vấn cho người viết. |
| "Deploy lên server mất bao lâu?" | Image đã build được trong mạng nội bộ (ba rào cản proxy/CA/git đã xử lý trong Dockerfile). Server chỉ cần Docker + `git pull` + `docker compose up`. |
| "AI có bịa số không?" | Có cổng chống bịa ba lớp: giá trị phải NEO được vào câu/bảng có thật trong tài liệu; trích dẫn không tìm lại được thì bị loại; không đặt được câu hỏi rải rác (C3 hỏi theo CỘT bảng). Model giả đạt 99,4% trên thước đo cũ nhưng **3,2%** trên thước đo thực chất — cổng là thật. |

## 4. Nếu demo trực tiếp trên giao diện web (tuỳ chọn)

```bash
docker exec sizing-copilot /app/.venv/bin/streamlit run ui/app.py \
    --server.port 8501 --server.address 0.0.0.0
```

Rồi mở `http://localhost:8502` trên máy của sếp (cần `-p 8502:8502` khi `docker
run` — hoặc dùng compose file riêng). Giao diện có 3 chế độ; hai chế độ đầu
(Đọc tài liệu, Điền checklist) chạy không cần model, phù hợp demo nhanh.
