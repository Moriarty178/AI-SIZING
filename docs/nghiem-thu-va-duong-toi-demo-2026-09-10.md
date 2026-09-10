# Nghiệm thu 1.13 và đường tới bản demo nội bộ

> Lập 2026-09-10, **TRƯỚC khi chạy** hai lượt còn lại. Ghi trước là có chủ đích:
> đặt tiêu chí sau khi nhìn kết quả thì bao giờ cũng đặt vừa khít kết quả ấy.

---

## 1. Đang có gì

Lượt dev đầy đủ đầu tiên (2026-09-09, 14 hồ sơ, 88 phút, song song 12):

| | |
|---|---:|
| Recall so với bộ quy tắc | 87,5% (273/312) |
| Recall so với mọi yêu cầu | 86,1% (273/317) |
| Recall thực chất (sàn) | 10,9% (34/312) |
| Recall theo LOẠI nhãn | 70,3% |
| **Nhóm quyết định** | **5/71 = 7,0%** |

Một lượt so sánh độc lập trên 3 hồ sơ (2026-09-10, đệm TẮT): **1/62 nhãn đổi kết
quả**, thực chất và nhóm quyết định không đổi.

---

## 2. Hai lượt sắp chạy — CHỐT TRƯỚC kết quả mong đợi

```powershell
$env:SIZING_COPILOT_KHONG_CACHE = "1"
py -m eval.run_eval --tap dev --song-song 12      # lượt C
py -m eval.run_eval --tap dev --song-song 12      # lượt D
Remove-Item Env:\SIZING_COPILOT_KHONG_CACHE
```

Đệm **phải tắt**: bật thì lượt C và D lấy lại nguyên kết quả lượt A và đo được
đúng con số 0.

Dự kiến mỗi lượt **~110–130 phút** (đệm tắt ⟹ ~1.930 lượt gọi, ở 16,6 lượt/phút
đo được).

### Ngưỡng ĐẠT — chốt trước

| Chỉ số | Lượt A | Dải chấp nhận cho C và D | Vì sao |
|---|---:|---|---|
| Trúng | 273 | **265–281** (±8 nhãn) | quy từ biên độ đo được 1/62 nhãn × 312 ≈ 5, nới lên 8 |
| Recall bộ quy tắc | 87,5% | **85,0–90,0%** | tương ứng dải trên |
| Thực chất | 34 | **28–40** | ±6 |
| **Nhóm quyết định** | **5/71** | **3–7 nhãn** (4,2–9,9%) | mẫu số nhỏ nên mỗi nhãn là 1,4 điểm % |
| Hồ sơ chạy được | 13/14 | **13/14** | VAPS không có `.docx` — bất biến |
| Hồ sơ lỗi | 0 | **0** | |

**Nghiệm thu ĐẠT khi cả ba lượt A · C · D nằm trong dải trên**, và nhóm quyết
định của ba lượt lệch nhau **không quá 2 nhãn**. Khi đó câu công bố là:

> *"Trên tập dev 14 hồ sơ, xếp nhóm theo phán quyết 2026-09-09, công cụ đạt
> **7% ± <biên độ quan sát>** ở nhóm nhãn đòi tính/so số (5/71), và 87,5% trên
> thước đo hào phóng nhất. Đo bằng ba lượt chạy độc lập, đệm tắt."*

### Ngưỡng KHÔNG ĐẠT — và làm gì khi đó

- **Nhóm quyết định lệch quá 2 nhãn** (ví dụ 5 · 9 · 2) ⟹ một lượt chạy KHÔNG đủ
  để công bố một con số điểm. Khi đó công bố **dải** chứ không công bố điểm, và
  ghi rõ cần thêm lượt hoặc thêm nhãn mới ổn định được.
- **Recall lệch quá 5 điểm %** ⟹ có gì đó khác ngoài dao động model (đổi mã, đổi
  bản tài liệu, lỗi ghép phiên bản). Dừng, truy nguyên, KHÔNG công bố.
- **Bất kỳ hồ sơ nào lỗi** ⟹ sửa rồi chạy lại; hồ sơ lỗi vẫn nằm trong mẫu số nên
  nó kéo recall xuống một cách không liên quan tới chất lượng.

### Ba lượt này KHÔNG trả lời được gì

Nói trước để không ai đọc quá con số:

1. **Không đo được false positive.** Finding không khớp nhãn không có nghĩa là
   sai. Ta chưa có cách đo, và đây vẫn là hạn chế lớn nhất.
2. **Không nói gì về tập test.** Tập test giữ kín, chỉ chạy một lần ở 3.6.
3. **Không nói công cụ có HỮU ÍCH không.** Recall đo mức trùng với người thẩm
   định; nó không đo việc người viết sizing đọc báo cáo rồi có sửa được không.
   Đó là việc của bản demo, xem phần 3.

---

## 3. Cái chặn bản demo, và nó KHÔNG phải recall

