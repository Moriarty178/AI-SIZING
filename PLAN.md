# PLAN.md — Lộ trình triển khai Sizing Copilot

> **Cách dùng file này:** đây là bảng công việc sống. Mỗi khi hoàn thành một
> mục, đánh dấu `[x]`. Không chuyển giai đoạn khi chưa đạt **Tiêu chí hoàn thành**
> của giai đoạn hiện tại. Bối cảnh và lý do đầy đủ: `docs/ke-hoach-trien-khai.md`.
> Nguyên tắc thiết kế bắt buộc: `CLAUDE.md`.

## Bảng trạng thái

| GĐ | Tên | Tiến độ | Trạng thái |
|----|-----|---------|------------|
| 0 | Chuẩn bị tri thức & dữ liệu | 11 / 13 (còn 0.9 thời gian/vòng, 0.12) | 🟢 Đủ để sang GĐ 1 |
| 1 | MVP chỉ xử lý text | 12 / 17 | 🟡 Đang làm — chờ số recall thật (1.13) |
| 2 | Đa phương thức & tái sử dụng | 0 / 14 | ⬜ Chưa bắt đầu |
| 3 | Tích hợp & tinh chỉnh | 0 / 11 | ⬜ Chưa bắt đầu |
| 4 | Vận hành & cải tiến | 0 / 6 | ⬜ Liên tục |

**Đang tập trung (2026-09-04):** Giai đoạn 1 đã xong **9/17** mục (1.1–1.6, 1.8, 1.9, 1.10) — nền tảng, C1, chuẩn hoá số/đơn vị, schema, bộ nạp quy tắc, C4 định lượng, C7 báo cáo Markdown; **88 unit test** chạy offline. Việc kế tiếp theo thứ tự: **1.7** C3 trích xuất (phần đo độ chính xác chờ `smoke_llm.py`), rồi 1.11 (RAG) · 1.12 (C5 — nguồn finding Vòng 1 cho C7). Song song, việc của người: (a) kiểm độc lập một lát cắt `eval_sheet_mau_kiem_daduyet.csv`; (b) chạy `scripts/smoke_llm.py` trong mạng công ty; (c) duyệt 8 mục `lookup:` cho `rules.yaml` và quy tắc "kiểm hợp lý"; (d) tìm cách đo false positive vì bản đã ký không sạch.

> **Bàn giao sang phiên chat mới: `docs/handoff-prompt.md`** (cập nhật 2026-09-04) —
> chép nguyên phần sau dấu `---` vào ô chat của phiên mới.

> **Tiến độ (2026-08-26):** 0.1–0.4 **đã xong cho cả bốn nguồn**. 10 quy tắc phát hiện
> sót khi rà độ phủ (R101–R110) nay đều có công thức hoặc tiêu chí:
> **77 quy tắc ĐL** ở `rules-formulas.md`, **30 quy tắc ĐT** có tiêu chí ở
> `rules-criteria.md`, **37 quy tắc `CL-*` Vòng 1** dùng tiêu chí mặc định chung.
>
> **0.5 KHÔNG còn bị chặn (2026-08-26).** Ba việc chốt ở `rules-crossmap.md` mục 7 đã
> xong: hiệu lực tài liệu (vốn đã xong, chỉ chưa tick), hai trục phân loại (đã xong,
> nhưng vá thêm `tat_ca`/`tai_lieu` cho ~21 quy tắc không gắn được thiết bị), hệ mã
> chính thức (lược đồ đã chốt, danh sách nhóm đã kiểm đủ). **Số trang đã thống nhất
> về số trang in** trên cả bộ tài liệu, kiểm chéo 0 lệch.

---

## GIAI ĐOẠN 0 — Chuẩn bị tri thức & dữ liệu  (1–1.5 tuần)

> Đây là giai đoạn quyết định trần chất lượng. Phần lớn là việc nghiệp vụ thủ
> công, KHÔNG giao cho AI. **Chưa xong GĐ 0 thì chưa viết code xử lý.**

> **BỐN NGUỒN QUY TẮC** — mục 0.1–0.4 phải phủ hết, không chỉ Guideline:
> 1. **Guideline** GL.CNVTQĐ.CNTT.18 lần 07 → **110 quy tắc** `R01–R110`
> 2. **Code web app hiện hành** → 46 quy tắc (`KPI-01`, `MDB-01`…)
> 3. **Checklist thẩm định** (nhận 2026-08-25) → **57 mục** `CL-<TT>` ⬅ **nguồn mới**
> 4. **Văn bản khác** — 849/QĐ (dự phòng, DC-DR), quy hoạch zone (FW/LB), bền vững
>    → `docs/rules/rules-nguon-khac.md`. Mới có quy tắc lõi, chờ văn bản đầy đủ.

- [x] 0.1 — Rà soát tài liệu tiêu chí, liệt kê mọi quy tắc thành danh sách phẳng
      **→ XONG cho cả bốn nguồn (2026-08-25).**
      → ⚠️ **Cần rà lại độ phủ.** Khi làm 0.4 phát hiện trang 9 sót 2 câu quy tắc →
      đã bổ sung **R101** (cơ chế dự phòng theo mức độ quan trọng) và **R102**
      (mức dự phòng căn cứ phân loại hệ thống) vào `rules-flat-draft.md` mục
      "BỔ SUNG". Nếu một trang sót 2 câu thì trang khác cũng có thể sót.
      → ✅ Guideline: **110 quy tắc R01–R110** — `docs/rules/rules-flat-draft.md`
      (100 ban đầu + 10 phát hiện sót khi rà độ phủ ở mục 0.2)
      → ✅ Code web app: **46 quy tắc** — `docs/0.1-danh-sach-quy-tac.md` phần A;
      đối chiếu hai nguồn (~15 quy tắc trùng): `docs/rules/rules-crossmap.md`
      → ✅ Văn bản khác: `QD849-01`, `QD849-02`, `ZONE-01` — `docs/rules/rules-nguon-khac.md`
      → ✅ **Checklist: 57 mục → 37 quy tắc** (tham số hóa khối phân hệ) —
      `docs/rules/rules-checklist-flat.md`. Trong đó **18 trùng** với nguồn sẵn có,
      **19 mới**, 1 chờ Guideline bền vững.
- [x] 0.2 — Phân loại từng quy tắc: định lượng (→C4) hay định tính (→C5); ghi tỷ lệ
      **→ XONG 2026-08-25.** `docs/rules/rules-classification.md` PHẦN 2.
      → ✅ **Rà độ phủ 0.1** bằng `scripts/audit_rule_coverage.py`: Guideline
      **100 → 110 quy tắc** (10 quy tắc bị sót, gồm R101 và R105 là định lượng).
      Sau khi bổ sung: **0 trang bị gắn cờ**.
      → ✅ Phân loại theo nguồn: Guideline 110 (77 ĐL/33 ĐT) · Văn bản khác 3 (3 ĐL) ·
      Code web app 46 (42 ĐL/4 ĐT) · Checklist 37 (**toàn bộ ĐT — đều là Vòng 1**).
      → ✅ **Tỷ lệ chung sau khử trùng: ~59% ĐL / ~41% ĐT** (~177 quy tắc).
      Riêng **Vòng 2 vẫn là 75/25** — phần định tính tăng thêm nằm trọn ở Vòng 1,
      và 37 quy tắc Vòng 1 dùng **chung một tiêu chí**, nên độ tin cậy cao.
      → ⚠️ Sửa 2 lỗi đếm cũ: code web app là **46** quy tắc (không phải 42);
      R66 còn tag `[đt]` trong `rules-flat-draft.md` (đã sửa thành `[đl]`).
- [x] 0.3 — Với quy tắc định lượng: viết rõ công thức, tham số, ngưỡng, đơn vị
      **→ XONG 2026-08-26.** `docs/rules/rules-formulas.md` — **77 quy tắc ĐL**.
      → ✅ 75 quy tắc ĐL Guideline ban đầu.
      → ✅ **2 quy tắc ĐL mới từ rà độ phủ** (mục "BỔ SUNG" cuối file):
      `R101` (cơ chế dự phòng theo mức độ quan trọng — ánh xạ enum→enum, so theo
      **bậc** `none < active-standby < active-active`, chỉ vi phạm khi khai **thấp
      hơn** yêu cầu) và `R105` (tổng toàn hệ = Σ phân hệ **+ Σ thành phần dùng chung**
      — bỏ số hạng dùng chung sẽ báo lệch giả cho mọi bản có FW/LB).
      → ⚠️ **13 điểm `[CHƯA CHẮC]`** cần người thẩm định xác nhận (thêm 3 điểm mới:
      mức `bình thường` của R101; có cảnh báo khi dự phòng **cao hơn** yêu cầu không;
      **dung sai** của R105 — đề xuất `≤ 1 đơn vị` hoặc `≤ 0.5%`, đặt trong `globals`).
      → ✅ Checklist: **không phát sinh công thức mới nào phải viết ở đây.** Đã rà
      từng mục ĐL: `CL-2.10`, `CL-2.11`, `CL-3.x.6` trạng thái **T** → công thức là
      `QD849-01`/`QD849-02` (`rules-nguon-khac.md`); `CL-3.x.9` → đầu vào của `ZONE-01`;
      `CL-3.2.7a` (3 phân vùng `/data`, `/log`, `/backup`) dùng **tiêu chí mặc định
      Vòng 1** (đã kiểm cột Ghi chú Excel — không có tiêu chí riêng), phần Vòng 2 là
      `MDB-03/04/05` của code web app, ghi ở `docs/0.1-danh-sach-quy-tac.md`.
      `rules-formulas.md` cố ý chỉ phủ quy tắc ĐL **nguồn Guideline**.
      → ✅ Quy tắc `CL-2.9` ↔ `CL-3.x.20` trước đây ghi "chưa nguồn nào nêu"
      **nay đã có nguồn văn bản là R105**.
- [x] 0.4 — Với quy tắc định tính: viết tiêu chí "thế nào là đạt" thật cụ thể
      **→ XONG 2026-08-26.** `docs/rules/rules-criteria.md` — **30/30 quy tắc cần
      tiêu chí đã có tiêu chí**; **36/36 trích dẫn đã kiểm khớp nguyên văn**.
      → ✅ **Bước 3: 8 quy tắc ĐT mới từ rà độ phủ** (mục 5.7) — `R102`, `R103`,
      `R104`, `R106`, `R107`, `R108`, `R109`, `R110`. Đúng khuôn đã duyệt.
      Nhóm kiểm: 6 nhóm A · 2 nhóm B (`R102` chờ 849/QĐ, `R109` thủ tục).
      Nhóm mã: `ARC` 2 · `EVD` 3 · `PRC` 1 · `BAK` 1 · `ALC` 1 — `BAK` và `ALC` lần
      đầu nhận quy tắc ĐT, thêm lý do phải **gán số một lượt ở 0.5**.
      → ✅ Bước 1: phân loại 25 quy tắc ĐT + 3 mẫu, văn phong đã duyệt
      → ✅ Bước 2: **19 quy tắc còn lại** — `ARC` 4 · `EVD` 5 · `MTH` 3 · `PRC` 5 ·
      `STO` 1 · `TST` 1. Tổng **22/22 quy tắc cần tiêu chí đã có tiêu chí**
      (25 − 2 nhóm C − 1 do gộp R25+R32). **26/26 trích dẫn đã kiểm khớp nguyên văn.**
      → ✅ Bước 3 (checklist) — **nhẹ hơn dự kiến rất nhiều, gần như đã xong.**
      Chốt 2026-08-25: thẩm định chạy **hai vòng**. Vòng 1 (checklist) dùng **một
      tiêu chí mặc định duy nhất** — *"có thông tin thực chất trong tài liệu là ĐẠT"* —
      áp cho mọi mục không có tiêu chí riêng, thay vì phải viết 48 tiêu chí lẻ.
      8 mã có tiêu chí riêng thì dùng nguyên văn cột Ghi chú Excel.
      Định nghĩa đầy đủ + các ca KHÔNG ĐẠT: `docs/rules/rules-checklist-flat.md`.
      Còn lại chỉ là rà từng mục xem có rơi vào diện "có điều kiện áp dụng" không.
- [x] 0.5 — Số hóa thành `config/rules.yaml`; mỗi quy tắc có mã
      **→ XONG 2026-08-26. 150/150 quy tắc, validator báo hợp lệ.**

  | | Kết quả |
  |---|---|
  | **Bảng mã chính thức** | `docs/rules/rules-id-map.md` — **150 quy tắc / 16 nhóm**, sinh bằng `scripts/build_rule_ids.py` có kiểm tra đầy đủ tự động |
  | **Bộ quy tắc** | `config/rules.yaml` — **151 quy tắc** (2026-09-03) · 101 định lượng / 50 định tính · 131 Vòng 2 / 20 Vòng 1 · 37 `critical` / 81 `major` / 33 `minor` |

  → ➕ **`PRC-11` bổ sung 2026-09-03** (người dùng duyệt): *"Phải nêu mục đích sizing —
  định cỡ mới hay bổ sung cho hệ đang chạy"*, `checklist_ref: CL-2.1`, Vòng 1, `major`.
  Trước đó `CL-2.1` bị xếp trạng thái **T** (trùng) và chỉ gắn `checklist_ref` vào nhóm
  `MTH`, nên **không quy tắc nào** kiểm được việc tài liệu có nêu mục đích sizing hay
  không — dò `rules.yaml` cho "mục đích sizing" được **0 khớp**. Căn cứ: **17 nhãn**
  trong eval set từ PNX nhiều hồ sơ. `MTH-01..04` là Vòng 2 về *phương pháp*; `PRC-11`
  là Vòng 1 về *sự có mặt của thông tin*. Bảng mã `rules-id-map.md` đã cập nhật tay —
  ⚠️ `build_rule_ids.py` đọc từ tài liệu nguồn, **không** đọc `rules.yaml`, chạy lại sẽ
  xóa mất dòng này.
  | **Validator** | `scripts/validate_rules.py` — chạy sau mỗi lần sửa; có `--coverage` |

  **Từ 196 quy tắc thô xuống 150.** 18 mục checklist trạng thái **T** chỉ gắn
  `checklist_ref`; 19 quy tắc code web app **gộp** vào quy tắc Guideline (thêm
  `code_ref`); 9 quy tắc **loại** có ghi lý do — trong đó 4 quy tắc là **code đang
  chạy sai** (`RDS-04`, `RDS-10`, `LBF-01`, `LBF-02`): số hóa theo Guideline cho
  đúng, KHÔNG số hóa công thức sai.

  → 🔧 **Lược đồ phải mở rộng 3 chỗ**, phát hiện khi viết quy tắc thật:
  **`check`** (bất đẳng thức — `formula`+`compare_with` chỉ diễn đạt được phép BẰNG,
  trong khi phần lớn quy tắc KPI là "≤") · **`applies_when`** (điều kiện loại trừ —
  không có nó thì 4 quy tắc `MTH` cùng chạy và sinh 3 finding sai cho MỌI bản sizing) ·
  **`role: lookup`** (đánh dấu tham số là khóa tra bảng, không xuất hiện trong biểu thức).
  Thêm 2 giá trị `equipment_types` (`tat_ca`, `tai_lieu`) và ~30 hằng số `globals`.

  → ⚠️ **4 quy tắc `enabled: false`**, mỗi cái một lý do đã ghi rõ trong `note`:
  `KPI-15` (Datanode ≤50% — `datanode_kpi` là `null`, bật lên là vi phạm NT2) ·
  `KPI-16` (tăng trưởng 1 năm — mâu thuẫn chưa giải với `ALC-01` quy định 6 tháng) ·
  `PRC-04` (mẫu Phụ lục 01 — chưa có tài liệu) ·
  `PRC-08` (mức độ SR — chưa rõ có nằm trong tài liệu sizing không).

  → ⚠️ **19 quy tắc mang điểm `[CHƯA CHẮC]` / `[CẦN XÁC NHẬN]`** và **20 quy tắc
  `source_doc: "Quy ước nội bộ — chưa có văn bản"`** (ngưỡng Redis/Kafka/MariaDB từ
  code web app). Tất cả đều `severity: minor` + `confidence_floor: high` cho tới khi
  có căn cứ văn bản.

  → ✅ Đã kiểm: mọi `see_also` trỏ tới mã có thật · mọi `checklist_ref` đúng định dạng ·
  mọi quy tắc Vòng 1 đều có `checklist_ref` · **không quy tắc nào thiếu `source_doc`** (NT2).

  → ⬜ **Còn lại của 0.5:** `CL-2.1` và `CL-2.4` chồng lấn (đều về cơ sở/dạng định cỡ) —
  đang để riêng, cân nhắc gộp sau khi có ý kiến đơn vị thẩm định.

  **Tiêu chí hoàn thành của 0.5 chưa đạt hết:** cần *"một người thứ hai đọc `rules.yaml`
  và xác nhận phản ánh đúng tài liệu gốc"*. Đây là việc của người, không phải của tôi.

