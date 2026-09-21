"""Test 5.9 bước 2 · kiểm đề xuất sửa quy tắc. OFFLINE, không cần model.

Phần lớn test chạy trên `config/rules.yaml` THẬT — đó mới là thứ Admin sẽ sửa, và
những cạm bẫy đáng gác (thụt đầu dòng, chú thích, khối `>` nhiều dòng) chỉ có ở file
thật. Vài ca hiếm dùng file nhỏ dựng tay vì không tái hiện được trên file thật.
"""
import pathlib

import pytest
import yaml

from src.validators.de_xuat import (
    bieu_thuc, bieu_thuc_hong, doc_khoi, ghep_khoi, kiem_de_xuat, pham_vi_khoi)
from src.validators.rules_loader import RuleSet, load_rules

VAN = pathlib.Path("config/rules.yaml").read_text(encoding="utf-8")


def _khoi(ma: str) -> str:
    return doc_khoi(VAN, ma)


def _ma_chay_duoc() -> str:
    """Một quy tắc C4 ĐANG chạy được. STO-02 không dùng được cho các ca "chạy được →
    không chạy được": nó vốn đã bị chặn vì thiếu bảng tra (`lookup` chưa số hoá)."""
    return load_rules().runnable()[0].id


class TestDocKhoi:
    def test_doc_dung_khoi_va_GIU_NGUYEN_chu_thich(self):
        k = _khoi("STO-02")
        assert k.startswith("  - id: STO-02\n")
        assert "RAID 6 chịu được hỏng 2 ổ đồng thời" in k, "chú thích `note` phải còn"
        assert "STO-03" not in k and "STO-01" not in k, "không lấn sang quy tắc kế"

    def test_ma_dai_khong_nuot_ma_ngan(self):
        """`STO-1` và `STO-14` cùng tiền tố. Khớp theo tiền tố là lấy nhầm khối."""
        for ma in ("STO-01", "STO-14"):
            assert yaml.safe_load(_khoi(ma))[0]["id"] == ma

    def test_khong_co_ma_thi_bao_chu_khong_tra_khoi_rong(self):
        assert pham_vi_khoi(VAN, "KHONG-CO") is None
        with pytest.raises(KeyError):
            doc_khoi(VAN, "KHONG-CO")

    def test_ghep_lai_y_nguyen_thi_file_khong_doi(self):
        """Bất biến nền: nếu `doc_khoi`/`ghep_khoi` lệch nhau một dòng thì mọi đề xuất
        đều âm thầm ăn mất hoặc nhân đôi một dòng của file."""
        for ma in ("KPI-01", "STO-02", [r.id for r in load_rules().rules][-1]):
            assert ghep_khoi(VAN, ma, _khoi(ma)) == VAN

    def test_moi_quy_tac_deu_doc_duoc_khoi(self):
        rs = load_rules()
        assert len(rs) == 151
        for r in rs.rules:
            assert yaml.safe_load(_khoi(r.id))[0]["id"] == r.id


def test_moi_bieu_thuc_cua_bo_quy_tac_dang_chay_deu_phan_tich_duoc():
    """Gác chính `rules.yaml` đang chạy: đo 2026-09-21 là 137 biểu thức trên 151 quy
    tắc (PLAN ghi «77 công thức» là con số cũ, đã sửa). Thêm quy tắc mà gõ sai cú pháp
    thì test này đỏ ngay, không phải chờ một lượt thẩm định 20 phút."""
    rs = load_rules()
    assert len(bieu_thuc(rs)) == 137
    assert bieu_thuc_hong(rs) == []


class TestDeXuatDat:
    def test_doi_nguong_trong_check_thi_dat(self):
        k = _khoi("STO-02").replace("check: \"cap_raid == 6\"",
                                    "check: \"cap_raid >= 6\"")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert kq.dat and kq.loi == []
        assert "cap_raid >= 6" in kq.diff and "-" in kq.diff
        assert kq.so_quy_tac == 151 and kq.so_bieu_thuc == 137
        assert kq.chay_duoc_truoc == kq.chay_duoc_sau
        assert "151 quy tắc" in kq.tom_tat()

    def test_van_moi_la_ca_file_da_ghep_va_nap_duoc(self):
        k = _khoi("STO-02").replace("severity: minor", "severity: major")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert kq.dat
        assert RuleSet(yaml.safe_load(kq.van_moi))["STO-02"].severity == "major"
        # Không đụng vào bất cứ dòng nào ngoài khối ấy.
        assert len(kq.van_moi.splitlines()) == len(VAN.splitlines())

    def test_tat_quy_tac_van_ap_duoc_nhung_PHAI_canh_bao(self):
        ma = _ma_chay_duoc()
        k = _khoi(ma).replace(f"  - id: {ma}\n", f"  - id: {ma}\n    enabled: false\n")
        kq = kiem_de_xuat(VAN, ma, k)
        assert kq.dat, "tắt một quy tắc là việc nghiệp vụ hợp lệ, không được chặn"
        assert any("enabled" in c for c in kq.canh_bao)
        assert any("KHÔNG còn đánh giá được" in c for c in kq.canh_bao)
        assert kq.chay_duoc_sau == kq.chay_duoc_truoc - 1

    def test_doi_severity_thi_canh_bao_vi_khong_bieu_thuc_nao_hong_de_bat(self):
        k = _khoi("STO-02").replace("severity: minor", "severity: critical")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert kq.dat and any("severity" in c for c in kq.canh_bao)


