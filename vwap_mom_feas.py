"""📈🔎 جدوى `T-VWAP-MOM` — «زخم الفيواب» (العقد `vwap_mom_prereg.md` §⑧ ‏+ الملحق 1 ‏+ **الملحق 2** `vwap_mom_prereg_addendum_2.md` · كلُّها قبل أيّ عائد).

**عدٌّ لا عائد:** لا يحسب هذا الملفُّ R ولا عائدًا ولا قمّةً لاحقة — مقفولٌ في السويّة (`VWM2`).
**v2 (الملحق 1):** H = **كسرٌ صاعدٌ للفيواب** (إغلاقُ 5 دقائق تحته ثمّ أوّلُ إغلاقٍ فوقه ثمّ 3 إغلاقاتٍ متتالية فوقه أو شمعة 15 دقيقة) ·
والمجتمع = **أحداثُ الكسر على الكون كلّه** بسعرٍ ≥ `PX_MIN` وحجمٍ دولاريٍّ تراكميّ حتى لحظة الحدث ≥ درجةِ `D_MIN` · والذراع E محذوفةٌ بأمر المالك.
**v3 (الملحق 2):** المحفّز C **شرطٌ للمجتمع** — خبرٌ خاصٌّ بالشركة في Polygon news (‏3 رموزٍ أو أقلّ) **أو** إيداعُ `8-K`/`6-K` مقبولٌ في النافذة
(من 16:00 للجلسة السابقة حتى نهاية الحدث) · والحدثُ بلا محفّزٍ لا يُعَدّ · والمجهولُ يُعَدّ مستقلًّا وله حارس · والذراع D (إعادةُ اختبار الفيواب) تُعَدّ وصفًا ·
وقاعدةُ `D_MIN` على وسيط A ∧ C · ولا درجةَ في 10-40 للمرّة الثالثة ⟵ يتوقّف المحور (الملحق 2 §④).
بلا تلغرام · بلا حالة · بلا كتابةٍ في المستودع. والمُخرَجُ سطرُ `VWMFEAS_JSON`. ونتيجتا v1 وv2 منشورتان ودوالُّهما باقيةٌ للإعادة.
"""
import csv
import datetime as dt
import gzip
import bisect
import heapq
import json
import os
import statistics as st
import sys
import tempfile
import time
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
MIN_PREFIX = "us_stocks_sip/minute_aggs_v1"
TOP_N = 20                                         # «Polygon snapshot gainers» — أعلى 20 (العقد §③)
D_LADDER = (250_000, 500_000, 1_000_000, 2_000_000, 5_000_000)   # §③ — مكتوبٌ قبل الرقم
D_RULE = (10, 40)                                  # وسيطُ المرشّحين الجدد/يوم بينهما
EXT_START = 4 * 60                                 # 04:00 نيويورك
EXT_END = 20 * 60                                  # 20:00 نيويورك
C_SAMPLE = 60
# ── الملحق 2 (مكتوبٌ قبل أرقام v3) ──
NEWS_MAX_TICKERS = 3                               # §② خبرٌ خاصٌّ بالشركة: `tickers` فيه 3 رموزٍ أو أقلّ — engineering
SEC_FORMS = ("8-K", "6-K")                         # §② مطابقةٌ تامّة · بلا `/A` — engineering
RETEST_TOL = 1.01                                  # العقد §④ D حرفيًّا: قاعُ شمعة الاختبار ≤ 1.01 × VWAP
UNKNOWN_MAX = 0.05                                 # §③-③ المجهولُ فوق 5% ⟵ «لا قياس»
NEWS_PAGE_CAP = 600                                # §③-① سقفُ صفحات جلب الأخبار (بلوغُه ⟵ «لا قياس»)
SEC_SLEEP = 0.12                                   # كبحُ نداءات SEC (حدُّها المعلَن 10/ث)
V2_FILE = "vwap_mom_feas_v2_2026-09.json"          # §⑤ فحصُ الإعادة


def log(m=""):
    print(m, flush=True)


# ── دوالُّ نقيّة (بلا شبكة · مقفولةٌ في السويّة) ──────────────────────────────
def vwap_series(bars):
    """VWAP تراكميّ لكلّ دقيقة: bars = [(mod, o, h, l, c, v)] مرتّبة ⟵ [vwap بعد كلّ دقيقة] (None قبل أوّل حجم)."""
    pv = vv = 0.0
    out = []
    for _m, _o, h, l, c, v in bars:
        pv += (h + l + c) / 3.0 * v
        vv += v
        out.append(pv / vv if vv > 0 else None)
    return out


