"""📈🔎 جدوى `T-VWAP-MOM` v4 — **التقاطعُ الكامل** (الملحق 3 `vwap_mom_prereg_addendum_3.md` · فتحٌ بقرار المالك 2026-10-29 · قبل أيّ رقم).

**عدٌّ لا عائد** (العقد §⑧): لا R ولا عائدَ ولا قمّةَ لاحقة. والمحورُ **مُغلَقٌ مُنفَّذًا** بعد v3 — هذه الأداةُ تقرأ الحارسَ نفسَه
(`vwap_mom_feas._closed_now` ⟵ `VWM_REOPEN=1` بقرار المالك وحدَه) ثمّ **بصمةَ الملحق 3** قبل أيّ شبكة (خروج 9 إن تغيّر).
الحدثُ A = الكسرُ الصاعد (الملحق 1 · `break_events` بالاسم) ⟵ في الحدث نفسِه:
① التغيّرُ ‏+20% فأكثر عن إغلاق الجلسة السابقة (مسوّى بتقسيم اليوم) · ② حجمُ الأسهم من 04:00 حتى الحدث ÷ متوسّطِه في 20 جلسةً حتى الدقيقة نفسِها
(‏3 حاكم · 5 مِجَسّ) · ③ L (`event_liq` بالاسم) · ④ بيانٌ من سلكٍ من الأربعة أو `8-K` في النافذة · ⑤ سعرٌ من 1 إلى ما دون 20 ونوعٌ CS/ADRC/OS وليس SPAC ·
وD بعد أوّل A كامل (`retest_signal` بالاسم) وصفًا. والقاعدةُ على وسيط `FULL` في اليوم (`pick_rule` · ‏10-40).
بلا تلغرام · بلا حالة · بلا كتابةٍ في المستودع · والمُخرَجُ سطرُ `VWMFEAS4_JSON`.
"""
import bisect
import datetime as dt
import hashlib
import json
import math
import os
import re
import statistics as st
import sys
import tempfile
import time
from array import array
from collections import deque
from urllib.parse import urlparse

import vwap_mom_feas as V3

ADD3_FILE = "vwap_mom_prereg_addendum_3.md"
ADD3_SHA = "c45043e7d3361950efcc2e3ca922815a86ebbaf747ec2b9faa8be7bec89d5c77"   # بصمةُ الملحق 3 (`VWM10`) · تغيّرُه ⟵ خروج 9
SHA_RC = 9
CHG_MIN = 0.20                                     # ① بأمر المالك
RVOL_MIN = 3.0                                     # ② حاكم (engineering بأمر المالك)
RVOL_PROBE = 5.0                                   # ② مِجَسٌّ يُطبع ولا يختار
RVOL_WIN = 20                                      # ② آخرُ 20 جلسة
RVOL_MIN_PRESENT = 10                              # ② ظهورٌ في أقلّ من 10 جلسات ⟵ مجهول
PX_MAX = 20.0                                      # ⑤ سعرٌ ما دون 20
TYPES_OK = ("CS", "ADRC", "OS")                    # ⑤ الأنواعُ المقبولة في Polygon
SPAC_SIC = "6770"                                  # ⑤ blank checks
SEC_FORMS4 = ("8-K",)                              # ④ 8-K وحدَه يُحتسب
SEC_FETCH = ("8-K", "6-K")                         # ويُجلب 6-K ليُطبع وصفًا
WIRES = (("globenewswire", "GlobeNewswire"), ("prnewswire", "PRNewswire"), ("businesswire", "Business Wire"),
         ("accessnewswire", "Accesswire"), ("accesswire", "Accesswire"))
TYPE_UNKNOWN_MAX = 0.05                            # الحارس ⑦
CHG_EDGES = (0, 10, 20, 30, 50, 100)               # مدرّجُ ① بالنسبة المئويّة
RVOL_EDGES = (1, 3, 5, 10, 20)                     # مدرّجُ ②
DETAIL_CAP = 400                                   # سقفُ نداءات تفاصيل الرمز للنوع الغائب
KEYS4 = ("H0", "BASE", "C1", "C2", "C2b", "C3", "C4", "C12", "C123", "FULL", "FULL5", "DH", "DHL", "U1", "U2", "U4", "FULL_rv_unknown_as_pass")


def log(m=""):
    print(m, flush=True)


# ── دوالُّ نقيّة (بلا شبكة · مقفولةٌ في السويّة) ──────────────────────────────
def _norm(s):
    return re.sub(r"[^a-z]", "", str(s or "").lower())


