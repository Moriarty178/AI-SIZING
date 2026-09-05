# Việc cần người làm — và làm ở máy nào

> Cập nhật 2026-09-04. Dự án chạy trên **hai môi trường tách rời**, và đó là ràng buộc
> lớn nhất về nhịp làm việc:
>
> | | Laptop ngoài | Máy trong mạng nội bộ |
> |---|---|---|
> | Model tự dựng (`10.221.58.70:8401`) | ❌ không với tới | ✅ |
> | Mã nguồn, hồ sơ, quy tắc, test | ✅ | ✅ |
> | Chi phí một lượt chạy | 0 | ~40 giây **mỗi lời gọi** |
>
> Nguyên tắc rút ra: **mọi thứ làm được không cần model thì làm ở laptop**, để thời gian
> ngồi trong mạng nội bộ chỉ dành cho những lượt chạy thật sự cần model.

---

## A. Làm được ở LAPTOP — không cần model

### A1. Soi độ chính xác của checklist tự điền (1.17) — *đang chặn việc nghiệm thu 1.17*

```bash
python scripts/fill_checklist.py "danh_sach_sizings_da_duyet/<thư mục>/<file>.docx"
```

Kết quả ra `docs/checklist/`: bản `.md` để đọc, bản `.csv` mở bằng Excel.

**Cần bạn:** mở một bản `.md`, xem cột *Tham chiếu theo tài liệu sizing* và nói cho tôi
**dòng nào trỏ sai chỗ**. Đã đo được **độ phủ** (trung vị 22/57 mục trên 47 bản) nhưng
**chưa đo được độ chính xác** — không có nhãn vàng cho việc "mục này đúng ra nằm ở đâu",
nên đây là thứ duy nhất tôi không tự làm thay được. Mất khoảng 5–10 phút.

### A2. Chạy giao diện thử (1.14)

```bash
pip install streamlit          # lần đầu
streamlit run ui/app.py
```

Hai chế độ **Đọc tài liệu** và **Điền checklist** chạy bình thường không cần model.
Chế độ **Thẩm định đầy đủ** tự ẩn kèm dòng giải thích khi chưa gọi được model.

Giao diện đã ép nghe trên `localhost` (`.streamlit/config.toml`) — mặc định của Streamlit
là lắng nghe mọi card mạng, không hợp với công cụ mở hồ sơ định cỡ nội bộ.

### A3. Duyệt 8 mục `lookup:` cho `rules.yaml`

`STO-02` · `STO-03` · `STO-09` · `STO-13` (IOPS theo loại ổ, write penalty theo RAID) ·
`CPU-10` · `BAK-07` (thế hệ LTO) · `LAN-02` · `RCK-01` (RU theo loại thiết bị).

Bảng tra của 8 quy tắc này hiện chỉ nằm trong trường `note` dạng văn xuôi
(*"NL-SAS 100 · SAS 10k 140 · SSD từ 5000"*) nên máy không đọc được. Chép bảng vào Python
sẽ **vi phạm NT3**, nên C4 đang đánh dấu `khong_kiem_chung_duoc` kèm lý do.

**Cần bạn:** xác nhận số liệu từng bảng với đơn vị thẩm định, rồi tôi viết vào mục
`lookup:` của `rules.yaml`. Không gây chặn việc khác.

### A4. Duyệt quy tắc "kiểm hợp lý đơn vị"

Xem `sanity.py`. Cũng không gây chặn.

### A5. Kiểm độc lập một lát cắt `eval_sheet_mau_kiem_daduyet.csv`

88 dòng audit do máy gợi ý mã quy tắc. Nợ từ mục 0.7: *"cần người đọc và xác nhận phản
ánh đúng tài liệu gốc"*. Chưa làm thì **mọi con số recall đều phải kèm cảnh báo "nhãn
chưa kiểm định độc lập"** — cảnh báo này đã được ép vào báo cáo eval bằng test.

### A6. Ghép `pnx_file` ↔ đúng phiên bản `.docx`

Nợ từ 0.7 mục 5. PNX nhận xét bản **trước khi sửa**, mà nhiều hồ sơ giữ nhiều bản
(PNM 5 bản, APIGW-Meta 3, SSO 3). Chạy trên bản đã sửa thì lỗi đã vá → **recall thấp giả
tạo**. Đây là việc đọc tài liệu, không cần model.

### A9. Diễn tập lượt B1 trước khi vào mạng nội bộ — *nên chạy ngay trước khi đi*

