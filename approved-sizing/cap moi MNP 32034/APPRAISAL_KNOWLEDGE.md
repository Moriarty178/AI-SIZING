# APPRAISAL KNOWLEDGE - MNP (MOBILE NUMBER PORTABILITY)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG MNP (Mobile Number Portability)  
**Mã PYC:** PYC-32034  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** tiendc  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### Nhóm yêu cầu:

1. **KPI calculation error:**
   - "Kpi dự phòng để tính toán đang bị sai"
   - Common mistake: Using KPI incorrectly in formula

2. **Sizing purpose:** Bổ sung mục đích sizing

3. **Input data justification:**
   - Bổ sung sởffff chỉ cho tất cả số liệu input (trang 2, 3)
   - 100.000, 600.000 subscriber, tx records

4. **Network connections:** Bổ sung thông tin kết nối

5. **FW/LB sizing:**
   - Tính toán lại thông lượng FW, LB kèm sởffff chỉ

6. **CPU unit conversion:**
   - Cint quy đổi về 2017 để tính toán

7. **APP server baseline:**
   - Cấu hình các máy chủ ứng dụng thực hiện đo tải
   - Kết quả đo tải

8. **Storage sizing (trang 56):**
   - RAM: 236 GB, TPS: 500, Cint: 990
   - Growth rate: 20%/năm
   - Data: 100K, 600K subscribers, 6 tables

9. **Detailed transaction analysis (trang 57):**
   - 700.000 transactions, 5.47 KB/xml, 7 tables

10. **XML message size (trang 59):**
    - File khoảng 5KB chưa đính kèm
    - Need actual file proof

11. **Transaction structure (trang 60):**
    - 3 files/yêu cầu, mỗi file 2 MB = 6MB
    - Tối đa 6MB file transfer
    - Hậu kiểm: tối đa 3MB
    - Yêu cầu tổng: 9MB

12. **Retention:** Giữ lại 2 tháng

---

## 💡 TRI THỨC RÚT RA

### 1. KPI calculation - Correct method

**Common error:** Multiplying instead of dividing

**WRONG:**
```
Required_CPU = Calculated_Needs × KPI ❌
```

**CORRECT:**
```
Required_CPU = Calculated_Needs / KPI

Where KPI = Maximum acceptable usage
- CPU KPI = 0.75 (75% max)
- RAM KPI = 0.90 (90% max)
-Disk KPI = 0.80 (80% max)
```

**Example MNP:**
```
CPU needed for workload: 742.5 Cint
Allow 75% usage:
Total_CPU = 742.5 / 0.75 = 990 Cint ✓
```

### 2. Growth rate projection - 20%/year

**MNP data:**
- Current: 100,000 subscribers
- Projection: 600,000 subscribers
- Growth assumption: 20%/year

**Validation:**
```
Year 0: 100K
Year 1: 100K × 1.2 = 120K
Year 2: 120K × 1.2 = 144K
Year 3: 144K × 1.2 = 172.8K
Year 4: 172.8K × 1.1.2 = 207.4K
Year 5: 207.4K × 1.2 = 248.9K
→ To reach 600K: Need more years or higher growth rate

Justification needed:
- Is 600K a 5-year target?
- What's the business driver?
- Industry growth: Port adoption rate?
```

### 3. XML message structure analysis

**Transaction breakup:**
```
Single portability request:
- 3 XML files
- Each file: 2 MB
- Total: 6 MB request data

With attachments:
- Customer data from home network: transferred via
- Received file: up to 6 MB
- Total with attachments: 6 + 6 = 12 MB

Post-processing:
- Verification files: up to 3 MB
- Final message size: 9 MB
```

**Sizing impact:**
```
Average transaction: 5 KB XML (700K transactions)
Peak transaction: 9 MB (max with files)

Storage per transaction:
- DB size: 6 + 7 = 13 tables
- Index overhead: ~2x raw data
```

### 4. MNP-specific retention: 2 months

**Why 2 months?**

**Factors:**
- **Regulatory:** Telecom law requirement?
- **Operational:** Transaction dispute window?
- **Audit:** Compliance verification period?

**Recommendation:**
```
MNP transactions are:
- Time-sensitive: Port must complete within X days
- Legally binding: After 2 months, transaction final
- Audit trail: Keep for compliance verification

If no regulation → 30-60 days typical
If regulatory requirement → Follow law exactly
```

**Storage with retention:**
```
Daily transactions: 700.000
Per transaction: 5 KB
Daily storage: 700K × 5 KB = 3.5 GB/day

60-day retention: 3.5 GB × 60 = 210 GB
With compression (70%): 210 × 0.3 = 63 GB
With growth (20%): Average 400K → 4.2 GB/day × 60 = 252 GB
```

### 5. Network signaling vs data

**MNP protocol traffic:**

**Signaling:**
- Initial port request
- verification messages
- Confirmation messages

**Data transfer:**
- Customer profile data (6 MB)
- Transaction files (up to 6 MB)
- Verification files (up to 3 MB)

**Sizing consideration:**
```
Network throughput must handle:
1. Signaling overhead (low bandwidth)
2. Peak data transfer (high bandwidth)
3. Concurrent transactions

Peak scenario:
- 100 concurrent ports
- Each with 9 MB data
- Total: 900 MB transfer
- Within SLA time window

Bandwidth = Peak data / SLA_time
```

### 6. Database table count: 6 tables

**Why 6 tables?**

**Likely MNP data model:**
```
Table 1: Port request master
Table 2: Subscriber data
Table 3: Operator data
Table 4: Transaction log
Table 5: Verification status
Table 6: Final confirmation

Or by operator (6 mobile operators in Vietnam):
- Each operator: 1 table for routing data
```

**Impact:**
```
More tables = More indexes
→ Higher RAM for DB cache
→ More storage for indexes
→ Slower queries if not optimized

Recommendation:
- Keep indexes vital for query performance
- Archive old data to separate tables
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Configuration (based on PNX feedback)

**APP Servers:**
- Current: Cint 990, RAM 236 GB, TPS 500
- Must verify with screenshots

**Storage:**
- Daily: 3.5 GB (700K × 5 KB)
- Retention: 2 months
- Growth: 20%/year

**Peak transaction:**
- Data transfer: 9 MB
- Throughput: Based on SLA requirements

### Network
- Calculate FW/LB based on actual throughput
- Include signaling + data transfer

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. KPI is for division, not multiplication
- Required = Calculated / KPI
- Example: 742.5 / 0.75 = 990 Cint

### 2. Growth rate must be justified
- 20%/year needs business validation
- Historical data or industry benchmark?

### 3. XML file size needs actual proof
- Don't estimate "khoảng 5KB"
- Include actual file sample

### 4. Transaction structure affects sizing
- 3 files × 2 MB = 6 MB base
- Plus attachments up to 6 MB
- Total up to 9 MB peak

### 5. Retention policy requires justification
- 2 months: Regulatory or operational?
- Document the requirement source

### 6. Network sizing must consider peaks
- Not average only
- Include file transfer scenarios
- 100 concurrent ports × 9 MB each

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (nhiều yêu cầu chi tiết)  
**Vấn đề chính:** KPI calculation error, growth rate justification, XML size verification

**Đặc điểm hệ thống:**
- MNP (Port Mobile Number)
- High transaction volume: 700K/day
- Complex transaction structure (multi-file)
- 2-month retention requirement

**Khuyến nghị:**
- Fix KPI calculation (divide, not multiply)
- Justify 20% growth with business data
- Provide actual XML file samples
- Clarify retention policy source
- Calculate network for peak file transfer
- Verify 6-table database structure
- Include baseline load screenshots