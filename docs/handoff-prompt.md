# Prompt bàn giao sang phiên mới

> **Chép thẳng nội dung từ dấu `---` trở xuống vào ô chat**, đừng bảo Claude "đọc file
> này". Trỏ file thì Claude phải gọi Read, nội dung vẫn vào context y hệt mà còn tốn
> thêm phần bao của lệnh gọi — và có thêm một bước có thể hỏng. Dán thì chắc chắn đọc.
>
> Cập nhật lại file này mỗi khi bàn giao.
> **Lần cập nhật gần nhất: 2026-08-26** — kết thúc mục 0.5 (150 quy tắc) + đối chiếu
> quy tắc với hồ sơ thẩm định thật. Phiên mới sẽ nhận **≥ 20 hồ sơ sizing thật**.

---

Dự án **Sizing Copilot**. Giai đoạn 0 (chuẩn bị tri thức) đã xong phần tri thức;
đang vướng phần **dữ liệu**. Tôi sắp cung cấp **≥ 20 hồ sơ sizing thật** để gỡ vướng.
Đọc hết phần dưới trước khi làm gì.

## 0. Việc sắp tới — vì sao phiên này quan trọng

Mục 0.1–0.5 đã xong: `config/rules.yaml` có **đủ 150 quy tắc**, validator sạch.
Mục **0.6, 0.7, 0.8 đang BỊ CHẶN** vì thiếu dữ liệu, kéo theo 1.5, 1.7, 1.13, 2.6,
2.7 và cả thành phần **C6**.

**Tôi sẽ đưa ≥ 20 hồ sơ sizing thật.** Việc của phiên này là dùng chúng gỡ chặn
0.6 → 0.9 theo đúng `PLAN.md`, rồi mở đường sang Giai đoạn 1.

⚠️ **Hỏi tôi trước khi bắt đầu xử lý:** mỗi hồ sơ gồm những file gì? Cụ thể có kèm
**PNX (Phiếu Nhận Xét của Phòng Hệ thống)** không, và có **checklist `.xlsx`** đã
chấm OK/NOK không. Câu trả lời quyết định hoàn toàn cách làm mục 0.7 — xem mục 4 dưới.

## 1. Đọc bắt buộc, theo thứ tự

Đọc **đúng phạm vi** ghi ở cột "Đọc phần nào" — vài file rất dài, đọc trọn là phí context.

| # | File | Đọc phần nào | Vì sao |
|---|---|---|---|
| — | `CLAUDE.md` | **KHÔNG cần Read** | Harness tự nạp. 4 nguyên tắc NT1–NT4 + cạm bẫy — không được vi phạm |
| 1 | `PLAN.md` | Toàn bộ | Trạng thái từng mục + **Nhật ký quyết định** (rất nhiều thứ đã chốt, đừng bàn lại) |
| 2 | `docs/rules/rules-id-map.md` | Bảng tổng hợp 16 nhóm ở đầu + mục "quy tắc KHÔNG vào rules.yaml" | **Mã quy tắc là CỐ ĐỊNH**, đổi là hỏng liên kết eval set |
| 3 | `config/rules.yaml` | **Chỉ phần đầu tới hết `globals`** (~250 dòng) | Lược đồ + hằng số dùng chung. Phần `rules:` 4.300 dòng — chỉ đọc quy tắc cụ thể khi cần |
| 4 | `docs/rules/rules-doi-chieu-thuc-te.md` | Toàn bộ (~150 dòng) | Đối chiếu 150 quy tắc với hành vi thẩm định thật — **9 khoảng trống** |
| 5 | `docs/rules/checklist-tham-dinh.md` | **Chỉ mục 2.3** | Mô hình **hai vòng thẩm định** — nền của toàn bộ thiết kế |

Đọc thêm **khi cần**, không đọc trước: `docs/ke-hoach-trien-khai.md` (bối cảnh đầy đủ) ·
`rules-formulas.md` (77 công thức ĐL) · `rules-criteria.md` (30 tiêu chí ĐT) ·
`rules-checklist-flat.md` · `rules-crossmap.md` · `rules-nguon-khac.md` ·
`0.1-danh-sach-quy-tac.md` · `0.7-nguon-nhan-vang.md` *(⚠️ tiền đề đã đổ, xem mục 3)*.

