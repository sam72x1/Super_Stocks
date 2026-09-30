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


def part_c2():
    """تشخيصُ C2 في `T-TVBARS` (وصفيّ · لا يغيّر الفرعَ 2): الرموزُ التي آخرُ شمعتِها عند TradingView أقدمُ من آخر جلسة —
    ما الذي عند ياهو بعدها؟ أيّامٌ **بحجمٍ صفر** (حشو) أم **تداولٌ فعليّ** فات TradingView؟"""
    import pandas as pd
    import yfinance as yf
    import Super_stock as S
    uni = S.get_universe()
    snap = TV.scan(["name", "close"]) or {}
    tmap = TV.ticker_map(snap)
    full = {s: tmap.get(s, "NASDAQ:" + s) for s in uni}
    got = TV.fetch_many(list(full.values()), interval="1D", n=15, workers=8, stagger=0.25, retry_pass=True)
    last = {s: TV.ny_day(b[-1][0]) for s in uni for b in [got.get(full[s]) or []] if b}
    latest = max(last.values()) if last else None
    cand = sorted(s for s, d in last.items() if d < latest)
    log(f"\n══ C2 تشخيص (وصفيّ) — آخرُ جلسة {latest} · بشموع {len(last)} من {len(uni)} · أقدمُ من آخر جلسة {len(cand)}")
    pad, real, none_ = [], [], []
    for i in range(0, len(cand), 100):
        chunk = cand[i:i + 100]
        try:
            df = yf.download(chunk, period="1mo", interval="1d", auto_adjust=True, group_by="ticker",
                             threads=True, progress=False)
        except Exception as e:                                     # noqa: BLE001
            log(f"   ⚠️ ياهو تعذّر لدفعة {i}: {type(e).__name__}")
            continue
        for s in chunk:
            try:
                d = df[s] if isinstance(df.columns, pd.MultiIndex) else df
                d = d.dropna(subset=["Close"])
            except Exception:                                      # noqa: BLE001
                none_.append(s)
                continue
            after = [(str(ix)[:10], float(v or 0)) for ix, v in zip(d.index, d["Volume"]) if str(ix)[:10] > last[s]]
            if not after:
                none_.append(s)
            elif all(v <= 0 for _, v in after):
                pad.append((s, last[s], [x[0] for x in after]))
            else:
                real.append((s, last[s], [(a, int(v)) for a, v in after if v > 0][:4]))
    log(f"   ياهو بعد آخر شمعةٍ عند TradingView: حشوٌ بحجم صفر {len(pad)} · تداولٌ فعليّ {len(real)} · لا شيء {len(none_)}")
    log(f"   حشو: {pad[:25]}")
    log(f"   تداولٌ فعليّ: {real[:40]}")


