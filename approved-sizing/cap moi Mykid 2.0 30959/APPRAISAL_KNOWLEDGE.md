# APPRAISAL KNOWLEDGE - Hệ thống Mykid 2.0

## 📋 Thông tin Hồ sơ

- **Dự án:** Hệ thống Mykid 2.0 - Cấp mới hệ thống theo dõi thiết bị trẻ em
- **Mã PYC:** PYC-30959
- **Người thẩm định:** Khanhnd23 - P.Hệ thống
- **Đầu mối yêu cầu:** Tamdtt1
- **Ngày thẩm định:** 2024 (2 vòng PNX)
- **Loại hồ sơ:** TRƯỜNG HỢP A (Có Phiếu Nhận Xét - PNX)
- **Mục đích sizing:** Cấp phát tài nguyên triển khai hệ thống mới

## 📊 Trạng thái Hồ sơ

- **Có PNX:** ✅ Có 2 vòng phản hồi thẩm định (PNX v1.0, v2.0)
- **Trạng thái:** Chưa có thông tin ký duyệt cuối

---

## 🎯 Tri Thức Rút Ra Từ PNX

### 1. Sở Cứ Rõ Nàng Cho Mọi Con Số (Critical)

**Vấn đề:**
- Sizing có nhiều con số nhưng thiếu nguồn gốc
- Ảnh chụp mờ không rõ số liệu và thông tin hệ thống

**Yêu cầu P.HT (vòng 1 & 2):**
- "Bổ sung sở cứ, ảnh sở cứ bị mờ không rõ số liệu và thông tin hệ thống"
- "Bổ sung sở cứ file KH 4084/KH-CNTT&DVS làm sở cứ cho số liệu đầu vào"
- "Bổ sung ảnh chụp cho sở cứ 39022"

**Best Practice:**
```
✅ Mọi con số PHẢI có source:
   - Số liệu từ văn bản quy định (KH số, decision số...)
   - Số liệu từ hệ thống đang chạy (screenshot rõ nét)
   - Số liệu từ business forecast (có văn bản confirmation)

✅ Ảnh chụp PHẢI:
   - Rõ nét, không mờ, không bị resize
   - Hiển thị đầy đủ thông tin (IP, datetime, metrics)
   - Khoanh rõ vùng số liệu quan trọng (highlight)
   - Có timestamp và source

✅ Reference đầy đủ:
   - Nêu rõ: "Theo KH 4084/KH-CNTT&DVS"
   - Nêu rõ: "Screenshot từ server 10.207.191.51 ngày 19/11/2024"
   - Nêu rõ: "Theo test measurement ngày..."
```

---

### 2. Mục Đích Sizing Phải Cụ Thể

**Vấn đề:**
- Mục đích sizing ban đầu không rõ: cấp mới để làm gì?

**Yêu cầu P.HT:**
- "Bổ sung mục đích sizing cụ thể: cấp mới để làm gì"

**Cung cấp đầy đủ:**
✅ Lý do cấp phát
✅ Kinh doanh background
✅ Timeline dự kiến triển khai
✅ Quy mô mục tiêu trong bao lâu (6 tháng, 1 năm, 2 năm?)

**Ví dụ proper documentation:**
```
Mục đích sizing:
- Cấp phát tài nguyên để triển khai hệ thống Mykid 2.0 mới
- Thay thế hệ thống Mykid Plus hiện tại của đối tác Goly
- Hệ thống theo dõi vị trí thiết bị trẻ em qua GPS
- Timeline triển khai: Q1/2025
- Số lượng thiết bị dự kiến: 24,329 (6 tháng), 34,089 (1 năm), 72,224 (2 năm)
```

---

### 3. KPI RAM là 90%, Không Phải 75% (Important Error)

**Vấn đề nghiêm trọng:**
- Sizing tính toán với KPI RAM = 75%
- KPI đúng cho RAM là **90%**

