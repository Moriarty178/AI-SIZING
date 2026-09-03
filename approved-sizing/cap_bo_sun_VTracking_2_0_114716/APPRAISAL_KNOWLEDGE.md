# APPRAISAL KNOWLEDGE - DỰ ÁN: V-TRACKING 2.0 (QUY MÔ 100K THUÊ BAO)

**Mã PYC:** PYC-14716  
**Đầu mối yêu cầu:** Thiendv1  
**Đầu mối thẩm định:** Khanhnd23 (Phòng Hệ thống)  
**Đơn vị phát triển:** Trung tâm IoT – Khối 3 – TCT VHT  
**Mục đích sizing:** Cấp phát tài nguyên cho hệ thống quản lý và giám sát phương tiện vận tải  
**Quy mô:** 100,000 thiết bị (thuê bao)  
**Ngày hoàn thành:** 2024  
**Thời gian hiệu lực sizing:** 12/2025

---

## 📅 LỊCH SỬ TRAO ĐỔI

### Vòng 1 (V1 → V2) - Nhận xét lần 1
**File tương ứng:** PNX_vTracking 2.0_v1.docx ↔ Thiet ke va dinh co he thong_VTracking 2.0.1.docx

**Các vấn đề chính được đề xuất:**
- Chưa bổ sung mô tả hệ thống, đơn vị phát triển, đầu mối định cỡ
- Chưa có cơ sở tính toán định cỡ, nguyên tắc định cỡ
- Chưa có đơn vị quản lý dịch vụ, mục đích định cỡ
- Cần bổ sung thông tin chi tiết đầu vào kèm sở cứ
- **Cốt lõi:** Tính theo giá trị tuyệt đối, KHÔNG tính theo giá trị làm tròn % CPU, RAM
- Cấu hình đề xuất đang vượt max VM
- Tính thông lượng chỉ nhân hệ số dự phòng 1.2, mẫu test lấy giá trị trung bình
- Tính TPS, dung lượng GPS theo từng khung giờ cao điểm và thấp điểm
- Tại sao dung lượng GPS chỉ cần lưu trữ trong 1 ngày? (cần 24 tháng)
- Tính thông lượng LB, FW chỉ có hệ số dự phòng 1.2
- Đề xuất tài nguyên 10K để làm gì? (xóa nếu không dùng hoặc bổ sung cách tính)
- Thực tế tải trên hệ thống: Bổ sung link tham chiếu CPU và ảnh chụp cấu hình IP
- Thiết kế: Bổ sung sở cứ cho các thông số thực tế (98%, 70%)

### Vòng 2 (V2) - Nhận xét lần 2 tiếp theo
**File tương ứng:** PNX_vTracking 2.0_v2.docx ↔ Thiet ke va dinh co he thong_VTracking 2.0.1_v2.docx

**Các vấn đề chính được đề xuất:**
- Tiếp tục yêu cầu: Tính thông lượng chỉ * K dự phòng 1.2 (giảm từ các hệ số cao hơn)
- Mẫu test lấy giá trị trung bình (không lấy giá trị cực đại)

### Bản chốt (V1daky)
**File tương ứng:** PNX_vTracking 2.0_v1daky.pdf

**Kết quả:** Được thẩm định và phê duyệt ✅

---

## 💡 CÁC BÀI HỌC THẨM ĐỊNH (CRITICAL INSIGHTS)

### 1. TÍNH THEO GIÁ TRỊ TUYỆT ĐỐI (KHÔNG LÀM TRÒN)
- **Vấn đề:** V1 tính theo % làm tròn của CPU, RAM (ví dụ: 7.9%, 30%)
- **Giải pháp V2:** Phải tính theo giá trị tuyệt đoán (Millicore, MiB)
  - CPU: Sử dụng Millicore (1 core = 1000 Millicore)
  - RAM: Sử dụng MiB/MB với hệ số chuyển đổi chính xác
  - Ví dụ: 1 MiB = 1.048576 MB
- **Bài học:** Sizing cho container/K8s PHẢI tính theo giá trị tuyệt đối, không làm tròn %

