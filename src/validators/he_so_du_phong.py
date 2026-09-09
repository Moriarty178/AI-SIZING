"""C4 · hệ số dự phòng trong công thức thông lượng FW/LB — THUẦN CODE (NT1).

Khuôn lỗi này người thẩm định nhắc **5 lần trên 5 hồ sơ** trong tập dev, và cả 5
nhãn đều nằm trong nhóm quyết định sau phán quyết 2026-09-09:

    «Tính thông lượng LB, FW chỉ có K dự phòng 1.2»          (VTracking)
    «Hệ số dự phòng thông lượng của FW = 1.2»                (Vtag)
    «Tính toán thông lượng FW, LB giao tiếp với các hệ thống/cụm khác»
                                       (campaign · Data Security VTT · PBH 4.0)

## Bằng chứng nó kiểm được, lấy từ hai bản của cùng một hồ sơ

VTracking bản bị nhận xét (trang 18) và bản sửa sau đó (trang 60):

    v1  = (125 + 32.5) * 3215/0.8*1.1 = 696,249 KB/s
    v2  = (125 + 32.5) * 3215/0.8*1.2 = 759,544 KB/s
    v1  = 17,284 * 6 = 103,704 KB/s          (không có hệ số nào)
    v2  = 17,284 * 6/0.8*1.2 = 155,556 KB/s

Tác giả tính ĐÚNG số học, chỉ dùng sai hằng số. Đó là thứ code bắt được trọn vẹn
mà không cần model: `cong_thuc.py` đọc phép tính tài liệu tự viết, ở đây chỉ soi
hằng số nhân.

## Vì sao phép kiểm cố ý HẸP

`1.1` là `error_margin` (Ksaisố) hợp lệ ở rất nhiều chỗ khác — máy chủ, lưu trữ.
Nói «thấy 1.1 là sai» sẽ báo bừa hàng loạt. Nên có bốn cửa, phải qua đủ cả bốn:

1. ô tự chứng minh được số học (`CongThucKhai.khop`);
2. biểu thức có `*` hoặc `/` — dòng cộng dồn các kết quả đã tính thì hệ số đã
   nằm trong chúng rồi, soi ở đó là báo sai;
3. ngữ cảnh nhắc THIẾT BỊ mạng (LB / cân bằng tải / FW / firewall);
4. ngữ cảnh nhắc ĐẠI LƯỢNG thông lượng / lưu lượng / băng thông.

Hệ số 1.2 KHÔNG hard-code: đọc từ `globals.port_reserve` của `config/rules.yaml`
(NT3). Sửa một chỗ trong YAML là đổi cả phép kiểm này.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..extraction.cong_thuc import CongThucKhai, doc_cong_thuc
from ..ingestion.docx_reader import DocxDocument
from ..reporting.finding import Finding
from .rules_loader import RuleSet

# «vLB», «LB», «Load Balancer», «cân bằng tải» · «FW», «firewall», «tường lửa».
# `v?LB` để bắt cả «vLB cho video streaming» của VTracking.
_RE_THIET_BI = re.compile(
    r"(?<![A-Za-z])v?LB(?![A-Za-z])|load\s*balanc|cân\s*bằng\s*tải"
    r"|(?<![A-Za-z])FW(?![A-Za-z])|firewall|tường\s*lửa", re.IGNORECASE)
_RE_DAI_LUONG = re.compile(
    r"thông\s*lượng|lưu\s*lượng|băng\s*thông|throughput", re.IGNORECASE)

# Mã quy tắc nhận phát hiện. Cả hai đều đã có sẵn trong `rules.yaml` với đúng
# công thức `… * port_reserve`; LBA-01 thậm chí đã ghi trong `message_template`:
# "Lưu ý hệ số dự phòng 1.2 hay bị bỏ sót".
MA_LB = "LBA-01"
MA_FW = "FWL-02"


@dataclass
class ThongKeHeSo:
    o_cong_thuc: int = 0        # ô có dạng «biểu thức = kết quả»
    khong_tu_khop: int = 0      # số học không khớp -> KHÔNG dùng làm căn cứ (NT4)
    ngoai_pham_vi: int = 0      # khớp nhưng không phải thông lượng FW/LB
    cong_don: int = 0           # dòng cộng dồn, cố ý bỏ qua
    trung_gian: int = 0         # kết quả bị dòng khác đem nhân hệ số -> chưa tới lượt
    dat: int = 0                # có đúng hệ số dự phòng
    thieu_he_so: int = 0        # KHÔNG có -> sinh finding
    luong_nghia: int = 0        # hai lối đọc số bất đồng -> NT4

    def tom_tat(self) -> str:
        return (f"{self.o_cong_thuc} ô công thức · {self.khong_tu_khop} không tự "
                f"khớp · {self.ngoai_pham_vi} ngoài phạm vi FW/LB · "
                f"{self.cong_don} cộng dồn · {self.trung_gian} bước trung gian · "
                f"{self.dat} đủ hệ số · "
                f"{self.thieu_he_so} thiếu hệ số · {self.luong_nghia} lưỡng nghĩa")


def _co_he_so_nho(ct: CongThucKhai) -> bool:
    """Có nhân với một hằng số trong khoảng (1, 2) — dáng dấp một hệ số dự phòng."""
    return any(1.0 < h < 2.0
               for h in ct.he_so_nhan.get(ct.quy_uoc[0], ()) if ct.quy_uoc)


def la_buoc_trung_gian(ct: CongThucKhai, cung_bang: list[CongThucKhai]) -> bool:
    """Kết quả của ô này có bị một ô KHÁC trong cùng bảng đem nhân hệ số không?

    Hồ sơ Mykid tách làm hai dòng — dòng gốc rồi mới dòng dự phòng:

        (958 * 8 * 630) / 1000000 = 4.83 Mbs
        4.83 * 1.1 = 5.31 Mbs        «Tổng băng thông cần thiết (Sau khi tính…)»

    Đòi hệ số ở dòng gốc là báo sai — nó chưa tới lượt. Nhưng cửa này phải HẸP:
    dòng «696,249 + 1,822,219 = 2,518,468» của VTracking cũng tiêu thụ kết quả
    dòng trên, mà ở đó hệ số ĐÁNG LẼ phải nằm sẵn trong từng dòng gốc rồi. Nên
    chỉ bỏ qua khi ô tiêu thụ có NHÂN hệ số, không phải khi nó chỉ cộng dồn.
    """
    if ct.gia_tri is None:
        return False
    for o in cung_bang:
        if o is ct or not o.khop or not _co_he_so_nho(o):
            continue
        if any(abs(s - ct.gia_tri) <= abs(ct.gia_tri) * 0.005 for s in o.so_hang()):
            return True
    return False


def _ngu_canh(ct: CongThucKhai) -> str:
    return " ".join((ct.nhan_dong, ct.section_title, ct.bang_text))


def la_thong_luong_mang(ct: CongThucKhai) -> bool:
    nc = _ngu_canh(ct)
    return bool(_RE_THIET_BI.search(nc) and _RE_DAI_LUONG.search(nc))


def _thiet_bi(ct: CongThucKhai) -> str:
    """`LBA-01` hay `FWL-02` — theo chỗ GẦN nhất nhắc tới thiết bị."""
    for phan in (ct.nhan_dong, ct.section_title, ct.bang_text):
        m = _RE_THIET_BI.search(phan or "")
        if m:
            return MA_FW if re.match(r"(?i)fw|firewall|tường", m.group()) else MA_LB
    return MA_LB


def kiem_he_so_du_phong(doc: DocxDocument, rules: RuleSet
                        ) -> tuple[list[Finding], ThongKeHeSo]:
    """Findings + thống kê. KHÔNG ném lỗi; không đủ căn cứ thì không xuất."""
    tk = ThongKeHeSo()
    ra: list[Finding] = []
    k = rules.globals.get("port_reserve")
    if k is None:
        return ra, tk

    moi = doc_cong_thuc(doc)
    theo_bang: dict[int, list[CongThucKhai]] = {}
    for c in moi:
        theo_bang.setdefault(c.bang_idx, []).append(c)

    for ct in moi:
        tk.o_cong_thuc += 1
        if not ct.khop:
            tk.khong_tu_khop += 1
            continue
        if not la_thong_luong_mang(ct):
            tk.ngoai_pham_vi += 1
            continue
        if not ct.co_nhan_chia:
            tk.cong_don += 1
            continue
        if la_buoc_trung_gian(ct, theo_bang.get(ct.bang_idx, [])):
            tk.trung_gian += 1
            continue

        ma = _thiet_bi(ct)
        r = rules.get(ma)
        co = ct.co_he_so(float(k))
        if co is None:
            tk.luong_nghia += 1
            ra.append(_finding_luong_nghia(ct, ma, r))
            continue
        if co:
            tk.dat += 1
            ra.append(_finding_dat(ct, ma, r, float(k)))
        else:
            tk.thieu_he_so += 1
            ra.append(_finding_thieu(ct, ma, r, float(k)))
    return ra, tk


def _chung(ct: CongThucKhai, ma: str, r, hau_to: str) -> dict:
    return dict(id=f"{ma}-hsdp-{hau_to}", rule_ref=ma,
                location=ct.location, scope_key=ct.nhan_dong,
                rule_quote=(r.name if r else ""),
                checklist_ref=list(r.checklist_ref) if r else [],
                source_doc=(r.source_doc if r else ""), vong=2)


def _da_co(ct: CongThucKhai) -> str:
    hs = ct.he_so_nhan.get(ct.quy_uoc[0], ()) if ct.quy_uoc else ()
    nho = [h for h in hs if 1.0 < h < 2.0]
    return ", ".join(f"×{h:g}" for h in nho)


def _finding_thieu(ct: CongThucKhai, ma: str, r, k: float) -> Finding:
    da_co = _da_co(ct)
    moi = ct.gia_tri * k if ct.gia_tri is not None else None
    return Finding(
        severity="critical", category="sai_cong_thuc",
        finding=(f"Công thức thông lượng {'firewall' if ma == MA_FW else 'cân bằng tải'} "
                 f"cho «{ct.nhan_dong or 'mục này'}» không nhân hệ số dự phòng "
                 f"{k:g}"
                 + (f"; công thức đang dùng {da_co}." if da_co
                    else "; không thấy hệ số dự phòng nào trong công thức.")),
        computed_evidence=(
            f"tài liệu ghi {ct.can_cu()}; tính lại đúng bằng {ct.ket_qua_khai}"
            f"{(' ' + ct.don_vi) if ct.don_vi else ''} nên số học không sai — "
            f"chỉ thiếu hệ số dự phòng {k:g}"
            + (f", nhân vào được {moi:,.0f}" if moi is not None else "")),
        suggestion=(f"Nhân thêm hệ số dự phòng {k:g} cho thông lượng thiết bị mạng"
                    + (f" (thay cho {da_co} đang dùng)" if da_co else "")
                    + (f": kết quả {moi:,.0f}"
                       f"{(' ' + ct.don_vi) if ct.don_vi else ''}."
                       if moi is not None else ".")),
        confidence="cao", **_chung(ct, ma, r, "thieu"))


def _finding_dat(ct: CongThucKhai, ma: str, r, k: float) -> Finding:
    return Finding(
        severity="info", category="dat_co_can_cu",
        finding=(f"Công thức thông lượng cho «{ct.nhan_dong or 'mục này'}» đã có "
                 f"hệ số dự phòng {k:g} và số học khớp."),
        computed_evidence=f"kiểm lại {ct.can_cu()} — đúng, có nhân ×{k:g}",
        confidence="cao", **_chung(ct, ma, r, "dat"))


def _finding_luong_nghia(ct: CongThucKhai, ma: str, r) -> Finding:
    return Finding(
        severity="minor", category="khong_kiem_chung_duoc",
        finding=(f"Không kết luận được hệ số dự phòng cho «{ct.nhan_dong or 'mục này'}»: "
                 "cách đọc dấu phẩy trong công thức cho hai kết quả khác nhau."),
        computed_evidence=f"{ct.can_cu()} — khớp với cả hai lối đọc số",
        suggestion="Ghi rõ hệ số dự phòng thành một thừa số riêng để tránh nhập nhằng.",
        confidence="thap", **_chung(ct, ma, r, "luongnghia"))
