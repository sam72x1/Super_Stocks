#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""💥🔗 `T-LINK100` — «الرابطُ المشترك» لكلّ سهمٍ انفجر ‏+100% فأكثر.

**العقد:** `link100_prereg.md` (مدفوعٌ ومدموجٌ `13be23e9` قبل هذا الملفّ). أمرُ المالك
«ابيك تجيب جميع الاسهم اللي انفجرت بنسبة ١٠٠٪ و اكثر … الين تجيب الرابط المشترك لها».

**المجتمع (§②):** كلُّ السوق الأمريكيّ من الشموع اليوميّة **المجمَّعة**
`/v2/aggs/grouped/.../{day}?adjusted=false` — **تخدم المشطوبين بالبناء** (السهمُ
موجودٌ في يومه ولو شُطب بعده) ⇒ **لا انحيازَ بقاء**. الحاكمُ
`high(d)/close(d−1) ≥ 2.0` و`close(d−1)` في ‏[`PRICE_LO`, 20$] · وقراءةُ الإغلاق
`close(d)/close(d−1) ≥ 2` **تُطبَع ولا تحكم**.

🔴 **ولماذا لا تُعاد `presession_radar.polygon_grouped`:** هي `adjusted=true`
والعقدُ يشترط `adjusted=false` صراحةً (وإلّا اختفى أثرُ التقسيم الذي يحرسه
`V-L2`) ⇒ جالبٌ مستقلٌّ بمعاملٍ مختلف، **لا منطقَ حسمٍ مكرَّر**.

🔒 **إعادةُ استعمالٍ بالاسم:** `kasih_scan.PRICE_LO`/`wilson` ·
`market_calendar.is_trading_day` · `Super_stock.rsi` · `tier_fwd_report.fetch_day`
(الطبقةُ الدقيقة) · `optrade_arms.selfcheck_readonly`/`no_config_assign`
(حارسا القراءة-فقط على مصدرِ هذا الملفّ).

