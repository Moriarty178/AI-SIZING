# Nghiệm thu lượt đo eval (1.13) — chạy trên máy nội bộ

> Lập 2026-09-09. **Chạy theo đúng thứ tự.** Bước 1–2 tốn vài phút và quyết định
> bước 3–4 tốn 7 giờ hay 2 giờ — nên đừng nhảy thẳng xuống bước 3.

## Thế nào là ĐẠT

Lượt đo được nghiệm thu khi nói được **một câu** có đủ bốn phần:

> *"Trên tập dev 14 hồ sơ, cách xếp nhóm nhãn theo phán quyết 2026-09-09, công cụ
> đạt recall nhóm quyết định X% ± Y, đo bằng lượt chạy `<file báo cáo>`."*

- **X** ← bước 3 (lượt dev đầy đủ)
- **± Y** ← bước 4 (biên độ giữa các lượt)
- **cách xếp nhóm** ← đã chốt, không còn phải chờ ai
- **chấm lại được** ← mỗi lượt nay ghi kèm `.json` chi tiết từng nhãn

Thiếu **Y** thì KHÔNG được trích **X** ra ngoài: `PLAN.md` đã chốt điều này, và
mục 2.3 ngày 09-09 đã tái xác nhận model không cho kết quả lặp lại dù nhiệt độ 0.

---

## Bước 1 — miễn phí, 0 lượt gọi model (~2 phút)

```powershell
git pull
py -m pytest -q                      # mong đợi: 481 passed
py scripts/khoi_dong_thu.py          # mong đợi: mã thoát 0
py -m eval.run_eval --uoc-tinh       # số lượt gọi dự kiến cho cả tập dev
```

Gửi lại: dòng cuối của `pytest`, khối tự kiểm, và bảng ước lượng.

**Vì sao có bước này:** dự án đã ba lần chạy model bằng mã CŨ vì `git pull` chưa
ăn, mỗi lần đốt vài phút và cho kết luận sai (`src/version.py`). Ba lệnh trên
loại hẳn khả năng đó trước khi tiêu giờ.

---

## Bước 2 — rẻ, nhưng quyết định mọi thứ (~3–5 phút gọi model)

```powershell
py scripts/do_song_song.py --muc 6,12,24
```

Gửi lại **toàn bộ bảng**. Rồi DỪNG, chờ chốt mức song song.

Script bắn **một lời gọi thử** trước, và dừng ngay nếu nó hỏng — lượt 09-09 đốt
36 lời gọi ở ba mức rồi mới lộ ra là ngân sách token quá nhỏ. Ngân sách mặc định
nay bám `DEFAULT_MAX_TOKENS` (4000) của chính dự án, bằng mức dùng thật.

Nếu thấy `PhanHoiRong[length]`: đó **không phải lỗi tải**, mà là model tiêu hết
ngân sách token vào phần suy luận rồi trả `content` rỗng. Chữa bằng
`--max-tokens` lớn hơn hoặc `--model` khác, đừng đi chỉnh mức song song.

**Vì sao phải dừng ở đây:** một tài liệu tốn ~239 lượt gọi. Ở song song 6 (mức đo
được hôm 09-09) đó là ~33 phút/tài liệu ⟹ **7 giờ cho lượt dev đầy đủ**. Thời
gian gần như tỉ lệ nghịch với mức song song, nên nếu gateway chịu được 24 thì
lượt ấy còn **~2 giờ**. Đo 5 phút để có thể tiết kiệm 5 giờ.

Script tự tắt đệm và dùng nội dung ngẫu nhiên mỗi lời gọi — nếu không, mức thứ
hai trở đi sẽ lấy trong đệm và cho một con số đẹp vô nghĩa.

⚠️ Mức nào bắt đầu báo lỗi thì **đừng dùng mức đó** cho lượt chạy thật, kể cả khi
thông lượng của nó cao hơn.

---

## Bước 3 — con số công bố được (7 giờ ở song song 6; ít hơn nếu bước 2 cho phép)

```powershell
Remove-Item Env:\SIZING_COPILOT_KHONG_CACHE -ErrorAction SilentlyContinue   # đệm BẬT
py -m eval.run_eval --tap dev --song-song <mức chốt ở bước 2>
```

Gửi lại: file `eval/reports/eval-dev-<ngày>.md` **và** file `.json` cùng tên.

Ba điều cố ý trong lệnh này:

- **KHÔNG có `--doc-anh`.** Đã kiểm: finding từ ảnh chỉ mang `computed_evidence`,
  không mang `rule_ref`, nên không khớp nhãn nào và **recall không đổi**. Bật nó
  chỉ thêm ~58 lượt gọi mỗi tài liệu (≈ +27% thời gian) để đổi lấy con số y hệt.
- **Đệm BẬT.** Lượt này chạy một lần; đệm chỉ giúp nếu phải chạy lại dở chừng
  bằng `--tiep-tuc`.
- **Cả 14 hồ sơ**, kể cả hồ sơ không có `.docx` — bỏ chúng ra khỏi mẫu số sẽ làm
  recall đẹp lên giả tạo.

Nếu đứt giữa chừng: `py -m eval.run_eval --tap dev --tiep-tuc --song-song <mức>`.

---

## Bước 4 — biên độ (3 lượt, mỗi lượt ~1,5 giờ ở song song 6)

```powershell
$env:SIZING_COPILOT_KHONG_CACHE = "1"      # đệm TẮT — bắt buộc
py -m eval.run_eval --tap dev --ho-so "campaign,VTracking,APIGee" --song-song <mức>
py -m eval.run_eval --tap dev --ho-so "campaign,VTracking,APIGee" --song-song <mức>
py -m eval.run_eval --tap dev --ho-so "campaign,VTracking,APIGee" --song-song <mức>
Remove-Item Env:\SIZING_COPILOT_KHONG_CACHE
```

Gửi lại: ba file `.md` (hoặc chỉ ba bảng đầu của chúng).

**Đệm phải TẮT.** Bật đệm thì lượt 2 và 3 lấy nguyên kết quả lượt 1 và ra con số
giống hệt — đo được đúng con số 0, tức không đo gì cả.

Ba hồ sơ này chính là ba hồ sơ của lượt `--chi 3` ngày 09-09, nên còn so được với
nền cũ (87,1% chính · 14,5% sàn · 62,1% theo loại · 2/17 nhóm quyết định).

---

## Bước 5 — chấm lại, miễn phí

Không cần chạy gì. Phán quyết 2026-09-09 đổi mẫu số nhóm quyết định **17 → 11**
cho ba hồ sơ trên, và **87 → 74** cho cả tập dev. Từ nay mỗi lượt chạy ghi kèm
`.json` chi tiết từng nhãn, nên mọi thay đổi cách xếp nhóm về sau chấm lại trong
vài giây thay vì 7 giờ.

---

## Tóm tắt chi phí

| Bước | Máy nội bộ | Trả lời câu gì |
|---|---:|---|
| 1 | ~2 phút, 0 lượt gọi | mã đúng bản, image chạy được |
| 2 | ~5 phút | song song bao nhiêu ⟹ bước 3–4 tốn bao lâu |
| 3 | 2–7 giờ | **X** — recall công bố được |
| 4 | 3 × (0,5–1,5 giờ) | **± Y** — có được phép trích X không |
| | **≈ 3,5–11,5 giờ** | |

Khoảng dao động rộng vì nó phụ thuộc **bước 2**. Đó chính là lý do bước 2 đứng
trước.
