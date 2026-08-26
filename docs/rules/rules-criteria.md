# Mục 0.4 — Tiêu chí "thế nào là đạt" cho 33 quy tắc định tính

> **Nguồn:** `docs/rules/rules-flat-draft.md` (**R01–R110**), phân loại tại
> `docs/rules/rules-classification.md` — **77 định lượng `[đl]` / 33 định tính `[đt]`**
> (R66 chuyển sang định lượng ngày 2026-08-25).
> File này phủ **33 quy tắc định tính**, song song với `rules-formulas.md` (77 định lượng).
>
> **Vì sao file này khó hơn `rules-formulas.md`:** quy tắc định lượng có
> `computed_evidence` làm căn cứ — code tính ra số, không cãi được. Quy tắc định
> tính chỉ có **một** căn cứ: `rule_quote`, trích dẫn nguyên văn (NT2). Tiêu chí
> viết chung chung ("hợp lý", "đầy đủ") sẽ khiến LLM ở C5 tự chế tiêu chuẩn riêng —
> nguồn gốc phổ biến nhất của kết quả thiếu nhất quán, và là đường ngắn nhất tới
> rủi ro R6.
>
> **Trạng thái: XONG (2026-08-26).** Bước 1 — phân loại đủ 25 + 3 mẫu, văn phong
> đã duyệt. Bước 2 — **19 quy tắc còn lại đã viết đầy đủ** (mục 5).
> Bước 3 (2026-08-26) — **8 quy tắc bổ sung R102–R110** từ rà độ phủ (mục **5.7**).
> Tổng cộng **30/30 quy tắc cần tiêu chí đã có tiêu chí**; 2 quy tắc nhóm C không
> viết tiêu chí theo đúng thiết kế; 1 quy tắc do gộp R25+R32.

---

## Nguồn trích dẫn và số trang

**Nguồn chính thức: `docs/rules/.tmp-lan7/clean.txt`** — bản trích từ Guideline
**lần ban hành 07**, sinh bằng `scripts/extract_pdf_text.py`. Ở bản này **trang vật
lý bằng trang in trên tài liệu**, không lệch.

> **Đã đồng bộ toàn bộ (2026-08-26).** Bản trích lần 06 (`docs/rules/.tmp/clean.txt`)
> lệch 1 trang vì PDF đó có thêm một trang chữ ký ở đầu, nên `rules-flat-draft.md` và
> `rules-formulas.md` (viết theo bản 06) từng lớn hơn số trang in đúng 1 đơn vị.
> **Hai file đó đã được sửa đồng loạt ở mục 0.5** bằng `scripts/unify_page_numbers.py`
> và kiểm chéo bằng `scripts/check_page_consistency.py` (0 lệch).
> File này vốn đã dùng số trang in đúng nên **không phải sửa gì**.
>
> Lần 07 **không đổi quy tắc nào** so với lần 06 — đối chiếu đầy đủ ở
> [`rules-lan7-doi-chieu.md`](rules-lan7-doi-chieu.md). Ba trích dẫn mẫu ở mục 4
> đã được kiểm khớp nguyên văn với **cả hai** bản.

**Toàn bộ 26 trích dẫn trong file này đã được kiểm khớp nguyên văn với nguồn.**
Khi kiểm lại, phải chuẩn hóa hai thứ — nếu không sẽ báo lệch giả:

| Hiện tượng | Ví dụ | Cách xử lý |
|---|---|---|
| **Nháy cong** trong PDF | `"Dung lượng lưu trữ"` (U+201C/U+201D) | Quy về nháy thẳng trước khi so |
| **Từ bị ngắt ngang dòng tại dấu gạch nối** | `active-` / `standby` trên hai dòng | Nối lại thành `active-standby`, **không** chèn dấu cách |

Trích dẫn trong file này đã nối lại các từ bị ngắt dòng cho đúng nghĩa gốc — đó là
lý do có chỗ không khớp ký tự-với-ký tự nếu so thô với `clean.txt`.

---

## 1. Phân loại theo khả năng kiểm được

**Không phải cả 33 quy tắc đều nên sinh finding.** Đây là phần quan trọng nhất của
0.4: quy tắc không kiểm được mà vẫn bật lên sẽ tạo cảnh báo sai, mà một cảnh báo
sai gây thiệt hại lớn hơn nhiều một lỗi bỏ sót (rủi ro R6).

| Nhóm | Nghĩa | Số | Xử lý |
|---|---|:--:|---|
| **A** | Kiểm được từ nội dung tài liệu — bản chất là kiểm tính đầy đủ / cụ thể của phần trình bày | **24** | Vào `rules.yaml`, `enabled: true` |
| **B** | Kiểm được **một phần** — chỉ xác nhận tài liệu *có nêu / có dẫn chiếu*, KHÔNG xác minh được văn bản hay chữ ký thật | **7** | Vào `rules.yaml`, câu finding phải nói rõ giới hạn |
| **C** | Không kiểm được, hoặc không phải quy tắc | **2** | Xem mục 1.3 |

> **Cập nhật 2026-08-26:** thêm 8 quy tắc R102–R110 (mục 5.7) — 6 vào nhóm A
> (R103, R104, R106, R107, R108, R110) và 2 vào nhóm B (R102, R109).
> Tổng 25 → **33**.

### 1.1. Nhóm A — kiểm được (24)

| Mã tạm | Quy tắc tóm tắt | Trang |
|---|---|---|
| R10 | Dự phòng không quá tải khi 1 node lỗi | 9/44 |
| R14 | Hiệu năng cao vượt cấu hình ảo hóa → định cỡ máy chủ vật lý | 9/44 |
| R23 | Phân biệt dung lượng khả dụng / dung lượng thô | 7/44 |
| R25 | Xác định yếu tố ảnh hưởng khi mở rộng / thu hẹp | 10/44 |
| R26 | Dạng I — định cỡ theo hệ tham chiếu tương đồng | 11/44 |
| R27 | Dạng I không có hệ tham chiếu → hoàn thiện sản phẩm + kiểm thử | 11/44 |
| R28 | Dạng II — định cỡ bằng môi trường kiểm thử | 11/44 |
| R29 | Dạng III — định cỡ theo hiện trạng + yêu cầu mở rộng | 12/44 |
| R32 | Chỉ rõ yếu tố scale up / scale out + ngưỡng tới hạn 1 node | 14–15/44 |
| R35 | Thông số chọn phải ảnh hưởng năng lực xử lý / quản lý | 16/44 |
| R37 | Chỉ rõ cấu hình CPU / RAM / ổ cứng đầy đủ | 20/44 |
| R53 | Mô tả tài nguyên dedicated, swap / huge-page | 25/44 |
| R59 | Hệ hiệu năng cao phải tính hiệu năng từng phân vùng | 26/44 |
| R67 | Hệ đọc/ghi ngẫu nhiên cao nên dùng ổ tốc độ cao | 30/44 |
| R91 | Triển khai trên Cloud Tập đoàn, trừ ngoại lệ có lý do | 40/44 |
| R95 | Big data → Bare-Metal; còn lại → ảo hóa | 41/44 |
| R97 | Thu hồi: ưu tiên giảm số máy chủ trước khi giảm cấu hình | 42/44 |
| R98 | Nêu công cụ kiểm thử chuẩn (sysbench / jmeter / ab) | 43–44/44 |
| R103 | Nêu tính sẵn sàng (phút/tháng) và downtime mỗi sự cố | 18/44 |
| R104 | Nêu các yếu tố ảnh hưởng thông số tài nguyên máy chủ | 18/44 |
| R106 | Module đủ tải vẫn phải thiết kế cho sẵn sàng / dự phòng | 20/44 |
| R107 | Có giải pháp sao lưu + cộng thêm năng lực cho tác vụ backup | 20/44 |
| R108 | Quy hoạch cấp phát: tránh lưu lượng vòng, an toàn khi lỗi phần cứng | 40/44 |
| R110 | Bảng thông số đầu vào tách tải theo nghiệp vụ kèm tỉ lệ | 17/44 |

### 1.2. Nhóm B — kiểm được một phần (7)

| Mã tạm | Quy tắc tóm tắt | Copilot kiểm được gì | Trang |
|---|---|---|---|
| R30 | Thông số đầu vào phải được lãnh đạo xác nhận bằng văn bản | Tài liệu **có nêu / dẫn chiếu** văn bản xác nhận không | 14/44 |
| R31 | Biên bản kiểm thử phải được xác nhận bằng văn bản | như trên | 14/44 |
| R33 | Hạ tầng Tập đoàn → xin ý kiến thẩm định TCT VTNet | Có nêu đã xin / đang xin ý kiến không | 15/44 |
| R92 | Cấp phát chỉ khi đủ hồ sơ (tờ trình, quy hoạch, kiểm thử, tài liệu định cỡ) | Có liệt kê đủ 4 loại hồ sơ không | 40/44 |
| R99 | Thống nhất công cụ đo + lưu vết, ký xác nhận | Có nêu công cụ đã thống nhất và nơi lưu vết không | 44/44 |
| R102 | Mức dự phòng căn cứ phân loại hệ thống (theo 849/QĐ) | Có nêu phân loại **và** nối được với mức dự phòng không; **không** đối chiếu được nội dung 849/QĐ (chưa có văn bản) | 9/44 |
| R109 | Thống nhất phương án cấp phát với TCT VTNet | Tài liệu có nêu / dẫn chiếu việc đã thống nhất không | 40/44 |

> **Bắt buộc khi viết câu finding cho nhóm B:** nêu rõ Copilot chỉ kiểm được *tài
> liệu có nói tới hay không*, **không** xác minh được văn bản có thật, chữ ký có
> hợp lệ. Không nói rõ thì người dùng hiểu nhầm là đã qua thẩm định.

### 1.3. Nhóm C — không đưa vào vận hành (2)

Hai trường hợp, hai lý do khác nhau:

**R24** — *"Định cỡ dựa trên KPI giả định tương lai… kết quả không chính xác 100%"*
→ Đây là **câu tuyên bố**, không phải yêu cầu. Không nội dung nào trong bản sizing
có thể vi phạm nó, nên không có tiêu chí ĐẠT/KHÔNG ĐẠT nào viết được.
**Loại khỏi `rules.yaml`.** Ghi lại lý do ở đây để sau này không ai thêm nhầm.

**R34** — *"Tài liệu định cỡ hoàn thiện theo mẫu Phụ lục 01"*
→ **Phụ lục 01 không có trong file PDF** (tài liệu kết thúc ở trang 44/44). Không
có mẫu thì không viết được tiêu chí "đủ mục" nào cả.
→ Vào `rules.yaml` với `enabled: false`, chờ phụ lục. Đã nằm trong mục **0.12**.
Lưu ý: phụ lục này cũng là đầu vào của mục **1.16** (mẫu Word chuẩn) — hai việc
cùng chờ một thứ.

> **R66 đã rời khỏi file này.** Trước đây nằm ở nhóm C với đề xuất chuyển sang định
> lượng. **Đã chốt 2026-08-25: chuyển.** Căn cứ: R55 (*IOPS tối đa theo loại ổ*) vốn
> đã là `đl` "ràng buộc (bảng giá trị)", mà R66 có đúng cấu trúc đó — bảng tra theo
> loại ổ, code so dải, không cần phán đoán. Chữ "thông dụng" được thể hiện bằng
> `severity: minor`, không bằng cách xếp sang định tính.
> Công thức nay ở `rules-formulas.md`; lý do đầy đủ ở `rules-classification.md`.

---

## 2. Khử trùng trong nội bộ 25 quy tắc

**R25 ↔ R32 — gộp làm một.** Cả hai cùng yêu cầu chỉ rõ yếu tố scale up / scale out.
R25 (trang 10/44) nêu ở phần khái niệm, R32 (trang 14/44) nêu lại thành một bước
trong bảng quy trình. Để riêng thì một bản sizing thiếu phần này sẽ bị bắt lỗi
**hai lần** với hai trích dẫn khác nhau — người dùng thấy như công cụ bị lặp.
→ Một quy tắc, **hai `source_doc`**. R32 giữ vai trò trích dẫn chính vì câu chữ
cụ thể hơn và có ví dụ 100TPS → 200TPS.

**R26 ↔ R27 — giữ riêng.** Không phải trùng lặp mà là hai nhánh bổ sung của Dạng I:
R26 khi *có* hệ tham chiếu tương đồng, R27 khi *không có*. Liên kết chéo bằng
`see_also` để C5 biết hai quy tắc loại trừ nhau — đúng một trong hai áp dụng, cái
còn lại phải trả về `không áp dụng`.

**Sau khử trùng: 25 → 24 quy tắc định tính.**

---

## 3. Nhóm mã — số thứ tự để lại cho mục 0.5

Kế hoạch ban đầu định gán mã đầy đủ ở 0.4. **Không làm được**, vì đụng độ: nhóm
`STO`, `TST`, `ARC` sẽ chứa cả quy tắc định lượng (R11, R12, R13, R15, R55, R57…)
lẫn định tính, mà 75 quy tắc định lượng chưa được đánh số. Gán số bây giờ thì 0.5
phải đánh số lại từ đầu.

→ **0.4 chỉ gán nhóm.** Số thứ tự gán một lượt cho cả 100 quy tắc ở mục 0.5.
Trong file này dùng dạng `EVD-xx`.

| Nhóm | Nghĩa | Quy tắc định tính thuộc nhóm |
|---|---|---|
| `ARC` | Kiến trúc, dự phòng, hạ tầng | R10, R14, R91, R95, **R102**, **R106** |
| `EVD` | Sở cứ & mô tả bắt buộc | R23, **R25+R32**, R35, R37, R53, R59, **R103**, **R104**, **R110** |
| `MTH` | Phương pháp định cỡ (Dạng I/II/III) | R26, R27, R28, R29 |
| `PRC` | Thủ tục & quy trình | R30, R31, R33, R34, R92, R97, R99, **R109** |
| `STO` | Lưu trữ | R67 |
| `TST` | Kiểm thử hiệu năng | R98 |
| `BAK` | Sao lưu | **R107** |
| `ALC` | Cấp phát / thu hồi | **R108** |

