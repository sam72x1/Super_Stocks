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
    # 📊 تدفق الأوامر (Polygon حي · وإلا لقطة Yahoo · وإلا «—» — لا يعيق الفحص)
    L.append("")
    L.append(f"📊 تدفق الأوامر: {r.get('order_flow') or '—'}")
    # بصمة طريقة الارتفاع (سياق)
    bh = r.get("behav") or {}
    if bh.get("score") is not None:
        L.append("")
        L.append(f"🧬 طريقة الارتفاع: {bh['score']}/100 · {bh.get('label', '')}")

    # ===== 📊 التحليل كسهم ارتكاز (طلب المستخدم: كل البوابات حتى لو سقط مبكرًا) =====
    L.append("")
    L.append("━━━━━ 📊 <b>التحليل كسهم ارتكاز</b> ━━━━━")
    # كل البوابات الإلزامية بحالتها ✅/❌ (تُقيَّم مستقلة — تظهر كاملة حتى لو سقط
    # السهم على بوابة صلبة مثل السعر تحت $1.5). هذا جوهر طلب المستخدم.
    gates = r.get("gates") or []
    if gates:
        passed = sum(1 for _, ok, _ in gates if ok)
        L.append(f"البوابات الإلزامية: <b>{passed}/{len(gates)}</b> "
                 "(كلها معروضة حتى لو سقط على بوابة صلبة):")
        for name, ok, detail in gates:
            L.append(f"  {'✅' if ok else '❌'} {name} — {detail}")
        L.append("")
    if r.get("interp"):        # مؤهّل بالفارز → الحالة + الدخول + الأهداف
        es = bot.entry_status(r)
        L.append("الحكم: 🎯 <b>سهم ارتكاز مؤهّل</b> · "
                 + ("🟢 جاهز للدخول الآن" if es["status"] == "ready_now"
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
    else:
        why = r.get("reject_reason") or "لم يجتز بوابة إلزامية (انظر ❌ أعلاه)"
        L.append(f"الحكم: ❌ <b>ليس سهم ارتكاز مؤهّلًا حاليًا</b> "
                 f"(أول سبب: {why})")
        L.append("<i>القرائن أعلاه عن اليد تبقى صالحة — لكن الفارز لا يرشّحه الآن "
                 "كارتكاز.</i>")
    L.append("")
    L.append("ℹ️ كشف/تحذير نوعي — علامات اشتباه بيد نشطة، ليست توصية ولا تُرجّح "
             "السهم بالفرز. تدفق الطلبات الحي (Level 2) غير متاح بمسار البوت "
             "(لقطة bid/ask فقط).")
    L.append(bot.FOOTER)
    return "\n".join(L)


def hand_check(sym: str):
    """يجمع بيانات السهم + كل البوابات + القرائن. يرجع (نص، None) أو (None، خطأ).
    يعيد استخدام `analyze_on_demand` (كل البوابات مستقلة — تظهر حتى لو سقط على
    بوابة صلبة) + `enrich` (شورت/فلوت/تدوير/لقطة طلبات/4س) — لا منطق فرز جديد."""
    import analyze_one as AO
    sym = sym.strip().upper()
    try:
        diag, gates, df = AO.analyze_on_demand(sym)
    except Exception as e:
        return None, f"تعذّر تحليل {sym}: {e}"
    if diag is None or df is None:
        return None, (gates if isinstance(gates, str)
                      else f"تعذّر جلب بيانات كافية لـ {sym}.")
    price = float(df["Close"].iloc[-1])
    diag["vol_today"] = float(df["Volume"].iloc[-1])   # للتدوير في enrich
    # إثراء (شورت/فلوت/تدوير/لقطة الطلبات N3/مستويات 4س بالسقف المُدار N2) — نفس
    # دالة البوت؛ ثم بوابتا الشورت/الفلوت (M13/M14) على البيانات المُثراة.
    try:
        bot.enrich([diag])
    except Exception:
        pass
    try:
        gates = AO.append_short_float_gates(diag, gates)
    except Exception:
        pass
    r = {"symbol": sym, "price": price, "last_price": price, "gates": gates,
         "float": diag.get("float"), "rotation_pct": diag.get("rotation_pct"),
         "session_ctx": diag.get("session_ctx"),
         "h4_levels": diag.get("h4_levels")}
    try:
        r["behav"] = bot.behavior_rise_profile(df)     # بصمة اليومي
        r["pump_scar"] = bot.group_pump_scar(df)       # رفعة القروب/كسر الدعوم
    except Exception:
        pass
    # 📊 تدفق الأوامر (Polygon حي · احتياط Yahoo · فاشل-آمن → «—» لا يعيق الفحص)
    try:
        r["order_flow"] = bot.order_snapshot(sym)
    except Exception:
        r["order_flow"] = None
    # مؤهّل ارتكاز؟ (interp + دخول/أهداف لو مرّ) · وإلا السبب الأول
    try:
        bot._REJECT_STATS.clear()
        official = bot.analyze_ticker(sym, df)
        if official:
            for k in ("pivot", "tranches", "stop", "key_levels",
                      "t1", "t2", "t3", "warnings", "soft_fails"):
                r[k] = official.get(k)
            if r.get("h4_levels"):
                official["h4_levels"] = r["h4_levels"]
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
