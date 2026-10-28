"""📈🔎 جدوى `T-VWAP-MOM` — «زخم الفيواب» (العقد `vwap_mom_prereg.md` §⑧ ‏+ **الملحق 1** `vwap_mom_prereg_addendum_1.md` · كلاهما قبل أيّ عائد).

**عدٌّ لا عائد:** لا يحسب هذا الملفُّ R ولا عائدًا ولا قمّةً لاحقة — مقفولٌ في السويّة (`VWM2`).
**v2 (الملحق 1):** H = **كسرٌ صاعدٌ للفيواب** (إغلاقُ 5 دقائق تحته ثمّ أوّلُ إغلاقٍ فوقه ثمّ 3 إغلاقاتٍ متتالية فوقه أو شمعة 15 دقيقة) ·
والمجتمع = **أحداثُ الكسر على الكون كلّه** بسعرٍ ≥ `PX_MIN` وحجمٍ دولاريٍّ تراكميّ حتى لحظة الحدث ≥ درجةِ `D_MIN` · والذراع E محذوفةٌ بأمر المالك.
الأسئلة: ① لكلّ يومٍ وكلّ درجة: أحداثُ A (النظاميّة) وB (الممتدّة) · H وH ∧ L ⟵ الوسيطُ/يوم مطبوعًا **قبل** أيّ اختيار ⟵ قاعدةُ §③.
② تغطيةُ المحفّز C في Polygon news على عيّنةٍ مُعلَنة من أحداث A عند أدنى درجة.
بلا تلغرام · بلا حالة · بلا كتابةٍ في المستودع. والمُخرَجُ سطرُ `VWMFEAS_JSON`. ونتيجةُ v1 (أعلى 20 رابحًا) في `vwap_mom_feas_result.md` ودوالُّها باقيةٌ للإعادة.
"""
import csv
import datetime as dt
import gzip
import heapq
import json
import os
import random
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
        log(f"   ⛔ تعذّر التنزيل ({i + 1}/{tries}): {key} · {(err or '')[:140]}")
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


def main():
    import flatfiles_probe as FP
    import market_calendar as MC
    from prelink_px import PX_MIN
    key = os.environ.get("POLYGON_API_KEY", "")
    month = os.environ.get("VWM_MONTH", "2026-09")
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    t0 = time.time()
    res = {"version": "v2-addendum-1", "month": month, "px_min": PX_MIN, "d_ladder": D_LADDER, "d_rule": D_RULE}
    y, mo = int(month[:4]), int(month[5:7])
    days = [d.isoformat() for d in (dt.date(y, mo, 1) + dt.timedelta(k) for k in range(31))
            if d.month == mo and is_session(d.isoformat(), MC.session_info)]
    log(f"📅 {month}: {len(days)} جلسة · PX_MIN={PX_MIN} · السلّم {D_LADDER} · القاعدة {D_RULE}")
    tmp = tempfile.mkdtemp(prefix="vwm2_")
    per_day, c_pool = {}, []
    for day in days:
        info = MC.session_info(day)
        op, cl = info["open_ny_min"], info["close_ny_min"]
        path = os.path.join(tmp, "d.csv.gz")
        okx, _ = _download(FP, _key(MIN_PREFIX, day), path)
        if not okx:
            per_day[day] = {"error": "download"}
            continue
        mins = _read_minutes(path)
        os.remove(path)
        row = {"symbols": len(mins)}
        cnt = {(arm, d, k): 0 for arm in "AB" for d in D_LADDER for k in ("H", "HL")}
        for sym, bars in mins.items():
            ev = day_events(bars, op, cl, D_LADDER, PX_MIN)
            for (arm, d), v in ev.items():
                cnt[(arm, d, "H")] += v["H"] is not None
                cnt[(arm, d, "HL")] += v["HL"] is not None
            a0 = ev[("A", D_LADDER[0])]["H"]
            if a0 is not None:
                c_pool.append((day, sym, a0[0]))
        for arm in "AB":
            for d in D_LADDER:
                row[f"{arm}@{d}"] = {"H": cnt[(arm, d, "H")], "HL": cnt[(arm, d, "HL")]}
        per_day[day] = row
        log(f"① {day}: " + " · ".join(f"{d // 1000}k A={row[f'A@{d}']['H']}/{row[f'A@{d}']['HL']} B={row[f'B@{d}']['H']}/{row[f'B@{d}']['HL']}"
                                      for d in D_LADDER) + f" · رموز {len(mins)}")
        del mins
    ok_days = [x for x in per_day if "error" not in per_day[x]]
    med = {arm: {d: {k: st.median([per_day[x][f"{arm}@{d}"][k] for x in ok_days] or [0]) for k in ("H", "HL")} for d in D_LADDER}
           for arm in "AB"}
    res["median_by_dmin"] = med
    log("① الوسيطُ/يوم قبل أيّ اختيار: " + " · ".join(f"{d // 1000}k A H={med['A'][d]['H']} HL={med['A'][d]['HL']} "
                                                       f"B H={med['B'][d]['H']} HL={med['B'][d]['HL']}" for d in D_LADDER))
    d_pick = pick_rule({d: med["A"][d]["H"] for d in D_LADDER}, D_LADDER, *D_RULE)
    res["D_MIN_pick_by_rule"] = d_pick
    log(f"① قاعدةُ §③ (وسيطُ أحداث A/يوم بين {D_RULE[0]} و{D_RULE[1]}) ⟵ D_MIN = {d_pick}")
    res["per_day"] = per_day
    # ② تغطيةُ C (عيّنةٌ مُعلَنة من أحداث A عند أدنى درجة)
    rnd = random.Random(20261028)
    samp = rnd.sample(c_pool, min(C_SAMPLE, len(c_pool)))
    hits = calls = 0
    for day, s, m0 in samp:
        pdx = dt.date.fromisoformat(day) - dt.timedelta(1)
        while not is_session(pdx.isoformat(), MC.session_info):
            pdx -= dt.timedelta(1)
        a = dt.datetime.combine(pdx, dt.time(16, 0), tzinfo=NY).astimezone(dt.timezone.utc)
        b = dt.datetime.combine(dt.date.fromisoformat(day), dt.time(m0 // 60, m0 % 60), tzinfo=NY).astimezone(dt.timezone.utc)
        j = _poly("/v2/reference/news", key, {"ticker": s, "published_utc.gte": a.strftime("%Y-%m-%dT%H:%M:%SZ"),
                                              "published_utc.lte": b.strftime("%Y-%m-%dT%H:%M:%SZ"), "limit": 10})
        calls += 1
        hits += bool(j and j.get("results"))
    res["C_coverage"] = {"rung": D_LADDER[0], "pool": len(c_pool), "sample": len(samp), "with_news": hits, "calls": calls}
    log(f"② C: خبرٌ في النافذة {hits} من {len(samp)} (من {len(c_pool)} حدثَ A عند {D_LADDER[0] // 1000}k)")
    res["seconds"] = round(time.time() - t0, 1)
    print("VWMFEAS_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