**الشاهدان (§②):** `CX` مقطعيٌّ مطابَق (اليومُ نفسُه · خانةُ السعر · عُشرُ الدولار ·
ولم يتحرّك ‏≥30%) · و`CC` ذاتيٌّ زمنيّ (الرمزُ نفسُه عند `d−21` بلا انفجارٍ في
‏[d−41, d−21]).

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ حالة · صفرُ إسنادٍ إلى إعدادات الإنتاج ·
والإنتاجُ لا يستورد هذا الملفّ.

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 لا مفتاح · 3 تغطيةُ أيّام `grouped`
دون الحدّ · 4 صفرُ أحداث · **5 شاهدُ التكامل `V-L4` ساقط** · **6 حارسٌ ساقط** ·
**9 «لا حكم» (الفرعُ 3)**.
"""
import datetime as dt
import math
import os
import statistics as st
import sys

import requests

from kasih_scan import PRICE_LO, wilson                          # بالاسم
from market_calendar import is_trading_day                       # بالاسم
from optrade_arms import no_config_assign, selfcheck_readonly    # بالاسم
from tier_fwd_report import fetch_day                            # بالاسم
from opcurve_probe import ny_hour                                # بالاسم

# ═══════════════ ⓪ الحدود — مثبَّتةٌ بالعقد §② ═════════════════════════════════
YEARS = [y.strip() for y in
         os.environ.get("LINK100_YEARS", "2023,2024,2025").split(",") if y.strip()]
DRY = os.environ.get("LINK100_DRY", "").strip() == "1"
LIVE_MD = "explosions100_live.md"                 # `V-L4`

PRICE_HI = 20.0                   # سقفُ إغلاقِ الأمس (§②)
EXPL_X = 2.0                      # `high(d)/close(d−1) ≥ 2` = ‏+100%
CTRL_MAX_MOVE = 0.30              # الشاهدُ `CX` لم يتحرّك ‏≥30% في `d`
FOLD_DAYS = 20                    # الحدثُ الأوّل للرمز في نافذة 20 جلسة
SPLIT_GUARD = 3                   # `V-L2` — تقسيمٌ في ‏[d−3, d+3] ⇒ استبعاد
CC_BACK = 21                      # الشاهدُ الذاتيّ عند `d−21`
CC_CLEAR = 41                     # بلا انفجارٍ في ‏[d−41, d−21]
HIST_BACK_DAYS = 420              # تقويميّة ⇒ تكفي 252 جلسةً قبل `d−21`
PM_CAP = 1500                     # سقفُ الطبقة الدقيقة لكلّ سنة (§②) — يُطبَع
DEC_N = 10                        # عشراتُ الدولار اليوميّ
MIN_DAYS_COVER = 0.95             # `V-L1`
MIN_MATCH = 0.90                  # `V-L3`
MIN_BUCKET_N = 50                 # `LK1`
RATIO_MIN = 2.0                   # `LK1`
ALPHA = 0.05                      # `LK1` — يُقسَم على عدد السلال (بونفيروني)
V_L4_MIN = 0.80                   # `V-L4`
RC_OK, RC_NOKEY, RC_COVER, RC_NOEVENT = 0, 2, 3, 4
RC_LIVE, RC_GUARD, RC_NOVERDICT = 5, 6, 9

# قائمةُ الميزات **مُغلَقةٌ** (§③) — لا تُضاف ميزةٌ بعد أيّ رقم.
FEATURES = ("vol_x", "ret5", "range_c", "gap1", "dd52", "sma_pos", "rsi14",
            "quiet", "px", "usd1", "rsplit180", "pm_gap", "pm_usd")
DAILY_FEATURES = FEATURES[:11]                   # ما يُحسَب بلا طبقةٍ دقيقة
PM_FEATURES = FEATURES[11:]


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ═══════════════ ① الجلب — فاشلٌ-آمنٌ دائمًا ═══════════════════════════════════
def grouped_day(day: str, key: str, get=None):
    """كلُّ السوق في نداءٍ واحد بـ`adjusted=false` ⟶ `{رمز: (o,h,l,c,v)}` أو `None`."""
    g = requests.get if get is None else get
    try:
        r = g("https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/"
              f"{day}?adjusted=false",
              headers={"Authorization": f"Bearer {key}"}, timeout=40)
        if getattr(r, "status_code", 0) != 200:
            return None
        out = {}
        for b in (r.json() or {}).get("results") or []:
            try:
                s = str(b.get("T") or "").strip().upper()
                o, h, lo = float(b["o"]), float(b["h"]), float(b["l"])
                c, v = float(b["c"]), float(b.get("v") or 0.0)
            except (TypeError, ValueError, KeyError):
                continue
            if s and c > 0 and h > 0:
                out[s] = (o, h, lo, c, v)
        return out or None
    except Exception:                                            # noqa: BLE001
        return None


def ticker_daily(sym: str, d0: str, d1: str, key: str, get=None):
    """شموعٌ يوميّة `adjusted=false` ⟶ `[(date,o,h,l,c,v)]` أو `None`."""
    g = requests.get if get is None else get
    try:
        r = g(f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
              f"/range/1/day/{d0}/{d1}?adjusted=false&sort=asc&limit=50000",
              headers={"Authorization": f"Bearer {key}"}, timeout=40)
        if getattr(r, "status_code", 0) != 200:
            return None
        out = []
        for b in (r.json() or {}).get("results") or []:
            try:
                d = dt.datetime.utcfromtimestamp(b["t"] / 1000).date().isoformat()
                out.append((d, float(b["o"]), float(b["h"]), float(b["l"]),
                            float(b["c"]), float(b.get("v") or 0.0)))
            except (TypeError, ValueError, KeyError):
                continue
        return out or None
    except Exception:                                            # noqa: BLE001
        return None


def splits_of(sym: str, key: str, get=None):
    """تقسيماتُ الرمز ⟶ `[(تاريخ، عكسيّ؟)]` — و`None` عند الإخفاق (يُعَدّ)."""
    g = requests.get if get is None else get
    try:
        r = g(f"https://api.polygon.io/v3/reference/splits?ticker={sym.upper()}"
              "&limit=1000", headers={"Authorization": f"Bearer {key}"},
              timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        out = []
        for s in (r.json() or {}).get("results") or []:
            try:
                d = str(s["execution_date"])
                sf, st_ = float(s["split_from"]), float(s["split_to"])
            except (TypeError, ValueError, KeyError):
                continue
            out.append((d, st_ < sf))            # عكسيٌّ = «إلى» أصغرُ من «من»
        return out
    except Exception:                                            # noqa: BLE001
        return None


# ═══════════════ ② المجتمع — الأحداثُ والشاهدُ المقطعيّ ═══════════════════════
def day_events(g_prev: dict, g_day: dict) -> list:
    """أحداثُ اليوم: `high(d)/close(d−1) ≥ 2` وإغلاقُ الأمس داخلَ النطاق.

    يُرجع `[(رمز، نسبةُ الأعلى، نسبةُ الإغلاق، إغلاقُ الأمس، دولارُ الأمس)]` —
    **وقراءةُ الإغلاق تُحمَل ولا تحكم** (§②)."""
    out = []
    for sym, (_o, h, _l, c, _v) in (g_day or {}).items():
        pv = (g_prev or {}).get(sym)
        if not pv:
            continue
        pc, pvol = pv[3], pv[4]
        if not (PRICE_LO <= pc <= PRICE_HI) or pvol <= 0:
            continue
        if h / pc >= EXPL_X:
            out.append((sym, h / pc, c / pc, pc, pc * pvol))
    return out


def px_bucket(c: float) -> str:
    if c < 1.0:
        return "<1$"
    if c < 3.0:
        return "1-3$"
    if c < 10.0:
        return "3-10$"
    return "10-20$"


def dollar_deciles(g_prev: dict) -> list:
    """حدودُ عشراتِ الدولار اليوميّ على كون اليوم — حتميّةٌ ومطبوعةُ الأساس."""
    vals = sorted(pv[3] * pv[4] for pv in (g_prev or {}).values()
                  if pv[3] > 0 and pv[4] > 0)
    if not vals:
        return []
    return [vals[int(len(vals) * i / DEC_N)] for i in range(1, DEC_N)]


def decile_of(v: float, edges: list) -> int:
    i = 0
    for e in edges:
        if v >= e:
            i += 1
    return i


def pick_cx(events: list, g_prev: dict, g_day: dict) -> dict:
    """شاهدٌ مقطعيٌّ لكلّ حدث — **حتميٌّ**: أوّلُ رمزٍ أبجديًّا في الخليّة لم يُستعمَل.

    الخليّة = (خانةُ السعر، عُشرُ الدولار) لإغلاقِ الأمس · والشاهدُ **لم يتحرّك
    ‏≥30%** في `d` (بالأعلى مقابل إغلاق الأمس)."""
    edges = dollar_deciles(g_prev)
    pool = {}
    ev_syms = {e[0] for e in events}
    for sym, pv in (g_prev or {}).items():
        if sym in ev_syms:
            continue
        cur = (g_day or {}).get(sym)
        pc, pvol = pv[3], pv[4]
        if not cur or pvol <= 0 or not (PRICE_LO <= pc <= PRICE_HI):
            continue
        if cur[1] / pc - 1.0 >= CTRL_MAX_MOVE:
            continue
        pool.setdefault((px_bucket(pc), decile_of(pc * pvol, edges)),
                        []).append(sym)
    for k in pool:
        pool[k].sort()
    used, out = set(), {}
    for sym, _hx, _cx, pc, usd in sorted(events):
        cell = (px_bucket(pc), decile_of(usd, edges))
        cand = next((s for s in pool.get(cell, []) if s not in used), None)
        if cand:
            used.add(cand)
            out[sym] = cand
    return out


def fold_events(rows: list) -> list:
    """الحدثُ الأوّل للرمز في نافذة `FOLD_DAYS` جلسةً يُعَدّ (§②)."""
    out, last = [], {}
    for r in sorted(rows, key=lambda x: (x["sym"], x["day_i"])):
        prev = last.get(r["sym"])
        # 🔒 النافذةُ تُقاس من آخر حدثٍ **معدود** لا من آخر حدثٍ مرئيّ — وإلّا
        #    ابتلعت سلسلةٌ يوميّةٌ متّصلة مدًى بلا حدّ (أمسكه `LKA4`).
        if prev is not None and r["day_i"] - prev < FOLD_DAYS:
            continue
        last[r["sym"]] = r["day_i"]
        out.append(r)
    return sorted(out, key=lambda x: (x["day"], x["sym"]))


# ═══════════════ ③ الميزاتُ — قائمةٌ مُغلَقة (§③) ═════════════════════════════
def _bucket(v, edges, labels):
    if v is None:
        return None
    for e, lab in zip(edges, labels):
        if v < e:
            return lab
    return labels[-1]


def daily_feats(hist: list, i: int, rsplit: bool):
    """ميزاتُ ما قبل الانفجار من تاريخ الرمز — `i` فهرسُ يوم الحدث `d`.

    كلُّها من `[..d−1]` حصرًا ⇒ **صفرُ تسريب**."""
    if i < 1:
        return None
    p = hist[:i]                                  # ‏[..d−1] حصرًا
    if len(p) < 21:
        return None
    cl = [b[4] for b in p]
    vo = [b[5] for b in p]
    hi = [b[2] for b in p]
    lo = [b[3] for b in p]
    op = [b[1] for b in p]
    f = {}
    base = [v for v in vo[-20:-5] if v > 0]
    f["vol_x"] = _bucket((vo[-1] / st.median(base)) if base and vo[-1] else None,
                         (1.0, 3.0), ("<1", "1-3", "≥3"))
    f["ret5"] = _bucket((cl[-1] / cl[-6] - 1.0) if len(cl) >= 6 and cl[-6]
                        else None, (-0.20, 0.20), ("<-20%", "-20..+20%", ">+20%"))
    r5 = [hi[k] - lo[k] for k in range(-5, 0)]
    rb = [hi[k] - lo[k] for k in range(-20, -5)] if len(p) >= 20 else []
    mb = st.mean(rb) if rb else 0.0
    f["range_c"] = _bucket((st.mean(r5) / mb) if mb > 0 else None,
                           (0.5, 1.0), ("<0.5", "0.5-1", ">1"))
    f["gap1"] = _bucket((op[-1] / cl[-2] - 1.0) if len(cl) >= 2 and cl[-2]
                        else None, (0.0, 0.10), ("<0", "0-10%", ">10%"))
    hh = max(hi[-252:]) if hi else 0.0
    f["dd52"] = _bucket((cl[-1] / hh - 1.0) if hh > 0 else None,
                        (-0.90, -0.50), ("<-90%", "-90..-50%", ">-50%"))
    s20 = st.mean(cl[-20:]) if len(cl) >= 20 else None
    s50 = st.mean(cl[-50:]) if len(cl) >= 50 else None
    if s20 is None or s50 is None:
        f["sma_pos"] = None
    elif cl[-1] > max(s20, s50):
        f["sma_pos"] = "فوق"
    elif cl[-1] < min(s20, s50):
        f["sma_pos"] = "تحت"
    else:
        f["sma_pos"] = "بين"
    f["rsi14"] = _bucket(_rsi_last(cl[-60:]), (30.0, 50.0),
                         ("<30", "30-50", ">50"))
    q = None
    for back in range(1, len(p)):
        b = p[-back]
        if b[3] > 0 and b[2] / b[3] - 1.0 >= 0.50:
            q = back - 1
            break
    f["quiet"] = _bucket(q if q is not None else len(p),
                         (20, 60), ("<20", "20-60", ">60"))
    f["px"] = px_bucket(cl[-1])
    f["usd1"] = _bucket(cl[-1] * vo[-1], (50_000.0, 300_000.0),
                        ("<50k", "50-300k", ">300k"))
    f["rsplit180"] = "نعم" if rsplit else "لا"
    return f


def _rsi_last(closes: list):
    """`Super_stock.rsi` بالاسم على آخر الإغلاقات — و`None` عند قصر العيّنة."""
    if len(closes) < 20:
        return None
    try:
        import pandas as pd                                      # noqa: PLC0415
        from Super_stock import rsi                              # بالاسم
        v = rsi(pd.Series(closes)).iloc[-1]
        return None if v != v else float(v)                      # NaN ⇒ None
    except Exception:                                            # noqa: BLE001
        return None


def pm_feats(bars, prev_close: float):
    """`pm_gap`/`pm_usd` من شموع الدقيقة قبل ‏09:30 — أو `None` بلا بيانات."""
    pre = [b for b in (bars or []) if ny_hour(b[0]) < 9.5]
    if not pre or not prev_close:
        return {"pm_gap": None, "pm_usd": None}
    last = pre[-1][4]
    usd = sum(b[4] * b[5] for b in pre)
    return {"pm_gap": _bucket(last / prev_close - 1.0, (0.10, 0.30),
                              ("<10%", "10-30%", "≥30%")),
            "pm_usd": _bucket(usd, (100_000.0, 1_000_000.0),
                              ("<100k", "100k-1M", ">1M"))}


# ═══════════════ ④ الإثراءُ والمعيار (§④) ═════════════════════════════════════
def enrich(ev_rows: list, ct_rows: list, feat: str) -> dict:
    """لكلّ سلّة: حصّةُ المنفجرين ÷ حصّةُ الشاهد ‏+ فاصلا ويلسون (‏`wilson` بالاسم)."""
    ne = sum(1 for r in ev_rows if r.get(feat) is not None)
    nc = sum(1 for r in ct_rows if r.get(feat) is not None)
    out = {}
    if not ne or not nc:
        return out
    labs = sorted({r[feat] for r in ev_rows + ct_rows if r.get(feat) is not None})
    for lab in labs:
        ke = sum(1 for r in ev_rows if r.get(feat) == lab)
        kc = sum(1 for r in ct_rows if r.get(feat) == lab)
        pe, pc = ke / ne, kc / nc
        we, wc = wilson(ke, ne), wilson(kc, nc)                  # بالاسم
        out[lab] = {"ke": ke, "ne": ne, "kc": kc, "nc": nc,
                    "pe": pe * 100.0, "pc": pc * 100.0,
                    "ratio": (pe / pc) if pc > 0 else None,
                    "we": we, "wc": wc,
                    "disjoint": bool(we[0] > wc[1] or wc[0] > we[1])}
    return out


def z_bonf(n_tests: int) -> float:
    """`z` لبونفيروني — `α/عدد السلال` بوجهين (بلا scipy: تقريبُ الدالّة العكسيّة)."""
    a = max(ALPHA / max(1, n_tests), 1e-9)
    p = 1.0 - a / 2.0
    # Acklam-style مبسَّط: كافٍ لعتبةٍ تُطبَع وتُقارَن، ومطبوعٌ صراحةً
    t = math.sqrt(-2.0 * math.log(1.0 - p)) if p < 1 else 8.0
    z = t - (2.30753 + 0.27061 * t) / (1.0 + 0.99229 * t + 0.04481 * t * t)
    return abs(z)


def cell_pass(e_cx: dict, e_cc: dict, z: float) -> bool:
    """`LK1` لخليّةٍ واحدة: ‏≥2× مقابل الشاهدَين **معًا** · فاصلان منفصلان · n≥50."""
    if not e_cx or not e_cc:
        return False
    if (e_cx["ke"] < MIN_BUCKET_N):
        return False
    for e in (e_cx, e_cc):
        if not e or e["ratio"] is None or e["ratio"] < RATIO_MIN:
            return False
        lo, hi = wilson(e["ke"], e["ne"], z), wilson(e["kc"], e["nc"], z)
        if not (lo[0] > hi[1] or hi[0] > lo[1]):
            return False
    return True


def read_verdict(per_year: dict, guards: dict) -> tuple:
    """§④ بحرفه — والفروعُ الثلاثةُ كلٌّ في سطرها."""
    if not guards.get("pass"):
        return 3, ("لا حكم", "حارسٌ ساقط ⇒ لا يُفسَّر رقم")
    yrs = sorted(per_year)
    hits = None
    for y in yrs:
        s = per_year[y]
        hits = set(s) if hits is None else (hits & set(s))
    if hits:
        return 1, ("رابطٌ مقيس",
                   "سلّةٌ تعبر `LK1` في السنوات الثلاث ⇒ تسجيلٌ أماميٌّ جديد قبل أيّ استعمال")
    return 2, ("لا رابط", "الحرّاسُ خضراء ولا سلّةَ تعبر `LK1` في الثلاث")


# ═══════════════ ⑤ `V-L4` — شاهدُ التكامل على الحقبة الحيّة ═══════════════════
def live_events(path: str = LIVE_MD):
    """`(رمز، تاريخ)` من جدول «النظيفة» في `explosions100_live.md`."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return None
    if "## ①" not in txt:
        return None
    body = txt.split("## ①", 1)[1].split("## ②", 1)[0]
    out = []
    for ln in body.splitlines():
        p = [x.strip() for x in ln.split("|")]
        if len(p) < 5 or not p[1].isdigit():
            continue
        sym = p[2].strip("`").upper()
        day = p[3]
        if sym and len(day) == 10 and day[4] == "-":
            out.append((sym, day))
    return out or None


