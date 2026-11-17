"""✂️🔎 هل يفوّت Polygon تقسيمًا عكسيًّا؟ وما أثرُه على «تحرّك 30%» الحيّ؟ — أمرُ المالك 2026-11-17
«افحص GPAK وSMFL على ياهو — وإن ثبت أن Polygon يفوّت تقسيمات عكسية فاطبع أثره على إشعار «تحرّك 30%» الحي (إشعارات كاذبة يوم التقسيم)
واقترح الحماية» · تشخيصٌ قارئ: لا تلغرام · لا إنتاج · لا حكمَ ولا عتبة.

- `cases`: لكلّ حالةٍ تقسيماتُ ياهو (`yf.Ticker(s).splits`) وتقسيماتُ Polygon (`/v3/reference/splits`) والشموعُ اليوميّة المسوّاة
  وغيرُ المسوّاة حول التاريخ (كلُّ يومٍ تغيّر إغلاقُه عن السابق ×1.3 فأكثر أو ÷1.3 فأكثر يُطبع).
- `impact`: الكونُ الحيّ لـ«تحرّك 30%» اليوم (`xmove_universe` على `weekly_watchlist.json` ∪ `near_watch.json` — كونُ اليوم لا كونُ كلّ يوم) ·
  كلُّ تقسيمٍ عكسيٍّ عند ياهو في آخر 365 يومًا ⟵ هل يعرفه Polygon (تاريخُ تنفيذٍ ضمن ±3 أيّام)؟ ⟵ ويُعاد الإشعارُ الحيّ بحرفه
  (`xmove_fire` على دقائق Polygon المسوّاة `polygon_day_minutes` · إغلاقُ الأمس = آخرُ شمعةٍ يوميّةٍ مسوّاة قبل اليوم = ما يُرجعه `/prev`
  ذلك اليوم) على يوم التقسيم والجلسة التالية ⟵ إطلاقٌ = إشعارٌ كاذبٌ كان سيُرسَل.
"""
import concurrent.futures as cf
import datetime as dt
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CASES = (("GPAK", "2024-08-06"), ("SMFL", "2024-09-19"), ("MVLA", "2024-04-10"))   # الشاذّ في `T-BASKET` (`outliers.py` · `43984912345`)
TOL_DAYS = 3          # engineering — تسامحُ مطابقة تاريخ التقسيم بين المصدرين
JUMP = 1.3            # engineering — قفزةُ إغلاقٍ يوميٍّ تُطبَع في الحالات (حدُّ «تحرّك 30%» نفسُه)
LOOKBACK_DAYS = 365


def _d(x):
    return dt.date.fromisoformat(str(x)[:10])


def yahoo_reverse(pairs, start, end):
    """(نقيّة) تقسيماتُ ياهو العكسيّة في [start، end] ⟵ [(تاريخ، نسبة جديد/قديم)] · ياهو يكتب 1:10 عكسيًّا = 0.1."""
    out = []
    for d, r in pairs or ():
        try:
            dd, rr = str(d)[:10], float(r)
        except (TypeError, ValueError):
            continue
        if 0 < rr < 1 and start <= dd <= end:
            out.append((dd, rr))
    return sorted(out)


def polygon_knows(day, psplits, tol=TOL_DAYS):
    """(نقيّة) هل في تقسيمات Polygon تقسيمٌ عكسيٌّ (`split_from` أكبر من `split_to`) تاريخُه ضمن ±tol يومًا من `day`؟"""
    d0 = _d(day)
    for x in psplits or ():
        try:
            fr, to, e = float(x.get("split_from") or 0), float(x.get("split_to") or 0), _d(x.get("execution_date"))
        except (TypeError, ValueError, AttributeError):
            continue
        if fr > to > 0 and abs((e - d0).days) <= tol:
            return True
    return False


def jumps(bars, mult=JUMP):
    """(نقيّة) أيّامٌ تغيّر إغلاقُها عن السابق ×mult فأكثر أو ÷mult فأكثر ⟵ [(يوم، نسبة)] · `bars` = [(يوم، إغلاق)] مرتّبة."""
    out = []
    for (d0, c0), (d1, c1) in itertools.pairwise(bars):
        if c0 and c1 and (c1 / c0 >= mult or c0 / c1 >= mult):
            out.append((d1, round(c1 / c0, 4)))
    return out


# ── الجلب (فاشلٌ-آمن: None عند أيّ تعذّر) ────────────────────────────────────────────────────────────────────────────
def _key():
    return (os.environ.get("POLYGON_API_KEY") or "").strip()


def _get(url, params=None):
    import requests
    try:
        r = requests.get(url, params=params or {}, headers={"Authorization": f"Bearer {_key()}"}, timeout=25)
        return r.json() if r.status_code == 200 else None
    except Exception:                                            # noqa: BLE001
        return None


def poly_splits(sym):
    js = _get("https://api.polygon.io/v3/reference/splits", {"ticker": sym, "limit": 1000})
    return None if js is None else [{k: x.get(k) for k in ("execution_date", "split_from", "split_to")} for x in js.get("results") or []]


