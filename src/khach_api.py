"""3.3 — khách gọi API thẩm định. Chỉ thư viện chuẩn, KHÔNG phụ thuộc Streamlit.

Tách khỏi `ui/app.py` cùng lý do `giao_dien.py` tách: test được mà không cần dựng
Streamlit, và sau này còn dùng lại được cho web nội bộ (mục 3.3 bản kế hoạch).

## Vì sao giao diện phải đi qua API thay vì gọi thẳng `pipeline.chay`

Một tài liệu tốn ~16 phút. `ui/app.py` bản cũ gọi thẳng `chay()` và **chặn cả
phiên Streamlit** suốt chừng ấy: đóng tab là mất trắng, tải lại trang là chạy
lại từ đầu, và mỗi người dùng chiếm một tiến trình.

Qua API thì việc chạy nền, người dùng cầm **mã việc** — đóng tab, mở lại, tra
bằng mã vẫn thấy kết quả.

## Ép UTF-8 ở MỌI chỗ đọc

`urllib` trả `bytes`; để Python tự đoán mã là mở đường cho đúng lỗi đã mất một
lượt truy vết ngày 2026-09-09 (`ChÆ°a cÃ³` thay vì `Chưa có`, do đường ống trên
Windows giải mã theo cp1252). Ở đây mọi chỗ `.decode("utf-8")` tường minh.

## KHÔNG đi qua proxy công ty

Dịch vụ thẩm định nằm ở `localhost` hoặc trong mạng nội bộ; proxy công ty không
bao giờ là đường đúng để tới nó. Mà `urllib` thì mặc định ĐỌC `HTTP_PROXY` /
`HTTPS_PROXY` của môi trường, nên một biến proxy đặt sai ở cửa sổ lệnh là hỏng
lời gọi tới chính máy mình.

Đã gặp thật 2026-09-16: biến proxy mang giá trị bọc ngoặc vuông
(`[http://…:3128]`), `urllib` lấy `[http` làm scheme rồi báo
`unknown url type: [http` — trong khi địa chỉ người dùng gõ hoàn toàn đúng, nên
thông báo lỗi trỏ sai chỗ. Ở đây dựng `opener` riêng với `ProxyHandler({})`:
lời gọi luôn đi thẳng, bất kể môi trường có gì.

## KHÔNG có đường lùi "chạy thẳng khi API chết"

Nghe thì tiện, nhưng đường lùi ấy sẽ chặn giao diện 16 phút — đúng cái mà module
này sinh ra để bỏ. API không với tới được thì NÓI RA kèm lệnh khởi động, đừng âm
thầm rơi về lối cũ (NT4).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from urllib.parse import quote, urlencode

BIEN_DIA_CHI = "SIZING_COPILOT_API"
DIA_CHI_MAC_DINH = "http://localhost:8000"

# Chỉ để BÁO cho người dùng biết môi trường đang đặt gì. Không dùng để định tuyến —
# xem `KhachAPI._mo`.
BIEN_PROXY = ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY")


def proxy_dang_dat() -> list[str]:
    """Tên các biến proxy đang có giá trị, để nói ra khi kết nối hỏng.

    Khử trùng không phân biệt hoa thường: trên Windows `os.environ` không phân
    biệt hoa thường, nên đặt `HTTP_PROXY` là thấy luôn cả `http_proxy` — in cả
    hai chỉ làm thông báo dài thêm mà không thêm thông tin.
    """
    ra: dict[str, str] = {}
    for b in BIEN_PROXY:
        if os.environ.get(b, "").strip():
            ra.setdefault(b.upper(), b)
    return list(ra.values())


def dia_chi_mac_dinh() -> str:
    return (os.environ.get(BIEN_DIA_CHI) or DIA_CHI_MAC_DINH).rstrip("/")


class LoiAPI(RuntimeError):
    """Gọi API hỏng. `ma_http` = None nghĩa là không kết nối được."""

    def __init__(self, thong_diep: str, ma_http: int | None = None):
        super().__init__(thong_diep)
        self.ma_http = ma_http


@dataclass
class SucKhoe:
    song: bool
    thong_diep: str = ""
    commit: str = ""
    phien_ban: str = ""
    model_san_sang: bool = False
    ghi_chu_model: str = ""
    dang_cho: int = 0
    tho: dict = field(default_factory=dict)


def _multipart(ten_truong: str, ten_file: str, noi_dung: bytes,
               truong: dict[str, str]) -> tuple[bytes, str]:
    """Gói multipart bằng tay — để không phải thêm một phụ thuộc chỉ vì upload."""
    ranh = "----sizing-copilot-" + uuid.uuid4().hex
    phan: list[bytes] = []
    for k, v in truong.items():
        if v is None or v == "":
            continue
        phan += [f"--{ranh}\r\n".encode(),
                 f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode(),
                 str(v).encode("utf-8"), b"\r\n"]
    phan += [
        f"--{ranh}\r\n".encode(),
        (f'Content-Disposition: form-data; name="{ten_truong}"; '
         f'filename="{ten_file}"\r\n').encode("utf-8"),
        b"Content-Type: application/vnd.openxmlformats-officedocument."
        b"wordprocessingml.document\r\n\r\n",
        noi_dung, b"\r\n", f"--{ranh}--\r\n".encode()]
    return b"".join(phan), f"multipart/form-data; boundary={ranh}"


class KhachAPI:
    def __init__(self, dia_chi: str | None = None, *, timeout: float = 15.0,
                 danh_tinh=None):
        self.dia_chi = (dia_chi or dia_chi_mac_dinh()).rstrip("/")
        # 5.0a — `src.luu_tru.danh_tinh.DanhTinh` hoặc None. Gửi trong header ở
        # MỌI yêu cầu, mã hoá phần trăm (xem module đó vì sao).
        self.danh_tinh = danh_tinh
        self.timeout = timeout
        # `ProxyHandler({})` = KHÔNG proxy, kể cả khi môi trường có đặt. Dịch vụ
        # thẩm định là localhost/nội bộ; đi vòng qua proxy công ty thì tốt nhất
        # là chậm, tệ nhất là hỏng vì một biến môi trường đặt sai.
        self._mo = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    # ------------------------------------------------------------------
    def _goi(self, duong: str, *, method: str = "GET", du_lieu: bytes | None = None,
             kieu: str = "", tho: bool = False):
        req = urllib.request.Request(f"{self.dia_chi}{duong}", data=du_lieu,
                                     method=method)
        if kieu:
            req.add_header("Content-Type", kieu)
        if self.danh_tinh is not None:
            from src.luu_tru.danh_tinh import thanh_header
            for k, v in thanh_header(self.danh_tinh).items():
                req.add_header(k, v)
        try:
            with self._mo.open(req, timeout=self.timeout) as r:
                van = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            chi_tiet = ""
            try:
                chi_tiet = json.loads(e.read().decode("utf-8")).get("detail", "")
            except Exception:
                pass
            raise LoiAPI(chi_tiet or f"HTTP {e.code}", e.code) from e
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            them = ""
            if "unknown url type" in str(e) and (bp := proxy_dang_dat()):
                # Lời gọi này KHÔNG đi qua proxy, nên biến proxy hỏng không còn
                # làm hỏng nó nữa. Vẫn nêu tên biến: gặp lại thông báo này thì
                # gần như chắc chắn là môi trường, không phải địa chỉ đã gõ.
                them = (f" · môi trường đang đặt {', '.join(bp)} — kiểm giá trị, "
                        "bọc ngoặc vuông là hỏng")
            raise LoiAPI(f"không kết nối được {self.dia_chi}: {e}{them}", None) from e
        return van if tho else json.loads(van)

    # ------------------------------------------------------------------
    def suc_khoe(self) -> SucKhoe:
        """KHÔNG ném lỗi: giao diện cần vẽ được cả khi API chết."""
        try:
            d = self._goi("/health")
        except LoiAPI as e:
            return SucKhoe(song=False, thong_diep=str(e))
        return SucKhoe(song=True, commit=d.get("commit", ""),
                       phien_ban=d.get("phien_ban", ""),
                       model_san_sang=bool(d.get("model_san_sang")),
                       ghi_chu_model=d.get("ghi_chu_model", ""),
                       dang_cho=int(d.get("dang_cho") or 0), tho=d)

    def nop(self, noi_dung: bytes, ten: str, **tuy_chon) -> dict:
        than, kieu = _multipart("file", ten, noi_dung,
                                {k: v for k, v in tuy_chon.items()})
        return self._goi("/review", method="POST", du_lieu=than, kieu=kieu)

    def ds_ho_so(self) -> list[dict]:
        return self._goi("/ho-so")["ho_so"]

    def ho_so(self, ho_so_id: int) -> dict:
        return self._goi(f"/ho-so/{int(ho_so_id)}")

    def finding_ho_so(self, ho_so_id: int, fb_id: int) -> dict:
        return self._goi(f"/ho-so/{int(ho_so_id)}/finding/{int(fb_id)}")

    def ghi_lan_sua(self, ho_so_id: int, fb_id: int, noi_dung_sua: str,
                    noi_dung_goc: str = "") -> dict:
        than = json.dumps({"noi_dung_sua": noi_dung_sua, "noi_dung_goc": noi_dung_goc},
                          ensure_ascii=False).encode("utf-8")
        return self._goi(f"/ho-so/{int(ho_so_id)}/finding/{int(fb_id)}/lan-sua",
                         method="POST", du_lieu=than,
                         kieu="application/json; charset=utf-8")

    def bang_admin(self, ho_so_id: int) -> dict:
        """5.6 — bảng lịch sử sửa lỗi cho Admin."""
        return self._goi(f"/ho-so/{int(ho_so_id)}/bang-admin")

    def ghi_chu_admin(self, ho_so_id: int, muc: list[dict]) -> dict:
        """5.9 — ba cột Admin; chỉ gửi những dòng ĐÃ ĐỔI."""
        than = json.dumps({"muc": muc}, ensure_ascii=False).encode("utf-8")
        return self._goi(f"/ho-so/{int(ho_so_id)}/ghi-chu-admin", method="POST",
                         du_lieu=than, kieu="application/json; charset=utf-8")

    def bao_loi(self, ho_so_id: int, ly_do: str, *, finding_baseline_id: int | None = None,
                finding_phat_sinh_id: int | None = None) -> dict:
        """5.4 — báo một dòng là lỗi của hệ thống (đúng một trong hai id)."""
        than = json.dumps({"ly_do": ly_do, "finding_baseline_id": finding_baseline_id,
                           "finding_phat_sinh_id": finding_phat_sinh_id},
                          ensure_ascii=False).encode("utf-8")
        return self._goi(f"/ho-so/{int(ho_so_id)}/bao-loi", method="POST", du_lieu=than,
                         kieu="application/json; charset=utf-8")

    def ds_bao_loi(self, ho_so_id: int) -> list[dict]:
        return self._goi(f"/ho-so/{int(ho_so_id)}/bao-loi")["bao_loi"]

    # ----------------------------------------------------- 5.9 bước 2 · quy tắc --
    def quy_tac(self, ma: str) -> dict:
        """Chi tiết một quy tắc + NGUYÊN VĂN khối YAML + các đề xuất của nó."""
        return self._goi(f"/quy-tac/{quote(str(ma), safe='')}")

    def kiem_quy_tac(self, ma: str, noi_dung_moi: str) -> dict:
        """Kiểm thử một sửa đổi, KHÔNG lưu."""
        than = json.dumps({"noi_dung_moi": noi_dung_moi},
                          ensure_ascii=False).encode("utf-8")
        return self._goi(f"/quy-tac/{quote(str(ma), safe='')}/kiem", method="POST",
                         du_lieu=than, kieu="application/json; charset=utf-8")

    def de_xuat_quy_tac(self, ma: str, noi_dung_moi: str, *, ly_do: str = "",
                        ho_so_id: int | None = None) -> dict:
        than = json.dumps({"noi_dung_moi": noi_dung_moi, "ly_do": ly_do,
                           "ho_so_id": ho_so_id}, ensure_ascii=False).encode("utf-8")
        return self._goi(f"/quy-tac/{quote(str(ma), safe='')}/de-xuat", method="POST",
                         du_lieu=than, kieu="application/json; charset=utf-8")

    def ds_de_xuat(self, *, rule_ref: str = "", trang_thai: str = "") -> list[dict]:
        q = urlencode({k: v for k, v in
                       (("rule_ref", rule_ref), ("trang_thai", trang_thai)) if v})
        return self._goi("/de-xuat" + (f"?{q}" if q else ""))["de_xuat"]

    def trang_thai_de_xuat(self, de_xuat_id: int, trang_thai: str, *,
                           bang_chung_eval: str | None = None) -> dict:
        than = json.dumps({"trang_thai": trang_thai,
                           "bang_chung_eval": bang_chung_eval},
                          ensure_ascii=False).encode("utf-8")
        return self._goi(f"/de-xuat/{int(de_xuat_id)}/trang-thai", method="POST",
                         du_lieu=than, kieu="application/json; charset=utf-8")

    def viec(self, ma: str) -> dict:
        return self._goi(f"/result/{ma}")

    def bao_cao(self, ma: str) -> str:
        return self._goi(f"/result/{ma}/bao-cao", tho=True)

    def findings(self, ma: str) -> dict:
        return self._goi(f"/result/{ma}/findings")

    def phan_hoi(self, ma: str) -> dict:
        return self._goi(f"/result/{ma}/phan-hoi")

    def luu_phan_hoi(self, ma: str, ds: list[dict]) -> dict:
        du_lieu = json.dumps({"phan_hoi": ds}, ensure_ascii=False).encode("utf-8")
        return self._goi(f"/result/{ma}/phan-hoi", method="POST",
                         du_lieu=du_lieu, kieu="application/json")

    def nhat_ky(self) -> str:
        return self._goi("/phan-hoi/nhat-ky", tho=True)

    def danh_sach(self) -> list[dict]:
        return self._goi("/jobs").get("cong_viec", [])

    def xoa(self, ma: str) -> bool:
        self._goi(f"/result/{ma}", method="DELETE")
        return True
