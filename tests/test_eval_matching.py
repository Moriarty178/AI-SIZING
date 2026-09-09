"""Test 1.13 — phần so khớp của eval harness. Thuần code, chạy offline."""
import pytest

from eval.matching import KetQuaEval, bang_markdown, doi_chieu, nap_nhan
from src.reporting.finding import Finding


def _f(rule_ref: str) -> Finding:
    return Finding(id=rule_ref, severity="major", category="thieu_thong_tin",
                   finding="x", rule_ref=rule_ref)


def _nhan(lid, dossier, refs, **kw):
    return {"label_id": lid, "dossier": dossier, "rule_ref": refs,
            "khoang_trong": kw.get("khoang_trong", False),
            "khong_neo_duoc": kw.get("khong_neo_duoc", False)}


def test_trung_khi_ma_finding_nam_trong_danh_sach_cua_nhan():
    labels = [_nhan("l1", "HS1", ["PRC-01", "PRC-02"])]
    kq = doi_chieu({"HS1": [_f("PRC-02")]}, labels)
    assert kq.trung == 1 and kq.recall_quy_tac == 1.0


def test_khong_trung_khi_khac_ho_so():
    """Cùng mã nhưng khác hồ sơ thì KHÔNG tính — nếu không recall sẽ ảo."""
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    kq = doi_chieu({"HS2": [_f("PRC-01")]}, labels)
    assert kq.trung == 0


def test_hai_mau_so_tach_roi_theo_scoring_note():
    """`khoang_trong` không có rule_ref -> chỉ vào mẫu số "mọi yêu cầu"."""
    labels = [_nhan("l1", "HS1", ["PRC-01"]),
              _nhan("l2", "HS1", [], khoang_trong=True)]
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, labels)
    assert kq.nhan_co_rule == 1 and kq.nhan_tong == 2
    assert kq.recall_quy_tac == 1.0
    assert kq.recall_moi_yeu_cau == 0.5      # luôn thấp hơn, và đây là số nói với người dùng


def test_ho_so_khong_chay_duoc_VAN_tinh_vao_mau_so():
    """Bỏ hồ sơ hỏng ra khỏi mẫu số sẽ làm recall đẹp lên một cách giả tạo."""
    labels = [_nhan("l1", "HS1", ["PRC-01"]), _nhan("l2", "HS2", ["CPU-03"])]
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, labels)      # HS2 không chạy được
    assert kq.nhan_co_rule == 2 and kq.trung == 1
    assert kq.recall_quy_tac == 0.5
    hs2 = next(h for h in kq.ho_so if h.dossier == "HS2")
    assert "chưa chạy được" in hs2.ghi_chu


def test_mot_nhan_chi_duoc_tinh_MOT_lan_du_khop_nhieu_ma():
    labels = [_nhan("l1", "HS1", ["PRC-01", "PRC-02"])]
    kq = doi_chieu({"HS1": [_f("PRC-01"), _f("PRC-02")]}, labels)
    assert kq.trung == 1


def test_finding_khong_khop_duoc_liet_ke_nhung_KHONG_goi_la_false_positive():
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    kq = doi_chieu({"HS1": [_f("PRC-01"), _f("STO-03")]}, labels)
    h = kq.ho_so[0]
    assert h.finding_khong_khop == ["STO-03"]
    bc = bang_markdown(kq)
    assert "Không đo được false positive" in bc


def test_bao_cao_LUON_kem_han_che(tmp_path):
    bc = bang_markdown(doi_chieu({}, [_nhan("l1", "HS1", ["PRC-01"])]))
    assert "hào phóng hơn thực tế" in bc
    assert "chưa qua kiểm định độc lập" in bc


# --- nối với eval set THẬT --------------------------------------------------
def test_nap_dung_tap_dev_va_khong_lan_sang_test():
    dev = nap_nhan("dev")
    test = nap_nhan("test")
    assert len(dev) == 317 and len(test) == 158
    assert not ({l["dossier"] for l in dev} & {l["dossier"] for l in test})


