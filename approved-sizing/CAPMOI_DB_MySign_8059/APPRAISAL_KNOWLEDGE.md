# APPRAISAL KNOWLEDGE - DB MYSIGN

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG DB MYSIGN  
**Mã PYC:** PYC-8059  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 2 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Bổ sung hạ tầng cho hệ thống có sẵn  
**Đầu mối:** thanhtt69  
**Thẩm định viên:** Khanhnd23 (P.Hệ thống)  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 2 (v3)

**Yêu cầu chính:**
1. **Rounding errors:** Số liệu làm tròn quá nhiều → cint, RAM tính bị sai lệch (cint 96, ram 47)
2. **DB type unclear:** DB dùng Oracle hay MariaDB → ảnh hưởng giá trị N server
3. **Missing App sizing:** Sao chỉ sizing DC cho DB, không thấy phần App
4. **Network equipment:** Bổ sung thông tin định cỡ FW/LB
5. **N+1 configuration:** Đề xuất N+1 (đang để là 3, cần rõ hơn)
6. **Timeframe confusion:** Số liệu tính trong 1 tháng hay 6 tháng?
7. **Storage breakdown:** Tổng tài nguyên data, log, backup - có tách ra không?
8. **IOPS justification:** Bổ sung sởffff chỉ tính IOPS
9. **SDD usage:** Bổ sung sởffff chỉ sử dụng SSD
10. **Connection info:** Bổ sung thông tin mở kết nối

---

## 💡 TRI THỨC RÚT RA

### 1. Rounding errors cascade

**The problem:**
```
WRONG approach (multiple rounding):
  Per-VM: 96.7 vCPU → round to 97
  Total: 97 × 3 = 291 vCPU
  With safety: 291 × 1.2 = 349.2 → round to 350 vCPU
  
Result: Errors compound at each step!

RIGHT approach (round at end):
  Per-VM: 96.7 vCPU (keep decimals)
  Total: 96.7 × 3 = 290.1 vCPU
  With safety: 290.1 × 1.2 = 348.12 → round to 348 vCPU
  
Result: More accurate!
```

### 2. DB type affects N value

**Oracle vs MariaDB clustering:**
```
MariaDB Galera Cluster:
  - Multi-master replication
  - Typically 3 nodes minimum
  - N = odd number (3, 5, 7)
  - No single point of failure

Oracle RAC:
  - Also multi-master
  - Typically 2+ nodes
  - More expensive licensing
  - N depends on workload

Impact on sizing:
  - CPU/RAM per node differs
  - Storage requirements differ
  - License costs vary significantly
```

### 3. DC-only sizing is incomplete

**What's missing:**
```
Sizing should include:
  ✅ DC (Data Center): Database servers
  ❌ APP (Application): Application servers
  ❌ FW (Firewall): Network security
  ❌ LB (Load Balancer): Traffic distribution

Without APP sizing:
  - Can't calculate true resource needs
  - DB sizing might be insufficient
  - Network requirements unknown
```

### 4. N+1 redundancy clarity

**N+1 means:**
```
N = Number of servers needed for workload
+1 = One additional server for redundancy

Example:
  Workload needs 2 servers
  N+1 = 2 + 1 = 3 servers total
  
Benefits:
  - If 1 server fails, 2 remain operational
  - Can handle 1 failure without degradation
  - Standard for production systems

Important:
  - N+1 ≠ 3 servers
  - N+1 = (workload servers) + 1
  - If workload needs 3 servers → N+1 = 4 servers
```

### 5. Storage partitioning

**Best practice breakdown:**
```
Total storage should be split:

/data:  Primary database data
  - Random I/O intensive
  - High performance storage (SSD)
  - Example: 500 GB

/log:   Transaction logs
  - Sequential writes
  - Can use HDD or SSD
  - Example: 100 GB

/backup: Database backups
  - Compressed archives
  - Cheaper storage (HDD)
  - Example: 1 TB

Total: 500 + 100 + 1000 = 1.6 TB
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System type
- MySign Database deployment
- Supplementing existing infrastructure
- Database-focused (app sizing missing)

### Key issues
- Rounding errors in calculations
- DB type unconfirmed (Oracle/MariaDB)
- Missing app, FW, LB sizing
- N+1 configuration unclear
- Storage partitioning needed
- IOPS justification required

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Avoid intermediate rounding**
  - Keep decimals during calculations
  - Round only at the final step
  - Reduces cumulative errors

2. **Confirm DB type before sizing**
  - Oracle ≠ MariaDB
  - Different clustering models
  - Different resource requirements
  - Affects N value significantly

3. **Size ALL components**
  - Database alone is insufficient
  - Include APP, FW, LB
  - Complete system needs complete sizing

4. **N+1 is formula, not magic number**
  - N+1 = workload + 1
  - Not always equal to 3
  - Depends on actual requirements

5. **Partition storage by function**
  - /data: Primary data (SSD preferred)
  - /log: Transaction logs (HDD acceptable)
  - /backup: Archives (HDD OK)
  - Each has different I/O patterns

6. **Justify SSD usage**
  - Calculate IOPS: r/s + w/s
  - Compare to HDD limits (~200 IOPS)
  - SSD only if IOPS > 1000-2000

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 2 (calculation errors + missing components)  
**Vấn đề chính:** Rounding errors, incomplete sizing, DB type unclear, N+1 confusion

**Đặc điểm:**
- Database supplement sizing
- Cloud CA system integration
- Multiple calculation errors
- Incomplete component coverage