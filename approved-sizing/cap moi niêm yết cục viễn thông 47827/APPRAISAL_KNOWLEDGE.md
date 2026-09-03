# APPRAISAL KNOWLEDGE - NIÊM YẾT CỤC VIỄN THÔNG

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG NIÊM YẾT CỤC VIỄN THÔNG  
**Mã PYC:** PYC-47827  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Hienlt15  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23

**Yêu cầu chính:**
1. **K8S microservices:** Need reference system info for each module
2. **Storage standard:** 150GB for log + code (MTA + OS)
3. **Import workload:** 7M records max, process by batch 20,000
4. **DB sizing:** 10GB buffer cache, 0.000362447 Cint/user
5. **Safety factor:** Only HSDP = 1.2 (not KPI)
6. **RAM >64GB:** Can split for virtualization?

---

## 💡 TRI THỨC RÚT RA

### 1. K8S microservice sizing - Per-module baseline

**Components:**
- K8S Master: 4 CPU, 8GB RAM
- Application pods: CCU 40,000 baseline
- Logging, UAA, Web App, Gateway, Common (Import, Report), LB

**Strategy:**
```
Each module needs:
1. Reference system specs
2. Current load measurement
3. Scaling factor to 40K CCU

Default storage: 150GB (log + code + OS)
```

### 2. HSDP (Hệ số dự phòng) = 1.2 only

**Important:**
```
For database sizing:
- KPI NOT used for DB in this case
- Only HSDP = 1.2 applied
- Reason: DB sizing uses reference system + linear scale

Formula:
  DB_Resource = Baseline_DB × Scale_Factor × 1.2
```

### 3. Import batch processing

**Workload:**
- Max 7M records per import
- Batch size: 20,000 records
- Need to handle: 7M / 20K = 350 batches

**Sizing consideration:**
```
Peak memory for batch:
  - 1000 numbers test: 14 MB RAM
  - Extrapolate to 20K: 14 MB × 20 = 280 MB/batch
  - With safety buffer: ~400-500 MB per worker
```

### 4. Database growth calculation

**Per-user data:**
```
Action logs: 6 records/user × 4KB = 24 KB/user
Subscriber info: 6 × 4KB = 24 KB/user

One posting cycle (7M subscribers):
  Records = 7M × 6 × 2 = 84M records
  Storage = 84M × 4KB = 336 GB
```

**Annual growth:**
```
100 posting cycles/year
Index buffer: 10GB per database
Content articles: 20GB/year
Total: ~336GB + 30GB = ~366 GB/year
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Baseline: E-invoicing system
- CCU: 40,000
- Per user: 0.000362447 Cint
- DB buffer: 10GB per database
- Storage per server: 150GB (default)

### Module breakdown
- K8S Master: 4 CPU, 8GB
- Multiple microservice pods
- Each pod: Scaled to handle 40K CCU

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Microservices need per-module sizing**
   - Don't aggregate all pods
   - Each module: Reference system + scaling

2. **HSDP ≠ KPI**
   - HSDP = 1.2 (safety margin)
   - KPI = Resource threshold (75%, 90%)
   - Sometimes use HSDP only, not KPI

3. **Import batch affects memory**
   - Test with 1000 → extrapolate to 20K
   - Linear scaling acceptable for batch operations

4. **Storage growth tied to business cycle**
   - 100 posting batches/year regular
   - 7M subscribers each time
   - Plan for peak, not average

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 1 (nhiều module K8S)  
**Vấn đề chính:** K8S microservice sizing, reference system requirements

**Đặc điểm:**
- K8S-based microservices architecture
- Electronic billing reference
- High periodic load (7M record imports)