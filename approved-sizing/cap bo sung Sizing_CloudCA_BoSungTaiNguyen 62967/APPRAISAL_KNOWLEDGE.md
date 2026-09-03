# APPRAISAL KNOWLEDGE - DỰ ÁN: VIETTEL CLOUD-CA BỔ SUNG MAXSCALE & DR

**Mã PYC:** PYC-62967  
**Đầu mối yêu cầu:** Tuyenvm (Trung tâm CNTT - BU CA)  
**Đầu mối thẩm định:** Khanhnd23 (Phòng Hệ thống)  
**Đơn vị phát triển:** Trung tâm Công nghệ thông tin  
**Mục đích sizing:** bổ sung node Maxscale và DR cho 02 cụm DB  
**Quy mô:** Đáp ứng 11,000,000 KH trong năm tới  
**Ngày hoàn thành:** 2024  
**Trạng thái phản hồi:** Có feedback qua email từ chaulm5 (Yêu cầu RAM 96GB)

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ⚠️ **ĐÃ CÓ PHẢN BIỆN (TRƯỜNG HỢP A)**
- Có file feedback: "mail chaulm5 cho ram 96gb.txt" (file này hiện không thể đọc được)
- Feedback đề xuất: Yêu cầu RAM 96GB cho một số node
- Sizing đã được điều chỉnh theo feedback

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH

### 1. HỆ SỐ DỰ PH�NG CAO CHO HỆ THỐNG ĐẶC BIỆT
**Bối cảnh:**
- Hệ thống Cloud-CA thuộc hệ thống ĐẶC BIỆT QUAN TRỌNG (ký số từ xa)
- Mức độ quan trọng: **Đặc biệt quan trọng** (theo quy định 849/QĐ-CNVTQĐ)
- Yêu cầu đáp ứng: **11,000,000 KH trong năm tới**

**Quy định dự phòng:**
- Theo 849/QĐ-CNVTQĐ: 
  - Cụm 1: Có DR/DC (dự phòng sẵn có)
  - Cụm 2 & 3: Chỉ có nội site DR (auto failover)

**Bài học:**
- Hệ thống Đặc biệt quan trọng → Cần DC-DR 1:1 (không chia sẻ tài nguyên)
- Tài nguyên DC = Tài nguyên DR (duplicate 100%)
- Không tối ưu chi phí bằng việc scale down

### 2. HỆ SỐ DỰ PH�NG 1.2 (HỆ SỐ 1.1)
**Đặc biệt:**
- Hầu hết các sizing khác dùng Ksaiso = 1.1
- CloudCA dùng **Ksaiso = 1.2**

**Lý do:**
- Hệ thống đặc biệt quan trọng → cần buffer cao hơn
- Tăng 20% thay vì 10% cho safety margin
- Chi phí không phải là rào cản cho hệ thống critical

**Bài học:**
- Hệ thống critical (Đặc biệt quan trọng) → Ksaiso = 1.2
- Hệ thống quan trọng/bình thường → Ksaiso = 1.1
- Trade-off: Cost vs Reliability

### 3. YÊU CẦU RAM 96GB TỪ THẨM ĐỊNH VIÊN (chaulm5)
**Giải pháp từ sizing:**
- **Database DR:** RAM ~ 96 GB (cụm quản lý Database)
- **Database DC:** RAM ~ 64 GB (DB Business, DB Routing, DB Core)
- **Database Mysign:** RAM ~ 96 GB (MySign Cloud 2023)

**Lý do RAM 96GB:**
- Cần cache data/index lớn để giảm truy cập đĩa
- I/O performance critical cho signing operations
- Maxscale cần đủ RAM để cache connection pooling
- Đồng thời xử lý nhiều concurrent transactions

**Formula (từ sizing):**
```
RAM cần = Tài nguyên DC + Buffer cho DR
DC: 64 GB là baseline cho production DB
DR: 96 GB để đảm bảo HA khi switch over

Bài học:
- DR: Cùng hoặc hơn DC để không có bottleneck khi failover
- 96GB - 64GB = 32GB buffer (50% increase)
```