def test_mau_so_tren_eval_set_that_khop_voi_meta():
    tat_ca = nap_nhan("tat_ca")
    assert len(tat_ca) == 475
    assert sum(1 for l in tat_ca if l.get("rule_ref")) == 469


def test_luot_chay_CO_LOC_phai_noi_ro_trong_bao_cao():
    """`--nhom KPI,CPU` cho C5 = 0 lượt (không quy tắc định tính nào thuộc hai nhóm
    đó), nên recall thấp hẳn. Báo cáo không nói thì sẽ có người trích như recall thật."""
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, [_nhan("l1", "HS1", ["PRC-01"])])
    kq.bo_loc = {"nhom C3": "KPI,CPU", "nhom C5": "KPI,CPU", "chi_vong": ""}
    bc = bang_markdown(kq)
    assert kq.da_loc
    assert "KHÔNG được trích như recall thật" in bc
    assert "KPI,CPU" in bc


def test_khong_loc_thi_khong_co_canh_bao_thua():
    kq = doi_chieu({"HS1": [_f("PRC-01")]}, [_nhan("l1", "HS1", ["PRC-01"])])
    assert not kq.da_loc
    assert "KHÔNG được trích như recall thật" not in bang_markdown(kq)


# --- chọn hồ sơ để chạy thử ------------------------------------------------
def test_chi_N_bo_qua_ho_so_khong_co_docx():
    """`--chi 1` từng rơi trúng "Cấp mới hệ thống VAPS" — hồ sơ duy nhất chỉ có PDF,
    sắp đầu bảng vì `C` hoa đứng trước `c` thường — nên cả lượt không gọi model lần nào."""
    from eval.run_eval import chon_ho_so
    tat_ca = ["Cấp mới hệ thống VAPS", "cap moi BCCS3", "cap bo sung campaign"]
    co_docx = ["cap bo sung campaign", "cap moi BCCS3"]
    assert chon_ho_so(tat_ca, co_docx, chi=1) == ["cap bo sung campaign"]


def test_chay_day_du_thi_GIU_ho_so_khong_co_docx_trong_mau_so():
    from eval.run_eval import chon_ho_so
    tat_ca = ["Cấp mới hệ thống VAPS", "cap moi BCCS3"]
    assert chon_ho_so(tat_ca, ["cap moi BCCS3"]) == tat_ca


def test_chon_dich_danh_mot_ho_so_theo_ten():
    from eval.run_eval import chon_ho_so
    tat_ca = ["cap moi BCCS3_thị_trường_Lào 34221", "cap moi c360 58872"]
    assert chon_ho_so(tat_ca, tat_ca, ho_so="bccs3") == [tat_ca[0]]
    assert chon_ho_so(tat_ca, tat_ca, ho_so="khong-co") == []


def test_ho_so_thang_thu_tu_khong_phan_biet_hoa_thuong():
    """Sắp xếp phân biệt hoa/thường là cái bẫy đã đưa VAPS lên đầu."""
    ds = sorted(["cap moi BCCS3", "Cấp mới VAPS", "cap bo sung campaign"], key=str.lower)
    assert ds[0] == "cap bo sung campaign"


def test_ho_so_nhan_nhieu_ten_ngan_cach_bang_phay():
    """Đo recall cả tập dev tốn 6–11 giờ, nên cách dùng thật là chạy một MẪU."""
    from eval.run_eval import chon_ho_so
    tat_ca = ["cap moi BCCS3 111", "cap moi CMP 222", "cap moi Mykid 333"]
    assert chon_ho_so(tat_ca, tat_ca, ho_so="bccs3, mykid") == [
        "cap moi BCCS3 111", "cap moi Mykid 333"]
    assert chon_ho_so(tat_ca, tat_ca, ho_so="cmp") == ["cap moi CMP 222"]

# --- chấm theo LOẠI nhãn ---------------------------------------------------
def _fc(rule_ref: str, category: str) -> Finding:
    return Finding(id=rule_ref, severity="major", category=category,
                   finding="x", rule_ref=rule_ref)


