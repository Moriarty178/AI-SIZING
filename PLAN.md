# PLAN.md — Lộ trình triển khai Sizing Copilot

> **Cách dùng file này:** đây là bảng công việc sống. Mỗi khi hoàn thành một
> mục, đánh dấu `[x]`. Không chuyển giai đoạn khi chưa đạt **Tiêu chí hoàn thành**
> của giai đoạn hiện tại. Bối cảnh và lý do đầy đủ: `docs/ke-hoach-trien-khai.md`.
> Nguyên tắc thiết kế bắt buộc: `CLAUDE.md`.

## Bảng trạng thái

| GĐ | Tên | Tiến độ | Trạng thái |
|----|-----|---------|------------|
| 0 | Chuẩn bị tri thức & dữ liệu | 10 / 13 (còn 0.9 thời gian/vòng, 0.10, 0.12) | 🟢 Đủ để sang GĐ 1 |
| 1 | MVP chỉ xử lý text | 0 / 17 | ⬜ Chưa bắt đầu |
| 2 | Đa phương thức & tái sử dụng | 0 / 14 | ⬜ Chưa bắt đầu |
| 3 | Tích hợp & tinh chỉnh | 0 / 11 | ⬜ Chưa bắt đầu |
| 4 | Vận hành & cải tiến | 0 / 6 | ⬜ Liên tục |

**Đang tập trung:** Giai đoạn 0 đã đủ điều kiện sang **Giai đoạn 1** — `config/rules.yaml` **151 quy tắc**, `data/eval_set.json` **475 nhãn**, `data/eval_split.json` đã chia dev/test. Việc kế tiếp theo thứ tự: **1.1** khởi tạo dự án (`uv`, cấu trúc thư mục), **1.2** kết nối vLLM, **1.3** C1 đọc `.docx`. Song song, việc của người: (a) kiểm độc lập một lát cắt `eval_sheet_mau_kiem_daduyet.csv`; (b) 0.10 xác minh hạ tầng; (c) tìm cách đo false positive vì bản đã ký không sạch.

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
- [ ] 🟡 0.10 — Xác minh hạ tầng: model vision, endpoint embedding, context window, rate limit
      → ✅ **Công cụ đã sẵn (2026-09-03):** `scripts/probe_llm_endpoint.py` — 9 phép thử
      A–I (models · chat · structured output 3 cách · embedding · vision · context ·
      rate limit), **chỉ dùng thư viện chuẩn**, không cần cài gì; đọc `config/settings.yaml`
      (copy từ `settings.example.yaml`, đã vào `.gitignore`) và khóa từ biến môi trường
      `SIZING_COPILOT_API_KEY`. Xuất `docs/0.10-ket-qua-xac-minh-endpoint.md`, không ghi khóa.
      → ⛔ **CHƯA CHẠY ĐƯỢC:** người dùng đang ở mạng ngoài, không với tới endpoint nội
      bộ. **Phải chạy từ máy trong mạng công ty** (copy `scripts/probe_llm_endpoint.py` +
      `config/settings.example.yaml` là đủ). Kết quả quyết định 1.7 (structured output),
      1.11 (embedding), 2.3 (vision), 1.3 (cắt tài liệu theo context).
      → Phương án thay thế đã chốt trước theo từng kết quả (xem nhật ký quyết định):
      structured output không có → prompt JSON + validate + retry; embedding không có →
      BGE-M3 cục bộ trên CPU; vision không có → C2 xuống cấp OCR-only theo NT4.
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
- [ ] 1.1 — Khởi tạo dự án, cấu trúc thư mục (docs Phụ lục B), Git, `uv`
- [ ] 1.2 — Kết nối thử vLLM: chạy `scripts/probe_llm_endpoint.py` từ máy trong mạng,
      **chốt cách structured output** (C `response_format` → D `guided_json` → E prompt +
      validate) rồi mới viết `src/llm/`. Mọi lời gọi chỉ qua `base_url` + khóa trong biến
      môi trường — không hard-code, không phụ thuộc tính năng riêng của vLLM ngoài những
      gì phép thử đã ĐẠT.
- [ ] 1.3 — C1: đọc `.docx` (text, heading, bảng), giữ vị trí phần tử
- [ ] 1.4 — Module chuẩn hóa đơn vị & số liệu + unit test riêng
- [ ] 🔴 1.5 — ~~Chạy C1 trên cả 30 bản lịch sử~~ **BỊ CHẶN bởi 0.13** — không còn bản gốc

### Tuần 2 — Trích xuất & kiểm tra định lượng
- [ ] 1.6 — Định nghĩa schema Pydantic (`SizingCore` + `SizingExtension`)
- [ ] 🔴 1.7 — C3: trích trường bằng structured output.
      Phần **đo độ chính xác** BỊ CHẶN bởi 0.13 (không có tập phát triển)
- [ ] 1.8 — Bộ nạp & diễn giải `rules.yaml`
- [ ] 1.9 — C4: thực thi quy tắc định lượng bằng code; unit test cho từng công thức
- [ ] 1.10 — C7 bản đơn giản: xuất báo cáo Markdown
      → **Trình bày theo hai vòng thẩm định**, Vòng 1 trước, Vòng 2 sau:
      Vòng 1 xếp theo thứ tự checklist (I → II → III) để người thẩm định đọc báo cáo
      và chấm checklist theo cùng một mạch; Vòng 2 là chi tiết tính toán.
      → **BẮT BUỘC: chặn finding Vòng 2 của mục đã trượt Vòng 1**, thay bằng
      "chưa đánh giá được — thiếu thông tin". Báo "công thức CPU sai" cho người chưa
      viết phần CPU là vô nghĩa và làm mất niềm tin (rủi ro R6).
      → Finding có thêm `checklist_ref` bên cạnh `rule_ref`, và nhãn vòng (1 hay 2).

### Tuần 3 — Kiểm tra định tính & giao diện thử
- [ ] 1.11 — Dựng RAG: chia nhỏ tài liệu tiêu chí, sinh embedding, nạp Qdrant
- [ ] 1.12 — C5: kiểm định tính, BẮT BUỘC trích dẫn quy tắc
- [ ] 🔴 1.13 — ~~Eval harness~~ **BỊ CHẶN bởi 0.13** — chưa có eval set
      → nhãn neo theo vị trí **trong web app**, bản sizing là **file Word rời** →
      phải so khớp qua ánh xạ mục Word ↔ tab web, không so khớp trực tiếp.
      Xem `docs/0.7-nguon-nhan-vang.md`.
- [ ] 1.14 — Giao diện Streamlit: tải file → xem báo cáo
- [ ] 1.15 — Demo nội bộ 2–3 đồng nghiệp, thu phản hồi
- [ ] 1.16 — Mẫu Word chuẩn — **KHÔNG còn bị chặn**. Trước đây phải chờ Phụ lục 01;
      nay **sinh thẳng từ 57 mục checklist**, vốn đã là danh mục đề mục bắt buộc,
      đúng thứ tự và phân cấp. Không cần LLM, không phụ thuộc thành phần nào.
      Cách rẻ nhất để đỡ người viết ngay từ khâu tạo, đồng thời kéo rủi ro R4 xuống.
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
| _(chờ)_ | 10 điểm mơ hồ/mâu thuẫn trong công thức code hiện hành | Xem `docs/0.1-danh-sach-quy-tac.md` mục C. Cần người thẩm định xác nhận trước khi số hóa vào `rules.yaml` |