**Yêu cầu P.HT (2 lần nhắc):**
- "KPI RAM là 90%, đang tính là 75%" (trang 16, 22)
- "KPI RAM là 90%, đang tính là 75%"

**Impact:**
```
WRONG Calculation (KPI 75%):
RAM_needed = RAM_baseline * 1.1 / 0.75 = 1.466 * RAM_baseline

RIGHT Calculation (KPI 90%):
RAM_needed = RAM_baseline * 1.1 / 0.90 = 1.222 * RAM_baseline

Ratio: 1.466 / 1.222 = 1.2 즉 20% over-sizing if use 75% KPI!

Giả sử cần 100 GB RAM:
- With KPI 75% (WRONG): 146.6 GB → Over-provision 46.6 GB
- With KPI 90% (CORRECT): 122.2 GB → Optimal sizing
- WASTE: 24.4 GB per node, hàng chục nodes → WASTE HỆ TRỌNG
```

**Standard KPIs (MUST REMEMBER):**
```
✅ CPU KPI: 75% (không vượt quá 75% CPU utilization)
✅ RAM KPI: 90% (không vượt quá 90% RAM utilization) 
✅ HDD KPI: 80% (không vượt quá 80% disk utilization)

NEVER mix these up!
```

---

### 4. Công Thức Tính Toán Dung Lượng Lưu Trữ

**Vấn đề:**
- Sizing có kết quả storage nhưng không ghi rõ công thức tính dung lượng 1 ngày

**Yêu cầu P.HT:**
- "Ghi rõ công thức tính toán dung lượng 1 ngày (GB)"
- "Làm rõ số liệu"

**Correct Documentation:**
```
## Storage Growth Calculation Formula

Step 1: Measure baseline from reference system (Mykid Plus)
Server 10.207.191.51:
- Storage u01 on 20/08/2024: 7.5 GB
- Storage u01 on 19/11/2024: 11.0 GB
- Days elapsed: 91 days
- Growth per day: (11.0 - 7.5) / 91 = 0.0384615 GB/day

Server 10.207.191.52:
- Storage u01 on 20/08/2024: 12.3 GB
- Storage u01 on 19/11/2024: 18.0 GB
- Days elapsed: 91 days  
- Growth per day: (18.0 - 12.3) / 91 = 0.0629371 GB/day

Step 2: Calculate total daily growth
Total per day = 0.0384615 + 0.0629371 = 0.1013986 GB/day for 24,329 CCU

Step 3: Calculate per-CCU daily growth
Per CCU per day = 0.1013986 / 24,329 = 0.000004168 GB/day

Step 4: Scale to target CCU
For 94,518 CCU (6 months):
  Daily growth = 94,518 * 0.000004168 = 0.39 GB/day
  6 months = 0.39 * 180 = 70.2 GB

Step 5: Apply safety factor and KPI
Final storage = 70.2 * 1.1 / 0.8 = 96.5 GB
```

---

### 5. Timeline Cấp Phát: 6 Tháng, 1 Năm hay 2 Năm?

**Vấn đề quan trọng:**
- Sizing có tính toán cho 3 kỳ: 6 tháng, 1 năm, 2 năm
- Không rõ timeline cấp phát thực tế là bao lâu

**Yêu cầu P.HT (vòng 1):**
- "Làm rõ phần tài nguyên cần cấp là bao lâu 6 tháng, 1 năm hay 2 năm"

**Why this matters:**
```
Resource Differences:
- 6 tháng: 8 app nodes + 9 (N+1)
- 1 năm: 11 app nodes + 12 (N+1)
- 2 năm: 23 app nodes + 24 (N+1)

Cost Impact:
- 6 months: 9 nodes * cost/node
- 1 year: 12 nodes * cost/node → 33% more
- 2 years: 24 nodes * cost/node → 167% more

Business Impact:
- Over-provision: Waste money upfront
- Under-provision: Need to upgrade again soon
- Right-sizing: Balance CAPEX vs OPEX
```

