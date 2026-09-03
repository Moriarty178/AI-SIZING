# APPRAISAL KNOWLEDGE - CALLBASE

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** CALLBASE - Hệ thống lấy tín hiệu cuộc gọi qua Kafka  
**Mã PYC:** PYC-44087  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN (TRƯỜNG HỢP A)  
**Đầu mối:** Phòng PTPM – Trung tâm VAS  

---

## 🔍 LƯU Ý THẨM ĐỊNH (PNX)

### Phiếu nhận xét lần 1

**Thẩm định viên:** khanhnd23 (Phòng Hệ thống)

#### Các điểm cần chỉnh sửa:

1. **Sở chứ định cỡ:** Cần cập nhật lại sở cứ để làm rõ cơ sở tính toán

2. **Cấu hình server testbed (Trang 4):**
   - Lỗi: Đang để Cint_rate = 39 (sai)
   - Đúng: Cần cập nhật đúng giá trị Cint 2017 = 115.75
   - **Nguyên nhân lỗi:** Tính toán lỗi khi chuyển đổi từ Cint2006
   
3. **Thông lượng Firewall:**
   - Lỗi: Đang ghi ">= 2.44 Gbps"
   - Sửa: Chỉ ghi "= 2.44 Gbps" (không dùng dấu >=)

4. **Hình ảnh sở cứ:**
   - Cần cập nhật ảnh chụp màn hình ngay tại vị trí giá trị cần làm rõ
   - Đừng để ảnh sở cứ ở cuối tài liệu

5. **Thông số RAM:**
   - Cần làm rõ nội dung "RAM DDR4"
   - Nếu không thực sự cần thiết thì bỏ đi

---

## 💡 TRI THỨC RÚT RA

### 1. Phương pháp định cỡ dựa trên Testbed

**Tình huống:** Hệ thống nghiệp vụ mới, không có dữ liệu lịch sử  
**Giải pháp:** Định cỡ dựa trên tải thực tế của hệ thống testbed

- **Công thức:**
  ```
  CPU_per_TPS = CPU_used_testbed / TPS_testbed
  RAM_per_TPS = RAM_used_testbed / TPS_testbed
  
  Total_CPU = CPU_per_TPS × Target_TPS × Safety_Factor / KPI
  Total_RAM = RAM_per_TPS × Target_TPS × Safety_Factor / KPI
  ```

- **Dữ liệu testbed:**
  - Testbed TPS: 40.000
  - CPU used (p95): 11.466 Cint
  - RAM used (p95): 15.712 GB
  - HDD daily: 0.65 GB

- **Mở rộng lên 400.000 TPS:**
  - CPU cần: 168 Cint (sau khi chia cho N=4 server → 42 Cint/server)
  - RAM cần: 192 GB (sau khi chia N=4 → 48 GB/server + 4GB OS = 52 GB)
  - HDD cần: 800 GB (sau khi chia N=4 → 200 GB/server + 60GB OS)

### 2. Chuyển đổi Cint2006 → Cint2017

**Lỗi thường gặp:** Tính toán sai khi chuyển đổi giữa 2 chuẩn CPU

**Công thức đúng:**
```
Cint2017 = Cint2006 / 8.38
```

**Ví dụ đúng:**
- CPU Intel Xeon E5-2670 v3: Cint2006 = 970
- Cint2017 = 970 / 8.38 = 115.75
- Với 16 vCPU: 16 × (115.75/48) = 38.6 ≈ 39 Cint

**Lưu ý:** Cần phải tính Cint cho từng vCPU, không dùng trực tiếp số total

### 3. Định cỡ Firewall cho hệ thống lấy tín hiệu

**Yêu cầu:** Tính toán thông lượng dựa trên card mạng thực tế

**Phương pháp:**
1. Xác định các card mạng truyền tải dữ liệu nghiệp vụ
2. Loại bỏ card DCN, card mirror
3. Tổng hợp lưu lượng qua các card còn lại
4. Đổi sang đơn vị Gbps

**Công thức:**
```
Throughput_Gbps = Total_KBps × 8 / 1024 / 1024
```

**CASE STUDY - CALLBASE:**
- Card em3 (OCS signal): 198465 KBps
- Card em4 (OCS signal): 120058 KBps
- Tổng: 319292 KBps
- Throughput: 319292 × 8 / 1024 / 1024 = 2.44 Gbps

### 4. KPI và Hệ số an toàn

**KPI áp dụng:**
- CPU: 75% (không quá)
- RAM: 90%
- HDD: 80%
- Hệ số dự phòng sai số: 1.1

**Tính toán:**
```
Resource_needed = Calculated_Value × 1.1 / KPI
```

---

## 📊 THÔNG SỐ KỸ THUẬT

### Cấu hình đề xuất (Đã duyệt)

**Máy chủ APP (5 server - N+1 backup):**
- CPU: 47 Cint 2017 (~2 vCPU vật lý)
- RAM: 52 GB DDR4
- HDD: 200 GB data + 60 GB OS

**Firewall:**
- Throughput: = 2.44 Gbps

### Quy mô hệ thống
- Nguồn tín hiệu: Kafka OCS
- Tải CK: 400.000 TPS
- Thời gian lưu log: 90 ngày
- Kết nối đến: Nagios, Airtime, TTOL, MappingGW

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Kiểm tra kỹ công thức chuyển đổi đơn vị:** Đặc biệt là Cint2006→Cint2017
 
2. **Tránh dùng phép so sánh không cần thiết:** Firewall throughput ghi số chính xác, không dùng ">="
 
3. **Hình ảnh minh chứng:** Cần chèn ngay tại vị trí số liệu, không để cuối tài liệu
 
4. **Testbed sizing:**
   - Cần có log p95 từ testbed
   - Đo tải tất cả các tài nguyên (CPU, RAM, HDD, Network)
   - Phải có ảnh chụp màn hình minh chứng

---

## 📌 NHẬN XÉT CHUNG

**Mức độ phức tạp:** Trung bình  
**Số vòng PNX:** 1  
**Vấn đề chính:** Lỗi tính toán đơn vị, thiếu minh chứng bằng hình ảnh, cú pháp không chuẩn xác

**Khuyến nghị:**
- Khi chuyển đổi đơn vị CPU, cần kiểm tra lại công thức
- Cần chèn hình ảnh minh chứng ngay tại vị trí số liệu
- Tránh dùng ký hiệu so sánh (>=, <=) khi không cần thiết
- Testbed sizing phải đầy đủ log p95, hình ảnh monitoring





