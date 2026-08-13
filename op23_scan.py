#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️📈 `T-OP23` — سلوكُ المضارب قبل الانفجار على 23 سنة (`op23_prereg.md`).

**الأمر:** «شغّل باكتيست على 23 سنة نستهدف الأسهم اللي انفجرت وتطابق شروط فيصل
فقط، ونحاول نطلع منها سلوك المضارب قبل الانفجار».

⚠️ **تصحيحُ إطارٍ يُقرأ أوّلًا (§⓪):** هذا **ليس** باكتيست `yfinance` القائم
(سقفُه ‏≈3 سنوات وكونُه ناجٍ) — هو **خطُّ أنابيب Polygon**: التاريخ من 2003
والكونُ **يشمل المشطوبين** ⇒ 🥇 أوّلُ دراسةٍ في المشروع **بلا انحياز بقاء**.

**المراحل (§①) — تُشغَّل مرحلةً مرحلة بأمر المالك:**
`discover` اكتشافُ الانفجارات (‏+100% فوق أدنى قاع 20 جلسة · مِرساةُ
`explosion_onset` **المصحَّحة بالاسم** · **وحارسُ التقسيم الوهميّ ±5 جلسات
بعدّادٍ مطبوع**) ⟶ `filter` «شروطُ فيصل فقط» = **`analyze_ticker` الإنتاجيّ
بالاسم** على الشريحة المنتهية **قبل** المِرساة ⟶ `trades` نوافذُ الصفقات
‏[−2،−1] وشاهدُ `crossover` ‏[−12،−11] ⟶ `report` الوصف.

**ومجموعةُ التمييز `G-NOEXP`:** مؤهَّلون بنفس الفلتر **لم يبلغوا +50% خلال 40
جلسة** — سحبٌ **حتميّ** بـ`sha256("سنة:رمز")` بنسبة 1:1 (نمطُ `control_panel`).

🔒 **خارج الإنتاج تمامًا** (لا يستورده `Super_stock`) · **والحكمُ ليس هنا**:
مخرجُ «مرشَّح تمييز» هو **اقتراحُ اختبارٍ أماميّ مسجَّل** لا قاعدة (§②).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys

RISE_PCT = 100.0                  # حدثُ الانفجار (§①-P1)
BASE_BARS = 20                    # نافذةُ القاع المرجعية
SPLIT_GUARD_BARS = 5              # ±5 جلسات حول الحدث (حارسُ التقسيم الوهميّ)
EVENT_OFFSETS = (-2, -1)
CTRL_OFFSETS = (-12, -11)
NOEXP_FWD = 40                    # نافذةُ «لم ينفجر» (جلسات)
NOEXP_RISE = 50.0
MIN_EVENTS_PER_ERA = 30           # أرضيةُ الحقبة (‏O8)
ERAS = (("2003-2012", 2003, 2012), ("2013-2019", 2013, 2019),
        ("2020-2026", 2020, 2026))
TRADE_CAP = 60_000


def _log(m: str) -> None:
    print(m, flush=True)


def era_of(year: int) -> str:
    """الحقبةُ — **تقسيمٌ إلزاميّ** (§②): البُنى الدقيقة تغيّرت، وما قبل 2013-12
    بلا كسور اللوت في شريط SIP ⇒ مقاييسُ الطبعات الصغيرة أضعفُ هناك (يُعلَن)."""
    for name, lo, hi in ERAS:
        if lo <= year <= hi:
            return name
    return "خارج المدى"


def control_panel(year: int, sym: str, rate: float = 1.0) -> bool:
    """سحبٌ **حتميّ** لمجموعة التمييز — `sha256("سنة:رمز")` (نمطُ `control_panel`
    المعتمَد): نفسُ المدخلات ⇒ نفسُ العيّنة، فالنتيجةُ قابلةٌ لإعادة الإنتاج
    حرفيًّا وبلا انتقاءٍ يدويّ."""
    h = hashlib.sha256(f"{year}:{sym}".encode()).hexdigest()
    return (int(h[:8], 16) % 10_000) < int(rate * 10_000)


