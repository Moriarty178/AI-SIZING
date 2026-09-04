"""Test 1.12 — C5. Chạy OFFLINE bằng transport giả, dùng bộ quy tắc THẬT.

Trọng tâm là chỗ căn cứ **bất đối xứng**: phía quy tắc luôn có (từ `rules.yaml`), phía
tài liệu thì "không đạt" thường là do THIẾU nên không trích dẫn được. Đòi trích dẫn cho
ca thiếu sẽ làm C5 bỏ sót đúng loại lỗi mà Vòng 1 sinh ra để bắt.
"""
import pytest

from src.extraction.schema import ExtractedValue, SizingCore, SizingExtension
from src.ingestion.docx_reader import DocxDocument, Element
from src.llm.client import ExtractionFailed, LLMClient
from src.validators.qualitative import NhanXetDinhTinh, QualitativeValidator
from src.validators.rules_loader import load_rules


@pytest.fixture(scope="module")
def rules():
    return load_rules()


class FakeLLM(LLMClient):
    def __init__(self, nx):
        self.nx = nx
        self.goi = 0
        self.chat_model, self.temperature, self.cfg = "fake", 0.0, {}

    def extract(self, schema, messages, *, model=None, max_retries=3, max_tokens=4000):
        self.goi += 1
        self.loi_nhac = messages[-1]["content"]
        if isinstance(self.nx, Exception):
            raise self.nx
        return schema.model_validate(self.nx)


def _doc(*texts: str) -> DocxDocument:
    return DocxDocument(path="giả.docx", page_source="rendered", elements=[
        Element(index=i, kind="paragraph", text=t, page=5, section="II.1")
        for i, t in enumerate(texts)])


def _nx(ket_luan, trich="", ly_do="lý do"):
    return {"ket_luan": ket_luan, "trich_dan_tai_lieu": trich, "ly_do": ly_do}


# ------------------------------------------------- căn cứ phía quy tắc ----
def test_rule_quote_lay_tu_rules_yaml_KHONG_phai_tu_model(rules):
    """Model không được tự nghĩ ra tiêu chí — căn cứ phía quy tắc là dữ liệu."""
    doc = _doc("Tài liệu không có mô tả tổng quan.")
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="Thiếu mô tả tổng quan.")),
                             rules=rules)
    out = v.check_rule(rules["EVD-12"], doc, SizingCore())
    f = out.finding
    assert out.status == "vi_pham"
    assert f.rule_ref == "EVD-12"
    assert f.rule_quote and f.rule_quote in rules["EVD-12"].criteria
    assert f.source_doc == rules["EVD-12"].source_doc
    assert f.co_can_cu()


def test_vong_1_truot_sinh_dung_nhom_thieu_muc_cho_C7_chan(rules):
    """C7 chặn finding Vòng 2 dựa trên nhóm `thieu_muc`/`thieu_thong_tin` ở Vòng 1."""
    doc = _doc("Không có bảng tổng hợp cấu hình.")
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="Thiếu bảng tổng hợp.")),
                             rules=rules)
    f = v.check_rule(rules["EVD-16"], doc, SizingCore()).finding
    assert rules["EVD-16"].round == 1
    assert f.category == "thieu_muc" and f.vong == 1
    assert f.checklist_ref == ["CL-2.9"]


def test_vong_2_truot_thi_KHONG_dung_nhom_thieu_muc(rules):
    doc = _doc("Có nêu cơ sở định cỡ nhưng sơ sài.")
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="Chưa đủ 5 phương diện.")),
                             rules=rules)
    r = rules["EVD-01"] if rules["EVD-01"].round == 2 else next(
        x for x in rules.select(type="qualitative", round=2) if not x.applies_when)
    f = v.check_rule(r, doc, SizingCore()).finding
    assert f.category == "thieu_thong_tin" and f.vong == 2


# ------------------------------------------------- căn cứ phía tài liệu ---
def test_khong_dat_KHONG_bi_doi_trich_dan_vi_cai_thieu_thi_khong_trich_duoc(rules):
    """Đòi trích dẫn cho ca thiếu sẽ làm C5 bỏ sót đúng loại lỗi Vòng 1 phải bắt."""
    doc = _doc("Tài liệu chỉ có phần mở đầu.")
    v = QualitativeValidator(
        FakeLLM(_nx("khong_dat", trich="", ly_do="Không có mô hình logic tổng quan.")),
        rules=rules)
    out = v.check_rule(rules["EVD-13"], doc, SizingCore())
    assert out.status == "vi_pham"                 # vẫn kết luận được
    assert out.finding.confidence == "vua"         # nhưng độ tin thấp hơn ca có neo