def bucketize(bars, vw, start, width, end):
    """تجميعُ دقائقَ [start, end) في سلالٍ بعرض width تبدأ من start ⟵ [{s, e, o, h, l, c, dv, vwap}] — vwap عند آخر دقيقةٍ في السلّة."""
    out, cur = [], None
    for (m, o, h, l, c, v), w in zip(bars, vw):
        if m < start or m >= end:
            continue
        k = start + ((m - start) // width) * width
        if cur is None or cur["s"] != k:
            if cur is not None:
                out.append(cur)
            cur = {"s": k, "e": k + width, "o": o, "h": h, "l": l, "c": c, "dv": c * v, "vwap": w}
        else:
            cur["h"] = max(cur["h"], h)
            cur["l"] = min(cur["l"], l)
            cur["c"] = c
            cur["dv"] += c * v
            cur["vwap"] = w
    if cur is not None:
        out.append(cur)
    return out


def liq_ok(b5, i):
    """L لـ(أ): الحجمُ الدولاريّ لثلاث السلال المنتهية عند i أكبر من الثلاث قبلها · وإغلاقُ الثالثة ≥ إغلاق الأولى."""
    if i < 5:
        return False
    now = b5[i - 2]["dv"] + b5[i - 1]["dv"] + b5[i]["dv"]
    before = b5[i - 5]["dv"] + b5[i - 4]["dv"] + b5[i - 3]["dv"]
    return now > before and b5[i]["c"] >= b5[i - 2]["c"]


def liq15_ok(b15, j):
    """L لـ(ب): الحجمُ الدولاريّ للسلّة أكبر من السابقة · وإغلاقُها ≥ افتتاحها."""
    return j >= 1 and b15[j]["dv"] > b15[j - 1]["dv"] and b15[j]["c"] >= b15[j]["o"]


def first_signal(b5, b15, after_mod, need_liq=True, skip=None):
    """أوّلُ اكتمالٍ لـH (‏3×5د فوق VWAP أو 15د فوقه) ‏[∧ L] **نهايتُه ≥ after_mod** ⟵ (نهايةُ الاكتمال، النوع) أو None.

    `skip=(a, b)`: اكتمالٌ نهايتُه في (a، b] لا يُعدّ ويُكمَل البحثُ بعده — للذراع B (الممتدّة): النظاميّةُ تُتخطّى ولا تُسقط الإشارةَ اللاحقة."""
    out_ok = (lambda e: True) if skip is None else (lambda e: not (skip[0] < e <= skip[1]))
    cands = []
    for i in range(2, len(b5)):
        if all(b5[k]["vwap"] is not None and b5[k]["c"] > b5[k]["vwap"] for k in (i - 2, i - 1, i)):
            if b5[i]["e"] >= after_mod and out_ok(b5[i]["e"]) and (not need_liq or liq_ok(b5, i)):
                cands.append((b5[i]["e"], "5x3"))
                break
    for j in range(len(b15)):
        if b15[j]["vwap"] is not None and b15[j]["c"] > b15[j]["vwap"]:
            if b15[j]["e"] >= after_mod and out_ok(b15[j]["e"]) and (not need_liq or liq15_ok(b15, j)):
                cands.append((b15[j]["e"], "15x1"))
                break
    return min(cands) if cands else None


def gainer_entries(minutes, prev_close, d_min, px_min, windows, top_n=TOP_N):
    """أوّلُ دقيقةٍ يدخل فيها كلُّ رمزٍ أعلى `top_n` رابحًا — داخل نوافذ `windows` [(a, b)] من دقائق نيويورك.

    minutes: {mod: [(sym, close, dv)]} · والحجمُ الدولاريّ تراكميٌّ من 04:00 · والمؤهَّلُ سعرُه ≥ px_min وتراكمُه ≥ d_min وله إغلاقٌ سابق."""
    last, cum, first, qual = {}, {}, {}, set()
    inw = lambda m: any(a <= m < b for a, b in windows)
    for m in sorted(minutes):
        for sym, c, dv in minutes[m]:
            last[sym] = c
            cum[sym] = cum.get(sym, 0.0) + dv
            if cum[sym] >= d_min and prev_close.get(sym, 0) > 0:       # التراكمُ لا ينقص ⇒ المؤهَّلُ بالحجم يبقى مؤهَّلًا
                qual.add(sym)
        if not inw(m):
            continue
        elig = ((sym, last[sym] / prev_close[sym] - 1.0) for sym in qual if last[sym] >= px_min)
        for sym, _chg in heapq.nlargest(top_n, elig, key=lambda x: x[1]):
            first.setdefault(sym, m)
    return first


def is_session(d, session_info):
    """جلسةٌ = يومُ عملٍ (الاثنين-الجمعة) ليس عطلة · `market_calendar.session_info` لا يفحص نهايةَ الأسبوع (يُرجع السبتَ «regular»)."""
    return dt.date.fromisoformat(d).weekday() < 5 and session_info(d).get("open_ny_min") is not None


def pick_rule(medians, ladder, lo, hi):
    """أصغرُ قيمةٍ من السلّم وسيطُها بين lo وhi (شاملًا) ⟵ القيمة أو None."""
    for x in ladder:
        v = medians.get(x)
        if v is not None and lo <= v <= hi:
            return x
    return None


def count_signals(mins, ent_reg, ent_ext, op, cl):
    """عدُّ H وH ∧ L لمرشّحي U: A في النظاميّة (VWAP من op) · B في الممتدّة (VWAP من 04:00 والإشارةُ خارج النظاميّة)."""
    hA = hlA = hB = hlB = 0
    for s, m0 in ent_reg.items():
        bars = [b for b in mins.get(s, []) if op <= b[0] < cl]
        vw = vwap_series(bars)
        b5, b15 = bucketize(bars, vw, op, 5, cl), bucketize(bars, vw, op, 15, cl)
        hA += first_signal(b5, b15, m0, need_liq=False) is not None
        hlA += first_signal(b5, b15, m0, need_liq=True) is not None
    for s, m0 in ent_ext.items():
        bars = [b for b in mins.get(s, []) if EXT_START <= b[0] < EXT_END]
        vw = vwap_series(bars)
        b5, b15 = bucketize(bars, vw, EXT_START, 5, EXT_END), bucketize(bars, vw, EXT_START, 15, EXT_END)
        for need, attr in ((False, "h"), (True, "hl")):
            # تصحيح 2026-10-28 (تشغيلة 40709709437): كان يأخذ أوّلَ H ثمّ يُسقطه إن وقع في النظاميّة ⟵ H∧L فاق H في 32 من 105 يومًا-درجة
            sig = first_signal(b5, b15, m0, need_liq=need, skip=(op, cl))
            ok = sig is not None
            if attr == "h":
                hB += ok
            else:
                hlB += ok
    return hA, hlA, hB, hlB


# ── v2: الكسرُ الصاعد للفيواب (الملحق 1) ─────────────────────────────────────
def break_events(b5, b15, skip=None):
    """أحداثُ الكسر الصاعد بترتيبها (الملحق 1 §②): شمعةُ 5 دقائق أُغلقت **تحت** VWAP ثمّ أوّلُ إغلاقٍ **فوقه** (شمعةُ الكسر k) ثمّ
    (أ) إغلاقاتُ k+1 وk+2 وk+3 كلُّها فوقه ⟵ الحدثُ عند نهاية k+3 · **أو** (ب) أوّلُ شمعة 15 دقيقة تبدأ بعد نهاية k تُغلق فوقه وكلُّ
    شموع الـ5 بين نهاية k وبدايتها فوقه ⟵ الحدثُ عند نهايتها · والأبكرُ منهما. ثمّ يلزم إغلاقٌ تحته من جديد لكسرٍ آخر.
    `skip=(a, b)`: حدثٌ نهايتُه في (a، b] لا يُعدّ (الذراع B). ⟵ [(نهاية، النوع، فهرسُ الشمعة، k)]."""
    out_ok = (lambda e: True) if skip is None else (lambda e: not (skip[0] < e <= skip[1]))
    above = lambda b: b["vwap"] is not None and b["c"] > b["vwap"]          # noqa: E731
    below_ = lambda b: b["vwap"] is not None and b["c"] < b["vwap"]         # noqa: E731
    out, below, n = [], False, len(b5)
    for k in range(n):
        if below_(b5[k]):
            below = True
            continue
        if not (below and above(b5[k])):
            continue
        below = False
        cands = []
        if k + 3 < n and all(above(b5[j]) for j in (k + 1, k + 2, k + 3)):
            cands.append((b5[k + 3]["e"], "5x3", k + 3))
        j15 = next((j for j in range(len(b15)) if b15[j]["s"] >= b5[k]["e"]), None)
        if j15 is not None and above(b15[j15]) and all(above(b) for b in b5[k + 1:] if b5[k]["e"] <= b["s"] < b15[j15]["s"]):
            cands.append((b15[j15]["e"], "15x1", j15))
        if cands:
            e, kind, idx = min(cands)
            if out_ok(e):
                out.append((e, kind, idx, k))
    return out


def event_liq(b5, b15, ev):
    """L للحدث (العقد §② كما هو): لـ(أ) `liq_ok` على شمعة الإكمال · لـ(ب) `liq15_ok` على شمعة الـ15."""
    e, kind, idx, _k = ev
    return liq_ok(b5, idx) if kind == "5x3" else liq15_ok(b15, idx)


def cum_dollar_at(bars, end_mod):
    """الحجمُ الدولاريُّ التراكميّ من 04:00 لدقائقَ قبل `end_mod` (Σ إغلاق × حجم)."""
    return sum(c * v for m, _o, _h, _l, c, v in bars if EXT_START <= m < end_mod)


def day_events(bars, op, cl, d_ladder, px_min):
    """لرمزٍ في يوم: لكلّ درجةٍ ولكلّ ذراع — أوّلُ حدثٍ مؤهَّل (سعرُ إغلاق الإكمال ≥ px_min وتراكمُ الدولار حتى نهايته ≥ الدرجة)
    ⟵ {("A"|"B", d): {"H": (نهاية، النوع) أو None, "HL": … أو None}}. A: النظاميّة وVWAP من الافتتاح · B: 04:00-20:00 وVWAP من 04:00 خارج النظاميّة."""
    out = {}
    for arm, lo, hi, skip in (("A", op, cl, None), ("B", EXT_START, EXT_END, (op, cl))):
        bb = [b for b in bars if lo <= b[0] < hi]
        vw = vwap_series(bb)
        b5, b15 = bucketize(bb, vw, lo, 5, hi), bucketize(bb, vw, lo, 15, hi)
        evs = break_events(b5, b15, skip=skip)
        info = []
        for ev in evs:
            px = b5[ev[2]]["c"] if ev[1] == "5x3" else b15[ev[2]]["c"]
            info.append((ev, px, cum_dollar_at(bars, ev[0]), event_liq(b5, b15, ev)))
        for d in d_ladder:
            ok = [(ev, liq) for ev, px, cum, liq in info if px >= px_min and cum >= d]
            h = ok[0][0] if ok else None
            hl = next((ev for ev, liq in ok if liq), None)
            out[(arm, d)] = {"H": (h[0], h[1]) if h else None, "HL": (hl[0], hl[1]) if hl else None}
    return out


# ── v3: المحفّزُ شرطٌ للمجتمع ‏+ الذراع D (الملحق 2) ─────────────────────────────
def _iso_ts(s):
    """«2026-09-14T12:30:00Z» (أو بكسورٍ أو بإزاحة) ⟵ ثانيةُ UTC · أو None."""
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except (TypeError, ValueError):
        return None


def news_index(items, max_tickers=NEWS_MAX_TICKERS):
    """أخبارُ Polygon [{id, published_utc, tickers}] ⟵ ({رمز: [ثانية]} للخاصّ بالشركة (رموزُه ≤ max_tickers) · {رمز: [ثانية]} لكلّ خبر) مرتّبة · بلا تكرار id."""
    seen, strict, anyn = set(), {}, {}
    for it in items:
        iid = it.get("id")
        if iid is not None:
            if iid in seen:
                continue
            seen.add(iid)
        ts = _iso_ts(it.get("published_utc"))
        tks = [str(t).strip().upper() for t in (it.get("tickers") or []) if str(t).strip()]
        if ts is None or not tks:
            continue
        for t in set(tks):
            anyn.setdefault(t, []).append(ts)
            if len(set(tks)) <= max_tickers:
                strict.setdefault(t, []).append(ts)
    for d in (strict, anyn):
        for v in d.values():
            v.sort()
    return strict, anyn


def make_acc_ts(parse_acc, to_ny):
    """`acceptanceDateTime` ⟵ ثانيةُ UTC بتفسير «B» المحسوم في `T-PRE-EDGAR-2` (‏`edgar2_probe.parse_acc`/`to_ny` بالاسم · بُنيتا لقراءة لحظة القبول نفسِها)."""
    def f(s):
        p = parse_acc(s)
        return None if p is None else to_ny(p, "B").timestamp()
    return f


def sec_index(recent, forms, acc_ts):
    """`filings.recent` (مصفوفاتٌ متوازية) ⟵ [(ثانيةُ القبول، النموذج، البنود)] مرتّبة للنماذج المطلوبة بالمطابقة التامّة."""
    fm = recent.get("form") or []
    ac = recent.get("acceptanceDateTime") or []
    it = recent.get("items") or [""] * len(fm)
    out = []
    for i, f in enumerate(fm):
        if f in forms and i < len(ac):
            ts = acc_ts(ac[i])
            if ts is not None:
                out.append((ts, f, it[i] if i < len(it) else ""))
    out.sort()
    return out


def sec_depth_ok(recent, has_older, since_date):
    """عمقُ `submissions`: كاملٌ إن لم تكن صفحاتٌ أقدم · أو أقدمُ تاريخ إيداعٍ في `recent` ≤ since_date (نصّ YYYY-MM-DD)."""
    if not has_older:
        return True
    fd = [d for d in (recent.get("filingDate") or []) if d]
    return bool(fd) and min(fd) <= since_date


def parse_master_idx(text, forms):
    """فهرسُ EDGAR اليوميّ (`master.YYYYMMDD.idx` · CIK|Company|Form|Date|File) ⟵ {CIK} لمن أودع نموذجًا مطلوبًا."""
    out = set()
    for ln in (text or "").splitlines():
        p = ln.split("|")
        if len(p) == 5 and p[0].strip().isdigit() and p[2].strip() in forms:
            out.add(int(p[0]))
    return out


def any_in(ts_list, a, b):
    """هل في قائمة الثواني المرتّبة عنصرٌ بين a وb شاملًا."""
    i = bisect.bisect_left(ts_list, a)
    return i < len(ts_list) and ts_list[i] <= b


def catalyst_flags(sym, a, b, nstrict, nany, sec_ts, sec8k_ts, sec_known):
    """محفّزُ حدثٍ نافذتُه [a، b] (ثوانٍ):
    news = خبرٌ خاصٌّ بالشركة · news_any = أيُّ خبر · sec/sec8k: True/False · أو None إن CIK معلومٌ وتعذّر `submissions` أو قصّر عمقُه (`sec_known` False) ·
    و**C** = news أو sec · ومجهولٌ (None) إن لا خبرَ خاصًّا وsec مجهول (الملحق 2 §③)."""
    news = any_in(nstrict.get(sym, ()), a, b)
    news_any = any_in(nany.get(sym, ()), a, b)
    if sec_known:
        sec, s8 = any_in(sec_ts, a, b), any_in(sec8k_ts, a, b)
    else:
        sec = s8 = None
    c = True if (news or sec) else (None if sec is None else False)
    return {"news": news, "news_any": news_any, "sec": sec, "sec8k": s8, "C": c}


def retest_signal(b5, b15, after_e, tol=RETEST_TOL, need_liq=False):
    """الذراع D (الملحق 2 §②): شمعةُ الاختبار = أوّلُ شمعة 5 دقائق تبدأ عند `after_e` أو بعده قاعُها ≤ tol × VWAP عند نهايتها ·
    ثمّ الثباتُ بتعريف العقد الأصليّ §② **كلُّه بعدها**: (أ) ثلاثُ إغلاقاتٍ متتالية فوق VWAP أوّلُها بعد شمعة الاختبار · (ب) شمعةُ 15 تبدأ عند نهاية
    شمعة الاختبار أو بعدها تُغلق فوقه · والأبكرُ [∧ L: أوّلُ اكتمالٍ يحقّقها] ⟵ (نهاية، النوع، فهرس) أو None."""
    t = next((i for i, b in enumerate(b5) if b["s"] >= after_e and b["vwap"] is not None and b["l"] <= tol * b["vwap"]), None)
    if t is None:
        return None
    te = b5[t]["e"]
    above = lambda b: b["vwap"] is not None and b["c"] > b["vwap"]          # noqa: E731
    cands = []
    for i in range(t + 3, len(b5)):
        if all(above(b5[k]) for k in (i - 2, i - 1, i)) and (not need_liq or liq_ok(b5, i)):
            cands.append((b5[i]["e"], "5x3", i))
            break
    for j in range(len(b15)):
        if b15[j]["s"] >= te and above(b15[j]) and (not need_liq or liq15_ok(b15, j)):
            cands.append((b15[j]["e"], "15x1", j))
            break
    return min(cands) if cands else None


def day_candidates(bars, op, cl, px_min, d0):
    """لرمزٍ في يوم: أحداثُ الكسر لكلّ ذراع بسعر إكمالٍ ≥ px_min وتراكمٍ ≥ d0 (أدنى درجة) ⟵ {"A": [ev], "B": [ev]} مرتّبة
    ev = (نهاية، النوع، سعرُ الإكمال، التراكم، L، نهايةُ D، نهايةُ D ∧ L) — D لـA ذاتِ L وحدَها (وإلّا None) وسعرُ إكماله ≥ px_min."""
    out = {}
    for arm, lo, hi, skip in (("A", op, cl, None), ("B", EXT_START, EXT_END, (op, cl))):
        bb = [b for b in bars if lo <= b[0] < hi]
        vw = vwap_series(bb)
        b5, b15 = bucketize(bb, vw, lo, 5, hi), bucketize(bb, vw, lo, 15, hi)
        evs = []
        for ev in break_events(b5, b15, skip=skip):
            px = b5[ev[2]]["c"] if ev[1] == "5x3" else b15[ev[2]]["c"]
            cum = cum_dollar_at(bars, ev[0])
            if px < px_min or cum < d0:
                continue
            liq = event_liq(b5, b15, ev)
            dh = dhl = None
            if arm == "A" and liq:
                for need in (False, True):
                    rt = retest_signal(b5, b15, ev[0], need_liq=need)
                    if rt is not None and (b5[rt[2]]["c"] if rt[1] == "5x3" else b15[rt[2]]["c"]) >= px_min:
                        if need:
                            dhl = rt[0]
                        else:
                            dh = rt[0]
            evs.append((ev[0], ev[1], px, cum, liq, dh, dhl))
        out[arm] = evs
    return out


def tally_v3(evs, d, flag_at):
    """عدُّ رمزٍ/يومٍ/ذراعٍ عند درجة d (الملحق 2): الأحداثُ المؤهَّلة بالدرجة ثمّ المحفّزُ لكلٍّ منها (`flag_at(نهاية)`) ⟵
    H: حدثٌ بمحفّز · HL: حدثٌ بمحفّز ∧ L · U: لا حدثَ بمحفّز ومجهولٌ واحدٌ على الأقلّ · H0/HL0: بلا C (فحصُ الإعادة) ·
    DH/DHL: D بعد **أوّل** حدث HL ∧ C · H_any: C بأيّ خبر (بلا حدّ الرموز) · H_8k: C بـ8-K وحدَه (بلا 6-K) · src: مصدرُ أوّل حدثٍ بمحفّز."""
    elig = [e for e in evs if e[3] >= d]
    fl = [(e, flag_at(e[0])) for e in elig]
    h = next(((e, f) for e, f in fl if f["C"]), None)
    hl = next(((e, f) for e, f in fl if f["C"] and e[4]), None)
    src = None
    if h is not None:
        f = h[1]
        src = "both" if (f["news"] and f["sec"]) else ("news" if f["news"] else "sec")
    return {"H": h is not None, "HL": hl is not None,
            "U": h is None and any(f["C"] is None for _e, f in fl),
            "H0": bool(elig), "HL0": any(e[4] for e in elig),
            "DH": hl is not None and hl[0][5] is not None, "DHL": hl is not None and hl[0][6] is not None,
            "H_any": any(f["news_any"] or f["sec"] for _e, f in fl),
            "H_8k": any(f["news"] or f["sec8k"] for _e, f in fl),
            "src": src}


def coverage_gates(news_meta, idx_missing, unknown, denom, days_missing):
    """حارسُ التغطية (الملحق 2 §③) ⟵ (يصلح؟، [أسباب]) — أيُّ سببٍ ⟵ «لا قياس» لا تُطبَّق معه القاعدة ولا يُعَدّ المرّةَ الثالثة."""
    why = []
    if not news_meta.get("complete"):
        why.append("news_incomplete")
    if idx_missing:
        why.append("edgar_index_missing")
    if denom and unknown / denom > UNKNOWN_MAX:
        why.append("unknown_over_5pct")
    if days_missing:
        why.append("minute_day_missing")
    return (not why), why


def verdict_v3(gates_ok, pick):
    """الملحق 2 §③-§④: «لا قياس» إن سقط الحارس · وإلّا «اختارت» بدرجة · أو «توقّف» (المرّة الثالثة بلا درجة ⟵ يتوقّف المحور)."""
    if not gates_ok:
        return "no_measure"
    return "pick" if pick is not None else "stop"


KEYS_A = ("H", "HL", "U", "H0", "HL0", "DH", "DHL", "H_any", "H_8k")
KEYS_B = ("H", "HL", "U", "H0", "HL0")


def ny_ts(day, mod):
    """دقيقةٌ من يومٍ بتوقيت نيويورك ⟵ ثانيةُ UTC."""
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(mod // 60, mod % 60), tzinfo=NY).timestamp()


def count_day(cands_day, day, win_start, sec, nstrict, nany, d_ladder=D_LADDER):
    """عدُّ يومٍ بالمحفّز (الملحق 2): `cands_day` {رمز: day_candidates} · `win_start` = 16:00 نيويورك للجلسة السابقة (ثانية) ·
    `sec` {tmap: رمز ⟵ CIK, filers: {CIK}, all/8k: {CIK: [ثانية]}, rows: {CIK: [(ثانية، نموذج، بنود)]}, unknown: {CIK}} ⟵
    (عدّاتٌ {(ذراع، درجة، مفتاح): n} · مصدرُ أوّل حدثٍ بمحفّز عند A وأدنى درجة · بنودُ 8-K له · بلا CIK · مقامُ المجهول · المجهول).
    بلا CIK ⟵ الأخبارُ وحدَها (SEC معلومٌ صفرًا) · CIK لم يُودِع في المدى ⟵ SEC صفرٌ معلوم · CIK في `unknown` ⟵ SEC مجهول."""
    cnt, src, items = {}, {"news": 0, "sec": 0, "both": 0}, {}
    nocik = den_u = num_u = 0
    d0 = d_ladder[0]
    for sym, cd in cands_day.items():
        cik = sec["tmap"].get(sym)
        if cik is None or cik not in sec["filers"]:
            s_all, s_8k, known = (), (), True
        else:
            s_all, s_8k, known = sec["all"].get(cik, ()), sec["8k"].get(cik, ()), cik not in sec["unknown"]

        def flag_at(e, sym=sym, s_all=s_all, s_8k=s_8k, known=known):
            return catalyst_flags(sym, win_start, ny_ts(day, e), nstrict, nany, s_all, s_8k, known)
        for arm, ks in (("A", KEYS_A), ("B", KEYS_B)):
            for d in d_ladder:
                t = tally_v3(cd[arm], d, flag_at)
                for k in ks:
                    cnt[(arm, d, k)] = cnt.get((arm, d, k), 0) + int(bool(t[k]))
                if arm != "A" or d != d0:
                    continue
                if t["src"]:
                    src[t["src"]] += 1
                if t["src"] in ("sec", "both"):
                    e0 = next(e for e in cd["A"] if e[3] >= d0 and flag_at(e[0])["C"])
                    b = ny_ts(day, e0[0])
                    r0 = next((r for r in sec["rows"].get(cik, ()) if r[1] == "8-K" and win_start <= r[0] <= b), None)
                    for it in (str(r0[2]).split(",") if r0 else []):
                        if it.strip():
                            items[it.strip()] = items.get(it.strip(), 0) + 1
                if t["H0"]:
                    if cik is None:
                        nocik += 1
                    else:
                        den_u += 1
                        num_u += int(t["U"])
    return cnt, src, items, nocik, den_u, num_u


# ── الشبكة (رنر فقط) ──────────────────────────────────────────────────────────
def _ny_mod(ns):
    d = dt.datetime.fromtimestamp(int(ns) / 1e9, tz=NY)
    return d.date().isoformat(), d.hour * 60 + d.minute


def _key(prefix, day):
    return f"{prefix}/{day[:4]}/{day[5:7]}/{day}.csv.gz"


def _download(FP, key, dest, tries=4):
    for i in range(tries):
        for ep in FP.ENDPOINTS:
            rc, _, err = FP.aws("cp", f"s3://{FP.BUCKET}/{key}", dest, endpoint=ep, timeout=1800)
            if rc == 0:
                return True, ep
            # 🔧 S3G1 (‏2026-10-29): `s3 cp` ردّ 403 على كلّ يومٍ في `40800488513` و`get-object` نجح في المِجَسّ ⟵ يُجرَّب بعده
            rc2, _, err2 = FP.get_object(key, dest, endpoint=ep, timeout=1800)
            if rc2 == 0:
                log(f"   ↩️ `s3 cp` تعذّر ونجح `get-object`: {key}")
                return True, ep
        # 🔧 S3E1 (‏2026-10-29): ذيلُ رسالة aws لا رأسُها — المسارُ كان يبتلع الـ140 محرفًا فضاع رمزُ الخطأ (تشغيلة 40790473567)
        log(f"   ⛔ تعذّر التنزيل ({i + 1}/{tries}): {key} · cp: {(err or '').strip()[-240:]} · get-object: {(err2 or '').strip()[-160:]}")
        time.sleep(10 * (2 ** i))
    return False, None


def _head(FP, key):
    for ep in FP.ENDPOINTS:
        rc, out, _ = FP.aws_api("head-object", "--bucket", FP.BUCKET, "--key", key, endpoint=ep)
        if rc == 0:
            try:
                return float(json.loads(out)["ContentLength"])
            except (ValueError, KeyError, TypeError):
                return None
    return None


def _read_minutes(path):
    """{sym: [(mod, o, h, l, c, v)]} مرتّبة ⟵ من ملفّ الدقيقة."""
    out = {}
    with gzip.open(path, "rt") as fh:
        rd = csv.reader(fh)
        hd = [h.strip().lower() for h in next(rd)]
        it, io, ih, il, ic, iv, iw = (hd.index(x) for x in ("ticker", "open", "high", "low", "close", "volume", "window_start"))
        for r in rd:
            try:
                _d, m = _ny_mod(r[iw])
                out.setdefault(r[it].strip().upper(), []).append(
                    (m, float(r[io]), float(r[ih]), float(r[il]), float(r[ic]), float(r[iv])))
            except (ValueError, IndexError):
                continue
    for v in out.values():
        v.sort()
    return out


def _poly(path, key, params=None, tries=3):
    import requests
    p = dict(params or {})
    for i in range(tries):
        try:
            r = requests.get("https://api.polygon.io" + path, params=p,
                             headers={"Authorization": f"Bearer {key}"}, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 * (2 ** i))
                continue
            return None
        except Exception:                                     # noqa: BLE001
            time.sleep(2 * (2 ** i))
    return None


def _paged(url_json, key, cap=40):
    import requests
    out, calls = [], 0
    nxt = None
    data = url_json
    while data is not None and calls < cap:
        out.extend(data.get("results") or [])
        nxt = data.get("next_url")
        if not nxt:
            break
        calls += 1
        try:
            r = requests.get(nxt, headers={"Authorization": f"Bearer {key}"}, timeout=30)
            data = r.json() if r.status_code == 200 else None
        except Exception:                                     # noqa: BLE001
            data = None
    return out, calls + 1


def _get_url(url, key, tries=3):
    import requests
    for i in range(tries):
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (2 ** i))
                continue
            return None
        except Exception:                                     # noqa: BLE001
            time.sleep(2 * (2 ** i))
    return None


def fetch_news(key, a_iso, b_iso, cap=NEWS_PAGE_CAP):
    """جلبٌ واحدٌ لأخبار Polygon في المدى مرتّبةً بالنشر (بلا رمز) ⟵ (عناصرُ مختصرة، {pages, complete, items, why})."""
    from urllib.parse import urlencode
    url = "https://api.polygon.io/v2/reference/news?" + urlencode(
        {"published_utc.gte": a_iso, "published_utc.lte": b_iso, "order": "asc", "sort": "published_utc", "limit": 1000})
    out, pages = [], 0
    while url:
        if pages >= cap:
            return out, {"pages": pages, "complete": False, "items": len(out), "why": "cap"}
        j = _get_url(url, key)
        if j is None:
            return out, {"pages": pages, "complete": False, "items": len(out), "why": "page_failed"}
        pages += 1
        for it in j.get("results") or []:
            out.append({"id": it.get("id"), "published_utc": it.get("published_utc"), "tickers": it.get("tickers") or []})
        url = j.get("next_url")
    return out, {"pages": pages, "complete": True, "items": len(out), "why": None}


def _sec_get(url, ua, as_json, tries=3):
    import requests
    for i in range(tries):
        try:
            r = requests.get(url, headers={"User-Agent": ua, "Accept-Encoding": "gzip, deflate"}, timeout=60)
            time.sleep(SEC_SLEEP)
            if r.status_code == 200:
                return r.json() if as_json else r.text
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 * (2 ** i))
                continue
            return None
        except Exception:                                     # noqa: BLE001
            time.sleep(2 * (2 ** i))
    return None


