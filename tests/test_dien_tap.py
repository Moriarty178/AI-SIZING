"""Diễn tập lượt B1 — chạy TRỌN đường thật trên hồ sơ THẬT bằng model giả.

Đây là test đắt nhất trong bộ (vài giây) và cũng là test đáng nhất: nó đi đúng
con đường sẽ chạy 1,1 giờ trong mạng nội bộ — `C1 → C3 → C4 → C5 → C7 → đối chiếu
nhãn → ghi báo cáo`, kèm điểm dừng và ghép phiên bản.

Lý do tồn tại, bằng hai lỗi nó đã bắt được ngay lần chạy đầu (2026-09-05):

1. `--tiep-tuc` **sập ngay lập tức** (`UnboundLocalError: canh_bao`). Không có
   diễn tập thì lỗi này chỉ lộ vào đúng lúc tệ nhất: sau khi một lượt chạy 1 giờ
   đứt và người dùng muốn chạy tiếp.
2. C7 xếp finding theo `id` nên vứt mất thứ tự ưu tiên của C2 (bắt ở lượt kiểm
   cùng ngày, xem `tests/test_canh_bao_anh.py`).

Cả hai đều là lỗi CHỖ CÁC THÀNH PHẦN GẶP NHAU — không unit test nào bắt được.
"""
import pathlib
import sys

import pytest

from eval import run_eval
from eval.gia_lap import ClientGiaLap
from src.validators.qualitative import NhanXetDinhTinh

HO_SO_MAU = "PBH 4.0"        # 2 phiên bản, 30 nhãn, chạy ~2 giây với model giả
GOC = pathlib.Path(run_eval.GOC_HO_SO)

pytestmark = pytest.mark.skipif(
    not GOC.exists(), reason="không có kho hồ sơ thật trong bản checkout này")


@pytest.fixture
def chay_dien_tap(tmp_path, monkeypatch):
    """Chạy `run_eval.main()` thật, chỉ đổi nơi ghi báo cáo và điểm dừng."""
    monkeypatch.setattr(run_eval, "THU_MUC_BAO_CAO", tmp_path / "reports")
    monkeypatch.setattr(run_eval, "THU_MUC_DIEM_DUNG", tmp_path / "diem_dung")
    (tmp_path / "reports").mkdir()

    def _chay(*args: str) -> tuple[int, list[pathlib.Path]]:
        monkeypatch.setattr(sys, "argv", ["run_eval", *args])
        ma = run_eval.main()
        return ma, sorted((tmp_path / "reports").glob("*.md"))
    return _chay


# --- đường chạy chính ------------------------------------------------------
def test_dien_tap_di_tron_duong_that_va_ghi_bao_cao(chay_dien_tap):
    ma, bc = chay_dien_tap("--gia-lap", "--ho-so", HO_SO_MAU, "--song-song", "4")
    assert ma == 0
    assert len(bc) == 1 and bc[0].name.startswith("dien-tap-")
    noi_dung = bc[0].read_text(encoding="utf-8")
    assert "MODEL GIẢ" in noi_dung and "VÔ NGHĨA" in noi_dung
    # Có finding thật, tức C4/C5 đã chạy chứ không im lặng bỏ qua.
    assert "Theo hồ sơ" in noi_dung and HO_SO_MAU.split()[0] in noi_dung


def test_bao_cao_dien_tap_KHONG_duoc_lan_voi_bao_cao_that(chay_dien_tap):
    """Tên file khác hẳn, và trong ruột có dấu đóng. Một con số diễn tập bị trích
    ra như kết quả thật là kiểu sai không ai lần lại được."""
    _, bc = chay_dien_tap("--gia-lap", "--ho-so", HO_SO_MAU, "--song-song", "4")
    assert not bc[0].name.startswith("eval-")


def test_tu_choi_dien_tap_tren_tap_TEST_giu_kin(chay_dien_tap):
    ma, bc = chay_dien_tap("--gia-lap", "--tap", "test", "--toi-hieu-rui-ro")
    assert ma == 2 and bc == []


