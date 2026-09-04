"""Test 1.17 — điền hộ cột tham chiếu của checklist. Thuần code, không gọi model.

Mỗi test dưới đây khoá một quyết định đã phải sửa sau khi chạy trên hồ sơ THẬT
(BCCS3, 2026-09-04). Không có chúng thì ba lần sửa ấy dễ trôi ngược.
"""
from src.ingestion.docx_reader import DocxDocument, Element
from src.reporting.dinh_vi_checklist import (
    NGUONG, bang_csv, bang_markdown, dinh_vi, dinh_vi_mot, tu_khoa,
    tu_khoa_dau, ung_vien_neo,
)
from src.reporting.mau_word import MucChecklist, doc_checklist


def _doc(*els: Element) -> DocxDocument:
    return DocxDocument(path="giả.docx", elements=list(els), page_source="rendered")


def _h(i: int, t: str, sec: str = "II") -> Element:
    return Element(index=i, kind="heading", text=t, page=2, section=sec, level=1)


def _p(i: int, t: str, sec: str = "II") -> Element:
    return Element(index=i, kind="paragraph", text=t, page=2, section=sec)


def _b(i: int, rows: list[list[str]], sec: str = "1") -> Element:
    return Element(index=i, kind="table", section=sec, page=1, rows=rows,
                   text=" ".join(c for r in rows for c in r))


def _muc(tt: str, ten: str) -> MucChecklist:
    return MucChecklist(dong="9", tt=tt, hang_muc=ten)


# --------------------------------------------------------------- từ khoá ---
def test_bo_hu_tu_va_phan_trong_ngoac():
    assert tu_khoa("Mô hình logic của phân hệ") == {"mô", "hình", "logic", "phân", "hệ"}
    # phần trong ngoặc là chú thích điều kiện, không phải tên thứ cần tìm
    assert "cấp" not in tu_khoa("Nguồn request (Từ nội bộ hay cấp ngoài)", bo_ngoac=True)


def test_tu_khoa_dau_lay_phan_dau_ten_hang_muc():
    ten = "Mô hình logic tổng quan triển khai thực tế gồm đầy đủ các thành phần"
    assert tu_khoa_dau(ten) == {"mô", "hình", "logic", "tổng", "quan"}


# ------------------------------------------------------------ cách chấm ---
def test_ten_hang_muc_DAI_van_khop_de_muc_NGAN():
    """Hồi quy: tên hạng mục là CÂU MÔ TẢ TIÊU CHÍ, đề mục tài liệu là TÊN NGẮN.

    Đo phủ một chiều theo phía hạng mục cho đề mục đúng chỉ 23% và loại nó đi — lần
    chạy đầu trên BCCS3 trượt cả 2.6 lẫn 2.7 vì lỗi này.
    """
    doc = _doc(_h(0, "Mô hình logic"))
    m = _muc("2.6", "Mô hình logic tổng quan triển khai thực tế gồm đầy đủ "
                    "các thành phần")
    v = dinh_vi_mot(doc, m)
    assert v.tim_thay and v.element_index == 0


def test_doan_van_dai_khong_nuot_moi_muc():
    """Đo phủ theo phía TÀI LIỆU thì mọi đoạn dài đều đạt 100% và hút hết mọi mục."""
    dai = ("Hệ thống mô tả tổng quan gồm mô hình logic, mô hình vật lý, luồng nghiệp "
           "vụ, cơ sở định cỡ, thông số đầu vào và bảng tổng hợp cấu hình thiết bị.")
    doc = _doc(_p(0, dai))
    v = dinh_vi_mot(doc, _muc("2.8", "Luồng nghiệp vụ tổng quan của hệ thống bao gồm "
                                     "luồng nội bộ và luồng giao tiếp với bên ngoài"))
    assert not v.tim_thay


# --------------------------------------------------------------- neo -------
def test_nhan_dong_bang_la_mot_nguon_neo():
    """Bảng "Thông tin hệ thống" của BCCS3 chứa thẳng các hạng mục checklist.

    Chấm cả bảng như một khối thì bốn nhãn ấy chìm trong nội dung và 2.2/2.3/2.4 đều
    trượt — đúng như lần chạy thứ hai. Trên cả 47 bản, **ô bảng là nguồn neo lớn nhất**.
    """
    doc = _doc(_b(4, [["STT", "", "Nội dung"],
                      ["1", "Mô tả hệ thống", "Hệ thống X phục vụ nghiệp vụ " * 12],
                      ["2", "Cơ sở định cỡ", "Định cỡ dựa trên hệ thống tương đồng " * 8]]))
    v = dinh_vi_mot(doc, _muc("2.4", "Cơ sở định cỡ"))
    assert v.tim_thay and v.nguon == "ô bảng" and v.element_index == 4


def test_o_bang_chi_la_so_thi_khong_lam_neo():
    neo = ung_vien_neo(_doc(_b(4, [["STT", "CPU"], ["1", "48"]])))
    assert all(n.text not in ("1", "48") for n in neo if n.loai == "ô bảng")


def test_de_muc_duoc_uu_tien_hon_van_xuoi_khi_diem_ngang_nhau():
    doc = _doc(_p(0, "Cơ sở định cỡ được nêu ở phần sau của tài liệu này."),
               _h(1, "Cơ sở định cỡ"))
    v = dinh_vi_mot(doc, _muc("2.4", "Cơ sở định cỡ"))
    assert v.element_index == 1 and v.nguon == "đề mục"


# ------------------------------------------------------- xuống cấp (NT4) ---
def test_duoi_nguong_thi_KHONG_dien_nhung_van_neu_ung_vien():
    """Cột tham chiếu điền bừa tệ hơn cột để trống: người thẩm định mở đúng trang đó
    và không thấy gì. Vẫn phải cho họ thấy ứng viên gần nhất để tự quyết."""
    doc = _doc(_h(0, "Kiến trúc triển khai vật lý", "III"))
    v = dinh_vi_mot(doc, _muc("2.11", "Mức độ dự phòng của hệ thống"))
    assert not v.tim_thay
    assert v.o_tham_chieu == "KHÔNG TÌM THẤY"
    assert v.diem < NGUONG


def test_khong_co_gi_khop_thi_khong_neo_gi_ca():
    v = dinh_vi_mot(_doc(_p(0, "Trang 1")), _muc("2.4", "Cơ sở định cỡ"))
    assert v.element_index is None and v.o_tham_chieu == "KHÔNG TÌM THẤY"


# ---------------------------------------------------------- bộ 57 mục -----
def test_bo_qua_tieu_de_chuong_va_tieu_de_khoi():
    """`I`/`II`/`III` và `3.1`/`3.2` là nhãn phân nhóm của chính checklist, không phải
    hạng mục để chấm."""
    kq = dinh_vi(_doc(_h(0, "Giải pháp thiết kế")))
    tt = {v.muc.tt for v in kq}
    assert not (tt & {"A", "I", "II", "III", "3.1", "3.2"})
    assert len(kq) == len([m for m in doc_checklist()
                           if not (m.la_chuong or m.la_tieu_de_khoi or m.tt == "A")])


def test_bao_cao_luon_noi_ro_han_che_va_khong_giau_muc_thieu():
    kq = dinh_vi(_doc(_h(0, "Cơ sở định cỡ")))
    md = bang_markdown(kq, ten_tai_lieu="x.docx")
    assert "cố vấn" in md and "KHÔNG TÌM THẤY" in md
    # không được diễn giải "không tìm thấy" thành "tài liệu thiếu mục"
    assert "không** có nghĩa tài liệu thiếu" in md
    assert bang_csv(kq).count("\n") == len(kq) + 1
