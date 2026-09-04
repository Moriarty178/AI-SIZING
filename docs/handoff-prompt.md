# Prompt bàn giao sang phiên mới

> **Chép thẳng nội dung từ dấu `---` trở xuống vào ô chat**, đừng bảo Claude "đọc file
> này". Trỏ file thì Claude phải gọi Read, nội dung vẫn vào context y hệt mà còn tốn
> thêm phần bao của lệnh gọi — và có thêm một bước có thể hỏng. Dán thì chắc chắn đọc.
>
> Cập nhật lại file này mỗi khi bàn giao.
> **Lần cập nhật gần nhất: 2026-09-04** — kết thúc **Giai đoạn 0** (26 hồ sơ thật,
> 475 nhãn, endpoint đã dò) và **8/17 mục Giai đoạn 1** (1.1–1.6, 1.8, 1.9).
> Việc kế tiếp: **1.10** (C7 báo cáo Markdown) rồi **1.7** (C3 trích xuất).
> Bản bàn giao trước (2026-08-26, lúc còn chờ hồ sơ) đã bị thay hoàn toàn.

---

Dự án **Sizing Copilot**. Giai đoạn 0 đã **xong**; Giai đoạn 1 đang làm dở
(**8/17 mục**). Việc kế tiếp là **mục 1.10** trong `PLAN.md`. Đọc hết phần dưới
trước khi làm gì.

## 0. Dự án là gì, và ranh giới không được vượt

Trợ lý AI giúp **người xin cấp tài nguyên tự kiểm bản định cỡ (sizing) Word trước khi
nộp**. Đọc `.docx`, đối chiếu bộ quy tắc của đơn vị thẩm định, trả về danh sách điểm
chưa đạt kèm căn cứ và gợi ý sửa. Là công cụ **cố vấn** — KHÔNG tự phê duyệt/từ chối.

`CLAUDE.md` được harness tự nạp, **không cần Read**. Bốn nguyên tắc trong đó
(NT1 tính bằng code không bằng LLM · NT2 mọi finding phải có căn cứ · NT3 quy tắc là
dữ liệu · NT4 xuống cấp có kiểm soát) là **ranh giới thiết kế**, vi phạm thì dừng lại
và hỏi tôi.

## 1. Đọc bắt buộc, theo thứ tự

Đọc **đúng phạm vi** ghi ở cột "Đọc phần nào" — vài file rất dài, đọc trọn là phí context.

| # | File | Đọc phần nào | Vì sao |
|---|---|---|---|
| — | `CLAUDE.md` | **KHÔNG cần Read** | Harness tự nạp |
| 1 | `PLAN.md` | **Giai đoạn 1 + Nhật ký quyết định** (Giai đoạn 0 chỉ lướt) | Trạng thái từng mục; rất nhiều thứ đã chốt, đừng bàn lại |
| 2 | `src/reporting/finding.py` | Toàn bộ (60 dòng) | Lược đồ `Finding` — đầu ra duy nhất của mọi thành phần kiểm |
| 3 | `src/validators/rules_loader.py` | Toàn bộ (~210 dòng) | Cách `rules.yaml` được diễn giải; `khong_danh_gia_duoc()` |
| 4 | `src/validators/quantitative.py` | Toàn bộ (~255 dòng) | C4 — mẫu mực cho mọi thành phần kiểm về sau |
| 5 | `docs/rules/rules-checklist-flat.md` | **Mục "Hệ quả cho báo cáo (C7)"** + 3 bảng I/II/III cuối file | Thứ tự checklist + luật chặn Vòng 2 — chính là mục 1.10 |
| 6 | `docs/0.10-ket-qua-xac-minh-endpoint.md` | Phần chốt | Endpoint thật làm được gì / không làm được gì |

Đọc thêm **khi cần**, không đọc trước: `docs/ke-hoach-trien-khai.md` (bối cảnh đầy đủ,
rất dài) · `docs/0.7-nhan-vang-tu-pnx.md` (cách dựng eval set + **mục 6 hạn chế**) ·
`docs/0.6-chuan-hoa-ho-so.md` · `docs/rules/rules-id-map.md` · `rules-formulas.md` ·
`rules-criteria.md` · `config/rules.yaml` (**4.300 dòng — chỉ đọc `globals` hoặc quy
tắc cụ thể khi cần**).

