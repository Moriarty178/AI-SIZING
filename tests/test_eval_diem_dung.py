"""Test điểm dừng của `run_eval` (2.11). Chạy offline.

Lượt đo recall kéo 1–2,4 giờ ở mạng nội bộ (~40 giây mỗi lời gọi). Trước đây bị
ngắt giữa chừng là mất sạch: kết quả các hồ sơ đã xong nằm trong RAM và không ai
thấy lại được.
"""
import argparse
import json

import pytest

from eval.run_eval import (_chu_ky, duong_dan_diem_dung, ghi_diem_dung,
                           nap_diem_dung)
from src.reporting.finding import Finding


@pytest.fixture(autouse=True)
def thu_muc_tam(tmp_path, monkeypatch):
    monkeypatch.setattr("eval.run_eval.THU_MUC_DIEM_DUNG", tmp_path / "eval")
    return tmp_path


def _args(**kw):
    m = dict(tap="dev", model="", chi_vong=0, moi_phien_ban=False)
    m.update(kw)
    return argparse.Namespace(**m)


def test_ghi_roi_nap_lai_duoc():
    ck = _chu_ky(_args(), None, None)
    ghi_diem_dung("dev", ck, {"hồ sơ A": {"findings": [], "da_dung": "x.docx"}})
    ho_so, ghi_chu = nap_diem_dung("dev", ck)
    assert list(ho_so) == ["hồ sơ A"]
    assert any("tiếp tục từ điểm dừng" in g for g in ghi_chu)


def test_chu_ky_lech_thi_BO_diem_dung_chu_khong_tron_ket_qua():
    """Trộn kết quả của hai lượt chạy khác bộ lọc cho ra một con số recall không ai
    lần lại được là gì — thà chạy lại từ đầu."""
    ghi_diem_dung("dev", _chu_ky(_args(), ["KPI"], None), {"A": {"findings": []}})
    ho_so, ghi_chu = nap_diem_dung("dev", _chu_ky(_args(), None, None))
    assert ho_so == {}
    assert any("khác bộ lọc" in g for g in ghi_chu)


@pytest.mark.parametrize("doi", [
    {"model": "claude-opus-4-6"},
    {"chi_vong": 1},
    {"moi_phien_ban": True},
    {"tap": "test"},
])
def test_moi_thu_doi_duoc_ket_qua_deu_nam_trong_chu_ky(doi):
    goc = _chu_ky(_args(), None, None)
    assert _chu_ky(_args(**doi), None, None) != goc


def test_diem_dung_hong_thi_bo_qua_chu_khong_no():
    ck = _chu_ky(_args(), None, None)
    p = duong_dan_diem_dung("dev")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{ khong phai json", encoding="utf-8")
    ho_so, ghi_chu = nap_diem_dung("dev", ck)
    assert ho_so == {} and any("hỏng" in g for g in ghi_chu)


def test_khong_co_diem_dung_thi_im_lang_chay_tu_dau():
    ho_so, ghi_chu = nap_diem_dung("dev", _chu_ky(_args(), None, None))
    assert ho_so == {} and ghi_chu == []


def test_finding_di_qua_diem_dung_khong_mat_truong_nao():
    """Điểm dừng chỉ dùng được nếu `Finding` đi ra rồi vào lại vẹn nguyên — nhất là
    `rule_ref` (khoá so khớp nhãn) và `vong` (luật chặn Vòng 2)."""
    f = Finding(id="KPI-02#App", severity="major", category="vuot_nguong",
                finding="CPU vượt ngưỡng", rule_ref="KPI-02", vong=2,
                checklist_ref=["CL-3.1.5"], scope_key="App",
                computed_evidence="0.92 > 0.8", confidence="cao")
    lai = Finding(**json.loads(json.dumps(f.as_dict(), ensure_ascii=False)))
    assert lai == f
    assert lai.rule_ref == "KPI-02" and lai.vong == 2


def test_ghi_de_diem_dung_khong_de_lai_file_tam():
    ck = _chu_ky(_args(), None, None)
    ghi_diem_dung("dev", ck, {"A": {"findings": []}})
    ghi_diem_dung("dev", ck, {"A": {"findings": []}, "B": {"findings": []}})
    p = duong_dan_diem_dung("dev")
    assert list(p.parent.glob("*.tmp")) == []
    assert len(json.loads(p.read_text(encoding="utf-8"))["ho_so"]) == 2
