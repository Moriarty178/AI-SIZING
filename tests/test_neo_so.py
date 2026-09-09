"""Test C2/2.5 — neo số đọc từ ảnh vào bảng khai báo. Chạy OFFLINE, không cần model.

Mọi dữ liệu ở đây lấy NGUYÊN VĂN từ hai lượt chạy vision thật ngày 2026-09-08
(`eval/reports/doc-anh-*.json`) và từ bảng trong chính hai file `.docx` tương ứng.
Không có ca bịa: mỗi ca đều là một thứ đã xảy ra thật.
"""
import pytest
from docx import Document

from src.ingestion.docx_reader import read_docx
from src.vision.doc_anh import KetQuaDocAnh, SoDaDoc
from src.vision.neo_so import (OKhaiBao, gia_tri_chuan, loai_dai_luong,
                               neo_mot_anh, neo_tai_lieu, thanh_finding,
                               thu_thap_khai_bao, ung_vien_gia_tri)


def so(nhan, raw, don_vi="", trich_dan=""):
    return SoDaDoc(nhan=nhan, raw=raw, gia_tri=None, don_vi=don_vi,
                   trich_dan=trich_dan or raw)


def anh(ma, location, so_lieu, loai="console"):
    return KetQuaDocAnh(ma_anh=ma, loai=loai, location=location,
                        doc_duoc=True, so_lieu=so_lieu)


# ---------------------------------------------------------------- đại lượng --
class TestLoaiDaiLuong:
    def test_millicore_va_megabyte_khong_bi_gop(self):
        """`1403m` và `10393Mi` nằm CÙNG một dòng `kubectl top nodes` của Vtag.

        Phân biệt HOA/thường là thứ duy nhất tách được chúng.
        """
        assert loai_dai_luong("1403m") == "milli_core"
        assert loai_dai_luong("10393Mi") == "byte"
        assert loai_dai_luong("504M") == "byte"       # `du -h` của Vtag anh#80

    def test_phan_tram_ca_khi_dau_nam_o_don_vi(self):
        """PBH `top` trả raw="31.2" với don_vi="%" — dấu % KHÔNG ở trong raw.

        Lượt dò đầu tiên bỏ sót đúng con số quan trọng nhất của cả hồ sơ vì chỉ
        tìm dấu % trong `raw`.
        """
        assert loai_dai_luong("31.2", "%") == "phan_tram"
        assert gia_tri_chuan("31.2", "%") == pytest.approx(31.2)
        assert loai_dai_luong("59%") == "phan_tram"

    def test_byte_qua_don_vi_rieng(self):
        """PBH `top`: raw="128010.0", don_vi="MiB"."""
        assert loai_dai_luong("128010.0", "MiB") == "byte"
        assert gia_tri_chuan("128010.0", "MiB") == 128010.0 * 1024**2

    def test_chuoi_khong_phai_gia_tri_thi_khong_xep_loai(self):
        assert loai_dai_luong("AMD Ryzen 9 7950X 16-Core Processor") is None
        assert loai_dai_luong("48 bits physical, 48 bits virtual") is None

    def test_tach_phan_tram_khi_raw_gom_ca_dong(self):
        """`df -h` của Vtag trả cả dòng vào `raw`; trong đó có đúng một dấu %."""
        raw = "983G  586G  335G  63%"
        assert loai_dai_luong(raw) is None
        assert ung_vien_gia_tri(raw) == ("phan_tram", 63.0)
        assert ung_vien_gia_tri(raw, tach_phan_tram=False) is None

    def test_hai_dau_phan_tram_thi_tu_choi(self):
        """Hai dấu % ⇒ không biết cái nào đang được nói tới ⇒ NT4: không đoán."""
        assert ung_vien_gia_tri("59%  4%") is None


# ------------------------------------------------------------- phía khai báo --
def _docx_khai_bao(tmp_path, rows, ten="t.docx"):
    d = Document()
    t = d.add_table(rows=len(rows), cols=len(rows[0]))
    for i, r in enumerate(rows):
        for j, c in enumerate(r):
            t.cell(i, j).text = c
    p = tmp_path / ten
    d.save(str(p))
    return read_docx(str(p))


