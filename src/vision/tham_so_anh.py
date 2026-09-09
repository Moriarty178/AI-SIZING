"""C2 · 2.5b — nối số đã NEO của ảnh vào tham số quy tắc, để C4 tính được.

Đây là nửa sau của mục 2.5. Nửa đầu (`neo_so.py`) trả lời *"con số này của phân hệ
nào"*; nửa này trả lời *"nó là tham số nào trong `rules.yaml`"*.

## Cấp giá trị KHAI BÁO, không cấp số đo trong ảnh

Ô đưa cho C4 là **ô trong bảng** mà 2.5 đã neo được, không phải con số đọc từ ảnh.
Lý do là chuyện đúng/sai chứ không phải lựa chọn: `kubectl top` cho một LÁT CẮT tại
một thời điểm, còn `cpu_95th` là bách phân vị 95 theo thời gian. Đưa lát cắt vào
chỗ đòi bách phân vị là lặng lẽ so sai đại lượng.

Vai của ảnh ở đây là **chứng cứ**: nó chứng minh con số trong bảng có thật và đúng
phân hệ nào. Vì thế `ExtractedValue.note` luôn dẫn lại ảnh đã neo.

## Vì sao 2.5 làm được việc mà C3 không làm được

C3 hỏi model *"cột này là tham số nào"* và bảy vòng vẫn không ra `cpu_95th`. 2.5
tìm ra nó bằng đường khác hẳn và **không tốn một lượt gọi model nào**: ô nào có
giá trị trùng với một số đọc từ ảnh thì ô ấy tự khai luôn cả nhãn dòng (phân hệ)
lẫn nhãn cột (đại lượng).

## Trần đã đo, đừng kỳ vọng quá

Đo 2026-09-09 trên 6 hồ sơ (`scripts/thu_neo_vao_c4.py`): gán được đúng 4 giá trị
— `Master{ram_95th}`, `Worker{cpu_95th, ram_95th}`, `Test{cpu_95th}` — cho ra 2
lượt `KPI-02` ĐẠT. Không phải phép màu cho recall; nó là 4 con số THẬT ở chỗ trước
đó trống trơn.

Neo dung lượng `%` (Postgres 63%, Redis 15%, MQTT 11%) hiện **không có tham số nào
nhận**: `rules.yaml` chỉ có ba input đơn vị `%` và không cái nào cho dung lượng.
Chúng được đếm vào `khong_co_tham_so` chứ không bỏ im lặng.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..extraction.schema import ExtractedValue, SizingCore, SizingExtension
from .neo_so import KetQuaNeoAnh, Neo, dai_luong_vat_ly

# (đại lượng vật lý, loại đo) -> tên tham số trong `rules.yaml`.
#
# Cố ý để trong code chứ không đẩy ra `rules.yaml`: đây KHÔNG phải quy tắc định cỡ
# (NT3 nói về quy tắc), mà là bảng dịch giữa từ vựng của ảnh và từ vựng của bộ quy
# tắc — cùng loại với `HO_DON_VI` trong `extraction/bang.py`. Đưa ra YAML sẽ khiến
# người nghiệp vụ tưởng sửa được ngưỡng ở đây.
ANH_XA_THAM_SO: dict[tuple[str, str], str] = {
    ("cpu", "phan_tram"): "cpu_95th",
    ("ram", "phan_tram"): "ram_95th",
}


@dataclass
class ThongKeGan:
    gan_moi: int = 0                # tham số C3 chưa có, 2.5 điền vào
    da_co_khop: int = 0             # C3 đã có và TRÙNG giá trị -> chỉ thêm chứng cứ
    da_co_lech: int = 0             # C3 đã có nhưng KHÁC -> giữ của C3, không đè
    khong_co_tham_so: int = 0       # neo đúng nhưng không tham số nào nhận
    phan_he_tao_moi: int = 0        # phân hệ C3 không thấy, dựng từ nhãn dòng bảng
    lech: list[str] = field(default_factory=list)

    def tom_tat(self) -> str:
        return (f"{self.gan_moi} tham số điền mới · {self.da_co_khop} trùng C3 · "
                f"{self.da_co_lech} lệch C3 (giữ của C3) · "
                f"{self.khong_co_tham_so} neo không có tham số nhận · "
                f"{self.phan_he_tao_moi} phân hệ dựng thêm")


def _chuan(s: str) -> str:
    return " ".join((s or "").split()).strip().lower()


def _tim_phan_he(core: SizingCore, ten: str) -> SizingExtension | None:
    m = _chuan(ten)
    for ph in core.phan_he:
        if _chuan(ph.ten_phan_he) == m:
            return ph
    return None


def tham_so_tu_neo(n: Neo) -> str | None:
    """Tên tham số mà một neo cấp được, hoặc None."""
    if n.o is None:
        return None
    dl = dai_luong_vat_ly(n.o.bang_con, n.o.tieu_de_cot)
    if dl is None:
        return None
    return ANH_XA_THAM_SO.get((dl, n.loai))


def gan_vao_core(core: SizingCore, ket: list[KetQuaNeoAnh]) -> ThongKeGan:
    """Đổ tham số 2.5 neo được vào `core`. Trả thống kê; KHÔNG ném lỗi.

    **Không bao giờ đè giá trị C3 đã có.** C3 đọc thẳng tài liệu, 2.5 suy ra từ
    một trùng khớp; khi hai bên lệch nhau thì đó là điều cần NÓI RA chứ không phải
    điều để một bên thắng lặng lẽ.
    """
    tk = ThongKeGan()
    for r in ket:
        for n in r.neo:
            if not n.truc_tiep or n.o is None:
                continue
            ten = tham_so_tu_neo(n)
            if ten is None:
                tk.khong_co_tham_so += 1
                continue

            ph = _tim_phan_he(core, n.scope_key)
            if ph is None:
                # Nhãn dòng của một bảng định cỡ là một phân hệ có thật, có vị trí
                # neo được (NT2). C3 không thấy nó không có nghĩa nó không tồn tại
                # — và nếu không dựng thì đúng ca C3 hỏng lại là ca 2.5 vô dụng.
                ph = SizingExtension(ten_phan_he=n.scope_key,
                                     location=n.o.location)
                core.phan_he.append(ph)
                tk.phan_he_tao_moi += 1

            cu = ph.params.get(ten)
            if cu is not None and cu.value is not None:
                if isinstance(cu.value, (int, float)) and \
                        abs(float(cu.value) - n.gia_tri) < 1e-9:
                    tk.da_co_khop += 1
                    cu.note = (cu.note + " · " if cu.note else "") + n.can_cu()
                else:
                    tk.da_co_lech += 1
                    tk.lech.append(f"{n.scope_key}.{ten}: C3={cu.value} "
                                   f"vs 2.5={n.gia_tri}")
                continue

            ph.params[ten] = ExtractedValue(
                value=n.gia_tri, unit="%", raw=n.o.raw, location=n.o.location,
                note=n.can_cu(), confidence="cao")
            tk.gan_moi += 1
    return tk
