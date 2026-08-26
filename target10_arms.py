#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯 **T-TARGET10** — «تجربةُ الهدف»: هل هدفُ ربحٍ ‏+10% يُحسّن الحصيلةَ
المحقَّقة لمركزٍ يُفتح عند كرت M5؟ (أداةُ قياسٍ تاريخيّ).

العقد: `target10_prereg.md` — **مدفوعٌ قبل أيّ رقم** (‏`16b4d1f`)، ولا معيارَ
يُحرَّك بعده. أمرُ المالك (2026-08-26): «سجل تجربة الهدف».

⚖️ **مقياسٌ واحدٌ لا اثنان:** الأنبوبةُ من `kasih_scan` بالاسم (‏`parse_day` ·
`prescreen` · `first_anchor` · `resolve` · `f2_usd5` · `coverage_verdict`) ·
سعرُ الدخول من `tier_days_report.true_e5` بالاسم · الخصائصُ من
`kasih2_scan.k2_features` · والفئةُ من `Super_stock.liq_tier` حرفيًّا.

🔒 **قراءة/قياسٌ فقط:** لا تلغرام ولا كتابةَ حالةٍ ولا مساسَ بعتبة، والإنتاجُ
لا يستورد هذا الملف. الأذرعُ الأربع تُحسَب على الصفوف نفسِها في تمريرةٍ واحدة
⇒ ميزانيةٌ واحدةٌ بالبناء.
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
import kasih2_scan as K2                                          # noqa: E402
import tier_days_report as TD                                     # noqa: E402
import Super_stock as S                                           # noqa: E402

MIN_MS = 60_000
TARGETS = (10.0, 20.0, 30.0)      # سلّمُ العقد §② — T10 الحاكمة ولا ذراعَ خامسة
FLOOR_ROWS = 150                  # أرضيةُ الحكم (العقد §④)
WINSOR_R = 10.0                   # ملحق ⑩ — سقفُ التشذيب لكلّ صفّ (‏±10R)
TIER_ORDER = ("قوي", "متوسط", "ضعيف", "بلا تصنيف")


def arm_exit(rows, a_ms: int, anchor_low: float, e5: float, tgt_pct=None):
    """خروجُ ذراعٍ واحدة — نقيّةٌ (العقد §② حرفيًّا).

    تُقيَّم الشموعُ التي بدايتُها `a_ms + 5د` فصاعدًا **حصرًا** (شمعةُ الدخول
    مستبعَدة — «رأسُ شمعة التعبئة مُستبعَد»). في كلّ شمعة **الوقفُ أوّلًا**:
    إغلاقٌ دون `anchor_low` ⇒ خروجٌ بالإغلاق ولو لمس رأسُها الهدف (قراءةٌ
    متحفّظة ضدّ أذرع الهدف)؛ ثم رأسٌ يبلغ `e5×(1+الهدف)` ⇒ خروجٌ **بسعر
    الهدف** (افتراضُ أمر الحدّ — حدُّ صدقٍ مُعلَن). وإلّا إغلاقُ آخر شمعة.

    تُرجع `(سعرُ الخروج، النوع break/target/eod)` أو `(None, None)` إن لم
    توجد شمعةُ تقييمٍ واحدة."""
    tgt = (e5 * (1.0 + float(tgt_pct) / 100.0)
           if tgt_pct is not None else None)
    last = None
    for b in rows:
        t, _o, h, _l, c, _v = b
        if t < a_ms + KS.ENTRY5_MIN * MIN_MS:
            continue
        last = float(c)
        if c < anchor_low:
            return (float(c), "break")
        if tgt is not None and h >= tgt:
            return (float(tgt), "target")
    return ((last, "eod") if last is not None else (None, None))


def mgday_pct(rows, a_ms: int, e5: float):
    """📏 §B — أقصى رأسٍ **بعد الدخول حتى نهاية اليوم بلا قطعٍ** عند الخروج
    البنيويّ (درسُ `HUIZ`: المقصوصُ وحده يكذب على «كم أعطى السهم»)."""
    mx = None
    for b in rows:
        if b[0] < a_ms + KS.ENTRY5_MIN * MIN_MS:
            continue
        mx = b[2] if mx is None else max(mx, b[2])
    return ((mx / e5 - 1.0) * 100.0
            if (mx is not None and e5 and e5 > 0) else None)


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return (sum(xs) / len(xs)) if xs else None


def _med(xs):
    xs = [x for x in xs if x is not None]
    return st_.median(xs) if xs else None


def _fmt(v, spec="+.3f"):
    return format(v, spec) if v is not None else "—"


