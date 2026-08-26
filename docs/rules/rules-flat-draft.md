# Mục 0.1 — Danh sách phẳng quy tắc (bản nháp đang xây dựng)

> **Nguồn:** `3-Guideline_Dinh_co_thiet_bi_CNTT_final.pdf` — "GUIDELINE ĐỊNH CỠ,
> CẤP PHÁT HẠ TẦNG CNTT" (Viettel), mã hiệu GL.CNVTQĐ.CNTT.18, lần ban hành 06,
> hiệu lực 01/10/2021 → 01/10/2023. PDF vật lý có **45 trang** (trang tài liệu đánh
> số 1/44 → 44/44).
>
> **Ghi chú giai đoạn 0.1:** chỉ lập danh sách phẳng. Đánh số thứ tự tạm `R01...`
> (chưa phải mã quy tắc `STO-xx`/`CPU-xx` — sẽ gán ở mục 0.5).
>
> **Ghi chú giai đoạn 0.2 (phân loại):** mỗi quy tắc đã được gắn ký hiệu phân loại
> chính thức cuối dòng:
> - `[đl]` = **định lượng** → kiểm bằng code thuần (C4): có ngưỡng số tuyệt đối,
>   công thức tính, hoặc ràng buộc hệ số kiểm được. Ví dụ: CPU ≤ 75%, công thức
>   ∑CPU, RAID write penalty.
> - `[đt]` = **định tính** → cần phán đoán nội dung/ngữ cảnh (C5): yêu cầu thủ tục
>   (xin xác nhận bằng văn bản, xin ý kiến thẩm định), yêu cầu mô tả/tường minh,
>   hoặc phán xét theo tình huống. Ví dụ: "xin ý kiến thẩm định VTNet".
>
> Các dòng **không đánh số R** ở phần khái niệm (95th, CCU, vCPU, SPEC, 1+1… chỉ
> là **định nghĩa thuật ngữ** phục vụ ngữ nghĩa, không phải quy tắc kiểm) được
> tách riêng, **không tính** vào danh sách quy tắc để 0.3/0.4 không xử lý lầm.
>
> **Ghi chú trạng thái đọc:** toàn bộ 45 trang đã đọc được (text sạch sau khi lọc
> watermark theo font — dùng `scripts/extract_pdf_text.py`). **Không trang nào bị
> "không đọc được"**, không phải dùng tới OCR. Thay đổi so với dự đoán ban đầu:
> text layer khôi phục được đầy đủ nhờ watermark dùng font riêng.
>
> **Ghi chú phụ lục thiếu (cần xác nhận):** tài liệu thân bài tham chiếu tới
> **Phụ lục 01** (mẫu biểu tài liệu định cỡ — mục R34) và **Phụ lục 02** (bảng
> Cint_rated/Cfp_rated các dòng CPU — các mục R52, R88...), nhưng hai phụ lục này
> **không nằm trong file PDF**. File kết thúc ở trang 44/44. Cần xác nhận có file
> riêng hay không (ảnh hưởng mức độ phủ khi lập `rules.yaml` ở mục 0.5).

## Tài liệu — thông tin chung

- Tham chiếu tới bộ tiêu chuẩn chất lượng dịch vụ CNTT: `TC.CNVTQĐ.CNTT.25`
- Gắn với Guideline phân chia mức độ quan trọng hệ thống: `GL.CNVTQĐ.CNTT.03`
- Mục lục: I. Mục đích · II. Khái niệm, phạm vi · III. Tài liệu tham chiếu ·
  IV. Nội dung (A. Định cỡ hạ tầng CNTT trang 8–40 · B. Cấp phát, thu hồi hạ tầng 40 ·
  C. Kiểm thử hiệu năng 43)

---

## Khái niệm — mapping chỉ số CPU (trang 6–8)

- **R100** [đl] Mapping chỉ số đánh giá CPU (tương thích tài liệu cũ): `Cint_Rated`
  ↔ `SPECrate_int_base` (hệ CNTT thông thường) / `SPECrate_int_peak` (hệ tính toán tối
  ưu); `Cfp_Rated` ↔ `SPECrate_fp_base` (dấu phảy động thông thường) /
  `SPECrate_fp_peak` (tính toán-biên dịch tối ưu). | trang 6–7
- (Định nghĩa thuật ngữ cơ bản — 95th, CCU, RPS, QPS/TPS, latency, IOPS, Frontend/
  Backend IOPS, 1+1, N+1, vCPU, SPEC… nằm ở trang 6–7, phục vụ ngữ nghĩa quy tắc, được
  ghi trong phần khái niệm của tài liệu.)

