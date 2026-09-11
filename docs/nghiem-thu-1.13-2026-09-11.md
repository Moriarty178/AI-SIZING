# Nghiệm thu 1.13 — kết luận sau ba lượt dev đầy đủ

> 2026-09-11. Đối chiếu với ngưỡng đã **chốt TRƯỚC** ở
> `docs/nghiem-thu-va-duong-toi-demo-2026-09-10.md`. Không đổi ngưỡng sau khi xem số.

## 1. Ba lượt đã chạy

| Lượt | Ngày | Nhiệt độ | Đệm | Thời gian |
|---|---|---:|---|---:|
| A | 09-09 | 0,1 | bật một phần (475 lượt) | 88 phút |
| C | 09-10 | 0,1 | **tắt** | 243 phút |
| D | 09-11 | **0,0** | **bật (374 lượt)** | 167 phút |

Chấm lại cả ba **dưới cùng một cách xếp nhóm** (từ file `.json` chi tiết, 0 lượt gọi
model) — vì lượt D đã không nạp được phán quyết thẩm định (mục 4):

| Chỉ số | Dải chốt trước | A | C | D |
|---|---|---:|---:|---:|
| Trúng | 265–281 | 273 ✓ | 270 ✓ | 275 ✓ |
| Recall bộ quy tắc | 85–90% | 87,5% ✓ | 86,5% ✓ | 88,1% ✓ |
| Thực chất | 28–40 | 34 ✓ | 32 ✓ | **45 ✗** |
| **Nhóm quyết định** | 3–7 | **5** ✓ | **5** ✓ | **12 ✗** |
| Hồ sơ chạy được | 13/14 | ✓ | ✓ | ✓ |
| Hồ sơ lỗi | 0 | ✓ | ✓ | ✓ |
| QĐ lệch ≤ 2 nhãn | | | | **✗ (5 · 5 · 12)** |

## 2. Kết luận theo đúng tiêu chí đã chốt: KHÔNG ĐẠT

Lượt D nằm ngoài dải ở hai chỉ số. **Không đổi tiêu chí để nó lọt.**

Nhưng lượt D **không phải phép lặp**: nó đổi nhiệt độ, bật đệm, và mất phán quyết
thẩm định. Nó trả lời một câu hỏi KHÁC (xem mục 5). Hai lượt hợp lệ — A và C — đều
trong dải và **trùng khít ở nhóm quyết định (5 = 5)**.

**Muốn nghiệm thu đúng tiêu chí đã chốt: thêm MỘT lượt nhiệt độ 0,1, đệm TẮT.**
Khi đó câu công bố sẽ là:

> *"Trên tập dev 14 hồ sơ, nhiệt độ 0,1, xếp nhóm theo phán quyết 2026-09-09:
> recall bộ quy tắc 86,5–87,5%; nhóm quyết định **5/71 = 7,0%** trong cả ba lượt;
> trong đó chỉ **1/71 = 1,4%** là nhờ code tính lại con số."*

## 3. Con số quan trọng nhất: 1/71

Nhóm quyết định đòi *tính hoặc so số*. Phán quyết Câu 2 là *"phải tính lại con số
mới tính là đạt"*. Soi từng nhãn trúng:

| | QĐ thực chất | trong đó **code tính** | chỉ nhờ `thieu_muc` (C5) |
|---|---:|---:|---:|
| A — t=0,1 | 5/71 | **1/71** | 4 |
| C — t=0,1 | 5/71 | **1/71** | 4 |
| D — t=0,0 | 12/71 | **4/71** | 8 |

Bốn trên năm cú "trúng thực chất" là C5 nói *"thiếu thành phần"*, khớp nhãn qua
`rule_ref` hào phóng. Ví dụ nhãn *«Tính toán lại số liệu Ram, cint, HDD»* được tính
trúng vì công cụ nói *"thiếu mục EVD-22"* — không tính gì về RAM cả.

Nhãn duy nhất code thật sự tính ra ở t=0,1 là VTracking *«Tính thông lượng LB, FW
chỉ có K dự phòng 1.2»* — tức phép kiểm 2.6 viết ngày 2026-09-09.

Từ nay báo cáo eval in cả hai con số (`Nhóm quyết định — TÍNH bằng code`).

## 4. Hai lỗi của tôi làm phán quyết thẩm định biến mất không dấu vết

Ở lượt D, 4 nhãn phán quyết đích danh bị xếp về nhóm quyết định **dù văn bản khớp
hoàn toàn**, mẫu số nhảy 71 → 75, và báo cáo không nói một chữ. Hai lỗi chồng nhau:

1. `_nhan_thu_tuc_dich_danh` nuốt mọi lỗi đọc file và trả `{}` im lặng.
2. `run_eval` ghi đè `ev.canh_bao = canh_bao`, vứt luôn cảnh báo `doi_chieu` vừa
   thêm — nên kể cả khi có phát hiện, nó cũng không tới được báo cáo.

Đã sửa: báo cáo **nói ra** khi phán quyết không nạp được và dặn không trích con số
nhóm quyết định của lượt đó; `run_eval` gộp chứ không ghi đè; đọc file chịu được
BOM; và **`run_eval` kiểm phán quyết TRƯỚC khi gọi model** — hỏng thì dừng ngay, không
phí 4 giờ.

**Nguyên nhân gốc trên máy nội bộ tôi chưa biết** — file có trong repo, lượt C còn
đọc được. Cần `git status` và mở thử `data/phan_nhom_tham_dinh.json` trên máy đó.

## 5. Nhiệt độ 0,0: đừng đổi dựa trên một lượt

Lượt D tăng nhóm quyết định 5 → 12. Nguồn của phần tăng:

- **+3 nhãn nhờ code tính**: đều là CÙNG MỘT finding `CPU-01 vuot_nguong` của
  APIGW-Meta, khớp 3 nhãn cùng mang mã `CPU-01`. Thực chất là **1** phát hiện mới.
- **+4 nhãn nhờ C5 phán `thieu_muc`**.

Và trên toàn tập, t=0,0 sinh thêm **58 finding "thiếu thành phần"** trên 38 cặp
(hồ sơ, quy tắc). Chỉ vài cái khớp nhãn thẩm định. Phần còn lại **không ai biết đúng
hay sai** — chưa có phép đo báo sai nào.

Đó là rủi ro đúng loại `CLAUDE.md` cảnh báo: *"tài liệu của anh thiếu mục X"* khi
mục X có thật là kiểu báo sai làm mất niềm tin nhanh nhất.

**Đề xuất:** giữ 0,1. Muốn cân nhắc 0,0 thì trước hết **người kiểm bảng dưới** — đó
sẽ là **phép đo báo sai đầu tiên** của dự án.

## 6. Bảng kiểm báo sai — 38 cặp mới xuất hiện ở t=0,0

Mở từng tài liệu, tìm mục quy tắc hỏi. **Có** = tài liệu thật sự thiếu (công cụ
đúng). **Không** = mục ấy có (công cụ báo sai). Ưu tiên các dòng có số lượt lớn.

