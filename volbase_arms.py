#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📏🔊 **أذرعُ مرجع الحجم** — عقدُها `volbase_prereg.md` (مدفوعٌ قبل أيّ رقم).

أمرُ المالك 2026-08-29: «سجل مرجع الحجم». السؤال: هل **مرجعُ حجمٍ لا تبتلعه
الحركةُ نفسُها** يُقدّم المِرساةَ ماديًّا بلا هدمِ جودةِ الإشعار ولا إغراقِ القناة؟

🔴 **العطبُ مقروءٌ من الكود:** مقامُ `vx` نافذةٌ متدحرجةٌ ‏63 دقيقة تدخلها شمعاتُ
الركضة نفسُها ⇒ بنموذجٍ بسيط ينهار `vx` من ‏5.00 إلى **‏2.95** عند الدقيقة الحادية
عشرة من الركض ⇒ **يستحيل بنيويًّا العبورُ بعدها.**

⚖️ **صفرُ رقمٍ مخترَع:** المضاعفُ ‏3.0 (رقمُ المالك) · النافذةُ 65 · و`B1` إحصاءٌ
آخرُ على البيانات نفسِها · و`B2` مقامُه ‏390 = طولُ الجلسة النظاميّة (‏`engineering`
مُعلَنٌ في `§⑨-5`) وحجمُ الأمس **مجلوبٌ في النداء نفسِه** ⇒ صفرُ نداءٍ إضافيّ.
🔒 **مقياسٌ واحدٌ لا اثنان:** البوّابةُ من `gate_probe.gate_trace` **نفسِها**
والإثمارُ من `liq_move_probe.fruit` **نفسِها** — والمِرساةُ بالميزانية نفسِها للأربع.
🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
"""
import datetime as dt
import os
import statistics as stt
import time
import zoneinfo

os.environ.setdefault("SCREENER_MODE", "PROBE")
import requests                                                    # noqa: E402
import Super_stock as bot                                          # noqa: E402
import gate_probe as GP                                            # noqa: E402
import cumrise_probe as CR                                          # noqa: E402
import liq_move_probe as LM                                        # noqa: E402
import m0_probe as MZ                                              # noqa: E402
import probe_common as PC                                          # noqa: E402

# ⚙️ **الأذرعُ الأربع مثبَّتةٌ في `volbase_prereg.md §②` — ولا تُزاد بعد الأرقام.**
ARMS = {
    "B0": {},
    "B1": {"vol_ref": "median"},
    "B2": {"vol_ref": "prev"},
    "B3": {"vol_ref": "min"},
}
ARM_DESC = {
    "B0": "الإنتاجُ كما هو — متوسّطُ النافذة (يُبتلَع بالركضة)",
    "B1": "🟢 وسيطُ النافذة نفسِها — إحصاءٌ صامد · صفرُ نداءٍ وصفرُ رقم",
    "B2": "🟢 حجمُ الجلسة السابقة ÷ 390 — مرجعٌ **يستحيل** ابتلاعُه",
    "B3": "⛔ الأدنى منهما — **حدٌّ أعلى رتيبٌ لا اقتراح**",
}
SESSION_MIN = 390.0         # engineering — طولُ الجلسة النظاميّة (‏§⑨-5)
# 🔒 **الحدودُ الأربعةُ تُقرأ من `cumrise_probe` بالاسم لا تُنسَخ** — وإلّا صار
#    للمشروع مسطرتان تتباعدان، وبطلت المقارنةُ مع `cumrise_result.md` صامتةً.
LATE_GAIN_MIN = CR.LATE_GAIN_MIN
ALERT_MAX_GROWTH = CR.ALERT_MAX_GROWTH
FRUIT_MIN_N = CR.FRUIT_MIN_N
LATE_MIN_N = CR.LATE_MIN_N
MOVER_MIN_N = CR.MOVER_MIN_N
NEAR_VX_LO, NEAR_VX_HI = 2.0, 3.0   # عدّادٌ وصفيّ «كادت» (‏§⑧)
_NY = zoneinfo.ZoneInfo("America/New_York")

# 📌 **[تاريخٌ — غيرُ نافذ]** كان مرجعَ `V0` الأصليّ: صفُّ `R0` في
#    `cumrise_result.md §①`. **سقط بنيويًّا** لأن الكونَ حالةٌ حيّةٌ
#    تتغيّر يوميًّا (‏382 مقابل 314) ⇒ حلَّ محلَّه `V0-ب` (ملحق ⑪).
#    ويبقى مكتوبًا **شاهدًا على ما قِيس هناك** لا حارسًا هنا.
V0_REF = {"fired": 29, "late_med": 20.5, "fruit_pct": 44.8, "fruit_n": 29,
          "alerts": 80, "movers_hit": 13, "movers": 15, "data": 307, "uni": 314}


def prev_day_bar(sym, day):
    """📉 **الشمعةُ اليوميّة السابقةُ كاملةً** (إغلاقًا **وحجمًا**) بمنطق
    `gate_probe.prev_close` حرفيًّا: مدًى يوميّ ثمّ **آخرُ جلسةٍ قبل يوم القياس**.

    ⚖️ ولماذا لا نُنادي `prev_close` ثم نجلب الحجمَ بنداءٍ ثانٍ: النداءُ **واحد**
    والاستجابةُ تحمل `v` أصلًا — و`prev_close` كانت ترميه. **والتكافؤُ مقفولٌ
    سلوكيًّا** (`VB2`) بحقنِ استجابةٍ واحدة في الوحدتين ⇒ صفرُ منطقٍ ثانٍ."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key or not day:
        return None
    try:
        d1 = dt.date.fromisoformat(str(day))
        d0 = (d1 - dt.timedelta(days=12)).isoformat()
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/"
                         f"{sym.upper()}/range/1/day/{d0}/{day}",
                         headers={"Authorization": f"Bearer {key}"},
                         params={"adjusted": "true", "sort": "asc",
                                 "limit": 50}, timeout=12)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        cut = int(dt.datetime.combine(
            d1, dt.time()).replace(tzinfo=dt.timezone.utc).timestamp()) * 1000
        prior = [b for b in res if b.get("t") is not None and int(b["t"]) < cut
                 and b.get("c")]
        return prior[-1] if prior else None
    except Exception:                                            # noqa: BLE001
        return None


