# PLAN.md — Lộ trình triển khai Sizing Copilot

> **Cách dùng file này:** đây là bảng công việc sống. Mỗi khi hoàn thành một
> mục, đánh dấu `[x]`. Không chuyển giai đoạn khi chưa đạt **Tiêu chí hoàn thành**
> của giai đoạn hiện tại. Bối cảnh và lý do đầy đủ: `docs/ke-hoach-trien-khai.md`.
> Nguyên tắc thiết kế bắt buộc: `CLAUDE.md`.

## Bảng trạng thái

| GĐ | Tên | Tiến độ | Trạng thái |
|----|-----|---------|------------|
| 0 | Chuẩn bị tri thức & dữ liệu | 4 / 12 | 🟡 Đang làm |
| 1 | MVP chỉ xử lý text | 0 / 17 | ⬜ Chưa bắt đầu |
| 2 | Đa phương thức & tái sử dụng | 0 / 14 | ⬜ Chưa bắt đầu |
| 3 | Tích hợp & tinh chỉnh | 0 / 11 | ⬜ Chưa bắt đầu |
| 4 | Vận hành & cải tiến | 0 / 6 | ⬜ Liên tục |

**Đang tập trung:** mục **0.5** — số hóa thành `config/rules.yaml`.

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
- [ ] 0.5 — Số hóa thành `config/rules.yaml` (cấu trúc ở docs, Phụ lục A); mỗi quy tắc có mã
      → khung + lược đồ + hai trục phân loại + `globals` đã đối chiếu Guideline.
      → Thêm trường **`checklist_ref`** cho mọi quy tắc; 18 mục checklist trạng thái
      **T** chỉ gắn `checklist_ref` vào quy tắc sẵn có, không tạo quy tắc mới.
      → Thêm trường **`scope`** (`he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru`)
      và **`round`** (1 = checklist, 2 = tài liệu định cỡ). Lược đồ đã có sẵn trong
      `config/rules.yaml`; giá trị từng quy tắc đã gán ở `rules-checklist-flat.md`.
      → Cân nhắc gộp `CL-2.1` và `CL-2.4` (chồng lấn về cơ sở định cỡ).
      → ~~**Quy tắc mới cần thêm:** tổng cấu hình toàn hệ thống (`CL-2.9`) phải bằng
      tổng các phân hệ (`CL-3.x.20`) — chưa nguồn nào nêu.~~ **Đã có nguồn: R105**
      (trang in 20). Không còn là quy tắc tự đề xuất → không vi phạm NT2.
      → ✅ ~~Sửa số trang trong `rules-flat-draft.md` và `rules-formulas.md`.~~
      **XONG 2026-08-26** — xem mục "Gỡ chặn 0.5" bên dưới.
      → **KHÔNG CÒN BỊ CHẶN (2026-08-26).** Ba việc "chặn 0.5" ở
      `rules-crossmap.md` mục 7 đã xong hết; chi tiết ngay dưới đây.

  **Gỡ chặn 0.5 — làm ngày 2026-08-26**

  | Việc chặn | Kết quả |
  |---|---|
  | Xác minh tài liệu còn hiệu lực | **Đã xong từ 2026-08-25**, chỉ là ô đánh dấu bị bỏ quên. `rules.yaml`: `status: active_confirmed` |
  | Chốt hai trục phân loại | **Đã xong từ 2026-08-25** (`equipment_types` + `module_types`), nhưng **phát hiện một lỗ hổng thật và đã vá** — xem dưới |
  | Chốt hệ mã chính thức | Lược đồ đã chốt trong Nhật ký quyết định; đã **kiểm danh sách 16 nhóm là đủ dùng**. Số thứ tự vẫn cố ý để lại cho chính 0.5 |
  | Thống nhất số trang | **Mới làm.** Toàn bộ R01–R110 nay dùng **số trang IN** |

  → 🔧 **Lỗ hổng đã vá trong `config/rules.yaml`:** `applies_to_equipment` là trường
  **bắt buộc**, nhưng **~21 quy tắc không gắn được với thiết bị nào** — 10 quy tắc
  thủ tục/phương pháp áp cho mọi thiết bị (R26, R30, R102…) và 11 mục checklist chỉ
  nói về cấu trúc tài liệu (`CL-2.2`, `CL-2.6`, `CL-2.8`, `CL-2.9`…). Nếu không vá
  thì 0.5 sẽ phải liệt kê cả 10 loại thiết bị cho một quy tắc về… mục lục tài liệu.
  Đã thêm hai giá trị **`tat_ca`** và **`tai_lieu`**, kèm quy ước "thiết bị mạng"
  của R09/R12 khai đủ bốn loại thay vì thêm giá trị `mang` (tránh chồng lấn).

  → 📄 **Thống nhất số trang** — trước đây hai hệ cùng tồn tại: R01–R100 dùng số
  trang vật lý bản lần 06 (= trang in + 1), R101–R110 dùng số trang in.
  - Kiểm chứng offset −1 bằng **12 phép dò độc lập** trải từ trang 8 tới trang 45
    trước khi sửa (ví dụ R09 ghi "trang 10" nhưng câu *"dự phòng 20% số port"* nằm ở
    trang in 9; R98 ghi "trang 44" nhưng `sysbench` ở trang in 43).
  - Chuyển đổi bằng `scripts/unify_page_numbers.py` — **307 vị trí** trên 4 file
    (`rules-flat-draft.md`, `rules-formulas.md`, `rules-classification.md`,
    `config/rules.yaml`). Script chỉ chạy **một lần**.
  - Kiểm chéo bằng `scripts/check_page_consistency.py` *(mới)*: **0 lệch** giữa ba
    file, mọi số trang trong 1..44. Kiểm lại với nội dung thật: **19/19 khớp**.
  - `scripts/audit_rule_coverage.py` bỏ hằng số bù trừ (`DRAFT_PAGE_OFFSET = 0`);
    chạy lại vẫn **0 trang bị gắn cờ**, số lượt quy tắc gắn trang 108 → **116**.

  → ⏸ **Ba việc còn treo nhưng KHÔNG chặn 0.5** (đều đã có cách xử lý tạm ghi ở
  `rules-crossmap.md` mục 7): báo đội web app 3 lỗi tính toán · hỏi nguồn KPI
  Datanode ≤ 50% · hỏi đơn vị thẩm định về khâu cấp phát không có mục checklist.
