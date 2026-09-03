# APPRAISAL KNOWLEDGE - PHÍ BÁN HÀNG 4.0 (PBH 4.0)

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** HỆ THỐNG PHÍ BÁN HÀNG BONUS 4.0  
**Mã PYC:** PYC-20043  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 6 VÒNG (TRƯỜNG HỢP A)  
**Số vòng PNX:** 6 (NHIỀU LẦN SỬA)  
**Đầu mối:** thanhdv125  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### 6 Vòng phản biện (v1→v6)

**Điểm chính:**
1. **Test system sizing:** Sizing theo test (18GB test in 25 min)
2. **CPU core mismatch:** Cấu hình 32 cores nhưng chỉ chạy 20 cores
3. **Cint rate calculation:** 175 * 20/32 = 109.375 (why only 20 active?)
4. **S3 storage:** Ceph S3 system với replicate 3
5. **Network throughput:** 12Gbps (cần làm rõ!)
6. **Database:** Chưa bao gồm DB trong sizing này

---

## 💡 TRI THỨC RÚT RA

### 1. Test-based sizing - Validation critical

**PBH approach:**
```
Test: 18GB in 25 minutes
Scaling: Need 5,520.8 GB in 180 minutes

Method:
  Target = 18 × (180/25) = 129.6 GB (wrong linear)
  Correct: Extrapolate rate per minute
  Rate = 18GB / 25min = 0.72 GB/min
  Target = 0.72 × 180 = 129.6 GB ✓
```

**Danger:** Linear scaling may not hold for large volumes
- Bottlenecks: IOPS, network, memory
- Must test with 324GB in 12h to validate

### 2. Partial CPU utilization issue

**Problem:**
```
Configuration: 32 cores
Active usage: 20 cores only  
Cint_rate: 175 * 20/32 = 109.375
```

**Why only 20 cores?**
- License limitation? (unlikely in 2024)
- NUMA binding requirement?
- Application not multi-threaded?
- **Must explain this constraint!**

### 3. S3 storage with replication factor

**Ceph S3 setup:**
```
Replication factor: 3
Usable storage = Total / 3

Example:
  13 nodes × 1TB/node = 13TB total
  Usable: 13TB / 3 = 4.33 TB only
```

**Decision changed:**
- Initially: Replicate 3
- Later: Bỏ replicate lên 3 → Changed to standard storage
- **Reason:** Cost impact too high (3x storage needed)

### 4. Network throughput: 12Gbps validation

**Question:** 12Gbps đi đâu?

**Analysis needed:**
```
If 12Gbps goes through shared FW/LB:
  → Will impact other systems!
  → Need dedicated network path

If 12Gbps is internal cluster:
  → Minimize cross-rack traffic
  → Use spine-leaf architecture
```

**Formula:**
```
Throughput = Data_volume / Time_window
3960GB in 12h = 3960 / 12 / 3600 = 0.0917 GB/s
= 0.733 Gbps

Peak may be 10-15x average → 7-11 Gbps ✓
```

### 5. 110 tables/database - Sampling strategy

**Problem:** 110 tables, too many to size individually

**Sampling approach:**
```
1. Identify largest 5-10 tables
2. Size for those (represent 60-80% of data)
3. Add buffer for remaining small tables
4. Verify with actual measurement

Better: Automated query to get top 10 by size
```

### 6. RAM 125GB - Physical server constraint

**Issue:** 
```
125GB RAM suggests physical server
But: Can we virtualize?

Viettel threshold: <64GB for single VM
125GB > 64GB → Should consider:
- 2 VMs of 64GB each (over-provisioned)
- Or 3 VMs with ~42GB each
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### K8S Cluster (sized separately, no DB)
- Test baseline: 18GB in 25 min
- Target: 5,520GB in 180 min
- Storage: S3 (no longer Ceph replicate 3)
- CPU: 32 cores (20 active, 12 standby?)
- RAM: 125GB per node

### Data volume
- Monthly: 2.9TB (2900 billion records)
- 50% raw data
- Sample: 5 largest tables represent 110 tables

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Test scaling may not be linear for large jumps**
   - 18GB → 5,520GB is 300x increase
   - Validate with intermediate volume (324GB)

2. **Partial CPU utilization must be explained**
   - 20/32 cores active = 62.5%
   - Why not use all 32 cores?

3. **Replication factor = 3x cost**
   - Careful with cost-sensitive systems
   - Changed to standard storage after review

4. **Network throughput needs dedicated path**
   - 12Gbps through shared FW = problem
   - Consider dedicated network or bypass

5. **Database sizing separate from app cluster**
   - K8S cluster sizing ≠ Database sizing
   - Need separate DB sizing document

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** RẤT CAO  
**Số vòng PNX:** 6 (nhiều vấn đề logic)  
**Vấn đề chính:** Test-based scaling validation, partial CPU usage, S3 replicate, network throughput

**Đặc điểm:**
- K8S-based microservices
- High data volume: 2.9TB/month
- S3 object storage
- 6 rounds of feedback (record high!)