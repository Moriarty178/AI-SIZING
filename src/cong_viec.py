"""3.2 — hàng đợi công việc thẩm định. Thuần Python, KHÔNG phụ thuộc FastAPI.

Tách khỏi `api/` để test được toàn bộ hành vi mà không cần dựng máy chủ, cùng lý
do `src/giao_dien.py` tách khỏi `ui/app.py`.

## Vì sao PHẢI có hàng đợi, không phải "làm cho đẹp"

Đo 2026-09-09 trên máy nội bộ: một tài liệu tốn **~216 lượt gọi model**, và ở mức
song song 12 (điểm bão hoà đo được) đó là **~16 phút**. Không giao diện nào bắt
người dùng đứng chờ 16 phút trong một lời gọi HTTP: proxy sẽ cắt, trình duyệt sẽ
bỏ, và người dùng sẽ bấm lại — nhân đôi tải.

Nên: nhận file rồi trả mã việc NGAY, chạy nền, người dùng hỏi lại bằng mã.

## Mỗi lúc chỉ chạy MỘT tài liệu — đây là con số, không phải sở thích

Bản thân pipeline đã chạy song song `song_song` lượt gọi bên trong. Chạy hai tài
liệu cùng lúc là **2 × 12 = 24 lượt đồng thời**, mà phép đo cùng ngày cho thấy
mức 24 **chậm hơn** mức 12 (138,9 so với 221,2 lượt/phút). Hai việc song song sẽ
khiến cả hai cùng lâu hơn là chạy lần lượt.

Muốn đổi thì đổi `so_viec_song_song`, nhưng phải ĐO lại trước.

## Ghi ra đĩa vì lượt chạy dài hơn tuổi thọ tiến trình

16 phút là đủ dài để container bị khởi động lại giữa chừng. Trạng thái và báo cáo
nằm trong `thu_muc`, nạp lại lúc khởi động — mất kết quả một lượt 16 phút vì một
lần restart là điều không cần phải xảy ra.

Việc đang chạy dở khi tiến trình chết được đánh dấu `gian_doan` chứ KHÔNG âm thầm
để nguyên trạng thái `dang_chay`: một việc `dang_chay` mà không có ai chạy nó là
lời nói dối với người đang chờ (NT4).
"""
from __future__ import annotations

import json
import pathlib
import threading
import time
import traceback
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Callable

THU_MUC_MAC_DINH = pathlib.Path(".cache/cong_viec")

# Mức song song BÊN TRONG một tài liệu. 12 là điểm bão hoà đo được 2026-09-09;
# 24 chậm hơn 12. Đổi thì phải chạy lại `scripts/do_song_song.py`.
SONG_SONG_MAC_DINH = 12

CHO = "cho"
DANG_CHAY = "dang_chay"
XONG = "xong"
HONG = "hong"
GIAN_DOAN = "gian_doan"


@dataclass
class CongViec:
    ma: str
    ten_file: str
    duong_dan: str = ""
    trang_thai: str = CHO
    tao_luc: float = field(default_factory=time.time)
    bat_dau: float | None = None
    ket_thuc: float | None = None
    giai_doan: str = ""          # C3 · C5 · C2 — đang ở bước nào
    da_xong: int = 0
    tong: int = 0
    loi: str = ""
    so_finding: int = 0
    theo_muc_do: dict = field(default_factory=dict)
    # Tuỳ chọn giới hạn chi phí, truyền thẳng vào `pipeline.chay`. Danh sách khoá
    # cho phép nằm ở tầng API — kho việc không tự quyết cái gì hợp lệ.
    tuy_chon: dict = field(default_factory=dict)

    @property
    def xong_roi(self) -> bool:
        return self.trang_thai in (XONG, HONG, GIAN_DOAN)

    @property
    def giay_da_chay(self) -> float:
        if self.bat_dau is None:
            return 0.0
        return (self.ket_thuc or time.time()) - self.bat_dau

    def tien_do(self) -> float | None:
        """0..1, hoặc None khi chưa biết tổng — KHÔNG bịa 0% cho 'chưa rõ'."""
        return (self.da_xong / self.tong) if self.tong else None

    def as_dict(self) -> dict:
        d = asdict(self)
        d["tien_do"] = self.tien_do()
        d["giay_da_chay"] = round(self.giay_da_chay, 1)
        return d


