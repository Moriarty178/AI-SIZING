"""5.3 — dùng lại câu trả lời model của lần thẩm định trước. OFFLINE.

Ba lớp:
- khoá và bộ ghi (`src/llm/phat_lai.py`) — thuần Python;
- TRỌN pipeline thật (C1 → C3 → C4 → C5 → C7, `rules.yaml` thật) trên FILE WORD THẬT,
  model giả tất định theo nội dung lời gọi: nộp y nguyên / sửa một ô bảng / chèn một
  đoạn ở đầu làm mọi chỉ số và số trang phía sau dịch đi;
- bộ chạy việc: lượt sau đọc bản ghi của lượt trước, nói ra khi không dùng lại được.
"""
import functools
import hashlib
import json
import random
import re
import tempfile

import pytest
from pydantic import BaseModel

docx = pytest.importorskip("docx")

from eval.gia_lap import ClientGiaLap                         # noqa: E402
from src.ingestion.docx_reader import read_docx               # noqa: E402
from src.llm.client import ExtractionFailed                   # noqa: E402
from src.llm.phat_lai import PHIEN_BAN, PhatLai, bo_vi_tri, khoa_loi_goi  # noqa: E402


# ------------------------------------------------------------------ khoá --
class _LD(BaseModel):
    gia_tri: str


class _Dem:
    """Client giả tối giản: đếm lượt gọi, trả theo hàng đợi."""
    chat_model, temperature = "m", 0.1

    def __init__(self, *tra):
        self.tra, self.so_goi = list(tra), 0

    def extract(self, schema, messages, **kw):
        self.so_goi += 1
        x = self.tra.pop(0)
        if isinstance(x, Exception):
            raise x
        return schema.model_validate(x)


def _tin(noi_dung):
    return [{"role": "system", "content": "hệ thống"}, {"role": "user", "content": noi_dung}]


def _khoa(noi_dung, **kw):
    return khoa_loi_goi(_LD, _tin(noi_dung), **{"model": "m", "nhiet_do": 0.1,
                                                "max_tokens": None, **kw})


class TestBoViTri:
    def test_bo_nhan_doan_bang_va_so_bang(self):
        s = ("[BẢNG #93 · Mục III.2, trang 14]\n  | CPU | 16 |\n"
             "[Mục III.2, trang 14] Kafka dùng 16 core\n[trang 3] mở đầu\n"
             "[phần tử #7] không mục\n=== BẢNG #93 CẦN PHÂN TÍCH ===")
        assert bo_vi_tri(s) == ("[BẢNG]\n  | CPU | 16 |\n[] Kafka dùng 16 core\n"
                                "[] mở đầu\n[] không mục\n=== BẢNG # CẦN PHÂN TÍCH ===")

    def test_KHONG_dong_vao_chu_cua_tai_lieu_giua_dong(self):
        assert bo_vi_tri("[] theo [Mục 2] của quy định") == "[] theo [Mục 2] của quy định"

    def test_chi_nhan_vi_tri_doi_thi_khoa_KHONG_doi(self):
        assert _khoa("[Mục II.1, trang 2] Kafka 16 core") == \
            _khoa("[Mục II.3, trang 9] Kafka 16 core")

    def test_noi_dung_doi_mot_chu_so_thi_khoa_doi(self):
        assert _khoa("[Mục II.1] Kafka 16 core") != _khoa("[Mục II.1] Kafka 18 core")

    def test_giu_vi_tri_thi_nhan_vi_tri_nam_trong_khoa(self):
        """Nhận diện phân hệ trả CHỈ SỐ bảng — dùng lại khi chỉ số đã dịch là trỏ lệch."""
        assert _khoa("[BẢNG #5 · Mục II] x", giu_vi_tri=True) != \
            _khoa("[BẢNG #6 · Mục II] x", giu_vi_tri=True)

    def test_duoi_so_cua_ten_luoc_do_la_vi_tri(self):
        """C3 hỏi bảng bằng lớp `GanBang{chỉ số}` — chèn một đoạn phía trước là đổi tên
        lớp của mọi bảng phía sau. Bắt được khi chạy trọn pipeline, không phải đoán."""
        from pydantic import create_model
        a, b = (create_model(f"GanBang{i}", cot_1=(str, ...)) for i in (5, 6))
        k = dict(model="m", nhiet_do=0.1, max_tokens=None)
        assert khoa_loi_goi(a, _tin("x"), **k) == khoa_loi_goi(b, _tin("x"), **k)
        assert khoa_loi_goi(a, _tin("x"), giu_vi_tri=True, **k) != \
            khoa_loi_goi(b, _tin("x"), giu_vi_tri=True, **k)

    def test_doi_model_hay_nhiet_do_hay_ngan_sach_thi_khoa_doi(self):
        goc = _khoa("x")
        assert goc != _khoa("x", model="khac")
        assert goc != _khoa("x", nhiet_do=0.0)
        assert goc != _khoa("x", max_tokens=9000)

    def test_doi_luoc_do_thi_khoa_doi(self):
        class _LD2(BaseModel):
            gia_tri: str
            them: str = ""
        _LD2.__name__ = "_LD"
        assert khoa_loi_goi(_LD2, _tin("x"), model="m", nhiet_do=0.1, max_tokens=None) \
            != _khoa("x")


