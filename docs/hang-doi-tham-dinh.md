# Hàng đợi thẩm định — xem, huỷ, chạy (GĐ 6, mục 6.6 — số mục tạm)

> Đọc cùng `CLAUDE.md` và `docs/tich-hop-fe-be.md`. Viết 2026-09-23.
> Số mục **6.6 là tạm**: bản PLAN.md cập nhật trên máy nội bộ chưa push lên, nên
> chưa biết GĐ 6 hiện đã tới số mấy. Ghép vào PLAN.md sau khi kéo được bản đó.

## 0. Yêu cầu

Trong phần **"Thẩm định sizing"** thêm **"Xem danh sách hàng đợi"**: bảng gồm
Job_ID · tên file · trạng thái · action, xếp theo thời điểm nộp (đúng thứ tự
hàng đợi). Action: **Huỷ** với việc đang chạy, **Run** với việc đang chờ.

- Huỷ việc đang chạy → hỏi *"Có muốn chạy sizing (job_id) tiếp theo không?"* —
  Có: chạy việc kế · Không: mọi việc giữ nguyên trạng thái chờ, mỗi dòng chờ có
  nút Run để chạy tay.
- Nộp sizing mới khi một sizing khác chưa xong → hỏi *"Có muốn dừng chạy sizing
  (job_id) để chạy sizing mới không?"* — Có: chạy sizing mới · Không: việc đang
  chạy chạy tiếp, sizing mới vào hàng chờ.

**Ba câu người dùng chốt 2026-09-23:**

1. **Mỗi người chỉ thấy việc của mình.** Admin (`admin1`/`admin2`) thấy tất.
2. Bấm "Có" để dừng việc đang chạy thì việc bị dừng **bị huỷ hẳn** (không quay
   lại hàng chờ; muốn chạy lại thì nộp lại).
3. **Run** trên một việc đang chờ, khi đang có việc khác chạy = **dừng việc đang
   chạy, chạy việc này** (hỏi xác nhận như mục trên).

**Không đổi:** pipeline C1–C7, `rules.yaml`, lược đồ CSDL Copilot. Việc này nằm ở
lớp hàng đợi (`src/cong_viec.py`), API và FE.

---

## 1. Hàng đợi hôm nay — đo từ code, không phỏng đoán

| Sự thật | Chỗ | Hệ quả cho tính năng |
|---|---|---|
| **Một** luồng chạy cho **mọi** người dùng, FIFO, tự lấy việc kế | `BoChay`, `so_viec_song_song=1` | Hàng đợi là của chung. Chạy hai việc song song chậm hơn chạy lần lượt (đo 2026-09-09) — KHÔNG đổi con số này. |
| **Chưa có khái niệm huỷ** | trạng thái: `cho · dang_chay · xong · hong · gian_doan` | Phải thêm `da_huy`. |
| `DELETE /result/{ma}` trên việc đang chạy chỉ xoá bản ghi — **luồng vẫn chạy tiếp tới hết** rồi ghi vào một việc không còn tồn tại | `KhoCongViec.xoa` | Lỗi có sẵn. Tính năng huỷ phải sửa luôn. |
| Khởi động lại container → mọi việc `cho` và `dang_chay` thành `gian_doan` ("hãy nộp lại") | `KhoCongViec._nap` | Hôm nay việc chờ chỉ đợi vài chục phút. Có nút "Không" (tạm giữ vô thời hạn) thì mất việc chờ vì restart sẽ thành chuyện thường. |
| `GET /jobs` trả việc của **tất cả** mọi người, kèm tên file | `api/main.py` | Qua nginx ai cũng mở được `/copilot/jobs` — đi ngược thẳng câu chốt số 1. |

---

## 2. Luật hoạt động

### 2.1 Chốt trực tiếp

- Bảng chỉ hiện việc của người đang đăng nhập; Admin thấy mọi việc, kèm cột
  **Người nộp**.
- Việc bị dừng để nhường chỗ → `da_huy`, ra khỏi hàng.
- Run khi đang có việc chạy → xác nhận → dừng việc đó (`da_huy`), chạy việc này.

