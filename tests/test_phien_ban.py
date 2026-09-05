"""Test ghép vòng nhận xét ↔ phiên bản `.docx`. Dựng thư mục hồ sơ giả, chạy offline.

Mỗi test dưới đây là **hồi quy cho một hồ sơ THẬT** đã làm hỏng một luật đơn giản
hơn — tên hồ sơ ghi trong docstring từng test. Xem `eval/phien_ban.py` để biết vì
sao không luật nào một mình đủ.
"""
import datetime
import pathlib

import pytest
from docx import Document

from eval.phien_ban import ghep_phien_ban, ho_cua, so_vong_theo_ho_so
from src.ingestion.filenames import is_pnx_doc


def _docx(thu_muc: pathlib.Path, ten: str, ngay: str | None) -> pathlib.Path:
    d = Document()
    d.add_paragraph("nội dung")
    if ngay:
        y, m, dd = (int(x) for x in ngay.split("-"))
        d.core_properties.modified = datetime.datetime(y, m, dd)
    p = thu_muc / ten
    p.parent.mkdir(parents=True, exist_ok=True)
    d.save(p)
    return p


@pytest.fixture
def ho_so(tmp_path):
    def _tao(ten_thu_muc: str, files: list[tuple[str, str | None]]) -> pathlib.Path:
        tm = tmp_path / ten_thu_muc
        tm.mkdir(parents=True, exist_ok=True)
        for ten, ngay in files:
            _docx(tm, ten, ngay)
        return tm
    return _tao


# --- ho_cua ----------------------------------------------------------------
def test_ho_bo_tien_to_ngay_ban_sao_va_hau_to_phien_ban():
    assert ho_cua("20240710_Sizing DataSec VTTv2.docx") == "sizing datasec vtt"
    assert ho_cua("Copy_Tài liệu vTag_v4.docx") == ho_cua("Tài liệu vTag.docx")
    # "…_v1.0v3" có hai lớp hậu tố phiên bản chồng nhau — ca thật ở GSCG.
    assert ho_cua("PL01_Sizing_GSCG_v1.0v3.docx") == ho_cua("PL01_Sizing_GSCG.docx")


def test_nhan_dien_pnx_khong_lay_phan_hoi_va_cong_van():
    assert is_pnx_doc("PNX_hethongVtag_v2.docx")
    assert not is_pnx_doc("16102023_Phản hồi PNX Sizing server VTAG.docx")
    assert not is_pnx_doc("Cong van lay PNX sizing CALLBASE.docx")
    assert not is_pnx_doc("Sizing_PBH_4.docx")


# --- ba ca hỏng thật, mỗi ca một luật -------------------------------------
def test_hai_ban_doi_ten_van_ghep_dung_tung_vong(ho_so):
    """`cap moi Data Security VTT`: hai bản cùng tài liệu, tên khác nhau nhiều.

    Cách cũ (theo bảng chữ cái) lấy `20240710_…v2` cho MỌI nhãn, tức chấm 21 nhãn
    vòng 1 trên bản đã sửa.
    """
    tm = ho_so("cap moi Data Security VTT 18476", [
        ("Sizing tài nguyên Data Security VTT.docx", "2024-06-03"),
        ("20240710_Sizing DataSec VTTv2.docx", "2024-07-11"),
        ("PNX_Data Security VTT.docx", "2024-06-07"),
        ("PNX_Data Security VTTv2.docx", "2024-07-18"),
    ])
    kq = ghep_phien_ban(tm, so_vong=2)
    assert kq.theo_vong[1].ten == "Sizing tài nguyên Data Security VTT.docx"
    assert kq.theo_vong[2].ten == "20240710_Sizing DataSec VTTv2.docx"
    # Hai tên khác nhau nhiều nên module vẫn phải nói ra là nó KHÔNG chắc chúng là
    # hai phiên bản của một tài liệu — ghép đúng nhưng độ tin không phải "cao".
    assert kq.do_tin == "vua"
    assert any("tên tài liệu khác nhau" in c for c in kq.canh_bao)


def test_tai_lieu_cua_he_thong_khac_lac_vao_thu_muc_bi_loai(ho_so):
    """`cap moi PNM 57012`: thư mục chứa 2 bản sizing của hệ thống callbot.

    Luật "lấy bản cũ nhất theo ngày" sẽ vớ đúng file callbot — tệ hơn cách cũ.
    """
    tm = ho_so("cap moi PNM 57012", [
        ("PL02_Sizing_callbot inbound CSKH_bosung2022_v1.1.docx", "2024-12-11"),
        ("PL02_Sizing_PNM_v1.docx", "2025-10-29"),
        ("PL02_Sizing_PNM_v1.2.docx", "2025-11-03"),
        ("PNX_PHONE NUMBER MASKING.docx", "2025-10-31"),
    ])
    kq = ghep_phien_ban(tm, so_vong=1)
    assert kq.theo_vong[1].ten == "PL02_Sizing_PNM_v1.docx"
    assert any("callbot" in b.ten for b in kq.bo_ngoai)


