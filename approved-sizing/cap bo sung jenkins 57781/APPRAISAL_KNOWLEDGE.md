# APPRAISAL KNOWLEDGE - DỰ ÁN: JENKINS CI/CD BỔ SUNG MASTER NODES

**Mã PYC:** PYC-57781  
**Đầu mối yêu cầu:** PhucNLX (Trung tâm CN - VHKT)  
**Đầu mối thẩm định:** DucTN8 (Phòng Hệ thống)  
**Đơn vị phát triển:** Phòng Vận hành khai thác - Trung tâm Công nghệ thông tin - VTT  
**Mục đích sizing:** Bổ sung 3 master nodes độc lập, tách biệt khỏi worker nodes  
**Quy mô:** 85 hệ thống VTT tự VHKT  
**Ngày hoàn thành:** 27/11/2025  
**Số và ký hiệu:** 68/TL-VHKT

---

## 📋 TRẠNG THÁI HỒ SƠ

**Loại hồ sơ:** ✅ **DUYỆT THỲNG (TRƯỜNG HỢP B)**
- Không có file phản hồi thẩm định (PNX)
- Hồ sơ được ký duyệt ngay trong lần trình đầu tiên
- Đây là một hồ sơ MẪU (Golden Pattern) cho việc sizing theo tiêu chuẩn

---

## 📊 THÔNG SỐ KỸ THUẬT CHỐT

### 1. BỐ CẢNH HIỆN TẠI (TRƯỚC KHI BỔ SUNG)

**Hạ tầng Kubernetes cũ:**
- **Số lượng:** 3 servers
- **Role:** vừa làm Control-plane (master) vừa làm Worker
- **IP:** 10.208.95.192, 10.208.95.193, 10.208.95.194
- **Vấn đề:**
  - Không có control-plane riêng biệt
  - Chỉ có 2 bản sao etcd (không đạt chuẩn 3)
  - Nguy cơ mất quorum → ảnh hưởng độ sẵn sàng
  - Không tách biệt được tài nguyên giữa master và workload

### 2. ĐỀ XUẤT BỔ SUNG (SAU KHI CẤP PHÁT)

**Mô hình mới:**
- **Bổ sung 3 master nodes mới:** Master-only (không chạy workload)
- **Giữ nguyên 3 servers cũ:** Chuyển thành Worker-only
- **Tổng cộng:** 6 nodes (3 master + 3 worker)

**Cấu hình chi tiết:**

#### Master Nodes (3 servers mới)
| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | 15 Cint | Theo checklist K8S |
| **RAM** | 8 GB | Theo checklist K8S |
| **HDD** | 100 GB | Chưa bao gồm 60GB cho OS |
| **Storage format** | Block storage | |
| **Yêu cầu mạng** | Cùng dải 10.208.95.x | Để tiện chuyển đổi với LB và các nodes cũ |
| **Storage cluster** | Trên 3 cụm storage khác nhau | Để đảm bảo HA |

#### Worker Nodes (3 servers cũ)
- **IP:** 10.208.95.192, 10.208.95.193, 10.208.95.194
- **Role:** Chỉ chạy workload, không còn role master
- **Không cần bổ sung tài nguyên** (chuyển đổi role)

#### Load Balancer (1 unit)
| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **Thông lượng** | 1 Gbps | Tính cho 85 hệ thống |
| **Backend port** | 8085 (nếu dùng LB cũ) hoặc 6443 (nếu cấp mới) | TCP mode |
| **Certificate** | Không cài | |
| **X-forward-for** | Không bật | |
| **Backend pool** | Trỏ đúng IP của 3 master nodes | |

#### Firewall
- **Thông lượng:** 1 Gbps (tương đương LB)

---

## 🎯 CÁC BÀI HỌC TỪ HỒ SƠ MẪU NÀY

### 1. CHUẨN K8S: TÁCH BIỆT CONTROL-PLANE VÀ WORKER
**Golden Pattern:**
```
✅ NÊN: 
- Master-only nodes (control-plane độc lập)
- Worker-only nodes (chạy workload)
- Tách biệt tài nguyên, độ sẵn sàng cao hơn

❌ TRÁNH:
- Server vừa làm master vừa làm worker
- Không có control-plane riêng
- Có危险的 mất quorum etcd
```

**Lý do:**
- **Độ sẵn sàng:** Master down không ảnh hưởng worker running pods
- **Hiệu năng:** Master resources không bị pod "chiếm dụng"
- **Bảo mật:** Tách biệt quyền truy cập control-plane vs data-plane
- **Vận hành:** Dễ dàng upgrade, maintenance riêng biệt

