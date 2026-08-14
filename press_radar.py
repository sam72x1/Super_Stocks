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


def should_alert(entry: dict, today_iso: str) -> bool:
    """دِدوب: لا إعادة تنبيه لنفس السهم قبل REALERT_DAYS."""
    last = (entry or {}).get("last_alert")
    if not last:
        return True
    gap = _days_between(last, today_iso)
    return gap is None or gap >= REALERT_DAYS


# ──────────────────── الرسالة (بلا علامات مقارنة ولا وسوم HTML) ────────────────────

def build_alert(rows, session_iso: str) -> str:
    """يبني رسالة التنبيه. **بلا `<` أو `>` أو `≥` أو `≤` إطلاقًا** (قاعدة العرض
    2026-06-23 + درسُ كسر HTML في تلغرام المُصلَح اليوم نفسه).

    🥇 «اعتمد الحفظ» (أمر المالك 2026-08-14 بعد §⑬): قسمان — 🟢 **جاهز**
    (حافظ قاعه `READY_HOLD` جلسات فأكثر = الشريحة الموجبة المقيسة) بكروتٍ
    كاملة، و👀 **قيد المتابعة** (مضغوطٌ لم يحفظ بعد) بأسطرٍ مضغوطة — لا
    يُسقَط (درس WETO: انفجر من حفظ 0ج) لكنه يتميّز. سقف ALERT_CAP لكل قسم
    والباقي يُذكَر عددًا (لا قصّ صامت). ألوانُ فيصل الموثّقة على الخطة:
    ‏🟣 الطلبات (الدخول عند الدعم) · 🔴 الوقف."""
    ready, watch = [], []
    for r in rows:
        h = int((r.get("read") or {}).get("hold_sessions") or 0)
        (ready if h >= READY_HOLD else watch).append(r)
    lines = [f"🗜️📡 رادار الضغط — جلسة {session_iso}",
             "ضغطُ مضاربٍ عند القاع (نموذج فيصل: «اذا حافظ ع ادنى قاع طبق النموذج»):",
             ""]
    shown = ready[:ALERT_CAP]
    if shown:
        lines.append(f"🟢 جاهز — حافظ قاعه {READY_HOLD} جلسات فأكثر "
                     "(الشريحة الموجبة المقيسة):")
    else:
        lines.append(f"لا جاهز هذي الجلسة (ما فيه مضغوطٌ حافظ قاعه "
                     f"{READY_HOLD} جلسات).")
    for r in shown:
        p = r["read"]
        seg = [f"• {r['symbol']} ${p['close']}",
               f"ضُغط من ${p['high_w']} (هبوط {p['drop_pct']}%) وجالسٌ عند قاعه ${p['press_low']}",
               f"حافظ قاعه {int(p.get('hold_sessions') or 0)} جلسة"]
        if float(p.get("runup_pct") or 0.0) >= 50.0:
            seg.append(f"ركض قبل الضغط {p['runup_pct']}% (نمط النموذج)")
        if r.get("prev_q"):
            seg.append(f"🔁 كان مؤهلًا عند البوت @{r['prev_q']} (تسلسل التركيبة الكامل)")
        if p.get("tested_level"):
            seg.append(f"مستوى مُختبَر عند ${p['tested_level']}")
        seg.append(f"🟣 الطلبات مقسّمة قرب القاع ${p['press_low']} · 🔴 الوقف تحته")
        if p.get("imp_head"):
            seg.append(f"🕯️ الشمعة المهمة: ذيلها ${p['press_low']} ورأسها "
                       f"${p['imp_head']} — طلبات فيصل داخل مداها، وكسرُ "
                       "الذيل بلا رجوع يُفشلها (درس NEXR)")
        plan = r.get("plan") or {}
        if plan.get("entry"):
            e = plan["entry"]
            t1 = plan.get("t1")
            seg.append("خطتنا المحفوظة: منطقة "
                       + (f"{e[0]}-{e[1]}" if isinstance(e, (list, tuple)) and len(e) == 2 else str(e))
                       + (f" · هدف أول {t1}" if t1 else ""))
        seg.append(f"المصدر: {r.get('src', '؟')}")
        lines.append(" — ".join(seg))
    if len(ready) > len(shown):
        lines.append(f"…و{len(ready) - len(shown)} جاهزون فوق سقف العرض (في سجل الحصاد كاملين).")
    if watch:
        lines += ["", f"👀 قيد المتابعة (مضغوطون لم يحفظوا {READY_HOLD} جلسات بعد):"]
        for r in watch[:ALERT_CAP]:
            p = r["read"]
            lines.append(f"• {r['symbol']} ${p['close']} — هبوط {p['drop_pct']}% "
                         f"· حفظ {int(p.get('hold_sessions') or 0)}ج · قاع ${p['press_low']}")
        if len(watch) > ALERT_CAP:
            lines.append(f"…و{len(watch) - ALERT_CAP} آخرون تحت المتابعة (في السجل كاملين).")
    lines += ["",
              "⚠️ عرضٌ وتنبيه قيد الإثبات الأمامي — ليس توصية. القراءة من الشموع "
              "اليومية (لا تشمل الافتر).",
              f"🧾 حصاد الرادار يتراكم في السجل ({len(rows)} قراءة هذي الجلسة)."]
    return "\n".join("‏" + ln if ln else ln for ln in lines)


def append_ledger(rows, session_iso: str, path=LEDGER_FILE) -> int:
    """يُلحق القراءات بسجل الحصاد — **بعد نجاح الإرسال حصرًا** (عقد «فُحص وسُلّم»)."""
    n = 0
    try:
        with open(path, "a", encoding="utf-8") as fh:
            for r in rows:
                rec = {"session": session_iso, "symbol": r["symbol"],
                       "src": r.get("src"), "prev_q": r.get("prev_q"),
                       **r["read"]}
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ سجل الحصاد لم يُكتب: {e}")
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
        if not should_alert(mem, session_iso):
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