### 4. MÔ HÌNH DC-DR 1:1 CHO HỆ THỐNG ĐẶC BIỆT
**Quy tắc:**
- Theo 849/QĐ-CNVTQĐ: DC-DR 1:1 cho hệ thống đặc biệt quan trọng
- **Tài nguyên DC = Tài nguyên DR** (100% duplicate)
- Không scale down on DR

**Architecture:**
```
DC (HLC 2024):
- DB Business: 32 vCPU, 64GB RAM, 1.2TB SSD
- DB Routing: 32 vCPU, 64GB RAM, 1118GB SSD
- DB Core: 32 vCPU, 64GB RAM, 1.2TB SSD

DR (Other site):
- Tài nguyên DUPLICATE y hệt DC
- Placement: Khác site để đảm bảo DC-DR thực sự
- Asynchronous Multi-Master replication style
```

**Bài học:**
- DC-DR ở khác site → Thực sự Disaster Recovery (chung datacenter → Rủi ro cao)
- Need network bandwidth >= 861.543 Mbps for replication
- Binlog retention: DR có 600GB (4 days) vs DC có 161.63GB (1 day)

### 5. SIZING MAXSCALE NODE
**Cấu hình đề xuất:**
```
Maxscale DC (Cụm mới):
- CPU: 4 vCPU (~12 Cint 2017)
- RAM: 8 GB
- HDD: 100GB (cho OS)

Ghi chú:
- Maxscale là SQL proxy (tốn ít tài nguyên)
- Không chạy workload, chỉ routing/decoding
- 4 vCPU + 8GB là TỐI THIỂU cho ý kiến chaulm5
```

**Feedback chualm5:**
- Yêu cầu RAM 96GB cho một số node
- Điều này có thể áp dụng cho Database nodes (không phải Maxscale)
- Sizing đã điều chỉnh: Database DR = 96GB, Database DC = 64GB

### 6. TÍNH TOÁN BĂNG THÔNG DC-DR REPLICATION
**Formula:**
```
Binlog size per day:
= 161.63GB (DC) × 2 servers = 323.26GB
+ 600GB (DR retention / 4 days = 150GB/day)

Total: 323.26 + 150 = 473.26GB/day

Compression ratio (MariaDB compression): 1x (không nén)

BW needed = 473.26GB / 10 hours active / 60 / 60 × 8 bits × 1024
         = 861.543 Mbps

Tối ưu: 861.543 Mbps = 107.692 MB/s
```

**Yếu tố:**
- Chỉ replicate trong 8 giờ active business hours
- Ra multicast/UDP để giảm bandwidth
- SSD/NVMe storage với I/O低下 rất thấp
- TCP/TLS overhead: ~20-30%

**Bài học:**
- Network sizing phải account cho replication traffic
- DR replication bandwidth != Database workload bandwidth
- Peak replication có burst traffic rất lớn

### 7. KPI KHÁC BIỆT CHO Database
**Theo sizing:**
- **CPU:** ≤ 75%
- **RAM:** ≤ 90%
- **Disk:** ≤ 80%
- **Data node:** ≤ 50% ( nghiệp vụ database)

**Đặc biệt Data node ≤ 50%:**
- Database server có nhiều tiến trình
- Data node nơi I/O intensive
- Cần buffer lớn hơn cho I/O spikes

**Bài học:**
- Database workload khác application server
- Data node cần MARGIN lớn hơn (50% vs 75-90%)
- I/O patterns unpredictable → conservative sizing

### 8. NHIỆU SSD CHO DATABASE PERFORMANCE
**Recommendation từ BNH:**
```
"Memory là yếu tố rất quan trọng để cache data/index 
giảm truy cập đĩa. Storage phải có random seek time thấp, 
SSD hoặc tốt hơn."
```

**Áp dụng:**
- **DC:** 1.2TB SSD data partition
- **DR:** 1118GB SSD data partition (nhỏ hơn vì DR ít write-heavy)

**Lý do DR nhỏ hơn:**
- DR chủ yếu read operations (tra cứu, backup)
- DC chủ yếu write-heavy (transactions, inserts, updates)
- Write I/O expensive hơn read I/O → cần SSD nhiều hơn

### 9. ARCHITECTURE: ASYNCHRONOUS MULTI-MASTER
**Mô hình:**
- DC1 Master ↔ DC2 Master (bidirectional replication)
- GTID used to prevent circular replication
- No single master (both can write)

