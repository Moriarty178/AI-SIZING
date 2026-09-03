# APPRAISAL KNOWLEDGE - DATA SECURITY VTT

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG DATA SECURITY VTT  
**Mã PYC:** PYC-18476  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Cuongnx8  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### 7 Nhóm yêu cầu chỉnh sửa:

**NHÓM 1: CƠ BẢN**

1. **Nhận xét chung:**
   - Bổ sung sởFFFF chỉ cho mọi số liệu
   - Tính toán lại số liệu
   - Lập bảng giá trị đề xuất số lượng máy chủ cụ thể theo mô hình của Viettel
   - Lưu ý giá trị N+1
   - Bổ sung thông tin kết nối, LB/FW

**NHÓM 2: MỤC ĐÍCH VÀ NGUYÊN TẮC**

2. **Mục I - Thông tin hệ thống:**
   - Bổ sung mục đích sizing (cấp mới, bổ sung, thay đổi?)
   - Bổ sung nguyên tắc định cỡ (baseline calculation, KPI targets)

**NHÓM 3: INPUT DATA VÀ CPU**

3. **Trang 2 - Input data:**
   - Bổ sung sởFFFF chỉ cho các số liệu thông tin đầu vào
   - Bổ sung sởFFFF chỉ cho thông tin CPU, RAM, link tham chiếu CPU
   - Bổ sung sởFFFF chỉ cho "Thông tin tài nguyên khởi tạo"
   - Bổ sung sởFFFF chỉ cho kết quả đo CPU

4. **Trang 3 - CPU sizing:**
   - Bổ sung sởFFFF chỉ cho số liệu trong bảng định cỡ CPU
   - **Ghi rõ công thức tính** để dễ đối soát (đang để mỗi kết quả)
   - **Lỗi logic:** "Dự phòng theo KPI 75% sao lại là 8000?"
     - Nếu KPI 75%, có nghĩa là CPU chạy ở 75% capacity
     - Tại sao con số 8000 xuất hiện? Không rõ ràng

**NHÓM 4: RAM**

5. **RAM sizing:**
   - Bổ sung sởFFFF chỉ cho kết quả đo RAM
   - Ghi rõ công thức tính để dễ đối soát

6. **Trang 4 - RAM sizing:**
   - Bổ sung sởFFFF chỉ cho số liệu trong bảng định cỡ RAM
   - Ghi rõ công thức tính (đang để mỗi kết quả)

**NHÓM 5: STORAGE VÀ BACKUP**

7. **Thiết bị lưu trữ:**
   - Bổ sung sởFFFF chỉ cho số liệu, tính toán lại
   - **Mô tả rõ:**
     - Tính năng backup 2 bản là gì?
     - Dữ liệu này thuộc loại nào (critical, important, normal?)
     - Lưu bao lâu theo quy định (QĐ)?
     - Trích dẫn QĐ về retention policy

---

## 💡 TRI THỨC RÚT RA

### 1. Show your work - FORMULA IS MANDATORY

**Vấn đề:** Document chỉ có kết quả, không có công thức

**SAI:**
```
CPU cần: 8000
RAM cần: 192 GB
Storage cần: 2 TB
```

**ĐÚNG:**
```
Step 1: Measure current usage
  - Current TPS: 10,000
  - CPU used: 6,000 Cint

Step 2: Calculate per-unit
  - CPU_per_TPS = 6,000 / 10,000 = 0.6 Cint/TPS

Step 3: Scale to target
  - Target TPS: 50,000
  - CPU_needed = 0.6 × 50,000 = 30,000 Cint

Step 4: Apply KPI and safety
  - KPI: 75% usage
  - Safety: 1.1
  - Total = 30,000 × 1.1 / 0.75 = 44,000 Cint

Step 5: Distribute to servers
  - Per_server = 44,000 / N (where N = number of servers)
```

**Lợi ích:**
- Dễ đối soát (traceable)
- Dễ debug nếu có lỗi
- Dễ explain với reviewer

### 2. KPI 75% - Don't misuse it!

**Hiểu sai thường gặp:**

**SAI:** "CPU needed = 8000 (theo KPI 75%)"
- Điều này không có nghĩa
- KPI 75% là target, không phải input

**ĐÚNG:**
```
Target_CPU_Usage = 75% of Total_CPU
Required_CPU = Calculated_Needs / 0.75
```

**Ví dụ đúng:**
```
Calculation:
  - CPU cần cho workload: 6,000 Cint
  - Muốn CPU chạy ở 75% capacity
  - Total_CPU = 6,000 / 0.75 = 8,000 Cint
```

**Bài học:**
- KPI là CONSTRAINT, không phải INPUT
- Document must show: workload → / KPI → result
- Don't magically jump to "8000"

### 3. Backup 2 copies - Context matters

**Viettel Data Security backup policy:**

**Question:** Why 2 copies?

**Factors to consider:**

**Factor 1: Data classification**
- **Critical data:** 3+ copies (production + 2+ backups)
- **Important data:** 2 copies (production + 1 backup)
- **Normal data:** 1 copy (production only)

