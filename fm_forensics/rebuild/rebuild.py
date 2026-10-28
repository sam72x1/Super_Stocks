# -*- coding: utf-8 -*-
"""🧭 `T-REBUILD` — إعادةُ بناء القبول من البيانات (العقد `fm_forensics/rebuild/T_REBUILD_prereg.md` · مدموجٌ قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا `LOGIC_VERSION` · ولا يُشحَن منه شيء (§⓪ · §⑫).

الأوضاع المبنيّة الآن (المراحل التالية تُضاف بعد قراءة أرقام هذه):
    REBUILD_MODE=d0        جدوى البيانات §③ — أعدادٌ فقط (اللقطات · الرموز · التغطية · الحرّاس على عيّنة الشموع · FINRA · وكيلُ الفلوت)
    REBUILD_MODE=ready117  جدولُ §⑤ — RSI14 للـ117 READY والـ277 MISSED_READY (وصفيّ · لا يختار شيئًا)
    REBUILD_MODE=bases_prep / bases_shard (SHARD · NSHARDS) / bases_assemble   §⑥ الأساسُ على TRAIN والاختيارُ على VAL — ولا TEST
    REBUILD_MODE=test_prep / test_shard / test_assemble   §⑩-§⑪ TEST مرّةً واحدة بالدرجة المجمَّدة (`data/freeze_rebuild.json`)
    REBUILD_MODE=pairs_shard (SHARD · NSHARDS) / pairs_assemble   §⑨ الأزواجُ ثمّ §⑧ الدرجةُ والتجميد بالملحق 1 (`T_REBUILD_ADDENDUM_1.md`) على TRAIN وحدَه

الدوالُّ النقيّة (مقفولةٌ سلوكيًّا في `RBD1`/`RBD3`): `asof_scale` · `new_entries` · `exploded` · `rsi14_before` · `gaps` · `band` ·
`base2_fire` · `owner_fire` · `jump_at` · `row_guards` · `rule_entries` · `boot_diff` · `choose_base` · و`post_scan` على الدوالّ الإنتاجيّة بالاسم ·
وفي `RBD6`: `jumps` · `p1_days` · `p1p_days` · `p2_days` · `p3_days` · `pair_flags` · `base2_dist` · `gate_stats` · `mh_rr` · `fit_logistic` · `find_theta` · `freeze_sha`.
"""
import csv
import datetime as dt
import json
import os
import random
import statistics as st
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CONTRACT = os.path.join(HERE, "T_REBUILD_prereg.md")
SEED = 20261028
WIN = 20                       # §⑥ نافذةُ الوسم ونافذةُ «الإدخال الجديد» (جلسات)
TRAIN = ("2023-01-03", "2024-03-28")
VAL = ("2024-04-01", "2024-12-31")
TEST = ("2025-01-02", "2025-12-31")
BARS_FROM, BARS_TO = "2020-10-01", "2026-01-31"   # §③ HISTORY_DAYS=800 قبل أوّل قرار
RECYCLE_GAP_DAYS = 15          # §③ حارسُ إعادة تدوير الرمز
COVERAGE_FLOOR = 0.85          # §③ تغطيةٌ دونها ⟵ «لا قياس»


def log(*a):
    print(*a, flush=True)


# ── نقيّة ────────────────────────────────────────────────────────────────────────────────────────────
def asof_factor(splits, day):
    """∏(to/from) للتقسيمات المنفّذة في D أو بعده (§③) — السعرُ × الحاصل والحجمُ ÷ الحاصل يُعيدان مقياسَ D−1."""
    f = 1.0
    for d, r in splits or []:
        if d >= day and r and r > 0:
            f *= float(r)
    return f


def asof_scale(rows, splits, day):
    """§③ التسويةُ بتاريخ القرار. rows = [(يوم ISO، o، h، l، c، v)] مسوّاةٌ بكلّ التقسيمات حتى الجلب ·
    splits = [(يوم التنفيذ ISO، نسبة to/from)] · day = يومُ القرار D. يُرجع الصفوف قبل D على **مقياس D−1**:
    السعرُ × ∏(النسبة) للتقسيمات المنفّذة في D أو بعده · والحجمُ ÷ الحاصل. صفوفُ D فصاعدًا لا تُرجع (لا نظرَ للأمام)."""
    f = asof_factor(splits, day)
    out = []
    for x in rows:
        if x[0] >= day:
            break
        out.append((x[0], x[1] * f, x[2] * f, x[3] * f, x[4] * f, x[5] / f if f else x[5]))
    return out


def new_entries(fire_days, sessions, win=WIN):
    """§⑥ الإدخالُ الجديد: من أيّام انطلاق القاعدة لرمزٍ (مرتّبة) يُبقي يومَ D إن لم تنطلق في الجلسات [D−win، D−1].
    sessions = قائمةُ أيّام الجلسات المرتّبة (لعدّ الجلسات لا الأيّام التقويميّة)."""
    ix = {d: i for i, d in enumerate(sessions)}
    out, last = [], None
    for d in sorted(fire_days):
        i = ix.get(d)
        if i is None:
            continue
        if last is None or i - last > win:
            out.append(d)
        last = i
    return out


def exploded(rows, day, pct, win=WIN):
    """§⑥ المنفجر: أعلى High في الجلسات [D، D+win−1] ≥ إغلاق(D−1) × (1 + pct/100) · وD = أوّلُ جلسةٍ في اليوم أو بعده
    (يومُ تشغيلٍ في عطلةٍ يُقرأ جلسةَ القرار التالية). None إن نقصت الجلسات اللاحقة أو غاب D−1."""
    i = next((k for k, x in enumerate(rows) if x[0] >= day), None)
    if i is None or i < 1:
        return None
    fut = rows[i: i + win]
    if len(fut) < win:
        return None
    ref = rows[i - 1][4]
    if not ref or ref <= 0:
        return None
    return max(x[2] for x in fut) >= ref * (1 + pct / 100.0)


def rsi14_before(rows, day, rsi_fn):
    """RSI14 على إغلاقاتٍ قبل D حصرًا (‏`Super_stock.rsi` يُمرَّر · لا نسخة)."""
    closes = [x[4] for x in rows if x[0] < day]
    if len(closes) < 15:
        return None
    import pandas as pd
    v = float(rsi_fn(pd.Series(closes, dtype=float), 14).iloc[-1])
    return v if v == v else None


def band(r):
    return None if r is None else ("≤27" if r <= 27 else "27-33" if r <= 33 else ">33")


def gaps(rows, max_days=RECYCLE_GAP_DAYS):
    """§③ حارسُ إعادة تدوير الرمز: [(يومٌ، اليومُ التالي)] لكلّ شمعتين متتاليتين بينهما أكثرُ من `max_days` يومًا تقويميًّا."""
    out = []
    for a, b in zip(rows, rows[1:]):
        if (dt.date.fromisoformat(b[0]) - dt.date.fromisoformat(a[0])).days > max_days:
            out.append((a[0], b[0]))
    return out


def _gen5_ext():
    """حارسُ GEN5 بالاسم (`gen5_ext.split_unadjusted`) · يُحمَّل من مساره (لا نسخة)."""
    import importlib.util as iu
    spec = iu.spec_from_file_location("gen5_ext", os.path.join(ROOT, "fm_forensics", "gen5", "gen5_ext.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ── الشبكة ───────────────────────────────────────────────────────────────────────────────────────────
def _get(url, tries=3, timeout=20):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "t-rebuild/1"}), timeout=timeout) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:                     # noqa: PERF203
            if e.code in (403, 404):
                return e.code, b""
            time.sleep(2 ** k)
        except Exception:                                       # noqa: BLE001
            time.sleep(2 ** k)
    return None, b""


def _rows(df):
    return [(i.date().isoformat(), float(r.Open), float(r.High), float(r.Low), float(r.Close), float(r.Volume))
            for i, r in df.iterrows()]


def _first_sessions(months, MC):
    out = []
    for y, m in months:
        d = dt.date(y, m, 1)
        while not (d.weekday() < 5 and MC.session_info(d.isoformat()).get("open_ny_min") is not None):
            d += dt.timedelta(1)
        out.append(d.isoformat())
    return out


