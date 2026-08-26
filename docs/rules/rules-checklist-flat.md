# Mục 0.1 — Danh sách phẳng: checklist thẩm định

> **Nguồn:** `Checklist sizing cap phat tai nguyen HTCNTT.xlsx` (bản cập nhật
> 2026-08-25, **thay thế** bản `...tai nguyen.xlsx` nhận buổi sáng cùng ngày) —
> công cụ người thẩm định dùng để chấm OK/NOK. Bản số hóa thô:
> [`.tmp-checklist/items.md`](.tmp-checklist/items.md).
>
> Khác biệt giữa hai bản: **nội dung 57 mục giống hệt**; bản mới **điền thêm cột
> Ghi chú cho 48 mục** (từ 10 ô lên 58 ô) và **ẩn cột C, D, E**. Không mục nào bị
> thêm/bớt/sửa câu chữ.
> Phân tích và lý do: [`checklist-tham-dinh.md`](checklist-tham-dinh.md).
>
> Đây là **nguồn quy tắc thứ ba** trong bốn nguồn (xem `PLAN.md`). File này ngang
> hàng với `rules-flat-draft.md` (Guideline) và `0.1-danh-sach-quy-tac.md` phần A (code).

## Quy ước

**Mã tạm** `CL-<TT>` theo số thứ tự trong Excel. Mã chính thức gán ở mục 0.5.

**Tham số hóa khối phân hệ** (đã chốt 2026-08-25): khối Application (20 mục) và
Database (23 mục) trùng nhau đúng 20 mục → gộp thành **20 quy tắc dùng chung**, ký
hiệu `CL-3.x.N`, cộng **3 quy tắc riêng cho Database**. Khối 20 mục này **lặp cho
mọi phân hệ** — Application, Database, Redis, Kafka, K8S, LB/FW và các phân hệ khác.
Vì vậy `applies_to_module` để trống = áp cho mọi phân hệ.

> Cột **"Mã App / DB"** giữ số gốc trong Excel để truy ngược.

**Trạng thái:**

| | Nghĩa | Xử lý ở 0.5 |
|---|---|---|
| **T** | Đã có quy tắc **Vòng 2** tương ứng ở nguồn khác | Tạo quy tắc Vòng 1, **liên kết** tới quy tắc Vòng 2 qua `checklist_ref` |
| **M** | Chưa nguồn nào phủ phần Vòng 2 | Tạo quy tắc Vòng 1; phần Vòng 2 để trống |
| **C** | Chờ văn bản (Guideline bền vững) | Tạo Vòng 1; phần Vòng 2 `enabled: false` |

> **Sửa cách hiểu (2026-08-25, khi làm mục 0.2).** Trước đây tôi ghi "T = không tạo
> quy tắc mới". **Sai** — nó mâu thuẫn với mô hình hai vòng. Mỗi mục checklist là một
> phép kiểm **Vòng 1** riêng ("tài liệu có phần này chưa?"), khác hẳn phép kiểm
> **Vòng 2** của quy tắc Guideline ("con số có đúng không?"). Hai phép kiểm có tiêu
> chí, `severity` và thời điểm chạy khác nhau.
>
> Ví dụ `CL-3.x.13` (T, map tới R48): Vòng 1 hỏi *"có phần tính CPU cho phân hệ
> không?"*; R48 ở Vòng 2 hỏi *"công thức tính có đúng không?"*. Bỏ Vòng 1 đi thì
> tài liệu thiếu hẳn phần CPU sẽ không bị bắt ở đâu cả.
>
> → **Cả 37 mục đều thành quy tắc**, đều `round: 1`. T/M/C chỉ nói **có sẵn quy tắc
> Vòng 2 hay chưa**, không nói có tạo quy tắc hay không.

**Loại:** `ĐT` định tính · `ĐL` định lượng · `ĐT→ĐL(Rxx)` = **hai vòng** — Vòng 1
(có thông tin chưa) do C5 kiểm, Vòng 2 (tính có đúng không) do C4 kiểm theo quy tắc
trong ngoặc. Xem tiêu chí mặc định Vòng 1 ngay dưới.

