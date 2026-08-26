# Checklist thẩm định — phân tích và cách đưa vào dự án

> **Nguồn:** `Checklist sizing cap phat tai nguyen HTCNTT.xlsx` (bản cập nhật
> 2026-08-25, thay thế bản nhận buổi sáng) — công cụ mà **người thẩm định thực sự
> dùng** để đánh giá bản sizing. Bản mới điền cột Ghi chú cho cả 57/57 mục.
> Trích bằng `scripts/extract_checklist.py`, bản đã số hóa:
> [`.tmp-checklist/items.md`](.tmp-checklist/items.md).
>
> Đây chính là "checklist rà soát đánh giá nội dung định cỡ" mà Guideline lần 07
> nói đã bổ sung nhưng không có trong file PDF (xem
> [`rules-lan7-doi-chieu.md`](rules-lan7-doi-chieu.md) mục 3).

---

## Kết luận ngắn

**Checklist này định nghĩa đầu ra của Copilot rõ hơn cả Guideline.**

Hai tài liệu trả lời hai câu hỏi khác nhau:

| | Trả lời câu hỏi | Thành phần phụ trách |
|---|---|---|
| **Checklist** (57 mục) | **Vòng 1** — thành phần cần có đã có chưa? | C5 với bar rất thấp: chỉ kiểm *có thông tin hay không* |
| **Guideline** (110 quy tắc) | **Vòng 2** — cách tính toán, định cỡ có đúng không? | C4 (định lượng) + C5 (định tính) |

Copilot được xây để giúp người nộp *vượt qua vòng thẩm định*. Vòng thẩm định chạy
theo checklist này. Nên checklist phải trở thành **khung của báo cáo C7**, còn 100
quy tắc Guideline là lớp kiểm sâu bên dưới từng mục.

Kèm theo: checklist làm lộ ra **ba tài liệu nữa cần xin** (mục 5), và **gỡ được thế
bí của mục 1.16** (mẫu Word chuẩn) mà trước đây phải chờ Phụ lục 01 (mục 6.3).

---

## 1. Cấu trúc checklist

65 dòng Excel, một sheet, không có dòng/cột ẩn. **57 mục kiểm** trong 4 phần:

| Phần | Nội dung | Số mục |
|---|---|---:|
| **I. Checklist SR/ITBrain** | Nguồn tài nguyên cấp phát, mức độ SR | 2 |
| **II. Checklist tổng quan** | Yêu cầu đầu vào, mô hình logic/vật lý, luồng nghiệp vụ, mức độ quan trọng, mức độ dự phòng | 12 |
| **III.1 Phân hệ Application** | Mô tả, công nghệ, mô hình, dự phòng, request, sizing CPU/RAM/IOPS/lưu trữ | 20 |
| **III.2 Phân hệ Database** | Như trên, thêm số node, backup, 3 phân vùng | 23 |

Bảy cột, chia vai trò rõ ràng giữa hai bên:

| Cột | Ai điền | Nội dung |
|---|---|---|
| A, B | — | TT, Hạng mục |
| **C** | **Đơn vị yêu cầu** | **Tham chiếu theo tài liệu sizing (trang, mục bao nhiêu)** |
| D, E, **F** | Đơn vị thẩm định | Đánh giá tài liệu kèm SR · Kết quả · **OK/NOK** |
| G | Đơn vị thẩm định | Ghi chú — thường là tiêu chí đạt viết bằng lời |
| H | — | Tài liệu tham chiếu |

---

## 2. Ba điều quan trọng nhất rút ra

### 2.1. Cột F (OK/NOK) chính là cấu trúc đánh giá trong web app

Web app hiện hành lưu đánh giá của người thẩm định dưới dạng `{eval: "OK"|"NOK",
note: "..."}` trong các cột `*_admin_review` ([`0.7-nguon-nhan-vang.md`](../0.7-nguon-nhan-vang.md)).
Đó **chính là checklist này đã được số hóa vào phần mềm**.

Hệ quả cho mục 0.7: nhãn vàng trong DB không phải là ghi chú rời rạc, mà là kết quả
chấm theo đúng 57 mục này. Việc so khớp finding của Copilot với nhãn vì vậy nên neo
theo **mã mục checklist** (`2.10`, `3.1.13`…) thay vì theo vị trí trong file Word —
đơn giản và chính xác hơn hẳn cách ánh xạ mục Word ↔ tab web mà tôi đã lo ở mục 1.13.