def _spearman(xs, ys):
    """ارتباطُ الرتب (سبيرمان) بلا مكتبات — متوسّطُ الرتب للمتعادل."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    if len(xs) < 3:
        return None
    rx, ry = ranks(xs), ranks(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


def part_vol():
    """🧪 تسويةُ الحجم — **شروطُ القبول مكتوبةٌ هنا قبل أوّل تشغيل (2026-09-30)** ولا تُرخى بعد الرقم:
    حجمُ دقائق TradingView للزائر جزئيّ (‏≈5-15%) ⟵ هل يعيد `f` = حجمُ الشمعة اليوميّة عند TradingView ÷ مجموعُ دقائق
    الجلسة النظاميّة مقياسَ `usd_day` إلى ما حسبه Polygon؟ على صفوف قرارَي البري 09-28/09-29 (يوما الشموع 09-25/09-28).
    القبول: ① وسيطُ (المسوّى ÷ Polygon) بين 0.8 و1.25 · ② ‏80% فأكثر من الصفوف بين 0.5 و2 · ③ سبيرمان (المسوّى مقابل
    Polygon) 0.9 فأكثر — **والثلاثة معًا** وإلّا لا تُشحن التسوية ويبقى حدُّ الصدق مُعلَنًا."""
    led = [json.loads(line) for line in open(PR.LEDGER_FILE, encoding="utf-8") if line.strip()]
    PR.tv_snapshot()
    tmap = PR._TV["tmap"]
    res, miss = [], []
    for day, sess in DECISIONS:
        rows = [r for r in led if r.get(PF.ROW_DAY) == day and r.get(PF.ROW_SESS) == sess and r.get("usd_day")]
        src = PR.prev_bday(day)
        cm = PR.reg_close_for(src)
        a, b = day_ms(src)
        full = {r[PF.ROW_SYM]: tmap.get(r[PF.ROW_SYM]) or ("NASDAQ:" + r[PF.ROW_SYM]) for r in rows}
        syms = list(full.values())
        mins = TV.fetch_many(syms, interval="1", n=5000, extended=True, workers=6, stagger=0.1, retry_pass=True)
        daily = TV.fetch_many(syms, interval="1D", n=15, workers=6, stagger=0.1, retry_pass=True)
        for r in rows:
            s = r[PF.ROW_SYM]
            bars = [x for x in PR.tv_bars8(mins.get(full[s]) or [], a, b) if PR.ny_mod(x[0])[0] == src]
            _, reg, _ = PR.split_bars(bars, src, cm)
            vt = sum(x[5] for x in reg)
            ut = sum(x[4] * x[5] for x in reg)
            vd = next((float(x[5]) for x in (daily.get(full[s]) or []) if TV.ny_day(x[0]) == src), None)
            if not reg or not vt or not vd:
                miss.append((s, len(reg), vd))
                continue
            f = vd / vt
            res.append({"sym": s, "day": day, "poly": float(r["usd_day"]), "raw": ut, "f": f, "scaled": ut * f})
    log(f"\n══ تسويةُ الحجم (وصفيّ · قبولٌ مكتوبٌ قبل الرقم) — صفوف {len(res)} · بلا دقائق جلسةٍ أو شمعةٍ يوميّة {len(miss)}")
    log(f"   الناقص: {miss[:30]}")
    if not res:
        log("   ⚖️ لا قياس")
        return
    raw_r = sorted(o["raw"] / o["poly"] for o in res)
    sc_r = sorted(o["scaled"] / o["poly"] for o in res)
    fs = sorted(o["f"] for o in res)
    q = lambda v, p: v[min(len(v) - 1, max(0, int(p * len(v))))]          # noqa: E731
    med = st.median(sc_r)
    band = sum(1 for x in sc_r if 0.5 <= x <= 2.0) / len(sc_r)
    rho = _spearman([o["scaled"] for o in res], [o["poly"] for o in res])
    rho_raw = _spearman([o["raw"] for o in res], [o["poly"] for o in res])
    log(f"   الخامّ ÷ Polygon: الوسيط {st.median(raw_r):.3f} · الربعان {q(raw_r, .25):.3f}-{q(raw_r, .75):.3f} · سبيرمان {rho_raw:.3f}")
    log(f"   f: الوسيط {st.median(fs):.1f} · الربعان {q(fs, .25):.1f}-{q(fs, .75):.1f} · الأدنى {fs[0]:.2f} · الأقصى {fs[-1]:.1f}")
    log(f"   المسوّى ÷ Polygon: الوسيط {med:.3f} · الربعان {q(sc_r, .25):.3f}-{q(sc_r, .75):.3f} · بين 0.5 و2 {band * 100:.1f}% · سبيرمان {rho:.3f}")
    far = sorted(res, key=lambda o: -abs(__import__('math').log(o["scaled"] / o["poly"])))[:12]
    log(f"   أبعدُها: {[(o['sym'], o['day'][5:], round(o['poly']), round(o['scaled']), round(o['f'], 1)) for o in far]}")
    ok1, ok2, ok3 = 0.8 <= med <= 1.25, band >= 0.80, (rho or 0) >= 0.90
    log(f"   ① الوسيط {'✅' if ok1 else '❌'} · ② النطاق {'✅' if ok2 else '❌'} · ③ الرتب {'✅' if ok3 else '❌'}")
    log(f"   ⚖️ {'مقبولة — تُشحن التسوية' if ok1 and ok2 and ok3 else 'مرفوضة — لا تُشحن ويبقى حدُّ الصدق مُعلَنًا'}")


if __name__ == "__main__":
    _parts = (os.environ.get("TVPROBE3_PART") or "PRE").upper()
    if "VOL" in _parts:
        part_vol()
    if "C2" in _parts:
        part_c2()
    raise SystemExit(main() if "PRE" in _parts else 0)
