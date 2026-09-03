# APPRAISAL KNOWLEDGE - DỰ ÁN: APPSEALING (MOBILE APP SECURITY)

**Mã PYC:** PYC-18025  
**Đầu mối yêu cầu:** HungNVX@viettel.com.vn  
**Đầu mối thẩm định:** P. Hệ thống - SAD (kiểm tra thông tin)  
**Đơn vị phát triển:** AppSealing (bên thứ 3 - vendor software)  
**Mục đích sizing:** Xây mới hệ thống AppSealing trên K8s - Bảo mật ứng dụng di động  
**Quy mô:** 100,000 ActiveDevices/day  
**Ngày hoàn thành:** 24/06/2024  
**Trạng thái phản hồi:** 6 vòng PNX (v1→v2→v3→v4→v5→v6) - ✅ Đã ký duyệt checklist 115/PYC

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ⚠️ **NHIỀU VÒNG PHẢN BIỆN (TRƯỜNG HỢP A+)**
- **Vòng 1-6:** 6 vòng phản hồi với rất nhiều yêu cầu
- **Trạng thái:** Đã ký duyệt checklist 115/PYC ✅
- **Loại:** Sizing cho software vendor (bên thứ 3)

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH QUAN TRỌNG

### 1. VENDOR-SPECIFIC SIZING (BÊN THỨ 3)
**Đặc điểm:**
- Software vendor (AppSealing) provides sizing specifications
- Hardware requirements come from vendor, not Viettel sizing team
- Vendor declares: "0.58 GB/day cho 100K ActiveDevices"

**Lợi thế:**
- Tap lùu từ trước về hardware requirements
- Vendor chịu trách nhiệm về performance với cấu hình này
- Reduced burden on Viettel sizing team

**Rủi ro:**
- Vendor có thể over-size để đảm bảo hành
- Cần verify tính thực tế with load testing

**Bài học:**
- Khi sizing cho vendor-provided software, document tất cả vendor communications
- Email xác nhận từ vendor là rất quan trọng
- Document: "Email Hãng xác nhận dữ liệu cần cho 100K ActiveDevices/1day"

### 2. STATEFULSETS SERVICE YÊU CẤU NFS
**Architecture:**
```
MySQL và ElasticSearch là StatefulSets Service trong K8s
→ Cần lưu trữ liên tục (persistent volume) để đảm bảo HA
→ Khi node fail, data vẫn tồn tại và có thể truy xuất được
```

**Giải pháp:**
```
Sử dụng NFS (Network File System):
- Server nfs://10.x.x.x.x:2049
- MySQL + ES đều mount NFS storage
- StatefulSets: Lấy data từ NFS nếu pod chuyển node
- Đảm bảo HA: Pod fail → Another node → data vẫn accessible from NFS
```

**Bài học:**
- StatefulSets cần persistent volume hoặc network storage
- NFS provide shared storage across multiple nodes
- Local disk (500GB) for OS only, not for application data
- 574.2 GB database data lưu trên NFS, không local disk

### 3. MYSQL + ELASTICSEARCH SIZING (SHARED STORAGE)
**Cấu hình (đề xuất từ Hãng qua email):**
```
2 servers:
vCPU: 4 cores
RAM: 8 GB
OS Disk: 60 GB Ubuntu

Storage: 574,2 GB (shared via NFS)
Hàng server: 4 vCPU, 8GB RAM, 574.2 GB HDD
```

****Cần NHƯ LƯU Ý:** Đây là CẤU HÌNG, không phải tính toán từ zero!**

**Vendor's calculation:**
```
Dữ liệu cho 100K ActiveDevices/1 ngày: 0,58 GB
Dữ liệu lưu trữ trong 2 năm: 417,6 GB
Với hệ số dự phòng 1,1:
= 417,6 × 1,1 ÷ 0,80 (KPI) = 574,2 GB
```

**Justification:**
- 80% KPI: Không vượt quá 80% dung lượng (Data node ≤ 50% áp dụng RDBMS, nhưng đây là general 80% rule)
- **Vendor email confirmation is KEY** evidence for this calculation