Ba nhóm `ARC`, `EVD`, `MTH` là **mới** — đã bổ sung vào `rules-crossmap.md` mục 6.
`BAK` và `ALC` đã có sẵn trong hệ nhóm ở `rules-crossmap.md` mục 6, nhưng đây là lần
đầu chúng nhận quy tắc **định tính** — thêm một lý do nữa để **số thứ tự gán một lượt ở
mục 0.5** (nhóm `ALC`, `BAK`, `ARC`, `STO` nay đều chứa cả ĐL lẫn ĐT).

---

## 4. Ba quy tắc mẫu

Chọn lệch nhau để thử khuôn trên ba tình huống khó nhất: kiểm nội dung (A), thủ tục
có giới hạn (B), và phán đoán tình huống (A nhưng mơ hồ nhất).

> **Cập nhật khuôn 2026-08-25 — thêm `checklist_ref`.** Ba mẫu này viết trước khi
> nhận checklist thẩm định, nên ban đầu thiếu trường nối sang mục checklist tương
> ứng. Đã bổ sung. Từ Bước 2 trở đi, **mọi quy tắc đều phải có `checklist_ref`**
> (hoặc ghi rõ là không thuộc mục checklist nào) — vì báo cáo C7 sẽ xếp theo thứ tự
> checklist, quy tắc không gắn được mục sẽ không biết in ra chỗ nào.
>
> **Cạm bẫy khi gắn `checklist_ref` — đừng nhầm đầu vào với đầu ra.** Ví dụ R37 và
> `CL-3.x.15` cùng nói về "IOPS và latency", nhưng khác nhau về bản chất:
> R37 là **IOPS/latency đo được của hệ tham chiếu** (số liệu *đầu vào*), còn
> `CL-3.x.15` là **IOPS/latency tính ra cho hệ mới** (kết quả *đầu ra*). Gắn nhầm
> thì Copilot sẽ báo "đã có" cho một mục thực ra còn thiếu.

---

### EVD-xx — Cấu hình hệ thống tham chiếu phải nêu đủ CPU, RAM, ổ cứng

- `legacy_ref: [R37]` · `checklist_ref: [CL-2.5]` · Trang **20/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `applies_to_module:` (mọi)
- `severity: major`

**Trích dẫn nguyên văn**

> Cấu hình hệ thống:
> - CPU: cần chỉ rõ số lượng và dòng (model) cụ thể, lưu ý đối với ảo hoá nên chỉ
>   rõ số lượng vCPU tương ứng với model pCPU (vật lý) hoặc CPU vật lý tham chiếu.
> - RAM: Dung lượng RAM của máy chủ, tính theo GB.
> - Ổ cứng: Dung lượng khả dụng (tính theo GB, sau RAID) hoặc dung lượng ổ cứng nếu
>   không có RAID của máy chủ. Cần chỉ rõ IOPS và latency cho từng phân vùng phục
>   vụ các mục đích hoặc nghiệp vụ khác nhau.

> ⚠️ **Chú ý sắc thái:** tài liệu dùng **"cần chỉ rõ"** (bắt buộc) cho CPU, ổ cứng,
> IOPS/latency — nhưng dùng **"nên chỉ rõ"** (khuyến nghị) riêng cho phần vCPU ↔
> model pCPU. Hai mức khác nhau, không được gộp thành một. Đây chính là lý do phải
> trích nguyên văn thay vì diễn giải lại.

**Phạm vi áp dụng:** mọi bản sizing có mô tả hệ thống tham chiếu hoặc hệ thống hiện
trạng (Dạng II và Dạng III).

**KHÔNG áp dụng khi:** bản sizing thuộc Dạng I và không có hệ thống tham chiếu nào
(khi đó R27 áp dụng thay). Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — phải có đủ **cả bốn**:
1. **CPU:** nêu số lượng **và** dòng/model cụ thể (ví dụ `2 × Intel Xeon Gold 6248R`).
   Chỉ ghi số lượng mà không có model → chưa đạt.
2. **RAM:** nêu dung lượng theo **GB**.
3. **Ổ cứng:** nêu dung lượng **khả dụng sau RAID** (hoặc nêu rõ là không dùng RAID).
4. **IOPS và latency của từng phân vùng** phục vụ mục đích/nghiệp vụ khác nhau —
   không phải một con số gộp cho cả máy.

Riêng với hệ ảo hóa, nêu được vCPU tương ứng model pCPU là **điểm cộng**, thiếu thì
hạ xuống `minor` chứ không tính là không đạt (vì tài liệu chỉ dùng "nên").

**Tiêu chí KHÔNG ĐẠT** — bất kỳ trường hợp nào sau đây:
- Bảng cấu hình chỉ có số lượng CPU, không có model.
- Ổ cứng chỉ ghi dung lượng thô, hoặc không nói rõ đã trừ RAID hay chưa
  (liên quan R23 — xem `see_also`).
- Có nhiều phân vùng nhưng chỉ nêu một giá trị IOPS/latency chung.
- Thiếu hẳn IOPS hoặc latency.

**Vị trí cần soi:** mục "Thông tin đầu vào" — bảng cấu hình hệ thống tham chiếu /
hiện trạng. Trong web app tương ứng tab **Thông tin đầu vào** và bảng
`baseline-table-body` của tab **Định cỡ hệ thống**.

**Ví dụ ĐẠT** `[minh họa]`
> Hệ thống tham chiếu gồm 03 máy chủ, mỗi máy: 2 × Intel Xeon Gold 6248R (24 core),
> RAM 256 GB. Ổ cứng: /u01 800 GB khả dụng sau RAID 10, IOPS đo được 12.400,
> latency 0,8 ms; /u02 4 TB khả dụng sau RAID 6, IOPS 950, latency 6,2 ms.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống tham chiếu: 3 máy chủ, 48 CPU, RAM 256 GB, ổ cứng 6 TB, IOPS khoảng 10.000.

*(Thiếu model CPU; không rõ 6 TB là thô hay khả dụng; IOPS gộp chung cho cả máy,
không tách phân vùng; không có latency.)*

`see_also: [R23]` — phân biệt dung lượng khả dụng / dung lượng thô.

---

### PRC-xx — Thông số đầu vào phải được lãnh đạo xác nhận bằng văn bản

- `legacy_ref: [R30]` · `checklist_ref: [CL-2.5]` · Trang **14/44** · Nhóm kiểm: **B**
- `applies_to_equipment:` (mọi) · `applies_to_module:` (mọi)
- `severity: major`

**Trích dẫn nguyên văn**

> Các thông số đầu vào phục vụ định cỡ phải được lãnh đạo đơn vị chủ trì sản phẩm
> xác nhận bằng văn bản. Trường hợp yêu cầu đến từ đơn vị, nhu cầu kinh doanh, cần
> có xác nhận của đơn vị/bộ phận liên quan ký xác nhận nhu cầu.

> *Nguồn nằm trong bảng quy trình định cỡ, bước 1 "Chuẩn bị thông số đầu vào".
> Text gốc bị ngắt dòng theo ô bảng hẹp (dòng 558–566 của `.tmp-lan7/clean.txt`) —
> trích dẫn trên đã nối lại và đối chiếu khớp từng chữ.*

**⚠️ Giới hạn kiểm — bắt buộc nêu trong finding:** Copilot chỉ kiểm được **tài liệu
có nêu hoặc dẫn chiếu văn bản xác nhận hay không**. Copilot **không** xác minh được
văn bản đó có thật, chữ ký có hợp lệ, người ký có đúng thẩm quyền. Câu finding phải
nói rõ điều này, nếu không người dùng sẽ hiểu nhầm là đã qua thẩm định.

**Phạm vi áp dụng:** mọi bản sizing.

**KHÔNG áp dụng khi:** không có trường hợp nào — đây là yêu cầu bắt buộc chung.

**Tiêu chí ĐẠT** — một trong hai:
1. Tài liệu **dẫn chiếu cụ thể** văn bản xác nhận thông số đầu vào: nêu được **số
   hiệu / ngày / người ký hoặc chức danh người ký**. Ví dụ: *"Theo văn bản số
   123/TTr-KD ngày 12/6/2026 do Giám đốc Trung tâm Kinh doanh ký xác nhận."*
2. Tài liệu **đính kèm** văn bản đó và có nhắc tới trong phần sở cứ.

Nếu yêu cầu đến từ đơn vị kinh doanh: phải có thêm xác nhận của đơn vị/bộ phận liên
quan, không chỉ lãnh đạo đơn vị chủ trì sản phẩm.

**Tiêu chí KHÔNG ĐẠT:**
- Không nhắc gì tới việc thông số đầu vào đã được xác nhận.
- Chỉ nói chung chung *"đã được lãnh đạo phê duyệt"* mà không có số hiệu, ngày,
  hoặc chức danh người ký — không đủ để người thẩm định truy được văn bản.
- Nguồn thông số đầu vào ghi là *"theo ước tính của nhóm dự án"* mà không có xác nhận.

**Vị trí cần soi:** mục "Thông tin đầu vào" / phần sở cứ số liệu, và danh mục tài
liệu đính kèm.

**Ví dụ ĐẠT** `[minh họa]`
> Thông số đầu vào (dự kiến 50.000 CCU giờ cao điểm) được lãnh đạo Trung tâm Sản
> phẩm xác nhận tại văn bản số 214/XN-TTSP ngày 03/6/2026 (đính kèm Phụ lục 3).

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Thông số đầu vào 50.000 CCU do nhóm dự án ước tính dựa trên kinh nghiệm triển
> khai các hệ thống tương tự, đã được lãnh đạo thống nhất.

*(Không có số hiệu văn bản, không có ngày, không rõ ai ký — người thẩm định không
truy được. Đồng thời chạm cả R30 lẫn nhóm "thiếu sở cứ".)*

`see_also: [R31]` — biên bản kiểm thử hiệu năng, yêu cầu xác nhận tương tự.

---

### MTH-xx — Dạng I: phải nêu đặc điểm tương đồng của hệ thống tham chiếu

- `legacy_ref: [R26]` · `checklist_ref: [CL-2.1, CL-2.4]` · Trang **11/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `applies_to_module:` (mọi)
- `severity: major` (nâng lên `critical` nếu là hệ CNTT nội bộ Tập đoàn — xem dưới)

**Trích dẫn nguyên văn**

> Cơ sở định cỡ: căn cứ vào các hệ thống tham chiếu có các đặc điểm tương đồng.
> Hệ thống tương đồng là hệ thống có đặc điểm chung về kiến trúc, công nghệ, các
> chức năng, luồng nghiệp vụ chính và đối tượng sử dụng. Đơn vị phát triển cần nêu
> các đặc điểm tương đồng về kiến trúc, công nghệ, chức năng giữa hệ thống định cỡ
> và hệ thống tham chiếu.

**Trích dẫn bổ sung — ràng buộc cấp phát** (cùng trang):

> Với các hệ thống CNTT nội bộ của Tập đoàn và các đơn vị trực thuộc Tập đoàn,
> không thực hiện cấp phát tài nguyên trên hạ tầng CNTT của Tập đoàn với các hệ
> thống CNTT định cỡ theo phương pháp này. Yêu cầu các hệ thống CNTT phải được
> kiểm thử hiệu năng và định cỡ chính xác trước khi cấp phát.

**Phạm vi áp dụng:** bản sizing **Dạng I** — chưa có sản phẩm phần mềm, định cỡ sơ
bộ để phục vụ cấu hình hệ thống kiểm thử, đầu tư thử nghiệm hoặc tham gia thầu.

**KHÔNG áp dụng khi:**
- Bản sizing đã có sản phẩm phần mềm (Dạng II) hoặc là nâng cấp hệ thống đang chạy
  (Dạng III). Trả về `không áp dụng`.
- Dạng I nhưng **không có** hệ tham chiếu tương đồng nào → R27 áp dụng thay, quy
  tắc này trả về `không áp dụng`.

**Tiêu chí ĐẠT** — phải nêu được đặc điểm tương đồng trên **cả năm** phương diện mà
tài liệu liệt kê, so sánh giữa hệ định cỡ và hệ tham chiếu:
1. Kiến trúc
2. Công nghệ
3. Các chức năng
4. Luồng nghiệp vụ chính
5. Đối tượng sử dụng

Nêu tên hệ tham chiếu thôi là chưa đủ — tài liệu yêu cầu *"nêu các đặc điểm tương
đồng"*, tức phải có so sánh, không phải chỉ dẫn tên.

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ nêu tên hệ tham chiếu, không so sánh đặc điểm nào.
- So sánh qua loa một hai phương diện (thường chỉ "cùng dùng Java/Oracle") rồi kết
  luận tương đồng.
- Hệ tham chiếu khác hẳn đối tượng sử dụng hoặc luồng nghiệp vụ chính nhưng vẫn
  được dùng làm cơ sở (ví dụ lấy hệ nội bộ vài trăm người dùng làm tham chiếu cho
  hệ phục vụ khách hàng hàng triệu người).

**Nâng mức nghiêm trọng:** nếu bản sizing là **hệ CNTT nội bộ Tập đoàn** và định cỡ
theo Dạng I, thì theo trích dẫn bổ sung, hệ đó **không được cấp phát** trên hạ tầng
Tập đoàn cho tới khi có kiểm thử hiệu năng. Trường hợp này sinh finding riêng mức
`critical` — người dùng cần biết ngay là hồ sơ sẽ bị trả lại bất kể phần còn lại
viết tốt đến đâu.

**Vị trí cần soi:** mục "Yêu cầu bài toán" (xác định dạng định cỡ) và "Thông tin
đầu vào" (mô tả hệ tham chiếu).

**Ví dụ ĐẠT** `[minh họa]`
> Hệ thống định cỡ tham chiếu hệ thống Quản lý đơn hàng đang vận hành từ 2024.
> Tương đồng về: kiến trúc (microservice trên K8S, 3 lớp); công nghệ (Spring Boot,
> MariaDB, Redis, Kafka); chức năng (tạo/tra cứu/cập nhật đơn, đối soát cuối ngày);
> luồng nghiệp vụ chính (đơn hàng → duyệt → xuất kho → đối soát); đối tượng sử dụng
> (nhân viên giao dịch tại điểm bán, quy mô 3.000–4.000 người dùng đồng thời).
> Khác biệt: hệ mới bổ sung kênh khách hàng tự phục vụ, ước tăng 40% lượt tra cứu.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Định cỡ dựa trên hệ thống Quản lý đơn hàng hiện có, là hệ thống tương tự về quy
> mô và công nghệ.

