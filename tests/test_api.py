"""Test 3.1 — API. OFFLINE: pipeline được thay bằng hàm giả, không gọi model."""
import pathlib

import pytest

fastapi = pytest.importorskip("fastapi", reason="cài với: uv sync --extra api")
pytest.importorskip("multipart", reason="python-multipart thiếu -> upload hỏng")
from fastapi.testclient import TestClient        # noqa: E402

from src.reporting.finding import Finding        # noqa: E402


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


def test_chay_xong_thi_bao_cao_lay_o_duong_rieng(client):
    """`/result` là bản ghi chẩn đoán, KHÔNG kèm toàn văn báo cáo.

    Người ta dán bản ghi này vào chat và gửi kèm khi báo lỗi; ngày 2026-09-16
    một bản như thế bị commit vào repo với 39 KB nội dung hồ sơ khách bên trong,
    lặp lại đúng sự cố `bao-cao-mau.md` hồi 2026-09-10. Giao diện còn hỏi lại
    mỗi 5 giây, nên kèm báo cáo là kéo ~116 KB mỗi lượt hỏi không ai đọc.
    """
    from api import main
    ma = _nop(client).json()["ma"]
    assert main.bo_chay.cho_rong(5)
    d = client.get(f"/result/{ma}").json()
    assert d["trang_thai"] == "xong"
    assert "bao_cao" not in d, "toàn văn báo cáo lọt vào bản ghi chẩn đoán"
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


class TestTuyChon:
    def test_tuy_chon_di_thang_vao_pipeline(self, client):
        from api import main
        nhan = {}

        def chay(duong_dan, *, on_tien_do=None, song_song=1, **kw):
            nhan.update({"song_song": song_song, **kw})
            return _KetQua()

        main.bo_chay.dung()
        from src.cong_viec import BoChay
        main.bo_chay = BoChay(main.kho, ham_chay=chay)
        main.bo_chay.bat_dau()

        r = client.post("/review", files={"file": ("a.docx", b"PK\x03\x04")},
                        data={"nhom": "KPI, CPU", "vong": 2, "song_song": 8})
        assert r.status_code == 202
        assert main.bo_chay.cho_rong(5)
        assert nhan == {"song_song": 8, "chi_nhom": ["KPI", "CPU"], "chi_vong": 2}

    def test_khong_gui_tuy_chon_thi_dung_mac_dinh_do_duoc(self, client):
        from src.cong_viec import SONG_SONG_MAC_DINH
        from api import main
        r = client.post("/review", files={"file": ("a.docx", b"PK\x03\x04")})
        assert r.status_code == 202
        assert main.kho.lay(r.json()["ma"]).tuy_chon == {}
        assert main.bo_chay.song_song == SONG_SONG_MAC_DINH == 12

    def test_song_song_qua_lon_bi_tu_choi(self, client):
        """Đo 2026-09-09: mức 24 đã CHẬM HƠN mức 12. Cho người gọi đặt 64 là để
        họ tự làm chậm mình VÀ cả người đang xếp hàng phía sau."""
        r = client.post("/review", files={"file": ("a.docx", b"PK\x03\x04")},
                        data={"song_song": 64})
        assert r.status_code == 400 and "song_song" in r.json()["detail"]

    def test_vong_khong_hop_le_bi_tu_choi(self, client):
        r = client.post("/review", files={"file": ("a.docx", b"PK\x03\x04")},
                        data={"vong": 7})
        assert r.status_code == 400 and "vong" in r.json()["detail"]