class KhoCongViec:
    """Trạng thái công việc + báo cáo, giữ trên đĩa. An toàn nhiều luồng."""

    def __init__(self, thu_muc: str | pathlib.Path | None = None):
        self.thu_muc = pathlib.Path(thu_muc or THU_MUC_MAC_DINH)
        self._khoa = threading.RLock()
        self._viec: dict[str, CongViec] = {}
        self._nap()

    # ---------------------------------------------------------------- đĩa --
    def _tep(self, ma: str, duoi: str) -> pathlib.Path:
        return self.thu_muc / f"{ma}{duoi}"

    def _nap(self) -> None:
        if not self.thu_muc.exists():
            return
        for p in sorted(self.thu_muc.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
                cv = CongViec(**{k: v for k, v in d.items()
                                 if k in CongViec.__dataclass_fields__})
            except (OSError, ValueError, TypeError):
                continue        # một file hỏng không được giết cả kho
            if cv.trang_thai in (CHO, DANG_CHAY):
                # Không còn luồng nào chạy nó nữa. Nói thật thay vì để người
                # dùng chờ mãi một việc `dang_chay` không có ai làm.
                cv.trang_thai = GIAN_DOAN
                cv.loi = "tiến trình dừng giữa chừng, hãy nộp lại tài liệu"
                cv.ket_thuc = cv.ket_thuc or time.time()
            self._viec[cv.ma] = cv

    def _ghi(self, cv: CongViec) -> None:
        try:
            self.thu_muc.mkdir(parents=True, exist_ok=True)
            tam = self._tep(cv.ma, ".json.tmp")
            tam.write_text(json.dumps(asdict(cv), ensure_ascii=False),
                           encoding="utf-8")
            tam.replace(self._tep(cv.ma, ".json"))
        except OSError:
            pass                # không ghi được thì vẫn chạy, đừng làm hỏng lượt

    # --------------------------------------------------------------- API --
    def them(self, ten_file: str, duong_dan: str,
             tuy_chon: dict | None = None) -> CongViec:
        cv = CongViec(ma=uuid.uuid4().hex[:12], ten_file=ten_file,
                      duong_dan=str(duong_dan), tuy_chon=dict(tuy_chon or {}))
        with self._khoa:
            self._viec[cv.ma] = cv
        self._ghi(cv)
        return cv

    def lay(self, ma: str) -> CongViec | None:
        with self._khoa:
            return self._viec.get(ma)

    def danh_sach(self) -> list[CongViec]:
        with self._khoa:
            return sorted(self._viec.values(), key=lambda c: -c.tao_luc)

    def cap_nhat(self, ma: str, **truong) -> CongViec | None:
        with self._khoa:
            cv = self._viec.get(ma)
            if cv is None:
                return None
            for k, v in truong.items():
                setattr(cv, k, v)
        self._ghi(cv)
        return cv

    def luu_bao_cao(self, ma: str, noi_dung: str) -> None:
        try:
            self.thu_muc.mkdir(parents=True, exist_ok=True)
            self._tep(ma, ".md").write_text(noi_dung, encoding="utf-8")
        except OSError:
            pass

    def bao_cao(self, ma: str) -> str | None:
        try:
            return self._tep(ma, ".md").read_text(encoding="utf-8")
        except OSError:
            return None

    def xoa(self, ma: str) -> bool:
        """Xoá hẳn việc, báo cáo VÀ tài liệu đã nộp.

        Tài liệu sizing là dữ liệu nội bộ của người nộp; giữ lại vô thời hạn trên
        máy chủ là một quyết định phải có người chọn, không phải mặc định.
        """
        with self._khoa:
            cv = self._viec.pop(ma, None)
        if cv is None:
            return False
        for p in (self._tep(ma, ".json"), self._tep(ma, ".md"),
                  pathlib.Path(cv.duong_dan) if cv.duong_dan else None):
            try:
                if p is not None:
                    p.unlink(missing_ok=True)
            except OSError:
                pass
        return True


class BoChay:
    """Chạy công việc lần lượt trên luồng nền.

    `ham_chay` tiêm được để test không cần model: chữ ký giống `pipeline.chay`.
    """

    def __init__(self, kho: KhoCongViec, *, ham_chay: Callable | None = None,
                 song_song: int = SONG_SONG_MAC_DINH,
                 so_viec_song_song: int = 1):
        self.kho = kho
        self.song_song = song_song
        self.so_viec_song_song = max(1, int(so_viec_song_song))
        self._ham_chay = ham_chay
        self._hang: deque[str] = deque()
        self._khoa = threading.Lock()
        self._co_viec = threading.Condition(self._khoa)
        self._luong: list[threading.Thread] = []
        self._dung = False

    def _chay_that(self):
        if self._ham_chay is not None:
            return self._ham_chay
        from .pipeline import chay          # nhập muộn: test không cần model
        return chay

    # ------------------------------------------------------------------
    def bat_dau(self) -> None:
        if self._luong:
            return
        for i in range(self.so_viec_song_song):
            t = threading.Thread(target=self._vong, name=f"bo-chay-{i}",
                                 daemon=True)
            t.start()
            self._luong.append(t)

    def dung(self, cho_giay: float = 5.0) -> None:
        with self._co_viec:
            self._dung = True
            self._co_viec.notify_all()
        for t in self._luong:
            t.join(timeout=cho_giay)
        self._luong.clear()

    def nop(self, cv: CongViec) -> None:
        with self._co_viec:
            self._hang.append(cv.ma)
            self._co_viec.notify()

    def cho_rong(self, giay: float = 30.0) -> bool:
        """Chờ hàng đợi cạn. Dùng trong test; không dùng trên đường phục vụ."""
        het = time.time() + giay
        while time.time() < het:
            with self._khoa:
                con = bool(self._hang)
            dang = any(c.trang_thai == DANG_CHAY for c in self.kho.danh_sach())
            if not con and not dang:
                return True
            time.sleep(0.01)
        return False

    # ------------------------------------------------------------------
    def _vong(self) -> None:
        while True:
            with self._co_viec:
                while not self._hang and not self._dung:
                    self._co_viec.wait(timeout=0.5)
                if self._dung and not self._hang:
                    return
                ma = self._hang.popleft()
            self._lam(ma)

    def _lam(self, ma: str) -> None:
        cv = self.kho.lay(ma)
        if cv is None:
            return
        self.kho.cap_nhat(ma, trang_thai=DANG_CHAY, bat_dau=time.time())

        def tien_do(giai_doan, i, tong, _nhan):
            self.kho.cap_nhat(ma, giai_doan=giai_doan, da_xong=i, tong=tong)

        tuy_chon = dict(cv.tuy_chon)
        song_song = int(tuy_chon.pop("song_song", None) or self.song_song)
        try:
            kq = self._chay_that()(cv.duong_dan, on_tien_do=tien_do,
                                   song_song=song_song, **tuy_chon)
            self.kho.luu_bao_cao(ma, kq.bao_cao())
            muc: dict[str, int] = {}
            for f in kq.findings:
                muc[f.severity] = muc.get(f.severity, 0) + 1
            self.kho.cap_nhat(ma, trang_thai=XONG, ket_thuc=time.time(),
                              so_finding=len(kq.findings), theo_muc_do=muc,
                              giai_doan="")
        except Exception as e:
            # Một tài liệu hỏng KHÔNG được giết luồng chạy: các việc còn lại
            # trong hàng đợi vẫn phải tới lượt.
            self.kho.cap_nhat(
                ma, trang_thai=HONG, ket_thuc=time.time(),
                loi=f"{type(e).__name__}: {e}"[:300])
            traceback.print_exc()
