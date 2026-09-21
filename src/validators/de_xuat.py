"""5.9 bước 2 — ĐỀ XUẤT sửa quy tắc, kiểm tự động trước khi người chốt áp tay.

Vì sao không ghi thẳng đè `config/rules.yaml`: một lần sửa sai âm thầm đổi mọi lượt
thẩm định về sau cho tất cả mọi người, và không có đường lùi khi quy tắc sai đã chạy
vài chục hồ sơ. Đường đi ở đây là **đề xuất → kiểm tự động → người chốt áp**.

## Vì sao công cụ KHÔNG tự ghi lại file

`rules.yaml` dài 4605 dòng mà **phần lớn là chú thích** — đó là tài liệu hướng dẫn
cho người nghiệp vụ, không phải rác. `yaml.safe_dump` một `dict` đã nạp rồi ghi đè
sẽ **xoá sạch mọi chú thích** và xáo lại thứ tự khoá. Nên ở đây chỉ làm việc trên
**nguyên văn KHỐI của một quy tắc**: đọc ra đúng đoạn văn bản ấy, nhận lại đoạn thay
thế do Admin viết, và ghép thử vào bản sao trong bộ nhớ để kiểm. Việc áp thật là
người sửa file rồi commit — có `git diff` làm đường lùi, thứ một bảng CSDL không có.

## Kiểm cái gì

Chặn (`loi`) — đề xuất không được phép áp:

1. khối mới phải là YAML hợp lệ, đúng hình dạng một phần tử của `rules:`;
2. `id` KHÔNG được đổi — `rules.yaml` ghi rõ "KHÔNG đổi mã đã dùng, sẽ làm hỏng liên
   kết với eval set", mà mã ấy còn nằm trong `rule_ref` của mọi finding đã lưu (5.1);
3. ghép vào cả file phải nạp được thành `RuleSet` — tức qua mọi bất biến của bộ nạp
   (trùng mã, `see_also` trỏ bậy, kiểu sai);
4. tập mã quy tắc trước/sau phải Y HỆT — một đề xuất sửa MỘT quy tắc mà làm mất hoặc
   thêm quy tắc khác là dấu hiệu khối văn bản bị cắt/ghép hỏng;
5. mọi biểu thức của CẢ bộ quy tắc phải còn phân tích cú pháp được bằng asteval
   (không chỉ của quy tắc vừa sửa — một khối ghép hỏng làm lệch thụt đầu dòng của
   quy tắc kế bên và biến `check` của nó thành rác).

Cảnh báo (`canh_bao`) — vẫn áp được nhưng phải đọc trước khi bấm:

- quy tắc chuyển từ đánh giá được sang KHÔNG đánh giá được (hoặc ngược lại);
- đổi `enabled`, `type`, `scope`, `severity` — bốn trường đổi phạm vi chấm chứ không
  đổi ngưỡng, nên dễ sửa mà không nhận ra ảnh hưởng.

**Không kiểm ở đây: eval set.** Chạy eval cần model và cả kho hồ sơ thật, mất hàng
giờ — không thể là cổng đồng bộ trong một lời gọi API. Điểm dừng ở `.cache/eval` cũng
không tái dùng được vì nó lưu KẾT QUẢ finding, không lưu phần trích xuất. Nên bằng
chứng eval là một trường RIÊNG của đề xuất, do người chạy rồi gắn vào; `kiem_de_xuat`
không bao giờ nói một đề xuất "đạt" theo nghĩa "đã đo eval".
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

import yaml
from asteval import Interpreter

from .rules_loader import RuleSet

# Mọi dòng mở đầu một quy tắc trong `rules.yaml` đều thụt đúng 2 dấu cách (đo
# 2026-09-21: 151/151 dòng). Neo theo con số ấy chứ không nhận thụt đầu dòng tuỳ ý —
# nhận bừa thì một `- id:` nằm trong ví dụ ở phần chú thích cũng bị coi là quy tắc.
THUT = "  "
_DAU_KHOI = re.compile(rf"^{THUT}- id:\s*(?P<ma>[^\s#]+)\s*(?:#.*)?$")


def _la_dau_khoi_khac(dong: str) -> bool:
    """Dòng mở đầu một mục khác của `rules:`, hoặc một khoá cấp cao hơn.

    Nhận cả `  -` đứng một mình (gạch đầu dòng ở dòng riêng, nội dung ở dòng sau) —
    YAML chấp nhận dạng đó. Chỉ so `startswith("  - ")` thì dạng ấy lọt lưới và khối
    của quy tắc TRƯỚC nó nuốt luôn nó; lúc ghép lại là mất hẳn một quy tắc.
    """
    if not dong.strip():
        return False
    thut = len(dong) - len(dong.lstrip())
    if thut < len(THUT):
        return True
    con_lai = dong[len(THUT):]
    return con_lai == "-" or con_lai.startswith("- ")


def pham_vi_khoi(van: str, ma: str) -> tuple[int, int] | None:
    """(dòng đầu, dòng cuối) của khối quy tắc `ma`, theo chỉ số dòng 0-based.

    `None` khi không tìm thấy. Dòng trắng ở cuối khối bị loại ra — để `diff` của hai
    đề xuất liên tiếp không lệch nhau chỉ vì một dòng trắng.
    """
    dong = van.splitlines()
    dau = next((i for i, d in enumerate(dong)
                if (m := _DAU_KHOI.match(d)) and m.group("ma") == ma), None)
    if dau is None:
        return None
    cuoi = next((i for i in range(dau + 1, len(dong)) if _la_dau_khoi_khac(dong[i])),
                len(dong))
    while cuoi > dau + 1 and not dong[cuoi - 1].strip():
        cuoi -= 1
    return dau, cuoi


def doc_khoi(van: str, ma: str) -> str:
    """Nguyên văn khối của một quy tắc, CÒN NGUYÊN chú thích và thụt đầu dòng."""
    pv = pham_vi_khoi(van, ma)
    if pv is None:
        raise KeyError(ma)
    return "\n".join(van.splitlines()[pv[0]:pv[1]]) + "\n"


def ghep_khoi(van: str, ma: str, khoi_moi: str) -> str:
    """Bản sao của cả file với khối của `ma` thay bằng `khoi_moi`. Không ghi đĩa."""
    pv = pham_vi_khoi(van, ma)
    if pv is None:
        raise KeyError(ma)
    dong = van.splitlines()
    moi = khoi_moi.rstrip("\n").splitlines()
    return "\n".join(dong[:pv[0]] + moi + dong[pv[1]:]) + "\n"


def bieu_thuc(rs: RuleSet) -> list[tuple[str, str, str]]:
    """(mã quy tắc, tên trường, biểu thức) của cả bộ — mọi chỗ asteval sẽ chạy."""
    return [(r.id, ten, bt)
            for r in rs.rules
            for ten, bt in (("check", r.check), ("formula", r.formula),
                            ("applies_when", r.applies_when)) if bt]


def bieu_thuc_hong(rs: RuleSet) -> list[str]:
    """Biểu thức KHÔNG còn phân tích cú pháp được. Chỉ phân tích, KHÔNG chạy.

    Chạy thử thì mọi biểu thức đều "hỏng" vì thiếu biến (`cpu_95th` chưa có giá trị
    lúc này). Cái cần gác là cú pháp: `and` viết thành `&&`, thiếu ngoặc, lọt ký tự
    của dòng bên cạnh do ghép khối lệch thụt đầu dòng.
    """
    a = Interpreter(no_print=True, no_import=True, no_delete=True, no_raise=True)
    ra = []
    for ma, ten, bt in bieu_thuc(rs):
        a.error = []
        try:
            a.parse(bt)
        except Exception as e:                       # asteval nuốt phần lớn
            ra.append(f"{ma}.{ten}: {type(e).__name__}: {e}")
            continue
        if a.error:
            ly_do = "; ".join(str(e.get_error()[1]) for e in a.error)[:160]
            ra.append(f"{ma}.{ten}: {ly_do}")
    return ra


# Bốn trường đổi PHẠM VI chấm chứ không đổi ngưỡng — sửa nhầm thì không có biểu thức
# nào hỏng để bắt, nên phải nói ra.
TRUONG_PHAM_VI = ("enabled", "type", "scope", "severity")


@dataclass
class KetQuaKiem:
    """Kết quả kiểm một đề xuất. `dat` KHÔNG có nghĩa là "đã đo eval" — xem docstring
    đầu module."""
    dat: bool = False
    loi: list[str] = field(default_factory=list)
    canh_bao: list[str] = field(default_factory=list)
    diff: str = ""
    so_quy_tac: int = 0
    so_bieu_thuc: int = 0
    chay_duoc_truoc: int = 0
    chay_duoc_sau: int = 0
    van_moi: str = ""           # cả file sau khi ghép — để xem trước / áp tay

    def tom_tat(self) -> str:
        if self.loi:
            return f"KHÔNG áp được: {self.loi[0]}" + (
                f" (và {len(self.loi) - 1} lỗi nữa)" if len(self.loi) > 1 else "")
        nen = (f"{self.so_quy_tac} quy tắc · {self.so_bieu_thuc} biểu thức còn phân "
               f"tích được · chạy được {self.chay_duoc_truoc} → {self.chay_duoc_sau}")
        return nen + (f" · {len(self.canh_bao)} cảnh báo" if self.canh_bao else "")


def kiem_de_xuat(van_goc: str, ma: str, khoi_moi: str) -> KetQuaKiem:
    """Kiểm một đề xuất sửa quy tắc `ma` thành `khoi_moi` (nguyên văn khối YAML)."""
    kq = KetQuaKiem()
    try:
        khoi_cu = doc_khoi(van_goc, ma)
    except KeyError:
        kq.loi.append(f"không có quy tắc `{ma}` trong bộ quy tắc đang chạy")
        return kq

    kq.diff = "".join(difflib.unified_diff(
        khoi_cu.splitlines(keepends=True), khoi_moi.splitlines(keepends=True),
        fromfile=f"{ma} (đang chạy)", tofile=f"{ma} (đề xuất)"))
    if not kq.diff:
        kq.loi.append("khối đề xuất y hệt khối đang chạy — không có gì để sửa")
        return kq

    try:
        nut = yaml.safe_load(khoi_moi)
    except yaml.YAMLError as e:
        kq.loi.append(f"khối đề xuất không phải YAML hợp lệ: {str(e)[:200]}")
        return kq
    if not (isinstance(nut, list) and len(nut) == 1 and isinstance(nut[0], dict)):
        kq.loi.append("khối đề xuất phải là ĐÚNG MỘT mục của `rules:`, mở đầu bằng "
                      "`  - id: …` và thụt đúng như trong file")
        return kq
    if str(nut[0].get("id", "")) != ma:
        kq.loi.append(f"`id` đổi từ `{ma}` thành `{nut[0].get('id', '')}` — mã quy tắc "
                      "đã dùng thì không được đổi: nó nằm trong `rule_ref` của mọi lỗi "
                      "đã lưu và trong nhãn của eval set")
        return kq

    van_moi = ghep_khoi(van_goc, ma, khoi_moi)
    try:
        rs_cu = RuleSet(yaml.safe_load(van_goc))
        rs_moi = RuleSet(yaml.safe_load(van_moi))
    except (yaml.YAMLError, ValueError, KeyError, TypeError) as e:
        kq.loi.append(f"ghép vào cả file thì bộ quy tắc không nạp được: "
                      f"{type(e).__name__}: {str(e)[:200]}")
        return kq

    # Lưới chắn cuối: nếu `pham_vi_khoi` dò SAI ranh giới khối thì phép ghép đã âm
    # thầm xoá hoặc nhân đôi quy tắc bên cạnh, mà mọi phép kiểm phía trên vẫn xanh.
    # Chưa biết đầu vào nào của người dùng lọt tới đây; nó gác các thay đổi SAU NÀY
    # của phần dò ranh giới, nên test gọi thẳng bằng ranh giới sai cố ý.
    ma_cu = [r.id for r in rs_cu.rules]
    ma_moi = [r.id for r in rs_moi.rules]
    if ma_cu != ma_moi:
        mat = sorted(set(ma_cu) - set(ma_moi))
        them = sorted(set(ma_moi) - set(ma_cu))
        kq.loi.append("đề xuất sửa MỘT quy tắc nhưng danh sách quy tắc đổi — "
                      + (f"mất {', '.join(mat)}. " if mat else "")
                      + (f"thêm {', '.join(them)}. " if them else "")
                      + "Nhiều khả năng khối bị cắt hoặc thụt đầu dòng sai.")
        return kq

    hong = bieu_thuc_hong(rs_moi)
    if hong:
        kq.loi.append(f"{len(hong)} biểu thức không phân tích được: "
                      + " | ".join(hong[:3]))
        return kq

    kq.so_quy_tac = len(rs_moi)
    kq.so_bieu_thuc = len(bieu_thuc(rs_moi))
    kq.chay_duoc_truoc = len(rs_cu.runnable())
    kq.chay_duoc_sau = len(rs_moi.runnable())
    kq.van_moi = van_moi

    r_cu, r_moi = rs_cu[ma], rs_moi[ma]
    vi_cu, vi_moi = r_cu.khong_danh_gia_duoc(), r_moi.khong_danh_gia_duoc()
    if vi_moi and not vi_cu:
        kq.canh_bao.append(f"sau khi sửa, `{ma}` KHÔNG còn đánh giá được: {vi_moi}")
    elif vi_cu and not vi_moi:
        kq.canh_bao.append(f"sau khi sửa, `{ma}` đánh giá được (trước đó: {vi_cu})")
    for t in TRUONG_PHAM_VI:
        a, b = getattr(r_cu, t), getattr(r_moi, t)
        if a != b:
            kq.canh_bao.append(f"`{t}` đổi {a!r} → {b!r} — đổi phạm vi chấm, "
                               "không phải đổi ngưỡng")
    kq.dat = True
    return kq
