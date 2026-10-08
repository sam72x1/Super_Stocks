"""🔬 PHASE 4 — مكتبةُ البحث (قراءةٌ فقط · الإنتاجُ بلا تعديل): أحداثُ اللمسة الأولى/الثانية/إعادة الاختبار/الزناد/الكسر بتعريفات الإنتاج
(`tested_level` · `pivot_cycle_state` · الثوابتُ بالاسم) على شموعٍ < يوم القرار · والأهليّةُ بلا مرساة من حالات المرحلة الثالثة
(اختصارٌ مُتحقَّقٌ منه 1,533/1,533: أهلٌ ⇔ PASS أو الجدارُ الأوّل ANCHOR) · والعيّناتُ المجمَّدة في `PHASE4_PREREG.md §⑦`."""
import csv
import gzip
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P3 = os.path.join(os.path.dirname(HERE), "phase3")
sys.path.insert(0, P3)
import p3lib as L                        # noqa: E402

S = L.S
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)

ANCHORS = ["DKI", "SXTC", "HUBC"]
DISCOVERY = ["AMIX", "BETA", "CANF", "CDIO", "CRE", "DXST", "EHGO", "ELAB", "ELPW", "FRSX", "MNDR", "NUWE", "ONCO", "PIII", "SLXN", "SMX", "SPRC", "TRUG", "UPC", "WORX", "ZCMD", "ZNB"]
VALIDATION = ["BRTX", "CETX", "CIIT", "CUPR", "DCOY", "EDBL", "GCTK", "IPDN", "LIMN", "MSGY", "NRSN", "OMH", "PPBT", "STKH", "SVRE", "YMT"]
POSITIVE_CONTROLS = ["AMIX", "CRE", "GCTK", "PIII", "SPRC", "UPC"]
STATES = ("FOCUS", "WATCH", "READY", "ENTRY")
TOL = 0.015
LOOKBACK = 30
E2_MAX = 30          # اللمسةُ الأولى تخرج من نافذة 30 بعدها
CYCLE_MAX = 60       # PIVOT_CYCLE_WIN


def which_set(sym):
    if sym in ANCHORS:
        return "anchor"
    if sym in DISCOVERY:
        return "discovery"
    if sym in VALIDATION:
        return "validation"
    return "other"


def cfg():
    return dict(tol=float(S.CONFIG["METHOD_HOLD_TOL"]), bounce=float(S.CONFIG["METHOD_BOUNCE_MIN_PCT"]), sweep=float(S.CONFIG["PIVOT_SWEEP_PCT"]),
                hold=int(S.CONFIG["STABILITY_MIN"]), win=int(S.CONFIG["PIVOT_CYCLE_WIN"]), anchor_mode=S.CONFIG.get("ANCHOR_MODE"))


# ---------------------------------------------------------------- Faisal rows (dated · classes · evidence class)
def faisal_timeline():
    rows = [r for r in csv.DictReader(open(os.path.join(P3, "FAISAL_TIMELINE.csv"), encoding="utf-8"))
            if r["IS_FAISAL"] == "1" and r["OBSERVATION_CLASS"] in STATES and len(r["DATE"]) == 10]
    days = {}
    for r in rows:
        days.setdefault(r["TICKER"], set()).add(r["DATE"])
    out = []
    for r in rows:
        et = r["EVIDENCE_TYPE"]
        if r["OBSERVATION_CLASS"] == "ENTRY":
            ev = "ACTION"
        elif et in ("TELEGRAM", "X_POST"):
            ev = "DIRECT_TEXT"
        elif et == "CHART_IMAGE":
            ev = "DIRECT_CHART"
        elif et == "APP_SCREENSHOT":
            ev = "WATCHLIST"
        else:
            ev = "UNKNOWN"
        sess = L.session(r["DATE"])
        out.append(dict(ticker=r["TICKER"], date=r["DATE"], session=sess, date_ambiguous=int(sess != r["DATE"]), state=r["OBSERVATION_CLASS"],
                        evidence_id=r["EVIDENCE_ID"], evidence_class=ev, repeated_attention=int(len(days[r["TICKER"]]) >= 2),
                        set=which_set(r["TICKER"]), has_bars=int(bool(L.load()["daily"].get(r["TICKER"])))))
    return sorted(out, key=lambda r: (r["ticker"], r["session"], r["evidence_id"]))


