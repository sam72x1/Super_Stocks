"""🧺 `T-BASKET` «السلة» — العقد `T_BASKET_prereg.md` (مدموجٌ قبل أيّ رقم · قراءةٌ فقط · لا إنتاج).

الأوضاع: `BASKET_MODE` = prep · shard (`SHARD`/`NSHARDS`) · assemble.
🔒 الحارس: يخرج 8 ما لم يكن `TRAIL_REOPEN` = "1" حرفيًّا (إقرارُ المالك لهذه القراءة وحدَها) · و11 إن تغيّرت بصمةُ العقد ·
و7 إن وُجدت نتيجةٌ في `data/` («مرّةٌ واحدة») — كلُّها قبل قراءة أيّ مُدخَلٍ أو نداءِ أيّ مصدر."""
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_BASKET_prereg.md")
CONTRACT_SHA = "6fa5f522b5d3aae1b9e87c5d0f0ff149d29a6af366526d9140005dced6f71de2"
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")
REOPEN_ENV = "TRAIL_REOPEN"
CLOSED_RC, ONCE_RC, DRIFT_RC = 8, 7, 11

GOV_YEARS = ("2023", "2024", "2025")
DESC_YEAR = "2026"
D_FROM, D_TO = "2023-01-03", "2026-10-16"          # §① أيّامُ القرار (2026 وصفٌ)
MONTHS = [(2022, 12)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)] + [(2026, m) for m in range(1, 11)]
SESS_FROM, ALL_FROM = "2022-12-01", "2022-11-01"   # إحماءُ «الإدخال الجديد» (لقطةُ 2022-12 · لا تُعَدّ)
BARS = ("2020-10-01", "2026-11-16")                # §① شموعٌ يوميّة · و800 يومٍ قبل أوّل قرار
WIN_END = "2026-11-13"                             # آخرُ جلسةٍ في نوافذ 2026
WIN = 20
T1, T2 = 1.50, 2.00                                # §② الأمران
STOPS = (None, 0.30, 0.50)                         # §② أذرعُ الوقف
STOP_TAG = {None: "0", 0.30: "30", 0.50: "50"}
COST = 0.018                                       # §② ذهابًا وإيابًا
FILL_USD = 5000.0                                  # §② تعديلُ المالك ①
X30_PCT, X30_USD, X30_FROM, X30_END = 0.30, 50_000.0, 240, 960
OPEN_MIN = 570                                     # 09:30 نيويورك
NCTRL = 5                                          # §④
SLOTS = (10, 15)                                   # §③
SEED, BOOT = 20261116, 10_000                      # §⑥
MIN_N, COV_FLOOR = 30, 0.80                        # §⑥
NSHARDS = 40
LISTS = (("CURRENT", 4), ("NEW", 5))
EDGAR_FORMS = {"424B1", "424B2", "424B3", "424B4", "424B5", "S-1", "S-1/A", "S-3", "S-3/A", "F-1", "F-1/A", "F-3", "F-3/A",
               "DEF 14A", "PRE 14A"}
EDGAR_DAYS = 30


def log(m=""):
    print(m, flush=True)


# ── 🔒 الحارس ────────────────────────────────────────────────────────────────────────────────────────────────────────
def contract_ok(path=CONTRACT, sha=CONTRACT_SHA):
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest() == sha
    except OSError:
        return False


def result_exists(data=DATA):
    try:
        return any(n.startswith("basket_result_") and n.endswith(".json") for n in os.listdir(data))
    except OSError:
        return False


def gate(env=None, ok=None, done=None):
    """رمزُ الحارس قبل أيّ عمل: 8 بلا إقرار · 11 بعقدٍ متغيّر · 7 «مرّةٌ واحدة» · 0 يمضي."""
    env = os.environ if env is None else env
    if (env.get(REOPEN_ENV) or "") != "1":
        return CLOSED_RC
    if not (contract_ok() if ok is None else ok):
        return DRIFT_RC
    if result_exists() if done is None else done:
        return ONCE_RC
    return 0


# ── أدواتٌ نقيّة ─────────────────────────────────────────────────────────────────────────────────────────────────────
def window_scales(days, splits, entry_day):
    """§② مقياسُ يوم الدخول: سعرُ يوم t بمقياس الدخول = الخامُ × scale[t] · وتقسيمٌ تنفيذُه e بنسبة r = to/from:
    لأيّام t ‏≥ entry_day: scale = Π r لـ entry_day < e ≤ t · وليوم الإدراج D (قبل الدخول): scale = Π 1/r لـ e = entry_day."""
    sp = [(str(e), float(r)) for e, r in (splits or []) if r and float(r) > 0]
    out = {}
    for t in days:
        if t >= entry_day:
            f = 1.0
            for e, r in sp:
                if entry_day < e <= t:
                    f *= r
            out[t] = f
        else:
            f = 1.0
            for e, r in sp:
                if t < e <= entry_day:
                    f /= r
            out[t] = f
    return out