class TestDeXuatBiChan:
    def test_doi_ma_quy_tac_bi_chan(self):
        """`rule_ref` của 719 dòng baseline hồ sơ #1 trỏ vào mã cũ."""
        k = _khoi("STO-02").replace("- id: STO-02", "- id: STO-02b")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert not kq.dat and "id" in kq.loi[0] and "rule_ref" in kq.loi[0]

    def test_yaml_hong_bi_chan(self):
        kq = kiem_de_xuat(VAN, "STO-02", "  - id: STO-02\n    name: \"chua dong ngoac\n")
        assert not kq.dat and "YAML" in kq.loi[0]

    def test_hai_quy_tac_trong_mot_khoi_bi_chan(self):
        k = _khoi("STO-02") + _khoi("STO-03")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert not kq.dat and "ĐÚNG MỘT mục" in kq.loi[0]

    def test_bieu_thuc_sai_cu_phap_bi_chan(self):
        """`&&` là lỗi quen tay của người viết code C/Java. asteval chạy cú pháp
        Python, `&&` không phải toán tử — mà lỗi chỉ nổ ra lúc thẩm định thật."""
        k = _khoi("STO-01").replace("co_neu_iops and co_neu_latency",
                                    "co_neu_iops && co_neu_latency")
        kq = kiem_de_xuat(VAN, "STO-01", k)
        assert not kq.dat and "không phân tích được" in kq.loi[0]
        assert "STO-01.check" in kq.loi[0]

    def test_khoi_y_het_thi_bao_khong_co_gi_de_sua(self):
        kq = kiem_de_xuat(VAN, "STO-02", _khoi("STO-02"))
        assert not kq.dat and "y hệt" in kq.loi[0]

    def test_ma_khong_ton_tai(self):
        kq = kiem_de_xuat(VAN, "KHONG-CO", "  - id: KHONG-CO\n")
        assert not kq.dat and "không có quy tắc" in kq.loi[0]

    def test_see_also_tro_vao_ma_khong_co_that_bi_chan(self):
        k = _khoi("STO-02").replace("see_also: [STO-09, STO-14]",
                                    "see_also: [STO-99]")
        kq = kiem_de_xuat(VAN, "STO-02", k)
        assert not kq.dat and "không nạp được" in kq.loi[0]


def _van_nho(dau_a02: str = "  - id: A-02") -> str:
    return (
        'version: "test"\n'
        "rules:\n"
        '  - id: A-01\n    name: "a"\n    type: quantitative\n'
        '    applies_to_equipment: [tat_ca]\n    check: "x > 1"\n'
        f'{dau_a02}\n    name: "b"\n    type: quantitative\n'
        '    applies_to_equipment: [tat_ca]\n    check: "y > 2"\n'
        '  - id: A-03\n    name: "c"\n    type: quantitative\n'
        '    applies_to_equipment: [tat_ca]\n    check: "z > 3"\n')


class TestRanhGioiKhoi:
    def test_gach_dau_dong_dung_mot_minh_van_la_ranh_gioi(self):
        """`  -` rồi nội dung ở dòng sau là YAML hợp lệ. Nếu không nhận ra đây là mục
        mới thì khối của A-01 nuốt luôn A-02, và ghép lại là MẤT HẲN một quy tắc."""
        van = _van_nho("  -\n    id: A-02")
        assert [r.id for r in RuleSet(yaml.safe_load(van)).rules] == \
            ["A-01", "A-02", "A-03"]
        assert "A-02" not in doc_khoi(van, "A-01")
        assert ghep_khoi(van, "A-01", doc_khoi(van, "A-01")) == van

    def test_hai_dau_cach_sau_gach_van_la_ranh_gioi(self):
        van = _van_nho("  -  id: A-02")
        assert "A-02" not in doc_khoi(van, "A-01")

    def test_do_SAI_ranh_gioi_thi_luoi_chan_cuoi_bat_duoc(self, monkeypatch):
        """Lưới chắn cuối của `kiem_de_xuat`. Không đi qua đầu vào người dùng được —
        mọi ca đã biết đều bị chặn sớm hơn — nên ép ranh giới sai để chứng minh nó
        thật sự gác, phòng khi phần dò ranh giới đổi về sau."""
        from src.validators import de_xuat as dx
        van = _van_nho()
        # Ranh giới trùm luôn A-02: đúng hậu quả của một lỗi dò ranh giới.
        monkeypatch.setattr(dx, "pham_vi_khoi", lambda v, m: (2, 12))
        kq = dx.kiem_de_xuat(van, "A-01", '  - id: A-01\n    name: "a moi"\n'
                                          "    type: quantitative\n"
                                          "    applies_to_equipment: [tat_ca]\n")
        assert not kq.dat
        assert "danh sách quy tắc đổi" in kq.loi[0] and "A-02" in kq.loi[0]
