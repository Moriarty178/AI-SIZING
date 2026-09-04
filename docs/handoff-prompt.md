# Prompt bàn giao sang phiên mới

> **Chép thẳng nội dung từ dấu `---` trở xuống vào ô chat**, đừng bảo Claude "đọc file
> này". Trỏ file thì Claude phải gọi Read, nội dung vẫn vào context y hệt mà còn tốn
> thêm phần bao của lệnh gọi — và có thêm một bước có thể hỏng. Dán thì chắc chắn đọc.
>
> Cập nhật lại file này mỗi khi bàn giao.
> **Lần cập nhật gần nhất: 2026-09-04 (tối)** — Giai đoạn 1 đạt **14/17**, commit
> `0c65296`, **225 test**. Ba mục còn lại đều **chặn bởi người hoặc bởi mạng nội bộ**.
> Bản trước (sáng 04-09, lúc còn 9/17 và sắp làm 1.7) đã bị thay hoàn toàn.

---

Dự án **Sizing Copilot**. Giai đoạn 0 xong; **Giai đoạn 1 đạt 14/17 mục**. Đọc hết
phần dưới trước khi làm gì.

## 0. Dự án là gì, và ranh giới không được vượt

Trợ lý AI giúp **người xin cấp tài nguyên tự kiểm bản định cỡ (sizing) Word trước khi
nộp**. Đọc `.docx`, đối chiếu bộ quy tắc của đơn vị thẩm định, trả về danh sách điểm
chưa đạt kèm căn cứ và gợi ý sửa. Là công cụ **cố vấn** — KHÔNG tự phê duyệt/từ chối.

`CLAUDE.md` được harness tự nạp, **không cần Read**. Bốn nguyên tắc trong đó
(NT1 tính bằng code không bằng LLM · NT2 mọi finding phải có căn cứ · NT3 quy tắc là
dữ liệu · NT4 xuống cấp có kiểm soát) là **ranh giới thiết kế**, vi phạm thì dừng lại
và hỏi tôi.

## ⚠️ 0b. Ràng buộc lớn nhất về nhịp làm việc: HAI MÔI TRƯỜNG

| | Laptop ngoài | Máy trong mạng nội bộ |
|---|---|---|
| Model tự dựng (`10.221.58.70:8401`) | ❌ không với tới | ✅ |
| Mã nguồn, hồ sơ, quy tắc, test | ✅ | ✅ |
| Chi phí | 0 | **~40 giây mỗi lời gọi** |

Phần lớn thời gian làm việc ở **laptop ngoài**. Nên: **mọi thứ làm được không cần model
thì làm ngay**; đừng đề nghị tôi "chạy thử để xem" trừ khi thật sự cần model.
Danh sách việc của người chia theo môi trường:
**`docs/viec-cua-nguoi-va-moi-truong.md`** — đọc file này sớm.

## 1. Đọc bắt buộc, theo thứ tự

Đọc **đúng phạm vi** ghi ở cột "Đọc phần nào" — vài file rất dài, đọc trọn là phí context.

| # | File | Đọc phần nào | Vì sao |
|---|---|---|---|
| — | `CLAUDE.md` | **KHÔNG cần Read** | Harness tự nạp |
| 1 | `PLAN.md` | **Giai đoạn 1 + Giai đoạn 2 + Nhật ký quyết định** | Trạng thái từng mục; rất nhiều thứ đã chốt, đừng bàn lại |
| 2 | `docs/viec-cua-nguoi-va-moi-truong.md` | Toàn bộ (~130 dòng) | Việc nào của tôi, chạy ở máy nào, cái gì đang chặn cái gì |
| 3 | `src/reporting/finding.py` | Toàn bộ (60 dòng) | Lược đồ `Finding` — đầu ra duy nhất của mọi thành phần kiểm |
| 4 | `src/extraction/bang.py` | **Docstring đầu module** (~45 dòng) | Vì sao C3 hỏi theo CỘT bảng; bài học đắt nhất của dự án |
| 5 | `src/validators/quantitative.py` | Toàn bộ (~255 dòng) | C4 — mẫu mực cho mọi thành phần kiểm |
| 6 | `src/reporting/report.py` | `chan_vong2()` + `xu_ly()` | Luật chặn Vòng 2 |
| 7 | `src/pipeline.py` | Toàn bộ (~150 dòng) | Cách 7 thành phần nối vào nhau |

