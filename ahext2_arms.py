#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌙⛰️② `T-AHEXT-2` — إعادةُ التصميم بمجتمعٍ غيرِ منحاز (العقد
`ahext2_prereg.md` مدفوعٌ **قبل هذا الملفّ** وقبل أيّ رقمٍ منه).

**العيبُ الذي يُصلَح:** غربالُ النسخة الأولى يقرأ فجوةَ الافتتاح فيلتقط مَن
**بقي** مرتفعًا ويُسقط مَن **ذاب** قبل 09:30 — وذوبانُ البري هو ما تصفه الدعوى
نفسُها ⇒ **فواتٌ مقيسٌ ‏63.7%**. وطبقةُ الفجوة السالبة كانت تُسقَط كلُّها.

**العلاجُ — معاينةٌ طبقيّةٌ موزونة (لا خفضُ عتبة):**

    H = gap ≥ GAP_MIN   ⟶ إحصاءٌ شامل (سقف H_CAP)
    L = 0 ≤ gap < GAP_MIN ⟶ عيّنةٌ حتميّة L_N
    Z = gap < 0          ⟶ عيّنةٌ حتميّة Z_N      ← طبقةٌ غابت عن العقد الأوّل

`H ⊎ L ⊎ Z` = كونُ (رمز·يوم) كلُّه داخلَ نطاق السعر ⇒ **لا «فائتٌ» يُقدَّر**،
ولذلك سقط `AX5` بزوال موضوعه.

🔒 **تجميدُ المقاييس بالبناء لا بالنسخ:** `CAP_HI` · `AH_MIN` · `PM_MIN` ·
`PRICE_LO/HI` وكلُّ دوالِّ القياس **تُستورَد من `ahext_arms` بالاسم** ⇒ لا يمكن
أن تنحرف عن النسخة الأولى ولو أردتُ. وهذا شرطُ §⓪-ب في العقد: **يتغيّر
المجتمعُ وحدَه** — لأنّي رأيتُ أرقامَ الأولى، فتحريكُ عتبةٍ الآن يجعل الاختيارَ
نفسَه هو النتيجة.

🔒 قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import Super_stock as S
from universe_arms import wilson
# ── الاستيرادُ بالاسم = التجميدُ بالبناء (‏`V-B1`) ──
from ahext_arms import (AH_MIN, CAP_HI, COVER_MIN, GAP_MIN, PM_MIN, PRICE_HI,
                        PRICE_LO, classify_arm, det_order, measure,
                        screen_symbol)

# ── ثوابتُ هذي النسخة وحدَها (§①-ج · مطبوعةٌ في كلّ تقرير) ──
H_CAP = 2500        # سقفُ الطبقة الشاملة
L_N = 25000         # عيّنةُ الطبقة [0, GAP_MIN)
Z_N = 15000         # عيّنةُ الطبقة السالبة
NEFF_MIN = 150      # `V-B4` حدُّ الدقّة لكلّ ذراع (حجمُ كيش)
WSUM_TOL = 0.01     # `V-B6` هامشُ مجموع الأوزان
THREADS = 8         # كلفةٌ لا منهج — لا تمسّ أيَّ رقم
SEED_TAG = "T-AHEXT2-20260910"
OUT_ROWS = "ahext2_rows.jsonl"


def _log(m):
    print(m, flush=True)


# ══════════════════ دوالُّ نقيّة (تُقفَل سلوكيًّا) ══════════════════
def strata(rows, gap_min: float = GAP_MIN):
    """`V-B6` — يقسّم صفوفَ الغربال إلى **ثلاثِ طبقاتٍ تستوعبه كلَّه**.

    نقيّةٌ وحتميّة. المجموعُ يساوي المدخلَ بت-بت — وهو ما يقرؤه القفلُ سلوكيًّا
    بدل الثقة بالتعريف."""
    h, low, z = [], [], []
    for r in rows:
        g = float(r["gap_pct"])
        (h if g >= gap_min else low if g >= 0 else z).append(r)
    return h, low, z


