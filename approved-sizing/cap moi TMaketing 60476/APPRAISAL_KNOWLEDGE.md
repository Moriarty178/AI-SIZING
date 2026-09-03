# APPRAISAL KNOWLEDGE - TENDOO MARKETING

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** TENDOO MARKETING MODULE  
**Mã PYC:** PYC-60476  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỲNG HỢP A)  
**Mục đích:** Cấp phát mới cho staging và production  
**Đầu mối:** Vudt16  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (P.CNHT)

**Yêu cầu chính:**
1. **ĐBQT requirement:** Bắt buộc phải có DR
2. **Timeline:** Cam kết hoàn thành + đổ tải thật (sởffff chỉ từ tờ trình 574/VTT-SME)
3. **Checklist:** Đính kèm file checklist
4. **CCU baseline:** 5% concurrent users → 500 CCU
5. **Storage:** KHÔNG dùng SSD, tính IOPS nếu cần tốc độ cao, OS 60GB riêng
6. **Reference system:** Ảnh sởffff chỉ phải hiển thị IP server
7. **Backup:** Lưu 3 bản, nén zstd/zip, retention 3 năm → 6 tháng

---

## 💡 TRI THỨC RÚT RA

### 1. Marketing module profile

**Tendoo Marketing characteristics:**
```
Type: Marketing automation module
Deployment: Staging + Production
Concurrent users: 5% of total users = 500 CCU
Criticality: Important (not ĐBQT)

Workload pattern:
  - Marketing campaigns (bursty traffic)
  - Email sending (I/O intensive)
  - Analytics/reporting (CPU intensive)
```

### 2. SSD vs HDD decision

**General rule:**
```
Use SSD if:
  - High IOPS required (>500)
  - Random access heavy
  - Database workloads

Use HDD if:
  - Sequential writes (logs, backups)
  - Large files, infrequent access
  - Cost-sensitive

Marketing module:
  - Likely mixed workload
  - HDD acceptable with proper IOPS calculation
```

### 3. Storage separation architecture

**Best practice:**
```
OS disk: 60GB (separate partition)
  - System files only
  - Easier to backup/restore

Data disk: Variable
  - Application data
  - Database files
  - Logs

Benefits:
  - OS corruption doesn't affect data
  - Can resize data disk independently
  - Better backup strategy
```

### 4. Backup strategy

**3-2-1 rule adapted:**
```
Keep 3 copies:
  - 1 primary (production)
  - 1 secondary (backup server)
  - 1 tertiary (offsite/archival)

Compression: zstd/zip
  - Reduces storage by 70-80%
  - Faster backup window

Retention: 6 months (reduced from 3 years)
  - Compliance with retention policy
  - Cost optimization
```

### 5. CCU calculation methodology

**5% concurrent rule:**
```
Total users: 10,000
Concurrent: 5% = 500 users

CCU needed = 500
Add safety factor: 500 × 1.2 = 600
Add N+1 redundancy: 600 × 2 = 1200 total capacity
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### Workload
- CCU: 500 (5% of total users)
- Deployment: Staging + Production
- Environment: Marketing automation

### Storage
- OS: 60GB (separate disk)
- Data: Calculate based on needs
- Backup: 3 copies, zstd/zip compressed
- Retention: 6 months

### Reference system
- Must include IP in screenshots
- Provide configuration details

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. ** Marketing has bursty traffic**
  - Campaign launches cause spikes
  - Size for peak, not average
  - Consider auto-scaling

2. **5% CCU is reasonable baseline**
  - Standard for web applications
  - May be lower for marketing (batch operations)
  - Validate with actual usage data

3. **Separate OS and data disks**
  - 60GB for OS is generous but safe
  - Data disk can grow independently
  - Better backup and recovery

4. **Calculate IOPS before choosing SSD**
  - Don't default to SSD
  - Measure actual requirements
  - HDD often sufficient for marketing workloads

5. **6-month retention for marketing**
  - Campaign data valuable for 6 months
  - Beyond that: archival or deletion
  - Reduces storage cost significantly

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (sizing improvements needed)  
**Vấn đề chính:** DR requirement, IOPS calculation, backup retention

**Đặc điểm:**
- Marketing automation module
- 500 CCU baseline (5% rule)
- Staging + Production deployment
- HDD acceptable with IOPS calculation

**Khuyến nghị:**
  - Include DR architecture (even if not ĐBQT)
  - Calculate IOPS to prove HDD sufficient
  - Use 60GB OS + separate data disk
  - Implement 3-copy backup with compression
  - Document CCU calculation methodology