## 2. Đã có gì — trạng thái Giai đoạn 0

| Mục | Trạng thái |
|---|---|
| 0.1 danh sách phẳng (4 nguồn) | ✅ |
| 0.2 phân loại & tỷ lệ | ✅ |
| 0.3 công thức định lượng | ✅ 77 quy tắc — `rules-formulas.md` |
| 0.4 tiêu chí định tính | ✅ 30/30 — `rules-criteria.md` |
| 0.5 số hóa `rules.yaml` | ✅ **150/150 quy tắc**, validator sạch |
| **0.6 chuẩn hóa hồ sơ lịch sử** | 🔴 **BỊ CHẶN** — sắp gỡ |
| **0.7 nhãn vàng eval set** | 🔴 **BỊ CHẶN** — sắp gỡ, nhưng **phải đổi cách làm** |
| **0.8 chia dev/test** | 🔴 **BỊ CHẶN** — sắp gỡ |
| 0.9 baseline | 🟡 có số vòng TB = 1,92 (gián tiếp); thiếu thời gian mỗi vòng |
| 0.10 xác minh hạ tầng | ⬜ chưa làm |
| 0.11 chốt đọc bản Word nào | ⬜ **chưa chốt — chặn mục 1.3** |
| 0.12 tài liệu còn thiếu | 🟡 còn chờ 849/QĐ, Guideline zone, Guideline bền vững, Phụ lục 01 |
| 0.13 thu thập hồ sơ thật *(mới)* | 🔴 **đang gỡ bằng ≥ 20 hồ sơ sắp đưa** |

**Bộ quy tắc `config/rules.yaml`:**
150 quy tắc · 101 định lượng / 49 định tính · 131 Vòng 2 / 19 Vòng 1 ·
37 `critical` / 80 `major` / 33 `minor` · 4 quy tắc `enabled: false` ·
19 quy tắc mang điểm `[CHƯA CHẮC]` · 20 quy tắc `source_doc: "Quy ước nội bộ — chưa
có văn bản"`.

16 nhóm mã: `ALC 5 · ARC 27 · BAK 11 · CPU 11 · EVD 22 · FWL 4 · KPI 16 · LAN 4 ·
LBA 2 · MTH 4 · PRC 10 · RAM 3 · RCK 3 · SAN 2 · STO 23 · TST 3`.

**Bốn nguồn quy tắc** (196 thô → 150 sau khử trùng):
1. **Guideline** GL.CNVTQĐ.CNTT.18 **lần 07**, 44 trang → 110 quy tắc `R01–R110`
2. **Code web app** (`frontend/script.js`) → 46 quy tắc → 20 giữ riêng, 19 gộp, 7 loại
3. **Checklist thẩm định** (57 mục Excel) → 37 quy tắc `CL-*` → 19 mới, 18 chỉ gắn `checklist_ref`
4. **Văn bản khác** → `QD849-01`, `QD849-02`, `ZONE-01`

**Công cụ trong `scripts/`:**

| Script | Việc | Ghi chú |
|---|---|---|
| `validate_rules.py` | Kiểm `rules.yaml`: lược đồ, enum, NT1/NT2/NT3, tiêu chí mơ hồ | **Chạy sau mỗi lần sửa.** `--coverage` in tiến độ |
| `build_rule_ids.py` | Sinh bảng mã `rules-id-map.md`, có kiểm đầy đủ tự động | Dùng một lần, giữ làm tài liệu |
| `check_page_consistency.py` | Đối chiếu số trang giữa 3 file quy tắc | Chạy lại sau mỗi lần đụng số trang |
| `unify_page_numbers.py` | Đã quy mọi số trang về **số trang IN** | ⚠️ **CHỈ CHẠY MỘT LẦN — đã chạy rồi.** Chạy lại sẽ trừ tiếp và làm sai |
| `extract_appraisal_issues.py` | Trích 667 vấn đề từ `approved-sizing/` | |
| `map_appraisal_to_rules.py` | Đối chiếu vấn đề thật ↔ 150 quy tắc | Sửa bảng `THEMES` trong script rồi chạy lại |
| `extract_pdf_text.py` · `diff_guideline.py` · `extract_checklist.py` · `audit_rule_coverage.py` | Công cụ giai đoạn trước | |

