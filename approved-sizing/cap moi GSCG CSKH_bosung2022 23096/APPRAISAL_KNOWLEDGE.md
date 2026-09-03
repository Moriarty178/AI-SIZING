# APPRAISAL KNOWLEDGE - GSCG CSKH (GIÁM SÁT CUỘC GỌI CSKH)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** GIÁM SÁT CUỘC GỌI CSKH BỔ SUNG 2022 (Customer Service Call Monitoring System)  
**Mã PYC:** PYC-23096  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** tungct  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### Nhóm yêu cầu chỉnh sửa:

**NHÓM 1: CƠ BẢN VÀ SOỞ CỨ**

1. **Nhận xét chung:**
   - Bổ sung thông tin sởFFFF chỉ cho mọi số liệu
   - Tính toán lại số liệu
   - Không được ước tính cho số liệu chính

2. **Mục đích sizing:**
   - Bổ sung mục đích sizing (cấp mới, bổ sung, nâng cấp?)

3. **Input data:**
   - Bổ sung sởFFFF chỉ cho các số liệu thông tin đầu vào (trang 2)
   - Nguồn dữ liệu在哪里？

**NHÓM 2: KẾT NỐI VÀ LOAD BALANCING**

4. **Network architecture:**
   - Bổ sung thông tin kết nối
   - Bổ sung thông tin cân bằng tải (Load Balancing)
   - Bổ sung yêu cầu khai báo phân tải

5. **Cấp phát tài nguyên:**
   - Cần làm rõ: Có cần cùng dải IP để chung LB không hay cấp ở đâu cũng được chỉ cần đảm bảo kết nối?
   - Tài nguyên này có trong QHĐC (Quy hoạch đầu tư) chưa?

**NHÓM 3: SIZING BỔ SUNG**

6. **Baseline sizing:**
   - Định cỡ tuyến tính bổ sung → cần đính kèm sizing cũ đã ký để làm sởFFFF chỉ
   - CANNOT size in isolation without baseline

7. **Speech processing module:**
   - Module Speech processing không rõ giá trị hệ thống hiện tại để định cỡ
   - Cần sởFFFF chỉ current system values

**NHÓM 4: SERVER CẤU HÌNH HIỆN TẠI**

8. **Baseline server - 300k calls/day:**
   - Bổ sung sởFFFF chỉ cho cấu hình server thực tế đang chạy
   - Current capacity: 300.000 cuộc gọi/ngày
   - Cấu hình:
     - CPU >= 196 Cint 2017
     - RAM >= 96 GB
     - SSD >= 1900 GB
     - Có card HBA (Host Bus Adapter)
   - **Yêu cầu:** Minh chứng cho con số này

**NHÓM 5: TÍNH TOÁN VÀ BẢNG TỔNG HỢP**

9. **Firewall và Load Balancer:**
   - Tính thông lượng FW, LB
   - Bổ sung sởFFFF chỉ calculation

10. **Table formatting:**
    - Lập bảng giá trị cho từng cụm
    - Don't mix different cluster types in one table

11. **Bảng tổng hợp:**
    - Bảng tổng hợp đề xuất bổ sung đầy đủ thông tin cấu hình xin cấp phát
    - Bổ sung thông tin FW, LB

---

## 💡 TRI THỨC RÚT RA

### 1. Additional capacity sizing - ALWAYS reference baseline

**Principle:** Don't size in vacuum

**WRONG approach:**
```
Need additional: 50,000 calls/day
→ Size from scratch without baseline ❌
```

**CORRECT approach:**
```
Step 1: Reference old signed sizing
  - Old sizing: PYC-XXXXX (signed date: [date])
  - Old capacity: 300,000 calls/day
  - Old config: CPU 196 Cint, RAM 96 GB, SSD 1900 GB

Step 2: Calculate scaling factor
  - Additional need: 50,000 calls/day
  - Scaling factor = 50,000 / 300,000 = 0.1667 (16.67%)

Step 3: Calculate additional resources
  - Additional CPU = 196 × 0.1667 × 1.1 (safety) = 35.9 Cint
  - Additional RAM = 96 × 0.1667 × 1.1 = 17.6 GB
  - Additional SSD = 1900 × 0.1667 × 1.1 = 349 GB

Step 4: Add to baseline
  - New total = 300k + 50k = 350k calls/day
  - New CPU = 196 + 36 = 232 Cint
  - New RAM = 96 + 18 = 114 GB
  - New SSD = 1900 + 349 = 2249 GB
```

**Document must include:**
```
Baseline Reference:
- Signed sizing document: [PYC number]
- Signed date: [date]
- Approved configuration: [spec]
- Current capacity: [calls/day]

Additional Requirement:
- Additional load: [calls/day]
- Scaling calculation: [formula]
- Additional resources needed: [spec]
```

