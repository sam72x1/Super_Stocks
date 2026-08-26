"""🕐📡 مِجَسُّ «فجوة المزوّد» — أمرُ المالك «قس فجوة المزود» (2026-08-26، حالة `$CRE`).

السؤال: شمعةُ الدقيقة تُغلق عند بدايتها + 60 ثانية — **متى تصير قابلةً للتقييم
في عينِ الإنتاج؟** الإنتاجُ يقرأ عبر `polygon_minute_bars` ويُسقط أحدثَ صفٍّ
دائمًا («المتكوّنةُ تُسقَط» — `rows[:-1]`) ⇒ الشمعةُ قابلةٌ للتقييم فقط حين
تظهر في الردّ **وليست آخرَ صفّ**. الحالةُ المؤسِّسة مقيسة: شمعةُ `$CRE` أغلقت
11:42:00 ومسحتا 11:42:02 و11:42:20 لم تجداها، والتُقطت في مسحة 11:44:04.

مقياسان لكلّ شمعةٍ **أغلقت أثناء المِجَسّ** (ما أغلق قبل بدايته يُستبعَد —
لا نعرف متى ظهر · وما كان حاضرًا في أوّل ردٍّ يُستبعَد أيضًا):
  • `lag_pub`  = أوّلُ رصدٍ للشمعة في الردّ − لحظةُ إغلاقها.
  • `lag_eval` = أوّلُ رصدٍ لها **داخل `rows[:-1]`** − لحظةُ إغلاقها ⟸ **الحاكم**
    (هو ما يراه الإنتاجُ فعلًا). والسالبُ يُصفَّر (ظهورٌ قبل الإغلاق = صفرُ فجوة).

⚖️ **عتبةُ القراءة مثبَّتةٌ قبل التشغيل (لا تُحرَّك بعد الأرقام):** وسيطُ
`lag_eval` فوق 60 ثانية ⇒ فجوةُ المزوّد مادّيةٌ وتفسّر نمطَ `$CRE` وحدَها ·
تحت 15 ثانية ⇒ المزوّدُ بريءٌ والمهيمنُ إيقاعُ مسحِنا (الدورةُ ‏≈دقيقتين مقيسةٌ
من سجلّ العامل) · بينهما ⇒ العاملان معًا.

🔒 **قراءةٌ فقط** (لا تلغرام ولا كتابةَ حالة) · الجالبُ جالبُ الإنتاج **بالاسم**
(`bot.polygon_minute_bars` — لا نداءَ URL محلّيًّا فلا يصير للقياس مقياسان) ·
وشاهدُ ضبطٍ `AAPL` (سائلٌ يطبع شمعةً كلَّ دقيقة — لو غابت شموعُه فالعطلُ في
المِجَسّ لا المزوّد).

🕐 **تأريخٌ (2026-08-26، بعد أمر «نفّذ»):** `lag_eval` هنا يقيس قاعدةَ
`rows[:-1]` **كما كانت قبل الإصلاح** — ومنذ اعتماد «الإسقاط بساعة الحائط» في
المسار الحيّ (`liq_stage_events(now_ms=...)`) صار عمودُ `lag_pub` هو الأقربَ
لِما يراه الإنتاج (‏+ هامش `LIQ_BAR_CLOSE_GUARD_MS`)، ويبقى `lag_eval` قياسًا
لِما **كانت** تُكلّفه القاعدةُ القديمة (شاهدُ قبل/بعد لو أُعيد القياس).

⚠️ **حدودُ صدقٍ تُطبَع مع النتيجة:** نافذةُ تشغيلٍ واحدة (مقطعٌ من جلسةٍ
واحدة) · حبيبةُ الرصد = زمنُ جولةِ الرموز (تُقاس وتُطبَع — الفجوةُ الحقيقية قد
تكون أدنى بها) · و«قابلةٌ للتقييم» لرمزٍ رقيقٍ تتأخّر بغياب الشمعة التالية
أصلًا (بنيةُ `rows[:-1]` لا بطءُ المزوّد) ⇒ يُفصَل عمودُ «التالية متّصلة»
(الشمعةُ t+60 موجودة) عن «بفجوة».

المخارج: 0 = قِيس · 2 = لا مفتاح · 4 = صفرُ شمعةٍ قابلةٍ للقياس (حارسُ
الـno-op — الصفرُ الموحَّد بصمةُ عطبٍ لا نتيجة).
"""
import hashlib
import json
import os
import statistics
import sys
import time

