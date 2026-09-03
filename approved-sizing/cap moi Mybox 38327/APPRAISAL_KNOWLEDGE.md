# APPRAISAL KNOWLEDGE - MYBOX FILE STORAGE SYSTEM

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** MYBOX (File Storage & Sharing System)  
**Mã PYC:** PYC-38327  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Hungnh46  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23

1. **Input data inconsistency:**
   - Claim: "Gần 1 triệu file trong 1 ngày"
   - But: Sizing theo 500K users
   - **Vấn đề:** Mâu thuẫn giữa file count và user base

2. **CCU calculation error:**
   - Must include server boot time in measurement
   - Formula: Tải sử dụng = Tải hiện tại - Tải khởi tạo
   - CCU tính theo tải sử dụng only

3. **ELK Stack sizing:**
   - Cần cấu hình app servers tham chiếu
   - Ảnh tải bị mờ, chưa có IP

4. **SSD justification:** Bổ sung sởffff chỉ

5. **Notation:** Replace >= with = (đáng chính xác)

6. **Current production data:**
   - 27,776 users upload 50,000 files/day
   - 700K images, 250K docs, 50K video/zip
   - Database: 4,449 records (142.14 MB), 6,427 records (81.93 MB)
   - Storage: 120 GB/year

---

## 💡 TRI THỨC RÚT RA

### 1. File storage capacity planning

**Mybox workload:**
```
Current: 27,776 users → 50,000 files/day
Future target: 500,000 users

Scaling factor: 500K / 27.7K = 18x

Projected daily files:
  50,000 × 18 = 900,000 files/day ≈ 1M files/day ✓

File type breakdown (per day):
- Images: 700K × 18 = 12.6M images
- Docs: 250K × 18 = 4.5M documents
- Video/Zip: 50K × 18 = 900K large files
```

### 2. CCU calculation - Include boot time

**Correct approach:**
```
Wrong: CPU_total = CPU_usage_per_user × CCU
Right: Real_Usage = Total_CPU - Boot_CPU
       CCU = Real_Usage / Usage_per_user

Example:
- Total CPU: 75% (including boot OS + apps)
- Boot CPU: 15% (OS + background services)
- Real usage: 75% - 15% = 60% available
- Per user CPU: 0.1%
- CCU = 60 / 0.1 = 600 CCU (not 750!)
```

### 3. ELK Stack sizing considerations

**Elasticsearch components:**
```
Elasticsearch nodes:
- Master nodes: 3 minimum (quorum)
- Data nodes: Based on storage
- Ingest nodes: Based on indexing rate

Key metrics for Mybox:
- Daily files: ~1M
- Metadata indexing: 1M docs/day
- Search query rate: Unknown (need measurement)
```

### 4. SSD vs HDD for ELK

**Decision factors:**
```
ELK writes: Sequential indices (OK for HDD)
ELK reads: Random queries (Needs SSD)

Recommendation:
- Hot data (7-30 days): SSD for fast search
- Warm data (30-90 days): HDD acceptable
- Cold data (90+ days): HDD or archive

Hybrid approach cost-effective while maintaining performance
```

### 5. Storage projection

**Mybox storage growth:**
```
Current: 120 GB/year for 27,776 users
Per user/year: 120GB / 27,776 = 4.32 MB/user/year

For 500,000 users:
  4.32 MB × 500,000 = 2,160 GB/year
  With growth buffer (30%): 2,808 GB/year

3-year projection: 2,808 × 3 = 8,424 GB
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Current Production
- Users: 27,776
- Files/day: 50,000
- Storage: 120 GB/year

### Projected (500K users)
- Files/day: ~1,000,000
- File types: 12.6M images, 4.5M docs, 900K video/zip daily
- Storage: ~2.8 TB/year

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Validate input data consistency**
   - Files/day must align with user count
   - "Gần 1M" ≈ 50K × (500K / 27.7K) ✓

2. **CCU excludes boot overhead**
   - Measure real usage, not total CPU
   - Subtract OS/boot: 15-20% typical

3. **ELK needs hot/warm storage tier**
   - SSD for active data (search performance)
   - HDD for archive (cost savings)

4. **Storage per user is useful metric**
   - 4.32 MB/user/year for Mybox
   - Scale linearly for projection

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** TRUNG BÌNH  
**Vấn đề chính:** Input validation, CCU calculation, ELK tiered storage

**Đặc điểm:**
- File storage with multiple formats
- High volume: ~1M files/day at scale
- ELK for log/metadata search