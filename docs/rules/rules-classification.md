# Mục 0.2 — Phân loại quy tắc: định lượng / định tính

> **Nguồn:** `docs/rules/rules-flat-draft.md` — 100 quy tắc R01–R100 rút từ
> `3-Guideline_Dinh_co_thiet_bi_CNTT_final.pdf` (Giai đoạn 0.1).
>
> **Phạm vi mục 0.2:** chỉ phân loại mỗi quy tắc thành **định lượng** (kiểm bằng
> code, C4) hay **định tính** (kiểm bằng RAG+LLM, C5). Chưa gán mã `STO-xx`
> (mục 0.5), chưa viết công thức/tiêu chí chi tiết (mục 0.3/0.4).

## Tiêu chí phân loại

- **`[đl]` Định lượng** (→ C4, Rules-as-Code): quy tắc mà code tự đánh giá
  đạt/không sau khi có số liệu trích xuất, thuộc một trong:
  1. **Ngưỡng số tuyệt đối** — so một con số với hằng số (CPU ≤ 75%, ≥ 2 tape…).
  2. **Công thức tính** — đầu vào là số, ra số (∑CPU, IOPS, số port, số rack…).
  3. **Ràng buộc hệ số / nhất quán số liệu** — tỷ lệ dự phòng 1.2/1.1/1.25,
     RAID write penalty, 65/35 read/write, bảng loại ổ ↔ IOPS/capacity.
- **`[đt]` Định tính** (→ C5, RAG + LLM): quy tắc cần phán đoán nội dung/ngữ cảnh,
  không quy về công thức được, thuộc một trong:
  1. **Yêu cầu thủ tục/quy trình** — xin xác nhận bằng văn bản, xin ý kiến thẩm
     định, thống nhất công cụ, lưu vết/ký xác nhận.
  2. **Yêu cầu mô tả/tường minh** — phải mô tả rõ (đặc tính, swap/huge-page),
     nêu đặc điểm tương đồng, chỉ rõ yếu tố mở rộng dọc/ngang.
  3. **Phán xét theo tình huống** — đối tượng áp dụng/ngoại lệ, chọn phương pháp
     định cỡ theo trường hợp.

> Ghi chú: các dòng **định nghĩa thuật ngữ** (95th, CCU, vCPU, SPEC, 1+1, N+1…)
> ở phần khái niệm không phải quy tắc kiểm → bị loại khỏi danh sách 100 quy tắc;
> chúng chỉ phục vụ ngữ nghĩa cho 0.3/0.4.

## Tỷ lệ tổng hợp — nguồn Guideline

> ⚠️ **Bảng này là kết quả TRUNG GIAN** (100 quy tắc đầu tiên). Sau khi rà độ phủ ở
> Phần 2, nguồn Guideline có **110 quy tắc — 77 `đl` / 33 `đt`**. Tỷ lệ chung cho cả
> bốn nguồn xem Phần 2 mục 4.

| Nhóm | Số quy tắc | Tỷ lệ |
|------|-----------:|------:|
| Định lượng (`[đl]`) | 75 | **75%** |
| Định tính (`[đt]`) | 25 | **25%** |
| **Tổng** | **100** | 100% |

> **Điều chỉnh 2026-08-25 — R66 chuyển từ `đt` sang `đl`.**
> Lý do: **R55** (*IOPS tối đa theo loại ổ*) đã được xếp `đl` với lý do
> "ràng buộc (bảng giá trị)". **R66** (*dung lượng ổ thông dụng theo loại*) có đúng
> cấu trúc đó — một bảng tra theo loại ổ, code so giá trị khai báo với dải cho phép,
> không cần phán đoán. Xếp hai quy tắc cùng hình dạng vào hai nhóm khác nhau là
> không nhất quán.
>
> Chữ "thông dụng" (mang tính khuyến nghị, không phải ngưỡng cứng) được thể hiện
> bằng **`severity: minor`** và câu chữ đề nghị xác nhận, **không** bằng cách xếp
> sang nhóm định tính. Phân loại quyết định *ai kiểm* (C4 hay C5), mức nghiêm trọng
> quyết định *nói nặng hay nhẹ* — hai việc khác nhau.
>
> Công thức đã bổ sung vào `rules-formulas.md`. Trước điều chỉnh: 74 `đl` / 26 `đt`.

