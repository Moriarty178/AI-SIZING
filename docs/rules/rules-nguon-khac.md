# Quy tắc từ các văn bản ngoài Guideline

> Checklist thẩm định tham chiếu ba văn bản mà ta chưa có bản đầy đủ:
> **849/QĐ-CNVTQĐ** (dự phòng), **Guideline quy hoạch zone**, **Guideline bền vững**.
> File này ghi các quy tắc từ những nguồn đó, tách khỏi `rules-flat-draft.md`
> (vốn chỉ chứa quy tắc rút từ Guideline GL.CNVTQĐ.CNTT.18).
>
> **Mã tạm:** `QD849-<n>`, `ZONE-<n>`, `BV-<n>` — mã chính thức gán ở mục 0.5.

---

## ⚠️ Về mức độ căn cứ của các quy tắc dưới đây

Nội dung hai quy tắc đầu đến từ **xác nhận trực tiếp của người dùng (2026-08-25)**,
chưa phải trích dẫn nguyên văn từ văn bản gốc. Điều này ảnh hưởng tới NT2 như sau:

- **Finding sinh ra vẫn có căn cứ hợp lệ**, vì cả hai đều là quy tắc định lượng —
  finding neo vào `computed_evidence` (giá trị hai trường đã trích + kết quả so sánh),
  không phụ thuộc `rule_quote`.
- **Nhưng bản thân ngưỡng/logic thì chưa có sở cứ văn bản.** Nếu đơn vị yêu cầu chất
  vấn "căn cứ vào đâu mà bắt buộc DC-DR?", hiện chưa trả lời bằng văn bản được.

→ Khi nhận được 849/QĐ-CNVTQĐ và Guideline quy hoạch zone, phải bổ sung trích dẫn
nguyên văn và số trang vào `source_doc`. Trước đó, giữ
`source_doc: "Xác nhận miệng 2026-08-25 — chờ văn bản"`.

---

## 849/QĐ-CNVTQĐ — Quy định đảm bảo dự phòng hệ thống CNTT

### QD849-01 — Mức độ quan trọng và DC-DR phải tương ứng hai chiều

- **Loại:** định lượng — **ràng buộc nhất quán nội bộ** (C4). Sau khi C3 trích được
  hai trường, code quyết định, không cần LLM.
- **Liên quan checklist:** mục **2.10** (mức độ quan trọng), **2.11** (mức độ dự phòng),
  **3.1.6** và **3.2.7** (dự phòng từng phân hệ).

**Bốn mức độ quan trọng:**
`đặc biệt quan trọng` · `rất quan trọng` · `quan trọng` · `bình thường`

**Quy tắc — quan hệ hai chiều, phải đi cùng nhau:**

```
co_dc_dr  ==  (muc_do_quan_trong == "đặc biệt quan trọng")
```

Nghĩa là có đúng **hai** kiểu vi phạm, và cả hai đều phải cảnh báo:

| # | Tình huống | Vi phạm | Mức |
|---|---|---|---|
| 1 | Mức độ = **đặc biệt quan trọng** nhưng **không có** DC-DR | Thiếu dự phòng bắt buộc | `critical` |
| 2 | Mức độ **khác** "đặc biệt quan trọng" nhưng **có** DC-DR | Không được phép — dư thừa tài nguyên | `critical` |

**Tham số đầu vào:**

| Tên | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `muc_do_quan_trong` | enum (4 giá trị trên) | có | checklist mục 2.10 |
| `co_dc_dr` | bool | có | checklist mục 2.11 — tài liệu có nêu site DR không |

Thiếu một trong hai → **không suy đoán**, sinh finding nhóm "thiếu thông tin" (NT4).

**Đã chốt (2026-08-25):** kiểu vi phạm #2 để `critical`, đúng theo câu *"không được
phép có DC-DR"*.