def wire_of(item):
    """خبرُ Polygon ⟵ (السلك، الحقلُ الذي عُرف منه) أو None — الناشرُ ثمّ الكاتبُ ثمّ مضيفُ الرابط (الملحق 3 §③-④)."""
    pub = item.get("publisher")
    pub = pub.get("name") if isinstance(pub, dict) else pub
    try:
        host = urlparse(str(item.get("article_url") or "")).netloc
    except ValueError:
        host = ""
    for field, val in (("publisher", pub), ("author", item.get("author")), ("host", host)):
        n = _norm(val)
        if not n:
            continue
        for key, label in WIRES:
            if key in n:
                return label, field
    return None


def wire_index(items):
    """أخبارٌ [{id, published_utc, tickers, publisher, author, article_url}] ⟵ ({رمز: [ثانية]} لأخبار الأسلاك مرتّبة،
    {سلك: عناصر}، {سلك|حقل: عناصر}، {ناشر: عناصر} لكلّ الأخبار) · بلا تكرار id · بلا حدّ عددِ رموز."""
    seen, ix, by_wire, by_field, pubs = set(), {}, {}, {}, {}
    for it in items:
        iid = it.get("id")
        if iid is not None:
            if iid in seen:
                continue
            seen.add(iid)
        pub = it.get("publisher")
        pname = (pub.get("name") if isinstance(pub, dict) else pub) or "?"
        pubs[pname] = pubs.get(pname, 0) + 1
        w = wire_of(it)
        if w is None:
            continue
        by_wire[w[0]] = by_wire.get(w[0], 0) + 1
        by_field[f"{w[0]}|{w[1]}"] = by_field.get(f"{w[0]}|{w[1]}", 0) + 1
        ts = V3._iso_ts(it.get("published_utc"))
        tks = {str(t).strip().upper() for t in (it.get("tickers") or []) if str(t).strip()}
        if ts is None:
            continue
        for t in tks:
            ix.setdefault(t, []).append(ts)
    for v in ix.values():
        v.sort()
    return ix, by_wire, by_field, pubs


def ge(x, t):
    """«x ≥ t» على حدّه بلا خطأ فاصلةٍ عائمة (‏6/5 − 1 = 0.19999… لا تُسقط ‏+20% بالضبط) · وNone لا ينجح · واللانهايةُ تنجح."""
    if x is None:
        return False
    return x == math.inf or round(x, 9) >= t


def pct_change(px, prev):
    """التغيّرُ عن إغلاق الجلسة السابقة (كسرٌ لا نسبة) · أو None إن غاب الإغلاقُ أو لم يكن موجبًا."""
    if prev is None or not prev or prev <= 0 or px is None:
        return None
    return px / prev - 1.0


def price_factor(splits, day):
    """عاملُ تسوية إغلاق الأمس بتقسيمٍ يُنفَّذ يومَ الحدث: Π split_from ÷ split_to (أماميٌّ 1:2 ⟵ ½ · عكسيٌّ 10:1 ⟵ 10)."""
    f = 1.0
    for ex, sf, stt in splits or ():
        if ex == day and sf and stt:
            f *= sf / stt
    return f


def vol_factor(splits, prior_day, day):
    """عاملُ تسوية حجم جلسةٍ سابقة بتقسيماتٍ نُفِّذت بعدها حتى يوم الحدث: Π split_to ÷ split_from."""
    f = 1.0
    for ex, sf, stt in splits or ():
        if prior_day < ex <= day and sf and stt:
            f *= stt / sf
    return f


def cum_curve(bars):
    """منحنى الحجم التراكميّ من 04:00 ⟵ (array الدقائق، array التراكم) — للنافذة المتدحرجة."""
    mods, cums, c = array("H"), array("d"), 0.0
    for m, _o, _h, _l, _c, v in bars:
        if m < V3.EXT_START:
            continue
        c += v
        mods.append(m)
        cums.append(c)
    return mods, cums


def curve_at(curve, end_mod):
    """الحجمُ التراكميّ للدقائق قبل `end_mod` (بنافذة `cum_dollar_at` نفسِها: 04:00 ≤ الدقيقة < النهاية)."""
    if curve is None:
        return 0.0
    mods, cums = curve
    i = bisect.bisect_left(mods, end_mod)
    return cums[i - 1] if i > 0 else 0.0


def rvol(cur, priors, win=RVOL_WIN, min_present=RVOL_MIN_PRESENT):
    """② النسبة: `cur` ÷ متوسّطِ `priors` [(ظهر؟، حجمٌ مسوّى)] على `win` جلسة (الغائبُ صفر) · أقلُّ من `min_present` ظهورًا ⟵ None ·
    ومتوسّطٌ صفرٌ ⟵ لا نهاية."""
    if sum(1 for p, _v in priors if p) < min_present:
        return None
    mean = sum(v for _p, v in priors) / float(win)
    if mean <= 0:
        return math.inf
    return cur / mean


