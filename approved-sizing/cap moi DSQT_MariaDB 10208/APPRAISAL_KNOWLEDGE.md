# APPRAISAL KNOWLEDGE - DSQT MARIADB

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG DSQT (Định Cỡ Query Tool) với MariaDB  
**Mã PYC:** PYC-10208  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Thaolt34  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### Nhóm yêu cầu chỉnh sửa:

**NHÓM 1: CƠ BẢN VÀ MINH CHỨNG**

1. **Nhận xét chung:**
   - Bổ sung sởFFFF chỉ cho số liệu và tính toán lại
   - Đề xuất lưu ý giá trị N+1 cho backup
   - **QUAN TRỌNG:** Các ảnh chụp sởFFFF chỉ (cấu hình, tải) phải kèm thông tin IP máy chủ tương ứng
   - Bỏ phần tính toán switch, rack nếu không cần thiết

2. **Network và kết nối:**
   - Bổ sung tính thông lượng LB, FW
   - Bổ sung thông tin kết nối của hệ thống với các hệ thống khác

**NHÓM 2: THÔNG TIN HỆ THỐNG**

3. **Mục I - Cơ bản:**
   - Bổ sung mục đích sizing (định cỡ mới, nâng cấp, migration?)
   - Bổ sung mức độ quan trọng (Critical/Important/Normal)
   - Bổ sung sởFFFF chỉ cho các số liệu đầu vào và tải hệ thống

**NHÓM 3: DATABASE SIZING**

4. **Mục III - Định cỡ Database:**
   - **TPS = 42:** Bổ sung sởFFFF chỉ
   - Bổ sung ảnh chụp cấu hình server (CPU, RAM, HDD)
   - Bổ sung link tham chiếu CPU (SPEC benchmark)
   - Bổ sung sởFFFF chỉ RAM CPU sử dụng, HDD
   
5. **Storage calculation:**
   - **Dữ liệu 2020:** "Dung lượng lưu trữ lấy tại thời điểm 2020 là 1.05 GB/ngày tương ứng với TPS 425"
   - **Câu hỏi:** Tại sao dùng data 2020? Có còn valid không?
   - **24 months storage:** 1.05 * 30 * 24 = 757 GB
   - **Validation check:** Tại sao nhân 30 ngày, rồi nhân 24 tháng?
   - Cần làm rõ retention policy

6. **SSD vs HDD:**
   - **Không có quy định** MariaDB phải dùng SSD
   - **Yêu cầu:** Chứng minh bằng số IOPS cụ thể
   - Nếu IOPS cần thiết > HDD có thể cung cấp → dùng SSD
   - Nếu IOPS thấp → HDD is acceptable

7. **Backup separation:**
   - **Lỗi:** Backup đang bị tính lẫn vào dung lượng data
   - **Yêu cầu:** Tách riêng phần dung lượng Backup
   - Data storage ≠ Backup storage

**NHÓM 4: MIGRATION CONSIDERATION**

8. **Oracle → MariaDB migration:**
   - Nếu mục đích là cắt chuyển DB từ Oracle sang MariaDB
   - **Yêu cầu:** Lựa chọn hệ thống tham chiếu tương ứng
     - Option A: Dùng hệ thống đang chạy MariaDB làm reference
     - Option B: Dùng tải từ hệ thống test migration
   - KHÔNG ĐƯỢC dùng Oracle sizing cho MariaDB (khác nhau nhiều)

---

## 💡 TRI THỨC RÚT RA

### 1. Oracle vs MariaDB - NOT equivalent!

**Common mistake:** Assuming MariaDB needs same resources as Oracle

**Reality:**

| Aspect | Oracle | MariaDB |
|--------|--------|---------|
| Architecture | Enterprise features | Open source, simpler |
| Resource usage | Higher (~2-3x) | Lower |
| Memory management | Complex (SGA, PGA) | Simpler (buffer pool) |
| CPU efficiency | Lower | Higher |
| Storage overhead | Higher | Lower |