def simulate(mins, closes, days, stop=None, mode="orders", fill_ok=None, prev_close=None, alert=None, cost=COST):
    """§② صفقةٌ واحدة بمقياس الدخول.
    mins: {يوم: [(ms، دقيقةُ نيويورك، o، h، l، c، v)] مرتّبة} · closes: {يوم: إغلاقٌ يوميّ} · days: الجلسات `D+1`… حتى 20 ·
    mode: orders (الأمران) · x30 (البيعُ كاملًا عند أوّل تحرّك 30%) · alert (البيعُ عند أوّل تنبيهٍ بعد دقيقة الدخول) ·
    fill_ok(يوم، ms، سعرُ الأمر) ⟵ شرطُ الخمسة آلاف (None ⟵ يُقبل) · prev_close: {يوم: إغلاقُ الأمس بمقياس الدخول} ·
    alert: [(يوم، ms، px أو None)] مرتّبة ⟵ dict: r (بعد التكلفة) · e · ex [(نوع، الجلسة، سعر، حصّة)] · m (قيمةُ الوحدة بالإغلاق) ·
    xi · rej (دقائقُ رفضها الشرط) · tu (أوامرُ لُمست ولم تُنفَّذ قطّ) · short."""
    if not days:
        return None
    first = [b for b in (mins.get(days[0]) or []) if b[1] >= OPEN_MIN]
    if not first:
        return None
    E, ms0 = float(first[0][2]), int(first[0][0])
    if E <= 0:
        return None
    SP = None if stop is None else E * (1.0 - stop)
    legs = ([{"k": T1, "tag": "t1", "f": 0.5}, {"k": T2, "tag": "t2", "f": 0.5}] if mode == "orders"
            else [{"k": None, "tag": mode, "f": 1.0}])
    for lg in legs:
        lg.update(done=False, touched=False, ordered=False)
    al = None
    if mode == "alert":
        al = next(((a_d, int(a_ms), a_px) for a_d, a_ms, a_px in (alert or []) if a_d in days and (a_d != days[0] or int(a_ms) >= ms0)), None)
    ex, marks, rej, cash, xi, last_px = [], [], 0, 0.0, None, E

    def _sell(lg, kind, k, px):
        nonlocal cash
        lg["done"] = True
        ex.append((kind, k, float(px), lg["f"]))
        cash += lg["f"] * float(px) / E
    for k, d in enumerate(days, start=1):
        cum = 0.0
        for ms, nm, o, h, lo, c, v in (mins.get(d) or []):
            cum += float(v) * float(c)
            if xi is not None or (k == 1 and ms < ms0):
                continue
            last_px = c
            rem = [lg for lg in legs if not lg["done"]]
            if SP is not None and lo <= SP:
                for lg in rem:
                    _sell(lg, "stop", k, o if o <= SP else SP)
            elif mode == "orders":
                for lg in rem:
                    L = E * lg["k"]
                    if h >= L:
                        lg["touched"] = True
                        if fill_ok is None or fill_ok(d, ms, L):
                            lg["ordered"] = True
                            _sell(lg, lg["tag"], k, L)
                        else:
                            rej += 1
            elif mode == "x30":
                p0 = (prev_close or {}).get(d)
                if p0 and X30_FROM <= nm < X30_END and h >= p0 * (1 + X30_PCT) and cum >= X30_USD:
                    for lg in rem:
                        _sell(lg, "x30", k, c)
            elif mode == "alert" and al and d == al[0] and ms >= al[1]:
                for lg in rem:
                    _sell(lg, "alert", k, al[2] if al[2] is not None else c)
            if all(lg["done"] for lg in legs):
                xi = k
        cl = closes.get(d)
        if cl is not None:
            last_px = cl
        rem_frac = sum(lg["f"] for lg in legs if not lg["done"])
        marks.append(cash + rem_frac * float(last_px) / E)
        if xi is not None:
            break
    short = closes.get(days[-1]) is None and not mins.get(days[-1])
    if xi is None:
        for lg in legs:
            if not lg["done"]:
                _sell(lg, "time", len(marks), last_px)
        marks[-1] = cash
        xi = len(marks)
    r = sum(fr * (px / E - 1.0) for _k, _i, px, fr in ex) - cost
    tu = sum(1 for lg in legs if lg["touched"] and not lg["ordered"])
    return {"r": round(r, 6), "e": E, "ex": [[a, b, round(c, 6), f] for a, b, c, f in ex], "m": [round(x, 6) for x in marks],
            "xi": xi, "rej": rej, "tu": tu, "short": short}


def q_at(vals, q):
    v = sorted(vals)
    return v[min(len(v) - 1, max(0, int(math.floor(q * (len(v) - 1) + 0.5))))] if v else None


def concentration(rets):
    """§③ تعديلُ المالك ②: المتوسّطُ والوسيطُ بعد استبعاد أعلى ⌈1%⌉ · وحصّةُ أعلى ⌈5%⌉ من مجموع العوائد الموجبة ومن الصافي (حين موجب)."""
    v = sorted(rets, reverse=True)
    n = len(v)
    if not n:
        return None
    k1, k5 = math.ceil(0.01 * n), math.ceil(0.05 * n)
    rest = v[k1:]
    gross = sum(x for x in v if x > 0)
    net = sum(v)
    top5 = sum(v[:k5])
    return {"drop1_n": k1, "mean_ex1": round(sum(rest) / len(rest), 6) if rest else None,
            "median_ex1": round(q_at(rest, 0.5), 6) if rest else None, "top5_n": k5,
            "top5_of_gross": round(top5 / gross, 4) if gross > 0 else None, "top5_of_net": round(top5 / net, 4) if net > 0 else None}