def bucket(x, edges):
    """سلّةُ القيمة: «تحت e0» · «e_i-e_{i+1}» · «eN+» · أو «مجهول»."""
    if x is None:
        return "?"
    if x < edges[0]:
        return f"<{edges[0]}"
    for a, b in zip(edges, edges[1:]):
        if a <= x < b:
            return f"{a}-{b}"
    return f"{edges[-1]}+"


def v4_events(bars, op, cl, px_min, d0, prev_adj, px_max=PX_MAX, chg_min=CHG_MIN):
    """لرمزٍ في يوم — أحداثُ A (الملحق 1 · النظاميّة · VWAP من الافتتاح) بسعر إكمالٍ ≥ px_min وتراكمٍ دولاريّ ≥ d0 ⟵ [ev]:
    ev = (نهاية، النوع، السعر، التراكمُ الدولاريّ، حجمُ الأسهم التراكميّ، L، نهايةُ D، نهايةُ D ∧ L) — وD لأحداث L وحدَها،
    ويُحتسب إن كان سعرُ إكماله في [px_min، px_max) وتغيّرُه عن `prev_adj` ≥ chg_min (الملحق 3 §③-⑥)."""
    bb = [b for b in bars if op <= b[0] < cl]
    vw = V3.vwap_series(bb)
    b5, b15 = V3.bucketize(bb, vw, op, 5, cl), V3.bucketize(bb, vw, op, 15, cl)
    out = []
    for ev in V3.break_events(b5, b15):
        px = b5[ev[2]]["c"] if ev[1] == "5x3" else b15[ev[2]]["c"]
        cum = V3.cum_dollar_at(bars, ev[0])
        if px < px_min or cum < d0:
            continue
        liq = V3.event_liq(b5, b15, ev)
        cv = sum(v for m, _o, _h, _l, _c, v in bars if V3.EXT_START <= m < ev[0])
        dh = dhl = None
        if liq:
            for need in (False, True):
                rt = V3.retest_signal(b5, b15, ev[0], need_liq=need)
                if rt is None:
                    continue
                rpx = b5[rt[2]]["c"] if rt[1] == "5x3" else b15[rt[2]]["c"]
                ch = pct_change(rpx, prev_adj)
                if px_min <= rpx < px_max and ge(ch, chg_min):
                    if need:
                        dhl = rt[0]
                    else:
                        dh = rt[0]
        out.append((ev[0], ev[1], px, cum, cv, liq, dh, dhl))
    return out


def catalyst4(sym, a, b, wix, s8k, s6k, sec_known):
    """④ في النافذة [a، b]: سلكٌ · 8-K (أو None إن SEC مجهول) · 6-K (وصف) ⟵ C = سلكٌ أو 8-K · ومجهولٌ إن لا سلكَ وSEC مجهول."""
    wire = V3.any_in(wix.get(sym, ()), a, b)
    if sec_known:
        k8, k6 = V3.any_in(s8k, a, b), V3.any_in(s6k, a, b)
    else:
        k8 = k6 = None
    c = True if (wire or k8) else (None if k8 is None else False)
    return {"wire": wire, "sec8k": k8, "sec6k": k6, "C": c}


