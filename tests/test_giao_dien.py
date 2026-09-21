"""Test 1.14 — logic giao diện. Chạy offline, KHÔNG cần cài Streamlit.

Điều quan trọng nhất phải giữ: giao diện **dùng được khi không có model**. Model tự
dựng chỉ với tới được từ máy trong mạng nội bộ, nên một giao diện nổ traceback lúc
thiếu cấu hình là một giao diện vô dụng ở đúng nơi phần lớn công việc diễn ra.
"""
import pathlib

import pytest

from src.giao_dien import (CAN_MODEL, CHE_DO, TrangThaiModel, chay_checklist,
                           che_do_kha_dung, kiem_model,
                           kiem_model_qua_dich_vu, luu_tam,
                           ten_file_ket_qua, tom_tat_tai_lieu, uoc_luong)
from src.ingestion.docx_reader import DocxDocument, Element


def _doc(*els: Element) -> DocxDocument:
    return DocxDocument(path="giả.docx", elements=list(els), page_source="rendered")


def _bang(i: int, rows: list[list[str]]) -> Element:
    return Element(index=i, kind="table", section="III", page=1, rows=rows,
                   text=" ".join(c for r in rows for c in r))


# ------------------------------------------------------- không có model ----
def test_thieu_cau_hinh_thi_BAO_chu_khong_no(tmp_path):
    """`kiem_model` không được ném lỗi — giao diện phải hiện được trong mọi ca."""
    tt = kiem_model(settings_path=str(tmp_path / "khong-co.yaml"))
    assert tt.san_sang is False
    assert "Chưa có cấu hình model" in tt.thong_diep
    assert tt.nhan.startswith("⚠️")


def test_thieu_bien_moi_truong_cung_BAO_chu_khong_no(tmp_path, monkeypatch):
    p = tmp_path / "settings.yaml"
    p.write_text("llm:\n  base_url: http://x\n  chat_model: m\n", encoding="utf-8")
    monkeypatch.delenv("SIZING_COPILOT_API_KEY", raising=False)
    tt = kiem_model(settings_path=str(p))
    assert tt.san_sang is False and "SIZING_COPILOT_API_KEY" in tt.thong_diep


def test_khong_co_model_thi_van_con_cac_che_do_khong_can_model():
    kd = che_do_kha_dung(TrangThaiModel(False, "chưa cấu hình"))
    assert set(kd) == set(CHE_DO) - CAN_MODEL
    assert "checklist" in kd and "doc" in kd     # hai việc làm được ở laptop


def test_co_model_thi_du_ca_ba_che_do():
    assert set(che_do_kha_dung(TrangThaiModel(True, "ok"))) == set(CHE_DO)


# ------------------------------------------------------------ ước lượng ---
def test_uoc_luong_tinh_TRUOC_khi_goi_model():
    """Bấm chạy rồi ngồi chờ mù đã đốt vài lượt chạy ngày 2026-09-04."""
    doc = _doc(_bang(1, [["STT", "CPU (Cint)", "RAM (GB)"], ["1", "48", "500"]]))
    ul = uoc_luong(doc, so_phan_he=5)
    assert ul.so_bang == 1 and ul.tong == ul.c3 + ul.c5 > 0
    assert "giả định 5 phân hệ" in ul.mo_ta(6)


def test_uoc_luong_tang_theo_so_phan_he():
    """Sai số tham số này rất lớn: BCCS3 có 13 phân hệ, mặc định cũ là 3."""
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]))
    assert uoc_luong(doc, so_phan_he=13).tong > uoc_luong(doc, so_phan_he=3).tong


def test_song_song_rut_ngan_thoi_gian_uoc_tinh():
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]))
    ul = uoc_luong(doc, so_phan_he=5)
    assert ul.phut(6) == pytest.approx(ul.phut(1) / 6)


# ------------------------------------------------------------- tài liệu ---
def test_tom_tat_dem_ca_bang_CO_SO_LIEU():
    """Số bảng thôi chưa đủ: bảng không có cột số liệu thì đường cột của C3 bỏ qua."""
    doc = _doc(_bang(1, [["STT", "CPU"], ["1", "48"]]),
               _bang(2, [["Cấu hình", "Ghi chú"], ["Thông lượng >= 1 Gbps", ""]]),
               Element(index=3, kind="image", section="II", page=1))
    t = tom_tat_tai_lieu(doc)
    assert (t.bang, t.bang_du_lieu, t.anh) == (2, 1, 1)
    assert "1 có số liệu" in t.dong_tom_tat