## A.1 — Nguyên tắc định cỡ (ngưỡng KPI) — trang 9–11

- **R01** [đl] Tải hệ thống để đánh giá KPI = giá trị **95th** các thông số tải
  trong khoảng đo (ngày/tháng/năm). | trang 8
- **R02** [đl] Máy chủ: tải CPU **không vượt quá 75%**. | trang 8
- **R03** [đl] Máy chủ: tỷ lệ sử dụng dung lượng RAM **không vượt quá 90%**. | trang 8
- **R04** [đl] Máy chủ: tỷ lệ sử dụng dung lượng ổ cứng **không vượt quá 80%**. | trang 8
- **R05** [đl] Thiết bị lưu trữ: hiệu năng (IOPS) **không vượt quá 80%**. | trang 8
- **R06** [đl] Thiết bị lưu trữ: dung lượng **không vượt quá 80%**. | trang 8
- **R07** [đl] Ngoại lệ R06: ổ SSD cho HĐH / DB OLTP / cache / snapshot (DB in-mem,
  write-intensive) → giới hạn **75%**; vượt quá thì tốc độ ghi suy giảm. | trang 8
- **R08** [đl] Ngoại lệ R06: ổ (SSD & HDD) volume lớn, dữ liệu lâu dài > 03 tháng,
  media, CDR → có thể **80–90%** tùy trường hợp. | trang 8
- **R09** [đl] Thiết bị mạng: dự phòng **20%** số port và thông lượng. | trang 9
- **R10** [đt] Hệ thống dự phòng (active-active / active-standby): không được
  hoạt động quá tải khi 1 node lỗi. | trang 9
- **R11** [đl] Máy chủ dự phòng tối thiểu **N+1** mức vật lý: ứng dụng/DB hoạt
  động bình thường khi 1 máy chủ lỗi. | trang 9
- **R12** [đl] Thiết bị mạng dự phòng **1+1**. | trang 9
- **R13** [đl] Máy chủ ảo hóa: cấu hình **≤ 32 vCPU và ≤ 128 GB RAM** (giới hạn
  server ảo hóa). | trang 9
- **R14** [đt] Dịch vụ yêu cầu hiệu năng cao vượt cấu hình quy định máy chủ ảo
  hóa → định cỡ máy chủ **vật lý**. | trang 9
- **R15** [đl] VM đóng vai trò dự phòng 1+N (vd 2 VM DB dự phòng 1+1) → phải
  phân bổ trên **hai máy chủ vật lý**. | trang 9
- **R16** [đl] Máy chủ đánh giá CPU bằng **Cint_rated** / **Cfp_rated** (SPEC
  CPU2017; chỉ dùng SPEC CPU2006 nếu CPU không có kết quả 2017). | trang 9–10
- **R17** [đl] Quy đổi SPEC CPU2006 → 2017: int_rate_peak ×**8.38**;
  int_rate_base ×**9.36**; fp_rate_peak ×**6.74**; fp_rate_base ×**7.38**. | trang 10
- **R18** [đl] Thiết bị lưu trữ đánh giá bằng **IOPS + latency**. | trang 10
- **R19** [đl] Dự phòng sai số tính toán định cỡ: sai số **≤ 10%**. | trang 10

## A.1 — Khái niệm / công thức (trang 8)

- **R20** [đl] Quy đổi SPEC của vCPU theo overcommit:
  `specValue_vCPU = specValue_CPU / (numOfCores × OR)`. | trang 7
- **R21** [đl] Tỷ lệ overcommit (OR) CPU thường là **4** hoặc **2** (VM hiệu năng
  cao); tỷ lệ 2:1 hoặc riêng phải tham khảo VTNet. | trang 7
- **R22** [đl] OR cho RAM = **1**. | trang 7
- **R23** [đt] Phân biệt "dung lượng lưu trữ" (dùng được sau RAID/partition/format)
  và "dung lượng thô" (trước RAID). | trang 7

## A.2 — Cơ sở định cỡ — Dạng III + quy trình (trang 13–17)

- **R29** [đt] Dạng III (nâng cấp hệ thống): định cỡ căn cứ hiện trạng hoạt động
  (tải, số người dùng, chất lượng dịch vụ) + yêu cầu mở rộng (CCU/TPS/RPS, latency);
  sau khi có tải phải đánh giá & điều chỉnh sizing. | trang 12
- **R30** [đt] Thông số đầu vào định cỡ phải được **lãnh đạo đơn vị chủ trì sản phẩm xác
  nhận bằng văn bản**; yêu cầu từ đơn vị/kinh doanh cần có xác nhận của bộ phận liên quan. | trang 14