## 3. Hai tiền đề ĐÃ ĐỔ — đọc kỹ, đừng lặp lại giả định cũ

**(a) `docs/0.7-nguon-nhan-vang.md` không dùng được lúc này.** File đó xây trọn trên
giả định *"DB web app đã lưu sẵn lỗi người thẩm định ở cột `project_data.*_admin_review`"*.
Xác nhận 2026-08-26: **DB chưa có bất kỳ dữ liệu phê duyệt lịch sử nào.** Hồ sơ cũ là
bản làm **thủ công**, chưa từng qua web app. Đã ghi cảnh báo ở đầu file đó; giữ phần
còn lại làm thiết kế cho tương lai.

**(b) `approved-sizing/` không có bản gốc.** Thư mục đó chỉ còn **53 file `.md`** —
tóm tắt do một AI khác (Cline) trích từ 50 hồ sơ đã ký, bản gốc `.docx`/`.pdf` **không
còn**. Có lỗi trích xuất thấy được (`sởffff`, `THÔNG SỐ KỨ THUẬT`).
→ **ĐÃ CHỐT: không dùng 50 file này làm nhãn vàng** (vi phạm NT2, recall sẽ ảo).
→ Đã dùng chúng cho việc khác, hợp lệ: **soi lại độ phủ bộ quy tắc** (mục 5 dưới).

## 4. Việc phải làm với ≥ 20 hồ sơ sắp đưa

**Trước tiên hỏi tôi hồ sơ gồm file gì** (xem mục 0). Rồi đi theo `PLAN.md`:

**0.6 — chuẩn hóa.** Đặt tên thống nhất + bảng metadata mỗi hồ sơ: loại sizing
(mới / bổ sung / nâng cấp / ứng cứu), ngày, đơn vị, mã PYC, người thẩm định, số vòng,
trạng thái ký. Ghi rõ hồ sơ nào thiếu file gì — **không đoán**.

**0.7 — nhãn vàng. ĐÂY LÀ MỤC PHẢI THIẾT KẾ LẠI.** Kế hoạch cũ lấy nhãn từ DB, nay
DB rỗng. Nguồn nhãn mới **phải là PNX đi kèm hồ sơ** — nguyên văn người thẩm định.
Cần viết lại quy trình: mỗi ý kiến trong PNX → một nhãn, neo vào vị trí trong tài liệu,
rồi **người nghiệp vụ gán `rule_ref`** (mã trong 150 quy tắc).
⚠️ Bước gán `rule_ref` **không giao cho AI** — đây là quyết định đã chốt. Sai ở bước
này thì mọi con số recall về sau đều vô nghĩa.
Nếu hồ sơ **không kèm PNX** thì nói thẳng là không dựng được eval set, đừng chế nhãn.

**0.8 — chia tập.** ~2/3 phát triển, ~1/3 kiểm tra **GIỮ KÍN**. Chia theo đơn vị
(`dev_unit`), **không** chia ngẫu nhiên — tránh rò rỉ văn phong cùng một đơn vị.

**0.9 — baseline.** Đo số vòng phản hồi TB + thời gian TB mỗi vòng **từ hồ sơ thật**.
Con số hiện có (**1,92 vòng**) là gián tiếp từ 50 file `.md`, dùng để đối chiếu.
**Phải chụp baseline trước khi Copilot đi vào sử dụng.**

**0.11 — chốt Copilot đọc bản Word nào** (bản người dùng tự viết hay bản web app xuất
ra). Nay có hồ sơ thật thì trả lời được. **Chặn mục 1.3.**

Sau đó mới sang Giai đoạn 1 (1.1 → 1.17).

## 5. Kết quả đối chiếu quy tắc với thẩm định thật — 9 khoảng trống

Đã đối chiếu **667 vấn đề / 50 hồ sơ** với 150 quy tắc
(`docs/rules/rules-doi-chieu-thuc-te.md`). **75/150 quy tắc được thực tế xác nhận**;
đứng đầu là `ARC-09` (dự phòng N+M, 64 lần), `FWL-04` (bắt buộc định cỡ FW/LB, 61 lần),
`PRC-01`/`PRC-02` (sở cứ có văn bản, 54 lần).

**9 chủ đề người thẩm định bắt mà không quy tắc nào phủ** — ba cái đầu **thuần code
kiểm được**, đáng thành quy tắc định lượng:

