# APPRAISAL KNOWLEDGE - CAMPAIGN PUSH MXH

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** CAMPAIGN PHÂN HỆ TRUYỀN THÔNG MẠNG XÃ HỘI (Social Media Campaign System)  
**Mã PYC:** PYC-36759  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Giangnt109  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### 10 Yêu cầu chỉnh sửa:

**NHÓM 1: SOỞ CỨ CƠ BẢN**

1. **Bổ sung sở cứ:** Thiếu cơ sở chứng minh cho các số liệu

2. **Mục đích sizing:**
   - Cần ghi rõ lý do sizing (cấp mới, bổ sung, thay đổi kiến trúc)
   
3. **Tốc độ tăng trưởng dữ liệu:**
   - Sở cứ cho "Mức độ tăng trưởng 20%/năm" là gì?
   - Cần có=log history hoặc trend analysis

**NHÓM 2: ĐƠN VỊ TÍNH TOÁN**

4. **Chuyển đổi đơn vị CPU:**
   - Yêu cầu: Chuyển sang Cint 2017 để tính toán
   - Không dùng Cint 2006 hoặc đơn vị cũ

5. **Cấu hình server test:**
   - Cập nhật lại ảnh sở cứ cấu hình, tải của máy chủ
   - Cần hiển thị IP máy chủ để traceability

**NHÓM 3: REQUEST RATE VÀ WORKLOAD**

6. **Request rate (Trang 4):**
   - Bổ sung sở cứ: "Mỗi ứng dụng 500.000 request/giờ"
   - Bổ sung sở cứ: "Hệ thống cần cung cấp WS để nhận request kết quả từ các ứng dụng đáp ứng 1.000.000 request/giờ"
   - **Mâu thuẫn logic:** Tại sao phần tính toán CPU/RAM lại là 2.5M khi yêu cầu chỉ 1.5M request/giờ?

7. **Dữ liệu và log retention:**
   - Câu hỏi: dữ liệu, log lưu 90 ngày có nén được không?
   - Mức độ nén và tác động đến storage

**NHÓM 4: RAM VẢ VIRTUALIZATION**

8. **High RAM requirement:**
   - Cần bổ sung sở cứ từ hệ thống tương đồng
   - Cần số liệu: request tương đương với RAM đó chạy như thế nào
   - Câu hỏi: chia thành 6 server để ảo hóa được không?
   - **Vấn đề:** RAM cao quá, có thể chia nhỏ server không?

**NHÓM 5: KIẾN TRÚC VÀ MẠNG**

9. **Mô hình hệ thống:**
   - Bổ sung ảnh mô hình tổng thể
   - Bổ sung mô hình logic

10. **Network và connections:**
    - Tính thông lượng FW, LB
    - Bổ sung thông tin kết nối đến các hệ thống khác

---

## 💡 TRI THỨC RÚT RA

### 1. Mâu thuẫn trong sizing calculation

**Vấn đề:** Input vs Calculation không khớp

**CASE STUDY:**
- Yêu cầu: 1.5M request/hour (450 request/second)
- Calculation: 2.5M request/hour (694 request/second)
- **Gap:** 1M request không giải thích được

**Nguyên nhân có thể:**
- Include buffer/safety factor?
- Include internal system requests?
- Include peak traffic vs average?
- Copy-paste error from different system?

**Khuyến nghị:**
- Làm rõ input assumptions
- Giải thích gap giữa requirement và calculation
- Nếu có safety factor, ghi rõ "1.5M × 1.67 = 2.5M"

### 2. High RAM - Virtualization strategy

**Vấn đề:** RAM cao quá, liệu có cần không?

**Các giải pháp:**

**Option 1: Single large server**
- Ưu điểm: Easy to manage
- Nhược điểm: Single point of failure, harder to scale

**Option 2: Multiple smaller servers (6 servers)**
- Ưu điểm: 
  - Better failure isolation
  - Easier to scale incrementally
  - Better resource utilization
- Nhược điểm: More complex management

**Option 3: Virtualization (1 physical → 6 VMs)**
- Ưu điểm: Flexible resource allocation
- Nhược点儿: Virtualization overhead (~5-10%)

**Decision criteria:**
- Nếu workload có thể distributed → dùng multiple servers
- Nếu cần shared memory/状态 → dùng single large server
- Benchmark để xem overhead có đáng kể không

