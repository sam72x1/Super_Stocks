# -*- coding: utf-8 -*-
"""🎯🪜 `T-TGTLADDER` «سلّمُ الأهداف» — العقد `T_TGTLADDER_prereg.md` (مدموجٌ قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا يغيّر الكرت.
الأوضاع: `--mode check` (بلا شبكة) · `posts` (① المطابقة لأرقام فيصل) · `prep` · `shard` (SHARD · NSHARDS) · `assemble` (②)
— وكلُّها تخرج 9 إن تغيّرت بصمةُ العقد.
"""
import argparse
import bisect
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_TGTLADDER_prereg.md")
CONTRACT_SHA = "1e3bcb6a3baa7f57ddf53a4595d0cbbf320de0de6212e195036f4a337dbe7ec0"
CONTRACT_RC = 9
OUT = os.path.join(HERE, "out")
SEED = 20261110
BOOT_B = 2000
WIN = 20                      # نافذةُ التعبئة · ونافذةُ الحمل · ونافذةُ بلوغ الهدف (جلسات)
TOL = 0.01                    # ① ضمن 1% (نصُّ المالك)
SHIFT = 1.05                  # ① ضابطُ المصادفة
LADDER_K = 6                  # «حتى 6» (نصُّ المالك)
GAP_PCT = 3.0                 # `MIN_TARGET_GAP_PCT` بالاسم (يُقرأ وقتَ النداء)
H4_DAYS = 60                  # تقويميّ قبل D (نافذةُ `fetch_4h` في الإنتاج)
FLOOR_POSTS = 30
FLOOR_TRADES = 30
H4_COVER = 0.80
PERIOD = ("2023-01-03", "2025-12-31")
BARS_TO = "2026-03-31"        # §③ الصفقةُ حتى D+39 لإدخالات ديسمبر 2025 (والقرارُ بشموعٍ قبل D وحدَها)
YEARS = ("2023", "2024", "2025")
LEVELS_TSV = os.path.join(ROOT, "faisal_levels_table.tsv")
# منشوراتُ 11-07 (‏`fm_forensics/app_compare/FAISAL_POSTS_20261107.md` · المقاومات ‏+ الأهداف ‏+ القمّة) — THH من لقطة المالك وحدَها
POSTS_1107 = {
    "THH": [1.490, 1.653, 1.820, 1.920, 2.106, 2.297, 2.571],
    "BRTX": [1.673, 1.911, 2.183, 2.427, 2.914, 3.234, 3.581, 4.209],
    "EHGO": [1.763, 1.863, 1.993, 2.228, 2.517, 2.752, 3.00],
    "NEXR": [2.364, 2.863, 3.373, 3.917, 4.764, 5.098, 5.750, 6.80],
}
POSTS_1107_DATE = "2026-11-07"


def log(*a):
    print(*a, flush=True)


def _sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None


def contract_ok(path=CONTRACT, sha=None):
    return _sha(path) == (sha or CONTRACT_SHA)


def _rb():
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "rebuild"))
    sys.path.insert(0, ROOT)
    import rebuild as RB
    return RB


# ── دوالُّ نقيّة ─────────────────────────────────────────────────────────────────────────────────
def ladder6(daily_res, h4_res, price, gap_pct=GAP_PCT, k=LADDER_K, t1=None):
    """§① LADDER6: اتّحادُ المقاومات فوق السعر مرتّبةً صعودًا · يُدمج ما يقع ضمن `gap_pct` من السابق (يبقى الأدنى) · أوّلُ k ·
    وإن خلت ⟵ [t1] (أو []) — يُرجع (القائمة، خلت؟)."""
    try:
        px = float(price)
    except (TypeError, ValueError):
        return ([round(float(t1), 4)] if t1 else []), True
    lv = sorted({round(float(x), 4) for x in list(daily_res or []) + list(h4_res or [])
                 if x is not None and float(x) > px})
    out = []
    for x in lv:
        if out and x <= out[-1] * (1.0 + gap_pct / 100.0):
            continue
        out.append(x)
        if len(out) >= k:
            break
    if not out:
        return ([round(float(t1), 4)] if t1 else []), True
    return out, False


