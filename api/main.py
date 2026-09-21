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
    GET    /ho-so/{id}/bang-admin      5.6 — bảng lịch sử sửa lỗi (mọi lần sửa + ghi chú Admin)
    POST   /ho-so/{id}/ghi-chu-admin   5.9 — ba cột Admin (chỉ vai admin)
    GET    /ho-so/{id}/bao-loi   5.4 — các lời báo «hệ thống báo sai» của hồ sơ
    POST   /ho-so/{id}/bao-loi   5.4 — báo một dòng (baseline hoặc phát sinh) là lỗi hệ thống
    GET    /quy-tac             5.9b — danh sách quy tắc đang chạy
    GET    /quy-tac/{ma}        5.9b — chi tiết một quy tắc + NGUYÊN VĂN khối YAML
    POST   /quy-tac/{ma}/kiem   5.9b — kiểm thử một sửa đổi, KHÔNG lưu, không cần CSDL
    POST   /quy-tac/{ma}/de-xuat 5.9b — kiểm rồi lưu thành đề xuất (chỉ vai admin)
    GET    /de-xuat             5.9b — danh sách đề xuất
    POST   /de-xuat/{id}/trang-thai 5.9b — đánh dấu đã áp / từ chối / gắn bằng chứng eval
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
import json
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
from src.validators.de_xuat import doc_khoi, kiem_de_xuat        # noqa: E402
from src.validators.rules_loader import DEFAULT_RULES_PATH, RuleSet  # noqa: E402
from src.version import PHIEN_BAN_C3, commit_hien_tai            # noqa: E402

import yaml                                                      # noqa: E402

DUOI_CHO_PHEP = ".docx"
# Bộ quy tắc đang chạy. Trong container là `/app/config/rules.yaml`, gắn từ máy chủ
# (5.9 bước 2) — trước đó nó nằm TRONG image nên sửa xong là `up -d` lần sau mất.
DUONG_RULES = DEFAULT_RULES_PATH
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


def _tt_csdl() -> dict:
    """Trạng thái CSDL cho `/health`, kèm phiên bản lược đồ ĐANG trong CSDL (5.4 có
    migration thật, nên người vận hành phải thấy được nó đã chạy chưa)."""
    d = trang_thai_csdl.as_dict()
    if kho_csdl is not None:
        try:
            d["luoc_do"] = kho_csdl.phien_ban_luoc_do()
        except Exception as e:                  # CSDL rớt giữa chừng: nói ra, đừng 500
            d["luoc_do"] = f"không đọc được: {type(e).__name__}"
    return d


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
            "csdl": _tt_csdl(),
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


class BaoLoiVao(BaseModel):
    ly_do: str = Field(min_length=1, max_length=2000)
    # Đúng MỘT trong hai — lớp lưu trữ kiểm lại, ở đây chỉ nhận.
    finding_baseline_id: int | None = None
    finding_phat_sinh_id: int | None = None


def _ghi_nhat_ky_4_1(ho_so_id: int, finding_id_goc: str, ly_do: str) -> str:
    """5.4 nối với vòng phản hồi 4.1: lời báo cũng vào nhật ký «Báo sai» của LẦN MỚI
    NHẤT, để dataset cải tiến công cụ chỉ có MỘT chỗ.

    Chạy tốt nhất có thể: hỏng thì lời báo trong CSDL vẫn còn, và câu trả lời nói ra
    vì sao không ghi được (NT4).
    """
    if not finding_id_goc:
        return "bỏ qua nhật ký 4.1: dòng này không có finding_id gốc"
    lan = kho_csdl.lan_moi_nhat(ho_so_id) if kho_csdl else None
    ma = (lan or {}).get("ma_viec") or ""
    if not ma or kho.lay(ma) is None:
        return "bỏ qua nhật ký 4.1: không còn việc của lần thẩm định mới nhất"
    if finding_id_goc not in {f["id"] for f in (kho.findings(ma) or {})
                              .get("findings", [])}:
        return "bỏ qua nhật ký 4.1: dòng không có trong tập finding của lần mới nhất"
    try:
        kho.luu_phan_hoi(ma, {finding_id_goc: {
            "ghi_chu": f"[Báo lỗi hệ thống] {ly_do}", "phan_loai": "bao_sai"}})
        return f"đã ghi nhật ký 4.1 (việc {ma})"
    except (OSError, KeyError, ValueError) as e:
        return f"bỏ qua nhật ký 4.1: {type(e).__name__}: {e}"[:200]


