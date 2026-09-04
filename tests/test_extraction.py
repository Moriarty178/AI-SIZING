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


def test_chay_song_song_cho_KET_QUA_GIONG_HET_chay_tuan_tu():
    """Chạy tuần tự một bản 13 phân hệ mất hàng giờ (đo thật ~40s/lượt), nên phải
    song song — nhưng chỉ khi kết quả không đổi và bộ đếm không hụt."""
    from src.extraction.schema import SizingCore, SizingExtension

    doc = _doc("Tải CPU đỉnh phân hệ App đạt 92%.", "Tải CPU đỉnh phân hệ DB đạt 50%.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    dap_an = {"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%", "cau_chua": "Tải CPU đỉnh phân hệ App đạt 92%."}}}

    def chay(song_song):
        core = SizingCore(phan_he=[SizingExtension(ten_phan_he=f"PH{i}")
                                   for i in range(6)])
        ex = Extractor(FakeLLM(dict(dap_an)), song_song=song_song)
        for ph in core.phan_he:
            pass
        for ph in core.phan_he:
            ex.trich_nhom(doc, _nhom(t), ph, ten_phan_he=ph.ten_phan_he)
        return core, ex.tk

    a_core, a_tk = chay(1)
    b_core, b_tk = chay(4)
    assert [ph.params["cpu_95th"].value for ph in a_core.phan_he] == [92] * 6
    assert a_tk.luot_goi == b_tk.luot_goi == 6
    assert a_tk.truong_co_gia_tri == b_tk.truong_co_gia_tri == 6


def test_ngu_canh_cat_theo_muc_cua_phan_he():
    """Hỏi về phân hệ Database mà đưa cả 13 phân hệ vào ngữ cảnh là mời model lấy
    nhầm số của phân hệ khác."""
    from src.ingestion.docx_reader import DocxDocument, Element
    els = [Element(index=0, kind="paragraph", text="A" * 500, page=1, section="III.1"),
           Element(index=1, kind="paragraph", text="B" * 500, page=2, section="III.2")]
    doc = DocxDocument(path="g.docx", elements=els, page_source="rendered")
    ex = Extractor(FakeLLM({}))
    assert "A" * 100 in ex.ngu_canh(doc, "III.1")
    assert "B" * 100 not in ex.ngu_canh(doc, "III.1")


def test_muc_qua_hep_thi_LUI_VE_toan_tai_lieu_chu_khong_trich_thieu():
    from src.ingestion.docx_reader import DocxDocument, Element
    from src.extraction.schema import SizingCore
    els = [Element(index=0, kind="paragraph", text="Tải CPU đỉnh đạt 92%.",
                   page=1, section="III.1"),
           Element(index=1, kind="paragraph", text="C" * 900, page=2, section="III.2")]
    doc = DocxDocument(path="g.docx", elements=els, page_source="rendered")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "92%", "cau_chua": "Tải CPU đỉnh đạt 92%."}}})
    core = SizingCore()
    # mục III.1 chỉ ~50 ký tự, dưới ngưỡng -> phải lùi về toàn văn, vẫn trích được
    Extractor(llm).trich_nhom(doc, _nhom(t), core, section="III.1")
    assert core.params["cpu_95th"].value == 92


# ===================== hồi quy từ lần chạy THẬT 2026-09-04 ==================
# Ba ca dưới đều lấy nguyên văn từ docs/smoke/c3-20260904-1621.json — C3 đã nhận
# những giá trị này và đưa thẳng cho C4.