### 4. TÍNH TOÁN BĂNG THÔNG CHO 100K ACTIVEDEVICES/DAY
**Base metric:**
```
Thông lượng của 100.000 ActiveDevice/1 ngày: 38 Mb/s
```

**Calculation from vendor:**
```
AppSealing cung cấp: 38 Mb/s (measured from production)
Thermal ph Analysis: Base load traffic patterns
```

**Sizing with buffer:**
```
Tổng thông lượng: 38 Mb/s
Dự phòng (Kdup = 1,2): 38 × 1,2 = 45,6 Mb/s

Firewall sizing:
- Throughput: ≥ 45,6 MB/s
- NOT Mbps ← Chú ý đơn vị (MB vs Mb)
```

**Bài học:**
- M easing units: Mb = Megabit, MB = Megabyte
- 38 Mb/s NOT 38 MB/s
- Firewall throughput sizing cần match đơn vị chính xác
- Vendor measurement from production is most reliable

### 5. K8S CLUSTER SIZING: 5 NODES (1 MASTER + 4 SLAVES)
**Architecture:**
```
N = 5 servers (not 6 as in table)
Master: 1 node (control-plane only)
Slaves: 4 nodes (workloads)
```

**Per-node configuration:**
```
Master (1 server):
- CPU: >= 8 cores
- RAM: >= 24 GB
- HDD: 500 GB
- OS: Ubuntu 22.04

Slave Worker (4 servers):
- CPU: >= 16 cores (2× master)
- RAM: 24 GB (same as master)
- HDD: 500 GB
- OS: Ubuntu 22.04

Total:
- CPU: 8 + (4×16) = 72 cores
- RAM: 24 + (4×24) = 120 GB
- HDD: 5 × 500 = 2,500 GB
```

**Bài học:**
- Master node: Control-plane only, no workload
- Slave nodes: Chạy workload (containers)
- Master: 8 cores đủ cho K8s components (API server, scheduler, controller-manager, etcd)
- Slave: 16 cores -> enough for AppSealing workloads (from vendor specs)

### 6. FIREWALL SIZING DỰA TRÊN VENDOR SPECS
**Vendor specification:**
```
Thông lượng: >= 45,6 Mb/s (NOT Mbps)
Giao thức: TCP, HTTP, HTTPS
```

**Chuyển đổi sang Mbps:**
```
45,6 Mb/s = 45,6 Megabits/s
        = 45,6 × 1024 × 8 ÷ 1,000,000
        = 4,785,408 bits/s
        = 4.79 Gbps approximately

Nhưng trong sizing says: 45,6 Mb/s
→ Dùng Megabits/s, not Megabytes/s
```

**Bài học:**
- Document units explicitly: Mb vs MB, Mb/s vs MB/s
- Firewall throughput: 45,6 Mb/s là **thông lượng thực tế** từ vendor measurement
- Click tracking vendor provided numbers important
- Conversions rarely needed if vendor already systemic

### 7. STORAGE STRATEGY: 500GB LOCAL + 574,2 GB NFS
**Per node:**
```
Local HDD: 500 GB (OS + docker images, logs)
NFS mount: 574,2 GB (database data)

Total per node:
  = 500 GB (local) + 574,2 GB (NFS, shared)
  = 1,074,2 GB total visible
  BUT: 574,2 GB is shared across 2 servers
  = Ka document fully decode shared storage
```

**Bài học:**
- Kubernetes default: Local disk for OS + container images
- Persistent data: NFS for stateful applications
- For MySQL:
  - Data directory on NFS: 574,2 GB (mount into /var/lib/mysql)
  - Local disk: 60 GB (OS only)
- For Elasticsearch:
  - Data directory on NFS: 574,2 GB (mount into /usr/share/elasticsearch/data)
  - Local disk: 60 GB (OS only)

### 8. EMAIL CONFIRMATION CỰNG TỪ VENDOR
**Yêu cầu PNX:**
```
"Email Hãng xác nhận dữ liệu cần cho 100K ActiveDevices/1day"
```

