# Mục 0.3 — Công thức, tham số, ngưỡng, đơn vị cho 77 quy tắc định lượng

> **Nguồn:** `docs/rules/rules-flat-draft.md` — **110 quy tắc R01–R110**, đã phân loại ở
> `docs/rules/rules-classification.md` (77 quy tắc định lượng `[đl]`, 33 định tính `[đt]` — R66 chuyển nhóm 2026-08-25).
>
> **Cập nhật 2026-08-26:** thêm **R101** và **R105** — hai quy tắc định lượng phát hiện
> khi rà độ phủ ở mục 0.2 (75 → **77**). Xem mục **"BỔ SUNG"** gần cuối tài liệu.
>
> **Phạm vi mục 0.3:** chỉ phát triển **77 quy tắc định lượng** — viết rõ công thức,
> tham số đầu vào, ngưỡng, đơn vị, và trang gốc. KHÔNG phân loại lại (đã xong 0.2),
> KHÔNG viết tiêu chí định tính (mục 0.4), KHÔNG gán mã `STO-xx` (mục 0.5).
>
> **Quy ước `Rxx`:** mã tạm từ 0.1/0.2; sẽ được gán mã chính thức `STO-xx`/`CPU-xx`
> ở mục 0.5 khi số hóa `rules.yaml`.
>
> **Nguyên tắc kỹ thuật (NT1, NT4):**
> - Mọi công thức dưới đây sẽ được **code Python thực thi** ở C4 (không qua LLM).
> - Chỗ nào **thiếu thông tin / chưa chắc** → ghi rõ `[CHƯA CHẮC]`, để tham số đó là
>   `None` (không tự điền), và tạo finding nhóm "thiếu thông tin" khi áp dụng. KHÔNG bịa.
> - Danh sách điểm cần xác nhận với người thẩm định được tổng hợp ở cuối tài liệu.

---

## Tổng hợp nhanh

| Nhóm | Quy tắc | Số lượng |
|------|---------|:--------:|
| A.1 — Nguyên tắc/ngưỡng KPI (trang 8–10) | R01–R09, R11–R13, R15–R19 | 17 |
| A.1 — Khái niệm/công thức (trang 7) | R20–R22 | 3 |
| 4. Máy chủ — chuẩn bị thông số (trang 17–21) | R36, R38–R42 | 6 |
| 4. Máy chủ — công thức tài nguyên (trang 22–25) | R43–R52 | 10 |
| 5. Lưu trữ — thông số & công thức (trang 25–26) | R54–R58 | 5 |
| 5. Lưu trữ — IOPS & số ổ (trang 27–31) | R60–R66, R68–R69 | 9 |
| 6. Sao lưu (trang 31–32) | R70, R71, R72–R76 | 7 |
| 7. SAN switch (trang 33) | R77–R78 | 2 |
| 8. LAN switch (trang 33–35) | R79–R82 | 4 |
| 9. Firewall (trang 35–36) | R83–R85 | 3 |
| 10. Load balancer (trang 37–38) | R86–R87 | 2 |
| 11. Tủ Rack (trang 38–39) | R88–R90 | 3 |
| B. Cấp phát, thu hồi (trang 40–41) | R93–R94, R96 | 3 |
| Khái niệm — mapping CPU (trang 6–7) | R100 | 1 |
| BỔ SUNG — rà độ phủ 0.2 (trang in 9, 20) | R101, R105 | 2 |
| **Tổng** | | **77** |

**Quy ước ký hiệu chung:**
- `95th_P` : giá trị phần trăm thứ 95 của thông số tải P trong khoảng đo.
- `Kkpi_x` : hệ số đảm bảo KPI cho tài nguyên x (đảm bảo tải thực tế ≤ ngưỡng hiệu năng).
- `Ksosánh` : hệ số so sánh hệ mới / hệ tham chiếu.
- `Ksaisố`  : hệ số dự phòng sai số tính toán (= 1.1).
- `Kdph`    : hệ số dự phòng (chung); giá trị theo từng ngữ cảnh (1.2 / 1.1 / 1.25).

---

## Khái niệm — mapping chỉ số CPU (trang 6–7)

### R100 — Mapping `Cint_Rated` / `Cfp_Rated` ↔ chỉ số SPECrate
- **Loại:** định lượng — ràng buộc (bảng quy đổi chuẩn).
- **Nội dung:** chỉ số đánh giá CPU máy chủ được quy đổi theo bảng mapping:
  - `Cint_Rated` ↔ `SPECrate_int_base` (hệ CNTT thông thường) / `SPECrate_int_peak`
    (hệ tính toán tối ưu).
  - `Cfp_Rated` ↔ `SPECrate_fp_base` (dấu phảy động thông thường) / `SPECrate_fp_peak`
    (tính toán-biên dịch tối ưu).
- **Công thức:** quy đổi 1–1 theo cột chỉ số phù hợp loại hệ thống (không có phép tính).
- **Tham số đầu vào:** loại hệ thống (thông thường / tính toán tối ưu); chỉ số SPECrate
  đo được trên CPU.
- **Ngưỡng:** không có; chỉ là phép chọn cột mapping.
- **Đơn vị:** chỉ số SPECrate (points).
- **Trang:** 6–7.
- **Xử lý `Cint_Rated` (theo quy ước 0.3):** bảng `Cint_Rated`/`Cfp_Rated` theo từng dòng
  CPU (trước đây ở **Phụ lục 02 — không có trong PDF**) được thay bằng quy tắc thực dụng
  theo hình thức cấp phát — xem mục riêng **"Quy ước `Cint_rated` (Phụ lục 02)"** dưới đây.

## Quy ước `Cint_rated` (thay thế Phụ lục 02) — quyết định 0.3

> **Trạng thái:** đã được người dùng chốt (2026-08-24). Thay bảng `Cint_rated`/`Cfp_rated`
> theo từng dòng CPU (Phụ lục 02 không có trong PDF) bằng quy tắc mặc định theo **hình thức
> cấp phát**. Áp dụng cho các quy tắc cần giá trị `Cint_rated`: **R100, R16, R20, R43, R44, R52**.

**Phân loại theo hình thức cấp phát:**
- **VM (chiếm ~90%):** mặc định **1 vCPU = 3 `Cint_rated`**.
  - **Số lượng vCPU** được lấy từ một trong hai nguồn:
    1. **Đo lường trên hệ thống cũ muốn scale lên** — khi đã có hệ thống đang chạy.
    2. **Đo trên server test** — đối với hệ thống mới (chưa có hệ thống cũ).
- **Vật lý (chiếm ~10%):** **KHÔNG có mặc định** (`Cint_rated = None`).
  - Người làm sizing phải **tự lên trang `spec.org`** để lấy thông số `Cint` dựa theo cấu
    hình server vật lý được cấp phát.
  - **Không ưu tiên** do chỉ chiếm ~10% trường hợp → nếu thiếu, tạo finding nhóm
    "thiếu thông tin" (NT4), không bịa.

**Hệ quả khi triển khai ở C4:**
- Hệ **VM** (phần lớn): tính được `Cint_rated(1 vCPU) = 3` → công thức CPU chạy được ngay.
- Hệ **vật lý** (`Cint_rated = None`): các phép tính quy về SPEC (R43, R44, R52) **không
  tính được** → phải đánh dấu `None` + sinh finding "cần bổ sung Cint từ spec.org"
  (theo NT4), thay vì bịa giá trị.

---

## A.1 — Nguyên tắc định cỡ / ngưỡng KPI (trang 8–10)

### R01 — Tải đánh giá KPI = giá trị 95th
- **Loại:** định lượng — ngưỡng đo.
- **Công thức:** `P_danhgia = P95th(P)` — dùng giá trị 95th làm thước tải để so ngưỡng.
- **Tham số đầu vào:** chuỗi thời gian của từng thông số tải trong khoảng đo
  (ngày/tháng/năm).
- **Ngưỡng:** không có ngưỡng so; quy định thống kê dùng 95th thay vì trung bình/đỉnh tuyệt đối.
- **Đơn vị:** theo thông số tải (%, IOPS, GB…).
- **Trang:** 8.

### R02 — Máy chủ: tải CPU ≤ 75%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `CPU95th ≤ 75%`.
- **Tham số đầu vào:** `CPU95th` (%) — tải CPU mức 95th.
- **Ngưỡng:** **75%** (giới hạn cứng, đảm bảo dự phòng khi có đột biến).
- **Đơn vị:** %.
- **Trang:** 8.

