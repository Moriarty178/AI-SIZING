# APPRAISAL KNOWLEDGE - CMP (CONTENT MANAGEMENT PLATFORM)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG CMP (Content Management Platform)  
**Mã PYC:** PYC-35119  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 2 VÒNG (TRƯỜNG HỢP A)  
**Số vòng PNX:** 2 (v3.0 → v4.0v2)  
**Đầu mối:** thuyttt12  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét vòng 1

**Thẩm định viên:** thongnv31 (Phòng Hệ thống)

#### Yêu cầu chỉnh sửa nhóm 1: Thông tin cơ bản

1. **Kết nối hệ thống:**
   - Bổ sung thông tin kết nối của hệ thống CMP với các hệ thống khác
   - Thiếu scheme mạng connectivity

2. **Mục đích sizing:**
   - Cần làm rõ: Đây là hệ thống mới hoàn toàn hay bổ sung tài nguyên để chạy song song với hệ thống cũ?
   - Impact assessment: Migration strategy là gì?

#### Yêu cầu chỉnh sửa nhóm 2: Sở cứ và Input data

3. **Input sizing đáng ngờ:**
   - "3,000,000 TB cho 1,080 người dùng" - CON SỐ VÔ LÝ!
   - 3 triệu TB = 3 Exabyte - KHÔNG THỂ CHO CHỈ 1080 users
   - **Câu hỏi:** Có phải là 3,000 TB (3 Petabyte) hoặc 3 TB?
   - Bổ sung hình ảnh, văn bản minh chứng cho con số này

4. **Cấu hình server hiện tại:**
   - Bổ sung hình ảnh sởffff chỉ thông tin các server trong bảng
   - CCU data: "tất cả các dữ liệu 200, 23" - không hiểu là gì
   - Cần screenshot monitoring từ hệ thống hiện tại

5. **Tải hiện tại:**
   - Bổ sung hình ảnh sởFFFF chỉ thông tin server, tải CPU/RAM/DISK
   - Cần real data, không được ước tính

#### Yêu cầu chỉnh sửa nhóm 3: Methodology

6. **Consistency issue - Module CMS:**
   - Hiện trạng có 2 modules: CMS1 và CMS2
   - Tính toán chỉ cho 1 module → giải thích tại sao?
   - Có phải đang tính per module rồi multiply?

7. **New methodology proposal:**
   ```
   Correct_Method:
   Total_Existing_Resource = Sum(CPU, RAM, DISK of all current servers)
   Scaling_Factor = New_TPS / Current_TPS
   Required_Resource = Total_Existing_Resource × Scaling_Factor × Safety_Factor
   Num_Servers = Required_Resource / Resource_Per_Server
   ```

8. **Áp dụng cho tất cả modules:**
   - Worker, PostgreSQL, Kafka đều phải làm tương tự
   - Bổ sung hình ảnh thực tế đo đạc, thực trạng hệ thống

9. **Master module:**
   - Bổ sung cấu hình, số node cho mô hình tối thiểu
   - Master thường là control plane, không thể thiếu specs

#### Yêu cầu chỉnh sửa nhóm 4: Load Balancer

10. **LB input data:**
    - Bổ sung sởFFFF chỉ: "124 yêu cầu/giây"
    - Bổ sung sởFFFF chỉ cho giả thiết:
      > "Giả thiết: Các yêu cầu đều là export dữ liệu – nghiệp vụ có dung lượng bản tin lớn nhất, và yêu cầu hồi đáp 10s, dung lượng mỗi bản tin yêu cầu (max): 7.5 MB"
    - Tại sao giả thiết như vậy? Có benchmark không?

11. **LB calculation method:**
    - Không cần nhân KPI (CPU 75%)
    - Chỉ cần nhân hệ số dự phòng = 1.2
    - **Lưu ý:** LB là network device, khác server sizing

### Phiếu nhận xét vòng 2

#### Yêu cầu chỉnh sửa bổ sung:

12. **Làm tròn giá trị:**
    - Các giá trị đề xuất và cấu hình server trong cùng module nên đồng nhất
    - Ví dụ: nếu dùng 64GB, không mixing 48GB, 96GB trong cùng module

