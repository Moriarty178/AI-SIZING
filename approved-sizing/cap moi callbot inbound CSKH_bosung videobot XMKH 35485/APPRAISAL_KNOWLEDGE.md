# APPRAISAL KNOWLEDGE - CALLBOT INBOUND CSKH + VIDEOBOT

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** TRỢ LÝ ẢO CALLBOT INBOUND CSKH – BỔ SUNNG NGHIỆP VỤ VIDEOBOT XÁC MINH KH  
**Mã PYC:** PYC-29293  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - NHIỀU VÒNG (TRƯỜNG HỢP A)  
**Số vòng PNX:** 3 vòng (v1.1 → v1.1v2 → v1.1v3 → v1.2v4)  
**Đầu mối:** Kientt6  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23 (Phòng Hệ thống)

#### 11 Yêu cầu chỉnh sửa:

**NHÓM 1: SOỞ CỨ VÀ TÍNH TOÁN**

1. **Bổ sung sở cứ:** Thiếu cơ sở chứng minh cho các số liệu dùng trong sizing

2. **Mục đích sizing:** Cần ghi rõ lý do tại sao cần sizing (cấp mới, bổ sung, thay đổi kiến trúc)

3. **Thông tin đầu vào (Trang 1):**
   - Cần bổ sung sở cứ cho các con số đầu vào
   - Làm rõ nguồn dữ liệu (log hệ thống, ước tính, benchmark?)

**NHÓM 2: TÍNH TOÁN CCU VÀ SERVER**

4. **Trang 4 - Server test và tính toán CCU:**
   - Bổ sung sở cứ cho "Thông tin server chạy thử"
   - Bổ sung sở cứ cho tải khi test 15 CCU
   - Làm rõ tính toán: 120 CCU cần 120/15 = 8 server
   - Tính toán lại số liệu và lập bảng giá trị

**NHÓM 3: GPU VÀ TEST TẢI**

5. **Trang 5 - Cấu hình test và GPU:**
   - Bổ sung sở cứ cho cấu hình khi test tải
   - Bổ sung sở cứ cho: "1 server với 8 card GPU đáp ứng tối đa 16 CCU"
   - Tính toán lại, lập bảng giá trị

**NHÓM 4: LƯU TRỮ VÀ STORAGE**

6. **Trang 6 - Dung lượng lưu trữ:**
   - Bổ sung sở cứ: 1200 cuộc gọi/ngày = 8.64 GB
   - Bổ sung sở cứ: thử nghiệm 1200 cuộc gọi = 5.42 GB
   - Bổ sung sở cứ: dung lượng 1 file ~ 2MB
   - Với 50.000 cuộc gọi/ngày videobot: tính toán lại
   - Tính toán lại số liệu, lập bảng giá trị

7. **SSD Storage:**
   - Bổ sung sở cứ tại sao dùng SSD thay vì HDD

**NHÓM 5: KẾT NỐI HỆ THỐNG**

8. **Kết nối các hệ thống:**
   - Bổ sung danh sách hệ thống cần kết nối
   - Bổ sơ scheme mạng vật lý

9. **Cấp phát tài nguyên mạng:**
   - Làm rõ: Cấp phát hay bổ sung?
   - Cần cùng dải IP để共用 LB không hay cấp ở đâu cũng được?
   - Tài nguyên này đã có trong QHĐC chưa?

10. **Firewall và Load Balancer:**
    - Tính thông lượng FW, LB dựa trên lưu lượng thực tế

**NHÓM 6: BẢNG TỔNG HỢP**

11. **Bảng đề xuất cấu hình:**
    - Bổ sung đầy đủ thông tin cấu hình xin cấp phát
    - Bổ sung thông tin FW, LB

---

## 💡 TRI THỨC RÚT RA

### 1. Định cỡ hệ thống AI/ML với GPU

**Yêu cầu đặc biệt:** Hệ thống Callbot + Videobot cần GPU để xử lý AI

**Mô hình sizing:**
- 1 server với 8 GPU cards = tối đa 16 CCU
- Mỗi GPU card hỗ trợ ~2 CCU
- Nhu cầu 120 CCU → cần 8 server (N+1 backup)

**Công thức:**
```
Servers_needed = Target_CCU / Max_CCU_per_server
Servers_needed = 120 / 16 = 7.5 ≈ 8 servers
```

**Lưu ý quan trọng:**
- Cần có thử nghiệm thực tế để xác định 1 GPU hỗ trợ bao nhiêu CCU
- Không được ước tính mà không có test benchmark

### 2. Tính toán dung lượng storage cho Video/Audio

**Yêu cầu:** Lưu trữ file audio/video callbot và videobot

**Phương pháp:**
1. Thử nghiệm với số lượng cuộc gọi nhỏ (1200 calls)
2. Đo dung lượng thực tế (5.42 GB)
3. Nội suy cho nhu cầu lớn (50.000 calls)