def v_l4(found: list, live: list) -> dict:
    """تُستعاد ‏≥80% من أحداث القائمة الحيّة بالرمز وتاريخٍ ضمن ‏±3 أيام."""
    if not live:
        return {"ok": False, "why": "قائمةُ الحقبة الحيّة غيرُ مقروءة"}
    idx = {}
    for r in found:
        idx.setdefault(r["sym"], []).append(r["day"])
    hit, miss = 0, []
    for sym, day in live:
        ds = idx.get(sym) or []
        d0 = dt.date.fromisoformat(day)
        if any(abs((dt.date.fromisoformat(x) - d0).days) <= SPLIT_GUARD
               for x in ds):
            hit += 1
        elif len(miss) < 8:
            miss.append(f"{sym}·{day}")
    sh = hit / len(live)
    return {"ok": sh >= V_L4_MIN, "share": sh, "hit": hit, "n": len(live),
            "miss": miss, "why": f"استُعيد {hit} من {len(live)} = {sh*100:.1f}%"}


# ═══════════════ ⑥ المسحُ لسنة ═════════════════════════════════════════════════
def year_days(year: str) -> list:
    d = dt.date(int(year), 1, 1)
    end = dt.date(int(year), 12, 31)
    out = []
    while d <= end:
        if is_trading_day(d.isoformat()):                        # بالاسم
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def scan_year(year: str, key: str) -> dict:
    """المرّةُ الأولى: أحداثٌ وشواهدُ مقطعيّة من `grouped` وحدَها."""
    days = year_days(year)
    got, prev, rows, cx_all = 0, None, [], {}
    for i, day in enumerate(days):
        g = grouped_day(day, key)
        if g is None:
            prev = None
            continue
        got += 1
        if prev is not None:
            evs = day_events(prev, g)
            if evs:
                cx = pick_cx(evs, prev, g)
                for sym, hx, cx_r, pc, usd in evs:
                    rows.append({"sym": sym, "day": day, "day_i": i,
                                 "hi_x": hx, "cl_x": cx_r, "prev_close": pc,
                                 "usd": usd, "ctrl": cx.get(sym)})
                cx_all[day] = cx
        prev = g
    cover = got / len(days) if days else 0.0
    folded = fold_events(rows)
    return {"year": year, "days": len(days), "got": got, "cover": cover,
            "raw": len(rows), "events": folded}


