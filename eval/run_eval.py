"""1.13 — chạy eval trên tập phát triển. CẦN MODEL, phải chạy trong mạng công ty.

    python -m eval.run_eval                 # tập dev
    python -m eval.run_eval --nhom KPI,CPU  # giới hạn cho rẻ
    python -m eval.run_eval --chi 3         # chỉ 3 hồ sơ đầu

⚠️ **Tập `test` giữ kín** — chỉ chạy MỘT LẦN ở mục 3.6. Script đòi cờ
`--toi-hieu-rui-ro` mới cho chạy tập test, để không ai lỡ tay làm rò rỉ.

⚠️ **Thiên lệch đã biết, chưa gỡ được: PHIÊN BẢN TÀI LIỆU.** Nhãn lấy từ PNX, mà PNX
nhận xét về **bản TRƯỚC khi sửa**. Nhiều hồ sơ còn giữ nhiều phiên bản `.docx`, và nếu
chạy trên bản đã sửa thì lỗi đã được vá — recall sẽ **thấp giả tạo**. Việc ghép
`pnx_file` ↔ phiên bản `.docx` là mục còn nợ từ 0.7 (mục 5). Ở đây script **liệt kê mọi
bản tìm thấy và ghi rõ bản nào đã dùng**, để người đọc biết con số bị lệch theo hướng nào.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from eval.gia_lap import ClientGiaLap
from eval.matching import bang_markdown, doi_chieu, nap_nhan
from eval.phien_ban import ghep_phien_ban, so_vong_theo_ho_so
from src.extraction.extractor import uoc_tinh_luot_goi
from src.ingestion.filenames import find_sizing_docs
from src.llm.client import LLMClient, LLMError
from src.reporting.finding import Finding
from src.pipeline import chay
from src.version import in_phien_ban
from src.validators.qualitative import uoc_tinh_luot_goi_dt
from src.validators.rules_loader import load_rules

GOC_HO_SO = "danh_sach_sizings_da_duyet"
# Điểm dừng nằm trong `.cache/` (đã gitignore) — nó là trạng thái của MỘT lượt chạy,
# không phải kết quả để lưu trữ.
THU_MUC_DIEM_DUNG = pathlib.Path(".cache/eval")
THU_MUC_BAO_CAO = pathlib.Path("eval/reports")
GIAY_MOI_LUOT = 40      # đo thật 2026-09-04, xem scripts/try_c3_on_dossier.py
BANG_GIA_DINH = 20      # đo trên BCCS3; chỉ dùng cho dòng ước lượng


def tim_ban(dossier: str) -> list[pathlib.Path]:
    thu_muc = pathlib.Path(GOC_HO_SO) / dossier
    return sorted(find_sizing_docs(str(thu_muc))) if thu_muc.exists() else []


def _chu_ky(a, chi_nhom, ma_dt) -> dict:
    """Chữ ký của lượt chạy. Điểm dừng chỉ dùng lại được khi chữ ký TRÙNG KHỚP.

    Không có nó thì `--tiep-tuc` sẽ trộn kết quả của hai lượt chạy khác bộ lọc vào
    một báo cáo — một con số recall không ai lần lại được là gì.
    """
    return {"tap": a.tap, "model": a.model or "", "nhom": ",".join(chi_nhom or []),
            "nhom_dt": ",".join(ma_dt or []), "chi_vong": a.chi_vong or 0,
            "moi_phien_ban": bool(a.moi_phien_ban),
            # Điểm dừng của lượt DIỄN TẬP không được dùng lại cho lượt chạy thật.
            "gia_lap": bool(getattr(a, "gia_lap", False))}


def duong_dan_diem_dung(tap: str) -> pathlib.Path:
    return THU_MUC_DIEM_DUNG / f"diem-dung-{tap}.json"


def nap_diem_dung(tap: str, chu_ky: dict) -> tuple[dict, list[str]]:
    """Trả (dữ liệu hồ sơ đã chạy, ghi chú). Chữ ký lệch thì BỎ, không trộn."""
    p = duong_dan_diem_dung(tap)
    if not p.exists():
        return {}, []
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, [f"điểm dừng `{p}` hỏng, bỏ qua"]
    if d.get("chu_ky") != chu_ky:
        return {}, [f"điểm dừng `{p}` thuộc lượt chạy khác bộ lọc "
                    f"({d.get('chu_ky')}) — BỎ, chạy lại từ đầu"]
    return d.get("ho_so", {}), [
        f"tiếp tục từ điểm dừng `{p}`: {len(d.get('ho_so', {}))} hồ sơ đã có kết quả"]


def ghi_diem_dung(tap: str, chu_ky: dict, ho_so: dict) -> None:
    """Ghi nguyên tử sau MỖI hồ sơ — lượt chạy 2 giờ bị ngắt không được mất sạch."""
    p = duong_dan_diem_dung(tap)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        tam = p.with_suffix(".tmp")
        tam.write_text(json.dumps({"chu_ky": chu_ky, "ho_so": ho_so},
                                  ensure_ascii=False), encoding="utf-8")
        tam.replace(p)
    except OSError:
        pass                    # không ghi được thì vẫn chạy tiếp, không làm hỏng lượt


def chon_ho_so(tat_ca: list[str], co_docx: list[str], *, chi: int = 0,
               ho_so: str = "") -> list[str]:
    """Chọn hồ sơ để chạy. Tách riêng vì đây là chỗ đã âm thầm đốt một lượt chạy.

    Hồ sơ không có `.docx` vẫn nằm trong mẫu số của lượt chạy ĐẦY ĐỦ — bỏ ra là làm
    recall đẹp lên giả tạo. Nhưng khi người dùng giới hạn để chạy THỬ thì chọn chúng là
    vô nghĩa: `--chi 1` từng rơi trúng "Cấp mới hệ thống VAPS" (hồ sơ duy nhất chỉ có
    PDF, sắp đầu bảng vì `C` hoa đứng trước `c` thường), nên cả lượt không gọi model
    lần nào.
    """
    if ho_so:
        # Nhận NHIỀU hồ sơ, ngăn cách bằng dấu phẩy. Đo recall trên cả tập dev tốn
        # 6–11 giờ gọi model (đo 2026-09-04), nên cách dùng thực tế là lấy một MẪU
        # vài hồ sơ. Không có chỗ này thì phải chạy tay từng hồ sơ rồi tự cộng — và
        # cộng tay hai mẫu số khác nhau là đúng lỗi `meta.scoring_note` cảnh báo.
        khoa = [k.strip().lower() for k in ho_so.split(",") if k.strip()]
        return [d for d in tat_ca if any(k in d.lower() for k in khoa)]
    if chi:
        return co_docx[:chi]
    return tat_ca


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tap", default="dev", choices=["dev", "test", "tat_ca"])
    ap.add_argument("--nhom", default="", help="lọc nhóm quy tắc cho C3, vd KPI,CPU")
    ap.add_argument("--chi-vong", type=int, default=None)
    ap.add_argument("--chi", type=int, default=0,
                    help="chỉ chạy N hồ sơ ĐẦU TIÊN CÓ .docx")
    ap.add_argument("--gia-lap", action="store_true",
                    help="DIỄN TẬP: chạy trọn đường thật với MODEL GIẢ, không gọi "
                         "mạng. Dùng để bắt lỗi ghép nối trước khi tiêu giờ mạng "
                         "nội bộ. Kết quả KHÔNG phải số đo chất lượng.")
    ap.add_argument("--bom-loi", type=float, default=0.0,
                    help="chỉ với --gia-lap: tỷ lệ lượt gọi bị bơm hỏng (0–1), để "
                         "chứng minh một lượt gọi hỏng không kéo sập cả lượt chạy")
    ap.add_argument("--tiep-tuc", action="store_true",
                    help="dùng lại kết quả các hồ sơ đã chạy xong ở lượt trước "
                         "(cùng bộ lọc) thay vì chạy lại từ đầu")
    ap.add_argument("--moi-phien-ban", action="store_true",
                    help="chạy ĐÚNG bản của từng vòng nhận xét thay vì chỉ bản vòng 1 "
                         "— gỡ thiên lệch phiên bản, nhưng tốn thêm lượt gọi model")
    ap.add_argument("--ho-so", default="",
                    help="chạy các hồ sơ khớp tên, ngăn cách bằng dấu phẩy")
    ap.add_argument("--model", default=None)
    ap.add_argument("--toi-hieu-rui-ro", action="store_true",
                    help="bắt buộc khi --tap test")
    ap.add_argument("--nhom-dinh-tinh", default=None,
                    help="lọc nhóm cho C5; mặc định DÙNG CHUNG --nhom")
    ap.add_argument("--song-song", type=int, default=6,
                    help="số lời gọi chạy đồng thời")
    ap.add_argument("--phan-he", type=int, default=5,
                    help="số phân hệ giả định khi ước lượng")
    ap.add_argument("--uoc-tinh", action="store_true",
                    help="chỉ in ước lượng số lời gọi rồi thoát")
    a = ap.parse_args()

    if a.tap == "test" and not a.toi_hieu_rui_ro:
        print("Tập TEST giữ kín, chỉ chạy một lần ở mục 3.6. "
              "Thêm --toi-hieu-rui-ro nếu thật sự muốn.")
        return 2

    in_phien_ban()
    labels = nap_nhan(a.tap)
    ds = sorted({l["dossier"] for l in labels}, key=str.lower)

    # Hồ sơ không có `.docx` vẫn phải nằm trong mẫu số của một lượt chạy ĐẦY ĐỦ (bỏ ra
    # là làm recall đẹp lên giả tạo). Nhưng khi người dùng giới hạn để chạy THỬ thì
    # chọn chúng là vô nghĩa: `--chi 1` từng rơi trúng "Cấp mới hệ thống VAPS" — hồ sơ
    # duy nhất chỉ có PDF — nên cả lượt chạy không gọi model lần nào (2026-09-04).
    co_docx = [d for d in ds if tim_ban(d)]
    khong_docx = [d for d in ds if d not in co_docx]
    if khong_docx:
        print(f"  ⚠ {len(khong_docx)} hồ sơ không có .docx: "
              + ", ".join(khong_docx))

    tat_ca = ds
    ds = chon_ho_so(ds, co_docx, chi=a.chi, ho_so=a.ho_so)
    if not ds:
        print(f"Không hồ sơ nào khớp {a.ho_so!r}. Có: " + " | ".join(tat_ca))
        return 2
    if a.ho_so or a.chi:
        labels = [l for l in labels if l["dossier"] in set(ds)]
    print(f"tập {a.tap}: {len(ds)} hồ sơ · {len(labels)} nhãn")
    if a.ho_so or a.chi:
        print("  chạy: " + " | ".join(ds))

    rules = load_rules()
    chi_nhom = [x.strip() for x in a.nhom.split(",") if x.strip()] or None
    # `--nhom` PHẢI giới hạn cả C5, không chỉ C3. Trước đây nó chỉ cắt C3 nên
    # `--nhom KPI,CPU` vẫn chạy đủ 84 lượt định tính — người chạy tưởng rẻ mà không rẻ,
    # và vì chưa có tiến trình nên trông y hệt treo (2026-09-04).
    ma_dt = ([x.strip() for x in a.nhom_dinh_tinh.split(",") if x.strip()] or None
             if a.nhom_dinh_tinh is not None else chi_nhom)
    n = a.phan_he
    # Ước lượng chạy TRƯỚC khi đọc hồ sơ nào, nên số bảng phải giả định. Lấy đúng con
    # số đo được ở BCCS3 (20 bảng dùng được) và NÓI RÕ là giả định — đường cột của v6
    # tốn một lượt mỗi bảng.
    u3 = uoc_tinh_luot_goi(rules, chi_nhom=chi_nhom, so_phan_he=n,
                           so_bang=BANG_GIA_DINH)["tong"]
    u5 = uoc_tinh_luot_goi_dt(rules, n, chi_vong=a.chi_vong, chi_ma=ma_dt)
    phut = (u3 + u5) * GIAY_MOI_LUOT / 60 / max(1, a.song_song)
    # Số BẢN phải chạy, không phải số hồ sơ: `--moi-phien-ban` chạy mỗi vòng một bản.
    so_vong_uoc = so_vong_theo_ho_so(labels)
    so_ban = len(ds)
    if a.moi_phien_ban:
        so_ban = sum(
            len({b.duong_dan for b in ghep_phien_ban(
                pathlib.Path(GOC_HO_SO) / d,
                so_vong=so_vong_uoc.get(d, 1)).theo_vong.values()}) or 1
            for d in ds)
    print(f"ước lượng mỗi hồ sơ (giả định {n} phân hệ): C3 {u3} + C5 {u5} = "
          f"{u3 + u5} lượt gọi · ~{phut:.0f} phút với {a.song_song} luồng · "
          f"{so_ban} bản phải chạy ~{phut * so_ban / 60:.1f} giờ"
          + (f" (gấp {so_ban / max(1, len(ds)):.1f}× vì `--moi-phien-ban`)"
             if a.moi_phien_ban else ""))
    print(f"  (giả định {BANG_GIA_DINH} bảng dùng được; BCCS3 thật có 13 phân hệ "
          f"— con số trên rất nhạy với hai tham số này)")
    if a.uoc_tinh:
        return 0

    if a.gia_lap:
        if a.tap == "test":
            print("TỪ CHỐI: không diễn tập trên tập TEST giữ kín.")
            return 2
        client = ClientGiaLap(ty_le_rong=a.bom_loi / 2,
                              ty_le_sai_luoc_do=a.bom_loi / 2,
                              ty_le_loi_mang=0.0)
        print("\n" + "!" * 74)
        print("DIỄN TẬP — MODEL GIẢ. Mọi con số dưới đây KHÔNG phải kết quả thật.")
        print("Mục đích duy nhất: bắt lỗi ghép nối trước khi tiêu giờ mạng nội bộ.")
        print("!" * 74 + "\n")
    else:
        try:
            client = LLMClient()
        except (FileNotFoundError, LLMError) as e:
            print(f"Chưa chạy được: {e}")
            return 2

    theo_ho_so: dict[str, list] = {}
    theo_vong_ho_so: dict[str, dict[int, list]] = {}
    da_dung: dict[str, str] = {}
    canh_bao: list[str] = []
    chu_ky = _chu_ky(a, chi_nhom, ma_dt)
    da_luu: dict = {}
    if a.tiep_tuc:
        da_luu, ghi_chu = nap_diem_dung(a.tap, chu_ky)
        canh_bao += ghi_chu
        for g in ghi_chu:
            print(f"  {g}")

    def tien_do(giai_doan: str, i: int, tong: int, nhan: str) -> None:
        print(f"    {giai_doan} {i}/{tong} · {nhan}", flush=True)

    # Chọn phiên bản theo VÒNG nhận xét, không theo bảng chữ cái (xem
    # `eval/phien_ban.py`). Cách cũ `sorted(...)[0]` chấm 21 nhãn vòng 1 của
    # `Data Security VTT` trên bản đã sửa — hồ sơ này nằm trong mẫu 5 hồ sơ.
    so_vong = so_vong_theo_ho_so(labels)
    nhan_sai_ban = 0
    for i, dossier in enumerate(ds, 1):
        ghep = ghep_phien_ban(pathlib.Path(GOC_HO_SO) / dossier,
                              so_vong=so_vong.get(dossier, 1))
        ban = ghep.ban_vong1
        if ban is None:
            canh_bao.append(f"`{dossier}`: không tìm thấy bản `.docx` nào")
            print(f"[{i}/{len(ds)}] {dossier}: KHÔNG CÓ .docx")
            continue
        for c in ghep.canh_bao:
            canh_bao.append(f"`{dossier}`: {c}")
        # Chỉ chạy MỘT bản mỗi hồ sơ (bản vòng 1 — 73% nhãn thuộc vòng 1). Nhãn của
        # vòng sau vì thế bị chấm trên bản TRƯỚC khi sửa; đếm ra chứ không giấu.
        khac_vong1 = sum(1 for l in labels
                         if l["dossier"] == dossier
                         and int(l.get("lan_nhan_xet") or 1) > 1)
        if khac_vong1 and not a.moi_phien_ban:
            nhan_sai_ban += khac_vong1
            canh_bao.append(
                f"`{dossier}`: {khac_vong1} nhãn thuộc vòng 2 trở đi nhưng được chấm "
                f"trên bản vòng 1 `{ban.ten}` — dùng `--moi-phien-ban` để chấm đúng "
                f"bản của từng vòng (tốn thêm lượt gọi model)")
        # Đã chạy xong ở lượt trước thì lấy lại, không gọi model lần nữa.
        if dossier in da_luu:
            luu = da_luu[dossier]
            theo_ho_so[dossier] = [Finding(**f) for f in luu["findings"]]
            if luu.get("theo_vong"):
                theo_vong_ho_so[dossier] = {
                    int(v): [Finding(**f) for f in fs]
                    for v, fs in luu["theo_vong"].items()}
            da_dung[dossier] = luu.get("da_dung", "")
            print(f"[{i}/{len(ds)}] {dossier}: lấy lại từ điểm dừng "
                  f"({len(theo_ho_so[dossier])} finding)")
            continue

        # Mặc định chạy MỘT bản (vòng 1). `--moi-phien-ban` chạy từng bản khác nhau
        # mà các vòng ghép vào — số lượt gọi nhân theo số bản, nên không để mặc định.
        can_chay: dict[int, str] = {}
        if a.moi_phien_ban:
            for v, b in ghep.theo_vong.items():
                can_chay[v] = b.duong_dan
        else:
            can_chay[1] = ban.duong_dan
        duy_nhat = sorted(set(can_chay.values()))
        da_dung[dossier] = ", ".join(sorted({
            pathlib.Path(x).name for x in duy_nhat}))

        ket_qua_ban: dict[str, list] = {}
        for j, dd in enumerate(duy_nhat, 1):
            nhan_ban = f" [{j}/{len(duy_nhat)}]" if len(duy_nhat) > 1 else ""
            print(f"[{i}/{len(ds)}]{nhan_ban} {dossier} → "
                  f"{pathlib.Path(dd).name[:46]} (ghép {ghep.do_tin})", flush=True)
            t0 = time.time()
            try:
                kq = chay(dd, client=client, rules=rules, model=a.model,
                          chi_nhom=chi_nhom, chi_vong=a.chi_vong, chi_ma_dt=ma_dt,
                          on_tien_do=tien_do, song_song=a.song_song)
            except Exception as e:                  # một bản hỏng không dừng cả lượt
                canh_bao.append(
                    f"`{dossier}` / `{pathlib.Path(dd).name}`: lỗi khi chạy — "
                    f"{type(e).__name__}: {e}")
                print(f"LỖI {type(e).__name__}")
                continue
            ket_qua_ban[dd] = kq.findings
            # In bộ đếm của từng thành phần, không chỉ số finding. Một lượt chạy
            # "qua" vì thành phần nào đó âm thầm không làm gì là lượt chạy vô giá
            # trị — nhất là khi diễn tập.
            c3, c5 = kq.thong_ke.get("c3", {}), kq.thong_ke.get("c5", {})
            chan_doan = " · ".join(x for x in [
                f"C1 {kq.thong_ke.get('c1_phan_tu', 0)} phần tử/"
                f"{kq.thong_ke.get('c1_bang', 0)} bảng",
                (f"C3 {c3.get('luot_goi', 0)} lượt/"
                 f"{c3.get('truong_co_gia_tri', 0)} trường có giá trị/"
                 f"{c3.get('khong_neo_duoc', 0)} không neo được" if c3 else ""),
                (f"C5 {c5.get('dat', 0)}đạt/{c5.get('khong_dat', 0)}không đạt/"
                 f"{c5.get('trich_dan_bia', 0)} trích dẫn bị loại" if c5 else ""),
            ] if x)
            print(f"{len(kq.findings)} finding ({time.time() - t0:.0f}s) · {chan_doan}")
        if not ket_qua_ban:
            continue
        # Mẫu số vẫn tính đủ; `theo_ho_so` gom mọi bản để `finding_khong_khop` đúng.
        theo_ho_so[dossier] = [f for fs in ket_qua_ban.values() for f in fs]
        if a.moi_phien_ban:
            theo_vong_ho_so[dossier] = {
                v: ket_qua_ban[dd] for v, dd in can_chay.items() if dd in ket_qua_ban}
        da_luu[dossier] = {
            "da_dung": da_dung[dossier],
            "findings": [f.as_dict() for f in theo_ho_so[dossier]],
            "theo_vong": {str(v): [f.as_dict() for f in fs]
                          for v, fs in theo_vong_ho_so.get(dossier, {}).items()},
        }
        ghi_diem_dung(a.tap, chu_ky, da_luu)

    if nhan_sai_ban:
        canh_bao.append(
            f"TỔNG: {nhan_sai_ban}/{len(labels)} nhãn thuộc vòng 2 trở đi được chấm "
            f"trên bản vòng 1 — recall của phần này THẤP GIẢ TẠO nếu lỗi đã được vá, "
            f"hoặc CAO GIẢ TẠO nếu lỗi mới phát sinh ở bản sau.")
    ev = doi_chieu(theo_ho_so, labels, tap=a.tap, file_da_dung=da_dung,
                   findings_theo_vong=theo_vong_ho_so or None)
    ev.canh_bao = canh_bao
    ev.dien_tap = bool(a.gia_lap)
    ev.bo_loc = {"nhom C3": ",".join(chi_nhom) if chi_nhom else "",
                 "nhom C5": ",".join(ma_dt) if ma_dt else "",
                 "chi_vong": a.chi_vong or "", "chi N ho so": a.chi or "",
                 "ho so": a.ho_so or "", "song song": a.song_song}
    if a.gia_lap:
        canh_bao.insert(0, "⚠️ LƯỢT DIỄN TẬP BẰNG MODEL GIẢ — mọi con số trong báo "
                           "cáo này là VÔ NGHĨA về mặt chất lượng. Chỉ dùng để xác "
                           "nhận đường chạy không vỡ. " + client.tk.tom_tat())
    tk_cache = client.cache.tk
    if tk_cache.trung or tk_cache.luu:
        canh_bao.append(
            f"đệm lời gọi (2.12): {tk_cache.trung} lượt lấy trong đệm, "
            f"{tk_cache.truot} lượt phải gọi model — tiết kiệm ước tính "
            f"~{tk_cache.tiet_kiem_giay / 60:.0f} phút"
            + (f"; {tk_cache.loi} lần đọc/ghi đệm hỏng" if tk_cache.loi else ""))
        print(f"\nđệm lời gọi: trúng {tk_cache.trung} · trượt {tk_cache.truot}"
              f" · tiết kiệm ~{tk_cache.tiet_kiem_giay / 60:.0f} phút")
    meta = json.load(open("data/eval_set.json", encoding="utf-8"))["meta"]
    bao_cao = bang_markdown(ev, meta=meta)

    ten = ("dien-tap" if a.gia_lap else "eval")
    ra = THU_MUC_BAO_CAO / f"{ten}-{a.tap}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(bao_cao + "\n", encoding="utf-8")
    print("\n" + bao_cao)
    print(f"\nĐã ghi {ra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
