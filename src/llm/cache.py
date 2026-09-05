"""2.12 — bộ nhớ đệm cho lời gọi model, khoá theo NỘI DUNG lời gọi.

## Vì sao đệm ở tầng LỜI GỌI chứ không phải "theo hash file" như dòng kế hoạch

Đo thật: **~40 giây mỗi lời gọi**, một hồ sơ tốn 191 lượt (C3 71 + C5 120), lượt
đo recall trên 4 hồ sơ mất ~1,1 giờ. Cái đắt là **lời gọi**, không phải việc đọc
`.docx` (mili giây, offline).

Đệm theo hash file chỉ cứu được lượt chạy lại **nguyên hồ sơ, nguyên tham số**.
Đệm theo lời gọi cứu cả những ca hay gặp hơn:

- lượt chạy đứt giữa chừng → chạy lại chỉ tốn phần chưa xong;
- đổi một quy tắc trong `rules.yaml` rồi chạy lại → chỉ những lượt gọi có nội
  dung THAY ĐỔI mới phải gọi lại, phần còn lại lấy trong đệm;
- C3 và C5 dùng chung một cơ chế, không phải viết hai lần.

## Khoá gồm những gì (và vì sao phải đủ)

Khoá là SHA-256 của JSON chuẩn hoá gồm **model · messages · temperature ·
max_tokens · mọi tham số phụ** (`response_format`…). Thiếu bất kỳ thứ nào là đệm
sai: đổi model mà vẫn trả kết quả cũ thì mọi so sánh model đều vô nghĩa.

Nhiệt độ 0–0,2 nên cùng đầu vào vốn đã gần như cùng đầu ra; đệm chỉ làm điều đó
thành chắc chắn, và **không đổi ngữ nghĩa của NT1/NT2** — nội dung trả về vẫn đi
qua đúng đường validate như khi gọi thật.

## Không đệm cái gì

**Lỗi không bao giờ được đệm.** Phản hồi rỗng, `finish_reason=length`, JSON hỏng —
đó là những ca cần gọi lại, đệm chúng sẽ đóng băng một lỗi tạm thời thành vĩnh viễn.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import tempfile
import time
from dataclasses import dataclass

THU_MUC_MAC_DINH = ".cache/llm"
BIEN_TAT = "SIZING_COPILOT_KHONG_CACHE"     # đặt =1 để tắt hẳn


@dataclass
class ThongKeCache:
    trung: int = 0          # lấy được trong đệm, không phải gọi model
    truot: int = 0
    luu: int = 0
    loi: int = 0            # đọc/ghi đệm hỏng — đếm, không nuốt im lặng

    @property
    def tiet_kiem_giay(self) -> float:
        """Ước lượng thời gian tiết kiệm được, theo ~40 giây mỗi lượt đã đo."""
        return self.trung * 40.0

    def as_dict(self) -> dict:
        return {**self.__dict__, "tiet_kiem_giay": round(self.tiet_kiem_giay)}


class BoNhoDem:
    """Đệm nội dung phản hồi model trên đĩa. Mỗi lời gọi một file JSON."""

    def __init__(self, thu_muc: str | pathlib.Path | None = None, *,
                 bat: bool | None = None):
        self.thu_muc = pathlib.Path(thu_muc or THU_MUC_MAC_DINH)
        if bat is None:
            bat = os.environ.get(BIEN_TAT, "").strip() not in ("1", "true", "yes")
        self.bat = bat
        self.tk = ThongKeCache()

    # ------------------------------------------------------------------
    def khoa(self, payload: dict) -> str:
        """SHA-256 của lời gọi đã chuẩn hoá. `sort_keys` để thứ tự khoá không đổi kết quả."""
        chuoi = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(chuoi.encode("utf-8")).hexdigest()

    def _duong_dan(self, khoa: str) -> pathlib.Path:
        # Chia hai cấp thư mục: một lượt chạy sinh hàng nghìn file, để phẳng thì
        # liệt kê thư mục chậm hẳn trên Windows.
        return self.thu_muc / khoa[:2] / f"{khoa}.json"

    def lay(self, khoa: str) -> str | None:
        if not self.bat:
            return None
        p = self._duong_dan(khoa)
        try:
            if not p.exists():
                self.tk.truot += 1
                return None
            noi_dung = json.loads(p.read_text(encoding="utf-8"))["noi_dung"]
        except (OSError, ValueError, KeyError):
            # File đệm hỏng thì coi như không có — KHÔNG làm hỏng lượt chạy.
            self.tk.loi += 1
            self.tk.truot += 1
            return None
        self.tk.trung += 1
        return noi_dung

    def luu(self, khoa: str, noi_dung: str, *, meta: dict | None = None) -> None:
        """Ghi nguyên tử: ghi file tạm rồi đổi tên, để lượt chạy bị ngắt không để lại
        file JSON cụt mà lần sau đọc vào lại tưởng là kết quả thật."""
        if not self.bat:
            return
        p = self._duong_dan(khoa)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            ban_ghi = {"noi_dung": noi_dung, "luc": time.strftime("%Y-%m-%dT%H:%M:%S"),
                       **(meta or {})}
            fd, tam = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(ban_ghi, f, ensure_ascii=False)
            os.replace(tam, p)
            self.tk.luu += 1
        except OSError:
            self.tk.loi += 1        # không ghi được đệm thì vẫn phải chạy tiếp

    # ------------------------------------------------------------------
    def so_ban_ghi(self) -> int:
        if not self.thu_muc.exists():
            return 0
        return sum(1 for _ in self.thu_muc.rglob("*.json"))
