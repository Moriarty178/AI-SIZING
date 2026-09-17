"""5.3 — bản nộp lần này khác bản trước ở đâu (`src/ingestion/so_sanh.py`). OFFLINE."""
import json

from src.ingestion.docx_reader import DocxDocument, Element
from src.ingestion.so_sanh import TOI_DA_VI_TRI, so_sanh_ban


def _doc(*els):
    return DocxDocument(path="x.docx", elements=[
        Element(index=i, kind=k, text=t, section="II.1", page=p, rows=r)
        for i, (k, t, p, r) in enumerate(els)])


P = ("paragraph", "Kafka dùng 16 core", 3, None)
B = ("table", "CPU | 8", 3, [["CPU", "8"]])


def test_giong_het_thi_noi_ro():
    d = so_sanh_ban(_doc(P, B), _doc(P, B))
    assert d == {"giong_het": True, "sua": 0, "them": 0, "xoa": 0, "vi_tri": [],
                 "con_nua": 0}


def test_sua_mot_o_bang():
    d = so_sanh_ban(_doc(P, B), _doc(P, ("table", "CPU | 8", 3, [["CPU", "12"]])))
    assert (d["sua"], d["them"], d["xoa"]) == (1, 0, 0)
    assert d["vi_tri"] == ["Mục II.1, trang 3 · bảng · sửa"]


def test_chen_dau_lam_lech_trang_KHONG_tinh_la_doi():
    moi = _doc(("paragraph", "đoạn mới", 1, None), (P[0], P[1], 4, None),
               (B[0], B[1], 4, B[3]))
    d = so_sanh_ban(_doc(P, B), moi)
    assert (d["sua"], d["them"], d["xoa"]) == (0, 1, 0)


def test_xoa_lay_vi_tri_ban_cu():
    d = so_sanh_ban(_doc(P, B), _doc(P))
    assert d["xoa"] == 1 and d["vi_tri"] == ["Mục II.1, trang 3 · bảng (bản cũ) · xoá"]


def test_cat_danh_sach_vi_tri_va_ra_json_duoc():
    nhieu = [("paragraph", f"đoạn {i}", 1, None) for i in range(TOI_DA_VI_TRI + 5)]
    d = so_sanh_ban(_doc(), _doc(*nhieu))
    assert len(d["vi_tri"]) == TOI_DA_VI_TRI and d["con_nua"] == 5
    json.dumps(d, ensure_ascii=False)