**Nhận định:** phản lớn quy tắc (74%) là định lượng — C4 (rules-as-code) sẽ gánh
gần hết giá trị kiểm tra, đồng thời đây là phần có độ tin cậy cao nhất. Nhóm
định tính (26%) tập trung ở quy trình/phương pháp định cỡ (Dạng I–III), thủ tục
xác nhận và chiến lược cấp phát/thu hồi — cần RAG + LLM với trích dẫn bắt buộc.
Kết luận này phù hợp hướng dẫn rà lại sau Giai đoạn 0 (xem `docs/ke-hoach-trien-khai.md`
mục 3.1): ưu tiên đầu tư C4 trước, C5 phục vụ phần quy trình.

## Bảng phân loại chi tiết (100 quy tắc đầu — R101–R110 xem `rules-flat-draft.md` mục BỔ SUNG)

> `Nhóm`: **đl** = định lượng, **đt** = định tính. `Lý do`: loại tiêu chí (ngưỡng /
> công thức / ràng buộc hệ số / thủ tục / mô tả / tình huống).

### Khái niệm — mapping chỉ số CPU (trang 6–7)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R100 | Mapping `Cint_Rated`↔`SPECrate_int`… theo loại hệ | đl | ràng buộc (bảng quy đổi chuẩn) | 6–7 |

### A.1 — Nguyên tắc định cỡ / ngưỡng KPI (trang 8–10)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R01 | Tải đánh giá KPI = giá trị 95th | đl | ngưỡng đo | 8 |
| R02 | Máy chủ: tải CPU ≤ 75% | đl | ngưỡng số | 8 |
| R03 | Máy chủ: tỷ lệ dùng RAM ≤ 90% | đl | ngưỡng số | 8 |
| R04 | Máy chủ: tỷ lệ dùng ổ cứng ≤ 80% | đl | ngưỡng số | 8 |
| R05 | Lưu trữ: hiệu năng IOPS ≤ 80% | đl | ngưỡng số | 8 |
| R06 | Lưu trữ: dung lượng ≤ 80% | đl | ngưỡng số | 8 |
| R07 | Ngoại lệ R06: SSD HĐH/OLTP/cache… → 75% | đl | ngưỡng số | 8 |
| R08 | Ngoại lệ R06: volume lớn/lâu dài → 80–90% | đl | ngưỡng số | 8 |
| R09 | Mạng: dự phòng 20% port & thông lượng | đl | ngưỡng số | 9 |
| R10 | Dự phòng không quá tải khi 1 node lỗi | đt | tình huống (đánh giá kiến trúc) | 9 |
| R11 | Máy chủ dự phòng tối thiểu N+1 | đl | ngưỡng số | 9 |
| R12 | Thiết bị mạng dự phòng 1+1 | đl | ngưỡng số | 9 |
| R13 | VM ảo hóa ≤ 32 vCPU và ≤ 128 GB RAM | đl | ngưỡng số | 9 |
| R14 | Hiệu năng cao vượt cấu hình → máy chủ vật lý | đt | tình huống | 9 |
| R15 | VM dự phòng phải phân bổ 2 máy chủ vật lý | đl | ngưỡng số (≥2 host) | 9 |
| R16 | Đánh giá CPU bằng Cint_rated/Cfp_rated | đl | ràng buộc (chuẩn đo) | 9–10 |
| R17 | Quy đổi SPEC2006→2017: hệ số 8.38/9.36/6.74/7.38 | đl | ràng buộc (hệ số) | 10 |
| R18 | Lưu trữ đánh giá bằng IOPS + latency | đl | ràng buộc (chuẩn đo) | 10 |
| R19 | Dự phòng sai số tính toán ≤ 10% | đl | ngưỡng số | 10 |

