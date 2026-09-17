"""5.3 — bản nộp lần này KHÁC bản lần trước ở đâu. Thuần Python, offline.

Hai việc, cả hai đều cho NGƯỜI đọc chứ không để chọn lượt gọi model (việc đó dựa vào
nội dung từng lượt hỏi, xem `src/llm/phat_lai.py`):

- nói ra người dùng đã đổi những chỗ nào — và nói rõ khi KHÔNG đổi gì: nộp nhầm đúng
  bản cũ là chuyện hay gặp, và khi đó mọi dòng «chưa đạt» giữ nguyên là đúng chứ không
  phải công cụ hỏng;
- cho phép nghiệm thu đối chiếu: lượt hỏi nào phải hỏi lại, có nằm ở chỗ đã đổi không.

So theo NỘI DUNG từng phần tử (loại + chữ + ô bảng), không theo số trang hay chỉ số:
thêm một dòng ở trang 3 làm mọi phần tử phía sau dịch trang, nhưng chúng không «đổi».
"""
from __future__ import annotations

import difflib

TOI_DA_VI_TRI = 20


def _van_tay(e) -> tuple:
    return (e.kind, e.text or "",
            tuple(tuple(o or "" for o in r) for r in (e.rows or [])))


def _nhan(e) -> str:
    loai = {"table": "bảng", "heading": "tiêu đề", "image": "ảnh"}.get(e.kind, "đoạn")
    return f"{e.location} · {loai}"


def so_sanh_ban(cu, moi) -> dict:
    """`cu`, `moi`: `DocxDocument`. Trả dict JSON được.

    `sua` đếm cặp phần tử đổi nội dung tại chỗ; phần dôi ra của một khối thay thế tính
    là `them`/`xoa`. Vị trí sửa/thêm lấy theo bản MỚI, vị trí xoá theo bản CŨ.
    """
    a = [_van_tay(e) for e in cu.elements]
    b = [_van_tay(e) for e in moi.elements]
    sua = them = xoa = 0
    vi_tri: list[str] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        n_cu, n_moi = i2 - i1, j2 - j1
        chung = min(n_cu, n_moi) if tag == "replace" else 0
        sua += chung
        them += n_moi - chung
        xoa += n_cu - chung
        for k in range(j1, j2):
            vi_tri.append(f"{_nhan(moi.elements[k])} · "
                          f"{'sửa' if k - j1 < chung else 'thêm'}")
        for k in range(i1 + chung, i2):
            vi_tri.append(f"{_nhan(cu.elements[k])} (bản cũ) · xoá")
    return {"giong_het": sua + them + xoa == 0, "sua": sua, "them": them, "xoa": xoa,
            "vi_tri": vi_tri[:TOI_DA_VI_TRI],
            "con_nua": max(0, len(vi_tri) - TOI_DA_VI_TRI)}
