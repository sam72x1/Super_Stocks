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

# 🧪 §⑪-ج: التركيباتُ الأربع المحسوبة من الشموع — مثبّتة من التسجيل، لا تُعدَّل
# بعد رؤية الأرقام. البقية (VB/VC/VD) تُركَّب من هذي القراءات + قرائن الحياة.
VARIANTS = (("V0", {}),
            ("VA1", {"w": 40}),
            ("VA2", {"band_pct": 20.0}),
            ("VA3", {"w": 40, "band_pct": 20.0}))
COMBO_ORDER = ("V0", "VA1", "VA2", "VA3",
               "VB-owner", "VB-union", "VC-safety", "VD-full")


def _log(m):
    print(m, flush=True)


def dollar_vol_ok(sl):
    """نقيّة (‏VC-safety): وسيطُ السيولة الدولارية لآخر 20 جلسة مقابل
    `MIN_DOLLAR_VOL` **النافذ** (ظرف فيصل عند `FAISAL_ONLY=1`). ترجع
    True/False أو None عند تعذّر القراءة (يُعَدّ ولا يُخمَّن)."""
    import Super_stock as S                                      # noqa: PLC0415
    try:
        import statistics                                        # noqa: PLC0415
        cl = sl["Close"].values.astype(float)[-20:]
        vo = sl["Volume"].values.astype(float)[-20:]
        if len(cl) < 5 or len(cl) != len(vo):
            return None
        med = statistics.median(float(c) * float(v) for c, v in zip(cl, vo))
        return med >= float(S.CONFIG.get("MIN_DOLLAR_VOL", 200000))
    except Exception:                                            # noqa: BLE001
        return None


def variant_day(bars, upto_idx):
    """نقيّة: قراءاتُ اليوم الواحد للتركيبات الأربع المحسوبة + بوّابة السلامة.
    تنادي `press_radar.press_read` **بالاسم** بوسيطَي البحث (‏§⑪-ج)."""
    import press_radar as PR                                     # noqa: PLC0415
    sl = bars.iloc[:upto_idx + 1]
    out = {name: PR.press_read(sl, **kw) for name, kw in VARIANTS}
    out["safety"] = dollar_vol_ok(sl)
    return out


def life_evidence(read, prev_q):
    """نقيّة (‏«قرينةُ حياةٍ واحدة»): مؤهلٌ سابقًا **أو** ركضة عند حد
    `EXPLOSION_PCT` فأكثر **أو** مستوى مُختبَر **أو** حفظٌ جلسة فأكثر."""
    import Super_stock as S                                      # noqa: PLC0415
    if prev_q:
        return True
    if not read:
        return False
    thr = float(S.CONFIG.get("EXPLOSION_PCT", 50.0))
    return bool(float(read.get("runup_pct") or 0.0) >= thr
                or read.get("tested_level")
                or int(read.get("hold_sessions") or 0) >= 1)


