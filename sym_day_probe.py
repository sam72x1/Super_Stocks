#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬📉 **مِجَسُّ سهمٍ في جلسة** — مسارُ الدقيقة كاملًا بلا قصّ.

بلاغُ المالك 2026-08-22: «‏`HUIZ` أنا متأكّد أنه وصل فوق 100% — هذي غلطة
كارثية». والسؤالُ المطلوب فصلُه بالقياس لا بالرأي:

**هل الرقمُ خطأٌ؟ أم صحيحٌ لمقياسٍ يقصّ عند الخروج البنيويّ فيُخفي ركضةً
وقعت بعده؟** — والفرقُ بين الاثنين هو الفرقُ بين عطبٍ وبين **حدِّ مقياسٍ
كان يجب أن يُعرَض من البداية**.

يطبع لكلّ (رمز، يوم): المِرساةَ ووقتَها · قاعَها · سعرَ كرت `M5` · **أقصى
ارتفاعٍ قبل الخروج البنيويّ** (وهو ما تقيسه أرقامُنا) · **ولحظةَ الخروج
وسعرَه** · **وأقصى ارتفاعٍ في اليوم كلِّه بلا أيّ قطع** (وهو ما يراه المالكُ
بعينه) · وقمّةَ اليوم وإغلاقَه · ومسارًا مختصرًا كلَّ خمس عشرة دقيقة.

⚖️ **مِجَسُّ تشخيصٍ سقفُ نجاحه صفر** — لا يُغيّر تعريفًا ولا عتبةً ولا رقمًا
منشورًا · قراءةٌ فقط · والإنتاجُ لا يستورده.
🔒 **ومقياسٌ واحدٌ:** المِرساةُ `kasih_scan.first_anchor` والحسمُ
`kasih_scan.resolve` **بالاسم** — صفرُ منطقٍ مكرّر؛ والجديدُ **قراءةُ ما بعد
الخروج** وهي غيرُ موجودةٍ في أيّ أداةٍ عندنا.

🔴 **ووضعٌ ثانٍ `PROBE_ALL=1`** أضيفَ بعد أن أثبت `HUIZ` أن الحدَّ ليس
حالةً مفردة: يُعيد قياسَ **كلّ مِرساةٍ في اليوم** بأنبوبة `kasih_scan` نفسِها
(الكونُ من إغلاق الأمس · `prescreen` · `first_anchor` · `GAP_CAP`) ويطبع
لكلّ صفٍّ **العمودَين معًا** — ما تقيسه أرقامُنا وما يراه المالكُ على الشارت
— ثم يعدّ **كم صفًّا وُسِم «خسرت» وقمّةُ يومه فوق 30% أو 50% أو 100%**.
⇒ **حجمُ الحدّ يصير رقمًا لا انطباعًا.**