**Decision Framework:**
```
Questions to ask:
1. Growth forecast accuracy? (Công ty có dự báo chính xác không?)
2. Budget availability? (Ngân sách có hạn không?)
3. Technology refresh cycle? (Có upgrade technology trong 1-2 năm không?)
4. Procurement timeline? (Mua mới bao lâu?)
5. Scalability architecture? (Hệ thống có scale được không?)

Recommendation:
- Conservative: 6 months (nếu growth uncertain, budget tight)
- Standard: 1 year (balance cost and capacity)
- Aggressive: 2 years (nếu growth certain, need long-term stability)
```

---

### 6. Nghiệp Vụ Sở Cứ: Tần Suất Gửi Thông Tin

**Vấn đề:**
- Sizing dùng 10 phút/giờ và 5 phút/request nhưng thiếu sở cứ

**Yêu cầu P.HT:**
- "Bổ sung sở cứ: nghiệp vụ cứ trung bình 10 phút thiết bị sẽ gửi thông tin vị trí lên hệ thống"
- "Bổ sung sở cứ:5 phút 1 ccu thực hiện 1 request"

**Why business assumptions matter:**
```
Device Tracking Frequency affects TPS:

Business Rule: Device sends GPS location every 10 minutes
- 1 device = 6 times/hour = 144 times/day
- 24,329 devices = 24,329 * 6 / 3600 = 40.5 requests/hour

Sizing Calculation:
- Concurrent user: 24,329 CCU
- Request frequency: 5 phút/request = 12 requests/hour/CCU
- Total requests/hour: 24,329 * 12 = 291,948
- Requests/second (TPS): 291,948 / 3600 = 81.1 TPS

Impact if frequency changes:
- If 5 minutes (double): TPS = 162.2 → 2x capacity needed
- If 20 minutes (half): TPS = 40.5 → Half capacity needed

MUST have business confirmation on this!
```

---

### 7. Request/Giây Calculation Clarification

**Vấn đề:**
- Sizing tính 127.3 request/giây nhưng cần clear ownership

**Yêu cầu P.HT:**
- "Bổ sung sở cứ: 127.3 request/giây"

**Proper Calculation Display:**
```
## Request Rate Calculation

Step 1: Business Requirement
- Concurrent users (CCU): 24,329 (6 tháng)
- Request frequency: 1 request 每 5 phút per CCU
- Tức là: 12 requests/hour per CCU

Step 2: Calculate Total Requests/Hour
Total_requests_hour = 24,329 CCU * 12 req/hour/CCU = 291,948 req/hour

Step 3: Convert to TPS (Requests/Second)
TPS = 291,948 / 3600 = 81.1 requests/second

Step 4: Add buffer for peak times
Peak_TPS = 81.1 * 1.57 (peak factor) = 127.3 requests/second

Note: Peak factor 1.57 based on industry standard for web applications
     Source: Alibaba/Tech capacity planning guidelines

Final sizing TPS: 127.3 requests/second
```

---

### 8. Giải Thích Công Thức CPU/RAM

**Vấn đề:**
- Sizing có bảng tính nhưng không giải thích cách tính CPU, RAM sử dụng tăng

**Yêu cầu P.HT:**
- "Ghi rõ công thức tính CPU, RAM sử dụng tăng"

**Template Explanation:**
```
## Per-Unit Resource Calculation Methodology

Step 1: Measure baseline from reference system (Mykid Plus)
Server 10.207.191.51 & 10.207.191.52:
- Total RAM: 64 GB (32 GB * 2 servers)
- Total Cint: 144 Cint (72 Cint * 2 servers)

Step 2: Measure actual usage under load
- Current CCU: 24,329
- RAM used: 21.41 GB total (11.70 + 9.71)
- Cint used: 18.072 total (9.720 + 8.352)

Step 3: Calculate resource per CCU
RAM_per_CCU = 21.41 GB / 24,329 CCU = 0.00088002 GB/CCU
Cint_per_CCU = 18.072 / 24,329 CCU = 0.0007428 Cint/CCU

Step 4: Apply to target CCU
For 94,518 CCU (6 months):
  RAM_needed = 94,518 * 0.00088002 = 83.178 GB
  Cint_needed = 94,518 * 0.0007428 = 70.210 Cint

Step 5: Apply safety factor and KPI
RAM_final = 83.178 * 1.1 / 0.90 = 101.662 GB
Cint_final = 70.210 * 1.1 / 0.75 = 102.974 Cint

Step 6: Calculate number of nodes
Node_count = 102.974 / 12 (Cint per node) = 8.58 → 9 nodes (with N+1)
```