### 2. Load Balancer IP range consideration

**Question:** Same IP range or anywhere?

**Scenario A: Same IP range (preferred for LB)**
```
Benefits:
- Easy routing configuration
- Single firewall rule
- Simplified monitoring
- Same latency characteristics

Configuration:
- APP servers: 10.60.135.0/24
- VIP (Virtual IP): 10.60.135.100
- All servers in same /24 subnet
```

**Scenario B: Different IP ranges**
```
Benefits:
- More flexible deployment
- Can use different DCs
- Better isolation

Challenges:
- Complex routing
- Multiple firewall rules
- Different latency
- Harder monitoring

Configuration:
- APP servers: 10.60.135.0/24, 10.60.136.0/24
- VIP: 10.60.135.100
- Need static routes or BGP
```

**Best practice:**
```
If possible: Keep in same IP range
Reason: Easier operations, better performance

If not possible: Document network design
- Include routing diagram
- Include firewall rules
- Include latency testing
```

### 3. Speech processing sizing challenge

**Problem:** Speech processing module không có current system values

**Why difficult:**
- Speech processing is resource-intensive
- Dependent on: Call duration, codec, quality
- CPU-intensive (transcoding, ASR, TTS)
- Storage-intensive (audio recordings)

**Approach:**

**Option A - If system exists elsewhere:**
```
Find reference:
1. Similar GSCG system in production
2. Measure actual usage per call
3. Extrapolate to required capacity

Example:
- Reference system: GSCG region HCM
- Currently handles: 100k calls/day
- Speech module usage: 50 Cint per call
- Project for 300k calls/day = 150 Cint
```

**Option B - If no reference:**
```
Estimate from vendor specs:
1. Check codec specs (G.711, G.729, Opus?)
2. Check ASR (Automatic Speech Recognition) requirements
3. Check TTS (Text-to-Speech) requirements
4. Include buffer + safety factor

Example estimate:
- Per call processing: 20-50 Cint (codec dependent)
- Target: 50,000 calls/day
- Peak concurrency: 50,000 / 86400 × 3600 = 2,083 concurrent
- CPU needed: 2,083 × 30 Cint = 62,490 Cint
Safety ×1.2: 75,000 Cint
```

**Option C - Bench test:**
```
1. Set up test environment
2. Run actual speech processing
3. Measure resource usage
4. Project to production scale
```

### 4. HBA card - When needed?

**HBA (Host Bus Adapter):** Specialized card for storage connectivity

**When needed:**
- SAN (Storage Area Network) connectivity
- Fiber Channel (FC) storage
- High-throughput storage requirements
- Low-latency storage access

**GSCG case:**
```
Current system has HBA:
- Storage: 1900 GB SSD
- Question: Is this SAN-attached SSD?

If YES (HBA present):
- Likely SAN storage
- Benefits: Shared storage, better reliability
- Impact: New servers need HBA too
- Cost: HBA adds $1000-$2000 per server

If NO (HBA not needed):
- Direct-attached storage (DAS)
- Local SSDs
- No HBA required
```

**Document must clarify:**
```
Storage Architecture:
- Type: SAN / DAS / NAS?
- Connectivity: HBA / Direct / iSCSI?
- If HBA: Model, Speed (8Gbps, 16Gbps, 32Gbps?)
- Why 1900 GB? IOPS requirement?
```

### 5. Cluster-specific sizing tables

**Don't mix different cluster types!**

**WRONG:**
```
One big table mixing:
- APP servers
- DB servers
- Speech processing
- Storage servers
❌ Confusing, hard to validate
```

**CORRECT:**
```
Table 1: APP Cluster
| Metric | Server | Total |
|--------|--------|-------|
| CPU | 47 Cint | 47 × 5 = 235 Cint |
| RAM | 114 GB | 114 × 5 = 570 GB |
| SSD | 300 GB | 300 × 5 = 1500 GB |

Table 2: Database Cluster
| Metric | Server | Total |
|--------|--------|-------|
| CPU | 60 Cint | 60 × 3 = 180 Cint |
| RAM | 256 GB | 256 × 3 = 768 GB |
| SSD | 2000 GB | 2000 × 3 = 6000 GB |

Table 3: Speech Processing Cluster
| Metric | Server | Total |
|--------|--------|-------|
| CPU | 75 Cint | 75 × 3 = 225 Cint |
| RAM | 128 GB | 128 × 3 = 384 GB |
| SSD | 500 GB | 500 × 3 = 1500 GB |
```

**Benefits:**
- Clear separation of concerns
- Easy to validate each cluster
- Easy to scale clusters independently
- Matches architecture document

### 6. Firewall/LB sizing for VoIP traffic

**VoIP (Voice over IP) has special characteristics:**

**Protocol stack:**
```
SIP (Session Initiation Protocol) - Signaling
RTP (Real-time Transport Protocol) - Audio
```

