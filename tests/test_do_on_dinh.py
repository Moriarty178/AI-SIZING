"""5.0b — phép đo độ ổn định. OFFLINE, không cần API lẫn model.

Phép đo này quyết định thiết kế 5.1/5.3/5.6, nên bản thân nó phải đúng: một con
số sai ở đây dẫn tới một tuần code sai hướng.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.do_on_dinh import (_dong_dich_vu, _khoa_goc,   # noqa: E402
                                _scope_chuan_hoa, gia_tri_do,
                                so_luot_goi, so_sanh)
from src.khach_api import SucKhoe                           # noqa: E402


def _f(fid, **kw):
    d = {"id": fid, "severity": "cao", "nhom": "vong2_chua_dat",
         "finding": "mô tả", "computed_evidence": "", "location": "Mục I"}
    d.update(kw)
    return d


class TestKhoaGoc:
    def test_bo_hau_to_khu_trung(self):
        assert _khoa_goc("KPI-02#PH1#2") == "KPI-02#PH1"

    def test_KHONG_dung_vao_id_thuong(self):
        """`id` gốc là `{rule}#{scope}` — hai phần. Cắt đi là hỏng khoá."""
        assert _khoa_goc("KPI-02#PH1") == "KPI-02#PH1"
        assert _khoa_goc("KPI-02#he_thong") == "KPI-02#he_thong"

    def test_scope_ket_thuc_bang_so_KHONG_bi_cat(self):
        """Phân hệ tên «PH2» rất thường gặp; cắt nhầm là gộp hai finding làm một."""
        assert _khoa_goc("KPI-02#PH2") == "KPI-02#PH2"


class TestSoSanh:
    def test_hai_luot_giong_het(self):
        ds = [_f("A#x"), _f("B#y")]
        kq = so_sanh(ds, list(ds))
        assert kq["khop"] == 2 and kq["chi_a"] == 0 and kq["chi_b"] == 0

    def test_dem_dung_ben_nao_thieu(self):
        kq = so_sanh([_f("A#x"), _f("B#y")], [_f("A#x"), _f("C#z")])
        assert (kq["khop"], kq["chi_a"], kq["chi_b"]) == (1, 1, 1)

    def test_tach_MAT_KHOP_VI_HAU_TO_khoi_model_doi_y(self):
        """Hai finding trùng `rule#scope`, lượt sau đảo thứ tự → id lệch nhưng
        tập finding KHÔNG đổi. Đây là lỗi khoá, sửa được bằng code — không được
        gộp chung với «model đổi ý»."""
        a = [_f("A#x", finding="một"), _f("A#x#2", finding="hai")]
        b = [_f("A#x", finding="hai"), _f("A#x#2", finding="một")]
        kq = so_sanh(a, b)
        assert kq["khop_theo_khoa_goc"] == 2
        assert kq["mat_khop_do_hau_to"] == 0, "id vẫn khớp, chỉ nội dung đảo chỗ"
        assert kq["doi"]["cau_chu"] == 2

    def test_mat_khop_do_hau_to_khi_so_ban_sao_giu_nguyen_ma_id_lech(self):
        a = [_f("A#x"), _f("A#x#2")]
        b = [_f("A#x"), _f("A#x#3")]
        kq = so_sanh(a, b)
        assert kq["khop"] == 1
        assert kq["khop_theo_khoa_goc"] == 2
        assert kq["mat_khop_do_hau_to"] == 1

    def test_dem_tung_loai_thay_doi_rieng(self):
        a = [_f("A#x", severity="cao", computed_evidence="12")]
        b = [_f("A#x", severity="thap", computed_evidence="13")]
        kq = so_sanh(a, b)
        assert kq["doi"]["muc_do"] == 1 and kq["doi"]["can_cu"] == 1
        assert kq["doi"]["cau_chu"] == 0

    def test_dem_dong_code_tinh_lai_duoc(self):
        """Chỉ dòng có `computed_evidence` mới mang được trạng thái Đạt/Chưa đạt
        một cách chắc chắn — con số này định cỡ cột Trạng thái của 5.6."""
        a = [_f("A#x", computed_evidence="1,2"), _f("B#y"), _f("C#z")]
        kq = so_sanh(a, list(a))
        assert kq["code_tinh_duoc_a"] == 1 and kq["code_tinh_duoc_khop"] == 1

    def test_khoang_trang_KHONG_tinh_la_can_cu(self):
        kq = so_sanh([_f("A#x", computed_evidence="   ")], [_f("A#x")])
        assert kq["code_tinh_duoc_a"] == 0

    def test_dem_dong_chua_kiem_duoc(self):
        a = [_f("A#x", nhom="vong2_chua_kiem"), _f("B#y")]
        assert so_sanh(a, a)["chua_kiem_duoc_a"] == 1

    def test_tap_rong_khong_no(self):
        kq = so_sanh([], [])
        assert kq["khop"] == 0 and kq["so_a"] == 0


class TestDongDichVu:
    """Dòng in ĐẦU TIÊN của script. Nổ ở đây là giết cả phép đo trước khi nó
    chạm tới dữ liệu — đã xảy ra thật 2026-09-16 (`SucKhoe` không có `.ban`)."""

    def test_health_khong_co_nhan_ban_van_in_duoc(self):
        d = _dong_dich_vu(SucKhoe(song=True, commit="abc1234"))
        assert "abc1234" in d and "—" in d

    def test_health_co_nhan_ban_thi_in_ra(self):
        sk = SucKhoe(song=True, commit="abc1234", tho={"ban": "v2"})
        assert "v2" in _dong_dich_vu(sk)

    def test_thieu_ca_commit_lan_nhan_van_khong_no(self):
        assert _dong_dich_vu(SucKhoe(song=True))


class TestGiaTriDo:
    """Phép đo tự nói nó có dùng được không — bằng DỮ LIỆU của hai lượt chạy.

    Ngày 2026-09-16 mất trọn một phép đo vì chuyện này chỉ nằm trong trí nhớ
    người chạy: hai lượt khớp 61/61 mà không ai chứng minh được lượt sau có gọi
    model hay chỉ phát lại từ đệm.
    """
    TAT = {"bat": False, "ghi_them": 0}
    BAT_CO_GOI = {"bat": True, "ghi_them": 96}
    BAT_PHAT_LAI = {"bat": True, "ghi_them": 0}

    def _v(self, tk, **kw):
        # Mặc định CÓ gọi model: lớp này kiểm phần đệm, nên đừng để thiếu bằng
        # chứng gọi làm nhiễu. Ca không gọi lần nào nằm ở `TestSoLuotGoi`.
        d = {"thong_ke_cache": tk, "tuy_chon": {},
             "thong_ke": {"c3": {"luot_goi": 71}, "c5": {"luot_goi": 120}}}
        d.update(kw)
        return d

    def test_ca_hai_luot_tat_dem_thi_dung_duoc(self):
        dung, _ = gia_tri_do(self._v(self.TAT), self._v(self.TAT))
        assert dung is True

    def test_dem_bat_nhung_co_ghi_them_van_la_goi_that(self):
        dung, ly = gia_tri_do(self._v(self.TAT), self._v(self.BAT_CO_GOI))
        assert dung is True
        assert "96 lời gọi thật" in " ".join(ly)

    def test_phat_lai_hoan_toan_tu_dem_thi_KHONG_dung_duoc(self):
        dung, ly = gia_tri_do(self._v(self.TAT), self._v(self.BAT_PHAT_LAI))
        assert dung is False
        assert "KHÔNG gọi model" in " ".join(ly)

    def test_thieu_so_lieu_dem_thi_KHONG_dam_bao(self):
        """Image cũ hơn bản 2026-09-16 không ghi `thong_ke_cache`. Im lặng coi
        như đạt là đúng cái bẫy đã sập một lần."""
        dung, ly = gia_tri_do(self._v({}), self._v(self.TAT))
        assert dung is False
        assert "KHÔNG có số liệu đệm" in " ".join(ly)

    def test_co_loc_nhom_thi_chua_du_co_so_chot_thiet_ke(self):
        """Lượt 2026-09-16 lọc `chi_nhom=['KPI']` — 61 finding của MỘT nhóm quy
        tắc, không phải một lượt thẩm định đầy đủ."""
        dung, ly = gia_tri_do(
            self._v(self.TAT, tuy_chon={"chi_nhom": ["KPI"], "song_song": 12}),
            self._v(self.TAT))
        assert dung is False
        assert "chi_nhom" in " ".join(ly)

    def test_loc_vong_hay_song_song_KHONG_lam_mat_gia_tri(self):
        """`song_song` chỉ đổi tốc độ, không đổi phạm vi quy tắc."""
        dung, _ = gia_tri_do(self._v(self.TAT, tuy_chon={"song_song": 12}),
                             self._v(self.TAT))
        assert dung is True


class TestSoLuotGoi:
    """Bằng chứng THẬT là số lời gọi, không phải cờ đệm.

    2026-09-16: hai lượt tắt đệm, trùng khớp 61/61, nhưng chạy hết 2 phút cho
    một tài liệu đáng lẽ tốn ~16 — dấu ✅ in ra dựa trên cờ đệm là sai.
    """

    def test_cong_du_ba_giai_doan_goi_model(self):
        v = {"thong_ke": {"c3": {"luot_goi": 71}, "c5": {"luot_goi": 120},
                          "c2": {"luot_goi": 5}, "c1_bang": 9}}
        assert so_luot_goi(v) == 196

    def test_C4_thuan_code_KHONG_duoc_tinh_vao(self):
        v = {"thong_ke": {"c3": {"luot_goi": 71},
                          "c4_he_so_du_phong": {"luot_goi": 999}}}
        assert so_luot_goi(v) == 71

    def test_khong_ghi_thong_ke_thi_None_chu_khong_phai_0(self):
        """Không biết KHÁC với biết là không. Trả 0 là biến một lượt chạy cũ
        thành một lời khẳng định sai."""
        assert so_luot_goi({}) is None
        assert so_luot_goi({"thong_ke": {"c1_bang": 9}}) is None

    def test_khong_goi_lan_nao_thi_phep_do_VO_NGHIA(self):
        v = {"thong_ke": {"c3": {"luot_goi": 0}, "c5": {"luot_goi": 0},
                          "cache": {"bat": False, "ghi_them": 0}},
             "thong_ke_cache": {"bat": False, "ghi_them": 0}, "tuy_chon": {}}
        dung, ly = gia_tri_do(v, v)
        assert dung is False
        assert "0 lời gọi model" in " ".join(ly)

    def test_dem_tat_KHONG_con_duoc_tinh_la_bang_chung_co_goi(self):
        """Đệm tắt chỉ chứng minh KHÔNG phát lại. Hai mệnh đề khác nhau."""
        v = {"thong_ke": {"c3": {"luot_goi": 0}},
             "thong_ke_cache": {"bat": False, "ghi_them": 0}, "tuy_chon": {}}
        dung, _ = gia_tri_do(v, v)
        assert dung is False

    def test_co_goi_that_va_dem_tat_thi_dung_duoc(self):
        v = {"thong_ke": {"c3": {"luot_goi": 71}, "c5": {"luot_goi": 120}},
             "thong_ke_cache": {"bat": False, "ghi_them": 0}, "tuy_chon": {}}
        dung, _ = gia_tri_do(v, v)
        assert dung is True


class TestScopeChuanHoa:
    """Đo 2026-09-16 (268/272 lời gọi thật): id lệch chủ yếu có dạng
    `ARC-02#Master (K8s Master node)` ↔ `ARC-02#Master (K8s Control plane)` —
    CÙNG phân hệ, chỉ phần mô tả trong ngoặc do C3 diễn đạt lại."""

    def test_bo_phan_dien_giai_trong_ngoac(self):
        assert _scope_chuan_hoa("ARC-02#Master (K8s Master node)") == \
            _scope_chuan_hoa("ARC-02#Master (K8s Control plane)")

    def test_KHONG_gop_hai_phan_he_khac_ten(self):
        """Chuẩn hoá mà gộp nhầm MinIO với FrontEnd là che mất một khác biệt thật."""
        assert _scope_chuan_hoa("ARC-06#MinIO") != _scope_chuan_hoa("ARC-06#FrontEnd")

    def test_KHONG_gop_hai_quy_tac_khac_nhau(self):
        assert _scope_chuan_hoa("ARC-02#Master (a)") != _scope_chuan_hoa("ARC-03#Master (a)")

    def test_khong_phan_biet_hoa_thuong_va_khoang_trang(self):
        assert _scope_chuan_hoa("CPU-01#Kafka ") == _scope_chuan_hoa("CPU-01#kafka")

    def test_bo_hau_to_khu_trung_truoc_khi_chuan_hoa(self):
        assert _scope_chuan_hoa("KPI-02#PH1 (x)#2") == "KPI-02#ph1"

    def test_he_thong_giu_nguyen(self):
        assert _scope_chuan_hoa("ARC-10#he_thong") == "ARC-10#he_thong"

    def test_so_sanh_dem_rieng_phan_mat_khop_do_ten_phan_he(self):
        a = [_f("ARC-02#Master (K8s Master node)"), _f("ARC-06#MinIO")]
        b = [_f("ARC-02#Master (K8s Control plane)"), _f("ARC-06#FrontEnd")]
        kq = so_sanh(a, b)
        assert kq["khop"] == 0
        assert kq["khop_scope_chuan_hoa"] == 1, "Master phải khớp lại"
        assert kq["mat_khop_do_ten_scope"] == 1
        assert kq["ds_chi_a"] and kq["ds_chi_b"], "phải giữ đủ danh sách"


def test_ben_vung_KHONG_dem_trung_dong_doi_nhieu_thu():
    """Bản trước trừ thẳng từng loại đổi: một dòng đổi cả mức độ lẫn căn cứ bị
    trừ hai lần, số «bền hoàn toàn» thấp hơn thật."""
    a = [_f("A#x", severity="cao", computed_evidence="1"), _f("B#y")]
    b = [_f("A#x", severity="thap", computed_evidence="2"), _f("B#y")]
    assert so_sanh(a, b)["ben_vung"] == 1
