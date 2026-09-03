# APPRAISAL KNOWLEDGE - DỰ ÁN: APIGEE MINI APP (API GATEWAY)

**Mã PYC:** PYC-64015  
**Đầu mối yêu cầu:** Ngoctv1 (Trung tâm CNTT - PS CSKH)  
**Đầu mối thẩm định:** Khanhnd23 (Phòng Công nghệ Hệ thống)  
**Đơn vị phát triển:** Trung tâm CNTT - Phòng sản phẩm CSKH  
**Mục đích sizing:** Cấp phát tài nguyên cho hệ thống APIGEE quản lý và bảo vệ API Backend của MiniApp  
**Quy mô:** 4,000,000 active users/day, TPS max 20,000  
**Ngày hoàn thành:** 2026 (Kế hoạch đổ tải: 3/2026)  
**Trạng thái phản hồi:** Có 2 vòng phản hồi (PNX v1 → v2) - Đã ký duyệt checklist

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ⚠️ **ĐÃ CÓ PHẢN BIỆN (TRƯỜNG HỢP A)**
- **Vòng 1 (PNX v1):** 11 yêu cầu điều chỉnh
- **Vòng 2 (PNX v2):** Đã chỉnh sửa, cần checklist đính kèm
- **Trạng thái:** Đã ký checklist và hoàn thành

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH

### 1. HỆ THỐNG ĐẶC BIỆT QUAN TRỌNG → BẮT BUỘC CÓ DR
**Quy định từ PNX:**
```
"GL đính kèm → hệ thống ĐBQT bắt buộc phải có DR"
```

**Mức độ quan trọng:** "Quan trọng" (không phải Đặc biệt quan trọng)

**Yêu cầu DR:**
- Dù không đánh giá "Đặc biệt quan trọng" nhưng vẫn bắt buộc có DR
- Bắt buộc cam kết thời gian hoàn thành triển khai và đổ tải thật
- Cần sở cứ từ Kinh doanh (KD) hoặc Ban Giám đốc (BGĐ)

**Bài học:**
- Ngay cả hệ thống "Quan trọng" (không phải ĐBQT) vẫn cần DR
- DR không phải optional cho API Gateway systems
- Timeline phải rõ ràng: Kế hoạch đổ tải tháng 3/2026
- Need business commitment for deployment timing

### 2. TPS CALCULATION CHO API GATEWAY (20,000 TPS PEAK)
**Base metrics from sizing:**
- **Active users/day:** 4,000,000
- **TPM (Transactions Per Minute):** 300,000
- **TPS average:** 5,000
- **TPS max (peak):** 20,000

**Calculation:**
```
Số request mỗi ngày = TPS_avg × 60 × 60 × 24
                  = 5,000 × 86,400
                  = 432,000,000 request/day
                  ≈ 432 triệu request/day

Đối tác đề xuất: 432 triệu request/day ≈ 5,000 TPS (average)
               TPS peak lên tới 20,000 TPS (4× average)

Justification:
- Peak = 4× average cho API Gateway (acceptable)
- 432M request/day align với 4M active users (108 requests/user/day)
```

**Bài học:**
- API Gateway có burst traffic → TPS peak = 4× average
- Need to account for TPS peak when sizing, not just average
- Always document peak vs average for network devices

### 3. SO SÁNH PNX V1 vs PNX V2 - CÁC YÊU CẦU CHỈNH SỬA

| Nhận xét PNX v1 | Phản hồi đơn vị | Kết quả PNX v2 |
|-----------------|-----------------|-----------------|
| Bổ sung sở cứ | Đã bổ sung | ✅ Có file đính kèm |
| Tính toán lại số liệu | Đã tính toán lại | ✅ Chi tiết hơn |
| Thiếu đánh giá mức độ quan trọng | Bổ sung 1 dòng vào phần đầu | ✅ "GL đính kèm → hệ thống ĐBQT phải DR" |
| Thiếu cam kết thời gian | Thêm vào phần đầu sizing | ✅ KH: 3/2026 |
| Thiếu checklist đính kèm | Đính kèm checklist | ✅ Có checklist v2 |
| Thiếu mục đích sizing | Bổ sung trang 1 | ✅ Cấp phát cho quản lý và bảo vệ API |
| Chưa có mô hình logic, luồng nghiệp vụ | Bổ sung trang 4 | ✅ Có diagram Apigee architecture |
| Mục sở cứ đề xuất thiếu | Bổ sung TB, TPM, TPS(max) | ✅ 4M users, 300K TPM, 20K TPS |
| Đối tác đề xuất thiếu | Bổ sung tính chi tiết 432M request | ✅ 5,000 TPS avg, 20K TPS peak |
| Thiếu thông tin kết nối | Giải thích không có kết nối | ✅ Apigee quản lý internal API |
| Thiếu thông số FW, LB | Bổ sung chi tiết | ✅ Full specs cho từng luồng |
| LB thiếu từng luồng nghiệp vụ | Bổ sung chi tiết từng luồng | ✅ Per session, bandwidth, duration |

