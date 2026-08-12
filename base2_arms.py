#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧱② T-BASE-2 — سلّمُ سقف عرض القاعدة (`base2_prereg.md`).

**السؤال (§①):** هل يوجد سقفٌ **وسطيّ** يرفض `LGHL` (عرضُ قاعدته 138.2%) ويُبقي
أكثر المنفجرين المُسلَّمين؟
**الأذرع (§②):** `B23685` (الأساس) · `B120` · `B80` · `B40` — **أربعةٌ ولا خامسة**،
وفي **تشغيلةٍ واحدة بميزانيةٍ ثابتة** (نفسُ اللقطة والمُرتِّب والسعة والنافذة).

🔒 **صفر مسٍّ بالإنتاج:** الوالدُ لا يستورد `Super_stock`؛ كلُّ ذراعٍ في **عملية
منفصلة** تضبط `CONFIG` **بعد** الاستيراد (‏`faisal_only_overrides` يُطبَّق وقتَه)
وتُطبَع القيمةُ النافذة. الفارزُ الحيّ لا يمرّ من هنا.

⚠️ **تجربةُ كلفةٍ لا حافّة** (‏§⑥): الاعتمادُ يلزمه استيفاءُ أربعة حرّاس.
🐞 **وكُتبت من الصفر لا بإعادةِ تسميةٍ آلية** — تلك تركت في `base_arms.py` مراجعَ
`hits['G214']` وسطَ بوّابة الصلاحية (‏`KeyError` كان سيُسقطها بعد استهلاك الأذرع).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# الترتيبُ مقصود: الأساسُ أوّلًا ثم الأضيقُ تدرّجًا (يُستعمل في حارس الرتابة).
ARMS: dict[str, float] = {"B23685": 23684.631623040408, "B120": 120.0,
                          "B80": 80.0, "B40": 40.0}
BASE_ARM = "B23685"

# 🧱④ `T-BASE-475` (‏`base475_prereg.md` · أمرُ المالك 2026-08-12 «قِس 475»):
#     ذراعٌ إضافيةٌ **بعلمٍ مطفأٍ افتراضيًّا** — فبلا `BASE2_EXTRA_ARM` تبقى الأذرعُ
#     **مطابقةً للأربعة المسجَّلة** في `base2_prereg.md` (§②: «أربعةٌ ولا خامسة»)
#     ⇒ تلك التجربةُ قابلةٌ لإعادة الإنتاج حرفيًّا. والصيغة: `الاسم=القيمة`.
# 🔒 **وتُدرَج بترتيبها** (الأوسعُ أوّلًا) فتنطبق حرّاسُ الرتابة ②/③ بلا تعديل —
#     وإدراجُها في غير موضعها كان سيُسقط بوّابةَ الصلاحية على عطبِ ترتيبٍ لا على
#     نتيجةٍ (نفسُ الفخّ الذي قلبَ الشرطَ ② في أوّل كتابة).
_EXTRA = (os.environ.get("BASE2_EXTRA_ARM") or "").strip()
if _EXTRA:
    _nm, _, _vl = _EXTRA.partition("=")
    _nm, _vl = _nm.strip(), _vl.strip()
    if not _nm or not _vl:
        raise SystemExit(f"⛔ `BASE2_EXTRA_ARM` صيغتُها `الاسم=القيمة` — وُجد {_EXTRA!r}")
    if _nm in ARMS:
        raise SystemExit(f"⛔ الذراع {_nm} موجودةٌ سلفًا — لا تُكرَّر")
    ARMS = dict(sorted({**ARMS, _nm: float(_vl)}.items(),
                       key=lambda kv: -kv[1]))