**Công thức:**
```
Storage_per_call = Measured_Storage / Test_Calls
Storage_per_call = 5.42 GB / 1200 = 4.52 MB/call

Total_Storage = Storage_per_call × Target_Calls × Retention_Days
```

**Lưu ý:**
- Cần phân biệt giữa ước tính (8.64 GB) và thực tế đo (5.42 GB)
- Dùng số liệu thực tế để tính toán chính xác hơn

### 3. Bảng giá trị định cỡ (Table-based sizing)

**Yêu cầu thẩm định:** Phải lập bảng tính toán chi tiết

**Cấu trúc bảng:**
| N | Cint per server | RAM per server | HDD per server | Ghi chú |
|---|---|---|---|---|
| 1 | 134.4 | 192 GB | 3 TB | Too large |
| 2 | 67.2 | 96 GB | 1.5 TB | Selected |
| 3 | 44.8 | 64 GB | 1 TB | Backup |

**Lợi ích:**
- Dễ so sánh các scenario
- Dễ đánh giá trade-off
- Dễ giải thích với thẩm định viên

### 4. SoỞ cứ cho mọi con số

**Nguyên tắc vàng:** Mọi số liệu trong sizing都必须 có nguồn

**Các loại sở cứ cần thiết:**

1. **Số liệu test:** 
   - Ảnh chụp màn hình monitoring
   - Log CPU, RAM, Storage
   - File cấu hình test

2. **Số liệu hệ thống hiện tại:**
   - Log production
   - Database query
   - Monitoring graph

3. **Số liệu benchmark từ vendor:**
   - Specs GPU card
   - Performance specs
   - Vendor whitepaper

4. **Số liệu tính toán:**
   - Công thức dùng
   - Refer guideline nào
   - Link tham khảo

### 5. SSD vs HDD cho AI workloads

**Yêu cầu thẩm định:** Tại sao dùng SSD?

**Lý do dùng SSD cho AI/ML:**
- **IOPS cao:** GPU cần đọc/write data rất nhanh
- **Latency thấp:** AI model loading cần tốc độ cao
- **Random access tốt:** Training/Inference cần access ngẫu nhiên
- **Throughput ổn định:** Không bottleneck ở disk I/O

**So sánh:**
- HDD: ~100 IOPS, latency ~10ms
- SSD: ~100.000 IOPS, latency <1ms

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt - v1.2v4)

**Máy chủ APP/Video (8 servers - Active + Backup):**
- CPU: dựa trên bài toán CCU
- RAM: dựa trên bài toán GPU
- GPU: 8 cards/server
- Storage: SSD cho performance

**Storage:**
- Dung lượng: dựa trên 50.000 calls/day × retention days
- Loại: SSD
- Backup: theo policy

**Network:**
- Firewall: Based on throughput calculation
- Load Balancer: Based on CCU and connection count
- IP range: cần làm rõ trong QHĐC

### Quy mô hệ thống
- Callbot Inbound CSKH
- Videobot xác minh khách hàng
- Nhu cầu: 120 CCU
- Peak: Thử nghiệm với 15 CCU để extrapolate

---

## ⚠️ BÀI HỌC KINH NGHIỆM

### 1. NEVER ước tính mà không có test benchmark
- **Sai lầm:** 1 server = 16 CCU (chưa test?)
- **Đúng:** Test với 15 CCU trước, rồi extrapolate lên 120 CCU

### 2. Mọi số liệu đều phải có "sở cứ"
- Không được viết "1200 cuộc gọi = 8.64 GB" mà không có minh chứng
- Cần chụp màn hình, file log, calculation sheet

### 3. Bảng tính toán giúp giải thích rõ hơn
- Thay vì viết một dãy số
- Hãy làm bảng với N=1,2,3,4,... để người đọc dễ hiểu

### 4. Storage tính toán khác ước tính
- Uớc tính lý thuyết: 5.42 GB
- Thực tế đo được: có thể khác
- Dùng số liệu thực tế (thử nghiệm)

### 5. GPU sizing
- Cần test để biết 1 GPU support bao nhiêu CCU
- Không thể假定 mỗi GPU card = fixed CCU
- Phụ thuộc vào model size, complexity

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** CAO  
**Số vòng PNX:** 3+  
**Vấn đề chính:** Thiếu sở cứ cho mọi số liệu, chưa test benchmark cho GPU

**Đặc điểm hệ thống:**
- Hệ thống AI/ML với GPU
- Có videobot cần lưu trữ file
- Phụ thuộc vào performance GPU

**Khuyến nghị:**
- Luôn test benchmark trước khi sizing GPU
- Mọi số liệu đều phải có minh chứng (screenshot, log)
- Làm bảng tính toán chi tiết
- Làm rõ storage calculation (test vs estimate)
- Bổ sung схем mạng, kết nối hệ thống
- Làm rõ IP allocation, QHĐC