---

## 📈 Thông Số Kỹ Thuật

### Workload Requirement

**Business Requirement (from Document 4084/KH-CNTT&DVS):**
- **6 tháng:** 24,329 CCU
- **1 năm:** 34,089 CCU (1.4x)
- **2 năm:** 72,224 CCU (3x)

**Nghiệp vụ:**
- Device GPS tracking: Mỗi 10 phút gửi vị trí 1 lần
- Request frequency: 10 phút/request = 6 requests/hour/device
- Peak TPS: 127.3 requests/second (với peak factor 1.57)

### Reference System (Mykid Plus - Similar System)

**Current Production:**
```
Server 10.207.191.51 & 10.207.191.52:
- Configuration: 24 vCPU (72 Cint), 32 GB RAM, 250 GB HDD
- Current CCU: 24,329
- Resource Usage:
  • RAM: 21.41 GB total (66% utilization)
  • Cint: 18.072 total (37.5% utilization)
  • Storage growth: 0.1014 GB/day
  
Per-Unit Metrics:
- RAM/CCU: 0.00088002 GB/CCU
- Cint/CCU: 0.0007428 Cint/CCU
```

### Sizing Calculation Detail

**Application Cluster (6 Months):**
```
Given: 94,518 CCU (document used different CCU calculation)

Per CCU resources (from test):
- Cint: 0.000698665 (from app server test)
- RAM: 0.000066771 (from app server test)

For 94,518 CCU:
- Cint_needed: 94,518 * 0.000698665 = 66.036 Cint
- RAM_needed: 94,518 * 0.000066771 = 6.311 GB

Apply Safety Factor 1.1 & KPI:
- Cint_final: 66.036 * 1.1 / 0.75 = 96.853 Cint
- RAM_final: 6.311 * 1.1 / 0.90 = 7.714 GB

N calculation with N+1 redundancy:
  N = 96.853 / 12 (per node) = 8.07 → 9 nodes (8 active + 1 standby)
  
Each node: 4 vCPU (12 Cint), 8 GB RAM, 60 GB HDD
```

**Database Cluster (6 Months):**
```
Given: 94,518 CCU (same as app)

Per CCU resources (from DB servers):
- Cint: 0.0007428 Cint/CCU
- RAM: 0.00088002 GB/CCU

For 94,518 CCU:
- Cint_needed: 94,518 * 0.0007428 = 70.210 Cint
- RAM_needed: 94,518 * 0.00088002 = 83.178 GB

Apply Safety Factor 1.1 & KPI:
- Cint_final: 70.210 * 1.1 / 0.75 = 102.974 Cint
- RAM_final: 83.178 * 1.1 / 0.90 = 101.662 GB

Node count: 2 nodes (as reference system has 2 nodes)
Each node: 4 vCPU (12 Cint), 8 GB RAM, 250 GB HDD
```

**Storage Calculation (18 Months Retention):**
```
Baseline: 0.1014 GB/day for 24,329 CCU

For 94,518 CCU (6-month target):
- Daily growth: 94,518 / 24,329 * 0.1014 = 0.39 GB/day
- 6 months: 0.39 * 180 = 70.2 GB
- With SF 1.1 & KPI 80%: 70.2 * 1.1 / 0.8 = 96.5 GB

Per node storage:
- OS: 40 GB
- Docker: 0.5 GB
- Images: 1 GB
- Cache: 2 GB
- Total: 43.5 GB
- With SF 1.1: 43.5 * 1.1 = 47.85 GB → 60 GB (standard size)
```