def vpm_of(bar):
    """🔊 حجمُ الجلسة السابقة **لكلّ دقيقة** — أو `None` (يُعَدّ ولا يُخمَّن)."""
    try:
        v = float((bar or {}).get("v") or 0.0)
        return (v / SESSION_MIN) if v > 0 else None
    except Exception:                                            # noqa: BLE001
        return None


def is_premarket(ms):
    """🌙 هل الشمعةُ قبل جرس ‏09:30 بتوقيت نيويورك؟ (يتشتّى آليًّا)."""
    t = dt.datetime.fromtimestamp(int(ms) / 1000, tz=dt.timezone.utc).astimezone(_NY)
    return t.hour * 60 + t.minute < 9 * 60 + 30


# ───────────────────────────────── الأقفال ─────────────────────────────────
def _lock_arms():
    """🔒 `LOCK-VB` — حرّاسٌ **منفَّذةٌ لا موصوفة** (‏`volbase_prereg §⑤`).

    `V1` البوّابةُ تطابق الإنتاج (تُستعار من `gate_probe._lock_g0` بالاسم) ·
    `V3` **بلا `vol_ref` المُخرَجُ بت-بت** (وإلّا بطلت أرقامُ G0-G6 وR0-R3) ·
    و**كلُّ ذراعٍ تفرّق فعلًا** على عيّنةٍ مبنيّة — وإلّا فهي `no-op`."""
    ok, notes = GP._lock_g0()
    notes = ["(من `gate_probe`) " + n for n in notes]

    def _b(i, o, h, l, c, v):
        return {"t": i * 60_000, "o": o, "h": h, "l": l, "c": c, "v": v}

    # 🔒 `V3` — بلا `vol_ref` المُخرَجُ مطابقٌ حرفيًّا (بأيّ `prev_vpm`)
    base = [_b(i, 1.0, 1.005, 0.995, 1.0, 500) for i in range(8)]
    hot = base + [_b(8, 1.00, 1.30, 1.00, 1.29, 40_000),
                  _b(9, 1.29, 1.30, 1.28, 1.29, 100)]
    t_a = GP.gate_trace(hot, 8, ARMS["B0"])
    t_b = GP.gate_trace(hot, 8, ARMS["B0"], prev_vpm=999_999.0)
    same = t_a == t_b
    notes.append(f"`V3` بلا vol_ref المُخرَجُ بت-بت مهما كان prev_vpm "
                 f"{'✅' if same else '❌'}")
    ok = ok and same

    # 🔒 **الابتلاع** — عيّنةٌ تُظهر العطبَ نفسَه: ركضةٌ طويلة تبتلع المتوسّطَ
    #    ولا تبتلع الوسيط ⇒ `B0` تسقط على الحجم و`B1` تعبر.
    # 🐞 **الأحجامُ معزولةٌ عمدًا:** عيّنتي الأولى سقطت على **الأرضية
    #    الدولاريّة** لا على الحجم (‏3 دقائقَ × ‏$5.8K = ‏$17.5K دون الثلاثين)
    #    ⇒ القفلُ كان يقيس شرطًا آخر — عينُ عيب `G2` الموثَّق في `_lock_g0`.
    #    الآن الهادئُ 2,000 والحارُّ 12,000 ⇒ التراكميُّ ‏≈$44K **فوق** الأرضية
    #    والفارقُ **قفزةُ الحجم وحدَها**: متوسّطُ `B0` مُبتلَعٌ ‏5,333 (‏vx=2.25 ❌)
    #    ووسيطُ `B1` صامدٌ 2,000 (‏vx=6.0 ✅).
    quiet = [_b(i, 1.0, 1.005, 0.995, 1.0, 2_000) for i in range(40)]
    ramp = list(quiet)
    px = 1.0
    for k in range(40, 60):                       # ‏20 دقيقةَ ركضٍ حارّة
        o_, px = px, round(px * 1.008, 4)
        ramp.append(_b(k, o_, px, o_, px, 12_000))
    o_, px2 = px, round(px * 1.06, 4)
    ramp.append(_b(60, o_, px2, o_, px2, 12_000))  # الدقيقةُ المرشَّحة
    ramp.append(_b(61, px2, px2, px2 * 0.999, px2, 100))
    got = {a: GP.anchor_of(ramp, ARMS[a], prev_vpm=1_000.0)[0] for a in ARMS}
    # `B0` يُبتلَع مرجعُه فلا يعبر عند 60 · و`B1`/`B2`/`B3` تعبر
    good = (got["B0"] != 60) and got["B1"] == got["B2"] == got["B3"] == 60
    notes.append(f"الابتلاع: {got} — `B0` مُبتلَعٌ والبقيّةُ تعبر "
                 f"{'✅' if good else '❌'}")
    ok = ok and good

    # 🔒 **و`B2` قد يكون أشدَّ** (مرجعٌ عالٍ من جلسةٍ سابقةٍ كثيفة) — يفرّق
    #    في الاتّجاه الآخر أيضًا فليس «تخفيفًا رتيبًا».
    got2 = {a: GP.anchor_of(hot, ARMS[a], prev_vpm=100_000.0)[0] for a in ARMS}
    good2 = got2["B0"] == 8 and got2["B2"] is None and got2["B3"] == 8
    notes.append(f"`B2` يشدّ بمرجعٍ عالٍ: {got2} {'✅' if good2 else '❌'}")
    ok = ok and good2

    # 🔒 **`B3` رتيبةٌ بنيويًّا**: لا تكتم دقيقةً يُطلقها `B0`
    for nm, bb, pv in (("ركضة", ramp, 1_000.0), ("حارّة", hot, 100_000.0)):
        f0 = set(GP.all_fires(bb, ARMS["B0"], prev_vpm=pv))
        f3 = set(GP.all_fires(bb, ARMS["B3"], prev_vpm=pv))
        g = f0 <= f3
        notes.append(f"{nm}: `B3` ⊇ `B0` {'✅' if g else '❌'}")
        ok = ok and g

    # 🔒 `VB2` — **تكافؤُ الجالب**: نفسُ الاستجابة ⇒ نفسُ الإغلاق في الوحدتين
    class _R:
        status_code = 200

        @staticmethod
        def json():
            return {"results": [{"t": 1_000, "c": 9.0, "v": 100.0},
                                {"t": 10**13, "c": 7.0, "v": 200.0}]}

    _og, _oq = GP.requests.get, requests.get
    _kk = os.environ.get("POLYGON_API_KEY")
    try:
        os.environ["POLYGON_API_KEY"] = "x"
        GP.requests.get = requests.get = lambda *a, **k: _R()
        _pc = GP.prev_close("AAPL", "2026-08-17")
        _pb = prev_day_bar("AAPL", "2026-08-17")
        eq = (_pb is not None) and float(_pb["c"]) == _pc == 9.0
    finally:
        GP.requests.get, requests.get = _og, _oq
        if _kk is None:
            os.environ.pop("POLYGON_API_KEY", None)
        else:
            os.environ["POLYGON_API_KEY"] = _kk
    notes.append(f"`VB2` الجالبُ يكافئ `prev_close` بت-بت {'✅' if eq else '❌'}")
    ok = ok and eq
    return ok, notes


