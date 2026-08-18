#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📈🧮 **مِجَسُّ الرفعة التراكميّة** — عقدُه `cumrise_prereg.md` (مدفوعٌ قبل أيّ رقم).

أمرُ المالك 2026-08-18: «قِس الرفعة التراكميّة». السؤال: هل قياسُ رفعةِ المِرساة
على **نافذة `LIQ_CUM_MINUTES`** — بدل دقيقةٍ واحدة — يُقلّل التأخّرَ بلا فقدِ
إثمارٍ ولا إغراق؟

⚖️ **صفرُ رقمٍ مخترَع:** ‏5% رقمُ المالك ولا يُمَسّ · و3 دقائقَ نافذةُ الإنتاج
اليوم للأرضية الدولاريّة · و5 دقائقَ منقولةٌ من `G3` في `gate_prereg §④`.
🔒 **مقياسٌ واحدٌ لا اثنان:** البوّابةُ من `gate_probe.gate_trace` **نفسِها**،
والإثمارُ من `liq_move_probe.fruit` **نفسِها** — لا نسخةَ ثانية.
🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
"""
import os
import sys
import time

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402
import gate_probe as GP                                            # noqa: E402
import liq_move_probe as LM                                        # noqa: E402
import m0_probe as MZ                                              # noqa: E402

# ⚙️ **الأذرعُ الأربع مثبَّتةٌ في `cumrise_prereg.md §④` — ولا تُزاد بعد الأرقام.**
ARMS = {
    "R0": {},
    "R1": {"rise_n": bot.LIQ_CUM_MINUTES},
    "R2": {"rise_n": 5},
    "R3": {"rise_any": bot.LIQ_CUM_MINUTES},
}
ARM_DESC = {
    "R0": "الإنتاجُ كما هو — رفعةُ دقيقةٍ واحدة",
    "R1": f"تراكميُّ {bot.LIQ_CUM_MINUTES} دقائقَ (الحاكمة)",
    "R2": "تراكميُّ 5 دقائقَ (حساسيّةُ النافذة · `engineering`)",
    "R3": "اتّحادٌ: دقيقةٌ **أو** تراكميّ — حدٌّ أعلى رتيبٌ لا يكتم",
}
LATE_GAIN_MIN = 5.0         # 🔒 حدُّ `T-GATE` نفسُه — منقولٌ لا مخترَع
ALERT_MAX_GROWTH = 0.50     # engineering — سقفُ زيادةِ الإشعارات (‏§⑤-3)
FRUIT_MIN_N = 20            # أرضيةُ مقام الإثمار (‏§⑥)
LATE_MIN_N = 8              # أرضيةُ وسيط التأخّر (‏§⑥)
MOVER_MIN_N = 5             # أرضيةُ المعيار ④ (‏§⑥)


def _b(i, o, h, l, c, v):
    return {"t": i * 60_000, "o": o, "h": h, "l": l, "c": c, "v": v}


def _lock_arms():
    """🔒 `LOCK-ARMS` — ثلاثةُ حرّاسٍ منفَّذةٌ لا موصوفة.

    `V1` البوّابةُ تطابق الإنتاج (تُستعار من `gate_probe._lock_g0` **بالاسم**
    فلا يصير للمشروع مقياسان) · `V2` كلُّ ذراعٍ **تفرّق فعلًا** على عيّنةٍ
    مبنيّة — وإلّا فهي `no-op` تُقرأ «لا فرق» كذبًا · وشاهدُ **`K2`**: `R1`
    تكتم ما يُطلقه `R0` (فليست مجموعةً فوقه) و`R3` تُعيده."""
    ok, notes = GP._lock_g0()
    notes = ["(من `gate_probe`) " + n for n in notes]

    # ① صعودٌ ثلاثيٌّ 3% × 3: لا دقيقةَ تبلغ 5% والتراكميُّ 9.3%
    flat = [_b(i, 1.0, 1.0, 1.0, 1.0, 500) for i in range(8)]
    climb = flat + [_b(8, 1.0000, 1.0300, 1.0000, 1.0300, 12_000),
                    _b(9, 1.0300, 1.0609, 1.0300, 1.0609, 12_000),
                    _b(10, 1.0609, 1.0927, 1.0609, 1.0927, 40_000),
                    _b(11, 1.0927, 1.0930, 1.0900, 1.0927, 100)]
    # ② هبوطٌ ثم قفزةُ 6%: الدقيقةُ تعبر والتراكميُّ سالب
    dropup = flat + [_b(8, 1.00, 1.00, 0.90, 0.90, 12_000),
                     _b(9, 0.90, 0.90, 0.82, 0.82, 12_000),
                     _b(10, 0.82, 0.8692, 0.82, 0.8692, 40_000),
                     _b(11, 0.8692, 0.8700, 0.8650, 0.8692, 100)]
    # ③ زحفٌ 1.6% × 5: تراكميُّ الثلاث 4.87% (دون الحدّ) والخمسِ 8.26%
    slow = [_b(i, 1.0, 1.0, 1.0, 1.0, 500) for i in range(6)]
    slow += [_b(6, 1.0000, 1.0160, 1.0000, 1.0160, 12_000),
             _b(7, 1.0160, 1.0323, 1.0160, 1.0323, 12_000),
             _b(8, 1.0323, 1.0488, 1.0323, 1.0488, 12_000),
             _b(9, 1.0488, 1.0656, 1.0488, 1.0656, 12_000),
             _b(10, 1.0656, 1.0826, 1.0656, 1.0826, 40_000),
             _b(11, 1.0826, 1.0830, 1.0800, 1.0826, 100)]
    cases = [
        ("صعودٌ ثلاثيّ", climb, {"R0": None, "R1": 10, "R2": 10, "R3": 10}),
        ("هبوطٌ ثم قفزة", dropup, {"R0": 10, "R1": None, "R2": None, "R3": 10}),
        ("زحفٌ خماسيّ", slow, {"R0": None, "R1": None, "R2": 10, "R3": None}),
    ]
    for name, bars, want in cases:
        got = {a: GP.anchor_of(bars, ARMS[a])[0] for a in ARMS}
        same = got == want
        notes.append(f"{name}: {got} · متوقَّع {want} {'✅' if same else '❌'}")
        ok = ok and same
    # 🔗 و`R3` **رتيبةٌ بنيويًّا**: لا تكتم دقيقةً يُطلقها `R0` في أيّ عيّنة
    for name, bars, _w in cases:
        f0 = set(GP.all_fires(bars, ARMS["R0"]))
        f3 = set(GP.all_fires(bars, ARMS["R3"]))
        good = f0 <= f3
        notes.append(f"{name}: `R3` ⊇ `R0` {'✅' if good else '❌'} "
                     f"({sorted(f0)} ⊆ {sorted(f3)})")
        ok = ok and good
    return ok, notes


def main():                                                       # noqa: C901
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("📈🧮 مِجَسُّ الرفعة التراكميّة — عقدُه `cumrise_prereg.md`\n")
    print(f"   النافذُ: قفزةٌ {bot.CONFIG['IGNITION_VOL_MULT']}× · أرضيةُ "
          f"${bot.LIQ_MIN_USD:,} على {bot.LIQ_CUM_MINUTES} دقائق · رفعةُ "
          f"{bot.LIQ_MIN_MOVE_PCT}% · موضعُ إغلاقٍ {bot.LIQ_CLOSE_POS_MIN}")
    print("   ⚖️ **‏5% رقمُ المالك ولا يُمَسّ** — المتغيّرُ نافذةُ قياسها.\n")
    ok, notes = _lock_arms()
    for n in notes:
        print("   🔒 " + n)
    if not ok:
        print("\n⛔ `LOCK-ARMS` سقط ⇒ **لا يُنشَر رقم** (خروج 3).")
        return 3
    print("   ✅ `LOCK-ARMS` عبر — والأذرعُ الأربعُ تفرّق فعلًا.\n")

    day = (os.environ.get("GATE_DAY") or "").strip() or None
    if day:
        back, nb = 0, len(MZ.day_minutes("AAPL", day=day) or [])
        if nb < 100:
            print(f"⛔ اليومُ المطلوب {day} بلا بياناتٍ لشاهد الضبط ⇒ لا قياس.")
            return 2
    else:
        day, back, nb = GP.resolve_day()
        if not day:
            print("⛔ لم تُوجَد جلسةٌ فيها بيانات خلال سبعةِ أيام ⇒ لا قياس.")
            return 2
    print(f"📅 **الجلسةُ المقيسة: {day}** (‏{back} يومًا للخلف · شاهدُ الضبط "
          f"`AAPL` {nb} شمعة) — تُحسَم مرّةً واحدةً للكلّ (‏`V3`).\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                        # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (نفسُ كونِ المُشغِّل · بلا استثناء)")

    import concurrent.futures as cf
    t0, data, pc, fails = time.time(), {}, {}, 0

    def _one(s):
        try:
            return (s, MZ.day_minutes(s, day=day), GP.prev_close(s, day))
        except Exception:                                        # noqa: BLE001
            return (s, None, None)

    # 🔒 `V5` — **ميزانيةٌ واحدة**: الشموعُ تُجلَب **مرّةً** والأذرعُ الأربعُ
    #    تُقاس عليها. (درسُ `T-CLIFF`: فرقٌ صنعتْه الميزانيةُ لا الذراع.)
    with cf.ThreadPoolExecutor(max_workers=GP.WORKERS) as pool:
        for s, bars, p in pool.map(_one, syms):
            if bars and len(bars) >= 5 and p:
                data[s], pc[s] = bars, p
            else:
                fails += 1
    print(f"📥 شموعُ اليوم ‏+ إغلاقُ الأمس: {len(data)} من {len(syms)} · "
          f"تعذّر {fails} (يُعَدّ ولا يُخمَّن) · {round(time.time() - t0, 1)}ث")
    if not data:
        print("⛔ صفرُ بيانات — لا قياس.")
        return 2

    movers, day_gain = [], {}
    for s, bars in data.items():
        hi = max(float(b["c"]) for b in bars)
        g = (hi / pc[s] - 1.0) * 100.0
        day_gain[s] = g
        if g >= GP.MOVER_PCT:
            movers.append(s)
    print(f"🏃 المتحرّكون (‏+{GP.MOVER_PCT:.0f}% فأكثر عن إغلاق الأمس): "
          f"**{len(movers)}** — {', '.join(sorted(movers)[:14])}"
          + (f"\n   ⚠️ **دون {MOVER_MIN_N} ⇒ المعيار ④ غيرُ مقيس** (‏§⑥)"
             if len(movers) < MOVER_MIN_N else "") + "\n")

    res, insane = {}, 0
    for an, arm in ARMS.items():
        late, fr, unres, fired, alerts, anch = [], [], 0, {}, 0, {}
        for s, bars in data.items():
            i, t = GP.anchor_of(bars, arm)
            alerts += len(GP.all_fires(bars, arm))
            if i is None:
                continue
            fired[s] = i
            anch[s] = t
            lt = (float(t["price"]) / pc[s] - 1.0) * 100.0
            if abs(lt) > GP.LATE_SANE_MAX:
                insane += 1
            else:
                late.append(lt)
            f = LM.fruit(bars, i, t["price"])
            if f is None:
                unres += 1
            else:
                fr.append(f)
        hit = sum(1 for f in fr if f >= LM.FRUIT_PCT)
        res[an] = {"late": late, "late_med": GP._med(late), "fired": fired,
                   "anch": anch, "alerts": alerts, "fruit_n": len(fr),
                   "fruit_pct": (100.0 * hit / len(fr)) if fr else None,
                   "unres": unres}

    if not any(r["fired"] for r in res.values()):
        print("⛔ صفرُ حدثٍ في هذي الجلسة ⇒ **لا مادّةَ تُقاس** (خروج 5 · `V6`).")
        return 5

    b = res["R0"]
    print("=" * 76)
    print("① الجدولُ — التأخّرُ والإثمارُ والإشعارات")
    print("=" * 76)
    print("  الذراع | أسهمٌ تُنبَّه | وسيطُ التأخّر | أثمر٪ (مقام) | إشعارات | متحرّكون")
    for an in ARMS:
        r = res[an]
        lm = ("—" if r["late_med"] is None or len(r["late"]) < LATE_MIN_N
              else f"{r['late_med']:+.1f}%")
        fp = ("—" if r["fruit_pct"] is None or r["fruit_n"] < FRUIT_MIN_N
              else f"{r['fruit_pct']:.1f}% ({r['fruit_n']})")
        mv = sum(1 for s in movers if s in r["fired"])
        print(f"  {an:<6} | {len(r['fired']):>11} | {lm:>13} | {fp:>13} | "
              f"{r['alerts']:>7} | {mv:>8}/{len(movers)}")
    for an in ARMS:
        print(f"     {an} = {ARM_DESC[an]}")
    if insane:
        print(f"  ⚠️ استُبعد {insane} تأخّرًا فوق {GP.LATE_SANE_MAX:.0f}% "
              "(تشويهُ تقسيمٍ) — يُعَدّ ويُسمّى ولا يُخمَّن.")

    print("\n" + "=" * 76)
    print("② الحكمُ بالمعايير الأربعة — كما سُجّلت قبل الأرقام")
    print("=" * 76)
    for an in ARMS:
        if an == "R0":
            continue
        r = res[an]
        lines, verdict = [], True
        if (r["late_med"] is None or b["late_med"] is None
                or len(r["late"]) < LATE_MIN_N or len(b["late"]) < LATE_MIN_N):
            lines.append("① التأخّر: ⚠️ **مقامٌ دون الأرضية ⇒ لا يُقرأ**")
            verdict = False
        else:
            d = b["late_med"] - r["late_med"]
            good = d >= LATE_GAIN_MIN
            verdict = verdict and good
            lines.append(f"① التأخّر: {b['late_med']:+.1f}% ⟶ "
                         f"{r['late_med']:+.1f}% = **{d:+.1f} نقطة** "
                         f"{'✅' if good else '🔴'} (الحدّ {LATE_GAIN_MIN:+.0f})")
        if (r["fruit_pct"] is None or b["fruit_pct"] is None
                or r["fruit_n"] < FRUIT_MIN_N or b["fruit_n"] < FRUIT_MIN_N):
            lines.append("② الإثمار: ⚠️ **مقامٌ دون الأرضية ⇒ لا يُقرأ**")
            verdict = False
        else:
            d = r["fruit_pct"] - b["fruit_pct"]
            good = d >= -GP.JITTER_PP
            verdict = verdict and good
            lines.append(f"② الإثمار: {b['fruit_pct']:.1f}% ⟶ "
                         f"{r['fruit_pct']:.1f}% = **{d:+.1f} نقطة** "
                         f"{'✅' if good else '🔴'} (الحدّ {-GP.JITTER_PP:+.1f})")
        gr = ((r["alerts"] - b["alerts"]) / b["alerts"]) if b["alerts"] else None
        good = gr is not None and gr <= ALERT_MAX_GROWTH
        verdict = verdict and bool(good)
        lines.append(f"③ الإشعارات: {b['alerts']} ⟶ {r['alerts']} = "
                     + (f"**{gr * 100:+.0f}%** " if gr is not None else "— ")
                     + f"{'✅' if good else '🔴'} (الحدّ +{ALERT_MAX_GROWTH:.0%})")
        lost = sorted(s for s in movers if s in b["fired"] and s not in r["fired"])
        if len(movers) < MOVER_MIN_N:
            lines.append("④ المتحرّكون: ⚠️ **غيرُ مقيس** (دون الأرضية) ⇒ لا يُعَدّ")
            verdict = False
        else:
            good = not lost
            verdict = verdict and good
            lines.append(f"④ متحرّكٌ مفقود: {len(lost)} "
                         + (f"({', '.join('$' + x for x in lost)}) " if lost else "")
                         + ("✅" if good else "🔴"))
        print(f"\n  **{an}** — {ARM_DESC[an]}")
        for ln in lines:
            print("     " + ln)
        print("     ⇒ " + ("🥇 **تستوفي الأربعة ⇒ تُعرَض اقتراحًا للمالك**"
                           if verdict else
                           "🔴 **لا تستوفي ⇒ لا تُقترَح** (ولا يُحرَّك حدّ)"))

    print("\n" + "=" * 76)
    print("③ الشاهدان المسمّيان قبل الأرقام (‏§⑪) — لا معيارَ بل عرض")
    print("=" * 76)
    for s in ("PFSA", "WFF"):
        if s not in data:
            print(f"  ${s}: ⚠️ ليس في كونِ اليوم أو تعذّرت بياناتُه — لا يُخمَّن.")
            continue
        print(f"  ${s} (قمّةُ اليوم {day_gain[s]:+.1f}% عن إغلاق الأمس):")
        for an in ARMS:
            i = res[an]["fired"].get(s)
            if i is None:
                print(f"     {an}: **لا يُطلِق**")
                continue
            t = res[an]["anch"][s]
            lt = (float(t["price"]) / pc[s] - 1.0) * 100.0
            print(f"     {an}: الدقيقة {i} · سعر ${t['price']:.4f} · "
                  f"تأخّر **{lt:+.1f}%** · رفعةُ الدقيقة {t['rise']:.1f}% · "
                  f"التراكميّة {t['rise_eff']:.1f}%")

    print("\n" + "=" * 76)
    print("④ حدودُ صدقٍ تُقرأ **مع** الجدول لا بعده (‏§⑩)")
    print("=" * 76)
    print("  1. **جلسةٌ واحدة** ⇒ اتّجاهٌ لا حكمُ ربحيّة · **ولا صفقةَ تُقاس**.")
    print(f"  2. «أثمر» = **لمسُ +{LM.FRUIT_PCT:.0f}% خلال {LM.FRUIT_MIN} دقيقة** "
          "لا ربحٌ محقَّق ولا تنفيذ.")
    print("  3. **دائريّةٌ جزئيّةٌ لا تُنفى**: الذراعُ تنتقي إشعاراتٍ أقربَ للحركة "
          "— انتقاءٌ لا تنبّؤ.")
    print("  4. **الإعادةُ ترى كلَّ دقيقة** والحيُّ يلفّ كلَّ ‏≈60 ثانية ⇒ أعدادُ "
          "الإشعارات **سقفٌ** والنِّسَبُ أدقُّ منها.")
    print("  5. **التأخّرُ يبتلع فجوةَ الافتتاح** — جزءٌ منه لا تسبقه بوّابةٌ "
          "لحظيّةٌ أصلًا فلا يُنسَب كلُّه للبوّابة.")
    print(f"  6. وأيُّ فرقٍ دون **{GP.JITTER_PP} نقطة** داخلَ الضجيج المقيس "
          "ولا يُدَّعى.")
    print("  7. **والفلترُ المشحون خارج هذا القياس** — يُقاس الزنادُ لا التسليم.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
