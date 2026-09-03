# Mục 0.5 — Bảng mã chính thức của bộ quy tắc

> **Sinh bằng `scripts/build_rule_ids.py`** (công cụ dùng một lần).
>
> ⚠️ **Mã trong bảng này là CỐ ĐỊNH.** Đổi mã sẽ làm hỏng liên kết với eval set
> (`PLAN.md` mục 0.7) và với `rule_ref` của mọi finding đã lưu.
>
> Quy ước gán: nhóm theo **chủ đề / loại thiết bị**, KHÔNG theo module phần mềm —
> module đi vào trường `applies_to_module` (quyết định "hai trục",
> `rules-crossmap.md` mục 5). Số chạy trong từng nhóm, gán **một lượt** cho cả bộ
> để nhóm chứa lẫn quy tắc định lượng và định tính không phải đánh số hai lần.

**Tổng: 151 quy tắc** vào `config/rules.yaml`.

> **BỔ SUNG 2026-09-03 — `PRC-11`** (*"Phải nêu mục đích sizing — định cỡ mới hay bổ
> sung cho hệ đang chạy"*), người dùng duyệt. `CL-2.1` trước đây bị xếp trạng thái **T**
> (trùng) và chỉ gắn `checklist_ref` vào nhóm `MTH`, nên không quy tắc nào kiểm được
> việc tài liệu có nêu mục đích sizing hay không. Căn cứ: 17 nhãn trong eval set từ PNX
> nhiều hồ sơ. Chi tiết ở `docs/0.7-nhan-vang-tu-pnx.md` mục 5.
> ⚠️ `scripts/build_rule_ids.py` đọc từ tài liệu nguồn, **không** đọc `rules.yaml` —
> chạy lại sẽ xóa mất dòng này. Sửa tay khi thêm quy tắc mới.

> ✅ **ĐÃ SỐ HÓA XONG 150/150 (2026-08-26).** Kiểm bằng
> `uv run python scripts/validate_rules.py --coverage`.
> Phân bố: 101 định lượng / 49 định tính · 131 Vòng 2 / 19 Vòng 1 ·
> 37 `critical` / 80 `major` / 33 `minor` · 4 quy tắc `enabled: false`.

| Nhóm | Nghĩa | Số quy tắc | Dải mã |
|---|---|---:|---|
| `ALC` | Cấp phát, thu hồi | 5 | `ALC-01` … `ALC-05` |
| `ARC` | Kiến trúc, dự phòng, hạ tầng | 27 | `ARC-01` … `ARC-27` |
| `BAK` | Sao lưu | 11 | `BAK-01` … `BAK-11` |
| `CPU` | CPU và quy đổi SPEC | 11 | `CPU-01` … `CPU-11` |
| `EVD` | Sở cứ & mô tả bắt buộc | 22 | `EVD-01` … `EVD-22` |
| `FWL` | Firewall | 4 | `FWL-01` … `FWL-04` |
| `KPI` | Ngưỡng & hệ số chung | 16 | `KPI-01` … `KPI-16` |
| `LAN` | LAN switch | 4 | `LAN-01` … `LAN-04` |
| `LBA` | Cân bằng tải | 2 | `LBA-01` … `LBA-02` |
| `MTH` | Phương pháp định cỡ (Dạng I/II/III) | 4 | `MTH-01` … `MTH-04` |
| `PRC` | Thủ tục & quy trình | 11 | `PRC-01` … `PRC-11` |
| `RAM` | RAM | 3 | `RAM-01` … `RAM-03` |
| `RCK` | Tủ Rack | 3 | `RCK-01` … `RCK-03` |
| `SAN` | SAN switch | 2 | `SAN-01` … `SAN-02` |
| `STO` | Lưu trữ | 23 | `STO-01` … `STO-23` |
| `TST` | Kiểm thử hiệu năng | 3 | `TST-01` … `TST-03` |

> Nhóm `CHK` đã dự trù ở `rules-crossmap.md` mục 6 nhưng **không dùng đến**:
> mọi mục checklist đều gắn được vào một nhóm chủ đề có sẵn.

---

## Bảng mã đầy đủ

### `ALC` — Cấp phát, thu hồi

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `ALC-01` | `R93` | Guideline |
| `ALC-02` | `R94` | Guideline |
| `ALC-03` | `R96` | Guideline |
| `ALC-04` | `R97` | Guideline |
| `ALC-05` | `R108` | Guideline |

### `ARC` — Kiến trúc, dự phòng, hạ tầng

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `ARC-01` | `R09` | Guideline |
| `ARC-02` | `R10` | Guideline |
| `ARC-03` | `R11` | Guideline |
| `ARC-04` | `R12` | Guideline |
| `ARC-05` | `R13` | Guideline |
| `ARC-06` | `R14` | Guideline |
| `ARC-07` | `R15` | Guideline |
| `ARC-08` | `R50` | Guideline |
| `ARC-09` | `R51` | Guideline |
| `ARC-10` | `R91` | Guideline |
| `ARC-11` | `R95` | Guideline |
| `ARC-12` | `R101` | Guideline |
| `ARC-13` | `R102` | Guideline |
| `ARC-14` | `R106` | Guideline |
| `ARC-15` | `CL-3.x.9` | Checklist |
| `ARC-16` | `CL-3.x.10` | Checklist |
| `ARC-17` | `MDB-01` | Code web app |
| `ARC-18` | `MDB-02` | Code web app |
| `ARC-19` | `RDS-03` | Code web app |
| `ARC-20` | `RDS-06` | Code web app |
| `ARC-21` | `RDS-07` | Code web app |
| `ARC-22` | `RDS-08` | Code web app |
| `ARC-23` | `KFK-05` | Code web app |
| `ARC-24` | `KFK-07` | Code web app |
| `ARC-25` | `KFK-11` | Code web app |
| `ARC-26` | `QD849-01` | Văn bản khác |
| `ARC-27` | `QD849-02` | Văn bản khác |

### `BAK` — Sao lưu

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `BAK-01` | `R39` | Guideline |
| `BAK-02` | `R70` | Guideline |
| `BAK-03` | `R71` | Guideline |
| `BAK-04` | `R72` | Guideline |
| `BAK-05` | `R73` | Guideline |
| `BAK-06` | `R74` | Guideline |
| `BAK-07` | `R75` | Guideline |
| `BAK-08` | `R76` | Guideline |
| `BAK-09` | `R107` | Guideline |
| `BAK-10` | `MDB-05` | Code web app |
| `BAK-11` | `MDB-06` | Code web app |

### `CPU` — CPU và quy đổi SPEC

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `CPU-01` | `R16` | Guideline |
| `CPU-02` | `R17` | Guideline |
| `CPU-03` | `R20` | Guideline |
| `CPU-04` | `R21` | Guideline |
| `CPU-05` | `R43` | Guideline |
| `CPU-06` | `R44` | Guideline |
| `CPU-07` | `R46` | Guideline |
| `CPU-08` | `R47` | Guideline |
| `CPU-09` | `R52` | Guideline |
| `CPU-10` | `R100` | Guideline |
| `CPU-11` | `KFK-06` | Code web app |

### `EVD` — Sở cứ & mô tả bắt buộc

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `EVD-01` | `R23` | Guideline |
| `EVD-02` | `R25 + R32` | Guideline |
| `EVD-03` | `R35` | Guideline |
| `EVD-04` | `R37` | Guideline |
| `EVD-05` | `R42` | Guideline |
| `EVD-06` | `R53` | Guideline |
| `EVD-07` | `R59` | Guideline |
| `EVD-08` | `R103` | Guideline |
| `EVD-09` | `R104` | Guideline |
| `EVD-10` | `R105` | Guideline |
| `EVD-11` | `R110` | Guideline |
| `EVD-12` | `CL-2.2` | Checklist |
| `EVD-13` | `CL-2.6` | Checklist |
| `EVD-14` | `CL-2.7` | Checklist |
| `EVD-15` | `CL-2.8` | Checklist |
| `EVD-16` | `CL-2.9` | Checklist |
| `EVD-17` | `CL-3.x.1` | Checklist |
| `EVD-18` | `CL-3.x.2` | Checklist |
| `EVD-19` | `CL-3.x.4` | Checklist |
| `EVD-20` | `CL-3.x.5` | Checklist |
| `EVD-21` | `CL-3.x.8` | Checklist |
| `EVD-22` | `CL-3.x.20` | Checklist |

### `FWL` — Firewall

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `FWL-01` | `R83` | Guideline |
| `FWL-02` | `R84` | Guideline |
| `FWL-03` | `R85` | Guideline |
| `FWL-04` | `ZONE-01` | Văn bản khác |

### `KPI` — Ngưỡng & hệ số chung

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `KPI-01` | `R01` | Guideline |
| `KPI-02` | `R02` | Guideline |
| `KPI-03` | `R03` | Guideline |
| `KPI-04` | `R04` | Guideline |
| `KPI-05` | `R05` | Guideline |
| `KPI-06` | `R06` | Guideline |
| `KPI-07` | `R07` | Guideline |
| `KPI-08` | `R08` | Guideline |
| `KPI-09` | `R19` | Guideline |
| `KPI-10` | `R36` | Guideline |
| `KPI-11` | `R38` | Guideline |
| `KPI-12` | `R40` | Guideline |
| `KPI-13` | `R48` | Guideline |
| `KPI-14` | `R49` | Guideline |
| `KPI-15` | `KPI-04` | Code web app |
| `KPI-16` | `GRW-01` | Code web app |

### `LAN` — LAN switch

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `LAN-01` | `R79` | Guideline |
| `LAN-02` | `R80` | Guideline |
| `LAN-03` | `R81` | Guideline |
| `LAN-04` | `R82` | Guideline |

### `LBA` — Cân bằng tải

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `LBA-01` | `R86` | Guideline |
| `LBA-02` | `R87` | Guideline |

### `MTH` — Phương pháp định cỡ (Dạng I/II/III)

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `MTH-01` | `R26` | Guideline |
| `MTH-02` | `R27` | Guideline |
| `MTH-03` | `R28` | Guideline |
| `MTH-04` | `R29` | Guideline |

### `PRC` — Thủ tục & quy trình

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `PRC-01` | `R30` | Guideline |
| `PRC-02` | `R31` | Guideline |
| `PRC-03` | `R33` | Guideline |
| `PRC-04` | `R34` | Guideline |
| `PRC-05` | `R92` | Guideline |
| `PRC-06` | `R109` | Guideline |
| `PRC-07` | `CL-1.1` | Checklist |
| `PRC-08` | `CL-1.2` | Checklist |
| `PRC-09` | `CL-2.3` | Checklist |
| `PRC-10` | `CL-2.10a` | Checklist |
| `PRC-11` | `CL-2.1` | Checklist |

### `RAM` — RAM

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `RAM-01` | `R22` | Guideline |
| `RAM-02` | `R45` | Guideline |
| `RAM-03` | `RDS-02` | Code web app |

### `RCK` — Tủ Rack

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `RCK-01` | `R88` | Guideline |
| `RCK-02` | `R89` | Guideline |
| `RCK-03` | `R90` | Guideline |

### `SAN` — SAN switch

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `SAN-01` | `R77` | Guideline |
| `SAN-02` | `R78` | Guideline |

### `STO` — Lưu trữ

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `STO-01` | `R18` | Guideline |
| `STO-02` | `R54` | Guideline |
| `STO-03` | `R55` | Guideline |
| `STO-04` | `R56` | Guideline |
| `STO-05` | `R57` | Guideline |
| `STO-06` | `R58` | Guideline |
| `STO-07` | `R60` | Guideline |
| `STO-08` | `R61` | Guideline |
| `STO-09` | `R62` | Guideline |
| `STO-10` | `R63` | Guideline |
| `STO-11` | `R64` | Guideline |
| `STO-12` | `R65` | Guideline |
| `STO-13` | `R66` | Guideline |
| `STO-14` | `R67` | Guideline |
| `STO-15` | `R68` | Guideline |
| `STO-16` | `R69` | Guideline |
| `STO-17` | `CL-3.x.18` | Checklist |
| `STO-18` | `CL-3.2.7a` | Checklist |
| `STO-19` | `RDS-01` | Code web app |
| `STO-20` | `RDS-05` | Code web app |
| `STO-21` | `KFK-02` | Code web app |
| `STO-22` | `KFK-03` | Code web app |
| `STO-23` | `KFK-04` | Code web app |

### `TST` — Kiểm thử hiệu năng

| Mã chính thức | `legacy_ref` | Nguồn |
|---|---|---|
| `TST-01` | `R41` | Guideline |
| `TST-02` | `R98` | Guideline |
| `TST-03` | `R99` | Guideline |

---

## Quy tắc KHÔNG vào `rules.yaml` — ghi lý do, không im lặng bỏ

### Từ Guideline

| Mã tạm | Lý do |
|---|---|
| `R24` | Câu tuyên bố ("kết quả định cỡ không chính xác 100%"), không phải yêu cầu — không nội dung nào có thể vi phạm nên không viết được tiêu chí ĐẠT/KHÔNG ĐẠT. Xem rules-criteria.md mục 1.3. |
| `R32` | Gộp vào R25 (cùng yêu cầu chỉ rõ yếu tố scale up/out). Một quy tắc mang hai `source_doc` để không bắt lỗi hai lần với hai trích dẫn khác nhau. Xem rules-criteria.md mục 2. |

### Từ code web app

| Mã tạm | Lý do |
|---|---|
| `LBF-01` | Code THIẾU (C-06: không áp Kdph = 1.2). R86/R87 đã có công thức đúng. |
| `LBF-02` | Như LBF-01 — R87 đã phủ. |
| `MDB-07` | Quy ước làm tròn lên (ceil) áp cho mọi kết quả — đưa vào `globals` làm quy ước chung, không thành một quy tắc riêng. |
| `PRC-01` | Ràng buộc vận hành của web app (không duyệt khi còn tab chưa đánh giá), không phải yêu cầu đối với bản sizing Word. Copilot không kiểm được và cũng không nên kiểm. |
| `PRC-02` | Như PRC-01 — ràng buộc của giao diện thẩm định, không phải của tài liệu. |
| `RDS-04` | Code SAI (rules-crossmap.md C-01: dùng Kkpi 0.8 cho RAM thay vì 0.9). Số hóa theo R49 cho đúng, KHÔNG số hóa công thức sai. |
| `RDS-10` | Code SAI (C-02: áp hệ số KPI và sai số hai lần). R48 quy định áp đúng một lần trên tổng tài nguyên. |

> Bốn dòng `RDS-04`, `RDS-10`, `LBF-01`, `LBF-02` là **lỗi tính toán đang chạy
> thật trên web app** (`rules-crossmap.md` mục 2). Copilot số hóa theo Guideline
> cho đúng; việc sửa code là của đội bảo trì web app.

---

## Quy tắc code web app được GỘP vào quy tắc Guideline

Không tạo quy tắc mới — chỉ thêm `code_ref` vào quy tắc Guideline tương ứng, để
khi code đổi thì còn đối chiếu được.

| Mã code | Gộp vào | Mã chính thức |
|---|---|---|
| `CPU-01` | `R48` | `KPI-13` |
| `DSK-01` | `R48` | `KPI-13` |
| `HA-01` | `R101` | `ARC-12` |
| `KFK-01` | `R40` | `KPI-12` |
| `KFK-08` | `R48` | `KPI-13` |
| `KFK-09` | `R48` | `KPI-13` |
| `KFK-10` | `R48` | `KPI-13` |
| `KPI-01` | `R02` | `KPI-02` |
| `KPI-02` | `R03` | `KPI-03` |
| `KPI-03` | `R04` | `KPI-04` |
| `KPI-05` | `R19` | `KPI-09` |
| `MDB-03` | `R48` | `KPI-13` |
| `MDB-04` | `R48` | `KPI-13` |
| `RAM-01` | `R48` | `KPI-13` |
| `RDS-09` | `R48` | `KPI-13` |
| `RDS-11` | `RDS-03` | `ARC-19` |
| `SCL-01` | `R40` | `KPI-12` |
| `SRV-01` | `R50` | `ARC-08` |
| `SRV-02` | `R50` | `ARC-08` |