### A.1 — Khái niệm / công thức (trang 7)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R20 | `specValue_vCPU = specValue_CPU / (cores × OR)` | đl | công thức | 7 |
| R21 | Tỷ lệ overcommit OR CPU = 4 hoặc 2 | đl | ngưỡng số | 7 |
| R22 | OR cho RAM = 1 | đl | ngưỡng số | 7 |
| R23 | Phân biệt dung lượng dùng được / dung lượng thô | đt | mô tả (diễn giải số liệu) | 7 |

### A.2 — Cơ sở định cỡ (trang 10–11)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R24 | Kết quả định cỡ không chính xác 100% | đt | mô tả (khái niệm) | 10 |
| R25 | Xác định yếu tố mở rộng/thu hẹp | đt | tình huống | 10 |
| R26 | Dạng I: định cỡ theo hệ tham chiếu tương đồng | đt | tình huống (đánh giá tương đồng) | 11 |
| R27 | Dạng I + không có tham chiếu → hoàn thiện sản phẩm | đt | quy trình | 11 |
| R28 | Dạng II: định cỡ bằng môi trường kiểm thử | đt | tình huống (chọn phương pháp) | 11 |

### A.2 — Dạng III + quy trình (trang 12–16)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R29 | Dạng III: định cỡ theo hiện trạng + yêu cầu mở rộng | đt | tình huống | 12 |
| R30 | Thông số đầu vào phải được xác nhận bằng văn bản | đt | thủ tục | 14 |
| R31 | Biên bản kiểm thử phải được xác nhận văn bản | đt | thủ tục | 14 |
| R32 | Chỉ rõ yếu tố scale up/out + kiểm thử ngưỡng tới hạn | đt | mô tả | 14–15 |
| R33 | Hạ tầng Tập đoàn → xin ý kiến thẩm định VTNet | đt | thủ tục | 15 |
| R34 | Hoàn thiện tài liệu theo mẫu Phụ lục 01 | đt | thủ tục | 15 |
| R35 | Thông số phải ảnh hưởng năng lực xử lý | đt | tình huống | 16 |

### 4. Định cỡ máy chủ — chuẩn bị thông số (trang 17–21)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R36 | Tải lấy 95th tối thiểu 1 tháng | đl | ngưỡng đo | 19 |
| R37 | Chỉ rõ cấu hình CPU/RAM/ổ đầy đủ | đt | mô tả | 20 |
| R38 | Diskgroup/raidgroup tải ≤ 80% | đl | ngưỡng số | 18 |
| R39 | Backup đáp ứng thời gian hoàn thành (vd 1TB/2h) | đl | công thức (thời gian) | 21 |
| R40 | `Ksosánh = hệ mới / hệ tương đồng` | đl | công thức | 21 |
| R41 | Kiểm thử ≥ 5 mẫu × ≥ 5 lần | đl | ngưỡng số | 21 |
| R42 | Định cỡ theo tổng tải giờ peak | đl | công thức (phương pháp) | 20 |

### 4. Định cỡ máy chủ — công thức tài nguyên (trang 22–25)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R43 | CPU máy chủ vật lý: công thức | đl | công thức | 22 |
| R44 | CPU máy ảo: công thức | đl | công thức | 22 |
| R45 | RAM: công thức | đl | công thức | 22 |
| R46 | HĐH yêu cầu ≥ 2 core CPU + 04 GB RAM | đl | ngưỡng số | 22 |
| R47 | Hypervisor: 10% CPU + 6GB RAM | đl | công thức | 22 |
| R48 | Tổng tài nguyên: ∑CPU = ∑dùng × Ksosánh/Kkpi × Ksaisố | đl | công thức | 23 |
| R49 | Kkpi_cpu 0.75 / Kkpi_ram 0.9 / Kkpi_disk 0.8; Ksaisố 1.1 | đl | ngưỡng số | 23 |
| R50 | Cấu hình 1 máy = ∑/N | đl | công thức | 24 |
| R51 | Mức dự phòng N+M, M mặc định = 1 | đl | ngưỡng số | 24 |
| R52 | Quy đổi máy ảo (vCPU, thread/core = 2 Intel) | đl | công thức | 24 |
| R53 | Mô tả tài nguyên dedicare, swap/huge-page | đt | mô tả | 25 |

