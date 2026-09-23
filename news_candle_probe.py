# -*- coding: utf-8 -*-
"""📰 مِجَسّ «شمعة الخبر» (R-01 · دفعة 2026-09-23) — **مؤقّت · قراءةٌ فقط · يُحذف بعد قراءة مُخرَجه**.

الجولتان الأولى والثانية (في تاريخ git لهذا الملفّ) أسقطتا افتراضين في تصميم R-01:
  ① CETX **بلا أيّ 8-K ببند 2.02** في 400 يوم ⇒ احتياطُ `10-Q`/`10-K` (تقريرُه 10-Q ‏2026-08-14 = Ⓔ فيصل).
  ② قاعدةُ «الأعلى حجمًا بين اليوم والتالي» اختارت لـ SNAL شمعةَ ردّ الفعل 08-12 وⒺ فيصل فوق 08-11
     ⇒ **جلسةُ يوم الإيداع نفسِه**.
**الجولة الثالثة (هذي):** تشغّل **المسارَ الإنتاجيَّ نفسَه** بعد التصحيح — `sec_recent_filings` ⟵ قناة
`_SEC_EARN` ⟵ `news_candle_level` ⟵ `news_candle_line` — على CETX وSNAL والقائمة الحيّة، فتطبع السطرَ كما
سيظهر وتَعُدّ التغطيةَ الفعليّة بعد الاحتياط (بدل تقديرها).
لا تلغرام · لا Polygon · لا كتابة حالة.
"""
import json
import time

import Super_stock as S

WITNESS = {"CETX": ("2026-08-14", 2.98, 3.10), "SNAL": ("2026-08-11", 4.17, 4.73)}


def third_round():
    print("████ الجولة الثالثة: المسارُ الإنتاجيّ نفسُه بعد التصحيح ████")
    wl = json.load(open("weekly_watchlist.json", encoding="utf-8"))
    act = sorted({s["symbol"] for s in wl.get("stocks", []) if s.get("status") == "active"})
    syms = list(WITNESS) + [s for s in act if s not in WITNESS]
    hist = S.download_history(syms, start_override="2025-06-01")
    tally, fails, lines_ok = {}, 0, 0
    for sym in syms:
        try:
            _, st = S.sec_recent_filings(sym)
        except Exception as e:                                   # noqa: BLE001
            fails += 1
            print(f"  ⛔ {sym}: {type(e).__name__}: {e}")
            continue
        ne = S._SEC_EARN.pop(sym.upper(), None)
        for ch in (S._SEC_PROXY, S._SEC_OFFERING, S._SEC_FOUNDING, S._SEC_FORM4):
            ch.pop(sym.upper(), None)
        form = (ne or {}).get("form")
        tally[form or "—"] = tally.get(form or "—", 0) + 1
        nc = S.news_candle_level(hist.get(sym), (ne or {}).get("date")) if ne else None
        ln = S.news_candle_line(nc, form)
        lines_ok += bool(ln)
        tag = "🔎" if sym in WITNESS else ("✅" if ln else "—")
        print(f"  {tag} {sym}: SEC={st} · إيداع={ne} ⟵ {ln or '— (لا سطر)'}")
        if sym in WITNESS:
            d, lo, hi = WITNESS[sym]
            ok = bool(nc) and nc["date"] == d and abs(nc["low"] - lo) < 0.011 and abs(nc["high"] - hi) < 0.011
            print(f"     ⟵ مقابل الشاهد {d} ‏{lo}-{hi}: {'✅ يطابق' if ok else '❌ لا يطابق'}")
        time.sleep(0.15)
    n_act = len([s for s in act if s not in WITNESS])
    print(f"\nالحصيلة: {len(syms)} رمزًا (الشاهدان + {n_act} نشطًا) · بسطرٍ = {lines_ok} · "
          f"مصادرُ التاريخ = {tally} · إخفاقاتُ SEC = {fails}")


if __name__ == "__main__":
    third_round()