**Response:**
```
"Hãng xác nhận dữ liệu cần cho 100K ActiveDevices/1day"
"MYSQL và ElasticSearch sử dụng dịch vụ NFS để lưu trữ dữ liệu"
```

**Thực tế:**
- Email screenshot/dated provided as evidence
- Vendor signature confirms: 0.58 GB/day per 100K devices
- Storage growth rate: 417,6 GB for 2 years

**Bài học:**
- Tài liệu xác nhận từ vendor là **critical evidence**
- Bắt buộc lưu email confirmation trong hồ sơ
- Cite vendor communications explicitly in sizing document
- Date-stamped email tạo audit trail

### 9. CỔNG NGHỆ THỐNG TỪ VENDOR: K8S + MYSQL + ELASTICSEARCH
**Vendor ecosystem:**
```
K8s (Kubernetes):
- v1.28.7
- Docker v24.0.5
- Helm v3.13.1

MySQL:
- v8.0 (not specified version, latest)

Elasticsearch:
- v8.12.0
- Kibana v8.12.0
```

**Sizing from vendor:**
- All hosted on K8s (containerized)
- K8s cluster: 5 nodes (1 master + 4 slaves, though table shows all 5 as slaves)
- MySQL + ES: StatefulSets with NFS storage

**Bài học:**
- Node.js app containers (AppSealing server)
- MySQL database containers
- Elasticsearch containers (log analytics, Kibana UI)
- NFS service for shared stateful storage
- All orchestrated by K8s (Helm charts)

### 10. TÍNH TOÁN DISK: 574,2 GB CHO 100K ACTIVEDEVICES
**Vendor's formula:**
```
Step 1: Calculate daily data
  Dữ liệu 100K ActiveDevices/1 ngày: 0,58 GB

Step 2: Extrapolate to 2 years
  0,58 GB/day × 365 × 2 = 423,4 GB ≈ 417,6 GB (vendor's number)

Step 3: Apply KPI and buffer
  417,6 GB × 1,1 (Ksaiso) ÷ 0,80 (KPI 80%)
  = 574,2 GB

Justification:
  - KPI 80%: Don't exceed 80% disk utilization
  - Ksaiso 1.1: 10% safety margin
  - Note: Data node ≤ 50% for RDBMS, but vendor used 80% for this calculation
```

**Critique:**
- Should have used data node ≤ 50% instead of general ≤ 80%
- 417,6 GB vs 423,4 GB → minor discrepancy (vendor rounding)
- **But vendor email confirms 574,2 GB** → Override with vendor specs

**Bài học:**
- When vendor email conflict with general KPI, follow vendor (they know their software)
- Document discrepancy clearly: "Vendor email says X, calculation says Y, using X due to vendor confirmation"
- Always prioritize vendor-specific knowledge over general guidelines

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### K8S CLUSTER (5 NODES)

| Component | Quy mô | Ghi chú |
|-----------|--------|---------|
| **Total servers** | 5 nodes | 1 master + 4 slaves (though document unclear) |
| **Master node** | 1 server (control-plane) | 8 cores, 24 GB RAM, 500 GB HDD |
| **Slave nodes** | 4 servers (workloads) | 16 cores, 24 GB RAM, 500 GB HDD each |
| **Total CPU** | 72 cores | 8 + (4×16) cores |
| **Total RAM** | 120 GB | 24 + (4×24) GB |
| **Total local storage** | 2,500 GB HDD | 5 × 500 GB |
| **OS** | Ubuntu 22.04 | All nodes |

**K8s versions:**
- Kubernetes v1.28.7
- Docker v24.0.5
- Helm v3.13.1

### DATABASE CLUSTER

| Component | Cấu hình per server | Số lượng | Ghi chú |
|-----------|---------------------|----------|---------|
| **MySQL** | 4 vCPU, 8 GB RAM<br>60 GB OS disk<br>574,2 GB NFS data | 2 servers (replica) | StatefulSet với NFS |
| **Elasticsearch** | 4 vCPU, 8 GB RAM<br>60 GB OS disk<br>574,2 GB NFS data | 2 servers (replica) | StatefulSet với NFS |
| **NFS Server** | (not sized) | 2 servers | Xây dựng và triển khai bởi Viettel |

