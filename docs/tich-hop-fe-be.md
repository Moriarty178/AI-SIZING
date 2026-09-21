# Tích hợp Sizing Copilot vào Tool Sizing (FE + BE) — GIAI ĐOẠN 6

> Nhánh: **`dev-integrate`** (tạo 2026-09-21 từ `dev-isolate`).
> Đọc cùng `CLAUDE.md` (nguyên tắc) và `PLAN.md` mục GĐ 6 (bảng việc).
> File này là phần KHẢO SÁT + THIẾT KẾ. PLAN.md chỉ giữ danh sách việc.

## 0. Việc này là gì, và KHÔNG phải là gì

Người dùng chốt 2026-09-21: **tạm dừng nâng cấp Copilot**, chuyển sang ghép
Copilot vào web app sẵn có thành một hệ thống hoàn chỉnh.

**Quy trình thẩm định của Copilot KHÔNG đổi một dòng nào.** Đầu vào vẫn là một
file `.docx`, đầu ra vẫn là báo cáo + danh sách lỗi. Việc của GĐ 6 là **lớp giao
diện và lớp mạng**, đúng như định hướng kiến trúc đã ghi từ đầu PLAN: *"khi tích
hợp vào frontend + backend của tool làm sizing thì chỉ đổi lớp kết nối, phần xử
lý và lưu trữ không bị ảnh hưởng."*

Hai chỗ ghép, không hơn:

- **Đầu luồng** — đăng nhập → tab **"Thẩm định sizing"** → tải file `.docx` lên →
  Copilot chấm.
- **Cuối luồng** — người dùng dựng bản sizing bằng Tool Sizing → bấm **"Xuất file
  DOCX"** → có thêm nút **"Thẩm định sizing"** ngay đó, đưa thẳng file vừa xuất
  sang Copilot. (Hoặc họ tự vào tab ở trên rồi tải lên như cách 1.)

**KHÔNG làm trong GĐ 6:** đổi pipeline, đổi `rules.yaml`, đổi lược đồ CSDL của
Copilot, gộp CSDL Copilot vào MySQL của web app, đụng vào luồng phê duyệt
`THAM_DINH`/`PHE_DUYET` sẵn có của backend.

---

## 1. Khảo sát hệ thống sẵn có (đo 2026-09-21, KHÔNG phải phỏng đoán)

### 1.1 Bốn dịch vụ trong `docker-compose.yml`

| Dịch vụ | Là gì | Cổng ra máy chủ | Ghi chú |
|---|---|---|---|
| `backend` | Spring Boot 3.5.9, Java 21 | **KHÔNG mở cổng** | chỉ gọi được trong `app-net` và qua nginx |
| `nginx` | phục vụ `frontend/` + `dashboard/`, proxy `/api/` → `backend:8081` | **9000:8080** | `nginx/nginx.conf` |
| `copilot` | API Copilot (FastAPI) | 8902:8000 | |
| `copilot-ui` | giao diện Streamlit của Copilot | 8903:8501 | GĐ 6 xong thì đây chỉ còn là đường phụ cho Admin |
| `copilot-db` | PostgreSQL 16 của Copilot | không mở cổng | KHÁC hẳn MySQL của backend |

### 1.2 Frontend là HTML/CSS/JS tĩnh, không build

Không có Node, không có bundler. `nginx/Dockerfile` chép thẳng thư mục vào image.
Sửa FE = sửa file rồi `docker compose up -d --build --no-deps nginx`.

- `frontend/index.html` (2902 dòng) — `#project-list-page` (danh sách dự án) và
  `#project-detail-page` (chi tiết, chứa `<nav class="horizontal-tabs">` với 5 tab).
- `frontend/script.js` (18879 dòng) — toàn bộ logic.
- `dashboard/` — trang riêng cho Admin.

### 1.3 Backend

- MySQL + Flyway (`V1`…`V7` trong `backend1/src/main/resources/db/migration`),
  `ddl-auto: validate` — tức **lược đồ phải khớp đúng**, không tự tạo bảng.
- Spring Security + JWT (`jjwt 0.11.5`). FE giữ token ở `localStorage.authToken`,
  gửi `Authorization: Bearer …` qua `getAuthHeaders()`.
