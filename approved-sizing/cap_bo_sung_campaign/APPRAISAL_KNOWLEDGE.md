# APPRAISAL KNOWLEDGE - DỰ ÁN: CẤP BỔ SUNG CAMPAIGN 2.0

**Mã PYC:** PYC-8964  
**Đầu mối yêu cầu:** Giangnt109  
**Đầu mối thẩm định:** Khanhnd23 (Phòng Hệ thống)  
**Mục đích sizing:** Cắt chuyển thay thế tài nguyên cụm Hadoop IDC, Kafka IDC và tài nguyên Datalake của hệ thống Campaign  
**Ngày hoàn thành:** 2024

---

## 📅 LỊCH SỬ TRAO ĐỔI

### Vòng 1 (V1 → V2) - Nhận xét lần 1
**File tương ứng:** PNX_CAMPAIGN_MANAGEMENT.pdf ↔ Định cỡ hệ thống Campaign 2.0 bổ sung.docx

**Các vấn đề chính được đề xuất:**
- Thiếu thông tin CPU trong sizing
- Chưa có sở cứ cho mức tăng trưởng 20%
- Chưa lấy tải thực tế để tính thông số CPU, RAM
- Chưa có sở cứ sử dụng SSD thay HDD
- Chưa tính toán thông lượng Firewall, Load Balancer
- Chưa trình bày rõ phương án thay cụm tài nguyên IDC, Datalake (toàn bộ hay 1 phần)
- Chưa áp dụng đúng các KPI khi tính toán CPU, RAM, Disk
- Chưa giải thích tại sao chỉ lưu 8TB/server
- Chưa bổ sung sở cứ cho con số 256GB RAM ở Hadoop, Kafka, Datalake

### Vòng 2 (V2 → V3) - Nhận xét lần 2
**File tương ứng:** PNX_CAMPAIGN_MANAGEMENT_v2.pdf ↔ Định cỡ hệ thống Campaign 2.0 bổ sung_v2.docx

**Các vấn đề chính được đề xuất:**
- **Công thức tính sai:** Chưa áp dụng đúng KPI CPU 75%, RAM 90%, Disk 80%
- **Số liệu CPU không rõ ràng:** 684.2 Cint 2017 cần làm rõ nguồn gốc
- **Thiếu link SPEC CPU 2017:** Cần tham chiếu chuẩn cho CPU
- **Dung lượng log/file cài đặt:** 3TB trong 6 tháng - cần bổ sung sở cứ
- **Chưa áp dụng mô hình N+1:** Thêm 1 server dự phòng cho các cụm
- **Lỗi tính toán:** 129 + 25 = 154 TB (không phải 151 TB)
- **Lỗi đơn vị đổi:** Chia 1024 chứ không phải 1000 khi đổi GB → TB
- **Dữ liệu Firewall sai:** Tính cho 6 tháng, không nhân 3 khi chưa có replicate

### Vòng 3 (V3) - Bản chốt
**File tương ứng:** PNX_CAMPAIGN_MANAGEMENT_v3.docx ↔ Định cỡ hệ thống Campaign 2.0 bổ sungv3.docx

**Kết quả:** Được thẩm định và phê duyệt ✅

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH (CRITICAL INSIGHTS)

### 1. YÊU CẦU BỔ SUNG SỞ CỨ TĂNG TRƯỞNG
- **Vấn đề:** V1 sử dụng mức tăng trưởng 20% nhưng không có sở cứ
- **Giải pháp:** V3 tính toán chính xác từ số liệu thực tế:
  - Số chương trình tạo mới năm 2023: 11,309
  - Số chương trình trước năm 2023: 58,260
  - Mức tăng trưởng: 11,309/58,260 × 100 = **19.42%/năm**
- **Bài học:** Luôn phải có số liệu thực tế để chứng minh mức tăng trưởng

### 2. THIẾU THÔNG TIN CPU
- **Vấn đề:** V1 hoàn toàn không có thông tin CPU
- **Giải pháp:** V3 đo tải thực tế và chuyển đổi sang Cint 2017
  - Server tham chiếu: Intel Xeon Silver 4110 @ 2.10GHz
  - Link SPEC: https://www.spec.org/cpu2017/results/res2017q4/cpu2017-20171127-00913.html
  - Tải CPU thực tế: 53.8% → 39.06 Cint 2017/server