⚠️ `docs/0.7-nguon-nhan-vang.md` **là thiết kế chết** — xây trên giả định DB web app
có sẵn nhãn, giả định đó đã đổ. Giữ lại cho tương lai, đừng dùng.

## 2. Trạng thái hiện tại

| GĐ | Tiến độ | Trạng thái |
|----|---------|------------|
| 0 — Chuẩn bị tri thức & dữ liệu | 11 / 13 | 🟢 Đủ để sang GĐ 1 (còn 0.9 thời gian mỗi vòng, 0.12 tài liệu) |
| 1 — MVP chỉ xử lý text | **8 / 17** | 🟡 Đang làm — **1.10 rồi 1.7** |
| 2 · 3 · 4 | 0 | ⬜ Chưa bắt đầu |

**Đã xong ở Giai đoạn 1:** 1.1 (khởi tạo) · 1.2 (client LLM, phần offline) · 1.3 (C1
đọc docx) · 1.4 (chuẩn hoá số/đơn vị) · 1.5 (chạy C1 trên toàn bộ hồ sơ) · 1.6 (schema)
· 1.8 (bộ nạp quy tắc) · 1.9 (C4 định lượng).

**Còn lại:** **1.7** (C3 trích xuất) · **1.10** (C7 báo cáo) · 1.11 (RAG) · 1.12 (C5
định tính) · 1.13 (eval harness) · 1.14 (Streamlit) · 1.15 (demo) · 1.16 (mẫu Word) ·
1.17 (điền hộ cột C checklist).

**77 unit test đang qua, chạy hoàn toàn offline.** `python -m pytest -q`.

### Bộ quy tắc `config/rules.yaml`

**151 quy tắc** · 101 định lượng / 50 định tính · 131 Vòng 2 / 20 Vòng 1 ·
37 `critical` / 81 `major` / 33 `minor` · **46 hằng số `globals`** ·
4 quy tắc `enabled: false` (`KPI-15`, `KPI-16`, `PRC-04`, `PRC-08`).

16 nhóm mã: `ALC 5 · ARC 27 · BAK 11 · CPU 11 · EVD 22 · FWL 4 · KPI 16 · LAN 4 ·
LBA 2 · MTH 4 · PRC 11 · RAM 3 · RCK 3 · SAN 2 · STO 23 · TST 3`.

**Bốn nguồn quy tắc** (196 thô → 151 sau khử trùng): Guideline GL.CNVTQĐ.CNTT.18 lần 07
(110 quy tắc `R01–R110`) · code web app (46) · checklist thẩm định 57 mục (37 quy tắc
`CL-*`) · văn bản khác (`QD849-01`, `QD849-02`, `ZONE-01`).

**`PRC-11` là quy tắc mới nhất** (thêm 2026-09-03, tôi duyệt): *"Phải nêu mục đích
sizing"*, `checklist_ref: CL-2.1`, Vòng 1, `major`. Vá khoảng trống 17 nhãn PNX đòi.
⚠️ `scripts/build_rule_ids.py` đọc từ tài liệu nguồn chứ **không** đọc `rules.yaml`,
chạy lại sẽ xoá dòng `PRC-11` khỏi `rules-id-map.md`.

### Dữ liệu thật

`danh_sach_sizings_da_duyet/` — **26 hồ sơ**, **23 có PNX** (Phiếu Nhận Xét của Phòng
Hệ thống, `.docx`), 42 file PNX. 3 hồ sơ **vĩnh viễn không có PNX** (CloudCA, ARVR,
CAMPAIGN_PUSH_MXH) → ngoài eval set nhưng vẫn dùng cho C1 và kho C6.

`data/eval_set.json` — **475 nhãn** từ PNX. `data/eval_split.json` — **DEV 14 hồ sơ /
317 nhãn**, **TEST giữ kín 9 hồ sơ / 158 nhãn** (chia theo *đầu mối yêu cầu*, seed
20260903). **Không đọc nhãn test** khi chỉnh quy tắc/prompt; chỉ chạy một lần ở 3.6.

## 3. Kiến trúc và code đã có

Luồng: `Ingest → Extract → Validate → Report`. Giai đoạn 1 dùng Python thuần, chưa
LangGraph.