@app.post("/ho-so/{ho_so_id}/bao-loi", status_code=201)
def bao_loi(ho_so_id: int, vao: BaoLoiVao, request: Request) -> dict:
    from src.luu_tru.kho import KhongCoFinding
    k = _can_csdl()
    try:
        dt = tu_header(request.headers)
    except ValueError as e:
        raise HTTPException(400, f"Danh tính trong header không hợp lệ: {e}")
    if dt is None:
        raise HTTPException(400, "Báo lỗi hệ thống cần danh tính — nhập tên ở thanh bên.")
    try:
        r = k.them_bao_cao_loi(
            ho_so_id, danh_tinh=dt, ly_do=vao.ly_do,
            finding_baseline_id=vao.finding_baseline_id,
            finding_phat_sinh_id=vao.finding_phat_sinh_id)
    except KhongCoFinding as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {**r, "nhat_ky": _ghi_nhat_ky_4_1(ho_so_id, r["finding_id_goc"], vao.ly_do)}


@app.get("/ho-so/{ho_so_id}/bao-loi")
def ds_bao_loi(ho_so_id: int) -> dict:
    k = _can_csdl()
    if k.trang_thai_ho_so(ho_so_id) is None:
        raise HTTPException(404, f"Không có hồ sơ #{ho_so_id}")
    return {"bao_loi": k.ds_bao_cao_loi(ho_so_id)}


class MucGhiChuAdminVao(BaseModel):
    finding_baseline_id: int
    ghi_chu: str = Field(default="", max_length=10_000)
    danh_gia: Literal["", "chap_nhan", "tu_choi", "can_ban"] = ""
    loi_o_phia: Literal["", "nguoi_lam_sizing", "he_thong_ai"] = ""


class GhiChuAdminVao(BaseModel):
    muc: list[MucGhiChuAdminVao] = Field(min_length=1, max_length=2000)


def _admin(request: Request, viec: str = "Ghi chú Admin"):
    """Ba cột 5.9 là tiếng nói của người thẩm định — dòng phải mang đúng vai Admin.

    Danh tính vẫn KHÔNG xác thực (5.0a): ai cũng chọn được vai Admin trên giao diện
    demo. Kiểm ở đây là để không ghi nhầm dòng của người làm sizing thành ý kiến
    Admin, không phải để bảo vệ.
    """
    try:
        dt = tu_header(request.headers)
    except ValueError as e:
        raise HTTPException(400, f"Danh tính trong header không hợp lệ: {e}")
    if dt is None:
        raise HTTPException(400, f"{viec} cần danh tính — nhập tên ở thanh bên.")
    if dt.vai != "admin":
        raise HTTPException(403, f"Chỉ vai «admin» làm được việc này ({viec}); "
                                 f"đang là «{dt.vai}».")
    return dt


@app.get("/ho-so/{ho_so_id}/bang-admin")
def bang_admin(ho_so_id: int) -> dict:
    d = _can_csdl().doc_bang_admin(ho_so_id)
    if d is None:
        raise HTTPException(404, f"Không có hồ sơ #{ho_so_id}")
    return d


@app.post("/ho-so/{ho_so_id}/ghi-chu-admin")
def ghi_chu_admin(ho_so_id: int, vao: GhiChuAdminVao, request: Request) -> dict:
    from src.luu_tru.kho import KhongCoFinding
    k = _can_csdl()
    dt = _admin(request)
    if k.trang_thai_ho_so(ho_so_id) is None:
        raise HTTPException(404, f"Không có hồ sơ #{ho_so_id}")
    try:
        return k.luu_ghi_chu_admin(ho_so_id, danh_tinh=dt,
                                   muc=[m.model_dump() for m in vao.muc])
    except KhongCoFinding as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))