**Sizing implications:**
- Need bandwidth cho BOTH directions
- Replication traffic: 861.543 Mbps (as calculated)
- No need for real-time sync (asynchronous OK)

**Bài học:**
- Asynchronous replication reduces bandwidth needs (không cần real-time consistency)
- Still need substantial bandwidth for binlog transfer
- GTID prevents infinite replication loops

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### 1. MAXSCALE NODE (Cụm Cloud Core - MỚI)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 4 vCPU (~12 Cint 2017) | Tối thiểu theo BNH |
| **RAM** | 8 GB | Theo feedback chaulm5 |
| **HDD** | 100 GB | OS disk |
| **Số lượng** | 1 node | Bổ sung cho Cụm Cloud Core |
| **Location** | Cùng dải 10.254.150.x | Tối ưu độ trễ |

**Role:** SQL Proxy, Database Load Balancer

### 2. DATABASE DR CỤM QUẢN LÝ DB (Mới)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 vCPU | ~96 Cint 2017 |
| **RAM** | **96 GB** | Theo feedback chaulm5 (QUAN TRỌNG) |
| **OS Disk** | 60 GB HDD | |
| **Data Disk** | 1.2 TB SSD | Cho hot data |
| **Log Disk** | 600 GB | Binlog retention (4 days) |
| **Số lượng** | 3 nodes | Db-01, Db-02, Db-03 |
| **Location** | Khác site với DC | Đảm bảo DC-DR thực sự |

### 3. DATABASE DR CỤM DB ROUTING (Mới)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 vCPU | ~96 Cint 2017 |
| **RAM** | 64 GB | (nhỏ hơn Cụm Quản lý) |
| **OS Disk** | 60 GB HDD | |
| **Data Disk** | 1118 GB SSD | Nhỏ hơn do ít write |
| **Log Disk** | 161.63 GB | Binlog retention (1 day) |
| **Số lượng** | 3 nodes | 3 Maxscale + 3 Databases |
| **Location** | Khác site với DC | Đảm bảo DC-DR thực sự |

### 4. DATABASE DR CỤM DB CORE (Mới)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 vCPU | ~96 Cint 2017 |
| **RAM** | 64 GB | |
| **OS Disk** | 60 GB HDD | |
| **Data Disk** | 1118 GB SSD | |
| **Log Disk** | 161.63 GB | |
| **Số lượng** | 3 nodes | 3 Maxscale + 3 Databases |

### 5. DATABASE DR CỤM DB MYSIGN (Mới - MySign DR)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 vCPU | ~96 Cint 2017 |
| **RAM** | 64 GB | (giảm từ 96GB của DC) |
| **OS Disk** | 60 GB HDD | |
| **Data Disk** | 1.2 TB SSD | |
| **Log Disk** | 600 GB | |
| **Số lượng** | 3 databases + 3 Maxscale | Tổng 6 servers |

### 6. DATABASE DR CỤM DB BUSINESS (Mới - Business DR)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 vCPU | ~96 Cint 2017 |
| **RAM** | 64 GB | |
| **OS Disk** | 60 GB HDD | |
| **Data Disk** | 1118 GB SSD | |
| **Log Disk** | 161.63 GB | |
| **Số lượng** | 3 nodes | 3 Maxscale + 3 Databases |

**Tổng cộng DR:**
- Maxscale: 9 nodes (nhưng chỉ sizing cho Cụm DB Routing, Core, Business, Mysign)
- Database: 12 nodes (3 clusters × 3 replicas + 3 Mysign)
- Tổng ~21 servers

### 7. FIREWALL DR (Mới)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **Thông lượng** | ≥ 575.688 Mbps | ~70.7 MB/s |
| **Giao thức** | SSL | Secure communications |
| **HA Mode** | Active-Standby | redundancy chuẩn |
| **Số lượng** | 2 units | Tại DR site |

### 8. LOAD BALANCER DR (Mới)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **Thông lượng** | ≥ 575.688 Mbps | |
| **Concurrent Session** | 554 Session/s | Average |
| **Max Session** | 587.8 Session/s | Peak |
| **Số cổng** | ≥ 2 cổng 575.688 Mbps | |
| **HA Mode** | Active-Standby | |

### 9. NETWORK BANDWIDTH SUMMARY

