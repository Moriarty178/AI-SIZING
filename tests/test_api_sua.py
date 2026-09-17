"""5.2 — API: xem chỗ cần sửa của một lỗi + ghi nhận đã sửa gì. OFFLINE.

Dùng FILE WORD THẬT dựng bằng python-docx: pipeline giả đọc lại chính tệp đã nộp
(qua `read_docx`, như C1 thật) để lấy `location` của phần tử — nên phép thử đi qua
đúng đường lưu tài liệu bền → đọc lại → định vị.
"""
import io

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("multipart")
pytest.importorskip("sqlalchemy")
docx = pytest.importorskip("docx")
from fastapi.testclient import TestClient        # noqa: E402

from src.ingestion.docx_reader import read_docx  # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header   # noqa: E402
from src.reporting.finding import Finding        # noqa: E402

NGUOI = thanh_header(tao_danh_tinh("nguoi_lam_sizing", "Trần Thị Bình"))


def _word() -> bytes:
    d = docx.Document()
    d.add_paragraph("Giới thiệu hệ thống")
    d.add_paragraph("Phân hệ Kafka dùng 12 core, tải đỉnh 95%")
    d.add_paragraph("Phân hệ Redis dùng 32 GB RAM")
    b = io.BytesIO()
    d.save(b)
    return b.getvalue()


class _KQ:
    def __init__(self, findings):
        self.findings = findings

    def bao_cao(self):
        return "# thử"


def _chay(duong_dan, **_):
    doc = read_docx(duong_dan)
    kafka = next(e for e in doc.elements if "Kafka" in (e.text or ""))
    return _KQ([
        Finding(id="CPU-01#Kafka", severity="major", category="vuot_nguong",
                finding="CPU Kafka vượt ngưỡng", rule_ref="CPU-01",
                computed_evidence="95% > 80%", scope_key="Kafka",
                location=kafka.location),
        # Không có vị trí — phải lùi về «đoạn nhắc tới phân hệ» và NÓI RÕ.
        Finding(id="RAM-01#Redis", severity="minor", category="thieu_thong_tin",
                finding="RAM Redis chưa có căn cứ", rule_ref="RAM-01",
                computed_evidence="32 GB", scope_key="Redis", location=""),
    ])


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api import main
    from src.cong_viec import BoChay, KhoCongViec
    monkeypatch.setenv("SIZING_COPILOT_DB_URL",
                       f"sqlite+pysqlite:///{(tmp_path / 'csdl.sqlite').as_posix()}")
    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho, ham_chay=_chay, sau_khi_xong=main._ghi_ho_so)
    main._doc_tai_lieu_dem.cache_clear()
    with TestClient(main.app) as c:
        yield c
    main.kho_csdl = None


def _ho_so(client):
    from api import main
    r = client.post("/review", files={"file": ("Sizing ABC.docx", _word())},
                    headers=NGUOI)
    assert r.status_code == 202, r.text
    assert main.bo_chay.cho_rong(10)
    v = client.get(f"/result/{r.json()['ma']}").json()
    assert v["ho_so_id"], v.get("ghi_ho_so")
    d = client.get(f"/ho-so/{v['ho_so_id']}").json()
    return v["ho_so_id"], {b["rule_ref"]: b["id"] for b in d["baseline"]}


def test_xem_cho_sua_dung_phan_tu(client):
    h, ids = _ho_so(client)
    d = client.get(f"/ho-so/{h}/finding/{ids['CPU-01']}").json()
    assert d["cho_sua"]["cach_tim"] == "phan_tu"
    assert "Kafka dùng 12 core" in d["cho_sua"]["doan"][0]["text"]
    assert d["lan_moi_nhat"]["ten_file"] == "Sizing ABC.docx"


