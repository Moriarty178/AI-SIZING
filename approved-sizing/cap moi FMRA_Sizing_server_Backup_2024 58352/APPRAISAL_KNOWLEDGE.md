# APPRAISAL KNOWLEDGE - vFMRA BACKUP SERVER

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** vFMRA (Training Data Table Backup Server)  
**Mã PYC:** PYC-58352  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Hungbs  
**Loại hệ thống:** HỆ THỐNG ĐỊNH BỘ QUYẾT TRỌNG (ĐBQT) - BẮT BUỘC CÓ DR  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (Phòng Công nghệ Hệ thống)

#### Nhóm yêu cầu chỉnh sửa:

**NHÓM 1: COMPLIANCE VÀ DOCUMENTATION**

1. **Đánh giá mức độ quan trọng:**
   - Bổ sung đánh giá mức độ quan trọng của hệ thống
   - **QUAN TRỌNG:** Theo GL (Guideline) đính kèm → hệ thống ĐBQT bắt buộc phải có DR
   - Đây là hệ thống quan trọng, phải có DR site

2. **Cam kết thời gian:**
   - **BẮT BUỘC:** Phải có thời gian cam kết hoàn thành triển khai và đổ tải thật
   - Phải có sở cứ chỉ từ KD (Kinh doanh) hoặc BGĐ (Ban Giám Đốc)
   - Không được ước tính thời gian

3. **Checklist:**
   - Ký sizing phải đính kèm thêm file checklist
   - Checklist để đảm bảo đầy đủ các thông tin

**NHÓM 2: INPUT DATA VÀ SOỞ CỨ**

4. **Thông tin đầu vào:**
   - Bổ sung sở cứ chỉ cho: 102TB, 738TB (lấy ảnh trên hệ thống)
   - Bổ sung sở cứ chỉ thời gian lưu trữ dữ liệu (tháng) cho backup là 12
   - **Câu hỏi:** Tại sao retention 12 tháng? Có policy nào?

5. **Cấu hình và tải hiện tại:**
   - Bổ sung ảnh sở cứ chỉ cấu hình có hiển thị thông tin IP máy chủ
   - Bổ sung ảnh sở cứ chỉ tải hệ thống hiện tại
   - **QUAN TRỌNG:** Phải hiển thị IP máy chủ và số lượng 250k thuê bao với 85 đặc trưng
   - Bổ sung sở cứ chỉ cho thực tế chạy với 100 triệu thuê bao cùng 20 case
   - Bổ sung sở cứ chỉ cho: 250.000 bản ghi chiếm 250MB

**NHÓM 3: KỸ THUẬT SIZING**

6. **Storage technology:**
   - Bổ sung sở cứ chỉ sử dụng SSD
   - Bổ sung sở cứ chỉ HĐH cần 600GB

7. **Virtualization consideration:**
   - Câu hỏi: Cấu hình có thể chia nhỏ để ảo hóa được không hay bắt buộc phải dùng vật lý?
   - Consider VM vs Bare-metal trade-offs

**NHÓM 4: KIẾN TRÚC VÀ MẠNG**

8. **Mô hình nghiệp vụ:**
   - Bổ sung thêm ảnh Mô hình logic nghiệp vụ
   - Show data flow and component interaction

9. **Kết nối hệ thống:**
   - Bổ sung thông tin kết nối đến các hệ thống khác
   - Thiếu network connectivity diagram

10. **Network bandwidth:**
    - Làm rõ, bổ sung sở cứ chỉ rõ ràng cho: "Đề xuất băng thông 2.5 Gbps trên mỗi server"
    - Tại sao là 2.5 Gbps? Có measurement không?

**NHÓM 5: ADMINISTRATIVE**

11. **Đơn vị tên:**
    - Sửa lại tên đơn vị đang bị sai ở chân ký
    - Wrong entity name → fix before submission

---

## 💡 TRI THỨC RÚT RA

### 1. ĐBQT (Decision Support) Systems - DR is MANDATORY

**Viettel Policy:**
```
Classification: ĐBQT (Hệ thống Định Bộ Quyết Trọng)
Mức độ: CRITICAL
Requirement: BẮT BUỘC CÓ DR (Disaster Recovery)
```

**What is ĐBQT?**
- Hệ thống hỗ trợ ra quyết định tại cấp lãnh đạo
- Ảnh hưởng trực tiếp đến business operation
- Không thể downtime quá lâu

**DR Requirements:**
```
Primary Site: Production environment
DR Site: Backup site in different location
RPO (Recovery Point Objective): < 15 minutes (data loss tolerance)
RTO (Recovery Time Objective): < 4 hours (downtime tolerance)
```

**Impact on sizing:**
```
Total_Resources = Primary_Site + DR_Site
DR_Site ≥ Primary_Site (usually same capacity)
→ Double the resources compared to non-ĐBQT systems
```

