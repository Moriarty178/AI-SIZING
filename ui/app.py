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

from src.giao_dien import (bang_baseline, bang_lan_sua, bang_phat_sinh, bang_tu_dong,
                           csdl_san_sang, nhan_ho_so, noi_dung_goc_tu_cho_sua,
                           tom_tat_ho_so, tom_tat_thay_doi, tom_tat_vung_doi,
                           CACH_TIM_CHINH_XAC,
                           CAN_MODEL, CHE_DO, cau_gioi_han, chay_checklist,
                           che_do_kha_dung, chuan_bi_bang, gom_thay_doi,
                           kiem_model_qua_dich_vu, loc_bang, luu_tam,
                           NHAN_PHAN_LOAI, noi_dung_day_du, spec_cot_bang,
                           ten_file_ket_qua, tom_tat_tai_lieu, uoc_luong)
from src.ingestion.docx_reader import read_docx
from src.khach_api import KhachAPI, LoiAPI, dia_chi_mac_dinh
from src.luu_tru.danh_tinh import NHAN_VAI, VAI_NGUOI_CHON, tao_danh_tinh
from src.version import PHIEN_BAN_C3, commit_hien_tai

st.set_page_config(page_title="Sizing Copilot", page_icon="📐", layout="wide")


# --------------------------------------------------------------- thanh bên --
def thanh_ben():
    st.sidebar.title("📐 Sizing Copilot")
    st.sidebar.caption(
        "Công cụ **cố vấn**: giúp tự kiểm bản định cỡ trước khi nộp. "
        "KHÔNG phê duyệt, KHÔNG từ chối — người thẩm định vẫn quyết định cuối cùng."
    )
    o_danh_tinh()
    # Hỏi DỊCH VỤ, không tự dựng client tại chỗ: giao diện không giữ khoá model
    # (xem `kiem_model_qua_dich_vu`).
    kh = _khach()
    sk = kh.suc_khoe()
    # Trang chính cần biết CSDL có sẵn không (lối vào «Mở hồ sơ»); đỡ hỏi lại.
    st.session_state["_health_tho"] = sk.tho or {}
    tt = kiem_model_qua_dich_vu(sk)
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


