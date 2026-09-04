"""1.14 — giao diện thử: tải file `.docx` → xem kết quả.

    streamlit run ui/app.py

Chỉ VẼ. Mọi thứ quyết định hành vi nằm ở `src/giao_dien.py` để test được mà không cần
cài Streamlit — xem docstring ở đó để biết vì sao tách.
"""
from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.giao_dien import (CAN_MODEL, CHE_DO, che_do_kha_dung, chay_checklist,
                           kiem_model, luu_tam, ten_file_ket_qua,
                           tom_tat_tai_lieu, uoc_luong)
from src.ingestion.docx_reader import read_docx
from src.pipeline import chay
from src.version import PHIEN_BAN_C3, commit_hien_tai

st.set_page_config(page_title="Sizing Copilot", page_icon="📐", layout="wide")


# --------------------------------------------------------------- thanh bên --
def thanh_ben():
    st.sidebar.title("📐 Sizing Copilot")
    st.sidebar.caption(
        "Công cụ **cố vấn**: giúp tự kiểm bản định cỡ trước khi nộp. "
        "KHÔNG phê duyệt, KHÔNG từ chối — người thẩm định vẫn quyết định cuối cùng."
    )
    tt = kiem_model()
    (st.sidebar.success if tt.san_sang else st.sidebar.warning)(tt.nhan)
    if not tt.san_sang:
        st.sidebar.caption(
            "Hai chế độ đầu vẫn dùng được bình thường. Chế độ thẩm định đầy đủ cần "
            "model tự dựng, chỉ với tới được từ máy trong mạng nội bộ."
        )
    st.sidebar.divider()
    st.sidebar.caption(f"{PHIEN_BAN_C3}  \ncommit `{commit_hien_tai()}`")
    return tt


# --------------------------------------------------------------- các chế độ --
def hien_doc(doc, tt_tl):
    st.subheader("Tài liệu đọc được")
    c = st.columns(5)
    for col, (nhan, gt) in zip(c, [
            ("Phần tử", tt_tl.phan_tu), ("Đề mục", tt_tl.de_muc),
            ("Bảng", tt_tl.bang), ("Bảng có số liệu", tt_tl.bang_du_lieu),
            ("Ảnh", tt_tl.anh)]):
        col.metric(nhan, gt)
    if tt_tl.nguon_trang == "none":
        st.warning("Không suy được số trang — vị trí trong báo cáo sẽ chỉ có số mục. "
                   "Mở và lưu lại file bằng Word thường sinh được thông tin phân trang.")
    for w in tt_tl.canh_bao:
        st.warning(w)
    if tt_tl.anh:
        st.info(f"Bản này CHƯA đọc nội dung {tt_tl.anh} hình ảnh (C2 thuộc Giai đoạn 2). "
                "Nếu sở cứ hoặc số liệu nằm trong ảnh thì phần đó chưa được kiểm.")

    with st.expander(f"Đề mục ({tt_tl.de_muc})"):
        for e in doc.elements:
            if e.kind == "heading":
                st.write(f"`{e.location}` — {e.text}")
    with st.expander(f"Bảng ({tt_tl.bang})"):
        for e in doc.tables():
            if e.rows:
                st.caption(f"Bảng #{e.index} · {e.location}")
                st.table(e.rows)


def hien_checklist(doc, ten):
    kq = chay_checklist(doc, ten_tai_lieu=ten)
    st.subheader("Checklist thẩm định — cột tham chiếu điền sẵn")
    st.markdown(kq.dong_tom_tat)
    st.caption(
        "Ô ghi `KHÔNG TÌM THẤY` nghĩa là máy không tìm ra chỗ nào đủ khớp — **không** "
        "có nghĩa tài liệu thiếu mục đó. Máy điền, người kiểm."
    )
    c1, c2 = st.columns(2)
    c1.download_button("⬇ Tải bản CSV (mở bằng Excel)", kq.csv.encode("utf-8-sig"),
                       ten_file_ket_qua(ten, "checklist", "csv"), "text/csv")
    c2.download_button("⬇ Tải bản Markdown", kq.markdown.encode("utf-8"),
                       ten_file_ket_qua(ten, "checklist", "md"), "text/markdown")
    st.markdown(kq.markdown)


