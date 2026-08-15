#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️📡 **رادار الضغط** — أداة مستقلة (أمر المالك 2026-08-14 «نفذ 1» بعد حالتَي
`WETO` ‏+177% و`CAPR` ‏+98%).

**الواقعة المسجَّلة:** السهمان كانا في قائمة مراقبة الارتداد يوم 08-07 بخطة كاملة
(‏WETO: منطقة 2.70-2.86 · هدف أول 5.50 · CAPR: منطقة 2.96-3.14 · هدف أول 4.48)،
ثم مسحتهما «بداية نظيفة» 08-08 مع الخمسة عشر، والمسار الرئيسي كان يرفضهما
بجدار `M4_base_واسعة`، فمرّت **فترة الضغط** (‏WETO: ‏11.72 ⟵ 3.34 في سبع جلسات
ثم الجلوس عند 3.4-3.6) **بلا أي عين** — وانفجرا في بريماركت 08-14.

**ماذا يفعل الرادار:** يوميًّا بعد إغلاق الافتر يمشي على **بِركة محدودة**
(قائمة الارتداد · أسهم القائمة · المتحرّكون والمشطوبون حديثًا · **وذاكرته
الخاصة التي تنجو من مسح القوائم** — وهذا حرفيًّا ثقب WETO/CAPR) ويقرأ نموذج
فيصل الموثّق (`FAISAL_PRESSURE_MODEL.md`: «اي سهم قبل يصعد يضغطه المضارب
لادنى شمعه · مسح السيوله = اوامر الوقف · اذا حافظ ع ادنى قاع طبق النموذج»):
  • **قراءة «مضغوطٌ جالسٌ عند قاعه»** (`press_read` نقيّة): قمةٌ حديثة في
    نافذة `W` ⟵ هبوطٌ منها بعمق `SPLIT_CLIFF_PCT`(=30) على الأقل ⟵ وآخرُ
    إغلاقٍ **عند قاع الضغط** (داخل `SPLIT_SWEEP_MAX_PCT`(=13)% فوقه — نطاق
    المسح الموثّق). الأرقام الثلاثة **قائمة في CONFIG لا مخترعة**.
  • «حافظ» يُعرَض عدّادًا (كم جلسة بلا قاعٍ جديد) ولا يُشترَط — فالتجربة
    الحيّة (‏WETO: القاع النهائي تكوّن مساء 08-13 والانفجار فجر 08-14) تثبت
    أن اشتراط جلساتِ حفظٍ مكتملة يجعل التنبيه **بعد** الحدث.
  • `Super_stock.tested_level` (مرساة الإنتاج المعتمدة) تُعرَض إثراءً إن وُجدت،
    ومعها **الخطة المحفوظة** من ذاكرة الرادار إن سبق للسهم خطةُ ارتداد.

⚠️ **تحقُّق تصميمٍ مسجَّل:** الصياغة الأولى (قاع 20 جلسة عبر `press_scan.classify`)
كانت **لن تلتقط WETO أصلًا** — قيعانُ ما قبل الركضة (‏2.70) أدنى من قاع الضغط
(‏3.34) فلا يكون «قاعًا جديدًا» أبدًا. فالقراءة هنا **من القمة لا من القاع
التاريخي**، وهي قراءةٌ جديدة باسمها لا نسخة من `press_scan`.

**🔒 عرض/تنبيه فقط — قيد الإثبات الأمامي:** خارج الفرز والجذور كليًّا
(`Super_stock` لا يستورد هذا الملف — مقفول)، لا بوّابة ولا وزن ولا توصية،
وكل تنبيه يُلحَق بسجلّ حصادٍ أماميّ (`press_radar_ledger.jsonl`) يُقاس منه
صدقُه بالجلسات (سابقة صيّاد المقسّم: يثبت نفسه حيًّا أو يسقط).
**صامتٌ عند اللا-مطابق** (سابقة صيّاد الظرف — قاعدة «الجاهز فقط»)، والتغطية
تُطبع في السجل دائمًا فلا يُخلَط «لا مطابق» بـ«لم يفحص».
🗜️ **حدُّ صدق:** `T-PRESS-Q` (فشلت) قاست حالة يوم الترشيح داخل المؤهَّلين؛
هذا الرادار يقرأ ظاهرةً أخرى (ضغطُ ما بعد الركضة على بِركة أسماءٍ نعرفها)
**ولم تُقَس بعد** — تنبيهُ عرضٍ بسجلّ حصاد، لا ادّعاءُ حافة.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import sys

STATE_FILE = "press_radar_state.json"      # ذاكرة البِركة + دِدوب التنبيه + ختم الجلسة
LEDGER_FILE = "press_radar_ledger.jsonl"   # حصاد أمامي (يُلحَق بعد الإرسال حصرًا)
W = 20                    # نافذة القمة الحديثة (نافذة نموذج الضغط المقيسة في T-PRESS)
# 🥇 «اعتمد الحفظ ووسّع» (أمر المالك 2026-08-14 مساءً بعد §⑪-ج و§⑬):
ALERT_W = 40              # نافذة قراءة **التنبيه** — VA1: التقاط الكتالوج 29/29
#                           والأفضل توقّعًا في كل سنة (§⑬)؛ نافذة الركضة تبقى W
READY_HOLD = 3            # «اذا حافظ ع ادنى قاع طبق النموذج» — الشريحة الموجبة
#                           المقيسة (§⑬: ‏+0.174R [+0.110,+0.240] · موجبة كل سنة)؛
#                           غير الحافظ يبقى ظاهرًا «👀 قيد المتابعة» (درس WETO:
#                           انفجر من حفظ 0ج — لا يُسقَط، يُميَّز)
MEMORY_DAYS = 45          # احتفاظ الذاكرة بالاسم منذ آخر ظهور (ينجو من مسح القوائم)
REALERT_DAYS = 5          # لا إعادة تنبيه لنفس السهم قبلها
POOL_CAP = 250            # سقف البِركة — القصّ يُعلَن بعدّاده لا صمتًا
ALERT_CAP = 8             # سقف أسطر الرسالة — الباقي يُذكَر عددًا لا يُطوى


