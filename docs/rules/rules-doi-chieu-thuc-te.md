# Đối chiếu 150 quy tắc với hành vi thẩm định thật

> Sinh bằng `scripts/map_appraisal_to_rules.py`. Chi tiết ánh xạ:
> [`appraisal-mapping.md`](appraisal-mapping.md). Dữ liệu thô:
> `.tmp-appraisal/issues.md`.

> ⚠️ **Nguồn là tóm tắt do một AI khác (Cline) viết lại từ hồ sơ đã ký, KHÔNG
> phải nguyên văn Phiếu Nhận Xét.** Bản gốc `.docx`/`.pdf` không còn (xác nhận
> 2026-08-26). Dùng để **soi lại bộ quy tắc**; KHÔNG dùng làm nhãn chấm điểm —
> làm vậy sẽ cho recall ảo và vi phạm NT2.

## Vì sao cần việc này

Toàn bộ 150 quy tắc suy ra từ **văn bản** — Guideline, checklist thẩm định,
code web app. Chưa lần nào đối chiếu với **hành vi**: người thẩm định thật sự
bắt gì. Kho `approved-sizing/` cho 667 vấn đề trên 50 hồ sơ đã ký,
là dịp duy nhất đang có để kiểm điều đó.

## Số liệu

- **50 hồ sơ** · 38 có phản biện (PNX) · 8 duyệt thẳng
- **667 vấn đề** trích được · 512 lượt khớp chủ đề **ở tiêu đề**
  (khớp trong đoạn ngữ cảnh: 810 lượt — dò nhưng KHÔNG tính, xem lý do
  ở `appraisal-mapping.md`)
- **75/150 quy tắc** có ít nhất một vấn đề thực tế khớp
- **9 khoảng trống** — chủ đề bị bắt mà không quy tắc nào phủ
- Số vòng phản hồi trung bình **1.92** (38 hồ sơ ghi rõ, phân bố {1: 21, 2: 8, 3: 5, 4: 1, 5: 1, 6: 2})

---

## 1. Khoảng trống — kết quả quan trọng nhất

Người thẩm định bắt những thứ này, `rules.yaml` không có quy tắc nào phủ.

| Chủ đề | Số lần | Hồ sơ | Vì sao chưa phủ |
|---|---:|---:|---|
| **Nhất quán chu kỳ lưu trữ giữa các phân vùng** | 31 | 13 | Ca thật: App 6 tháng · /data 2 năm · /log 6 tháng · /backup 4 ngày, không giải thích vì sao khác nhau. Không quy tắc nào bắt được sự không nhất quán này. ALC-01 chỉ kiểm mốc 06 tháng của cấp phát. |
| **Kiểm tính hợp lý đơn vị số liệu đầu vào** | 14 | 9 | Ca thật: khai "3.000.000 TB cho 1.080 người dùng" = 2,7 PB mỗi người. Đây là phép kiểm rẻ và bắt được lỗi nặng, thuần code làm được, nhưng không quy tắc nào có. |
| **Định cỡ GPU / tải AI** | 11 | 4 | Đã biết trước: Guideline lần 07 không có nội dung GPU nào (PLAN.md mục 0.12f). Nay có bằng chứng là thực tế CÓ phát sinh. |
| **Sở cứ cho tốc độ tăng trưởng dữ liệu** | 10 | 6 | PNX hỏi thẳng "sở cứ cho mức tăng trưởng 20%/năm là gì?", đòi log history hoặc trend analysis. Guideline không có quy tắc nào về tốc độ tăng trưởng. KPI-16 (tăng trưởng 01 năm) đang `enabled: false`. |
| **Làm tròn và độ chính xác số trung gian** | 8 | 4 | PNX xếp lỗi làm tròn số trung gian là CRITICAL. `globals.lam_tron` mới là quy ước làm tròn kết quả cuối, chưa thành quy tắc kiểm. |
| **Phải trình bày công thức, không chỉ kết quả** | 6 | 5 | PNX đòi bảng tính trung gian để lần được từ đầu vào tới kết quả. EVD-09 chỉ yêu cầu mọi con số truy được nguồn, không yêu cầu hiện phép tính. |
| **Sizing phần mềm bên thứ ba / vendor** | 5 | 2 | PNX chấp nhận email hãng xác nhận làm sở cứ khi phần mềm do vendor cung cấp. Guideline không nói gì về trường hợp này. |
| **Cấp bổ sung phải tính phần TĂNG THÊM** | 3 | 2 | PNX bắt lỗi khai TỔNG tài nguyên trong khi hồ sơ là cấp BỔ SUNG — phải khai phần tăng thêm. CL-2.1 chỉ hỏi "mới hay bổ sung", không ràng buộc cách khai con số. |
| **Sizing ứng cứu khẩn cấp** | 3 | 1 | Có luồng riêng (VTNet UCTT) với hệ số dự phòng khác. Bốn dạng định cỡ MTH-01..04 không có dạng này. |