def test_nhan_thieu_trung_bang_finding_thieu_thong_tin_la_DUNG():
    """Cạm bẫy chính của thước đo theo loại: 56% nhãn dev là lời phàn nàn "chưa
    nêu / thiếu". Với chúng, một finding `thieu_thong_tin` chính là bắt đúng —
    loại nó ra (như cột `Thực chất` làm) là phạt oan."""
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    labels[0]["text"] = "Chưa nêu sở cứ tính toán số lượng máy chủ"
    kq = doi_chieu({"HS1": [_fc("PRC-01", "thieu_thong_tin")]}, labels)
    assert kq.trung_thuc_chat == 0        # sàn khắt khe: không tính
    assert kq.recall_theo_loai == 1.0     # theo loại: tính, vì ĐÚNG loại


def test_nhan_dinh_luong_KHONG_trung_bang_finding_thieu_thong_tin():
    """Người thẩm định hỏi một con số sai; công cụ chỉ nói "không tìm thấy trường"
    thì chưa bắt được gì. Đây là chỗ thước đo cũ cho điểm sai."""
    labels = [_nhan("l1", "HS1", ["PRC-01"])]
    labels[0]["text"] = "Dự phòng theo KPI 75% sao lại ra 8000, đề nghị tính lại"
    kq = doi_chieu({"HS1": [_fc("PRC-01", "thieu_thong_tin")]}, labels)
    assert kq.trung == 1                  # thước đo chính vẫn tính -> chính là lỗi
    assert kq.recall_theo_loai == 0.0
    kq2 = doi_chieu({"HS1": [_fc("PRC-01", "vuot_nguong")]}, labels)
    assert kq2.recall_theo_loai == 1.0


def test_nhan_qua_ngan_bi_BO_khoi_mau_so_chu_khong_doan():
    """NT4: không đủ chữ để biết đòi gì thì nói ra, không đoán về phía nào."""
    labels = [_nhan("l1", "HS1", ["PRC-01"]), _nhan("l2", "HS1", ["PRC-02"])]
    labels[0]["text"] = "Tài nguyên ram"
    labels[1]["text"] = "Dự phòng theo KPI 75% sao lại ra 8000, đề nghị tính lại"
    kq = doi_chieu({"HS1": [_fc("PRC-01", "thieu_thong_tin"),
                            _fc("PRC-02", "vuot_nguong")]}, labels)
    assert kq.theo_loai_mau["manh_vun"] == 1
    assert kq.recall_theo_loai == 1.0     # mẫu số chỉ còn nhãn l2
    assert "KHÔNG vào mẫu số" in bang_markdown(kq)

def test_nhan_MENH_LENH_doi_trinh_bay_duoc_tach_rieng_chu_khong_gop():
    """«Lập bảng…», «Đề xuất cấu hình cần có N+1» — người thẩm định nói *anh chưa
    trình bày*, không nói *số của anh sai*. Chúng không chứa chữ "chưa nêu/thiếu" nên
    rơi vào nhóm «yêu cầu khác», mà nhóm ấy từ chối đúng loại finding hợp với chúng.

    TÁCH RIÊNG chứ không gộp vào «thiếu»: gộp sẽ đẩy 15 nhãn từ nhóm ta đạt 4% sang
    nhóm ta đạt 94% — tự sửa thước đo cho con số của mình đẹp lên.
    """
    from eval.matching import loai_nhan
    assert loai_nhan("Đề xuất cấu hình cần có ít nhất N+1 server để đảm bảo HA")         == "menh_lenh"
    assert loai_nhan("Lập bảng giá trị đề xuất số lượng máy chủ theo mô hình của VT")         == "menh_lenh"
    kq = doi_chieu({"HS1": [_fc("PRC-01", "thieu_thong_tin")]},
                   [dict(_nhan("l1", "HS1", ["PRC-01"]),
                         text="Đề xuất cấu hình cần có ít nhất N+1 server")])
    assert kq.theo_loai_mau == {"menh_lenh": 1}
    assert "CHỜ XÁC NHẬN" in bang_markdown(kq)


