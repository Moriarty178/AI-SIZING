"""Model GIẢ để diễn tập đường chạy thật ở laptop — KHÔNG phải để lấy kết quả.

## Vì sao cần

Lượt đo recall (B1) chạy 1,1–2,4 giờ trong mạng nội bộ ở ~40 giây mỗi lời gọi.
Một lỗi ghép nối làm hỏng lượt chạy ở phút thứ 50 là mất đúng chừng ấy **giờ mạng
nội bộ** — tài nguyên khan hiếm nhất của dự án.

Đến 2026-09-05, đường `C1 → C3 → C4 → C5 → C7 → đối chiếu nhãn → ghi báo cáo`
**chưa từng được chạy trọn trên `.docx` THẬT mà không cần model**: `test_pipeline.py`
dùng tài liệu tổng hợp, còn `run_eval.py` đòi model thật. Loại lỗi chỉ lộ ở chỗ các
thành phần gặp nhau là có thật — 2026-09-05 vừa bắt được một cái: C7 xếp finding
theo `id` nên vứt mất thứ tự ưu tiên mà C2 dựng.

## Nó giả cái gì, và KHÔNG giả cái gì

Giả **nội dung** model trả về. KHÔNG giả bất cứ thứ gì khác: vẫn là `.docx` thật,
`rules.yaml` thật, C3/C4/C5/C7 thật, `run_eval` thật, cùng một điểm dừng và cùng
một đường ghi báo cáo.

Hai chỗ phải sinh khéo, nếu không diễn tập sẽ chỉ đi vào nhánh "hỏng":

- **`dong` của C3** phải là nhãn dòng CÓ THẬT thì code mới neo được ô. Lấy ngay từ
  danh sách `«...»` trong mô tả trường.
- **`trich_dan_tai_lieu` của C5** phải là câu CÓ THẬT trong tài liệu thì mới qua
  cổng chống bịa. Lấy một câu ngẫu nhiên từ chính thông điệp gửi vào.

Nhờ vậy diễn tập đi qua **cả nhánh chấp nhận lẫn nhánh loại bỏ**, chứ không phải
chỉ nhánh loại bỏ như khi trả chuỗi ngẫu nhiên.

## Ba chế độ hỏng bơm được — đều là lỗi ĐÃ GẶP THẬT

`ty_le_rong` (phản hồi rỗng vì `reasoning_content` ăn hết `max_tokens` — đã làm
hỏng 7/53 rồi 2/94 lượt gọi), `ty_le_sai_luoc_do` (JSON không hợp lược đồ), và
`ty_le_loi_mang`. Bơm để chứng minh **một lượt gọi hỏng không kéo sập cả lượt chạy**.

⚠️ Kết quả của lượt diễn tập KHÔNG phải số đo chất lượng. Mọi báo cáo sinh ra từ
đây đều bị đóng dấu, và `run_eval --gia-lap` từ chối chạy trên tập test.
"""
from __future__ import annotations

import random
import re
import types
import typing
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

from src.llm.cache import BoNhoDem
from src.llm.client import ExtractionFailed, LLMError

# Nhãn dòng mà C3 đưa vào mô tả trường dưới dạng «...»
_TUY_CHON = re.compile(r"«([^»]{1,120})»")
# Câu trong tài liệu: đủ dài để không trùng ngẫu nhiên, đủ ngắn để còn là một câu
_CAU = re.compile(r"[^\n.;•|]{25,160}")

_TU_TRICH_DAN = ("trich_dan", "quote", "cau_trich", "nguyen_van")


@dataclass
class ThongKeGiaLap:
    luot_goi: int = 0
    bom_rong: int = 0
    bom_sai_luoc_do: int = 0
    bom_loi_mang: int = 0
    truong_da_sinh: int = 0
    trich_dan_that: int = 0     # lấy được câu THẬT từ tài liệu -> qua được cổng neo
    trich_dan_bia: int = 0      # cố ý sinh câu không có trong tài liệu

    def tom_tat(self) -> str:
        return (f"{self.luot_goi} lượt gọi giả · {self.truong_da_sinh} trường đã sinh · "
                f"trích dẫn thật {self.trich_dan_that} / bịa {self.trich_dan_bia} · "
                f"bơm hỏng: rỗng {self.bom_rong}, sai lược đồ {self.bom_sai_luoc_do}, "
                f"lỗi mạng {self.bom_loi_mang}")


