# APPRAISAL KNOWLEDGE - HỆ THỐNG VTAG

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG VTAG (Vehicle Tag System)  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - NHIỀU LỖI TÍNH TOÁN (TRƯỜNG HỢP A)  
**Đầu mối:** Tungnt12  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Lê Đình Hoàng (Phòng Hệ thống)

#### 8 Nhóm lỗi nghiêm trọng:

**LỖI NGHIÊM TRỌNG #1: Thiếu mục đích sizing**
- Mục đích sizing không ghi rõ trong document
- Cần làm rõ: Định cỡ mới, nâng cấp, hay migration?

**LỖI NGHIÊM TRỌNG #2: Cint values không đồng nhất**
- Document có nhiều giá trị Cint khác nhau: 226, 12.6, 25.1, ...
- **Vấn đề:** Rất khó để thẩm định khi con số không thống nhất
- Có thể là: Cint total, Cint per core, Cint per vCPU?
- **Yêu cầu:** Đồng nhất đơn vị, ghi rõ ý nghĩa

**LỖI NGHIÊM TRỌNG #3: Sẵn có thiếu formal approval**
- Yêu cầu: sở cứ chỉ phải bằng văn bản, email của BGĐ TT
- Không được dùng口头 hoặc không chính thức
- Cần formal document xác nhận số thiết bị

**LỖI NGHIÊM TRỌNG #4: Link tham chiếu bị lỗi**
- Link Dell Inc: PowerEdge R740xd không mở được
- Không thể verify CPU specs
- **Yêu cầu:** Cung cấp working link hoặc screenshot từ spec.org

**LỖI NGHIÊM TRỌNG #5: Công thức tính toán sai toàn diện**
- Worker: "2.35/3 = ~0.8 TPS" - công thức không đúng
- PostgreSQL: Công thức tính sai
- Mongo/Kafka: Tải CPU chưa đúng theo hình
- Redis: Công thức tính sai
- MQTT: Tương tự Redis

**LỖI NGHIÊM TRỌNG #6: 6.72 TPS - Không có sở cứ chỉ**
- 6.72 TPS xuất hiện nhiều lần nhưng thiếu cơ sở
- Từ đâu ra? Benchmark? Production log?
- **Yêu cầu:** Cần minh chứng cho con số này

**LỖI NGHIÊM TRỌNG #7: Thiếu hình ảnh minh chứng**
- Trang 8: Bổ sung ảnh thực tế tải của các server
- Mongo/Kafka: Hình dung lượng chưa rõ % chiếm dụng
- Redis/MQTT: Chưa có ảnh CPU, dung lượng

**LỖI NGHIÊM TRỌNG #8: HA không đủ**
- Tất cả modules: Đề xuất cấu hình cần có ít nhất N+1 server
- Đang tính cho N servers mà không tính backup

---

## 💡 TRI THỨC RÚT RA

### 1. Cint unit consistency - CRITICAL!

**Problem:** Multiple Cint values without clarification

**Common mistakes:**

**Mistake #1: Confusing total with per-unit**
```
Total CPU: 226 Cint (all CPUs_combined)
Per vCPU: 12.6 Cint (single_vCPU_value)
Per core: 25.1 Cint (single_physical_core)

Document doesn't specify which is which! ❌
```

**Mistake #2: Unit confusion**
```
Cint2017_total vs Cint2017_per_core vs Cint2017_per_vCPU
Need to be CONSISTENT throughout document
```

**Best practice:**
```
1. Define unit at the beginning:
   "All CPU values in Cint2017 per vCPU unless specified"

2. Use consistent notation:
   - Total: "Total CPU: 226 Cint (18 vCPUs)"
   - Per unit: "12.6 Cint/vCPU"
   - Show calculation: 12.6 × 18 = 226.8 Cint

3. Don't mix units:
   - Either use total Cint OR per-vCPU Cint
   - Not both in same document
```

**For Vtag case:**
```
Re-measure all CPU values:
- Clarify if 226 is total or per-unit
- Clarify if 12.6 is per-vCPU or per-core
- Re-calculate using consistent unit
- Document your unit choice clearly
```

### 2. Formal approval requirement - Not optional!

**Why formal approval matters:**

**Example Scenario:**
```
Informal: "We have about 2000 devices" (口头)
Formal: "Email from BGĐ dated 15/03/2023 confirms 2000 devices"
```

**Formal approval format:**
```
Email from leadership:
From: deputy_director@viettel.com
To: team@viettel.com
Subject: Confirmation of device count for Vtag sizing
Date: [date]

Body: Confirmed that current Vtag system manages 2000 devices.
This count is official baseline for sizing calculations.

[Signature/Stamp]
```

**Document must include:**
```
Baseline Approval:
- Document type: Email / Decision / Meeting minutes
- From: [Leadership title and name]
- Date: [date]
- Reference number: [if applicable]
- Confirmed values:
  * Device count: 2000
  * Current TPS: 6.72
  * Current load: [metrics]
```

### 3. Worker calculation error - CASE STUDY

**THE ERROR:**
```
Document says: "Mỗi server chịu tải trung bình: 2.35/3 = ~0.8 TPS"
```

