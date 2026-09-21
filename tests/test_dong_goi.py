"""Kiểm `Dockerfile.copilot` + `docker-compose.yml`. OFFLINE, không cần Docker.

Ba lỗi dưới đây đều đã xảy ra thật trên máy nội bộ, và không lỗi nào bị test bắt
vì trước bản này không có test nào đọc hai file ấy.
"""
import pathlib

import pytest

yaml = pytest.importorskip("yaml")

GOC = pathlib.Path(__file__).resolve().parents[1]
DOCKERFILE = (GOC / "Dockerfile.copilot").read_text(encoding="utf-8")
# Chỉ phần LỆNH. Chú thích cố ý nhắc tới `apt-get` và `--frozen` để CẤM chúng,
# nên dò cả chú thích thì test tự đánh mình.
LENH = "\n".join(d for d in DOCKERFILE.splitlines()
                 if d.strip() and not d.lstrip().startswith("#"))
COMPOSE = yaml.safe_load((GOC / "docker-compose.yml").read_text(encoding="utf-8"))
DOCKERIGNORE = (GOC / ".dockerignore").read_text(encoding="utf-8")


class TestDockerfile:
    def test_KHONG_co_apt_get(self):
        """Proxy nội bộ trả rác cho kho apt (`Clearsigned … NOSPLIT`, 2026-09-09),
        nên mọi `apt-get install` đều hỏng. Thêm lại là build hỏng ngay."""
        assert "apt-get" not in LENH

    def test_KHONG_dung_uv_sync_frozen_vi_repo_khong_co_uv_lock(self):
        """`--frozen` đòi `uv.lock`, mà repo không có."""
        assert not (GOC / "uv.lock").exists()
        assert "--frozen" not in LENH
        assert "uv pip install --system" in LENH

    def test_cai_CA_extra_ui_de_giao_dien_chay_duoc(self):
        """Bản 2026-09-11 chỉ cài `--extra api` nên Streamlit không có trong
        image — không ai nộp được file qua giao diện."""
        assert '".[api,ui,db]"' in LENH

    def test_KHONG_copy_eval_hay_tests_vao_image(self):
        """`.dockerignore` chặn cả hai, nên `COPY eval/` sẽ làm build hỏng. Và
        `eval/` cần `data/eval_set.json` — nhãn thẩm định nội bộ."""
        for xau in ("COPY eval", "COPY tests", "COPY .streamlit"):
            assert xau not in LENH, xau

    def test_proxy_la_ARG_chu_khong_phai_ENV(self):
        """`ENV http_proxy=` sẽ theo image sang môi trường khác."""
        assert "ARG HTTP_PROXY" in LENH
        assert "ENV http_proxy" not in LENH

    def test_CA_noi_bo_la_TUY_CHON(self):
        """Máy ngoài mạng nội bộ không có file `.pem` vẫn phải build được."""
        assert "viettel-mitm-ca.pem* ./" in LENH
        assert 'if [ -f "$CA" ]' in LENH

    def test_dockerignore_mo_dung_CA_va_chan_pem_khac(self):
        assert "*.pem" in DOCKERIGNORE
        assert "!viettel-mitm-ca.pem" in DOCKERIGNORE