| File | Nội dung | Bài học đã đóng vào code |
|---|---|---|
| `src/llm/client.py` | Gọi gateway OpenAI-compatible; `chat()` + `extract()` | `max_tokens` mặc định **4000**; `content` rỗng ⇒ **ném lỗi**; **luôn** strip fence ```` ```json ```` và **luôn** validate bằng Pydantic; retry ≤3 nhắc lại lỗi validate; hết lượt ném `ExtractionFailed` |
| `src/ingestion/numbering.py` | Dựng lại đánh số tự động của Word từ `numbering.xml` | Số mục **không nằm trong text**; cấp 1 là **số La Mã** |
| `src/ingestion/docx_reader.py` | C1: `Element` (kind/text/page/section/level/rows) + `DocxDocument` | `page_source` ∈ rendered/manual/**none**; none ⇒ `page=None` + cảnh báo, không đoán trang 1 |
| `src/ingestion/filenames.py` | Nguồn duy nhất trả lời "file này có phải bản sizing không" | `NOT_SIZING` regex + `NOT_SIZING_EXACT` (`tuanha3.docx` — tôi xác nhận không phải bản sizing) |
| `config/units.yaml` | Bảng đơn vị — **dữ liệu**, không phải code | Dung lượng cơ sở **1024**, băng thông **1000**; `KB/s` ≠ `kb/s` (8 lần) nên so khớp **có phân biệt hoa thường** |
| `src/normalization/numbers.py` | `ParsedNumber(value, ambiguous, alt_value, note)` | *"1.500"* là 1500 hay 1,5 — còn lưỡng nghĩa thì trả **cả hai cách đọc**, không im lặng chọn một |
| `src/normalization/units.py` | `Quantity`, `resolve()`, `factor()` | Đơn vị **không khai hệ số ⇒ không quy đổi được**, KHÔNG mặc định 1.0 (từng âm thầm coi 1 vCPU = 1 Cint) |
| `src/normalization/sanity.py` | Lưới kiểm hợp lý (dung lượng/người, TPS/người) | Bắt được ca thật *"3.000.000 TB cho 1.080 người dùng"* |
| `src/extraction/schema.py` | `ExtractedValue`, `SizingExtension`, `SizingCore` | **Túi tham số** thay vì 203 trường cứng; `value=None` = KHÔNG TÌM THẤY |
| `src/reporting/finding.py` | `Finding` + `co_can_cu()` + `loc_bo_khong_can_cu()` | Cổng NT2 nằm ở đây |
| `src/validators/rules_loader.py` | `Rule`, `RuleSet`, `runnable()`, `blocked()` | `khong_danh_gia_duoc()` trả **chuỗi lý do**, không phải bool |
| `src/validators/quantitative.py` | C4 — thuần code, `asteval` | 4 đường xuống cấp NT4, không đường nào đoán giá trị |

**Thư mục `src/normalization/` lệch Phụ lục B** (Phụ lục B không có nó). Lý do: dùng
chung cho cả C3 và C4; để trong một trong hai sẽ tạo phụ thuộc chéo.

`scripts/` có ~30 script. Đáng nhớ: `validate_rules.py` (**chạy sau mỗi lần sửa
`rules.yaml`**) · `try_c1_on_dossiers.py` (chạy C1 trên toàn bộ hồ sơ) ·
`check_section_match.py` (đối chiếu số mục C1 ↔ PNX) · `parse_pnx.py` ·
`suggest_rule_refs.py` · `finalize_labels.py` · `probe_llm_endpoint.py` ·
`smoke_llm.py` (**chưa chạy** — xem mục 5).

## 4. VIỆC KẾ TIẾP — mục 1.10, C7 báo cáo Markdown

Đây là việc phiên mới bắt tay vào. **Thuần code, không cần mạng, không cần model.**

**Yêu cầu trong `PLAN.md`:**

1. Trình bày **hai vòng**: Vòng 1 trước, Vòng 2 sau.
2. **Vòng 1 xếp theo thứ tự checklist I → II → III** để người thẩm định đọc báo cáo và
   chấm checklist theo cùng một mạch. Mã `CL-1.x` → `CL-2.x` → `CL-3.x`; trong phần III,
   khối chung `CL-3.x.N` đứng trước 3 mục riêng của Database (`CL-3.2.4`, `CL-3.2.7a`,
   `CL-3.2.19`).
3. **BẮT BUỘC — chặn finding Vòng 2 của mục đã trượt Vòng 1**, thay bằng một dòng
   *"chưa đánh giá được — thiếu thông tin"*. Nối qua `checklist_ref`.
   *Lý do:* nói *"công thức CPU của bạn sai"* với người **chưa viết phần CPU** là vô
   nghĩa và làm mất niềm tin (rủi ro R6). Đây là **quyết định đã chốt**, không bàn lại.
4. C7 còn phải: **gom, khử trùng, xếp ưu tiên** (theo `severity`), và **lọc bỏ finding
   không có căn cứ** (NT2) — nhưng **đếm số bị lọc**, không im lặng.

**Gợi ý thiết kế** (chưa chốt, phiên mới tự quyết trong khuôn NT):
- Nguồn "mục nào trượt Vòng 1": finding có `vong == 1` và `category` ∈
  {`thieu_muc`, `thieu_thong_tin`}. `khong_kiem_chung_duoc` ở Vòng 1 **không** nên chặn
  — không biết là thiếu thì không được coi như thiếu.
- Khớp phạm vi: mục Vòng 1 `scope: he_thong` trượt ⇒ chặn mọi `scope_key`; mục
  `scope: phan_he` trượt ở "App" ⇒ chặn `scope_key` "App" và "App/SSD".
- Nên tách Vòng 2 thành **"chưa đạt"** (`vuot_nguong`, `sai_cong_thuc`,
  `khong_nhat_quan`) và **"chưa kiểm được"** (`thieu_thong_tin`,
  `khong_kiem_chung_duoc`) — nếu không, tài liệu rỗng sẽ ra 124 dòng "thiếu thông tin"
  nhấn chìm phần có ý nghĩa.
- Nhãn hiển thị tiếng Việt (tên phần I/II/III, tên mức độ, tên nhóm) nên để **trong
  file cấu hình** chứ không hard-code — tinh thần NT3.
- Báo cáo phải mở đầu bằng câu nói rõ **đây là công cụ cố vấn**, người thẩm định quyết
  định cuối cùng.
- Cần unit test cho: luật chặn hoạt động · thứ tự checklist đúng · khử trùng · finding
  thiếu căn cứ bị lọc và **được đếm**.

**Trở ngại thật:** nguồn finding Vòng 1 là **C5 (mục 1.12) chưa có**. Đừng vì thế mà
tự viết một bộ kiểm Vòng 1 tạm trong C7 — làm thế là lấn việc 1.12. C7 nhận `Finding`
làm đầu vào; demo thì dựng dữ liệu tay và **ghi rõ là demo**.

**Sau 1.10 là 1.7 (C3).** Phần **đo độ chính xác của 1.7 cần model**, nên chỉ viết được
phần khung cho tới khi tôi gửi kết quả `smoke_llm.py`.

## 5. Hạ tầng LLM — kết quả dò thật (0.10)

Chạy `scripts/probe_llm_endpoint.py` từ máy trong mạng công ty, 9 phép thử.
Kết quả đầy đủ: `docs/0.10-ket-qua-xac-minh-endpoint.md`.

- **KHÔNG phải cụm vLLM tự host** mà là **gateway OpenAI-compatible nội bộ**, phục vụ
  6 model (Claude opus-4-6 / sonnet-4-5 / haiku-4-5, gpt-oss-120b, Qwen2.5-Coder-7B).
  Kiến trúc không đổi, nhưng **thôi gọi là "vLLM"** để không ai kỳ vọng `guided_json`.
- ⚠️ **Phép thử `guided_json` "ĐẠT" là dương tính giả.** Output bọc trong fence
  ```` ```json ````, mà guided decoding thật thì token đầu **bắt buộc** là `{` — tức
  tham số được nhận nhưng **bỏ qua**. ⟹ **Client LUÔN validate + retry**;
  `response_format` chỉ là tối ưu hoá, không phải bảo đảm. Đã đóng vào `client.py`.