def _log(m):
    print(m, flush=True)


# ─────────────────────────── الحالة (ذاكرة تنجو من المسح) ───────────────────────────

def load_state(path=STATE_FILE) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:                                            # noqa: BLE001
        return {}


def save_state(state: dict, path=STATE_FILE) -> bool:
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except Exception:                                            # noqa: BLE001
        return False


def _days_between(a_iso, b_iso):
    try:
        a = _dt.date.fromisoformat(str(a_iso)[:10])
        b = _dt.date.fromisoformat(str(b_iso)[:10])
        return abs((b - a).days)
    except Exception:                                            # noqa: BLE001
        return None


def build_pool(wl: dict, state: dict, today_iso: str):
    """يبني بِركة الرادار ويحدّث الذاكرة. ترجع (قائمة الرموز، عدد المقصوصين).

    المصادر بالأولوية: قائمة الارتداد (بخطتها — **تُلتقط لقطتها في الذاكرة**
    فتنجو من أي مسحٍ لاحق) ⟵ أسهم القائمة ⟵ المشطوبون حديثًا ⟵ المتحرّكون
    حديثًا ⟵ ذاكرة الرادار (آخر MEMORY_DAYS يومًا منذ آخر ظهور)."""
    mem = state.setdefault("symbols", {})
    order = []

    def _seen(sym, src, plan=None):
        sym = str(sym or "").upper()
        if not sym:
            return
        e = mem.setdefault(sym, {"first_seen": today_iso, "src": src})
        e["last_seen"] = today_iso
        if plan:                       # الخطة تُحدَّث عند توفرها (لقطة تنجو من المسح)
            e["plan"] = plan
            e["src"] = src
        if sym not in order:
            order.append(sym)

    for it in (wl.get("pullback") or []):
        plan = {k: it.get(k) for k in ("entry", "tranches", "pivot", "stop", "t1")
                if it.get(k) is not None}
        _seen(it.get("symbol"), "قائمة الارتداد", plan or None)
    for it in (wl.get("stocks") or []):
        _seen(it.get("symbol"), "قائمة الترشيح")
    for it in (wl.get("removed") or []):
        d = it.get("date") or it.get("removed_at")
        if d and (_days_between(d, today_iso) or 999) <= MEMORY_DAYS:
            _seen(it.get("symbol"), "شُطب حديثًا")
    for it in (wl.get("explosions") or []):
        d = it.get("date")
        if d and (_days_between(d, today_iso) or 999) <= MEMORY_DAYS:
            _seen(it.get("symbol"), "متحرّك حديث")
    # ذاكرة الرادار: كل اسم ظهر خلال MEMORY_DAYS يبقى مراقَبًا ولو مُسحت القوائم
    for sym, e in list(mem.items()):
        gap = _days_between(e.get("last_seen") or e.get("first_seen"), today_iso)
        if gap is not None and gap > MEMORY_DAYS:
            del mem[sym]                                   # تقليم الذاكرة القديمة
        elif sym not in order:
            order.append(sym)
    cut = max(0, len(order) - POOL_CAP)
    return order[:POOL_CAP], cut


# ─────────────────────────── قراءة الضغط (نقيّة) ───────────────────────────

