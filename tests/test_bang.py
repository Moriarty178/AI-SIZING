"""Test C3 v6 — đường CỘT. Chạy hoàn toàn OFFLINE.

Điều phải giữ được, và là toàn bộ lý do đảo chiều câu hỏi: **số giá trị sinh ra không
bao giờ vượt quá số cột dữ liệu của bảng**. Ba vòng v3–v5 đều lọc sau khi model đã điền
bừa; ở đây lược đồ không có chỗ để điền bừa. Test đầu tiên khoá đúng tính chất đó.
"""
import pytest

from src.extraction.bang import (KHONG_RO, cot_du_lieu, la_o_so, luoc_do_bang,
                                 nhan_dong, phan_vung_bang, tham_so_so)
from src.extraction.extractor import Extractor, so_bang_dung_duoc
from src.extraction.plan import ThamSo
from src.extraction.schema import ExtractedValue, SizingCore, SizingExtension
from src.ingestion.docx_reader import DocxDocument, Element
from tests.test_extraction import FakeLLM

# Đúng hình dạng bảng của BCCS3 (đo 2026-09-04): cột STT và cột «Ghi chú» là bẫy —
# một cột đánh số, một cột rỗng.
BANG_CAU_HINH = [
    ["STT", "Nội dung", "CPU (Cint)", "RAM (GB)", "Ghi chú"],
    ["1", "Tài nguyên cài đặt 1 node DBIN", "16", "16", ""],
]
BANG_TONG = [
    ["N", "CPU", "RAM", "Storage (TB)"],
    ["1", "64", "64", "4"],
    ["4", "16", "16", "1"],
]


def _bang(index: int, rows: list[list[str]], section: str = "III") -> Element:
    return Element(index=index, kind="table", text=" ".join(c for r in rows for c in r),
                   page=3, section=section, rows=rows)


def _doc(*els: Element) -> DocxDocument:
    return DocxDocument(path="giả.docx", elements=list(els), page_source="rendered")


def _ts(name: str, unit: str = "") -> ThamSo:
    return ThamSo(name=name, kieu="so", unit=unit, scope="phan_he")


# ------------------------------------------------------- nhận cột dữ liệu --
def test_cot_van_xuoi_khong_bao_gio_duoc_hoi():
    """Cột «Nội dung» và «Ghi chú» không phải cột dữ liệu.

    Hồi quy cho v5: `he_so_sai_so_khai = 1.1` đã được lấy từ cột «Nội dung» của một
    bảng mô tả — con số nằm trong câu, không phải một trường dữ liệu.
    """
    assert cot_du_lieu(_bang(9, BANG_CAU_HINH)) == [
        (0, "STT"), (2, "CPU (Cint)"), (3, "RAM (GB)")]


def test_bang_khong_co_cot_so_thi_khong_hoi_lan_nao():
    e = _bang(9, [["Cấu hình", "Ghi chú"], ["Thông lượng >= 1 Gbps", ""]])
    assert cot_du_lieu(e) == []


@pytest.mark.parametrize("s,mong", [
    ("16", True), ("1.500", True), ("2 TB", True), ("92%", True),
    ("", False), ("Tài nguyên cài đặt 1 node database", False),
    ("Server ảo hóa nên không đề xuất switch", False),
])
def test_o_so(s, mong):
    assert la_o_so(s) is mong


# ------------------------------------------------------ trần cấu trúc ------
def test_luoc_do_co_dung_MOT_truong_moi_cot():
    """Đây là cả luận điểm của v6: model không thể trả nhiều hơn số cột."""
    e = _bang(9, BANG_CAU_HINH)
    cot = cot_du_lieu(e)
    lop = luoc_do_bang(e, cot, [_ts("cpu_95th"), _ts("ram_cau_hinh_gb")], False)
    assert set(lop.model_fields) == {"cot_0", "cot_2", "cot_3"}
    enum = lop.model_json_schema()["properties"]["cot_2"]["enum"]
    assert enum == ["cpu_95th", "ram_cau_hinh_gb", KHONG_RO]


def test_bang_nhieu_dong_thi_lươc_do_bat_chon_dong():
    e = _bang(9, BANG_TONG)
    lop = luoc_do_bang(e, cot_du_lieu(e), [_ts("tong_su_dung")], True)
    assert "dong" in lop.model_fields
    assert nhan_dong(e) == ["1", "4"]


# ------------------------------------------------------------- trích ------
def _chay_bang(dap_an: dict, rows=BANG_CAU_HINH, uv=None, index=9):
    e = _bang(index, rows)
    doc = _doc(e)
    dich = SizingExtension(ten_phan_he="DBIN", element_index=index)
    ex = Extractor(FakeLLM(dap_an))
    ex.trich_bang(doc, e, dich, uv or [_ts("cpu_95th", "%"), _ts("ram_cau_hinh_gb", "GB")])
    return ex, dich


def test_code_doc_o_chu_khong_phai_model_doc():
    """Model chỉ NÓI cột nào là tham số nào; con số do code lấy từ ô (NT1 + NT2)."""
    ex, dich = _chay_bang({"GanBang9": {
        "cot_0": KHONG_RO, "cot_2": "cpu_95th", "cot_3": "ram_cau_hinh_gb"}})
    assert dich.params["ram_cau_hinh_gb"].value == 16.0
    assert dich.params["ram_cau_hinh_gb"].element_index == 9
    assert "cột «RAM (GB)»" in dich.params["ram_cau_hinh_gb"].note
    assert ex.tk.cot_gan_duoc == 2 and ex.tk.cot_khong_ro == 1
    assert ex.tk.cot_hoi == 3