def o_danh_tinh():
    """5.0a — ai đang thao tác. Danh tính DEMO, không xác thực.

    Giữ trong `session_state` theo `key` của widget, nên sống qua mọi lần vẽ lại
    trong một phiên trình duyệt; tải lại trang là chọn lại. Chưa có tính năng nào
    GHI theo danh tính (bắt đầu từ 5.1), nên thiếu tên chỉ nhắc, không chặn gì.
    """
    st.sidebar.subheader("Bạn là ai")
    vai = st.sidebar.selectbox("Vai", VAI_NGUOI_CHON, key="danh_tinh_vai",
                               format_func=lambda v: NHAN_VAI[v])
    ten = st.sidebar.text_input("Tên", key="danh_tinh_ten", max_chars=200,
                                placeholder="vd: Nguyễn Văn A")
    try:
        st.session_state["danh_tinh"] = tao_danh_tinh(vai, ten)
    except ValueError as e:
        st.session_state["danh_tinh"] = None
        if ten.strip():                   # gõ rồi mà sai thì nói; chưa gõ thì nhắc nhẹ
            st.sidebar.warning(str(e))
        else:
            st.sidebar.caption("Chưa nhập tên — sửa lỗi, ghi chú và phê duyệt "
                               "(Giai đoạn 5) sẽ cần biết ai làm.")
    st.sidebar.caption(
        "⚠️ **Danh tính demo, KHÔNG xác thực** — ai cũng chọn được vai Admin. Chỉ "
        "để ghi lại ai đã làm gì; khi ghép vào tool sizing sẽ lấy từ đăng nhập thật.")
    st.sidebar.divider()


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
    return KhachAPI(st.session_state.get("dia_chi_api") or dia_chi_mac_dinh(),
                    danh_tinh=st.session_state.get("danh_tinh"))


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
        column_order=[c for c in (rows[0] if rows else {})
                      if c != "xem"] + ["xem"],
        disabled=[c for c in rows[0] if c not in ("ghi_chu", "phân loại", "xem")] if rows else None,
        column_config=spec_cot_bang(),
        height=420, use_container_width=True)

    # data_editor với dữ liệu list THÌ TRẢ LIST (không phải DataFrame) — lỗi
    # `'list' object has no attribute 'to_dict'` ngày 2026-09-14.
    if st.button("💾 Lưu ghi chú", type="primary"):
        payload = gom_thay_doi(rows, sua if isinstance(sua, list) else
                               sua.to_dict("records"))
        if not payload:
            st.info("Chưa có thay đổi nào để lưu.")
        else:
            try:
                kq = kh.luu_phan_hoi(ma, payload)
                st.success(f"Đã lưu {kq['da_luu']} mục vào nhật ký phản hồi.")
            except LoiAPI as e:
                st.error(f"Lưu không thành công: {e}")

    # Chi tiết đầy đủ: tick «xem» ở dòng cần đọc nguyên văn — bảng cắt «nội
    # dung» ở 200 ký tự, không phải lăn ngược lên báo cáo phía trên.
    xem = [r for r in (sua if isinstance(sua, list) else []) if r.get("xem")]
    if xem:
        for r in xem:
            f = next((x for x in du_lieu.get("findings", [])
                      if x["id"] == r["finding_id"]), None)
            if f is not None:
                st.markdown(
                    f"**Chi tiết `{r['finding_id']}`** "
                    f"({r['mức độ']} · {r['vị trí']})")
                st.markdown(noi_dung_day_du(f))
        st.caption("Bỏ tick «xem» để thu gọn.")

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

    # 5.3 — đã dùng lại câu trả lời của lần trước ra sao, và bản này đổi ở đâu.
    tt_doi = tom_tat_thay_doi(d.get("thay_doi"))
    if tt_doi:
        (st.warning if tt_doi[0] == "warning" else st.info)(tt_doi[1])
    if d.get("phat_lai"):
        (st.warning if d["phat_lai"].casefold().find("không") >= 0 else st.caption)(
            f"Dùng lại: {d['phat_lai']}")
        vung = tom_tat_vung_doi((d.get("thong_ke") or {}).get("phat_lai"))
        if vung:
            st.caption(vung)

    if d.get("ghi_ho_so"):
        # NT4: bỏ qua hay hỏng khi ghi hồ sơ đều phải hiện ra, không im lặng.
        (st.caption if d.get("ho_so_id") else st.warning)(
            f"Hồ sơ: {d['ghi_ho_so']}")
    if d.get("ho_so_id"):
        with st.expander(f"🗂 Hồ sơ #{d['ho_so_id']} — baseline cố định & lỗi phát "
                         "sinh", expanded=True):
            hien_ho_so(kh, d["ho_so_id"])

    with st.expander("📝 Bảng ghi chú cho người thẩm định", expanded=False):
        _bang_phan_hoi(kh, d, ten_tai)
    return False


