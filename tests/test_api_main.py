"""Test cho api/main.py — endpoints, dùng TestClient (không mở cổng mạng)."""
from __future__ import annotations

import io

import pytest

pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

import api.jobs as jobs
import api.main as api_main


@pytest.fixture()
def khach(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "THU_MUC_JOB", tmp_path / "jobs")
    monkeypatch.setattr(api_main, "THU_MUC_TAI", tmp_path / "tai_len")
    goi = []
    monkeypatch.setattr(jobs, "khoi_dong_worker", lambda id_job: goi.append(id_job))
    api_main.jobs = jobs
    return TestClient(api_main.app), goi, tmp_path


def _docx_hop_le() -> bytes:
    """Docx THẬT do python-docx sinh — phải qua được cả read_docx của C1."""
    from docx import Document
    buf = io.BytesIO()
    d = Document()
    d.add_paragraph("Bản sizing thử nghiệm")
    d.save(buf)
    return buf.getvalue()


def test_review_tu_choi_file_khong_phai_docx(khach):
    client, goi, _ = khach
    r = client.post("/review", files={"f": ("x.pdf", b"PDF", "application/pdf")})
    assert r.status_code == 415
    assert goi == []                               # không xếp job


def test_review_tu_choi_tep_qua_nho(khach):
    client, goi, _ = khach
    r = client.post("/review", files={"f": ("nho.docx", b"doc", "application/octet-stream")})
    assert r.status_code == 422


def test_review_tu_choi_tep_hong(khach):
    client, goi, _ = khach
    noi_dung = "đây không phải zip nào cả".encode("utf-8") * 100
    r = client.post("/review", files={"f": ("hu.docx", noi_dung, "application/octet-stream")})
    assert r.status_code == 422
    assert goi == []                               # file hỏng bị chặn TRƯỚC khi xếp hàng


def test_review_khoi_dong_worker_va_tra_id(khach):
    client, goi, tmp = khach
    r = client.post("/review",
                    files={"f": ("Sizing_Hệ thống.docx", _docx_hop_le(), "application/octet-stream")},
                    data={"chi_nhom": "KPI,CPU", "gia_lap": "true"})
    assert r.status_code == 200
    id_job = r.json()["id_job"]
    assert goi == [id_job]                         # worker khởi động đúng một lần
    j = api_main.jobs.nap(id_job)
    assert j["ten_file"] == "Sizing_Hệ thống.docx"  # giữ nguyên tên gốc (1.14)
    assert j["tuy_chon"]["chi_nhom"] == ["KPI", "CPU"]
    assert j["tuy_chon"]["gia_lap"] is True
    assert j["tuy_chon"]["song_song"] == 6


def test_song_song_bi_chan_trong_khoang_1_16(khach):
    client, _, _ = khach
    r = client.post("/review", files={"f": ("a.docx", _docx_hop_le(), "application/octet-stream")},
                    data={"song_song": "999"})
    assert r.status_code == 200
    j = api_main.jobs.nap(r.json()["id_job"])
    assert j["tuy_chon"]["song_song"] == 16


def test_result_404_voi_id_la(khach):
    client, _, _ = khach
    assert client.get("/result/khong-co").status_code == 404


def test_result_xong_lay_bao_cao_truc_tiep(khach):
    client, _, tmp = khach
    id_job = jobs.tao("a.docx", {})
    jobs.dat_cho(id_job)
    j = jobs.nap(id_job)
    j["kq"] = {"bao_cao": "# Báo cáo", "so_finding": 1}
    jobs.ghi(id_job, j)
    jobs.doi_ten_trang_thai(id_job, "chay", "xong")

    r = client.get(f"/result/{id_job}")
    assert r.json()["trang_thai"] == "xong"
    # ?chi_bao_cao=true trả nguyên báo cáo Markdown, không bọc JSON
    rb = client.get(f"/result/{id_job}?chi_bao_cao=true")
    assert rb.text.startswith("# Báo cáo")


def test_health_khong_nem_khi_chua_co_model(khach):
    client, _, _ = khach
    r = client.get("/health")
    assert r.status_code == 200
    assert "trang_thai" in r.json()
