# APPRAISAL KNOWLEDGE - Hệ thống DB MySign (Cloud-CA)

## 📋 Thông tin Hồ sơ

- **Dự án:** Hệ thống Signing File Service (MySign) - Ký số từ xa
- **Mã PYC:** PYC-8059
- **Người thẩm định:** Khanhnd23 - P.Hệ thống
- **Đầu mối yêu cầu:** thanhtt69
- **Ngày thẩm định:** 2024 (2 vòng PNX)
- **Loại hồ sơ:** TRƯỜNG HỢP A (Có Phiếu Nhận Xét - PNX)
- **Mục đích sizing:** Phục vụ QHDC 2024

## 📊 Trạng thái Hồ sơ

- **Có PNX:** ✅ Có 2 vòng phản hồi thẩm định (PNX v2)
- **Trạng thái:** Chưa có thông tin ký duyệt cuối

---

## 🎯 Tri Thức Rút Ra Từ PNX

### 1. Số Liệu Làm Tròn Quá Nhiều (Critical Error)

**Vấn đề:**
- Sizing có nhiều số liệu nhưng làm tròn quá nhiều
- Khiến kết quả tính toán bị sai lệch: cint, ram thấp hơn thực tế

**Yêu cầu P.HT:**
- "Số liệu tính toán làm tròn quá nhiều  até cint, ram tính toán bi sai lệch"
- "Tính toán lại số liệu"

**Impact Analysis:**
```
Example from sizing:
App Server sizing:
- Per-subscriber metrics: 
  • Cint/thuê bao = 6.02 / 340,000 = 0.0000177 (CORRECT)
  • Sizing documented: 0.000018 (ROUNDED - 2.8% ERROR!)
  
RAM/thuê bao = 18.74 / 340,000 = 0.0000551 (CORRECT)
  • Sizing documented: 0.000056 (ROUNDED - 1.6% ERROR!)

For 2,000,000 subscribers:
Cint_needed = 0.000018 * 2,000,000 = 36 Cint (documented)
Cint_needed = 0.0000177 * 2,000,000 = 35.4 Cint (accurate)

Error small now BUT:
- At scale: Small % * large number = SIGNIFICANT DIFFERENCE
- Accumulation: Multiple rounding compounds error
- N value calculation: Small difference changes node count
```

**Best Practice:**
```markdown
✅ Use full precision for intermediate calculations:
   Per_CCU_Cint = 6.02 / 340,000 = 0.00001770588
   Per_CCU_RAM = 18.74 / 340,000 = 0.00005511765

✅ Only round final numbers:
   RAM_needed = 136.89 → 137 GB (reasonable)
   Or 136.89 → 140 GB (standard size)

✅ Document rounding decisions:
   "RAM calculated as 136.89 GB with KPI 90%, rounded to 140 GB for standard server configuration"

❌ DON'T round per-unit metrics:
   Wrong: 0.000018 Cint/subscriber (3 significant figures)
   Right: 0.00001770588 Cint/subscriber (full precision)
```

---

### 2. Database Type Affects N Value (Important)

**Vấn đề:**
- Sizing không rõ database là Oracle hay MariaDB
- Điều này ảnh hưởng lớn đến số lượng server (value N) cần thiết

**Yêu cầu P.HT:**
- "DB dùng loại gì (Oracle, MariaDB) --> xem lại giá trị N server cho phù hợp"

**Why Database Type Matters:**
```
Oracle Database Characteristics:
- Proprietary, licensed software
- Typically requires: N+2 or higher redundancy (1 primary + 2+ standby)
- RAC (Real Application Clusters): 2+ nodes minimum
- Data Guard: 1 primary + 1-4 standby databases
- Recommended N: 3-6 servers for production

MariaDB/MySQL Characteristics:
- Open-source database
- Typical configuration: 1 master + N replicas
- Master-slave replication: 1 primary + 1-2 replicas sufficient
- Galera Cluster: 3 nodes minimum for quorum
- Recommended N: 2-4 servers for production

Sizing Impact:
N=2 (as calculated for MySign):
- For Oracle: TOO LOW (only 2 nodes = insufficient HA)
- For MariaDB: APPROPRIATE (1 master + 1 slave is standard)

Cost Impact:
- Oracle: Need N=3-6 → Higher CAPEX
- MariaDB: N=2 is acceptable → Lower CAPEX

MySign Sizing Final:
Document specifies MariaDB v10.4 (correct)
N=2 servers calculated (APPROPRIATE for MariaDB)
Each server: 105.6 Cint, 34.2 GB RAM
```

