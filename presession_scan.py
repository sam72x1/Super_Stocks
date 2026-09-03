# -*- coding: utf-8 -*-
"""🌙⏱️ `T-PRESESSION` — أداةُ القياس التاريخيّ: «قائمةٌ قبل الافتر/البري بعشر دقائق».

العقد: `presession_prereg.md` (مدفوعٌ قبل أيّ رقم). أمرُ المالك 2026-09-03.

لكلّ يومِ تداولٍ (ملفُّ شموع الدقيقة المجمَّع من Polygon — PIT بالبناء) وكلّ رمزٍ في
الكون السعريّ [MIN_PRICE, SPLIT_RADAR_PRICE_MAX] يُصدر صفَّين:
  • `AH` — القرارُ 15:50 نيويورك (قبل الافتر بعشر دقائق): الميزاتُ من شموع اليوم حتى
    القرار، والوسمُ من أوّل 10/30/60 دقيقة من الافتر والافترِ كلِّه.
  • `PM` — القرارُ 03:50 من اليوم التالي: الميزاتُ من اليوم كاملًا (بري + نظاميّ +
    افتر)، والوسمُ من أوّل 10/30/60 دقيقة من بريماركت اليوم التالي وبريماركتِه كلِّه.
الوسمُ الحاكم `hit80_10`: أعلى قمّةٍ في النافذة ‏≥ ‏`ref × 1.80` **و** دولارُ النافذة
‏≥ `LABEL_MIN_USD`.

🔒 قراءةٌ فقط: صفرُ إرسال · صفرُ كتابةِ حالة · لا تستوردها `Super_stock`.
🔒 مقياسٌ واحد: الأنبوبةُ (`day_key`/`head_size_mb`/`download`/`_pick`/`ny_minute`)
   وبوّابةُ المِرساة (`prescreen`/`first_anchor` ⟶ `liq_stage_events` الإنتاجيّة)
   **بالاسم** من `ah_scan`/`kasih_scan` — لا نسخةَ منطقٍ ثانية.
🔒 لا نظرَ مستقبليّ: كلُّ ميزةٍ من شموعٍ دقيقتُها **أقلُّ من** لحظة القرار (`V1` تُثبته
   بعدّادٍ يرمي عند أوّل خرق).
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import os
import statistics
import sys
import time

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import ah_scan as AH                                              # noqa: E402
import kasih_scan as KS                                           # noqa: E402
import market_calendar as MC                                      # noqa: E402
import presession_feats as PF                                     # noqa: E402
import Super_stock as S                                           # noqa: E402

NY = KS.NY
PROD_WIN = int(S.LIQ_WINDOW_MIN)          # نافذةُ بوّابة الإنتاج — تُطبَع لا تُخمَّن
PRICE_LO, PRICE_HI = KS.PRICE_LO, KS.PRICE_HI      # كونُ kasih_scan بالاسم (مُعاد)
KEEP_HI = 12.0            # سعةُ الاحتفاظ بالشموع (سوبرست الكون — لا حكمَ عليه)
WITNESS = (os.environ.get("PRESESSION_WITNESS") or "AAPL").strip().upper()
SEED_DAYS = 25            # بذرةُ الملخّص المتدحرج (‏20 يومًا + احتياط)

# 🔒 **مصدرٌ واحد** لكلّ ثابتٍ يشترك فيه القياسُ والأداةُ الحيّة (`presession_feats`).
LABEL_MIN_USD = PF.LABEL_MIN_USD
HIT_PCT = PF.HIT_PCT
LADDER = PF.LADDER
PRE_OPEN, EXT_CLOSE = PF.PRE_OPEN, PF.EXT_CLOSE
DECISION_LEAD, WINDOWS, TOPK, ROLL_N = PF.DECISION_LEAD, PF.WINDOWS, PF.TOPK, PF.ROLL_N
FEATS_DESC, FEATS_ASC, BASELINES = PF.FEATS_DESC, PF.FEATS_ASC, PF.BASELINES
LookAhead = PF.LookAhead
_r = PF._r
core_feats = PF.core_feats
post_feats = PF.post_feats
rolling_feats = PF.rolling_feats


def log(m: str = "") -> None:
    print(m, flush=True)


# ── قراءةُ ملفّ اليوم (مع عمود `transactions`) ────────────────────────────────
def parse_day_ext(fh, keep_prev: dict, witness: str = WITNESS):
    """يقرأ ملفَّ اليوم ويُرجع (bars, closes):
    `bars[sym]` = قائمةُ (ms, o, h, l, c, v, n, mod) مرتّبةً · لرموزٍ إغلاقُ أمسها
    داخل [0.3, KEEP_HI] أو مجهولٌ وأوّلُ شمعةٍ ‏≤ KEEP_HI (سوبرست الكون) · والشاهدُ
    دائمًا · `closes[sym]` = آخرُ إغلاقٍ نظاميّ (‏≤16:00) **لكلّ** الرموز."""
    rd = csv.reader(fh)
    header = next(rd)
    i_t = AH._pick(header, "ticker", "symbol")
    i_o, i_h = AH._pick(header, "open"), AH._pick(header, "high")
    i_l, i_c = AH._pick(header, "low"), AH._pick(header, "close")
    i_v = AH._pick(header, "volume")
    i_n = AH._pick(header, "transactions", "n")
    i_w = AH._pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_o, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    bars: dict = {}
    closes: dict = {}
    skip: set = set()
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            ns = int(row[i_w])
            o, h = float(row[i_o]), float(row[i_h])
            lo, c = float(row[i_l]), float(row[i_c])
            v = float(row[i_v])
            n = float(row[i_n]) if i_n >= 0 and row[i_n] else 0.0
        except (IndexError, ValueError, TypeError):
            continue
        if not sym:
            continue
        day, mod = AH.ny_minute(ns)
        if day is None:
            continue
        if mod <= 16 * 60:
            pc = closes.get(sym)
            if pc is None or mod > pc[0]:
                closes[sym] = (mod, c)
        if sym in skip:
            continue
        if sym not in bars:
            pv = keep_prev.get(sym)
            keep = (sym == witness or (pv is not None and 0.3 <= pv <= KEEP_HI)
                    or (pv is None and c <= KEEP_HI))
            if not keep:
                skip.add(sym)
                continue
        if mod < PRE_OPEN or mod >= EXT_CLOSE:
            continue
        bars.setdefault(sym, []).append((int(ns / 1e6), o, h, lo, c, v, n, mod))
    for b in bars.values():
        b.sort(key=lambda x: x[0])
    return bars, {k: v[1] for k, v in closes.items()}


# ── دوالُّ نقيّة ───────────────────────────────────────────────────────────────
def anchor_feat(rows8: list, cut_ms: int) -> tuple:
    """`F9`: هل أطلقت بوّابةُ الإنتاج مِرساةً على الشموع قبل القرار؟ — بالاسم
    (`KS.prescreen` مرشِّحٌ سوبرست ثم `KS.first_anchor` ⟶ `S.liq_stage_events`)."""
    rows6 = [(b[0], b[1], b[2], b[3], b[4], b[5]) for b in rows8]
    if not rows6 or not KS.prescreen(rows6):
        return 0, None
    e = KS.first_anchor(rows6)
    if not e:
        return 0, None
    return 1, (cut_ms - int(e["anchor_ms"])) / 60_000.0


def window_label(sess_bars: list, start: int, end: int, ref: float) -> dict:
    """وسمُ نافذةٍ [start, end) بدقائق نيويورك: القمّةُ ودولارُها وبلوغُ ‏+80% (بشرط
    الأرضية) وزمنُ أوّل بلوغ. `ref` سعرُ المرجع عند القرار."""
    w = [b for b in sess_bars if start <= b[7] < end]
    if not w or not ref or ref <= 0:
        return {"max": None, "usd": 0.0, "hit80": 0, "t80": None, "n": 0}
    mx = max(b[2] for b in w)
    usd = sum(b[4] * b[5] for b in w)
    thr = ref * (1.0 + HIT_PCT / 100.0)
    hit = 1 if (mx >= thr and usd >= LABEL_MIN_USD) else 0
    t80 = next((b[7] - start for b in w if b[2] >= thr), None) if hit else None
    return {"max": (mx / ref - 1.0) * 100.0, "usd": usd, "hit80": hit, "t80": t80,
            "n": len(w)}


def ladder(sess_bars: list, start: int, end: int, ref: float) -> dict:
    w = [b for b in sess_bars if start <= b[7] < end]
    if not w or not ref or ref <= 0:
        return {f"hit{int(p)}_10": 0 for p in LADDER}
    mx = max(b[2] for b in w)
    usd = sum(b[4] * b[5] for b in w)
    return {f"hit{int(p)}_10": (1 if (mx >= ref * (1 + p / 100.0) and usd >= LABEL_MIN_USD)
                                else 0) for p in LADDER}


def topk_hits(rows: list, key: str, k: int = TOPK, label: str = "hit80_10",
              asc: bool = False) -> tuple:
    """(إصاباتُ أعلى k بالمفتاح · عددُ المرشَّحين المرتَّبين) — كسرُ التعادل بالرمز."""
    cand = [r for r in rows if r.get(key) is not None and not r.get(PF.ROW_WIT)]
    if not cand:
        return 0, 0
    top = PF.order_rows(cand, key, k, asc)      # 🔒 الترتيبُ من المصدر الواحد
    return sum(1 for r in top if r.get(label)), len(cand)


# ── التشغيل ───────────────────────────────────────────────────────────────────
def _decision_rows_ah(day: str, info: dict, bars: dict, prev_close: dict,
                      universe: set, hist: dict, witness: str):
    """صفوفُ قرار `AH` ليوم `day`."""
    open_min, close_min = info["open_ny_min"], info["close_ny_min"]
    cut = close_min - DECISION_LEAD
    out = []
    for sym in sorted(universe | ({witness} if witness in bars else set())):
        b = bars.get(sym)
        if not b:
            continue
        pc = prev_close.get(sym)
        pre = [x for x in b if PRE_OPEN <= x[7] < open_min]
        reg_cut = [x for x in b if open_min <= x[7] < cut]
        post = [x for x in b if close_min <= x[7] < EXT_CLOSE]
        f = core_feats(reg_cut, pre, pc, cut) if pc else None
        if f is None:
            continue
        ref = f["price"]
        cut_ms = int(dt.datetime.combine(dt.date.fromisoformat(day), dt.time(cut // 60, cut % 60),
                                         tzinfo=NY).timestamp() * 1000)
        a, ago = anchor_feat(pre + reg_cut, cut_ms)
        f.update({"anchor": a, "anchor_min_ago": ago})
        f.update(rolling_feats(hist.get(sym, []), ref, f["usd_day"]))
        f.update({"post_usd": None, "post_ret": None, "post_hi_ret": None,
                  "post_share": None})
        row = {PF.ROW_DAY: day, PF.ROW_SESS: "AH", PF.ROW_SYM: sym, "ref": ref,
               PF.ROW_WIT: 1 if sym == witness else 0}
        row.update({k: _r(v) for k, v in f.items()})
        for w in WINDOWS:
            lab = window_label(post, close_min, close_min + w, ref)
            row[f"max{w}"] = _r(lab["max"], 2)
            row[f"usd{w}"] = _r(lab["usd"], 0)
            row[f"hit80_{w}"] = lab["hit80"]
            if w == 10:
                row["t80_10"] = lab["t80"]
                row.update(ladder(post, close_min, close_min + 10, ref))
        labs = window_label(post, close_min, EXT_CLOSE, ref)
        row["maxs"], row["hit80_s"], row["usds"] = _r(labs["max"], 2), labs["hit80"], _r(labs["usd"], 0)
        out.append(row)
    return out


def _pending_pm(day: str, info: dict, bars: dict, prev_close: dict,
                next_universe: set, hist_after: dict, witness: str) -> dict:
    """ميزاتُ قرار `PM` (من اليوم `day` كاملًا) لرموز كون الغد — تُحسم بشموع الغد."""
    open_min, close_min = info["open_ny_min"], info["close_ny_min"]
    out = {}
    for sym in sorted(next_universe | ({witness} if witness in bars else set())):
        b = bars.get(sym)
        if not b:
            continue
        pc = prev_close.get(sym)
        pre = [x for x in b if PRE_OPEN <= x[7] < open_min]
        reg = [x for x in b if open_min <= x[7] < close_min]
        post = [x for x in b if close_min <= x[7] < EXT_CLOSE]
        f = core_feats(reg, pre, pc, close_min) if pc else None
        if f is None:
            continue
        reg_close = reg[-1][4]
        vol_all = sum(x[5] for x in b)
        pf = post_feats(post, reg_close, vol_all)
        ref = pf.pop("post_last") or reg_close
        f.update(pf)
        cut_ms = int(dt.datetime.combine(dt.date.fromisoformat(day), dt.time(19, 59),
                                         tzinfo=NY).timestamp() * 1000)
        a, ago = anchor_feat(pre + reg + post, cut_ms)
        f.update({"anchor": a, "anchor_min_ago": ago})
        f.update(rolling_feats(hist_after.get(sym, []), ref, f["usd_day"]))
        f["price"] = ref
        out[sym] = {"prev_day": day, "ref": ref,
                    PF.ROW_WIT: 1 if sym == witness else 0,
                    "f": {k: _r(v) for k, v in f.items()}}
    return out


def _resolve_pm(day: str, info: dict, bars: dict, pending: dict) -> list:
    """يحسم صفوفَ `PM` المعلَّقة بشموع بريماركت `day`."""
    open_min = info["open_ny_min"]
    out = []
    for sym, p in pending.items():
        b = bars.get(sym) or []
        pre = [x for x in b if PRE_OPEN <= x[7] < open_min]
        ref = p["ref"]
        row = {PF.ROW_DAY: day, PF.ROW_SESS: "PM", PF.ROW_SYM: sym, "ref": ref,
               PF.ROW_WIT: p["wit"],
               "prev_day": p["prev_day"]}
        row.update(p["f"])
        for w in WINDOWS:
            lab = window_label(pre, PRE_OPEN, PRE_OPEN + w, ref)
            row[f"max{w}"] = _r(lab["max"], 2)
            row[f"usd{w}"] = _r(lab["usd"], 0)
            row[f"hit80_{w}"] = lab["hit80"]
            if w == 10:
                row["t80_10"] = lab["t80"]
                row.update(ladder(pre, PRE_OPEN, PRE_OPEN + 10, ref))
        labs = window_label(pre, PRE_OPEN, open_min, ref)
        row["maxs"], row["hit80_s"], row["usds"] = _r(labs["max"], 2), labs["hit80"], _r(labs["usd"], 0)
        out.append(row)
    return out


def _summ_day(bars: dict, info: dict, prev_close: dict) -> dict:
    """ملخّصُ اليوم لكلّ رمزٍ محتفَظٍ به (للذاكرة المتدحرجة)."""
    open_min, close_min = info["open_ny_min"], info["close_ny_min"]
    out = {}
    for sym, b in bars.items():
        reg = [x for x in b if open_min <= x[7] < close_min]
        if not reg:
            continue
        pc = prev_close.get(sym)
        c = reg[-1][4]
        out[sym] = {"c": c, "hi": max(x[2] for x in reg), "lo": min(x[3] for x in reg),
                    "usd": sum(x[4] * x[5] for x in reg),
                    "ret": (c / pc - 1.0) if pc else None}
    return out


class Acc:
    """عدّاداتُ التقرير لكلّ جلسة: الصفوفُ والإصاباتُ لكلّ نافذة · و`P@10` للمفاتيح
    المنفردة والشاهدَين الساذجَين — تُحسب لكلّ قرارٍ لحظةَ اكتماله (بلا حفظ الصفوف)."""

    def __init__(self):
        self.rows = {"AH": 0, "PM": 0}
        self.dec = {"AH": 0, "PM": 0}
        self.hits = {s: {w: 0 for w in list(WINDOWS) + ["s"]} for s in ("AH", "PM")}
        self.ladder = {s: {int(p): 0 for p in LADDER} for s in ("AH", "PM")}
        self.top = {s: {} for s in ("AH", "PM")}      # key -> [hits, decisions_with_cand]
        self.t80 = {"AH": [], "PM": []}
        self.wit_bad = 0
        self.lookahead = 0

    def add_decision(self, sess: str, rows: list):
        real = [r for r in rows if not r.get(PF.ROW_WIT)]
        for r in rows:
            if r.get(PF.ROW_WIT) and (r["hit80_10"] or r["hit80_s"]):
                self.wit_bad += 1
        if not real:
            return
        self.dec[sess] += 1
        self.rows[sess] += len(real)
        for w in WINDOWS:
            self.hits[sess][w] += sum(r[f"hit80_{w}"] for r in real)
        self.hits[sess]["s"] += sum(r["hit80_s"] for r in real)
        for p in LADDER:
            self.ladder[sess][int(p)] += sum(r.get(f"hit{int(p)}_10", 0) for r in real)
        self.t80[sess] += [r["t80_10"] for r in real if r.get("t80_10") is not None]
        keys = [(f, False) for f in FEATS_DESC] + [(f, True) for f in FEATS_ASC]
        for f, asc in keys:
            h, n = topk_hits(real, f, asc=asc)
            if n:
                t = self.top[sess].setdefault(f, [0, 0])
                t[0] += h
                t[1] += 1

    def report(self, year_tag: str):
        log("\n" + "=" * 78)
        log(f"🌙⏱️ T-PRESESSION — {year_tag} · العقد presession_prereg.md (مدفوع قبل أي رقم)")
        log("=" * 78)
        for s in ("AH", "PM"):
            n, d = self.rows[s], self.dec[s]
            if not n:
                log(f"\n【{s}】 لا صفوف.")
                continue
            log(f"\n【{s}】 قرارات {d} · صفوف {n:,} · وسيطُ الكون/قرار {n / max(1, d):.0f}")
            for w in list(WINDOWS) + ["s"]:
                h = self.hits[s][w]
                lo, hi = KS.wilson(h, n)
                log(f"   نافذة {w if w != 's' else 'الجلسة'}: منفجرون +80% = {h} "
                    f"({h / n * 100:.3f}% [{lo:.3f}·{hi:.3f}]) · لكلّ قرار {h / max(1, d):.2f}")
            lad = " · ".join(f"+{p}% {self.ladder[s][p]}" for p in sorted(self.ladder[s]))
            log(f"   سلّمٌ وصفيّ (‏10 دقائق): {lad}")
            if self.t80[s]:
                log(f"   زمنُ أوّل بلوغ +80% (دقائق من بدء الجلسة، وسيط): "
                    f"{statistics.median(self.t80[s]):.0f} · n={len(self.t80[s])}")
            base = self.hits[s][10] / n
            log(f"   P@{TOPK} بالمفاتيح المنفردة (S0) والشاهدَين — الحاكمُ يُقاس في التقرير "
                f"(2025 خارج العيّنة) · base={base * 100:.3f}%:")
            items = sorted(self.top[s].items(), key=lambda kv: -(kv[1][0] / max(1, kv[1][1])))
            for f, (h, dd) in items:
                tag = next((b for b, ff in BASELINES.items() if ff == f), "")
                p = h / max(1, dd * TOPK)
                lift = (p / base) if base > 0 else float("nan")
                log(f"      {f:14} {'(' + tag + ')' if tag else '':5} إصابات {h:4} من "
                    f"{dd * TOPK:6} ⇒ P@10 {p * 100:.3f}% · lift {lift:5.1f}×")
        log(f"\n🔒 V1 خرقُ النظر المستقبليّ: {self.lookahead} (يجب 0) · "
            f"V3 شاهدُ الضبط {WITNESS}: صفوفٌ منفجرة {self.wit_bad} (يجب 0)")


def year_range(year: str, end_env: str = "") -> tuple:
    """(‏أوّلُ يومٍ · آخرُه) لسنةٍ مقيسة — و`end_env` فارغٌ ⇒ **السنةُ كاملةً**.

    🔒 الافتراضُ بت-بت: أرقامُ 2023/2024/2025 المنشورة تبقى قابلةً للإعادة
    حرفيًّا. و«السنةُ الجزئيّة» **تُعلَن ولا تُخمَّن** (‏`PRESESSION_END`) —
    فسنةٌ جارية تنتهي عند آخرِ يومٍ نُشر ملفُّه، وما بعده ليس «مفقودًا».
    """
    end = (end_env or "").strip() or f"{year}-12-31"
    return f"{year}-01-01", end


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("PRESESSION_YEAR") or "").strip()
    one_day = (os.environ.get("PRESESSION_DAY") or "").strip()
    syms_env = [s.strip().upper() for s in (os.environ.get("PRESESSION_SYMS") or "").split(",")
                if s.strip()]
    if one_day:
        days = [one_day]
        seed_days = KS.weekdays(
            (dt.date.fromisoformat(one_day) - dt.timedelta(days=45)).isoformat(),
            (dt.date.fromisoformat(one_day) - dt.timedelta(days=1)).isoformat())[-SEED_DAYS:]
    elif year:
        d0, d1 = year_range(year, os.environ.get("PRESESSION_END") or "")
        days = KS.weekdays(d0, d1)
        seed_days = KS.weekdays(f"{int(year) - 1}-11-15", f"{int(year) - 1}-12-31")[-SEED_DAYS:]
    else:
        print("⛔ لا PRESESSION_YEAR ولا PRESESSION_DAY.")
        return 2
    tag = one_day or year
    log(f"🌙⏱️ T-PRESESSION — {'يوم ' + one_day if one_day else 'سنة ' + year} · أيام {len(days)} · "
        f"بذرة {len(seed_days)} · كون [{PRICE_LO}, {PRICE_HI}]$ · القرارُ قبل الجلسة بـ{DECISION_LEAD} دقائق · "
        f"الوسمُ +{HIT_PCT:g}% بأرضية ${LABEL_MIN_USD:,.0f} · النوافذ {WINDOWS} · الشاهد {WITNESS}")
    if year and (os.environ.get("PRESESSION_END") or "").strip():
        log(f"⚠️ **سنةٌ جزئيّة**: المدى {days[0] if days else '—'} ⟶ {days[-1] if days else '—'} "
            f"(‏آخرُ يومٍ نُشر ملفُّه) — وما بعده **ليس مفقودًا**. وعطلاتُ البوّابة "
            f"مأخوذةٌ للسنة **كاملةً** ⇒ التغطيةُ هنا **متساهلة** ولا تُقرأ تصديقًا.")
    log(f"🔒 بوّابةُ المِرساة الإنتاجيّة بالاسم: رفعةٌ {S.LIQ_MIN_MOVE_PCT:g}% · "
        f"${S.LIQ_MIN_USD:,.0f} تراكميًّا على {S.LIQ_CUM_MINUTES} دقائق · "
        f"قفزةُ حجمٍ {S.CONFIG['IGNITION_VOL_MULT']:g}× · نافذةٌ {PROD_WIN} دقيقة — أرقامُ المالك لا تُمَسّ")
    acc = Acc()
    prev_close: dict = {}
    hist: dict = {}
    pending: dict = {}
    n_files = n_missing = n_pm_dropped = 0
    out_path = f"presession_rows_{tag}.jsonl.gz"
    fout = gzip.open(out_path, "wt", encoding="utf-8")
    t_start = time.time()
    last_day_rows = {"AH": [], "PM": []}
    for di, day in enumerate(seed_days + days):
        seeding = di < len(seed_days)
        info = MC.session_info(day)
        if info.get("open_ny_min") is None:
            if not seeding:
                n_missing += 1
            continue
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
                if pending:
                    n_pm_dropped += len(pending)
                    pending = {}
            continue
        dest = f"/tmp/presession-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            if not seeding:
                n_missing += 1
                if pending:
                    n_pm_dropped += len(pending)
                    pending = {}
            continue
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes = parse_day_ext(fh, prev_close)
        except (OSError, KeyError, ValueError) as e:
            log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            if not seeding:
                n_missing += 1
            try:
                os.remove(dest)
            except OSError:
                pass
            continue
        try:
            os.remove(dest)
        except OSError:
            pass
        universe = {s for s, c in prev_close.items() if PRICE_LO <= c <= PRICE_HI}
        try:
            # ① حسمُ PM المعلَّق من الأمس بشموع بريماركت اليوم
            if pending and not seeding:
                pm_rows = _resolve_pm(day, info, bars, pending)
                acc.add_decision("PM", pm_rows)
                for r in pm_rows:
                    fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                last_day_rows["PM"] = pm_rows
            pending = {}
            # ② قرارُ AH لليوم
            if not seeding:
                ah_rows = _decision_rows_ah(day, info, bars, prev_close, universe, hist, WITNESS)
                acc.add_decision("AH", ah_rows)
                for r in ah_rows:
                    fout.write(json.dumps(r, ensure_ascii=False) + "\n")
                last_day_rows["AH"] = ah_rows
                n_files += 1
            # ③ ملخّصُ اليوم ⟵ الذاكرة · ثم قرارُ PM للغد (بذاكرةٍ تشمل اليوم)
            summ = _summ_day(bars, info, prev_close)
            for sym, d in summ.items():
                h = hist.setdefault(sym, [])
                h.append(d)
                if len(h) > ROLL_N:
                    del h[:-ROLL_N]
            next_universe = {s for s, c in closes.items() if PRICE_LO <= c <= PRICE_HI}
            pending = _pending_pm(day, info, bars, prev_close, next_universe, hist, WITNESS)
        except LookAhead as e:
            acc.lookahead += 1
            log(f"   ⛔ V1 {day}: {e}")
        prev_close.update(closes)
        if seeding:
            if di == len(seed_days) - 1:
                log(f"🌱 البذرة اكتملت: {len(prev_close):,} إغلاقًا · ذاكرة {len(hist):,} رمزًا")
            continue
        if n_files % 20 == 0:
            el = (time.time() - t_start) / 60.0
            log(f"   📦 {n_files}/{len(days)} يومًا · كون {len(universe):,} · AH {acc.rows['AH']:,} "
                f"صفًّا (+80%/10د {acc.hits['AH'][10]}) · PM {acc.rows['PM']:,} (+80%/10د "
                f"{acc.hits['PM'][10]}) · {el:.0f} دقيقة")
    fout.close()
    # ④ وضعُ اليوم الواحد: أسماءُ المنفجرين وترتيبُ الرموز المطلوبة (تشخيصٌ لا حكم)
    if one_day:
        for s in ("AH", "PM"):
            rows = [r for r in last_day_rows[s] if not r.get(PF.ROW_WIT)]
            hits = sorted((r for r in rows if r["hit80_10"] or r["hit80_s"]),
                          key=lambda r: -(r["maxs"] or 0))
            log(f"\n【{s} {one_day}】 كون {len(rows)} · منفجرون +80% (10د/الجلسة): "
                + (", ".join(f"{r['sym']}({r['max10']}/{r['maxs']}%)" for r in hits[:30]) or "لا شيء"))
            for sym in syms_env:
                r = next((x for x in rows if x["sym"] == sym), None)
                if not r:
                    log(f"   {sym}: خارج الكون/بلا صفّ")
                    continue
                ranks = {}
                for f, asc in [(f, False) for f in FEATS_DESC] + [(f, True) for f in FEATS_ASC]:
                    cand = [x for x in rows if x.get(f) is not None]
                    cand.sort(key=lambda x: ((x[f] if asc else -x[f]), x["sym"]))
                    ranks[f] = next((i + 1 for i, x in enumerate(cand) if x["sym"] == sym), None)
                best = sorted((v, k) for k, v in ranks.items() if v)[:5]
                log(f"   {sym}: ref ${r['ref']} · max10 {r['max10']}% · maxs {r['maxs']}% · "
                    f"أفضلُ رتبٍ: " + " · ".join(f"{k}#{v}" for v, k in best))
    acc.report(tag)
    log(f"\n📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · صفوفُ PM أُسقطت لغياب الغد {n_pm_dropped} · "
        f"الملفّ {out_path} ({os.path.getsize(out_path) / 1e6:.1f}MB) · {(time.time() - t_start) / 60:.0f} دقيقة")
    if not one_day:
        n_rows = acc.rows["AH"] + acc.rows["PM"]
        bad, line = KS.coverage_verdict(year, n_files, n_missing, n_rows)
        log(line.replace("مراسٍ", "صفوف"))
        if bad:
            log("\n⛔ بوّابةُ صلاحية V2: تغطيةٌ ناقصة أو صفرُ صفوف ⇒ عطبُ أداةٍ لا نتيجة.")
            return 3
    if acc.lookahead:
        log("\n⛔ V1: نظرٌ مستقبليّ مكتشَف ⇒ عطبُ أداة.")
        return 3
    if acc.wit_bad:
        log(f"\n⛔ V3: الشاهد {WITNESS} «انفجر» {acc.wit_bad} مرّة ⇒ عطبُ وسم.")
        return 3
    if not (acc.rows["AH"] + acc.rows["PM"]):
        log("\n⛔ V4: صفرُ صفوف ⇒ no-op.")
        return 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