def hien_sua_finding(kh: KhachAPI, ho_so_id: int, fb_id: int, vung: str):
    """5.2 — một lỗi: chỗ trong tài liệu + lịch sử sửa + ghi nhận lần sửa mới.

    `vung` vào khoá widget: cùng một hồ sơ có thể hiện HAI lần trên một trang (khối
    «Mở hồ sơ» và khối việc vừa chạy xong), trùng khoá là Streamlit ném lỗi.
    """
    thong_bao = st.session_state.pop(f"da_ghi_sua_{fb_id}", None)
    if thong_bao:
        st.success(thong_bao)
    try:
        d = kh.finding_ho_so(ho_so_id, fb_id)
    except LoiAPI as e:
        st.warning(f"Không đọc được lỗi #{fb_id}: {e}")
        return
    st.markdown(f"#### {d.get('rule_ref') or '—'} · {d.get('scope_goc') or 'toàn hệ thống'}")
    st.markdown(d.get("noi_dung") or "")
    st.caption(f"Mức độ: {d.get('muc_do')} · Vị trí công cụ ghi: "
               f"{d.get('vi_tri') or 'không có'} · Bản đang xem: lần "
               f"{(d.get('lan_moi_nhat') or {}).get('so_thu_tu', '?')} "
               f"«{(d.get('lan_moi_nhat') or {}).get('ten_file', '')}»")

    cho = d.get("cho_sua") or {}
    # Gợi ý theo tên phân hệ / không tìm được → cảnh báo, để không bị đọc như vị trí.
    (st.info if cho.get("cach_tim") in CACH_TIM_CHINH_XAC else st.warning)(
        cho.get("ghi_chu") or "")
    for doan in cho.get("doan") or []:
        st.caption(f"{doan.get('location')} · {doan.get('kind')}"
                   + (f" · chỉ hiện dòng nhắc tên phân hệ "
                      f"({len(doan['rows']) - 1}/{doan.get('tong_dong', 0) - 1} dòng)"
                      if doan.get("loc_theo_ten") else "")
                   + (" · đã cắt bớt" if doan.get("cat_bot") else ""))
        if doan.get("rows"):
            st.dataframe(bang_tu_dong(doan["rows"]), hide_index=True,
                         use_container_width=True)
        else:
            st.text(doan.get("text") or "")
    if cho.get("con_nua"):
        st.caption(f"… còn {cho['con_nua']} đoạn nữa trong phạm vi này.")

    ls = bang_lan_sua(d)
    if ls:
        st.markdown("**Đã ghi nhận sửa**")
        st.dataframe(ls, hide_index=True, use_container_width=True)
    st.caption("Công cụ **KHÔNG sửa file Word**. Sửa trong Word, ghi nhận ở đây, rồi "
               "nộp lại để thẩm định lại hồ sơ.")

    if d.get("ho_so_trang_thai") != "dang_sua":
        st.info("Hồ sơ đã gửi duyệt — không ghi nhận sửa được nữa.")
        return
    if st.session_state.get("danh_tinh") is None:
        st.warning("Nhập tên ở thanh bên để ghi nhận lần sửa — cần biết ai đã sửa.")
        return
    with st.form(key=f"{vung}_form_sua_{ho_so_id}_{fb_id}", clear_on_submit=True):
        nd = st.text_area("Bạn đã sửa gì trong tài liệu", max_chars=10_000,
                          placeholder="vd: Bổ sung số đo tải đỉnh 7 ngày cho Kafka; "
                                      "đổi 12 → 16 core")
        if st.form_submit_button("Ghi nhận lần sửa"):
            if not nd.strip():
                st.error("Chưa nhập nội dung đã sửa.")
                return
            try:
                r = kh.ghi_lan_sua(ho_so_id, fb_id, nd, noi_dung_goc_tu_cho_sua(cho))
            except LoiAPI as e:
                st.error(f"Không ghi nhận được: {e}")
                return
            st.session_state[f"da_ghi_sua_{fb_id}"] = f"Đã ghi nhận lần sửa {r['so_lan']}."
            st.rerun()


def mo_ho_so_da_co():
    """5.2 — lối vào hồ sơ KHÔNG cần mã việc: người dùng quay lại sửa sau vài ngày."""
    if not csdl_san_sang(st.session_state.get("_health_tho")):
        return
    kh = _khach()
    with st.expander("🗂 Mở hồ sơ đã có — xem lỗi, chỗ cần sửa, ghi nhận sửa",
                     expanded=False):
        try:
            ds = kh.ds_ho_so()
        except LoiAPI as e:
            st.warning(f"Không lấy được danh sách hồ sơ: {e}")
            return
        if not ds:
            st.caption("Chưa có hồ sơ nào. Nộp một bản sizing ở dưới để tạo hồ sơ.")
            return
        h = st.selectbox("Hồ sơ", ds, format_func=nhan_ho_so, key="mo_ho_so")
        hien_ho_so(kh, int(h["id"]), vung="mo")


def hien_ho_so(kh: KhachAPI, ho_so_id: int, vung: str = "viec"):
    """5.1 — baseline CỐ ĐỊNH từ lần đầu + trạng thái lần mới nhất + rổ phát sinh."""
    try:
        d = kh.ho_so(ho_so_id)
    except LoiAPI as e:
        st.warning(f"Không đọc được hồ sơ #{ho_so_id}: {e}")
        return
    t = tom_tat_ho_so(d)
    c = st.columns(5)
    c[0].metric("Lỗi baseline (cố định)", t["so_loi_baseline"])
    c[1].metric("Đạt", t["dat"])
    c[2].metric("Chưa đạt", t["chua_dat"])
    c[3].metric("Chưa kiểm được", t["chua_kiem_duoc"])
    c[4].metric("Phát sinh", t["phat_sinh"])
    st.caption(
        f"Lần {t['so_thu_tu']}. Số lỗi baseline lấy từ lần thẩm định ĐẦU TIÊN và giữ "
        "nguyên. «Đạt» nghĩa là lỗi không còn xuất hiện ở lần này — đo được khoảng "
        "1,4% lỗi tự biến mất giữa hai lần chạy dù không ai sửa, nên kiểm lại các "
        "dòng «Đạt» mà bạn chưa động tới.")
    st.caption("👉 **Chọn một dòng** để xem chỗ cần sửa trong tài liệu và ghi nhận đã "
               "sửa gì.")
    ev = st.dataframe(bang_baseline(d), use_container_width=True, hide_index=True,
                      on_select="rerun", selection_mode="single-row",
                      key=f"{vung}_bang_ho_so_{ho_so_id}")
    chon = list(getattr(getattr(ev, "selection", None), "rows", []) or [])
    if chon and chon[0] < len(d.get("baseline") or []):
        with st.container(border=True):
            hien_sua_finding(kh, ho_so_id, d["baseline"][chon[0]]["id"], vung)

    # Rổ phát sinh LUÔN hiện, kể cả khi rỗng — im lặng thì người dùng không phân
    # biệt «không có lỗi mới» với «công cụ không kiểm lỗi mới».
    if t["so_thu_tu"] <= 1:
        st.markdown("**Lỗi phát sinh:** lần đầu — chưa có lần trước để so.")
    else:
        st.markdown(f"**Phát sinh sau lần sửa {t['so_thu_tu'] - 1}** "
                    f"({t['phat_sinh']} lỗi — KHÔNG cộng vào số lỗi baseline)")
        ps = bang_phat_sinh(d)
        if ps:
            st.dataframe(ps, use_container_width=True, hide_index=True)
        else:
            st.caption("Không có lỗi nào mới xuất hiện so với baseline.")