# --------------------------------------------------- 5.9 bước 2 · quy tắc --
# Đọc `config/rules.yaml` NGUYÊN VĂN mỗi lần: file nằm ở bind-mount (xem
# `docker-compose.yml`), nên người chốt sửa xong là API thấy ngay, KHÔNG phải dựng
# lại image.
#
# CỐ Ý không đệm theo mtime. Phần đắt là `yaml.safe_load` (mỗi chỗ gọi tự parse lại),
# còn đọc 200 KB thì không đáng gì — đệm chỉ đổi lấy một lớp lỗi mới: sửa file rồi
# đọc lại ra bản CŨ vì hai lần ghi rơi vào cùng một nhịp đồng hồ. Mà đúng chỗ này là
# chỗ phải đọc đúng: nó quyết định một đề xuất có được đánh dấu «đã áp» hay không.
def _rules_hien_tai() -> str:
    p = pathlib.Path(DUONG_RULES)
    if not p.exists():
        raise HTTPException(500, f"Không thấy bộ quy tắc ở `{DUONG_RULES}`.")
    return p.read_text(encoding="utf-8")


def _tom_tat_quy_tac(r) -> dict:
    return {"id": r.id, "name": r.name, "type": r.type, "severity": r.severity,
            "scope": r.scope, "enabled": r.enabled,
            "applies_to_equipment": r.applies_to_equipment,
            "khong_danh_gia_duoc": r.khong_danh_gia_duoc()}


@app.get("/quy-tac")
def ds_quy_tac() -> dict:
    rs = RuleSet(yaml.safe_load(_rules_hien_tai()))
    return {"so_quy_tac": len(rs), "chay_duoc": len(rs.runnable()),
            "quy_tac": [_tom_tat_quy_tac(r) for r in rs.rules]}


@app.get("/quy-tac/{ma}")
def chi_tiet_quy_tac(ma: str) -> dict:
    """Chi tiết + NGUYÊN VĂN khối YAML — thứ Admin sẽ sửa và dán lại."""
    van = _rules_hien_tai()
    rs = RuleSet(yaml.safe_load(van))
    r = rs.get(ma)
    if r is None:
        raise HTTPException(404, f"Không có quy tắc `{ma}`")
    d = dict(_tom_tat_quy_tac(r), khoi=doc_khoi(van, ma), raw=r.raw,
             duong_dan=DUONG_RULES)
    # Không có CSDL thì vẫn xem được quy tắc, chỉ là không có đề xuất nào để kể.
    d["de_xuat"] = kho_csdl.ds_de_xuat(rule_ref=ma) if kho_csdl is not None else []
    return d


class KiemQuyTacVao(BaseModel):
    noi_dung_moi: str = Field(min_length=1, max_length=20_000)


class DeXuatVao(KiemQuyTacVao):
    ly_do: str = Field(default="", max_length=10_000)
    ho_so_id: int | None = None


def _kiem(ma: str, noi_dung_moi: str) -> tuple[dict, object]:
    try:
        kq = kiem_de_xuat(_rules_hien_tai(), ma, noi_dung_moi)
    except ValueError as e:
        raise HTTPException(422, str(e))
    # `van_moi` là CẢ file — không trả ra: người chốt sửa file, không dán lại 4605 dòng.
    return {"dat": kq.dat, "loi": kq.loi, "canh_bao": kq.canh_bao, "diff": kq.diff,
            "tom_tat": kq.tom_tat(), "so_quy_tac": kq.so_quy_tac,
            "so_bieu_thuc": kq.so_bieu_thuc,
            "chay_duoc_truoc": kq.chay_duoc_truoc,
            "chay_duoc_sau": kq.chay_duoc_sau}, kq


@app.post("/quy-tac/{ma}/kiem")
def kiem_quy_tac(ma: str, vao: KiemQuyTacVao, request: Request) -> dict:
    """Kiểm thử, KHÔNG lưu gì. Không cần CSDL — chạy được cả trên máy không có CSDL."""
    _admin(request, "Sửa quy tắc")
    return _kiem(ma, vao.noi_dung_moi)[0]