- ⚠️ **Bẫy `max_tokens`:** model trả kèm `reasoning_content`; đặt 200 làm `content`
  **rỗng mà vẫn HTTP 200**, không ném lỗi. `max_tokens ≥ 2000`, `content` rỗng = LỖI.
- ✅ **Vision CÓ** → C2 không phải xuống cấp OCR-only; mục 2.3 giữ nguyên phạm vi.
- ❌ **Embedding KHÔNG có** (`/v1/embeddings` 404/400) → **BGE-M3 chạy cục bộ** bằng
  `sentence-transformers` trên CPU (kho nhỏ nên đủ). Ảnh hưởng 1.11, C5, C6.
- ✅ Context **200k–1M** → không cần chunk gắt. ✅ Rate limit thoáng (0/10 lần 429,
  TB 1,8 s) → GĐ 1 chưa cần hàng đợi.
- ⬜ **Chưa chốt model chính cho C3.** Tạm dùng `claude-opus-4-6` (sạch format nhất);
  **không dùng `gpt-oss-120b`** cho trích xuất (2/2 lần nhầm trường). Chốt sau khi
  chạy eval thật ở 1.13.
- ⬜ **`scripts/smoke_llm.py` chưa chạy** — tôi đang ở mạng ngoài, sẽ chạy trong mạng
  công ty và gửi kết quả. **Không chặn** các mục thuần code.

