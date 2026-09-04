"""1.6 — Lược đồ Pydantic cho dữ liệu trích từ bản sizing.

Vì sao KHÔNG liệt kê cứng mọi trường: 151 quy tắc tham chiếu **203 tên tham số
khác nhau**, phần lớn chỉ dùng đúng một lần (`write_penalty_khai`,
`dung_luong_1_tape_gb`, …). Khai cả 203 trường thành thuộc tính Pydantic sẽ tạo
một lớp khổng lồ phải sửa mỗi lần thêm quy tắc — trái NT3, vì thêm quy tắc lẽ ra
chỉ phải sửa `rules.yaml`.

Thay vào đó: một **túi tham số có nguồn gốc** (`params`), khoá là đúng tên trong
`inputs` của quy tắc. Phần khai tường minh chỉ giữ những thông tin cấp tài liệu
mà nhiều quy tắc và cả báo cáo C7 đều cần.

Mỗi giá trị mang theo **xuất xứ** (`location`, `raw`) vì NT2 đòi finding phải
dẫn được nguồn, và mang `ambiguous` từ tầng chuẩn hoá (1.4) để C4 biết khi nào
phải xuống cấp thành cảnh báo "không kiểm chứng được" (NT4).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

LoaiSizing = Literal["cap_moi", "bo_sung", "nang_cap", "ung_cuu"]
MucDoQuanTrong = Literal["dac_biet_quan_trong", "rat_quan_trong", "quan_trong", "binh_thuong"]
DangDinhCo = Literal[1, 2, 3]
Confidence = Literal["cao", "vua", "thap"]


class ExtractedValue(BaseModel):
    """Một giá trị lấy từ tài liệu, kèm xuất xứ.

    `value=None` nghĩa là **không tìm thấy** — KHÔNG được thay bằng giá trị mặc
    định phỏng đoán. C4 gặp `None` thì sinh finding nhóm `thieu_thong_tin`.
    """

    value: float | int | str | bool | None = None
    unit: str | None = None
    raw: str = ""                       # nguyên văn trong tài liệu
    location: str = ""                  # "Mục IV.1.2, trang 8"
    element_index: int | None = None    # trỏ về Element của C1
    ambiguous: bool = False             # từ tầng chuẩn hoá 1.4
    note: str = ""
    confidence: Confidence = "cao"

    @property
    def missing(self) -> bool:
        return self.value is None


class SizingExtension(BaseModel):
    """Khối định cỡ của MỘT phân hệ — ứng với `scope: phan_he`."""

    ten_phan_he: str
    cong_nghe: str | None = None        # MariaDB / Redis / Kafka / K8s …
    module: str | None = None           # khớp `applies_to_module` của quy tắc
    cong_nghe_luu_tru: str | None = None  # cho `scope: phan_he_x_cong_nghe_luu_tru`
    location: str = ""
    # Số mục chứa phân hệ, do C1 gán.
    muc: str = ""
    # Vị trí phần tử nơi phân hệ được nhắc tới. C3 cắt ngữ cảnh theo KHOẢNG phần tử
    # giữa phân hệ này và phân hệ kế tiếp — cắt theo `muc` không đủ: ở BCCS3 cả 13
    # phân hệ đều nằm trong mục III, nên cắt theo mục không tách được gì.
    element_index: int | None = None
    params: dict[str, ExtractedValue] = Field(default_factory=dict)

    @property
    def scope_key(self) -> str:
        if self.cong_nghe_luu_tru:
            return f"{self.ten_phan_he}/{self.cong_nghe_luu_tru}"
        return self.ten_phan_he


class SizingCore(BaseModel):
    """Thông tin cấp tài liệu — ứng với `scope: he_thong`."""

    ten_he_thong: str | None = None
    ma_pyc: str | None = None
    # PRC-11 (thêm 2026-09-03): 17 nhãn PNX đòi mục này, nên nó là trường riêng
    # chứ không nằm lẫn trong `params`.
    muc_dich_sizing: str | None = None
    loai_sizing: LoaiSizing | None = None
    muc_do_quan_trong: MucDoQuanTrong | None = None
    dang_dinh_co: DangDinhCo | None = None      # quyết định MTH-01..04 nào chạy
    co_dc_dr: bool | None = None                # ARC-26, hai chiều với mức độ QT
    dau_moi_yeu_cau: str | None = None          # PRC-09
    don_vi_phat_trien: str | None = None
    don_vi_dinh_co: str | None = None
    thoi_gian_cam_ket: str | None = None        # PRC-10

    params: dict[str, ExtractedValue] = Field(default_factory=dict)
    phan_he: list[SizingExtension] = Field(default_factory=list)

    # ------------------------------------------------------------------
    def get(self, name: str, scope_key: str = "") -> ExtractedValue | None:
        """Tra một tham số: ưu tiên phân hệ, thiếu thì lùi về cấp tài liệu.

        Cho phép quy tắc `scope: phan_he` dùng chung một giá trị khai một lần ở
        đầu tài liệu (ví dụ hệ số KPI) mà không phải chép lại vào từng phân hệ.
        """
        if scope_key:
            for ph in self.phan_he:
                if ph.scope_key == scope_key and name in ph.params:
                    return ph.params[name]
        return self.params.get(name)

    def scope_keys(self, scope: str) -> list[str]:
        """Danh sách lượt chấm cho một `scope` của quy tắc."""
        if scope == "he_thong":
            return [""]
        if scope == "phan_he":
            return [ph.ten_phan_he for ph in self.phan_he]
        if scope == "phan_he_x_cong_nghe_luu_tru":
            return [ph.scope_key for ph in self.phan_he if ph.cong_nghe_luu_tru]
        raise ValueError(f"scope lạ: {scope!r}")

    def set_param(self, name: str, value: Any, **kw) -> None:
        """Tiện ích cho test và cho C3; luôn đi qua ExtractedValue để giữ xuất xứ."""
        self.params[name] = ExtractedValue(value=value, **kw)
