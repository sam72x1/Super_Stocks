"""🌙 T-NIGHT · المرحلة 1 «فحص الحقيقة» (أمرُ المالك 2026-11-19 · قراءةٌ فقط · بلا تلغرام · لا يكتب في المستودع).

سؤالان قبل أيّ عقد: ① هل مصادرُ البوت الثلاثة (Polygon · TradingView · ياهو) تعطي شموعَ الجلسة الليليّة
(20:00–04:00 نيويورك) ولأيّ عمق؟ ② ماذا فعلت الأسهمُ الأربعة (SVRE · INHD · LGHL · BRTX) في لياليها؟
المخرَج: JSON واحد + ملخّصٌ مطبوع. لا حكمَ ولا عتبة — وصفٌ فقط.
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
import zoneinfo

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
NY = zoneinfo.ZoneInfo("America/New_York")
CASES = {"SVRE": "2026-11-18", "INHD": "2026-11-19", "LGHL": "2026-11-19", "BRTX": "2026-11-19"}
DEPTH_SYMS = ("TSLA", "NVDA")
DEPTH_DAYS = ("2023-06-14", "2024-06-12", "2025-03-12", "2025-09-10", "2026-03-11", "2026-08-12", "2026-11-18")


def session_of(t: dt.datetime) -> str:
    """وقتُ نيويورك ⟵ pre (04:00-09:30) · reg (09:30-16:00) · after (16:00-20:00) · night (20:00-04:00)."""
    m = t.hour * 60 + t.minute
    if 240 <= m < 570:
        return "pre"
    if 570 <= m < 960:
        return "reg"
    if 960 <= m < 1200:
        return "after"
    return "night"


def night_of(t: dt.datetime) -> str:
    """الليلةُ تُنسَب إلى يوم التداول التالي: 20:00-23:59 ⟵ الغد · 00:00-03:59 ⟵ اليوم نفسُه."""
    d = t.date()
    if t.hour >= 20:
        d = d + dt.timedelta(days=1)
    return d.isoformat()


def bucket(bars):
    """[(ts_s, o, h, l, c, v)] ⟵ {يوم|جلسة: ملخّص}."""
    out = {}
    for ts, o, h, lo, c, v in bars:
        t = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).astimezone(NY)
        s = session_of(t)
        day = night_of(t) if s == "night" else t.date().isoformat()
        k = f"{day}|{s}"
        b = out.setdefault(k, {"n": 0, "first": t.strftime("%H:%M"), "open": o, "high": h, "high_at": t.strftime("%H:%M"),
                               "low": lo, "last": c, "last_at": t.strftime("%H:%M"), "vol": 0.0, "usd": 0.0})
        b["n"] += 1
        if h > b["high"]:
            b["high"], b["high_at"] = h, t.strftime("%H:%M")
        b["low"] = min(b["low"], lo)
        b["last"], b["last_at"] = c, t.strftime("%H:%M")
        b["vol"] += v or 0
        b["usd"] += (v or 0) * c
    return {k: out[k] for k in sorted(out)}


def poly(path, key, **params):
    try:
        r = requests.get("https://api.polygon.io" + path, params=params, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if r.status_code != 200:
            return {"_status": r.status_code}
        return r.json() or {}
    except Exception as e:                                         # noqa: BLE001
        return {"_status": f"exc:{type(e).__name__}"}


def poly_minutes(sym, d0, d1, key):
    j = poly(f"/v2/aggs/ticker/{sym}/range/1/minute/{d0}/{d1}", key, adjusted="true", sort="asc", limit=50000)
    if "_status" in j:
        return None, j["_status"]
    return [(int(b["t"] // 1000), b["o"], b["h"], b["l"], b["c"], b.get("v") or 0) for b in j.get("results") or []], 200


def poly_daily(sym, d0, d1, key):
    j = poly(f"/v2/aggs/ticker/{sym}/range/1/day/{d0}/{d1}", key, adjusted="true", sort="asc", limit=5000)
    if "_status" in j:
        return {"_status": j["_status"]}
    return {dt.datetime.fromtimestamp(b["t"] / 1000, tz=dt.timezone.utc).date().isoformat():
            {"o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b.get("v")} for b in j.get("results") or []}


def poly_night_trades(sym, day, key):
    """صفقاتٌ خام في [20:00 أمس، 04:00 اليوم) نيويورك — العددُ ومعرّفاتُ البورصات (هل Polygon يرى منصّةً ليليّة؟)."""
    d = dt.date.fromisoformat(day)
    a = dt.datetime.combine(d - dt.timedelta(days=1), dt.time(20, 0), tzinfo=NY)
    b = dt.datetime.combine(d, dt.time(4, 0), tzinfo=NY)
    j = poly(f"/v3/trades/{sym}", key, **{"timestamp.gte": int(a.timestamp() * 1e9), "timestamp.lt": int(b.timestamp() * 1e9),
                                           "limit": 50000, "order": "asc"})
    if "_status" in j:
        return {"_status": j["_status"]}
    res = j.get("results") or []
    ex = {}
    for t in res:
        ex[str(t.get("exchange"))] = ex.get(str(t.get("exchange")), 0) + 1
    return {"n": len(res), "exchanges": ex, "shares": sum(t.get("size") or 0 for t in res),
            "first": res[0].get("participant_timestamp") if res else None,
            "last": res[-1].get("participant_timestamp") if res else None}


def tv_bars(symbol, session, n=5000, interval="1"):
    """شموعُ TradingView بجلسةٍ تُسمّى صراحةً (regular · extended · overnight …) — نسخةُ `tv_data.Chart.bars` بمُدخَل الجلسة."""
    import tv_data as T
    ch = T.Chart()
    cs = "cs_" + T._rand()
    spec = json.dumps({"symbol": symbol, "adjustment": "splits", "session": session}, separators=(",", ":"))
    got, status = [], None
    try:
        ws = ch.open()
        ws.send(T.msg("chart_create_session", [cs, ""]))
        ws.send(T.msg("resolve_symbol", [cs, "symbol_1", "=" + spec]))
        ws.send(T.msg("create_series", [cs, "s1", "s1", "symbol_1", str(interval), int(n)]))
        t_end = time.time() + 25
        while status is None and time.time() < t_end:
            raw = ws.recv()
            for pl in T.split_frames(raw):
                kind, m = T.decode(pl)
                if kind == "hb":
                    ws.send(T.frame(m))
                    continue
                if kind != "msg":
                    continue
                name = m.get("m")
                mp = m.get("p") or []
                if name in ("critical_error", "protocol_error") or (mp and mp[0] == cs and name in T.ERRORS):
                    status = f"{name}:{json.dumps(mp, ensure_ascii=False)[:160]}"
                    break
                if mp and mp[0] == cs:
                    got.append(m)
                    if name == "series_completed":
                        status = "ok"
                        break
    except Exception as e:                                         # noqa: BLE001
        status = f"exc:{type(e).__name__}"
    finally:
        ch.close()
    sessions = None
    for m in got:
        if m.get("m") == "symbol_resolved":
            info = (m.get("p") or [None, None, {}])[2] or {}
            sessions = {k: info.get(k) for k in ("session", "session_display", "subsessions", "subsession_id", "timezone",
                                                  "has_extended_hours", "exchange", "listed_exchange", "update_mode", "delay")
                        if k in info}
            if isinstance(sessions.get("subsessions"), list):
                sessions["subsessions"] = [{k: s.get(k) for k in ("id", "description", "session", "private")} for s in sessions["subsessions"]]
    return (T.bars_from(got) if status == "ok" else None), status or "timeout", sessions


def yahoo_minutes(sym):
    try:
        import yfinance as yf
        df = yf.Ticker(sym).history(period="5d", interval="1m", prepost=True, auto_adjust=False)
        if df is None or df.empty:
            return [], "empty"
        return [(int(ix.timestamp()), float(r["Open"]), float(r["High"]), float(r["Low"]), float(r["Close"]), float(r["Volume"] or 0))
                for ix, r in df.iterrows() if r["Close"] == r["Close"]], "ok"
    except Exception as e:                                         # noqa: BLE001
        return None, f"exc:{type(e).__name__}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="night_probe.json")
    ap.add_argument("--received", default="", help="طابعُ وصول إشارة BRTX (UTC ISO) ⟵ سعرُ الدقيقة عنده")
    a = ap.parse_args()
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    rep = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "cases": {}, "depth": {}, "tv": {}, "yahoo": {}}
    if not key:
        print("⛔ لا مفتاح Polygon")
        rep["polygon"] = "no_key"
    for sym, day in CASES.items():
        c = {"move_day": day}
        if key:
            c["daily"] = poly_daily(sym, "2026-11-10", "2026-11-20", key)
            bars, st = poly_minutes(sym, "2026-11-16", "2026-11-20", key)
            c["minute_status"] = st
            c["polygon_sessions"] = bucket(bars) if bars else {}
            c["night_trades"] = poly_night_trades(sym, day, key)
            if sym == "BRTX" and a.received and bars:
                try:
                    rt = dt.datetime.fromisoformat(a.received.replace("Z", "+00:00")).timestamp()
                    prev = [b for b in bars if b[0] <= rt]
                    c["price_at_received"] = {"received": a.received, "bar_utc": dt.datetime.fromtimestamp(prev[-1][0], tz=dt.timezone.utc).isoformat(),
                                              "close": prev[-1][4]} if prev else None
                except ValueError:
                    c["price_at_received"] = "bad_ts"
        rep["cases"][sym] = c
        tv = {}
        for full in (f"NASDAQ:{sym}", f"BOATS:{sym}"):
            for ses in ("extended", "overnight") if full.startswith("NASDAQ") else ("regular", "extended"):
                bars, st, info = tv_bars(full, ses)
                tv[f"{full}|{ses}"] = {"status": st, "n": len(bars or []), "info": info,
                                       "first": tv_ts(bars, 0), "last": tv_ts(bars, -1),
                                       "sessions": {k: v for k, v in bucket(bars or []).items() if k >= "2026-11-17"}}
        rep["tv"][sym] = tv
        yb, st = yahoo_minutes(sym)
        rep["yahoo"][sym] = {"status": st, "n": len(yb or []), "sessions": bucket(yb or [])}
    if key:
        for sym in DEPTH_SYMS:
            d = {}
            for day in DEPTH_DAYS:
                prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
                bars, st = poly_minutes(sym, prev, day, key)
                b = bucket(bars) if bars else {}
                d[day] = {"status": st, "night_bars": (b.get(f"{day}|night") or {}).get("n", 0),
                          "night_vol": (b.get(f"{day}|night") or {}).get("vol", 0),
                          "pre_bars": (b.get(f"{day}|pre") or {}).get("n", 0), "trades": poly_night_trades(sym, day, key)}
            rep["depth"][sym] = d
    for sym in DEPTH_SYMS:
        tv = {}
        for full, ses in ((f"NASDAQ:{sym}", "extended"), (f"NASDAQ:{sym}", "overnight"), (f"BOATS:{sym}", "regular")):
            for iv, n in (("1", 5000), ("30", 5000)):
                bars, st, info = tv_bars(full, ses, n=n, interval=iv)
                b = bucket(bars or [])
                nights = [k for k in b if k.endswith("|night")]
                tv[f"{full}|{ses}|{iv}"] = {"status": st, "n": len(bars or []), "info": info, "first": tv_ts(bars, 0), "last": tv_ts(bars, -1),
                                            "night_days": len(nights), "night_first": nights[0] if nights else None,
                                            "night_bars": sum(b[k]["n"] for k in nights)}
        rep["tv"][sym] = tv
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


def tv_ts(bars, i):
    if not bars:
        return None
    return dt.datetime.fromtimestamp(bars[i][0], tz=dt.timezone.utc).astimezone(NY).strftime("%Y-%m-%d %H:%M")


if __name__ == "__main__":
    sys.exit(main())
