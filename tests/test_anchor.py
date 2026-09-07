"""Cổng neo dùng chung (C3 + C5) — thuần code, chạy offline."""
from src.ingestion.anchor import DAI_TOI_THIEU, chuan_hoa, neo
from src.ingestion.docx_reader import DocxDocument, Element


def _e(index: int, kind: str, text: str) -> Element:
    return Element(index=index, kind=kind, text=text, page=1, section="III")


def _doc(*els: Element) -> DocxDocument:
    return DocxDocument(path="giả.docx", elements=list(els), page_source="rendered")


# --- hành vi nền -----------------------------------------------------------
def test_khong_tim_thay_thi_tra_None_chu_khong_doan():
    doc = _doc(_e(1, "paragraph", "Hệ thống dùng 3 node Kafka."))
    assert neo(doc, "câu này không có trong tài liệu") == (None, -1)


def test_thu_tu_khoa_la_thu_tu_uu_tien():
    """Khoá đầu là bằng chứng mạnh; bên gọi dựa vào chỉ số trả về để hạ độ tin cậy."""
    doc = _doc(_e(1, "paragraph", "Redis chạy 3 node"), _e(2, "paragraph", "16 vCPU"))
    assert neo(doc, "Redis chạy 3 node", "16 vCPU")[1] == 0
    assert neo(doc, "câu không có thật", "16 vCPU")[1] == 1


def test_khoa_qua_ngan_bi_bo_qua_vi_khop_bua():
    doc = _doc(_e(1, "paragraph", "Hệ thống dùng 16 vCPU"))
    assert neo(doc, "16"[:DAI_TOI_THIEU - 1]) == (None, -1)


def test_khoang_gioi_han_vung_tim():
    doc = _doc(_e(1, "paragraph", "Redis 16 vCPU"), _e(9, "paragraph", "Redis 64 vCPU"))
    assert neo(doc, "Redis", khoang=(5, 12))[0].index == 9


def test_bo_tien_to_vi_tri_model_hay_chep_kem():
    doc = _doc(_e(1, "paragraph", "Hệ thống dùng 3 node Kafka."))
    assert neo(doc, "[Mục IV.1, trang 8] Hệ thống dùng 3 node Kafka.")[0].index == 1


def test_chuan_hoa_gop_khoang_trang_va_ha_chu_thuong():
    assert chuan_hoa("  Hệ   THỐNG \n dùng ") == "hệ thống dùng"


# --- ưu tiên heading -------------------------------------------------------
def test_uu_tien_heading_bo_qua_bang_thuat_ngu_o_dau_tai_lieu():
    """Hồi quy cho bản Vtag, lượt B1 2026-09-07.

    Quét theo thứ tự tài liệu thì tên phân hệ khớp trúng bảng «# | Tên | Mô tả» ở
    đầu tài liệu (#30) chứ không phải heading mở đầu mục của nó (#49). Mốc sai kéo
    theo khoảng phân hệ sai, và khoảng sai làm hỏng CẢ hai đường trích xuất: neo câu
    trượt, phân vùng bảng lệch. Trên bản Vtag, 5/6 phân hệ cùng trỏ vào #30 — tức
    việc tách phân hệ mất hẳn tác dụng.
    """
    doc = _doc(_e(30, "table", "# | Tên | Mô tả\n1 | Worker | Thành phần xử lý"),
               _e(49, "heading", "Định cỡ module Worker (N + 1)"),
               _e(50, "paragraph", "Worker cần 16 vCPU"))
    assert neo(doc, "Worker")[0].index == 30                        # hành vi cũ
    assert neo(doc, "Worker", uu_tien_kind="heading")[0].index == 49


def test_uu_tien_heading_van_giu_thu_tu_khoa():
    """Khoá mạnh hơn thắng, kể cả khi khoá yếu hơn có một heading đẹp hơn: tên phân
    hệ là bằng chứng mạnh hơn tên công nghệ."""
    doc = _doc(_e(1, "paragraph", "Redis Cluster dùng 3 node"),
               _e(2, "heading", "Phụ lục Redis"))
    el, i = neo(doc, "Redis Cluster", "Redis", uu_tien_kind="heading")
    assert (el.index, i) == (1, 0)


def test_khong_co_heading_thi_roi_ve_hanh_vi_cu():
    """Ba hồ sơ dev còn lại không có heading trùng tên phân hệ — thay đổi này phải
    THÊM chứ không được lấy đi cái đang chạy được."""
    doc = _doc(_e(7, "table", "ELK Stack | 16 | 32"))
    assert neo(doc, "ELK Stack", uu_tien_kind="heading")[0].index == 7
