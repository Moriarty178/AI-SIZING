"""Test 3.1 — API. OFFLINE: pipeline được thay bằng hàm giả, không gọi model."""
import pathlib

import pytest

fastapi = pytest.importorskip("fastapi", reason="cài với: uv sync --extra api")
pytest.importorskip("multipart", reason="python-multipart thiếu -> upload hỏng")
from fastapi.testclient import TestClient        # noqa: E402


class _KetQua:
    findings = []

    def bao_cao(self):
        return "# Báo cáo thử\n\nkhông có phát hiện nào."


def _chay_gia(duong_dan, *, on_tien_do=None, song_song=1, **kw):
    if on_tien_do:
        on_tien_do("C3", 1, 1, "CPU")
    return _KetQua()


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api import main
    from src.cong_viec import BoChay, KhoCongViec

    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho, ham_chay=_chay_gia)
    # Phải vá vào `api.main.luu_tam`, KHÔNG phải `src.giao_dien.luu_tam`:
    # `main` đã `from ... import luu_tam` nên nó giữ tham chiếu riêng, vá vào
    # module gốc không ăn và test sẽ lặng lẽ ghi file thật ra ngoài `tmp_path`.
    monkeypatch.setattr(main, "luu_tam",
                        lambda noi_dung, ten, thu_muc=None:
                        _ghi(tmp_path / "tai_lieu" / pathlib.Path(ten).name,
                             noi_dung))
    with TestClient(main.app) as c:
        yield c


def _ghi(p: pathlib.Path, noi_dung: bytes) -> pathlib.Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(noi_dung)
    return p


def _nop(client, ten="sizing.docx", noi_dung=b"PK\x03\x04gia lap"):
    return client.post("/review", files={"file": (ten, noi_dung)})


def test_health_noi_ro_CHUA_co_cau_hinh_model_chu_khong_im(client):
    """Image cố ý không mang `settings.yaml`. Container sống là 200, nhưng phải
    nói ra là chưa cấu hình — đừng để người triển khai tưởng đã xong."""
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["song"] is True and "commit" in d
    assert "model_san_sang" in d and "ghi_chu_model" in d


def test_nop_file_tra_202_va_ma_viec_NGAY(client):
    """Không được giữ kết nối 16 phút: proxy sẽ cắt, người dùng sẽ bấm lại."""
    r = _nop(client)
    assert r.status_code == 202
    d = r.json()
    assert d["ma"] and d["ten_file"] == "sizing.docx"
    assert d["trang_thai"] in ("cho", "dang_chay", "xong")


def test_chay_xong_thi_result_kem_bao_cao(client):
    from api import main
    ma = _nop(client).json()["ma"]
    assert main.bo_chay.cho_rong(5)
    d = client.get(f"/result/{ma}").json()
    assert d["trang_thai"] == "xong"
    assert "Báo cáo thử" in d["bao_cao"]
    assert client.get(f"/result/{ma}/bao-cao").text.startswith("# Báo cáo thử")


def test_chua_xong_thi_bao_cao_tra_409_chu_khong_tra_rong(client):
    """Trả chuỗi rỗng cho việc chưa chạy xong là nói dối: người gọi không phân
    biệt được 'chưa xong' với 'không có phát hiện nào'."""
    from api import main
    cv = main.kho.them("a.docx", "a.docx")       # nộp thẳng vào kho, không chạy
    r = client.get(f"/result/{cv.ma}/bao-cao")
    assert r.status_code == 409 and "cho" in r.json()["detail"]


class TestTuChoiDauVao:
    def test_khong_phai_docx(self, client):
        r = _nop(client, ten="sizing.pdf")
        assert r.status_code == 400 and ".docx" in r.json()["detail"]

    def test_file_rong(self, client):
        r = _nop(client, noi_dung=b"")
        assert r.status_code == 400

    def test_ten_file_khong_duoc_thoat_ra_ngoai_thu_muc(self, client):
        """`../../etc/passwd.docx` phải thành `passwd.docx`."""
        r = _nop(client, ten="../../evil.docx")
        assert r.status_code == 202
        assert r.json()["ten_file"] == "evil.docx"

    def test_ma_khong_ton_tai_tra_404(self, client):
        assert client.get("/result/khongcothat").status_code == 404
        assert client.delete("/result/khongcothat").status_code == 404


def test_xoa_don_ca_tai_lieu_da_nop(client, tmp_path):
    from api import main
    ma = _nop(client).json()["ma"]
    assert main.bo_chay.cho_rong(5)
    f = pathlib.Path(main.kho.lay(ma).duong_dan)
    assert f.exists()
    assert client.delete(f"/result/{ma}").status_code == 200
    assert not f.exists()
    assert client.get(f"/result/{ma}").status_code == 404


def test_jobs_liet_ke_moi_viec(client):
    _nop(client, ten="a.docx")
    _nop(client, ten="b.docx")
    ds = client.get("/jobs").json()["cong_viec"]
    assert {c["ten_file"] for c in ds} == {"a.docx", "b.docx"}


def test_tai_lieu_nop_len_nam_dung_trong_thu_muc_thu(client, tmp_path):
    """Chốt phép vá: nếu vá sai chỗ, test vẫn XANH nhưng ghi hồ sơ thật ra thư
    mục tạm của hệ thống. Với dữ liệu sizing nội bộ, đó không phải chuyện nhỏ."""
    from api import main
    ma = _nop(client).json()["ma"]
    assert main.bo_chay.cho_rong(5)
    f = pathlib.Path(main.kho.lay(ma).duong_dan)
    assert tmp_path in f.parents, f"tài liệu bị ghi ra ngoài tmp_path: {f}"