# ── الأوضاع ─────────────────────────────────────────────────────────────────────────────────────────
def mode_d0(key):
    sys.path.insert(0, ROOT)
    import market_calendar as MC
    import pit_universe as PU
    import pit_history as PH
    import pit_snapshot as PS
    res = {"mode": "d0"}
    months = [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
    snaps, union, types = {}, set(), {}
    for d in _first_sessions(months, MC):
        try:
            rows = PU.fetch_universe(d, key)
        except Exception as e:                                  # noqa: BLE001
            snaps[d] = {"error": f"{type(e).__name__}"}
            continue
        keep = [r["ticker"] for r in rows if r.get("type") in ("CS", "ADRC")]
        for r in rows:
            types[r.get("type")] = types.get(r.get("type"), 0) + 1
        snaps[d] = {"all": len(rows), "cs_adrc": len(keep)}
        union |= set(keep)
        log(f"d0 snapshot {d}: {len(rows)} · CS/ADRC {len(keep)}")
    res["snapshots"] = snaps
    res["union_cs_adrc"] = len(union)
    res["types_over_snapshots"] = types
    sp_by = {}
    try:
        sp = PS.fetch_all_splits(BARS_FROM, BARS_TO, key)
        res["splits"] = {"rows": len(sp), "reverse": sum(1 for r in sp if float(r.get("split_from") or 0) > float(r.get("split_to") or 0))}
        for r in sp:
            try:
                sp_by.setdefault(r["ticker"], []).append((r["execution_date"], float(r["split_to"]) / float(r["split_from"])))
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                continue
    except Exception as e:                                      # noqa: BLE001
        res["splits"] = {"error": f"{type(e).__name__}: {str(e)[:80]}"}
    log(f"d0 splits: {res['splits']}")
    G5 = _gen5_ext()
    sample = random.Random(SEED).sample(sorted(union), min(200, len(union)))
    ok, lens, diag = 0, [], {}
    gap_syms, gap_n, su_syms, su_n = 0, 0, 0, 0
    for s in sample:
        df, why = PH.polygon_daily(s, BARS_FROM, BARS_TO, key)
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        if df is not None and len(df) >= 60:
            ok += 1
            lens.append(len(df))
            rows = _rows(df)
            g = gaps(rows)
            gap_syms += bool(g)
            gap_n += len(g)
            u = G5.split_unadjusted(rows, sp_by.get(s), BARS_FROM, BARS_TO)
            su_syms += bool(u)
            su_n += len(u)
    res["bars_sample"] = {"n": len(sample), "ok_60plus": ok, "share": round(ok / max(1, len(sample)), 4),
                          "median_len": st.median(lens) if lens else None, "diag": diag}
    res["guards_sample"] = {"recycle_gap_days": RECYCLE_GAP_DAYS, "symbols_with_gap": gap_syms, "gaps": gap_n,
                            "symbols_split_unadjusted": su_syms, "split_unadjusted_days": su_n, "of_symbols_with_bars": ok}
    log(f"d0 bars sample: {ok}/{len(sample)} with ≥60 bars · diag {diag}")
    log(f"d0 guards on the sample: {res['guards_sample']}")
    finra = {}
    for d in ("2023-01-03", "2023-06-15", "2023-11-01"):
        code, body = _get(f"https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d.replace('-', '')}.txt")
        finra[d] = {"http": code, "lines": body.count(b"\n")}
    res["finra"] = finra
    log(f"d0 FINRA: {finra}")
    so, so_ok = random.Random(SEED + 1).sample(sorted(union), min(50, len(union))), 0
    for s in so:
        code, body = _get(f"https://api.polygon.io/v3/reference/tickers/{s}?date=2024-06-03&apiKey={key}")
        try:
            v = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
        except Exception:                                       # noqa: BLE001
            v = None
        so_ok += v is not None
    res["float_proxy"] = {"n": len(so), "with_value": so_ok}
    log(f"d0 float proxy (share_class_shares_outstanding @2024-06-03): {so_ok}/{len(so)}")
    res["coverage_floor"] = COVERAGE_FLOOR
    res["verdict_d0"] = "OK" if res["bars_sample"]["share"] >= COVERAGE_FLOOR else "NO_MEASURE (coverage)"
    return res


def mode_ready117(key):
    sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "1")
    import pit_history as PH
    import Super_stock as S
    pct = float(S.CONFIG["EXPLOSION_PCT"])
    ready = list(csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "READY_NOW_OUTCOMES.csv"), encoding="utf-8")))
    missed = [r for r in csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "READY_NOW_MISSED_SIGNALS.csv"), encoding="utf-8"))
              if r["READY_CLASS"] == "MISSED_READY"]
    syms = sorted({r["symbol"] for r in ready} | {r["SYMBOL"] for r in missed})
    bars, diag = {}, {}
    for s in syms:
        df, why = PH.polygon_daily(s, "2025-12-01", "2026-10-27", key)
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        if df is not None:
            bars[s] = _rows(df)
    out = {"mode": "ready117", "explosion_pct": pct, "symbols": len(syms), "with_bars": len(bars), "diag": diag}
    tab_r = {}
    rows_r = []
    for r in ready:
        b = bars.get(r["symbol"]) or []
        v = rsi14_before(b, r["first_ready"], S.rsi)
        y = exploded(b, r["first_ready"], pct)
        rows_r.append({"symbol": r["symbol"], "first_ready": r["first_ready"], "rsi14": None if v is None else round(v, 2),
                       "band": band(v), "exploded": y, "outcome": r["outcome"]})
        t = tab_r.setdefault(band(v) or "UNKNOWN", {"n": 0, "exploded": 0, "not": 0, "unknown_label": 0})
        t["n"] += 1
        t["exploded" if y else ("not" if y is False else "unknown_label")] += 1
    tab_m = {}
    rows_m = []
    for r in missed:
        b = bars.get(r["SYMBOL"]) or []
        v = rsi14_before(b, r["EXPL_DATE"], S.rsi)
        rows_m.append({"symbol": r["SYMBOL"], "expl_date": r["EXPL_DATE"], "rsi14": None if v is None else round(v, 2), "band": band(v),
                       "blocking_layer": r["BLOCKING_LAYER"]})
        tab_m[band(v) or "UNKNOWN"] = tab_m.get(band(v) or "UNKNOWN", 0) + 1
    out.update({"ready_table": tab_r, "missed_table": tab_m, "ready_rows": rows_r, "missed_rows": rows_m})
    log("ready117 READY by band: " + json.dumps(tab_r, ensure_ascii=False))
    log("ready117 MISSED by band: " + json.dumps(tab_m, ensure_ascii=False))
    return out


# ── §⑥ الأساس (`bases`) — ثلاثُ مراحل على رنرات: prep ⟵ shards ⟵ assemble ─────────────────────────────────
SESS_FROM = "2022-12-01"       # إحماءٌ: انطلاقاتُ ما قبل TRAIN تفتح نافذةَ «الإدخال الجديد» ولا تُعَدّ إدخالًا
WARMUP_SNAPSHOT = "2022-12-01"  # لقطةُ عضويّة الإحماء وحدَه (خارج لقطات العقد الـ36 · لا تدخل أيَّ عدّ)
HISTORY_DAYS = 800             # §③ = نافذةُ الإنتاج: `analyze_ticker` يرى آخرَ 800 يومٍ تقويميّ قبل D
STALE_DAYS = 7                 # لا شمعةَ في الأيّام السبعة قبل D ⟵ ليس في كون يومِه (مُعلَنٌ في النتيجة · يُعَدّ)
NSHARDS = 20
BOOT_B = 2000                  # §④ بوتستراب عنقوديٌّ بالرمز · بذرة SEED
B2_RSI, B2_DROP, B2_HI = 33.0, 70.0, 252                 # §⑥ BASE2 بحرفه (`perf.py` · `score_test.py`)
OW_RSI, OW_JUMP, OW_VOLX, OW_LB = 20.0, 1.20, 3.0, 20    # §⑥ OWNER
RULES = ("BASE2", "OWNER", "CURRENT", "ORIGINAL")
VAL_MIN_BURDEN = 0.3           # §⑥ نصفُ الهدف (0.6 إدخالٍ/جلسة)
OUT = os.path.join(HERE, "out")
PROXY_URL = "https://api.polygon.io/v3/reference/tickers/{t}?date={d}&apiKey={k}"
FINRA_URL = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{d}.txt"   # مسارُ `Super_stock.finra_daily_short` نفسُه


def sessions_between(a, b, MC):
    out, d, end = [], dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    while d <= end:
        if d.weekday() < 5 and MC.session_info(d.isoformat()).get("open_ny_min") is not None:
            out.append(d.isoformat())
        d += dt.timedelta(1)
    return out


def base2_fire(rsi, c, h, i):
    """§⑥ BASE2 عند D = الصفّ i (شموعٌ قبل D وحدَها): RSI14(D−1) **أقلّ من** 33 ∧ هبوطُ إغلاق D−1 عن أعلى High في 252 جلسةً ≥ 70%."""
    if i < 15:
        return False
    hi = max(h[max(0, i - B2_HI): i])
    return rsi[i - 1] < B2_RSI and hi > 0 and (1.0 - c[i - 1] / hi) * 100.0 >= B2_DROP


def jump_at(c, v, k, lb=OW_LB):
    """§⑥ «قفزة» يومَ k: إغلاق(k)/إغلاق(k−1) ≥ 1.20 **أو** حجم(k) ≥ 3 × وسيط حجم [k−20، k−1]."""
    if k < 1:
        return False
    if c[k - 1] > 0 and c[k] / c[k - 1] >= OW_JUMP:
        return True
    if k < lb:
        return False
    return v[k] >= OW_VOLX * st.median(v[k - lb: k])


def owner_fire(rsi, c, v, i):
    """§⑥ OWNER عند D = الصفّ i: J = i−1 · RSI14 على إغلاقاتٍ حتى J−1 ≤ 20 ∧ قفزةٌ يومَ J ∧ لا قفزةَ في [J−20، J−1] (أوّلُ قفزة)."""
    j = i - 1
    if j - OW_LB < 1 or j - 1 < 14:
        return False
    return rsi[j - 1] <= OW_RSI and jump_at(c, v, j) and not any(jump_at(c, v, k) for k in range(j - OW_LB, j))


def row_guards(dates, i, d, unadj_days, gap_pairs):
    """§③ (split, gap) لـ D = d (و`i` أوّلُ صفٍّ في D أو بعده): تقسيمٌ عكسيٌّ غيرُ مسوّى في (D−800 يوم، D+19] · فجوةٌ أطولُ من 15 يومًا
    تتقاطع مع [D−60 يومًا، D+19] (التقاطعُ أشدُّ من «طرفاها داخل النافذة» — مُعلَن). وD+19 = آخرُ ما يوجد إن قصرت الشموع."""
    lo = (dt.date.fromisoformat(d) - dt.timedelta(HISTORY_DAYS)).isoformat()
    lo60 = (dt.date.fromisoformat(d) - dt.timedelta(60)).isoformat()
    hi = max(d, dates[min(i + WIN - 1, len(dates) - 1)])
    return any(lo < u <= hi for u in unadj_days), any(b > lo60 and a < hi for a, b in gap_pairs)