```bash
python -m eval.run_eval --gia-lap --ho-so "GSCG,Data Security,Vtag,PBH 4.0" --song-song 6
```

Chạy TRỌN đường của lượt B1 bằng **model giả**, mất **~12 giây** thay vì 1,1 giờ.
Mục đích duy nhất: bảo đảm không có lỗi ghép nối nào làm hỏng lượt chạy thật. Lần chạy
đầu đã bắt được hai lỗi, trong đó `--tiep-tuc` sập ngay khi gọi.

Muốn thử cả tình huống xấu: thêm `--bom-loi 0.3` (bơm 30% lượt gọi hỏng).

⚠️ Báo cáo sinh ra tên `dien-tap-*.md` và **mọi con số trong đó là vô nghĩa** — chỉ
dùng để xác nhận đường chạy không vỡ.

### A7. Sinh mẫu Word chuẩn (1.16) nếu cần đưa cho người viết hồ sơ

```bash
python scripts/make_word_template.py
```
### A8. Xác nhận nhãn cho 40 ảnh mẫu (2.2) — *không chặn việc khác*

```bash
python scripts/danh_gia_phan_loai_anh.py            # in độ chính xác + hạn chế
python scripts/danh_gia_phan_loai_anh.py --toan-bo  # thêm phân bố trên 776 ảnh (~3 phút)
```

`data/nhan_anh_mau.json` giữ 40 nhãn ảnh (console / dashboard / sơ đồ / ảnh văn bản).
**Nhãn do tôi nhìn ảnh mà gán, chưa ai xác nhận** — cùng hạn chế đã ghi cho eval set.
Nếu bạn thấy một nhãn sai thì sửa thẳng trường `loai` trong file rồi chạy lại script;
độ chính xác hiện là **34/40 (85%), 92% khi máy dám kết luận**.


---

## B. Phải làm ở MÁY TRONG MẠNG NỘI BỘ — cần model

### B1. Đo recall trên mẫu 5 hồ sơ — ⭐ **việc quan trọng nhất còn lại của Giai đoạn 1**

```bash
git pull
py -m eval.run_eval --ho-so "GSCG,Data Security,Vtag,PBH 4.0" --song-song 8 --uoc-tinh
py -m eval.run_eval --ho-so "GSCG,Data Security,Vtag,PBH 4.0" --song-song 8
```

- **~1,1 giờ máy** (ước lượng in ra trước khi chạy), chạy nền, không cần ngồi canh.
- Bốn hồ sơ này gộp **160/475 nhãn (34%)**.
- ⚠️ **Đã bỏ `Mybox` khỏi lệnh**: nó nằm trong **tập TEST giữ kín**, nên lệnh cũ vẫn
  chỉ chạy 4 hồ sơ (script tự lọc theo tập). Con số "5 hồ sơ / 191 nhãn" ghi trước đây
  là **sai**. **Đừng** thêm `--tap test` để "chạy cho đủ 5" — làm thế là đốt tập giữ kín
  vốn chỉ được dùng một lần ở mục 3.6.
- Cả tập dev tốn **6,5–11 giờ**, nên **không chạy toàn tập**.
- Kết quả ra `eval/reports/`. Đây là con số quyết định tiêu chí hoàn thành Giai đoạn 1.
- Muốn gỡ nốt thiên lệch phiên bản thì thêm **`--moi-phien-ban`** (chạy đúng bản của
  từng vòng nhận xét): đúng hơn nhưng **2,4 giờ** thay vì 1,1 giờ.
- **Bị ngắt giữa chừng thì chạy lại kèm `--tiep-tuc`** — hồ sơ nào đã xong được lấy lại
  từ `.cache/eval/`, không gọi model lần nữa. Kể cả không có cờ đó, **đệm lời gọi**
  (2.12) cũng đã làm phần lớn lượt chạy lại gần như miễn phí. Muốn đo lại THẬT từ đầu
  thì đặt `SIZING_COPILOT_KHONG_CACHE=1`.
- Xem trước cách chọn phiên bản mà không cần model: `python scripts/ghep_phien_ban.py`.

Khi đọc kết quả, nhớ: **29/475 nhãn (6%) vĩnh viễn không với tới được** vì `cap moi MNP
32034` và `Cấp mới hệ thống VAPS` không có bản `.docx` nào. Chúng vẫn nằm trong mẫu số.

### B2. Xác nhận C3 v6 — *không bắt buộc*

