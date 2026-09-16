"""5.1 — khoá baseline + đối chiếu. OFFLINE, thuần Python.

Dùng id THẬT từ phép đo 5.0b (`docs/do-on-dinh-20260916-180655.json`) ở những chỗ
quyết định thiết kế đứng trên chúng.
"""
from src.luu_tru.baseline import (dong_finding, doi_chieu, gan_khoa, ket_luan_boi,
                                  ket_qua_lan_dau, scope_goc, trang_thai_khi_con)


def _f(fid, **kw):
    d = {"id": fid, "severity": "major", "category": "vuot_nguong",
         "finding": "mô tả", "computed_evidence": "", "location": "Mục I",
         "nhom": "vong2_chua_dat", "rule_ref": fid.split("#")[0]}
    d.update(kw)
    return d


def _khoa(*ids):
    return [k for k, _ in gan_khoa([_f(i) for i in ids])]


class TestGanKhoa:
    def test_ten_phan_he_dien_giai_lai_van_cung_khoa(self):
        """50/59 dòng lệch ở 5.0b là đúng dạng này."""
        assert _khoa("ARC-02#Master (K8s Master node)") == \
            _khoa("ARC-02#Master (K8s Control plane)")

    def test_KHONG_gop_Primary_voi_Replica_trong_cung_mot_lan(self):
        """Hai phân hệ THẬT chỉ khác phần trong ngoặc. Gộp là để lỗi bên này che
        lỗi bên kia."""
        k = _khoa("STO-17#DB (Primary)", "STO-17#DB (Replica)")
        assert len(set(k)) == 2
        assert k == ["STO-17#DB (Primary)", "STO-17#DB (Replica)"]

    def test_chan_gop_chi_ap_dung_cho_khoa_bi_trung(self):
        k = _khoa("STO-17#DB (Primary)", "STO-17#DB (Replica)",
                  "ARC-02#Master (K8s Master node)")
        assert k[2] == "ARC-02#master"

    def test_hau_to_khu_trung_giu_nguyen(self):
        assert _khoa("KPI-02#PH1 (x)", "KPI-02#PH1 (x)#2") == ["KPI-02#ph1", "KPI-02#ph1#2"]

    def test_ten_phan_he_ket_thuc_bang_so_KHONG_bi_cat(self):
        assert _khoa("KPI-02#PH2") == ["KPI-02#ph2"]

    def test_id_khong_co_phan_he_giu_nguyen(self):
        assert _khoa("NT4-C1", "LBA-01-hsdp-a") == ["NT4-C1", "LBA-01-hsdp-a"]

    def test_khoa_luon_duy_nhat_ke_ca_id_trung_that(self):
        """UNIQUE(ho_so_id, khoa) trong CSDL sẽ làm hỏng CẢ baseline vì một dòng."""
        k = _khoa("A#x", "A#x", "A#x")
        assert len(set(k)) == 3

    def test_tat_dinh_khong_phu_thuoc_thu_tu(self):
        ids = ["STO-17#DB (Primary)", "ARC-02#Master (a)", "STO-17#DB (Replica)"]
        assert dict(zip(ids, _khoa(*ids))) == \
            dict(zip(ids[::-1], _khoa(*ids[::-1])))

    def test_hien_thi_dung_ten_goc(self):
        assert scope_goc(_f("ARC-02#Master (K8s Master node)#2")) == \
            "Master (K8s Master node)"


class TestTrangThai:
    def test_con_va_chua_kiem_duoc(self):
        assert trang_thai_khi_con(_f("A#x", nhom="vong2_chua_kiem")) == "chua_kiem_duoc"
        assert trang_thai_khi_con(_f("A#x", nhom="vong2_tam_hoan")) == "chua_kiem_duoc"
        assert trang_thai_khi_con(
            _f("NT4-C1", nhom="khac", category="khong_kiem_chung_duoc")) == "chua_kiem_duoc"
        assert trang_thai_khi_con(_f("A#x")) == "chua_dat"

    def test_ai_ket_luan(self):
        assert ket_luan_boi(_f("CPU-01#Kafka", computed_evidence="95% > 80%")) == "c4"
        assert ket_luan_boi(_f("ARC-02#x")) == "c5"
        assert ket_luan_boi(_f("A#x", nhom="vong2_chua_kiem")) == "khong_ro"

    def test_canh_bao_NT4_co_so_dem_KHONG_phai_C4(self):
        """`NT4-TRANG` mang `computed_evidence` là số phần tử — không phải một quy
        tắc C4 kết luận đạt/chưa đạt."""
        f = _f("NT4-TRANG", computed_evidence="264 phần tử", nhom="khac",
               category="khong_kiem_chung_duoc")
        assert ket_luan_boi(f) == "khong_ro"