import Super_stock as bot

CONTROL = "AAPL"
CASE = "CRE"
UNI_N = 6                      # عيّنةٌ حتميّة من قوائمنا (نمط control_panel)


def sample_universe(n=UNI_N):
    """عيّنةٌ حتميّةٌ بالهاش من قوائم البوت (لا انتقاءَ يدويًّا)."""
    syms = set()
    try:
        wl = json.load(open("weekly_watchlist.json", encoding="utf-8"))
        for sec in ("stocks", "pullback"):
            syms |= {s.get("symbol") for s in (wl.get(sec) or [])
                     if s.get("symbol")}
    except Exception:                                            # noqa: BLE001
        pass
    try:
        nw = json.load(open("near_watch.json", encoding="utf-8"))
        if isinstance(nw, dict):
            syms |= {k for k in nw if isinstance(k, str) and k.isalpha()}
    except Exception:                                            # noqa: BLE001
        pass
    syms.discard(CONTROL)
    syms.discard(CASE)
    ranked = sorted(syms, key=lambda s: hashlib.sha256(
        f"pg:{s}".encode()).hexdigest())
    return ranked[:n]


def _stats(vals):
    if not vals:
        return "n=0"
    v = sorted(vals)
    p90 = v[min(len(v) - 1, int(0.9 * len(v)))]
    return (f"n={len(v)} · وسيط {statistics.median(v):.1f}ث · "
            f"p90 {p90:.1f}ث · أقصى {v[-1]:.1f}ث")


def run(fetch=None, clock=None, sleep=None, syms=None,
        run_min=None, poll_sec=None):
    """يلفّ على الرموز ويرصد أوّلَ ظهورٍ وأوّلَ قابليةِ تقييمٍ لكلّ شمعة.

    الحاقناتُ (fetch/clock/sleep) للاختبار — الافتراضُ يُحسَم **وقتَ النداء**
    (درسُ «المسارُ يُحسم وقت النداء لا وقت التعريف»)."""
    fetch = fetch or bot.polygon_minute_bars
    clock = clock or time.time
    sleep = sleep or time.sleep
    # ⚠️ المدخلُ الفارغ من الـworkflow يصل "" — `or` لا `get(default)` وإلّا
    #    انهار `float("")` (بصمةُ «المدخل الفارغ» المقيسة في أدواتٍ سابقة).
    run_min = float((os.environ.get("PG_RUN_MIN") or "25")
                    if run_min is None else run_min)
    poll_sec = float((os.environ.get("PG_POLL_SEC") or "3")
                     if poll_sec is None else poll_sec)
    if syms is None:
        env_s = (os.environ.get("PG_SYMS") or "").replace("،", ",")
        if env_s.strip():
            syms = [s.strip().upper() for s in env_s.split(",") if s.strip()]
        else:
            syms = [CONTROL, CASE] + sample_universe()
    t0 = clock()
    t0_ms = int(t0 * 1000)
    first_pub, first_eval = {}, {}
    baseline, seen_all = {}, {}
    rounds = []
    while clock() - t0 < run_min * 60:
        r0 = clock()
        for sym in syms:
            try:
                bars = fetch(sym, minutes=30) or []
            except Exception:                                    # noqa: BLE001
                continue                       # عطلُ جلبٍ لرمزٍ لا يقتل الجولة
            now = clock()
            ts = [b.get("t") for b in bars if b.get("t")]
            seen_all.setdefault(sym, set()).update(ts)
            if sym not in baseline:
                baseline[sym] = set(ts)        # الحاضرُ عند البدء يُستبعَد
                continue
            for i, t in enumerate(ts):
                if t in baseline[sym] or (t + 60_000) < t0_ms:
                    continue                   # أغلقت قبل البدء ⇒ خارج المقام
                k = (sym, t)
                if k not in first_pub:
                    first_pub[k] = now
                if i < len(ts) - 1 and k not in first_eval:
                    first_eval[k] = now        # داخل rows[:-1] = قابلة للتقييم
        rounds.append(clock() - r0)
        rest = poll_sec - (clock() - r0)
        if rest > 0:
            sleep(rest)
    return _report(first_pub, first_eval, seen_all, rounds, syms, t0, clock())