- **Bài học:** CPU là thông tin BẮT BUỘC, phải đo tải thực tế và có link SPEC

### 3. SỞ CỨ SỬ DỤNG SSD
- **Vấn đề:** V1 dùng ổ cứng thông thường, không giải thích
- **Giải pháp:** V3 giải thích rõ:
  - SSD cần thiết để xử lý Campaign Online (xử lý real-time)
  - Hệ thống hiện tại đang sử dụng SSD
  - IOPS đo được: 212.73 → cần ổ cứng > 15K rpm
- **Bài học:** BigData/Real-time system CẦN SSD, phải giải thích rõ lý do

### 4. CÔNG THỨC TÍNH TOÁN SAI
- **Vấn đề V1-V2:** Đúng KPI nhưng công thức không rõ ràng
- **Giải pháp V3:** Áp dụng đúng công thức chuẩn
  ```
  CPU cần = CPU hiện tại / 0.75 × 1.1 × (1 + 19.42%)
  RAM cần = RAM hiện tại / 0.90 × 1.1 × (1 + 19.42%)
  Disk cần = Disk hiện tại / 0.80 × 1.1 × (1 + 19.42%)
  
  Trong đó:
  - KPI CPU: ≤ 75%
  - KPI RAM: ≤ 90%
  - KPI Disk: ≤ 80%
  - Hệ số dự phòng sai số: 1.1
  - Mức tăng trưởng: 19.42%/năm
  ```
- **Bài học:** Luôn HIỂN THỊ công thức tính toán rõ ràng

### 5. MÔ HÌNH N+1 (REDUNDANCY)
- **Vấn đề:** V1, V2 không đề cập đến đảm bảo dự phòng
- **Giải pháp V3:** Áp dụng N+1
  - Hadoop: 18 + 1 = **19 servers**
  - Kafka: 5 + 1 = **6 servers** (N+1)
- **Lý do Kafka là 5:**
  - Kafka cần số lẻ > 3 để election với Zookeeper
  - Cụm Kafka cài cùng Zookeeper nên cần instances lẻ
- **Bài học:** BigData cluster LUÔN cần N+1 cho HA

### 6. ĐƠN VỊ TÍNH TOÁN (SAI)
- **Vấn đề:** V2 tính 129 + 25 = 151 TB (sai!)
- **Giải pháp V3:** 129 + 25 = **154 TB** (đúng)
- **Vấn đề:** Đổi GB → TB chia 1000 (sai!)
- **Giải pháp V3:** Phải chia **1024** (chuẩn tính toán)
- **Bài học:** KIỂM TRA LẠI các phép tính đơn giản, đơn vị chuẩn

### 7. DỮ LIỆU FIREWALL (KHÔNG NHÂN 3)
- **Vấn đề V2:** Tổng dung lượng = 151.4TB/365 rồi nhân 3 (sai!)
- **Lý do sai:** Dữ liệu "chưa có replicate" KHÔNG ĐƯỢC nhân 3
- **Giải pháp V3:** 
  - Tính cho 6 tháng: 284.03TB / 180 ngày = 1.58TB/ngày
  - Chuyển đổi sang GB: 1.58 × 1024 = 1618.54GB
  - Trong khung giờ 0-5h: 1618.54 × 1024 / (5×60×60) = 93.15 MB/s
  - Sau khi nhân hệ số: **402 Mbps** (2 chiều)
- **Bài học:** HIỂU RÕ nghĩa của dữ liệu (replicate vs non-replicate)

---

## 📐 CÔNG THỨC ÁP DỤNG CHO HỆ THỐNG CAMPAIGN

### Công thức tính toán tài nguyên

```
CPU cần = CPU hiện tại / 0.75 × 1.1 × (1 + 19.42%)
RAM cần = RAM hiện tại / 0.90 × 1.1 × (1 + 19.42%)
Disk cần = Disk hiện tại / 0.80 × 1.1 × (1 + 19.42%)
```

