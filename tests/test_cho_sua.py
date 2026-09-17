"""5.2 — tìm chỗ trong tài liệu mà một lỗi nói tới. OFFLINE, thuần Python.

Hai lớp cuối dựng lại đúng hai ca trong ảnh chụp nghiệm thu 2026-09-17.
"""
from src.ingestion.docx_reader import DocxDocument, Element
from src.luu_tru.cho_sua import (TOI_DA_DOAN, TOI_DA_DOAN_GOI_Y, TOI_DA_DONG_BANG,
                                 tim_cho_sua)


def _doc(*els):
    return DocxDocument(path="x.docx", elements=list(els))


def _p(i, text, section="", page=None, kind="paragraph", rows=None, level=None):
    return Element(index=i, kind=kind, text=text, section=section, page=page,
                   rows=rows, level=level)


DOC = _doc(
    _p(0, "Định cỡ máy chủ", section="IV.1", page=8, kind="heading", level=2),
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


def test_muc_trang_giu_THU_TU_TAI_LIEU():
    """Ảnh nghiệm thu: xếp đoạn nhắc tên lên trước làm nhãn ngắn chiếm hết chỗ, bảng
    số rơi ra ngoài. Trong một mục, nhãn và bảng đi thành cặp."""
    c = tim_cho_sua(DOC, "Mục IV.1, trang 8", "Redis")
    assert c.cach_tim == "muc_trang"
    assert [d.index for d in c.doan] == [0, 1, 2]
    assert "thứ tự" in c.ghi_chu


def test_muc_khong_trang_lay_ca_muc():
    c = tim_cho_sua(DOC, "Mục IV.1", "")
    assert c.cach_tim == "muc" and [d.index for d in c.doan] == [0, 1, 2, 3]


def test_bang_hien_bang_dong_va_bo_anh():
    c = tim_cho_sua(DOC, "Mục IV.2, trang 10", "")
    assert [d.kind for d in c.doan] == ["table"], "ảnh không có chữ để hiện"
    assert c.doan[0].rows[1] == ["Master", "8"]


def test_khong_vi_tri_va_khong_tieu_de_thi_goi_y_phan_tu_roi_va_NOI_RO():
    """NT4: đoạn nhắc tên phân hệ KHÔNG phải vị trí lỗi — không được giả làm vị trí."""
    c = tim_cho_sua(DOC, "", "Kafka")
    assert c.cach_tim == "ten_phan_he" and [d.index for d in c.doan] == [1]
    assert "KHÔNG phải vị trí chính xác" in c.ghi_chu


def test_vi_tri_cu_khong_con_khop_ban_moi_thi_lui_ve_goi_y():
    """Người dùng sửa và nộp lại: `Mục IV.9` của bản cũ có thể không còn."""
    c = tim_cho_sua(DOC, "Mục IV.9, trang 99", "Kafka")
    assert c.cach_tim == "ten_phan_he" and "không còn khớp" in c.ghi_chu


def test_he_thong_KHONG_dem_di_tim_nhu_mot_ten():
    c = tim_cho_sua(DOC, "", "he_thong")
    assert c.cach_tim == "khong_tim_duoc" and c.doan == []


def test_khong_tim_duoc_thi_noi_ra_khong_tra_rong_im_lang():
    c = tim_cho_sua(DOC, "phần tử #999", "")
    assert c.cach_tim == "khong_tim_duoc" and "phần tử #999" in c.ghi_chu


def test_cat_so_doan_va_bao_con_bao_nhieu():
    doc = _doc(*[_p(i, f"đoạn {i}", section="I") for i in range(TOI_DA_DOAN + 8)])
    c = tim_cho_sua(doc, "Mục I", "")
    assert len(c.doan) == TOI_DA_DOAN and c.con_nua == 8


def test_cat_bang_dai_va_danh_dau():
    rows = [[f"r{i}", "x"] for i in range(TOI_DA_DONG_BANG + 10)]
    doc = _doc(_p(0, "", section="I", kind="table", rows=rows))
    d = tim_cho_sua(doc, "phần tử #0", "").doan[0]
    assert len(d.rows) == TOI_DA_DONG_BANG and d.cat_bot is True


def test_ra_json_duoc():
    import json
    json.dumps(tim_cho_sua(DOC, "Mục IV.1", "Redis").as_dict(), ensure_ascii=False)


# --- ảnh 2 nghiệm thu: lỗi «Mongo» không có vị trí --------------------------------
MAY_CHU = [["Máy chủ", "IP"], ["Nginx LoadBalancer", "172.21.5.244"]] + \
    [[f"Master 0{i}", f"172.21.5.{245 + i}"] for i in range(1, 30)] + \
    [["Mongo 01", "172.21.5.90"]]
DOC_MONGO = _doc(
    _p(0, "", page=3, kind="table", rows=MAY_CHU),
    _p(1, "", page=4, kind="table",
       rows=[["Phân hệ", "Cores"], ["Video Streaming", "16"], ["Mongo", "8"]]),
    _p(2, "Định cỡ module Mongo (N + 1)", section="1.1", page=14, kind="heading",
       level=3),
    _p(3, "Mức tiêu thụ CPU của Mongo", section="1.1", page=14),
    _p(4, "", section="1.1", page=14, kind="table", rows=[["CPU", "RAM"], ["8", "32"]]),
    _p(5, "Định cỡ module Redis", section="1.2", page=15, kind="heading", level=3),
    _p(6, "Redis dùng 16 GB", section="1.2", page=15),
)


class TestAnhNghiemThuMongo:
    def test_co_tieu_de_nhac_ten_thi_hien_CA_MUC_do(self):
        c = tim_cho_sua(DOC_MONGO, "", "Mongo")
        assert c.cach_tim == "ten_phan_he"
        assert [d.index for d in c.doan] == [2, 3, 4], "tiêu đề + nội dung tới mục sau"
        assert "MỤC có tiêu đề" in c.ghi_chu and "KHÔNG phải vị trí" in c.ghi_chu

    def test_muc_dung_o_tieu_de_cung_cap(self):
        c = tim_cho_sua(DOC_MONGO, "", "Mongo")
        assert 5 not in [d.index for d in c.doan]

    def test_tieu_de_con_KHONG_cat_muc(self):
        doc = _doc(_p(0, "Định cỡ Mongo", kind="heading", level=2),
                   _p(1, "CPU", kind="heading", level=3),
                   _p(2, "8 core"),
                   _p(3, "Định cỡ Redis", kind="heading", level=2))
        assert [d.index for d in tim_cho_sua(doc, "", "Mongo").doan] == [0, 1, 2]

    def test_khong_tieu_de_thi_bang_CHI_hien_dong_nhac_ten(self):
        """Ảnh 2: 25 dòng đầu của bảng máy chủ không có dòng Mongo nào — người dùng
        không thấy vì sao bảng hiện ra."""
        doc = _doc(DOC_MONGO.elements[0], DOC_MONGO.elements[1])
        c = tim_cho_sua(doc, "", "Mongo")
        bang = c.doan[0]
        assert bang.rows == [["Máy chủ", "IP"], ["Mongo 01", "172.21.5.90"]]
        assert bang.loc_theo_ten is True and bang.tong_dong == len(MAY_CHU)

    def test_goi_y_roi_xep_doan_van_truoc_bang(self):
        doc = _doc(_p(0, "", kind="table", rows=[["a"], ["Mongo"]]),
                   _p(1, "Mongo chạy 3 node"))
        c = tim_cho_sua(doc, "", "Mongo")
        assert [d.kind for d in c.doan] == ["paragraph", "table"]
        assert len(c.doan) <= TOI_DA_DOAN_GOI_Y


# --- ảnh 3 nghiệm thu: EVD-17 FrontEnd, «Mục 1.1, trang 18» ------------------------
class TestAnhNghiemThuFrontEnd:
    def test_bang_so_KHONG_bi_nhan_ngan_day_ra_ngoai(self):
        els = [_p(0, "Định cỡ phân hệ FrontEnd.", section="1.1", page=18,
                  kind="heading", level=3)]
        for i, nhan in enumerate(["CPU", "RAM", "log", "CPU & RAM"]):
            els.append(_p(1 + 2 * i, f"Mức tiêu thụ {nhan} của FrontEnd", section="1.1",
                          page=18))
            els.append(_p(2 + 2 * i, "", section="1.1", page=18, kind="table",
                          rows=[["Chỉ số", "Giá trị"], ["đỉnh", str(90 + i)]]))
        c = tim_cho_sua(_doc(*els), "Mục 1.1, trang 18", "FrontEnd")
        assert [d.kind for d in c.doan].count("table") == 4
        assert c.con_nua == 0

    def test_trong_muc_bang_KHONG_bi_loc_theo_ten(self):
        """Bảng của mục FrontEnd không lặp chữ «FrontEnd» ở từng dòng CPU/RAM — lọc là
        mất đúng con số cần sửa."""
        doc = _doc(_p(0, "", section="1.1", page=18, kind="table",
                      rows=[["FrontEnd", ""], ["CPU", "12"], ["RAM", "32"]]))
        d = tim_cho_sua(doc, "Mục 1.1, trang 18", "FrontEnd").doan[0]
        assert len(d.rows) == 3 and d.loc_theo_ten is False
