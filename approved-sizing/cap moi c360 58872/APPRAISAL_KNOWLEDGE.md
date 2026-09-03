# C360 MARIADB - BỔ SUNG RAM (176 GB)

**Mã PYC:** PYC-58872  
**Đầu mối yêu cầu:** Sonln3 (Trung tâm DAC - PTPM)  
**Đầu mối thẩm định:** Haipn (Phòng Hệ thống)  
**Mục đích sizing:** Bổ sung RAM và CPU cho cụm server database MariaDB C360 hiện tại (10.207.62.120-122)  
**Hệ thống:** Customer 360 (kho dữ liệu khách hàng tập trung)  
**Trạng thái:** Có PNX + usage_benchmark.zip (tài liệu benchmark) - TRƯỜNG HỢP A

---

## THÔNG SỐ KỸ THUẬT CHỐT

### DATABASE MARIADB C360 (BỔ SUNG TÀI NGUYÊN)

| Thông số | Giá trị mới | Ghi chú |
|----------|-------------|---------|
| **CPU** | >= 143 Cint 2017 | Bổ sung cho 3 servers DB hiện tại |
| **RAM** | >= 176 GB | Bổ sung cho 3 servers DB hiện tại |
| **Servers** | 3 nodes (10.207.62.120-122) | Hệ thống hiện tại |
| **Hệ điều hành** | MariaDB | (Không specific version) |

---

## BÀI HỌC QUAN TRỌNG

1. **Bổ sung RAM cho hệ thống sản xuất:** 176 GB là rất cao → cache lớn cho queries
2. **Sizing dựa trên benchmark:** File usage_benchmark.zip cung cấp bằng chứng thực tế
3. **Hệ thống C360 data warehouse:** Khá lớn - kho dữ liệu khách hàng tập trung
4. **Database nodes: 3 servers (10.207.62.120-122)** - Có thể là Active-Active or Master-Slave
5. **Dữ liệu tăng trưởng 20%/năm** - Cần plan cho scaling tiếp theo

---
**Trạng thái:** ✅ Hoàn thành - TRƯỜNG HỢP A (có PNX + benchmark data)