#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 صيّاد «النهج العلمي» (فيصل) — **أداة مستقلّة** عن فارز الارتكاز وعن صيّاد المقسّم.

قرار المالك 2026-08-01: «خلّها أداة مستقلّة … نفس الطريقة اللي قدرت تبني فيها أداة
الصيّاد». فبُنيت على **نمط `split_hunter.py` حرفيًّا** بكلّ حرّاسه: بوّابة توقيت ·
دِدوب بطبقتين · حارس تغطية · إبلاغٌ صريح لا صمت · ختمُ حياة.

**المصدر:** `FAISAL_SCIENTIFIC_METHOD.md` (ستّ صور UPC، انفجر ‏+99.76% بالافتر)
**+ ما كان عندنا ولم يُستغَلّ**: `trigger_state` وسندُها `TG_1870`.

**الشروط الستّة** (‏`scan_method_hunter`): حدثٌ مؤسِّس (صعودٌ عالٍ ثم هبوط 20-30
جلسة) · التسلسل الرباعيّ · هدفٌ بنيويّ (رأس شمعة الفجوة) · خالٍ من قروب · لا
إعلان طرح · وسياق الاقتراض.

⚖️ **وميزتُها على القياس التاريخيّ:** الشرطان اللذان **استحال باكتيستُهما** —
«لا إعلان طرح» و«شورت قليل ورسوم عالية» — **يعملان حيًّا** ⇒ تُطبَّق الوصفة كاملة.
⚠️ **وحدُّ صدقٍ في كلّ رسالة:** الوصفة **قيد الإثبات الأماميّ** (‏`method_result.md`:
العيّنة 27 دون 30 ⇒ «لا حكم») — ولها سابقةٌ عندنا: **صيّاد المقسّم لم يُثبَت
بباكتيست قطّ وأثبت نفسه حيًّا** (‏NUWE قبل انفجاره بيومين).

🔒 عرض/تنبيه فقط — خارج الفرز والحالة، ولا `LOGIC_VERSION`.
"""

MIN_COVERAGE_PCT = 60.0        # 🩺 أرضية تغطية المسح (أقلّ منها = لم نفحص السوق)
STAMP_FILE = "method_hunter_stamp.json"


def session_gate(now_utc=None, close_hour=20):
    """⏰ نفس بوّابة الصيّاد: لا مسحَ قبل إغلاق الافتر (20:00 نيويورك) — تُصيب
    الفصلين ذاتيًّا. يرجّع `(مفتوحة، تاريخ الجلسة النيويوركيّ)`. نقيّة."""
    import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    now = now_utc or _dt.datetime.now(_dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    et = now.astimezone(_Z("America/New_York"))
    if et.hour < int(close_hour):
        return (False, None)
    return (True, et.date())


def _fail(S, why: str) -> int:
    """🚨 عطلٌ صريح لا صمت (درس الصيّاد): وظيفةٌ خضراء بلا رسالة = مطابقةٌ ليوم
    «لا مرشّح» ⇒ العطل غير مرئي. يرجّع 1 فتصير الوظيفة حمراء أيضًا."""
    S.log(f"🔬 النهج العلمي: {why}")
    try:
        S.send_telegram("🔬 <b>النهج العلمي</b>\n\n"
                        f"⚠️ تعذّر المسح اليوم: {S.esc(why[:200])}\n"
                        "<i>الصمت اليوم عطل لا «لا مرشّح» — يُعاد غدًا آليًّا.</i>"
                        f"\n\n{S.FOOTER}")
    except Exception:                                            # noqa: BLE001
        pass
    return 1


def _read_stamp(S):
    try:
        import json
        with open(STAMP_FILE, encoding="utf-8") as f:
            return str((json.load(f) or {}).get("last_session") or "")
    except Exception:                                            # noqa: BLE001
        return ""


def _write_stamp(S, session_date) -> None:
    """🔔 ختمُ حياة — يُكتب **بعد الإرسال** (درس الصيّاد: لو خُتم قبل إرسالٍ فاشل
    لقرأه الكرون الثاني «سُلِّم» فضاعت رسالة الليلة). فاشل-آمن مطلق."""
    try:
        S._atomic_write_json(STAMP_FILE, {"last_session": str(session_date)})
        S.git_save([STAMP_FILE])
    except Exception as e:                                       # noqa: BLE001
        S.log(f"⚠️ ختم النهج العلمي: {e}")


def run(now_utc=None) -> int:
    import Super_stock as S
    import os
    manual = os.environ.get("METHOD_FORCE", "").strip() == "1"
    open_ok, sess_et = session_gate(now_utc)
    if not open_ok and not manual:
        S.log("⏰ النهج العلمي: الافتر لم يُغلق بعد — لا مسح.")
        return 0
    prev = _read_stamp(S)
    if sess_et is not None and not manual and prev == sess_et.isoformat():
        S.log(f"🔁 النهج العلمي: مساء {sess_et} سُلِّم سلفًا — لا تكرار.")
        return 0
    if S.yf is None:
        return _fail(S, "yfinance غير متاح على الرنر.")
    try:
        uni = S.get_universe()
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر جلب كون ناسداك ({e}).")
    if not uni:
        return _fail(S, "كون ناسداك رجع فارغًا.")
    try:
        hist = S.download_history(uni)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تحميل البيانات فشل ({e}).")
    if not hist:
        return _fail(S, "لا بيانات مُحمَّلة إطلاقًا.")
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} رمزًا "
                        f"({cov:.0f}%) — لم يُفحَص السوق.")
    try:
        sess = max(df.index[-1] for df in hist.values() if len(df)).date()
    except Exception:                                            # noqa: BLE001
        sess = None
    if sess is not None and not manual and prev == sess.isoformat():
        S.log(f"🔁 النهج العلمي: جلسة {sess} سُلِّمت سلفًا — لا تكرار.")
        return 0
    try:
        rows = S.scan_method_hunter(hist, today=sess)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار المسح ({e}).")
    syms = " · ".join(str(r.get("symbol") or "?") for r in rows) or "—"
    S.log(f"🔬 النهج العلمي: فحص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) "
          f"→ {len(rows)} مطابق كامل: {syms}")
    if not rows:
        msg = S._rtl_join([
            "🔬 <b>النهج العلمي</b>", "",
            "لا يوجد سهم يطابق الشروط اليوم.",
            f"🩺 فُحِص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}% تغطية)"
            + (f" · جلسة {S.esc(str(sess))}" if sess else ""),
        ]) + "\n\n" + S.FOOTER
    else:
        try:
            msg = S.build_method_alert(rows, today=sess) + "\n\n" + S.FOOTER
        except Exception as e:                                   # noqa: BLE001
            return _fail(S, f"تعذّر بناء التنبيه رغم {len(rows)} مطابق ({e}).")
    if not S.send_telegram(msg):
        S.log("⛔ النهج العلمي: تلغرام رفض الرسالة.")
        return 1
    S.log("✅ أُرسلت رسالة النهج العلمي.")
    _write_stamp(S, sess)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
