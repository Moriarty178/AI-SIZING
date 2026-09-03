# APPRAISAL KNOWLEDGE - VIETTEL APP V1.0

## 📋 THÔNG TIN HỆ THỤNG

**Dự án:** HỆ THỐNG VIETTEL APP V1.0  
**Mã PYC:** PYC-53803  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Xây mới  
**Đầu mối:** Minhca  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23

**Yêu cầu chính:**
1. **HSDP only:** Chỉ nhân HSDP = 1.2 (không nhân KPI)
2. **Notation:** LB cứng = 94 Mbps (bỏ dấu `>`)
3. **Network card:** Làm rõ nội dung sử dụng 10Gbps
4. **SSD:** Bổ sung sởffff chỉ
5. **Input data:** Bổ sung đầy đủ sởffff chỉ bằng văn bản + hình ảnh xác thực
6. **Storage time:** Bổ sung sởffff chỉ thời gian lưu trữ
7. **LB calculation:** Tính toán chính xác, không có "khoảng"
8. **DB unit issue:** 1 event = 1KB, tại sao tính ra KB/s?

---

## 💡 TRI THỨC RÚT RA

### 1. Load balancer sizing - HSDP only

**Important distinction:**
```
WRONG: LB_throughput = Average × HSDP / KPI
RIGHT: LB_throughput = Average × HSDP (HSDP = 1.2 only)

Reason:
  - Network equipment ≠ server application
  - No CPU usage threshold (KPI)
  - Only safety margin needed

Example:
  - Average throughput: 100 Mbps
  - HSDP = 1.2
  - Required: 120 Mbps
```

### 2. Network card justification

**10Gbps card requirement:**
```
When is 10Gbps needed?
  - Measured throughput >1Gbps
  - Expected growth >4x current
  - High-frequency trading/real-time
  - Multiple services share same NIC

Viettel App v1.0:
  - Must justify 10Gbps usage
  - Document actual/expected traffic
  - Consider link aggregation instead
```

### 3. Database event sizing unit error

**The issue:**
```
Claim: 1 event = 1 KB
Calculation: Result in KB/s ❌

Problem:
  - Event is count (not data rate)
  - KB/s is data rate (not count)
  - Dimension mismatch!

Correct approach:
  Events/sec × Size/event = KB/s
  
  Example:
  - 100 events/sec × 1 KB/event = 100 KB/s ✓
```

### 4. Precise LB calculations

**No more "khoảng" (ranges):**
```
BAD: Throughput: khoảng 100-200 Mbps
GOOD: Throughput = 150 Mbps

Requirements:
  - Exact input numbers
  - Exact calculations
  - Document every parameter
```

### 5. Evidence documentation

**Text + images:**
```
For every sizing input:
  - Text description of source
  - Screenshot/document as proof
  - Link to reference if applicable

Example:
  - "商用 forecast: 10K users"
  - Screenshot of business projection
  - Email from product team
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System type
- Mobile application backend
- New build (v1.0)

### Key issues
- LB sizing methodology (HSDP only)
- 10Gbps NIC justification
- DB unit consistency
- Precise calculations required

### Storage
- SSD justification needed
- Retention period justification

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **HSDP ≠ KPI for network equipment**
  - Use HSDP = 1.2 only
  - Don't divide by KPI (75%)
  - Network and server sizing differ

2. **Unit consistency is critical**
  - Don't mix events/sec with KB/s
  - Ensure dimensional analysis
  - Event rate × Size = Data rate

3. **Precise numbers, not ranges**
  - "Khoảng" suggests uncertainty
  - Calculate exact values
  - Document assumptions

4. **Network tier must be justified**
  - 10Gbps needs strong business case
  - Consider cost vs benefit
  - Link aggregation as alternative

5. **Evidence in multiple formats**
  - Text description
  - Screenshot proof
  - Reference links
  - Make it auditable

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (calculation/methodology issues)  
**Vấn đề chính:** HSDP vs KPI, unit consistency, precise calculations

**Đặc điểm:**
- Mobile application backend
- Load balancer critical component
- Database event processing
- Network-intensive workload