### 2. SỐ LƯỢNG MASTER NODES: LUÔN LÀ SỐ LẺ
**Quy tắc vàng:**
- etcd cần quorum = majority (N/2 + 1)
- Để HA, cần tối thiểu 3 master nodes
- 1 master down → vẫn có 2 masters hoạt động → vẫn có quorum
- Vậy nên N LUÔN = 3, 5, 7, ...

**Tại sao không 2 masters?**
- 2 masters → 1 down → chỉ còn 1 → mất quorum (cần 2/3) → cả cluster down
- 3 masters → 1 down → còn 2 → vẫn có quorum (2/3) → cluster vận hành bình thường

### 3. ETCD REPLICAS: TỐI THIỂU 3 BẢN SAO
**Quy tắc:**
- etcd là "bộ nhớ" của K8s (lưu trữ cluster state)
- Một cluster K8s khỏe mạnh CẦN 3 etcd replicas
- Mỗi etcd trên master node khác nhau
- Nếu 3 master trên cùng 1 storage cluster → tất cả down cùng lúc → không đạt HA

**Giải pháp:**
- Đặt 3 master trên 3 cụm storage khác nhau
- Nếu 1 storage cluster down → 1 master down → 2 masters còn lại vẫn OK

### 4. TÍNH TOÁN BĂNG THÔNG CHO CI/CD SYSTEM
**Công thức:**
```
Băng thông hiện tại (cho 8 systems) = 80 Mbps
Băng thông cần (cho 85 systems) = 85 × 80 / 8 = 850 Mbps
Băng thông với dự phòng (Kdup = 1.2) = 850 × 1.2 = 1,020 Mbps ≈ 1 Gbps
```

**Các yếu tố cần xem xét:**
- **Image pull:** Mỗi image 500MB-2GB, pull đồng loạt nhiều nodes
- **Monitoring traffic:** Metrics collection, logs
- **Build artifacts:** Code + artifacts truyền qua LB
- **Peak hour:** 8h-16h có nhiều builds hơn
- **Disaster recovery:** Cần băng thông cao để RTO nhanh

**Traffic patterns:**
- **Normal:** 25-35 concurrent sessions
- **Peak:** 80-100 concurrent sessions
- **Mass deployment:** Up to 100 concurrent sessions
- **Throughput:** 80 Mbps cho 8 systems/month

### 5. LOAD BALANCER CHO K8S CONTROL-PLANE
**Chức năng:**
- Single entry point cho K8s API Server (port 6443)
- Cân bằng tải cho 3 master nodes
- Health check để tự động loại bỏ nodes lỗi
- Xử lý traffic lớn: image pull, metrics, NodePort services

**Cấu hình QUAN TRỌNG:**
- ✅ TCP mode (not HTTP/HTTPS)
- ✅ Không cài certificate (K8s tự quản lý TLS)
- ✅ Không bật x-forward-for (tránh IP spoofing)
- ✅ Backend pool trỏ đúng 3 master IPs

**Lưu ý:**
- Nếu dùng LB cũ (10.208.95.213): port 8085 TCP mode
- Nếu cấp LB mới: port 6443 TCP mode

### 6. SIZING MASTER NODES THEO CHUẨN K8S
**Minimum requirements (theo 1033/QĐ-CNVTQĐ):**
- CPU: 15 Cint
- RAM: 8 GB
- HDD: 100 GB (block storage)
- Chưa bao gồm OS disk (thêm 60GB cho OS nếu cần)

**Real-world consideration:**
- 15 Cint là TỐI THIỂU cho 85 systems
- Nếu scale lên 200+ systems → cần tăng CPU/RAM
- etcd I/O rất quan trọng → cần SSD/NVMe storage
- Master nodes KHÔNG chạy workload → chỉ control-plane traffic

### 7. CHIẾN LƯỢC CẤP PHÁT LINH HOẠT
**Trường hợp 1: Còn IP cùng dải 10.208.95.x**
```
✅ Tận dụng lại LB cũ: 10.208.95.213
✅ Cấp 3 master mới vào IPs còn lại trong dải
✅ chuyển 3 server cũ thành worker-only
```

**Trường hợp 2: Hết IP cùng dải hoặc masters khác dải mạng**
```
✅ Cấp phát LB mới (1 Gbps)
✅ Cấp 3 master mới (có thể khác dải)
✅ Cập nhật endpoint trong K8s configuration
```

**Lợi ích của linh hoạt:**
- Giảm chi phí nếu còn IP
- Phục vụ nhanh chóng (không đợi quy trình mới network)
- Dễ migrate từ cấu hình cũ sang mới

### 8. THỜI GIAN ĐẢM BẢO ĐỔ TẢI
**Yêu cầu:**
- P.VHKT sẽ triển khai và đổ tải trong **không quá 3 tháng** kể từ ngày cấp phát

