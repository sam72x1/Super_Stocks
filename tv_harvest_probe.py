#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 مِجَسٌّ مؤقّت (يُحذف بعد قراءته) — هل يُطابق حسمُ الحصاد على دقائق TradingView مصدرًا مستقلًّا؟

الدافع (‏2026-09-30): أوّلُ حصادٍ على TradingView (`36675175184`) حسم 74 صفًّا — 48 ليوم 09-29 و26 صفًّا قديمًا
(09-04 ⟶ 09-28) تركها Polygon بلا حسمٍ طوال نافذة الاستدراك (لا شموعَ له في النافذة) · منها RAY ‏2026-09-10 PM «بلغ»
‏+674.6% (والنظاميّةُ +43.2%) وGLMD ‏+45.9% (والنظاميّةُ +2.8%). ودقائقُ TradingView مسوّاةٌ بالتقسيم (`adjustment=splits`)
ومرجعُ الصفّ `ref` خامٌّ من يوم القرار ⇒ تقسيمٌ بعده يزيّف النسبة.

المقارنة (لكلّ صفٍّ موسومٍ `src=tv` في `presession_outcomes.jsonl`):
 ① قمّةُ نافذة الوسم من دقائق TradingView (المسارُ الإنتاجيّ: `tv_bars8` · `window_label`) مقابل شموع ياهو 5 دقائق
    بالبري والأفتر (`prepost=True`) للنافذة نفسِها — مصدرٌ مستقلّ.
 ② فحصُ المقياس: سعرُ المصدر عند القرار (قرارُ PM: آخرُ شمعةٍ في يوم الجلسة السابقة · قرارُ AH: آخرُ شمعةٍ نظاميّة في
    يومه) مقسومًا على `ref` الخامّ — والبعيدُ عن 1 يعني مقياسًا آخر (تقسيم).
 ③ تقسيماتُ ياهو من يوم الجلسة السابقة فصاعدًا.

معيارُ القبول (مكتوبٌ قبل أوّل تشغيل · لا يُرخى بعد رؤية رقم):
 A1 — في الصفوف التي لها شموعٌ في النافذة عند المصدرين: قمّةُ TradingView ضمن 3% من قمّة ياهو في 90% منها فأكثر.
 A2 — كلُّ «بلغ» (+80%) عند TradingView يؤكّده ياهو (قمّةُ النافذة عنده +80% فأكثر) — وإلّا «غيرُ مؤكَّد».
 A3 — مقياسُ TradingView عند القرار داخل [0.9، 1.1] من `ref` في كلّ صفّ.
 القرار المكتوب قبل الرقم: صفٌّ قديمٌ (يومُه قبل 2026-09-29) يسقط على A2 أو A3 ⇒ حسمُ الأيّام القديمة على TradingView
 غيرُ موثوق ⇒ يُمنع ويُستثنى القديمُ المكتوبُ من التراكم بقاعدةٍ في الكود (لا حذفَ لصفّ) · وسقوطُ A1 أو A3 على صفوف 09-29
 ⇒ حارسُ مقياسٍ في الحصاد ‏+ حدُّ صدقٍ في الرسالة.

