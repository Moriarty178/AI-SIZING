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
    assert "7%" in van, "phải nêu cả con số YẾU, không chỉ con số đẹp"
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
