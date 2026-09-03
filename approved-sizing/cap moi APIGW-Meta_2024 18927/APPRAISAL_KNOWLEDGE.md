# APPRAISAL KNOWLEDGE - DỰ ÁN: API GATEWAY META (FACEBOOK AUTOFLEX)

**Mã PYC:** PYC-18927  
**Đầu mối yêu cầu:** Hoanglm9 (PTPM - Trung tâm CNTT)  
**Đầu mối thẩm định:** Khanhnd23 (Phòng Hệ thống)  
**Đơn vị phát triển:** Phần mềm Open Source - Gravitee  
**Mục đích sizing:** Triển khai tích hợp 700 TPS với đối tác Meta (Facebook Autoflex)  
**Quy mô:** 700 TPS  
**Trạng thái phản hồi:** 4 vòng (PNX v1→v2→v3→v4) - Đã ký duyệt

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ⚠️ **NHIỀU VÒNG PHẢN BIỆN (TRƯỜNG HỢP A+)**
- **Vòng 1 (PNX v1):** 8 lỗi về tài liệu (thiếu sở cứ, thông tin kết nối)
- **Vòng 2 (PNX v2):** 5 lỗi về tính toán (lỗi đơn vị, số liệu không khớp)
- **Vòng 3 (PNX v3):** Yêu cầu làm sạch cách chia tài nguyên
- **Vòng 4 (PNX v4):** ✅ Đã ký duyệt checklist

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG

### 1. LỖI ĐƠN VỊ TÍNH: KB/s SANG Mb/s
**Lỗi trong V2/V3:**
```
SAI: 35.000 KB/s = 35 Mb/s  ❌ (chia 1000, nhân 10)

ĐÚNG: 35.000 KB/s ÷ 1024 × 8 = 273.44 Mb/s ✅

Lặp lại nhiều lần với các con số khác.
```

**Bài học critical:**
- **KB → KB, MB → MB** (1024 conversion)
- **KB/s → Mb/s** = KB/s ÷ 1024 × 8 (bit, not Byte)
- Common mistake: Chia 1000 thay vì 1024
- Verify: 1 MB = 1024 KB, 1 Mb = 8 Mb (megabit)

### 2. TÍNH TOÁN BĂNG THÔNG UPLOAD CHO 700 TPS
**Đề xuất ban đầu (có lỗi):**
```
Upload speed = 10KB × 700 / 0.01s
             = 700.000 KB/s
             = 683 Mb/s  ❌ (lỗi: chia 1000, nhân 10)
```

**Corrections:**
```
ĐÚNG: Upload speed = 10KB × 700 / 0.01s
                  = 700.000 KB/s
                  = 700.000 ÷ 1024 × 8
                  = 5.46875 Mb/s

Nhưng sizing ultimate says: 0.32 Gbps (320 Mbps)
→ Là cho TPS cả hệ thống, không chỉ upload
```

**Bài học:**
- Tính per-request: 10KB per request
- Tính per-second: 700 requests/s × 10KB = 7.000 KB/s = 6.83 MB/s
- Total system bandwidth: 0.32 Gbps (cho cả upload + download + overhead)

### 3. KÍCH THƯỚC REQUEST/RESPONSE CẦN SỞ CỨ THỰC TẾ
**Yêu cầu PNX:**
```
"Bổ sung sở cứ cho Giá trị định cỡ 700"

"Bổ sung sở cứ cho Với 1 request/response ~ 0.35KB/1 giao dịch"

"Bổ sung sở cứ cho Một giao dịch api trung bình là 10KB"

"Bổ sung sở cứ cho Thông lượng HSDP là 1.2 chứ không phải 1.1"
```

**Cách làm đúng:**
- ✅ Integrate test with Meta để đo request/response size
- ✅ Document: 0.35KB/response, 10KB/api transaction
- ✅ Screenshot IP từ hệ thống test
- ✅ Hệ số dự phòng: HSDP 1.2 (not 1.1)

**Bài học:**
- Mọi con số phải có **evidence** (test results, logs)
- Không dùng "rule of thumb" cho API Gateway sizing
- Hệ số dự phụngr có thể khác 1.1 tùy workload

### 4. CHI TIẾT KHI CHIA TÀI NGUYÊN THÀNH N+1 SERVERS
**Vấn đề:**
```
Tổng tài nguyên: CPU 6,16 Cint, RAM 282 GB, HDD 1546 GB

Nhưng chia 4 server lại:
- CPU: 1,5 Cint per server (mất 0,16 Cint?)
- RAM: 64 GB per server (×4 = 256 GB, mất 26 GB?)
- HDD: 600 GB per server (×4 = 2.400 GB, zí hơn 1546 GB?)

PNX comments:
"Cpu 6,16 ram 282 hdd 1546 mà sao chia 4 lại nhiều thế.
Lập bảng giá trị đề xuất cụ thể."
```