_STUB = {"short": {}}


def install_stubs(S):
    """بلا شبكةٍ ولا نظرٍ للأمام داخل `apply_short_gate`/`apply_float_gate`: Fintel غائبٌ تاريخيًّا · FINRA = ملفُّ D−1 المُمرَّر ·
    وياهو (الفلوتُ اليوم) مُستبدَلٌ بفراغٍ فالمجهولُ يمرّ كالإنتاج · والسجلُّ والانتظارُ صامتان."""
    import types
    S.fintel_short = lambda syms: {}
    S.finra_daily_short = lambda syms: dict(_STUB["short"])

    class _Tk:
        def __init__(self, s):
            self.info = {}
    S.yf = types.SimpleNamespace(Ticker=_Tk)
    S.log = lambda *a, **k: None

    class _T:
        def __getattr__(self, k):
            return getattr(time, k)

        @staticmethod
        def sleep(*a):
            return None
    S.time = _T()


def post_scan(S, r, short_vol, proxy):
    """CURRENT/ORIGINAL بعد `analyze_ticker` بمسار `scan_market` نفسِه: `apply_short_gate` ⟵ `apply_float_gate` ⟵ `classify_tier`
    (الدوالُّ الإنتاجيّة بالاسم · يلزم `install_stubs` قبلها)."""
    r = dict(r)
    r["soft_fails"] = list(r.get("soft_fails") or [])
    r["flags"] = list(r.get("flags") or [])
    r["float"] = proxy
    _STUB["short"] = {} if short_vol is None else {r["symbol"]: short_vol}
    res = S.apply_float_gate(S.apply_short_gate([r]))
    return any(S.classify_tier(x.get("soft_fails", [])) is not None for x in res)


def configs(S):
    """(الحيّة، الأصليّة): `S` مستوردٌ بـ`FAISAL_ONLY=0` ⟵ أرقامُ الكود قبل الظرف · والحيّةُ نسخةٌ عليها `apply_faisal_only` بالمفتاح 1
    (لا تمسّ `S.CONFIG`) — ولا قيمةَ افتراضيّةَ لدالّةٍ تُقرأ من `CONFIG` ولا ثابتَ مشتقًّا بعد التطبيق سوى `LIQ_TC_USD` (خارج المفاتيح)."""
    org = dict(S.CONFIG)
    cur = dict(org)
    cur["FAISAL_ONLY"] = 1
    S.apply_faisal_only(cur, log_fn=lambda *a: None)
    return cur, org


def with_config(S, cfg):
    S.CONFIG.clear()
    S.CONFIG.update(cfg)


def shard_symbol(sym, rows, splits_sym, member_days, prev_of, finra, proxy_fn, S, cfgs, pct, G5):
    """صفوفُ رمزٍ واحد: [[D، BASE2، OWNER، CURRENT، ORIGINAL، y]] حيث تنطلق قاعدةٌ واحدةٌ على الأقلّ · ومعها العدّادات.
    rows مسوّاةٌ بكلّ التقسيمات (Polygon) · وCURRENT/ORIGINAL على آخر 800 يومٍ قبل D **بمقياس D−1** (`asof_factor`)."""
    import bisect
    import pandas as pd
    cnt = {"rows": 0, "no_history": 0, "stale": 0, "excl_split": 0, "excl_gap": 0, "unlabeled": 0,
           "pass_cur": 0, "pass_org": 0, "fire": [0, 0, 0, 0]}
    out = []
    if not rows:
        return out, cnt
    dates = [x[0] for x in rows]
    c = [float(x[4]) for x in rows]
    h = [float(x[2]) for x in rows]
    v = [float(x[5]) for x in rows]
    rsi = [float(z) for z in S.rsi(pd.Series(c, dtype=float), 14).values]
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = gaps(rows)
    full = pd.DataFrame({"Open": [x[1] for x in rows], "High": h, "Low": [x[3] for x in rows], "Close": c, "Volume": v},
                        index=pd.to_datetime(dates))
    for d in member_days:
        i = bisect.bisect_left(dates, d)
        if i < 1:
            cnt["no_history"] += 1
            continue
        if (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > STALE_DAYS:
            cnt["stale"] += 1
            continue
        sp, gq = row_guards(dates, i, d, unadj, gp)
        if sp:
            cnt["excl_split"] += 1
            continue
        if gq:
            cnt["excl_gap"] += 1
            continue
        cnt["rows"] += 1
        y = exploded(rows, d, pct)
        cnt["unlabeled"] += y is None
        b2 = base2_fire(rsi, c, h, i)
        ow = owner_fire(rsi, c, v, i)
        lo = bisect.bisect_left(dates, (dt.date.fromisoformat(d) - dt.timedelta(HISTORY_DAYS)).isoformat())
        sub = full.iloc[lo:i]
        f = asof_factor(splits_sym, d)
        if f != 1.0:
            sub = sub.copy()
            sub[["Open", "High", "Low", "Close"]] *= f
            sub["Volume"] /= f
        fired = [b2, ow, False, False]
        res = []
        for k, cfg in ((2, cfgs[0]), (3, cfgs[1])):
            with_config(S, cfg)
            try:
                r = S.analyze_ticker(sym, sub)
            except Exception:                                   # noqa: BLE001
                r = None
            res.append((k, cfg, r))
        if any(r for _, _, r in res):
            prev = prev_of[d]
            short = (finra.get(prev) or {}).get(sym)
            proxy = proxy_fn(sym, prev)
            for k, cfg, r in res:
                if r:
                    cnt["pass_cur" if k == 2 else "pass_org"] += 1
                    with_config(S, cfg)
                    fired[k] = post_scan(S, r, short, proxy)
        for k in range(4):
            cnt["fire"][k] += bool(fired[k])
        if any(fired):
            out.append([d] + [int(bool(z)) for z in fired] + [y])
    with_config(S, cfgs[0])
    return out, cnt


def rule_entries(rows_by_sym, sess, period, k):
    """§⑥ إدخالاتُ القاعدة k الجديدة في الفترة: {(sym، D): y} — الانطلاقُ قبل الفترة (الإحماء) يفتح النافذةَ ولا يُعَدّ."""
    out = {}
    for sym, rws in rows_by_sym.items():
        fire = [r[0] for r in rws if r[1 + k]]
        ys = {r[0]: r[5] for r in rws}
        for d in new_entries(fire, sess):
            if period[0] <= d <= period[1]:
                out[(sym, d)] = ys.get(d)
    return out


def share_stats(ent, n_sess):
    lab = [y for y in ent.values() if y is not None]
    e = sum(1 for y in lab if y)
    return {"entries": len(ent), "burden": round(len(ent) / max(1, n_sess), 3), "labelled": len(lab), "exploded": e,
            "share": round(e / len(lab), 4) if lab else None, "unknown": len(ent) - len(lab)}


def boot_diff(ent_a, ent_b, seed=SEED, b=BOOT_B):
    """فاصلُ 95% لفرق الحصّة (a − b) ببوتستراب عنقوديٍّ بالرمز (يُسحب الرمزُ بكلّ صفوفه في القاعدتين)."""
    per = {}
    for j, ent in ((0, ent_a), (1, ent_b)):
        for (sym, _), y in ent.items():
            if y is None:
                continue
            p = per.setdefault(sym, [0, 0, 0, 0])
            p[2 * j] += 1
            p[2 * j + 1] += int(bool(y))
    syms = sorted(per)
    if not syms:
        return None
    rng = random.Random(seed)
    diffs = []
    for _ in range(b):
        la = ea = lb = eb = 0
        for _k in range(len(syms)):
            p = per[syms[rng.randrange(len(syms))]]
            la += p[0]
            ea += p[1]
            lb += p[2]
            eb += p[3]
        if la and lb:
            diffs.append(ea / la - eb / lb)
    if not diffs:
        return None
    diffs.sort()
    return [round(diffs[int(0.025 * len(diffs))], 4), round(diffs[min(len(diffs) - 1, int(0.975 * len(diffs)))], 4)]


def choose_base(stats, cis):
    """§⑥ BASE2 هو الأساس ما لم يتفوّق مرشّحٌ على VAL بفاصلٍ لا يلمس الصفر ∧ تقديرٍ نقطيٍّ أعلى على TRAIN ∧ عبءٍ على VAL ≥ 0.3/جلسة ·
    وإن تفوّق أكثرُ من واحد فالأعلى حصّةً على VAL."""
    b2t, ok = stats["TRAIN"]["BASE2"]["share"], []
    for r in RULES[1:]:
        ci, tr, va = cis.get(r), stats["TRAIN"][r]["share"], stats["VAL"][r]
        if ci and ci[0] > 0 and tr is not None and b2t is not None and tr > b2t and va["burden"] >= VAL_MIN_BURDEN:
            ok.append((va["share"], r))
    return max(ok)[1] if ok else "BASE2"


def _jdump(obj, path):
    import gzip
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, separators=(",", ":"))