### R03 — Máy chủ: tỷ lệ dùng RAM ≤ 90%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `RAM_dungluong ≤ 90% × RAM_caunhinh`.
- **Tham số đầu vào:** `RAM_dungluong` (GB) dùng 95th; `RAM_caunhinh` (GB) cấu hình.
- **Ngưỡng:** **90%**.
- **Đơn vị:** % (tương đối) / GB (tuyệt đối).
- **Trang:** 8.

### R04 — Máy chủ: tỷ lệ dùng ổ cứng ≤ 80%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `Dungluong_dung ≤ 80% × Dungluong_khadung`.
- **Tham số đầu vào:** `Dungluong_dung` (GB); `Dungluong_khadung` (GB, dung lượng
  khả dụng sau RAID/partition/format — đúng tinh thần R23).
- **Ngưỡng:** **80%**.
- **Đơn vị:** % / GB.
- **Trang:** 8.

### R05 — Thiết bị lưu trữ: hiệu năng (IOPS) ≤ 80%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `IOPS95th ≤ 80% × IOPS_toida`.
- **Tham số đầu vào:** `IOPS95th` (hiệu năng dùng ở mức 95th); `IOPS_toida` của loại ổ
  (xem R55).
- **Ngưỡng:** **80%**.
- **Đơn vị:** % / IOPS.
- **Trang:** 8.

### R06 — Thiết bị lưu trữ: dung lượng ≤ 80%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `Dungluong_dung ≤ 80% × Dungluong_khadung`.
- **Tham số đầu vào:** `Dungluong_dung` (GB); `Dungluong_khadung` (GB).
- **Ngưỡng:** **80%** (dung lượng).
- **Đơn vị:** % / GB.
- **Trang:** 8.

### R07 — Ngoại lệ R06: SSD HĐH / DB OLTP / cache / snapshot → 75%
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `Dungluong_dung ≤ 75% × Dungluong_khadung`.
- **Tham số đầu vào:** `Dungluong_dung`, `Dungluong_khadung` (GB), áp dụng cho SSD của:
  HĐH, DB OLTP, cache, snapshot (DB in-memory, write-intensive).
- **Ngưỡng:** **75%** — lý do: vượt quá thì tốc độ ghi SSD suy giảm đáng kể (xem R68).
- **Đơn vị:** % / GB.
- **Trang:** 8.

### R08 — Ngoại lệ R06: volume lớn / lâu dài → 80–90%
- **Loại:** định lượng — ngưỡng số tuyệt đối (khoảng).
- **Công thức:** kiểm tra `Dungluong_dung ≤ (80–90%) × Dungluong_khadung`, tùy trường hợp.
- **Tham số đầu vào:** `Dungluong_dung`, `Dungluong_khadung` (GB); áp dụng cho SSD & HDD
  volume lớn, dữ liệu lâu dài > 03 tháng, media, CDR.
- **Ngưỡng:** **80–90%** (khoảng tùy tình huống — cần người quyết định giá trị cụ thể).
- **Đơn vị:** % / GB.
- **Trang:** 8.
- **`[CHƯA CHẮC]`:** ngưỡng là một khoảng (80–90%), không phải hằng số đơn. C4 cần
  cấu hình theo tình huống thay vì một ngưỡng cứng.

### R09 — Thiết bị mạng: dự phòng 20% port & thông lượng
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `Port_thietke = Port_dung × 1.2`; tương tự cho thông lượng.
- **Tham số đầu vào:** `Port_dung`, `Throughput_dung` thực tế.
- **Ngưỡng:** hệ số dự phòng **20%** → hệ số nhân **1.2**.
- **Đơn vị:** port / Mbps–Gbps.
- **Trang:** 9.

### R11 — Máy chủ dự phòng tối thiểu N+1 (mức vật lý)
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `So_maychinh ≥ N` (vận hành bình thường khi 1 máy chủ lỗi) và số máy dự
  phòng `M ≥ 1` → tổng `N + M`, mặc định **N+1**.
- **Tham số đầu vào:** `N` (số máy hoạt động tối thiểu), `M` (số máy dự phòng, mặc định 1).
- **Ngưỡng:** `M = 1` (N+1) — ứng dụng/DB hoạt động bình thường khi 1 máy chủ lỗi.
- **Đơn vị:** máy chủ (node).
- **Trang:** 9. (Chi tiết N+M tại R51.)
- **`[CHƯA CHẮC]`:** xem bổ sung tại R51.

### R12 — Thiết bị mạng dự phòng 1+1
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `So_thietbi_mang = 2` (1 dự phòng) cho mỗi cụm thiết bị mạng quan trọng.
- **Tham số đầu vào:** danh sách thiết bị mạng.
- **Ngưỡng:** dự phòng **1+1** (đủ 2 bộ, 1 hoạt động + 1 dự phòng).
- **Đơn vị:** thiết bị.
- **Trang:** 9.

### R13 — Máy chủ ảo hóa: ≤ 32 vCPU và ≤ 128 GB RAM
- **Loại:** định lượng — ngưỡng số tuyệt đối.
- **Công thức:** kiểm tra `vCPU ≤ 32` AND `RAM ≤ 128 GB`.
- **Tham số đầu vào:** `vCPU`, `RAM` (GB) của từng VM.
- **Ngưỡng:** **32 vCPU**, **128 GB RAM** (giới hạn máy chủ ảo hóa).
- **Đơn vị:** vCPU / GB.
- **Trang:** 9.

### R15 — VM dự phòng (1+N) phải phân bổ trên 2 máy chủ vật lý
- **Loại:** định lượng — ngưỡng số (≥ 2 host).
- **Công thức:** kiểm tra số máy chủ vật lý chứa các VM dự phòng `≥ 2`.
- **Tham số đầu vào:** vị trí vật lý của các VM dự phòng (vd 2 VM DB dự phòng 1+1).
- **Ngưỡng:** **≥ 2 máy chủ vật lý** (chống lỗi cùng host).
- **Đơn vị:** host.
- **Trang:** 9.

### R16 — Đánh giá CPU bằng `Cint_rated` / `Cfp_rated`
- **Loại:** định lượng — ràng buộc (chuẩn đo).
- **Công thức:** `SPEC_CPU = Cint_Rated` (hoặc `Cfp_Rated` cho dấu phảy động) — chuẩn
  SPEC **CPU2017**; chỉ dùng SPEC CPU2006 nếu CPU không có kết quả 2017.
- **Tham số đầu vào:** loại chỉ số (int/fp), thế hệ SPEC (2017/2006).
- **Ngưỡng:** bắt buộc chuẩn SPEC CPU2017 (2006 chỉ khi không có kết quả 2017).
- **Đơn vị:** points.
- **Trang:** 9–10.
- **`[CHƯA CHẮC]`:** giá trị `Cint_Rated`/`Cfp_Rated` lấy theo quy ước hình thức cấp phát
  (VM: 1 vCPU = 3; vật lý: `None`, tự lấy từ spec.org) — xem mục "Quy ước `Cint_rated`".

### R17 — Quy đổi SPEC CPU2006 → CPU2017
- **Loại:** định lượng — ràng buộc (hệ số quy đổi).
- **Công thức:**
  - `SPEC2017_int_rate_peak  = SPEC2006_int_rate_peak  × 8.38`
  - `SPEC2017_int_rate_base  = SPEC2006_int_rate_base  × 9.36`
  - `SPEC2017_fp_rate_peak   = SPEC2006_fp_rate_peak   × 6.74`
  - `SPEC2017_fp_rate_base   = SPEC2006_fp_rate_base   × 7.38`
- **Tham số đầu vào:** chỉ số SPEC CPU2006 của từng hạng mục.
- **Ngưỡng:** hệ số cố định: **8.38 / 9.36 / 6.74 / 7.38** cho 4 hạng mục tương ứng.
- **Đơn vị:** points (SPEC).
- **Trang:** 10.

### R18 — Thiết bị lưu trữ đánh giá bằng IOPS + latency
- **Loại:** định lượng — ràng buộc (chuẩn đo).
- **Công thức:** kiểm tra đồng thời `IOPS95th ≤ 80% × IOPS_toida` (xem R05) **và**
  `latency ≤ ngưỡng` (phụ thuộc loại ổ/hệ thống, chưa định lượng trong tài liệu).