| Khoảng trống | Số lần / hồ sơ |
|---|---|
| Nhất quán chu kỳ lưu trữ giữa các phân vùng (`/data` 2 năm vs `/log` 6 tháng vs `/backup` 4 ngày) | 31 / 13 |
| Kiểm hợp lý đơn vị số liệu đầu vào (ca thật: "3.000.000 TB cho 1.080 người dùng") | 14 / 9 |
| Định cỡ GPU / tải AI | 11 / 4 |
| Sở cứ cho tốc độ tăng trưởng dữ liệu | 10 / 6 |
| Làm tròn và độ chính xác số trung gian | 8 / 4 |
| Phải trình bày công thức, không chỉ kết quả | 6 / 5 |
| Sizing phần mềm bên thứ ba / vendor | 5 / 2 |
| Cấp bổ sung phải tính phần TĂNG THÊM, không phải TỔNG | 3 / 2 |
| Sizing ứng cứu khẩn cấp (luồng VTNet UCTT riêng) | 3 / 1 |

⚠️ **CHƯA quyết** có bổ sung quy tắc cho các khoảng trống này không — thêm quy tắc là
mở lại 0.1–0.4 và **phải có tôi duyệt**. Bộ 150 quy tắc giữ nguyên cho tới lúc đó.

## 6. Quyết định ĐÃ CHỐT — đừng bàn lại

- **Thẩm định chạy HAI VÒNG nối tiếp.** Vòng 1 = checklist, chỉ hỏi *"thành phần cần
  có đã có chưa"*, tiêu chí mặc định *"có thông tin thực chất là ĐẠT"*. Vòng 2 =
  Guideline, kiểm cách tính. **C7 CHẶN finding Vòng 2 cho mục đã trượt Vòng 1.**
- **Đường vào chính là file `.docx`**, không phải JSON của web app.
- **Copilot KHÔNG phải trợ lý soạn thảo từng bước** — là bước kiểm trước khi nộp.
- **Mã quy tắc `<NHÓM>-<số>` là CỐ ĐỊNH**, `legacy_ref` giữ mã cũ `Rxx`/`CL-*` để truy vết.
- **Nhóm mã theo chủ đề/thiết bị, KHÔNG theo module phần mềm** — module đi vào
  `applies_to_module` (quyết định "hai trục").
- **KHÔNG số hóa 4 công thức code đang chạy sai** (`RDS-04`, `RDS-10`, `LBF-01`,
  `LBF-02`) — số hóa theo Guideline cho đúng. `rules.yaml` là bộ quy tắc để KIỂM,
  không phải bản chép hiện trạng.
- **`check` cho bất đẳng thức, `formula` cho phép tính lại** — không dùng đồng thời.
- **`applies_when`** cho quy tắc loại trừ nhau (4 quy tắc `MTH` Dạng I/II/III).
- **`scope`**: `he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru`.
- **`equipment_types`** có thêm `tat_ca` (mọi thiết bị) và `tai_lieu` (yêu cầu về cấu
  trúc tài liệu) — ~21 quy tắc không gắn được thiết bị nào.
- **Số trang đã thống nhất về SỐ TRANG IN** cho cả R01–R110.
- **R66 là định lượng** (không phải định tính).
- `QD849-01`: `đặc biệt quan trọng` ⟺ có DC-DR, hai chiều, hai kiểu vi phạm đều `critical`.

## 7. Cạm bẫy kỹ thuật — đã mất thời gian vì chúng

- **`unify_page_numbers.py` CHỈ CHẠY MỘT LẦN — đã chạy.** Tôi từng chạy lại nhầm và
  trừ hai lần cho bảng trong `rules-classification.md`, phải cộng bù +1 cho 100 dòng.
- **Nguồn trích dẫn chính thức: `docs/rules/.tmp-lan7/clean.txt`** (Guideline lần 07).
- Khi đối chiếu trích dẫn phải chuẩn hóa: **nháy cong** `“”` → `"`, và **từ bị ngắt
  ngang dòng tại dấu gạch nối** (`active-` / `standby` → `active-standby`, không dấu cách).