**Ba lỗi trong file Excel gốc** — xử lý bằng ghi chú, không sửa file nguồn:
ô A42 ghi `3.1.2` nhưng theo ngữ cảnh là `3.2` · dòng 18 thiếu TT → đặt `CL-2.10a` ·
dòng 50 thiếu TT → đặt `CL-3.2.7a`.

---

## ⭐ Tiêu chí mặc định VÒNG 1 — áp cho mọi mục không có tiêu chí riêng

> **✅ Nay đã có NGUỒN VĂN BẢN.** Bản checklist cập nhật
> (`Checklist sizing cap phat tai nguyen HTCNTT.xlsx`) đã điền tiêu chí này vào cột
> Ghi chú cho **toàn bộ 48 mục** trước đây để trống — **57/57 mục nay đều có tiêu chí**.
> Trước đó tôi chỉ có xác nhận miệng; giờ trích dẫn được nguyên văn, tức NT2 được
> thỏa mãn đầy đủ cho nhóm quy tắc Vòng 1.

**Trích dẫn nguyên văn** (cột Ghi chú, áp cho 48 mục):

> Yêu cầu chỉ cần có thông tin là được đánh giá OK. OK chỉ mang tính pass vòng
> checklist còn đúng sai chi tiết sẽ đánh giá sau khi pass vòng này để đánh giá sâu
> hơn về mặt cấp phát thông qua các rules trong Guiline định cỡ

> ⚠️ **Lỗi dữ liệu ở dòng 5 (mục 1.1):** ô Ghi chú bị **cắt cụt** giữa chừng —
> dừng ở *"…sẽ đánh giá sau khi"*. Các dòng khác có đủ câu. Nên báo đơn vị thẩm định
> sửa; tạm thời dùng bản đầy đủ ở dòng 6.

**Thẩm định chạy hai vòng, không phải một:**

| | Vòng 1 — Checklist | Vòng 2 — Tài liệu định cỡ |
|---|---|---|
| Hỏi gì | **Thành phần cần có đã có chưa?** | **Cách tính toán, định cỡ tài nguyên có đúng không?** |
| Căn cứ | 37 quy tắc `CL-*` trong file này | 110 quy tắc Guideline + `QD849-*`, `ZONE-01` |
| Đạt nghĩa là | **Pass vòng checklist** — chưa nói gì về đúng/sai | Số liệu và lập luận đạt yêu cầu |
| Thành phần | C5 (bar rất thấp) + C3 | C4 (định lượng) + C5 (định tính) |

**`OK` ở Vòng 1 chỉ mang nghĩa "có đủ thành phần để đánh giá tiếp"** — không phải
"đã đúng". Đúng/sai xét ở Vòng 2.

### Diễn giải để C5 thực thi được

Câu nguyên văn nói rõ *tinh thần* nhưng chưa nói *biên*. Bốn ca KHÔNG ĐẠT dưới đây
là phần cụ thể hóa, **đã được xác nhận 2026-08-25**:

**ĐẠT** khi trong tài liệu sizing có **nội dung thực chất** ứng với mục đó:
- có phần / bảng / đoạn văn nói đúng nội dung mục yêu cầu, và
- nội dung mang giá trị cụ thể (số, tên, mô tả), đủ để người thẩm định đọc và đánh giá tiếp.

**KHÔNG ĐẠT** khi:
- không tìm thấy nội dung nào tương ứng;
- **chỉ có tiêu đề, không có nội dung**;
- nội dung là chỗ giữ chỗ — *"TBD"*, *"sẽ bổ sung sau"*, *"đang cập nhật"*, ô bảng trống;
- ghi *"không áp dụng"* mà **không nêu lý do**.

**KHÔNG áp dụng** khi mục có điều kiện áp dụng và điều kiện không thỏa — ví dụ
`CL-3.x.11` / `CL-3.x.12` (*"nếu phân hệ có sử dụng"* LB / FW), `CL-1.1`
(*"nếu là yêu cầu cấp phát"*). Trả về `không áp dụng`, không tính là vi phạm.