### 2.2. Cột C là một việc Copilot làm được ngay, và có ích ngay

Cột C bắt đơn vị yêu cầu ghi **mỗi mục checklist được trình bày ở trang nào, mục nào**
trong tài liệu sizing của mình. Đây là việc thủ công, buồn tẻ, dễ bỏ sót — và là
đúng thứ máy làm tốt: đọc file Word, định vị từng mục, điền tham chiếu.

Giá trị kép: người nộp được điền hộ một biểu mẫu bắt buộc, còn Copilot thì có sẵn
bản đồ "mục checklist ↔ vị trí trong tài liệu" để gắn finding vào đúng chỗ.

Đề xuất đưa thành một tính năng riêng, xem mục 6.4.

### 2.3. Thẩm định chạy HAI VÒNG, không phải một

> **Làm rõ 2026-08-25.** Ban đầu tôi mô tả đây là hai *lớp* kiểm chạy song song.
> Thực tế là hai **vòng nối tiếp** — khác biệt quan trọng, vì nó quyết định thứ tự
> báo cáo và việc chặn cảnh báo thừa.

```
Mục checklist 3.1.13 "Tính toán sizing CPU mỗi request (Cint2017) và cho toàn phân hệ"
   │
   ├─ VÒNG 1 — CHECKLIST: "thành phần cần có đã có chưa?"
   │     Tài liệu có phần tính CPU cho phân hệ này không?
   │     → không có ⇒ finding "thiếu mục 3.1.13"
   │                 ⇒ CHẶN mọi finding Vòng 2 của mục này
   │     → có rồi  ⇒ OK vòng 1, đi tiếp
   │
   └─ VÒNG 2 — TÀI LIỆU ĐỊNH CỠ: "cách tính có đúng không?"
         Theo Guideline R43/R44/R48/R49: con số tính lại có khớp không?
         → lệch 49% ⇒ finding "sai công thức", kèm computed_evidence
```

**`OK` ở Vòng 1 chỉ có nghĩa "pass vòng checklist"** — đủ thành phần để đánh giá
tiếp, **chưa nói gì** về đúng hay sai. Thấy số liệu vô lý ở Vòng 1 cũng vẫn `OK`;
việc đó để Vòng 2.

Hai hệ quả thiết kế:

1. **Schema finding** thêm `checklist_ref` bên cạnh `rule_ref`, và cần biết finding
   thuộc vòng nào.
2. **Báo cáo C7 chặn finding Vòng 2 cho mục đã trượt Vòng 1** — thay bằng
   *"chưa đánh giá được, thiếu thông tin"*. Nói *"công thức CPU sai"* với người
   chưa viết phần CPU là vô nghĩa và làm mất niềm tin.

