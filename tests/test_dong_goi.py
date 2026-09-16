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
        assert '".[api,ui]"' in LENH

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
    dung = set(re.findall(r"\$\{([A-Z_][A-Z0-9_]*)", tho))
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