### 5. Định cỡ lưu trữ — thông số & công thức (trang 25–26)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R54 | NL-SAS/SATA 7.2k khuyến cáo RAID 6 | đl | ràng buộc (loại ổ → RAID) | 25 |
| R55 | IOPS tối đa theo loại ổ (100/140/210/≥5000) | đl | ràng buộc (bảng giá trị) | 25 |
| R56 | `Dung lượng thô = Tổng × RAID × format × sai số × dự phòng` | đl | công thức | 26 |
| R57 | Tỷ lệ RAID/format 1.1/sai số 1.1/dự phòng 1.25 | đl | ngưỡng số | 26 |
| R58 | Thêm dung lượng phục hồi (3 bản 1TB + restore → 4TB) | đl | công thức | 26 |
| R59 | Hệ hiệu năng cao phải tính hiệu năng từng phân vùng | đt | mô tả (phạm vi) | 26 |

### 5. Định cỡ lưu trữ — IOPS & số lượng ổ (trang 27–31)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R60 | IOPS hệ thống = ∑IOPS máy chủ (95th, ≥7 ngày) | đl | công thức | 27 |
| R61 | Frontend/Backend IOPS: công thức | đl | công thức | 27 |
| R62 | Write penalty: RAID5=5, RAID6=6 | đl | ngưỡng số (hệ số) | 27 |
| R63 | Tỷ lệ đọc/ghi = 65/35 | đl | ngưỡng số | 28 |
| R64 | Số ổ = MAX(ổ dung lượng, ổ hiệu năng) + hotspare | đl | công thức | 30 |
| R65 | Công thức số ổ theo dung lượng / theo hiệu năng | đl | công thức | 30 |
| R66 | Dung lượng ổ thông dụng theo loại | **đl** | ràng buộc (bảng giá trị) — *đổi từ `đt` ngày 2026-08-25, xem ghi chú dưới bảng tỷ lệ* | 30 |
| R67 | Hệ đọc/ghi ngẫu nhiên cao nên dùng ổ tốc độ cao | đt | tình huống (khuyến nghị) | 30 |
| R68 | SSD ≥ 75% dung lượng thì tốc độ ghi giảm | đl | ngưỡng số | 30 |
| R69 | Hotspare ≥ 02 ổ/loại hoặc 7% (làm tròn lên) | đl | ngưỡng số | 31 |

### 6. Định cỡ sao lưu (trang 31–32)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R70 | Tổng dung lượng sao lưu = toàn bộ + gia tăng | đl | công thức | 31 |
| R71 | Số tape toàn bộ: công thức | đl | công thức | 31 |
| R72 | Số tape gia tăng: công thức | đl | công thức | 32 |
| R73 | Dung lượng/giây + số driver/đường kết nối | đl | công thức | 32 |
| R74 | ≥ 2 băng từ; hệ số dự phòng 1.1 | đl | ngưỡng số | 32 |
| R75 | Capacity/tốc độ tape theo LTO-3..LTO-9 | đl | ràng buộc (bảng giá trị) | 32 |
| R76 | Cleaning tape tương đương đầu đọc | đl | ràng buộc (1:1) | 32 |

### 7. Định cỡ SAN switch (trang 33)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R77 | Số port = ∑port × 1.2 | đl | công thức | 33 |
| R78 | Port active/thiết bị; chọn switch 24/48 | đl | công thức | 33 |

### 8. Định cỡ LAN switch (trang 33–35)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R79 | Số port = (∑dịch vụ + kiến trúc) × 1.2 | đl | công thức | 34 |
| R80 | Chọn bandwidth port 100/1000/10000 | đl | ngưỡng số | 34–35 |
| R81 | Thông lượng = bandwidth × port × 2 | đl | công thức | 35 |
| R82 | Ghép port tối đa 04 port | đl | ngưỡng số | 35 |

### 9. Định cỡ Firewall (trang 35–36)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R83 | Số port = (∑zone + HA) × Kdựphòng | đl | công thức | 36 |
| R84 | Lưu lượng zone + thông lượng thiết bị | đl | công thức | 36 |
| R85 | Throughput theo 1518 Byte (hoặc 512) | đl | ràng buộc (chuẩn đo) | 36 |