def press_read(df, w=W, band_pct=None):
    """نقيّة: هل السهم «مضغوطٌ جالسٌ عند قاع ضغطه» الآن؟

    من نموذج فيصل الموثّق — والقراءة **من القمة الحديثة** لا من قاع التاريخ:
      ① قمةُ النافذة: أعلى High في آخر `w` جلسة (يوم القمة j*).
      ② عمق الضغط: هبوط آخر إغلاقٍ من القمة **‏SPLIT_CLIFF_PCT(=30)% فأكثر**.
      ③ قاعُ الضغط: أدنى Low من يوم القمة إلى اليوم — وآخرُ إغلاقٍ **جالسٌ
        عنده**: داخل `SPLIT_SWEEP_MAX_PCT`(=13)% فوقه (نطاق المسح الموثّق).
    «حافظ» يُرجَع **عدّادًا** (`hold_sessions` = جلسات منذ آخر قاعٍ جديد)
    و`tested_level` الإنتاجية تُرجَع إثراءً إن وُجدت. تعذّرٌ ⇒ None بلا انهيار.

    🧪 وسيطا البحث `w`/`band_pct` (‏§⑪-ج): افتراضُهما `W` و`None` (⇒ يقرأ
    `SPLIT_SWEEP_MAX_PCT` من CONFIG) = **سلوك الإنتاج بت-بت**؛ تمريرُ غيرهما
    مقصورٌ على مِجَسّ شبكة التركيبات — لا مسار إنتاجيّ يمرّرهما (مقفول).

    ✅ متحقَّق على أرقام WETO الحيّة: قمة 11.72 · إغلاق 08-13 = 3.61 ⇒ عمق
    ‏69.2% ✓ · قاع الضغط 3.34 ⇒ الجلوس 3.61 ≈ ‏+8.1% داخل 13% ✓ ⇒ يُطلق
    مساء 08-13 — قبل انفجار بريماركت 08-14."""
    import Super_stock as S                                      # noqa: PLC0415
    try:
        lo = df["Low"].values.astype(float)
        cl = df["Close"].values.astype(float)
        hi = df["High"].values.astype(float)
    except Exception:                                            # noqa: BLE001
        return None
    n = len(cl)
    i = n - 1
    if n < w + 1:
        return None
    try:
        win_hi = hi[i - w + 1:i + 1]
        j_star = int(i - w + 1 + max(range(len(win_hi)), key=lambda k: win_hi[k]))
        high_w = float(hi[j_star])
        close = float(cl[i])
        if high_w <= 0 or close <= 0 or j_star >= i:
            return None                       # القمةُ اليومَ نفسه = ما زال صاعدًا
        if close < float(S.CONFIG.get("SPLIT_RADAR_PRICE_MIN", 1.0)):
            return None                       # «السنتات خارج الشرح» (فيصل IMG_0153)
        drop = (high_w - close) / high_w * 100.0
        if drop < float(S.CONFIG.get("SPLIT_CLIFF_PCT", 30.0)):
            return None                       # هبوطٌ ضحل — ليس ضغط النموذج
        press_seg = lo[j_star:i + 1]
        press_low = float(min(press_seg))
        if press_low <= 0:
            return None
        j_low = int(j_star + max(k for k in range(len(press_seg))
                                 if float(press_seg[k]) == press_low))
        band = (float(band_pct) if band_pct is not None
                else float(S.CONFIG.get("SPLIT_SWEEP_MAX_PCT", 13.0)))
        near_cap = press_low * (1.0 + band / 100.0)
        if close > near_cap:
            return None                       # غادر قاعه — التنبيه فات محله
        tl = None
        try:
            _t = S.tested_level(df)
            if _t:
                tl = round(float(_t["level"]), 4)
        except Exception:                                        # noqa: BLE001
            tl = None
        # 🕯️ «الشمعة المهمة» (نص فيصل على NEXR، صورة 2026-08-14: «الشمعه
        # واضحه · ذيلها 2.60 · راسها 2.80 · لو كسر ذيلها ولا رجع يفشل ·
        # لذلك فيه طلبات مضارب — لو حطيت طلبي 2.70 و2.80 ممتاز»): شمعةُ
        # صنع القاع — ذيلُها القاع نفسه ورأسُها High يومها؛ طلباتُ فيصل
        # داخل مداها والفشلُ كسرُ الذيل بلا رجوع. حقلُ عرضٍ إضافيّ حصرًا.
        return {"close": round(close, 4), "high_w": round(high_w, 4),
                "press_low": round(press_low, 4),
                "imp_head": round(float(hi[j_low]), 4),
                "drop_pct": round(drop, 1),
                "hold_sessions": int(i - j_low),
                "runup_pct": round(runup_pct(hi, lo, j_star), 1),
                "tested_level": tl}
    except Exception:                                            # noqa: BLE001
        return None


def runup_pct(hi, lo, j_star, w=W):
    """نقيّة: **ركضةُ ما قبل الضغط** — قمةُ النافذة منسوبةً لأدنى قاعٍ في الـ`w`
    جلسة قبلها. من نموذج فيصل حرفيًّا («اي سهم **قبل يصعد** يضغطه المضارب»):
    الفئةُ المقصودة ركضت ثم ضُغطت (‏WETO: ‏2.6 ⟵ 11.72 = ‏+350%)، والميّتُ
    المنهار ينزل بلا ركضةٍ أصلًا (قمتُه بقايا هبوطٍ لا صعود). تعذّرٌ ⇒ 0."""
    try:
        j0 = max(0, int(j_star) - int(w))
        if int(j_star) <= j0:
            return 0.0
        base = float(min(lo[j0:int(j_star)]))
        if base <= 0:
            return 0.0
        return (float(hi[int(j_star)]) / base - 1.0) * 100.0
    except Exception:                                            # noqa: BLE001
        return 0.0


def prev_qualified(sym, bars, anchor_iso, max_back=120, step=5):
    """🔁 فكرة المالك (2026-08-14): «متجاوزُ البوابات **سابقًا** ثم ركض ثم
    انضغط». تفحص: هل قبله الإنتاجُ (أيُّ المسارين — الفرز أو الارتداد) في أيّ
    يومٍ معيَّن قبل المِرساة؟ عيّنةُ كلّ `step` جلسات حتى `max_back` ⇒ الناتج
    **أرضيةٌ لا حصر** (نافذةُ تأهّلٍ قصيرة قد تقع بين العيّنات). بإعدادات
    الإنتاج الحيّة اليوم (ومنها المرساة المُختبَرة) — مُعلَن."""
    import Super_stock as S                                      # noqa: PLC0415
    try:
        idx = [d for d in bars.index if str(d.date()) < anchor_iso]
        pos = {d: k for k, d in enumerate(bars.index)}
        n = len(idx)
        for off in range(3, max_back + 1, step):
            k = n - off
            if k < 60:
                break
            i = pos[idx[k]]
            sl = bars.iloc[:i + 1]
            try:
                if S.analyze_ticker(sym, sl) or S.analyze_ticker(sym, sl, pullback=True):
                    return str(idx[k].date())
            except Exception:                                    # noqa: BLE001
                continue
    except Exception:                                            # noqa: BLE001
        return None
    return None