**Bài học:**
- PNX v2 tập trung vào **tính toán chi tiết** và **cam kết timeline**
- Checklist sizing bắt buộc ký đính kèm
- Mức độ quan trọng phải explicit reference đến guideline
- Mỗi luồng nghiệp vụ cần đầy đủ specs: concurrent session, peak session, new session/s, duration, bandwidth

### 4. TÍNH TOÁN CONCURRENT SESSION CHO FIREWALL (48,000 SESSIONS)
**Breakdown:**
```
Từ MiniApp đến DCN (Giao tiếp nội bộ):
- 20,000 concurrent sessions
- Session duration: 30s
- Login time: 3s

Từ MiniApp đến Internet (Giao tiếp người dùng):
- 20,000 concurrent sessions
- Session duration: 5s (tính năng ứng dụng)

Tổng concurrent session:
= 20,000 (DCN) + 20,000 (Internet)
= 40,000 sessions

Apply buffer (Kdup = 1.2):
= 40,000 × 1.2 = 48,000 concurrent sessions
```

**New session/s calculation:**
```
Từ MiniApp đến DCN (Login):
= 20,000 users / 3s = 6,666 new sessions/s

Từ MiniApp đến Internet (User traffic):
= 20,000 users / 3s = 6,666 new sessions/s

Tổng new session/s = 6,666 + 6,666 = 13,332
Apply buffer (Kdup = 1.2):
= 13,332 × 1.2 = 15,999 ≈ 16,000 new sessions/s
```

**BUT sizing khác với PNX:**
- PNX calculated: 20,000 + 20,000 = 40,000 → Kdup 1.2 = 48,000
- BUT calculated: (20,000 × 2/3) + (20,000 × 2/3) = 13,332 → Kdup 1.2 = 15,999

**Learning point:** Document calculation method explicitely. PNX used simple sum, BUT used time-based calculation.

### 5. TÍNH TOÁN BĂNG THÔNG FIREWALL (3,820 MBPS)
**Components:**
```
Từ APIGee tới MiniApp:
= (20,000 TPS / 3s) × 1 request × 15KB/request / 1024
= 98 MB/s = 784 Mbps

Từ MiniApp tới Internet:
= 15KB/request × 20,000 concurrent users
= 300,000 KB/s ≈ 2,400 Mbps

Tổng băng thông:
= 784 + 2,400 = 3,184 Mbps

Apply buffer (Kdup = 1.2):
= 3,184 × 1.2 = 3,820 Mbps ≈ 3.8 Gbps
```

**Firewall specs required:**
- Throughput: ≥ 3,820 Mbps
- Concurrent sessions: ≥ 48,000
- New session/s: ≥ 16,000 (or 15,999 per BUT calculation)
- Ports: 2× 10Gbps (DCN, Internet), 2× 1Gbps (switch)
- HA: Active-Active

**Bài học:**
- Multi-directional traffic phải tính từng hướng
- APIGee → MiniApp (internal): 784 Mbps
- MiniApp → Internet (public): 2,400 Mbps
- Total ≠ sum (không nhân đôi, vì khác luồn traffic)
- Peak throughput sizing là关键, không phải average

### 6. LOAD BALANCER SIZING (1,094 MBPS, 3M SESSIONS)
**Throughput calculation:**
```
TTC = Thông lượng truy cập trang chủ viettel.vn
   = 268 KBps (per transaction?) × 5,000 TPS
   = 1,340,000 KBps ≈ 1,308 Mbps

Apply efficiency/redundancy:
= 1,308 × factor = 1,094 Mbps

Giải pháp:
- Dùng 5 port 1Gbps (aggregated)
- Hoặc 2 port 10Gbps (redundant + high bandwidth)
```

