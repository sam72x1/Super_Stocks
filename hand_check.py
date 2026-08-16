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
import datetime as dt

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
    # (🔬 التجميع الصامت أُزيل 2026-07-09 — تجربة T-ACC فشلت بالسنتين، غير مميِّز
    #  للمنفجر؛ لا نعرض إشارة سقطت في اختبارها. الدوال + acc_verify.py محفوظة.)
    # 📊 الشورت الرسمي (SI) + أيام التغطية (🎬 فيديو DSY — فيصل قرأهما من Fintel)
    _sil = bot.short_interest_line(r)
    if _sil:
        L.append(_sil)
    # 💧 سبريد/سيولة (🎬 فيصل يبدأ فيديو DSY بدفتر الأوامر) — من NBBO الخام إن توفّر
    _fr = r.get("flow_raw") or {}
    _spl = bot.spread_line(_fr.get("bid"), _fr.get("ask"))
    if _spl:
        L.append(_spl)
    # 🕵️ «من وراء السهم» = دمج FSTO (قوة التذبذب من الشموع) + شروط تدفق Polygon
    # (بصمة الخوارزميات من التّيب — O/OI/Ap/Dp) — طلب المستخدم «ندمج الثنتين». أوّلي/لحظي.
    _actor = bot.flow_actor_read(r.get("fsto_osc"), _fr.get("operator_profile"))
    if _actor:
        L.append(_actor)
    # 🆕 N8 «المشتريات الموحّدة» (المسح الثاني 2026-07-27، TG_2113): تكرار حجمٍ بعينه
    # (1·3·5·7·10 رموز خوارزمية بين مضاربين · 100 حفاظ على نطاق · 500 انفجار نادر).
    _up = (_fr.get("prints") or {})
    if _up.get("uniform_size"):
        L.append(f"🔣 مشتريات موحّدة: الحجم <b>{_up['uniform_size']}</b> تكرّر "
                 f"{_up['uniform_count']} مرة — {_up['uniform_meaning']}")
    # 🎯 «أهداف الشورت» — منظومة فيصل كاملةً (TG_1813 + TG_2041). عند الطلب فقط
    # (فحص اليد) فلا تُضاف رسالة ثالثة للتقرير اليومي — عقد المستخدم: رسالتان.
    # ⚠️ **تصحيحان (تدقيق الخلط 2026-07-27):** (1) كنت أقرأ `r.get("df")` وهو مفتاح
    # **غير موجود** — الإطار يصل وسيطًا `df`، فكانت سطور «القاع التالي/سحب السيولة»
    # ميتة دائمًا. (2) مرجع الـ÷2 كان `r.get("split_ref") or r.get("ref")` والمفتاح
    # العامّ `ref` **بابُ خلط**: لو حمله سجلٌّ يومًا لطُبع «هدف هبوط» مُختلَق على
    # ارتكاز غير مقسّم. صار المفتاح **خاصًّا بالحدث المؤسِّس** حصرًا (`split_ref`).
    try:
        _nb = bot.next_bottom_by_own_drop(df)
        _pl = r.get("plan") or bot.faisal_split_plan(df, r.get("price"))
        L.append("")
        L += bot.short_targets_report(
            post_split_high=r.get("split_ref"),
            price=r.get("price"),
            avail=(r.get("shares_available") if r.get("shares_available")
                   is not None else (r.get("borrow") or {}).get("shares_available")),
            float_shares=r.get("float"),
            # ⚠️ **المجهول ليس نفيًا** (تدقيق 2026-07-27): `pump_scar` يُحسب في كتلة
            # try مشتركة، فأي استثناء يُسقط المفتاح — و`bool(None)` كان يطبع «✅ خالٍ
            # من رفعات القروبات» كأنه فحصٌ متحقَّق. الغياب الآن = None = لا سطر.
            pump=((bool((r.get("pump_scar") or {}).get("found")))
                  if isinstance(r.get("pump_scar"), dict)
                  and "found" in r["pump_scar"] else None),
            offering=bool(r.get("offering_event")) if r.get("offering_event") else None,
            next_bottom=_nb,
            sweep=(_pl or {}).get("sweep"))
    except Exception:
        pass
    # ⭐ «اتفاق الفريمات» وصيد الارتداد (فيصل IMG_0305/0306): 5د+15د+30د على نفس الدعم +
    # «الارتداد الأول لا دخول · الثاني تأكيد». يعيد استخدام دقائق Polygon (فاشل-آمن → لا سطر).
    try:
        _rbe = bot.rebound_entry_state(bot.polygon_minute_bars(sym, minutes=240))
        _rbl = bot.rebound_entry_line(_rbe)
        if _rbl:
            L.append(_rbl)
    except Exception:
        pass
    # 🎬 KST 4س (حالة زخم مساندة — مؤشر فيصل بالفيديو)
    if r.get("kst4"):
        L.append(f"📈 KST (4س): {r['kst4']}")
    # 🌙 «اليوميُّ فوّت هذا» (فيصل على DRCT: «الفريم اليومي فقط وقت الماركت»)
    # ⚖️ وفحصُ اليد **يُصرّح بالفراغ** لا يصمت: غيابُ السطر قد يكون «لا فارق»
    #    أو «تعذّر القياس» — والاثنان يُقالان بلفظهما لا يُخلطان.
    _ahm = r.get("ah_missed")
    _ahl = bot.ah_missed_line(_ahm)
    if _ahl:
        L += _ahl
    elif isinstance(_ahm, dict):
        L.append("🌙 اليوميُّ فوّت هذا: — (الجلسةُ الممتدّة لم تتجاوز مدى "
                 "النظاميّة بفارقٍ يستحقّ الذكر)")
    else:
        L.append("🌙 اليوميُّ فوّت هذا: — (تعذّر القياس — تعذّرٌ ليس نفيًا)")
    # 🔒 معدّل الاقتراض (فيصل: أساس الارتكاز · اقتراض صعب = وقود سكويز · «—» عند التعذّر)
    L.append(bot.borrow_line(r))
    # 📅 الأحداث المعلنة القادمة (أرباح/تجارب — يوم الانفجار المحتمل، فيصل 9428)
    _evls = bot.events_lines(r.get("upcoming_events"))
    L += _evls if _evls else ["📅 أحداث معلنة قادمة: — (لا أرباح/تجارب معلنة بالأفق)"]
    # 📄 شراء الداخليين (Form 4) — فيصل يعدّه سببًا مباشرًا للارتفاع (SVRE/BNKK)
    _ibl = bot.insider_buy_line(r)
    # ⚖️ صياغة صادقة (تدقيق): الفراغ يعني «لم نجد شراءً مؤكَّدًا ضمن ما فحصناه» —
    # لا «لا يوجد شراء داخلي» (نفحص آخر مستندَين فقط وقد يتعذّر الجلب).
    L.append(_ibl or "📄 شراء داخلي: — (لا شراء مؤكَّد ضمن آخر مستندَي Form 4 · "
                     "أو تعذّر الجلب — ليس نفيًا قاطعًا)")
    # 🆕 الطرح الجديد حدثًا مؤسِّسًا (بطاقة فيصل MWC) — سياق
    _ofe = r.get("offering_event") or {}
    if _ofe.get("date"):
        L.append(f"🆕 طرح جديد: {_ofe.get('form', '')} — {_ofe['date']} "
                 "(حدث مؤسِّس يعامله فيصل كالتقسيم)")
    # 📉 «خبره عدم قبوله = هبوط» (فيصل MBRX) — مرجعه من شمعة الحدث نفسها
    _ln = bot.news_rejected_line(r.get("news_acc"))
    if _ln:
        L.append(_ln)
    # 🔁 تقسيمات متكررة = نَفَس قصير (قرينة فيصل §P4 — عرض/تحذير فقط)
    _sf = bot._split_freq_line(r.get("split_freq"))
    if _sf:
        L.append(_sf)
    # بصمة طريقة الارتفاع (سياق)
    bh = r.get("behav") or {}
    if bh.get("score") is not None:
        L.append("")
        L.append(f"🧬 طريقة الارتفاع: {bh['score']}/100 · {bh.get('label', '')}")

    # ===== 📊 التحليل كسهم ارتكاز (طلب المستخدم: كل البوابات حتى لو سقط مبكرًا) =====
    L.append("")
    L.append("━━━━━ 📊 <b>التحليل كسهم ارتكاز</b> ━━━━━")
    # البوابات بتقسيمها الصادق (مسكة المالك 2026-08-08 «13 بوابة هذي أصلًا من
    # البوابات اللي حنا مسوينها مب اللي من فيصل»): صلبة ترفض (أرقامها من ظرف
    # كتالوج فيصل · الشورت/الفلوت بقرار المالك) · لينة نقص لا رفض · «معلومة»
    # خرجت بقياس الكاتالوج. تُقيَّم مستقلة وتظهر كاملة حتى لو سقط على صلبة
    # (طلب المستخدم الأصلي باقٍ). العرض المشترك في analyze_one.render_gate_lines.
    gates = r.get("gates") or []
    if gates:
        import analyze_one as AO
        # 🧭 «الهبوط الصادق» (مسكة المالك 2026-08-08): يُمرَّر من هنا لأن هذي
        # نقطة النداء التي تملك التقسيمات فعلًا (تُجلب أصلًا لتكرار التقسيم) —
        # فصفر نداء شبكي إضافي. غيابُه (سهم غير مقسّم) ⇒ صفر سطر.
        L += AO.render_gate_lines(gates, truthful=r.get("m2_truthful"))
        L.append("")
    if r.get("interp"):        # مؤهّل بالفارز → الحالة + الدخول + الأهداف
        es = bot.entry_status(r)
        L.append("الحكم: 🎯 <b>سهم ارتكاز مؤهّل</b> · "
                 + ("🟢 جاهز للدخول الآن" if es["status"] == "ready_now"
                    else "👀 متابعة")
                 + (f" — {es['reason']}" if es["reason"] else "")
                 + bot._ready_war_suffix(r, es))   # ⚠️ تعارض «جاهز» فوق «حرب وتصريف» (كرت NAMI)
        L += bot.interp_card_lines(r["interp"])      # 🧭 الإعداد · 🎯 الرقم الحرج · 🕓 4س · ⚠️
        if r.get("tranches") and r.get("stop"):
            trs = r["tranches"]
            stop0 = r["stop"][0] if isinstance(r["stop"], (list, tuple)) else r["stop"]
            L.append("📥 دخول: " + " · ".join(f"${p:.2f}" for p in trs)
                     + f"  ·  ⛔ وقف ${stop0:.2f}")
        if all(r.get(k) for k in ("t1", "t2", "t3")):
            L.append(f"🎯 أهداف: ${r['t1']:.2f} · ${r['t2']:.2f} · ${r['t3']:.2f}")
    elif r.get("analysis_error"):
        # 14د (إصلاح تدقيق 2026-07-12): انهيار التحليل كان يُعرض حكمًا سلبيًا
        # واثقًا «ليس ارتكازًا» — الآن يُصرَّح بالتعذّر (تعذّر ≠ رفض).
        L.append("الحكم: ⚠️ <b>تعذّر تقييمه كارتكاز</b> (خطأ أثناء التحليل — "
                 "ليس رفضًا؛ أعد المحاولة أو افحص السجل)")
    else:
        why = r.get("reject_reason") or "لم يجتز بوابة صلبة (انظر ❌ أعلاه)"
        L.append(f"الحكم: ❌ <b>ليس سهم ارتكاز مؤهّلًا حاليًا</b> "
                 f"(أول سبب: {why})")
        L.append("<i>القرائن أعلاه عن اليد تبقى صالحة — لكن الفارز لا يرشّحه الآن "
                 "كارتكاز.</i>")
    L.append("")
    # تذييل صادق حسب المصدر الفعلي لسطر «تدفق الأوامر» أعلاه (order_snapshot يوسمه):
    # مع اشتراك Polygon = تدفق حي فعلي (شراء/بيع + عرض/طلب)؛ بدونه = لقطة bid/ask فقط.
    if "تدفق حي" in (r.get("order_flow") or ""):
        L.append("ℹ️ كشف/تحذير نوعي — علامات اشتباه بيد نشطة، ليست توصية ولا تُرجّح "
                 "السهم بالفرز. «تدفق الأوامر» أعلاه حي من Polygon (شراء/بيع + عرض/طلب)؛ "
                 "عمق L2 الكامل (كل مستويات الأوامر) غير مستعمل.")
    else:
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
         "h4_levels": diag.get("h4_levels"),
         "borrow_fee": diag.get("borrow_fee"),              # 🔒 الاقتراض (فيصل: سكويز)
         "shares_available": diag.get("shares_available"),
         "short_interest": diag.get("short_interest"),      # 📊 SI الرسمي (🎬 فيديو DSY)
         "days_to_cover": diag.get("days_to_cover"),        # 📊 أيام التغطية (🎬 DSY)
         "kst4": diag.get("kst4"),                          # 🎬 KST 4س (حالة زخم)
         "upcoming_events": diag.get("upcoming_events"),    # 📅 أحداث معلنة قادمة
         # 🧾 بطاقة فيصل الفرزية (2026-07-27): بدونها كانت أسطر العرض ميتة وتقول
         # «لا إفصاح شراء» كأنها حقيقة (لقّاها التدقيق الخصومي).
         "insider_buys": diag.get("insider_buys"),          # 📄 Form 4 (شراء داخلي)
         "offering_event": diag.get("offering_event")}      # 🆕 طرح جديد (حدث مؤسِّس)
    try:
        # 📉 «خبره عدم قبوله» + «÷2 على المستوى السائد» — يلزمهما الإطار اليومي وهو
        # متاح هنا (مسار الفرز يحسبهما في التحديث اليومي حيث الشمعة متوفّرة).
        r["news_acc"] = bot.news_acceptance(df, bot._latest_event_date(r))
    except Exception:
        pass
    try:
        r["behav"] = bot.behavior_rise_profile(df)     # بصمة اليومي
        r["pump_scar"] = bot.group_pump_scar(df)       # رفعة القروب/كسر الدعوم
        r["fsto_osc"] = bot.fsto_oscillation(          # 🌀 FSTO قوة التذبذب (للدمج مع التدفق)
            bot.full_stoch(df["High"], df["Low"], df["Close"])[0])
    except Exception:
        pass
    # 📊 تدفق الأوامر (Polygon حي · احتياط Yahoo · فاشل-آمن → «—» لا يعيق الفحص)
    try:
        r["order_flow"] = bot.order_snapshot(sym)
    except Exception:
        r["order_flow"] = None
    # 🕳️ لقطة NBBO الخام + ملخّص الطبعات لقرائن N5/N6/N7 (§P2 + دروس 2026-07-20 —
    # with_prints=True فحص اليد فقط، صفر نداء إضافي · فاشل-آمن → None)
    try:
        r["flow_raw"] = bot.polygon_flow(sym, with_prints=True)
    except Exception:
        r["flow_raw"] = None
    # 🔁 تكرار التقسيم العكسي في آخر سنة (قرينة فيصل §P4 — فاشل-آمن → 0)
    sp = None
    try:
        sp = bot.yf.Ticker(sym).splits if bot.yf is not None else None
        r["split_freq"] = (bot._split_frequency(sp, dt.date.today())
                           if sp is not None and len(sp) else 0)
    except Exception:
        r["split_freq"] = 0
    # 🎯 مرجع الـ÷2 لـ«أهداف الشورت» = **قمة ما بعد آخر تقسيم عكسي** (`_post_split_high`،
    # مرجع فيصل الحرفي: JEM 6.90÷2=3.45). مفتاح **خاصّ بالمقسّم** لا عامّ: سهم غير مقسّم
    # ⇒ None ⇒ يُطبع «—» ولا يُختلق هدف هبوط على ارتكاز عادي (تدقيق الخلط 2026-07-27).
    try:
        r["split_ref"] = (bot._post_split_high(df["High"], sp, df.index[-1])
                          if sp is not None and len(sp) else None)
    except Exception:
        r["split_ref"] = None
    # 🧭 مرجع «الهبوط الصادق» لسطر M2 — **بنافذة 252 حرفيًّا كما يقيس الفارز**
    # (لا كامل التاريخ كمرجع الـ÷2 أعلاه، وإلا صار «الصادق» بمقياسٍ ثالث).
    # عرض/تشخيص فقط · فاشل-آمن ⇒ None فلا سطر.
    try:
        _m2ref = (bot._post_split_high(df["High"].tail(252), sp, df.index[-1])
                  if sp is not None and len(sp) else None)
        r["m2_truthful"] = ({"price": float(df["Close"].iloc[-1]), "ref": _m2ref,
                             "floor": bot.CONFIG["MIN_DROP_FLOOR"],
                             "cap": bot.CONFIG["MAX_DROP_PCT"]}
                            if _m2ref else None)
    except Exception:
        r["m2_truthful"] = None
    # (🔬 التجميع الصامت أُزيل — تجربة T-ACC فشلت بالسنتين؛ لا نجلبه ولا نعرضه)
    # مؤهّل ارتكاز؟ (interp + دخول/أهداف لو مرّ) · وإلا السبب الأول
    try:
        bot._REJECT_STATS.clear()
        official = bot.analyze_ticker(sym, df)
        if official:
            # ⚠️ **إصلاح 2026-07-27 (تدقيق «أعلى مستوى»):** كنّا ننسخ تسعة مفاتيح فقط
            # ثم نبني التفسير — و`build_interpretation` تقرأ **ستّة أخرى** غائبة عن `r`
            # (bars_after · gaps_above · liberation · recent_split · sec_filings ·
            # trendline). النتيجة **مُثبَتة بالتشغيل**: «الرقم الحرج» يخرج مختلفًا عن
            # الكرت، وسطر «⚠️ الخطر» يختفي كليًّا — وهذا يخالف قفل «الفحص اليدوي =
            # الأساسي». (المسار اليومي و`analyze_one` سالمان: `enrich` تعيد بناء
            # التفسير على سجلٍّ كامل — وحدَه فحص اليد كان يناديها مباشرةً.)
            for k in ("pivot", "tranches", "stop", "key_levels",
                      "t1", "t2", "t3", "warnings", "soft_fails",
                      "bars_after", "gaps_above", "liberation"):
                r[k] = official.get(k)
            for k in ("recent_split", "sec_filings"):     # من enrich على diag
                r[k] = diag.get(k)
            try:                                          # §10 — كما يفعل analyze_one
                r["trendline"] = bot.descending_trendline(df, r.get("price") or 0)
            except Exception:
                r["trendline"] = None
            # (أُزيل سطران ميّتان كانا يكتبان h4_levels على `official` بينما التفسير
            #  يُبنى من `r`، و`official` لا يُقرأ بعدها إطلاقًا.)
            r["interp"] = bot.build_interpretation(r)
        elif getattr(bot, "_REJECT_STATS", None):
            r["reject_reason"] = " · ".join(f"{k}={v}"
                                            for k, v in bot._REJECT_STATS.items())
            # 🧭 يُمرَّر اسمُ الجدار للسطر الصادق ليكشف التعارض صراحةً
            # («فوق السقف» مُسجَّلًا والصدقُ «تحت الأرضية») — عرض فقط.
            if isinstance(r.get("m2_truthful"), dict):
                r["m2_truthful"]["reason"] = r["reject_reason"]
    except Exception as e:
        # 14د: كان `pass` صامتًا فيُعرض انهيارُ التحليل حكمًا سلبيًا واثقًا.
        bot.log(f"⚠️ فحص اليد: انهار تحليل الارتكاز لـ{sym}: {e}")
        r["analysis_error"] = True
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
