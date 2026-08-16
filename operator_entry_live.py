# -*- coding: utf-8 -*-
"""🎯 **«هنا الدخول» — عاملُ جلسةٍ حيّ** (أمرُ المالك 2026-08-16 «سرعة»).

يمسح **كونَ المتابعة الحيّة** (قوائمنا الخمس) كلَّ ‏≈60 ثانية عن **ثلاثية
فيصل على فريم الدقيقة** — صعودٌ أوّل ⟵ رجعَ لنفس الدعم وثبت ⟵ عبرَ الفيواب
صاعدًا — ويرسل «‏🎯 هنا الدخول» أوّلَ ما تكتمل، **قبل الافتتاح وبعده**.

⚖️ **ولماذا عاملُ جلسةٍ لا كرون:** المراقبُ الدوريّ حبيبتُه 15 دقيقة، ونافذةُ
`WETO` في صورة المالك (لمسةُ الدعم ⟶ عبورُ الفيواب) كانت **‏≈10 دقائق** ⇒
الحبيبةُ الخشنة قد تُدخله بعد بدء الحركة بدقائق. وهذا **يكمّله لا يستبدله**:
المراقبُ يبقى شبكةَ أمانٍ للأفتر ولِما يُسقطه GitHub من تشغيلات.

🔒 **إشعارٌ/توقيتٌ فقط:** لا يمسّ فرزًا ولا عضويةَ قائمة ولا عتبة — يقرأ
القوائمَ ويرسل. وبلا `POLYGON_API_KEY` = **صفرُ عمل** (فاشلٌ-آمن).

المقاطع (`OE_SEGMENT`): `pre` قبل الافتتاح · `open` الجلسة · `post` الإغلاق
والأفتر. وكلٌّ يقف عند سقف زمنه أو عند نهاية الجلسة الممتدّة — أيُّهما أبكر.
"""
import json
import os
import subprocess
import time

try:
    import Super_stock as bot
except ImportError:                                              # pragma: no cover
    import super_stock as bot

INTERVAL_DEFAULT = 60          # ثانيةً بين الدورات
MAX_RUNTIME_MIN = 330          # سقفُ أمانٍ تحت حدّ GitHub (‏6 ساعات)
REFRESH_EVERY = 10             # كلَّ ~10 دقائق: تحديثُ القوائم من origin/main
EXT_CLOSE_NY = 20 * 60         # نهايةُ الجلسة الممتدّة (‏20:00 نيويورك)
EXT_OPEN_NY = 4 * 60           # بدءُ الجلسة الممتدّة (‏04:00 نيويورك)


def _log(msg):
    bot.log(msg)


def _ny_minutes(now=None):
    """دقائقُ اليوم بتوقيت نيويورك — **يتصيّف/يتشتّى ذاتيًّا** (لا ثوابت UTC)."""
    try:
        from zoneinfo import ZoneInfo
        n = now or bot.dt.datetime.now(bot.dt.timezone.utc)
        ny = n.astimezone(ZoneInfo("America/New_York"))
        return ny.hour * 60 + ny.minute, ny.date().isoformat()
    except Exception:                                            # noqa: BLE001
        n = now or bot.dt.datetime.now(bot.dt.timezone.utc)
        return (n.hour * 60 + n.minute - 240) % 1440, n.date().isoformat()


def _holiday(date_iso) -> bool:
    """عطلةُ سوق؟ **فاشل-آمن ⇒ False** (نعمل ولا نصمت على شكٍّ في التقويم)."""
    try:
        import market_calendar as mc
        return (mc.session_info(date_iso) or {}).get("type") == "holiday"
    except Exception:                                            # noqa: BLE001
        return False