- **R31** [đt] Biên bản kiểm thử hiệu năng phải được lãnh đạo đơn vị thực hiện kiểm thử
  xác nhận bằng văn bản. | trang 14
- **R32** [đt] Khi tính tài nguyên từng thành phần, phải **chỉ rõ yếu tố mở rộng dọc/ngang
  (scale up/scale out)** và kết quả kiểm thử ngưỡng tới hạn 1 node làm cơ sở mở rộng. | trang 14–15
- **R33** [đt] Hệ thống triển khai trên hạ tầng Tập đoàn → tài liệu định cỡ phải **xin ý
  kiến thẩm định TCT VTNet**. | trang 15
- **R34** [đt] Tài liệu định cỡ hoàn thiện theo **mẫu Phụ lục 01**, qua các bước: chuẩn bị
  thông số → tính tài nguyên → xác định số lượng/cấu hình → hoàn thiện hồ sơ → thẩm định
  → phê duyệt. | trang 15
- **R35** [đt] Các thông số chọn phục vụ định cỡ phải **ảnh hưởng đến năng lực xử lý/quản
  lý** của tài nguyên phần cứng và phần mềm. | trang 16

## 4. Định cỡ máy chủ — chuẩn bị thông số (trang 18–20)

- **R36** [đl] Tải máy chủ lấy **giá trị 95th** các thông số tải; với hệ thống tham
  chiếu/hiện tại phải lấy tải tối thiểu **01 tháng** (tính cả cao điểm), bỏ khoảng
  máy chủ chạy không tải; tải lấy từ kiểm thử hiệu năng / giám sát / script / log. | trang 19
- **R37** [đt] Tải và cấu hình hệ thống: cần chỉ rõ cấu hình CPU (số lượng + dòng/model,
  với ảo hóa ghi rõ vCPU ↔ model pCPU), RAM (GB), ổ cứng (dung lượng khả dụng sau RAID
  + IOPS & latency từng phân vùng). | trang 20
- **R38** [đl] Diskgroup (DB) / raidgroup (storage): tải dung lượng & hiệu năng
  **không quá 80%** (ngoại lệ theo A.1). | trang 18
- **R39** [đl] Tác vụ backup phải đáp ứng yêu cầu thời gian hoàn thành (vd backup
  1TB trong 2h → vùng lưu trữ backup phải là SSD, cổng 32Gbps); mạng lưu trữ/IP phục
  vụ backup không chiếm kênh traffic người dùng. | trang 21

## 4. Định cỡ máy chủ — hệ số so sánh & kiểm thử (trang 21–22)

- **R40** [đl] Xác định **hệ số so sánh Ksosánh** = tỷ lệ thông số đầu vào giữa hệ
  thống mới và hệ thống tham chiếu tương đồng: hệ mới/ hệ tương đồng. | trang 21
- **R41** [đl] Đã có phần mềm: kiểm thử hiệu năng đo tài nguyên (CPU, RAM) với mẫu
  đầu vào tăng dần, tối thiểu **05 mẫu**, mỗi mẫu **≥ 05 lần**, kiểm thử toàn bộ
  nghiệp vụ chính. | trang 21
- **R42** [đl] Định cỡ toàn bộ hệ thống dựa trên **tổng tải giao dịch tại giờ Peak**
  (tổ hợp toàn bộ chức năng/nghiệp vụ); mỗi module phục vụ nhiều loại giao dịch phải
  định cỡ theo tổng giao dịch đó. | trang 20

## 4. Định cỡ máy chủ — công thức tính tài nguyên (trang 23–24)

- **R43** [đl] Máy chủ vật lý:
  `CPUsử dụng = CPU95percentile × Cint_rated(1 CPU) × số CPU vật lý`. | trang 22
- **R44** [đl] Máy chủ ảo:
  `CPUsử dụng = CPU95percentile(máy ảo) × vCPU_máyảo / tổng_vCPU_vậtlý × Cint_rated(1 CPU) × số CPU vật lý`. | trang 22
- **R45** [đl] `RAMsử dụng = RAM95percentile × dung lượng RAM`; tính thêm RAM cho HĐH/ảo hóa khi cần. | trang 22
- **R46** [đl] HĐH Linux/Windows (máy chủ) yêu cầu **tối thiểu 02 core CPU và 04GB RAM**. | trang 22
- **R47** [đl] Phần mềm ảo hóa (hypervisor): cấp tương đương **10% CPU máy chủ + 6GB RAM**. | trang 22
- **R48** [đl] Công thức tổng tài nguyên:
  `∑CPU = ∑CPUsử dụng × Ksosánh / Kkpi × Ksaisố` (tương tự ∑RAM, ∑ổ cứng). | trang 23
