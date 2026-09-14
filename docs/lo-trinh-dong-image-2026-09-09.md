# Lộ trình tới đóng image và chạy thử trên server thật

> Lập ngày 2026-09-09. Mọi con số dưới đây là **đo được**, không ước theo cảm giác;
> chỗ nào chưa đo thì ghi rõ là chưa đo.

---

## 1. Đang ở đâu

| GĐ | Tên | Xong | Nhận xét |
|----|-----|------|----------|
| 0 | Chuẩn bị tri thức & dữ liệu | 11/13 | đủ dùng |
| 1 | MVP xử lý text | 14/17 | **1.13 chưa đạt** — chưa từng chạy đủ một lượt dev |
| 2 | Đa phương thức | 7,5/14 | 2.1 · 2.2 · 2.3 · 2.5 · 2.6 · 2.12 xong |
| 3 | Tích hợp & tinh chỉnh | **0/11** | chưa bắt đầu — đây là toàn bộ phần triển khai |
| 4 | Vận hành | 0/6 | sau khi chạy thật |

Đường chạy C1 → C2 → C3 → C4 → C5 → C7 **thông suốt**, 477 unit test.
`ui/app.py` (Streamlit) chạy được. Thư mục `api/` **rỗng**.

`docker-compose.yml`, `backend1/`, `nginx/`, `frontend/` trong repo là **web app
nội bộ sẵn có (Spring Boot)**, KHÔNG phải Copilot. Copilot chưa có Dockerfile nào.

---

## 2. Con số quyết định cách triển khai: **~30 phút cho MỘT tài liệu**

Đếm offline trên bộ quy tắc hiện tại và một hồ sơ thật (VTracking):

| Thành phần | Số lượt gọi model |
|---|---:|
| C3 trích xuất | 43 nhóm → **43 lượt** |
| C5 định tính | 48 quy tắc (30 hệ thống + 18 × số phân hệ) → **138 lượt** với 6 phân hệ |
| C2 đọc ảnh | 58 ảnh → **58 lượt** |
| | **≈ 239 lượt / tài liệu** |

Đối chiếu tốc độ thật đo trên máy nội bộ 2026-09-09 (649 lượt · 90 phút · song
song 6): **≈ 8,3 giây/lượt tính theo đồng hồ**.

> **239 × 8,3 s ≈ 33 phút cho một tài liệu.**

Hệ quả bắt buộc, không thương lượng được:

1. **Không thể trả kết quả đồng bộ.** `ui/app.py` hiện gọi thẳng `chay()` và
   chặn cho tới khi xong — người dùng thật sẽ ngồi nhìn màn hình 30 phút. Phải
   có việc chạy nền + mã theo dõi (mục 3.2).
2. **Mức song song là đòn bẩy lớn nhất.** Thời gian gần như tỉ lệ nghịch với nó.
   Song song 6 → 33 phút; nếu gateway chịu được 24 → **≈ 8 phút**. Chưa đo trần
   của gateway — đây là phép đo rẻ nhất và đáng làm sớm nhất.

---

## 3. Các bước tới image + deploy thử

Ước lượng tách làm hai loại, vì chúng **không đổi cho nhau được**:
**Người** = việc viết code (làm trên laptop) · **Máy** = giờ chạy trên máy nội bộ
(phải có người bấm, laptop không có model).

### A. Bắt buộc để đóng được image chạy thật

| # | Việc | Người | Máy | Ghi chú |
|---|------|------:|----:|---|
| A1 | `Dockerfile` + `.dockerignore` | 0,5 ngày | — | **Phải loại `danh_sach_sizings_da_duyet/` (52 file .docx hồ sơ thật), `data/`, `.cache/` khỏi image** — vừa nặng vừa là dữ liệu nội bộ |
| A2 | `config/settings.yaml` cho container; khoá API qua biến môi trường | 0,25 ngày | — | đã có `settings.example.yaml`; khoá KHÔNG được nằm trong image |
| A3 | Smoke test container bằng **model giả** (`--gia-lap`) | 0,25 ngày | — | chạy được ngay trên laptop, không cần model |
| A4 | Đo trần song song của gateway | 0,25 ngày | **1–2 h** | quyết định 33 phút hay 8 phút/tài liệu |
| | **Cộng A** | **1,25 ngày** | **1–2 h** | |

Sau A: **có image chạy được**, nhưng chỉ đủ cho người trong đội dùng.

### B. Bắt buộc để người NGOÀI đội dùng được