def test_model_tra_ca_MOT_CAU_thay_vi_gia_tri_thi_BI_LOAI():
    """Ca thật: raw = "Tài nguyên CPU/RAM của 1 node database … | 48 | 500 |" →
    parse_number bắt "1" từ "1 node" và C4 nhận `spec2006 = 1.0` hoàn toàn bịa."""
    from src.extraction.schema import SizingCore
    cau = ("Tài nguyên CPU/RAM của 1 node database BCCS 3.0 tại thị trường có "
           "4 triệu thuê bao. Cần tối thiểu 3 node để đảm bảo HA. | 48 | 500 | ")
    doc = _doc(cau)
    t = ThamSo(name="spec2006", kieu="so", unit="points")
    llm = FakeLLM({"TrichTEST1": {"spec2006": {
        "gia_tri_nguyen_van": cau, "cau_chua": cau}}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert "spec2006" not in core.params
    assert ex.tk.khong_phai_gia_tri == 1


def test_gia_tri_KHONG_CO_trong_cau_da_neo_thi_BI_LOAI():
    """Ca thật: phân hệ Firewall nhận `kich_thuoc_ban_ghi_byte = 500`, neo vào bảng
    của phân hệ Database. Câu có thật, con số có thật — nhưng thuộc về chỗ khác."""
    from src.extraction.schema import SizingCore
    doc = _doc("Cấu hình firewall theo thiết kế chuẩn của đơn vị.")
    t = ThamSo(name="kich_thuoc_ban_ghi_byte", kieu="so", unit="byte")
    llm = FakeLLM({"TrichTEST1": {"kich_thuoc_ban_ghi_byte": {
        "gia_tri_nguyen_van": "500",
        "cau_chua": "Cấu hình firewall theo thiết kế chuẩn của đơn vị."}}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert "kich_thuoc_ban_ghi_byte" not in core.params
    assert ex.tk.gia_tri_khong_co_trong_cau == 1


def test_gia_tri_ngoai_khoang_hop_le_cua_don_vi_thi_KHONG_dua_cho_C4():
    """Ca thật: `datanode_95th = 500` với đơn vị `%`. Con số 500 CÓ THẬT trong tài
    liệu nên cổng neo không chặn được — nó chỉ thuộc về trường khác."""
    from src.extraction.schema import SizingCore
    doc = _doc("Dung lượng RAM 500 GB cho mỗi node.")
    t = ThamSo(name="datanode_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"datanode_95th": {
        "gia_tri_nguyen_van": "500", "cau_chua": "Dung lượng RAM 500 GB cho mỗi node."}}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert core.params["datanode_95th"].value is None
    assert "ngoài khoảng hợp lệ" in core.params["datanode_95th"].note
    assert ex.tk.ngoai_khoang_hop_le == 1


def test_phan_tram_trong_khoang_van_duoc_nhan():
    from src.extraction.schema import SizingCore
    doc = _doc("Tải CPU đỉnh đạt 48%.")
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": {
        "gia_tri_nguyen_van": "48", "cau_chua": "Tải CPU đỉnh đạt 48%."}}})
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    assert core.params["cpu_95th"].value == 48


