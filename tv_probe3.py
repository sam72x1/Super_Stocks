#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف بعد قراءته) — عقدُ `tv_presession_prereg.md` (`T-TVPRE`) حرفيًّا: مفتاحُ البري `post_hi_ret`
مُعادًا بـ`feature_row` الإنتاجيّة على دقائق TradingView الممتدّة مقابل قيمته المحسوبة بدقائق Polygon في السجلّ الأماميّ.
قراءةٌ فقط: لا تلغرام · لا كتابةَ حالة · لا Polygon."""
import datetime as dt
import json
import os
import statistics as st
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import presession_feats as PF                                     # noqa: E402
import presession_radar as PR                                     # noqa: E402
import tv_data as TV                                              # noqa: E402

DECISIONS = (("2026-09-28", "PM"), ("2026-09-29", "PM"))   # يوما الشموع 09-25 و09-28 — بدقائق Polygon قبل انتهائه
TOL = 0.02
FLOOR = PF.rank_floor("PM")
NY = ZoneInfo("America/New_York")


def log(*a):
    print(*a, flush=True)


def day_ms(day_iso):
    d = dt.date.fromisoformat(day_iso)
    a = dt.datetime.combine(d, dt.time(0, 0), tzinfo=NY)
    return int(a.timestamp() * 1000), int((a + dt.timedelta(days=1)).timestamp() * 1000)


def main():
    led = [json.loads(line) for line in open(PR.LEDGER_FILE, encoding="utf-8") if line.strip()]
    snap, latest = PR.tv_snapshot()
    log(f"لقطةُ الماسح: {len(snap or {})} صفًّا · آخرُ جلسة {latest} · الأرضية {FLOOR}")
    tmap = PR._TV["tmap"]
    allv, p3 = [], {}
    rows_n = cov_n = 0
    for day, sess in DECISIONS:
        rows = [r for r in led if r.get(PF.ROW_DAY) == day and r.get(PF.ROW_SESS) == sess]
        src = PR.prev_bday(day)
        cm = PR.reg_close_for(src)
        a, b = day_ms(src)
        full = {r[PF.ROW_SYM]: tmap.get(r[PF.ROW_SYM]) or ("NASDAQ:" + r[PF.ROW_SYM]) for r in rows}
        got = TV.fetch_many(list(full.values()), interval="1", n=5000, extended=True, workers=6, stagger=0.1,
                            retry_pass=True)
        out = []
        for r in rows:
            s = r[PF.ROW_SYM]
            bars = PR.tv_bars8(got.get(full[s]) or [], a, b)
            bars = [x for x in bars if PR.ny_mod(x[0])[0] == src]
            tvv = None
            if bars:
                pre, reg, _ = PR.split_bars(bars, src)
                pc = reg[0][1] if reg else (pre[0][1] if pre else None)
                f = PR.feature_row(s, bars, pc, sess, PF.EXT_CLOSE, close_min=cm)
                tvv = (f or {}).get("post_hi_ret")
            out.append({"sym": s, "rank": r.get("rank"), "poly": r.get("post_hi_ret"), "tv": tvv,
                        "n_poly": r.get("bars_n"), "n_tv": len(bars), "full": full[s],
                        "pu": r.get("post_usd"), "tu": (f or {}).get("post_usd") if bars else None})
        rows_n += len(out)
        both = [o for o in out if o["tv"] is not None and o["poly"] is not None]
        cov_n += len(both)
        allv.extend(both)
        miss = [(o["sym"], o["full"], o["n_tv"]) for o in out if o["tv"] is None]
        tv_rank = sorted(both, key=lambda o: -o["tv"])
        top_tv = {o["sym"] for o in tv_rank[:10]}
        top_poly = {o["sym"] for o in out if (o["rank"] or 99) <= 10}
        p3[day] = len(top_tv & top_poly)
        log(f"\n══ {sess} {day} (يومُ الشموع {src} · إغلاقُه {cm // 60:02d}:{cm % 60:02d}) — صفوف {len(out)} · بالمصدرين {len(both)}")
        log(f"   بلا دقائق عند TradingView ({len(miss)}): {miss[:20]}")
        log(f"   P3 العشرة: مشترك {p3[day]} من 10 · Polygon {sorted(top_poly)} · TradingView {sorted(top_tv)}")
        for o in sorted(both, key=lambda o: o["rank"] or 99)[:15]:
            log(f"      #{o['rank']:>2} {o['sym']:<6} Polygon {o['poly']:+.4f} · TradingView {o['tv']:+.4f} · "
                f"Δ {o['tv'] - o['poly']:+.4f} · شموع {o['n_poly']}/{o['n_tv']}")
        big = sorted(both, key=lambda o: -abs(o["tv"] - o["poly"]))[:10]
        log(f"   أبعدُ الفروق: {[(o['sym'], round(o['poly'], 4), round(o['tv'], 4), o['n_poly'], o['n_tv']) for o in big]}")
        ur = [o["tu"] / o["pu"] for o in both if o.get("tu") and o.get("pu")]
        if ur:
            log(f"   وصفيّ: سيولةُ الأفتر TradingView/Polygon — الوسيط {st.median(ur):.3f} على {len(ur)}")
    covr = cov_n / rows_n if rows_n else 0.0
    p1 = sum(1 for o in allv if abs(o["tv"] - o["poly"]) <= TOL) / len(allv) if allv else 0.0
    agree = [o for o in allv if (o["tv"] >= FLOOR) == (o["poly"] >= FLOOR)]
    p2 = len(agree) / len(allv) if allv else 0.0
    dis = [(o["sym"], round(o["poly"], 4), round(o["tv"], 4)) for o in allv if (o["tv"] >= FLOOR) != (o["poly"] >= FLOOR)]
    above = [(o["sym"], round(o["poly"], 4), round(o["tv"], 4)) for o in allv if o["tv"] >= FLOOR or o["poly"] >= FLOOR]
    log("\n══ الحكم (tv_presession_prereg.md §②-§③)")
    log(f"   التغطية {cov_n} من {rows_n} = {covr * 100:.1f}% (الحدّ 80%) {'✅' if covr >= 0.80 else '❌'}")
    if covr < 0.80:
        log("   ⚖️ الفرعُ 3 — لا قياس")
        return 0
    log(f"   P1 |Δ| لا يتجاوز {TOL}: {p1 * 100:.1f}% (الحدّ 90%) {'✅' if p1 >= 0.90 else '❌'}")
    log(f"   P2 قرارُ الأرضية نفسُه: {p2 * 100:.1f}% (الحدّ 95%) {'✅' if p2 >= 0.95 else '❌'} · مختلف {dis} · فوقها بأحدهما {above}")
    log(f"   P3 العشرة: {p3} (الحدّ 8 في كلٍّ) {'✅' if all(v >= 8 for v in p3.values()) else '❌'}")
    ok = p1 >= 0.90 and p2 >= 0.95 and all(v >= 8 for v in p3.values())
    log(f"   ⚖️ الفرعُ {'1 — مطابق: الأرضيةُ تبقى' if ok else '2 — غيرُ مطابق: الأرضيةُ على TradingView غيرُ معايَرة (تُعلَن) · والقرارُ للمالك'}")
    ds = sorted(abs(o["tv"] - o["poly"]) for o in allv)
    log(f"   وصفيّ |Δ|: الوسيط {st.median(ds):.4f} · 90٪ {ds[int(0.9 * len(ds)) - 1]:.4f} · الأقصى {ds[-1]:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
