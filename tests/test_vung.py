"""5.3 — vùng phân hệ và vân tay nội dung (`src/extraction/vung.py`). OFFLINE."""
from src.extraction.schema import SizingCore, SizingExtension
from src.extraction.vung import chuan_ten, van_tay, vung_phan_he
from src.ingestion.docx_reader import DocxDocument, Element


def _e(i, kind="paragraph", text="", section="", page=None, rows=None, level=None):
    return Element(index=i, kind=kind, text=text or f"đoạn {i}", section=section,
                   page=page, rows=rows, level=level)


DOC = DocxDocument(path="x.docx", elements=[
    _e(0, "heading", "I. Giới thiệu", "I", level=1),
    _e(1, text="mở đầu", section="I"),
    _e(2, "heading", "1. Kafka", "III.1", level=2),
    _e(3, section="III.1"),
    _e(4, "table", "Kafka | 16", "III.1", rows=[["Kafka", "16"]]),
    _e(5, "heading", "2. Redis", "III.2", level=2),
    _e(6, "table", "Redis | 8", "III.2", rows=[["Redis", "8"]]),
    _e(7, "heading", "IV. Tổng hợp", "IV", level=1),
    _e(8, "table", "tổng | 24", "IV", rows=[["tổng", "24"]]),
])


def _core(*ph):
    return SizingCore(phan_he=list(ph))


def test_vung_la_khoang_phan_he_gioi_han_trong_muc_goc():
    """Phân hệ cuối KHÔNG nuốt Mục IV tổng hợp — cùng luật `phan_vung_bang`."""
    core = _core(SizingExtension(ten_phan_he="Kafka", element_index=4, muc="III.1"),
                 SizingExtension(ten_phan_he="Redis", element_index=6, muc="III.2"))
    vung, chung = vung_phan_he(DOC, core)
    assert vung == {"Kafka": [2, 3, 4], "Redis": [5, 6]}
    assert chung == [0, 1, 7, 8]


def test_phan_he_khong_neo_duoc_co_vung_la_ca_tai_lieu():
    core = _core(SizingExtension(ten_phan_he="Kafka", element_index=4, muc="III.1"),
                 SizingExtension(ten_phan_he="Mongo"))
    vung, chung = vung_phan_he(DOC, core)
    assert vung["Mongo"] == list(range(9))
    assert 4 not in chung and 8 in chung


def test_van_tay_bo_qua_so_trang_so_muc_va_chi_so():
    a = DocxDocument(path="a", elements=[_e(3, text="x", section="II.1", page=2)])
    b = DocxDocument(path="b", elements=[_e(9, text="x", section="II.4", page=7)])
    assert van_tay(a, [3]) == van_tay(b, [9])


def test_van_tay_doi_khi_mot_o_bang_doi():
    a = DocxDocument(path="a", elements=[_e(0, "table", "t", rows=[["CPU", "8"]])])
    b = DocxDocument(path="b", elements=[_e(0, "table", "t", rows=[["CPU", "12"]])])
    assert van_tay(a, [0]) != van_tay(b, [0])


def test_chuan_ten_cung_luat_khoa_baseline():
    assert chuan_ten("Master (K8s Master node)") == chuan_ten("master  (Control plane)") \
        == "master"