def tally4(evs, d, prev_adj, rv_of, cat_of, type_status, spac):
    """عدُّ رمزٍ/يومٍ عند درجة d (الملحق 3 §③-④) ⟵ {مفتاح: bool} ‏+ «src» لأوّل FULL ‏+ «cov» لـC123 ‏+ «hist» (أعلى ① وأعلى ② على BASE).
    `rv_of(ev)` ⟵ النسبة أو None · `cat_of(نهاية)` ⟵ catalyst4 · `type_status` ∈ {ok · excluded · unknown} · `spac` bool."""
    elig = [e for e in evs if e[3] >= d]
    out = {k: False for k in KEYS4}
    out["H0"] = bool(elig)
    out["src"], out["cov"], out["hist"], out["type_unknown_c1"], out["c1_any_type"] = None, None, None, False, False
    pxok = [e for e in elig if e[2] < PX_MAX]
    f1_any_type = [e for e in pxok if ge(pct_change(e[2], prev_adj), CHG_MIN)]
    out["c1_any_type"] = bool(f1_any_type)
    if type_status == "unknown":
        out["type_unknown_c1"] = bool(f1_any_type)
    if type_status != "ok" or spac:
        return out
    base = pxok
    out["BASE"] = bool(base)
    rows = []
    for e in base:
        ch = pct_change(e[2], prev_adj)
        rv = rv_of(e)
        rows.append((e, ch, rv, e[5], cat_of(e[0])))
    f1 = lambda r: ge(r[1], CHG_MIN)                                          # noqa: E731
    f2 = lambda r, t=RVOL_MIN: ge(r[2], t)                                    # noqa: E731
    f4 = lambda r: r[4]["C"] is True                                          # noqa: E731
    out["C1"] = any(f1(r) for r in rows)
    out["C2"] = any(f2(r) for r in rows)
    out["C2b"] = any(f2(r, RVOL_PROBE) for r in rows)
    out["C3"] = any(r[3] for r in rows)
    out["C4"] = any(f4(r) for r in rows)
    out["C12"] = any(f1(r) and f2(r) for r in rows)
    c123 = [r for r in rows if f1(r) and f2(r) and r[3]]
    out["C123"] = bool(c123)
    full = next((r for r in rows if f1(r) and f2(r) and r[3] and f4(r)), None)
    out["FULL"] = full is not None
    out["FULL5"] = any(f1(r) and f2(r, RVOL_PROBE) and r[3] and f4(r) for r in rows)
    if full is not None:
        out["DH"], out["DHL"] = full[0][6] is not None, full[0][7] is not None
        out["src"] = "both" if (full[4]["wire"] and full[4]["sec8k"]) else ("wire" if full[4]["wire"] else "sec8k")
    out["U1"] = bool(rows) and not out["C1"] and any(r[1] is None for r in rows)
    u2 = any(f1(r) and r[2] is None and r[3] and f4(r) for r in rows)
    out["U2"] = (not out["FULL"]) and u2
    out["FULL_rv_unknown_as_pass"] = out["FULL"] or u2
    out["U4"] = (not out["FULL"]) and any(f1(r) and f2(r) and r[3] and r[4]["C"] is None for r in c123)
    if c123:
        w = any(r[4]["wire"] for r in c123)
        k8 = any(r[4]["sec8k"] for r in c123)
        k6 = any(r[4]["sec6k"] for r in c123)
        out["cov"] = "both" if (w and k8) else ("wire" if w else ("sec8k" if k8 else ("sec6k_only" if k6 else "none")))
    if rows:
        chs = [r[1] for r in rows if r[1] is not None]
        rvs = [r[2] for r in rows if r[2] is not None]
        out["hist"] = (max(chs) * 100.0 if chs else None, max(rvs) if rvs else None)
    return out


def coverage_gates4(news_meta, idx_missing, sec_unknown, sec_denom, days_missing, prev_missing, ref_ok, type_unknown, type_denom):
    """الحارسُ (الملحق 3 §④) ⟵ (يصلح؟، [أسباب])."""
    why = []
    if not news_meta.get("complete"):
        why.append("news_incomplete")
    if idx_missing:
        why.append("edgar_index_missing")
    if sec_denom and sec_unknown / sec_denom > V3.UNKNOWN_MAX:
        why.append("sec_unknown_over_5pct")
    if days_missing:
        why.append("minute_day_missing")
    if prev_missing:
        why.append("prev_close_missing")
    if not ref_ok:
        why.append("reference_incomplete")
    if type_denom and type_unknown / type_denom > TYPE_UNKNOWN_MAX:
        why.append("type_unknown_over_5pct")
    return (not why), why


def verdict4(gates_ok, pick):
    """«لا قياس» · «اختارت» · أو «إغلاقٌ نهائيّ» (الملحق 3 §④ — لا ملحقَ بعده)."""
    if not gates_ok:
        return "no_measure"
    return "pick" if pick is not None else "final_close"


def addendum_ok(path=ADD3_FILE, pin=None):
    """بصمةُ الملحق 3 تطابق المثبَّتة؟"""
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest() == (pin or ADD3_SHA)
    except OSError:
        return False


# ── الشبكة (رنر فقط) ──────────────────────────────────────────────────────────
def _prev_sessions(day, n, MC):
    out, d = [], dt.date.fromisoformat(day)
    while len(out) < n:
        d -= dt.timedelta(1)
        if V3.is_session(d.isoformat(), MC.session_info):
            out.append(d.isoformat())
    return out[::-1]


