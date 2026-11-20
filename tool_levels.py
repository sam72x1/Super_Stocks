#!/usr/bin/env python3
"""🎯 الأهداف والمقاومات لكلّ سهمٍ جاهز في رسائل الأدوات (أمرُ المالك 2026-11-20:
«تضيف الأهداف و المقاومات للجميع الأسهم الجاهزة لكل الأدوات صياد التقسيم و النهج العلمي و الشروط الثلاثة الخ»).

الأرقامُ **ليست جديدة**: تُحسب بالفحص اليدويّ نفسِه (`analyze_one.analyze_on_demand` — مرآةُ `analyze_ticker`:
الأهدافُ الثلاثة وألوانُها · المقاومةُ الفرعيّة والأساسيّة من `key_levels`) على شموع الأداة نفسِها إن مُرِّرت ·
ثمّ قسمٌ واحد في آخر الرسالة قبل التذييل: سطرٌ لكلّ سهم.
عرضٌ فقط: بعد اختيار الأداة (لا يُدخل سهمًا ولا يُخرجه) · فاشلٌ-آمن لكلّ سهمٍ على حدة (تعذّرُه ⟵ سطرُه يغيب ويُعَدّ) ·
سقفُ `LEVELS_MAX` سهمًا ويُعلَن القصّ · `TOOL_LEVELS=0` ⟵ الرسائلُ بت-بت · `TLV1`-`TLV4`.
"""
import os


def _bot():
    import Super_stock                                          # كسولٌ: مستوردُ الأداة لا يدفع ثمنَه قبل الحاجة
    return Super_stock

LEVELS_MAX = 12                     # engineering — يحدّ زمنَ الحساب وطولَ الرسالة · والقصُّ يُعلَن
TITLE = "🎯 <b>الأهداف والمقاومات</b> — بحساب فارز الارتكاز (مستقلّةٌ عن هدف الأداة ووقفها)"


def enabled() -> bool:
    return os.environ.get("TOOL_LEVELS", "1").strip() != "0"


def levels_for(sym, df=None, analyze=None):
    """{t1,t2,t3,kind,res_minor,res_major} من الفحص اليدويّ · `df` شموعُ الأداة (لا جلبَ ثانٍ) · تعذّرٌ ⟵ None."""
    import analyze_one as AO
    bot = _bot()
    _dl = bot.download_history
    try:
        if df is not None:
            bot.download_history = lambda syms, *a, **k: {str(sym).upper(): df}
        out = (analyze or AO.analyze_on_demand)(sym)
    except Exception:                                            # noqa: BLE001
        return None
    finally:
        bot.download_history = _dl
    res = out[0] if isinstance(out, tuple) and out else None
    if not isinstance(res, dict) or res.get("t1") is None:
        return None
    kl = res.get("key_levels") or {}
    return {"t1": res.get("t1"), "t2": res.get("t2"), "t3": res.get("t3"),
            "kind": res.get("targets_kind"), "res_minor": kl.get("res_minor"), "res_major": kl.get("res_major")}


def _px(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f <= 0:
        return None
    return f"${f:.4f}".rstrip("0").rstrip(".") if f < 1 else f"${f:.2f}"


def levels_line(sym, lv) -> str:
    """«$SYM — 🎯 الأهداف: $1 · $2 · $3 · 🔴 مقاومة فرعية $x · أساسية $y» — نقيّة."""
    bot = _bot()
    kind = lv.get("kind") or [None, None, None]
    tg = []
    for i, k in enumerate(("t1", "t2", "t3")):
        p = _px(lv.get(k))
        if p:
            c = kind[i] if i < len(kind) and kind[i] else ""
            tg.append(f"{p}{(' ' + c) if c else ''}")
    parts = [f"<b>${bot.esc(sym)}</b> — 🎯 الأهداف: " + (" · ".join(tg) if tg else "—")]
    rm, rM = _px(lv.get("res_minor")), _px(lv.get("res_major"))
    if rm or rM:
        rs = []
        if rm:
            rs.append(f"فرعية {rm}")
        if rM and rM != rm:
            rs.append(f"أساسية {rM}")
        parts.append("🔴 مقاومة " + " · ".join(rs))
    return " · ".join(parts)


def levels_section(syms, hist=None, analyze=None) -> str:
    """القسمُ كاملًا لرموزٍ مطابِقة (بلا تكرار · بترتيبها) — «» حين المفتاحُ مطفأ أو لا رمز."""
    if not enabled():
        return ""
    bot = _bot()
    seen = []
    for s in syms or []:
        s = str(s or "").strip().upper()
        if s and s not in seen:
            seen.append(s)
    if not seen:
        return ""
    cut = max(0, len(seen) - LEVELS_MAX)
    lines, miss = [TITLE], 0
    for s in seen[:LEVELS_MAX]:
        lv = levels_for(s, (hist or {}).get(s), analyze=analyze)
        if lv is None:
            miss += 1
            continue
        lines.append(levels_line(s, lv))
    if len(lines) == 1:
        bot.log(f"🎯 الأهداف والمقاومات: تعذّر حسابُها لـ{miss} من {len(seen[:LEVELS_MAX])} — لا قسم.")
        return ""
    if miss:
        lines.append(f"<i>تعذّر حسابُها لـ{miss}</i>")
    if cut:
        lines.append(f"<i>✂️ قُصّ {cut} سهمًا (السقف {LEVELS_MAX})</i>")
    lines.append("<i>⚫ مقاومة · 🔵 هدف بلا مقاومة</i>")
    bot.log(f"🎯 الأهداف والمقاومات: {len(lines) - 2 - bool(miss) - bool(cut)} سطرًا · تعذّر {miss} · قُصّ {cut}.")
    return bot._rtl_join(lines)


def with_levels(body: str, syms, hist=None, analyze=None) -> str:
    """`body` ‏+ القسم (إن وُجد) — بلا تذييل · تعذّرٌ مطلق ⟵ `body` كما هو."""
    try:
        sec = levels_section(syms, hist, analyze=analyze)
    except Exception as e:                                       # noqa: BLE001
        _bot().log(f"⚠️ الأهداف والمقاومات تعذّرت ({type(e).__name__}) — الرسالةُ بلاها.")
        sec = ""
    return body + ("\n\n" + sec if sec else "")
