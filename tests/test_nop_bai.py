"""`--giong-nhu` — chép nguyên tuỳ chọn của một lượt đã nộp. OFFLINE.

Phép đo 5.0b chỉ có nghĩa khi hai lượt chạy cùng bộ lọc. Chép tay `--nhom` /
`--vong` / `--song-song` từ một lượt nộp qua giao diện là chỗ sai mà không có gì
báo: tập finding khác nhau vì bộ lọc khác nhau, còn người đọc lại kết luận model
không ổn định.
"""
import argparse
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.nop_bai import _ap_tuy_chon_cua      # noqa: E402
from src.khach_api import LoiAPI                   # noqa: E402


class KhachGia:
    def __init__(self, viec_tra=None, no=None):
        self._viec, self._no = viec_tra, no

    def viec(self, ma):
        if self._no:
            raise self._no
        return self._viec


def _a(**kw):
    d = {"docx": "Sizing ABC.docx", "nhom": "", "vong": None,
         "song_song": None, "giong_nhu": "abc123"}
    d.update(kw)
    return argparse.Namespace(**d)


def _viec(tuy_chon, ten="Sizing ABC.docx"):
    return {"ten_file": ten, "tuy_chon": tuy_chon}


def test_chep_dung_ca_ba_tuy_chon():
    a = _a()
    assert _ap_tuy_chon_cua(KhachGia(_viec(
        {"chi_nhom": ["KPI", "CPU"], "chi_vong": 2, "song_song": 12})), a)
    assert (a.nhom, a.vong, a.song_song) == ("KPI,CPU", 2, 12)


def test_luot_goc_khong_loc_gi_thi_luot_sau_cung_khong_loc():
    a = _a()
    assert _ap_tuy_chon_cua(KhachGia(_viec({})), a)
    assert (a.nhom, a.vong, a.song_song) == ("", None, None)


@pytest.mark.parametrize("tay", [{"nhom": "KPI"}, {"vong": 1}, {"song_song": 6}])
def test_tu_choi_khi_vua_giong_nhu_vua_dat_tay(tay, capsys):
    """Im lặng chọn một bên là cách chắc nhất để phép đo sai mà không ai biết."""
    assert _ap_tuy_chon_cua(KhachGia(_viec({})), _a(**tay)) is False
    assert "bỏ bớt một bên" in capsys.readouterr().out


def test_khong_tra_duoc_viec_goc_thi_DUNG_chu_khong_chay_bua():
    """Chạy tiếp với tuỳ chọn mặc định là đốt 16 phút cho một lượt không so được."""
    assert _ap_tuy_chon_cua(
        KhachGia(no=LoiAPI("không có việc này", 404)), _a()) is False


def test_canh_bao_khi_nop_NHAM_tai_lieu_khac(capsys):
    a = _a(docx=r"D:\ho so\Sizing KHAC.docx")
    assert _ap_tuy_chon_cua(KhachGia(_viec({"chi_vong": 1})), a)
    ra = capsys.readouterr().out
    assert "TÊN FILE KHÁC" in ra and "5.0b" in ra


def test_duong_dan_day_du_van_khop_theo_TEN_FILE(capsys):
    """Lượt A nộp qua giao diện chỉ lưu tên file, không lưu đường dẫn máy người
    dùng — so cả đường dẫn thì cảnh báo giả mỗi lần."""
    a = _a(docx=r"D:\ho so\2026\Sizing ABC.docx")
    assert _ap_tuy_chon_cua(KhachGia(_viec({})), a)
    assert "TÊN FILE KHÁC" not in capsys.readouterr().out
