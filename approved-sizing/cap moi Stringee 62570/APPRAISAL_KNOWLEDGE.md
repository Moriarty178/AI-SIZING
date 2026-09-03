# APPRAISAL KNOWLEDGE - STRINGEE VIDEO CALL

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** STRINGEE VIDEO CALL - MỞ RỘNG HỆ THỐNG  
**Mã PYC:** PYC-62570  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Sizing mở rộng hệ thống video call  
**Đầu mối:** Thangpq19  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (P.CNHT)

**Yêu cầu chính:**
1. **Mức độ quan trọng:** Hệ thống ĐBQT bắt buộc phải có DR
2. **Timeline:** Bắt buộc cam kết hoàn thành triển khai và đổ tải thật
3. **Checklist:** Ký sizing phải đính kèm file checklist
4. **Load inconsistency:** Tính thì 70, đầu vào thì 80, sởffff chỉ thì 100
5. **Resource gap:** Tính lại CPU/RAM khi lập bảng giá trị (cần trừ số đã có)

---

## 💡 TRI THỨC RÚT RA

### 1. ĐBQT system = DR mandatory

**Critical system requirement:**
```
ĐBQT (Đảng bộ Quân ư) systems:
  - MUST have DR (Disaster Recovery)
  - Active + DR configuration
  - Double all resources

Stringee for ĐBQT:
  - Video call for critical communications
  - Cannot afford downtime
  - Full duplication required
```

### 2. Load inconsistency is common issue

**Problem:**
```
Three different load numbers in same document:
  - Calculation uses: 70 concurrent calls
  - Input specification: 80 concurrent calls
  - Reference/justification: 100 concurrent calls

Which one is correct?
```

**Solution:**
```
1. Pick ONE source of truth
2. Document the decision
3. Use consistent value throughout
4. Explain if different numbers represent scenarios
```

### 3. Resource gap calculation

**Expansion sizing:**
```
Current system: Has some resources already
New sizing: Total resources needed

WRONG: Request total (ignores existing)
RIGHT: Delta = Total - Existing

Example:
  Total needed: 8 CPU, 32GB RAM
  Current: 4 CPU, 16GB RAM
  Request: 4 CPU, 16GB RAM (not 8/32!)
```

### 4. Video call system architecture

**Stringee video call components:**
```
Media servers:
  - Handle video/audio streaming
  - High CPU for encoding/decoding
  - GPU recommended for video processing

Signaling servers:
  - Session management
  - Lower resource requirements
  - Can scale horizontally

TURN/STUN servers:
  - NAT traversal
  - Network intensive
  - Bandwidth critical
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System profile
- Type: Video conferencing expansion
- Criticality: ĐBQT (requires DR)
- Current load: 70-100 concurrent calls (inconsistent)

### Requirements
- DR mandatory (Active + DR)
- Deployment timeline with commitment
- Checklist attachment required

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **ĐBQT = double resources**
   - DR not optional
   - Active site + DR site
   - Full duplication required

2. **Load numbers must be consistent**
   - Pick one source of truth
   - Use same value throughout document
   - Document the basis for the number

3. **Expansion = delta not total**
   - Calculate: New - Existing = Request
   - Don't request full amount if already have partial
   - Clearly show current vs proposed

4. **Video call needs GPU consideration**
   - Encoding/decoding is CPU-intensive
   - GPU offloading recommended
   - Bandwidth more important than storage

5. **Timeline commitment required**
   - Cannot leave deployment open-ended
   - Must specify: design, deploy, test milestones
   - Support actual load testing before acceptance

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (expansion with inconsistencies)  
**Vấn đề chính:** Load inconsistency, DR requirement, resource gap calculation

**Đặc điểm:**
- Video call system expansion
- ĐBQT critical system (DR mandatory)
- Load data inconsistent across document

**Khuyến nghị:**
- Resolve load number inconsistency upfront
- Calculate delta (total - existing) correctly
- Include comprehensive DR architecture
- Attach checklist as required
- Provide deployment timeline with commitments