# ------------------------------------------------------------ checklist ---
def test_chay_checklist_khong_can_model():
    doc = _doc(Element(index=0, kind="heading", text="Cơ sở định cỡ",
                       section="I", page=1, level=1))
    kq = chay_checklist(doc, ten_tai_lieu="x.docx")
    assert kq.tong > 0 and kq.thay >= 1
    assert "KHÔNG TÌM THẤY" in kq.markdown
    assert kq.csv.startswith("TT,")


# --------------------------------------------------------------- tệp ------
def test_luu_tam_giu_nguyen_ten_goc(tmp_path):
    """Tên hồ sơ mang mã PYC và tên hệ thống, còn hiện lại trong báo cáo."""
    p = luu_tam(b"xyz", "Sizing_BCCS3_Lào.docx", str(tmp_path))
    assert p.name == "Sizing_BCCS3_Lào.docx" and p.read_bytes() == b"xyz"


def test_luu_tam_chan_duong_dan_lo_ra_ngoai(tmp_path):
    p = luu_tam(b"x", "../../thoat.docx", str(tmp_path))
    assert p.parent == tmp_path


def test_ten_file_ket_qua():
    assert ten_file_ket_qua("a/b/Sizing X.docx", "checklist", "csv") == \
        "Sizing X-checklist.csv"


# --- trạng thái model đến TỪ DỊCH VỤ, không từ tiến trình giao diện --------
class TestKiemModelQuaDichVu:
    """Container `copilot-ui` không có khoá model và không nên có (B3)."""

    def test_dich_vu_chet_thi_noi_ro_la_DICH_VU_chet(self):
        from src.khach_api import SucKhoe
        tt = kiem_model_qua_dich_vu(SucKhoe(song=False, thong_diep="không kết nối được"))
        assert tt.san_sang is False
        assert "dịch vụ" in tt.thong_diep.lower()

    def test_dich_vu_song_nhung_chua_cau_hinh_model(self):
        from src.khach_api import SucKhoe
        tt = kiem_model_qua_dich_vu(SucKhoe(
            song=True, model_san_sang=False,
            ghi_chu_model="Chưa đặt biến môi trường SIZING_COPILOT_API_KEY"))
        assert tt.san_sang is False
        assert "SIZING_COPILOT_API_KEY" in tt.thong_diep

    def test_dich_vu_san_sang_thi_MO_che_do_tham_dinh(self):
        """Đây là ca hỏng thật 2026-09-14: API có khoá, giao diện thì không, và
        giao diện giấu mất chế độ chính."""
        from src.khach_api import SucKhoe
        tt = kiem_model_qua_dich_vu(SucKhoe(
            song=True, model_san_sang=True, ghi_chu_model="Sẵn sàng, model `x`"))
        assert tt.san_sang is True
        assert "tham_dinh" in che_do_kha_dung(tt)


# ------------------------------------------------- chính trang Streamlit ---
# Chỉ chạy khi máy có cài Streamlit (nó nằm ở nhóm phụ thuộc tuỳ chọn `ui`).
# `AppTest` chạy thật `ui/app.py` không cần trình duyệt, nên bắt được lỗi cú pháp,
# import sai, hay API Streamlit dùng nhầm — những thứ mà test logic không thấy.
st_test = pytest.importorskip("streamlit.testing.v1", reason="chưa cài streamlit")


GOC = pathlib.Path(__file__).resolve().parents[1]


def _chay_app():
    # Đường dẫn TƯƠNG ĐỐI được `AppTest` giải theo file gọi nó, không theo thư mục
    # chạy pytest — nên phải đưa đường dẫn tuyệt đối.
    at = st_test.AppTest.from_file(str(GOC / "ui" / "app.py"), default_timeout=30)
    at.run()
    return at


def test_trang_chay_duoc_khi_CHUA_co_model(monkeypatch):
    """Ca thường gặp nhất khi làm việc ngoài mạng nội bộ. Không được có exception."""
    monkeypatch.delenv("SIZING_COPILOT_API_KEY", raising=False)
    at = _chay_app()
    assert not at.exception
    assert any("cố vấn" in m.value for m in at.sidebar.caption)


def test_trang_hien_o_TAI_TEP_khi_chua_chon_gi():
    at = _chay_app()
    assert not at.exception
    assert len(at.file_uploader) == 1