> ## ✅ 0.6–0.8 XONG (2026-09-03) — **26 hồ sơ thật, 23 có PNX, `data/eval_set.json` đã có**
>
> `danh_sach_sizings_da_duyet/`: lô 1 (7 hồ sơ) + lô 2 (19 hồ sơ).
> PNX thay thế được vai trò của DB làm nguồn nhãn vàng. Kết quả:
> **0.6 xong (26 hồ sơ)** · **0.7 xong — 501 nhãn, 475 vào eval set, `rule_ref` gán bằng
> luật + kiểm mẫu** · **0.8 xong — DEV 14 hồ sơ/317 nhãn, TEST giữ kín 9/158** ·
> **0.11 chốt** · **0.9 số vòng thật = 1.65 (n=23)** nhưng vẫn thiếu thời gian mỗi vòng.
>
> **Rủi ro lớn nhất của dự án đã chuyển** từ *"không có dữ liệu"* sang *"nhãn do một
> tác nhân AI gán và tự kiểm — chưa có kiểm định độc lập"*, và *"bản đã ký không sạch nên
> chưa có cách đo false positive"*. Xem hạn chế ở 0.7.
>
> Phần dưới giữ lại để nhớ vì sao từng bị chặn.
>
> ## ⛔ (lịch sử) 0.6–0.9 BỊ CHẶN — hai tiền đề đã đổ (xác nhận 2026-08-26)
>
> 1. **Không còn bản gốc hồ sơ sizing nào.** `approved-sizing/` chỉ còn **53 file
>    `.md`** — tóm tắt do một AI khác (Cline) trích lại. Không một `.docx`/`.pdf`/`.xlsx`.
> 2. **DB chưa có dữ liệu phê duyệt lịch sử nào.** `project_data.*_admin_review` và
>    `projects.status_round` đều rỗng — hồ sơ cũ là bản làm **thủ công**, chưa từng đi
>    qua web app.
>
> `docs/0.7-nguon-nhan-vang.md` xây trọn trên tiền đề (2) nên **không dùng được lúc
> này** — đã ghi cảnh báo ở đầu file đó, giữ lại làm thiết kế cho tương lai.
>
> **Đây là rủi ro lớn nhất của dự án hiện giờ**, lớn hơn mọi việc kỹ thuật còn lại:
> không có hồ sơ thật thì Giai đoạn 1 **không chứng minh được giá trị**, và tiêu chí
> hoàn thành *"recall ≥ 50%"* **không đo được**.

- [x] 0.6 — Chuẩn hóa hồ sơ sizing lịch sử — **XONG cho 26 hồ sơ (lô 1 + lô 2), 2026-09-03.**
      **→ `docs/0.6-chuan-hoa-ho-so.md`** (phân tích) + **`docs/0.6-bang-metadata.md`**
      (bảng đầy đủ, **tự sinh** bằng `scripts/make_dossier_report.py` — chạy lại được
      sau mỗi lô, không chép tay).
      → ✅ **26 thư mục hồ sơ · 23 có nhãn · 42 file PNX `.docx`** đã phân tích.
      → ✅ Lô 2 phá vỡ tình trạng một người thẩm định: nay có **3 người**
      (Khanhnd23 ×20, thongnv31 ×2, Lê Đình Hoàng ×1).
      → ⚠️ **11 điểm lệch cần đơn vị xác nhận** (mục 2), đáng chú ý:
      **D1** 3 hồ sơ không dựng được nhãn (CloudCA + ARVR không có PNX;
      CAMPAIGN_PUSH_MXH chỉ có PNX dạng PDF) · **D2** số ở tên thư mục **≠ mã PYC**
      ở 4 hồ sơ (CMP, MySign, c360, callbot), Vtag không có mã PYC ·
      **D4** PNX bỏ trống ngày → vẫn không đo được thời gian mỗi vòng ·
      **D10** thư mục `PNM 57012` **chứa tài liệu của hệ thống khác** ·
      **D11** FMRA lẫn cả bản Backup_2024 và Training_2025.
      → ⬜ Quy ước đặt tên đã đề xuất nhưng **chưa đổi tên gì** — chờ duyệt.
