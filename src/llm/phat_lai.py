"""5.3 — DÙNG LẠI câu trả lời model của lần thẩm định trước cho phần tài liệu không đổi.

## Cách chọn: theo chính nội dung model được đọc, không theo "phần đã sửa"

Mỗi lượt hỏi model được khoá bằng MỌI thứ đổi được câu trả lời: lược đồ, lời nhắc, đoạn
tài liệu gửi kèm, model, nhiệt độ, ngân sách token. Lần thẩm định lại chạy TRỌN pipeline
trên bản mới; lượt nào ra đúng khoá của lần trước thì lấy lại câu trả lời cũ, không gọi.

Không cần một bước riêng "tìm phần đã sửa rồi chọn lượt gọi": lượt nào đọc đoạn đã sửa thì
khoá của nó tự khác. Nhờ vậy C4 và mọi bước kiểm bằng code vẫn chạy lại TOÀN BỘ trên tập
trường đã hợp nhất — đúng yêu cầu của 5.3, và không có đường hợp nhất tự viết nào để sai.

## Bỏ vị trí khỏi khoá

Ngữ cảnh gửi model gắn nhãn vị trí cho từng phần tử (`[Mục IV.1, trang 8]`,
`[BẢNG #93 · …]`). Thêm MỘT đoạn ở trang 3 làm số trang và chỉ số của mọi phần tử phía
sau dịch đi — để nguyên nhãn trong khoá thì cả tài liệu phía sau phải hỏi lại dù nội dung
không đổi chữ nào. Nên khoá bỏ nhãn vị trí.

Làm vậy an toàn vì câu trả lời của các lượt này KHÔNG chứa vị trí: C3 và C5 trả nguyên
văn giá trị/trích dẫn, rồi CODE neo lại vào bản MỚI. Ngoại lệ duy nhất là nhận diện phân
hệ: nó trả `bang_cau_hinh` là chỉ số bảng — lượt đó giữ nguyên vị trí trong khoá
(`giu_vi_tri=True`), nếu không một ảnh chèn thêm sẽ làm mốc phân hệ trỏ lệch một bảng.

## Chặt: C5 đọc cả tài liệu nên sửa bất kỳ đâu là hỏi lại toàn bộ C5

Người dùng chốt 2026-09-17: làm CHẶT, và ĐO xem nếu C5 cấp phân hệ chỉ hỏi lại khi vùng
của phân hệ đó hoặc phần chung đổi thì có kết luận nào khác không (`ghi_do_c5`). Số đo đó
để quyết lần sau — không dùng để bỏ lượt gọi nào ở đây.

## Không dùng lại cái gì

Lượt hỏng (hết lượt thử, lỗi mạng) không được ghi — lần sau hỏi lại. Bản ghi cũ không
còn hợp lược đồ (đổi code) thì hỏi lại, không cố đọc.
"""
from __future__ import annotations

import hashlib
import json
import re
import threading
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError

PHIEN_BAN = 1
TOI_DA_VI_DU = 40

# Nhãn vị trí do C3 (`Extractor._ve_phan_tu`) và C5 (`QualitativeValidator.ngu_canh`)
# gắn vào ngữ cảnh. Dạng `Element.location`: «Mục X, trang Y» · «Mục X» · «trang Y» ·
# «phần tử #N».
_NHAN_BANG = re.compile(r"\[BẢNG #\d+ · [^\]\n]*\]")
_NHAN_DONG = re.compile(r"(?m)^\[(?:Mục [^\]\n]*|trang \d+|phần tử #\d+)\] ")
_SO_BANG = re.compile(r"BẢNG #\d+")
# Tên lược đồ cũng mang chỉ số: C3 hỏi bảng bằng lớp `GanBang{e.index}`
# (`bang.luoc_do_bang`). Bỏ đuôi số là an toàn cho mọi lớp: hai lược đồ khác trường
# (`TrichCPU1` / `TrichCPU2`) vẫn khác khoá vì nội dung JSON Schema nằm trong khoá.
_DUOI_SO = re.compile(r"\d+$")