# --- D3: nói thẳng giới hạn (2026-09-10) ------------------------------------
class TestCauGioiHan:
    def test_moi_cau_deu_co_noi_dung(self):
        from src.giao_dien import cau_gioi_han
        cs = cau_gioi_han()
        assert len(cs) >= 5 and all(c.strip() for c in cs)

    def test_KHONG_lam_tron_87_5_thanh_88(self):
        """87,5% và 88% là hai điều khác nhau khi có người trích lại. `f"{:.0%}"`
        làm tròn LÊN đúng con số sắp công bố."""
        from src.giao_dien import _pt, cau_gioi_han
        assert _pt(0.875) == "87,5%"
        assert _pt(0.07, 0) == "7%"
        assert any("87,5%" in c for c in cau_gioi_han())
        assert not any("88%" in c for c in cau_gioi_han())

    def test_neu_ca_con_so_YEU_NHAT_chu_khong_chi_con_so_dep(self):
        """Nêu 87,5% mà giấu con số yếu là để người đánh giá tự suy ra một công
        cụ khác công cụ thật. Nghiệm thu 2026-09-11 lộ ra con số yếu nhất: trong
        nhóm đòi tính/so số, phần CODE thật sự tính lại được chỉ 1/71."""
        from src.giao_dien import cau_gioi_han
        van = " ".join(cau_gioi_han())
        assert "đòi TÍNH hoặc SO số" in van
        assert "7–8,5%" in van, "nêu DẢI ba lượt, không nêu một điểm đẹp nhất"
        assert "1,4%" in van and "thật sự tính lại được" in van

    def test_noi_ro_phan_nhieu_KHONG_phai_loi_cua_tai_lieu(self):
        from src.giao_dien import cau_gioi_han
        van = " ".join(cau_gioi_han())
        assert "chưa đọc được" in van and "không phải** lỗi của bản sizing" in van

    def test_noi_ro_CHUA_do_duoc_ti_le_bao_sai(self):
        """Hạn chế lớn nhất còn lại. Im lặng về nó là để người dùng tưởng mọi
        dòng đều đúng."""
        from src.giao_dien import cau_gioi_han
        assert any("Chưa đo được tỉ lệ báo sai" in c for c in cau_gioi_han())

    def test_con_so_khop_voi_ket_qua_da_nghiem_thu(self):
        """Mỗi con số phải kèm NGÀY và NGUỒN — để lần sau đo lại thì biết sửa ở
        đâu, và để không ai trích một con số đã cũ. Khớp nghiệm thu 1.13
        2026-09-11: ba lượt A · C · E ở nhiệt độ 0,1."""
        import pathlib
        from src.giao_dien import DO_LUONG
        assert DO_LUONG.ngay == "2026-09-11" and DO_LUONG.ho_so == 14
        assert DO_LUONG.so_luot == 3
        assert DO_LUONG.recall_chinh == (0.865, 0.875)
        assert DO_LUONG.recall_quyet_dinh == (5 / 71, 6 / 71)
        assert abs(DO_LUONG.quyet_dinh_tinh - 1 / 71) < 1e-9
        assert pathlib.Path(DO_LUONG.nguon).exists(), "nguồn phải là file có thật"

    def test_dai_mot_diem_thi_khong_viet_thanh_dai(self):
        from src.giao_dien import _dai
        assert _dai((0.865, 0.875)) == "86,5–87,5%"
        assert _dai((0.5, 0.5)) == "50%"