**Tham số:**
- **KPI CPU:** ≤ 75% (để room cho traffic spike)
- **KPI RAM:** ≤ 90% (để room cho memory overhead)
- **KPI Disk:** ≤ 80% (để room cho log, temp files)
- **Hệ số dự phòng sai số:** 1.1 (10% margin cho sự inaccuracies in calculation)
- **Mức tăng trưởng:** 19.42%/năm (tính từ số liệu thực tế 2023)

### Cách tính toán số server (Mô hình N)

**Bước 1:** Tính tổng tài nguyên cần thiết
**Bước 2:** Chia cho tài nguyên mỗi server
**Bước 3:** Làm tròn lên → Được số N
**Bước 4:** Áp dụng N+1 → Thêm 1 server dự phòng

**Ví dụ Hadoop:**
- Cần: 25.92 TB/server
- Tổng cần: 466.39 TB
- N = 466.39 / 25.92 = 18 servers
- N+1 = 18 + 1 = **19 servers**

### Chuyển đổi đơn vị QUAN TRỌNG

```
1 TB = 1024 GB (KHÔNG PHẢI 1000 GB)
1 GB = 1024 MB
```

---

## 📊 THÔNG SỐ CUỐI CÙNG ĐƯỢC DUYỆT (BẢN V3)

### 1. Cụm Hadoop Campaign

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | ≥ 59.85 Cint 2017 | Intel Xeon Silver 4110 @ 2.10GHz |
| **RAM** | ≥ 256 GB | Per server |
| **Disk** | ≥ 25.92 TB | SSD (>15K rpm) |
| **Số lượng** | **19 servers** | Mô hình N+1 (18 + 1) |
| **Tổng RAM** | 4,432.8 GB | 19 × 256 GB |
| **Tổng Disk** | 466.39 TB | 19 × 25.92 TB |
| **Tổng CPU** | 1,077.24 Cint 2017 | 19 × 59.85 |

**Lý do N+1:**
- Đảm bảo High Availability (HA)
- 1 server chết không ảnh hưởng hệ thống
- Cluster có thể maintenance mà không downtime

### 2. Cụm Kafka Campaign

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | ≥ 104.84 Cint 2017 | Intel Xeon Silver 4110 @ 2.10GHz |
| **RAM** | ≥ 256 GB | Per server |
| **Disk** | ≥ 6,991.7 GB (~6.8 TB) | Per server |
| **Số lượng** | **6 servers** | Mô hình N+1 (5 + 1) |
| **Tổng RAM** | 1,176.13 GB | 6 × 256 GB |
| **Tổng Disk** | 34,958.72 GB (~34.2 TB) | 6 × 6,991.7 GB |
| **Tổng CPU** | 524.19 Cint 2017 | 6 × 104.84 |

**Lý do 5 instances:**
- Kafka cần số lẻ > 3 để election với Zookeeper
- Cụm Kafka cài cùng Zookeeper
- Zookeeper yêu cầu số lẻ để consensus (quorum)
- 5 instances tối ưu cho performance + HA

**Dữ liệu Kafka:**
- Bản ghi/ngày: 676,552,571 records
- Dung lượng/bản ghi: 2 KB
- Tổng/ngày: 1,290 GB
- Retention: 7 ngày
- Replication factor: 3
- Tổng cần: 1,290 × 7 × 3 = 20,790 GB + 500 GB (log) = 21,290 GB

### 3. Network Infrastructure

#### Switch 10Gbps
| Thông số | Giá trị |
|----------|---------|
| **Số lượng** | **4 units** |
| **Port type** | 48 port 10Gbps |
| **Switching capacity** | ≥ 213 Gbps |
| **Layer** | Layer 3 |
| **Features** | VRF support, ≥2 power supplies |
| **Mô hình** | 1+1 redundancy (2 active + 2 standby) |

**Tính toán:**
- Server Hadoop: 18 × 1 = 18 ports
- Server Kafka: 6 × 1 = 6 ports
- Firewall: 1 port
- Management: 1 port/switch × 2 = 2 ports
- **Tổng cần:** 27 ports
- **HSDP (20% buffer):** 27 × 1.2 = 33 ports
- **Sử dụng:** 48 port switch
- **Redundancy:** 2 switches active (96 ports total)

