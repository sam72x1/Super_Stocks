#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕯️ `T-CANDLE` — «أيُّ شمعةٍ انعكاسية تفصل؟» (العقد: `candle_prereg.md`
مدفوعٌ **قبل هذا الملفّ**).

**السؤال (§①):** قِيست «الشمعة الانعكاسية» **مجموعةً** مرّتين وكلاهما ضعيف
(‏§⑯ و`T-FUSE`) — **ولم يُقَس نمطٌ بعينه قطّ**. فهل يفصل **اسمُ النمط**؟ وهل
تنعكس **مرتبةُ فيصل المنصوصة** (همر > نجمة صباح > هرامي > أيًّا كانت) في
الأرقام؟

**المحرّك — إعادةُ استعمالٍ بالاسم، صفرُ مِشيةٍ منسوخة (‏§②/`CV3`):**
الحلقاتُ من `fuse_arms.walk` **نفسِها** (وهي `press_wake_arms.walk_symbol_wake`
المجمَّدة ‏+ `enrich_episode`)، واسمُ النمط يأتي جاهزًا في `rev` من
`press_radar.wake_read` (تُنادي `reversal_candle` ثم `extra_candle`
الإنتاجيَّتين). **الحقلُ الوحيد المضاف: لونُ الشمعة** (‏`close > open` عند
فهرس الحلقة — **حقيقةٌ لا عتبة**) لشقّ «الهمر الأحمر» المنصوص.

🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import math
import os
import sys

# §③ — الأنماطُ الستّة المنصوصة (بترتيب فيصل ثم المضافتان) — لا نمطَ يُضاف بعد الأرقام
FAISAL_ORDER = ("همر", "نجمة صباح", "هرامي", "وت")   # `IMG_0448` بترتيبه حرفيًّا
EXTRA = ("همر مقلوب", "دوجي")                        # دفعة 37 صورة · AMCI
PATTERNS = FAISAL_ORDER + EXTRA
GOV = "همر"                                          # §③ الحاكمة C1 — مرتبتُه الأولى
N_COMPARE = len(PATTERNS)                            # بونفيروني ×6 (§③ قاعدة الترقية)
Z95 = 1.959964                                       # ثابتٌ قياسيّ لا عتبةَ مُعايَرة
Z_BONF = 2.638257                                    # ‏α = 0.05/6 ثنائيّ الطرف
OUT_ROWS = "candle_rows.jsonl"

# §⑤ `CV0`-أ — مِرساةُ `T-FUSE` المنشورة: شريحةُ «شمعة انعكاسية» داخل `F1`
# (حلقات · محسومة · فائزة) — أيُّ تفرّقٍ ⇒ خروج 3 (عطبُ أداةٍ لا نتيجة).
PUB_FUSE_F1_REV = {"2023": (481, 459, 69),
                   "2024": (401, 381, 69),
                   "2025": (485, 465, 93)}
# §⑤ `CV0`-ب — مِرساةُ §⑬ السنوية (‏H3): تُجمع عبر الثلاث ⟶ 5371 · 19.08% · +0.174R
PUB13_H3 = {"2023": (1660, 351), "2024": (1857, 333), "2025": (1854, 341)}


def _log(m):
    print(m, flush=True)


def wilson(k, n, z=Z95):
    """نقيّة: فاصلُ Wilson بالنسبة المئوية. مقامٌ صفر ⇒ (0.0, 0.0)."""
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100.0 * (c - h), 100.0 * (c + h)


def candle_color(df, i):
    """نقيّة: لونُ شمعة الحلقة عند فهرسها — «أخضر» إن أغلقت فوق فتحها.

    ⚖️ **حقيقةٌ لا عتبة** (‏§②): لا رقمَ يُعايَر هنا. سندُه نصُّ فيصل
    «**شمعة همر حمرا = صعود قصير الأمد** ويؤخذ منها الوتد الهابط فقط» —
    تحفّظٌ منصوصٌ و`reversal_candle` لا تميّز اللون. تعذّرٌ ⇒ None."""
    try:
        o = float(df["Open"].values[int(i)])
        c = float(df["Close"].values[int(i)])
    except Exception:                                            # noqa: BLE001
        return None
    return "أخضر" if c > o else "أحمر"


