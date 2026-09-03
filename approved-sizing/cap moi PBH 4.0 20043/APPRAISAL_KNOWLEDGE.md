# APPRAISAL KNOWLEDGE - PHÍ BÁN HÀNG 4.0 (ỨNG CỨU)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG PHÍ BÁN HÀNG 4.0 - ỨNG CỨU  
**Mã PYC:** PYC-20043 (Sao với PBH 21050)  
**Mục đích:** ỨNG CỨU tài nguyên cho hệ thống PBH  
**Đầu mối:** thanhdv125  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23

**Điểm chính:**
1. **Emergency sizing:** "Nếu ứng cứu thì xử lý theo luồng UCTT của VTNet"
2. **Sizing scope:** Database separated from app cluster
3. **Inconsistency:** RAM 80GB in config, 125GB in screenshot
4. **Network:** 10Gbps per node cần justification
5. **CPU values:** 109.375 vs 175 vs 103.975 - không rõ

---

## 💡 TRI THỨC RÚT RA

### 1. Emergency sizing workflow - VTNet UCTT

**Emergency capacity request:**
```
Standard flow:
  1. Submit emergency request to VTNet
  2. VTNet reviews availability
  3. Allocate from resource pool
  4. Deploy to production

Sizing should be:
  - Based on immediate need (not 1-year projection)
  - Use VM/template for fast deployment
  - Document resource pool source
```

### 2. RAM inconsistency traceability

**Problem:**
```
Config documents: 80GB RAM
Screenshot measurement: 125GB RAM usage
```

**Root cause analysis:**
- Config shows allocated resource
- Screenshot shows actual usage
- Or: Different measurement times
- **Must clarify which is reference base**

### 3. Separated concern - Sizing scope

**Important clarification:**
```
PBH sizing covers:
  - Application cluster (K8S)
  - Storage (S3)
  - Network components

NOT included:
  - Database sizing (separate sizing document)
  - Database backup (separate)
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### Emergency allocation
- Purpose: Ứng cứu (not new deployment)
- Data volume: 2.9TB/month, 2.9 billion records
- 50% raw data

### Resource requirements
- Network: 10Gbps per node (needs justification)
- RAM: Config 80GB, Actual 125GB (inconsistent)
- CPU: Multiple Cint values (conflicting)

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Follow emergency sizing流程**
   - Use VTNet UCTT standard workflow
   - Fast deployment templates over custom sizing

2. **Config vs actual inconsistency**
   - Document which is source of truth
   - Allocated (80GB) vs Used (125GB)

3. **Separated sizing concerns**
   - App cluster: This document
   - Database: Separate sizing
   - Clear scope boundaries

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (emergency allocation)  
**Vấn đề chính:** Emergency workflow, config inconsistency

**Lưu ý:** Cùng PYC-20043 với "cap moi PBH 21050" - có thể là các version khác nhau của cùng hệ thống

**Đặc điểm:**
- Emergency resource allocation
- Not new deployment
- Must follow VTNet UCTT流程