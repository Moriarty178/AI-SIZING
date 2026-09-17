"""5.1 — API hồ sơ: nộp → lần 1 đóng băng baseline → thẩm định lại → đối chiếu.

OFFLINE: pipeline giả trả finding THẬT (lớp `Finding`), đi qua đúng `xuat_findings`
và C7 như lượt chạy thật; CSDL là SQLite trên đĩa (luồng chạy việc ghi, luồng API
đọc — SQLite trong bộ nhớ thì mỗi kết nối là một CSDL rỗng khác).
"""
import pathlib

import pytest

pytest.importorskip("fastapi", reason="cài với: uv sync --extra api")
pytest.importorskip("multipart")
pytest.importorskip("sqlalchemy", reason="cài với: pip install '.[db]'")
from fastapi.testclient import TestClient        # noqa: E402

from src.luu_tru.danh_tinh import tao_danh_tinh, thanh_header   # noqa: E402
from src.reporting.finding import Finding        # noqa: E402

NGUOI = thanh_header(tao_danh_tinh("nguoi_lam_sizing", "Nguyễn Văn A"))


def _f(rule, scope, n):
    return Finding(id=f"{rule}#{scope}", severity="major", category="vuot_nguong",
                   finding=f"{rule} ở {scope}: vượt ngưỡng lần {n}", rule_ref=rule,
                   computed_evidence=f"{n}% > 80%", scope_key=scope, vong=2,
                   location=f"Mục {n}")


class _KQ:
    def __init__(self, findings):
        self.findings = findings

    def bao_cao(self):
        return "# Báo cáo thử"


# Lượt chạy thứ i trả tập finding thứ i: lượt 2 đổi tên phân hệ trong ngoặc (như
# 5.0b đo được), bỏ một lỗi, thêm một lỗi.
LUOT = [
    [_f("CPU-01", "Master (K8s Master node)", 1), _f("RAM-01", "Redis", 2),
     _f("STO-17", "MinIO", 3)],
    [_f("CPU-01", "Master (K8s Control plane)", 1), _f("RAM-01", "Redis", 2),
     _f("ARC-06", "FrontEnd", 4)],
]


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


def _ghi(p, nd):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(nd)
    return p


def _nop(client, headers=None, **form):
    return client.post("/review", files={"file": ("sizing.docx", b"PK\x03\x04x")},
                       data={k: str(v) for k, v in form.items()}, headers=headers or {})


def _xong(client, ma):
    from api import main
    assert main.bo_chay.cho_rong(10)
    return client.get(f"/result/{ma}").json()


def test_health_bao_csdl_san_sang(client):
    assert client.get("/health").json()["csdl"]["san_sang"] is True


def test_lan_dau_dong_bang_baseline_va_lan_sau_doi_chieu(client):
    v1 = _xong(client, _nop(client, NGUOI).json()["ma"])
    assert v1["trang_thai"] == "xong"
    h = v1["ho_so_id"]
    assert h and "lần 1" in v1["ghi_ho_so"], v1["ghi_ho_so"]
    d1 = client.get(f"/ho-so/{h}").json()
    assert d1["so_loi_baseline"] == 3

    v2 = _xong(client, _nop(client, NGUOI, ho_so_id=h).json()["ma"])
    assert v2["ho_so_id"] == h and "lần 2" in v2["ghi_ho_so"]
    d2 = client.get(f"/ho-so/{h}").json()
    assert d2["so_loi_baseline"] == 3, "số lỗi baseline giữ nguyên"
    tt = {b["rule_ref"]: b["trang_thai"] for b in d2["baseline"]}
    assert tt == {"CPU-01": "chua_dat", "RAM-01": "chua_dat", "STO-17": "dat"}, \
        "đổi tên phân hệ trong ngoặc KHÔNG được thành «đã sửa»"
    assert [p["rule_ref"] for p in d2["phat_sinh"]] == ["ARC-06"]
    assert d2["cac_lan"][1]["dem"] == {"dat": 1, "chua_dat": 2,
                                       "chua_kiem_duoc": 0, "phat_sinh": 1}
    assert d2["cac_lan"][1]["ten"] == "Nguyễn Văn A", "tên tiếng Việt qua header"


