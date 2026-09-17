"""3.1 — REST API bọc pipeline. Mỏng: mọi hành vi nằm ở `src/cong_viec.py`.

    uvicorn api.main:app --host 0.0.0.0 --port 8000

    POST   /review          nộp .docx  -> 202 kèm mã việc
    GET    /result/{ma}     trạng thái + tiến độ + thống kê (KHÔNG kèm báo cáo)
    GET    /result/{ma}/bao-cao   báo cáo Markdown thô
    GET    /result/{ma}/findings  tập finding C7 dạng JSON (cho bảng ghi chú)
    GET    /result/{ma}/phan-hoi  ghi chú người thẩm định đã lưu cho việc này
    POST   /result/{ma}/phan-hoi  lưu ghi chú mới/thay đổi (patch-merge)
    GET    /phan-hoi/nhat-ky      nhật ký phản hồi CSV (append-only)
    GET    /jobs            danh sách việc
    GET    /ho-so           5.1 — danh sách hồ sơ (cần CSDL)
    GET    /ho-so/{id}      5.1 — baseline cố định + trạng thái lần mới nhất + rổ phát sinh
    GET    /ho-so/{id}/finding/{fb}          5.2 — một lỗi + chỗ trong tài liệu + lịch sử sửa
    POST   /ho-so/{id}/finding/{fb}/lan-sua  5.2 — ghi nhận đã sửa gì (cần danh tính)
    DELETE /result/{ma}     xoá việc, báo cáo VÀ tài liệu đã nộp (KHÔNG đụng nhật ký)
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

import functools
import pathlib
import sys
import threading
from typing import Literal

from contextlib import asynccontextmanager

from fastapi import FastAPI, Form, HTTPException, Request, Response, UploadFile, File
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.cong_viec import BoChay, KhoCongViec                    # noqa: E402
from src.giao_dien import kiem_model                             # noqa: E402
from src.llm.cache import BoNhoDem                              # noqa: E402
from src.luu_tru.cau_hinh import TrangThaiCSDL, mo_kho_tu_moi_truong  # noqa: E402
from src.luu_tru.danh_tinh import tao_danh_tinh, tu_header          # noqa: E402
from src.version import PHIEN_BAN_C3, commit_hien_tai            # noqa: E402

DUOI_CHO_PHEP = ".docx"
CO_TOI_DA = 80 * 1024 * 1024        # 80 MB — bản sizing lớn nhất trong kho ~12 MB

# Trần mức song song NHẬN từ người gọi. 12 là điểm bão hoà đo được 2026-09-09 và
# mức 24 CHẬM HƠN, nên để người gọi đặt 64 là để họ tự làm chậm chính mình — và
# làm chậm cả người đang xếp hàng phía sau.
SONG_SONG_TOI_DA = 24

kho = KhoCongViec()

# CSDL Giai đoạn 5 (5.0). Mở MỘT lần lúc khởi động, không mở trong `/health` —
# xem `src/luu_tru/cau_hinh.py` vì sao. None = chưa cấu hình hoặc hỏng.
kho_csdl = None
trang_thai_csdl = TrangThaiCSDL(False, False, "Chưa khởi động")


def _ghi_ho_so(cv, du_lieu: dict | None) -> dict:
    """5.1 — sau khi một việc chạy xong: ghi lần thẩm định vào hồ sơ.

    Mọi nhánh BỎ QUA đều nói ra lý do trong `ghi_ho_so` (NT4), trừ khi CSDL chưa
    cấu hình — lúc đó tính năng đang tắt, Copilot chạy y như trước.
    Không có danh tính thì KHÔNG ghi: một dòng CSDL không có người là thứ 5.0a sinh
    ra để tránh. Việc vẫn xong và báo cáo vẫn đọc được bình thường.
    """
    if not trang_thai_csdl.cau_hinh:
        return {}
    if kho_csdl is None:
        return {"ghi_ho_so": f"bỏ qua: CSDL không sẵn sàng — "
                             f"{trang_thai_csdl.thong_diep}"[:300]}
    if not cv.danh_tinh:
        return {"ghi_ho_so": "bỏ qua: không có danh tính người nộp — không ghi dòng "
                             "không có người. Nhập tên ở thanh bên rồi nộp lại."}
    if du_lieu is None:
        return {"ghi_ho_so": "bỏ qua: không xuất được tập finding của lượt này"}
    r = kho_csdl.ghi_lan_tham_dinh(
        ma_viec=cv.ma, ten_file=cv.ten_file, ho_so_id=cv.ho_so_id,
        danh_tinh=tao_danh_tinh(**cv.danh_tinh),
        findings=list(du_lieu.get("findings") or []),
        commit=commit_hien_tai()[:80])
    return {"ho_so_id": r["ho_so_id"],
            "ghi_ho_so": (f"hồ sơ #{r['ho_so_id']} · lần {r['so_thu_tu']} · baseline "
                          f"{r['so_loi_baseline']} lỗi · đạt {r['dat']} · chưa đạt "
                          f"{r['chua_dat']} · chưa kiểm được {r['chua_kiem_duoc']} · "
                          f"phát sinh {r['phat_sinh']}")}


bo_chay = BoChay(kho, sau_khi_xong=_ghi_ho_so)


def _can_csdl():
    if kho_csdl is None:
        raise HTTPException(409, "Hồ sơ Giai đoạn 5 cần CSDL — "
                                 f"{trang_thai_csdl.thong_diep}")
    return kho_csdl


# Thử mở lại CSDL mỗi chừng ấy giây khi đã cấu hình mà chưa mở được.
CHO_THU_LAI_CSDL = 30.0


def _mo_csdl() -> None:
    global kho_csdl, trang_thai_csdl
    kho_csdl, trang_thai_csdl = mo_kho_tu_moi_truong()


def _vong_thu_lai_csdl(dung: threading.Event) -> None:
    """Thử mở lại CSDL NỀN cho tới khi được — `/health` vẫn không tự kết nối.

    Trước bản này CSDL chỉ được kiểm MỘT lần lúc khởi động, và hỏng lúc đó là hỏng
    tới khi có người khởi động lại Copilot. Hai ca có thật:
    - máy khởi động lại: `restart: always` đưa `copilot` và `copilot-db` lên CÙNG
      lúc, `copilot` không phụ thuộc CSDL (cố ý, xem compose) nên hay tới trước khi
      PostgreSQL nhận kết nối → tính năng hồ sơ tắt im lặng tới lần khởi động sau;
    - sửa mật khẩu phía CSDL (`ALTER USER`) cho khớp `.env` → phải chờ Copilot tự
      nhận ra, không bắt người vận hành khởi động lại.
    Không cứu được ca đổi `.env`: biến môi trường chỉ đọc lúc tạo container.
    """
    while not dung.wait(CHO_THU_LAI_CSDL):
        if kho_csdl is not None or not trang_thai_csdl.cau_hinh:
            return
        truoc = trang_thai_csdl.thong_diep
        _mo_csdl()
        if kho_csdl is not None:
            print(f"[csdl] đã mở lại được: {trang_thai_csdl.thong_diep}", flush=True)
            return
        if trang_thai_csdl.thong_diep != truoc:     # chỉ in khi lỗi ĐỔI, đỡ rác log
            print(f"[csdl] vẫn chưa mở được: {trang_thai_csdl.thong_diep}", flush=True)


@asynccontextmanager
async def vong_doi(_app: FastAPI):
    _mo_csdl()
    dung = threading.Event()
    if trang_thai_csdl.cau_hinh and kho_csdl is None:
        threading.Thread(target=_vong_thu_lai_csdl, args=(dung,),
                         name="thu-lai-csdl", daemon=True).start()
    bo_chay.bat_dau()
    yield
    dung.set()
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
            # Kiểm TRƯỚC khi đốt 32 phút cho một cặp lượt đo độ ổn định, thay vì
            # phát hiện sau khi đã chạy xong (2026-09-16).
            "cache_bat": BoNhoDem().bat,
            "csdl": trang_thai_csdl.as_dict(),
            "model_san_sang": tt.san_sang, "ghi_chu_model": tt.thong_diep.strip(),
            "dang_cho": sum(1 for c in kho.danh_sach() if not c.xong_roi)}


@app.post("/review", status_code=202)
async def review(
    request: Request,
    file: UploadFile = File(...),
    nhom: str = Form("", description="giới hạn nhóm quy tắc C3, vd «KPI,CPU»"),
    vong: int | None = Form(None, description="1 hoặc 2; để trống là cả hai"),
    song_song: int | None = Form(None, description=f"1..{SONG_SONG_TOI_DA}"),
    ho_so_id: int | None = Form(None, description="5.1 — thẩm định lại hồ sơ này"),
    toan_bo: bool = Form(False, description="5.3 — thẩm định lại KHÔNG dùng lại câu "
                                             "trả lời model của lần trước"),
) -> dict:
    # 5.0a — header hỏng là lỗi của bên gọi: nói ra, đừng coi như vô danh.
    try:
        danh_tinh = tu_header(request.headers)
    except ValueError as e:
        raise HTTPException(400, f"Danh tính trong header không hợp lệ: {e}")
    if ho_so_id is not None:
        # Chặn Ở CỬA: không đợi 20 phút chạy xong mới báo hồ sơ không dùng được.
        k = _can_csdl()
        if danh_tinh is None:
            raise HTTPException(400, "Thẩm định lại hồ sơ cần danh tính người nộp.")
        tt = k.trang_thai_ho_so(ho_so_id)
        if tt is None:
            raise HTTPException(404, f"Không có hồ sơ #{ho_so_id}")
        if tt != "dang_sua":
            raise HTTPException(409, f"Hồ sơ #{ho_so_id} đang «{tt}» — chỉ thẩm định "
                                     "lại được khi đang sửa.")
    elif toan_bo:
        raise HTTPException(400, "«toan_bo» chỉ dùng khi thẩm định lại một hồ sơ "
                                 "(kèm «ho_so_id»).")

    ten = pathlib.Path(file.filename or "").name
    if not ten.lower().endswith(DUOI_CHO_PHEP):
        raise HTTPException(400, f"Chỉ nhận file {DUOI_CHO_PHEP}; nhận được «{ten}»")
    noi_dung = await file.read()
    if not noi_dung:
        raise HTTPException(400, "File rỗng")
    if len(noi_dung) > CO_TOI_DA:
        raise HTTPException(413, f"File {len(noi_dung) / 1e6:.1f} MB, vượt "
                                 f"{CO_TOI_DA / 1e6:.0f} MB")

    if vong not in (None, 1, 2):
        raise HTTPException(400, "«vong» chỉ nhận 1, 2 hoặc để trống")
    if song_song is not None and not 1 <= song_song <= SONG_SONG_TOI_DA:
        raise HTTPException(400, f"«song_song» phải trong 1..{SONG_SONG_TOI_DA}")

    # Danh sách khoá CHO PHÉP, không phải danh sách chặn: một trường lạ lọt vào
    # `pipeline.chay` sẽ thành `TypeError` giữa chừng một lượt chạy 16 phút.
    tuy_chon: dict = {}
    if nhom.strip():
        tuy_chon["chi_nhom"] = [x.strip() for x in nhom.split(",") if x.strip()]
    if vong is not None:
        tuy_chon["chi_vong"] = vong
    if song_song is not None:
        tuy_chon["song_song"] = song_song

    # Tài liệu vào kho việc (volume), không vào `/tmp`: 5.2 mở lại nó nhiều ngày
    # sau để hiện chỗ cần sửa — xem `KhoCongViec._luu_tai_lieu`.
    # 5.3 — lần MỚI NHẤT lúc nộp: dùng lại câu trả lời model của nó và so tài liệu với
    # nó. Hai lượt thẩm định lại xếp hàng liền nhau thì lượt sau dùng lại lần trước
    # nữa — vẫn đúng, chỉ dùng lại được ít hơn.
    lan = k.lan_moi_nhat(ho_so_id) if ho_so_id is not None else None
    cv = kho.them(ten, "", tuy_chon, ho_so_id=ho_so_id, noi_dung=noi_dung,
                  danh_tinh=({"vai": danh_tinh.vai, "ten": danh_tinh.ten}
                             if danh_tinh else None),
                  lan_truoc=(lan or {}).get("ma_viec") or "", toan_bo=toan_bo)
    bo_chay.nop(cv)
    return {**cv.as_dict(),
            "ghi_chu": "Đã nhận. Một tài liệu tốn khoảng 16 phút; hỏi lại bằng "
                       f"GET /result/{cv.ma}."}


@app.get("/result/{ma}")
def result(ma: str) -> dict:
    cv = kho.lay(ma)
    if cv is None:
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    # KHÔNG kèm toàn văn báo cáo. Ba lý do, lý do đầu là lý do bắt buộc:
    #
    # 1. Báo cáo chứa NỘI DUNG HỒ SƠ KHÁCH. `/result` là bản ghi chẩn đoán —
    #    người ta chụp lại, dán vào chat, gửi kèm khi báo lỗi. Ngày 2026-09-16
    #    một bản ghi như thế bị commit vào repo với 39 KB báo cáo bên trong,
    #    lặp lại đúng sự cố `bao-cao-mau.md` hồi 2026-09-10.
    # 2. Giao diện hỏi lại mỗi 5 giây; kèm báo cáo là kéo theo ~116 KB mỗi lượt
    #    hỏi mà không ai đọc tới.
    # 3. Đã có `GET /result/{ma}/bao-cao` trả nguyên văn cho người thật sự cần.
    return cv.as_dict()


@app.get("/result/{ma}/bao-cao", response_class=PlainTextResponse)
def bao_cao(ma: str) -> str:
    cv = kho.lay(ma)
    if cv is None:
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    if cv.trang_thai != "xong":
        raise HTTPException(409, f"Việc đang ở trạng thái «{cv.trang_thai}», "
                                 "chưa có báo cáo")
    return kho.bao_cao(ma) or ""


@app.get("/ho-so")
def ds_ho_so() -> dict:
    return {"ho_so": _can_csdl().ds_ho_so()}


@app.get("/ho-so/{ho_so_id}")
def ho_so(ho_so_id: int) -> dict:
    d = _can_csdl().doc_ho_so(ho_so_id)
    if d is None:
        raise HTTPException(404, f"Không có hồ sơ #{ho_so_id}")
    return d


@app.get("/jobs")
def jobs() -> dict:
    return {"cong_viec": [c.as_dict() for c in kho.danh_sach()]}


# ------------------------------------------------- phản hồi thẩm định ------
# ------------------------------------------------------------ 5.2 — sửa ------
class LanSuaVao(BaseModel):
    noi_dung_sua: str = Field(min_length=1, max_length=10_000)
    # Đoạn người dùng đang nhìn lúc ghi nhận — để 5.6 đặt «trước» cạnh «sau».
    noi_dung_goc: str = Field(default="", max_length=20_000)


def _doc_tai_lieu(duong_dan: str):
    """Đọc lại tài liệu của một lần nộp; đệm theo (đường dẫn, mtime) vì người dùng
    bấm qua lại giữa các dòng của cùng một hồ sơ."""
    p = pathlib.Path(duong_dan)
    return _doc_tai_lieu_dem(str(p), p.stat().st_mtime)


@functools.lru_cache(maxsize=4)
def _doc_tai_lieu_dem(duong_dan: str, _mtime: float):
    from src.ingestion.docx_reader import read_docx
    return read_docx(duong_dan)


@app.get("/ho-so/{ho_so_id}/finding/{fb_id}")
def finding_ho_so(ho_so_id: int, fb_id: int) -> dict:
    from src.luu_tru.cho_sua import ChoSua, tim_cho_sua
    d = _can_csdl().doc_finding(ho_so_id, fb_id)
    if d is None:
        raise HTTPException(404, f"Lỗi #{fb_id} không thuộc hồ sơ #{ho_so_id}")
    lan = d.get("lan_moi_nhat") or {}
    cv = kho.lay(lan.get("ma_viec", "")) if lan else None
    duong = cv.duong_dan if cv else ""
    if not duong or not pathlib.Path(duong).is_file():
        # NT4: nói rõ vì sao không hiện được chỗ, đừng trả khối rỗng.
        cho = ChoSua("khong_tim_duoc",
                     f"Tài liệu của lần {lan.get('so_thu_tu', '?')} "
                     f"(«{lan.get('ten_file', '')}») không còn trên máy chủ — việc đã bị "
                     "xoá, hoặc nộp trước bản lưu tài liệu bền (2026-09-17).")
    else:
        try:
            cho = tim_cho_sua(_doc_tai_lieu(duong), d.get("vi_tri", ""),
                              d.get("scope_goc", ""))
        except Exception as e:                    # tài liệu hỏng không được giết API
            cho = ChoSua("khong_tim_duoc",
                         f"Không đọc lại được tài liệu: {type(e).__name__}: {e}"[:300])
    d["cho_sua"] = cho.as_dict()
    return d


@app.post("/ho-so/{ho_so_id}/finding/{fb_id}/lan-sua", status_code=201)
def ghi_lan_sua(ho_so_id: int, fb_id: int, vao: LanSuaVao, request: Request) -> dict:
    from src.luu_tru.kho import HoSoKhongDangSua, KhongCoFinding
    k = _can_csdl()
    try:
        dt = tu_header(request.headers)
    except ValueError as e:
        raise HTTPException(400, f"Danh tính trong header không hợp lệ: {e}")
    if dt is None:
        # 5.0a: thao tác ghi đầu tiên theo danh tính — không có người thì không ghi.
        raise HTTPException(400, "Ghi nhận sửa cần danh tính — nhập tên ở thanh bên.")
    try:
        return k.them_lan_sua(ho_so_id, fb_id, danh_tinh=dt,
                              noi_dung_sua=vao.noi_dung_sua, noi_dung_goc=vao.noi_dung_goc)
    except KhongCoFinding as e:
        raise HTTPException(404, str(e))
    except HoSoKhongDangSua as e:
        raise HTTPException(409, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))


class MucPhanHoiVao(BaseModel):
    finding_id: str = Field(min_length=1, max_length=300)
    ghi_chu: str = Field(default="", max_length=2000)
    phan_loai: Literal["", "chap_nhan", "bao_sai", "can_ban"] = ""


class PhanHoiVao(BaseModel):
    phan_hoi: list[MucPhanHoiVao] = Field(min_length=1, max_length=2000)


def _viec_xong(ma: str):
    cv = kho.lay(ma)
    if cv is None:
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    if cv.trang_thai != "xong":
        raise HTTPException(409, f"Việc đang ở trạng thái «{cv.trang_thai}», "
                                 "chưa có kết quả")
    return cv


@app.get("/result/{ma}/findings")
def findings(ma: str) -> dict:
    _viec_xong(ma)
    d = kho.findings(ma)
    if d is None:
        # NT4: không giả vờ trả bảng rỗng — nói rõ bảng không tạo được cho việc này
        raise HTTPException(409, "Việc này không có tập findings để lập bảng "
                                 "(chạy trước khi tính năng có mặt, hoặc ghi file lỗi)")
    return d


@app.get("/result/{ma}/phan-hoi")
def doc_phan_hoi(ma: str) -> dict:
    _viec_xong(ma)
    return {"phan_hoi": kho.phan_hoi(ma) or {}}


@app.post("/result/{ma}/phan-hoi")
def luu_phan_hoi(ma: str, vao: PhanHoiVao) -> dict:
    _viec_xong(ma)
    tap_f = {f["id"] for f in (kho.findings(ma) or {}).get("findings", [])}
    if not tap_f:
        raise HTTPException(409, "Việc này không có tập findings — không lưu được ghi chú")
    la = [m.finding_id for m in vao.phan_hoi if m.finding_id not in tap_f]
    if la:
        hien = ", ".join(f"`{x}`" for x in la[:10])
        raise HTTPException(400, f"finding_id không thuộc việc này: {hien}")
    try:
        return kho.luu_phan_hoi(ma, {m.finding_id: {"ghi_chu": m.ghi_chu,
                                                    "phan_loai": m.phan_loai}
                                     for m in vao.phan_hoi})
    except OSError:
        raise HTTPException(500, "Ghi phản hồi vào đĩa thất bại")


@app.get("/phan-hoi/nhat-ky")
def nhat_ky() -> Response:
    csv = kho.doc_nhat_ky()
    if csv is None:
        raise HTTPException(404, "Chưa có ghi chú nào được lưu")
    return Response(csv, media_type="text/csv; charset=utf-8")


@app.delete("/result/{ma}")
def xoa(ma: str) -> dict:
    if not kho.xoa(ma):
        raise HTTPException(404, f"Không có việc nào mã «{ma}»")
    return {"da_xoa": ma}
