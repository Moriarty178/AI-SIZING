"""Test 1.4 — chuẩn hóa đơn vị & số liệu. Chạy offline.

Phần lớn ca thử lấy từ tài liệu sizing và PNX THẬT, nên chúng là hồi quy cho lỗi
đã xảy ra ngoài đời chứ không phải ví dụ bịa.
"""
import pytest

from src.normalization.numbers import parse_all_numbers, parse_number, parse_percent
from src.normalization.sanity import check_storage_per_user, check_tps_per_user
from src.normalization.units import UnknownUnit, Units, load_units


# ---------------------------------------------------------------- số ------
@pytest.mark.parametrize("text, value", [
    ("3.000.000", 3_000_000),   # nhiều nhóm 3 chữ số -> chắc chắn phân nhóm nghìn
    ("6,72", 6.72),             # 2 chữ số sau dấu -> chắc chắn thập phân
    ("0.75", 0.75),
    ("2,9", 2.9),
    ("1.234,56", 1234.56),      # cả hai dấu -> dấu sau là thập phân
    ("1,234.56", 1234.56),
    ("143", 143),
    ("-12,5", -12.5),
])
def test_doc_so_khong_luong_nghia(text, value):
    p = parse_number(text)
    assert p.value == pytest.approx(value)
    assert not p.ambiguous


@pytest.mark.parametrize("text", ["0,042", "0.042", "0,500"])
def test_nhom_dau_la_0_thi_chac_chan_la_thap_phan(text):
    """Phân nhóm nghìn không bao giờ cho '0' ở nhóm đầu."""
    p = parse_number(text)
    assert p.value < 1
    assert not p.ambiguous


def test_1_500_la_luong_nghia_va_bao_ca_hai_cach_doc():
    """Cạm bẫy chính: 1.500 có thể là 1500 hoặc 1,5 — lệch 1000 lần."""
    p = parse_number("1.500")
    assert p.ambiguous
    assert p.value == 1500          # kiểu Việt là mặc định
    assert p.alt_value == 1.5       # nhưng cách đọc kia vẫn được trả về
    assert "1500" in p.note or "1.500" in p.note


def test_doi_kieu_tai_lieu_thi_doi_cach_doc_mac_dinh():
    assert parse_number("1.500", style="en").value == 1.5
    assert parse_number("1,500", style="en").value == 1500


def test_khong_co_so_thi_tra_None():
    assert parse_number("không có số nào") is None


def test_lay_moi_so_theo_thu_tu():
    got = [p.value for p in parse_all_numbers("CPU 143 Cint, RAM 176 GB, 3 máy")]
    assert got == [143, 176, 3]


def test_phan_tram_chia_100_chi_khi_co_dau_phan_tram():
    assert parse_percent("75%").value == pytest.approx(0.75)
    assert parse_percent("0,75").value == pytest.approx(0.75)
    # "75" trần có thể là 75 đơn vị bất kỳ -> KHÔNG tự chia 100
    assert parse_percent("75").value == 75


# -------------------------------------------------------------- đơn vị ----
def test_dung_luong_dung_co_so_1024_dung_nhu_PNX_yeu_cau():
    """PNX: 'Đổi từ GB ra TB phải chia 1024 chứ không phải 1000'."""
    u = load_units()
    assert u.convert(2048, "GB", "TB") == pytest.approx(2.0)
    assert u.convert(1, "TB", "GB") == pytest.approx(1024)


def test_bang_thong_dung_co_so_1000():
    u = load_units()
    assert u.convert(1, "Gbps", "Mbps") == pytest.approx(1000)


def test_KB_tren_giay_la_BYTE_khong_phai_bit():
    """Chênh đúng 8 lần — lỗi im lặng nguy hiểm nhất của nhóm băng thông."""
    u = load_units()
    q_byte = u.parse_quantity("35000 KB/s")
    q_bit = u.parse_quantity("35000 kb/s")
    assert q_byte.unit == "kbyte_s"
    assert q_bit.unit == "kbps"
    assert q_byte.base_value == pytest.approx(q_bit.base_value * 8)