Đếm trên chính lượt dev đầy đủ, **trước C7**:

| | finding | «không tìm thấy» | thực chất |
|---|---:|---:|---:|
| VTracking | 717 | 681 | 36 |
| BCCS3 | 568 | 532 | 36 |
| PNM | 488 | 474 | 14 |
| … 13 hồ sơ | **4.381** | **4.184 (95,5%)** | **197** |

Trên toàn tập dev, đúng **3 finding `sai_cong_thuc` và 1 `vuot_nguong`**.

C7 còn khử trùng và hoãn Vòng 2 nên báo cáo cuối nhỏ hơn — **nhưng chưa ai đo
nhỏ bao nhiêu**. Đó là con số quyết định demo: người đánh giá mở báo cáo ra và
thấy bao nhiêu dòng.

> **Một báo cáo 700 dòng toàn «không tìm thấy trường này» sẽ khiến người đọc kết
> luận công cụ không chạy được — bất kể recall 87,5%.**

Đo bằng một lệnh, gần như miễn phí vì đệm còn ấm:

```powershell
py scripts/do_bao_cao.py "danh_sach_sizings_da_duyet/cap bo sung VTracking 2.0.1 14716/Thiet ke va dinh co he thong_VTracking 2.0.1.docx" --ghi bao-cao-mau.md
```

Gửi lại khối thống kê + file `bao-cao-mau.md`. **Chạy cái này TRƯỚC hai lượt eval**
— nó tốn 2 phút và quyết định thứ tự mọi việc còn lại.

---

## 4. Đường tới demo trên máy nội bộ

### Đã xong

`Dockerfile` (đã build thật, `/app` 1,2 MB, không có hồ sơ khách) ·
`docker-compose.copilot.yml` (API + giao diện) · API bất đồng bộ + hàng đợi ·
giao diện nộp bài bằng mã việc · `docs/docker-mang-noi-bo.md` (proxy · apt · TLS
MITM) · `scripts/khoi_dong_thu.py`.

### Còn lại

| # | Việc | Người | Máy | Chặn demo? |
|---|---|---:|---:|---|
| D1 | Đo kích thước báo cáo thật (`do_bao_cao.py`) | — | 2 phút | quyết định D2 |
| D2 | **Cắt nhiễu báo cáo** — gộp «không tìm thấy» theo NHÓM thay vì mỗi tham số một dòng | 1–2 ngày | — | **CÓ** |
| B4 | C7 chịu được bản NHÁP — phân biệt *"người viết chưa làm"* với *"công cụ không đọc được"* | (gộp vào D2) | — | **CÓ** |
| D3 | Ghi rõ giới hạn ngay trên giao diện: đây là công cụ **cố vấn**, bắt được 7% nhóm đòi tính | 0,25 ngày | — | **CÓ** |
| B5 | Hướng dẫn sử dụng 1–2 trang | 0,5 ngày | — | CÓ |
| D4 | Tài liệu mẫu cho người đánh giá thử | 0,25 ngày | — | CÓ |
| D5 | Build image trên máy nội bộ (proxy + CA) rồi `compose up` | 0,25 ngày | 30 phút | **CÓ** |
| — | 3 lượt eval (phần 2) | 0,5 ngày | ~4 giờ | không |

**Cộng: ~2,5–3,5 ngày người · ~35 phút máy** (chưa kể 4 giờ eval chạy song song).

### D2 là việc lớn nhất, và đây là hình dạng của nó

Hiện mỗi tham số C3 không trích được sinh **một** finding `thieu_thong_tin`. Với
một tài liệu, đó là 400–680 dòng gần như giống hệt nhau.

Cần gộp: thay vì 47 dòng *«Chưa có `dung_luong_backup` cho phân hệ X»*, một dòng:

> **Chưa đọc được 47 tham số nhóm SAO LƯU** (BAK-01…BAK-11) trên 6 phân hệ. Nếu
> tài liệu CÓ những số này, hãy trình bày chúng thành bảng; nếu CHƯA có, đây là
> phần còn thiếu.

Câu ấy làm đúng hai việc cùng lúc — cắt nhiễu, và nói thật rằng công cụ **không
phân biệt được** «người viết chưa làm» với «công cụ không đọc được» (NT4). Đó
chính là B4.

### Thứ tự đề xuất

1. **D1 ngay** (2 phút máy) — nó quyết định D2 to hay nhỏ.
2. **Hai lượt eval chạy nền** (~4 giờ máy) — không đụng gì tới việc của tôi.
3. **Tôi làm D2/B4 trên laptop song song** — 0 lượt gọi model.
4. D3 · B5 · D4 sau khi D2 xong.
5. **D5 cuối cùng**: build trên máy nội bộ rồi `compose up`.

Demo trước khi làm D2 là tự đưa cho người đánh giá một báo cáo 700 dòng nhiễu.
Recall 87,5% sẽ không cứu được ấn tượng đó.