def reverse_split_near(splits, anchor_iso: str, bars=SPLIT_GUARD_BARS) -> bool:
    """🔴 **حارسُ التقسيم الوهميّ (‏O2):** تقسيمٌ **عكسيّ** (نسبة < 1) داخل
    ‏±`bars` يومًا من الحدث ⇒ «الانفجار» صناعةُ تقسيمٍ لا حركةَ سوق.
    الدرسُ مقيس (`T-METHOD`: ‏192 من المرشّحين كانوا تقسيمات — أكثرَ من الباقين).
    **فاشلٌ-آمنٌ مُغلَق:** تعذّرُ القراءة ⇒ `True` (يُستبعَد ويُعَدّ) — فلا يدخل
    حدثٌ مشكوكٌ فيه العيّنةَ بصمت."""
    try:
        a = dt.date.fromisoformat(anchor_iso[:10])
    except Exception:                                             # noqa: BLE001
        return True
    try:
        for d, ratio in (splits or []):
            dd = dt.date.fromisoformat(str(d)[:10])
            if abs((dd - a).days) <= bars * 2 and float(ratio) < 1.0:
                return True
        return False
    except Exception:                                             # noqa: BLE001
        return True


def onset_anchor(high, low):
    """مِرساةُ الحدث — `explosion_index` ثم **`explosion_onset` المصحَّحة**
    (مقفولٌ نحويًّا `O3`: لا تُستعمل `explosion_index` وحدَها مِرساةً)."""
    import catalog_envelope as CE                                # noqa: PLC0415
    ix = CE.explosion_index(high, low, rise_pct=RISE_PCT, base_bars=BASE_BARS)
    if ix is None:
        return None
    return CE.explosion_onset(low, ix, base_bars=BASE_BARS)


def faisal_qualified(bars, anchor_idx) -> bool:
    """«شروطُ فيصل فقط» — **`analyze_ticker` الإنتاجيّ بالاسم** (‏O4) على شريحةٍ
    تنتهي **قبل** المِرساة ⇒ نفسُ تعريف فئة `BOXL`/الـ24 معمَّمًا على عقدين.
    **صفرُ نسخةٍ مبسَّطة** — الحكمُ حكمُ الفارز الحيّ بالحرف."""
    import Super_stock as S                                      # noqa: PLC0415
    try:
        sl = bars.iloc[:anchor_idx]
        if len(sl) < S.CONFIG["MIN_BARS"]:
            return False
        return S.analyze_ticker("OP23", sl) is not None
    except Exception:                                             # noqa: BLE001
        return False


def control_probe() -> bool:
    """‏`O5` شاهدُ ضبطٍ لكلّ حقبة: يومُ `AAPL` — «الصفرُ عطبُ أداةٍ حتى يُنفى»."""
    import preexp_probe as PP                                     # noqa: PLC0415
    d = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    r = PP.trades_layer("AAPL", d)
    ok = bool(r.get("fetch_ok")) and int(r.get("n_trades") or 0) > 1000
    _log(f"🧪 O5 شاهدُ الضبط AAPL@{d}: {r.get('n_trades')} ⇒ "
         + ("✅" if ok else "⛔ عطبُ أداةٍ محتمَل"))
    return ok


def cost_projection(n_syms: int, n_days: int, secs_per_day: float) -> str:
    """‏`O9` — **كلُّ إسقاطِ كلفةٍ يُطبَع معه معامِلُ التوسيع** (درسٌ مقيس:
    قسمُ الكلفة أسقط رقمَ عيّنةٍ كأنه يومٌ كامل فأخطأ ‏12×)."""
    tot = n_syms * n_days * secs_per_day
    return (f"⏱️ إسقاطُ الكلفة: {n_syms} رمزًا × {n_days} يومًا × "
            f"{secs_per_day:.2f}ث/يوم = {tot / 3600:.1f} ساعة "
            f"(**معامِلُ التوسيع مطبوعٌ صراحةً — لا إسقاطَ من عيّنةٍ بلا معامِل**)")


HISTORY_START = "2003-01-01"      # بدءُ تاريخ Polygon المُثبَت (‏flatfiles §)


