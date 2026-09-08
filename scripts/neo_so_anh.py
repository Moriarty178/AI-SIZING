"""C2 · 2.5 — đối chiếu số đọc từ ẢNH với số khai báo trong BẢNG. KHÔNG CẦN MODEL.

Đọc lại báo cáo vision đã có trong `eval/reports/` (không gọi lại model), nối với
bảng khai báo trong chính file `.docx`, rồi in ra số nào dùng được cho C4.

    py scripts/neo_so_anh.py --tat-ca                 # mọi báo cáo trong eval/reports
    py scripts/neo_so_anh.py <bao-cao.json>           # một báo cáo
    py scripts/neo_so_anh.py --tat-ca --quet          # quét tham số, in lưới để chỉnh
    py scripts/neo_so_anh.py --tat-ca --loai phan_tram,dem,byte
    py scripts/neo_so_anh.py --tat-ca --gan-trang 5 --dung-sai 0.005

Đường dẫn `.docx` lấy từ chính trường `docx` trong báo cáo; `--docx` để đè khi hồ
sơ đã chuyển chỗ.

**Con số quan trọng nhất cần nhìn: cột `sai` trong phần chi tiết** — mỗi khớp đều
in kèm ô khai báo đã khớp, để đọc bằng mắt xem có khớp nhảm không. Dung sai > 0
gần như chắc chắn sinh khớp nhảm; xem `src/vision/neo_so.py` mục đo.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.ingestion.docx_reader import read_docx                      # noqa: E402
from src.version import in_phien_ban                                 # noqa: E402
from src.vision.doc_anh import KetQuaDocAnh, SoDaDoc                 # noqa: E402
from src.vision.neo_so import (GAN_TRANG_MAC_DINH,                   # noqa: E402
                               LOAI_NHAN_MAC_DINH, neo_tai_lieu,
                               thanh_finding, thu_thap_khai_bao)

THU_MUC_BAO_CAO = pathlib.Path("eval/reports")


def nap_bao_cao(p: pathlib.Path) -> tuple[str, list[KetQuaDocAnh]]:
    """Dựng lại `KetQuaDocAnh` từ JSON của `scripts/thu_doc_anh.py`."""
    d = json.loads(p.read_text(encoding="utf-8"))
    kq = []
    for k in d.get("ket_qua", []):
        kq.append(KetQuaDocAnh(
            ma_anh=k["ma"], loai=k["loai"], location=k.get("location", ""),
            doc_duoc=k.get("doc_duoc", False), ly_do=k.get("ly_do", ""),
            thanh_phan=k.get("thanh_phan") or [], luong=k.get("luong") or [],
            mo_ta=k.get("mo_ta", ""), lenh=k.get("lenh", ""),
            so_lieu=[SoDaDoc(**s) for s in (k.get("so_lieu") or [])]))
    return d.get("docx", ""), kq


def tim_docx(duong_dan: str) -> pathlib.Path | None:
    p = pathlib.Path(duong_dan)
    if p.exists():
        return p
    # Báo cáo ghi đường dẫn lúc chạy; hồ sơ có thể đã chuyển chỗ. Dò theo tên file.
    for c in pathlib.Path("danh_sach_sizings_da_duyet").rglob(p.name):
        return c
    return None


def chay_mot(bao_cao: pathlib.Path, docx_de: str | None, a) -> dict | None:
    duong_dan, ket_qua = nap_bao_cao(bao_cao)
    dx = tim_docx(docx_de or duong_dan)
    if dx is None:
        print(f"  ✗ không tìm thấy .docx cho {bao_cao.name}: {duong_dan}")
        return None
    doc = read_docx(str(dx))
    loai = tuple(x.strip() for x in a.loai.split(",") if x.strip())
    gan = None if a.gan_trang < 0 else a.gan_trang

    ket, tk = neo_tai_lieu(doc, ket_qua, loai_nhan=loai,      # type: ignore[arg-type]
                           gan_trang=gan, dung_sai=a.dung_sai,
                           tach_phan_tram=not a.khong_tach_phan_tram,
                           ca_anh=a.ca_anh)

    print(f"\n{'=' * 78}\n{dx.name}\n{'=' * 78}")
    print(f"  {tk.tom_tat()}")

    for r in ket:
        if not r.neo and not a.tat_ca_anh:
            continue
        dau = "✓" if r.neo_duoc else "·"
        print(f"\n  {dau} {r.ma_anh} ({r.location}) — {r.so_da_doc} số đọc được, "
              f"{len(r.neo)} dùng được"
              + (f", quy kết: {', '.join(r.scope_keys)}" if r.neo else "")
              + (f", {r.va_cham} va chạm" if r.va_cham else ""))
        for n in r.neo:
            if not n.truc_tiep:
                continue
            assert n.o is not None
            print(f"      KHỚP  {n.so.raw[:28]:>28}  ← {n.so.nhan[:38]}")
            print(f"             ↔ «{n.o.raw}» {n.o.location} · {n.o.mo_ta_o()}")
        thua = [n for n in r.neo if not n.truc_tiep]
        if thua:
            print(f"      thừa hưởng theo dòng nguồn ({len(thua)}):")
            for n in thua[:a.max_thua]:
                print(f"             {n.so.raw:>10}  {n.so.nhan[:40]:40}"
                      f" → «{n.scope_key}»")
            if len(thua) > a.max_thua:
                print(f"             … còn {len(thua) - a.max_thua} số nữa")

    canh_bao = [f for f in (thanh_finding(r, source_doc=dx.name) for r in ket)
                if f is not None]
    if canh_bao:
        print(f"\n  --- NT4: {len(canh_bao)} ảnh không neo được ---")
        for f in canh_bao:
            print(f"      {f.location}: {f.computed_evidence}")

    return {"docx": str(dx), "bao_cao": str(bao_cao),
            "thong_ke": tk.__dict__,
            "anh": [{"ma": r.ma_anh, "location": r.location,
                     "so_da_doc": r.so_da_doc, "va_cham": r.va_cham,
                     "scope_keys": r.scope_keys,
                     "neo": [{"raw": n.so.raw, "nhan": n.so.nhan,
                              "gia_tri": n.gia_tri, "loai": n.loai,
                              "scope_key": n.scope_key,
                              "truc_tiep": n.truc_tiep,
                              "trich_dan": n.so.trich_dan,
                              "can_cu": n.can_cu()} for n in r.neo]}
                    for r in ket],
            "finding": [f.as_dict() for f in canh_bao]}


def quet(bao_caos: list[pathlib.Path], a) -> None:
    """Lưới tham số — để chọn ngưỡng bằng số, không bằng cảm tính."""
    print(f"\n{'=' * 78}\nQUÉT THAM SỐ\n{'=' * 78}")
    print(f"{'loại':<22} {'gần trang':>10} {'dung sai':>9} "
          f"{'trực tiếp':>10} {'thừa hưởng':>11} {'va chạm':>8}")
    print("-" * 78)
    nap = []
    for bc in bao_caos:
        duong_dan, ket_qua = nap_bao_cao(bc)
        dx = tim_docx(duong_dan)
        if dx is None:
            continue
        nap.append((read_docx(str(dx)), ket_qua))

    for loai in (("phan_tram",), ("phan_tram", "dem"),
                 ("phan_tram", "dem", "byte", "milli_core")):
        for gan in (0, 1, 3, 5, None):
            for ds in (0.0, 0.005, 0.02):
                tt = th = vc = 0
                for doc, ket_qua in nap:
                    _, tk = neo_tai_lieu(doc, ket_qua, loai_nhan=loai,
                                         gan_trang=gan, dung_sai=ds,
                                         tach_phan_tram=not a.khong_tach_phan_tram,
                                         ca_anh=a.ca_anh)
                    tt += tk.neo_truc_tiep
                    th += tk.neo_thua_huong
                    vc += tk.va_cham
                print(f"{'+'.join(loai):<22} {str(gan):>10} {ds:>9.3f} "
                      f"{tt:>10} {th:>11} {vc:>8}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bao_cao", nargs="?", help="file JSON trong eval/reports/")
    ap.add_argument("--tat-ca", action="store_true",
                    help="chạy mọi báo cáo doc-anh-*.json trong eval/reports/")
    ap.add_argument("--docx", default=None, help="đè đường dẫn .docx trong báo cáo")
    ap.add_argument("--loai", default=",".join(LOAI_NHAN_MAC_DINH),
                    help="loại đại lượng được nhận: phan_tram,dem,byte,milli_core")
    ap.add_argument("--gan-trang", type=int, default=GAN_TRANG_MAC_DINH,
                    help="khoảng cách trang tối đa; -1 = không giới hạn")
    ap.add_argument("--dung-sai", type=float, default=0.0,
                    help="sai số tương đối khi khớp; 0 = khớp chính xác")
    ap.add_argument("--tat-ca-anh", action="store_true",
                    help="in cả ảnh không neo được")
    ap.add_argument("--max-thua", type=int, default=8)
    ap.add_argument("--khong-tach-phan-tram", action="store_true",
                    help="bỏ qua các `raw` gộp cả dòng (df -h) thay vì tách lấy %")
    ap.add_argument("--ca-anh", action="store_true",
                    help="suy rộng quy kết ra CẢ ảnh khi ảnh chỉ quy về một phân hệ "
                         "(đúng cho top/free/lscpu, SAI cho kubectl top — mặc định tắt)")
    ap.add_argument("--quet", action="store_true",
                    help="quét lưới tham số rồi thoát")
    ap.add_argument("--ghi", default=None, help="ghi kết quả ra file JSON")
    a = ap.parse_args()

    in_phien_ban("C2/2.5 neo số ảnh")

    if a.tat_ca:
        bao_caos = sorted(THU_MUC_BAO_CAO.glob("doc-anh-*.json"))
    elif a.bao_cao:
        bao_caos = [pathlib.Path(a.bao_cao)]
    else:
        ap.error("cần một báo cáo, hoặc --tat-ca")
    if not bao_caos:
        print(f"Không có báo cáo nào trong {THU_MUC_BAO_CAO}. "
              f"Chạy scripts/thu_doc_anh.py trước.")
        return 2

    if a.quet:
        quet(bao_caos, a)
        return 0

    print(f"  cổng: loại={a.loai} · gần trang="
          f"{'không giới hạn' if a.gan_trang < 0 else a.gan_trang} "
          f"· dung sai={a.dung_sai}")
    ra = [x for x in (chay_mot(bc, a.docx, a) for bc in bao_caos) if x]
    if a.ghi:
        pathlib.Path(a.ghi).write_text(
            json.dumps(ra, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nĐã ghi {a.ghi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