**Bản chất DC-DR:** là kiểu dự phòng **clone toàn bộ hệ thống sang một site khác**.
Đây là yêu cầu riêng của mức `đặc biệt quan trọng` — **không phải** bản nâng cấp của
dự phòng nội site, và **không thay thế** dự phòng nội site. Xem `QD849-02`.

---

### QD849-02 — Mọi hệ thống đều phải có dự phòng nội site, ở mọi mức độ quan trọng

- **Loại:** định lượng — kiểm trường bắt buộc (C4). Sau khi C3 trích cơ chế dự phòng
  của từng module, code kiểm có khai hay không.
- **Liên quan checklist:** mục **2.11**, **3.1.6**, **3.2.7**.

**Quy tắc:** dự phòng **nội site** là **bắt buộc với mọi mức độ quan trọng** —
`đặc biệt quan trọng`, `rất quan trọng`, `quan trọng`, `bình thường` đều phải có.
Người làm sizing phải **chọn và nêu rõ** cơ chế cho từng module trong hệ thống:

```
co_che_du_phong_noi_site[module] ∈ { active-active, active-standby }
```

**Điểm dễ hiểu nhầm — phải kiểm riêng:** hệ thống mức `đặc biệt quan trọng` có DC-DR
thì **vẫn phải khai dự phòng nội site cho từng module nhỏ**. Có DC-DR không miễn trừ
yêu cầu này.

| # | Tình huống | Vi phạm | Mức |
|---|---|---|---|
| 1 | Module không khai cơ chế dự phòng nội site | Thiếu thông tin bắt buộc | `critical` |
| 2 | Hệ `đặc biệt quan trọng` có DC-DR nhưng **không khai** nội site cho module | Hiểu nhầm DC-DR thay được nội site | `critical` |

**Tham số đầu vào:**

| Tên | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `co_che_du_phong_noi_site` | enum {active-active, active-standby} — **theo từng module** | có | checklist 3.x.6 |

**✅ Đã có lời đáp — và nằm ngay trong Guideline, không phải 849/QĐ.**
Rà lại trang 9 khi làm mục 0.4 phát hiện một câu **bị sót khỏi R01–R100**:

> Các thiết bị phần cứng phải đảm bảo hoạt động với cơ chế dự phòng active-active
> (đối với các hệ thống Rất quan trọng trở lên) hoặc active-standby (đối với các hệ
> thống Quan trọng).

Nghĩa là mức độ quan trọng **CÓ ép** chọn cơ chế:

| Mức độ | Cơ chế nội site bắt buộc |
|---|---|
| Đặc biệt quan trọng · Rất quan trọng | **active-active** |
| Quan trọng | **active-standby** |
| Bình thường | Guideline không quy định → chỉ cần khai, không ép |

→ Đã ghi thành **`R101`** ở `rules-flat-draft.md` mục "BỔ SUNG". `QD849-02` vì vậy
chỉ còn kiểm *có khai hay không*; việc **khai đúng cơ chế theo mức độ** do `R101`
kiểm, và đó là quy tắc **định lượng** (ánh xạ enum → enum, code quyết định).

**`[CẦN XÁC NHẬN]`** còn lại: mức `bình thường` có bắt buộc cơ chế nào không, hay
được tự chọn? Guideline im lặng ở mức này.

---

## Guideline quy hoạch zone

### ZONE-01 — Hệ thống có đường ra internet/public phải định cỡ firewall và LB

- **Loại:** định lượng — **ràng buộc nhất quán có điều kiện** (C4).
- **Liên quan checklist:** mục **3.1.11** (giao thức, port), **3.1.12** / **3.2.13**
  (sizing FW), **3.1.11** / **3.2.12** (sizing LB), **3.1.10** / **3.2.10**
  (nguồn request — nội bộ hay bên ngoài).

**Điều kiện kích hoạt:** hệ thống có **đường ra internet / public**.