- **Tham số đầu vào:** `IOPS95th`, `latency` đo được.
- **Ngưỡng:** IOPS theo R05; latency **chuẩn đo kèm theo nhưng tài liệu không cho ngưỡng số**.
- **Đơn vị:** IOPS / ms.
- **Trang:** 10.
- **`[CHƯA CHẮC]`:** ngưỡng latency cụ thể KHÔNG được định nghĩa trong tài liệu. Cần xác
  nhận ngưỡng latency (theo loại ổ / theo loại hệ thống) trước khi áp dụng được ở C4.

### R19 — Dự phòng sai số tính toán ≤ 10%
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** hệ số dự phòng sai số xuyên suốt quá trình tính toán `Ksaisố = 1.1`
  (ứng vào ∑CPU, ∑RAM, ∑ổ cứng — xem R48, R49).
- **Tham số đầu vào:** không có (hằng số quy ước).
- **Ngưỡng:** sai số dự phòng **10%** → `Ksaisố = 1.1`.
- **Đơn vị:** hệ số (không thứ nguyên).
- **Trang:** 10.

---

## A.1 — Khái niệm / công thức (trang 7)

### R20 — Quy đổi SPEC của vCPU theo overcommit
- **Loại:** định lượng — công thức.
- **Công thức:**
  `specValue_vCPU = specValue_CPU / (numOfCores × OR)`
- **Tham số đầu vào:**
  - `specValue_CPU`: chỉ số SPEC của 1 CPU (points) — giá trị `Cint_Rated`/`Cfp_Rated`.
  - `numOfCores`: số core 1 CPU.
  - `OR`: tỷ lệ overcommit CPU (xem R21).
- **Ngưỡng:** không có (phép chia thuần).
- **Đơn vị:** points (vCPU).
- **Trang:** 7.

### R21 — Tỷ lệ overcommit (OR) CPU = 4 hoặc 2
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `OR = 4` (mặc định) hoặc `OR = 2` (VM hiệu năng cao).
- **Tham số đầu vào:** loại VM (chuẩn / hiệu năng cao).
- **Ngưỡng:** **OR = 4** (thường), **OR = 2** (hiệu năng cao); tỷ lệ 2:1 hoặc riêng
  phải tham khảo VTNet.
- **Đơn vị:** hệ số.
- **Trang:** 7.

### R22 — OR cho RAM = 1
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `OR_ram = 1` (không overcommit RAM).
- **Tham số đầu vào:** không có.
- **Ngưỡng:** **1**.
- **Đơn vị:** hệ số.
- **Trang:** 7.

---

## 4. Định cỡ máy chủ — chuẩn bị thông số (trang 17–21)

### R36 — Lấy tải 95th, tối thiểu 01 tháng
- **Loại:** định lượng — ngưỡng đo.
- **Công thức:** `P_danhgia = P95th(P, ≥ 1 tháng)` — bỏ khoảng máy chủ chạy không tải;
  nguồn tải: kiểm thử hiệu năng / giám sát / script / log.
- **Tham số đầu vào:** chuỗi thời gian tải `P`, độ dài quan sát.
- **Ngưỡng:** tối thiểu **01 tháng** (tính cả cao điểm).
- **Đơn vị:** theo thông số (% / IOPS / GB…).
- **Trang:** 19.

### R38 — Diskgroup / raidgroup: tải dung lượng & hiệu năng ≤ 80%
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `Dungluong_dung ≤ 80% × Dungluong_khadung` **và** `IOPS ≤ 80% × IOPS_toida`
  cho từng disk/raid group.
- **Tham số đầu vào:** dung lượng, IOPS từng group (95th).
- **Ngưỡng:** **80%** (cả dung lượng lẫn hiệu năng); ngoại lệ theo A.1 (R07, R08).
- **Đơn vị:** % / GB / IOPS.
- **Trang:** 18.

### R39 — Tác vụ backup đáp ứng thời gian hoàn thành
- **Loại:** định lượng — công thức (thời gian).
- **Công thức:** `Thoigian_backup = Dungluong_backup / Bandwidth_backup ≤ YeuCau_hoanthanh`.
  Kèm ràng buộc: mạng lưu trữ/IP phục vụ backup **không chiếm kênh traffic người dùng**.
- **Tham số đầu vào:** `Dungluong_backup` (GB), `Bandwidth_backup` (GB/s), yêu cầu thời
  gian hoàn thành (giờ).
- **Ngưỡng/ví dụ:** backup 1 TB trong 2 h → cần vùng lưu trữ SSD, cổng 32 Gbps.
  Công thức cần tính: tốc độ ≥ 1 TB / 2 h = 500 GB/h ≈ 1.14 GB/s.
- **Đơn vị:** GB / GBps / giờ.
- **Trang:** 21.

### R40 — Hệ số so sánh `Ksosánh`
- **Loại:** định lượng — công thức.
- **Công thức:**
  `Ksosánh = Thongsodautieu_he_moi / Thongsodautieu_he_tuongdong`
- **Tham số đầu vào:** giá trị thông số đầu vào (vd số CCU, QPS…) của hệ mới và hệ
  tham chiếu tương đồng.
- **Ngưỡng:** không có (tỷ lệ tính được ≥ 0).
- **Đơn vị:** hệ số (không thứ nguyên).
- **Trang:** 21.

### R41 — Kiểm thử ≥ 5 mẫu × ≥ 5 lần
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra số mẫu đầu vào tăng dần `≥ 5` và số lần đo mỗi mẫu `≥ 5`;
  kiểm thử toàn bộ nghiệp vụ chính.
- **Tham số đầu vào:** số mẫu, số lần lặp/mẫu.
- **Ngưỡng:** **≥ 5 mẫu**, **≥ 5 lần/mẫu**.
- **Đơn vị:** mẫu / lượt.
- **Trang:** 21.

### R42 — Định cỡ theo tổng tải giao dịch giờ peak
- **Loại:** định lượng — công thức (phương pháp).
- **Công thức:** `Tongtai_Peak = Σ (tải giao dịch của từng chức năng/nghiệp vụ tại giờ peak)`
  — mỗi module phục vụ nhiều loại giao dịch phải định cỡ theo tổng giao dịch đó.
- **Tham số đầu vào:** tải từng chức năng/nghiệp vụ tại giờ peak (QPS/TPS/CCU…).
- **Ngưỡng:** không có (phép tổng).
- **Đơn vị:** theo thông số giao dịch.
- **Trang:** 20.

---

## 4. Định cỡ máy chủ — công thức tài nguyên (trang 22–25)

### R43 — CPU máy chủ vật lý
- **Loại:** định lượng — công thức.
- **Công thức:**
  `CPUsudung = CPU95percentile × Cint_rated(1 CPU) × So_CPU_vatly`
- **Tham số đầu vào:**
  - `CPU95percentile`: tải CPU 95th (% của CPU, 0–1).
  - `Cint_rated(1 CPU)`: SPEC của 1 CPU (points).
  - `So_CPU_vatly`: số CPU vật lý.
- **Ngưỡng:** không có (tính tài nguyên dùng).
- **Đơn vị:** points-SPEC (tải tính quy về SPEC).
- **Trang:** 22.
- **`[CHƯA CHẮC]`:** cần giá trị `Cint_rated` — lấy theo quy ước hình thức cấp phát
  (VM: 1 vCPU = 3; vật lý: `None`, lấy từ spec.org) — xem mục "Quy ước `Cint_rated`".

### R44 — CPU máy chủ ảo
- **Loại:** định lượng — công thức.
- **Công thức:**
  `CPUsudung = CPU95percentile(VM) × (vCPU_mayao / tong_vCPU_vatly) × Cint_rated(1 CPU) × So_CPU_vatly`
- **Tham số đầu vào:**
  - `CPU95percentile(VM)`: tải CPU 95th của máy ảo.
  - `vCPU_mayao`, `tong_vCPU_vatly`: số vCPU máy ảo / tổng vCPU vật lý host.
  - `Cint_rated(1 CPU)`, `So_CPU_vatly` như R43.
- **Ngưỡng:** không có.
- **Đơn vị:** points-SPEC.
- **Trang:** 22.
- **`[CHƯA CHẮC]`:** cần giá trị `Cint_rated` — lấy theo quy ước hình thức cấp phát
  (VM: 1 vCPU = 3; vật lý: `None`, lấy từ spec.org) — xem mục "Quy ước `Cint_rated`".

### R45 — RAM
- **Loại:** định lượng — công thức.
- **Công thức:**
  `RAMsudung = RAM95percentile × Dungluong_RAM`
- **Tham số đầu vào:** `RAM95percentile` (0–1), `Dungluong_RAM` (GB); bổ sung RAM HĐH/ảo
  hóa khi cần (xem R46, R47).
