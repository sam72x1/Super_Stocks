"""📈🔎 جدوى `T-VWAP-MOM` — «زخم الفيواب» (العقد `vwap_mom_prereg.md` §⑧ · مدموجٌ قبل أيّ رقم).

**عدٌّ لا عائد:** لا يحسب هذا الملفُّ R ولا عائدًا ولا قمّةً لاحقة — مقفولٌ في السويّة (`VWM2`).
الأسئلة بترتيب العقد:
  ① ملفّاتُ الدقيقة المجمَّعة (S3) مقروءةٌ الآن؟ كم يومًا متاحًا 2023-2025؟ وهل تحمل رموزًا غائبةً عن قائمة النشطة اليوم؟
  ② لكلّ يومٍ من الشهر: كم رمزًا دخل U (أعلى 20 رابحًا لحظيًّا) عند كلّ `D_MIN` في السلّم ⟵ تثبيتُ `D_MIN` بقاعدة §③.
  ③ كم رمزًا/يومًا يعبر H ثمّ H ∧ L (النظاميّة A · والممتدّة B) عند `D_MIN` المختار.
  ④ تغطيةُ المحفّز C في Polygon news (عيّنةٌ مُعلَنة).
  ⑤ كلفةُ E: مجتمعُ RSI دون 30 · ونداءاتُ `/v3/quotes` ليومٍ · والإشاراتُ/يوم عند كلّ `E_RATIO` ⟵ تثبيتُه بقاعدة §④.
بلا تلغرام · بلا حالة · بلا كتابةٍ في المستودع. والمُخرَجُ سطرُ `VWMFEAS_JSON`.
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
DAY_PREFIX = "us_stocks_sip/day_aggs_v1"
TOP_N = 20                                         # «Polygon snapshot gainers» — أعلى 20 (العقد §③)
D_LADDER = (250_000, 500_000, 1_000_000, 2_000_000, 5_000_000)   # §③ — مكتوبٌ قبل الرقم
D_RULE = (10, 40)                                  # وسيطُ المرشّحين الجدد/يوم بينهما
E_LADDER = (5, 10, 20, 50)                         # §④
E_RULE = (5, 30)
RSI_MAX = 30.0
EXT_START = 4 * 60                                 # 04:00 نيويورك
EXT_END = 20 * 60                                  # 20:00 نيويورك
PRE_END_E = 9 * 60 + 25                            # نافذةُ E: 04:00–09:25
C_SAMPLE = 60
E_DAYS_SAMPLE = 3
E_SYMS_SAMPLE = 25


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


def first_signal(b5, b15, after_mod, need_liq=True):
    """أوّلُ اكتمالٍ لـH (‏3×5د فوق VWAP أو 15د فوقه) ‏[∧ L] **نهايتُه ≥ after_mod** ⟵ (نهايةُ الاكتمال، النوع) أو None."""
    cands = []
    for i in range(2, len(b5)):
        if all(b5[k]["vwap"] is not None and b5[k]["c"] > b5[k]["vwap"] for k in (i - 2, i - 1, i)):
            if b5[i]["e"] >= after_mod and (not need_liq or liq_ok(b5, i)):
                cands.append((b5[i]["e"], "5x3"))
                break
    for j in range(len(b15)):
        if b15[j]["vwap"] is not None and b15[j]["c"] > b15[j]["vwap"]:
            if b15[j]["e"] >= after_mod and (not need_liq or liq15_ok(b15, j)):
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


def rsi14(closes):
    """RSI14 بطريقة وايلدر على قائمة إغلاقات ⟵ آخرُ قيمة أو None (أقلّ من 15 إغلاقًا)."""
    if len(closes) < 15:
        return None
    gains = [max(closes[i] - closes[i - 1], 0.0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0.0) for i in range(1, len(closes))]
    ag, al = sum(gains[:14]) / 14.0, sum(losses[:14]) / 14.0
    for g, lo in zip(gains[14:], losses[14:]):
        ag, al = (ag * 13 + g) / 14.0, (al * 13 + lo) / 14.0
    if al == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + ag / al)


def book_signal(quotes, ratio):
    """أوّلُ اقتباسٍ (ns, bid_size, ask_size) بنسبة طلب÷عرض ≥ ratio (والعرضُ موجب) ⟵ طابعُه أو None."""
    for t, bs, as_ in quotes:
        if as_ and as_ > 0 and bs is not None and bs / as_ >= ratio:
            return t
    return None


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
            sig = first_signal(b5, b15, m0, need_liq=need)
            ok = sig is not None and not (op < sig[0] <= cl)
            if attr == "h":
                hB += ok
            else:
                hlB += ok
    return hA, hlA, hB, hlB


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


def _read_day_closes(path):
    out = {}
    with gzip.open(path, "rt") as fh:
        rd = csv.reader(fh)
        hd = [h.strip().lower() for h in next(rd)]
        it, ic = hd.index("ticker"), hd.index("close")
        for r in rd:
            try:
                out[r[it].strip().upper()] = float(r[ic])
            except (ValueError, IndexError):
                continue
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
    res = {"month": month, "px_min": PX_MIN, "d_ladder": D_LADDER, "e_ladder": E_LADDER}
    y, mo = int(month[:4]), int(month[5:7])
    days = [d.isoformat() for d in (dt.date(y, mo, 1) + dt.timedelta(k) for k in range(31))
            if d.month == mo and is_session(d.isoformat(), MC.session_info)]
    # الجلسةُ السابقة لأوّل يوم (لإغلاقٍ سابق)
    p = dt.date.fromisoformat(days[0]) - dt.timedelta(1)
    while not is_session(p.isoformat(), MC.session_info):
        p -= dt.timedelta(1)
    prev_day = p.isoformat()
    log(f"📅 {month}: {len(days)} جلسة · السابقة {prev_day} · PX_MIN={PX_MIN}")

    # ① التوفّر 2023-2025 (head-object على كلّ جلسة) ‏+ الرموزُ المشطوبة
    from concurrent.futures import ThreadPoolExecutor
    avail = {}
    for yy in (2023, 2024, 2025):
        sess = []
        d = dt.date(yy, 1, 1)
        while d.year == yy:
            if is_session(d.isoformat(), MC.session_info):
                sess.append(d.isoformat())
            d += dt.timedelta(1)
        with ThreadPoolExecutor(8) as ex:
            got = list(ex.map(lambda x: _head(FP, _key(MIN_PREFIX, x)), sess))
        miss = [x for x, g in zip(sess, got) if g is None]
        avail[yy] = {"sessions": len(sess), "files": len(sess) - len(miss), "missing": miss[:20]}
        log(f"① {yy}: ملفّاتُ الدقيقة {len(sess) - len(miss)} من {len(sess)} جلسة" + (f" · الغائب {miss[:6]}" if miss else ""))
    res["availability"] = avail
    tmp = tempfile.mkdtemp(prefix="vwm_")
    sample_day = "2023-03-01"
    act, act_calls = _paged(_poly("/v3/reference/tickers", key, {"market": "stocks", "active": "true", "limit": 1000}) or {}, key)
    active = {str(r.get("ticker", "")).upper() for r in act}
    okd, _ = _download(FP, _key(MIN_PREFIX, sample_day), os.path.join(tmp, "s.csv.gz"))
    if okd and active:
        syms = set(_read_minutes(os.path.join(tmp, "s.csv.gz")))
        gone = sorted(syms - active)
        res["delisted_check"] = {"day": sample_day, "tickers_in_file": len(syms), "active_now": len(active),
                                 "not_active_now": len(gone), "examples": gone[:15], "active_calls": act_calls}
        log(f"① {sample_day}: رموزُ الملفّ {len(syms)} · غيرُ نشطةٍ اليوم {len(gone)} (أمثلة: {gone[:8]})")
        os.remove(os.path.join(tmp, "s.csv.gz"))
    else:
        res["delisted_check"] = {"day": sample_day, "error": "download or active list failed", "active_now": len(active)}

    # ② ③ اليومُ بيومه
    okp, _ = _download(FP, _key(MIN_PREFIX, prev_day), os.path.join(tmp, "p.csv.gz"))
    if not okp:
        log("⛔ تعذّر ملفُّ الجلسة السابقة — لا ②")
        print("VWMFEAS_JSON " + json.dumps(res, ensure_ascii=False))
        return 3
    pm = _read_minutes(os.path.join(tmp, "p.csv.gz"))
    pinfo = MC.session_info(prev_day)
    prev_close = {s: next((b[4] for b in reversed(v) if pinfo["open_ny_min"] <= b[0] < pinfo["close_ny_min"]), None)
                  for s, v in pm.items()}
    prev_close = {s: c for s, c in prev_close.items() if c}
    per_day = {}
    c_pool = {}
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
        sp = _poly("/v3/reference/splits", key, {"execution_date": day, "limit": 1000}) or {}
        pc = dict(prev_close)
        nsplit = 0
        for r in sp.get("results") or []:
            s = str(r.get("ticker", "")).upper()
            f, t = r.get("split_from"), r.get("split_to")
            if s in pc and f and t:
                pc[s] = pc[s] * float(f) / float(t)
                nsplit += 1
        bymin = {}
        for s, v in mins.items():
            for m, o, h, l, c, vol in v:
                if EXT_START <= m < EXT_END:
                    bymin.setdefault(m, []).append((s, c, c * vol))
        reg_w, ext_w = [(op, cl)], [(EXT_START, op), (cl, EXT_END)]
        row = {"splits_adjusted": nsplit, "symbols": len(mins)}
        for d_min in D_LADDER:
            ent_reg = gainer_entries(bymin, pc, d_min, PX_MIN, reg_w)
            ent_ext = gainer_entries(bymin, pc, d_min, PX_MIN, ext_w)
            row[f"U_reg@{d_min}"] = len(ent_reg)
            hA, hlA, hB, hlB = count_signals(mins, ent_reg, ent_ext, op, cl)
            row[f"A@{d_min}"] = {"U": len(ent_reg), "H": hA, "HL": hlA}
            row[f"B@{d_min}"] = {"U": len(ent_ext), "H": hB, "HL": hlB}
            c_pool.setdefault(d_min, []).extend((day, s_, m_) for s_, m_ in ent_reg.items())
        per_day[day] = row
        log(f"② {day}: " + " · ".join(f"{d // 1000}k U={row[f'U_reg@{d}']} H∧L={row[f'A@{d}']['HL']}" for d in D_LADDER)
            + f" · تقسيمات {nsplit}")
        # الإغلاقُ السابق لليوم التالي = آخرُ دقيقةٍ نظاميّة اليوم
        prev_close = {s: next((b[4] for b in reversed(v) if op <= b[0] < cl), None) for s, v in mins.items()}
        prev_close = {s: c for s, c in prev_close.items() if c}
        del mins, bymin
    meds = {d: st.median([per_day[x][f"U_reg@{d}"] for x in per_day if f"U_reg@{d}" in per_day[x]] or [0]) for d in D_LADDER}
    d_pick = pick_rule(meds, D_LADDER, *D_RULE)
    res["U_median_by_dmin"] = meds
    res["D_MIN_pick"] = d_pick
    log(f"② وسيطُ المرشّحين الجدد/يوم: {meds} ⟵ D_MIN = {d_pick}")
    # ③ H و H∧L عند D_MIN المختار (A نظاميّة · B ممتدّة) — من العدّ اليوميّ أعلاه
    if d_pick is not None:
        for arm in ("A", "B"):
            vals = [per_day[x][f"{arm}@{d_pick}"] for x in per_day if f"{arm}@{d_pick}" in per_day[x]]
            res[f"{arm}_daily_median"] = {k: st.median([v[k] for v in vals]) for k in ("U", "H", "HL")} if vals else None
            res[f"{arm}_month_total"] = {k: sum(v[k] for v in vals) for k in ("U", "H", "HL")} if vals else None
            log(f"③ {arm} عند D_MIN={d_pick}: وسيطٌ/يوم {res[f'{arm}_daily_median']} · مجموعُ الشهر {res[f'{arm}_month_total']}")
    res["per_day"] = per_day
    # ④ تغطيةُ C (عيّنةٌ مُعلَنة)
    rnd = random.Random(20261028)
    pool_c = c_pool.get(d_pick, []) if d_pick is not None else []
    samp = rnd.sample(pool_c, min(C_SAMPLE, len(pool_c)))
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
    res["C_coverage"] = {"sample": len(samp), "with_news": hits, "calls": calls}
    log(f"④ C: خبرٌ في النافذة {hits} من {len(samp)}")
    # ⑤ E: مجتمعُ RSI دون 30 ونداءاتُ الاقتباس
    closes_by_day = []
    dd = dt.date.fromisoformat(days[0]) - dt.timedelta(1)
    hist_days = []
    while len(hist_days) < 30:
        if is_session(dd.isoformat(), MC.session_info):
            hist_days.append(dd.isoformat())
        dd -= dt.timedelta(1)
    hist_days = sorted(hist_days) + days
    for d in hist_days:
        pth = os.path.join(tmp, "day.csv.gz")
        okk, _ = _download(FP, _key(DAY_PREFIX, d), pth)
        closes_by_day.append((d, _read_day_closes(pth) if okk else {}))
        if okk:
            os.remove(pth)
    e_pop = {}
    for i, (d, _cl) in enumerate(closes_by_day):
        if d not in days:
            continue
        prevs = closes_by_day[max(0, i - 30):i]
        syms = set(prevs[-1][1]) if prevs else set()
        pop = []
        for s in syms:
            seq = [c[s] for _d, c in prevs if s in c]
            r = rsi14(seq)
            if r is not None and r < RSI_MAX and seq[-1] >= PX_MIN:
                pop.append(s)
        e_pop[d] = pop
    res["E_population"] = {d: len(v) for d, v in e_pop.items()}
    log(f"⑤ E: مجتمعُ RSI دون 30/يوم وسيط {st.median([len(v) for v in e_pop.values()] or [0])}")
    e_days = [days[0], days[len(days) // 2], days[-1]][:E_DAYS_SAMPLE]
    e_sig = {r: [] for r in E_LADDER}
    q_calls = 0
    q_t = time.time()
    for d in e_days:
        pop = sorted(e_pop.get(d, []))
        smp = rnd.sample(pop, min(E_SYMS_SAMPLE, len(pop)))
        a = dt.datetime.combine(dt.date.fromisoformat(d), dt.time(4, 0), tzinfo=NY)
        b = dt.datetime.combine(dt.date.fromisoformat(d), dt.time(PRE_END_E // 60, PRE_END_E % 60), tzinfo=NY)
        cnt = {r: 0 for r in E_LADDER}
        for s in smp:
            j = _poly(f"/v3/quotes/{s}", key, {"timestamp.gte": int(a.timestamp() * 1e9),
                                               "timestamp.lt": int(b.timestamp() * 1e9), "limit": 50000, "order": "asc"})
            rows, nc = _paged(j or {}, key, cap=10)
            q_calls += nc
            qs = [(r.get("sip_timestamp"), r.get("bid_size"), r.get("ask_size")) for r in rows]
            for r in E_LADDER:
                cnt[r] += book_signal(qs, r) is not None
        for r in E_LADDER:
            e_sig[r].append(cnt[r] * (len(e_pop.get(d, [])) / max(1, len(smp))))
        log(f"⑤ {d}: عيّنة {len(smp)} من {len(e_pop.get(d, []))} · إشارات " + " · ".join(f"{r}:{cnt[r]}" for r in E_LADDER))
    e_meds = {r: st.median(v) if v else None for r, v in e_sig.items()}
    res["E"] = {"days": e_days, "sample_per_day": E_SYMS_SAMPLE, "quote_calls": q_calls,
                "quote_seconds": round(time.time() - q_t, 1), "signals_per_day_extrapolated": e_meds,
                "E_RATIO_pick": pick_rule(e_meds, E_LADDER, *E_RULE)}
    log(f"⑤ E: نداءاتُ الاقتباس {q_calls} · الإشاراتُ/يوم (مُستقرأة) {e_meds} ⟵ E_RATIO = {res['E']['E_RATIO_pick']}")
    res["seconds"] = round(time.time() - t0, 1)
    print("VWMFEAS_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