- **R49** [đl] Hệ số đảm bảo KPI: `Kkpi_cpu = 0.75`, `Kkpi_ram = 0.9`, `Kkpi_ổ cứng = 0.8`;
  `Ksaisố = 1.1` (dự phòng sai số). | trang 23
- **R50** [đl] Cấu hình 01 máy chủ vật lý khi hoạt động N máy: `CPU_1máy = ∑CPU/N`,
  `RAM_1máy = ∑RAM/N`; chọn N tối ưu chi phí & cân đối cấu hình. | trang 24
- **R51** [đl] Mức dự phòng N+M: **M mặc định = 1** (tức N+1), tùy phân loại hệ thống. | trang 24
- **R52** [đl] Quy đổi máy ảo:
  `vCPU_thànhphần = ∑CPU_thànhphần / Cint_rated(1 vCPU)`;
  `Cint_rated(1 vCPU) = Cint_rated(1 CPU) / số core / số thread`;
  **số thread/1 core = 2** với CPU Intel (Hyper-Threading). | trang 24
- **R53** [đt] Ứng dụng dùng tài nguyên dedicare (DPDK core, Storm RAM) phải mô tả rõ
  để định cỡ; ứng dụng RAM nhiều (IMDB, Redis) phải mô tả swap/huge-page, %. | trang 25

## 5. Định cỡ thiết bị lưu trữ — thông số & công thức (trang 26–27)

- **R54** [đl] RAID: khi dùng ổ **NL-SAS / SATA 7.2k rpm** (rebuild lâu) khuyến cáo
  **RAID 6** đảm bảo an toàn. | trang 25
- **R55** [đl] IOPS tối đa tham khảo: NL-SAS/SATA 7.2k=**100**, SAS 10k=**140**,
  SAS/FC 15k=**210**, Flash/SSD **≥ 5000** (tùy chip SLC/MLC/eMLC/TLC). | trang 25
- **R56** [đl] `Dung lượng thô = Tổng cần thiết × tỷ lệ RAID × tỷ lệ format × tỷ lệ sai số × tỷ lệ dự phòng`. | trang 26
- **R57** [đl] Tỷ lệ cấu hình RAID = tổng số ổ / số ổ lưu dữ liệu (RAID 5 6 ổ = 6/5;
  RAID 6 8 ổ = 8/6); **tỷ lệ format = 1.1**; **tỷ lệ sai số = 1.1**; **tỷ lệ dự phòng = 1.25**
  (mục tiêu dùng ≤ 80% dung lượng). | trang 26
- **R58** [đl] Khối lượng dữ liệu cần thêm dung lượng để **phục hồi**: vd lưu online
  3 bản backup 1TB + khả năng restore 1 bản → cần 4TB. | trang 26
- **R59** [đt] Hệ thống yêu cầu hiệu năng đọc/ghi cao (VDI, DB OLTP dùng chung, ảo hóa số
  lượng máy chủ lớn, media, big data) **phải tính toán hiệu năng** từng phân vùng riêng
  (DB, backup, archive). | trang 26

## 5. Định cỡ lưu trữ — hiệu năng IOPS & số lượng ổ cứng (trang 28–31)

- **R60** [đl] `IOPS hệ thống = ∑ IOPS máy chủ`; IOPS máy chủ = ∑ IOPS phân vùng (giá trị
  **95th**); đo bằng iostat định kỳ 1 phút/lần, thống kê **tối thiểu 7 ngày**, lấy r/s và w/s. | trang 27
- **R61** [đl] `Frontend IOPS = IOPS hệ thống`;
  `Backend IOPS = Frontend IOPS × (1×%read + penalty×%write)`. | trang 27
- **R62** [đl] Write penalty theo RAID: **RAID 5 = 5**, **RAID 6 = 6** (RAID 0 = 1,
  RAID 1 = 1). | trang 27
- **R63** [đl] Tỷ lệ đọc/ghi đa phần ứng dụng Viettel: **65% read / 35% write** (fio
  rwmixread=65). | trang 28
- **R64** [đl] Số lượng ổ cứng = `MAX(ổ theo dung lượng, ổ theo hiệu năng) + hotspare`. | trang 30
- **R65** [đl] Số ổ theo dung lượng = dung lượng thô / dung lượng 01 ổ; số ổ theo hiệu
  năng = `Backend IOPS × tỷ lệ dự phòng (1.25) / IOPS loại ổ` (mục tiêu dùng ≤ 80% hiệu năng). | trang 30