# ------------------------------------------------- bảng ghi chú thẩm định --
class TestBangPhanHoi:
    @staticmethod
    def _f(id="KPI-02#App", severity="major", rule_ref="KPI-02", finding="CPU vượt ngưỡng",
           location="Mục IV.1, trang 8", scope_key="App", nhom="vong2_chua_dat"):
        return {"id": id, "severity": severity, "rule_ref": rule_ref,
                "finding": finding, "location": location, "scope_key": scope_key,
                "nhom": nhom}

    def test_1_finding_1_dong_du_cot(self):
        from src.giao_dien import chuan_bi_bang
        rows = chuan_bi_bang([self._f()])
        assert len(rows) == 1
        r = rows[0]
        assert r["finding_id"] == "KPI-02#App"
        assert r["mức độ"] == "Quan trọng"
        assert r["mã quy tắc"] == "KPI-02"
        assert r["nội dung"] == "CPU vượt ngưỡng"
        assert r["phân hệ"] == "App"
        assert r["ghi_chu"] == "" and r["phân loại"] == "(chưa phân loại)"

    def test_prefill_ghi_chu_cu(self):
        from src.giao_dien import chuan_bi_bang
        rows = chuan_bi_bang([self._f()], {"KPI-02#App": {
            "ghi_chu": "đúng, quy tắc áp nhầm", "phan_loai": "bao_sai"}})
        assert rows[0]["ghi_chu"] == "đúng, quy tắc áp nhầm"
        assert rows[0]["phân loại"] == "Báo sai"

    def test_noi_dung_dai_bi_cat_va_gop_dong(self):
        from src.giao_dien import NOI_DUNG_TOI_DA, chuan_bi_bang
        f = self._f(finding="từ " * 300)
        rows = chuan_bi_bang([f])
        assert len(rows[0]["nội dung"]) <= NOI_DUNG_TOI_DA
        f2 = self._f(id="x", finding="dòng 1\ndòng 2")
        assert chuan_bi_bang([f2])[0]["nội dung"] == "dòng 1 dòng 2"

    def test_khong_co_rule_ref_thi_gach(self):
        from src.giao_dien import chuan_bi_bang
        f = self._f(id="CANH_BAO#anh", rule_ref="", nhom="khac")
        rows = chuan_bi_bang([f])
        assert rows[0]["mã quy tắc"] == "—"
        assert rows[0]["nhóm"] == "Khác"

    def test_findings_rong_thi_bang_rong(self):
        from src.giao_dien import chuan_bi_bang
        assert chuan_bi_bang([]) == []

    def test_loc_va_thu_tu_severity_truoc(self):
        from src.giao_dien import chuan_bi_bang, loc_bang
        fs = [self._f(id="a", severity="minor", rule_ref="A-01"),
              self._f(id="b", severity="critical", rule_ref="B-01"),
              self._f(id="c", severity="major", rule_ref="C-01"),
              self._f(id="d", severity="major", rule_ref="B-02")]
        rows = loc_bang(chuan_bi_bang(fs), "Tất cả")
        # nghiêm trọng trước; ngang mức thì theo mã quy tắc (B-02 trước C-01)
        assert [r["finding_id"] for r in rows] == ["b", "d", "c", "a"]

        rows_major = loc_bang(chuan_bi_bang(fs), "Quan trọng")
        assert [r["finding_id"] for r in rows_major] == ["d", "c"]

    def test_gom_thay_doi_chi_tra_dong_khac(self):
        from src.giao_dien import chuan_bi_bang, gom_thay_doi
        fs = [self._f(id="a"), self._f(id="b", rule_ref="B-01")]
        goc = chuan_bi_bang(fs)
        sau = [dict(r) for r in goc]
        sau[0]["ghi_chu"] = "đã ghi"
        sau[0]["phân loại"] = "Chấp nhận"
        kq = gom_thay_doi(goc, sau)
        assert kq == [{"finding_id": "a", "ghi_chu": "đã ghi",
                       "phan_loai": "chap_nhan"}]

    def test_gom_thay_doi_luu_lai_y_nguyen_tra_rong(self):
        from src.giao_dien import chuan_bi_bang, gom_thay_doi
        goc = chuan_bi_bang([self._f()])
        assert gom_thay_doi(goc, [dict(r) for r in goc]) == []

    def test_cot_xem_mac_dinh_False_va_khong_dhuy_hai_gom_thay_doi(self):
        """Cột «xem» chỉ để mở khung chi tiết; tick nó KHÔNG được tính là thay
        đổi cần lưu (Lưu hai lần không nhân bản dòng nhật ký)."""
        from src.giao_dien import chuan_bi_bang, gom_thay_doi
        goc = chuan_bi_bang([self._f()])
        assert goc[0]["xem"] is False
        sau = [dict(goc[0])]
        sau[0]["xem"] = True
        assert gom_thay_doi(goc, sau) == []

    def test_noi_dung_day_du_khong_bi_cat_co_can_cu_va_goi_y(self):
        """Bảng cắt «nội dung» 200 ký tự — khung chi tiết phải trả NGUYÊN VĂN
        kèm căn cứ và gợi ý, để không phải lăn ngược lên báo cáo."""
        from src.giao_dien import NOI_DUNG_TOI_DA, noi_dung_day_du
        dai = "từ " * 300
        f = {"finding": dai, "rule_quote": "CPU peak ≤ 70%",
             "computed_evidence": "85% > 70%", "suggestion": "Tăng lên 8 vCPU"}
        van_ban = noi_dung_day_du(f)
        assert van_ban.startswith(dai.strip())          # nguyên văn, KHÔNG cắt
        assert len(van_ban) > NOI_DUNG_TOI_DA
        assert "Nguyên văn quy tắc:** CPU peak ≤ 70%" in van_ban
        assert "Căn cứ tính toán:** 85% > 70%" in van_ban
        assert "Gợi ý sửa:** Tăng lên 8 vCPU" in van_ban

    def test_noi_dung_day_du_bo_qua_phan_trong_va_rong(self):
        """Chi tiết là NGUYÊN VĂN (chỉ strip hai đầu) — khác cột bảng có gộp dòng."""
        from src.giao_dien import noi_dung_day_du
        assert noi_dung_day_du({}) == "(không có nội dung)"
        van = noi_dung_day_du({"finding": "  có khoảng trắng  "})
        assert van == "có khoảng trắng"