13. **Mô hình chạy:**
    - Bổ sung thông tin mô hình sản xuất là gì
    - Active-Active? Active-Standby? Master-Slave?

14. **Review lại N+1 backup:**
    - **Trang 14 - CMS module:** N=5+1 có hợp lý?
    - **Trang 16 - Worker module:** N=? hợp lý?
    - **Trang 19 - PostgreSQL:** N=3 có đủ HA?
    - **Trang 21 - Kafka:** N=4+1 có đúng với Kafka quorum?
    - **Trang 24 - N=5+1:** Giải thích
    - **Trang 24 - N=3:** Giải thích
    - **Trang 28 - N=4+1:** Giải thích
    - **Trang 30 - N=6:** Giải thích

---

## 💡 TRI THỨC RÚT RA

### 1. Unit sanity check - QUAN TRỌNG!

**CASE STUDY - 3,000,000 TB ERROR:**

**Input:** "3,000,000 TB cho 1,080 users"

**Sanity check:**
```
TB_per_user = 3,000,000 / 1,080 = 2,777 TB/user
2,777 TB = 2.7 PB per user!
```

**Điều này vô lý vì:**
- Google data center mới có ~15-20 Exabytes total
- 3,000,000 TB = 3 EB = 15% của Google!!!
- Cho 1,080 users? KHÔNG THỂ

**Có thể là:**
- 3 TB total for system → 2.7 GB/user (reasonable)
- 3,000 TB total → 2.7 TB/user (high but possible)
- 30,000 TB → 27 TB/user (very high)

**Bài học:**
- LUÔN làm sanity check v.s input data
- Nếu con số look too good to be true → thường là SAI
- Convert per-user để dễ visualize

### 2. Methodology: System-wide scaling vs Per-module sizing

**WRONG approach (đang dùng):**
```
Size CMS1 module only
Size Worker module only
... don't consider total system capacity
```

**CORRECT approach (đề xuất):**
```
Step 1: Measure TOTAL current system capacity
  - Sum all CPU across all servers
  - Sum all RAM across all servers
  - Sum all Storage across all servers

Step 2: Calculate scaling factor
  - Scaling_Factor = New_TPS / Current_TPS

Step 3: Calculate required resource
  - Required_CPU = Total_CPU × Scaling_Factor × Safety_Factor
  - Required_RAM = Total_RAM × Scaling_Factor × Safety_Factor

Step 4: Distribute to modules
  - Based on current module distribution
  - Apply same scaling factor to each module
```

**Why this is better:**
- Accounts for shared resources (network, OS overhead)
- More realistic than sizing module individually
- Easier to justify to reviewers

### 3. Load Balancer sizing - Different methodology

**LB sizing vs Server sizing:**

**Server sizing:**
```
CPU_server = (CPU_per_request × Requests × Safety) / KPI
KPI = 75% (CPU not exceed 75%)
```

**LB sizing:**
```
Throughput_LB = Requests × Avg_Request_Size × Safety_Factor
Safety_Factor = 1.2 (no KPI division)
```

**Why no KPI for LB?**
- LB is network equipment
- Design for peak traffic, not average
- KPI applies to latency, not throughput
- Safety factor accounts for burst traffic

**CMP LB example:**
```
Input: 124 req/s
Avg size: 7.5 MB (export scenario)
Throughput = 124 × 7.5 × 8 / 1024 / 1024 = 7.1 Gbps
With safety 1.2: 7.1 × 1.2 = 8.5 Gbps
```

### 4. N+1 backup for different technologies

**N+1 varies by technology:**

**CMS/Worker (Stateless):**
- N+1 = N+1
- Any node can fail, system continues
- Example: 5+1 means 5 active, 1 standby

**PostgreSQL (Stateful, Master-Slave):**
- Minimum: 1 master + 2 replicas = 3 nodes
- N=3 gives: 1 master + 2 replicas (can survive 1 failure)
- N=5 gives: 1 master + 4 replicas (can survive 2 failures)