GATE_KEY = "M4_base_واسعة"      # عدّادُ البوّابة في توزيع رفض الإنتاج
# §④-5 فحصُ التكامل: أرقامٌ منشورةٌ سلفًا يجب أن تُعاد بت-بت (سنة ⟶ d50).
# §④-5 فحصُ التكامل — 🔴 **أُشدَّ 2026-08-12** (‏`base475_prereg.md` §④): كانت
#      مِرساتين فصارت **ثلاثًا** بإضافة `B120` (‏d50 المنشور 25 · 18 · 10 في
#      `base2_result.md §①`) ⇒ **الأساسُ نفسُه صار مُبرهَنًا** — تشديدٌ لا إرخاء.
# ⚠️ **وقيدٌ مُعلَن:** الأرقامُ المنشورةُ مقيسةٌ عند **سعة 10**، والسعةُ الحيّة صارت
#      **15** بقرار المالك 2026-08-12 ⇒ فحصُ التكامل **سيخرق** حتمًا، والتشغيلةُ
#      تُوسَم «مقامٌ جديد» ولا تُقارَن بالمنشور. ولذلك تُقاس المِرساةُ **في نفس
#      التشغيلة** فيُقارَن مثلٌ بمثل (‏§③ من التسجيل).
INTEGRITY = {"B23685": {"2024": 20, "2025": 22, "2026": 11},
             "B120": {"2024": 25, "2025": 18, "2026": 10},
             "B40": {"2024": 17, "2025": 15, "2026": 9}}


