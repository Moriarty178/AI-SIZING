# APPRAISAL KNOWLEDGE - VAPS SYSTEM

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG VAPS  
**Mã PYC:** PYC-57140  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Cấp mới  
**Đầu mối:** Giangnt109  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** thongnv31 (P.CNHT)

**Yêu cầu chính:**
1. **Missing servers:** Management servers (register/config/payment/reporting) not in proposal
2. **TPS vs CCU:** Làm rõ TPS hay CCU một cách cẩn thận
3. **Test data:** Hệ thống Test confirm TPS như thế nào?
4. **Reference system:** Viettel++ tương tự APS, dùng làm reference
5. **Database partitions:** /backup /data /log
6. **Input justification:** Làm rõ sởffff chỉ dung lượng trung bình của 1 giao dịch

---

## 💡 TRI THỨC RÚT RA

### 1. K8S microservice architecture

**VAPS components:**
```
K8S Service encompasses:
  - Register/config servers
  - Payment processing
  - Reporting/analytics
  - Monitoring
  
All grouped under Service K8S → Total resource sizing
```

### 2. TPS vs CCU confusion

**Critical distinction:**
```
WRONG: CCU calculated from TPS
RIGHT: Measure both independently

TPS (Transactions Per Second):
  - 200K TPS = workload rate
  - Throughput metric

CCU (Concurrent Users):
  - 20K users simultaneously
  - Connection metric

Relationship:
  - Not directly proportional
  - Depends on transaction rate per user
```

### 3. Database partitioning

**Best practice:**
```
/backup: Database dumps
  - Sequential writes
  - Compressed storage
  - Multiple versions

/data: Primary database
  - Random I/O heavy
  - Index storage
  - May need SSD

/log: Transaction logs
  - Sequential writes
  - Rotates frequently
  - HDD acceptable
```

### 4. Viettel++ reference system

**Similar to vAPS:**
```
Viettel++ characteristics:
  - API provider similar to APS
  - Authentication platform
  - Can reference for workload patterns

Usage:
  - Use TPS/CCU ratios as baseline
  - Adjust for vAPS specifics
  - Document differences
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System type
- VAPS (Authentication/platform system)
- K8S-based microservices
- New deployment

### Key issues
- TPS vs CCU clarity needed
- Reference: Viettel++ (similar system)
- DB storage partitioning required
- Missing app server components

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Don't mix TPS and CCU**
  - They measure different aspects
  - TPS: transaction throughput
  - CCU: concurrent user connections
  - Calculate separately

2. **All servers must be included**
  - Missing components cause sizing gaps
  - Register, config, payment, reporting all crucial
  - K8S grouping is OK but must be explicit

3. **Test environment sizing is tricky**
  - Test TPS ≠ Production TPS
  - Don't use test data for production sizing
  - Use pilot data or plus growth projection

4. **Database partitioning is mandatory**
  - /data /log /backup separate
  - Each has different I/O characteristics
  - Enables better backup and monitoring

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 1 (completeness needed)  
**Vấn đề chính:** TPS/CCU confusion, missing components, DB partitioning