- Xuất Word bằng `poi-ooxml`, endpoint `POST /api/export/project/{id}` trả blob
  `.docx`.

---

## 2. BỐN vật cản phải gỡ trước khi ghép (đây là nội dung của bước 2)

Đừng bắt đầu sửa giao diện trước khi bốn cái này xanh. Cả bốn đều đã kiểm bằng
cách đọc file, không phải đoán.

> **Trạng thái 2026-09-21:** VC1, VC2, VC3 **đã sửa xong trên nhánh
> `dev-integrate`** (chờ dựng thật trên máy nội bộ để xác nhận). VC4 là cạm bẫy
> của bước 6.3, chưa tới lúc. Mô tả bên dưới giữ nguyên để biết **vì sao** mỗi
> chỗ lại như thế; đừng "sửa lại cho gọn" mà không đọc.

### VC1 — `backend1/Dockerfile` KHÔNG build jar

```dockerfile
COPY --chown=appuser:appgroup target/sizing-*.jar app.jar
```

Nó chép một jar **đã có sẵn**. `docker compose build backend` trên máy sạch sẽ
hỏng ngay vì `backend1/target/` trống. `Jenkinsfile` cho thấy cách làm thật: chạy
Maven trong một container riêng, dùng `settings.xml` trỏ mirror nội bộ:

```
registry.kcntt.net/library/maven:3.9-eclipse-temurin-21-alpine
mvn -s /tmp/settings.xml clean install -DskipTests=true
```

**Hai đường:** (a) chạy Maven trước như Jenkins; (b) đổi `backend1/Dockerfile`
thành multi-stage tự build. (b) gọn hơn cho người vận hành nhưng cần máy build
với tới được mirror Maven — **đo rồi mới chọn**, đừng chọn trước.

### VC2 — Compose KHÔNG có MySQL cho backend

`application.yaml` mặc định trỏ `jdbc:mysql://localhost:3306/sizing_local`, mà
`localhost` **bên trong container là chính container ấy** → chắc chắn hỏng.
`.env` có `SPRING_DATASOURCE_URL` để đè, nhưng `.env.example` để trống.

**Phải trả lời bằng đo, ở bước 2:** máy nội bộ đã có MySQL chạy sẵn chưa?

- Có → điền `SPRING_DATASOURCE_URL` trỏ vào nó (từ trong container thì
  `localhost` phải thành `host.docker.internal` hoặc IP thật của máy).
- Chưa → **thêm service `mysql:8` vào compose** kèm volume riêng, để Flyway tự
  dựng lược đồ từ `V1`. Đây là cách khuyên dùng khi chỉ cần chạy thử toàn hệ
  thống: không đụng CSDL thật nào.

⚠️ Dù chọn đường nào cũng **không được** dùng chung CSDL với `copilot-db`.

### VC3 — FE gọi thẳng `http://localhost:8081`, trong khi cổng đó KHÔNG mở

```js
frontend/script.js:1       const API_BASE_URL = 'http://localhost:8081/api';
frontend/login.html:75     const BACKEND_URL = "http://localhost:8081";
dashboard/js/api.js:7      const API_BASE = 'http://localhost:8081/api';
```

Dòng ngay trên `dashboard/js/api.js:7` là `//const API_BASE = '/api';` — tức bản
tương đối từng tồn tại rồi bị thay bằng bản tuyệt đối để chạy máy lập trình viên.
Qua nginx cổng 9000 thì cả ba dòng này sai: trình duyệt sẽ gọi `localhost:8081`,
nơi không có gì lắng nghe (backend không `ports:`).

**Sửa: đưa cả ba về đường tương đối** (`/api`) để đi qua proxy của nginx — cùng
gốc, không CORS, không phụ thuộc cổng. Đây là điều kiện cần của cả bước 2 lẫn
bước 3.

### VC4 — `showSection` bị ĐỊNH NGHĨA HAI LẦN, và tab mới sẽ bị cổng chặn

`frontend/script.js:11453` và `:11509` cùng khai báo `function showSection(...)`.
Bản sau đè bản trước — sửa nhầm bản là sửa vào chỗ không chạy.