> **Ranh giới phải giữ:** Vòng 1 **không** phán xét nội dung đúng hay sai, không so
> số, không kiểm công thức. Thấy số liệu vô lý cũng vẫn `OK` ở vòng này — việc đó
> để Vòng 2. Trộn hai vòng vào nhau là cách nhanh nhất tạo cảnh báo trùng và làm
> người dùng mất phương hướng.

### Hệ quả cho báo cáo (C7) — không báo lỗi Vòng 2 cho mục trượt Vòng 1

Nếu một mục trượt Vòng 1 (không có thông tin), thì **mọi finding Vòng 2 của mục đó
phải bị chặn**, thay bằng một dòng *"chưa đánh giá được — thiếu thông tin"*.

Lý do: nói với người dùng *"công thức CPU của bạn sai"* khi họ **chưa viết phần CPU**
là vô nghĩa và làm mất niềm tin. Báo cáo phải trình bày Vòng 1 trước, Vòng 2 sau.

> Bốn ca KHÔNG ĐẠT trên chi phối 29/37 quy tắc Vòng 1 — đó là lý do phải chốt rõ
> thay vì để C5 tự suy từ câu *"chỉ cần có thông tin"*.

---

## ⭐ Phạm vi đánh giá (`scope`) — một quy tắc chấm bao nhiêu lần?

> **Bổ sung 2026-08-25** sau lưu ý *"các tiêu chí trong checklist đã được phân rõ ra
> cho Tổng quan, Application, Database"*. Đây là chiều tôi bỏ sót khi tham số hóa.

Tham số hóa gộp 43 mục thành 23 quy tắc, nhưng **không** có nghĩa mỗi quy tắc chỉ
chấm một lần. Checklist phân rõ ba cấp, và mỗi cấp có số lần chấm khác nhau:

| `scope` | Viết tắt trong bảng | Chấm bao nhiêu lần | Quy tắc |
|---|---|---|---|
| `he_thong` | `he_thong` | **Một lần** cho cả hệ thống | `CL-1.*`, `CL-2.*` (Tổng quan) — 14 quy tắc |
| `phan_he` | `phan_he` | **Một lần cho MỖI phân hệ** có trong tài liệu | phần lớn `CL-3.*` — 19 quy tắc |
| `phan_he_x_cong_nghe_luu_tru` | **`ph×cnlt`** | **Một lần cho mỗi công nghệ lưu trữ** trong mỗi phân hệ | `CL-3.x.15`, `CL-3.x.16`, `CL-3.x.17`, `CL-3.2.19` — 4 quy tắc |

Cấp thứ ba đến từ chính câu chữ checklist — mục 3.2.16/3.2.17/3.2.18 ghi rõ
*"Nếu phân hệ dùng nhiều công nghệ lưu trữ khác nhau thì **tính toán độc lập cho
mỗi công nghệ**"*, còn 3.1.16/3.1.17 ghi *"**sizing lặp lại** nếu phân hệ dùng nhiều
công nghệ lưu trữ khác nhau"*. Hai cách nói, cùng một yêu cầu.

**Ví dụ cụ thể:** tài liệu có 4 phân hệ (App, MariaDB, Redis, Kafka), riêng MariaDB
dùng 2 công nghệ lưu trữ → `CL-3.x.1` chấm **4 lần**, `CL-3.x.16` chấm **5 lần**
(3 phân hệ × 1 + MariaDB × 2).

Cấu trúc này khớp sẵn với web app hiện hành: `moduleInstanceReviews[]` có
`instanceKey` (cấp phân hệ) và `storageRowReviews[]` có `rowIndex` (cấp phân vùng /
công nghệ). Nghĩa là nhãn vàng trong DB đã ở đúng độ mịn cần thiết.

→ Trường `scope` phải vào `config/rules.yaml` ở mục 0.5.

---

## Khác biệt câu chữ giữa khối Application và Database