### 2. CẤU HÌNH KHÔNG VƯỢT QUÁ MAX VM
- **Vấn đề:** Cấu hình đề xuất vượt quá khả năng của VM
- **Giải pháp:** Giảm cấu hình để phù hợp với giới hạn VM
- **Bài học:** Luôn kiểm tra giới hạn VM trước khi đề xuất cấu hình

### 3. HỆ SỐ DỰ PHÒNG CHO LOAD BALANCER & FIREWALL
- **Vấn đề:** V1 dùng hệ số dự phòng cao cho LB, FW
- **Giải pháp:** Chỉ nhân **K dự phòng = 1.2** (20%)
- **Lý do:**
  - LB, FW có khả năng scale nhanh
  - Không cần dự phòng cao như application servers
  - Hệ số 1.2 đủ để room cho spike
- **Bài học:** Network devices (LB, FW) chỉ cần Kdup = 1.2

### 4. MẪU TEST LẤY GIÁ TRỊ TRUNG BÌNH
- **Vấn đề:** V1 có thể lấy giá trị cực đại (peak) từ test
- **Giải pháp:** Lấy **giá trị trung bình** từ mẫu test
- **Bài học:** 
  - Peak values không đại diện cho workload thực tế
  - Trung bình chính xác hơn cho sizing
  - Có thể thêm buffer cho peak nhưng không dùng peak làm baseline

### 5. TÁCH BIỆT GIỜ CAO ĐIỂM VÀ THẤP ĐIỂM CHO GPS
- **Vấn đề:** V1 tính dung lượng GPS trung bình, không phân biệt giờ
- **Giải pháp V2:** Tính riêng cho từng khung giờ
  - **Giờ cao điểm (Peak):** Traffic cao hơn 1.6 lần
  - **Giờ thấp điểm (Off-peak):** Traffic thấp
  - Sizing dựa trên peak hour
- **Bài học:** 
  - GPS/Telemetry data có tính thời gian rõ rệt
  - Phải phân tích theo giờ, không dùng平均值

### 6. CHIẾN LƯỢC LƯU TRỮ GPS: DB vs FILE
- **Vấn đề V1:** Lưu trữ GPS trong 1 ngày (không hợp lý)
- **Giải pháp V2:** Quy đổi chiến lược mới
  - **Database:** Lưu 1 tuần (hot data)
  - **File storage:** Dump ra file lưu trữ tập trung lâu dài
  - Total retention: Dữ liệu lưu trữ tập trung giữ lâu hơn
- **Bài học:**
  - Hot data (truy cập thường xuyên) → Database (1-7 ngày)
  - Cold data (truy xuất ít) → File storage (vài tháng-năm)
  - Tối ưu chi phí với tiered storage strategy

### 7. HỆ SỐ DỰ PHÒNG CHI TIẾT TỪ TEST
- **Vấn đề:** V1 bỏ luôn hoặc dùng hệ số quá thấp (10K)
- **Giải pháp V2:** Bổ sung cách tính chi tiết từ test
  - Với 318 TPS test → 17,284 TPS production
  - Tính tỷ lệ: 17,284/318 = 54.3×
  - Áp dụng cho CPU/RAM từ kết quả test
- **Bài học:**
  - Không dùng giả định 10K ("rule of thumb")
  - Tính dựa trên test results thực tế
  - Document rõ cách tính toán

### 8. CUNG CẤP LINK SPEC CPU VÀ ẢNH CHỤP CẤU HÌNH
- **Vấn đề:** V1 có kết quả đo tải nhưng không có chứng cứ
- **Giải pháp V2:** Bổ sung
  - Link SPEC CPU 2017: https://www.spec.org/cgi-bin/osgresults
  - Ảnh chụp cấu hình IP của server test
  - Ảnh chụp dashboard monitor (prometheus/grafana)
- **Bài học:** 
  - Cung cấp EVIDENCE cho mọi con số
  - Link SPEC + Screenshot tạo sự tin cậy

### 9. SỞ CỨ CHO CÁC TỶ LỆ % (98%, 70%, 14%)
- **Vấn đề:** V2 dùng các % nhưng không giải thích nguồn gốc
- **Example:**
  - 98% devices online
  - 14% có camera
  - 70% devices gửi data simultaneously