def match_counts(faisal, bot, tol=TOL):
    """§② (استرجاعٌ، عددُ فيصل، دقّةٌ، عددُ البوت): رقمٌ لفيصل «مُسترجَع» إن كان في البوت رقمٌ ضمن tol نسبيًّا منه · والعكسُ للدقّة."""
    f = [float(x) for x in faisal if x]
    b = [float(x) for x in bot if x]
    near = lambda v, pool: any(abs(p / v - 1.0) <= tol for p in pool)
    return sum(1 for v in f if near(v, b)), len(f), sum(1 for v in b if near(v, f)), len(b)


def scale_rows(rows, f):
    """§③ المقياسُ الواحد: صفوف (يوم، o، h، l، c، v) × asof_factor(D) — نفسُ ضرب تاريخ القرار."""
    if f == 1.0:
        return [tuple(r[:6]) for r in rows]
    return [(r[0], r[1] * f, r[2] * f, r[3] * f, r[4] * f, (r[5] / f if f else r[5])) for r in rows]


def hit_flags(rows, i, targets, win=WIN):
    """§③ بلوغُ كلّ هدف: أعلى High في الجلسات [D، D+win−1] ≥ الهدف (بصرف النظر عن التعبئة) · None إن نقصت الجلسات."""
    fut = rows[i: i + win]
    if len(fut) < win:
        return None
    hi = max(float(r[2]) for r in fut)
    return [bool(hi >= float(t)) for t in targets]


def trade_r(rows, i, entry, stop, targets, win=WIN):
    """§③ الصفقة: أمرُ شراءٍ عند `entry` في [D، D+win−1] (Low ≤ entry ⟵ min(open، entry)) · الوقفُ حين Low < stop (يُنفَّذ
    بـmin(open، stop)) · أوامرُ بيعٍ مقسّمةٌ بالتساوي على الأهداف · يومُ التعبئة يُفحص فيه الوقفُ وحدَه · وبعده الوقفُ أوّلًا ثمّ
    الأهدافُ صعودًا (بـmax(open، الهدف)) · وما بقي بإغلاق الجلسة win من التعبئة.
    يُرجع (R، عُبّئت؟، R بالأجزاء صعودًا) · و(None، False، None) إن تعذّر (الدخولُ لا يعلو الوقف · أهدافٌ فارغة · جلساتٌ ناقصة)."""
    try:
        E, st = float(entry), float(stop)
        tg = sorted(float(t) for t in targets if t is not None and float(t) > 0)
    except (TypeError, ValueError):
        return None, False, None
    if not (E > st > 0) or not tg or i < 1 or i + 2 * win - 1 > len(rows):
        return None, False, None
    k0 = None
    fill = None
    for k in range(i, i + win):
        if float(rows[k][3]) <= E:
            k0, fill = k, min(float(rows[k][1]), E)
            break
    if k0 is None:
        return None, False, None
    risk = fill - st
    if risk <= 0:
        return None, False, None
    w = 1.0 / len(tg)
    left = list(tg)
    leg = {t: None for t in tg}

    def _out():
        return round(sum(leg.values()) / risk, 6), True, [round(leg[t] / risk, 6) for t in tg]
    for k in range(k0, k0 + win):
        o, h, lo = float(rows[k][1]), float(rows[k][2]), float(rows[k][3])
        if lo < st:
            px = min(o, st) if k > k0 else st
            for t in left:
                leg[t] = w * (px - fill)
            return _out()
        if k == k0:
            continue
        for t in list(left):
            if h >= t:
                leg[t] = w * (max(o, t) - fill)
                left.remove(t)
        if not left:
            return _out()
    c_end = float(rows[k0 + win - 1][4])
    for t in left:
        leg[t] = w * (c_end - fill)
    return _out()