class TestGhiVaDungLai:
    def test_luot_sau_KHONG_goi_model_va_tra_dung_cau_cu(self):
        c = _Dem({"gia_tri": "16"})
        p1 = PhatLai()
        assert p1.goi(c, _LD, _tin("[Mục I] a"), thanh_phan="c3").gia_tri == "16"
        p2 = PhatLai(json.loads(json.dumps(p1.xuat())), tu_viec="v1")
        kq = p2.goi(c, _LD, _tin("[Mục IX] a"), thanh_phan="c3")
        assert (kq.gia_tri, c.so_goi) == ("16", 1)
        assert p2.thong_ke()["c3"] == {"dung_lai": 1, "goi_moi": 0, "goi_moi_vi_du": []}

    def test_ban_ghi_luot_sau_DU_ca_phan_dung_lai(self):
        """Lần 3 dùng lại từ lần 2 — bản ghi lần 2 phải có cả câu nó lấy từ lần 1."""
        c = _Dem({"gia_tri": "a"}, {"gia_tri": "b"})
        p1 = PhatLai()
        p1.goi(c, _LD, _tin("một"), thanh_phan="c3")
        p2 = PhatLai(p1.xuat())
        p2.goi(c, _LD, _tin("một"), thanh_phan="c3")
        p2.goi(c, _LD, _tin("hai"), thanh_phan="c5", nhan="ARC-01#Kafka")
        assert len(p2.xuat()["phan_hoi"]) == 2
        assert p2.thong_ke()["c5"]["goi_moi_vi_du"] == ["ARC-01#Kafka"]

    def test_luot_hong_KHONG_duoc_ghi_lan_sau_hoi_lai(self):
        c = _Dem(ExtractionFailed(3, "hỏng"), {"gia_tri": "ok"})
        p1 = PhatLai()
        with pytest.raises(ExtractionFailed):
            p1.goi(c, _LD, _tin("x"), thanh_phan="c3")
        assert p1.xuat()["phan_hoi"] == {}
        assert PhatLai(p1.xuat()).goi(c, _LD, _tin("x"), thanh_phan="c3").gia_tri == "ok"
        assert c.so_goi == 2

    def test_ban_ghi_khong_con_hop_luoc_do_thi_hoi_lai(self):
        c = _Dem({"gia_tri": "moi"})
        k = _khoa("x")
        p = PhatLai({"phien_ban": PHIEN_BAN, "phan_hoi": {k: '{"sai": 1}'}})
        assert p.goi(c, _LD, _tin("x"), thanh_phan="c3").gia_tri == "moi"

    @pytest.mark.parametrize("hong", [None, [], {"phien_ban": 0},
                                      {"phien_ban": PHIEN_BAN, "phan_hoi": []}])
    def test_ban_ghi_hong_hay_khac_phien_ban_thi_coi_nhu_khong_co(self, hong):
        p = PhatLai(hong, tu_viec="v1")
        assert p.co_ban_cu is False and p.tu_viec == ""
        c = _Dem({"gia_tri": "a"})
        p.goi(c, _LD, _tin("x"), thanh_phan="c3")
        assert c.so_goi == 1