Tiêu chí đầy đủ của Vòng 1:
[`rules-checklist-flat.md`](rules-checklist-flat.md#-tiêu-chí-mặc-định-vòng-1--áp-cho-mọi-mục-không-có-tiêu-chí-riêng).

---

## 3. Checklist thêm gì so với 110 quy tắc Guideline

> **Số liệu chính thức (sau khi làm xong 0.1):** 57 mục → **37 quy tắc** sau tham số
> hóa, gồm **18 trùng** với nguồn sẵn có và **19 mới**. Bảng đầy đủ:
> [`rules-checklist-flat.md`](rules-checklist-flat.md). Phần dưới liệt kê nhóm mới
> theo chủ đề để dễ đọc.

**Nhóm mới — yêu cầu về cấu trúc tài liệu** (Guideline không nói tới):

| Mục | Nội dung |
|---|---|
| 2.2, 2.3 | Mô tả tổng quan hệ thống; đầu mối, đơn vị phát triển/định cỡ |
| 2.6, 2.7, 2.8 | Mô hình **logic** tổng quan · mô hình **vật lý** tổng quan · **luồng nghiệp vụ** (nội bộ + giao tiếp ngoài) |
| 2.9 | Bảng tổng hợp đề xuất cấu hình toàn hệ thống |
| 3.x.1, 3.x.2 | Mô tả chi tiết phân hệ; công nghệ sử dụng |
| 3.x.4, 3.x.5 | Mô hình logic / vật lý **của từng phân hệ** |
| 3.x.20, 3.x.22 | Bảng tổng hợp đề xuất cấu hình **cho từng phân hệ** |

**Nhóm mới — thông số chưa từng có trong Guideline:**

| Mục | Nội dung |
|---|---|
| 3.x.9 | **Lưu lượng dữ liệu mỗi request** |
| 3.x.10 | **Nguồn request** — từ nội bộ hay bên ngoài |
| 3.x.11 | **Giao thức của request** (HTTP…) và **port** |
| 3.x.19 / 3.2.20 | **Loại lưu trữ**: Block, Object, File local, File NAS |
| dòng 50 | **Đảm bảo 3 phân vùng** `/data`, `/log`, `/backup` (phân hệ DB) |
| dòng 18 | Thời gian cam kết triển khai và đổ tải |

**Một khác biệt về phương pháp cần làm rõ:** checklist yêu cầu tính CPU/RAM/IOPS
**cho mỗi request** rồi mới nhân lên toàn phân hệ (3.x.13–3.x.16). Guideline lại
cho công thức ở **mức hệ thống**, xuất phát từ giá trị 95th của một hệ đang chạy
(R43–R52). Hai cách phân rã khác nhau, cùng dẫn tới một kết quả nhưng đường đi khác.
Web app hiện hành đi theo kiểu Guideline (`factor = định cỡ / POC`).
→ **Cần hỏi người thẩm định chấp nhận cách nào**, hoặc cả hai.

---

## 4. Điểm yếu của bản checklist hiện tại

Ghi lại để hỏi lại đơn vị thẩm định, không tự sửa:

1. ~~**Chỉ chi tiết 2 phân hệ.**~~ **✅ Đã trả lời (2026-08-25): khối 20 mục lặp cho
   MỌI phân hệ** — Redis, Kafka, K8S, LB/FW và các phân hệ khác. File Excel chỉ viết
   sẵn hai khối Application và Database làm mẫu. Vì vậy quy tắc được tham số hóa,
   `applies_to_module` để trống = áp cho mọi phân hệ. LB và FW vẫn kiểm *bên trong*
   mỗi phân hệ (3.x.11, 3.x.12), không thành phân hệ riêng.
2. ~~**48/57 mục không có tiêu chí đạt.**~~ **✅ ĐÃ ĐƯỢC BỔ SUNG VÀO CHÍNH FILE
   EXCEL (2026-08-25).** Bản `...HTCNTT.xlsx` điền tiêu chí mặc định cho cả 48 mục:
   *"Yêu cầu chỉ cần có thông tin là được đánh giá OK…"*. Nay 57/57 mục có tiêu chí,
   và tiêu chí Vòng 1 có **nguồn văn bản** thay vì chỉ xác nhận miệng.
   Chi tiết: `rules-checklist-flat.md`.
3. **Lỗi đánh số:** ô A42 ghi `3.1.2` nhưng theo ngữ cảnh phải là `3.2`
   (tiêu đề phân hệ Database).
4. **Hai dòng thiếu số thứ tự:** dòng 18 ("Thời gian cam kết triển khai và đổ tải",
   thuộc 2.10) và dòng 50 ("Đảm bảo 3 phân vùng /data, /log, /backup", thuộc 3.2.7).

---

## 5. Ba tài liệu mới bị tham chiếu mà ta chưa có

| Tài liệu | Được nhắc ở | Trạng thái |
|---|---|---|
| **849/QĐ-CNVTQĐ** — *Quy định đảm bảo dự phòng hệ thống CNTT* | 2.10, 2.11, 3.1.6, 3.2.7 | 🟡 **Đã có 2 quy tắc lõi** (xác nhận 2026-08-25) → `QD849-01` (DC-DR) và `QD849-02` (dự phòng nội site). Vẫn cần văn bản để lấy trích dẫn và làm rõ mức độ có ép chọn cơ chế nội site không |
| **Guideline quy hoạch zone** | 3.1.11, 3.1.12, 3.2.12, 3.2.13 | 🟡 **Đã có quy tắc lõi** → `ZONE-01`. Vẫn cần văn bản |
| **Guideline bền vững** | 3.x.19/3.x.21, phần đầu | ⬜ Chưa có gì |

Hai quy tắc lõi đã ghi ở [`rules-nguon-khac.md`](rules-nguon-khac.md):

- **`QD849-01`** — mức độ quan trọng và DC-DR là **quan hệ hai chiều**:
  `đặc biệt quan trọng` ⟺ có DC-DR. Hai kiểu vi phạm, cả hai `critical`.
- **`QD849-02`** — dự phòng **nội site** (active-active / active-standby) là **bắt
  buộc với mọi mức độ**, khai theo từng module. Hệ `đặc biệt quan trọng` có DC-DR
  thì **vẫn phải** khai nội site — DC-DR không thay thế được nội site.
- **`ZONE-01`** — hệ thống có **đường ra internet/public** thì bắt buộc phải có phần
  định cỡ **firewall và LB**, tính theo băng thông và kích thước bản tin.

Cả hai là **ràng buộc nhất quán → C4 (code quyết định)**, không phải C5. Đây là kết
quả tốt: chúng bổ sung vào nhóm quy tắc đáng tin cậy nhất, không làm nặng thêm phần
phụ thuộc LLM.

> **Lưu ý về căn cứ:** nội dung hai quy tắc đến từ xác nhận trực tiếp, chưa có trích
> dẫn văn bản. Finding vẫn hợp lệ theo NT2 vì neo vào `computed_evidence`, nhưng
> bản thân ngưỡng chưa có sở cứ giấy tờ — cần bổ sung khi nhận được văn bản.

---

## 6. Đưa vào đâu

### 6.1. Bộ quy tắc — mở lại 0.1–0.4 cho phần checklist

57 mục checklist là **nguồn quy tắc thứ ba**, bên cạnh Guideline (R01–R100) và code
web app (46 quy tắc). Cần đi lại đúng quy trình đã dùng cho hai nguồn kia:

| Mục | Việc |
|---|---|
| 0.1 | Thêm 57 mục vào danh sách phẳng, mã tạm `CL-<TT>` (ví dụ `CL-3.1.13`) |
| 0.2 | Phân loại — dự đoán đa số là định tính (kiểm đủ mục), một phần trỏ về quy tắc định lượng đã có |
| 0.3 | Chỉ với mục nào ra được công thức mới |
| 0.4 | **Nhẹ** — 48 mục dùng chung *tiêu chí mặc định Vòng 1*; chỉ 8 mã có tiêu chí riêng |
| 0.5 | `rules.yaml`: thêm trường `checklist_ref` cho mọi quy tắc; mục checklist không map được về quy tắc nào thì thành quy tắc riêng nhóm `CHK` |

### 6.2. Schema finding và báo cáo C7

- Thêm `checklist_ref` vào cấu trúc finding (bên cạnh `rule_ref`, `computed_evidence`).
- **Báo cáo C7 nên xếp theo đúng thứ tự checklist**, để người thẩm định đọc báo cáo
  Copilot và chấm checklist theo cùng một mạch. Đây là thay đổi về hình thức báo cáo,
  ảnh hưởng mục 1.10 và 3.4.

### 6.3. Mục 1.16 (mẫu Word chuẩn) — đã gỡ được thế bí

Trước đây 1.16 phải chờ **Phụ lục 01** (mẫu tài liệu định cỡ) mà chưa xin được.
Nay **checklist thay thế được**: 57 mục chính là các đề mục bắt buộc phải có trong
tài liệu sizing, đã sắp sẵn thứ tự và phân cấp.

→ Mẫu Word chuẩn sinh thẳng từ checklist, **không còn phụ thuộc Phụ lục 01**.
Quy tắc R34 ("theo mẫu Phụ lục 01") vẫn giữ `enabled: false` vì đó là quy tắc riêng.

### 6.4. Đề xuất tính năng mới — điền hộ cột C

Copilot đọc file Word, với mỗi mục trong 57 mục xác định nó nằm ở trang/mục nào,
rồi xuất ra bản checklist đã điền sẵn cột C, kèm đánh dấu những mục **không tìm thấy**.

Đây gần như là một MVP độc lập: không cần C4, không cần C6, chỉ cần C1 + C3 + C5 nhẹ.
Giá trị thấy được ngay và rủi ro thấp — nếu Copilot điền sai vị trí, người dùng sửa
mất vài giây, không như một cảnh báo sai về số liệu.

---

## 7. PLAN.md cần đổi gì

Đã cập nhật, tóm tắt:

| Mục | Thay đổi |
|---|---|
| 0.1–0.4 | Ghi rõ phải phủ **cả 3 nguồn**: Guideline · code web app · **checklist** |
| 0.5 | Thêm yêu cầu trường `checklist_ref` |
| 0.7 | Ghi chú: nhãn trong DB neo theo mã mục checklist → so khớp trực tiếp |
| 0.12 | Checklist ✅ đã nhận. Bổ sung 3 tài liệu cần xin: 849/QĐ, quy hoạch zone, bền vững |
| 1.10, 3.4 | Báo cáo xếp theo thứ tự checklist |
| 1.16 | **Bỏ phụ thuộc Phụ lục 01** — sinh mẫu Word từ checklist |
| 1.17 *(mới)* | Điền hộ cột C của checklist |

**Về tiến độ:** Giai đoạn 0 **không còn ở mức "gần xong"**. Mục 0.1–0.3 đang tick
`[x]` nhưng chỉ phủ Guideline và code, chưa phủ checklist. Cần mở lại — không phải
làm lại từ đầu, mà bổ sung nguồn thứ ba.

Đây là tin tốt chứ không phải trở ngại: thà phát hiện thiếu một nguồn quy tắc ở
Giai đoạn 0 còn hơn phát hiện ở Giai đoạn 3 khi đã xây xong pipeline theo sai khung.

---

## 8. Đưa 57 mục vào danh sách phẳng (mục 0.1) — ✅ ĐÃ DUYỆT VÀ THỰC HIỆN

> **Duyệt 2026-08-25.** Ba câu hỏi ở mục 8.8 đã được trả lời: tham số hóa ✅ đồng ý ·
> `QD849-01` vi phạm kiểu #2 để `critical` · khối 20 mục **lặp cho mọi phân hệ**.
> Kết quả: **57 mục → 37 quy tắc** tại [`rules-checklist-flat.md`](rules-checklist-flat.md)
> (18 trùng · 19 mới · 1 chờ Guideline bền vững).
> Phần dưới giữ lại làm hồ sơ quyết định.

### 8.1. Đầu ra

Một file mới: **`docs/rules/rules-checklist-flat.md`**, theo đúng khuôn per-nguồn
đang dùng (Guideline → `rules-flat-draft.md`, code → `0.1-danh-sach-quy-tac.md`).
Không gộp bốn nguồn làm một ngay bây giờ — việc hợp nhất để `rules.yaml` ở mục 0.5
làm, `rules-crossmap.md` giữ vai trò nối các nguồn.

Mỗi dòng gồm: mã tạm · mục checklist · ĐL/ĐT (tạm) · trạng thái · đối ứng sẵn có ·
nhóm mã dự kiến · ghi chú.

### 8.2. Mã tạm và ba lỗi nguồn cần xử lý

Mã tạm `CL-<TT>` lấy thẳng số thứ tự trong Excel: `CL-2.10`, `CL-3.1.13`.

Ba chỗ file gốc bị lỗi, **không tự sửa file Excel**, chỉ ghi cách xử lý:

| Vấn đề | Xử lý đề xuất |
|---|---|
| Ô A42 ghi `3.1.2`, theo ngữ cảnh phải là `3.2` (tiêu đề phân hệ Database) | Dùng `3.2`, ghi chú lỗi gốc |
| Dòng 18 có nội dung, không có TT — *"Thời gian cam kết triển khai và đổ tải"* | Đặt `CL-2.10a` |
| Dòng 50 có nội dung, không có TT — *"Đảm bảo 3 phân vùng /data, /log, /backup"* | Đặt `CL-3.2.7a` |

### 8.3. ⭐ Tham số hóa khối phân hệ — quyết định quan trọng nhất

Khối Application (20 mục) và khối Database (23 mục) **trùng nhau 20 mục**, chỉ khác
tên gọi. Đối chiếu từng dòng cho thấy Database chỉ có **3 mục riêng**:

| Mục riêng của Database | Mã |
|---|---|
| Số node DB sử dụng | `CL-3.2.4` |
| Đảm bảo 3 phân vùng `/data`, `/log`, `/backup` | `CL-3.2.7a` |
| Tính toán sizing lưu trữ **backup** cho phân hệ | `CL-3.2.19` |

Hai cách làm:

| | Cách làm | Số quy tắc | Nhận xét |
|---|---|---:|---|
| (i) | Giữ 43 mục cấp 3 thành 43 quy tắc riêng | 43 | Trùng lặp nặng. Sửa một tiêu chí phải sửa hai nơi, dễ lệch |
| (ii) | **Tham số hóa theo phân hệ** — 20 quy tắc dùng chung + 3 quy tắc riêng cho DB | **23** | ⭐ Khuyến nghị |

Cách (ii) còn **tự giải quyết điểm yếu ở mục 4.1**: checklist chỉ chi tiết
Application và Database, nhưng web app có thêm Redis, Kafka, K8S, LB/FW. Nếu quy tắc
được tham số hóa thì các phân hệ đó **áp dụng được ngay** mà không phải viết thêm
mục nào — dùng `applies_to_module` để trống nghĩa là áp cho mọi phân hệ.

Cách này cũng khớp với cách người thẩm định thực sự nghĩ: cùng một bộ ~20 câu hỏi,
hỏi lại cho từng phân hệ.

### 8.4. Ba trạng thái khi đối chiếu

Với mỗi mục checklist, đối chiếu ba nguồn đã có (Guideline R01–R100, code web app,
`rules-nguon-khac.md`) rồi gán một trong ba:

| Trạng thái | Nghĩa | Xử lý ở 0.5 |
|---|---|---|
| **T** — trùng | Đã có quy tắc tương ứng | KHÔNG tạo quy tắc mới, chỉ thêm `checklist_ref` vào quy tắc sẵn có |
| **M** — mới | Chưa nguồn nào phủ | Tạo quy tắc mới |
| **C** — chờ văn bản | Cần 849/QĐ, quy hoạch zone, hoặc bền vững | Tạo nhưng `enabled: false`, trừ phần đã có lõi (`QD849-01`, `ZONE-01`) |

Trạng thái **T** là chỗ tiết kiệm công lớn nhất — tránh viết lại tiêu chí cho thứ
`rules-formulas.md` đã có công thức đầy đủ.

### 8.5. Ước lượng khối lượng

| | Số lượng |
|---|---:|
| Mục checklist gốc | 57 |
| Sau tham số hóa khối phân hệ (8.3) | **~37 quy tắc** |
| — trong đó **T** (trùng, chỉ gắn `checklist_ref`) | ~15–20 |
| — trong đó **M** (mới, phải viết tiêu chí) | ~15–20 |
| — trong đó **C** (chờ văn bản) | ~2–4 |

Con số chốt lại trong lúc làm; đây là ước lượng khi đọc lần đầu.

### 8.6. Phân loại ĐL/ĐT làm luôn trong 0.1

`rules-flat-draft.md` của bạn đã gắn `[đl]`/`[đt]` ngay khi lập danh sách phẳng —
làm giống vậy cho nhất quán: 0.1 gán **tạm**, 0.2 rà lại và chốt tỷ lệ.

Dự đoán: đa số mục checklist là **ĐT** (kiểm đủ mục, đủ nội dung), nhưng những mục
trỏ về công thức Guideline (`CL-3.x.13` CPU, `CL-3.x.14` RAM, `CL-3.x.15` IOPS…) sẽ
là **ĐT ở Vòng 1 + ĐL ở Vòng 2** — đúng mô hình hai vòng ở mục 2.3. Trong
bảng sẽ ghi rõ dạng `ĐT→ĐL(R48)`.

### 8.7. Nhịp làm

- **Bước 1 (việc này):** lập bảng ~37 dòng đầy đủ trạng thái và đối ứng → **bạn duyệt**.
  Xong bước này là **mục 0.1 hoàn tất cho cả bốn nguồn** — đã đạt.
- **Bước 2:** 0.2 chốt phân loại và tỷ lệ · 0.3 công thức cho mục ĐL mới · 0.4 tiêu
  chí cho mục ĐT mới (gộp chung với 22 quy tắc ĐT Guideline còn dở).

### 8.8. Ba điều cần bạn chốt khi duyệt

1. **Tham số hóa khối phân hệ** (8.3) — đồng ý gộp 43 → 23 quy tắc không?
2. **`QD849-01` vi phạm kiểu #2** (có DC-DR khi mức độ không phải "đặc biệt quan
   trọng") — để `critical` theo đúng câu "không được phép", hay hạ `major` vì thực
   chất là lãng phí chi phí?
3. **Khối 20 mục có lặp cho mọi phân hệ không** (Redis, Kafka, K8S…), hay checklist
   cố ý chỉ soi kỹ Application và Database? Câu này quyết định phạm vi `applies_to_module`.
