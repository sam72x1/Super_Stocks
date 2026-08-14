#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️📚 مِجَسُّ الكتالوج `T−2` — هل كان رادارُ الضغط سيرى منفجري فيصل قبل
جلستين؟ (العقد: `press_prereg.md §⑪` · مدفوعٌ **قبل** أيّ رقم).

**إعادةُ استعمالٍ بالاسم — صفر منطق منسوخ:** المجموعتان والمِرساة والجلب من
`preexp_probe` (‏`catalog_events`/`live_events`/`fetch_bars`/`_sessions_before`
واشتقاقُ مِرساة أ بـ`explosion_onset` المصحَّحة)، والقراءةُ
`press_radar.press_read` **نفسُها التي التقطت WETO** — على شريحة الشموع حتى
الجلسة ‏−2 ثم ‏−1 قبل المِرساة حصرًا (لا نظر مستقبليّ: الشريحة تنتهي قبل
جلسة الانفجار دائمًا).

**المُخرَج:** لكل مجموعة نسبةُ مَن أطلق عند أيٍّ من الجلستين + تفكيكُ أسباب
عدم الإطلاق **بحالاتٍ مُسمّاة** (لا صفرَ غامضًا — درس `_status_tally`).
⚠️ توصيفُ التقاطٍ لا معدلَ إصابة (العيّنة مختارة على النتيجة — مُعلَن)."""
from __future__ import annotations

import os
import sys

OFFSETS = (-2, -1)


def _log(m):
    print(m, flush=True)


def probe_day(bars, upto_idx):
    """نقيّة: تقصّ الشموع حتى الفهرس (شاملًا) وتقرأ `press_read` بالاسم.
    ترجع (قراءة أو None، سببُ عدم الإطلاق المُسمّى)."""
    import Super_stock as S                                      # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    sl = bars.iloc[:upto_idx + 1]
    if len(sl) < PR.W + 1:
        return None, "تاريخ قصير"
    r = PR.press_read(sl)
    if r:
        return r, "أطلق"
    # تفكيك السبب — بنفس ترتيب شروط `press_read` (تشخيصٌ لا قرارٌ ثانٍ)
    try:
        hi = sl["High"].values.astype(float)
        lo = sl["Low"].values.astype(float)
        cl = sl["Close"].values.astype(float)
        i = len(cl) - 1
        win_hi = hi[i - PR.W + 1:i + 1]
        j_star = int(i - PR.W + 1 + max(range(len(win_hi)), key=lambda k: win_hi[k]))
        close = float(cl[i])
        if j_star >= i:
            return None, "القمة اليوم نفسه (ما زال صاعدًا)"
        if close < float(S.CONFIG.get("SPLIT_RADAR_PRICE_MIN", 1.0)):
            return None, "سعر تحت أرضية $1"
        drop = (float(hi[j_star]) - close) / float(hi[j_star]) * 100.0
        if drop < float(S.CONFIG.get("SPLIT_CLIFF_PCT", 30.0)):
            return None, "عمق أقل من الحد (ليس مضغوطًا)"
        press_low = float(min(lo[j_star:i + 1]))
        cap = press_low * (1.0 + float(S.CONFIG.get("SPLIT_SWEEP_MAX_PCT", 13.0)) / 100.0)
        if close > cap:
            return None, "غادر قاعه"
        return None, "سببٌ آخر"
    except Exception:                                            # noqa: BLE001
        return None, "تعذّر التشخيص"


def main() -> int:
    import preexp_probe as PX                                    # noqa: PLC0415
    _log(f"\n{'=' * 78}\n🗜️📚 مِجَسُّ الكتالوج T−2 — قراءةُ رادار الضغط قبل "
         f"الانفجار بجلستين (press_prereg §⑪)\n{'=' * 78}")
    _log(f"📡 المصدر: {os.environ.get('PREEXP_SOURCE', 'yahoo')!r} · "
         f"الإزاحات {OFFSETS} (قبل المِرساة حصرًا)")
    events = PX.catalog_events() + PX.live_events()
    if not events:
        _log("⛔ صفرُ أحداث — خروج 4.")
        return 4
    rows, skipped = [], {}
    for ev in events:
        sym = ev["symbol"]
        try:
            bars = PX.fetch_bars(sym)
        except Exception as e:                                    # noqa: BLE001
            skipped[sym] = f"تحميل: {e}"
            continue
        if bars is None or len(bars) < 60:
            skipped[sym] = "بيانات قصيرة/غائبة"
            continue
        anchor = ev.get("anchor")
        if not anchor:                        # المجموعة (أ): مِرساة مصحَّحة
            try:
                import catalog_envelope as CE                     # noqa: PLC0415
                _hi = bars["High"].values.astype(float)
                _lo = bars["Low"].values.astype(float)
                _ix = CE.explosion_index(_hi, _lo)
                k = CE.explosion_onset(_lo, _ix) if _ix is not None else None
                anchor = str(bars.index[k].date()) if k is not None else None
            except Exception:                                     # noqa: BLE001
                anchor = None
        if not anchor:
            skipped[sym] = "بلا مِرساة"
            continue
        sess = PX._sessions_before(bars, anchor, OFFSETS)
        if not sess:
            skipped[sym] = "جلساتُ ما قبل المِرساة غائبة"
            continue
        idx_map = {d: k for k, d in enumerate(bars.index)}
        day_res = []
        for si in sess:
            r, why = probe_day(bars, idx_map[si])
            day_res.append((str(si.date()), bool(r), why,
                            (r or {}).get("drop_pct"), (r or {}).get("press_low"),
                            (r or {}).get("tested_level")))
        fired = any(x[1] for x in day_res)
        rows.append({"symbol": sym, "group": ev["group"], "anchor": anchor,
                     "fired": fired, "days": day_res})
        mark = "🔥" if fired else "—"
        det = " · ".join(f"{d}:{'✅' if f else w}" for d, f, w, *_ in day_res)
        _log(f"  {mark} {sym} ({ev['group']}) مِرساة {anchor} ⇒ {det}")
    if not rows:
        _log("⛔ صفرُ أزواجٍ مقيسة (بصمة الـno-op) — خروج 4.")
        return 4
    _log(f"\n{'—' * 70}\n📊 الخلاصة:")
    for g in ("أ", "ب"):
        sub = [r for r in rows if r["group"] == g]
        if not sub:
            continue
        k = sum(1 for r in sub if r["fired"])
        _log(f"  المجموعة ({g}): أطلق الرادار قبل الانفجار (‏−2 أو −1) في "
             f"{k} من {len(sub)} = {100.0 * k / len(sub):.1f}%")
    # تفكيكُ أسباب عدم الإطلاق (على مستوى الأيام) — لا صفرَ غامضًا
    from collections import Counter                              # noqa: PLC0415
    why = Counter(w for r in rows for _, f, w, *_ in r["days"] if not f)
    _log("  أسبابُ عدم الإطلاق (يوم-قراءة): "
         + " · ".join(f"{k}={v}" for k, v in why.most_common()))
    if skipped:
        _log(f"  ⚪️ متخطَّون ({len(skipped)}): "
             + " · ".join(f"{s}({w})" for s, w in list(skipped.items())[:10])
             + (" …" if len(skipped) > 10 else ""))
    _log("\n⚠️ توصيفُ التقاطٍ لا معدلَ إصابة (عيّنة مختارة على النتيجة — §⑪)؛"
         " «كم ممّن يراهم الرادار ينفجر؟» يجيبه سجلُّ الحصاد الأماميّ حصرًا.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