# --- 5.1: vẽ hồ sơ -------------------------------------------------------------
class TestVeHoSo:
    D = {
        "so_loi_baseline": 3,
        "cac_lan": [{"so_thu_tu": 1, "dem": {"dat": 0, "chua_dat": 3}},
                    {"so_thu_tu": 2, "dem": {"dat": 1, "chua_dat": 1,
                                             "chua_kiem_duoc": 1, "phat_sinh": 2}}],
        "baseline": [
            {"rule_ref": "CPU-01", "scope_goc": "Master (K8s Master node)",
             "muc_do": "major", "muc_do_lan": "minor", "trang_thai": "chua_dat",
             "ket_luan_boi": "c4", "noi_dung": "CPU vượt", "computed_evidence": "95%",
             "computed_evidence_lan": "92%", "vi_tri": "Mục 1"},
            {"rule_ref": "STO-17", "scope_goc": "MinIO", "muc_do": "major",
             "muc_do_lan": None, "trang_thai": "dat", "ket_luan_boi": "khong_ro"},
        ],
        "phat_sinh": [{"rule_ref": "ARC-06", "scope_goc": "FrontEnd",
                       "muc_do": "minor", "noi_dung": "mới"}],
    }

    def test_csdl_san_sang_doc_tu_health_tho(self):
        from src.giao_dien import csdl_san_sang
        assert csdl_san_sang({"csdl": {"san_sang": True}}) is True
        assert csdl_san_sang({"csdl": {"san_sang": False}}) is False
        assert csdl_san_sang({}) is False, "image cũ không có khoá `csdl`"
        assert csdl_san_sang(None) is False

    def test_tom_tat_lay_lan_moi_nhat(self):
        from src.giao_dien import tom_tat_ho_so
        t = tom_tat_ho_so(self.D)
        assert (t["so_loi_baseline"], t["so_thu_tu"], t["dat"], t["phat_sinh"]) == \
            (3, 2, 1, 2)

    def test_tom_tat_ho_so_chua_co_lan_nao_khong_no(self):
        from src.giao_dien import tom_tat_ho_so
        assert tom_tat_ho_so({"so_loi_baseline": 0})["so_thu_tu"] == 0

    def test_muc_do_giu_baseline_va_ghi_chu_lan_nay(self):
        """5.6: mức độ đóng băng theo baseline; lần này khác thì chú thích."""
        from src.giao_dien import bang_baseline
        b = bang_baseline(self.D)
        assert b[0]["Mức độ"] == "major (lần này: minor)"
        assert b[1]["Mức độ"] == "major"

    def test_hien_can_cu_ca_hai_lan_va_ai_ket_luan(self):
        from src.giao_dien import bang_baseline
        b = bang_baseline(self.D)[0]
        assert (b["Căn cứ lần đầu"], b["Căn cứ lần này"]) == ("95%", "92%")
        assert b["Ai kết luận"] == "Code (C4)"
        assert "Đạt" in bang_baseline(self.D)[1]["Trạng thái"]

    def test_phan_he_hien_ten_GOC(self):
        from src.giao_dien import bang_baseline
        assert bang_baseline(self.D)[0]["Phân hệ"] == "Master (K8s Master node)"

    def test_bang_phat_sinh(self):
        from src.giao_dien import bang_phat_sinh
        assert [r["Quy tắc"] for r in bang_phat_sinh(self.D)] == ["ARC-06"]
        assert bang_phat_sinh({}) == []

    def test_nhan_ho_so(self):
        from src.giao_dien import nhan_ho_so
        n = nhan_ho_so({"id": 7, "ten_file": "a.docx", "so_lan": 2,
                        "so_loi_baseline": 717, "ten": "An"})
        assert n.startswith("#7") and "717 lỗi" in n


# --- 5.2: sửa ----------------------------------------------------------------------
class TestSua:
    def test_bang_baseline_co_so_lan_sua(self):
        from src.giao_dien import bang_baseline
        assert bang_baseline({"baseline": [{"so_lan_sua": 3}]})[0]["Số lần sửa"] == 3

    def test_bang_lan_sua(self):
        from src.giao_dien import bang_lan_sua
        r = bang_lan_sua({"lan_sua": [{"so_lan": 1, "ten": "An", "noi_dung_sua": "x",
                                       "tao_luc": "2026-09-17T10:23:18.123+07:00"}]})
        assert r == [{"Lần": 1, "Người ghi nhận": "An", "Lúc": "2026-09-17 10:23:18",
                      "Đã sửa": "x"}]

    def test_noi_dung_goc_chi_lay_khi_DINH_VI_duoc(self):
        """Gợi ý theo tên phân hệ KHÔNG phải chỗ lỗi — ghi vào «nội dung gốc» là để
        bảng Admin hiểu nhầm."""
        from src.giao_dien import noi_dung_goc_tu_cho_sua
        doan = [{"text": "Redis dùng 32 GB", "rows": None}]
        assert noi_dung_goc_tu_cho_sua({"cach_tim": "phan_tu", "doan": doan}) == \
            "Redis dùng 32 GB"
        assert noi_dung_goc_tu_cho_sua({"cach_tim": "ten_phan_he", "doan": doan}) == ""
        assert noi_dung_goc_tu_cho_sua({"cach_tim": "khong_tim_duoc"}) == ""
        assert noi_dung_goc_tu_cho_sua({}) == ""

    def test_noi_dung_goc_cua_bang_moi_dong_mot_hang_va_cat_do_dai(self):
        from src.giao_dien import TOI_DA_NOI_DUNG_GOC, noi_dung_goc_tu_cho_sua
        cho = {"cach_tim": "muc", "doan": [{"rows": [["A", "1"], ["B", "2"]]}]}
        assert noi_dung_goc_tu_cho_sua(cho) == "A | 1\nB | 2"
        dai = {"cach_tim": "muc", "doan": [{"text": "x" * 5000}]}
        assert len(noi_dung_goc_tu_cho_sua(dai)) == TOI_DA_NOI_DUNG_GOC


