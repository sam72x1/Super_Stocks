#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 T-METHOD — المُشغِّل (`method_prereg.md`). بحث/قياس · **صفر مسّ إنتاج**.

يمشي السوق سببيًّا بوصفة «النهج العلمي» ويطبع **أحجام الشرائح أوّلًا** (‏فحصُ قدرةٍ
معمّى، §⑧-مكرّر ⑤) ثم النتائج. يلزمه `BACKTEST_YEAR`، ويقرأ لقطةً مجمّدة إن وُجدت.
"""
from __future__ import annotations

import os

os.environ.setdefault("SCREENER_MODE", "BACKTEST")

import Super_stock as S            # noqa: E402
import method_scan as M            # noqa: E402


def run() -> int:
    year = int((os.environ.get("BACKTEST_YEAR") or "0").strip() or 0)
    print(f"\n{'=' * 72}\n🔬 T-METHOD · السنة {year}\n{'=' * 72}")
    if not year:
        print("⛔ لا `BACKTEST_YEAR` ⇒ لا تشغيل.")
        return 2
    uni = S.get_universe()
    if not uni:
        print("⛔ كون ناسداك فارغ ⇒ لا قياس (لا نتيجة مفبركة).")
        return 2
    hist = S.download_history(uni, start_override=f"{year - 2}-01-01")
    if not hist:
        print("⛔ صفر بيانات ⇒ لا قياس.")
        return 2
    cov = {}
    sig, judged, excluded_src, no_splits = [], [], 0, 0
    offer_idx = M.load_offering_index()
    for sym, df in hist.items():
        if df is None or len(df) < 80:
            cov["short_hist"] = cov.get("short_hist", 0) + 1
            continue
        try:
            d = df[(df.index >= f"{year}-01-01") & (df.index <= f"{year}-12-31")]
            if len(d) < 40:
                continue
            base = df[df.index <= f"{year}-12-31"]
        except Exception:                                        # noqa: BLE001
            continue
        # ① **حارس التقسيم — تغطيةٌ حقيقية.** التشغيلة الأولى كشفت أن اللقطة
        #    المجمّدة تغطّي **79 من 3386** رمزًا ⇒ الحارس **الأخطر** كان خاملًا
        #    في 98% من الكون، والنتيجة غير قابلة للتفسير. الآن: اللقطة أوّلًا،
        #    وإلّا **جلبٌ مباشر لكل رمزٍ يبلغ الحدث المؤسِّس** (‏والجلبُ فاشل-آمن
        #    ⇒ `None` ⇒ لا إقصاء، فيُعَدّ ويُعلَن بدل أن يُدَّعى).
        sp = (S._BT_SPLITS_CTX or {}).get(sym) if S._BT_SPLITS_CTX else None
        if sp is None:
            try:
                sp = S._fetch_splits(sym)
            except Exception:                                    # noqa: BLE001
                sp = None
        if sp is None:
            no_splits += 1
        try:                                   # ④ القروب — محسوبٌ في المُنادي
            pump = S.group_pump_scar(base)
        except Exception:                                        # noqa: BLE001
            pump = None
        rows = M.walk(S, sym, base, splits=sp,
                      off_dates=offer_idx.get(sym), pump=pump, cov=cov)
        rows = [r for r in rows if str(r["date"])[:4] == str(year)]
        if not rows:
            continue
        sig.extend(rows)
        if sym.upper() in M.SOURCE_SYMBOLS:     # ④ استبعاد رموز المصدر
            excluded_src += len(rows)
            continue
        judged.extend(rows)

    # 🩺 **العلم فعّال؟** — يُطبَع قبل أي نتيجة (بصمة الـno-op)
    print(f"🩺 التغطية: رموز={len(hist)} · إشارات خام={len(sig)} · "
          f"للحكم={len(judged)} · مستبعَد كمصدر={excluded_src}")
    print(f"🩺 الإقصاءات: {cov}")
    _cov_split = 1.0 - (no_splits / max(1, len(hist)))
    print(f"🔴 حارس التقسيم: تغطية {_cov_split * 100:.0f}% "
          f"(بلا سياق: {no_splits} من {len(hist)})"
          + ("  ⇒ **خامل ⇒ لا تُفسَّر النتيجة** (البيانات المعدَّلة تُصنّع الحدث)"
             if _cov_split < 0.5 else ""))
    print("🔴 شرط «لا إعلان طرح»: "
          + (f"مُختبَر على {sum(1 for r in judged if r['offer_tested'])} من "
             f"{len(judged)}" if offer_idx else
             "**غير مُختبَر** (لا فهرس SEC مؤرَّخ) — لا يُدَّعى استيفاؤه"))
    if len(judged) < 30:
        print(f"\n🧭 العيّنة {len(judged)} دون 30 ⇒ **«لا حكم» لا «فشل»** (§⑥-1).")
    dec = [r for r in judged if r["ret"] is not None]
    if not dec:
        print("صفر صفقة محسومة.")
        return 0
    ex = sum(1 for r in dec if r["mg_pre_stop"] >= 100.0)
    win = sum(1 for r in dec if r["outcome"] == "win")
    print(f"\n📊 محسومة={len(dec)} · نجاح={win / len(dec) * 100:.1f}% · "
          f"**منفجرون مُسلَّمون (‏≥+100%)={ex}** · "
          f"وسيط الحركة={sorted(r['mg_pre_stop'] for r in dec)[len(dec) // 2]:.0f}%")
    print("\n⚠️ حدود الصدق: شرطا الشورت/الاقتراض **بلا تاريخ** فخارج القياس ⇒ "
          "المُختبَر **أوسع** من وصفة فيصل ⇒ النتيجة **أرضيّة لا سقف** · "
          "وعتبة الارتداد 7% إنتاجية لا 10-15% النصّية (‏§⑧-مكرّر ④).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