**Database Selection Criteria:**
```
When to choose Oracle:
- Enterprise-grade requirements
- Advanced features needed (RAC, partitioning, advanced security)
- Existing Oracle expertise/team
- Budget allows for licensing cost

When to choose MariaDB/MySQL:
- Cost-conscious project
- Open-source preference
- Standard features sufficient
- Horizontal scaling requirements

For MySign:
- Already using MariaDB v10.4 in current system
- Successfully running with 2 node master-slave
- No need for Oracle-specific features
- CORRECT to stay with MariaDB
```

---

### 3. Thiếu Phần App Sizing (Critical Omission)

**Vấn đề nghiêm trọng:**
- Sizing chỉ có phần Database (DB)
- Không thấy phần Application (App) sizing

**Yêu cầu P.HT:**
- "Sao chỉ sizing DC cho DB, không thấy phần App"

**Impact:**
```
MySign System Architecture:
- Application Layer: File signing service, API gateway, web UI
- Database Layer: MariaDB cluster storing certificates, signing requests
- Storage Layer: NAS for file storage, logs, backups

Missing App Sizing means:
❌ No CPU/RAM for application servers
❌ No network bandwidth for API calls
❌ No sizing for load balancers
❌ Incomplete sizing for FIREWALL/LB

Completed Architecture (after fix):
✅ App cluster: 2 nodes (2 servers with 26.4 Cint, 68.45 GB RAM)
✅ DB cluster: 6 nodes (6 servers with 105.6 Cint, 34.2 GB RAM)
✅ NAS storage: 2 nodes (5,362.5 GB each)
✅ Firewalls: 2 active-standby
✅ Load Balancers: 2 active-standby
```

---

### 4. Timeline Confusion: 1 Tháng hay 6 Tháng?

**Vấn đề:**
- Sizing tính toán cho timeline không rõ ràng
- P.HT hỏi: "Số liệu tính trong 1 tháng hay 6 tháng?"

**Yêu cầu P.HT:**
- "Số liệu tính trong 1 tháng hay 6 tháng ? (trang 10)"
- "2 năm sao chỉ *6 ?"

**Timeline Analysis from Sizing:**
```
App Server Sizing (page 10):
- Growth target: 340,000 → 2,000,000 subscribers (5.9x)
- Time horizon: NOT explicitly stated in calculation
- BUT appears to be for 6-month period

DB Server Sizing (page 15):
- /data partition: 2 years ( dòng 1109: 0.6*30*12*2 = 432 GB)
- /log partition: 6 months ( dòng 1155: 4.7*30*6 = 846 GB)
- /backup partition: 4 days ( dòng 1197: 84.1*4 = 336.4 GB)

❌ INCONSISTENCY:
- App sizing: Unknown timeline (appears 6 months)
- DB /data: 2 years
- DB /log: 6 months (not 2 years!)
- DB /backup: 4 days (very short!)

Best Practice for Timeline Consistency:
✅ Define single timeline for entire system
✅ All components scale to same horizon
✅ OR clearly justify different timelines per component
✅ Document WHY log is 6 months but data is 2 years

Question for P.HT:
Why is log retention 6 months but data retention 2 years?
Typical practice:
- Data: Long-term (2-7 years) for business records
- Logs: Medium-term (3-6 months) for troubleshooting
- Backups: Short-term (7-30 days) for recovery
- This is ACCEPTABLE if documented properly
```

---

### 5. Bảng Giá Trị N (N Value Table)

**Vấn đề:**
- Sizing có đề xuất N=2 cho App servers nhưng thiếu bảng tính toán
- P.HT yêu cầu lập bảng giá trị để tối ưu

**Yêu cầu P.HT:**
- "Lập bảng giá trị (trang 15)"
- "Lưu ý giá trị đề xuất N+1 (trang 10)"

**App Server N Value Calculation:**
```
Total Resources Needed:
- Cint: 52.8
- RAM: 136.89 GB

Bảng giá trị N:
N | Cint/Node | RAM/Node (GB) | Total Cint | Total RAM | Comments
--+-----------+--------------+-----------+----------+--------
2 | 52.8/2 = 26.4 | 136.89/2 = 68.45 | 52.8 | 136.89 | Meets requirement
3 | 52.8/3 = 17.6 | 136.89/3 = 45.63 | 52.8 | 137.07 | Underutilized

Selection: N = 2
With N+1 redundancy: N+1 = 3 servers proposed
Each server: 26.4 Cint, 68.45 GB RAM
```