- **Ngưỡng:** không có (tính lượng dùng).
- **Đơn vị:** GB.
- **Trang:** 22.

### R46 — HĐH máy chủ tối thiểu 02 core CPU + 04 GB RAM
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra `CPU_HDH ≥ 2 core` AND `RAM_HDH ≥ 4 GB`.
- **Tham số đầu vào:** cấu hình tối thiểu HĐH (Linux/Windows).
- **Ngưỡng:** **≥ 2 core CPU**, **≥ 04 GB RAM**.
- **Đơn vị:** core / GB.
- **Trang:** 22.

### R47 — Hypervisor: 10% CPU + 6 GB RAM
- **Loại:** định lượng — công thức.
- **Công thức:**
  `CPU_hypervisor = 0.10 × CPU_maychu`; `RAM_hypervisor = 6 GB`.
- **Tham số đầu vào:** `CPU_maychu` (tổng CPU máy chủ).
- **Ngưỡng:** **10%** CPU, **6 GB** RAM.
- **Đơn vị:** % / GB.
- **Trang:** 22.

### R48 — Công thức tổng tài nguyên
- **Loại:** định lượng — công thức.
- **Công thức:**
  `ΣCPU = ΣCPUsudung × Ksosánh / Kkpi_cpu × Ksaisố`
  (tương tự `ΣRAM = ΣRAMsudung × Ksosánh / Kkpi_ram × Ksaisố`,
  `ΣODia = ΣODia_sudung × Ksosánh / Kkpi_dia × Ksaisố`)
- **Tham số đầu vào:** `ΣCPUsudung` (từ R43/R44), `Ksosánh` (R40), `Kkpi_cpu` (R49),
  `Ksaisố = 1.1` (R19/R49).
- **Ngưỡng:** không có (phép tổng + hệ số).
- **Đơn vị:** theo tài nguyên (SPEC / GB / GB).
- **Trang:** 23.

### R49 — Hệ số đảm bảo KPI & sai số
- **Loại:** định lượng — ngưỡng số.
- **Công thức:**
  - `Kkpi_cpu    = 0.75`  (tương ứng ngưỡng CPU ≤ 75%, R02)
  - `Kkpi_ram    = 0.9`   (tương ứng RAM ≤ 90%, R03)
  - `Kkpi_dia    = 0.8`   (tương ứng ổ cứng ≤ 80%, R04)
  - `Ksaisố      = 1.1`   (dự phòng sai số, R19)
- **Tham số đầu vào:** không có (hằng số).
- **Ngưỡng:** **0.75 / 0.9 / 0.8 / 1.1**.
- **Đơn vị:** hệ số.
- **Trang:** 23.

### R50 — Cấu hình 01 máy chủ vật lý (hoạt động N máy)
- **Loại:** định lượng — công thức.
- **Công thức:**
  `CPU_1máy = ΣCPU / N`; `RAM_1máy = ΣRAM / N`.
- **Tham số đầu vào:** `ΣCPU`, `ΣRAM` (từ R48), `N` (số máy chủ hoạt động — chọn tối ưu
  chi phí & cân đối cấu hình).
- **Ngưỡng:** không có (phép chia trung bình).
- **Đơn vị:** SPEC / GB (mỗi máy).
- **Trang:** 24.

### R51 — Mức dự phòng N+M; M mặc định = 1
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `Tong_may = N + M`, mặc định `M = 1` (tức **N+1**); `M` điều chỉnh theo
  phân loại hệ thống.
- **Tham số đầu vào:** `N` (số máy hoạt động), `M` (dự phòng).
- **Ngưỡng:** **M = 1** (mặc định).
- **Đơn vị:** máy chủ.
- **Trang:** 24. (Bổ sung R11.)

### R52 — Quy đổi máy ảo
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `vCPU_thanhphan = ΣCPU_thanhphan / Cint_rated(1 vCPU)`
  - `Cint_rated(1 vCPU) = Cint_rated(1 CPU) / socore / sothread`
  - `sothread / 1 core = 2` với CPU Intel (Hyper-Threading)
- **Tham số đầu vào:** `ΣCPU_thanhphan` (SPEC), `Cint_rated(1 CPU)` (Phụ lục 02),
  `socore`, `sothread` (= 2 Intel).
- **Ngưỡng:** số thread/core = **2** (Intel).
- **Đơn vị:** vCPU / core / thread.
- **Trang:** 24.
- **`[CHƯA CHẮC]`:** cần giá trị `Cint_rated` — lấy theo quy ước hình thức cấp phát
  (VM: 1 vCPU = 3; vật lý: `None`, lấy từ spec.org) — xem mục "Quy ước `Cint_rated`".

---

## 5. Định cỡ thiết bị lưu trữ — thông số & công thức (trang 25–26)

### R54 — NL-SAS / SATA 7.2k → khuyến cáo RAID 6
- **Loại:** định lượng — ràng buộc (loại ổ → RAID).
- **Công thức:** nếu loại ổ = NL-SAS hoặc SATA 7.2k rpm (rebuild lâu) → `RAID = RAID 6`.
- **Tham số đầu vào:** loại ổ.
- **Ngưỡng:** RAID 6 bắt buộc/khuyến cáo cho 7.2k rpm.
- **Đơn vị:** cấp RAID.
- **Trang:** 25.

### R55 — IOPS tối đa theo loại ổ
- **Loại:** định lượng — ràng buộc (bảng giá trị).
- **Công thức:** bảng tra IOPS tối đa (tham khảo) theo loại ổ:
  | Loại ổ | IOPS tối đa |
  |--------|------------:|
  | NL-SAS / SATA 7.2k | 100 |
  | SAS 10k | 140 |
  | SAS/FC 15k | 210 |
  | Flash/SSD | ≥ 5000 (tùy chip SLC/MLC/eMLC/TLC) |
- **Tham số đầu vào:** loại ổ.
- **Ngưỡng:** **100 / 140 / 210 / ≥ 5000** IOPS.
- **Đơn vị:** IOPS.
- **Trang:** 25.

### R56 — Dung lượng thô
- **Loại:** định lượng — công thức.
- **Công thức:**
  `Dungluong_tho = Tong_canthiet × TyLe_RAID × TyLe_format × TyLe_saiso × TyLe_duphong`
- **Tham số đầu vào:**
  - `Tong_canthiet`: dung lượng dữ liệu thực cần (GB).
  - `TyLe_RAID`: tỷ lệ cấu hình RAID (R57).
  - `TyLe_format = 1.1` (R57).
  - `TyLe_saiso = 1.1` (R57).
  - `TyLe_duphong = 1.25` (R57) — mục tiêu dùng ≤ 80%.
- **Ngưỡng:** không có (phép nhân); các hệ số ở R57.
- **Đơn vị:** GB.
- **Trang:** 26.

### R57 — Tỷ lệ RAID / format / sai số / dự phòng
- **Loại:** định lượng — ngưỡng số.
- **Công thức:**
  - `TyLe_RAID = Tong_so_o / So_o_luu_du_lieu`
    - RAID 5, 6 ổ: 6/5
    - RAID 6, 8 ổ: 8/6
  - `TyLe_format  = 1.1`
  - `TyLe_saiso   = 1.1`
  - `TyLe_duphong = 1.25` (mục tiêu dùng ≤ 80% dung lượng)
- **Tham số đầu vào:** loại RAID, số ổ tổng, số ổ lưu dữ liệu.
- **Ngưỡng:** **1.1 / 1.1 / 1.25**; RAID theo loại.
- **Đơn vị:** hệ số.
- **Trang:** 26.

### R58 — Thêm dung lượng phục hồi
- **Loại:** định lượng — công thức.
- **Công thức:**
  `Dungluong_phuchoi = (So_ban_luu × Dungluong_1ban) + Dungluong_restore`
- **Ví dụ:** lưu online 3 bản backup 1 TB (3 TB) + khả năng restore 1 bản (1 TB)
  → cần **4 TB**.
- **Tham số đầu vào:** `So_ban_luu`, `Dungluong_1ban` (GB/ban), `Dungluong_restore` (GB).
- **Ngưỡng:** không có (phép cộng); cách tính theo ví dụ.
- **Đơn vị:** GB.
- **Trang:** 26.

---

## 5. Định cỡ lưu trữ — IOPS & số lượng ổ (trang 27–31)