def alert_rank(r: dict):
    """نقيّة: مفتاح ترتيب الرسالة — الأقرب لنمط WETO يتقدّم.

    🔴 تصحيحُ أول تشغيلة حيّة (2026-08-14): «الأعمق أولًا» صدّر أمواتَ ‏−99%
    (‏YYAI بستّة سنتات) في رأس الرسالة. الترتيب: صاحبُ خطةٍ محفوظة ⟵ مستوى
    مُختبَر ⟵ حفظٌ فعليّ (جلسات بلا قاعٍ جديد) ⟵ ثم العمق."""
    p = r.get("read") or {}
    # 🗜️ «ركضة قبل الضغط» مفتاحُ ترتيبٍ لا فلتر (قرار 2026-08-14 بعد القياس:
    # الفلترُ الصلب عند 50% يُبقي 13 من 26 من التقاط الكتالوج — يقتل النصف،
    # لأن ركضة الفئة أقدمُ من النافذة غالبًا. فتُعرَض وتُقدِّم ولا تُسقِط).
    import Super_stock as S                                      # noqa: PLC0415
    ran = 1 if float(p.get("runup_pct") or 0.0) >= float(
        S.CONFIG.get("EXPLOSION_PCT", 50.0)) else 0
    # 🔁 «تركيبة المالك» (2026-08-14): «مؤهلٌ سابقًا ثم انضغط» = الدرجة الأولى
    # (قِيست: 19 من 26 من التقاط الكتالوج + شبه صفر ضجيج) — **درجةٌ لا فلتر**
    # (الفلترُ الصلب يفقد 7 حقيقيين منهم ONCO/KUST — مقيس في §⑪-ب).
    return (-(1 if r.get("plan") else 0),
            -(1 if r.get("prev_q") else 0),
            -(1 if p.get("tested_level") else 0),
            -(1 if p.get("hold_sessions") else 0),
            -ran,
            -float(p.get("drop_pct") or 0.0))


def wake_read(df, ah_pct=None):
    """🔥 نقيّة: «صحوةُ آخر جلستين» — هل يُظهر السهمُ المضغوطُ الحافظُ سلوكَ
    مضاربٍ يتحرّك الآن؟ (مسكةُ المالك 2026-08-15: «27 سهمًا وش أدخل فيه؟ …
    المفروض وقت سلوك المضارب في آخر جلستين — فيصل يقول السهم بيتحرّك في
    الافتر/البري ومعناها فيه أشياء تدلّ على التحرّك يسويها المضارب»).

    **صفرُ منطقٍ جديد وصفرُ رقمٍ من عندي — تركيبُ ثلاث أدواتٍ قائمة بالاسم:**
      • `S.activity_features` (المبنيّة لسؤال «هل يجهّزه المضارب الآن؟» —
        عتباتُها من `CONFIG`: قفزةُ حجم `VOL_SPIKE_MULT`ד20 · توسّعُ مدى ·
        موضعُ إغلاق) — تُنادى على **آخر جلستين** (جلسةً جلسة) ويُؤخذ الأقوى،
        لأن نصَّ المالك «آخر جلستين» حرفيًّا.
      • `S.reversal_candle` (نموذجُ فيصل المنصوص: همر/نجمة صباح/هرامي/وت)
        على آخر ثلاث شموعٍ يومية.
      • حركةُ الجلسة الممتدة `ah_pct` (تُمرَّر من `extended_last_price` —
        «بيتحرك في الافتر» بلفظه) بعتبة `PM_MOVE_PCT` **القائمة** (‏10).
    **`awake`** = قفزةُ الحجم **أو** شمعةٌ انعكاسية **أو** حركةُ افترٍ فوق
    العتبة — الثلاثُ القويّة حصرًا (توسّعُ المدى وموضعُ الإغلاق سياقٌ في
    `score` لا يرفعان العلم: منتصفاتٌ محايدة يجتازها نصفُ الأيام).

    ⚠️ **حدُّ صدقٍ إلزاميّ (يُقرأ قبل أي بناء):** عائلةُ «سلوكٌ يميّز المنفجر»
    فشلت **خمس مرّات مقيسة** على مجتمع الفارز الرئيسي (آخرها `T-RANKER3`) —
    هذي الطبقةُ **عرضٌ وترتيبُ انتباهٍ وحصادٌ أماميّ** على مجتمعٍ آخر (فئة
    الضغط)، **لا فلتر**: لا اسمَ يُسقَط بها (درسُ WETO)، وحكمُها يأتي من
    سجلّ الحصاد لا يُدَّعى سلفًا. تعذّرٌ ⇒ خمود (فاشلة-آمنة، لا ترمي)."""
    import Super_stock as S                                      # noqa: PLC0415
    out = {"vol_x": None, "score": 0, "rev": None,
           "ah_pct": ah_pct, "awake": False}
    # 🐞 التدهورُ **مكوّنًا مكوّنًا لا كلًّا** (أمسكه فحصُ PRD19 قبل الدفع):
    # الصياغةُ الأولى كانت ترجع مبكّرًا عند غياب عمود الحجم — **فتقتل قرينةَ
    # الافتر المستقلّةَ معه** (الكرتُ يطبع سطرَ الافتر والحصادُ يقول خامد =
    # عرضٌ يناقض سجلَّه). كلُّ قرينةٍ في حارسها.
    a1 = 0
    try:                       # ① الحجم/النشاط — آخر جلستين جلسةً جلسة، الأقوى
        h = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        c = df["Close"].values.astype(float)
        v = df["Volume"].values.astype(float)
        for cut in (None, -1):
            f = S.activity_features(h[:cut], lo[:cut], c[:cut], v[:cut])
            if f.get("vol_x") and (out["vol_x"] is None
                                   or f["vol_x"] > out["vol_x"]):
                out["vol_x"] = round(float(f["vol_x"]), 1)
            a1 = max(a1, int(f.get("a1") or 0))
            out["score"] = max(out["score"], int(f.get("act_score") or 0))
    except Exception:                                            # noqa: BLE001
        pass
    try:                       # ② الشمعة الانعكاسية (لا تحتاج الحجم أصلًا)
        o2 = df["Open"].values.astype(float)
        h2 = df["High"].values.astype(float)
        l2 = df["Low"].values.astype(float)
        c2 = df["Close"].values.astype(float)
        ohlc = [(float(o2[k]), float(h2[k]), float(l2[k]), float(c2[k]), 0.0)
                for k in range(max(0, len(c2) - 3), len(c2))]
        out["rev"] = S.reversal_candle(ohlc)
    except Exception:                                            # noqa: BLE001
        out["rev"] = None
    ah_hot = False
    try:
        if ah_pct is not None:
            ah_hot = abs(float(ah_pct)) >= float(
                S.CONFIG.get("PM_MOVE_PCT", 10))
    except Exception:                                            # noqa: BLE001
        ah_hot = False
    out["awake"] = bool(a1) or out["rev"] is not None or ah_hot
    return out


