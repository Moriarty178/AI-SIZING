# APPRAISAL KNOWLEDGE - AR/VR THỬ NGHIỆM CHO QUẢNG BÁ 5G

**Mã PYC:** PYC-645/VAS  
**Đầu mối yêu cầu:** ADT Creative  
**Đầu mối thẩm định:** Phòng Hệ thống  
**Đơn vị phát triển:** Trung tâm VAS - Khối Giải pháp CNTT và Dịch vụ số  
**Mục đích sizing:** 08 server cho AR/VR thử nghiệm quảng bá 5G  
**Quy mô:** 1,000 users, CCU 225  
**Ngày hoàn thành:** 10/05/2024  
**Trạng thái phản hồi:** TRƯỜNG HỢP B - Duyệt thẳng, không có PNX ✅

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ✅ **DUYỆT THẢNG (TRƯỜNG HỢP B)**
- Chỉ 1 file sizing PDF đã ký
- Không có phiếu nhận xét (PNX)
- Hồ sơ mẫu - tham chiếu tốt

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH

### 1. CDN CACHE RATIO 98% GIẢM BĂNG THÔNG ORIGIN
**Architecture:**
```
Enduser → CDN → Origin (Storage)

Nội dung 4K: 25 Mbps mỗi stream
CCU: 225 concurrent users
```

**Bandwidth calculation:**
```
Enduser → CDN:
= 225 users × 25 Mbps = 5,625 Mbps = 5,5 Gbps

CDN → Origin:
= 5,5 Gbps × (100% - 98% cache) = 5,5 × 0,02 = 0,11 Gbps

Cache hit ratio: 98% → Chỉ 2% traffic đến Origin
```

**Bài học:**
- CDN **cache ratio cực kỳ quan trọng** cho video streaming
- 98% cache → Giảm 98% bandwidth đến Origin
- Validate cache ratio with actual measurements (CDN analytics)
- Plan for cache miss scenarios (worst case: 0% cache = 5,5 Gbps to Origin)

### 2. TRANSCODER CẦN CPU CAO (16 vCPU) CHO VIDEO 4K
**Sizing:**
```
Livestream Transcoder: 16 vCPU, 64 GB RAM
VOD Transcoder: 16 vCPU, 64 GB RAM

Per server: 2 instances (N+1 backup)
```

**Why 16 vCPU?**
- Video transcoding (livestream + VOD) là **compute-intensive**
- 4K transcoding demanding: 1 transcode ≈ 2-4 vCPU
- CCU 225 → Multiple concurrent transcodes
- GPU acceleration recommended but not specified here

**Bài học:**
- Transcoder workloads are CPU/GPU intensive, NOT I/O intensive
- HDD 200GB sufficient (OS + app only, video streams in-memory/temp)
- RAM 64GB critical for frame buffering
- Consider GPU acceleration for production systems

### 3. STORAGE CHO NỘI DUNG AR/VR: 5TB
**Requirement:**
```
Phân vùng lưu trữ nội dung AR/VR: >= 5TB
```

**Justification:**
- 1000 nội dung (content pieces)
- Mỗi nội dung 4K → khoảng 5GB (compressed)
- 1000 × 5GB = 5TB (matches requirement)

**Storage architecture:**
```
WEB/CMS servers (2): Kết nối đến 5TB storage
Livestream Transcoder (2): Kết nối đến 5TB storage
VOD Transcoder (2): Kết nối đến 5TB storage
DB servers (2): Local 200GB (MySQL)
```

**Bài học:**
- Shared storage (5TB) cho tất cả transcoder nodes
- Video content stored centrally
- 5TB may need scaling: Plan for growth (e.g., 10TB, 20TB)
- Consider object storage (S3, MinIO) instead of file system for better scalability

### 4. N+1 BACKUP CHO 8 SERVERS
**Servers:**
```
WEB/CMS: 2 servers (Active-Active)
Livestream Transcoder: 2 servers (Active-Active)
VOD Transcoder: 2 servers (Active-Active)
DB: 2 servers (Active-Standby or Active-Active cluster)

Total: 8 servers
```

**N+1 interpretation:**
- 2 instances per service = N+1 (N=1 active + 1 backup)
- Or = N servers where each service has minimum backup