def boot_mean(vals_by_sym, seed=SEED, b=BOOT_B):
    """متوسّطٌ وفاصلُ 95% ببوتستراب عنقوديّ بالرمز."""
    syms = sorted(vals_by_sym)
    allv = [v for s in syms for v in vals_by_sym[s]]
    if not allv:
        return None, (None, None)
    rng = random.Random(seed)
    ms = []
    for _ in range(b):
        pick = [syms[rng.randrange(len(syms))] for _ in syms]
        v = [x for s in pick for x in vals_by_sym[s]]
        if v:
            ms.append(sum(v) / len(v))
    ms.sort()
    return sum(allv) / len(allv), (ms[int(0.025 * len(ms))], ms[int(0.975 * len(ms)) - 1])


def verdict2(pooled, per_year, n_year, floor=FLOOR_TRADES, cover=1.0):
    """§③ بالأضعف: «لا قياس» دون الأرضيّة أو التغطية · «السلّمُ أربح/أخسر» بفاصلٍ يجتنب الصفر وإشارةِ كلّ سنة · وإلّا «لا فرق قابل للكشف»."""
    if cover < H4_COVER or any(n_year.get(y, 0) < floor for y in YEARS):
        return "لا قياس"
    m, (lo, hi) = pooled
    if lo is not None and lo > 0 and all((per_year.get(y) or 0) > 0 for y in YEARS):
        return "السلّمُ أربح"
    if hi is not None and hi < 0 and all((per_year.get(y) or 0) < 0 for y in YEARS):
        return "السلّمُ أخسر"
    return "لا فرق قابل للكشف"


def verdict1(rec_lad, rec_cur, rec_null, prec_lad, prec_cur, n_f):
    """§② الحكمُ الوصفيّ بقاعدته (نقاطٌ مئويّة)."""
    if n_f < FLOOR_POSTS:
        return "لا قياس"
    if rec_lad - rec_cur >= 10 and rec_lad - rec_null >= 10 and prec_lad >= prec_cur - 10:
        return "السلّمُ أقربُ لفيصل"
    if rec_lad < rec_cur:
        return "أبعد"
    return "لا فرق قابل للكشف"


# ── ① منشوراتُ فيصل ───────────────────────────────────────────────────────────────────────────────
def table_units(path=LEVELS_TSV):
    """§② الوحداتُ المؤرَّخة: (الرمز، التاريخ) ⟵ أرقامُ `target_clean`/`resistance` · ومصدرُ التاريخ."""
    out = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            if not r.get("date") or r.get("role") not in ("target_clean", "resistance"):
                continue
            try:
                v = float(r["level"])
            except (TypeError, ValueError):
                continue
            u = out.setdefault((r["symbol"].upper(), r["date"]), {"nums": [], "src": r.get("date_source")})
            u["nums"].append(v)
    return out


def units_all():
    u = {(s, POSTS_1107_DATE): {"nums": list(v), "src": "post_1107"} for s, v in POSTS_1107.items()}
    for k, v in table_units().items():
        u.setdefault(k, v)
    return u


def unit_factor(S, splits, day):
    """🔧 (2026-11-10 · عطلٌ مُثبَت في أوّل تشغيلة `42923696006`: شموعُ الإنتاج مسوّاةٌ بكلّ تقسيمٍ حتى اليوم ⟵ NEXR يومَ 04-01 بسعر 199.76
    وأرقامُ فيصل 1.71-3.26) — عاملُ مقياس يوم الوحدة: حاصلُ نسب التقسيمات المنفّذة في D أو بعده (اصطلاحُ `asof_factor`) بـ`_split_scale_factor`
    بالاسم (بعد D−1 حصريًا) · والسعرُ × العامل يُعيد مقياسَ D−1 · وتعذّرُ التقسيمات ⟵ 1.0 (يُطبَع)."""
    prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    try:
        return float(S._split_scale_factor(splits, prev))
    except Exception:                                            # noqa: BLE001
        return 1.0