class TestKhoaTheoVung:
    """C5 gửi model cả tài liệu nhưng khoá theo vùng của phân hệ (chốt 2026-09-18)."""

    def test_doi_phan_NGOAI_vung_van_dung_lai_duoc(self):
        c = _Dem({"gia_tri": "16"})
        vung = "[Mục II.1] Kafka 16 core"
        p1 = PhatLai()
        p1.goi(c, _LD, _tin(f"{vung}\n[Mục II.2] Redis 8 core"), thanh_phan="c5",
               vung_tai_lieu=(f"{vung}\n[Mục II.2] Redis 8 core", vung))
        p2 = PhatLai(p1.xuat())
        p2.goi(c, _LD, _tin(f"{vung}\n[Mục II.2] Redis 12 core"), thanh_phan="c5",
               vung_tai_lieu=(f"{vung}\n[Mục II.2] Redis 12 core", vung))
        assert c.so_goi == 1 and p2.thong_ke()["c5"]["dung_lai"] == 1

    def test_doi_TRONG_vung_thi_hoi_lai(self):
        c = _Dem({"gia_tri": "16"}, {"gia_tri": "18"})
        p1 = PhatLai()
        p1.goi(c, _LD, _tin("cả tài liệu"), thanh_phan="c5",
               vung_tai_lieu=("cả tài liệu", "[Mục II.1] Kafka 16 core"))
        p2 = PhatLai(p1.xuat())
        kq = p2.goi(c, _LD, _tin("cả tài liệu"), thanh_phan="c5",
                    vung_tai_lieu=("cả tài liệu", "[Mục II.1] Kafka 18 core"))
        assert (kq.gia_tri, c.so_goi) == ("18", 2)

    def test_vung_rong_thi_khoa_theo_ca_tai_lieu(self):
        """Quy tắc cấp hệ thống, hoặc phân hệ không biết vùng — không được nới khoá.

        Bản đầu thay đoạn tài liệu bằng chuỗi RỖNG, tức khoá không còn chứa tài liệu:
        mọi quy tắc cấp hệ thống dùng lại kết luận cũ kể cả khi tài liệu đã đổi."""
        c = _Dem({"gia_tri": "a"}, {"gia_tri": "b"})
        p1 = PhatLai()
        p1.goi(c, _LD, _tin("tài liệu bản 1"), thanh_phan="c5", vung_tai_lieu=("x", ""))
        p2 = PhatLai(p1.xuat())
        p2.goi(c, _LD, _tin("tài liệu bản 2"), thanh_phan="c5", vung_tai_lieu=("x", ""))
        assert c.so_goi == 2


class TestVungDoi:
    def test_bao_vung_doi_vung_moi_va_phan_chung(self):
        p1 = PhatLai()
        p1.ghi_vung({"": "c", "kafka": "k", "redis": "r"})
        p2 = PhatLai(p1.xuat())
        p2.ghi_vung({"": "c2", "kafka": "k", "redis": "r2", "mongo": "m"})
        tk = p2.thong_ke()
        assert (tk["vung_doi"], tk["vung_moi"], tk["chung_doi"]) == (["redis"], ["mongo"], True)


# ------------------------------------------- trọn pipeline trên Word thật --
DAI = ("Phân hệ này xử lý luồng bản tin vị trí từ thiết bị giám sát hành trình, "
       "nhận qua cổng TCP, chuẩn hoá và đẩy sang lớp lưu trữ. Mô hình triển khai "
       "active-active trên ba node, mỗi node chịu tối đa năm mươi phần trăm tải đỉnh "
       "để khi mất một node hệ thống vẫn phục vụ đủ. Lưu lượng mỗi bản tin khoảng "
       "hai kilobyte, giao thức HTTPS qua cổng 443, nguồn request từ bên ngoài. ")