### 2.2 Suy ra từ ba câu trên — ⚠️ SỬA NẾU SAI

Ba câu trả lời đúng từng câu, nhưng ghép lại có một chỗ chúng không tự nói: **hàng
đợi của chung, mà mỗi người chỉ thấy phần của mình.** Nếu vẫn cho người A "dừng
việc đang chạy" khi việc đó là của người B, thì A huỷ hẳn (câu 2) lượt thẩm định
15 phút của B mà không nhìn thấy nó là gì, và B không được hỏi câu nào. Nên:

1. **Chỉ dừng được việc của chính mình** (Admin: mọi việc).
   - Nộp sizing mới khi việc **của mình** đang chạy → hỏi "dừng (job_id)?" như yêu cầu.
   - Nộp khi việc **của người khác** đang chạy → KHÔNG hỏi, sizing mới vào hàng chờ.
2. **"Tạm giữ" là của từng người, không phải của cả hàng.** A huỷ việc đang chạy của
   A rồi chọn "Không" → chỉ các việc chờ của **A** bị giữ lại; việc của B, C vẫn
   chạy đúng lượt. Nếu không, một câu trả lời của A làm đứng hàng của cả đơn vị.
3. **Chỉ hỏi "chạy tiếp theo?" khi người đó còn việc chờ.** "Việc tiếp theo" là việc
   chờ kế tiếp **của chính họ**.
4. **Run trên việc đang giữ, khi việc của người khác đang chạy** → không dừng được
   việc kia (luật 1), nên Run = **thả việc này về đúng chỗ cũ trong hàng** (xếp theo
   giờ nộp). Nhãn nút đổi thành "Xếp lại vào hàng".
5. **Người dùng vẫn cần biết vì sao mình phải chờ**, mà không được thấy việc người
   khác → dòng chờ hiện **"Chờ — còn N sizing phía trước"** (chỉ con số, không tên
   file, không người nộp).

### 2.3 Bảng tình huống

| Tình huống | Hành vi |
|---|---|
| Nộp, không có gì đang chạy | Chạy ngay |
| Nộp, việc **của mình** đang chạy | Hỏi "dừng (job_id) để chạy sizing mới?" · Có → việc cũ `da_huy`, việc mới chạy · Không → việc mới cuối hàng |
| Nộp, việc **người khác** đang chạy | Vào cuối hàng, không hỏi |
| Huỷ việc đang chạy của mình, **còn** việc chờ | Máy chủ giữ ngay các việc chờ của mình → hỏi "chạy (job_id kế) tiếp?" · Có → thả ra · Không → giữ, mỗi dòng có Run |
| Huỷ việc đang chạy của mình, **không còn** việc chờ | Huỷ, không hỏi gì |
| Run, không có gì chạy | Chạy ngay |
| Run, việc **của mình** đang chạy | Hỏi xác nhận → việc đang chạy `da_huy`, việc này chạy |
| Run, việc **người khác** đang chạy | "Xếp lại vào hàng" — thả về đúng chỗ theo giờ nộp |
| Admin | Như trên, nhưng dừng/huỷ được việc của bất kỳ ai; xác nhận ghi rõ tên người nộp |

**Vì sao máy chủ giữ hàng NGAY khi huỷ, không đợi người dùng trả lời:** câu hỏi
hiện trên trình duyệt. Nếu máy chủ chờ câu trả lời mới quyết, thì trong lúc người
dùng còn đọc, luồng chạy đã lấy việc kế và bắt đầu gọi model — "Không" lúc đó phải
huỷ một việc vừa chạy. Người dùng đóng tab thì không bao giờ có câu trả lời. Giữ
trước là mặc định an toàn: không đốt 16 phút model cho thứ người dùng có thể không
muốn.

---

## 3. Huỷ việc đang chạy: làm được tới đâu

