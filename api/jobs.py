"""3.2 — hàng đợi công việc cho API, bằng THƯ MỤC và SUBPROCESS, không cần Redis.

Vì sao không Redis/Celery: lượt chạy dài nhất đã đo là ~30 phút/hồ sơ, các lượt
đo recall cạn dần theo tỷ lệ trúng đệm (2.12), và 0.10 xác nhận rate limit của
gateway rất thoáng — một hàng đợi thực sự là hạ tầng cho nhu cầu chưa tồn tại.
Hàng đợi tối giản nhưng phải đúng hai ràng buộc thật:

  - **Lượt chạy 30 phút thì client phải tách khỏi nó**: FastAPI chạy trong một
    process, pipeline chạy trong subprocess — API sập/tải lại không giết lượt chạy,
    và ngược lại lượt chạy treo không khoá worker API.
  - **Mất điện không được mất trắng công** — cùng bài học với `APITimeoutError`
    làm mất trắng 41 nhãn, và cùng khuôn với điểm dừng `run_eval --tiep-tuc`:
    trạng thái job ghi ra file NGAY khi đổi (ghi nguyên tử: ghi file tạm rồi
    `replace`, trên Windows `write_text` ghi đè thẳng có thể để lại file dở).

Thiết kế an toàn với N worker trên MỘT máy: chuyển trạng thái `cho` → `chay` phải
đi qua `rename` nguyên tử — ai rename được thì người đó sở hữu job. Job chạy bằng
subprocess `python -m api.worker <job_id>` nên lỗi pipeline không giết API, và
`on_tien_do` ghi vào file job để `GET /result` xem được tiến độ từng lượt gọi.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

THU_MUC_JOB = pathlib.Path("data/jobs")

TRANG_THAI = ("cho", "chay", "xong", "loi")
HET_HAN_NGAY = 7  # job xong/loi quá 7 ngày bị dọn khi quét — đỡ phình data/jobs/


class JobKhongTonTai(KeyError):
    pass


def _ghi_nguyen_tu(p: pathlib.Path, noi_dung: str) -> None:
    tmp = p.with_suffix(".tmp")
    tmp.write_text(noi_dung, encoding="utf-8")
    os.replace(tmp, p)          # nguyên tử trên cùng một ổ


def _duong(id_job: str) -> pathlib.Path:
    # id do máy sinh (uuid hex) nên an toàn với path traversal; kiểm cho chắc (NT: đầu vào từ API)
    if not id_job or not all(c.isalnum() or c == "-" for c in id_job):
        raise JobKhongTonTai(id_job)
    return THU_MUC_JOB / f"{id_job}.json"


def _tim_file(id_job: str) -> pathlib.Path:
    """File vật lý luôn mang tiền tố trạng thái (`cho-`/`chay-`/`xong-`/`loi-`).
    Tìm theo cả bốn; không thấy thì ném JobKhongTonTai."""
    if not id_job or not all(c.isalnum() or c == "-" for c in id_job):
        raise JobKhongTonTai(id_job)
    for tt in TRANG_THAI:
        p = THU_MUC_JOB / f"{tt}-{id_job}.json"
        if p.exists():
            return p
    raise JobKhongTonTai(id_job)


def nap(id_job: str) -> dict:
    try:
        return json.loads(_tim_file(id_job).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise JobKhongTonTai(id_job) from None


def ghi(id_job: str, job: dict) -> None:
    # Ghi vào file HIỆN TẠI (đúng tiền tố trạng thái của nó) — đổi trạng thái là
    # việc của `dat_cho`/`doi_ten_trang_thai`, `ghi` không tự đoán trạng thái.
    p = _tim_file(id_job)
    job["cap_nhat"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _ghi_nguyen_tu(p, json.dumps(job, ensure_ascii=False, indent=1))


def tao(ten_file: str, tuy_chon: dict) -> str:
    id_job = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid():05d}-{os.urandom(3).hex()}"
    job = {
        "id": id_job,
        "trang_thai": "cho",
        "ten_file": pathlib.Path(ten_file).name,
        "tuy_chon": tuy_chon,
        "tien_do": "",
        "kq": None,
    }
    THU_MUC_JOB.mkdir(parents=True, exist_ok=True)
    p = THU_MUC_JOB / f"cho-{id_job}.json"
    job["cap_nhat"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _ghi_nguyen_tu(p, json.dumps(job, ensure_ascii=False, indent=1))
    return id_job


def dat_cho(id_job: str) -> str | None:
    """Chuyển `cho` → `chay`. Trả id nếu THẮNG, None nếu job đã bị người khác lấy.

    `os.replace` nguyên tử và ném `FileNotFoundError` nếu đích không tồn tại —
    nhưng trên Windows replace đè được file đang mở thì không đủ phân xử, nên
    đổi tên file: chỉ MỘT process đổi thành công tên `cho-<id>.json` (bắt buộc
    tồn tại trước đó) thành `chay-<id>.json`.
    """
    nguon = THU_MUC_JOB / f"cho-{id_job}.json"
    dich = THU_MUC_JOB / f"chay-{id_job}.json"
    try:
        os.rename(nguon, dich)          # nguyên tử; thua thì FileNotFound/Exists
    except OSError:
        return None
    job = json.loads(dich.read_text(encoding="utf-8"))
    job["trang_thai"] = "chay"
    job["bat_dau"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _ghi_nguyen_tu(dich, json.dumps(job, ensure_ascii=False, indent=1))
    return id_job


def doi_ten_trang_thai(id_job: str, tu: str, sang: str) -> None:
    src = THU_MUC_JOB / f"{tu}-{id_job}.json"
    dst = THU_MUC_JOB / f"{sang}-{id_job}.json"
    # Trường `trang_thai` và TIỀN TỐ tên file phải khớp nhau — worker chỉ đổi tên
    # trước đây nên `/result` đọc trạng thái cũ dù file đã sang `xong-`.
    job = json.loads(src.read_text(encoding="utf-8"))
    job["trang_thai"] = sang
    job["cap_nhat"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _ghi_nguyen_tu(src, json.dumps(job, ensure_ascii=False, indent=1))
    os.replace(src, dst)


def nap_duoi_ten(ten_file: pathlib.Path) -> dict:
    return json.loads(ten_file.read_text(encoding="utf-8"))


def khoi_dong_worker(id_job: str) -> None:
    """Tách process: lỗi pipeline không giết API, API restart không giết lượt chạy."""
    subprocess.Popen(
        [sys.executable, "-m", "api.worker", id_job],
        cwd=str(pathlib.Path(__file__).resolve().parents[1]),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def quet_cho() -> str | None:
    """Lấy một job `cho` bất kỳ và chiếm nó. Không có thì trả None."""
    for f in sorted(THU_MUC_JOB.glob("cho-*.json")):
        id_job = f.stem.removeprefix("cho-")
        if dat_cho(id_job):
            return id_job
    return None


def danh_sach() -> list[dict]:
    ra = []
    if not THU_MUC_JOB.exists():
        return ra
    for f in THU_MUC_JOB.glob("*-*.json"):
        if f.suffix == ".tmp":
            continue
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue                      # file ghi dở — bỏ qua, đừng giết cả danh sách
        ra.append({k: j.get(k) for k in
                   ("id", "trang_thai", "ten_file", "cap_nhat", "tien_do")})
    return sorted(ra, key=lambda j: str(j.get("id")), reverse=True)


def don_cu() -> int:
    """Xoá job xong/loi quá HET_HAN_NGAY ngày. Trả số file đã dọn."""
    if not THU_MUC_JOB.exists():
        return 0
    moc = time.time() - HET_HAN_NGAY * 86400
    n = 0
    for f in THU_MUC_JOB.glob("*.json"):
        if f.stat().st_mtime < moc:
            f.unlink()
            n += 1
    return n