def _word(*, chen_dau=False, redis_cpu="8") -> str:
    """Hai phân hệ, mỗi phân hệ một mục riêng ĐỦ DÀI (ngữ cảnh hẹp dưới 400 ký tự thì
    C3 lùi về cả tài liệu) và một bảng số liệu. Ngắt trang thủ công để có số trang."""
    d = docx.Document()
    d.add_heading("I. Giới thiệu", level=1)
    if chen_dau:
        d.add_paragraph("Đoạn mới chèn thêm ở đầu tài liệu sau lần thẩm định trước.")
        d.add_page_break()
    d.add_paragraph("Tài liệu định cỡ hệ thống giám sát hành trình. " * 3)
    d.add_page_break()
    d.add_heading("II. Định cỡ", level=1)
    for ten, cpu, ram in (("Kafka", "16", "32"), ("Redis", redis_cpu, "64")):
        d.add_heading(f"{1 if ten == 'Kafka' else 2}. Phân hệ {ten}", level=2)
        d.add_paragraph(f"{ten}. " + DAI)
        t = d.add_table(rows=2, cols=3)
        for i, v in enumerate(["Thành phần", "CPU (core)", "RAM (GB)"]):
            t.rows[0].cells[i].text = v
        for i, v in enumerate([f"{ten} node", cpu, ram]):
            t.rows[1].cells[i].text = v
    f = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
    d.save(f.name)
    f.close()
    return f.name


class ModelTheoNoiDung(ClientGiaLap):
    """Model giả TẤT ĐỊNH theo nội dung lời gọi: cùng lời nhắc thì cùng câu trả lời,
    khác một chữ thì câu trả lời có thể khác — đúng tính chất dùng lại dựa vào."""

    def __init__(self):
        super().__init__(ty_le_trich_dan_bia=0.0)
        self.so_goi = 0

    def extract(self, schema, messages, **kw):
        self.so_goi += 1
        noi_dung = messages[-1]["content"]
        if schema.__name__ == "DanhSachPhanHe":
            bang = [int(x) for x in re.findall(r"\[BẢNG #(\d+)", noi_dung)]
            return schema.model_validate({"phan_he": [
                {"ten_phan_he": ten, "cong_nghe": ten, "cong_nghe_luu_tru": "khong_neu",
                 "muc": "", "bang_cau_hinh": b} for ten, b in zip(("Kafka", "Redis"), bang)]})
        self.rnd = random.Random(hashlib.sha256(
            json.dumps(messages, ensure_ascii=False).encode("utf-8")).hexdigest())
        return super().extract(schema, messages, **kw)


def _chay(path, model, phat_lai):
    from src.pipeline import chay
    return chay(path, client=model, phat_lai=phat_lai)


def _vet(kq):
    return sorted((f.id, f.severity, f.category, f.finding, f.location,
                   f.computed_evidence) for f in kq.findings)


@pytest.fixture(scope="module")
def lan_1():
    goc = _word()
    m = ModelTheoNoiDung()
    p = PhatLai()
    kq = _chay(goc, m, p)
    return goc, kq, json.loads(json.dumps(p.xuat())), m.so_goi