Ngoài ra `showSection` chặn chuyển tab tiến tới khi tab hiện tại chưa điền xong
(`TAB_FLOW_ORDER` + `validateTabCompletion`). Tab "Thẩm định sizing" **không được
nằm trong `TAB_FLOW_ORDER`**, nếu không người dùng phải điền xong cả 5 tab mới
bấm vào được — trong khi cách dùng chính là tải một file có sẵn lên.

---

## 3. Thiết kế phần ghép

### 3.1 Đường mạng: thêm một `location` vào nginx, KHÔNG mở cổng mới

```nginx
location /copilot/ {
    proxy_pass http://copilot:8000/;
    client_max_body_size 100M;
    proxy_connect_timeout 300s;
    proxy_send_timeout    300s;
    proxy_read_timeout    300s;
}
```

Vì sao đi qua nginx thay vì để FE gọi thẳng `localhost:8902`:

- **Cùng gốc** → không phải bật CORS ở FastAPI, không phải lo preflight.
- Người dùng chỉ cần mở **một** cổng (9000). Cổng 8902/8903 giữ nguyên cho Admin
  và cho script nghiệm thu, không phải đường người dùng cuối đi.
- Thẩm định một tài liệu mất ~16–22 phút, nhưng **API là bất đồng bộ**: `POST
  /review` trả mã việc ngay (202), FE tự hỏi lại. Timeout 300s là cho lúc TẢI
  FILE LÊN, không phải chờ chạy xong.

⚠️ `nginx` phải `depends_on: copilot` hoặc ít nhất cùng `app-net` — hiện nginx đã
ở `app-net` nên gọi được `copilot:8000`. Kiểm lại lúc sửa.

### 3.2 API Copilot mà FE sẽ dùng (đã có sẵn, không viết thêm gì ở backend)

| Việc | Lời gọi |
|---|---|
| Nộp file | `POST /copilot/review` (multipart `file`) → `202 {"ma": …}` |
| Hỏi tiến độ | `GET /copilot/result/{ma}` → trạng thái · giai đoạn · giây đã chạy |
| Lấy báo cáo | `GET /copilot/result/{ma}/bao-cao` (Markdown thô) |
| Lấy danh sách lỗi | `GET /copilot/result/{ma}/findings` |
| Kiểm dịch vụ sống | `GET /copilot/health` |

**Không cần backend Spring đụng vào.** FE nói thẳng với Copilot qua nginx. Đây là
lý do việc ghép rẻ: không sinh endpoint mới, không sinh bảng mới.

### 3.3 Danh tính: Copilot KHÔNG xác thực

Copilot nhận danh tính qua header (`src/luu_tru/danh_tinh.py`, mục 5.0a) và
**không xác minh** nó — đúng như đã ghi: đây là danh tính demo.

GĐ 6 **giữ nguyên** điều đó, nhưng FE phải gửi header danh tính lấy từ phiên đăng
nhập của Tool Sizing (tên + vai), để dòng CSDL Copilot có người thật thay vì để
trống. **Không** gửi JWT sang Copilot — nó không biết kiểm và cũng không nên biết.

> ⚠️ Hệ quả phải nói với người vận hành: mở `/copilot/` qua nginx nghĩa là **ai
> vào được trang cũng gọi được API Copilot**, kể cả các endpoint Admin (5.9 —
> chúng chỉ kiểm `vai == "admin"` trong header, không xác thực). Nếu điều đó
> không chấp nhận được thì phải chặn ở nginx, và đó là việc phải quyết chứ không
> tự làm — xem mục 6.

### 3.4 Chỗ ghép 1 — tab "Thẩm định sizing"

Đặt ở đâu: người dùng phải tới được **ngay sau khi đăng nhập**, không cần mở dự
án nào. Nhưng thanh tab hiện tại nằm trong `#project-detail-page`. Nên:

- **Nút "Thẩm định sizing" ở `nav.nav-right`** (thanh trên cùng, luôn hiện sau
  khi đăng nhập) → mở một trang/khối riêng `#page-tham-dinh` ngang hàng với
  `#project-list-page`, **không** nằm trong `#project-detail-page`.
- Đồng thời **thêm một tab thứ 6** trong `horizontal-tabs` của trang chi tiết,
  trỏ tới cùng khối ấy, cho người đang ở trong dự án. Tab này **không** vào
  `TAB_FLOW_ORDER` (xem VC4).

