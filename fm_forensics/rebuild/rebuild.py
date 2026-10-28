# -*- coding: utf-8 -*-
"""🧭 `T-REBUILD` — إعادةُ بناء القبول من البيانات (العقد `fm_forensics/rebuild/T_REBUILD_prereg.md` · مدموجٌ قبل أيّ رقم).

قراءةٌ وقياسٌ فقط: لا يُستورَد في الإنتاج · لا يكتب حالةً · لا تلغرام · لا `LOGIC_VERSION` · ولا يُشحَن منه شيء (§⓪ · §⑫).

الأوضاع المبنيّة الآن (المراحل التالية تُضاف بعد قراءة أرقام هذه):
    REBUILD_MODE=d0        جدوى البيانات §③ — أعدادٌ فقط (اللقطات · الرموز · التغطية · الحرّاس على عيّنة الشموع · FINRA · وكيلُ الفلوت)
    REBUILD_MODE=ready117  جدولُ §⑤ — RSI14 للـ117 READY والـ277 MISSED_READY (وصفيّ · لا يختار شيئًا)

الدوالُّ النقيّة (مقفولةٌ سلوكيًّا في `RBD1`): `asof_scale` · `new_entries` · `exploded` · `rsi14_before` · `gaps` · `band`.
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
def asof_scale(rows, splits, day):
    """§③ التسويةُ بتاريخ القرار. rows = [(يوم ISO، o، h، l، c، v)] مسوّاةٌ بكلّ التقسيمات حتى الجلب ·
    splits = [(يوم التنفيذ ISO، نسبة to/from)] · day = يومُ القرار D. يُرجع الصفوف قبل D على **مقياس D−1**:
    السعرُ × ∏(النسبة) للتقسيمات المنفّذة في D أو بعده · والحجمُ ÷ الحاصل. صفوفُ D فصاعدًا لا تُرجع (لا نظرَ للأمام)."""
    f = 1.0
    for d, r in splits or []:
        if d >= day and r and r > 0:
            f *= float(r)
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


def main():
    mode = os.environ.get("REBUILD_MODE", "").strip()
    key = os.environ.get("POLYGON_API_KEY", "")
    if not os.path.exists(CONTRACT):
        log("⛔ العقد غائب")
        return 9
    if mode not in ("d0", "ready117"):
        log(f"⛔ وضعٌ غيرُ مبنيّ: {mode!r} (المبنيّ: d0 · ready117)")
        return 3
    if not key:
        log("⛔ لا مفتاح Polygon")
        return 2
    t0 = time.time()
    res = mode_d0(key) if mode == "d0" else mode_ready117(key)
    res["seconds"] = round(time.time() - t0, 1)
    print("REBUILD_JSON " + json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