**Migration sizing approach:**

**WRONG:**
```
Oracle needs 100 GB RAM
→ MariaDB also needs 100 GB RAM ❌
```

**CORRECT:**
```
Option A - Benchmark approach:
1. Set up MariaDB test environment
2. Migrate sample data
3. Run actual workload
4. Measure resource usage
5. Size based on MariaDB performance

Option B - Reference system:
1. Find similar MariaDB system in production
2. Compare TPS, Data size, User count
3. Scale based on reference system resources
```

**Typical resource ratio:**
```
MariaDB_Resources ≈ Oracle_Resources × 0.5 to 0.7
```

### 2. IP addresses in screenshots - MANDATORY!

**Why important:**

**Problem scenario:**
```
Screenshot 1: CPU utilization 50%
Screenshot 2: RAM utilization 60%
Question: Which server? When? How to verify?
```

**Correct approach:**
```
Screenshot includes:
- IP: 10.60.105.79
- Hostname: db-server-01
- Timestamp: 2025-01-15 14:30:00
- Metrics: CPU 50%, RAM 60%
→ Result: Traceable and verifiable
```

**Best practice:**
1. Always include full hostname/IP in screenshot
2. Include timestamp
3. Include monitoring tool name (Nagios, Prometheus, etc.)
4. Show command used to get metrics

### 3. SSD vs HDD - IOPS is the decision factor

**Decision criteria:**

**Calculate required IOPS:**
```
Required_IOPS = (TPS × Random_IO_Per_Transaction) + (Background_Overhead)
```

**MariaDB typical IOPS:**
```
Read workload: 50-200 IOPS per MB/s
Write workload: 100-300 IOPS per MB/s
Mixed workload: 100-200 IOPS per MB/s
```

**Storage capabilities:**
```
HDD (7.2K RPM): 80-100 IOPS per disk
HDD (10K RPM): 130-150 IOPS per disk
SSD (SATA): 5,000-10,000 IOPS
SSD (NVMe): 100,000+ IOPS
```

**Decision tree:**
```
Required_IOPS < 500 → HDD is fine
Required_IOPS = 500-2,000 → HDD RAID or Entry SSD
Required_IOPS > 2,000 → SSD required
Required_IOPS > 10,000 → NVMe SSD required
```

**DSQT case:**
```
TPS = 42
Assume mix R/W: 50 R + 50 W per transaction
R_per_sec = 42 × 50 = 2,100 reads
W_per_sec = 42 × 50 = 2,100 writes
Required_IOPS ≈ 4,200 IOPS
→ SSD or high-end HDD RAID needed
→ Must calculate actual workload to decide
```

### 4. Backup storage - Separate from data!

**Current mistake (in DSQT):**
```
Total_Storage = Data + Backup (mixed together) ❌
```

**Correct approach:**
```
Component 1: Data Storage
  - Database files
  - Index files
  - Transaction logs
  - Calculation: Daily_Growth × Retention_Days

Component 2: Backup Storage
  - Full backups (weekly)
  - Incremental backups (daily)
  - Archive logs
  - Separate retention policy

Total_Storage = Data_Storage + Backup_Storage
```

**Example calculation:**
```
Data (2020): 1.05 GB/day
TPS (2020): 425

Current TPS: 42 (likely different from 2020!)
Growth_Rate: 1.05 GB / 425 TPS = 0.00247 GB/TPS

Data Storage (24 months):
  = TPS × 0.00247 × 30 days × 24 months
  = 42 × 0.00247 × 720
  = 74.7 GB

Backup Storage:
  - Weekly full backup: 75 GB × 4 = 300 GB
  - Daily incremental: 10 GB/day × 30 = 300 GB
  - Archive logs: 20 GB
  Total_Backup: 620 GB

Total: 74.7 + 620 = 694.7 GB
```

### 5. Using 2020 data - Validity check!

**Problem:** DSQT uses 2020 data point (TPS 425, 1.05 GB/day)