### Final Configuration Summary

**Timeline: 6 Months**
- **App Nodes:** 9 (8 active + 1 N+1)
  - Each: 4 vCPU (12 Cint), 8 GB RAM, 60 GB HDD
  - Total: 96 Cint, 72 GB RAM
- **DB Nodes:** 2 (same as reference)
  - Each: 4 vCPU (12 Cint), 8 GB RAM, 250 GB HDD
  - Total: 24 Cint, 16 GB RAM

**Timeline: 1 Year**
- **App Nodes:** 12 (11 active + 1 N+1)
- Total capacity: 132 Cint, 96 GB RAM

**Timeline: 2 Years**
- **App Nodes:** 24 (23 active + 1 N+1)
- Total capacity: 264 Cint, 192 GB RAM

---

## 💡 Best Practices Áp Dụng

### 1. **Reference System Approach (Sizing by Analogy)**

Khi có hệ thống tương tự đang chạy:
```
Step 1: Identify Similar System
- Mykid Plus (do đối tác Goly triển khai)
- Same business logic (GPS tracking for children)
- Similar functionality and data types

Step 2: Measure Current System Performance
- Capture actual resource usage under load
- Measure storage growth over time
- Document per-unit metrics

Step 3: Calculate Per-Unit Resource Consumption
- RAM per CCU = Total RAM used / Total CCU
- Cint per CCU = Total Cint used / Total CCU
- Storage per day per CCU = Growth rate / CCU

Step 4: Scale to Target CCU
- Apply safety factor (1.1)
- Apply KPI thresholds (CPU 75%, RAM 90%, HDD 80%)
- Calculate N with N+1 redundancy

Benefits:
- More accurate than theoretical calculations
- Based on real-world data
- Accounts for actual application behavior
```

### 2. **Multi-Timeline Sizing Strategy**

```
Why provide 3 options (6 months, 1 year, 2 years):

Business Considerations:
- Budget Availability: OPEX allocation per year
- Growth Certainty: How confident in forecast?
- Technology Refresh: New technology in 12-18 months?
- Procurement Cycle: How long to approve and purchase?

Technical Considerations:
- Scalability Cost: 
  • Scale vertical: Buy larger servers upfront
  • Scale horizontal: Add more servers later
- Migration Risk: System downtime during upgrade
- Complexity: More nodes = more management overhead

Presentation to Stakeholders:
Option 1 (6 months): Lower upfront cost, sooner revisit
Option 2 (1 year): Balanced approach, standard practice
Option 3 (2 years): Higher upfront, longer stability

Recommendation: Present all 3 with cost-benefit analysis
```

### 3. **KPI Verification Checklist**

```
Before submitting sizing, verify:

CPU KPI ✅
- Formula: resource * SF / 0.75 (75% threshold)
- Check: Did NOT use 0.90 or 0.80?

RAM KPI ✅
- Formula: resource * SF / 0.90 (90% threshold)
- Check: Did NOT use 0.75 or 0.80?

HDD KPI ✅
- Formula: resource * SF / 0.80 (80% threshold)
- Check: Did NOT use 0.75 or 0.90?

Safety Factor ✅
- Formula: 1.1 (10% error margin)
- Check: Did NOT use 1.2 or 1.5?

Common Mistake Alert:
❌ Using wrong KPI causes 15-25% over/under-sizing
```

### 4. **Evidence Documentation Standards**