def kish(weights) -> float:
    """حجمُ العيّنة **الفعّال** (كيش): `(Σw)² / Σw²`.

    🔴 **ولماذا هو لا العددُ الموزون:** صفٌّ وزنُه 45 ليس خمسًا وأربعين مشاهدة،
    وحسابُ ويلسون على العدد الموزون **يُضيّق الفاصلَ كذبًا** فيصنع ثقةً بلا سند.
    هذا أخطرُ ما في التصميم الموزون (العقد §①-ب)."""
    s1 = sum(float(w) for w in weights)
    s2 = sum(float(w) ** 2 for w in weights)
    return (s1 * s1 / s2) if s2 > 0 else 0.0


def w_rate(vals, weights, thresh: float):
    """النسبةُ **الموزونة** فوق `thresh` + فاصلُ ويلسون على `n_eff` لا الخام."""
    tot = sum(float(w) for w in weights)
    if tot <= 0:
        return {"n_raw": len(vals), "n_eff": 0.0, "pct": 0.0, "wilson": [0.0, 0.0]}
    hit = sum(float(w) for v, w in zip(vals, weights)
              if v is not None and float(v) > float(thresh))
    p = hit / tot
    ne = kish(weights)
    lo, hi = wilson(p * ne, ne)
    return {"n_raw": len(vals), "n_eff": round(ne, 1),
            "pct": round(p * 100.0, 2), "wilson": [round(lo, 1), round(hi, 1)]}


def w_pctile(vals, weights, q: float):
    """المئينُ **الموزون**: أصغرُ قيمةٍ يبلغ تراكمُ وزنِها `q%` من الكلّ."""
    pairs = sorted((float(v), float(w)) for v, w in zip(vals, weights)
                   if v is not None and float(w) > 0)
    tot = sum(w for _, w in pairs)
    if not pairs or tot <= 0:
        return None
    need, acc = tot * (float(q) / 100.0), 0.0
    for v, w in pairs:
        acc += w
        if acc >= need:
            return round(v, 4)
    return round(pairs[-1][0], 4)


def w_diff_se(a, b):
    """الخطأُ المعياريُّ لفرقِ نسبتين موزونتين — **على `n_eff`** (§①-ب)."""
    na, nb = a["n_eff"], b["n_eff"]
    if na < 1 or nb < 1:
        return None
    pa, pb = a["pct"] / 100.0, b["pct"] / 100.0
    return round(((pa * (1 - pa) / na + pb * (1 - pb) / nb) ** 0.5) * 100.0, 2)


def plan_stratum(rows, cap: int, tag: str = SEED_TAG):
    """يُعايِن طبقةً **حتميًّا** ويُرجع (المُعايَنون، الوزن، الحجمُ الكلّيّ).

    الوزنُ `N/n` — وهو ما يجعل التقديرَ غيرَ منحازٍ بالبناء. والقصُّ **يُعلَن
    بعدده** في المُنادي (لا قصَّ صامت)."""
    n = len(rows)
    if n == 0:
        return [], 0.0, 0
    pick = det_order(rows, tag)[:int(cap)] if n > int(cap) else list(rows)
    return pick, n / float(len(pick)), n