class TestBangTuDong:
    """Ảnh nghiệm thu 5.2: tiêu đề cột hiện `0, 1, 2…`, hàng tiêu đề thật thành dữ liệu."""

    def test_hang_dau_lam_tieu_de(self):
        from src.giao_dien import bang_tu_dong
        assert bang_tu_dong([["Máy chủ", "IP"], ["Master 01", "172.21.5.245"]]) == \
            [{"Máy chủ": "Master 01", "IP": "172.21.5.245"}]

    def test_tieu_de_trung_KHONG_nuot_cot(self):
        from src.giao_dien import bang_tu_dong
        r = bang_tu_dong([["Phân hệ", "Cores", "Cores", "RAM", "RAM"],
                          ["Worker", "16", "7.9%", "32,000", "1%"]])
        assert list(r[0]) == ["Phân hệ", "Cores", "Cores (2)", "RAM", "RAM (2)"]
        assert r[0]["Cores (2)"] == "7.9%"

    def test_tieu_de_rong_va_dong_dai_hon_tieu_de(self):
        from src.giao_dien import bang_tu_dong
        r = bang_tu_dong([["A", ""], ["1", "2", "3"]])
        assert list(r[0]) == ["A", "Cột 2", "Cột 3"] and r[0]["Cột 3"] == "3"

    def test_bang_mot_dong_giu_du_lieu(self):
        from src.giao_dien import bang_tu_dong
        assert bang_tu_dong([["x", "y"]]) == [{"Cột 1": "x", "Cột 2": "y"}]

    def test_rong(self):
        from src.giao_dien import bang_tu_dong
        assert bang_tu_dong([]) == [] and bang_tu_dong(None) == []

    def test_trung_voi_ten_da_danh_so_san(self):
        from src.giao_dien import bang_tu_dong
        r = bang_tu_dong([["A", "A (2)", "A"], ["1", "2", "3"]])
        assert len(r[0]) == 3


class TestThamDinhLai53:
    """5.3 — dòng «bản này khác lần trước ở đâu» và «phân hệ nào đổi»."""

    def test_khong_phai_tham_dinh_lai_thi_khong_hien(self):
        from src.giao_dien import tom_tat_thay_doi, tom_tat_vung_doi
        assert tom_tat_thay_doi({}) is None and tom_tat_thay_doi(None) is None
        assert tom_tat_vung_doi({"c3": {}}) == ""

    def test_nop_y_nguyen_thi_CANH_BAO_nop_nham(self):
        from src.giao_dien import tom_tat_thay_doi
        muc, cau = tom_tat_thay_doi({"giong_het": True, "sua": 0, "them": 0, "xoa": 0})
        assert muc == "warning" and "nộp nhầm bản cũ" in cau

    def test_liet_ke_cho_doi(self):
        from src.giao_dien import tom_tat_thay_doi
        muc, cau = tom_tat_thay_doi({"giong_het": False, "sua": 1, "them": 2, "xoa": 0,
                                     "vi_tri": ["Mục II.2, trang 3 · bảng · sửa"],
                                     "con_nua": 2})
        assert muc == "info"
        assert "1 chỗ sửa · 2 chỗ thêm · 0 chỗ xoá" in cau
        assert cau.endswith("Mục II.2, trang 3 · bảng · sửa; và 2 chỗ khác")

    def test_khong_so_duoc_thi_noi_ra(self):
        from src.giao_dien import tom_tat_thay_doi
        assert tom_tat_thay_doi({"loi": "tài liệu lần trước không còn"})[0] == "warning"

    def test_vung_doi(self):
        from src.giao_dien import tom_tat_vung_doi
        assert tom_tat_vung_doi({"vung_doi": ["redis"], "vung_moi": [], "chung_doi": False}) \
            == "phân hệ đổi: redis · phần chung (ngoài mọi phân hệ) không đổi"
        assert "CÓ đổi" in tom_tat_vung_doi({"vung_doi": [], "chung_doi": True})