def posts_unit(S, AO, sym, day, nums, daily_full, h1_full, splits=None):
    """وحدةٌ واحدة: الشموعُ قبل `day` بمقياس يومها (`unit_factor`) · 4س بالإصلاح على اليوميّ المقيس · CUR3 بالفحص اليدويّ · وLADDER6."""
    import pandas as pd
    out = {"symbol": sym, "date": day}
    if daily_full is None or not len(daily_full):
        out["error"] = "بلا شموع يوميّة"
        return out
    cut = daily_full[daily_full.index < pd.Timestamp(day)]          # §② سعرُ D−1 (لا نظرَ للأمام)
    if len(cut) < 60:
        out["error"] = f"شموعٌ قليلة ({len(cut)})"
        return out
    f = unit_factor(S, splits, day)
    out["factor"] = round(f, 6)
    if f != 1.0:
        cut = cut.copy()
        cut[["Open", "High", "Low", "Close"]] *= f
        cut["Volume"] /= f
    price = float(cut["Close"].iloc[-1])
    h1 = None
    if h1_full is not None and len(h1_full):
        idx = h1_full.index if getattr(h1_full.index, "tz", None) is not None else h1_full.index.tz_localize("UTC")
        end = pd.Timestamp(day).tz_localize("America/New_York")      # نهايةُ D−1
        h1 = h1_full[(idx < end) & (idx >= end - pd.Timedelta(days=H4_DAYS + 1))]
        h1, _rs = S.h1_daily_rescale(h1, cut)
    h4 = S.resample_ohlc(h1, "4h") if h1 is not None and len(h1) else None
    h4 = h4 if h4 is not None and len(h4) >= 20 else None
    keep_dh, keep_f4 = S.download_history, S.fetch_4h
    try:
        S.download_history = lambda syms, *a, **k: {sym: cut}
        S.fetch_4h = lambda s, with_h1=False, daily=None: ((h4, h1) if with_h1 else h4)
        r = (list(AO.analyze_on_demand(sym)) + [None])[0]
    finally:
        S.download_history, S.fetch_4h = keep_dh, keep_f4
    if not r:
        out["error"] = "تعذّر الفحصُ اليدويّ"
        return out
    cur3 = [r.get("t1"), r.get("t2"), r.get("t3")]
    dres = list(S.resistance_levels(cut, price))
    h4l = S.four_hour_levels(h4, price) if h4 is not None else None
    lad, empty = ladder6(dres, (h4l or {}).get("resistances") or [], price, t1=r.get("t1"))
    fnum = [x for x in nums if x > price]
    out.update({"price": round(price, 4), "faisal": fnum, "cur3": cur3, "ladder": lad, "ladder_empty": empty,
                "h4": h4 is not None, "src": None})
    out["m_cur"] = match_counts(fnum, cur3)
    out["m_lad"] = match_counts(fnum, lad)
    out["m_null"] = match_counts(fnum, [x * SHIFT for x in lad])
    return out