def _axis_table(rows, year):
    """§B — جدولُ التقاط المتحرّكين (وصفيٌّ بالإعلان — العقد §⑥)."""
    movers30 = [r for r in rows if (r["mgday"] or 0) >= 30.0]
    movers50 = [r for r in rows if (r["mgday"] or 0) >= 50.0]
    print(f"\n  ── §B التقاطُ المتحرّكين — {year} · متحرّك30 = "
          f"{len(movers30)} · متحرّك50 = {len(movers50)} "
          f"(من {len(rows)} صفًّا مؤهَّلًا · المقياسُ mgday غيرُ المقصوص) ──")
    axes = [(f"فئة {t}", lambda r, t=t: r["tier"] == t) for t in TIER_ORDER]
    axes += [("J1 توليفة", lambda r: bool(r["j1"])),
             ("أقوى خليّة (قوي×75%+)", lambda r: bool(r["j1_top"])),
             ("فجوة فوق 75%", lambda r: r.get("f5") == "فوق 75%")]
    print(f"  {'المحور':26} {'ن':>6} {'م30 فيه':>8} {'recall30':>9} "
          f"{'precision30':>12} {'recall50':>9}")
    for name, pred in axes:
        grp = [r for r in rows if pred(r)]
        m30 = sum(1 for r in grp if (r["mgday"] or 0) >= 30.0)
        m50 = sum(1 for r in grp if (r["mgday"] or 0) >= 50.0)
        rec30 = (100.0 * m30 / len(movers30)) if movers30 else None
        rec50 = (100.0 * m50 / len(movers50)) if movers50 else None
        prec = (100.0 * m30 / len(grp)) if grp else None
        low = " (دون أرضية 40 ⇒ لا حكم)" if len(grp) < 40 else ""
        print(f"  {name:26} {len(grp):>6} {m30:>8} "
              f"{_fmt(rec30, '5.1f') + '%':>9} {_fmt(prec, '5.1f') + '%':>12} "
              f"{_fmt(rec50, '5.1f') + '%':>9}{low}")
    print("  🔴 دائريّةٌ مُعلَنة (العقد §⑥): وصفُ تغطيةٍ لا إثباتُ تنبّؤ.")