- **R66** [đl] Dung lượng ổ thông dụng: Flash/SSD 100GB–1.92TB; SAS/FC 15k 300–600GB;
  SAS/FC 10k 300GB–2TB; SATA/NL-SAS 7.2k 1–8TB. | trang 30
- **R67** [đt] Hệ đọc/ghi ngẫu nhiên cao (VAS, OLTP, File server nhiều file nhỏ) nên
  dùng ổ tốc độ cao (10k/15k/SSD), dung lượng < 1TB. | trang 30
- **R68** [đl] SSD khi dùng đến **≥ 75%** dung lượng thì tốc độ ghi giảm đáng kể. | trang 30
- **R69** [đl] Ổ hotspare: tối thiểu **02 ổ mỗi loại**; nếu số ổ cùng loại lớn → hotspare =
  **7% tổng số ổ cùng loại, làm tròn lên**. | trang 31

## 6. Định cỡ thiết bị sao lưu (trang 32)

- **R70** [đl] `Tổng dung lượng sao lưu = dung lượng sao lưu toàn bộ + sao lưu gia tăng`
  (theo thời gian lưu trữ dữ liệu). | trang 31
- **R71** [đl] Số tape toàn bộ = `(dung lượng sao lưu toàn bộ / dung lượng 01 tape) × số bản sao lưu × hệ số dự phòng`. | trang 31

## 6. Định cỡ sao lưu — tape/driver (trang 33)

- **R72** [đl] Số tape gia tăng = `(dung lượng sao lưu gia tăng / dung lượng 1 tape) × số bản × hệ số dự phòng`. | trang 32
- **R73** [đl] `Tổng dung lượng xử lý/giây = tổng dung lượng cần sao lưu / yêu cầu thời gian (giây)`;
  `số driver = Max(dung lượng/giây / tốc độ 1 tape, 2)`;
  `số đường kết nối = Max(dung lượng/giây / tốc độ 1 đường, 2)`. | trang 32
- **R74** [đl] Một dữ liệu phải được sao lưu trên **tối thiểu 02 băng từ** khác nhau;
  hệ số dự phòng = **1.1**. | trang 32
- **R75** [đl] Capacity/tốc độ tape: LTO-3 400GB/80MBps, LTO-4 800/120, LTO-5 1500/140,
  LTO-6 2500/160, LTO-7 6TB/300, LTO-8 12TB/360, LTO-9 18TB/400MBps. | trang 32
- **R76** [đl] Cần lượng **cleaning tape** tương đương lượng đầu đọc (tape drive). | trang 32

## 7. Định cỡ SAN switch (trang 34)

- **R77** [đl] `Số port cần = ∑(port từng dịch vụ) × Kdựphòngport` với **Kdựphòngport = 1.2**. | trang 33
- **R78** [đl] `Port Active 01 thiết bị = số port cần / số thiết bị` (tối thiểu 02 thiết bị);
  port < 24 → switch 24 port; 24–48 → switch 48 port. | trang 33

## 8. Định cỡ LAN switch (trang 34–36)

- **R79** [đl] `Số port = (∑ port dịch vụ + port theo kiến trúc mạng) × 1.2`;
  < 24 → switch 24; 24–48 → switch 48 (hoặc stack 2×24). | trang 34
- **R80** [đl] `Lưu lượng port TB = ∑ lưu lượng dịch vụ / số port dịch vụ`; chọn bandwidth
  port gần bằng chuẩn 100M/1000M/10000M: <100→100 (ưu tiên 1000 nếu có thể mở rộng);
  100–1000→1000; 1000–10G→10G (nếu không ghép port). | trang 34–35
- **R81** [đl] `Thông lượng thiết bị = bandwidth port × số lượng port × 2`
  (throughput ≥ ∑ bandwidth các port). | trang 35
- **R82** [đl] Ghép port vật lý → port logic: **tối đa 04 port**. | trang 35

## 9. Định cỡ Firewall (trang 36–37)

- **R83** [đl] `Số port = (∑ port từng zone + port triển khai HA) × Kdựphòngport`. | trang 36
- **R84** [đl] `Lưu lượng dịch vụ = số kết nối đồng thời × lưu lượng mỗi kết nối`;
  `lưu lượng zone = ∑ lưu lượng các dịch vụ`; `thông lượng thiết bị = ∑(lưu lượng zone up + down) × Kdựphòngthônglượng`. | trang 36
- **R85** [đl] Throughput firewall đo theo kích cỡ gói **1518 Byte** (chuẩn) hoặc 512 Byte;
  bandwidth port chọn theo ngưỡng 100M/1000M/10G (nếu không ghép port). | trang 36