def test_hai_cot_cung_gia_tri_khong_bi_coi_la_tranh_mot_o():
    """`CPU 16 | RAM 16`: cùng con số, khác cột — cổng một-ô-một-tham-số không được bỏ."""
    ex, dich = _chay_bang({"GanBang9": {
        "cot_0": KHONG_RO, "cot_2": "cpu_95th", "cot_3": "ram_cau_hinh_gb"}})
    assert ex.loc_o_bi_nhieu_tham_so(dich) == 0
    assert dich.params["cpu_95th"].value == 16.0
    assert dich.params["ram_cau_hinh_gb"].value == 16.0


def test_hai_cot_nhan_cung_tham_so_thi_bo_ca_hai():
    ex, dich = _chay_bang({"GanBang9": {
        "cot_0": KHONG_RO, "cot_2": "cpu_95th", "cot_3": "cpu_95th"}})
    assert "cpu_95th" not in dich.params
    assert ex.tk.cot_trung_tham_so == 2 and ex.tk.cot_gan_duoc == 0


def test_nhan_dong_khong_co_that_thi_bo_ca_bang():
    """Không định vị được dòng ⇒ không có căn cứ (NT2), không đoán dòng nào."""
    ex, dich = _chay_bang({"GanBang9": {
        "dong": "dòng tổng", "cot_0": KHONG_RO, "cot_1": "cpu_95th",
        "cot_2": "ram_cau_hinh_gb", "cot_3": KHONG_RO}}, rows=BANG_TONG)
    assert dich.params == {} and ex.tk.bang_mat_dong == 1


def test_chon_dung_dong_model_chi_toi():
    ex, dich = _chay_bang({"GanBang9": {
        "dong": "4", "cot_0": KHONG_RO, "cot_1": "cpu_95th",
        "cot_2": "ram_cau_hinh_gb", "cot_3": KHONG_RO}}, rows=BANG_TONG)
    assert dich.params["cpu_95th"].value == 16.0        # dòng «4», không phải «1» (64)
    assert "dòng «4»" in dich.params["cpu_95th"].note


def test_luot_goi_hong_khong_sinh_gia_tri_nao():
    ex, dich = _chay_bang({})                           # FakeLLM ném ExtractionFailed
    assert dich.params == {} and ex.tk.luot_goi_hong == 1


def test_gia_tri_ngoai_khoang_van_bi_chan():
    """Đường cột không được bỏ qua các cổng đơn vị của 1.4: 16 cho một trường `%`
    thì hợp lệ, nhưng 64 cho `cpu_95th_ty_le` (0–1) thì không."""
    ex, dich = _chay_bang({"GanBang9": {
        "dong": "1", "cot_0": KHONG_RO, "cot_1": "cpu_95th_ty_le",
        "cot_2": KHONG_RO, "cot_3": KHONG_RO}},
        rows=BANG_TONG, uv=[_ts("cpu_95th_ty_le", "tỷ lệ 0–1")])
    assert dich.params["cpu_95th_ty_le"].value is None
    assert ex.tk.ngoai_khoang_hop_le == 1


# --------------------------------------------------- mâu thuẫn giữa bảng ---
def test_hai_bang_hai_so_cho_cung_tham_so_thi_bo_ca_hai():
    ph = SizingExtension(ten_phan_he="DBIN")
    ex = Extractor(FakeLLM({}))
    t = _ts("cpu_95th", "%")
    ex._ghi_nhan(ph, "cpu_95th", ex._so(t, "16", ExtractedValue(
        raw="16", element_index=9, o_nguon="r0c2")), "bảng #9")
    assert ph.params["cpu_95th"].value == 16.0
    ex._ghi_nhan(ph, "cpu_95th", ex._so(t, "48", ExtractedValue(
        raw="48", element_index=19, o_nguon="r0c2")), "bảng #19")
    assert ph.params["cpu_95th"].value is None
    assert ex.tk.mau_thuan_giua_bang == 1
    assert "cho giá trị khác" in ph.params["cpu_95th"].note


# ------------------------------------------------------------ phân vùng ---
def test_bang_ngoai_muc_cua_phan_he_khong_thuoc_phan_he_do():
    """Phân hệ cuối không được nuốt bảng tổng hợp ở mục sau.

    Hồi quy cho v5: Firewall (#105, Mục III) sẽ ôm luôn bảng thiết bị #111 ở Mục IV
    nếu chỉ chặn theo khoảng phần tử.
    """
    doc = _doc(_bang(10, BANG_CAU_HINH, "III"), _bang(30, BANG_TONG, "IV"))
    core = SizingCore(phan_he=[SizingExtension(
        ten_phan_he="Firewall", muc="III", element_index=10)])
    vung = {e.index: ph for e, ph, _ in phan_vung_bang(doc, core)}
    assert vung[10] is not None and vung[10].ten_phan_he == "Firewall"
    assert vung[30] is None            # Mục IV — của cả hệ thống, không của Firewall


def test_so_bang_dung_duoc_dem_dung():
    doc = _doc(_bang(1, BANG_CAU_HINH),
               _bang(2, [["Cấu hình", "Ghi chú"], ["Thông lượng >= 1 Gbps", ""]]))
    assert so_bang_dung_duoc(doc) == 1


def test_ung_vien_chi_gom_tham_so_kieu_so_dung_pham_vi():
    uv = tham_so_so(scope="phan_he")
    assert all(t.kieu == "so" and t.scope == "phan_he" for t in uv)
    assert any(t.name == "cpu_95th" for t in uv)