def dist_stats(rets):
    if not rets:
        return {"n": 0}
    n = len(rets)
    qs = (0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99)
    return {"n": n, "mean": round(sum(rets) / n, 6), "median": round(q_at(rets, 0.5), 6), "min": round(min(rets), 6),
            "max": round(max(rets), 6), "q": {str(q): round(q_at(rets, q), 6) for q in qs},
            "worse_m50": round(sum(1 for x in rets if x < -0.50) / n, 4)}


def boot_mean(pairs, seed=SEED, b=BOOT):
    """§⑥ فاصلُ 95% لمتوسّط العائد ببوتستراب عنقوديٍّ بالرمز (pairs = [(رمز، عائد)])."""
    import numpy as np
    per = {}
    for s, r in pairs:
        p = per.setdefault(s, [0.0, 0])
        p[0] += r
        p[1] += 1
    if not per:
        return None
    sums = np.array([per[s][0] for s in sorted(per)])
    cnts = np.array([per[s][1] for s in sorted(per)])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(b, len(sums)))
    vals = np.sort(sums[idx].sum(axis=1) / cnts[idx].sum(axis=1))
    return [round(float(vals[int(0.025 * b)]), 6), round(float(vals[min(b - 1, int(0.975 * b))]), 6)]


def cell_verdict(by_year, cis, covs):
    """§⑥: «موجبٌ مُثبَت» إن كانت كلُّ سنةٍ من الثلاث: عددُها ‏≥ 30 · تغطيتُها ‏≥ 80% · وأدنى فاصلها فوق الصفر · وإلّا «غيرُ مُثبَت» أو «لا قياس»."""
    for y in GOV_YEARS:
        if (by_year.get(y) or {}).get("n", 0) < MIN_N or (covs.get(y) or 0) < COV_FLOOR:
            return "لا قياس"
    if all(cis.get(y) and cis[y][0] > 0 for y in GOV_YEARS):
        return "موجبٌ مُثبَت"
    return "غيرُ مُثبَت"


def portfolio(trades, sessions, n_slots, cost=COST):
    """§③ سلّةُ n خاناتٍ: trades = [{"day": يومُ الدخول، "key": (D، رمز)، "m": [قيمةُ الوحدة بإغلاق كلّ جلسة]}] ·
    ⟵ dict: eq (قيمٌ يوميّة) · dd (أعمقُ هبوط) · months {شهر: عائد} · skipped · ret (عائدُ الفترة)."""
    by_day = {}
    for t in trades:
        by_day.setdefault(t["day"], []).append(t)
    days = [d for d in sessions if d >= min(by_day)] if by_day else []
    cash, pos, eq_prev, eq_path, skipped = 1.0, [], 1.0, [], 0
    for d in days:
        for t in sorted(by_day.get(d, []), key=lambda x: x["key"]):
            if len(pos) >= n_slots:
                skipped += 1
                continue
            alloc = eq_prev / n_slots
            cash -= alloc * (1.0 + cost)
            pos.append([alloc, t["m"], 0])
        val, keep = 0.0, []
        for p in pos:
            k = p[2]
            v = p[0] * p[1][k]
            if k == len(p[1]) - 1:
                cash += v
            else:
                val += v
                p[2] = k + 1
                keep.append(p)
        pos = keep
        eq_prev = cash + val
        eq_path.append((d, eq_prev))
        if not pos and d > max(by_day):
            break
    if not eq_path:
        return None
    peak, dd = 1.0, 0.0                                           # رأسُ المال الابتدائيّ ذروةٌ أولى
    for _d, e in eq_path:
        peak = max(peak, e)
        dd = min(dd, e / peak - 1.0)
    months, last = {}, {}
    for d, e in eq_path:
        last[d[:7]] = e
    prev = 1.0
    for mth in sorted(last):
        months[mth] = round(last[mth] / prev - 1.0, 6)
        prev = last[mth]
    mv = list(months.values())
    return {"ret": round(eq_path[-1][1] - 1.0, 6), "dd": round(dd, 6), "skipped": skipped, "months": months,
            "m_mean": round(sum(mv) / len(mv), 6) if mv else None, "m_median": round(q_at(mv, 0.5), 6) if mv else None,
            "m_worst": round(min(mv), 6) if mv else None, "m_best": round(max(mv), 6) if mv else None,
            "m_pos": sum(1 for x in mv if x > 0), "m_n": len(mv)}


def ctrl_pick(sym, d, decs, n=NCTRL):
    """§④ خمسةٌ من عُشير (س، D) غيرُ س بترتيب sha256("{س}|{D}|{k}") — حتميّ ومستقلٌّ عن التقسيم."""
    dec = (decs or {}).get(sym)
    if dec is None:
        return []
    cands = sorted(s for s, q in decs.items() if q == dec and s != sym)
    return sorted(cands, key=lambda c: hashlib.sha256(f"{sym}|{d}|{c}".encode()).hexdigest())[:n]