def enrich_rows(events: list, key: str, pm_budget: int) -> dict:
    """المرّةُ الثانية: تاريخُ كلّ رمزٍ مرّةً واحدة ⇒ ميزاتُ الحدث و`CC` و`CX`."""
    ev_rows, cc_rows, cx_rows = [], [], []
    dropped_split, no_hist, no_cc, pm_used = 0, 0, 0, 0
    hcache, scache = {}, {}

    def hist_of(sym, day):
        k = (sym, day)
        if k not in hcache:
            d0 = (dt.date.fromisoformat(day)
                  - dt.timedelta(days=HIST_BACK_DAYS)).isoformat()
            hcache[k] = ticker_daily(sym, d0, day, key)
        return hcache[k]

    def splits_cached(sym):
        if sym not in scache:
            scache[sym] = splits_of(sym, key)
        return scache[sym]

    for ev in events:
        sym, day = ev["sym"], ev["day"]
        sp = splits_cached(sym)
        d0 = dt.date.fromisoformat(day)
        if sp is None:
            dropped_split += 1
            continue
        if any(abs((dt.date.fromisoformat(x) - d0).days) <= SPLIT_GUARD
               for x, _rev in sp):
            dropped_split += 1
            continue
        h = hist_of(sym, day)
        if not h:
            no_hist += 1
            continue
        idx = next((k for k, b in enumerate(h) if b[0] == day), None)
        if idx is None:
            no_hist += 1
            continue
        rsp = any(0 <= (d0 - dt.date.fromisoformat(x)).days <= 180
                  for x, rev in sp if rev)
        f = daily_feats(h, idx, rsp)
        if f is None:
            no_hist += 1
            continue
        f.update({"pm_gap": None, "pm_usd": None, "_sym": sym, "_day": day})
        # ── الشاهدُ الذاتيّ `CC` عند `d−21` من التاريخ نفسِه (بلا نداءٍ إضافيّ) ──
        j = idx - CC_BACK
        if j >= 1:
            clear = True
            for k in range(max(1, idx - CC_CLEAR), j + 1):
                if h[k - 1][4] > 0 and h[k][2] / h[k - 1][4] >= EXPL_X:
                    clear = False
                    break
            if clear:
                cf = daily_feats(h, j, rsp)
                if cf:
                    cf.update({"pm_gap": None, "pm_usd": None,
                               "_sym": sym, "_day": h[j][0]})
                    cc_rows.append(cf)
                else:
                    no_cc += 1
            else:
                no_cc += 1
        else:
            no_cc += 1
        # ── الشاهدُ المقطعيّ `CX` ────────────────────────────────────────────
        cs = ev.get("ctrl")
        cxf = None
        if cs:
            ch = hist_of(cs, day)
            ci = next((k for k, b in enumerate(ch or []) if b[0] == day), None)
            if ch and ci is not None:
                csp = splits_cached(cs) or []
                crsp = any(0 <= (d0 - dt.date.fromisoformat(x)).days <= 180
                           for x, rev in csp if rev)
                cxf = daily_feats(ch, ci, crsp)
                if cxf:
                    cxf.update({"pm_gap": None, "pm_usd": None,
                                "_sym": cs, "_day": day})
        # ── الطبقةُ الدقيقة — بسقفٍ مُعلَنٍ ويُطبَع ─────────────────────────
        if pm_used < pm_budget:
            eb = fetch_day(sym, day, key)                        # بالاسم
            f.update(pm_feats(eb, ev["prev_close"]))
            if cxf and cs:
                cb = fetch_day(cs, day, key)
                ch2 = hist_of(cs, day)
                cpc = None
                if ch2:
                    k2 = next((k for k, b in enumerate(ch2) if b[0] == day), None)
                    cpc = ch2[k2 - 1][4] if k2 and k2 >= 1 else None
                cxf.update(pm_feats(cb, cpc))
            pm_used += 1
        ev_rows.append(f)
        if cxf:
            cx_rows.append(cxf)
    return {"ev": ev_rows, "cx": cx_rows, "cc": cc_rows,
            "dropped_split": dropped_split, "no_hist": no_hist,
            "no_cc": no_cc, "pm_used": pm_used,
            "match": (len(cx_rows) / len(ev_rows)) if ev_rows else 0.0}