# --- chịu được lượt gọi hỏng ----------------------------------------------
def test_bom_loi_khong_keo_sap_ca_luot_chay(chay_dien_tap):
    """30% lượt gọi hỏng (rỗng + sai lược đồ) vẫn phải ra báo cáo. Đây là hai chế
    độ hỏng ĐÃ GẶP THẬT ở lượt chạy 2026-09-04."""
    ma, bc = chay_dien_tap("--gia-lap", "--bom-loi", "0.3",
                           "--ho-so", HO_SO_MAU, "--song-song", "4")
    assert ma == 0 and len(bc) == 1


# --- điểm dừng -------------------------------------------------------------
def test_chay_tiep_lay_lai_ho_so_da_xong_khong_goi_lai(chay_dien_tap):
    """Hồi quy cho lỗi `UnboundLocalError: canh_bao` — `--tiep-tuc` từng sập ngay."""
    ma1, _ = chay_dien_tap("--gia-lap", "--ho-so", HO_SO_MAU, "--song-song", "4")
    ma2, bc = chay_dien_tap("--gia-lap", "--ho-so", HO_SO_MAU, "--song-song", "4",
                            "--tiep-tuc")
    assert ma1 == 0 and ma2 == 0
    assert "tiếp tục từ điểm dừng" in bc[-1].read_text(encoding="utf-8")


def test_diem_dung_cua_dien_tap_KHONG_dung_lai_cho_luot_chay_that():
    """Chữ ký có `gia_lap`, nên số của model giả không thể lẫn vào lượt chạy thật."""
    import argparse

    def _a(**kw):
        m = dict(tap="dev", model="", chi_vong=0, moi_phien_ban=False, gia_lap=False)
        m.update(kw)
        return argparse.Namespace(**m)
    assert run_eval._chu_ky(_a(gia_lap=True), None, None) != \
           run_eval._chu_ky(_a(gia_lap=False), None, None)


# --- model giả phải bám lược đồ THẬT ---------------------------------------
def test_sinh_duoc_luoc_do_that_cua_C5():
    """Nếu `NhanXetDinhTinh` thêm trường mà bộ sinh không dựng nổi, diễn tập phải
    đỏ ngay — chứ không phải im lặng bỏ qua nhánh đó."""
    c = ClientGiaLap(seed=1, ty_le_trich_dan_bia=0.0)
    tin = [{"role": "user", "content":
            "Hệ thống dùng 3 node Kafka, mỗi node 16 vCPU và 32 GB RAM."}]
    nx = c.extract(NhanXetDinhTinh, tin)
    assert nx.ket_luan in ("dat", "khong_dat", "khong_xac_dinh")
    # Trích dẫn phải là câu CÓ THẬT trong thông điệp, nếu không C5 loại hết và
    # diễn tập chỉ đi được nhánh "bị loại".
    assert nx.trich_dan_tai_lieu and nx.trich_dan_tai_lieu in tin[0]["content"]


def test_sinh_duoc_luoc_do_dong_cua_C3_va_chon_dung_nhan_dong():
    from typing import Literal

    from pydantic import BaseModel, Field, create_model

    LD = create_model(
        "GanBangThu",
        dong=(str, Field(description="Chép NGUYÊN VĂN ô đầu: «Kafka» / «Postgres»")),
        cot_1=(Literal["so_cpu", "dung_luong", "khong_ro"], Field(description="?")),
    )
    assert issubclass(LD, BaseModel)
    out = ClientGiaLap(seed=3).extract(LD, [{"role": "user", "content": "x"}])
    assert out.dong in ("Kafka", "Postgres")        # nhãn dòng CÓ THẬT
    assert out.cot_1 in ("so_cpu", "dung_luong", "khong_ro")


def test_bom_loi_dung_hai_che_do_hong_that():
    c = ClientGiaLap(seed=5, ty_le_rong=1.0)
    with pytest.raises(Exception, match="rỗng"):
        c.extract(NhanXetDinhTinh, [{"role": "user", "content": "x"}])
    assert c.tk.bom_rong == 1
