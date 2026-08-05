#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📐 ظرف الكاتالوج — «الحدّ الأدنى» مقيسًا من أسهم فيصل نفسها لا مخترَعًا.

**العقد كاملًا في `catalog_envelope_design.md` (مدفوعٌ قبل أوّل تشغيل).**
فكرة المالك: «سهم واحد فقط RSI 23 ⇒ **هذا هو الحدّ** — وقِسها على باقي النواقص».

**الطريقة:** لكل رمزٍ من الكاتالوج ⟶ نجد **يوم انفجاره** (‏D2) ⟶ نمشي **العشرين
جلسةً قبله** (‏D3) ⟶ في كل جلسة نُرخي **كلّ** البوّابات الصلبة وننادي
`analyze_ticker` **الإنتاجيّ نفسه** فيمضي للنهاية ويُرجع القيم (‏D4) ⟶ نبني الظرف
(‏D5) ⟶ **ونقيس كلفته على السوق الكامل** (‏D6 — وهو الحكم لا الالتقاط).

🔒 **بحث/قياس فقط:** لا يُستورَد في أي مسار إنتاج · لا يمسّ الجذور · يعيد `CONFIG`
في `finally` مهما حصل · ولا يقترح رقمًا — يُخرج **جدولًا** والقرار للمالك.