Đã đối chiếu từng cặp trong 20 mục dùng chung: **14 cặp giống hệt**, 6 cặp khác chữ.
Ghi lại để việc tham số hóa không làm mất chi tiết nào:

| Cặp | Khác biệt | Đánh giá |
|---|---|---|
| 3.1.13 / 3.2.14 · 3.1.14 / 3.2.15 | *"toàn phân hệ"* vs *"toàn bộ phân hệ"* | Thuần diễn đạt, cùng nghĩa |
| 3.1.16 / 3.2.17 · 3.1.17 / 3.2.18 | *"sizing lặp lại nếu…"* vs *"tính toán độc lập cho mỗi công nghệ"* | Cùng yêu cầu → đã gom vào `scope` ở trên |
| **3.1.15 / 3.2.16** | Bản DB **có thêm** *"(Nếu phân hệ dùng nhiều công nghệ lưu trữ khác nhau thì tính toán độc lập cho mỗi công nghệ)"*, bản App **không có** | **Khác biệt thật.** Đã áp `scope` per-công-nghệ cho **cả hai** — vì bản App ở mục 3.1.16/3.1.17 cũng yêu cầu lặp lại, nên hiểu đây là thiếu sót câu chữ bên App chứ không phải miễn trừ. **`[CẦN XÁC NHẬN]`** |
| 3.1.2 / 3.2.2 | Script đối chiếu đọc nhầm — ô **A42 ghi `3.1.2`** thay vì `3.2` nên đè lên mục 3.1.2 thật | Không phải khác biệt nội dung, là hệ quả **lỗi đánh số A42**. Cả hai đều là *"công nghệ sử dụng"* |

> Lỗi A42 không chỉ gây khó đọc — nó **làm hỏng cả xử lý tự động**. Bất kỳ script
> nào đọc checklist theo mã TT đều sẽ ghi đè mục 3.1.2 bằng tiêu đề khối Database.
> Cần báo đơn vị thẩm định sửa ở bản phát hành sau.

---

### Mục có tiêu chí RIÊNG — thay thế tiêu chí mặc định

9 ô Ghi chú mang nội dung riêng (không phải câu mặc định), gom lại thành **5 nội
dung khác nhau**. Dùng **nguyên văn của người thẩm định**, không diễn giải lại:

| Mã quy tắc | Ô Excel | Tiêu chí riêng (nguyên văn, rút gọn) |
|---|---|---|
| `CL-2.1` | 2.1 | *"phải chỉ rõ sizing cho ứng dụng mới hay sizing bổ sung cho hệ thống, phân hệ đang chạy"* |
| `CL-2.6`, `CL-2.7`, `CL-2.8`, `CL-2.9` | 2.6–2.9 | *"Gồm đầy đủ các thành phần đang chạy và thêm mới (nếu có)"* |
| `CL-2.10` | 2.10 | Đúng 4 mức: *Đặc biệt quan trọng / Rất quan trọng / Quan trọng / Bình thường* |
| `CL-2.11` | 2.11 | *"phải chỉ rõ hệ thống dự phòng như thế nào? Có DC-DR không? Tại mỗi site thì các thành phần dự phòng như thế nào? Cơ chế dự phòng?"* |
| `CL-3.x.6` | 3.1.6, 3.2.7 | Dự phòng theo 849/QĐ: nội site (active-active? active-standby?) và ngoại site DR (*"Site DR sizing cấu hình tương đương DC không?"*) |

→ **8 mã quy tắc** dùng tiêu chí riêng, **29 mã** còn lại dùng tiêu chí mặc định.

---

## Tổng hợp

| | Số lượng |
|---|---:|
| Mục checklist gốc | 57 |
| Sau tham số hóa | **37 quy tắc** |
| — **T** trùng | 18 |
| — **M** mới | 19 |
| — trong đó có phần **C** chờ văn bản | 1 |

---

## I. Checklist SR/ITBrain

