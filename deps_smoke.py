# -*- coding: utf-8 -*-
"""
==========================================================
🧪 فحص دخان حيّ للاعتماديات (Deps Smoke) — أداة مستقلة
==========================================================
تسدّ فجوة موثّقة: **سويّة `test_bot.py` تعمل بلا إنترنت بتصميمها** (كل الجالبات محقونة)
⇒ كسرُ `yfinance` **لا يُسقط أي اختبار**، فتبقى `tests.yml` خضراء بينما الإنتاج يقرأ
صفر بيانات. حراس التغطية تمنع الضرر لكنها **لا تشخّص السبب** — يرى المالك «تغطية
ضعيفة» يوميًّا بلا معرفة أنها ترقية مكتبة.

هذا الجوب هو **الكاشف الوحيد**: يفحص **العقود التي يعتمدها البوت فعلًا** لا مجرّد
«هل تُستورَد المكتبة»:
  1) `get_universe()` يرجّع كونًا معتبرًا       (كسر nasdaqtrader/الفلترة)
  2) `download_history()` بالشكل والأعمدة والطول (كسر `yf.download`/`group_by="ticker"`)
  3) `Ticker().info` فيه حقول الشركة            (كسر `.info` الذي يعتمده `_fetch_info`/M14)
  4) آخر شمعة ليست بائتة                        (بيانات متوقّفة)

**🔒 عرض/تشخيص فقط:** لا يستورد ولا ينادي أي دالّة تكتب حالة (لا `git_save` ولا
`save_watchlist` ولا `_atomic_write_json` ولا `record_*`) · لا يقرأ `weekly_watchlist.json`
· لا يلمس `POLYGON_API_KEY` · لا يطبع أي سرّ. الرموز ثابتة هنا.
الخروج **غير صفري عند أي سقوط** فتظهر الوظيفة حمراء حتى لو تعذّر تلغرام.

التشغيل: `python deps_smoke.py`   (workflow: `deps_smoke.yml` — يدوي + أسبوعي)
"""
import datetime as dt
import sys

try:
    import Super_stock as bot
except ImportError:                        # pragma: no cover
    import super_stock as bot

_SYMS = ["AAPL", "MSFT", "GEOS"]           # سائلان دائمان + ميكروكاب (يشبه كون البوت)
_STALE_MAX_DAYS = 7                        # آخر شمعة أقدم من هذا = بيانات متوقّفة


def _versions():
    """أسطر نسخ المكتبات الأربع (تشخيص — لا سرّ فيها)."""
    out = []
    for name in ("yfinance", "pandas", "numpy", "requests"):
        try:
            mod = __import__(name)
            out.append(f"{name} {getattr(mod, '__version__', '؟')}")
        except Exception as e:             # noqa: BLE001
            out.append(f"{name} ❌ ({type(e).__name__})")
    return out


def _check_universe():
    uni = bot.get_universe()
    if not uni or len(uni) < 1000:
        return (False, f"كون ناسداك رجع {len(uni or [])} رمزًا (المتوقّع بالآلاف) — "
                       "كسر مصدر الرموز أو الفلترة")
    return (True, f"{len(uni):,} رمزًا بعد الفلترة")


def _check_history():
    hist = bot.download_history(_SYMS)
    if not hist or len(hist) < 2:
        return (False, f"تحميل {len(_SYMS)} رموز رجع {len(hist or {})} — "
                       "كسر شكل yf.download أو خنق تامّ")
    need = ("Open", "High", "Low", "Close", "Volume")
    for sym, df in hist.items():
        miss = [c for c in need if c not in df.columns]
        if miss:
            return (False, f"{sym}: أعمدة ناقصة {miss} — تغيّر شكل المُخرَج")
        if len(df) < bot.CONFIG["MIN_BARS"]:
            return (False, f"{sym}: {len(df)} شمعة فقط (الحدّ {bot.CONFIG['MIN_BARS']})")
    return (True, f"{len(hist)}/{len(_SYMS)} رموز · الأعمدة والطول سليمة")


def _check_info():
    if bot.yf is None:
        return (False, "yfinance غير متاحة")
    info = bot.yf.Ticker("AAPL").info or {}
    keys = [k for k in ("sector", "country", "floatShares", "sharesOutstanding")
            if info.get(k) is not None]
    if not keys:
        return (False, "Ticker().info بلا أي حقل شركة — كسر المسار الذي يعتمده "
                       "_fetch_info وبوّابة الفلوت M14")
    return (True, "حقول متاحة: " + "، ".join(keys))


def _check_fresh():
    hist = bot.download_history(["AAPL"])
    df = (hist or {}).get("AAPL")
    if df is None or len(df) == 0:
        return (False, "تعذّر تحميل AAPL لفحص الطزاجة")
    last = df.index[-1].date()
    age = (dt.date.today() - last).days
    if age > _STALE_MAX_DAYS:
        return (False, f"آخر شمعة {last} — عمرها {age} يومًا (بيانات متوقّفة)")
    return (True, f"آخر شمعة {last} (عمرها {age} يومًا)")


def main():
    checks = [("كون ناسداك", _check_universe),
              ("تحميل الشموع (شكل/أعمدة/طول)", _check_history),
              ("Ticker().info (حقول الشركة)", _check_info),
              ("طزاجة آخر شمعة", _check_fresh)]
    lines = [f"🧪 <b>فحص دخان الاعتماديات</b> · {dt.date.today().isoformat()}", ""]
    ok_all = True
    results = []
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:             # noqa: BLE001
            ok, detail = False, f"استثناء: {type(e).__name__}: {e}"
        ok_all = ok_all and ok
        results.append((name, ok, detail))
    lines.insert(1, "✅ <b>كل العقود سليمة</b>" if ok_all
                 else "❌ <b>عقدٌ مكسور — الإنتاج سيقرأ بيانات ناقصة بصمت</b>")
    for name, ok, detail in results:
        lines.append(f"{'✅' if ok else '❌'} {name}: {bot.esc(str(detail))[:300]}")
    lines.append("")
    lines.append("📦 " + " · ".join(_versions()))
    if not ok_all:
        lines.append("")
        lines.append("ℹ️ سويّة الاختبارات تعمل بلا إنترنت فلا تكشف هذا — "
                     "راجع requirements.txt وبروتوكول الترقية فيه.")
    msg = "\n".join(lines)
    bot.log(msg)                            # السجلّ أولًا (يبقى حتى لو تعذّر تلغرام)
    try:
        bot.send_telegram(msg + "\n\n" + bot.FOOTER)
    except Exception as e:                  # noqa: BLE001
        bot.log(f"⚠️ إرسال فحص الدخان: {type(e).__name__}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
