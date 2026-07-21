#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕰️ تحليل تاريخي «كما رآه البوت في يومٍ محدّد» (point-in-time، بلا نظر مستقبلي).

الغرض (طلب المستخدم 2026-07-20): التحقّق من سهمٍ حلّله فيصل في أيام معيّنة (أربعاء/
خميس/جمعة) — **لا اليوم** بعد أن ركض السعر. نقصّ التاريخ حتى نهاية كل يوم مطلوب ثم
نشغّل **نفس** `analyze_ticker` (الجذر) فنرى ما كانت ستعرضه البطاقة **ذلك اليوم**:
الجاهزية · حالة الدخول (🟢 جاهز / 👀 متابعة + السبب) · الأهداف الجديدة · التحرر.

الاستعمال (Actions، workflow_dispatch):
  ASOF_TICKER=DXST  ASOF_DATES=2026-07-15,2026-07-16,2026-07-17  python analyze_asof.py

⚠️ حدّ صدق: yfinance يعدّل الأسعار رجعيًّا للتقسيمات — لو حصل تقسيم **بعد** التاريخ
المطلوب فالعرض التاريخي يتشوّه. لنافذة أيام قليلة ماضية (بلا تقسيم) الأمر سليم؛ يُذكر
التحذير. عرض/تشخيص فقط — لا يحفظ قائمة ولا يمسّ الفرز/الحالة."""
import os
import datetime as dt

import Super_stock as bot

C = bot.CONFIG


def _one(sym, df_full, dstr):
    """يحلّل السهم عند نهاية يوم dstr (قصّ df) ويرجع سطر عرض مختصر."""
    try:
        cut = dt.date.fromisoformat(dstr)
    except Exception:
        return f"❌ تاريخ غير صالح: {dstr}"
    df = df_full[df_full.index.date <= cut]     # قصّ حتى نهاية اليوم (بلا مستقبل)
    if len(df) < C["MIN_BARS"]:
        return f"📅 {dstr}: بيانات غير كافية حتى هذا التاريخ (شموع={len(df)})"
    last = df.index[-1].date()
    stale = "" if last == cut else f" ⚠️(آخر تداول متاح {last})"

    if getattr(bot, "_REJECT_STATS", None) is not None:
        bot._REJECT_STATS.clear()
    r = None
    try:
        r = bot.analyze_ticker(sym, df)
    except Exception as e:
        bot.log(f"analyze {dstr}: {e}")
    pull = None
    if r is None:
        try:
            pull = bot.analyze_ticker(sym, df, pullback=True)
        except Exception:
            pull = None
    card = r or pull

    head = f"📅 <b>{dstr}</b>{stale}"
    if card is None:
        reason = "?"
        if getattr(bot, "_REJECT_STATS", None):
            reason = " · ".join(f"{k}={v}" for k, v in bot._REJECT_STATS.items())
        return f"{head}\n   ⛔ لم يُرشَّح ({reason})"

    # طبقة التفسير (لحساب entry_mode → entry_status) — نفس مسار البطاقة
    try:
        card["interp"] = bot.build_interpretation(card)
    except Exception:
        pass
    es = bot.entry_status(card)
    price = float(card.get("price") or 0)
    trs = card.get("tranches") or []
    zone = (f"{min(trs):.2f}-{max(trs):.2f}" if trs else "—")
    mode = "" if (r is not None) else " (وضع مراقبة ارتداد)"
    lib = card.get("liberation")
    _tk = card.get("targets_kind") or []      # 🎨 لون فيصل: 🔵 نظيف · ⚫ مقاومة
    _tp = []
    for _i, _tv in enumerate((card["t1"], card["t2"], card["t3"])):
        _kc = _tk[_i] if _i < len(_tk) else ""
        _pre = (_kc + " ") if _kc in ("🔵", "⚫") else ""
        _tp.append(f"{_pre}${_tv:.2f}")
    out = [
        f"{head}{mode}",
        f"   💰 ${price:.2f} · منطقة الدفعات {zone} · جاهزية {card.get('readiness', '?')}%",
        f"   {es['label']}" + (f" — {es['reason']}" if es.get("reason") else ""),
        f"   🎯 {' · '.join(_tp)}"
        + (f" · 🚀 تحرر ${float(lib):.2f}" if lib else ""),
    ]
    return "\n".join(out)


def run():
    sym = os.environ.get("ASOF_TICKER", "").strip().upper()
    dates = [d.strip() for d in os.environ.get("ASOF_DATES", "").split(",")
             if d.strip()]
    if not sym or not dates:
        bot.log("⚠️ يلزم ASOF_TICKER و ASOF_DATES (مفصولة بفاصلة).")
        return
    bot.log(f"🕰️ تحليل تاريخي لـ {sym} عند: {', '.join(dates)}")
    try:
        data = bot.download_history([sym])
    except Exception as e:
        bot.send_telegram(f"🕰️ {sym}: تعذّر جلب البيانات ({e})\n\n{bot.FOOTER}")
        return
    df_full = data.get(sym)
    if df_full is None or len(df_full) < C["MIN_BARS"]:
        bot.send_telegram(f"🕰️ {sym}: بيانات غير كافية.\n\n{bot.FOOTER}")
        return
    blocks = [_one(sym, df_full, d) for d in dates]
    msg = (f"🕰️ <b>تحليل تاريخي (كما رآه البوت): {sym}</b>\n"
           f"🧾 {bot.LOGIC_VERSION}\n\n" + "\n\n".join(blocks)
           + "\n\n⚠️ الأسعار مُعدَّلة رجعيًّا لأي تقسيم لاحق (سليم بلا تقسيم حديث)."
           + f"\n\n{bot.FOOTER}")
    bot.send_telegram(msg)
    bot.log(msg)


if __name__ == "__main__":
    run()
