# Prompt bàn giao sang phiên mới

> **Chép thẳng nội dung dưới đây vào ô chat**, đừng bảo Claude "đọc file này".
> Trỏ file thì Claude phải gọi Read, nội dung vẫn vào context y hệt mà còn tốn thêm
> phần bao của lệnh gọi — và có thêm một bước có thể hỏng. Dán thì chắc chắn đọc.
>
> Cập nhật lại file này mỗi khi bàn giao, để lần sau không phải viết lại.
> **Lần cập nhật gần nhất: 2026-08-26** (kết thúc mục 0.2).

---

Dự án Sizing Copilot. Tôi đang ở **Giai đoạn 0** (chuẩn bị tri thức), cần bạn tiếp
tục đúng chỗ đang dở. Đọc theo thứ tự dưới đây trước khi làm gì.

## 1. Đọc bắt buộc, theo thứ tự

**Đọc đúng phạm vi ghi ở cột "Đọc phần nào"** — vài file rất dài, đọc trọn là phí context.

| # | File | Đọc phần nào | Vì sao |
|---|---|---|---|
| — | `CLAUDE.md` | **KHÔNG cần Read** | Harness tự nạp mỗi phiên. 4 nguyên tắc NT1–NT4 và các cạm bẫy — không được vi phạm |
| 1 | `PLAN.md` | Toàn bộ | Trạng thái từng mục + **Nhật ký quyết định** (nhiều thứ đã chốt, đừng bàn lại) |
| 2 | `docs/rules/rules-flat-draft.md` | **Chỉ mục "BỔ SUNG"** ở cuối | R101–R110 — chính là việc phải làm |
| 3 | `docs/rules/rules-criteria.md` | **Chỉ mục 4 và 4b** | Khuôn viết tiêu chí đã duyệt + 3 mẫu. *(Cả file dài ~1.300 dòng, đừng đọc hết)* |
| 4 | `docs/rules/rules-formulas.md` | **Vài mục `### Rxx` bất kỳ** | Khuôn viết công thức |
| 5 | `docs/rules/checklist-tham-dinh.md` | Mục 2.3 | **Mô hình hai vòng** — nền của toàn bộ thiết kế |

Đọc thêm **chỉ khi cần**: `rules-crossmap.md` (quan hệ bốn nguồn),
`rules-classification.md` PHẦN 2 (tỷ lệ chốt), `rules-checklist-flat.md`,
`rules-nguon-khac.md`, `rules-lan7-doi-chieu.md`, `docs/0.1-danh-sach-quy-tac.md`,
`docs/0.7-nguon-nhan-vang.md`, `docs/ke-hoach-trien-khai.md`.

## 2. Trạng thái Giai đoạn 0

| Mục | Trạng thái |
|---|---|
| 0.1 danh sách phẳng | ✅ xong — 4 nguồn |
| 0.2 phân loại & tỷ lệ | ✅ xong |
| **0.3 công thức định lượng** | 🟡 **dở — việc tiếp theo** |
| **0.4 tiêu chí định tính** | 🟡 **dở — việc tiếp theo** |
| 0.5 → 0.12 | ⬜ chưa bắt đầu |

**Bốn nguồn quy tắc** (mọi mục 0.1–0.4 phải phủ cả bốn):

1. **Guideline** GL.CNVTQĐ.CNTT.18 lần 07 → **110 quy tắc** `R01–R110` (77 ĐL / 33 ĐT)
2. **Code web app hiện hành** → 46 quy tắc (`KPI-01`, `MDB-01`…)
3. **Checklist thẩm định** → 37 quy tắc `CL-*` — **toàn bộ là Vòng 1**
4. **Văn bản khác** → `QD849-01`, `QD849-02`, `ZONE-01`

## 3. VIỆC TIẾP THEO — hoàn tất 0.3 và 0.4 cho 10 quy tắc mới

Mục 0.2 rà lại độ phủ và phát hiện **10 quy tắc bị sót** khỏi danh sách 100 ban đầu.
Chúng đã được ghi ở `docs/rules/rules-flat-draft.md` mục **"BỔ SUNG"** nhưng
**chưa có công thức / tiêu chí**.

**a) Mục 0.3 — viết công thức cho 2 quy tắc định lượng**, thêm vào `rules-formulas.md`
theo đúng khuôn các quy tắc đã có ở đó:

- **R101** — cơ chế dự phòng bắt buộc theo mức độ quan trọng: `active-active` với hệ
  *Rất quan trọng trở lên*, `active-standby` với hệ *Quan trọng*. Là ánh xạ enum→enum.
- **R105** — định cỡ ở cả hai mức (toàn hệ thống **và** từng module); bảng tổng hợp
  toàn hệ = tổng hợp kết quả từng module. Là kiểm nhất quán số.

**b) Mục 0.4 — viết tiêu chí cho 8 quy tắc định tính**, thêm vào `rules-criteria.md`
mục 5, **đúng khuôn đã duyệt** (xem 3 mẫu ở mục 4 của file đó):
`R102`, `R103`, `R104`, `R106`, `R107`, `R108`, `R109`, `R110`.

Khuôn bắt buộc mỗi quy tắc: `legacy_ref` · `checklist_ref` · trang · nhóm kiểm (A/B/C) ·
`applies_to_equipment` · `severity` · **Trích dẫn nguyên văn** · Phạm vi áp dụng ·
**KHÔNG áp dụng khi** · Tiêu chí ĐẠT · **Tiêu chí KHÔNG ĐẠT viết riêng** ·
Vị trí cần soi · Ví dụ ĐẠT/KHÔNG ĐẠT gắn nhãn `[minh họa]`.