def _prev_session(day, MC):
    pdx = dt.date.fromisoformat(day) - dt.timedelta(1)
    while not is_session(pdx.isoformat(), MC.session_info):
        pdx -= dt.timedelta(1)
    return pdx.isoformat()


def main():
    """v3 (الملحق 2): ① ملفّاتُ الدقيقة ⟵ أحداثُ v2 بلا C (فحصُ الإعادة) وأحداثُ v3 المرشّحة · ② أخبارُ Polygon للشهر · ③ فهارسُ EDGAR ثمّ `submissions`
    · ④ العدُّ بالمحفّز لكلّ يومٍ ودرجة ⟵ الوسيطُ مطبوعًا قبل القاعدة ⟵ حارسُ التغطية ⟵ القاعدةُ ⟵ الحكم (اختارت · توقّف · لا قياس)."""
    import flatfiles_probe as FP
    import market_calendar as MC
    from prelink_px import PX_MIN
    key = os.environ.get("POLYGON_API_KEY", "")
    ua = (os.environ.get("SEC_CONTACT") or "").strip()
    month = os.environ.get("VWM_MONTH", "2026-09")
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    if not ua:
        log("⛔ SEC_CONTACT غيرُ مضبوط — عطبُ إعداد (الملحق 2 §②: SEC مصدرٌ لازم)")
        return 2
    t0 = time.time()
    res = {"version": "v3-addendum-2", "month": month, "px_min": PX_MIN, "d_ladder": D_LADDER, "d_rule": D_RULE,
           "news_max_tickers": NEWS_MAX_TICKERS, "sec_forms": SEC_FORMS, "retest_tol": RETEST_TOL, "unknown_max": UNKNOWN_MAX}
    y, mo = int(month[:4]), int(month[5:7])
    days = [d.isoformat() for d in (dt.date(y, mo, 1) + dt.timedelta(k) for k in range(31))
            if d.month == mo and is_session(d.isoformat(), MC.session_info)]
    p0 = _prev_session(days[0], MC)
    win_a = {d: dt.datetime.combine(dt.date.fromisoformat(_prev_session(d, MC)), dt.time(16, 0), tzinfo=NY).timestamp() for d in days}
    log(f"📅 {month}: {len(days)} جلسة · الجلسةُ السابقة {p0} · PX_MIN={PX_MIN} · السلّم {D_LADDER} · القاعدة {D_RULE} · "
        f"خبرٌ خاصّ ≤{NEWS_MAX_TICKERS} رموز · SEC {SEC_FORMS}")
    # ① ملفّاتُ الدقيقة
    tmp = tempfile.mkdtemp(prefix="vwm3_")
    cands, v2c, days_missing, nsyms = {}, {}, [], {}
    self_mismatch = 0
    for day in days:
        info = MC.session_info(day)
        op, cl = info["open_ny_min"], info["close_ny_min"]
        path = os.path.join(tmp, "d.csv.gz")
        okx, _ = _download(FP, _key(MIN_PREFIX, day), path)
        if not okx:
            days_missing.append(day)
            continue
        mins = _read_minutes(path)
        os.remove(path)
        cnt2 = {(arm, d, k): 0 for arm in "AB" for d in D_LADDER for k in ("H", "HL")}
        dc = {}
        for sym, bars in mins.items():
            ev = day_events(bars, op, cl, D_LADDER, PX_MIN)
            cd = day_candidates(bars, op, cl, PX_MIN, D_LADDER[0])
            for (arm, d), v in ev.items():
                cnt2[(arm, d, "H")] += v["H"] is not None
                cnt2[(arm, d, "HL")] += v["HL"] is not None
                e = [x for x in cd[arm] if x[3] >= d]
                if bool(e) != (v["H"] is not None) or any(x[4] for x in e) != (v["HL"] is not None):
                    self_mismatch += 1
            if cd["A"] or cd["B"]:
                dc[sym] = cd
        cands[day], nsyms[day] = dc, len(mins)
        v2c[day] = {f"{arm}@{d}": {"H": cnt2[(arm, d, "H")], "HL": cnt2[(arm, d, "HL")]} for arm in "AB" for d in D_LADDER}
        log(f"① {day}: رموز {len(mins)} · بأحداث {len(dc)} · بلا C: A@250k H={v2c[day]['A@250000']['H']} · فحصٌ داخليّ {self_mismatch}")
        del mins
    ok_days = [d for d in days if d not in days_missing]
    # ⑤ فحصُ الإعادة مقابل v2 المنشورة
    v2chk = {"compared": 0, "mismatch": 0, "examples": []}
    try:
        old = json.load(open(V2_FILE, encoding="utf-8"))
        if old.get("month") == month:
            for d in ok_days:
                for k, v in v2c[d].items():
                    o = (old.get("per_day") or {}).get(d, {}).get(k)
                    v2chk["compared"] += 1
                    if o is None or o.get("H") != v["H"] or o.get("HL") != v["HL"]:
                        v2chk["mismatch"] += 1
                        if len(v2chk["examples"]) < 10:
                            v2chk["examples"].append([d, k, o, v])
    except (OSError, ValueError) as e:
        v2chk["error"] = type(e).__name__
    log(f"⑤ فحصُ الإعادة مقابل v2: {v2chk['mismatch']} فرقًا من {v2chk['compared']} · الفحصُ الداخليّ {self_mismatch}")
    # ② الأخبار
    a_iso = dt.datetime.combine(dt.date.fromisoformat(p0), dt.time(16, 0), tzinfo=NY).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    b_iso = dt.datetime.combine(dt.date.fromisoformat(days[-1]), dt.time(20, 0), tzinfo=NY).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items, nmeta = fetch_news(key, a_iso, b_iso)
    nstrict, nany = news_index(items)
    nmeta.update({"from": a_iso, "to": b_iso, "tickers_strict": len(nstrict), "tickers_any": len(nany)})
    del items
    log(f"② الأخبار {a_iso} ⟵ {b_iso}: {nmeta['items']} خبرًا في {nmeta['pages']} صفحة · مكتمل={nmeta['complete']} · "
        f"رموزٌ بخبرٍ خاصّ {len(nstrict)} · بأيّ خبر {len(nany)}")
    # ③ SEC
    cmap = _sec_get("https://www.sec.gov/files/company_tickers.json", ua, True) or {}
    tmap = {str(v.get("ticker", "")).upper(): int(v["cik_str"]) for v in cmap.values() if isinstance(v, dict) and v.get("cik_str")}
    filers, idx_missing = set(), ([] if tmap else ["company_tickers"])      # خريطةٌ تعذّرت ⟵ مصدرُ SEC ناقص (§③-②) لا «بلا CIK» للكلّ
    for d in [p0] + days:
        dd = dt.date.fromisoformat(d)
        url = (f"https://www.sec.gov/Archives/edgar/daily-index/{dd.year}/QTR{(dd.month - 1) // 3 + 1}/"
               f"master.{dd.strftime('%Y%m%d')}.idx")
        text = _sec_get(url, ua, False)
        if text is None:
            idx_missing.append(d)
            continue
        filers |= parse_master_idx(text, SEC_FORMS)
    syms_all = set()
    for v in cands.values():
        syms_all |= set(v)
    need = sorted({tmap[s] for s in syms_all if s in tmap and tmap[s] in filers})
    from edgar2_probe import parse_acc, to_ny        # بالاسم — بُنيتا لقراءة لحظة القبول في `T-PRE-EDGAR-2` (المِجَسُّ باقٍ والدراسةُ مُغلَقة لا تُشغَّل)
    acc_ts = make_acc_ts(parse_acc, to_ny)
    sec_all, sec_8k, sec_rows, sec_unknown = {}, {}, {}, set()
    for cik in need:
        j = _sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", ua, True)
        if j is None:
            sec_unknown.add(cik)
            continue
        rec = (j.get("filings") or {}).get("recent") or {}
        if not sec_depth_ok(rec, bool((j.get("filings") or {}).get("files")), p0):
            sec_unknown.add(cik)
            continue
        rows = sec_index(rec, SEC_FORMS, acc_ts)
        sec_rows[cik] = rows
        sec_all[cik] = [r[0] for r in rows]
        sec_8k[cik] = [r[0] for r in rows if r[1] == "8-K"]
    smeta = {"tickers_mapped": len(tmap), "filers": len(filers), "index_days": 1 + len(days), "index_missing": idx_missing,
             "event_symbols": len(syms_all), "with_cik": sum(1 for s in syms_all if s in tmap), "need": len(need),
             "unknown_ciks": len(sec_unknown)}
    log(f"③ SEC: خريطة {len(tmap)} · مودِعو {SEC_FORMS} في المدى {len(filers)} · رموزُ الأحداث {len(syms_all)} (بـCIK {smeta['with_cik']}) · "
        f"submissions {len(need)} · مجهول {len(sec_unknown)} · فهارسُ ناقصة {idx_missing}")
    # ④ العدّ
    per_day, src_tot, items_tally = {}, {"news": 0, "sec": 0, "both": 0}, {}
    nocik = den_u = num_u = 0
    sec = {"tmap": tmap, "filers": filers, "all": sec_all, "8k": sec_8k, "rows": sec_rows, "unknown": sec_unknown}
    for day in ok_days:
        cnt, src_d, items_d, nc, du, nu = count_day(cands[day], day, win_a[day], sec, nstrict, nany)
        nocik, den_u, num_u = nocik + nc, den_u + du, num_u + nu
        for k, v in src_d.items():
            src_tot[k] += v
        for k, v in items_d.items():
            items_tally[k] = items_tally.get(k, 0) + v
        per_day[day] = {"symbols": nsyms[day], "with_events": len(cands[day])}
        for arm, ks in (("A", KEYS_A), ("B", KEYS_B)):
            for d in D_LADDER:
                per_day[day][f"{arm}@{d}"] = {k: cnt.get((arm, d, k), 0) for k in ks}
        log(f"④ {day}: " + " · ".join(f"{d // 1000}k A∧C={per_day[day][f'A@{d}']['H']}/{per_day[day][f'A@{d}']['HL']} "
                                      f"D={per_day[day][f'A@{d}']['DH']} B∧C={per_day[day][f'B@{d}']['H']}" for d in D_LADDER))
    med = {arm: {d: {k: st.median([per_day[x][f"{arm}@{d}"][k] for x in ok_days] or [0]) for k in ks} for d in D_LADDER}
           for arm, ks in (("A", KEYS_A), ("B", KEYS_B))}
    tot = {arm: {d: {k: sum(per_day[x][f"{arm}@{d}"][k] for x in ok_days) for k in ks} for d in D_LADDER}
           for arm, ks in (("A", KEYS_A), ("B", KEYS_B))}
    res.update({"median_by_dmin": med, "month_totals": tot, "per_day": per_day, "news": nmeta, "sec": smeta,
                "v2_check": v2chk, "self_mismatch": self_mismatch, "days_missing": days_missing,
                "nocik_A_lowest": nocik, "unknown_A_lowest": {"unknown": num_u, "denom_with_cik": den_u},
                "src_A_lowest_month": src_tot, "items_8k_A_lowest": dict(sorted(items_tally.items(), key=lambda x: -x[1])[:15])})
    log("① الوسيطُ/يوم قبل أيّ اختيار: " + " · ".join(
        f"{d // 1000}k A∧C H={med['A'][d]['H']} HL={med['A'][d]['HL']} D={med['A'][d]['DH']}/{med['A'][d]['DHL']} "
        f"(بلا C {med['A'][d]['H0']}) B∧C H={med['B'][d]['H']} HL={med['B'][d]['HL']}" for d in D_LADDER))
    ok, why = coverage_gates(nmeta, idx_missing, num_u, den_u, days_missing)
    pick = pick_rule({d: med["A"][d]["H"] for d in D_LADDER}, D_LADDER, *D_RULE) if ok else None
    verdict = verdict_v3(ok, pick)
    res.update({"gates_ok": ok, "gates_why": why, "rule_applied": ok, "D_MIN_pick_by_rule": pick, "verdict": verdict})
    log(f"⑥ الحارس: {'يصلح' if ok else 'لا قياس ' + str(why)} · المجهول {num_u} من {den_u} · بلا CIK {nocik} · "
        f"قاعدةُ §③ على A ∧ C ⟵ D_MIN = {pick} · الحكم: {verdict}")
    res["seconds"] = round(time.time() - t0, 1)
    print("VWMFEAS_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
