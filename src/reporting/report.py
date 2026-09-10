"""C7 — gom, khử trùng, xếp ưu tiên và xuất báo cáo Markdown. THUẦN CODE (NT1).

Nhận `list[Finding]` từ mọi thành phần kiểm (C2/C4/C5) và dựng báo cáo tiếng Việt.
Không gọi LLM, không tính toán số liệu — chỉ tổ chức và trình bày.

Bốn việc C7 làm, theo thứ tự:

  1. **Lọc bỏ finding không có căn cứ (NT2)** — nhưng ĐẾM số bị loại, không im lặng.
  2. **Khử trùng** finding lặp (cùng quy tắc, cùng phân hệ, cùng nội dung).
  3. **Chặn finding Vòng 2 của mục đã trượt Vòng 1** (quyết định 2026-08-25): báo
     *"công thức CPU sai"* cho người **chưa viết phần CPU** là vô nghĩa và làm mất
     niềm tin (rủi ro R6). Nối qua `checklist_ref`.
  4. **Xếp ưu tiên** theo `severity`; trình bày **Vòng 1 trước** (theo thứ tự
     checklist I → II → III), **Vòng 2 sau** (tách "chưa đạt" / "chưa kiểm được").

Nhãn hiển thị (tên phần, tên mức độ, thứ tự checklist, câu cố vấn) nằm trong
`config/report_labels.yaml` — DỮ LIỆU người nghiệp vụ sửa được (tinh thần NT3),
không hard-code ở đây.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import yaml

from .finding import Finding, loc_bo_khong_can_cu

DEFAULT_LABELS_PATH = "config/report_labels.yaml"

# Giá trị mặc định an toàn: dùng khi `report_labels.yaml` thiếu khoá hoặc không có
# file. Báo cáo vẫn chạy được, chỉ kém đẹp — không được vì thiếu nhãn mà vỡ.
_FALLBACK = {
    "disclaimer": ("Đây là công cụ CỐ VẤN — người thẩm định vẫn là người quyết định "
                   "cuối cùng. Mọi phát hiện cần được kiểm chứng lại."),
    "demo_note": ("Dữ liệu Vòng 1 dựng tay để minh hoạ (C5 chưa có) — không dùng làm "
                  "kết quả thật."),
    "severity_order": ["critical", "major", "minor", "info"],
    "severity_labels": {"critical": "Nghiêm trọng", "major": "Quan trọng",
                        "minor": "Nhẹ", "info": "Thông tin"},
    "category_labels": {},
    "vong1_categories_truot": ["thieu_muc", "thieu_thong_tin"],
    "vong2_chua_dat": ["vuot_nguong", "sai_cong_thuc", "khong_nhat_quan"],
    "vong2_chua_kiem_duoc": ["thieu_thong_tin", "khong_kiem_chung_duoc"],
    "checklist_parts": [{"id": "I", "ten": "Checklist SR/ITBrain", "prefixes": ["CL-1."]},
                        {"id": "II", "ten": "Checklist tổng quan", "prefixes": ["CL-2."]},
                        {"id": "III", "ten": "Checklist chi tiết theo phân hệ",
                         "prefixes": ["CL-3."]}],
    "checklist_order": [],
}


@dataclass
class ReportLabels:
    """Nhãn hiển thị đã nạp, kèm truy cập tiện dụng."""

    data: dict = field(default_factory=dict)

    def _get(self, key):
        val = self.data.get(key)
        return _FALLBACK[key] if val is None else val

    @property
    def disclaimer(self) -> str:
        return str(self._get("disclaimer")).strip()

    @property
    def demo_note(self) -> str:
        return str(self._get("demo_note")).strip()

    @property
    def severity_order(self) -> list[str]:
        return list(self._get("severity_order"))

    @property
    def vong1_truot(self) -> set[str]:
        return set(self._get("vong1_categories_truot"))

    @property
    def vong2_chua_dat(self) -> set[str]:
        return set(self._get("vong2_chua_dat"))

    @property
    def vong2_chua_kiem(self) -> set[str]:
        return set(self._get("vong2_chua_kiem_duoc"))

    @property
    def anh_loai(self) -> dict:
        """Nhãn từng loại ảnh của C2. Thiếu khoá nào thì phần đó chỉ hiện tên mã."""
        return dict(self.data.get("anh_loai") or {})

    @property
    def parts(self) -> list[dict]:
        return list(self._get("checklist_parts"))

    @property
    def order_index(self) -> dict[str, int]:
        return {c: i for i, c in enumerate(self._get("checklist_order"))}

    def severity_label(self, sev: str) -> str:
        return self._get("severity_labels").get(sev, sev)

    def category_label(self, cat: str) -> str:
        return self._get("category_labels").get(cat, cat)

    def severity_rank(self, sev: str) -> int:
        order = self.severity_order
        return order.index(sev) if sev in order else len(order)


def load_labels(path: str = DEFAULT_LABELS_PATH) -> ReportLabels:
    try:
        with open(path, encoding="utf-8") as f:
            return ReportLabels(dict(yaml.safe_load(f) or {}))
    except FileNotFoundError:
        return ReportLabels({})


# ---------------------------------------------------------------------------
# Bước 2 — khử trùng
# ---------------------------------------------------------------------------
def khu_trung(findings: list[Finding]) -> tuple[list[Finding], int]:
    """Giữ lần xuất hiện ĐẦU của mỗi finding trùng. Trả (giữ lại, số đã gộp).

    "Trùng" = cùng quy tắc, cùng phân hệ, cùng nhóm, cùng câu mô tả — tức cùng một
    vấn đề được hai thành phần (vd C4 và C5) báo lại. Đếm số gộp, không im lặng.
    """
    seen: set = set()
    kept: list[Finding] = []
    for f in findings:
        key = (f.rule_ref, f.scope_key, f.category, f.finding)
        if key in seen:
            continue
        seen.add(key)
        kept.append(f)
    return kept, len(findings) - len(kept)


# ---------------------------------------------------------------------------
# Bước 3 — chặn Vòng 2 theo mục trượt Vòng 1
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MucTruot:
    """Một mục checklist đã trượt Vòng 1: mã + phạm vi bị chặn (`""` = cả hệ thống)."""

    code: str
    scope_key: str


def muc_truot_vong1(findings: list[Finding], categories_truot: set[str]) -> list[MucTruot]:
    """Các mục checklist trượt Vòng 1 — nguồn để chặn Vòng 2.

    Chỉ tính finding `vong == 1` thuộc nhóm "trượt" (mặc định `thieu_muc`,
    `thieu_thong_tin`). `khong_kiem_chung_duoc` ở Vòng 1 CỐ Ý không chặn: không
    biết thì không được coi như thiếu.
    """
    out: list[MucTruot] = []
    seen: set = set()
    for f in findings:
        if f.vong != 1 or f.category not in categories_truot:
            continue
        for code in f.checklist_ref:
            key = (code, f.scope_key)
            if key not in seen:
                seen.add(key)
                out.append(MucTruot(code, f.scope_key))
    return out


def _scope_bao_trum(blocked_scope: str, target: str) -> bool:
    """Phạm vi trượt Vòng 1 có bao trùm phạm vi của finding Vòng 2 không?

    - `""` (he_thong) chặn MỌI phạm vi.
    - Trượt ở "App" chặn cả "App" lẫn "App/SSD" (phan_he × công nghệ lưu trữ).
    """
    if blocked_scope == "":
        return True
    if blocked_scope == target:
        return True
    return target.startswith(blocked_scope + "/")


def chan_vong2(findings: list[Finding], truot: list[MucTruot]
               ) -> tuple[list[Finding], list[Finding]]:
    """(cho qua, bị chặn). Chỉ finding `vong == 2` mới bị xét chặn."""
    by_code: dict[str, list[str]] = {}
    for m in truot:
        by_code.setdefault(m.code, []).append(m.scope_key)

    thong: list[Finding] = []
    bi_chan: list[Finding] = []
    for f in findings:
        if f.vong != 2:
            thong.append(f)
            continue
        blocked = any(
            code in by_code and any(_scope_bao_trum(s, f.scope_key) for s in by_code[code])
            for code in f.checklist_ref
        )
        (bi_chan if blocked else thong).append(f)
    return thong, bi_chan


# ---------------------------------------------------------------------------
# Gom kết quả xử lý
# ---------------------------------------------------------------------------
@dataclass
class Report:
    """Cấu trúc trung gian đã xử lý xong — tách khỏi việc dựng Markdown để test được."""

    vong1: list[Finding]
    vong2_chua_dat: list[Finding]
    vong2_chua_kiem: list[Finding]
    vong2_tam_hoan: list[Finding]      # bị chặn vì mục Vòng 1 trượt
    khac: list[Finding]                # vong không phải 1/2 (vd cảnh báo C2)
    so_loc_khong_can_cu: int
    so_khu_trung: int
    ten_he_thong: str | None = None
    ma_pyc: str | None = None
    is_demo: bool = False


def xu_ly(findings: list[Finding], labels: ReportLabels, *,
          ten_he_thong: str | None = None, ma_pyc: str | None = None,
          is_demo: bool = False) -> Report:
    """Chạy trọn bốn bước C7, trả cấu trúc `Report` (chưa dựng Markdown)."""
    # 1 — NT2: lọc bỏ finding không có căn cứ, ĐẾM.
    co_can_cu, bo = loc_bo_khong_can_cu(findings)
    # 2 — khử trùng.
    co_can_cu, so_trung = khu_trung(co_can_cu)
    # 3 — chặn Vòng 2 theo mục trượt Vòng 1.
    truot = muc_truot_vong1(co_can_cu, labels.vong1_truot)
    thong, tam_hoan = chan_vong2(co_can_cu, truot)

    vong1 = [f for f in thong if f.vong == 1]
    vong2 = [f for f in thong if f.vong == 2]
    khac = [f for f in thong if f.vong not in (1, 2)]

    chua_dat = [f for f in vong2 if f.category in labels.vong2_chua_dat]
    chua_kiem = [f for f in vong2 if f.category in labels.vong2_chua_kiem]
    # Nhóm không rơi vào hai danh sách (cấu hình lạ) coi như "chưa kiểm được".
    con_lai = [f for f in vong2
               if f.category not in labels.vong2_chua_dat
               and f.category not in labels.vong2_chua_kiem]
    chua_kiem += con_lai

    return Report(
        vong1=_sap_xep_checklist(vong1, labels),
        vong2_chua_dat=_sap_xep_severity(chua_dat, labels),
        vong2_chua_kiem=_sap_xep_severity(chua_kiem, labels),
        vong2_tam_hoan=_sap_xep_checklist(tam_hoan, labels),
        khac=_sap_xep_severity(khac, labels),
        so_loc_khong_can_cu=len(bo),
        so_khu_trung=so_trung,
        ten_he_thong=ten_he_thong,
        ma_pyc=ma_pyc,
        is_demo=is_demo,
    )


# ---------------------------------------------------------------------------
# Sắp xếp
# ---------------------------------------------------------------------------
def _checklist_key(f: Finding, order_index: dict[str, int]) -> tuple:
    idxs = [order_index[c] for c in f.checklist_ref if c in order_index]
    primary = min(idxs) if idxs else len(order_index)      # mã lạ đẩy xuống cuối
    return (primary, f.scope_key, f.id)


def _sap_xep_checklist(findings: list[Finding], labels: ReportLabels) -> list[Finding]:
    idx = labels.order_index
    return sorted(findings, key=lambda f: _checklist_key(f, idx))


def _sap_xep_severity(findings: list[Finding], labels: ReportLabels) -> list[Finding]:
    return sorted(findings, key=lambda f: (labels.severity_rank(f.severity),
                                           f.rule_ref, f.scope_key, f.id))


def _part_of(f: Finding, parts: list[dict]) -> str | None:
    for code in f.checklist_ref:
        for p in parts:
            if any(code.startswith(pref) for pref in p.get("prefixes", [])):
                return p["id"]
    return None


# ---------------------------------------------------------------------------
# Dựng Markdown
# ---------------------------------------------------------------------------
MAX_PHAN_HE_LIET_KE = 12    # nhiều hơn thì cắt bớt và ghi rõ còn bao nhiêu


def gop_pham_vi(findings: list[Finding]) -> list[tuple[Finding, list[str]]]:
    """Gộp CÙNG MỘT vấn đề lặp trên nhiều phân hệ thành một mục.

    Đo trên báo cáo thật của VTracking (2026-09-10): **713 finding nhưng chỉ 99
    mã quy tắc**, và 718 dòng tiêu đề chỉ có **151 câu khác nhau**. Mỗi quy tắc
    lặp đúng 13 lần — 13 phân hệ, văn bản y hệt, chỉ khác `scope_key`. Riêng
    dòng «Căn cứ» chiếm **103 KB = 30%** báo cáo vì trích nguyên tiêu chí 713
    lần thay vì 99.

    `khu_trung` không đụng được vào đây: khoá của nó có `scope_key`, mà đúng là
    chúng khác nhau thật. Việc cần làm không phải khử trùng mà là **thôi lặp
    lại**: nói một lần, kèm danh sách phân hệ.

    KHÔNG phải giấu bớt (NT4): số lượng và tên từng phân hệ đều còn nguyên trong
    dòng «Phân hệ». Giữ đúng thứ tự xuất hiện đầu tiên.
    """
    nhom: dict[tuple, list[Finding]] = {}
    for f in findings:
        nhom.setdefault((f.rule_ref, f.category, f.finding, f.severity,
                         f.computed_evidence, f.suggestion), []).append(f)
    ra: list[tuple[Finding, list[str]]] = []
    for ds in nhom.values():
        scopes = [f.scope_key for f in ds if f.scope_key]
        ra.append((ds[0], scopes))
    return ra


def _dong_pham_vi(scopes: list[str]) -> str:
    """«Phân hệ: A, B, C (13 phân hệ)» — cắt bớt khi quá dài, nhưng NÓI RA."""
    n = len(scopes)
    if n <= MAX_PHAN_HE_LIET_KE:
        return ", ".join(scopes) + (f" ({n} phân hệ)" if n > 1 else "")
    con = n - MAX_PHAN_HE_LIET_KE
    return (", ".join(scopes[:MAX_PHAN_HE_LIET_KE])
            + f" … và {con} phân hệ nữa ({n} phân hệ)")


def _render_finding(f: Finding, labels: ReportLabels,
                    scopes: list[str] | None = None) -> list[str]:
    sev = labels.severity_label(f.severity)
    cat = labels.category_label(f.category)
    lines = [f"- **[{sev}]** {f.finding}  _(nhóm: {cat})_"]
    pham_vi = scopes if scopes is not None else ([f.scope_key] if f.scope_key else [])
    if pham_vi:
        lines.append(f"  - Phân hệ: {_dong_pham_vi(pham_vi)}")
    if f.location:
        lines.append(f"  - Vị trí: {f.location}")
    # Căn cứ (NT2): ưu tiên trích dẫn quy tắc, kèm mã checklist nếu có.
    can_cu = []
    if f.rule_ref:
        quote = f' — “{f.rule_quote}”' if f.rule_quote else ""
        can_cu.append(f"quy tắc `{f.rule_ref}`{quote}")
    if f.checklist_ref:
        can_cu.append("checklist " + ", ".join(f"`{c}`" for c in f.checklist_ref))
    if can_cu:
        lines.append("  - Căn cứ: " + "; ".join(can_cu))
    if f.computed_evidence:
        lines.append(f"  - Số liệu: {f.computed_evidence}")
    if f.suggestion:
        lines.append(f"  - Gợi ý: {f.suggestion}")
    return lines


MAX_O_BANG = 170            # cắt ô bảng cho khỏi tràn, có dấu … khi cắt


def _o(s: str, toi_da: int = MAX_O_BANG) -> str:
    """Một ô bảng Markdown: gộp xuống dòng, thoát `|`, cắt khi quá dài."""
    t = " ".join((s or "").split()).replace("|", "\\|")
    return t if len(t) <= toi_da else t[:toi_da - 1].rstrip() + "…"


def _tom_tat_can_xu_ly(rep: "Report", labels: ReportLabels) -> list[str]:
    """Mục đầu báo cáo: cái gì người viết phải SỬA, tách khỏi cái công cụ không đọc được.

    Đo trên báo cáo thật (VTracking, 2026-09-10): sau khi đã cắt 88% số dòng, ba
    phát hiện thật sự nói *"số của anh sai"* vẫn nằm ở **dòng 267/418** — sau 251
    dòng checklist Vòng 1. Thứ đáng đọc nhất bị chôn ở 60% độ sâu.

    KHÔNG đảo thứ tự các mục phía dưới: Vòng 1 đứng trước Vòng 2 là theo đúng
    trình tự thẩm định (mục Vòng 1 trượt thì chặn Vòng 2). Chỉ NÊU LÊN ĐẦU.
    """
    nhieu = labels.vong2_chua_kiem
    v1_thuc_chat = [f for f in rep.vong1 if f.category not in nhieu]
    v1_nhieu = sum(1 for f in rep.vong1 if f.category in nhieu)
    tong_nhieu = v1_nhieu + len(rep.vong2_chua_kiem)

    L = ["## Cần xử lý trước khi nộp", ""]
    if not rep.vong2_chua_dat and not v1_thuc_chat:
        L += ["Trong phần đọc được, công cụ **không tìm thấy chỗ nào tính sai** và "
              "**không thấy thành phần nào thiếu**.", ""]
    if rep.vong2_chua_dat:
        nhom = gop_pham_vi(rep.vong2_chua_dat)
        L += [f"### {len(nhom)} chỗ số liệu CHƯA ĐẠT", "",
              "_Công cụ tính lại được và thấy lệch. Đây là phần đáng xem trước nhất._",
              ""]
        for f, scopes in nhom:
            vt = f" — {f.location}" if f.location else ""
            L.append(f"1. **[{labels.severity_label(f.severity)}]** "
                     f"{_o(f.finding, 220)}{vt}")
        L += ["", "_Chi tiết kèm số liệu: mục «Vòng 2 → Chưa đạt» bên dưới._", ""]
    if v1_thuc_chat:
        L += [f"### {len(gop_pham_vi(v1_thuc_chat))} thành phần còn THIẾU", "",
              "Checklist Vòng 1 — xem mục «Vòng 1» bên dưới.", ""]
    if tong_nhieu:
        L += [f"### {tong_nhieu} mục công cụ CHƯA ĐỌC ĐƯỢC", "",
              "Xem bảng «Vòng 2 → Chưa kiểm được». **Đây không phải lỗi của bản "
              "sizing** — công cụ không trích được số để kiểm. Nếu tài liệu CÓ "
              "những số đó, trình bày chúng rõ hơn (thành bảng) sẽ giúp công cụ "
              "đọc được; nếu CHƯA có thì đó là phần còn thiếu thật.", ""]
    return L


def _bang_chua_kiem(findings: list[Finding], labels: ReportLabels) -> list[str]:
    """Mục «chưa kiểm được» dựng thành BẢNG, không phải danh sách đầy đủ.

    Mục này nói *công cụ không đọc được chỗ này*, KHÔNG nói *tài liệu sai chỗ
    này*. Với một tài liệu thật (VTracking, đo 2026-09-10) nó chiếm **586/724**
    phát hiện, và mỗi mục kéo theo nguyên văn tiêu chí quy tắc — riêng các dòng
    «Căn cứ» chiếm **30% toàn báo cáo**.

    Trích tiêu chí đầy đủ ở đây không giúp người viết sizing thêm được gì: họ
    chưa có gì để đối chiếu cả. Nên bảng giữ đủ **mã quy tắc · lý do · phạm vi**
    — tra lại nguyên văn thì xem `config/rules.yaml`, và câu dưới bảng nói rõ
    thế chứ không lặng lẽ bỏ.
    """
    if not findings:
        return ["_(không có mục nào thiếu thông tin để kiểm)_"]
    nhom = gop_pham_vi(findings)
    ra = [
        f"Công cụ **chưa đủ dữ liệu để kiểm** {len(findings)} lượt, gom thành "
        f"**{len(nhom)}** mục dưới đây. Đây là chỗ công cụ KHÔNG ĐỌC ĐƯỢC — "
        "không phải chỗ bản sizing sai.",
        "",
        "| Quy tắc | Mức | Vì sao chưa kiểm được | Phạm vi |",
        "|---|---|---|---|",
    ]
    for f, scopes in nhom:
        ra.append(f"| `{f.rule_ref or '—'}` | {labels.severity_label(f.severity)} "
                  f"| {_o(f.finding)} | {_o(_dong_pham_vi(scopes) or 'cả hệ thống', 60)} |")
    ra += ["", "_Nguyên văn tiêu chí từng quy tắc: xem `config/rules.yaml` theo mã ở "
           "cột đầu._"]
    return ra


def _render_list(findings: list[Finding], labels: ReportLabels,
                 empty: str = "_(không có)_") -> list[str]:
    if not findings:
        return [empty]
    out: list[str] = []
    for f, scopes in gop_pham_vi(findings):
        out += _render_finding(f, labels, scopes)
    return out


def to_markdown(rep: Report, labels: ReportLabels) -> str:
    L: list[str] = []
    ten = rep.ten_he_thong or "(chưa rõ tên hệ thống)"
    L.append(f"# Báo cáo tự kiểm bản định cỡ — {ten}")
    L.append("")
    if rep.ma_pyc:
        L.append(f"**Mã PYC:** {rep.ma_pyc}")
        L.append("")
    L.append(f"> ⚠️ **Công cụ cố vấn.** {labels.disclaimer}")
    L.append("")
    if rep.is_demo:
        L.append(f"> 🧪 **Demo.** {labels.demo_note}")
        L.append("")

    # --- Tổng quan ------------------------------------------------------
    L.append("## Tổng quan")
    L.append("")
    tong = (len(rep.vong1) + len(rep.vong2_chua_dat) + len(rep.vong2_chua_kiem)
            + len(rep.vong2_tam_hoan) + len(rep.khac))
    muc = sum(len(gop_pham_vi(ds)) for ds in
              (rep.vong1, rep.vong2_chua_dat, rep.vong2_chua_kiem,
               rep.vong2_tam_hoan, rep.khac))
    L.append(f"- Tổng số phát hiện: **{tong}**"
             + (f", trình bày thành **{muc}** mục (cùng một vấn đề lặp trên nhiều "
                "phân hệ được nói MỘT lần, kèm danh sách phân hệ)"
                if muc < tong else ""))
    L.append(f"- Vòng 1 (checklist thành phần): **{len(rep.vong1)}** mục chưa đạt")
    L.append(f"- Vòng 2 (Guideline): **{len(rep.vong2_chua_dat)}** chưa đạt · "
             f"**{len(rep.vong2_chua_kiem)}** chưa kiểm được · "
             f"**{len(rep.vong2_tam_hoan)}** tạm hoãn vì trượt Vòng 1")
    if rep.khac:
        L.append(f"- Cảnh báo khác: **{len(rep.khac)}**")
    L.append(f"- Đã lọc bỏ **{rep.so_loc_khong_can_cu}** phát hiện không có căn cứ (NT2)"
             + (f"; gộp **{rep.so_khu_trung}** phát hiện trùng hệt nhau."
                if rep.so_khu_trung else "."))
    L.append("")

    L += _tom_tat_can_xu_ly(rep, labels)

    # --- Vòng 1 ---------------------------------------------------------
    L.append("## Vòng 1 — Kiểm thành phần theo checklist")
    L.append("")
    L.append("_Vòng 1 chỉ hỏi: thành phần cần có đã có thông tin thực chất chưa? "
             "Chưa xét đúng/sai — việc đó ở Vòng 2._")
    L.append("")
    if not rep.vong1:
        L.append("Không có mục nào trượt Vòng 1.")
        L.append("")
    else:
        for p in labels.parts:
            trong_phan = [f for f in rep.vong1 if _part_of(f, labels.parts) == p["id"]]
            if not trong_phan:
                continue
            L.append(f"### {p['id']}. {p['ten']}")
            L.append("")
            L += _render_list(trong_phan, labels)
            L.append("")
        khong_ro = [f for f in rep.vong1 if _part_of(f, labels.parts) is None]
        if khong_ro:
            L.append("### Khác (chưa gắn phần checklist)")
            L.append("")
            L += _render_list(khong_ro, labels)
            L.append("")

    # --- Vòng 2 ---------------------------------------------------------
    L.append("## Vòng 2 — Kiểm cách tính theo Guideline")
    L.append("")
    L.append("### Chưa đạt")
    L.append("")
    L += _render_list(rep.vong2_chua_dat, labels, empty="_(không có phát hiện chưa đạt)_")
    L.append("")
    L.append("### Chưa kiểm được")
    L.append("")
    L += _bang_chua_kiem(rep.vong2_chua_kiem, labels)
    L.append("")

    # Tạm hoãn: thay các finding Vòng 2 bị chặn bằng dòng tóm tắt, nhóm theo phân hệ.
    L.append("### Tạm hoãn vì mục checklist tương ứng chưa có thông tin")
    L.append("")
    if not rep.vong2_tam_hoan:
        L.append("_(không có)_")
    else:
        L.append("Các kiểm tra Vòng 2 dưới đây **chưa chạy** vì mục checklist tương ứng "
                 "chưa có thông tin ở Vòng 1 — chưa đánh giá được, thiếu thông tin:")
        L.append("")
        theo_scope: dict[str, list[str]] = {}
        for f in rep.vong2_tam_hoan:
            key = f.scope_key or "(toàn hệ thống)"
            theo_scope.setdefault(key, [])
            if f.rule_ref and f.rule_ref not in theo_scope[key]:
                theo_scope[key].append(f.rule_ref)
        for scope in sorted(theo_scope):
            refs = ", ".join(f"`{r}`" for r in theo_scope[scope])
            L.append(f"- {scope}: {refs}")
    L.append("")

    # --- Cảnh báo khác --------------------------------------------------
    if rep.khac:
        L.append("## Cảnh báo khác")
        L.append("")
        L += _render_list(rep.khac, labels)
        L.append("")

    return "\n".join(L).rstrip() + "\n"


def build_report(findings: list[Finding], *, ten_he_thong: str | None = None,
                 ma_pyc: str | None = None, is_demo: bool = False,
                 labels: ReportLabels | None = None) -> str:
    """Đầu vào là `list[Finding]`, đầu ra là báo cáo Markdown tiếng Việt.

    `is_demo=True` khi dữ liệu (đặc biệt Vòng 1 từ C5 chưa có) được dựng tay —
    báo cáo sẽ ghi rõ là demo, không để ai nhầm là kết quả thật.
    """
    labels = labels or load_labels()
    rep = xu_ly(findings, labels, ten_he_thong=ten_he_thong, ma_pyc=ma_pyc,
                is_demo=is_demo)
    return to_markdown(rep, labels)
