#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🛑📊 **T-EXIT-STOP** — «وقفٌ من الشموع» أذرعًا مقيسة · وتصنيفٌ ثلاثيّ.

عقدُها `exit_stop_prereg.md` **مدفوعٌ قبل أيّ رقم** (‏`6b80802`). أمرُ المالك
بنصّه: «يكون معطيني **وقف خسارة حسب الشموع** … عندنا **قرار دخول باقي قرار
الخروج** … **ابدا**».

🔒 **مقياسٌ واحدٌ لا اثنان:** كشفُ المِرساة والحسمُ من `kasih_scan` **بالاسم**
(‏`parse_day`/`prescreen`/`first_anchor`/`resolve`/`f2_usd5`/`wilson`) وخصائصُ
التصنيف من `kasih2_scan` **بالاسم** (‏`j1_bucket`/`c3`/`c4`/`v2`/`v3`) —
والجديدُ هنا **أذرعُ الوقف §③ ومقاييسُ §⑤ وحدَها**. قراءة/قياسٌ فقط: لا كرون ·
لا كتابةَ حالة · لا تلغرام · والإنتاجُ لا يستورد هذا الملف.

⚠️ **قصورُ صياغةٍ مُعلَنٌ في §⑤ يُحسَم هنا بقراءةٍ واحدةٍ موحّدةٍ للأذرع
الأربع** (فلا تُحابي واحدةً منها): العقدُ نصّ أن `R = (+30% أو الوقف) ÷ المسافة`
**ولم ينصّ على مصير مَن لا يبلغ الهدفَ ولا يُضرَب** ⇒ المعتمَد: **الخروجُ
بإغلاق آخر شمعةٍ في اليوم**. وهي قراءةٌ **محايدةٌ بين الأذرع** لأنها لا تعتمد
على المستوى إطلاقًا.
"""
import gzip
import json
import os
import sys

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import ah_scan as AH                                              # noqa: E402
import kasih2_scan as K2                                          # noqa: E402
import kasih_scan as KS                                           # noqa: E402
import Super_stock as S                                           # noqa: E402

MIN2 = 60_000
PRE_WIN_MIN = 15          # نافذةُ `S3` — §③ حرفيًّا
ARMS = ("S0", "S1", "S2", "S3")
FLOOR_TIER_YEAR = 40      # §⑥ — أرضيةُ المِرساة لكلّ فئةٍ في كلّ سنة
COVERAGE_MAX_MISS = 0.05  # `V4` — أقصى نسبةِ أيامٍ مفقودةٍ يُقبَل معها حكم


def coverage_bad(n_files: int, n_missing: int) -> bool:
    """`V4` — هل التغطيةُ ناقصةٌ بما يُبطل الحكم؟ **نقيّةٌ لتُقفَل سلوكيًّا**:
    قفلٌ بنيويٌّ يُثبت أن الاسمَ داخلَ شرط الإيقاف **ولا يرى دلالةَ العتبة**،
    وقد نجت منه طفرةُ قلبِ `>` إلى `<`. ⚖️ **والمقامُ كلُّ أيام السنة المُدرَجة**
    (مقيسةٌ + مفقودة) · وصفرُ أيامٍ ⇒ **لا حكم** (لا تُقرأ «تغطيةٌ تامّة»)."""
    tot = int(n_files or 0) + int(n_missing or 0)
    if tot <= 0:
        return True
    return (int(n_missing or 0) / float(tot)) > COVERAGE_MAX_MISS
FLOOR_TIER_SWEEP = 30     # §⑥ — أرضيةُ الكاسحين لكلّ فئةٍ مجمَّعًا (تُقرأ لاحقًا)

TOP = {"c3": "صادقت (إغلاقٌ فوق المرساة)", "c4": "خضراء 3-4",
       "v2": "المرساة دون 30% (سيولة تتوالى)",
       "v3": "سيولةٌ داخلة (نبضٌ صافٍ موجب)"}


# ── أذرعُ الوقف §③ (نقيّة) ──────────────────────────────────────────────────
def stop_levels(rows, a_ms):
    """`S0`-`S3` بتعريفات §③ حرفيًّا. `None` لما لا شموعَ له."""
    ab = next((b for b in rows if b[0] == a_ms), None)
    if ab is None:
        return None
    s0 = ab[3]
    w5 = [b for b in rows if a_ms <= b[0] < a_ms + KS.ENTRY5_MIN * MIN2]
    s1 = min(b[3] for b in w5) if w5 else s0
    prev = [b for b in rows if b[0] < a_ms]
    s2 = prev[-1][3] if prev else None
    w15 = [b for b in rows if a_ms - PRE_WIN_MIN * MIN2 <= b[0] < a_ms]
    s3 = min(b[3] for b in w15) if w15 else None
    return {"S0": s0, "S1": s1, "S2": s2, "S3": s3}


def entry5(rows, a_ms, entry):
    """سعرُ الدخول المقيس = آخرُ إغلاقٍ قبل الدقيقة الخامسة (‏`resolve` حرفيًّا)
    ⇒ **هو سعرُ كرت M5**. و`None` لمن لا شمعةَ له بعد النافذة."""
    win = [b for b in rows if a_ms < b[0] < a_ms + KS.ENTRY5_MIN * MIN2]
    after = [b for b in rows if b[0] >= a_ms + KS.ENTRY5_MIN * MIN2]
    if not after:
        return None, None
    return (win[-1][4] if win else entry), after


def walk(after, e5, lv):
    """مسارُ ما بعد الكرت: أوّلُ لمسٍ لـ+30% · أوّلُ كسرٍ لكلّ مستوًى (إغلاقًا)
    · وأقصى تراجعٍ قبل اللمس. **الكسرُ بإغلاق دقيقةٍ دون المستوى لا بلمسةِ
    ذيل** (تعريفُ `resolve` نفسُه)."""
    # 🔒 **صيغةُ `resolve` حرفيًّا لا مكافئُها الجبريّ** — أسقط `V0-ب` سنةَ
    #    2023 بتفرّقٍ **واحد** من 10,819 صفًّا، والسببُ أن `h >= e5*(1+30/100)`
    #    و`(h/e5-1)*100 >= 30` **متساويان جبريًّا ومختلفان عائمًا**: مقيسٌ على
    #    أسعارِ أربعِ خاناتٍ ‏0.4-10.0$ ⇒ **تفرّقٌ في 0.244% من الأزواج الحدّية
    #    وفي الاتجاهين** (‏e5=0.4040/h=0.5252 ⟶ الأداةُ نعم وresolve لا ·
    #    e5=0.5050/h=0.6565 ⟶ العكس). ⇒ **مقياسٌ واحدٌ لا اثنان** (`ES9`).
    hit_ms = None
    low_to_hit = e5
    last_c = e5
    brk = {k: None for k in ARMS}
    for t, _o, h, lo, c, _v in after:
        if hit_ms is None:
            low_to_hit = min(low_to_hit, lo)      # ⚠️ يشمل شمعةَ اللمس (أعمق)
            if (h / e5 - 1.0) * 100.0 >= KS.KASIH_PCT:
                hit_ms = t
        last_c = c
        for k in ARMS:
            L = lv.get(k)
            if L is not None and brk[k] is None and c < L:
                brk[k] = t
    return hit_ms, low_to_hit, last_c, brk


def repro_resolve(rows, a_ms, entry, s0):
    """`V0` — إعادةُ إنتاج `resolve` بت-بت بذراع `S0` وسعرِ المِرساة."""
    mx = entry
    ex = "eod"
    for t, _o, h, _l, c, _v in rows:
        if t <= a_ms:
            continue
        mx = max(mx, h)
        if c < s0:
            ex = "break"
            break
    return ex, (mx / entry - 1.0) * 100.0 >= KS.KASIH_PCT


def tier_of(row):
    """🥇🥈🥉 §④ — تسميةُ سلالٍ منشورة (‏`J1` × عدّادِ المواصلة)."""
    got = [f for f in ("c3", "c4", "v2", "v3") if row.get(f)]
    if not got:
        return None, None
    green = sum(1 for f in got if row.get(f) == TOP[f])
    j1 = str(row.get("j1") or "").startswith("توليفة")
    if j1 and green >= 3:
        return "قوي", green
    if (not j1) and green <= 1:
        return "ضعيف", green
    return "متوسط", green


def med(xs):
    if not xs:
        return None
    v = sorted(xs)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def pct(xs, p):
    if not xs:
        return None
    v = sorted(xs)
    i = min(len(v) - 1, max(0, int(round((p / 100.0) * (len(v) - 1)))))
    return v[i]


def main() -> int:
    year = (os.environ.get("STOP_YEAR") or "").strip()
    if not year:
        print("⛔ لا STOP_YEAR.")
        return 2
    days = KS.weekdays(f"{year}-01-01", f"{year}-12-31")
    seed = KS.weekdays(f"{int(year) - 1}-12-20", f"{int(year) - 1}-12-31")[-3:]
    KS.log(f"🛑 T-EXIT-STOP — سنة {year} · أيام {len(days)} · "
           f"كون [{KS.PRICE_LO}, {KS.PRICE_HI}]$ · هدفٌ {KS.KASIH_PCT}% · "
           f"أذرع {'/'.join(ARMS)}")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_anchored = n_gapcap = n_no5 = 0
    v0_bad = v0_bad5 = 0
    n_k5 = k_k5 = 0            # 🔗 فحصُ تكاملٍ مع الرفيق المنشور في kasih_result
    out_path = f"exit_stop_rows_{year}.jsonl"
    fout = open(out_path, "w", encoding="utf-8")

    for di, day in enumerate(seed + days):
        seeding = di < len(seed)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
            continue
        dest = f"/tmp/exitstop-{day}.csv.gz"
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
            n_missing += 0 if seeding else 1
            try:
                os.remove(dest)
            except OSError:
                pass
            continue
        try:
            os.remove(dest)
        except OSError:
            pass
        if seeding:
            prev_close.update(closes)
            continue
        n_files += 1
        for sym, b in bars.items():
            if not KS.prescreen(b):
                continue
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
            lv = stop_levels(b, a_ms)
            if lv is None:
                continue

            # 🔒 V0 — إعادةُ إنتاج الحسم المنشور بت-بت
            ex0, k30_0 = repro_resolve(b, a_ms, entry, lv["S0"])
            if ex0 != res["exit"] or bool(k30_0) != bool(res["kasih30"]):
                v0_bad += 1

            e5, after = entry5(b, a_ms, entry)
            if e5 is None or e5 <= 0:
                n_no5 += 1
                continue
            hit_ms, low_hit, last_c, brk = walk(after, e5, lv)

            # 🔒 V0-ب — الرفيقُ `kasih30_from5` يُعاد بذراع S0
            if "kasih30_from5" in res:
                n_k5 += 1
                k_k5 += 1 if res["kasih30_from5"] else 0
                s0b = brk.get("S0")
                mine5 = (hit_ms is not None
                         and (s0b is None or hit_ms <= s0b))
                if bool(mine5) != bool(res["kasih30_from5"]):
                    v0_bad5 += 1

            usd5 = KS.f2_usd5(b, a_ms)
            usd1 = float(e.get("usd") or 0)
            f2key = S._ignition_candle_class(usd5)[0]
            row = {"sym": sym, "day": day, "anchor_ms": a_ms,
                   "entry": entry, "e5": round(e5, 4),
                   "gap_pct": round(gap, 1) if gap is not None else None,
                   "f2": f2key,
                   "j1": K2.j1_bucket(f2key, gap),
                   "c3": K2.c3_bucket(b, a_ms, entry),
                   "c4": K2.c4_bucket(b, a_ms),
                   "v2": K2.v2_bucket(usd1, usd5),
                   "v3": K2.v3_bucket(b, a_ms),
                   "sweeper": hit_ms is not None,
                   "mae_pct": (round((low_hit / e5 - 1.0) * 100.0, 2)
                               if hit_ms is not None else None),
                   "eod_pct": round((last_c / e5 - 1.0) * 100.0, 2)}
            tk, green = tier_of(row)
            row["tier"] = tk
            row["green"] = green
            for k in ARMS:
                L = lv.get(k)
                if L is None:
                    row[k] = None
                    continue
                dist = (e5 - L) / e5 * 100.0
                pre = any(c < L for (_t, _o, _h, _l, c, _v) in b
                          if a_ms <= _t < a_ms + KS.ENTRY5_MIN * MIN2)
                bm = brk[k]
                if dist <= 0:
                    row[k] = {"lv": round(L, 4), "dist": round(dist, 2),
                              "below": True, "pre": pre}
                    continue
                surv = (hit_ms is not None
                        and (bm is None or bm >= hit_ms))
                if surv:
                    outc = KS.KASIH_PCT
                elif bm is not None:
                    outc = -dist
                else:
                    outc = row["eod_pct"]
                row[k] = {"lv": round(L, 4), "dist": round(dist, 2),
                          "below": False, "pre": pre, "surv": surv,
                          "R": round(outc / dist, 3)}
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_out.append(row)
        prev_close.update(closes)
        if n_files % 20 == 0:
            KS.log(f"   📦 {n_files}/{len(days)} يومًا · مراسٍ {n_anchored:,}")
    fout.close()

    print("\n" + "=" * 74)
    print(f"🛑 T-EXIT-STOP — سنة {year} · العقد exit_stop_prereg.md "
          "(مدفوعٌ قبل أيّ رقم)")
    print("=" * 74)
    print(f"📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · **مراسٍ "
          f"{n_anchored:,}** · بلا شمعةٍ بعد الخمس {n_no5} · "
          f"تشويهُ تقسيم {n_gapcap} · صفوفٌ مقيسة {len(rows_out):,}")

    # ── بوّاباتُ الصلاحية §⑥ ────────────────────────────────────────────────
    print("\n🔒 بوّاباتُ الصلاحية (سقوطُ أيٍّ منها ⇒ لا حكم)")
    print(f"   V0  إعادةُ إنتاج `resolve` بذراع S0: تفرّقٌ {v0_bad} "
          f"{'✅' if v0_bad == 0 else '⛔'}")
    print(f"   V0-ب الرفيقُ kasih30_from5: تفرّقٌ {v0_bad5} "
          f"{'✅' if v0_bad5 == 0 else '⛔'}")
    diff = {k: sum(1 for r in rows_out
                   if r.get(k) and r.get("S0")
                   and abs(r[k]["lv"] - r["S0"]["lv"]) > 1e-9)
            for k in ("S1", "S2", "S3")}
    v1_ok = all(v > 0 for v in diff.values())
    print("   V1  تفرّقُ المستويات عن S0: "
          + " · ".join(f"{k}={v:,}" for k, v in diff.items())
          + (" ✅" if v1_ok else " ⛔ (no-op)"))
    mono1 = sum(1 for r in rows_out if r.get("S1") and r.get("S0")
                and r["S1"]["lv"] > r["S0"]["lv"] + 1e-9)
    mono3 = sum(1 for r in rows_out if r.get("S3") and r.get("S2")
                and r["S3"]["lv"] > r["S2"]["lv"] + 1e-9)
    v2_ok = (mono1 == 0 and mono3 == 0)
    print(f"   V2  الرتابةُ البنيوية S1≤S0 و S3≤S2: خرقٌ {mono1}/{mono3} "
          f"{'✅' if v2_ok else '⛔'}")
    tiers = {}
    for r in rows_out:
        if r.get("tier"):
            tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    v3_ok = (len(tiers) == 3 and all(v >= FLOOR_TIER_YEAR
                                     for v in tiers.values()))
    print("   V3  الفئاتُ الثلاث: "
          + " · ".join(f"{k}={v:,}" for k, v in sorted(tiers.items()))
          + (" ✅" if v3_ok else f" ⛔ (الأرضية {FLOOR_TIER_YEAR}/فئة)"))
    # 🔴🔴 **`V4` تغطيةُ الأيام — أُضيف 2026-08-20 بعد عطبٍ مقيسٍ لا مفترَض:**
    #   تشغيلةُ 2024 (`32398766093`) قِيست **‏194 يومًا ومفقودٌ 68 (‏26%)** لأن
    #   ‏S3 ردّ **‏503 Service Unavailable** حين شُغّلت السنواتُ الثلاث معًا على
    #   البكت نفسِه — والأداةُ **طبعت التغطيةَ ومضت** فأنتجت أرقامًا على عيّنةٍ
    #   أصغرَ بـ30% ومنحازةٍ زمنيًّا (الضياعُ وقع في ذيل السنة) ⇒ **سنواتٌ
    #   تُقارَن وكلٌّ منها على مجتمعٍ آخر**. وهو صنفُ «حارسِ التغطية» المدوَّن
    #   (‏`press_radar` كان الوحيدَ بلا أرضيةِ تغطيةٍ فكان خنقُ المزوّد يمرّ
    #   صامتًا). ⚖️ **والأرضيةُ ‏5% رقمٌ مستدير**، والتشغيلاتُ الثلاثُ ذاتُ
    #   الجودة قِيست عند **‏3.8-4.2%** مفقودًا.
    cov_bad = coverage_bad(n_files, n_missing)
    print(f"   V4  تغطيةُ الأيام: مفقودٌ {n_missing}/{n_files + n_missing} "
          f"({n_missing / max(1, n_files + n_missing) * 100:.1f}%) "
          + ("✅" if not cov_bad else
             f"⛔ (الحدّ {COVERAGE_MAX_MISS * 100:.0f}%)"))
    if v0_bad or v0_bad5 or not v1_ok or not v2_ok or cov_bad:
        print("\n⛔ بوّابةُ صلاحيةٍ ساقطة ⇒ **عطبُ أداةٍ لا نتيجة** — لا حكم.")
        return 3

    sweep = [r for r in rows_out if r["sweeper"]]
    n, k = len(rows_out), len(sweep)
    lo, hi = KS.wilson(k, n) if n else (0, 0)
    print(f"\n📊 الأساس: كاسح30 (بلا وقف، من سعر كرت M5) = {k:,}/{n:,} "
          f"({k / max(1, n) * 100:.1f}% [{lo:.0f}·{hi:.0f}])")
    if n_k5:
        # 🔴 **تصحيحٌ ذاتيّ 2026-08-20:** كان هنا «يجب أن يطابق
        #    `kasih_result` بت-بت» — **دعوًى لا سندَ لها**: لم يُنشَر قطُّ
        #    معدَّلٌ سنويٌّ مجمَّعٌ لهذا الرفيق (المنشورُ ‏9.7/11.7/11.2 هو
        #    الأساسُ **من إغلاق المِرساة** لا من `e5`) ⇒ لا شيءَ يُقارَن به.
        #    **وحارسُ التكامل الحقيقيُّ `V0`/`V0-ب` صفًّا بصفّ** أعلاه.
        print(f"🔗 وصفيّ — الرفيقُ `kasih30_from5` (‏من e5 **بوقف S0**) = "
              f"{k_k5:,}/{n_k5:,} ({k_k5 / n_k5 * 100:.1f}%) · "
              f"⚠️ لا يُقارَن بأساس `kasih_result` (مِرساةٌ مختلفة) — "
              f"والتكاملُ يحرسه `V0`/`V0-ب` صفًّا بصفّ.")

    # ── الحاكمُ الوصفيّ: MAE §⑤ ─────────────────────────────────────────────
    mae = [-r["mae_pct"] for r in sweep if r.get("mae_pct") is not None]
    print("\n🩸 **MAE — أقصى تراجعٍ قبل بلوغ +30% (للكاسحين)** — الحاكمُ "
          "الوصفيّ: لا ذراعَ تفوز به، ويجيب «كم عمقًا يلزم الوقف»")
    if mae:
        print(f"   ن={len(mae):,} · الوسيط {med(mae):.1f}% · "
              f"ربعٌ أعلى (p75) {pct(mae, 75):.1f}% · p90 {pct(mae, 90):.1f}% "
              f"· p95 {pct(mae, 95):.1f}% · الأقصى {max(mae):.1f}%")
        for d in (3, 5, 7, 10, 13, 20, 30):
            c = sum(1 for x in mae if x <= d)
            print(f"      وقفٌ بعمق {d:>2}% يُبقي {c / len(mae) * 100:5.1f}% "
                  f"من الكاسحين")

    # ── الأذرعُ §⑤ ─────────────────────────────────────────────────────────
    print("\n🛑 **الأذرع** (‏`survive30` من الكاسحين · `risk` وسيطُ المسافة · "
          "`R` بحجمِ مركزٍ مُصغَّرٍ كلّما عمُق الوقف)")
    print(f"   {'ذراع':<5}{'ن':>8}{'مسافة%':>9}{'كاسح ناجٍ':>11}"
          f"{'survive30':>11}{'R':>8}{'تحت المستوى':>13}{'كُسر قبل الكرت':>15}")
    arm_stats = {}
    for a in ARMS:
        vals = [r[a] for r in rows_out if r.get(a)]
        below = sum(1 for v in vals if v.get("below"))
        ok = [v for v in vals if not v.get("below")]
        pre = sum(1 for v in ok if v.get("pre"))
        sw = [(r, r[a]) for r in sweep
              if r.get(a) and not r[a].get("below")]
        surv = sum(1 for _r, v in sw if v.get("surv"))
        s30 = surv / len(sw) * 100.0 if sw else None
        risk = med([v["dist"] for v in ok])
        rr = sum(v["R"] for v in ok) / len(ok) if ok else None
        arm_stats[a] = {"n": len(ok), "s30": s30, "risk": risk, "R": rr,
                        "sw": len(sw), "surv": surv}
        print(f"   {a:<5}{len(ok):>8,}{(risk if risk is not None else 0):>9.2f}"
              f"{surv:>7,}/{len(sw):<4,}"
              f"{(f'{s30:.1f}%' if s30 is not None else '—'):>11}"
              f"{(f'{rr:+.3f}' if rr is not None else '—'):>8}"
              f"{below:>13,}{pre:>15,}")
    b0 = arm_stats["S0"]
    print("\n   Δ عن S0 (المعيارُ §⑥: +5 نقاطٍ فأكثر في كلّ سنة · "
          "و R لا يسوء بأكثر من 0.02 مجمَّعًا · بلا انقلاب)")
    for a in ("S1", "S2", "S3"):
        s = arm_stats[a]
        d30 = (s["s30"] - b0["s30"]) if (s["s30"] is not None
                                         and b0["s30"] is not None) else None
        dr = (s["R"] - b0["R"]) if (s["R"] is not None
                                    and b0["R"] is not None) else None
        print(f"   {a}: Δsurvive30 = "
              f"{(f'{d30:+.1f}ن' if d30 is not None else '—'):>8} · ΔR = "
              f"{(f'{dr:+.3f}' if dr is not None else '—'):>8} · "
              + ("✅ تعبر ①" if (d30 is not None and d30 >= 5.0)
                 else "🔴 تسقط ①"))
    # 📌 مقارنةٌ **مقترنةٌ داخل الصفّ** — وصفيّةٌ خارج المعيار المسجَّل، تُضاف
    #    حرسًا من عيب «مجموعتين مختلفتين» المقيس في `T-GATE`: كلُّ ذراعٍ تُقارَن
    #    بـ`S0` على **المراسي التي تصلح للاثنتين معًا** لا على مجموعتين.
    print("\n   📌 المقترنُ داخل الصفّ (وصفيٌّ خارج المعيار — حارسُ المقامَين)")
    for a in ("S1", "S2", "S3"):
        pair = [r for r in rows_out
                if r.get(a) and r.get("S0")
                and not r[a].get("below") and not r["S0"].get("below")]
        psw = [r for r in pair if r["sweeper"]]
        if not psw:
            continue
        sa = sum(1 for r in psw if r[a].get("surv")) / len(psw) * 100.0
        s0p = sum(1 for r in psw if r["S0"].get("surv")) / len(psw) * 100.0
        ra = sum(r[a]["R"] for r in pair) / len(pair)
        r0 = sum(r["S0"]["R"] for r in pair) / len(pair)
        print(f"   {a}: ن={len(pair):,} · كاسح={len(psw):,} · "
              f"Δsurvive30 = {sa - s0p:+.1f}ن · ΔR = {ra - r0:+.3f}")

    # ── الفئاتُ §④ ─────────────────────────────────────────────────────────
    print("\n🥇🥈🥉 **الفئاتُ الثلاث** (تسميةُ سلالٍ منشورة — "
          "🔴 دائريّةٌ مُعلَنة: وصفُ عيّنةٍ لا تنبّؤ)")
    print(f"   {'الفئة':<8}{'ن':>8}{'كاسح':>8}{'نسبة':>9}{'ويلسون':>14}"
          f"{'survive30(S0)':>15}{'recall':>9}")
    order = ["قوي", "متوسط", "ضعيف"]
    tier_stats = {}
    for t in order:
        rs = [r for r in rows_out if r.get("tier") == t]
        sw = [r for r in rs if r["sweeper"]]
        if not rs:
            continue
        p = len(sw) / len(rs) * 100.0
        wl, wh = KS.wilson(len(sw), len(rs))
        swa = [r for r in sw if r.get("S0") and not r["S0"].get("below")]
        srv = sum(1 for r in swa if r["S0"].get("surv"))
        s30 = srv / len(swa) * 100.0 if swa else None
        rec = len(sw) / max(1, k) * 100.0
        tier_stats[t] = {"n": len(rs), "sw": len(sw), "pct": p,
                         "s30": s30, "recall": rec}
        print(f"   {t:<8}{len(rs):>8,}{len(sw):>8,}{p:>8.1f}%"
              f"{f'[{wl:.0f}·{wh:.0f}]':>14}"
              f"{(f'{s30:.1f}%' if s30 is not None else '—'):>15}"
              f"{rec:>8.1f}%")
    if "قوي" in tier_stats and "ضعيف" in tier_stats:
        a_, b_ = tier_stats["قوي"], tier_stats["ضعيف"]
        al, ah = KS.wilson(a_["sw"], a_["n"])
        bl, bh = KS.wilson(b_["sw"], b_["n"])
        print(f"   🔒 فاصلا (قوي × ضعيف) "
              f"{'منفصلان ✅' if al > bh else 'متداخلان 🔴'}")
    floors = [t for t in order
              if tier_stats.get(t, {}).get("n", 0) < FLOOR_TIER_YEAR]
    if floors:
        print(f"\n⛔ أرضيةُ {FLOOR_TIER_YEAR}/فئة لم تُبلَغ: "
              f"{'، '.join(floors)} ⇒ **لا حكم** للفئات.")

    print("\n⚠️ حدودُ الصدق (§⑨): دائريّةُ التصنيف · «كاسح» لمسٌ لا تنفيذ · "
          "سعرُ القياس `e5` قد يخالف سعرَ الكرت الحيّ · «كُسر قبل الكرت» "
          "خانةٌ مستقلّةٌ لا خسارة · الأفقُ يومُ المِرساة وحده · مِرساةٌ واحدةٌ "
          "لكلّ رمزٍ يوميًّا · والافترُ داخلٌ فالقياسُ متفائل. "
          "**والتعادلُ في الدقيقة نفسِها (كسرٌ ولمسٌ معًا) يُحسَب نجاةً** — "
          "قراءةٌ متفائلةٌ مطابقةٌ لترتيب `resolve` وتُعلَن ولا تُخفى.")
    if floors or not v3_ok:
        return 5
    return 0


if __name__ == "__main__":
    sys.exit(main())
