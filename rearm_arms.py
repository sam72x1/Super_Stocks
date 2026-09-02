#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔁⚓ **T-REARM** — «إعادةُ المِرساة بعد الخروج البنيويّ»: هل تستحقّ المِرساةُ
الثانيةُ كرتًا؟ (أداةُ قياسٍ تاريخيّ).

العقد: `rearm_prereg.md` — **مدفوعٌ قبل أيّ رقم**، ولا معيارَ يُحرَّك بعده.
أمرُ المالك (2026-09-02): «سجّل إعادة المِرساة».

⚖️ **مقياسٌ واحدٌ لا اثنان:** الأنبوبةُ من `kasih_scan` بالاسم (‏`weekdays` ·
`parse_day` · `prescreen` · `first_anchor` · `resolve` · `f2_usd5` · `GAP_CAP` ·
`coverage_verdict`) · سعرُ الدخول من `tier_days_report.true_e5` · خروجُ
`T0`/`T10` من `target10_arms.arm_exit` · والمِرساةُ الثانية بـ
`Super_stock.liq_stage_events` **نفسِها** بحالةٍ مصفَّرة علامتُها `last_eval_ms`
= زمنُ شمعة الخروج (النمطُ القانونيّ: شرائح `bars[max(0, k-LIQ_WINDOW_MIN):k]`).

