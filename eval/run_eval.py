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

from eval.matching import bang_markdown, doi_chieu, nap_nhan
from src.extraction.extractor import uoc_tinh_luot_goi

GIAY_MOI_LUOT = 40      # đo thật 2026-09-04, xem scripts/try_c3_on_dossier.py
from src.ingestion.filenames import find_sizing_docs
from src.llm.client import LLMClient, LLMError
from src.pipeline import chay
from src.validators.qualitative import uoc_tinh_luot_goi_dt
from src.validators.rules_loader import load_rules

GOC_HO_SO = "danh_sach_sizings_da_duyet"


def tim_ban(dossier: str) -> list[pathlib.Path]:
    thu_muc = pathlib.Path(GOC_HO_SO) / dossier
    return sorted(find_sizing_docs(str(thu_muc))) if thu_muc.exists() else []


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
        return [d for d in tat_ca if ho_so.lower() in d.lower()]
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
    ap.add_argument("--ho-so", default="", help="chạy đúng một hồ sơ, khớp theo tên")
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
    u3 = uoc_tinh_luot_goi(rules, chi_nhom=chi_nhom, so_phan_he=n)["tong"]
    u5 = uoc_tinh_luot_goi_dt(rules, n, chi_vong=a.chi_vong, chi_ma=ma_dt)
    phut = (u3 + u5) * GIAY_MOI_LUOT / 60 / max(1, a.song_song)
    print(f"ước lượng mỗi hồ sơ (giả định {n} phân hệ): C3 {u3} + C5 {u5} = "
          f"{u3 + u5} lượt gọi · ~{phut:.0f} phút với {a.song_song} luồng · "
          f"cả {len(ds)} hồ sơ ~{phut * len(ds) / 60:.1f} giờ")
    print("  (BCCS3 thật có 13 phân hệ — con số trên rất nhạy với tham số này)")
    if a.uoc_tinh:
        return 0

    try:
        client = LLMClient()
    except (FileNotFoundError, LLMError) as e:
        print(f"Chưa chạy được: {e}")
        return 2

    theo_ho_so: dict[str, list] = {}
    da_dung: dict[str, str] = {}
    canh_bao: list[str] = []

    def tien_do(giai_doan: str, i: int, tong: int, nhan: str) -> None:
        print(f"    {giai_doan} {i}/{tong} · {nhan}", flush=True)

    for i, dossier in enumerate(ds, 1):
        bans = tim_ban(dossier)
        if not bans:
            canh_bao.append(f"`{dossier}`: không tìm thấy bản `.docx` nào")
            print(f"[{i}/{len(ds)}] {dossier}: KHÔNG CÓ .docx")
            continue
        if len(bans) > 1:
            canh_bao.append(
                f"`{dossier}`: có {len(bans)} bản, đã dùng `{bans[0].name}` — "
                f"nhãn PNX nói về bản TRƯỚC khi sửa, nếu đây là bản đã sửa thì "
                f"recall thấp giả tạo. Các bản: " +
                ", ".join(f"`{b.name}`" for b in bans))
        da_dung[dossier] = bans[0].name

        print(f"[{i}/{len(ds)}] {dossier} → {bans[0].name[:50]}", flush=True)
        t0 = time.time()
        try:
            kq = chay(str(bans[0]), client=client, rules=rules, model=a.model,
                      chi_nhom=chi_nhom, chi_vong=a.chi_vong, chi_ma_dt=ma_dt,
                      on_tien_do=tien_do, song_song=a.song_song)
        except Exception as e:                      # một hồ sơ hỏng không dừng cả lượt
            canh_bao.append(f"`{dossier}`: lỗi khi chạy — {type(e).__name__}: {e}")
            print(f"LỖI {type(e).__name__}")
            continue
        theo_ho_so[dossier] = kq.findings
        print(f"{len(kq.findings)} finding ({time.time() - t0:.0f}s)")

    ev = doi_chieu(theo_ho_so, labels, tap=a.tap, file_da_dung=da_dung)
    ev.canh_bao = canh_bao
    ev.bo_loc = {"nhom C3": ",".join(chi_nhom) if chi_nhom else "",
                 "nhom C5": ",".join(ma_dt) if ma_dt else "",
                 "chi_vong": a.chi_vong or "", "chi N ho so": a.chi or "",
                 "ho so": a.ho_so or "", "song song": a.song_song}
    meta = json.load(open("data/eval_set.json", encoding="utf-8"))["meta"]
    bao_cao = bang_markdown(ev, meta=meta)

    ra = pathlib.Path("eval/reports") / f"eval-{a.tap}-{time.strftime('%Y%m%d-%H%M')}.md"
    ra.parent.mkdir(parents=True, exist_ok=True)
    ra.write_text(bao_cao + "\n", encoding="utf-8")
    print("\n" + bao_cao)
    print(f"\nĐã ghi {ra}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