Nội dung khối: ô chọn file `.docx` → nút Thẩm định → thanh tiến độ hỏi lại mỗi
vài giây → bảng lỗi + báo cáo. Tái dùng nguyên `showToast`, `showLoading`,
`fetchAPI` sẵn có.

### 3.5 Chỗ ghép 2 — nút ngay sau khi xuất DOCX

`exportSavedSnapshotToWord()` (`frontend/script.js:9104`) gọi
`POST /api/export/project/{id}` rồi nhận **blob** và tải về. Blob ấy đang nằm sẵn
trong trình duyệt — **giữ lại nó** và hiện nút "Thẩm định sizing" ngay cạnh, bấm
là `POST /copilot/review` với chính blob đó.

Không phải tải file về rồi bắt người dùng chọn lại. Không phải nhờ backend gửi
file sang Copilot. Đây là chỗ rẻ nhất và đúng nhất của cả GĐ 6.

---

## 4. Thứ tự làm (mỗi bước xong thì commit + push; không nhảy cóc)

1. **6.1 — Chạy được FE+BE trước đã.** Gỡ VC1, VC2, VC3. Tiêu chí: mở
   `http://<máy>:9000` → đăng nhập → thấy danh sách dự án → mở một dự án → xuất
   được DOCX. **Chưa đụng gì tới Copilot.**
2. **6.2 — Đường mạng.** Thêm `location /copilot/`, kiểm
   `curl http://<máy>:9000/copilot/health`.
3. **6.3 — Chỗ ghép 1** (tab + trang thẩm định + hỏi tiến độ + hiện kết quả).
4. **6.4 — Chỗ ghép 2** (nút sau khi xuất DOCX, dùng lại blob).
5. **6.5 — Nghiệm thu đầu-tới-cuối** trên máy nội bộ, có model thật.

## 5. Tiêu chí nghiệm thu GĐ 6 (đặt TRƯỚC khi code)

- **T1** `docker compose up -d` bốn dịch vụ → cả bốn `healthy`.
- **T2** Đăng nhập ở cổng 9000, mở một dự án, xuất DOCX thành công (chứng minh
  FE/BE chạy độc lập với Copilot).
- **T3** Tab "Thẩm định sizing": tải một `.docx` lên → nhận mã việc → thanh tiến
  độ chạy → hiện đúng số finding như khi nộp bằng `copilot-ui`. **Cùng file thì
  phải ra cùng con số** — khác là lớp ghép đang làm hỏng dữ liệu.
- **T4** Xuất DOCX rồi bấm "Thẩm định sizing" ngay đó → chạy được, không phải
  chọn lại file.
- **T5** Đóng tab trình duyệt giữa chừng rồi mở lại, tra bằng mã việc → kết quả
  còn nguyên (vốn là tính chất của API bất đồng bộ, phải giữ được sau khi ghép).
- **T6** Tắt `copilot` (`docker compose stop copilot`) → Tool Sizing vẫn dùng
  được bình thường, chỉ tab thẩm định báo lỗi rõ ràng. **Copilot hỏng không được
  kéo sập web app.**
- **Đ1** Đo: thời gian từ lúc bấm tới lúc có kết quả, số lượt hỏi tiến độ.

## 6. Ba câu đã hỏi và đã được trả lời (2026-09-21)

1. **MySQL của backend** → **thêm service `mysql:8` vào compose.** Đo cùng ngày
   trên máy nội bộ: không có gì nghe ở cổng 3306, `.env` để trống cả ba biến
   `SPRING_DATASOURCE_*`, và `backend1/target/` không tồn tại — tức chưa có CSDL
   nào để trỏ vào, cũng chưa có jar nào.
2. **Ai được gọi `/copilot/`** → **mở cho mọi người đã đăng nhập.** Ghi lại cho
   rõ: nghĩa là ai mở được trang cũng gọi được **mọi** endpoint Copilot, kể cả
   endpoint Admin của 5.9 — chúng chỉ đọc `vai` trong header chứ không xác thực.
   Chấp nhận được trong mạng nội bộ; nếu một ngày mở ra ngoài thì đây là chỗ
   đầu tiên phải chặn.
3. **`copilot-ui` (Streamlit)** → **tạm thời giữ.** Nó là đường của Admin cho
   5.6/5.9 mà FE chưa làm.