| # | Hồ sơ | Mã | Quy tắc hỏi gì | Số lượt | Tài liệu THẬT SỰ thiếu? |
|---|---|---|---|---:|:---:|
| 1 | cap bo sung VTracking 2.0.1 14 | `EVD-17` | Phải có mô tả chi tiết từng phân hệ | 1 | ☐ có ☐ không |
| 2 | cap bo sung VTracking 2.0.1 14 | `EVD-18` | Phải nêu công nghệ sử dụng của từng phân hệ | 1 | ☐ có ☐ không |
| 3 | cap bo sung VTracking 2.0.1 14 | `EVD-19` | Phải có mô hình logic của từng phân hệ | 2 | ☐ có ☐ không |
| 4 | cap bo sung VTracking 2.0.1 14 | `EVD-21` | Phải nêu lưu lượng dữ liệu mỗi request | 1 | ☐ có ☐ không |
| 5 | cap bo sung VTracking 2.0.1 14 | `STO-17` | Phải nêu loại lưu trữ sử dụng — Block, Object, File local hay File NAS | 1 | ☐ có ☐ không |
| 6 | cap bo sung campaign 2.0 8964 | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 1 | ☐ có ☐ không |
| 7 | cap bo sung campaign 2.0 8964 | `EVD-21` | Phải nêu lưu lượng dữ liệu mỗi request | 1 | ☐ có ☐ không |
| 8 | cap bo sung campaign 2.0 8964 | `EVD-22` | Phải có bảng tổng hợp đề xuất cấu hình cho từng phân hệ | 1 | ☐ có ☐ không |
| 9 | cap moi APIGW-Meta_2024 18927 | `STO-17` | Phải nêu loại lưu trữ sử dụng — Block, Object, File local hay File NAS | 1 | ☐ có ☐ không |
| 10 | cap moi APIGee Mini App 64015 | `EVD-18` | Phải nêu công nghệ sử dụng của từng phân hệ | 1 | ☐ có ☐ không |
| 11 | cap moi BCCS3_thị_trường_Lào 3 | `ARC-15` | Phải nêu nguồn request — từ nội bộ hay từ bên ngoài | 2 | ☐ có ☐ không |
| 12 | cap moi BCCS3_thị_trường_Lào 3 | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 3 | ☐ có ☐ không |
| 13 | cap moi BCCS3_thị_trường_Lào 3 | `EVD-18` | Phải nêu công nghệ sử dụng của từng phân hệ | 3 | ☐ có ☐ không |
| 14 | cap moi BCCS3_thị_trường_Lào 3 | `EVD-21` | Phải nêu lưu lượng dữ liệu mỗi request | 2 | ☐ có ☐ không |
| 15 | cap moi BCCS3_thị_trường_Lào 3 | `EVD-22` | Phải có bảng tổng hợp đề xuất cấu hình cho từng phân hệ | 2 | ☐ có ☐ không |
| 16 | cap moi BCCS3_thị_trường_Lào 3 | `PRC-10` | Phải nêu thời gian cam kết triển khai và đổ tải | 1 | ☐ có ☐ không |
| 17 | cap moi BCCS3_thị_trường_Lào 3 | `PRC-11` | Phải nêu mục đích sizing — định cỡ mới hay bổ sung cho hệ đang chạy | 1 | ☐ có ☐ không |
| 18 | cap moi BCCS3_thị_trường_Lào 3 | `STO-17` | Phải nêu loại lưu trữ sử dụng — Block, Object, File local hay File NAS | 3 | ☐ có ☐ không |
| 19 | cap moi FMRA_Sizing_server_Bac | `ARC-15` | Phải nêu nguồn request — từ nội bộ hay từ bên ngoài | 3 | ☐ có ☐ không |
| 20 | cap moi FMRA_Sizing_server_Bac | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 3 | ☐ có ☐ không |
| 21 | cap moi FMRA_Sizing_server_Bac | `EVD-18` | Phải nêu công nghệ sử dụng của từng phân hệ | 1 | ☐ có ☐ không |
| 22 | cap moi FMRA_Sizing_server_Bac | `EVD-21` | Phải nêu lưu lượng dữ liệu mỗi request | 3 | ☐ có ☐ không |
| 23 | cap moi FMRA_Sizing_server_Bac | `EVD-22` | Phải có bảng tổng hợp đề xuất cấu hình cho từng phân hệ | 1 | ☐ có ☐ không |
| 24 | cap moi FMRA_Sizing_server_Bac | `STO-17` | Phải nêu loại lưu trữ sử dụng — Block, Object, File local hay File NAS | 4 | ☐ có ☐ không |
| 25 | cap moi GSCG CSKH_bosung2022 2 | `EVD-20` | Phải có mô hình vật lý của từng phân hệ | 1 | ☐ có ☐ không |
| 26 | cap moi MySign 10371 | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 1 | ☐ có ☐ không |
| 27 | cap moi MySign 10371 | `EVD-22` | Phải có bảng tổng hợp đề xuất cấu hình cho từng phân hệ | 1 | ☐ có ☐ không |
| 28 | cap moi PBH 4.0 20043 | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 1 | ☐ có ☐ không |
| 29 | cap moi PBH 4.0 20043 | `EVD-17` | Phải có mô tả chi tiết từng phân hệ | 1 | ☐ có ☐ không |
| 30 | cap moi PBH 4.0 20043 | `EVD-22` | Phải có bảng tổng hợp đề xuất cấu hình cho từng phân hệ | 1 | ☐ có ☐ không |
| 31 | cap moi PBH 4.0 20043 | `PRC-09` | Phải nêu đầu mối, đơn vị phát triển và đơn vị định cỡ | 1 | ☐ có ☐ không |
| 32 | cap moi PNM 57012 | `ARC-16` | Phải nêu giao thức của request và port sử dụng | 1 | ☐ có ☐ không |
| 33 | cap moi PNM 57012 | `EVD-17` | Phải có mô tả chi tiết từng phân hệ | 1 | ☐ có ☐ không |
| 34 | cap moi PNM 57012 | `EVD-19` | Phải có mô hình logic của từng phân hệ | 1 | ☐ có ☐ không |
| 35 | cap moi PNM 57012 | `EVD-21` | Phải nêu lưu lượng dữ liệu mỗi request | 1 | ☐ có ☐ không |
| 36 | cap moi hethong Vtag | `ARC-15` | Phải nêu nguồn request — từ nội bộ hay từ bên ngoài | 1 | ☐ có ☐ không |
| 37 | cap moi hethong Vtag | `EVD-19` | Phải có mô hình logic của từng phân hệ | 2 | ☐ có ☐ không |
| 38 | cap moi hethong Vtag | `STO-17` | Phải nêu loại lưu trữ sử dụng — Block, Object, File local hay File NAS | 1 | ☐ có ☐ không |