class TestDoiChieu:
    def _baseline(self, *ids, muc_do="major"):
        return [{"id": i + 1, "khoa": k, "muc_do": muc_do}
                for i, (k, _) in enumerate(gan_khoa([_f(x) for x in ids]))]

    def test_khong_doi_gi_thi_khong_dat_khong_phat_sinh(self):
        b = self._baseline("A#x", "B#y")
        dc = doi_chieu(b, [_f("A#x"), _f("B#y")])
        assert dc.dem() == {"dat": 0, "chua_dat": 2, "chua_kiem_duoc": 0, "phat_sinh": 0}

    def test_bien_mat_la_dat(self):
        """Luật 5.3 người dùng chốt 2026-09-16."""
        dc = doi_chieu(self._baseline("A#x", "B#y"), [_f("A#x")])
        assert dc.dem()["dat"] == 1
        assert dc.ket_qua[2]["trang_thai"] == "dat"

    def test_loi_moi_vao_ro_phat_sinh_KHONG_vao_baseline(self):
        dc = doi_chieu(self._baseline("A#x"), [_f("A#x"), _f("C#z")])
        assert len(dc.ket_qua) == 1, "baseline KHÔNG thêm dòng"
        assert [p["khoa"] for p in dc.phat_sinh] == ["C#z"]

    def test_doi_ten_phan_he_KHONG_thanh_da_sua_va_phat_sinh(self):
        """Đúng ca 5.0b: không có chuẩn hoá thì 50 dòng thành «đã sửa» + 50 dòng
        «phát sinh» dù không ai sửa gì."""
        dc = doi_chieu(self._baseline("ARC-02#Master (K8s Master node)"),
                       [_f("ARC-02#Master (K8s Control plane)")])
        assert dc.dem() == {"dat": 0, "chua_dat": 1, "chua_kiem_duoc": 0, "phat_sinh": 0}

    def test_muc_do_dong_bang_chi_ghi_chu_khi_khac(self):
        b = self._baseline("A#x", "B#y", muc_do="major")
        dc = doi_chieu(b, [_f("A#x", severity="major"), _f("B#y", severity="minor")])
        assert dc.ket_qua[1]["muc_do_lan"] is None
        assert dc.ket_qua[2]["muc_do_lan"] == "minor"

    def test_con_so_code_tinh_cua_lan_nay_duoc_giu(self):
        """5.0b: `CPU-01#Kafka` ra con số khác giữa hai lượt. Bảng 5.6 phải thấy."""
        dc = doi_chieu(self._baseline("CPU-01#Kafka"),
                       [_f("CPU-01#Kafka", computed_evidence="92%")])
        assert dc.ket_qua[1]["computed_evidence"] == "92%"
        assert dc.ket_qua[1]["ket_luan_boi"] == "c4"


def test_lan_dau_moi_dong_deu_con_khong_phat_sinh():
    kf = gan_khoa([_f("A#x"), _f("B#y", nhom="vong2_chua_kiem")])
    dc = ket_qua_lan_dau(kf, {k: i for i, (k, _) in enumerate(kf, 1)})
    assert dc.dem() == {"dat": 0, "chua_dat": 1, "chua_kiem_duoc": 1, "phat_sinh": 0}


def test_dong_finding_cat_dung_do_dai_cot():
    """Cột `rule_ref` là String(40): một id dài bất thường không được làm hỏng
    cả giao dịch ghi baseline."""
    d = dong_finding("k", _f("X" * 500 + "#y", rule_ref="R" * 100))
    assert len(d["rule_ref"]) == 40 and len(d["finding_id_goc"]) == 400
