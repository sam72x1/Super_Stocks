# -*- coding: utf-8 -*-
"""
==========================================================
🕵️ فحص اليد عند الطلب (Hand Check) — أداة مستقلة
==========================================================
تعطيها أي رمز سهم → تقول لك: هل وراه مضارب يشتغل عليه أم لا؟ بكل القرائن
(شموع يومية · فريم 4 ساعات · لقطة الطلبات · رفعة قروب ثم كسر دعوم) + ماذا فعلت
اليد اليوم. **عرض/تشخيص فقط** — لا تمسّ الفرز ولا الحالة ولا أي حساب؛ تعيد
استخدام دوال البوت الجاهزة (hand_evidence · hand_activity_today · behav · 4س).

⚠️ الحكم **نوعي بعدد القرائن، بلا درجة مبتدعة** (حكم السنتين §0-ح: بصمة اليد
لا تُرجّح السهم بالفرز — قيمتها أن تعرف وتتوقّع كسر الدعوم، لا أن ترفع السهم).
تدفق الطلبات الحي (Level 2) غير متاح بمسار البوت → يُقال حرفيًا، لا يُخمَّن.

التشغيل (عبر GitHub، مسار مستقل):
  متغير البيئة:  HAND_CHECK=AAPL   →   python hand_check.py
"""
import os

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot


def _verdict(n: int) -> str:
    """حكم نوعي بعدد القرائن (لا درجة مبتدعة)."""
    if n >= 3:
        return "🔴 <b>قرائن قوية — غالبًا وراءه يد نشطة</b>"
    if n == 2:
        return "🟠 <b>قرائن متوسطة — يُشتبه بوجود يد</b>"
    if n == 1:
        return "🟡 <b>قرينة واحدة فقط — إشارة ضعيفة</b>"
    return "🟢 <b>لا قرائن واضحة على يد نشطة</b> (بالبيانات المتاحة)"


def render_hand_check(sym: str, r: dict, df=None) -> str:
    """يبني رسالة فحص اليد من نتيجة مُجمّعة `r` (تحوي behav/pump_scar/h4_levels/
    rotation_pct/session_ctx/interp). دالة نقية قابلة للاختبار (بلا شبكة)."""
    ev = bot.hand_evidence(r)
    L = [f"🕵️ <b>فحص اليد: {bot.esc(sym.upper())}</b>", _verdict(len(ev)), ""]
    if r.get("price"):
        L.append(f"السعر: ${r['price']:.2f}")
    # القرائن (كل دليل بسطره — الإطار + الوصف + القيمة)
    if ev:
        L.append("📋 <b>القرائن المرصودة:</b>")
        for e in ev:
            L.append(f"  • [{e['frame']}] {e['sign']} — {e['detail']}")
    else:
        L.append("لا قرائن مرصودة من الشموع/4س/التدوير/الرفعة.")
    # ماذا فعلت اليد اليوم (شمعة اليوم)
    if df is not None:
        acts = bot.hand_activity_today(r, df)
        if acts:
            L.append("")
            L.append("📌 <b>ماذا فعلت اليد اليوم:</b>")
            for a in acts:
                L.append(f"  • {a}")
    # بصمة طريقة الارتفاع (سياق)
    bh = r.get("behav") or {}
    if bh.get("score") is not None:
        L.append("")
        L.append(f"🧬 طريقة الارتفاع: {bh['score']}/100 · {bh.get('label', '')}")

    # ===== 📊 التحليل كسهم ارتكاز (طلب المستخدم: يحلّله على أنه سهم ارتكاز) =====
    L.append("")
    L.append("━━━━━ 📊 <b>التحليل كسهم ارتكاز</b> ━━━━━")
    if r.get("interp"):        # مؤهّل بالفارز → interp محسوب
        es = bot.entry_status(r)
        L.append("الحكم: 🎯 <b>سهم ارتكاز مؤهّل</b>")
        L.append(("🟢 جاهز للدخول الآن" if es["status"] == "ready_now"
                  else "👀 متابعة")
                 + (f" — {es['reason']}" if es["reason"] else ""))
        L += bot.interp_card_lines(r["interp"])      # 🧭 الإعداد · 🎯 الرقم الحرج · 🕓 4س · ⚠️
        if r.get("tranches") and r.get("stop"):
            trs = r["tranches"]
            stop0 = r["stop"][0] if isinstance(r["stop"], (list, tuple)) else r["stop"]
            L.append("📥 دخول: " + " · ".join(f"${p:.2f}" for p in trs)
                     + f"  ·  ⛔ وقف ${stop0:.2f}")
        if all(r.get(k) for k in ("t1", "t2", "t3")):
            L.append(f"🎯 أهداف: ${r['t1']:.2f} · ${r['t2']:.2f} · ${r['t3']:.2f}")
        # النواقص (بوابات التأكيد الناقصة) — نفس صيغة التقرير اليومي «N/14»
        sf = r.get("soft_fails") or []
        if sf:
            L.append(f"🅱️ الناقص ({len(sf)}/14): "
                     + " · ".join(f"{j}- {x}" for j, x in enumerate(sf, 1)))
        else:
            L.append("✅ اجتاز كل بوابات التأكيد (لا نواقص)")
        _tfi = bot.timeframes_info(r.get("tf_count"), r.get("tf_display"))
        if _tfi:
            L.append(_tfi)
    else:
        why = r.get("reject_reason") or "لم يجتز بوابات الارتكاز الإلزامية"
        L.append(f"الحكم: ❌ <b>ليس سهم ارتكاز مؤهّلًا حاليًا</b> (السبب: {why})")
        L.append("<i>القرائن أعلاه عن اليد تبقى صالحة — لكن الفارز لا يرشّحه الآن "
                 "كارتكاز.</i>")
    L.append("")
    L.append("ℹ️ كشف/تحذير نوعي — علامات اشتباه بيد نشطة، ليست توصية ولا تُرجّح "
             "السهم بالفرز. تدفق الطلبات الحي (Level 2) غير متاح بمسار البوت "
             "(لقطة bid/ask فقط).")
    L.append(bot.FOOTER)
    return "\n".join(L)