def mode_posts():
    os.environ.setdefault("FAISAL_ONLY", "1")
    sys.path.insert(0, ROOT)
    import Super_stock as S
    import analyze_one as AO
    import yfinance as yf
    units = units_all()
    syms = sorted({s for s, _d in units})
    hist = S.download_history(syms) or {}
    rows = []
    for (sym, day), u in sorted(units.items()):
        try:
            h1 = yf.download(sym, start=(dt.date.fromisoformat(day) - dt.timedelta(days=H4_DAYS + 2)).isoformat(),
                             end=(dt.date.fromisoformat(day) + dt.timedelta(days=2)).isoformat(),
                             interval="1h", auto_adjust=True, prepost=True, progress=False)
            if h1 is not None and len(h1) and hasattr(h1.columns, "levels"):
                h1.columns = h1.columns.get_level_values(0)
        except Exception:                                        # noqa: BLE001
            h1 = None
        try:
            sp = S._fetch_splits_dq(sym)
        except Exception:                                        # noqa: BLE001
            sp = None
        r = posts_unit(S, AO, sym, day, u["nums"], hist.get(sym), h1, splits=sp)
        r["date_src"] = u["src"]
        rows.append(r)
        log(f"🎯 {sym} {day}: {json.dumps({k: r.get(k) for k in ('factor', 'price', 'faisal', 'cur3', 'ladder', 'm_cur', 'm_lad', 'm_null', 'error')}, ensure_ascii=False)}")
    ok = [r for r in rows if "m_lad" in r]
    tot = lambda key, j: sum(r[key][j] for r in ok)
    nf = tot("m_lad", 1)
    pct = lambda a, b: (100.0 * a / b) if b else 0.0
    rec = {k: pct(tot(k, 0), nf) for k in ("m_cur", "m_lad", "m_null")}
    prec = {k: pct(tot(k, 2), tot(k, 3)) for k in ("m_cur", "m_lad")}
    ver = verdict1(rec["m_lad"], rec["m_cur"], rec["m_null"], prec["m_lad"], prec["m_cur"], nf)
    res = {"units": len(rows), "measured": len(ok), "n_faisal": nf, "recall": rec, "precision": prec, "verdict": ver,
           "preds": {"TL1": rec["m_lad"] - rec["m_cur"] >= 10, "TL2": prec["m_lad"] < prec["m_cur"],
                     "TL3": rec["m_null"] >= 0.5 * rec["m_lad"], "TL4": ver == "لا فرق قابل للكشف"}}
    log(f"① الوحدات {len(rows)} (مقيسة {len(ok)}) · أرقامُ فيصل {nf} · الاسترجاع CUR3 {rec['m_cur']:.1f}% · LADDER6 {rec['m_lad']:.1f}% · "
        f"المصادفة {rec['m_null']:.1f}% · الدقّة CUR3 {prec['m_cur']:.1f}% · LADDER6 {prec['m_lad']:.1f}% ⟵ **{ver}**")
    print("TGL_POSTS_JSON " + json.dumps({"res": res, "rows": rows}, ensure_ascii=False, default=str))
    return 0


# ── ② ثلاثُ سنوات PIT ────────────────────────────────────────────────────────────────────────────
def polygon_hourly(sym, d, key, fetch=None):
    """شموعُ Polygon الساعيّة المسوّاة لـH4_DAYS يومًا تقويميًّا حتى نهاية D−1 (UTC) ⟵ إطارٌ أو None."""
    import pandas as pd
    sys.path.insert(0, ROOT)
    import pit_history as PH
    fetch = fetch or PH._fetch
    d0 = (dt.date.fromisoformat(d) - dt.timedelta(days=H4_DAYS)).isoformat()
    d1 = (dt.date.fromisoformat(d) - dt.timedelta(days=1)).isoformat()
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/hour/{d0}/{d1}?adjusted=true&sort=asc&limit=50000")
    try:
        blob = fetch(url, key)
    except Exception:                                            # noqa: BLE001
        return None
    rs = []
    for r in (blob or {}).get("results") or []:
        try:
            rs.append({"t": pd.to_datetime(int(r["t"]), unit="ms", utc=True), "Open": float(r["o"]), "High": float(r["h"]),
                       "Low": float(r["l"]), "Close": float(r["c"]), "Volume": float(r.get("v") or 0.0)})
        except (KeyError, TypeError, ValueError):
            continue
    if not rs:
        return None
    return pd.DataFrame(rs).set_index("t").sort_index()


