# -*- coding: utf-8 -*-
"""🌙▶️ تشغيلٌ **يدويٌّ** لرادار ما قبل الجلسة — أمرُ المالك «شغّل الأداة» (2026-09-04).

القرارُ المجدول يقع في نافذةِ ستِّ دقائقَ داخل العامل الحيّ (‏03:50 و15:50
نيويورك) ⇒ **لا سبيلَ لتشغيلها خارجها**، فيستحيل على المالك أن يراها تعمل متى
شاء. هذي الأداةُ تسدّ ذلك:

- 🔒 **تنادي `run_presession` الإنتاجيّة نفسَها** — صفرُ منطقٍ مكرّر، فلا يصير
  للرادار قراءتان (درسُ «مقياسٌ واحدٌ لا اثنان»).
- 🔴 **ولا تكتب السجلَّ الأماميّ إطلاقًا**: صفوفُه سلسلةٌ زمنيّةٌ من قراراتٍ في
  **نافذتها**، وإلحاقُ تشغيلٍ يدويٍّ خارجها **يلوّث الحصادَ** بصفوفٍ لا تصف
  قرارًا. ⇒ عرضٌ/تشخيصٌ فقط.
- 🏷️ **والرسالةُ تقول إنها يدويّة** بوقتها — وإلّا قُرئت قرارَ اليوم المجدول.
- ⚙️ فاشلٌ-آمن: بلا مفتاح Polygon ⇒ لا عمل · وأيُّ عطلٍ يُطبَع ويُرجع رمزًا
  غيرَ صفريّ (لا فشلَ صامت).
"""
from __future__ import annotations

import os
import sys
import time

import Super_stock as bot
import presession_radar as PRE


def _log(msg: str) -> None:
    print(msg, flush=True)


def resolve_slot(env_val: str | None, mod_ny: int) -> str:
    """أيُّ جلسةٍ نشغّلها؟ **صريحُ البيئة يعلو**، وإلّا يُشتقّ من ساعة نيويورك:
    قبل ظهرِ نيويورك ⇒ `PM` (البريماركت) وبعده ⇒ `AH`. نقيّةٌ وقابلةٌ للاختبار."""
    v = str(env_val or "").strip().upper()
    if v in ("PM", "AH"):
        return v
    try:
        m = int(mod_ny)
    except (TypeError, ValueError):
        return "PM"
    return "PM" if m < 12 * 60 else "AH"


def manual_header(slot: str, mod_ny: int) -> str:
    """ترويسةُ «هذا تشغيلٌ يدويّ» — بلا علامات مقارنة (قاعدةُ العرض)."""
    name = "الافتر" if slot == "AH" else "البريماركت"
    hh, mm = int(mod_ny) // 60, int(mod_ny) % 60
    return (f"▶️ <b>تشغيلٌ يدويّ</b> (خارج نافذة القرار) — {name} · "
            f"الساعةُ {hh:02d}:{mm:02d} نيويورك. "
            "لا يُكتَب في السجلّ الأماميّ.")


def main() -> int:
    if not (os.environ.get("POLYGON_API_KEY") or "").strip():
        _log("⚠️ لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return 0
    mod, day = None, (os.environ.get("PRESESSION_DAY") or "").strip()
    today = None
    try:
        today, mod = PRE.ny_mod(int(time.time() * 1000))   # (تاريخ، دقيقة)
    except Exception as e:                                       # noqa: BLE001
        _log(f"⛔ تعذّرت ساعةُ نيويورك: {e}")
        return 2
    if mod is None or not today:
        _log("⛔ تعذّرت ساعةُ نيويورك (رجعت فارغة) — لا تخمين.")
        return 2
    day = day or today
    slot = resolve_slot(os.environ.get("PRESESSION_SLOT"), mod)
    _log(f"🌙▶️ تشغيلٌ يدويّ: جلسة {slot} · يوم {day} · "
         f"الساعة {mod // 60:02d}:{mod % 60:02d} نيويورك")
    try:
        rows, msg, diag = PRE.run_presession(
            slot, day, int(time.time() * 1000), log=_log,
            price_lo=float(bot.CONFIG["MIN_PRICE"]),
            price_hi=float(bot.CONFIG["SPLIT_RADAR_PRICE_MAX"]),
            liq_fn=bot.liq_stage_events, win=int(bot.LIQ_WINDOW_MIN))
    except Exception as e:                                       # noqa: BLE001
        _log(f"⛔ سقط المسح: {type(e).__name__}: {e}")
        return 3
    _log(f"🌙 حصيلةُ {slot} {day}: {diag}")
    if diag.get("reason"):
        _log(f"⛔ عطلُ جلبٍ مُسمًّى: {diag['reason']} — لا رسالة.")
        return 4
    if not msg:
        _log("⛔ رسالةٌ فارغة — وهي حالةٌ لا ينبغي أن تقع بعد «الليلةُ الصامتة "
             "تتكلّم». تُبلَّغ ولا تُصمَت.")
        return 5
    if not PRE.send_enabled(slot, os.environ.get("PRESESSION_SEND")):
        _log("🔇 الإرسالُ مطفأٌ لهذي الجلسة (`PRESESSION_SEND`) — الرسالةُ أدناه "
             "للعرض فقط.\n" + msg)
        return 0
    ok = bot.send_telegram(manual_header(slot, mod) + "\n\n" + msg
                           + "\n\n" + bot.FOOTER)
    _log("✅ أُرسلت." if ok else "⛔ تيليجرام رفض الرسالة.")
    return 0 if ok else 6


if __name__ == "__main__":
    raise SystemExit(main())
