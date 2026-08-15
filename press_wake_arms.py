#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️🔥 شرائحُ الرادار على اللقطات (العقد: `press_prereg.md §⑯` · مدفوعٌ
**قبل** أيّ رقم · أمرُ المالك «شغّل الباكتست ٣ سنوات على الرادار»).

**تشخيصُ شرائحَ لا جولةَ معايرة** — إغلاقُ §⑭ قائم: صفرُ تغيير عتبةٍ أو
اعتمادٍ من هذي الأرقام؛ تُنشَر بفواصلها فقط.

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** القراءةُ `press_radar.press_read`
(‏w=40 كما في الإنتاج والباكتيست) · الصحوةُ `press_radar.wake_read` (بلا
الافتر — غيرُ قابلٍ للقياس من اليومي، **أرضيّةٌ** مُعلَنة) · الكنسُ من
`press_read` نفسها (‏`swept_hold`) · الخطةُ `rebound_arms.mirror_plan` ·
الحسمُ `rebound_arms.resolve_episode` · القفزةُ `WAIT` بعد كل مطابقةٍ =
مِشيةُ §⑬ **بالبناء** ⇒ بوّابةُ التكامل: مجموعُ HOLD3 عبر الثلاث يعيد
أرقامَ §⑬ (‏5371 محسومة · 19.08% · ‏+0.174R) وإلا عطبُ أداةٍ لا نتيجة.
🔒 خارج مسار الفرز كليًّا (لا يستورده الإنتاج) · لا `LOGIC_VERSION`."""
from __future__ import annotations

import os
import sys


def _log(m):
    print(m, flush=True)


def walk_symbol_wake(sym, df, year=None):
    """مِشيةُ §⑬ حرفيًّا + حقولُ الشرائح لكل حلقة. ترجع قائمة قواميس."""
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    recs = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return recs
    n = len(df)
    i = RB.MIN_BARS
    vm = float(S.CONFIG.get("VOL_SPIKE_MULT", 5.0))
    while i < n:
        if year and yrs[i] != str(year):
            i += 1
            continue
        sl = df.iloc[:i + 1]
        r = PR.press_read(sl, w=40)
        if r:
            pl = float(r["press_low"])
            tr, st = RB.mirror_plan(pl)
            oc = RB.resolve_episode(hi, lo, i, tr, st)
            w = PR.wake_read(sl)                 # بلا افتر — أرضيّة (§⑯)
            vol_flag = bool(w.get("vol_x")
                            and float(w["vol_x"]) >= vm)
            recs.append({"i": i,
                         "hold": int(r.get("hold_sessions") or 0),
                         "oc": oc,
                         "awake": bool(w.get("awake")),
                         "vol": vol_flag,
                         "rev": w.get("rev"),
                         "swept": bool(r.get("swept_hold"))})
            i += RB.WAIT
            continue
        i += 1
    return recs


def _slice_line(name, sub):
    """سطرُ شريحةٍ: عدد · محسومة · بلوغ الهدف % بفاصل Wilson · التوقّع R."""
    import press_backtest as PB                                  # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    dec = [e for e in sub if e["oc"] in ("win", "loss")]
    k = sum(1 for e in dec if e["oc"] == "win")
    if not dec:
        return f"  {name:<22} حلقات={len(sub):<6} محسومة=0 — لا رقم"
    wlo, whi = RB.wilson(k, len(dec))
    rw = PB.r_win_value()
    ev = (k * rw - (len(dec) - k)) / len(dec)
    return (f"  {name:<22} حلقات={len(sub):<6} محسومة={len(dec):<6} "
            f"بلغ الهدف={100.0 * k / len(dec):6.2f}% "
            f"[{100 * wlo:.1f},{100 * whi:.1f}] · التوقّع {ev:+.3f}R")


def report(recs, n_syms, year) -> int:
    import press_radar as PR                                     # noqa: PLC0415
    _log(f"\n{'—' * 74}\n📊 §⑯ سنة {year} — رموز {n_syms} · حلقات {len(recs)}")
    if not recs:
        _log("⛔ صفرُ حلقات (بصمة الـno-op) — خروج 4.")
        return 4
    h3 = [e for e in recs if e["hold"] >= PR.READY_HOLD]
    _log(_slice_line("الكل (كل قراءة)", recs))
    _log(_slice_line("🟢 HOLD3 (بوابة التكامل)", h3))
    _log("  — شرائحُ §⑯ داخل HOLD3 (أرقامُ «مستيقظ» أرضيّةٌ بلا الافتر):")
    _log(_slice_line("🔥 مستيقظ (أي قرينة)", [e for e in h3 if e["awake"]]))
    _log(_slice_line("   قفزةُ حجم", [e for e in h3 if e["vol"]]))
    _log(_slice_line("   شمعةٌ انعكاسية",
                     [e for e in h3 if e["rev"] and not e["vol"]]))
    _log(_slice_line("😴 هادئ", [e for e in h3 if not e["awake"]]))
    _log(_slice_line("🩸 مكنوسٌ بعد حفظ", [e for e in h3 if e["swept"]]))
    _log(_slice_line("   غيرُ مكنوس", [e for e in h3 if not e["swept"]]))
    dec3 = [e for e in h3 if e["oc"] in ("win", "loss")]
    k3 = sum(1 for e in dec3 if e["oc"] == "win")
    _log(f"  🔗 مِرساةُ التكامل السنوية: HOLD3 محسومة={len(dec3)} · "
         f"فائزة={k3} (المجموعُ عبر الثلاث يجب أن يعيد §⑬: ‏5371 · 19.08%)")
    _log("\n⚠️ تشخيصُ شرائحَ لا معايرة (§⑯): صفرُ تغيير عتبةٍ من هذي الأرقام ·"
         " والصحوةُ بلا الافتر = أرضيّة.")
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🗜️🔥 §⑯ شرائح الرادار — سنة {year}\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    recs, n_syms = [], 0
    yr = year if year and year != "?" else None
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        recs.extend(walk_symbol_wake(sym, df, year=yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(recs)}")
    return report(recs, n_syms, year)


if __name__ == "__main__":
    sys.exit(main())