class TestCompose:
    def test_co_ca_API_lan_giao_dien(self):
        assert {"copilot", "copilot-ui"} <= set(COMPOSE["services"])

    def test_trang_thai_viec_gan_vao_app_cache_khong_phai_app_data(self):
        """Trạng thái công việc và đệm lời gọi nằm ở `/app/.cache`. Bản
        2026-09-11 gắn volume vào `/app/data` — chỗ không có gì ghi vào — nên
        việc đang chạy mất sạch mỗi lần container khởi động lại."""
        v = COMPOSE["services"]["copilot"]["volumes"]
        assert any(x.endswith(":/app/.cache") for x in v), v
        assert not any(":/app/data" in x for x in v), v

    def test_giao_dien_tro_dung_ten_dich_vu_API(self):
        """Mặc định `http://localhost:8000` là BÊN TRONG container giao diện."""
        env = COMPOSE["services"]["copilot-ui"]["environment"]
        assert "SIZING_COPILOT_API=http://copilot:8000" in env

    def test_hai_dich_vu_dung_chung_MOT_image(self):
        s = COMPOSE["services"]
        assert s["copilot"]["image"] == s["copilot-ui"]["image"]
        assert "build" not in s["copilot-ui"], "chỉ build một lần"

    def test_giao_dien_cho_API_khoe_roi_moi_len(self):
        assert COMPOSE["services"]["copilot-ui"]["depends_on"]["copilot"] \
            ["condition"] == "service_healthy"

    def test_KHONG_dong_cua_backend_va_nginx_san_co(self):
        """Copilot ghép vào compose của web app nội bộ — đừng đụng hai dịch vụ kia."""
        assert {"backend", "nginx"} <= set(COMPOSE["services"])
        assert COMPOSE["services"]["nginx"]["ports"] == ["9000:8080"]

    def test_khoa_API_qua_bien_moi_truong_chu_khong_nam_trong_file(self):
        env = COMPOSE["services"]["copilot"]["environment"]
        assert any(x == "SIZING_COPILOT_API_KEY=${SIZING_COPILOT_API_KEY}"
                   for x in env), env


    def test_giao_dien_KHONG_giu_khoa_model(self):
        """Giao diện nộp bài cho API (B3), không gọi gateway — nên không cần khoá.

        Ngày 2026-09-14 thanh bên trong container `copilot-ui` báo «Chưa gọi được
        model» và GIẤU chế độ «Thẩm định đầy đủ», dù API bên cạnh chạy tốt: nó tự
        dựng client tại chỗ. Cách sửa ĐÚNG là hỏi `/health` của API, không phải
        rải khoá thêm một chỗ nữa.
        """
        env = COMPOSE["services"]["copilot-ui"].get("environment", [])
        assert not any("SIZING_COPILOT_API_KEY" in x for x in env), env


    def test_bien_moi_truong_di_vao_container_qua_env_file(self):
        """Hướng dẫn đo 5.0b bảo người dùng đặt `SIZING_COPILOT_KHONG_CACHE=1`
        vào `.env` rồi `up -d`. Điều đó chỉ đúng khi dịch vụ còn `env_file`.

        Bỏ `env_file` đi thì biến im lặng không vào container, lượt chạy lại
        được phát ra từ đệm, và phép đo in 100% ổn định — một kết luận sai mà
        không có gì báo lỗi.
        """
        assert ".env" in COMPOSE["services"]["copilot"].get("env_file", [])


def test_moi_bien_compose_dung_deu_co_trong_env_example():
    """`docker compose build copilot` in `WARN … SPRING_DATASOURCE_URL is not set`
    dù Spring chẳng liên quan gì: compose nội suy biến của TOÀN BỘ file dù chỉ
    build một dịch vụ. Khai đủ biến ở `.env.example` thì hết nhắc.

    Test này để lần sau ai thêm một `${BIEN_MOI}` vào compose thì nhớ khai luôn.
    """
    import re
    tho = (GOC / "docker-compose.yml").read_text(encoding="utf-8")
    # `$${X}` là `$` thoát cho shell TRONG container (vd healthcheck của postgres),
    # không phải biến compose nội suy — không cần khai.
    dung = set(re.findall(r"(?<!\$)\$\{([A-Z_][A-Z0-9_]*)", tho))
    mau = (GOC / ".env.example").read_text(encoding="utf-8")
    khai = {d.split("=")[0].strip() for d in mau.splitlines()
            if "=" in d and not d.lstrip().startswith("#")}
    assert dung <= khai, f"chưa khai trong .env.example: {sorted(dung - khai)}"


def test_env_that_KHONG_duoc_commit():
    """`.env` chứa khoá gọi model và mật khẩu CSDL."""
    assert ".env\n" in (GOC / ".gitignore").read_text(encoding="utf-8")


def test_proxy_bi_GO_HAN_o_moi_truong_luc_chay():
    """`env_file: .env` nạp HTTP_PROXY/HTTPS_PROXY vào container. Hai biến ấy
    chỉ cần lúc BUILD để `uv` kéo gói; để nguyên lúc chạy thì mọi lời gọi model
    đi qua Squid công ty và trả về TRANG HTML LỖI.

    Hỏng thật 2026-09-16: 43/43 lượt C3 và 16/16 lượt C5 hỏng, không trích được
    trường nào, mà việc vẫn báo «xong» với 61 finding.

    `NO_PROXY` không thay được: httpx khớp no_proxy theo hậu tố tên miền hoặc
    địa chỉ IP, KHÔNG theo ký tự đại diện — `10.*` không khớp `10.221.58.70`.
    """
    env = COMPOSE["services"]["copilot"]["environment"]
    for b in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        assert f"{b}=" in env, f"{b} phải được đặt RỖNG lúc chạy: {env}"
    no = [x for x in env if x.startswith("NO_PROXY=")]
    assert no and "*" not in no[0], f"NO_PROXY không dùng được ký tự đại diện: {no}"