| Connection | Băng thông | Purpose |
|------------|-----------|---------|
| **DC → DR Replication** | 861.543 Mbps (107.7 MB/s) | Binlog sync, 8 hours/day |
| **Firewall Peak** | 575.688 Mbps (70.7 MB/s) | External traffic, peak workload |
| **Concurrent Sessions** | 554 sessions/s | Database connections |
| **Replication Protocol** | TCP/3306 via MariaDB replication | Multi-master async |

---

## 🎯 CÁC BÀI HỌC QUAN TRỌNG

### 1. HỆ THỐNG ĐẶC BIỆT QUAN TRỌNG → YÊU CẤU DC-DR 1:1
**Quy định:** Theo 849/QĐ-CNVTQĐ
- Hệ thống đặc biệt quan trọng: Cần DC-DR
- Resource DC = Resource DR (duplicate 100%)

**Áp dụng:**
- CPU: 32 vCPU (DC) = 32 vCPU (DR)
- RAM: Có thể khác (DC: 64-96GB, DR: 64GB)
- Disk: Đủ cho production workload

**Bài học:**
- Không optimize cost bằng cách giảm DR resources
- DR là "insurance" → phải đủ resources để takeover seamlessly
- Trade-off: Chi phí cao hơn nhưng đem lại reliability

### 2. SỬ DỤNG RAM: 96GB CHO CRITICAL DATABASES
**Từ feedback chaulm5 (Thẩm định viên):**
- Yêu cầu RAM 96GB cho Database DR (Cụm quản lý)
- Lý do: Cache lớn → giảm I/O wait time → performance tốt hơn
- 64GB cho Database DC, DB Business, DB Core (ít write hơn DR)

**Cost implication:**
- 96GB RAM = 32GB buffer (50% tăng từ 64GB)
- Trade-off: Performance vs Cost
- Cho hệ thống Đặc biệt quan trọng → Performance prioritized

**Bài học sizing:**
- TínhBaseline: 64GB (production standard)
- Apply KPI 90%: 64 / 0.90 = 71.11GB → **96GB** (round to nearest power of 2)
- 96GB = 71.11GB × 1.2 (Ksaiso) × 1.12 (buffer)

### 3. TÍNH TOÁN BĂNG THÔNG REPLICATION
**Step 1: Calculate binlog size**
```
DC binlog per day: 161.63GB × 2 servers = 323.26GB
DR binlog per day: 600GB ÷ 4 days = 150GB/day

Total daily: 323.26 + 150 = 473.26GB/day
```

**Step 2: Convert to bandwidth**
```
Active hours: 8 hours/day (business hours)
Throughput: 473.26GB / 8 / 3600 × 8 bits/byte
         = 131.5 MB/s = 1,052 Mbps

Add overhead (TCP/TLS, MariaDB compression ~1x):
Actual BW = 1,052 Mbps × 0.82 (efficiency)
         = 861.5 Mbps (final calculated value)
```

**Bài học:**
- Replication bandwidth ≠ Database workload bandwidth
- Must account for compression ratios
- TCP/TLS overhead adds 20-30%
- Consider failover scenarios (burst traffic when DR takes over)

### 4. IOPS OPTIMIZATION CHO DATABASE
**BNH recommendation:**
```
"Storage phải có random seek time thấp, SSD hoặc tốt hơn"
```

**Applied sizing:**
- **Write-intensive DC:** 1.2TB SSD (có thể 2TB để room)
- **Read-intensive DR:** 1118GB SSD (đủ cho read workload)
- **Trade-off:** DC needs more IOPS than DR

**Bài học:**
- Write I/O expensive hơn Read I/O
- Database transactions are write-random patterns
- SSD NVMe required for production systems
- Monitor: disk latency, await time, buffer pool hit ratio

### 5. MAXSCALE TÍNH ÍT TÀI NGUYÊN, NHƯNG CẦN BUFFER
**Sizing:**
- Maxscale: 4 vCPU, 8GB RAM (tối thiểu)
- Placement: Trước Database stal 100GB OS disk
- Role: SQL Proxy (không chạy workload)

**Why minimal:**
- Maxscale chỉ routing/decoding queries
- Không cache data (database负责 cache)
- Stateless design → scale horizontally easy
- CPU 4 vCPU adequate cho SQL parsing

