"""Test C2/2.5b — nối số đã neo vào tham số quy tắc. OFFLINE, không cần model.

Dữ liệu lấy từ lượt chạy vision thật 2026-09-08 trên Vtag và PBH 4.0.
"""
from src.extraction.schema import ExtractedValue, SizingCore, SizingExtension
from src.validators.quantitative import QuantitativeValidator
from src.validators.rules_loader import load_rules
from src.vision.neo_so import KetQuaNeoAnh, Neo, OKhaiBao
from src.vision.tham_so_anh import gan_vao_core, tham_so_tu_neo
from src.vision.doc_anh import SoDaDoc


def _neo(scope, gia_tri, cot, bang_con="", raw="20%", loai="phan_tram"):
    return Neo(
        so=SoDaDoc(nhan="node4 - CPU%", raw=raw, gia_tri=None, don_vi="",
                   trich_dan="node4  1403m  20%  10393Mi  66%"),
        loai=loai, gia_tri=gia_tri, scope_key=scope,
        o=OKhaiBao(gia_tri=gia_tri, loai=loai, raw=raw, page=11,
                   location="Mục 1, trang 11", nhan_dong=scope,
                   tieu_de_cot=cot, bang_con=bang_con))


def _kq(*neos):
    return [KetQuaNeoAnh(ma_anh="anh#53", location="Mục 1, trang 11",
                         neo=list(neos), so_da_doc=len(neos))]


class TestAnhXa:
    def test_cot_CPU_ra_cpu_95th(self):
        assert tham_so_tu_neo(_neo("Worker", 20.0, "Số cores / % Tiêu thụ CPU")) \
            == "cpu_95th"

    def test_cot_RAM_ra_ram_95th(self):
        assert tham_so_tu_neo(_neo("Worker", 66.0, "RAM / % Tiêu thụ")) == "ram_95th"

    def test_dai_DISK_khong_co_tham_so_nao_nhan(self):
        """`rules.yaml` có ba input đơn vị `%` và không cái nào cho dung lượng.

        Neo Postgres 63% / Redis 15% / MQTT 11% là ĐÚNG nhưng chưa dùng được — phải
        đếm ra chứ không bỏ im lặng.
        """
        assert tham_so_tu_neo(_neo("Postgres", 63.0, "% Tiêu thụ", "DISK")) is None


class TestGanVaoCore:
    def test_dien_vao_phan_he_C3_da_co(self):
        core = SizingCore(phan_he=[SizingExtension(ten_phan_he="Worker")])
        tk = gan_vao_core(core, _kq(_neo("Worker", 20.0, "% Tiêu thụ CPU")))
        assert tk.gan_moi == 1 and tk.phan_he_tao_moi == 0
        v = core.get("cpu_95th", "Worker")
        assert v is not None and v.value == 20.0 and v.unit == "%"
        assert v.location == "Mục 1, trang 11"
        assert "ảnh đọc" in v.note, "NT2: phải dẫn lại ảnh làm chứng cứ"

    def test_dung_phan_he_khi_C3_khong_thay(self):
        """Nếu không dựng thì đúng ca C3 hỏng lại là ca 2.5 vô dụng — mà C3 hỏng
        chính là lý do 2.5 tồn tại."""
        core = SizingCore()
        tk = gan_vao_core(core, _kq(_neo("Worker", 20.0, "% Tiêu thụ CPU")))
        assert tk.phan_he_tao_moi == 1
        assert core.get("cpu_95th", "Worker").value == 20.0

    def test_KHONG_de_gia_tri_cua_C3(self):
        """C3 đọc thẳng tài liệu; 2.5 suy từ một trùng khớp. Lệch nhau thì phải
        NÓI RA, không để một bên thắng lặng lẽ."""
        core = SizingCore(phan_he=[SizingExtension(
            ten_phan_he="Worker",
            params={"cpu_95th": ExtractedValue(value=45.0, unit="%")})])
        tk = gan_vao_core(core, _kq(_neo("Worker", 20.0, "% Tiêu thụ CPU")))
        assert tk.da_co_lech == 1 and tk.gan_moi == 0
        assert core.get("cpu_95th", "Worker").value == 45.0
        assert "C3=45.0" in tk.lech[0] and "2.5=20.0" in tk.lech[0]

    def test_trung_C3_thi_chi_them_chung_cu(self):
        core = SizingCore(phan_he=[SizingExtension(
            ten_phan_he="Worker",
            params={"cpu_95th": ExtractedValue(value=20.0, unit="%")})])
        tk = gan_vao_core(core, _kq(_neo("Worker", 20.0, "% Tiêu thụ CPU")))
        assert tk.da_co_khop == 1
        assert "ảnh đọc" in core.get("cpu_95th", "Worker").note


def test_C4_ket_luan_duoc_sau_khi_gan():
    """Chuỗi đầy-đủ: neo -> tham số -> C4 ra kết luận, và ĐẠT nay CÓ finding."""
    core = SizingCore()
    gan_vao_core(core, _kq(_neo("Worker", 20.0, "% Tiêu thụ CPU")))
    kq = [o for o in QuantitativeValidator(load_rules()).run(core)
          if o.rule_id == "KPI-02" and o.scope_key == "Worker"]
    assert len(kq) == 1
    assert kq[0].status == "dat"                    # 20% <= 75%
    assert kq[0].finding is not None
    assert kq[0].finding.category == "dat_co_can_cu"


def test_vuot_nguong_van_ra_finding_nang():
    core = SizingCore()
    gan_vao_core(core, _kq(_neo("Worker", 92.0, "% Tiêu thụ CPU", raw="92%")))
    kq = [o for o in QuantitativeValidator(load_rules()).run(core)
          if o.rule_id == "KPI-02" and o.scope_key == "Worker"]
    assert kq[0].status == "vi_pham"
    assert kq[0].finding.severity == "critical"
