# Vấn đề người thẩm định đã bắt — trích từ `approved-sizing/`

> Sinh bằng `scripts/extract_appraisal_issues.py`. **Không sửa tay file này** —
> chạy lại script. Bản ánh xạ sang mã quy tắc nằm ở `appraisal-mapping.md`.

> ⚠️ **Nguồn là tóm tắt do AI khác viết lại, không phải nguyên văn PNX.**
> Bản gốc (.docx/.pdf) không còn. Dùng để hiểu xu hướng, KHÔNG dùng làm nhãn
> vàng chấm điểm (vi phạm NT2, recall tính ra sẽ ảo).

**50 hồ sơ · 667 vấn đề.** Trường hợp A 38 · B 8 · không rõ 4.
Số vòng phản hồi trung bình **1.92** trên 38 hồ sơ ghi rõ.


7 hồ sơ không trích được vấn đề nào: `cap moi Backup tập trung cho VTT 29293`, `cap moi SmartHome 27860`, `cap moi tindy_khanhdn1`, `cap moi unify_anhdt156`, `cap moi vtracking`, `Nang_cap_he_thong_Roaming_1_0`, `Nang_cap_smartmoto_nang_ram`.


---

## cap moi CMP 40562

**PYC:** PYC-35119 · **Thẩm định:** thongnv31 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Kết nối hệ thống | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Mục đích sizing | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Input sizing đáng ngờ | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Cấu hình server hiện tại | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Tải hiện tại | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Consistency issue - Module CMS | LƯU Ý THẨM ĐỊNH PNX |
| 7 | New methodology proposal | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Áp dụng cho tất cả modules | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Master module | LƯU Ý THẨM ĐỊNH PNX |
| 10 | LB input data | LƯU Ý THẨM ĐỊNH PNX |
| 11 | LB calculation method | LƯU Ý THẨM ĐỊNH PNX |
| 12 | Làm tròn giá trị | LƯU Ý THẨM ĐỊNH PNX |
| 13 | Mô hình chạy | LƯU Ý THẨM ĐỊNH PNX |
| 14 | Review lại N+1 backup | LƯU Ý THẨM ĐỊNH PNX |
| 15 | Unit sanity check - QUAN TRỌNG | TRI THỨC RÚT RA |
| 16 | Methodology: System-wide scaling vs Per-module sizing | TRI THỨC RÚT RA |
| 17 | Load Balancer sizing - Different methodology | TRI THỨC RÚT RA |
| 18 | N+1 backup for different technologies | TRI THỨC RÚT RA |
| 19 | Greenfield vs Brownfield deployment | TRI THỨC RÚT RA |
| 20 | Module count consistency | TRI THỨC RÚT RA |
| 21 | LUÔN sanity check input data | BÀI HỌC KINH NGHIỆM |
| 22 | Methodology quan trọng hơn calculation | BÀI HỌC KINH NGHIỆM |
| 23 | LB sizing khác server sizing | BÀI HỌC KINH NGHIỆM |
| 24 | N+1 varies by technology | BÀI HỌC KINH NGHIỆM |
| 25 | Clarify deployment scenario | BÀI HỌC KINH NGHIỆM |
| 26 | Module count consistency | BÀI HỌC KINH NGHIỆM |
| 27 | HÌNH ẢNH很重要 | BÀI HỌC KINH NGHIỆM |

## cap moi FMRA_Sizing_server_Backup_2024 58352