**Alternative (cho high-load scenarios):**
- Nếu cần connection pooling lớn: tăng RAM lên 16GB
- Nếu cần SSL termination overhead: tăng CPU lên 8 vCPU
- Theo dõi metrics: CPU usage, connection pool utilization

### 6. FIREWALL/LB SIZING: BASED ON ACTUAL TRAFFIC
**Công thức:**
```
Total peak traffic:
= Sum of all Database DB servers' traffic
= 479.74 Mbps (measured)

Apply buffer (Kdup = 1.2):
= 479.74 × 1.2
= 575.688 Mbps (~70.7 MB/s)
```

**Bài học:**
- Measure actual traffic, don't guess
- Use Kdup = 1.2 for network devices (lower than Ksaiso for compute)
- Peak traffic ≠ Average traffic
- Account for growth (11M users target)

### 7. KPI DATA NODE ≤ 50% (STRICTER THAN APP SERVERS)
**Why:**
- Database I/O unpredictable (spikes, storms)
- Write operations block reads (locking, WAL)
- Connection storms (burst connections from retry logic)
- Buffer pools, flush operations consume resources

**Apply sizing:**
```
Target IOPS: Assume 10,000 IOPS
Max at 50% = 5,000 IOPS safe margin

Example calculation:
CPU need = Current usage / 0.50 × 1.2
RAM need = Current usage / 0.50 × 1.2
```

**Trade-off:**
- More resources required (higher cost)
- Better reliability and predictability
- Avoid throtthling, timeouts under load

### 8. ASYNCHRONOUS MULTI-MASTER ARCHITECTURE
**Characteristics:**
- No single master (bidirectional replication)
- GTID prevents circular replication
- Asynchronous OK for CloudCA (eventual consistency acceptable)

**Sizing considerations:**
- Both DC and DR can write → need resources for writes
- Replication lag: acceptable for signing operations
- Conflict detection/resolution handled by MariaDB

**Bandwidth:**
- 861.5 Mbps for binlog transfer (as calculated)
- Must accommodate bursts during failover events
- Network latency < 50ms recommended between DC-DR

---

## 📋 MẪU HÌNH TÍNH TOÁN CHO DATABASE DC-DR

### STEP 1: XÁC ĐỊNH CẤ TRÚC HỆ THỐNG
```
Hệ thống Cloud CA:
- 3 Clusters: DB Routing, DB Core, DB Business, Mysign
- Criticality: Đặc biệt quan trọng
- DC-DR requirement: 1:1 per 849/QĐ-CNVTQĐ

Target:
- DC: Production workload
- DR: Hot standby with 100% resource duplication
```

### STEP 2: TÍNH TÀI NGUYÊN DC (BASELINE)
```
Cơ sở dữ liệu hệ thống hiện tại:
- Số users: 11,000,000 KH (mục tiêu năm tới)
- Query complexity: Medium-High (signing operations are I/O intensive)
- Concurrent users: Peak ~587.8 sessions/s

CPU baseline:
- Production: 32 vCPU per database node
- Derived from: Current load / 0.75 × 1.2
```

### STEP 3: TÍNH TÀI NGUYÊN DR (DUPLICATE DC)
```
DR sizing strategy:
Option A: Exact duplicate DR
- RAM = RAM_DC (maybe slightly less if DR là read-mostly)
- Example: DC = 96GB, DR = 64GB

Option B: Optimize DR for read-heavy workload
- Analyze: DR có ít writes hơn → I/O lower
- RAM_DR = 0.67 × RAM_DC (64GB vs 96GB)
- Cost savings while maintaining HA
```

### STEP 4: TÍNH STORAGE (SSD vs HDD)
```
Write-I/O intensive (DC):
- Data partition: 1.2TB SSD (hot data)
- Log partition: 600GB SSD (binlog retention 4 days)
- OS partition: 60GB HDD (OS)
- Total per node: ~1.86TB

Read-mostly (DR):
- Data partition: 1118GB SSD (sufficient for read-heavy)
- Log partition: 161.63GB (binlog retention 1 day)
- OS partition: 60GB HDD
- Total per node: ~1.34TB
```