def _jload(path):
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def mode_bases_prep(key, months=None, sess_from=SESS_FROM, sess_to=None, all_from="2022-11-01", out="prep.json.gz",
                    tag="bases_prep"):
    """العضويّةُ الشهريّة (36 لقطةً ‏+ لقطةُ الإحماء) · التقسيماتُ بالرمز · وملفُّ FINRA لجلسة D−1 لكلّ D (للاتّحاد وحدَه) —
    والوسائطُ لـTEST وحدَه (`mode_test_prep`) · وافتراضُها سلوكُ bases بت-بت."""
    sys.path.insert(0, ROOT)
    import market_calendar as MC
    import pit_universe as PU
    import pit_snapshot as PS
    months = months or [(2022, 12)] + [(y, m) for y in (2023, 2024, 2025) for m in range(1, 13)]
    sess_to = sess_to or VAL[1]
    snaps, union = {}, set()
    for d in _first_sessions(months, MC):
        rows = PU.fetch_universe(d, key)
        keep = sorted(r["ticker"] for r in rows if r.get("type") in ("CS", "ADRC"))
        snaps[d[:7]] = keep
        union |= set(keep)
        log(f"prep snapshot {d}: CS/ADRC {len(keep)}")
    sp_by = {}
    for r in PS.fetch_all_splits(BARS_FROM, BARS_TO, key):
        try:
            if r["ticker"] in union:
                sp_by.setdefault(r["ticker"], []).append([r["execution_date"], float(r["split_to"]) / float(r["split_from"])])
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    sess = sessions_between(sess_from, sess_to, MC)
    allsess = sessions_between(all_from, sess_to, MC)
    prev_of = {d: allsess[allsess.index(d) - 1] for d in sess}
    finra, miss = {}, []
    for p in sorted(set(prev_of.values())):
        code, body = _get(FINRA_URL.format(d=p.replace("-", "")), timeout=40)
        txt = body.decode("utf-8", "replace") if code == 200 else ""
        if "|" not in txt[:200]:
            miss.append(p)
            continue
        m = {}
        for ln in txt.splitlines()[1:]:                      # تحليلُ `finra_daily_short` بحرفه: الحقلُ الثاني رمزٌ والثالثُ حجمُ الشورت
            q = ln.split("|")
            if len(q) >= 5 and q[1] in union and q[1] not in m:
                try:
                    m[q[1]] = int(q[2])
                except ValueError:
                    pass
        finra[p] = m
    log(f"prep: union {len(union)} · splits for {len(sp_by)} symbols · sessions {len(sess)} · FINRA {len(finra)} files · missing {len(miss)}")
    prep = {"snapshots": snaps, "union": sorted(union), "splits": sp_by, "sessions": sess, "prev_of": prev_of, "finra": finra,
            "finra_missing": miss}
    _jdump(prep, os.path.join(OUT, out))
    return {"mode": tag, "union": len(union), "snapshots": {k: len(v) for k, v in snaps.items()}, "split_symbols": len(sp_by),
            "sessions": len(sess), "finra_files": len(finra), "finra_missing": miss}


def mode_bases_shard(key, shard, nshards, fetch_bars=None, fetch_proxy=None, prep=None):
    """رموزُ الشريحة `sorted(union)[shard::nshards]` ⟵ صفوفُ الانطلاق والعدّادات (لا شيءَ بعد VAL)."""
    prep = prep or _jload(os.path.join(OUT, "prep.json.gz"))
    if not prep["sessions"] or prep["sessions"][-1] > VAL[1]:
        raise ValueError("bases لا يلمس TEST: آخرُ جلسةٍ بعد VAL")
    sys.path.insert(0, ROOT)
    os.environ["FAISAL_ONLY"] = "0"                              # أرقامُ الكود قبل الظرف ⟵ والحيّةُ تُشتقّ منها (`configs`)
    import Super_stock as S
    import pit_history as PH
    cfgs = configs(S)
    install_stubs(S)
    G5 = _gen5_ext()
    pct = float(cfgs[0]["EXPLOSION_PCT"])
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            if fetch_proxy is not None:
                cache[(sym, day)] = fetch_proxy(sym, day)
            else:
                code, body = _get(PROXY_URL.format(t=sym, d=day, k=key))
                try:
                    cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
                except Exception:                               # noqa: BLE001
                    cache[(sym, day)] = None
        return cache[(sym, day)]

    syms = prep["union"][shard::nshards]
    rows_by, tot, diag = {}, {}, {}
    t0 = time.time()
    for n, sym in enumerate(syms):
        if fetch_bars is not None:
            rows = fetch_bars(sym)
            why = "ok" if rows else "empty"
        else:
            df, why = PH.polygon_daily(sym, BARS_FROM, BARS_TO, key)
            rows = _rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out, cnt = shard_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["prev_of"], prep["finra"], _proxy,
                                S, cfgs, pct, G5)
        if out:
            rows_by[sym] = out
        for k, val in cnt.items():
            tot[k] = [a + b for a, b in zip(tot.get(k, [0] * 4), val)] if isinstance(val, list) else tot.get(k, 0) + val
        if n % 25 == 0:
            log(f"shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · {tot}")
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "counts": tot,
           "proxy_calls": len(cache), "proxy_none": sum(1 for x in cache.values() if x is None), "rows": rows_by}
    if fetch_bars is None:
        _jdump(res, os.path.join(OUT, f"shard_{shard:02d}.json.gz"))
    return res


def mode_bases_assemble(shards=None, prep=None):
    """§⑥ الإدخالاتُ الجديدة · العبءُ · الحصّة · فاصلُ الفرق مع BASE2 على VAL · والاختيار — ولا TEST."""
    import glob
    prep = prep or _jload(os.path.join(OUT, "prep.json.gz"))
    if shards is None:
        shards = [_jload(p) for p in sorted(glob.glob(os.path.join(OUT, "**", "shard_*.json.gz"), recursive=True))]
    sess = prep["sessions"]
    rows_by, tot = {}, {}
    for sh in shards:
        if any(r[0] > VAL[1] for rws in sh["rows"].values() for r in rws):
            raise ValueError("bases لا يلمس TEST: صفٌّ بعد VAL")
        rows_by.update(sh["rows"])
        for k, val in sh["counts"].items():
            tot[k] = [a + b for a, b in zip(tot.get(k, [0] * 4), val)] if isinstance(val, list) else tot.get(k, 0) + val
    n_sess = {p: sum(1 for d in sess if a <= d <= b) for p, (a, b) in (("TRAIN", TRAIN), ("VAL", VAL))}
    ents = {p: {r: rule_entries(rows_by, sess, per, k) for k, r in enumerate(RULES)} for p, per in (("TRAIN", TRAIN), ("VAL", VAL))}
    stats = {p: {r: share_stats(ents[p][r], n_sess[p]) for r in RULES} for p in ents}
    cis = {r: boot_diff(ents["VAL"][r], ents["VAL"]["BASE2"]) for r in RULES[1:]}
    base = choose_base(stats, cis)
    words = ("الأداةُ تُعاد من ثلاث خطواتٍ لا أربعَ عشرة" if base == "OWNER" else
             f"OWNER لم يفز: حصّتُه على VAL {stats['VAL']['OWNER']['share']} مقابل BASE2 {stats['VAL']['BASE2']['share']} "
             f"وفاصلُ الفرق {cis.get('OWNER')} وعبؤه {stats['VAL']['OWNER']['burden']}/جلسة")
    return {"mode": "bases_assemble", "shards": len(shards), "symbols_with_fires": len(rows_by), "counts": tot, "sessions": n_sess,
            "stats": stats, "val_diff_ci_vs_base2": cis, "base": base, "owner_words": words}


# ── §⑨ الأزواج (B5) ثمّ §⑧ الدرجة والتجميد — الملحق 1 §②-§③ · TRAIN وحدَه ─────────────────────────────────
ADDENDUM = os.path.join(HERE, "T_REBUILD_ADDENDUM_1.md")
ADDENDUM_SHA = "1f2902c0c0832c9c094e6b53e7c8a3346ff2a913d88d92be164ff4b99964d3e3"           # بصمةُ الملحق 1 كما دُمج قبل الأداة (الأوضاعُ الجديدة ترفض 9 بغيرها)
BASES_DATA = os.path.join(HERE, "data", "bases_2026-10-28.json")
FREEZE = os.path.join(HERE, "data", "freeze_rebuild.json")
PAIRS = ("P1", "P1p", "P2", "P3")             # P1 · P1′ (أوّلُ قفزةٍ وحدَها) · P2 · P3 — m = 4
PAIR_WIN = 5                                  # I_P = زنادٌ في [D−5، D−1]
P2_STEP, P2_ABOVE, P2_RSI, P2_RSI_WIN = 1.02, 3, 27.0, 10
P3_VOLX, P3_LB, P3_DROP, P3_FALL, P3_WIN = 3.0, 20, 70.0, 0.80, 10
DIST_S = 0.25                                 # §⑧ s = 25% من مقدار العتبة (ثابتٌ مسبق)
L2_LAMBDA, IRLS_TOL, IRLS_MAX = 1.0, 1e-10, 100
THETA_RATE = 0.6                              # §⑧ ≈0.6 إدخالٍ جديد/جلسة
ADD_BURDEN = 0.15                             # §⑦ «تضيف» تشترط عبءَ الأساس ∧ P على TRAIN ≥ 0.15/جلسة
PRICE_BINS = (1.0, 3.0, 10.0, 20.0)           # §⑦ أقلّ من 1 · 1-3 · 3-10 · 10-20 · 20 فأكثر
FLOAT_BINS = (10e6, 50e6)                     # §⑦ أقلّ من 10م · 10-50م · 50م فأكثر · ومجهول = 3