| Mã | `scope` | Hạng mục | Loại | TT | Đối ứng | Nhóm | Ghi chú |
|---|---|---|:--:|:--:|---|---|---|
| `CL-1.1` | `he_thong` | Nguồn tài nguyên cấp phát | ĐT | M | — | `PRC` | Chỉ áp dụng khi là **yêu cầu cấp phát**; yêu cầu thẩm định sizing thì bỏ qua → cần trường "KHÔNG áp dụng khi" |
| `CL-1.2` | `he_thong` | Mức độ SR (căn cứ khối lượng đánh giá) | ĐT | M | — | `PRC` | **`[CẦN XÁC NHẬN]`** thuộc quy trình ITBrain, có nằm trong tài liệu sizing không? Nếu không thì ngoài phạm vi Copilot |

---

## II. Checklist tổng quan

| Mã | `scope` | Hạng mục | Loại | TT | Đối ứng | Nhóm | Ghi chú |
|---|---|---|:--:|:--:|---|---|---|
| `CL-2.1` | `he_thong` | Yêu cầu đầu vào — ứng dụng mới hay nâng cấp hệ đang chạy | ĐT | **T** | R26, R27, R28, R29 | `MTH` | ✅ Đã có tiêu chí ở cột Ghi chú: *"phải chỉ rõ sizing cho ứng dụng mới hay sizing bổ sung cho hệ thống, phân hệ đang chạy"*. Quyết định dạng I/II/III |
| `CL-2.2` | `he_thong` | Mô tả tổng quan hệ thống | ĐT | M | — | `EVD` | |
| `CL-2.3` | `he_thong` | Đầu mối, đơn vị phát triển, định cỡ | ĐT | M | — | `PRC` | Liên quan R30 (ai xác nhận) nhưng khác việc |
| `CL-2.4` | `he_thong` | Cơ sở định cỡ | ĐT | **T** | R26–R29 | `MTH` | Chồng lấn `CL-2.1` — cân nhắc gộp ở 0.5 |
| `CL-2.5` | `he_thong` | Thông số đầu vào | ĐT | **T** | R30, R36, R37 | `EVD` | |
| `CL-2.6` | `he_thong` | Mô hình **logic** tổng quan, đủ thành phần | ĐT | M | — | `EVD` | ✅ Tiêu chí sẵn: *"gồm đầy đủ các thành phần đang chạy và thêm mới (nếu có)"* |
| `CL-2.7` | `he_thong` | Mô hình **vật lý** tổng quan, đủ thành phần | ĐT | M | — | `EVD` | ✅ Tiêu chí sẵn như trên |
| `CL-2.8` | `he_thong` | **Luồng nghiệp vụ** tổng quan — nội bộ + giao tiếp ngoài | ĐT | M | — | `EVD` | ✅ Tiêu chí sẵn như trên. Là đầu vào để xác định `co_duong_ra_public` của `ZONE-01` |
| `CL-2.9` | `he_thong` | Bảng tổng hợp đề xuất cấu hình **toàn hệ thống** | ĐT | M | (R42 một phần) | `EVD` | ✅ Tiêu chí sẵn. Kiểm nhất quán: tổng ở đây phải khớp tổng các phân hệ (`CL-3.x.20`) |
| `CL-2.10` | `he_thong` | Mức độ quan trọng của hệ thống | **ĐL** | **T** | **QD849-01** | `ARC` | ✅ Tiêu chí sẵn: đúng 4 giá trị `đặc biệt quan trọng` / `rất quan trọng` / `quan trọng` / `bình thường` |
| `CL-2.10a` | `he_thong` | Thời gian cam kết triển khai và đổ tải | ĐT | M | — | `PRC` | Dòng 18 Excel, thiếu TT |
| `CL-2.11` | `he_thong` | Mức độ dự phòng của hệ thống | **ĐL** | **T** | **QD849-01**, **QD849-02** | `ARC` | ✅ Tiêu chí sẵn: *"phải chỉ rõ hệ thống dự phòng như thế nào? Có DC-DR không? Tại mỗi site thì các thành phần dự phòng như thế nào?"* |

---

