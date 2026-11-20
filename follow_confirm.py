#!/usr/bin/env python3
"""🔎✅ أداةُ تأكيد المتابعة (أمرُ المالك 2026-11-20).

«اكتب فيها أيّ سهمٍ ويتأكّد لو ارتكاز ولا لا ويرسلي في البوت، ولو كان ارتكاز يرسل البيانات
كاملة — المقاومة والوقف والأهداف — كأنه سهمٌ جاهز باختصار».

الحكمُ **ليس جديدًا**: يُشغَّل الفحصُ اليدويّ `analyze_one.main` نفسُه (مطابقٌ للفرز بأقفاله:
`analyze_ticker` ثمّ الإثراء ثمّ حكمُ ما بعد الإثراء) ويُلتقط ما كان سيُرسَل إلى `render_ondemand`
قبل الإرسال، ثمّ تُبنى رسالةٌ مختصرة:
  ✅ ارتكاز مؤهّل ⟵ حالتُه (جاهز/متابعة) ‏+ الكرتُ الكامل (`build_message`: الدفعات · الدعم · الوقف · الأهداف · المقاومات)
  👁️ ارتكازٌ ارتفع عن دخوله ⟵ سعرُ الرجوع المنتظَر ‏+ الكرت
  ❌ ليس ارتكازًا بشروط البوت ⟵ السببُ والبوّاباتُ الصلبة الساقطة
ومعه سطرٌ: هل السهمُ في قائمة البوت أو «تحت المتابعة» الآن.
🧰 **ثمّ على بقيّة الأدوات** (أمرُ المالك 2026-11-20 «ابي الاداة تكون تفحص السهم على كل الأدوات»): كلُّ أداةٍ بدالّة مسحها
الإنتاجيّة نفسِها على شموع هذا الرمز وحدَه (`tools_check`) ⟵ ✅ مع كرتها هي · أو ❌ ومرحلةُ السقوط من عدّادات المسح نفسِه.
عرضٌ فقط: لا يكتب حالةً ولا سجلًّا ولا يمسّ عتبةً ولا جذرًا · `FCF1`-`FCF5`.

التشغيل: `FOLLOW_CONFIRM=SXTC,YMT python follow_confirm.py` (حتى 5 رموز · رسالةٌ لكلّ رمز).
"""
import json
import os
import re

import Super_stock as bot
import analyze_one as AO

MAX_SYMBOLS = 5                      # engineering — رسالةٌ لكلّ رمز · سقفٌ يمنع إغراق المحادثة
TITLE = "🔎✅ <b>أداة تأكيد المتابعة</b>"


def parse_symbols(raw) -> list:
    """«sxtc, ymt ctnt» ⟵ ['SXTC','YMT','CTNT'] — بلا تكرار · حتى `MAX_SYMBOLS`."""
    out = []
    for t in re.split(r"[\s,،;]+", str(raw or "").upper()):
        t = t.strip().lstrip("$")
        if t and re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,9}", t) and t not in out:
            out.append(t)
    return out[:MAX_SYMBOLS]


def capture(sym: str, run=None) -> dict:
    """يشغّل `analyze_one.main` على `sym` ويلتقط مُدخَلات `render_ondemand` ورسائله **بلا إرسال**.
    يُرجع {"args": (card, gates, official, reject, pull, layers) أو None, "sent": [نصوص]}."""
    cap = {"args": None, "sent": []}
    _render0, _send0 = AO.render_ondemand, bot.send_telegram
    _env0 = os.environ.get("ANALYZE")

    def _render(result, gates, official, reject_reason=None, pullback=None, layers=None):
        cap["args"] = (result, gates, official, reject_reason, pullback, layers)
        return ""

    def _send(text, *a, **k):
        cap["sent"].append(text)
        return True
    try:
        AO.render_ondemand = _render
        bot.send_telegram = _send
        os.environ["ANALYZE"] = sym
        (run or AO.main)()
    finally:
        AO.render_ondemand, bot.send_telegram = _render0, _send0
        if _env0 is None:
            os.environ.pop("ANALYZE", None)
        else:
            os.environ["ANALYZE"] = _env0
    return cap