Kiểm hết ~45–60 phút. Kiểm 10 dòng đầu có số lượt lớn nhất đã đủ để biết t=0,0
đang thêm tín hiệu hay thêm nhiễu.

## 7. Việc tiếp theo

| # | Việc | Ai | Tốn |
|---|---|---|---|
| 1 | `git pull`, `git status`, mở thử `data/phan_nhom_tham_dinh.json` | máy nội bộ | 2 phút |
| 2 | Một lượt dev t=0,1, đệm TẮT — hoàn tất nghiệm thu theo tiêu chí đã chốt | máy nội bộ | ~2–4 giờ |
| 3 | Kiểm bảng mục 6 (ít nhất 10 dòng) — phép đo báo sai đầu tiên | người | 15–60 phút |

---

## 8. KẾT LUẬN CUỐI — lượt E (2026-09-11 15:06, nhiệt độ 0,1): **ĐẠT**

Mục 2 đã ghi TRƯỚC khi có số: *"thêm MỘT lượt nhiệt độ 0,1, đệm TẮT"* để hoàn tất
theo đúng tiêu chí. Lượt E là lượt đó.

| Chỉ số | Dải chốt trước | A | C | E |
|---|---|---:|---:|---:|
| Trúng | 265–281 | 273 ✓ | 270 ✓ | 273 ✓ |
| Recall bộ quy tắc | 85–90% | 87,5% ✓ | 86,5% ✓ | 87,5% ✓ |
| Thực chất | 28–40 | 34 ✓ | 32 ✓ | 34 ✓ |
| Nhóm quyết định | 3–7 | 5 ✓ | 5 ✓ | 6 ✓ |
| Hồ sơ chạy / lỗi | 13/14 · 0 | ✓ | ✓ | ✓ |
| QĐ lệch ≤ 2 nhãn | | **5 · 5 · 6 → lệch 1 ✓** | | |

Biên độ từng cặp (số nhãn đổi kết quả trên 312): A↔C **5** · A↔E **6** · C↔E **8**.

### Câu công bố

> *Trên tập dev 14 hồ sơ, nhiệt độ 0,1, xếp nhóm theo phán quyết thẩm định
> 2026-09-09, ba lượt độc lập:*
> - *recall so với bộ quy tắc **86,5–87,5%**; so với mọi yêu cầu 85,2–86,1%;*
> - *recall theo loại nhãn 69,3–70,7%;*
> - ***nhóm nhận xét đòi tính/so số: 5–6/71 = 7,0–8,5%;***
> - ***trong đó phần công cụ thật sự tính lại được con số: 1/71 = 1,4%*** *(cả ba lượt).*

Luôn kèm ba hạn chế ở đầu mọi báo cáo eval: recall hào phóng vì `rule_ref` dư mã ·
chưa đo được báo sai · nhãn chưa qua kiểm định độc lập.

### Ba điều phải nói kèm kết luận này

1. **Lượt A bật đệm một phần** (475 lượt, từ lượt `--chi 3` trên 3 hồ sơ). A↔C (5)
   xấp xỉ A↔E (6), nên A hành xử như một mẫu độc lập — nhưng không hoàn toàn.
2. **Không xác nhận được từ báo cáo rằng lượt E đã tắt đệm** — vì một lỗi của tôi làm
   mất dòng đệm và dòng thời gian khỏi báo cáo (mục 9). Bằng chứng gián tiếp: nếu đệm
   bật ở t=0,1, E sẽ phát lại câu trả lời đã lưu của A và lệch gần 0; thực tế A↔E lệch
   6, ngang A↔C.
3. **Lượt D (t=0,0) bị loại khỏi phép nghiệm thu** vì không phải phép lặp — không
   phải vì số của nó xấu. Nó vẫn là dữ liệu cho câu hỏi nhiệt độ (mục 5).

## 9. Lỗi thứ ba của tôi trong cùng một chuỗi

Bản vá *"gộp chứ đừng ghi đè cảnh báo"* (mục 4) đổi `ev.canh_bao = canh_bao` thành
`ev.canh_bao = canh_bao + ev.canh_bao`. Dòng mới tạo **một danh sách khác**, nên mọi
dòng `run_eval` thêm SAU đó — thời gian, đệm lời gọi, cảnh báo diễn tập — rơi vào
danh sách cũ và biến mất.

Tôi sửa một lỗi nuốt cảnh báo bằng cách tạo ra một lỗi nuốt cảnh báo khác. 552 test
khi ấy vẫn xanh, vì bài diễn tập chạy trọn `run_eval` thật nhưng không ai kiểm dòng
thời gian. Đã sửa, và đã chứng minh test hồi quy mới **đỏ khi gỡ bản vá**.