def fetch_news4(key, a_iso, b_iso, cap=V3.NEWS_PAGE_CAP):
    """كـ`fetch_news` في v3 ويحفظ الناشرَ والكاتبَ والرابط (للأسلاك)."""
    from urllib.parse import urlencode
    url = "https://api.polygon.io/v2/reference/news?" + urlencode(
        {"published_utc.gte": a_iso, "published_utc.lte": b_iso, "order": "asc", "sort": "published_utc", "limit": 1000})
    out, pages = [], 0
    while url:
        if pages >= cap:
            return out, {"pages": pages, "complete": False, "items": len(out), "why": "cap"}
        j = V3._get_url(url, key)
        if j is None:
            return out, {"pages": pages, "complete": False, "items": len(out), "why": "page_failed"}
        pages += 1
        for it in j.get("results") or []:
            pub = it.get("publisher") or {}
            out.append({"id": it.get("id"), "published_utc": it.get("published_utc"), "tickers": it.get("tickers") or [],
                        "publisher": {"name": pub.get("name") if isinstance(pub, dict) else pub},
                        "author": it.get("author"), "article_url": it.get("article_url")})
        url = j.get("next_url")
    return out, {"pages": pages, "complete": True, "items": len(out), "why": None}


def _paged_all(key, path, params, cap=100):
    """كلُّ صفحات نداءٍ مرجعيّ ⟵ (نتائج، مكتمل؟)."""
    from urllib.parse import urlencode
    url = "https://api.polygon.io" + path + "?" + urlencode(params)
    out, pages = [], 0
    while url:
        if pages >= cap:
            return out, False
        j = V3._get_url(url, key)
        if j is None:
            return out, False
        pages += 1
        out.extend(j.get("results") or [])
        url = j.get("next_url")
    return out, True