### 10. Định cỡ load balancer (trang 37–38)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R86 | CPS/TPS/thông lượng công thức | đl | công thức | 37–38 |
| R87 | Lưu lượng dịch vụ + chọn bandwidth | đl | công thức | 38 |

### 11. Định cỡ tủ Rack (trang 38–39)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R88 | RU chuẩn theo thiết bị (2U, tray×3U, 8U…) | đl | ràng buộc (bảng giá trị) | 39 |
| R89 | Số rack = ∑RU / 38 | đl | công thức | 39 |
| R90 | Kích thước rack 42U/600mm/1000mm; 02 PDU | đl | ngưỡng số | 39 |

### B. Cấp phát, thu hồi hạ tầng (trang 40–42)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R91 | Hệ thống triển khai trên Cloud Tập đoàn (trừ ngoại lệ) | đt | tình huống | 40 |
| R92 | Cấp phát chỉ khi có đủ hồ sơ | đt | thủ tục | 40 |
| R93 | Cấp phát đảm bảo hoạt động 06 tháng + quota | đl | ngưỡng số | 40 |
| R94 | Overcommit CPU ≤ 4, RAM ≤ 1.5 | đl | ngưỡng số | 41 |
| R95 | Big data Bare-Metal, còn lại ảo hóa | đt | tình huống | 41 |
| R96 | Thu hồi: CPU ≤ 15% hoặc RAM ≤ 30% (≥6 tháng) | đl | ngưỡng số | 41 |
| R97 | Ưu tiên giảm số máy chủ trước | đt | quy trình | 42 |

### C. Kiểm thử hiệu năng (trang 43–44)

| Mã | Quy tắc tóm tắt | Nhóm | Lý do | Trang |
|----|-----------------|:----:|-------|------:|
| R98 | Dùng công cụ chuẩn: sysbench/jmeter/ab | đt | mô tả (chọn công cụ) | 43–44 |
| R99 | Thống nhất công cụ + lưu vết/ký xác nhận | đt | thủ tục | 44 |

---

# PHẦN 2 — Chốt phân loại và tỷ lệ cho CẢ BỐN NGUỒN (2026-08-25)

> Phần 1 ở trên chỉ phủ nguồn Guideline và dừng ở 100 quy tắc. Phần này rà lại độ
> phủ, hợp nhất bốn nguồn và chốt tỷ lệ chung — đây mới là kết quả cuối của mục 0.2.

## 1. Rà độ phủ nguồn Guideline — 100 → 110 quy tắc

Sau khi phát hiện R101/R102 bị sót (khi lấy trích dẫn cho mục 0.4), đã rà lại toàn
bộ 44 trang bằng `scripts/audit_rule_coverage.py`. Công cụ đếm **câu mang dấu hiệu
quy phạm** ("phải", "không vượt quá", "tối thiểu"…) trên mỗi trang rồi so với số quy
tắc đã bắt ở trang đó, gắn cờ trang nào chênh lệch lớn.

| | Trước rà | Sau rà |
|---|---:|---:|
| Câu quy phạm phát hiện được | 115 | 115 |
| Lượt quy tắc gắn trang | 108 | 116 |
| Trang bị gắn cờ (ngưỡng 4) | 3 | **0** |
| **Tổng quy tắc Guideline** | **100** | **110** |

**10 quy tắc bổ sung** (chi tiết ở `rules-flat-draft.md` mục "BỔ SUNG"):

| Mã | Nội dung | Loại | Trang |
|---|---|:--:|---|
| R101 | Cơ chế dự phòng bắt buộc theo mức độ quan trọng (active-active / active-standby) | đl | 9 |
| R102 | Mức dự phòng căn cứ phân loại hệ thống theo quy định hiện hành | đt | 9 |
| R103 | Phải nêu tính sẵn sàng (phút/tháng) và downtime cho phép mỗi sự cố | đt | 18 |
| R104 | Phải nêu các yếu tố ảnh hưởng thông số tài nguyên máy chủ (tài liệu liệt kê 11) | đt | 18 |
| R105 | Định cỡ ở cả hai mức: toàn hệ thống **và** từng module; tổng phải khớp | đl | 20 |
| R106 | Sau khi định cỡ giao dịch, phải thiết kế cho tính sẵn sàng/dự phòng/CTKT | đt | 20 |
| R107 | Phải có giải pháp sao lưu phục hồi; cộng thêm năng lực cho tác vụ sao lưu | đt | 20 |
| R108 | Cấp phát LB/lưu trữ tránh lưu lượng vòng nhiều lớp mạng; node ảo hóa quan trọng an toàn khi sự cố | đt | 40 |
| R109 | Đơn vị chủ quản và TCT VTNet thống nhất phương án cấp phát | đt | 40 |
| R110 | Phải nêu tổng thuê bao và giao dịch Peak, phân tách theo nghiệp vụ kèm tỉ lệ % | đt | 17 |