def membership(sym: str, wl_path: str = "weekly_watchlist.json", nw_path: str = "near_watch.json") -> str:
    """سطرُ «أين هو عند البوت الآن» من ملفّي الحالة المدفوعَين — فاشلٌ-آمن ⟵ نصٌّ فارغ."""
    try:
        wl = json.load(open(wl_path, encoding="utf-8"))
        for e in wl.get("stocks") or []:
            if (e or {}).get("symbol") == sym:
                st = "مشطوب بالوقف" if e.get("stopped") else "نشط"
                return f"📌 في قائمة البوت الأسبوعيّة منذ {e.get('added') or '—'} ({st})"
    except Exception:                                            # noqa: BLE001
        pass
    try:
        nw = json.load(open(nw_path, encoding="utf-8"))
        e = nw.get(sym) if isinstance(nw, dict) else None
        if e:
            why = " · ".join(e.get("outside") or []) or "—"
            return f"👀 تحت المتابعة منذ {e.get('first_seen') or '—'} — الناقص: {why}"
    except Exception:                                            # noqa: BLE001
        pass
    return "ℹ️ ليس في قائمة البوت ولا «تحت المتابعة» اليوم"


def build_confirm_message(sym: str, cap: dict, member: str = "") -> str:
    """الرسالةُ المختصرة من الملتقَط — نقيّة."""
    args = cap.get("args")
    if not args:                                                 # تعذّر التحليل ⟵ رسالةُ الفحص اليدويّ كما هي
        txt = (cap.get("sent") or [f"⚠️ تعذّر تحليل {sym}"])[-1]
        return f"{TITLE} — ${sym}\n\n{txt}"
    card, gates, official, reject, pull, _layers = args
    head = [f"{TITLE} — ${sym}"]
    if card.get("dq_line"):
        head.append(bot.esc(card["dq_line"]))
    if official is not None:
        try:
            card["interp"] = bot.build_interpretation(card)
            st = bot.entry_status(card) or {}
        except Exception:                                        # noqa: BLE001
            st = {}
        head.append("الحكم: ✅ <b>سهم ارتكاز — مؤهّل بشروط البوت</b>")
        if st.get("label"):
            head.append(f"الحالة: {st.get('label')}" + (f" — {st.get('reason')}" if st.get("reason") else ""))
    elif pull is not None:
        tgt = (pull.get("entry") or [None, None])[1]
        head.append("الحكم: 👁️ <b>سهم ارتكاز ارتفع عن دخوله</b> — انتظر رجوعه"
                    + (f" لسعر الدعم <b>${tgt:.2f}</b>" if isinstance(tgt, (int, float)) else ""))
    else:
        hard_bad = [g[0] for g in gates if not g[1] and AO._gate_kind(g) == "hard"]
        head.append("الحكم: ❌ <b>ليس سهم ارتكاز بشروط البوت</b>")
        head.append(f"السبب: {bot.esc(reject or '؛ '.join(hard_bad) or 'لم يجتز بوابة صلبة')}")
        if hard_bad:
            head.append("البوّابات الصلبة الساقطة: " + "، ".join(hard_bad[:6]))
        if member:
            head.append(member)
        head += ["", bot.FOOTER]
        return bot._rtl_join(head)
    if member:
        head.append(member)
    card["interp"] = bot.build_interpretation(card)
    body = bot.build_message([card], [], title="📊 <b>البيانات كاملة</b>")
    return bot._rtl_join(head) + "\n\n" + body


# ─────────────────────────── 🧰 بقيّةُ الأدوات ───────────────────────────
# أسماءُ مراحل العدّادات بترتيبها في دالّة المسح (`stage` في `scan_split_filter` و`scan_method_hunter`) ⟵ أوّلُ صفرٍ = مكانُ السقوط.
SF_STAGES = (("price", "أرضية السعر"), ("split_setup", "setup تقسيم (القمّة÷2)"), ("didnt_rise", "لم يصعد أوّل التقسيم"),
             ("seq", "ثبات الدعم الثاني"), ("entry_zone", "داخل الطلبات"), ("short_ok", "الشورت"))