def test_ban_sua_sau_vong_tham_dinh_cuoi_bi_loai(ho_so):
    """`cap moi FMRA…`: bản `…Training_2025…` (20/11) sửa SAU PNX duy nhất (19/11)."""
    tm = ho_so("cap moi FMRA_Sizing_server_Backup_2024 58352", [
        ("FMRA_Sizing_server_Backup_2024_Final_New.docx", "2025-11-18"),
        ("FMRA_Sizing_server_Backup_2024_Final_New_v2.docx", "2025-11-20"),
        ("PNX_FMRA_Sizing_server_Backup_2024.docx", "2025-11-19"),
    ])
    kq = ghep_phien_ban(tm, so_vong=1)
    assert kq.theo_vong[1].ten == "FMRA_Sizing_server_Backup_2024_Final_New.docx"
    assert any("sửa SAU vòng thẩm định cuối" in c for c in kq.canh_bao)


def test_pnx_tich_luy_nhieu_vong_khong_duoc_keo_vong1_sang_ban_muon(ho_so):
    """`cap bo sung VTracking 2.0.1`: PNX vòng 1 được lưu SAU cả hai bản sizing.

    Đây là lý do ngày PNX chỉ được dùng làm TRẦN, không dùng để đánh số vòng.
    """
    tm = ho_so("cap bo sung VTracking 2.0.1 14716", [
        ("Thiet ke va dinh co he thong_VTracking 2.0.1.docx", "2024-04-11"),
        ("Thiet ke va dinh co he thong_VTracking 2.0.1_v2.docx", "2024-04-22"),
        ("PNX_vTracking 2.0_v1.docx", "2024-04-25"),
        ("PNX_vTracking 2.0_v2.docx", "2024-05-06"),
    ])
    kq = ghep_phien_ban(tm, so_vong=2)
    assert kq.theo_vong[1].ten == "Thiet ke va dinh co he thong_VTracking 2.0.1.docx"
    assert kq.theo_vong[2].ten.endswith("_v2.docx")


# --- xuống cấp có kiểm soát ------------------------------------------------
def test_it_ban_hon_so_vong_thi_canh_bao_va_ha_do_tin(ho_so):
    tm = ho_so("cap moi Mybox 38327", [
        ("PL07_Sizing_Mybox.docx", "2025-03-26"),
        ("PNX_PL07_Sizing_Mybox.docx", "2025-03-28"),
    ])
    kq = ghep_phien_ban(tm, so_vong=2)
    assert kq.theo_vong[1] is kq.theo_vong[2]
    assert kq.do_tin == "thap"
    assert any("chỉ ghép được 1 bản" in c for c in kq.canh_bao)


def test_khong_co_docx_thi_noi_ro_chu_khong_no(ho_so):
    tm = ho_so("hồ sơ rỗng", [])
    kq = ghep_phien_ban(tm, so_vong=1)
    assert kq.ban_vong1 is None
    assert kq.cach_ghep == "khong_ghep_duoc"
    assert kq.canh_bao


def test_ban_khong_doc_duoc_ngay_bi_xep_cuoi_khong_lam_ban_vong1():
    """NT4: không có bằng chứng thời gian thì KHÔNG được coi là bản sớm nhất."""
    from eval.phien_ban import Ban
    khong_ngay = Ban(duong_dan="a", ten="Sizing A.docx", sua_cuoi="")
    co_ngay = Ban(duong_dan="b", ten="Sizing B.docx", sua_cuoi="2025-01-05T00:00:00")
    assert sorted([khong_ngay, co_ngay], key=lambda b: b.khoa_sap_xep)[0] is co_ngay


def test_khong_co_pnx_thi_ha_do_tin_va_noi_ro(ho_so):
    tm = ho_so("cap moi ARVR", [("Sizing ARVR.docx", "2025-01-01")])
    kq = ghep_phien_ban(tm, so_vong=1)
    assert kq.cach_ghep == "tu_khoa"
    assert kq.do_tin == "thap"
    assert any("không có file PNX" in c for c in kq.canh_bao)


def test_so_vong_suy_tu_nhan():
    nhan = [{"dossier": "A", "lan_nhan_xet": 1}, {"dossier": "A", "lan_nhan_xet": 3},
            {"dossier": "B", "lan_nhan_xet": 2}, {"dossier": "C"}]
    assert so_vong_theo_ho_so(nhan) == {"A": 3, "B": 2, "C": 1}
