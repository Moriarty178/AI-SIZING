"""1.13 — Đối chiếu finding của Copilot với nhãn vàng từ PNX. THUẦN CODE.

Tách khỏi `run_eval.py` để test được offline: phần so khớp và tính recall không cần
model, chỉ phần chạy pipeline mới cần.

Cách tính lấy nguyên từ `data/eval_set.json` → `meta.scoring_note`, không tự nghĩ:

    Một finding TRÚNG nhãn khi `rule_ref` của finding nằm trong danh sách `rule_ref`
    của nhãn VÀ cùng hồ sơ.

Hai mẫu số, cố ý tách rời:

  **so với bộ quy tắc hiện có** — chỉ 469 nhãn có `rule_ref`. Trả lời: *trong những
  điều bộ quy tắc CÓ THỂ bắt, ta bắt được bao nhiêu?*
  **so với mọi yêu cầu** — cả 475 nhãn, gồm `khoang_trong` (yêu cầu thật mà bộ quy tắc
  chưa phủ) và `khong_neo_duoc`. Trả lời: *so với người thẩm định, ta bắt được bao
  nhiêu?* Con số này luôn thấp hơn, và nó mới là con số nói với người dùng.

⚠️ **Recall ở đây HÀO PHÓNG hơn thực tế.** 397/475 nhãn nhận gợi ý `rule_ref` của máy
nguyên xi, thường **dư mã** (xem `docs/0.7-nhan-vang-tu-pnx.md` mục 6). Nhãn càng nhiều
mã thì càng dễ có một mã trùng với finding. Phải nêu hạn chế này mỗi lần công bố số.

⚠️ **KHÔNG đo được false positive.** Finding không khớp nhãn nào KHÔNG có nghĩa là sai:
PNX chỉ ghi những điều người thẩm định CHỌN nhận xét, không phải mọi lỗi có trong tài
liệu. Và bản đã ký cũng không sạch (c360 ký với lỗi còn nguyên). Nên phần "không khớp"
chỉ để soi, không được gọi là false positive.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field

DUONG_DAN_EVAL = "data/eval_set.json"
DUONG_DAN_SPLIT = "data/eval_split.json"


# --- loại của NHÃN (không phải của finding) --------------------------------
# Cột `Thực chất` là SÀN và cố ý khắt khe: nó loại mọi cú trúng do finding
# "thiếu thông tin". Nhưng 87/155 nhãn dev (56%) BẢN THÂN CHÚNG là lời phàn nàn
# "chưa nêu / thiếu / bổ sung" — với những nhãn đó, một finding `thieu_thong_tin`
# là bắt ĐÚNG, và loại nó ra là phạt oan. Thước đo theo loại nối hai đầu lại:
# đòi finding phải CÙNG LOẠI với điều người thẩm định thật sự yêu cầu.
#
# Phân loại bằng từ khoá, THUẦN CODE và xem được — không hỏi LLM (NT1). Danh sách
# này là chỗ cần người nghiệp vụ soi lại; nó quyết định con số nên không được giấu.
TU_KHOA_THIEU = (
    "chưa nêu", "không nêu", "chưa có", "không có", "thiếu", "bổ sung",
    "chưa thuyết minh", "chưa làm rõ", "làm rõ", "chưa mô tả", "chưa cung cấp",
    "chưa đưa ra", "chưa trình bày",
)
# Nhãn quá ngắn thì không đủ chữ để biết người thẩm định đòi gì ("Tài nguyên ram",
# "Thiết bị lưu trữ"). KHÔNG đoán: tách riêng và nói ra, đúng NT4.
TU_TOI_DA_MANH_VUN = 5

# Câu MỆNH LỆNH đòi trình bày/bổ sung. Không chứa chữ "chưa nêu/thiếu" nên rơi vào
# nhóm «yêu cầu khác», mà nhóm ấy lại từ chối finding `thieu_thong_tin` — chính là
# câu trả lời ĐÚNG cho chúng. Ví dụ thật, cùng gắn mã ARC-03 (`so_may_du_phong >= 1`):
#   «Lập bảng giá trị đề xuất số lượng máy chủ cụ thể…, lưu ý giá trị N+1»
#   «Đề xuất cấu hình cần có ít nhất N+1 server để đảm bảo HA dự phòng»
# Người thẩm định đang nói *anh chưa trình bày*, không nói *số của anh sai*.
#
# Đo ở B1 2026-09-07: 20/57 nhãn (35%) nhóm «yêu cầu khác» thuộc loại này.
#
# TÁCH RIÊNG chứ KHÔNG gộp vào «thiếu»: gộp sẽ đẩy 20 nhãn từ nhóm ta đạt 4% sang
# nhóm ta đạt 94%, tức tự sửa thước đo cho con số của mình đẹp lên. Người thẩm định
# phải là người xác nhận chúng thuộc về đâu.
TU_KHOA_MENH_LENH = (
    "lập bảng", "đề xuất", "cần có", "ghi rõ", "ghi chú", "thuyết minh", "nêu rõ",
    "mô tả rõ", "cung cấp", "đưa vào", "xây dựng",
)
# CỐ Ý không có «tính lại» / «tính toán lại»: đó là chất vấn con số SAI, không phải
# đòi bổ sung thông tin. «Dự phòng theo KPI 75% sao lại ra 8000, đề nghị tính lại»
# là việc phải kiểm bằng số — xếp nhầm nó sang nhóm mệnh lệnh là tự cho điểm.


def loai_nhan(text: str | None) -> str:
    """`thieu` | `menh_lenh` | `khac` | `manh_vun` — yêu cầu thuộc loại nào."""
    t = (text or "").strip()
    thap = t.lower()
    if any(k in thap for k in TU_KHOA_THIEU):
        return "thieu"
    if len(t.split()) <= TU_TOI_DA_MANH_VUN:
        return "manh_vun"
    if any(k in thap for k in TU_KHOA_MENH_LENH):
        return "menh_lenh"
    return "khac"


@dataclass
class KetQuaHoSo:
    dossier: str
    file_da_dung: str = ""
    nhan_tong: int = 0
    nhan_co_rule: int = 0
    trung: int = 0
    trung_ids: list[str] = field(default_factory=list)
    truot_ids: list[str] = field(default_factory=list)
    finding_khong_khop: list[str] = field(default_factory=list)
    # Số finding nhóm ĐẠT đã bị loại khỏi phép chấm. Đếm ra chứ không lọc im lặng.
    finding_dat_loai_tru: int = 0
    # Trong số `trung`, bao nhiêu nhãn trúng nhờ một finding THỰC CHẤT — tức không
    # phải chỉ vì công cụ nói "không tìm thấy trường này". Xem `CAT_MEM`.
    trung_thuc_chat: int = 0
    # Chấm theo LOẠI nhãn: nhãn "thiếu" trúng bằng finding `thieu_thong_tin` là
    # đúng; nhãn "khác" đòi finding thực chất. Nhãn `manh_vun` KHÔNG vào mẫu số.
    theo_loai_mau: dict = field(default_factory=dict)
    theo_loai_trung: dict = field(default_factory=dict)
    ghi_chu: str = ""


# Loại finding KHÔNG tự nó chứng minh công cụ bắt được điều gì: nó chỉ nói công cụ
# không đọc được chỗ đó. Một finding như vậy vẫn hợp lệ với người dùng (và đúng NT4),
# nhưng dùng nó để tính recall thì thước đo THƯỞNG CHO VIỆC TRÍCH XUẤT THẤT BẠI:
# càng ít trường đọc được thì càng nhiều mã quy tắc được nhắc, càng dễ trùng nhãn.
#
# Đo được ở lượt B1 2026-09-07: trên MỘT hồ sơ, pipeline nhắc tới 120–124 trong 151
# quy tắc, với 96/123 finding thuộc `thieu_thong_tin` và đúng 1 finding `vuot_nguong`.
# Hệ quả: model GIẢ (sinh bừa) đạt 99,4% còn model THẬT đạt 88,4% trên cùng thước đo.
CAT_MEM = frozenset({"thieu_thong_tin", "khong_kiem_chung_duoc"})

# Finding nhóm ĐẠT bị LOẠI HẲN khỏi phép chấm recall (người dùng chốt sinh chúng
# 2026-09-09, cho BÁO CÁO).
#
# Vì sao loại: một nhãn PNX là điều người thẩm định thấy SAI. Đếm một lượt ĐẠT là
# "trúng" nhãn ấy nghĩa là công cụ nói «chỗ này ổn» còn người thẩm định nói «chỗ
# này hỏng», mà ta vẫn ghi điểm. Đó đúng là kiểu tự sửa thước đo cho số mình đẹp
# lên mà `CLAUDE.md` cấm, và cùng họ với lỗi đã phát hiện ngày 2026-09-07 (thước
# đo thưởng cho trích xuất thất bại).
#
# Chúng cũng KHÔNG bị tính vào `finding_khong_khop`: một lượt ĐẠT không phải dấu
# hiệu công cụ báo bừa.
#
# Nếu người thẩm định về sau muốn ĐẠT-có-căn-cứ được tính cho nhóm nhãn "bổ sung
# sở cứ", đó là quyết định của họ, KHÔNG phải của công cụ — sửa ở đây và nói rõ
# trong báo cáo.
CAT_KHONG_TINH_RECALL = frozenset({"dat_co_can_cu"})


@dataclass
class KetQuaEval:
    ho_so: list[KetQuaHoSo] = field(default_factory=list)
    tap: str = "dev"
    canh_bao: list[str] = field(default_factory=list)
    # Bộ lọc đã dùng khi chạy. PHẢI ghi vào báo cáo: một lượt chạy lọc nhóm cho recall
    # thấp hơn hẳn, và nếu báo cáo không nói vì sao thì sẽ có người trích con số đó
    # như thể là recall thật.
    bo_loc: dict = field(default_factory=dict)
    # Lượt DIỄN TẬP bằng model giả. Phải nằm ngay TIÊU ĐỀ, không phải ở mục cảnh báo
    # cuối: con số recall nằm ở đầu báo cáo, ai liếc qua hoặc chép phần đầu ra ngoài
    # sẽ không thấy dấu đóng nếu nó ở dưới.
    dien_tap: bool = False

    @property
    def da_loc(self) -> bool:
        return any(v for v in self.bo_loc.values())

    @property
    def nhan_co_rule(self) -> int:
        return sum(h.nhan_co_rule for h in self.ho_so)

    @property
    def nhan_tong(self) -> int:
        return sum(h.nhan_tong for h in self.ho_so)

    @property
    def trung(self) -> int:
        return sum(h.trung for h in self.ho_so)

    @property
    def trung_thuc_chat(self) -> int:
        return sum(h.trung_thuc_chat for h in self.ho_so)

    @property
    def recall_thuc_chat(self) -> float:
        """Recall khi chỉ tính cú trúng do một finding THỰC CHẤT tạo ra."""
        return (self.trung_thuc_chat / self.nhan_co_rule) if self.nhan_co_rule else 0.0

    @property
    def theo_loai_mau(self) -> dict:
        r: dict = {}
        for h in self.ho_so:
            for k, v in h.theo_loai_mau.items():
                r[k] = r.get(k, 0) + v
        return r

    @property
    def theo_loai_trung(self) -> dict:
        r: dict = {}
        for h in self.ho_so:
            for k, v in h.theo_loai_trung.items():
                r[k] = r.get(k, 0) + v
        return r

    @property
    def recall_theo_loai(self) -> float:
        """Mẫu số BỎ nhãn `manh_vun` — không đủ chữ để biết yêu cầu thuộc loại nào."""
        mau = sum(v for k, v in self.theo_loai_mau.items() if k != "manh_vun")
        trung = sum(v for k, v in self.theo_loai_trung.items() if k != "manh_vun")
        return trung / mau if mau else 0.0

    @property
    def recall_quy_tac(self) -> float:
        return self.trung / self.nhan_co_rule if self.nhan_co_rule else 0.0

    @property
    def recall_moi_yeu_cau(self) -> float:
        return self.trung / self.nhan_tong if self.nhan_tong else 0.0


def nap_nhan(tap: str = "dev", *, duong_dan: str = DUONG_DAN_EVAL,
             duong_dan_split: str = DUONG_DAN_SPLIT) -> list[dict]:
    """Nhãn của một tập. `tap='test'` GIỮ KÍN — chỉ chạy một lần ở 3.6."""
    labels = json.load(open(duong_dan, encoding="utf-8"))["labels"]
    if tap == "tat_ca":
        return labels
    split = json.load(open(duong_dan_split, encoding="utf-8"))
    ten = {d["dossier"] for d in split[tap]["dossiers"]}
    return [l for l in labels if l["dossier"] in ten]


def _findings_cua_vong(theo_vong: dict[int, list], vong: int) -> list:
    """Finding của đúng vòng; thiếu vòng đó thì lùi về vòng gần nhất ĐÃ CHẠY.

    Lùi xuống chứ không lùi lên: bản của vòng trước là bản CHƯA sửa theo nhận xét
    của vòng đó, nên nó vẫn còn lỗi — đoán theo hướng này an toàn hơn.
    """
    if vong in theo_vong:
        return theo_vong[vong]
    truoc = [v for v in theo_vong if v < vong]
    return theo_vong[max(truoc)] if truoc else theo_vong[min(theo_vong)]


def doi_chieu(findings_theo_ho_so: dict[str, list], labels: list[dict], *,
              tap: str = "dev", file_da_dung: dict[str, str] | None = None,
              findings_theo_vong: dict[str, dict[int, list]] | None = None
              ) -> KetQuaEval:
    """So khớp theo `meta.scoring_note`. `findings_theo_ho_so`: hồ sơ → list[Finding].

    `findings_theo_vong` (tuỳ chọn): hồ sơ → {vòng: findings}. Khi có, nhãn của
    vòng N được chấm trên finding của ĐÚNG bản mà PNX vòng N đã đọc — gỡ thiên
    lệch phiên bản (hạn chế số 6). Không có thì mọi nhãn chấm chung một bản, và
    `run_eval` phải nói ra số nhãn bị chấm sai bản.
    """
    file_da_dung = file_da_dung or {}
    findings_theo_vong = findings_theo_vong or {}
    theo_ho_so: dict[str, list[dict]] = {}
    for l in labels:
        theo_ho_so.setdefault(l["dossier"], []).append(l)

    kq = KetQuaEval(tap=tap)
    for dossier, ds in sorted(theo_ho_so.items()):
        fs = findings_theo_ho_so.get(dossier)
        h = KetQuaHoSo(dossier=dossier, nhan_tong=len(ds),
                       nhan_co_rule=sum(1 for l in ds if l.get("rule_ref")),
                       file_da_dung=file_da_dung.get(dossier, ""))
        if fs is None:
            # KHÔNG chạy được hồ sơ này. Đếm vào mẫu số (nếu bỏ ra thì recall sẽ đẹp
            # lên một cách giả tạo), nhưng ghi rõ lý do.
            h.ghi_chu = "chưa chạy được (không tìm thấy bản .docx hoặc lỗi khi chạy)"
            h.truot_ids = [l["label_id"] for l in ds if l.get("rule_ref")]
            kq.ho_so.append(h)
            continue

        h.finding_dat_loai_tru = sum(
            1 for f in fs if getattr(f, "category", "") in CAT_KHONG_TINH_RECALL)
        fs = [f for f in fs
              if getattr(f, "category", "") not in CAT_KHONG_TINH_RECALL]
        theo_vong = {v: [f for f in lst
                         if getattr(f, "category", "") not in CAT_KHONG_TINH_RECALL]
                     for v, lst in (findings_theo_vong.get(dossier) or {}).items()}
        ma_finding = {f.rule_ref for f in fs if f.rule_ref}
        ma_trung: set[str] = set()
        for l in ds:
            refs = set(l.get("rule_ref") or [])
            if not refs:
                continue                      # khoang_trong / khong_neo_duoc
            if theo_vong:
                fs_l = _findings_cua_vong(theo_vong, int(l.get("lan_nhan_xet") or 1))
                ma_l = {f.rule_ref for f in fs_l if f.rule_ref}
            else:
                ma_l = ma_finding
            chung = refs & ma_l
            if chung:
                h.trung += 1
                h.trung_ids.append(l["label_id"])
                ma_trung |= chung
                nguon = fs_l if theo_vong else fs
                thuc_chat = any(f.rule_ref in chung and f.category not in CAT_MEM
                                for f in nguon)
                if thuc_chat:
                    h.trung_thuc_chat += 1
                lo = loai_nhan(l.get("text"))
                h.theo_loai_mau[lo] = h.theo_loai_mau.get(lo, 0) + 1
                # Nhãn "thiếu": finding "thiếu thông tin" là bắt ĐÚNG loại.
                # Nhãn "khác": phải có finding thực chất mới tính.
                # `menh_lenh` chấm như «thiếu» — nhưng ĐẾM RIÊNG để thấy được nó
                # đóng góp bao nhiêu, và để người thẩm định xác nhận cách xếp.
                if lo in ("thieu", "menh_lenh") or (lo == "khac" and thuc_chat):
                    h.theo_loai_trung[lo] = h.theo_loai_trung.get(lo, 0) + 1
            else:
                h.truot_ids.append(l["label_id"])
                lo = loai_nhan(l.get("text"))
                h.theo_loai_mau[lo] = h.theo_loai_mau.get(lo, 0) + 1
        h.finding_khong_khop = sorted(ma_finding - ma_trung)
        kq.ho_so.append(h)
    return kq


def _bang_loai(kq: "KetQuaEval") -> str:
    """Bảng nhỏ: mỗi loại nhãn được chấm trên bao nhiêu và trúng bao nhiêu."""
    ten = {"thieu": "«chưa nêu / thiếu» — finding `thieu_thong_tin` tính là ĐÚNG",
           "menh_lenh": "«lập bảng / đề xuất / ghi rõ» — đòi trình bày, CHỜ XÁC NHẬN",
           "khac": "thật sự đòi TÍNH hoặc SO số — đòi finding thực chất",
           "manh_vun": "quá ngắn, không biết đòi gì — KHÔNG vào mẫu số"}
    mau, trung = kq.theo_loai_mau, kq.theo_loai_trung
    d = ["| Loại nhãn | Nhãn | Trúng | Recall |", "|---|---:|---:|---:|"]
    for k in ("thieu", "menh_lenh", "khac", "manh_vun"):
        m = mau.get(k, 0)
        if not m:
            continue
        t = trung.get(k, 0)
        r = "—" if k == "manh_vun" else f"{t / m:.0%}"
        d.append(f"| {ten[k]} | {m} | {t if k != 'manh_vun' else '—'} | {r} |")
    return "\n".join(d)


def bang_markdown(kq: KetQuaEval, *, meta: dict | None = None) -> str:
    tieu_de = (f"# ⚠️ DIỄN TẬP (MODEL GIẢ) — tập `{kq.tap}`" if kq.dien_tap
               else f"# Kết quả eval — tập `{kq.tap}`")
    d = [tieu_de, ""]
    d += [
         "| | Giá trị |", "|---|---:|",
         f"| Hồ sơ | {len(kq.ho_so)} |",
         f"| Nhãn (mọi yêu cầu) | {kq.nhan_tong} |",
         f"| Nhãn có `rule_ref` | {kq.nhan_co_rule} |",
         f"| Trúng | **{kq.trung}** |",
         f"| **Recall so với bộ quy tắc hiện có** | **{kq.recall_quy_tac:.1%}** |",
         f"| **Recall so với mọi yêu cầu** | **{kq.recall_moi_yeu_cau:.1%}** |",
         f"| Trúng nhờ finding THỰC CHẤT | {kq.trung_thuc_chat} |",
         f"| **Recall thực chất** (sàn) | **{kq.recall_thuc_chat:.1%}** |",
         f"| **Recall theo LOẠI nhãn** | **{kq.recall_theo_loai:.1%}** |",
         "",
         "> **Hai con số này KHÔNG thay thế nhau.** Con số dưới là con số nói với "
         "người dùng: so với người thẩm định, công cụ bắt được bao nhiêu. Con số trên "
         "chỉ nói bộ quy tắc hiện có được khai thác tới đâu.",
         "",
         "> **Recall thực chất là SÀN, và là con số đáng tin hơn.** Một nhãn được "
         "tính trúng chỉ vì công cụ nói *\"không tìm thấy trường này\"* thì chưa "
         "chứng minh được điều gì — mà công cụ nói câu đó cho gần như mọi quy "
         "tắc. Bằng chứng: ở lượt B1 2026-09-07, model GIẢ (sinh bừa) đạt "
         "**99,4%** trên thước đo chính, cao hơn model thật (88,4%), vì trích "
         "xuất càng tệ thì càng nhiều cảnh báo \"thiếu\" và càng dễ trùng nhãn. "
         "Cột `Thực chất` không có tính chất ngược đời đó.",
         "",
         "> **Recall theo LOẠI nhãn** đòi finding CÙNG LOẠI với điều người thẩm "
         "định yêu cầu: nhãn *\"chưa nêu / thiếu\"* trúng bằng finding `thieu_thong_tin` "
         "là đúng, nhãn còn lại phải có finding thực chất. Nhãn quá ngắn để biết đòi gì "
         "(`manh_vun`) bị BỎ khỏi mẫu số chứ không đoán. Việc phân loại dùng từ khoá "
         "thuần code — xem `TU_KHOA_THIEU` trong `eval/matching.py`, **danh sách này "
         "cần người nghiệp vụ soi lại vì nó quyết định con số**.",
         "",
         "> ⚠️ **Nhóm «chưa nêu / thiếu» gần như CHO KHÔNG.** Công cụ sinh cảnh "
         "báo `thieu_thong_tin` cho hầu hết quy tắc, nên model GIẢ cũng đạt **99%** "
         "ở nhóm này — nhưng chỉ **12%** ở nhóm «yêu cầu khác». Vì vậy **nhóm «yêu "
         "cầu khác» mới là chỗ phân biệt được công cụ tốt với công cụ sinh bừa**; "
         "đọc con số tổng mà bỏ qua tách nhóm là đọc sai.",
         "",
         _bang_loai(kq),
         "",
         "## Hạn chế phải nêu kèm mỗi khi công bố",
         "",
         "1. **Recall ở đây hào phóng hơn thực tế** — 397/475 nhãn nhận gợi ý "
         "`rule_ref` của máy nguyên xi, thường dư mã; nhãn càng nhiều mã càng dễ trúng.",
         "2. **Không đo được false positive.** Finding không khớp nhãn KHÔNG phải là "
         "sai: PNX chỉ ghi những điều người thẩm định chọn nhận xét, và bản đã ký cũng "
         "không sạch. Cột dưới chỉ để soi.",
         "3. **Nhãn chưa qua kiểm định độc lập** — gợi ý và phán quyết cùng do một tác "
         "nhân AI (`docs/0.7-nhan-vang-tu-pnx.md` mục 6).",
         ""]
    if kq.da_loc:
        d[1:1] = ["", "> ⚠️ **LƯỢT CHẠY NÀY CÓ LỌC — con số dưới KHÔNG so sánh được với "
                  "một lượt chạy đầy đủ và KHÔNG được trích như recall thật.** Bộ lọc: "
                  + " · ".join(f"`{k}` = {v}" for k, v in kq.bo_loc.items() if v), ""]
    if kq.dien_tap:
        # Chèn SAU khối `da_loc` để nổi lên trên cùng: dấu đóng phải nằm ngay dưới
        # tiêu đề, không phải dưới bảng recall. Người liếc qua hoặc chép phần đầu
        # báo cáo ra ngoài chỉ nhìn thấy vài dòng đầu.
        d[1:1] = ["", "> **KHÔNG PHẢI KẾT QUẢ THẬT.** Lượt chạy này dùng model giả "
                  "lập, mọi con số recall dưới đây là VÔ NGHĨA về mặt chất lượng. "
                  "Mục đích duy nhất: xác nhận đường chạy không vỡ TRƯỚC khi tiêu "
                  "giờ mạng nội bộ."]
    if kq.canh_bao:
        d += ["## Cảnh báo khi chạy", ""] + [f"- {c}" for c in kq.canh_bao] + [""]

    d += ["## Theo hồ sơ", "",
          "| Hồ sơ | Nhãn | Có `rule_ref` | Trúng | Thực chất | Recall | "
          "Mã finding không khớp nhãn |",
          "|---|---:|---:|---:|---:|---:|---|"]
    for h in sorted(kq.ho_so, key=lambda x: -x.nhan_tong):
        r = f"{h.trung / h.nhan_co_rule:.0%}" if h.nhan_co_rule else "—"
        kk = ", ".join(h.finding_khong_khop[:6]) or "—"
        if h.ghi_chu:
            kk = f"⚠ {h.ghi_chu}"
        d.append(f"| {h.dossier[:38]} | {h.nhan_tong} | {h.nhan_co_rule} | "
                 f"{h.trung} | {h.trung_thuc_chat} | {r} | {kk} |")

    truot = Counter()
    for h in kq.ho_so:
        for _ in h.truot_ids:
            truot[h.dossier] += 1
    d += ["", f"Tổng nhãn trượt: **{sum(truot.values())}**.", ""]
    if meta:
        d += [f"Nguồn nhãn: `{meta.get('source', '?')}` · sinh ngày "
              f"{meta.get('generated', '?')}.", ""]
    return "\n".join(d)