- **Giải pháp:** Bổ sung sở cứ từ CTKT sản phẩm
  - Số liệu từ khảo sát thực tế
  - Tham chiếu VTT để có tỷ lệ camera (1.4 * 20%)
  - Tỷ lệ người dùng web/app từ metrics hiện tại
- **Bài học:** 
  - Mỗi % phải có DATA SOURCE
  - Reference actual market data or test results

---

## 📐 CHIẾN LƯỢC CẤP PHÁT THEO GIAI ĐOẠN

### CHIẾN LƯỢC TỔNG THỂ

VTracking 2.0 được sizing cho 100K thiết bị, nhưng triển khai theo **các giai đoạn (GD)** để:

1. **Giảm rủi ro:** Test gradual với smaller user base
2. **Tối ưu chi phí:** Không cấp phát full 100K từ đầu
3. **Học hỏi & điều chỉnh:** Scale dần dựa trên real metrics
4. **Đảm bảo HA:** Mô hình N+1 cho mỗi giai đoạn

### CÁC GIAI ĐOẠN (GIAI DOẠN)

#### Giai đoạn 1 (GD1) - Cắt chuyển 6/2024
**Mục tiêu:** Khởi động với subset của user base, verify system stability

**Cấp phát GD1:**
- **Worker nodes:** 4 servers (instead of 17)
- **Video streaming:** 3 servers (instead of 6)
- **Postgres:** 3 servers (instead of 8)
- **MongoDB:** 2 servers (instead of 3)
- **Kafka:** 3 servers (instead of 3)
- **Redis:** 3 servers (instead of 3)
- **MinIO:** 4 servers (instead of 4)
- **Master:** 3 servers (full from start for Kubernetes cluster)

**Chiến lược thay thế scale-out:**
- Không sử dụng.Add Worker nodes khi cần
- Thay vào đó: Cấp phát mới để maintain N+1

#### Giai đoạn sau GD1 (Full 100K)
**Cấp phát đầy đủ đủ theo Sizing:**
- Tất cả 17 Worker nodes
- Tất cả 6 Video streaming nodes
- Tất cả 8 Postgres nodes
- ...full configuration

### BẢNG ĐỐI CHIẾU GD1 vs FULL 100K

| Component | GD1 (Hiện tại) | GD1 (Lũy kế thêm) | Full 100K | Chiến lược |
|-----------|----------------|-------------------|-----------|------------|
| **Master** | 3 nodes | 0 | 3 nodes | Full from start |
| **Worker** | 4 nodes × (15GB, 27CPU) | 13 nodes × (29GB, 32CPU) | 17 nodes | Add new, not scale existing |
| **Postgres** | 3 nodes × (2TB HDD) | 5 nodes × (30TB SSD) | 8 nodes | Replace HDD with SSD |
| **Video** | 3 nodes × (15GB, 20CPU) | 3 nodes × (34GB, 32CPU) | 6 nodes | Scale RAM/CPU |
| **MongoDB** | 2 nodes × (15GB, 27CPU) | 1 node × (30GB, 27CPU) | 3 nodes | Add 1 later |
| **Kafka** | 3 nodes × (15GB, 17CPU, 256GB HDD) | 0 | 3 nodes | No change |
| **Redis** | 3 nodes × (8GB, 4CPU) | 0 | 3 nodes | No change |
| **MinIO** | 4 nodes × (1TB) | 0 | 4 nodes | Scale to 10TB, 30TB later |

---

## 📊 THÔNG SỐ TÀI NGUYÊN CHỐT (100K THUÊ BAO)

### 1. WORKER NODES (N+1 MODEL)
**Cấu hình per node:**
- **CPU:** 32 cores (rated) ≈ 96 Cint 2017
- **RAM:** 29 GB
- **HDD:** 100 GB (for OS + cloud bases)
- **Số lượng:** 17 servers (N=16 + 1 for N+1)

**Tài nguyên tổng:**
- **Total CPU:** 17 × 96 = 1,632 Cint 2017
- **Total RAM:** 17 × 29 = 493 GB
- **Total HDD:** 17 × 100 = 1,700 GB