### 2. Timeline commitment from KD/BGĐ

**Why important:**

**Problem:**
```
Technical estimate: "3 months to deploy"
Question: Is this aligned with business expectations?
```

**Solution:**
```
Must have formal commitment from:
- KD (Kinh doanh/Business): When is it needed for operations?
- BGĐ (Ban Giám Đốc/Executive Board): Strategic timeline

Example:
Business deadline: 30/06/2025 (from KD)
Technical estimate: 90 days → Complete by 25/06/2025
Buffer: 5 days for testing → ✅ Aligned
```

**Document must include:**
```
1. Business requirement date (from KD)
2. Technical deployment estimate
3. Buffer for testing/UAT
4. Final commitment date
5. Signature approval from KD/BGĐ
```

### 3. Large data volumes - 102TB và 738TB

**Understanding the numbers:**

**102TB:**
- Likely: Current production data size
- Or: Baseline for one type of data

**738TB:**
- Likely: Total storage needed with retention
- Or: Sum of multiple data sources

**Validation questions:**
1. What's the relationship between 102TB and 738TB?
   - 738TB / 102TB = 7.23x
   - Is this retention-based? (7 months retention?)
   - Or multiple backups?

2. Growth rate?
   - How much data added daily/monthly?
   - Projections for next 12-24 months?

3. Compression/deduplication?
   - Can we reduce these numbers?
   - Data compression ratio?
   - Deduplication savings?

**Best practice:**
```
Explain clearly:
- 102TB: Live production data (as of [date])
- 738TB: Total including:
  * Retention copies: 102TB × [months]
  * Backup history: [amount]
  * Archive data: [amount]
  * Buffer for growth: [amount]
```

### 4. Training data characteristics

**vFMRA training data specifics:**

```
Current dataset:
  - Subscribers: 250,000
  - Characteristics (features): 85 per subscriber
  - Records: 250,000
  - Size: 250 MB

Calculation:
  - Record size = 250 MB / 250,000 = 1 KB/record
  - Features per record = 85
  - Feature size = 1,000 bytes / 85 ≈ 12 bytes/feature

Test dataset:
  - Subscribers: 100,000,000
  - Test cases: 20
  - Extrapolated size = (100M / 250K) × 250 MB = 100 GB per test case
  - Total for 20 cases = 100 GB × 20 = 2 TB
```

**Scaling considerations:**
- Training data can be very large (100M subscribers)
- Need fast I/O for training iterations
- May need to load multiple times during training
- **Storage impact:** Need high throughput, not just capacity

### 5. SSD justification for backup servers

**Typical assumption:** Backup servers use HDD (cheaper, slower)

**vFMRA case:** Why SSD?

**Possible reasons:**

**Reason 1: Fast restore required**
- DR restoration must be quick
- HDD slow for large data restore (102TB+)
- SSD significant faster (10x-100x)

**Reason 2: Training workload needs fast I/O**
- Not just backup, but also training support
- Training algorithms need fast random access
- SLA for training completion time

**Reason 3: RTO requirement**
- If RTO < 4 hours (DR requirement)
- HDD restore of 102TB might take > 4 hours
- SSD needed to meet RTO

**Justification template:**
```
SSD Requirement:
1. RTO: < 4 hours (ĐBQT requirement)
2. Restore speed:
   - HDD @ 100 MB/s: 102TB / 100 MB/s = 293 hours ❌
   - SSD @ 500 MB/s: 102TB / 500 MB/s = 58 hours ❌
   - Need parallel restore: 10 drives @ 500 MB/s = 5.8 hours ✅
3. Training workload: Fast random access needed
4. IOPS requirement: [specific number] > HDD can provide
→ SSD is REQUIRED, not optional
```

### 6. OS allocation - 600GB

**Why 600GB for OS?**

**Typical OS allocation:**
- Standard Linux: 50-100 GB
- With logs: 200-300 GB
- **600GB is VERY large**

**Possible reasons:**

**Reason 1: System logs are large**
- Training produces massive logs
- Debug logs during training
- Application logs

**Reason 2: Temporary space**
- ETL (Extract-Transform-Load) operations
- Data staging before loading to DB
- Sort/hash operations

**Reason 3: OS + Application + Tools**
- Not just OS, but:
  - Database software
  - Training framework (TensorFlow, PyTorch?)
  - Data processing tools
  - Cache/tmp space

**Justification needed:**
```
OS Partition (600GB):
- Base OS: 100 GB
- Application software: 100 GB
- System logs (30 days): 150 GB
- Temp/ETL space: 200 GB
- Buffer: 50 GB
Total: 600 GB
```

### 7. Network bandwidth - 2.5 Gbps per server

**Why 2.5 Gbps?**