@app.post("/quy-tac/{ma}/de-xuat", status_code=201)
def de_xuat_quy_tac(ma: str, vao: DeXuatVao, request: Request) -> dict:
    """Kiểm rồi LƯU thành đề xuất. Không bao giờ ghi vào `config/rules.yaml`.

    Lưu cả đề xuất KHÔNG đạt (`kiem_hong`): một lần sửa hỏng cũng là dữ liệu —
    nó nói quy tắc ấy khó diễn đạt. Muốn thử nháp thì dùng `/kiem`.
    """
    from src.luu_tru.kho import KhongCoFinding
    k = _can_csdl()
    dt = _admin(request, "Đề xuất sửa quy tắc")
    kq, _ = _kiem(ma, vao.noi_dung_moi)
    van = _rules_hien_tai()
    try:
        cu = doc_khoi(van, ma)
    except KeyError:
        cu = ""
    try:
        r = k.them_de_xuat(
            rule_ref=ma, danh_tinh=dt, noi_dung_cu=cu,
            noi_dung_moi=vao.noi_dung_moi, ly_do=vao.ly_do, ho_so_id=vao.ho_so_id,
            trang_thai="kiem_dat" if kq["dat"] else "kiem_hong",
            ket_qua_kiem=json.dumps(kq, ensure_ascii=False))
    except KhongCoFinding as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    return {"de_xuat": r, "kiem": kq}


@app.get("/de-xuat")
def ds_de_xuat(rule_ref: str = "", ho_so_id: int | None = None,
               trang_thai: str = "") -> dict:
    return {"de_xuat": _can_csdl().ds_de_xuat(
        rule_ref=rule_ref, ho_so_id=ho_so_id, trang_thai=trang_thai)}


class TrangThaiDeXuatVao(BaseModel):
    trang_thai: Literal["cho_kiem", "kiem_dat", "kiem_hong", "da_ap", "tu_choi"]
    bang_chung_eval: str | None = Field(default=None, max_length=10_000)


@app.post("/de-xuat/{de_xuat_id}/trang-thai")
def doi_trang_thai_de_xuat(de_xuat_id: int, vao: TrangThaiDeXuatVao,
                           request: Request) -> dict:
    """Đánh dấu đã áp / từ chối, hoặc gắn bằng chứng eval.

    `da_ap` được ĐỐI CHIẾU với `config/rules.yaml` đang chạy: công cụ không tự ghi
    file nên nó không biết ai đã áp hay chưa, nhưng nó ĐỌC được. Đánh dấu "đã áp"
    trong khi file chưa đổi là ghi một điều sai vào lịch sử quyết định (NT4), nên
    bị từ chối kèm chỗ lệch.
    """
    from src.luu_tru.kho import KhongCoFinding
    k = _can_csdl()
    _admin(request, "Đổi trạng thái đề xuất")
    ds = [d for d in k.ds_de_xuat() if d["id"] == de_xuat_id]
    if not ds:
        raise HTTPException(404, f"Không có đề xuất #{de_xuat_id}")
    d = ds[0]
    if vao.trang_thai == "da_ap":
        try:
            dang_chay = doc_khoi(_rules_hien_tai(), d["rule_ref"])
        except KeyError:
            raise HTTPException(409, f"`config/rules.yaml` đang chạy không còn quy "
                                     f"tắc `{d['rule_ref']}`.")
        if dang_chay.strip() != (d["noi_dung_moi"] or "").strip():
            raise HTTPException(409, (
                f"Chưa áp được: khối `{d['rule_ref']}` trong `{DUONG_RULES}` đang "
                "chạy KHÁC nội dung đề xuất. Sửa file rồi khởi động lại dịch vụ "
                "`copilot`, sau đó đánh dấu lại."))
    try:
        return k.doi_trang_thai_de_xuat(de_xuat_id, vao.trang_thai,
                                        bang_chung_eval=vao.bang_chung_eval)
    except KhongCoFinding as e:
        raise HTTPException(404, str(e))
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