def first_states(rows):
    """لكلّ رمز: أوّلُ جلسةٍ لكلّ صنف · وأوّلُ حالةٍ قابلةٍ للدفاع (أبكرُ FOCUS/WATCH/READY/ENTRY)."""
    out = {}
    for r in rows:
        d = out.setdefault(r["ticker"], {})
        for k in ("first_state",) + tuple(f"first_{s.lower()}" for s in STATES):
            d.setdefault(k, None)
        if d["first_state"] is None or r["session"] < d["first_state"]:
            d["first_state"] = r["session"]; d["first_state_class"] = r["state"]; d["first_state_evidence"] = r["evidence_class"]; d["first_state_ambiguous"] = r["date_ambiguous"]
        k = f"first_{r['state'].lower()}"
        if d[k] is None or r["session"] < d[k]:
            d[k] = r["session"]
    return out


# ---------------------------------------------------------------- bot eligibility (identity gates without the anchor)
_BS = None


def bot_states():
    global _BS
    if _BS is None:
        _BS = {}
        with gzip.open(os.path.join(P3, "out", "bot_states.csv.gz"), "rt", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                _BS[(r["symbol"], r["date"])] = r
    return _BS


_EXTRA = {}


def gate_row(sym, day):
    """نتيجةُ الإنتاج (CURRENT) عند day: من حالات المرحلة الثالثة أو تشغيلٌ جديد (مخبَّأ في out/extra_states.csv)."""
    r = bot_states().get((sym, day))
    if r:
        return dict(result=r["result"], gate=r["gate"], reason=r["reason"], src="bot_states")
    if (sym, day) in _EXTRA:
        return _EXTRA[(sym, day)]
    df = L.frame(L.bars_before(sym, day))
    res, why, _ = L.run_gates(sym, df)
    row = dict(result=res, gate=(L.reason_gate(why) if res == "REJECT" else ("DEPTH" if res == "TOO_FEW_BARS" else "")), reason=why, src="run")
    _EXTRA[(sym, day)] = row
    return row


def load_extra():
    p = os.path.join(OUT, "extra_states.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            _EXTRA[(r["symbol"], r["date"])] = dict(result=r["result"], gate=r["gate"], reason=r["reason"], src="run")


def save_extra():
    p = os.path.join(OUT, "extra_states.csv")
    rows = [dict(symbol=s, date=d, **v) for (s, d), v in sorted(_EXTRA.items()) if v.get("src") == "run"]
    if rows:
        L.write_csv(p, [{k: r[k] for k in ("symbol", "date", "result", "gate", "reason")} for r in rows])


def eligible(sym, day):
    g = gate_row(sym, day)
    return (g["result"] == "PASS") or (g["gate"] == "ANCHOR"), g


# ---------------------------------------------------------------- events
def level_at(sym, T):
    """E0/E1: المستوى = أدنى Low في آخر 30 شمعةً < T · اللمسةُ الأولى = أوّلُ شمعةٍ بلغته."""
    rows = L.bars_before(sym, T)
    if len(rows) < 3:
        return None
    t = rows[-LOOKBACK:]
    lows = [float(r[3]) for r in t]
    base = min(lows)
    if base <= 0:
        return None
    i = lows.index(base)
    ft = t[i][0]
    hits = [abs(x / base - 1.0) <= TOL for x in lows]
    clusters = sum(1 for k, v in enumerate(hits) if v and not (k and hits[k - 1]))
    return dict(level=round(base, 4), first_touch=ft, sessions_since=L.cal_index(T) - L.cal_index(ft), touches=clusters, asof=rows[-1][0], window_start=t[0][0])


def sym_sessions_after(sym, day, n):
    """تواريخُ شموع الرمز بعد day (حتى n شمعة)؛ يومُ القرار لكلّ شمعةٍ = الجلسةُ التالية لها."""
    rows = L.load()["daily"].get(sym) or []
    return [r[0] for r in rows if r[0] > day][:n]


def e2_scan(sym, level, first_touch):
    """E2 اللمسةُ الثانية الإنتاجيّة: أوّلُ يومِ قرارٍ تُرجع فيه tested_level لمستين فأكثر على المستوى نفسِه · أو سببُ الاستحالة."""
    for d in sym_sessions_after(sym, first_touch, E2_MAX + 1):
        T = L.shift(d, 1)
        df = L.frame(L.bars_before(sym, T))
        lows = df["Low"].tail(LOOKBACK).astype(float)
        if float(lows.min()) < level * (1 - 1e-9) and abs(float(lows.min()) / level - 1) > 1e-6:
            return dict(date=None, decision=T, status="LEVEL_INVALIDATED", at=d)
        r = L._ORIG_TL(df, LOOKBACK, TOL, 2)
        if r and abs(float(r["level"]) - level) <= 1e-4 * max(1.0, level):
            return dict(date=T, decision=T, status="E2", at=d, touches=int(r["touches"]))
        if first_touch not in set(df.index.strftime("%Y-%m-%d").tolist()[-LOOKBACK:]):
            return dict(date=None, decision=T, status="WINDOW_EXPIRED", at=d)
    return dict(date=None, decision=None, status="WINDOW_EXPIRED", at=None)


def cycle_scan(sym, level, first_touch):
    """E3/E4/E5 بدالّة الإنتاج pivot_cycle_state على نافذتها 60: إعادةُ الاختبار (hold/sweep) · الزناد (استعادةٌ بعد سحب أو ثبات 3) · الكسر."""
    out = dict(e3=None, e3_branch=None, e3_decision=None, e3_bottom=None, e4=None, e4_branch=None, e5=None, e5_kind=None, level_mismatch=0, sweep_low=None, sweep_pct=None)
    c = cfg()
    swept_seen = False
    for k, d in enumerate(sym_sessions_after(sym, first_touch, CYCLE_MAX + 1)):
        T = L.shift(d, 1)
        rows = L.bars_before(sym, T)
        low = float(rows[-1][3]); close = float(rows[-1][4])
        if low < level * (1 - c["sweep"] / 100.0):
            out["e5"] = T; out["e5_kind"] = "BROKEN_BELOW_SWEEP_MAX"; return out
        pc = S.pivot_cycle_state(L.frame(rows))
        if not pc:
            continue
        same = abs(float(pc["bottom"]) - level) <= 1e-4 * max(1.0, level)
        if pc["stage"] >= 3 and out["e3"] is None:
            # PHASE4_PREREG §③-E3: إن اختلف قاعُ pivot_cycle_state (نافذته 60) عن المستوى (نافذة 30) يُؤخذ E3 على قاعه ويُوسَم LEVEL_MISMATCH
            out["e3"] = T; out["e3_branch"] = pc["branch"]; out["e3_decision"] = T; out["e3_bottom"] = float(pc["bottom"]); out["level_mismatch"] = int(not same)
            out["sweep_low"] = pc.get("retest_low"); out["sweep_pct"] = pc.get("sweep_pct")
        if out["e3"] is not None and pc["branch"] == "sweep":
            swept_seen = True
        if out["e3"] is not None and out["e4"] is None:
            ref = out["e3_bottom"] if out["e3_bottom"] else level     # الاستعادةُ فوق القاع الذي اختُبر (قاعُ pivot عند الاختلاف)
            if swept_seen and close > ref:
                out["e4"] = T; out["e4_branch"] = "sweep_reclaim"
            elif pc["stage"] == 4:
                out["e4"] = T; out["e4_branch"] = "stability"
        if out["e4"] is not None:
            return out
        if k >= CYCLE_MAX:
            break
    if out["e3"] is None:
        out["e5"] = L.shift(first_touch, CYCLE_MAX); out["e5_kind"] = "NO_RETEST_IN_60"
    return out


def lookahead_check(sym, T):
    """الشموعُ المستعملة < T (تحقّقٌ آليّ)."""
    rows = L.bars_before(sym, T)
    return (rows[-1][0] < T) if rows else True


def wilson(k, n, z=1.96):
    if n <= 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (round(c - h, 3), round(c + h, 3))


def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return dict(n=0, median=None, q1=None, q3=None, min=None, max=None)
    import statistics
    n = len(xs)
    def pct(p):
        i = (n - 1) * p
        lo, hi = int(i), min(int(i) + 1, n - 1)
        return round(xs[lo] + (xs[hi] - xs[lo]) * (i - lo), 1)
    return dict(n=n, median=statistics.median(xs), q1=pct(0.25), q3=pct(0.75), min=xs[0], max=xs[-1])
