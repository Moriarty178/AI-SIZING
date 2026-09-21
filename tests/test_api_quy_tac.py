"""5.9 bước 2 — xem quy tắc, đề xuất sửa, kiểm tự động, đánh dấu đã áp. Qua API.

OFFLINE. Dùng `config/rules.yaml` THẬT cho phần đọc/kiểm, và một file tạm cho phần
"người chốt đã sửa file" — không bao giờ ghi vào file thật của repo.
"""
import pathlib
import shutil

import pytest

pytest.importorskip("fastapi", reason="cài với: uv sync --extra api")
pytest.importorskip("multipart")
pytest.importorskip("sqlalchemy", reason="cài với: pip install '.[db]'")
from fastapi.testclient import TestClient        # noqa: E402

from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header   # noqa: E402
from src.validators.de_xuat import doc_khoi                     # noqa: E402

ADMIN = thanh_header(tao_danh_tinh("admin", "Quản trị"))
NGUOI = thanh_header(tao_danh_tinh("nguoi_lam_sizing", "Nguyễn Văn A"))
VAN = pathlib.Path("config/rules.yaml").read_text(encoding="utf-8")
MA = "STO-02"


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api import main
    from src.cong_viec import BoChay, KhoCongViec

    monkeypatch.setenv("SIZING_COPILOT_DB_URL",
                       f"sqlite+pysqlite:///{(tmp_path / 'csdl.sqlite').as_posix()}")
    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho)
    with TestClient(main.app) as c:
        yield c
    main.kho_csdl = None


@pytest.fixture
def rules_tam(tmp_path, monkeypatch):
    """Bản sao `rules.yaml` để test sửa được — API đọc theo `main.DUONG_RULES`."""
    from api import main
    p = tmp_path / "rules.yaml"
    shutil.copy("config/rules.yaml", p)
    monkeypatch.setattr(main, "DUONG_RULES", str(p))
    return p


def _khoi_sua(severity: str = "critical") -> str:
    return doc_khoi(VAN, MA).replace("severity: minor", f"severity: {severity}")


class TestXemQuyTac:
    def test_danh_sach(self, client):
        d = client.get("/quy-tac").json()
        assert d["so_quy_tac"] == 151 and 0 < d["chay_duoc"] < d["so_quy_tac"]
        r = next(r for r in d["quy_tac"] if r["id"] == MA)
        assert r["type"] == "quantitative" and r["severity"] == "minor"
        assert "bảng tra" in r["khong_danh_gia_duoc"], "nói ra vì sao không chấm được"

    def test_chi_tiet_co_NGUYEN_VAN_khoi_yaml(self, client):
        """Admin sửa bằng cách sửa chính khối này — không có nó thì phải tự mở file
        trong container ra mà chép."""
        d = client.get(f"/quy-tac/{MA}").json()
        assert d["khoi"].startswith(f"  - id: {MA}\n")
        assert "RAID 6 chịu được hỏng 2 ổ" in d["khoi"], "chú thích còn nguyên"
        assert d["raw"]["check"] == "cap_raid == 6"
        assert d["de_xuat"] == []

    def test_ma_khong_co(self, client):
        assert client.get("/quy-tac/KHONG-CO").status_code == 404

    def test_ai_cung_xem_duoc(self, client):
        """Xem quy tắc không cần vai Admin: người làm sizing bấm vào mã lỗi trong báo
        cáo cũng phải đọc được căn cứ (NT2)."""
        assert client.get(f"/quy-tac/{MA}", headers=NGUOI).status_code == 200


class TestKiemThu:
    def test_kiem_dat_tra_ve_diff_va_con_so(self, client):
        r = client.post(f"/quy-tac/{MA}/kiem", headers=ADMIN,
                        json={"noi_dung_moi": _khoi_sua()})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["dat"] and d["loi"] == []
        assert "severity: critical" in d["diff"]
        assert any("severity" in c for c in d["canh_bao"])
        assert d["so_quy_tac"] == 151 and d["so_bieu_thuc"] == 137

    def test_kiem_hong_noi_ro_vi_sao(self, client):
        k = doc_khoi(VAN, "STO-01").replace("co_neu_iops and co_neu_latency",
                                            "co_neu_iops && co_neu_latency")
        d = client.post("/quy-tac/STO-01/kiem", headers=ADMIN,
                        json={"noi_dung_moi": k}).json()
        assert not d["dat"] and "không phân tích được" in d["loi"][0]
        assert d["tom_tat"].startswith("KHÔNG áp được")

    def test_kiem_KHONG_ghi_gi(self, client):
        client.post(f"/quy-tac/{MA}/kiem", headers=ADMIN,
                    json={"noi_dung_moi": _khoi_sua()})
        assert client.get("/de-xuat").json()["de_xuat"] == []

    def test_vai_khac_va_khong_danh_tinh_bi_chan(self, client):
        than = {"noi_dung_moi": _khoi_sua()}
        assert client.post(f"/quy-tac/{MA}/kiem", headers=NGUOI,
                           json=than).status_code == 403
        assert client.post(f"/quy-tac/{MA}/kiem", json=than).status_code == 400