def _prod_anchor(bars):
    """🏭 مِرساةُ **دالّة الإنتاج** `liq_stage_events` بإعادةِ تشغيلٍ تدريجيّة.

    ⚖️ **ولماذا تدريجيّة:** بحالةٍ فارغةٍ تُقيّم الدالّةُ **آخرَ شمعةٍ مغلقة
    وحدَها** («أوّلُ رؤيةٍ بلا رشٍّ رجعيّ») ⇒ تمريرُ اليوم كاملًا مرّةً واحدةً
    يفحص دقيقةً واحدةً لا الجلسة. والبدءُ من `k=4` ليكون أوّلُ مُقيَّمٍ
    `bars[2]` — **وهو أوّلُ ما يفحصه `anchor_of`** فيتطابق المجالان.

    🔴🔴 **والنافذةُ تُقصّ عند المُنادي لا داخل الدالّة** — `scan_liq_stages`
    يجلب `fb(sym, minutes=LIQ_WINDOW_MIN)` ⇒ `liq_stage_events` **لا ترى
    أكثرَ من 65 دقيقةً أبدًا في الإنتاج**. وأوّلُ صياغةٍ لي مرّرت **اليومَ
    كاملًا** فقارنت مرجعَ يومٍ بمرجعِ 65 دقيقة ⇒ ثلاثةُ تفرّقاتٍ **باتّجاهين
    متعاكسين** في التشغيلة `33243937802`. 🧭 **والدرس: محاكاةُ الإنتاج تشمل
    ما يفعله المُنادي، لا جسمَ الدالّة وحدَه** — وستُّ عيّناتٍ مصطنعةٍ من عشر
    شمعاتٍ لا تكشفه لأن القصَّ فيها `no-op`."""
    W = int(bot.LIQ_WINDOW_MIN)
    st = {}
    for k in range(4, len(bars) + 1):
        try:
            ev, st = bot.liq_stage_events(bars[max(0, k - W):k], st)
        except Exception:                                        # noqa: BLE001
            return "رمى"
        for e in (ev or []):
            if e.get("stage") == "M1":
                return int(e["last_ms"])
    return None