MH_STAGES = (("price", "أرضية السعر"), ("window_ok", "نافذة الهبوط بعد الصعود"), ("founding", "الحدث المؤسِّس"),
             ("seq", "التسلسل (قاع ⟵ اختبار مقاومة ⟵ رجوع ⟵ ثبات)"), ("entry_zone", "منطقة الدخول"))


def first_fail(stage: dict, order) -> str:
    """أوّلُ مرحلةٍ عدّادُها صفر ⟵ اسمُها · وكلُّها عابرة ⟵ «بعد المراحل كلِّها» — نقيّة."""
    for k, name in order:
        if not int((stage or {}).get(k) or 0):
            return name
    return "بعد المراحل كلِّها (شرطٌ أخير)"


def _spy(fn, calls: set, key: str):
    def _w(*a, **k):
        calls.add(key)
        return fn(*a, **k)
    return _w


def _near_why(lst, sym):
    for n in lst or []:
        if (n or {}).get("symbol") == sym:
            return (n.get("why") or "").strip()
    return ""


def chk_split_hunter(sym, hist, sess, scan=None):
    """🪝 صيّادُ التقسيم: `scan_split_hunter` بالجالبات الإنتاجيّة نفسِها ملفوفةً بعدّاد نداء ⟵ ترتيبُ النداء يكشف مرحلةَ السقوط."""
    calls = set()
    rows = (scan or bot.scan_split_hunter)(
        hist, fetch_splits=_spy(bot._fetch_splits, calls, "splits"), fetch_float=_spy(bot._yahoo_float, calls, "float"),
        fetch_pump=_spy(bot.group_pump_scar, calls, "pump"))
    rows = [r for r in rows or [] if r.get("symbol") == sym]
    if rows:
        return True, "مطابق كامل", bot.build_split_hunter_alert(rows, today=sess)
    C = bot.CONFIG
    if "splits" not in calls:
        why = (f"لم يمرّ المرشّحَ الأوّل (سعرٌ بين ${C['SPLIT_RADAR_PRICE_MIN']:g} و${C['SPLIT_RADAR_PRICE_MAX']:g} "
               f"وهبوطُ يومٍ واحد {C['SPLIT_CLIFF_PCT']:g}% فأكثر في آخر {int(C['SPLIT_LOOKBACK_DAYS'])} جلسة)")
    elif "float" not in calls:
        nm = [n for n in (getattr(bot, "_SPLIT_NEAR_MISS", []) or []) if n.get("symbol") == sym]
        why = (f"صعد {nm[0]['rose_pct']:.0f}% بعد الحدث (الحدّ {C['SPLIT_ROSE_MAX_PCT']:g}%)" if nm else
               "لا تقسيم/طرح حديث، أو لم يصل قاع القمّة÷2، أو لم يحافظ 3 جلسات، أو صعد بعد الحدث")
    elif "pump" not in calls:
        why = f"الفلوت فوق {C['SPLIT_RADAR_FLOAT_MAX'] / 1e6:g} مليون أو مجهول"
    else:
        why = "عليه أثرُ قروب (رفعة ثمّ كسر)"
    return False, why, ""


def chk_split_filter(sym, hist, sess, scan=None):
    rows = [r for r in ((scan or bot.scan_split_filter)(hist, today=sess) or []) if r.get("symbol") == sym]
    if rows:
        tag = " (🔸 ثباتُ الدعم الثاني ناقصٌ لين)" if rows[0].get("g2_soft") else ""
        return True, "مطابق" + tag, bot.build_split_filter_alert(rows, today=sess)
    why = "توقّف عند: " + first_fail(getattr(bot, "_SPLIT_FILTER_STAGE", {}), SF_STAGES)
    nw = _near_why(getattr(bot, "_SPLIT_FILTER_NEAR", []), sym)
    return False, why + (f" — {nw}" if nw else ""), ""


