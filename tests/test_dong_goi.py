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
