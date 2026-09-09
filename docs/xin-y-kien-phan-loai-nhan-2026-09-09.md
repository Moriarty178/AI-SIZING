# Xin ý kiến: xếp nhóm nhận xét PNX để chấm điểm công cụ

> Gửi: đơn vị thẩm định · Ngày: 2026-09-09
> Người hỏi: nhóm phát triển Sizing Copilot
> **Cần chốt: 29 nhận xét dưới đây thuộc nhóm nào.** Không cần đọc mã nguồn.

---

## 1. Vì sao phải hỏi

Chúng tôi đo công cụ bằng cách so kết quả của nó với **475 nhận xét PNX thật** của
các anh/chị. Nhưng không phải nhận xét nào cũng cùng loại yêu cầu, nên chúng được
chia nhóm trước khi chấm:

| Nhóm | Yêu cầu là gì | Công cụ trả lời đúng bằng cách nào |
|---|---|---|
| **A — chưa nêu / thiếu** | tài liệu chưa có thông tin | báo *"thiếu mục này"* |
| **B — đòi trình bày** | có thông tin nhưng chưa lập bảng / chưa ghi rõ | báo *"cần trình bày rõ"* |
| **C — đòi TÍNH hoặc SO số** | con số trong tài liệu sai, hoặc phải tính lại | **tính lại bằng máy rồi chỉ ra chỗ lệch** |

**Nhóm C là nhóm quyết định.** Nhóm A gần như cho không: một công cụ chỉ biết nói
*"tôi không tìm thấy"* cũng đạt ~94% ở nhóm A mà chẳng hiểu gì. Chỉ nhóm C mới phân
biệt được công cụ chạy được với công cụ nói bừa — nên đó là con số chúng tôi báo cáo.

Hiện trên tập đo (317 nhận xét): **nhóm A 179 · nhóm B 29 · nhóm C 87** · 22 nhận xét
quá ngắn không đoán được, đã bỏ ra ngoài.

**Vấn đề:** trong 87 nhận xét nhóm C, chúng tôi thấy **29 nhận xét không đòi tính
toán gì cả** — chúng đòi một thủ tục, một tài liệu đính kèm, một cam kết, hoặc một
lời giải thích. Công cụ không thể "tính" ra chúng, nên đang bị chấm trượt ở những
chỗ mà không phép tính nào thoả mãn được.

Việc xếp lại nhóm **làm điểm của công cụ đẹp lên**. Chính vì vậy chúng tôi không tự
quyết, mà xin các anh/chị chốt.

---

## 2. Ba câu hỏi, tương ứng ba tập nhận xét

### Câu 1 — 13 nhận xét đòi THỦ TỤC. Có nên tách khỏi nhóm C không?

Không có phép tính nào trả lời được những câu này.

**Đòi cam kết / phê duyệt (4)** — cùng một câu, lặp ở 4 hồ sơ (c360, APIGee, FMRA, PNM):
> *"Bắt buộc phải có thời gian cam kết hoàn thành triển khai và đổ tải thật (thêm 1
> dòng vào phần đầu của sizing), có sở cứ từ KD hoặc BGĐ"*

**Đòi tài liệu đính kèm (4)** — c360, APIGee, FMRA, campaign:
> *"Ký sizing phải đính kèm thêm file checklist (đính kèm)"* (3 hồ sơ)
> *"Trình bày rõ p/án thay thế cụm tài nguyên IDC, Datalake ntn (toàn bộ hay 1 phần) qua mail"*

**Đòi giải thích lựa chọn thiết kế (5)**:
> *"Tài nguyên con này đã có trong QHDC nào chưa ạ"* (APIGee)
> *"Sở cứ cần sử dụng SSD"* (campaign)
> *"Tại sao mô hình Kafka là 5 instances"* (campaign)
> *"Các máy chủ cần nhiều ram có thể chia nhỏ ra để ảo hóa được không ?"* (BCCS3 Lào)
> *"Tổng tài nguyên data, log, backup giữ nguyên không chia ra à ?"* (MySign)

☐ **Tách ra nhóm D (thủ tục)** — công cụ chỉ cần nhắc *"hồ sơ còn thiếu thủ tục này"*
☐ **Giữ trong nhóm C** — các anh/chị muốn công cụ trả lời được cả những câu này
☐ Ý kiến khác: ......................................................

---

### Câu 2 — 9 nhận xét ĐÒI SỞ CỨ. Thế nào là công cụ trả lời đúng?

Đây là nhóm chúng tôi phân vân nhất. Các anh/chị đang đòi **bằng chứng cho một con
số**, chứ không đòi tính lại con số đó.