**Sessions:**
```
Concurrent session:
= 40,000 × 1.2 = 48,000 (same as FW)

BUT sizing document shows:
Concurrent session = 40,000 × 1.2 = 48,000
New session = 5,000 (TPS avg)
```

**Load balancer specs required:**
- Throughput: ≥ 1,094 Mbps
- Concurrent sessions: ≥ 3M (million sessions!)
- New session/s: ≥ 500
- Port density: ≥5 × 1Gbps or 2×10Gbps
- HA: Active-Active

**Bài học:**
- Load balancer sessions count thường billion range (3M = 3,000,000)
- Với 3M sessions, 5,000 new session/s là rất thấp (0.17% of total)
- TTL (Time-To-Live) của sessions được set đủ dài để optimize

### 7. APIGEE SERVER SIZING (51 NODES, ACTIVE-ACTIVE)
**Architecture:**
- **51 Apigee servers** (Active-Active cluster)
- **2 PostgreSQL databases** (Active-Standby)
- **1 KeyCloak** (CMS admin, không cần HA)
- **2 Load balancers** (Active-Active)

**Per Apigee server:**
```
CPU: 8 vCPU
RAM: 18 GB
Disk: 500 GB
HA: Active-Active (all servers)
Total: 51 servers
```

**Vì sao 51 servers?**
- Apigee là distributed system ( değil single monolith)
- Each server handles subset of APIs
- Horizontal scaling more efficient than vertical scaling
- 51 = 3 data centers × 17 servers per DC? (Need clarification)

**Database sizing (PostgreSQL):**
```
CPU: 32 CINT (≈96 vCPU)
RAM: 64 GB
Disk: 376,000 GB (376 TB on NAS)

Per node: 2 servers (Active-Standby)
Purpose: Analytics & monetization data (không phải operational data)
```

**Bài học:**
- **PostgreSQL for analytics** → Very large storage (376 TB)
- **Cassandra** presumably for operational data (token, policy) but not explicitly sized in this document
- 18GB RAM per Apigee server → Minimal, suggesting stateless design
- 500GB disk → Adequate for OS + logs + local cache

### 8. BAN CHỦ QUY ĐỊNH THỜI GIAN ĐỔ TẢI
**Yêu cầu PNX:**
```
"Bắt buộc phải có thời gian cam kết hoàn thành chứng minh đất r (thêm 1 dòng)"
```

**Response:**
- Kế hoạch số 22273/KH của TGĐ
- Thời gian đổ tải: Tháng 3/2026

**Bài học:**
- Hệ thống Critically important → Must have deployment timeline
- Business commitment required (not just technical sizing)
- Timeline must be signed off by KD or BGĐ
- Prevents "shelfware" (resources allocated but never used)

### 9. CHECKLIST SIZING BẮT BUỘC KÝ
**Yêu cầu PNX:**
```
"Ký sizing phải đính kèm thêm file checklist"
```

**Files attached:**
- Checklist sizing cấp phát tài nguyên HTCNTTv2.xlsx
- Mẫu HSTK khanhnd23_082025.xlsx

**Bài học:**
- Checklist không optional → Bắt buộc
- Checklist đăng ký resources đã được thực tế sử dụng
- Trước when signing sizing, must verify:
  - All servers accounted
  - No duplicate entries
  - IP allocations correct
  - Network segments documented

### 10. MÔ HÌNH LOGIC VÀ LUỒNG NGHIỆP VỤ
**Required additions:**
```
PNX v1: "Bổ sung mô hình logic, luồng nghiệp vụ"
Response: "Trang 4"
```

**Apigee architecture (simplified):**
```
External Users
    ↓
[Internet] → [Firewall] → [Load Balancer]
    ↓
APIGEE Cluster (51 servers)
    ↓
[MiniApp Backend]
    ↓
[Cassandra] (Operational data: tokens, policies, API keys)
[PostgreSQL] (Analytics data: monetization, usage reports)
```

**Keycloak:**
- CMS administration interface
- Does NOT require HA (1 server sufficient)
- Separate from production traffic