**Kafka (Distributed log):**
- Minimum viable cluster: 3 brokers (supports 1 failure)
- Recommended: 4+1 = 5 brokers (supports 2 failures)
- Replication factor = 3 typically
- Formula: N = Required_Partitions × Replication / Partitions_Per_Broker

**Master/Control Plane:**
- Usually 3 nodes (quorum-based)
- Raft consensus requires odd number ≥3

### 5. Greenfield vs Brownfield deployment

**Scenario cần làm rõ:**

**Scenario A: Greenfield (New system, no legacy)**
```
No existing system to migrate
Full new deployment
Sizing based on requirements only
```

**Scenario B: Brownfield (Running parallel, then cutover)**
```
New system runs alongside old system
Need DOUBLE resources during migration
Sizing = New_System + Partial_Old_System
Consider cutover strategy (big bang vs phased)
```

**CMP must clarify:**
- Which scenario?
- Migration timeline?
- Resource overlap period?

### 6. Module count consistency

**CMS example:**
- Current: CMS1 + CMS2 (2 modules)
- Sizing: Only calculate for 1 module
- **Problem:** Is sizing per module or total?

**Best practice:**
```
If sizing per module:
  - State clearly: "Sizing for ONE CMS module"
  - Mention: "Total for 2 modules = Result × 2"

If sizing for total:
  - Sum measurements from both modules
  - Calculate total capacity needed
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Modular Architecture

**Modules in CMP system:**
1. **CMS** (Content Management Service)
2. **Worker** (Background processing)
3. **PostgreSQL** (Database)
4. **Kafka** (Message queue)
5. **Master** (Control plane/Orchestrator)
6. **Other supporting modules**

### Sizing approach cần sửa
- **HIỆN TẠI:** Per-module sizing, không consistency
- **ĐỀ XUẤT:** System-wide scaling with per-module distribution

### Key metrics
- Users: 1,080 (questionable input: 3M TB data)
- Request rate: 124 req/s (for LB sizing)
- Max message size: 7.5 MB (export scenario)
- Response time: 10s (for export)

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. LUÔN sanity check input data
- 3,000,000 TB = 3 EB cho 1,080 users = IMPOSSIBLE
- Convert per-user để dễ phát hiện lỗi
- Đừng trust con số quá lớn mà không verify

### 2. Methodology quan trọng hơn calculation
- System-wide scaling > Per-module sizing
- Document methodology clearly
- Get methodology approved before calculating

### 3. LB sizing khác server sizing
- LB: Network throughput, safety factor only
- Server: CPU/RAM with KPI constraints
- Don't mix methodologies

### 4. N+1 varies by technology
- Stateless: N+1 is sufficient
- Database (Master-Slave): Usually 3+ nodes
- Kafka: Depends on partitions × replication
- Master: 3 nodes (quorum)

### 5. Clarify deployment scenario
- Greenfield vs Brownfield
- Migration strategy affects sizing
- Resource overlap during transition

### 6. Module count consistency
- State assumptions: per module or total?
- Don't assume reviewer knows your intent
- Be explicit in documentation

### 7. HÌNH ẢNH很重要
- "Hình ảnh sởffff chỉ" - screenshot is mandatory
- Don't rely on text descriptions alone
- Show actual monitoring data from current system

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** RẤT CAO  
**Số vòng PNX:** 2 (nhiều vấn đề fundamental)  
**Vấn đề chính:** Input data vô lý, methodology sai, thiếu minh chứng

**Đặc điểm hệ thống:**
- Modular architecture (CMS, Worker, DB, Kafka, Master)
- Stateful components (PostgreSQL, Kafka) + Stateless (Worker, CMS)
- Likely migration from system cũ to mới (brownfield)

**Khuyến nghị:**
- SAI LẦM NGHIÊM TRỌNG: Verify input 3,000,000 TB (likely typo)
- Change to system-wide scaling methodology
- Provide screenshots of current system monitoring
- Clarify greenfield vs brownfield deployment
- Review N+1 backup strategy per technology
- Document module count assumptions
- Provide LB sizing justification with benchmark