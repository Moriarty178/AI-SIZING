# APPRAISAL KNOWLEDGE - SMARTHOME IoT PLATFORM

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG SMARTHOME (IoT Platform)  
**Mã PYC:** PYC-13709  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 3 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** NÂNG CẤP ĐẾN ỔN HỖ TRỢ 500,000 THIẾT BỊ  
**Đầu mối:** Tuta8  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét (3 rounds)

**Vòng 1-3 feedback:**
1. **500K devices target:** Bổ sung sởffff chỉ cho số liệu 500,000 (mong muốn VTT tương lai)
2. **CPU specs:** Loại CPU, Cint tương ứng, link tham chiếu (3 Cint2017 = 1 vCPU)
3. **IOPS calculation:** Tính lại IOPS cụ thể cho từng node để làm sởffff chỉ SSD
4. **FW/LB sizing:** Chỉ nhân K = 1.2 (không phải *1.1/0.75)
5. **Summary table:** Bảng tổng hợp tài nguyên cần với N+1

---

## 💡 TRI THỨC RÚT RA

### 1. Scaling 100K → 500K devices (5x)

**Approach:**
```
Current: 100,000 devices (reference system)
Target: 500,000 devices
Scale factor: 5x

Resource scaling:
  - CPU: 5x current usage
  - RAM: 5x current usage
  - Storage: 5x current usage
  - With safety factor: × 1.2
```

**Risk:** 5x is significant jump - consider phased rollout

### 2. K8S worker nodes per namespace

**Smarthome multi-tenant:**
```
Different services in different namespaces:
- Namespace A: Service 1 workers
- Namespace B: Service 2 workers
- Each needs separate load measurement

Total cluster = Sum(all namespaces) + overhead
```

### 3. Multi-database architecture

**Components:**
- **MongoDB:** Document store for IoT data
- **PostgreSQL:** Relational data
- **ScyllaDB:** Time-series/Cassandra-compatible

**Each needs:**
- Current usage baseline
- IOPS measurement
- Storage projection (5x)
- SSD justification with specific IOPS

### 4. IOPS calculation for SSD justification

**Formula:**
```
IOPS_needed = (Read_Ops + Write_Ops)

Where:
- Read_Ops = Query_rate × Records_per_query
- Write_Ops = Device_events × Events_per_device

SSD required if:
  IOPS_needed > 500 (HDD 7.2K RPM limitation)
```

### 5. FW/LB safety factor = 1.2 only

**Important correction:**
```
WRONG: Throughput × 1.1 / 0.75
RIGHT: Throughput × 1.2 only

Reason:
- Network equipment sizing ≠ Server sizing
- No KPI (like 75% CPU usage)
- Only safety margin
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### Scalability
- Current: 100,000 devices
- Target: 500,000 devices (5x scale)
- Approach: Reference system scaling

### Storage
- Multiple databases: Mongo, PostgreSQL, ScyllaDB
- All SSD-justified by IOPS calculations
- OS/Log storage: Separate consideration

### Network
- API app throughput
- CMS web throughput
- FW/LB with 1.2 safety factor

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **5x scale is aggressive**
   - Consider phased deployment
   - Monitor at 200K, 300K before full 500K

2. **CPU spec clarity is mandatory**
   - Model name + Cint2017 value
   - Reference link to SPEC benchmark
   - 3 Cint2017 = 1 vCPU assumption

3. **IOPS drives SSD decision**
   - Calculate per component (not aggregate)
   - MongoDB IOPS ≠ PostgreSQL IOPS
   - Document each separately

4. **FW/LB uses different safety factor**
   - Network: ×1.2 only
   - Don't apply KPI division
   - Different from server sizing methodology

5. **Namespace-level granularity**
   - Don't aggregate all K8S workers
   - Measure per service/namespace
   - Sum with cluster overhead

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 3 (nhiều yêu cầu chi tiết)  
**Vấn đề chính:** 5x scaling validation, IOPS calculation, multi-database sizing

**Đặc điểm hệ thống:**
- IoT platform: Smart home devices
- Multi-database: MongoDB, PostgreSQL, ScyllaDB
- K8S-based microservices
- Target: 500K devices (from 100K baseline)

**Khuyến nghị:**
- Validate 500K target with business planning
- Provide CPU SPEC benchmarks with links
- Calculate IOPS per database individually
- Use 1.2 for FW/LB (not server formula)
- Include namespace-level K8S metrics
- Create clear summary table with N+1 for each component