⚠️ **لقطةٌ مجمَّدة إلزامية** (كـ`hunter_six_check`): بلا `BT_FROZEN_PATH` يخرج بخطأ،
فلا تُقاس أرقامٌ على بياناتٍ تتحرّك تحت أقدامنا.
"""
from __future__ import annotations

import os
import sys

# ── D3: نافذة الشراء (مثبَّتة في ملفّ التصميم قبل أي رقم) ─────────────────────
ENTRY_WINDOW = 20
# حساسيةٌ تُنشَر ولا تُغيّر الحكم الأساسيّ (‏D3)
SENSITIVITY_WINDOWS = (10, 40)
# D2: تعريف الانفجار — أوّل +100% فوق أدنى قاعٍ في العشرين جلسةً السابقة
EXPLOSION_RISE_PCT = 100.0
EXPLOSION_BASE_BARS = 20
# 📌 تعديل ② (‏2026-08-05، بعد التشغيلة الأولى — **تصحيحُ صلاحية**): المِرساة صارت
#    **أحدثَ** انفجارٍ لا أقدمَه. السبب مُثبَتٌ بمعزلٍ عن الأرقام: أداتي أمسكت
#    ZCMD ‏2022-11-15 ولحظةُ فيصل الموثّقة **‏2026-07-02** · EHGO ‏2024-10-31 مقابل
#    **‏2026-05-22** ⇒ كنتُ أقيس ما قبل انفجاراتٍ لا علاقة لفيصل بها. وكاتالوجُه
#    مادّةٌ حديثة (‏2025-2026) ⇒ الأحدث هو المُوثَّق. `"first"` محفوظةٌ للمقارنة.
ANCHOR = "last"
# D6: عتبات الحكم على الكلفة (مُعلَنة سلفًا)
COST_WORTHLESS = 50.0
COST_USABLE = 5.0

# D1: كاتالوج فيصل — الواحد والثلاثون في `additions_audit.md §③` + الستة
CATALOG = [
    "ONCO", "KUST", "LABT", "ELAB", "INLF", "GWAV", "HTCR", "BNKK", "MWC",
    "SVRE", "MBRX", "WORX", "CANF", "APVO", "CMTL", "DXST", "TRUG", "EZRA",
    "ERNA", "CCHH", "EDBL", "KLXE", "LNAI", "PPCB", "XHLD", "YYAI", "HTZ",
    "JEM", "NUWE", "SPRC", "AZI", "DSY", "EHGO", "ZCMD", "JZ",
]

# ── D4: كلّ البوّابات الصلبة تُرخى دفعةً واحدة ────────────────────────────────
# 🔒 كلُّ مفتاحٍ هنا **موجودٌ في CONFIG** ومقفولٌ باختبار (لا اسمَ مخترَعًا).
RELAX_ALL = {
    "MIN_PRICE": 0.0,
    "MAX_DROP_PCT": 1e9,
    "MIN_DROP_FLOOR": -1e9,
    "PRIOR_SPIKE_FLOOR": -1e9,
    "BASE_RANGE_MAX_PCT": 1e9,
    "RECENT_RISE_BLOCK_PCT": 1e9,
    "MIN_DOLLAR_VOL": 0.0,
    "RSI_OS_HARD": 1e9,
    "RSI_NOW_HARD": 1e9,
    "WATCH_MAX_FAILS": 999,
    "NEAR_PCT": 0.0,
    "SCORE_MIN": 0,
    "MIN_RR_T1": -1e9,
}

# ── D5: المعايير واتّجاه بوّابة كلٍّ منها ─────────────────────────────────────
#   "lo"   = البوّابة حدٌّ أدنى  ⇒ حافّة الظرف **أصغر** قيمةٍ لوحظت
#   "hi"   = البوّابة سقف       ⇒ حافّة الظرف **أكبر** قيمةٍ لوحظت
#   "both" = أرضيةٌ وسقف        ⇒ [أصغر · أكبر]
CRITERIA = [
    ("price",       "lo",   "M1 السعر",              "MIN_PRICE"),
    ("drop_pct",    "both", "M2 الهبوط من قمة 52أ",   "MIN_DROP_FLOOR|MAX_DROP_PCT"),
    ("best_spike",  "lo",   "M3 الانفجار السابق",     "PRIOR_SPIKE_FLOOR"),
    ("base_range",  "hi",   "M4 عرض القاعدة",         "BASE_RANGE_MAX_PCT"),
    ("dollar_vol",  "lo",   "M5 السيولة الدولارية",   "MIN_DOLLAR_VOL"),
    ("rsi_min",     "hi",   "RSI قاعُه",              "RSI_OS_HARD"),
    ("rsi_now",     "hi",   "RSI الآن",               "RSI_NOW_HARD"),
    ("n_soft",      "hi",   "عدد النواقص",            "WATCH_MAX_FAILS"),
    ("readiness",   "lo",   "الجاهزية",               "NEAR_PCT"),
    ("score",       "lo",   "النقاط",                 "SCORE_MIN"),
    ("rr",          "lo",   "العائد/المخاطرة",        "MIN_RR_T1"),
]


# ──────────────────────────────────────────────────────────────────────────────
# دوالّ نقيّة (قابلة للاختبار بلا شبكة)
# ──────────────────────────────────────────────────────────────────────────────
def explosion_index(high, low, rise_pct=EXPLOSION_RISE_PCT,
                    base_bars=EXPLOSION_BASE_BARS, pick=None):
    """🎯 D2: فهرسُ جلسةٍ يبلغ فيها `high` نسبة `rise_pct`% فوق **أدنى `low`** في
    `base_bars` جلسةً **سابقة**. يرجّع `None` إن لم يقع.

    `pick="last"` (الافتراض · **تعديل ②**) ⇒ **أحدثُ** انفجار — لأن كاتالوج فيصل
    مادّةٌ حديثة، والأقدمُ يُمسك حدثًا لا علاقة له به.
    `pick="first"` ⇒ أقدمُه (محفوظةٌ للمقارنة والاختبار).

    🔒 **بلا نظرٍ مستقبليّ داخل النافذة**: القاعُ من الجلسات **قبل** الجلسة
    المفحوصة حصرًا (‏`i-base_bars … i-1`) — والانفجار نفسه حدثٌ نستعمله مرساةً
    ثم **نقيس ما قبله فقط** (‏D3 تستبعد يومه صراحةً)."""
    n = len(high)
    if n <= base_bars:
        return None
    order = (range(base_bars, n) if (pick or ANCHOR) == "first"
             else range(n - 1, base_bars - 1, -1))
    for i in order:
        base = min(low[i - base_bars:i])
        if base <= 0:
            continue
        if (high[i] / base - 1.0) * 100.0 >= rise_pct:
            return i
    return None


def envelope_edge(values, direction, pct=100.0):
    """📐 D5: حافّة الظرف لقيمٍ ملحوظة.

    `pct=100` ⇒ يستوعب الكلّ (فكرة المالك حرفيًّا) · `pct=90` ⇒ يُسقط أشدّ 10%
    تطرّفًا. يرجّع `None` لقائمةٍ فارغة، و`(lo, hi)` لـ`both`.

    🔒 **الحصّة تُقتطع من الطرف المتطرّف وحده** — فـ`lo` تُسقط الأصغرَ و`hi`
    تُسقط الأكبر؛ ولو عُكس لصار الظرف **أضيق** من الكاتالوج نفسه = نقضٌ لغرضه."""
    vals = sorted(float(v) for v in values
                  if v is not None and float(v) == float(v))
    if not vals:
        return None
    n = len(vals)
    if pct >= 100.0:
        keep_lo, keep_hi = vals[0], vals[-1]
    else:
        drop = int(n * (100.0 - pct) / 100.0)
        keep_lo = vals[min(drop, n - 1)]
        keep_hi = vals[max(n - 1 - drop, 0)]
    if direction == "lo":
        return keep_lo
    if direction == "hi":
        return keep_hi
    return (keep_lo, keep_hi)


def inside_envelope(row, env):
    """✅ هل قيمُ جلسةٍ داخل الظرف؟ يُستعمل لقياس **الكلفة** (‏D6) ولشاهد الضبط.

    🔒 **قيمةٌ مفقودة تمرّ بفائدة الشك** — نفس قاعدة الفارز الحيّة (مجهول ≠ رفض)،
    فلا يبدو الظرف أضيقَ ممّا هو بسبب عطلِ جلبٍ."""
    for key, direction, _, _ in CRITERIA:
        edge = env.get(key)
        if edge is None:
            continue
        v = row.get(key)
        if v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if v != v:
            continue
        if direction == "lo" and v < edge:
            return False
        if direction == "hi" and v > edge:
            return False
        if direction == "both" and not (edge[0] <= v <= edge[1]):
            return False
    return True


def cost_verdict(per_day, worthless=COST_WORTHLESS, usable=COST_USABLE):
    """⚖️ D6: الحكم من عدد المطابقين في اليوم — **العتبات مُعلَنة قبل الأرقام**."""
    if per_day is None:
        return "لا حكم (لم تُقَس)"
    if per_day > worthless:
        # 📌 تعديل ① (المالك، قبل أيّ رقم): العدد **لا يُسقط** الظرف — «ممكن تزيد
        #    الأسهم لكن على الأقل بتكون مشابهة لمنفجرين». فينتقل السؤال للتسليم.
        return (f"🟠 يلزمه مُرتِّبٌ مُثبَت — {per_day:.1f} مطابق/يوم "
                f"(فوق {worthless:.0f}؛ والسعة 15 والمُرتِّب «غير حاسم»)")
    if per_day >= usable:
        return f"🟡 صالح بشرط مُرتِّب — {per_day:.1f} مطابق/يوم"
    return f"🟢 قابل للتنفيذ — {per_day:.1f} مطابق/يوم (تحت {usable:.0f})"


# ──────────────────────────────────────────────────────────────────────────────
# قراءة القيم من `analyze_ticker` الإنتاجيّ (‏D4)
# ──────────────────────────────────────────────────────────────────────────────
def _rsi_bottom_from_gates(res):
    """يستخرج «قاع RSI» من `gates_status` (الحقل الوحيد الذي يحمله بالمُخرَج).

    🔒 فاشلة-آمنة: أي تغيّرٍ في نصّ المفتاح ⇒ `None` ⇒ المعيار يُعلَن **غير مقيس**
    بدل أن يُخمَّن رقمٌ — وهو الفرق بين «لا نعرف» و«كذبة»."""
    try:
        for k, (_ok, txt) in (res.get("gates_status") or {}).items():
            if "RSI" in k and "تشبع" in k:
                return float(str(txt).replace("قاع", "").strip())
    except Exception:                                            # noqa: BLE001
        return None
    return None


def measure_session(S, sym, df):
    """📏 قيمُ كلّ المعايير لجلسةٍ واحدة — بإرخاء كلّ البوّابات (‏D4).

    يرجّع `dict` أو `None` إن سقط `analyze_ticker` لسببٍ بنيويّ (بياناتٌ ناقصة)."""
    saved = {k: S.CONFIG.get(k) for k in RELAX_ALL}
    try:
        S.CONFIG.update(RELAX_ALL)
        res = S.analyze_ticker(sym, df)
    except Exception:                                            # noqa: BLE001
        return None
    finally:
        for k, v in saved.items():
            if v is None:
                S.CONFIG.pop(k, None)
            else:
                S.CONFIG[k] = v
    if not res:
        return None
    return {
        "price": res.get("price"),
        "drop_pct": res.get("drop_pct"),
        "best_spike": res.get("best_spike"),
        "base_range": res.get("base_range"),
        "dollar_vol": res.get("dollar_vol"),
        "rsi_min": _rsi_bottom_from_gates(res),
        "rsi_now": res.get("rsi"),
        "n_soft": len(res.get("soft_fails") or []),
        "readiness": res.get("readiness"),
        "score": res.get("score"),
        "rr": res.get("rr"),
    }


def walk_symbol(S, sym, df, window=ENTRY_WINDOW):
    """🚶 يمشي نافذة الشراء لرمزٍ ويرجّع `(صفوف، تشخيص)`.

    🔒 **يوم الانفجار مستبعَدٌ صراحةً** (‏D3) — الشريحة تنتهي عند `idx` غير
    الشاملة، فأقصى جلسةٍ مقيسة هي `idx-1`."""
    try:
        hi = df["High"].values
        lo = df["Low"].values
    except Exception:                                            # noqa: BLE001
        return [], "بيانات غير صالحة"
    idx = explosion_index(hi, lo)
    if idx is None:
        return [], f"لم يقع انفجار +{EXPLOSION_RISE_PCT:.0f}% في المدى"
    start = max(0, idx - window)
    if idx - start < 3:
        return [], "نافذة الشراء أقصر من ثلاث جلسات"
    rows = []
    for j in range(start, idx):            # ← `idx` مستبعَد: لا نظر مستقبليّ
        sl = df.iloc[:j + 1]
        if len(sl) < 60:
            continue
        m = measure_session(S, sym, sl)
        if m:
            m["symbol"] = sym
            m["date"] = str(df.index[j].date())
            rows.append(m)
    if not rows:
        return [], f"انفجارُه {df.index[idx].date()} لكن لا جلسة قابلة للقياس"
    return rows, f"انفجر {df.index[idx].date()} · قِيست {len(rows)} جلسة"


def build_envelope(rows, pct=100.0):
    """📐 يبني الظرف من الصفوف المقيسة (‏D5)."""
    env = {}
    for key, direction, _, _ in CRITERIA:
        env[key] = envelope_edge([r.get(key) for r in rows], direction, pct)
    return env


# ──────────────────────────────────────────────────────────────────────────────
def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, tuple):
        return f"[{_fmt(v[0])} · {_fmt(v[1])}]"
    return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}"


def _print_envelope(S, env90, env100, cur):
    S.log("")
    S.log("═══ 📐 جدول الظرف — الحدّ المقيس من الكاتالوج مقابل حدّنا الحاليّ ═══")
    S.log(f"{'المعيار':<26}{'حدّنا':>14}{'ظرف P100':>20}{'ظرف P90':>20}   الحكم")
    for key, direction, label, cfg_key in CRITERIA:
        e100, e90 = env100.get(key), env90.get(key)
        now = " | ".join(_fmt(cur.get(k)) for k in cfg_key.split("|"))
        verdict = "—"
        if e100 is not None and cur.get(cfg_key.split("|")[0]) is not None:
            try:
                if direction == "lo":
                    verdict = ("🔴 حدُّنا أضيق" if cur[cfg_key] > e100
                               else "✅ حدُّنا يستوعبه")
                elif direction == "hi":
                    verdict = ("🔴 حدُّنا أضيق" if cur[cfg_key] < e100
                               else "✅ حدُّنا يستوعبه")
                else:
                    f_key, c_key = cfg_key.split("|")
                    verdict = ("🔴 حدُّنا أضيق"
                               if (cur[f_key] > e100[0] or cur[c_key] < e100[1])
                               else "✅ حدُّنا يستوعبه")
            except Exception:                                    # noqa: BLE001
                verdict = "—"
        S.log(f"{label:<26}{now:>14}{_fmt(e100):>20}{_fmt(e90):>20}   {verdict}")


def run():
    import Super_stock as S

    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        S.log("⛔ ظرف الكاتالوج: `BT_FROZEN_PATH` إلزاميّ — لا قياسَ على بياناتٍ حيّة.")
        return 2
    hist, _splits, asof = S.load_frozen_dataset(path)
    if not hist:
        S.log(f"⛔ ظرف الكاتالوج: تعذّر تحميل اللقطة {path}.")
        return 2
    S.log(f"📐 ظرف الكاتالوج — لقطة as-of {asof} · {len(hist)} رمزًا بالكون.")
    S.log(f"   العقد: catalog_envelope_design.md · نافذة {ENTRY_WINDOW} جلسة "
          f"· انفجار +{EXPLOSION_RISE_PCT:.0f}%")

    syms = [s.strip().upper() for s in
            os.environ.get("ENV_SYMBOLS", "").split(",") if s.strip()] or CATALOG

    # ── ① نمشي الكاتالوج ────────────────────────────────────────────────────
    rows, found, missing = [], [], []
    for sym in syms:
        df = hist.get(sym)
        if df is None or len(df) < 60:
            missing.append((sym, "غير موجود باللقطة أو تاريخُه أقصر من 60 جلسة"))
            continue
        r, why = walk_symbol(S, sym, df)
        S.log(f"   {'✅' if r else '⚪️'} {sym:<6} {why}")
        if r:
            rows.extend(r)
            found.append(sym)
        else:
            missing.append((sym, why))

    S.log("")
    S.log(f"📊 المجموعة A (منفجرون): {len(found)} رمزًا · {len(rows)} جلسة مقيسة")
    S.log(f"📊 المجموعة X (مستبعَدون): {len(missing)} — وتُعلَن كلُّها:")
    for sym, why in missing:
        S.log(f"      ⚪️ {sym}: {why}")
    if not rows:
        S.log("⛔ لا جلسةَ مقيسة — لا ظرف. (وهذي نتيجةٌ تُنشَر لا تُخفى.)")
        return 1

    env100 = build_envelope(rows, 100.0)
    env90 = build_envelope(rows, 90.0)
    _print_envelope(S, env90, env100, S.CONFIG)

    # ── 🎯 التقاطُ الكاتالوج — رقمٌ **حقيقيّ لـ`P90` وحده** ───────────────────
    # `P100` يلتقط 100% **بالبناء** (لا معلومة فيه)، أمّا `P90` فيُسقط أشدّ 10%
    # تطرّفًا **لكل معيارٍ على حدة** ⇒ التقاطُه المشترك مجهولٌ حتى يُقاس. وهو
    # نصفُ المعادلة: التقاطٌ عالٍ بكلفةٍ منخفضة = إثراءٌ حقيقيّ · والعكس بالعكس.
    S.log("")
    S.log("═══ 🎯 التقاط الكاتالوج (النصف الثاني من المعادلة) ═══")
    for nm, e in (("P100", env100), ("P90", env90)):
        insid = [r for r in rows if inside_envelope(r, e)]
        syms_in = {r["symbol"] for r in insid}
        S.log(f"   ── ظرف {nm}: {len(insid)} من {len(rows)} جلسة "
              f"({100.0 * len(insid) / max(1, len(rows)):.1f}%) · "
              f"و{len(syms_in)} من {len(found)} رمزًا "
              f"({100.0 * len(syms_in) / max(1, len(found)):.1f}%)")
        miss = sorted(set(found) - syms_in)
        if miss:
            S.log(f"      ⚪️ لم يُلتقَط ولا جلسةً: {' · '.join(miss)}")

    # ── 🔬 الالتقاط **خارج العيّنة** (‏leave-one-out) — الحكم الحقيقيّ ─────────
    # الالتقاط أعلاه **داخل العيّنة**: الظرف مُفصَّلٌ على هؤلاء الرموز أنفسهم.
    # هنا نبني الظرف من **الثلاثين الآخرين** ونسأل: هل يلتقط المتروك؟ ⇒ هذا وحده
    # يفرّق «الظرف يعمّم» عن «الظرف يحفظ». والدرس مدوَّنٌ عندنا: انهيار «رابط
    # Technology 2025» جاء من غياب `leave-one-out` بالضبط.
    S.log("")
    S.log("═══ 🔬 الالتقاط خارج العيّنة (‏leave-one-out) — يفرّق التعميم عن الحفظ ═══")
    for nm, pct in (("P100", 100.0), ("P90", 90.0)):
        loo_hit, loo_miss = [], []
        for sym in found:
            others = [r for r in rows if r["symbol"] != sym]
            mine = [r for r in rows if r["symbol"] == sym]
            if not others or not mine:
                continue
            e = build_envelope(others, pct)
            (loo_hit if any(inside_envelope(r, e) for r in mine)
             else loo_miss).append(sym)
        tot = len(loo_hit) + len(loo_miss)
        S.log(f"   ── ظرف {nm}: {len(loo_hit)} من {tot} رمزًا "
              f"({100.0 * len(loo_hit) / max(1, tot):.1f}%) يُلتقَط **وهو خارج**")
        if loo_miss:
            S.log(f"      ⚪️ سقط خارج العيّنة: {' · '.join(sorted(loo_miss))}")

    # ── ② حساسية النافذة (‏D3 — تُنشَر ولا تغيّر الحكم) ──────────────────────
    for w in SENSITIVITY_WINDOWS:
        alt = []
        for sym in found:
            r, _ = walk_symbol(S, sym, hist[sym], window=w)
            alt.extend(r)
        if alt:
            e = build_envelope(alt, 100.0)
            S.log(f"   🔎 حساسية نافذة {w:>2}ج: "
                  + " · ".join(f"{k}={_fmt(e[k])}" for k, _, _, _ in CRITERIA[:5]))

    # ── ③ 🔴 الكلفة على السوق الكامل — وهي الحكم (‏D6) ───────────────────────
    S.log("")
    S.log("═══ 🔴 الكلفة — الحكم الحقيقيّ (الالتقاط وحده صفرُ معلومة) ═══")
    cat = set(syms)
    universe = [s for s in hist if s not in cat]
    cap = int(os.environ.get("ENV_COST_CAP", "600"))
    probe_days = int(os.environ.get("ENV_COST_DAYS", "5"))
    # 🔴 **الظرفان يُقاسان في تمريرةٍ واحدة** — كان `P100` وحده يُقاس، و`P90` هو
    #    المُرشَّح العمليّ المُعلَن في `D5` ⇒ قياسُ أحدهما وترك الآخر ثغرةٌ في الأداة.
    envs = {"P100": env100, "P90": env90}
    hits = {k: 0 for k in envs}
    ctrl = {k: 0 for k in envs}
    tested = 0
    for sym in universe[:cap]:
        df = hist.get(sym)
        if df is None or len(df) < 60:
            continue
        tested += 1
        seen = {k: False for k in envs}
        for back in range(1, probe_days + 1):
            sl = df.iloc[:len(df) - back + 1]
            if len(sl) < 60:
                continue
            m = measure_session(S, sym, sl)
            if not m:
                continue
            for k, e in envs.items():
                if inside_envelope(m, e):
                    hits[k] += 1
                    seen[k] = True
        for k in envs:
            if seen[k]:
                ctrl[k] += 1
    S.log(f"   فُحِص {tested} رمزًا × {probe_days} جلسات (سقف {cap} من "
          f"{len(universe)} خارج الكاتالوج)")
    for k in ("P100", "P90"):
        per_day = (hits[k] / probe_days) if probe_days else None
        scaled = ((per_day * len(universe) / max(1, tested))
                  if per_day is not None else None)
        S.log(f"   ── ظرف {k}: مطابقات {hits[k]} · رموزٌ مطابقة {ctrl[k]} "
              f"⇒ {per_day:.1f}/يوم بالعيّنة · ≈{scaled:.0f} على الكون")
        S.log(f"      ⚖️ {cost_verdict(scaled)}")
        if tested:
            S.log(f"      🎯 التمييز: {100.0 * ctrl[k] / tested:.1f}% من شاهد "
                  f"الضبط يستوعبه — وكلَّما اقترب من 100% ضعُف التمييز.")

    S.log("")
    S.log("⚠️ حدود صدقٍ قائمة: انحياز بقاء · تشويه تقسيمات · بلا افتر · n=31 "
          "على 11 معيارًا · والكاتالوج اختيارٌ لاحقٌ للحدث ⇒ تشخيصٌ لا معدَّل.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