Đọc thêm **khi cần**: `docs/ke-hoach-trien-khai.md` (bối cảnh, rất dài) ·
`docs/0.10-ket-qua-xac-minh-endpoint.md` · `docs/0.7-nhan-vang-tu-pnx.md` (**mục 6 hạn
chế**) · `docs/rules/rules-id-map.md` · `config/rules.yaml` (**4.300 dòng — chỉ đọc
`globals` hoặc quy tắc cụ thể**).

⚠️ `docs/0.7-nguon-nhan-vang.md` **là thiết kế chết** (xây trên giả định DB web app có
sẵn nhãn, đã đổ). Giữ cho tương lai, đừng dùng.

## 2. Trạng thái hiện tại

| GĐ | Tiến độ | Trạng thái |
|----|---------|------------|
| 0 — Chuẩn bị tri thức & dữ liệu | 11 / 13 | 🟢 Xong đủ để đi tiếp |
| 1 — MVP chỉ xử lý text | **14 / 17** | 🟡 **Hàng đợi việc offline đã CẠN** |
| 2 · 3 · 4 | 0 | ⬜ Chưa bắt đầu |

**Xong:** 1.1–1.10 · **1.7** (C3, đã qua 4 vòng v3→v6) · **1.12** (C5 định tính) ·
**1.13 phần code** (eval harness) · **1.14** (Streamlit) · **1.16** (mẫu Word) ·
**1.17** (điền hộ cột C checklist).

**Còn lại — cả ba đều CHẶN:**
- **1.13 chạy thật** — cần model, ~2 giờ trong mạng nội bộ. **Đây là con số quyết định
  tiêu chí hoàn thành Giai đoạn 1.**
- **1.15 demo** — chờ 1.13 có số.
- **1.11 RAG** — đã hoãn: C5 không cần RAG (50/50 quy tắc định tính đã có sẵn
  `criteria` + `source_doc` trong `rules.yaml`). Chỉ còn cần cho **C6 ở Giai đoạn 2**,
  và cần tôi quyết định cài `sentence-transformers` (~2GB torch).

**225 test đang qua, chạy hoàn toàn offline.** `python -m pytest -q`.

### Dữ liệu thật
`danh_sach_sizings_da_duyet/` — **26 hồ sơ, 47 bản `.docx`** (nhiều hồ sơ có nhiều
phiên bản). `data/eval_set.json` — **475 nhãn** từ PNX; `data/eval_split.json` —
DEV 14 hồ sơ / TEST **giữ kín** 9 hồ sơ. **Không đọc nhãn test** khi chỉnh quy tắc hay
prompt; chỉ chạy một lần ở 3.6.

### Bộ quy tắc `config/rules.yaml`
**151 quy tắc** · 101 định lượng / 50 định tính · 131 Vòng 2 / 20 Vòng 1 · **46 hằng số
`globals`** · 4 quy tắc `enabled: false`. 16 nhóm mã (`ALC ARC BAK CPU EVD FWL KPI LAN
LBA MTH PRC RAM RCK SAN STO TST`). Bốn nguồn: Guideline `R01–R110` · code web app ·
checklist 57 mục (`CL-*`) · văn bản khác.

## 3. ⭐ BỐN PHÉP ĐO ĐỊNH HÌNH LẠI DỰ ÁN (2026-09-04)

Đây là phần quan trọng nhất của bản bàn giao. Cả bốn đo bằng code, offline, không đoán.

**(1) Tài liệu thật NGHÈO SỐ LIỆU hơn bộ quy tắc giả định rất nhiều.**
Đọc cả 47 bản bằng C1: tài liệu **trung vị chỉ có 23 cột số liệu**. BCCS3 (65 cột) là
ca giàu nhất nhì. Mỗi phân hệ BCCS3 có đúng hai bảng chứa **~4 con số**.