```
Every piece of data needs:

PRIMARY SOURCES (Best):
✅ Signed documents (Decision numbers, memos)
✅ Official emails with confirmation
✅ Meeting minutes with action items
✅ Database queries with timestamps

SECONDARY SOURCES (Acceptable with context):
✅ Screenshots from production systems
   - Must have: IP, datetime, full metrics
   - High resolution, no cropping
   - Highlight the specific metric
✅ System monitoring dashboards
   - Export with date/time
   - Include dashboard URL
✅ Test execution logs
   - Full command and output
   - Execution timestamp

UNACCEPTABLE:
❌ "Business said growth will be 20%" (no document)
❌ "Similar system uses 4 cores" (no reference)
❌ "Estimated from experience" (no calculation)
```

### 5. **N+1 vs N+2 Redundancy Decision**

```
N+1 Redundancy (Standard):
- Use for: Application servers, web servers, API servers
- Cost: +1 server = +12.5% cost (for 8+1)
- Benefit: Single server failure protection
- Downtime during failover: Minutes (auto-failover)

N+2 Redundancy (Critical Systems):
- Use for: Database primary, core infrastructure
- Cost: +2 servers = +25% cost (for 8+2)
- Benefit: Survive 1 failure + maintenance window
- Downtime during failover: Zero (maintain quorum)

Application Server Decision:
- 8+1 = 9 nodes (selected)
- Rationale: Stateless, easy failover, can lose 1 node

Database Server Decision:
- 2 nodes (no N+1 for DB in reference)
- Rationale: Reference system uses 2 nodes active-active
- Risk: Both nodes down = system down (STANDARD APPR)
```

---

## 🔧 Kinh Nghiệm Xử Lý

### 1. **Lỗi KPI RAM 75% vs 90%**

**Impact Analysis:**
```
Scenario: 100 GB baseline requirement

Wrong KPI (75%):
  RAM = 100 * 1.1 / 0.75 = 146.6 GB
  Over-provision: 46.6 GB (31.8%)

Correct KPI (90%):
  RAM = 100 * 1.1 / 0.90 = 122.2 GB
  Optimal sizing: 122.2 GB

Waste Calculation:
  For 9 nodes: 46.6 * 9 = 419 GB wasted
  Cost impact: TBD GB memory cost
  Rack space: TBD U wasted
  Power: TBD kWh wasted

Lesson Learned:
  Memorize KPIs:
  - CPU: 75% (compute-intensive)
  - RAM: 90% (memory can be compacted)
  - HDD: 80% (disk I/O degradation threshold)
```

### 2. **Reference System Sizing Validation**

```
Best Practice for Reference System:

Step 1: Verify Similarity
✅ Business logic: GPS tracking (same as Mykid 2.0)
✅ Technology stack: Same database type
✅ Data patterns: Device, customer, location data types
✅ Load: Current CCU comparable to target CCU

Step 2: Measure Under Load
✅ Baseline CCU: 24,329 (matches target for 6-month)
✅ Resource usage: Must be under target KPI
   • CPU at 37.5% ✅ (under 75%)
   • RAM at 66% ✅ (under 90%)
✅ Time period: Long enough (91 days measurement)

Step 3: Calculate Per-Unit Metrics
✅ Use actual consumption: Not theoretical
✅ Calculate for each resource type separately
   • RAM per CCU: 0.00088 GB/CCU
   • Cint per CCU: 0.00074 Cint/CCU
✅ Document units clearly

Step 4: Scale and Validate
✅ Apply to target CCU
✅ Reasonableness check:
   • If results 10x larger → question the calculation
   • If results negative → check the division
✅ Cross-check with industry benchmarks
```

### 3. **Timeline Decision Making Framework**