Sau đó cập nhật `PLAN.md` (tick 0.3, 0.4) và tỷ lệ ở `rules-classification.md` nếu đổi.

## 4. Quyết định ĐÃ CHỐT — đừng bàn lại

- **Thẩm định chạy HAI VÒNG nối tiếp.** Vòng 1 = checklist, chỉ hỏi *"thành phần cần
  có đã có chưa"*, tiêu chí mặc định *"có thông tin thực chất là ĐẠT"*. Vòng 2 =
  Guideline, kiểm cách tính. **C7 chặn finding Vòng 2 cho mục đã trượt Vòng 1.**
- **Đường vào chính là file `.docx`**, không phải JSON của web app. Lý do: người dùng
  soạn Word trước rồi mới nhập vào web; 30 bản lịch sử là Word rời.
- **Copilot KHÔNG phải trợ lý soạn thảo từng bước** — là bước kiểm trước khi nộp.
- **Mã quy tắc:** `<NHÓM>-<số>` + `legacy_ref: [Rxx]`. **Số thứ tự gán một lượt ở mục
  0.5**, không gán sớm (nhóm `ARC`/`STO`/`TST` chứa cả ĐL lẫn ĐT).
- **Khối 20 mục checklist lặp cho MỌI phân hệ** (App, DB, Redis, Kafka, K8S…) →
  đã tham số hóa 43 mục thành 23 quy tắc.
- **`scope`**: `he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru` — một quy tắc
  chấm bao nhiêu lần.
- **R66 là định lượng** (không phải định tính).
- `QD849-01`: `đặc biệt quan trọng` ⟺ có DC-DR, hai chiều, hai kiểu vi phạm đều `critical`.

## 5. Cạm bẫy kỹ thuật — đã mất thời gian vì chúng, đừng lặp lại

- **Hai hệ đánh số trang cùng tồn tại** trong `rules-flat-draft.md`: R01–R100 dùng số
  trang bản lần 06 (**= trang in + 1**); R101–R110 dùng số trang in. Sẽ thống nhất ở
  0.5. `scripts/audit_rule_coverage.py` có hằng số xử lý việc này.
- **Nguồn trích dẫn chính thức: `docs/rules/.tmp-lan7/clean.txt`** (bản lần 07).
- Khi đối chiếu trích dẫn phải chuẩn hóa: **nháy cong** `“”` → `"`, và **từ bị ngắt
  ngang dòng tại dấu gạch nối** (`active-` / `standby` → `active-standby`, không có
  dấu cách).
- **Ký tự PUA** (U+E000–U+F8FF) của font Symbol/Wingdings: `U+F0A3` là `≤`,
  `U+F0B3` là `≥` — **không phải bullet**. Quy tất cả về `-` sẽ phá hỏng ngưỡng.
- File `frontend/script.js` có **mojibake UTF-8** ở vài chỗ (`case 'KhÃ¡c':`).
- Ô **A42** của file checklist Excel ghi `3.1.2` nhưng phải là `3.2` — làm hỏng script
  đọc theo mã TT.
- Khi chạy Python in tiếng Việt trên Windows: đặt `PYTHONIOENCODING=utf-8`.
- Bash tool ở máy này **không chạy được `python -c` nhiều dòng** — viết ra file rồi chạy.

## 6. Công cụ đã có (`scripts/`)

| Script | Việc |
|---|---|
| `extract_pdf_text.py` | Trích text PDF, lọc watermark theo font, ánh xạ PUA theo font |
| `diff_guideline.py` | So hai lần ban hành Guideline, bỏ nhiễu hình thức |
| `extract_checklist.py` | Trích checklist Excel ra Markdown |
| `audit_rule_coverage.py` | Rà độ phủ — trang nào nhiều câu quy phạm mà ít quy tắc |

## 7. Đang chờ tài liệu (mục 0.12)

Chưa có, và một số quy tắc bị chặn vì thiếu: **849/QĐ-CNVTQĐ** (đã có quy tắc lõi),
**Guideline quy hoạch zone** (đã có quy tắc lõi), **Guideline bền vững** (chưa có gì),
**Phụ lục 01** (chặn R34), **Phụ lục 02** (đã có quy ước thay thế),
**tài liệu định cỡ server GPU**.

## 8. Câu hỏi còn treo với đơn vị thẩm định

- CPU/RAM/IOPS tính **"mỗi request"** (checklist) hay **"mức hệ thống"** (Guideline)
  hay **`factor = định cỡ/POC`** (web app)? Ba cách phân rã.
- Mức `bình thường` có bắt buộc cơ chế dự phòng nội site nào không?
- `CL-1.2` (mức độ SR) có nằm trong tài liệu sizing không, hay ngoài phạm vi Copilot?
- Hai quy tắc **không có mục checklist tương ứng**: `R25+R32` (scale up/out) và `R97`
  (thu hồi) — có nên bổ sung mục checklist không?
- Ba lỗi tính toán trong web app đang chạy thật (`rules-crossmap.md` mục 2) — đã báo
  đội bảo trì chưa?

## 9. Cách làm việc mong muốn

Làm theo thứ tự PLAN.md, không nhảy cóc. Xong mục nào tick mục đó. Gặp chỗ mơ hồ
hoặc mâu thuẫn trong tài liệu thì **nêu ra, không tự quyết**. Mọi trích dẫn phải
kiểm khớp nguyên văn với nguồn trước khi dùng.
