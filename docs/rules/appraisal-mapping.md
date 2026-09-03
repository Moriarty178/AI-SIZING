# Ánh xạ vấn đề thẩm định thật → quy tắc

> Sinh bằng `scripts/map_appraisal_to_rules.py`. **Không sửa tay** — sửa bảng
> `THEMES` trong script rồi chạy lại.

> ⚠️ **Nguồn là tóm tắt do một AI khác (Cline) viết lại từ hồ sơ đã ký, KHÔNG
> phải nguyên văn Phiếu Nhận Xét.** Bản gốc `.docx`/`.pdf` không còn (xác nhận
> 2026-08-26). Dùng để **soi lại bộ quy tắc**; KHÔNG dùng làm nhãn chấm điểm —
> làm vậy sẽ cho recall ảo và vi phạm NT2.

## Cách đọc

Ánh xạ đi qua hai lớp: vấn đề → **chủ đề** (máy gán bằng từ khóa) → **quy tắc**
(người gán). Nhờ vậy phần cần duyệt chỉ là ~30 dòng bảng chủ đề dưới đây, thay
vì 667 dòng vấn đề.

`độ tin cậy`: **cao** = chủ đề và quy tắc nói đúng một việc · **vừa** = có phủ
nhưng lệch phạm vi · **thấp** = từ khóa khớp rộng, dễ dính nhầm.

**Chỉ đếm khớp ở TIÊU ĐỀ.** Bản đầu dò từ khóa trên cả đoạn ngữ cảnh và sinh
khớp nhầm rõ rệt — kiểm tay 5 ca ngẫu nhiên thấy *"PNM system sizing best
practices"* dính chủ đề RAM, *"Table format"* dính chủ đề dự phòng N+1. Nay
khớp-ở-ngữ-cảnh (810 lượt) vẫn dò nhưng **không** tính vào
số liệu, để con số ở đây không bị thổi phồng.

## Bảng chủ đề → quy tắc

| Chủ đề | Số lần | Hồ sơ | Quy tắc phủ | Độ tin cậy |
|---|---:|---:|---|:--:|
| Sở cứ / minh chứng cho số liệu | 50 | 24 | `EVD-09` `EVD-03` `PRC-01` `PRC-02` | cao |
| Dung lượng lưu trữ | 46 | 24 | `STO-04` `STO-05` `KPI-06` `EVD-01` | vừa |
| LB / Firewall / băng thông | 44 | 21 | `LBA-01` `LBA-02` `FWL-01` `FWL-02` `FWL-03` `FWL-04` `ARC-01` | cao |
| Tải đầu vào CCU / TPS / peak | 35 | 17 | `EVD-05` `EVD-11` `KPI-01` `KPI-10` | cao |
| KHOẢNG TRỐNG · Nhất quán chu kỳ lưu trữ giữa các phân vùng | 31 | 13 | **— không có —** | cao |
| Chọn loại ổ / SSD | 29 | 17 | `STO-02` `STO-03` `STO-13` `STO-14` `STO-15` `KPI-07` | cao |
| Số node / cấu hình cụm | 25 | 10 | `ARC-08` `ARC-09` `ARC-19` `ARC-20` `ARC-21` `ARC-22` `ARC-23` `ARC-24` `ARC-25` | vừa |
| RAM | 25 | 15 | `RAM-01` `RAM-02` `KPI-03` | thấp |
| Dự phòng N+1 / HA | 20 | 14 | `ARC-02` `ARC-03` `ARC-09` `ARC-12` `ARC-27` | cao |
| Phương pháp định cỡ / hệ tham chiếu | 20 | 14 | `MTH-01` `MTH-02` `MTH-03` `MTH-04` `KPI-12` | cao |
| Nhất quán số liệu giữa các bảng | 19 | 9 | `EVD-10` `ARC-09` `ARC-22` | vừa |
| Ngưỡng KPI 75/90/80 | 17 | 9 | `KPI-02` `KPI-03` `KPI-04` `KPI-14` | cao |
| Kết nối / port | 17 | 12 | `ARC-16` `FWL-04` | vừa |
| Mô hình logic / vật lý | 14 | 12 | `EVD-13` `EVD-14` `EVD-19` `EVD-20` | cao |
| KHOẢNG TRỐNG · Kiểm tính hợp lý đơn vị số liệu đầu vào | 14 | 9 | **— không có —** | cao |
| Mục đích / phạm vi sizing | 13 | 10 | `MTH-01` `PRC-09` | vừa |
| DC-DR cho hệ đặc biệt quan trọng | 12 | 7 | `ARC-26` | cao |
| IOPS / latency | 12 | 8 | `KPI-05` `STO-01` `STO-08` `STO-12` `EVD-07` | cao |
| Sao lưu / backup | 11 | 7 | `BAK-01` `BAK-02` `BAK-09` `STO-06` `STO-18` | cao |
| KHOẢNG TRỐNG · Định cỡ GPU / tải AI | 11 | 4 | **— không có —** | cao |
| KHOẢNG TRỐNG · Sở cứ cho tốc độ tăng trưởng dữ liệu | 10 | 6 | **— không có —** | cao |
| CPU / SPEC / Cint | 8 | 7 | `CPU-01` `CPU-02` `CPU-05` `CPU-06` `CPU-09` `CPU-10` | cao |
| KHOẢNG TRỐNG · Làm tròn và độ chính xác số trung gian | 8 | 4 | **— không có —** | cao |
| KHOẢNG TRỐNG · Phải trình bày công thức, không chỉ kết quả | 6 | 5 | **— không có —** | vừa |
| KHOẢNG TRỐNG · Sizing phần mềm bên thứ ba / vendor | 5 | 2 | **— không có —** | vừa |
| Thủ tục / phê duyệt | 4 | 2 | `PRC-01` `PRC-02` `PRC-03` `PRC-05` | vừa |
| KHOẢNG TRỐNG · Cấp bổ sung phải tính phần TĂNG THÊM | 3 | 2 | **— không có —** | vừa |
| KHOẢNG TRỐNG · Sizing ứng cứu khẩn cấp | 3 | 1 | **— không có —** | vừa |