> **Không tự thêm quy tắc nào từ bảng này.** Thêm quy tắc là mở lại
> 0.1–0.4 và phải có người duyệt. Bộ 150 quy tắc giữ nguyên cho tới lúc đó.

---

## 2. Quy tắc được thực tế xác nhận

Xếp theo số lần vấn đề thực tế khớp. Đây là phần đáng tin nhất của bộ quy tắc —
có căn cứ văn bản **và** có bằng chứng người thẩm định thật sự soi.

| Quy tắc | Tên | Số lần | Hồ sơ | Mức hiện tại |
|---|---|---:|---:|:--:|
| `ARC-09` | Mức dự phòng N+M; M mặc định bằng 1 | 64 | 28 | major |
| `FWL-04` | Hệ thống có đường ra internet/public phải định cỡ fi | 61 | 28 | critical |
| `PRC-01` | Thông số đầu vào phải được lãnh đạo xác nhận bằng vă | 54 | 25 | major |
| `PRC-02` | Biên bản kiểm thử hiệu năng phải được xác nhận bằng  | 54 | 25 | major |
| `EVD-03` | Thông số chọn để định cỡ phải ảnh hưởng tới năng lực | 50 | 24 | minor |
| `EVD-09` | Phải nêu các yếu tố ảnh hưởng thông số tài nguyên má | 50 | 24 | major |
| `KPI-06` | Thiết bị lưu trữ: dung lượng sử dụng không vượt quá  | 46 | 24 | critical |
| `STO-04` | Dung lượng thô = tổng cần thiết × RAID × format × sa | 46 | 24 | critical |
| `STO-05` | Tỷ lệ RAID, format, sai số, dự phòng của lưu trữ | 46 | 24 | major |
| `EVD-01` | Phân biệt rõ dung lượng lưu trữ khả dụng và dung lượ | 46 | 24 | major |
| `ARC-01` | Thiết bị mạng: dự phòng 20% số port và thông lượng | 44 | 21 | major |
| `ARC-22` | Redis: tổng số server = số master × (1 + số slave mỗ | 44 | 17 | minor |
| `FWL-01` | Số port firewall = (port các zone + port HA) × hệ số | 44 | 21 | major |
| `FWL-02` | Lưu lượng zone và thông lượng thiết bị firewall | 44 | 21 | critical |
| `FWL-03` | Throughput firewall phải đo theo gói chuẩn 1518 Byte | 44 | 21 | major |
| `LBA-01` | Cân bằng tải: số port, CPS lớp 4, TPS lớp 7 và thông | 44 | 21 | critical |
| `LBA-02` | Lưu lượng dịch vụ của cân bằng tải và chọn bandwidth | 44 | 21 | major |
| `KPI-03` | Máy chủ: tỷ lệ sử dụng RAM không vượt quá 90% | 42 | 18 | critical |
| `KPI-01` | Tải dùng để đánh giá KPI phải là giá trị 95th | 35 | 17 | major |
| `KPI-10` | Khoảng đo tải phải dài tối thiểu 01 tháng | 35 | 17 | major |
| `EVD-05` | Định cỡ theo tổng tải giao dịch giờ cao điểm | 35 | 17 | critical |
| `EVD-11` | Bảng thông số đầu vào phải tách tải theo loại nghiệp | 35 | 17 | major |
| `MTH-01` | Dạng I: phải nêu đặc điểm tương đồng của hệ thống th | 33 | 18 | major |
| `KPI-07` | Ngoại lệ: SSD cho HĐH / DB OLTP / cache / snapshot d | 29 | 17 | major |
| `STO-02` | Ổ NL-SAS / SATA 7.2k nên dùng RAID 6 | 29 | 17 | minor |
| `STO-03` | IOPS tối đa theo loại ổ | 29 | 17 | major |
| `STO-13` | Dung lượng mỗi ổ nên nằm trong dải thông dụng của lo | 29 | 17 | minor |
| `STO-14` | Hệ đọc/ghi ngẫu nhiên cao nên dùng ổ tốc độ cao, dun | 29 | 17 | minor |
| `STO-15` | SSD dùng từ 75% dung lượng trở lên thì tốc độ ghi su | 29 | 17 | major |
| `ARC-08` | Cấu hình 01 máy chủ = tổng tài nguyên / số máy hoạt  | 25 | 10 | major |
| `ARC-19` | Redis: dưới 32 GB dùng Sentinel, từ 32 GB dùng Clust | 25 | 10 | minor |
| `ARC-20` | Redis Cluster: số master là số lẻ nhỏ nhất giữ RAM m | 25 | 10 | minor |
| `ARC-21` | Redis: số slave mỗi master theo mức độ quan trọng | 25 | 10 | minor |
| `ARC-23` | Kafka: RAM mỗi broker = S × R / N + 8, giữ trong dải | 25 | 10 | minor |
| `ARC-24` | Kafka: cluster tối thiểu 3 broker | 25 | 10 | minor |
| `ARC-25` | Kafka: số broker trong dải 3–20 và RAM mỗi broker tr | 25 | 10 | minor |
| `RAM-01` | Không overcommit RAM khi định cỡ | 25 | 15 | major |
| `RAM-02` | RAM sử dụng = tỷ lệ dùng 95th × dung lượng RAM | 25 | 15 | critical |
| `KPI-12` | Hệ số so sánh Ksosánh = thông số hệ mới / hệ tham ch | 20 | 14 | critical |
| `MTH-02` | Dạng I không có hệ tham chiếu: phải hoàn thiện sản p | 20 | 14 | critical |

_(còn 35 quy tắc nữa, xem `appraisal-mapping.md`)_

---

## 3. Quy tắc chưa lần nào khớp — 75 quy tắc

**Không có nghĩa là quy tắc sai.** Ba lý do có thể, phải phân biệt:

1. Quy tắc đúng nhưng **hiếm gặp** (SAN switch, tủ Rack, tape) — giữ nguyên.
2. Vấn đề **có bị bắt** nhưng bản tóm tắt của AI không ghi lại đủ chi tiết
   để từ khóa nhận ra — lỗi của nguồn, không phải của quy tắc.
3. Quy tắc thật sự **không ai soi** — mới là ứng viên xem lại.

Với nguồn gián tiếp như thế này, **không đủ căn cứ để bỏ quy tắc nào**.

| Nhóm | Chưa khớp | Mã |
|---|---:|---|
| `ALC` | 5 | `ALC-01` `ALC-02` `ALC-03` `ALC-04` `ALC-05` |
| `ARC` | 11 | `ARC-04` `ARC-05` `ARC-06` `ARC-07` `ARC-10` `ARC-11` `ARC-13` `ARC-14` `ARC-15` `ARC-17` `ARC-18` |
| `BAK` | 8 | `BAK-03` `BAK-04` `BAK-05` `BAK-06` `BAK-07` `BAK-08` `BAK-10` `BAK-11` |
| `CPU` | 5 | `CPU-03` `CPU-04` `CPU-07` `CPU-08` `CPU-11` |
| `EVD` | 11 | `EVD-02` `EVD-04` `EVD-06` `EVD-08` `EVD-12` `EVD-15` `EVD-16` `EVD-17` `EVD-18` `EVD-21` `EVD-22` |
| `KPI` | 6 | `KPI-08` `KPI-09` `KPI-11` `KPI-13` `KPI-15` `KPI-16` |
| `LAN` | 4 | `LAN-01` `LAN-02` `LAN-03` `LAN-04` |
| `PRC` | 5 | `PRC-04` `PRC-06` `PRC-07` `PRC-08` `PRC-10` |
| `RAM` | 1 | `RAM-03` |
| `RCK` | 3 | `RCK-01` `RCK-02` `RCK-03` |
| `SAN` | 2 | `SAN-01` `SAN-02` |
| `STO` | 11 | `STO-07` `STO-09` `STO-10` `STO-11` `STO-16` `STO-17` `STO-19` `STO-20` `STO-21` `STO-22` `STO-23` |
| `TST` | 3 | `TST-01` `TST-02` `TST-03` |

---

## 4. Khuyến nghị — nêu ra, KHÔNG tự áp dụng

1. **Quyết định về 9 khoảng trống ở mục 1.** Ít nhất ba chỗ đáng thành quy tắc
   định lượng vì thuần code kiểm được: kiểm hợp lý đơn vị số liệu đầu vào,
   nhất quán chu kỳ lưu trữ giữa các phân vùng, và làm tròn số trung gian.
2. **Xem lại `KPI-16`** (tăng trưởng) đang `enabled: false` — thực tế cho thấy
   tốc độ tăng trưởng bị hỏi sở cứ thường xuyên. Nhưng bật lên thì phải giải
   quyết mâu thuẫn 01 năm ↔ 06 tháng với `ALC-01` trước.
3. **Chưa đủ căn cứ điều chỉnh `severity`** theo tần suất. Nguồn là tóm tắt
   gián tiếp, tần suất ở đây phản ánh cả cách AI kia viết lẫn hành vi thật.