```bash
py scripts/try_c3_on_dossier.py "danh_sach_sizings_da_duyet/cap moi BCCS3_thị_trường_Lào 34221/Sizing_BCCS3_thị_trường_Lào_23072024.docx"
```

~4 phút (32 lượt gọi, v5 tốn 94). Con số cần nhìn: `cột gán được/cột hỏi`,
`cột trùng tham số`, `mâu thuẫn giữa bảng` (kỳ vọng thấp), `lượt gọi hỏng` (kỳ vọng 0).

Đã **chốt dừng vòng lặp cải tiến C3 ở v6** nên dù kết quả thế nào tôi cũng chỉ ghi nhận,
không sửa tiếp. Bỏ qua bước này cũng được.

### B5. *(sau khi B1 xong)* Chạy thử 2.3 — đọc ảnh bằng vision

⚠️ **Đừng bật 2.3 trong lượt B1.** Đã chốt: B1 chạy sạch trước để con số recall quy
được về đúng một thay đổi. 2.3 mặc định TẮT trong pipeline, có test chặn.

Khi B1 xong và muốn thử đọc ảnh, gọi `pipeline.chay(..., doc_anh=True)` (mặc định đọc
`so_do` + `console` — 325/776 ảnh, ~3,6 giờ cho cả 47 bản; một bản Vtag là 19/43 ảnh
≈ 13 phút). Muốn đọc thêm biểu đồ giám sát thì truyền
`loai_anh=("so_do","console","dashboard")`.

Con số cần nhìn: **`trich_dan_bia`** — số giá trị bị loại vì không nằm trong trích dẫn
của chính nó. Cao là dấu hiệu model đang bịa, cùng loại rủi ro với C3.

### B3. Xem báo cáo thật trên giao diện

`streamlit run ui/app.py` → chế độ **Thẩm định đầy đủ**. Giao diện in ước lượng chi phí
trước khi cho bấm chạy, và hiện tiến độ từng lượt gọi.

### B4. *(chỉ khi làm 1.11 / C6 ở Giai đoạn 2)* cài `sentence-transformers`

Kéo theo `torch` ~2GB. Cụm nội bộ **không có** endpoint `/v1/embeddings` (đo ở 0.10) nên
BGE-M3 phải chạy cục bộ. Chưa cần cho Giai đoạn 1.

---

## C. Cần hỏi ĐƠN VỊ THẨM ĐỊNH — không phải việc của máy nào

Bốn điểm dưới đây tôi **không tự quyết** theo đúng quy ước làm việc của dự án.

### C1. 8 mục checklist không xuất hiện ở bất kỳ bản nào trong 47 bản

`3.1.6`/`3.2.7` (mức độ dự phòng theo 849/QĐ-CNVTQĐ) · `3.1.9`/`3.2.10` (nguồn request) ·
`3.1.10`/`3.2.11` (giao thức, port) · `3.1.15`/`3.2.16` (IOPS, latency mỗi request).

Chúng đi thành **từng cặp Application/Database** nên khó là ngẫu nhiên. Hỏi: hồ sơ thực
tế có bao giờ nêu chúng không, hay đây là khoảng trống có hệ thống?

### C2. `R104` — có tập tối thiểu các yếu tố ảnh hưởng không?

Guideline liệt kê 11 yếu tố nhưng không nói cái nào bắt buộc. Ép đủ 11 sẽ sinh cảnh báo
sai hàng loạt.

### C3. Khâu cấp phát không có mục checklist nào phủ

`R25+R32`, `R97`, `R108`, `R109`. Nằm ngoài phạm vi checklist một cách cố ý, hay bị sót?

### C4. Cách đo false positive

Bản đã ký **không sạch** (vẫn còn lỗi PNX từng nêu), nên không dùng thẳng làm tập
"Copilot phải im lặng" được. Tiêu chí Giai đoạn 3 đòi false positive ≤ 20%.

---

## D. Việc tôi làm tiếp, không cần chờ ai

- 1.15 — demo nội bộ (chờ B1 để có số thật mà trình bày).
- Giai đoạn 2: **2.1 + 2.2 đã xong 2026-09-04** (trích ảnh kèm ngữ cảnh, phân loại ảnh —
  cả hai chạy offline). Còn **2.3** (vision + OCR) cần model, và **2.4/2.5**.
- C6 truy hồi hồ sơ tương tự (cần `sentence-transformers`, xem **B4**).
- Sửa 1.17 theo phản hồi ở **A1**.