def main():
    """v4 (الملحق 3): الحارسُ ⟵ بصمةُ الملحق ⟵ المرجع (تقسيمات · إغلاقٌ سابق · أنواع) ⟵ ملفّاتُ الدقيقة لـ20 جلسةً قبل الشهر ثمّ الشهر
    (نافذةٌ متدحرجة لـ②) ⟵ الأخبار ⟵ SEC (فهارس ⟵ submissions: 8-K/6-K · SIC) ⟵ العدّ ⟵ الوسيط ⟵ الحارس ⟵ القاعدة ⟵ الحكم."""
    if V3._closed_now():
        for _ln in V3.closure_notice():
            log(_ln)
        return V3.CLOSED_RC
    if not addendum_ok():
        log(f"⛔ بصمةُ {ADD3_FILE} لا تطابق المثبَّتة — العقدُ تغيّر بعد التثبيت (الملحق 3 مدموجٌ قبل أيّ رقم)")
        return SHA_RC
    key = os.environ.get("POLYGON_API_KEY", "")
    ua = (os.environ.get("SEC_CONTACT") or "").strip()
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    if not ua:
        log("⛔ SEC_CONTACT غيرُ مضبوط — عطبُ إعداد (④: 8-K مصدرٌ لازم)")
        return 2
    import flatfiles_probe as FP
    import market_calendar as MC
    from prelink_px import PX_MIN
    t0 = time.time()
    month = os.environ.get("VWM_MONTH", "2026-09")
    y, mo = int(month[:4]), int(month[5:7])
    days = [d.isoformat() for d in (dt.date(y, mo, 1) + dt.timedelta(k) for k in range(31))
            if d.month == mo and V3.is_session(d.isoformat(), MC.session_info)]
    prior = _prev_sessions(days[0], RVOL_WIN, MC)
    all_days = prior + days
    prev_of = {d: V3._prev_session(d, MC) for d in days}
    win_a = {d: dt.datetime.combine(dt.date.fromisoformat(prev_of[d]), dt.time(16, 0), tzinfo=V3.NY).timestamp() for d in days}
    d0 = V3.D_LADDER[0]
    res = {"version": "v4-addendum-3", "month": month, "px_min": PX_MIN, "px_max": PX_MAX, "chg_min": CHG_MIN, "rvol_min": RVOL_MIN,
           "rvol_probe": RVOL_PROBE, "rvol_win": RVOL_WIN, "rvol_min_present": RVOL_MIN_PRESENT, "types_ok": TYPES_OK,
           "spac_sic": SPAC_SIC, "sec_forms": SEC_FORMS4, "wires": sorted({w[1] for w in WIRES}),
           "d_ladder": V3.D_LADDER, "d_rule": V3.D_RULE, "prior_sessions": [prior[0], prior[-1]], "add3_sha": ADD3_SHA}
    log(f"📅 {month}: {len(days)} جلسة · قبلها {len(prior)} ({prior[0]} ⟵ {prior[-1]}) · ① ≥{CHG_MIN:.0%} · ② ≥{RVOL_MIN} (مِجَسّ {RVOL_PROBE}) · "
        f"⑤ [{PX_MIN}، {PX_MAX}) {TYPES_OK} · السلّم {V3.D_LADDER} · القاعدة {V3.D_RULE}")
    # ⓪ المرجع
    sp_rows, sp_ok = _paged_all(key, "/v3/reference/splits",
                                {"execution_date.gte": all_days[0], "execution_date.lte": days[-1], "limit": 1000})
    splits = {}
    for r in sp_rows:
        t = str(r.get("ticker") or "").upper()
        try:
            splits.setdefault(t, []).append((str(r["execution_date"]), float(r["split_from"]), float(r["split_to"])))
        except (KeyError, TypeError, ValueError):
            continue
    prev_close, prev_missing = {}, []
    for d in days:
        j = V3._poly(f"/v2/aggs/grouped/locale/us/market/stocks/{prev_of[d]}", key, {"adjusted": "false"})
        if not j or not j.get("results"):
            prev_missing.append(prev_of[d])
            continue
        prev_close[d] = {str(r.get("T") or "").upper(): r.get("c") for r in j["results"] if r.get("T")}
    types, ref_ok = {}, sp_ok
    for asof in (days[0], days[-1]):
        rows, okr = _paged_all(key, "/v3/reference/tickers", {"market": "stocks", "date": asof, "active": "true", "limit": 1000})
        ref_ok = ref_ok and okr
        for r in rows:
            t = str(r.get("ticker") or "").upper()
            if t and r.get("type") and t not in types:
                types[t] = str(r["type"])
    log(f"⓪ المرجع: تقسيمات {len(sp_rows)} (مكتمل {sp_ok}) · إغلاقٌ سابق {len(prev_close)} من {len(days)} (ناقص {prev_missing}) · أنواع {len(types)} (مكتمل {ref_ok})")
    # ① ملفّاتُ الدقيقة — نافذةٌ متدحرجة
    tmp = tempfile.mkdtemp(prefix="vwm4_")
    window = deque()                                       # [(يوم، {رمز: منحنى})]
    store, days_missing, nsyms = {}, [], {}
    for day in all_days:
        path = os.path.join(tmp, "d.csv.gz")
        okx, _ = V3._download(FP, V3._key(V3.MIN_PREFIX, day), path)
        if not okx:
            days_missing.append(day)
            window.append((day, {}))
            if len(window) > RVOL_WIN:
                window.popleft()
            continue
        mins = V3._read_minutes(path)
        os.remove(path)
        if day in prev_of:
            info = MC.session_info(day)
            op, cl = info["open_ny_min"], info["close_ny_min"]
            pc = prev_close.get(day, {})
            ds = {}
            for sym, bars in mins.items():
                sp = splits.get(sym, ())
                pv = pc.get(sym)
                prev_adj = pv * price_factor(sp, day) if pv else None
                evs = v4_events(bars, op, cl, PX_MIN, d0, prev_adj)
                if not evs:
                    continue
                rvs = []
                for e in evs:
                    if e[2] >= PX_MAX:
                        rvs.append(None)
                        continue
                    pri = []
                    for pdy, curves in window:
                        cv = curves.get(sym)
                        pri.append((cv is not None, curve_at(cv, e[0]) * vol_factor(sp, pdy, day)))
                    rvs.append(rvol(e[4], pri))
                ds[sym] = (prev_adj, evs, rvs)
            store[day], nsyms[day] = ds, len(mins)
            log(f"① {day}: رموز {len(mins)} · بأحداث A {len(ds)} · النافذة {len(window)} جلسة")
        window.append((day, {s: cum_curve(b) for s, b in mins.items()}))
        if len(window) > RVOL_WIN:
            window.popleft()
        del mins
    window.clear()
    ok_days = [d for d in days if d in store]
    # ② الأخبار
    p0 = prev_of[days[0]]
    a_iso = dt.datetime.combine(dt.date.fromisoformat(p0), dt.time(16, 0), tzinfo=V3.NY).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    b_iso = dt.datetime.combine(dt.date.fromisoformat(days[-1]), dt.time(20, 0), tzinfo=V3.NY).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    items, nmeta = fetch_news4(key, a_iso, b_iso)
    wix, by_wire, by_field, pubs = wire_index(items)
    nmeta.update({"from": a_iso, "to": b_iso, "wire_items": by_wire, "wire_fields": by_field, "wire_symbols": len(wix),
                  "top_publishers": dict(sorted(pubs.items(), key=lambda x: -x[1])[:15])})
    del items
    log(f"② الأخبار: {nmeta['items']} في {nmeta['pages']} صفحة · مكتمل={nmeta['complete']} · الأسلاك {by_wire} · رموزٌ بسلك {len(wix)}")
    # ③ SEC
    cmap = V3._sec_get("https://www.sec.gov/files/company_tickers.json", ua, True) or {}
    tmap = {str(v.get("ticker", "")).upper(): int(v["cik_str"]) for v in cmap.values() if isinstance(v, dict) and v.get("cik_str")}
    filers, idx_missing = set(), ([] if tmap else ["company_tickers"])
    for d in [p0] + days:
        dd = dt.date.fromisoformat(d)
        url = (f"https://www.sec.gov/Archives/edgar/daily-index/{dd.year}/QTR{(dd.month - 1) // 3 + 1}/"
               f"master.{dd.strftime('%Y%m%d')}.idx")
        text = V3._sec_get(url, ua, False)
        if text is None:
            idx_missing.append(d)
            continue
        filers |= V3.parse_master_idx(text, SEC_FETCH)
    base_syms, c1_syms = set(), set()
    for d in ok_days:
        for sym, (pa, evs, _r) in store[d].items():
            if any(e[2] < PX_MAX for e in evs):
                base_syms.add(sym)
                if any(e[2] < PX_MAX and ge(pct_change(e[2], pa), CHG_MIN) for e in evs):
                    c1_syms.add(sym)
    miss_t = sorted(s for s in c1_syms if s not in types)[:DETAIL_CAP]
    for s in miss_t:
        j = V3._poly(f"/v3/reference/tickers/{s}", key, {"date": days[-1]})
        t = ((j or {}).get("results") or {}).get("type")
        if t:
            types[s] = str(t)
    need = sorted({tmap[s] for s in base_syms if s in tmap and tmap[s] in filers} | {tmap[s] for s in c1_syms if s in tmap})
    from edgar2_probe import parse_acc, to_ny
    acc_ts = V3.make_acc_ts(parse_acc, to_ny)
    s8k, s6k, sic, sec_unknown = {}, {}, {}, set()
    for cik in need:
        j = V3._sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", ua, True)
        if j is None:
            sec_unknown.add(cik)
            continue
        sic[cik] = str(j.get("sic") or "")
        rec = (j.get("filings") or {}).get("recent") or {}
        if not V3.sec_depth_ok(rec, bool((j.get("filings") or {}).get("files")), p0):
            sec_unknown.add(cik)
            continue
        rows = V3.sec_index(rec, SEC_FETCH, acc_ts)
        s8k[cik] = [r[0] for r in rows if r[1] == "8-K"]
        s6k[cik] = [r[0] for r in rows if r[1] == "6-K"]
    log(f"③ SEC: خريطة {len(tmap)} · مودِعو {SEC_FETCH} {len(filers)} · submissions {len(need)} · مجهول {len(sec_unknown)} · "
        f"فهارسُ ناقصة {idx_missing} · أنواعٌ بالتفاصيل {len(miss_t)}")
    # ④ العدّ
    per_day = {}
    hist_c, hist_r, cross = {}, {}, {}
    cov = {k: 0 for k in ("both", "wire", "sec8k", "sec6k_only", "none")}
    src_full = {"wire": 0, "sec8k": 0, "both": 0}
    gate = {"sec_unknown": 0, "sec_denom": 0, "type_unknown": 0, "type_denom": 0, "nocik_c123": 0, "spac_c1": 0, "type_excl_c1": 0}
    for day in ok_days:
        cnt = {(d, k): 0 for d in V3.D_LADDER for k in KEYS4}
        for sym, (pa, evs, rvs) in store[day].items():
            tstat = "unknown" if sym not in types else ("ok" if types[sym] in TYPES_OK else "excluded")
            cik = tmap.get(sym)
            spac = cik is not None and sic.get(cik) == SPAC_SIC
            if cik is None or cik not in filers:             # كالملحق 2: لم يُودِع في المدى ⟵ صفرٌ معلوم (وجلبُه للـSIC وحدَه)
                k8l, k6l, known = (), (), True
            else:
                k8l, k6l, known = s8k.get(cik, ()), s6k.get(cik, ()), cik not in sec_unknown
            rvmap = {e: r for e, r in zip(evs, rvs)}

            def cat_of(e_end, sym=sym, k8l=k8l, k6l=k6l, known=known):
                return catalyst4(sym, win_a[day], V3.ny_ts(day, e_end), wix, k8l, k6l, known)
            for d in V3.D_LADDER:
                t = tally4(evs, d, pa, lambda e: rvmap.get(e), cat_of, tstat, spac)
                for k in KEYS4:
                    cnt[(d, k)] += int(bool(t[k]))
                if d != d0:
                    continue
                if t["c1_any_type"]:
                    gate["type_denom"] += 1
                    gate["type_unknown"] += int(t["type_unknown_c1"])
                    gate["spac_c1"] += int(tstat == "ok" and spac)
                    gate["type_excl_c1"] += int(tstat == "excluded")
                if t["C123"]:
                    if cik is None:
                        gate["nocik_c123"] += 1
                    else:
                        gate["sec_denom"] += 1
                        gate["sec_unknown"] += int(cik in sec_unknown and cik in filers)
                    cov[t["cov"]] += 1
                if t["src"]:
                    src_full[t["src"]] += 1
                if t["hist"] is not None:
                    bc, br = bucket(t["hist"][0], CHG_EDGES), bucket(t["hist"][1], RVOL_EDGES)
                    hist_c[bc] = hist_c.get(bc, 0) + 1
                    hist_r[br] = hist_r.get(br, 0) + 1
                    cross[f"{bc}|{br}"] = cross.get(f"{bc}|{br}", 0) + 1
        per_day[day] = {"symbols": nsyms[day], "with_events": len(store[day])}
        for d in V3.D_LADDER:
            per_day[day][f"A@{d}"] = {k: cnt[(d, k)] for k in KEYS4}
        log(f"④ {day}: " + " · ".join(f"{d // 1000}k FULL={per_day[day][f'A@{d}']['FULL']} C1={per_day[day][f'A@{d}']['C1']} "
                                      f"C2={per_day[day][f'A@{d}']['C2']}" for d in V3.D_LADDER))
    med = {d: {k: st.median([per_day[x][f"A@{d}"][k] for x in ok_days] or [0]) for k in KEYS4} for d in V3.D_LADDER}
    tot = {d: {k: sum(per_day[x][f"A@{d}"][k] for x in ok_days) for k in KEYS4} for d in V3.D_LADDER}
    # ⑤ فحصُ الإعادة مقابل H0 في v3
    rep = {"compared": 0, "mismatch": 0, "examples": []}
    try:
        old = json.load(open("vwap_mom_feas_v3_2026-09.json", encoding="utf-8"))
        if old.get("month") == month:
            for d in ok_days:
                for dm in V3.D_LADDER:
                    o = ((old.get("per_day") or {}).get(d) or {}).get(f"A@{dm}", {}).get("H0")
                    v = per_day[d][f"A@{dm}"]["H0"]
                    rep["compared"] += 1
                    if o != v:
                        rep["mismatch"] += 1
                        if len(rep["examples"]) < 10:
                            rep["examples"].append([d, dm, o, v])
    except (OSError, ValueError) as e:
        rep["error"] = type(e).__name__
    log("① الوسيطُ/يوم قبل أيّ اختيار: " + " · ".join(
        f"{d // 1000}k FULL={med[d]['FULL']} (FULL5 {med[d]['FULL5']}) C1={med[d]['C1']} C2={med[d]['C2']} C12={med[d]['C12']} "
        f"C123={med[d]['C123']} BASE={med[d]['BASE']}" for d in V3.D_LADDER))
    ok, why = coverage_gates4(nmeta, idx_missing, gate["sec_unknown"], gate["sec_denom"], days_missing, prev_missing, ref_ok,
                              gate["type_unknown"], gate["type_denom"])
    pick = V3.pick_rule({d: med[d]["FULL"] for d in V3.D_LADDER}, V3.D_LADDER, *V3.D_RULE) if ok else None
    verdict = verdict4(ok, pick)
    res.update({"median_by_dmin": med, "month_totals": tot, "per_day": per_day, "news": nmeta,
                "sec": {"tickers_mapped": len(tmap), "filers": len(filers), "index_missing": idx_missing, "need": len(need),
                        "unknown_ciks": len(sec_unknown), "spac_ciks": sum(1 for v in sic.values() if v == SPAC_SIC)},
                "reference": {"splits": len(sp_rows), "splits_complete": sp_ok, "prev_close_days": len(prev_close),
                              "prev_missing": prev_missing, "types": len(types), "types_complete": ref_ok, "type_details": len(miss_t)},
                "gate_counts": gate, "coverage_C123_lowest": cov, "src_FULL_lowest": src_full,
                "hist_chg_lowest": hist_c, "hist_rvol_lowest": hist_r, "cross_lowest": cross,
                "replay_v3_H0": rep, "days_missing": days_missing, "gates_ok": ok, "gates_why": why,
                "rule_applied": ok, "D_MIN_pick_by_rule": pick, "verdict": verdict})
    log(f"⑤ فحصُ الإعادة مقابل H0 في v3: {rep['mismatch']} فرقًا من {rep['compared']}")
    log(f"⑥ الحارس: {'يصلح' if ok else 'لا قياس ' + str(why)} · قاعدةُ الملحق 3 على FULL ⟵ D_MIN = {pick} · الحكم: {verdict}")
    res["seconds"] = round(time.time() - t0, 1)
    print("VWMFEAS4_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
