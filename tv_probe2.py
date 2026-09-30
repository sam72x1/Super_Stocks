# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف في الـPR نفسِه) — أسئلةٌ قبل نقل «قائمة البري» وشموع البوت إلى TradingView.

قراءةٌ فقط: لا تلغرام · لا كتابةَ حالة · لا Polygon.
  A) أيُّ حقول الماسح صالحة (إغلاق/افتتاح/قمّة/قاع/حجم/تغيّر · بري/أفتر) — وماذا يعني «close» بعد الإغلاق؟
  B) الماسحُ مقابل شمعة الجلسة اليوميّة من المِقبس (آخرُ جلسةٍ مكتملة) لعيّنة.
  C) شموعُ الدقيقة الممتدّة: كم شمعةً تعود · من متى إلى متى · وتغطيةُ اليوم السابق 04:00-20:00.
  D) عيّنةُ مطابقةٍ مع ياهو (للبند #228): الإغلاق · الحجم · آخرُ جلسة · وتعديلُ «dividends».
"""
import datetime as dt
import os
import statistics as st
import sys
import time

import tv_data as TV

NY = TV.NY


def log(*a):
    print(*a, flush=True)


def part_a():
    log("\n══ A) حقولُ الماسح ══")
    base = ["name", "close", "open", "high", "low", "volume", "change", "change_abs", "update_mode"]
    extras = ["premarket_close", "premarket_change", "premarket_volume", "premarket_high", "premarket_low",
              "postmarket_close", "postmarket_change", "postmarket_volume", "postmarket_high", "postmarket_low",
              "Value.Traded", "average_volume_10d_calc", "total_shares_outstanding", "float_shares_outstanding",
              "market_cap_basic", "sector", "country", "type", "subtype", "gap", "close|1", "volume|1",
              "Perf.W", "Recommend.All", "description", "exchange", "is_primary", "currency", "fundamental_currency_code",
              "earnings_release_next_date", "number_of_employees"]
    flt = [{"left": "name", "operation": "in_range", "right": ["AAPL", "SXTC", "KITT", "GCTK", "LABT", "MTEK"]}]
    snap = TV.scan(base, extra_filters=flt)
    log(f"   الأساس: {'✅' if snap else '⛔'} · {len(snap or {})} صفًّا")
    for k, v in sorted((snap or {}).items()):
        log(f"   {k}: {v}")
    ok, bad = [], []
    for c in extras:
        s = TV.scan(["name", c], extra_filters=flt)
        (ok if s else bad).append(c)
        if s:
            log(f"   ✅ {c}: " + " · ".join(f"{k.split(':')[1]}={v.get(c)}" for k, v in sorted(s.items())))
        time.sleep(0.3)
    log(f"   صالح {len(ok)} · مرفوض {len(bad)}: {bad}")
    return ok


def part_b(n_sample=40):
    log("\n══ B) الماسحُ مقابل شمعة الجلسة ══")
    cols = ["name", "close", "open", "high", "low", "volume", "change"]
    snap = TV.scan(cols) or {}
    nas = {k: v for k, v in snap.items() if k.startswith("NASDAQ:") and v.get("close") and v.get("volume")}
    liquid = sorted(nas, key=lambda k: -(nas[k]["close"] or 0) * (nas[k]["volume"] or 0))[:20]
    penny = [k for k in sorted(nas) if 0.2 <= (nas[k]["close"] or 0) < 1.0 and (nas[k]["volume"] or 0) > 200000][:20]
    sample = liquid + penny
    got = TV.fetch_many(sample, interval="1D", n=3, workers=4)
    same = {"close": 0, "open": 0, "high": 0, "low": 0, "volume": 0}
    n = 0
    for s in sample:
        bars = got.get(s)
        if not bars:
            continue
        ts, o, h, lo, c, v = bars[-1]
        sc = nas[s]
        n += 1
        diffs = {}
        for key, bv in (("close", c), ("open", o), ("high", h), ("low", lo), ("volume", v)):
            sv = sc.get(key)
            if sv and bv and abs(float(sv) - float(bv)) <= 1e-6 * max(abs(float(bv)), 1e-9):
                same[key] += 1
            else:
                diffs[key] = (sv, bv)
        prevc = bars[-2][4] if len(bars) > 1 else None
        chg = (c / prevc - 1) * 100 if prevc else None
        log(f"   {s:<14} يوم {TV.ny_day(ts)} · ماسح close {sc.get('close')} · شمعة {c} · change الماسح "
            f"{sc.get('change')} · محسوب {None if chg is None else round(chg, 4)}" + (f" · فروق {diffs}" if diffs else ""))
    log(f"   تطابقٌ تامّ من {n}: " + " · ".join(f"{k} {v}" for k, v in same.items()))


def part_c():
    log("\n══ C) شموعُ الدقيقة الممتدّة ══")
    ch = TV.Chart()
    try:
        for sym in ("NASDAQ:AAPL", "NASDAQ:SXTC", "NASDAQ:KITT", "NASDAQ:GCTK", "NASDAQ:LABT", "NASDAQ:MTEK"):
            for n in (2000, 5000):
                t0 = time.time()
                b = ch.bars(sym, interval="1", n=n, extended=True)
                dtm = time.time() - t0
                if not b:
                    log(f"   {sym} n={n}: {'[]' if b == [] else 'None'} ({dtm:.1f}ث)")
                    continue
                days = {}
                for ts, o, h, lo, c, v in b:
                    t = TV.ny_time(ts)
                    d = t.date().isoformat()
                    m = t.hour * 60 + t.minute
                    seg = "pre" if m < 570 else ("reg" if m < 960 else "post")
                    days.setdefault(d, {"pre": 0, "reg": 0, "post": 0, "vreg": 0.0, "first": m, "last": m})
                    days[d][seg] += 1
                    days[d]["first"] = min(days[d]["first"], m)
                    days[d]["last"] = max(days[d]["last"], m)
                    if seg == "reg":
                        days[d]["vreg"] += float(v or 0)
                f0, f1 = TV.ny_time(b[0][0]), TV.ny_time(b[-1][0])
                log(f"   {sym} n={n}: {len(b)} شمعة ({dtm:.1f}ث) · من {f0:%Y-%m-%d %H:%M} إلى {f1:%Y-%m-%d %H:%M} نيويورك")
                for d in sorted(days)[-3:]:
                    x = days[d]
                    log(f"      {d}: بري {x['pre']} · نظاميّ {x['reg']} · أفتر {x['post']} · "
                        f"أوّل {x['first'] // 60:02d}:{x['first'] % 60:02d} · آخر {x['last'] // 60:02d}:{x['last'] % 60:02d}"
                        f" · حجمُ النظاميّ {x['vreg']:,.0f}")
            d1 = ch.bars(sym, interval="1D", n=3)
            if d1:
                log("      يوميّ: " + " · ".join(f"{TV.ny_day(t)} v={v:,.0f}" for t, o, h, lo, c, v in d1))
    finally:
        ch.close()


def part_d():
    """عقدُ `tv_bars_prereg.md` حرفيًّا: C1-C4 تحكم · C5-C6 تُطبَع."""
    log("\n══ D) T-TVBARS — شموعُ TradingView مقابل ياهو على كون الفرز (tv_bars_prereg.md) ══")
    os.environ["SPLIT_SOURCE_REPAIR"] = "0"
    import pandas as pd
    import Super_stock as S
    uni = S.get_universe()
    snap = TV.scan(["name", "close", "float_shares_outstanding"]) or {}
    tmap = TV.ticker_map(snap)
    log(f"   الكون {len(uni)} · الماسح {len(snap)} صفًّا")
    if not uni or not snap:
        log("   ⛔ لا قياس (الكون أو الماسح تعذّر)")
        return
    t0 = time.time()
    full = {s: tmap.get(s, "NASDAQ:" + s) for s in uni}
    tv = TV.fetch_many(list(full.values()), interval="1D", n=560, workers=8, stagger=0.25, retry_pass=True)
    log(f"   TradingView: {sum(1 for v in tv.values() if v)} بشموع من {len(uni)} في {time.time() - t0:.0f}ث · CALLS {TV.CALLS}")
    t0 = time.time()
    yh = S.download_history(uni)
    log(f"   ياهو: {len(yh)} من {len(uni)} في {time.time() - t0:.0f}ث")
    if len(yh) < 0.85 * len(uni):
        log("   ⛔ لا قياس — ياهو دون 85% من الكون")
        return
    minb = int(S.CONFIG["MIN_BARS"])

    def tframe(b):
        return pd.DataFrame([(pd.Timestamp(TV.ny_day(t)), o, h, lo, c, v) for t, o, h, lo, c, v in b],
                            columns=["Date", "Open", "High", "Low", "Close", "Volume"]).set_index("Date")

    R = {}
    for s in uni:
        b = tv.get(full[s]) or []
        y = yh.get(s)
        r = {"n_t": len(b), "n_y": 0 if y is None else len(y)}
        R[s] = r
        if len(b) < minb or y is None or len(y) < minb:
            continue
        tdf = tframe(b)
        yc = {str(i)[:10]: float(c) for i, c in zip(y.index, y["Close"])}
        yv = {str(i)[:10]: float(v) for i, v in zip(y.index, y["Volume"])}
        tc = {str(i)[:10]: float(c) for i, c in zip(tdf.index, tdf["Close"])}
        tvv = {str(i)[:10]: float(v) for i, v in zip(tdf.index, tdf["Volume"])}
        com = sorted(set(yc) & set(tc))
        if len(com) < 20:
            continue
        c250, c20 = com[-250:], com[-20:]
        ratios = [yc[d] / tc[d] for d in c250 if tc[d] > 0 and yc[d] > 0]
        r.update(last_t=max(tc), last_y=max(yc),
                 rng=(max(ratios) / min(ratios)) if ratios else None,
                 med20=st.median([abs(yc[d] / tc[d] - 1) for d in c20 if tc[d] > 0]),
                 med250=st.median([abs(x - 1) for x in ratios]) if ratios else None,
                 vol20=st.median([yv[d] / tvv[d] for d in c20 if tvv[d] > 0 and yv[d] > 0] or [float("nan")]))
        vt = S.analyze_ticker(s, tdf)
        r["vt"] = "✅" if vt is not None else S._REJECT_REASONS.get(s)
        vy = S.analyze_ticker(s, y)
        r["vy"] = "✅" if vy is not None else S._REJECT_REASONS.get(s)
    Y = [s for s in uni if R[s]["n_y"] >= minb]
    YT = [s for s in Y if R[s]["n_t"] >= minb]
    both = [s for s in YT if "last_t" in R[s]]
    c1 = len(YT) / len(Y) if Y else 0.0
    c2 = (sum(1 for s in both if R[s]["last_t"] >= R[s]["last_y"]) / len(both)) if both else 0.0
    cons = [s for s in both if R[s]["rng"] is not None and R[s]["rng"] <= 1.5]
    c3 = (sum(1 for s in cons if R[s]["med20"] <= 0.005) / len(cons)) if cons else 0.0
    vv = [s for s in both if R[s]["vol20"] == R[s]["vol20"]]
    c4 = (sum(1 for s in vv if 0.8 <= R[s]["vol20"] <= 1.25) / len(vv)) if vv else 0.0
    log(f"\n   C1 التغطية: {len(YT)} من {len(Y)} = {c1 * 100:.2f}% (الحدّ 97%) {'✅' if c1 >= 0.97 else '❌'}")
    miss = [s for s in Y if R[s]["n_t"] < minb]
    log(f"      بلا شموعٍ كافية عند TradingView ({len(miss)}): {miss[:40]}")
    log(f"   C2 الطزاجة: {c2 * 100:.2f}% من {len(both)} (الحدّ 99%) {'✅' if c2 >= 0.99 else '❌'}")
    stale = [(s, R[s]['last_t'], R[s]['last_y']) for s in both if R[s]['last_t'] < R[s]['last_y']]
    log(f"      أقدمُ من ياهو ({len(stale)}): {stale[:20]}")
    log(f"   C3 الأسعار (آخر 20): {c3 * 100:.2f}% من {len(cons)} غيرِ مختلٍّ (الحدّ 95%) {'✅' if c3 >= 0.95 else '❌'}")
    bad3 = sorted(((R[s]["med20"], s) for s in cons if R[s]["med20"] > 0.005), reverse=True)
    log(f"      فوق 0.5% ({len(bad3)}): {[(s, round(m * 100, 2)) for m, s in bad3[:25]]}")
    m250 = sorted(R[s]["med250"] for s in cons if R[s]["med250"] is not None)
    if m250:
        log(f"      وصفيّ (آخر 250): الوسيط {st.median(m250) * 100:.3f}% · 90٪ {m250[int(0.9 * len(m250)) - 1] * 100:.3f}%")
    split_bad = sorted(((R[s]["rng"], s) for s in both if R[s]["rng"] is not None and R[s]["rng"] > 1.5), reverse=True)
    log(f"      مختلٌّ تقسيمًا بين المصدرين ({len(split_bad)}): {[(s, round(g, 2)) for g, s in split_bad[:30]]}")
    log(f"   C4 الحجم (آخر 20): {c4 * 100:.2f}% من {len(vv)} داخل [0.8، 1.25] (الحدّ 90%) {'✅' if c4 >= 0.90 else '❌'}")
    vs = sorted(R[s]["vol20"] for s in vv)
    if vs:
        log(f"      نسبةُ حجم ياهو/TradingView: 10٪ {vs[int(0.1 * len(vs))]:.3f} · الوسيط {st.median(vs):.3f} · 90٪ {vs[int(0.9 * len(vs)) - 1]:.3f}")
    same = [s for s in both if R[s].get("vt") == R[s].get("vy")]
    flips = [(s, R[s].get("vy"), R[s].get("vt"), "مختلٌّ تقسيمًا" if (R[s]["rng"] or 1) > 1.5 else "")
             for s in both if (R[s].get("vt") == "✅") != (R[s].get("vy") == "✅")]
    log(f"\n   C5 (يُطبَع ولا يحكم) الحكمُ نفسُه سببًا {len(same)} من {len(both)} · انقلابُ القبول {len(flips)}:")
    for f in flips[:60]:
        log(f"      {f[0]}: ياهو {f[1]} ⟵ TradingView {f[2]} {f[3]}")
    dr = {}
    for s in both:
        if R[s].get("vt") != R[s].get("vy"):
            k = f"{R[s].get('vy')} ⟵ {R[s].get('vt')}"
            dr[k] = dr.get(k, 0) + 1
    log(f"      أكثرُ فروق السبب: {sorted(dr.items(), key=lambda kv: -kv[1])[:15]}")
    ok = c1 >= 0.97 and c2 >= 0.99 and c3 >= 0.95 and c4 >= 0.90
    log(f"\n   ⚖️ الفرعُ {'1 — TradingView افتراضًا (خلف BARS_SOURCE)' if ok else '2 — ياهو يبقى · القرارُ للمالك'}")
    # C6 الفلوت (يُطبَع ولا يحكم)
    samp = [s for s in both][:: max(1, len(both) // 150)][:150]
    rows6 = []
    for s in samp:
        tf = (snap.get(full[s]) or {}).get("float_shares_outstanding")
        try:
            yf_ = S._yahoo_float(s, strict=True)
        except Exception:                                          # noqa: BLE001
            yf_ = None
        if tf and yf_:
            rows6.append((s, float(tf) / float(yf_)))
    if rows6:
        rs = sorted(r for _, r in rows6)
        within = sum(1 for r in rs if 0.8 <= r <= 1.25)
        log(f"\n   C6 (يُطبَع) الفلوت TradingView/ياهو على {len(rows6)}: داخل [0.8، 1.25] {within} · الوسيط {st.median(rs):.3f} · "
            f"أبعدُها {[(s, round(r, 2)) for s, r in sorted(rows6, key=lambda x: -abs(__import__('math').log(x[1])))[:15]]}")


def main():
    log(f"🧪 tv_probe2 · {dt.datetime.now(NY):%Y-%m-%d %H:%M} نيويورك")
    for name, fn in (("A", part_a), ("B", part_b), ("C", part_c), ("D", part_d)):
        if os.environ.get("PARTS") and name not in os.environ["PARTS"]:
            continue
        try:
            fn()
        except Exception as e:                                     # noqa: BLE001
            import traceback
            log(f"⛔ الجزء {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
    log(f"\n📊 CALLS {TV.CALLS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
