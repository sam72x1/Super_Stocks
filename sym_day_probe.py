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


def main() -> int:
    if not (os.environ.get("AWS_ACCESS_KEY_ID") or "").strip():
        print("⛔ لا مفاتيح S3 — لا قياس (ولا يُخمَّن رقم).")
        return 2
    syms = [s.strip().upper() for s in
            (os.environ.get("PROBE_SYMS") or "").split(",") if s.strip()]
    days = [d.strip() for d in
            (os.environ.get("PROBE_DAYS") or "").split(",") if d.strip()]
    if not syms or not days:
        print("⛔ يلزم PROBE_SYMS و PROBE_DAYS.")
        return 2
    print(f"🔬 مِجَسُّ سهمٍ في جلسة · الرموز {syms} · الأيام {days}")
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
            bars, _c = KS.parse_day(fh, set(syms))
        try:
            os.remove(dest)
        except OSError:
            pass
        for s in syms:
            probe(s, day, bars, prev_close.get(s))
    return 0


if __name__ == "__main__":
    sys.exit(main())
