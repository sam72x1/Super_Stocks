"""تشخيصٌ وصفيٌّ لقبول T-GCROSS (فرعٌ لا يُدمج · لا يغيّر العقد): أين تقع أرقامُ نايف في بيانات Polygon؟"""
import datetime as dt
import os
import sys

import ema_cross_live as E
import golden_cross_scan as G
import market_calendar as MC
import vwap_momentum_live as V

key = os.environ["POLYGON_API_KEY"]
net = V.Net(key, os.environ.get("SEC_CONTACT", ""))


def hm(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def show(tag, bars, fast=8, slow=15, lim=40):
    xs = E.crosses(bars, fast, slow)
    print(f"   [{tag}] شموع {len(bars)} · تقاطعات {len(xs)}: " + " · ".join(f"{x['sign']}{hm(x['m'])} ${x['px']:g}" for x in xs[:lim]))


def day_diag(sym, day):
    by = net.minutes(sym, day, day)
    allb = (by or {}).get(day) or []
    if not allb:
        print(f"{sym} {day}: لا دقائق")
        return
    reg = E.regular(allb, 570, 960)
    pre = [b for b in allb if b[0] < 570]
    aft = [b for b in allb if b[0] >= 960]
    f = lambda bs: "—" if not bs else f"أدنى {min(b[3] for b in bs):g} ({hm(min(bs, key=lambda b: b[3])[0])}) · أعلى {max(b[2] for b in bs):g} ({hm(max(bs, key=lambda b: b[2])[0])})"   # noqa: E731
    print(f"{sym} {day}: بري {len(pre)} [{f(pre)}] · نظاميّ {len(reg)} [{f(reg)}] · أفتر {len(aft)} [{f(aft)}]")
    show("نظاميّ 8/15", reg)
    show("ممتدّ 04-20 8/15", sorted(allb, key=lambda b: b[0]))
    ext = sorted(allb, key=lambda b: b[0])
    xs = [x for x in E.crosses(ext) if 570 <= x["m"] < 960]
    print("   [نظاميّ بـEMA من البري] " + " · ".join(f"{x['sign']}{hm(x['m'])} ${x['px']:g}" for x in xs[:40]))


mode = sys.argv[1]
if mode == "chsn":
    d = dt.date(2026, 10, 29)
    while d <= dt.date(2026, 11, 5):
        if d.weekday() < 5:
            day_diag("CHSN", d.isoformat())
        d += dt.timedelta(1)
elif mode == "omh":
    for day in ("2026-11-03", "2026-11-04", "2026-11-05"):
        day_diag("OMH", day)
elif mode == "intc":
    b30 = G.fetch_30m(net, "INTC", "2024-06-01", "2026-11-04")
    print(f"INTC 30د {len(b30)}")
    import chart_id_tv as CT
    for tag, starts, end in (("4س نظاميّ 09:30/13:30", [570, 810], 960), ("4س ممتدّ 04/08/12/16", [240, 480, 720, 960], 1200),
                             ("4س 04:00/09:30/13:30/16:00", [240, 570, 810, 960], 1200)):
        b4 = CT.aggregate(b30, starts, end)
        for kind, fn in (("SMA", G.sma_series), ("EMA", E.ema_series)):
            closes = [b[4] for b in b4]
            f, s = fn(closes, 50), fn(closes, 200)
            out = []
            for j in range(200, len(b4)):
                if f[j - 1] is None or s[j - 1] is None:
                    continue
                up, was = f[j] > s[j], f[j - 1] > s[j - 1]
                if up != was:
                    out.append(f"{'⭐' if up else '💀'}{G.ny_day(b4[j][0])} ${closes[j]:g}")
            print(f"[{tag} · {kind} · شموع {len(b4)}] " + " · ".join(out[-8:]))
    # يوميّ
    j = net.poly("/v2/aggs/ticker/INTC/range/1/day/2024-01-01/2026-11-04", {"adjusted": "true", "sort": "asc", "limit": 5000})
    rows = [(int(r["t"]) // 1000, float(r["c"])) for r in (j or {}).get("results") or []]
    closes = [c for _t, c in rows]
    for kind, fn in (("SMA", G.sma_series), ("EMA", E.ema_series)):
        f, s = fn(closes, 50), fn(closes, 200)
        out = []
        for i in range(200, len(rows)):
            if f[i - 1] is None or s[i - 1] is None:
                continue
            up, was = f[i] > s[i], f[i - 1] > s[i - 1]
            if up != was:
                out.append(f"{'⭐' if up else '💀'}{G.ny_day(rows[i][0])} ${closes[i]:g}")
        print(f"[يوميّ · {kind}] " + " · ".join(out[-8:]))
    mx = [(G.ny_day(t), c) for t, c in rows if G.ny_day(t) >= "2026-01-01"]
    for m0 in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"):
        cs = [c for d0, c in mx if d0.startswith(m0)]
        if cs:
            print(f"   INTC {m0}: إغلاقٌ أدنى {min(cs):g} · أعلى {max(cs):g}")