def chk_method(sym, hist, sess, scan=None):
    rows = [r for r in ((scan or bot.scan_method_hunter)(hist, today=sess, fetch_h4=bot.fetch_4h) or [])
            if r.get("symbol") == sym]
    if rows:
        return True, "مطابق كامل", bot.build_method_alert(rows, today=sess)
    rel = [r for r in (getattr(bot, "_METHOD_RELAXED", []) or []) if r.get("symbol") == sym]
    ng = [r for r in (getattr(bot, "_METHOD_NOGAP", []) or []) if r.get("symbol") == sym]
    if rel or ng:
        body = bot._rtl_join(bot.method_relaxed_lines(rel) if rel else bot.method_nogap_lines(ng))
        return True, ("🟡 مستوى مخفّف (تجاوز الدخول قليلًا)" if rel else "🏷️ بلا هدف فجوة"), body
    why = "توقّف عند: " + first_fail(getattr(bot, "_METHOD_STAGE", {}), MH_STAGES)
    nw = _near_why(getattr(bot, "_METHOD_NEAR", []), sym)
    return False, why + (f" — {nw}" if nw else ""), ""


def chk_envelope(sym, hist, sess, decide=None, float_of=None):
    import envelope_scan as ES
    import envelope_hunter as EH
    edges = ES.load_edges()
    if not edges:
        return None, "حوافُّ الظرف غائبة — لا قرار", ""
    good, why, vals = (decide or ES.decide)(bot, sym, hist[sym], edges)
    if not good:
        return False, why, ""
    fl = (float_of or EH._float_of)(bot, sym, [1])
    if bot._float_too_big(fl):
        return False, f"M14 فلوت {fl:,.0f}", ""
    return True, "داخل ظرف كاتالوج فيصل" + ("" if fl is not None else " (الفلوت مجهول — يمرّ بفائدة الشك)"), ""


def chk_split_radar(sym, hist, sess, scan=None):
    rows = [r for r in ((scan or bot.scan_split_radar)(hist) or []) if r.get("symbol") == sym]
    sec = bot.build_split_radar_section(rows) if rows else ""
    if sec:
        return True, "مطابق كامل", sec
    return False, ("setup جزئيّ (لم تكتمل الشروط الستّ)" if rows else "ليس مقسّمًا عند قاع القمّة÷2"), ""


def chk_press(sym, hist, sess, read=None):
    import press_radar as PR
    df = hist[sym]
    r = (read or PR.press_read)(df, w=PR.ALERT_W)
    if not r:
        return False, f"لا ضغطَ عند القاع بقراءة الرادار (نافذة {PR.ALERT_W})", ""
    row = {"symbol": sym, "read": r, "plan": None, "src": "تأكيد المتابعة", "bars_src": PR._bars_src_of(df)}
    return True, "مطابق (الرادارُ اليوميّ يفحص بِركتَه وحدَها · هنا قراءةٌ مباشرة)", PR.build_alert([row], str(sess))


def chk_three(sym, hist, sess, card=None):
    import three_cond_daily as TCD
    try:
        rsi = float(bot.rsi(hist[sym]["Close"]).iloc[-1])
    except Exception:                                            # noqa: BLE001
        rsi = None
    card = card or {}
    r = {"rsi": rsi, "px": float(hist[sym]["Close"].iloc[-1]), "fl": card.get("float"), "av": card.get("shares_available")}
    f = TCD.flags3(r)
    v = TCD.WW.conj(f)

    def _t(x):
        return "✅" if x else ("❌" if x is False else "❔")
    txt = (f"RSI {('—' if rsi is None else f'{rsi:.1f}')} {_t(f[0])} · فلوت {_t(f[1])} · المتاح {_t(f[2])}"
           " (وثباتُ 5 جلسات والانفجارُ يُفحصان في رسالتها اليوميّة)")
    return v, txt, ""


TOOL_CHECKS = (("🪝 صيّاد التقسيم", chk_split_hunter), ("🧮 فلترة التقسيم", chk_split_filter),
               ("🔬 النهج العلمي", chk_method), ("📐 صيّاد الظرف", chk_envelope),
               ("🎯 رادار التقسيم", chk_split_radar), ("🗜️ رادار الضغط", chk_press), ("🔎 شروطك الثلاثة", chk_three))


