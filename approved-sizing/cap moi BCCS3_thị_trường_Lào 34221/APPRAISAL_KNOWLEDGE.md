# BCCS 3.0 THỊ TRƯỜNG MỚI (LÀO)

**Mã PYC:** (không thấy mã cụ thể)  
**Trạng thái:** 1 PNX - TRƯỜNG HỢP A  
**Mục đích:** Triển khai BCCS3.0 cho thị trường mới (Lào) giống thị trường Lào  
**Đơn vị:** K.CNTT - VTT, DVSD: AnTV124, thẩm định: P.HT (VinhTQ18)

---

## THÔNG SỐ KỸ THUẬT CHỐT

### SERVER CONFIGURATIONS

| Phân hệ | CPU | RAM | HDD | Số lượng |
|---------|-----|-----|-----|----------|
| **Module vệ tinh + Monitor** | 20 Cint | 120 GB | 3 TB | 2 |
| **Oracle GoldenGate + Downstream** | 20 Cint | 256 GB | 0.5 TB | 2 |
| **Kafka (5 clusters × 2)** | 6 Cint | 8 GB | 0.2 TB | 10 |
| **DBIN + FTP** | 16 Cint | 16 GB | 1 TB | 2 |
| **Firewall** | - | - | >= 1 Gbps | 1 |

**Tổng:**
- CPU: ~218 C tổng (20×2 + 20×2 + 6×10 + 16×2)
- RAM: ~528 GB tổng (120×2 + 256×2 + 8×10 + 16×2)
- Storage: ~13 TB tổng (3×2 + 0.5×2 + 0.2×10 + 1×2)

---

## BÀI HỌC QUAN TRỌNG

1. **GoldenGate cần RAM lớn:** 256 GB cho replication/capture/apply
2. **Kafka cluster:** 10 servers (5 clusters × 2 replicas each) cho HA
3. **Module vé sinh:** 120 GB RAM (monitoring intensive)
4. **Thị trường mới = Sản xuất hiện tại:** Sizing giống hệ thống Lào đang chạy

---
**Trạng thái:** ✅ Hoàn thành - TRƯỜNG HỢP A (1 PNX)