# --- 5.0: CSDL Giai đoạn 5 — một lần `git pull` KHÔNG được đổi gì trên máy nội bộ
class TestCSDLKhongAnhHuongKhiPull:
    DB = COMPOSE["services"]["copilot-db"]

    def test_KHONG_mo_cong_ra_may_chu(self):
        """Mở cổng là thêm chỗ trùng với PostgreSQL sẵn có trên máy (backend Spring
        dùng một CSDL) và thêm một CSDL lộ ra mạng. Copilot gọi qua `copilot-db:5432`."""
        assert "ports" not in self.DB

    def test_copilot_KHONG_phu_thuoc_csdl(self):
        """Phụ thuộc thì `docker compose up -d copilot` sẽ kéo image postgres qua
        proxy và khởi động CSDL — tức một lần pull đổi hành vi dịch vụ đang chạy."""
        dep = COMPOSE["services"]["copilot"].get("depends_on") or {}
        assert "copilot-db" not in dep

    def test_mat_khau_KHONG_dong_cung_va_KHONG_dung_dau_hoi(self):
        """`${X:?}` làm MỌI lệnh compose hỏng khi thiếu biến — kể cả lệnh chỉ động
        tới `copilot`, trên một máy có `.env` chép từ mẫu cũ."""
        import re
        tho = (GOC / "docker-compose.yml").read_text(encoding="utf-8")
        # Dò đúng cú pháp nội suy, không dò chuỗi — chú thích trong compose cố ý
        # nhắc tới `:?` để CẤM nó.
        assert not re.search(r"\$\{[A-Z_][A-Z0-9_]*:\?", tho)
        env = self.DB["environment"]
        assert "POSTGRES_PASSWORD=${SIZING_COPILOT_DB_PASSWORD:-}" in env

    def test_url_csdl_mac_dinh_TRONG(self):
        """Trống = Copilot chạy như trước, không cần CSDL."""
        env = COMPOSE["services"]["copilot"]["environment"]
        assert "SIZING_COPILOT_DB_URL=${SIZING_COPILOT_DB_URL:-}" in env

    def test_du_lieu_nam_o_volume_rieng(self):
        assert any(str(v).startswith("copilot-db-data:") for v in self.DB["volumes"])
        assert "copilot-db-data" in (COMPOSE.get("volumes") or {})

    def test_image_postgres_ghim_phien_ban_chinh(self):
        """`postgres:latest` sẽ nhảy phiên bản chính khi kéo lại, và PostgreSQL
        KHÔNG đọc được thư mục dữ liệu của phiên bản chính khác."""
        assert self.DB["image"].startswith("postgres:16")


class TestBoQuyTacOMayChu:
    """5.9 bước 2 — vật cản đã ghi trong PLAN: `rules.yaml` nằm TRONG image, nên
    người chốt sửa quy tắc xong là `up -d` lần sau mất sạch, không ai báo gì."""

    @staticmethod
    def _v(dich_vu: str) -> list[str]:
        return [str(x) for x in COMPOSE["services"][dich_vu]["volumes"]]

    def test_ca_hai_dich_vu_gan_rules_yaml_tu_may_chu(self):
        for dv in ("copilot", "copilot-ui"):
            assert any(x.startswith("./config/rules.yaml:/app/config/rules.yaml")
                       for x in self._v(dv)), self._v(dv)

    def test_gan_CHI_DOC(self):
        """Công cụ không bao giờ tự ghi vào bộ quy tắc: đề xuất nằm ở CSDL, người
        chốt sửa file trên máy chủ (có `git diff` làm đường lùi)."""
        for dv in ("copilot", "copilot-ui"):
            r = next(x for x in self._v(dv) if "rules.yaml" in x)
            assert r.endswith(":ro"), r

    def test_image_VAN_co_bo_quy_tac_de_chay_mot_minh(self):
        """Gắn từ máy chủ là ĐÈ LÊN, không phải thay thế: `docker run` trần (không
        compose) vẫn phải có quy tắc, nếu không mọi lượt thẩm định ra 0 finding."""
        assert "COPY config ./config" in DOCKERFILE


# ============================== GĐ 6 — tích hợp FE + BE ======================
BE_DOCKERFILE = (GOC / "backend1" / "Dockerfile").read_text(encoding="utf-8")
BE_LENH = "\n".join(d for d in BE_DOCKERFILE.splitlines()
                    if d.strip() and not d.lstrip().startswith("#"))