class ClientGiaLap:
    """Thay đúng chỗ `LLMClient` đứng. Sinh kết quả HỢP LỆ theo lược đồ được hỏi.

    Sinh theo lược đồ chứ không theo danh sách trường viết sẵn: thêm một trường vào
    `NhanXetDinhTinh` hay đổi lược đồ bảng của C3 thì diễn tập tự bao phủ luôn, không
    phải sửa file này. Nếu sinh theo danh sách cứng thì đúng những thay đổi nguy hiểm
    nhất lại là thứ diễn tập KHÔNG chạm tới.
    """

    def __init__(self, *, seed: int = 7, ty_le_rong: float = 0.0,
                 ty_le_sai_luoc_do: float = 0.0, ty_le_loi_mang: float = 0.0,
                 ty_le_trich_dan_bia: float = 0.25):
        self.rnd = random.Random(seed)
        self.ty_le_rong = ty_le_rong
        self.ty_le_sai_luoc_do = ty_le_sai_luoc_do
        self.ty_le_loi_mang = ty_le_loi_mang
        self.ty_le_trich_dan_bia = ty_le_trich_dan_bia
        self.tk = ThongKeGiaLap()
        # Giữ đúng bề mặt của `LLMClient` để không chỗ nào phải biết mình đang giả.
        self.chat_model = "GIA-LAP"
        self.vision_model = "GIA-LAP"
        self.cache = BoNhoDem(bat=False)     # đệm kết quả giả là vô nghĩa
        self.last_attempts = 1
        self.last_schema_path = "json_schema"
        self.last_schema_error = ""

    # ------------------------------------------------------------------
    def chat(self, messages: list[dict], *, model: str | None = None,
             max_tokens: int = 4000, **extra) -> str:
        self.tk.luot_goi += 1
        self._bom_loi()
        return "OK"

    def extract(self, schema: type[BaseModel], messages: list[dict], *,
                model: str | None = None, max_retries: int = 3,
                max_tokens: int = 4000) -> BaseModel:
        self.tk.luot_goi += 1
        self._bom_loi()
        van_ban = _van_ban(messages)
        if self.rnd.random() < self.ty_le_sai_luoc_do:
            self.tk.bom_sai_luoc_do += 1
            raise ExtractionFailed(max_retries, "trường bắt buộc bị thiếu", "{}")
        try:
            return self._sinh(schema, van_ban)
        except ValidationError as e:      # lược đồ có ràng buộc mà bộ sinh chưa biết
            raise ExtractionFailed(1, f"bộ sinh giả lập không dựng nổi lược đồ: {e}",
                                   "") from e

    def _bom_loi(self) -> None:
        if self.rnd.random() < self.ty_le_rong:
            self.tk.bom_rong += 1
            raise LLMError("phản hồi rỗng (finish_reason=length) — bơm bởi diễn tập")
        if self.rnd.random() < self.ty_le_loi_mang:
            self.tk.bom_loi_mang += 1
            raise LLMError("lỗi mạng giả lập — bơm bởi diễn tập")

    # ------------------------------------------------------------------
    def _sinh(self, schema: type[BaseModel], van_ban: str) -> BaseModel:
        gia_tri = {}
        for ten, f in schema.model_fields.items():
            self.tk.truong_da_sinh += 1
            gia_tri[ten] = self._gia_tri(ten, f.annotation,
                                         str(f.description or ""), van_ban)
        return schema(**gia_tri)

    def _gia_tri(self, ten: str, kieu, mo_ta: str, van_ban: str):
        goc = typing.get_origin(kieu)
        args = typing.get_args(kieu)

        if goc is typing.Literal:
            return self.rnd.choice(args)
        if goc in (typing.Union, types.UnionType):
            khong_none = [a for a in args if a is not type(None)]
            if type(None) in args and self.rnd.random() < 0.3:
                return None
            return self._gia_tri(ten, khong_none[0], mo_ta, van_ban)
        if goc in (list, set, tuple):
            trong = args[0] if args else str
            return [self._gia_tri(ten, trong, mo_ta, van_ban)
                    for _ in range(self.rnd.randint(1, 2))]
        if goc is dict:
            return {}
        if isinstance(kieu, type) and issubclass(kieu, BaseModel):
            return self._sinh(kieu, van_ban)
        if kieu is bool:
            return self.rnd.random() < 0.5
        if kieu is int:
            return self.rnd.choice([2, 4, 8, 16, 32, 64, 128])
        if kieu is float:
            return self.rnd.choice([0.8, 1.2, 16.0, 143.5, 1024.0])

        return self._chuoi(ten, mo_ta, van_ban)

    def _chuoi(self, ten: str, mo_ta: str, van_ban: str) -> str:
        """Chuỗi phải NEO ĐƯỢC ở hai chỗ, nếu không diễn tập chỉ đi nhánh bị loại."""
        # C3: mô tả liệt kê các nhãn dòng có thật dưới dạng «...» — chọn một cái.
        tuy_chon = _TUY_CHON.findall(mo_ta)
        if tuy_chon:
            return self.rnd.choice(tuy_chon)

        # C5: trích dẫn phải là câu CÓ THẬT trong tài liệu mới qua cổng chống bịa.
        if any(k in ten.lower() for k in _TU_TRICH_DAN):
            if self.rnd.random() < self.ty_le_trich_dan_bia:
                self.tk.trich_dan_bia += 1
                return "câu này cố ý không có trong tài liệu để thử cổng chống bịa"
            cau = _CAU.findall(van_ban)
            if cau:
                self.tk.trich_dan_that += 1
                return self.rnd.choice(cau).strip()
            return ""
        return f"nội dung giả lập cho trường `{ten}`"


def _van_ban(messages: list[dict]) -> str:
    """Gộp phần chữ của mọi thông điệp — nguồn để lấy câu trích dẫn có thật."""
    ra = []
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            ra.append(c)
        elif isinstance(c, list):        # thông điệp có ảnh (2.3)
            ra += [p.get("text", "") for p in c if p.get("type") == "text"]
    return "\n".join(ra)
