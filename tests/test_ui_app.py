"""Chạy THẬT kịch bản Streamlit `ui/app.py` bằng bộ test của Streamlit.

Cú pháp đúng KHÔNG có nghĩa là giao diện chạy được: `ui/app.py` gọi hàng chục API
của Streamlit và của `src/`, và một tên sai chỉ lộ ra khi kịch bản chạy. Trước
bản này, cách duy nhất để biết là dựng container rồi mở trình duyệt.

Không cần model: `kiem_model()` chỉ đọc `config/settings.yaml`; thiếu file thì
giao diện vào nhánh "chưa cấu hình" — vẫn là một nhánh phải chạy được.
"""
import pathlib

import pytest

pytest.importorskip("streamlit", reason="cài với: uv sync --extra ui")
from streamlit.testing.v1 import AppTest        # noqa: E402

DUONG_DAN = str(pathlib.Path(__file__).resolve().parents[1] / "ui" / "app.py")


@pytest.fixture
def app():
    at = AppTest.from_file(DUONG_DAN, default_timeout=90)
    at.run()
    return at


def test_giao_dien_chay_khong_ngoai_le(app):
    assert not app.exception, [str(getattr(e, "value", e)) for e in app.exception]


def test_D3_gioi_han_hien_SAN_o_thanh_ben(app):
    """Giấu giới hạn sau một cú bấm là để phần lớn người xem không bao giờ thấy."""
    van = " ".join(str(c.value) for c in app.sidebar.caption)
    assert "87,5%" in van, "phải nêu con số đo được, không làm tròn thành 88%"
    assert "1,4%" in van, "phải nêu cả con số YẾU NHẤT, không chỉ con số đẹp"
    assert "Chưa đo được tỉ lệ báo sai" in van
    assert "không phải** lỗi của bản sizing" in van


def test_D4_co_nut_tai_mau_Word_khi_chua_nop_gi(app):
    """Người đánh giá cần một file để thử NGAY, không phải đi xin hồ sơ thật."""
    nhan = [b.label for b in app.download_button]
    assert any("mẫu Word" in n for n in nhan), nhan


def test_mau_Word_dung_duoc_thanh_docx_that():
    """Nút tải về mà ra file hỏng thì tệ hơn không có nút.

    Bộ test của Streamlit không lộ nội dung `download_button`, nên kiểm thẳng
    hàm mà `ui/app.py` gọi — đúng thứ quyết định file tải về có mở được không.
    """
    import io
    import zipfile
    from src.reporting.mau_word import doc_checklist, dung_mau
    buf = io.BytesIO()
    dung_mau(doc_checklist()).save(buf)
    with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
        assert "word/document.xml" in z.namelist()
    assert buf.tell() > 10_000, "mẫu rỗng thì người đánh giá không thử được gì"


def test_bang_phan_hoi_dung_cac_ham_logic_that():
    """Bộ test của Streamlit không điều khiển được `data_editor` sâu, nên kiểm
    đúng chuỗi hàm mà `_bang_phan_hoi` gọi với dữ liệu findings thật shape."""
    from src.giao_dien import (NHAN_PHAN_LOAI, chuan_bi_bang, gom_thay_doi,
                               loc_bang, spec_cot_bang)
    assert set(spec_cot_bang()) >= {"nội dung", "ghi_chu", "phân loại"}
    fs = [{"id": "KPI-02#App", "severity": "major", "category": "vuot_nguong",
           "finding": "CPU vượt ngưỡng", "rule_ref": "KPI-02", "rule_quote": "",
           "location": "Mục IV.1, trang 8", "computed_evidence": "",
           "suggestion": "", "confidence": "cao", "checklist_ref": [],
           "vong": 2, "scope_key": "App", "source_doc": "", "nhom": "vong2_chua_dat"}]
    rows_goc = chuan_bi_bang(fs, {})
    assert len(rows_goc) == 1
    rows = loc_bang(rows_goc, "Tất cả")
    assert rows == rows_goc
    # nhãn selectbox khớp giá trị mặc định của dòng
    assert rows[0]["phân loại"] in NHAN_PHAN_LOAI
    # diff với chính nó rỗng — Lưu hai lần không nhân bản
    assert gom_thay_doi(rows, [dict(r) for r in rows]) == []


# --- 5.0a: danh tính demo ----------------------------------------------------
class TestDanhTinhDemo:
    def test_co_o_chon_vai_va_o_nhap_ten(self, app):
        assert [s.label for s in app.sidebar.selectbox] == ["Vai"]
        assert [t.label for t in app.sidebar.text_input] == ["Tên"]

    def test_NOI_RA_la_khong_xac_thuc(self, app):
        """Không nói thì người xem tưởng «vai Admin» là quyền thật."""
        van = " ".join(str(c.value) for c in app.sidebar.caption)
        assert "KHÔNG xác thực" in van

    def test_KHONG_cho_chon_vai_he_thong(self, app):
        """`he_thong` dành cho dòng máy ghi."""
        assert "he_thong" not in list(app.sidebar.selectbox[0].options)
        assert "Hệ thống" not in list(app.sidebar.selectbox[0].options)

    def test_nhap_ten_thi_danh_tinh_vao_phien(self, app):
        app.sidebar.selectbox[0].set_value("admin")
        app.sidebar.text_input[0].set_value("  Nguyễn   Văn A ").run()
        assert not app.exception
        dt = app.session_state["danh_tinh"]
        assert (dt.vai, dt.ten) == ("admin", "Nguyễn Văn A")

    def test_chua_nhap_ten_thi_nhac_chu_KHONG_chan_gi(self, app):
        """Chưa có tính năng nào ghi theo danh tính (bắt đầu từ 5.1): chặn bây giờ
        là chặn luôn phần nộp bài đang chạy tốt."""
        assert app.session_state["danh_tinh"] is None
        assert not app.sidebar.warning or all(
            "tên" not in str(w.value).lower() for w in app.sidebar.warning)
        assert len(app.file_uploader) == 1