def addendum_ok():
    """الأوضاعُ الجديدة لا تعمل إلّا والملحقُ 1 بالبصمة التي دُمجت (التعريفاتُ قبل الرقم)."""
    import hashlib
    try:
        with open(ADDENDUM, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest() == ADDENDUM_SHA
    except OSError:
        return False


def price_bin(p):
    if p is None or p != p:
        return None
    return sum(1 for b in PRICE_BINS if p >= b)


def float_bin(f):
    try:
        f = float(f)
    except (TypeError, ValueError):
        return 3
    if f != f:
        return 3
    return sum(1 for b in FLOAT_BINS if f >= b)


def jumps(c, v):
    """`jump_at` لكلّ يوم (مرّةً واحدة)."""
    return [jump_at(c, v, k) for k in range(len(c))]


def p1_days(rsi, J):
    """P1 يومَ t = زنادُ OWNER نفسُه (`owner_fire` عند D = t+1): RSI14(t−1) ≤ 20 ∧ قفزةٌ يومَ t ∧ لا قفزةَ في [t−20، t−1]."""
    return {t for t in range(len(J)) if t - OW_LB >= 1 and t - 1 >= 14 and rsi[t - 1] <= OW_RSI and J[t]
            and not any(J[t - OW_LB: t])}


def p1p_days(J):
    """P1′ = «أوّلُ قفزة» وحدَها (بلا شرط RSI)."""
    return {t for t in range(len(J)) if t - OW_LB >= 1 and J[t] and not any(J[t - OW_LB: t])}


def p2_days(rsi, c, low, S):
    """P2 يومَ t: L = `S.tested_level` على شموعٍ حتى t−1 · الإغلاقاتُ t−3..t−1 فوق L · إغلاق(t−1) أقلُّ من L×1.02 ≤ إغلاق(t) ·
    أدنى RSI14 في [t−10، t−1] ≤ 27 (الملحق 1 §②)."""
    import pandas as pd
    out = set()
    for t in range(max(P2_ABOVE, P2_RSI_WIN, 3), len(c)):
        rw = [x for x in rsi[t - P2_RSI_WIN: t] if x == x]
        if not rw or min(rw) > P2_RSI or not c[t] > c[t - 1]:
            continue
        tl = S.tested_level(pd.DataFrame({"Low": low[max(0, t - 30): t]}))
        if not tl:
            continue
        lv = float(tl["level"])
        if all(x > lv for x in c[t - P2_ABOVE: t]) and c[t - 1] < lv * P2_STEP <= c[t]:
            out.add(t)
    return out


def p3_days(c, h, v):
    """P3: سبايكٌ يومَ k (حجم ≥ 3× وسيط [k−20، k−1] ∧ هبوطُ إغلاق(k) عن أعلى High في 252 قبله ≥ 70%) ⟵ الزنادُ أوّلُ t في (k، k+10]
    بإغلاق ≤ 0.80 × إغلاق(k)."""
    out = set()
    for k in range(P3_LB, len(c)):
        hi = max(h[max(0, k - B2_HI): k])
        if not (hi > 0 and (1.0 - c[k] / hi) * 100.0 >= P3_DROP and v[k] >= P3_VOLX * st.median(v[k - P3_LB: k])):
            continue
        for t in range(k + 1, min(len(c), k + P3_WIN + 1)):
            if c[t] <= P3_FALL * c[k]:
                out.add(t)
                break
    return out


def pair_flags(trig, i):
    """I_P لـ D = الصفّ i: زنادٌ في [D−5، D−1] = الشموعُ i−5..i−1 (لا D نفسُه ولا ما قبل i−5)."""
    return [int(any(t in tp for t in range(i - PAIR_WIN, i))) for tp in trig]


def base2_dist(rsi, c, h, i):
    """§⑧ مسافتا شرطَي BASE2 عند D = الصفّ i: (d_rsi، d_drop) — 1 إن عبر · وإلّا max(0، 1 − |x − العتبة| / s) و s = 25% من العتبة."""
    if i < 15 or rsi[i - 1] != rsi[i - 1]:
        return 0.0, 0.0
    r = rsi[i - 1]
    hi = max(h[max(0, i - B2_HI): i])
    if not hi > 0:
        return 0.0, 0.0
    dp = (1.0 - c[i - 1] / hi) * 100.0
    d_r = 1.0 if r < B2_RSI else max(0.0, 1.0 - abs(r - B2_RSI) / (DIST_S * B2_RSI))
    d_d = 1.0 if dp >= B2_DROP else max(0.0, 1.0 - abs(dp - B2_DROP) / (DIST_S * B2_DROP))
    return d_r, d_d


def pairs_symbol(sym, rows, splits_sym, member_days, sess, S, G5, pct, proxy_fn, prev_of):
    """صفوفُ البِركة لرمز (من الإحماء حتى نهاية TRAIN) بحرّاس `shard_symbol` نفسِها:
    [sym، D، y، إدخالُ الأساس الجديد، d_rsi، d_drop، I_P1، I_P1′، I_P2، I_P3، خانةُ السعر، خانةُ الفلوت (للإدخالات وحدَها)]."""
    import bisect
    import pandas as pd
    if not rows:
        return []
    dates = [x[0] for x in rows]
    c = [float(x[4]) for x in rows]
    h = [float(x[2]) for x in rows]
    low = [float(x[3]) for x in rows]
    v = [float(x[5]) for x in rows]
    rsi = [float(z) for z in S.rsi(pd.Series(c, dtype=float), 14).values]
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = gaps(rows)
    J = jumps(c, v)
    trig = (p1_days(rsi, J), p1p_days(J), p2_days(rsi, c, low, S), p3_days(c, h, v))
    keep, fire = [], []
    for d in member_days:
        if d > TRAIN[1]:
            break
        i = bisect.bisect_left(dates, d)
        if i < 1 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > STALE_DAYS:
            continue
        sp, gq = row_guards(dates, i, d, unadj, gp)
        if sp or gq:
            continue
        if base2_fire(rsi, c, h, i):
            fire.append(d)
        dr, dd = base2_dist(rsi, c, h, i)
        if dr > 0 and dd > 0:
            keep.append((d, i, dr, dd))
    ents = set(new_entries(fire, sess))
    out = []
    for d, i, dr, dd in keep:
        ind = pair_flags(trig, i)
        ent = int(d in ents and TRAIN[0] <= d <= TRAIN[1])
        f = asof_factor(splits_sym, d)
        fb = float_bin(proxy_fn(sym, prev_of[d])) if ent else None
        out.append([sym, d, exploded(rows, d, pct) if d >= TRAIN[0] else None, ent, round(dr, 6), round(dd, 6)] + ind
                   + [price_bin(c[i - 1] * f), fb])
    return out


def mh_rr(y, p, strat, w):
    """خطرٌ نسبيٌّ Mantel-Haenszel لـ y بين p=1 وp=0 في الطبقات (أوزانُ الصفوف w) — None إن لم تُسهم طبقة."""
    import numpy as np
    k = int(strat.max()) + 1 if len(strat) else 0
    n1 = np.bincount(strat, weights=w * p, minlength=k)
    a = np.bincount(strat, weights=w * p * y, minlength=k)
    n0 = np.bincount(strat, weights=w * (1 - p), minlength=k)
    c = np.bincount(strat, weights=w * (1 - p) * y, minlength=k)
    nn = n1 + n0
    ok = (n1 > 0) & (n0 > 0)
    if not ok.any():
        return None
    num = float((a[ok] * n0[ok] / nn[ok]).sum())
    den = float((c[ok] * n1[ok] / nn[ok]).sum())
    return num / den if den > 0 else None


def gate_stats(rows, names, n_sess, seed=SEED, b=BOOT_B):
    """قاعدةُ §⑦ لكلّ عمود: rows = [sym، D، y، شهر/خانة سعر/خانة فلوت ⟵ (month، pbin، fbin)، [أعلام]] على وحدةٍ واحدة ·
    فرقُ الحصّة والخطرُ النسبيّ MH بفاصلي بونفيروني (m = len(names) · SE بوتستراب عنقوديٍّ بالرمز) والحكم."""
    import math
    import numpy as np
    from statistics import NormalDist
    m = len(names)
    z = NormalDist().inv_cdf(1 - 0.025 / m)
    if any(r[1] > TRAIN[1] for r in rows):
        raise ValueError("الأزواجُ لا تقرأ وسمَ VAL ولا TEST")
    lab = [r for r in rows if r[2] is not None]
    syms = sorted({r[0] for r in lab})
    si = {s: j for j, s in enumerate(syms)}
    sym_idx = np.array([si[r[0]] for r in lab], dtype=int)
    y = np.array([int(bool(r[2])) for r in lab], dtype=float)
    P = np.array([r[4] for r in lab], dtype=float).reshape(len(lab), m)
    keys = sorted({tuple(r[3]) for r in lab})
    ki = {kk: j for j, kk in enumerate(keys)}
    strat = np.array([ki[tuple(r[3])] for r in lab], dtype=int)

    def _stat(w):
        lw, ew = w.sum(), (w * y).sum()
        lg, eg = w @ P, (w * y) @ P
        with np.errstate(divide="ignore", invalid="ignore"):
            diff = np.where(lg > 0, eg / np.where(lg > 0, lg, 1) - ew / lw, np.nan)
        rr = [mh_rr(y, P[:, j], strat, w) for j in range(m)]
        return diff, np.array([math.log(x) if x and x > 0 else np.nan for x in rr])

    d0, l0 = _stat(np.ones(len(lab)))
    rng = np.random.default_rng(seed)
    bd, bl = [], []
    for _ in range(b):
        cnt = np.bincount(rng.integers(0, len(syms), len(syms)), minlength=len(syms)).astype(float)
        d, lr = _stat(cnt[sym_idx])
        bd.append(d)
        bl.append(lr)
    bd, bl = np.array(bd), np.array(bl)
    out = {}
    for j, g in enumerate(names):
        npass = int(sum(1 for r in rows if r[4][j]))
        nl = int(P[:, j].sum())
        sd = float(np.nanstd(bd[:, j], ddof=1)) if np.isfinite(bd[:, j]).sum() > 1 else None
        sl = float(np.nanstd(bl[:, j], ddof=1)) if np.isfinite(bl[:, j]).sum() > 1 else None
        diff = None if not np.isfinite(d0[j]) else float(d0[j])
        dci = None if diff is None or sd is None else [round(diff - z * sd, 4), round(diff + z * sd, 4)]
        rr = None if not np.isfinite(l0[j]) else math.exp(l0[j])
        rci = None if rr is None or sl is None else [round(math.exp(l0[j] - z * sl), 3), round(math.exp(l0[j] + z * sl), 3)]
        burden = round(npass / max(1, n_sess), 3)
        if nl == len(lab) or nl == 0:
            verdict = "لا تفرّق — لا مقارنة"
        elif dci and dci[0] > 0 and rci and rci[0] > 1 and burden >= ADD_BURDEN:
            verdict = "تضيف"
        elif dci and dci[1] < 0:
            verdict = "تنقص"
        else:
            verdict = "لا تفرّق"
        out[g] = {"pass": npass, "pass_labelled": nl, "exploded_pass": int((y * P[:, j]).sum()),
                  "share_pass": round(float((y * P[:, j]).sum() / nl), 4) if nl else None,
                  "diff": None if diff is None else round(diff, 4), "diff_ci": dci,
                  "mh_rr": None if rr is None else round(rr, 3), "mh_ci": rci, "burden": burden, "verdict": verdict,
                  "boot_nan": int((~np.isfinite(bl[:, j])).sum())}
    return {"m": m, "z": round(z, 4), "units": len(rows), "labelled": len(lab), "exploded": int(y.sum()),
            "base_share": round(float(y.mean()), 4) if len(y) else None, "symbols": len(syms), "strata": len(keys), "cols": out}


def fit_logistic(X, y, lam=L2_LAMBDA, tol=IRLS_TOL, it_max=IRLS_MAX):
    """L2 لوجستيّ بنيوتن (IRLS): −Σ loglik + (λ/2)‖w‖² والإزاحةُ بلا عقوبة ⟵ (w، b، الدورات)."""
    import numpy as np
    n, k = X.shape
    A = np.hstack([X, np.ones((n, 1))])
    beta = np.zeros(k + 1)
    pen = np.full(k + 1, lam)
    pen[-1] = 0.0
    for it in range(1, it_max + 1):
        p = 1.0 / (1.0 + np.exp(-(A @ beta)))
        g = A.T @ (p - y) + pen * beta
        H = (A * (p * (1 - p))[:, None]).T @ A + np.diag(pen)
        step = np.linalg.solve(H, g)
        beta = beta - step
        if float(np.max(np.abs(step))) < tol:
            break
    return beta[:-1], float(beta[-1]), it


def entries_rate(score_rows, theta, sess, n_sess):
    """عددُ «الإدخالات الجديدة» على TRAIN ÷ جلساته عند θ (`new_entries` نفسُها · الإحماءُ يفتح النافذةَ ولا يُعَدّ)."""
    by = {}
    for sym, d, s in score_rows:
        if s >= theta:
            by.setdefault(sym, []).append(d)
    n = sum(1 for fs in by.values() for d in new_entries(sorted(fs), sess) if TRAIN[0] <= d <= TRAIN[1])
    return n / max(1, n_sess), n


def find_theta(score_rows, sess, n_sess, rate=THETA_RATE):
    """θ بالتنصيف على القيم الفريدة المرتّبة: أصغرُ قيمةٍ عبؤها ≤ rate (العبءُ شبهُ رتيب) — ويُطبع العبءُ عندها وعند سابقتها."""
    u = sorted({s for _, _, s in score_rows})
    if not u:
        return None
    lo, hi = 0, len(u) - 1
    if entries_rate(score_rows, u[hi], sess, n_sess)[0] > rate:
        return {"theta": None, "why": "حتى أعلى درجةٍ عبؤها فوق الهدف"}
    while lo < hi:
        mid = (lo + hi) // 2
        if entries_rate(score_rows, u[mid], sess, n_sess)[0] <= rate:
            hi = mid
        else:
            lo = mid + 1
    r_at, n_at = entries_rate(score_rows, u[lo], sess, n_sess)
    r_prev = entries_rate(score_rows, u[lo - 1], sess, n_sess)[0] if lo > 0 else None
    return {"theta": u[lo], "rate": round(r_at, 4), "entries": n_at, "rate_prev": None if r_prev is None else round(r_prev, 4),
            "unique": len(u)}


def freeze_sha(fz):
    import hashlib
    body = {k: v for k, v in fz.items() if k != "sha"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def mode_pairs_shard(key, shard, nshards, fetch_bars=None, fetch_proxy=None, prep=None):
    """رموزُ الشريحة ⟵ صفوفُ بِركة TRAIN بمؤشّرات الأزواج ومسافتي الأساس (لا شيءَ بعد TRAIN)."""
    prep = prep or _jload(os.path.join(OUT, "prep.json.gz"))
    sys.path.insert(0, ROOT)
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    import pit_history as PH
    live, _ = configs(S)
    G5 = _gen5_ext()
    pct = float(live["EXPLOSION_PCT"])
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    calls = {"proxy": 0, "proxy_none": 0}

    def _proxy(sym, day):
        calls["proxy"] += 1
        if fetch_proxy is not None:
            v = fetch_proxy(sym, day)
        else:
            code, body = _get(PROXY_URL.format(t=sym, d=day, k=key))
            try:
                v = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
            except Exception:                                   # noqa: BLE001
                v = None
        calls["proxy_none"] += v is None
        return v

    out, diag = [], {}
    syms = prep["union"][shard::nshards]
    t0 = time.time()
    for n, sym in enumerate(syms):
        if fetch_bars is not None:
            rows = fetch_bars(sym)
            why = "ok" if rows else "empty"
        else:
            df, why = PH.polygon_daily(sym, BARS_FROM, BARS_TO, key)
            rows = _rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out += pairs_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["sessions"], S, G5, pct, _proxy,
                            prep["prev_of"])
        if n % 25 == 0:
            log(f"pairs shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · rows {len(out)}")
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "calls": calls, "rows": out}
    if fetch_bars is None:
        _jdump(res, os.path.join(OUT, f"pairs_shard_{shard:02d}.json.gz"))
    return res