🔒 **قراءة/قياسٌ فقط:** لا تلغرام ولا كتابةَ حالةٍ ولا مساسَ بعتبة، والإنتاجُ
لا يستورد هذا الملف. الأذرعُ الثلاث (‏A0 الإنتاج · A1 إعادةٌ واحدة · A2 بلا
حدّ) تُحسَب على الصفوف نفسِها في تمريرةٍ واحدة ⇒ ميزانيةٌ واحدةٌ بالبناء.
"""
import gzip
import json
import os
import statistics as st_
import sys

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import datetime as dt                                             # noqa: E402

import ah_scan as AH                                              # noqa: E402
import kasih_scan as KS                                           # noqa: E402
import target10_arms as T10                                       # noqa: E402
import tier_days_report as TD                                     # noqa: E402
import Super_stock as S                                           # noqa: E402

MIN_MS = 60_000
FLOOR_SECOND = 150            # أرضيةُ الحكم لكلّ سنة (العقد §④)
COST_MAX_PCT = 50.0           # العقد §⑤-1 — مُعادٌ من T-GATE/T-CUMRISE
QUALITY_TOL_PP = 3.6          # العقد §⑤-2 — JITTER_PP المقيس في T-GATE
RECOVER_MIN_PCT = 1.0         # العقد §⑤-3
REARM_CAP = 20                # سقفُ A2 الهندسيّ — يُعَدّ ولا يُخفى
WINSOR_R = 10.0               # سقفُ التشذيب (سابقة T-TARGET10 ملحق ⑩)
# 🔒 V0 — المنشورُ في kasih_result.md (مراسٍ · كاسح30) لكلّ سنة — بت-بت أو خروج 3
PUBLISHED = {"2023": (10_851, 1_049), "2024": (14_312, 1_676),
             "2025": (19_037, 2_128)}
# 🔒 V3 — شاهدُ الحالة (العقد §④): رمز:يوم:من-إلى (نيويورك)
V3_DEFAULT = "CHAI:2026-08-28:11:50-12:15"


def exit_bar_ms(rows, anchor_ms: int, anchor_low: float):
    """زمنُ شمعة الخروج البنيويّ (أوّلُ إغلاقٍ دون قاع شمعة المِرساة **بعدها**)
    أو `None` — التعريفُ نفسُه في `kasih_scan.resolve`، ويُقفَل تكافؤُهما
    بالبوّابة `V5` لكلّ صفّ."""
    for b in rows:
        if b[0] <= anchor_ms:
            continue
        if b[4] < anchor_low:
            return int(b[0])
    return None


def next_anchor(rows, after_ms: int):
    """المِرساةُ التالية **بعد** شمعة الخروج — بدالّة الإنتاج نفسِها.

    الحالةُ المصفَّرة تحمل `last_eval_ms = after_ms` فتُقيَّم كلُّ شمعةٍ مغلقةٍ
    بعد الخروج (الأقدمُ أوّلًا) بـ`_bar_gates` الإنتاجية على نافذتها — لا
    الشمعةُ الأخيرة وحدَها (قاعدةُ «أوّلُ رؤيةٍ = الأخيرة» تخصّ الإقلاعَ لا
    الإعادة). صفرُ عتبةٍ جديدة."""
    bd = KS._dicts(rows)
    win = int(S.LIQ_WINDOW_MIN)
    i0 = next((i for i, b in enumerate(bd) if int(b["t"]) > int(after_ms)),
              None)
    if i0 is None:
        return None
    st = {"last_eval_ms": int(after_ms)}
    for k in range(i0 + 2, len(bd) + 1):
        evs, st = S.liq_stage_events(bd[max(0, k - win):k], st)
        for e in (evs or []):
            if e.get("stage") == "M1":
                return e
    return None


def _ny(ms: int) -> str:
    return dt.datetime.fromtimestamp(ms / 1000, tz=KS.NY).strftime("%H:%M")


def anchor_record(rows, e, prev_close, idx: int, prev_exit_ms):
    """صفُّ مِرساةٍ واحدة (أولى أو لاحقة) بالمقاييس المسجَّلة (العقد §③).

    يُرجع `(الصفّ، زمنُ الخروج البنيويّ أو None)`؛ و`None` كصفٍّ إن سقطت
    المِرساةُ على `GAP_CAP` أو تعذّر حسمُها."""
    a_ms = int(e["anchor_ms"])
    entry = float(e["price"])
    gap = (entry / prev_close - 1.0) * 100.0 if prev_close else None
    if gap is not None and abs(gap) > KS.GAP_CAP:
        return ("gapcap", None)
    res = KS.resolve(rows, a_ms, entry)
    if res is None:
        return (None, None)
    ab = next(b for b in rows if b[0] == a_ms)
    alow = float(ab[3])
    x_ms = exit_bar_ms(rows, a_ms, alow)
    e5, broke5 = TD.true_e5(rows, a_ms, entry)
    risk = (e5 - alow) if e5 else None
    r_ok = bool(e5) and not broke5 and risk is not None and risk > 0
    t0 = T10.arm_exit(rows, a_ms, alow, e5 or 0.0, None) if e5 else (None, None)
    t10 = (T10.arm_exit(rows, a_ms, alow, e5, T10.TARGETS[0]) if e5
           else (None, None))
    usd1 = float(e.get("usd") or 0)
    row = {"idx": idx, "anchor_ms": a_ms, "anchor_ny": _ny(a_ms),
           "entry": entry, "anchor_low": round(alow, 6),
           "exit": res["exit"], "exit_ms": x_ms,
           "exit_ny": (_ny(x_ms) if x_ms else None),
           "mg_after": res["mg_after"], "kasih30": bool(res["kasih30"]),
           "kasih50": bool(res.get("kasih50")),
           "kasih100": bool(res.get("kasih100")),
           "kasih30_from5": res.get("kasih30_from5"),
           "e5": (round(e5, 6) if e5 else None), "broke5": bool(broke5),
           "r_ok": r_ok,
           "r_t0": (round((t0[0] - e5) / risk, 4)
                    if r_ok and t0[0] is not None else None),
           "r_t10": (round((t10[0] - e5) / risk, 4)
                     if r_ok and t10[0] is not None else None),
           "t0_kind": t0[1], "t10_kind": t10[1],
           "gap_pct": (round(gap, 1) if gap is not None else None),
           "f5": (KS.f5_bucket(gap) if gap is not None else None),
           "f3": KS.f3_bucket(a_ms),
           "usd1": round(usd1), "f1": S._ignition_candle_class(usd1)[0],
           "vol_x": e.get("vol_x"),
           "gap_min": (round((a_ms - prev_exit_ms) / MIN_MS)
                       if prev_exit_ms is not None else None)}
    return (row, x_ms)


def chain_anchors(rows, first_e, prev_close):
    """سلسلةُ مراسي اليوم: الأولى ثم إعادةٌ بعد **كلّ** خروجٍ بنيويّ (`A2`)،
    و`A1` = أوّلُ عنصرين منها. تُرجع `(الصفوف، مقصوصٌ بالسقف؟، عدّادُ gapcap،
    عدّادُ V2، عدّادُ V5)`."""
    out, e, prev_x = [], first_e, None
    capped = False
    n_gap2 = v2_bad = v5_bad = 0
    while e is not None:
        if len(out) >= REARM_CAP:
            capped = True
            break
        row, x_ms = anchor_record(rows, e, prev_close, len(out) + 1, prev_x)
        if row == "gapcap":
            if out:
                n_gap2 += 1
            break
        if row is None:
            break
        # 🔒 V5: شمعةُ الخروج ⟺ resolve.exit == "break" (مقياسُ خروجٍ واحد)
        if (x_ms is not None) != (row["exit"] == "break"):
            v5_bad += 1
        # 🔒 V2: كلُّ مِرساةٍ لاحقة بعد شمعة خروج سابقتها
        if prev_x is not None and not (row["anchor_ms"] > prev_x):
            v2_bad += 1
        out.append(row)
        if x_ms is None:
            break
        prev_x = x_ms
        e = next_anchor(rows, x_ms)
    return out, capped, n_gap2, v2_bad, v5_bad


def recovered(rows_day) -> bool:
    """«مسترجَع» (العقد §③): الأولى لم تبلغ ‏+30% من `e5` (أو كُسرت قبل
    الخمس) **و**الثانية بلغته."""
    if len(rows_day) < 2:
        return False
    a1, a2 = rows_day[0], rows_day[1]
    return (a1.get("kasih30_from5") is not True
            and a2.get("kasih30_from5") is True)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def _med(xs):
    xs = [x for x in xs if x is not None]
    return st_.median(xs) if xs else None


def _pct(k, n):
    return (100.0 * k / n) if n else None


def _fmt(v, spec="+.3f"):
    return format(v, spec) if v is not None else "—"


def _pf(v):
    return f"{v:.1f}%" if v is not None else "—"


def quality_row(name, arows):
    """سطرُ جودةٍ لمجموعة مراسٍ (العقد §③)."""
    n = len(arows)
    k30 = sum(1 for a in arows if a["kasih30"])
    n5 = sum(1 for a in arows if a.get("kasih30_from5") is not None)
    k5 = sum(1 for a in arows if a.get("kasih30_from5") is True)
    brk = sum(1 for a in arows if a["exit"] == "break")
    r0 = [a["r_t0"] for a in arows if a.get("r_t0") is not None]
    r10 = [a["r_t10"] for a in arows if a.get("r_t10") is not None]
    r10w = [max(-WINSOR_R, min(WINSOR_R, x)) for x in r10]
    lo, hi = KS.wilson(k30, n)
    lo5, hi5 = KS.wilson(k5, n5)
    return {"name": name, "n": n, "k30": k30, "p30": _pct(k30, n),
            "w30": (lo, hi), "n5": n5, "k5": k5, "p5": _pct(k5, n5),
            "w5": (lo5, hi5), "med_mg": _med([a["mg_after"] for a in arows]),
            "p_break": _pct(brk, n), "n_r": len(r10),
            "r_t0": _mean(r0), "r_t10": _mean(r10), "r_t10w": _mean(r10w)}


def print_quality(rows_q):
    print(f"  {'المجموعة':30} {'ن':>6} {'كاسح30':>8} {'ويلسون':>11} "
          f"{'كاسح من د5':>11} {'ويلسون':>11} {'وسيط mg':>8} {'كُسر%':>6} "
          f"{'ن(R)':>6} {'R(T0)':>7} {'R(T10)':>7} {'مشذّب':>7}")
    for q in rows_q:
        print(f"  {q['name']:30} {q['n']:>6,} {_pf(q['p30']):>8} "
              f"[{q['w30'][0]:>4.1f}·{q['w30'][1]:>4.1f}] "
              f"{_pf(q['p5']):>11} [{q['w5'][0]:>4.1f}·{q['w5'][1]:>4.1f}] "
              f"{_fmt(q['med_mg'], '+.1f'):>8} {_pf(q['p_break']):>6} "
              f"{q['n_r']:>6,} {_fmt(q['r_t0']):>7} {_fmt(q['r_t10']):>7} "
              f"{_fmt(q['r_t10w']):>7}")


def parse_expect(txt: str):
    """`رمز:يوم:من-إلى` ⇒ (رمز، يوم، دقيقةُ البداية، دقيقةُ النهاية) أو None."""
    try:
        sym, day, rng = txt.strip().split(":", 2)
        a, b = rng.split("-")
        ha, ma = a.split(":")
        hb, mb = b.split(":")
        return (sym.strip().upper(), day.strip(),
                int(ha) * 60 + int(ma), int(hb) * 60 + int(mb))
    except (ValueError, AttributeError):
        return None


def v3_check(expect, chains: dict) -> tuple:
    """🔒 V3 (العقد §④): مِرساةٌ ثانية للرمز المتوقَّع داخل النافذة ⇒ True.
    تُرجع `(نتيجة، سطرٌ مطبوع)`؛ و`(None, ...)` إن لم يكن الرمزُ مقيسًا."""
    if not expect:
        return (None, "V3: بلا شاهدٍ متوقَّع")
    sym, _day, m_a, m_b = expect
    ch = chains.get(sym)
    if ch is None:
        return (None, f"V3: {sym} ليس في الرموز المقيسة ⇒ لا يُحكَم")
    seconds = ch[1:2]
    if not seconds:
        return (False, f"V3 ⛔ {sym}: لا مِرساةَ ثانية "
                       f"(مراسٍ {len(ch)} · خروجُ الأولى "
                       f"{ch[0].get('exit_ny') or 'eod'})")
    a2 = seconds[0]
    hh, mm = a2["anchor_ny"].split(":")
    mod = int(hh) * 60 + int(mm)
    ok = m_a <= mod <= m_b
    return (ok, f"V3 {'✅' if ok else '⛔'} {sym}: المِرساةُ الثانية "
                f"{a2['anchor_ny']} عند {a2['entry']:.4g} "
                f"(النافذة {m_a // 60:02d}:{m_a % 60:02d}-"
                f"{m_b // 60:02d}:{m_b % 60:02d})")


def main() -> int:                                                # noqa: C901
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("REARM_YEAR") or "").strip()
    one_day = (os.environ.get("REARM_DAY") or "").strip()
    syms = [s.strip().upper() for s in
            (os.environ.get("REARM_SYMS") or "").split(",") if s.strip()]
    expect = parse_expect(os.environ.get("REARM_EXPECT") or V3_DEFAULT)
    if one_day:
        days = [one_day]
        seed_days = KS.weekdays(
            (dt.date.fromisoformat(one_day)
             - dt.timedelta(days=7)).isoformat(),
            (dt.date.fromisoformat(one_day)
             - dt.timedelta(days=1)).isoformat())[-3:]
    elif year:
        days = KS.weekdays(f"{year}-01-01", f"{year}-12-31")
        seed_days = KS.weekdays(f"{int(year) - 1}-12-20",
                                f"{int(year) - 1}-12-31")[-3:]
    else:
        print("⛔ لا REARM_YEAR ولا REARM_DAY.")
        return 2
    if syms and not one_day:
        print("⛔ وضعُ الرموز يلزمه REARM_DAY.")
        return 2
    KS.log(f"🔁⚓ T-REARM — {'يوم ' + one_day if one_day else 'سنة ' + year}"
           + (f" · الرموز {syms}" if syms else
              f" · كون [{KS.PRICE_LO}, {KS.PRICE_HI}]$")
           + f" · أذرع A0/A1/A2 · سقف A2 {REARM_CAP} · العقد rearm_prereg.md")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_syms = n_screened = 0
    n_gapcap1 = n_gapcap2 = n_capped = v2_bad = v5_bad = 0
    out_path = f"rearm_rows_{year or one_day}.jsonl"
    fout = open(out_path, "w", encoding="utf-8")
    chains_last: dict = {}

    for di, day in enumerate(seed_days + days):
        seeding = di < len(seed_days)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
            continue
        dest = f"/tmp/rearm-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            n_missing += 0 if seeding else 1
            continue
        if seeding:
            universe = set()
        elif syms:
            universe = set(syms)          # سابقةُ sym_day_probe: بلا فلتر سعر
        else:
            universe = {s for s, c in prev_close.items()
                        if KS.PRICE_LO <= c <= KS.PRICE_HI}
        try:
            with gzip.open(dest, "rt") as fh:
                bars, closes = KS.parse_day(fh, universe)
        except (OSError, KeyError, ValueError) as e:
            KS.log(f"   ⛔ {day}: تعذّرت القراءة ({type(e).__name__}: {e})")
            try:
                os.remove(dest)
            except OSError:
                pass
            n_missing += 0 if seeding else 1
            continue
        try:
            os.remove(dest)
        except OSError:
            pass
        if seeding:
            prev_close.update(closes)
            KS.log(f"🌱 بذرة إغلاق الأمس من {day}: {len(closes):,} رمزًا")
            continue
        n_files += 1
        n_syms += len(bars)
        screened = {s: b for s, b in bars.items() if KS.prescreen(b)}
        n_screened += len(screened)
        for sym, b in screened.items():
            e = KS.first_anchor(b)
            if e is None:
                continue
            pc = prev_close.get(sym)
            entry = float(e["price"])
            gap = (entry / pc - 1.0) * 100.0 if pc else None
            if gap is not None and abs(gap) > KS.GAP_CAP:
                n_gapcap1 += 1
                continue
            chain, capped, g2, b2, b5 = chain_anchors(b, e, pc)
            if not chain:
                continue
            n_gapcap2 += g2
            v2_bad += b2
            v5_bad += b5
            if capped:
                n_capped += 1
            row = {"sym": sym, "day": day, "prev_close": pc,
                   "n_anchors": len(chain), "capped": capped,
                   "recovered": recovered(chain), "anchors": chain}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_out.append(row)
            if syms:
                chains_last[sym] = chain
        prev_close.update(closes)
        if n_files % 20 == 0:
            KS.log(f"   📦 {n_files}/{len(days)} يومًا · مرشَّح {n_screened:,}"
                   f" · مراسٍ أولى {len(rows_out):,} · ثانية "
                   f"{sum(1 for r in rows_out if r['n_anchors'] >= 2):,}")
    fout.close()

    print("\n" + "=" * 74)
    print(f"🔁⚓ T-REARM — {'يوم ' + one_day if one_day else 'سنة ' + year}"
          f" · العقد rearm_prereg.md (مدفوعٌ قبل أيّ رقم)")
    print("=" * 74)
    print(KS.MEASURE_CUT_NOTE)
    n1 = len(rows_out)
    k30_1 = sum(1 for r in rows_out if r["anchors"][0]["kasih30"])
    print(f"📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · رمز-يوم بالكون "
          f"{n_syms:,} · عبر المرشِّح {n_screened:,} · **مراسٍ أولى {n1:,}** "
          f"(كاسح30 {k30_1:,}) · استُبعد بتشويه تقسيم: أولى {n_gapcap1} · "
          f"ثانية {n_gapcap2} · مقصوصٌ بسقف A2 {n_capped}")
    # 🔒 V0 — تكاملٌ بت-بت مع kasih_result.md
    v0_bad = False
    if year in PUBLISHED and not syms:
        pn, pk = PUBLISHED[year]
        v0_bad = (n1, k30_1) != (pn, pk)
        print(f"🔒 V0 (تكامل kasih_result): مراسٍ {n1:,} مقابل {pn:,} · كاسح30 "
              f"{k30_1:,} مقابل {pk:,} {'✅ بت-بت' if not v0_bad else '⛔ تفرّق'}")
    print(f"🔒 V2 (كلُّ لاحقةٍ بعد خروج سابقتها): تفرّقات {v2_bad} "
          f"{'✅' if v2_bad == 0 else '⛔'} · V5 (شمعةُ الخروج ⟺ break): "
          f"تفرّقات {v5_bad} {'✅' if v5_bad == 0 else '⛔'}")

    firsts = [r["anchors"][0] for r in rows_out]
    firsts_brk = [a for a in firsts if a["exit"] == "break"]
    days2 = [r for r in rows_out if r["n_anchors"] >= 2]
    seconds = [r["anchors"][1] for r in days2]
    firsts_of2 = [r["anchors"][0] for r in days2]
    thirds = [a for r in rows_out for a in r["anchors"][2:]]
    n_all = sum(r["n_anchors"] for r in rows_out)
    n2 = len(seconds)
    rec = [r for r in rows_out if r["recovered"]]
    if rows_out:
        print(f"\n① الكلفة (العقد §⑤-1): أولى {n1:,} · خرجت بنيويًّا "
              f"{len(firsts_brk):,} ({_pf(_pct(len(firsts_brk), n1))}) · "
              f"**ثانية (A1) {n2:,} = {_pf(_pct(n2, n1))} من الأولى** "
              f"{'✅' if _pct(n2, n1) is not None and _pct(n2, n1) <= COST_MAX_PCT else '🔴'}"
              f" (الحدّ {COST_MAX_PCT:.0f}%) · ثالثةٌ فأكثر (A2) {len(thirds):,} · "
              f"كلُّ المراسي A2 {n_all:,} = +{_pf(_pct(n_all - n1, n1))}")
        dist = {}
        for r in rows_out:
            k = min(r["n_anchors"], 4)
            dist[k] = dist.get(k, 0) + 1
        print("   توزيعُ المراسي/يوم: " + " · ".join(
            f"{('4+' if k == 4 else k)}: {dist.get(k, 0):,} "
            f"({_pf(_pct(dist.get(k, 0), n1))})" for k in (1, 2, 3, 4)))
        print(f"   ثانيةٌ من الأولى المكسورة: "
              f"{_pf(_pct(n2, len(firsts_brk)))} · أيامُ الثانية "
              f"{'≥' if False else 'فوق أو عند'} الأرضية {FLOOR_SECOND}: "
              f"{'✅' if n2 >= FLOOR_SECOND else '⛔ لا حكم لهذي السنة'}")
        gaps = [a["gap_min"] for a in seconds if a.get("gap_min") is not None]
        if gaps:
            gs = sorted(gaps)
            q = lambda p: gs[min(len(gs) - 1, int(p * len(gs)))]  # noqa: E731
            print(f"   الفاصلُ خروجُ الأولى ⟶ الثانية (دقائق): وسيط "
                  f"{_med(gaps):.0f} · ربيعان {q(0.25)}/{q(0.75)} · "
                  f"أدنى {gs[0]} · أقصى {gs[-1]}")
        f3d = {}
        for a in seconds:
            f3d[a["f3"]] = f3d.get(a["f3"], 0) + 1
        if f3d:
            print("   وقتُ الثانية: " + " · ".join(
                f"{k}: {v:,}" for k, v in sorted(f3d.items(),
                                                key=lambda kv: -kv[1])))

        print(f"\n② الجودة (العقد §⑤-2 — الحاكمُ كاسح30 من سعر كرت M5 · "
              f"التسامح {QUALITY_TOL_PP} نقطة)")
        qs = [quality_row("الأولى (كلُّها = A0)", firsts),
              quality_row("الأولى في أيام الثانية", firsts_of2),
              quality_row("الثانية (A1)", seconds),
              quality_row("الثالثة فأكثر (A2)", thirds)]
        print_quality(qs)
        q1, q2 = qs[0], qs[2]
        if q1["p5"] is not None and q2["p5"] is not None:
            d5 = q2["p5"] - q1["p5"]
            d30 = (q2["p30"] - q1["p30"]) if (q1["p30"] is not None
                                              and q2["p30"] is not None) else None
            ok_q = d5 >= -QUALITY_TOL_PP
            print(f"  ⚖️ الحاكم: كاسح-من-د5(الثانية) − (الأولى) = {d5:+.1f} نقطة "
                  f"{'✅' if ok_q else '🔴'} (الحدّ {-QUALITY_TOL_PP:+.1f}) · "
                  f"الرفيقُ كاسح30(من سعر المِرساة) {_fmt(d30, '+.1f')} نقطة "
                  f"{'يوافق' if (d30 is None or (d30 >= 0) == (d5 >= 0)) else '🔴 يناقض'}"
                  f" · وحكمُ السنوات الثلاث في ملف النتيجة لا هنا.")
        print(f"\n③ الاسترجاع (العقد §⑤-3): «مسترجَع» {len(rec):,} = "
              f"{_pf(_pct(len(rec), n1))} من أيام الأولى "
              f"{'✅' if _pct(len(rec), n1) is not None and _pct(len(rec), n1) >= RECOVER_MIN_PCT else '🔴'}"
              f" (الحدّ {RECOVER_MIN_PCT}%) · منهم بلغت الثانيةُ +50% (من سعرها) "
              f"{sum(1 for r in rec if r['anchors'][1]['kasih50']):,} · +100% "
              f"{sum(1 for r in rec if r['anchors'][1]['kasih100']):,}")
        if rec:
            top = sorted(rec, key=lambda r: -r["anchors"][1]["mg_after"])[:8]
            print("   أكبرُ ثمانية مسترجَعين: " + " · ".join(
                f"${r['sym']} {r['day'][5:]} {r['anchors'][1]['anchor_ny']} "
                f"{r['anchors'][1]['mg_after']:+.0f}%" for r in top))

    if syms:
        print(f"\n④ سلاسلُ الرموز ({one_day}):")
        for sym in syms:
            ch = chains_last.get(sym)
            if not ch:
                print(f"   ${sym}: لا مِرساةَ أولى (لم يعبر المرشِّح/البوّابات)"
                      + (" أو خارج الملفّ" if sym not in chains_last else ""))
                continue
            for a in ch:
                print(f"   ${sym} #{a['idx']} مِرساة {a['anchor_ny']} عند "
                      f"{a['entry']:.4g} (قاع {a['anchor_low']:.4g}) · e5 "
                      f"{_fmt(a['e5'], '.4g')} · خروج {a['exit']} "
                      f"{a['exit_ny'] or ''} · mg {a['mg_after']:+.1f}% · "
                      f"كاسح30 {'✅' if a['kasih30'] else '—'} · من د5 "
                      f"{'✅' if a['kasih30_from5'] else '—'} · "
                      f"R(T10) {_fmt(a['r_t10'])}"
                      + (f" · بعد الخروج بـ{a['gap_min']} دقيقة"
                         if a.get("gap_min") is not None else ""))
        v3, v3_line = v3_check(expect, chains_last)
        print("🔒 " + v3_line)
        if v3 is False:
            print("\n⛔ V3: شاهدُ الحالة لم يُعَد إنتاجُه ⇒ عطبُ أداةٍ أو فرضيةٌ "
                  "باطلة — يُعلَن قبل السنوات (لا يُخمَّن).")
            return 3

    print("\n⚠️ حدودُ صدقٍ (العقد §⑧): لمسٌ لا تنفيذ · يومُ المِرساة وحده · "
          "الإعادةُ بالقاعدة المجمَّدة (بلا ساعة الحائط) · الثانية مجتمعٌ "
          "اختير بكسر الأولى (ليس سببيًّا) · الكلفةُ بالمراسي لا بالرسائل.")
    if not one_day:
        _cov_bad, _cov_line = KS.coverage_verdict(year, n_files, n_missing,
                                                  n1)
        print(_cov_line)
        if _cov_bad:
            print("\n⛔ بوّابةُ صلاحية V4: تغطيةٌ ناقصة أو صفرُ مراسٍ ⇒ "
                  "**عطبُ أداةٍ لا نتيجة** — لا حكم.")
            return 3
        if n2 == 0:
            print("\n⛔ V1: صفرُ مِرساةٍ ثانية في سنةٍ كاملة ⇒ ذراعٌ خامدة (no-op)"
                  " — عطبُ أداةٍ لا نتيجة.")
            return 4
    if one_day and n_files == 0:
        print(f"\n⛔ يومُ {one_day} لم يُقَس (ملفٌّ غائب/تعذّر) ⇒ لا حكم "
              "ولا يُقرأ الخروجُ نجاحًا.")
        return 3
    if v0_bad or v2_bad or v5_bad:
        print("\n⛔ بوّابةُ صلاحية (V0/V2/V5) ساقطة ⇒ عطبُ أداةٍ لا نتيجة.")
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