### 3. Data compression for retention

**Yêu cầu:** Lưu log 90 ngày

**Câu hỏi:** Có nén được không?

**Compression analysis:**
- **Text log (JSON, CSV):** Nén được 70-80% với gzip
- **Binary log:** Nén được 30-50%
- **Database dump:** Nén được 60-70%

**Trade-offs:**
- **Compression:** Tiết kiệm storage, tăng CPU khi compress/decompress
- **No compression:** Fast access, high storage cost

**Formula:**
```
Storage_compressed = Raw_Storage × Compression_Ratio × Retention_Days
```

**Best practice:**
- Compress old logs (>7 days)
- Keep recent logs uncompressed for fast access
- Use tiered storage: SSD (7 days) + HDD (83 days)

### 4. Growth rate justification

**Yêu cầu:** 20%/năm growth

**Làm gì để justify:**

1. **Historical data analysis:**
   - Plot growth trend from last 3-5 years
   - Calculate CAGR (Compound Annual Growth Rate)
   - Show if 20% is reasonable

2. **Business forecast:**
   - Expected new campaigns
   - User base expansion
   - New features/products

3. **Industry benchmark:**
   - Industry average growth rate
   - Competitor growth

4. **Conservative vs Aggressive:**
   - 20% relatively conservative
   - Can justify with historical trend

**Example justification:**
```
Year 2022: 10M requests/day
Year 2023: 12M requests/day (20% growth)
Year 2024: 14.5M requests/day (20.8% growth)
→ Average growth ~20%
→ Use 20% for planning
```

### 5. Request-based sizing

**Input:**
- 500.000 requests/hour per application
- 1.000.000 requests/hour for WS

**Convert to per-second:**
```
Requests_per_second = Requests_per_hour / 3600
500.000 / 3600 = 139 req/s per app
1.000.000 / 3600 = 278 req/s for WS
```

**CPU sizing:**
```
CPU_needed = (CPU_per_request × Requests_per_second × Safety_Factor) / KPI
```

**Need to know:**
- CPU per request (from testing)
- Safety factor (1.1-1.5)
- KPI target (75% CPU usage)

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Máy chủ APP:**
- High RAM configuration
- Single large server or 6 smaller servers (pending decision)
- Storage: 90 days retention with compression

**Storage:**
- Raw storage needed
- Compressed storage (if applicable)

**Network:**
- Firewall: Based on throughput calculation
- Load Balancer: Based on request rate

### Quy mô hệ thống
- Social Media Campaign system
- Multiple applications pushing campaigns
- Central WS receiving request results
- Request rate: 500K/app + 1M WS per hour
- Growth: 20%/year

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. LUÔN giải thích gap giữa input và calculation
- Input: 1.5M request
- Calc: 2.5M request
- Gap: 1M request không giải thích = SUSPICIOUS

### 2. High RAM → cân nhắc virtualization
- Single large server vs Multiple smaller servers
- Consider failure isolation, scaling flexibility
- Virtualization overhead ~5-10%

### 3. Growth rate phải có historical data
- Không được假定 20% mà không có log
- Show trend analysis from past years
- Use actual CAGR if possible

### 4. Compression strategy cho long retention
- 90 days log = consider compression
- Trade-off: storage vs CPU vs access speed
- Tiered storage: SSD (hot) + HDD (cold)

### 5. Request rate → convert to per-second
- "500K request/hour" không直观
- Convert: 139 req/s để dễ hình dung
- Helps sizing CPU, RAM,connection pool

### 6. Mô hình kiến trúc rất quan trọng
- Thẩm định viên cần thấy big picture
- Bổ sơ architecture diagram
- Show data flow, component interaction

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (nhiều vấn đề cần làm rõ)  
**Vấn đề chính:** Mâu thuẫn input vs calculation, high RAM không có justification

**Đặc điểm hệ thống:**
- Social Media Campaign system
- High request rate workload
- Long retention requirement (90 days)
- High growth rate (20%/year)

**Khuyến nghị:**
- Giải thích gap 1.5M vs 2.5M request
- Provide historical data for growth rate
- Consider virtualization for high RAM
- Add compression strategy
- Provide architecture diagrams
- Convert request/hour to request/second for clarity