class TestThuThapKhaiBao:
    def test_nhan_dong_bo_qua_so_thu_tu(self):
        """Bảng PBH tr.9 mở đầu bằng STT «1», nhãn thật là «Test» ở ô kế."""
        doc = _docx_khai_bao(pytest.importorskip("pathlib") and _tmp(), [
            ["STT", "Server", "Tải CPU"],
            ["1", "Test", "31.2%"],
        ])
        kb = [o for o in thu_thap_khai_bao(doc) if o.loai == "phan_tram"]
        assert [o.gia_tri for o in kb] == [31.2]
        assert kb[0].nhan_dong == "Test"

    def test_dai_cua_bang_xep_chong(self):
        """Vtag nhét RAM và DISK vào cùng một bảng Word, cách nhau bằng dòng nhãn.

        Không nhận ra dải thì ô «Postgres · DISK · 63%» bị chú thích thành một cột
        CPU — chứng cứ NT2 mô tả sai chính nó.
        """
        doc = _docx_khai_bao(_tmp(), [
            ["", "Số cores", "% Tiêu thụ"],
            ["Postgres", "8", "16%"],
            ["DISK", "DISK", "DISK"],
            ["", "Tổng dung lượng (GB)", "% Tiêu thụ"],
            ["Postgres", "1000", "63%"],
        ])
        kb = {o.gia_tri: o for o in thu_thap_khai_bao(doc) if o.loai == "phan_tram"}
        assert kb[16.0].bang_con == ""
        assert kb[63.0].bang_con == "DISK"
        assert kb[63.0].nhan_dong == "Postgres"

    def test_khong_noi_ve_cot_khi_khong_kiem_duoc_thang_hang(self):
        """Bảng có ô gộp: tiêu đề 3 ô, dữ liệu 4 ô ⇒ chỉ số cột không trỏ cùng chỗ."""
        doc = _docx_khai_bao(_tmp(), [
            ["", "Số cores", "% Tiêu thụ", ""],
            ["Worker", "Tổng", "8", "20%"],
        ])
        kb = [o for o in thu_thap_khai_bao(doc) if o.gia_tri == 20.0]
        assert kb and kb[0].nhan_dong == "Worker"
        # cùng độ dài nên vẫn nói được về cột; điều cần bảo đảm là không bịa
        assert kb[0].tieu_de_cot in ("", "% Tiêu thụ", "Số cores")


def _tmp():
    import pathlib
    import tempfile
    return pathlib.Path(tempfile.mkdtemp())


# ---------------------------------------------------------------------- neo --
KB_VTAG = [
    OKhaiBao(gia_tri=59.0, loai="phan_tram", raw="59%", page=9,
             location="Mục 1, trang 9", nhan_dong="Master", tieu_de_cot="RAM"),
    OKhaiBao(gia_tri=66.0, loai="phan_tram", raw="66%", page=9,
             location="Mục 1, trang 9", nhan_dong="Worker", tieu_de_cot="RAM"),
    OKhaiBao(gia_tri=20.0, loai="phan_tram", raw="20%", page=11,
             location="Mục 1, trang 11", nhan_dong="Worker",
             tieu_de_cot="% Tiêu thụ"),
    # Cùng con số 20%, KHÁC đại lượng, ở trang liền kề. Ca thật Vtag tr.10.
    OKhaiBao(gia_tri=20.0, loai="phan_tram", raw="20%", page=10,
             location="Mục 1, trang 10", nhan_dong="Thông số thiết kế",
             tieu_de_cot="Tỷ lệ online"),
]

DONG_NODE4 = "node4   1403m       20%    10393Mi         66%"
DONG_NODE1 = "node1   162m        4%     4385Mi          59%"


