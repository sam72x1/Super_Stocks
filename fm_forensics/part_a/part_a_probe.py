"""Part A runner probe (read-only · no Telegram · no state writes · definitions in PART_A_DEFS.md written before any number).

Modes (env PART_A_MODE, comma-separated): a2 · a2b · a3 · a3b · vol · l2 · tape · all. Output: one JSON per mode under
fm_forensics/part_a/out/ and a compact summary printed with the prefix PAOUT (the job log is the evidence)."""
import os, sys, json, time, datetime as dt
from zoneinfo import ZoneInfo
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "out")
NY = ZoneInfo("America/New_York")
API = "https://api.polygon.io"
KEY = os.environ.get("POLYGON_API_KEY", "").strip()
CALLS = {"ok": 0, "fail": 0}
EXPLOSION_PCT = 50.0  # Super_stock.CONFIG["EXPLOSION_PCT"] — asserted at start


def log(*a):
    print(*a, flush=True)


def get(path, params=None, tries=3):
    params = dict(params or {}); params["apiKey"] = KEY
    last = ""
    for i in range(tries):
        try:
            r = requests.get(API + path, params=params, timeout=40)
            if r.status_code == 200:
                CALLS["ok"] += 1
                return r.json()
            if r.status_code == 429:
                time.sleep(2 + 2 * i); continue
            CALLS["fail"] += 1
            return {"_status": r.status_code, "_text": r.text[:300]}
        except Exception as e:  # noqa: BLE001
            time.sleep(1 + i)
            last = str(e)
    CALLS["fail"] += 1
    return {"_status": "EXC", "_text": last[:300]}