def _fetch_state(paths):
    """يجلب أحدثَ نسخةٍ من ملفّات الحالة من `origin/main` — العاملُ على رنرٍ
    منفصل، فدفعاتُ المراقب/الفرز لا تصل نسختَه المحلّية أبدًا.
    **فاشل-آمن:** أيُّ إخفاق ⇒ نُبقي المحلّيّ (سلوكُ اليوم)."""
    out = {}
    try:
        subprocess.run(["git", "fetch", "origin", "main", "-q"],
                       capture_output=True, timeout=60)
    except Exception:                                            # noqa: BLE001
        return out
    for p in paths:
        try:
            r = subprocess.run(["git", "show", f"FETCH_HEAD:{p}"],
                               capture_output=True, timeout=30)
            if r.returncode == 0 and r.stdout:
                out[p] = json.loads(r.stdout.decode("utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
    return out


def _load_universe():
    """يبني كونَ المتابعة من **أحدث** نسخةٍ للقوائم الخمس (أو المحلّية عند التعذّر)."""
    fresh = _fetch_state(["weekly_watchlist.json", "near_watch.json",
                          "press_radar_state.json", "hunter_watchlist.json",
                          bot.OP_ENTRY_STATE_FILE])
    wl = fresh.get("weekly_watchlist.json") or bot.load_watchlist()
    near = fresh.get("near_watch.json")
    if near is None:
        near = bot.load_near_watch()
    press = fresh.get("press_radar_state.json") or {}
    hunter = fresh.get("hunter_watchlist.json") or bot.load_hunter_watch()
    seen = fresh.get(bot.OP_ENTRY_STATE_FILE)
    if not isinstance(seen, dict):
        seen = bot.load_op_entry_state()
    uni, cut = bot.live_watch_universe(wl, near, press, hunter)
    return uni, cut, seen


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        _log("⚠️ «هنا الدخول»: لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return 0
    role = (os.environ.get("OE_SEGMENT", "").strip().lower() or "full")
    try:
        interval = max(20, int(os.environ.get("OE_INTERVAL", "")
                               or INTERVAL_DEFAULT))
    except Exception:                                            # noqa: BLE001
        interval = INTERVAL_DEFAULT
    t0 = time.time()
    mins, day = _ny_minutes()
    if _holiday(day):
        _log(f"📅 {day} عطلةُ سوق — لا جلسةَ متابعة.")
        return 0
    # نهايةُ العمل: إغلاقُ الجلسة الممتدّة (‏20:00 نيويورك) أو سقفُ الزمن.
    left_min = max(0, EXT_CLOSE_NY - mins)
    budget = min(MAX_RUNTIME_MIN, left_min)
    if budget <= 0:
        _log(f"⏹️ الجلسةُ الممتدّة انتهت (‏{mins // 60:02d}:{mins % 60:02d} "
             "نيويورك) — لا عمل.")
        return 0
    _log(f"🎯 «هنا الدخول» [{role}]: يبدأ عند {mins // 60:02d}:{mins % 60:02d} "
         f"نيويورك · كلَّ {interval}ث · لمدّة {budget} دقيقة.")
    uni, cut, seen = _load_universe()
    if cut:
        _log(f"ℹ️ كون المتابعة: قُصّ {cut} فوق السقف {bot.LIVE_WATCH_CAP} "
             "(مُعلَن لا صامت).")
    _log(f"👁️ كون المتابعة: {len(uni)} سهمًا — "
         + " · ".join(f"{k}={sum(1 for r in uni if r['src'] == k)}"
                      for k in bot.LIVE_WATCH_SOURCES))
    loops, fired, errs = 0, 0, 0
    while (time.time() - t0) < budget * 60:
        loops += 1
        if loops % REFRESH_EVERY == 0:
            try:
                uni, _c, _s = _load_universe()
                for _k, _v in (_s or {}).items():
                    seen.setdefault(_k, _v)
            except Exception as e:                               # noqa: BLE001
                _log(f"⚠️ تحديثُ الكون (دورة {loops}): {e}")
        try:
            _today = _ny_minutes()[1]
            rows = bot.scan_operator_entry(uni, _today, seen=seen)
        except Exception as e:                                   # noqa: BLE001
            errs += 1
            rows = []
            _log(f"⚠️ المسح (دورة {loops}): {e}")
        if rows:
            _syms = [r[0]["symbol"] for r in rows]
            try:
                ok = bot.send_telegram(
                    bot.build_operator_entry_alert(rows) + "\n\n" + bot.FOOTER)
            except Exception as e:                               # noqa: BLE001
                ok, _ = False, _log(f"⚠️ إرسال «هنا الدخول»: {e}")
            if ok:
                fired += len(rows)
                _log(f"🎯 {len(rows)} دخول: {', '.join(_syms)}")
                # ⚠️ الختمُ **بعد** الإرسال حصرًا (عقدُ «فُحِص وسُلِّم») — والدفعُ
                #    فورًا كي ينجو الدِدوب من موت الرنر وتقرأه المقاطعُ التالية.
                bot.save_op_entry_state(seen)
                try:
                    bot.git_save([bot.OP_ENTRY_STATE_FILE])
                except Exception as e:                           # noqa: BLE001
                    _log(f"⚠️ دفعُ الدِدوب: {e}")
            else:
                for _s in _syms:                 # لم يصل ⇒ يُعاد في الدورة التالية
                    seen.pop(_s, None)
                _log(f"⚠️ تيليجرام رفض «هنا الدخول» ({len(rows)}) — "
                     "نُزع الختمُ لتُعاد المحاولة.")
        time.sleep(interval)
    _log(f"✅ انتهى [{role}]: {loops} دورة · {fired} دخولًا · {errs} خطأ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