def fetch_history(syms: list) -> dict:
    """📥 **جالبُ التاريخ الطويل** — `pit_history.polygon_daily` **بالاسم**
    (المنفذُ مُتحقَّقٌ سلفًا في `pit_prereg §P2`: تغطيةُ 90% ويخدم **المشطوبة**).

    🔴🔴 **ولماذا لا `download_history`** (إصلاحُ عيبٍ مقيسٍ بعد أوّل تشغيلة —
    ملحق `op23_prereg §⓪-أ`): جالبُ الإنتاج مسقوفٌ بـ`HISTORY_DAYS`=800 يومًا
    (‏≈2.2 سنة) ⇒ **كلُّ المِرساة تقع في 2026 بالضرورة** فطبع التوزيعُ
    ‏2003-2012=0 · 2013-2019=0 — أي أن «‏23 سنة» كانت **دعوًى لا تنفيذًا**.
    ⚠️ **وتعذّرُ الجلب يُعلَن بسببه المُسمّى** (‏`O7`: «الصفرُ عطبُ أداةٍ حتى
    يُنفى») · **وارتدادٌ صريحٌ إلى جالب الإنتاج عند غياب المفتاح** مع **وسمٍ
    ظاهر** أن المدى قصيرٌ فلا تُقرأ الحقبُ الفارغةُ نتيجةً."""
    import os as _os                                             # noqa: PLC0415
    key = (_os.environ.get("POLYGON_API_KEY") or "").strip()
    if not key:
        import Super_stock as S                                  # noqa: PLC0415
        _log("⚠️ **بلا `POLYGON_API_KEY`** ⇒ ارتدادٌ لجالب الإنتاج (سقفٌ "
             "‏≈2.2 سنة) — **الحقبُ القديمةُ ستُطبَع صفرًا لضيق المدى لا لغياب "
             "الأحداث**، فلا تُقرأ نتيجةً.")
        return S.download_history(syms)
    import pit_history as PH                                     # noqa: PLC0415
    end = dt.date.today().isoformat()
    out, bad = {}, []
    for i, sym in enumerate(syms, 1):
        df, why = PH.polygon_daily(sym, HISTORY_START, end, key)
        if df is None or len(df) < 60:
            bad.append(f"{sym}:{why}")
            continue
        out[sym] = df
        if i % 25 == 0:
            _log(f"   … {i}/{len(syms)} رمزًا")
    _log(f"📥 تاريخٌ من {HISTORY_START}: {len(out)}/{len(syms)} رمزًا"
         + (f" · **تعذّر {len(bad)}**: " + " · ".join(bad[:8]) if bad else ""))
    return out


