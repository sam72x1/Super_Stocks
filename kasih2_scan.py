#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌊② **T-KASIH-2** — «أقوى توليفة دخولٍ للأسهم القوية التي ستُواصل».

عقدُها `kasih2_prereg.md` **مدفوعٌ قبل أيّ رقم**. أمرُ المالك بنصّه: «ممكن يكون
السبب نمط معين في الشموع او الفوليوم او اي شي ثاني بس الاكيد ان فيه شي يخلينا
نتاكد ان السهم قوي جدا و بيواصل».

🔒 **مقياسٌ واحدٌ لا اثنان:** أدواتُ القياس كلُّها تُستورَد من `kasih_scan`
**بالاسم** (‏`parse_day`/`prescreen`/`first_anchor`/`resolve`/`f2_usd5`/السلال/
`bucket_table`) — الجديدُ هنا **خصائصُ العقد §② وحدَها**. قراءة/قياسٌ فقط:
لا كرون · لا كتابةَ حالة · لا تلغرام · والإنتاجُ لا يستورد هذا الملف.
"""
import gzip
import json
import os
import sys

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import datetime as dt                                             # noqa: E402

import ah_scan as AH                                              # noqa: E402
import kasih_scan as KS                                           # noqa: E402
import Super_stock as S                                           # noqa: E402

MIN2 = 60_000


# ── خصائصُ العقد §② (نقيّةٌ كلُّها — تعريفاتُها حرفيًّا من التسجيل) ──────────
def j1_bucket(f2key, gap):
    """🥇 الحاكمة: (صنفُ الخمس قوي/مضارب) و(فجوةٌ من إغلاق الأمس 30% فأكثر)."""
    if gap is None:
        return None
    return ("توليفة (قوي/مضارب × فجوة 30%+)"
            if f2key in ("strong", "operator") and float(gap) >= 30.0
            else "الباقي")


def c1_bucket(ab):
    """C1 — موضعُ إغلاق شمعة المِرساة (البوّابةُ تضمن 0.5 فأعلى)."""
    _t, _o, h, lo, c, _v = ab
    rng = h - lo
    cpos = 1.0 if rng <= 0 else (c - lo) / rng
    if cpos < 0.75:
        return "إغلاق 0.50-0.75"
    if cpos < 0.90:
        return "إغلاق 0.75-0.90"
    return "إغلاق 0.90-1.00"


def c2_bucket(ab):
    """C2 — الفتيلُ العلويّ لشمعة المِرساة (سقفُه 50% بحكم موضع الإغلاق)."""
    _t, _o, h, lo, c, _v = ab
    rng = h - lo
    uw = 0.0 if rng <= 0 else (h - c) / rng
    if uw < 0.10:
        return "مارِبو (فتيل دون 10%)"
    if uw < 0.30:
        return "فتيل 10-30%"
    return "فتيل 30-50%"


def c3_bucket(rows, a_ms, entry):
    """C3 — شمعةُ التصديق: أوّلُ دقيقةٍ مغلقةٍ خلال 3 دقائق من المِرساة."""
    nxt = next((b for b in rows if a_ms < b[0] <= a_ms + 3 * MIN2), None)
    if nxt is None:
        return None                    # لا شمعةَ قريبة ⇒ تُستبعَد (العقد §②)
    c = nxt[4]
    if c > entry:
        return "صادقت (إغلاقٌ فوق المرساة)"
    if c < entry:
        return "نقضت"
    return "حيّدت"


def _win5(rows, a_ms):
    return [b for b in rows
            if a_ms < b[0] < a_ms + KS.ENTRY5_MIN * MIN2]


def c4_bucket(rows, a_ms):
    """C4 — عدُّ الشموع الخضراء في دقائق ما بعد المِرساة داخل نافذة الخمس."""
    w = _win5(rows, a_ms)
    if not w:
        return None
    g = sum(1 for b in w if b[4] > b[1])
    if g <= 1:
        return "خضراء 0-1"
    return "خضراء 2" if g == 2 else "خضراء 3-4"


def v1_bucket(rows, a_ms):
    """V1 — اتجاهُ السيولة داخل الخمس: (الدقيقتان 3-4) مقابل (1-2)."""
    w = _win5(rows, a_ms)
    h1 = sum(b[4] * b[5] for b in w if b[0] < a_ms + 3 * MIN2)
    h2 = sum(b[4] * b[5] for b in w if b[0] >= a_ms + 3 * MIN2)
    if h1 <= 0 or h2 <= 0:
        return None                    # نصفٌ فارغ ⇒ تُستبعَد (العقد §②)
    return ("سيولةٌ متصاعدة (النصفُ الثاني أكبر)" if h2 >= h1
            else "سيولةٌ خابية")


def v2_bucket(usd1, usd5):
    """V2 — تركُّزُ المِرساة: نصيبُ دقيقتها من دولارات الخمس."""
    try:
        u1, u5 = float(usd1), float(usd5)
    except (TypeError, ValueError):
        return None
    if u5 <= 0:
        return None
    share = u1 / u5
    if share > 0.60:
        return "المرساة فوق 60% من الخمس (اندفاعة وحيدة)"
    if share >= 0.30:
        return "المرساة 30-60% من الخمس"
    return "المرساة دون 30% (سيولة تتوالى)"


def v3_bucket(rows, a_ms):
    """💓 V3 — صافي نبضات السيولة (‏±10%) على أزواج الدقائق **المتتالية فعلًا**
    داخل نافذة الخمس — اختبارُ فرضية «نبض السيولة» تاريخيًّا (العقد K2-P2)."""
    seg = [b for b in rows
           if a_ms <= b[0] < a_ms + KS.ENTRY5_MIN * MIN2]
    pos = neg = pairs = 0
    for a, b in zip(seg, seg[1:]):
        if b[0] - a[0] != MIN2:        # فجوةُ دقائق ⇒ ليس زوجًا متتاليًا
            continue
        ua, ub = a[4] * a[5], b[4] * b[5]
        if ua <= 0:
            continue
        pairs += 1
        if ub >= 1.10 * ua:
            pos += 1
        elif ub <= 0.90 * ua:
            neg += 1
    if pairs == 0:
        return None
    net = pos - neg
    if net > 0:
        return "سيولةٌ داخلة (نبضٌ صافٍ موجب)"
    if net < 0:
        return "سيولةٌ نازحة (نبضٌ صافٍ سالب)"
    return "نبضٌ متعادل"


def p1_bucket(rows, a_ms, entry):
    """P1 — موضعُ الفيواب: إغلاقُ المِرساة مقابل Σc·v/Σv من بداية الجلسة
    الممتدّة حتى لحظتها (مقياسُ الدولار الإنتاجيّ — لا السعرُ النموذجيّ)."""
    pv = vv = 0.0
    for b in rows:
        if b[0] > a_ms:
            break
        pv += b[4] * b[5]
        vv += b[5]
    if vv <= 0:
        return None
    return "فوق الفيواب" if float(entry) >= pv / vv else "دون الفيواب"


def p2_bucket(rows, a_ms, entry):
    """P2 — طزاجةُ القمّة: المِرساةُ على قمّة يومها أم تحت قمّةٍ سابقة."""
    prior = [b[2] for b in rows if b[0] < a_ms]
    if not prior:
        return "على قمة يومه"
    return ("على قمة يومه" if float(entry) >= 0.995 * max(prior)
            else "تحت قمة سابقة")


def k2_features(rows, a_ms, entry, f2key, gap, usd1, usd5):
    """يجمع خصائصَ العقد §② لصفٍّ واحد — نقيّةٌ وقابلةٌ للاختبار."""
    ab = next((b for b in rows if b[0] == a_ms), None)
    if ab is None:
        return {}
    f5 = KS.f5_bucket(gap) if gap is not None else None
    return {
        "j1": j1_bucket(f2key, gap),
        "j1_cell": (f"{f2key} × {f5}" if f5 else None),
        "c1": c1_bucket(ab), "c2": c2_bucket(ab),
        "c3": c3_bucket(rows, a_ms, entry),
        "c4": c4_bucket(rows, a_ms),
        "v1": v1_bucket(rows, a_ms),
        "v2": v2_bucket(usd1, usd5),
        "v3": v3_bucket(rows, a_ms),
        "p1": p1_bucket(rows, a_ms, entry),
        "p2": p2_bucket(rows, a_ms, entry),
    }


def entry_view(rows, a_ms, entry, prev_c):
    """💵 **«لو دخلت، على كم؟»** — عرضُ وضع اليوم (أمرُ المالك 2026-08-20:
    «طبّقها على رداك وخواتها وعلّمني كنت بدخل على نسبة كم»).

    يُرجع نقطتَي الدخول الواقعيّتين ونسبةَ كلٍّ عن **إغلاق الأمس**:
    ① `M1` = إغلاقُ شمعة المِرساة (أوّلُ إشعار) ② `M5` = **إغلاقُ الدقيقة
    الخامسة** — وهو **سعرُ كرت M5 حرفيًّا** (الكرتُ يفير حين `span ≥ 5`
    فيكون أحدثُ مغلقةٍ هي `anchor+4د`، وهي نفسُها آخرُ شمعةٍ داخل نافذة
    الخمس) ⇒ الوسمُ الموسَّع يُقرأ عند هذا السعر بالضبط.

    ⚖️ **ومقياسٌ واحدٌ لا اثنان:** الحسمُ يبقى `kasih_scan.resolve`؛ وهذي
    أرقامُ **عرض** تُقارَن ببوليانِه (`kasih30_from5`) في نداءِ المُنادي —
    وأيُّ تفرّقٍ يُطبَع ويُعَدّ (لا يُبتلَع)."""
    ab = next((b for b in rows if b[0] == a_ms), None)
    if ab is None or entry <= 0:
        return None
    anchor_low = ab[3]
    e5 = entry
    e5_frozen = False
    mx5 = None
    mx = entry
    for b in rows:
        t, _o, h, _l, c, _v = b
        if t <= a_ms:
            continue
        if not e5_frozen and t < a_ms + KS.ENTRY5_MIN * MIN2:
            e5 = c
        elif not e5_frozen:
            e5_frozen = True
            mx5 = e5
        mx = max(mx, h)
        if mx5 is not None:
            mx5 = max(mx5, h)
        if c < anchor_low:
            break
    out = {"e1": entry, "e5": e5,
           "mg1": (mx / entry - 1.0) * 100.0,
           "mg5": ((mx5 / e5 - 1.0) * 100.0
                   if (mx5 is not None and e5 > 0) else None)}
    if prev_c:
        out["gap1"] = (entry / float(prev_c) - 1.0) * 100.0
        out["gap5"] = (e5 / float(prev_c) - 1.0) * 100.0
    return out


def main() -> int:                                                # noqa: C901
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    year = (os.environ.get("KASIH_YEAR") or "").strip()
    one_day = (os.environ.get("KASIH_DAY") or "").strip()
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
        print("⛔ لا KASIH_YEAR ولا KASIH_DAY.")
        return 2
    KS.log(f"🌊② T-KASIH-2 — {'يوم ' + one_day if one_day else 'سنة ' + year}"
           f" · أيام {len(days)} · كون [{KS.PRICE_LO}, {KS.PRICE_HI}]$ · "
           f"بوابات الإنتاج: رفعة {S.LIQ_MIN_MOVE_PCT}% · "
           f"أرضية ${S.LIQ_MIN_USD:,} × {S.LIQ_CUM_MINUTES}د · "
           f"قفزة {S.CONFIG['IGNITION_VOL_MULT']}×")

    prev_close: dict = {}
    rows_out: list = []
    n_files = n_missing = n_syms = n_screened = n_anchored = 0
    n_gapcap = n_evmis = 0
    out_path = f"kasih2_rows_{year or one_day}.jsonl"
    fout = open(out_path, "w", encoding="utf-8")

    for di, day in enumerate(seed_days + days):
        seeding = di < len(seed_days)
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            if not seeding:
                n_missing += 1
            continue
        dest = f"/tmp/kasih2-{day}.csv.gz"
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
            usd5 = KS.f2_usd5(b, a_ms)
            usd1 = float(e.get("usd") or 0)
            f2key = S._ignition_candle_class(usd5)[0]
            row = {"sym": sym, "day": day, "anchor_ms": a_ms,
                   "entry": entry, "usd1": usd1, "usd5": round(usd5),
                   "gap_pct": round(gap, 1) if gap is not None else None,
                   "f2": f2key, "f3": KS.f3_bucket(a_ms),
                   "f5": (KS.f5_bucket(gap) if gap is not None else None)}
            row.update(res)
            row.update(k2_features(b, a_ms, entry, f2key, gap, usd1, usd5))
            if one_day:
                ev = entry_view(b, a_ms, entry, pc)
                if ev:
                    row["_ev"] = ev
                    # 🔒 تفرّقُ العرض عن الحسم يُطبَع ويُعَدّ — لا يُبتلَع
                    if (ev["mg5"] is not None
                            and "kasih30_from5" in res
                            and (ev["mg5"] >= KS.KASIH_PCT)
                            != bool(res["kasih30_from5"])):
                        n_evmis += 1
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            rows_out.append(row)
        prev_close.update(closes)
        if n_files % 20 == 0:
            KS.log(f"   📦 {n_files}/{len(days)} يومًا · مرشَّح "
                   f"{n_screened:,} · مراسٍ {n_anchored:,}")
    fout.close()

    print("\n" + "=" * 74)
    print(f"🌊② T-KASIH-2 — {'يوم ' + one_day if one_day else 'سنة ' + year}"
          f" · العقد kasih2_prereg.md (مدفوع قبل أي رقم)")
    print("=" * 74)
    print(f"📥 أيامٌ قِيست {n_files} · مفقودة {n_missing} · رمز-يوم بالكون "
          f"{n_syms:,} · عبر المرشِّح {n_screened:,} · "
          f"**مراسٍ {n_anchored:,}** · استُبعد بتشويه تقسيم {n_gapcap}")
    print("🔗 فحصُ تكامل: عددُ المراسي والأساسُ وجدولا F2/F5 يجب أن تطابق "
          "kasih_result لهذي السنة **بت-بت** (نفسُ اللقطة والدوالّ) — "
          "تفرّقٌ = عطبُ أداةٍ لا نتيجة.")
    if rows_out:
        k = sum(1 for r in rows_out if r["kasih30"])
        lo, hi = KS.wilson(k, len(rows_out))
        print(f"\n📊 الأساس: كاسح30 = {k}/{len(rows_out)} "
              f"({k / len(rows_out) * 100:.1f}% [{lo:.0f}·{hi:.0f}])")
        KS.bucket_table(rows_out, "j1",
                        "🥇 J1 الحاكمة — «التوليفة» مقابل الباقي (العقد §②)")
        KS.bucket_table(rows_out, "j1_cell",
                        "J1 تفصيلًا — خلايا F2 × F5 (أرضية 40/خلية)")
        KS.bucket_table(rows_out, "c1", "C1 — موضعُ إغلاق شمعة المِرساة")
        KS.bucket_table(rows_out, "c2", "C2 — الفتيلُ العلويّ للمِرساة")
        KS.bucket_table(rows_out, "c3", "C3 — شمعةُ التصديق (خلال 3 دقائق)")
        KS.bucket_table(rows_out, "c4", "C4 — الخضراء داخل نافذة الخمس")
        KS.bucket_table(rows_out, "v1", "V1 — اتجاهُ السيولة داخل الخمس")
        KS.bucket_table(rows_out, "v2", "V2 — تركُّزُ المِرساة من الخمس")
        KS.bucket_table(rows_out, "v3",
                        "💓 V3 — صافي نبضات السيولة (فرضيةُ النبض تاريخيًّا)")
        KS.bucket_table(rows_out, "p1", "P1 — موضعُ الفيواب عند المِرساة")
        KS.bucket_table(rows_out, "p2", "P2 — طزاجةُ قمّة اليوم")
        KS.bucket_table(rows_out, "f2", "🔗 مرجع F2 (فحصُ التكامل مع kasih)")
        KS.bucket_table(rows_out, "f5", "🔗 مرجع F5 (فحصُ التكامل مع kasih)")
    if one_day and rows_out:
        # 💵 «لو دخلت، على كم؟» — سطرٌ لكلّ مِرساة، بلا قصّ (أمرُ المالك)
        print(f"\n💵 مراسي اليوم كلُّها ({len(rows_out)} — بلا قصّ) · "
              f"«لو دخلت، على كم؟»")
        print(f"   🔒 تفرّقُ العرض عن الحسم: {n_evmis} "
              f"{'✅' if n_evmis == 0 else '⛔ يُقرأ عطبَ أداةٍ لا نتيجة'}")
        print(f"   {'الرمز':7}{'مرساة':>7} {'سعرُ M1':>9}{'عن أمس':>9} "
              f"{'سعرُ M5':>9}{'عن أمس':>9} {'بعد M5':>8}  الوسمُ الذي كان سيصلك")
        # ⚠️ `mg5` قد يكون `None` (سهمٌ بلا شمعةٍ بعد الدقيقة الخامسة) —
        #    و`-None` يرمي: كُشف بالتشغيل لا بالقراءة.
        for r in sorted(rows_out,
                        key=lambda x: -(((x.get("_ev") or {}).get("mg5")
                                         if (x.get("_ev") or {}).get("mg5")
                                         is not None else -999.0))):
            e = r.get("_ev") or {}
            tag = ("🥇توليفة" if str(r.get("j1") or "").startswith("توليفة")
                   else "—")
            marks = []
            for fk, sym_ in (("c3", "تصديق"), ("c4", "خضراء"),
                             ("v2", "سيولة"), ("v3", "نبض")):
                v = r.get(fk)
                if not v:
                    continue
                good = (v.startswith("صادقت") or v == "خضراء 3-4"
                        or v.startswith("المرساة دون 30")
                        or v.startswith("سيولةٌ داخلة"))
                bad = (v == "نقضت" or v == "خضراء 0-1"
                       or v.startswith("المرساة فوق 60")
                       or v.startswith("سيولةٌ نازحة"))
                marks.append(("✅" if good else ("🔴" if bad else "◻️")) + sym_)
            ny_t = dt.datetime.fromtimestamp(
                r["anchor_ms"] / 1000, tz=KS.NY).strftime("%H:%M")
            g1 = e.get("gap1")
            g5 = e.get("gap5")
            mg5 = e.get("mg5")
            print(f"   ${r['sym']:6}{ny_t:>7} "
                  f"{e.get('e1', 0):>9.4g}{(f'{g1:+.0f}%' if g1 is not None else '—'):>9} "
                  f"{e.get('e5', 0):>9.4g}{(f'{g5:+.0f}%' if g5 is not None else '—'):>9} "
                  f"{(f'{mg5:+.1f}%' if mg5 is not None else '—'):>8}  "
                  f"{tag} {' '.join(marks)} [{r.get('f2')} · {r.get('exit')}]")
    print("\n⚠️ حدودُ الصدق (العقد §⑦): لمسٌ لا تنفيذ · يومُ المِرساة وحده · "
          "الرفيقُ من د5 هو الحاكم على دائرية نافذة الخمس · الحكمُ عبر "
          "السنوات الثلاث لا سنةً واحدة · والحاكمةُ J1 وحدَها والبقيةُ استكشاف.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