- [x] 0.7 — Nhãn vàng — **XONG 2026-09-03, đã có `data/eval_set.json`** (có hạn chế, xem dưới).
      **→ `docs/0.7-nhan-vang-tu-pnx.md`** thay cho `0.7-nguon-nhan-vang.md` (mất tiền đề).
      → ✅ Nguồn nhãn là **PNX** — nguyên văn người thẩm định, có neo vị trí, đối chiếu
      ngược được. Thỏa NT2 theo cách 50 file `.md` không thỏa.
      → ✅ **1198 atom → 931 request → 501 NHÃN** sau khử trùng, **23 hồ sơ**.
      Loại `anchor`/`lead`/tiêu đề mục (kể cả tiêu đề đánh số *"5.1.3 …"*) để không thổi
      mẫu số; **giữ số lần lặp** trong cùng bảng để không hụt mẫu số (*"Công thức tính không
      đúng"* ×5 = 5 phân hệ, nay mỗi dòng mang đúng tiêu đề phân hệ nhờ `lead` lan sang ô dưới).
      → ✅ **`rule_ref` gán bằng luật** (`scripts/suggest_rule_refs.py`, không LLM), người
      kiểm mẫu — người dùng đổi quyết định vì 500 nhãn quá nhiều để gán tay. Mẫu kiểm
      **đóng băng** 83 id (`data/audit_sample_ids.json`), phán quyết khóa theo `label_id`.
      → ✅ **Chốt cuối** (`scripts/finalize_labels.py`): **475 nhãn vào eval set** —
      469 có `rule_ref` · 3 `khoang_trong` (bộ quy tắc chưa phủ) · 3 `khong_neo_duoc`
      (không có chủ ngữ, *"Tính toán lại số liệu"*). **26 nhãn `ngoai_pham_vi` LOẠI
      khỏi mẫu số** (chất lượng ảnh sở cứ, tham chiếu chéo, thủ tục, chính tả).
      `nguon_rule_ref`: 104 có phán quyết riêng · 397 nhận gợi ý máy nguyên.
      `vong`/`checklist_ref` **suy từ `rules.yaml`**, không gõ tay.
      → ✅ Cách tính ghi trong `meta.scoring_note`: trúng khi `rule_ref` finding ∈ danh
      sách của nhãn, cùng hồ sơ. Hai loại có cờ riêng chỉ vào recall *"so với mọi yêu cầu"*.
      → ✅ **`PRC-11` vá "mục đích sizing"** (17 nhãn) — bộ quy tắc **151**.
      → ⚠️ **HẠN CHẾ phải nêu khi công bố** (mục 6 tài liệu 0.7):
      (1) **không phải kiểm định độc lập** — gợi ý và mọi phán quyết do cùng một tác
      nhân AI; ước tính máy đúng chủ đề **≈65%** trên mẫu, chỉ để quyết định soát chỗ
      nào. (2) 397 nhãn nhận gợi ý nguyên, thường **dư mã** → recall hào phóng hơn thực;
      nên cắt bớt khi có người nghiệp vụ. (3) **Bản "đã ký" không sạch** — c360 ký với lỗi
      còn nguyên, người dùng xác nhận *sót khi duyệt, dự án gấp bypass* →
      **không dùng tập đã ký làm chuẩn false positive**. (4) Recall là *"so với người
      thẩm định"*, không phải sự thật tuyệt đối. (5) Ghép `pnx_file` ↔ phiên bản `.docx`
      để chạy thật **chưa làm** — thuộc 1.5/1.13.
      → ✅ Quyết định người dùng 2026-09-03: **ca hỗn hợp "sở cứ + ảnh mờ" → loại hẳn
      cả dòng** (4 nhãn); **QHĐC = quy hoạch định cỡ** → `PRC-07`; **3 hồ sơ không có
      PNX là vĩnh viễn** (CloudCA, ARVR, CAMPAIGN_PUSH_MXH) → ngoài eval set.
- [x] 0.8 — Chia tập phát triển / kiểm tra — **XONG 2026-09-03** → `data/eval_split.json`
      (`scripts/split_dev_test.py`).
      → Chia theo **đầu mối yêu cầu** (22 người), cân bằng tham lam theo số nhãn, seed
      cố định. **Không** chia theo người thẩm định (20/23 cùng Khanhnd23).
      → **DEV: 14 hồ sơ · 317 nhãn (67%)** — BCCS3, Data Security, VAPS, campaign, PNM,
      APIGW-Meta, FMRA, APIGee, c360, PBH, MySign, VTracking, GSCG, Vtag.
      → **TEST giữ kín: 9 hồ sơ · 158 nhãn (33%)** — SSO, CALLBASE, Mybox, callbot,
      StrongSwan, C360_Public, Mykid, CMP, MNP. **Không đọc nhãn test khi chỉnh quy
      tắc/prompt; chỉ chạy một lần ở 3.6.**
      → ⚠️ MNP (test) chỉ có sizing dạng PDF; VAPS (dev) cũng vậy — GĐ 1 chưa đọc PDF
      nên hai hồ sơ này tạm không chạy được, tập test thực dụng còn 8 hồ sơ.
- [ ] 🟡 0.9 — Đo baseline — **làm được một phần.**
      → ✅ **Số vòng TB = 1.65 từ hồ sơ THẬT** (2026-09-03, cập nhật sau lô 2):
      **23 hồ sơ có PNX** — 1 vòng ×11 · 2 vòng ×9 · 3 vòng ×3 (tổng 38/23).
      Đếm từ tiêu đề "NHẬN XÉT LẦN n" bằng `scripts/parse_pnx.py`.
      → ✅ Đối chiếu mốc gián tiếp cũ **1.92** (38 hồ sơ, từ 50 file `.md`). Lệch 0.27.
      Hai nguồn độc lập cho kết quả gần nhau → **mốc 1.6–1.9 vòng là đáng tin**.
      Với n=23 đo trực tiếp từ văn bản gốc, **1.65 nay là con số chính**; nêu kèm
      nguồn và cỡ mẫu khi công bố.
      → ❌ **Thời gian trung bình mỗi vòng: vẫn không có dữ liệu.** Nguyên nhân đã rõ:
      **cả 6 PNX bỏ trống ô ngày tháng** ("Hà Nội, ngày __ tháng __ năm 2024") — chỉ
      còn **năm**. Ngoại lệ duy nhất: Mykid có "Bảng thay đổi tài liệu" ghi
      `23/08/2024` khởi tạo → `05/12/2024` sửa theo nhận xét lần 2 (~3,5 tháng cho
      2 vòng). 5 hồ sơ còn lại **không có bảng này**.
      → **Gỡ chặn bằng:** xin sổ theo dõi PYC của đơn vị thẩm định, hoặc đề nghị điền
      ngày vào PNX từ nay. **Phải chụp baseline trước khi Copilot đi vào sử dụng.**
- [x] 0.13 *(mới)* — **Thu thập hồ sơ sizing thật** — **ĐỦ CHO GIAI ĐOẠN 1, 2026-09-03.**
      → ✅ **26 hồ sơ** ở `danh_sach_sizings_da_duyet/` (lô 1: 7, lô 2: 19), **23 có PNX**,
      **527 nhãn**. Vượt mốc *"tối thiểu ~10 bộ"* đặt ra ban đầu.
      → ✅ Lô 2 kèm **đủ các phiên bản sizing**, nên ghép được nhãn ↔ phiên bản tài liệu.
      → ✅ **Chốt 2026-09-03: 3 hồ sơ CloudCA, ARVR, CAMPAIGN_PUSH_MXH KHÔNG có PNX —
      vĩnh viễn.** Ngoài eval set; vẫn dùng cho C1 (1.5) và kho C6.
      → ⬜ **Còn nên xin thêm** (không chặn, chỉ tăng chất lượng):
      1. **Ngày tháng thẩm định** (D4) — sổ theo dõi PYC, để đo thời gian mỗi vòng (0.9).
      2. **Bản `.docx`** cho VAPS, MNP — hiện chỉ có PDF (D8); cả hai đang nằm trong
         tập dev/test nên GĐ 1 sẽ thiếu 2 hồ sơ chạy thật.
      3. Thêm hồ sơ cho **C6** (2.6/2.7) — kho bản tương tự càng nhiều càng tốt.
- [x] 0.10 — Xác minh hạ tầng — **XONG 2026-09-03.**
      **→ `docs/0.10-ket-qua-xac-minh-endpoint.md`** (bảng tự sinh + phần chốt viết tay).
      Dò bằng `scripts/probe_llm_endpoint.py`, 9 phép thử, chạy từ máy trong mạng công ty.
      → ✅ **Endpoint KHÔNG phải cụm vLLM tự host** mà là **gateway OpenAI-compatible nội
      bộ** phục vụ 6 model (Claude opus-4-6 / sonnet-4-5 / haiku-4-5, gpt-oss-120b,
      Qwen2.5-Coder-7B). Kiến trúc không đổi; nhưng **thôi gọi là "vLLM"** để không ai kỳ
      vọng `guided_json` / `max_model_len`.
      → ⚠️ **Phép thử D (`guided_json`) ĐẠT là DƯƠNG TÍNH GIẢ**: output bọc trong fence
      ```` ```json ````, mà guided decoding thật thì token đầu bắt buộc là `{` — tức tham
      số được nhận nhưng **bỏ qua**. Không có bảo đảm ràng buộc văn phạm ở máy chủ.
      **⟹ Client LUÔN validate + retry**, `response_format` chỉ là tối ưu hoá.
      → ⚠️ **Bẫy `max_tokens`**: model trả kèm `reasoning_content`; đặt 200 làm `content`
      **rỗng mà vẫn HTTP 200**, không ném lỗi. Client phải để `max_tokens ≥ 2000` và coi
      `content` rỗng là LỖI.
      → ✅ **Vision CÓ** (haiku nhận ảnh, trả lời đúng) → **C2 không phải xuống cấp
      OCR-only**; 2.3 giữ nguyên phạm vi.
      → ❌ **Embedding KHÔNG có** (`/v1/embeddings` 404/400) → **BGE-M3 chạy cục bộ**
      (`sentence-transformers`, CPU đủ cho kho nhỏ). Ảnh hưởng 1.11, C5, C6.
      → ✅ **Context 200k–1M** → 1.3 không cần chunk gắt; vẫn cắt theo mục/bảng vì
      `scope: phan_he`, không phải vì giới hạn ngữ cảnh.
      → ✅ **Rate limit thoáng** (0/10 lần 429, TB 1.8s) → GĐ 1 chưa cần hàng đợi (3.2);
      giữ retry (2.11).
      → ⬜ **Chưa chốt model chính cho C3** — phụ lục so sánh chỉ 1 đoạn × 2 lần, không đủ
      căn cứ. Chốt sau khi chạy eval thật (1.13) trên tập dev. Tạm dùng `claude-opus-4-6`
      (sạch format nhất); **không dùng `gpt-oss-120b`** cho trích xuất (2/2 lần nhầm trường).
- [x] 0.11 — Chốt **Copilot đọc bản Word nào** — **CHỐT 2026-09-03: bản người dùng
      tự viết.** Không còn giả định, đã có 7 hồ sơ thật làm bằng chứng.
      → Bằng chứng: tên file do người đặt tay (`PL07_Sizing_Mybox_update_20251803_
      hungnh46_update_20_03v2.docx`, `..._bổ sungv3.docx`) · cấu trúc bảng "Thông tin
      hệ thống" **khác nhau giữa các hồ sơ** (6 dòng ở c360/BCCS3, 7 dòng có "Mục đích"
      ở Mybox) · ảnh chụp màn hình dán tay mà PNX liên tục phàn nàn *"ảnh bị mờ"*,
      *"ảnh và bảng số liệu không đồng nhất"* · `>=` gõ tay mà thẩm định bắt bỏ.
      Không hồ sơ nào có dấu hiệu do web app sinh.
      → **Hệ quả:** C1 phải chịu định dạng lộn xộn (rủi ro R4 ở mức cao đúng như dự
      liệu), và **C2/vision không phải việc của GĐ 2 mà là nhu cầu có thật ngay từ
      đầu** — nhiều nhận xét của người thẩm định là về ảnh sở cứ.
      → ⚠️ **MNP chỉ có PDF** (D8). GĐ 1 chỉ đọc `.docx` nên hồ sơ này tạm để ngoài.
      → **1.3 hết bị chặn.**
- [ ] 0.12 — Hiệu lực tài liệu & tài liệu còn thiếu
      → ✅ **Đã nhận bản lần ban hành 07** (2026-08-25), hiệu lực 01/10/2023–01/10/2025,
      44 trang. Đã trích (`scripts/extract_pdf_text.py`) và đối chiếu với lần 06
      (`scripts/diff_guideline.py`): **KHÔNG quy tắc nào đổi** — giống nhau 97,9% ở
      các dòng có số, khác biệt chỉ ở chữ ký/lịch sử sửa đổi/mục lục.
      Báo cáo: `docs/rules/rules-lan7-doi-chieu.md`.
      → ✅ **(a) Checklist thẩm định — ĐÃ NHẬN 2026-08-25.** 57 mục.
      Bản dùng chính thức: `Checklist sizing cap phat tai nguyen HTCNTT.xlsx` — đã điền
      cột Ghi chú cho **cả 57/57 mục**, nên tiêu chí Vòng 1 có nguồn văn bản (NT2).
      Phân tích: `docs/rules/checklist-tham-dinh.md`.
      → 🟡 **(b) 849/QĐ-CNVTQĐ** — **đã có quy tắc lõi** (xác nhận 2026-08-25):
      `đặc biệt quan trọng` ⟺ có DC-DR, quan hệ hai chiều, hai kiểu vi phạm đều
      cảnh báo → `QD849-01` trong `docs/rules/rules-nguon-khac.md`.
      Vẫn cần văn bản để lấy trích dẫn và làm rõ dự phòng **nội site** theo từng mức.
      → 🟡 **(c) Guideline quy hoạch zone** — **đã có quy tắc lõi**: có đường ra
      internet/public ⟹ bắt buộc định cỡ firewall + LB theo băng thông và kích thước
      bản tin → `ZONE-01`. Vẫn cần văn bản.
      → ⬜ **(d) Guideline bền vững** — nhắc ở 3.x.19/3.x.21, chưa có gì.
      **(e) Phụ lục 02** (bảng `Cint_rated`) — đã có quy ước thay thế nên không chặn.
      **(f) Tài liệu định cỡ server GPU** — đã kiểm: lần 07 không có nội dung GPU nào.
      **(g) Phụ lục 01** (mẫu tài liệu định cỡ) — **hạ ưu tiên**: checklist đã thay
      thế được vai trò của nó cho mục 1.16; chỉ còn cần cho quy tắc R34.

**Tiêu chí hoàn thành:** một người thứ hai đọc `rules.yaml` và xác nhận phản ánh
đúng tài liệu gốc; đã có `data/eval_set.json` và báo cáo baseline.

---

## GIAI ĐOẠN 1 — MVP chỉ xử lý text  (2–3 tuần)

> Chạy đầu-cuối trên text + bảng, TẠM BỎ QUA hình ảnh. Chứng minh giá trị sớm.

### Tuần 1 — Nền tảng & bóc tách
- [x] 1.1 — Khởi tạo dự án, cấu trúc thư mục — **XONG 2026-09-03.**
      → ✅ `pyproject.toml` (hatchling, Python ≥3.11). Phụ thuộc lõi tối thiểu:
      `openai` · `pydantic` · `pyyaml` · `python-docx` · `asteval` (KHÔNG `eval()`).
      Nhóm tuỳ chọn tách riêng: `rag` (sentence-transformers + qdrant), `ocr`, `api`,
      `ui`, `dev` — GĐ 1 chỉ cần phần lõi.
      → ✅ Cấu trúc theo Phụ lục B: `src/{ingestion,vision,extraction,validators,
      retrieval,reporting,llm}` · `eval/reports` · `api` · `ui` · `tests` ·
      `data/{historical,knowledge_base}`.
      → ⚠️ **Máy này chưa có `uv`**; đã cài phụ thuộc bằng `pip` vào Python 3.12 (pyenv).
      `pyproject.toml` viết chuẩn nên `uv sync` dùng được ngay khi có `uv`.
- [x] 1.2 — Client LLM + kiểm structured output — **XONG 2026-09-03**, đã chạy thật 2026-09-04.
      **→ `src/llm/client.py`**, hiện thực đúng ba bài học của 0.10:
      (a) **luôn** strip fence ```` ```json ```` rồi **luôn** validate bằng chính model
      Pydantic — `response_format` chỉ là tối ưu hoá, không phải bảo đảm;
      (b) `max_tokens` mặc định **4000** và **`content` rỗng ném `LLMError`**, không coi
      là kết quả hợp lệ; (c) retry ≤3, mỗi lần **nhắc lại lỗi validate** cho model tự sửa;
      hết lượt thì ném `ExtractionFailed` để tầng trên tạo finding "thiếu thông tin" —
      **không bịa giá trị** (NT4).
      → ✅ **11 unit test, chạy hoàn toàn OFFLINE** (`tests/test_llm_client.py`) bằng
      transport giả. Đều là hồi quy cho lỗi THẬT quan sát ở 0.10, không phải test cho vui.
      → ✅ **Đã chạy thật 2026-09-04** (`claude-opus-4-6`, mạng công ty) —
      **`docs/1.2-ket-qua-smoke-llm.md`**. Client nói chuyện được với gateway;
      `response_format: json_schema` **được nhận** (không phải lùi về prompt thuần);
      1 lời gọi mỗi lượt trích, ~8,7s; chat 2,3s.
      → ✅ **Đọc số tiếng Việt ĐẠT 4/4** — cạm bẫy trung tâm của 1.4: `"3.500"` → 3500
      và **`"12.000"` → 12000** (không phải 12), mỗi đoạn 2/2 lần. Không vì thế bỏ
      `numbers.py`: NT1 nói code quyết định, không phải model.
      → ⚠️ **Bảng báo "0/4 trích đúng" là lỗi lược đồ THỬ, không phải lỗi model.**
      `loai_sizing` khai `str` nên JSON Schema **không có ràng buộc `enum`**; model trả
      `"định cỡ mới"` — đúng nghĩa, hợp lược đồ, chỉ không phải token mong đợi. Lược đồ
      thật ở `src/extraction/schema.py` vốn dùng `Literal`, tức **smoke test yếu hơn
      thứ nó phải kiểm**. Đã sửa sang `Literal`; cần **chạy lần 2**.
      → ⚠️ **Giá trị enum không ràng buộc thì KHÔNG ổn định**: cùng một đoạn, hai lần
      chạy cho hai chuỗi khác nhau. ⟹ C3 **không được** ánh xạ mờ chuỗi tự do sang enum;
      không khớp sau khi hết lượt retry thì để `None` + finding "thiếu thông tin" (NT4).
      → ✅ **Lần chạy 2 (2026-09-04, `temperature 0.0`, 3 model): 1.2 XONG HẲN.**
      sonnet-4-5 · opus-4-6 · haiku-4-5 đều chạy; `json_schema` được nhận, **1 lời gọi
      mỗi lượt trích** (~4,5–5,0s), chat 0,4–1,4s. **Đọc số đúng 12/12** ở cả 3 model.
      → ✅ **`Literal` đổi hành vi model**: lần 1 (`str`, không `enum`) trả chuỗi tự do;
      lần 2 **12/12 giá trị đều trong enum**, không lượt nào retry.
      → ⬜ **Không chứng minh được gateway ép schema phía máy chủ** — `lần thử = 1.00`
      không phân biệt "máy chủ ép" với "model tự tuân" (đúng bất đối xứng đã đọc sai ở
      phép thử D của 0.10). **Nhưng câu hỏi này thành vô hại**: `client.py` vốn LUÔN
      validate + retry bất kể máy chủ thế nào, nên cả hai thế giới đều đã xử lý.
      **Không còn chặn 1.7.**
      → ⚠️ **KHÔNG chốt được model chính cho C3.** Thứ hạng 4/4 > 3/4 > 2/4 là **n=4 mỗi
      model**, và **cả 3 lượt trượt nằm trên đúng một câu mơ hồ** — bảng đang đo "model
      xử lý một câu mơ hồ thế nào", không đo chất lượng trích xuất. Độ trễ gần như nhau
      nên không có lập luận tốc độ. Giữ `claude-opus-4-6` mặc định tạm, **chốt ở 1.13**
      trên tập DEV. (Cùng loại kết luận vội đã mắc với thang `confidence` ở 0.7.)
      → ⚠️ **`temperature 0.0` KHÔNG cho kết quả lặp lại được**: opus chạy cùng một đoạn
      hai lần ra hai kết quả khác nhau. ⟹ **1.13 không được chạy một lượt rồi chốt số** —
      phải lặp hoặc báo kèm biên độ dao động.
- [x] 1.3 — C1: đọc `.docx` (text, heading, bảng), giữ vị trí — **XONG 2026-09-03.**
      **→ `src/ingestion/docx_reader.py` + `src/ingestion/numbering.py`.**
      → ✅ **Chạy sạch 48/48 bản sizing thật**: 6.178 phần tử · 870 bảng · 767 ảnh
      (`scripts/try_c1_on_dossiers.py`). Ảnh KHÔNG bị bỏ im lặng — ghi thành phần tử
      `image` kèm vị trí để C2 dùng và để NT4 cảnh báo.
      → ✅ **Suy được số trang cho 45/48 (94%)** từ `w:lastRenderedPageBreak` /
      ngắt trang thủ công. 3 file không có dấu nào → `page=None` **và nói rõ trong
      `warnings`**, không đoán bừa là trang 1 (NT4).
      → ✅ **Nhận ra đề mục 47/48** (ban đầu chỉ 20/48). Ba lỗi phải sửa, đều lộ ra
      nhờ chạy trên tài liệu thật chứ không phải unit test:
      **(a)** Số mục là **đánh số tự động của Word** (`w:numPr`), không nằm trong
      text — phải đọc `numbering.xml` để dựng lại. Cấp 1 của các bản này là **số
      La Mã**, đoán bừa số Ả Rập sẽ lệch với mọi trích dẫn trong PNX.
      **(b)** Tài liệu dùng **numId riêng cho mỗi chương** ở cấp 2 nên Word hiện
      "1." lặp lại dưới mọi chương → hai mục khác nhau trùng `section`. Phải ghép
      theo **cấp heading** thành đường dẫn đầy đủ (`III.4.1`), đúng dạng PNX trích.
      **(c)** Có bản gán **"Heading 1" cho MỌI đề mục** kể cả mục con → khi text đã
      ghi rõ số thì tin con số hơn style; La Mã = cấp chương, Ả Rập = cấp dưới.
      → ✅ **Đối chiếu với PNX** (`scripts/check_section_match.py`): **11/17 (65%)**
      số mục người thẩm định trích dẫn tìm thấy đúng trong tài liệu. 6 ca trượt
      **không phải lỗi C1**: 4 do **lệch phiên bản** (campaign chỉ còn bản v3, không
      còn mục IV.1.1–IV.1.3 mà PNX nhận xét — vấn đề đã ghi ở `0.7` mục 4), 1 do
      Vtag **không đánh số đề mục** (C1 cố ý không bịa số), 1 còn lại chưa rõ.
      → ✅ **12 unit test offline** (`tests/test_docx_reader.py`), tổng 23 test qua.
      → ⬜ `tuanha3.docx` (thư mục Data Security) không nhận ra đề mục nào — liên
      quan **D11**, file này có vẻ không phải bản sizing.
- [x] 1.4 — Module chuẩn hóa đơn vị & số liệu — **XONG 2026-09-03.**
      **→ `config/units.yaml`** (bảng đơn vị là DỮ LIỆU, NT3) +
      **`src/normalization/{numbers,units,sanity}.py`** · **30 unit test**, tổng 53 test qua.
      → ✅ **Cạm bẫy trung tâm: "1.500" là 1500 hay 1,5?** Dấu chấm vừa là phân nhóm
      nghìn (kiểu Việt) vừa là dấu thập phân (kiểu Anh), tài liệu thật dùng lẫn cả hai.
      Đọc sai một lần lệch **1000 lần**. Cách xử lý theo NT4: suy theo quy ước, còn
      lưỡng nghĩa thì trả `ambiguous=True` **kèm cả hai cách đọc** để C4 xuất cảnh báo
      "không kiểm chứng được", KHÔNG lặng lẽ chọn một cách rồi tính tiếp.
      Thử trên tài liệu thật: **234 đại lượng / 12 bản, 13% lưỡng nghĩa** — đều lưỡng
      nghĩa thật (`6991.744 GB`, `17,284 TPS`).
      → ✅ **Dung lượng dùng cơ sở 1024, băng thông dùng 1000.** Đúng lỗi PNX từng bắt:
      *"Đổi từ GB ra TB phải chia 1024 chứ không phải 1000"*.
      → ✅ **`KB/s` (byte) ≠ `kb/s` (bit) — chênh đúng 8 lần**, chỉ chữ B hoa/thường
      phân biệt được. Nhóm băng thông so khớp **có phân biệt hoa thường**; viết mập mờ
      (`KBPS`) thì đánh dấu lưỡng nghĩa. Hạ hết về chữ thường là lặng lẽ sai 8 lần.
      → ✅ **Đơn vị không khai hệ số thì KHÔNG quy đổi được, không mặc định bằng 1.**
      Lỗi này test bắt được: `convert(1,"vcpu","cint")` từng âm thầm trả `1.0`, tức coi
      1 vCPU = 1 Cint — lặng lẽ ghi đè `CPU-03`/`CPU-09`, vi phạm NT3. CCU↔user cũng vậy.
      → ✅ **Lưới kiểm hợp lý** (`sanity.py`) bắt được ca thật *"3.000.000 TB cho 1.080
      người dùng"*; ngưỡng nằm trong `units.yaml` để người nghiệp vụ chỉnh (NT3), mọi
      cảnh báo kèm `computed_evidence` (NT2). Phục vụ **khoảng trống** *"kiểm hợp lý
      đơn vị số liệu đầu vào"* — **chưa** thành quy tắc trong `rules.yaml`, cần bạn duyệt.
      → ⚠️ **Lệch Phụ lục B**: thêm thư mục `src/normalization/` (Phụ lục B không có).
      Lý do: dùng chung cho cả C3 và C4, để trong một trong hai sẽ tạo phụ thuộc chéo.
- [x] 1.5 — Chạy C1 trên toàn bộ bản lịch sử — **XONG 2026-09-03, hết bị chặn.**
      → Đã chạy trên **47 bản sizing thật** (nhiều hơn mốc 30 ban đầu):
      `scripts/try_c1_on_dossiers.py`. Kết quả ở mục 1.3.

### Tuần 2 — Trích xuất & kiểm tra định lượng
- [x] 1.6 — Schema Pydantic `SizingCore` + `SizingExtension` — **XONG 2026-09-03.**
      **→ `src/extraction/schema.py`** + `src/reporting/finding.py` (lược đồ Finding).
      → ✅ **KHÔNG khai cứng 203 trường.** 151 quy tắc tham chiếu **203 tên tham số
      khác nhau**, phần lớn dùng đúng một lần. Khai hết thành thuộc tính sẽ tạo một
      lớp khổng lồ phải sửa mỗi lần thêm quy tắc — trái NT3, vì thêm quy tắc lẽ ra chỉ
      phải sửa `rules.yaml`. Dùng **túi tham số có xuất xứ** (`params: dict[str,
      ExtractedValue]`), khoá đúng bằng tên trong `inputs`.
      → ✅ Mỗi giá trị mang `location`/`raw` (NT2 cần dẫn nguồn) và `ambiguous` (nối
      với 1.4). **`value=None` nghĩa là KHÔNG TÌM THẤY**, không bao giờ thay bằng giá
      trị mặc định phỏng đoán.
      → ✅ `scope_keys()` sinh đúng lượt chấm cho `he_thong` / `phan_he` /
      `phan_he_x_cong_nghe_luu_tru`; `get()` ưu tiên phân hệ rồi lùi về cấp tài liệu.
- [x] 1.7 — C3: trích trường bằng structured output — **XONG 2026-09-04** (phần code).
      **→ `src/extraction/plan.py` + `src/extraction/extractor.py`** · **19 unit test**
      (`tests/test_extraction.py`), tổng **109 test** qua, chạy offline bằng transport giả.
      → ✅ **Danh sách trường phải trích SUY TỪ `rules.yaml`, không hard-code** (NT3):
      **237 tham số** đọc ra từ `inputs` + `compare_with`. Thêm quy tắc mới thì C3 tự
      biết phải trích thêm gì, không phải sửa Python.
      → ✅ **Phát hiện: `unit` trong `rules.yaml` đang gánh HAI VAI** — vừa là đơn vị đo
      (`GB`, `IOPS`, `%`) vừa là **kiểu dữ liệu** (`đúng/sai` = boolean với 28 tham số;
      `ao_hoa | vat_ly | bare_metal` = enum với 17 tham số). Không tách thì C3 sẽ hỏi
      model *"IOPS của `co_duong_ra_public` là bao nhiêu"*. Tách ngay tại chỗ đọc dữ
      liệu, không rải `if` khắp nơi. Còn lại **192 tham số kiểu số**.
      → ✅ **Model trả NGUYÊN VĂN, code mới ra số.** Không nhận `85.0` mà nhận `"85%"`,
      rồi `numbers.py` quyết định. Lý do: *"1.500"* là 1500 hay 1,5 là **quyết định dưới
      sự mơ hồ**, mà 1.4 đã dựng cả thang suy luận có cờ `ambiguous` cho đúng việc đó —
      để model trả thẳng số là đi vòng qua thang ấy và âm thầm chọn một cách đọc. 1.2 đo
      được model đọc đúng 12/12 nhưng 12 mẫu không phải căn cứ để giao việc (NT1).
      Đổi lại còn được `raw` — thứ NT2 cần để dẫn nguồn.
      → ✅ **Cổng chống bịa: trích dẫn phải NEO ĐƯỢC vào tài liệu.** Model trả kèm câu
      chứa giá trị; code tìm lại câu đó trong `DocxDocument`, **không thấy thì bỏ giá
      trị** và đếm vào `khong_neo_duoc`. Một con số không tìm lại được trong văn bản thì
      không có căn cứ (NT2) và finding dựng trên nó sẽ dẫn người dùng tới chỗ không tồn
      tại. Kiểm trên tài liệu thật: câu có thật → neo được · câu bịa → bị loại.
      → ✅ **Enum chỉ lấy khi tài liệu NÊU RÕ** — mọi enum có giá trị hợp lệ `khong_neu`,
      và `loai_sizing` còn phải neo được câu dẫn mới nhận. Trực tiếp từ phép đo 1.2
      (nêu rõ 6/6 đúng · phải suy ra 3/6 và ba model phân kỳ).
      → ✅ **Quy đổi về đúng đơn vị quy tắc dùng**: `"1,5 TB"` cho tham số khai `GB` →
      **1536**, không phải 1,5. Khác NHÓM đơn vị (khai `GB`, tài liệu ghi `Mbps`) →
      `value=None` + lý do, KHÔNG đưa số sai đơn vị cho C4 (NT4).
      → ✅ Tự bắt một lỗi mình gây ra: ngữ cảnh gửi model có tiền tố `[Mục IV.1, trang 8]`,
      model hay chép cả tiền tố vào câu trích → tự làm hỏng cổng neo của chính mình.
      Đã cắt tiền tố trước khi so, có test hồi quy.
      → 📏 **Chi phí đo được**: 31 lượt gọi cho tài liệu 1 phân hệ · 63 với 3 phân hệ ·
      95 với 5 phân hệ (~2,6–7,9 phút ở 5s/lượt). Nhóm to cắt nhỏ ≤18 trường/lượt để
      một lỗi validate không huỷ cả 55 trường của nhóm `STO`.
      → 📏 Ngữ cảnh: bản lớn nhất trong 47 bản thật là **37k ký tự**, trần đặt 60k →
      **không bản nào bị cắt**. Trần là lưới an toàn, không phải ràng buộc đang siết.
      → 🔧 **Ba sai lầm lộ ra ở lần chạy thật đầu tiên (2026-09-04), đã sửa:**
      (a) **Chi phí đo sai 8 lần.** Ước lượng cũ lấy 5s/lượt từ smoke test, thực tế
      **~40s/lượt**: smoke test chỉ có 3 trường, còn một lượt trích thật có 18 trường ×
      2 chuỗi — **token ĐẦU RA mới chi phối**, không phải ngữ cảnh.
      (b) **Giả định 3 phân hệ là sai với tài liệu thật.** BCCS3 có **13 phân hệ**
      (Database, Maxscale, 3 nhóm k8s, GoldenGate…), nên 18 lượt dự kiến hoá ra 223.
      Ước lượng nay chạy theo 1/5/13 phân hệ và nói rõ độ nhạy.
      (c) **`run()` KHÔNG truyền `section` dù `trich_nhom` có nhận** — cả 68 lượt đều
      gửi lại toàn bộ tài liệu để hỏi về MỘT phân hệ. Không chỉ tốn: hỏi về phân hệ
      Database mà đưa cả 13 phân hệ vào ngữ cảnh là **mời model lấy nhầm số của phân hệ
      khác**. Nay cắt theo mục của phân hệ, có lưới an toàn lùi về toàn văn khi mục quá
      hẹp (<400 ký tự) — thà chậm còn hơn trích thiếu.
      → ✅ **Chạy song song** (`song_song`, mặc định 6 ở script): C3 và C5 đều dùng
      `ThreadPoolExecutor`. `ThongKeDT` có **khoá riêng** vì `x += 1` trên thuộc tính
      int không nguyên tử — mất một lượt đếm là mất một dòng chẩn đoán. **Có test chứng
      minh song song cho kết quả và bộ đếm y hệt tuần tự.**
      ⚠️ Rate limit ở 0.10 chỉ đo **tuần tự** (0/10 lần 429), chưa đo đồng thời — nên
      mặc định giữ thấp.
      → 📏 **Ước lượng thật (6 luồng)**: BCCS3 13 phân hệ **223 lượt ≈ 25 phút**
      (149 phút nếu tuần tự). Cả tập dev không lọc ≈ **5,6 giờ**; `--chi-vong 1` với 8
      luồng ≈ **2,9 giờ**.
      → ⬜ **CHƯA ĐO trên tài liệu thật** — cần model. Con số phải nhìn đầu tiên là
      **`không neo được`**: trên dữ liệu giả bằng 0, trên tài liệu thật chưa ai biết, và
      nó quyết định cổng chống bịa dùng được hay phải nới.
      → 🔴 **ĐÃ ĐO TRÊN TÀI LIỆU THẬT (2026-09-04) — CHẤT LƯỢNG CHƯA DÙNG ĐƯỢC.**
      BCCS3: 68 lượt gọi · 579s (6 luồng) · **164/669 trường có giá trị** ·
      **64 không neo được**. Nhưng phần *nhận được* mới là chỗ đáng lo:
      **(a) Model gán cùng một ô bảng cho nhiều tham số khác nhau.** Bảng Database có
      `CPU (Cint) = 48`, `RAM (GB) = 500`; C3 nhận `48` cho **cả bốn** `cpu_95th`,
      `spec2017_khai`, `spec_1_cpu`, `spec_1_vcpu_khai`, và `500` cho **cả bốn**
      `dung_luong_dung_gb`, `datanode_95th`, `ram_cau_hinh_gb`, `dung_luong_ram_gb`.
      **(b) Lấy số của phân hệ KHÁC.** Phân hệ `Firewall` nhận
      `kich_thuoc_ban_ghi_byte = 500` neo vào **bảng của Database**. Cắt ngữ cảnh theo
      mục không cứu được vì C1 chỉ nhận ra **5 mục** (I, II, III, IV, 1) — **cả 13 phân
      hệ đều nằm trong mục III**.
      **(c) Giá trị vô lý mà cổng neo không chặn được**: `datanode_95th = 500%`,
      `cpu_95th_ty_le = 80` cho trường "tỷ lệ 0–1". Con số CÓ THẬT trong tài liệu, chỉ
      thuộc về trường khác.
      **(d) Model trả cả một CÂU vào ô giá trị**: `spec2006 = "Tài nguyên CPU/RAM của
      1 node database…"` → `parse_number` bắt `1` từ *"1 node"* ⇒ C4 nhận `spec2006 = 1`.
      **(e) Model tự nghĩ ra `kho_neu`** (gõ sai của `khong_neu`) cho 8 trường số, dù
      lược đồ `GiaTriSo` chỉ cho phép chuỗi rỗng.
      → ✅ **Ba cổng mới, đo được hiệu quả**: chuỗi phải TRÔNG như một giá trị (dài
      ≤30, chữ số nằm gần đầu) · giá trị phải có mặt **ngay trong phần tử đã neo**, không
      chỉ trong tài liệu · giá trị phải nằm trong **khoảng hợp lệ của đơn vị**
      (`gia_tri_hop_le` trong `units.yaml` — dữ liệu, NT3).
      Chạy lại ba cổng trên chính kết quả thật: **loại 34/174 giá trị** (14 không phải
      giá trị · 14 không có trong câu đã neo · 6 ngoài khoảng). 6 test hồi quy lấy
      nguyên văn từ `docs/smoke/c3-20260904-1621.json`.
      → ✅ Sửa `cong_nghe_luu_tru` bị chép nguyên từ `cong_nghe` ("MariaDB Database" làm
      công nghệ **lưu trữ**) — không chỉ sai nhãn mà còn khiến **mọi** phân hệ chạy thêm
      một vòng scope `phan_he_x_cong_nghe_luu_tru`, nhân đôi chi phí.
      → 🔴 **CÒN LẠI ~140 giá trị mà ba cổng KHÔNG chặn được**, vì lỗi là **gán nhầm
      tham số**: con số có thật, đúng khoảng, nằm đúng ô đã neo — chỉ là nó trả lời một
      câu hỏi khác. Cổng dựa trên *căn cứ* không phân biệt được loại lỗi này.
      → 🔴 **Nguyên nhân gốc:** C3 hỏi *"điền 18 tham số có tên này"* và model đáp lại
      bằng cách **đi tìm 18 con số**, thay vì kiểm xem tài liệu có thật sự nêu tham số đó
      không.
      → ✅ **HƯỚNG A đã chốt và triển khai 2026-09-04 — hỏi theo BẢNG.**
      **(1) Bảng vẽ lại thành lưới, giữ hàng tiêu đề.** C1 giữ `rows` cho **21/21 bảng**
      của BCCS3 nhưng C3 chỉ gửi `e.text` đã làm phẳng — tức **vứt đúng thứ cho biết con
      số nào là gì**. Bảng Database ghi rõ `CPU (Cint) | RAM (GB)`; mất cấu trúc đó thì
      `48` và `500` thành hai con số trần. Ngữ cảnh chỉ phình 7% (9.135 → 9.775 ký tự).
      **(2) Model chỉ NÓI con số ở cột nào, CODE tự đọc ô.** Thêm trường `tieu_de_cot`;
      code tìm bảng có cột đó rồi kiểm giá trị có nằm đúng cột không. Model không đặt
      được một con số vào cột nó không thuộc về, và **không tự gõ ra con số nào**.
      **(3) Cắt ngữ cảnh theo KHOẢNG PHẦN TỬ giữa hai phân hệ**, không theo `section`.
      Cắt theo mục vô dụng ở đây: cả 13 phân hệ đều nằm trong mục III, nên `Firewall`
      vẫn nhìn thấy bảng của `Database`.
      **(4) Cột nguồn hiện trong `note`** (*"lấy từ cột «CPU (Cint)» của bảng #29"*) để
      người đọc tự thấy khi con số đúng thật nhưng trả lời **nhầm câu hỏi** — loại lỗi
      không cổng tự động nào phân biệt được, nên phải để người nhìn.
      → 📏 **Lượt chạy 2 (2026-09-04 18:07) — chạy bằng code TRƯỚC hướng A**, nên chỉ
      đo được phần chạy song song: **53 lượt · 155s** (lượt 1: 68 lượt · 579s) →
      **nhanh 3,7 lần**. Phát lại các cổng hiện tại trên chính kết quả đó: **loại
      52/197 giá trị (26%)** — 19 không phải giá trị · 27 không có trong câu đã neo ·
      6 ngoài khoảng hợp lệ.
      → ✅ **`cong_nghe_luu_tru` thành `Literal`** lấy danh sách từ tham số `loai_o`
      trong `rules.yaml` (NT3). Khai `str` đã hỏng **hai lần** trên tài liệu thật: lượt 1
      model chép nguyên `cong_nghe` sang ("MariaDB Database" làm công nghệ *lưu trữ*),
      lượt 2 điền cả tiêu đề mục (*"Mục III - Định cỡ cụm máy chủ cho Database"*). Cả hai
      lần giá trị đều **khác rỗng**, nên **mọi phân hệ đều chạy thêm một vòng scope
      `phan_he_x_cong_nghe_luu_tru`** trên một trường vô nghĩa. Đúng bài học 1.2 lặp lại.
      → 📌 **Model liên tục tự nghĩ ra cách nói "không có"** cho trường số: `kho_neu`
      (lượt 1), `khoong_ghi_trong_tai_lieu` (lượt 2). Không liệt kê từng biến thể —
      cổng *"chuỗi phải chứa chữ số"* bắt được cả hai một cách tổng quát.
      → 🔧 **Lượt chạy 3 (18:37) — vẫn bằng mã CŨ, lần thứ ba liên tiếp.** Ba lượt chạy
      thật đã bị đốt vì `git pull` chưa ăn mà **không có dấu hiệu nào trên màn hình**;
      chỉ phát hiện được khi đọc kỹ file kết quả (thiếu bộ đếm mới, `cong_nghe_luu_tru`
      lại chép nguyên `cong_nghe`). ⟹ Thêm **`src/version.py`**: mọi script chạy thật
      **IN phiên bản + commit + cờ "có sửa cục bộ"** TRƯỚC khi gọi model, và ghi cả vào
      file kết quả JSON.
      → 🔴 **Lỗi thật lượt 3: hết ngân sách token đầu ra.** Nhóm `KPI/he_thong` **hỏng cả
      3 lần thử** với `finish_reason=length, max_tokens=4000`. Một lượt 18 trường phải
      sinh tới **54 chuỗi** (giá trị + câu chứa + tiêu đề cột), trong khi mặc định 4000
      đặt ra ở 0.10 là cho lời gọi **3 trường**. Sửa: ngân sách tính theo số trường
      (`1200 + 280 × số trường`) và **giảm nhóm từ 18 xuống 12 trường** — nhóm nhỏ cũng
      giảm thiệt hại khi một lượt hỏng.
      → 📏 Sau khi giảm nhóm: BCCS3 13 phân hệ còn **81 lượt** (trước 223) ≈ **9 phút**
      với 6 luồng.
      → ⬜ **Chưa đo lại trên tài liệu thật SAU hướng A** — cần chạy lại
      `try_c3_on_dossier.py`. Kiểm bằng mắt: dòng đầu phải in `C3-v4`. Con số phải nhìn là
      **`lấy từ ô bảng`** (càng cao càng tốt) so với **`cột không có thật`** +
      **`giá trị không nằm trong cột khai`**.
      → ⚠️ **1.7 tick `[x]` là cho phần CODE. Chất lượng trích xuất CHƯA đạt**; đừng coi
      C3 là dùng được cho tới khi có hướng xử lý (a)(b) ở trên.
- [x] 1.8 — Bộ nạp & diễn giải `rules.yaml` — **XONG 2026-09-03.**
      **→ `src/validators/rules_loader.py`.** Nạp 151 quy tắc + 46 hằng số, kiểm bất
      biến (mã trùng, `see_also` trỏ vào mã không có thật), lọc theo loại/vòng/scope.
      → ✅ **Không im lặng bỏ qua quy tắc nào**: `blocked()` trả về quy tắc không chạy
      được **kèm LÝ DO**. Im lặng bỏ qua là cách âm thầm làm hụt recall.
      → ✅ **90/101 quy tắc định lượng chạy được.** Ban đầu chỉ 81 — vì tiêu chí chặn
      quá thô: `role: lookup` đang gánh **hai vai** trong `rules.yaml`, (a) khoá suy ra
      hằng số Guideline (`loai_o` → `iops_toi_da_loai_o`, cần bảng) và (b) **cờ điều
      kiện** dùng trong `applies_when` (`co_duong_ra_public`, `co_kiem_thu_hieu_nang`,
      **không** cần bảng). Gộp hai vai chặn nhầm 9 quy tắc vốn chạy được.
- [x] 1.9 — C4 thực thi quy tắc định lượng bằng code — **XONG 2026-09-03.**
      **→ `src/validators/quantitative.py`.** Thuần code, không gọi LLM (NT1).
      Biểu thức đánh giá bằng **`asteval`**, không bao giờ `eval()` — quy tắc là dữ
      liệu người nghiệp vụ sửa được nên phải coi như đầu vào không tin cậy (có test
      chứng minh không chạy được lệnh hệ thống).
      → ✅ Bốn đường xuống cấp theo NT4, **không đường nào đoán giá trị**:
      thiếu đầu vào → `thieu_thong_tin` · đầu vào lưỡng nghĩa (từ 1.4) →
      `khong_kiem_chung_duoc` · bảng tra chưa số hoá → `khong_kiem_chung_duoc` nêu rõ
      thiếu bảng nào · biểu thức lỗi → báo lỗi, không nuốt.
      → ✅ `check` cho bất đẳng thức, `formula`+`compare_with`+`tolerance` cho tính lại
      — đúng quyết định 2026-08-26. Mọi finding vi phạm đều có `computed_evidence`
      (NT2), chấm đúng số lượt theo `scope` của quy tắc.
      → ✅ Chạy thử trên tài liệu rỗng: 151 lượt chấm → **124 finding đều có căn cứ**,
      toàn nhóm "thiếu thông tin" — đúng hành vi mong muốn.
      → ✅ **24 unit test** (1.6+1.8+1.9), tổng **77 test** qua, dùng bộ quy tắc THẬT.
- [x] 1.10 — C7 bản đơn giản: xuất báo cáo Markdown — **XONG 2026-09-04.**
      **→ `src/reporting/report.py`** + **`config/report_labels.yaml`** (nhãn hiển thị
      là DỮ LIỆU, NT3) · **11 unit test** (`tests/test_report.py`), tổng **88 test** qua.
      Thuần code, chạy offline. `scripts/demo_report.py` in báo cáo mẫu (đánh dấu demo).
      → ✅ **Trình bày hai vòng, Vòng 1 trước:** Vòng 1 xếp theo thứ tự checklist
      I → II → III (khối chung `CL-3.x.N` trước 3 mục riêng Database), lấy từ danh sách
      `checklist_order` trong config. Vòng 2 tách **"chưa đạt"** (`vuot_nguong`,
      `sai_cong_thuc`, `khong_nhat_quan`) khỏi **"chưa kiểm được"** (`thieu_thong_tin`,
      `khong_kiem_chung_duoc`) — nếu không, tài liệu rỗng ra ~100 dòng "thiếu thông tin"
      nhấn chìm phần có ý nghĩa (đã kiểm bằng demo: 1 chưa đạt / 101 chưa kiểm được).
      → ✅ **Luật chặn Vòng 2** nối qua `checklist_ref`: mục trượt Vòng 1 (chỉ nhóm
      `thieu_muc`/`thieu_thong_tin`; `khong_kiem_chung_duoc` CỐ Ý **không** chặn vì
      "không biết" ≠ "thiếu") thì mọi finding Vòng 2 cùng mục bị dời sang phần "Tạm
      hoãn". Khớp phạm vi đúng: trượt `he_thong` chặn tất cả; trượt phân hệ "App" chặn
      cả "App" lẫn "App/SSD". Demo xác nhận fail `CL-2.9` cấp hệ thống chặn đúng `EVD-10`.
      → ✅ **NT2 + gom/khử trùng:** lọc finding không căn cứ và **ĐẾM** (không im lặng);
      khử trùng theo `(rule_ref, scope_key, category, finding)` và đếm số gộp; xếp ưu
      tiên theo `severity`. Báo cáo mở đầu bằng câu nói rõ **đây là công cụ cố vấn**.
      → ⚠️ Nguồn finding Vòng 1 là **C5 (mục 1.12) chưa có** — C7 nhận `Finding` làm đầu
      vào, demo dựng Vòng 1 bằng tay và cờ `is_demo=True` in cảnh báo demo trong báo cáo.

### Tuần 3 — Kiểm tra định tính & giao diện thử
- [ ] 1.11 — Dựng RAG: chia nhỏ tài liệu tiêu chí, sinh embedding, nạp Qdrant
- [x] 1.12 — C5: kiểm định tính, BẮT BUỘC trích dẫn quy tắc — **XONG 2026-09-04.**
      **→ `src/validators/qualitative.py`** · **17 unit test** (`tests/test_qualitative.py`),
      tổng **126 test** qua, chạy offline bằng transport giả, dùng bộ quy tắc THẬT.
      → ✅ **Làm TRƯỚC 1.11 vì C5 KHÔNG cần RAG.** Khảo sát khi bắt đầu: cả **50 quy tắc
      định tính đã có sẵn `criteria`** (thế nào là đạt) và **`source_doc`** (trích dẫn kèm
      số trang) trong `rules.yaml`, **30 quy tắc có `examples` với ca pass/fail**. Căn cứ
      NT2 nằm sẵn trong dữ liệu; RAG là để lấy THÊM ngữ cảnh, không phải điều kiện tiên
      quyết. (1.11 còn đang vướng: `sentence-transformers` + `qdrant-client` chưa cài.)
      → ✅ **Ví dụ pass/fail làm few-shot, lấy thẳng từ `rules.yaml`** — không tự viết ví
      dụ trong code (NT3), nên ví dụ không trôi khỏi quy tắc khi quy tắc đổi.
      → ✅ **Căn cứ BẤT ĐỐI XỨNG, có chủ ý.** Phía quy tắc luôn có, lấy từ `rules.yaml`
      (`rule_quote` = `criteria`, `source_doc`) — **model không được tự nghĩ ra tiêu chí**.
      Phía tài liệu thì model trích và code phải neo lại được. Nhưng **"không đạt" thường
      là do THIẾU, mà cái thiếu thì không trích dẫn được** — nên C5 KHÔNG đòi trích dẫn
      tài liệu cho kết luận không đạt (`rule_ref` + `rule_quote` đã đủ NT2). Đòi trích dẫn
      cho ca thiếu sẽ làm C5 bỏ sót đúng loại lỗi mà Vòng 1 sinh ra để bắt.
      → ✅ **Ngược lại: model đưa trích dẫn mà code KHÔNG neo được ⇒ huỷ kết luận**, hạ
      xuống "không xác định" (`confidence: thap`). Dẫn một đoạn không có trong tài liệu là
      dấu hiệu bịa, không phải bằng chứng.
      → ✅ **`applies_when` do CODE quyết định, không hỏi model** — dùng chung
      **`src/validators/expressions.py`** (tách ra từ `quantitative.py`, vì 21/50 quy tắc
      định tính cũng có `applies_when`; chép đôi sẽ tạo hai bản dễ trôi khỏi nhau).
      Thiếu đầu vào để biết quy tắc có áp dụng hay không thì **báo "không đánh giá được",
      KHÔNG đoán là có áp dụng** — đoán sai sẽ cảnh báo về phần người dùng chưa viết tới
      (rủi ro R6). Ca này còn **không tốn lời gọi model nào**.
      → ✅ **Vòng 1 trượt sinh đúng nhóm `thieu_muc`** — chính là nhóm luật chặn của C7
      dựa vào. **Có test mạch thật C5 → C7**: `EVD-16` (Vòng 1, `CL-2.9`) trượt thì
      finding `EVD-10` (Vòng 2, cùng `CL-2.9`) bị dời sang phần "Tạm hoãn". Đây là lý do
      1.12 đáng làm sớm: C7 viết xong luật chặn từ 1.10 nhưng tới giờ **chưa có gì nuôi nó
      ngoài dữ liệu demo**.
      → ✅ **Cổng neo dùng chung** `src/ingestion/anchor.py` (tách từ C3) — cả C3 và C5
      đều phải trả lời cùng một câu: *đoạn này có thật trong tài liệu không?*
      → 📏 **Chi phí**: 48 lượt gọi cho tài liệu 1 phân hệ · 84 với 3 · 120 với 5.
      **Riêng Vòng 1 chỉ 18 / 36 / 54 lượt** (`run(chi_vong=1)`) — rẻ hơn nhiều và đúng
      thứ C7 cần nhất.
      → ⬜ **CHƯA đo trên tài liệu thật** (cần model). Con số phải nhìn là
      **`trích dẫn không neo được`**, cùng loại rủi ro với C3.
- [ ] 🟡 1.13 — Eval harness — **HẾT BỊ CHẶN. Phần code XONG 2026-09-04, chờ chạy thật.**
      **→ `eval/matching.py`** (thuần code, so khớp + tính recall) **+ `eval/run_eval.py`**
      (chạy thật, cần model) · **9 unit test**.
      → ⚠️ **Chốt chặn cũ đã LỖI THỜI**: dòng "BỊ CHẶN bởi 0.13 — nhãn neo theo vị trí
      trong web app" viết trên tiền đề **DB web app đã đổ**. Nay `data/eval_set.json` có
      **475 nhãn** từ PNX, `meta.scoring_note` định nghĩa rõ cách tính trúng, mỗi nhãn có
      `dossier` + `rule_ref`. Không còn phải ánh xạ mục Word ↔ tab web.
      → ✅ **Hai mẫu số tách rời**, lấy nguyên từ `scoring_note`, không tự nghĩ:
      *so với bộ quy tắc hiện có* (469 nhãn có `rule_ref`) và *so với mọi yêu cầu*
      (475 nhãn, gồm `khoang_trong` + `khong_neo_duoc`). Con số thứ hai luôn thấp hơn và
      **nó mới là con số nói với người dùng**.
      → ✅ **Hồ sơ chạy hỏng VẪN tính vào mẫu số** — bỏ ra sẽ làm recall đẹp lên giả tạo.
      → ✅ Báo cáo **luôn kèm 3 hạn chế** (có test): recall hào phóng vì 397 nhãn nhận
      gợi ý máy dư mã · **không đo được false positive** · nhãn chưa kiểm định độc lập.
      Finding không khớp nhãn được liệt kê để soi nhưng **cấm gọi là false positive**.
      → ⚠️ **Thiên lệch PHIÊN BẢN chưa gỡ được**: PNX nhận xét về bản TRƯỚC khi sửa, mà
      nhiều hồ sơ giữ nhiều bản `.docx` (PNM 5 bản, APIGW-Meta 3). Chạy trên bản đã sửa
      thì lỗi đã vá → **recall thấp giả tạo**. Ghép `pnx_file` ↔ phiên bản là mục còn nợ
      từ 0.7 mục 5; hiện script **liệt kê mọi bản và ghi rõ bản nào đã dùng**.
      → ✅ Tập TEST đòi cờ `--toi-hieu-rui-ro` mới chạy được, để không ai lỡ tay làm rò rỉ.
      → ✅ **Báo cáo GHI RÕ bộ lọc đã dùng** kèm cảnh báo *"không được trích như recall
      thật"* (có test). Cần vì `--nhom KPI,CPU` cho **C5 = 0 lượt** — không quy tắc định
      tính nào thuộc hai nhóm đó — nên recall thấp hẳn mà báo cáo không nói vì sao.
      → 🔧 **Sửa sau lần chạy thử đầu của người dùng trong mạng công ty (2026-09-04):**
      (a) **thiếu tiến trình** — `Extractor.run()` và `QualitativeValidator.run()` chạy
      hàng chục lượt gọi × ~5s mà **không in gì**, nhìn y hệt TREO. Nay cả hai nhận
      `on_tien_do`, pipeline gắn nhãn giai đoạn C3/C5, script in mỗi lượt một dòng.
      (b) **`--nhom` chỉ cắt C3, không cắt C5** — `--nhom KPI,CPU` cắt C3 còn 15 lượt
      nhưng C5 vẫn chạy đủ 84, tức ~99 lượt ≈ **8 phút mỗi hồ sơ** trong khi người chạy
      tưởng đang chạy rẻ. Nay `--nhom` áp cho cả hai; `--nhom-dinh-tinh` để tách khi cần.
      (c) **`--uoc-tinh`** in trước số lời gọi dự kiến rồi thoát, **không cần
      `settings.yaml`**. Đo được: cả tập dev không lọc ≈ **147 lượt/hồ sơ ≈ 172 phút**;
      `--chi-vong 1 --nhom KPI` ≈ 10 phút.
      → 🔧 **Sửa sau lượt chạy thử thứ hai (2026-09-04): `--chi 1` đốt một lượt chạy
      vào hồ sơ không chạy được.** Nó lấy hồ sơ đầu theo thứ tự chữ cái, ra đúng
      *"Cấp mới hệ thống VAPS"* — hồ sơ **duy nhất trong tập dev chỉ có PDF** (D8) — và
      nó đứng đầu bảng vì `C` hoa sắp trước `c` thường. Cả lượt **không gọi model lần
      nào**, báo cáo ra recall 0% vô nghĩa. Nay `--chi N` chỉ chọn hồ sơ **có `.docx`**,
      thêm `--ho-so <tên>` để chỉ đích danh, sắp xếp không phân biệt hoa thường, và in
      cảnh báo danh sách hồ sơ thiếu `.docx` ngay từ đầu. Hàm `chon_ho_so()` tách riêng
      để test được — 4 test.
      ⚠️ Hồ sơ thiếu `.docx` **vẫn nằm trong mẫu số của lượt chạy ĐẦY ĐỦ**; chỉ bị bỏ
      qua khi người dùng giới hạn để chạy thử.
      → ⬜ **Chưa có số recall thật** — cần model. Đây là con số quyết định tiêu chí hoàn
      thành Giai đoạn 1.
- [ ] 1.14 — Giao diện Streamlit: tải file → xem báo cáo
- [ ] 1.15 — Demo nội bộ 2–3 đồng nghiệp, thu phản hồi
- [x] 1.16 — Mẫu Word chuẩn — **XONG 2026-09-04.**
      **→ `src/reporting/mau_word.py` + `scripts/make_word_template.py`** · **8 unit test**.
      Sinh thẳng từ **57 mục checklist** (checklist vốn đã là danh mục đề mục bắt buộc,
      đúng thứ tự và phân cấp — chính là thứ Phụ lục 01 lẽ ra cung cấp). Không cần LLM.
      → ✅ **Tiêu chí đạt của từng mục chép NGUYÊN VĂN vào mẫu** làm lời nhắc, nên người
      viết thấy đúng câu người thẩm định sẽ dùng để chấm.
      → ✅ **Khối 20 mục của phần III lặp cho MỌI phân hệ**, không chỉ Application và
      Database — `--phan-he Redis,Kafka` sinh thêm bản sao đúng số phân hệ thật.
      → ✅ **Tự kiểm bằng chính C1**: mẫu sinh ra được `read_docx` đọc lại, **204 phần tử
      · 60 số mục nhận ra**. Mẫu ta phát ra mà C1 không đọc được thì vô nghĩa.
      → ✅ Vá 3 lỗi nguồn Excel lúc đọc (ô A42, dòng 18, dòng 50), **không sửa file gốc**.
- [ ] 1.17 — **Điền hộ cột C của checklist.** Đọc file Word, với mỗi mục trong 57
      mục xác định nó nằm ở trang/mục nào, xuất bản checklist đã điền sẵn cột
      "Tham chiếu theo tài liệu sizing", đánh dấu rõ mục **không tìm thấy**.
      Gần như một MVP độc lập: chỉ cần C1 + C3 + C5 nhẹ, không cần C4/C6.
      Rủi ro thấp — điền sai vị trí thì người dùng sửa vài giây, khác hẳn một cảnh
      báo sai về số liệu. Cân nhắc làm sớm để có thứ giao được cho người dùng.

**Tiêu chí hoàn thành:** ~~recall ≥ 50% trên tập phát triển~~ — **hiện KHÔNG ĐO ĐƯỢC**
(bị chặn bởi 0.13, chưa có eval set). Phần còn đo được: KHÔNG finding nào thiếu căn cứ
(mọi mục đều có `rule_ref` hoặc `computed_evidence`).

⚠️ Không được coi Giai đoạn 1 là xong khi chưa đo được recall — đó chính là con số
chứng minh công cụ có giá trị hay không.

---

## GIAI ĐOẠN 2 — Đa phương thức & tái sử dụng  (2–3 tuần)

### Tuần 4 — Xử lý hình ảnh
- [ ] 2.1 — Trích ảnh từ `.docx` kèm ngữ cảnh văn bản trước/sau
- [ ] 2.2 — Phân loại ảnh (sơ đồ / biểu đồ-dashboard / khác)
- [ ] 2.3 — C2: vision + OCR, sinh mô tả và trích số
- [ ] 2.4 — Cơ chế xuống cấp có kiểm soát: cảnh báo khi không kiểm chứng được (NT4)
- [ ] 2.5 — Kiểm tra chéo: số trong ảnh biểu đồ vs số trong bảng sizing

### Tuần 5 — Truy hồi & scale
- [ ] 🔴 2.6 — ~~Nạp 30 bản lịch sử vào vector DB~~ **BỊ CHẶN bởi 0.13**
- [ ] 🔴 2.7 — ~~C6: tìm bản tương tự~~ **BỊ CHẶN bởi 0.13.**
      ⚠️ Cả **thành phần C6** dựa hoàn toàn vào kho bản lịch sử — không có hồ sơ thật
      thì C6 không tồn tại được, không chỉ chậm.
- [ ] 2.8 — Logic scale kèm phân loại tuyến tính / phi tuyến (bảng ở docs mục C6)
- [ ] 2.9 — Sinh bản nháp đã scale kèm cảnh báo rõ cho từng tham số cần xem lại

### Tuần 6 — Củng cố
- [ ] 2.10 — Chuyển điều phối sang LangGraph nếu pipeline đã đủ phức tạp (không bắt buộc)
- [ ] 2.11 — Xử lý lỗi & timeout khi gọi LLM; cơ chế retry
- [ ] 2.12 — Cache kết quả trích xuất theo hash file
- [ ] 2.13 — Chạy lại eval set đầy đủ, so sánh với GĐ 1
- [ ] 2.14 — C7 chịu được **bản nháp chưa hoàn chỉnh**: phân biệt "người dùng chưa
      viết tới" và "thiếu hẳn", để chạy kiểm nhiều lần trong lúc soạn mà không bị
      ngập cảnh báo giả. Yêu cầu của NT4, trực tiếp giảm rủi ro R6.

**Tiêu chí hoàn thành:** recall ≥ 65% trên tập phát triển; tính năng scale được
≥ 3 người dùng thử xác nhận hữu ích.

---

## GIAI ĐOẠN 3 — Tích hợp & tinh chỉnh  (2 tuần)

### Tuần 7 — Tích hợp
- [ ] 3.1 — Bọc pipeline thành REST API FastAPI (`POST /review`, `GET /result/{id}`)
- [ ] 3.2 — Xử lý bất đồng bộ (job queue) vì thời gian chạy có thể vài phút
- [ ] 3.3 — Phối hợp thêm nút "Kiểm tra sizing" vào web nội bộ sẵn có
- [ ] 3.4 — Thiết kế hiển thị báo cáo trên web: nhóm theo mức độ, hiện trích dẫn quy tắc
      → bố cục bám theo checklist thẩm định để người thẩm định đối chiếu 1:1
- [ ] 3.5 — Đóng gói Docker Compose, triển khai môi trường nội bộ

### Tuần 8 — Tinh chỉnh & bàn giao
- [ ] 3.6 — Chạy trên tập kiểm tra GIỮ KÍN — đây mới là con số thật
- [ ] 3.7 — Phân tích false positive; siết prompt/quy tắc cho mẫu sai lặp lại
- [ ] 3.8 — Cân chỉnh ngưỡng mức độ nghiêm trọng theo phản hồi người thẩm định
- [ ] 3.9 — Tài liệu hướng dẫn sử dụng (1–2 trang, cho người không chuyên)
- [ ] 3.10 — Tài liệu vận hành: cách cập nhật `rules.yaml`, cách bổ sung bản mới
- [ ] 3.11 — Thử nghiệm thật với 3–5 đơn vị, thu phản hồi

**Tiêu chí hoàn thành:** recall ≥ 70% và false positive ≤ 20% trên tập kiểm tra
giữ kín; người thẩm định xác nhận báo cáo phù hợp cách họ đánh giá.

---

## GIAI ĐOẠN 4 — Vận hành & cải tiến  (liên tục)

- [ ] 4.1 — Vòng phản hồi: người dùng đánh dấu finding đúng/sai trên giao diện
- [ ] 4.2 — Hằng tháng: rà finding bị đánh dấu sai, điều chỉnh quy tắc/prompt
- [ ] 4.3 — Bổ sung bản sizing mới đã ký vào kho lịch sử + eval set
- [ ] 4.4 — Cập nhật `rules.yaml` khi tài liệu tiêu chí đổi; CHẠY LẠI eval set sau mỗi lần
- [ ] 4.5 — Hằng quý: báo cáo chỉ số so với baseline
- [ ] 4.6 — Khi kho đạt ~100+ bản có nhãn: cân nhắc fine-tune model trích xuất (chưa làm với 30 bản)

---

## Nhật ký quyết định

> Ghi lại các quyết định quan trọng và lý do, để không lặp lại tranh luận cũ.

| Ngày | Quyết định | Lý do |
|------|-----------|-------|
| 2026-08-23 | `config/rules.yaml` đặt ở gốc repo, dùng chung repo với app Java hiện hành | Đúng đường dẫn đã ghi trong `CLAUDE.md` và Phụ lục B; GĐ 3 sẽ phải tích hợp ngược vào chính app này. **Chưa chốt** vị trí mã nguồn Python (`src/` gốc hay `copilot/src/`) |
| 2026-08-23 | Nhãn vàng cho eval set lấy từ cột `*_admin_review` trong DB, không ghi tay | Đánh giá `OK`/`NOK` + ghi chú đã được lưu sẵn, neo đúng vị trí từng trường/dòng — chính xác hơn và không tốn công |
| 2026-08-24 | **Giữ `.docx` làm đường vào chính.** Bác phương án kiểm thẳng trên `project_data` JSON trong web app | Người dùng **soạn Word trước rồi mới nhập lại vào web** → lỗi phát sinh ở bản Word, kiểm trong web app là kiểm bản đã gõ lại, phản hồi đến sau khi việc đã rồi. 30 bản lịch sử cũng là **Word rời** nên GĐ 1 vẫn cần C1 đọc `.docx`. Dữ kiện đối lập (nếu sau này đổi): web app tự sinh `.docx` từ JSON (`ExportService.exportToDocx`) và backend không có đường tải `.docx` lên |
| 2026-08-25 | **Quy tắc có `scope` — chấm một lần / mỗi phân hệ / mỗi công nghệ lưu trữ.** Tham số hóa khối phân hệ KHÔNG có nghĩa mỗi quy tắc chỉ chấm một lần | Checklist phân rõ ba cấp Tổng quan / Application / Database. Một số mục còn ghi rõ *"tính toán độc lập cho mỗi công nghệ lưu trữ"* → cấp thứ ba. Độ mịn này khớp sẵn `moduleInstanceReviews[].instanceKey` và `storageRowReviews[].rowIndex` của web app, nên nhãn vàng trong DB dùng được ngay |
| 2026-08-25 | **Thẩm định chạy HAI VÒNG nối tiếp.** Vòng 1 = checklist, chỉ hỏi "thành phần cần có đã có chưa", tiêu chí mặc định *"có thông tin thực chất là ĐẠT"*. Vòng 2 = tài liệu định cỡ, kiểm cách tính theo Guideline. C7 chặn finding Vòng 2 cho mục trượt Vòng 1 | `OK` ở Vòng 1 chỉ nghĩa là **pass vòng checklist**, chưa nói gì về đúng/sai. Nhờ vậy 48 mục checklist không cần viết tiêu chí riêng — chỉ 8 mã có tiêu chí riêng từ cột Ghi chú Excel. Chi tiết: `docs/rules/rules-checklist-flat.md` |
| 2026-08-25 | **Checklist thẩm định là nguồn quy tắc thứ ba**, ngang hàng Guideline và code web app. Báo cáo C7 xếp theo thứ tự checklist | Checklist là công cụ người thẩm định thực sự dùng để chấm OK/NOK — nó định nghĩa đầu ra của Copilot rõ hơn cả Guideline. Guideline trả lời "định cỡ thế nào cho đúng" (C4), checklist trả lời "người thẩm định soi những gì" (C5). Chi tiết: `docs/rules/checklist-tham-dinh.md` |
| 2026-08-24 | Copilot **không** làm trợ lý soạn thảo từng bước | Người dùng soạn trên Word — môi trường không can thiệp được nếu không làm add-in. Hỗ trợ khâu tạo dồn vào C6 (GĐ 2), mẫu Word chuẩn (1.16) và kiểm bản nháp (2.14). Chi tiết: `docs/ke-hoach-trien-khai.md` mục 1.4 |
| 2026-08-26 | **Hai tiền đề dữ liệu đã đổ:** không còn bản gốc hồ sơ sizing, và DB chưa có dữ liệu phê duyệt lịch sử nào | Người dùng xác nhận hồ sơ cũ là bản làm **thủ công**, chưa từng qua web app; `approved-sizing/` chỉ còn 53 file `.md` tóm tắt. Kéo theo 0.6/0.7/0.8 bị chặn, `docs/0.7-nguon-nhan-vang.md` mất tiền đề, và các mục 1.5/1.7/1.13/2.6/2.7 cùng thành phần C6 bị chặn theo. Thêm mục **0.13 — thu thập hồ sơ sizing thật** làm đường tới hạn |
| 2026-08-26 | **KHÔNG dùng 50 file `APPRAISAL_KNOWLEDGE.md` làm nhãn vàng cho eval set** | Là diễn giải của một AI khác từ bản gốc nay đã mất, có lỗi trích xuất thấy được (`sởffff`, `THÔNG SỐ KỨ THUẬT`), không neo vào mục checklist, không đối chiếu ngược được. Dùng làm nhãn sẽ cho recall ảo và vi phạm NT2. Vẫn dùng tốt cho việc khác: **soi lại độ phủ bộ quy tắc** |
| 2026-08-26 | **Đối chiếu quy tắc chỉ đếm khớp ở TIÊU ĐỀ vấn đề, không đếm khớp trong đoạn ngữ cảnh** | Bản đầu dò từ khóa trên cả ngữ cảnh, kiểm tay 5 ca ngẫu nhiên thì 3 ca khớp nhầm ("Table format" → quy tắc dự phòng N+1). Siết lại còn tiêu đề: 810 lượt khớp-ngữ-cảnh bị loại khỏi số liệu, đổi lại con số còn lại tin được |
| 2026-08-26 | **Nhóm mã theo CHỦ ĐỀ/THIẾT BỊ, không theo module phần mềm.** Module đi vào `applies_to_module` | Guideline chia theo loại thiết bị, code web app chia theo module (MDB/RDS/KFK/K8S/LBF) — hai trục khác nhau. Gộp làm một trục sẽ buộc chọn một và mất thông tin của trục kia. Nay quy tắc Redis về RAM nằm ở nhóm `RAM` với `applies_to_module: [redis]`, tra theo cả hai chiều đều được |
| 2026-08-26 | **KHÔNG số hóa 4 công thức code đang chạy sai** (`RDS-04`, `RDS-10`, `LBF-01`, `LBF-02`); số hóa theo Guideline cho đúng | `rules.yaml` là bộ quy tắc để KIỂM, không phải bản chép lại hiện trạng. Số hóa công thức sai thì Copilot sẽ xác nhận cái sai là đúng. Đã ghi lý do trong `rules-id-map.md`; việc sửa code là của đội bảo trì web app |
| 2026-08-26 | **Loại `PRC-01`/`PRC-02` của code web app khỏi `rules.yaml`** | Đó là ràng buộc vận hành của giao diện thẩm định ("không duyệt khi còn tab chưa đánh giá"), không phải yêu cầu với bản sizing Word. Copilot không kiểm được và cũng không nên kiểm |
| 2026-08-26 | **Quy tắc định lượng dùng `check` cho bất đẳng thức, `formula` cho phép tính lại** — không dùng đồng thời | `formula` + `compare_with` + `tolerance` chỉ diễn đạt được phép BẰNG, trong khi phần lớn quy tắc ngưỡng là "≤". Ép mọi thứ vào `formula` sẽ khiến C4 phải đoán ý — nguồn lỗi âm thầm |
| 2026-08-26 | **Thống nhất số trang về SỐ TRANG IN** của Guideline lần 07 cho toàn bộ R01–R110 | Hai hệ cùng tồn tại gây tra cứu sai: R01–R100 dùng trang vật lý bản lần 06 (= trang in + 1) vì PDF đó có thêm trang chữ ký ở đầu. Đã kiểm chứng offset −1 bằng 12 phép dò độc lập **trước khi** sửa, không tin ghi chú suông. Đổi bằng `scripts/unify_page_numbers.py` (307 vị trí, 4 file), kiểm chéo bằng `scripts/check_page_consistency.py` — 0 lệch. Số trang là thứ người thẩm định dùng để mở tài liệu đối chiếu, sai một trang là mất niềm tin |
| 2026-08-26 | **Thêm `tat_ca` và `tai_lieu` vào `equipment_types`** thay vì bỏ ràng buộc bắt buộc của `applies_to_equipment` | Guideline chia chương theo loại thiết bị, nhưng ~21 quy tắc không gắn được thiết bị nào: 10 quy tắc thủ tục/phương pháp (R26, R30, R102…) và 11 mục checklist về cấu trúc tài liệu (`CL-2.2`, `CL-2.6`…). Bỏ ràng buộc thì mất khả năng lọc quy tắc theo thiết bị; liệt kê cả 10 loại cho một quy tắc về mục lục tài liệu thì vô nghĩa. Hai giá trị này giữ được cả hai. **Không** thêm `mang` cho R09/R12 — sẽ chồng lấn với 4 loại thiết bị mạng khi so khớp; khai đủ bốn loại thay thế |
| 2026-08-26 | **R101 so theo bậc, không so bằng.** `none < active-standby < active-active`; chỉ sinh finding vi phạm khi cơ chế khai **thấp hơn** mức yêu cầu, khai cao hơn thì ĐẠT | Guideline quy định mức **tối thiểu** theo phân loại hệ thống, không cấm dự phòng cao hơn. So bằng sẽ báo sai cho hệ `Quan trọng` chọn `active-active` — một cảnh báo sai thiệt hại hơn một lỗi bỏ sót. Vẫn treo `[CHƯA CHẮC]`: có nên sinh finding `minor` về chi phí không |
| 2026-08-26 | **R104 không ép đủ 11 yếu tố ảnh hưởng.** Tiêu chí neo vào *"những yếu tố bản sizing thực sự dùng trong công thức"*, không đếm đủ danh sách | Guideline liệt kê 11 yếu tố nhưng không nói yếu tố nào bắt buộc, và nhiều yếu tố không áp dụng cho mọi hệ (ví dụ "số thiết bị kết nối đồng thời" với hệ web nội bộ). Ép đủ 11 sinh cảnh báo sai hàng loạt. **Cần hỏi đơn vị thẩm định** có tập tối thiểu không |
| 2026-08-26 | **Khâu cấp phát không có mục checklist nào phủ** — ghi nhận là khoảng trống có hệ thống, không phải ca lẻ | Bốn quy tắc `R25+R32`, `R97`, `R108`, `R109` đều không map được sang mục checklist nào, và ba trong bốn thuộc khâu cấp phát. Nên hỏi đơn vị thẩm định xem cấp phát nằm ngoài phạm vi checklist một cách cố ý hay không, thay vì đề nghị bổ sung từng mục |
| 2026-09-03 | **Nguồn nhãn vàng là PNX, không phải DB.** Thay `docs/0.7-nguon-nhan-vang.md` bằng `docs/0.7-nhan-vang-tu-pnx.md` | PNX là văn bản chính thức **do chính người thẩm định viết**, nguyên văn, có neo vị trí ("Trang 7", "Mục IV.1.1"), và còn đối chiếu ngược được với tài liệu sizing — thỏa NT2 theo đúng cách mà 50 file `.md` không thỏa. DB vẫn rỗng nên thiết kế cũ giữ làm phương án tương lai |
| 2026-09-03 | **Tách nhãn theo ĐOẠN trong ô nhận xét, và loại `anchor`/`lead` khỏi số nhãn** | Một ô nhận xét gộp tới 6 yêu cầu độc lập, mỗi cái ứng một quy tắc khác — để nguyên ô thì không gán `rule_ref` được. Ngược lại, 33 atom là neo vị trí (*"Trang 1"*, *"Nhận xét chung:"*) và 9 là dẫn nhập (*"Bổ sung sở cứ:"*); đếm chúng làm nhãn sẽ **thổi mẫu số recall**, đúng lỗi "recall ảo" đã bác ngày 2026-08-26. 170 atom → **128 nhãn** |
| 2026-09-03 | **Nhãn phải ghép với ĐÚNG phiên bản tài liệu; kiểm bằng bằng chứng trong tài liệu, không suy đoán** | PNX nhận xét bản NỘP nhưng file còn lại thường là bản ĐÃ SỬA — chạy Copilot trên bản đã sửa sẽ cho recall gần 0 dù công cụ hoàn toàn đúng. Đã kiểm từng hồ sơ xem lỗi PNX nêu **còn hay đã mất** (c360 vẫn còn `>=` và thiếu "Mục đích" → bản nộp; Mybox đã thêm "Mục đích" nhưng còn `>=` → bản sau lần 1; Mykid có Bảng thay đổi ghi rõ đã sửa theo lần 2). Kết quả: **55/128 nhãn** ghép được |
| 2026-09-03 | **Hồ sơ ĐÃ SỬA VÀ ĐÃ DUYỆT dùng làm tập đo FALSE POSITIVE, không vứt đi** | Trên bản đã được người thẩm định chấp nhận, Copilot **phải im lặng**; mọi finding Vòng 2 ở đó nhiều khả năng là báo động giả. Kế hoạch cũ không có tập này, trong khi tiêu chí GĐ 3 đòi *"false positive ≤ 20%"*. Biến một hạn chế của dữ liệu thành một phép đo có ích |
| 2026-09-03 | **0.11 chốt: Copilot đọc bản Word NGƯỜI DÙNG TỰ VIẾT** | 7 hồ sơ thật không có hồ sơ nào do web app sinh: tên file đặt tay kèm handle cá nhân, bảng "Thông tin hệ thống" số dòng khác nhau giữa các hồ sơ, ảnh chụp dán tay bị thẩm định phàn nàn *"ảnh bị mờ"*, `>=` gõ tay. Hệ quả: rủi ro R4 cao đúng dự liệu, và **C2/vision là nhu cầu có thật ngay từ đầu** chứ không phải việc để dành GĐ 2 |
| 2026-09-03 | **0.8 chia tập theo ĐẦU MỐI YÊU CẦU, không theo người thẩm định** | Cả 7 hồ sơ lô 1 cùng một người thẩm định (Khanhnd23) nên trục đó không chia được; 7 đầu mối yêu cầu thì khác nhau. Vẫn hoãn 0.8 tới khi đủ hồ sơ — chia 2/3–1/3 trên 4 hồ sơ dùng được là vô nghĩa thống kê |
| 2026-09-03 | **Khử trùng giữa các phiên bản PNX phải GIỮ số lần lặp trong cùng một bảng** | Trong một bảng lần 1 của Vtag, *"Công thức tính không đúng"* xuất hiện **5 lần ở 5 dòng** — cùng một lỗi nêu cho **5 phân hệ khác nhau**, tức 5 finding riêng biệt (đúng `scope: phan_he` đã chốt 2026-08-25). Khử trùng theo văn bản đơn thuần gộp 5 thành 1 và **làm hụt mẫu số recall** — hỏng ngang với việc thổi mẫu số bằng `anchor`. Quy tắc: trong nhóm `(hồ sơ, lần, nội dung)` lấy số lần lặp của phiên bản báo nhiều nhất |
| 2026-09-03 | **Khóa so sánh khi khử trùng bỏ mọi ký tự không phải chữ/số** | PNX bản sau chép lại bản trước nhưng sửa hình thức: thêm `- ` đầu dòng, đổi khoảng trắng trong danh sách số (`226;12.6;25.1…` → `226; 12.6; 25.1;…`), thêm dấu chấm cuối. So theo từ thì 16 nhãn của Vtag bị coi nhầm là nhãn mới. **Văn bản nhãn lưu lại vẫn giữ nguyên vẹn** — chỉ khóa so sánh mới chuẩn hóa (NT2) |
| 2026-09-03 | **Hợp nhất (union) mọi phiên bản PNX, không chọn "bản đầy đủ nhất"** | Giả định *"bản sau là tập cha của bản trước"* không đứng vững: GSCG v3 có lần 1–3 còn v4 chỉ có lần 1–2. Chọn một bản sẽ âm thầm mất nhãn. Hợp nhất rồi khử trùng thì không bao giờ mất |
| 2026-09-03 | **Bảng metadata hồ sơ để script TỰ SINH (`docs/0.6-bang-metadata.md`), không chép tay** | 26 hồ sơ × 9 cột là quá nhiều để chép tay mà không sai, và mỗi lô mới lại phải chép lại. Tách phần tự sinh khỏi phần phân tích viết tay giữ được cả tính chính xác lẫn chỗ để ghi nhận xét |
| 2026-09-03 | **ĐỔI QUYẾT ĐỊNH: máy gợi ý `rule_ref`, người kiểm mẫu ngẫu nhiên** (thay cho "chỉ người gán") | 517 nhãn là quá nhiều để gán tay. Người dùng quyết định đổi cách làm. Để việc kiểm mẫu vẫn có giá trị: gợi ý đi vào cột **riêng** `rule_ref_goi_y` kèm `do_tin_cay` và `can_cu_goi_y` (mẫu nào đã khớp), cột `rule_ref` chính vẫn để trống cho người xác nhận. Nhãn không có căn cứ thì **để trống, không gán bừa** (NT2) |
| 2026-09-03 | **Gán `rule_ref` bằng LUẬT trong code, KHÔNG dùng LLM** | NT1 (code quyết định, không hỏi LLM); chạy lại cho kết quả y hệt nên kiểm chứng được; phán đoán nghiệp vụ gom vào bảng `PATTERNS` ~40 dòng đọc được trong vài phút, thay vì 517 quyết định không giải thích được. Ngoài ra 0.10 chưa xác minh endpoint LLM nào |
| 2026-09-03 | **Lấy mẫu kiểm PHÂN TẦNG theo `do_tin_cay`, không lấy ngẫu nhiên phẳng** | Các mức tin cậy có độ chính xác rất khác nhau; mẫu phẳng sẽ dồn vào mức đông nhất và không nói được gì về mức yếu. Lấy cố định 15 dòng mỗi mức cho phép ước lượng riêng từng mức rồi nhân trọng số ra con số toàn bộ |
| 2026-09-03 | **Bỏ luật "dòng ngắn không có động từ là tiêu đề"**, thay bằng danh sách tiêu đề tường minh | Luật chung loại nhầm yêu cầu thật (*"Sở cứ sử dụng ssd"*, *"Lưu ý giá trị N+1"* — chủ ngữ là danh từ nên không có động từ), và nuốt cả `lead` (*"Định cỡ máy chủ worker:"*) làm mất ngữ cảnh của các dòng dưới. **Mất một nhãn thật tệ hơn sót một tiêu đề**: nhãn thiếu là finding Copilot vĩnh viễn không được tính, còn tiêu đề lọt vào thì không khớp quy tắc nào và bị bắt khi soát |
| 2026-09-03 | **"Chất lượng ảnh sở cứ" là NGOÀI PHẠM VI Copilot, không phải khoảng trống quy tắc** — và phải LOẠI KHỎI MẪU SỐ RECALL | Người dùng xác nhận: người thẩm định **tự soi bằng mắt** rồi yêu cầu đơn vị cung cấp lại ảnh, không phải việc AI đánh giá. Nếu vẫn để trong mẫu số thì Copilot bị trừ điểm vì không tìm ra thứ nó không được giao tìm — sai lệch đúng theo hướng làm chỉ số vô nghĩa. Ranh giới cố ý hẹp: chỉ chất lượng/tính đọc được của ảnh đã có; **thiếu hẳn sở cứ cho một con số vẫn là `PRC-01` và vẫn trong phạm vi**, dù sở cứ đó tình cờ ở dạng ảnh |
| 2026-09-03 | **Thêm `PRC-11` — quy tắc thứ 151** (*"Phải nêu mục đích sizing"*), người dùng duyệt | 17 nhãn PNX từ nhiều hồ sơ lặp lại yêu cầu này, mà dò toàn bộ `rules.yaml` được **0 khớp**. `CL-2.1` từng bị xếp trạng thái T (trùng) và chỉ gắn `checklist_ref` vào nhóm `MTH`, nhưng `MTH-01..04` là Vòng 2 về *phương pháp định cỡ*, không tạo ra yêu cầu Vòng 1 về *sự có mặt* của thông tin mục đích. Là đầu vào cho `MTH-01`/`MTH-04` và cho việc kiểm "cấp bổ sung phải tính phần TĂNG THÊM". Validator sạch sau khi thêm |
| 2026-09-03 | **Thang tin cậy `cao`/`vừa`/`thấp` KHÔNG tách được chất lượng — giữ nguyên, chỉ ghi nhận** | Mẫu 88 dòng: ba mức nằm chen nhau 67–80% trong khi sai số n=15 đã ±12 điểm ⇒ chênh lệch chủ yếu là nhiễu. ⚠️ Ở mẫu 80 dòng đầu tôi kết luận *"`vừa` (100%) tốt hơn `cao` (80%)"*; mở rộng mẫu thì thứ tự **đảo lại** — kết luận cũ đã sai vì đọc quá nhiều vào n=15. Hai mức thực sự yếu là `không xác định` (47%) và `khoảng trống` (45%) |
| 2026-09-03 | **Phán quyết kiểm mẫu khóa theo `label_id`, không theo số dòng** | Bản đầu khóa theo chỉ số dòng và hỏng ngay khi thêm tầng `ngoài phạm vi` làm mẫu phân tầng được vẽ lại — chỉ 32/80 phán quyết còn khớp. Khóa theo nhãn thì phán quyết cũ sống sót qua mọi lần lấy mẫu lại |
| 2026-09-03 | **Script phải BÁO LỖI khi phán quyết trỏ tới `label_id` không tồn tại** | Tôi từng gõ `label_id` theo trí nhớ thay vì tra, nên 5 phán quyết ghi đè **không khớp dòng nào** và 5 dòng lặng lẽ giữ phán quyết cũ đã lỗi thời — làm sai hẳn con số của tầng `ngoài phạm vi` (55% thay vì 82%). Nay sai kiểu này dừng chương trình thay vì trôi qua |
| 2026-09-03 | **Chấm mẫu 80 dòng bằng máy, và ghi rõ đây KHÔNG phải kiểm định độc lập** | Người dùng giao việc điền cả 80 dòng. Vì phần gợi ý và phần chấm do cùng một tác nhân làm, con số 72% chỉ dùng để **quyết định soát tay chỗ nào** (rút từ 517 xuống ~152 nhãn), không dùng để công bố. Cần một lát cắt do người nghiệp vụ kiểm mới có số độc lập |
| 2026-09-03 | **"Đã ký" ≠ "sạch" — KHÔNG dùng tập hồ sơ đã ký làm chuẩn false positive** | Bản c360 ký duyệt với `>=` còn nguyên trong bảng tổng hợp và thiếu "Mô hình logic"; người dùng xác nhận *sót khi duyệt vì dự án gấp, bypass*. Vậy finding của Copilot trên bản đã ký có thể là lỗi thật bị bỏ qua — coi là báo động giả sẽ sai lệch theo hướng nguy hiểm nhất. Cần cách đo FP khác (ví dụ người thẩm định chấm lại finding của Copilot trên 3–5 hồ sơ) |
| 2026-09-03 | **Ca hỗn hợp "bổ sung sở cứ + ảnh mờ" → LOẠI HẲN cả dòng** (người dùng quyết) | 4 nhãn gộp một vế trong phạm vi (`PRC-01`) với một vế ngoài phạm vi. Người dùng chọn loại hẳn thay vì giữ `PRC-01` hay tách đôi. Chấp nhận mất tối đa 4 lần được tính điểm nếu Copilot bắt đúng "thiếu sở cứ" ở đó |
| 2026-09-03 | **Ba lý do tách bạch khi một nhãn không có `rule_ref`**: `ngoai_pham_vi` (loại khỏi mẫu số) · `khoang_trong` (bộ quy tắc chưa phủ) · `khong_neo_duoc` (yêu cầu không có chủ ngữ) | Gộp chung sẽ làm recall vô nghĩa theo hai chiều: nhãn ngoài phạm vi để trong mẫu số thì Copilot bị trừ điểm oan; nhãn *"Tính toán lại số liệu"* mà ép vào `EVD-10` thì Copilot được điểm ảo. Hai loại sau vẫn ở trong `eval_set.json` với cờ riêng để đo được recall *"so với mọi yêu cầu của người thẩm định"* |
| 2026-09-03 | **Bỏ `EVD-03` khỏi mẫu chung "sở cứ"** — chỉ còn `PRC-01` | Khi soát 88 dòng, `EVD-03` (*thông số chọn phải ảnh hưởng năng lực*) bị cắt gần như mọi lần: đòi sở cứ là `PRC-01`, không phải `EVD-03`. Giữ lại sẽ tặng Copilot điểm trúng trên một quy tắc người thẩm định không hề nhắc |
| 2026-09-03 | **Mẫu kiểm ĐÓNG BĂNG theo `label_id`** (`data/audit_sample_ids.json`), không rút lại theo seed | Mỗi lần sửa parser hay bộ phân loại là dân số các mức đổi, và rút mẫu theo seed trên dân số mới là một mẫu MỚI — đã mất phán quyết hai lần vì vậy. Đóng băng id thì phán quyết sống sót; id thành tiêu đề thì tự rơi ra |
| 2026-09-03 | **`lead` đứng một mình trong ô phải lan sang các ô dưới; tiêu đề đánh số (`5.1.3 …`) là `anchor` nhưng phải bắt đầu bằng chữ hoa** | *"Định cỡ máy chủ Redis:"* nằm riêng một ô, các yêu cầu ở các ô dưới — không lan thì 5 dòng *"Công thức tính không đúng"* mất phân hệ. Regex tiêu đề đánh số bản đầu bắt nhầm *"2.9 tỉ bản ghi"* (tưởng mục 2.9) và xóa mất `lead` của dòng dưới → đòi chữ hoa sau số |
| 2026-09-03 | **0.8 chia theo đầu mối yêu cầu, cân bằng tham lam theo số nhãn, seed cố định** | 20/23 hồ sơ cùng người thẩm định nên trục đó không tách được gì; văn phong đơn vị nộp mới là thứ không được rò từ test sang dev. Cân bằng theo số nhãn (không theo số hồ sơ) để hai tập có trọng lượng thống kê tương xứng: 317/158 |
| 2026-09-03 | **`data/eval_set.json` là sản phẩm 0.7 dù nhãn do AI gán và tự kiểm** — với hạn chế ghi rõ trong `meta` | Tiêu chí hoàn thành GĐ 0 đòi "đã có `data/eval_set.json`". Chờ người gán tay 500 nhãn là không khả thi (người dùng đã quyết). Đổi lại, mọi số recall về sau **phải kèm** câu *"nhãn gán bằng luật + kiểm mẫu bởi cùng tác nhân, chưa kiểm định độc lập"* cho tới khi có người nghiệp vụ soát một lát cắt | Giả định *"bản đã ký thì sạch"* bị bằng chứng bác: bản c360 có khối chữ ký nhưng bảng "Tổng hợp đề xuất" vẫn ghi `CPU >= 143 Cint 2017`, đúng chỗ PNX bảo bỏ `>=`, và vẫn thiếu "Mô hình logic". Nếu coi bản đã ký là sạch thì Copilot bắt đúng lỗi này lại bị tính thành báo động giả — sai lệch chỉ số theo hướng nguy hiểm nhất |
| 2026-09-03 | **Dùng `base_url` + API key của model công ty (vLLM) — KHÔNG ảnh hưởng kiến trúc; chỉ ba năng lực chưa kiểm là rủi ro** | Đó chính là giả định gốc của kế hoạch (SDK `openai` trỏ `base_url`). Nhưng structured output, embedding và vision đều **chưa được xác minh trên cụm thật**, và structured output bị coi là đương nhiên dù không phải bản vLLM nào cũng bật. Viết `scripts/probe_llm_endpoint.py` (stdlib) để 0.10 thành phép đo thay vì câu hỏi treo; chốt sẵn phương án thay thế cho từng năng lực thiếu để 1.7/1.11/2.3 không xây trên cát |
| 2026-09-03 | **Mã LLM phải trung lập với nhà cung cấp OpenAI-compatible** — chỉ dựa vào những gì phép thử 0.10 ĐẠT | Người dùng phát triển từ laptop ở mạng ngoài, không với tới endpoint nội bộ. Nếu cần một endpoint thay thế để phát triển (tự chọn, cấu hình riêng, không commit), việc chuyển về cụm công ty phải là **đổi `settings.yaml`**, không đổi code. Vì vậy đường dự phòng E (prompt JSON + validate + retry) phải tồn tại trong 1.7 bất kể cụm có guided decoding hay không |
| 2026-09-03 | **Endpoint là GATEWAY OpenAI-compatible nội bộ, không phải cụm vLLM tự host — thôi dùng chữ "vLLM" trong tài liệu** | Dò thật (`0.10`) thấy 6 model: Claude opus-4-6/sonnet-4-5/haiku-4-5, gpt-oss-120b, Qwen2.5-Coder-7B. Kiến trúc không đổi (vẫn SDK `openai` + `base_url` + khóa qua biến môi trường), nhưng gọi sai tên khiến người ta kỳ vọng tính năng riêng của vLLM (`guided_json`, `max_model_len`) — chính là cái bẫy đã sập ở phép thử D |
| 2026-09-03 | **KHÔNG tin structured output của máy chủ: client LUÔN validate + retry** | Phép thử `guided_json` báo ĐẠT nhưng output **bọc trong fence ```json** — guided decoding thật ràng buộc văn phạm nên token đầu bắt buộc là `{`, không thể có fence. Tức tham số được nhận nhưng **bỏ qua**; model chỉ tình cờ trả JSON vì prompt yêu cầu. Một mẫu không phân biệt được `response_format` là thật hay cũng chỉ là model tuân lệnh. Đường an toàn duy nhất: strip fence → validate bằng chính model Pydantic → retry ≤3 → thất bại thì trả `None` + finding "thiếu thông tin", KHÔNG bịa |
| 2026-09-03 | **`max_tokens` mặc định ≥ 2000, và `content` rỗng phải coi là LỖI** | Model trả kèm `reasoning_content`; đặt `max_tokens=200` làm `content` rỗng **mà vẫn HTTP 200**, không ném exception. Đây là lỗi im lặng — nếu client coi chuỗi rỗng là kết quả hợp lệ thì C3 sẽ âm thầm trích ra rỗng cho cả tài liệu |
| 2026-09-03 | **Vision CÓ trên cụm → C2 giữ nguyên phạm vi, không xuống cấp OCR-only** | Model Claude trên gateway nhận ảnh qua `image_url` (đã thử, trả lời đúng). Phương án dự phòng OCR-only ở `ke-hoach-trien-khai.md:638` **không phải kích hoạt**. Củng cố kết luận 0.11 rằng vision là nhu cầu có thật |
| 2026-09-03 | **Embedding KHÔNG có trên cụm → BGE-M3 chạy cục bộ** | `/v1/embeddings` trả 404 với model chat, 400 "does not support Embeddings API" với gpt-oss. Kho cần nhúng rất nhỏ (151 quy tắc + Guideline 44 trang + 26 bản sizing) nên CPU đủ, không cần xin hạ tầng dựng thêm. Qdrant giữ nguyên |
| 2026-09-03 | **C1 dựng lại số mục từ `numbering.xml` và ghép theo cấp heading, thay vì lấy nguyên chuỗi Word hiển thị** | Chạy thật trên 48 bản sizing: chỉ 20/48 nhận ra đề mục nếu chỉ đọc text, vì số mục là đánh số TỰ ĐỘNG nên không nằm trong `paragraph.text`. Thêm nữa tài liệu dùng numId riêng cho mỗi chương ở cấp 2 nên Word hiện "1." lặp lại dưới mọi chương — lấy nguyên chuỗi đó thì hai mục khác nhau trùng `section` và finding không neo được. Ghép theo cấp heading ra `III.4.1`, đúng dạng người thẩm định trích trong PNX ("Mục IV.1.5"). Sau sửa: **47/48** |
| 2026-09-03 | **Khi text đã ghi rõ số mục thì tin CON SỐ hơn Heading style** | Có bản gán "Heading 1" cho mọi đề mục kể cả mục con ("1. Thông tin hệ thống" nằm dưới chương "I."), nên tin style sẽ đặt mục con ngang hàng chương. Quy ước ổn định trong mọi bản sizing thật: **số La Mã là cấp chương, số Ả Rập là cấp dưới** |
| 2026-09-03 | **C1 KHÔNG bịa số trang và KHÔNG bịa số mục khi không suy được** | 3/48 file không có dấu ngắt trang nào ⇒ `page=None` kèm cảnh báo, thay vì mặc định trang 1; Vtag không đánh số đề mục ⇒ để trống `section` thay vì tự đánh số. Số trang/số mục sai còn tệ hơn không có, vì người thẩm định dùng chúng để mở tài liệu đối chiếu (cùng lý do đã thống nhất số trang Guideline ở 2026-08-26) |
| 2026-09-03 | **Số lưỡng nghĩa ("1.500") được đánh dấu `ambiguous` kèm CẢ HAI cách đọc, không tự chọn một** | Dấu chấm vừa là phân nhóm nghìn kiểu Việt vừa là dấu thập phân kiểu Anh, và tài liệu sizing thật dùng lẫn cả hai — có khi trong cùng một bảng. Chọn thầm một cách là rủi ro lệch **1000 lần**, đúng loại lỗi làm mất niềm tin ngay. Theo NT4: trả cả hai, để C4 xuất cảnh báo "không kiểm chứng được". Đo trên tài liệu thật: 13% đại lượng rơi vào diện này |
| 2026-09-03 | **Đơn vị không khai hệ số thì KHÔNG quy đổi được — bỏ mặc định 1.0** | Unit test bắt được: `convert(1,"vcpu","cint")` âm thầm trả `1.0`, tức coi 1 vCPU = 1 Cint và **lặng lẽ ghi đè `CPU-03`/`CPU-09`** (tỷ lệ thật phụ thuộc đời CPU và mức overcommit) — vi phạm NT3. CCU↔user cũng bị 1:1 trong khi tỷ lệ đồng thời là dữ liệu đầu vào từng hệ thống. Nay các đơn vị đó nhận diện được nhưng quy đổi thì báo lỗi |
| 2026-09-03 | **Nhóm băng thông so khớp CÓ phân biệt hoa/thường** | `KB/s` (kilobyte) và `kb/s` (kilobit) chênh **đúng 8 lần** và chỉ chữ B hoa/thường phân biệt được; hạ hết về chữ thường là sai 8 lần mà không có dấu hiệu gì. Viết mập mờ (`KBPS`) thì đánh dấu lưỡng nghĩa thay vì đoán |
| 2026-09-03 | **Thêm `src/normalization/` — lệch Phụ lục B, có chủ ý** | Chuẩn hóa đơn vị/số liệu dùng chung cho cả C3 (trích xuất) lẫn C4 (kiểm định lượng); đặt vào một trong hai sẽ tạo phụ thuộc chéo giữa hai thành phần vốn phải độc lập |
| 2026-09-03 | **Schema trích xuất dùng TÚI THAM SỐ có xuất xứ, không khai cứng 203 trường** | 151 quy tắc tham chiếu 203 tên tham số, phần lớn dùng đúng một lần (`write_penalty_khai`, `dung_luong_1_tape_gb`…). Khai hết thành thuộc tính Pydantic sẽ tạo lớp khổng lồ phải sửa mỗi lần thêm quy tắc — trái NT3, vì thêm quy tắc lẽ ra chỉ phải sửa `rules.yaml`. Mỗi giá trị vẫn mang `location`/`raw` để thoả NT2, và `value=None` nghĩa là KHÔNG TÌM THẤY chứ không phải 0 |
| 2026-09-03 | **`role: lookup` trong `rules.yaml` đang gánh HAI vai khác nhau** | (a) khoá suy ra hằng số Guideline không có trong tài liệu (`loai_o` → `iops_toi_da_loai_o`) — cần bảng tra; (b) cờ bật/tắt quy tắc dùng trong `applies_when` (`co_duong_ra_public`, `co_kiem_thu_hieu_nang`) — chỉ là giá trị trích từ tài liệu, không cần bảng. Bộ nạp coi chung một vai thì chặn nhầm **9 quy tắc vốn chạy được** (81→90). Phân biệt bằng: khoá có xuất hiện trong `applies_when` hay không |
| 2026-09-03 | ⚠️ **8 quy tắc KHÔNG chạy được vì bảng tra chỉ nằm trong `note` dạng văn xuôi** — chưa vá, cần người dùng duyệt | `STO-02/03/09/13` (IOPS theo loại ổ, write penalty theo RAID), `CPU-10`, `BAK-07` (thế hệ LTO), `LAN-02`, `RCK-01` (RU theo loại thiết bị). Bảng đang viết kiểu *"NL-SAS 100 · SAS 10k 140 · SSD từ 5000"* trong `note`, máy không đọc được. **Chép bảng vào Python sẽ vi phạm NT3**, nên C4 chỉ đánh dấu `khong_kiem_chung_duoc` kèm lý do và đề nghị bổ sung mục `lookup:` vào `rules.yaml`. Sửa `rules.yaml` là việc cần duyệt |
| 2026-09-03 | **C4 báo LÝ DO cho mọi quy tắc không chạy được, không im lặng bỏ qua** | Một quy tắc bị bỏ qua âm thầm sẽ làm hụt recall mà không ai biết vì sao — nguy hiểm hơn một finding sai, vì nó không để lại dấu vết nào để lần ra |
| 2026-09-04 | **Điều phối `src/pipeline.py`: C5 chạy SAU C3 và cần kết quả C3** | Không phải vì nội dung mà vì `applies_when`: 21/50 quy tắc định tính chỉ áp dụng trong một số trường hợp, điều kiện tính từ tham số C3 trích ra. Chạy C5 trước sẽ khiến 4 quy tắc `MTH` cùng nổ trên mọi tài liệu |
| 2026-09-04 | **Cảnh báo NT4 về ảnh đặt ở pipeline, không ở C1** | Giai đoạn 1 cố ý bỏ qua ảnh (C2 thuộc GĐ 2), nhưng "bỏ qua" không được phép có nghĩa là IM LẶNG: 767 ảnh trên 47 bản thật và PNX liên tục nhận xét về ảnh sở cứ. Cảnh báo có `computed_evidence` do code đếm nên vẫn thoả NT2 dù không gắn được mã quy tắc nào |
| 2026-09-04 | **Eval (1.13): hồ sơ chạy hỏng VẪN tính vào mẫu số; finding không khớp nhãn KHÔNG được gọi là false positive** | Bỏ hồ sơ hỏng ra khỏi mẫu số làm recall đẹp lên giả tạo. Và PNX chỉ ghi những điều người thẩm định CHỌN nhận xét, không phải mọi lỗi có trong tài liệu — cộng thêm bản đã ký không sạch, nên phần "không khớp" chỉ để soi |
| 2026-09-04 | **C5 (1.12) làm TRƯỚC 1.11 vì C5 không cần RAG** | Cả 50 quy tắc định tính đã có `criteria` + `source_doc` trong `rules.yaml`, nên căn cứ NT2 nằm sẵn trong dữ liệu. RAG chỉ để lấy thêm ngữ cảnh. Cộng thêm: 1.11 cần `sentence-transformers` (kéo torch ~2GB) chưa cài, còn C5 cấp đúng thứ C7 đang thiếu — nguồn finding Vòng 1 |
| 2026-09-04 | **C5: "không đạt" KHÔNG bị đòi trích dẫn tài liệu; nhưng trích dẫn có mà neo không được thì HUỶ kết luận** | Căn cứ bất đối xứng: phía quy tắc luôn có (`rules.yaml`), phía tài liệu thì cái THIẾU không trích dẫn được. Đòi trích dẫn cho ca thiếu sẽ làm C5 bỏ sót đúng loại lỗi Vòng 1 sinh ra để bắt. Ngược lại, dẫn một đoạn không có thật là dấu hiệu bịa, không phải bằng chứng |
| 2026-09-04 | **C3 (1.7): model trả NGUYÊN VĂN, code mới quyết định con số** | *"1.500"* là 1500 hay 1,5 là quyết định dưới sự mơ hồ; 1.4 đã dựng thang suy luận có cờ `ambiguous` cho đúng việc đó. Để model trả thẳng số là đi vòng qua thang ấy và âm thầm chọn một cách đọc — sai một lần lệch 1000 lần (NT1). Đổi lại còn được `raw` cho NT2 |
| 2026-09-04 | **C3 (1.7): giá trị không NEO được vào tài liệu thì BỎ, không dùng** | Cổng chống bịa. Số không tìm lại được trong văn bản thì không có căn cứ (NT2), và finding dựng trên nó dẫn người dùng tới chỗ không tồn tại. Thà thiếu còn hơn sai — đúng thứ tự ưu tiên "chính xác hơn độ phủ" |
| 2026-09-04 | **C3 (1.7): danh sách 237 trường phải trích SUY TỪ `rules.yaml`, không hard-code** | NT3: thêm quy tắc lẽ ra chỉ phải sửa `rules.yaml`. Kèm phát hiện `unit` đang gánh hai vai (đơn vị đo ↔ kiểu dữ liệu: 28 bool, 17 enum, 192 số) — không tách thì C3 hỏi model những câu vô nghĩa |
| 2026-09-04 | **C3 (1.7): `loai_sizing` và mọi enum có `applies_when` phụ thuộc CHỈ lấy khi tài liệu nêu tường minh; mơ hồ ⟹ `None` + finding `PRC-11`, không suy diễn** | Đo thật ở 1.2: khi mục đích sizing được nêu rõ, cả 3 model đúng **6/6**; khi phải suy ra thì chỉ **3/6** và ba model phân kỳ. `loai_sizing` quyết định `applies_when` của `MTH-01..04`, nên đọc sai làm **chạy nhầm cả nhóm quy tắc phương pháp** cho toàn tài liệu — không phải hỏng một finding. Xác nhận độc lập rằng `PRC-11` (thêm 2026-09-03) bảo vệ đúng chỗ dễ sai nhất |
| 2026-09-04 | **C7 (1.10): nhãn hiển thị + thứ tự checklist là DỮ LIỆU trong `config/report_labels.yaml`, không hard-code** | Tinh thần NT3: người nghiệp vụ sửa được tên phần/mức độ và **thứ tự checklist** (`checklist_order`, 37 mã, khối chung `CL-3.x.N` trước 3 mục riêng Database) mà không đụng Python. Code chỉ nạp; thiếu khoá thì lùi về `_FALLBACK` an toàn để báo cáo không vỡ |
| 2026-09-04 | **C7 tách Vòng 2 thành "chưa đạt" và "chưa kiểm được"; `khong_kiem_chung_duoc` ở Vòng 1 KHÔNG chặn Vòng 2** | Không tách thì tài liệu rỗng ra ~100 dòng "thiếu thông tin" nhấn chìm phần có ý nghĩa (đã kiểm bằng `demo_report.py`). Chỉ `thieu_muc`/`thieu_thong_tin` ở Vòng 1 mới chặn Vòng 2 — "không biết" (số lưỡng nghĩa, ảnh chưa đọc) ≠ "thiếu", coi như thiếu sẽ chặn oan các kiểm tra vốn chạy được |
| 2026-09-04 | **Luật chặn Vòng 2 khớp phạm vi phân cấp**: trượt `he_thong` chặn mọi `scope_key`; trượt phân hệ "App" chặn cả "App" và "App/SSD" | Đúng mô hình `scope` đã chốt 2026-08-25 (`he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru`). Nếu chỉ khớp `scope_key` bằng nhau thì fail Vòng 1 ở phân hệ sẽ bỏ sót các kiểm Vòng 2 ở cấp công nghệ lưu trữ của chính phân hệ đó |