def wake_line(w: dict) -> str:
    """سطرُ الصحوة للكرت — يسمّي القرائنَ الحاضرة فقط (لا ادّعاءَ بلا شاهد)."""
    import Super_stock as S                                      # noqa: PLC0415
    sigs = []
    try:
        if w.get("vol_x") and float(w["vol_x"]) >= float(
                S.CONFIG.get("VOL_SPIKE_MULT", 5.0)):
            sigs.append(f"قفزة حجم ×{w['vol_x']}")
        if w.get("rev"):
            sigs.append(f"شمعة انعكاسية ({w['rev']})")
        if w.get("ah_pct") is not None and abs(float(w["ah_pct"])) >= float(
                S.CONFIG.get("PM_MOVE_PCT", 10)):
            sigs.append(f"حركة افتر {float(w['ah_pct']):+.1f}%")
    except Exception:                                            # noqa: BLE001
        return ""
    return ("   🔥 صحوة آخر جلستين: " + " · ".join(sigs)) if sigs else ""


def should_alert(entry: dict, today_iso: str) -> bool:
    """دِدوب: لا إعادة تنبيه لنفس السهم قبل REALERT_DAYS."""
    last = (entry or {}).get("last_alert")
    if not last:
        return True
    gap = _days_between(last, today_iso)
    return gap is None or gap >= REALERT_DAYS


# ──────────── الرسالة (بأسلوب التقرير الأسبوعي · بلا علامات مقارنة) ────────────

