# APPRAISAL KNOWLEDGE - STRONGSWAN VPN

## 📋 THÔNG TIN HỆ THỐNG

**Dự án:** STRONGSWAN (IPsec VPN)  
**Mã PYC:** PYC-40325  
**Trạng thái hồ sơ:** CÓ PHẢN BIỆN - 1 VÒNG (TRƯỜNG HỢP A)  
**Mục đích:** Đáp ứng yêu cầu triển khai của C06  
**Đầu mối:** lamtn6  

---

## 🔍 LƯU Ý THẨM ĐỊNH

### Phiếu nhận xét lần 1

**Thẩm định viên:** Khanhnd23

**Yêu cầu chính:**
1. **Throughput alignment:** Đề xuất phải khớp với số liệu tính toán
2. **Notation:** dùng `=` thay vì `>=` (chính xác hơn)
3. **Storage:** Cần bổ sung sởffff chỉ, tính toán lại dung lượng lưu trữ
4. **Table format:** Lập bảng giá trị với N+1 redundancy

---

## 💡 TRI THỨC RÚT RA

### 1. StrongSwan VPN architecture

**What is StrongSwan:**
```
StrongSwan = IPsec-based VPN solution

Key components:
  - IKE daemon (Internet Key Exchange)
  - IPsec kernel module
  - Configuration files
  - Certificate management

Typical deployment:
  - Site-to-site VPN (gateway to gateway)
  - Remote access VPN (client to gateway)
  - High availability with VRRP/Corosync
```

### 2. VPN throughput sizing

**Network bandwidth consideration:**
```
Throughput calculation:
  - Encryption overhead: ~20-30% reduction
  - CPU-bound: AES-NI acceleration helps
  - Packet size: Smaller packets = more overhead

Example:
  Raw link: 1 Gbps
  Encrypted throughput: ~700-800 Mbps
  Proposal should reflect actual encrypted rate, not raw link speed
```

### 3. Storage requirements for VPN

**VPN logs and certificates:**
```
Storage needs:
  - Certificate files: ~1-5 MB
  - Configuration: ~1-2 MB
  - Connection logs: Variable
  - IKE/ESP logs: Variable

Default approach:
  - Minimal storage (logs rotate frequently)
  - Focus on network throughput, not disk I/O
```

### 4. N+1 for VPN gateways

**High availability requirement:**
```
VPN gateway HA:
  - Active + Standby configuration
  - VRRP for failover
  - Synchronized state (if supported)
  
N+1 means:
  - If need 2 gateways, request 3
  - Allows one gateway maintenance without downtime
  - Critical infrastructure requirement
```

---

## 📊 THÔNG SỐ KỨ THUẬT

### System type
- IPsec VPN deployment
- Site-to-site or remote access
- Part of C06 infrastructure requirements

### Sizing focus
- Network throughput (primary metric)
- CPU for encryption (AES-NI recommended)
- Minimal storage (logs + certificates)
- N+1 redundancy for HA

---

## ⚠️ BÀI HỌC KINH NGHIỆM

1. **Throughput must match reality**
   - Don't propose raw link speed
   - Account for encryption overhead
   - Use actual encrypted throughput in sizing

2. **Use `=` not `>=`**
   - More precise to state exact requirement
   - `>=` suggests uncertainty in calculation

3. **VPN storage is minimal**
   - Don't over-provision disk
   - Logs rotate quickly (security best practice)
   - Certificates are small files

4. **N+1 essential for VPN**
   - VPN is network infrastructure
   - Downtime breaks connectivity
   - HA standard practice for gateways

---

## 📌 NHẬN XẾT CHUNG

**Mức độ phức tạp:** THẤP  
**Số vòng PNX:** 1 (minor issues)  
**Vấn đề chính:** Throughput accuracy, notation, storage justification

**Đặc điểm:**
- IPsec VPN solution (StrongSwan)
- Part of C06 infrastructure
- Network-focused sizing (not CPU/storage intensive)

**Khuyến nghị:**
- Focus on encrypted throughput calculation
- Use AES-NI CPU for better performance
- Minimal storage sufficient
- Always include N+1 for HA