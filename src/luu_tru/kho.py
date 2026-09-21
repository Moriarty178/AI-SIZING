"""Mọi truy cập CSDL của Giai đoạn 5 đi qua đây.

Hàm cho từng tính năng thêm vào khi làm tính năng đó, KHÔNG viết trước cho có.
Giao diện và API không viết SQL. Khi ghép vào tool sizing, chỉ lớp này đổi.

- 5.0 — mở kết nối, khởi tạo lược đồ, đường đi hồ sơ → lần → baseline.
- 5.1 — `ghi_lan_tham_dinh`: lần đầu đóng băng baseline, lần sau đối chiếu và ghi
  rổ phát sinh; `ds_ho_so`, `doc_ho_so` để API/giao diện đọc lại.
- 5.2 — `doc_finding` (một dòng baseline + lịch sử sửa + lần nộp mới nhất),
  `them_lan_sua` (người dùng ghi nhận đã sửa gì).
- 5.3 — `lan_moi_nhat`: lần thẩm định mới nhất của hồ sơ, để lần sau dùng lại câu trả
  lời model của nó.
- 5.4 — `them_bao_cao_loi` / `ds_bao_cao_loi`: người dùng báo «hệ thống báo sai», cho
  cả dòng baseline lẫn dòng trong rổ phát sinh.
- 5.6/5.9 — `doc_bang_admin`: một dòng mỗi lỗi baseline, kèm mọi lần sửa, giá trị đầu
  vào C4 đã dùng, số lời báo và ghi chú Admin mới nhất; `luu_ghi_chu_admin` ghi ba cột
  Admin theo kiểu CHỈ THÊM.
- 5.9 bước 2 — `them_de_xuat` / `ds_de_xuat` / `doi_trang_thai_de_xuat`: Admin đề
  xuất sửa một quy tắc, công cụ kiểm, NGƯỜI mới áp vào `config/rules.yaml`.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event, func, insert, select, update
from sqlalchemy.engine import Connection, Engine

from . import baseline as bl
from . import luoc_do as ld
from .cau_hinh import an_mat_khau
from .danh_tinh import DanhTinh

# Dòng do MÁY ghi (baseline AI sinh) mang vai `he_thong` — không lẫn với dòng người.
MAY = DanhTinh("he_thong", "copilot")


class LoiCSDL(RuntimeError):
    """Lỗi có thể hành động được — nói rõ phải làm gì, không trần trụi."""


class KhongThamDinhLaiDuoc(LoiCSDL):
    """Hồ sơ không tồn tại, hoặc đã gửi duyệt/đã có quyết định."""


class KhongCoFinding(LoiCSDL):
    """Dòng lỗi không có, hoặc không thuộc hồ sơ đang nói tới."""


class HoSoKhongDangSua(LoiCSDL):
    """Hồ sơ đã gửi duyệt / đã có quyết định — không ghi nhận sửa được nữa."""


TOI_DA_NOI_DUNG_SUA = 10_000
TOI_DA_LY_DO = 2_000


def _bat_khoa_ngoai_sqlite(engine: Engine) -> None:
    """SQLite mặc định TẮT khoá ngoại. Không bật thì test "xoá hồ sơ kéo theo
    con" qua được trên SQLite mà hỏng trên PostgreSQL — test nói dối."""
    @event.listens_for(engine, "connect")
    def _bat(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


def _dict(r) -> dict:
    """Dòng → dict JSON được (datetime → ISO)."""
    d = dict(r._mapping)
    for k, v in d.items():
        if hasattr(v, "isoformat"):
            d[k] = v.isoformat()
    return d


class KhoCSDL:
    def __init__(self, url: str):
        self.url_an = an_mat_khau(url)
        tham_so: dict = {"pool_pre_ping": True}
        if url.startswith("postgresql"):
            # Chờ tối đa 5 giây: CSDL tắt thì lúc khởi động API phải báo lỗi
            # nhanh, không treo cả tiến trình.
            tham_so["connect_args"] = {"connect_timeout": 5}
        if url.startswith("sqlite"):
            # Luồng chạy việc ghi hồ sơ, luồng API đọc — cùng một engine.
            tham_so["connect_args"] = {"check_same_thread": False}
        self.engine = create_engine(url, **tham_so)
        if url.startswith("sqlite"):
            _bat_khoa_ngoai_sqlite(self.engine)

    # ------------------------------------------------------------------ nền --
    def khoi_tao(self) -> None:
        """Tạo bảng còn thiếu; DỪNG nếu CSDL mang phiên bản lược đồ khác.

        Gọi nhiều lần vẫn an toàn. `create_all` KHÔNG sửa bảng đã có, nên chạy
        tiếp trên lược đồ lệch là để lỗi hiện ra ở một câu SQL nào đó giữa
        chừng, xa chỗ gây ra nó (NT4).
        """
        ld.metadata.create_all(self.engine)
        with self.engine.begin() as c:
            co = c.execute(select(ld.thong_tin_luoc_do.c.gia_tri).where(
                ld.thong_tin_luoc_do.c.khoa == "phien_ban")).scalar()
            if co is None:
                c.execute(insert(ld.thong_tin_luoc_do).values(
                    khoa="phien_ban", gia_tri=ld.PHIEN_BAN_LUOC_DO))
            elif co != ld.PHIEN_BAN_LUOC_DO:
                # Nâng cấp TRONG CÙNG giao dịch với việc ghi số phiên bản: hỏng giữa
                # chừng thì lùi cả hai, không để lại CSDL nửa bản này nửa bản kia.
                try:
                    da_lam = ld.nang_cap(c, co)
                except ValueError as e:
                    raise LoiCSDL(
                        f"CSDL {self.url_an} mang lược đồ phiên bản {co}, mã hiện tại "
                        f"cần {ld.PHIEN_BAN_LUOC_DO}, và {e}. KHÔNG chạy tiếp trên "
                        "lược đồ lệch.") from e
                c.execute(update(ld.thong_tin_luoc_do)
                          .where(ld.thong_tin_luoc_do.c.khoa == "phien_ban")
                          .values(gia_tri=ld.PHIEN_BAN_LUOC_DO))
                print(f"[csdl] nâng lược đồ {co} → {ld.PHIEN_BAN_LUOC_DO}: "
                      + "; ".join(da_lam), flush=True)

    def phien_ban_luoc_do(self) -> str:
        """Phiên bản lược đồ ĐANG NẰM TRONG CSDL — `/health` báo lại để người vận hành
        thấy migration đã chạy chưa, không phải đoán qua log."""
        with self.engine.connect() as c:
            return c.execute(select(ld.thong_tin_luoc_do.c.gia_tri).where(
                ld.thong_tin_luoc_do.c.khoa == "phien_ban")).scalar() or ""

    # ------------------------------------------ viên gạch — dùng chung một c --
    @staticmethod
    def _tao_ho_so(c: Connection, ten_file: str, dt: DanhTinh) -> int:
        return c.execute(insert(ld.ho_so).values(
            ten_file=ten_file, vai=dt.vai, ten=dt.ten)).inserted_primary_key[0]

    @staticmethod
    def _them_lan(c: Connection, ho_so_id: int, ma_viec: str, dt: DanhTinh,
                  ten_file: str, commit: str) -> tuple[int, int]:
        so = (c.execute(select(func.max(ld.lan_tham_dinh.c.so_thu_tu)).where(
            ld.lan_tham_dinh.c.ho_so_id == ho_so_id)).scalar() or 0) + 1
        i = c.execute(insert(ld.lan_tham_dinh).values(
            ho_so_id=ho_so_id, so_thu_tu=so, ma_viec=ma_viec, ten_file=ten_file,
            commit=commit, vai=dt.vai, ten=dt.ten)).inserted_primary_key[0]
        return i, so

    # ----------------------------------------------------- hồ sơ và baseline --
    def tao_ho_so(self, ten_file: str, *, vai: str, ten: str) -> int:
        with self.engine.begin() as c:
            return self._tao_ho_so(c, ten_file, DanhTinh(vai, ten))

    def them_lan_tham_dinh(self, ho_so_id: int, ma_viec: str, *, vai: str, ten: str,
                           commit: str = "", ten_file: str = "") -> tuple[int, int]:
        """(id, số thứ tự). Lần đầu tiên của một hồ sơ là baseline (5.1)."""
        with self.engine.begin() as c:
            return self._them_lan(c, ho_so_id, ma_viec, DanhTinh(vai, ten),
                                  ten_file, commit)

    def them_finding_baseline(self, ho_so_id: int, dong: list[dict]) -> int:
        """Ghi tập lỗi cố định. Trong MỘT giao dịch: hỏng một dòng là không ghi dòng
        nào, để không bao giờ có baseline dở dang."""
        if not dong:
            return 0
        with self.engine.begin() as c:
            c.execute(insert(ld.finding_baseline),
                      [{**d, "ho_so_id": ho_so_id} for d in dong])
        return len(dong)

    def doc_baseline(self, ho_so_id: int) -> list[dict]:
        t = ld.finding_baseline
        with self.engine.connect() as c:
            return [_dict(r) for r in c.execute(
                select(t).where(t.c.ho_so_id == ho_so_id).order_by(t.c.id))]

    # ------------------------------------------------------------------ 5.1 --
    def ghi_lan_tham_dinh(self, *, ma_viec: str, ten_file: str, danh_tinh: DanhTinh,
                          findings: list[dict], ho_so_id: int | None = None,
                          commit: str = "") -> dict:
        """Ghi MỘT lần thẩm định — toàn bộ trong MỘT giao dịch.

        `ho_so_id=None` → hồ sơ mới, lần 1, ĐÓNG BĂNG baseline.
        Có `ho_so_id` → lần N: đối chiếu với baseline, ghi trạng thái từng dòng và
        rổ phát sinh; baseline KHÔNG đổi một dòng nào.

        Một giao dịch vì hỏng giữa chừng mà để lại «lần 2» không có kết quả nào thì
        bảng Admin sẽ đọc thành «mọi lỗi đã sửa».
        """
        with self.engine.begin() as c:
            if ho_so_id is None:
                ho_so_id = self._tao_ho_so(c, ten_file, danh_tinh)
            else:
                hs = c.execute(select(ld.ho_so.c.trang_thai).where(
                    ld.ho_so.c.id == ho_so_id)).scalar()
                if hs is None:
                    raise KhongThamDinhLaiDuoc(f"Không có hồ sơ #{ho_so_id}.")
                if hs != "dang_sua":
                    raise KhongThamDinhLaiDuoc(
                        f"Hồ sơ #{ho_so_id} đang ở trạng thái «{hs}» — chỉ thẩm định "
                        "lại được khi đang sửa.")

            lan_id, so = self._them_lan(c, ho_so_id, ma_viec, danh_tinh, ten_file,
                                        commit)
            if so == 1:
                kf = bl.gan_khoa(findings)
                id_theo_khoa: dict[str, int] = {}
                for khoa, f in kf:
                    id_theo_khoa[khoa] = c.execute(insert(ld.finding_baseline).values(
                        ho_so_id=ho_so_id, nguon="ai", vai=MAY.vai, ten=MAY.ten,
                        **bl.dong_finding(khoa, f))).inserted_primary_key[0]
                dc = bl.ket_qua_lan_dau(kf, id_theo_khoa)
            else:
                baseline = [dict(r._mapping) for r in c.execute(
                    select(ld.finding_baseline.c.id, ld.finding_baseline.c.khoa,
                           ld.finding_baseline.c.muc_do).where(
                        ld.finding_baseline.c.ho_so_id == ho_so_id))]
                dc = bl.doi_chieu(baseline, findings)
                if dc.phat_sinh:
                    c.execute(insert(ld.finding_phat_sinh),
                              [{**p, "lan_tham_dinh_id": lan_id} for p in dc.phat_sinh])
            if dc.ket_qua:
                c.execute(insert(ld.ket_qua_lan),
                          [{**r, "lan_tham_dinh_id": lan_id, "finding_baseline_id": b}
                           for b, r in dc.ket_qua.items()])
        return {"ho_so_id": ho_so_id, "lan_id": lan_id, "so_thu_tu": so,
                "so_loi_baseline": len(dc.ket_qua), **dc.dem()}

    def trang_thai_ho_so(self, ho_so_id: int) -> str | None:
        """Kiểm nhanh lúc NỘP — để chặn ngay ở cửa, không đợi 20 phút chạy xong
        mới báo «hồ sơ không tồn tại»."""
        with self.engine.connect() as c:
            return c.execute(select(ld.ho_so.c.trang_thai).where(
                ld.ho_so.c.id == ho_so_id)).scalar()

    def lan_moi_nhat(self, ho_so_id: int) -> dict | None:
        """5.3 — lần thẩm định có số thứ tự lớn nhất. None nếu hồ sơ chưa có lần nào."""
        lan = ld.lan_tham_dinh
        with self.engine.connect() as c:
            r = c.execute(select(lan).where(lan.c.ho_so_id == ho_so_id)
                          .order_by(lan.c.so_thu_tu.desc()).limit(1)).first()
        return _dict(r) if r is not None else None

    def ds_ho_so(self) -> list[dict]:
        hs, lan, fb = ld.ho_so, ld.lan_tham_dinh, ld.finding_baseline
        so_lan = (select(func.count()).where(lan.c.ho_so_id == hs.c.id)
                  .scalar_subquery())
        so_loi = (select(func.count()).where(fb.c.ho_so_id == hs.c.id)
                  .scalar_subquery())
        with self.engine.connect() as c:
            return [_dict(r) for r in c.execute(
                select(hs, so_lan.label("so_lan"), so_loi.label("so_loi_baseline"))
                .order_by(hs.c.id.desc()))]

    def doc_ho_so(self, ho_so_id: int) -> dict | None:
        """Hồ sơ + các lần + baseline kèm trạng thái MỚI NHẤT + rổ phát sinh của
        lần mới nhất. None nếu không có hồ sơ."""
        hs, lan, fb, kq, ps = (ld.ho_so, ld.lan_tham_dinh, ld.finding_baseline,
                               ld.ket_qua_lan, ld.finding_phat_sinh)
        with self.engine.connect() as c:
            h = c.execute(select(hs).where(hs.c.id == ho_so_id)).first()
            if h is None:
                return None
            cac_lan = [_dict(r) for r in c.execute(
                select(lan).where(lan.c.ho_so_id == ho_so_id)
                .order_by(lan.c.so_thu_tu))]
            for l in cac_lan:
                dem = {"dat": 0, "chua_dat": 0, "chua_kiem_duoc": 0}
                for tt, n in c.execute(
                        select(kq.c.trang_thai, func.count())
                        .where(kq.c.lan_tham_dinh_id == l["id"])
                        .group_by(kq.c.trang_thai)):
                    dem[tt] = n
                dem["phat_sinh"] = c.execute(select(func.count()).where(
                    ps.c.lan_tham_dinh_id == l["id"])).scalar()
                l["dem"] = dem

            baseline = [_dict(r) for r in c.execute(
                select(fb).where(fb.c.ho_so_id == ho_so_id).order_by(fb.c.id))]
            so_sua = dict(c.execute(
                select(ld.lan_sua.c.finding_baseline_id, func.count())
                .join(fb, fb.c.id == ld.lan_sua.c.finding_baseline_id)
                .where(fb.c.ho_so_id == ho_so_id)
                .group_by(ld.lan_sua.c.finding_baseline_id)).all())
            # 5.4 — đã báo lỗi hệ thống mấy lần, cho cả hai rổ.
            bl = ld.bao_cao_loi
            so_bao = dict(c.execute(
                select(bl.c.finding_baseline_id, func.count())
                .where(bl.c.ho_so_id == ho_so_id,
                       bl.c.finding_baseline_id.is_not(None))
                .group_by(bl.c.finding_baseline_id)).all())
            so_bao_ps = dict(c.execute(
                select(bl.c.finding_phat_sinh_id, func.count())
                .where(bl.c.ho_so_id == ho_so_id,
                       bl.c.finding_phat_sinh_id.is_not(None))
                .group_by(bl.c.finding_phat_sinh_id)).all())
            for b in baseline:
                b["so_lan_sua"] = so_sua.get(b["id"], 0)
                b["so_bao_loi"] = so_bao.get(b["id"], 0)
            moi_nhat = cac_lan[-1]["id"] if cac_lan else None
            if moi_nhat is not None:
                theo_b = {r.finding_baseline_id: r for r in c.execute(
                    select(kq).where(kq.c.lan_tham_dinh_id == moi_nhat))}
                for b in baseline:
                    r = theo_b.get(b["id"])
                    b["trang_thai"] = r.trang_thai if r else None
                    b["ket_luan_boi"] = r.ket_luan_boi if r else None
                    b["muc_do_lan"] = r.muc_do_lan if r else None
                    b["computed_evidence_lan"] = r.computed_evidence if r else ""
                    b["dau_vao_lan"] = r.dau_vao if r else ""
            phat_sinh = [] if moi_nhat is None else [_dict(r) for r in c.execute(
                select(ps).where(ps.c.lan_tham_dinh_id == moi_nhat).order_by(ps.c.id))]
            for r in phat_sinh:
                r["so_bao_loi"] = so_bao_ps.get(r["id"], 0)
        return {"ho_so": _dict(h), "so_loi_baseline": len(baseline),
                "cac_lan": cac_lan, "baseline": baseline, "phat_sinh": phat_sinh}

    # ------------------------------------------------------------------ 5.2 --
    def doc_finding(self, ho_so_id: int, fb_id: int) -> dict | None:
        """Một dòng baseline + trạng thái lần mới nhất + lịch sử sửa + lần nộp mới
        nhất (để mở đúng bản tài liệu). None nếu dòng không thuộc hồ sơ."""
        fb, lan, kq, ls = (ld.finding_baseline, ld.lan_tham_dinh, ld.ket_qua_lan,
                           ld.lan_sua)
        with self.engine.connect() as c:
            r = c.execute(select(fb).where(fb.c.id == fb_id,
                                           fb.c.ho_so_id == ho_so_id)).first()
            if r is None:
                return None
            d = _dict(r)
            moi = c.execute(select(lan).where(lan.c.ho_so_id == ho_so_id)
                            .order_by(lan.c.so_thu_tu.desc()).limit(1)).first()
            d["lan_moi_nhat"] = _dict(moi) if moi else None
            k = None if moi is None else c.execute(select(kq).where(
                kq.c.lan_tham_dinh_id == moi.id, kq.c.finding_baseline_id == fb_id)).first()
            d["trang_thai"] = k.trang_thai if k else None
            d["ket_luan_boi"] = k.ket_luan_boi if k else None
            d["muc_do_lan"] = k.muc_do_lan if k else None
            d["computed_evidence_lan"] = k.computed_evidence if k else ""
            d["dau_vao_lan"] = k.dau_vao if k else ""
            d["lan_sua"] = [_dict(x) for x in c.execute(
                select(ls).where(ls.c.finding_baseline_id == fb_id)
                .order_by(ls.c.so_lan))]
            d["bao_cao_loi"] = [_dict(x) for x in c.execute(
                select(ld.bao_cao_loi)
                .where(ld.bao_cao_loi.c.finding_baseline_id == fb_id)
                .order_by(ld.bao_cao_loi.c.id))]
            d["ho_so_trang_thai"] = c.execute(select(ld.ho_so.c.trang_thai).where(
                ld.ho_so.c.id == ho_so_id)).scalar()
        return d

    def them_lan_sua(self, ho_so_id: int, fb_id: int, *, danh_tinh: DanhTinh,
                     noi_dung_sua: str, noi_dung_goc: str = "") -> dict:
        """Ghi nhận MỘT lần sửa. `so_lan` tăng theo từng dòng baseline.

        Kiểm trong CÙNG giao dịch với INSERT: tách ra thì giữa lúc kiểm và lúc ghi,
        hồ sơ có thể đã được gửi duyệt.
        """
        noi_dung_sua = (noi_dung_sua or "").strip()
        if not noi_dung_sua:
            raise ValueError("Chưa nhập nội dung đã sửa.")
        if len(noi_dung_sua) > TOI_DA_NOI_DUNG_SUA:
            raise ValueError(f"Nội dung sửa dài {len(noi_dung_sua)} ký tự, tối đa "
                             f"{TOI_DA_NOI_DUNG_SUA}.")
        fb, ls = ld.finding_baseline, ld.lan_sua
        with self.engine.begin() as c:
            tt = c.execute(select(ld.ho_so.c.trang_thai).where(
                ld.ho_so.c.id == ho_so_id)).scalar()
            if tt is None:
                raise KhongCoFinding(f"Không có hồ sơ #{ho_so_id}.")
            if c.execute(select(fb.c.id).where(fb.c.id == fb_id,
                                               fb.c.ho_so_id == ho_so_id)).first() is None:
                raise KhongCoFinding(f"Lỗi #{fb_id} không thuộc hồ sơ #{ho_so_id}.")
            if tt != "dang_sua":
                raise HoSoKhongDangSua(f"Hồ sơ #{ho_so_id} đang «{tt}» — không ghi nhận "
                                       "sửa được nữa.")
            so = (c.execute(select(func.max(ls.c.so_lan)).where(
                ls.c.finding_baseline_id == fb_id)).scalar() or 0) + 1
            i = c.execute(insert(ls).values(
                finding_baseline_id=fb_id, so_lan=so, noi_dung_goc=noi_dung_goc or "",
                noi_dung_sua=noi_dung_sua, vai=danh_tinh.vai,
                ten=danh_tinh.ten)).inserted_primary_key[0]
        return {"id": i, "so_lan": so}

    # ------------------------------------------------------------------ 5.4 --
    def them_bao_cao_loi(self, ho_so_id: int, *, danh_tinh: DanhTinh, ly_do: str,
                         finding_baseline_id: int | None = None,
                         finding_phat_sinh_id: int | None = None) -> dict:
        """Người dùng báo một dòng là lỗi của hệ thống. Đúng MỘT nguồn: dòng baseline
        hoặc dòng trong rổ phát sinh.

        KHÔNG đòi hồ sơ «đang sửa»: người dùng hay nhận ra một dòng vô lý ĐÚNG LÚC
        đang xem lại trước khi gửi duyệt, hoặc sau khi Admin hỏi tới. Chặn lúc đó là
        vứt đi đúng phản hồi đáng giá nhất (mục tiêu 4.1: dữ liệu để sửa công cụ).
        """
        ly_do = (ly_do or "").strip()
        if not ly_do:
            raise ValueError("Chưa nhập lý do báo lỗi.")
        if len(ly_do) > TOI_DA_LY_DO:
            raise ValueError(f"Lý do dài {len(ly_do)} ký tự, tối đa {TOI_DA_LY_DO}.")
        if (finding_baseline_id is None) == (finding_phat_sinh_id is None):
            raise ValueError("Phải chỉ đúng MỘT dòng: baseline hoặc phát sinh.")

        fb, ps, lan = ld.finding_baseline, ld.finding_phat_sinh, ld.lan_tham_dinh
        with self.engine.begin() as c:
            if c.execute(select(ld.ho_so.c.id).where(
                    ld.ho_so.c.id == ho_so_id)).first() is None:
                raise KhongCoFinding(f"Không có hồ sơ #{ho_so_id}.")
            if finding_baseline_id is not None:
                r = c.execute(select(fb.c.khoa, fb.c.finding_id_goc).where(
                    fb.c.id == finding_baseline_id,
                    fb.c.ho_so_id == ho_so_id)).first()
                nguon = "baseline"
            else:
                r = c.execute(
                    select(ps.c.khoa, ps.c.finding_id_goc)
                    .join(lan, lan.c.id == ps.c.lan_tham_dinh_id)
                    .where(ps.c.id == finding_phat_sinh_id,
                           lan.c.ho_so_id == ho_so_id)).first()
                nguon = "phát sinh"
            if r is None:
                raise KhongCoFinding(
                    f"Dòng {nguon} #{finding_baseline_id or finding_phat_sinh_id} "
                    f"không thuộc hồ sơ #{ho_so_id}.")
            i = c.execute(insert(ld.bao_cao_loi).values(
                ho_so_id=ho_so_id, finding_baseline_id=finding_baseline_id,
                finding_phat_sinh_id=finding_phat_sinh_id, khoa=r.khoa or "",
                ly_do=ly_do, vai=danh_tinh.vai, ten=danh_tinh.ten)).inserted_primary_key[0]
        return {"id": i, "khoa": r.khoa or "", "finding_id_goc": r.finding_id_goc or "",
                "nguon": nguon}

    def ds_bao_cao_loi(self, ho_so_id: int) -> list[dict]:
        """Mọi lời báo của một hồ sơ, mới nhất trước — hàng chờ của Admin (5.12)."""
        b = ld.bao_cao_loi
        with self.engine.connect() as c:
            return [_dict(r) for r in c.execute(
                select(b).where(b.c.ho_so_id == ho_so_id).order_by(b.c.id.desc()))]

    # ------------------------------------------------------------ 5.6/5.9 --
    def doc_bang_admin(self, ho_so_id: int) -> dict | None:
        """Bảng lịch sử sửa lỗi cho Admin: MỘT dòng mỗi lỗi baseline (cố định từ 5.1),
        kèm nội dung TỪNG lần sửa, giá trị đầu vào C4 đã dùng ở lần mới nhất, số lời báo
        lỗi hệ thống, và ghi chú Admin mới nhất. None nếu không có hồ sơ.

        Đọc riêng chứ không dùng `doc_ho_so`: bảng này cần nội dung từng lần sửa (bảng
        kia chỉ đếm), và Admin mở nó độc lập với màn hình người làm sizing.
        """
        d = self.doc_ho_so(ho_so_id)
        if d is None:
            return None
        fb, ls, bl, ga = (ld.finding_baseline, ld.lan_sua, ld.bao_cao_loi,
                          ld.ghi_chu_admin)
        theo_dong: dict[int, list] = {}
        moi_nhat: dict[int, dict] = {}
        with self.engine.connect() as c:
            for r in c.execute(
                    select(ls).join(fb, fb.c.id == ls.c.finding_baseline_id)
                    .where(fb.c.ho_so_id == ho_so_id)
                    .order_by(ls.c.finding_baseline_id, ls.c.so_lan)):
                theo_dong.setdefault(r.finding_baseline_id, []).append(_dict(r))
            # CHỈ THÊM: dòng có id lớn nhất của mỗi lỗi là dòng đang có hiệu lực.
            for r in c.execute(
                    select(ga).join(fb, fb.c.id == ga.c.finding_baseline_id)
                    .where(fb.c.ho_so_id == ho_so_id).order_by(ga.c.id)):
                moi_nhat[r.finding_baseline_id] = _dict(r)
            ly_do: dict[int, list[str]] = {}
            for r in c.execute(select(bl.c.finding_baseline_id, bl.c.ly_do).where(
                    bl.c.ho_so_id == ho_so_id, bl.c.finding_baseline_id.is_not(None))
                    .order_by(bl.c.id)):
                ly_do.setdefault(r.finding_baseline_id, []).append(r.ly_do)
        so_lan_sua_max = 0
        for b in d["baseline"]:
            b["lan_sua"] = theo_dong.get(b["id"], [])
            b["ghi_chu_admin"] = moi_nhat.get(b["id"]) or {}
            b["ly_do_bao_loi"] = ly_do.get(b["id"], [])
            so_lan_sua_max = max(so_lan_sua_max, len(b["lan_sua"]))
        d["so_lan_sua_max"] = so_lan_sua_max
        return d

    def luu_ghi_chu_admin(self, ho_so_id: int, *, danh_tinh: DanhTinh,
                          muc: list[dict]) -> dict:
        """Ghi ba cột Admin. CHỈ THÊM: mỗi lần đổi là một dòng mới, dòng mới nhất có
        hiệu lực — Admin quyết phê duyệt dựa trên đây nên lịch sử phải còn.

        Mục nào KHÔNG khác dòng mới nhất thì bỏ qua: bấm Lưu hai lần không được nhân
        bản lịch sử (cùng luật với bảng ghi chú 4.1).
        """
        hop_le_dg = (None, "chap_nhan", "tu_choi", "can_ban")
        hop_le_lop = (None, "nguoi_lam_sizing", "he_thong_ai")
        fb, ga = ld.finding_baseline, ld.ghi_chu_admin
        da_luu = bo_qua = 0
        with self.engine.begin() as c:
            thuoc = {r.id for r in c.execute(
                select(fb.c.id).where(fb.c.ho_so_id == ho_so_id))}
            cu: dict[int, dict] = {}
            for r in c.execute(select(ga).join(fb, fb.c.id == ga.c.finding_baseline_id)
                               .where(fb.c.ho_so_id == ho_so_id).order_by(ga.c.id)):
                cu[r.finding_baseline_id] = _dict(r)
            for m in muc:
                i = int(m.get("finding_baseline_id") or 0)
                if i not in thuoc:
                    raise KhongCoFinding(f"Lỗi #{i} không thuộc hồ sơ #{ho_so_id}.")
                ghi_chu = str(m.get("ghi_chu") or "").strip()
                if len(ghi_chu) > TOI_DA_NOI_DUNG_SUA:
                    raise ValueError(f"Ghi chú dài {len(ghi_chu)} ký tự, tối đa "
                                     f"{TOI_DA_NOI_DUNG_SUA}.")
                dg = m.get("danh_gia") or None
                lop = m.get("loi_o_phia") or None
                if dg not in hop_le_dg or lop not in hop_le_lop:
                    raise ValueError(f"Giá trị không hợp lệ: danh_gia={dg!r}, "
                                     f"loi_o_phia={lop!r}.")
                truoc = cu.get(i) or {}
                if (str(truoc.get("ghi_chu") or "") == ghi_chu
                        and (truoc.get("danh_gia") or None) == dg
                        and (truoc.get("loi_o_phia") or None) == lop):
                    bo_qua += 1
                    continue
                c.execute(insert(ga).values(
                    finding_baseline_id=i, ghi_chu=ghi_chu, danh_gia=dg,
                    loi_o_phia=lop, vai=danh_tinh.vai, ten=danh_tinh.ten))
                da_luu += 1
        return {"da_luu": da_luu, "bo_qua": bo_qua}

    # ------------------------------------------------------- 5.9 bước 2 --
    def them_de_xuat(self, *, rule_ref: str, danh_tinh: DanhTinh, noi_dung_cu: str,
                     noi_dung_moi: str, ly_do: str = "", ho_so_id: int | None = None,
                     trang_thai: str = "cho_kiem", ket_qua_kiem: str = "") -> dict:
        """Ghi một đề xuất sửa quy tắc. KHÔNG đụng vào `config/rules.yaml`.

        Lưu `noi_dung_cu` (khối YAML lúc đề xuất) chứ không chỉ `noi_dung_moi`: khi
        người chốt đọc lại sau vài tuần, file có thể đã đổi vì một đề xuất khác, và
        không có bản cũ thì cái `diff` kia không còn nghĩa gì.
        """
        rule_ref = (rule_ref or "").strip()
        if not rule_ref:
            raise ValueError("Thiếu mã quy tắc.")
        if not (noi_dung_moi or "").strip():
            raise ValueError("Chưa nhập nội dung quy tắc đề xuất.")
        for ten, v in (("Nội dung đề xuất", noi_dung_moi), ("Lý do", ly_do)):
            if len(v or "") > TOI_DA_NOI_DUNG_SUA:
                raise ValueError(f"{ten} dài {len(v)} ký tự, tối đa "
                                 f"{TOI_DA_NOI_DUNG_SUA}.")
        with self.engine.begin() as c:
            if ho_so_id is not None and c.execute(select(ld.ho_so.c.id).where(
                    ld.ho_so.c.id == ho_so_id)).first() is None:
                raise KhongCoFinding(f"Không có hồ sơ #{ho_so_id}.")
            r = c.execute(insert(ld.de_xuat_quy_tac).values(
                ho_so_id=ho_so_id, rule_ref=rule_ref, noi_dung_cu=noi_dung_cu,
                noi_dung_moi=noi_dung_moi, ly_do=(ly_do or "").strip(),
                trang_thai=trang_thai, ket_qua_kiem=ket_qua_kiem,
                vai=danh_tinh.vai, ten=danh_tinh.ten
            ).returning(ld.de_xuat_quy_tac.c.id))
            return {"id": r.scalar_one(), "rule_ref": rule_ref,
                    "trang_thai": trang_thai}

    def ds_de_xuat(self, *, rule_ref: str = "", ho_so_id: int | None = None,
                   trang_thai: str = "") -> list[dict]:
        """Đề xuất sửa quy tắc, mới nhất trước. Lọc rỗng = lấy tất."""
        d = ld.de_xuat_quy_tac
        q = select(d).order_by(d.c.id.desc())
        if rule_ref:
            q = q.where(d.c.rule_ref == rule_ref)
        if ho_so_id is not None:
            q = q.where(d.c.ho_so_id == ho_so_id)
        if trang_thai:
            q = q.where(d.c.trang_thai == trang_thai)
        with self.engine.connect() as c:
            return [_dict(r) for r in c.execute(q)]

    def doi_trang_thai_de_xuat(self, de_xuat_id: int, trang_thai: str, *,
                               bang_chung_eval: str | None = None) -> dict:
        """Người chốt đánh dấu đã áp / từ chối, hoặc gắn bằng chứng eval vào.

        KHÔNG tự chuyển sang `da_ap`: công cụ không sửa `rules.yaml`, nên nó không
        biết đề xuất đã được áp hay chưa — người áp xong tự đánh dấu. Bên gọi (API)
        đối chiếu lại với file đang chạy trước khi cho đánh dấu.
        """
        hop_le = ("cho_kiem", "kiem_dat", "kiem_hong", "da_ap", "tu_choi")
        if trang_thai not in hop_le:
            raise ValueError(f"Trạng thái {trang_thai!r} không hợp lệ "
                             f"({', '.join(hop_le)}).")
        d = ld.de_xuat_quy_tac
        gt: dict = {"trang_thai": trang_thai}
        if bang_chung_eval is not None:
            gt["bang_chung_eval"] = bang_chung_eval
        with self.engine.begin() as c:
            if c.execute(select(d.c.id).where(d.c.id == de_xuat_id)).first() is None:
                raise KhongCoFinding(f"Không có đề xuất #{de_xuat_id}.")
            c.execute(update(d).where(d.c.id == de_xuat_id).values(**gt))
            return _dict(c.execute(select(d).where(d.c.id == de_xuat_id)).one())

    def dat_trang_thai_ho_so(self, ho_so_id: int, trang_thai: str) -> None:
        """Dùng ở 5.5/5.8; ở 5.1 chỉ để test chặn thẩm định lại hồ sơ đã gửi duyệt."""
        with self.engine.begin() as c:
            c.execute(update(ld.ho_so).where(ld.ho_so.c.id == ho_so_id)
                      .values(trang_thai=trang_thai))