**(2) Kể cả C3 hoàn hảo cũng không cứu được Vòng 2.**
101 quy tắc định lượng dùng **191 tham số riêng biệt**; tham số phổ biến nhất chỉ xuất
hiện ở **5** quy tắc; **58/101 quy tắc cần ≥3 tham số cùng lúc**. Đối chiếu 23 cột/hồ
sơ: phần lớn quy tắc Vòng 2 sẽ luôn thiếu đầu vào — **vì hồ sơ không nêu**, không phải
vì trích xuất kém.
⟹ **Sản phẩm chính của C3 với Vòng 2 là danh sách THAM SỐ CÒN THIẾU**, không phải bảng
tham số đã điền. `thieu_thong_tin` (`severity=major`, C4 đã sinh sẵn) chính là giá trị
cố vấn. **Không đầu tư thêm vào C3 để "tăng độ phủ".**

**(3) Recall không nằm ở phần định lượng.**
Chia 475 nhãn theo loại quy tắc bắt được chúng: **102 (21%) chỉ bằng định lượng** ·
**175 chỉ bằng định tính** · **192 bằng cả hai**. ⟹ **367/475 (77%) không cần một con
số nào.** Recall Giai đoạn 1 nằm ở **C5 + Vòng 1 checklist**.

**(4) Đo recall toàn tập là không khả thi.**
Cả tập dev tốn **6,5–11 giờ** gọi model. ⟹ Đo trên **mẫu 5 hồ sơ nhiều nhãn nhất**
(GSCG 47 · Data Security 45 · Vtag 38 · Mybox 31 · PBH 4.0 30) = **191/475 nhãn (40%)**
trong ~2 giờ. `--ho-so` nhận nhiều tên ngăn cách bằng dấu phẩy.
📌 **Bài học chọn mẫu:** cả ngày 04-09 đo trên **BCCS3, hồ sơ chỉ có 8 nhãn** — gần thấp
nhất. Nó giàu số liệu nên hợp soi C3 nhưng **không nói được gì về recall**. Chọn hồ sơ
theo mục đích đo.

⚠️ **29/475 nhãn (6%) vĩnh viễn không với tới được**: `cap moi MNP 32034` và `Cấp mới
hệ thống VAPS` không có bản `.docx` nào. Vẫn nằm trong mẫu số; mọi báo cáo recall phải
nói ra.

## 4. Kiến trúc và code đã có

Luồng: `Ingest → Extract → Validate → Report`. Điều phối: `src/pipeline.py`. Python
thuần, chưa LangGraph. **C5 chạy SAU C3** vì 21/50 quy tắc định tính có `applies_when`
tính từ tham số C3.

