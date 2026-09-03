# APPRAISAL KNOWLEDGE - VIETTEL REPORT 2026

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** VIETTEL REPORT 2026  
**Mã PYC:** PYC-62005  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Cấp phát mới VIETTEL REPORT  
**Đầu mối:** Haidm6  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (P.CNHT)

**Yêu cầu chính:**
1. **ĐBQT = DR mandatory:** Bắt buộc phải có DR
2. **Timeline:** Cam kết hoàn thành + đổ tải thật
3. **Input data:** 500, 500, 100, 2 năm → cần bổ sung sởffff chỉ
4. **Reference:** Cấu hình hệ thống tham chiếu + tải
5. **Storage policy:** 2.39 GB/ngày × 365 ngày × N nodes
6. **Bỏ SSD/DDR4:** Tính IOPS cụ thể, bỏ DDR4
7. **Partition:** /data /log /backup
8. **Backup:** Lưu mấy bản? Nén như nào?
9. **LB details:** concurrent, peak, new, duration, bandwidth

---

## 💡 TRI THỨC RÚT RA

### 1. Report system characteristics

**Viettel Report profile:**
```
Type: Business intelligence/reporting
Workload:
  - Batch processing (scheduled reports)
  - Ad-hoc queries (user-initiated)
  - Data aggregation/analysis
  
Storage-heavy:
  - 2.39 GB log data per day per node
  - 365 days retention
  - Needs systematic partitioning
```

### 2. Storage partitioning strategy

**Best practice partitions:**
```
/data (Reports, databases):
  - Primary storage
  - Largest allocation
  - May need SSD for performance

/log (Application logs):
  - Sequential writes
  - Rotate frequently
  - HDD acceptable

/backup (Backup dumps):
  - Sequential writes
  - Compressed storage
  - HDD acceptable
  - May use separate storage tier
```

### 3. Log retention calculation

**Storage projection:**
```
Per node:
  - 2.39 GB/day × 365 days = 872 GB/year
  - With N nodes: 872 GB × N

Consider:
  - Compression: ~70% reduction = 262 GB/year
  - Growth: Add 20% buffer = 315 GB/year per node

HDD acceptable because:
  - Logs are sequential writes
  - Compression reduces I/O load
  - Not performance-critical
```

### 4. Backup policy considerations

**Common strategies:**
```
Number of copies:
  - 3 copies is standard (primary + 2 backups)
  - Or rotation: Daily-Weekly-Monthly

Compression:
  - zstd: Best compression (3:1), slower
  - zip: Good compression (2:1), faster
  - gzip: OK compression (2.5:1), compatible
```

### 5. IOPS calculation methodology

**When to calculate:**
```
Report system IOPS sources:
  - Database queries (random)
  - Log writes (sequential)
  - Report generation (mixed)

Calculate:
  - Read IOPS: Query load
  - Write IOPS: Log rotation rate
  - Mixed: Aggregate both
  
Result determines:
  - HDD sufficient if IOPS < 1000
  - SSD needed if IOPS > 1000
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System type
- Business intelligence/reporting
- New deployment

### Storage
- Log data: 2.39 GB/day/node
- Retention: 365 days
- Partitions: /data /log /backup

### Requirements
- DR mandatory (ĐBQT)
- Calculate IOPS (no SSD default)
- Detailed LB metrics
- N+1 redundancy

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Report systems are storage-heavy**
  - Log retention policy critical
  - Compression saves 70% space
  - H2226 acceptable for logs

2. **Partition separation is essential**
  - /data for active data
  - /log for application logs
  - /backup for backup dumps
  - Each has different characteristics

3. **365 days retention is significant**
  - Requires large storage allocation
  - Consider tiered storage (hot/warm/cold)
  - Archive old data to cheaper storage

4. **Calculate IOPS before choosing SSD**
  - Report workload often sequential
  - HDD may be sufficient
  - Don't default to SSD without measurement

5. **Business forecast validation**
  - Numbers like 500, 500, 100 need context
  - What do they represent?
  - Document assumptions clearly

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Số vòng PNX:** 1 (reporting system sizing)  
**Vấn đề chính:** Retention policy, partitioning, IOPS calculation

**Đặc điểm:**
- Business intelligence/reporting
- High log data volume (2.39 GB/day)
- 365-day retention
- Storage-intensive workload