def test_don_vi_bang_thong_viet_mo_ho_thi_danh_dau_luong_nghia():
    u = load_units()
    q = u.parse_quantity("100 KBPS")     # không khớp dạng hoa/thường nào
    assert q.ambiguous
    assert "byte hay bit" in q.note


def test_parse_quantity_tren_cac_chuoi_lay_tu_tai_lieu_that():
    u = load_units()
    assert u.parse_quantity("2,9 TB").base_value == pytest.approx(2.9 * 1024 ** 4)
    assert u.parse_quantity("176GB").value == 176
    assert u.parse_quantity("6 tháng").base_value == pytest.approx(6 * 2592000)
    assert u.parse_quantity("3500 CCU").unit == "ccu"
    assert u.parse_quantity("143 Cint").group == "cpu"


def test_khong_quy_doi_giua_hai_nhom_khac_nhau():
    u = load_units()
    with pytest.raises(UnknownUnit):
        u.convert(1, "GB", "Gbps")


def test_don_vi_la_thi_bao_loi_chu_khong_doan():
    u = load_units()
    with pytest.raises(UnknownUnit):
        u.resolve("quả táo")


def test_KHONG_quy_doi_vcpu_sang_cint():
    """Tỷ lệ phụ thuộc đời CPU và overcommit — đã là quy tắc CPU-03/CPU-09.

    Đặt hằng số ở units.yaml sẽ lặng lẽ ghi đè quy tắc, vi phạm NT3.
    """
    u = load_units()
    with pytest.raises(UnknownUnit):
        u.convert(1, "vcpu", "cint")


def test_KHONG_quy_doi_CCU_sang_tong_nguoi_dung():
    """Tỷ lệ đồng thời là dữ liệu đầu vào từng hệ, không được giả định."""
    u = load_units()
    with pytest.raises(UnknownUnit):
        u.convert(1, "ccu", "user")


# ------------------------------------------------------------ hợp lý -----
def test_bat_duoc_ca_that_3_trieu_TB_cho_1080_nguoi():
    """Ca thật trong PNX: '3.000.000 TB cho 1.080 người dùng' = 2,7 PB/người."""
    u = load_units()
    total = u.parse_quantity("3000000 TB").base_value
    issue = check_storage_per_user(total, 1080)
    assert issue is not None
    assert issue.code == "HOPLY-DUNGLUONG"
    assert "ĐƠN VỊ" in issue.message
    assert issue.computed_evidence          # NT2: phải có căn cứ tính được


def test_dung_luong_hop_ly_thi_khong_canh_bao():
    u = load_units()
    total = u.parse_quantity("500 GB").base_value
    assert check_storage_per_user(total, 1080) is None


def test_tps_moi_nguoi_dung_qua_cao_thi_canh_bao():
    issue = check_tps_per_user(tps=50_000, n_users=300)
    assert issue is not None and issue.code == "HOPLY-TPS"


def test_khong_canh_bao_khi_thieu_du_lieu():
    assert check_storage_per_user(0, 100) is None
    assert check_tps_per_user(100, 0) is None


def test_nguong_hop_ly_doc_tu_config_khong_hard_code():
    """NT3: người nghiệp vụ sửa ngưỡng trong units.yaml là đổi được hành vi."""
    u = load_units()
    cfg = dict(u.cfg)
    cfg["hop_ly"] = {"dung_luong_moi_nguoi_dung": {"canh_bao_tren_gb": 0.001},
                     "tps_moi_nguoi_dung": {"canh_bao_tren": 10}}
    strict = Units(cfg)
    total = u.parse_quantity("500 GB").base_value
    assert check_storage_per_user(total, 1080, units=strict) is not None