**DB Server N Value Calculation:**
```
Total Resources Needed:
- Cint: 528
- RAM: 171.1 GB

Bảng giá trị N:
N | Cint/Node | RAM/Node (GB) | Total Cint | Total RAM | Comments
--+-----------+--------------+-----------+----------+--------
5 | 528/5 = 105.6 | 171.1/5 = 34.2 | 528 | 171 | Optimal
6 | 528/6 = 88 | 171.1/6 = 28.5 | 528 | 171 | Lower config

Selection: N = 5 (minimum to meet single server resource)
With N+1 redundancy: N+1 = 6 servers proposed
Each server: 105.6 Cint, 34.2 GB RAM

Note: For MariaDB master-slave:
- 1 master handles writes + reads
- 5 slaves handle read queries
- Total: 6 servers (N+1 where N=5)
```

---

### 6. Mục Đích Sizing Cụ Thể

**Vấn đề:**
- Mục đích sizing ban đầu: "Phục vụ QHDC 2024"
- Không rõ QHDC là gì và tại sao cần sizing

**Yêu cầu P.HT:**
- "Bổ sung lại mục đích sizing"

**Proper Documentation:**
```
Mục đích sizing:
1. Lý do: Phát triển hệ thống MySign để đáp ứng quy hoạch phát triển Đầu tư Công Nghệ Trung ương (QHDC) năm 2024
2. Nhu cầu: Mở rộng từ 340,000 khách hàng lên 2,000,000 khách hàng
3. Mục tiêu:
   - Hỗ trợ ký số từ xa tuân thủ thông tư 16/2019/TT-BTTTT
   - Đảm bảo HA (High Availability) cho hệ thống chứng thư số
   - Tăng năng lực phục vụ ký file cho khách hàng
4. Timeline: Triển khai trong năm 2024
5. Công nghệ: MariaDB v10.4, CentOS 7, Cloud infrastructure
```

---

### 7. Sở Cứ SSD Usage

**Vấn đề:**
- Sizing đề xuất dùng SSD cho database nhưng thiếu lý do
- P.HT hỏi về sở cứ sử dụng SSD

**Yêu cầu P.HT:**
- "Bổ sung sở cứ sử dụng SSD"

**SSD vs HDD Decision Framework:**
```
Characteristics:
SSD (Solid State Drive):
- Fast I/O: 100,000+ IOPS vs HDD 200 IOPS
- Low latency: <1ms vs HDD 5-10ms
- Higher cost: $/GB 3-5x HDD
- Better for: Database, logs, high-transaction systems

HDD (Hard Disk Drive):
- Slower I/O: ~200 IOPS
- Higher latency: 5-10ms
- Lower cost: $/GB much lower
- Better for: File storage, backup, archival

MySign Database Analysis:
Workload: 2,000,000 customers
- High transaction rate: Signing requests per second
- Random I/O pattern: Certificate lookups
- Low latency required: Signing must be fast

Sizing Partition Strategy:
✅ /data (database files): SSD 594 GB
   Reason: Fast I/O for certificate storage
   
✅ /log (transaction logs): SSD 1,163.3 GB
   Reason: High write rate for transaction logs
   
✅ /backup (database backups): HDD 462.55 GB
   Reason: Backup is sequential I/O, cost-effective

✅ OS partition: SSD 60 GB
   Reason: Fast boot and application startup

Evidence/Reference:
- Current system uses SSD for /data and /log
- Database performance best practices: Use SSD for active data
- Industry standard: SSD for DB data, HDD for backups
```

---

### 8. Thiếu Thông Tin FW/LB Sizing

**Vấn đề:**
- Sizing ban đầu thiếu phần định cỡ thiết bị mạng (Firewall và Load Balancer)

**Yêu cầu P.HT:**
- "Bổ sung thông tin định cỡ thiết bị mạng (FW/LB)"
- "Bổ sung thông tin mở kết nối của hệ thống"