**Không huỷ tức thì được.** Lúc bấm Huỷ, pipeline đang ở giữa ~12 lượt gọi model
song song; Python không giết được luồng, và một lượt gọi HTTP đang bay thì phải
chờ nó về. Chỉ có thể **xin dừng ở điểm kiểm kế tiếp**.

**Điểm kiểm:** mọi lượt gọi model của C3 và C5 trên đường chạy việc đều đi qua
`PhatLai.goi` (`src/llm/phat_lai.py`) — `BoChay` luôn truyền `phat_lai` vào. Thêm
MỘT phép kiểm ở đầu hàm đó: đã có yêu cầu huỷ thì ném `DaHuy` thay vì gọi model.

C2 (đọc ảnh) là đường gọi model DUY NHẤT không qua `PhatLai`, nhưng nó **mặc định
tắt** (`pipeline.chay(doc_anh=False)`) và `/review` không mở tuỳ chọn ấy — tức trên
đường chạy dịch vụ, `PhatLai.goi` phủ **mọi** lượt gọi model. Thêm một phép kiểm
trong callback tiến độ của `BoChay` làm lưới phụ cho giai đoạn không gọi model
(C1, C4, C7): các hàm `_bao` của C3/C5/C2 gọi thẳng callback, không bọc `try`, nên
ném ở đó là nổi lên được.

Vì sao chỗ này đủ, đã kiểm trong code:

- Lỗi model bị bắt **hẹp** — `except (ExtractionFailed, LLMError)` ở cả C3 lẫn C5.
  `DaHuy` không kế thừa hai lớp đó nên **không bị xuống cấp thành "không kiểm
  được"** (nếu bị nuốt, việc huỷ sẽ "xong" với một báo cáo rác — tệ hơn cả không huỷ).
- Hai vòng song song (`extractor.py:893`, `qualitative.py:321`) đều `f.result()`
  lại, nên `DaHuy` nổi lên tới `BoChay._lam`.
- Chỗ `except Exception` rộng DUY NHẤT trong `pipeline.py` bọc phần vân tay vùng,
  không bọc C3/C5.
- Các việc con đã nộp vào pool nhưng chưa chạy: mỗi cái vào `PhatLai.goi` là ném
  `DaHuy` ngay — cỡ micro-giây, không gọi model.

**Độ trễ huỷ = một lượt gọi model đang bay.** Trên model thật cỡ 15–40 giây, xấu
nhất bằng `timeout_s` (120 s). Giao diện phải có trạng thái **"Đang huỷ…"** —
im lặng 40 giây sau khi bấm là người dùng bấm tiếp.

> ⚠️ **Đây là chỗ DUY NHẤT chạm xuống dưới lớp hàng đợi** — `CLAUDE.md` bảo phải
> hỏi trước khi sửa pipeline. `src/llm/phat_lai.py` là tầng phát lại lời gọi model
> (5.3), không phải logic thẩm định: thêm một phép kiểm ở đầu `goi` **không đổi kết
> quả thẩm định nào** của một việc chạy tới cùng. Phương án không đụng nó là chỉ kiểm
> trong `tien_do` — nhưng khi ấy thoát khỏi vòng C3 thì `ThreadPoolExecutor` vẫn chạy
> hết ~118 việc con đã nộp, tức **huỷ mất gần như cả lượt chạy**. Duyệt kế hoạch này
> là đồng ý với thay đổi ấy.

---

## 4. Thiết kế

### 4.1 `CongViec` — một trạng thái và bốn trường mới

- Trạng thái `DA_HUY = "da_huy"`.
- `giu_lai: bool` — việc chờ đang bị giữ (luật 2.2-2). Luồng chạy bỏ qua nó.
- `yeu_cau_huy: bool` — đã bấm Huỷ, đang chờ điểm kiểm (giao diện: "Đang huỷ…").
- `huy_boi: str`, `huy_luc: float` — ai huỷ, lúc nào. Người bị Admin huỷ việc phải
  đọc được **ai** đã huỷ, không chỉ thấy chữ "Đã huỷ".

Chủ của việc = `danh_tinh.ten` đã có sẵn trên `CongViec`. FE phải gửi **username**
của Tool Sizing (duy nhất, `uk_users_username`), không phải tên hiển thị.