**Bài học:**
- For trial systems: 2 instances sufficient
- Active-Active for compute (WEB, Transcoder)
- Active-Standby or cluster for database (MySQL)
- Single point of failure eliminated: All services have backup

### 5. HỆ THỐNG THỬ NGHIỆM → ÍT NGHIÊM GHT MORE RELAXED
**Context:**
```
Mục đích: Thử nghiệm quảng bá 5G Viettel
Users: 1,000 (trial)
CCU: 225 (peak)
Nội dung: 1000 content pieces
```

**Implications:**
- Không cần DC-DR (thử nghiệm, không production)
- N+1 backup adequate (not full disaster recovery)
- Tighter SLA acceptable (maintenance windows OK)
- Focus on functionality over 99.999% availability

**Bài học:**
- Trial systems = less stringent sizing compared to production
- Trade-off: Cost vs. Availability → Accept lower availability for trials
- Still important: N+1 backup, monitoring, incident response
- Plan for production sizing when transitioning from trial to live

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### SERVER CONFIGURATIONS (8 SERVERS)

| Service | CPU | RAM | Storage | Network | Quantity |
|---------|-----|-----|---------|----------|----------|
| **WEB/CMS** | 4 vCPU | 16 GB | 200 GB HDD | 1 IP DCN, 1 IP Public | 2 |
| **Livestream Transcoder** | 16 vCPU | 64 GB | 200 GB HDD | 1 IP DCN, 1 IP Public | 2 |
| **VOD Transcoder** | 16 vCPU | 64 GB | 200 GB HDD | 1 IP DCN | 2 |
| **Database (MySQL)** | 2 vCPU | 6 GB | 200 GB HDD | 1 IP DCN | 2 |
| **Shared Storage** | - | - | 5TB | Network attached | 1 |

**Total:**
- CPU: 76 vCPU (4×2 + 16×2 + 16×2 + 2×2 = 8 + 32 + 32 + 4 = 76)
- RAM: 300 GB (16×2 + 64×2 + 64×2 + 6×2 = 32 + 128 + 128 + 12 = 300)
- Storage: 9.6 TB local (200GB × 8 = 1,6 TB) + 5 TB shared = 6.6 TB

### NETWORK BANDWIDTH

| Connection | Bandwidth | Ghi chú |
|------------|-----------|---------|
| **Enduser → CDN** | 1–5,5 Gbps | Peak 5,5 Gbps cho 225 CCU @ 25 Mbps |
| **CDN → Origin** | 0,11–1 Gbps | 98% cache hit ratio |
| **Cache ratio** | 98% | CDN cached content |

**Rationale:**
- CDN absorbs 98% of bandwidth →减轻 Origin server burden
- 225 CCU × 25 Mbps = 5,625 Mbps (5,5 Gbps) to CDN
- Cache miss (2%): 5,5 Gbps × 0,02 = 0,11 Gbps to Origin

---

## 🎯 KEY LEARNING

1. **CDN cache ratio:** 98% → Giảm 98% bandwidth đến Origin (critical for video)
2. **Transcoder CPU-intensive:** 16 vCPU, 64 GB RAM cho 4K transcoding
3. **Shared storage strategy:** 5TB centralized content for all transcoder nodes
4. **Trial systems:** N+1 backup adequate (not full DC-DR needed)
5. **Network sizing with CDN:** Separate băng thông cho (Enduser → CDN) vs (CDN → Origin)
6. **4K video bandwidth:** 25 Mbps per stream (base assumption for 225 CCU)
7. **Database minimal:** 2 vCPU, 6 GB sufficient for trial (not production)
8. **Object storage consideration:** 5TB may need scaling (S3/MinIO for better performance)

---

**Người tạo:** AI Assistant  
**Ngày:** 2024  
**Phiên bản:** 1.0  
**Trạng thái:** ✅ Hoàn thành - TRƯỜNG HỢP B (duyệt thẳng, hồ sơ mẫu)

**Ghi chú:** Đây là sizing cho hệ thống **AR/VR thử nghiệm**. 8 servers với CDN cache ratio 98% cho bandwidth efficiency. Transcoder nodes (16 vCPU) intensive compute cho 4K video transcoding.