**Network Infrastructure Sizing:**
```
Bandwidth Calculation:
Current system (340,000 customers):
- Total traffic across all servers: 69.6 Mb/s
- Measured from actual network interfaces

Target system (2,000,000 customers):
- Scaled traffic: 69.6 * 2,000,000 / 340,000 = 409.1 Mb/s
- With safety factor 1.2: 409.1 * 1.2 = 492.3 Mb/s
- With peak factor 1.5: Final = 492.3 * 1.5 = 738 Mb/s

Firewall Sizing:
Requirements:
- Minimum throughput: 492.3 Mb/s (average)
- Recommended throughput: 1 Gb/s (for peak and growth)
- Redundancy: Active-standby pair
- SSL termination support (for HTTPS)
- Connection limit: Support 2,000,000 concurrent users

Load Balancer Sizing:
Requirements:
- Minimum throughput: 492.3 Mb/s per appliance
- Redundancy: Active-active or active-standby pair
- Session persistence: Cookie-based (already configured)
- Health check: HTTP endpoint /actuator (already configured)
- SSL offload: Support HTTPS 443, HTTP 80

Connection Policy Table:
(Provided in sizing document with 10 connection rules)
- From DB to IIM system (monitoring)
- From DB to DCIM system (infrastructure management)
- From DB to AAM system (access management)
- From DB to Prometheus (monitoring)
- From Gateway to DB (application traffic)
- From Server to NTP (time sync)
- From Server to SIRC (security)
- From Server to Repo (package repository)
```

---

### 9. Tổng Tài Nguyên Storage Chia Ra?

**Vấn đề:**
- P.HT hỏi về việc chia storage dữ liệu, log, backup thành các phần riêng biệt

**Yêu cầu P.HT:**
- "Tổng tài nguyên data, log, backup giữ nguyên không chia ra à?"

**Storage Partition Strategy:**
```
Why Separate Partitions:

1. /data partition (594 GB SSD):
   - Stores: Database table data (.ibd files)
   - Access pattern: High random I/O
   - Performance requirement: FAST (SSD required)
   - Recovery time: Critical (must be available immediately)
   - Backup frequency: Full backup daily

2. /log partition (1,163.3 GB SSD):
   - Stores: Transaction logs (binlog, slow query log, error log)
   - Access pattern: Sequential write-heavy
   - Performance requirement: FAST (SSD required)
   - Retention: 6 months (not 2 years like data)
   - Purpose: Troubleshooting and recovery

3. /backup partition (462.55 GB HDD):
   - Stores: Full database backups
   - Access pattern: Sequential read (restore operations)
   - Performance requirement: MEDIUM (HDD acceptable)
   - Retention: 4 days rolling backup
   - Purpose: Point-in-time recovery

Benefits of Separate Partitions:
✅ Performance isolation: Log writes don't affect data I/O
✅ Storage optimization: SSD where needed, HDD where sufficient
✅ Backup management: Easy to manage backup retention policy
✅ Recovery speed: Can restore from backup while log is active
✅ Cost optimization: HDD is cheaper than SSD

Total Storage per Node:
- OS: 60 GB SSD
- /data: 594 GB SSD
- /log: 1,163.3 GB SSD
- /backup: 462.55 GB HDD
- TOTAL: 2,280 GB (2.2 TB) per node
- For 6 nodes: 2,280 * 6 = 13,680 GB (13.2 TB) across cluster

Storage Redundancy:
"At tối thiếu 2 storage độc lập đảm bảo tính dự phòng"
- Storage 1: Primary storage for nodes 1,2,3
- Storage 2: Primary storage for nodes 4,5,6
- Or: Shared storage with RAID 1/10 for redundancy
```

---

## 📈 Thông Số Kỹ Thuật

### System Architecture

**Application Layer - File Signing Service:**
- Function: Provide remote file signing service
- Protocol: HTTPS (SSL/TLS)
- Compliance: Circular 16/2019/TT-BTTTT
- High Availability: Active-active clustering

**Database Layer - MariaDB v10.4:**
- Function: Store certificates, signing requests, metadata
- Configuration: Master-slave replication
- Current: 340,000 customers
- Target: 2,000,000 customers

**Storage Layer:**
- NAS: File storage for signing operations (2 nodes × 5,362.5 GB)
- Database storage: /data, /log, /backup partitions

### Workload Requirement

**Business Growth:**
- **Current:** 340,000 customers (actual measured)
- **Target:** 2,000,000 customers (5.9x growth)
- **Growth period:** Not explicitly stated (appears 6-month projection)