## 6. Quyết định ĐÃ CHỐT — đừng bàn lại

- **Thẩm định chạy HAI VÒNG nối tiếp.** Vòng 1 = checklist, chỉ hỏi *"thành phần cần
  có đã có chưa"*, tiêu chí mặc định *"có thông tin thực chất là ĐẠT"*. Vòng 2 =
  Guideline, kiểm cách tính. **C7 CHẶN finding Vòng 2 cho mục đã trượt Vòng 1.**
  (Khác với `lan_nhan_xet` = số lần PNX phản hồi 1/2/3 — đừng lẫn hai thứ.)
- **Đường vào chính là file `.docx` do người dùng tự viết**, không phải JSON web app
  (chốt 0.11, có 26 hồ sơ thật làm bằng chứng). ⟹ C1 phải chịu định dạng lộn xộn, và
  **C2/vision là nhu cầu có thật ngay từ đầu** chứ không phải việc của GĐ 2.
- **Copilot KHÔNG phải trợ lý soạn thảo từng bước** — là bước kiểm trước khi nộp.
- **Mã quy tắc `<NHÓM>-<số>` là CỐ ĐỊNH**, đổi là hỏng liên kết eval set.
- **`check` cho bất đẳng thức, `formula`+`compare_with`+`tolerance` cho tính lại** —
  không dùng đồng thời. **`applies_when`** cho quy tắc loại trừ nhau.
- **`scope`**: `he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru` — quyết định một
  quy tắc bị chấm bao nhiêu lượt trên một tài liệu.
- **KHÔNG số hóa 4 công thức code đang chạy sai** (`RDS-04`, `RDS-10`, `LBF-01`,
  `LBF-02`) — số hóa theo Guideline cho đúng.
- **`rule_ref` của eval set do AI gán** (đổi quyết định 2026-09-03 vì 500 nhãn quá
  nhiều để gán tay), tôi kiểm mẫu ngẫu nhiên. Mẫu kiểm **đóng băng 83 id** ở
  `data/audit_sample_ids.json`, phán quyết khoá theo `label_id`.
- **Bản đã ký KHÔNG sạch** → không dùng làm chuẩn false positive. c360 ký với lỗi còn
  nguyên; tôi xác nhận *sót khi duyệt, dự án gấp nên bypass*.
- **Chất lượng ảnh sở cứ là việc người thẩm định tự đánh giá**, không phải việc của AI
  → 26 nhãn `ngoai_pham_vi` loại khỏi mẫu số.
- `QHĐC` = **Quy hoạch định cỡ** → `PRC-07`.

## 7. Cần TÔI duyệt trước khi làm — đừng tự quyết

1. **8 quy tắc không chạy được vì bảng tra chỉ nằm trong `note` dạng văn xuôi**:
   `STO-02`, `STO-03`, `STO-09`, `STO-13`, `CPU-10`, `BAK-07`, `LAN-02`, `RCK-01`.
   Ví dụ STO-03 ghi *"NL-SAS 100 · SAS 10k 140 · SAS/FC 15k 210 · SSD từ 5000"*.
   Chép bảng vào Python **vi phạm NT3**; đề xuất là thêm mục `lookup:` vào `rules.yaml`.
   **Chờ tôi duyệt.**
2. **Lưới kiểm hợp lý** (`sanity.py`) đã có code nhưng **chưa thành quy tắc** trong
   `rules.yaml` — cần tôi duyệt.
3. **Không tự thêm/xoá quy tắc, không tự đổi `severity`.**
4. `CL-2.1` và `CL-2.4` chồng lấn (đều về cơ sở/dạng định cỡ) — chờ ý kiến đơn vị
   thẩm định, đang để riêng.

## 8. Hạn chế phải nêu khi công bố kết quả

Đây là **rủi ro lớn nhất của dự án hiện giờ**, đã chuyển từ *"không có dữ liệu"* sang:

1. **Nhãn không phải kiểm định độc lập** — gợi ý `rule_ref` và mọi phán quyết kiểm mẫu
   đều do **cùng một tác nhân AI**. Ước tính máy đúng chủ đề **≈65%**.
   → Cần một người đọc lại một lát cắt `eval_sheet_mau_kiem_daduyet.csv`.
2. **397/475 nhãn nhận gợi ý máy nguyên**, thường **dư mã** ⇒ recall sẽ **hào phóng hơn
   thực tế**.
3. **Chưa có cách đo false positive** (bản đã ký không sạch).
4. Recall là *"so với người thẩm định"*, không phải sự thật tuyệt đối.
5. **Ba tầng `confidence` (cao/vừa/thấp) KHÔNG phân tách được chất lượng** — 67–80%,
   ±12pp ở n=15. Đừng dùng chúng để lọc cho tới khi hiệu chỉnh lại.
   *(Tôi từng kết luận vội "thang bị lệch"; với mẫu 88 dòng thứ tự đảo lại. Kết luận
   đúng là ba tầng không tách được gì cả.)*
6. **~56 nhãn** ở tầng `không xác định` + `khoảng trống` vẫn cần soát tay.

## 9. Cạm bẫy kỹ thuật — đã mất thời gian vì chúng

**Môi trường máy này:**
- **Máy này KHÔNG có `uv`.** Phụ thuộc cài bằng `pip` vào Python 3.12 (pyenv).
  `pyproject.toml` viết chuẩn nên `uv sync` dùng được ngay khi có `uv`.
- **Bash tool không chạy được heredoc dài / `python -c` nhiều dòng** — viết ra file rồi
  chạy, hoặc dùng Write.
- **In tiếng Việt trên Windows phải đặt `PYTHONIOENCODING=utf-8`**, nếu không sẽ
  `UnicodeEncodeError: 'charmap' codec`.
- Đường dẫn `/tmp/...` trong Python **không hoạt động** — dùng đường dẫn tương đối
  trong repo.
- `scripts/unify_page_numbers.py` **CHỈ CHẠY MỘT LẦN — đã chạy rồi.** Chạy lại sẽ trừ
  tiếp và làm sai số trang.

**Dữ liệu thật:**
- **Số mục của Word là đánh số tự động** (`w:numPr` + `numbering.xml`), **không nằm
  trong text**. Cấp 1 các bản này là **số La Mã**. Ban đầu C1 chỉ nhận ra đề mục 20/48
  bản; sau ba lần sửa nhờ chạy trên tài liệu thật mới lên **47/47**.
- Tài liệu dùng **`numId` riêng cho mỗi chương** ở cấp 2 → Word hiện "1." lặp lại dưới
  mọi chương. Phải ghép theo cấp heading thành đường dẫn đầy đủ (`III.4.1`).
- Có bản gán **"Heading 1" cho MỌI đề mục** kể cả mục con → khi text đã ghi rõ số thì
  **tin con số hơn style**.
- **Ký tự PUA** (U+E000–U+F8FF) của font Symbol/Wingdings: `U+F0A3` là `≤`, `U+F0B3` là
  `≥` — **không phải bullet**. Quy về `-` sẽ phá hỏng ngưỡng.
- **YAML khối `>`**: dòng thụt sâu hơn dòng đầu sẽ **giữ nguyên xuống dòng**, làm hỏng
  biểu thức `check`/`formula` nhiều dòng.
- Nháy cong `“”` → `"`, và từ bị **ngắt ngang dòng tại dấu gạch nối** (`active-` /
  `standby` → `active-standby`, không dấu cách) khi đối chiếu trích dẫn.

**Bẫy tư duy đã sập ít nhất một lần:**
- **Đừng bịa định danh rồi giả định nó khớp.** Tôi từng viết `label_id` trong bảng
  `OVERRIDES` theo trí nhớ — **không cái nào khớp**, 5 phán quyết cũ sống sót âm thầm
  và làm sai hẳn một tầng thống kê (55% vs 82% thật). Nay script có **kiểm khoá lạc và
  báo lỗi to**. Nguyên tắc: mọi bảng gõ tay khoá theo id phải có bước kiểm khoá tồn tại.
- **Đừng để giá trị mặc định lặng lẽ thay cho "không biết".** `convert(1,"vcpu","cint")`
  từng trả `1.0`, tức coi 1 vCPU = 1 Cint — lặng lẽ ghi đè `CPU-03`/`CPU-09`.