## 6b. Dựng trên máy NGOÀI mạng công ty (GĐ 6.1a, 2026-09-21)

Trước 2026-09-21 mọi lệnh dựng đều phải chạy trên máy nội bộ. Đo lại thì lý do ấy
sai một nửa: Docker có sẵn trên máy lập trình viên, cái thiếu là **đường mạng**.

| | Máy ngoài (Wi-Fi nhà) | Máy nội bộ |
|---|---|---|
| `registry.kcntt.net` — ảnh nền backend + nginx | **TCP 443 hỏng** | có |
| `nexus-lab.kcntt.net` — phụ thuộc Maven | **TCP 443 hỏng** | có |
| Proxy `10.207.156.52:3128` — `uv` kéo gói lúc build Copilot | **không với tới** | có |
| Docker Hub · ghcr.io · PyPI | được | được |
| Model `10.221.58.70:8401` | không | có |

Đã gỡ ba cái đầu:

- **Ảnh nền chuyển hẳn sang Docker Hub** ở cả `backend1/Dockerfile` và
  `nginx/Dockerfile`. Ảnh nội bộ vốn là bản sao của chính ảnh công khai ấy.
- **Nguồn Maven** là nút bấm DUY NHẤT còn lại: `MAVEN_NEXUS_NOI_BO`, mặc định `1`
  (Nexus nội bộ — máy nội bộ và Jenkins không phải đổi gì), máy ngoài đặt `0`.
  Maven không cho mirror có điều kiện nên không gộp hai trường hợp được.
- **Proxy**: máy ngoài để `HTTP_PROXY`/`HTTPS_PROXY` TRỐNG trong `.env`.

Còn **model** thì không gỡ được — và đó không phải chuyện nhỏ nếu bỏ qua:

> ⚠️ `10.221.58.70` từ ngoài mạng KHÔNG có đường đi, nên mỗi lượt gọi **treo** tới
> hết `timeout_s: 120`, nhân `max_retries: 3` (`src/llm/client.py`), nhân ~268
> lượt ở song song 12 ⇒ **hơn 2 giờ** cho một lượt chạy vô nghĩa.
>
> Cách chữa, sửa `config/settings.yaml` (đã gitignore, bind-mount — không vào repo):
> `base_url: "http://127.0.0.1:1/v1"` và `timeout_s: 5`. Cổng đóng thì hỏng trong
> vài mili-giây, cả lượt chạy xong trong vài giây và **vẫn ra finding** từ đường
> thuần code C4 — đúng như sự cố Squid 2026-09-16 (43/43 lượt C3 hỏng, việc vẫn
> báo xong với 61 finding).

Nên **việc FE của 6.3/6.4 làm tại chỗ được**; chỉ **chất lượng thẩm định thật**
(6.5) mới phải chạy trên máy nội bộ.

## 7. Cạm bẫy đã biết — đọc lại trước khi sửa FE

- `showSection` định nghĩa **hai lần**; sửa bản ở `:11509`.
- Tab mới **không** thêm vào `TAB_FLOW_ORDER`.
- `frontend/index.html.bak`, `script.js.bak`, `style.css.bak` là **file rác đang
  nằm trong repo** — đừng sửa nhầm, và đừng để nginx chép chúng vào image.
- `.env` **không commit**. Mọi biến mới phải khai ở `.env.example`, nếu không
  `tests/test_dong_goi.py::test_moi_bien_compose_dung_deu_co_trong_env_example`
  sẽ đỏ.
- Mọi thay đổi `docker-compose.yml` đều có test khoá ở `tests/test_dong_goi.py` —
  chạy `uv run --no-sync pytest tests/test_dong_goi.py` sau khi sửa.
- `.dockerignore` ở gốc **chặn tất rồi mở lại theo danh sách**. Thêm thư mục mới
  mà `nginx/Dockerfile` cần chép thì phải mở nó ra, nếu không build hỏng ở `COPY`
  — đúng lỗi đã có từ lúc file ấy ra đời cho tới 2026-09-21.
- Chỉ **lượt thẩm định thật** mới cần máy nội bộ (xem mục 6b). Build và chạy cả
  bốn dịch vụ thì máy lập trình viên làm được.