def entry_row(S, RB, sym, rows, i, sub, f, r0, hourly, d=None):
    """صفُّ إدخالٍ واحد: CUR3 (بتنقيح 4س) · LADDER6 · بلوغُ الأهداف · وR الذراعين على المقياس الواحد.
    🔧 (2026-11-10 · عطلٌ مُثبَت: الشريحة 5 في `42923696006` سقطت بـIndexError) — يومُ D يُمرَّر ولا يُقرأ من `rows[i]`: رمزٌ آخرُ شموعه قبل D
    (`bisect` يُرجع طولَ القائمة) يبقى إدخالًا بلا جلساتٍ لاحقة ⟵ بلوغٌ None وصفقةٌ لا تُعبَّأ (تُعَدّ) كما يقول العقد."""
    price = float(sub["Close"].iloc[-1])
    h4 = None
    if hourly is not None and len(hourly):
        h = hourly.copy()
        if f != 1.0:
            h[["Open", "High", "Low", "Close"]] *= f
            h["Volume"] /= f
        h4 = S.resample_ohlc(h, "4h")
        h4 = h4 if len(h4) >= 20 else None
    h4l = S.four_hour_levels(h4, price) if h4 is not None else None
    t1, t2, t3 = r0.get("t1"), r0.get("t2"), r0.get("t3")
    if h4l:
        t2, t3 = S.refine_targets_4h(t1, t2, t3, price, h4l)
    cur3 = [x for x in (t1, t2, t3) if x]
    lad, empty = ladder6(S.resistance_levels(sub, price), (h4l or {}).get("resistances") or [], price, t1=t1)
    rs = scale_rows(rows, f)
    tr = r0.get("tranches") or []
    entry = sum(tr) / len(tr) if tr else None
    stop = (r0.get("stop") or (None,))[0]
    rc, fc, _lc = trade_r(rs, i, entry, stop, cur3)
    rl, fl, ll = trade_r(rs, i, entry, stop, lad)
    return {"d": d or rows[i][0], "h4": h4 is not None, "cur3": cur3, "lad": lad, "lad_empty": empty,
            "hit_cur": hit_flags(rs, i, cur3), "hit_lad": hit_flags(rs, i, lad),
            "r_cur": rc, "r_lad": rl, "legs_lad": ll, "filled": bool(fc and fl)}


def shard_symbol(sym, rows, splits_sym, member_days, sessions_ix, prev_of, finra, proxy_fn, S, cfg_cur, G5, RB, key,
                 hourly_fn=None):
    """إدخالاتُ CURRENT الجديدة لرمز (حرّاسُ `appdiff_symbol` بالاسم) ⟵ صفوفُ `entry_row`."""
    import pandas as pd
    cnt = {"rows": 0, "fire_cur": 0, "entries": 0, "h4": 0, "entry_err": 0}
    out = []
    if not rows:
        return out, cnt
    dates = [x[0] for x in rows]
    full = pd.DataFrame({"Open": [x[1] for x in rows], "High": [x[2] for x in rows], "Low": [x[3] for x in rows],
                         "Close": [x[4] for x in rows], "Volume": [x[5] for x in rows]}, index=pd.to_datetime(dates))
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = RB.gaps(rows)
    last = None
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 1 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > RB.STALE_DAYS:
            continue
        sp, gq = RB.row_guards(dates, i, d, unadj, gp)
        if sp or gq:
            continue
        cnt["rows"] += 1
        lo = bisect.bisect_left(dates, (dt.date.fromisoformat(d) - dt.timedelta(RB.HISTORY_DAYS)).isoformat())
        sub = full.iloc[lo:i]
        f = RB.asof_factor(splits_sym, d)
        if f != 1.0:
            sub = sub.copy()
            sub[["Open", "High", "Low", "Close"]] *= f
            sub["Volume"] /= f
        RB.with_config(S, cfg_cur)
        try:
            r0 = S.analyze_ticker(sym, sub)
        except Exception:                                       # noqa: BLE001
            r0 = None
        if not r0:
            continue
        prev = prev_of[d]
        if not RB.post_scan(S, r0, (finra.get(prev) or {}).get(sym), proxy_fn(sym, prev)):
            continue
        cnt["fire_cur"] += 1
        ix = sessions_ix.get(d)
        new = ix is not None and (last is None or ix - last > WIN)
        if ix is not None:
            last = ix
        if not new or not (PERIOD[0] <= d <= PERIOD[1]):
            continue
        cnt["entries"] += 1
        hourly = (hourly_fn or (lambda s, dd: polygon_hourly(s, dd, key)))(sym, d)
        try:
            er = entry_row(S, RB, sym, rows, i, sub, f, r0, hourly, d=d)
        except Exception as e:                                   # noqa: BLE001 — يُعَدّ ويُسمّى ولا يُسقط الشريحة
            cnt["entry_err"] += 1
            log(f"⚠️ {sym} {d}: تعذّر صفُّ الإدخال ({type(e).__name__}: {e}) — يُعَدّ")
            continue
        cnt["h4"] += er["h4"]
        out.append(er)
    RB.with_config(S, cfg_cur)
    return out, cnt