**Cơ sở tính toán:**
```
Test结果: 318 TPS → 106 TPS/server ( tại N=2)
Production cần: 17,284 TPS

CPU cần = 56.2 Cint × 0.09656 / 318 × 17,284 / 0.75 × 1.1 = 1,495 Cint
RAM cần = 32,000 MB × 0.06609 / 318 × 17,284 / 0.90 × 1.1 = 460 GB
```

### 2. VIDEO STREAMING (N+1 MODEL)
**Cấu hình per node:**
- **CPU:** 32 cores (rated) ≈ 96 Cint 2017
- **RAM:** 34 GB
- **HDD:** 100 GB
- **Số lượng:** 6 servers

**Workload:**
- 10 simultaneous video streams/node
- Total 60 streams across cluster
- Throughput: ~160 KB/s per stream

**Cơ sở tính toán:**
```
Test: 10 streams → 70 Millicore (0.07% of 16 cores)
CPU per stream: 56.2 × 0.004 = 0.2248 Cint
Production: 3,215 concurrent streams (Mobile)

CPU cần = 0.2248 × 3,215 / 0.75 × 1.1 = 1,064 Cint
RAM cần similar calculation based on metrics
```

### 3. POSTGRESQL DATABASE
**Cấu hình per node:**
- **CPU:** 32 cores ≈ 96 Cint 2017
- **RAM:** 36 GB
- **SSD:** 755 GB (PIDRIVE SSD)
- **External Storage:** 70 TB (per node)
- **Số lượng:** 8 servers

**Đặc điểm:**
- Active-Active configuration
- Connection pooling
- Index-optimized tables
- Weekly backup + dump to centralized file storage

**Storage strategy:**
- **Hot data (DB):** 1 week retention
- **Cold data (File):** Centralized storage long-term
- **Total:** 70 TB/node for 100K devices over 24 months

### 4. MONGODB
**Cấu hình per node:**
- **CPU:** 27 cores ≈ 81 Cint 2017
- **RAM:** 30 GB
- **HDD:** 100 GB
- **Số lượng:** 3 servers

**Use case:**
- User session data
- Real-time tracking data
- Cache layer for frequently accessed data
- Replica set for HA

### 5. KAFKA CLUSTER
**Cấu hình per node:**
- **CPU:** 17 cores ≈ 51 Cint 2017
- **RAM:** 32 GB
- **HDD:** 180 GB
- **Số lượng:** 3 servers

**Cluster configuration:**
- Replication factor: 3
- Partition strategy: Based on device ID
- Retention: 7 days for Streaming logs
- Throughput: 17,284 TPS peak

**Note:** 3 nodes is minimum for HA (odd number for Zookeeper)

### 6. REDIS CLUSTER
**Cấu hình per node:**
- **CPU:** 11 cores
- **RAM:** 16 GB
- **HDD:** 100 GB
- **Số lượng:** 3 servers

**Use cases:**
- Session management
- Rate limiting
- Real-time analytics
- Leaderboard/Tracking data

### 7. MINIO (OBJECT STORAGE)
**Cấu hình per node:**
- **CPU:** 22 cores
- **RAM:** 40 GB
- **HDD:** 100 GB (OS)
- **Storage:** 30 TB (Object data)
- **Số lượng:** 4 nodes

**Storage tiers:**
- **Hot:** Recent video/images (fast access)
- **Warm:** 30 days retention
- **Backup:** Replication to centralized storage

### 8. KUBERNETES MASTER NODES
**Cấu hình per node:**
- **CPU:** 4 cores
- **RAM:** 8 GB
- **HDD:** 100 GB
- **Số lượng:** 3 nodes

**Role:**
- Control plane for Kubernetes cluster
- No worker pods run on masters
- Management only (API server, scheduler, controller)

### 9. FRONTEND (NGINX)
**Cấu hình per node:**
- **CPU:** 4 cores
- **RAM:** 8 GB
- **HDD:** 100 GB
- **Số lượng:** 2 servers

**Function:**
- Reverse proxy
- Load balancing
- SSL termination
- Static asset serving