Hai quy tắc đáng chú ý:
- **R101** trả lời điểm `[CẦN XÁC NHẬN]` treo ở `QD849-02` — mức độ quan trọng **có**
  ép chọn cơ chế dự phòng, và ràng buộc nằm trong Guideline chứ không phải 849/QĐ.
- **R105** chính là quy tắc *"tổng toàn hệ thống = tổng các phân hệ"* mà tôi đã đề
  xuất khi làm checklist (`CL-2.9` ↔ `CL-3.x.20`) — **nay có nguồn văn bản**, không
  còn là đề xuất tự nghĩ.

> **Giới hạn của công cụ:** nó khoanh vùng, không kết luận. Câu có chữ "phải" chưa
> chắc là quy tắc, và một quy tắc có thể trải nhiều câu. Kết quả "0 trang bị gắn cờ"
> nghĩa là **không còn chênh lệch bất thường**, không phải bảo đảm tuyệt đối không sót.

---

## 2. Sửa hai lỗi đếm phát hiện khi hợp nhất

**(a) Nguồn code web app có 46 quy tắc, không phải 42.** Đếm lại từng bảng con của
`docs/0.1-danh-sach-quy-tac.md` phần A: A1 7 · A2 6 · A3 7 · A4 8 · A5 3 · A6 7 ·
A7 4 · A8 2 · A9 2 = **46**. Con số 42 ghi ở các file trước là lỗi cộng của tôi, đã
sửa ở `PLAN.md`, `0.1-danh-sach-quy-tac.md`, `checklist-tham-dinh.md`.

**(b) R66 còn tag `[đt]` trong `rules-flat-draft.md`.** Khi chốt chuyển R66 sang định
lượng, tôi mới sửa ở file này mà quên file danh sách phẳng — hai file lệch nhau
suốt từ đó. Đã sửa.

---

## 3. Phân loại theo nguồn

| Nguồn | Vòng | Tổng | `đl` | `đt` | Ghi chú |
|---|:--:|---:|---:|---:|---|
| **Guideline** GL.CNVTQĐ.CNTT.18 | 2 | **110** | 77 | 33 | Nguồn có thẩm quyền |
| **Văn bản khác** (849/QĐ, quy hoạch zone) | 2 | **3** | 3 | 0 | Mới có quy tắc lõi, chờ văn bản đầy đủ |
| **Code web app** | 2 | **46** | 42 | 4 | ~19 trùng Guideline; phần còn lại **chưa có căn cứ văn bản** |
| **Checklist thẩm định** | **1** | **37** | 0 | 37 | Toàn bộ là kiểm "có thông tin chưa" |

### Vì sao toàn bộ checklist là `đt`

Mọi quy tắc Vòng 1 đều hỏi cùng một câu — *"tài liệu có phần này chưa?"* — nên đều
cần C5 đọc hiểu nội dung, không có công thức nào để code tự quyết. Ký hiệu
`ĐT→ĐL(Rxx)` trong `rules-checklist-flat.md` **không** có nghĩa quy tắc đó nửa nọ
nửa kia: nó là **ĐT ở Vòng 1**, còn `Rxx` là quy tắc **ĐL ở Vòng 2** đã được đếm
riêng bên nguồn Guideline. Không tính trùng.

Bốn mục đánh dấu `ĐL` trong bảng checklist (`CL-2.10`, `CL-2.11`, `CL-3.x.6`…) cũng
vậy — phần định lượng thuộc `QD849-01`/`QD849-02`, đã đếm ở dòng "Văn bản khác".

