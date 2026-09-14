#!/usr/bin/env python
"""A3 — tự kiểm lúc khởi động. KHÔNG gọi model, KHÔNG cần mạng.

    py scripts/khoi_dong_thu.py
    docker run --rm sizing-copilot:dev python scripts/khoi_dong_thu.py

Trả mã thoát 0 nếu image/máy này chạy được, khác 0 nếu không. Dùng được trong CI,
trong `docker build` và bằng tay.

## Nó kiểm cái gì, và vì sao đúng những cái đó

Image chỉ mang `src/`, `config/`, `ui/`, `scripts/` — cố ý không mang `data/` hay
hồ sơ thật (xem `.dockerignore`). Nên thứ dễ hỏng nhất không phải logic mà là
**thiếu file cấu hình** hoặc **thiếu phụ thuộc**, và cả hai chỉ lộ ra khi có
người tải tài liệu lên — tức là muộn.

Sáu phép kiểm dưới đây chạy hết đường code KHÔNG cần model:

  1. nạp `config/rules.yaml`   — thiếu là hỏng toàn bộ C4/C5
  2. nạp `config/units.yaml`   — thiếu là chuẩn hoá số/đơn vị sai lặng lẽ
  3. nạp `config/report_labels.yaml` — thiếu là C7 không xuất được báo cáo
  4. C4 chạy được trên `SizingCore` rỗng — bộ máy quy tắc còn sống
  5. đọc công thức + soi hệ số dự phòng — đường code thuần, không model (2.6)
  6. có `config/settings.yaml` không, và chế độ nào dùng được nếu KHÔNG có

Phép kiểm 6 cố ý **không coi việc thiếu `settings.yaml` là lỗi**: image không
được mang nó theo. Nhưng phải NÓI RA là đang thiếu, kèm chế độ nào vẫn chạy —
đúng NT4, và để người triển khai không tưởng mình đã cấu hình xong.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

DAT, HONG, LUU_Y = "  ĐẠT ", "  HỎNG", "  LƯU Ý"


def _chay(ten: str, ham) -> tuple[bool, str]:
    try:
        return True, ham()
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def kiem_rules() -> str:
    from src.validators.rules_loader import load_rules
    rs = load_rules()
    dl = sum(1 for r in rs.rules if r.type == "quantitative")
    dt = sum(1 for r in rs.rules if r.type == "qualitative")
    if not rs.globals.get("port_reserve"):
        raise ValueError("thiếu globals.port_reserve")
    return f"{len(rs)} quy tắc ({dl} định lượng · {dt} định tính)"


def kiem_units() -> str:
    from src.normalization.units import load_units
    from src.vision.neo_so import co_so_dung_luong
    u = load_units()
    n = len(u.cfg.get("nhom") or {})
    if not n:
        raise ValueError("units.yaml không có nhóm đơn vị nào")
    # Cơ số 1024 vs 1000 từng làm lệch số 1000 lần (nhật ký 2026-09-09), nên kiểm
    # thẳng giá trị chứ không chỉ kiểm file nạp được.
    return f"{n} nhóm đơn vị · cơ số dung lượng {co_so_dung_luong()}"


def kiem_nhan_bao_cao() -> str:
    from src.reporting.report import load_labels
    return f"nhãn báo cáo nạp được ({type(load_labels()).__name__})"


def kiem_c4() -> str:
    from src.extraction.schema import SizingCore
    from src.validators.quantitative import QuantitativeValidator
    from src.validators.rules_loader import load_rules
    kq = QuantitativeValidator(load_rules()).run(SizingCore())
    if not kq:
        raise ValueError("C4 không chấm được lượt nào trên core rỗng")
    return f"C4 chạy {len(kq)} lượt chấm trên core rỗng"


def kiem_cong_thuc() -> str:
    """Đường 2.6: đọc công thức tài liệu tự viết rồi soi hệ số dự phòng."""
    from src.extraction.cong_thuc import doc_mot_o
    from src.validators.he_so_du_phong import kiem_he_so_du_phong
    from src.validators.rules_loader import load_rules

    ct = doc_mot_o("= (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s")
    if ct is None or not ct.khop or ct.co_he_so(1.2) is not False:
        raise ValueError("đọc công thức sai trên ca mẫu đã biết")

    class _B:
        rows = [["vLB cho video", "Thông lượng", "= (125 + 32.5) * 3215/0.8*1.1 = 696,249"]]
        text = "vLB cho video Thông lượng"
        page, section, section_title = 18, "1.1", "Thông lượng luồng FLV"
        location = "Mục 1.1, trang 18"

    class _D:
        def tables(self):
            return [_B()]

    fs, _ = kiem_he_so_du_phong(_D(), load_rules())
    if len(fs) != 1 or fs[0].category != "sai_cong_thuc":
        raise ValueError(f"soi hệ số dự phòng sai: {[f.category for f in fs]}")
    return "đọc công thức + soi hệ số dự phòng: đúng trên ca mẫu"


def kiem_cau_hinh() -> tuple[str, bool]:
    """(thông điệp, có phải cảnh báo không). Thiếu settings.yaml KHÔNG phải lỗi."""
    from src.giao_dien import CHE_DO, che_do_kha_dung, kiem_model
    tt = kiem_model()
    ds = che_do_kha_dung(tt)
    ten = ", ".join(CHE_DO[k] for k in ds) or "(không chế độ nào)"
    if tt.san_sang:
        return f"cấu hình model SẴN SÀNG · chế độ dùng được: {ten}", False
    return (f"CHƯA có cấu hình model ({tt.thong_diep.strip()[:80]}) — "
            f"chế độ vẫn dùng được: {ten}", True)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chi-tiet", action="store_true", help="in cả traceback khi hỏng")
    a = ap.parse_args()

    from src.version import PHIEN_BAN_C3, commit_hien_tai
    print(f"Sizing Copilot · {PHIEN_BAN_C3} · commit {commit_hien_tai()}")
    print(f"Python {sys.version.split()[0]} · thư mục làm việc {pathlib.Path.cwd()}\n")

    hong = 0
    for ten, ham in (("rules.yaml", kiem_rules),
                     ("units.yaml", kiem_units),
                     ("report_labels.yaml", kiem_nhan_bao_cao),
                     ("C4 định lượng", kiem_c4),
                     ("2.6 công thức + hệ số dự phòng", kiem_cong_thuc)):
        ok, tin = _chay(ten, ham)
        print(f"{DAT if ok else HONG}  {ten:34} {tin}")
        if not ok:
            hong += 1
            if a.chi_tiet:
                traceback.print_exc()

    ok, tin = _chay("cấu hình", kiem_cau_hinh)
    if not ok:
        print(f"{HONG}  {'cấu hình model':34} {tin}")
        hong += 1
    else:
        thong_diep, canh_bao = tin
        print(f"{LUU_Y if canh_bao else DAT}  {'cấu hình model':34} {thong_diep}")

    print()
    if hong:
        print(f"✗ {hong} phép kiểm HỎNG — image/máy này chưa chạy được.")
        return 1
    print("✓ Mọi phép kiểm không cần model đều đạt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