class TestNeo:
    def test_trang_gan_nhat_thang_truoc_khi_xet_va_cham(self):
        """Ca thật Vtag `anh#53` (tr.11): `20%` khớp «Worker» tr.11 VÀ «Tỷ lệ
        online» tr.10. Xét va chạm trên cả cửa sổ thì mất một neo ĐÚNG.
        """
        kq = anh("anh#53", "Mục 1, trang 11", [
            so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
            # `20%` một mình là chứng cứ yếu (xem `test_neo_yeu_...`); dòng thật
            # có cả `66%`, và chính cặp đó mới đủ căn cứ.
            so("node4 - MEMORY%", "66%", trich_dan=DONG_NODE4)])
        r = neo_mot_anh(kq, KB_VTAG)
        assert r.va_cham == 0
        assert {n.scope_key for n in r.neo} == {"Worker"}
        o20 = next(n.o for n in r.neo if n.so.raw == "20%")
        assert o20.location == "Mục 1, trang 11"

    def test_va_cham_that_thi_bo(self):
        """Cùng khoảng cách trang, hai nhãn khác nhau ⇒ không biết ⇒ bỏ (NT4)."""
        kb = [
            OKhaiBao(gia_tri=20.0, loai="phan_tram", raw="20%", page=11,
                     location="Mục 1, trang 11", nhan_dong="Worker"),
            OKhaiBao(gia_tri=20.0, loai="phan_tram", raw="20%", page=11,
                     location="Mục 1, trang 11", nhan_dong="Redis"),
        ]
        kq = anh("a", "Mục 1, trang 11", [so("CPU%", "20%")])
        r = neo_mot_anh(kq, kb)
        assert r.va_cham == 1 and r.neo == []

    def test_thua_huong_theo_dong_nguon(self):
        """Đây là chỗ C4 lấy được số mà BẢNG KHÔNG khai: `1403m`, `10393Mi`."""
        kq = anh("anh#53", "Mục 1, trang 11", [
            so("node4 - CPU(cores)", "1403m", trich_dan=DONG_NODE4),
            so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
            so("node4 - MEMORY(bytes)", "10393Mi", trich_dan=DONG_NODE4),
            so("node4 - MEMORY%", "66%", trich_dan=DONG_NODE4),
        ])
        r = neo_mot_anh(kq, KB_VTAG)
        thua = {n.so.raw: n.scope_key for n in r.neo if not n.truc_tiep}
        assert thua == {"1403m": "Worker", "10393Mi": "Worker"}

    def test_khong_thua_huong_qua_dong_khac(self):
        """`kubectl top nodes`: mỗi dòng một node. Neo được node4 KHÔNG cho phép
        gán node1 vào cùng phân hệ."""
        kq = anh("anh#53", "Mục 1, trang 11", [
            so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
            so("node4 - MEMORY%", "66%", trich_dan=DONG_NODE4),
            so("node1 - CPU(cores)", "162m", trich_dan=DONG_NODE1),
        ])
        r = neo_mot_anh(kq, KB_VTAG)
        assert {n.so.raw for n in r.neo} == {"20%", "66%"}

    def test_ca_anh_mac_dinh_tat(self):
        """Suy rộng ra cả ảnh chỉ đúng cho `top`/`free`; mặc định phải TẮT."""
        kq = anh("anh#79", "Mục 3, trang 9", [
            so("CPU - us", "31.2", "%", trich_dan="%Cpu(s): 31.2 us,  9.5 sy"),
            so("RAM total", "128010.0", "MiB",
               trich_dan="MiB Mem : 128010.0 total"),
        ])
        kb = [OKhaiBao(gia_tri=31.2, loai="phan_tram", raw="31.2%", page=9,
                       location="Mục 3, trang 9", nhan_dong="Test",
                       tieu_de_cot="Tải CPU")]
        assert len(neo_mot_anh(kq, kb).neo) == 1
        r = neo_mot_anh(kq, kb, ca_anh=True)
        assert {n.so.raw for n in r.neo} == {"31.2", "128010.0"}

    def test_ca_anh_gan_sai_khi_anh_co_nhieu_may(self):
        """Đã ĐO trên Vtag `anh#134`, không phải phỏng đoán: chỉ node4/5 neo được
        ⇒ tập phân hệ = {Worker} ⇒ `ca_anh` gán luôn node1 (vốn là **Master**,
        chính tr.9 khai «Master · RAM · 59%») thành «Worker».

        Test này khoá lý do `ca_anh` phải mặc định TẮT.
        """
        kq = anh("anh#134", "Mục 1, trang 22", [
            so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
            so("node1 - MEMORY(bytes)", "4385Mi", trich_dan=DONG_NODE1),
        ])
        kb = [OKhaiBao(gia_tri=20.0, loai="phan_tram", raw="20%", page=22,
                       location="Mục 1, trang 22", nhan_dong="Worker")]
        assert [n.scope_key for n in neo_mot_anh(kq, kb).neo] == ["Worker"]
        sai = neo_mot_anh(kq, kb, ca_anh=True)
        assert {n.so.nhan: n.scope_key for n in sai.neo}[
            "node1 - MEMORY(bytes)"] == "Worker", "ca_anh gán sai — đúng như đã đo"

    def test_neo_yeu_gia_tri_mo_ho_dung_mot_minh_thi_bo(self):
        """Ca thật VTracking `anh#61`: ảnh đọc `CPU% - master-node = 1%`.

        `1%` có ở 4 ô khai báo thuộc 3 phân hệ (Kafka, Video Streaming, Worker).
        Cổng đại lượng loại hai ô RAM rồi để lại đúng một ô «Video Streaming ·
        Cores» — nó THẮNG BẰNG LOẠI TRỪ chứ không bằng chứng cứ, và kéo theo 6 số
        cùng dòng thừa hưởng quy kết sai.
        """
        kb = [
            OKhaiBao(gia_tri=1.0, loai="phan_tram", raw="1%", page=4,
                     location="trang 4", nhan_dong="Video Streaming",
                     tieu_de_cot="Cores"),
            OKhaiBao(gia_tri=1.0, loai="phan_tram", raw="1%", page=4,
                     location="trang 4", nhan_dong="Worker", tieu_de_cot="RAM"),
            OKhaiBao(gia_tri=1.0, loai="phan_tram", raw="1%", page=4,
                     location="trang 4", nhan_dong="Kafka", tieu_de_cot="RAM"),
        ]
        dong = "master-node   226m   1%   4971Mi   31%"
        kq = anh("anh#61", "Mục 1, trang 5", [
            so("CPU% - master-node", "1%", trich_dan=dong),
            so("MEMORY% - master-node", "31%", trich_dan=dong),
            so("CPU(cores) - master-node", "226m", trich_dan=dong),
        ])
        r = neo_mot_anh(kq, kb)
        assert r.neo == [], "1% đứng một mình không đủ căn cứ"
        assert r.neo_yeu == 1
        # và vì không neo được, KHÔNG số nào cùng dòng được thừa hưởng
        assert thanh_finding(r) is not None

    def test_gia_tri_duy_nhat_thi_dung_mot_minh_van_du(self):
        """PBH `31.2` và Vtag `63%` chỉ ứng với MỘT phân hệ ⇒ tự nó đã định danh."""
        kb = [OKhaiBao(gia_tri=31.2, loai="phan_tram", raw="31.2%", page=9,
                       location="Mục 3, trang 9", nhan_dong="Test",
                       tieu_de_cot="Tải CPU")]
        kq = anh("anh#79", "Mục 3, trang 9", [
            so("CPU - us (user)", "31.2", "%", trich_dan="%Cpu(s): 31.2 us")])
        r = neo_mot_anh(kq, kb)
        assert [n.scope_key for n in r.neo] == ["Test"] and r.neo_yeu == 0

    def test_lech_dai_luong_thi_bo(self):
        """Ca thật callbot XMKH `anh#88`: `GPU 0 — Bộ nhớ = 80%` khớp một ô `80%`
        nằm ở cột «Lưu trữ». Trùng số, khác hẳn thứ đang nói tới."""
        kb = [OKhaiBao(gia_tri=80.0, loai="phan_tram", raw="80%", page=11,
                       location="Mục III, trang 11", nhan_dong="Model",
                       tieu_de_cot="Lưu trữ")]
        kq = anh("anh#88", "Mục III, trang 13", [
            so("GPU 0 — Bộ nhớ / Util", "80%",
               trich_dan="18235MiB / 24220MiB | 80% Default")])
        r = neo_mot_anh(kq, kb)
        assert r.neo == [] and r.lech_dai_luong == 1

    def test_gan_trang_loai_bang_o_xa(self):
        # Dùng `66%` vì nó chỉ thuộc MỘT nhãn trong KB_VTAG, nên đứng một mình
        # vẫn đủ căn cứ — phép thử này nói về cổng TRANG, không về chứng cứ.
        kq = anh("a", "Mục 1, trang 30", [so("MEMORY%", "66%")])
        assert neo_mot_anh(kq, KB_VTAG).neo == []
        assert neo_mot_anh(kq, KB_VTAG, gan_trang=None).neo != []

    def test_dung_sai_0_loai_khop_gan_dung(self):
        """`706` khớp `715` ở dung sai 2% — đúng loại rác mà cổng phải chặn."""
        kb = [OKhaiBao(gia_tri=715.0, loai="dem", raw="715", page=9,
                       location="Mục 3, trang 9", nhan_dong="Test")]
        kq = anh("a", "Mục 3, trang 9", [so("Tasks", "706")])
        assert neo_mot_anh(kq, kb, loai_nhan=("dem",)).neo == []
        assert neo_mot_anh(kq, kb, loai_nhan=("dem",), dung_sai=0.02).neo != []

    def test_khac_loai_dai_luong_thi_khong_khop(self):
        """`5,0M` (byte) không được khớp ô khai báo `5.0` (số trần)."""
        kb = [OKhaiBao(gia_tri=5.0, loai="dem", raw="5.0", page=5,
                       location="Mục 2, trang 5", nhan_dong="Test")]
        kq = anh("a", "Mục 2, trang 5", [so("/run/lock", "5,0M")])
        r = neo_mot_anh(kq, kb, loai_nhan=("dem", "byte"))
        assert r.neo == [] and r.so_khong_neo == 1


