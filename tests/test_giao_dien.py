"""Test 1.14 — logic giao diện. Chạy offline, KHÔNG cần cài Streamlit.

Điều quan trọng nhất phải giữ: giao diện **dùng được khi không có model**. Model tự
dựng chỉ với tới được từ máy trong mạng nội bộ, nên một giao diện nổ traceback lúc
thiếu cấu hình là một giao diện vô dụng ở đúng nơi phần lớn công việc diễn ra.
"""
import pathlib

import pytest

from src.giao_dien import (CAN_MODEL, CHE_DO, TrangThaiModel, chay_checklist,
                           che_do_kha_dung, kiem_model, luu_tam,
                           ten_file_ket_qua, tom_tat_tai_lieu, uoc_luong)
from src.ingestion.docx_reader import DocxDocument, Element


def _doc(*els: Element) -> DocxDocument:
    return DocxDocument(path="giả.docx", elements=list(els), page_source="rendered")


def _bang(i: int, rows: list[list[str]]) -> Element:
    return Element(index=i, kind="table", section="III", page=1, rows=rows,
                   text=" ".join(c for r in rows for c in r))


# ------------------------------------------------------- không có model ----
def test_thieu_cau_hinh_thi_BAO_chu_khong_no(tmp_path):
    """`kiem_model` không được ném lỗi — giao diện phải hiện được trong mọi ca."""
    tt = kiem_model(settings_path=str(tmp_path / "khong-co.yaml"))
    assert tt.san_sang is False
    assert "Chưa có cấu hình model" in tt.thong_diep
    assert tt.nhan.startswith("⚠️")


def test_thieu_bien_moi_truong_cung_BAO_chu_khong_no(tmp_path, monkeypatch):
    p = tmp_path / "settings.yaml"
    p.write_text("llm:\n  base_url: http://x\n  chat_model: m\n", encoding="utf-8")
    monkeypatch.delenv("SIZING_COPILOT_API_KEY", raising=False)
    tt = kiem_model(settings_path=str(p))
    assert tt.san_sang is False and "SIZING_COPILOT_API_KEY" in tt.thong_diep


def test_khong_co_model_thi_van_con_cac_che_do_khong_can_model():
    kd = che_do_kha_dung(TrangThaiModel(False, "chưa cấu hình"))
    assert set(kd) == set(CHE_DO) - CAN_MODEL
    assert "checklist" in kd and "doc" in kd     # hai việc làm được ở laptop


def test_co_model_thi_du_ca_ba_che_do():
    assert set(che_do_kha_dung(TrangThaiModel(True, "ok"))) == set(CHE_DO)


# ------------------------------------------------------------ ước lượng ---
def test_uoc_luong_tinh_TRUOC_khi_goi_model():
    """Bấm chạy rồi ngồi chờ mù đã đốt vài lượt chạy ngày 2026-09-04."""
    doc = _doc(_bang(1, [["STT", "CPU (Cint)", "RAM (GB)"], ["1", "48", "500"]]))
    ul = uoc_luong(doc, so_phan_he=5)
    assert ul.so_bang == 1 and ul.tong == ul.c3 + ul.c5 > 0
    assert "giả định 5 phân hệ" in ul.mo_ta(6)


def test_uoc_luong_tang_theo_so_phan_he():
    """Sai số tham số này rất lớn: BCCS3 có 13 phân hệ, mặc định cũ là 3."""
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]))
    assert uoc_luong(doc, so_phan_he=13).tong > uoc_luong(doc, so_phan_he=3).tong


def test_song_song_rut_ngan_thoi_gian_uoc_tinh():
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]))
    ul = uoc_luong(doc, so_phan_he=5)
    assert ul.phut(6) == pytest.approx(ul.phut(1) / 6)


# ------------------------------------------------------------- tài liệu ---
def test_tom_tat_dem_ca_bang_CO_SO_LIEU():
    """Số bảng thôi chưa đủ: bảng không có cột số liệu thì đường cột của C3 bỏ qua."""
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]),
               _bang(2, [["Cấu hình", "Ghi chú"], ["Thông lượng >= 1 Gbps", ""]]),
               Element(index=3, kind="image", section="II", page=1))
    t = tom_tat_tai_lieu(doc)
    assert (t.bang, t.bang_du_lieu, t.anh) == (2, 1, 1)
    assert "1 có số liệu" in t.dong_tom_tat


# ------------------------------------------------------------ checklist ---
def test_chay_checklist_khong_can_model():
    doc = _doc(Element(index=0, kind="heading", text="Cơ sở định cỡ",
                       section="I", page=1, level=1))
    kq = chay_checklist(doc, ten_tai_lieu="x.docx")
    assert kq.tong > 0 and kq.thay >= 1
    assert "KHÔNG TÌM THẤY" in kq.markdown
    assert kq.csv.startswith("TT,")


# --------------------------------------------------------------- tệp ------
def test_luu_tam_giu_nguyen_ten_goc(tmp_path):
    """Tên hồ sơ mang mã PYC và tên hệ thống, còn hiện lại trong báo cáo."""
    p = luu_tam(b"xyz", "Sizing_BCCS3_Lào.docx", str(tmp_path))
    assert p.name == "Sizing_BCCS3_Lào.docx" and p.read_bytes() == b"xyz"


def test_luu_tam_chan_duong_dan_lo_ra_ngoai(tmp_path):
    p = luu_tam(b"x", "../../thoat.docx", str(tmp_path))
    assert p.parent == tmp_path


def test_ten_file_ket_qua():
    assert ten_file_ket_qua("a/b/Sizing X.docx", "checklist", "csv") == \
        "Sizing X-checklist.csv"


# ------------------------------------------------- chính trang Streamlit ---
# Chỉ chạy khi máy có cài Streamlit (nó nằm ở nhóm phụ thuộc tuỳ chọn `ui`).
# `AppTest` chạy thật `ui/app.py` không cần trình duyệt, nên bắt được lỗi cú pháp,
# import sai, hay API Streamlit dùng nhầm — những thứ mà test logic không thấy.
st_test = pytest.importorskip("streamlit.testing.v1", reason="chưa cài streamlit")


GOC = pathlib.Path(__file__).resolve().parents[1]


def _chay_app():
    # Đường dẫn TƯƠNG ĐỐI được `AppTest` giải theo file gọi nó, không theo thư mục
    # chạy pytest — nên phải đưa đường dẫn tuyệt đối.
    at = st_test.AppTest.from_file(str(GOC / "ui" / "app.py"), default_timeout=30)
    at.run()
    return at


def test_trang_chay_duoc_khi_CHUA_co_model(monkeypatch):
    """Ca thường gặp nhất khi làm việc ngoài mạng nội bộ. Không được có exception."""
    monkeypatch.delenv("SIZING_COPILOT_API_KEY", raising=False)
    at = _chay_app()
    assert not at.exception
    assert any("cố vấn" in m.value for m in at.sidebar.caption)


def test_trang_hien_o_TAI_TEP_khi_chua_chon_gi():
    at = _chay_app()
    assert not at.exception
    assert len(at.file_uploader) == 1
