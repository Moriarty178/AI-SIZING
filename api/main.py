"""3.1 — REST API bọc pipeline: POST /review, GET /result/{id}.

    uv run uvicorn api.main:app --reload

Nhận `.docx` tải lên, xếp job chạy nền (api/jobs.py — subprocess + thư mục, không
cần Redis), trả id. Client hỏi `GET /result/{id}` tới khi xong — lượt chạy thật
là **hàng chục phút** (đo 2026-09-09: 649 lượt gọi ≈ 30 phút/hồ sơ), không API
đồng bộ nào chịu được điều đó.

Báo cáo mở đầu luôn nói rõ đây là công cụ cố vấn — quyền quyết định vẫn ở người
thẩm định; API chỉ chuyển phát, không đổi điều đó.
"""
from __future__ import annotations

import pathlib
import sys

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from api import jobs
from src.giao_dien import (CAN_MODEL, GIAY_MOI_LUOT, kiem_model, luu_tam,
                           ten_file_ket_qua)
from src.ingestion.docx_reader import read_docx
from src.version import PHIEN_BAN_C3, commit_hien_tai

GOC = pathlib.Path(__file__).resolve().parents[1]
THU_MUC_TAI = GOC / "data" / "tai_len"

app = FastAPI(title="Sizing Copilot API", version=PHIEN_BAN_C3,
              description="Công cụ cố vấn tự kiểm bản định cỡ. KHÔNG phê duyệt — "
                          "người thẩm định quyết định cuối cùng.")


@app.get("/health")
def health():
    tt = kiem_model()
    return {"trang_thai": "sống", "model": tt.san_sang, "chat_model": tt.chat_model,
            "phien_ban": PHIEN_BAN_C3, "commit": commit_hien_tai()}


@app.post("/review")
async def review(f: UploadFile = File(...),
                 chi_nhom: str = Form(""),
                 chi_vong: int = Form(0),
                 doc_anh: bool = Form(False),
                 song_song: int = Form(6),
                 gia_lap: bool = Form(False)):
    """Nộp một bản sizing `.docx` để thẩm định. Trả `id_job` để hỏi kết quả.

    `chi_nhom`: "KPI,CPU" — giới hạn nhóm quy tắc cho rẻ khi thử.
    `chi_vong`: 0 = cả hai vòng, 1 = chỉ checklist, 2 = chỉ Guideline.
    `doc_anh`: đọc ảnh (2.3) — mỗi ảnh thuộc loại đã chọn tốn thêm ~1 lượt gọi.
    `gia_lap`: chạy bằng model giả — KIỂM HẠ TẦNG, kết quả vô nghĩa về chất lượng.
    """
    if not f.filename or not f.filename.lower().endswith(".docx"):
        raise HTTPException(415, "Cần tệp .docx — pipeline đọc Word, không phải PDF.")

    noi_dung = await f.read()
    if len(noi_dung) < 1000:
        raise HTTPException(422, "Tệp rỗng hoặc quá nhỏ để là một bản sizing.")
    try:
        p = luu_tam(noi_dung, f.filename, thu_muc=str(THU_MUC_TAI))
        read_docx(str(p))            # bắt lỗi file hỏng TRƯỚC khi xếp hàng
    except Exception as e:
        raise HTTPException(422, f"Không đọc được .docx: {type(e).__name__}: {e}")

    tuy_chon = {
        "chi_nhom": [x.strip() for x in (chi_nhom or "").split(",") if x.strip()] or None,
        "chi_vong": chi_vong or None,
        "doc_anh": bool(doc_anh),
        "song_song": max(1, min(16, int(song_song := song_song or 6))),
        "gia_lap": bool(gia_lap),
    }
    id_job = jobs.tao(f.filename, tuy_chon)
    jobs.khoi_dong_worker(id_job)
    return {"id_job": id_job, "trang_thai": "cho",
            "hỏi_kết_quả": f"GET /result/{id_job}"}


@app.get("/result/{id_job}")
def ket_qua(id_job: str, chi_bao_cao: bool = False):
    try:
        j = jobs.nap(id_job)
    except jobs.JobKhongTonTai:
        raise HTTPException(404, f"Không có job {id_job}.")
    if chi_bao_cao and j.get("trang_thai") == "xong":
        return PlainTextResponse(j["kq"]["bao_cao"])
    return j


@app.get("/jobs")
def cac_job():
    jobs.don_cu()
    return {"jobs": jobs.danh_sach()}


@app.get("/uoc-luong")
def uoc_luong_get(chi_nhom: str = "", chi_vong: int = 0, so_phan_he: int = 5):
    """Ước lượng chi phí — cùng công thức với giao diện, in TRƯỚC khi nộp job."""
    from src.giao_dien import uoc_luong as uoc
    # Không có tài liệu ở đây nên chỉ ước lượng theo bộ quy tắc; số bảng = 0 ⇒ cẩn thận
    from src.validators.rules_loader import load_rules
    ul = uoc.__wrapped__ if hasattr(uoc, "__wrapped__") else None
    from src.extraction.extractor import uoc_tinh_luot_goi
    from src.validators.qualitative import uoc_tinh_luot_goi_dt
    rs = load_rules()
    nhom = [x.strip() for x in chi_nhom.split(",") if x.strip()] or None
    vong = chi_vong or None
    c3 = uoc_tinh_luot_goi(rs, chi_nhom=nhom, so_phan_he=so_phan_he, so_bang=0)["tong"]
    c5 = uoc_tinh_luot_goi_dt(rs, so_phan_he, chi_vong=vong, chi_ma=nhom)
    return {"c3": c3, "c5": c5, "tong": c3 + c5,
            "phut_1_luong": round((c3 + c5) * 40 / 60),
            "luu_y": "chưa tính bảng của tài liệu — số thật sẽ cao hơn; "
                     "dùng để so sánh các lựa chọn bộ lọc, không phải hứa hẹn"}
