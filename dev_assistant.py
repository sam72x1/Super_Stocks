# -*- coding: utf-8 -*-
"""
==========================================================
أداة التطوير (Dev Assistant) — وحدة مستقلة قابلة لإعادة الاستخدام
==========================================================
مستخرجة من Super_stock.py (مشروع أسهم الارتكاز) لتُستعمل في **بوت ثانٍ**.

تحلّل الصفقات المحسومة المتراكمة وتُنتج تقرير أداء يتعلّم من نتائج بوتك:
  • نسبة النجاح الكلية + **بالشرائح** (قائمة A/B · قطاع · RSI · فلوت · شورت · RR · إشارة)
  • أنماط الخاسرين (أي شريحة/قطاع يخسر أكثر)
  • عمق الأهداف (t1/t2/t3) + متوسط زمن الوصول للهدف
  • 👻 الفرص الفائتة (مرفوض صعد ≥ نسبة)
  • 💥 كاشف الانفجارات (اختياري — يحتاج دالة فرز من بوتك)
  • 💡 اقتراحات ضبط (اقتراح فقط — لا يغيّر إعدادات)
  • 📎 تصدير CSV (اختياري)

التصميم لإعادة الاستخدام:
  - **بلا CONFIG/globals**: كل الإعدادات ثوابت أعلى الملف، والمدخلات تُمرَّر صراحةً.
  - **التبعيات الخارجية تُمرَّر كدوال**: دالة الفرز (`analyze_fn`) ودالة إرسال
    الملفات (`send_document_fn`) — فلا تربطك ببوت معيّن.
  - **تبعية واحدة اختيارية**: pandas (للـCSV فقط). الباقي مكتبة قياسية.

النصوص HTML-آمنة لتيليجرام (`parse_mode=HTML`).

----------------------------------------------------------
بنية البيانات المتوقّعة (wl — قاموس حالة بوتك)
----------------------------------------------------------
wl = {
  "stocks":  [ سجل_صفقة, ... ],   # القائمة النشطة الآن
  "removed": [ سجل_صفقة, ... ],   # ما خرج (هدف/ستوب)
  "history": [ {"stocks": [سجل_صفقة, ...]}, ... ],  # أرشيف أسابيع سابقة (اختياري)
  "explosions": [ سجل_انفجار, ... ],               # يملؤه accumulate_explosions (اختياري)
}

سجل_صفقة (كل الحقول اختيارية — الموجود يُحلَّل، الغائب يُتجاوز):
  symbol        : رمز السهم (نص)
  tier          : "A" أو "B" (تصنيف القائمة) — للتشريح حسب القائمة
  sector        : القطاع بالإنجليزي (يُعرّب تلقائيًا) مثل "Technology"
  rsi           : قيمة RSI عند الدخول (رقم)
  float         : الفلوت بالأسهم (رقم، مثل 1_890_000)
  short         : حجم الشورت (رقم)
  rr            : العائد/المخاطرة (رقم، مثل 2.3)
  flags         : قائمة إشارات نصية مثل ["⚡ دخول المضارب", "🚀 تحرر(...)"]
  max_gain_pct  : أقصى ربح وصله السهم % (رقم) — لحساب المتوسط
  hit           : "t1"/"t2"/"t3" لو حقّق هدفًا (= صفقة رابحة)، وإلا None
  status        : "stopped" لو ضرب الستوب (= خاسرة لو بلا hit)
  added         : تاريخ الدخول ISO "YYYY-MM-DD" (لحساب زمن الوصول)
  hit_date      : تاريخ تحقيق الهدف ISO (لحساب زمن الوصول)
  removal_reason: سبب الخروج (نص، للـCSV)

سجل_فرصة_فائتة (قائمة missed التي تمرّرها):
  {"symbol": نص, "reason": كود_سبب_الرفض, "gain_10d": صعود% بعد الرفض}
  ملاحظة: أكواد الرفض التي تبدأ بـ"M1_"/"M2_"/"M3_" تُعدّ «ليست ارتكازًا أصلًا»
  (رفض صحيح). عدّلها في `_is_identity_reason` بما يناسب أكواد بوتك.

سجل_انفجار (يملؤه accumulate_explosions):
  {"symbol", "date", "expl_date", "gain", "reason", "was_pivot"}
==========================================================
"""
import datetime as dt

