"""1.14 — giao diện thử: tải file `.docx` → xem kết quả.

    streamlit run ui/app.py

Chỉ VẼ. Mọi thứ quyết định hành vi nằm ở `src/giao_dien.py` để test được mà không cần
cài Streamlit — xem docstring ở đó để biết vì sao tách.
"""
from __future__ import annotations

import pathlib
import sys

import time

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from src.giao_dien import (CAN_MODEL, CHE_DO, che_do_kha_dung, chay_checklist,
                           kiem_model, luu_tam, ten_file_ket_qua,
                           tom_tat_tai_lieu, uoc_luong)
from src.ingestion.docx_reader import read_docx
from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh
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


NHAN_TRANG_THAI = {
    "cho": ("⏳", "đang xếp hàng"),
    "dang_chay": ("⚙️", "đang chạy"),
    "xong": ("✅", "xong"),
    "hong": ("❌", "hỏng"),
    "gian_doan": ("⚠️", "gián đoạn giữa chừng"),
}


def _khach() -> KhachAPI:
    return KhachAPI(st.session_state.get("dia_chi_api") or dia_chi_mac_dinh())


def _hien_mot_viec(kh: KhachAPI, d: dict, ten_tai: str) -> bool:
    """Vẽ trạng thái một việc. Trả True nếu còn đang chạy (cần tự làm mới)."""
    bieu, nhan = NHAN_TRANG_THAI.get(d["trang_thai"], ("•", d["trang_thai"]))
    st.markdown(f"### {bieu} {nhan} — mã việc `{d['ma']}`")
    st.caption(f"`{d['ten_file']}` · đã chạy {d['giay_da_chay']:.0f} giây. "
               "**Ghi lại mã việc**: đóng tab rồi mở lại vẫn tra được bằng mã.")

    if d["trang_thai"] in ("cho", "dang_chay"):
        td = d.get("tien_do")
        if td is None:
            # NT4: chưa biết tổng thì nói chưa biết. Vẽ 0% suốt 16 phút sẽ khiến
            # người dùng tưởng nó treo.
            st.progress(0.0, text="chưa biết tổng số bước")
        else:
            st.progress(td, text=f"{d.get('giai_doan') or '…'} "
                                 f"{d['da_xong']}/{d['tong']}")
        st.caption("Một tài liệu tốn khoảng 16 phút. Trang tự làm mới mỗi 5 giây.")
        return True

    if d["trang_thai"] != "xong":
        st.error(d.get("loi") or "Không rõ lý do.")
        return False

    if d.get("theo_muc_do"):
        cot = st.columns(len(d["theo_muc_do"]))
        for c, (muc, n) in zip(cot, sorted(d["theo_muc_do"].items())):
            c.metric(muc, n)
    try:
        bc = kh.bao_cao(d["ma"])
    except LoiAPI as e:
        st.error(f"Không lấy được báo cáo: {e}")
        return False
    st.download_button("⬇ Tải báo cáo Markdown", bc.encode("utf-8"),
                       ten_file_ket_qua(ten_tai or d["ten_file"], "bao-cao", "md"),
                       "text/markdown")
    st.markdown(bc)
    return False


def hien_tham_dinh(doc, duong_dan, ten, noi_dung: bytes):
    st.subheader("Thẩm định đầy đủ")
    kh = _khach()
    sk = kh.suc_khoe()
    if not sk.song:
        # KHÔNG âm thầm rơi về chạy thẳng trong tiến trình: đường lùi ấy chặn
        # giao diện 16 phút, đúng cái mà bản này sinh ra để bỏ.
        st.error(f"Chưa gọi được dịch vụ thẩm định tại `{kh.dia_chi}`."
                 f"\n\n{sk.thong_diep}")
        st.code("uvicorn api.main:app --host 0.0.0.0 --port 8000", language="bash")
        st.caption("Đổi địa chỉ bằng biến môi trường `SIZING_COPILOT_API`. "
                   "Hai chế độ còn lại không cần dịch vụ này.")
        return
    if not sk.model_san_sang:
        st.warning("Dịch vụ chạy được nhưng CHƯA cấu hình model — nộp bài sẽ hỏng. "
                   + sk.ghi_chu_model)

    dang_theo = st.session_state.get("ma_viec")
    if dang_theo:
        try:
            d = kh.viec(dang_theo)
        except LoiAPI as e:
            st.warning(f"Không tra được mã `{dang_theo}`: {e}")
            st.session_state.pop("ma_viec", None)
        else:
            con_chay = _hien_mot_viec(kh, d, ten)
            c1, c2 = st.columns(2)
            if c1.button("Nộp bài khác"):
                st.session_state.pop("ma_viec", None)
                st.rerun()
            if c2.button("🗑 Xoá việc này khỏi máy chủ"):
                kh.xoa(dang_theo)
                st.session_state.pop("ma_viec", None)
                st.rerun()
            if con_chay:
                time.sleep(5)
                st.rerun()
            return

    c1, c2, c3 = st.columns(3)
    so_phan_he = c1.number_input("Số phân hệ (giả định, để ước lượng)", 1, 30, 5)
    song_song = c2.number_input("Số luồng chạy song song", 1, 24, 12,
                                help="12 là mức nhanh nhất đo được 2026-09-09; "
                                     "mức 24 CHẬM HƠN mức 12.")
    vong = c3.selectbox("Vòng", ["cả hai", "chỉ Vòng 1", "chỉ Vòng 2"])
    nhom = st.text_input("Giới hạn nhóm quy tắc (để trống là chạy tất cả)",
                         placeholder="ví dụ: KPI,CPU,RAM")

    chi_nhom = [x.strip() for x in nhom.split(",") if x.strip()] or None
    chi_vong = {"cả hai": None, "chỉ Vòng 1": 1, "chỉ Vòng 2": 2}[vong]
    ul = uoc_luong(doc, chi_nhom=chi_nhom, chi_vong=chi_vong,
                   so_phan_he=int(so_phan_he))
    st.info("Ước lượng trước khi chạy: " + ul.mo_ta(int(song_song)))

    if not st.button("▶ Chạy thẩm định", type="primary"):
        return
    try:
        d = kh.nop(noi_dung, ten, nhom=nhom.strip(),
                   vong="" if chi_vong is None else chi_vong,
                   song_song=int(song_song))
    except LoiAPI as e:
        st.error(f"Nộp bài không thành công: {e}")
        return
    st.session_state["ma_viec"] = d["ma"]
    st.rerun()


# ------------------------------------------------------------------- chính --
def main():
    tt = thanh_ben()
    st.title("Tự kiểm bản định cỡ")

    f = st.file_uploader("Chọn bản sizing (.docx)", type=["docx"])
    if f is None:
        st.caption("Chưa có tệp nào. Mẫu Word chuẩn sinh được bằng "
                   "`python scripts/make_word_template.py`.")
        return

    noi_dung = f.getvalue()
    duong_dan = luu_tam(noi_dung, f.name)
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
        hien_tham_dinh(doc, duong_dan, f.name, noi_dung)


main()