def _v0b_check(data, fired, sample_n=40):
    """🔒 `V0-ب` (ملحق ⑪ · 2026-08-29) — `B0` يطابق **دالّةَ الإنتاج** على
    **بياناتِ السوق الحقيقيّة** رمزًا رمزًا. وتفرّقٌ واحدٌ ⇒ **خروج 3**.

    🔴 **وحلَّ محلَّ `V0` الأصليّ لأنه غيرُ قابلٍ للاستيفاء بنيويًّا:** الكونُ
    يُبنى من حالةٍ حيّةٍ يعيد البوتُ كتابتها كلَّ دقائق ⇒ إعادةُ الجلسة نفسِها
    لا تُعيد الكونَ نفسَه (‏382 مقابل 314). **والسببُ والبديلُ معلنان في العقد.**

    ⚖️ **والعيّنةُ تُعلَن بعددها** (درسُ `RV0`): **كلُّ** مَن له مِرساةٌ تحت
    `B0` — وهم موضعُ الخطر — **زائدَ** عيّنةٍ حتميّةٍ ممّن لا مِرساةَ لهم
    (فالمطابقةُ تشمل «صمتَ الطرفين» لا «إطلاقَهما» فقط)."""
    quiet = sorted(s for s in data if s not in fired)[:int(sample_n)]
    syms = sorted(fired) + quiet
    diff = []
    for s in syms:
        bars = data[s]
        i, _t = GP.anchor_of(bars, ARMS["B0"])
        mine = int(bars[i]["t"]) if i is not None else None
        prod = _prod_anchor(bars)
        if prod != mine:
            diff.append((s, prod, mine))
    return (not diff), len(syms), len(fired), diff[:6]


