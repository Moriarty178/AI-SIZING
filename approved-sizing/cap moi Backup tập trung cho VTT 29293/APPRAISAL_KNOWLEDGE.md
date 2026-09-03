# BACKUP TẬP TRUNG - HỆ THỐNG SAO LƯU 100 HỆ THỐNG

**Mã PYC:** PYC-29293  
**Trạng thái:** 5 vòng PNX (v1→v2→v3→v4→v5) - TRƯỜNG HỢP A  
**Mục đích:** Backup tập trung cho 100 hệ thống VHKT (42 systems đang backup trong 14 tháng đầu)  
**Đơn vị:** P.VHKT – TT CNTT (HungNH56), thẩm định: P.Hệ thống (KhanhND23)

---

## THÔNG SỐ KỸ THUẬT CHỐT

### BACKUP SERVERS (2 SERVERS - ACTIVE-ACTIVE/ACTIVE-STANDBY)
| Thông số | Giá trị |
|----------|---------|
| CPU | >= 38 Cint (SPEC Cint 2017) |
| RAM | >= 35 GB |
| OS | CentOS 9 Stream |
| Storage | 40 TB SAN |
| IOPS | 1,452,000 IOPS |
| HA Mode | Active-Active hoặc Active-Standby |

### FIREWALL
| Thông số | Giá trị |
|----------|---------|
| Throughput | >= 3.28 Gbps |
| Calculation | 550 Mbps cho 42 systems/14 days → Extrapolate 100 systems/month dengan Kdup 1.2 |

---

## BÀI HỌC QUAN TRỌNG

1. IOPS scaling: 13,200 IOPS per system × 100 systems = 1,320,000 IOPS
2. Bandwidth calculation: Extrapolate from 42 systems (14 days) → 100 systems (30 days)
3. SAN storage: 40 TB cho 100 systems ≈ 400 GB/system (reasonable)
4. Data node KPI: ≤ 50% applied (backup system special consideration)

---
**Trạng thái:** ✅ Hoàn thành - TRƯỜNG HỢP A (5 vòng PNX)