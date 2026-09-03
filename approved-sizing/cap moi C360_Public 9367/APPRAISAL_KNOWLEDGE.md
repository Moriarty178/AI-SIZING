# C360 PUBLIC WEB APP (REPORT)

**Mã PYC:** PYC-9367  
**Đầu mối yêu cầu:** Sonln3 (Trung tâm DAC - PTPM)  
**Đầu mối thẩm định:** Haipn (Phòng Hệ thống)  
**Mục đích sizing:** Xin LB Public Internet 2 nodes cho C360 Public  
**Hệ thống:** Customer 360 - Public Web App (Report)  
**Trạng thái:** 1 PNX - TRƯỜNG HỢP A

---

## THÔNG SỐ KỸ THUẬT CHỐT

### C360 PUBLIC WEB APP (DATA PROCESS + WEB)

| Thông số | Giá trị | Ghi chú |
|----------|---------|---------|
| **CPU** | >= 10.24 Cint 2017 | Per node |
| **RAM** | >= 44 GB | Per node |
| **HDD** | >= 501.87 GB | Per node |
| **Số lượng** | 2 nodes | Xin LB Public Internet |
| **HA Mode** | Load Balancer | Public Internet access |

---

## BÀI HỌC QUAN TRỌNG

1. **Public Internet access:** Cần LB Public Internet cho external users
2. **HDD 501.87 GB:** Cụ thể số lẻ → từ sizing calculation (không round lên)
3. **CPU 10.24 Cint:** Cụ thể số lẻ → từ sizing calculation (không round lên)
4. **RAM 44 GB:** Giống sizing #9 (c360 internal) - cùng hệ thống C360
5. **2 nodes cho LB:** Load balancer redundancy cho high availability

---
**Trạng thái:** ✅ Hoàn thành - TRƯỜNG HỢP A (1 PNX) - **THƯ MỤC CUỐI CÙNG!**