# --------------------------------------------------------------------- NT4 --
class TestNT4:
    def test_anh_khong_neo_duoc_sinh_canh_bao_co_can_cu(self):
        kq = anh("anh#30", "Mục 2, trang 5", [so("CPU(s)", "32")])
        r = neo_mot_anh(kq, KB_VTAG)
        f = thanh_finding(r)
        assert f is not None
        assert f.category == "khong_kiem_chung_duoc"
        assert f.co_can_cu(), "NT2: cảnh báo phải có computed_evidence"
        assert "anh#30" in f.finding

    def test_moi_so_bi_loai_deu_duoc_dem(self):
        """Bộ đếm bị nuốt là mù — lượt chạy đầu in ra dòng NT4 RỖNG vì số bị loại
        ở nhánh «loại không được nhận» không được đếm ở đâu cả."""
        kq = anh("a", "Mục 1, trang 13", [
            so("root", "983G", trich_dan="/dev/x 983G"),          # byte, không nhận
            so("model", "AMD Ryzen 9 7950X"),                     # không xếp loại
        ])
        r = neo_mot_anh(kq, KB_VTAG)
        assert r.so_ngoai_loai_nhan + r.so_khong_xep_loai + r.so_khong_neo \
            + r.va_cham + len([n for n in r.neo if n.truc_tiep]) == r.so_da_doc
        f = thanh_finding(r)
        assert f is not None and f.computed_evidence.strip()

    def test_neo_duoc_thi_khong_sinh_canh_bao(self):
        kq = anh("anh#53", "Mục 1, trang 11", [
            so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
            so("node4 - MEMORY%", "66%", trich_dan=DONG_NODE4)])
        assert thanh_finding(neo_mot_anh(kq, KB_VTAG)) is None