class TestDeXuat:
    def test_de_xuat_dat_duoc_luu_kem_ket_qua_kiem(self, client):
        r = client.post(f"/quy-tac/{MA}/de-xuat", headers=ADMIN,
                        json={"noi_dung_moi": _khoi_sua(), "ly_do": "RAID 6 quá chặt"})
        assert r.status_code == 201, r.text
        assert r.json()["de_xuat"]["trang_thai"] == "kiem_dat"
        d = client.get("/de-xuat").json()["de_xuat"][0]
        assert d["rule_ref"] == MA and d["vai"] == "admin"
        assert d["ly_do"] == "RAID 6 quá chặt"
        assert d["noi_dung_cu"].startswith(f"  - id: {MA}"), "chụp lại khối lúc đề xuất"
        assert '"dat": true' in d["ket_qua_kiem"]
        assert d["bang_chung_eval"] == ""
        assert client.get(f"/quy-tac/{MA}").json()["de_xuat"][0]["id"] == d["id"]

    def test_de_xuat_HONG_van_duoc_luu_de_con_biet(self, client):
        k = doc_khoi(VAN, MA).replace("- id: STO-02", "- id: STO-02b")
        r = client.post(f"/quy-tac/{MA}/de-xuat", headers=ADMIN,
                        json={"noi_dung_moi": k, "ly_do": "đổi mã"})
        assert r.status_code == 201 and not r.json()["kiem"]["dat"]
        assert client.get("/de-xuat").json()["de_xuat"][0]["trang_thai"] == "kiem_hong"

    def test_loc_theo_ma_quy_tac(self, client):
        for ma in (MA, "STO-01"):
            client.post(f"/quy-tac/{ma}/de-xuat", headers=ADMIN,
                        json={"noi_dung_moi": doc_khoi(VAN, ma) + "    round: 3\n"})
        assert len(client.get("/de-xuat", params={"rule_ref": MA}).json()["de_xuat"]) == 1

    def test_ho_so_khong_co_thi_404(self, client):
        r = client.post(f"/quy-tac/{MA}/de-xuat", headers=ADMIN,
                        json={"noi_dung_moi": _khoi_sua(), "ho_so_id": 4242})
        assert r.status_code == 404

    def test_vai_khac_bi_chan(self, client):
        r = client.post(f"/quy-tac/{MA}/de-xuat", headers=NGUOI,
                        json={"noi_dung_moi": _khoi_sua()})
        assert r.status_code == 403 and client.get("/de-xuat").json()["de_xuat"] == []


class TestDanhDauDaAp:
    """Công cụ không tự sửa `rules.yaml`, nhưng nó ĐỌC được — nên không cho đánh dấu
    «đã áp» khi file chưa đổi. Ghi một điều sai vào lịch sử quyết định là NT4."""

    def _de_xuat(self, client, khoi):
        return client.post(f"/quy-tac/{MA}/de-xuat", headers=ADMIN,
                           json={"noi_dung_moi": khoi}).json()["de_xuat"]["id"]

    def test_file_chua_doi_thi_TU_CHOI_danh_dau(self, client, rules_tam):
        i = self._de_xuat(client, _khoi_sua())
        r = client.post(f"/de-xuat/{i}/trang-thai", headers=ADMIN,
                        json={"trang_thai": "da_ap"})
        assert r.status_code == 409 and "đang chạy KHÁC" in r.json()["detail"]
        assert client.get("/de-xuat").json()["de_xuat"][0]["trang_thai"] == "kiem_dat"

    def test_sua_file_roi_thi_danh_dau_duoc(self, client, rules_tam):
        khoi = _khoi_sua()
        i = self._de_xuat(client, khoi)
        from src.validators.de_xuat import ghep_khoi
        rules_tam.write_text(ghep_khoi(rules_tam.read_text(encoding="utf-8"), MA, khoi),
                             encoding="utf-8")
        r = client.post(f"/de-xuat/{i}/trang-thai", headers=ADMIN,
                        json={"trang_thai": "da_ap",
                              "bang_chung_eval": "eval-dev 09-21: 0.62 → 0.64"})
        assert r.status_code == 200, r.text
        assert r.json()["trang_thai"] == "da_ap"
        assert "0.64" in r.json()["bang_chung_eval"]
        assert client.get(f"/quy-tac/{MA}").json()["severity"] == "critical", \
            "API đọc lại file đã sửa, không phải bản trong image"

    def test_tu_choi_KHONG_doi_chieu_file(self, client, rules_tam):
        i = self._de_xuat(client, _khoi_sua())
        r = client.post(f"/de-xuat/{i}/trang-thai", headers=ADMIN,
                        json={"trang_thai": "tu_choi"})
        assert r.status_code == 200 and r.json()["trang_thai"] == "tu_choi"

    def test_de_xuat_khong_co_va_vai_khac(self, client, rules_tam):
        i = self._de_xuat(client, _khoi_sua())
        assert client.post("/de-xuat/4242/trang-thai", headers=ADMIN,
                           json={"trang_thai": "tu_choi"}).status_code == 404
        assert client.post(f"/de-xuat/{i}/trang-thai", headers=NGUOI,
                           json={"trang_thai": "tu_choi"}).status_code == 403