**Questions to ask:**

1. **Is current TPS still similar?**
   - If current TPS = 42 (very different from 425!)
   - Ratio: 42/425 = ~10% of 2020 traffic
   - 2020 data is NOT representative

2. **Have data patterns changed?**
   - Same query complexity?
   - Same user behavior?
   - Same business requirements?

3. **Is 5-year-old data still valid?**
   - Technology changes
   - Schema changes
   - Usage pattern changes

**Best practice:**
```
Current_Measurement:
  - Measure actual TPS from last 7 days
  - Measure actual storage growth from last 7 days
  - Calculate ratio: Storage_per_TPS = Current_Storage / Current_TPS

Projection:
  - Use current ratio to project future storage
  - Apply growth rate if expected to increase
```

### 6. N+1 for Database - Special consideration

**Database HA is different:**

**MariaDB replication models:**

**Model A: Master-Slave (Asynchronous)**
```
1 Master + N Slaves
N+1 = 1 master + 2 slaves (can survive 1 failure)
Recommended for: Read-heavy workloads
```

**Model B: Master-Master (Synchronous)**
```
N masters (usually 2-3)
Each can accept writes
N+1 = 3 masters (can survive 1 failure)
Recommended for: High availability, geo-redundancy
```

**Model C: Galera Cluster (Multi-master)**
```
Minimum 3 nodes, recommended 5
All nodes are equal (no master-slave)
N+1 = 4 or 6 nodes
Recommended for: Critical systems
```

**DSQT must specify:**
- Which HA model?
- RPO/RTO requirements?
- Can tolerate brief downtime for failover?

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Database (MariaDB):**
- TPS: 42 (current load)
- Storage: Needs recalculation with current data
- Storage type: HDD or SSD based on IOPS calculation
- HA strategy: N+1 (model TBD)

### Quy mô hệ thống
- DSQT (Query Tool) system
- Database backend: MariaDB
- Possible migration from Oracle (TO BE CONFIRMED)
- Criticality level: TO BE SPECIFIED

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. Oracle ≠ MariaDB for sizing
- Don't assume same resource requirements
- MariaDB typically needs 50-70% of Oracle resources
- Use MariaDB-specific benchmarks or migration testing

### 2. IP addresses in screenshots are MANDATORY
- Every screenshot must show IP/Hostname
- Include timestamp
- Make it traceable and verifiable

### 3. SSD vs HDD decision based on IOPS
- Calculate required IOPS from workload
- Compare with storage capabilities
- Don't just assume SSD is required

### 4. Separate backup from data storage
- Two different calculation methods
- Different retention policies
- Sum them for total storage

### 5. Old data (2020) may not be valid
- Check if current patterns similar to 2020
- Measure current actual usage
- Use current data for projection

### 6. Database HA needs model specification
- Master-Slave vs Master-Master vs Galera Cluster
- Each has different N+1 calculation
- Specify latency tolerance

### 7. Migration sizing requires testing
- Set up test environment
- Run actual workload
- Measure MariaDB-specific resource usage
- Don't extrapolate from other DBs

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (nhiều issue về methodology)  
**Vấn đề chính:** Dùng dữ liệu cũ (2020), thiếu IOPS calculation, MariaDB vs Oracle confusion

**Đặc điểm hệ thống:**
- DSQT (Query Tool) system
- Database backend: MariaDB
- Possible migration from Oracle (chưa xác định)
- Low TPS (42) nhưng cần verify accuracy

**Khuyến nghị:**
- Confirm if migrating from Oracle or new deployment
- Use MariaDB-specific sizing (not Oracle)
- Measure current TPS and storage growth
- Calculate IOPS requirement for SSD vs HDD decision
- Separate backup storage calculation from data storage
- Specify MariaDB HA model (Master-Slave, Master-Master, Galera)
- Include IP addresses in all screenshots
- Provide CPU SPEC benchmark reference
- Define criticality level and RPO/RTO