**رموز الخروج:** 0 طُبع · 2 مدخلاتٌ ناقصة · 3 تعذّر الملفّ.
"""
import datetime as dt
import gzip
import os
import sys

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import ah_scan as AH                                             # noqa: E402
import kasih_scan as KS                                          # noqa: E402
import kasih2_scan as K2                                         # noqa: E402
import Super_stock as S                                          # noqa: E402
from tier_days_report import exit_price, outcome, true_e5        # noqa: E402

NY = KS.NY


def _hm(ms):
    return dt.datetime.fromtimestamp(ms / 1000, tz=NY).strftime("%H:%M")


def full_day_max(rows, a_ms, ref):
    """أقصى ارتفاعٍ **بلا قطعٍ عند الخروج** — ما يراه المالكُ على الشارت."""
    best, at = None, None
    for t, _o, h, _l, _c, _v in rows:
        if t <= a_ms or ref <= 0:
            continue
        pct = (h / ref - 1.0) * 100.0
        if best is None or pct > best:
            best, at = pct, t
    return best, at


def exit_point(rows, a_ms, alow):
    """أوّلُ إغلاقِ دقيقةٍ دون قاع المِرساة — الخروجُ البنيويّ."""
    for t, _o, _h, _l, c, _v in rows:
        if t <= a_ms:
            continue
        if c < alow:
            return float(c), int(t)
    return None, None


def probe(sym, day, bars, prev_c):
    b = bars.get(sym)
    print("\n" + "=" * 78)
    print(f"🔬 {sym} · {day}")
    print("=" * 78)
    if not b:
        print("⛔ لا شموعَ لهذا الرمز في ملفّ اليوم.")
        return
    print(f"📊 شموعُ الدقيقة: {len(b)} · من {_hm(b[0][0])} إلى {_hm(b[-1][0])}"
          " (بتوقيت نيويورك · تشمل البريماركت والأفتر)")
    d_hi = max(x[2] for x in b)
    d_lo = min(x[3] for x in b)
    print(f"📈 قمّةُ اليوم {d_hi:.4f} · قاعُه {d_lo:.4f} · "
          f"إغلاقُ الأمس {prev_c if prev_c else '—'}")
    if prev_c:
        print(f"   ↳ القمّةُ عن إغلاق الأمس: {(d_hi / prev_c - 1) * 100:+.1f}%")
    e = KS.first_anchor(b)
    if e is None:
        print("⛔ لم تُكشَف مِرساة.")
        return
    a_ms, entry = int(e["anchor_ms"]), float(e["price"])
    res = KS.resolve(b, a_ms, entry)
    ev = K2.entry_view(b, a_ms, entry, prev_c)
    alow = float(res["anchor_low"]) if res else None
    e5 = (ev or {}).get("e5")
    print(f"\n⚓ المِرساة {_hm(a_ms)} · سعرُها {entry:.4f} · قاعُها "
          f"{alow if alow is None else f'{alow:.4f}'}")
    if e5:
        print(f"💳 سعرُ كرت M5 {e5:.4f}")
    ex_px, ex_ms = exit_point(b, a_ms, alow) if alow else (None, None)
    if ex_ms:
        print(f"🛑 **الخروجُ البنيويّ {_hm(ex_ms)}** بسعر {ex_px:.4f} "
              f"({(ex_px / entry - 1) * 100:+.1f}% عن المِرساة)")
    else:
        print("🛑 لم يقع خروجٌ بنيويّ (‏eod)")
    print(f"\n📏 **ما تقيسه أرقامُنا** (أقصى ارتفاعٍ **قبل** الخروج): "
          f"من المِرساة {res.get('mg_after'):+.1f}%"
          + (f" · من كرت M5 {(ev or {}).get('mg5'):+.1f}%"
             if (ev or {}).get("mg5") is not None else " · من M5: تعذّر"))
    m1_all, at1 = full_day_max(b, a_ms, entry)
    m5_all, at5 = full_day_max(b, a_ms, e5) if e5 else (None, None)
    print(f"🔴 **وأقصى ارتفاعٍ في اليوم كلِّه بلا قطع**: من المِرساة "
          f"{m1_all:+.1f}% عند {_hm(at1)}"
          + (f" · من كرت M5 {m5_all:+.1f}% عند {_hm(at5)}"
             if m5_all is not None else ""))
    if ex_ms and at1 and at1 > ex_ms:
        print("   ⚠️ **والقمّةُ وقعت بعد الخروج البنيويّ** ⇒ أرقامُنا تقصّها "
              "بالتعريف — ليست خطأً بل **حدُّ مقياسٍ يجب أن يُعرَض**.")
    print("\n🕐 مسارُ الدقيقة (كلَّ 15 دقيقة بعد المِرساة · قمّةُ الشريحة):")
    seg, cur, hi = [], None, None
    for t, _o, h, _l, c, _v in b:
        if t <= a_ms:
            continue
        k = (t - a_ms) // (15 * 60_000)
        if cur is None or k != cur:
            if cur is not None:
                seg.append((cur, hi, last_c, last_t))
            cur, hi = k, h
        hi = max(hi, h)
        last_c, last_t = c, t
    if cur is not None:
        seg.append((cur, hi, last_c, last_t))
    for k, hi, cc, tt in seg[:28]:
        mark = " 🛑" if (ex_ms and tt >= ex_ms
                        and (k == 0 or True) and ex_ms <= tt) else ""
        print(f"   +{k * 15:>4}د حتى {_hm(tt)}: قمّة {hi:.4f} "
              f"({(hi / entry - 1) * 100:+6.1f}%) · إغلاق {cc:.4f}"
              f"{mark if False else ''}")
    if len(seg) > 28:
        print(f"   … و{len(seg) - 28} شريحةً أخرى (قُصّت بإعلانٍ لا صمتًا)")


BARS_ALL = (30.0, 50.0, 100.0)     # حدودُ العرض — 30 و50 من `KASIH_DESC`


def batch(day, bars, prev_close):
    """🔁 **إعادةُ قياس اليوم كلِّه** بأنبوبة `kasih_scan` نفسِها — عمودان
    لكلّ صفّ: **قبل الخروج** (ما تقيسه أرقامُنا) و**اليومُ كاملًا بلا قطع**
    (ما يراه المالك). يُرجع صفوفَ اليوم."""
    universe = {s for s, c in prev_close.items()
                if KS.PRICE_LO <= c <= KS.PRICE_HI}
    out = []
    for sym, b in bars.items():
        if universe and sym not in universe:
            continue
        if not KS.prescreen(b):
            continue
        e = KS.first_anchor(b)
        if e is None:
            continue
        a_ms, entry = int(e["anchor_ms"]), float(e["price"])
        pc = prev_close.get(sym)
        gap = (entry / pc - 1.0) * 100.0 if pc else None
        if gap is not None and abs(gap) > KS.GAP_CAP:
            continue
        res = KS.resolve(b, a_ms, entry)
        if res is None:
            continue
        usd5 = KS.f2_usd5(b, a_ms)
        f2key = S._ignition_candle_class(usd5)[0]
        k2 = K2.k2_features(b, a_ms, entry, f2key, gap,
                            float(e.get("usd") or 0), usd5)
        tev = {"stage": "M5", "k2": k2, "class": (f2key, ""),
               "anchor_price": entry, "prev_close": pc}
        tier = S.liq_tier(tev)
        alow = float(res["anchor_low"])
        ex_px, ex_ms, broke = exit_price(b, a_ms, alow)
        e5, broke5 = true_e5(b, a_ms, entry)
        ev = K2.entry_view(b, a_ms, entry, pc)
        mg5 = (ev or {}).get("mg5")
        o, pct = outcome(entry, res.get("mg_after"), ex_px, broke)
        if o == "تعذّر" and broke5:
            o = "خسرت"
        m5_all, at5 = full_day_max(b, a_ms, e5) if e5 else (None, None)
        m1_all, at1 = full_day_max(b, a_ms, entry)
        out.append({
            "sym": sym, "tier": (tier[0] if tier else None),
            "green": (tier[1] if tier else None),
            "entry": entry, "e5": e5, "mg5": mg5,
            "res": pct, "outcome": o,
            "ex_ms": ex_ms, "broke": broke,
            "m5_all": m5_all, "at5": at5, "m1_all": m1_all, "at1": at1,
            "after": bool(ex_ms and at5 and at5 > ex_ms),
        })
    out.sort(key=lambda r: -(r["m5_all"] if r["m5_all"] is not None else -1e9))
    print("\n" + "=" * 78)
    print(f"🔁 إعادةُ قياس اليوم كلِّه · {day} · {len(out)} مِرساة")
    print("=" * 78)
    print("الرمز    | الفئة  | أخضر | سعر M5  | 📏 قبل الخروج | الحصيلة "
          "| 🔴 اليومُ كاملًا | وقتُ القمّة | بعد الخروج؟")
    for r in out:
        e5s = f"{r['e5']:.4f}" if r["e5"] else "—"
        b4 = f"{r['mg5']:+.1f}%" if r["mg5"] is not None else "كُسر قبل5"
        allp = f"{r['m5_all']:+.1f}%" if r["m5_all"] is not None else "—"
        tt = _hm(r["at5"]) if r["at5"] else "—"
        print(f"{r['sym']:<8} | {(r['tier'] or '—'):<6} | "
              f"{(r['green'] if r['green'] is not None else '—'):>4} | "
              f"{e5s:>7} | {b4:>13} | {r['outcome']:<7} | {allp:>14} | "
              f"{tt:>10} | {'✅ نعم' if r['after'] else 'لا'}")
    # 🔴 حجمُ الحدّ بالرقم
    lost = [r for r in out if r["outcome"] in ("خسرت", "معلّقة")]
    print(f"\n🔴 **حجمُ الحدّ في {day}:**")
    for thr in BARS_ALL:
        n = sum(1 for r in lost
                if r["m5_all"] is not None and r["m5_all"] >= thr)
        print(f"   ↳ وُسِمت «خسرت/معلّقة» وقمّةُ يومها **‏+{thr:.0f}% فأكثر**"
              f" من سعر كرت M5: **{n}** من {len(lost)}")
    naf = sum(1 for r in out if r["after"])
    print(f"   ↳ وقعت قمّةُ اليوم **بعد** الخروج البنيويّ في **{naf}** من "
          f"{len(out)} مِرساة")
    return out


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    syms = [s.strip().upper() for s in
            (os.environ.get("PROBE_SYMS") or "").split(",") if s.strip()]
    days = [d.strip() for d in
            (os.environ.get("PROBE_DAYS") or "").split(",") if d.strip()]
    all_mode = (os.environ.get("PROBE_ALL") or "").strip() == "1"
    if (not syms and not all_mode) or not days:
        print("⛔ يلزم PROBE_DAYS ومعه PROBE_SYMS أو PROBE_ALL=1.")
        return 2
    print(f"🔬 مِجَسُّ سهمٍ في جلسة · "
          + ("**الكونُ كاملًا**" if all_mode else f"الرموز {syms}")
          + f" · الأيام {days}")
    print("⚖️ تشخيصٌ فقط — لا يُغيّر تعريفًا ولا رقمًا منشورًا.")
    for day in days:
        seed = KS.weekdays((dt.date.fromisoformat(day)
                            - dt.timedelta(days=7)).isoformat(),
                           (dt.date.fromisoformat(day)
                            - dt.timedelta(days=1)).isoformat())[-3:]
        prev_close = {}
        for sd in seed:
            k = AH.day_key(sd)
            mb, ep = AH.head_size_mb(k)
            if mb is None:
                continue
            dest = f"/tmp/sd-{sd}.csv.gz"
            if not AH.download(k, dest, ep):
                continue
            try:
                with gzip.open(dest, "rt") as fh:
                    _b, closes = KS.parse_day(fh, set())
                prev_close.update(closes)
            except (OSError, KeyError, ValueError):
                pass
            finally:
                try:
                    os.remove(dest)
                except OSError:
                    pass
        key = AH.day_key(day)
        mb, ep = AH.head_size_mb(key)
        if mb is None:
            print(f"⛔ ملفُّ {day} غيرُ متاح.")
            return 3
        dest = f"/tmp/sd-{day}.csv.gz"
        if not AH.download(key, dest, ep):
            print(f"⛔ تعذّر تنزيلُ {day}.")
            return 3
        with gzip.open(dest, "rt") as fh:
            bars, _c = KS.parse_day(fh, set() if all_mode else set(syms))
        try:
            os.remove(dest)
        except OSError:
            pass
        if all_mode:
            batch(day, bars, prev_close)
        else:
            for s in syms:
                probe(s, day, bars, prev_close.get(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