def _chon_ho_so(kh: KhachAPI, sk):
    """5.1 — hồ sơ mới hay thẩm định lại. None = mới · int = hồ sơ · False = chặn.

    Chỉ hiện khi dịch vụ báo CSDL sẵn sàng; không thì nộp y như trước.
    """
    if not csdl_san_sang(sk.tho):
        return None
    st.markdown("**Hồ sơ**")
    co_ten = st.session_state.get("danh_tinh") is not None
    kieu = st.radio("Lượt này là", ["Hồ sơ mới", "Thẩm định lại hồ sơ đã có"],
                    horizontal=True, key="kieu_ho_so")
    if kieu == "Hồ sơ mới":
        if not co_ten:
            st.warning("Chưa nhập tên ở thanh bên — lượt này vẫn chạy nhưng KHÔNG được "
                       "lưu thành hồ sơ, nên không thẩm định lại được về sau.")
        return None
    if not co_ten:
        st.error("Thẩm định lại cần biết ai nộp — nhập tên ở thanh bên.")
        return False
    try:
        ds = [h for h in kh.ds_ho_so() if h.get("trang_thai") == "dang_sua"]
    except LoiAPI as e:
        st.error(f"Không lấy được danh sách hồ sơ: {e}")
        return False
    if not ds:
        st.info("Chưa có hồ sơ nào đang sửa. Chọn «Hồ sơ mới» cho lần đầu.")
        return False
    h = st.selectbox("Chọn hồ sơ", ds, format_func=nhan_ho_so, key="chon_ho_so")
    st.caption("Baseline của hồ sơ giữ nguyên; lượt này chỉ cập nhật trạng thái từng "
               "lỗi và đưa lỗi mới vào rổ «phát sinh».")
    st.checkbox("Thẩm định lại TOÀN BỘ (không dùng lại kết quả lần trước)",
                key="tham_dinh_lai_toan_bo",
                help="Mặc định chỉ hỏi model lại cho phần tài liệu đã đổi; phần không "
                     "đổi lấy đúng kết quả lần trước, nên không dao động. Chọn ô này "
                     "khi nghi kết quả lần trước sai, hoặc sau khi sửa bộ quy tắc.")
    return int(h["id"])


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

    ho_so_id = _chon_ho_so(kh, sk)
    if ho_so_id is False:
        return
    if not st.button("▶ Chạy thẩm định", type="primary"):
        return
    try:
        toan_bo = ho_so_id is not None and st.session_state.get("tham_dinh_lai_toan_bo")
        d = kh.nop(noi_dung, ten, nhom=nhom.strip(),
                   vong="" if chi_vong is None else chi_vong,
                   song_song=int(song_song),
                   ho_so_id="" if ho_so_id is None else ho_so_id,
                   toan_bo="true" if toan_bo else "")
    except LoiAPI as e:
        st.error(f"Nộp bài không thành công: {e}")
        return
    st.session_state["ma_viec"] = d["ma"]
    st.rerun()


# ------------------------------------------------------------------- chính --
def main():
    tt = thanh_ben()
    st.title("Tự kiểm bản định cỡ")
    mo_ho_so_da_co()

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