Tất cả đều có giá trị mặc định → file `.json` việc cũ nạp lại bình thường
(`_nap` đã lọc theo trường khai báo).

### 4.2 `BoChay`

- Hàng vẫn là `deque` theo giờ nộp. Luồng chạy lấy **việc đầu tiên còn `cho` và
  không `giu_lai`** — không còn `popleft()` mù.
- `huy(ma, danh_tinh)` — kiểm quyền; việc chờ → `da_huy` ngay; việc đang chạy →
  bật `yeu_cau_huy` + `threading.Event` của việc đó, và **giữ ngay** các việc chờ
  của cùng chủ. Trả về việc chờ kế tiếp của chủ (hoặc không có) để FE biết có
  phải hỏi "chạy tiếp?" hay không.
- `tha(chu)` — "Có": bỏ `giu_lai` trên các việc chờ của chủ.
- `chay(ma, danh_tinh, dung_viec_dang_chay: bool)` — theo bảng 2.3. Cần dừng việc
  đang chạy mà chưa có `dung_viec_dang_chay=True` → ném lỗi kèm việc đang chạy, để
  API trả 409 và FE hỏi xác nhận rồi gọi lại. Không tin FE đã hỏi.
- `_lam`: truyền `Event` vào `PhatLai`; bắt `DaHuy` → `da_huy` (không phải `hong`),
  **không** ghi báo cáo, không ghi hồ sơ CSDL, không lưu kho phát lại.
- `xoa` trên việc đang chạy: xin huỷ trước, không để luồng mồ côi.

### 4.3 API Copilot

| Lời gọi | Việc |
|---|---|
| `GET /hang-doi` | Việc của người gọi (Admin: tất), xếp theo giờ nộp, kèm `so_truoc` cho dòng chờ và `dang_chay_cua_minh` |
| `POST /hang-doi/{ma}/huy` | Huỷ. Trả `{trang_thai, tiep_theo}` |
| `POST /hang-doi/tiep-tuc` | "Có" — thả các việc đang giữ của người gọi |
| `POST /hang-doi/{ma}/chay` | Run. Body `{dung_viec_dang_chay}`. Chưa xác nhận mà cần dừng → **409** kèm việc sẽ bị dừng |
| `POST /review` | Thêm trường form `uu_tien` — "Có" ở câu hỏi mục 2 |

Quyền kiểm ở API bằng header danh tính (`tu_header`), **403** khi đụng việc của
người khác mà không phải Admin.

### 4.4 FE (trong phần "Thẩm định sizing" của 6.3)

> ⚠️ Phần 6.3 trên máy nội bộ **chưa push**; mục này viết theo mô tả, chỗ móc cụ
> thể chốt sau khi kéo được mã đó về.

- Khối **"Hàng đợi"**: bảng Job_ID · tên file · trạng thái · action; Admin thêm cột
  Người nộp. Tự làm mới vài giây một lần khi còn việc `cho`/`dang_chay`.
- Nộp file: gọi `GET /hang-doi` trước; `dang_chay_cua_minh` → hỏi câu mục 2 → gửi
  `uu_tien` theo câu trả lời. Máy chủ vẫn tự kiểm lại (việc có thể vừa xong giữa
  lúc hỏi và lúc nộp).
- Huỷ → "Đang huỷ…" → khi có `tiep_theo` thì hỏi "chạy (job_id) tiếp theo?".
- Run → nếu 409 thì hỏi xác nhận, gọi lại với `dung_viec_dang_chay: true`.

### 4.5 nginx — chặn `/copilot/jobs`

`GET /jobs` liệt kê việc của mọi người. Để nguyên thì câu chốt số 1 bị vượt bằng
cách gõ một địa chỉ. Chặn đường này ở `location` của nginx; `copilot-ui` gọi thẳng
`http://copilot:8000` trong mạng compose nên **không bị ảnh hưởng**.