**Validation:**

**Scenario A: Backup/Restore traffic**
```
Data to restore: 102 TB
RTO: 4 hours = 14,400 seconds
Required bandwidth: 102 TB / 14,400 s = 7.4 GB/s
= 59.2 Gbps
→ Single 2.5 Gbps is NOT enough for restore! ❌

Solution: Parallel restore across multiple servers
Total bandwidth: 2.5 Gbps × N_servers
N_servers = 59.2 / 2.5 = 24 servers minimum
```

**Scenario B: Ongoing replication**
```
Daily change rate: 100 GB (assume)
Replication window: 8 hours = 28,800 s
Required bandwidth: 100 GB / 28,800 = 3.5 MB/s
= 0.028 Gbps
→ 2.5 Gbps is PLENTY ✅
```

**Scenario C: Training data loading**
```
Training dataset: 100 GB
Load time target: 10 minutes = 600 s
Required bandwidth: 100 GB / 600 = 0.17 GB/s
= 1.36 Gbps
→ 2.5 Gbps is adequate ✅
```

**Document must specify:**
```
Bandwidth Requirement: 2.5 Gbps per server

Justification:
1. Ongoing replication: [calculation]
2. Training data loading: [calculation]
3. Backup/restore: [calculation with parallelization]

Note: For full restore of 102TB under 4 hour RTO,
      need N servers configured in parallel
```

### 8. Checklist attachment - Mandatory

**Purpose of checklist:**

Ensure ALL required information is present:
```
□ System classification (ĐBQT)
□ Criticality assessment
□ DR requirement confirmed
□ Timeline commitment from KD/BGĐ
□ Input data with screenshots showing IPs
□ Current load measurements (250k subs, 85 chars)
□ Test data validation (100M subs, 20 cases)
□ Storage breakdown (102TB, 738TB)
□ Retention policy justification (12 months)
□ SSD vs HDD justification with IOPS calculation
□ Network bandwidth calculation (2.5 Gbps)
□ DR sizing (N+1, primary + DR sites)
□ Implementation timeline with milestones
□ Risk assessment and mitigation
□ Signatures from all stakeholders
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Backup Servers:**
- Storage: SSD (justification required for IOPS/RTO)
- OS allocation: 600GB (needs breakdown)
- Network: 2.5 Gbps per server
- **DR requirement:** Double capacity (Primary + DR sites)

### Quy mô hệ thống
- Production data: 250,000 subscribers
- Features per subscriber: 85 characteristics
- Record size: ~1 KB/record
- Total data: 102 TB (production), 738 TB (with retention)
- Test data: 100,000,000 subscribers with 20 test cases

### Criticality
- **Classification:** ĐBQT (Decision Support System)
- **DR requirement:** MANDATORY
- **RTO/RPO:** Must be defined

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. ĐBQT = DR is MANDATORY
- Decision support systems cannot have extended downtime
- Must double resources (Primary + DR)
- RTO/RPO must be strictly defined

### 2. Timeline needs business approval
- Technical estimate alone is insufficient
- Must have commitment from KD/BGĐ
- Align business needs with technical capability

### 3. Large volumes need breakdown explanation
- 102TB vs 738TB - what's the relationship?
- Retention policy, backup history, growth rate?
- Don't just show numbers, explain the math

### 4. Training data has IOPS requirements
- Not just backup, also training support
- Random access patterns during training
- May justify SSD over HDD

### 5. Network bandwidth must align with RTO
- Calculate restore time with current bandwidth
- If insufficient, specify parallel restore strategy
- Show the math in sizing document

### 6. OS allocation needs justification
- 600GB is large for OS alone
- Break down: OS + Apps + Logs + Temp + Buffer
- Show each component's allocation

### 7. Checklist is not optional
- Ensures completeness of sizing document
- Catch common omissions early
- Must be attached to signed sizing

### 8. Show IP addresses in ALL screenshots
- Makes data traceable
- Allows verification
- Standard requirement for audit

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 1 (nhiều compliance requirements)  
**Vấn đề chính:** ĐBQT system requiring DR, large data volumes, timeline commitment

**Đặc điểm hệ thống:**
- vFMRA: Training data backup server
- Classification: ĐBQT (Critical decision support)
- Large scale: 250k → 100M subscribers
- High storage: 102TB production, 738TB total
- DR requirement doubles all resources

**Khuyến nghị:**
- Confirm DR site sizing (double resources)
- Get formal timeline commitment from KD/BGĐ
- Breakdown 102TB vs 738TB relationship
- Justify SSD with IOPS calculation and RTO
- Explain 600GB OS allocation breakdown
- Validate 2.5 Gbps for restore scenario
- Include complete checklist
- Attach all supporting documentation
- Define RTO/RPO for DR scenario
- Specify parallel restore strategy if needed