## 10. Định cỡ thiết bị cân bằng tải (trang 38–39)

- **R86** [đl] `Số port = ∑ port từng dịch vụ`;
  `CPS layer 4 = ∑ CPS × KdựphòngCPS(1.2)`; `TPS layer 7 = ∑ TPS × KdựphòngTPS`;
  `thông lượng = ∑ lưu lượng dịch vụ × 1.2` (Kdựphònglưulượng = 1.2). | trang 37–38
- **R87** [đl] `Lưu lượng dịch vụ = CPS×lưu lượng/1 CPS + TPS×lưu lượng/1 TPS`; chọn port
  < 1000 → 1000Mbps; 1000–10G → 10Gbps (nếu không ghép port). | trang 38

## 11. Định cỡ tủ Rack (trang 39–40)

- **R88** [đl] RU chuẩn: máy chủ **2U**; SAN switch **1U**; thiết bị lưu trữ `= số tray × 3U`;
  sao lưu **8U**; load balancer **1U**; firewall **1U**; switch **1U**. | trang 39
- **R89** [đl] `Số Rack = Tổng RU / 38` (lấy 38 do bỏ 2U trên + 2U dưới để đi dây/thao tác). | trang 39
- **R90** [đl] Kích thước Rack: cao 42U, rộng 600mm, sâu tối thiểu 1000mm; **02 bộ PDU**;
  nếu tổng công suất danh định vượt mức cho phép của rack → phân chia lại số rack. | trang 39

## B. Cấp phát, thu hồi hạ tầng CNTT (trang 41–42)

- **R91** [đt] Toàn bộ hệ thống CNTT nội bộ Tập đoàn phải triển khai trên **Cloud của Tập
  đoàn**, trừ các hệ thống phân tán tại vị trí không có hạ tầng Cloud / yêu cầu đặc thù
  (cô lập hạ tầng, thiết bị đặc chủng). | trang 40
- **R92** [đt] Cấp phát chỉ với hệ thống có **tờ trình đầu tư tài nguyên, quy hoạch định cỡ,
  kiểm thử hiệu năng, tài liệu định cỡ** đáp ứng quy định; hệ định cỡ khi chưa có sản
  phẩm phải định cỡ lại theo phương pháp có sản phẩm khi cấp phát. | trang 40
- **R93** [đl] Cấp phát đảm bảo hoạt động hệ thống trong **06 tháng**, áp hạn ngạch (quota)
  và theo dõi điều chỉnh theo KPI. | trang 40
- **R94** [đl] Cấp phát tài nguyên ảo hóa phải đảm bảo overcommit: **CPU ≤ 4**, **RAM ≤ 1.5**. | trang 41
- **R95** [đt] Hệ Big data → cấp phát **Bare-Metal** trên Cloud (không ảo hóa); hệ còn lại → ảo hóa. | trang 41
- **R96** [đl] Thu hồi: VTNet rà soát, đánh giá hiệu suất **tối thiểu 06 tháng/lần**; máy
  chủ có tải **CPU ≤ 15% hoặc RAM ≤ 30%** trong thời gian đánh giá → xem xét thu hồi. | trang 41

## B. Thu hồi — bổ sung (trang 43)

- **R97** [đt] Thu hồi: ưu tiên **giảm số máy chủ** trước khi giảm cấu hình từng máy (máy chủ
  ứng dụng chạy ảo hóa); với hệ cluster (DB) giữ số máy tối thiểu theo mô hình cụm. | trang 42

## C. Kiểm thử hiệu năng hệ thống CNTT (trang 44–45)

- **R98** [đt] Với ứng dụng/nền tảng (DB), định cỡ dùng công cụ chuẩn để ra số CCU/TPS/RPS:
  sysbench (test OLTP) cho DB nguồn mở; jmeter/ab (benchmark end-2-end) cho ứng dụng. | trang 43–44
- **R99** [đt] Đơn vị PTPM phải **thống nhất một công cụ + cách thức đo** với đơn vị quy hoạch
  định cỡ/triển khai; mọi công thức, công cụ, bài kiểm thử định cỡ phải được **lưu vết,
  ký xác nhận** làm sở cứ. | trang 44

## A.2 — Cơ sở định cỡ (trang 11–12)

- **R24** [đt] Định cỡ dựa trên KPI giả định tương lai (CCU, số giao dịch, hành vi người
  dùng) + đặc tả phần mềm + đặc tính thiết bị → kết quả không chính xác 100%. | trang 10
