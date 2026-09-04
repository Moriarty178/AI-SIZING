"""Test 1.7 — C3. Chạy hoàn toàn OFFLINE bằng transport giả.

Phần lớn là hồi quy cho ba quyết định thiết kế ở đầu `extractor.py`: model trả nguyên
văn, trích dẫn phải neo được, enum chỉ lấy khi tài liệu nêu rõ. Hai cái sau là cổng
chống bịa — nếu chúng hỏng thì C3 sẽ đưa số không có thật vào C4 mà không ai thấy.
"""
import json

import pytest

from src.extraction.extractor import (
    Extractor, GiaTriBool, GiaTriSo, ThongTinChung, luoc_do_nhom,
)
from src.extraction.plan import NhomTrich, ThamSo, ke_hoach_trich, tham_so_cua_bo_quy_tac
from src.ingestion.docx_reader import DocxDocument, Element
from src.llm.client import ExtractionFailed, LLMClient


# ----------------------------------------------------------- đồ giả --------
class FakeLLM(LLMClient):
    """Thay phần gọi mạng bằng đáp án định sẵn, khoá theo tên lược đồ."""

    def __init__(self, dap_an: dict):
        self.dap_an = dap_an
        self.goi: list[str] = []
        self.chat_model, self.temperature, self.cfg = "fake", 0.0, {}
        self.last_attempts, self.last_schema_path = 1, "json_schema"

    def extract(self, schema, messages, *, model=None, max_retries=3, max_tokens=4000):
        self.goi.append(schema.__name__)
        p = self.dap_an.get(schema.__name__)
        if p is None:
            raise ExtractionFailed(3, "không có đáp án giả", "")
        if isinstance(p, Exception):
            raise p
        return schema.model_validate(p)


def _doc(*texts: str) -> DocxDocument:
    els = [Element(index=i, kind="paragraph", text=t, page=3, section="IV.1")
           for i, t in enumerate(texts)]
    return DocxDocument(path="giả.docx", elements=els, page_source="rendered")


def _nhom(*ts: ThamSo) -> NhomTrich:
    return NhomTrich(ma_nhom="TEST", scope="phan_he", tham_so=list(ts))


# ------------------------------------------------- 1.7 kế hoạch (NT3) ------
def test_ke_hoach_suy_tu_rules_yaml_chu_khong_hard_code():
    ts = tham_so_cua_bo_quy_tac()
    assert len(ts) == 237
    assert ts["cpu_95th"].kieu == "so" and ts["cpu_95th"].unit == "%"
    assert ts["cpu_95th"].scope == "phan_he"


def test_unit_gánh_hai_vai_duoc_tach_thanh_kieu_du_lieu():
    """`unit` trong rules.yaml vừa là đơn vị đo vừa là kiểu — không tách thì C3 sẽ
    hỏi model "IOPS của co_duong_ra_public là bao nhiêu", một câu vô nghĩa."""
    ts = tham_so_cua_bo_quy_tac()
    assert ts["co_he_tham_chieu"].kieu == "bool"          # unit: "đúng/sai"
    assert ts["hinh_thuc_cap_phat"].kieu == "enum"
    assert ts["hinh_thuc_cap_phat"].options == ["ao_hoa", "vat_ly", "bare_metal"]
    assert ts["loai_o"].kieu == "enum" and ts["loai_o"].la_khoa_tra_bang


def test_mo_ta_tham_so_lay_tu_ten_quy_tac_chu_khong_tu_nghi():
    ts = tham_so_cua_bo_quy_tac()
    assert "CPU" in ts["cpu_95th"].mo_ta          # tên quy tắc KPI-02
    assert ts["cpu_95th"].rule_ids


def test_nhom_to_bi_cat_nho_de_mot_loi_khong_huy_ca_luot():
    kh = ke_hoach_trich(max_truong=5)
    assert all(len(n.tham_so) <= 5 for n in kh)
    assert any(n.tong_phan > 1 for n in kh)


# ------------------------------------------------- lược đồ động -----------
def test_truong_enum_sinh_rang_buoc_enum_trong_luoc_do():
    """Hồi quy bài học 1.2: khai `str` + liệt kê trong description là KHÔNG đủ."""
    t = ThamSo(name="loai_o", kieu="enum", options=["ssd", "sas_10k"])
    sch = json.dumps(luoc_do_nhom(_nhom(t)).model_json_schema(), ensure_ascii=False)
    assert '"enum"' in sch and "ssd" in sch
    assert "khong_neu" in sch          # phải có đường hợp lệ để nói "không nêu"


def test_luoc_do_chon_dung_lop_theo_kieu():
    n = _nhom(ThamSo(name="a", kieu="so", unit="GB"),
              ThamSo(name="b", kieu="bool"))
    ann = luoc_do_nhom(n).model_fields
    assert ann["a"].annotation is GiaTriSo
    assert ann["b"].annotation is GiaTriBool


