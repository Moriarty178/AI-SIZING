"""5.2 — tìm chỗ trong tài liệu mà một lỗi nói tới. OFFLINE, thuần Python."""
from src.ingestion.docx_reader import DocxDocument, Element
from src.luu_tru.cho_sua import TOI_DA_DOAN, TOI_DA_DONG_BANG, tim_cho_sua


def _doc(*els):
    return DocxDocument(path="x.docx", elements=list(els))


def _p(i, text, section="", page=None, kind="paragraph", rows=None):
    return Element(index=i, kind=kind, text=text, section=section, page=page, rows=rows)


DOC = _doc(
    _p(0, "Định cỡ máy chủ", section="IV.1", page=8, kind="heading"),
    _p(1, "Phân hệ Kafka dùng 12 core", section="IV.1", page=8),
    _p(2, "Phân hệ Redis dùng 32 GB RAM", section="IV.1", page=8),
    _p(3, "Ghi chú chung", section="IV.1", page=9),
    _p(4, "", section="IV.2", page=10, kind="table",
       rows=[["Phân hệ", "CPU"], ["Master", "8"]]),
    _p(5, "", section="IV.2", page=10, kind="image"),
)


def test_phan_tu_chinh_xac():
    c = tim_cho_sua(DOC, "phần tử #2", "Redis")
    assert c.cach_tim == "phan_tu" and [d.index for d in c.doan] == [2]


def test_muc_trang_dua_doan_nhac_ten_phan_he_len_dau():
    c = tim_cho_sua(DOC, "Mục IV.1, trang 8", "Redis")
    assert c.cach_tim == "muc_trang"
    assert [d.index for d in c.doan] == [2, 0, 1]
    assert "Redis" in c.ghi_chu


def test_muc_khong_trang_lay_ca_muc():
    c = tim_cho_sua(DOC, "Mục IV.1", "")
    assert c.cach_tim == "muc" and [d.index for d in c.doan] == [0, 1, 2, 3]


def test_ten_phan_he_bo_phan_trong_ngoac_khi_tim():
    """Phần trong ngoặc là mô tả C3 tự viết lại (5.0b), không chắc có trong tài liệu."""
    c = tim_cho_sua(DOC, "Mục IV.2, trang 10", "Master (K8s Control plane)")
    assert c.doan[0].index == 4


def test_bang_hien_bang_dong_va_bo_anh():
    c = tim_cho_sua(DOC, "Mục IV.2, trang 10", "")
    assert [d.kind for d in c.doan] == ["table"], "ảnh không có chữ để hiện"
    assert c.doan[0].rows[1] == ["Master", "8"]


def test_khong_vi_tri_thi_lui_ve_ten_phan_he_va_NOI_RO_la_goi_y():
    """NT4: đoạn nhắc tên phân hệ KHÔNG phải vị trí lỗi — không được giả làm vị trí."""
    c = tim_cho_sua(DOC, "", "Kafka")
    assert c.cach_tim == "ten_phan_he" and [d.index for d in c.doan] == [1]
    assert "KHÔNG phải vị trí chính xác" in c.ghi_chu


def test_vi_tri_cu_khong_con_khop_ban_moi_thi_lui_ve_ten_phan_he():
    """Người dùng sửa và nộp lại: `Mục IV.3` của bản cũ có thể không còn."""
    c = tim_cho_sua(DOC, "Mục IV.9, trang 99", "Kafka")
    assert c.cach_tim == "ten_phan_he" and "không còn khớp" in c.ghi_chu


def test_he_thong_KHONG_dem_di_tim_nhu_mot_ten():
    c = tim_cho_sua(DOC, "", "he_thong")
    assert c.cach_tim == "khong_tim_duoc" and c.doan == []


def test_khong_tim_duoc_thi_noi_ra_khong_tra_rong_im_lang():
    c = tim_cho_sua(DOC, "phần tử #999", "")
    assert c.cach_tim == "khong_tim_duoc" and "phần tử #999" in c.ghi_chu


def test_cat_so_doan_va_bao_con_bao_nhieu():
    doc = _doc(*[_p(i, f"đoạn {i}", section="I") for i in range(12)])
    c = tim_cho_sua(doc, "Mục I", "")
    assert len(c.doan) == TOI_DA_DOAN and c.con_nua == 12 - TOI_DA_DOAN


def test_cat_bang_dai_va_danh_dau():
    rows = [[f"r{i}", "x"] for i in range(TOI_DA_DONG_BANG + 10)]
    doc = _doc(_p(0, "", section="I", kind="table", rows=rows))
    d = tim_cho_sua(doc, "phần tử #0", "").doan[0]
    assert len(d.rows) == TOI_DA_DONG_BANG and d.cat_bot is True


def test_ra_json_duoc():
    import json
    json.dumps(tim_cho_sua(DOC, "Mục IV.1", "Redis").as_dict(), ensure_ascii=False)