def hand_check(sym: str):
    """يجمع بيانات السهم (يومي + 4س + info) ويحسب القرائن. يرجع (نص، None) أو
    (None, رسالة خطأ). يعيد استخدام دوال البوت — لا منطق فرز جديد."""
    sym = sym.strip().upper()
    try:
        data = bot.download_history([sym])
    except Exception as e:
        return None, f"تعذّر الاتصال لجلب بيانات {sym}: {e}"
    df = data.get(sym)
    if df is None or len(df) < 30:
        return None, (f"تعذّر جلب بيانات كافية لـ {sym} "
                      "(رمز خاطئ أو سهم جديد جدًا).")
    price = float(df["Close"].iloc[-1])
    r = {"symbol": sym, "price": price, "last_price": price,
         "vol_today": float(df["Volume"].iloc[-1])}
    # بصمة اليومي + رفعة القروب
    try:
        r["behav"] = bot.behavior_rise_profile(df)
        r["pump_scar"] = bot.group_pump_scar(df)
    except Exception:
        pass
    # مستويات 4س (السقف المُدار) — بيانات 4س المجلوبة
    try:
        h4 = bot.fetch_4h(sym)
        if h4 is not None:
            r["h4_levels"] = bot.four_hour_levels(h4, price)
    except Exception:
        pass
    # info: الفلوت (للتدوير) + لقطة bid/ask الصادقة
    if bot.yf is not None:
        try:
            info = bot._fetch_info(bot.yf.Ticker(sym))
            flt = info.get("floatShares")
            if flt:
                r["float"] = flt
                r["rotation_pct"] = round(r["vol_today"] / flt * 100.0)
            _bid, _ask = info.get("bid"), info.get("ask")
            _spread = None
            if _bid and _ask and _ask > 0 and _ask >= _bid:
                _spread = round((_ask - _bid) / _ask * 100.0, 1)
            r["session_ctx"] = {"quote": {
                "bid": _bid, "ask": _ask, "spread_pct": _spread,
                "note": "لقطة وحيدة — تدفق الطلبات الحي غير متاح بمسار البوت"}}
        except Exception:
            pass
    # التحليل كسهم ارتكاز (طلب المستخدم): مؤهّل → interp كامل · مرفوض → السبب
    try:
        bot._REJECT_STATS.clear()
        official = bot.analyze_ticker(sym, df)
        if official:
            r["pivot"] = official.get("pivot")
            r["tranches"] = official.get("tranches")
            r["stop"] = official.get("stop")
            r["key_levels"] = official.get("key_levels")
            for k in ("t1", "t2", "t3", "warnings", "soft_fails",
                      "readiness", "tf_count", "tf_display"):
                r[k] = official.get(k)
            if r.get("h4_levels"):
                official["h4_levels"] = r["h4_levels"]
                r["h4_levels"] = r["h4_levels"]
            r["interp"] = bot.build_interpretation(r)
        elif getattr(bot, "_REJECT_STATS", None):
            r["reject_reason"] = " · ".join(f"{k}={v}"
                                            for k, v in bot._REJECT_STATS.items())
    except Exception:
        pass
    return render_hand_check(sym, r, df), None


def main():
    sym = os.environ.get("HAND_CHECK", "").strip()
    if not sym:
        bot.log("⚠️ ضع HAND_CHECK=الرمز (مثل HAND_CHECK=VFF).")
        return
    bot.log(f"🕵️ فحص اليد للسهم: {sym}")
    msg, err = hand_check(sym)
    if msg is None:
        bot.send_telegram(f"🕵️ <b>فحص اليد: {bot.esc(sym.upper())}</b>\n\n"
                          f"⚠️ {bot.esc(err)}\n\n{bot.FOOTER}")
        bot.log(f"تعذّر: {err}")
        return
    bot.send_telegram(msg)
    bot.log("✅ أُرسل فحص اليد.")


if __name__ == "__main__":
    main()