def _counts(sub):
    dec = [e for e in sub if e["oc"] in ("win", "loss")]
    k = sum(1 for e in dec if e["oc"] == "win")
    nf = sum(1 for e in sub if e["oc"] == "no_fill")
    return len(sub), len(dec), k, nf


def ev_of(sub, r_win):
    """نقيّة: التوقّعُ `E` لكل صفقةٍ محسومة (فائزةٌ ‏×r_win · خاسرةٌ ‏−1)."""
    _n, dec, k, _nf = _counts(sub)
    if not dec:
        return None
    return (k * float(r_win) - (dec - k)) / dec


def _line(name, sub, r_win, z=Z95):
    n, dec, k, nf = _counts(sub)
    e = ev_of(sub, r_win)
    lo, hi = wilson(k, dec, z)
    pct = (100.0 * k / dec) if dec else 0.0
    return (f"  {name:<26} حلقات={n:<5d} محسومة={dec:<5d} فائزة={k:<4d} "
            f"بلغ الهدف={pct:6.2f}% [{lo:.1f},{hi:.1f}] · التوقّع="
            + (f"{e:+.3f}R" if e is not None else "—")
            + f"   ⟵ no_fill={nf}")


def walk(sym, df, year):
    """حلقاتُ الرمز: `fuse_arms.walk` **بالاسم** + لونُ الشمعة عند الفهرس."""
    import fuse_arms as FU                                       # noqa: PLC0415
    rows, issues = FU.walk(sym, df, year)
    for r in rows:
        r["color"] = candle_color(df, r["i"]) if r.get("rev") else None
    return rows, issues