- [ ] 0.6 — Chuẩn hóa 30 bản sizing lịch sử: đặt tên + metadata (loại, ngày, trạng thái)
- [ ] 0.7 — Với mỗi bản, ghi lại lỗi người thẩm định đã bắt → nhãn cho eval set
      → nguồn nhãn có sẵn trong DB hệ thống hiện hành: `docs/0.7-nguon-nhan-vang.md`
      → **Đơn giản hơn dự kiến:** cột OK/NOK trong DB chính là checklist này đã số
      hóa → neo nhãn theo **mã mục checklist** (`2.10`, `3.1.13`…), không cần ánh xạ
      mục Word ↔ tab web như lo ngại ở mục 1.13
- [ ] 0.8 — Chia dữ liệu: ~20 bản tập phát triển, ~10 bản tập kiểm tra GIỮ KÍN
      → chia theo `projects.dev_unit`, không chia ngẫu nhiên
- [ ] 0.9 — Đo baseline: số vòng phản hồi TB + thời gian TB mỗi vòng hiện nay
      → tính được từ `projects.status_round`; SQL trong `docs/0.7-nguon-nhan-vang.md`.
      **Phải chụp trước khi Copilot đi vào sử dụng.**
- [ ] 0.10 — Xác minh hạ tầng: model vision, endpoint embedding, context window, rate limit
- [ ] 0.11 — Chốt **Copilot đọc bản Word nào**: bản người dùng tự viết, hay bản web
      app xuất ra (`ExportService.exportToDocx`)? Thu 3–5 mẫu thật mỗi loại.
      Khuyến nghị: bản tự viết — đúng thời điểm can thiệp, nhưng C1 phải chịu định
      dạng lộn xộn (rủi ro R4 lên mức cao). **Phải chốt trước khi bắt đầu 1.3.**
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
- [ ] 1.2 — Kết nối thử vLLM: gọi chat + kiểm tra structured output chạy được
- [ ] 1.3 — C1: đọc `.docx` (text, heading, bảng), giữ vị trí phần tử
- [ ] 1.4 — Module chuẩn hóa đơn vị & số liệu + unit test riêng
- [ ] 1.5 — Chạy C1 trên cả 30 bản lịch sử, ghi nhận ca lỗi định dạng

### Tuần 2 — Trích xuất & kiểm tra định lượng
- [ ] 1.6 — Định nghĩa schema Pydantic (`SizingCore` + `SizingExtension`)
- [ ] 1.7 — C3: trích trường bằng structured output; đo độ chính xác trên tập phát triển
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
- [ ] 1.13 — Eval harness: chạy eval set, tính recall + false positive
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

**Tiêu chí hoàn thành:** recall ≥ 50% trên tập phát triển; KHÔNG finding nào
thiếu căn cứ (mọi mục đều có `rule_ref` hoặc `computed_evidence`).