*(Không so sánh phương diện nào cụ thể; "tương tự về quy mô và công nghệ" là khẳng
định chứ không phải sở cứ.)*

`see_also: [R27, R28, R29]` — ba dạng định cỡ còn lại, loại trừ lẫn nhau.

---

## 4b. Phạm vi file này — chỉ VÒNG 2

> **Làm rõ 2026-08-25.** Thẩm định chạy hai vòng nối tiếp
> ([chi tiết](rules-checklist-flat.md#-tiêu-chí-mặc-định-vòng-1--áp-cho-mọi-mục-không-có-tiêu-chí-riêng)):
>
> - **Vòng 1 — checklist:** *thành phần cần có đã có chưa?* Tiêu chí mặc định
>   "có thông tin thực chất là ĐẠT", dùng chung cho 37 quy tắc `CL-*`.
>   **Không thuộc file này.**
> - **Vòng 2 — tài liệu định cỡ:** *cách tính toán, định cỡ có đúng không?*
>   **Đây mới là phạm vi file này**, cùng với `rules-formulas.md`.
>
> Cả ba mẫu ở mục 4 đều là quy tắc **Vòng 2** — chúng đòi hỏi nội dung đạt một mức
> cụ thể (R37 phải có model CPU, dung lượng sau RAID, IOPS/latency **từng phân vùng**),
> chứ không chỉ "có phần cấu hình". Đúng như vậy, không cần sửa.
>
> Ranh giới cần giữ khi viết tiếp: tiêu chí trong file này **được phép** đòi hỏi
> mức chi tiết; tiêu chí Vòng 1 thì **không** — chỉ hỏi có hay không.

---

## 5. Bước 2 — 19 quy tắc còn lại

Bước 1 đã lập khuôn; phần này viết 19 quy tắc còn lại theo đúng khuôn đó, xếp theo
nhóm mã để quy tắc liên quan nằm cạnh nhau.

> Mọi trích dẫn dưới đây lấy từ `docs/rules/.tmp-lan7/clean.txt` và đã đối chiếu
> khớp nguyên văn. Ví dụ đều gắn nhãn `[minh họa]` vì chưa có bản sizing thật.
>
> **Tất cả 19 quy tắc này thuộc VÒNG 2** (kiểm cách tính, mức chi tiết) — không phải
> Vòng 1. Xem mục 4b.

---

### 5.1. Nhóm `ARC` — kiến trúc, dự phòng, hạ tầng

---

#### ARC-xx — Hệ dự phòng không được quá tải khi một node lỗi

- `legacy_ref: [R10]` · `checklist_ref: [CL-2.11, CL-3.x.6]` · Trang **9/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: critical`

**Trích dẫn nguyên văn**

> Với các hệ thống dự phòng (active-active hoặc active-standby), thiết bị không hoạt
> động quá tải khi 1 node bị lỗi.

**Phạm vi áp dụng:** mọi hệ thống có từ 2 node trở lên ở bất kỳ phân hệ nào.

**KHÔNG áp dụng khi:** phân hệ chỉ có 1 node và tài liệu nêu rõ đây là thành phần
không yêu cầu dự phòng. Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — tài liệu phải cho thấy đã tính đến kịch bản mất 1 node:
1. Nêu rõ mô hình dự phòng của phân hệ (active-active hay active-standby).
2. Có phép tính hoặc lập luận cho thấy tải dồn về các node còn lại **vẫn dưới ngưỡng
   KPI** (CPU ≤ 75%, RAM ≤ 90%, ổ cứng ≤ 80% — theo R02/R03/R04).
3. Với active-active N node: tải mỗi node khi mất 1 node là `tổng_tải / (N-1)`, và
   giá trị đó phải được đối chiếu với ngưỡng.

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ khai "có dự phòng" mà không có phép tính kịch bản mất node.
- Tính tải chia đều cho N node nhưng **không** xét trường hợp còn N-1.
- Cấu hình vừa khít ở trạng thái bình thường — mất 1 node là vượt ngưỡng.

**Vị trí cần soi:** mục mô hình hệ thống và bảng định cỡ từng phân hệ.

**Ví dụ ĐẠT** `[minh họa]`
> Cụm App gồm 03 node active-active, mỗi node 16 vCPU. Tải giờ cao điểm 24 vCPU,
> phân bổ 8 vCPU/node (50%). Khi mất 01 node: 24/2 = 12 vCPU/node = 75% — vẫn ở
> ngưỡng cho phép.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Cụm App gồm 03 node active-active, mỗi node 16 vCPU, tải 24 vCPU chia đều 8
> vCPU/node. Hệ thống có dự phòng đầy đủ.

*(Không xét kịch bản mất node. Thực tế mất 1 node là 12/16 = 75%, sát ngưỡng; mất
node ở cụm 2 node sẽ vượt.)*

`see_also: [R11, R101]`

---

#### ARC-xx — Dịch vụ vượt cấu hình ảo hóa phải định cỡ máy chủ vật lý

- `legacy_ref: [R14]` · `checklist_ref: [CL-3.x.3]` · Trang **9/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Với dịch vụ yêu cầu hiệu năng cao vượt cấu hình quy định máy chủ ảo hóa, thực hiện
> định cỡ máy chủ chạy trên môi trường vật lý.

**Phạm vi áp dụng:** phân hệ được khai là chạy trên máy chủ **ảo hóa**.

**KHÔNG áp dụng khi:** phân hệ đã khai chạy trên máy chủ vật lý hoặc Bare-Metal.

**Tiêu chí ĐẠT** — một trong hai:
1. Cấu hình mỗi VM nằm trong giới hạn ảo hóa (**≤ 32 vCPU và ≤ 128 GB RAM**, theo R13);
2. Hoặc vượt giới hạn nhưng tài liệu **đã chuyển sang định cỡ máy chủ vật lý** và
   nêu rõ lý do.

**Tiêu chí KHÔNG ĐẠT:**
- Khai VM với > 32 vCPU hoặc > 128 GB RAM mà vẫn để hình thức cấp phát là ảo hóa.
- Nhu cầu tính ra vượt giới hạn nhưng tài liệu "ép" xuống cho vừa ngưỡng mà không
  giải trình.

> Phần so ngưỡng 32 vCPU / 128 GB là **định lượng (R13)** — C4 làm. Quy tắc này chỉ
> kiểm phần **giải trình khi vượt**, tức phần C5.

**Vị trí cần soi:** bảng đề xuất cấu hình từng phân hệ.

**Ví dụ ĐẠT** `[minh họa]`
> Phân hệ xử lý luồng thời gian thực cần 48 vCPU, vượt giới hạn 32 vCPU của máy chủ
> ảo hóa nên định cỡ trên máy chủ vật lý 2 × 24 core.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Phân hệ xử lý luồng thời gian thực: 01 VM cấu hình 48 vCPU, 192 GB RAM.

`see_also: [R13, R95]`

---

#### ARC-xx — Hệ thống nội bộ phải triển khai trên Cloud Tập đoàn, trừ ngoại lệ có lý do

- `legacy_ref: [R91]` · `checklist_ref: [CL-2.2, CL-3.x.3]` · Trang **40/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [cap_phat]` · `severity: major`

**Trích dẫn nguyên văn**

> Toàn bộ các hệ thống CNTT nội bộ Tập đoàn phải triển khai, tích hợp với hạ tầng
> điện toán đám mây (Cloud) của Tập đoàn, ngoại trừ các hệ thống triển khai phân tán
> tại các vị trí không có hạ tầng Cloud hoặc yêu cầu đặc thù về điều kiện triển khai
> (cô lập về hạ tầng, thiết bị đặc chủng...).

**Phạm vi áp dụng:** hệ thống CNTT **nội bộ Tập đoàn**.

**KHÔNG áp dụng khi:** hệ thống phục vụ kinh doanh / triển khai cho khách hàng ngoài.

**Tiêu chí ĐẠT** — một trong hai:
1. Tài liệu nêu rõ hệ thống triển khai trên hạ tầng Cloud Tập đoàn;
2. Hoặc **không** triển khai trên Cloud nhưng nêu rõ thuộc ngoại lệ nào — phân tán ở
   vị trí không có Cloud, cô lập hạ tầng, hoặc thiết bị đặc chủng — kèm lý do cụ thể.

**Tiêu chí KHÔNG ĐẠT:**
- Không nói gì về hình thức hạ tầng triển khai.
- Đề xuất hạ tầng riêng mà chỉ nói chung chung *"do yêu cầu đặc thù"*, không chỉ ra
  thuộc ngoại lệ nào.

**Vị trí cần soi:** mục mô tả tổng quan hệ thống và mô hình vật lý.

**Ví dụ ĐẠT** `[minh họa]`
> Hệ thống triển khai trên Cloud Tập đoàn tại DC Hòa Lạc. Riêng 04 node thu thập dữ
> liệu đặt phân tán tại 04 tỉnh chưa có hạ tầng Cloud — thuộc ngoại lệ triển khai
> phân tán.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống đề xuất đầu tư 12 máy chủ vật lý đặt tại phòng máy đơn vị do yêu cầu đặc thù.

`see_also: [R95]`

---

#### ARC-xx — Big data cấp Bare-Metal, hệ còn lại cấp máy ảo

- `legacy_ref: [R95]` · `checklist_ref: [CL-3.x.3]` · Trang **41/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [cap_phat, may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Các hệ thống Big data (xử lý tập dữ liệu lớn phân tán): Cấp phát Bare-Metal trên
> hạ tầng Cloud (ứng dụng được cài đặt trên các server vật lý, không sử dụng ảo hóa).
> Các hệ thống còn lại: Cấp phát máy chủ ảo hóa trên hạ tầng Cloud để tận dụng các
> ưu điểm của hạ tầng này (tận dụng tối đa tài nguyên phần cứng của máy chủ vật lý,
> tiết kiệm chi phí đầu tư hệ thống).

**Phạm vi áp dụng:** mọi phân hệ được cấp phát trên hạ tầng Cloud Tập đoàn.

**KHÔNG áp dụng khi:** hệ thống thuộc ngoại lệ không triển khai trên Cloud (xem R91).

**Tiêu chí ĐẠT:**
1. Phân hệ Big data (Hadoop, Spark, HDFS, Kafka quy mô lớn, xử lý dữ liệu phân tán)
   → khai **Bare-Metal**.
2. Phân hệ còn lại → khai **máy chủ ảo hóa**.
3. Trường hợp lệch khỏi hai quy tắc trên phải có giải trình.

**Tiêu chí KHÔNG ĐẠT:**
- Hệ Big data khai chạy trên VM mà không giải trình.
- Hệ thường xin cấp Bare-Metal mà không nêu lý do (thường là dấu hiệu xin dư tài nguyên).
- Không khai hình thức cấp phát.

**Vị trí cần soi:** bảng đề xuất cấu hình từng phân hệ, cột hình thức cấp phát.

**Ví dụ ĐẠT** `[minh họa]`
> Phân hệ Hadoop (06 datanode) cấp Bare-Metal trên Cloud. Phân hệ Application và
> MariaDB cấp máy chủ ảo hóa.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Toàn bộ hệ thống gồm cụm Spark 08 node và 04 máy chủ ứng dụng, đề xuất cấp Bare-Metal.

*(Không giải thích vì sao máy chủ ứng dụng cũng cần Bare-Metal.)*

`see_also: [R14, R91]`

---

### 5.2. Nhóm `EVD` — sở cứ và mô tả bắt buộc

---

#### EVD-xx — Phân biệt rõ dung lượng lưu trữ khả dụng và dung lượng thô

- `legacy_ref: [R23]` · `checklist_ref: [CL-2.5, CL-3.x.17]` · Trang **7/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [luu_tru, may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> "Dung lượng lưu trữ" hay "Dung lượng lưu trữ cần thiết": Là dung lượng có thể sử
> dụng được của chương trình ứng dụng (sau khi RAID, chia partition và format,..).
> "Dung lượng lưu trữ thô": Là dung lượng thiết bị lưu trữ vật lý cần cấp phát
> (SSD, HDD, Tape) (trước khi RAID).

**Phạm vi áp dụng:** mọi bản sizing có phần định cỡ lưu trữ.

**KHÔNG áp dụng khi:** bản sizing không đề xuất tài nguyên lưu trữ nào.

**Tiêu chí ĐẠT** — với **mỗi** con số dung lượng trong tài liệu, phải xác định được
nó là loại nào:
1. Ghi rõ nhãn *"khả dụng"* / *"sau RAID"* hoặc *"thô"* / *"trước RAID"*; **hoặc**
2. Nêu đồng thời cả hai giá trị kèm tỷ lệ RAID dùng để quy đổi.

**Tiêu chí KHÔNG ĐẠT:**
- Bảng chỉ ghi *"Dung lượng: 6 TB"* không rõ loại — đây là ca phổ biến nhất.
- Trộn hai loại trong cùng một bảng mà không phân biệt.
- Lấy dung lượng thô đem so với ngưỡng 80% (R06) — ngưỡng đó áp cho dung lượng khả dụng.

> **Vì sao nghiêm trọng:** nhầm hai loại này làm sai toàn bộ chuỗi tính từ R56 (dung
> lượng thô) tới R64/R65 (số ổ cứng). Với RAID 6 8 ổ, chênh lệch là 33%.

**Vị trí cần soi:** bảng cấu hình hệ tham chiếu và bảng đề xuất lưu trữ.

**Ví dụ ĐẠT** `[minh họa]`
> Nhu cầu dữ liệu 6 TB khả dụng. Với RAID 6 (8 ổ, tỷ lệ 8/6), format 1.1, sai số 1.1,
> dự phòng 1.25 → dung lượng thô cần cấp: 6 × 1.333 × 1.1 × 1.1 × 1.25 = 12,1 TB.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Nhu cầu lưu trữ của hệ thống: 6 TB. Đề xuất cấp 6 TB trên thiết bị lưu trữ SAN.

`see_also: [R56, R57, R06]`

---

#### EVD-xx — Chỉ rõ yếu tố mở rộng dọc/ngang làm sở cứ mở rộng sau này

- `legacy_ref: [R25, R32]` — **hai quy tắc đã gộp** (xem mục 2)
- `checklist_ref: []` — **checklist không có mục tương ứng** (xem ghi chú cuối)
- Trang **10/44** và **14/44** · Nhóm kiểm: **A** · `severity: major`

**Trích dẫn nguyên văn** (R32, trang 14/44 — bản chi tiết hơn, dùng làm trích dẫn chính)

> Cần chỉ rõ các yếu tố ảnh hưởng mở rộng chiều dọc/ mở rộng chiều ngang (scale
> up/scale out), làm sở cứ phục vụ mở rộng sau này. Ví dụ: Cần chỉ rõ khi mở rộng
> hệ thống để đáp ứng từ 100TPS lên 200TPS thì phải mở rộng những loại module nào…

**Trích dẫn bổ sung** (R25, trang 10/44)

> …thêm node thành phần với Load Blancing hay không và suy giảm bao nhiêu % để xác
> định thành phần hệ thống phù hợp với mở rộng theo chiều dọc hay mở rộng theo chiều ngang.

**Phạm vi áp dụng:** mọi bản sizing.

**KHÔNG áp dụng khi:** không có — đây là yêu cầu chung.

**Tiêu chí ĐẠT** — phải trả lời được **cả ba**:
1. Khi tải tăng, **module nào** phải mở rộng?
2. Mỗi module mở rộng theo **chiều dọc hay chiều ngang**?
3. Với module scale out: thêm node có kèm Load Balancing không, và hiệu năng **suy
   giảm bao nhiêu %** khi thêm node (do overhead đồng bộ)?

Cách trình bày đạt yêu cầu là nêu một kịch bản cụ thể có số, như ví dụ 100 → 200 TPS
trong tài liệu.

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ nói chung *"hệ thống có khả năng mở rộng ngang"* mà không chỉ ra module nào.
- Nêu module nhưng không nói dọc hay ngang.
- Không đề cập mức suy giảm hiệu năng khi scale out.

**Vị trí cần soi:** mục tính toán tài nguyên từng thành phần, phần lập luận mở rộng.

**Ví dụ ĐẠT** `[minh họa]`
> Từ 100 TPS lên 200 TPS: module API Gateway và App Service mở rộng ngang (thêm node
> sau LB, hiệu năng suy giảm ~8%/node do đồng bộ session); module MariaDB mở rộng dọc
> (tăng RAM buffer pool) vì mô hình master-slave không chia tải ghi.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống thiết kế theo kiến trúc microservice nên có khả năng mở rộng linh hoạt khi
> nhu cầu tăng.

> **Ghi chú đáng lưu ý:** đây là **quy tắc Guideline không có mục checklist tương ứng**.
> Nghĩa là Vòng 1 sẽ không bắt được nếu tài liệu thiếu hẳn phần này — chỉ Vòng 2 bắt
> được. Cần nêu với đơn vị thẩm định xem có nên bổ sung một mục checklist không.

---

#### EVD-xx — Thông số chọn để định cỡ phải ảnh hưởng tới năng lực xử lý

- `legacy_ref: [R35]` · `checklist_ref: [CL-2.5]` · Trang **16/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: minor`

**Trích dẫn nguyên văn**

> Các thông số được chọn phục vụ đánh giá định cỡ các module phải là các thông số có
> ảnh hưởng đến năng lực xử lý, khả năng quản lý của tài nguyên phần cứng cũng như
> năng lực xử lý của phần mềm.

**Phạm vi áp dụng:** mọi bản sizing có nêu thông số đầu vào.

**KHÔNG áp dụng khi:** không có.

**Tiêu chí ĐẠT:**
1. Thông số dùng làm cơ sở tính toán là loại **có quan hệ nhân quả với tải tài
   nguyên** — CCU, TPS, RPS, QPS, số giao dịch, khối lượng dữ liệu, IOPS.
2. Nếu dùng thông số nghiệp vụ gián tiếp (số thuê bao, số chi nhánh, doanh thu…),
   phải nêu **cách quy đổi** sang thông số tải.

**Tiêu chí KHÔNG ĐẠT:**
- Định cỡ dựa thẳng vào con số nghiệp vụ mà không quy đổi — ví dụ *"hệ thống phục vụ
  5 triệu thuê bao nên cần 20 máy chủ"*.
- Thông số nêu ra không được dùng ở bất kỳ phép tính nào phía sau.

**Vị trí cần soi:** mục thông số đầu vào và phần lập luận chọn thông số.

**Ví dụ ĐẠT** `[minh họa]`
> Hệ thống phục vụ 5 triệu thuê bao. Theo số liệu giám sát hệ hiện tại, tỷ lệ hoạt
> động đồng thời giờ cao điểm là 1,2% → CCU = 60.000. Định cỡ dựa trên CCU 60.000
> và 3.500 TPS đo được.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống phục vụ 5 triệu thuê bao trên 63 tỉnh thành, do đó đề xuất cấu hình 20 máy
> chủ ứng dụng.

---

#### EVD-xx — Mô tả tài nguyên dành riêng và cơ chế swap / huge-page

- `legacy_ref: [R53]` · `checklist_ref: [CL-3.x.2]` · Trang **25/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Với các Ứng dụng đặc thù sử dụng tài nguyên dành riêng (ví dụ dedicate CPU core như
> DPDK, dedicate RAM như Storm) cần mô tả rõ để có thể định cỡ phù hợp.
> Với các Ứng dụng sử dụng RAM nhiều (như IMDB, Redis…) cần mô tả về cơ chế sử dụng
> swap và huge-page, có cấu hình và sử dụng swap không, cho phép sử dụng bao nhiêu %
> RAM thì mới sử dụng Swap để tránh ảnh hưởng hiệu năng sử dụng.

**Phạm vi áp dụng — hai nhánh, xét riêng:**
- **(a)** Phân hệ dùng tài nguyên dành riêng: DPDK, CPU pinning, dedicate RAM (Storm…).
- **(b)** Phân hệ dùng nhiều RAM: IMDB, Redis, Memcached, cache in-memory.

**KHÔNG áp dụng khi:** phân hệ không thuộc cả hai nhánh — ứng dụng web/API thông
thường, DB quan hệ tiêu chuẩn. Trả về `không áp dụng`.

**Tiêu chí ĐẠT:**
- Nhánh (a): nêu rõ **loại tài nguyên dành riêng** và **số lượng** (bao nhiêu core
  pinning, bao nhiêu GB RAM dành riêng), tách khỏi phần tài nguyên dùng chung.
- Nhánh (b): nêu rõ **có bật swap không**; nếu có thì **ngưỡng %RAM** bắt đầu dùng
  swap; có dùng **huge-page** không.

**Tiêu chí KHÔNG ĐẠT:**
- Phân hệ Redis/IMDB chỉ khai tổng RAM, không nói gì về swap và huge-page.
- Khai dùng DPDK nhưng không tách số core dành riêng khỏi tổng vCPU.

**Vị trí cần soi:** mục công nghệ sử dụng của phân hệ và bảng đề xuất cấu hình.

**Ví dụ ĐẠT** `[minh họa]`
> Phân hệ Redis: 64 GB RAM, không bật swap (`vm.swappiness=0`) để tránh suy giảm độ
> trễ; bật huge-page 2 MB cho vùng dữ liệu. Dung lượng dữ liệu tối đa giữ ở 80% RAM.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Phân hệ Redis: 03 node, mỗi node 16 vCPU / 64 GB RAM.

---

#### EVD-xx — Hệ hiệu năng cao phải tính hiệu năng cho từng phân vùng riêng

- `legacy_ref: [R59]` · `checklist_ref: [CL-3.x.15]` · Trang **26/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [luu_tru]` · `severity: major`

**Trích dẫn nguyên văn**

> Tính toán hiệu năng: với các hệ thống có yêu cầu cao về năng lực đọc ghi của thiết
> bị lưu trữ như hệ thống VDI, thiết bị lưu trữ dùng chung nhiều hệ thống hiệu năng
> cao như CSDL OLTP, ảo hóa số lượng máy chủ lớn, hệ thống đa phương tiện (media),
> dữ liệu lớn,... cần tính toán hiệu năng thiết bị lưu trữ cần đáp ứng. Cần thiết kế
> và tính toán hiệu năng cho mỗi phân vùng riêng biệt tương ứng với một loại dữ liệu
> cần lưu trữ, ví dụ phân vùng cho DB, phân vùng cho backup và archive.

**Phạm vi áp dụng:** hệ thuộc một trong các loại tài liệu liệt kê — VDI, lưu trữ dùng
chung cho nhiều hệ hiệu năng cao, CSDL OLTP, ảo hóa số lượng lớn, media, dữ liệu lớn.

**KHÔNG áp dụng khi:** hệ thống không thuộc nhóm trên và tài liệu không khai yêu cầu
hiệu năng lưu trữ đặc biệt. Trả về `không áp dụng`.

**Tiêu chí ĐẠT:**
1. Có phần tính hiệu năng (IOPS, latency) cho thiết bị lưu trữ, không chỉ dung lượng.
2. Tính **riêng cho từng phân vùng** theo loại dữ liệu — tối thiểu tách được phân
   vùng DB, phân vùng backup, phân vùng archive nếu hệ thống có.
3. Mỗi phân vùng có IOPS và latency riêng, không gộp một con số cho cả thiết bị.

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ tính dung lượng, bỏ hẳn phần hiệu năng.
- Có nhiều phân vùng nhưng chỉ một giá trị IOPS chung.
- Gộp phân vùng DB và backup làm một khi hai loại có đặc tính I/O khác hẳn nhau.

**Vị trí cần soi:** mục định cỡ thiết bị lưu trữ.

**Ví dụ ĐẠT** `[minh họa]`
> Phân vùng `/u01` (DB OLTP): 12.000 IOPS, latency ≤ 1 ms, RAID 10, ổ SSD.
> Phân vùng `/backup`: 900 IOPS, latency ≤ 10 ms, RAID 6, ổ NL-SAS 7.2k.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống cần thiết bị lưu trữ dung lượng 40 TB, hiệu năng khoảng 15.000 IOPS.

`see_also: [R60, R61, R65]`

---

### 5.3. Nhóm `MTH` — phương pháp định cỡ (Dạng I / II / III)

> Bốn quy tắc `MTH` **loại trừ lẫn nhau**: đúng một dạng áp dụng cho mỗi bản sizing,
> ba dạng còn lại trả về `không áp dụng`. C5 phải xác định dạng trước, rồi mới xét
> quy tắc tương ứng. `MTH-xx (R26)` đã viết ở mục 4.

---

#### MTH-xx — Dạng I không có hệ tham chiếu tương đồng → phải hoàn thiện sản phẩm và kiểm thử

- `legacy_ref: [R27]` · `checklist_ref: [CL-2.1, CL-2.4]` · Trang **11/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: critical`

**Trích dẫn nguyên văn**

> Nếu sản phẩm phần mềm chưa có và không có hệ thống tham chiếu tương đồng thì đơn vị
> phát triển phải hoàn thiện sản phẩm và thực hiện kiểm thử hiệu năng để định cỡ.

**Phạm vi áp dụng:** bản sizing **Dạng I** (chưa có sản phẩm phần mềm) **và** không
nêu được hệ tham chiếu tương đồng nào.

**KHÔNG áp dụng khi:** Dạng II, Dạng III, hoặc Dạng I **có** hệ tham chiếu tương đồng
— khi đó R26 áp dụng thay.

**Tiêu chí ĐẠT:** tài liệu thừa nhận không có hệ tham chiếu tương đồng, và nêu rõ
**kế hoạch hoàn thiện sản phẩm + kiểm thử hiệu năng** trước khi xin cấp phát chính thức.

**Tiêu chí KHÔNG ĐẠT:**
- Không có hệ tham chiếu nhưng vẫn đưa ra con số tài nguyên cụ thể như thể đã đo được.
- Lấy một hệ **không tương đồng** làm tham chiếu để né yêu cầu kiểm thử — trường hợp
  này R26 bắt phần "không tương đồng", quy tắc này bắt phần "chưa kiểm thử".

> `severity: critical` vì theo trích dẫn ở R26, hệ CNTT nội bộ Tập đoàn định cỡ theo
> Dạng I **không được cấp phát** cho tới khi có kiểm thử hiệu năng.

**Vị trí cần soi:** mục cơ sở định cỡ.

**Ví dụ ĐẠT** `[minh họa]`
> Sản phẩm chưa hoàn thiện và không có hệ thống tương đồng trong Tập đoàn. Bản định
> cỡ này phục vụ đầu tư môi trường kiểm thử. Sau khi hoàn thiện sản phẩm, đơn vị sẽ
> kiểm thử hiệu năng và định cỡ lại trước khi xin cấp phát production.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Đây là sản phẩm mới, chưa có hệ thống tương tự. Ước tính nhu cầu: 12 máy chủ ứng
> dụng 16 vCPU/32 GB và cụm DB 03 node.

`see_also: [R26, R28, R29]`

---

#### MTH-xx — Dạng II: định cỡ bằng môi trường kiểm thử, không dùng phương pháp Dạng I

- `legacy_ref: [R28]` · `checklist_ref: [CL-2.1, CL-2.4]` · Trang **11/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: critical`

**Trích dẫn nguyên văn**

> Không áp dụng phương pháp I - Định cỡ khi chưa có sản phẩm phần mềm đối với các sản
> phẩm đã có phần mềm.
> Cơ sở định cỡ: sử dụng môi trường kiểm thử, đo nhu cầu tài nguyên sử dụng của hệ
> thống theo các mẫu đầu vào khác nhau. Từ đó tính ra bình quân nhu cầu tài nguyên sử
> dụng của mỗi người dùng (hoặc giao dịch) để làm cơ sở tính toán nhu cầu tài nguyên
> của hệ thống cần đáp ứng.

**Phạm vi áp dụng:** bản sizing **Dạng II** — đã có sản phẩm phần mềm, định cỡ để
triển khai thực tế lần đầu.

**KHÔNG áp dụng khi:** Dạng I hoặc Dạng III.

**Tiêu chí ĐẠT** — phải có đủ **ba**:
1. Nêu rõ đã đo trên **môi trường kiểm thử**, không phải ước lượng.
2. Đo theo **nhiều mẫu đầu vào khác nhau** (liên hệ R41: ≥ 5 mẫu, mỗi mẫu ≥ 5 lần).
3. Tính ra **bình quân tài nguyên trên mỗi người dùng hoặc mỗi giao dịch**, rồi nhân
   lên theo quy mô mục tiêu.

**Tiêu chí KHÔNG ĐẠT — quan trọng nhất:**
- **Đã có phần mềm nhưng vẫn định cỡ theo hệ tham chiếu tương đồng** (cách của Dạng I).
  Tài liệu cấm rõ điều này.
- Có đo nhưng chỉ một mẫu đầu vào duy nhất.
- Nhảy thẳng từ số liệu đo sang tổng tài nguyên mà không qua bước bình quân/giao dịch.

**Vị trí cần soi:** mục cơ sở định cỡ và phần số liệu kiểm thử.

**Ví dụ ĐẠT** `[minh họa]`
> Đo trên môi trường kiểm thử với 05 mức tải (500/1.000/2.000/3.000/5.000 CCU), mỗi
> mức lặp 05 lần. Bình quân 1 CCU tiêu thụ 0,018 vCPU và 12 MB RAM. Với mục tiêu
> 60.000 CCU → 1.080 vCPU, 720 GB RAM trước khi áp hệ số KPI và sai số.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Sản phẩm đã triển khai tại đơn vị A. Định cỡ cho đơn vị B tham chiếu theo cấu hình
> đang chạy tại A, nhân hệ số 1,5 theo tỷ lệ người dùng.

*(Đã có phần mềm mà dùng cách của Dạng I. Đúng ra phải đo trên môi trường kiểm thử,
hoặc coi như nâng cấp hệ thống theo Dạng III.)*

`see_also: [R26, R27, R29, R41]`

---

#### MTH-xx — Dạng III: định cỡ theo hiện trạng và yêu cầu mở rộng

- `legacy_ref: [R29]` · `checklist_ref: [CL-2.1, CL-2.4]` · Trang **12/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: major`

**Trích dẫn nguyên văn**

> Thực hiện khi sản phẩm phần mềm đã đi vào hoạt động, cần tăng số lượng người dùng,
> tăng quy mô phần mềm... cần nâng cấp hạ tầng để đảm bảo. Sau khi hệ thống hoạt động
> có tải, cần thực hiện đánh giá và điều chỉnh sizing để đảm bảo hoạt động của hệ
> thống và tối ưu hiệu suất sử dụng.
> Cơ sở định cỡ: Căn cứ vào hiện trạng hoạt động của hệ thống hiện tại (tải, số người
> dùng, chất lượng dịch vụ...) và yêu cầu mở rộng (số người dùng, CCU/TPS/RPS,
> Latency...) để tính toán và xác định được cấu hình tài nguyên cần nâng cấp.

**Phạm vi áp dụng:** bản sizing **Dạng III** — nâng cấp hệ thống đang chạy.

**KHÔNG áp dụng khi:** Dạng I hoặc Dạng II.

**Tiêu chí ĐẠT** — phải có **cả hai vế**:
1. **Hiện trạng:** tải thực tế đang chạy (giá trị 95th, tối thiểu 01 tháng — theo
   R36), số người dùng hiện tại, chất lượng dịch vụ hiện tại.
2. **Yêu cầu mở rộng:** con số mục tiêu cụ thể — số người dùng, CCU/TPS/RPS, latency
   yêu cầu.

Thiếu một trong hai vế thì không tính được hệ số so sánh `Ksosánh` (R40), tức không
có cơ sở tính toán.

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ nêu cấu hình đang chạy, không nêu tải thực tế đo được.
- Chỉ nêu mục tiêu mở rộng, không nêu hiện trạng.
- Nêu cả hai nhưng lấy tải **đỉnh tuyệt đối** hoặc **trung bình** thay vì 95th.

**Vị trí cần soi:** mục thông tin đầu vào (hiện trạng) và yêu cầu bài toán (mục tiêu).

**Ví dụ ĐẠT** `[minh họa]`
> Hiện trạng: 03 máy chủ ứng dụng, tải CPU 95th = 62% (đo tháng 5–6/2026 qua Zabbix),
> phục vụ 18.000 CCU giờ cao điểm, latency P95 = 240 ms.
> Yêu cầu mở rộng: 45.000 CCU, giữ latency P95 ≤ 300 ms → Ksosánh = 45.000/18.000 = 2,5.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống hiện có 03 máy chủ 16 vCPU/32 GB. Do nhu cầu tăng, đề nghị bổ sung thêm
> 04 máy chủ cùng cấu hình.

`see_also: [R26, R27, R28, R36, R40]`

---

### 5.4. Nhóm `PRC` — thủ tục và quy trình

> Bốn quy tắc đầu thuộc **nhóm kiểm B** — Copilot chỉ xác nhận tài liệu *có nêu / có
> dẫn chiếu*, **không** xác minh được văn bản có thật hay chữ ký hợp lệ. Câu finding
> bắt buộc nói rõ giới hạn này. `PRC-xx (R30)` đã viết ở mục 4.

---

#### PRC-xx — Biên bản kiểm thử hiệu năng phải được xác nhận bằng văn bản

- `legacy_ref: [R31]` · `checklist_ref: [CL-2.5]` · Trang **14/44** · Nhóm kiểm: **B**
- `applies_to_equipment:` (mọi) · `severity: major`

**Trích dẫn nguyên văn**

> Biên bản kiểm thử hiệu năng phải được lãnh đạo đơn vị thực hiện kiểm thử xác nhận
> bằng văn bản.

**⚠️ Giới hạn kiểm:** chỉ kiểm được tài liệu **có dẫn chiếu biên bản** hay không.
Không xác minh được biên bản có thật, ai ký, ký có đúng thẩm quyền.

**Phạm vi áp dụng:** bản sizing có dùng **số liệu kiểm thử hiệu năng** làm cơ sở —
tức Dạng II, và Dạng I khi đã kiểm thử.

**KHÔNG áp dụng khi:** bản sizing hoàn toàn dựa trên hệ tham chiếu đang vận hành
(Dạng III thuần), không dùng số liệu kiểm thử nào.

**Tiêu chí ĐẠT:** dẫn chiếu được biên bản kiểm thử với **số hiệu / ngày / người ký
hoặc chức danh**, hoặc đính kèm biên bản và nhắc tới trong phần sở cứ.

**Tiêu chí KHÔNG ĐẠT:**
- Trình bày kết quả kiểm thử nhưng không nhắc tới biên bản nào.
- Chỉ nói *"đã kiểm thử và được lãnh đạo thông qua"* mà không có số hiệu, ngày, người ký.

**Vị trí cần soi:** mục số liệu kiểm thử và danh mục tài liệu đính kèm.

**Ví dụ ĐẠT** `[minh họa]`
> Kết quả kiểm thử theo Biên bản số 88/BB-KTHN ngày 20/5/2026, do Giám đốc Trung tâm
> Kiểm thử ký xác nhận (đính kèm Phụ lục 2).

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Nhóm dự án đã kiểm thử hiệu năng trên môi trường staging, kết quả đạt 3.500 TPS.

`see_also: [R30, R41, R99]`

---

#### PRC-xx — Hệ triển khai trên hạ tầng Tập đoàn phải xin ý kiến thẩm định TCT VTNet

- `legacy_ref: [R33]` · `checklist_ref: [CL-1.1]` · Trang **15/44** · Nhóm kiểm: **B**
- `applies_to_equipment: [cap_phat]` · `severity: major`

**Trích dẫn nguyên văn**

> …hệ thống CNTT triển khai tại hạ tầng CNTT của Tập đoàn, đơn vị xây dựng tài liệu
> định cỡ cần xin ý kiến thẩm định của TCT VTNet.

**⚠️ Giới hạn kiểm:** chỉ kiểm được tài liệu **có nêu đã/đang xin ý kiến** hay không.

**Phạm vi áp dụng:** hệ thống triển khai trên hạ tầng CNTT của Tập đoàn.

**KHÔNG áp dụng khi:** hệ thống triển khai trên hạ tầng riêng của đơn vị, hoặc phục
vụ khách hàng ngoài. Trả về `không áp dụng`.

**Tiêu chí ĐẠT:** tài liệu nêu rõ đã gửi / đang chờ ý kiến thẩm định của TCT VTNet,
kèm mốc thời gian hoặc số công văn nếu có.

**Tiêu chí KHÔNG ĐẠT:** không đề cập gì tới bước thẩm định VTNet trong khi hệ thống
rõ ràng dùng hạ tầng Tập đoàn.

**Vị trí cần soi:** mục quy trình / phê duyệt, phần đầu tài liệu.

**Ví dụ ĐẠT** `[minh họa]`
> Tài liệu định cỡ đã gửi TCT VTNet xin ý kiến thẩm định tại Công văn số 145/CV-TTSP
> ngày 10/6/2026.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Tài liệu định cỡ do nhóm dự án lập, đã được lãnh đạo đơn vị phê duyệt.

---

#### PRC-xx — Cấp phát chỉ với hệ thống có đủ bốn loại hồ sơ

- `legacy_ref: [R92]` · `checklist_ref: [CL-1.1]` · Trang **40/44** · Nhóm kiểm: **B**
- `applies_to_equipment: [cap_phat]` · `severity: critical`

**Trích dẫn nguyên văn**

> Chỉ thực hiện cấp phát hạ tầng CNTT với các hệ thống CNTT có tờ trình đầu tư tài
> nguyên, có quy hoạch định cỡ. Được kiểm thử hiệu năng và có tài liệu định cỡ đáp
> ứng quy định.

**Trích dẫn bổ sung** (cùng trang, ràng buộc kèm theo)

> Khi thực hiện cấp phát yêu cầu hệ thống CNTT phải được kiểm thử hiệu năng và định
> cỡ chính xác trước khi cấp phát. Các hệ thống được định cỡ khi chưa có sản phẩm,
> khi yêu cầu cấp phát cần định cỡ lại theo phương pháp có sản phẩm phần mềm.

**⚠️ Giới hạn kiểm:** chỉ kiểm được tài liệu **có liệt kê / dẫn chiếu** bốn loại hồ sơ.

**Phạm vi áp dụng:** hồ sơ **xin cấp phát** tài nguyên.

**KHÔNG áp dụng khi:** hồ sơ chỉ xin **thẩm định bản định cỡ**, chưa xin cấp phát.
Trả về `không áp dụng` — trùng điều kiện của `CL-1.1`.

**Tiêu chí ĐẠT** — dẫn chiếu được đủ **bốn**:
1. Tờ trình đầu tư tài nguyên
2. Quy hoạch định cỡ
3. Kết quả kiểm thử hiệu năng
4. Tài liệu định cỡ

**Tiêu chí KHÔNG ĐẠT:**
- Thiếu bất kỳ loại nào trong bốn.
- Hệ thống **định cỡ theo Dạng I** (chưa có sản phẩm) mà xin cấp phát luôn, không
  định cỡ lại theo phương pháp đã có sản phẩm → vi phạm trích dẫn bổ sung, `critical`.

**Vị trí cần soi:** phần mở đầu hồ sơ, danh mục tài liệu kèm theo.

**Ví dụ ĐẠT** `[minh họa]`
> Hồ sơ gồm: Tờ trình số 210/TTr-TTSP ngày 1/6/2026; Quy hoạch định cỡ v2.1; Biên bản
> kiểm thử hiệu năng số 88/BB-KTHN ngày 20/5/2026; Tài liệu định cỡ này.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Kính đề nghị cấp phát tài nguyên theo bảng cấu hình đính kèm.

`see_also: [R26, R27, R31]`

---

#### PRC-xx — Thu hồi: ưu tiên giảm số máy chủ trước khi giảm cấu hình

- `legacy_ref: [R97]` · `checklist_ref: []` — **checklist không có mục tương ứng**
- Trang **42/44** · Nhóm kiểm: **A** · `severity: minor`

**Trích dẫn nguyên văn**

> Với từng hệ thống, cần thực hiện đánh giá giữa phương án thực hiện giảm số máy chủ
> trong hệ thống và phương án so với giảm cấu hình từng máy chủ của hệ thống.
> Với máy chủ ứng dụng chạy hạ tầng ảo hóa, ưu tiên thực hiện giảm số máy chủ trong
> hệ thống trước khi giảm cấu hình từng máy chủ trong hệ thống.
> Với các hệ thống chạy cluster như cơ sở dữ liệu, khi thu hồi cần đảm bảo số lượng
> máy chủ tối thiểu theo mô hình cụm cluster.

**Phạm vi áp dụng:** hồ sơ **thu hồi / cắt giảm** tài nguyên.

**KHÔNG áp dụng khi:** hồ sơ xin cấp phát mới hoặc mở rộng — tức **phần lớn** bản
sizing. Trả về `không áp dụng`.

**Tiêu chí ĐẠT:**
1. Có so sánh **hai phương án**: giảm số máy chủ vs giảm cấu hình từng máy.
2. Với máy chủ ứng dụng ảo hóa: chọn giảm số máy chủ, hoặc giải trình vì sao không.
3. Với cụm cluster (DB): nêu rõ số máy tối thiểu theo mô hình cụm và không cắt xuống
   dưới mức đó.

**Tiêu chí KHÔNG ĐẠT:**
- Cắt cấu hình từng máy mà không xét phương án giảm số máy.
- Cắt số node cụm DB xuống dưới mức tối thiểu của mô hình (ví dụ cụm 3 node quorum
  cắt còn 2).

**Vị trí cần soi:** mục phương án thu hồi / tối ưu tài nguyên.

**Ví dụ ĐẠT** `[minh họa]`
> Hiện 08 máy chủ ứng dụng, hiệu suất CPU 95th chỉ 18%. So sánh: (a) giảm còn 04 máy
> giữ nguyên 16 vCPU — tải lên 36%; (b) giữ 08 máy giảm còn 8 vCPU — cùng mức tải
> nhưng tốn thêm 4 license OS. Chọn (a). Cụm MariaDB giữ nguyên 03 node theo yêu cầu
> quorum.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Đề xuất giảm cấu hình toàn bộ 08 máy chủ ứng dụng từ 16 vCPU xuống 8 vCPU.

> **Ghi chú:** giống `R25+R32`, đây là quy tắc **không có mục checklist tương ứng** —
> vì checklist chỉ phủ luồng cấp phát, không phủ luồng thu hồi.

---

#### PRC-xx — Thống nhất công cụ đo và lưu vết, ký xác nhận

- `legacy_ref: [R99]` · `checklist_ref: [CL-2.5]` · Trang **44/44** · Nhóm kiểm: **B**
- `applies_to_equipment: [kiem_thu]` · `severity: major`

**Trích dẫn nguyên văn**

> Việc tính toán và định cỡ ứng dụng, nền tảng không phụ thuộc và bó buộc vào một
> công cụ duy nhất, do đó, đơn vị PTPM cần phối hợp và thống nhất với đơn vị quy
> hoạch định cỡ, triển khai để thống nhất cùng một công cụ, cùng một cách thức đo
> kiểm để có thể phục vụ việc nâng cấp, mở rộng sau này. Khi tiến hành đầu tư, triển
> khai, tất cả các công thức, công cụ, bài kiểm thử định cỡ cần phải được lưu vết,
> ký xác nhận để làm sở cứ phục vụ các công tác sau này.

**⚠️ Giới hạn kiểm:** chỉ kiểm được tài liệu **có nêu** công cụ đã thống nhất và nơi
lưu vết; không xác minh được việc thống nhất có thật hay chữ ký hợp lệ.

**Phạm vi áp dụng:** bản sizing có dùng số liệu đo/kiểm thử.

**KHÔNG áp dụng khi:** không dùng số liệu đo nào (hiếm — thường là Dạng I chưa kiểm thử).

**Tiêu chí ĐẠT** — cả hai:
1. Nêu **tên công cụ** dùng để đo và nói rõ đã **thống nhất với đơn vị quy hoạch định
   cỡ / triển khai**.
2. Nêu **nơi lưu vết** công thức, kịch bản kiểm thử, kết quả — để lần nâng cấp sau đo
   lại theo đúng cách.

**Tiêu chí KHÔNG ĐẠT:**
- Nêu kết quả đo nhưng không nói dùng công cụ gì.
- Nêu công cụ nhưng không nói đã thống nhất với ai — lần mở rộng sau đo bằng công cụ
  khác sẽ không so sánh được.
- Không nói gì về việc lưu vết.

**Vị trí cần soi:** mục phương pháp đo và phần kết luận/kiến nghị.

**Ví dụ ĐẠT** `[minh họa]`
> Công cụ đo: JMeter 5.6, kịch bản và ngưỡng đã thống nhất với TTKTTC VTNet tại cuộc
> họp ngày 12/5/2026. Kịch bản, công thức tính và kết quả lưu tại kho tài liệu dự án
> (mã DA-2026-114), có ký xác nhận của hai bên.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Kết quả đo cho thấy hệ thống đáp ứng 3.500 TPS với latency trung bình 137 ms.

`see_also: [R31, R98]`

---

### 5.5. Nhóm `STO` — lưu trữ

---

#### STO-xx — Hệ đọc/ghi ngẫu nhiên cao nên dùng ổ tốc độ cao, dung lượng nhỏ

- `legacy_ref: [R67]` · `checklist_ref: [CL-3.x.18]` · Trang **30/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [luu_tru]` · `severity: minor`

**Trích dẫn nguyên văn**

> Với các hệ thống có yêu cầu cao về năng lực đọc ghi ngẫu nhiên (như ứng dụng VAS,
> CSDL OLTP, File server với nhiều file dung lượng nhỏ, số lượng file lớn,...) nên sử
> dụng các ổ cứng có tốc độ cao (10krpm, 15krpm, SSD) và dung lượng nhỏ hơn 1TB để
> đảm bảo hiệu năng và thời gian khôi phục dữ liệu nhanh.

**Phạm vi áp dụng:** phân hệ thuộc nhóm đọc/ghi ngẫu nhiên cao — VAS, CSDL OLTP,
File server nhiều file nhỏ.

**KHÔNG áp dụng khi:** phân hệ lưu trữ tuần tự, dữ liệu lớn ít truy cập, archive,
media, backup. Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — cả hai:
1. Loại ổ chọn là **10krpm, 15krpm hoặc SSD**.
2. Dung lượng mỗi ổ **< 1 TB**.

Nếu lệch một trong hai thì cần giải trình (ví dụ đã dùng SSD dung lượng lớn nhưng
có lý do về mật độ rack).

**Tiêu chí KHÔNG ĐẠT:**
- Hệ OLTP nhưng chọn ổ NL-SAS/SATA 7.2k.
- Chọn ổ tốc độ cao nhưng dung lượng 4–8 TB → thời gian rebuild rất lâu, đúng điều
  tài liệu muốn tránh.
- Không nêu loại ổ nào cả.

> `severity: minor` vì tài liệu dùng chữ **"nên"** — khuyến nghị, không phải ngưỡng
> cứng. Câu thông báo phải là đề nghị xác nhận, không phải khẳng định sai.

**Vị trí cần soi:** mục loại lưu trữ sử dụng và bảng đề xuất thiết bị lưu trữ.

**Ví dụ ĐẠT** `[minh họa]`
> Phân vùng CSDL OLTP dùng 12 ổ SSD 960 GB, RAID 10 — ưu tiên IOPS và thời gian
> rebuild ngắn.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Phân vùng CSDL dùng 06 ổ NL-SAS 4 TB, RAID 6.

`see_also: [R54, R55, R66, R68]`

---

### 5.6. Nhóm `TST` — kiểm thử hiệu năng

---

#### TST-xx — Nêu công cụ kiểm thử chuẩn theo loại đối tượng

- `legacy_ref: [R98]` · `checklist_ref: [CL-2.5]` · Trang **43–44/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [kiem_thu]` · `severity: minor`

**Trích dẫn nguyên văn**

> Đối với các CSDL nguồn mở, có thể sử dụng công cụ sysbench hoặc công cụ…
> Đối với ứng dụng, có thể sử dụng các công cụ benchmark end-2-end để tính toán ra
> các con số CCU, RPS như jmeter, ab.

**Phạm vi áp dụng:** bản sizing có phần kiểm thử hiệu năng.

**KHÔNG áp dụng khi:** không có kiểm thử (Dạng I chưa hoàn thiện sản phẩm).

**Tiêu chí ĐẠT:**
1. Nêu **tên công cụ** đã dùng.
2. Công cụ **phù hợp với đối tượng đo**: CSDL nguồn mở → sysbench hoặc tương đương;
   ứng dụng → công cụ benchmark end-to-end như JMeter, ab.
3. Nêu **chỉ số đo được** đúng loại — CCU, RPS, TPS, latency.

**Tiêu chí KHÔNG ĐẠT:**
- Không nêu công cụ.
- Dùng công cụ đo tầng ứng dụng để kết luận năng lực CSDL, hoặc ngược lại.
- Nêu công cụ nhưng không có chỉ số đo nào kèm theo.

> Tài liệu dùng chữ **"có thể sử dụng"** → công cụ khác vẫn chấp nhận được, miễn phù
> hợp đối tượng và có nêu rõ. Vì vậy `severity: minor` và tiêu chí không ép đúng tên
> công cụ trong danh sách.

**Vị trí cần soi:** mục kiểm thử hiệu năng.

**Ví dụ ĐẠT** `[minh họa]`
> CSDL MariaDB đo bằng sysbench (OLTP read-write, 5 triệu bản ghi): 12.400 TPS.
> Ứng dụng đo end-to-end bằng JMeter: 3.500 RPS, latency P95 = 240 ms.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Đã thực hiện kiểm thử hiệu năng, hệ thống đáp ứng yêu cầu đề ra.

`see_also: [R41, R99]`

---

### 5.7. BỔ SUNG — 8 quy tắc định tính từ rà độ phủ (R102–R110)

> **Thêm 2026-08-26.** Mục 0.2 rà lại độ phủ bằng `scripts/audit_rule_coverage.py` và
> tìm ra 10 quy tắc bị sót khỏi danh sách R01–R100 — 2 định lượng (R101, R105, nay đã có
> công thức ở `rules-formulas.md`) và **8 định tính viết ở đây**.
>
> **Số trang là số trang IN** (bản lần 07, trang vật lý = trang in) — nay đã thống nhất
> trên cả bộ tài liệu. Trích dẫn lấy từ `docs/rules/.tmp-lan7/clean.txt`, **đã kiểm khớp
> nguyên văn** (dòng 356–357 cho R102; 813–825 và 854–867 cho R103/R104; 944–949 cho
> R106/R107; 1931–1934 và 1946–1950 cho R108/R109; 774–781 cho R110).
>
> **Tất cả 8 quy tắc này thuộc VÒNG 2** — xem mục 4b.

---

#### ARC-xx — Mức độ dự phòng phải căn cứ phân loại hệ thống, không tự đặt

- `legacy_ref: [R102]` · `checklist_ref: [CL-2.10, CL-2.11, CL-3.x.6]` · Trang **9/44** · Nhóm kiểm: **B**
- `applies_to_equipment:` (mọi) · `severity: major`

**Trích dẫn nguyên văn**

> Mức độ dự phòng của từng hệ thống, thiết bị căn cứ vào phân loại hệ thống trong các
> quy định về dự phòng của Tập đoàn hiện hành.

**⚠️ Giới hạn kiểm — bắt buộc nêu trong finding:** *"các quy định về dự phòng của Tập
đoàn hiện hành"* trỏ tới **849/QĐ-CNVTQĐ**, mà ta **chưa có văn bản** (mục 0.12b).
Copilot chỉ kiểm được **tài liệu có nêu phân loại hệ thống và có suy ra mức dự phòng từ
phân loại đó hay không**; Copilot **không** đối chiếu được với nội dung 849/QĐ. Câu
finding phải nói rõ điều này.

**Phạm vi áp dụng:** mọi bản sizing.

**KHÔNG áp dụng khi:** không có trường hợp nào — đây là yêu cầu bắt buộc chung.

**Tiêu chí ĐẠT** — phải có đủ **cả ba**:
1. Nêu **mức độ quan trọng** của hệ thống, đúng một trong bốn giá trị
   `đặc biệt quan trọng` / `rất quan trọng` / `quan trọng` / `bình thường` (theo `CL-2.10`).
2. Nêu **mức độ dự phòng** tương ứng cho từng hệ thống/thiết bị (`CL-2.11`, `CL-3.x.6`).
3. **Nối được hai thứ đó với nhau**: tài liệu chỉ ra mức dự phòng được chọn *vì* hệ
   thuộc phân loại nào, hoặc dẫn chiếu quy định dự phòng của Tập đoàn.

**Tiêu chí KHÔNG ĐẠT:**
- Có mức độ quan trọng nhưng không nói gì về mức dự phòng, hoặc ngược lại.
- Có cả hai nhưng **không có liên hệ nào** — mức dự phòng khai như một lựa chọn kỹ thuật
  độc lập, không dẫn chiếu phân loại hệ thống hay quy định của Tập đoàn.
- Mức độ quan trọng ghi bằng chữ tự đặt (*"khá quan trọng"*, *"mức trung bình"*) không
  thuộc bốn giá trị chuẩn.

> **Phân vai với R101:** R101 là **định lượng** — ánh xạ cứng mức độ → cơ chế
> (`active-active` / `active-standby`), C4 so bằng code. R102 chỉ kiểm phần **trình bày
> căn cứ**, C5 làm. Một bản sizing khai đúng cơ chế nhưng không nói vì sao thì **qua
> R101, trượt R102** — đúng như thiết kế, không phải trùng lặp.

**Vị trí cần soi:** mục mức độ quan trọng của hệ thống và mục mức độ/mô hình dự phòng
(tổng quan lẫn từng phân hệ).

**Ví dụ ĐẠT** `[minh họa]`
> Hệ thống được phân loại **Rất quan trọng** theo 849/QĐ-CNVTQĐ. Căn cứ phân loại này,
> mức dự phòng áp dụng: nội site active-active cho phân hệ Application và Database;
> chưa yêu cầu DC-DR (chỉ bắt buộc với mức Đặc biệt quan trọng).

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống là hệ thống quan trọng của đơn vị. Các phân hệ đều triển khai dự phòng
> active-active để đảm bảo tính sẵn sàng.

*(Không dẫn chiếu quy định phân loại nào; mức dự phòng khai như lựa chọn kỹ thuật rời,
không nối với phân loại. Ngoài ra "hệ thống quan trọng của đơn vị" không rõ có phải mức
`Quan trọng` chuẩn hay chỉ là cách nói.)*

`see_also: [R101, QD849-01, QD849-02]`

---

#### EVD-xx — Phải nêu tính sẵn sàng và thời gian downtime cho phép

- `legacy_ref: [R103]` · `checklist_ref: [CL-2.5]` · Trang **18/44** · Nhóm kiểm: **A**
- `applies_to_equipment:` (mọi) · `severity: major`

**Trích dẫn nguyên văn** *(hai dòng của bảng "Thông số đầu vào", đã ghép lại từ các ô)*

> Tính sẵn sàng của hệ thống — Phút/tháng — Là thời gian cho phép downtime/tháng.
> Thời gian downtime cho phép đối với mỗi sự cố — Phút — Là thời gian cho phép downtime
> đối với mỗi một lỗi xảy ra trên hệ thống.

**Phạm vi áp dụng:** mọi bản sizing.

**KHÔNG áp dụng khi:** không có trường hợp nào.

**Tiêu chí ĐẠT** — phải có **cả hai** con số, kèm đơn vị:
1. **Tính sẵn sàng**: thời gian cho phép downtime **mỗi tháng**, tính bằng **phút/tháng**.
2. **Thời gian downtime cho phép cho mỗi sự cố**, tính bằng **phút**.

Khai theo tỷ lệ phần trăm (`99,9%`) được chấp nhận **nếu** quy đổi ra phút/tháng ngay
tại chỗ hoặc con số phút/tháng xuất hiện ở nơi khác trong tài liệu; nếu chỉ có `99,9%`
đơn độc thì hạ xuống `minor` và đề nghị bổ sung, không tính là không đạt.

**Tiêu chí KHÔNG ĐẠT:**
- Bảng thông số đầu vào không có dòng nào về tính sẵn sàng / downtime.
- Chỉ có một trong hai con số (thường chỉ có tính sẵn sàng tháng, thiếu downtime mỗi sự cố).
- Nêu bằng lời không có số: *"đảm bảo hoạt động liên tục 24/7"*, *"hạn chế tối đa gián đoạn"*.
- Có số nhưng sai đơn vị so với tài liệu (ví dụ downtime mỗi sự cố ghi theo giờ/năm).

> Đây là **thông số đầu vào**, không phải kết quả định cỡ. Nó là căn cứ để đánh giá mức
> dự phòng có tương xứng không — vì vậy thiếu nó thì R101/R102 mất một phần sở cứ.

**Vị trí cần soi:** mục "Thông tin đầu vào" — bảng thông số đầu vào về khả năng đáp ứng
của phần mềm.

**Ví dụ ĐẠT** `[minh họa]`
> Tính sẵn sàng: cho phép downtime tối đa **43 phút/tháng** (tương đương 99,9%).
> Thời gian downtime cho phép với mỗi sự cố: **15 phút**.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống yêu cầu tính sẵn sàng cao, hoạt động 24/7, đảm bảo phục hồi nhanh khi có sự cố.

`see_also: [R102, R39]`

---

#### EVD-xx — Phải nêu các yếu tố ảnh hưởng thông số tài nguyên máy chủ

- `legacy_ref: [R104]` · `checklist_ref: [CL-2.5, CL-3.x.7]` · Trang **18/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Các yếu tố ảnh hưởng thông số tài nguyên máy chủ
> - Số lượng người/thuê bao đăng ký (registered account/sub)
> - Số lượng thuê bao đăng ký (active account/sub)
> - Số lượng người dùng đồng thời (conccurent account/sub)
> - Số lượng thiết bị kết nối/phục vụ đồng thời
> - Số lượng tiến trình (process) đồng thời
> - Số lượng yêu cầu (request) đồng thời
> - Số lượng giao dịch một người dùng
> - Độ phức tạp của giao dịch
> - Yêu cầu về kích thước, dung lượng bản tin trao đổi và lưu trữ
> - Yêu cầu cụ thể về lưu trữ của ứng dụng (lưu log, dữ liệu văn bản, media, cơ sở dữ
>   liệu, kết nối SAN...)
> - Mục đích sử dụng máy chủ: cơ sở dữ liệu, ứng dụng, lưu media, kết nối SAN...

*(Lỗi chính tả `conccurent` là của tài liệu gốc, giữ nguyên khi trích.)*

**Phạm vi áp dụng:** mọi bản sizing có định cỡ máy chủ.

**KHÔNG áp dụng khi:** không có trường hợp nào.

**Tiêu chí ĐẠT** — cả hai:
1. **Mọi yếu tố mà chính bản sizing dùng làm đầu vào cho một phép tính đều được khai
   trong bảng thông số đầu vào**, có giá trị và đơn vị. Nói cách khác: không có con số
   nào xuất hiện lần đầu ngay trong công thức mà không có nguồn ở phần đầu vào.
2. Bảng thông số đầu vào nêu được ít nhất các yếu tố ứng với **mục đích sử dụng máy chủ**
   đã khai (CSDL / ứng dụng / media / SAN) — vì tài liệu liệt kê mục đích sử dụng là một
   yếu tố ảnh hưởng.

**Tiêu chí KHÔNG ĐẠT:**
- Bảng thông số đầu vào **không có yếu tố nào** trong danh sách trên.
- Công thức định cỡ dùng một con số (ví dụ *"số request đồng thời = 1.200"*) mà con số
  đó không có ở phần thông số đầu vào — không truy được nguồn.
- Chỉ khai một yếu tố tổng (*"5 triệu thuê bao"*) rồi tính thẳng, không phân biệt
  đăng ký / active / đồng thời — ba con số khác nhau nhiều bậc, gộp lại là mất căn cứ.

> ⚠️ **`[CẦN XÁC NHẬN]` — không ép đủ cả 11 yếu tố.** Tài liệu liệt kê 11 yếu tố nhưng
> không nói yếu tố nào **bắt buộc**; nhiều yếu tố không áp dụng cho mọi hệ (ví dụ "số
> thiết bị kết nối đồng thời" với hệ thuần web nội bộ). Ép đủ 11 sẽ sinh cảnh báo sai
> hàng loạt — trái với ưu tiên "độ chính xác hơn độ phủ". Vì vậy tiêu chí trên neo vào
> **những yếu tố bản sizing thực sự dùng**, chứ không đếm đủ danh sách.
> **Cần hỏi đơn vị thẩm định:** có tập yếu tố tối thiểu bắt buộc không?

**Vị trí cần soi:** mục "Thông tin đầu vào" — bảng thông số đầu vào; đối chiếu chéo với
mọi công thức trong phần tính toán từng phân hệ.

**Ví dụ ĐẠT** `[minh họa]`
> Thông số đầu vào: thuê bao đăng ký 5.200.000; thuê bao active 1.800.000; người dùng
> đồng thời giờ cao điểm 42.000; request đồng thời 3.500; số giao dịch/người dùng/ngày 7;
> kích thước bản tin trung bình 12 KB; mục đích máy chủ: ứng dụng (App) và CSDL (MariaDB).
> Toàn bộ công thức mục 4 dùng lại đúng các giá trị này.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống phục vụ khoảng 5 triệu thuê bao. Định cỡ CPU dựa trên 3.500 request đồng thời
> tại giờ cao điểm.

*(Không phân biệt đăng ký / active / đồng thời; con số 3.500 request xuất hiện lần đầu
trong phần tính toán, không có ở bảng thông số đầu vào nên không truy được nguồn.)*

`see_also: [R42, R110, R35]`

---

#### ARC-xx — Module đã đủ năng lực giao dịch vẫn phải thiết kế cho sẵn sàng và dự phòng

- `legacy_ref: [R106]` · `checklist_ref: [CL-3.x.19, CL-3.x.6]` · Trang **20/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Module sau khi được định cỡ đáp ứng về giao dịch, cần thiết kế định cỡ để đảm bảo tính
> sẵn sàng, dự phòng và các yêu cầu trong chỉ tiêu kĩ thuật.

*(Chữ "kĩ thuật" viết `i` ngắn là của tài liệu gốc.)*

**Phạm vi áp dụng:** mọi phân hệ có bảng định cỡ.

**KHÔNG áp dụng khi:** phân hệ được nêu rõ là thành phần dùng thử/tạm, không yêu cầu
sẵn sàng. Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — phần định cỡ của phân hệ phải cho thấy **hai bước tách bạch**:
1. Con số tài nguyên **đủ đáp ứng tải giao dịch** (kết quả của R43–R49).
2. Con số đó **được nâng lên hoặc nhân số node** để đáp ứng tính sẵn sàng và dự phòng —
   ví dụ từ "cần 24 vCPU" thành "3 node × 16 vCPU active-active" — và nêu rõ căn cứ
   (mức dự phòng theo R101/R102, chỉ tiêu kỹ thuật đã ban hành).

**Tiêu chí KHÔNG ĐẠT:**
- Bảng cấu hình đề xuất **đúng bằng** nhu cầu tính ra theo tải, không có phần cho dự phòng.
- Có nhiều node nhưng không nói vì sao lại chọn số node đó — không phân biệt được đây là
  chia tải hay là dự phòng.
- Không nhắc gì tới chỉ tiêu kỹ thuật của hệ thống trong phần định cỡ phân hệ.

> **Ranh giới với R10:** R10 kiểm **phép tính** kịch bản mất 1 node (tải dồn về N−1 node
> có vượt ngưỡng không). R106 kiểm **bước thiết kế** — có nâng cấu hình lên vì lý do sẵn
> sàng/dự phòng hay không. Một bản chỉ tính đủ tải rồi dừng sẽ trượt R106 kể cả khi
> không có gì để R10 tính.

**Vị trí cần soi:** phần tính toán và bảng đề xuất cấu hình của **từng phân hệ**
(`CL-3.x.19`, `CL-3.x.20`).

**Ví dụ ĐẠT** `[minh họa]`
> Nhu cầu tải giờ cao điểm của phân hệ App: 24 vCPU, 96 GB RAM. Theo mức dự phòng
> active-active (hệ Rất quan trọng), đề xuất **03 node × 16 vCPU / 64 GB** — khi mất 01
> node, 02 node còn lại gánh 12 vCPU/node = 75%, vẫn trong ngưỡng KPI.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Nhu cầu tính toán của phân hệ App là 24 vCPU, 96 GB RAM. Đề xuất cấu hình: 02 node ×
> 12 vCPU / 48 GB.

*(Cấu hình đúng bằng nhu cầu tải, không có phần cho dự phòng; mất 01 node là quá tải 100%.)*

`see_also: [R10, R11, R51, R101]`

---

#### BAK-xx — Phải có giải pháp sao lưu và cộng thêm năng lực cho tác vụ sao lưu

- `legacy_ref: [R107]` · `checklist_ref: [CL-3.x.19, CL-3.2.19]` · Trang **20/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu, sao_luu]` · `severity: major`

**Trích dẫn nguyên văn**

> Có giải pháp sao lưu phục hồi đi kèm. Các máy chủ tính toán năng lực cần bổ sung năng
> lực đáp ứng cho tác vụ sao lưu dữ liệu. Tác vụ sao lưu cần đáp ứng được đưa yêu cầu về
> thời gian

*(Câu cuối bị cắt ở cuối trang 20 và nối sang trang 21 — phần thời gian hoàn thành backup
đã được bắt riêng ở **R39**, nên quy tắc này chỉ dùng hai câu đầu.)*

**Phạm vi áp dụng:** mọi phân hệ có dữ liệu cần sao lưu.

**KHÔNG áp dụng khi:** phân hệ không lưu trạng thái và tài liệu nêu rõ không cần sao lưu
(ví dụ node stateless thuần tính toán). Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — cả hai:
1. Tài liệu **có phần giải pháp sao lưu phục hồi**: nêu được đối tượng sao lưu, chu kỳ,
   nơi lưu bản sao (thiết bị/hệ thống khác), và cách phục hồi.
2. Cấu hình máy chủ đề xuất **có tính thêm phần tài nguyên cho tác vụ sao lưu** — nêu rõ
   phần cộng thêm là bao nhiêu (CPU/RAM/IOPS/băng thông trong cửa sổ backup), hoặc nêu
   giải pháp sao lưu không tiêu tốn tài nguyên máy chủ (ví dụ snapshot ở tầng lưu trữ)
   và giải thích vì sao.

**Tiêu chí KHÔNG ĐẠT:**
- Không có phần sao lưu nào trong tài liệu.
- Có nêu sao lưu nhưng cấu hình máy chủ **không cộng thêm gì** cho tác vụ này và cũng
  không giải thích vì sao không cần.
- Chỉ nói *"sử dụng hệ thống backup tập trung của Tập đoàn"* mà không cho biết tác vụ
  sao lưu chiếm bao nhiêu tài nguyên của máy chủ nguồn.

> **Phân vai với R39:** R39 là **định lượng** — kiểm *thời gian hoàn thành backup* có đáp
> ứng yêu cầu không (ví dụ 1 TB trong 2 giờ). R107 kiểm phần **cộng thêm tài nguyên** vào
> cấu hình máy chủ. Hai việc khác nhau, đừng gộp.

**Vị trí cần soi:** mục giải pháp sao lưu/phục hồi, mục sizing lưu trữ backup
(`CL-3.2.19`) và phần giải trình bảng cấu hình đề xuất từng phân hệ.

**Ví dụ ĐẠT** `[minh họa]`
> Sao lưu: full CSDL hằng tuần + incremental hằng ngày, ghi sang thiết bị lưu trữ backup
> riêng, giữ 30 ngày. Cửa sổ backup 01:00–03:00. Tác vụ backup chiếm thêm ~4 vCPU và
> ~180 MB/s I/O trên mỗi node DB → cấu hình đề xuất đã cộng thêm 4 vCPU/node so với nhu
> cầu tải nghiệp vụ.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Dữ liệu được sao lưu hằng ngày sang hệ thống backup tập trung của Tập đoàn.

*(Không nêu đối tượng, chu kỳ giữ, cách phục hồi; cấu hình máy chủ không cộng thêm phần
nào cho tác vụ sao lưu.)*

`see_also: [R39, R58, R70]`

---

#### ALC-xx — Quy hoạch cấp phát tránh lưu lượng vòng và đảm bảo an toàn khi lỗi phần cứng

- `legacy_ref: [R108]` · `checklist_ref: [CL-2.7, CL-3.x.5]` *(không có mục checklist chuyên
  về cấp phát — xem ghi chú)* · Trang **40/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [cap_phat, load_balancer, luu_tru, may_chu]` · `severity: major`

**Trích dẫn nguyên văn**

> Cấp phát tài nguyên LB, lưu trữ trên mạng lưới cần tránh lưu lượng chạy vòng qua nhiều
> lớp mạng, quy hoạch cấp phát tài nguyên lưu trữ, các node ảo hoá quan trọng (Ví dụ các
> cặp DB) đảm bảo an toàn khi gặp sự cố phần cứng thiết bị.

**Phạm vi áp dụng:** bản sizing có đề xuất cấp phát LB, lưu trữ, hoặc có cặp node ảo hóa
dự phòng.

**KHÔNG áp dụng khi:** hệ thống chỉ có một node duy nhất, không dùng LB và không dùng
lưu trữ dùng chung. Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — cả hai vế của trích dẫn:
1. **Đường đi lưu lượng:** mô hình vật lý cho thấy vị trí đặt LB và thiết bị lưu trữ so
   với các phân hệ dùng chúng, đủ để thấy lưu lượng không phải đi vòng qua nhiều lớp
   mạng; hoặc tài liệu nêu rõ yêu cầu đặt cùng zone/cùng lớp mạng.
2. **An toàn khi lỗi phần cứng:** các node ảo hóa dự phòng của cùng một cụm (điển hình là
   cặp DB) được nêu rõ là **phân bổ trên các máy chủ vật lý khác nhau** — hoặc nêu yêu
   cầu anti-affinity tương đương khi cấp phát.

**Tiêu chí KHÔNG ĐẠT:**
- Có cặp DB dự phòng nhưng không nói gì về việc đặt trên host vật lý khác nhau
  (vi phạm cùng lúc **R15**, vốn là quy tắc định lượng — xem `see_also`).
- Mô hình vật lý không thể hiện vị trí LB / lưu trữ so với các phân hệ dùng chúng.
- Đề xuất cấp phát nêu số lượng tài nguyên nhưng không có yêu cầu quy hoạch vị trí nào.

> **Ghi chú `checklist_ref`:** checklist thẩm định **không có mục nào riêng cho khâu cấp
> phát**, giống trường hợp R97. Hai mục gần nhất là `CL-2.7` (mô hình vật lý tổng quan)
> và `CL-3.x.5` (mô hình vật lý phân hệ) — đó là nơi thông tin này thực tế xuất hiện.
> Gộp chung vào danh sách "quy tắc không có mục checklist tương ứng" cần hỏi đơn vị
> thẩm định (mục 6).

**Vị trí cần soi:** mô hình vật lý tổng quan và mô hình vật lý từng phân hệ; mục đề xuất
cấp phát nếu có.

**Ví dụ ĐẠT** `[minh họa]`
> Cụm MariaDB gồm 03 node đặt trên 03 host vật lý khác nhau (yêu cầu anti-affinity khi
> cấp phát). LB và thiết bị lưu trữ đặt cùng zone DMZ-App với cụm Application, lưu lượng
> App → LB → DB không đi qua lớp core.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Cụm MariaDB gồm 03 VM cấu hình 16 vCPU / 64 GB, cấp phát trên hạ tầng Cloud Tập đoàn.

*(Không nêu yêu cầu phân bổ trên host vật lý khác nhau; 03 VM có thể rơi cùng một host,
mất cả cụm khi hỏng phần cứng.)*

`see_also: [R15, R91, ZONE-01]`

---

#### PRC-xx — Phương án cấp phát phải được thống nhất với TCT VTNet

- `legacy_ref: [R109]` · `checklist_ref:` *(không có mục checklist tương ứng)* ·
  Trang **40/44** · Nhóm kiểm: **B**
- `applies_to_equipment: [cap_phat]` · `severity: minor`

**Trích dẫn nguyên văn**

> Việc cấp phát tài nguyên vật lý tách biệt hoàn toàn, một phần, Bare-Metal, VM hay
> container là theo nhu cầu của bài toán, nếu không có yêu cầu đặc biệt thì cần phải
> triển khai trên hạ tầng Cloud tập trung của Tập đoàn. Đơn vị chủ quản hệ thống và TCT
> VTNet thống nhất phương án cấp phát trong quá trình xây dựng sizing và triển khai hệ thống.

**⚠️ Giới hạn kiểm — bắt buộc nêu trong finding:** Copilot chỉ kiểm được **tài liệu có
nêu hoặc dẫn chiếu việc đã thống nhất phương án cấp phát với TCT VTNet hay chưa**.
Copilot **không** xác minh được cuộc thống nhất đó có thật, biên bản có hợp lệ hay không.

**Phạm vi áp dụng:** mọi bản sizing đi kèm đề nghị cấp phát tài nguyên trên hạ tầng
Tập đoàn.

**KHÔNG áp dụng khi:** bản sizing chỉ phục vụ dự toán đầu tư / tham gia thầu, chưa xin
cấp phát. Trả về `không áp dụng`.

**Tiêu chí ĐẠT** — một trong hai:
1. Tài liệu nêu **hình thức cấp phát đã thống nhất** (vật lý tách biệt / Bare-Metal / VM
   / container) **và** dẫn chiếu được việc thống nhất với TCT VTNet — nêu buổi làm việc,
   văn bản, hoặc ý kiến thẩm định đã có.
2. Tài liệu ghi rõ **đang trong quá trình thống nhất** với TCT VTNet và nêu phương án
   đang đề xuất.

**Tiêu chí KHÔNG ĐẠT:**
- Chọn hình thức cấp phát (đặc biệt là Bare-Metal hoặc vật lý tách biệt) mà không nhắc
  gì tới việc trao đổi/thống nhất với TCT VTNet.
- Không nêu hình thức cấp phát nào.

> `severity: minor` vì đây là **yêu cầu thủ tục** và Copilot chỉ kiểm được bề mặt. Câu
> thông báo nên là lời nhắc bổ sung, không phải khẳng định hồ sơ sai.
>
> **Ghi chú `checklist_ref`:** không có mục checklist nào phủ — cùng nhóm với R97 và R108.

**Vị trí cần soi:** mục đề xuất cấp phát / kiến nghị, và danh mục tài liệu đính kèm.

**Ví dụ ĐẠT** `[minh họa]`
> Hình thức cấp phát: VM trên hạ tầng Cloud tập trung, riêng 06 datanode Hadoop cấp
> Bare-Metal. Phương án đã được thống nhất với TCT VTNet tại buổi làm việc ngày
> 12/6/2026 (biên bản kèm Phụ lục 4).

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Đề nghị cấp phát 08 máy chủ Bare-Metal cho cụm xử lý dữ liệu.

`see_also: [R91, R92, R95, R33]`

---

#### EVD-xx — Bảng thông số đầu vào phải tách tải theo loại nghiệp vụ kèm tỉ lệ

- `legacy_ref: [R110]` · `checklist_ref: [CL-2.5, CL-3.x.7]` · Trang **17/44** · Nhóm kiểm: **A**
- `applies_to_equipment: [may_chu]` · `severity: major`

**Trích dẫn nguyên văn** *(ô "Ghi chú" của dòng 2 bảng thông số đầu vào, trang 17)*

> Trong hệ thống có nhiều loại nghiệp vụ. Do vậy cần làm rõ những loại tải cần đáp ứng
> trong thời điểm Peak và tỉ lệ về số lượng mỗi loại trên tổng số giao dịch (tỉ lệ này
> được đánh giá, giả định sát nhất với thực tế).

**Trích dẫn bổ sung — hai dòng bắt buộc của bảng** (cùng trang):

> Tổng số thuê bao/người dùng sử dụng dịch vụ — Người dùng / thuê bao
> Tổng số giao dịch đồng thời tại thời điểm đạt giá trị Peak — TPS (TPM)

**Phạm vi áp dụng:** mọi bản sizing.

**KHÔNG áp dụng khi:** phần tách theo loại nghiệp vụ không áp dụng cho hệ **chỉ có một
loại giao dịch duy nhất** — nhưng tài liệu phải nói rõ điều đó; khi ấy hai dòng tổng vẫn
bắt buộc.

**Tiêu chí ĐẠT** — phải có đủ **cả ba**:
1. **Tổng số thuê bao/người dùng** sử dụng dịch vụ, có đơn vị.
2. **Tổng số giao dịch đồng thời tại thời điểm Peak**, theo **TPS** (hoặc TPM), hoặc
   CCU/RPS như tài liệu cho phép ở đoạn trên.
3. **Phân tách theo loại nghiệp vụ**: liệt kê các loại tải chính, mỗi loại có **tỉ lệ %
   trên tổng số giao dịch**, và **tổng các tỉ lệ bằng 100%**. Kèm một câu về căn cứ của
   tỉ lệ giả định (số liệu hệ đang chạy, thống kê, hoặc hệ tham chiếu).

**Tiêu chí KHÔNG ĐẠT:**
- Chỉ có một con số TPS tổng, không tách loại nghiệp vụ nào, trong khi phần mô tả hệ
  thống cho thấy có nhiều nhóm chức năng khác nhau.
- Có tách loại nghiệp vụ nhưng **không có tỉ lệ %**, hoặc tổng các tỉ lệ ≠ 100%.
- Tỉ lệ được đưa ra không kèm bất kỳ căn cứ nào (*"giả định 50/50"* không giải thích).
- Thiếu tổng số thuê bao/người dùng.

> **Phân vai với R42:** R42 (định lượng) nói *định cỡ phải làm theo **tổng** tải giao
> dịch giờ Peak*. R110 nói tài liệu phải **trình bày phân tách** tổng đó theo loại nghiệp
> vụ kèm tỉ lệ. Một bản sizing tính đúng theo tổng nhưng không tách loại thì **qua R42,
> trượt R110**.
>
> Phần "tổng các tỉ lệ = 100%" là **kiểm được bằng code** — nên khi số hóa ở 0.5, tách
> ý này thành `computed_evidence` để finding có căn cứ mạnh hơn `rule_quote` đơn thuần.

**Vị trí cần soi:** mục "Thông tin đầu vào" — bảng thông số đầu vào của đơn vị yêu cầu;
đối chiếu với mục mô tả chức năng/nghiệp vụ để biết hệ có nhiều loại giao dịch không.

**Ví dụ ĐẠT** `[minh họa]`
> Tổng số thuê bao sử dụng dịch vụ: 5.200.000. Tổng giao dịch đồng thời giờ Peak: 4.000 TPS,
> gồm: tra cứu số dư 60% (2.400 TPS), chuyển tiền 25% (1.000 TPS), nạp thẻ 15% (600 TPS).
> Tỉ lệ lấy theo thống kê 03 tháng gần nhất của hệ thống hiện hành.

**Ví dụ KHÔNG ĐẠT** `[minh họa]`
> Hệ thống cần đáp ứng 4.000 TPS tại giờ cao điểm cho toàn bộ các nghiệp vụ tra cứu,
> chuyển tiền và nạp thẻ.

*(Không có tổng số thuê bao; không tách tỉ lệ từng loại nghiệp vụ — trong khi ba nghiệp
vụ này có độ phức tạp rất khác nhau nên tỉ lệ ảnh hưởng trực tiếp tới kết quả định cỡ.)*

`see_also: [R42, R104, R26]`

---

## 6. Tổng kết Bước 2

| | Số lượng |
|---|---:|
| Quy tắc định tính (sau khi R66 chuyển sang định lượng) | 25 |
| — nhóm C, không viết tiêu chí (R24 loại, R34 chờ Phụ lục 01) | 2 |
| — gộp R25 + R32 làm một | −1 |
| **Cần viết tiêu chí** | **22** |
| — đã viết ở Bước 1 (mẫu): R26, R30, R37 | 3 |
| — **viết ở Bước 2** | **19** |

Phân bố 19 quy tắc Bước 2: `ARC` 4 · `EVD` 5 · `MTH` 3 · `PRC` 5 · `STO` 1 · `TST` 1.

### Ba việc phát sinh khi viết Bước 2

1. **Phát hiện quy tắc bị sót ở 0.1.** Khi lấy trích dẫn cho R10 (trang 9) thấy hai
   câu chưa có trong R01–R100 — đã bổ sung thành **R101** (cơ chế dự phòng bắt buộc
   theo mức độ quan trọng) và **R102** (mức dự phòng căn cứ phân loại hệ thống), ghi
   ở `rules-flat-draft.md` mục "BỔ SUNG". R101 trả lời điểm `[CẦN XÁC NHẬN]` đang
   treo ở `QD849-02`.
   → **Nên rà lại độ phủ của 0.1 một lượt**: nếu trang 9 sót 2 câu thì trang khác
   cũng có thể sót.

2. **Hai quy tắc không có mục checklist tương ứng:** `R25+R32` (yếu tố scale up/out)
   và `R97` (thu hồi). Nghĩa là Vòng 1 không bắt được nếu tài liệu thiếu hẳn phần đó
   — chỉ Vòng 2 bắt được. Với R97 thì hợp lý (checklist chỉ phủ luồng cấp phát); với
   R25+R32 thì nên hỏi đơn vị thẩm định xem có nên bổ sung một mục checklist.

3. **Bốn quy tắc `MTH` loại trừ lẫn nhau** — R26, R27, R28, R29. C5 phải xác định dạng
   định cỡ **trước**, rồi chỉ chạy quy tắc tương ứng; ba quy tắc còn lại trả về
   `không áp dụng`. Đây là ràng buộc thực thi, cần ghi vào `rules.yaml` ở mục 0.5
   (dùng `see_also` + một trường điều kiện loại trừ).

---

## 7. Tổng kết Bước 3 — 8 quy tắc bổ sung (2026-08-26)

| | Số lượng |
|---|---:|
| Quy tắc định tính phát hiện khi rà độ phủ (mục 0.2) | 8 |
| — nhóm A | 6 |
| — nhóm B (R102, R109) | 2 |
| — nhóm C | 0 |

Phân bố: `ARC` 2 (R102, R106) · `EVD` 3 (R103, R104, R110) · `PRC` 1 (R109) ·
`BAK` 1 (R107) · `ALC` 1 (R108).

**Tổng toàn file: 30/30 quy tắc cần tiêu chí đã có tiêu chí** (22 ở Bước 1–2 + 8 ở Bước 3).
Số trích dẫn đã kiểm khớp nguyên văn với `.tmp-lan7/clean.txt`: **26 + 10 = 36**.

### Ba việc phát sinh khi viết Bước 3

1. **`[CẦN XÁC NHẬN]` R104 — 11 yếu tố có bắt buộc đủ không?** Tài liệu liệt kê 11 yếu
   tố ảnh hưởng thông số tài nguyên máy chủ nhưng không nói yếu tố nào bắt buộc, và
   nhiều yếu tố không áp dụng cho mọi hệ. Tiêu chí đã viết neo vào *"những yếu tố bản
   sizing thực sự dùng"* thay vì đếm đủ danh sách — nếu ép đủ 11 sẽ sinh cảnh báo sai
   hàng loạt. **Cần hỏi đơn vị thẩm định có tập yếu tố tối thiểu không.**

2. **Thêm hai quy tắc vào danh sách "không có mục checklist tương ứng".** Trước đây có
   `R25+R32` và `R97`; nay thêm **R108** (quy hoạch cấp phát) và **R109** (thống nhất
   phương án với TCT VTNet). Cả bốn đều thuộc khâu **cấp phát**, mà checklist thẩm định
   không phủ khâu này. Đây là một khoảng trống có hệ thống, không phải bốn ca lẻ →
   nên hỏi đơn vị thẩm định xem cấp phát có nằm ngoài phạm vi checklist một cách cố ý
   hay không, thay vì đề nghị bổ sung từng mục.

3. **Ba cặp quy tắc phân vai ĐL ↔ ĐT nằm sát nhau, phải giữ ranh giới khi số hóa ở 0.5:**
   R101 (ánh xạ cơ chế dự phòng — C4) ↔ R102 (trình bày căn cứ — C5);
   R39 (thời gian backup — C4) ↔ R107 (cộng thêm tài nguyên cho backup — C5);
   R42 (định cỡ theo tổng tải — C4) ↔ R110 (trình bày phân tách tải — C5).
   Mỗi cặp là hai quy tắc khác nhau, **không được khử trùng thành một** — nhưng khi cả
   hai cùng trượt thì C7 nên gom lại một khối để người dùng không thấy như báo lỗi hai lần.