**Yêu cầu khi kích hoạt — phải có đủ cả hai:**
1. Phần **định cỡ firewall**
2. Phần **định cỡ cân bằng tải (LB)**

Cả hai phải tính bằng **băng thông** và **kích thước bản tin**, không được khai
cấu hình suông.

**KHÔNG áp dụng khi:** hệ thống chỉ chạy nội bộ, không có đường ra internet/public.
Trả về `không áp dụng`.

**Tham số đầu vào:**

| Tên | Kiểu | Bắt buộc | Ghi chú |
|---|---|---|---|
| `co_duong_ra_public` | bool | có | suy từ checklist 3.x.10 (nguồn request) và 3.x.11 (giao thức, port) |
| `co_dinh_co_firewall` | bool | có | checklist 3.1.12 / 3.2.13 |
| `co_dinh_co_lb` | bool | có | checklist 3.1.11 / 3.2.12 |

### ⚠️ "Kích thước bản tin" KHÔNG phải gói 1518/512 Byte của R85

Đã chốt (2026-08-25). Đây là hai thứ khác nhau, rất dễ nhầm và nhầm thì sai kết quả:

| | Kích cỡ gói **1518 / 512 Byte** (R85) | **Kích thước bản tin** của ZONE-01 |
|---|---|---|
| Là gì | Kích cỡ gói chuẩn để **đo năng lực** throughput của thiết bị firewall | Kích cỡ gói tin **thực tế của ứng dụng / dự án đang định cỡ** |
| Dùng để | Đọc thông số thiết bị trên CTKT | **Tính băng thông cần** cho hệ thống |
| Nguồn | Hằng số chuẩn trong Guideline | Số liệu riêng từng dự án — checklist mục **3.x.8** *"Lưu lượng dữ liệu mỗi request"* |

→ Băng thông yêu cầu tính từ **kích thước bản tin của chính ứng dụng**, rồi mới đối
chiếu với năng lực thiết bị (vốn đo theo gói chuẩn). Lấy 1518 Byte đi tính nhu cầu
băng thông của ứng dụng là **sai phương pháp**.

**Nối với công thức đã có** — ZONE-01 chỉ là *điều kiện bắt buộc phải làm*; cách
tính đã nằm trong Guideline:

| Việc | Quy tắc Guideline |
|---|---|
| Số port firewall theo zone + HA | **R83** |
| Lưu lượng zone = số kết nối đồng thời × lưu lượng mỗi kết nối; thông lượng thiết bị | **R84** ← dùng kích thước bản tin của ứng dụng |
| Gói chuẩn 1518/512 Byte để **đọc năng lực thiết bị**, chọn bandwidth port | **R85** |
| Số port LB, CPS layer 4, TPS layer 7, thông lượng | **R86** |
| Lưu lượng dịch vụ theo CPS/TPS, chọn bandwidth | **R87** |

Nghĩa là ZONE-01 sinh finding **Vòng 1 (đủ mục)** — thiếu hẳn phần định cỡ FW/LB — còn
R83–R87 sinh finding **Vòng 2 (đúng số)** — đúng mô hình hai vòng ở
[`checklist-tham-dinh.md`](checklist-tham-dinh.md) mục 2.3.

**Phụ thuộc dữ liệu:** ZONE-01 cần checklist mục **3.x.8** (lưu lượng dữ liệu mỗi
request) làm đầu vào. Thiếu mục đó thì không tính được băng thông → sinh finding
nhóm "thiếu thông tin" (NT4), không tự lấy 1518 Byte thay thế.

---

## Guideline bền vững

Chưa có nội dung. Được nhắc ở checklist mục 3.1.19 / 3.2.21
(*"dự phòng mức dịch vụ, mức vật lý, backup trên thiết bị khác đang chạy dịch vụ,
sai số tính toán, hướng dẫn bền vững"*) và ở phần đầu checklist.

→ Cần xin văn bản. Xem `PLAN.md` mục 0.12(d).