**Problems:**
1. **Division doesn't make sense:** 2.35 what? Total TPS?
2. **Why divide by 3?** Number of servers?
3. **Result 0.8 TPS/server** seems very low for a production system

**Likely correct calculation:**
```
Current system:
- TPS_total: 2.35 (measured from production)
- Servers_running: 3
- Load per server: 2.35 / 3 = 0.78 TPS/server ✓

But this seems LOW! Possible explanations:
1. These are peak TPS, not average
2. System has idle capacity (good for growth)
3. Measurement timeframe was during low-traffic period
4. TPS definition is different (transactions vs requests)
```

**Validation needed:**
```
Questions:
1. Confirm TPS definition: Is it transactions/second or something else?
2. Confirm measurement period: Peak hour, average day, or slow period?
3. Validate 0.8 TPS seems reasonable for Vtag workload
4. If using different metric (e.g., devices/second), clarify
```

### 4. PostgreSQL sizing - 2000 devices and 3-month retention

**Questions to answer:**

**Q1: Why 2000 devices?**
- Current production count?
- Future target (next 12-24 months)?
- Maximum capacity?
- **Must have formal approval** from leadership

**Q2: Why 3-month retention?**
- Regulatory requirement?
- Business requirement (replay needed for 3 months)?
- Operational need (troubleshooting window)?
- **Document the policy** requiring 3 months

**Q3: Storage calculation:**
```
If correct calculation:
- 2000 devices
- Per-device data: X MB/day
- Retention: 90 days (3 months)

Storage_needed = 2000 × X MB × 90

If X is unknown:
- Need measurement from current system
- Or estimate based on record size
- Or benchmark with sample data
```

**Best practice for database sizing:**
```
Step 1: Measure current usage
  - Query pg_database_size()
  - Check growth rate over 30 days
  - Calculate daily growth: (size_day30 - size_day1) / 30

Step 2: Project to target
  - Current_size = [measured]
  - Daily_growth = [calculated]
  - Retention_days = 90
  - Projected_size = Current + (Daily_growth × 90)

Step 3: Add safety margin
  - Safety_factor = 1.2 (20% buffer)
  - Total_storage = Projected_size × 1.2
```

### 5. N+1 HA requirement - Formal standard

**Viettel standard:**

**Stateless services (Worker, API):**
```
N = Calculated_servers
Total = N + 1 (1 standby)

Example:
- Need 3 workers for load
- Deploy 4 workers (3 active + 1 standby)
```

**Stateful services (Database, Kafka):**
```
Minimum = 3 nodes (quorum-based)
N+1 = Preferred for critical systems

Example:
- PostgreSQL: 3 nodes minimum, 4 preferred
- Kafka: 3 brokers minimum, 5 preferred
```

**For Vtag system:**
```
Worker cluster: N servers → Deploy N+1
PostgreSQL: Minimum 3, recommend 4
MongoDB: 3 nodes (replica set)
Kafka: 3 brokers minimum, 5 recommended
Redis: 3 nodes (sentinel or cluster)
MQTT: N+1 (stateless)

Rule of thumb:
- If budget allows: Always N+1
- For critical systems: N+2
- Starting small: N only, but document limitation
```

### 6. Kafka and MongoDB - Special sizing considerations

**Kafka sizing challenges:**

**Factor #1: Partition count**
```
Throughput = Partitions × Per_partition_capacity

If need 6.72 TPS and partition capacity = 2 TPS:
  Partitions_needed = 6.72 / 2 = 3.36 → 4 partitions
  Brokers = At least 3 (for replication factor 3)
```

**Factor #2: Replication factor**
```
Replication factor = 3 (common standard)
  - Each partition has 3 replicas
  - Requires 3 brokers minimum
  - N+1 = 4 brokers for fault tolerance
```

**Factor #3: Retention and storage**
```
Retention = Based on business requirement
Storage_per_partition = Message_rate × Message_size × Retention

Example:
- Message rate: 6.72 msg/s
- Message size: 1 KB
- Retention: 7 days
- Storage = 6.72 × 1 KB × 86400 × 7 = 4.06 GB per partition
- Total storage = 4.06 × 4 partitions = 16.2 GB
```

**MongoDB sizing challenges:**

**Factor #1: Working set**
```
MongoDB performance depends on:
  - Memory: Working set should fit in RAM
  - Working set = Hot data + Indexes

Rule of thumb:
  - RAM ≥ 2 × Working_set
  - If working set = 50 GB, need 100 GB RAM
```

**Factor #2: Replication**
```
Replica set: 3 nodes minimum
  - 1 primary
  - 2 secondaries
  - Automatic failover

N+1 consideration:
  - Add arbiter (lightweight) = 4 nodes
  - Or add secondary = 4 nodes (better)
```

### 7. Redis and MQTT - Cache and messaging

**Redis sizing:**

**Factor #1: In-memory storage**
```
All data must fit in RAM
Storage_needed = Keys × (Key_size + Value_size + Overhead)

Example:
- 1,000,000 keys
- Average key: 20 bytes
- Average value: 100 bytes
- Overhead: 50 bytes per entry
- Total = 1,000,000 × (20 + 100 + 50) = 170 MB
- Add headroom (50%): 170 × 1.5 = 255 GB RAM
```