---

## GIAI ĐOẠN 2 — Đa phương thức & tái sử dụng  (2–3 tuần)

### Tuần 4 — Xử lý hình ảnh
- [ ] 2.1 — Trích ảnh từ `.docx` kèm ngữ cảnh văn bản trước/sau
- [ ] 2.2 — Phân loại ảnh (sơ đồ / biểu đồ-dashboard / khác)
- [ ] 2.3 — C2: vision + OCR, sinh mô tả và trích số
- [ ] 2.4 — Cơ chế xuống cấp có kiểm soát: cảnh báo khi không kiểm chứng được (NT4)
- [ ] 2.5 — Kiểm tra chéo: số trong ảnh biểu đồ vs số trong bảng sizing

### Tuần 5 — Truy hồi & scale
- [ ] 2.6 — Nạp 30 bản lịch sử đã trích trường vào vector DB
- [ ] 2.7 — C6: tìm bản tương tự, hiển thị độ tương đồng + điểm khác biệt
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
| 2026-08-26 | **Thống nhất số trang về SỐ TRANG IN** của Guideline lần 07 cho toàn bộ R01–R110 | Hai hệ cùng tồn tại gây tra cứu sai: R01–R100 dùng trang vật lý bản lần 06 (= trang in + 1) vì PDF đó có thêm trang chữ ký ở đầu. Đã kiểm chứng offset −1 bằng 12 phép dò độc lập **trước khi** sửa, không tin ghi chú suông. Đổi bằng `scripts/unify_page_numbers.py` (307 vị trí, 4 file), kiểm chéo bằng `scripts/check_page_consistency.py` — 0 lệch. Số trang là thứ người thẩm định dùng để mở tài liệu đối chiếu, sai một trang là mất niềm tin |
| 2026-08-26 | **Thêm `tat_ca` và `tai_lieu` vào `equipment_types`** thay vì bỏ ràng buộc bắt buộc của `applies_to_equipment` | Guideline chia chương theo loại thiết bị, nhưng ~21 quy tắc không gắn được thiết bị nào: 10 quy tắc thủ tục/phương pháp (R26, R30, R102…) và 11 mục checklist về cấu trúc tài liệu (`CL-2.2`, `CL-2.6`…). Bỏ ràng buộc thì mất khả năng lọc quy tắc theo thiết bị; liệt kê cả 10 loại cho một quy tắc về mục lục tài liệu thì vô nghĩa. Hai giá trị này giữ được cả hai. **Không** thêm `mang` cho R09/R12 — sẽ chồng lấn với 4 loại thiết bị mạng khi so khớp; khai đủ bốn loại thay thế |
| 2026-08-26 | **R101 so theo bậc, không so bằng.** `none < active-standby < active-active`; chỉ sinh finding vi phạm khi cơ chế khai **thấp hơn** mức yêu cầu, khai cao hơn thì ĐẠT | Guideline quy định mức **tối thiểu** theo phân loại hệ thống, không cấm dự phòng cao hơn. So bằng sẽ báo sai cho hệ `Quan trọng` chọn `active-active` — một cảnh báo sai thiệt hại hơn một lỗi bỏ sót. Vẫn treo `[CHƯA CHẮC]`: có nên sinh finding `minor` về chi phí không |
| 2026-08-26 | **R104 không ép đủ 11 yếu tố ảnh hưởng.** Tiêu chí neo vào *"những yếu tố bản sizing thực sự dùng trong công thức"*, không đếm đủ danh sách | Guideline liệt kê 11 yếu tố nhưng không nói yếu tố nào bắt buộc, và nhiều yếu tố không áp dụng cho mọi hệ (ví dụ "số thiết bị kết nối đồng thời" với hệ web nội bộ). Ép đủ 11 sinh cảnh báo sai hàng loạt. **Cần hỏi đơn vị thẩm định** có tập tối thiểu không |
| 2026-08-26 | **Khâu cấp phát không có mục checklist nào phủ** — ghi nhận là khoảng trống có hệ thống, không phải ca lẻ | Bốn quy tắc `R25+R32`, `R97`, `R108`, `R109` đều không map được sang mục checklist nào, và ba trong bốn thuộc khâu cấp phát. Nên hỏi đơn vị thẩm định xem cấp phát nằm ngoài phạm vi checklist một cách cố ý hay không, thay vì đề nghị bổ sung từng mục |
| _(chờ)_ | 10 điểm mơ hồ/mâu thuẫn trong công thức code hiện hành | Xem `docs/0.1-danh-sach-quy-tac.md` mục C. Cần người thẩm định xác nhận trước khi số hóa vào `rules.yaml` |
