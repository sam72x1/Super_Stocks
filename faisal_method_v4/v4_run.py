# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — مُشغِّلُ workflow ‏faisal_v4.yml (قراءةٌ فقط · لا تلغرام · لا حالةَ إنتاج · بلا أسرار).

الأوضاع (V4_MODE):
  fetch  — شموعٌ يوميّة لكلّ رموز الحالات (S1-S4) من TradingView ⟵ تقييمٌ بالمحرّك المجمَّد ⟵ طباعةُ الشموع والنتيجة في السجلّ
  atmv   — §21: كلُّ مصدرٍ مشروعٍ متاحٍ لـATMV (خريطةُ الماسح · أربعُ بورصات · صيغُ الرمز · ياهو) ⟵ ما وُجد وما لم يوجد بالضبط
  cov30  — §22: تغطيةُ 30 دقيقة الفعليّة (نظاميّ · ممتدّ) لرموز الحالات الذهبيّة والأساسيّة
  ticker — تحليلُ رمزٍ عند الطلب بالمحرّك (كائنُ القرار ‏+ التفسير) — بلا إرسال

📦 المخرَجُ يُطبع في السجلّ أجزاءً (V4OUT|الاسم|i|n|جزء) لأنّ تنزيلَ الـartifact محجوبٌ من بيئة الجلسة (عطلٌ مُثبَت في V3.1).
"""
import base64
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "faisal_method_v3"))

OUT = os.path.join(HERE, "out")
CHUNK = 3500
DAILY_N = 1000
KEEP_FROM = "2025-06-01"          # §③: 120 جلسةً للدورة ‏+ هامش قبل أقدم عبارة (2026-01-22)
M30_N = 5000
EXCHANGES = ["NASDAQ", "NYSE", "AMEX", "OTC"]


def pack(obj):
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode("ascii")


def unpack(s):
    return json.loads(gzip.decompress(base64.b64decode(s)).decode("utf-8"))


def emit(name, obj, chunk=CHUNK):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)
    n = max(1, (len(s) + chunk - 1) // chunk)
    for i in range(n):
        print(f"V4OUT|{name}|{i + 1}|{n}|{s[i * chunk:(i + 1) * chunk]}")
    return n


def _tmap():
    try:
        import Super_stock as S
        return S._tv_ticker_map() or {}
    except Exception as e:                                         # noqa: BLE001
        print(f"⚠️ خريطةُ الماسح تعذّرت ({type(e).__name__}) ⟵ البورصاتُ بالترتيب")
        return {}


def resolve(sym, chart, tmap, tf="1D", n=DAILY_N):
    cands = []
    if tmap.get(sym):
        cands.append(tmap[sym])
    for e in EXCHANGES:
        c = f"{e}:{sym}"
        if c not in cands:
            cands.append(c)
    tries = []
    for full in cands:
        b = chart.bars(full, tf, n=n)
        tries.append([full, None if b is None else len(b)])
        if b:
            return full, b, tries
    return None, None, tries


def rows_of(bars, day=True):
    import tv_data as TV
    out = []
    for b in bars or []:
        t = str(TV.ny_time(b[0]))
        out.append([t[:10] if day else t[:16]] + [None if x is None else round(float(x), 6) for x in b[1:6]])
    return out


def case_tickers(cases):
    t = []
    for c in cases:
        if c.get("set") in ("S1", "S2", "S3", "S4"):
            for x in c.get("tickers") or []:
                if x and x.isalpha() and x not in t:
                    t.append(x)
    return t


def mode_fetch():
    import tv_data as TV
    import v4_eval as EV
    doc = json.load(open(os.path.join(HERE, "results", "cases_v4.json"), encoding="utf-8"))
    cases = doc["cases"]
    tick = case_tickers(cases)
    chart = TV.Chart(timeout=30.0)
    tmap = _tmap()
    bars, cov = {}, {}
    for s in tick:
        full, b, tries = resolve(s, chart, tmap)
        rows = [r for r in rows_of(b) if r[0] >= KEEP_FROM]
        bars[s] = rows
        cov[s] = {"full": full, "tries": tries, "n": len(rows), "first": rows[0][0] if rows else None,
                  "last": rows[-1][0] if rows else None}
        print(f"── {s}: {full or '⛔ لا شموع'} · {cov[s]['n']} جلسة · {tries}")
    res = EV.evaluate(cases, bars)
    os.makedirs(OUT, exist_ok=True)
    payload = {"tool": "v4_run fetch", "engine": __import__("decision_engine").ENGINE_VERSION, "keep_from": KEEP_FROM,
               "coverage": cov, "tv_calls": dict(getattr(TV, "CALLS", {})), "b64gz_bars": pack(bars)}
    json.dump(payload, open(os.path.join(OUT, "v4_bars.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(res["metrics"], open(os.path.join(OUT, "v4_metrics.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    emit("v4_bars.json", payload)
    emit("v4_metrics.json", res["metrics"])
    miss = [s for s in tick if not bars.get(s)]
    print(f"📦 رموزٌ بشموع {len(tick) - len(miss)} من {len(tick)} · بلا شموع: {miss or 'لا شيء'}")
    for g, m in res["metrics"].items():
        print(f"📏 {g}: حالات {m['cases']} · سليمة {m['ok']} · H-LEVEL {m['h_level_verdict']} {m['h_level']} · "
              f"H-CLASS {m['h_class'].get('verdict')} {m['h_class'].get('rate')}")
    return 0


def mode_atmv():
    import tv_data as TV
    chart = TV.Chart(timeout=30.0)
    tmap = _tmap()
    rep = {"symbol": "ATMV", "sources": []}
    for sym in ("ATMV", "ATMVU", "ATMVR", "ATMVW"):
        rep["sources"].append({"source": "TradingView scanner map", "symbol": sym, "result": tmap.get(sym)})
        for e in EXCHANGES:
            b = chart.bars(f"{e}:{sym}", "1D", n=DAILY_N)
            rep["sources"].append({"source": "TradingView chart", "symbol": f"{e}:{sym}",
                                   "bars": None if b is None else len(b),
                                   "first": rows_of(b)[0][0] if b else None, "last": rows_of(b)[-1][0] if b else None})
        try:
            import yfinance as yf
            h = yf.Ticker(sym).history(period="max", auto_adjust=False)
            rep["sources"].append({"source": "Yahoo (yfinance)", "symbol": sym, "bars": int(len(h)),
                                   "first": str(h.index[0])[:10] if len(h) else None, "last": str(h.index[-1])[:10] if len(h) else None})
        except Exception as e:                                     # noqa: BLE001
            rep["sources"].append({"source": "Yahoo (yfinance)", "symbol": sym, "error": type(e).__name__})
    try:
        import Super_stock as S
        uni = set(S.get_universe() or [])
        rep["sources"].append({"source": "NASDAQ universe (production list)", "symbol": "ATMV*",
                               "members": sorted(x for x in uni if str(x).startswith("ATMV"))})
    except Exception as e:                                         # noqa: BLE001
        rep["sources"].append({"source": "NASDAQ universe (production list)", "error": type(e).__name__})
    found = [x for x in rep["sources"] if x.get("bars")]
    rep["verdict"] = "DATA_AVAILABLE" if found else "DATA_UNAVAILABLE"
    os.makedirs(OUT, exist_ok=True)
    json.dump(rep, open(os.path.join(OUT, "v4_atmv.json"), "w", encoding="utf-8"), ensure_ascii=False)
    emit("v4_atmv.json", rep)
    print(f"ATMV ⟵ {rep['verdict']} · مصادرُ بشموع: {[x['symbol'] for x in found] or 'لا شيء'}")
    return 0


def mode_cov30():
    import tv_data as TV
    doc = json.load(open(os.path.join(HERE, "results", "cases_v4.json"), encoding="utf-8"))
    tick = [t for t in case_tickers([c for c in doc["cases"] if c["set"] in ("S1", "S3")])]
    chart = TV.Chart(timeout=30.0)
    tmap = _tmap()
    cov = {}
    for s in tick:
        full, b, tries = resolve(s, chart, tmap, n=50)
        if not full:
            cov[s] = {"full": None, "tries": tries}
            continue
        cov[s] = {"full": full, "requested": M30_N}
        for key, ext in (("regular", False), ("extended", True)):
            bb = chart.bars(full, "30", n=M30_N, extended=ext)
            r = rows_of(bb, day=False)
            days = sorted({x[0][:10] for x in r})
            cov[s][key] = {"returned": len(r), "first": r[0][0] if r else None, "last": r[-1][0] if r else None,
                           "sessions": len(days)}
        print(f"── {s}: {json.dumps(cov[s], ensure_ascii=False)}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(cov, open(os.path.join(OUT, "v4_cov30.json"), "w", encoding="utf-8"), ensure_ascii=False)
    emit("v4_cov30.json", cov)
    return 0


def mode_ticker():
    import tv_data as TV
    import decision_engine as E
    sym = (os.environ.get("V4_TICKER") or "").strip().upper().lstrip("$")
    if not sym:
        print("⛔ ticker فارغ")
        return 2
    asof = (os.environ.get("V4_ASOF") or "").strip() or None
    ctx = {}
    for k, env in (("groups", "V4_GROUPS"), ("offering_pending", "V4_OFFERING")):
        v = (os.environ.get(env) or "").strip().lower()
        ctx[k] = True if v in ("1", "true", "yes") else (False if v in ("0", "false", "no") else None)
    sh = (os.environ.get("V4_SHORT") or "").strip()
    ctx["short_available"] = int(float(sh)) if sh else None
    ctx["operator_press"] = None
    chart = TV.Chart(timeout=30.0)
    full, b, tries = resolve(sym, chart, _tmap())
    if not full:
        print(f"⛔ لا شموع لـ{sym} · {tries}")
        return 2
    rows = rows_of(b)
    nxt = None
    if asof:
        nxt = next((r[0] for r in rows if r[0] > asof), "9999-12-31")
    d = E.analyze_rows(rows, asof_date=nxt, context=ctx, symbol=sym)
    for x in d.get("explain") or []:
        print("‏" + x)
    os.makedirs(OUT, exist_ok=True)
    json.dump(d, open(os.path.join(OUT, f"v4_{sym}.json"), "w", encoding="utf-8"), ensure_ascii=False, default=str)
    emit(f"v4_{sym}.json", d)
    return 0


def main():
    mode = (os.environ.get("V4_MODE") or "ticker").strip()
    fn = {"fetch": mode_fetch, "atmv": mode_atmv, "cov30": mode_cov30, "ticker": mode_ticker}.get(mode)
    if not fn:
        print(f"⛔ وضعٌ غيرُ معروف: {mode}")
        return 2
    return fn()


if __name__ == "__main__":
    raise SystemExit(main())