## III. Checklist chi tiết — khối 20 mục, lặp cho MỌI phân hệ

> Áp dụng cho Application, Database, Redis, Kafka, K8S, LB/FW và mọi phân hệ khác.
> `applies_to_module` để trống.

| Mã | `scope` | Hạng mục | Loại | TT | Đối ứng | Nhóm | Mã App / DB |
|---|---|---|:--:|:--:|---|---|---|
| `CL-3.x.1` | `phan_he` | Mô tả chi tiết phân hệ | ĐT | M | — | `EVD` | 3.1.1 / 3.2.1 |
| `CL-3.x.2` | `phan_he` | Công nghệ sử dụng | ĐT | M | — | `EVD` | 3.1.2 / 3.2.2 |
| `CL-3.x.3` | `phan_he` | Hạ tầng vật lý hay ảo hóa | ĐT→ĐL(R13) | **T** | R13, R14 | `ARC` | 3.1.3 / 3.2.3 |
| `CL-3.x.4` | `phan_he` | Mô hình **logic** của phân hệ | ĐT | M | — | `EVD` | 3.1.4 / 3.2.5 |
| `CL-3.x.5` | `phan_he` | Mô hình **vật lý** của phân hệ | ĐT | M | — | `EVD` | 3.1.5 / 3.2.6 |
| `CL-3.x.6` | `phan_he` | Mức độ & khả năng dự phòng theo 849/QĐ | **ĐL** | **T** | **QD849-01**, **QD849-02** | `ARC` | 3.1.6 / 3.2.7 |
| `CL-3.x.7` | `phan_he` | Max request (TPS, RPS, CCU…) từ phân hệ khác / từ ngoài | ĐT→ĐL(R42) | **T** | R42 | `EVD` | 3.1.7 / 3.2.8 |
| `CL-3.x.8` | `phan_he` | **Lưu lượng dữ liệu mỗi request** | ĐT | M | — | `EVD` | 3.1.8 / 3.2.9 |
| `CL-3.x.9` | `phan_he` | **Nguồn request** — nội bộ hay bên ngoài | ĐT→ĐL | M | (đầu vào **ZONE-01**) | `ARC` | 3.1.9 / 3.2.10 |
| `CL-3.x.10` | `phan_he` | **Giao thức** của request (HTTP…) và **port** | ĐT | M | (đầu vào **ZONE-01**) | `ARC` | 3.1.10 / 3.2.11 |
| `CL-3.x.11` | `phan_he` | Sizing tính toán **LB** nếu phân hệ có sử dụng | ĐT→ĐL(R86,R87) | **T** | R86, R87, **ZONE-01** | `LBA` | 3.1.11 / 3.2.12 |
| `CL-3.x.12` | `phan_he` | Sizing tính toán **FW** nếu phân hệ có sử dụng | ĐT→ĐL(R83–R85) | **T** | R83–R85, **ZONE-01** | `FWL` | 3.1.12 / 3.2.13 |
| `CL-3.x.13` | `phan_he` | Sizing **CPU mỗi request** (Cint2017) và toàn phân hệ | ĐT→ĐL(R48) | **T** | R43, R44, R48, R49; R16, R100 | `CPU` | 3.1.13 / 3.2.14 |
| `CL-3.x.14` | `phan_he` | Sizing **RAM mỗi request** (MB) và toàn phân hệ | ĐT→ĐL(R48) | **T** | R45, R48, R49 | `RAM` | 3.1.14 / 3.2.15 |
| `CL-3.x.15` | `ph×cnlt` | **IOPS, latency** mỗi request và toàn phân hệ | ĐT→ĐL(R61) | **T** | R18, R60, R61 | `STO` | 3.1.15 / 3.2.16 |
| `CL-3.x.16` | `ph×cnlt` | Sizing lưu trữ **log** | ĐT→ĐL(R56) | **T** | R56, R57 | `STO` | 3.1.16 / 3.2.17 |
| `CL-3.x.17` | `ph×cnlt` | Sizing lưu trữ **data** | ĐT→ĐL(R56) | **T** | R56, R57 | `STO` | 3.1.17 / 3.2.18 |
| `CL-3.x.18` | `phan_he` | **Loại lưu trữ** — Block / Object / File local / File NAS | ĐT | M | — | `STO` | 3.1.18 / 3.2.20 |
| `CL-3.x.19` | `phan_he` | Sizing có tính dự phòng mức dịch vụ, mức vật lý, backup trên thiết bị khác, sai số, hướng dẫn bền vững | ĐT→ĐL | **T** + **C** | R11, R51 (N+1); R19, R49 (Ksaisố) · **chờ Guideline bền vững** | `ARC` | 3.1.19 / 3.2.21 |
| `CL-3.x.20` | `phan_he` | Bảng tổng hợp đề xuất cấu hình **cho phân hệ** | ĐT | M | — | `EVD` | 3.1.20 / 3.2.22 |