def mode_prep(key):
    RB = _rb()
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "appdiff"))
    import appdiff as AD
    res = RB.mode_bases_prep(key, months=AD.MONTHS, sess_from=AD.SESS_FROM, sess_to=AD.SESS_TO, all_from=AD.ALL_FROM,
                             out=os.path.join(OUT, "prep.json.gz"), tag="tgtladder_prep",
                             splits_range=(RB.BARS_FROM, dt.date.today().isoformat()))
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    late = sorted(s for s, sp in (prep.get("splits") or {}).items() if any(d > RB.BARS_TO for d, _r in sp))
    log(f"✂️ رموزُ الاتّحاد بتقسيمٍ بعد {RB.BARS_TO} (خارج تقسيمات T-REBUILD/T-APPDIFF · والشموعُ المسوّاة تشملها): {len(late)} من {len(prep.get('union') or [])}")
    print("TGL_LATE_SPLITS " + json.dumps(late))
    return res


def mode_shard(key, shard, nshards):
    RB = _rb()
    os.environ["FAISAL_ONLY"] = "0"
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "appdiff"))
    import appdiff as AD
    import Super_stock as S
    import pit_history as PH
    prep = RB._jload(os.path.join(OUT, "prep.json.gz"))
    cur, _piv = AD.cfgs_of(S, RB)
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    six = {d: n for n, d in enumerate(prep["sessions"])}
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                cache[(sym, day)] = None
        return cache[(sym, day)]
    syms = prep["union"][shard::nshards]
    rows_by, tot, diag = {}, {}, {}
    for n, sym in enumerate(syms):
        df, why = PH.polygon_daily(sym, RB.BARS_FROM, BARS_TO, key)
        rows = RB._rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out, cnt = shard_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), six, prep["prev_of"], prep["finra"],
                                _proxy, S, cur, G5, RB, key)
        if out:
            rows_by[sym] = out
        for k, v in cnt.items():
            tot[k] = tot.get(k, 0) + v
        if n % 25 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {tot}")
    RB._jdump({"shard": shard, "nshards": nshards, "counts": tot, "bars_diag": diag, "rows": rows_by},
              os.path.join(OUT, f"shard_{shard:02d}.json.gz"))
    log(f"shard {shard}: انتهت · {tot} · الشموع {diag}")
    return 0


