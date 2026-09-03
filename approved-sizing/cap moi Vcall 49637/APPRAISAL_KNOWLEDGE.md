# APPRAISAL KNOWLEDGE - VCALL (Wifi Calling)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG VCALL (WiFi Calling)  
**Mã PYC:** PYC-47827  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 3 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Xây mới hệ thống VCall hỗ trợ thoại qua DataWiFi  
**Đầu mối:** Dungbtk1  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét (3 rounds)

**Yêu cầu chính:**
1. **Scale:** 45,833 CCU cần business justification
2. **TPS:** 1000 TPS kết nối DRA/OCS
3. **Retention:** Log 24 tháng
4. **Virtualization:** Chia nhỏ <64GB RAM, 32 vCPU
5. **HBase:** Chia thành 5 VM
6. **SSD:** Tham khảo vendor docs (MongoDB, Redis, HBase, MySQL)
7. **IOPS:** Tính cụ thể trên server tham chiếu
8. **Reference:** Hệ thống Mocha VTM hiện tại

---

## 💡 TRI THỨC RÚT RA

### 1. VCall architecture breakdown

**VCall components (microservices):**
```
Application layer:
  - Call app: 500 CCU
  - API backend: 1000 CCU
  - XMPP server: 2000 CCU
  - CMS: 10 CCU
  - Charging: 1000 CCU
  - Load Balancer: 4000 CCU

Database layer:
  - MySQL: 2000 CCU
  - HBase: 2000 CCU (NOSQL)
  - MongoDB: 2000 CCU (document store)

Message queue:
  - RabbitMQ: 5000 CCU
  - Redis: 4000 CCU (cache)

Infrastructure:
  - Log tập trung: 10,000 CCU
```

### 2. Large-scale database distribution

**HBase cluster strategy:**
```
Reason to split into 5 VMs:
  - No single point of failure
  - Better load distribution
  - Easier maintenance
  - Viettel threshold: <64GB per VM

HBase nature:
  - NOSQL (Hadoop database)
  - Stores call records (CDRs)
  - Scales horizontally
  - RegionServer architecture
```

### 3. Serice-specific sizing (Mocha reference)

**Reference system sizing:**
```
For each service (using Mocha as baseline):
  - Call: Mocha Call server with CCU=500
  - API: Mocha API with CCU=1000
  - XMPP: Mocha Chat with CCU=2000
  - etc.

Methodology:
  1. Measure Mocha resource usage
  2. Calculate per-CCU consumption
  3. Multiply by target CCU
  4. Add safety factor (1.2)
  5. Add N+1 redundancy
```

### 4. SSD justification for each DB

**Vendor documentation reference:**
```
MongoDB:
  - Recommends SSD for production
  - Random I/O heavy workload
  - Journaling benefits from SSD

Redis:
  - In-memory but persists to disk
  - SSD recommended for snapshot performance
  - Read/write intensive

HBase:
  - Hadoop-based, random reads
  - SSD improves RegionServer performance
  - Optional but recommended for production

MySQL:
  - Traditional RDBMS
  - SSD beneficial for index-heavy queries
  - Transaction log performance
```

### 5. VoIP-specific considerations

**WiFi Call vs Regular Call:**
```
VCall特点:
  - Uses Data WiFi (not cellular)
  - Integrates with DRA/OCS (charging)
  - Requires XMPP for signaling
  - Media traffic: RTP/UDP

Bandwidth calculation:
  - Codec: G.711 (~64 Kbps) vs G.729 (~8 Kbps)
  - Overhead: 20% for IP/UDP/RTP headers
  - Concurrent calls affect LB sizing
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### Workload
- Total CCU: 45,833 (large scale)
- TPS to DRA/OCS: 1,000
- Log retention: 24 months

### Architecture
- 12+ microservices
- Call signaling via XMPP
- Charging via DRA/OCS integration
- Multiple databases (SQL + NoSQL)

### Virtualization
- Split large servers into <64GB VMs
- HBase: 5 VMs for distribution
- Enable better resource allocation

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Large CCU requires strong justification**
  - 45,833 is aggressive for new system
  - Need business forecast from KD
  - Consider phased rollout

2. **HBase needs cluster approach**
  - Don't put on single large server
  - 5 VMs = better distribution
  - Follow Hadoop best practices

3. **SSD justifies by workload type**
  - Random I/O: MongoDB, Redis → SSD
  - Sequential: Logs, backups → HDD
  - Calculate IOPS before deciding

4. **VoIP needs accurate codec sizing**
  - G.711 vs G.729 bandwidth difference
  - Multiple by concurrent calls
  - Include protocol overhead

5. **Reference system is Mocha**
  - Mocha already runs similar services
  - Measure current resource consumption
  - Extrapolate to new CCU targets

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** RẤT CAO  
**Số vòng PNX:** 3 (nhiều microservices cần validated)  
**Vấn đề chính:** Large CCU, multi-database sizing, SSD justification

**Đặc điểm hệ thống:**
  - WiFi Calling (VoIP over WiFi)
  - 12+ microservices architecture
  - Multiple databases (MySQL, MongoDB, HBase, Redis)
  - Integration with DRA/OCS (charging)

**Khuyến nghị:**
  - Validate 45.8K CCU with business
  - Use Mocha as reference baseline
  - Calculate IOPS for each DB type
  - Split HBase into 5-node cluster
  - Document codec choice for bandwidth