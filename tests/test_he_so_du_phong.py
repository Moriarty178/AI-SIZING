"""Test C4 · hệ số dự phòng thông lượng FW/LB. OFFLINE, không cần model.

Mọi ô công thức dưới đây chép NGUYÊN VĂN từ hồ sơ thật trong tập dev
(`cap bo sung VTracking 2.0.1 14716`, hai bản trước/sau khi sửa theo nhận xét).
"""
import dataclasses

from src.extraction.cong_thuc import doc_mot_o
from src.validators.he_so_du_phong import (
    MA_FW, MA_LB, ThongKeHeSo, kiem_he_so_du_phong, la_buoc_trung_gian,
    la_thong_luong_mang)
from src.validators.rules_loader import load_rules


class _Bang:
    kind = "table"
    page = 18
    section = "1.1"
    section_title = "Thông lượng luồng FLV"

    def __init__(self, rows):
        self.rows = rows
        self.text = " ".join(" ".join(r) for r in rows)

    @property
    def location(self):
        return "Mục 1.1, trang 18"


class _Doc:
    def __init__(self, *bangs):
        self._b = list(bangs)

    def tables(self):
        return self._b


def _doc_vtracking_v1():
    return _Doc(_Bang([
        ["Module", "Thông số", "Máy chủ Tiến trình", "Ghi chú"],
        ["1. vLB cho video streaming", "Thông lượng cho Web cho 3215 TPS (1)",
         "= (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s", "KPI 80%, Ksaiso = 1.1."],
        ["1. vLB cho video streaming", "Thông lượng cho Mobile cho 10,602 TPS (2)",
         "=125*10602/0.8*1.1 = 1,822,219 KB/s", "KPI 80%"],
        ["1. vLB cho video streaming", "Tổng thông lượng cần thiết + (2)",
         "696,249 + 1,822,219 = 2,518,468 KB/s", ""],
        ["vLB cho thiết bị", "Thông lượng cho 17,284 TPS lên Protocol Adaptor",
         "= 17,284 * 6 = 103,704 KB/s", ""]]))


def _doc_vtracking_v2():
    return _Doc(_Bang([
        ["Module", "Thông số", "Máy chủ Tiến trình"],
        ["1. LB cho video streaming", "Thông lượng cho Web cho 3215 TPS (1)",
         "= (125 + 32.5) * 3215/0.8*1.2 = 759,544 KB/s"],
        ["LB cho thiết bị", "Thông lượng cho 17,284 TPS",
         "= 17,284 * 6/0.8*1.2 = 155,556 KB/s"]]))


def test_bat_dung_ba_dong_ma_ban_sau_da_sua():
    """Bằng chứng mạnh nhất có được: bản v2 của chính hồ sơ này sửa đúng ba dòng
    ấy thành ×1.2. Người thẩm định viết «Tính thông lượng LB, FW chỉ có K dự
    phòng 1.2»."""
    fs, tk = kiem_he_so_du_phong(_doc_vtracking_v1(), load_rules())
    sai = [f for f in fs if f.category == "sai_cong_thuc"]
    assert len(sai) == 3
    assert tk.cong_don == 1, "dòng cộng dồn phải bị bỏ qua, không bị báo"
    assert all(f.rule_ref == MA_LB for f in sai)
    assert all(f.co_can_cu() for f in sai), "NT2"
    assert "×1.1" in sai[0].finding
    assert "không thấy hệ số dự phòng nào" in sai[2].finding


def test_ban_da_sua_thi_ra_finding_DAT_chu_khong_im_lang():
    fs, tk = kiem_he_so_du_phong(_doc_vtracking_v2(), load_rules())
    assert tk.thieu_he_so == 0 and tk.dat == 2
    assert all(f.category == "dat_co_can_cu" for f in fs)
    assert all(f.severity == "info" for f in fs)


