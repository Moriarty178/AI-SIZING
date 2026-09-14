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

from src.giao_dien import (CAN_MODEL, CHE_DO, cau_gioi_han, chay_checklist,
                           che_do_kha_dung, chuan_bi_bang, gom_thay_doi,
                           kiem_model_qua_dich_vu, loc_bang, luu_tam,
                           NHAN_PHAN_LOAI, spec_cot_bang, ten_file_ket_qua,
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
    # Hỏi DỊCH VỤ, không tự dựng client tại chỗ: giao diện không giữ khoá model
    # (xem `kiem_model_qua_dich_vu`).
    kh = _khach()
    tt = kiem_model_qua_dich_vu(kh.suc_khoe())
    (st.sidebar.success if tt.san_sang else st.sidebar.warning)(tt.nhan)
    if not tt.san_sang:
        st.sidebar.caption(
            f"Hai chế độ đầu vẫn dùng được bình thường. Chế độ thẩm định đầy đủ "
            f"gọi dịch vụ tại `{kh.dia_chi}` — khoá `SIZING_COPILOT_API_KEY` đặt ở "
            "**dịch vụ đó** (file `.env` cạnh `docker-compose.yml`), không phải ở "
            "giao diện."
        )
    st.sidebar.divider()
    # D3 — giới hạn phải hiện SẴN, không giấu sau một cú bấm. Demo cho người
    # ngoài mà không nêu chúng là để họ tự suy ra một công cụ khác công cụ thật.
    st.sidebar.subheader("Công cụ này làm được gì")
    for c in cau_gioi_han():
        st.sidebar.caption(c)
    st.sidebar.divider()
    st.sidebar.caption(f"{PHIEN_BAN_C3}  \ncommit `{commit_hien_tai()}`")
    return tt


def mau_word():
    """D4 — người đánh giá cần một file để thử NGAY, không phải đi xin hồ sơ thật."""
    import io

    from src.reporting.mau_word import doc_checklist, dung_mau
    try:
        d = dung_mau(doc_checklist())
    except Exception as e:               # thiếu bảng checklist thì nói ra, đừng im
        st.caption(f"(chưa dựng được mẫu Word: {type(e).__name__})")
        return
    buf = io.BytesIO()
    d.save(buf)
    st.download_button("⬇ Tải mẫu Word chuẩn để thử", buf.getvalue(),
                       "mau-sizing-chuan.docx",
                       "application/vnd.openxmlformats-officedocument."
                       "wordprocessingml.document")
    st.caption("Mẫu dựng từ 57 mục checklist thẩm định — điền vào rồi tải lên đây.")


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


def _bang_phan_hoi(kh: KhachAPI, d: dict, ten_tai: str | None = None):
    """Bảng ghi chú cho người thẩm định — hiện khi việc đã xong.

    Findings cache trong session_state: editor chỉ vẽ khi `xong` nên không có
    rerun 5 giây đụng vào, nhưng cache còn cho phép mở lại tab không refetch.
    """
    ma = d["ma"]
    kho_cache = f"findings_{ma}"
    if kho_cache not in st.session_state:
        try:
            st.session_state[kho_cache] = kh.findings(ma)
        except LoiAPI as e:
            st.error(f"Không lấy được danh sách đánh giá: {e}")
            return
    du_lieu = st.session_state[kho_cache]

    try:
        ph_cu = kh.phan_hoi(ma).get("phan_hoi") or {}
    except LoiAPI:
        ph_cu = {}
    rows_goc = chuan_bi_bang(du_lieu.get("findings", []), ph_cu)

    muc = st.selectbox("Mức độ", ["Tất cả", "Nghiêm trọng", "Quan trọng",
                                  "Nhẹ", "Thông tin"])
    rows = loc_bang(rows_goc, muc)

    sua = st.data_editor(
        rows,
        key=f"bang_{ma}_{muc}",       # key gồm filter: edit ở một lọc không nhảy
                                      # sang dòng khác ở lọc khác
        hide_index=True, num_rows="fixed",
        disabled=[c for c in rows[0] if c not in ("ghi_chu", "phân loại")] if rows else None,
        column_config=spec_cot_bang(),
        height=420, use_container_width=True)

    if st.button("💾 Lưu ghi chú", type="primary"):
        payload = gom_thay_doi(rows, sua.to_dict("records"))
        if not payload:
            st.info("Chưa có thay đổi nào để lưu.")
        else:
            try:
                kq = kh.luu_phan_hoi(ma, payload)
                st.success(f"Đã lưu {kq['da_luu']} mục vào nhật ký phản hồi.")
            except LoiAPI as e:
                st.error(f"Lưu không thành công: {e}")

    st.caption("Đổi «Mức độ» hoặc đóng trang sẽ mất ghi chú CHƯA bấm Lưu.")

    try:
        log = kh.nhat_ky()
    except LoiAPI as e:
        if getattr(e, "ma_http", None) == 404:
            st.caption("Chưa có ghi chú nào được lưu trên máy chủ.")
        else:
            st.caption(f"Không lấy được nhật ký phản hồi: {e}")
    else:
        st.download_button("⬇ Tải nhật ký phản hồi (CSV — mở bằng Excel)",
                           log.encode("utf-8-sig"),
                           ten_file_ket_qua(ten_tai or d["ten_file"],
                                            "phan-hoi", "csv"), "text/csv")


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

    with st.expander("📝 Bảng ghi chú cho người thẩm định", expanded=False):
        _bang_phan_hoi(kh, d, ten_tai)
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
        st.caption("Chưa có tệp nào.")
        mau_word()
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