> *"Sở cứ tải hệ thống cho 166 CCU"* (c360)
> *"Chưa thấy sở cứ cho Dung lượng mẫu thử GB: 18"* (PBH 4.0)
> *"Tính toán số liệu cụ thể làm sở cứ đặc biệt băng thông cần kết nối với các hệ thống khác"* (PBH 4.0)
> *"Bảng tổng hợp dung lượng đầu vào từ các nguồn: Tính toán thông lượng tính toán số liệu cụ thể theo hệ thống test kèm sở cứ"* (PBH 4.0)
> *"Module Speech processing không rõ giá trị hệ thống hiện tại để định cỡ, cần sở cứ"* (GSCG)
> *"Trang 27: sở cứ đây là ảnh chụp cho 150 t/bị trong 1.5 tháng ? Sở cứ lưu 24 tháng"* (VTracking)
> *"Không hiểu tại sao lại có dung lượng 100GB, nếu dựa trên máy chủ có sẵn thì **cần chụp ảnh dung lượng**"* (Vtag)
> *"Không hiểu cơ sở 2000 thiết bị?"* (Vtag)
> *"Tính TPS, dung lượng cho GPS theo từng khung giờ cao điểm và thấp điểm. Sao dung lượng này lại chỉ cần lưu trữ trong 1 ngày ?"* (VTracking)

Công cụ nay **đọc được ảnh chụp màn hình** trong tài liệu và đối chiếu số trong ảnh
với số trong bảng. Ví dụ thật ở hồ sơ Vtag: ảnh `kubectl top nodes` cho *"node4 —
CPU 20%, RAM 66%"*, và bảng định cỡ khai đúng *"Worker — 20% / 66%"* — công cụ nối
được hai chỗ đó với nhau.

☐ **Công cụ chỉ ra được ảnh/bảng làm sở cứ ⇒ tính là ĐẠT** cho nhóm này
☐ **Phải tính lại con số mới tính là đạt** — chỉ trỏ sở cứ là chưa đủ
☐ **Tách thành nhóm riêng**, chấm bằng thước đo khác
☐ Ý kiến khác: ......................................................

---

### Câu 3 — 7 nhận xét chúng tôi cho là VẪN THUỘC nhóm C. Xin xác nhận.

Những câu này máy kiểm được bằng số học thuần tuý, nên chúng tôi **đề nghị giữ
nguyên** trong nhóm C — tức công cụ đáng bị chấm trượt nếu không bắt được.

> *"CPU ở trên lúc thì 109.375 lúc thì 175 mà ở dưới này là 103.975 xem lại số liệu và sở cứ"* (PBH 4.0)
> *"Xem lại giá trị Cint đưa ra không đồng nhất trong toàn văn bản (226; 12.6; 25.1;…) rất khó để thẩm định"* (Vtag)
> *"Khối lượng log trong 1 tháng (có sai số và KPI) = 20,2\*30\*1.1/0.8 = 833,25 GB. không thấy dùng vào việc gì ?"* (APIGW-Meta)
> *"2 năm sao chỉ \*6 ?"* (MySign)
> *"Sửa lại thông tin cpu, cint 2017, link tham chiếu (trang 7)"* (campaign)
> *"Sửa lại thông tin cpu, cint 2017, link tham chiếu (trang 9)"* (campaign)
> *"Link tham chiếu cpu đang không đúng"* (Data Security VTT)

☐ **Đồng ý giữ trong nhóm C**
☐ Có câu không thuộc nhóm C: ........................................

---

## 3. Hệ quả lên con số, nói trước cho minh bạch

Nhóm C hiện có **87 nhận xét**. Tuỳ các anh/chị chốt:

| Phương án | Nhóm C còn | Ảnh hưởng |
|---|---:|---|
| Giữ nguyên | 87 | điểm công cụ **thấp** — gồm cả những câu máy không thể tính |
| Tách 13 câu thủ tục (Câu 1) | 74 | mẫu số giảm 15% |
| Tách thêm 9 câu sở cứ (Câu 2) | 65 | mẫu số giảm 25% |

Chúng tôi **không đề nghị phương án nào**. Điểm của công cụ đẹp hay xấu không quan
trọng bằng việc nó đo đúng thứ các anh/chị thật sự cần.

---

## 4. Một lỗi chúng tôi tự tìm ra và đã sửa — xin khai báo

Bốn nhận xét của hồ sơ GSCG viết **"Bổ  sung"** với *hai dấu cách* (chép từ Word).
Chương trình dò chữ "bổ sung" nên trượt, và cả bốn bị xếp nhầm từ nhóm A xuống
nhóm C.

Đã sửa (gộp khoảng trắng trước khi dò). Việc sửa này **làm điểm công cụ đẹp lên**,
nên chúng tôi nêu ra đây thay vì lặng lẽ sửa. Đây là lỗi so khớp chữ, không phải
thay đổi cách chấm.

---

## 5. Sau khi có ý kiến

Chúng tôi sẽ cập nhật cách xếp nhóm đúng như các anh/chị chốt, chạy lại phép đo, và
báo cáo con số kèm ghi rõ đã xếp nhóm theo quyết định nào — để lần sau đọc lại vẫn
biết con số dựa trên cơ sở gì.

Xin cảm ơn các anh/chị.