NGINX_CONF = (GOC / "nginx" / "nginx.conf").read_text(encoding="utf-8")
# Chỉ phần LỆNH — chú thích cố ý nhắc tới `proxy_pass http://copilot:8000` để CẤM
# nó, nên dò cả chú thích thì test tự đánh mình (đúng bẫy đã dính ở `LENH` phía trên).
NGINX_LENH = "\n".join(d for d in NGINX_CONF.splitlines()
                       if d.strip() and not d.lstrip().startswith("#"))


class TestBackendTuBuildDuoc:
    """6.1/VC1 — bản cũ chỉ `COPY target/sizing-*.jar`, tức đòi một jar đã có sẵn.
    Đo 2026-09-21 trên máy nội bộ: `backend1/target/` không tồn tại, nên
    `docker compose build backend` hỏng ngay ở dòng COPY."""

    def test_co_tang_BUILD_chay_maven(self):
        assert "AS build" in BE_LENH
        assert "mvn -B -DskipTests clean package" in BE_LENH

    def test_jar_lay_tu_tang_build_chu_KHONG_tu_may_chu(self):
        assert "COPY --from=build" in BE_LENH
        assert "COPY target/" not in BE_LENH and "COPY --chown=appuser:appgroup target/" \
            not in BE_LENH

    def test_dung_settings_xml_cua_repo(self):
        """Mạng nội bộ chặn Maven Central; `backend1/.m2/settings.xml` trỏ Nexus
        nội bộ và ĐÃ nằm trong repo. Jenkins gắn cùng nội dung từ máy chủ — cách
        đó không dựng tay được."""
        assert "COPY .m2/settings.xml" in BE_LENH
        assert (GOC / "backend1" / ".m2" / "settings.xml").exists()

    def test_anh_chay_van_chi_co_JRE(self):
        """Gộp Maven vào ảnh chạy là cộng ~300 MB cho mỗi lần deploy."""
        cuoi = BE_LENH[BE_LENH.rindex("FROM "):]
        assert "jre" in cuoi.split("\n")[0]
        assert "mvn" not in cuoi

    def test_co_dockerignore_rieng_chan_target(self):
        """Ngữ cảnh build là `./backend1`, nên `.dockerignore` ở gốc KHÔNG áp
        dụng. Không có file riêng thì `target/` (hàng trăm MB sau một lần chạy
        Maven trên máy) bị nhét vào mọi lượt build."""
        p = GOC / "backend1" / ".dockerignore"
        assert p.exists()
        d = p.read_text(encoding="utf-8")
        assert d.splitlines()[-1] or True
        dong = [x.strip() for x in d.splitlines() if x.strip()
                and not x.lstrip().startswith("#")]
        assert "*" in dong, "phải CHẶN TẤT CẢ rồi mở lại, như file ở gốc"
        assert "!pom.xml" in dong and "!src" in dong and "!.m2" in dong
        assert "!target" not in dong


class TestMySQLChoBackend:
    """6.1/VC2 — `application.yaml` trỏ `jdbc:mysql://localhost:3306/…`, mà
    `localhost` BÊN TRONG container là chính container ấy. Đo 2026-09-21: máy nội
    bộ không có gì nghe ở 3306 và `.env` để trống cả ba biến datasource."""

    MY = COMPOSE["services"]["mysql"]

    def test_co_dich_vu_mysql(self):
        assert self.MY["image"].startswith("mysql:8"), self.MY["image"]

    def test_KHONG_mo_cong_ra_may_chu(self):
        """Cùng lý do với `copilot-db`: chỉ `backend` trong `app-net` cần tới nó."""
        assert "ports" not in self.MY

    def test_utf8mb4_dat_o_MAY_CHU_csdl(self):
        """Tài liệu sizing đầy tiếng Việt. V1 khai charset cho từng BẢNG, nhưng
        kết nối và biến hệ thống vẫn theo mặc định của server."""
        c = " ".join(str(x) for x in self.MY["command"])
        assert "--character-set-server=utf8mb4" in c
        assert "utf8mb4_unicode_ci" in c

    def test_du_lieu_nam_o_volume_rieng(self):
        assert any(str(v).startswith("mysql-data:") for v in self.MY["volumes"])
        assert "mysql-data" in (COMPOSE.get("volumes") or {})

    def test_KHONG_gop_voi_csdl_cua_copilot(self):
        """Hai hệ thống, hai lược đồ, hai bộ migration. Flyway của Spring không
        hiểu lược đồ Copilot và ngược lại."""
        assert self.MY["image"] != COMPOSE["services"]["copilot-db"]["image"]
        assert not any("copilot-db-data" in str(v) for v in self.MY["volumes"])

    def test_MOT_bien_mat_khau_dung_cho_ca_hai_dich_vu(self):
        """Khai mật khẩu ở hai chỗ là cách chắc chắn để chúng lệch nhau."""
        assert "MYSQL_PASSWORD=${SPRING_DATASOURCE_PASSWORD:-}" in self.MY["environment"]
        be = COMPOSE["services"]["backend"]["environment"]
        assert "SPRING_DATASOURCE_PASSWORD=${SPRING_DATASOURCE_PASSWORD:-}" in be

    def test_KHONG_dat_MYSQL_USER_thanh_root(self):
        """MySQL từ chối khởi động với `MYSQL_USER=root`."""
        u = next(x for x in self.MY["environment"] if x.startswith("MYSQL_USER="))
        assert not u.endswith("root")


