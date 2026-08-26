# Đối chiếu Guideline lần ban hành 07 với bộ quy tắc hiện có

> **Ngày làm:** 2026-08-25
> **File mới:** `Guideline_Dinh_co_thiet_bi_CNTT_lan7_7.01.pdf` — 44 trang,
> mã hiệu GL.CNVTQĐ.CNTT.18, **lần ban hành 07**, hiệu lực **01/10/2023 → 01/10/2025**.
> **File cũ:** lần ban hành 06, hiệu lực 01/10/2021 → 01/10/2023 (đã trích trước đó,
> `docs/rules/.tmp/clean.txt`; bản PDF gốc không có trong repo).
>
> **Công cụ:** `scripts/extract_pdf_text.py` (trích + lọc watermark) và
> `scripts/diff_guideline.py` (so hai bản).

---

## Kết luận

**Lần 07 không làm thay đổi quy tắc nào trong 100 quy tắc đã số hóa.** Toàn bộ
ngưỡng, hệ số và công thức giữ nguyên. Không cần sửa `rules-flat-draft.md`,
`rules-classification.md`, `rules-formulas.md` hay `rules-criteria.md` về nội dung.

Nhưng có **một thứ được tuyên bố là đã thêm mà không tìm thấy trong tài liệu** —
xem mục 3. Đó là việc cần theo tiếp.

---

## 1. Kết quả so sánh

| Phép so | Giống nhau | Khối THÊM | Khối BỎ | Khối SỬA |
|---|---:|---:|---:|---:|
| Chỉ các dòng có số (ngưỡng, hệ số) | **97,9%** | 0 | 2 | 5 |
| Toàn văn | **97,6%** | 1 | 2 | 15 |

Toàn bộ khác biệt nằm ở phần **siêu dữ liệu và trình bày**, không có khác biệt nội dung:

| Loại khác biệt | Ví dụ | Ảnh hưởng quy tắc |
|---|---|---|
| Bảng chữ ký số đầu tài liệu | Bản 06 có trang chữ ký riêng; bản 07 đưa vào watermark | Không |
| Bảng lịch sử sửa đổi | Thêm 1 dòng ở đầu → các dòng dưới bị đánh số lại 1→2, 2→3… | Không |
| Mục lục | Số dấu gạch dưới lấp chỗ khác nhau | Không |
| Ngắt dòng khi trích | `Bộ / tiêu / chuẩn chất` vs `Bộ tiêu chuẩn / chất lượng` | Không |

**Đã kiểm riêng các hằng số then chốt — tất cả giữ nguyên:**
R17 (8.38 / 9.36 / 6.74 / 7.38) · R49 (0.75 / 0.9 / 0.8 / 1.1) · R57 (1.1 / 1.1 / 1.25) ·
R13 (≤ 32 vCPU, ≤ 128 GB RAM) · R68 (≥ 75%) · R94 (CPU ≤ 4, RAM ≤ 1.5) · R89 (÷ 38).

---

## 2. Ba điều tài liệu mới **không** có

### 2.1. Không có phần định cỡ server GPU

Tìm `GPU`, `NVIDIA`, `CUDA`, `Tensor`, `card đồ họa` trong toàn bộ 44 trang: **không
có kết quả nào**. Phần GPU nằm ở tài liệu khác, đúng như bạn nói sẽ gửi sau.

### 2.2. Vẫn không có Phụ lục 01 và Phụ lục 02

Mục lục lần 07 kết thúc ở `C. KIỂM THỬ HIỆU NĂNG HỆ THỐNG CNTT — trang 43`, trang
44 là trang cuối. Không có mục "Phụ lục" nào.

Nghĩa là hai vướng mắc cũ **vẫn còn nguyên**:
- **Phụ lục 01** (mẫu tài liệu định cỡ) — vẫn chặn quy tắc R34 và mục 1.16 (mẫu Word chuẩn).
- **Phụ lục 02** (bảng `Cint_rated`/`Cfp_rated` theo dòng CPU) — vẫn dùng quy ước
  thay thế đã chốt ở 0.3 (VM: 1 vCPU = 3; vật lý: `None`, tra `spec.org`).

Đáng chú ý: bảng lịch sử sửa đổi có dòng *"Hiệu chỉnh và bổ sung phụ lục cho SPEC
CPU int/float cho cả giá trị peak và base"* và *"Bổ sung phụ lục về hệ thống đánh
giá CPU"* — tức là **hai phụ lục đó có tồn tại**, chỉ là không nằm trong file PDF này.

### 2.3. Không có checklist — dù tài liệu nói là đã thêm

Xem mục 3.

---

## 3. ⚠️ Thay đổi duy nhất của lần 07 lại không tìm thấy trong tài liệu

Bảng lịch sử sửa đổi của lần 07 có đúng **một** dòng mang ngày hiệu lực 01/10/2023
(các dòng còn lại đều là thay đổi từ những lần ban hành trước):

> | 1 | Bổ sung checklist rà soát đánh giá nội dung định cỡ | 01/10/2023 |