# ------------------------------------------------------- chạy trên tài liệu --
def test_neo_tai_lieu_dem_du_moi_so(tmp_path):
    doc = _docx_khai_bao(tmp_path, [
        ["Phân hệ", "% Tiêu thụ"],
        ["Worker", "20%"],
    ])
    kq = [anh("a", "Mục 1, trang 1", [
        so("node4 - CPU%", "20%", trich_dan=DONG_NODE4),
        so("node4 - CPU(cores)", "1403m", trich_dan=DONG_NODE4)])]
    ket, tk = neo_tai_lieu(doc, kq)
    assert tk.anh_co_so == 1 and tk.anh_neo_duoc == 1
    assert tk.neo_truc_tiep == 1 and tk.neo_thua_huong == 1
    assert ket[0].scope_keys == ["Worker"]
    # `python-docx` dựng file không có thông tin phân trang ⇒ cổng trang phải tự
    # tắt và NÓI RA, chứ không lặng lẽ trả 0 neo.
    assert tk.khong_co_so_trang is True
    assert "KHÔNG có số trang" in tk.tom_tat()


def test_bo_qua_anh_khong_co_so_lieu(tmp_path):
    doc = _docx_khai_bao(tmp_path, [["Phân hệ", "%"], ["Worker", "20%"]])
    kq = [KetQuaDocAnh(ma_anh="s", loai="so_do", location="trang 4",
                       doc_duoc=True, thanh_phan=["MQTT Broker"])]
    ket, tk = neo_tai_lieu(doc, kq)
    assert ket == [] and tk.anh_co_so == 0