**Giải pháp V4:**
```
N=4 servers (3 active + 1 backup, N+1 model)
CPU per server: 1,5 Cint ÷ 0,75 × 1,1 = 2,2 Cint ≈ 4 vCPU
RAM per server: 64 GB
HDD per server: 400 GB (data) + 200 GB (app) = 600 GB

Để đảm bảo N+1:
- 3 servers: 1,5 Cint each (4,5 Cint total)
- 1 server: 1,5 Cint (backup)
- Total: 6 Cint (chừa 6,16 Cint requirement)
```

**Bài học:**
- Chia resource phải transparency: Show breakdown before/after
- N+1 means N active + 1 backup (total N+1 servers)
- Per-server resource = Total ÷ (N+1) ÷ KPI × Ksaiso
- Round UP to practical values (e.g., 1,5 Cint ≈ 4 vCPU)

### 5. HDD VERSUS SSD CHO API GATEWAY
**Yêu cầu:**
```
"Phần storage chỉ cần ổ HDD thông thường mặc định 10 krpm"

"Storage: Sử dụng HDD thông thường. Tốc độ vòng quay >= 10 krpm."
```

**Justification:**
- API Gateway là CPU-bound, NOT I/O-bound
- Logs, configs, metrics stored on HDD OK
- Database (MySQL) might need SSD but NOT API Gateway servers

**Bài học:**
- API Gateway servers: HDD sufficient (read-mostly write logs)
- Application servers: HDD OK for majority cases
- Database servers: SSD required for I/O-intensive workloads
- Always consider workload type (CPU vs I/O bound) before storage decision

### 6. MÔ HÌNH DEPLOYMENT: DOCKER SWARM + ELASTICSEARCH
**Requirements:**
```
"Do áp dụng mô hình cài đặt docker swarm và elastic search cluster
nên yêu cầu tối thiểu 3 server để đáp ứng mô hình cài đặt"
```

**Architecture:**
```
Docker Swarm:
- 3 managers (control-plane)
- Multiple workers (run containers)
- Requires odd number for quorum

Elasticsearch:
- 3 nodes minimum for cluster
- Master-eligible nodes: 3
- Data nodes: 3 or more

Hence: Minimum 3 servers for both Swarm + ES
```

**N+1 sizing:**
```
Active: 3 servers
Backup: 1 server
Total: 4 servers
```

**Bài học:**
- Distributed systems have minimum node requirements
- Docker Swarm: 3 managers (for Raft)
- Elasticsearch: 3 master-eligible nodes
- Cannot scale down below minimum for HA
- Remember: Even if resource requirements low, architecture dictates minimum

### 7. SỐ LIỆU TÍNH TOÁN PHÍA TRÊN VÀ PHÍA DƯỚI KHÁC NHAU
**Yêu cầu PNX:**
```
"Số liệu tính toán phía trên và dưới đang khác nhau"
```

**Đây là vấn đề về consistency trong sizing document:**
- Trang 8 nói X, Trang 9 nói Y
- Tổng resource không khớp với per-node resource
- Need cross-verification across document

**Giải pháp:**
- Single source of truth: Create "Bảng tổng hợp đề xuất" at end
- All calculations should reference this table
- Document step-by-step to show how X leads to Y

**Bài học:**
- Keep calculations consistent across entire document
- Use tables for summary, reference from all pages
- Cross-check: Total = Per-node × Number of nodes
- Document assumptions explicitly (e.g., 4 servers = N+1 model)

### 8. RAM VERSUS CPU: CINT VERSUS VCPU
**Confusion:**
```
"Cpu này là cint hay vcpu"
```

**Clarification needed:**
- **Cint:** SPEC CPU 2017 benchmark score
- **vCPU:** Virtual CPU (e.g., in VMware, KVM)
- Conversion rule of thumb: 1 vCPU ≈ 1-2 Cint (depends on CPU generation)

**In this sizing:**
- Total CPU needed: 6,16 Cint
- Per server: 1,5 Cint
- Converted to vCPU: 4 vCPU per server
- Implies: 1 vCPU ≈ 0,375 Cint (high-performance CPU)

**Bài học:**
- Always document: Cint vs vCPU
- Provide conversion ratio (e.g., SPEC Cint 2017 score per vCPU)
- Different CPUs have different Cint/vCPU ratios
- Reference SPEC scores: https://www.spec.org/cpu2017/

### 9. LOG STORAGE PLANNING (833,25 GB/MONTH)
**Calculation:**
```
Log size per month:
= 20,2 GB/day × 30 days × 1,1 (buffer) ÷ 0,8 (KPI)
= 833,25 GB/month

Nhưng hỏi:"Khối lượng log... không thấy dùng vào việc gì?"
```