def daily(sym, d0, d1, adjusted=True):
    js = get(f"/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}", {"adjusted": "true" if adjusted else "false", "sort": "asc", "limit": "5000"})
    out = []
    for b in (js or {}).get("results") or []:
        d = dt.datetime.fromtimestamp(b["t"] / 1000, tz=NY).date().isoformat()
        out.append({"d": d, "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b.get("v", 0)})
    return out


def minutes(sym, day):
    js = get(f"/v2/aggs/ticker/{sym}/range/1/minute/{day}/{day}", {"adjusted": "true", "sort": "asc", "limit": "50000"})
    return [{"t": b["t"], "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b.get("v", 0)} for b in (js or {}).get("results") or []]


def trades(sym, t0_ns, t1_ns, cap=200000):
    out, url, params = [], f"/v3/trades/{sym}", {"timestamp.gte": str(t0_ns), "timestamp.lt": str(t1_ns), "limit": "50000", "sort": "timestamp", "order": "asc"}
    while url and len(out) < cap:
        js = get(url, params)
        res = (js or {}).get("results")
        if res is None:
            return out if out else js
        out += res
        nxt = js.get("next_url")
        if not nxt:
            break
        url, params = nxt.replace(API, ""), {}
    return out


def rsi_wilder(closes, period=14):
    """Super_stock.rsi itself (Wilder ewm · NaN→50) on closes up to d−1 — the production formula, not a copy."""
    if len(closes) < period + 1:
        return None
    import pandas as pd
    import Super_stock as S
    return float(S.rsi(pd.Series(closes, dtype=float), period).iloc[-1])


def ny_ms(day, hh, mm, ss=0):
    return int(dt.datetime(*map(int, day.split("-")), hh, mm, ss, tzinfo=NY).timestamp() * 1000)


def save(name, obj):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=0, sort_keys=True)


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


# ------------------------------------------------------------------ A2 (D1)
def replay_first(bars, prev_close):
    """D1 cause ④: the production `liq_stage_events` replayed minute by minute on the day's bars with a fresh state —
    T-C on (yesterday's close), no operator gate, no alert filter, positional closed-bar rule (`kasih_scan.first_anchor`).
    Returns the earliest anchor the definition itself allows: (anchor_ms, price, trig) or None."""
    import Super_stock as S
    st, win = {}, int(S.LIQ_WINDOW_MIN)
    for k in range(3, len(bars) + 1):
        tc = None
        if S.LIQ_TC_ON and prev_close and not st.get("anchor_ms"):
            tc = {"usd": S.LIQ_TC_USD, "pct": S.LIQ_TC_PCT, "prev_close": float(prev_close)}
        evs, st = S.liq_stage_events(bars[max(0, k - win):k], st, tc=tc)
        if any((e or {}).get("stage") == "M1" for e in (evs or [])):
            m1 = next(e for e in evs if (e or {}).get("stage") == "M1")
            return (st.get("anchor_ms"), m1.get("price"), st.get("trig"))
    return None


def mode_a2():
    A = json.load(open(os.path.join(HERE, "in", "anchors.json")))["anchors"]
    A = [a for a in A if a.get("sent") and a.get("day", "") >= "2026-10-14"]   # D1: from 2026-10-14
    rows, cache = [], {}
    for a in sorted(A, key=lambda x: (x["day"], x["anchor_ms"])):
        k = (a["sym"], a["day"])
        if k not in cache:
            cache[k] = minutes(a["sym"], a["day"])
        bars = cache[k]
        ta = int(a["anchor_ms"])
        before = [b for b in bars if b["t"] < ta]
        p15 = [b for b in bars if b["t"] <= ta - 15 * 60000]
        if ("D",) + k not in cache:
            cache[("D",) + k] = daily(a["sym"], (dt.date.fromisoformat(a["day"]) - dt.timedelta(days=10)).isoformat(), a["day"])
        dly = cache[("D",) + k]
        prev = [b for b in dly if b["d"] < a["day"]]
        px = a.get("anchor_price")
        r = {"sym": a["sym"], "day": a["day"], "t_alert_ny": dt.datetime.fromtimestamp(ta / 1000, tz=NY).strftime("%H:%M"),
             "alert_px": px, "trig": a.get("trig") or "R1", "first_seen": a.get("first_seen"),
             "lag_min": round((dt.datetime.fromisoformat(a["first_seen"]).timestamp() * 1000 - ta) / 60000, 1) if a.get("first_seen") else None,
             "px_15": p15[-1]["c"] if p15 else None, "peak_before": max((b["h"] for b in before), default=None),
             "low_before": min((b["l"] for b in before), default=None), "prev_close": prev[-1]["c"] if prev else None,
             "n_bars": len(bars)}
        f = lambda den: (round((px / den - 1) * 100, 1) if (px and den) else None)
        r["missed_15"], r["missed_prev"], r["missed_low"] = f(r["px_15"]), f(r["prev_close"]), f(r["low_before"])
        r["past_peak"] = (r["peak_before"] is not None and px is not None and r["peak_before"] > px)
        if ("R",) + k not in cache:                       # the replay once per (sym, day)
            try:
                cache[("R",) + k] = replay_first(bars, r["prev_close"])
            except Exception as e:  # noqa: BLE001
                cache[("R",) + k] = ("ERR", str(e)[:120], None)
        rp = cache[("R",) + k]
        first_live = min(int(x["anchor_ms"]) for x in A if (x["sym"], x["day"]) == k)
        r["is_first_live"] = (ta == first_live)
        if rp and rp[0] not in (None, "ERR"):
            r["replay_t_ny"] = dt.datetime.fromtimestamp(rp[0] / 1000, tz=NY).strftime("%H:%M")
            r["replay_px"], r["replay_trig"] = rp[1], rp[2] or "R1"
            r["deferral_min"] = round((first_live - rp[0]) / 60000, 1)
            r15 = [b for b in bars if b["t"] <= rp[0] - 15 * 60000]
            r["replay_missed_15"] = round((rp[1] / r15[-1]["c"] - 1) * 100, 1) if (r15 and rp[1]) else None
        else:
            r["replay_t_ny"] = None if not rp else "ERR"
        rows.append(r)
    summ = {"n": len(rows), "median_missed_15": median([r["missed_15"] for r in rows]),
            "median_missed_prev": median([r["missed_prev"] for r in rows]), "median_missed_low": median([r["missed_low"] for r in rows]),
            "median_lag_min": median([r["lag_min"] for r in rows]),
            "by_trig": {t: {"n": sum(1 for r in rows if r["trig"] == t),
                            "median_missed_15": median([r["missed_15"] for r in rows if r["trig"] == t]),
                            "median_missed_prev": median([r["missed_prev"] for r in rows if r["trig"] == t])} for t in sorted({r["trig"] for r in rows})},
            "past_peak": sum(1 for r in rows if r["past_peak"]), "no_minute_bars": sum(1 for r in rows if not r["n_bars"])}
    firsts = [r for r in rows if r.get("is_first_live")]
    summ["replay"] = {"first_live_anchors": len(firsts),
                      "replayed": sum(1 for r in firsts if r.get("deferral_min") is not None),
                      "no_replay_anchor": sum(1 for r in firsts if r.get("replay_t_ny") is None),
                      "replay_error": sum(1 for r in firsts if r.get("replay_t_ny") == "ERR"),
                      "median_deferral_min": median([r.get("deferral_min") for r in firsts]),
                      "deferral_ge5": sum(1 for r in firsts if (r.get("deferral_min") or 0) >= 5),
                      "deferral_le_minus5": sum(1 for r in firsts if (r.get("deferral_min") or 0) <= -5),
                      "median_replay_missed_15": median([r.get("replay_missed_15") for r in firsts]),
                      "median_live_missed_15_firsts": median([r.get("missed_15") for r in firsts])}
    save("a2", {"rows": rows, "summary": summ})
    log("PAOUT a2 " + json.dumps(summ, ensure_ascii=False))


# ------------------------------------------------------------------ A2-b (D2)
def mode_a2b():
    U = json.load(open(os.path.join(HERE, "in", "universe.json")))
    alerts = {}
    for line in open(os.path.join(ROOT, "tier_fwd_ledger.jsonl"), encoding="utf-8"):
        r = json.loads(line); alerts.setdefault((r["symbol"], r["date"]), r.get("anchor_price"))
    for a in json.load(open(os.path.join(HERE, "in", "anchors.json")))["anchors"]:
        if a.get("sent"):
            alerts.setdefault((a["sym"], a["day"]), a.get("anchor_price"))
    borrow = {}
    for line in open(os.path.join(ROOT, "ctb_log.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if r.get("shares_available") is not None:
            borrow.setdefault(r["symbol"], []).append((r["date"], r["shares_available"]))
    for v in borrow.values():
        v.sort()
    syms = sorted({s for (s, _d) in alerts} | {s for d in U.values() for s in d["list"] + d["near"]})
    log(f"a2b: alerts {len(alerts)} · symbols {len(syms)}")
    bars = {}
    for i, s in enumerate(syms):
        bars[s] = daily(s, "2026-02-01", "2026-10-27")
        if i % 200 == 0:
            log(f"  bars {i}/{len(syms)} · calls {CALLS}")
    def feat(s, d):
        b = bars.get(s) or []
        idx = next((i for i, x in enumerate(b) if x["d"] == d), None)
        if idx is None or idx < 15:
            return None
        rsi = rsi_wilder([x["c"] for x in b[:idx]])          # closes up to d-1
        ref = b[idx]["c"]
        fut10, fut20 = b[idx + 1: idx + 11], b[idx + 1: idx + 21]
        h10 = max((x["h"] for x in fut10), default=None); h20 = max((x["h"] for x in fut20), default=None)
        return {"rsi": rsi, "ref": ref, "n_fut": len(fut20),
                "hit10": (h10 is not None and h10 >= ref * (1 + EXPLOSION_PCT / 100)) if len(fut10) == 10 else None,
                "hit20": (h20 is not None and h20 >= ref * (1 + EXPLOSION_PCT / 100)) if len(fut20) == 20 else None}
    def band(r):
        return None if r is None else ("<=20" if r <= 20 else "20-25" if r <= 25 else "25-30" if r <= 30 else "30-40" if r <= 40 else ">40")
    def av(s, d):
        xs = [v for (dd, v) in borrow.get(s, []) if dd <= d]
        return "UNKNOWN" if not xs else ("<20k" if xs[-1] < 20000 else ">=20k")
    rows, ctrl = [], []
    for (s, d), apx in sorted(alerts.items()):
        f = feat(s, d)
        if not f:
            continue
        ready = s in (U.get(d) or {}).get("ready", [])
        rows.append(dict(f, sym=s, day=d, band=band(f["rsi"]), borrow=av(s, d), ready=ready, alert_px=apx))
    for d, u in sorted(U.items()):
        al = {s for (s, dd) in alerts if dd == d}
        for s in sorted(set(u["list"]) | set(u["near"])):
            if s in al:
                continue
            f = feat(s, d)
            if f:
                ctrl.append(dict(f, sym=s, day=d, band=band(f["rsi"]), borrow=av(s, d)))
    def tab(xs):
        out = {}
        for bnd in ("<=20", "20-25", "25-30", "30-40", ">40"):
            z = [x for x in xs if x["band"] == bnd]
            m10 = [x for x in z if x["hit10"] is not None]; m20 = [x for x in z if x["hit20"] is not None]
            out[bnd] = {"n": len(z), "hit10": sum(1 for x in m10 if x["hit10"]), "mature10": len(m10),
                        "hit20": sum(1 for x in m20 if x["hit20"]), "mature20": len(m20),
                        "not_ready": sum(1 for x in z if not x.get("ready")),
                        "not_ready_winners10": sum(1 for x in m10 if x["hit10"] and not x.get("ready"))}
        return out
    summ = {"alerts": tab(rows), "control": tab(ctrl),
            "alerts_le20_by_borrow": {k: tab([x for x in rows if x["borrow"] == k])["<=20"] for k in ("<20k", ">=20k", "UNKNOWN")},
            "clro": [x for x in rows if x["sym"] == "CLRO"], "n_alert_rows": len(rows), "n_control_rows": len(ctrl)}
    save("a2b", {"rows": rows, "summary": summ, "control_n": len(ctrl)})
    log("PAOUT a2b " + json.dumps(summ, ensure_ascii=False))


# ------------------------------------------------------------------ A3-b (D3)
def mode_a3b():
    import csv
    R = list(csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "READY_NOW_OUTCOMES.csv"), encoding="utf-8")))
    cells = {"swept_then_exploded": [], "exploded_no_sweep": [], "swept_no_explosion": [], "neither": [], "exploded_before_sweep": [], "no_data": []}
    for r in R:
        s, d0 = r["symbol"], r["first_ready"]
        # D3 (amended before any number): first_ready is a snapshot date (weekend renewals) ⟶ P = close of the last
        # session on or before it; the future windows start the session after that one
        b = daily(s, (dt.date.fromisoformat(d0) - dt.timedelta(days=7)).isoformat(), (dt.date.fromisoformat(d0) + dt.timedelta(days=45)).isoformat())
        i0 = max((i for i, x in enumerate(b or []) if x["d"] <= d0), default=None)
        if i0 is None or len(b) - i0 < 11:
            cells["no_data"].append(s); continue
        P = b[i0]["c"]; fut = b[i0 + 1:i0 + 21]
        sw = next((i for i, x in enumerate(fut[:10]) if x["l"] <= 0.8 * P), None)
        ex = next((i for i, x in enumerate(fut) if x["h"] >= 1.5 * P), None)
        tag = f"{s}@{d0}"
        if sw is not None and ex is not None:
            (cells["swept_then_exploded"] if ex > sw else cells["exploded_before_sweep"]).append(tag)
        elif ex is not None:
            cells["exploded_no_sweep"].append(tag)
        elif sw is not None:
            cells["swept_no_explosion"].append(tag)
        else:
            cells["neither"].append(tag)
    summ = {k: len(v) for k, v in cells.items()}
    save("a3b", {"cells": cells, "summary": summ})
    log("PAOUT a3b " + json.dumps(summ) + " · names " + json.dumps({k: v for k, v in cells.items() if k != "neither"}))


# ------------------------------------------------------------------ A3 (D7) · SXTC / DKI on their near-watch entry days
A3_DAYS = {"SXTC": ["2026-08-18", "2026-08-20", "2026-10-15", "2026-10-23", "2026-10-27"], "DKI": ["2026-08-16", "2026-09-02"]}


def mode_a3():
    import pandas as pd
    import Super_stock as S
    out = {}
    for sym, days in A3_DAYS.items():
        b = daily(sym, "2025-06-01", "2026-10-27")
        rows = []
        for d in days:
            hist = [x for x in b if x["d"] < d]            # the screener runs before the open: closes through d-1
            if len(hist) < 60:
                rows.append({"day": d, "bars": len(hist)}); continue
            cl = pd.Series([x["c"] for x in hist], dtype=float)
            rsi_now = float(S.rsi(cl, 14).iloc[-1])
            e30 = float(cl.ewm(span=30, adjust=False).mean().iloc[-1]); e50 = float(cl.ewm(span=50, adjust=False).mean().iloc[-1])
            px = float(cl.iloc[-1])
            rows.append({"day": d, "last_bar": hist[-1]["d"], "close": px, "rsi14": round(rsi_now, 2),
                         "above_ema30_pct": round((px / e30 - 1) * 100, 1), "above_ema50_pct": round((px / e50 - 1) * 100, 1),
                         "gain5_pct": round((px / hist[-6]["c"] - 1) * 100, 1) if len(hist) > 6 else None})
        out[sym] = rows
    save("a3", out)
    log("PAOUT a3 " + json.dumps(out))


# ------------------------------------------------------------------ A0③ (D4)
def mode_vol():
    out = {}
    for sym, post_day, faisal in (("JEM", "2026-10-24", (2.00, 2.20)), ("ELAB", "2026-10-21", (1.80, 2.20)),
                                  ("ZCMD", "2026-10-14", None), ("FBGL", "2026-10-22", None)):
        pb = daily(sym, (dt.date.fromisoformat(post_day) - dt.timedelta(days=200)).isoformat(), post_day)
        pb = [x for x in pb if x["d"] < post_day][-120:]
        tvb = None
        try:
            import tv_data as TV
            for ex in ("NASDAQ", "NYSE", "AMEX"):
                bb = TV.Chart().bars(f"{ex}:{sym}", "1D", 400)
                if bb:
                    tvb = [{"d": TV.ny_day(t), "o": o, "h": h, "l": l, "c": c, "v": v} for (t, o, h, l, c, v) in bb]
                    tvb = [x for x in tvb if x["d"] < post_day][-120:]
                    break
        except Exception as e:  # noqa: BLE001
            tvb = {"error": str(e)[:200]}
        res = {}
        for src, b in (("tradingview", tvb), ("polygon", pb)):
            if not isinstance(b, list) or not b:
                res[src] = {"bars": 0 if not isinstance(b, dict) else b}; continue
            px = b[-1]["c"]
            top = sorted(b, key=lambda x: -x["v"])[:3]
            below = [x for x in top if x["h"] < px] or [x for x in top if x["l"] < px]
            rng = [min(x["l"] for x in below), max(x["h"] for x in below)] if below else None
            match = None
            if faisal and rng:
                lo, hi = faisal
                overlap = not (hi < rng[0] or lo > rng[1])
                match = overlap and abs(lo - rng[0]) / rng[0] <= 0.10 and abs(hi - rng[1]) / rng[1] <= 0.10
            res[src] = {"bars": len(b), "last_close": px, "top3": top, "range_below": rng, "faisal": faisal, "match": match}
        out[sym] = res
    save("vol", out)
    log("PAOUT vol " + json.dumps({k: {s: {kk: v[s].get(kk) for kk in ("last_close", "range_below", "faisal", "match")} for s in v} for k, v in out.items()}))


# ------------------------------------------------------------------ A1-c (D5)
def mode_l2():
    q = get("/v3/quotes/CMMB", {"limit": "5", "order": "desc"})
    snap = get("/v2/snapshot/locale/us/markets/stocks/tickers/CMMB")
    conds = get("/v3/reference/conditions", {"asset_class": "stocks", "data_type": "trade", "limit": "1000"})
    keep = [c for c in (conds or {}).get("results") or [] if any(w in (c.get("name") or "") for w in ("Average", "Derivativ", "Odd Lot", "Closing", "Contingent"))]
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8"))
    syms = [s["symbol"] for s in wl.get("stocks") or [] if not s.get("removed_date") and s.get("status") not in ("stopped", "removed")]
    day = "2026-10-27"; t0 = ny_ms(day, 4, 0) * 1_000_000; t1 = ny_ms(day, 20, 0) * 1_000_000
    dp = {}
    for s in syms:
        tr = trades(s, t0, t1)
        if not isinstance(tr, list):
            dp[s] = {"error": tr}; continue
        tot = sum(x.get("size", 0) for x in tr); off = sum(x.get("size", 0) for x in tr if x.get("exchange") == 4)
        dp[s] = {"trades": len(tr), "volume": tot, "off_exchange_pct": round(100 * off / tot, 1) if tot else None}
    out = {"quotes_fields": sorted((((q or {}).get("results") or [{}])[0]).keys()), "quotes_sample": ((q or {}).get("results") or [])[:2],
           "snapshot_keys": sorted(((snap or {}).get("ticker") or {}).keys()), "snapshot_lastQuote": ((snap or {}).get("ticker") or {}).get("lastQuote"),
           "conditions": [{k: c.get(k) for k in ("id", "name", "description", "sip_mapping", "type")} for c in keep], "off_exchange": dp}
    save("l2", out)
    log("PAOUT l2 " + json.dumps({k: out[k] for k in ("quotes_fields", "snapshot_keys", "snapshot_lastQuote")}))
    log("PAOUT conditions " + json.dumps(out["conditions"], ensure_ascii=False)[:3000])
    log("PAOUT offexch " + json.dumps(dp))


# ------------------------------------------------------------------ A1-e (D6)
FP_W_S, FP_N, FP_SIZES, FP_DIR = 10, 8, {1, 2, 3, 5, 7, 10}, 3   # faisal_verbatim (TG_1850/1853 · TG_2113)


def fingerprint(tr):
    """Windows of FP_W_S seconds holding ≥FP_N trades, every size in FP_SIZES or ≤10, with ≥FP_DIR price-direction changes."""
    hits, ts = [], [(x["sip_timestamp"] // 1_000_000_000, x) for x in tr if "sip_timestamp" in x]
    j = 0
    for i in range(len(ts)):
        while ts[i][0] - ts[j][0] >= FP_W_S:
            j += 1
        win = [x for _, x in ts[j:i + 1]]
        if len(win) < FP_N or not all((x.get("size") in FP_SIZES) or (x.get("size", 99) <= 10) for x in win):
            continue
        px = [x["price"] for x in win]; dirs = [1 if b > a else -1 for a, b in zip(px, px[1:]) if b != a]
        chg = sum(1 for a, b in zip(dirs, dirs[1:]) if a != b)
        if chg >= FP_DIR:
            hits.append({"t_ny": dt.datetime.fromtimestamp(ts[i][0], tz=NY).strftime("%H:%M:%S"), "n": len(win), "chg": chg,
                         "sizes": sorted({x.get("size") for x in win}), "px": [min(px), max(px)]})
    return hits


def mode_tape():
    out = {}
    # TRUG: 17:28:25–17:28:40 ET, sessions 2026-07-13 … 07-31
    trug = {}
    d = dt.date(2026, 7, 13)
    while d <= dt.date(2026, 7, 31):
        if d.weekday() < 5:
            ds = d.isoformat()
            for tag, hh in (("et", 17), ("riyadh", 10)):   # D6: primary 17:28 ET · secondary 10:28 ET (post clock = Riyadh)
                tr = trades("TRUG", ny_ms(ds, hh, 28, 25) * 1_000_000, ny_ms(ds, hh, 28, 40) * 1_000_000)
                if isinstance(tr, list):
                    trug[ds + "/" + tag] = {"n": len(tr), "sizes": sorted({x.get("size") for x in tr})[:12], "px": sorted({x.get("price") for x in tr})[:8],
                                            "conds": sorted({c for x in tr for c in (x.get("conditions") or [])}), "fp": fingerprint(tr)}
        d += dt.timedelta(days=1)
    out["TRUG"] = trug
    # ADIL: days with range covering 1.70–1.77 (Jul–Sep), 10:05–10:09 ET
    adil = {}
    for b in daily("ADIL", "2026-06-01", "2026-09-30", adjusted=False):   # raw: the post's prices and the trades are raw
        if b["l"] <= 1.70 and b["h"] >= 1.77:
            tr = trades("ADIL", ny_ms(b["d"], 10, 5) * 1_000_000, ny_ms(b["d"], 10, 9) * 1_000_000)
            if isinstance(tr, list):
                seq = [x for x in tr if x.get("size") == 3]
                adil[b["d"]] = {"n": len(tr), "size3": len(seq), "size3_px": sorted({x["price"] for x in seq})[:6], "fp": fingerprint(tr)}
    out["ADIL"] = adil
    # ZCMD 2026-07-02 after hours
    tr = trades("ZCMD", ny_ms("2026-07-02", 16, 0) * 1_000_000, ny_ms("2026-07-02", 20, 0) * 1_000_000)
    if isinstance(tr, list):
        lots = [x for x in tr if x.get("size") == 1000]
        out["ZCMD"] = {"n": len(tr), "size1000": len(lots), "fp": fingerprint(tr)[:20],
                       "usd_5min_max": None}
        # max dollar volume in any 5-minute window
        ts = sorted((x["sip_timestamp"] // 1_000_000_000, x["price"] * x["size"]) for x in tr)
        best, j, acc = 0.0, 0, 0.0
        for i in range(len(ts)):
            acc += ts[i][1]
            while ts[i][0] - ts[j][0] >= 300:
                acc -= ts[j][1]; j += 1
            best = max(best, acc)
        out["ZCMD"]["usd_5min_max"] = round(best)
    # 3-year availability: TRUG 2023-10-27 after hours
    tr = trades("TRUG", ny_ms("2023-10-27", 9, 30) * 1_000_000, ny_ms("2023-10-27", 20, 0) * 1_000_000, cap=50000)
    out["availability_2023"] = {"n": len(tr) if isinstance(tr, list) else tr,
                                "odd_lots": sum(1 for x in tr if 37 in (x.get("conditions") or [])) if isinstance(tr, list) else None,
                                "after_16": sum(1 for x in tr if x.get("sip_timestamp", 0) >= ny_ms("2023-10-27", 16, 0) * 1_000_000) if isinstance(tr, list) else None}
    save("tape", out)
    summ = {"TRUG_days_fired": [d for d, v in out["TRUG"].items() if v["fp"]], "TRUG_days": len(out["TRUG"]),
            "ADIL_days_checked": len(out["ADIL"]), "ADIL_days_fired": [d for d, v in out["ADIL"].items() if v["fp"]],
            "ZCMD": {k: out.get("ZCMD", {}).get(k) for k in ("n", "size1000", "usd_5min_max")}, "ZCMD_fired": bool(out.get("ZCMD", {}).get("fp")),
            "availability_2023": out["availability_2023"]}
    log("PAOUT tape " + json.dumps(summ))
    log("PAOUT tape_trug " + json.dumps({d: {k: v[k] for k in ("n", "sizes", "px", "conds")} for d, v in out["TRUG"].items()})[:4000])


def main():
    if not KEY:
        log("⛔ no POLYGON_API_KEY"); return 2
    sys.path.insert(0, ROOT)
    import re
    src = open(os.path.join(ROOT, "Super_stock.py"), encoding="utf-8").read()
    assert float(re.search(r'"EXPLOSION_PCT":\s*([0-9.]+)', src).group(1)) == EXPLOSION_PCT
    modes = [m.strip() for m in (os.environ.get("PART_A_MODE") or "all").split(",")]
    table = {"a2": mode_a2, "a2b": mode_a2b, "a3": mode_a3, "a3b": mode_a3b, "vol": mode_vol, "l2": mode_l2, "tape": mode_tape}
    for m in (list(table) if "all" in modes else modes):
        t = time.time()
        try:
            table[m]()
        except Exception as e:  # noqa: BLE001
            import traceback; traceback.print_exc()
            log(f"PAOUT {m} ⛔ {type(e).__name__}: {e}")
        log(f"⏱️ {m}: {time.time() - t:.0f}s · calls {CALLS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
