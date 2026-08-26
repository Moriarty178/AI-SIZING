# Đối chiếu hai nguồn quy tắc — tài liệu gốc ↔ code hiện hành

> **Mục đích:** hợp nhất hai công việc đang chạy song song và chưa biết đến nhau:
>
> | Nguồn | File | Số quy tắc | Mã tạm |
> |---|---|---|---|
> | **TL** — Guideline định cỡ (lần 07, **44 trang**) | `docs/rules/rules-flat-draft.md` | **110** | `R01`–`R110` |
> | **CODE** — hệ thống web hiện hành | `docs/0.1-danh-sach-quy-tac.md` | **46** | `KPI-01`, `MDB-01`… |
>
> *(Cập nhật 2026-08-26: file này viết khi mới có hai nguồn và bản lần 06 — nay là
> bốn nguồn, bản lần 07 44 trang, Guideline 110 quy tắc, code web app 46 quy tắc.
> Hai nguồn còn lại: `rules-checklist-flat.md` (37) và `rules-nguon-khac.md` (3).)*
>
> Hai danh sách **chồng lấn một phần và mâu thuẫn ở vài chỗ**. File này là bản đối
> chiếu, dùng làm đầu vào cho mục 0.5 (số hóa `rules.yaml`).
>
> **Nguyên tắc:** tài liệu Guideline là **nguồn có thẩm quyền**. Code chỉ là một
> cách hiện thực hóa, và đã lệch ở ba chỗ. Nhưng code cũng chứa quy tắc **không có
> trong Guideline** — đó không tự động là sai, xem mục 3.

---

## 0. ~~Việc cần xử lý trước tiên — tài liệu đã hết hiệu lực~~ ĐÃ XONG

> **Cập nhật 2026-08-25.** Vấn đề hiệu lực đã được giải quyết:
>
> - Đã nhận **lần ban hành 07** (hiệu lực 01/10/2023 → 01/10/2025, 44 trang) và
>   được xác nhận đây là bản đang áp dụng thực tế.
> - Đã đối chiếu lần 06 → lần 07 bằng `scripts/diff_guideline.py`:
>   **không quy tắc nào trong 100 quy tắc bị thay đổi.** Mọi ngưỡng, hệ số, công
>   thức giữ nguyên. Khác biệt chỉ ở chữ ký, bảng lịch sử sửa đổi và mục lục.
> - Nguồn trích dẫn nguyên văn chuyển sang `docs/rules/.tmp-lan7/clean.txt`.
>
> Báo cáo đầy đủ: [`rules-lan7-doi-chieu.md`](rules-lan7-doi-chieu.md).
>
> **Còn treo:** checklist rà soát của người thẩm định (lần 07 tuyên bố đã bổ sung
> nhưng không có trong file), Phụ lục 01, Phụ lục 02, và tài liệu định cỡ server
> GPU. Xem `PLAN.md` mục 0.12.

---

## 1. Khớp — code hiện thực hóa đúng Guideline

Phát hiện quan trọng nhất: **công thức lõi của web app chính là R48 + R49.**