def poly_daily(sym, d1, d2, adjusted):
    js = _get(f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{d1}/{d2}",
              {"adjusted": "true" if adjusted else "false", "sort": "asc", "limit": 5000})
    if js is None:
        return None
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
    return [(dt.datetime.fromtimestamp(b["t"] / 1000, dt.timezone.utc).astimezone(ny).date().isoformat(), float(b["c"]),
             float(b.get("v") or 0)) for b in js.get("results") or [] if b.get("c")]


def yahoo_splits(sym):
    try:
        import yfinance as yf
        s = yf.Ticker(sym).splits
        return [(i.date().isoformat(), float(v)) for i, v in s.items()] if s is not None else []
    except Exception:                                            # noqa: BLE001
        return None


def _bot():
    sys.path.insert(0, ROOT)
    os.environ.setdefault("FAISAL_ONLY", "0")
    import Super_stock as S
    return S


def mode_cases():
    for sym, d in CASES:
        a, b = (_d(d) - dt.timedelta(days=40)).isoformat(), (_d(d) + dt.timedelta(days=45)).isoformat()
        ys, ps = yahoo_splits(sym), poly_splits(sym)
        adj, raw = poly_daily(sym, a, b, True), poly_daily(sym, a, b, False)
        row = {"sym": sym, "d": d, "yahoo_splits": ys, "polygon_splits": ps,
               "adj_jumps": jumps([(x, c) for x, c, _ in adj]) if adj else None,
               "raw_jumps": jumps([(x, c) for x, c, _ in raw]) if raw else None,
               "yahoo_reverse_in_window": yahoo_reverse(ys, a, b) if ys is not None else None,
               "polygon_knows": [(x, polygon_knows(x, ps)) for x, _ in yahoo_reverse(ys or [], a, b)] if ps is not None else None}
        print("SGP_CASE " + json.dumps(row, ensure_ascii=False))


def _impact_one(S, sym, start, end):
    ys = yahoo_splits(sym)
    if ys is None:
        return {"sym": sym, "status": "yahoo_fail"}
    rev = yahoo_reverse(ys, start, end)
    if not rev:
        return {"sym": sym, "status": "none"}
    ps = poly_splits(sym)
    out = []
    for d, r in rev:
        known = None if ps is None else polygon_knows(d, ps)
        bars = poly_daily(sym, (_d(d) - dt.timedelta(days=10)).isoformat(), (_d(d) + dt.timedelta(days=6)).isoformat(), True) or []
        days = [x for x, _, _ in bars]
        fire, fire_day = None, None
        for target in [x for x in days if x >= d][:2]:          # يومُ التقسيم والجلسة التالية (تاريخُ ياهو قد يسبق التنفيذ بجلسة)
            prev = [c for x, c, _ in bars if x < target]
            if not prev:
                continue
            f = S.xmove_fire(S.polygon_day_minutes(sym, target), target, prev[-1])
            if f:
                fire, fire_day = f, target
                break
        out.append({"d": d, "ratio": r, "polygon_knows": known, "fire_day": fire_day,
                    "fire_pct": None if not fire else round(fire["pct"], 4), "bars": len(bars)})
    return {"sym": sym, "status": "ok", "events": out}


def mode_impact():
    S = _bot()
    with open(os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8") as fh:
        wl = json.load(fh)
    with open(os.path.join(ROOT, "near_watch.json"), encoding="utf-8") as fh:
        near = json.load(fh)
    uni = sorted(S.xmove_universe(wl, near))
    end = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=LOOKBACK_DAYS)).isoformat()
    print(f"SGP_UNIVERSE n={len(uni)} window={start}..{end}")
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda s: _impact_one(S, s, start, end), uni))
    ev = [dict(e, sym=r["sym"]) for r in res if r["status"] == "ok" for e in r["events"]]
    for e in ev:
        print("SGP_EVENT " + json.dumps(e, ensure_ascii=False))
    known = [e for e in ev if e["polygon_knows"] is True]
    miss = [e for e in ev if e["polygon_knows"] is False]
    unk = [e for e in ev if e["polygon_knows"] is None]
    summ = {"universe": len(uni), "yahoo_fail": sum(1 for r in res if r["status"] == "yahoo_fail"),
            "reverse_events": len(ev), "polygon_known": len(known), "polygon_missing": len(miss), "polygon_unknown": len(unk),
            "fires_known": sum(1 for e in known if e["fire_day"]), "fires_missing": sum(1 for e in miss if e["fire_day"]),
            "fires_unknown": sum(1 for e in unk if e["fire_day"]), "window_days": LOOKBACK_DAYS}
    print("SGP_SUMMARY " + json.dumps(summ, ensure_ascii=False))


def main():
    if not _key():
        print("⛔ لا مفتاح Polygon")
        return 2
    mode = (os.environ.get("SGP_MODE") or "both").strip()
    if mode in ("cases", "both"):
        mode_cases()
    if mode in ("impact", "both"):
        mode_impact()
    return 0


if __name__ == "__main__":
    sys.exit(main())