def _report(first_pub, first_eval, seen_all, rounds, syms, t0, t1):
    def lag(rec, k):
        sym, t = k
        return max(0.0, rec[k] - (t / 1000.0 + 60.0))

    strata = {"شاهد الضبط (AAPL)": [CONTROL],
              "سهم الحالة (CRE)": [CASE],
              "عيّنة قوائمنا": [s for s in syms if s not in (CONTROL, CASE)]}
    print("=" * 68)
    print(f"🕐📡 فجوةُ المزوّد — {len(syms)} رمزًا · "
          f"{(t1 - t0) / 60:.1f} دقيقة قياس · حبيبةُ الرصد "
          f"وسيطًا {statistics.median(rounds) if rounds else 0:.1f}ث")
    print("=" * 68)
    total_eval = 0
    for name, group in strata.items():
        pub = [lag(first_pub, k) for k in first_pub if k[0] in group]
        evl = [lag(first_eval, k) for k in first_eval if k[0] in group]
        # المنشورةُ ولم تصر قابلةً للتقييم حتى النهاية (آخرُ صفٍّ بقيت)
        stuck = sum(1 for k in first_pub
                    if k[0] in group and k not in first_eval)
        cons = [lag(first_eval, k) for k in first_eval if k[0] in group
                and (k[1] + 60_000) in seen_all.get(k[0], set())]
        total_eval += len(evl)
        print(f"\n— {name}:")
        print(f"   الظهور   (lag_pub) : {_stats(pub)}")
        print(f"   التقييم  (lag_eval): {_stats(evl)}")
        print(f"   منها متّصلةُ التالية: {_stats(cons)}")
        if evl:
            over = {s: sum(1 for v in evl if v > s) for s in (30, 60, 120)}
            print(f"   فوق 30ث: {over[30]}/{len(evl)} · فوق 60ث: "
                  f"{over[60]}/{len(evl)} · فوق 120ث: {over[120]}/{len(evl)}")
        print(f"   ظهرت ولم تصر قابلةً للتقييم حتى النهاية: {stuck}")
    print("\n⚖️ القراءةُ بالعتبة المثبَّتة سلفًا: وسيطُ التقييم فوق 60ث = فجوةُ"
          " مزوّدٍ مادّية · تحت 15ث = المزوّدُ بريءٌ والمهيمنُ إيقاعُ المسح.")
    print("⚠️ حدودُ الصدق: نافذةٌ واحدة · الحبيبةُ أعلاه سقفُ دقّةِ كلّ رقم · "
          "والرقيقُ تتأخّر قابليتُه ببنية rows[:-1] لا بالمزوّد (اقرأ عمودَ "
          "«متّصلة التالية»).")
    if total_eval == 0:
        print("⛔ صفرُ شمعةٍ قابلةٍ للقياس — no-op لا نتيجة (خروج 4).")
        return 4
    return 0


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس.")
        return 2
    return run()


if __name__ == "__main__":
    sys.exit(main())
