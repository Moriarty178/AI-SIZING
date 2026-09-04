"""Nhận dạng phiên bản mã đang chạy.

Ba lượt chạy thật liên tiếp (2026-09-04) được thực hiện bằng mã CŨ vì `git pull` chưa
ăn, và không có dấu hiệu nào trên màn hình cho biết điều đó — chỉ phát hiện được khi
đọc kỹ file kết quả. Mỗi lượt như vậy đốt 2–10 phút gọi model và cho một kết luận sai
về chất lượng. Nên mọi script chạy thật đều IN phiên bản trước khi gọi model.
"""
from __future__ import annotations

import subprocess

# Tăng số này mỗi khi đổi hành vi trích xuất, để người chạy đối chiếu được bằng mắt.
# Lượt 19:07 chạy mã v5 nhưng chuỗi này vẫn ghi "C3-v4" vì tôi quên tăng — đúng thứ
# module này sinh ra để chặn. Tăng cùng lúc với thay đổi hành vi, không để sau.
PHIEN_BAN_C3 = "C3-v6 (hỏi theo CỘT bảng: mỗi cột một tham số)"


def commit_hien_tai() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        ban = r.stdout.strip()
        s = subprocess.run(["git", "status", "--porcelain"],
                           capture_output=True, text=True, timeout=5)
        ban += " (có sửa cục bộ)" if s.stdout.strip() else ""
        return ban or "?"
    except Exception:                       # không có git thì cũng không sao
        return "?"


def in_phien_ban(ten: str = "") -> None:
    print(f"phiên bản: {PHIEN_BAN_C3} · commit {commit_hien_tai()}"
          + (f" · {ten}" if ten else ""))