### R60 — `IOPS hệ thống = Σ IOPS máy chủ`
- **Loại:** định lượng — công thức.
- **Công thức:**
  `IOPS_hethong = Σ IOPS_maychu`; `IOPS_maychu = Σ IOPS_phanvung` (giá trị 95th); đo bằng
  `iostat` định kỳ 1 phút/lần, thống kê **tối thiểu 7 ngày**, lấy `r/s` và `w/s`.
- **Tham số đầu vào:** IOPS 95th từng phân vùng (`r/s` + `w/s`) của từng máy chủ.
- **Ngưỡng:** thời gian đo **≥ 7 ngày**.
- **Đơn vị:** IOPS.
- **Trang:** 27.

### R61 — Frontend / Backend IOPS
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `Frontend_IOPS = IOPS_hethong`
  - `Backend_IOPS = Frontend_IOPS × (1 × %read + penalty × %write)`
- **Tham số đầu vào:** `Frontend_IOPS`, `%read`, `%write` (mặc định 65/35, R63),
  `penalty` (R62).
- **Ngưỡng:** không có (phép tính).
- **Đơn vị:** IOPS.
- **Trang:** 27.

### R62 — Write penalty theo RAID
- **Loại:** định lượng — ngưỡng số (hệ số).
- **Công thức:** `penalty` theo bảng:
  | RAID | Write penalty |
  |------|:-------------:|
  | RAID 0 | 1 |
  | RAID 1 | 1 |
  | RAID 5 | 5 |
  | RAID 6 | 6 |
- **Tham số đầu vào:** cấp RAID.
- **Ngưỡng:** **1 / 1 / 5 / 6**.
- **Đơn vị:** hệ số.
- **Trang:** 27.

### R63 — Tỷ lệ đọc/ghi = 65/35
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** `%read : %write = 65 : 35` (đa phần ứng dụng Viettel; fio rwmixread=65).
- **Tham số đầu vào:** không có (mặc định); ghi đè nếu có số liệu thực tế của hệ thống.
- **Ngưỡng:** **65% read / 35% write**.
- **Đơn vị:** %.
- **Trang:** 28.
- **`[CHƯA CHẮC]`:** tỷ lệ này là **mặc định** — cần xác nhận có được thay bằng số liệu
  thực tế riêng của hệ thống khi có hay không.

### R64 — Số ổ cứng = MAX(ổ dung lượng, ổ hiệu năng) + hotspare
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_o = MAX(So_o_theo_dungluong, So_o_theo_hieunang) + So_o_hotspare`
- **Tham số đầu vào:** kết quả R65 (hai loại ổ), hotspare (R69).
- **Ngưỡng:** không có (phép MAX + cộng).
- **Đơn vị:** ổ.
- **Trang:** 30.

### R65 — Số ổ theo dung lượng / theo hiệu năng
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `So_o_theo_dungluong = Dungluong_tho / Dungluong_1_o`
  - `So_o_theo_hieunang = Backend_IOPS × TyLe_duphong(1.25) / IOPS_loai_o`
    (mục tiêu dùng ≤ 80% hiệu năng)
- **Tham số đầu vào:** `Dungluong_tho` (R56), `Dungluong_1_o`, `Backend_IOPS` (R61),
  `IOPS_loai_o` (R55).
- **Ngưỡng:** hệ số dự phòng **1.25**; dùng ≤ **80%** hiệu năng.
- **Đơn vị:** ổ.
- **Trang:** 30.

### R66 — Dung lượng ổ thông dụng theo loại
- **Loại:** định lượng — ràng buộc (bảng giá trị). *Chuyển từ `đt` sang `đl` ngày
  2026-08-25; lý do ghi ở `rules-classification.md`, ngay dưới bảng tỷ lệ.*
- **Công thức:** kiểm `Dungluong_1_o` có nằm trong dải thông dụng của loại ổ không:

  | Loại ổ | Dải dung lượng thông dụng |
  |--------|---------------------------|
  | Flash / SSD | 100 GB – 1.92 TB |
  | SAS/FC 15k | 300 – 600 GB |
  | SAS/FC 10k | 300 GB – 2 TB |
  | SATA / NL-SAS 7.2k | 1 – 8 TB |

- **Tham số đầu vào:** `loai_o`, `Dungluong_1_o` (GB).
- **Ngưỡng:** bảng trên. Đây là dải **thông dụng**, không phải giới hạn cứng.
- **Đơn vị:** GB / TB.
- **Trang:** 30.
- **Mức nghiêm trọng:** `minor`. Ra ngoài dải không phải là sai — chỉ là dấu hiệu
  nên rà lại (ổ quá lạ thường khó mua, thời gian rebuild lâu, hoặc gõ nhầm đơn vị).
  Câu thông báo phải là **đề nghị xác nhận**, không phải khẳng định sai.
- **Liên hệ:** R55 (IOPS tối đa theo loại ổ) là bảng tra song song cho hiệu năng;
  R67 (chọn ổ tốc độ cao, dung lượng < 1 TB cho hệ đọc/ghi ngẫu nhiên cao) là
  khuyến nghị định tính đi kèm.

### R68 — SSD ở ≥ 75% dung lượng thì tốc độ ghi suy giảm
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra `%dungluong_SSD_đang_dung ≥ 75%` → cảnh báo suy giảm tốc độ ghi.
- **Tham số đầu vào:** dung lượng SSD đang dùng / tổng.
- **Ngưỡng:** **75%**.
- **Đơn vị:** %.
- **Trang:** 30. (Liên hệ R07.)

### R69 — Hotspare ≥ 02 ổ/loại hoặc 7% (làm tròn lên)
- **Loại:** định lượng — ngưỡng số.
- **Công thức:**
  `So_hotspare = maxhi(2, ceil(0.07 × So_o_cung_loai))` — lấy tối thiểu 02 ổ mỗi loại;
  nếu số ổ cùng loại lớn → **7% tổng số ổ cùng loại, làm tròn lên**.
- **Tham số đầu vào:** `So_o_cung_loai`.
- **Ngưỡng:** **≥ 02 ổ/loại** hoặc **7%**.
- **Đơn vị:** ổ.
- **Trang:** 31.

---

## 6. Định cỡ thiết bị sao lưu (trang 31–32)

### R70 — Tổng dung lượng sao lưu
- **Loại:** định lượng — công thức.
- **Công thức:**
  `Tong_dungluong_saoluu = Dungluong_saoluu_toanbo + Dungluong_saoluu_giatang`
  (theo thời gian lưu trữ dữ liệu).
- **Tham số đầu vào:** `Dungluong_saoluu_toanbo`, `Dungluong_saoluu_giatang` (GB).
- **Ngưỡng:** không có (phép cộng).
- **Đơn vị:** GB.
- **Trang:** 31.

### R71 — Số tape toàn bộ
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_tape_toanbo = (Dungluong_saoluu_toanbo / Dungluong_1_tape) × So_ban × HeSo_duphong`
- **Tham số đầu vào:** `Dungluong_saoluu_toanbo` (GB), `Dungluong_1_tape` (GB, theo LTO, R75),
  `So_ban` (số bản sao lưu), `HeSo_duphong`.
- **Ngưỡng:** `So_ban ≥ 2` (R74); `HeSo_duphong = 1.1` (R74).
- **Đơn vị:** tape.
- **Trang:** 31.
- **`[CHƯA CHẮC]`:** tài liệu không ghi tường minh `HeSo_duphong` trong R71 — suy ra từ
  R74 (1.1). Cần xác nhận.