def combo_flags(var_days, prev_q):
    """نقيّة: أعلامُ التركيبات الثماني لحدثٍ واحد من قراءات أيامه.
    VC/VD تشترط السلامة **في نفس يوم الإطلاق** (لا خلط أيام)."""
    c = {name: any(d.get(name) for d in var_days)
         for name, _ in VARIANTS}
    c["VB-owner"] = bool(c["V0"] and prev_q)
    c["VB-union"] = any(d.get("V0") and life_evidence(d.get("V0"), prev_q)
                        for d in var_days)
    c["VC-safety"] = any(d.get("V0") and d.get("safety") is True
                         for d in var_days)
    c["VD-full"] = any(d.get("VA3") and life_evidence(d.get("VA3"), prev_q)
                       and d.get("safety") is True for d in var_days)
    return c


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
        day_res, var_days = [], []
        for si in sess:
            r, why = probe_day(bars, idx_map[si])
            day_res.append((str(si.date()), bool(r), why,
                            (r or {}).get("drop_pct"), (r or {}).get("press_low"),
                            (r or {}).get("tested_level"),
                            (r or {}).get("runup_pct")))
            var_days.append(variant_day(bars, idx_map[si]))     # §⑪-ج
        fired = any(x[1] for x in day_res)
        runups = [x[6] for x in day_res if x[1] and x[6] is not None]
        import press_radar as PR                             # noqa: PLC0415
        pq = PR.prev_qualified(sym, bars, anchor)
        rows.append({"symbol": sym, "group": ev["group"], "anchor": anchor,
                     "fired": fired, "days": day_res, "prev_q": pq,
                     "runup": max(runups) if runups else None,
                     "combo": combo_flags(var_days, pq),
                     "safety_unknown": sum(1 for d in var_days
                                           if d.get("safety") is None)})
        mark = "🔥" if fired else "—"
        det = " · ".join(f"{d}:{'✅' if f else w}" for d, f, w, *_ in day_res)
        ru = f" · ركضة {max(runups):.0f}%" if runups else ""
        pqs = f" · مؤهلٌ سابقًا @{pq}" if pq else " · لم يتأهل سابقًا"
        _log(f"  {mark} {sym} ({ev['group']}) مِرساة {anchor} ⇒ {det}{ru}{pqs}")
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
    # 🔁 «تركيبة المالك» (تأهّل سابقًا ⟵ انضغط ⟵ انفجر): كم تُبقي من الالتقاط؟
    for g in ("أ", "ب"):
        sub = [r for r in rows if r["group"] == g]
        fired_g = [r for r in sub if r["fired"]]
        pq_all = sum(1 for r in sub if r["prev_q"])
        pq_fired = sum(1 for r in fired_g if r["prev_q"])
        if sub:
            _log(f"  🔁 تركيبة «مؤهلٌ سابقًا + مضغوط»: المجموعة ({g}) — "
                 f"مؤهلون سابقًا {pq_all} من {len(sub)} · ومن المُطلَقين "
                 f"{pq_fired} من {len(fired_g)} (هذي صيدُ التركيبة الكاملة)")
    # 🗜️ توزيع «ركضة ما قبل الضغط» بين المُطلَقين — لقياس فلتر المالك المقترح
    # (‏«فلاتر مو كل متحرك») قبل فرضه: كم من الالتقاط يبقى عند كل عتبة قائمة؟
    fired_rows = [r for r in rows if r["fired"] and r.get("runup") is not None]
    for thr, name in ((50.0, "EXPLOSION_PCT=50"), (70.0, "EXPLOSION_RUN_PCT=70")):
        for g in ("أ", "ب"):
            sub = [r for r in fired_rows if r["group"] == g]
            if sub:
                keep = sum(1 for r in sub if r["runup"] >= thr)
                _log(f"  فلتر الركضة ‏≥{name}: المجموعة ({g}) يبقى {keep} من {len(sub)} مُطلَقًا")
    # 🧪 §⑪-ج: شبكةُ التركيبات الثماني — الالتقاط لكل مجموعة + الغائبون بأسمائهم
    _log(f"\n{'—' * 70}\n🧪 شبكة التركيبات (§⑪-ج — مثبّتة قبل القياس):")
    for name in COMBO_ORDER:
        parts = []
        for g in ("أ", "ب"):
            sub = [r for r in rows if r["group"] == g]
            if not sub:
                continue
            k = sum(1 for r in sub if r["combo"].get(name))
            parts.append(f"({g}) {k} من {len(sub)}")
        _log(f"  {name}: " + " · ".join(parts))
        miss_a = [r["symbol"] for r in rows
                  if r["group"] == "أ" and not r["combo"].get(name)]
        if miss_a:
            _log(f"     غائبو الكتالوج: {' · '.join(miss_a)}")
    unk = sum(r.get("safety_unknown") or 0 for r in rows)
    if unk:
        _log(f"  ⚠️ قراءاتُ سلامةٍ متعذّرة (يوم-قراءة): {unk} — تُعَدّ سقوطًا"
             " في VC/VD (مُعلَن لا صامت)")
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