def main():                                                       # noqa: C901
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("📏🔊 أذرعُ مرجع الحجم — عقدُها `volbase_prereg.md`\n")
    print(f"   النافذُ: قفزةٌ {bot.CONFIG['IGNITION_VOL_MULT']}× · نافذةٌ "
          f"{bot.LIQ_WINDOW_MIN}د · أرضيةُ ${bot.LIQ_MIN_USD:,} على "
          f"{bot.LIQ_CUM_MINUTES}د · رفعةُ {bot.LIQ_MIN_MOVE_PCT}%")
    print("   ⚖️ **أرقامُ المالك لا تُمَسّ** — المتغيّرُ **مقامُ قفزة الحجم** وحدَه.\n")
    ok, notes = _lock_arms()
    for n in notes:
        print("   🔒 " + n)
    if not ok:
        print("\n⛔ `LOCK-VB` سقط ⇒ **لا يُنشَر رقم** (خروج 3).")
        return 3
    print("   ✅ `LOCK-VB` عبر — والأذرعُ الأربعُ تفرّق في الاتّجاهين.\n")

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
          f"`AAPL` {nb} شمعة) — تُحسَم مرّةً واحدةً للكلّ.\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                        # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (نفسُ كونِ المُشغِّل · بلا استثناء)")

    import concurrent.futures as cf
    t0, data, pc, vpm, fails, no_vol = time.time(), {}, {}, {}, 0, 0

    def _one(s):
        try:
            return (s, MZ.day_minutes(s, day=day), prev_day_bar(s, day))
        except Exception:                                        # noqa: BLE001
            return (s, None, None)

    # 🔒 **ميزانيةٌ واحدة**: الشموعُ وحجمُ الأمس يُجلَبان **مرّةً** والأربعُ
    #    تُقاس عليها (درسُ `T-CLIFF`: فرقٌ صنعته الميزانيةُ لا الذراع).
    with cf.ThreadPoolExecutor(max_workers=GP.WORKERS) as pool:
        for s, bars, pb in pool.map(_one, syms):
            c = float(pb["c"]) if (pb and pb.get("c")) else None
            if bars and len(bars) >= 5 and c:
                data[s], pc[s] = bars, c
                v = vpm_of(pb)
                if v is None:
                    no_vol += 1
                else:
                    vpm[s] = v
            else:
                fails += 1
    print(f"📥 شموعُ اليوم ‏+ شمعةُ الأمس: {len(data)} من {len(syms)} · تعذّر "
          f"{fails} · بلا حجمِ أمسٍ {no_vol} (يُعَدّ ولا يُخمَّن) · "
          f"{round(time.time() - t0, 1)}ث")
    if not data:
        print("⛔ صفرُ بيانات — لا قياس.")
        return 2
    if PC.coverage_bad(len(data), len(syms), PC.MAX_MISS_FRAC):
        print(f"⛔ تغطيةٌ ناقصة: {fails} من {len(syms)} (الحدّ "
              f"{PC.MAX_MISS_FRAC:.0%}) ⇒ عطبُ أداةٍ لا نتيجة — لا حكم.")
        return 3
    if no_vol:
        print(f"   ⚠️ **{no_vol} سهمًا بلا حجمِ أمس** ⇒ `B2`/`B3` تُقصيهم "
              "**والمقامُ يُعلَن** — ولا يُنسَب فقدُهم إلى الذراع.")

    movers = []
    for s, bars in data.items():
        hi = max(float(b["c"]) for b in bars)
        if (hi / pc[s] - 1.0) * 100.0 >= GP.MOVER_PCT:
            movers.append(s)
    print(f"🏃 المتحرّكون (‏+{GP.MOVER_PCT:.0f}% فأكثر): **{len(movers)}** — "
          f"{', '.join(sorted(movers)[:14])}"
          + (f"\n   ⚠️ **دون {MOVER_MIN_N} ⇒ المعيار ④ غيرُ مقيس**"
             if len(movers) < MOVER_MIN_N else "") + "\n")

    res, insane = {}, 0
    for an, arm in ARMS.items():
        late, fr, unres, fired, alerts, pre_n = [], [], 0, {}, 0, 0
        for s, bars in data.items():
            pv = vpm.get(s)
            i, t = GP.anchor_of(bars, arm, prev_vpm=pv)
            alerts += len(GP.all_fires(bars, arm, prev_vpm=pv))
            if i is None:
                continue
            fired[s] = i
            if is_premarket(bars[i]["t"]):
                pre_n += 1
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
                   "alerts": alerts, "fruit_n": len(fr), "pre_n": pre_n,
                   "fruit_pct": (100.0 * hit / len(fr)) if fr else None,
                   "unres": unres}

    if not any(r["fired"] for r in res.values()):
        print("⛔ صفرُ حدثٍ في هذي الجلسة ⇒ **لا مادّةَ تُقاس** (خروج 5).")
        return 5

    # 🔒 `V1` — حارسُ الـ`no-op`: الأذرعُ الأربعُ **تتفرّق** على البيانات الحيّة
    sig = {a: (len(res[a]["fired"]), res[a]["alerts"]) for a in ARMS}
    if len(set(sig.values())) < 2:
        print(f"⛔ `V1`: الأذرعُ الأربعُ متطابقةٌ بت-بت {sig} = **بصمةُ `no-op`** "
              "⇒ لا تُفسَّر نتيجتُها (خروج 4).")
        return 4

    b = res["B0"]
    print("=" * 76)
    print("⓪ `V0-ب` — هل يطابق `B0` **دالّةَ الإنتاج** على بياناتِ السوق؟")
    print("=" * 76)
    _t0 = time.time()
    okv, n_cmp, n_fire, diff = _v0b_check(data, b["fired"])
    print(f"   قُورن **{n_cmp}** رمزًا حقيقيًّا (‏{n_fire} منها له مِرساة "
          f"و{n_cmp - n_fire} صامت) · {round(time.time() - _t0, 1)}ث")
    if not okv:
        print(f"   🔴 تفرّقٌ في {len(diff)} فأكثر — أوّلُها {diff} ⇒ "
              "**عطبُ أداةٍ لا نتيجة** (خروج 3).")
        return 3
    print("   ✅ مطابقٌ رمزًا رمزًا — إضافةُ `vol_ref` لم تُزحزح الإنتاج بحرف.")
    print("   🔴 **ولا تُقارَن هذي الأرقامُ عدديًّا بـ`cumrise_result.md`** — "
          "الكونُ حالةٌ حيّةٌ تغيّرت (ملحق ⑪).\n")

    print("=" * 76)
    print("① الجدولُ — التأخّرُ والإثمارُ والإشعارات")
    print("=" * 76)
    print("  الذراع | أسهمٌ تُنبَّه | وسيطُ التأخّر | أثمر٪ (مقام) | إشعارات | "
          "متحرّكون | بريماركت")
    for an in ARMS:
        r = res[an]
        lm = ("—" if r["late_med"] is None or len(r["late"]) < LATE_MIN_N
              else f"{r['late_med']:+.1f}%")
        fp = ("—" if r["fruit_pct"] is None or r["fruit_n"] < FRUIT_MIN_N
              else f"{r['fruit_pct']:.1f}% ({r['fruit_n']})")
        mv = sum(1 for s in movers if s in r["fired"])
        print(f"  {an:<6} | {len(r['fired']):>11} | {lm:>13} | {fp:>13} | "
              f"{r['alerts']:>7} | {mv:>7}/{len(movers)} | {r['pre_n']:>8}")
    for an in ARMS:
        print(f"     {an} = {ARM_DESC[an]}")
    if insane:
        print(f"  ⚠️ استُبعد {insane} تأخّرًا فوق {GP.LATE_SANE_MAX:.0f}% "
              "(تشويهُ تقسيمٍ) — يُعَدّ ويُسمّى ولا يُخمَّن.")

    print("\n" + "=" * 76)
    print("② الحكمُ بالمعايير الأربعة — كما سُجّلت قبل الأرقام")
    print("=" * 76)
    passed = []
    for an in ARMS:
        if an == "B0":
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
            lines.append("④ المتحرّكون: ⚠️ **غيرُ مقيس** (دون الأرضية)")
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
        if verdict and an == "B3":
            print("     ⇒ ⛔ **حدٌّ أعلى مسجَّلٌ سلفًا — لا يُقترَح مهما استوفى**")
        elif verdict:
            print("     ⇒ 🥇 **تستوفي الأربعة ⇒ مرشَّحٌ لقياس ناتجٍ ثلاثيِّ السنوات**")
            passed.append(an)
        else:
            print("     ⇒ 🔴 **لا تستوفي ⇒ لا تُقترَح**")

    print("\n" + "=" * 76)
    print("③ عدّاداتٌ وصفيّةٌ — تُطبَع ولا تحكم (‏§⑧)")
    print("=" * 76)
    near, only_vol, med_hi, med_n = 0, 0, 0, 0
    for s, bars in data.items():
        for i in range(2, len(bars) - 1):
            t = GP.gate_trace(bars, i, ARMS["B0"])
            if not t:
                continue
            if (not t["g_vol"]) and all(t[k] for k, _ in GP.GATE_ORDER
                                        if k != "g_vol"):
                only_vol += 1
                if NEAR_VX_LO <= t["vx"] < NEAR_VX_HI:
                    near += 1
        W = int(bot.LIQ_WINDOW_MIN)
        for i in range(2, len(bars) - 1, 5):
            win = bars[max(0, i + 2 - W): i + 2]
            pr = [float(x["v"]) for x in win[:-1][:-1]]
            if len(pr) >= 3:
                med_n += 1
                if stt.median(pr) > (sum(pr) / len(pr)):
                    med_hi += 1
    print(f"  🔊 دقائقُ سقطت **على قفزة الحجم وحدَها**: {only_vol} — منها "
          f"{near} ‏`vx` بين {NEAR_VX_LO} و{NEAR_VX_HI} («كادت») = "
          f"{(100.0 * near / only_vol) if only_vol else 0:.1f}%")
    print(f"  📐 نوافذُ كان فيها **الوسيطُ أعلى** من المتوسّط: {med_hi} من "
          f"{med_n} = {(100.0 * med_hi / med_n) if med_n else 0:.1f}% "
          "⇒ `B1` **ليس تخفيفًا رتيبًا** (‏`VB-P2`)")
    for an in ARMS:
        r = res[an]
        n = len(r["fired"])
        print(f"  🌙 {an}: بريماركت {r['pre_n']} من {n} = "
              f"{(100.0 * r['pre_n'] / n) if n else 0:.0f}% · "
              f"تعذّرَ إثمارُ {r['unres']}")

    print("\n" + "=" * 76)
    print("④ الخلاصة")
    print("=" * 76)
    if passed:
        print(f"  🥇 مرشَّحٌ للقياس الثلاثيّ: {', '.join(passed)} — "
              "**ولا اعتمادَ قبله** (‏`§⑥`).")
    else:
        print("  🔴 **لا ذراعَ تستوفي الأربعة** ⇒ مرجعُ الحجم ليس الرافعة "
              "على هذي الجلسة — والحكمُ يُقرأ مع حدود `§⑨`.")
    print("  ⚠️ جلسةٌ واحدة · «أثمر» لمسٌ لا تنفيذ · وسيطُ التأخّر على "
          "مجموعتين مختلفتين · و‏390 طولُ الجلسة النظاميّة لا مقياسٌ مُعايَر.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