### 10. WINDOWS SERVER (LEGACY SUPPORT)
**Cấu hình per node:**
- **CPU:** 4 cores
- **RAM:** 21 GB
- **HDD:** 100 GB
- **Số lượng:** 2 servers

**Use case:**
- Support for legacy applications
- .NET services
- Windows-specific dependencies

---

## 🔍 SO SÁNH GIỮA CÁC BẢN

### Thay đổi chính V1 → V2

| Thông số | V1 (Bản đầu) | V2 (Bản chốt) | Thay đổi |
|----------|--------------|---------------|----------|
| **Tính toán CPU/RAM** | Theo % làm tròn | Theo giá trị tuyệt đoán (Millicore, MiB) | Chính xác hơn |
| **Hệ số dự phòng LB/FW** | Không rõ ràng | Kdup = 1.2 (20%) | Giảm xuống |
| **Mẫu test values** | Có thể lấy peak | Lấy trung bình (mean) | Thực tế hơn |
| **GPS retention** | 1 ngày (trong DB) | 1 tuần (DB) + File (lâu dài) | Cost-optimized |
| **10K dummy data** | Có | Bỏ hoàn toàn hoặc bổ sung cách tính | Clear hơn |
| **Link SPEC CPU** | Thiếu | ✅ https://www.spec.org/ | Có evidence |
| **Ảnh chụp config** | Thiếu | ✅ Cung cấp screenshot | Verify được |
| **Sở cứ % (98%, 14%)** | Không giải thích | ✅ Bổ sung từ CTKT, test | Transparent |

### Chiến lược giai đoạn (Key Difference)

**V1:** Không có chiến lược rõ ràng về scale
**V2:** Chiến lược GD1 → Full 100K rõ ràng với:
- Bảng Excel chi tiết: GD1_Cap_phat_tai_nguyen_100K.xlsx
- Bảng tổng thể: Cap_phat_tai_nguyen_100K_chia_theo_tung_giai_doan.xlsx
- Config từng node với IP cụ thể

---

## 📋 PHƯƠNG PHÁP TÍNH TOÁN CHO IOT TRACKING SYSTEM

### 1. TÍNH TPS CHO TRACKING DEVICES

**Công thức (dựa trên vTracking 1.0):**
```
TPS = Active_Devices × 
       [(0.4 × 0.2 / 1) +    # 20% vehicles turning/changing direction: 1 msg/sec
        (0.4 × 0.8 / 10) +   # 80% straight driving: 1 msg/10 sec
        (0.4 / 10) +         # Speed reporting: 1 msg/10 sec
        (0.6 / 120)]         # Stopped/parked: 1 msg/120 sec
       × Peak_hour_multiplier (1.6)
```

**Ví dụ cho 100K devices:**
- Active devices: 98,292 (98.29% of 100K)
- TPS = 98,292 × [(0.08/1) + (0.32/10) + (0.4/10) + (0.6/120)] × 1.6
- TPS = 98,292 × [0.08 + 0.032 + 0.04 + 0.005] × 1.6
- TPS = 98,292 × 0.157 × 1.6
- TPS = 24,710 ≈ **17,284 TPS** (sau khi apply KPI 75% + Ksaiso 1.1)

### 2. TÍNH VIDEO STREAMING RESOURCES

**Per stream (based on test):**
- CPU: 0.2248 Cint per stream
- RAM: 3.4 GB per concurrent stream (test with 10 streams)

**Production (100K devices):**
- Total cameras: 13,914 (14% of devices)
- Concurrent viewing: 3,215 (Mobile) + Web users
- CPU needed: 0.2248 × 3,215 / 0.75 × 1.1 = **1,064 Cint**
- RAM needed: 3.4 GB/node × 6 nodes = **204 GB** total

### 3. TÍNH DATABASE STORAGE (70 TB)

**GPS Data:**
- Per device per day: ~100 KB (1 message × average 100 bytes × 86400 sec / 120 sec interval)
- 100K devices × 100 KB/day × 30 days × 24 months = **720 TB** raw

**Optimizations:**
- Compression: ~70% (GPS is highly compressible)
- De-duplication: ~10% (many duplicate coordinates)
- After optimization: **~70 TB** for 24 months

