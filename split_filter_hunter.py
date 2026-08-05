#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧮 صيّاد «فلترة أسهم التقسيم» — **النظام الرابع**، أداةٌ مستقلّة.

المصدر: `FAISAL_SPLIT_FILTER_METHOD.md` (نصّ فيصل الكامل + خمس صور) — النوعان
① و② حصرًا. **والنوع ③ متروكٌ عمدًا** لأنه وصفةُ «النهج العلمي» نفسها (صعودٌ عالٍ
ثم انتظارُ 20 يومًا) ولها أداتُها؛ **والنوع ④ (اكتتاب) بلفظه «صعب شرحه يحتاج
ممارسة علمية»** فلا يُبرمَج.

⚖️ **تصحيحا المالك 2026-08-05 مُدرَجان:** «**الحراج = القروبات**» ⇒ الشرط مخدومٌ
بـ`group_pump_scar` · و«برنامج هدف الشورت **مب لازم** — المهمّ نعرف كم الشورت»
⇒ يكفي `ce_borrow_info`.

🔴 **وقفُه «ذيل شمعة القاع»** — رابعُ وقفٍ في مادّة فيصل ولا يُخلط بالثلاثة.
🔒 خارج الفرز والحالة · لا `LOGIC_VERSION` · **ولا يمسّ صيّاد المقسّم بحرف**.