def analyse(rows_by, seed=SEED, b=BOOT_B):
    ents = [(s, e) for s, es in rows_by.items() for e in es]
    n = len(ents)
    cover = (sum(1 for _s, e in ents if e["h4"]) / n) if n else 0.0
    share = {}
    for arm, key, kmax in (("CUR3", "hit_cur", 3), ("LADDER6", "hit_lad", LADDER_K)):
        sh = []
        for j in range(kmax):
            v = [e[key][j] for _s, e in ents if e[key] is not None and len(e[key]) > j]
            sh.append((round(100.0 * sum(v) / len(v), 1) if v else None, len(v)))
        share[arm] = sh
    tr = [(s, e) for s, e in ents if e["filled"] and e["r_cur"] is not None and e["r_lad"] is not None]
    by_sym, by_year, n_year = {}, {}, {}
    for s, e in tr:
        dlt = e["r_lad"] - e["r_cur"]
        by_sym.setdefault(s, []).append(dlt)
        y = e["d"][:4]
        by_year.setdefault(y, []).append(dlt)
        n_year[y] = n_year.get(y, 0) + 1
    pooled = boot_mean(by_sym, seed, b)
    per_year = {y: (sum(v) / len(v) if v else None) for y, v in by_year.items()}
    mean = lambda xs: (sum(xs) / len(xs)) if xs else None
    med = lambda xs: (sorted(xs)[len(xs) // 2]) if xs else None
    desc = {"n_entries": n, "n_trades": len(tr), "lad_mean_k": mean([len(e["lad"]) for _s, e in ents]),
            "lad_lt3": (sum(1 for _s, e in ents if len(e["lad"]) < 3) / n) if n else None,
            "lad_empty": sum(1 for _s, e in ents if e["lad_empty"]),
            "r_cur_mean": mean([e["r_cur"] for _s, e in tr]), "r_cur_med": med([e["r_cur"] for _s, e in tr]),
            "r_lad_mean": mean([e["r_lad"] for _s, e in tr]), "r_lad_med": med([e["r_lad"] for _s, e in tr]),
            "win_cur": mean([1.0 if e["r_cur"] > 0 else 0.0 for _s, e in tr]),
            "win_lad": mean([1.0 if e["r_lad"] > 0 else 0.0 for _s, e in tr]),
            "legs_lad": [(round(mean(v), 4) if v else None, len(v)) for v in
                         ([e["legs_lad"][j] for _s, e in tr if e.get("legs_lad") and len(e["legs_lad"]) > j] for j in range(LADDER_K))],
            "excluded_no_trade": sum(1 for _s, e in ents if not e["filled"])}
    ver = verdict2(pooled, per_year, n_year, cover=cover)
    return {"cover": cover, "share": share, "pooled": pooled, "per_year": per_year, "n_year": n_year, "desc": desc,
            "verdict": ver,
            "preds": {"TL5": (share["LADDER6"][0][0] or 0) > (share["CUR3"][0][0] or 0),
                      "TL6": (desc["lad_mean_k"] or 0) >= 4, "TL7": ver == "لا فرق قابل للكشف", "TL8": cover >= H4_COVER}}


def mode_assemble(nshards):
    RB = _rb()
    paths = sorted(glob.glob(os.path.join(OUT, "**", "shard_*.json.gz"), recursive=True))
    shards = [RB._jload(p) for p in paths]
    got = sorted({s["shard"] for s in shards})
    if got != list(range(nshards)):
        log(f"⛔ شرائحُ ناقصة: {sorted(set(range(nshards)) - set(got))} — «لا قياس»")
        return 7
    rows_by, tot = {}, {}
    for sh in shards:
        rows_by.update(sh["rows"])
        for k, v in sh["counts"].items():
            tot[k] = tot.get(k, 0) + v
    res = analyse(rows_by)
    m, (lo, hi) = res["pooled"]
    log(f"② عدّاداتُ الشرائح {tot} — وتعذّرُ صفِّ الإدخال (entry_err) يُطبع هنا ولا يُخفى")
    log(f"② الإدخالات {res['desc']['n_entries']} · الصفقاتُ المعبَّأة {res['desc']['n_trades']} · تغطيةُ 4س {res['cover']:.3f}")
    log(f"   حصّةُ البلوغ CUR3 {res['share']['CUR3']} · LADDER6 {res['share']['LADDER6']}")
    _yr = ", ".join(f"{y}: {round(v, 3)} (n={res['n_year'].get(y)})" for y, v in sorted(res["per_year"].items()) if v is not None)
    _f = lambda x: None if x is None else round(x, 3)
    log(f"   ΔR (LADDER6 − CUR3) {_f(m)} [{_f(lo)}، {_f(hi)}] · لكلّ سنة {{{_yr}}} ⟵ **{res['verdict']}**")
    print("TGL_PIT_JSON " + json.dumps({"res": res, "counts": tot, "run": os.environ.get("GITHUB_RUN_ID")}, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="check", choices=("check", "posts", "prep", "shard", "assemble"))
    a = ap.parse_args(argv)
    if not contract_ok():
        log("⛔ بصمةُ العقد تغيّرت — لا تشغيل")
        return CONTRACT_RC
    if a.mode == "check":
        log("✅ العقدُ مطابق")
        return 0
    if a.mode == "posts":
        return mode_posts()
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key and a.mode in ("prep", "shard"):
        log("⛔ بلا مفتاح Polygon — لا قياس")
        return 3
    if a.mode == "prep":
        log(json.dumps(mode_prep(key), ensure_ascii=False, default=str)[:2000])
        return 0
    if a.mode == "shard":
        return mode_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", "20")))
    return mode_assemble(int(os.environ.get("NSHARDS", "20")))


if __name__ == "__main__":
    sys.exit(main())