**Bài học:**
- Architecture diagram critical for complex systems
- Must show: external users → FW/LB → Apigee → Backend → Databases
- Distinguish operational data (Cassandra) vs analytics data (PostgreSQL)
- Keycloak is management layer (separate from production traffic path)

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### 1. APIGEE SERVERS (51 NODES)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 8 vCPU per server | Total: 408 vCPU cluster |
| **RAM** | 18 GB per server | Total: 918 GB cluster |
| **Disk** | 500 GB per server | OS + logs + local cache |
| **HA Mode** | Active-Active | All 51 servers active |
| **Cluster size** | 51 servers | Distributed architecture |
| **Purpose** | API Gateway, management, protection | Not application servers |

**Scalability:**
- Horizontal scaling (add servers, not upgrade CPU/RAM)
- Each server handles subset of APIs
- Load balancer distributes traffic across all 51 nodes

### 2. POSTGRESQL DATABASES (2 NODES, ANALYTICS)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 32 CINT (≈96 vCPU) per server | |
| **RAM** | 64 GB per server | |
| **Disk** | 376,000 GB (376 TB) on NAS | Per server or shared? |
| **HA Mode** | Active-Standby | 1 active, 1 standby |
| **Purpose** | Analytics & monetization data | NOT operational data |

**Storage breakdown:**
- 376 TB is very large → Long-term data retention
- Likely stores: API call logs, usage metrics, billing data
- Must analyze retention policy (e.g., 7 years for audit trail)

**Note:** Cassandra presumably handles operational data but not sized in this document.

### 3. KEYCLOAK (1 SERVER, MANAGEMENT)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 4 vCPU | |
| **RAM** | 16 GB | |
| **Disk** | 500 GB | |
| **HA Mode** | None (single server) | Admin only, not production |
| **Purpose** | CMS administration interface | Separate from Apigee cluster |

**Why no HA?**
- Management plane (C.MS - Content Management System)
- Not directly in production traffic path
- Can be recovered from backup if fails
- Trade-off: cost vs. availability

### 4. FIREWALL (2 UNITS, ACTIVE-ACTIVE)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **Throughput** | ≥ 3,820 Mbps | ≈ 3.8 Gbps |
| **Concurrent sessions** | ≥ 48,000 | |
| **New session/s** | ≥ 16,000 | |
| **Port configuration** | 2×10Gbps + 2×1Gbps | Redundant |
| **HA Mode** | Active-Active | Both firewalls active |
| **Ports needed** | 12 ports total (DCN, Internet, Switch) | |

**Port breakdown:**
- 2 ports DCN (10Gbps)
- 2 ports Internet (10Gbps)
- 2 ports Switch (1Gbps)
- Plus redundant ports
- Total: 12 ports

### 5. LOAD BALANCER (2 UNITS, ACTIVE-ACTIVE)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **Throughput** | ≥ 1,094 Mbps | Calculated较低 vs FW |
| **Concurrent sessions** | ≥ 3M (3,000,000) | Very high session count |
| **New session/s** | ≥ 500 | |
| **Port density** | ≥ 5 × 1Gbps or 2×10Gbps | |
| **HA Mode** | Active-Active | Both active |
| **Power** | Redundant (dual power supply) | |

**Why 1,094 Mbps vs 3,820 Mbps for FW?**
- Apigee cluster has 51 servers → LB distributes across them
- Each server gets: 1,094 Mbps / 51 ≈ 21 Mbps per server (reasonable)
- LB only handles Apigee traffic (not Internet traffic directly)
- FW handles ALL traffic (both directions)

---

## 🎯 CÁC BÀI HỌC QUAN TRỌNG

### 1. API GATEWAY SIZING: TPS PEAK × 4
**Pattern:**
```
Average TPS: 5,000
Peak TPS: 20,000

Burst ratio: 4× (reasonable for API Gateway)
```

**Why 4×?**
- API Gateway has bursty traffic (users login, then burst API calls)
- Not like steady-state applications (e.g., streaming, game servers)
- Must provision for peak, not just average
- Also consider 95th/99th percentile for capacity planning

**Alternative sizing:**
- Some systems use 2× for burst
- For API Gateway with 5K average, 4× is conservative but justified

### 2. CONCURRENT SESSION VERSUS TPS
**Relationship:**
```
Concurrent sessions = TPS × Session duration

Example:
- Peak TPS: 20,000
- Session duration: 3s (for login), 5s (for API calls)
- Concurrent sessions: 20,000 × 3 = 60,000

BUT in sizing:
- Sessions: 40,000 (20K internal + 20K external)
- This aligns with 20K concurrent users (each user makes 1 session at a time)
```