**Bandwidth calculation:**

**SIP signaling:**
```
Per call: ~100 bytes/sec
50,000 calls/day = 50,000 × 100 / 86400 = 58 KB/s
Peak (10×): 580 KB/s = 4.6 Mbps
```

**RTP audio (G.711 codec):**
```
Per call: 64 kbps (uncompressed)
50,000 calls/day = 50,000 × 64 / 86400 = 37 kbps
Peak concurrent: 2,083 calls
RTP bandwidth: 2,083 × 64 kbps = 133 Mbps
```

**Total bandwidth:**
```
Signaling: 4.6 Mbps
Audio: 133 Mbps
Total: 137.6 Mbps
Safety ×1.5: 206 Mbps
→ 1 Gbps link is SUFFICIENT
```

**Firewall/LB sizing:**
```
Throughput: 206 Mbps (peak)
Connections: 2,083 concurrent
Packets/sec: ~500,000 pps (estimate)
→ Use 1 Gbps firewall/LB
→ Or 10 Gbps for future growth
```

### 7. QHĐC (Quy hoạch đầu tư) - Investment planning

**Câu hỏi:** Tài nguyên này có trong QHĐC chưa?

**Why important:**
- QHĐC = Capital investment plan
- Resources must be allocated and approved
- Cannot provision if not in budget

**Process:**
```
Step 1: Check QHĐC
- Does current QHĐC include this sizing?
- If YES: Aligned, can proceed
- If NO: Need amendment or new request

Step 2: If not in QHĐC
- Submit request for QHĐC amendment
- Include business justification
- Include cost-benefit analysis
- Get approval from finance/planning

Step 3: Document compliance
- Reference QHĐC item: [code]
- Approval date: [date]
- Approved amount: [VND]
```

**Document must include:**
```
QHĐC Compliance:
- QHĐC reference: [item code]
- Approved budget: [amount]
- Allocated resources: [servers, storage, network]
- If not in QHĐC: Amendment request [number]
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Baseline (300k calls/day):**
- CPU: >= 196 Cint 2017
- RAM: >= 96 GB
- SSD: >= 1900 GB
- HBA: Yes (for SAN connectivity)

**Bổ sung (50k calls/day - scaling factor 16.67%):**
- Additional CPU: ~36 Cint
- Additional RAM: ~18 GB
- Additional SSD: ~350 GB

### Quy mô hệ thống
- Current capacity: 300,000 cuộc gọi/ngày
- Additional need: 50,000 cuộc gọi/ngày
- Total after expansion: 350,000 cuộc gọi/ngày
- Module: Giám sát cuộc gọi CSKH

### Modules
- Call monitoring core
- Speech processing (ASR/TTS)
- Storage (audio recordings)
- Load balancing
- Firewall

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. Additional sizing ALWAYS needs baseline
- Reference old signed sizing document
- Calculate scaling factor from baseline
- Don't estimate from scratch

### 2. Load balancer IP range affects architecture
- Same subnet: Easier routing, better performance
- Different subnets: Flexible but complex
- Document network design clearly

### 3. Speech processing needs special handling
- CPU-intensive (transcoding, ASR, TTS)
- Find reference system or benchmark
- Include codec specifications

### 4. HBA card indicates SAN storage
- If baseline has HBA, new servers need it too
- SAN vs DAS affects architecture
- Clarify storage architecture

### 5. Cluster-specific tables are mandatory
- Don't mix different cluster types
- Separate table for each module type
- Makes validation easier

### 6. VoIP has unique bandwidth characteristics
- SIP signaling: Low bandwidth
- RTP audio: High bandwidth
- Calculate both separately
- Use codec-specific values

### 7. QHĐC compliance is mandatory
- Resources must be in investment plan
- If not, need amendment request
- Document QHĐC reference

### 8. Firewall/LB sizing for VoIP
- Consider protocol stack (SIP + RTP)
- Calculate peak concurrent calls
- Don't just use average daily rate

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (thiếu baseline reference, nhiều module không rõ)  
**Vấn đề chính:** Thiếu baseline sizing reference, speech processing không có current values, network architecture không rõ

**Đặc điểm hệ thống:**
- GSCG CSKH: Giám sát cuộc gọi CSKH
- VoIP system (SIP signaling + RTP audio)
- Modules: Core monitoring, Speech processing, Storage
- Expansion from 300k to 350k calls/day

**Khuyến nghị:**
- Attach old signed sizing as baseline
- Calculate scaling from baseline (16.67% growth)
- Clarify speech processing current values
- Find reference system or run benchmark
- Specify HBA requirement (SAN vs DAS)
- Create cluster-specific sizing tables
- Calculate VoIP bandwidth for FW/LB
- Document IP range strategy for LB
- Verify QHĐC compliance
- Include network architecture diagram