# ------------------------------------------------------ dung lượng (byte) --
class TestByte:
    def test_co_so_lay_tu_units_yaml_khong_hard_code(self):
        """NT3: «GB» = 2³⁰ là DỮ LIỆU trong `config/units.yaml`, không phải hằng
        số trong code. Người dùng xác nhận quy ước 2026-09-09."""
        from src.vision.neo_so import _boi_byte, co_so_dung_luong
        assert co_so_dung_luong() == 1024
        assert _boi_byte()["g"] == 1024 ** 3

    def test_don_vi_o_tieu_de_cot(self, tmp_path):
        """«Tổng dung lượng (GB)» rồi ô chỉ ghi «1000» — đơn vị ở TIÊU ĐỀ.

        Không đọc tiêu đề thì 50/58 ô dung lượng của Vtag bị xếp nhầm là `dem`.
        """
        doc = _docx_khai_bao(tmp_path, [
            ["Phân hệ", "Tổng dung lượng (GB)"],
            ["Postgres", "1000"],
        ])
        kb = [o for o in thu_thap_khai_bao(doc) if o.loai == "byte"]
        assert [o.gia_tri for o in kb] == [1000 * 1024 ** 3]

    def test_chuoi_luong_nghia_KHONG_duoc_lam_neo(self, tmp_path):
        """Ca thật: «15.712» dưới cột «RAM used (GB)» — 15712 hay 15,712?

        Sai một lần là lệch 1000 lần, mà giá trị lệch 1000 lần vẫn có thể TÌNH CỜ
        bằng một số đọc từ ảnh. `units.yaml`: *"TUYỆT ĐỐI không im lặng chọn một
        cách rồi tính tiếp"*.
        """
        doc = _docx_khai_bao(tmp_path, [
            ["Server", "RAM used (GB)"],
            ["10.60.105.79", "15.712"],
        ])
        assert [o for o in thu_thap_khai_bao(doc) if o.loai == "byte"] == []
        assert gia_tri_chuan("15.712", "GB", chat_che=True) is None
        assert gia_tri_chuan("15.712", "GB") is not None      # lỏng thì vẫn ra số

    def test_neo_duoc_dung_luong_do_bang_du(self):
        """Ca thật Vtag `anh#65`: `du /var/lib/postgresql/14` = 536G, và bảng khai
        đúng «536 GB» cho Postgres — ảnh này trước đó không neo nổi gì."""
        kb = [OKhaiBao(gia_tri=536 * 1024 ** 3, loai="byte", raw="536 GB", page=14,
                       location="Mục 1, trang 14", nhan_dong="Postgres",
                       bang_con="DISK")]
        kq = anh("anh#65", "Mục 1, trang 13", [
            so("Dung lượng lưu trữ (output của lệnh du)", "536G", "G",
               trich_dan="536G    /var/lib/postgresql/14")])
        r = neo_mot_anh(kq, kb, loai_nhan=("byte",))
        assert [n.scope_key for n in r.neo] == ["Postgres"]
