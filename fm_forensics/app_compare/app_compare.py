#!/usr/bin/env python3
"""📱 لقطاتُ تطبيق «مراقب استراتيجية فيصل» (دفعة `B4_20261107`) مقابل قيم البوت — قراءةٌ فقط (أمرُ المالك 2026-11-07 ①-ب/ج).

`--mode probe` (رنر): لكلّ رمزٍ في `APP_SYMS` (افتراضًا الأربعة): شموعُ الإنتاج (`Super_stock.download_history` بمصدر `BARS_SOURCE`=tradingview كالفرز اليوميّ) ⟵
`analyze_ticker` (مقبولٌ أم جدارُه بالاسم من `_REJECT_REASONS`) · `near_watch_measure` (قيمُ ظرف الكاتالوج والخارجُ عنه بحوافّ `envelope_p100.json`
الحيّة) · `tested_level` (المستوى واللمسات) · و`drop_pct`/`rr` مقابل حدّيهما ⟵ سطرٌ لكلّ رمز و`APP_JSON`.
🔒 لا تلغرام · لا حفظ حالة · لا تغيير في أيّ جذرٍ أو عتبة.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DEFAULT_SYMS = ("BRTX", "THH", "EHGO", "NEXR")
KEYS = ("drop_pct", "rr")


def edge_of(edges, name):
    """حدُّ معيارٍ من الحوافّ ⟵ (أرضية، سقف) لمعيار النطاق أو (None، حدّ) أو (حدّ، None)."""
    from catalog_envelope import CRITERIA
    for nm, side, _desc, _k in CRITERIA:
        if nm != name:
            continue
        e = (edges or {}).get(name)
        if e is None:
            return None
        if side == "both" and isinstance(e, (list, tuple)) and len(e) == 2:
            return (float(e[0]), float(e[1]))
        return (float(e), None) if side == "lo" else (None, float(e))
    return None


def probe_one(S, sym, df, edges):
    """صفُّ رمزٍ واحد — بلا شبكة (الشموعُ ممرَّرة)."""
    out = {"symbol": sym, "bars": 0 if df is None else int(len(df))}
    if df is None or len(df) == 0:
        return out
    S._CUR_SYM = sym
    S._REJECT_REASONS.pop(sym, None)
    r = S.analyze_ticker(sym, df)
    out["accepted"] = bool(r)
    out["wall"] = None if r else S._REJECT_REASONS.get(sym)
    tl = S.tested_level(df)
    out["tested_level"] = tl
    m = S.near_watch_measure(sym, df, edges)
    if m:
        vals, outside = m
        out["outside"] = outside
        out["vals"] = {k: vals.get(k) for k in KEYS}
        out["edges"] = {k: edge_of(edges, k) for k in KEYS}
        out["price"] = vals.get("price")
    return out


def _f(x, nd=4):
    try:
        v = float(x)
        return None if v != v else round(v, nd)
    except (TypeError, ValueError):
        return None


def levels_one(S, AO, sym):
    """📏 مستوياتُ البوت لرمزٍ واحد (`APP_LEVELS=1` · مقارنةُ منشورات فيصل 11-07) — قراءةٌ فقط:
    الفحصُ اليدويّ نفسُه (`analyze_one.analyze_on_demand` = بطاقةُ فحص اليد) ‏+ `tested_level` (مِرساةُ الإنتاج) ‏+
    `resistance_levels` اليوميّة ‏+ `four_hour_levels` ‏+ `faisal_candle_supports` ‏+ أدنى القيعان ‏+ المتاحُ من ChartExchange."""
    out = {"symbol": sym}
    try:
        res = AO.analyze_on_demand(sym)
    except Exception as e:                                       # noqa: BLE001
        out["error"] = f"analyze_on_demand: {type(e).__name__}: {e}"
        return out
    r, gates, df = (list(res) + [None, None, None])[:3]
    if not r:
        out["error"] = str(gates)[:200]
        return out
    out["price"] = _f(r.get("price"))
    out["bars"] = int(len(df)) if df is not None else 0
    out["last_bar"] = str(df.index[-1])[:10] if df is not None and len(df) else None
    out["pivot"] = _f(r.get("pivot"))
    out["stop"] = [_f(x) for x in (r.get("stop") or ())]
    out["tranches"] = [_f(x) for x in (r.get("tranches") or ())]
    out["sweep"] = [_f(x) for x in (r.get("sweep") or ())]
    out["t"] = [_f(r.get(k)) for k in ("t1", "t2", "t3")]
    out["targets_kind"] = r.get("targets_kind")
    out["rr"] = _f(r.get("rr"), 3)
    out["drop_pct"] = _f(r.get("drop_pct"), 4)
    out["key_levels"] = {k: _f(v) for k, v in (r.get("key_levels") or {}).items()}
    h4l = r.get("h4_levels") or {}
    out["h4"] = {"supports": [_f(x) for x in (h4l.get("supports") or [])],
                 "resistances": [_f(x) for x in (h4l.get("resistances") or [])],
                 "flip": h4l.get("flip"), "sweep_low": _f(h4l.get("sweep_low")),
                 "managed_ceiling": h4l.get("managed_ceiling")}
    out["gates_failed"] = [g[0] for g in (gates or []) if len(g) > 1 and not g[1]]
    out["warnings"] = list(r.get("warnings") or [])[:8]
    if df is not None and len(df):
        price = float(df["Close"].iloc[-1])
        try:
            out["daily_resistances"] = [_f(x) for x in S.resistance_levels(df, price)]
        except Exception as e:                                   # noqa: BLE001
            out["daily_resistances"] = f"⛔ {type(e).__name__}"
        try:
            out["tested_level"] = S.tested_level(df)
        except Exception as e:                                   # noqa: BLE001
            out["tested_level"] = f"⛔ {type(e).__name__}"
        try:
            out["candle_supports"] = S.faisal_candle_supports(df, price)
        except Exception as e:                                   # noqa: BLE001
            out["candle_supports"] = f"⛔ {type(e).__name__}"
        lo = df["Low"]
        out["low5"] = _f(lo.tail(5).min())
        out["low20"] = _f(lo.tail(20).min())
        out["low252"] = _f(lo.tail(252).min())
        out["last5"] = [[str(i)[:10], _f(o), _f(h), _f(l), _f(c)] for i, o, h, l, c in
                        zip(df.index[-5:], df["Open"].tail(5), df["High"].tail(5), lo.tail(5), df["Close"].tail(5))]
    try:
        h4 = S.fetch_4h(sym)
        if h4 is not None and len(h4):
            out["h4_low20"] = _f(h4["Low"].tail(20).min())
            out["h4_last6"] = [[str(i)[:16], _f(o), _f(h), _f(l), _f(c)] for i, o, h, l, c in
                               zip(h4.index[-6:], h4["Open"].tail(6), h4["High"].tail(6), h4["Low"].tail(6), h4["Close"].tail(6))]
    except Exception as e:                                       # noqa: BLE001
        out["h4_err"] = f"{type(e).__name__}"
    try:
        out["borrow"] = S.ce_borrow_info(sym)
    except Exception as e:                                       # noqa: BLE001
        out["borrow"] = f"⛔ {type(e).__name__}"
    return out


def main_levels(syms):
    import Super_stock as S
    import analyze_one as AO
    rows = [levels_one(S, AO, s) for s in syms]
    for r in rows:
        print(f"📏 {r.get('symbol')}: {json.dumps(r, ensure_ascii=False, default=str)}")
    print("APP_LEVELS_JSON " + json.dumps(rows, ensure_ascii=False, default=str))
    return 0


def main(argv=None):
    import Super_stock as S
    import envelope_scan as ES                     # 🔧 مصدرُ الحوافّ كالإنتاج (`Super_stock.py` · «تحت المتابعة») — كان `catalog_envelope.load_edges` ولا وجودَ لها
    syms = [s.strip().upper() for s in os.environ.get("APP_SYMS", ",".join(DEFAULT_SYMS)).split(",") if s.strip()]
    if os.environ.get("APP_LEVELS", "0").strip() == "1":
        return main_levels(syms)
    edges = ES.load_edges() or {}
    hist = S.download_history(syms)
    rows = [probe_one(S, s, (hist or {}).get(s), edges) for s in syms]
    for r in rows:
        print(f"📱 {r['symbol']}: شموع {r.get('bars')} · مقبول {r.get('accepted')} · الجدار {r.get('wall')} · المستوى المختبر {r.get('tested_level')} · "
              f"القيم {r.get('vals')} · الحدّان {r.get('edges')} · خارج الظرف {r.get('outside')}")
    print("APP_JSON " + json.dumps(rows, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
