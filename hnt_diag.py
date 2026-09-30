# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ تشخيصيّ مؤقّت (يُحذف قبل الدمج) — لماذا انقلب صيّادُ المقسّم على WOK وYHC بين ياهو وTradingView (جلسة 09-29 ·
`hnt_probe` ‏36746517991)؟ وما صفوفُ LS الثلاثة التي لا يفسّرها تقسيمٌ مؤكَّد؟ **قراءةٌ فقط:** لا تلغرام · لا كتابةَ حالة · لا Polygon.
وصفيٌّ لا يحكم: يُطبع مَن دخل المرشِّحَ الأوّليّ (نداءاتُ `fetch_splits`) وترتيبُه · ونتيجةُ `_split_setup_probe` لكلّ مصدر · والفلوت
والقروب · وشموعُ المصدرين حول أحداث التقسيم وحول أكبر فرق."""
import datetime as dt
import math
import os
import sys

os.environ["SPLIT_SOURCE_REPAIR"] = "0"
import Super_stock as S                          # noqa: E402
import hunter_ledger as LEDGER                   # noqa: E402

SYMS = ["WOK", "YHC"]


def log(*a):
    print(*a, flush=True)


def cut(frames, day):
    out = {}
    for s, d in frames.items():
        c = d[[str(i)[:10] <= day for i in d.index]]
        if len(c):
            c.attrs.update(getattr(d, "attrs", {}) or {})
            out[s] = c
    return out


def rows_of(df, days):
    out = {}
    for i, r in zip(df.index, df[["Open", "High", "Low", "Close", "Volume"]].values):
        k = str(i)[:10]
        if k in days:
            out[k] = [round(float(x), 4) for x in r]
    return out


def main():
    day = S.last_closed_session()
    today = dt.date.today()
    log(f"آخرُ جلسةٍ مكتملة {day} · today={today}")
    uni = S.get_universe()
    os.environ["BARS_SOURCE"] = "tradingview"
    tvh = cut(S.download_history(uni), day)
    os.environ.pop("BARS_SOURCE", None)
    yhh = cut(S.download_history(uni), day)
    for tag, hist in (("ياهو", yhh), ("TradingView", tvh)):
        calls, floats, pumps = [], {}, {}

        def fs(s):
            calls.append(s)
            return S._fetch_splits(s)

        def ff(s):
            v = S._yahoo_float(s)
            floats[s] = v
            return v

        def fp(df, _h=hist):
            v = S.group_pump_scar(df)
            return v

        res = S.scan_split_hunter(hist, fetch_splits=fs, fetch_float=ff, fetch_pump=fp)
        log(f"\n═══ {tag}: المرشِّحُ الأوّليّ {len(calls)} (السقف {S.CONFIG['SPLIT_RADAR_PROBE_CAP']}) · مطابق {[r['symbol'] for r in res]}")
        for s in SYMS:
            pos = calls.index(s) + 1 if s in calls else None
            log(f"   {s}: في المرشِّح الأوّليّ={pos} · فلوت={floats.get(s)}")
            df = hist.get(s)
            if df is None:
                log("      لا إطار")
                continue
            c = df["Close"].values.astype(float)
            look = min(int(S.CONFIG["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
            cl = [(c[-k] / c[-k - 1] - 1.0, str(df.index[-k])[:10]) for k in range(1, look + 1) if c[-k - 1] > 0]
            mn = min(cl)
            log(f"      src={LEDGER.frame_src(df)} · شموع {len(df)} ({str(df.index[0])[:10]}…{str(df.index[-1])[:10]}) · "
                f"أشدُّ هبوطٍ يوميّ {mn[0] * 100:.1f}% ({mn[1]}) · الحدّ −{S.CONFIG['SPLIT_CLIFF_PCT']}% · آخرُ إغلاق {c[-1]:.4f}")
            pr = S._split_setup_probe(df, S._fetch_splits(s), today)
            if pr:
                keep = {k: pr.get(k) for k in ("split_date", "event_kind", "ref", "half", "price", "near_bottom", "held_ok",
                                               "didnt_rise", "rose_pct", "freq")}
                log(f"      _split_setup_probe: {keep}")
            else:
                log("      _split_setup_probe: None")
            pump = S.group_pump_scar(df) or {}
            log(f"      قروب: found={pump.get('found')}")
    for s in SYMS:
        sp = S._fetch_splits(s)
        pairs = list(zip([str(i)[:10] for i in sp.index], [float(v) for v in sp.values])) if sp is not None else []
        log(f"\n🔎 {s}: تقسيماتُ ياهو {pairs[-6:]}")
        a, b = yhh.get(s), tvh.get(s)
        if a is None or b is None:
            continue
        days = set()
        for d, _v in pairs[-3:]:
            dd = dt.date.fromisoformat(d)
            for k in range(-4, 6):
                days.add((dd + dt.timedelta(days=k)).isoformat())
        ra, rb = rows_of(a, None or set(str(i)[:10] for i in a.index)), rows_of(b, set(str(i)[:10] for i in b.index))
        worst = sorted(((abs(ra[k][3] / rb[k][3] - 1) if rb[k][3] else 0, k) for k in set(ra) & set(rb)), reverse=True)[:3]
        for _w, k in worst:
            dd = dt.date.fromisoformat(k)
            for j in range(-3, 4):
                days.add((dd + dt.timedelta(days=j)).isoformat())
        days |= set(sorted(set(ra) | set(rb))[-8:])
        log(f"   أكبرُ فروق الإغلاق: {[(k, round(w * 100, 2)) for w, k in worst]}")
        log("   اليوم | ياهو O H L C V | TradingView O H L C V")
        for k in sorted(days):
            if k in ra or k in rb:
                log(f"   {k} | {ra.get(k)} | {rb.get(k)}")
    # صفوفُ LS غيرُ المفسَّرة
    log("\n═══ صفوفُ LS خارج [0.8، 1.25] ولا يفسّرها تقسيمٌ مؤكَّد ═══")
    rows = [r for r in LEDGER.load() if not r.get("outcome") and r.get("ref_close")]
    need = sorted({r["symbol"] for r in rows} - set(yhh))
    extra = S.download_history(need) if need else {}
    allh = {**yhh, **extra}
    n = 0
    for r in rows:
        df = allh.get(r["symbol"])
        if df is None:
            continue
        d0 = str(r["session"])[:10]
        px = [float(x) for i, x in zip(df.index, df["Close"].values) if str(i)[:10] <= d0]
        if not px:
            continue
        rr = px[-1] / float(r["ref_close"])
        if 0.8 <= rr <= 1.25:
            continue
        f = S._split_scale_factor(S._fetch_splits(r["symbol"]), d0)
        if f != 1.0 and 0.9 <= rr * f <= 1.1:
            continue
        n += 1
        log(f"   {r['hunter']} {d0} {r['symbol']}: ref {r['ref_close']:.4g} · إغلاقُ ياهو الطازج {px[-1]:.4g} · r {rr:.3f} · f {f:.4g}")
    log(f"   ⇒ {n} صفًّا")
    return 0


if __name__ == "__main__":
    sys.exit(main())