def test_moi_o_cong_thuc_deu_roi_vao_dung_MOT_nhom_dem():
    """Bộ đếm phải cộng lại bằng tổng. Lỗi 'nuốt bộ đếm' đã xảy ra một lần ở
    `neo_so.py` ngày 2026-09-08 và làm cả một lượt đo thành vô nghĩa."""
    _, tk = kiem_he_so_du_phong(_doc_vtracking_v1(), load_rules())
    ten = [f.name for f in dataclasses.fields(ThongKeHeSo) if f.name != "o_cong_thuc"]
    assert sum(getattr(tk, a) for a in ten) == tk.o_cong_thuc


def test_he_so_1_2_lay_tu_rules_yaml_chu_khong_hard_code():
    """NT3. Đổi `globals.port_reserve` là đổi cả phép kiểm."""
    rs = load_rules()
    assert rs.globals["port_reserve"] == 1.20
    rs.globals["port_reserve"] = 1.1        # giả định người nghiệp vụ sửa YAML
    fs, tk = kiem_he_so_du_phong(_doc_vtracking_v1(), rs)
    assert tk.thieu_he_so == 1 and tk.dat == 2   # hai dòng ×1.1 nay là ĐẠT


class TestCuaChan:
    def test_KHONG_soi_ngoai_thong_luong_mang(self):
        """`1.1` là `error_margin` hợp lệ ở rất nhiều chỗ. Bảng máy chủ không
        được đụng tới, nếu không sẽ báo bừa hàng loạt."""
        d = _Doc(_Bang([["Máy chủ", "RAM"], ["App", "= 2960*1.1 = 3256 GB"]]))
        fs, tk = kiem_he_so_du_phong(d, load_rules())
        assert fs == [] and tk.ngoai_pham_vi == 1

    def test_can_ca_thiet_bi_LAN_dai_luong(self):
        ct = doc_mot_o("= 100*1.1 = 110")
        ct.bang_text = "Thông lượng cho Web"          # có đại lượng, thiếu thiết bị
        assert not la_thong_luong_mang(ct)
        ct.bang_text = "vLB cho video streaming"      # có thiết bị, thiếu đại lượng
        assert not la_thong_luong_mang(ct)
        ct.bang_text = "vLB cho video streaming — thông lượng"
        assert la_thong_luong_mang(ct)

    def test_so_hoc_khong_tu_khop_thi_khong_bao(self):
        """NT4: ô mà chính số học của tác giả không xác nhận thì không được dùng
        làm căn cứ cho bất cứ kết luận nào."""
        d = _Doc(_Bang([["vLB", "Thông lượng"], ["x", "= 100*1.1 = 999"]]))
        fs, tk = kiem_he_so_du_phong(d, load_rules())
        assert fs == [] and tk.khong_tu_khop == 1

    def test_buoc_trung_gian_bi_dong_sau_nhan_he_so_thi_bo_qua(self):
        """Ca thật (hồ sơ Mykid, tập TEST): dòng gốc rồi mới dòng dự phòng. Đòi
        hệ số ở dòng gốc là báo sai — nó chưa tới lượt."""
        goc = doc_mot_o("(958 * 8 * 630) / 1000000 = 4.83 Mbs")
        sau = doc_mot_o("4.83 * 1.1 = 5.31 Mbs")
        assert la_buoc_trung_gian(goc, [goc, sau])
        assert not la_buoc_trung_gian(sau, [goc, sau])

    def test_dong_bi_CONG_DON_thi_van_phai_soi(self):
        """Cửa trên phải HẸP. «696,249 + 1,822,219» cũng tiêu thụ kết quả dòng
        gốc, nhưng ở đó hệ số đáng lẽ đã nằm sẵn trong từng dòng — bỏ qua dòng
        gốc vì lý do này sẽ mất hai phát hiện đúng của VTracking."""
        goc = doc_mot_o("= (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s")
        tong = doc_mot_o("696,249 + 1,822,219 = 2,518,468 KB/s")
        assert not la_buoc_trung_gian(goc, [goc, tong])


def test_chon_ma_quy_tac_theo_thiet_bi():
    d = _Doc(_Bang([["Firewall", "Thông lượng"], ["x", "= 100*1.1 = 110"]]))
    fs, _ = kiem_he_so_du_phong(d, load_rules())
    assert [f.rule_ref for f in fs] == [MA_FW]