#### Switch 1Gbps
| Thông số | Giá trị |
|----------|---------|
| **Số lượng** | **2 units** |
| **Port type** | 48 port 1Gbps |
| **Features** | Layer 3, 48 Gbps throughput, ≥2 power supplies |
| **Mô hình** | 1+1 redundancy |

**Tính toán:**
- Server Hadoop (management): 18 ports
- Server Kafka (management): 6 ports
- **Tổng cần:** 24 ports
- **Sử dụng:** 48 port switch
- **Redundancy:** 1+1 (2 switches active-active)

#### Firewall
| Thông số | Giá trị |
|----------|---------|
| **Băng thông** | **≥ 402 Mbps** (2 chiều) |
| **Tích hợp** | Vào VTNet FW hiện có |

**Tính toán:**
- Dữ liệu đồng bộ/ngày: 64.55 TB / 180 ngày = 367.22 GB
- Khung giờ xử lý: 0h - 5h (5 tiếng)
- Throughput cần: 367.22 × 1024 / (5 × 60 × 60) = 20.9 MB/s
- Hệ số dự phòng (Kdup = 1.2): 20.9 × 8 × 1.2 = 201 Mbps
- 2 chiều: 201 × 2 = **402 Mbps**

---

## 🔍 SO SÁNH THAY ĐỔI GIỮA CÁC BẢN

### Hadoop Cluster

| Thông số | V1 (Bản đầu) | V3 (Bản chốt) | Thay đổi |
|----------|--------------|---------------|----------|
| Số server | 16 | **19** | +3 (N+1) |
| CPU info | ❌ Không có | ✅ Intel Xeon + Link SPEC | Thêm |
| CPU/server | ❌ Không có | ✅ 59.85 Cint 2017 | Thêm |
| RAM/server | ✅ 256 GB | ✅ 256 GB | Giữ nguyên |
| Disk/server | 8 TB | **25.92 TB** | +224% |
| Disk type | SSD | **SSD (>15K rpm)** | Rõ hơn |
| Tổng disk | 128 TB | **466.39 TB** | +264% |

**Lý do thay đổi:**
- Thêm N+1: 16 → 19 servers
- Tính lại disk dựa trên dữ liệu IDC + Datalake thực tế
- Bổ sung CPU, link SPEC, IOPS

### Kafka Cluster

| Thông số | V1 (Bản đầu) | V3 (Bản chốt) | Thay đổi |
|----------|--------------|---------------|----------|
| Số server | 5 | **6** | +1 (N+1) |
| CPU info | ❌ Không có | ✅ Intel Xeon + Link SPEC | Thêm |
| CPU/server | ❌ Không có | ✅ 104.84 Cint 2017 | Thêm |
| RAM/server | ✅ 256 GB | ✅ 256 GB | Giữ nguyên |
| Disk/server | 6,387 GB | **6,991.7 GB** | +9.5% |
| Tổng disk | 31,935 GB | **34,959 GB** | +9.5% |

**Lý do thay đổi:**
- Thêm N+1: 5 → 6 servers
- Tính lại dựa trên công thức chuẩn với KPI 80%, hệ số 1.1
- Bổ sung CPU, link SPEC

### Mức tăng trưởng

| Thông số | V1 (Bản đầu) | V3 (Bản chốt) | Thay đổi |
|----------|--------------|---------------|----------|
| Mức tăng trưởng | 20% (không có sở cứ) | **19.42%** (có số liệu) | Chính xác hơn |

**Số liệu thực tế:**
- Chương trình mới (2023): 11,309
- Chương trình cũ (trước 2023): 58,260
- Tăng trưởng: 11,309/58,260 × 100 = 19.42%

---

## 📋 CHECKLIST THẨM ĐỊNH SIZING CHO BIGDATA SYSTEM

Dựa trên bài học từ dự án Campaign 2.0, đây là checklist cho các sizing BigData tương lai:

### ✅ YÊU CẦU BẮT BUỘC

#### 1. Thông tin hệ thống
- [ ] Mô tả rõ mục đích sizing (cấp mới, nâng cấp, thay thế)
- [ ] Định cỡ dựa trên hệ thống tham chiếu nào
- [ ] Nguyên tắc định cỡ (KPI CPU, RAM, Disk)
- [ ] Mức độ quan trọng của hệ thống