def test_trich_dan_KHONG_neo_duoc_thi_HUY_ket_luan_khong_dat(rules):
    """Model dẫn đoạn không có trong tài liệu ⇒ đang bịa ⇒ không tin kết luận."""
    doc = _doc("Tài liệu chỉ có phần mở đầu.")
    v = QualitativeValidator(
        FakeLLM(_nx("khong_dat", trich="Mục 3.2 ghi rõ mô hình logic gồm 5 khối.",
                    ly_do="Mô hình logic thiếu thành phần.")), rules=rules)
    out = v.check_rule(rules["EVD-13"], doc, SizingCore())
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "khong_kiem_chung_duoc"
    assert out.finding.confidence == "thap"
    assert v.tk.trich_dan_bia == 1


def test_trich_dan_neo_duoc_thi_finding_mang_dung_vi_tri(rules):
    doc = _doc("Mô hình logic tổng quan chỉ vẽ 2 khối, thiếu khối xử lý.")
    v = QualitativeValidator(
        FakeLLM(_nx("khong_dat", trich="Mô hình logic tổng quan chỉ vẽ 2 khối",
                    ly_do="Mô hình logic thiếu thành phần.")), rules=rules)
    f = v.check_rule(rules["EVD-13"], doc, SizingCore()).finding
    assert f.location == "Mục II.1, trang 5" and f.confidence == "cao"


def test_dat_thi_khong_sinh_finding(rules):
    doc = _doc("Hệ thống gồm 3 phân hệ: App, DB, Redis. Mô tả tổng quan đầy đủ.")
    v = QualitativeValidator(FakeLLM(_nx("dat", trich="Hệ thống gồm 3 phân hệ")),
                             rules=rules)
    out = v.check_rule(rules["EVD-12"], doc, SizingCore())
    assert out.status == "dat" and out.finding is None


# ------------------------------------------------- applies_when (code) ----
def test_applies_when_do_CODE_quyet_dinh_chu_khong_hoi_model(rules):
    """MTH-01 chỉ áp dụng cho Dạng I có hệ tham chiếu."""
    doc = _doc("bất kỳ")
    core = SizingCore()
    core.set_param("dang_dinh_co", 2)
    core.set_param("co_he_tham_chieu", False)
    llm = FakeLLM(_nx("khong_dat"))
    out = QualitativeValidator(llm, rules=rules).check_rule(rules["MTH-01"], doc, core)
    assert out.status == "khong_ap_dung"
    assert llm.goi == 0                    # không tốn lời gọi nào


def test_thieu_dau_vao_cua_applies_when_thi_KHONG_doan_la_co_ap_dung(rules):
    doc = _doc("bất kỳ")
    llm = FakeLLM(_nx("khong_dat"))
    out = QualitativeValidator(llm, rules=rules).check_rule(
        rules["MTH-01"], doc, SizingCore())
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "thieu_thong_tin"
    assert "dang_dinh_co" in out.finding.finding
    assert llm.goi == 0


def test_applies_when_dung_thi_van_cham(rules):
    doc = _doc("Hệ tham chiếu là hệ thống ABC.")
    core = SizingCore()
    core.set_param("dang_dinh_co", 1)
    core.set_param("co_he_tham_chieu", True)
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="Thiếu 3/5 phương diện.")),
                             rules=rules)
    assert v.check_rule(rules["MTH-01"], doc, core).status == "vi_pham"


# ------------------------------------------------- few-shot từ dữ liệu ----
def test_vi_du_pass_fail_lay_tu_rules_yaml_dua_vao_loi_nhac(rules):
    """30 quy tắc có `examples` — dùng làm few-shot, không tự viết ví dụ trong code."""
    doc = _doc("bất kỳ")
    core = SizingCore()
    core.set_param("dang_dinh_co", 1)
    core.set_param("co_he_tham_chieu", True)
    llm = FakeLLM(_nx("dat"))
    QualitativeValidator(llm, rules=rules).check_rule(rules["MTH-01"], doc, core)
    assert "Ví dụ ĐẠT:" in llm.loi_nhac
    assert rules["MTH-01"].criteria[:60] in llm.loi_nhac