class TestTronPipeline:
    def test_lan_1_ghi_lai_moi_luot_hoi_thanh_cong(self, lan_1):
        _, kq, ban_ghi, so_goi = lan_1
        tk = kq.thong_ke
        hong = tk["c3"]["luot_goi_hong"] + tk["c5"]["luot_goi_hong"]
        assert so_goi > 50
        assert tk["phat_lai"]["c3"]["dung_lai"] == tk["phat_lai"]["c5"]["dung_lai"] == 0
        assert len(ban_ghi["phan_hoi"]) >= so_goi - hong - 5   # trùng khoá được gộp

    def test_nop_Y_NGUYEN_thi_KHONG_hoi_model_va_ket_qua_GIONG_HET(self, lan_1):
        """Đây là thứ xoá được ~10 dòng «đạt» giả mỗi lần thẩm định lại (5.0b): phần
        không đổi cho ĐÚNG kết quả cũ, không phải một lượt model mới dao động."""
        goc, kq1, ban_ghi, _ = lan_1
        m = ModelTheoNoiDung()
        kq2 = _chay(goc, m, PhatLai(ban_ghi, tu_viec="v1"))
        hong = kq1.thong_ke["c3"]["luot_goi_hong"] + kq1.thong_ke["c5"]["luot_goi_hong"]
        assert m.so_goi == hong == 0
        assert _vet(kq2) == _vet(kq1)
        assert kq2.thong_ke["c4_he_so_du_phong"] == kq1.thong_ke["c4_he_so_du_phong"]

    def test_sua_MOT_O_BANG_cua_Redis_chi_hoi_lai_phan_doc_toi_no(self, lan_1):
        _, kq1, ban_ghi, _ = lan_1
        m = ModelTheoNoiDung()
        kq = _chay(_word(redis_cpu="12"), m, PhatLai(ban_ghi, tu_viec="v1"))
        pl = kq.thong_ke["phat_lai"]
        hoi_lai = " | ".join(pl["c3"]["goi_moi_vi_du"])
        assert pl["c3"]["dung_lai"] > 0 and pl["c3"]["goi_moi"] > 0
        assert "Redis · nhóm" in hoi_lai and "Kafka · nhóm" not in hoi_lai
        assert "Mục II.1" not in hoi_lai, "bảng Kafka không đọc ô đã sửa — phải dùng lại"
        # C5 khoá theo vùng (chốt 2026-09-18): quy tắc của Kafka dùng lại được, quy
        # tắc cấp hệ thống và của Redis thì hỏi lại.
        c5 = " | ".join(pl["c5"]["goi_moi_vi_du"])
        assert pl["c5"]["dung_lai"] > 0 and "#Kafka" not in c5
        assert "#Redis" in c5 and "#he_thong" in c5
        assert (pl["vung_doi"], pl["chung_doi"]) == (["redis"], False)

    def test_chen_doan_o_DAU_lam_lech_chi_so_va_trang_van_dung_lai_C3_phan_he(self, lan_1):
        goc, _, ban_ghi, _ = lan_1
        moi = _word(chen_dau=True)
        kafka = [e for e in read_docx(goc).elements if e.kind == "table"][0]
        kafka_moi = [e for e in read_docx(moi).elements if e.kind == "table"][0]
        assert (kafka.index, kafka.location) != (kafka_moi.index, kafka_moi.location), \
            "phép thử phải thật sự làm lệch chỉ số và số trang"
        kq = _chay(moi, ModelTheoNoiDung(), PhatLai(ban_ghi, tu_viec="v1"))
        pl = kq.thong_ke["phat_lai"]
        hoi_lai = " | ".join(pl["c3"]["goi_moi_vi_du"])
        assert "Kafka · nhóm" not in hoi_lai and "Redis · nhóm" not in hoi_lai
        assert not any(x.startswith("bảng") for x in pl["c3"]["goi_moi_vi_du"])
        assert "nhận diện phân hệ" in hoi_lai, "lượt trả chỉ số bảng giữ vị trí trong khoá"
        assert (pl["vung_doi"], pl["chung_doi"]) == ([], True)

    def test_sua_PHAN_CHUNG_thi_moi_quy_tac_C5_deu_hoi_lai(self, lan_1):
        """Vùng khoá của một phân hệ gồm cả phần chung: sửa phần giới thiệu là mọi kết
        luận định tính đều có thể đổi."""
        _, kq1, ban_ghi, _ = lan_1
        kq = _chay(_word(chen_dau=True), ModelTheoNoiDung(), PhatLai(ban_ghi))
        pl = kq.thong_ke["phat_lai"]
        assert pl["c5"]["dung_lai"] == 0
        assert pl["c5"]["goi_moi"] == kq1.thong_ke["phat_lai"]["c5"]["goi_moi"]
        assert pl["chung_doi"] is True