def main() -> int:                                                # noqa: C901
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("TGT_YEAR") or "").strip()
    one_day = (os.environ.get("TGT_DAY") or "").strip()
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
        print("⛔ لا TGT_YEAR ولا TGT_DAY.")
        return 2
    KS.log(f"🎯 T-TARGET10 — {'يوم ' + one_day if one_day else 'سنة ' + year}"
           f" · أيام {len(days)} · كون [{KS.PRICE_LO}, {KS.PRICE_HI}]$ · "
           f"أذرع T0/T10/T20/T30 · العقد target10_prereg.md")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_syms = n_screened = n_anchored = 0
    n_gapcap = 0
    n_broke5 = n_noafter = n_rundef = 0
    v0_bad = 0
    out_path = f"target10_rows_{year or one_day}.jsonl"
    fout = open(out_path, "w", encoding="utf-8")

    for di, day in enumerate(seed_days + days):
        seeding = di < len(seed_days)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
            continue
        dest = f"/tmp/tgt10-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            n_missing += 0 if seeding else 1
            continue
        universe = ({s for s, c in prev_close.items()
                     if KS.PRICE_LO <= c <= KS.PRICE_HI}
                    if not seeding else set())
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
            a_ms = int(e["anchor_ms"])
            entry = float(e["price"])
            pc = prev_close.get(sym)
            gap = (entry / pc - 1.0) * 100.0 if pc else None
            if gap is not None and abs(gap) > KS.GAP_CAP:
                n_gapcap += 1
                continue
            res = KS.resolve(b, a_ms, entry)
            if res is None:
                continue
            n_anchored += 1
            e5, broke5 = TD.true_e5(b, a_ms, entry)
            if broke5:
                n_broke5 += 1        # العقد §② استبعاد 1 — يُعَدّ لا يُطوى
                continue
            ab = next(bb for bb in b if bb[0] == a_ms)
            alow = float(ab[3])      # الخامُّ لا المدوَّر (تطابقُ resolve)
            t0 = arm_exit(b, a_ms, alow, e5 or 0.0, None)
            if e5 is None or t0[0] is None:
                n_noafter += 1       # العقد §② استبعاد 2
                continue
            # ‏V0: تكافؤُ T0 مع `resolve` بت-بت (العقد §④) — تفرّقٌ = عطب
            r_break = (res["exit"] == "break")
            if (t0[1] == "break") != r_break:
                v0_bad += 1
                KS.log(f"   🔴 V0: تفرّقُ نوع الخروج في {sym} يوم {day} "
                       f"({t0[1]} مقابل {res['exit']})")
            usd5 = KS.f2_usd5(b, a_ms)
            usd1 = float(e.get("usd") or 0)
            f2key = S._ignition_candle_class(usd5)[0]
            k2 = K2.k2_features(b, a_ms, entry, f2key, gap, usd1, usd5)
            tev = {"stage": "M5", "k2": k2, "class": (f2key, ""),
                   "anchor_price": entry, "prev_close": pc}
            t = S.liq_tier(tev)
            j1, j1_top = S.kasih_j1(tev)
            ev = K2.entry_view(b, a_ms, entry, pc)
            risk = e5 - alow
            r_ok = risk > 0
            if not r_ok:
                n_rundef += 1        # العقد §② استبعاد 3 (من تجميع R وحده)
            row = {"sym": sym, "day": day, "anchor_ms": a_ms,
                   "e1": entry, "e5": round(e5, 6),
                   "anchor_low": round(alow, 6),
                   "risk": round(risk, 6), "r_ok": bool(r_ok),
                   "tier": (t[0] if t else "بلا تصنيف"),
                   "green": (t[1] if t else None),
                   "j1": bool(j1), "j1_top": bool(j1_top),
                   "f2": f2key,
                   "f5": (KS.f5_bucket(gap) if gap is not None else None),
                   "gap_pct": (round(gap, 1) if gap is not None else None),
                   "mg5": (ev or {}).get("mg5"),
                   "mgday": mgday_pct(b, a_ms, e5),
                   "exit_res": res["exit"]}
            for nm, tp in (("t0", None), ("t10", TARGETS[0]),
                           ("t20", TARGETS[1]), ("t30", TARGETS[2])):
                px, kind = (t0 if tp is None
                            else arm_exit(b, a_ms, alow, e5, tp))
                pct = (px / e5 - 1.0) * 100.0
                row[nm] = {"px": round(px, 6), "kind": kind,
                           "pct": round(pct, 2),
                           "r": (round((px - e5) / risk, 4)
                                 if r_ok else None)}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_out.append(row)
        prev_close.update(closes)
        if n_files % 20 == 0:
            KS.log(f"   📦 {n_files}/{len(days)} يومًا · مرشَّح "
                   f"{n_screened:,} · مراسٍ {n_anchored:,} · "
                   f"مؤهَّل {len(rows_out):,}")
    fout.close()

    print("\n" + "=" * 74)
    print(f"🎯 T-TARGET10 — {'يوم ' + one_day if one_day else 'سنة ' + year}"
          f" · العقد target10_prereg.md (مدفوعٌ قبل أيّ رقم)")
    print("=" * 74)
    print(KS.MEASURE_CUT_NOTE)
    print(f"📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · رمز-يوم بالكون "
          f"{n_syms:,} · عبر المرشِّح {n_screened:,} · "
          f"**مراسٍ {n_anchored:,}** · استُبعد بتشويه تقسيم {n_gapcap}")
    print("🔗 فحصُ تكامل: عددُ المراسي يجب أن يطابق kasih_result لهذي السنة "
          "**بت-بت** — تفرّقٌ = عطبُ أداةٍ لا نتيجة.")
    print(f"🚧 الاستبعاداتُ المُعلَنة (العقد §②): كُسر قبل الخمس {n_broke5} · "
          f"بلا شموعِ تقييم {n_noafter} · R غيرُ مُعرَّف {n_rundef} "
          f"(يبقى في النِّسَب ويخرج من R وحده)")
    print(f"🔒 V0 (تكافؤ T0 مع resolve): تفرّقات {v0_bad} "
          f"{'✅' if v0_bad == 0 else '⛔ عطبُ أداة'}")

    if rows_out:
        n = len(rows_out)
        print(f"\n① §A — الأذرعُ الأربع على {n:,} صفًّا مؤهَّلًا "
              f"({'أرضيةُ الحكم مستوفاة ✅' if n >= FLOOR_ROWS else '⛔ دون أرضية 150 ⇒ لا حكم'})")
        print(f"  {'الذراع':8} {'ن(R)':>7} {'متوسط R':>9} {'مشذّب±10':>9} "
              f"{'وسيط R':>8} {'وسيط %':>8} {'موجب %':>8} {'عبّأ الهدف %':>12}")
        stats = {}
        stats_w = {}
        for nm, ttl in (("t0", "T0"), ("t10", "T10"),
                        ("t20", "T20"), ("t30", "T30")):
            rs = [r[nm]["r"] for r in rows_out if r[nm]["r"] is not None]
            rw = [max(-WINSOR_R, min(WINSOR_R, x)) for x in rs]
            ps = [r[nm]["pct"] for r in rows_out]
            wins = sum(1 for p in ps if p > 0)
            fills = sum(1 for r in rows_out if r[nm]["kind"] == "target")
            stats[nm] = _mean(rs)
            stats_w[nm] = _mean(rw)
            print(f"  {ttl:8} {len(rs):>7,} {_fmt(_mean(rs)):>9} "
                  f"{_fmt(_mean(rw)):>9} {_fmt(_med(rs)):>8} "
                  f"{_fmt(_med(ps), '+.1f'):>8} "
                  f"{100.0 * wins / len(ps):>7.1f}% "
                  f"{100.0 * fills / len(ps):>11.1f}%")
        if stats.get("t0") is not None and stats.get("t10") is not None:
            print(f"\n  ⚖️ الحاكم (العقد §④): متوسط R(T10) − متوسط R(T0) = "
                  f"{stats['t10'] - stats['t0']:+.3f}R خامًّا · "
                  f"{stats_w['t10'] - stats_w['t0']:+.3f}R مشذَّبًا (ملحق ⑩)"
                  " — والحكمُ عبر السنوات الثلاث مجمَّعةً لا هنا، واختلافُ"
                  " إشارة الخام عن المشذَّب = «غيرُ قابلٍ للقراءة».")
            # 🔎 ملحق ⑩ — فحصُ التركُّز: نصيبُ أكبر خمسة صفوف من فرق T10−T0
            _dfs = [r["t10"]["r"] - r["t0"]["r"] for r in rows_out
                    if r["t10"]["r"] is not None and r["t0"]["r"] is not None]
            if _dfs:
                _top5 = sorted(_dfs, key=abs, reverse=True)[:5]
                print(f"  🔎 تركُّز الفرق (ملحق ⑩): مجموعُ فروق الصفوف "
                      f"{sum(_dfs):+.1f}R · أكبرُ خمسة "
                      f"{sum(_top5):+.1f}R "
                      f"({', '.join(f'{d:+.1f}' for d in _top5)})")

        print("\n② تفصيلُ الفئات (وصفيٌّ يُنشَر ولا يحكم — «القوي فيه خاسرة؟»)")
        print(f"  {'الفئة':10} {'ن':>6} {'T0 متوسط R':>11} {'T0 موجب%':>9} "
              f"{'T10 متوسط R':>12} {'T10 موجب%':>10}")
        for tk in TIER_ORDER:
            g = [r for r in rows_out if r["tier"] == tk]
            if not g:
                continue
            r0 = _mean([r["t0"]["r"] for r in g if r["t0"]["r"] is not None])
            r1 = _mean([r["t10"]["r"] for r in g
                        if r["t10"]["r"] is not None])
            w0 = 100.0 * sum(1 for r in g if r["t0"]["pct"] > 0) / len(g)
            w1 = 100.0 * sum(1 for r in g if r["t10"]["pct"] > 0) / len(g)
            print(f"  {tk:10} {len(g):>6} {_fmt(r0):>11} {w0:>8.1f}% "
                  f"{_fmt(r1):>12} {w1:>9.1f}%")

        _axis_table(rows_out, year or one_day)

        if one_day:
            print(f"\n③ صفوفُ اليوم كلُّها ({len(rows_out)} — بلا قصّ):")
            for r in sorted(rows_out, key=lambda x: -(x["mgday"] or -999)):
                print(f"   ${r['sym']:6} فئة {r['tier']:6} خضراء "
                      f"{r['green'] if r['green'] is not None else '—'} "
                      f"J1 {'✅' if r['j1'] else '—'} · e5 {r['e5']:.4g} · "
                      f"mgday {_fmt(r['mgday'], '+.1f')}% · "
                      f"mg5 {_fmt(r['mg5'], '+.1f')}% · "
                      f"T0 {r['t0']['pct']:+.1f}% ({r['t0']['kind']}) · "
                      f"T10 {r['t10']['pct']:+.1f}% ({r['t10']['kind']})")

    print("\n⚠️ حدودُ صدقٍ (العقد §⑧): تعبئةُ الهدف افتراضُ أمرِ حدٍّ بلا "
          "انزلاقٍ ولا حجم ⇒ سقفٌ متفائل · الوقفُ أوّلًا داخل الدقيقة (ضدّ "
          "أذرع الهدف) · الفئةُ مُعادُ بناؤها لا ما رآه المالك · الحكمُ عبر "
          "السنوات الثلاث حصرًا.")
    if not one_day:
        _cov_bad, _cov_line = KS.coverage_verdict(year, n_files, n_missing,
                                                  n_anchored)
        print(_cov_line)
        if _cov_bad:
            print("\n⛔ بوّابةُ صلاحية: تغطيةٌ ناقصة أو صفرُ مراسٍ ⇒ "
                  "**عطبُ أداةٍ لا نتيجة** — لا حكم.")
            return 3
    if v0_bad:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
