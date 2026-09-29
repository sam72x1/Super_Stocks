# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف بعد القراءة) — هل تصل رنراتُ GitHub إلى TradingView؟ وكم تستغرق؟ وهل يطابق RSI الماسح حسابَنا؟
قراءةٌ فقط · لا تلغرام · لا كتابةَ حالة. المراحل: A الماسح · B اليوميّ للعيّنة · C الساعة الممتدّة · D الإنتاجيّة · E مقارنةُ ياهو."""
import datetime as dt
import sys
import time

import pandas as pd

import tv_data as T

SAMPLE = ["SXTC", "HCAI", "XCH", "MGN", "UONE", "CCHH", "CETX", "AAPL", "SXTP", "SMX"]
COLS = ["name", "close", "RSI", "RSI[1]", "float_shares_outstanding", "volume", "update_mode", "type", "subtype",
        "exchange", "premarket_close", "postmarket_close", "change", "Low.1M", "High.1M", "price_52_week_high"]


def log(x):
    print(x, flush=True)


def rsi_last(closes):
    import Super_stock as S
    if len(closes) < 21:
        return None
    return float(S.rsi(pd.Series(closes)).iloc[-1])


def stage_a():
    log("═══ A الماسح ═══")
    t0 = time.time()
    snap = T.scan(COLS)
    log(f"A: {'None' if snap is None else len(snap)} صفًّا في {time.time() - t0:.1f}ث · CALLS={T.CALLS}")
    if snap is None:
        base = T.scan(["name", "close"])
        log(f"A-min: {'None' if base is None else len(base)}")
        for c in COLS[2:]:
            one = T.scan(["name", c], page=50)
            log(f"   عمود {c}: {'✗' if one is None else '✓'}")
        return base or {}
    by_ex = {}
    for k in snap:
        by_ex[k.split(':')[0]] = by_ex.get(k.split(':')[0], 0) + 1
    log(f"A: حسب السوق {by_ex}")
    tm = T.ticker_map(snap)
    for s in SAMPLE:
        full = tm.get(s)
        log(f"A {s}: {full} {snap.get(full)}")
    try:
        import Super_stock as S
        uni = S.get_universe()
        hit = sum(1 for s in uni if f"NASDAQ:{s}" in snap)
        log(f"A: الكون {len(uni)} · في الماسح بـNASDAQ {hit} = {hit / max(1, len(uni)) * 100:.1f}% · "
            f"غائب (أوّل 30) {[s for s in uni if f'NASDAQ:{s}' not in snap][:30]}")
    except Exception as e:                                         # noqa: BLE001
        log(f"A: الكون تعذّر {type(e).__name__}: {e}")
    return snap


def stage_b(snap):
    log("═══ B اليوميّ للعيّنة ═══")
    tm = T.ticker_map(snap)
    ch = T.Chart()
    res = {}
    for s in SAMPLE:
        full = tm.get(s, f"NASDAQ:{s}")
        t0 = time.time()
        b = ch.bars(full, "1D", 600)
        el = time.time() - t0
        if not b:
            log(f"B {s}: {b} في {el:.2f}ث")
            continue
        closes = [x[4] for x in b]
        r = rsi_last(closes)
        sc = snap.get(full) or {}
        f0, f1 = T.ny_time(b[0][0]), T.ny_time(b[-1][0])
        log(f"B {s}: {len(b)} شمعة في {el:.2f}ث · الأولى {f0:%Y-%m-%d %H:%M} · الأخيرة {f1:%Y-%m-%d %H:%M} "
            f"إغلاق {closes[-1]} · RSI محسوب {r} · الماسح RSI {sc.get('RSI')} RSI[1] {sc.get('RSI[1]')} "
            f"close {sc.get('close')} · أحدثُ 3 {[(T.ny_day(x[0]), x[4]) for x in b[-3:]]}")
        res[s] = b
    ch.close()
    return res


def stage_c(snap):
    log("═══ C الساعة الممتدّة ═══")
    tm = T.ticker_map(snap)
    ch = T.Chart()
    for s in SAMPLE[:4]:
        full = tm.get(s, f"NASDAQ:{s}")
        for iv in ("60", "1H"):
            t0 = time.time()
            b = ch.bars(full, iv, 700, extended=True)
            el = time.time() - t0
            if not b:
                log(f"C {s} [{iv}]: {b} في {el:.2f}ث")
                continue
            days = {}
            for x in b:
                t = T.ny_time(x[0])
                days.setdefault(t.date().isoformat(), []).append(f"{t:%H:%M}")
            last = sorted(days)[-2:]
            log(f"C {s} [{iv}]: {len(b)} شمعة في {el:.2f}ث · أيّام {len(days)} · من {sorted(days)[0]} · "
                f"ساعاتُ {last[0]}: {days[last[0]]} · وأدنى low آخر 25 يومًا "
                f"{min(x[3] for x in b if T.ny_day(x[0]) >= sorted(days)[-25])}")
            break
    ch.close()


def stage_d(snap):
    log("═══ D الإنتاجيّة ═══")
    tm = T.ticker_map(snap)
    import Super_stock as S
    try:
        uni = S.get_universe()
    except Exception:                                              # noqa: BLE001
        uni = sorted(k.split(":")[1] for k in snap if k.startswith("NASDAQ:"))
    step = max(1, len(uni) // 240)
    pick = [tm.get(s, f"NASDAQ:{s}") for s in uni[::step]][:240]
    one, many = pick[:40], pick[40:]
    c0 = dict(T.CALLS)
    t0 = time.time()
    r1 = T.fetch_many(one, "1D", 600, workers=1)
    e1 = time.time() - t0
    ok1 = sum(1 for v in r1.values() if v)
    log(f"D1 مقبسٌ واحد: {len(one)} رمزًا في {e1:.1f}ث = {e1 / max(1, len(one)):.2f}ث/رمز · ناجح {ok1} · "
        f"فارغ {sum(1 for v in r1.values() if v == [])} · فاشل {sum(1 for v in r1.values() if v is None)}")
    for w in (6, 12):
        part = many[:100] if w == 6 else many[100:]
        t0 = time.time()
        r = T.fetch_many(part, "1D", 600, workers=w)
        e = time.time() - t0
        ok = sum(1 for v in r.values() if v)
        log(f"D {w} مقابس: {len(part)} رمزًا في {e:.1f}ث = {e / max(1, len(part)):.2f}ث/رمز · ناجح {ok} · "
            f"فاشل {[k for k, v in r.items() if v is None][:15]}")
    log(f"D: CALLS فرق {({k: T.CALLS[k] - c0.get(k, 0) for k in T.CALLS})}")


def stage_e(res):
    log("═══ E مقارنةُ ياهو ═══")
    import Super_stock as S
    try:
        yh = S.download_history(SAMPLE)
    except Exception as e:                                         # noqa: BLE001
        log(f"E: ياهو تعذّر {type(e).__name__}: {e}")
        return
    for s in SAMPLE:
        b = res.get(s)
        ydf = yh.get(s)
        if not b or ydf is None:
            log(f"E {s}: TV {bool(b)} · ياهو {ydf is not None}")
            continue
        tvc = {T.ny_day(x[0]): x[4] for x in b}
        yc = {i.date().isoformat(): float(c) for i, c in ydf["Close"].items()}
        common = sorted(set(tvc) & set(yc))
        ratios = [yc[d] / tvc[d] for d in common[-120:] if tvc[d]]
        rt = rsi_last([tvc[d] for d in sorted(tvc)])
        ry = rsi_last([yc[d] for d in sorted(yc)])
        log(f"E {s}: أيّامٌ مشتركة {len(common)} · TV فقط {len(set(tvc) - set(yc))} · ياهو فقط {len(set(yc) - set(tvc))} · "
            f"نسبةُ الإغلاق ياهو/TV آخر 120: من {min(ratios):.4f} إلى {max(ratios):.4f} · RSI TV {rt} ياهو {ry}")


def main():
    log(f"🧪 مِجَسّ TradingView {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC · بايثون {sys.version.split()[0]}")
    snap = {}
    try:
        snap = stage_a() or {}
    except Exception as e:                                         # noqa: BLE001
        log(f"A انهار: {type(e).__name__}: {e}")
    res = {}
    for f, arg in ((stage_b, snap), (stage_c, snap), (stage_d, snap)):
        try:
            out = f(arg)
            if f is stage_b:
                res = out or {}
        except Exception as e:                                     # noqa: BLE001
            log(f"{f.__name__} انهار: {type(e).__name__}: {e}")
    try:
        stage_e(res)
    except Exception as e:                                         # noqa: BLE001
        log(f"E انهار: {type(e).__name__}: {e}")
    log(f"✅ انتهى · CALLS={T.CALLS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