**Factor #2: Persistence**
```
If using RDB/AOF snapshots:
  - Need disk storage
  - Storage = RAM_size × Configuration_factor
  - Typical: 2-3× RAM size for disk
```

**MQTT Broker sizing:**

**Factor #1: Connection count**
```
MQTT broker scales by concurrent connections, not TPS

Example:
- 2000 devices
- Concurrent connections: Assume 50% = 1000
- Per connection RAM: ~1 MB
- Total RAM = 1000 × 1 MB = 1 GB
- CPU depends on message throughput
```

**Factor #2: Message throughput**
```
Throughput = Connections × Messages_per_second_per_connection

Example:
- 1000 concurrent connections
- 1 msg/sec each = 1000 msg/s total
- CPU needed: 1000 × CPU_per_message
  (typically 0.01-0.1 Cint per message)
```

### 8. Verification with actual screenshots - MANDATORY

**What screenshots are needed:**

**For Worker:**
```
1. Server list with IP addresses
2. CPU utilization graphs showing current load
3. Memory usage graphs
4. Load average (number of processes)
5. Network I/O graphs
6. All must show timestamps
```

**For PostgreSQL:**
```
1. Database size: SELECT pg_database_size('vtag')
2. Table sizes: SELECT pg_total_relation_size('tablename')
3. CPU during peak query time
4. Memory usage (shared_buffers, cache)
5. Storage usage graphs
```

**For Kafka/MongoDB/Redis/MQTT:**
```
1. Service process CPU/Memory usage
2. Storage capacity and usage (%)
3. Network throughput
4. Key metrics:
   - Kafka: Messages/sec, Bytes/sec
   - MongoDB: Operations/sec, Document count
   - Redis: Keys, Memory used, Hit rate
   - MQTT: Connections, Messages/sec
```

**Screenshot requirements:**
```
- Must show IP/hostname
- Must show timestamp
- Must show metric value clearly visible
- Must be from production system (not test/demo)
- Include tool name (top, htop, Grafana, etc.)
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu trúc hệ thống Vtag

**Components identified:**
1. **Worker servers:** Processing units
2. **PostgreSQL:** Primary database
3. **MongoDB:** Document store
4. **Kafka:** Message queue
5. **Redis:** Cache layer
6. **MQTT Broker:** IoT messaging

### Current baseline (needs verification)
- Devices: ~2000 (needs formal approval)
- TPS: 6.72 (needs source/documentation)
- Retention: 3 months for PostgreSQL

### Sizing issues (must fix)
- Cint values inconsistent (226, 12.6, 25.1)
- Worker calculation errors (2.35/3 = 0.8 TPS)
- Missing HA (N+1 not included)
- Broken reference links
- No actual load screenshots

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. Cint unit consistency is NON-NEGOTIABLE
- Define unit at document start
- Use consistent unit throughout
- Don't mix total vs per-unit values
- Clarify: Cint_total vs Cint/vCPU vs Cint/core

### 2. Formal approval is MANDATORY for baselines
- Email/decision from leadership required
- No informal or口头 confirmations
- Document source + date + reference number

### 3. Verify EVERY calculation step
- Don't trust "2.35/3 = 0.8 TPS"
- Validate each formula
- Show intermediate steps
- Include units in calculation

### 4. Database retention needs policy justification
- Why 3 months? (Regulatory, business, operational?)
- Document the requirement
- Reference the policy if exists

### 5. HA is NOT optional for production
- Stateless: N+1 minimum
- Stateful: 3 nodes minimum (quorum)
- Document HA strategy
- Explain failover behavior

### 6. Kafka/MongoDB need special sizing considerations
- Kafka: Partitions, replication, retention
- MongoDB: Working set in RAM
- Don't use generic sizing approaches

### 7. Screenshots must show ALL required info
- IP/hostname (traceability)
- Timestamp (when was this measured?)
- Metric value (actual number)
- Tool name (how was it measured?)

### 8. Reference links must be VALID
- Test all links before submitting
- Provide alternative if link breaks
- Include screenshots as backup

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** RẤT CAO  
**Số vòng PNX:** 1 (nhiều lỗi tính toán nghiêm trọng)  
**Vấn đề chính:** Cint không đồng nhất, công thức sai, thiếu hình ảnh, thiếu HA

**Đặc điểm hệ thống:**
- Vtag: Vehicle tag/IoT system
- Multi-component architecture (Worker, DB, Cache, Message queue)
- IoT workload (MQTT messaging)
- ~2000 devices current baseline

**Khuyến nghị CRITICAL:**
- **URGENT:** Fix Cint unit consistency throughout document
- Recalculate ALL sizing with correct formulas
- Add N+1 for all components
- Include complete screenshot set (IP, timestamp, metrics visible)
- Get formal baseline approval from leadership
- Fix broken reference links
- Document retention policy justification
- Clarify TPS definition and measurement period
- Validate 0.8 TPS/server is reasonable
- Verify 2000 devices count with formal documentation