def report(rows, n_syms, year, issues) -> int:
    import press_backtest as PB                                  # noqa: PLC0415
    r_win = PB.r_win_value()
    _log(f"\n{'—' * 78}\n🕯️ T-CANDLE سنة {year} — رموز {n_syms} · "
         f"حلقات {len(rows)} · r_win={r_win:.4f}")
    if not rows:
        _log("⛔ `CV1`: صفرُ حلقات (بصمة الـno-op) ⇒ خروج 4.")
        return 4

    # ── `CV0`-أ: شريحةُ «شمعة انعكاسية» داخل `F1` تعيد `T-FUSE` بت-بت
    f1_rev = [e for e in rows if e["cell"] == "F1" and e.get("rev")]
    got = _counts(f1_rev)[:3]
    want = PUB_FUSE_F1_REV.get(str(year))
    if want and tuple(got) != tuple(want):
        _log(f"⛔ `CV0`-أ: شريحةُ F1×انعكاسية {got} تخالف المنشور في "
             f"`fuse_result` {want} ⇒ **عطبُ أداةٍ لا نتيجة** ⇒ خروج 3.")
        return 3
    _log(f"🔗 `CV0`-أ ✅ F1×انعكاسية = {got} — مطابقةٌ بت-بت لِـ`T-FUSE`.")
    h3 = [e for e in rows if e["hold"] >= 3]
    _hn, hd, hk, _ = _counts(h3)
    wh = PUB13_H3.get(str(year))
    if wh and (hd, hk) != tuple(wh):
        _log(f"⛔ `CV0`-ب: مِرساةُ §⑬ ({hd}, {hk}) تخالف {wh} ⇒ خروج 3.")
        return 3
    _log(f"🔗 `CV0`-ب ✅ مِرساةُ §⑬ السنوية: محسومة={hd} · فائزة={hk}")

    # ── `CV2`: التقسيمُ تامٌّ ومنفصل — وأيُّ اسمٍ خارج الستّة يُعَدّ ويُسمّى
    rev_all = [e for e in rows if e.get("rev")]
    buckets = {p: [e for e in rev_all if e["rev"] == p] for p in PATTERNS}
    other = [e for e in rev_all if e["rev"] not in PATTERNS]
    tot = sum(len(v) for v in buckets.values()) + len(other)
    _log(f"🧮 `CV2` التقسيم: REV-ALL={len(rev_all)} · مجموعُ الأنماط={tot} · "
         f"خارج الستّة={len(other)}"
         + (f" ⇒ الأسماء: {sorted({e['rev'] for e in other})}" if other else "")
         + (" ✅" if tot == len(rev_all) else " 🔴 تفرّق"))
    if tot != len(rev_all):
        _log("⛔ `CV2`: التقسيمُ غيرُ تامّ ⇒ خروج 3.")
        return 3
    if not buckets.get(GOV):
        _log(f"⛔ `CV1`: الذراعُ الحاكمة «{GOV}» فارغة ⇒ خروج 4.")
        return 4

    _log("\n📊 الأذرع (‏§③) — الجدولُ كاملًا، والترقيةُ بمعايير §④ وحدها:")
    _log(_line("REV-ALL (المجتمع)", rev_all, r_win))
    _log(_line("REV-NONE (شاهدُ العزل)",
               [e for e in rows if not e.get("rev")], r_win))
    for p in PATTERNS:
        tag = " 🥇C1" if p == GOV else ""
        _log(_line(f"{p}{tag}", buckets[p], r_win))

    # ── الحاكمةُ C1: «همر» مقابل بقيّة REV-ALL
    gov = buckets[GOV]
    rest = [e for e in rev_all if e["rev"] != GOV]
    eg, er = ev_of(gov, r_win), ev_of(rest, r_win)
    _log("\n🥇 الحاكمة `C1` — «همر» مقابل بقيّة الشمع الانعكاسية:")
    _log(_line("C1 همر", gov, r_win))
    _log(_line("بقيّةُ REV-ALL", rest, r_win))
    if eg is not None and er is not None:
        _log(f"  ⇒ الفرق = {eg - er:+.4f}R (الحدُّ المسجَّل +0.15R)")
    for nm, sub in (("همر", gov), ("بقيّة", rest)):
        _n, d, k, _ = _counts(sub)
        _log(f"  ‏Wilson بونفيروني ×{N_COMPARE} لـ{nm}: "
             f"{wilson(k, d, Z_BONF)[0]:.1f} — {wilson(k, d, Z_BONF)[1]:.1f}")

    # ── استكشافيّاتٌ تُنشَر ولا تُرقّى (‏§③)
    _log("\n🔬 استكشافيّات §③ (تُنشَر ولا تحكم — ولا تُرقّى إلّا بكامل §④):")
    for p in ("همر", "همر مقلوب"):
        for col in ("أخضر", "أحمر"):
            _log(_line(f"    {p} {col}",
                       [e for e in buckets[p] if e.get("color") == col], r_win))
    _log(_line("    انعكاسيةٌ داخل F2", [e for e in rev_all
                                          if e["cell"] == "F2"], r_win))
    _log(_line("    انعكاسيةٌ مع مستوًى مُختبَر",
               [e for e in rev_all if e.get("tl")], r_win))
    _log(_line("    انعكاسيةٌ بلا مستوًى", [e for e in rev_all
                                             if not e.get("tl")], r_win))

    if issues:
        _log(f"\n🩺 حلقاتٌ لم تُثرَ (بأسبابها): {issues}")
    _log("\n⚠️ حدود §⑧: «بلغ الهدف» لمسٌ لا تنفيذ · E بخطّة المرآة لا ربحيةَ "
         "البوت · **الفريمُ يوميٌّ حصرًا وفيصل قال «كلاهما»** (شقُّ 4س خارج "
         "القياس) · الأسماءُ متنافسةٌ (أوّلُ مطابقةٍ تفوز) · وبونفيروني ×6 "
         "شرطُ ترقية.")
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🕯️ T-CANDLE — سنة {year} · الحاكمة «{GOV}» "
         f"(مرتبةُ فيصل الأولى) · لقطة={path}\n{'=' * 78}")
    if not year:
        _log("⛔ `BACKTEST_YEAR` غائب ⇒ خروج 2.")
        return 2
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ لقطةٌ فارغة ⇒ خروج 2.")
        return 2
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    rows, n_syms, issues = [], 0, {}
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        r, iss = walk(sym, df, year)
        rows.extend(r)
        for k, v in iss.items():
            issues[k] = issues.get(k, 0) + v
        if n_syms % 400 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(rows)}")
    if issues.get("fatal"):
        _log(f"⛔ `CV0`: تفرّقٌ في الإثراء ({issues}) ⇒ خروج 3.")
        return 3
    try:
        with open(OUT_ROWS, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        _log(f"💾 {OUT_ROWS}: {len(rows)} صفًّا")
    except Exception as _e:                                      # noqa: BLE001
        _log(f"⚠️ تعذّر حفظُ الصفوف: {type(_e).__name__}")
    return report(rows, n_syms, year, issues)


if __name__ == "__main__":
    sys.exit(main())