**File Signing Operations:**
- Concurrent users: 2,000,000
- Signing requests: Per customer activity (hard to estimate from doc)
- Network bandwidth: 492.3 Mb/s average

### Sizing Calculation Detail

**Application Cluster:**
```
Baseline (current 2 servers, 340,000 customers):
- Total Cint used: 6.02 (3.97% + 7.79% of 51.2 each)
- Total RAM used: 18.74 GB (9.65 + 9.09)
- CPU utilization: LOW (3.97%, 7.79%)
- RAM utilization: MEDIUM (60.3%, 56.8%)

Per-customer metrics:
- Cint/customer = 6.02 / 340,000 = 0.0000177 Cint/customer
- RAM/customer = 18.74 / 340,000 = 0.0000551 GB/customer

Target (2,000,000 customers):
- Cint needed: 0.0000177 * 2,000,000 = 35.4 Cint
- RAM needed: 0.0000551 * 2,000,000 = 110.2 GB

Apply safety factor 1.1 & KPI:
- Cint_final: 35.4 * 1.1 / 0.75 = 51.92 Cint ≈ 52.8 Cint
- RAM_final: 110.2 * 1.1 / 0.90 = 134.7 GB ≈ 136.89 GB

N value calculation:
N = 52.8 / 26.4 = 2
With N+1 redundancy: 3 servers (2 active + 1 standby)
Each: 26.4 Cint, 68.45 GB RAM
```

**Database Cluster (MariaDB):**
```
Baseline (current 2 servers, 340,000 customers):
- Total Cint used: 61.6 (19.2% + 40.9% of 102.4 each)
- Total RAM used: 23.56 GB (9.82 + 13.74)
- CPU utilization: MEDIUM (19.2%, 40.9%)
- RAM utilization: MEDIUM (30.7%, 42.9%)

Per-customer metrics:
- Cint/customer = 61.6 / 340,000 = 0.000181 Cint/customer
- RAM/customer = 23.56 / 340,000 = 0.0000693 GB/customer

Target (2,000,000 customers):
- Cint needed: 0.000181 * 2,000,000 = 362 Cint
- RAM needed: 0.0000693 * 2,000,000 = 138.6 GB

Apply safety factor 1.1 & KPI:
- Cint_final: 362 * 1.1 / 0.75 = 530.9 Cint ≈ 528 Cint
- RAM_final: 138.6 * 1.1 / 0.90 = 169.4 GB ≈ 171.1 GB

N value calculation:
N = 528 / 105.6 = 5
With N+1 redundancy: 6 servers (5 + 1)
Each: 105.6 Cint, 34.2 GB RAM

Storage partitions per node:
- /data: 594 GB SSD (2-year retention)
- /log: 1,163.3 GB SSD (6-month retention)
- /backup: 462.55 GB HDD (4-day rolling backup)
- OS: 60 GB SSD
```

**Network Bandwidth:**
```
Current measured bandwidth (340,000 customers): 69.6 Mb/s

Target (2,000,000 customers):
- Scaled: 69.6 * 2,000,000 / 340,000 = 409.1 Mb/s
- With safety factor 1.2: 409.1 * 1.2 = 492.3 Mb/s

Firewall/LB sizing:
- Minimum throughput: 492.3 Mb/s
- Recommended: 1 Gb/s
- Configuration: Active-standby pair
```

### Final Configuration Summary

**Application Servers:**
- **Count:** 3 (2 active + 1 standby, N+1)
- **Each:** 26.4 Cint, 68.45 GB RAM, 2,634 GB HDD
- **OS:** CentOS 7
- **NAS:** 2 nodes × 5,362.5 GB (active-standby)

**Database Servers:**
- **Count:** 6 (5 + 1 N+1 redundancy) - MariaDB master-slave
- **Each:** 105.6 Cint, 34.2 GB RAM
- **Storage per node:**
  - SSD 60 GB (OS)
  - SSD 594 GB (/data - 2 years)
  - SSD 1,163.3 GB (/log - 6 months)
  - HDD 462.55 GB (/backup - 4 days)
- **OS:** CentOS 7
- **Database:** MariaDB v10.4

**Network Infrastructure:**
- **Firewall:** 2 active-standby, 1 Gb/s
- **Load Balancer:** 2 active-standby, 1 Gb/s
- **Protocol:** SSL termination supported