# ══════════════════ التشغيل ══════════════════
def main() -> int:                                               # noqa: PLR0911
    year = str(os.environ.get("AHEXT2_YEAR", "")).strip()
    frozen = str(os.environ.get("AHEXT2_FROZEN", "")).strip()
    if year not in ("2023", "2024", "2025", "2026") or not frozen:
        _log("⛔ يلزم AHEXT2_YEAR و AHEXT2_FROZEN")
        return 2
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        _log("⛔ يلزم POLYGON_API_KEY — ولا يُخمَّن رقمٌ بدونه")
        return 5

    hist, _sp, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return 2
    if str(asof or "")[:4] != year:
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year}")
        return 4
    _log(f"🔒 سنةُ اللقطة {str(asof)[:4]} = سنةُ القياس {year} ✅ · "
         f"رموزُها {len(hist)}")
    _log(f"📌 مجمَّدٌ من العقد الأوّل بالاستيراد: GAP_MIN={GAP_MIN} · "
         f"PM_MIN={PM_MIN} · AH_MIN={AH_MIN} · CAP_HI={CAP_HI} · "
         f"السعر [{PRICE_LO}, {PRICE_HI}]")
    _log(f"📌 ميزانيّةُ هذي النسخة: H_CAP={H_CAP} · L_N={L_N} · Z_N={Z_N} · "
         f"NEFF_MIN={NEFF_MIN} · خيوط={THREADS}")

    # ── ① الغربالُ نفسُه بت-بت، والتقسيمُ ثلاثيّ ──
    allrows = []
    for sym in sorted(hist):
        for c in screen_symbol(hist[sym], year):
            c["symbol"] = sym
            allrows.append(c)
    h, low, z = strata(allrows)
    if len(h) + len(low) + len(z) != len(allrows):
        _log("⛔ `V-B6` الطبقاتُ لا تستوعب الغربال")
        return 6
    _log(f"🧱 الكون {len(allrows)} صفًّا ⇒ H {len(h)} · L {len(low)} · Z {len(z)}")
    if not h or not low:
        _log("⛔ طبقةٌ أساسيّةٌ فارغة")
        return 6

    plans = {}
    for name, rows, cap in (("H", h, H_CAP), ("L", low, L_N), ("Z", z, Z_N)):
        pick, w, N = plan_stratum(rows, cap)
        for r in pick:
            r["stratum"], r["w"] = name, w
        plans[name] = {"pick": pick, "w": w, "N": N,
                       "dropped": N - len(pick)}
        _log(f"   {name}: N={N} · مُشغَّلٌ {len(pick)} · **مُسقَطٌ "
             f"{N - len(pick)}** · وزنٌ {w:.3f}")

    todo = [r for p in plans.values() for r in p["pick"]]
    _log(f"📡 القياس: {len(todo)} صفًّا بـ{THREADS} خيوطٍ متوازية")

    # ── ② القياسُ متوازيًا — والحتميّةُ محفوظةٌ لأن الاختيارَ والترتيب سابقان ──
    def _one(r):
        m = measure(r["symbol"], r["prev_date"], r["date"])
        if m is not None:
            m["stratum"], m["w"], m["gap_pct"] = r["stratum"], r["w"], r["gap_pct"]
        return m

    done = []
    with ThreadPoolExecutor(max_workers=THREADS) as ex:
        for i, m in enumerate(ex.map(_one, todo)):
            if m is not None:
                done.append(m)
            if (i + 1) % 2000 == 0:
                _log(f"   … {i + 1}/{len(todo)} · ناجحٌ {len(done)}")
    with open(OUT_ROWS, "w", encoding="utf-8") as fh:
        for m in sorted(done, key=lambda x: (x["symbol"], x["date"])):
            fh.write(json.dumps(m, ensure_ascii=False) + "\n")

    # ── ③ `V-B7` التغطيةُ **لكلّ طبقةٍ على حدة** (إهمالُ طبقةٍ يُعيد الانحياز) ──
    cov = {}
    for name, p in plans.items():
        got = sum(1 for m in done if m["stratum"] == name)
        cov[name] = round(got / len(p["pick"]) * 100.0, 1) if p["pick"] else 0.0
        _log(f"🔒 `V-B7` تغطيةُ {name}: {got}/{len(p['pick'])} = {cov[name]}%")
    if any(v < COVER_MIN for v in cov.values()):
        _log(f"⛔ طبقةٌ دون {COVER_MIN}% ⇒ **الفرعُ 3: لا حكم**")
        return 7

    # ── ④ المجتمعُ والذراعان ──
    pop = [m for m in done
           if m["pm_peak"] is not None and m["pm_peak"] * 100.0 >= PM_MIN
           and classify_arm(m["ah_rise"]) is not None]
    ah = [m for m in pop if classify_arm(m["ah_rise"]) == "E-AH"]
    fr = [m for m in pop if classify_arm(m["ah_rise"]) == "E-FRESH"]
    if len(ah) + len(fr) != len(pop):
        _log("⛔ `V-A5` الذراعان لا تستوعبان المجتمع")
        return 6
    w_pop = sum(m["w"] for m in pop)
    _log(f"👥 المجتمع {len(pop)} صفًّا خامًا (موزونٌ {w_pop:,.0f}) · "
         f"`E-AH` {len(ah)} · `E-FRESH` {len(fr)}")
    share = {n: round(sum(m["w"] for m in pop if m["stratum"] == n)
                      / w_pop * 100.0, 1) if w_pop else 0.0
             for n in ("H", "L", "Z")}
    _log(f"🧱 حصّةُ الطبقات من المجتمع الموزون: {share}")

    # ── ⑤ المقاييس ──
    def _vals(rows):
        return [m["pm_peak"] * 100.0 for m in rows], [m["w"] for m in rows]

    va, wa = _vals(ah)
    vf, wf = _vals(fr)
    r_ah, r_fr = w_rate(va, wa, CAP_HI), w_rate(vf, wf, CAP_HI)
    d = round(r_fr["pct"] - r_ah["pct"], 2)
    se = w_diff_se(r_fr, r_ah)
    sig = round(abs(d) / se, 2) if se else None
    ax3 = w_pctile(va, wa, 90)
    alt = [(m, (1 + m["pm_peak"]) / (1 + m["ah_close_rise"]) * 100.0 - 100.0)
           for m in ah if m.get("ah_close_rise") is not None
           and (1 + m["ah_close_rise"]) > 0]
    ax4 = w_pctile([x for _, x in alt], [m["w"] for m, _ in alt], 90)
    floor_ok = min(r_ah["n_eff"], r_fr["n_eff"]) >= NEFF_MIN

    # `AX7` — شاهدُ صحّةٍ: الطبقةُ `H` وحدَها تُقابَل بأرقام التشغيلة الأولى
    h_ah = [m for m in ah if m["stratum"] == "H"]
    h_fr = [m for m in fr if m["stratum"] == "H"]
    ax7 = {"E_AH": w_rate(*_vals(h_ah), CAP_HI),
           "E_FRESH": w_rate(*_vals(h_fr), CAP_HI)}

    _log("")
    _log(f"📊 `AX1` فوق {CAP_HI}% (موزون): `E-AH` {r_ah['pct']}% "
         f"[n_eff {r_ah['n_eff']}] · `E-FRESH` {r_fr['pct']}% "
         f"[n_eff {r_fr['n_eff']}]")
    _log(f"📊 الفرقُ (FRESH−AH) = **{d:+} نقطة** · σ={se} · {sig}σ")
    _log(f"📊 `AX3` المئينُ 90 الموزون لـ`E-AH` = **{ax3}%**")
    _log(f"📊 `AX4` القراءةُ الثانية (مرجعُ إغلاق الافتر) = {ax4}%")
    _log(f"📊 `AX7` شاهدُ الصحّة — الطبقة H وحدَها: `E-AH` "
         f"{ax7['E_AH']['pct']}% · `E-FRESH` {ax7['E_FRESH']['pct']}% "
         f"(التشغيلةُ الأولى: 22.64% · 19.14%)")
    _log(f"🔒 `V-B4` حدُّ الدقّة {NEFF_MIN}/ذراع: "
         f"{'✅' if floor_ok else '⛔ لا تدخل AX1'}")

    print("AHEXT2_JSON " + json.dumps(
        {"year": year, "asof": str(asof), "universe": len(allrows),
         "strata": {n: {"N": plans[n]["N"], "run": len(plans[n]["pick"]),
                        "dropped": plans[n]["dropped"],
                        "w": round(plans[n]["w"], 4), "cover": cov[n]}
                    for n in ("H", "L", "Z")},
         "pop_raw": len(pop), "pop_weighted": round(w_pop, 1),
         "pop_share": share,
         "AX1": {"E_AH": r_ah, "E_FRESH": r_fr, "diff": d, "se": se,
                 "sigma": sig},
         "AX3_p90_ah": ax3, "AX4_p90_alt": ax4, "AX7_H_only": ax7,
         "floor_ok": floor_ok, "no_verdict": not floor_ok},
        ensure_ascii=False))
    return 0 if floor_ok else 9


if __name__ == "__main__":
    sys.exit(main())
