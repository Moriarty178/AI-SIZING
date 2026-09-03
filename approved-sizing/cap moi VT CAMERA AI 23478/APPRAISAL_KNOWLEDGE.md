# APPRAISAL KNOWLEDGE - VIETTEL AI CAMERA

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** VIETTEL AI CAMERA  
**Mã PYC:** PYC-23096  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 2 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Triển khai hệ thống Viettel AI Camera  
**Đầu mối:** Anhnt576  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### 2 Vòng phản biện

**Yêu cầu chính:**
1. **300 Camera devices:** Cần bổ sung sở chỉ
2. **Multiple reference systems:** VHT S3, HT FaceSearch (CCU=155), GSCG Kafka (250K calls/day)
3. **Large storage:** 10.1TB total, 1.5TB RAM, 121M records
4. **GPU requirement:** 10.207.188.9 config needs justification
5. **Bandwidth:** 833 Mbps = 155 CCU × 280KB × 2 images × 8 × 1.2
6. **RPS:** 28.33 requests/sec
7. **Network topology:** Zone Internet → partner systems (JF Camera)
8. **Retention:** 90 days for VideoBot

---

## 💡 TRI THỨC RÚT RA

### 1. AI Camera bandwidth calculation

**FaceSearch reference (CCU=155):**
```
Per transaction:
  - Image: 250 KB
  - Text metadata: 30 KB
  - Minimum: 2 images per transaction
  
Bandwidth = 155 × ((250+30) KB × 2) × 8 × 1.2
         = 833 Mbps
         
Initial deployment: 300 Mbps (trial phase)
Production: >=1 Gbps
```

### 2. Storage indexing multiplier

**Formula: 7×2 indexing factor**
```
Raw data: 7 TB
With indexing: 7 × 2 = 14 TB

Reason:
  - Elasticsearch indexes multiple fields
  - Each record creates several index entries
  - Search optimization requires overhead
  - Standard ES practice: 2-3× raw size
```

### 3. GPU for AI workloads

**Config: 10.207.188.9**
```
AI Camera applications:
  - Face detection/recognition
  - Object detection
  - Video analytics
  - Real-time processing

GPU requirements:
  - CUDA cores: Higher is better for inference
  - VRAM: Critical for batch processing images
  - Tensor cores: For AI model acceleration
```

### 4. Multi-system architecture

**Reference systems:**
```
VHT S3: Object storage
  - 7.56 TB data
  - 300 cameras
  - 3.6 GB/day/device

HT FaceSearch: Reference baseline
  - CCU: 155
  - Image processing workload
  - Similar recognition patterns

GSCG Kafka: Message queue
  - 250K calls/day reference
  - Event streaming architecture
```

### 5. RPS calculation

**Requests Per Second:**
```
RPS: 28.33

Calculation:
  - 200K transactions/day
  - 200,000 / 24 / 3600 = 2.31 TPS average
  - Peak (hourly): 8-10x average
  - RPS 28.33 = Peak rate
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### Input
- Cameras: 300 devices
- Resources: 288 vCPU, 384 GB RAM, 2.5TB SSD
- RPS: 28.33
- Transactions/day: 200K average

### Storage
- Total: 10.1 TB (with indexing 7×2 = 14 TB)
- RAM: 1.5 TB system total
- Records: 121 million
- Retention: 90 days

### Network
- Bandwidth: 833 Mbps, deploy 1 Gbps
- Trial phase: 300 Mbps acceptable
- Zone: Internet (partner systems)

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **AI = GPU + Storage intensive**
  - Recognition models need GPU
  - Indexed data 2-3× raw size (ES overhead)
  - Plan for both compute and storage growth

2. **Reference multiple similar systems**
  - FaceSearch (CCU=155) for workload
  - S3 for storage patterns
  - Kafka for event streaming
  - Don't rely on single reference

3. **Bandwidth calculation by images**
  - Per image size × images/transaction
  - Multiply by transactions/second
  - Include protocol overhead
  - Add safety margin

4. **RPS vs TPS clarification**
  - RPS = Web requests (may include multiple transactions)
  - TPS = Database transactions
  - Different metrics, measure both

5. **Zone Internet considerations**
  - Public-facing systems
  - Partner connectivity (JF Camera)
  - Need DDoS protection
  - CDN benefit for static assets

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** RẤT CAO  
**Số vòng PNX:** 2 (multiple references, sizing validation)  
**Vấn đề chính:** Multiple reference systems, indexing multiplier, GPU sizing

**Đặc điểm:**
- AI-powered camera recognition
- 300 camera deployment
- High storage requirements (10TB+)
- GPU-intensive workload
- Zone Internet deployment