def test_chat_van_con_so_SAI_khong_bi_xep_nham_sang_menh_lenh():
    """«…sao lại ra 8000, đề nghị tính lại» là chất vấn con số, phải kiểm bằng số.
    Xếp nó sang nhóm mệnh lệnh là tự cho điểm."""
    from eval.matching import loai_nhan
    assert loai_nhan("Dự phòng theo KPI 75% sao lại ra 8000, đề nghị tính lại") == "khac"


def test_dau_cach_dup_khong_duoc_lam_truot_tu_khoa():
    """Ca thật, 4 nhãn của GSCG: «Bổ  sung sở cứ cho Cấu hình server…» — HAI dấu
    cách giữa «Bổ» và «sung», chép nguyên từ Word.

    Không gộp khoảng trắng thì `"bổ sung" in text` trượt, và nhãn rơi từ nhóm
    «thiếu» xuống nhóm «đòi tính/so số» — đúng nhóm quyết định con số của 1.13.
    """
    from eval.matching import loai_nhan
    assert loai_nhan("Bổ  sung sở cứ cho Cấu hình server thực tế đang chạy") == "thieu"
    assert loai_nhan("Bổ sung sở cứ cho cấu hình") == "thieu"
    assert loai_nhan("Chưa\tnêu rõ cấu hình máy chủ ứng dụng") == "thieu"


# --- nhóm THỦ TỤC (phán quyết thẩm định 2026-09-09) ------------------------
def test_nhan_doi_THU_TUC_tach_khoi_nhom_quyet_dinh():
    """«Bắt buộc phải có thời gian cam kết…», «Ký sizing phải đính kèm checklist»
    — không phép tính nào trả lời được. Đơn vị thẩm định chốt tách, công cụ chỉ
    cần nhắc *"hồ sơ còn thiếu thủ tục này"*."""
    from eval.matching import loai_nhan
    assert loai_nhan("Bắt buộc phải có thời gian cam kết hoàn thành triển khai "
                     "và đổ tải thật, có sở cứ từ KD hoặc BGĐ") == "thu_tuc"
    assert loai_nhan("- Ký sizing phải đính kèm thêm file checklist (đính kèm)") \
        == "thu_tuc"
    assert loai_nhan("Tài nguyên con này đã có trong QHDC nào chưa ạ") == "thu_tuc"


def test_thu_tuc_xet_TRUOC_thieu_de_cung_doi_hoi_vao_cung_nhom():
    """Trước phán quyết, cùng một đòi hỏi rơi hai nhóm chỉ vì hành văn: «Bắt buộc
    phải có thời gian cam kết…» vào «khác» còn «Bổ sung thời gian cam kết…» vào
    «thiếu». Cả hai đều là thủ tục."""
    from eval.matching import loai_nhan
    assert loai_nhan("Bổ sung thời gian cam kết triển khai và đổ tải trên bảng "
                     "thông tin hệ thống") == "thu_tuc"


def test_nhan_DOI_SO_CU_o_LAI_nhom_quyet_dinh():
    """Câu 2 chốt NGƯỢC hướng có lợi cho công cụ: phải TÍNH LẠI con số mới tính
    đạt, trỏ được sở cứ là chưa đủ. Hai nhãn dưới từng bị tín hiệu `rule_ref`
    toàn mã `PRC-` kéo nhầm sang nhóm thủ tục."""
    from eval.matching import loai_nhan
    assert loai_nhan("Module Speech processing không rõ giá trị hệ thống hiện "
                     "tại để định cỡ, cần sở cứ") == "khac"
    assert loai_nhan("1. Thông tin hệ thống: Trang 27: sở cứ đây là ảnh chụp cho "
                     "150 t/bị trong 1.5 tháng ?Sở cứ lưu 24 tháng") == "khac"