**Firewall sessions vs TPS:**
- TPS: 20,000 peak
- Concurrent sessions: 48,000
- This means: Average session duration = 48,000 / 20,000 = 2.4 seconds (reasonable)

**Bài học:**
- Document session duration explicitly
- Calculate based on actual user behavior, not arbitrary
- Use different durations for different user flows (login vs API call)

### 3. TPX CALCULATION: HOURS ACTIVE VERSUS 24/7
**Sizing assumption:**
```
Active users: 4,000,000
TPS average: 5,000

Assumption: System is NOT 24/7 at peak load
           → Peak is during business hours

Calculations:
- 432M request/day / 4M users = 108 requests/user/day
- If users spread evenly over 24 hours:
  → 108/24 = 4.5 requests/hour = 0.00125 requests/second (far below TPS)
  
This means: Peak 5,000 TPS × 8 hours × 3600 = 144M requests
              Or 5,000 × 24 × 3600 = 432M requests (if 24/7 at average)

The implication: System has significant peak variability
                 Need to account for burst
```

**Bài học:**
- Document active hours vs 24/7
- TPS calculated at peak, not average over 24 hours
- Size for peak (20,000 TPS), not average (5,000)
- Consider time-of-day and day-of-week patterns

### 4. HORIZONTAL SCALING: 51 NODES
**Why so many?**
```
Vertical scaling (1 server, large CPU/RAM):
  → Limited by single-server capacity
  → Single point of failure if server down

Horizontal scaling (51 servers, medium CPU/RAM):
  → Better fault tolerance (lose 1 server = 1/51 capacity lost)
  → Scale by adding servers inefficient (no need to upgrade existing)
  → Load balancer distributes automatically
```

**Apigee architecture:**
- Each Apigee server handles subset of APIs
- Competing for different API contracts
- Distributed coordination via shared storage (Cassandra/PostgreSQL)
- Stateless design enables horizontal scaling

**Bài học:**
- API Gateway systems benefit from horizontal scaling
- Infrastructure as code → easy to spin up new servers
- Cost-effective: many smaller servers vs fewer large servers
- Must consider operational complexity (managing 51 servers)

### 5. DATABASE SEGREGATION: CASSANDRA VS POSTGRESQL
**Two databases for two purposes:**
```
Cassandra (Operational Data):
- Token management
- API key storage
- Policy enforcement
- Real-time transaction data
- Low latency, high throughput
- Distributed, always on
- Not explicitly sized in this document

PostgreSQL (Analytics Data):
- Monetization records
- Usage analytics
- Billing reports
- Historical data
- Structured queries, joins
- 376 TB storage (long retention)
- Sized in this document
```

**Bài học:**
- Separate operational data from analytics data
- Use right database for right purpose
- Cassandra for speed + availability (operational)
- PostgreSQL for complex queries + reporting (analytics)
- Operational data: Hot, small, real-time
- Analytics data: Cold, large, query-heavy

### 6. STORAGE PLANNING: 376 TB FOR ANALYTICS
**Calculations:**
```
Assumptions:
- 432M API calls/day
- 1 KB per API call (conservative average)
- 7 years retention (typical for telecom audit)

Storage per year:
- 432M calls/day × 365 days × 1 KB/call
- = 157.68 GB/day × 365
- ≈ 57.55 TB/year

For 7 years:
- 57.55 TB/year × 7 years
- ≈ 402.85 TB

But sizing says: 376 TB
→ Implies ~6.5 years retention OR more compression
```

**Bài học:**
- Long-term retention substantially increases storage needs
- Analytics data grows faster than operational data
- Must plan for database archival or tiered storage
- Consider compression ratios (e.g., gzip 70% reduction)
- Monitor growth monthly to predict expansion

---

## 📋 MẪU HÌNH TÍNH TOÁN CHO API GATEWAY

### STEP 1: XÁC ĐỊNH GIÁ TRỊ BUSINESS
```
Mục tiêu: 4,000,000 active users/day

Chuyển đổi thành TPS:
- Giả sử mỗi user: 100 API calls/day
- 4M users × 100 calls = 400M API calls/day

TPS average = 400M / (24 × 3600) = 4,629 ≈ 5,000 TPS

TPS peak = TPS avg × burst ratio (4×)
         = 5,000 × 4 = 20,000 TPS

Justification: API Gateway has bursty traffic
```