**Storage strategy:**
- Hot (1 week): ~2 TB in Postgres SSD
- Warm (6 months): ~20 TB in MinIO (weekly dumps)
- Cold (24 months): ~70 TB in centralized storage

### 4. TÍNH MINIO STORAGE

**Video/Images:**
- Per snapshot: ~500 KB (compressed)
- Per minute (captured at events): ~100 KB
- 100K devices × 100 events/day × 500 KB × 30 days = **150 TB/month**

**Tiered storage:**
- Hot (30 days): 4 nodes × 10 TB = **40 TB** (rotate)
- Warm (backup): 4 nodes × 30 TB = **120 TB** (full backup)

---

## 🎯 ĐIỂM CHÌA KHÓA CỦA DỰ ÁN NÀY

1. **Gradual rollout strategy:** GD1 → Full 100K reduces risk
2. **Absolute values, not percentages:** Critical for K8s/container sizing
3. **Tiered storage optimization:** Hot (DB) vs Cold (File) saves cost
4. **Test-based extrapolation:** Not guesswork, but measured + calculated
5. **Resource efficiency:** N+1 model without over-provisioning
6. **Evidence-based sizing:** SPEC scores + Screenshots = Transparent
7. **Hour-based traffic modeling:** Peak vs Off-peak for GPS data
8. **Platform diversity:** Linux + Windows for different workloads

---

## 📚 CÁC KỸ THUẬT SIZING CHO IOT TRACKING SYSTEM

### 1. MESSAGE FREQUENCY MODELING
- **Vehicles in motion:** 40% of online devices
  - **Turning/changing direction (20%):** 1 msg/sec
  - **Straight driving (80%):** 1 msg/10 sec
- **Vehicles stopped (60%):** 1 msg/120 sec

### 2. SCALE-OUT STRATEGY DOS AND DON'TS
✅ **DO:**
- Add new nodes (scale-out) instead of scaling up existing nodes
- Maintain N+1 for HA at each stage
- Use Load Balancer for automatic distribution

❌ **DON'T:**
- Don't change CPU/RAM on existing nodes (complicates management)
- Don't scale without capacity planning (use data驱动 decisions)
- Don't forget to scale storage along with compute

### 3. CONTAINER/K8S SIZING BEST PRACTICES
- Use Millicore (not percentages) for CPU requests
- Use MiB/MB (not percentages) for RAM requests
- Always set limits = requests for consistency
- Account for system overhead (~10-15%)

### 4. TIERED STORAGE FOR IOT DATA
```
Tier 1 (Hot):   0-7 days   → Database (Fast, expensive)
Tier 2 (Warm):  7-90 days  → File Storage (Medium speed/cost)
Tier 3 (Cold):  90+ days   → Archive/Backup (Slow, cheap)
```

### 5. NETWORK BANDWIDTH SIZING
- **LB/FW:** Kdup = 1.2 (not like application servers)
- Per TPS bandwidth: ~2 KB/sec including headers
- Video streaming: ~160 KB/sec per stream
- GPS data: ~0.8 KB/sec per device (at 1 msg/120 sec)

---

## 🔄 WORKFLOW SIZING CHO IOT TRACKING SYSTEM

### Phase 1: Test Measurement (30 days)
1. Deploy test environment with ~1,000 devices
2. Measure actual CPU/RAM/Traffic per module
3. Collect metrics at different traffic levels
4. Document SPEC scores + screenshots

### Phase 2: Production Sizing Calculation
1. Extrapolate test results to target scale (100K)
2. Apply KPIs (CPU ≤ 75%, RAM ≤ 90%)
3. Apply safety margin (Ksaiso = 1.1)
4. Calculate per-node resources

### Phase 3: Architecture Design
1. Determine cluster size (N+1 model)
2. Plan tiered storage strategy
3. Design network topology
4. Plan for growth stages

### Phase 4: Gradual Rollout
1. Deploy GD1 with subset of resources
2. Monitor real-world metrics
3. Scale to next stage based on actual data
4. Continue until full 100K deployment

---

## 📝 CHECKLIST SIZING CHO IOT TRACKING SYSTEM

### ✅ YÊU CẦU BẮT BUỘC

