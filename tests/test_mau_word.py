"""Test 1.16 — mẫu Word sinh từ checklist. Thuần code, không cần model."""
import tempfile

from src.ingestion.docx_reader import read_docx
from src.reporting.mau_word import (
    MucChecklist, doc_checklist, dung_mau, khoi_phan_he,
)


def test_doc_du_57_muc_checklist():
    """57 mục + 6 dòng tiêu đề (A, I, II, III, 3.1, 3.2) = 63 dòng."""
    m = doc_checklist()
    assert len(m) == 63
    muc = [x for x in m if not x.la_chuong and x.tt != "A" and not x.la_tieu_de_khoi]
    assert len(muc) == 57


def test_va_ba_loi_nguon_da_biet_chu_khong_sua_file_goc():
    """Ô A42 ghi 3.1.2 nhưng theo ngữ cảnh là 3.2; dòng 18 và 50 thiếu số thứ tự."""
    m = {x.dong: x for x in doc_checklist()}
    assert m["42"].tt == "3.2" and m["42"].la_tieu_de_khoi
    assert m["18"].tt == "2.10a"
    assert m["50"].tt == "3.2.7a"


def test_tieu_chi_dat_duoc_chep_nguyen_van_tu_checklist():
    """Người viết phải thấy đúng câu người thẩm định sẽ dùng để chấm."""
    m = {x.tt: x for x in doc_checklist()}
    assert "sizing cho ứng dụng mới hay sizing bổ sung" in m["2.1"].tieu_chi
    assert m["2.6"].tieu_chi.startswith("Gồm đầy đủ các thành phần")


def test_khoi_phan_he_dung_20_muc():
    assert len(khoi_phan_he(doc_checklist(), "3.1")) == 20


def test_phan_cap_dung():
    m = {x.tt: x for x in doc_checklist()}
    assert m["II"].la_chuong and m["II"].cap == 1
    assert m["3.1"].la_tieu_de_khoi and m["3.1"].cap == 2
    assert m["3.1.1"].cap == 3
    assert not m["2.1"].la_tieu_de_khoi        # "2.1" không thuộc phần III


# ------------------------------------------------------------------------
def _sinh(**kw) -> str:
    d = dung_mau(doc_checklist(), **kw)
    f = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    d.save(f.name)
    f.close()
    return f.name


def test_mau_sinh_ra_C1_DOC_LAI_DUOC():
    """Mẫu ta phát ra mà chính C1 không đọc được thì vô nghĩa."""
    doc = read_docx(_sinh(ten_he_thong="MyKid 2.0"))
    assert len(doc.elements) > 100
    assert len({e.section for e in doc.elements if e.section}) > 40
    txt = doc.full_text()
    assert "MyKid 2.0" in txt
    assert "Mô hình logic tổng quan" in txt


def test_khoi_20_muc_lap_cho_moi_phan_he_them():
    it = read_docx(_sinh()).full_text()
    nhieu = read_docx(_sinh(phan_he_them=["Redis", "Kafka"])).full_text()
    assert "Phân hệ Redis" in nhieu and "Phân hệ Redis" not in it
    assert nhieu.count("Mô tả chi tiết phân hệ") > it.count("Mô tả chi tiết phân hệ")


def test_tieu_chi_di_kem_vao_mau_de_nguoi_viet_biet_can_gi():
    assert "Tiêu chí đạt:" in read_docx(_sinh()).full_text()