### R72 — Số tape gia tăng
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_tape_giatang = (Dungluong_saoluu_giatang / Dungluong_1_tape) × So_ban × HeSo_duphong`
- **Tham số đầu vào:** tương tự R71 nhưng dùng `Dungluong_saoluu_giatang`.
- **Ngưỡng:** `So_ban ≥ 2`, `HeSo_duphong = 1.1` (R74).
- **Đơn vị:** tape.
- **Trang:** 32.
- **`[CHƯA CHẮC]`:** như R71 — suy từ R74.

### R73 — Dung lượng/giây, số driver & đường kết nối
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `Dungluong_giay = Tong_dungluong_can_saoluu / Thoigian_yeucau(giay)`
  - `So_driver = max(ceil(Dungluong_giay / Tốcđộ_1_tape), 2)`
  - `So_duongketnoi = max(ceil(Dungluong_giay / Tốcđộ_1_duong), 2)`
- **Tham số đầu vào:** `Tong_dungluong_can_saoluu` (GB), `Thoigian_yeucau` (giây),
  `Tốcđộ_1_tape` (MBps, R75), `Tốcđộ_1_duong` (MBps).
- **Ngưỡng:** tối thiểu **2 driver / 2 đường kết nối**.
- **Đơn vị:** GB/s, driver, đường.
- **Trang:** 32.

### R74 — ≥ 02 băng từ khác nhau; hệ số dự phòng 1.1
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** mỗi dữ liệu phải nằm trên **≥ 02 băng từ khác nhau**; `HeSo_duphong = 1.1`.
- **Tham số đầu vào:** số băng chứa 1 tập dữ liệu.
- **Ngưỡng:** **≥ 2 băng**, hệ số dự phòng **1.1**.
- **Đơn vị:** băng / hệ số.
- **Trang:** 32.

### R75 — Capacity / tốc độ tape theo LTO
- **Loại:** định lượng — ràng buộc (bảng giá trị).
- **Công thức:** bảng tra capacity & tốc độ:
  | Thế hệ | Capacity | Tốc độ (MBps) |
  |--------|---------:|--------------:|
  | LTO-3 | 400 GB | 80 |
  | LTO-4 | 800 GB | 120 |
  | LTO-5 | 1500 GB | 140 |
  | LTO-6 | 2500 GB | 160 |
  | LTO-7 | 6 TB | 300 |
  | LTO-8 | 12 TB | 360 |
  | LTO-9 | 18 TB | 400 |
- **Tham số đầu vào:** thế hệ LTO.
- **Ngưỡng:** bảng trên.
- **Đơn vị:** GB/TB và MBps.
- **Trang:** 32.

### R76 — Cleaning tape tương đương đầu đọc
- **Loại:** định lượng — ràng buộc (1:1).
- **Công thức:** `So_cleaning_tape = So_dau_doc(tape_drive)` (tỷ lệ 1:1).
- **Tham số đầu vào:** `So_dau_doc`.
- **Ngưỡng:** bằng số đầu đọc.
- **Đơn vị:** tape.
- **Trang:** 32.

---

## 7. Định cỡ SAN switch (trang 33)

### R77 — Số port = Σ(port dịch vụ) × 1.2
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_port_can = Σ(port_tungdichvu) × Kdph_port`, với `Kdph_port = 1.2`.
- **Tham số đầu vào:** số port từng dịch vụ.
- **Ngưỡng:** `Kdph_port = 1.2`.
- **Đơn vị:** port.
- **Trang:** 33.

### R78 — Port active/thiết bị; chọn switch 24/48
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `PortActive_1_thietbi = So_port_can / So_thietbi` (tối thiểu **02 thiết bị**)
  - `Port < 24` → switch **24 port**; `24–48` → switch **48 port**.
- **Tham số đầu vào:** `So_port_can` (R77), `So_thietbi` (≥ 2).
- **Ngưỡng:** **≥ 2 thiết bị**; phân cấp **24 / 48** port.
- **Đơn vị:** port / thiết bị.
- **Trang:** 33.

---

## 8. Định cỡ LAN switch (trang 33–35)

### R79 — Số port = (Σ dịch vụ + kiến trúc) × 1.2
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_port = (Σ port_dichvu + port_kientrucmang) × 1.2`
  — `< 24` → switch 24; `24–48` → switch 48 (hoặc stack 2×24).
- **Tham số đầu vào:** port từng dịch vụ, port theo kiến trúc mạng.
- **Ngưỡng:** hệ số **1.2**; phân cấp **24 / 48** (hoặc stack 2×24).
- **Đơn vị:** port.
- **Trang:** 34.

### R80 — Lưu lượng port TB; chọn bandwidth
- **Loại:** định lượng — ngưỡng số.
- **Công thức:**
  `Luu_luong_port_TB = Σ luu_luong_dichvu / So_port_dichvu`;
  chọn bandwidth theo quy tắc:
  - `< 100` → **100M** (ưu tiên 1000 nếu có thể mở rộng)
  - `100–1000` → **1000M**
  - `1000–10G` → **10G** (nếu không ghép port)
- **Tham số đầu vào:** lưu lượng từng dịch vụ, số port dịch vụ.
- **Ngưỡng:** chuẩn bandwidth **100 / 1000 / 10000** Mbps.
- **Đơn vị:** Mbps / Gbps.
- **Trang:** 34–35.

### R81 — Thông lượng thiết bị = bandwidth × port × 2
- **Loại:** định lượng — công thức.
- **Công thức:**
  `Thongluong_thietbi = Bandwidth_port × So_port × 2`
  (yêu cầu: `throughput ≥ Σ bandwidth các port`).
- **Tham số đầu vào:** `Bandwidth_port`, `So_port`.
- **Ngưỡng:** hệ số **2** (full duplex); `throughput ≥ Σ bandwidth port`.
- **Đơn vị:** Mbps/Gbps.
- **Trang:** 35.

### R82 — Ghép port tối đa 04 port
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra `So_port_ghep (1 logic) ≤ 4`.
- **Tham số đầu vào:** số port vật lý ghép thành 1 port logic.
- **Ngưỡng:** **≤ 04 port**.
- **Đơn vị:** port.
- **Trang:** 35.

---

## 9. Định cỡ Firewall (trang 35–36)

### R83 — Số port = (Σ zone + HA) × Kdph
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_port = (Σ port_tungzone + port_HA) × Kdph_port`
- **Tham số đầu vào:** port từng zone, port triển khai HA.
- **Ngưỡng:** `Kdph_port` (xem R09 → **1.2**); chọn switch theo R78/R79.
- **Đơn vị:** port.
- **Trang:** 36.
- **`[CHƯA CHẮC]`:** R83 không ghi tường minh giá trị `Kdph_port`; suy từ R09 (1.2).
  Cần xác nhận.

### R84 — Lưu lượng zone & thông lượng thiết bị
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `Luuluong_dichvu = So_ketnoi_dongthoi × Luuluong_moi_ketnoi`
  - `Luuluong_zone = Σ luuluong_cac_dichvu`
  - `Thongluong_thietbi = Σ(Luuluong_zone_up + down) × Kdph_thongluong`
- **Tham số đầu vào:** số kết nối đồng thời, lưu lượng mỗi kết nối, lưu lượng từng zone
  (up/down).
- **Ngưỡng:** `Kdph_thongluong` (xem R09 → **1.2**).
- **Đơn vị:** bps / kết nối.
- **Trang:** 36.
- **`[CHƯA CHẮC]`:** `Kdph_thongluong` suy từ R09 (1.2). Cần xác nhận.

### R85 — Throughput theo 1518 Byte (hoặc 512)
- **Loại:** định lượng — ràng buộc (chuẩn đo).
- **Công thức:** throughput firewall phải được đo theo kích cỡ gói **1518 Byte** (chuẩn)
  hoặc **512 Byte**; bandwidth port chọn theo ngưỡng 100M/1000M/10G (nếu không ghép port).
- **Tham số đầu vào:** kích cỡ gói đo chuẩn; bandwidth port.
- **Ngưỡng:** chuẩn gói **1518 / 512** Byte; bandwidth **100M/1000M/10G**.
- **Đơn vị:** Byte (gói), bps.
- **Trang:** 36.

---

## 10. Định cỡ thiết bị cân bằng tải (trang 37–38)

### R86 — CPS / TPS / thông lượng
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `So_port = Σ port_tungdichvu`
  - `CPS_L4 = Σ CPS × Kdph_CPS` (Kdph_CPS = **1.2**)
  - `TPS_L7 = Σ TPS × Kdph_TPS`
  - `Thongluong = Σ luuluong_dichvu × 1.2` (Kdph_luuluong = **1.2**)
- **Tham số đầu vào:** port, CPS, TPS, lưu lượng từng dịch vụ.
- **Ngưỡng:** `Kdph_CPS = 1.2`, `Kdph_luuluong = 1.2`; `Kdph_TPS` chưa ghi giá trị.
- **Đơn vị:** port / CPS / TPS / bps.
- **Trang:** 37–38.
- **`[CHƯA CHẮC]`:** R86 KHÔNG ghi giá trị `Kdph_TPS`. Cần xác nhận (nghi là 1.2
  đồng bộ các Kdph khác, nhưng không được bịa).

### R87 — Lưu lượng dịch vụ & chọn bandwidth
- **Loại:** định lượng — công thức.
- **Công thức:**
  - `Luuluong_dichvu = CPS × luuluong_1_CPS + TPS × luuluong_1_TPS`
  - chọn port: `< 1000` → **1000M**; `1000–10G` → **10G** (nếu không ghép port)