- **R25** [đt] Cần xác định yếu tố ảnh hưởng khi mở rộng/thu hẹp (tăng CCU → thêm tài
  nguyên/LB; 100→200 TPS mở rộng module nào, dọc hay ngang). | trang 10
- **R26** [đt] Dạng I (chưa có phần mềm): định cỡ theo hệ thống tham chiếu **tương đồng**
  (cùng kiến trúc, công nghệ, chức năng, luồng nghiệp vụ, đối tượng dùng); phải nêu
  đặc điểm tương đồng. Không cấp phát hạ tầng Tập đoàn cho hệ định cỡ kiểu này nếu
  chưa kiểm thử hiệu năng & định cỡ chính xác. | trang 11
- **R27** [đt] Dạng I + không có hệ thống tham chiếu tương đồng → phải hoàn thiện sản
  phẩm + kiểm thử hiệu năng để định cỡ. | trang 11
- **R28** [đt] Dạng II (đã có phần mềm): định cỡ bằng môi trường kiểm thử, đo nhu cầu
  tài nguyên theo các mẫu đầu vào, suy bình quân tài nguyên/người dùng (hoặc giao
  dịch). Không áp dụng phương pháp Dạng I cho sản phẩm đã có phần mềm. | trang 11

---

## BỔ SUNG — quy tắc phát hiện sót khi làm mục 0.4 (2026-08-25)

> Phát hiện khi rà lại trang 9 để lấy trích dẫn nguyên văn cho R10. Hai câu dưới đây
> nằm ngay cạnh R10–R12 nhưng **chưa được đưa vào danh sách R01–R100**.
> Nguồn: `docs/rules/.tmp-lan7/clean.txt` dòng 356–360.
>
> **Trạng thái 2026-08-26 — cả 10 quy tắc R101–R110 đã được phát triển xong:**
> 2 quy tắc định lượng (**R101**, **R105**) → công thức ở
> [`rules-formulas.md`](rules-formulas.md) mục "BỔ SUNG";
> 8 quy tắc định tính (**R102–R104**, **R106–R110**) → tiêu chí ở
> [`rules-criteria.md`](rules-criteria.md) mục **5.7**.

- **R101** [đl] **Cơ chế dự phòng bắt buộc theo mức độ quan trọng:** `active-active`
  với hệ **Rất quan trọng trở lên**; `active-standby` với hệ **Quan trọng**. | trang 9
  > *Nguyên văn:* "Các thiết bị phần cứng phải đảm bảo hoạt động với cơ chế dự phòng
  > active-active (đối với các hệ thống Rất quan trọng trở lên) hoặc active-standby
  > (đối với các hệ thống Quan trọng)."
- **R102** [đt] Mức độ dự phòng của từng hệ thống/thiết bị **căn cứ vào phân loại hệ
  thống** trong các quy định về dự phòng hiện hành của Tập đoàn (tức 849/QĐ-CNVTQĐ). | trang 9
  > *Nguyên văn:* "Mức độ dự phòng của từng hệ thống, thiết bị căn cứ vào phân loại
  > hệ thống trong các quy định về dự phòng của Tập đoàn hiện hành."

**Vì sao đáng chú ý:** R101 trả lời đúng điểm `[CẦN XÁC NHẬN]` đang treo ở
`QD849-02` — mức độ quan trọng **có** ép chọn cơ chế dự phòng nội site, và ràng buộc
đó nằm ngay trong Guideline chứ không phải chỉ ở 849/QĐ.

### Rà độ phủ toàn tài liệu (mục 0.2, 2026-08-25)

Sau khi phát hiện R101/R102, đã rà lại cả 44 trang bằng
`scripts/audit_rule_coverage.py` — công cụ đếm câu mang dấu hiệu quy phạm mỗi trang
rồi so với số quy tắc đã bắt. Kết quả: **115 câu quy phạm / 108 lượt quy tắc**,
gắn cờ **3 trang** (18, 20, 40). Đọc lại cả ba, phát hiện thêm **7 quy tắc sót**:

**Trang 17 — bảng thông số đầu vào (phần đầu)**

- **R110** [đt] Bảng thông số đầu vào phải nêu **tổng số thuê bao/người dùng sử dụng
  dịch vụ** và **tổng số giao dịch đồng thời tại thời điểm Peak** (TPS/TPM); với hệ
  nhiều loại nghiệp vụ phải **làm rõ từng loại tải và tỉ lệ % của mỗi loại trên tổng
  số giao dịch**, tỉ lệ giả định sát thực tế. | trang 17
  > Cụ thể hơn R42 (R42 nói *định cỡ theo tổng tải peak*); R110 nói phải **trình bày
  > phân tách** theo nghiệp vụ kèm tỉ lệ.

