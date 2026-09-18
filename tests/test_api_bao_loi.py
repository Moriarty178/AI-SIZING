"""5.4 — API nút «Báo lỗi hệ thống»: báo được cả dòng baseline lẫn dòng phát sinh.

OFFLINE, pipeline giả trả `Finding` thật nên đi qua đúng `xuat_findings` như lượt chạy
thật — cần thế thì mới kiểm được việc nối sang nhật ký phản hồi 4.1.
"""
import pytest

pytest.importorskip("fastapi", reason="cài với: uv sync --extra api")
pytest.importorskip("multipart")
pytest.importorskip("sqlalchemy", reason="cài với: pip install '.[db]'")
from fastapi.testclient import TestClient        # noqa: E402

from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header   # noqa: E402
from src.reporting.finding import Finding        # noqa: E402

NGUOI = thanh_header(tao_danh_tinh("nguoi_lam_sizing", "Nguyễn Văn A"))


def _f(rule, scope):
    return Finding(id=f"{rule}#{scope}", severity="major", category="vuot_nguong",
                   finding=f"{rule} ở {scope}: vượt ngưỡng", rule_ref=rule,
                   computed_evidence="95% > 80%", scope_key=scope, vong=2,
                   location="Mục 1")


# Lần 2 giữ lỗi cũ và thêm một lỗi mới → rổ phát sinh có đúng một dòng.
LUOT = [[_f("CPU-01", "Kafka")], [_f("CPU-01", "Kafka"), _f("ARC-06", "Tủ rack")]]


class _KQ:
    def __init__(self, findings):
        self.findings = findings

    def bao_cao(self):
        return "# Báo cáo thử"


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api import main
    from src.cong_viec import BoChay, KhoCongViec

    dem = {"i": 0}

    def _chay(duong_dan, *, on_tien_do=None, song_song=1, **kw):
        kq = _KQ(LUOT[min(dem["i"], len(LUOT) - 1)])
        dem["i"] += 1
        return kq

    monkeypatch.setenv("SIZING_COPILOT_DB_URL",
                       f"sqlite+pysqlite:///{(tmp_path / 'csdl.sqlite').as_posix()}")
    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho, ham_chay=_chay, sau_khi_xong=main._ghi_ho_so)
    with TestClient(main.app) as c:
        yield c
    main.kho_csdl = None


@pytest.fixture
def ho_so(client):
    """Hồ sơ đã chạy hai lần: 1 dòng baseline + 1 dòng phát sinh."""
    from api import main
    for _ in range(2):
        r = client.post("/review", files={"file": ("sizing.docx", b"PK\x03\x04x")},
                        data={"ho_so_id": ""} if _ == 0 else {"ho_so_id": "1"},
                        headers=NGUOI)
        assert r.status_code == 202
        assert main.bo_chay.cho_rong(10)
    d = client.get("/ho-so/1").json()
    return 1, d["baseline"][0]["id"], d["phat_sinh"][0]["id"]


def _bao(client, ho_so_id, **than):
    return client.post(f"/ho-so/{ho_so_id}/bao-loi", json=than, headers=NGUOI)


def test_bao_dong_baseline_va_ghi_ca_nhat_ky_4_1(client, ho_so):
    from api import main
    h, fb, _ = ho_so
    r = _bao(client, h, ly_do="Sửa ba lần rồi vẫn bị báo", finding_baseline_id=fb)
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["khoa"] == "CPU-01#kafka" and d["nguon"] == "baseline"
    assert d["nhat_ky"].startswith("đã ghi nhật ký 4.1"), d["nhat_ky"]
    ma = main.kho_csdl.lan_moi_nhat(h)["ma_viec"]
    ph = main.kho.phan_hoi(ma)
    assert ph["CPU-01#Kafka"]["phan_loai"] == "bao_sai"
    assert "Sửa ba lần" in ph["CPU-01#Kafka"]["ghi_chu"]
    assert "bao_sai" in (main.kho.doc_nhat_ky() or ""), "vào cả nhật ký CSV của 4.1"


def test_bao_dong_PHAT_SINH(client, ho_so):
    """Rổ phát sinh là chỗ «phân hệ ma» của 5.3 đổ vào — phải báo được."""
    h, _, ps = ho_so
    r = _bao(client, h, ly_do="«Tủ rack» không phải phân hệ", finding_phat_sinh_id=ps)
    assert r.status_code == 201 and r.json()["nguon"] == "phát sinh"
    assert client.get(f"/ho-so/{h}/bao-loi").json()["bao_loi"][0]["khoa"] == "ARC-06#tủ rack"


def test_dem_hien_tren_bang_cua_ca_hai_ro(client, ho_so):
    h, fb, ps = ho_so
    _bao(client, h, ly_do="a", finding_baseline_id=fb)
    _bao(client, h, ly_do="b", finding_baseline_id=fb)
    _bao(client, h, ly_do="c", finding_phat_sinh_id=ps)
    d = client.get(f"/ho-so/{h}").json()
    assert d["baseline"][0]["so_bao_loi"] == 2
    assert d["phat_sinh"][0]["so_bao_loi"] == 1
    assert len(client.get(f"/ho-so/{h}/finding/{fb}").json()["bao_cao_loi"]) == 2


def test_khong_co_danh_tinh_thi_400(client, ho_so):
    h, fb, _ = ho_so
    r = client.post(f"/ho-so/{h}/bao-loi",
                    json={"ly_do": "x", "finding_baseline_id": fb})
    assert r.status_code == 400 and "danh tính" in r.json()["detail"]


def test_dong_khong_thuoc_ho_so_thi_404(client, ho_so):
    h, _, _ = ho_so
    assert _bao(client, h, ly_do="x", finding_baseline_id=9999).status_code == 404


def test_ly_do_rong_hoac_chi_mot_dong_thi_tu_choi(client, ho_so):
    h, fb, ps = ho_so
    assert _bao(client, h, ly_do="", finding_baseline_id=fb).status_code == 422
    assert _bao(client, h, ly_do="x", finding_baseline_id=fb,
                finding_phat_sinh_id=ps).status_code == 422
    assert _bao(client, h, ly_do="x").status_code == 422


def test_ho_so_khong_ton_tai_thi_404(client, ho_so):
    assert client.get("/ho-so/424242/bao-loi").status_code == 404
    assert _bao(client, 424242, ly_do="x", finding_baseline_id=1).status_code == 404


def test_viec_cua_lan_moi_nhat_da_bi_xoa_thi_van_bao_duoc(client, ho_so):
    """Nhật ký 4.1 là phần THÊM; mất nó không được chặn lời báo (NT4)."""
    from api import main
    h, fb, _ = ho_so
    main.kho.xoa(main.kho_csdl.lan_moi_nhat(h)["ma_viec"])
    r = _bao(client, h, ly_do="x", finding_baseline_id=fb)
    assert r.status_code == 201 and r.json()["nhat_ky"].startswith("bỏ qua nhật ký 4.1")