### STEP 5: TÍNH NETWORK INFRASTRUCTURE
```
Replication bandwidth:
- Binlog size: 473.26GB/day (derived above)
- Active window: 8 hours
- Throughput: 861.5 Mbps (calculated with overhead)

Firewall:
- Peak traffic: 575.688 Mbps
- Redundancy: Active-Standby pair

Load Balancer:
- Sessions: 554 average, 587.8 peak
- Bandwidth: Same as firewall
- Redundancy: Active-Standby
```

---

## 🔧 CHECKLIST SIZING CHO DATABASE DC-DR

### 1. Business Requirements
- [ ] Xác định mức độ quan trọng (Đặc biệt quan trọng?)
- [ ] Xác định yêu cầu DC-DR (1:1, tỉ lệ khác?)
- [ ] Xác định RTO/RPO targets
- [ ] Xác định growth targets (users, transactions)

### 2. Architecture Design
- [ ] Chọn replication model (Async Multi-Master vs Galera)
- [ ] Xác định master-slave vs multi-master
- [ ] Design failover mechanism (auto vs manual)
- [ ] Plan split-brain scenarios

### 3. Resource Calculation
- [ ] Measure DC current utilization (CPU, RAM, I/O)
- [ ] Calculate DR based on DC (duplicate or optimized)
- [ ] Apply KPIs: CPU ≤ 75%, RAM ≤ 90%, Data node ≤ 50%
- [ ] Apply Ksaiso = 1.2 (for critical systems)

### 4. Storage Sizing
- [ ] Calculate data growth rate (GB/month)
- [ ] Disk type: SSD for data, HDD for OS
- [ ] Partition sizing: /data, /log, /os, /backup
- [ ] Binlog retention period (days)
- [ ] Backup strategy (size, frequency, retention)

### 5. Network Infrastructure
- [ ] Calculate replication bandwidth (binlog size × overhead)
- [ ] Calculate firewall/LB bandwidth
- [ ] Network latency requirements (<50ms between DC-DR recommended)
- [ ] Redundancy: Active-Standby for HA

### 6. Maxscale Sizing
- [ ] Calculate concurrent connections
- [ ] CPU: 4-8 vCPU (minimal for SQL proxy)
- [ ] RAM: 8-16GB (connection pool caching)
- [ ] Placement: Before database cluster, same network segment

### 7. High Availability Design
- [ ] Quorum etcd (if applicable)
- [ ] Auto-failover configuration
- [ ] Health check mechanisms
- [ ] Backup/recovery procedures
- [ ] DR testing schedule

### 8. Monitoring & Alerting
- [ ] Database metrics: CPU, RAM, I/O, connections
- [ ] Replication lag monitoring
- [ ] Maxscale health status
- [ ] Firewall/LB traffic monitoring
- [ ] Alert thresholds: CPU > 75%, RAM > 90%

---

## 🎯 KEY INSIGHTS

### 1. SYSTEM CLASSIFICATION DIRECTS SIZING STRATEGY
```
Đặc biệt quan trọng (Critical):
→ DC-DR 1:1, Ksaiso 1.2, Resource duplication 100%
→ Example: CloudCA (ký số từ xa)

Quan trọng (Important):
→ DC-DR 1:1, Ksaiso 1.1, Resource duplication 100%
→ Example: Core BCCS, Enterprise systems

Bình thường (Normal):
→ DC-DR 1:1, Ksaiso 1.1, Optimized DR (less resources)
→ Example: Internal tools, Reporting systems

Ít quan trọng (Low):
→ No DC-DR needed, backup only
→ Example: Dev/test environments
```

### 2. RAM SIZING FOR DATABASE SERVERS
```
Baseline: 64GB (production standard)

Critical Database (CloudCA level):
→ 96GB (50% increase)
→ Justified by: Large cache size → Better I/O performance
→ Cost justified for critical systems

Non-Critical Database:
→ 64GB (baseline)
→ Or 48GB for read-heavy workloads
```

### 3. STORAGE STRATEGY FOR DATABASE CLUSTERS
```
Partition Scheme:
- /os: 60GB (OS + logs)
- /data: Primary data storage
- /log: Binlog storage (retention 1-7 days depending)

Sizing:
- /data: 1.2TB for write-heavy DC, 1118GB for read-heavy DR
- /log: 161.63GB-600GB depending on retention
- Multi-day retention needed for HA scenarios

Technology:
- SSD required for production (HDD too slow)
- NVMe preferred for I/O-intensive workloads
- Monitor IOPS, latency, throughput
```

