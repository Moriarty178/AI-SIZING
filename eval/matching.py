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
    ghi_chu: str = ""


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

        theo_vong = findings_theo_vong.get(dossier) or {}
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
            else:
                h.truot_ids.append(l["label_id"])
        h.finding_khong_khop = sorted(ma_finding - ma_trung)
        kq.ho_so.append(h)
    return kq


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
         "",
         "> **Hai con số này KHÔNG thay thế nhau.** Con số dưới là con số nói với "
         "người dùng: so với người thẩm định, công cụ bắt được bao nhiêu. Con số trên "
         "chỉ nói bộ quy tắc hiện có được khai thác tới đâu.",
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
          "| Hồ sơ | Nhãn | Có `rule_ref` | Trúng | Recall | Mã finding không khớp nhãn |",
          "|---|---:|---:|---:|---:|---|"]
    for h in sorted(kq.ho_so, key=lambda x: -x.nhan_tong):
        r = f"{h.trung / h.nhan_co_rule:.0%}" if h.nhan_co_rule else "—"
        kk = ", ".join(h.finding_khong_khop[:6]) or "—"
        if h.ghi_chu:
            kk = f"⚠ {h.ghi_chu}"
        d.append(f"| {h.dossier[:38]} | {h.nhan_tong} | {h.nhan_co_rule} | "
                 f"{h.trung} | {r} | {kk} |")

    truot = Counter()
    for h in kq.ho_so:
        for _ in h.truot_ids:
            truot[h.dossier] += 1
    d += ["", f"Tổng nhãn trượt: **{sum(truot.values())}**.", ""]
    if meta:
        d += [f"Nguồn nhãn: `{meta.get('source', '?')}` · sinh ngày "
              f"{meta.get('generated', '?')}.", ""]
    return "\n".join(d)
