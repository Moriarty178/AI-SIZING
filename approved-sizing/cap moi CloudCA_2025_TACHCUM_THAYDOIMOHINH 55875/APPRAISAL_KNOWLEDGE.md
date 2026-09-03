# APPRAISAL KNOWLEDGE - CLOUDCA 2025 TẠCH CỤM THAY ĐỔI MÔ HÌNH

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** VIETTEL CLOUD-CA - Tách cụm thay đổi mô hình  
**Mã PYC:** PYC-55875  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Tuyenvm  
**Mục đích:** Bổ sung tài nguyên theo mô hình mới  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (Phòng Công nghệ Hệ thống)

#### 6 Yêu cầu chỉnh sửa:

1. **Virtualization DB cluster:**
   - Cụm quản lý Database RAM 256GB có chia <= 64GB để ảo hóa được không?
   - **Câu hỏi:** Single large server hay multiple smaller VMs?

2. **Cú pháp bảng tổng hợp:**
   - Bỏ dấu ">=" trong bảng tổng hợp
   - Chỉ dùng "=" để ghi giá trị chính xác

3. **DB Storage division inconsistency:**
   - **Lỗi logic:** Storage tính tổng cho 3 server, nhưng chia lại theo cụm với server giống nhau
   - Giải thích lý do storage của DB chỉ chia 5, không chia 15
   - **Vấn đề:** Tính toán ban đầu: chia theo 3 server
   - **Phân chia cuối:** chia theo cụm, các server giống nhau

4. **Maxscale node count:**
   - Giải thích lý do chọn 10 node Maxscale
   - Có phải là over-provisioning?

5. **Redis cluster sizing:**
   - Giải thích chọn 9 nodes cho Redis
   - Đây là recommendation hay minimum?
   - Minimum cũng có thể chạy được rồi?

6. **Load Balancer sizing:**
   - Giải thích: Đang tính LB dựa trên thông tin của những server nào?
   - LB đang giao tiếp với hệ thống hay network nào ở bên ngoài?

---

## 💡 TRI THỨC RÚT RA

### 1. Large RAM vs Virtualization Trade-off

**Vấn đề:** Database cluster với 256GB RAM

**Scenario:** 
- Cụm DB quản lý với 256GB RAM
- Câu hỏi: Chia thành 4 VMs 64GB hay giữ 1 server 256GB?

**Database workloads - đặc biệt:**

**Ưu điểm Single Large Server:**
- Shared buffer cache across all connections
- Lower latency (no VM switch overhead)
- Simpler administration
- Better for大型 databases với shared data structures