try:
    import pandas as pd          # للـCSV فقط (اختياري)
except Exception:                # pragma: no cover
    pd = None


# ==========================================================
# الإعدادات (ثوابت — عدّلها كما يناسب بوتك)
# ==========================================================
DEV_MIN_SAMPLE = 10        # أقل عدد صفقات محسومة قبل أن تكون الأرقام ذات معنى
MISSED_RISE_PCT = 30.0     # مرفوض صعد ≥ هذا = فرصة فائتة (يُعرض في التقرير)
EXPLOSION_PCT = 50.0       # قفزة يوم واحد ≥ هذا = انفجار نحلّله
EXPLOSION_LOOKBACK = 5     # نبحث عن يوم الانفجار في آخر N جلسة
EXPLOSION_KEEP_DAYS = 30   # نحتفظ بسجل الانفجارات آخر N يوم
MIN_BARS = 120             # أقل عدد شموع مقبول لتحليل شريحة تاريخية
SEG_MIN_N = 3              # أقل عدد صفقات في الشريحة حتى تُعرض


def log(msg: str) -> None:
    """خطّاف تسجيل — استبدله بمسجّل بوتك إن رغبت (افتراضيًا print)."""
    print(msg)


# ==========================================================
# مساعدات صغيرة (HTML-آمن + تعريب القطاع)
# ==========================================================
def esc(s) -> str:
    """تعقيم النصوص الخارجية حتى لا تكسر HTML تيليجرام."""
    return (str(s).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


SECTOR_AR = {
    "Technology": "تقنية",
    "Communication Services": "اتصالات وإعلام",
    "Healthcare": "رعاية صحية",
    "Financial Services": "خدمات مالية",
    "Financials": "خدمات مالية",
    "Consumer Cyclical": "استهلاكي تدويري",
    "Consumer Defensive": "استهلاكي دفاعي",
    "Energy": "طاقة",
    "Industrials": "صناعات",
    "Basic Materials": "مواد أساسية",
    "Real Estate": "عقارات",
    "Utilities": "مرافق",
    "Biotechnology": "تقنية حيوية",
}


def ar_sector(s):
    """يرجّع القطاع بالعربي إن وُجد، وإلا الأصل كما هو."""
    return SECTOR_AR.get(s, s) if s else s


# ==========================================================
# جمع الصفقات المحسومة + حساب نسبة النجاح
# ==========================================================

def _alert_hit_from_status(status: str):
    """يرجّع t1/t2/t3 من حالة سجل التنبيهات hit_t*، وإلا None."""
    st = str(status or "")
    return st.replace("hit_", "") if st.startswith("hit_t") else None


def _collect_closed_alerts(alert_data) -> list:
    """يجمع الصفقات المحسومة من alerts_history.json (اختياري، طبقة تقارير فقط)."""
    if not alert_data:
        return []
    alerts = alert_data.get("alerts", alert_data) if isinstance(alert_data, dict) else alert_data
    rows = []
    for a in alerts or []:
        status = str(a.get("status") or "")
        hit = _alert_hit_from_status(status)
        won = bool(hit)
        lost = status == "stopped"
        if not (won or lost):
            continue
        r = dict(a)
        r["entry_ref"] = r.get("entry_ref", r.get("price"))
        r["hit"] = hit
        r["hit_date"] = r.get("hit_date") or r.get("result_date")
        r["added"] = r.get("added") or r.get("date")
        if lost and not r.get("removal_reason"):
            r["removal_reason"] = "ضرب الستوب"
        r["_win"] = won
        rows.append(r)
    return rows


def _collect_closed(wl: dict) -> list:
    """يجمع كل الصفقات المحسومة (رابحة=حقّقت هدفًا · خاسرة=ضربت الستوب بلا هدف)
    من الأرشيف التراكمي + الأسبوع الحالي. كل صف يحمل سماته عند الدخول."""
    rows = []
    seen = set()
    buckets = list(wl.get("history") or [])
    buckets.append({"stocks": (wl.get("removed") or []) + (wl.get("stocks") or [])})
    for wk in buckets:
        for s in wk.get("stocks", []):
            won = bool(s.get("hit"))
            lost = (s.get("status") == "stopped") and not won
            if not (won or lost):
                continue
            key = (s.get("symbol"), s.get("entry_ref"))
            if key in seen:                 # تفادي التكرار بين الأرشيف والحالي
                continue
            seen.add(key)
            r = dict(s)
            r["_win"] = won
            rows.append(r)
    return rows


def _wr(rows: list):
    """(عدد، نسبة النجاح %، متوسط أقصى ربح%) لمجموعة صفقات."""
    n = len(rows)
    if not n:
        return (0, 0.0, 0.0)
    wins = sum(1 for r in rows if r["_win"])
    avg_mg = sum((r.get("max_gain_pct") or 0) for r in rows) / n
    return (n, wins / n * 100.0, avg_mg)


def _is_identity_reason(reason) -> bool:
    """هل سبب الرفض = «ليس النمط المطلوب أصلًا» (رفض صحيح لا يدل على تشدّد)؟
    في مشروع الارتكاز: بوابات الهوية/البنية M1(سعر)/M2(هبوط)/M3(انفجار) +
    M4_base (قاعدة واسعة/شاذّة = ليست تجميعًا ضيّقًا، بنيوية مثل M1-M3). أما
    M4_انفجر_فعلاً («فات القطار») وRSI/النواقص فتبقى «متحرّكة» قابلة للمراجعة.
    عدّل البادئات بما يناسب أكواد رفض بوتك."""
    r = str(reason)
    return r.startswith(("M1_", "M2_", "M3_")) or r.startswith("M4_base")


# ==========================================================
# التقرير الرئيسي: مساعد التطوير
# ==========================================================
def build_dev_assistant_report(wl: dict, missed: list = None,
                               alert_data: dict = None) -> str:
    """🔬 يحلّل الصفقات المحسومة ويطلّع تشخيص الأداء بالشرائح + أنماط الفشل
    + الفرص الفائتة + الانفجارات + اقتراحات ضبط (اقتراح فقط — لا يغيّر إعدادات).

    wl     : قاموس حالة بوتك (انظر البنية أعلى الملف).
    missed : قائمة الفرص الفائتة (اختياري) — [{symbol, reason, gain_10d}, ...].
    alert_data : محتوى alerts_history.json اختياريًا؛ يضم صفقات محسومة من نظام
                 التتبع القديم/الموازي حتى لا تظهر «0» كاذبة في تقرير التطوير.
    يرجّع نص HTML جاهز للإرسال على تيليجرام.
    """
    missed = missed or []
    rows = _collect_closed(wl) + _collect_closed_alerts(alert_data)
    n, wr, avg = _wr(rows)
    head = ["🔬 <b>مساعد التطوير — تحليل أداء المنهجية</b>",
            f"صفقات محسومة متراكمة: <b>{n}</b>"]

    def _missed_block():
        if not missed:
            return []
        # تصنيف: بوابات الهوية = «ليس النمط أصلًا» (رفض صحيح). الباقي = نمط فعلي
        # تحرّك أو حدّي → هو الإشارة الحقيقية للمراجعة.
        moved = [m for m in missed if not _is_identity_reason(m["reason"])]
        not_pivot = [m for m in missed if _is_identity_reason(m["reason"])]
        out = [f"\n👻 <b>فرص فائتة (مرفوض صعد {int(MISSED_RISE_PCT)}% أو أكثر)</b>",
               f"   📌 نمط تحرّك (راجِع): <b>{len(moved)}</b> · "
               f"🗑️ ليس النمط (تجاهل صحيح): {len(not_pivot)}"]
        if moved:
            rc = {}
            for m in moved:
                rc[m["reason"]] = rc.get(m["reason"], 0) + 1
            out.append("   أسباب النمط المتحرّك: "
                       + "، ".join(f"{k} ({v})" for k, v in
                                   sorted(rc.items(), key=lambda x: -x[1])[:3]))
            for m in sorted(moved, key=lambda x: -x["gain_10d"])[:6]:
                out.append(f"   • {m['symbol']}: +{m['gain_10d']:.0f}% — "
                           f"تحرّك ({m['reason']})")
            out.append("   ↳ هذي مرشّحات للمراجعة؛ تأكّد بوتك يلتقط أقواها.")
        else:
            out.append("   ✅ لا نمط فعلي فاتنا — كل الفائتة ليست من نمطنا.")
        return out

    def _explosions_block():
        ex = wl.get("explosions") or []
        if not ex:
            return []
        was_target = [e for e in ex if e.get("was_pivot")]
        junk = [e for e in ex if not e.get("was_pivot")]
        out = [f"\n💥 <b>انفجارات يومية ({int(EXPLOSION_PCT)}% أو أكثر) — "
               f"{len(ex)} سهم</b>",
               f"   🎯 كان نمطنا وفاتنا: {len(was_target)} · "
               f"🗑️ عشوائية (صح تجاهلناها): {len(junk)}"]
        if was_target:
            rc = {}
            for e in was_target:
                rc[e["reason"]] = rc.get(e["reason"], 0) + 1
            out.append("   سبب التفويت: "
                       + "، ".join(f"{k} ({v})" for k, v in
                                   sorted(rc.items(), key=lambda x: -x[1])[:3]))
            for e in sorted(was_target, key=lambda x: -x["gain"])[:6]:
                out.append(f"   • {e['symbol']}: +{e['gain']:.0f}% — كان نمطنا، "
                           f"رُفض بـ{e['reason']}")
            out.append("   ↳ راجِع هذي البوابة — قد تكون متشدّدة وتفوّت فرصًا.")
        return out

    if n < DEV_MIN_SAMPLE:
        head.append(f"⏳ صفقات محسومة قليلة (أقل من {DEV_MIN_SAMPLE}) — "
                    "تشخيص الأداء يتراكم أسبوعيًا (~10+ صفقة).")
        head += _missed_block()           # الفرص الفائتة تظهر فورًا (مستقلة)
        head += _explosions_block()       # الانفجارات المفقودة (مستقلة)
        head.append("\n⚠️ <i>أداة تطوير ذاتي — ليست توصية.</i>")
        return "\n".join(head)

    wins = [r for r in rows if r["_win"]]
    losses = [r for r in rows if not r["_win"]]
    head.append(f"النجاح الكلي: <b>{wr:.0f}%</b> ({len(wins)}✅ / {len(losses)}🛑) "
                f"· متوسط أقصى ربح {avg:+.0f}%")

    def seg(title, keyfn):
        groups = {}
        for r in rows:
            k = keyfn(r)
            if k is None:
                continue
            groups.setdefault(k, []).append(r)
        items = [(k, _wr(v)) for k, v in groups.items() if _wr(v)[0] >= SEG_MIN_N]
        if not items:
            return []
        items.sort(key=lambda x: -x[1][1])
        out = [f"\n📊 <b>{title}</b>"]
        for k, (gn, gwr, gmg) in items:
            out.append(f"   • {esc(str(k))}: {gwr:.0f}% نجاح "
                       f"({gn} صفقة · {gmg:+.0f}% متوسط)")
        return out

    def _bucket(v, edges):
        if v is None:
            return None
        for lo, hi, lbl in edges:
            if lo <= v < hi:
                return lbl
        return None

    # (1) تشخيص الأداء بالشرائح
    body = []
    body += seg("حسب القائمة", lambda r: ("A صارمة" if r.get("tier") == "A"
                                          else "B مراقبة") if r.get("tier") else None)
    body += seg("حسب القطاع", lambda r: ar_sector(r.get("sector")) or None)
    body += seg("حسب RSI عند الدخول", lambda r: _bucket(
        r.get("rsi"), [(0, 28, "27 أو أقل (مثالي)"), (28, 33, "28-32"),
                       (33, 41, "33-40"), (41, 200, "أعلى من 40")]))
    body += seg("حسب الفلوت", lambda r: _bucket(
        (r.get("float") or 0) / 1e6 if r.get("float") else None,
        [(0, 10, "أقل من 10م"), (10, 30, "10-30م"), (30, 1e9, "أكثر من 30م")]))
    body += seg("حسب الشورت", lambda r: _bucket(
        r.get("short"),
        [(0, 20000, "20ألف أو أقل"), (20000, 40000, "20-40ألف"), (40000, 1e12, "أعلى من 40ألف")]))
    body += seg("حسب العائد/المخاطرة", lambda r: _bucket(
        r.get("rr"), [(0, 1.5, "أقل من 1.5×"), (1.5, 2.5, "1.5-2.5×"), (2.5, 99, "2.5× أو أكثر")]))

    # إشارات: نسبة النجاح عند وجود كل إشارة
    flag_names = set()
    for r in rows:
        for f in (r.get("flags") or []):
            flag_names.add(f.split("(")[0].strip())
    flag_rows = []
    for fn in flag_names:
        present = [r for r in rows if any(
            (f.split("(")[0].strip() == fn) for f in (r.get("flags") or []))]
        gn, gwr, _ = _wr(present)
        if gn >= SEG_MIN_N:
            flag_rows.append((fn, gn, gwr))
    if flag_rows:
        flag_rows.sort(key=lambda x: -x[2])
        body.append("\n🚦 <b>حسب الإشارة (نسبة النجاح عند وجودها)</b>")
        for fn, gn, gwr in flag_rows:
            body.append(f"   • {fn}: {gwr:.0f}% ({gn})")

    # (2) أنماط الفشل
    fails = ["\n🛑 <b>أنماط الخاسرين</b>"]
    if losses:
        sec_cnt, flag_cnt = {}, {}
        for r in losses:
            sc = ar_sector(r.get("sector"))
            if sc:
                sec_cnt[sc] = sec_cnt.get(sc, 0) + 1
            for f in (r.get("flags") or []):
                nm = f.split("(")[0].strip()
                flag_cnt[nm] = flag_cnt.get(nm, 0) + 1
        tier_l = sum(1 for r in losses if r.get("tier") == "B")
        fails.append(f"   • {tier_l}/{len(losses)} من الخاسرين كانوا B مراقبة")
        top_sec = sorted(sec_cnt.items(), key=lambda x: -x[1])[:2]
        if top_sec:
            fails.append("   • أكثر قطاعات الخسارة: "
                         + "، ".join(f"{esc(str(k))} ({v})" for k, v in top_sec))
    body += fails if len(fails) > 1 else []

    # عمق الأهداف: أي هدف نوصله؟ وكم يطول؟ (هل أهدافنا واقعية / نخرج بدري؟)
    if wins:
        depth = {"t1": 0, "t2": 0, "t3": 0}
        for w_ in wins:
            h = w_.get("hit")
            if h in depth:
                depth[h] += 1
        days = []
        for w_ in wins:
            try:
                a = dt.date.fromisoformat(str(w_.get("added")))
                hd = dt.date.fromisoformat(str(w_.get("hit_date")))
                days.append((hd - a).days)
            except Exception:
                pass
        dep = ["\n🎯 <b>عمق الأهداف (الرابحون)</b>",
               f"   t1 فقط: {depth['t1']} · t2: {depth['t2']} · t3: {depth['t3']}"]
        if depth["t2"] + depth["t3"] == 0 and depth["t1"] >= 4:
            dep.append("   ↳ نوصل t1 فقط دائمًا — قد تكون t2/t3 بعيدة، فكّر بتقريبها.")
        if days:
            dep.append(f"   متوسط زمن الوصول للهدف: {sum(days)/len(days):.0f} يوم")
        body += dep

    body += _missed_block()           # 👻 الفرص الفائتة
    body += _explosions_block()       # 💥 الانفجارات المفقودة

    # (3) اقتراحات ضبط (اقتراح فقط — لا يغيّر إعدادات)
    sugg = ["\n💡 <b>اقتراحات ضبط (للمراجعة فقط — لا تُطبّق تلقائيًا)</b>"]
    a_rows = [r for r in rows if r.get("tier") == "A"]
    b_rows = [r for r in rows if r.get("tier") == "B"]
    an, awr, _ = _wr(a_rows)
    bn, bwr, _ = _wr(b_rows)
    if an >= 5 and bn >= 5 and awr - bwr >= 20:
        sugg.append(f"   • A ({awr:.0f}%) أفضل بوضوح من B ({bwr:.0f}%) — "
                    "فكّر بتشديد B أو تقليل وزنها.")
    hi_rsi = [r for r in rows if (r.get("rsi") or 0) > 40]
    if len(hi_rsi) >= 5 and _wr(hi_rsi)[1] < wr - 15:
        sugg.append(f"   • صفقات RSI أعلى من 40 نجاحها {_wr(hi_rsi)[1]:.0f}% (أقل من المعدل) "
                    "— فكّر بتشديد سقف RSI.")
    lo_rr = [r for r in rows if (r.get("rr") or 0) < 1.5]
    if len(lo_rr) >= 5 and _wr(lo_rr)[1] < wr - 15:
        sugg.append(f"   • صفقات RR أقل من 1.5× نجاحها {_wr(lo_rr)[1]:.0f}% — "
                    "فكّر برفع حد RR الأدنى.")
    if len(sugg) == 1:
        sugg.append("   • لا نمط واضح بعد — البيانات متّسقة أو غير كافية لاقتراح.")

    tail = ["", "⚠️ <i>أداة تطوير ذاتي تتعلّم من نتائج البوت — ليست توصية. "
            "الاقتراحات للمراجعة البشرية فقط.</i>"]
    return "\n".join(head + body + sugg + tail)


# ==========================================================
# كاشف الانفجارات (اختياري — يحتاج دالة فرز من بوتك)
# ==========================================================
def scan_explosions(history: dict, analyze_fn=None,
                    reject_reasons: dict = None, today: str = None) -> list:
    """يلتقط الأسهم التي قفزت ≥ EXPLOSION_PCT في يوم واحد (آخر EXPLOSION_LOOKBACK
    جلسة) ويصنّفها was_pivot (كانت نمطك قبل الانفجار = فاتتك) أم عشوائية.

    history       : {رمز: DataFrame يومي بأعمدة OHLC على الأقل ["Close"]}.
    analyze_fn    : دالة بوتك للفرز: analyze_fn(sym, df_slice) → غير None لو
                    كانت «نمطك» قبل يوم الانفجار. لو None → was_pivot=False دائمًا.
    reject_reasons: {رمز: سبب_عدم_الترشيح_اليوم} (اختياري، للعرض فقط).
    يعيد قائمة سجلات انفجار مرتّبة بالأكبر. (لا تحميل بيانات — يعيد استخدام history.)
    """
    reject_reasons = reject_reasons or {}
    today = today or dt.date.today().isoformat()
    out = []
    for sym, df in history.items():
        try:
            c = df["Close"].values.astype(float)
        except Exception:
            continue
        if len(c) < MIN_BARS + 1:
            continue
        look = min(int(EXPLOSION_LOOKBACK), len(c) - 1)
        # نتتبّع إزاحة اليوم k مع كل قفزة (لا نعتمد .index على قائمة مُرشَّحة).
        gains = [(k, (c[-k] / c[-k - 1] - 1.0) * 100.0)
                 for k in range(1, look + 1) if c[-k - 1] > 0]
        if not gains:
            continue
        k_max, g = max(gains, key=lambda p: p[1])
        if g < EXPLOSION_PCT:
            continue
        idx = len(c) - k_max                      # موقع يوم الانفجار (مطلق، صحيح)
        try:
            expl_date = df.index[idx].date().isoformat()
        except Exception:
            expl_date = today
        reason = reject_reasons.get(sym, "—")     # لماذا لم يُرشّح اليوم
        was_pivot = False
        slice_df = df.iloc[:idx]                   # بياناته قبل يوم الانفجار
        if analyze_fn is not None and len(slice_df) >= MIN_BARS:
            try:
                was_pivot = analyze_fn(sym, slice_df) is not None
            except Exception:
                was_pivot = False
        out.append({"symbol": sym, "date": today, "expl_date": expl_date,
                    "gain": round(g, 0), "reason": reason,
                    "was_pivot": bool(was_pivot)})
    out.sort(key=lambda x: -x["gain"])
    return out


def accumulate_explosions(wl: dict, history: dict, analyze_fn=None,
                          reject_reasons: dict = None) -> int:
    """يضيف انفجارات اليوم لسجل تراكمي في wl["explosions"] (dedup symbol+expl_date،
    يحتفظ بآخر EXPLOSION_KEEP_DAYS يوم). يُعرض في build_dev_assistant_report."""
    found = scan_explosions(history, analyze_fn, reject_reasons)
    log_ex = wl.setdefault("explosions", [])

    def _ek(e):
        return (e["symbol"], e.get("expl_date", e.get("date")))

    seen = {_ek(e) for e in log_ex}
    for e in found:
        if _ek(e) not in seen:
            log_ex.append(e)
            seen.add(_ek(e))
    cutoff = (dt.date.today()
              - dt.timedelta(days=int(EXPLOSION_KEEP_DAYS))).isoformat()
    wl["explosions"] = [e for e in log_ex if e.get("date", "") >= cutoff][-300:]
    return len(found)


# ==========================================================
# تصدير CSV (اختياري)
# ==========================================================
def _write_csv_file(rows: list, prefix: str):
    """يكتب صفوفًا إلى CSV ويرجع المسار (أو None لو فاضي/فشل/لا pandas)."""
    if not rows or pd is None:
        return None
    try:
        fn = f"{prefix}_{dt.date.today().isoformat()}.csv"
        pd.DataFrame(rows).to_csv(fn, index=False, encoding="utf-8-sig")
        return fn
    except Exception as e:
        log(f"⚠️ كتابة CSV {prefix}: {e}")
        return None


def export_weekly_csvs(wl: dict, picks: list, missed: list = None,
                       send_document_fn=None, alert_data: dict = None) -> list:
    """يصدّر 3 ملفات CSV: الصفقات المحسومة · الإشارات الحالية · الفرص الفائتة.

    picks            : القائمة الحالية (لكل عنصر: symbol/tier/sector/.../pivot/stop/t1..t3).
    missed           : قائمة الفرص الفائتة (اختياري).
    send_document_fn : دالة إرسال اختيارية send_document_fn(filepath, caption).
                       لو None → تُكتب الملفات فقط وتُرجَع مساراتها.
    alert_data       : محتوى alerts_history.json اختياريًا لإدخال صفقات نظام التتبع.
    يرجّع قائمة مسارات الملفات المكتوبة.
    """
    missed = missed or []
    d = dt.date.today().isoformat()
    cols_t = ("symbol", "tier", "sector", "rsi", "float", "short", "drop_pct",
              "best_spike", "rr", "score", "max_gain_pct", "status", "hit",
              "hit_date", "added", "removal_reason")
    trades = [{k: r.get(k) for k in cols_t}
              for r in (_collect_closed(wl) + _collect_closed_alerts(alert_data))]

    def _stop0(r):
        st = r.get("stop")
        try:
            return round(st[0], 2)
        except Exception:
            return st

    signals = [{"symbol": r.get("symbol"), "tier": r.get("tier"),
                "sector": r.get("sector"), "rsi": r.get("rsi"),
                "float": r.get("float"),
                # تدرّج الشورت: حجم Fintel ← FINRA ← (نسبة Yahoo بعمود منفصل)،
                # فلا يظهر فارغًا رغم توفّر short_pct.
                "short": ((r.get("fintel") or {}).get("short_volume")
                          or r.get("finra_short")),
                "short_pct": r.get("short_pct"),
                "drop_pct": round(r.get("drop_pct", 0) or 0, 1),
                "best_spike": round(r.get("best_spike", 0) or 0, 0),
                "rr": r.get("rr"), "score": r.get("score"),
                "pivot": r.get("pivot"), "stop": _stop0(r),
                "t1": r.get("t1"), "t2": r.get("t2"),
                "t3": r.get("t3")} for r in (picks or [])]

    written = []
    for rows, prefix, cap in [
            (trades, "trades", "📎 الصفقات المحسومة ونتائجها"),
            (signals, "signals", "📎 كل الإشارات (القائمة الحالية)"),
            (list(missed), "missed", "📎 الفرص الفائتة (مرفوض صعد)")]:
        fn = _write_csv_file(rows, prefix)
        if fn:
            written.append(fn)
            if send_document_fn is not None:
                try:
                    send_document_fn(fn, f"{cap} — {d}")
                except Exception as e:
                    log(f"⚠️ إرسال {prefix}: {e}")
    return written


# ==========================================================
# مثال استخدام (تشغيل مباشر = عرض تجريبي بلا إنترنت)
# ==========================================================
if __name__ == "__main__":
    demo_wl = {
        "stocks": [
            {"symbol": "AAA", "tier": "A", "sector": "Technology", "rsi": 26,
             "float": 8_000_000, "short": 15000, "rr": 2.6, "max_gain_pct": 48,
             "hit": "t2", "added": "2026-06-01", "hit_date": "2026-06-09",
             "flags": ["⚡ دخول المضارب"]},
            {"symbol": "BBB", "tier": "B", "sector": "Healthcare", "rsi": 44,
             "float": 25_000_000, "short": 33000, "rr": 1.3, "max_gain_pct": -7,
             "status": "stopped", "added": "2026-06-02", "flags": []},
        ],
        "removed": [
            {"symbol": "CCC", "tier": "A", "sector": "Energy", "rsi": 30,
             "float": 6_000_000, "short": 12000, "rr": 3.1, "max_gain_pct": 65,
             "hit": "t1", "added": "2026-05-20", "hit_date": "2026-05-27",
             "flags": ["🚀 تحرر"]},
        ],
        "explosions": [
            {"symbol": "ZZZ", "gain": 80, "reason": "M9_rsi", "was_pivot": True,
             "date": "2026-06-20", "expl_date": "2026-06-18"},
        ],
    }
    demo_missed = [{"symbol": "DDD", "reason": "M9_rsi", "gain_10d": 42.0},
                   {"symbol": "EEE", "reason": "M1_price", "gain_10d": 35.0}]
    print(build_dev_assistant_report(demo_wl, missed=demo_missed))