### Ghi chú từng chủ đề khoảng trống

**KHOẢNG TRỐNG · Sở cứ cho tốc độ tăng trưởng dữ liệu** — 10 lần, 6 hồ sơ  
PNX hỏi thẳng "sở cứ cho mức tăng trưởng 20%/năm là gì?", đòi log history hoặc trend analysis. Guideline không có quy tắc nào về tốc độ tăng trưởng. KPI-16 (tăng trưởng 01 năm) đang `enabled: false`.

**KHOẢNG TRỐNG · Nhất quán chu kỳ lưu trữ giữa các phân vùng** — 31 lần, 13 hồ sơ  
Ca thật: App 6 tháng · /data 2 năm · /log 6 tháng · /backup 4 ngày, không giải thích vì sao khác nhau. Không quy tắc nào bắt được sự không nhất quán này. ALC-01 chỉ kiểm mốc 06 tháng của cấp phát.

**KHOẢNG TRỐNG · Kiểm tính hợp lý đơn vị số liệu đầu vào** — 14 lần, 9 hồ sơ  
Ca thật: khai "3.000.000 TB cho 1.080 người dùng" = 2,7 PB mỗi người. Đây là phép kiểm rẻ và bắt được lỗi nặng, thuần code làm được, nhưng không quy tắc nào có.

**KHOẢNG TRỐNG · Cấp bổ sung phải tính phần TĂNG THÊM** — 3 lần, 2 hồ sơ  
PNX bắt lỗi khai TỔNG tài nguyên trong khi hồ sơ là cấp BỔ SUNG — phải khai phần tăng thêm. CL-2.1 chỉ hỏi "mới hay bổ sung", không ràng buộc cách khai con số.

**KHOẢNG TRỐNG · Phải trình bày công thức, không chỉ kết quả** — 6 lần, 5 hồ sơ  
PNX đòi bảng tính trung gian để lần được từ đầu vào tới kết quả. EVD-09 chỉ yêu cầu mọi con số truy được nguồn, không yêu cầu hiện phép tính.

**KHOẢNG TRỐNG · Làm tròn và độ chính xác số trung gian** — 8 lần, 4 hồ sơ  
PNX xếp lỗi làm tròn số trung gian là CRITICAL. `globals.lam_tron` mới là quy ước làm tròn kết quả cuối, chưa thành quy tắc kiểm.

**KHOẢNG TRỐNG · Sizing phần mềm bên thứ ba / vendor** — 5 lần, 2 hồ sơ  
PNX chấp nhận email hãng xác nhận làm sở cứ khi phần mềm do vendor cung cấp. Guideline không nói gì về trường hợp này.

**KHOẢNG TRỐNG · Sizing ứng cứu khẩn cấp** — 3 lần, 1 hồ sơ  
Có luồng riêng (VTNet UCTT) với hệ số dự phòng khác. Bốn dạng định cỡ MTH-01..04 không có dạng này.

**KHOẢNG TRỐNG · Định cỡ GPU / tải AI** — 11 lần, 4 hồ sơ  
Đã biết trước: Guideline lần 07 không có nội dung GPU nào (PLAN.md mục 0.12f). Nay có bằng chứng là thực tế CÓ phát sinh.

### ⚠️ Chủ đề độ tin cậy THẤP — cần người duyệt xem lại

- **RAM** (25 lần) — từ khóa khớp rộng, số liệu này có thể bị thổi phồng.

### Chưa phân loại — 63 vấn đề