def phase_discover(years) -> dict:
    """‏P1 — اكتشافُ الأحداث. **يُشغَّل أوّلًا وحدَه** فنرى `W1`/`W2` قبل حرق
    ساعاتِ الصفقات (§⑥-3)."""
    import Super_stock as S                                      # noqa: PLC0415
    syms = [x.strip().upper() for x in
            (os.environ.get("OP23_SYMS") or "").split(",") if x.strip()]
    if not syms:
        _log("⚠️ `OP23_SYMS` فارغ — وضعُ الاكتشاف يحتاج كونًا. "
             "(الكونُ الكامل يُبنى من `pit_universe`/الملفّات المجمَّعة "
             "بأمرٍ منفصل — لا يُختلَق هنا.)")
        return {"events": [], "raw": 0, "split_blocked": 0}
    raw, blocked, events = 0, 0, []
    hist = fetch_history(syms)
    for sym in syms:
        bars = hist.get(sym)
        if bars is None or len(bars) < BASE_BARS * 3:
            continue
        hi = bars["High"].values.astype(float)
        lo = bars["Low"].values.astype(float)
        k = onset_anchor(hi, lo)
        if k is None:
            continue
        raw += 1
        anchor = str(bars.index[k].date())
        try:
            sp = S._fetch_splits(sym)
            pairs = [(str(d)[:10], float(v)) for d, v in
                     (sp.items() if hasattr(sp, "items") else (sp or []))]
        except Exception:                                         # noqa: BLE001
            pairs = None
        if reverse_split_near(pairs, anchor):
            blocked += 1
            continue
        yr = int(anchor[:4])
        events.append({"symbol": sym, "anchor": anchor, "year": yr,
                       "era": era_of(yr),
                       "qualified": faisal_qualified(bars, k)})
    q = sum(1 for e in events if e["qualified"])
    _log(f"\n📊 P1: خامٌّ {raw} · **مستبعَدٌ بحارس التقسيم {blocked}** "
         f"({100.0 * blocked / raw:.1f}% — تنبّؤ `W2` ‏≥15%)" if raw else
         "\n📊 P1: صفرُ حدثٍ خام.")
    _log(f"📊 P2: مطابقٌ لشروط فيصل **{q}** من {len(events)} "
         f"(تنبّؤ `W1`: مئاتٌ على الأقلّ عبر العقدين)")
    for name, _lo, _hi in ERAS:
        n = sum(1 for e in events if e["era"] == name and e["qualified"])
        _log(f"   {name}: {n}"
             + ("" if n >= MIN_EVENTS_PER_ERA else
                f" ⚠️ **دون أرضية {MIN_EVENTS_PER_ERA} ⇒ «لا تكفي» وتُنشَر خامًا**"))
    # 🔴 حدُّ صدقٍ بنيويّ يُطبَع مع الحقب لا بعدها: `explosion_index` افتراضُها
    #    `pick="last"` ⇒ **مِرساةٌ واحدةٌ لكلّ رمز وهي الأحدث** ⇒ سقفُ الأحداث =
    #    عددُ الرموز، **وتوزيعُ الحقب أثرُ اختيار المِرساة لا شحُّ تاريخ** (والتاريخُ
    #    من 2003 فعلًا). ملءُ الحقب يلزمه مسحٌ متعدّدُ المراسي — تسجيلٌ جديد.
    _log(f"   ⚠️ **مِرساةٌ واحدة لكلّ رمز (‏`pick='last'`) ⇒ السقفُ {len(syms)} "
         "حدثًا** — فراغُ الحقب القديمة **أثرُ التصميم** لا نقصَ تاريخ.")
    return {"events": events, "raw": raw, "split_blocked": blocked}


def main() -> int:
    phase = (os.environ.get("OP23_PHASE") or "discover").strip()
    years = (os.environ.get("OP23_YEARS") or "").strip()
    _log(f"\n{'=' * 78}\n🕵️📈 T-OP23 — سلوكُ المضارب قبل الانفجار · الطور "
         f"{phase!r} · السنوات {years or 'كلّها'}\n{'=' * 78}")
    if phase not in ("discover", "filter", "trades", "report"):
        _log(f"⛔ طورٌ غيرُ معروف {phase!r} ⇒ خروج 8.")
        return 8
    if phase in ("trades", "report") and not os.environ.get(
            "POLYGON_API_KEY", "").strip():
        _log("⛔ `POLYGON_API_KEY` غائب ⇒ خروج 2.")
        return 2
    if phase in ("trades", "report") and not control_probe():
        _log("⛔ شاهدُ الضبط سقط ⇒ خروج 3 (لا رقمَ يُنشَر ولا يُفسَّر).")
        return 3
    res = phase_discover(years)
    out = os.environ.get("OP23_CSV") or "op23_events.jsonl"
    with open(out, "a", encoding="utf-8") as fh:
        for e in res["events"]:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    _log(f"💾 {len(res['events'])} حدثًا في {out} (تراكميّ · قابلٌ للاستئناف)")
    _log(cost_projection(max(1, len(res["events"])), len(EVENT_OFFSETS)
                         + len(CTRL_OFFSETS), 2.5))
    _log("\n⚠️ **تشخيصٌ لا حكم (§⑤):** العيّنةُ الحدثية مختارةٌ على النتيجة ⇒ "
         "التوصيفُ لا يُترجَم عائدًا · والصفقاتُ تشمل الجلسةَ الممتدّة · "
         "و«مرشَّحُ تمييز» مخرجُه **اقتراحُ اختبارٍ أماميّ مسجَّل** لا قاعدة.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