| # | Việc | Người | Máy | Ghi chú |
|---|------|------:|----:|---|
| B1 | 3.1 — API FastAPI `POST /review` · `GET /result/{id}` | 1,5 ngày | — | `api/` đang rỗng; phụ thuộc `api` đã khai trong `pyproject.toml` |
| B2 | 3.2 — chạy nền + trạng thái công việc | 1,5 ngày | — | **bắt buộc vì 30 phút/tài liệu**, không phải tuỳ chọn |
| B3 | Streamlit gọi API thay vì gọi thẳng `chay()` | 0,5 ngày | — | kèm thanh tiến độ theo `on_tien_do` đã có sẵn |
| B4 | 2.14 — C7 chịu được bản NHÁP chưa hoàn chỉnh | 1 ngày | — | người dùng thật nộp bản chưa xong; phải phân biệt *"người viết chưa làm"* với *"công cụ không đọc được"* |
| B5 | 3.9 — hướng dẫn sử dụng 1–2 trang | 0,5 ngày | — | cho người không chuyên |
| | **Cộng B** | **5 ngày** | — | |

### C. Bắt buộc để DÁM công bố con số chất lượng

| # | Việc | Người | Máy | Ghi chú |
|---|------|------:|----:|---|
| C1 | Chờ người thẩm định chốt cách xếp nhóm nhãn | — | — | **đã gửi 2026-09-09**, đang chờ |
| C2 | 1.13 — đo biên độ trên 3 hồ sơ cố định × 3 lượt | 0,25 ngày | **4,5 h** | phải bỏ đệm, nếu không mọi lượt ra kết quả y hệt |
| C3 | 1.13 — một lượt dev đầy đủ 14 hồ sơ | 0,25 ngày | **7 h** | con số công bố được |
| C4 | 3.7 — soi false positive, siết chỗ sai lặp lại | 1–2 ngày | — | phụ thuộc kết quả C3 |
| | **Cộng C** | **1,5–2,5 ngày** | **11,5 h** | |

### D. CHƯA cần cho lượt chạy thử đầu tiên

Nói rõ để khỏi ai chờ:

- **1.11 RAG + Qdrant** — C5 hiện chạy tốt không cần; hoãn được.
- **2.7 / 2.8 / 2.9 C6 tìm bản tương tự** — đang bị chặn bởi 0.13, không nằm trên
  đường tới image.
- **3.6 tập kiểm tra giữ kín** — chỉ được chạy **một lần**. Chạy sớm là phí. Để
  sau khi C4 (soi false positive) đã ổn định.
- **3.3 nút "Kiểm tra sizing" trong web nội bộ** — cần API (B1) chạy ổn trước.

---

## 4. Tổng và hai đường đi

| Đường | Gồm | Người | Máy nội bộ |
|---|---|---:|---:|
| **Ngắn** — image cho đội tự dùng | A | **1,25 ngày** | 1–2 h |
| **Đủ** — người ngoài dùng được | A + B | **6,25 ngày** | 1–2 h |
| **Công bố được số** | A + B + C | **7,75–8,75 ngày** | **12,5–13,5 h** |

**Đề xuất: đi đường Ngắn trước**, ngay tuần này. Lý do là đo được chứ không phải
sở thích: mục A4 (trần song song) quyết định 33 phút hay 8 phút mỗi tài liệu, mà
con số đó lại quyết định B2 phải làm tới đâu. Đóng image sớm để lấy con số đó về
rẻ hơn nhiều so với thiết kế hàng đợi trước rồi mới biết mình thiết kế cho sai
mức tải.

---

## 5. Rủi ro phải nói trước

1. **30 phút/tài liệu** là rủi ro lớn nhất về trải nghiệm. Nếu gateway không cho
   nâng song song, phải cắt bớt phạm vi mỗi lượt (ví dụ tách C2 đọc ảnh thành
   tuỳ chọn) — và đó là đánh đổi chất lượng, phải do người quyết.
2. **Chưa từng chạy đủ một lượt dev.** Mọi con số recall đang có đều từ 3/14 hồ
   sơ và **có lọc**. Không được trích chúng như recall thật.
3. **Rò tập test đã khai báo** — một cửa chặn của phép kiểm hệ số dự phòng
   (2026-09-09) sinh ra từ tài liệu hồ sơ Mykid thuộc tập test. Con số ở 3.6 phải
   nêu kèm hạn chế này.
4. **Dữ liệu nội bộ trong repo.** 52 file `.docx` hồ sơ thật + nhãn PNX đang nằm
   trong cây mã nguồn. `.dockerignore` phải loại chúng, và cần soát lại xem image
   có vô tình mang theo gì không trước khi đẩy lên registry.
5. **Bộ quy tắc còn 8 mục `lookup:` và vài chỗ `"[CHƯA CHẮC]"`** trong
   `rules.yaml` chờ người thẩm định duyệt. Không chặn việc đóng image, nhưng chặn
   việc gọi kết quả là "đúng theo Guideline".