Không khớp chủ đề nào. Có thể là nhãn mục (không phải vấn đề), hoặc là
khoảng trống chưa nhận ra. Cần đọc tay.

| Hồ sơ | Vấn đề |
|---|---|
| cap moi APIGee Mini App 64015 | CHECKLIST SIZING BẮT BUỘC KÝ |
| cap moi BCCS3_thị_trường_Lào 34221 | Thị trường mới Sản xuất hiện tại |
| cap moi c360 58872 | Hệ thống C360 data warehouse |
| cap moi C360_Public 9367 | Public Internet access |
| cap moi callbot inbound CSKH_bosun | Bảng đề xuất cấu hình |
| cap moi callbot inbound CSKH_bosun | Số liệu hệ thống hiện tại |
| cap moi callbot inbound CSKH_bosun | Số liệu tính toán |
| cap moi CAMPAIGN_PUSH_MXH 36759 | Business forecast |
| cap moi CloudCA_2025_TACHCUM_THAYD | Cú pháp bảng tổng hợp |
| cap moi CloudCA_2025_TACHCUM_THAYD | LB sizing phải rõ ràng về layer và traffic |
| cap moi CloudCA_2025_TACHCUM_THAYD | Avoid cú pháp không cần thiết |
| cap moi DSQT_MariaDB 10208 | Have data patterns changed |
| cap moi DSQT_MariaDB 10208 | Old data (2020) may not be valid |
| cap moi FMRA_Sizing_server_Backup_ | Checklist |
| cap moi FMRA_Sizing_server_Backup_ | Virtualization consideration |
| cap moi FMRA_Sizing_server_Backup_ | Đơn vị tên |
| cap moi FMRA_Sizing_server_Backup_ | Training data characteristics |
| cap moi FMRA_Sizing_server_Backup_ | OS allocation - 600GB |
| cap moi FMRA_Sizing_server_Backup_ | Checklist is not optional |
| cap moi GSCG CSKH_bosung2022 23096 | Nhận xét chung |
| cap moi GSCG CSKH_bosung2022 23096 | Baseline sizing |
| cap moi GSCG CSKH_bosung2022 23096 | Bảng tổng hợp |
| hethong Vtag | Why divide by 3 |
| cap moi MNP 32034 | FW/LB sizing |
| cap moi MNP 32034 | APP server baseline |
| cap moi MNP 32034 | Detailed transaction analysis (trang 57) |
| cap moi MNP 32034 | XML message size (trang 59) |
| cap moi MNP 32034 | Transaction structure (trang 60) |
| cap moi MNP 32034 | XML file size needs actual proof |
| cap moi Mybox 38327 | ELK Stack sizing |
| cap moi Mykid 2.0 30959 | Request/giây calculation |
| cap moi MySign 10371 | Missing App sizing |
| cap moi MySign 10371 | N value table |
| cap moi PBH 21050 | Test system sizing |
| cap moi PBH 21050 | CPU core mismatch |
| cap moi PBH 21050 | Database |
| cap moi PBH 21050 | 110 tables/database - Sampling strategy |
| cap moi PBH 21050 | Test scaling may not be linear for large jumps |
| cap moi PBH 4.0 20043 | CPU values |
| cap moi Smarthome 13709 | 500K devices target |
| cap moi Smarthome 13709 | FW/LB sizing |
| cap moi Smarthome 13709 | 5x scale is aggressive |
| cap moi Stringee 62570 | Checklist |
| cap moi TMaketing 60476 | Checklist |
| cap moi Vcall 49637 | Reference |
| cap moi VDA 12720 | Sởffff chỉ |
| cap moi VDA 12720 | Mức độ quan trọng |
| cap moi Viettel API Gateway 65091 | Business flow |
| cap moi Viettel API Gateway 65091 | Reference |
| cap moi Viettel App_v1.0 53803 | Network card |
| cap moi Viettel App_v1.0 53803 | LB calculation |
| cap moi Viettel App_v1.0 53803 | Precise numbers, not ranges |
| cap moi Viettel Report_2026 62005 | Input data |
| cap moi Viettel Report_2026 62005 | Reference |
| cap moi Viettel Report_2026 62005 | Business forecast validation |
| cap moi VT CAMERA AI 23478 | 300 Camera devices |
| cap moi VT CAMERA AI 23478 | Network topology |
| cap moi VT CAMERA AI 23478 | Zone Internet considerations |
| cap_bo_sun_VTracking_2_0_114716 | CẤU HÌNH KHÔNG VƯỢT QUÁ MAX VM |
| CAPMOI_DB_MySign_8059 | DB type unclear |
| CAPMOI_DB_MySign_8059 | Missing App sizing |
| CAPMOI_DB_MySign_8059 | Network equipment |
| CAPMOI_DB_MySign_8059 | Size ALL components |