Nhưng tìm `checklist`, `bảng kiểm`, `tiêu chí rà soát`, `danh mục kiểm` trong cả
`clean.txt` lẫn `raw-layout.txt`: **chỉ khớp đúng dòng lịch sử sửa đổi nói trên**.
Bản thân checklist không có trong 44 trang.

**Vì sao điều này quan trọng với dự án:** một "checklist rà soát đánh giá nội dung
định cỡ" chính là **danh mục kiểm của người thẩm định** — thứ gần nhất với đầu ra
mà Copilot cần sinh ra. Nó có giá trị hơn hẳn phần lớn nội dung còn lại của
Guideline đối với dự án này, vì:

- Nó cho biết người thẩm định **thực sự soi những gì**, theo thứ tự nào.
- Nó là căn cứ trực tiếp để xếp mức nghiêm trọng (`severity`) cho từng finding.
- Nó có thể trả lời gọn phần lớn 10 điểm `[CHƯA CHẮC]` còn treo ở `rules-formulas.md`.

→ **Đề nghị hỏi xin riêng file checklist này.** Cùng đợt với Phụ lục 01 và 02.

---

## 4. Thay đổi trong repo sau lần đối chiếu

### 4.1. Nguồn trích dẫn chuyển sang bản lần 07

| | Bản 06 (cũ) | Bản 07 (mới) |
|---|---|---|
| Đường dẫn | `docs/rules/.tmp/clean.txt` | `docs/rules/.tmp-lan7/clean.txt` |
| Số trang vật lý | 45 | 44 |
| Quan hệ trang | vật lý = trang in **+ 1** | vật lý = **trang in** |
| Ký tự `≤` `≥` | sai thành `£` `³` | đúng |
| Bullet | lẫn lộn `ü`, `` | thống nhất `-` |

**Hệ quả tốt:** cảnh báo lệch số trang ghi ở đầu `rules-criteria.md` **không còn
đúng nữa** — với nguồn mới, trang vật lý bằng trang in. Đã cập nhật lại file đó.

Bản 06 vẫn giữ trong repo để truy vết, không xóa.

### 4.2. Hai lỗi trích xuất đã phát hiện và sửa

Trong lúc làm, phát hiện hai lỗi **của script trích**, không phải khác biệt tài liệu:

1. **Quy mọi ký tự PUA về `-`.** Font Symbol dùng vùng Private Use Area cho **toán
   tử so sánh**: `U+F0A3` là `≤`, `U+F0B3` là `≥`. Cách làm ban đầu biến
   *"cần có ≤ 32 vCPU và ≤ 128GB RAM"* (R13) thành *"cần có - 32 vCPU"*, và
   *"dung lượng ≥ 75%"* (R68) thành *"- 75%"* — tức là **phá đúng những ngưỡng mà
   quy tắc định lượng dựa vào**. Đã sửa thành ánh xạ **theo font**, kèm cảnh báo khi
   gặp ký tự PUA chưa có trong bảng (không đoán bừa).
2. **Diff bị nhiễu bởi hình thức.** Hai lần trích ngắt span khác nhau nên khác biệt
   thuần khoảng trắng và bullet lấn át nội dung thật (ban đầu chỉ 79,6% giống nhau).
   Sau khi chuẩn hóa: 97,9%.

Bài học ghi lại cho lần sau: **luôn chạy `--probe-fonts` trước khi tin vào kết quả
trích**, và kiểm tra riêng `≤` `≥` `×` `÷` sau mỗi lần trích tài liệu mới.

### 4.3. File đã cập nhật

| File | Thay đổi |
|---|---|
| `scripts/extract_pdf_text.py` | Mới. Trích + lọc watermark theo font, ánh xạ PUA theo font |
| `scripts/diff_guideline.py` | Mới. So hai lần ban hành, bỏ nhiễu hình thức |
| `docs/rules/.tmp-lan7/` | Mới. Bản trích lần 07 — nguồn trích dẫn chính từ nay |
| `config/rules.yaml` | `sources` cập nhật sang lần 07; ghi nhận checklist còn thiếu |
| `docs/rules/rules-criteria.md` | Bỏ cảnh báo lệch trang; trỏ nguồn sang bản lần 07 |
| `docs/rules/rules-crossmap.md` | Cập nhật mục 0 (vấn đề hiệu lực đã được giải quyết) |
| `PLAN.md` | Cập nhật 0.12 |

---

## 5. Việc còn phải làm

- [ ] **Xin file checklist rà soát đánh giá nội dung định cỡ** (mục 3) — giá trị cao nhất
- [ ] Xin **Phụ lục 01** (mẫu tài liệu định cỡ) — chặn R34 và mục 1.16
- [ ] Xin **Phụ lục 02** (bảng `Cint_rated`) — có quy ước thay thế nên không chặn
- [ ] Nhận tài liệu **định cỡ server GPU** → mở lại 0.1–0.4 cho riêng phần đó
- [ ] Kiểm lại số trang trong `rules-formulas.md` (74 quy tắc định lượng): đang dùng
      số trang vật lý của bản 06, tức lệch 1 so với trang in. Sửa đồng loạt ở mục 0.5.