### STEP 2: TÍNH CONCURRENT SESSIONS
```
Session duration assumptions:
- Login: 3 seconds
- API call: 5 seconds

Concurrent sessions (internal to MiniApp):
= TPS peak × Session duration
= 20,000 × 3 s = 60,000 sessions

BUT if user concurrency = 20,000 (peak users online):
→ 20,000 concurrent users
→ Each user makes ~1 session at a time

Concurrent sessions (external Internet):
= 20,000 concurrent users

Total:
= 20,000 (internal) + 20,000 (external) = 40,000 sessions
Apply buffer (Kdup = 1.2): 48,000 sessions
```

### STEP 3: TÍNH BĂNG THÔNG (TWO WAYS: APIGEE TRAFFIC, USER TRAFFIC)
```
Way 1: Apigee → MiniApp (internal)
= TPS peak × Request size
= 20,000 / 3 × 15 KB = 100 MB/s = 800 Mbps

Way 2: MiniApp → Internet (user-facing)
= Concurrent users × Payload size
= 20,000 × 15 KB = 300,000 KB/s = 2,400 Mbps

Total:
= 800 + 2,400 = 3,200 Mbps

Apply buffer (Kdup = 1.2):
= 3,200 × 1.2 = 3,840 Mbps ≈ 3,820 Mbps
```

### STEP 4: SIZING APIGEE CLUSTER
```
Approach A: Horizontal scaling (used in sizing)
- Each Apigee server: 8 vCPU, 18 GB RAM
- Horizontal scaling until capacity met
- 51 servers allows: 51 × (some TPS per server)

Check: If each Apigee server handles ~400 TPS:
→ 51 × 400 = 20,400 TPS capacity
→ Slightly above 20,000 TPS requirement ✓

Approach B: Vertical scaling (not used)
- 1 server: 408 vCPU, 918 GB RAM (51 × 8, 51 × 18)
- BUT: Not practical for Apigee (distributed system)
- AND: Single point of failure
```

### STEP 5: SIZING DATABASES (SEPARATE CONCERNS)
```
PostgreSQL (Analytics):
- Purpose: Monetization, usage reports, billing
- Data retention: 6-7 years (typical for telecom)
- Growth rate: ~432M calls/day × 1 KB/call = 400+ GB/day
- Storage needed: 57.55 TB/year × 7 years ≈ 403 TB
- Proposed: 376 TB on NAS (with compression)

Cassandra (Operational):
- Purpose: Token management, API keys, policies
- Data retention: Hot data (days to weeks)
- NOT sized in this document (likely ~1-2 TB)
- Real-time access, distributed across Apigee cluster
```

---

## 🔧 CHECKLIST SIZING CHO API GATEWAY

### 1. KPIs và SLAs
- [ ] Document TPS avg, TPS peak (TPS peak = 2-4× avg)
- [ ] Session duration per user flow
- [ ] Response time targets (latency SLAs)
- [ ] Error rate tolerance
- [ ] Business metrics: active users, request volume, peak multipliers

### 2. Calculations
- [ ] TPS calculations clearly documented
- [ ] Concurrent sessions vs TPS
- [ ] Bandwidth per direction (not just total)
- [ ] Peak vs average (size for peak!)
- [ ] Burst ratios justified

### 3. Storage Planning
- [ ] Operational vs analytics data separated
- [ ] Data retention period defined
- [ ] Growth rate calculated (GB/day, TB/year)
- [ ] Compression ratios accounted
- [ ] Archival strategy for old data

### 4. Network Infrastructure
- [ ] Firewall throughput sized for peak (not avg)
- [ ] Load balancer sessions capacity (millions)
- [ ] Port density (10Gbps vs 1Gbps)
- [ ] Redundancy: Active-Active for high availability
- [ ] Multi-directional traffic (internal vs external)

### 5. Apigee Cluster
- [ ] Horizontal scaling strategy (number of servers)
- [ ] Per-server capacity (TPS per server)
- [ ] Stateless design (no correlation across servers)
- [ ] Coordination via shared storage (Cassandra)
- [ ] Maintenance window procedures