def mode_pairs_assemble(shards=None, prep=None, bases=None, seed=SEED, b=BOOT_B):
    """§⑨ حكمُ الأزواج على إدخالات الأساس ⟵ §⑧ الدرجةُ وθ ⟵ ملفُّ التجميد (يُدمج قبل TEST)."""
    import glob
    import numpy as np
    prep = prep or _jload(os.path.join(OUT, "prep.json.gz"))
    if bases is None:
        with open(BASES_DATA, encoding="utf-8") as fh:
            bases = json.load(fh)
    if shards is None:
        shards = [_jload(p) for p in sorted(glob.glob(os.path.join(OUT, "**", "pairs_shard_*.json.gz"), recursive=True))]
    rows = [r for sh in shards for r in sh["rows"]]
    if any(r[1] > TRAIN[1] for r in rows):
        raise ValueError("الأزواجُ والدرجةُ لا تلمس VAL ولا TEST")
    sess = prep["sessions"]
    n_sess = sum(1 for d in sess if TRAIN[0] <= d <= TRAIN[1])
    ents = [r for r in rows if r[3]]
    expect = bases["stats"]["TRAIN"][bases["base"]]["entries"]
    res = {"mode": "pairs_assemble", "base": bases["base"], "shards": len(shards), "pool_rows": len(rows),
           "entries": len(ents), "entries_expected": expect, "match": len(ents) == expect and bases["base"] == "BASE2",
           "train_sessions": n_sess}
    if not res["match"] or not shards or len(shards) != shards[0]["nshards"]:
        res["verdict"] = "⛔ لا حكم — الأساسُ ليس BASE2 أو عددُ الإدخالات أو الشرائح لا يطابق"
        return res
    units = [[r[0], r[1], r[2], (r[1][:7], r[10], r[11]), r[6:10]] for r in ents]
    ps = gate_stats(units, PAIRS, n_sess, seed=seed, b=b)
    res["pairs"] = ps
    surv = [g for g in PAIRS if ps["cols"][g]["verdict"] == "تضيف"]
    best13 = max(("P1", "P3"), key=lambda g: (ps["cols"][g]["diff"] if ps["cols"][g]["diff"] is not None else -9))
    res["p1_vs_p3"] = best13
    res["rsi20_words"] = ("RSI ≤ 20 أضاف فوق «أوّل قفزة»" if ps["cols"]["P1"]["verdict"] == "تضيف"
                          and ps["cols"]["P1p"]["verdict"] != "تضيف" else "RSI ≤ 20 لم يضف شيئًا")
    fcols = ["d_rsi", "d_drop"] + [f"I_{g}" for g in surv]
    idx = {"d_rsi": 4, "d_drop": 5, "I_P1": 6, "I_P1p": 7, "I_P2": 8, "I_P3": 9}
    lab = [r for r in rows if r[2] is not None and TRAIN[0] <= r[1]]
    X = np.array([[float(r[idx[f]]) for f in fcols] for r in lab], dtype=float)
    yv = np.array([int(bool(r[2])) for r in lab], dtype=float)
    mu, sd = X.mean(axis=0), X.std(axis=0)
    keep = [j for j in range(len(fcols)) if sd[j] > 0]
    dropped = [fcols[j] for j in range(len(fcols)) if sd[j] <= 0]
    fcols = [fcols[j] for j in keep]
    mu, sd = mu[keep], sd[keep]
    w, b0, it = fit_logistic((X[:, keep] - mu) / sd, yv)

    def _score(r):
        x = (np.array([float(r[idx[f]]) for f in fcols]) - mu) / sd
        return float(1.0 / (1.0 + np.exp(-(x @ w + b0))))
    srows = [(r[0], r[1], _score(r)) for r in rows]
    th = find_theta(srows, sess, n_sess)
    fz = {"contract": "T_REBUILD_prereg.md", "addendum_sha": ADDENDUM_SHA, "base": "BASE2", "pairs_in": surv,
          "features": fcols, "dropped_zero_sd": dropped, "mu": [float(x) for x in mu], "sd": [float(x) for x in sd],
          "w": [float(x) for x in w], "b": b0, "lambda": L2_LAMBDA, "iters": it, "n_fit": int(len(lab)),
          "theta": th.get("theta") if th else None, "theta_search": th, "dist_s": DIST_S}
    fz["sha"] = freeze_sha(fz)
    res["freeze"] = fz
    return res


