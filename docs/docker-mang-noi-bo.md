# Xây và chạy image trong mạng nội bộ Viettel

> Ghi 2026-09-09, từ ba lỗi gặp thật khi build trên máy nội bộ. Mỗi mục ghi
> **triệu chứng → nguyên nhân → cách xử lý**, để lần sau không ai phải dò lại.

Trên máy ngoài (laptop thường) không cần gì trong tài liệu này — `docker build .`
chạy thẳng.

---

## 1. Docker Desktop không kéo được image nền

**Triệu chứng.** `docker build` treo hoặc lỗi ở bước `FROM python:3.12-slim`.

**Nguyên nhân.** Docker Desktop để proxy ở chế độ `system`, mà chế độ ấy **không
đọc được file PAC** của Viettel. Kết quả: nó tưởng mình không có proxy.

**Xử lý.** Đặt proxy **thủ công** cho Docker Desktop (qua backend API bằng named
pipe hoặc trong Settings → Resources → Proxies):

    mode   = manual
    http   = 10.207.156.52:3128
    https  = 10.207.156.52:3128

Cấu hình này cho **daemon kéo image nền**. Nó KHÔNG tự chảy vào các bước `RUN`
bên trong build — phần đó xem mục 3.

---

## 2. `apt-get` trong build luôn hỏng

**Triệu chứng.** `Clearsigned file isn't valid, got 'NOSPLIT'`.

**Nguyên nhân.** Proxy trả về nội dung không phải file kho apt (thường là trang
chặn hoặc trang xác thực), nên chữ ký của kho không phân tích được.

**Xử lý: đừng cài gói hệ thống nào cả.** `Dockerfile` hiện **không có `apt-get`**
và phải giữ nguyên như vậy.

Thứ duy nhất từng cần `apt-get` là `git`, chỉ để đọc một chuỗi 7 ký tự cho phần
truy vết phiên bản. Nay không cần nữa:

- `Dockerfile` ghi commit ra `/app/.commit` lúc build (`--build-arg COMMIT=...`)
  và đặt cả biến `SIZING_COPILOT_COMMIT`;
- `src/version.py` đọc biến trước, rồi tới file, rồi mới thử `git`.

Báo cáo và `GET /health` vẫn truy vết được commit, mà image không cần gói nào.

⚠️ Nếu sau này ai đó thêm một `RUN apt-get …` vào `Dockerfile`, build trên máy
nội bộ sẽ hỏng ngay. Cần gói hệ thống thì phải bàn cách khác trước.

---

## 3. Proxy TLS MITM làm `pip`/`uv` từ chối chứng chỉ

**Triệu chứng.** `UnknownIssuer`, hoặc `certificate verify failed` khi cài gói
Python. Chứng chỉ do **Websecurity Gateway (VCS)** ký, không có trong bộ CA gốc
của image.

**Xử lý.** Trích CA nội bộ từ Windows cert store ra file `.pem`, rồi truyền vào
build **dưới dạng BuildKit secret** — không phải `COPY`:

```powershell
# 1. Trích CA từ Windows cert store (chạy một lần)
$ca = Get-ChildItem Cert:\LocalMachine\Root |
      Where-Object { $_.Subject -match "Websecurity|VCS|Viettel" }
$b64 = [Convert]::ToBase64String($ca[0].RawData, 'InsertLineBreaks')
"-----BEGIN CERTIFICATE-----`n$b64`n-----END CERTIFICATE-----" |
    Out-File -Encoding ascii viettel-mitm-ca.pem

# 2. Build
docker build -t sizing-copilot:dev `
  --build-arg COMMIT=$(git rev-parse --short HEAD) `
  --build-arg HTTP_PROXY=http://10.207.156.52:3128 `
  --build-arg HTTPS_PROXY=http://10.207.156.52:3128 `
  --secret id=ca_noi_bo,src=viettel-mitm-ca.pem .
