# APPRAISAL KNOWLEDGE - SSO 2.0 (XÁC THỰC TẬP TRUNG)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** XÁC THỰC TẬP TRUNG SSO 2.0  
**Mã PYC:** PYC-46385  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 2 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** CẤP MỚI tài nguyên triển khai hệ thống SSO 2.0 cho các hệ thống VTT  
**Đầu mối:** Chinh3  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét (2 rounds)

**Vòng 1-2 feedback:**
1. **KPI thresholds:** 80% disk, 75% Cint, 90% RAM (sizing đang dùng: 70%, 50%, 60% → Thấp!)
2. **MariaDB Galera Cluster:** Không có Master/Slave, multi-master architecture
3. **N+4 justification:** Bổ sung sởffff chỉ dự phòng N+4 (tại sao không N+1?)
4. **Storage:** 100GB data, 10GB log/day, keep 12 months
5. **Backup:** 3 years retention
6. **Reference system:** VSA system database

---

## 💡 TRI THỨC RÚT RA

### 1. SSO 2.0 architecture - Multi-master database

**MariaDB Galera Cluster:**
```
Traditional Master-Slave:
  - 1 Master (write)
  - N Slaves (read only)
  - Problem: Single point of failure

Galera Cluster (Multi-Master):
  - All nodes can read/write
  - Synchronous replication
  - No single master
  - Better HA but complex
```

**Sizing impact:**
```
Each node handles: 100% read/write (not shared)
Formula: Total_Load / Number_of_Nodes
NOT: Master + (Slaves × percentage)
```

### 2. Low KPI issue - Why 70%, 50%, 60%?

**Problem:**
```
Standard KPI:
  - Disk: 80% before alert
  - CPU: 75% (Cint) before scale
  - RAM: 90% before warning

SSO 2.0 sizing used:
  - Disk: 70% (conservative)
  - CPU: 50% (very conservative)
  - RAM: 60% (very conservative)
```

**Why so conservative?**
- May be over-provisioning
- Wastes resources
- Need justification for low thresholds

### 3. N+4 vs N+1 redundancy

**N+4 seems excessive:**
```
N+1: 1 spare node (standard for HA)
N+2: 2 spare nodes (high availability)
N+4: 4 spare nodes (unusual)

Common patterns:
  - 3-node cluster: N=3, add 1 = 4 total
  - 5-node cluster: N=5, add 1 = 6 total
  
N+4 would mean: if need 3 nodes, request 7 total
```

**Question:** Why N+4 for SSO?
- Expected high failure rate?
- Frequent maintenance windows?
- Or calculation error?

### 4. Storage retention policies

**SSO 2.0 requirements:**
```
Data storage: 100GB
Log generation: 10GB per day
Log retention: 12 months
Backup retention: 3 years

Total log storage: 10GB × 365 = 3.65 TB/year
With N+1 redundancy: 3.65 × 2 = 7.3 TB
```

### 5. One-way integration pattern

**SSO as authentication hub:**
```
SSO 2.0 receives connections:
  - Other systems connect TO SSO for auth
  - SSO does NOT connect TO others
  - Inbound traffic only

Network sizing:
  - Inbound spikes (login storms)
  - No outbound data transfer
  - FW rules: Allow inbound, restrict outbound
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### KPI Thresholds (Used in sizing)
- Disk: 70% (vs standard 80%)
- CPU: 50% (vs standard 75%)
- RAM: 60% (vs standard 90%)

### Storage
- Database: 100GB
- Log: 10GB/day × 365 days = 3.65 TB/year
- Retention: 12 months
- Backup: 3 years

### Database
- Type: MariaDB Galera Cluster
- Initial proposal: Master-Slave
- Corrected: Multi-master Galera
- Each node: 4 vCPU, 8GB RAM per node (corrected as insufficient)

### Redundancy
- N+4 (unusually high)
- Active + DR configuration

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Galera Cluster scales differently**
   - Multi-master, not master-slave
   - Each node handles full load
   - Don't divide by nodes for write capacity

2. **Low KPI = Over-provisioning**
   - 50% CPU = 2x resource needed
   - Should use standard: 75% for critical systems
   - Wastes budget unless justified

3. **N+4 is unusual**
   - Standard is N+1 for HA
   - Need strong justification for N+4
   - May indicate calculation error

4. **SSO has bursty traffic pattern**
   - Login storms (peak hours)
   - Authentication spikes (9AM, after lunch)
   - Size for peak, not average

5. **Long retention has storage impact**
   - 12 months logs = 3.65 TB
   - 3 years backup = 11 TB+
   - Storage cost grows linearly

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 2 (cần làm rõ kiến trúc)  
**Vấn đề chính:** Galera architecture, low KPI, N+4 redundancy

**Đặc điểm hệ thống:**
- Central authentication hub for VTT systems
- MariaDB Galera Cluster (multi-master)
- One-way integration (inbound only)
- Critical authentication service

**Khuyến nghị:**
- Use standard KPI (75%, 90%) unless justified
- Verify N+4 calculation (likely N+1 sufficient)
- Size for login storm peak (not average)
- Consider log storage cost for 12-month retention
- Document Galera-specific sizing methodology