حرّاسُه نفسُ حرّاس الصيّادين: بوّابة توقيت بعد إغلاق الافتر · دِدوب بطبقتين ·
حارس تغطية · إبلاغٌ صريح لا صمت · «لا يوجد» ومعها التغطية · وختمٌ **بعد** الإرسال.
"""

MIN_COVERAGE_PCT = 60.0
STAMP_FILE = "split_filter_stamp.json"


def session_gate(now_utc=None, close_hour=20):
    """⏰ نفسُ بوّابة الصيّادين: لا مسحَ قبل إغلاق الافتر (20:00 نيويورك) — تُصيب
    الفصلين ذاتيًّا. يرجّع `(مفتوحة، تاريخ الجلسة النيويوركيّ)`. نقيّة.

    🐞 **وسببُ وجودها هنا عيبٌ في مسوّدتي:** كتبتُ أوّلًا
    `S.split_hunter_session_gate(...) if hasattr(...) else (True, None)` —
    والدالّة **ليست في `Super_stock`** أصلًا (كلُّ صيّادٍ يملك نسختَه) ⇒ الشرطُ
    يسقط دائمًا على الاحتياط ⇒ **البوّابة معطَّلةٌ بصمت**. وهذا صنفُ «حارسٍ
    يبدو موجودًا وهو مُلغًى» الذي بُني كلُّ قفلٍ هنا ضدّه.
    🔒 ومقفولٌ باختبارٍ يقارنها بنظيرتَيها في الصيّادين على أوقاتٍ متطابقة."""
    import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    now = now_utc or _dt.datetime.now(_dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    et = now.astimezone(_Z("America/New_York"))
    if et.hour < int(close_hour):
        return (False, None)
    return (True, et.date())


def _fail(S, msg):
    """⛔ إبلاغٌ صريح — **الصمت لا يُخلَط بالعطل** (نفس عقد الصيّادين)."""
    S.log(f"⛔ فلترة التقسيم: {msg}")
    try:
        S.send_telegram(S._rtl_join(
            ["🧮 <b>فلترة أسهم التقسيم</b>", "",
             f"⛔ <b>تعذّر المسح</b> — {S.esc(msg)}",
             "<i>هذا عطل لا «لا يوجد مرشّح».</i>"]) + "\n\n" + S.FOOTER)
    except Exception:                                            # noqa: BLE001
        pass
    return 1


def _read_stamp(S):
    try:
        import json
        with open(STAMP_FILE, encoding="utf-8") as fh:
            return str(json.load(fh).get("session") or "")
    except Exception:                                            # noqa: BLE001
        return ""


def _write_stamp(S, sess):
    """🔏 الختمُ **بعد** الإرسال — فرفضُ تلغرام لا يختم ⇒ يُعاد غدًا."""
    try:
        import json
        with open(STAMP_FILE, "w", encoding="utf-8") as fh:
            json.dump({"session": (sess.isoformat() if sess else None)}, fh)
        # 🐞 **عيبٌ كشفه التشغيلُ الحيّ وحده (2026-08-05):** كتبتُ
        #    `git_save([STAMP_FILE], "split filter stamp")` ظنًّا أن الوسيط
        #    الثاني رسالةُ commit — **وتوقيعُها `(filenames, runner, sender)`**
        #    فصار النصُّ هو `runner` ⇒ `run(...)` ⇒ **`'str' object is not
        #    callable`** ⇒ **الختمُ لا يُحفَظ ⇒ الدِدوب بلا ذاكرة ⇒ رسالةٌ
        #    مكرّرة على الكرون الثاني**. والاختبارات لا تراه (تحقن حول الدفع).
        #    🧭 والدرس: **وسيطٌ ثانٍ لم أقرأ توقيعَه = خطأٌ ينتظر التشغيل.**
        S.git_save([STAMP_FILE])
    except Exception as e:                                       # noqa: BLE001
        S.log(f"⚠️ فلترة التقسيم: تعذّر ختمُ الجلسة ({e}).")


def run(now_utc=None) -> int:
    import os
    import Super_stock as S
    manual = os.environ.get("SPLIT_FILTER_FORCE", "") == "1"
    ok, sess_et = session_gate(now_utc)
    if not manual and not ok:
        S.log("⏳ فلترة التقسيم: قبل إغلاق الافتر — لا مسح.")
        return 0
    prev = _read_stamp(S)
    if not manual and sess_et is not None and prev == sess_et.isoformat():
        S.log(f"🔁 فلترة التقسيم: جلسة {sess_et} سُلِّمت سلفًا — لا تكرار.")
        return 0
    if S.yf is None:
        return _fail(S, "yfinance غير متاح.")
    try:
        uni = S.get_universe()
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر جلب كون ناسداك ({e}).")
    if not uni:
        return _fail(S, "كون ناسداك فارغ.")
    try:
        hist = S.download_history(uni)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار التحميل ({e}).")
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} رمزًا "
                        f"({cov:.0f}%) — لم يُفحَص السوق.")
    try:
        sess = max(df.index[-1] for df in hist.values() if len(df)).date()
    except Exception:                                            # noqa: BLE001
        sess = None
    if sess is not None and not manual and prev == sess.isoformat():
        S.log(f"🔁 فلترة التقسيم: جلسة {sess} سُلِّمت سلفًا — لا تكرار.")
        return 0
    try:
        rows = S.scan_split_filter(hist, today=sess)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار المسح ({e}).")
    syms = " · ".join(str(r.get("symbol") or "?") for r in rows) or "—"
    S.log(f"🧮 فلترة التقسيم: فحص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) "
          f"→ {len(rows)} مطابق كامل: {syms}")
    for _n in (getattr(S, "_SPLIT_FILTER_NEAR", []) or []):
        S.log(f"   🔭 {_n.get('symbol')} ${float(_n.get('price') or 0):.2f} — "
              f"{_n.get('why')}")
    if not rows:
        _near = getattr(S, "_SPLIT_FILTER_NEAR", []) or []
        msg = S._rtl_join([
            "🧮 <b>فلترة أسهم التقسيم</b>", "",
            "لا يوجد سهم يطابق الشروط اليوم.",
            f"🩺 فُحِص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}% تغطية)"
            + (f" · جلسة {S.esc(str(sess))}" if sess else ""),
        ] + ([""] + S.method_near_lines(_near) if _near else [])) \
            + "\n\n" + S.FOOTER
    else:
        try:
            msg = S.build_split_filter_alert(rows, today=sess) + "\n\n" + S.FOOTER
        except Exception as e:                                   # noqa: BLE001
            return _fail(S, f"تعذّر بناء التنبيه رغم {len(rows)} مطابق ({e}).")
    if not S.send_telegram(msg):
        S.log("⛔ فلترة التقسيم: تلغرام رفض الرسالة.")
        return 1
    S.log("✅ أُرسلت رسالة فلترة التقسيم.")
    _write_stamp(S, sess)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
