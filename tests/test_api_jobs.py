"""Test cho api/jobs.py — hàng đợi job bằng thư mục + subprocess.

Đây là phần giữ trạng thái của API: mất hoặc sai trạng thái là mất kết quả của
một lượt chạy 30 phút. Mỗi test khoá một ca đã gặp thật (bản chạy đầu 2026-09-09
để lộ: rename `xong-` nhưng trường `trang_thai` vẫn `chay`; worker không chiếm
job nên hai worker cùng chạy một job).
"""
from __future__ import annotations

import json
import pathlib

import pytest

import api.jobs as jobs
from api.jobs import JobKhongTonTai


@pytest.fixture()
def thu_muc_job(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs, "THU_MUC_JOB", tmp_path)
    return tmp_path


# ---------------------------------------------------------------- tạo & nạp --
@pytest.fixture(autouse=True)
def _thu_muc_rieng(tmp_path, monkeypatch):
    """MỌI test trong file này dùng thư mục job riêng — data/jobs/ thật có thể
    còn job dở của lượt chạy thật, đụng vào là mất kết quả 30 phút của nó."""
    monkeypatch.setattr(jobs, "THU_MUC_JOB", tmp_path)


def test_tao_tao_file_cho_ke_tien_to():
    """File vật lý phải mang tiền tố `cho-` — state machine dựa vào nó."""
    id_job = jobs.tao("thu.docx", {})
    p = jobs.THU_MUC_JOB / f"cho-{id_job}.json"
    assert p.exists()
    j = json.loads(p.read_text(encoding="utf-8"))
    assert j["trang_thai"] == "cho"
    assert j["ten_file"] == "thu.docx"


def test_nap_job_khong_ton_tai_nem_loi():
    with pytest.raises(JobKhongTonTai):
        jobs.nap("khong-co")


def test_nap_tu_choi_id_lua_dao():
    # path traversal — đầu vào từ API, không được chạm ra ngoài THU_MUC_JOB
    with pytest.raises(JobKhongTonTai):
        jobs.nap("../settings.yaml")
    with pytest.raises(JobKhongTonTai):
        jobs.nap("a/b")
    with pytest.raises(JobKhongTonTai):
        jobs.nap("")


# --------------------------------------------------------------- chiếm job --
def test_dat_cho_mot_worker_thang_worker_thua():
    id_job = jobs.tao("a.docx", {})
    assert jobs.dat_cho(id_job) == id_job          # worker 1 chiếm được
    assert jobs.dat_cho(id_job) is None            # worker 2 thua, không chạy đè
    j = jobs.nap(id_job)
    assert j["trang_thai"] == "chay"
    # file vật lý đã đổi tiền tố
    assert (jobs.THU_MUC_JOB / f"chay-{id_job}.json").exists()
    assert not (jobs.THU_MUC_JOB / f"cho-{id_job}.json").exists()


# ------------------------------------------------------- đổi trạng thái -----
def test_doi_ten_trang_thai_cap_ca_ten_lan_truong():
    """Lỗi thật 2026-09-09: file đổi sang `xong-` nhưng trường `trang_thai`
    vẫn `chay` — `/result` trả trạng thái cũ, nhánh `chi_bao_cao` không vào."""
    id_job = jobs.tao("a.docx", {})
    jobs.dat_cho(id_job)
    jobs.doi_ten_trang_thai(id_job, "chay", "xong")
    j = jobs.nap(id_job)
    assert j["trang_thai"] == "xong"
    assert (jobs.THU_MUC_JOB / f"xong-{id_job}.json").exists()


def test_doi_ten_trang_thai_khong_mat_du_lieu_kq():
    id_job = jobs.tao("a.docx", {"chi_vong": 1})
    jobs.dat_cho(id_job)
    j = jobs.nap(id_job)
    j["kq"] = {"bao_cao": "markdown", "so_finding": 5}
    jobs.ghi(id_job, j)
    jobs.doi_ten_trang_thai(id_job, "chay", "xong")
    kq = jobs.nap(id_job)["kq"]
    assert kq["bao_cao"] == "markdown" and kq["so_finding"] == 5


# ------------------------------------------------------------- ghi dữ liệu --
def test_ghi_vao_dung_file_hien_tai():
    """`ghi` không tự đoán trạng thái — phải ghi vào file có tiền tố hiện tại."""
    id_job = jobs.tao("a.docx", {})
    jobs.dat_cho(id_job)
    j = jobs.nap(id_job)
    j["tien_do"] = "C3 5/20"
    jobs.ghi(id_job, j)
    # không sinh file trần (bug cũ: ghi ra `<id>.json` không tiền tố)
    assert not (jobs.THU_MUC_JOB / f"{id_job}.json").exists()
    assert jobs.nap(id_job)["tien_do"] == "C3 5/20"


def test_danh_sach_bao_ca_hai_trang_thai_va_bo_file_hong():
    id1 = jobs.tao("one.docx", {})
    jobs.tao("two.docx", {})
    # file ghi dở (bắt gặp thật trên Windows: file rỗng tạo trước, đổ sau)
    (jobs.THU_MUC_JOB / "cho-hong.json").write_text("", encoding="utf-8")
    ds = jobs.danh_sach()
    assert len(ds) == 2
    assert all("trang_thai" in j for j in ds)


# ------------------------------------------------------------------ dọn cũ --
def test_don_cu_xoa_job_qua_han_giu_job_moi(tmp_path, monkeypatch):
    id_job = jobs.tao("cu.docx", {})
    jobs.tao("moi.docx", {})
    f_cu = jobs.THU_MUC_JOB / f"cho-{id_job}.json"
    co = f_cu.stat().st_mtime - 30 * 86400          # già hơn 30 ngày
    import os
    os.utime(f_cu, (co, co))
    n = jobs.don_cu()
    assert n == 1
    assert not f_cu.exists()
    assert len(jobs.danh_sach()) == 1