---

## 💡 Best Practices Áp Dụng

### 1. **Dual-Layer Sizing (App + DB)**

```
MySign Example demonstrates proper dual-layer sizing:

APPLICATION LAYER:
- Stateless services (easier to scale)
- Lower resource requirements
- N+1 standard redundancy
- Example: 3 app servers (2+1)

DATABASE LAYER:
- Stateful data (harder to scale)
- Higher resource requirements
- N+1 or higher redundancy (master-slave or clustering)
- Example: 6 DB servers (5+1)

Why this matters:
- App can be stateless: Easy horizontal scaling
- DB is stateful: Complex scaling (replication, sharding)
- Resource ratios: DB requires 4x more Cint than App (528 vs 52.8)
- N value differs: App N=2, DB N=5 for same 2M customers
```

### 2. **MariaDB vs Oracle for Production**

```
Decision Matrix:

Choose MariaDB if:
✅ Open-source preference (no licensing cost)
✅ Standard database features sufficient
✅ Web application pattern (read-heavy)
✅ Horizontal scaling via replicas
✅ Budget constraints
✅ Team has MySQL/MariaDB expertise

Choose Oracle if:
✅ Enterprise-grade requirements
✅ Advanced features needed (RAC, advanced partitioning)
✅ Existing Oracle investment/skills
✅ Very high availability requirements (99.999%)
✅ Complex transaction processing
✅ Compliance requires specific Oracle features

MySign Analysis:
Current: Successfully using MariaDB v10.4 with 2-node master-slave
Requirement: Standard PKI database (certificates, requests)
Workload: Read-heavy (many certificate lookups per signing)
Growth: 340K → 2M customers (manageable for MariaDB)
Decision: ✅ MariaDB is APPROPRIATE
```

### 3. **Storage Tiering Strategy**

```
Three-Tier Storage Model:

TIER 1: HOT DATA (SSD - /data partition)
- Purpose: Active database tables
- Access pattern: High random I/O
- Performance: CRITICAL
- Retention: Long-term (2 years)
- Cost: HIGH (SSD required)

TIER 2: WARM LOGS (SSD - /log partition)
- Purpose: Transaction logs, query logs
- Access pattern: Sequential write-heavy
- Performance: HIGH (fast write required)
- Retention: Medium-term (6 months)
- Cost: HIGH (SSD required)

TIER 3: COLD BACKUP (HDD - /backup partition)
- Purpose: Full database backups
- Access pattern: Sequential read-only (restore)
- Performance: MEDIUM (HDD acceptable)
- Retention: Short-term (4 days rolling)
- Cost: LOW (HDD cost-effective)

MySign Implementation:
✅ /data: 594 GB SSD (2-year data retention)
✅ /log: 1,163.3 GB SSD (6-month log retention)
✅ /backup: 462.55 GB HDD (4-day backup rolling)
✅ Cost optimization: SSD where critical, HDD where acceptable

Annual Storage Growth:
Data: 0.6 GB/day * 365 = 219 GB/year
Logs: 4.7 GB/day * 365 = 1,715 GB/year
Backup: 84.1 GB/day (rolling 4-day window = 336 GB)
```

### 4. **Precision in Sizing Calculations**

```
Step-by-Step Calculation Best Practice:

STEP 1: Measure Baseline (Full Precision)
- Don't round: 6.02 / 340,000 = 0.00001770588
- Not: 6.02 / 340,000 ≈ 0.000018

STEP 2: Calculate for Target (Full Precision)
- Don't round: 0.00001770588 * 2,000,000 = 35.41176
- Not: 0.000018 * 2,000,000 = 36

STEP 3: Apply Safety Factor (Full Precision)
- Don't round: 35.41176 * 1.1 / 0.75 = 51.93925
- Not: 36 * 1.1 / 0.75 = 52.8

STEP 4: Round for Presentation (STANDARD SIZES)
- Acceptable: 51.93925 → 52 Cint (round to nearest integer)
- Acceptable: 136.89 GB → 140 GB (standard size)

STEP 5: Document Rounding
"Resource needed = 51.94 Cint, rounded to 52 Cint for standard server configuration"

WHY THIS MATTERS:
For large systems, small % = large absolute difference
Example: 3% error at 2M customers = 60 customers
60 customers × resources = significant server impact
```