**Factor 2: RPO/RTO requirements**
- **RPO (Recovery Point Objective):** Max data loss allowed
- **RTO (Recovery Time Objective):** Max downtime allowed
- Critical systems: RPO < 5min, RTO < 15min
- Normal systems: RPO < 1hr, RTO < 4hrs

**Factor 3: Regulatory compliance**
- QĐ 4137/QĐ-CNVTQĐ-CNTT: retention policy
- State Bank regulations (if applicable)
- Data protection law compliance

**Document must specify:**
```
Data Type: [Critical/Important/Normal]
RPO: [minutes/hours]
RTO: [minutes/hours]
Retention: [days/years] per QD XXXXX
Backup copies: N
Reason: [High availability / Fault tolerance / Compliance]
```

### 4. System-specific sizing: Data Security

**Data Security systems have special requirements:**

**Factor 1: Performance vs Security trade-off**
- Encryption/decryption overhead
- SSL/TLS termination
- Authentication processing
- **Impact:** May need 20-30% more resources than non-security systems

**Factor 2: Compliance requirements**
- Audit logging (all transactions)
- Data retention policies
- Immutable logs (tamper-proof)
- **Impact:** Storage calculation must include audit logs

**Factor 3: High availability**
- Security systems cannot go down
- Need geo-redundancy for critical components
- **Impact:** N+1 is minimum, N+M for critical

**Sizing formula for data security:**
```
Base_Resources = Calculate_like_normal_system
Security_Overhead = × 1.3 (for encryption, auth)
HA_Factor = × 2 (for N+1 redundancy)
Total = Base × Security_Overhead × HA_Factor
```

### 5. Reference links for CPU specs

**Why important:**
- Reviewer needs to verify CPU calculations
- Different CPU models have different Cint values
- Must use SPEC CPU benchmark data

**Where to find:**
- https://www.spec.org/cpu2017/results/
- Vendor website (Intel, AMD)
- Performance papers

**Document must include:**
```
CPU Model: Intel Xeon E5-2670 v3
SPEC Cint2017: 115.75 (base)
Link: https://www.spec.org/cpu2017/results/res2019q1/...
Date accessed: [date]
```

### 6. N+1 following Viettel model

**Viettel standard HA model:**

**Stateless services (APP, Worker):**
```
N = Calculated_servers
Total = N + 1 (1 standby for any failure)
Example: Need 5 servers → Deploy 6 servers
```

**Stateful services (Database):**
```
Minimum: 3 nodes (1 master + 2 replicas)
N+1: 3 + 1 = 4 nodes
Example: PostgreSQL cluster
```

**Leader-based systems (Kafka, Redis Cluster):**
```
Follow technology minimum
Kafka: 3 brokers minimum, 5 recommended
Redis Cluster: 6 nodes (3 masters × 2 replicas)
```

**Viettel preference:**
- Small systems: N+1 is sufficient
- Medium systems: N+2 for critical modules
- Large systems: N+3 for core components

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Data Security System components:**
- [CPU specs based on calculation]
- [RAM based on measurement]
- [Storage with 2-copy backup policy]

### Quy mô hệ thống
- Security system for Viettel Telecom (VTT)
- Compliance with retention policies
- High availability requirements

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. FORMULA IS NOT OPTIONAL
- Don't just show results
- Show step-by-step calculation
- Include all intermediate values
- Make it traceable

### 2. KPI is a constraint, not input
- KPI 75% means "use up to 75% capacity"
- Formula: Required = Workload / 0.75
- Don't magically arrive at numbers

### 3. Backup policy needs context
- Data type (Critical/Important/Normal)
- RPO/RTO requirements
- Regulatory compliance (QD reference)
- Why 2 copies? Why not 3?

### 4. Security systems need overhead
- Encryption/decryption costs CPU
- Audit logging needs storage
- HA requirements are higher
- Add 20-30% overhead

### 5. Reference links are mandatory
- SPEC CPU benchmark data
- Vendor specifications
- Access date
- Make it verifiable

### 6. Follow Viettel HA model
- Stateless: N+1
- Stateful: ≥3 nodes
- Leader-based: Follow technology minimum
- Document your choice

### 7. Table format for server count
```
Module | Base (N) | Backup (+1) | Total | Notes
APP    | 5       | +1         | 6     | N+1 HA
DB     | 2       | +1         | 3     | Quorum
```

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (thiếu nhiều minh chứng)  
**Vấn đề chính:** Thiếu công thức tính toán, KPI bị hiểu sai, backup policy không rõ

**Đặc điểm hệ thống:**
- Data Security system cho Viettel Telecom
- Cần compliance với quy định retention
- High availability requirements
- Backup policy: 2 copies

**Khuyến nghị:**
- Show full calculation formulas
- Clarify KPI usage (constraint, not input)
- Document backup policy with data classification
- Reference regulatory QĐ for retention
- Add security overhead (~20-30%)
- Include SPEC CPU benchmark links
- Follow Viettel N+1 model
- Create clear server count table