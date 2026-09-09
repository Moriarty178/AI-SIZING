"""Đo TRƯỚC KHI XÂY: nối số của 2.5 vào C4 thì recall của 1.13 có nhúc nhích không?

    py scripts/thu_neo_vao_c4.py            # mọi báo cáo trong eval/reports
    py scripts/thu_neo_vao_c4.py --chi-tiet

KHÔNG cần model. Script dựng một `SizingCore` **chỉ chứa** các tham số mà 2.5 neo
được, rồi chạy thẳng C4 lên đó. Đây là cận trên của phần 2.5 đóng góp được: mọi
tham số khác đều để trống, nên con số ra đây là *nhiều nhất* 2.5 có thể mua.

## Vì sao phải đo trước

`PLAN.md` (2026-09-07) đã chốt: nút thắt của 1.13 là **độ phủ trích xuất của C3**,
và 2.5 sinh ra để lấp đúng chỗ đó — số đo tải nằm trong ẢNH chứ không trong văn
xuôi. Nghe thì hợp lý. Nhưng "hợp lý" là thứ phiên trước đã đoán sai ba lần liên
tiếp, mỗi lần tốn một lượt chạy model. Nên: dựng thật, chạy thật, đọc số.

## Kết quả đo 2026-09-09

    Vtag       gán được  Master{ram_95th 59} · Worker{cpu_95th 20, ram_95th 66}
               C4 ra     130 không đánh giá được · 1 ĐẠT (KPI-02 Worker)
    PBH 4.0    gán được  Test{cpu_95th 31.2}
               C4 ra      78 không đánh giá được · 1 ĐẠT (KPI-02 Test)

**Cả hai lượt ĐẠT đều KHÔNG sinh finding** (`quantitative.py` trả `RuleOutcome`
trạng thái `dat` không kèm `Finding`). Mà thước đo 1.13 tính một nhãn là TRÚNG khi
có finding nhắc mã quy tắc của nó. ⟹ **Nối 2.5 vào C4 không đổi recall một chút
nào.** Xây phần nối trước khi chốt việc "quy tắc ĐẠT có sinh finding không" là xây
vào chỗ trống.

`ALC-03` cũng có đủ `cpu_95th` + `ram_95th` cho Worker nhưng vẫn không đánh giá
được: nó còn đòi `la_ho_so_thu_hoi` (`role: lookup`), thứ chưa số hoá.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.extraction.schema import (ExtractedValue, SizingCore,   # noqa: E402
                                   SizingExtension)
from src.ingestion.docx_reader import read_docx                  # noqa: E402
from src.validators.quantitative import QuantitativeValidator    # noqa: E402
from src.validators.rules_loader import load_rules               # noqa: E402
from src.version import in_phien_ban                             # noqa: E402
from src.vision.doc_anh import KetQuaDocAnh, SoDaDoc             # noqa: E402
from src.vision.neo_so import dai_luong_vat_ly, neo_tai_lieu     # noqa: E402

# (đại lượng vật lý, loại đo) -> tên tham số trong `rules.yaml`.
# Chỉ hai dòng vì `rules.yaml` chỉ có ba input đơn vị `%`: `cpu_95th` (2 quy tắc),
# `ram_95th` (1), `datanode_95th` (1 — riêng cho node dữ liệu, không suy từ ảnh
# chung được). Dung lượng `%` không có tham số nào nhận, nên neo DISK của Vtag
# (Postgres 63%, Redis 15%, MQTT 11%) hiện KHÔNG có chỗ để vào.
ANH_XA: dict[tuple[str, str], str] = {
    ("cpu", "phan_tram"): "cpu_95th",
    ("ram", "phan_tram"): "ram_95th",
}

THU_MUC_BAO_CAO = pathlib.Path("eval/reports")


def nap(p: pathlib.Path) -> tuple[str, list[KetQuaDocAnh]]:
    d = json.loads(p.read_text(encoding="utf-8"))
    return d.get("docx", ""), [
        KetQuaDocAnh(ma_anh=k["ma"], loai=k["loai"], location=k.get("location", ""),
                     doc_duoc=k.get("doc_duoc", False),
                     so_lieu=[SoDaDoc(**s) for s in (k.get("so_lieu") or [])])
        for k in d.get("ket_qua", [])]


def tim_docx(dd: str) -> pathlib.Path | None:
    p = pathlib.Path(dd)
    if p.exists():
        return p
    return next(pathlib.Path("danh_sach_sizings_da_duyet").rglob(p.name), None)


def moi_nhat(files: list[pathlib.Path]) -> list[pathlib.Path]:
    theo: dict[str, tuple[float, pathlib.Path]] = {}
    for f in files:
        try:
            dd = json.loads(f.read_text(encoding="utf-8")).get("docx", "")
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            continue
        khoa = pathlib.Path(dd).name or f.name
        if khoa not in theo or f.stat().st_mtime > theo[khoa][0]:
            theo[khoa] = (f.stat().st_mtime, f)
    return sorted(v[1] for v in theo.values())


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chi-tiet", action="store_true",
                    help="in mọi lượt chấm có kết luận, không chỉ tóm tắt")
    a = ap.parse_args()
    in_phien_ban("thử nối 2.5 vào C4")

    rs = load_rules()
    tong_dat = tong_vi_pham = tong_finding = 0
    for f in moi_nhat(sorted(THU_MUC_BAO_CAO.glob("doc-anh-*.json"))):
        dd, kqs = nap(f)
        dx = tim_docx(dd)
        if dx is None:
            continue
        ket, _ = neo_tai_lieu(read_docx(str(dx)), kqs)

        gan: dict[str, dict[str, tuple[float, str]]] = {}
        bo_qua: list[str] = []
        for r in ket:
            for n in r.neo:
                if not n.truc_tiep or n.o is None:
                    continue
                dl = dai_luong_vat_ly(n.o.bang_con, n.o.tieu_de_cot)
                ten = ANH_XA.get((dl or "", n.loai))
                if ten is None:
                    bo_qua.append(f"{n.scope_key}·{dl or '?'}·{n.loai}")
                    continue
                gan.setdefault(n.scope_key, {})[ten] = (n.gia_tri, n.o.location)

        core = SizingCore(phan_he=[
            SizingExtension(ten_phan_he=sk, params={
                k: ExtractedValue(value=v, unit="%", location=loc)
                for k, (v, loc) in ps.items()})
            for sk, ps in gan.items()])

        kq = QuantitativeValidator(rs).run(core)
        dem: dict[str, int] = {}
        for o in kq:
            dem[o.status] = dem.get(o.status, 0) + 1
        co_ket_luan = [o for o in kq if o.status in ("dat", "vi_pham")]
        n_finding = sum(1 for o in co_ket_luan if o.finding is not None)
        tong_dat += dem.get("dat", 0)
        tong_vi_pham += dem.get("vi_pham", 0)
        tong_finding += n_finding

        print(f"\n{'=' * 78}\n{dx.name}\n{'=' * 78}")
        print("  gán được: " + (json.dumps(
            {k: {a2: b[0] for a2, b in v.items()} for k, v in gan.items()},
            ensure_ascii=False) if gan else "(không có)"))
        if bo_qua:
            print(f"  neo KHÔNG có tham số nhận ({len(bo_qua)}): "
                  + ", ".join(sorted(set(bo_qua))))
        print(f"  C4: " + " · ".join(f"{k}={v}" for k, v in sorted(dem.items())))
        print(f"  → {len(co_ket_luan)} lượt có kết luận, "
              f"{n_finding} trong số đó sinh finding")
        for o in co_ket_luan if a.chi_tiet else []:
            print(f"     {o.rule_id:8} [{o.scope_key or 'he_thong'}] {o.status}"
                  f"  finding={'CÓ' if o.finding else 'KHÔNG'}")

    print(f"\n{'=' * 78}")
    print(f"TỔNG: {tong_dat} lượt ĐẠT · {tong_vi_pham} lượt VI PHẠM · "
          f"{tong_finding} finding sinh ra")
    if tong_finding == 0 and (tong_dat or tong_vi_pham):
        print("\n⚠ C4 kết luận được nhưng KHÔNG sinh finding nào — thước đo 1.13 tính")
        print("  nhãn là TRÚNG khi có finding nhắc mã quy tắc, nên recall KHÔNG đổi.")
        print("  Chốt «quy tắc ĐẠT có sinh finding không» trước khi xây phần nối.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