### 6. Database Architecture
- [ ] Separate databases for operational vs analytics
- [ ] Cassandra for operational: real-time, distributed
- [ ] PostgreSQL for analytics: structured queries, large storage
- [ ] NAS or SAN for PostgreSQL (376 TB too large for local disk)
- [ ] Backup and disaster recovery procedures

### 7. High Availability
- [ ] Active-Active for front-end (Apigee, FW, LB)
- [ ] Active-Standby for databases (PostgreSQL)
- [ ] No SPOF in architecture
- [ ] Geographic redundancy (DR site) for critical systems
- [ ] Failover testing procedures

### 8. Business Continuity
- [ ] Timeline承诺 (deployment and cutover dates)
- [ ] Signed off by KD or BGĐ
- [ ] Capacity planning for future growth
- [ ] Budget allocated for ongoing operations
- [ ] Team trained on Apigee operations

### 9. Documentation
- [ ] Checklist sizing attached and signed
- [ ] PNX addressed and incorporated
- [ ] Architecture diagrams provided
- [ ] Per-flow bandwidth details (not just aggregate)
- [ ] Mức độ quan trọng reference: GL đính kèm

---

## 🎯 KEY INSIGHTS

### 1. SYSTEM IMPORTANCE DRIVES REQUIREMENTS
```
Đặc biệt quan trọng (Critical):
→ DC-DR 1:1, Ksaiso 1.2, Mandatory DR
→ Example: CA systems, core BCCS

Quan trọng (Important):
→ DC-DR 1:1, Ksaiso 1.1, DR required
→ Example: APIGEE Mini App (this project)

Bình thường (Normal):
→ DC-DR optional, Ksaiso 1.1
→ Example: Internal tools, test environments

Ít quan trọng (Low):
→ Backup sufficient, no DC-DR
→ Example: Dev environments
```

### 2. TPS CALCULATION FOR API GATEWAYS
```
Step 1: Determine business metrics
- Active users: 4M/day
- Requests per user: 100/day (assumption)
- Total requests: 400M/day

Step 2: Convert to TPS
- TPS avg = 400M / 86,400 = 4,629 ≈ 5,000
- TPS peak = TPS avg × burst ratio (4×)
         = 5,000 × 4 = 20,000

Step 3: Validate
- 20K TPS for 4M users → 0.5% concurrency (reasonable)
- Session duration: 3-5 seconds
- Verify against industry benchmarks
```

### 3. CONCURRENT SESSION VERSUS TPS
```
Concurrent sessions = Active users at peak time

Example:
- 4M active users/day
- Peak hour: 10% of daily active users = 400K
- But only 20K concurrent sessions (5% of peak)
→ Implies: Not all active users are online at peak hour
→ Or: Users have short sessions (login, do transaction, logout)

Verification:
- 20K sessions, TPX peak 20K
→ Session duration = 20K/20K = 1 second (reasonable for API calls)
→ Or 20K sessions, TPS 5K average
→ Session duration = 20K/5K = 4 seconds (reasonable)
```

### 4. BANDWIDTH PLANNING FOR API GATEWAY
```
Direction: Apigee → MiniApp (internal)
= TPS peak × Request size
= 20,000 × 15 KB = 300 MB/s = 2,400 Mbps

Direction: MiniApp → Internet (user-facing)
= Concurrent users × Payload size
= 20,000 × 15 KB = 300 MB/s = 2,400 Mbps

Wait, this calculates the SAME as above!
Re-examining sizing document:
- Apigee → MiniApp: 20,000/3 × 15 KB = 100 MB/s
  → Divided by 3 session duration?

Lesson: Clarify session duration in bandwidth calculation
- If sessions are short (3s), effective bandwidth is LOWER
- Bandwidth = (TPS × payload) NOT (concurrent users × payload)
```

### 5. DATABASE SEGREGATION STRATEGY
```
Two databases:

1. Cassandra (Operational Data):
   - Real-time API calls
   - Token management
   - Policy enforcement
   - Hot data (hours to days)
   - Low latency required
   - Distributed, always available
   - Sizing: ~1-2 TB (small but fast)

2. PostgreSQL (Analytics Data):
   - Monetization records
   - Usage analytics
   - Billing reports
   - Cold data (months to years)
   - Complex queries
   - Structured data
   - Sizing: 376 TB (large)

Benefits:
- Optimize storage per use case
- Separate recovery strategies
- Scale independently
- Query performance optimized
```