def test_khong_co_danh_tinh_thi_viec_VAN_XONG_nhung_KHONG_ghi_ho_so(client):
    v = _xong(client, _nop(client).json()["ma"])
    assert v["trang_thai"] == "xong"
    assert v["ho_so_id"] is None
    assert v["ghi_ho_so"].startswith("bỏ qua: không có danh tính")
    assert client.get("/ho-so").json()["ho_so"] == []


def test_tham_dinh_lai_can_danh_tinh(client):
    r = _nop(client, ho_so_id=1)
    assert r.status_code == 400 and "danh tính" in r.json()["detail"]


def test_tham_dinh_lai_ho_so_khong_ton_tai_bi_chan_NGAY(client):
    """Không đợi 20 phút chạy xong mới báo."""
    assert _nop(client, NGUOI, ho_so_id=999).status_code == 404


def test_tham_dinh_lai_ho_so_da_gui_duyet_bi_chan(client):
    from api import main
    h = _xong(client, _nop(client, NGUOI).json()["ma"])["ho_so_id"]
    main.kho_csdl.dat_trang_thai_ho_so(h, "cho_duyet")
    r = _nop(client, NGUOI, ho_so_id=h)
    assert r.status_code == 409 and "cho_duyet" in r.json()["detail"]


def test_header_danh_tinh_hong_thi_400(client):
    r = _nop(client, {"X-Copilot-Vai": "he_thong", "X-Copilot-Ten": "gia"})
    assert r.status_code == 400


def test_ho_so_khong_ton_tai_404(client):
    assert client.get("/ho-so/424242").status_code == 404


def test_ds_ho_so(client):
    _xong(client, _nop(client, NGUOI).json()["ma"])
    (h,) = client.get("/ho-so").json()["ho_so"]
    assert (h["so_lan"], h["so_loi_baseline"]) == (1, 3)


def test_KHONG_cau_hinh_csdl_thi_ho_so_409_va_viec_KHONG_mang_ghi_chu(tmp_path,
                                                                      monkeypatch):
    """Máy nội bộ `git pull` về mà chưa bật CSDL: nộp bài y như trước, không thêm
    dòng «bỏ qua» nào vào bản ghi việc."""
    from api import main
    from src.cong_viec import BoChay, KhoCongViec
    monkeypatch.delenv("SIZING_COPILOT_DB_URL", raising=False)
    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho, ham_chay=lambda *a, **k: _KQ(LUOT[0]),
                          sau_khi_xong=main._ghi_ho_so)
    with TestClient(main.app) as c:
        assert c.get("/ho-so").status_code == 409
        v = _xong(c, _nop(c, NGUOI).json()["ma"])
        assert v["trang_thai"] == "xong" and v["ghi_ho_so"] == ""
        assert _nop(c, NGUOI, ho_so_id=1).status_code == 409


def test_csdl_len_SAU_copilot_thi_tu_mo_lai_KHONG_can_khoi_dong_lai(tmp_path,
                                                                    monkeypatch):
    """Máy khởi động lại: `restart: always` đưa `copilot` và `copilot-db` lên cùng
    lúc, `copilot` hay tới trước. Trước bản này tính năng hồ sơ tắt im lặng tới lần
    khởi động sau. Mô phỏng: CSDL chưa mở được lúc khởi động, lát sau mới được."""
    import time as _t
    from api import main
    from src.cong_viec import BoChay, KhoCongViec
    thu_muc = tmp_path / "chua_co"
    monkeypatch.setenv("SIZING_COPILOT_DB_URL",
                       f"sqlite+pysqlite:///{(thu_muc / 'csdl.sqlite').as_posix()}")
    monkeypatch.setattr(main, "CHO_THU_LAI_CSDL", 0.05)
    main.kho = KhoCongViec(tmp_path / "cv")
    main.bo_chay = BoChay(main.kho, ham_chay=lambda *a, **k: _KQ([]))
    with TestClient(main.app) as c:
        h = c.get("/health").json()["csdl"]
        assert h["cau_hinh"] is True and h["san_sang"] is False
        thu_muc.mkdir()                       # «CSDL lên»
        het = _t.time() + 5
        while _t.time() < het and not c.get("/health").json()["csdl"]["san_sang"]:
            _t.sleep(0.05)
        assert c.get("/health").json()["csdl"]["san_sang"] is True
        assert c.get("/ho-so").status_code == 200
    main.kho_csdl = None