---

## 4. Tỷ lệ chung sau khử trùng

Khử trùng: ~19 quy tắc code trùng Guideline (xem `rules-crossmap.md` mục 1) → chỉ
còn ~27 quy tắc code là riêng, và những quy tắc này **chưa có căn cứ văn bản**.

| | Số quy tắc | Tỷ lệ |
|---|---:|---:|
| **Vòng 2 — kiểm đúng/sai** | **~140** | |
| — `đl` (C4, thuần code) | ~105 | **75%** |
| — `đt` (C5, RAG + LLM) | ~35 | 25% |
| **Vòng 1 — kiểm đủ mục** | **37** | |
| — `đt` toàn bộ (C5, bar thấp) | 37 | 100% |
| **TỔNG** | **~177** | |
| — `đl` | ~105 | **59%** |
| — `đt` | ~72 | **41%** |

> Dấu `~` là có chủ ý: con số chính xác phụ thuộc việc khử trùng từng quy tắc code,
> làm ở mục 0.5 khi số hóa `rules.yaml`. Sai số ước tính ±5 quy tắc.

### Điều này đổi gì so với kết luận ban đầu

Khi mới có nguồn Guideline, tỷ lệ là **74% đl / 26% đt** và tôi kết luận "C4 gánh gần
hết giá trị, C5 chỉ phục vụ phần quy trình". Sau khi có đủ bốn nguồn, tỷ lệ định
tính tăng lên **41%** — **C5 nay gánh phần lớn hơn hẳn dự tính ban đầu.**

Nhưng đây **không** phải tin xấu, vì ba lý do:

1. **Nếu chỉ xét Vòng 2, tỷ lệ vẫn là 75/25** — đúng như kết luận ban đầu. Phần định
   tính tăng thêm nằm trọn ở Vòng 1.
2. **37 quy tắc Vòng 1 dùng chung MỘT tiêu chí duy nhất** — *"có thông tin thực chất
   là ĐẠT"*. Đây là dạng kiểm định tính **dễ nhất và ổn định nhất**: không phán xét
   chất lượng, chỉ xác định có/không. Rủi ro sai lệch thấp hơn nhiều so với kiểu
   "đánh giá lập luận có thuyết phục không".
3. **Vòng 1 chặn Vòng 2** — mục trượt Vòng 1 thì finding Vòng 2 bị chặn. Nghĩa là
   phần C5 rẻ chạy trước, lọc bớt việc cho phần C4/C5 đắt chạy sau.

**Hệ quả cho thứ tự làm ở Giai đoạn 1:** không nên dồn hết công vào C4 rồi mới làm
C5 như kế hoạch ban đầu ngầm định. Vòng 1 (C5 bar thấp) là thứ **chạy trước trong
pipeline** và phủ được 37 quy tắc bằng một tiêu chí — nên làm sớm, và nó cũng chính
là nền cho mục 1.17 (điền hộ cột C của checklist).

---

## 5. Việc còn lại của 0.2

- [x] Rà độ phủ Guideline → 110 quy tắc, 0 trang gắn cờ
- [x] Sửa hai lỗi đếm (46 quy tắc code; R66 tag)
- [x] Chốt phân loại 4 nguồn và tỷ lệ chung
- [x] **Phân loại `đl`/`đt` cho 10 quy tắc mới R101–R110** — **XONG 2026-08-26.**
      2 quy tắc `đl` (R101, R105) đã có công thức ở `rules-formulas.md` mục "BỔ SUNG";
      8 quy tắc `đt` (R102, R103, R104, R106, R107, R108, R109, R110) đã có tiêu chí ở
      `rules-criteria.md` mục 5.7. **Tỷ lệ ở Phần 2 không đổi** — bảng mục 3 và mục 4
      đã tính sẵn theo 110 quy tắc (77 `đl` / 33 `đt`), việc này chỉ hiện thực hóa
      con số đó sang hai file 0.3/0.4.
- [ ] Khử trùng chính xác nhóm quy tắc code — làm ở mục 0.5
