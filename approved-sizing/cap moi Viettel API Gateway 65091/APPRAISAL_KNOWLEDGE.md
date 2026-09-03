# APPRAISAL KNOWLEDGE - VIETTEL API GATEWAY

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** VIETTEL DATA API GATEWAY  
**Mã PYC:** PYC-65091  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Thẩm định sizing ELK, MariaDB cho Viettel Data API Gateway  
**Đầu mối:** Duclv32  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (P.CNHT)

**Yêu cầu chính:**
1. **ĐBQT = DR mandatory:** Bắt buộc phải có DR
2. **300 CCU:** Cần bổ sung sởffff chỉ
3. **Storage:** Bỏ SSD, chỉ dùng HDD
4. **Business flow:** Bổ sung luồng nghiệp vụ
5. **Reference:** ELK, DB tham chiếu
6. **Virtualization limit:** CPU<32 vCPU (96 Cint), RAM<64GB
7. **LB details:** concurrent session, peak, duration, bandwidth
8. **Notation:** Dùng `=` không dùng `>=`

---

## 💡 TRI THỨC RÚT RA

### 1. API Gateway architecture

**Viettel Data API Gateway:**
```
Components:
  - API Gateway (Kong/WSO2/etc)
  - ELK Stack (Elasticsearch + Logstash + Kibana)
  - MariaDB (configuration/metadata)

Workload:
  - 300 CCU
  - API request/response handling
  - Logging and monitoring
  - Configuration storage
```

### 2. HDD acceptable for API Gateway

**Why HDD works:**
```
API Gateway I/O pattern:
  - Primarily network I/O (not disk)
  - Logs rotate frequently (sequential writes)
  - Configuration data relatively small

ELK considerations:
  - Hot data: Could use SSD
  - Warm data: HDD acceptable
  - Cold data: HDD (archive)

MariaDB:
  - If read-heavy, HDD may suffice
  - Write-heavy might benefit from SSD
```

### 3. Virtualization thresholds

**Viettel standards:**
```
CPU: <32 vCPU (96 Cint2017)
RAM: <64 GB

Reasons:
  - Easier VM migration
  - Better resource allocation
  - Avoid over-provisioning

If sizing exceeds:
  - Split into multiple VMs
  - Each under the threshold
```

### 4. Load balancer sizing details

**Required metrics:**
```
Concurrent sessions:
  - Active connections at once
  - Example: 300 CCU = 300 simultaneous

Peak concurrent:
  - Maximum expected surge
  - Example: 1.5x normal = 450

New concurrent rate:
  - New connections per second
  - Example: 10 new/sec

Session duration:
  - Average connection lifetime
  - Example: 5 minutes

Bandwidth calculation:
  - Per-session bandwidth × CCU
  - Include protocol overhead
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System profile
- Type: API Gateway for Viettel Data
- CCU: 300
- Components: Gateway, ELK, MariaDB

### Virtualization
- CPU limit: <32 vCPU (96 Cint)
- RAM limit: <64 GB
- Use HDD (not SSD)

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **API Gateway is network-intensive**
  - Disk I/O less critical
  - HDD often sufficient
  - Focus on throughput, not storage

2. **300 CCU needs justification**
  - Document source of traffic forecast
  - Include growth projections
  - Reference current similar systems

3. **Virtualization thresholds matter**
  - Keep under 32 vCPU, 64GB RAM
  - Split into multiple VMs if needed
  - Improves resource utilization

4. **ELK can use tiered storage**
  - Hot data on SSD (optional)
  - Warm/cold on HDD
  - Cost-effective approach

5. **LB sizing requires detail**
  - Not just total CCU
  - Need concurrent, peak, new rates
  - Session duration affects connection pool

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (API Gateway sizing)  
**Vấn đề chính:** CCU justification, HDD vs SSD, virtualization limits

**Đặc điểm:**
  - API Gateway for data services
  - ELK + MariaDB backend
  - 300 CCU workload
  - HDD storage acceptable