**Ý nghĩa:**
- Tránh lãng phí tài nguyên cấp mà không dùng
- Đảm bảo tài nguyên có giá trị sử dụng thực tế
- Có timeline để tracking và escalation

### 9. QUY MÔ HỆ THỐNG DỰA TRÊN BUSINESS PLAN
**Số liệu đầu vào:**
- Hiện tại: 8 systems đang chạy CI/CD
- Mục tiêu 2025: 85 systems VTT tự VHKT
- Tăng trưởng: ~10.6× (85/8)

**Sizing calculation:**
- Scale băng thông theo tỷ lệ systems
- Cấp phát Master nodes theo chuẩn K8s (không scale theo systems)
- Master nodes chiếm fixed resource baseline
- Worker nodes scale theo workload

### 10. MSIZE UNG DỤNG CI/CD ĐANG CHẠY
**Hiện tại chạy CI/CD cho 8 systems:**
- MyBox
- MyKid
- MySign
- MyViettel
- Vacess
- Vcontract-daitra
- Vess
- Vsale

**Thông tin quan trọng:**
- OS: Ubuntu
- Program: Java, Spring, Angular
- Database: MariaDB
- Đây là reference architecture cho các hệ thống Java/Spring

---

## 🔧 KỸ THUẬT SIZING CHO KUBERNETES MASTER NODES

### CHECKLIST SIZING K8S MASTER

#### 1. Yêu cầu tối thiểu
- [ ] Số lượng: 3, 5, 7, ... (luôn số lẻ)
- [ ] CPU: Tối thiểu 15 Cint
- [ ] RAM: Tối thiểu 8 GB
- [ ] HDD: 100 GB (block storage, không phải file storage)
- [ ] etcd replicas: 3 (mỗi master một replica)

#### 2. Yêu cầu HA (High Availability)
- [ ] 3 master trên 3 storage clusters khác nhau
- [ ] Tách biệt control-plane và worker nodes
- [ ] Load balancer trước master cluster
- [ ] Health check enabled trên LB
- [ ] Không SPOF (Single Point of Failure)

#### 3. Yêu cầu mạng
- [ ] Cùng dải mạng nếu tận dụng tài nguyên cũ
- [ ] Backend port: 6443 (API server) hoặc 8085 (nếu LB cũ)
- [ ] TCP mode trên LB
- [ ] Không x-forward-for enabled
- [ ] Không certificate trên LB (K8s tựTLS)

#### 4. Storage considerations
- [ ] etcd I/O performance: Nên dùng SSD/NVMe
- [ ] etcd size: 100GB adequate cho 85 systems
- [ ] Backup etcd định kỳ (snapshots)
- [ ] Monitoring etcd metrics (wal fsync duration)

#### 5. Scaling considerations
- [ ] Master nodes không scale theo số systems (fixed baseline)
- [ ] Worker nodes scale theo workload
- [ ] Monitor controller manager, scheduler CPU/RAM
- [ ] etcd WAL size và sync duration
- [ ] API server latency, throughput

### CÁC BƯỚC TRIỂN KHAI K8S CONTROL-PLANE HA

#### Phase 1: Preparation
1. Backup toàn bộ cluster state
2. Document current architecture
3. Lấy approval cho downtime window

#### Phase 2: Deploy Master Nodes
1. Cấp phát 3 master nodes mới
2. Cài K8s components (API server, scheduler, controller-manager, etcd)
3. Config etcd cluster trên 3 nodes
4. Setup K8s control-plane trên các master mới

#### Phase 3: Configure Load Balancer
1. Tận dụng hoặc cấp LB mới
2. Config backend pool trỏ 3 master IPs
3. Enable health check
4. Test LB → master connectivity

#### Phase 4: Migrate Existing Cluster
1. Update kubelet config trên worker nodes để trỏ LB
2. Verify pods vẫn running
3. Gradually migrate workloads
4. Taint master nodes để không chạy workload

#### Phase 5: Cleanup
1. Remove master roles từ 3 servers cũ
2. Verify cluster health
3. Document new architecture
4. Update disaster recovery procedures

---

## 📈 MẪU HÌNH TÍNH TOÁN CHO K8S CI/CD

### BÀI TOÁN 1: TÍNH BĂNG THÔNG LB/FW

**Step 1: Xác định baseline**
```
Hiện tại: 8 systems
→ Băng thông đo được: 80 Mbps (average)
```

**Step 2: Extrapolation**
```
Mục tiêu: 85 systems
→ Băng thông cần = 85 × 80 / 8 = 850 Mbps
```