def test_model_tu_nghi_ra_kho_neu_cho_truong_so_thi_coi_la_THIEU():
    """Ca thật: model trả chuỗi `kho_neu` (gõ sai của `khong_neu`) cho 8 trường số,
    dù lược đồ `GiaTriSo` chỉ cho phép chuỗi rỗng."""
    from src.extraction.schema import SizingCore
    doc = _doc("Cụm Kafka gồm 3 broker.")
    t = ThamSo(name="so_cpu_vat_ly", kieu="so", unit="CPU")
    llm = FakeLLM({"TrichTEST1": {"so_cpu_vat_ly": {
        "gia_tri_nguyen_van": "kho_neu", "cau_chua": "Cụm Kafka gồm 3 broker."}}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(doc, _nhom(t), core)
    assert "so_cpu_vat_ly" not in core.params
    assert ex.tk.khong_doc_duoc_so == 0        # không phải lỗi đọc số, là "không nêu"


# ===================== hướng A: hỏi theo BẢNG ==============================
def _doc_bang():
    """Bảng thật của phân hệ Database trong BCCS3."""
    from src.ingestion.docx_reader import DocxDocument, Element
    rows = [["STT", "Nội dung", "CPU (Cint)", "RAM (GB)", "Ghi chú"],
            ["1", "Tài nguyên CPU/RAM của 1 node database BCCS 3.0", "48", "500", ""]]
    return DocxDocument(path="g.docx", page_source="rendered", elements=[
        Element(index=29, kind="table", text=" | ".join(rows[0]) + "\n" + " | ".join(rows[1]),
                rows=rows, page=4, section="III")])


def _ev(gia_tri, cot="", cau=""):
    return {"gia_tri_nguyen_van": gia_tri, "cau_chua": cau, "tieu_de_cot": cot}


def test_bang_duoc_ve_lai_thanh_LUOI_giu_hang_tieu_de():
    """C1 giữ `rows` cho 21/21 bảng của BCCS3 nhưng C3 từng chỉ gửi bản làm phẳng —
    tức vứt đúng thứ cho biết con số nào là gì."""
    nc = Extractor(FakeLLM({})).ngu_canh(_doc_bang())
    assert "BẢNG #29" in nc
    assert "| STT | Nội dung | CPU (Cint) | RAM (GB) | Ghi chú |" in nc


def test_lay_dung_o_bang_thi_ghi_ro_COT_NGUON_trong_note():
    """Model chỉ NÓI con số ở cột nào; code tự đọc ô. Cột nguồn hiện trong báo cáo để
    người đọc tự thấy khi con số đúng thật nhưng trả lời nhầm câu hỏi."""
    from src.extraction.schema import SizingCore
    t = ThamSo(name="cint_rated_1_cpu", kieu="so", unit="points")
    llm = FakeLLM({"TrichTEST1": {"cint_rated_1_cpu": _ev("48", cot="CPU (Cint)")}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(_doc_bang(), _nhom(t), core)
    ev = core.params["cint_rated_1_cpu"]
    assert ev.value == 48 and ev.element_index == 29
    assert "CPU (Cint)" in ev.note
    assert ex.tk.lay_tu_bang == 1


def test_khai_cot_KHONG_CO_THAT_thi_bi_loai():
    from src.extraction.schema import SizingCore
    t = ThamSo(name="cpu_95th", kieu="so", unit="%")
    llm = FakeLLM({"TrichTEST1": {"cpu_95th": _ev("48", cot="Tải CPU 95th (%)")}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(_doc_bang(), _nhom(t), core)
    assert "cpu_95th" not in core.params
    assert ex.tk.cot_khong_co_that == 1


def test_gia_tri_khong_nam_trong_COT_da_khai_thi_bi_loai():
    """Ca thật: `500` là RAM (GB) nhưng bị gán cho một tham số rồi khai cột CPU."""
    from src.extraction.schema import SizingCore
    t = ThamSo(name="cint_rated_1_cpu", kieu="so", unit="points")
    llm = FakeLLM({"TrichTEST1": {"cint_rated_1_cpu": _ev("500", cot="CPU (Cint)")}})
    core = SizingCore()
    ex = Extractor(llm)
    ex.trich_nhom(_doc_bang(), _nhom(t), core)
    assert "cint_rated_1_cpu" not in core.params
    assert ex.tk.gia_tri_khong_trong_cot == 1


def test_khoang_phan_he_chan_lay_so_cua_phan_he_khac():
    """Ca thật: `Firewall` lấy `kich_thuoc_ban_ghi_byte = 500` từ bảng của `Database`.
    Cắt theo `section` không cứu được vì cả 13 phân hệ đều ở mục III."""
    from src.extraction.schema import SizingCore, SizingExtension
    doc = _doc_bang()
    core = SizingCore(phan_he=[
        SizingExtension(ten_phan_he="Database", muc="III", element_index=20),
        SizingExtension(ten_phan_he="Firewall", muc="III", element_index=100)])
    ex = Extractor(FakeLLM({}))
    assert ex.khoang_phan_he(core, core.phan_he[0], 200) == (20, 100)
    assert ex.khoang_phan_he(core, core.phan_he[1], 200) == (100, 200)
    # bảng #29 thuộc Database, nằm NGOÀI khoảng của Firewall
    el, vi_sao = ex.o_trong_cot(doc, "RAM (GB)", "500", khoang=(100, 200))
    assert el is None and "không bảng nào" in vi_sao
    el2, _ = ex.o_trong_cot(doc, "RAM (GB)", "500", khoang=(20, 100))
    assert el2 is not None


def test_cong_nghe_luu_tru_la_ENUM_lay_tu_rules_yaml():
    """Khai `str` đã hỏng hai lần trên tài liệu thật: lần đầu model chép nguyên
    `cong_nghe` sang, lần sau điền cả tiêu đề mục "Mục III - Định cỡ cụm máy chủ…".
    Cả hai lần đều khác rỗng nên MỌI phân hệ chạy thêm một vòng scope vô nghĩa."""
    import json
    from src.extraction.extractor import PhanHeNhanDien
    from src.extraction.plan import tham_so_cua_bo_quy_tac
    sch = PhanHeNhanDien.model_json_schema()["properties"]["cong_nghe_luu_tru"]
    assert set(sch["enum"]) == set(tham_so_cua_bo_quy_tac()["loai_o"].options) | {"khong_neu"}
    assert "Mục III" not in json.dumps(sch, ensure_ascii=False)


def test_khong_neu_cho_cong_nghe_luu_tru_thi_KHONG_chay_them_scope():
    from src.extraction.extractor import DanhSachPhanHe
    doc = _doc("Phân hệ Database dùng MariaDB.")
    llm = FakeLLM({"DanhSachPhanHe": {"phan_he": [{
        "ten_phan_he": "Database", "cong_nghe": "MariaDB",
        "cong_nghe_luu_tru": "khong_neu", "muc": "III"}]}})
    ph = Extractor(llm).nhan_dien_phan_he(doc)
    assert ph[0].cong_nghe_luu_tru is None
    from src.extraction.schema import SizingCore
    assert SizingCore(phan_he=ph).scope_keys("phan_he_x_cong_nghe_luu_tru") == []


# ============ v5: một ô một tham số + neo phân hệ theo số hiệu bảng =========
def test_mot_O_bi_NHIEU_tham_so_cung_nhan_thi_BO_HET():
    """Ca thật 2026-09-04 18:51: ô `#93 = 16` của DBIN/FTP được **9 tham số** cùng
    nhận làm nguồn. Khi 9 tham số cùng trỏ một ô thì không có căn cứ chọn cái đúng —
    giữ lại cái nào cũng là đoán."""
    from src.extraction.schema import ExtractedValue, SizingExtension
    ph = SizingExtension(ten_phan_he="DBIN và FTP")
    for ten in ("cint_rated_1_cpu", "core_danh_cho_hdh", "cpu_95th", "datanode_95th"):
        ph.params[ten] = ExtractedValue(value=16, raw="16", element_index=93,
                                        location="Mục III")
    ph.params["rieng"] = ExtractedValue(value=60, raw="60", element_index=95,
                                        location="Mục III")
    ex = Extractor(FakeLLM({}))
    assert ex.loc_o_bi_nhieu_tham_so(ph) == 4
    assert all(ph.params[t].value is None for t in
               ("cint_rated_1_cpu", "core_danh_cho_hdh", "cpu_95th", "datanode_95th"))
    assert "còn được 3 tham số khác nhận" in ph.params["cpu_95th"].note
    assert ph.params["rieng"].value == 60          # ô chỉ một tham số nhận thì giữ


def test_hai_tham_so_lay_tu_HAI_O_khac_nhau_thi_deu_giu():
    from src.extraction.schema import ExtractedValue, SizingExtension
    ph = SizingExtension(ten_phan_he="Maxscale")
    ph.params["a"] = ExtractedValue(value=10, raw="10", element_index=37)
    ph.params["b"] = ExtractedValue(value=60, raw="60", element_index=37)
    assert Extractor(FakeLLM({})).loc_o_bi_nhieu_tham_so(ph) == 0
    assert ph.params["a"].value == 10 and ph.params["b"].value == 60


def test_neo_phan_he_theo_SO_HIEU_BANG_khi_ten_khong_khop_tai_lieu():
    """Lượt 18:51 mất neo 3/10 phân hệ vì model trả tên mô tả dài không có nguyên văn
    trong tài liệu — mất neo là mất luôn giới hạn khoảng."""
    doc = _doc_bang()
    llm = FakeLLM({"DanhSachPhanHe": {"phan_he": [{
        "ten_phan_he": "Các module vệ tinh, monitor (Birt report, VSA, MariaDB)",
        "cong_nghe": "", "cong_nghe_luu_tru": "khong_neu", "muc": "",
        "bang_cau_hinh": 29}]}})
    ph = Extractor(llm).nhan_dien_phan_he(doc)
    assert len(ph) == 1
    assert ph[0].element_index == 29        # neo được nhờ số hiệu bảng
    assert ph[0].muc == "III"


def test_so_hieu_bang_khong_co_that_thi_lui_ve_neo_theo_ten():
    doc = _doc_bang()
    llm = FakeLLM({"DanhSachPhanHe": {"phan_he": [{
        "ten_phan_he": "node database", "cong_nghe": "", "muc": "",
        "cong_nghe_luu_tru": "khong_neu", "bang_cau_hinh": 999}]}})
    ph = Extractor(llm).nhan_dien_phan_he(doc)
    assert ph[0].element_index == 29        # tìm thấy qua tên trong ô bảng


def test_enum_khong_duoc_neo_ra_NGOAI_phan_he_dang_hoi():
    """Hồi quy lượt chạy 19:07: 6/32 giá trị neo ra ngoài phân hệ đang hỏi.

    GoldenGate (phần tử #69–83) nhận `chuan_spec` neo vào phần tử #28 của phân hệ
    Database. `khoang_phan_he` sinh ra để chặn đúng việc đó, nhưng đường neo lại tìm
    trên toàn tài liệu nên bỏ qua nó.
    """
    from src.extraction.schema import SizingCore, SizingExtension
    els = [Element(index=0, kind="paragraph", text="Database dùng chuẩn SPEC 2006.",
                   page=1, section="III"),
           Element(index=9, kind="paragraph", text="GoldenGate: tài nguyên như trên.",
                   page=2, section="III")]
    doc = DocxDocument(path="g.docx", elements=els, page_source="rendered")
    t = ThamSo(name="chuan_spec", kieu="enum", options=["2006", "2017"])
    llm = FakeLLM({"TrichTEST1": {"chuan_spec": {
        "gia_tri": "2006", "cau_chua": "Database dùng chuẩn SPEC 2006."}}})
    ph = SizingExtension(ten_phan_he="GoldenGate", element_index=9)
    Extractor(llm).trich_nhom(doc, _nhom(t), ph, ten_phan_he="GoldenGate",
                              khoang=(9, 20))
    assert "chuan_spec" not in ph.params        # câu đó thuộc phân hệ KHÁC

    # cùng dữ liệu, không giới hạn khoảng -> vẫn nhận (đường cấp tài liệu)
    core = SizingCore()
    Extractor(llm).trich_nhom(doc, _nhom(t), core)
    assert core.params["chuan_spec"].value == "2006"