- **Ký tự PUA** (U+E000–U+F8FF) của font Symbol/Wingdings: `U+F0A3` là `≤`, `U+F0B3`
  là `≥` — **không phải bullet**. Quy về `-` sẽ phá hỏng ngưỡng.
- **YAML khối `>`**: dòng thụt sâu hơn dòng đầu sẽ **giữ nguyên xuống dòng**, làm hỏng
  biểu thức `check`/`formula` nhiều dòng. Giữ mọi dòng nối cùng mức thụt lề.
- File `frontend/script.js` có **mojibake UTF-8** ở vài chỗ (`case 'KhÃ¡c':`).
- Ô **A42** của checklist Excel ghi `3.1.2` nhưng phải là `3.2`. Dòng 18 và dòng 50
  thiếu số thứ tự → đã đặt `CL-2.10a`, `CL-3.2.7a`. Ô Ghi chú dòng 5 bị **cắt cụt**.
- Khi chạy Python in tiếng Việt trên Windows: đặt `PYTHONIOENCODING=utf-8`.
- **Bash tool ở máy này không chạy được heredoc dài / `python -c` nhiều dòng** — viết
  ra file rồi chạy, hoặc dùng Write.
- Đường dẫn `/tmp/...` trong Python **không hoạt động** (Windows map khác Bash) —
  dùng đường dẫn tương đối trong repo.

## 8. Ba lỗi tính toán đang chạy thật trên web app

Độc lập với Copilot, nên báo đội bảo trì (`rules-crossmap.md` mục 2):

| Mã | Lỗi | Hệ quả |
|---|---|---|
| **C-01** | Redis dùng `Kkpi = 0.8` cho RAM thay vì `0.9` | RAM dư ~12,5% |
| **C-02** | Redis áp hệ số KPI và sai số **hai lần** | RAM dư ~22% |
| **C-06** | LB/FW không áp `Kdph = 1.2` | Băng thông **thiếu 20%** |

## 9. Câu hỏi còn treo với đơn vị thẩm định

- CPU/RAM/IOPS tính **"mỗi request"** (checklist) hay **"mức hệ thống"** (Guideline)
  hay **`factor = định cỡ/POC`** (web app)? Ba cách phân rã.
- Mức `bình thường` có bắt buộc cơ chế dự phòng nội site nào không? (`ARC-12`)
- Khai dự phòng **cao hơn** mức yêu cầu — có cảnh báo lãng phí không? (`ARC-12`)
- **Dung sai** khi so tổng toàn hệ với tổng các phân hệ? (`EVD-10`, đang đề xuất
  `≤ 1 đơn vị` hoặc `≤ 0,5%`)
- `R104` — Guideline liệt kê 11 yếu tố ảnh hưởng, có tập **tối thiểu bắt buộc** không?
- `CL-1.2` (mức độ SR) có nằm trong tài liệu sizing không, hay ngoài phạm vi Copilot?
  (`PRC-08` đang `enabled: false`)
- **Khâu cấp phát không có mục checklist nào phủ** — `EVD-02`, `PRC-06`, `ALC-04`,
  `ALC-05` không map được. Cố ý hay thiếu sót?
- Nguồn của **KPI Datanode ≤ 50%** và các ngưỡng Redis/Kafka/MariaDB nội bộ?
- Mâu thuẫn **tăng trưởng 01 năm** (web app) ↔ **cấp phát 06 tháng** (`ALC-01`/R93)?
- Ba lỗi tính toán ở mục 8 — đã báo đội bảo trì chưa?

## 10. Cách làm việc mong muốn

- Làm theo thứ tự `PLAN.md`, không nhảy cóc. Xong mục nào tick mục đó và ghi kết quả.
- Gặp chỗ mơ hồ hoặc mâu thuẫn trong tài liệu thì **nêu ra, không tự quyết**.
- Mọi trích dẫn phải **kiểm khớp nguyên văn** với nguồn trước khi dùng.
- Việc gì máy kiểm được thì viết script kiểm, đừng tin mắt — đã bắt được nhiều lỗi
  nhờ vậy (3 quy tắc sót khi gán mã, khớp nhầm khi đối chiếu, trừ trang hai lần).
- Sửa `rules.yaml` xong **luôn chạy `validate_rules.py`**.
- Không tự thêm/xóa quy tắc, không tự đổi `severity` — phải hỏi tôi.
