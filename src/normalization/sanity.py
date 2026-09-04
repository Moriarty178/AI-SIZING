"""Lưới chặn lỗi đơn vị thô thiển — phục vụ khoảng trống đã ghi nhận ở 0.7.

Ca thật người thẩm định bắt được: khai **"3.000.000 TB cho 1.080 người dùng"**
= 2,7 PB mỗi người. Không quy tắc nào trong 151 quy tắc phủ việc này, và nó
thuần code kiểm được.

Đây **KHÔNG phải quy tắc thẩm định** — chỉ là lưới chặn lỗi đơn vị/độ lớn hiển
nhiên. Ngưỡng nằm trong `config/units.yaml` mục `hop_ly` để người nghiệp vụ chỉnh
được (NT3). Mọi kết quả đều kèm `computed_evidence` để thỏa NT2.
"""
from __future__ import annotations

from dataclasses import dataclass

from .units import Units, load_units


@dataclass
class SanityIssue:
    code: str
    message: str
    computed_evidence: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"SanityIssue({self.code}: {self.message})"


def check_storage_per_user(total_storage_bytes: float, n_users: float,
                           units: Units | None = None) -> SanityIssue | None:
    """Dung lượng mỗi người dùng có nằm trong khoảng tin được không."""
    if n_users <= 0 or total_storage_bytes <= 0:
        return None
    u = units or load_units()
    cap_gb = float(u.cfg["hop_ly"]["dung_luong_moi_nguoi_dung"]["canh_bao_tren_gb"])
    per_user_gb = total_storage_bytes / n_users / (1024 ** 3)
    if per_user_gb <= cap_gb:
        return None
    return SanityIssue(
        code="HOPLY-DUNGLUONG",
        message=(f"Dung lượng mỗi người dùng lên tới {per_user_gb:,.0f} GB — "
                 f"vượt xa ngưỡng {cap_gb:,.0f} GB. Nhiều khả năng nhầm ĐƠN VỊ "
                 f"(ví dụ khai TB trong khi số liệu là GB)."),
        computed_evidence=(f"{total_storage_bytes:,.0f} byte ÷ {n_users:,.0f} người "
                           f"= {per_user_gb:,.1f} GB/người > {cap_gb:,.0f} GB"),
    )


def check_tps_per_user(tps: float, n_users: float,
                       units: Units | None = None) -> SanityIssue | None:
    """TPS mỗi người dùng đồng thời có hợp lý không."""
    if n_users <= 0 or tps <= 0:
        return None
    u = units or load_units()
    cap = float(u.cfg["hop_ly"]["tps_moi_nguoi_dung"]["canh_bao_tren"])
    per_user = tps / n_users
    if per_user <= cap:
        return None
    return SanityIssue(
        code="HOPLY-TPS",
        message=(f"{per_user:,.1f} TPS cho mỗi người dùng đồng thời — vượt ngưỡng "
                 f"{cap:g}. Xem lại đơn vị hoặc cách quy đổi CCU sang TPS."),
        computed_evidence=f"{tps:,.0f} TPS ÷ {n_users:,.0f} CCU = {per_user:,.2f} TPS/người",
    )