# ── §⑩ القبول (B6) و§⑪ الرقم (B7) — TEST مرّةً واحدة بعد التجميد (الملحق 1 §④) ───────────────────────────────
TEST_WARM = "2024-12-01"                      # إحماءُ «الإدخال الجديد» على TEST (لقطةُ 2024-12 · لا تُعَدّ)
TEST_HALVES = (("2025-01-02", "2025-06-30"), ("2025-07-01", "2025-12-31"))
TEST_MIN_ENTRIES, TEST_MIN_EXPLODED = 100, 15      # §⑩ «لا قياس»
STOP_S5 = 0.95                                # §⑪ S5 = tested_level × 0.95
TEST_RESULT_GLOB = os.path.join(HERE, "data", "test_result_*.json")
PROD_OFF = (("M8_GAP_REQUIRED", "مطفأة (GAP_REQUIRED=False)"),
            ("STABILITY_BT (STABILITY_MIN رفضًا)", "مطفأة (BT_STABILITY_GATE فارغ: يُحسب ويُعرض ولا يرفض)"),
            ("STABILITY_MAX", "مطفأة (لا تُنفَّذ في أيّ ذراع)"),
            ("NEAR_READINESS", "مطفأة (NEAR_PCT=0)"),
            ("PIVOT_SWEEP_PCT", "عرضٌ فقط لا بوّابة"),
            ("RSI_OVERSOLD · RSI_MAX_NOW · MA_GATE_MAX_ABOVE_PCT", "ليّنة (نقصٌ يُعَدّ في WATCH_MAX_FAILS · لا رفضَ وحدَها)"),
            ("M13_SHORT", "ليّنة (نقصٌ لا رفض)"),
            ("BORROW_AVAIL_MAX", "حيّةٌ في الإنتاج · لم تُقَس هنا (لا تاريخ)"))


def freeze_load(path=FREEZE):
    """ملفُّ التجميد ببصمته وبصمةِ الملحق ⟵ dict أو None."""
    try:
        with open(path, encoding="utf-8") as fh:
            fz = json.load(fh)
    except (OSError, ValueError):
        return None
    if fz.get("sha") != freeze_sha(fz) or fz.get("addendum_sha") != ADDENDUM_SHA or fz.get("theta") is None:
        return None
    return fz


def frozen_score(fz, d_rsi, d_drop, flags):
    """الدرجةُ المجمَّدة لصفٍّ من البِركة (المسافتان ‏+ أعلامُ الأزواج الداخلة بأسمائها)."""
    import math
    val = {"d_rsi": d_rsi, "d_drop": d_drop, "I_P1": flags[0], "I_P1p": flags[1], "I_P2": flags[2], "I_P3": flags[3]}
    s = fz["b"] + sum(w * (float(val[f]) - m) / sd for f, w, m, sd in zip(fz["features"], fz["w"], fz["mu"], fz["sd"]))
    return 1.0 / (1.0 + math.exp(-s))


def stop_outcome(rows, i, stop, pct, win=WIN):
    """§⑪ لصفّ D = i: «بلغ ‏+50% قبل أن يلمس الوقف» على [D، D+19] (يومُ اللمستين ⟵ الوقفُ أوّلًا) — True/False · None بلا وقفٍ أو بلا 20 جلسة."""
    if stop is None or i < 1 or i + win > len(rows):
        return None
    tgt = float(rows[i - 1][4]) * (1 + pct / 100.0)
    for k in range(i, i + win):
        lo, hi = float(rows[k][3]), float(rows[k][2])
        if lo <= stop:
            return False
        if hi >= tgt:
            return True
    return False


def test_symbol(sym, rows, splits_sym, member_days, sess, prev_of, finra, proxy_fn, S, cfg_live, pct, G5, fz):
    """صفوفُ TEST لرمز (من الإحماء): [sym، D، y، BASE2، CURRENT، الجديدة، الدرجة، S0، S5] حيث تنطلق قائمةٌ واحدةٌ على الأقلّ."""
    import bisect
    import pandas as pd
    if not rows:
        return []
    dates = [x[0] for x in rows]
    c = [float(x[4]) for x in rows]
    h = [float(x[2]) for x in rows]
    low = [float(x[3]) for x in rows]
    v = [float(x[5]) for x in rows]
    rsi = [float(z) for z in S.rsi(pd.Series(c, dtype=float), 14).values]
    unadj = G5.split_unadjusted(rows, splits_sym, "0000-00-00", "9999-99-99")
    gp = gaps(rows)
    J = jumps(c, v)
    trig = (p1_days(rsi, J), p1p_days(J), p2_days(rsi, c, low, S), p3_days(c, h, v))
    full = pd.DataFrame({"Open": [x[1] for x in rows], "High": h, "Low": low, "Close": c, "Volume": v},
                        index=pd.to_datetime(dates))
    out = []
    for d in member_days:
        if d > TEST[1]:
            break
        i = bisect.bisect_left(dates, d)
        if i < 1 or (dt.date.fromisoformat(d) - dt.date.fromisoformat(dates[i - 1])).days > STALE_DAYS:
            continue
        sp, gq = row_guards(dates, i, d, unadj, gp)
        if sp or gq:
            continue
        b2 = base2_fire(rsi, c, h, i)
        dr, dd = base2_dist(rsi, c, h, i)
        sc = frozen_score(fz, dr, dd, pair_flags(trig, i)) if dr > 0 and dd > 0 else None
        new = sc is not None and sc >= fz["theta"]
        lo = bisect.bisect_left(dates, (dt.date.fromisoformat(d) - dt.timedelta(HISTORY_DAYS)).isoformat())
        sub = full.iloc[lo:i]
        f = asof_factor(splits_sym, d)
        if f != 1.0:
            sub = sub.copy()
            sub[["Open", "High", "Low", "Close"]] *= f
            sub["Volume"] /= f
        with_config(S, cfg_live)
        try:
            r = S.analyze_ticker(sym, sub)
        except Exception:                                       # noqa: BLE001
            r = None
        cur = bool(r) and post_scan(S, r, (finra.get(prev_of[d]) or {}).get(sym), proxy_fn(sym, prev_of[d]))
        if not (b2 or cur or new):
            continue
        tl = S.tested_level(full.iloc[:i]) if new else None
        lv = float(tl["level"]) if tl else None
        out.append([sym, d, exploded(rows, d, pct), int(b2), int(cur), int(new), None if sc is None else round(sc, 6),
                    stop_outcome(rows, i, lv, pct) if new else None,
                    stop_outcome(rows, i, None if lv is None else lv * STOP_S5, pct) if new else None])
    return out


def boot_share(ent, seed=SEED, b=BOOT_B):
    """فاصلُ 95% لحصّة قائمةٍ واحدة ببوتستراب عنقوديٍّ بالرمز (§⑪ «من كلّ 10»)."""
    per = {}
    for (sym, _), y in ent.items():
        if y is None:
            continue
        p = per.setdefault(sym, [0, 0])
        p[0] += 1
        p[1] += int(bool(y))
    syms = sorted(per)
    if not syms:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(b):
        n_l = n_e = 0
        for _k in range(len(syms)):
            p = per[syms[rng.randrange(len(syms))]]
            n_l += p[0]
            n_e += p[1]
        if n_l:
            vals.append(n_e / n_l)
    vals.sort()
    return [round(vals[int(0.025 * len(vals))], 4), round(vals[min(len(vals) - 1, int(0.975 * len(vals)))], 4)]


def test_verdict(st_new, st_b2, st_cur, ci, halves, coverage):
    """§⑩ بنصّه: 4 «لا قياس» ⟵ 1 «تُقبل» ⟵ 2 «التعقيدُ لم يضف شيئًا» ⟵ 3 «لا يُقبل»."""
    if (st_new["entries"] < TEST_MIN_ENTRIES or st_new["exploded"] < TEST_MIN_EXPLODED or coverage is None
            or coverage < COVERAGE_FLOOR):
        return 4, "لا قياس"
    sn, sc = st_new["share"], st_cur["share"]                    # BASE2 يدخل الحكمَ بفاصل الفرق وبنصفَي 2025
    if ci and ci[0] > 0 and sc is not None and sn >= sc and all(x is not None and x > 0 for x in halves):
        return 1, "تُقبل"
    if sc is not None and sn > sc:
        return 2, "التعقيدُ لم يضف شيئًا"
    return 3, "لا يُقبل"