**Step 3: Apply buffer**
```
Vì traffic CI/CD có tính burst:
→ Kdup = 1.2 (20% buffer)
→ Total bandwidth = 850 × 1.2 = 1,020 Mbps ≈ 1 Gbps
```

**Step 4: Consider additional factors**
- Image pull overhead: ~20-30% TCP/TLS overhead
- Monitoring traffic: Prometheus, Grafana, Loki
- Build artifacts: Maven/Gradle dependencies, Docker images
- Disaster recovery: Need spike bandwidth for RTO

### BÀI TOÁN 2: TÍNH SỐ LƯỢNG MASTER NODES

**Hiểu về etcd quorum:**
- etcd dùng Raft consensus algorithm
- Quorum = majority of nodes = (N/2) + 1
- Ví dụ: 3 nodes → quorum = 2, 5 nodes → quorum = 3

**Tại sao minimum 3 masters?**
- 1 master: No HA (single point of failure)
- 2 masters: 1 down → mất quorum (cần 2/3) → cluster down
- 3 masters: 1 down → vẫn 2 masters → có quorum → cluster OK
- 5 masters: 2 down → vẫn 3 masters → có quorum (tốn kém hơn)

**Trade-off:**
- 3 masters: Cost-effective, đủ HA cho medium clusters
- 5 masters: HA cao hơn, nhưng cost hơn, operations phức tạp hơn
- 7+ masters: Chỉ dùng cho very large clusters (thousands of nodes)

### BÀI TOÁN 3: TÍNH MASTER NODE RESOURCES

**Reference: K8s checklist từ 1033/QĐ-CNVTQĐ**
```
Minimum per master:
- CPU: 15 Cint
- RAM: 8 GB
- Storage: 100 GB (block storage)
```

**Real-world sizing:**
```
Factors to consider:
- Số systems: 85 (medium cluster)
- Concurrent builds: 80-100 peak
- Deployments per day: ~100-200
- Pods per namespace: ~50-100 average

Recommendation:
- 15 Cint adequate cho 85 systems
- Nếu scale lên 200+ systems → consider 30 Cint
- RAM 8GB adequate for Kubernetes overhead
```

**Etcd specific:**
```
Etcd là I/O intensive:
- Thường xuyên write: leader elected, heartbeats
- Monitor WAL fsync duration
- Nếu > 100ms → cần storage nhanh hơn
```

---

## 🎯 ĐIỂM CHÌA KHÓA

1. **Tách biệt control-plane và worker:** Best practice cho K8s production clusters
2. **Quorum etcd:** Hiểu rõ tại sao cần 3, 5, 7 masters (số lẻ)
3. **HA across storage clusters:** Masters trên 3 storage khác nhau → thực sự HA
4. **Băng thông tính toán thực tế:** 80 Mbps measured → 1 Gbps với buffer
5. **Load balancer config:** TCP mode, không certificate, x-forward-for off
6. **Sizing dựa trên checklist K8S:** Tuân thủ 1033/QĐ-CNVTQĐ
7. **Chiến lược cấp phát linh hoạt:** Tận dụng hoặc mới tùy tình trạng IP/mạng
8. **Timeline đổ tải:** 3 tháng để tài nguyên có giá trị sử dụng
9. **Business-driven sizing:** 85 systems từ kế hoạch 7393/KH-CNTT
10. **Reference architecture:** 8 systems Java/Spring hiện tại là baseline

---

## 📚 CÁC TÀI LIỆU THAM KHẢO

- **Quy định:** 1033/QĐ-CNVTQĐ - Quy định bàn giao hệ thống từ SC sang VHKT
- **Checklist K8S:** BM01_Checklist_yeu_cau_ha_tang_cai_dat_K8s.xlsx
- **CTKT K8s:** PL20_Mau_bieu_CTKT_Kubernetes_Platform.xlsx
- **Best Practice:** https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ha-etcd/

---

**Người tạo tài liệu:** AI Assistant (dựa trên tài liệu sizing Jenkins CI/CD)  
**Ngày tạo:** 2024  
**Phiên bản:** 1.0  
**Trạng thái:** ✅ Hoàn thành - Hồ sơ mẫu (Golden Pattern) cho sizing K8s Master nodes

---

## 📝 GHI CHÚ

- Tài liệu này trích xuất tri thức từ hồ sizing đã ký duyệt (không có PNX)
- Đây là một hồ sơ MẪU để tham khảo cho các dự án K8s tương tự
- Đặc biệt hữu ích cho: việc tách biệt control-plane, sizing etcd cluster, tính băng thông CI/CD
- Cần tuân thủ guideline sizing của Viettel (xem trong thư mục guideline_sizing/)
- File sizing gốc: Sizing_VHKT 2025_Jenkins_Bổ sung (1).pdf trong thư mục sr/