def test_tu_khoa_thu_tuc_KHONG_duoc_bat_nhan_doi_tinh():
    """«đính kèm» trần bắt cả «Bổ sung tính toán băng thông cho FW/LB (tham khảo
    VD đính kèm)» — đó là đòi TÍNH. Test này khoá lại để không ai thêm nó."""
    from eval.matching import loai_nhan, TU_KHOA_THU_TUC
    assert "đính kèm" not in TU_KHOA_THU_TUC
    assert "tại sao" not in TU_KHOA_THU_TUC
    assert loai_nhan("Tổng hợp tính toán định cỡ: Bổ sung tính toán băng thông "
                     "cho FW/LB (tham khảo VD đính kèm)") == "thieu"


def test_phan_quyet_DICH_DANH_chi_ap_dung_khi_van_ban_con_khop(tmp_path):
    """Neo vào văn bản chứ không chỉ `label_id`: nhãn sinh lại mà đổi chữ thì
    phán quyết cũ có thể đang nói về câu khác — thà không áp dụng."""
    from eval.matching import loai_nhan
    lid = "PNX_CAMPAIGN_MANAGEMENT_v3|R1-04-03"
    assert loai_nhan("Tại sao mô hình Kafka là 5 instances", label_id=lid) \
        == "thu_tuc"
    assert loai_nhan("Tại sao mô hình Kafka là 9 instances", label_id=lid) == "khac"
    assert loai_nhan("Tại sao mô hình Kafka là 5 instances") == "khac"


def test_bao_cao_dem_ra_so_nhan_vao_nhom_thu_tuc_DICH_DANH():
    """Cơ chế đích danh là chỗ duy nhất thước đo can thiệp theo từng nhãn —
    không được giấu."""
    labels = [dict(_nhan("PNX_MySign_v2|R2-02-06", "HS1", ["BAK-01"]),
                   text="Tổng tài nguyên data, log, backup giữ nguyên không chia ra à ?")]
    kq = doi_chieu({"HS1": [_fc("BAK-01", "thieu_thong_tin")]}, labels)
    assert kq.theo_loai_mau == {"thu_tuc": 1}
    assert kq.thu_tuc_dich_danh == 1
    bc = bang_markdown(kq)
    assert "ĐÍCH DANH" in bc and "phải tính lại con số mới tính là đạt" in bc.lower()


def test_van_ban_nhan_doi_thi_CANH_BAO_chu_khong_im_lang():
    labels = [dict(_nhan("PNX_MySign_v2|R2-02-06", "HS1", ["BAK-01"]),
                   text="Câu này đã bị sửa thành một nhận xét hoàn toàn khác")]
    kq = doi_chieu({"HS1": [_fc("BAK-01", "thieu_thong_tin")]}, labels)
    assert kq.thu_tuc_dich_danh == 0
    assert any("đã đổi" in c for c in kq.canh_bao)


def test_luu_chi_tiet_TUNG_nhan_de_cham_lai_khong_can_model():
    """Lượt dev đầy đủ tốn ~7 giờ máy nội bộ. Chỉ lưu số tổng thì mỗi lần đổi
    cách xếp nhóm là phải chạy lại — đã vấp đúng thế ngày 2026-09-09."""
    labels = [dict(_nhan("l1", "HS1", ["PRC-01"]),
                   text="Dự phòng theo KPI 75% sao lại ra 8000, đề nghị tính lại")]
    kq = doi_chieu({"HS1": [_fc("PRC-01", "vuot_nguong"),
                            _fc("STO-03", "thieu_thong_tin")]}, labels)
    h = kq.ho_so[0]
    assert h.chi_tiet_nhan == [{"label_id": "l1", "rule_ref": ["PRC-01"],
                                "text": "Dự phòng theo KPI 75% sao lại ra 8000, "
                                        "đề nghị tính lại",
                                "loai": "khac", "trung": True, "thuc_chat": True,
                                "ma_khop": ["PRC-01"]}]
    assert h.ma_finding_loai == {"PRC-01": ["vuot_nguong"],
                                 "STO-03": ["thieu_thong_tin"]}