| File | Nội dung | Bài học đã đóng vào code |
|---|---|---|
| `src/llm/client.py` | Gateway OpenAI-compatible; `chat()` + `extract()` | `content` rỗng ⇒ **ném lỗi**; **luôn** strip fence + validate Pydantic; retry ≤3; `BadRequestError` chứ không phải `TypeError` khi gateway từ chối tham số |
| `src/ingestion/docx_reader.py` | C1: `Element(kind/text/page/section/level/rows)` | `page_source` ∈ rendered/manual/**none**; none ⇒ `page=None` + cảnh báo, không đoán trang 1 |
| `src/ingestion/numbering.py` | Dựng lại đánh số tự động của Word | Số mục **không nằm trong text**; cấp 1 là **số La Mã** |
| `src/ingestion/anchor.py` | Cổng chống bịa dùng chung C3+C5 | `neo(..., khoang=)` giới hạn vùng tìm — không có nó thì giá trị của phân hệ này neo vào phân hệ khác |
| `src/normalization/numbers.py` | `ParsedNumber(value, ambiguous, alt_value)` | *"1.500"* là 1500 hay 1,5 — còn lưỡng nghĩa thì trả **cả hai**, không im lặng chọn |
| `src/normalization/units.py` | `Quantity`, `resolve()`, `factor()` | Không khai hệ số ⇒ **không quy đổi được**, KHÔNG mặc định 1.0. `parse_quantity` **NÉM `UnknownUnit`** khi sau số không có đơn vị — "92%", "12" là ca bình thường |
| `src/normalization/sanity.py` | Lưới kiểm hợp lý | Bắt được ca thật *"3.000.000 TB cho 1.080 người dùng"* |
| **`src/extraction/bang.py`** | **C3 v6 — hỏi theo CỘT bảng** | Xem mục 5 |
| `src/extraction/extractor.py` | C3 — enum/bool + phương án lùi | Ngân sách token `3000 + 450×trường` vì **`reasoning_content` ăn vào `max_tokens`** |
| `src/extraction/plan.py` | Suy 237 tham số từ `rules.yaml` (NT3) | `unit` gánh **hai vai**: đơn vị đo ↔ kiểu dữ liệu (`đúng/sai`, `a\|b\|c`) |
| `src/validators/quantitative.py` | C4 — thuần code, `asteval` | 4 đường xuống cấp NT4, không đường nào đoán giá trị |
| `src/validators/qualitative.py` | C5 — RAG-free, bắt trích dẫn | **Căn cứ BẤT ĐỐI XỨNG**: "không đạt" thường do THIẾU, mà cái thiếu không trích dẫn được ⟹ không đòi trích dẫn tài liệu; nhưng trích dẫn **không neo được** ⇒ huỷ kết luận |
| `src/validators/expressions.py` | `danh_gia()` dùng chung C4+C5 | Tách ra vì chép đôi sẽ trôi khỏi nhau |
| `src/reporting/report.py` | C7 — gom, khử trùng, xếp ưu tiên | **Chặn finding Vòng 2 của mục trượt Vòng 1**; `khong_kiem_chung_duoc` CỐ Ý không chặn |
| **`src/reporting/dinh_vi_checklist.py`** | **1.17 — điền cột tham chiếu, KHÔNG gọi model** | Xem mục 6 |
| `src/reporting/mau_word.py` | 1.16 — sinh mẫu Word từ 57 mục checklist | `doc_checklist()` đọc `docs/rules/.tmp-checklist/items.md`; vá 3 lỗi nguồn lúc đọc, **không sửa file nguồn** |
| **`src/giao_dien.py`** | **1.14 — logic giao diện, tách khỏi Streamlit** | `kiem_model()` bắt cả `Exception` lạ: giao diện phải hiện được khi KHÔNG có model |
| `ui/app.py` | Trang Streamlit — **chỉ vẽ** | 2/3 chế độ không cần model |
| `eval/matching.py` + `eval/run_eval.py` | 1.13 | **Hai mẫu số** theo `meta.scoring_note`; hồ sơ chạy hỏng **vẫn tính vào mẫu số** |
| `config/units.yaml`, `config/report_labels.yaml` | **Dữ liệu**, không phải code (NT3) | Dung lượng cơ sở **1024**, băng thông **1000**; `KB/s` ≠ `kb/s` |
| `.streamlit/config.toml` | Ép `localhost`, tắt telemetry | Streamlit mặc định nghe **mọi card mạng** — lần chạy đầu in ra External URL công khai |

## 5. ⭐ C3 — bốn vòng, và quyết định DỪNG

Đọc kỹ phần này trước khi định "cải tiến C3".

**v3 → v4 → v5 → v6 trong một ngày.** Mỗi vòng thêm một cổng lọc, mỗi vòng một lượt chạy
thật 4–10 phút. **Ba vòng đầu đều chữa triệu chứng.**

Chế độ hỏng, đo được ở v5: trong **98 giá trị** model đưa ra, **66 (67%)** đến từ một ô
mà tham số khác cũng nhận ⟹ điền bừa. Nguyên nhân **cấu trúc**: lược đồ hỏi 98 tham số
số học ở `scope: phan_he`, mà bảng một phân hệ chỉ có ~4 con số.

**v6 đảo chiều câu hỏi.** Không hỏi *"tìm 8 tham số này"* nữa mà hỏi từng BẢNG: *"mỗi
CỘT chứa tham số nào?"*. Lược đồ có **đúng một trường cho mỗi cột dữ liệu** ⟹ bảng 3 cột
sinh tối đa 3 gán ghép. **Điền bừa trở thành bất khả về cấu trúc, không phải bị lọc sau.**
Kèm theo miễn phí: neo tuyệt đối (code tự định vị `(bảng, dòng, cột)` — bỏ hẳn khâu
"tìm lại câu model trích" từng làm rơi 73/94 lượt), NT1 giữ nguyên, và **32 lượt gọi
thay vì 94**.

Ba cổng còn lại: cột văn xuôi không bao giờ được hỏi tới · hai cột cùng nhận một tham số
⇒ bỏ cả hai · hai bảng cho hai số khác nhau cho cùng tham số ⇒ bỏ cả hai (NT4).

🔒 **ĐÃ CHỐT: dừng vòng lặp cải tiến C3 ở v6.** Nghiệm thu C3 từ nay **soi tay các giá
trị lấy được** (vài chục cái), **không dùng tỷ lệ trường** — mẫu số 617 là con số vô
nghĩa (xem mục 3.1). Nếu lượt chạy xác nhận v6 có kém thì **ghi nhận, không sửa tiếp**.

## 6. 1.17 — điền hộ cột checklist (mục giao được sớm nhất)

`python scripts/fill_checklist.py "<bản-sizing.docx>"` → `docs/checklist/*.md` + `*.csv`.
**Không gọi LLM** ⟹ chạy ở đâu cũng được, và lặp lại y hệt giữa hai lần chạy.

**Đo trên cả 47 bản: trung vị 22/57 mục.** Nguồn neo: **ô bảng 477 (44%)** · nhãn mục
329 (30%) · đề mục thật 262 (24%). **Chỉ khớp đề mục thì hỏng** — BCCS3 có 7 đề mục
trên 112 phần tử.

Ba lỗi đã sửa (đều có test hồi quy): **đo phủ một chiều là sai phép đo** (tên hạng mục
là *câu mô tả tiêu chí*, đề mục tài liệu là *tên ngắn* ⟹ dùng **F1 hai chiều**) ·
**bỏ sót nhãn dòng trong bảng** · **chấm thêm theo phần đầu tên hạng mục** (tiếng Việt
đặt từ chính trước).

⬜ **Độ CHÍNH XÁC chưa đo** — không có nhãn vàng cho "mục này đúng ra nằm ở đâu".
**Đang chờ tôi soi một bản `.md`** và chỉ ra dòng nào trỏ sai chỗ. Đây là việc duy nhất
đang chặn nghiệm thu 1.17.

❓ **8 mục checklist không định vị được ở BẤT KỲ bản nào trong 47 bản**, đi thành từng
cặp Application/Database: `3.1.6`/`3.2.7` (dự phòng theo 849/QĐ-CNVTQĐ) ·
`3.1.9`/`3.2.10` (nguồn request) · `3.1.10`/`3.2.11` (giao thức, port) ·
`3.1.15`/`3.2.16` (IOPS, latency mỗi request). **Cần hỏi đơn vị thẩm định.**

## 7. VIỆC KẾ TIẾP

Hàng đợi offline của Giai đoạn 1 đã cạn. Hai hướng, ưu tiên theo thứ tự:

**(a) Sửa 1.17 theo phản hồi của tôi** — nếu tôi đã gửi kết quả soi tay. Ưu tiên cao
nhất vì nó đang chặn nghiệm thu một mục đã giao được.

**(b) Giai đoạn 2 — C2 xử lý ảnh.** `767 ảnh trên 47 bản`, và PNX liên tục nhận xét về
ảnh sở cứ, nên đây là khoảng trống thật (0.11 đã chốt *"C2 là nhu cầu có thật ngay từ
đầu"*). **2.1** (trích ảnh kèm ngữ cảnh trước/sau) và **2.2** (phân loại ảnh: sơ đồ /
biểu đồ-dashboard / khác) **dựng và test được offline**; chỉ **2.3** (vision + OCR) mới
cần model. ✅ Endpoint **CÓ vision** (0.10) nên không phải xuống cấp OCR-only.

Pipeline đã sinh sẵn cảnh báo NT4 về ảnh (`canh_bao_nt4()` trong `pipeline.py`) — C2 sẽ
thay dần cảnh báo đó bằng nội dung đọc được.

## 8. Hạ tầng LLM — kết quả dò thật (0.10 + các lượt chạy sau)

- **KHÔNG phải cụm vLLM tự host** mà là **gateway OpenAI-compatible nội bộ**, 6 model
  (Claude opus-4-6 / sonnet-4-5 / haiku-4-5, gpt-oss-120b, Qwen2.5-Coder-7B).
  **Thôi gọi là "vLLM"** để không ai kỳ vọng `guided_json`.
- ⚠️ **`guided_json` được NHẬN nhưng BỎ QUA** (output bọc trong fence ⟹ không phải
  guided decoding thật). Client **LUÔN** validate + retry.
- ⚠️ **`reasoning_content` ĂN VÀO CHÍNH `max_tokens`** — đây là bẫy đã làm hỏng
  7/53 rồi 2/94 lượt gọi với `finish_reason=length` và `content` rỗng nhưng **HTTP 200**.
  Ngân sách token phải phủ cả suy luận lẫn đầu ra.
- ✅ **Vision CÓ.** ❌ **Embedding KHÔNG có** (`/v1/embeddings` 404/400) ⟹ BGE-M3 phải
  chạy cục bộ bằng `sentence-transformers`. ✅ Context **200k–1M**. ✅ Rate limit thoáng.
- **~40 giây mỗi lời gọi** (đo thật, không phải 5s như ước lượng ban đầu).
- ⬜ **Chưa chốt model chính cho C3.** Tạm `claude-opus-4-6`; **không dùng
  `gpt-oss-120b`** cho trích xuất (2/2 lần nhầm trường). Chốt sau khi chạy 1.13.

## 9. Quyết định ĐÃ CHỐT — đừng bàn lại

- **Thẩm định HAI VÒNG nối tiếp.** Vòng 1 = checklist (*"thành phần cần có đã có chưa"*,
  tiêu chí mặc định *"có thông tin thực chất là ĐẠT"*). Vòng 2 = Guideline, kiểm cách
  tính. **C7 CHẶN finding Vòng 2 cho mục đã trượt Vòng 1.** (Khác `lan_nhan_xet` = số
  lần PNX phản hồi — đừng lẫn.)
- **Đường vào chính là `.docx` người dùng tự viết**, không phải JSON web app (0.11).
- **Copilot KHÔNG phải trợ lý soạn thảo từng bước.**
- **Mã quy tắc `<NHÓM>-<số>` là CỐ ĐỊNH** — đổi là hỏng liên kết eval set.
- **`check` cho bất đẳng thức, `formula`+`compare_with`+`tolerance` cho tính lại** —
  không dùng đồng thời. **`applies_when`** cho quy tắc loại trừ nhau.
- **`scope`**: `he_thong` / `phan_he` / `phan_he_x_cong_nghe_luu_tru`.
- **KHÔNG số hóa 4 công thức code đang chạy sai** (`RDS-04`, `RDS-10`, `LBF-01`,
  `LBF-02`) — số hóa theo Guideline cho đúng.
- **Bản đã ký KHÔNG sạch** → không dùng làm chuẩn false positive.
- **Chất lượng ảnh sở cứ là việc người thẩm định tự đánh giá**, không phải của AI.
- **C3 dừng ở v6** · **đo recall trên mẫu 5 hồ sơ** · **ưu tiên C5/Vòng 1 trước C4**
  (mục 3 và 5 ở trên).

## 10. Cần TÔI duyệt trước khi làm — đừng tự quyết

1. **8 quy tắc không chạy được vì bảng tra chỉ nằm trong `note` dạng văn xuôi**:
   `STO-02/03/09/13`, `CPU-10`, `BAK-07`, `LAN-02`, `RCK-01`. Chép bảng vào Python
   **vi phạm NT3**; đề xuất là thêm mục `lookup:` vào `rules.yaml`. **Chờ tôi duyệt.**
2. **Lưới kiểm hợp lý** (`sanity.py`) chưa thành quy tắc trong `rules.yaml`.
3. **Không tự thêm/xoá quy tắc, không tự đổi `severity`.**
4. `CL-2.1` và `CL-2.4` chồng lấn — chờ ý kiến đơn vị thẩm định.

## 11. Hạn chế phải nêu khi công bố kết quả

1. **Nhãn không phải kiểm định độc lập** — gợi ý `rule_ref` và phán quyết kiểm mẫu đều
   do **cùng một tác nhân AI**. Ước tính máy đúng chủ đề **≈65%**.
2. **397/475 nhãn nhận gợi ý máy nguyên**, thường **dư mã** ⇒ recall **hào phóng hơn
   thực tế**.
3. **Chưa có cách đo false positive.**
4. Recall là *"so với người thẩm định"*, không phải sự thật tuyệt đối.
5. **Ba tầng `confidence` KHÔNG phân tách được chất lượng** (67–80%, ±12pp ở n=15).
   Đừng dùng để lọc cho tới khi hiệu chỉnh lại.
6. **Thiên lệch PHIÊN BẢN chưa gỡ**: PNX nhận xét bản TRƯỚC khi sửa, mà nhiều hồ sơ giữ
   nhiều bản ⟹ chạy trên bản đã sửa cho **recall thấp giả tạo**.

## 12. Cạm bẫy kỹ thuật — đã mất thời gian vì chúng

**Môi trường máy này (laptop):**
- **KHÔNG có `uv`.** Dùng **`python`** (pyenv 3.12) — ⚠️ **`py` trỏ vào Python 3.14.7
  mới cài, KHÔNG có phụ thuộc dự án.** Trong mạng nội bộ thì `py` lại đúng.
- Đã cài `streamlit` 1.63.0.
- **Bash tool không chạy được heredoc dài / `python -c` nhiều dòng** — viết ra file rồi
  chạy, hoặc dùng Write. PowerShell here-string `@'...'@` cũng bị băm.
- **In tiếng Việt trên Windows phải đặt `PYTHONIOENCODING=utf-8`**.
- Đường dẫn `/tmp/...` **không hoạt động** — dùng đường dẫn tương đối trong repo hoặc
  thư mục scratchpad.
- `scripts/unify_page_numbers.py` **CHỈ CHẠY MỘT LẦN — đã chạy rồi.**

**Dữ liệu thật:**
- Số mục Word là **đánh số tự động**, không nằm trong text; cấp 1 là **số La Mã**.
- **Ký tự PUA** U+F0A3 = `≤`, U+F0B3 = `≥` — **không phải bullet**.
- **YAML khối `>`**: dòng thụt sâu hơn dòng đầu **giữ nguyên xuống dòng**, hỏng biểu thức.
- Nháy cong `""` → `"`; từ bị **ngắt tại dấu gạch nối** khi đối chiếu trích dẫn.

**Bẫy tư duy đã sập ít nhất một lần:**
- **Đừng bịa định danh rồi giả định nó khớp.** `label_id` viết theo trí nhớ — không cái
  nào khớp, làm sai hẳn một tầng thống kê.
- **Đừng để giá trị mặc định lặng lẽ thay cho "không biết".** `convert(1,"vcpu","cint")`
  từng trả `1.0`.
- **Đừng im lặng bỏ qua quy tắc không chạy được** — `blocked()` luôn kèm lý do.
- **Đừng lặp thêm một vòng cải tiến khi chưa hiểu chế độ hỏng.** C3 mất ba vòng chữa
  triệu chứng trước khi ai đó đi đọc tài liệu và đếm xem nó có bao nhiêu con số.
- **Đừng tin con số của chính mình khi mẫu số do mình chọn.** "32/617 trường" nghe như
  C3 hỏng; thật ra 617 là con số vô nghĩa.
- **Đừng chọn tài liệu thử theo cảm tính.** Cả ngày đo trên hồ sơ chỉ có 8 nhãn.
- **Kiểm tra `PHIEN_BAN_C3` trong `src/version.py` khi đổi hành vi trích xuất** — đã
  quên tăng một lần, khiến file kết quả v5 tự nhận là v4.

## 13. Cách làm việc mong muốn

- Làm theo thứ tự `PLAN.md`, **không nhảy cóc**. Xong mục nào tick `[x]` và ghi ngắn gọn
  kết quả + lý do quyết định đáng nhớ.
- Text hướng tới người dùng cuối viết **tiếng Việt**; định danh code/log/commit tiếng
  Anh. ⚠️ Thực tế repo dùng **định danh tiếng Việt** (`chay`, `dinh_vi`, `bang_markdown`)
  — theo code xung quanh, đừng đổi phong cách giữa chừng.
- **Mọi hàm trong `validators/quantitative.py` phải có unit test.** Test phải là **hồi
  quy cho lỗi thật**.
- **Việc gì máy kiểm được thì viết script kiểm, đừng tin mắt.** Nhiều lỗi chỉ lộ khi
  chạy trên **tài liệu thật**.
- **Đừng viết file script phân tích trong scratchpad khi dữ liệu đã có trong context** —
  tôi đã từ chối một lần.
- Sửa `rules.yaml` xong **luôn chạy `scripts/validate_rules.py`**.
- **Ưu tiên độ chính xác hơn độ phủ.**
- Gặp chỗ mơ hồ/mâu thuẫn trong tài liệu thì **nêu ra, không tự quyết**.

## 14. Câu hỏi còn treo với đơn vị thẩm định

- **8 mục checklist vắng ở cả 47 bản** (mục 6) — khoảng trống hệ thống hay tên gọi khác?
- CPU/RAM/IOPS tính **"mỗi request"** (checklist) hay **"mức hệ thống"** (Guideline) hay
  **`factor = định cỡ/POC`** (web app)? Ba cách phân rã.
- `R104` — có **tập tối thiểu** các yếu tố ảnh hưởng không? Ép đủ 11 sinh cảnh báo sai
  hàng loạt.
- **Khâu cấp phát không có mục checklist nào phủ** (`R25+R32`, `R97`, `R108`, `R109`).
- **Cách đo false positive** khi bản đã ký không sạch.
- Mức `bình thường` có bắt buộc cơ chế dự phòng nội site nào không? (`ARC-12`)
- **Dung sai** khi so tổng toàn hệ với tổng các phân hệ? (`EVD-10`)
- Nguồn của **KPI Datanode ≤ 50%** và các ngưỡng Redis/Kafka/MariaDB nội bộ?
- Mâu thuẫn **tăng trưởng 01 năm** (web app) ↔ **cấp phát 06 tháng** (`ALC-01`)?
- Bản `.docx` cho **VAPS** và **MNP** (chỉ có PDF ⟹ 29 nhãn không với tới được).
- **Ngày tháng thẩm định** — 6 PNX bỏ trống ô ngày ⟹ 0.9 vẫn thiếu thời gian trung bình
  mỗi vòng. **Phải chụp baseline trước khi Copilot đi vào sử dụng.**

## 15. Ba lỗi tính toán đang chạy thật trên web app

Độc lập với Copilot, nên báo đội bảo trì (`rules-crossmap.md` mục 2):

| Mã | Lỗi | Hệ quả |
|---|---|---|
| **C-01** | Redis dùng `Kkpi = 0.8` cho RAM thay vì `0.9` | RAM dư ~12,5% |
| **C-02** | Redis áp hệ số KPI và sai số **hai lần** | RAM dư ~22% |
| **C-06** | LB/FW không áp `Kdph = 1.2` | Băng thông **thiếu 20%** |