def child_env() -> dict:
    """أعلامُ الباكتيست — **بلا هذي لا يُحسَب `d50` ولا `R`** (عيبٌ مقيس أسقط
    ثلاثَ تشغيلاتٍ لـ`T-CHASE`). ولا علمَ يفترق بين الأذرع: الفرقُ سقفُ البوّابة."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
            "BT_ENVVALS": "1", "BT_POTENTIAL": "1"}


def rates(trades) -> dict:
    """نسبةُ الدقة **بمقامها** (‏§⑤-3) — لا نسبةَ بلا عدد محسومة."""
    w = sum(1 for t in trades if t.get("outcome") == "win")
    ls = sum(1 for t in trades if t.get("outcome") == "loss")
    dec = w + ls
    return {"signals": len(trades), "decided": dec, "wins": w, "losses": ls,
            "no_fill": sum(1 for t in trades if t.get("outcome") == "no_fill"),
            "win_rate": (round(100.0 * w / dec, 1) if dec else None)}


def gate_hits(text: str) -> int:
    """عدّادُ البوّابة من **توزيع رفض الإنتاج نفسِه** (‏§④-2).
    صيغتُه: «‏   1. M4_base_واسعة = 18220 (31.0%)». غيابُ المفتاح ⇒ 0."""
    return sum(int(m.group(1)) for m in
               re.finditer(re.escape(GATE_KEY) + r"[^=\n]*=\s*(\d+)", text or ""))


def probe(syms: str = None) -> int:
    """🔬 مِجَسٌّ تشخيصيّ **خارج الحكم** (‏§⑧) — يحسم الشرط (د): هل تُرفَض LGHL؟"""
    import Super_stock as S                                      # noqa: PLC0415
    names = [x.strip().upper() for x in
             (syms or os.environ.get("BASE_PROBE_SYMS") or "LGHL").split(",")
             if x.strip()]
    if not names:
        return 0
    print(f"\n{'─' * 74}\n🔬 مِجَسٌّ تشخيصيّ (خارج الحكم · §⑧): {' · '.join(names)}"
          f"\n{'─' * 74}", flush=True)
    try:
        hist = S.download_history(names)
    except Exception as e:                                        # noqa: BLE001
        print(f"  ⛔ تعذّر التحميل ({e}) — تشخيصٌ فلا يُسقط التجربة.")
        return 0
    bw = int(S.CONFIG["BASE_WINDOW"])
    for sym in names:
        df = hist.get(sym)
        if df is None or len(df) < bw:
            print(f"  ⚪️ {sym}: لا بيانات كافية.")
            continue
        hi, lo = float(df["High"].tail(bw).max()), float(df["Low"].tail(bw).min())
        rng = (hi / lo - 1.0) * 100.0 if lo > 0 else float("nan")
        print(f"  📏 {sym}: نافذة {bw} جلسة — أعلى ${hi:.4f} · أدنى ${lo:.4f} ⇒ "
              f"**عرض القاعدة {rng:.1f}%** (آخر شمعة {df.index[-1].date()})")
        for arm, cap in ARMS.items():
            print(f"     {arm:<7} (سقف {cap:>12,.2f}): "
                  + ("❌ يُرفَض M4_base_واسعة" if rng > cap else "✅ يمرّ M4"))
        # 🔒 **حكمُ كلّ ذراعٍ بكودِ الإنتاج نفسِه** — التزامًا بنصّ §⑧ («بـ
        #    `_diagnose_symbol` الإنتاجيّة»)؛ فالمقارنةُ الحسابية أعلاه وحدها
        #    استدلالٌ منّي، وهذي شهادةُ الفارز. والاستعادةُ في `finally` فلا
        #    يتسرّب سقفٌ إلى ذراعٍ تالية ولا إلى بقيّة المِجَسّ.
        for arm, cap in ARMS.items():
            print(f"  ── تشخيصُ الإنتاج بسقف {arm} ({cap:,.2f}) ──")
            _old = S.CONFIG["BASE_RANGE_MAX_PCT"]
            try:
                S.CONFIG["BASE_RANGE_MAX_PCT"] = float(cap)
                S._diagnose_symbol(sym, df)
            except Exception as e:                                # noqa: BLE001
                print(f"     ⚠️ تعذّر التشخيص: {e}")
            finally:
                S.CONFIG["BASE_RANGE_MAX_PCT"] = _old
    return 0


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    S.CONFIG["BASE_RANGE_MAX_PCT"] = float(ARMS[arm])     # **بعد** الاستيراد
    print(f"ARM_EFFECTIVE {arm} BASE_RANGE_MAX_PCT="
          f"{S.CONFIG['BASE_RANGE_MAX_PCT']!r}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "cap": S.CONFIG["BASE_RANGE_MAX_PCT"]}
    out.update(rates(trades))
    wf = [t for t in trades if t.get("exit_date")]
    if wf:
        cands, idx, oc = RP.candidates_from_trades(wf)
        res = RP.replay(cands, outcome_of=oc, ranker=RP.rank_live,
                        sessions=range(0, len(idx)))
        taken = res["taken"]
        rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]

        def _d(thr):
            n = 0
            for c in taken:
                p = c.payload
                if p.get("mg_outcome") in (None, "no_fill"):
                    continue
                try:
                    if float(p.get("mg_pre_stop") or 0.0) >= thr:
                        n += 1
                except (TypeError, ValueError):
                    pass
            return n
        out.update({"taken": len(taken), "rejected_cap": res["rejected_cap"],
                    "d50": _d(float(S.CONFIG["EXPLOSION_PCT"])), "d100": _d(100.0),
                    "per_trade": (round(sum(rs) / len(taken), 4)
                                  if taken else 0.0)})
    print("BASE2_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def validity(res: dict, hits: dict, year: str) -> tuple[bool, list]:
    """§④ — خمسةُ شروطٍ تُقرأ **قبل** أيّ تفسير. تُرجع (سليم، أسطر)."""
    order = list(ARMS)                       # الأساس ثم الأضيق تدرّجًا
    lines, ok = [], True

    caps = [res[a]["cap"] for a in order]
    c1 = len({round(c, 6) for c in caps}) == len(order)
    lines.append(("①", c1, "القيمُ النافذة أربعٌ متمايزة: "
                  + " · ".join(f"{a}={res[a]['cap']:,.2f}" for a in order)))

    # 🐞 **مقلوبةٌ في أوّل كتابة، كشفها الدخانُ قبل أيّ تشغيلةٍ حقيقية:** السقفُ
    #    **الأضيق** يرفض **أكثر** ⇒ العدّادُ **يتزايد** كلَّما ضاق (‏B120 < B80 < B40)
    #    — وكنتُ أشترط العكس فكانت البوّابةُ ستُسقط الثلاثَ تشغيلاتٍ كلَّها وتُقرأ
    #    «no-op» بينما العطبُ في الشرط. (‏`ARMS` مرتَّبةٌ من الأوسع إلى الأضيق.)
    narrow = [a for a in order if a != BASE_ARM]
    c2 = (all(hits[narrow[i]] < hits[narrow[i + 1]] for i in range(len(narrow) - 1))
          and hits[BASE_ARM] < min(hits[a] for a in narrow))
    lines.append(("②", c2, "العدّادُ يشتعل تدرّجًا: "
                  + " · ".join(f"{a}={hits[a]}" for a in order)))

    sig = [res[a]["signals"] for a in order]
    c3 = all(sig[i] >= sig[i + 1] for i in range(len(sig) - 1))
    lines.append(("③", c3, "الإشاراتُ رتيبةٌ تنازليًّا: "
                  + " ≥ ".join(f"{a}={res[a]['signals']}" for a in order)))

    c4 = all(res[a].get("taken") is not None and res[a].get("d50") is not None
             for a in order)
    lines.append(("④", c4, "المقياسُ الحاكم محسوبٌ لا غائب: "
                  + " · ".join(f"{a}.d50={res[a].get('d50')}" for a in order)))

    # ⑤ فحصُ التكامل — أرقامٌ منشورةٌ سلفًا تُعاد بت-بت (خرقُه يُبطل التشغيلة).
    bad = [f"{a}:{res[a].get('d50')}≠{INTEGRITY[a][year]}"
           for a in INTEGRITY if year in INTEGRITY[a]
           and res[a].get("d50") != INTEGRITY[a][year]]
    c5 = not bad and any(year in INTEGRITY[a] for a in INTEGRITY)
    lines.append(("⑤", c5, "فحصُ التكامل (يُعيد المنشور بت-بت)"
                  + (f" — خرق: {' · '.join(bad)}" if bad
                     else " — سنةٌ غير مرجعية (تُرفَض عمدًا)" if not c5 else "")))

    for _t, _o, _w in lines:
        ok = ok and _o
    return ok, lines


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 78}\n🧱② T-BASE-2 — سلّمُ سقف عرض القاعدة · السنة {year}"
          f"\n{'=' * 78}", flush=True)
    res, hits = {}, {}
    for arm in ARMS:
        print(f"\n──── الذراع {arm} (سقف {ARMS[arm]:,.2f}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env={**dict(os.environ), **child_env()})
        blob = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob)
        for ln in blob.splitlines():
            if not ln.startswith("BASE2_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob.splitlines() if x.startswith("BASE2_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("BASE2_JSON:", 1)[1])

    ok, lines = validity(res, hits, year)
    print("\n🚧 بوّابةُ الصلاحية (‏§④ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why in lines:
        print(f"  {tag} {'✅' if good else '⛔'} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return 3

    print(f"\n📊 النتيجة (سعة 10 · rank_live · السنة {year}):")
    base = res[BASE_ARM]
    for arm in ARMS:
        r = res[arm]
        wr = r["win_rate"]
        print(f"  {arm:<7}: إشارات={r['signals']:<5} · محسومة={r['decided']:<5} · "
              f"دقة={wr}% ({r['wins']}✅/{r['losses']}🛑) · مأخوذة={r['taken']:<4} · "
              f"d50={r['d50']:<3} (d100={r['d100']:<3}) · R/صفقة={r['per_trade']} · "
              f"مرفوض بالسعة={r.get('rejected_cap')} · عدّاد={hits[arm]}")
    print("\n🧭 الفرق عن الأساس:")
    for arm in ARMS:
        if arm == BASE_ARM:
            continue
        r = res[arm]
        d = r["d50"] - base["d50"]
        pct = (f"{100.0 * d / base['d50']:+.1f}%" if base["d50"]
               else "مقامٌ صفر — لا نسبة")
        parts = [f"d50 {d:+d} ({pct})",
                 f"R/صفقة {r['per_trade'] - base['per_trade']:+.3f}"]
        if r["win_rate"] is not None and base["win_rate"] is not None:
            parts.append(f"الدقة {r['win_rate'] - base['win_rate']:+.1f} نقطة")
        if base["signals"]:
            parts.append(f"الإشارات {100.0 * r['signals'] / base['signals'] - 100:+.1f}%")
        print(f"  {arm:<7}: " + " · ".join(parts))
    print("\n⚠️ **تجربةُ كلفةٍ لا حافّة (§⑥):** «لم يُكلّف» ليست «ربّح» · والحكمُ "
          "يلزمه السنواتُ الثلاث والحرّاسَ الأربعة (‏د: ترفض LGHL — بالمِجَسّ) · "
          "وحدودُ §⑨ قائمة (انحياز بقاء · تشويه تقسيمات · بلا افتر · والمُرتِّب "
          "عند الصدفة · وLGHL حالةٌ تشخيصية لا اختبار).")
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        sys.exit(run_child(sys.argv[sys.argv.index("--child") + 1]))
    if "--probe" in sys.argv:
        sys.exit(probe())
    _rc = run_parent()
    try:                                  # المِجَسّ **بعد** الحكم فلا يؤثّر عليه
        probe()
    except Exception as _e:                                       # noqa: BLE001
        print(f"⚠️ المِجَسّ التشخيصيّ: {_e} — ولا يمسّ الحكم.")
    sys.exit(_rc)