# ═══════════════ ⑦ main ════════════════════════════════════════════════════════
def main() -> int:                                               # noqa: PLR0911, PLR0915
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    src = open(__file__, encoding="utf-8").read()
    if not (selfcheck_readonly(src) and no_config_assign(src)):   # بالاسم
        _log("⛔ حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط — خروج 6")
        return RC_GUARD
    _log("💥🔗 T-LINK100 — الرابطُ المشترك لمنفجري +100% (العقد link100_prereg.md)")
    _log(f"⚙️ السنوات: {' · '.join(YEARS)} · الحاكمُ high(d)/close(d−1) ≥ "
         f"{EXPL_X} · إغلاقُ الأمس في [{PRICE_LO:.2f}, {PRICE_HI:.0f}]$ · "
         f"طيُّ {FOLD_DAYS} جلسة · حارسُ تقسيمٍ ±{SPLIT_GUARD} يوم")
    _log("🌐 المصدر: grouped يوميّة adjusted=false ⇒ **بالمشطوبين** (لا انحياز بقاء)")
    scans, all_found = {}, []
    for y in YEARS:
        s = scan_year(y, key)
        scans[y] = s
        all_found.extend(s["events"])
        _log(f"📅 {y}: أيّامُ تداولٍ {s['days']} · جُلبت {s['got']} "
             f"({s['cover']*100:.1f}%) · أحداثٌ خام {s['raw']} ⇒ بعد الطيّ "
             f"{len(s['events'])}")
        if s["cover"] < MIN_DAYS_COVER:
            _log(f"⛔ V-L1 — تغطيةُ أيّام {y} دون {MIN_DAYS_COVER*100:.0f}% — خروج 3")
            return RC_COVER
    if not all_found:
        _log("⛔ صفرُ أحداث — خروج 4")
        return RC_NOEVENT
    live = live_events()
    vl4 = v_l4(all_found, live) if live else {"ok": None,
                                              "why": "القائمةُ الحيّةُ خارجَ السنوات المقيسة"}
    if live and YEARS and any(y == "2026" for y in YEARS):
        _log(f"🔒 V-L4: {vl4['why']}" + (f" · فائتٌ {vl4['miss']}"
                                          if not vl4["ok"] else ""))
        if not vl4["ok"]:
            _log("⛔ V-L4 ساقط — خروج 5")
            return RC_LIVE
    else:
        _log("ℹ️ V-L4 — شاهدُ التكامل يلزمه تشغيلُ 2026 (وصفيٌّ هنا): "
             f"{vl4.get('why')}")
    if DRY:
        _log("")
        _log("🧪 وضعُ الجدوى — أعدادُ المجتمع فقط · **صفرُ إثراءٍ وصفرُ فاصل**.")
        for y in YEARS:
            s = scans[y]
            _log(f"   {y}: أحداثٌ {len(s['events'])} · بشاهدٍ مقطعيّ "
                 f"{sum(1 for e in s['events'] if e.get('ctrl'))} "
                 f"({100*sum(1 for e in s['events'] if e.get('ctrl'))/max(1,len(s['events'])):.1f}%)")
        _log("⚠️ ودرسُ T-PMGATE: وضعُ الجدوى يُجيز ما يمرّ به وحدَه.")
        return RC_OK
    return report(scans, key, vl4)