> Nói thẳng: danh tính của Copilot là danh tính demo KHÔNG xác thực (5.0a) — ai
> tự dựng header được thì giả làm người khác được. "Chỉ thấy việc của mình" ở đây
> là **ranh giới lịch sự trong mạng nội bộ, không phải lớp bảo mật.** Muốn thật thì
> phải xác minh JWT của Tool Sizing ở nginx hoặc ở Copilot — việc riêng, chưa làm.

### 4.6 Khởi động lại container

Việc `cho` (kể cả đang giữ) được **xếp lại vào hàng** theo giờ nộp thay vì thành
`gian_doan` — tài liệu đã nộp vẫn nằm trên đĩa (`tai_lieu/{ma}/`). Việc
`dang_chay` vẫn thành `gian_doan` như cũ: nó chạy dở, không có gì để tiếp.

Lý do đổi: có nút "Không" thì việc chờ có thể nằm đó hàng giờ, và một lần
`docker compose up -d` sẽ âm thầm biến cả hàng thành "hãy nộp lại".

---

## 5. Tiêu chí nghiệm thu (đặt TRƯỚC khi code)

- **Q1** Bảng xếp đúng theo giờ nộp; người dùng thường chỉ thấy việc của mình;
  Admin thấy tất kèm người nộp; `/copilot/jobs` qua nginx bị chặn.
- **Q2** Huỷ việc đang chạy → trạng thái "Đang huỷ…" rồi `da_huy`; **KHÔNG có báo
  cáo, KHÔNG có dòng hồ sơ CSDL** cho việc đó. **Đo độ trễ huỷ** trên model thật.
- **Q3** Huỷ khi còn việc chờ: "Không" → việc chờ đứng yên, có nút Run; chờ 2 phút
  vẫn đứng yên. "Có" → việc kế chạy.
- **Q4** Nộp khi việc của mình đang chạy: "Có" → việc cũ `da_huy`, việc mới chạy;
  "Không" → việc cũ chạy tiếp, việc mới cuối hàng.
- **Q5** Hai người dùng: A không thấy việc của B; A nộp khi việc của B đang chạy thì
  **không bị hỏi** và việc của B không bị động tới; API trả **403** khi A cố huỷ
  việc của B.
- **Q6** Run khi việc người khác đang chạy → việc về đúng chỗ theo giờ nộp.
- **Q7** Khởi động lại container giữa lúc có việc chờ đang giữ → việc chờ vẫn là
  `cho`, vẫn giữ; việc đang chạy thành `gian_doan`.
- **Q8** Một việc chạy tới cùng cho **cùng số finding** trước và sau thay đổi — phép
  kiểm ở `PhatLai.goi` không được đổi kết quả thẩm định nào.

Q1, Q3–Q7 kiểm được ngay trên máy lập trình viên (model trỏ cổng đóng, việc chạy
~40 giây). Q2 phần **độ trễ** và Q8 cần model thật → máy nội bộ.

## 6. Thứ tự làm

1. `CongViec` + `BoChay` + `DaHuy` trong `PhatLai` — thuần Python, test offline với
   `ham_chay` giả chặn trên một `Event` (không cần model).
2. API + test.
3. nginx chặn `/jobs` + test ở `tests/test_dong_goi.py`.
4. FE — **sau khi kéo được mã 6.3 từ máy nội bộ.**
5. Nghiệm thu tại chỗ Q1, Q3–Q7; máy nội bộ Q2 + Q8.

## 7. Chưa làm — nêu ra để quyết sau

- **Huỷ một việc đang CHỜ.** Yêu cầu chỉ cho dòng chờ nút Run. Người nộp nhầm file
  sẽ muốn gỡ nó khỏi hàng; API `huy` làm được sẵn, chỉ là FE chưa có nút.
- **Giữ câu trả lời model của lượt bị huỷ** để lần nộp lại dùng lại (5.3). Hôm nay
  kho phát lại chỉ ghi khi việc xong; lượt huỷ ở phút 14 là mất trắng 14 phút.
- **Xác thực thật** cho `/copilot/` (mục 4.5).