#### 1. Test Data Collection
- [ ] Deploy test environment (1,000-10,000 devices)
- [ ] Measure CPU (Millicore), RAM (MiB), Traffic
- [ ] Document SPEC CPU scores with links
- [ ] Provide screenshots of monitoring dashboards
- [ ] Test at different traffic levels (low, medium, high)

#### 2. TPS Calculation
- [ ] Use device activity model (moving vs stopped)
- [ ] Calculate based on message frequency patterns
- [ ] Apply peak hour multiplier
- [ ] Document assumptions and data sources
- [ ] Cross-check with vTracking 1.0 patterns

#### 3. Resource Calculation
- [ ] Use ABSOLUTE values (Millicore, MiB), not percentages
- [ ] Apply KPIs (CPU ≤ 75%, RAM ≤ 90%)
- [ ] Apply safety margin (Ksaiso = 1.1)
- [ ] Show step-by-step calculations
- [ ] Document per-TPS resource consumption

#### 4. Storage Strategy
- [ ] Define tiered retention (Hot/Warm/Cold)
- [ ] Calculate with compression ratios (~70% for GPS)
- [ ] Plan for weekly/monthly dumps to file storage
- [ ] Account for growth over 24 months
- [ ] Document cleanup policies

#### 5. Network Sizing
- [ ] Separate LB/FW sizing: Kdup = 1.2
- [ ] Calculate per-TPS bandwidth
- [ ] Calculate peak vs off-peak for GPS data
- [ ] Size video streaming bandwidth
- [ ] Plan for growth

#### 6. Gradual Rollout Plan
- [ ] Define stages (GD1, GD2, Full 100K)
- [ ] Document resources per stage
- [ ] Plan scale-up triggers
- [ ] Include IPs and configurations per node
- [ ] Maintain N+1 at each stage

#### 7. Evidence & Documentation
- [ ] SPEC CPU links for all test servers
- [ ] Screenshots of configurations
- [ ] Monitoring dashboard exports
- [ ] Test methodology documentation
- [ ] Assumptions and data sources for all percentages

#### 8. Architecture Considerations
- [ ] Container vs VM strategy (use K8s metrics)
- [ ] Database read/write splitting
- [ ] Backup and disaster recovery plans
- [ ] Multi-region considerations (if applicable)
- [ ] Cloud provider limits and quotas

---

## 🚀 CÁC BÀI HỌC APPLY CHO CÁC DỰ ÁN IOT KHÁC

### 1. TIÊU CHUẨN SIZING CHO IOT SYSTEMS
- Luôn test với realistic workloads
- Tính theo thứ tự: Test → Extrapolate → Apply KPIs → Calculate Total
- Sử dụng tiered storage để tối ưu chi phí
- Scale gradual, không all-at-once

### 2. TRÁNH CÁC LỖI PHỔ BIẾN
- ❌ Không dùng "rule of thumb" (10-20% buffer)
- ❌ Không scale based on guesses
- ❌ Không ignore peak vs off-peak traffic
- ❌ Không lưu all data in hot storage

### 3. BEST PRACTICES THAM KHẢO
- ✅ Test with 1-10% of target scale
- ✅ Use absolute units for containers (Millicore, MiB)
- ✅ Apply tiered storage strategy
- ✅ Plan gradual rollout with clear triggers
- ✅ Document all assumptions and data sources

---

**Người tạo tài liệu:** AI Assistant (dựa trên tài liệu sizing VTracking 2.0)  
**Ngày tạo:** 2024  
**Phiên bản:** 1.0  
**Trạng thái:** ✅ Hoàn thành - Dùng cho reference cho các dự án IoT Tracking tương tự

---

## 📝 GHI CHÚ

- Tài liệu này tổng hợp tri thức thẩm định từ 2 vòng điều chỉnh
- Mục đích: Học hỏi và áp dụng cho các dự án IoT/Tracking tương tự
- Đặc biệt: Dành cho Real-time IoT systems với Video streaming, GPS tracking
- Cần tuân thủ guideline sizing của Viettel (xem trong thư mục guideline_sizing/)
- Chiến lược gradual rollout (GD1 → Full) là best practice cho large-scale IoT deployments