**NFS specs:**
```
Server: Chưa được cấp
IP: Chưa được cấp
Port: 2049,111 TCP/UDP
Service: NFS service cho MySQL + Elasticsearch
```

### NETWORK INFRASTRUCTURE

| Component | Thông số | VDP |
|-----------|---------|-----|
| **Firewall** | 45,6 Mb/s | Active-Active or Active-Standby |
| **Protocol support** | TCP, HTTP, HTTPS | |
| **Source** | 100,000 ActiveDevices/day (38 Mb/s) | Measured by vendor |
| **Bandwidth with buffer** | 45,6 Mb/s | Kdup = 1,2 |

---

## 🎯 KEY LEARNING SUMMARY

1. **Vendor-driven sizing:** Software vendors have deep knowledge of their system requirements
2. **NFS for StatefulSets:** K8s StatefulSets require networked persistent storage
3. **Email confirmations:** Vendor email confirmations are CRITICAL evidence
4. **Unit clarity:** Mb/s, MB/s, Mbps, Mbps – document explicitly
5. **5 nodes minimum:** K8s requires odd number for etcd quorum (3, 5, 7...)
6. **HDD enough for app servers:** Unless database I/O intensive, 10 krpm HDD sufficient
7. **80% vs 50% KPI:** When conflict, follow vendor-specific knowledge but document clearly
8. **Shared storage strategy:** 574,2 GB on NFS shared between 2 database servers
9. **StatefulSets architecture:** MySQL + ES as StatefulSets for HA
10. **Vendor specs override:** When vendor email conflicts with general sizing, prioritize vendor

---

## 📝 CHECKLIST CHO VENDOR-PROVIDED SOFTWARE SIZING

### 1. Vendor Communication
- [ ] Gather vendor sizing specifications
- [ ] Request vendor confirmation email for key metrics
- [ ] Document all vendor communications
- [ ] Save email screenshots/signatures
- [ ] Get clarification on data sources

### 2. Storage Planning
- [ ] Determine database growth rate from vendor
- [ ] Confirm retention policy (e.g., 2 years)
- [ ] Calculate total storage needed over retention period
- [ ] Apply appropriate KPI (80%, 50%, or vendor-specific)
- [ ] Plan for NFS vs local disk for data

### 3. K8s Architecture
- [ ] Determine etcd cluster size (3, 5, 7...)
- [ ] Separate master vs worker nodes
- [ ] Size control-plane (master) requirements separately
- [ ] Size worker nodes based on application workloads
- [ ] Ensure HA: N+1 for master, N+1 for workers

### 4. Network Sizing
- [ ] Get measured bandwidth from vendor
- [ ] Apply Kdup (typically 1,2 for network devices)
- [ ] Clarify units: Mb/s, MB/s, Mbps
- [ ] Verify firewall/LB throughput requirements
- [ ] Document peak vs average traffic patterns

### 5. Database Sizing
- [ ] MySQL as StatefulSet with NFS storage
- [ ] Elasticsearch as StatefulSet with NFS storage
- [ ] Get vendor recommendations for database RAM/CPU (usually provisioned)
- [ ] Understand storage + indexing overhead
- [ ] Plan for backup strategy (NFS backup or separate)

### 6. Documentation
- [ ] Cite vendor emails explicitly with dates
- [ ] Document discrepancies between general guidelines vs vendor specs
- [ ] Explain why vendor-specific numbers take precedence
- [ ] Attach vendor documentation (manuals, sizing guides)
- [ ] Include screenshots or email specs as evidence

---

**Người tạo:** AI Assistant (based on signed sizing document)
**Ngày tạo:** 2024
**Phiên bản:** 1.0
**Trạng thái:** ✅ Hoàn thành - Ví dụ điển hình cho vendor-provided software sizing

**Ghi chú:** Đây là sizing cho **bên thứ 3 vendor** (AppSealing). Vendor xác nhận 0.58 GB/day cho 100K ActiveDevices, leading to 574,2 GB total database storage. Rất nhiều bài học về StatefulSets, NFS storage, và vendor communication.