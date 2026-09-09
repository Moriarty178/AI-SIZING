#!/usr/bin/env python
"""A4 — đo TRẦN SONG SONG của gateway. Phải chạy trong mạng nội bộ.

    py scripts/do_song_song.py                 # thử 4, 8, 16, 24
    py scripts/do_song_song.py --muc 6,12,24,32
    py scripts/do_song_song.py --moi-muc 12

## Vì sao script này tồn tại

Một tài liệu tốn ~239 lượt gọi model (đếm offline 2026-09-09: C3 43 · C5 138 với
6 phân hệ · C2 58 ảnh). Ở song song 6 — mức đo được ngày 2026-09-09 — đó là
**~33 phút cho một tài liệu** và **~7 giờ cho một lượt dev đầy đủ**.

Thời gian gần như tỉ lệ NGHỊCH với mức song song, nên con số này quyết định:

  * lượt eval dev tốn 7 giờ hay 2 giờ;
  * mục 3.2 (chạy nền) phải làm tới đâu — 33 phút thì bắt buộc có hàng đợi,
    8 phút thì một thanh tiến độ có khi đã đủ.

Đo nó tốn vài phút. Đoán sai nó tốn vài giờ máy nội bộ. Nên đo.

## Cách đo, và vì sao nó công bằng

Mỗi mức song song bắn cùng MỘT số lời gọi giống hệt nhau về kích thước, đo thời
gian theo đồng hồ, rồi quy ra **lượt/phút**. Dùng prompt sinh ngẫu nhiên mỗi lần
và **tắt đệm** — nếu không, mức thứ hai trở đi sẽ lấy trong đệm và cho ra một
con số đẹp vô nghĩa.

Điểm bão hoà là chỗ lượt/phút **thôi tăng**. Vượt qua đó, tăng song song chỉ làm
tăng lỗi và độ trễ đuôi, không tăng thông lượng.

## ⚠️ Con số tuyệt đối ở đây KHÔNG phải tốc độ thật

Lời gọi thử là *"Trả lời đúng một từ: OK"* — vài chục token. Lời gọi thật của
C3/C5 mang theo cả ngữ cảnh tài liệu và sinh structured output, nặng hơn hàng
chục lần.

Đo được ngày 2026-09-09, cùng cổng, cùng mức song song 6:

    lời gọi nhỏ (script này)   119,7 lượt/phút
    lời gọi thật (lượt eval)     7,2 lượt/phút   ← 649 lượt / 90 phút
                                 ---------------
                                 lệch 16,6 lần

Bản đầu của script in thẳng "0,3 giờ cho lượt dev" từ con số nhỏ ấy, trong khi
thực tế là ~7 giờ. Nên nay script chỉ dùng phép đo này cho thứ nó ĐO ĐÚNG —
**tỉ lệ giữa các mức** — rồi quy ra giờ bằng cách nhân tỉ lệ đó với tốc độ THẬT
đã đo. Và vì lời gọi nặng làm cổng bão hoà SỚM hơn lời gọi nhẹ, tỉ lệ ấy là
**cận trên**: thực tế thường được ít hơn.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import statistics
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.llm.cache import BIEN_TAT                    # noqa: E402
from src.llm.client import (DEFAULT_MAX_TOKENS, LLMClient, LLMError,  # noqa: E402
                            PhanHoiRong)
from src.version import in_phien_ban                  # noqa: E402

MUC_MAC_DINH = "4,8,16,24"

# Tốc độ THẬT đã đo trên máy nội bộ 2026-09-09: lượt eval 649 lời gọi / 90 phút ở
# song song 6. Đây là mốc để quy tỉ lệ đo được thành giờ; đo lại được thì cập nhật.
TOC_DO_THAT = 7.2          # lượt/phút
MUC_THAT = 6               # ở mức song song này


def _mot_luot(client: LLMClient, model: str | None,
              max_tokens: int) -> tuple[bool, float, str]:
    """Một lời gọi, nội dung DUY NHẤT để không bao giờ trúng đệm."""
    t0 = time.perf_counter()
    rieng = uuid.uuid4().hex[:8]
    try:
        client.chat(
            [{"role": "user",
              "content": f"Trả lời đúng một từ: OK. (mã {rieng})"}],
            model=model, max_tokens=max_tokens)
        return True, time.perf_counter() - t0, ""
    except PhanHoiRong as e:
        # Đây KHÔNG phải lỗi tải — là ngân sách token quá nhỏ. Ghi kèm
        # `finish_reason` để đọc log biết ngay, đừng bắt ai đoán.
        return False, time.perf_counter() - t0, f"PhanHoiRong[{e.finish_reason}]"
    except LLMError as e:
        return False, time.perf_counter() - t0, type(e).__name__
    except Exception as e:                              # pragma: no cover
        return False, time.perf_counter() - t0, type(e).__name__


def do_mot_muc(client: LLMClient, muc: int, n: int, model: str | None,
               max_tokens: int) -> dict:
    t0 = time.perf_counter()
    do_tre: list[float] = []
    loi: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=muc) as pool:
        fut = [pool.submit(_mot_luot, client, model, max_tokens)
               for _ in range(n)]
        for f in as_completed(fut):
            ok, dt, ten = f.result()
            do_tre.append(dt)
            if not ok:
                loi[ten] = loi.get(ten, 0) + 1
    tong = time.perf_counter() - t0
    xong = n - sum(loi.values())
    return {"muc": muc, "n": n, "giay": tong, "thanh_cong": xong,
            "luot_moi_phut": (xong / tong * 60) if tong else 0.0,
            "do_tre_giua": statistics.median(do_tre) if do_tre else 0.0,
            "do_tre_p90": (sorted(do_tre)[int(len(do_tre) * 0.9)]
                           if do_tre else 0.0),
            "loi": loi}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--muc", default=MUC_MAC_DINH,
                    help=f"các mức song song cần thử (mặc định {MUC_MAC_DINH})")
    ap.add_argument("--moi-muc", type=int, default=12,
                    help="số lời gọi mỗi mức (mặc định 12)")
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                    help=f"ngân sách token mỗi lời gọi (mặc định {DEFAULT_MAX_TOKENS}, "
                         "bằng mức dùng thật). ĐỪNG hạ xuống vài chục: model dồn "
                         "ngân sách vào reasoning rồi trả content rỗng")
    ap.add_argument("--luot-mot-tai-lieu", type=int, default=239,
                    help="số lượt gọi cho MỘT tài liệu, để quy ra phút/tài liệu")
    a = ap.parse_args()
    in_phien_ban("đo trần song song")

    # Bắt buộc tắt đệm: mức thứ hai trở đi mà lấy trong đệm thì con số vô nghĩa.
    os.environ[BIEN_TAT] = "1"
    client = LLMClient()

    # MỘT lời gọi thử trước khi bắn cả loạt. Lượt chạy 2026-09-09 đốt 36 lời gọi
    # ở ba mức rồi mới lộ ra là ngân sách token quá nhỏ — đáng lẽ hỏng sau 2 giây.
    ok, dt, vi_sao = _mot_luot(client, a.model, a.max_tokens)
    if not ok:
        print(f"\n✗ Lời gọi THỬ đã hỏng sau {dt:.1f}s: {vi_sao}")
        print("  Chưa đo gì cả — sửa chỗ này trước, đừng bắn cả loạt.")
        if vi_sao.startswith("PhanHoiRong"):
            print(f"  `PhanHoiRong` KHÔNG phải lỗi tải: model tiêu hết "
                  f"{a.max_tokens} token vào phần suy luận rồi trả `content` rỗng.")
            print("  Chữa: tăng --max-tokens (mặc định của dự án là "
                  f"{DEFAULT_MAX_TOKENS}), hoặc chọn --model khác.")
        else:
            print("  Kiểm `config/settings.yaml` và biến SIZING_COPILOT_API_KEY.")
        return 2
    print(f"\nLời gọi thử ĐẠT sau {dt:.1f}s · ngân sách {a.max_tokens} token")

    muc = [int(m) for m in a.muc.split(",") if m.strip()]
    print(f"{a.moi_muc} lời gọi mỗi mức · đệm ĐÃ TẮT · lời gọi NHỎ — đây là "
          f"trần cổng, KHÔNG phải tốc độ thật\n")
    print(f"{'song song':>9} {'lượt/phút':>10} {'trễ giữa':>9} {'trễ p90':>8} "
          f"{'so mức đầu':>11}  lỗi")
    print("-" * 62)

    kq = []
    for m in muc:
        r = do_mot_muc(client, m, a.moi_muc, a.model, a.max_tokens)
        kq.append(r)
        # Cột cuối là TỈ LỆ, không phải phút/tài liệu: phép đo này chỉ đáng tin
        # về mặt so sánh giữa các mức. Quy ra giờ để ở phần kết luận, qua
        # `TOC_DO_THAT`.
        nen = kq[0]["luot_moi_phut"]
        ti_le = (r["luot_moi_phut"] / nen) if nen else 0.0
        loi = ", ".join(f"{k}×{v}" for k, v in r["loi"].items()) or "—"
        print(f"{m:>9} {r['luot_moi_phut']:>10.1f} {r['do_tre_giua']:>8.1f}s "
              f"{r['do_tre_p90']:>7.1f}s {ti_le:>10.2f}×  {loi}")

    tot = max(kq, key=lambda r: r["luot_moi_phut"])
    # Điều kiện là KHÔNG CÓ LƯỢT NÀO THÀNH CÔNG, không phải "thông lượng bằng 0":
    # `time.time()` trên Windows có độ phân giải ~15 ms, nên một loạt lời gọi
    # nhanh mà thành công cũng có thể đo ra 0. Đã đổi sang `perf_counter`, nhưng
    # điều kiện vẫn phải bám vào cái mình thật sự muốn nói.
    if not any(r["thanh_cong"] for r in kq):
        # Không được sập ở đây. Lượt 2026-09-09 ném `ZeroDivisionError` ngay sau
        # khi in đủ ba dòng chẩn đoán — làm mất luôn kết luận, đúng lúc người
        # chạy cần nó nhất.
        gop: dict[str, int] = {}
        for r in kq:
            for k, v in r["loi"].items():
                gop[k] = gop.get(k, 0) + v
        print("\n✗ KHÔNG mức nào có lời gọi nào thành công — chưa đo được gì.")
        print("  Lỗi: " + (", ".join(f"{k}×{v}" for k, v in gop.items()) or "?"))
        return 2

    if tot["luot_moi_phut"] <= 0:       # có lượt thành công nhưng nhanh quá để đo
        print("\n⚠ Có lời gọi thành công nhưng nhanh hơn độ phân giải đồng hồ — "
              "tăng --moi-muc rồi đo lại.")
        return 0

    goc = kq[0]
    ti_le = (tot["luot_moi_phut"] / goc["luot_moi_phut"]
             if goc["luot_moi_phut"] else 1.0)
    print(f"\nBão hoà ở song song {tot['muc']}: nhanh gấp {ti_le:.2f}× "
          f"mức {goc['muc']}.")

    # Quy ra giờ bằng tốc độ THẬT, KHÔNG bằng thông lượng lời gọi nhỏ ở trên.
    # Bản đầu quy thẳng từ lời gọi nhỏ và ra "0,3 giờ cho lượt dev" trong khi
    # thực tế ~7 giờ — sai 16,6 lần, và tệ hơn là in ra như một sự thật.
    that = TOC_DO_THAT * ti_le
    phut_tl = a.luot_mot_tai_lieu / that
    print(f"\nƯớc tính theo TỐC ĐỘ THẬT ({TOC_DO_THAT} lượt/phút ở song song "
          f"{MUC_THAT}, đo 2026-09-09):")
    print(f"  {that:.1f} lượt/phút ⟹ ~{phut_tl:.0f} phút/tài liệu ⟹ "
          f"lượt dev 14 hồ sơ ≈ {14 * phut_tl / 60:.1f} giờ")
    print("  Đây là CẬN TRÊN của phần lợi: lời gọi thật nặng hơn nên cổng bão "
          "hoà sớm hơn lời gọi nhỏ.")
    if goc["muc"] != MUC_THAT:
        print(f"  ⚠ Mức đầu trong --muc là {goc['muc']}, không phải {MUC_THAT} — "
              f"tỉ lệ quy đổi lệch gốc. Cho {MUC_THAT} vào --muc để so đúng.")
    if any(r["loi"] for r in kq):
        print("\n⚠ Có lỗi ở một số mức — mức nào bắt đầu lỗi thì ĐỪNG dùng mức đó "
              "cho lượt chạy thật, kể cả khi thông lượng của nó cao hơn.")
    if [r for r in kq if r["muc"] > tot["muc"]]:
        print("Các mức cao hơn KHÔNG nhanh hơn — đã bão hoà, tăng nữa chỉ tăng "
              "độ trễ đuôi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