# ------------------------------------------------------------ bộ chạy việc --
@pytest.fixture
def bo(tmp_path):
    from src.cong_viec import BoChay, KhoCongViec
    from src.pipeline import chay
    m = ModelTheoNoiDung()
    kho = KhoCongViec(tmp_path / "cv")
    b = BoChay(kho, ham_chay=functools.partial(chay, client=m), song_song=1)
    b.bat_dau()
    yield kho, b, m
    b.dung()


def _nop(kho, b, path, **kw):
    with open(path, "rb") as f:
        cv = kho.them("Sizing thử.docx", "", noi_dung=f.read(), **kw)
    b.nop(cv)
    assert b.cho_rong(120)
    return kho.lay(cv.ma)


class TestBoChay:
    def test_lan_sau_dung_lai_lan_truoc_va_noi_ra(self, bo):
        kho, b, m = bo
        goc = _word()
        v1 = _nop(kho, b, goc)
        assert v1.trang_thai == "xong" and v1.phat_lai == "" and v1.thay_doi == {}
        assert kho.phat_lai(v1.ma)["phien_ban"] == PHIEN_BAN
        truoc = m.so_goi
        v2 = _nop(kho, b, goc, lan_truoc=v1.ma)
        assert m.so_goi == truoc, "nộp y nguyên: không một lượt nào tới model"
        assert v2.phat_lai.startswith("dùng lại ") and f"việc {v1.ma}" in v2.phat_lai
        assert v2.thay_doi["giong_het"] is True and v2.thay_doi["voi_viec"] == v1.ma

    def test_chon_toan_bo_thi_hoi_lai_het(self, bo):
        kho, b, m = bo
        goc = _word()
        v1 = _nop(kho, b, goc)
        truoc = m.so_goi
        v2 = _nop(kho, b, goc, lan_truoc=v1.ma, toan_bo=True)
        assert m.so_goi - truoc == truoc
        assert v2.phat_lai == "không dùng lại — người nộp chọn thẩm định lại toàn bộ"

    def test_lan_truoc_KHONG_co_ban_ghi_thi_noi_ra_va_chay_toan_bo(self, bo):
        """Hồ sơ chạy trước bản 5.3: lần thẩm định lại đầu tiên sau khi nâng cấp."""
        kho, b, m = bo
        v1 = _nop(kho, b, _word())
        kho._tep(v1.ma, ".phat_lai.json").unlink()
        v2 = _nop(kho, b, _word(redis_cpu="12"), lan_truoc=v1.ma)
        assert v2.phat_lai.startswith("không dùng lại được") and "chạy toàn bộ" in v2.phat_lai
        assert v2.thay_doi["sua"] == 1 and not v2.thay_doi["giong_het"]
        assert kho.phat_lai(v2.ma) is not None, "lượt này vẫn GHI cho lần sau"

    def test_tai_lieu_lan_truoc_da_xoa_thi_noi_khong_so_duoc(self, bo):
        kho, b, _ = bo
        v1 = _nop(kho, b, _word())
        kho.xoa(v1.ma)
        v2 = _nop(kho, b, _word(), lan_truoc=v1.ma)
        assert "không còn trên máy chủ" in v2.thay_doi["loi"]
        assert v2.phat_lai.startswith("không dùng lại được")

    def test_xoa_viec_xoa_ca_ban_ghi_cau_tra_loi(self, bo):
        kho, b, _ = bo
        v1 = _nop(kho, b, _word())
        assert kho._tep(v1.ma, ".phat_lai.json").exists()
        kho.xoa(v1.ma)
        assert not kho._tep(v1.ma, ".phat_lai.json").exists()