# ------------------------------------------------- neo / chống bịa --------
def test_gia_tri_khong_neo_duoc_vao_tai_lieu_thi_BI_LOAI():
    """Cổng chống bịa: số không tìm lại được trong văn bản thì không có căn cứ (NT2)."""
    doc = _doc("Tải CPU trung bình 60%.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%",
        "cau_chua": "Tải CPU đỉnh đạt 92% vào giờ cao điểm."}}})   # câu KHÔNG có thật
    ex = Extractor(llm)
    core = __import__("src.extraction.schema", fromlist=["x"]).SizingCore()
    ex.trich_nhom(doc, _nhom(t), core)
    assert "cpu_95th" not in core.params
    assert ex.tk.khong_neo_duoc == 1


def test_neo_duoc_thi_lay_kem_vi_tri_va_nguyen_van():
    doc = _doc("Tải CPU đỉnh đạt 92% vào giờ cao điểm.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%",
        "cau_chua": "Tải CPU đỉnh đạt 92% vào giờ cao điểm."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    ev = core.params["cpu_95th"]
    assert ev.value == 92 and ev.raw == "92%"
    assert ev.location == "Mục IV.1, trang 3" and ev.element_index == 0


# ------------------------------------------------- số & đơn vị (nối 1.4) --
def test_model_tra_nguyen_van_con_CODE_moi_quyet_dinh_so():
    """"1.500" là 1500 hay 1,5 — quyết định đó thuộc về 1.4, không thuộc về model."""
    doc = _doc("Dung lượng dữ liệu 1.500 GB cho toàn hệ thống.")
    t = ThamSo(name="dung_luong_gb", kieu="so", unit="GB")
    llm = FakeLLM({"TrichTEST1": {"dung_luong_gb": {
        "gia_tri_nguyen_van": "1.500 GB",
        "cau_chua": "Dung lượng dữ liệu 1.500 GB cho toàn hệ thống."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    assert core.params["dung_luong_gb"].value == 1500
    assert core.params["dung_luong_gb"].raw == "1.500 GB"


def test_quy_doi_ve_dung_don_vi_quy_tac_dung():
    """Bỏ bước quy đổi thì "1,5 TB" vào biểu thức tính bằng GB sẽ lệch 1024 lần."""
    doc = _doc("Dung lượng backup 1,5 TB.")
    t = ThamSo(name="dung_luong_backup_gb", kieu="so", unit="GB")
    llm = FakeLLM({"TrichTEST1": {"dung_luong_backup_gb": {
        "gia_tri_nguyen_van": "1,5 TB", "cau_chua": "Dung lượng backup 1,5 TB."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    ev = core.params["dung_luong_backup_gb"]
    assert ev.value == pytest.approx(1536)      # 1,5 × 1024, KHÔNG phải 1500
    assert "quy đổi" in ev.note


def test_don_vi_khac_NHOM_thi_bo_gia_tri_chu_khong_dua_so_sai_cho_C4():
    doc = _doc("Băng thông ra internet 200 Mbps.")
    t = ThamSo(name="dung_luong_gb", kieu="so", unit="GB")
    llm = FakeLLM({"TrichTEST1": {"dung_luong_gb": {
        "gia_tri_nguyen_van": "200 Mbps",
        "cau_chua": "Băng thông ra internet 200 Mbps."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert core.params["dung_luong_gb"].value is None
    assert "khác nhóm" in core.params["dung_luong_gb"].note
    assert ex.tk.khong_quy_doi_duoc == 1


def test_don_vi_dem_khong_co_trong_units_yaml_thi_giu_nguyen_so():
    """`IOPS`, `máy`, `points` cố ý không nằm trong units.yaml — không cần quy đổi."""
    doc = _doc("Tổng số máy 12 máy.")
    t = ThamSo(name="tong_may_khai", kieu="so", unit="máy")
    llm = FakeLLM({"TrichTEST1": {"tong_may_khai": {
        "gia_tri_nguyen_van": "12", "cau_chua": "Tổng số máy 12 máy."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert core.params["tong_may_khai"].value == 12
    assert ex.tk.khong_quy_doi_duoc == 0


# ------------------------------------------------- thiếu / hỏng (NT4) -----
def test_tai_lieu_khong_neu_thi_de_TRONG_chu_khong_doan():
    doc = _doc("Tài liệu không nói gì về CPU.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "", "cau_chua": ""}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    assert "cpu_95th" not in core.params        # C4 sẽ báo "thiếu thông tin"


def test_enum_khong_neu_thi_khong_lay():
    doc = _doc("Không nói gì về hình thức cấp phát.")
    t = ThamSo(name="hinh_thuc_cap_phat", kieu="enum", options=["ao_hoa", "vat_ly"])
    llm = FakeLLM({"TrichTEST1": {"hinh_thuc_cap_phat": {
        "gia_tri": "khong_neu", "cau_chua": ""}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    assert "hinh_thuc_cap_phat" not in core.params


def test_goi_model_hong_thi_KHONG_bia_gia_tri_va_co_ghi_lai_loi():
    doc = _doc("bất kỳ")
    llm = FakeLLM({})                    # không có đáp án -> ExtractionFailed
    from src.extraction.schema import SizingCore
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(ThamSo(name="cpu_95th", kieu="so", unit="%")), core)
    assert core.params == {}
    assert ex.tk.luot_goi_hong == 1 and ex.tk.loi


# ------------------------------------------------- loai_sizing (bài học 1.2)
def test_loai_sizing_chi_nhan_khi_cau_dan_CO_THAT_trong_tai_lieu():
    """Đo ở 1.2: nêu rõ thì 6/6 đúng, phải suy ra thì 3/6 và ba model phân kỳ."""
    doc = _doc("Hệ thống MyKid 2.0 phục vụ 3.500 người dùng đồng thời.")
    llm = FakeLLM({"ThongTinChung": {
        "ten_he_thong": "MyKid 2.0", "ma_pyc": "", "muc_dich_sizing": "nâng cấp",
        "cau_chua_muc_dich": "Tài liệu định cỡ nâng cấp hệ thống.",   # KHÔNG có thật
        "loai_sizing": "nang_cap", "muc_do_quan_trong": "khong_neu",
        "dau_moi_yeu_cau": "", "don_vi_phat_trien": "", "don_vi_dinh_co": "",
        "thoi_gian_cam_ket": ""}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_cap_tai_lieu(doc, core)
    assert core.ten_he_thong == "MyKid 2.0"
    assert core.loai_sizing is None            # suy đoán -> không nhận
    assert ex.tk.khong_neo_duoc == 1


def test_loai_sizing_duoc_nhan_khi_tai_lieu_neu_ro():
    doc = _doc("Tài liệu định cỡ bổ sung tài nguyên cho hệ thống CSKH đang vận hành.")
    llm = FakeLLM({"ThongTinChung": {
        "ten_he_thong": "CSKH", "ma_pyc": "PYC-1", "muc_dich_sizing": "bổ sung tài nguyên",
        "cau_chua_muc_dich":
            "Tài liệu định cỡ bổ sung tài nguyên cho hệ thống CSKH đang vận hành.",
        "loai_sizing": "bo_sung", "muc_do_quan_trong": "quan_trong",
        "dau_moi_yeu_cau": "", "don_vi_phat_trien": "", "don_vi_dinh_co": "",
        "thoi_gian_cam_ket": ""}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    Extractor(llm).trich_cap_tai_lieu(doc, core)
    assert core.loai_sizing == "bo_sung"
    assert core.muc_do_quan_trong == "quan_trong"


# ------------------------------------------------- nối C3 -> C4 -----------
def test_C3_noi_duoc_vao_C4_va_moi_finding_deu_co_can_cu():
    from src.extraction.schema import SizingCore, SizingExtension
    from src.validators.quantitative import QuantitativeValidator

    doc = _doc("Tải CPU đỉnh của phân hệ App đạt 92%.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%",
        "cau_chua": "Tải CPU đỉnh của phân hệ App đạt 92%."}}})
    core = SizingCore(phan_he=[SizingExtension(ten_phan_he="App")])
    Extractor(llm).trich_nhom(doc, _nhom(t), core.phan_he[0], ten_phan_he="App")

    v = QuantitativeValidator()
    out = [o for o in v.run(core) if o.rule_id == "KPI-02" and o.scope_key == "App"]
    assert out and out[0].status == "vi_pham"
    assert "92" in out[0].finding.computed_evidence
    assert out[0].finding.location == "Mục IV.1, trang 3"      # neo về tài liệu thật
    assert all(f.co_can_cu() for f in v.findings(core))


def test_model_chep_ca_tien_to_vi_tri_thi_van_neo_duoc():
    """Ngữ cảnh gửi đi có tiền tố '[Mục …, trang …]'; model hay chép cả nó vào câu.
    Không cắt tiền tố thì tự mình làm hỏng cổng neo của chính mình."""
    doc = _doc("Tải CPU đỉnh đạt 92%.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%",
        "cau_chua": "[Mục IV.1, trang 3] Tải CPU đỉnh đạt 92%."}}})
    from src.extraction.schema import SizingCore
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert core.params["cpu_95th"].value == 92
    assert ex.tk.khong_neo_duoc == 0