- **Đừng im lặng bỏ qua quy tắc không chạy được** — đó là cách âm thầm làm hụt recall.
  `blocked()` luôn kèm lý do.
- **Một tiêu chí chặn quá thô chặn nhầm quy tắc tốt.** `role: lookup` gánh **hai vai**
  (khoá tra bảng ↔ cờ điều kiện trong `applies_when`); gộp lại chặn nhầm 9 quy tắc.
  81 → **90/101**.
- **Heuristic "câu ngắn không có động từ mệnh lệnh là tiêu đề" đã làm mất nhãn thật**
  (*"Sở cứ sử dụng ssd"*). Đã thay bằng danh sách tiêu đề tường minh. Mất một nhãn thật
  tệ hơn để lọt một tiêu đề.

## 10. Cách làm việc mong muốn

- Làm theo thứ tự `PLAN.md`, **không nhảy cóc**. Xong mục nào tick `[x]` mục đó và ghi
  ngắn gọn kết quả + lý do các quyết định đáng nhớ.
- Text hướng tới người dùng cuối (finding, báo cáo, gợi ý) viết **tiếng Việt**; định
  danh code, log, commit viết tiếng Anh.
- **Mọi hàm trong `validators/quantitative.py` phải có unit test.** Test phải là **hồi
  quy cho lỗi thật**, không phải test cho vui.
- Gặp chỗ mơ hồ hoặc mâu thuẫn trong tài liệu thì **nêu ra, không tự quyết**.
- **Việc gì máy kiểm được thì viết script kiểm, đừng tin mắt.** Nhiều lỗi chỉ lộ ra khi
  chạy trên **tài liệu thật**, không phải trên unit test.
- Sửa `rules.yaml` xong **luôn chạy `scripts/validate_rules.py`**.
- **Ưu tiên độ chính xác hơn độ phủ.** Một cảnh báo sai làm mất niềm tin nặng hơn một
  lỗi bỏ sót.

## 11. Câu hỏi còn treo với đơn vị thẩm định

- CPU/RAM/IOPS tính **"mỗi request"** (checklist) hay **"mức hệ thống"** (Guideline)
  hay **`factor = định cỡ/POC`** (web app)? Ba cách phân rã.
- Mức `bình thường` có bắt buộc cơ chế dự phòng nội site nào không? (`ARC-12`)
- Khai dự phòng **cao hơn** mức yêu cầu — có cảnh báo lãng phí không?
- **Dung sai** khi so tổng toàn hệ với tổng các phân hệ? (`EVD-10`)
- `CL-1.2` (mức độ SR) có nằm trong tài liệu sizing không? (`PRC-08` đang tắt)
- Nguồn của **KPI Datanode ≤ 50%** và các ngưỡng Redis/Kafka/MariaDB nội bộ?
- Mâu thuẫn **tăng trưởng 01 năm** (web app) ↔ **cấp phát 06 tháng** (`ALC-01`)?
- **Ngày tháng thẩm định** — cả 6 PNX bỏ trống ô ngày, nên **0.9 vẫn thiếu thời gian
  trung bình mỗi vòng**. Cần sổ theo dõi PYC. **Phải chụp baseline trước khi Copilot đi
  vào sử dụng.**
- Bản `.docx` cho **VAPS** và **MNP** (hiện chỉ có PDF, GĐ 1 chưa đọc PDF).
- 11 điểm lệch khi chuẩn hoá hồ sơ (mục 2 của `docs/0.6-chuan-hoa-ho-so.md`), đáng chú ý:
  thư mục `PNM 57012` **chứa tài liệu của hệ thống khác**; FMRA lẫn cả Backup_2024 và
  Training_2025; số ở tên thư mục **≠ mã PYC** ở 4 hồ sơ.

## 12. Ba lỗi tính toán đang chạy thật trên web app

Độc lập với Copilot, nên báo đội bảo trì (`rules-crossmap.md` mục 2):

| Mã | Lỗi | Hệ quả |
|---|---|---|
| **C-01** | Redis dùng `Kkpi = 0.8` cho RAM thay vì `0.9` | RAM dư ~12,5% |
| **C-02** | Redis áp hệ số KPI và sai số **hai lần** | RAM dư ~22% |
| **C-06** | LB/FW không áp `Kdph = 1.2` | Băng thông **thiếu 20%** |