def report(scans: dict, key: str, vl4: dict) -> int:             # noqa: PLR0915
    per_year, guards_ok = {}, True
    _log("")
    for y in YEARS:
        ev = scans[y]["events"]
        en = enrich_rows(ev, key, PM_CAP)
        _log(f"═══ {y} — أحداثٌ {len(en['ev'])} · شاهدٌ مقطعيّ {len(en['cx'])} "
             f"({en['match']*100:.1f}%) · شاهدٌ ذاتيّ {len(en['cc'])} ═══")
        _log(f"   مُستبعَدو التقسيم (±{SPLIT_GUARD}ي) {en['dropped_split']} · "
             f"بلا تاريخٍ كافٍ {en['no_hist']} · بلا شاهدٍ ذاتيّ {en['no_cc']} · "
             f"طبقةٌ دقيقةٌ لـ{en['pm_used']} حدثًا (سقف {PM_CAP})")
        if en["match"] < MIN_MATCH:
            _log(f"   🔴 V-L3 — مطابقةُ الشاهد المقطعيّ دون {MIN_MATCH*100:.0f}%")
            guards_ok = False
        if not en["ev"]:
            _log("   🔴 V-L5 — صفرُ حدثٍ مثرًى")
            guards_ok = False
            per_year[y] = set()
            continue
        n_cells = sum(len(enrich(en["ev"], en["cx"], f)) for f in FEATURES)
        z = z_bonf(max(1, n_cells))
        _log(f"   🧮 خلايا {n_cells} · z بونفيروني {z:.3f} (α={ALPHA}/خليّة)")
        passed = set()
        for feat in FEATURES:
            ecx = enrich(en["ev"], en["cx"], feat)
            ecc = enrich(en["ev"], en["cc"], feat)
            if not ecx:
                continue
            line = []
            for lab in sorted(ecx):
                a, b = ecx[lab], ecc.get(lab)
                ok = cell_pass(a, b, z)
                if ok:
                    passed.add(f"{feat}:{lab}")
                rx = "—" if a["ratio"] is None else f"{a['ratio']:.2f}×"
                rc = "—" if not b or b["ratio"] is None else f"{b['ratio']:.2f}×"
                line.append(f"{lab}: {a['pe']:.1f}% (CX {rx} · CC {rc}"
                            f" · n={a['ke']}){' ✅' if ok else ''}")
            _log(f"   {feat:10s} " + " | ".join(line))
        per_year[y] = passed
        _log(f"   ⇒ عابرو `LK1` في {y}: {sorted(passed) or 'لا شيء'}")
        _log("")
    guards = {"pass": guards_ok}
    br, (lbl, why) = read_verdict(per_year, guards)
    common = None
    for y in YEARS:
        common = set(per_year.get(y, set())) if common is None \
            else (common & set(per_year.get(y, set())))
    _log("═══ الحكم ═══")
    _log(f"   العابرُ في كلّ سنة: {sorted(common or []) or 'لا شيء'}")
    _log(f"🏁 الفرعُ {br} — **{lbl}** · {why}")
    if vl4.get("ok") is not None:
        _log(f"🔒 V-L4: {vl4['why']}")
    _log("⚠️ حدودُ الصدق (§⑥): إثراءٌ قبل الحدث لا تنبّؤٌ بالمقدار · ولا حافّةَ "
         "تداولٍ (بلا وقفٍ ولا تكلفة) · والشاهدُ `CX` لا يضبط القطاع.")
    return RC_OK if br in (1, 2) else RC_NOVERDICT


if __name__ == "__main__":
    sys.exit(main())