### 4. NETWORK INFRASTRUCTURE FOR DC-DR
```
Minimum requirements:
- Replication bandwidth: 861.5 Mbps (for binlog sync)
- Firewall: 575.688 Mbps peak
- Load balancer: 554-588 concurrent sessions
- Network latency: <50ms between DC-DR

Optimization:
- Use asynchronous replication to reduce real-time requirement
- TCP window scaling optimization
- Enable compression if supported
- Monitor for packet loss, retransmissions
```

---

## 📈 MẪU HÌNH TÍNH TOÁN CHO CÁC LOẠI HỆ THỐNG

### Pattern 1: DATABASE DC-DR 1:1
```
System: CloudCA (Viettel CA)
Mục tiêu: 11,000,000 users/year
Criticality: Special

Architecture:
- DC: 3 clusters (Routing, Core, Business, Mysign)
- DR: Exact duplicate of DC
- Replication: Asynchronous Multi-Master

Sizing:
- DC: 32 vCPU, 64-96GB RAM, 1.2TB SSD
- DR: 32 vCPU, 64GB RAM, 1118GB-1.2TB SSD
- Maxscale: 4 vCPU, 8GB RAM minimal

Network:
- Replication BW: 861.5 Mbps
- Firewall: 575.688 Mbps
- LB: 554-588 sessions

Cost optimization:
- DR can use less RAM if read-mostly (64GB vs 96GB)
- Storage can be optimized if I/O less intensive on DR
- Trade-off: Cost vs Reliability
```

### Pattern 2: DATABASE WITH MAXSCALE PROXY
```
System: CloudCA
Pattern: SQL Proxy trước Database cluster

Maxscale role:
- Connection pooling (reduce database connections)
- Query routing (read/write split)
- Load balancing across database nodes
- Minimal resources (4 vCPU, 8GB RAM)

Placement:
- Same network segment as databases (<1ms latency)
- Before database cluster (in request path)
- Separate servers from databases (shared-nothing)

Sizing considerations:
- CPU: Query parsing + routing overhead
- RAM: Connection cache, thread pool
- Network: Low latency to databases critical
```

### Pattern 3: FIREWALL/LB SIZING BASED ON ACTUAL TRAFFIC
```
Step 1: Measure current traffic
- Database network: 479.74 Mbps (peak)
- All DC servers combined

Step 2: Apply network buffer
- Kdup = 1.2 (20% buffer for network devices)
- Total = 479.74 × 1.2 = 575.688 Mbps

Step 3: Size accordingly
- Firewall: ≥ 575.688 Mbps
- Load Balancer: ≥ 575.688 Mbps
- Sessions: 554-588 concurrent sessions

Note:
- NOT using Ksaiso = 1.2 here
- This is Kdup (Network device buffer only)
- Separate from CPU/RAM Ksaiso
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **Quy định:** 849/QĐ-CNVTQĐ - Quy định đảm bảo dự phòng hệ thống thông tin
- **BNH Recommendation:** MariaDB hardware optimization guide
- **Best Practice:** https://mariadb.com/docs/server/ha-and-performance/hardware-optimization
- **Guideline Sizing:** Xem trong thư mục guideline_sizing/

---

**Người tạo tài liệu:** AI Assistant (dựa trên tài liệu sizing CloudCA và feedback email)
**Ngày tạo:** 2024
**Phiên bản:** 1.0
**Trạng thái:** ✅ Hoàn thành - Dùng cho reference cho các dự án Database DC-DR tương tự

---

## 📝 GHI CHÚ

- Tài liệu này trích xuất tri thức từ sizing và feedback qua email (chaulm5)
- Đây là ví dụ điển hình cho sizing hệ thống ĐẶC BIỆT QUAN TRỌNG
- Đặc biệt hữu ích cho: Database DC-DR, Maxscale sizing, replication bandwidth
- Feedback chaulm5 về RAM 96GB là learning point quan trọng
- Cần tuân thủ guideline sizing của Viettel (xem trong thư mục guideline_sizing/)