def deciles(ret5):
    """{رمز: صعودُ خمس جلسات} ⟵ {رمز: عُشير 0-9} بالرتبة (التعادلُ بالرمز)."""
    items = sorted(ret5.items(), key=lambda kv: (kv[1], kv[0]))
    n = len(items)
    return {s: min(9, (10 * i) // n) for i, (s, _v) in enumerate(items)} if n else {}


def edgar_flag(filings, d, days=EDGAR_DAYS):
    """§⑤ (ب): إيداعٌ مستبعِدٌ في [D − 30 يومًا، D) ⟵ True · filings = [(تاريخ، نوع، بنود)] أو None (غيرُ معلوم)."""
    if filings is None:
        return None
    lo = (dt.date.fromisoformat(d) - dt.timedelta(days)).isoformat()
    for fd, form, items in filings:
        if lo <= fd < d and (form in EDGAR_FORMS or (form == "8-K" and "3.01" in str(items or ""))):
            return True
    return False


# ── المصادر (Polygon · SEC) ──────────────────────────────────────────────────────────────────────────────────────────
NY = None


def _ny():
    global NY
    if NY is None:
        from zoneinfo import ZoneInfo
        NY = ZoneInfo("America/New_York")
    return NY


def _getjson(url, headers=None, tries=3, timeout=30):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers or {"User-Agent": "t-basket/1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:                      # noqa: PERF203
            if e.code in (403, 404):
                return None
            time.sleep(2 ** k)
        except Exception:                                        # noqa: BLE001
            time.sleep(2 ** k)
    return None


def poly_minutes(sym, d1, d2, key):
    """دقائقُ خامٌ ⟵ {يوم: [(ms، دقيقةُ نيويورك، o، h، l، c، v)]} أو None."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/minute/{d1}/{d2}?adjusted=false&sort=asc&limit=50000&apiKey={key}")
    out, n = {}, 0
    while url and n < 4:
        js = _getjson(url)
        if js is None:
            return None
        for b in js.get("results") or []:
            t = dt.datetime.fromtimestamp(b["t"] / 1000, tz=dt.timezone.utc).astimezone(_ny())
            out.setdefault(t.date().isoformat(), []).append((int(b["t"]), t.hour * 60 + t.minute, float(b["o"]), float(b["h"]),
                                                            float(b["l"]), float(b["c"]), float(b.get("v") or 0.0)))
        url = js.get("next_url")
        if url:
            url += f"&apiKey={key}"
        n += 1
    return out


def poly_dailies(sym, d1, d2, key):
    js = _getjson(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d1}/{d2}?adjusted=false&sort=asc&limit=500&apiKey={key}")
    if js is None:
        return None
    return {dt.datetime.fromtimestamp(b["t"] / 1000, tz=dt.timezone.utc).astimezone(_ny()).date().isoformat(): float(b["c"])
            for b in js.get("results") or []}


def poly_usd_at_or_above(sym, ms, price_raw, key):
    """§② تعديلُ المالك ①: دولارُ الصفقات بسعرٍ ‏≥ الأمر (خامًا) في الدقيقة [ms، ms+60ث)."""
    lo, hi = int(ms) * 1_000_000, (int(ms) + 60_000) * 1_000_000
    url = f"https://api.polygon.io/v3/trades/{sym}?timestamp.gte={lo}&timestamp.lt={hi}&limit=50000&apiKey={key}"
    usd, pages = 0.0, 0
    while url and pages < 5:
        js = _getjson(url)
        if js is None:
            return None
        for t in js.get("results") or []:
            p, s = float(t.get("price") or 0), float(t.get("size") or 0)
            if p >= price_raw - 1e-9:
                usd += p * s
        url = js.get("next_url")
        if url:
            url += f"&apiKey={key}"
        pages += 1
    return usd


def scaled(mins_raw, closes_raw, scales):
    m = {d: [(a, b, o * scales.get(d, 1.0), h * scales.get(d, 1.0), lo * scales.get(d, 1.0), c * scales.get(d, 1.0), v)
             for a, b, o, h, lo, c, v in bars] for d, bars in (mins_raw or {}).items()}
    c = {d: x * scales.get(d, 1.0) for d, x in (closes_raw or {}).items()}
    return m, c


# ── الأوضاع ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def _rb():
    spec = importlib.util.spec_from_file_location("rb_basket", os.path.join(ROOT, "fm_forensics", "rebuild", "rebuild.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _jdump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


def _jload(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def mode_prep(key):
    """§⑧ العضويّةُ والتقسيماتُ وFINRA (`mode_bases_prep` بالاسم) · عُشيراتُ الزخم · خريطةُ CIK · تنبيهاتُ «هنا الدخول»."""
    sys.path.insert(0, ROOT)
    RB = _rb()
    import market_calendar as MC
    RB.OUT = OUT
    pr = RB.mode_bases_prep(key, months=MONTHS, sess_from=SESS_FROM, sess_to=D_TO, all_from=ALL_FROM, out="basket_rbprep.json.gz",
                            tag="basket_prep", splits_range=BARS)
    prep = _jload(os.path.join(OUT, "basket_rbprep.json.gz"))
    allsess = RB.sessions_between(ALL_FROM, WIN_END, MC)
    gsess = [d for d in allsess if d <= D_TO]
    closes = {}
    for d in gsess:
        js = _getjson(f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{d}?adjusted=true&apiKey={key}")
        closes[d] = {r["T"]: float(r["c"]) for r in ((js or {}).get("results") or []) if r.get("c")}
    decs, miss = {}, 0
    for i, d in enumerate(gsess):
        if d < D_FROM or i < 5:
            continue
        mem = prep["snapshots"].get(d[:7]) or []
        c0, c5 = closes.get(d) or {}, closes.get(gsess[i - 5]) or {}
        r5 = {s: c0[s] / c5[s] - 1.0 for s in mem if s in c0 and s in c5 and c5[s] > 0}
        if not r5:
            miss += 1
        decs[d] = deciles(r5)
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    cik = {}
    if contact:
        js = _getjson("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent": contact})
        for v in (js or {}).values():
            cik[str(v.get("ticker", "")).upper()] = int(v.get("cik_str"))
    alerts, src = {}, []
    try:
        LVS = _load_lvs()
        U = {"sessions": [d for d in allsess if "2026-08-12" <= d <= WIN_END]}
        alerts = LVS.rebuild_alerts(U, True)
        src = LVS.source_days(dict(U, alerts=alerts))
    except Exception as e:                                        # noqa: BLE001
        log(f"⚠️ «هنا الدخول»: تعذّر بناءُ التنبيهات ({type(e).__name__}) ⟵ الوصفُ «لا قياس»")
    extra = {"allsess": allsess, "decs": decs, "dec_missing_days": miss, "cik": cik, "sec": bool(contact), "alerts": alerts, "alert_src": src}
    _jdump(extra, os.path.join(OUT, "basket_extra.json.gz"))
    return {"mode": "prep", "rb": pr, "sessions_all": len(allsess), "dec_days": len(decs), "dec_missing_days": miss, "cik": len(cik),
            "sec_contact": bool(contact), "alert_days": len(alerts), "alert_src_days": len(src)}


def _load_lvs():
    sys.path.insert(0, ROOT)
    spec = importlib.util.spec_from_file_location("lvs_basket", os.path.join(ROOT, "fm_forensics", "live_vs_shadow", "live_vs_shadow.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def edgar_filings(cik, contact, cache):
    if cik in cache:
        return cache[cik]
    hdr = {"User-Agent": contact}
    time.sleep(0.15)
    js = _getjson(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", headers=hdr)
    if js is None:
        cache[cik] = None
        return None
    out = []

    def _take(blk):
        for fd, fm, it in zip(blk.get("filingDate") or [], blk.get("form") or [], blk.get("items") or [""] * len(blk.get("form") or [])):
            out.append((fd, fm, it))
    _take((js.get("filings") or {}).get("recent") or {})
    for f in (js.get("filings") or {}).get("files") or []:
        if str(f.get("filingTo") or "") >= "2022-11-01":
            time.sleep(0.15)
            js2 = _getjson(f"https://data.sec.gov/submissions/{f['name']}", headers=hdr)
            if js2 is None:
                cache[cik] = None
                return None
            _take(js2)
    cache[cik] = out
    return out


def trade_all(sym, d, window, splits, key, arms, alert=None, fcache=None):
    """دقائقُ النافذة ⟵ الأذرعُ المطلوبة {اسم: نتيجة} · وNone بلا دقائق."""
    if not window:
        return None, "no_window"
    mins_raw = poly_minutes(sym, window[0], window[-1], key)
    cls_raw = poly_dailies(sym, d, window[-1], key)
    if not mins_raw:
        return None, "no_minutes"
    sc = window_scales([d] + list(window), splits, window[0])
    mins, cls = scaled(mins_raw, cls_raw or {}, sc)
    fcache = {} if fcache is None else fcache

    def _fill(day, ms, L):
        k = (sym, ms, round(L, 8))
        if k not in fcache:
            usd = poly_usd_at_or_above(sym, ms, L / sc.get(day, 1.0), key)
            fcache[k] = usd is not None and usd >= FILL_USD
        return fcache[k]
    seq = [d] + list(window)
    prev = {seq[i]: cls.get(seq[i - 1]) for i in range(1, len(seq))}
    out = {}
    for arm in arms:
        mode, stop = arm
        out[f"{mode[0].upper()}{STOP_TAG[stop]}"] = simulate(mins, cls, list(window), stop=stop, mode=mode,
                                                            fill_ok=_fill if mode == "orders" else None,
                                                            prev_close=prev if mode == "x30" else None, alert=alert)
    return out, "ok"


def mode_shard(key, shard, nshards):
    sys.path.insert(0, ROOT)
    RB = _rb()
    RB.OUT = OUT
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    import pit_history as PH
    prep = _jload(os.path.join(OUT, "basket_rbprep.json.gz"))
    extra = _jload(os.path.join(OUT, "basket_extra.json.gz"))
    fz = RB.freeze_load()
    if fz is None:
        raise ValueError("لا تجميدَ ببصمته")
    live, _ = RB.configs(S)
    RB.install_stubs(S)
    G5 = RB._gen5_ext()
    pct = float(live["EXPLOSION_PCT"])
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    allsess = extra["allsess"]
    pos = {d: i for i, d in enumerate(allsess)}
    contact = (os.environ.get("SEC_CONTACT") or "").strip()
    pcache, ecache, fcache, ccache = {}, {}, {}, {}

    def _proxy(sym, day):
        if (sym, day) not in pcache:
            code, body = RB._get(RB.PROXY_URL.format(t=sym, d=day, k=key))
            try:
                pcache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                    # noqa: BLE001
                pcache[(sym, day)] = None
        return pcache[(sym, day)]
    syms = prep["union"][shard::nshards]
    recs, diag, t0 = [], {}, time.time()
    arms_main = [("orders", s) for s in STOPS] + [("x30", s) for s in STOPS]
    for n, sym in enumerate(syms):
        df, why = PH.polygon_daily(sym, BARS[0], BARS[1], key)
        rows = RB._rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        fired = RB.test_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["sessions"], prep["prev_of"], prep["finra"],
                               _proxy, S, live, pct, G5, fz, period_end=D_TO)
        lists = {}
        for name, k in LISTS:
            days = sorted({r[1] for r in fired if r[k]})
            for d in RB.new_entries(days, prep["sessions"]):
                if D_FROM <= d <= D_TO:
                    lists.setdefault(d, []).append(name)
        for d, names in sorted(lists.items()):
            i = pos.get(d)
            window = allsess[i + 1:i + 1 + WIN] if i is not None else []
            src = set(extra.get("alert_src") or [])
            in_src = bool(window) and all(x in src for x in window)
            al = [(x, a["ms"], a.get("px")) for x in window for a in [((extra.get("alerts") or {}).get(x) or {}).get(sym)] if a] if in_src else []
            arms = arms_main + ([("alert", s) for s in STOPS] if in_src else [])
            res, st = trade_all(sym, d, window, prep["splits"].get(sym), key, arms, alert=al, fcache=fcache)
            filings = edgar_filings(int(extra["cik"][sym]), contact, ecache) if (contact and sym in (extra.get("cik") or {})) else None
            ctrls = []
            for c in ctrl_pick(sym, d, (extra.get("decs") or {}).get(d) or {}):
                ck = (c, d)
                if ck not in ccache:
                    cr, cst = trade_all(c, d, window, prep["splits"].get(c), key, [("orders", s) for s in STOPS], fcache=fcache)
                    ccache[ck] = {a: (v or {}).get("r") for a, v in (cr or {}).items()} if cr else None
                ctrls.append(ccache[ck])
            recs.append({"sym": sym, "d": d, "y": d[:4], "lists": names, "st": st, "in_src": in_src, "alert": bool(al),
                         "res": res, "b": edgar_flag(filings, d), "ctrl": ctrls, "day1": window[0] if window else None})
        if n % 10 == 0:
            log(f"basket shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · entries {len(recs)}")
    out = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "freeze_sha": fz["sha"], "recs": recs,
           "trades_calls": len(fcache)}
    _jdump(out, os.path.join(OUT, f"basket_shard_{shard:02d}.json.gz"))
    return {k: v for k, v in out.items() if k != "recs"} | {"entries": len(recs)}


def summarize(recs, allsess):
    """§③-§⑥ من سجلّات الشرائح ⟵ النتيجة (بلا نداء)."""
    res = {"cells": {}, "verdict": {}, "coverage": {}, "rejected": {}, "arm_b": {}, "arm_a": {}, "alert": {}, "control": {}, "portfolio": {},
           "y2026": {}}
    years = GOV_YEARS + (DESC_YEAR,)
    for name, _k in LISTS:
        L = [r for r in recs if name in r["lists"]]
        res["coverage"][name] = {y: (lambda ys: round(sum(1 for r in ys if r["res"] and (r["res"].get("O0") is not None)) / len(ys), 4)
                                     if ys else None)([r for r in L if r["y"] == y]) for y in years}
        for stop in STOPS:
            arm = f"O{STOP_TAG[stop]}"
            cell = {}
            cis = {}
            for y in years:
                ok = [r for r in L if r["y"] == y and r["res"] and r["res"].get(arm)]
                rets = [r["res"][arm]["r"] for r in ok]
                st = dist_stats(rets)
                st["conc"] = concentration(rets)
                mix = {}
                for r in ok:
                    for e in r["res"][arm]["ex"]:
                        mix[e[0]] = mix.get(e[0], 0) + 1
                st["exits"] = mix
                st["rej_minutes"] = sum(r["res"][arm]["rej"] for r in ok)
                st["touched_unfilled"] = sum(r["res"][arm]["tu"] for r in ok)
                st["short"] = sum(1 for r in ok if r["res"][arm]["short"])
                ci = boot_mean([(r["sym"], r["res"][arm]["r"]) for r in ok]) if len(ok) >= 2 else None
                st["ci"] = ci
                cis[y] = ci
                for ns in SLOTS:
                    tr = [{"day": r["day1"], "key": (r["d"], r["sym"]), "m": r["res"][arm]["m"]} for r in ok]
                    st[f"basket{ns}"] = portfolio(tr, allsess, ns) if tr else None
                cell[y] = st
            res["cells"][f"{name}|{arm}"] = cell
            res["verdict"][f"{name}|{arm}"] = cell_verdict(cell, cis, res["coverage"][name])
            for mode, tag in (("x30", "X"), ("alert", "A")):
                key_ = f"{tag}{STOP_TAG[stop]}"
                tgt = res["arm_a"] if mode == "x30" else res["alert"]
                tgt[f"{name}|{key_}"] = {y: dist_stats([r["res"][key_]["r"] for r in L if r["y"] == y and r["res"] and r["res"].get(key_)])
                                         for y in years}
            res["arm_b"][f"{name}|{arm}"] = {y: dist_stats([r["res"][arm]["r"] for r in L if r["y"] == y and r["res"] and r["res"].get(arm)
                                                            and r["b"] is False])
                                             | {"excluded": sum(1 for r in L if r["y"] == y and r["b"] is True),
                                                "unknown": sum(1 for r in L if r["y"] == y and r["b"] is None)} for y in years}
            diffs = {}
            for y in years + ("ALL3",):
                pairs = []
                for r in L:
                    if (r["y"] == y or (y == "ALL3" and r["y"] in GOV_YEARS)) and r["res"] and r["res"].get(arm):
                        cr = [c.get(arm) for c in r["ctrl"] if c and c.get(arm) is not None]
                        if cr:
                            pairs.append((r["sym"], r["res"][arm]["r"] - sum(cr) / len(cr)))
                diffs[y] = {"n": len(pairs), "mean": round(sum(p[1] for p in pairs) / len(pairs), 6) if pairs else None,
                            "ci": boot_mean(pairs) if len(pairs) >= 2 else None}
            res["control"][f"{name}|{arm}"] = diffs
    return res


def predictions(res):
    def cell(name, arm, y):
        return ((res["cells"].get(f"{name}|{arm}") or {}).get(y) or {})

    def pooled(name, arm, fn):
        vals = []
        for y in GOV_YEARS:
            c = cell(name, arm, y)
            vals.append(fn(c))
        return vals
    out = {}
    out["BKP1"] = res["verdict"].get("CURRENT|O0") != "موجبٌ مُثبَت"
    a, b = cell("NEW", "O0", "2025").get("mean"), cell("CURRENT", "O0", "2025").get("mean")
    out["BKP2"] = None if a is None or b is None else a > b
    w = []
    for nm in ("CURRENT", "NEW"):
        n = sum(cell(nm, "O0", y).get("n", 0) for y in GOV_YEARS)
        k = sum(cell(nm, "O0", y).get("n", 0) * (cell(nm, "O0", y).get("worse_m50") or 0) for y in GOV_YEARS)
        w.append(k / n if n else None)
    out["BKP3"] = None if None in w else all(x >= 0.10 for x in w)
    m = []
    for nm in ("CURRENT", "NEW"):
        def _mean(arm):
            n = sum(cell(nm, arm, y).get("n", 0) for y in GOV_YEARS)
            s = sum(cell(nm, arm, y).get("n", 0) * (cell(nm, arm, y).get("mean") or 0) for y in GOV_YEARS)
            return s / n if n else None
        m.append((_mean("O30"), _mean("O0")))
    out["BKP4"] = None if any(None in t for t in m) else all(x < y for x, y in m)
    dds = [((cell("CURRENT", "O0", y).get("basket15") or {}).get("dd")) for y in GOV_YEARS]
    out["BKP5"] = None if all(x is None for x in dds) else any(x is not None and x < -0.40 for x in dds)
    v = []
    for nm in ("CURRENT", "NEW"):
        xa = [((res["arm_a"].get(f"{nm}|X0") or {}).get(y) or {}) for y in GOV_YEARS]
        nx = sum(c.get("n", 0) for c in xa)
        sx = sum(c.get("n", 0) * (c.get("mean") or 0) for c in xa)
        no = sum(cell(nm, "O0", y).get("n", 0) for y in GOV_YEARS)
        so = sum(cell(nm, "O0", y).get("n", 0) * (cell(nm, "O0", y).get("mean") or 0) for y in GOV_YEARS)
        v.append(None if not nx or not no else sx / nx < so / no)
    out["BKP6"] = None if None in v else all(v)
    v = []
    for nm in ("CURRENT", "NEW"):
        xb = [((res["arm_b"].get(f"{nm}|O0") or {}).get(y) or {}) for y in GOV_YEARS]
        nb = sum(c.get("n", 0) for c in xb)
        sb = sum(c.get("n", 0) * (c.get("mean") or 0) for c in xb)
        no = sum(cell(nm, "O0", y).get("n", 0) for y in GOV_YEARS)
        so = sum(cell(nm, "O0", y).get("n", 0) * (cell(nm, "O0", y).get("mean") or 0) for y in GOV_YEARS)
        v.append(None if not nb or not no else sb / nb > so / no)
    out["BKP7"] = None if None in v else all(v)
    ci = ((res["control"].get("CURRENT|O0") or {}).get("ALL3") or {}).get("ci")
    out["BKP8"] = None if not ci else ci[0] <= 0 <= ci[1]
    tu = sum(cell(nm, "O0", y).get("touched_unfilled", 0) for nm in ("CURRENT", "NEW") for y in GOV_YEARS)
    touched = sum(sum(v for k, v in (cell(nm, "O0", y).get("exits") or {}).items() if k in ("t1", "t2")) for nm in ("CURRENT", "NEW")
                  for y in GOV_YEARS) + tu
    out["BKP9"] = None if not touched else tu / touched <= 0.05
    out["BKP10"] = res.get("pooled_top5_current_o0")
    if out["BKP10"] is not None:
        out["BKP10"] = out["BKP10"] >= 0.50
    return out


def mode_assemble():
    import glob
    sys.path.insert(0, ROOT)
    RB = _rb()
    fz = RB.freeze_load()
    extra = _jload(os.path.join(OUT, "basket_extra.json.gz"))
    shards = [_jload(p) for p in sorted(glob.glob(os.path.join(OUT, "**", "basket_shard_*.json.gz"), recursive=True))]
    if not shards or len(shards) != shards[0]["nshards"] or any(sh["freeze_sha"] != fz["sha"] for sh in shards):
        return {"mode": "assemble", "verdict": "⛔ لا حكم — الشرائحُ ناقصةٌ أو بتجميدٍ آخر", "shards": len(shards)}
    recs = [r for sh in shards for r in sh["recs"]]
    res = summarize(recs, extra["allsess"])
    pooled = [r["res"]["O0"]["r"] for r in recs if "CURRENT" in r["lists"] and r["y"] in GOV_YEARS and r["res"] and r["res"].get("O0")]
    res["pooled_top5_current_o0"] = (concentration(pooled) or {}).get("top5_of_gross") if pooled else None
    res["predictions"] = predictions(res)
    diag = {}
    for sh in shards:
        for k, v in sh["bars_diag"].items():
            diag[k] = diag.get(k, 0) + v
    res.update({"mode": "assemble", "contract_sha": CONTRACT_SHA, "freeze_sha": fz["sha"], "entries": len(recs), "bars_diag": diag,
                "status": {k: sum(1 for r in recs if r["st"] == k) for k in sorted({r["st"] for r in recs})},
                "trades_calls": sum(sh.get("trades_calls", 0) for sh in shards), "sec": extra.get("sec"),
                "alert_src_days": len(extra.get("alert_src") or [])})
    return res


def _pc(x):
    return "—" if x is None else f"{x * 100:+.1f}%"


def report_lines(res):
    """سطورٌ مقروءة لكلّ خليّة — والحكمُ آخرَ الأسطر (درسُ `T-TRAIL`: الحاكمُ لا يُدفن فوق الجداول)."""
    out = []
    for cell, by in (res.get("cells") or {}).items():
        for y, c in by.items():
            if not c.get("n"):
                out.append(f"BKT {cell} {y}: n=0")
                continue
            b10, b15 = c.get("basket10") or {}, c.get("basket15") or {}
            cc = c.get("conc") or {}
            out.append(f"BKT {cell} {y}: n={c['n']} mean={_pc(c['mean'])} median={_pc(c['median'])} ci=[{_pc((c.get('ci') or [None])[0])},"
                       f"{_pc((c.get('ci') or [None, None])[1])}] worse-50={c['worse_m50'] * 100:.1f}% mean_ex1={_pc(cc.get('mean_ex1'))} "
                       f"top5/gross={cc.get('top5_of_gross')} exits={c.get('exits')} rej_min={c.get('rej_minutes')} touched_unfilled={c.get('touched_unfilled')} "
                       f"b10 ret={_pc(b10.get('ret'))} dd={_pc(b10.get('dd'))} b15 ret={_pc(b15.get('ret'))} dd={_pc(b15.get('dd'))} "
                       f"b15 m_mean={_pc(b15.get('m_mean'))} m_worst={_pc(b15.get('m_worst'))} pos={b15.get('m_pos')}/{b15.get('m_n')}")
    for k, v in (res.get("predictions") or {}).items():
        out.append(f"BKP {k}: {v}")
    for k, v in (res.get("verdict") or {}).items():
        out.append(f"BASKET_VERDICT {k}: {v}")
    return out


def main():
    rc = gate()
    if rc:
        log({CLOSED_RC: "🔒 محورُ الخروج مُغلَق — `TRAIL_REOPEN` ليس \"1\" (خروج 8)",
             DRIFT_RC: "⛔ بصمةُ العقد تغيّرت (خروج 11)", ONCE_RC: "⛔ نتيجةٌ في data/ — «مرّةٌ واحدة» (خروج 7)"}[rc])
        return rc
    mode = os.environ.get("BASKET_MODE", "").strip()
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if mode != "assemble" and not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    t0 = time.time()
    if mode == "prep":
        res = mode_prep(key)
    elif mode == "shard":
        res = mode_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", str(NSHARDS))))
    elif mode == "assemble":
        res = mode_assemble()
        _jdump(res, os.path.join(OUT, "basket_result.json.gz"))
    else:
        log(f"⛔ وضعٌ غيرُ مبنيّ: {mode!r}")
        return 3
    res["seconds"] = round(time.time() - t0, 1)
    blob = json.dumps(res, ensure_ascii=False, separators=(",", ":"))
    parts = [blob[i:i + 3000] for i in range(0, len(blob), 3000)] or [""]
    for i, ch in enumerate(parts, start=1):
        print(f"BASKET_JSON_PART {i}/{len(parts)} {ch}")
    if mode == "assemble":
        for ln in report_lines(res):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
