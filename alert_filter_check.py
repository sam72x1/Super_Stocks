#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎛️📏 **مِجَسُّ الفلتر** — كم يبقى وكم يسقط، **بالاسم**، من جلسةٍ حقيقيّة؟

أمرُ المالك 2026-08-18: «ابن الفلتر و قس». هذا هو الشقُّ الثاني: يُعيد جلسةً
بقواعد الإنتاج نفسِها، ثم يُسعّر **كلّ توليفةِ فلترٍ مرشَّحة** فيقول: هذي تُبقي
كذا سهمًا وتُسقط فلانًا وفلانًا.

🔒 **مِجَسُّ كلفةٍ لا تجربةَ حكم** ⇒ بلا تسجيلٍ مسبق (سابقةُ `flatfiles_probe`
و`wall_stack`) — **ولا يُشتقّ منه ادّعاءُ حافّةٍ ولا ربحيّة**؛ سقفُه **جدولُ
كلفةٍ يختار منه المالك**.
🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
"""
import json
import os
import sys
import time

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402
import m0_probe as MZ                                              # noqa: E402
import gate_probe as GP                                            # noqa: E402

WORKERS = 8

# 🎛️ **التوليفاتُ المرشَّحة — كلٌّ محورٌ واحدٌ مفهوم**، ولا تُخلَط حتى يُعرَف
#    صاحبُ الأثر. (والمالكُ يختار واحدةً أو يركّب بكلمته.)
PRESETS = {
    "P0 بلا فلتر": {},
    "P1 قوائمُ الترشيح والارتداد فقط": {"sources": ["الترشيح", "الارتداد"]},
    "P2 داخلَ نطاق الدفعات": {"in_entry_band_only": True},
    "P3 شمعةُ مضاربٍ فأعلى (لا قروب)": {"classes": ["operator", "strong"]},
    "P4 المضاربُ مؤكَّدٌ بالطبعات (يُسقط ما لم يُقَس)": {"require_operator": True},
    "P5 أوّلُ إشعارٍ فقط (بلا تحديثات)": {"stages": ["M0", "M1", "M5", "M30"]},
    "P6 سيولةُ الدقيقة ‏100 ألفٍ فأكثر": {"min_usd": 100_000},
    "P7 رفعةُ الدقيقة ‏10% فأكثر": {"min_move_pct": 10.0},
    "P8 السعرُ من دولارٍ إلى عشرة": {"price_min": 1.0, "price_max": 10.0},
}


# 🚫 **ما لا يُقاس هنا يُعلَن ولا يُخمَّن:** الإعادةُ لا تجلب الصفقات ⇒ حقلُ
#    `operator` غائبٌ أصلًا، فذراعُ `require_operator` كانت ستطبع «كُتم 100%»
#    وهو **رقمٌ كاذب** (كلفةُ عدمِ الجلب لا كلفةُ الفلتر). ⇒ تُستبعَد بالاسم.
UNMEASURED = {"require_operator"}


def replay_symbol(bars):
    """▶️ دقيقةٌ مكتملةٌ في كلّ خطوة — **بدالّة الإنتاج نفسِها**."""
    st, out = {}, []
    win = int(bot.LIQ_WINDOW_MIN)
    for k in range(3, len(bars) + 1):
        evs, st = bot.liq_stage_events(bars[max(0, k - win):k], st)
        out.extend(evs or [])
    return out


def main():                                                       # noqa: C901
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("🎛️📏 مِجَسُّ الفلتر — «ابن الفلتر و قس» (أمرُ المالك)\n")
    print("   🔒 مِجَسُّ كلفةٍ لا تجربةَ حكم · وسقفُه جدولُ كلفةٍ يختار منه المالك.\n")

    day = (os.environ.get("GATE_DAY") or "").strip() or None
    if day:
        nb = len(MZ.day_minutes("AAPL", day=day) or [])
        if nb < 100:
            print(f"⛔ اليومُ {day} بلا بياناتٍ لشاهد الضبط ⇒ لا قياس.")
            return 2
        back = 0
    else:
        day, back, nb = GP.resolve_day()
        if not day:
            print("⛔ لم تُوجَد جلسةٌ فيها بيانات ⇒ لا قياس.")
            return 2
    print(f"📅 **الجلسةُ المقيسة: {day}** (‏{back} يومًا للخلف · شاهدُ الضبط "
          f"`AAPL` {nb} شمعة)\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                        # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    wl = dict(oel._WL)
    print(f"👁️ الكون: {len(uni_all)} سهمًا · وقائمةُ الترشيح "
          f"{len((wl.get('stocks') or []))} سهمًا (للسياق)")

    import concurrent.futures as cf
    t0, rows, fails = time.time(), [], 0
    by_sym = {r["symbol"]: r for r in uni_all if r.get("symbol")}

    def _one(sym):
        try:
            return (sym, MZ.day_minutes(sym, day=day))
        except Exception:                                        # noqa: BLE001
            return (sym, None)

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for sym, bars in pool.map(_one, sorted(by_sym)):
            if not bars or len(bars) < 5:
                fails += 1
                continue
            evs = replay_symbol(bars)
            if evs:
                rows.append((by_sym[sym], evs))
    n_ev = sum(len(e) for _r, e in rows)
    print(f"📥 أُعيدت الجلسةُ: {len(rows)} سهمًا مُنبَّهًا · **{n_ev} حدثًا** · "
          f"تعذّر {fails} · {round(time.time() - t0, 1)}ث")
    if not rows:
        print("⛔ صفرُ حدثٍ في هذي الجلسة ⇒ لا مادّةَ تُقاس.")
        return 5
    # 🕵️ **حدُّ صدقٍ يُقال قبل الجدول:** لا تُجلَب صفقاتُ المضارب في الإعادة
    #    (نداءٌ لكلّ حدث) ⇒ محورُ «المضارب مؤكَّد» **لا يكتم شيئًا هنا** ويُوسَم.
    print("   ⚠️ ولا تُجلَب صفقاتُ المضارب في الإعادة ⇒ محورُ «المضاربُ مؤكَّد» "
          "**غيرُ مقيسٍ هنا** ويُوسَم في الجدول.\n")

    base_syms = {r["symbol"] for r, _e in rows}
    print("=" * 74)
    print("① جدولُ الكلفة — كم يبقى وكم يُكتَم؟")
    print("=" * 74)
    print("  التوليفة | أسهمٌ تصلك | أحداث | كُتم | نصيبُ الكتم")
    res = {}
    for name, cfg in PRESETS.items():
        # 🔒 **الاستبعادُ بنيويٌّ من المفاتيح لا من اسمِ التوليفة** — فاسمٌ يُعاد
        #    تسميتُه لا يُسقط الوسمَ صامتًا (فخُّ «القفل النصّيّ» بعينه).
        if set(cfg) & UNMEASURED:
            res[name] = {"syms": None, "ev": None, "muted": [], "lost": []}
            print(f"  {name:<40} |  ⚠️ غيرُ مقيسٍ هنا — لا رقمَ يُطبَع "
                  f"(الطبعاتُ لا تُجلَب في الإعادة)")
            continue
        kept, muted = bot.apply_alert_filter(rows, cfg, wl)
        ks = {r["symbol"] for r, _e in kept}
        ke = sum(len(e) for _r, e in kept)
        res[name] = {"syms": ks, "ev": ke, "muted": muted,
                     "lost": sorted(base_syms - ks)}
        print(f"  {name:<40} | {len(ks):>9} | {ke:>5} | {len(muted):>4} | "
              f"{100.0 * len(muted) / max(1, n_ev):>5.0f}%")

    print("\n" + "=" * 74)
    print("② مَن يسقط — بالاسم لا مجمَّعًا")
    print("=" * 74)
    for name in PRESETS:
        if res[name]["syms"] is None:
            print(f"  {name}: ⚠️ غيرُ مقيس")
            continue
        lost = res[name]["lost"]
        if not lost:
            print(f"  {name}: **لا يسقط أحد**")
            continue
        print(f"  {name}: يسقط **{len(lost)}** ⇒ "
              + ", ".join("$" + x for x in lost[:16])
              + (f" … و{len(lost) - 16}" if len(lost) > 16 else ""))

    print("\n" + "=" * 74)
    print("③ أسبابُ الكتم — أوّلُ ثمانيةٍ لكلّ توليفة (شفافيّةُ القرار)")
    print("=" * 74)
    for name in PRESETS:
        m = res[name]["muted"]
        if not m:
            continue
        print(f"  {name}:")
        for sym, stg, why in m[:8]:
            print(f"     ${sym} · {stg} · {why}")
        if len(m) > 8:
            print(f"     … و{len(m) - 8} أخرى")

    print("\n" + "=" * 74)
    print("④ حدودُ صدقٍ تُقرأ مع الجدول لا بعده")
    print("=" * 74)
    print("  1. **جلسةٌ واحدة** ⇒ جدولُ كلفةٍ لا حكمٌ على العائد · **ولا صفقةَ تُقاس**.")
    print("  2. **الإعادةُ ترى كلَّ دقيقة** والحيُّ يلفّ كلَّ ‏≈60 ثانية ⇒ أعدادُ "
          "الأحداث **سقفٌ**، ونِسَبُ الكتم أدقُّ من أعدادها.")
    print("  3. **محورُ «المضاربُ مؤكَّد» غيرُ مقيسٍ هنا** (لا تُجلَب الصفقات في "
          "الإعادة) ⇒ يُوسَم ولا يُقارَن.")
    print("  4. **والسياقُ من قائمةِ اليوم لا من لحظة الحدث** (الدفعاتُ والفلوت "
          "والمتاح تتغيّر) ⇒ محاورُ السياق **تقريبٌ مُعلَن**.")
    print("  5. **وكلُّ محورٍ فاشلٌ-آمنٌ مفتوح**: حقلٌ غائبٌ ⇒ **يمرّ** — فالكتمُ "
          "المقيسُ أدنى ما يكون لا أعلاه.")
    print("  6. والكونُ رقيقٌ (أسهمُ فيصل) ⇒ لا يُعمَّم على كونٍ سائل.")
    print(f"\n⏱️ زمنُ التشغيل: {round(time.time() - t0, 1)}ث")
    print("\n📌 **للتشغيل حيًّا:** اكتب التوليفةَ في `alert_filter.json` — "
          "وملفٌّ فارغٌ `{}` = **بلا فلتر بت-بت**.")
    print("   نموذج: " + json.dumps({"sources": ["الترشيح"], "min_usd": 100000},
                                    ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