Guideline R48: `ΣCPU = ΣCPUsudung × Ksosánh / Kkpi_cpu × Ksaisố`
Code ([script.js:6704](../../frontend/script.js#L6704)): `cintAfterKPI = (totalCint × factor) / 0.75 × 1.1`

Thay `Ksosánh = factor`, `Kkpi_cpu = 0.75`, `Ksaisố = 1.1` → **trùng khít**.

| Mã CODE | Nội dung | Mã TL | Nhận xét |
|---|---|---|---|
| KPI-01 | CPU ≤ 75% | **R02** | khớp |
| KPI-02 | RAM ≤ 90% | **R03** | khớp |
| KPI-03 | Ổ cứng ≤ 80% | **R04** | khớp |
| KPI-05 | Hệ số sai số 1.1 | **R19, R49** | khớp (`Ksaisố`) |
| HA-01 | Dự phòng active-active / active-standby | **R10, R11, R12** | khớp; TL chi tiết hơn (N+1 máy chủ, 1+1 thiết bị mạng) |
| SCL-01 | `factor = định_cỡ / POC` | **R40** | khớp (`Ksosánh`) |
| CPU-01 | `cint × factor / 0.75 × 1.1` | **R48 + R49** | khớp chính xác |
| RAM-01 | `ram × factor / 0.9 × 1.1` | **R48 + R49** | khớp chính xác |
| DSK-01 | `disk × factor / 0.8 × 1.1` | **R48 + R49** | khớp chính xác |
| MDB-01…04 | MariaDB CPU/RAM/data/log | **R43, R45, R48, R49** | khớp phần công thức nền |
| KFK-02 | `D = A×3600×T×R×C×1.1/0.8` | **R48, R49** | nhất quán — dùng đúng `Kkpi_dia` và `Ksaisố` |
| KFK-08…10 | Kafka linear CPU/RAM/disk | **R48, R49** | khớp |
| PRC-01, PRC-02 | Phải được đánh giá mới cho duyệt | **R30, R31, R33, R34, R92** | khớp tinh thần thủ tục |

**Ý nghĩa:** phần lõi tính toán của web app đúng chuẩn. Không cần thiết kế lại —
Copilot chỉ cần kiểm lại đúng công thức này trên bản Word.

---

## 2. Lệch — code sai so với Guideline

Đây là kết quả quan trọng nhất của việc đối chiếu: **ba điểm tôi liệt kê ở mục C
của `docs/0.1-danh-sach-quy-tac.md` giờ đã có đáp án**, không còn là "cần hỏi".

| # | Điểm lệch | Guideline nói gì | Kết luận |
|---|---|---|---|
| **C-01** | Redis (PP Key): code dùng `C × 1.1 / 0.8` cho **RAM** ([15224](../../frontend/script.js#L15224), [15237](../../frontend/script.js#L15237)) | **R49**: `Kkpi_ram = 0.9`. Hệ số `0.8` là của **ổ cứng**, không phải RAM | ❌ **Code sai.** Text hiển thị cho người dùng ([15268](../../frontend/script.js#L15268)) ghi `/0.9` mới là đúng. RAM Redis đang bị tính **dư ~12.5%** |
| **C-02** | Redis (PP Cấu hình): áp `1.1 / 0.9` **hai lần** ([15336](../../frontend/script.js#L15336) → [15356](../../frontend/script.js#L15356)) | **R48** áp `Kkpi` và `Ksaisố` **đúng một lần** trên tổng tài nguyên | ❌ **Code sai.** Hệ số cộng dồn `(1.1/0.9)² ≈ 1.494` → RAM dư **~22%** |
| **C-06** | LB/FW: không áp hệ số nào ([13527-13530](../../frontend/script.js#L13527-L13530)) | **R86**: `Thongluong = Σ luuluong_dichvu × Kdph_luuluong`, `Kdph = 1.2` | ❌ **Code thiếu.** Băng thông LB đang bị tính **thiếu 20%** |
| **C-05** | Code ghim "tăng trưởng **01 năm**" ([script.js:3843](../../frontend/script.js#L3843)) | **R93**: cấp phát đảm bảo hoạt động **06 tháng** | ⚠️ **Mâu thuẫn chu kỳ.** Hai mốc khác nhau phục vụ hai việc khác nhau (định cỡ vs cấp phát) hay là lệch thật? Cần hỏi |
| **C-04** | KPI **Datanode ≤ 50%** trong `FIXED_SIZING_RULE` | **Không có** trong R01–R100 | ⚠️ Quy tắc này **không có nguồn trong Guideline**. Nó từ đâu ra? Nếu là quy định riêng cho Hadoop/Big data thì cần văn bản gốc, nếu không thì không đưa vào `rules.yaml` (vi phạm NT2 — không có `source_doc`) |

> Ba dòng ❌ là **lỗi tính toán đang chạy trên hệ thống thật**, không phải vấn đề
> của Copilot. Nên báo cho đội bảo trì web app độc lập với dự án này.

---

## 3. Code có, Guideline không có — phần mở rộng theo công nghệ

Guideline dừng ở mức **loại thiết bị** (máy chủ, lưu trữ, switch…). Code đi xuống
mức **phần mềm cụ thể** (Redis, Kafka, MariaDB, K8S). Đây là khoảng trống Guideline
không phủ, không phải code làm sai.

| Nhóm CODE | Nội dung | Tình trạng |
|---|---|---|
| RDS-03, 05, 06, 07 | Ngưỡng 32 GB chọn Sentinel/Cluster; `DISK = 4 × RAM`; `N` lẻ sao cho RAM/node < 64 GB; slave theo mức DBQT | Không có trong TL — cần văn bản nội bộ làm căn cứ |
| KFK-03, 05, 06, 11 | `T=168h`, `R=3`, `C_nén=0.5`; `RAM_broker = S×R/N + 8`; vCPU 8/16 theo ngưỡng 50 MB/s; N ∈ [3,20] | Không có trong TL |
| MDB-01/02 (phần `÷3`) | Active-Active chia cứng cho 3 master | Không có trong TL; sai nếu không đúng 3 master |
| C-10 | Ngưỡng RAM/node 16–64 GB | TL **R13** cho ngưỡng khác: VM **≤ 32 vCPU và ≤ 128 GB RAM**. Ngưỡng 64 GB của code chặt hơn, không rõ căn cứ |

**Cách xử lý đề xuất:** giữ các quy tắc này trong `rules.yaml` nhưng đánh dấu
`source_doc: "Quy ước nội bộ — chưa có văn bản"` và đặt `severity: minor` +
`confidence_floor: high` cho tới khi có căn cứ. Không xóa (chúng đang được dùng
thật), cũng không nâng lên `critical` khi chưa có nguồn.

---

## 4. Guideline có, code không có — đây mới là phần Copilot tạo giá trị

Khoảng **60/100 quy tắc** trong Guideline **không có đối ứng nào** trong web app.
Web app chỉ định cỡ **máy chủ** (CPU/RAM/disk) và một phần **LB** (băng thông).

| Nhóm Guideline | Mã | Web app có kiểm? |
|---|---|---|
| Định cỡ **lưu trữ** — RAID, IOPS, write penalty, số ổ, hotspare | R54–R69 (16 quy tắc) | ❌ không |
| Định cỡ **sao lưu** — dung lượng, tape, driver, LTO | R70–R76 (7) | ❌ không |
| **SAN switch** | R77–R78 (2) | ❌ không |
| **LAN switch** — số port, bandwidth, thông lượng, ghép port | R79–R82 (4) | ❌ không |
| **Firewall** — port theo zone, lưu lượng, throughput | R83–R85 (3) | ❌ không (module LB/FW chỉ tính băng thông) |
| **Tủ Rack** — RU, số rack, PDU | R88–R90 (3) | ❌ không |
| **Cấp phát / thu hồi** | R91–R97 (7) | ❌ không |
| **Kiểm thử hiệu năng** | R98–R99 (2) | ❌ không |
| Chuẩn bị thông số máy chủ — 95th, ≥1 tháng, ≥5 mẫu×5 lần | R36–R42 | ❌ không |
| Quy đổi SPEC, HĐH, hypervisor, N+M | R46, R47, R51, R52 | ❌ không |

> **Đây là luận cứ giá trị mạnh nhất của dự án.** Người làm sizing hiện phải tự
> nhớ ~60 quy tắc mà không công cụ nào nhắc. Copilot phủ được phần này là phần
> tăng thêm thật, không trùng với thứ web app đã làm.

---

## 5. Hai trục phân loại — cần thống nhất trước mục 0.5

Hai nguồn phân loại theo hai trục khác nhau, và `config/rules.yaml` hiện chỉ có một trục:

- **Guideline** phân theo **loại thiết bị**: máy chủ · lưu trữ · sao lưu · SAN switch ·
  LAN switch · firewall · load balancer · tủ rack · cấp phát/thu hồi · kiểm thử.
- **Web app** phân theo **module phần mềm**: App · MariaDB · Redis · Kafka · K8S ·
  LB/FW · Khác.

Đây không phải hai cách gọi của cùng một thứ — một bản sizing Redis đồng thời là
"định cỡ máy chủ" (theo TL) và "module Redis" (theo web app).

**Đề xuất:** `rules.yaml` dùng **hai trường riêng**:

```yaml
applies_to_equipment: [may_chu, luu_tru, sao_luu, san_switch, lan_switch,
                       firewall, load_balancer, rack, cap_phat, kiem_thu]
applies_to_module:    [app, mariadb, redis, kafka, k8s, lb_fw, other]   # tùy chọn
```

Quy tắc từ Guideline điền trục thứ nhất; quy tắc mở rộng từ code điền cả hai.
Trường `service_types` hiện có trong `config/rules.yaml` sẽ được thay bằng cặp này.

---

## 6. Mã quy tắc chính thức — cần chốt ở mục 0.5

Đang có ba hệ mã cùng tồn tại:

| Hệ | Ví dụ | Nguồn |
|---|---|---|
| `Rxx` | R01–R100 | mã tạm của `rules-flat-draft.md` |
| Nhóm-số | `KPI-01`, `MDB-04` | mã tạm của `0.1-danh-sach-quy-tac.md` |
| `STO-xx` / `CPU-xx` | mẫu ở Phụ lục A | mã chính thức dự kiến |

**Đề xuất:** dùng hệ **`<NHÓM>-<số>`** theo nhóm thiết bị của Guideline, và **giữ
`Rxx` làm trường truy vết** trong `rules.yaml`:

```yaml
- id: CPU-01
  legacy_ref: [R48, R49]          # truy về danh sách phẳng 0.1
  code_ref: "frontend/script.js:6704"   # nếu có đối ứng trong code
```

Nhóm đề xuất: `KPI` (ngưỡng chung) · `CPU` · `RAM` · `STO` (lưu trữ) · `BAK` (sao lưu) ·
`SAN` · `LAN` · `FWL` · `LBA` · `RCK` · `ALC` (cấp phát/thu hồi) · `TST` (kiểm thử) ·
`PRC` (thủ tục).

**Bổ sung 2026-08-25** — ba nhóm phát sinh khi làm mục 0.4 cho quy tắc định tính:

| Nhóm | Nghĩa |
|---|---|
| `ARC` | Kiến trúc, dự phòng, hạ tầng (R10, R14, R91, R95, R101, R102) |
| `EVD` | Sở cứ & mô tả bắt buộc (R23, R25+R32, R35, R37, R53, R59) |
| `MTH` | Phương pháp định cỡ — Dạng I/II/III (R26, R27, R28, R29) |

`ARC` và `STO` chứa **cả** quy tắc định lượng lẫn định tính, nên số thứ tự phải gán
một lượt cho cả 100+ quy tắc ở mục 0.5, không gán riêng theo nhóm.

**Bổ sung 2026-08-26** — sau khi viết tiêu chí cho 8 quy tắc R102–R110, thêm **`BAK`**
(R107 — cộng thêm năng lực cho tác vụ sao lưu) và **`ALC`** (R108 — quy hoạch cấp phát)
vào danh sách nhóm chứa **cả ĐL lẫn ĐT**. Nay có bốn nhóm như vậy: `ARC`, `STO`, `BAK`,
`ALC` — càng khẳng định phải gán số một lượt ở 0.5.

> **✅ ĐÃ CHỐT (2026-08-26).** Lược đồ `<NHÓM>-<số>` + `legacy_ref: [Rxx]` là mã
> chính thức. **Số thứ tự gán một lượt ở mục 0.5**, không gán sớm. Danh sách 16 nhóm
> ở trên đã được kiểm là đủ dùng — mọi nhóm đang gán thực tế đều nằm trong danh sách,
> 5 nhóm còn trống (`KPI`, `LAN`, `SAN`, `RCK`, `CHK`) dành cho 77 quy tắc định lượng.

---

## 7. Việc còn lại để hợp nhất

> **Rà lại 2026-08-26 — ba việc "chặn 0.5" nay đã xong hết.** Hai trong ba thực ra
> đã xong từ trước nhưng ô đánh dấu chưa được cập nhật; việc thứ ba (số trang) mới
> làm. **0.5 không còn bị chặn.**

### Đã xong — không còn chặn 0.5

- [x] **Xác minh tài liệu còn hiệu lực** (mục 0) — xong từ **2026-08-25**, ô đánh dấu
      bị bỏ quên. Đã nhận lần ban hành 07, đối chiếu lần 06 → 07: **0 quy tắc đổi**.
      `config/rules.yaml` ghi `status: active_confirmed`, `confirmed_on: 2026-08-24`.
- [x] **Chốt hai trục phân loại** (mục 5) — xong từ **2026-08-25**, ô đánh dấu bị bỏ
      quên. `config/rules.yaml` đã có `equipment_types` + `module_types`, trường
      `service_types` cũ đã bỏ.
      → ⚠️ **Nhưng còn một lỗ hổng, đã vá 2026-08-26:** `applies_to_equipment` là
      trường **bắt buộc**, trong khi **~21 quy tắc không gắn được với thiết bị nào** —
      10 quy tắc thủ tục/phương pháp áp cho mọi thiết bị (R26, R30, R102…) và 11 mục
      checklist chỉ nói về cấu trúc tài liệu (`CL-2.2`, `CL-2.6`, `CL-2.8`, `CL-2.9`…).
      → Đã thêm hai giá trị: **`tat_ca`** (mọi thiết bị) và **`tai_lieu`** (yêu cầu về
      cấu trúc/trình bày tài liệu). Kèm quy ước: "thiết bị mạng" của R09/R12 khai đủ
      bốn loại `[san_switch, lan_switch, firewall, load_balancer]`, **không** thêm giá
      trị `mang` để tránh chồng lấn khi so khớp.
- [x] **Chốt hệ mã chính thức** (mục 6) — lược đồ `<NHÓM>-<số>` + `legacy_ref: [Rxx]`
      đã chốt trong Nhật ký quyết định của `PLAN.md`; số thứ tự **cố ý để lại cho 0.5**
      (gán một lượt cho cả bộ). Đã kiểm **danh sách nhóm đủ dùng**: mọi nhóm đang được
      gán thực tế đều nằm trong 16 nhóm đã khai; 5 nhóm còn trống (`KPI`, `LAN`, `SAN`,
      `RCK`, `CHK`) dành cho 77 quy tắc định lượng sẽ đánh số ở 0.5.
- [x] **Thống nhất số trang** — *(việc này trước đây nằm trong phần mô tả 0.5 của
      `PLAN.md`, không có ô riêng ở đây)*. Toàn bộ R01–R110 nay dùng **số trang IN**.
      Xem `rules-flat-draft.md` mục "Ghi chú về số trang".
- [x] Làm mục **0.4** — **XONG 2026-08-26.** `rules-criteria.md` phủ **30/30 quy tắc
      định tính cần tiêu chí** (33 `đt` − 2 nhóm C − 1 do gộp R25+R32);
      `rules-formulas.md` phủ **77 quy tắc định lượng**.

### Còn treo — KHÔNG chặn 0.5

Ba việc dưới đây cần câu trả lời từ người khác, nhưng đều đã có cách xử lý tạm nên
không giữ 0.5 lại. Ghi rõ cách xử lý tạm để 0.5 số hóa được ngay:

- [ ] **Báo đội web app 3 lỗi tính toán** ở mục 2 (C-01, C-02, C-06) — độc lập với
      dự án này, không ảnh hưởng `rules.yaml`.
- [ ] **Hỏi nguồn của KPI Datanode ≤ 50%** và các ngưỡng Redis/Kafka ở mục 3.
      *Xử lý tạm ở 0.5:* giữ trong `rules.yaml` với
      `source_doc: "Quy ước nội bộ — chưa có văn bản"`, `severity: minor`,
      `confidence_floor: high` (đã thống nhất ở mục 3). `datanode_kpi` để `null`.
- [ ] **Hỏi đơn vị thẩm định: khâu cấp phát không có mục checklist nào phủ** —
      `R25+R32`, `R97`, `R108`, `R109` đều không map được sang mục checklist.
      *Xử lý tạm ở 0.5:* để `checklist_ref` rỗng và ghi `note` lý do; các quy tắc này
      chỉ chạy ở Vòng 2.