def tools_check(sym, card=None, hist=None, checks=None):
    """كلُّ أداةٍ على شموع الرمز وحدَه ⟵ [(الأداة، True/False/None، النصّ، الكرت)] · كلُّ أداةٍ فاشلةٌ-آمنة على حدة."""
    if hist is None:
        try:
            hist = bot.download_history([sym]) or {}
        except Exception:                                        # noqa: BLE001
            hist = {}
    if sym not in hist:
        return [("🧰 بقيّة الأدوات", None, "تعذّر جلبُ الشموع", "")]
    try:
        sess = hist[sym].index[-1].date()
    except Exception:                                            # noqa: BLE001
        sess = None
    out = []
    for name, fn in (checks or TOOL_CHECKS):
        try:
            ok, txt, body = (fn(sym, hist, sess, card=card) if fn is chk_three else fn(sym, hist, sess))
        except Exception as e:                                   # noqa: BLE001
            ok, txt, body = None, f"تعذّر الفحص ({type(e).__name__})", ""
        out.append((name, ok, txt, body or ""))
    return out


def full_card(card) -> str:
    """📊 البياناتُ كاملة بحساب البوت (الدفعات · الدعم · الوقف · الأهداف · المقاومات) من كرت الفحص اليدويّ — فاشلٌ-آمن ⟵ ""."""
    if not card:
        return ""
    try:
        card["interp"] = bot.build_interpretation(card)
    except Exception:                                            # noqa: BLE001
        pass
    try:
        return bot.build_message([card], [], title="📊 <b>البيانات كاملة</b> (بحساب البوت)")
    except Exception as e:                                       # noqa: BLE001
        bot.log(f"⚠️ تأكيد المتابعة: تعذّر بناء البيانات الكاملة ({type(e).__name__}: {e}) — رسالةُ الأدوات بلاها.")
        return ""


def build_tools_message(sym, res, card=None, card_shown=True) -> str:
    """رسالةُ الأدوات: سطرٌ لكلّ أداة ثمّ كروتُ المطابِقة كلٌّ بشكل أداتها — ومتى طابق السهمُ أداةً **ولم تحمل الرسالةُ الأولى
    كرتَه** (ليس ارتكازًا ولا ارتدادًا) يُلحق كرتُ البوت الكامل (أمرُ المالك 2026-11-20 «يعطيني بيانات السهم كاملة لو مطابق احد
    الأدوات») — نقيّة."""
    icon = {True: "✅", False: "❌", None: "⚠️"}
    lines = [f"🧰 <b>${bot.esc(sym)} على بقيّة الأدوات</b>", ""]
    lines += [f"{icon[ok]} {n}: {bot.esc(t)}" for n, ok, t, _b in res]
    out = bot._rtl_join(lines)
    for n, ok, _t, b in res:
        if ok and b:
            out += f"\n\n{bot.DAILY_CARD_SEP}\n{b}"
    if not card_shown and any(ok is True for _n, ok, _t, _b in res):
        fc = full_card(card)
        if fc:
            bot.log(f"📊 تأكيد المتابعة: {sym} طابق أداةً ⟵ أُلحقت البياناتُ الكاملة.")
            out += f"\n\n{bot.DAILY_CARD_SEP}\n{fc}"
            return out
    return out + "\n\n" + bot.FOOTER


def main():
    syms = parse_symbols(os.environ.get("FOLLOW_CONFIRM") or os.environ.get("ANALYZE"))
    if not syms:
        bot.log("⚠️ لم يُحدَّد رمز: FOLLOW_CONFIRM=SXTC (حتى 5 بفاصلة).")
        return
    for sym in syms:
        bot.log(f"🔎✅ تأكيد المتابعة: {sym}")
        cap = capture(sym)
        msg = build_confirm_message(sym, cap, membership(sym))
        bot.send_telegram(msg)
        _args = cap.get("args") or (None, None, None, None, None, None)
        _card, _shown = _args[0], (_args[2] is not None or _args[4] is not None)
        bot.send_telegram(build_tools_message(sym, tools_check(sym, card=_card), card=_card, card_shown=_shown))
    bot.log(f"✅ أُرسل {len(syms)} تأكيد.")


if __name__ == "__main__":
    main()