class TestBaoLoi54:
    """5.4 — bảng lời báo «hệ thống báo sai» và cột đếm trên hai rổ."""

    def test_bang_bao_loi_noi_ro_ro_nao_va_admin_xu_ly_chua(self):
        from src.giao_dien import bang_bao_loi
        r = bang_bao_loi([
            {"tao_luc": "2026-09-18T10:17:03+07:00", "ten": "Nguyễn Văn A",
             "khoa": "ARC-06#tủ rack", "finding_phat_sinh_id": 7, "ly_do": "không có thật",
             "da_xu_ly": False},
            {"tao_luc": "2026-09-18T09:00:00", "ten": "A", "khoa": "CPU-01#kafka",
             "finding_baseline_id": 3, "ly_do": "sửa rồi vẫn báo", "da_xu_ly": True}])
        assert [x["Rổ"] for x in r] == ["phát sinh", "baseline"]
        assert r[0]["Lúc"] == "2026-09-18 10:17:03" and r[0]["Admin đã xử lý"] == "chưa"
        assert r[1]["Admin đã xử lý"] == "rồi"

    def test_rong(self):
        from src.giao_dien import bang_bao_loi
        assert bang_bao_loi(None) == [] and bang_bao_loi([]) == []

    def test_cot_da_bao_loi_tren_ca_hai_bang(self):
        from src.giao_dien import bang_baseline, bang_phat_sinh
        d = {"baseline": [{"rule_ref": "CPU-01", "so_bao_loi": 2}],
             "phat_sinh": [{"rule_ref": "ARC-06", "so_bao_loi": 1}]}
        assert bang_baseline(d)[0]["Đã báo lỗi"] == 2
        assert bang_phat_sinh(d)[0]["Đã báo lỗi"] == 1


class TestBangAdmin56:
    """5.6/5.9 — dựng bảng Admin, lọc mặc định, và chỉ gửi dòng đã đổi."""

    @staticmethod
    def _d(**kw):
        b = {"id": 1, "rule_ref": "CPU-01", "scope_goc": "Kafka", "muc_do": "major",
             "trang_thai": "chua_dat", "ket_luan_boi": "c4", "noi_dung": "CPU vượt ngưỡng",
             "computed_evidence_lan": "`cpu<80` sai", "dau_vao_lan": "cpu_95th=85",
             "vi_tri": "Mục I", "so_bao_loi": 0, "lan_sua": [], "ghi_chu_admin": {}}
        b.update(kw)
        return {"so_lan_sua_max": kw.pop("_max", 0), "baseline": [b]}

    def test_cot_lan_sua_theo_dong_nhieu_nhat_va_o_trong_khi_thieu(self):
        from src.giao_dien import bang_admin
        d = self._d(_max=2, lan_sua=[{"so_lan": 1, "noi_dung_sua": "đổi 12 → 16"}])
        r = bang_admin(d)[0]
        assert r["Lần sửa 1"] == "đổi 12 → 16" and r["Lần sửa 2"] == ""

    def test_hien_dau_vao_code_da_dung(self):
        """5.0b: chỉ 8/11 dòng do code kết luận trùng ở hai lượt — Admin phải thấy
        đầu vào mới biết vì sao trạng thái lật."""
        from src.giao_dien import bang_admin
        assert bang_admin(self._d())[0]["Đầu vào code đã dùng"] == "cpu_95th=85"

    def test_ba_cot_admin_hien_nhan_tieng_Viet(self):
        from src.giao_dien import COT_DANH_GIA, COT_GHI_CHU, COT_LOI_O_PHIA, bang_admin
        d = self._d(ghi_chu_admin={"ghi_chu": "xem lại", "danh_gia": "can_ban",
                                   "loi_o_phia": "he_thong_ai"})
        r = bang_admin(d)[0]
        assert (r[COT_GHI_CHU], r[COT_DANH_GIA], r[COT_LOI_O_PHIA]) == \
            ("xem lại", "Cần bàn", "Hệ thống AI")

    def test_mac_dinh_an_chua_kiem_duoc_nhung_GIU_dong_da_co_nguoi_dung_toi(self):
        from src.giao_dien import bang_admin, loc_bang_admin
        d = self._d(_max=1)
        d["baseline"] += [
            {**d["baseline"][0], "id": 2, "trang_thai": "chua_kiem_duoc"},
            {**d["baseline"][0], "id": 3, "trang_thai": "chua_kiem_duoc",
             "so_bao_loi": 1},
            {**d["baseline"][0], "id": 4, "trang_thai": "chua_kiem_duoc",
             "lan_sua": [{"so_lan": 1, "noi_dung_sua": "đã sửa"}]},
            {**d["baseline"][0], "id": 5, "trang_thai": "chua_kiem_duoc",
             "ghi_chu_admin": {"ghi_chu": "để đó"}}]
        hien, an = loc_bang_admin(bang_admin(d))
        assert [r["id"] for r in hien] == [1, 3, 4, 5] and an == 1
        het, an2 = loc_bang_admin(bang_admin(d), hien_chua_kiem=True)
        assert len(het) == 5 and an2 == 0

    def test_loc_theo_chu(self):
        from src.giao_dien import bang_admin, loc_bang_admin
        d = self._d()
        d["baseline"].append({**d["baseline"][0], "id": 2, "scope_goc": "Redis",
                              "rule_ref": "STO-17"})
        assert [r["id"] for r in loc_bang_admin(bang_admin(d), tim="redis")[0]] == [2]
        assert [r["id"] for r in loc_bang_admin(bang_admin(d), tim="CPU-01")[0]] == [1]

    def test_chi_gui_dong_DA_DOI_va_doi_nhan_ve_ma(self):
        from src.giao_dien import COT_DANH_GIA, COT_GHI_CHU, bang_admin, thay_doi_admin
        d = self._d()
        d["baseline"].append({**d["baseline"][0], "id": 2})
        goc = bang_admin(d)
        sau = [dict(goc[0]), dict(goc[1])]
        sau[1][COT_GHI_CHU] = "cần bàn thêm"
        sau[1][COT_DANH_GIA] = "Từ chối"
        assert thay_doi_admin(goc, sau) == [
            {"finding_baseline_id": 2, "ghi_chu": "cần bàn thêm", "danh_gia": "tu_choi",
             "loi_o_phia": ""}]
        assert thay_doi_admin(goc, goc) == [], "bấm Lưu hai lần không nhân bản lịch sử"