def hien_tham_dinh(doc, duong_dan, ten):
    st.subheader("Thẩm định đầy đủ")
    c1, c2, c3 = st.columns(3)
    so_phan_he = c1.number_input("Số phân hệ (giả định, để ước lượng)", 1, 30, 5)
    song_song = c2.number_input("Số luồng chạy song song", 1, 16, 6)
    vong = c3.selectbox("Vòng", ["cả hai", "chỉ Vòng 1", "chỉ Vòng 2"])
    nhom = st.text_input("Giới hạn nhóm quy tắc (để trống là chạy tất cả)",
                         placeholder="ví dụ: KPI,CPU,RAM")

    chi_nhom = [x.strip() for x in nhom.split(",") if x.strip()] or None
    chi_vong = {"cả hai": None, "chỉ Vòng 1": 1, "chỉ Vòng 2": 2}[vong]
    ul = uoc_luong(doc, chi_nhom=chi_nhom, chi_vong=chi_vong,
                   so_phan_he=int(so_phan_he))
    st.info("Ước lượng trước khi chạy: " + ul.mo_ta(int(song_song)))
    if ul.phut(int(song_song)) > 10:
        st.warning("Lượt chạy này khá lâu. Cân nhắc giới hạn nhóm quy tắc hoặc "
                   "chọn một vòng để thử trước.")

    if not st.button("▶ Chạy thẩm định", type="primary"):
        return

    thanh, dong = st.progress(0.0), st.empty()

    def tien_do(giai_doan, i, tong, nhan):
        thanh.progress(min(1.0, i / max(1, tong)))
        dong.caption(f"{giai_doan} {i}/{tong} · {nhan}")

    with st.spinner("Đang chạy…"):
        kq = chay(str(duong_dan), chi_nhom=chi_nhom, chi_vong=chi_vong,
                  on_tien_do=tien_do, song_song=int(song_song))
    thanh.progress(1.0)
    dong.empty()

    bc = kq.bao_cao()
    st.download_button("⬇ Tải báo cáo Markdown", bc.encode("utf-8"),
                       ten_file_ket_qua(ten, "bao-cao", "md"), "text/markdown")
    st.markdown(bc)
    with st.expander("Thống kê chạy (để soi lỗi)"):
        st.json(kq.thong_ke)


# ------------------------------------------------------------------- chính --
def main():
    tt = thanh_ben()
    st.title("Tự kiểm bản định cỡ")

    f = st.file_uploader("Chọn bản sizing (.docx)", type=["docx"])
    if f is None:
        st.caption("Chưa có tệp nào. Mẫu Word chuẩn sinh được bằng "
                   "`python scripts/make_word_template.py`.")
        return

    duong_dan = luu_tam(f.getvalue(), f.name)
    doc = read_docx(str(duong_dan))
    tt_tl = tom_tat_tai_lieu(doc)
    st.success(f"Đã đọc `{f.name}` — {tt_tl.dong_tom_tat}")

    kha_dung = che_do_kha_dung(tt)
    khoa = st.radio("Việc cần làm", kha_dung,
                    format_func=lambda k: CHE_DO[k], horizontal=True)
    for k in CHE_DO:
        if k in CAN_MODEL and k not in kha_dung:
            st.caption(f"«{CHE_DO[k]}» tạm ẩn vì chưa gọi được model.")

    if khoa == "doc":
        hien_doc(doc, tt_tl)
    elif khoa == "checklist":
        hien_checklist(doc, f.name)
    else:
        hien_tham_dinh(doc, duong_dan, f.name)


main()