**Ưu điểm Multiple VMs (Virtualization):**
- Better isolation (crash in 1 VM doesn't affect others)
- Easier to migrate/move individual instances
- Better resource utilization if DBs have different peak times
- Easier to scale incrementally

**Decision criteria:**
- Nếu single large database → single server
- Nếu multiple smaller databases → multiple VMs
- Nếu cần backup/recovery granularity → VMs
- Nếu performance is critical → single server

**Best practice for CloudCA:**
- Consider workload isolation requirements
- Consider management complexity
- Consider performance SLA

### 2. Storage division inconsistency

**Vấn đề:** Calculation method không đồng nhất

**CASE STUDY:**
- **Tính ban đầu:** Chia storage cho 3 server
- **Phân chia cuối:** Chia theo cụm, server giống nhau
- **Result:** Chia 5 thay vì 15

**Lỗi logic:**
```
Wrong: Total_Storage / 3_servers / 5_servers_per_cluster
Right: Total_Storage / Total_servers (3×5=15)
```

**Nguyên nhân:**
- Double division
- Confusion between cluster count and server count
- Calculation sheet không rõ ràng

**Khuyến nghị:**
1. Define rõ: total servers = cluster_count × servers_per_cluster
2. Calculate per-server resource first: Total / Total_servers
3. Then aggregate by cluster if needed

**Formula đúng:**
```
Per_Server_Storage = Total_Storage / (Cluster_Count × Servers_Per_Cluster)
Per_Server_Storage = Total_Storage / (3 × 5) = Total_Storage / 15
```

### 3. Maxscale node selection

**Maxscale:** MySQL/MariaDB proxy for read-write splitting

**Yếu tố để chọn số node:**

**Factor 1: Connection count**
- Nếu每_maxscale_connections = 10.000
- Nếu cần 100.000 concurrent connections
- → Cần 10 Maxscale nodes

**Factor 2: High availability**
- N+1 redundancy
- Zone distribution (multi-AZ)
- Maintenance window (1 node down不影响)

**Factor 3: Throughput**
- CPU processing per query
- Network bandwidth
- Latency requirements

**Typical sizing:**
- Small: 2-3 nodes
- Medium: 5-7 nodes
- Large: 10+ nodes (CloudCA case)

**Justification needed:**
- Show connection count calculation
- Show throughput requirement
- Show HA requirement (RPO, RTO)

### 4. Redis cluster sizing

**Redis cluster modes:**

**Mode 1: Standalone (Single node)**
- Minimum viable
- No HA
- Dùng cho dev/test

**Mode 2: Redis Sentinel (3 nodes)**
- Basic HA
- 1 master + 2 sentinels
- Minimum for production

**Mode 3: Redis Cluster (6+ nodes)**
- Sharding + HA
- 3 masters + 3 replicas (minimum)
-推荐: 9 nodes (3 masters × 3 replicas)

**CloudCA case: 9 nodes**
- Likely using Redis Cluster mode
- 3 master shards × 3 replicas = 9 nodes
- Provides both sharding and HA

**Justification:**
- Sharding: Split data across 3 masters for throughput
- HA: Each master has 2 replicas
- N+1 redundancy per shard

**Answer to "minimum cũng có thể chạy?":**
- Yes, minimum is 6 nodes (3 masters + 1 replica each)
- But 9 nodes provides better failure tolerance
- Trade-off: cost vs reliability

### 5. Load Balancer sizing

**Câu hỏi quan trọng:** LB giao tiếp với ai?

**3 scenarios:**

**Scenario 1: LB in front of APP servers**
```
Internet → LB → APP Servers
```
- Sizing based on: Total user traffic to APP
- Throughput = User_Request_Rate × Average_Request_Size

**Scenario 2: LB between APP and DB**
```
APP → LB → DB Cluster
```
- Sizing based on: APP to DB traffic
- Throughput = DB_Query_Rate × Query_Size

**Scenario 3: LB for external systems**
```
External_Systems → LB → CloudCA
```
- Sizing based on: External API calls
- Need to know which external systems

**CloudCA phải làm rõ:**
1. LB nằm ở layer nào? (Edge, Internal, External?)
2. Traffic source là gì? (Users, APP servers, External APIs?)
3. Protocol là gì? (HTTP, TCP, MySQL?)
4. Connection pool size expectations?

**Formula:**
```
LB_Throughput = Sum(Traffic_from_all_sources)
BW_needed = LB_Throughput × Safety_Factor
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu trúc hệ thống (New Model)

**Database Cluster:**
- DB management cluster with 256GB RAM
- Storage: calculated per server
- Question: Virtualized or bare-metal?

**Maxscale Proxy Layer:**
- 10 Maxscale nodes
- Purpose: MySQL/MariaDB read-write splitting
- HA and load balancing

**Redis Layer:**
- 9 Redis nodes (likely 3 masters + 6 replicas)
- Purpose: Caching and session management
- Sharding for high throughput

**Load Balancer:**
- Sizing depends on traffic source
- Need clarification on layer and protocol

### Quy mô hệ thống
- Viettel Cloud-CA system
- Architecture change: tách cụm để improve scalability
- Multi-tier architecture: LB → Maxscale → DB → Redis
- High availability requirements

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. DB sizing: Large RAM không phải lúc nào cũng tốt
- Consider virtualization if multiple databases
- Single large DB → single server
- Multiple small DBs → multiple VMs
- Trade-off: performance vs flexibility

### 2. LUÔN check consistency trong calculation
- Input: 3 clusters × 5 servers = 15 servers
- Wrong: Divide by 3, then divide by 5
- Right: Divide by (3×5) = 15
- Double-check division logic

### 3. Proxy node count phải có justification
- Maxscale: Show connection count requirement
- Redis: Explain cluster mode (6 vs 9 nodes)
- Don't just pick random numbers

### 4. LB sizing phải rõ ràng về layer và traffic
- Layer 7 (HTTP) vs Layer 4 (TCP)
- Edge vs Internal
- User traffic vs inter-service traffic
- Clarify in sizing document

### 5. Avoid cú pháp không cần thiết
- Don't use ">=" when you mean "="
- Be precise in specifications
- "=" conveys exact requirement

### 6. Explain your choices
- Why 10 Maxscale nodes?
- Why 9 Redis nodes instead of 6?
- Why this specific architecture?
- Include trade-off analysis

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 1 (v3.0 → v7.0, nhiều vấn đề logic)  
**Vấn đề chính:** Th inconsistency trong calculation, thiếu justification cho node count

**Đặc điểm hệ thống:**
- Multi-tier architecture (LB → Proxy → DB → Cache)
- Redis cluster with sharding
- Maxscale for database proxy
- Cloud CA system với high availability

**Khuyến nghị:**
- Làm rõ virtualization strategy cho DB
- Fix storage calculation inconsistency
- Provide justification for Maxscale/Redis node count
- Clarify LB layer and traffic source
- Use precise notation (avoid >=)
- Include architecture diagram showing traffic flow