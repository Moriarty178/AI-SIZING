"""3.1 — REST API bọc pipeline. Mỏng: mọi hành vi nằm ở `src/cong_viec.py`.

    uvicorn api.main:app --host 0.0.0.0 --port 8000

    POST   /review          nộp .docx  -> 202 kèm mã việc
    GET    /result/{ma}     trạng thái + tiến độ; xong thì kèm báo cáo
    GET    /result/{ma}/bao-cao   báo cáo Markdown thô
    GET    /jobs            danh sách việc
    DELETE /result/{ma}     xoá việc, báo cáo VÀ tài liệu đã nộp
    GET    /health          cho healthcheck của container

## Vì sao KHÔNG có API chạy đồng bộ

Một tài liệu tốn ~16 phút (đo 2026-09-09: ~216 lượt gọi ở mức song song 12). Một
`POST` giữ kết nối 16 phút sẽ bị proxy cắt và người dùng bấm lại — nhân đôi tải
lên đúng cái cổng vốn đã là nút thắt. Nên chỉ có đường bất đồng bộ; không mở
thêm đường đồng bộ "cho tiện", vì nó sẽ được dùng.

## Giới hạn cố ý

Không xác thực. API này chạy trong mạng nội bộ sau lớp bảo vệ sẵn có; thêm một
cơ chế xác thực tự chế ở đây là tạo cảm giác an toàn giả. Nếu mở ra ngoài thì
phải đặt sau cổng xác thực thật, và điều đó phải do người quyết.
"""
from __future__ import annotations

import pathlib
import sys

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import PlainTextResponse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.cong_viec import BoChay, KhoCongViec                    # noqa: E402
from src.giao_dien import kiem_model, luu_tam                    # noqa: E402
from src.version import PHIEN_BAN_C3, commit_hien_tai            # noqa: E402

DUOI_CHO_PHEP = ".docx"
CO_TOI_DA = 80 * 1024 * 1024        # 80 MB — bản sizing lớn nhất trong kho ~12 MB

kho = KhoCongViec()
bo_chay = BoChay(kho)


@asynccontextmanager
async def vong_doi(_app: FastAPI):
    bo_chay.bat_dau()
    yield
    bo_chay.dung()


app = FastAPI(title="Sizing Copilot", version=PHIEN_BAN_C3, lifespan=vong_doi)


@app.get("/health")
def health() -> dict:
    """Sống chưa, và có cấu hình model chưa — HAI câu hỏi khác nhau.

    Container chạy được mà chưa có `config/settings.yaml` là trạng thái hợp lệ
    (image cố ý không mang file đó theo), nên `health` vẫn 200 — nhưng phải NÓI
    RA, đừng để người triển khai tưởng đã cấu hình xong.
    """
    tt = kiem_model()
    return {"song": True, "phien_ban": PHIEN_BAN_C3, "commit": commit_hien_tai(),
            "model_san_sang": tt.san_sang, "ghi_chu_model": tt.thong_diep.strip(),
            "dang_cho": sum(1 for c in kho.danh_sach() if not c.xong_roi)}


@app.post("/review", status_code=202)
async def review(file: UploadFile = File(...)) -> dict:
    ten = pathlib.Path(file.filename or "").name
    if not ten.lower().endswith(DUOI_CHO_PHEP):
        raise HTTPException(400, f"Chỉ nhận file {DUOI_CHO_PHEP}; nhận được «{ten}»")
    noi_dung = await file.read()
    if not noi_dung:
        raise HTTPException(400, "File rỗng")
    if len(noi_dung) > CO_TOI_DA:
        raise HTTPException(413, f"File {len(noi_dung) / 1e6:.1f} MB, vượt "
                                 f"{CO_TOI_DA / 1e6:.0f} MB")

    duong_dan = luu_tam(noi_dung, ten)
    cv = kho.them(ten, str(duong_dan))
    bo_chay.nop(cv)
    return {**cv.as_dict(),
            "ghi_chu": "Đã nhận. Một tài liệu tốn khoảng 16 phút; hỏi lại bằng "
                       f"GET /result/{cv.ma}."}


@app.get("/result/{ma}")
def result(ma: str) -> dict:
    cv = kho.lay(ma)
    if cv is None:
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    d = cv.as_dict()
    if cv.trang_thai == "xong":
        d["bao_cao"] = kho.bao_cao(ma) or ""
    return d


@app.get("/result/{ma}/bao-cao", response_class=PlainTextResponse)
def bao_cao(ma: str) -> str:
    cv = kho.lay(ma)
    if cv is None:
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    if cv.trang_thai != "xong":
        raise HTTPException(409, f"Việc đang ở trạng thái «{cv.trang_thai}», "
                                 "chưa có báo cáo")
    return kho.bao_cao(ma) or ""


@app.get("/jobs")
def jobs() -> dict:
    return {"cong_viec": [c.as_dict() for c in kho.danh_sach()]}


@app.delete("/result/{ma}")
def xoa(ma: str) -> dict:
    if not kho.xoa(ma):
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    return {"da_xoa": ma}