قراءةٌ فقط: لا تلغرام · لا كتابةَ حالة · لا Polygon."""
import datetime as dt
import json
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import presession_digest as DG                                    # noqa: E402
import presession_feats as PF                                     # noqa: E402
import presession_radar as PR                                     # noqa: E402
import presession_scan as PS                                      # noqa: E402
import tv_data as TV                                              # noqa: E402

NY = ZoneInfo("America/New_York")
SWITCH = "2026-09-29"
TOL_HIGH = 0.03
SCALE_LO, SCALE_HI = 0.9, 1.1


def log(*a):
    print(*a, flush=True)


def day_ms(day_iso):
    d = dt.date.fromisoformat(day_iso)
    a = dt.datetime.combine(d, dt.time(0, 0), tzinfo=NY)
    return int(a.timestamp() * 1000), int((a + dt.timedelta(days=1)).timestamp() * 1000)


def yahoo_bars8(df, day_iso):
    """شموعُ ياهو ليومٍ واحد بعقد الثمانيّ (ms, o, h, l, c, v, n, mod) — نقيّة على الإطار."""
    out = []
    if df is None or len(df) == 0:
        return out
    for ts, row in df.iterrows():
        try:
            t = ts.tz_convert(NY) if ts.tzinfo else ts.tz_localize("UTC").tz_convert(NY)
            if t.date().isoformat() != day_iso:
                continue
            o, h, lo, c = (float(row[k]) for k in ("Open", "High", "Low", "Close"))
            v = float(row["Volume"] or 0.0)
        except Exception:                                        # noqa: BLE001
            continue
        if not (h == h) or h <= 0:                               # NaN
            continue
        out.append((int(t.timestamp() * 1000), o, h, lo, c, v, 0.0, t.hour * 60 + t.minute))
    return out


def anchor_close(bars8, sess, day, prev):
    """سعرُ المصدر عند القرار: PM ⟵ آخرُ شمعةٍ في يوم الجلسة السابقة (حتى 20:00) · AH ⟵ آخرُ شمعةٍ نظاميّة في يومه."""
    if sess == "PM":
        w = [b for b in bars8.get(prev, []) if b[7] < PF.EXT_CLOSE]
    else:
        cm = PR.reg_close_for(day)
        w = [b for b in bars8.get(day, []) if PR.REG_OPEN <= b[7] < cm]
    return w[-1][4] if w else None


def main():
    import yfinance as yf                                         # noqa: PLC0415

    rows = [json.loads(line) for line in open(DG.OUT_FILE, encoding="utf-8") if line.strip()]
    rows = [r for r in rows if r.get("src") == "tv"]
    log(f"📒 صفوفُ الحصاد الموسومة tv: {len(rows)} · قديمةٌ (قبل {SWITCH}): "
        f"{sum(1 for r in rows if str(r.get(PF.ROW_DAY)) < SWITCH)}")
    snap, latest = PR.tv_snapshot()
    tmap = PR._TV["tmap"]
    log(f"📺 لقطةُ الماسح: {len(snap or {})} صفًّا · آخرُ جلسة {latest}")
    syms = sorted({str(r[PF.ROW_SYM]).upper() for r in rows})
    full = {s: tmap.get(s) or ("NASDAQ:" + s) for s in syms}
    got = TV.fetch_many(sorted(set(full.values())), interval="1", n=PR.TV_MAX_N, extended=True, workers=6,
                        stagger=0.1, retry_pass=True) or {}
    log(f"📺 دقائقُ TradingView: {sum(1 for s in syms if got.get(full[s]))} من {len(syms)} رمزًا")

    ycache, splits = {}, {}
    res = []
    for r in sorted(rows, key=lambda x: (x[PF.ROW_DAY], x[PF.ROW_SESS], x[PF.ROW_SYM])):
        day, sess, sym = str(r[PF.ROW_DAY]), str(r[PF.ROW_SESS]).upper(), str(r[PF.ROW_SYM]).upper()
        ref = float(r["ref"])
        prev = PR.prev_bday(day)
        st, en = DG.window_bounds(sess, day)
        tvb = {}
        for d in (prev, day):
            a, b = day_ms(d)
            tvb[d] = [x for x in PR.tv_bars8(got.get(full[sym]) or [], a, b) if PR.ny_mod(x[0])[0] == d]
        tv_lab = PS.window_label(tvb[day], st, en, ref)
        tv_anchor = anchor_close(tvb, sess, day, prev)
        key = (sym, prev, day)
        if key not in ycache:
            try:
                df = yf.download(sym, start=prev, end=(dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat(),
                                 interval="5m", prepost=True, progress=False, auto_adjust=False, threads=False)
                if df is not None and hasattr(df.columns, "nlevels") and df.columns.nlevels > 1:
                    df.columns = df.columns.get_level_values(0)
            except Exception as e:                               # noqa: BLE001
                log(f"⚠️ ياهو {sym}: {type(e).__name__}")
                df = None
            ycache[key] = {d: yahoo_bars8(df, d) for d in (prev, day)}
        yb = ycache[key]
        y_lab = PS.window_label(yb[day], st, en, ref)
        y_anchor = anchor_close(yb, sess, day, prev)
        if sym not in splits:
            try:
                sp = yf.Ticker(sym).splits
                splits[sym] = [(ix.date().isoformat(), float(v)) for ix, v in sp.items()] if sp is not None else []
            except Exception as e:                               # noqa: BLE001
                splits[sym] = [("?", type(e).__name__)]
        sp_after = [x for x in splits[sym] if x[0] == "?" or x[0] >= prev]
        tvh = (1 + tv_lab["max"] / 100.0) * ref if tv_lab.get("max") is not None else None
        yh = (1 + y_lab["max"] / 100.0) * ref if y_lab.get("max") is not None else None
        agree = (abs(tvh / yh - 1.0) <= TOL_HIGH) if (tvh and yh) else None
        tv_scale = (tv_anchor / ref) if tv_anchor else None
        y_scale = (y_anchor / ref) if y_anchor else None
        res.append(dict(day=day, sess=sess, sym=sym, ref=ref, old=day < SWITCH, stored=r.get("max_pct"),
                        stored_hit=int(r.get("hit") or 0), tv_n=tv_lab["n"], tv_max=tv_lab["max"],
                        tv_hit=tv_lab["hit80"], y_n=y_lab["n"], y_max=y_lab["max"], y_hit=y_lab["hit80"],
                        agree=agree, tv_scale=tv_scale, y_scale=y_scale, splits=sp_after))

    def f(x, nd=1):
        return "—" if x is None else f"{x:+.{nd}f}"

    log("\nيوم · جلسة · رمز · ref | TV: شموع قمّة% مقياس | ياهو: شموع قمّة% مقياس | اتّفاق | المخزَّن | تقسيمات")
    for x in res:
        log(f"{x['day']} {x['sess']} {x['sym']:6s} {x['ref']:.4g} | TV {x['tv_n']:3d} {f(x['tv_max'])}% "
            f"{'—' if x['tv_scale'] is None else format(x['tv_scale'], '.3f')}"
            f" | Y {x['y_n']:3d} {f(x['y_max'])}% {'—' if x['y_scale'] is None else format(x['y_scale'], '.3f')}"
            f" | {'—' if x['agree'] is None else ('✅' if x['agree'] else '❌')} | {f(x['stored'])}% hit={x['stored_hit']}"
            f" | {x['splits'] or '—'}{'  ⟵ قديم' if x['old'] else ''}")

    both = [x for x in res if x["agree"] is not None]
    a1 = sum(1 for x in both if x["agree"])
    hits = [x for x in res if x["tv_hit"]]
    a2_bad = [x for x in hits if not x["y_hit"]]
    sc_bad = [x for x in res if x["tv_scale"] is not None and not (SCALE_LO <= x["tv_scale"] <= SCALE_HI)]
    sc_none = [x for x in res if x["tv_scale"] is None]
    same = sum(1 for x in res if x["tv_max"] is not None and x["stored"] is not None
               and abs(x["tv_max"] - x["stored"]) < 1e-6)
    log("\n══ الحكم بالمعيار المكتوب قبل التشغيل ══")
    log(f"شاهدُ الهُويّة: قمّةُ TradingView اليوم = المخزَّن في {same} من {len(res)}")
    log(f"A1: اتّفاقُ القمّة ضمن {TOL_HIGH:.0%} في {a1} من {len(both)}"
        f" = {100.0 * a1 / len(both) if both else 0:.1f}% (الحدّ 90%) ⇒ {'✅' if both and a1 >= 0.9 * len(both) else '❌'}")
    log(f"A2: «بلغ» عند TradingView {len(hits)} · غيرُ مؤكَّدٍ عند ياهو {len(a2_bad)}: "
        f"{[(x['day'], x['sess'], x['sym']) for x in a2_bad]} ⇒ {'✅' if not a2_bad else '❌'}")
    log(f"A3: مقياسُ TradingView خارج [{SCALE_LO}، {SCALE_HI}] في {len(sc_bad)}: "
        f"{[(x['day'], x['sym'], round(x['tv_scale'], 3)) for x in sc_bad]} · بلا شمعة مرجع {len(sc_none)} ⇒ "
        f"{'✅' if not sc_bad else '❌'}")
    old_bad = [x for x in res if x["old"] and (x in a2_bad or x in sc_bad)]
    new_bad = [x for x in res if not x["old"] and (x in sc_bad or x["agree"] is False)]
    log(f"القديمُ الساقطُ على A2/A3: {len(old_bad)} {[(x['day'], x['sym']) for x in old_bad]}")
    log(f"صفوفُ 09-29 فصاعدًا الساقطةُ على A1/A3: {len(new_bad)} {[(x['day'], x['sym']) for x in new_bad]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
