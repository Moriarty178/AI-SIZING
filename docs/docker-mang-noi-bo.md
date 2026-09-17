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

Copilot nằm trong `docker-compose.yml` cùng `backend`/`nginx` sẵn có, dùng
`Dockerfile.copilot`. Hai dịch vụ, **một image**:

| Dịch vụ | Cổng | Là gì |
|---|---|---|
| `copilot` | `8902 → 8000` | API thẩm định |
| `copilot-ui` | `8903 → 8501` | giao diện nộp bài |

```powershell
copy .env.example .env                                    # điền khoá + proxy
copy config\settings.example.yaml config\settings.yaml   # điền endpoint TRƯỚC
$env:COMMIT = (git rev-parse --short HEAD)
docker compose build copilot
docker compose up -d copilot copilot-ui
#  → API       http://localhost:8902/health
#  → Giao diện http://localhost:8903
```

**Vì sao cần `.env`.** Compose nội suy biến của **toàn bộ** `docker-compose.yml`
dù bạn chỉ build một dịch vụ, nên thiếu `SPRING_DATASOURCE_*` của web app sẵn có
cũng sinh `WARN … is not set` khi build Copilot. Đó chỉ là cảnh báo — nó KHÔNG
build Spring và KHÔNG chặn gì — nhưng khai đủ biến ở `.env` thì hết nhắc.

⚠️ **Tạo `config/settings.yaml` TRƯỚC.** Bind-mount một file chưa tồn tại thì
Docker tạo một **thư mục** trùng tên. `load_settings` nay gọi tên lỗi này ra
thay vì để `IsADirectoryError` trần trụi, nhưng tránh hẳn vẫn hơn.

Giao diện **không tự chạy pipeline nữa**: nó nộp bài cho dịch vụ API và tra bằng
mã việc, nên đóng tab không mất kết quả.

### Đặt khoá model khi đã đóng vào container

Chạy Streamlit bằng tay thì đặt `$env:SIZING_COPILOT_API_KEY` trước khi chạy là
xong. Trong container thì **`.env` cạnh `docker-compose.yml`** thay chỗ đó —
compose tự đọc file này, không cần `--env-file`:

```powershell
notepad .env                      # SIZING_COPILOT_API_KEY=<khoá được cấp>
docker compose up -d copilot      # đọc lại .env; KHÔNG cần build lại
docker compose exec copilot printenv SIZING_COPILOT_API_KEY   # kiểm đã vào chưa
curl.exe http://localhost:8902/health          # "model_san_sang": true
```

`docker compose restart` **không** đọc lại `.env` — nó khởi động lại đúng
container cũ với đúng biến cũ. Phải `up -d` để compose dựng lại container.

### Nút Run trong Docker Desktop — dùng được ngay

Từ 2026-09-14, hai dịch vụ copilot khai `env_file: .env`, nên compose nạp
**toàn bộ** `.env` vào container lúc chạy (khoá model, proxy, NO_PROXY). Cách
chạy giản lược:

```powershell
copy .env.example .env                                    # điền khoá + proxy
copy config\settings.example.yaml config\settings.yaml   # điền endpoint TRƯỚC
docker compose build copilot
```

Sau đó mở **Docker Desktop → Containers → nhấn ▶ Run** trên compose là cả hai
dịch vụ lên với đủ cấu hình — không cần đặt biến môi trường trong shell, không
cần `docker exec` điền thêm gì. Bấm vào tab của từng container để xem log.

Hai điều cần biết:

- **Proxy chỉ để BUILD — lúc CHẠY nó phải RỖNG.** `env_file` nạp `HTTP_PROXY` vào
  container, và lời gọi gateway model (`http://10.221.58.70:8401`) sẽ đi vòng qua
  proxy công ty rồi nhận **trang lỗi HTML của Squid**. `docker-compose.yml` nay đặt
  rỗng cả bốn biến proxy trong `environment:` của `copilot` (đè `env_file`).
  **Đừng tin `NO_PROXY=10.*`** — hướng dẫn cũ ở đây ghi như vậy và nó sai: httpx
  khớp no_proxy theo hậu tố tên miền hoặc IP, không theo ký tự đại diện. Hậu quả
  thật ngày 2026-09-16: 43/43 lời gọi C3 và 16/16 lời gọi C5 hỏng, `/health` vẫn
  xanh, việc vẫn báo «xong». Kiểm nhanh:
  `docker compose exec copilot printenv | Select-String proxy` — phải rỗng.
  Lượt chạy hỏng sạch nay sinh finding critical `NT4-MODEL-*` nói thẳng điều đó.