**Explanation:**
- Logs stored on each server (200 GB for OS + app + logs)
- Logs also replicated to centralized log system (ELK stack?)
- Total 833 GB/month distributed across 4 servers = ~208 GB per server

**Bài học:**
- Document log storage strategy clearly
- Distinguish local log vs centralized log (ELK, Loki, etc.)
- Mention retention policy (how long logs kept)
- Account for log growth in sizing

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### SERVER CONFIGURATION PER NODE (N+1 Model: 4 Servers)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 4 vCPU | ~1,5 Cint 2017 |
| **RAM** | 64 GB | Per server |
| **HDD** | 600 GB | 400GB data + 200GB OS/app |
| **Storage** | HDD, ≥ 10 krpm | Không cần SSD cho APIGW |
| **Architecture** | Docker Swarm + Elasticsearch | Minimum 3 nodes |
| **HA Mode** | N+1 (3 active, 1 backup) | |

**Cluster requirements:**
- Docker Swarm: 3 managers
- Elasticsearch: 3 master-eligible nodes
- Combined: Minimum 3 servers (4th for backup)

### NETWORK INFRASTRUCTURE

| Component | Thông số | Ghi chú |
|-----------|---------|---------|
| **Firewall** | ≥ 0,32 Gbps (320 Mbps) | With TPS=700 |
| **Load Balancer** | ≥ 0,32 Gbps (320 Mbps) | Active-Active or Active-Standby |
| **TPS** | 700 | Target for Meta integration |

**DETAILED CALCULATION:**
```
Upload bandwidth per request: 10 KB
TPS: 700 requests/s

Per-second: 700 × 10 KB = 7.000 KB/s = 6,83 MB/s
Per-second overhead: 6,83 × 1,2 = 8,2 MB/s

Total system bandwidth: 0,32 Gbps = 320 Mbps
→ Accounts for both directions + overhead + multiple services
```

### STORAGE LOG PLANNING

| Metric | Giá trị | Ghi chú |
|--------|---------|---------|
| **Log generation** | 20,2 GB/day | Measured |
| **Monthly logs** | 833,25 GB | With 20% headroom |
| **Per server** | ~200 GB | Distributed across 4 servers |
| **Local retention** | 1-3 months | Before rotation |
| **Centralized log** | ELK/Loki (separate sizing) | |

---

## 🎯 KEY LEARNING (SUMMARY)

1. **Lỗi đơn vị tính:** KB/s → Mb/s cần chia 1024, then × 8
2. **Evidence required:** Test integration với Meta để đo request size
3. **Transparency:** Chi tiết resource breakdown khi chia N+1
4. **Minimum nodes:** Docker Swarm (3) + Elasticsearch (3) = minimum 3
5. **HDD sufficient:** API Gateway không cần SSD (I/O thấp)
6. **Consistency:** Single source of truth cho calculations
7. **CPU vs vCPU:** Document SPEC Cint conversion clearly
8. **Log storage:** Plan from beginning (833 GB/month)
9. **Hệ số dự phòng:** HSDP 1.2 (not always 1.1)
10. **Ký checklist:** Bắt buộc checklist signed before sizing approval

---

## 📝 CHECKLIST SIZING CHO API GATEWAY

### 1. Unit Conversion
- [ ] Verify KB → MB, MB → GB (÷ 1024)
- [ ] Verify KB/s → Mb/s (÷ 1024 × 8)
- [ ] Document all conversions
- [ ] Double-check arithmetic

### 2. Evidence Gathering
- [ ] Integrate test with external partner (Meta)
- [ ] Measure actual request/response sizes
- [ ] Screenshot system metrics
- [ ] Document test methodology

### 3. Resource Allocation (N+1 Model)
- [ ] Calculate total resources first
- [ ] Determine N (active servers)
- [ ] Add 1 backup server
- [ ] Show breakdown: Total = Per-node × (N+1)

### 4. Storage Planning
- [ ] HDD vs SSD decision (justify)
- [ ] Log growth rate per day/month
- [ ] Local vs centralized log strategy
- [ ] Retention policy

### 5. Distributed Systems
- [ ] Minimum nodes for quorum (Docker Swarm: 3)
- [ ] Minimum nodes for cluster (Elasticsearch: 3)
- [ ] Cannot scale below minimum for HA
- [ ] N+1 means N active + 1 backup

### 6. Documentation
- [ ] Cint vs vCPU conversion documented
- [ ] All assumptions explicit
- [ ] Single source of truth table
- [ ] Cross-check calculations across document

---

**Người tạo:** AI Assistant  
**Ngày:** 2024  
**Phiên bản:** 1.0  
**Trạng thái:** ✅ Hoàn thành

**Ghi chú:** Đây là ví dụ điển hình cho **lỗi đơn vị tính** và **chi tiết resource allocation**. Rất nhiều bài học cho việc làm sạch calculations và transparency.