- **Tham số đầu vào:** CPS, TPS, lưu lượng mỗi CPS/TPS.
- **Ngưỡng:** chuẩn bandwidth **1000M / 10G**.
- **Đơn vị:** bps / Mbps.
- **Trang:** 38.

---

## 11. Định cỡ tủ Rack (trang 38–39)

### R88 — RU chuẩn theo thiết bị
- **Loại:** định lượng — ràng buộc (bảng giá trị).
- **Công thức:** bảng RU chuẩn:
  | Thiết bị | RU |
  |----------|:--:|
  | Máy chủ | 2U |
  | SAN switch | 1U |
  | Thiết bị lưu trữ | số tray × 3U |
  | Sao lưu | 8U |
  | Load balancer | 1U |
  | Firewall | 1U |
  | Switch | 1U |
- **Tham số đầu vào:** số lượng từng loại thiết bị, số tray lưu trữ.
- **Ngưỡng:** bảng trên.
- **Đơn vị:** RU (U).
- **Trang:** 39.
- **`[CHƯA CHẮC]`:** số RU/1 tray thiết bị lưu trữ phụ thuộc hãng — chưa có hằng số
  chung. Cần chốt chuẩn tray (vd 4U/24 disk…) khi có danh mục thiết bị.

### R89 — Số Rack = Tổng RU / 38
- **Loại:** định lượng — công thức.
- **Công thức:**
  `So_Rack = ceil(Tong_RU / 38)`
  (lấy **38** do bỏ 2U trên + 2U dưới để đi dây/thao tác — tổng rack 42U).
- **Tham số đầu vào:** `Tong_RU` (từ R88).
- **Ngưỡng:** mẫu số **38 RU**/rack.
- **Đơn vị:** rack.
- **Trang:** 39.

### R90 — Kích thước Rack & PDU
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra kích thước ràng buộc + bổ sung:
  - Cao **42U**, rộng **600mm**, sâu ≥ **1000mm**
  - **02 bộ PDU**
  - Nếu tổng công suất danh định vượt **mức cho phép của rack** → phân chia lại số rack.
- **Tham số đầu vào:** kích thước rack, công suất danh định thiết bị/rack.
- **Ngưỡng:** **42U / 600mm / ≥1000mm / 2 PDU**.
- **Đơn vị:** U / mm / bộ / kW.
- **Trang:** 39.
- **`[CHƯA CHẮC]`:** "mức công suất cho phép của rack" (kW) KHÔNG có giá trị cụ thể
  trong tài liệu. Cần xác nhận ngưỡng công suất/rack.

---

## B. Cấp phát, thu hồi hạ tầng CNTT (trang 40–41)

### R93 — Cấp phát đảm bảo hoạt động 06 tháng + quota
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra tài nguyên cấp phát đủ cho vận hành **06 tháng**; áp hạn ngạch
  (quota) và theo dõi điều chỉnh theo KPI.
- **Tham số đầu vào:** mức tăng trưởng tài nguyên dự kiến 6 tháng, quota hiện có.
- **Ngưỡng:** thời gian cấp phát đủ **06 tháng**.
- **Đơn vị:** tháng.
- **Trang:** 40.

### R94 — Overcommit ảo hóa: CPU ≤ 4, RAM ≤ 1.5
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** kiểm tra `OR_cpu ≤ 4` AND `OR_ram ≤ 1.5`.
- **Tham số đầu vào:** tỷ lệ overcommit CPU, RAM.
- **Ngưỡng:** CPU **≤ 4**, RAM **≤ 1.5**.
- **Đơn vị:** hệ số.
- **Trang:** 41.
- **`[CHƯA CHẮC]`:** R94 cho `OR_ram ≤ 1.5` trong khi R22 cho `OR_ram = 1` (định cỡ máy
  chủ). Hai ngưỡng này phục vụ 2 giai đoạn khác nhau (định cỡ vs cấp phát) — cần xác
  nhận với người thẩm định để không mâu thuẫn khi áp dụng.

### R96 — Thu hồi: CPU ≤ 15% hoặc RAM ≤ 30% (≥ 6 tháng)
- **Loại:** định lượng — ngưỡng số.
- **Công thức:** VTNet rà soát ≥ **06 tháng/lần**; máy chủ có **CPU ≤ 15%** hoặc
  **RAM ≤ 30%** trong thời gian đánh giá → xem xét thu hồi.
- **Tham số đầu vào:** tải CPU, RAM máy chủ trong chu kỳ đánh giá.
- **Ngưỡng:** CPU **≤ 15%** hoặc RAM **≤ 30%**; chu kỳ **≥ 6 tháng**.
- **Đơn vị:** % / tháng.
- **Trang:** 41.

---

## BỔ SUNG — hai quy tắc định lượng phát hiện khi rà độ phủ (mục 0.2)

> **Nguồn:** `docs/rules/rules-flat-draft.md` mục "BỔ SUNG". Hai quy tắc này nằm ngoài
> danh sách R01–R100 ban đầu, phát hiện khi rà độ phủ bằng `scripts/audit_rule_coverage.py`.
>
> **Số trang: đã thống nhất toàn file về SỐ TRANG IN** (2026-08-26, mục 0.5) — trước
> đây R01–R100 dùng số trang bản lần 06 (= trang in + 1). Xem
> `rules-flat-draft.md` mục "Ghi chú về số trang".

### R101 — Cơ chế dự phòng bắt buộc theo mức độ quan trọng
- **Loại:** định lượng — ràng buộc (ánh xạ enum → enum).
- **Trích dẫn nguyên văn** (đã nối lại từ bị ngắt dòng `active-` / `standby`):
  > Các thiết bị phần cứng phải đảm bảo hoạt động với cơ chế dự phòng active-active
  > (đối với các hệ thống Rất quan trọng trở lên) hoặc active-standby (đối với các hệ
  > thống Quan trọng).
- **Công thức:**
  ```
  co_che_yeu_cau(muc_do) =
      "active-active"   nếu muc_do ∈ {đặc biệt quan trọng, rất quan trọng}
      "active-standby"  nếu muc_do == quan trọng
      None              nếu muc_do == bình thường          # [CHƯA CHẮC] — xem dưới

  bậc("none") = 0 < bậc("active-standby") = 1 < bậc("active-active") = 2

  ĐẠT      khi  bậc(co_che_khai) ≥ bậc(co_che_yeu_cau)
  VI PHẠM  khi  bậc(co_che_khai) <  bậc(co_che_yeu_cau)
  ```
- **Tham số đầu vào:**
  - `muc_do_quan_trong` — enum 4 giá trị `đặc biệt quan trọng` / `rất quan trọng` /
    `quan trọng` / `bình thường` (lấy từ mục checklist `CL-2.10`).
  - `co_che_du_phong_khai` — enum `active-active` / `active-standby` / `none`, **khai
    theo từng phân hệ** (`CL-3.x.6`), không phải một giá trị cho cả hệ thống.
- **Ngưỡng:** bảng ánh xạ ở trên; không có phép tính số.
- **Đơn vị:** không (enum).
- **`scope`:** `phan_he` — chấm một lần cho mỗi phân hệ. Căn cứ: `QD849-02` yêu cầu
  khai dự phòng nội site theo từng module.
- **Trang:** 9 (trang in).
- **Thiếu thông tin:** `muc_do_quan_trong` hoặc `co_che_du_phong_khai` là `None` →
  finding nhóm "thiếu thông tin" (NT4), **không** suy ra giá trị mặc định.
- **`[CHƯA CHẮC]` (a):** mức **`bình thường`** — Guideline không quy định cơ chế nào.
  Tạm xử lý: trả `không áp dụng`, KHÔNG sinh finding. Đây đúng là câu hỏi đang treo với
  đơn vị thẩm định (*"mức bình thường có bắt buộc cơ chế dự phòng nội site nào không?"*).
- **`[CHƯA CHẮC]` (b):** khai **cao hơn** mức yêu cầu (hệ `Quan trọng` khai
  `active-active`) — theo công thức trên là ĐẠT, không sinh finding vi phạm. Có nên
  sinh thêm finding `minor` "cấu hình dự phòng cao hơn yêu cầu, cân nhắc chi phí" không?
  Cần xác nhận; mặc định hiện tại là **không sinh**.
- **Liên quan:** R10 (không quá tải khi mất 1 node), R11, R12, `QD849-01`, `QD849-02`.
  R101 **trả lời điểm `[CẦN XÁC NHẬN]` đang treo ở `QD849-02`** — mức độ quan trọng
  **có** ép chọn cơ chế dự phòng nội site, và ràng buộc đó nằm ngay trong Guideline.