### 5. **N+1 vs N+2 Redundancy for Database**

```
Redundancy Levels:

N+1 (Standard for MariaDB):
Configuration: 1 master + 1 standby
Total: 2 nodes
Benefit: Automatic failover, read replica
Risk: If standby fails = no protection during maintenance
Cost: +1 server = +50%
Use case: Standard production systems

N+2 (High Availability):
Configuration: 1 master + 2 standbys
Total: 3 nodes
Benefit: Can lose 1 node + perform maintenance on another
Risk: Higher cost
Cost: +2 servers = +100%
Use case: Mission-critical systems

N+5+1 (MySign Configuration):
Configuration: 1 master + 5 replicas + 1 extra = 7 nodes
Rationale: 
- 5 replicas handle read scaling (heavy read workload)
- 1 extra for N+1 redundancy
Total: 6 nodes (1 master + 5 slaves, with N+1 = 6 actually)
MySign specifics: N=5 calculated, N+1 = 6 total

WHY N=5 FOR MYSIGN:
- N=5 means each node handles 1/5 of read load
- Each needs 105.6 Cint, 34.2 GB RAM
- Total capacity: 528 Cint, 171 GB RAM
- Heavy read workload requires many replicas
```

---

## 🔧 Kinh Nghiệm Xử Lý

### 1. **Lỗi Rounding Số Liệu**

**Impact Analysis:**
```
Scenario: Per-customer metric calculation

Wrong approach (rounding intermediate):
Cint/customer = 6.02 / 340,000 = 0.000018 (rounded 3 sig figs)
For 2M customers: 0.000018 * 2,000,000 = 36 Cint
After safety factor: 36 * 1.1 / 0.75 = 52.8 Cint
Node count: 52.8 / 26.4 = 2 nodes ✓ (correct by luck)

Correct approach (full precision):
Cint/customer = 6.02 / 340,000 = 0.00001770588 (11 sig figs)
For 2M customers: 0.00001770588 * 2,000,000 = 35.41176 Cint
After safety factor: 35.41176 * 1.1 / 0.75 = 51.93925 Cint
Node count: 51.93925 / 26.4 = 1.967 → 2 nodes ✓ (still correct)
Margin: 52.8 vs 51.94 = 1.66% difference

BUT for different scenarios:
If threshold = 27 Cint/node instead of 26.4:
- Rounded: 52.8 / 27 = 1.955 → 2 nodes
- Precise: 51.94 / 27 = 1.924 → 2 nodes (same)
- If threshold = 25 Cint/node:
  - Rounded: 52.8 / 25 = 2.112 → 3 nodes
  - Precise: 51.94 / 25 = 2.077 → 3 nodes (same)

Lesson: 
✓ Small rounding errors usually don't change N value
✓ BUT use full precision anyway for correctness
✓ Round only final presentation numbers, not intermediate
```

### 2. **Timeline Confusion Resolution**

```
MySign Timeline Issues Found:

1. App servers: No timeline mentioned
   Appears to be: 6 months (based on resource needs)

2. DB /data partition: 2 years (page 15, line 1109)
   Formula: 0.6 * 30 * 12 * 2 = 432 GB

3. DB /log partition: 6 months (page 15, line 1155)
   Formula: 4.7 * 30 * 6 = 846 GB
   Question: Why 6 months not 24 months?

4. DB /backup partition: 4 days (page 15, line 1197)
   Formula: 84.1 * 4 = 336.4 GB

Best Practice for Timeline Consistency:
✅ Define primary timeline for entire system
✅ Document why different components have different timelines
✅ Justify shorter retention (cost, compliance, performance)

MySign Proper Documentation Could Be:
"System timeline: 2 years (2024-2026)
- DB /data: 2 years (regulatory requirement for certificate records)
- DB /log: 6 months (troubleshooting window, disk space management)
- DB /backup: 4 days (operational recovery, older backups in offsite storage)
- App servers: Scaled for 6-month capacity (will revisit at 6 months)
- NAS file storage: 6 months (customer file retention policy)"
```

### 3. **N Value Calculation Methodology**

