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
from src.ingestion.filenames import find_sizing_docs
from src.llm.client import LLMClient, LLMError
from src.pipeline import chay
from src.validators.rules_loader import load_rules

GOC_HO_SO = "danh_sach_sizings_da_duyet"


def tim_ban(dossier: str) -> list[pathlib.Path]:
    thu_muc = pathlib.Path(GOC_HO_SO) / dossier
    return sorted(find_sizing_docs(str(thu_muc))) if thu_muc.exists() else []


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tap", default="dev", choices=["dev", "test", "tat_ca"])
    ap.add_argument("--nhom", default="", help="lọc nhóm quy tắc cho C3, vd KPI,CPU")
    ap.add_argument("--chi-vong", type=int, default=None)
    ap.add_argument("--chi", type=int, default=0, help="chỉ chạy N hồ sơ đầu")
    ap.add_argument("--model", default=None)
    ap.add_argument("--toi-hieu-rui-ro", action="store_true",
                    help="bắt buộc khi --tap test")
    a = ap.parse_args()

    if a.tap == "test" and not a.toi_hieu_rui_ro:
        print("Tập TEST giữ kín, chỉ chạy một lần ở mục 3.6. "
              "Thêm --toi-hieu-rui-ro nếu thật sự muốn.")
        return 2

    labels = nap_nhan(a.tap)
    ds = sorted({l["dossier"] for l in labels})
    if a.chi:
        ds = ds[:a.chi]
        labels = [l for l in labels if l["dossier"] in set(ds)]
    print(f"tập {a.tap}: {len(ds)} hồ sơ · {len(labels)} nhãn")

    try:
        client = LLMClient()
    except (FileNotFoundError, LLMError) as e:
        print(f"Chưa chạy được: {e}")
        return 2

    rules = load_rules()
    chi_nhom = [x.strip() for x in a.nhom.split(",") if x.strip()] or None
    theo_ho_so: dict[str, list] = {}
    da_dung: dict[str, str] = {}
    canh_bao: list[str] = []

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

        print(f"[{i}/{len(ds)}] {dossier} → {bans[0].name[:50]} ...", end=" ", flush=True)
        t0 = time.time()
        try:
            kq = chay(str(bans[0]), client=client, rules=rules, model=a.model,
                      chi_nhom=chi_nhom, chi_vong=a.chi_vong)
        except Exception as e:                      # một hồ sơ hỏng không dừng cả lượt
            canh_bao.append(f"`{dossier}`: lỗi khi chạy — {type(e).__name__}: {e}")
            print(f"LỖI {type(e).__name__}")
            continue
        theo_ho_so[dossier] = kq.findings
        print(f"{len(kq.findings)} finding ({time.time() - t0:.0f}s)")

    ev = doi_chieu(theo_ho_so, labels, tap=a.tap, file_da_dung=da_dung)
    ev.canh_bao = canh_bao
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