def _esc(t) -> str:
    """تهريبٌ أدنى للحقول الديناميكية (تلغرام `parse_mode=HTML`) — عرضٌ فقط.
    فيبقى العقدُ قائمًا: لا `<` ولا `>` خامّ يصل الرسالةَ فيكسرها."""
    return (str(t).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


def _card_sep() -> str:
    """فاصلُ الكروت = **فاصلُ التقرير الأسبوعي نفسُه حرفيًّا** (مصدرٌ واحد فلا
    يتفرّق الشكلان بعد اليوم). تعذّرُ الاستيراد ⇒ نفسُ الشرطات (فاشلٌ-آمن)."""
    try:
        import Super_stock as S                                  # noqa: PLC0415
        return S.DAILY_CARD_SEP
    except Exception:                                            # noqa: BLE001
        return "━" * 15


def _compact_line(r: dict) -> str:
    """سطرٌ مضغوطٌ لسهمٍ واحد (بقيّةُ الجاهزين · وقيدُ المتابعة) — نمطُ السطر
    الصغير في التقرير الأسبوعي: الرمزُ ثم الصغائرُ مفصولةً بنقاط."""
    p = r.get("read") or {}
    return (f"• <b>${_esc(r.get('symbol'))}</b> ${p.get('close')} · "
            f"هبوط {p.get('drop_pct')}% · قاع ${p.get('press_low')} · "
            f"حافظ {int(p.get('hold_sessions') or 0)} جلسة")


def _ready_card(i: int, r: dict) -> list:
    """كرتُ سهمٍ جاهز — **بترتيب كرت التقرير الأسبوعي حرفيًّا**: رأسٌ ⟵ الصغائرُ
    في سطر 💰 ⟵ السياق ⟵ 📥 الدخول والوقف ⟵ 🎯 الهدف ⟵ المستويات ⟵ 🔗 المصدر.
    كلُّ معلومةٍ مهمّة بسطرها (قاعدة العرض 2026-06-23) — والشرحُ المكرّر خرج للذيل."""
    p = r.get("read") or {}
    h = int(p.get("hold_sessions") or 0)
    seg = [f"{i}) 🗜️ <b>${_esc(r.get('symbol'))}</b> · 🟢 حافظ قاعه {h} جلسة",
           f"   💰 ${p.get('close')} · هبوط {p.get('drop_pct')}% من "
           f"${p.get('high_w')} · قاع الضغط ${p.get('press_low')}"]
    if float(p.get("runup_pct") or 0.0) >= 50.0:
        seg.append(f"   📈 ركض قبل الضغط {p['runup_pct']}% (نمط النموذج)")
    if r.get("prev_q"):
        seg.append(f"   🔁 كان مؤهلًا عند البوت @{_esc(r['prev_q'])}")
    plan = r.get("plan") or {}
    e = plan.get("entry")
    if e:
        ln = ("   📥 دخول (خطتنا المحفوظة): "
              + (f"{e[0]} - {e[1]}"
                 if isinstance(e, (list, tuple)) and len(e) == 2 else str(e)))
        if plan.get("stop"):
            ln += f"  ·  ⛔ وقف خسارة ${plan['stop']}"
        seg.append(ln)
    if plan.get("t1"):
        seg.append(f"   🎯 هدف أول: ${plan['t1']}")
    if p.get("tested_level"):
        seg.append(f"   📍 مستوى مُختبَر عند ${p['tested_level']}")
    _wl = wake_line(r.get("wake") or {})
    if _wl:                             # 🔥 قرائنُ الصحوة الحاضرة بأسمائها
        seg.append(_wl)
    seg.append(f"   🟣 الطلبات قرب القاع ${p.get('press_low')} · 🔴 الوقف تحته")
    if p.get("imp_head"):
        seg.append(f"   🕯️ الشمعة المهمة: ذيلها ${p.get('press_low')} · "
                   f"رأسها ${p['imp_head']}")
    seg.append(f"   🔗 المصدر: {_esc(r.get('src', '؟'))}")
    return seg


def build_alert(rows, session_iso: str) -> str:
    """يبني رسالة التنبيه **بأسلوب إشعار الأسهم الأسبوعي حرفيًّا** (أمرُ المالك
    2026-08-15 بعد أوّل تسليمٍ حيّ: «ارجع شكل الرسالة لأنها فوضى دسمة مرّة —
    خلّها بنفس أسلوب وطريقة إشعار الأسهم الأسبوعية بالضبط»).

    الشكلُ منقولٌ من `build_daily_message`: ترويسةٌ بعدّادين ⟵ عنوانُ قسمٍ
    بعدده ⟵ كروتٌ **مرقّمة** كلُّ معلومةٍ مهمّة فيها بسطرها والصغائرُ مجموعةٌ
    في سطر 💰 ⟵ فاصلُ شرطاتٍ بين كل سهمين (`DAILY_CARD_SEP` **نفسُه**) ⟵ ذيل.
    🔴 والعلّةُ التي شكا منها: **الشرحُ المكرّر في كل سهم** (الشمعة المهمة/
    النموذج) — نُقل إلى الذيل **مرّةً واحدة**، والسهمُ كان سطرًا واحدًا طويلًا
    مربوطًا بـ« — » فصار كرتًا مقروءًا.

    🥇 «اعتمد الحفظ» (أمر المالك 2026-08-14 بعد §⑬): قسمان — 🟢 **جاهز**
    (حافظ قاعه `READY_HOLD` جلسات فأكثر = الشريحة الموجبة المقيسة) بكروتٍ
    كاملة، و👀 **قيد المتابعة** (مضغوطٌ لم يحفظ بعد) بأسطرٍ مضغوطة — لا
    يُسقَط (درس WETO: انفجر من حفظ 0ج) لكنه يتميّز. **ولا قصَّ صامتًا:** ما
    فوق سقف الكروت يُعرَض أسطرًا مضغوطة ثم يُذكَر الباقي عددًا.
    🔒 وسومُ HTML **مقصورةٌ على `<b>`/`<i>`** (تلغرام `parse_mode=HTML` كما في
    التقرير الأسبوعي)، والحقولُ الديناميكية تمرّ بـ`_esc` — فلا `<`/`>` خامّ
    يكسر الرسالة (درس 2026-08-14)، **ولا علاماتِ مقارنةٍ إطلاقًا** (قاعدة
    العرض 2026-06-23). ألوانُ فيصل: 🟣 الطلبات (الدخول عند القاع) · 🔴 الوقف."""
    ready, watch = [], []
    for r in rows:
        h = int((r.get("read") or {}).get("hold_sessions") or 0)
        (ready if h >= READY_HOLD else watch).append(r)
    # 🔥 «صحوة آخر جلستين» (مسكة المالك 2026-08-15 «27 سهمًا وش أدخل فيه؟»):
    # الحافظُ **المتحرّك الآن** يتصدّر بكرتٍ كامل، والحافظُ الهادئ ينزل أسطرًا
    # مضغوطة — **ترتيبُ انتباهٍ لا فلتر** (لا اسمَ يُسقَط — درسُ WETO)، وصفرُ
    # صحوةٍ ⇒ الشكلُ السابق حرفيًّا (الجاهزون كلُّهم كروتًا حتى السقف).
    fire = [r for r in ready if (r.get("wake") or {}).get("awake")]
    quiet = [r for r in ready if not (r.get("wake") or {}).get("awake")]
    sep = _card_sep()
    lines = [f"🗜️📡 <b>رادار الضغط</b> — {session_iso}",
             (f"🔥 {len(fire)} يتحرّك الآن · " if fire else "")
             + f"🟢 {len(ready)} جاهز · 👀 {len(watch)} قيد المتابعة "
             "(نموذج فيصل: «اذا حافظ ع ادنى قاع طبق النموذج»)",
             ""]
    if fire:
        shown = fire[:ALERT_CAP]
        lines.append("🔥 <b>يتحرّك الآن — حافظٌ وعليه سلوكُ مضاربٍ في آخر "
                     f"جلستين</b> ({len(fire)})")
    else:
        shown = ready[:ALERT_CAP]
        if shown:
            lines.append(f"🟢 <b>جاهز — حافظ قاعه {READY_HOLD} جلسات فأكثر</b> "
                         f"({len(ready)})")
        else:
            lines.append(f"🟢 لا سهم حافظ قاعه {READY_HOLD} جلسات هذي الجلسة — "
                         f"{len(watch)} تحت المتابعة (يظهرون أدناه).")
    for i, r in enumerate(shown, 1):
        if i > 1:                       # فاصلُ الكروت (نفسُ التقرير الأسبوعي)
            lines += ["", sep, ""]
        lines += _ready_card(i, r)
    if fire:
        _rest = fire[len(shown):] + quiet
        _rest_title = (f"🟢 <b>جاهزون هادئون — حافظوا قاعهم بلا صحوةٍ بعد</b> "
                       f"({len(quiet)})")
        if len(fire) > len(shown):      # فائضُ النار يتقدّم بإعلانٍ لا صمت
            _rest_title = (f"🟢 <b>البقية</b> ({len(_rest)} — منهم "
                           f"{len(fire) - len(shown)} 🔥 فوق سقف الكروت)")
    else:
        _rest = ready[len(shown):]
        _rest_title = f"🟢 <b>باقي الجاهزين</b> ({len(_rest)}) — سطرٌ لكل سهم:"
    if _rest:
        lines += ["", _rest_title]
        for r in _rest[:ALERT_CAP * 2]:
            lines.append(_compact_line(r))
        if len(_rest) > ALERT_CAP * 2:
            lines.append(f"…و{len(_rest) - ALERT_CAP * 2} في سجل الحصاد "
                         "(لا قصَّ صامتًا).")
    if watch:
        lines += ["", f"👀 <b>قيد المتابعة — لم يحفظ قاعه {READY_HOLD} جلسات "
                      f"بعد</b> ({len(watch)})"]
        for r in watch[:ALERT_CAP * 2]:
            lines.append(_compact_line(r))
        if len(watch) > ALERT_CAP * 2:
            lines.append(f"…و{len(watch) - ALERT_CAP * 2} في السجل "
                         "(لا قصَّ صامتًا).")
    body = "\n".join(lines)
    lines += ["", sep, ""]
    if "🔥" in body:                    # شرحُ الصحوة مرّةً واحدة — وحدُّ صدقها معه
        lines.append("🔥 <b>الصحوة</b> = قفزةُ حجمٍ أو شمعةٌ انعكاسية أو حركةُ "
                     "افترٍ في آخر جلستين — ترتيبُ انتباهٍ قيد الإثبات الأمامي، "
                     "لا يُسقِط أحدًا ولا يضمن انفجارًا.")
    if "🕯️" in body:                    # شرحٌ مرّةً واحدة — لا في كل سهم
        lines.append("🕯️ <b>الشمعة المهمة</b> = شمعةُ صنع القاع: طلباتُ فيصل "
                     "داخل مداها، وكسرُ ذيلها بلا رجوعٍ يُفشل النموذج (درس NEXR).")
    if "🟣" in body:
        lines.append("🟣 <b>الطلبات</b> = منطقةُ الشراء عند القاع · 🔴 الوقف "
                     "تحتها (ألوان فيصل الموثّقة).")
    lines += ["⚠️ <i>عرضٌ وتنبيه قيد الإثبات الأمامي — ليست توصية. قراءةُ "
              "الضغط من الشموع اليومية، وقرينةُ الافتر وحدَها من الجلسة "
              "الممتدة عند توفّرها.</i>",
              f"📒 الحصاد: {len(rows)} قراءة سُجّلت هذي الجلسة."]
    return "\n".join("‏" + ln if ln else ln for ln in lines)


def _ledger_seen(path, session_iso) -> set:
    """رموزُ الجلسة المسجَّلةُ سلفًا في الحصاد — فيبقى **صفٌّ واحدٌ لكل سهمٍ في
    الجلسة** مهما تكرّر الإرسال (التشغيلُ اليدويّ لا يضاعف عيّنة القياس).
    تعذّرُ القراءة ⇒ مجموعةٌ فارغة (فاشلٌ-آمنٌ **مفتوح**: لا نُسقط حصادًا بسبب
    عطلِ قراءة — والتكرارُ يبقى قابلًا للكشف بالمفتاح، والفقدُ لا يُستعاد)."""
    seen = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    d = json.loads(ln)
                except Exception:                                # noqa: BLE001
                    continue
                if str(d.get("session")) == str(session_iso):
                    seen.add(str(d.get("symbol")))
    except FileNotFoundError:
        return seen
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ قراءة سجل الحصاد تعذّرت ({e}) — يُكتَب بلا فحص تكرار.")
        return set()
    return seen


def append_ledger(rows, session_iso: str, path=LEDGER_FILE) -> int:
    """يُلحق القراءات بسجل الحصاد — **بعد نجاح الإرسال حصرًا** (عقد «فُحص
    وسُلّم»). 🔒 وإلحاقٌ **مُتماثِلُ التكرار** (2026-08-15): الرمزُ المسجَّلُ
    لهذي الجلسة لا يُعاد — فإعادةُ الإرسال اليدويّ **لا تضاعف عيّنة الحصاد**
    (وهي عيّنةُ قياسٍ أمامية: التكرارُ يفسدها بصمت)."""
    seen = _ledger_seen(path, session_iso)
    n, dup = 0, 0
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for r in rows:
                if str(r["symbol"]) in seen:
                    dup += 1
                    continue
                _w = r.get("wake") or {}
                rec = {"session": session_iso, "symbol": r["symbol"],
                       "src": r.get("src"), "prev_q": r.get("prev_q"),
                       # 🔥 حقولُ الصحوة تُحصَد مع كل صفّ — فيصير سؤال «هل
                       # الصحوةُ تتنبّأ؟» قابلًا للقياس من السجل لا مُدَّعًى
                       "wake_vol_x": _w.get("vol_x"),
                       "wake_rev": _w.get("rev"),
                       "wake_ah_pct": _w.get("ah_pct"),
                       "wake_score": _w.get("score"),
                       "awake": bool(_w.get("awake")),
                       **r["read"]}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                seen.add(str(r["symbol"]))
                n += 1
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ سجل الحصاد لم يُكتب: {e}")
    if dup:
        _log(f"📒 الحصاد: {dup} رمزًا مسجَّلًا سلفًا لهذي الجلسة — لم يُكرَّر.")
    return n


# ─────────────────────────── المسار الرئيسي ───────────────────────────

def run(now_utc=None, fetch_hist=None, sender=None, state_path=STATE_FILE,
        ledger_path=LEDGER_FILE, saver=None) -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import split_hunter as H                                     # noqa: PLC0415
    force = os.environ.get("PRESS_RADAR_FORCE", "").strip() == "1"
    ok, session_date = H.session_gate(now_utc=now_utc)
    if force and not ok:
        import zoneinfo as _zi                                   # noqa: PLC0415
        _now = now_utc or _dt.datetime.now(_dt.timezone.utc)
        session_date = _now.astimezone(_zi.ZoneInfo("America/New_York")).date()
    elif not ok:
        _log("⏰ بوّابة التوقيت: الافتر لم يُغلق بعد — لا مسح (الكرون الثاني سيلتقط).")
        return 0
    session_iso = str(session_date)
    state = load_state(state_path)
    if state.get("last_session") == session_iso and not force:
        _log(f"🔁 دِدوب: جلسة {session_iso} فُحصت وسُلّمت — لا إعادة.")
        return 0
    wl = S.load_watchlist() or {}
    pool, cut = build_pool(wl, state, session_iso)
    if cut:
        _log(f"⚠️ بِركة الرادار قُصّت: {cut} رمزًا فوق السقف {POOL_CAP} (يُعلَن لا يُصمَت).")
    _log(f"📡 بِركة الرادار: {len(pool)} رمزًا (ارتداد/قائمة/مشطوب/متحرّك/ذاكرة).")
    fetch = fetch_hist or S.download_history
    hist = fetch(pool) or {}
    rows, failed = [], 0
    grid = {"V0": 0, "VA1": 0, "VA2": 0, "VA3": 0}
    for sym in pool:
        df = hist.get(sym)
        if df is None or getattr(df, "empty", True):
            failed += 1
            continue
        # 🥇 «وسّع» (2026-08-14): قراءةُ التنبيه صارت VA1 (نافذة `ALERT_W`=40 —
        # التقاط الكتالوج 29/29 والأفضل توقّعًا في §⑬). العدّاداتُ تبقى سجلًّا.
        r = press_read(df, w=ALERT_W)
        grid["V0"] += 1 if press_read(df) else 0
        grid["VA1"] += 1 if r else 0
        grid["VA2"] += 1 if press_read(df, band_pct=20.0) else 0
        grid["VA3"] += 1 if press_read(df, w=40, band_pct=20.0) else 0
        if not r:
            continue
        mem = state.get("symbols", {}).get(sym, {})
        # 🔓 التشغيلُ اليدويُّ يتخطّى **دِدوب السهم أيضًا** (2026-08-15، أمرُ
        # المالك «شغّله خلّه يوصلني الآن»): الـworkflow يَعِد صراحةً أن الزرّ
        # «يتخطّى بوّابة التوقيت **والدِدوب معًا**» — والكودُ كان يتخطّى دِدوبَ
        # الجلسة وحده، فيبقى دِدوبُ السهم (‏REALERT_DAYS=5) كاتمًا كلَّ مطابقٍ
        # نُبِّه أمس ⇒ **زرُّ المالك أخضرُ بصفر رسالة** = عينُ الصنف الذي كُتب
        # التعليقُ لمنعه. ⇒ الوعدُ يُنفَّذ في الكود. 🔒 والكرونُ لم يُمَسّ
        # (‏`force` صفرٌ فيه) والحصادُ صار متماثلَ التكرار فلا تتضاعف العيّنة.
        if not force and not should_alert(mem, session_iso):
            continue
        rows.append({"symbol": sym, "read": r,
                     "plan": mem.get("plan"), "src": mem.get("src", "؟")})
    # 🔁 تركيبة المالك: «مؤهلٌ سابقًا عند البوت؟» تُحسب للمطابقين فقط (قلّة
    # بعد الدِدوب) — فاشلة-آمنة: تعذّرها لا يمس التنبيه.
    for r in rows:
        try:
            _df = hist.get(r["symbol"])
            r["prev_q"] = (prev_qualified(r["symbol"], _df, "9999-12-31")
                           if _df is not None else None)
        except Exception:                                        # noqa: BLE001
            r["prev_q"] = None
    # 🔥 صحوةُ آخر جلستين (2026-08-15): تُحسب لكل مطابق من شموعه الموجودة
    # أصلًا (صفر نداء إضافي)، وحركةُ الافتر تُجلب **للحافظين وحدهم** (سقفُ
    # نداءات Polygon = عدد الجاهزين ≈ عشرات لا مئات) — فاشلة-آمنة: بلا مفتاح/
    # تعذّر ⇒ ah_pct=None والقراءةُ الباقية تعمل.
    for r in rows:
        ah_pct = None
        try:
            if int((r.get("read") or {}).get("hold_sessions") or 0) >= READY_HOLD:
                _ext = S.extended_last_price(r["symbol"], session_iso)
                _cl = float((r.get("read") or {}).get("close") or 0)
                if _ext and _cl > 0:
                    ah_pct = round((float(_ext) / _cl - 1.0) * 100.0, 1)
        except Exception:                                        # noqa: BLE001
            ah_pct = None
        try:
            r["wake"] = wake_read(hist.get(r["symbol"]), ah_pct=ah_pct)
        except Exception:                                        # noqa: BLE001
            r["wake"] = {}
    rows.sort(key=alert_rank)        # الأقرب لنمط WETO أولًا (تصحيح أول تشغيلة)
    _log(f"🩺 التغطية: فُحص {len(pool) - failed} · تعذّر {failed} · مطابق {len(rows)}.")
    _log(f"🧪 عدّادات §⑪-ج (كلفة التركيبات على البِركة — سجلّ فقط): "
         f"V0={grid['V0']} · VA1={grid['VA1']} · VA2={grid['VA2']} · "
         f"VA3={grid['VA3']} من {len(pool) - failed} مفحوصًا.")
    if rows:
        msg = build_alert(rows, session_iso)
        send = sender or S.send_telegram
        if not send(msg):
            _log("⛔ إرسال تلغرام فشل — لا ختم ولا سجل (الكرون الثاني يعيد).")
            return 1
        for r in rows:
            state.setdefault("symbols", {}).setdefault(r["symbol"], {})["last_alert"] = session_iso
        append_ledger(rows, session_iso, path=ledger_path)
    else:
        _log("📭 لا مطابق هذي الجلسة — صامتٌ عمدًا (قاعدة «الجاهز فقط»)، والتغطية أعلاه دليل الحياة.")
    state["last_session"] = session_iso
    if not save_state(state, state_path):
        _log("⚠️ حالة الرادار لم تُحفظ — الكرون الثاني قد يكرّر (تحذير لا صمت).")
    try:
        (saver or S.git_save)([state_path, ledger_path])
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ دفع حالة الرادار: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