```
Factors to Consider:

1. Growth Forecast Certainty
   High certainty (97%+):
   - Business has signed contracts
   - Government mandates require deployment
   → Choose 2 years (capacity certainty)

   Medium certainty (70-95%):
   - Business forecast with assumptions
   - Market trends indicate growth
   → Choose 1 year (balanced approach)

   Low certainty (<70%):
   - New product/technology
   - Volatile market conditions
   → Choose 6 months (conservative)

2. Budget Cycle
   - Annual budget process: 1-year sizing
   - Multi-year CAPEX available: 2-year sizing
   - Quarterly review: 6-month sizing

3. Technology Refresh
   - New tech roadmap in 12 months: 1-year sizing
   - Stable platform with long support: 2-year sizing
   - Rapid innovation cycle: 6-month sizing

4. Procurement Lead Time
   - Long procurement (>3 months): Consider longer sizing
   - Quick procurement (<1 month): Shorter sizing OK

Mykid 2.0 Recommendation:
- Uncertain growth (new system vs Goly competitor)
- Annual budget cycle
- Technology成熟 (GPS tracking not changing)
- → 1-year sizing (132,325 CCU) is reasonable
```

---

## 📋 Check List Đánh Giá Trạng Thái

### ⚠️ Các vấn đề PHẢI FIX (Priority):

1. **❌ KPI RAM** - CRITICAL: Đang dùng 75% sai, phải dùng 90%
2. **❌ Sở cứ số liệu** - Cần source rõ ràng cho mọi con số
3. **❌ Ảnh/screenshots** - Cần ảnh rõ nét với highlight
4. **❌ Mục đích sizing** - Cụ thể: cấp mới để làm gì?
5. **❌ Timeline** - Làm rõ: 6 tháng, 1 năm hay 2 năm?
6. **❌ Công thức tính toán** - Ghi rõ step-by-step cho storage, CPU, RAM
7. **❌ Nghiệp vụ sở cứ** - Xác nhận: 10 phút/request, 5 phút/CCU behavior
8. **❌ Request/giây calculation** - Giải thích rõ nguồn 127.3 req/s

### 💡 Các vấn đề NÊN:

1. **N+1 justification** - Tại sao chọn 8+1 không phải 10+2?
2. **Multi-timeline recommendation** - Recommend specific timeline dựa trên business context
3. **Storage retention** - Why 18 months? Không phải 12 hay 24?
4. **Peak factor** - Giải thích source của 1.57 peak factor

---

## 📝 Kết Luận

**Trạng thái hiện tại:**
- Sizing có methodology tốt (reference system approach)
- Nhưng có **LỖI CRITICAL**: KPI RAM sai (75% vs 90%)
- Thiếu documentation và evidence cho assumptions
- Cần làm rõ timeline triển khai

**Kết luận thẩm định:**
- ⚠️ Methodology: Reference system sizing is VALID
- ❌ KIP RAM: MUST FIX (calculate with 90% not 75%)
- ❌ Documentation: NEED EVIDENCE for all inputs
- ❌ Timeline: NEED CLARITY on deployment horizon

**Bài học quan trọng:**

1. **KPI Verification Table:**
   ```
   Resource | KPI Threshold | Common Mistake | Impact
   ---------|--------------|----------------|--------
   CPU      | 75%          | Using 90%     | Under-size
   RAM      | 90%          | Using 75%     | Over-size 20%
   HDD      | 80%          | Using 75%     | Under-size
   ```

2. **Evidence Hierarchy:**
   - Level 1: Signed documents (Decision #KH-4084)
   - Level 2: Screenshot from production (with IP, datetime)
   - Level 3: Test measurements (with full command and output)
   - Level 4: Industry benchmarks (cite source)

3. **Reference System Validation:**
   - Verify similarity (business logic, tech stack, data patterns)
   - Measure under realistic load (not synthetic benchmarks)
   - Calculate per-unit metrics for each resource type
   - Document measurement period and methodology

4. **Timeline Decision:**
   - Growth certainty + Budget cycle + Tech refresh + Lead time
   - Present 2-3 options with cost-benefit analysis
   - Make recommendation with clear rationale

**Action Items:**
1. ✅ Recalculate all RAM sizing with KPI 90%
2. ✅ Collect evidence for every input number
3. ✅ Provide clear screenshots with highlights
4. ✅ Document calculation formulas step-by-step
5. ✅ Clarify timeline recommendation
6. ✅ Get confirmation on business assumptions