# ------------------------------------------- 5.9 bước 2 — đề xuất sửa quy tắc --
class TestDeXuatQuyTac59b:
    def test_bang_de_xuat_doi_nhan_va_NOI_RO_chua_do_eval(self):
        from src.giao_dien import bang_de_xuat
        r = bang_de_xuat([{"id": 3, "rule_ref": "STO-02", "ten": "Quản trị",
                           "trang_thai": "kiem_dat", "ly_do": "quá chặt",
                           "tao_luc": "2026-09-21T09:10:11.5", "bang_chung_eval": "",
                           "ho_so_id": 1}])[0]
        assert r["Trạng thái"] == "Kiểm đạt — chờ người chốt áp"
        assert r["Lúc"] == "2026-09-21 09:10:11"
        assert r["Eval"] == "chưa ai đo", "trống mà im lặng thì tưởng đã đo (NT4)"

    def test_bang_de_xuat_giu_bang_chung_eval_khi_co(self):
        from src.giao_dien import bang_de_xuat
        r = bang_de_xuat([{"id": 1, "bang_chung_eval": "recall 0.62 → 0.64"}])[0]
        assert r["Eval"] == "recall 0.62 → 0.64"

    def test_tom_tat_kiem_dat_luon_noi_CHUA_do_eval(self):
        from src.giao_dien import tom_tat_kiem_de_xuat
        s = tom_tat_kiem_de_xuat({"dat": True, "so_quy_tac": 151, "so_bieu_thuc": 137,
                                  "chay_duoc_truoc": 77, "chay_duoc_sau": 76,
                                  "canh_bao": ["severity đổi"]})
        assert s.startswith("✓") and "77 → 76" in s and "1 cảnh báo" in s
        assert "CHƯA đo eval" in s, "kiểm tự động KHÔNG phải bằng chứng chất lượng"

    def test_tom_tat_kiem_hong_neu_ro_ly_do_dau_tien(self):
        from src.giao_dien import tom_tat_kiem_de_xuat
        s = tom_tat_kiem_de_xuat({"dat": False, "loi": ["`id` đổi từ …"]})
        assert s.startswith("✗ KHÔNG áp được") and "`id` đổi" in s
        assert tom_tat_kiem_de_xuat(None) == ""

    def test_ma_quy_tac_xep_theo_so_dong_loi(self):
        from src.giao_dien import ma_quy_tac_trong_ho_so
        d = {"baseline": [{"rule_ref": "STO-02"}, {"rule_ref": "EVD-17"},
                          {"rule_ref": "EVD-17"}, {"rule_ref": ""}, {}]}
        assert ma_quy_tac_trong_ho_so(d) == ["EVD-17", "STO-02"]
        assert ma_quy_tac_trong_ho_so(None) == []