### Ba mục riêng của phân hệ Database

| Mã | `scope` | Hạng mục | Loại | TT | Đối ứng | Nhóm | Mã DB |
|---|---|---|:--:|:--:|---|---|---|
| `CL-3.2.4` | `phan_he` | Số node DB sử dụng | ĐT→ĐL(R50) | **T** | R50, R51 | `ARC` | 3.2.4 |
| `CL-3.2.7a` | `phan_he` | Đảm bảo **3 phân vùng** `/data`, `/log`, `/backup` | **ĐL** | M | (code web app: `MDB-03`, `MDB-04`, `MDB-05`) | `STO` | dòng 50, thiếu TT |
| `CL-3.2.19` | `ph×cnlt` | Sizing lưu trữ **backup** cho phân hệ | ĐT→ĐL(R70) | **T** | R58, R70–R76 | `BAK` | 3.2.19 |

---

## Ghi nhận cho các mục sau

**Cho 0.2 (phân loại):** 9 mục có sẵn tiêu chí đạt ở cột Ghi chú Excel (đánh ✅ ở
trên) — dùng nguyên văn của người thẩm định, không diễn giải lại.

**Cho 0.4 (tiêu chí):** 19 mục **M** cần viết tiêu chí từ đầu, cộng các mục **T**
đã có công thức Vòng 2 sẵn, chỉ cần áp tiêu chí mặc định Vòng 1.

**Cho 0.5 (`rules.yaml`):**
- 18 mục **T** không tạo quy tắc mới — chỉ thêm `checklist_ref` vào quy tắc sẵn có.
- `CL-2.1` và `CL-2.4` chồng lấn (đều về cơ sở / dạng định cỡ) → cân nhắc gộp.
- `CL-2.9` (bảng tổng hợp toàn hệ thống) và `CL-3.x.20` (bảng tổng hợp từng phân hệ)
  mở ra một **kiểm nhất quán mới**: tổng toàn hệ thống phải bằng tổng các phân hệ.
  ~~Đây là quy tắc định lượng thuần, chưa nguồn nào nêu → đề xuất thêm ở 0.5.~~
  **Cập nhật 2026-08-26: đã có nguồn văn bản — `R105`** (Guideline trang in 20), công
  thức ở `rules-formulas.md` mục "BỔ SUNG". Không còn là quy tắc tự đề xuất.
  Lưu ý công thức phải cộng thêm **thành phần dùng chung** (mạng, Firewall, LB), vì
  chúng nằm trong bảng toàn hệ nhưng không thuộc phân hệ nào.

**Điểm phương pháp còn treo:** checklist yêu cầu tính CPU/RAM/IOPS **mỗi request**
(`CL-3.x.13`–`CL-3.x.15`) rồi nhân lên; Guideline cho công thức ở **mức hệ thống**
xuất phát từ 95th của hệ đang chạy (R43–R52); web app đi theo kiểu Guideline
(`factor = định cỡ / POC`). Ba cách phân rã, cần người thẩm định chốt chấp nhận cách
nào — xem [`checklist-tham-dinh.md`](checklist-tham-dinh.md) mục 3.