### R105 — Định cỡ ở cả hai mức; tổng toàn hệ = tổng các module
- **Loại:** định lượng — kiểm nhất quán số.
- **Trích dẫn nguyên văn:**
  > Định cỡ phải đáp ứng được yêu cầu đầu vào của đơn vị yêu cầu, bao gồm: Định cỡ toàn
  > bộ hệ thống và chi tiết đến từng module […] Bảng tổng hợp nhu cầu tài nguyên toàn hệ
  > thống sẽ bao gồm tổng hợp kết quả tính toán của từng Module (tổng hợp lại một số
  > thành phần dùng chung như mạng, Firewall, LB).
- **Công thức:** với **mỗi loại tài nguyên** `r` xuất hiện trong bảng tổng hợp:
  ```
  Tong_toan_he[r]  ==  Σ(module m) Tong_module[m][r]  +  Σ(dùng chung c) Tong_chung[c][r]
  ```
  Kiểm bằng dung sai:
  ```
  lech[r]     = | Tong_toan_he[r] − (Σ module + Σ dùng chung) |
  lech_tuongdoi[r] = lech[r] / Tong_toan_he[r]
  ĐẠT khi   lech[r] ≤ 1 đơn vị  HOẶC  lech_tuongdoi[r] ≤ 0.5%     # [CHƯA CHẮC]
  ```
- **Tham số đầu vào:**
  - `Tong_toan_he[r]` — bảng tổng hợp cấu hình toàn hệ thống (`CL-2.9`).
  - `Tong_module[m][r]` — bảng tổng hợp cấu hình từng phân hệ (`CL-3.x.20`).
  - `Tong_chung[c][r]` — tài nguyên **thành phần dùng chung** (mạng, Firewall, LB) không
    thuộc phân hệ nào. **Bắt buộc phải có số hạng này trong công thức**, nếu bỏ qua sẽ
    báo lệch giả cho mọi bản sizing có FW/LB.
  - `r` ∈ {vCPU, RAM (GB), lưu trữ (GB), IOPS, băng thông (Mbps), số node}.
- **Ngưỡng:** dung sai `≤ 1 đơn vị` hoặc `≤ 0.5%` (xem `[CHƯA CHẮC]`).
- **Đơn vị:** theo từng `r` — vCPU / GB / IOPS / Mbps / node.
- **`scope`:** `he_thong` — chấm một lần, nhưng đọc dữ liệu của mọi phân hệ.
- **Trang:** 20 (trang in).
- **Thiếu thông tin (NT4):** thiếu hẳn bảng tổng hợp toàn hệ **hoặc** thiếu bảng của
  một phân hệ → finding nhóm **"thiếu thông tin"**, KHÔNG phải finding "sai số liệu".
  Đây cũng chính là mục Vòng 1 `CL-2.9` / `CL-3.x.20`; theo mô hình hai vòng, trượt
  Vòng 1 thì C7 **chặn** finding R105 của Vòng 2.
- **`[CHƯA CHẮC]`:** giá trị dung sai. Guideline không cho con số; `1 đơn vị / 0.5%` là
  đề xuất để hấp thụ sai lệch làm tròn, chưa được người thẩm định xác nhận. Đặt trong
  `globals` của `rules.yaml` để sửa được không cần code.
- **Ghi chú nguồn:** quy tắc "tổng toàn hệ = tổng các phân hệ" trước đây được đề xuất ở
  `rules-checklist-flat.md` như một quy tắc **chưa nguồn nào nêu** (`CL-2.9` ↔ `CL-3.x.20`).
  Nay **đã có nguồn văn bản** là R105 — bỏ ghi chú "chưa có nguồn" ở mục 0.5.

---

## Danh sách điểm cần xác nhận với người thẩm định (NT4 — KHÔNG bịa)

Dưới đây là các chỗ **thiếu thông tin / mơ hồ / mâu thuẫn** phát hiện khi viết công thức.
Cần xác nhận trước khi số hóa (0.5) để tránh code-sai. Mỗi mục ghi rõ quy tắc liên quan.

### A. Dữ liệu phụ lục thiếu (ảnh hưởng nhiều quy tắc)
1. **`[ĐÃ CHỐT]` Phụ lục 02** — bảng `Cint_Rated`/`Cfp_Rated` theo dòng CPU **không có
   trong file PDF** (kết thúc trang 44/44) → **đã thay bằng quy ước 0.3** theo hình thức
   cấp phát: VM (90%) 1 vCPU = 3 `Cint_rated`; vật lý (10%) không mặc định, tự lấy từ
   `spec.org`. Áp dụng **R100, R16, R20, R43, R44, R52**. Chi tiết: mục "Quy ước `Cint_rated`".
2. **`[CHƯA CHẮC]` Phụ lục 01** — mẫu tài liệu định cỡ (liên quan R34 định tính) cũng
   không có trong PDF.

### B. Hệ số chưa ghi tường minh (cần chốt giá trị)
3. **`[CHƯA CHẮC]` R83, R84** — `Kdph_port`, `Kdph_thongluong` cho Firewall không ghi
   tường minh; suy từ R09 (1.2). Xác nhận có dùng hệ số 1.2 không.
4. **`[CHƯA CHẮC]` R86** — `Kdph_TPS` (layer 7) KHÔNG cho giá trị. Các hệ số khác của
   LB đều 1.2. Xác nhận.
5. **`[CHƯA CHẮC]` R71, R72** — `HeSo_duphong` cho số tape không ghi tường minh; suy từ
   R74 (1.1). Xác nhận.

### C. Ngưỡng khoảng / không có giá trị số
6. **`[CHƯA CHẮC]` R08** — ngưỡng là **khoảng 80–90%** (không phải hằng số đơn). Cần
   xác định chọn giá trị nào theo tình huống → cấu hình được trong `rules.yaml`.
7. **`[CHƯA CHẮC]` R18** — ngưỡng **latency** không được định lượng trong tài liệu.
   Cần ngưỡng theo loại ổ/hệ thống.
8. **`[CHƯA CHẮC]` R90** — "mức công suất cho phép của rack" (kW) không có số. Cần
   ngưỡng công suất/rack.

### D. Mâu thuẫn cần làm rõ
9. **`[CHƯA CHẮC]` R22 vs R94** — `OR_ram`: R22 (định cỡ máy chủ) = **1**; R94 (cấp phát
   ảo hóa) ≤ **1.5**. Khác ngữ cảnh, nhưng cần xác nhận để không đánh giá sai khi so
   một con số vào cả hai.
10. **`[CHƯA CHẮC]` R63** — tỷ lệ 65/35 là "đa phần ứng dụng" → hỏi có được thay bằng số
    liệu đo thực tế riêng của hệ thống khi có không.
11. **`[CHƯA CHẮC]` R88** — RU/tray thiết bị lưu trữ phụ thuộc hãng; cần chốt chuẩn tray.

### E. Phát sinh từ hai quy tắc bổ sung (2026-08-26)
12. **`[CHƯA CHẮC]` R101(a)** — hệ mức **`bình thường`**: Guideline không quy định cơ chế
    dự phòng nào. Hiện trả `không áp dụng`. Trùng với câu hỏi đang treo với đơn vị thẩm định.
13. **`[CHƯA CHẮC]` R101(b)** — khai cơ chế **cao hơn** mức yêu cầu (hệ `Quan trọng` khai
    `active-active`): có sinh finding `minor` về chi phí không? Mặc định hiện tại: không.
14. **`[CHƯA CHẮC]` R105** — **dung sai** khi so tổng toàn hệ với tổng các phân hệ.
    Guideline không cho con số; đề xuất `≤ 1 đơn vị` hoặc `≤ 0.5%`, đặt trong `globals`.

---

## Tổng kết

- Đã viết rõ **công thức / tham số đầu vào / ngưỡng / đơn vị / trang** cho **77 quy tắc
  định lượng** (nhóm tại bảng tổng hợp ở đầu tài liệu).
- **14 điểm cần xác nhận** (mục trên); đã chốt **1 điểm** (Phụ lục 02 → quy ước
  VM/vật lý), còn **13 điểm** `[CHƯA CHẮC]` — đều đánh dấu in ngay tại quy tắc, không bịa giá trị.
- Kết quả này là đầu vào cho **mục 0.5** (số hóa `rules.yaml` theo Phụ lục A của
  `docs/ke-hoach-trien-khai.md`) và cho **C4** (thực thi bằng code, NT1).
