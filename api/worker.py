"""3.2 — worker chạy pipeline trong process riêng, cập nhật file job.

Chạy bằng `python -m api.worker <job_id>` từ thư mục gốc dự án. Tách process vì:
lỗi pipeline không được giết API, và lượt chạy 30 phút không được khoá worker
API. Tiến độ từng lượt gọi ghi NGAY vào file job để `GET /result` đọc được mà
không cần đợi xong.
"""
from __future__ import annotations

import pathlib
import sys
import time
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from api import jobs
from src.giao_dien import luu_tam
from src.pipeline import chay
from src.version import PHIEN_BAN_C3, commit_hien_tai

GOC = pathlib.Path(__file__).resolve().parents[1]
THU_MUC_TAI = GOC / "data" / "tai_len"


def tien_do_ghi(id_job: str):
    def hook(giai_doan: str, i: int, tong: int, nhan: str) -> None:
        try:
            j = jobs.nap(id_job)
            j["tien_do"] = f"{giai_doan} {i}/{tong} · {nhan}"
            jobs.ghi(id_job, j)
        except Exception:
            pass                      # tiến độ không bao giờ được giết lượt chạy
    return hook


def main(id_job: str) -> int:
    # Chiếm job trước khi chạy: rename nguyên tử `cho`→`chay` là quyền sở hữu.
    # Thua (job bị worker khác lấy) thì thoát lặng lẽ — đúng một người chạy.
    if jobs.dat_cho(id_job) is None:
        print(f"job {id_job} đã bị worker khác lấy, thoát")
        return 3
    j = jobs.nap(id_job)
    tuy = j.get("tuy_chon") or {}
    try:
        docx = THU_MUC_TAI / j["ten_file"]
        if not docx.exists():
            raise FileNotFoundError(f"không thấy tệp đã tải: {docx}")

        # `gia_lap` chỉ để kiểm hạ tầng không cần model (C3 của lộ trình deploy).
        # Báo cáo sinh ra VÔ NGHĨA về chất lượng — worker đóng dấu ngay vào kq
        # để không ai nhầm với lượt chạy thật.
        client = None
        if tuy.get("gia_lap"):
            from eval.gia_lap import ClientGiaLap
            client = ClientGiaLap()

        kq = chay(str(docx), client=client,
                  chi_nhom=tuy.get("chi_nhom"),
                  chi_vong=tuy.get("chi_vong"),
                  doc_anh=bool(tuy.get("doc_anh")),
                  song_song=int(tuy.get("song_song", 6)),
                  on_tien_do=tien_do_ghi(id_job))

        bao = kq.bao_cao()
        file_bao = THU_MUC_TAI / (pathlib.Path(j["ten_file"]).stem[:60]
                                  + "-bao-cao.md")
        file_bao.write_text(bao, encoding="utf-8")

        j["kq"] = {
            "bao_cao": bao,
            "file_bao_cao": str(file_bao.relative_to(GOC)),
            "thong_ke": kq.thong_ke,
            "so_finding": len(kq.findings),
            "phien_ban": PHIEN_BAN_C3,
            "commit": commit_hien_tai(),
            "gia_lap": bool(tuy.get("gia_lap")),
        }
        j["tien_do"] = "xong"
        jobs.ghi(id_job, j)
        jobs.doi_ten_trang_thai(id_job, "chay", "xong")
        return 0
    except Exception as e:
        try:
            j = jobs.nap(id_job)
            j["trang_thai"] = "loi"
            j["kq"] = {"loi": f"{type(e).__name__}: {e}",
                       "traceback": traceback.format_exc()[-2000:]}
            j["tien_do"] = "lỗi"
            jobs.ghi(id_job, j)
            jobs.doi_ten_trang_thai(id_job, "chay", "loi")
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("dùng: python -m api.worker <job_id>")
        raise SystemExit(2)
    t0 = time.time()
    ma = main(sys.argv[1])
    print(f"worker thoát {ma} sau {time.time() - t0:.0f}s")
    raise SystemExit(ma)