- **`SIZING_COPILOT_API` trong `.env` chỉ là mẫu.** Trong compose, `environment`
  đè giá trị này bằng `http://copilot:8000` (tên dịch vụ trong mạng compose) —
  đúng luôn, dù `.env` ghi gì. Giá trị trong `.env` chỉ có tác dụng khi chạy
  giao diện bằng `docker run` riêng ngoài compose.

Khoá chỉ vào dịch vụ `copilot`. **Giao diện `copilot-ui` cố ý không có khoá**:
từ mục B3 nó nộp bài cho API chứ không gọi model. Thanh bên lấy trạng thái model
từ `/health` của API — trước 2026-09-14 nó tự dựng client tại chỗ, nên trong
container luôn báo «Chưa gọi được model» và **giấu luôn** chế độ «Thẩm định đầy
đủ», dù API bên cạnh chạy tốt.

### CSDL Giai đoạn 5 (tuỳ chọn, 5.0)

Service `copilot-db` (`postgres:16-alpine`) KHÔNG tự lên cùng Copilot và KHÔNG mở
cổng ra máy chủ — máy nội bộ đã có PostgreSQL cho backend Spring. Để trống
`SIZING_COPILOT_DB_URL` thì Copilot chạy y như trước.

```powershell
notepad .env        # SIZING_COPILOT_DB_PASSWORD=<tuỳ ý>
                    # SIZING_COPILOT_DB_URL=postgresql+psycopg://copilot:<mật khẩu đó>@copilot-db:5432/copilot
docker compose up -d copilot-db
docker compose ps copilot-db                         # chờ (healthy)
docker compose up -d copilot
curl.exe http://localhost:8902/health                # "csdl": {"san_sang": true, ...}
docker compose exec copilot-db psql -U copilot -c "\dt"   # 11 bảng (10 nghiệp vụ + phiên bản lược đồ)
```

Nghiệm thu 5.1 (baseline cố định + rổ phát sinh) sau khi CSDL sẵn sàng — nộp cùng
tài liệu hai lần và tự chấm 6 tiêu chí; để đệm BẬT thì ~25 phút:

```powershell
py scripts/nghiem_thu_5_1.py "D:\duong\dan\Sizing ABC.docx" --api http://localhost:8902 --ten "Tên bạn"
docker compose exec copilot-db psql -U copilot -c "select count(*) from finding_baseline"
```

Nghiệm thu 5.2 (hiện chỗ cần sửa + ghi nhận sửa) — thẩm định lại hồ sơ nghiệm thu
một lần (tài liệu của các lần nộp trước bản 5.2 nằm ở `/tmp` cũ, đã mất), rồi hỏi
chỗ sửa cho mọi dòng. Script GHI hai lần sửa thử vào dòng đầu tiên của hồ sơ:

```powershell
py scripts/nghiem_thu_5_2.py --ho-so 1 "D:\duong\dan\Sizing ABC.docx" --api http://localhost:8902 --ten "Tên bạn"
```

Từ 5.2, tài liệu nộp lên được **giữ bền** ở `.cache/cong_viec/tai_lieu/` trong volume
`copilot-cache`; xoá việc (`DELETE /result/{ma}`) xoá cả tài liệu.

⚠️ **Mật khẩu CSDL chỉ được đặt ở LẦN ĐẦU tạo volume `copilot-db-data`.** Image
`postgres` đọc `POSTGRES_PASSWORD` đúng một lần; sửa `SIZING_COPILOT_DB_PASSWORD`
về sau KHÔNG đổi mật khẩu trong CSDL, và Copilot sẽ báo `password authentication
failed`. Sửa mà không mất dữ liệu:

```powershell
docker compose exec copilot-db psql -U copilot -c "ALTER USER copilot PASSWORD '<mật khẩu trong .env>'"
```

Copilot tự thử mở lại CSDL mỗi 30 giây, nên sửa phía CSDL thì KHÔNG cần khởi động
lại. Sửa `.env` thì phải `docker compose up -d copilot` (biến môi trường chỉ đọc lúc
tạo container). Mật khẩu có `@ : / # % ?` phải mã hoá phần trăm trong
`SIZING_COPILOT_DB_URL` (vd `@` → `%40`) — dễ nhất là dùng mật khẩu chỉ chữ và số.

`/health` KHÔNG tự kết nối CSDL — nó báo lại kết quả lần thử gần nhất.
CSDL hỏng thì `csdl.san_sang=false` kèm lý do (mật khẩu đã che), dịch vụ vẫn chạy.

### Hoặc chạy từng cái

```powershell
# API — cổng 8902
docker run --rm -p 8902:8000 `
  -e SIZING_COPILOT_API_KEY=$env:SIZING_COPILOT_API_KEY `
  -v "${PWD}\config\settings.yaml:/app/config/settings.yaml:ro" `
  -v copilot-cache:/app/.cache `
  sizing-copilot:dev

# Giao diện Streamlit — cổng 8903
docker run --rm -p 8903:8501 `
  -e SIZING_COPILOT_API=http://host.docker.internal:8902 `
  sizing-copilot:dev `
  streamlit run ui/app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true
```

Chạy tay thì phải chỉ cho giao diện biết API ở đâu:
`-e SIZING_COPILOT_API=http://host.docker.internal:8000` (mặc định là
`http://localhost:8000`, tức *bên trong* chính container giao diện — không có gì
ở đó).

### Kiểm nhanh sau khi chạy

```powershell
docker run --rm sizing-copilot:dev python scripts/khoi_dong_thu.py   # mã thoát 0
docker run --rm sizing-copilot:dev sh -c "du -sh /app; ls /app"      # KHÔNG có hồ sơ khách
curl.exe http://localhost:8902/health
```

Lệnh thứ hai là lệnh quan trọng nhất: nó chứng minh **176 MB hồ sơ sizing thật
của khách không lọt vào image**. Chạy nó mỗi lần đổi `.dockerignore`.

### Giữ việc đang chạy qua một lần khởi động lại

Một tài liệu tốn ~16 phút. Muốn trạng thái công việc sống sót thì mount thư mục
đệm ra ngoài:

```powershell
docker run --rm -p 8902:8000 -v copilot-cache:/app/.cache ... sizing-copilot:dev
```

`docker-compose.yml` đã gắn sẵn volume `copilot-cache` vào **`/app/.cache`** —
KHÔNG phải `/app/data`. Bản 2026-09-11 gắn nhầm chỗ nên việc đang chạy mất sạch
mỗi lần container khởi động lại.

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


---

## 7. Nộp một bản sizing để thử

Cách gọn nhất — một lệnh, tự chờ, tự ghi báo cáo:

```powershell
py scripts/nop_bai.py "D:\duong\dan\Sizing ABC.docx" --api http://localhost:8902
```

Nó in mã việc ngay, rồi in tiến độ theo giai đoạn (C3 → C5) cho tới khi xong, và
ghi `bao-cao-<mã>.md`. Đóng cửa sổ giữa chừng cũng không mất — tra lại bằng:

```powershell
py scripts/nop_bai.py --ma <mã việc> --api http://localhost:8902
```

Hoặc qua giao diện: mở `http://localhost:8903`, kéo file vào, chọn **Thẩm định
đầy đủ**. Trang tự làm mới 5 giây một lần và hiện mã việc.

**Một tài liệu tốn khoảng 16 phút.** Đọc mục «Cần xử lý trước khi nộp» ở đầu báo
cáo trước — khoảng 95% số dòng còn lại là *«công cụ chưa đọc được chỗ này»*, không
phải lỗi của bản sizing.