#### 2. Số liệu đầu vào
- [ ] ĐO TẢI THỰC TẾ từ hệ thống đang chạy
- [ ] CPU utilization, RAM usage, Disk usage
- [ ] Link SPEC CPU (CPU 2006 hoặc CPU 2017)
- [ ] Dung lượng dữ liệu hiện tại
- [ ] Mức tăng trưởng (CÓ SỐ LIỆU CHỨNG MINH)

#### 3. Công thức tính toán
- [ ] HIỂN THỊ công thức rõ ràng (như mẫu trên)
- [ ] Giải thích từng tham số (KPI, hệ số, mức tăng trưởng)
- [ ] Tính toán từng bước (current → after KPI → after margin → after growth)

#### 4. Cấu hình chi tiết
- [ ] CPU: Model + Cint score + Link SPEC
- [ ] RAM: Số lượng GB per server
- [ ] Disk: Type (SSD/HDD), Speed (RPM), Capacity per server
- [ ] Network: Bandwidth, throughput, latency requirements
- [ ] IOPS: Minimum IOPS (nếu BigData/DB)

#### 5. Mô hình triển khai
- [ ] N+1 cho HA (High Availability)
- [ ] Số lượng replicas/replication factor
- [ ] Active-active hay Active-standby
- [ ] Đảm bảo không Single Point of Failure (SPOF)

#### 6. Tính toán mạng
- [ ] Firewall throughput (1 chiều vs 2 chiều)
- [ ] Switch capacity (1G vs 10Gbps)
- [ ] Số port cần dùng + buffer (20%)
- [ ] Redundancy cho network devices

#### 7. Rõ ràng về đơn vị
- [ ] 1 TB = 1024 GB (KHÔNG PHẢI 1000)
- [ ] KIỂM TRA LẠI các phép tính đơn giản
- [ ] Cross-check tổng = sum các phần

#### 8. Sở cứ cho quyết định
- [ ] Tại sao 256GB RAM? ( Không ngẫu nhiên!)
- [ ] Tại sao SSD thay HDD? (Performance requirement!)
- [ ] Tại sao số server là số lẻ/chẵn? (Cluster architecture!)
- [ ] Tại sao retention 7 ngày? (Business requirement!)

---

## 🎯 ĐIỂM CHÌA KHÓA CỦA DỰ ÁN NÀY

1. **Kỹ thuật đo tải chính xác:** Đo CPU, RAM, Disk từ server đang chạy
2. **Chuyển đổi sang Cint 2017:** Đảm bảo so sánh "táo với táo"
3. **Số liệu thực tế cho tăng trưởng:** Lấy từ business metrics (số campaign mới/cũ)
4. **Công thức chuẩn hóa:** Áp dụng KPI, hệ số margin đúng theo guideline
5. **Mô hình N+1:** Luôn có 1 server dự phòng cho HA
6. **Đơn vị chuẩn:** 1 TB = 1024 GB (not 1000!)
7. **Network redundancy:** Switch, FW đều có backup 1+1

---

## 📚 TÀI LIỆU THAM KHẢO

- **SPEC CPU 2017:** https://www.spec.org/cpu2017/results/
- **Hadoop Hardware Guide:** https://subscription.packtpub.com/book/cloud-and-networking/9781783281718/1/ch01lvl1sec08/choosing-hadoop-cluster-hardware
- **Kafka Deployment:** https://docs.confluent.io/platform/current/kafka/deployment.html#network
- **Guideline Sizing:** Xem trong thư mục `guideline_sizing/`

---

**Người tạo tài liệu:** AI Assistant (dựa trên tài liệu sizing Campaign 2.0)  
**Ngày tạo:** 2024  
**Phiên bản:** 1.0  
**Trạng thái:** ✅ Hoàn thành - Dùng cho reference cho các dự án BigData tương tự

---

## 📝 GHI CHÚ

- Tài liệu này tổng hợp tri thức thẩm định từ 3 vòng điều chỉnh
- Mục đích: Học hỏi và áp dụng cho các dự án sizing tương tự
- Đặc biệt: Dành cho BigData systems (Hadoop, Kafka, Spark, etc.)
- Cần tuân thủ guideline sizing của Viettel (xem trong thư mục guideline_sizing/)