def test_khong_vi_tri_thi_goi_y_theo_ten_phan_he_va_noi_ro(client):
    h, ids = _ho_so(client)
    c = client.get(f"/ho-so/{h}/finding/{ids['RAM-01']}").json()["cho_sua"]
    assert c["cach_tim"] == "ten_phan_he"
    assert "Redis dùng 32 GB" in c["doan"][0]["text"]
    assert "KHÔNG phải vị trí chính xác" in c["ghi_chu"]


def test_ghi_nhan_sua_hai_lan_va_doc_lai_lich_su(client):
    h, ids = _ho_so(client)
    url = f"/ho-so/{h}/finding/{ids['RAM-01']}/lan-sua"
    r1 = client.post(url, json={"noi_dung_sua": "Bổ sung số đo RAM Redis 7 ngày",
                                "noi_dung_goc": "Phân hệ Redis dùng 32 GB RAM"},
                     headers=NGUOI)
    r2 = client.post(url, json={"noi_dung_sua": "Đổi 32 GB → 48 GB"}, headers=NGUOI)
    assert (r1.status_code, r1.json()["so_lan"], r2.json()["so_lan"]) == (201, 1, 2)
    d = client.get(f"/ho-so/{h}/finding/{ids['RAM-01']}").json()
    assert [x["so_lan"] for x in d["lan_sua"]] == [1, 2]
    assert d["lan_sua"][0]["ten"] == "Trần Thị Bình", "tên tiếng Việt qua header"
    assert {b["rule_ref"]: b["so_lan_sua"]
            for b in client.get(f"/ho-so/{h}").json()["baseline"]} == \
        {"CPU-01": 0, "RAM-01": 2}


def test_ghi_nhan_sua_KHONG_co_danh_tinh_thi_400(client):
    """5.0a: thao tác GHI đầu tiên theo danh tính — không có người thì không ghi."""
    h, ids = _ho_so(client)
    r = client.post(f"/ho-so/{h}/finding/{ids['CPU-01']}/lan-sua",
                    json={"noi_dung_sua": "x"})
    assert r.status_code == 400 and "danh tính" in r.json()["detail"]


def test_ghi_nhan_sua_noi_dung_rong_bi_chan(client):
    h, ids = _ho_so(client)
    r = client.post(f"/ho-so/{h}/finding/{ids['CPU-01']}/lan-sua",
                    json={"noi_dung_sua": ""}, headers=NGUOI)
    assert r.status_code == 422


def test_finding_khong_thuoc_ho_so_thi_404(client):
    h, ids = _ho_so(client)
    assert client.get(f"/ho-so/{h}/finding/99999").status_code == 404
    assert client.post(f"/ho-so/{h}/finding/99999/lan-sua", json={"noi_dung_sua": "x"},
                       headers=NGUOI).status_code == 404


def test_ho_so_da_gui_duyet_thi_409(client):
    from api import main
    h, ids = _ho_so(client)
    main.kho_csdl.dat_trang_thai_ho_so(h, "cho_duyet")
    r = client.post(f"/ho-so/{h}/finding/{ids['CPU-01']}/lan-sua",
                    json={"noi_dung_sua": "x"}, headers=NGUOI)
    assert r.status_code == 409


def test_tai_lieu_khong_con_tren_may_thi_NOI_RO(client):
    """Việc đã bị xoá (xoá cả tài liệu) — vẫn đọc được lỗi và lịch sử sửa, chỉ
    không hiện được chỗ, và phải nói vì sao."""
    h, ids = _ho_so(client)
    ma = client.get(f"/ho-so/{h}").json()["cac_lan"][0]["ma_viec"]
    assert client.delete(f"/result/{ma}").status_code in (200, 204)
    d = client.get(f"/ho-so/{h}/finding/{ids['CPU-01']}").json()
    assert d["cho_sua"]["cach_tim"] == "khong_tim_duoc"
    assert "không còn trên máy chủ" in d["cho_sua"]["ghi_chu"]
    assert d["rule_ref"] == "CPU-01"