# --------------------------------------------------- phản hồi thẩm định ----
class TestFindingsVaPhanHoi:
    _F = {"id": "KPI-02#App", "severity": "major", "category": "vuot_nguong",
          "finding": "CPU vượt ngưỡng", "rule_ref": "KPI-02", "rule_quote": "",
          "location": "", "computed_evidence": "", "suggestion": "",
          "confidence": "cao", "checklist_ref": [], "vong": 2, "scope_key": "App",
          "source_doc": "", "nhom": "vong2_chua_dat"}

    def _nop_xong(self, client):
        """Nộp bài và chờ hàm chạy giả hoàn tất — đọc kết quả sớm là 409 đúng
        (việc vẫn đang chạy), không phải lỗi endpoint."""
        from api import main
        ma = _nop(client).json()["ma"]
        assert main.bo_chay.cho_rong(5)
        return ma

    def test_xong_thi_co_findings_dang_json(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        r = client.get(f"/result/{ma}/findings")
        assert r.status_code == 200
        assert r.json()["findings"][0]["id"] == "KPI-02#App"

    def test_thieu_findings_thi_409_KHONG_tra_rong(self, client, tmp_path):
        """Trả [] cho 'không có file' là nói dối: người gọi không phân biệt được
        'không có phát hiện' với 'chưa lưu được tập findings' (NT4)."""
        from api import main
        ma = self._nop_xong(client)
        # Mô phỏng việc chạy TRƯỚC khi có tính năng / ghi findings lỗi: xoá file
        # mà _luu_findings vừa tạo tự động.
        (tmp_path / "cv" / f"{ma}.findings.json").unlink()
        r = client.get(f"/result/{ma}/findings")
        assert r.status_code == 409 and "findings" in r.json()["detail"]

    def test_post_phan_hoi_hop_le_va_id_la_thuoc_viec(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        r = client.post(f"/result/{ma}/phan-hoi", json={"phan_hoi": [{
            "finding_id": "KPI-02#App", "ghi_chu": "quy tắc áp nhầm",
            "phan_loai": "bao_sai"}]})
        assert r.status_code == 200 and r.json()["da_luu"] == 1
        assert client.get(f"/result/{ma}/phan-hoi").json()["phan_hoi"] == {
            "KPI-02#App": {"ghi_chu": "quy tắc áp nhầm", "phan_loai": "bao_sai"}}

    def test_post_lai_y_nguyen_da_luu_0(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        body = {"phan_hoi": [{"finding_id": "KPI-02#App", "ghi_chu": "ok",
                              "phan_loai": "chap_nhan"}]}
        client.post(f"/result/{ma}/phan-hoi", json=body)
        r = client.post(f"/result/{ma}/phan-hoi", json=body)
        assert r.status_code == 200 and r.json()["da_luu"] == 0

    def test_post_id_la_thu_tu_400(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        r = client.post(f"/result/{ma}/phan-hoi", json={"phan_hoi": [
            {"finding_id": "BEA-99#May", "ghi_chu": "x", "phan_loai": ""}]})
        assert r.status_code == 400 and "BEA-99#May" in r.json()["detail"]

    def test_post_phan_loai_sai_gia_tri_422(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        r = client.post(f"/result/{ma}/phan-hoi", json={"phan_hoi": [
            {"finding_id": "KPI-02#App", "ghi_chu": "x", "phan_loai": "sai"}]})
        assert r.status_code == 422

    def test_nhat_ky_lay_duoc_va_song_sot_delete_viec(self, client):
        from api import main
        ma = self._nop_xong(client)
        main.kho.luu_findings(ma, {"phien_ban": 1, "findings": [self._F],
                                   "so_loc_khong_can_cu": 0, "so_khu_trung": 0})
        client.post(f"/result/{ma}/phan-hoi", json={"phan_hoi": [
            {"finding_id": "KPI-02#App", "ghi_chu": "x", "phan_loai": "can_ban"}]})
        r = client.get("/phan-hoi/nhat-ky")
        assert r.status_code == 200
        assert "thoi_gian" in r.text and "KPI-02#App" in r.text
        assert "text/csv" in r.headers["content-type"]

        client.delete(f"/result/{ma}")               # xoá việc
        assert client.get("/phan-hoi/nhat-ky").status_code == 200

    def test_chua_co_ghi_chu_thi_nhat_ky_404(self, client):
        assert client.get("/phan-hoi/nhat-ky").status_code == 404

    def test_phan_hoi_viec_chua_xong_409(self, client):
        from api import main
        cv = main.kho.them("a.docx", "a.docx")       # không chạy
        assert client.get(f"/result/{cv.ma}/phan-hoi").status_code == 409
        assert client.post(f"/result/{cv.ma}/phan-hoi", json={"phan_hoi": [
            {"finding_id": "x", "ghi_chu": "", "phan_loai": ""}]}).status_code == 409