```

**Vì sao dùng secret chứ không `COPY`.** Một file `COPY` vào image sẽ nằm lại
trong lớp image **vĩnh viễn**, kể cả khi bước sau `rm` nó — ai kéo image về cũng
moi ra được chứng chỉ nội bộ. BuildKit secret chỉ tồn tại trong đúng lệnh `RUN`
đó và không tạo lớp nào.

Build **không có** secret vẫn chạy bình thường (`required=false`), nên máy ngoài
không cần làm gì.

`.gitignore` và `.dockerignore` đều chặn `*.pem` / `*.crt` — chứng chỉ không lọt
vào git, cũng không lọt vào ngữ cảnh build.

**Proxy là `ARG`, không phải `ENV`** — nó chỉ có hiệu lực lúc build. Image mang
sang môi trường khác sẽ không kéo theo địa chỉ proxy của một mạng cụ thể.

---

## 4. Chạy

### Cách gọn nhất: cả hai dịch vụ bằng một lệnh

```powershell
copy config\settings.example.yaml config\settings.yaml   # điền endpoint trước
docker compose -f docker-compose.copilot.yml up --build
#  → API       http://localhost:8000/health
#  → Giao diện http://localhost:8501
```

⚠️ **Tạo `config/settings.yaml` TRƯỚC.** Bind-mount một file chưa tồn tại thì
Docker tạo một **thư mục** trùng tên. `load_settings` nay gọi tên lỗi này ra
thay vì để `IsADirectoryError` trần trụi, nhưng tránh hẳn vẫn hơn.

Giao diện **không tự chạy pipeline nữa**: nó nộp bài cho dịch vụ API và tra bằng
mã việc, nên đóng tab không mất kết quả.

### Hoặc chạy từng cái

```powershell
# API (mặc định) — cổng 8000
docker run --rm -p 8000:8000 `
  -e SIZING_COPILOT_API_KEY=$env:SIZING_COPILOT_API_KEY `
  -v "${PWD}\config\settings.yaml:/app/config/settings.yaml:ro" `
  sizing-copilot:dev

# Giao diện Streamlit — cổng 8501
docker run --rm -p 8501:8501 `
  -e SIZING_COPILOT_API_KEY=$env:SIZING_COPILOT_API_KEY `
  -v "${PWD}\config\settings.yaml:/app/config/settings.yaml:ro" `
  sizing-copilot:dev `
  streamlit run ui/app.py --server.address=0.0.0.0 --server.headless=true
```

Chạy tay thì phải chỉ cho giao diện biết API ở đâu:
`-e SIZING_COPILOT_API=http://host.docker.internal:8000` (mặc định là
`http://localhost:8000`, tức *bên trong* chính container giao diện — không có gì
ở đó).

### Kiểm nhanh sau khi chạy

```powershell
docker run --rm sizing-copilot:dev python scripts/khoi_dong_thu.py   # mã thoát 0
docker run --rm sizing-copilot:dev sh -c "du -sh /app; ls /app"      # KHÔNG có hồ sơ khách
curl http://localhost:8000/health
```

Lệnh thứ hai là lệnh quan trọng nhất: nó chứng minh **176 MB hồ sơ sizing thật
của khách không lọt vào image**. Chạy nó mỗi lần đổi `.dockerignore`.

### Giữ việc đang chạy qua một lần khởi động lại

Một tài liệu tốn ~16 phút. Muốn trạng thái công việc sống sót thì mount thư mục
đệm ra ngoài:

```powershell
docker run --rm -p 8000:8000 -v "${PWD}\.cache:/app/.cache" ... sizing-copilot:dev
```

Không mount thì việc đang chạy dở lúc container chết sẽ hiện trạng thái
`gian_doan` kèm lời nhắn nộp lại — chứ không treo mãi ở `dang_chay`.

---

## 5. Nếu chính lúc CHẠY cũng vướng TLS MITM

Chỉ xảy ra khi `llm.base_url` là `https://` đi qua gateway MITM. Khi đó mount CA
vào container lúc chạy và trỏ `SSL_CERT_FILE` vào nó:

```powershell
docker run --rm -p 8000:8000 `
  -v "${PWD}\viettel-mitm-ca.pem:/app/ca-noi-bo.pem:ro" `
  -e SSL_CERT_FILE=/app/ca-noi-bo.pem `
  ... sizing-copilot:dev
```

Mount lúc chạy chứ không nướng vào image — cùng một lý do như mục 3.

---

## 6. Cạm bẫy khi soi kết quả trên Windows

`curl ... | python -m json.tool` trên Windows đọc stdin theo **cp1252**, nên tiếng
Việt trong phản hồi hiện ra như `ChÆ°a cÃ³`. **API không sai** —
đó là UTF-8 đúng bị đường ống giải mã nhầm. Đã mất một lượt truy vết vì chuyện này
ngày 2026-09-09.

Soi cho đúng:

```powershell
# PowerShell
(Invoke-RestMethod http://localhost:8000/result/<ma>).loi
```

hoặc đọc bằng Python có ép mã:

```python
import json, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
d = json.loads(urllib.request.urlopen("http://localhost:8000/result/<ma>")
               .read().decode("utf-8"))
print(d["loi"])
```