# ------------------------------------------------- NT4 ---------------------
def test_goi_model_hong_thi_bao_khong_kiem_chung_duoc_chu_khong_im_lang(rules):
    doc = _doc("bất kỳ")
    v = QualitativeValidator(FakeLLM(ExtractionFailed(3, "hỏng", "")), rules=rules)
    out = v.check_rule(rules["EVD-12"], doc, SizingCore())
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.category == "khong_kiem_chung_duoc"
    assert out.finding.co_can_cu() and v.tk.loi


def test_model_noi_khong_xac_dinh_thi_KHONG_bien_thanh_khong_dat(rules):
    doc = _doc("bất kỳ")
    v = QualitativeValidator(FakeLLM(_nx("khong_xac_dinh", ly_do="Nội dung nằm trong ảnh.")),
                             rules=rules)
    out = v.check_rule(rules["EVD-12"], doc, SizingCore())
    assert out.status == "khong_danh_gia_duoc"
    assert out.finding.severity == "info"      # không dọa người dùng bằng mức cao


# ------------------------------------------------- run / phạm vi ----------
def test_run_chi_vong_1_de_lay_dung_thu_C7_can(rules):
    doc = _doc("bất kỳ")
    v = QualitativeValidator(FakeLLM(_nx("dat")), rules=rules)
    outs = v.run(doc, SizingCore(), chi_vong=1)
    assert outs and all(rules[o.rule_id].round == 1 for o in outs)


def test_cham_moi_phan_he_cho_quy_tac_scope_phan_he(rules):
    doc = _doc("bất kỳ")
    core = SizingCore(phan_he=[SizingExtension(ten_phan_he="App"),
                               SizingExtension(ten_phan_he="DB")])
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="thiếu")), rules=rules)
    outs = [o for o in v.run(doc, core, chi_vong=1) if o.rule_id == "EVD-17"]
    assert {o.scope_key for o in outs} == {"App", "DB"}


def test_moi_finding_deu_co_can_cu(rules):
    doc = _doc("bất kỳ")
    v = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="thiếu")), rules=rules)
    fs = v.findings(doc, SizingCore(), chi_vong=1)
    assert fs and all(f.co_can_cu() for f in fs)


# ------------------------------------------------- C5 -> C7 (mạch thật) ---
def test_C5_cap_nguon_finding_vong1_va_C7_CHAN_dung_finding_vong2(rules):
    """Đây là lý do 1.12 đáng làm trước 1.11: C7 (1.10) viết xong luật chặn từ
    2026-09-04 nhưng tới giờ chưa có gì nuôi nó ngoài dữ liệu demo."""
    from src.reporting.report import load_labels, xu_ly
    from src.validators.quantitative import QuantitativeValidator

    doc = _doc("Tài liệu chưa có bảng tổng hợp đề xuất cấu hình toàn hệ thống.")
    core = SizingCore()
    # Có số liệu để C4 chấm được EVD-10 (tổng toàn hệ so với tổng các phân hệ)
    core.params["tong_toan_he_khai"] = ExtractedValue(value=100, location="Mục V, trang 9")
    core.params["tong_cac_phan_he"] = ExtractedValue(value=180, location="Mục V, trang 9")

    # C5: EVD-16 (Vòng 1, CL-2.9) TRƯỢT -> tài liệu chưa có bảng tổng hợp
    v5 = QualitativeValidator(FakeLLM(_nx("khong_dat", ly_do="Chưa có bảng tổng hợp.")),
                              rules=rules)
    f_vong1 = [v5.check_rule(rules["EVD-16"], doc, core).finding]
    assert f_vong1[0].category == "thieu_muc" and f_vong1[0].checklist_ref == ["CL-2.9"]

    # C4: mọi finding Vòng 2 (trong đó EVD-10 cũng gắn CL-2.9)
    f_vong2 = QuantitativeValidator(rules).findings(core)
    assert any("CL-2.9" in f.checklist_ref for f in f_vong2)

    rep = xu_ly(f_vong1 + f_vong2, load_labels())
    bi_chan = {f.rule_ref for f in rep.vong2_tam_hoan}
    assert "EVD-10" in bi_chan, "finding Vòng 2 của mục đã trượt Vòng 1 phải bị chặn"
