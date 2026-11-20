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
عرضٌ فقط: لا يكتب حالةً ولا يمسّ عتبةً ولا جذرًا · `FCF1`-`FCF3`.

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
    bot.log(f"✅ أُرسل {len(syms)} تأكيد.")


if __name__ == "__main__":
    main()