def bo_vi_tri(s: str) -> str:
    """Bỏ nhãn vị trí khỏi một đoạn lời nhắc — chỉ để dựng khoá, không gửi model."""
    s = _NHAN_BANG.sub("[BẢNG]", s)
    s = _NHAN_DONG.sub("[] ", s)
    return _SO_BANG.sub("BẢNG #", s)


def khoa_loi_goi(schema: type[BaseModel], messages: list[dict], *, model, nhiet_do,
                 max_tokens, giu_vi_tri: bool = False) -> str:
    tin = [{**m, "content": (m.get("content") if giu_vi_tri
                             or not isinstance(m.get("content"), str)
                             else bo_vi_tri(m["content"]))} for m in messages]
    js = schema.model_json_schema()
    ten = schema.__name__
    if not giu_vi_tri:
        ten = _DUOI_SO.sub("", ten)
        if js.get("title") == schema.__name__:
            js["title"] = ten
    goi = {"luoc_do": ten, "json_schema": js,
           "messages": tin, "model": model, "nhiet_do": nhiet_do,
           "max_tokens": max_tokens, "giu_vi_tri": giu_vi_tri}
    chuoi = json.dumps(goi, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(chuoi.encode("utf-8")).hexdigest()


@dataclass
class _Dem:
    dung_lai: int = 0
    goi_moi: int = 0
    goi_moi_vi_du: list[str] = field(default_factory=list)


class PhatLai:
    """Ghi lại mọi câu trả lời model của lượt chạy này; dùng lại câu trả lời của lượt
    trước khi khoá khớp. Một đối tượng cho một lượt chạy, an toàn nhiều luồng."""

    def __init__(self, cu: dict | None = None, *, tu_viec: str = ""):
        # Tệp bản ghi đọc từ đĩa: sai kiểu ở đâu cũng coi như KHÔNG có — hỏi model lại,
        # không được làm chết luồng chạy việc.
        hop_le = (isinstance(cu, dict) and cu.get("phien_ban") == PHIEN_BAN
                  and all(isinstance(cu.get(k, {}), dict)
                          for k in ("phan_hoi", "do_c5", "vung")))
        cu = cu if hop_le else {}
        self.co_ban_cu = hop_le
        self.tu_viec = tu_viec if hop_le else ""
        self._cu: dict[str, str] = dict(cu.get("phan_hoi") or {})
        self._cu_do: dict[str, dict] = dict(cu.get("do_c5") or {})
        self._cu_vung: dict[str, str] = dict(cu.get("vung") or {})
        self._moi: dict[str, str] = {}
        self._moi_do: dict[str, dict] = {}
        self._vung: dict[str, str] = {}
        self._khoa = threading.Lock()
        self._dem = {"c3": _Dem(), "c5": _Dem()}

    # ------------------------------------------------------------------
    def goi(self, client, schema: type[BaseModel], messages: list[dict], *,
            thanh_phan: str, nhan: str = "", giu_vi_tri: bool = False, **kw):
        """Thay cho `client.extract(schema, messages, **kw)`. Lỗi của client đi thẳng
        ra ngoài như cũ — bên gọi đã có đường xuống cấp cho nó (NT4)."""
        return self.goi_kem_nguon(client, schema, messages, thanh_phan=thanh_phan,
                                  nhan=nhan, giu_vi_tri=giu_vi_tri, **kw)[0]

    def goi_kem_nguon(self, client, schema: type[BaseModel], messages: list[dict], *,
                      thanh_phan: str, nhan: str = "", giu_vi_tri: bool = False,
                      **kw) -> tuple[BaseModel, bool]:
        """Như `goi`, kèm cờ câu trả lời có phải dùng lại không — phần đo của C5 cần
        biết từng lượt, mà đếm chênh bộ đếm thì sai khi chạy song song."""
        k = khoa_loi_goi(schema, messages,
                         model=kw.get("model") or getattr(client, "chat_model", None),
                         nhiet_do=getattr(client, "temperature", None),
                         max_tokens=kw.get("max_tokens"), giu_vi_tri=giu_vi_tri)
        dem = self._dem.setdefault(thanh_phan, _Dem())
        cu = self._cu.get(k)
        if cu is not None:
            try:
                kq = schema.model_validate_json(cu)
            except (ValidationError, ValueError):
                kq = None
            if kq is not None:
                with self._khoa:
                    self._moi[k] = cu
                    dem.dung_lai += 1
                return kq, True
        kq = client.extract(schema, messages, **kw)
        with self._khoa:
            self._moi[k] = kq.model_dump_json()
            dem.goi_moi += 1
            if nhan and len(dem.goi_moi_vi_du) < TOI_DA_VI_DU:
                dem.goi_moi_vi_du.append(nhan)
        return kq, False

    # ------------------------------------------------------------ phần đo --
    def ghi_vung(self, vung: dict[str, str]) -> None:
        """{tên phân hệ đã chuẩn hoá | "" cho phần chung: vân tay nội dung}."""
        with self._khoa:
            self._vung = dict(vung)

    def ghi_do_c5(self, khoa_ket_qua: str, *, khoa_vung: str, ket_luan: str,
                  dung_lai: bool) -> None:
        with self._khoa:
            self._moi_do[khoa_ket_qua] = {"khoa_vung": khoa_vung, "ket_luan": ket_luan,
                                          "dung_lai": dung_lai}

    def _do_c5(self) -> dict:
        """Nếu C5 cấp phân hệ chỉ hỏi lại khi vùng của nó hoặc phần chung đổi, bao nhiêu
        lượt SẼ được dùng lại, và trong đó bao nhiêu lượt model (hỏi lại thật lần này)
        cho kết luận KHÁC lần trước. Chỉ đếm lượt hỏi lại thật: lượt dùng lại thì kết
        luận trùng lần trước là điều hiển nhiên, không nói gì."""
        d = {"so_sanh_duoc": 0, "vung_khong_doi": 0, "giong": 0, "khac": 0,
             "vung_doi": 0, "vung_doi_khac": 0, "khac_vi_du": []}
        for khoa, r in self._moi_do.items():
            truoc = self._cu_do.get(khoa)
            if r["dung_lai"] or truoc is None:
                continue
            d["so_sanh_duoc"] += 1
            if r["khoa_vung"] == truoc.get("khoa_vung"):
                d["vung_khong_doi"] += 1
                if r["ket_luan"] == truoc.get("ket_luan"):
                    d["giong"] += 1
                else:
                    d["khac"] += 1
                    if len(d["khac_vi_du"]) < TOI_DA_VI_DU:
                        d["khac_vi_du"].append(
                            f"{khoa}: {truoc.get('ket_luan')} → {r['ket_luan']}")
            else:
                d["vung_doi"] += 1
                d["vung_doi_khac"] += r["ket_luan"] != truoc.get("ket_luan")
        return d

    # ------------------------------------------------------------------
    def thong_ke(self) -> dict:
        with self._khoa:
            ra: dict = {"tu_viec": self.tu_viec, "co_ban_cu": self.co_ban_cu}
            for ten, dem in self._dem.items():
                ra[ten] = {"dung_lai": dem.dung_lai, "goi_moi": dem.goi_moi,
                           "goi_moi_vi_du": list(dem.goi_moi_vi_du)}
            if self.co_ban_cu and self._cu_vung and self._vung:
                ra["vung_doi"] = sorted(t for t, v in self._vung.items()
                                        if t and self._cu_vung.get(t) not in (None, v))
                ra["vung_moi"] = sorted(t for t in self._vung
                                        if t and t not in self._cu_vung)
                ra["chung_doi"] = self._cu_vung.get("") != self._vung.get("")
            if self.co_ban_cu:
                ra["do_c5_theo_vung"] = self._do_c5()
            return ra

    def xuat(self) -> dict:
        with self._khoa:
            return {"phien_ban": PHIEN_BAN, "phan_hoi": dict(self._moi),
                    "do_c5": dict(self._moi_do), "vung": dict(self._vung)}