**Trang 18 — bảng thông số đầu vào (phần sau)**

- **R103** [đt] Tài liệu phải nêu **tính sẵn sàng của hệ thống** (phút/tháng — thời
  gian cho phép downtime/tháng) và **thời gian downtime cho phép đối với mỗi sự cố**
  (phút). | trang 18
- **R104** [đt] Phải nêu **các yếu tố ảnh hưởng thông số tài nguyên máy chủ**: số
  thuê bao đăng ký / active / đồng thời, số thiết bị kết nối đồng thời, số tiến
  trình đồng thời, số request đồng thời, số giao dịch một người dùng, độ phức tạp
  giao dịch, kích thước bản tin trao đổi và lưu trữ, yêu cầu lưu trữ của ứng dụng,
  mục đích sử dụng máy chủ. | trang 18

**Trang 20 — yêu cầu về cách trình bày kết quả định cỡ**

- **R105** [đl] Định cỡ phải làm ở **cả hai mức**: toàn bộ hệ thống **và** chi tiết
  đến từng module. Bảng tổng hợp toàn hệ thống là **tổng hợp kết quả tính toán của
  từng module**, gồm cả thành phần dùng chung (mạng, Firewall, LB). | trang 20
  > Đây là **kiểm nhất quán tính được**: tổng toàn hệ = tổng các module. Trùng với
  > quy tắc mới đã đề xuất ở `rules-checklist-flat.md` (`CL-2.9` ↔ `CL-3.x.20`) —
  > nay có nguồn văn bản, không còn là đề xuất.
- **R106** [đt] Module sau khi định cỡ đáp ứng về giao dịch, **cần thiết kế định cỡ
  để đảm bảo tính sẵn sàng, dự phòng và các yêu cầu trong chỉ tiêu kỹ thuật**. | trang 20
- **R107** [đt] Phải **có giải pháp sao lưu phục hồi đi kèm**; máy chủ tính toán năng
  lực **cần bổ sung năng lực đáp ứng cho tác vụ sao lưu dữ liệu**. | trang 20
  > Khác R39 (R39 nói *thời gian* hoàn thành backup); R107 nói phải **cộng thêm tài
  > nguyên** cho tác vụ sao lưu vào cấu hình máy chủ.

**Trang 40 — cấp phát**

- **R108** [đt] Cấp phát tài nguyên LB, lưu trữ **tránh lưu lượng chạy vòng qua nhiều
  lớp mạng**; quy hoạch các node ảo hóa quan trọng (ví dụ các cặp DB) **đảm bảo an
  toàn khi gặp sự cố phần cứng thiết bị**. | trang 40
- **R109** [đt] Đơn vị chủ quản hệ thống và **TCT VTNet thống nhất phương án cấp
  phát** trong quá trình xây dựng sizing và triển khai hệ thống. | trang 40

---

### Ghi chú về số trang — ĐÃ THỐNG NHẤT (2026-08-26)

~~Hai hệ đánh số trang cùng tồn tại trong file này.~~ **Đã xử lý ở mục 0.5.**

Trước đây R01–R100 dùng **số trang vật lý của bản lần 06** (có thêm 01 trang chữ ký
ở đầu nên = số trang in + 1), còn R101–R110 dùng **số trang in**. Nay **toàn bộ
R01–R110 đều dùng SỐ TRANG IN** của bản lần 07 (trang vật lý = trang in).

- Chuyển đổi: `scripts/unify_page_numbers.py` (trừ 1 cho R01–R100, giữ nguyên R101+).
  Script chỉ được chạy **một lần**; chạy lại sẽ trừ tiếp và làm sai.
- Kiểm chứng offset −1: 12 phép dò độc lập trải từ trang 8 tới trang 45 — ví dụ R09
  ghi "trang 10" nhưng câu *"dự phòng 20% số port"* nằm ở trang in 9; R98 ghi
  "trang 44" nhưng `sysbench` nằm ở trang in 43.
- Kiểm chéo ba file (`rules-flat-draft.md`, `rules-formulas.md`,
  `rules-classification.md`): `scripts/check_page_consistency.py` — **0 lệch**,
  mọi số trang nằm trong 1..44.
- `scripts/audit_rule_coverage.py` đã bỏ hằng số bù trừ (`DRAFT_PAGE_OFFSET = 0`).

---
*(Ghi chú cũ "đang đọc tiếp các trang 13+" đã lỗi thời — toàn bộ 44 trang đã được đọc.)*