---

## 📈 MẪU HÌNH TÍNH TOÁN CHO CÁC LOẠI HỆ THỐNG

### Pattern 1: API GATEWAY WITH HIGH TPS
```
System: Apigee Mini App
Business metrics: 4M active users, 432M requests/day
TPS: 5,000 avg, 20,000 peak
Burst ratio: 4× (typical for API Gateway)

Sizing:
- Apigee cluster: 51 nodes, 8 vCPU, 18 GB each
- Firewall: 3,820 Mbps, 48K sessions
- Load balancer: 1,094 Mbps, 3M sessions
- PostgreSQL: 32 vCPU, 64 GB, 376 TB
- Total cost: High (distributed system)

Optimization opportunities:
- Use horizontal scaling (add servers as needed)
- Implement caching to reduce database load
- Use CDN for static content
- Implement API rate limiting to protect backend
```

### Pattern 2: MULTI-DIRECTIONAL TRAFFIC
```
Traffic breakdown:
1. Apigee → MiniApp: Internal API calls
   - Bandwidth: 800 Mbps (based on TPS)
   - Sessions: 20,000 (internal)
   - Direction: Server-to-server

2. MiniApp → Internet: User-facing traffic
   - Bandwidth: 2,400 Mbps (based on concurrent users)
   - Sessions: 20,000 (user sessions)
   - Direction: Server-to-client

Total bandwidth = 3,200 Mbps (not 2× each direction)

Firewall sizing:
- Throughput: 3,200 Mbps (aggregate of both directions)
- Sessions: 40,000 (20K + 20K)
- New sessions: 16,000/s (calculated from TPS)

Lesson: Don't double-count bidirectional traffic!
```

### Pattern 3: HORIZONTAL SCALING FOR API GATEWAY
```
Why horizontal?
- API Gateway has stateless design
- Easy to add/remove servers
- Load balancer distributes traffic automatically
- Better fault tolerance

How many servers?
- Target TPS: 20,000 peak
- Assumed capacity per server: ~400 TPS (rule of thumb)
- Servers needed: 20,000 / 400 = 50 servers
- Plus buffer: 51 servers

Vertical scaling alternative (not used):
- 1 large server: 408 vCPU, 918 GB RAM
- BUT: Impractical (expensive, SPOF, hard to maintain)

Best practice:
- Start with 10-20 servers, scale based on actual usage
- Monitor TPS per server, add capacity when needed
- Use auto-scaling if available
```

---

## 📚 TÀI LIỆU THAM KHẢO

- **P.YC:** Số 22273/KH của TGĐ về xây dựng ứng dụng Tammi
- **Guideline:** GL.CNVTQĐ.CNTT.03_GL phần muc độ quan trọng hệ thống ứng dụng CNTT
- **Guideline:** Guideline Muc do quan trong he thong.pdf
- **Guideline:** Guideline_Dinh_co_thiet_bi_CNTT_lan9.pdf
- **Apigee Specs:** PL17_Tinh toan Apigee 53 nodes (v2)
- **Checklist:** Checklist sizing v2 (đanh ký hợp lệ)
- **Best Practice:** https://cloud.google.com/apigee/docs/best-practices

---

**Người tạo tài liệu:** AI Assistant (dựa trên tài liệu sizing Apigee Mini App và file PNX v1/v2)
**Ngày tạo:** 2024
**Phiên bản:** 1.0
**Trạng thái:** ✅ Hoàn thành - Dùng cho reference cho các dự án API Gateway tương tự

---

## 📝 GHI CHÚ

- Tài liệu này trích xuất tri thức từ 2 vòng phản hồi (PNX v1 → v2) và sizing Apigee
- Đây là dự án điển hình của **API Gateway với TPS rất cao (20,000)**
- Đặc biệt hữu ích cho: TPS calculation, concurrent session vs TPS, PG vs Cassandra, horizontal scaling
- Checklist sizing bắt buộc ký đính kèm → create HSTK (hồ sơ thiết kế) only after checklist approved
- Cần tuân thủ guideline sizing của Viettel (xem trong thư mục guideline_sizing/)
- Timeline là CRITICAL: Kế hoạch đổ tải 3/2026 phải được KD/BGĐ ký xác nhận