def mode_test_shard(key, shard, nshards, fetch_bars=None, fetch_proxy=None, prep=None, fz=None):
    """رموزُ الشريحة على TEST بالدرجة المجمَّدة (لا شيءَ قبل الإحماء ولا بعد 2025)."""
    fz = fz or freeze_load()
    if fz is None:
        raise ValueError("لا تجميدَ ببصمته ⟵ لا TEST")
    prep = prep or _jload(os.path.join(OUT, "test_prep.json.gz"))
    sys.path.insert(0, ROOT)
    os.environ["FAISAL_ONLY"] = "0"
    import Super_stock as S
    import pit_history as PH
    live, _ = configs(S)
    install_stubs(S)
    G5 = _gen5_ext()
    pct = float(live["EXPLOSION_PCT"])
    member = {}
    for d in prep["sessions"]:
        for s in prep["snapshots"].get(d[:7], []):
            member.setdefault(s, []).append(d)
    cache = {}

    def _proxy(sym, day):
        if (sym, day) not in cache:
            if fetch_proxy is not None:
                cache[(sym, day)] = fetch_proxy(sym, day)
            else:
                code, body = _get(PROXY_URL.format(t=sym, d=day, k=key))
                try:
                    cache[(sym, day)] = json.loads(body or b"{}").get("results", {}).get("share_class_shares_outstanding")
                except Exception:                               # noqa: BLE001
                    cache[(sym, day)] = None
        return cache[(sym, day)]

    out, diag = [], {}
    syms = prep["union"][shard::nshards]
    t0 = time.time()
    for n, sym in enumerate(syms):
        if fetch_bars is not None:
            rows = fetch_bars(sym)
            why = "ok" if rows else "empty"
        else:
            df, why = PH.polygon_daily(sym, BARS_FROM, BARS_TO, key)
            rows = _rows(df) if df is not None else []
        diag[why.split("(")[0]] = diag.get(why.split("(")[0], 0) + 1
        out += test_symbol(sym, rows, prep["splits"].get(sym), member.get(sym, []), prep["sessions"], prep["prev_of"],
                           prep["finra"], _proxy, S, live, pct, G5, fz)
        if n % 25 == 0:
            log(f"test shard {shard}: {n + 1}/{len(syms)} · {round(time.time() - t0)}s · rows {len(out)}")
    with_config(S, live)
    res = {"shard": shard, "nshards": nshards, "symbols": len(syms), "bars_diag": diag, "proxy_calls": len(cache),
           "freeze_sha": fz["sha"], "rows": out}
    if fetch_bars is None:
        _jdump(res, os.path.join(OUT, f"test_shard_{shard:02d}.json.gz"))
    return res


def list_entries(rows, sess, k, period):
    """إدخالاتُ القائمة k (3 BASE2 · 4 CURRENT · 5 الجديدة) الجديدة في الفترة: {(sym، D): الصفّ}."""
    by, out = {}, {}
    for r in rows:
        if r[k]:
            by.setdefault(r[0], []).append(r)
    for sym, rs in by.items():
        days = {r[1]: r for r in rs}
        for d in new_entries(sorted(days), sess):
            if period[0] <= d <= period[1]:
                out[(sym, d)] = days[d]
    return out


def mode_test_assemble(shards=None, prep=None, fz=None):
    """§⑩ الحكم · §⑪ «من كلّ 10» وذراعا الوقف · وجدولُ المطفأ في الإنتاج — مرّةً واحدة."""
    import glob
    fz = fz or freeze_load()
    if fz is None:
        raise ValueError("لا تجميدَ ببصمته ⟵ لا TEST")
    prep = prep or _jload(os.path.join(OUT, "test_prep.json.gz"))
    if shards is None:
        shards = [_jload(p) for p in sorted(glob.glob(os.path.join(OUT, "**", "test_shard_*.json.gz"), recursive=True))]
    if not shards or len(shards) != shards[0]["nshards"] or any(sh["freeze_sha"] != fz["sha"] for sh in shards):
        return {"mode": "test_assemble", "verdict": "⛔ لا حكم — الشرائحُ ناقصةٌ أو بتجميدٍ آخر"}
    rows = [r for sh in shards for r in sh["rows"]]
    sess = prep["sessions"]
    n_sess = sum(1 for d in sess if TEST[0] <= d <= TEST[1])
    ents = {n: list_entries(rows, sess, k, TEST) for n, k in (("NEW", 5), ("BASE2", 3), ("CURRENT", 4))}
    lab = {n: {kk: r[2] for kk, r in e.items()} for n, e in ents.items()}
    st_ = {n: share_stats(lab[n], n_sess) for n in ents}
    ci = boot_diff(lab["NEW"], lab["BASE2"])
    halves = []
    for a, b in TEST_HALVES:
        hn = {kk: y for kk, y in lab["NEW"].items() if a <= kk[1] <= b}
        hb = {kk: y for kk, y in lab["BASE2"].items() if a <= kk[1] <= b}
        sn, sb = share_stats(hn, 1)["share"], share_stats(hb, 1)["share"]
        halves.append(None if sn is None or sb is None else round(sn - sb, 4))
    diag = {}
    for sh in shards:
        for kk, vv in sh["bars_diag"].items():
            diag[kk] = diag.get(kk, 0) + vv
    cov = diag.get("ok", 0) / max(1, sum(diag.values()))
    code, words = test_verdict(st_["NEW"], st_["BASE2"], st_["CURRENT"], ci, halves, cov)
    newl = [r for r in ents["NEW"].values()]
    s0 = [r[7] for r in newl if r[7] is not None]
    s5 = [r[8] for r in newl if r[8] is not None]
    ci10 = boot_share(lab["NEW"])
    sn = st_["NEW"]["share"]
    return {"mode": "test_assemble", "freeze_sha": fz["sha"], "sessions": n_sess, "coverage": round(cov, 4), "bars_diag": diag,
            "stats": st_, "diff_ci_new_vs_base2": ci, "halves_diff": halves, "branch": code, "verdict": words,
            "of10": None if sn is None else round(10 * sn, 2), "of10_ci": None if not ci10 else [round(10 * x, 2) for x in ci10],
            "stops": {"S0": {"n": len(s0), "hit50_first": sum(1 for x in s0 if x)},
                      "S5": {"n": len(s5), "hit50_first": sum(1 for x in s5 if x)},
                      "unknown_level": sum(1 for r in newl if r[7] is None)},
            "production_off": [list(x) for x in PROD_OFF]}


def mode_test_prep(key):
    """§⑩ عضويّةُ 2025 (‏+ لقطةُ الإحماء 2024-12) · التقسيمات · FINRA لجلسة D−1 — بـ`mode_bases_prep` نفسِها."""
    return mode_bases_prep(key, months=[(2024, 12)] + [(2025, m) for m in range(1, 13)], sess_from=TEST_WARM, sess_to=TEST[1],
                           all_from="2024-11-01", out="test_prep.json.gz", tag="test_prep")


def main():
    mode = os.environ.get("REBUILD_MODE", "").strip()
    key = os.environ.get("POLYGON_API_KEY", "")
    if not os.path.exists(CONTRACT):
        log("⛔ العقد غائب")
        return 9
    built = ("d0", "ready117", "bases_prep", "bases_shard", "bases_assemble", "pairs_shard", "pairs_assemble", "test_prep", "test_shard", "test_assemble")
    if mode not in built:
        log(f"⛔ وضعٌ غيرُ مبنيّ: {mode!r} (المبنيّ: {' · '.join(built)})")
        return 3
    if mode.startswith("test_"):
        import glob as _g
        if _g.glob(TEST_RESULT_GLOB):
            log("⛔ TEST قِيس مرّةً ونتيجتُه في data/ ⟵ لا إعادة (§⑩ «مرّةً واحدة»)")
            return 7
        if not addendum_ok() or freeze_load() is None:
            log("⛔ لا ملحقَ ببصمته أو لا تجميدَ ببصمته على main ⟵ لا TEST (الملحق 1 §③)")
            return 9
    if mode.startswith("pairs_") and not addendum_ok():
        log("⛔ الملحق 1 غائبٌ أو غيرُ بصمته المدموجة ⟵ لا جرد (التعريفاتُ قبل الرقم)")
        return 9
    if mode.startswith("pairs_"):
        with open(BASES_DATA, encoding="utf-8") as fh:
            _base = json.load(fh)["base"]
        if _base != "BASE2":
            log(f"⛔ الأساسُ {_base} ⟵ ملحقٌ ثانٍ قبل الدرجة (الملحق 1 §③)")
            return 3
    if not key and mode not in ("bases_assemble", "pairs_assemble", "test_assemble"):
        log("⛔ لا مفتاح Polygon")
        return 2
    t0 = time.time()
    if mode == "d0":
        res = mode_d0(key)
    elif mode == "ready117":
        res = mode_ready117(key)
    elif mode == "bases_prep":
        res = mode_bases_prep(key)
    elif mode == "bases_shard":
        res = mode_bases_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", str(NSHARDS))))
        res = {k: v for k, v in res.items() if k != "rows"}
    elif mode == "bases_assemble":
        res = mode_bases_assemble()
        _jdump(res, os.path.join(OUT, "bases_result.json.gz"))
    elif mode == "test_prep":
        res = mode_test_prep(key)
    elif mode == "test_shard":
        res = mode_test_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", str(NSHARDS))))
        res = {k: v for k, v in res.items() if k != "rows"} | {"rows_n": len(res["rows"])}
    elif mode == "test_assemble":
        res = mode_test_assemble()
        _jdump(res, os.path.join(OUT, "test_result.json.gz"))
    elif mode == "pairs_shard":
        res = mode_pairs_shard(key, int(os.environ.get("SHARD", "0")), int(os.environ.get("NSHARDS", str(NSHARDS))))
        res = {k: v for k, v in res.items() if k != "rows"} | {"entries": len(res["rows"])}
    else:
        res = mode_pairs_assemble()
        _jdump(res, os.path.join(OUT, "pairs_result.json.gz"))
    res["seconds"] = round(time.time() - t0, 1)
    print("REBUILD_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