**PYC:** PYC-58352 · **Thẩm định:** khanhnd23 (Phòng Công nghệ Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Đánh giá mức độ quan trọng | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Cam kết thời gian | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Checklist | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Thông tin đầu vào | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Cấu hình và tải hiện tại | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Storage technology | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Virtualization consideration | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Mô hình nghiệp vụ | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Kết nối hệ thống | LƯU Ý THẨM ĐỊNH PNX |
| 10 | Network bandwidth | LƯU Ý THẨM ĐỊNH PNX |
| 11 | Đơn vị tên | LƯU Ý THẨM ĐỊNH PNX |
| 12 | ĐBQT (Decision Support) Systems - DR is MANDATORY | TRI THỨC RÚT RA |
| 13 | Timeline commitment from KD/BGĐ | TRI THỨC RÚT RA |
| 14 | Large data volumes - 102TB và 738TB | TRI THỨC RÚT RA |
| 15 | Training data characteristics | TRI THỨC RÚT RA |
| 16 | SSD justification for backup servers | TRI THỨC RÚT RA |
| 17 | OS allocation - 600GB | TRI THỨC RÚT RA |
| 18 | Network bandwidth - 2.5 Gbps per server | TRI THỨC RÚT RA |
| 19 | Checklist attachment - Mandatory | TRI THỨC RÚT RA |
| 20 | ĐBQT DR is MANDATORY | BÀI HỌC KINH NGHIỆM |
| 21 | Timeline needs business approval | BÀI HỌC KINH NGHIỆM |
| 22 | Large volumes need breakdown explanation | BÀI HỌC KINH NGHIỆM |
| 23 | Training data has IOPS requirements | BÀI HỌC KINH NGHIỆM |
| 24 | Network bandwidth must align with RTO | BÀI HỌC KINH NGHIỆM |
| 25 | OS allocation needs justification | BÀI HỌC KINH NGHIỆM |
| 26 | Checklist is not optional | BÀI HỌC KINH NGHIỆM |
| 27 | Show IP addresses in ALL screenshots | BÀI HỌC KINH NGHIỆM |

## cap moi GSCG CSKH_bosung2022 23096

**PYC:** PYC-23096 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Nhận xét chung | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Mục đích sizing | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Input data | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Network architecture | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Cấp phát tài nguyên | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Baseline sizing | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Speech processing module | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Baseline server - 300k calls/day | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Firewall và Load Balancer | LƯU Ý THẨM ĐỊNH PNX |
| 10 | Table formatting | LƯU Ý THẨM ĐỊNH PNX |
| 11 | Bảng tổng hợp | LƯU Ý THẨM ĐỊNH PNX |
| 12 | Additional capacity sizing - ALWAYS reference baseline | TRI THỨC RÚT RA |
| 13 | Load Balancer IP range consideration | TRI THỨC RÚT RA |
| 14 | Speech processing sizing challenge | TRI THỨC RÚT RA |
| 15 | HBA card - When needed | TRI THỨC RÚT RA |
| 16 | Cluster-specific sizing tables | TRI THỨC RÚT RA |
| 17 | Firewall/LB sizing for VoIP traffic | TRI THỨC RÚT RA |
| 18 | QHĐC (Quy hoạch đầu tư) - Investment planning | TRI THỨC RÚT RA |
| 19 | Additional sizing ALWAYS needs baseline | BÀI HỌC KINH NGHIỆM |
| 20 | Load balancer IP range affects architecture | BÀI HỌC KINH NGHIỆM |
| 21 | Speech processing needs special handling | BÀI HỌC KINH NGHIỆM |
| 22 | HBA card indicates SAN storage | BÀI HỌC KINH NGHIỆM |
| 23 | Cluster-specific tables are mandatory | BÀI HỌC KINH NGHIỆM |
| 24 | VoIP has unique bandwidth characteristics | BÀI HỌC KINH NGHIỆM |
| 25 | QHĐC compliance is mandatory | BÀI HỌC KINH NGHIỆM |
| 26 | Firewall/LB sizing for VoIP | BÀI HỌC KINH NGHIỆM |

## cap moi callbot inbound CSKH_bosung videobot XMKH 35485

**PYC:** PYC-29293 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 3

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Bổ sung sở cứ | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Mục đích sizing | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Thông tin đầu vào (Trang 1) | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Trang 4 - Server test và tính toán CCU | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Trang 5 - Cấu hình test và GPU | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Trang 6 - Dung lượng lưu trữ | LƯU Ý THẨM ĐỊNH PNX |
| 7 | SSD Storage | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Kết nối các hệ thống | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Cấp phát tài nguyên mạng | LƯU Ý THẨM ĐỊNH PNX |
| 10 | Firewall và Load Balancer | LƯU Ý THẨM ĐỊNH PNX |
| 11 | Bảng đề xuất cấu hình | LƯU Ý THẨM ĐỊNH PNX |
| 12 | Định cỡ hệ thống AI/ML với GPU | TRI THỨC RÚT RA |
| 13 | Tính toán dung lượng storage cho Video/Audio | TRI THỨC RÚT RA |
| 14 | Bảng giá trị định cỡ (Table-based sizing) | TRI THỨC RÚT RA |
| 15 | SoỞ cứ cho mọi con số | TRI THỨC RÚT RA |
| 16 | Số liệu test | TRI THỨC RÚT RA |
| 17 | Số liệu hệ thống hiện tại | TRI THỨC RÚT RA |
| 18 | Số liệu benchmark từ vendor | TRI THỨC RÚT RA |
| 19 | Số liệu tính toán | TRI THỨC RÚT RA |
| 20 | SSD vs HDD cho AI workloads | TRI THỨC RÚT RA |
| 21 | NEVER ước tính mà không có test benchmark | BÀI HỌC KINH NGHIỆM |
| 22 | Mọi số liệu đều phải có sở cứ | BÀI HỌC KINH NGHIỆM |
| 23 | Bảng tính toán giúp giải thích rõ hơn | BÀI HỌC KINH NGHIỆM |
| 24 | Storage tính toán khác ước tính | BÀI HỌC KINH NGHIỆM |
| 25 | GPU sizing | BÀI HỌC KINH NGHIỆM |

## cap moi CAMPAIGN_PUSH_MXH 36759

**PYC:** PYC-36759 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Bổ sung sở cứ | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Mục đích sizing | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Tốc độ tăng trưởng dữ liệu | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Chuyển đổi đơn vị CPU | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Cấu hình server test | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Request rate (Trang 4) | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Dữ liệu và log retention | LƯU Ý THẨM ĐỊNH PNX |
| 8 | High RAM requirement | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Mô hình hệ thống | LƯU Ý THẨM ĐỊNH PNX |
| 10 | Network và connections | LƯU Ý THẨM ĐỊNH PNX |
| 11 | Mâu thuẫn trong sizing calculation | TRI THỨC RÚT RA |
| 12 | High RAM - Virtualization strategy | TRI THỨC RÚT RA |
| 13 | Data compression for retention | TRI THỨC RÚT RA |
| 14 | Growth rate justification | TRI THỨC RÚT RA |
| 15 | Historical data analysis | TRI THỨC RÚT RA |
| 16 | Business forecast | TRI THỨC RÚT RA |
| 17 | Industry benchmark | TRI THỨC RÚT RA |
| 18 | Conservative vs Aggressive | TRI THỨC RÚT RA |
| 19 | Request-based sizing | TRI THỨC RÚT RA |
| 20 | LUÔN giải thích gap giữa input và calculation | BÀI HỌC KINH NGHIỆM |
| 21 | High RAM cân nhắc virtualization | BÀI HỌC KINH NGHIỆM |
| 22 | Growth rate phải có historical data | BÀI HỌC KINH NGHIỆM |
| 23 | Compression strategy cho long retention | BÀI HỌC KINH NGHIỆM |
| 24 | Request rate convert to per-second | BÀI HỌC KINH NGHIỆM |
| 25 | Mô hình kiến trúc rất quan trọng | BÀI HỌC KINH NGHIỆM |

## cap moi DSQT_MariaDB 10208

**PYC:** PYC-10208 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Nhận xét chung | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Network và kết nối | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Mục I - Cơ bản | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Mục III - Định cỡ Database | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Storage calculation | LƯU Ý THẨM ĐỊNH PNX |
| 6 | SSD vs HDD | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Backup separation | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Oracle MariaDB migration | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Oracle vs MariaDB - NOT equivalent | TRI THỨC RÚT RA |
| 10 | IP addresses in screenshots - MANDATORY | TRI THỨC RÚT RA |
| 11 | SSD vs HDD - IOPS is the decision factor | TRI THỨC RÚT RA |
| 12 | Backup storage - Separate from data | TRI THỨC RÚT RA |
| 13 | Using 2020 data - Validity check | TRI THỨC RÚT RA |
| 14 | Is current TPS still similar | TRI THỨC RÚT RA |
| 15 | Have data patterns changed | TRI THỨC RÚT RA |
| 16 | Is 5-year-old data still valid | TRI THỨC RÚT RA |
| 17 | N+1 for Database - Special consideration | TRI THỨC RÚT RA |
| 18 | Oracle MariaDB for sizing | BÀI HỌC KINH NGHIỆM |
| 19 | IP addresses in screenshots are MANDATORY | BÀI HỌC KINH NGHIỆM |
| 20 | SSD vs HDD decision based on IOPS | BÀI HỌC KINH NGHIỆM |
| 21 | Separate backup from data storage | BÀI HỌC KINH NGHIỆM |
| 22 | Old data (2020) may not be valid | BÀI HỌC KINH NGHIỆM |
| 23 | Database HA needs model specification | BÀI HỌC KINH NGHIỆM |
| 24 | Migration sizing requires testing | BÀI HỌC KINH NGHIỆM |

## cap moi MNP 32034

**PYC:** PYC-32034 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | KPI calculation error | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Sizing purpose | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Input data justification | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Network connections | LƯU Ý THẨM ĐỊNH PNX |
| 5 | FW/LB sizing | LƯU Ý THẨM ĐỊNH PNX |
| 6 | CPU unit conversion | LƯU Ý THẨM ĐỊNH PNX |
| 7 | APP server baseline | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Storage sizing (trang 56) | LƯU Ý THẨM ĐỊNH PNX |
| 9 | Detailed transaction analysis (trang 57) | LƯU Ý THẨM ĐỊNH PNX |
| 10 | XML message size (trang 59) | LƯU Ý THẨM ĐỊNH PNX |
| 11 | Transaction structure (trang 60) | LƯU Ý THẨM ĐỊNH PNX |
| 12 | Retention | LƯU Ý THẨM ĐỊNH PNX |
| 13 | KPI calculation - Correct method | TRI THỨC RÚT RA |
| 14 | Growth rate projection - 20%/year | TRI THỨC RÚT RA |
| 15 | XML message structure analysis | TRI THỨC RÚT RA |
| 16 | MNP-specific retention: 2 months | TRI THỨC RÚT RA |
| 17 | Network signaling vs data | TRI THỨC RÚT RA |
| 18 | Database table count: 6 tables | TRI THỨC RÚT RA |
| 19 | KPI is for division, not multiplication | BÀI HỌC KINH NGHIỆM |
| 20 | Growth rate must be justified | BÀI HỌC KINH NGHIỆM |
| 21 | XML file size needs actual proof | BÀI HỌC KINH NGHIỆM |
| 22 | Transaction structure affects sizing | BÀI HỌC KINH NGHIỆM |
| 23 | Retention policy requires justification | BÀI HỌC KINH NGHIỆM |
| 24 | Network sizing must consider peaks | BÀI HỌC KINH NGHIỆM |

## cap moi MySign 10371

**PYC:** PYC-8059 · **Thẩm định:** Khanhnd23 - P.Hệ thống · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Số Liệu Làm Tròn Quá Nhiều (Critical Error) | TRI THỨC RÚT RA TỪ PNX |
| 2 | Database Type Affects N Value (Important) | TRI THỨC RÚT RA TỪ PNX |
| 3 | Thiếu Phần App Sizing (Critical Omission) | TRI THỨC RÚT RA TỪ PNX |
| 4 | Timeline Confusion: 1 Tháng hay 6 Tháng | TRI THỨC RÚT RA TỪ PNX |
| 5 | Bảng Giá Trị N (N Value Table) | TRI THỨC RÚT RA TỪ PNX |
| 6 | Mục Đích Sizing Cụ Thể | TRI THỨC RÚT RA TỪ PNX |
| 7 | Sở Cứ SSD Usage | TRI THỨC RÚT RA TỪ PNX |
| 8 | Thiếu Thông Tin FW/LB Sizing | TRI THỨC RÚT RA TỪ PNX |
| 9 | Tổng Tài Nguyên Storage Chia Ra | TRI THỨC RÚT RA TỪ PNX |
| 10 | Lỗi Rounding Số Liệu | KINH NGHIỆM XỬ LÝ |
| 11 | Timeline Confusion Resolution | KINH NGHIỆM XỬ LÝ |
| 12 | N Value Calculation Methodology | KINH NGHIỆM XỬ LÝ |
| 13 | Rounding errors | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 14 | Timeline inconsistency | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 15 | DB type justification | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 16 | Missing App sizing | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 17 | N value table | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 18 | SSD justification | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 19 | Purpose clarity | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 20 | Connection details | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 21 | Workload estimation | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 22 | Peak traffic analysis | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 23 | Storage growth validation | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 24 | Firewall/LB capacity | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |

## cap bo sung Sizing_CloudCA_BoSungTaiNguyen 62967

**PYC:** PYC-62967 · **Thẩm định:** — · **Loại:** A · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | HỆ SỐ DỰ PHNG CAO CHO HỆ THỐNG ĐẶC BIỆT | CÁC BÀI HỌC THẨM ĐỊNH |
| 2 | HỆ SỐ DỰ PHNG 1.2 (HỆ SỐ 1.1) | CÁC BÀI HỌC THẨM ĐỊNH |
| 3 | YÊU CẦU RAM 96GB TỪ THẨM ĐỊNH VIÊN (chaulm5) | CÁC BÀI HỌC THẨM ĐỊNH |
| 4 | MÔ HÌNH DC-DR 1:1 CHO HỆ THỐNG ĐẶC BIỆT | CÁC BÀI HỌC THẨM ĐỊNH |
| 5 | SIZING MAXSCALE NODE | CÁC BÀI HỌC THẨM ĐỊNH |
| 6 | TÍNH TOÁN BĂNG THÔNG DC-DR REPLICATION | CÁC BÀI HỌC THẨM ĐỊNH |
| 7 | KPI KHÁC BIỆT CHO Database | CÁC BÀI HỌC THẨM ĐỊNH |
| 8 | NHIỆU SSD CHO DATABASE PERFORMANCE | CÁC BÀI HỌC THẨM ĐỊNH |
| 9 | ARCHITECTURE: ASYNCHRONOUS MULTI-MASTER | CÁC BÀI HỌC THẨM ĐỊNH |
| 10 | HỆ THỐNG ĐẶC BIỆT QUAN TRỌNG YÊU CẤU DC-DR 1:1 | CÁC BÀI HỌC QUAN TRỌNG |
| 11 | SỬ DỤNG RAM: 96GB CHO CRITICAL DATABASES | CÁC BÀI HỌC QUAN TRỌNG |
| 12 | TÍNH TOÁN BĂNG THÔNG REPLICATION | CÁC BÀI HỌC QUAN TRỌNG |
| 13 | IOPS OPTIMIZATION CHO DATABASE | CÁC BÀI HỌC QUAN TRỌNG |
| 14 | MAXSCALE TÍNH ÍT TÀI NGUYÊN, NHƯNG CẦN BUFFER | CÁC BÀI HỌC QUAN TRỌNG |
| 15 | FIREWALL/LB SIZING: BASED ON ACTUAL TRAFFIC | CÁC BÀI HỌC QUAN TRỌNG |
| 16 | KPI DATA NODE 50% (STRICTER THAN APP SERVERS) | CÁC BÀI HỌC QUAN TRỌNG |
| 17 | ASYNCHRONOUS MULTI-MASTER ARCHITECTURE | CÁC BÀI HỌC QUAN TRỌNG |
| 18 | SYSTEM CLASSIFICATION DIRECTS SIZING STRATEGY | KEY INSIGHTS |
| 19 | RAM SIZING FOR DATABASE SERVERS | KEY INSIGHTS |
| 20 | STORAGE STRATEGY FOR DATABASE CLUSTERS | KEY INSIGHTS |
| 21 | NETWORK INFRASTRUCTURE FOR DC-DR | KEY INSIGHTS |

## cap moi APIGee Mini App 64015

**PYC:** PYC-64015 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | HỆ THỐNG ĐẶC BIỆT QUAN TRỌNG BẮT BUỘC CÓ DR | CÁC BÀI HỌC THẨM ĐỊNH |
| 2 | TPS CALCULATION CHO API GATEWAY (20,000 TPS PEAK) | CÁC BÀI HỌC THẨM ĐỊNH |
| 3 | SO SÁNH PNX V1 vs PNX V2 - CÁC YÊU CẦU CHỈNH SỬA | CÁC BÀI HỌC THẨM ĐỊNH |
| 4 | TÍNH TOÁN CONCURRENT SESSION CHO FIREWALL (48,000 SESSIONS) | CÁC BÀI HỌC THẨM ĐỊNH |
| 5 | TÍNH TOÁN BĂNG THÔNG FIREWALL (3,820 MBPS) | CÁC BÀI HỌC THẨM ĐỊNH |
| 6 | LOAD BALANCER SIZING (1,094 MBPS, 3M SESSIONS) | CÁC BÀI HỌC THẨM ĐỊNH |
| 7 | APIGEE SERVER SIZING (51 NODES, ACTIVE-ACTIVE) | CÁC BÀI HỌC THẨM ĐỊNH |
| 8 | BAN CHỦ QUY ĐỊNH THỜI GIAN ĐỔ TẢI | CÁC BÀI HỌC THẨM ĐỊNH |
| 9 | CHECKLIST SIZING BẮT BUỘC KÝ | CÁC BÀI HỌC THẨM ĐỊNH |
| 10 | MÔ HÌNH LOGIC VÀ LUỒNG NGHIỆP VỤ | CÁC BÀI HỌC THẨM ĐỊNH |
| 11 | API GATEWAY SIZING: TPS PEAK × 4 | CÁC BÀI HỌC QUAN TRỌNG |
| 12 | CONCURRENT SESSION VERSUS TPS | CÁC BÀI HỌC QUAN TRỌNG |
| 13 | TPX CALCULATION: HOURS ACTIVE VERSUS 24/7 | CÁC BÀI HỌC QUAN TRỌNG |
| 14 | HORIZONTAL SCALING: 51 NODES | CÁC BÀI HỌC QUAN TRỌNG |
| 15 | DATABASE SEGREGATION: CASSANDRA VS POSTGRESQL | CÁC BÀI HỌC QUAN TRỌNG |
| 16 | STORAGE PLANNING: 376 TB FOR ANALYTICS | CÁC BÀI HỌC QUAN TRỌNG |
| 17 | SYSTEM IMPORTANCE DRIVES REQUIREMENTS | KEY INSIGHTS |
| 18 | TPS CALCULATION FOR API GATEWAYS | KEY INSIGHTS |
| 19 | CONCURRENT SESSION VERSUS TPS | KEY INSIGHTS |
| 20 | BANDWIDTH PLANNING FOR API GATEWAY | KEY INSIGHTS |
| 21 | DATABASE SEGREGATION STRATEGY | KEY INSIGHTS |

## CAPMOI_DB_MySign_8059

**PYC:** PYC-8059 · **Thẩm định:** Khanhnd23 (P.Hệ thống) · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Rounding errors | LƯU Ý THẨM ĐỊNH |
| 2 | DB type unclear | LƯU Ý THẨM ĐỊNH |
| 3 | Missing App sizing | LƯU Ý THẨM ĐỊNH |
| 4 | Network equipment | LƯU Ý THẨM ĐỊNH |
| 5 | N+1 configuration | LƯU Ý THẨM ĐỊNH |
| 6 | Timeframe confusion | LƯU Ý THẨM ĐỊNH |
| 7 | Storage breakdown | LƯU Ý THẨM ĐỊNH |
| 8 | IOPS justification | LƯU Ý THẨM ĐỊNH |
| 9 | SDD usage | LƯU Ý THẨM ĐỊNH |
| 10 | Connection info | LƯU Ý THẨM ĐỊNH |
| 11 | Rounding errors cascade | TRI THỨC RÚT RA |
| 12 | DB type affects N value | TRI THỨC RÚT RA |
| 13 | DC-only sizing is incomplete | TRI THỨC RÚT RA |
| 14 | N+1 redundancy clarity | TRI THỨC RÚT RA |
| 15 | Storage partitioning | TRI THỨC RÚT RA |
| 16 | Avoid intermediate rounding | BÀI HỌC KINH NGHIỆM |
| 17 | Confirm DB type before sizing | BÀI HỌC KINH NGHIỆM |
| 18 | Size ALL components | BÀI HỌC KINH NGHIỆM |
| 19 | N+1 is formula, not magic number | BÀI HỌC KINH NGHIỆM |
| 20 | Partition storage by function | BÀI HỌC KINH NGHIỆM |
| 21 | Justify SSD usage | BÀI HỌC KINH NGHIỆM |

## cap moi Data Security VTT 18476

**PYC:** PYC-18476 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Nhận xét chung | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Mục I - Thông tin hệ thống | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Trang 2 - Input data | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Trang 3 - CPU sizing | LƯU Ý THẨM ĐỊNH PNX |
| 5 | RAM sizing | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Trang 4 - RAM sizing | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Thiết bị lưu trữ | LƯU Ý THẨM ĐỊNH PNX |
| 8 | Show your work - FORMULA IS MANDATORY | TRI THỨC RÚT RA |
| 9 | KPI 75% - Dont misuse it | TRI THỨC RÚT RA |
| 10 | Backup 2 copies - Context matters | TRI THỨC RÚT RA |
| 11 | System-specific sizing: Data Security | TRI THỨC RÚT RA |
| 12 | Reference links for CPU specs | TRI THỨC RÚT RA |
| 13 | N+1 following Viettel model | TRI THỨC RÚT RA |
| 14 | FORMULA IS NOT OPTIONAL | BÀI HỌC KINH NGHIỆM |
| 15 | KPI is a constraint, not input | BÀI HỌC KINH NGHIỆM |
| 16 | Backup policy needs context | BÀI HỌC KINH NGHIỆM |
| 17 | Security systems need overhead | BÀI HỌC KINH NGHIỆM |
| 18 | Reference links are mandatory | BÀI HỌC KINH NGHIỆM |
| 19 | Follow Viettel HA model | BÀI HỌC KINH NGHIỆM |
| 20 | Table format for server count | BÀI HỌC KINH NGHIỆM |

## hethong Vtag

**PYC:** — · **Thẩm định:** Lê Đình Hoàng (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Cint unit consistency - CRITICAL | TRI THỨC RÚT RA |
| 2 | Formal approval requirement - Not optional | TRI THỨC RÚT RA |
| 3 | Worker calculation error - CASE STUDY | TRI THỨC RÚT RA |
| 4 | Division doesnt make sense | TRI THỨC RÚT RA |
| 5 | Why divide by 3 | TRI THỨC RÚT RA |
| 6 | Result 0.8 TPS/server | TRI THỨC RÚT RA |
| 7 | PostgreSQL sizing - 2000 devices and 3-month retention | TRI THỨC RÚT RA |
| 8 | N+1 HA requirement - Formal standard | TRI THỨC RÚT RA |
| 9 | Kafka and MongoDB - Special sizing considerations | TRI THỨC RÚT RA |
| 10 | Redis and MQTT - Cache and messaging | TRI THỨC RÚT RA |
| 11 | Verification with actual screenshots - MANDATORY | TRI THỨC RÚT RA |
| 12 | Cint unit consistency is NON-NEGOTIABLE | BÀI HỌC KINH NGHIỆM |
| 13 | Formal approval is MANDATORY for baselines | BÀI HỌC KINH NGHIỆM |
| 14 | Verify EVERY calculation step | BÀI HỌC KINH NGHIỆM |
| 15 | Database retention needs policy justification | BÀI HỌC KINH NGHIỆM |
| 16 | HA is NOT optional for production | BÀI HỌC KINH NGHIỆM |
| 17 | Kafka/MongoDB need special sizing considerations | BÀI HỌC KINH NGHIỆM |
| 18 | Screenshots must show ALL required info | BÀI HỌC KINH NGHIỆM |
| 19 | Reference links must be VALID | BÀI HỌC KINH NGHIỆM |

## cap moi Mykid 2.0 30959

**PYC:** PYC-30959 · **Thẩm định:** Khanhnd23 - P.Hệ thống · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Sở Cứ Rõ Nàng Cho Mọi Con Số (Critical) | TRI THỨC RÚT RA TỪ PNX |
| 2 | Mục Đích Sizing Phải Cụ Thể | TRI THỨC RÚT RA TỪ PNX |
| 3 | KPI RAM là 90%, Không Phải 75% (Important Error) | TRI THỨC RÚT RA TỪ PNX |
| 4 | Công Thức Tính Toán Dung Lượng Lưu Trữ | TRI THỨC RÚT RA TỪ PNX |
| 5 | Lỗi KPI RAM 75% vs 90% | KINH NGHIỆM XỬ LÝ |
| 6 | Reference System Sizing Validation | KINH NGHIỆM XỬ LÝ |
| 7 | Timeline Decision Making Framework | KINH NGHIỆM XỬ LÝ |
| 8 | Sở cứ số liệu | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 9 | Ảnh/screenshots | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 10 | Mục đích sizing | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 11 | Timeline | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 12 | Công thức tính toán | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 13 | Nghiệp vụ sở cứ | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 14 | Request/giây calculation | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 15 | N+1 justification | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 16 | Multi-timeline recommendation | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 17 | Storage retention | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |
| 18 | Peak factor | CHECK LIST ĐÁNH GIÁ TRẠNG THÁI |

## cap moi Viettel Report_2026 62005

**PYC:** PYC-62005 · **Thẩm định:** khanhnd23 (P.CNHT) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | ĐBQT DR mandatory | LƯU Ý THẨM ĐỊNH |
| 2 | Timeline | LƯU Ý THẨM ĐỊNH |
| 3 | Input data | LƯU Ý THẨM ĐỊNH |
| 4 | Reference | LƯU Ý THẨM ĐỊNH |
| 5 | Storage policy | LƯU Ý THẨM ĐỊNH |
| 6 | Bỏ SSD/DDR4 | LƯU Ý THẨM ĐỊNH |
| 7 | Partition | LƯU Ý THẨM ĐỊNH |
| 8 | LB details | LƯU Ý THẨM ĐỊNH |
| 9 | Report system characteristics | TRI THỨC RÚT RA |
| 10 | Storage partitioning strategy | TRI THỨC RÚT RA |
| 11 | Log retention calculation | TRI THỨC RÚT RA |
| 12 | Backup policy considerations | TRI THỨC RÚT RA |
| 13 | IOPS calculation methodology | TRI THỨC RÚT RA |
| 14 | Report systems are storage-heavy | BÀI HỌC KINH NGHIỆM |
| 15 | Partition separation is essential | BÀI HỌC KINH NGHIỆM |
| 16 | 365 days retention is significant | BÀI HỌC KINH NGHIỆM |
| 17 | Calculate IOPS before choosing SSD | BÀI HỌC KINH NGHIỆM |
| 18 | Business forecast validation | BÀI HỌC KINH NGHIỆM |

## cap moi CloudCA_2025_TACHCUM_THAYDOIMOHINH 55875

**PYC:** PYC-55875 · **Thẩm định:** khanhnd23 (Phòng Công nghệ Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Virtualization DB cluster | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Cú pháp bảng tổng hợp | LƯU Ý THẨM ĐỊNH PNX |
| 3 | DB Storage division inconsistency | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Maxscale node count | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Redis cluster sizing | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Load Balancer sizing | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Large RAM vs Virtualization Trade-off | TRI THỨC RÚT RA |
| 8 | Storage division inconsistency | TRI THỨC RÚT RA |
| 9 | Maxscale node selection | TRI THỨC RÚT RA |
| 10 | Redis cluster sizing | TRI THỨC RÚT RA |
| 11 | Load Balancer sizing | TRI THỨC RÚT RA |
| 12 | DB sizing: Large RAM không phải lúc nào cũng tốt | BÀI HỌC KINH NGHIỆM |
| 13 | LUÔN check consistency trong calculation | BÀI HỌC KINH NGHIỆM |
| 14 | Proxy node count phải có justification | BÀI HỌC KINH NGHIỆM |
| 15 | LB sizing phải rõ ràng về layer và traffic | BÀI HỌC KINH NGHIỆM |
| 16 | Avoid cú pháp không cần thiết | BÀI HỌC KINH NGHIỆM |
| 17 | Explain your choices | BÀI HỌC KINH NGHIỆM |

## cap moi Log tap trung AI chatbot 16669

**PYC:** PYC-16669 · **Thẩm định:** Khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Hình ảnh minh cụ không rõ IP | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Thiếu thông số network | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Sửa mục đích sizing | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Tải hệ thống hiện tại (trang 11) | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Log retention - YÊU CẦU QUAN TRỌNG | LƯU Ý THẨM ĐỊNH PNX |
| 6 | SSD vs HDD | LƯU Ý THẨM ĐỊNH PNX |
| 7 | Network I/O measurement - MANDATORY | TRI THỨC RÚT RA |
| 8 | Log compression strategy - MUST DO | TRI THỨC RÚT RA |
| 9 | 60 vs 180 days retention - Which one | TRI THỨC RÚT RA |
| 10 | RAM virtualization threshold | TRI THỨC RÚT RA |
| 11 | SSD vs HDD - IOPS requirement | TRI THỨC RÚT RA |
| 12 | Network I/O is CRITICAL for log systems | BÀI HỌC KINH NGHIỆM |
| 13 | Log compression is NOT optional | BÀI HỌC KINH NGHIỆM |
| 14 | RAM threshold for virtualization: 64 GB | BÀI HỌC KINH NGHIỆM |
| 15 | SSD vs HDD depends on workload | BÀI HỌC KINH NGHIỆM |
| 16 | Screenshot clarity is mandatory | BÀI HỌC KINH NGHIỆM |
| 17 | Operational vs regulatory retention | BÀI HỌC KINH NGHIỆM |

## cap moi PBH 21050

**PYC:** PYC-20043 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 6

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Test system sizing | LƯU Ý THẨM ĐỊNH |
| 2 | CPU core mismatch | LƯU Ý THẨM ĐỊNH |
| 3 | Cint rate calculation | LƯU Ý THẨM ĐỊNH |
| 4 | S3 storage | LƯU Ý THẨM ĐỊNH |
| 5 | Network throughput | LƯU Ý THẨM ĐỊNH |
| 6 | Database | LƯU Ý THẨM ĐỊNH |
| 7 | Test-based sizing - Validation critical | TRI THỨC RÚT RA |
| 8 | Partial CPU utilization issue | TRI THỨC RÚT RA |
| 9 | S3 storage with replication factor | TRI THỨC RÚT RA |
| 10 | Network throughput: 12Gbps validation | TRI THỨC RÚT RA |
| 11 | 110 tables/database - Sampling strategy | TRI THỨC RÚT RA |
| 12 | RAM 125GB - Physical server constraint | TRI THỨC RÚT RA |
| 13 | Test scaling may not be linear for large jumps | BÀI HỌC KINH NGHIỆM |
| 14 | Partial CPU utilization must be explained | BÀI HỌC KINH NGHIỆM |
| 15 | Replication factor 3x cost | BÀI HỌC KINH NGHIỆM |
| 16 | Network throughput needs dedicated path | BÀI HỌC KINH NGHIỆM |
| 17 | Database sizing separate from app cluster | BÀI HỌC KINH NGHIỆM |

## cap moi Viettel App_v1.0 53803

**PYC:** PYC-53803 · **Thẩm định:** khanhnd23 · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | HSDP only | LƯU Ý THẨM ĐỊNH |
| 2 | Notation | LƯU Ý THẨM ĐỊNH |
| 3 | Network card | LƯU Ý THẨM ĐỊNH |
| 4 | Input data | LƯU Ý THẨM ĐỊNH |
| 5 | Storage time | LƯU Ý THẨM ĐỊNH |
| 6 | LB calculation | LƯU Ý THẨM ĐỊNH |
| 7 | DB unit issue | LƯU Ý THẨM ĐỊNH |
| 8 | Load balancer sizing - HSDP only | TRI THỨC RÚT RA |
| 9 | Network card justification | TRI THỨC RÚT RA |
| 10 | Database event sizing unit error | TRI THỨC RÚT RA |
| 11 | Precise LB calculations | TRI THỨC RÚT RA |
| 12 | Evidence documentation | TRI THỨC RÚT RA |
| 13 | HSDP KPI for network equipment | BÀI HỌC KINH NGHIỆM |
| 14 | Unit consistency is critical | BÀI HỌC KINH NGHIỆM |
| 15 | Precise numbers, not ranges | BÀI HỌC KINH NGHIỆM |
| 16 | Network tier must be justified | BÀI HỌC KINH NGHIỆM |
| 17 | Evidence in multiple formats | BÀI HỌC KINH NGHIỆM |

## cap moi VT CAMERA AI 23478

**PYC:** PYC-23096 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | 300 Camera devices | LƯU Ý THẨM ĐỊNH |
| 2 | Multiple reference systems | LƯU Ý THẨM ĐỊNH |
| 3 | Large storage | LƯU Ý THẨM ĐỊNH |
| 4 | GPU requirement | LƯU Ý THẨM ĐỊNH |
| 5 | Bandwidth | LƯU Ý THẨM ĐỊNH |
| 6 | Network topology | LƯU Ý THẨM ĐỊNH |
| 7 | Retention | LƯU Ý THẨM ĐỊNH |
| 8 | AI Camera bandwidth calculation | TRI THỨC RÚT RA |
| 9 | Storage indexing multiplier | TRI THỨC RÚT RA |
| 10 | GPU for AI workloads | TRI THỨC RÚT RA |
| 11 | Multi-system architecture | TRI THỨC RÚT RA |
| 12 | RPS calculation | TRI THỨC RÚT RA |
| 13 | AI GPU + Storage intensive | BÀI HỌC KINH NGHIỆM |
| 14 | Reference multiple similar systems | BÀI HỌC KINH NGHIỆM |
| 15 | Bandwidth calculation by images | BÀI HỌC KINH NGHIỆM |
| 16 | RPS vs TPS clarification | BÀI HỌC KINH NGHIỆM |
| 17 | Zone Internet considerations | BÀI HỌC KINH NGHIỆM |

## cap moi Mybox 38327

**PYC:** PYC-38327 · **Thẩm định:** Khanhnd23 · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Input data inconsistency | LƯU Ý THẨM ĐỊNH PNX |
| 2 | CCU calculation error | LƯU Ý THẨM ĐỊNH PNX |
| 3 | ELK Stack sizing | LƯU Ý THẨM ĐỊNH PNX |
| 4 | SSD justification | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Notation | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Current production data | LƯU Ý THẨM ĐỊNH PNX |
| 7 | File storage capacity planning | TRI THỨC RÚT RA |
| 8 | CCU calculation - Include boot time | TRI THỨC RÚT RA |
| 9 | ELK Stack sizing considerations | TRI THỨC RÚT RA |
| 10 | SSD vs HDD for ELK | TRI THỨC RÚT RA |
| 11 | Storage projection | TRI THỨC RÚT RA |
| 12 | Validate input data consistency | BÀI HỌC KINH NGHIỆM |
| 13 | CCU excludes boot overhead | BÀI HỌC KINH NGHIỆM |
| 14 | ELK needs hot/warm storage tier | BÀI HỌC KINH NGHIỆM |
| 15 | Storage per user is useful metric | BÀI HỌC KINH NGHIỆM |

## cap moi Smarthome 13709

**PYC:** PYC-13709 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 3

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | 500K devices target | LƯU Ý THẨM ĐỊNH |
| 2 | CPU specs | LƯU Ý THẨM ĐỊNH |
| 3 | IOPS calculation | LƯU Ý THẨM ĐỊNH |
| 4 | FW/LB sizing | LƯU Ý THẨM ĐỊNH |
| 5 | Summary table | LƯU Ý THẨM ĐỊNH |
| 6 | Scaling 100K 500K devices (5x) | TRI THỨC RÚT RA |
| 7 | K8S worker nodes per namespace | TRI THỨC RÚT RA |
| 8 | Multi-database architecture | TRI THỨC RÚT RA |
| 9 | IOPS calculation for SSD justification | TRI THỨC RÚT RA |
| 10 | FW/LB safety factor 1.2 only | TRI THỨC RÚT RA |
| 11 | 5x scale is aggressive | BÀI HỌC KINH NGHIỆM |
| 12 | CPU spec clarity is mandatory | BÀI HỌC KINH NGHIỆM |
| 13 | IOPS drives SSD decision | BÀI HỌC KINH NGHIỆM |
| 14 | FW/LB uses different safety factor | BÀI HỌC KINH NGHIỆM |
| 15 | Namespace-level granularity | BÀI HỌC KINH NGHIỆM |

## cap moi TMaketing 60476

**PYC:** PYC-60476 · **Thẩm định:** khanhnd23 (P.CNHT) · **Loại:** — · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | ĐBQT requirement | LƯU Ý THẨM ĐỊNH |
| 2 | Timeline | LƯU Ý THẨM ĐỊNH |
| 3 | Checklist | LƯU Ý THẨM ĐỊNH |
| 4 | CCU baseline | LƯU Ý THẨM ĐỊNH |
| 5 | Reference system | LƯU Ý THẨM ĐỊNH |
| 6 | Marketing module profile | TRI THỨC RÚT RA |
| 7 | SSD vs HDD decision | TRI THỨC RÚT RA |
| 8 | Storage separation architecture | TRI THỨC RÚT RA |
| 9 | Backup strategy | TRI THỨC RÚT RA |
| 10 | CCU calculation methodology | TRI THỨC RÚT RA |
| 11 | Marketing has bursty traffic | BÀI HỌC KINH NGHIỆM |
| 12 | 5% CCU is reasonable baseline | BÀI HỌC KINH NGHIỆM |
| 13 | Separate OS and data disks | BÀI HỌC KINH NGHIỆM |
| 14 | Calculate IOPS before choosing SSD | BÀI HỌC KINH NGHIỆM |
| 15 | 6-month retention for marketing | BÀI HỌC KINH NGHIỆM |

## cap moi Viettel API Gateway 65091

**PYC:** PYC-65091 · **Thẩm định:** khanhnd23 (P.CNHT) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | ĐBQT DR mandatory | LƯU Ý THẨM ĐỊNH |
| 2 | Business flow | LƯU Ý THẨM ĐỊNH |
| 3 | Reference | LƯU Ý THẨM ĐỊNH |
| 4 | Virtualization limit | LƯU Ý THẨM ĐỊNH |
| 5 | LB details | LƯU Ý THẨM ĐỊNH |
| 6 | Notation | LƯU Ý THẨM ĐỊNH |
| 7 | API Gateway architecture | TRI THỨC RÚT RA |
| 8 | HDD acceptable for API Gateway | TRI THỨC RÚT RA |
| 9 | Virtualization thresholds | TRI THỨC RÚT RA |
| 10 | Load balancer sizing details | TRI THỨC RÚT RA |
| 11 | API Gateway is network-intensive | BÀI HỌC KINH NGHIỆM |
| 12 | 300 CCU needs justification | BÀI HỌC KINH NGHIỆM |
| 13 | Virtualization thresholds matter | BÀI HỌC KINH NGHIỆM |
| 14 | ELK can use tiered storage | BÀI HỌC KINH NGHIỆM |
| 15 | LB sizing requires detail | BÀI HỌC KINH NGHIỆM |

## cap moi niêm yết cục viễn thông 47827

**PYC:** PYC-47827 · **Thẩm định:** khanhnd23 · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | K8S microservices | LƯU Ý THẨM ĐỊNH |
| 2 | Storage standard | LƯU Ý THẨM ĐỊNH |
| 3 | Import workload | LƯU Ý THẨM ĐỊNH |
| 4 | DB sizing | LƯU Ý THẨM ĐỊNH |
| 5 | Safety factor | LƯU Ý THẨM ĐỊNH |
| 6 | RAM 64GB | LƯU Ý THẨM ĐỊNH |
| 7 | K8S microservice sizing - Per-module baseline | TRI THỨC RÚT RA |
| 8 | HSDP (Hệ số dự phòng) 1.2 only | TRI THỨC RÚT RA |
| 9 | Import batch processing | TRI THỨC RÚT RA |
| 10 | Database growth calculation | TRI THỨC RÚT RA |
| 11 | Microservices need per-module sizing | BÀI HỌC KINH NGHIỆM |
| 12 | HSDP KPI | BÀI HỌC KINH NGHIỆM |
| 13 | Import batch affects memory | BÀI HỌC KINH NGHIỆM |
| 14 | Storage growth tied to business cycle | BÀI HỌC KINH NGHIỆM |

## cap moi SSO 2.0 46385

**PYC:** PYC-46385 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | KPI thresholds | LƯU Ý THẨM ĐỊNH |
| 2 | MariaDB Galera Cluster | LƯU Ý THẨM ĐỊNH |
| 3 | N+4 justification | LƯU Ý THẨM ĐỊNH |
| 4 | Reference system | LƯU Ý THẨM ĐỊNH |
| 5 | SSO 2.0 architecture - Multi-master database | TRI THỨC RÚT RA |
| 6 | Low KPI issue - Why 70%, 50%, 60% | TRI THỨC RÚT RA |
| 7 | N+4 vs N+1 redundancy | TRI THỨC RÚT RA |
| 8 | Storage retention policies | TRI THỨC RÚT RA |
| 9 | One-way integration pattern | TRI THỨC RÚT RA |
| 10 | Galera Cluster scales differently | BÀI HỌC KINH NGHIỆM |
| 11 | Low KPI Over-provisioning | BÀI HỌC KINH NGHIỆM |
| 12 | N+4 is unusual | BÀI HỌC KINH NGHIỆM |
| 13 | SSO has bursty traffic pattern | BÀI HỌC KINH NGHIỆM |
| 14 | Long retention has storage impact | BÀI HỌC KINH NGHIỆM |

## cap moi Stringee 62570

**PYC:** PYC-62570 · **Thẩm định:** khanhnd23 (P.CNHT) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Mức độ quan trọng | LƯU Ý THẨM ĐỊNH |
| 2 | Timeline | LƯU Ý THẨM ĐỊNH |
| 3 | Checklist | LƯU Ý THẨM ĐỊNH |
| 4 | Load inconsistency | LƯU Ý THẨM ĐỊNH |
| 5 | Resource gap | LƯU Ý THẨM ĐỊNH |
| 6 | ĐBQT system DR mandatory | TRI THỨC RÚT RA |
| 7 | Load inconsistency is common issue | TRI THỨC RÚT RA |
| 8 | Resource gap calculation | TRI THỨC RÚT RA |
| 9 | Video call system architecture | TRI THỨC RÚT RA |
| 10 | ĐBQT double resources | BÀI HỌC KINH NGHIỆM |
| 11 | Load numbers must be consistent | BÀI HỌC KINH NGHIỆM |
| 12 | Expansion delta not total | BÀI HỌC KINH NGHIỆM |
| 13 | Video call needs GPU consideration | BÀI HỌC KINH NGHIỆM |
| 14 | Timeline commitment required | BÀI HỌC KINH NGHIỆM |

## Cap_moi_he_thong_VAPS

**PYC:** PYC-57140 · **Thẩm định:** thongnv31 (P.CNHT) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Missing servers | LƯU Ý THẨM ĐỊNH |
| 2 | TPS vs CCU | LƯU Ý THẨM ĐỊNH |
| 3 | Test data | LƯU Ý THẨM ĐỊNH |
| 4 | Reference system | LƯU Ý THẨM ĐỊNH |
| 5 | Database partitions | LƯU Ý THẨM ĐỊNH |
| 6 | Input justification | LƯU Ý THẨM ĐỊNH |
| 7 | K8S microservice architecture | TRI THỨC RÚT RA |
| 8 | TPS vs CCU confusion | TRI THỨC RÚT RA |
| 9 | Database partitioning | TRI THỨC RÚT RA |
| 10 | Viettel++ reference system | TRI THỨC RÚT RA |
| 11 | Dont mix TPS and CCU | BÀI HỌC KINH NGHIỆM |
| 12 | All servers must be included | BÀI HỌC KINH NGHIỆM |
| 13 | Test environment sizing is tricky | BÀI HỌC KINH NGHIỆM |
| 14 | Database partitioning is mandatory | BÀI HỌC KINH NGHIỆM |

## cap moi CALLBASE 44087

**PYC:** PYC-44087 · **Thẩm định:** khanhnd23 (Phòng Hệ thống) · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Sở chứ định cỡ | LƯU Ý THẨM ĐỊNH PNX |
| 2 | Cấu hình server testbed (Trang 4) | LƯU Ý THẨM ĐỊNH PNX |
| 3 | Thông lượng Firewall | LƯU Ý THẨM ĐỊNH PNX |
| 4 | Hình ảnh sở cứ | LƯU Ý THẨM ĐỊNH PNX |
| 5 | Thông số RAM | LƯU Ý THẨM ĐỊNH PNX |
| 6 | Phương pháp định cỡ dựa trên Testbed | TRI THỨC RÚT RA |
| 7 | Chuyển đổi Cint2006 Cint2017 | TRI THỨC RÚT RA |
| 8 | Định cỡ Firewall cho hệ thống lấy tín hiệu | TRI THỨC RÚT RA |
| 9 | KPI và Hệ số an toàn | TRI THỨC RÚT RA |
| 10 | Kiểm tra kỹ công thức chuyển đổi đơn vị | BÀI HỌC KINH NGHIỆM |
| 11 | Tránh dùng phép so sánh không cần thiết | BÀI HỌC KINH NGHIỆM |
| 12 | Hình ảnh minh chứng | BÀI HỌC KINH NGHIỆM |
| 13 | Testbed sizing | BÀI HỌC KINH NGHIỆM |

## cap moi Vcall 49637

**PYC:** PYC-47827 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 3

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Retention | LƯU Ý THẨM ĐỊNH |
| 2 | Virtualization | LƯU Ý THẨM ĐỊNH |
| 3 | Reference | LƯU Ý THẨM ĐỊNH |
| 4 | VCall architecture breakdown | TRI THỨC RÚT RA |
| 5 | Large-scale database distribution | TRI THỨC RÚT RA |
| 6 | Serice-specific sizing (Mocha reference) | TRI THỨC RÚT RA |
| 7 | SSD justification for each DB | TRI THỨC RÚT RA |
| 8 | VoIP-specific considerations | TRI THỨC RÚT RA |
| 9 | Large CCU requires strong justification | BÀI HỌC KINH NGHIỆM |
| 10 | HBase needs cluster approach | BÀI HỌC KINH NGHIỆM |
| 11 | SSD justifies by workload type | BÀI HỌC KINH NGHIỆM |
| 12 | VoIP needs accurate codec sizing | BÀI HỌC KINH NGHIỆM |
| 13 | Reference system is Mocha | BÀI HỌC KINH NGHIỆM |

## cap moi VDA 12720

**PYC:** PYC-12720 · **Thẩm định:** Khanhnd23 · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Sởffff chỉ | LƯU Ý THẨM ĐỊNH |
| 2 | Throughput | LƯU Ý THẨM ĐỊNH |
| 3 | Mục đích | LƯU Ý THẨM ĐỊNH |
| 4 | Mức độ quan trọng | LƯU Ý THẨM ĐỊNH |
| 5 | Database server conversion | TRI THỨC RÚT RA |
| 6 | SSD justification for database | TRI THỨC RÚT RA |
| 7 | Throughput calculation for database | TRI THỨC RÚT RA |
| 8 | CPU reference requirements | TRI THỨC RÚT RA |
| 9 | Every number needs justification | BÀI HỌC KINH NGHIỆM |
| 10 | Database SSD generally | BÀI HỌC KINH NGHIỆM |
| 11 | Network sizing matters | BÀI HỌC KINH NGHIỆM |
| 12 | Include CPU SPEC benchmarks | BÀI HỌC KINH NGHIỆM |

## cap_bo_sun_VTracking_2_0_114716

**PYC:** PYC-14716 · **Thẩm định:** — · **Loại:** — · **Số vòng:** 2

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | TÍNH THEO GIÁ TRỊ TUYỆT ĐỐI (KHÔNG LÀM TRÒN) | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 2 | CẤU HÌNH KHÔNG VƯỢT QUÁ MAX VM | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 3 | HỆ SỐ DỰ PHÒNG CHO LOAD BALANCER FIREWALL | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 4 | MẪU TEST LẤY GIÁ TRỊ TRUNG BÌNH | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 5 | TÁCH BIỆT GIỜ CAO ĐIỂM VÀ THẤP ĐIỂM CHO GPS | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 6 | CHIẾN LƯỢC LƯU TRỮ GPS: DB vs FILE | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 7 | HỆ SỐ DỰ PHÒNG CHI TIẾT TỪ TEST | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 8 | CUNG CẤP LINK SPEC CPU VÀ ẢNH CHỤP CẤU HÌNH | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 9 | SỞ CỨ CHO CÁC TỶ LỆ % (98%, 70%, 14%) | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 10 | TIÊU CHUẨN SIZING CHO IOT SYSTEMS | CÁC BÀI HỌC APPLY CHO CÁC DỰ ÁN IOT KH |
| 11 | TRÁNH CÁC LỖI PHỔ BIẾN | CÁC BÀI HỌC APPLY CHO CÁC DỰ ÁN IOT KH |
| 12 | BEST PRACTICES THAM KHẢO | CÁC BÀI HỌC APPLY CHO CÁC DỰ ÁN IOT KH |

## cap bo sung jenkins 57781

**PYC:** PYC-57781 · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | CHUẨN K8S: TÁCH BIỆT CONTROL-PLANE VÀ WORKER | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 2 | SỐ LƯỢNG MASTER NODES: LUÔN LÀ SỐ LẺ | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 3 | ETCD REPLICAS: TỐI THIỂU 3 BẢN SAO | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 4 | TÍNH TOÁN BĂNG THÔNG CHO CI/CD SYSTEM | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 5 | LOAD BALANCER CHO K8S CONTROL-PLANE | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 6 | SIZING MASTER NODES THEO CHUẨN K8S | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 7 | CHIẾN LƯỢC CẤP PHÁT LINH HOẠT | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 8 | THỜI GIAN ĐẢM BẢO ĐỔ TẢI | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 9 | QUY MÔ HỆ THỐNG DỰA TRÊN BUSINESS PLAN | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |
| 10 | MSIZE UNG DỤNG CI/CD ĐANG CHẠY | CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY |

## cap moi APPSEALING 18025

**PYC:** PYC-18025 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 6

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | VENDOR-SPECIFIC SIZING (BÊN THỨ 3) | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 2 | STATEFULSETS SERVICE YÊU CẤU NFS | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 3 | MYSQL + ELASTICSEARCH SIZING (SHARED STORAGE) | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 4 | TÍNH TOÁN BĂNG THÔNG CHO 100K ACTIVEDEVICES/DAY | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 5 | K8S CLUSTER SIZING: 5 NODES (1 MASTER + 4 SLAVES) | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 6 | FIREWALL SIZING DỰA TRÊN VENDOR SPECS | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 7 | STORAGE STRATEGY: 500GB LOCAL + 574,2 GB NFS | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 8 | EMAIL CONFIRMATION CỰNG TỪ VENDOR | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 9 | CỔNG NGHỆ THỐNG TỪ VENDOR: K8S + MYSQL + ELASTICSEARCH | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 10 | TÍNH TOÁN DISK: 574,2 GB CHO 100K ACTIVEDEVICES | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |

## cap moi PBH 4.0 20043

**PYC:** PYC-20043 (Sao với PBH 21050) · **Thẩm định:** Khanhnd23 · **Loại:** — · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Emergency sizing | LƯU Ý THẨM ĐỊNH |
| 2 | Sizing scope | LƯU Ý THẨM ĐỊNH |
| 3 | Inconsistency | LƯU Ý THẨM ĐỊNH |
| 4 | CPU values | LƯU Ý THẨM ĐỊNH |
| 5 | Emergency sizing workflow - VTNet UCTT | TRI THỨC RÚT RA |
| 6 | RAM inconsistency traceability | TRI THỨC RÚT RA |
| 7 | Separated concern - Sizing scope | TRI THỨC RÚT RA |
| 8 | Follow emergency sizing流程 | BÀI HỌC KINH NGHIỆM |
| 9 | Config vs actual inconsistency | BÀI HỌC KINH NGHIỆM |
| 10 | Separated sizing concerns | BÀI HỌC KINH NGHIỆM |

## cap moi StrongSwan 40325

**PYC:** PYC-40325 · **Thẩm định:** Khanhnd23 · **Loại:** A · **Số vòng:** 1

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Throughput alignment | LƯU Ý THẨM ĐỊNH |
| 2 | Notation | LƯU Ý THẨM ĐỊNH |
| 3 | Table format | LƯU Ý THẨM ĐỊNH |
| 4 | StrongSwan VPN architecture | TRI THỨC RÚT RA |
| 5 | VPN throughput sizing | TRI THỨC RÚT RA |
| 6 | Storage requirements for VPN | TRI THỨC RÚT RA |
| 7 | N+1 for VPN gateways | TRI THỨC RÚT RA |
| 8 | Throughput must match reality | BÀI HỌC KINH NGHIỆM |
| 9 | VPN storage is minimal | BÀI HỌC KINH NGHIỆM |
| 10 | N+1 essential for VPN | BÀI HỌC KINH NGHIỆM |

## cap moi APIGW-Meta_2024 18927

**PYC:** PYC-18927 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 4

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | LỖI ĐƠN VỊ TÍNH: KB/s SANG Mb/s | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 2 | TÍNH TOÁN BĂNG THÔNG UPLOAD CHO 700 TPS | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 3 | KÍCH THƯỚC REQUEST/RESPONSE CẦN SỞ CỨ THỰC TẾ | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 4 | CHI TIẾT KHI CHIA TÀI NGUYÊN THÀNH N+1 SERVERS | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 5 | HDD VERSUS SSD CHO API GATEWAY | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 6 | MÔ HÌNH DEPLOYMENT: DOCKER SWARM + ELASTICSEARCH | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 7 | SỐ LIỆU TÍNH TOÁN PHÍA TRÊN VÀ PHÍA DƯỚI KHÁC NHAU | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 8 | RAM VERSUS CPU: CINT VERSUS VCPU | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |
| 9 | LOG STORAGE PLANNING (833,25 GB/MONTH) | CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG |

## cap_bo_sung_campaign

**PYC:** PYC-8964 · **Thẩm định:** — · **Loại:** — · **Số vòng:** 3

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | YÊU CẦU BỔ SUNG SỞ CỨ TĂNG TRƯỞNG | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 2 | THIẾU THÔNG TIN CPU | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 3 | SỞ CỨ SỬ DỤNG SSD | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 4 | CÔNG THỨC TÍNH TOÁN SAI | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 5 | MÔ HÌNH N+1 (REDUNDANCY) | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 6 | ĐƠN VỊ TÍNH TOÁN (SAI) | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |
| 7 | DỮ LIỆU FIREWALL (KHÔNG NHÂN 3) | CÁC BÀI HỌC THẨM ĐỊNH CRITICAL INSIGHT |

## cap moi ARVR

**PYC:** PYC-645/VAS · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | CDN CACHE RATIO 98% GIẢM BĂNG THÔNG ORIGIN | CÁC BÀI HỌC THẨM ĐỊNH |
| 2 | TRANSCODER CẦN CPU CAO (16 vCPU) CHO VIDEO 4K | CÁC BÀI HỌC THẨM ĐỊNH |
| 3 | STORAGE CHO NỘI DUNG AR/VR: 5TB | CÁC BÀI HỌC THẨM ĐỊNH |
| 4 | N+1 BACKUP CHO 8 SERVERS | CÁC BÀI HỌC THẨM ĐỊNH |
| 5 | HỆ THỐNG THỬ NGHIỆM ÍT NGHIÊM GHT MORE RELAXED | CÁC BÀI HỌC THẨM ĐỊNH |

## cap moi c360 58872

**PYC:** PYC-58872 · **Thẩm định:** — · **Loại:** A · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Bổ sung RAM cho hệ thống sản xuất | BÀI HỌC QUAN TRỌNG |
| 2 | Sizing dựa trên benchmark | BÀI HỌC QUAN TRỌNG |
| 3 | Hệ thống C360 data warehouse | BÀI HỌC QUAN TRỌNG |
| 4 | Database nodes: 3 servers (10.207.62.120-122) | BÀI HỌC QUAN TRỌNG |
| 5 | Dữ liệu tăng trưởng 20%/năm | BÀI HỌC QUAN TRỌNG |

## cap moi C360_Public 9367

**PYC:** PYC-9367 · **Thẩm định:** — · **Loại:** A · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | Public Internet access | BÀI HỌC QUAN TRỌNG |
| 2 | HDD 501.87 GB | BÀI HỌC QUAN TRỌNG |
| 3 | CPU 10.24 Cint | BÀI HỌC QUAN TRỌNG |
| 4 | RAM 44 GB | BÀI HỌC QUAN TRỌNG |
| 5 | 2 nodes cho LB | BÀI HỌC QUAN TRỌNG |

## cap moi BCCS3_thị_trường_Lào 34221

**PYC:** (không thấy mã cụ thể) · **Thẩm định:** — · **Loại:** A · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | GoldenGate cần RAM lớn | BÀI HỌC QUAN TRỌNG |
| 2 | Kafka cluster | BÀI HỌC QUAN TRỌNG |
| 3 | Module vé sinh | BÀI HỌC QUAN TRỌNG |
| 4 | Thị trường mới Sản xuất hiện tại | BÀI HỌC QUAN TRỌNG |

## cap moi PNM 57012

**PYC:** PYC-57012 · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

| # | Vấn đề | Mục nguồn |
|---:|---|---|
| 1 | PNM system sizing best practices | TRI THỨC RÚT RA GOLDEN PATTERN |

## cap moi Backup tập trung cho VTT 29293

**PYC:** PYC-29293 · **Thẩm định:** — · **Loại:** A · **Số vòng:** 5

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## cap moi SmartHome 27860

**PYC:** PYC-13709 (Sao với cap moi Smarthome 13709) · **Thẩm định:** — · **Loại:** A · **Số vòng:** 3

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## cap moi tindy_khanhdn1

**PYC:** — · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## cap moi unify_anhdt156

**PYC:** — · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## cap moi vtracking

**PYC:** — · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## Nang_cap_he_thong_Roaming_1_0

**PYC:** — · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

## Nang_cap_smartmoto_nang_ram

**PYC:** — · **Thẩm định:** — · **Loại:** B · **Số vòng:** —

_Không trích được vấn đề nào — cấu trúc file khác, cần xem tay._