class TestBackendNoiDungCSDL:
    BE = COMPOSE["services"]["backend"]

    def test_cho_csdl_KHOE_roi_moi_len(self):
        """Flyway chạy lúc khởi động và `ddl-auto: validate` không tự tạo bảng —
        lên trước CSDL là hỏng hẳn, không phải chậm một nhịp."""
        assert self.BE["depends_on"]["mysql"]["condition"] == "service_healthy"

    def test_url_mac_dinh_tro_vao_dich_vu_mysql_KHONG_phai_localhost(self):
        url = next(x for x in self.BE["environment"] if "SPRING_DATASOURCE_URL" in x)
        assert "jdbc:mysql://mysql:3306/" in url
        assert "localhost:3306" not in url

    def test_co_bien_tai_khoan_mam(self):
        """Migration V1–V7 KHÔNG chèn user nào. Thiếu biến này thì dựng xong sẽ
        đứng trước màn đăng nhập mà không có tài khoản nào để vào."""
        assert "DEFAULT_USERS=${DEFAULT_USERS:-}" in self.BE["environment"]


class TestDuongCopilotQuaNginx:
    """6.2 — FE nói với Copilot qua nginx, cùng gốc, không CORS."""

    def test_co_location_copilot(self):
        assert "location /copilot/" in NGINX_LENH

    def test_proxy_pass_dung_BIEN_de_copilot_tat_khong_lam_sap_nginx(self):
        """Tiêu chí T6. `proxy_pass` viết thẳng tên máy thì nginx phân giải DNS
        lúc NẠP CẤU HÌNH và không khởi động nổi khi `copilot` đang tắt — tức tắt
        Copilot là sập cả Tool Sizing."""
        assert "proxy_pass http://copilot:8000" not in NGINX_LENH
        assert "set $copilot_upstream" in NGINX_LENH
        assert "proxy_pass http://$copilot_upstream" in NGINX_LENH
        assert "resolver 127.0.0.11" in NGINX_LENH

    def test_cat_tien_to_copilot_truoc_khi_chuyen_tiep(self):
        """Dùng biến thì nginx KHÔNG tự cắt tiền tố `location` nữa."""
        assert "rewrite ^/copilot/(.*)$ /$1 break;" in NGINX_LENH

    def test_cho_phep_tai_file_lon(self):
        i = NGINX_LENH.index("location /copilot/")
        khoi = NGINX_LENH[i:NGINX_LENH.index("location /api/", i)]
        assert "client_max_body_size 100M" in khoi

    def test_nginx_KHONG_phu_thuoc_copilot(self):
        """Phụ thuộc thì `up -d nginx` kéo theo Copilot, và tắt Copilot lại thành
        chặn nginx — vòng lại đúng chỗ T6 cấm."""
        assert "copilot" not in (COMPOSE["services"]["nginx"].get("depends_on") or {})


class TestFEKhongGoiThangCongBackend:
    """6.1/VC3 — `backend` KHÔNG mở cổng ra máy chủ, nên mọi lời gọi tuyệt đối
    tới `localhost:8081` từ trình duyệt đều rơi vào chỗ không ai nghe."""

    @pytest.mark.parametrize("duong", [
        "frontend/script.js", "frontend/login.html", "dashboard/js/api.js"])
    def test_khong_con_dia_chi_tuyet_doi(self, duong):
        van = (GOC / duong).read_text(encoding="utf-8")
        lenh = [d for d in van.splitlines()
                if "localhost:8081" in d
                and not d.lstrip().startswith(("//", "#", "<!--"))]
        assert lenh == [], lenh

    def test_goc_api_la_duong_tuong_doi(self):
        assert "const API_BASE_URL = '/api';" in \
            (GOC / "frontend" / "script.js").read_text(encoding="utf-8")
        assert "const API_BASE = '/api';" in \
            (GOC / "dashboard" / "js" / "api.js").read_text(encoding="utf-8")