```
Systematic Approach to N Calculation:

STEP 1: Calculate Total Resources Needed
Example (MySign DB):
Cint_total = 360 × 1.1 / 0.75 = 528 Cint
RAM_total = 140 × 1.1 / 0.90 = 171.1 GB

STEP 2: Determine Minimum Nodes for Single Server Capacity
Option A: Find max N where (resource / N) >= standard_config
Try N=3: 528/3 = 176 Cint/node
Try N=4: 528/4 = 132 Cint/node
Try N=5: 528/5 = 105.6 Cint/node
Try N=6: 528/6 = 88 Cint/node
Minimum N=5 (105.6 Cint/node is reasonable)

STEP 3: Build N Value Table
N | Cint/Node | RAM/Node | Meets Req? | Comments
--+-----------+---------+-----------+----------
3 | 176 | 57 | ✓ but oversized | Underutilized
4 | 132 | 42.8 | ✓ better balance | Good
5 | 105.6 | 34.2 | ✓ optimal | Selected
6 | 88 | 28.5 | ✗ too small | Below standard

STEP 4: Apply Redundancy
Selected N = 5
Redundancy = N+1 = 6 nodes total

MySign Final Decision:
N = 5 → N+1 = 6 nodes
Each: 105.6 Cint, 34.2 GB RAM
Rationale: Optimal balance of resource utilization and redundancy
```

---

## 📋 Check List Đánh Giá Trạng Thái

### ⚠️ Các vấn đề PHẢI FIX (Priority):

1. **❌ Rounding errors** - CRITICAL: Sử dụng full precision, chỉ round final numbers
2. **❌ Timeline inconsistency** - App (unknown) vs DB /data (2Y) vs DB /log (6M) vs DB /backup (4D)
3. **❌ DB type justification** - Cần explain why MariaDB not Oracle
4. **❌ Missing App sizing** - Initially only had DB, App added later
5. **❌ N value table** - Cần build table showing N=2 vs N=3 vs N=4 options
6. **❌ SSD justification** - Cần evidence why SSD required for /data and /log
7. **❌ Purpose clarity** - "QHDC 2024" không rõ, cần expand
8. **❌ Connection details** - Added 10 connection rules (GOOD FIX)

### 💡 Các vấn đề NÊN:

1. **Workload estimation** - 2M customers but unclear request rate
2. **Peak traffic analysis** - Only have average, 95th percentile data
3. **Storage growth validation** - 3-day measurement too short (should be 30+ days)
4. **Firewall/LB capacity** - 1 Gb/s might be insufficient if peak > 5x average

---

## 📝 Kết Luận

**Trạng thái hiện tại:**
- Sizing đầy đủ cả App và DB (sau khi bổ sung)
- Có lỗi rounding trong calculations (small but avoidable)
- Timeline inconsistency across components (needs documentation)
- N value calculated but thiếu systematic table

**Kết luận thẩm định:**
- ⚠️ Methodology: VALID (reference system approach)
- ⚠️ Calculations: Minor rounding errors, otherwise CORRECT
- ⚠️ Completeness: Initial version missing App, fixed in PNX v2
- ⚠️ Documentation: Timeline inconsistencies, needs clarification

**Bài học quan trọng:**

1. **Precision Matters:**
   ```
   Intermediate calculations: Full precision (11 sig figs)
   Final presentation: Round to reasonable (1-2 sig figs)
   Never round per-unit metrics (causes cumulative errors)
   ```

2. **Timeline Consistency:**
   ```
   Define PRIMARY timeline for entire system
   Document WHY components have different retention policies
   Align sizing target with business planning horizon
   ```

3. **N Value Optimization:**
   ```
   Build table showing N vs resource-per-node
   Select N based on standard server configurations
   Apply N+1 or N+2 redundancy based on criticality
   Database N > Application N (stateful complexity)
   ```

4. **Storage Partitioning Strategy:**
   ```
   Tiered storage: HOT (data) + WARM (logs) + COLD (backup)
   Use SSD where performance is critical
   Use HDD where cost optimization is acceptable
   Document retention policies for each partition
   ```

5. **Dual-Layer Sizing:**
   ```
   APPLICATION LAYER: Stateless, easier scaling, lower resources
   DATABASE LAYER: Stateful, complex scaling, higher resources
   Separate N values for each layer
   Different redundancy requirements (N+1 vs N+5+1)
   ```

**Action Items:**
1. ✅ Use full precision in calculations, round only final results
2. ✅ Document timeline rationale for each storage partition
3. ✅ Build N value tables for systematic decision-making
4. ✅ Provide SSD vs HDD evidence and justification
5. ✅ Clarify "QHDC 2024" business context