#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧱⛰️ T-CEILING — سلّمُ سقف الانهيار `MAX_DROP_PCT` (‏`ceiling_prereg.md`).

**السؤال (§①):** كم يُكلّف رفعُ سقف `M2` — الجدارُ الذي يحجب `RUBI` سبعةَ أيامٍ
متتالية ويصطاد عائلةَ فيصل (‏`rubi_case.md`)؟
**الأذرع (§②):** `C0` الأساس (‏99.94998…) · `C1` 99.99 · `C2` 99.999 ·
`C3` **100.0 = بلا سقف** — **أربعٌ ولا خامسة**، وفي **تشغيلةٍ واحدةٍ بميزانيةٍ
ثابتة** (نفسُ اللقطة والكون والسعة والمُرتِّب والنافذة).

🔒 **صفر مسٍّ بالإنتاج:** الوالدُ لا يستورد `Super_stock`؛ كلُّ ذراعٍ في **عملية
منفصلة** تضبط `CONFIG` **بعد** الاستيراد.

🔴🔴 **ولماذا «بعد الاستيراد» شرطٌ لا أسلوب (‏§⑧ من التسجيل):** تمريرُ
`BT_MAX_DROP_PCT` بالبيئة **ميّتٌ بنيويًّا** عند `FAISAL_ONLY=1` —
`_apply_backtest_overrides` عند `Super_stock.py:769` ثم `apply_faisal_only`
عند `:945` تدهسه بـ`cfg.update(ov)` (‏والظرفُ يحوي `MAX_DROP_PCT` بالضبط).
فالضبطُ هنا **بعد** اكتمال الاستيراد، و`V1` يطبع القيمةَ النافذة فيستحيل أن
تمرّ ذراعٌ ميّتة.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# الترتيبُ مقصود: الأساسُ أوّلًا ثم **الأوسعُ تدرّجًا** (يُستعمل في حرّاس الرتابة
# `V2`/`V5`). ⛔ ولا ذراعَ تُضاف بعد رؤية الأرقام (‏§② من التسجيل).
ARMS: dict[str, float] = {"C0": 99.94998260261913, "C1": 99.99,
                          "C2": 99.999, "C3": 100.0}
BASE_ARM = "C0"
GATE_KEY = "M2_هبوط_فوق_97"     # عدّادُ البوّابة في توزيع رفض الإنتاج
# 🔴 السعةُ التي قِيست عندها أرقامُ `INTEGRITY` — **وتُطابق الحيّة 15** ⇒ `V3`
#    يُفرَض **بت-بت بلا تأجيل** (بخلاف `base2_arms` حيث اختلفت السعتان).
PUB_CAP = 15
# §⑤ `V3` فحصُ التكامل: `C0` = الإنتاجُ الحاليّ حرفيًّا ⇒ يجب أن يعيد أرقامَ
#     الذراع `B2` المنشورة في `anchor_prereg.md §⑫` (‏sum = 88).
INTEGRITY = {"C0": {"2024": 32, "2025": 41, "2026": 15}}
_LAST_GATE: list = []           # أسطرُ البوّابة — تُعاد طباعتُها آخرًا


def frozen_missing() -> str:
    """§④ خروج **4** — تُرجع المسارَ المفقود أو `""`.

    بلا اللقطة يمضي الباكتيست على **كون اليوم** ⇒ مجتمعٌ آخر ومِرساةُ `V3` بلا
    معنًى **بصمتٍ تام**. **دالّةٌ نقيّةٌ لتُقفَل في الاتّجاهين:** المفقودُ يُوقِف
    · **والموجودُ لا يُوقِف** — فحارسٌ يمنع الصحيحَ **قفلٌ مكسور** لا أشدّ."""
    p = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    return p if (p and not os.path.exists(p)) else ""


def child_env() -> dict:
    """أعلامُ الباكتيست — **بلا هذي لا يُحسَب `d50` ولا `R`** (‏`V4`؛ عيبٌ مقيس
    أسقط ثلاثَ تشغيلاتٍ لـ`T-CHASE` وطبع «‏+0» فقُرئ «لا فرق»). ولا علمَ يفترق
    بين الأذرع: الفرقُ **سقفُ البوّابة** وحده."""
    return {"SCREENER_MODE": "BACKTEST", "BT_REPLAY10": "1",
            "BT_ENVVALS": "1", "BT_POTENTIAL": "1"}


def rates(trades) -> dict:
    """نسبةُ الدقة **بمقامها** — لا نسبةَ بلا عددِ محسومة."""
    w = sum(1 for t in trades if t.get("outcome") == "win")
    ls = sum(1 for t in trades if t.get("outcome") == "loss")
    dec = w + ls
    return {"signals": len(trades), "decided": dec, "wins": w, "losses": ls,
            "no_fill": sum(1 for t in trades if t.get("outcome") == "no_fill"),
            "win_rate": (round(100.0 * w / dec, 1) if dec else None)}


def gate_hits(text: str) -> int:
    """عدّادُ جدار السقف من **سطر التجميع العالميّ وحده**.

    صيغتُه المرساة: «‏   1. M2_هبوط_فوق_97 = 18220 (31.0%)» — **مرقَّمةٌ** بخلاف
    سطر كلّ رمز («‏باكتيست·أسباب AAA (…): M2_هبوط_فوق_97=5»).

    🐞 **عيبٌ أمسكه ناقدٌ خصوميّ قبل أيّ تشغيلة — والعدّادُ كان مضروبًا في ٢:**
    السطرُ لكلّ رمزٍ **غيرُ محروسٍ بـ`market`** (‏`Super_stock.py:18272`) فيُطبع
    في السوق الكامل أيضًا، ومجموعُ سطور الرموز = التجميعُ نفسُه ⇒ الرقعةُ الحرّة
    كانت تجمعهما (‏مُستنسَخٌ على سجلّ `RUBI`: 13 + 13 = **26** والحقيقيّ 13).
    ⚠️ **ويمسّ أدواتٍ أخرى:** `base2_arms.gate_hits`/`base_arms`/`stability_arms`
    بالنمط الحرّ نفسِه ⇒ **عدّاداتُ الجدار المنشورة هناك مضروبةٌ في ٢** (أحكامُها
    على `d50`/`R` فلا تتأثّر) — **يُبلَّغ ولا يُصحَّح صامتًا في ملفٍّ منشور.**"""
    # 🐞🐞 **ولا مِرساةَ بدايةِ سطر** — عيبٌ ثانٍ في إصلاحي كشفته **القنارية** لا
    #    القراءة: سطرُ الإنتاج مسبوقٌ بختمٍ («‏[04:38:41] باكتيست·   1. KEY = 13»)
    #    فمرساةُ `^` تطابق **صفرًا** ⇒ العدّادُ صفرٌ في الأذرع الأربع ⇒ `V2` أسقط
    #    تشغيلةً **سليمة**. 🧭 **وفكستشرُ القفل هو الكاذب**: كتبتُه بلا الختم
    #    فمرّ أخضرَ على نمطٍ لا يقع في الإنتاج — «القفلُ لا يحرس إلّا بقدر ما
    #    تُشبه عيّنتُه الواقع». المميِّزُ الباقي **`N. ` قبل المفتاح** (سطرُ الرمز
    #    بلا ترقيمٍ وبلا مسافاتٍ حول `=`) وهو وحده يكفي للتفرقة.
    return sum(int(m.group(1)) for m in
               re.finditer(r"\d+\.\s*" + re.escape(GATE_KEY) + r"\s*=\s*(\d+)",
                           text or ""))


def ratio_needed(cap: float) -> float:
    """📐 ترجمةُ السقف إلى نسبةٍ مفهومة (‏§①): `drop > cap` ⟺ `hi52/price >
    1/(1−cap/100)`. **دالّةٌ نقيّة** — و`cap ≥ 100` ⇒ `inf` (بلا سقف)."""
    x = 1.0 - float(cap) / 100.0
    return float("inf") if x <= 0 else 1.0 / x


def probe(syms: str = None) -> int:
    """🔬 مِجَسُّ `RUBI` — **تشخيصٌ مُعلَنٌ خارج الحكم** (‏§⑥-د).

    🔴 **ولا يقلب حكمًا بحالٍ:** «يقبل RUBI» ليس معيارَ نجاح (‏السهمُ مختارٌ
    **بعد الحدث**) — الغرضُ أن يُطبَع **أيُّ جدارٍ يليه** تحت كلّ ذراع.
    يُشغَّل `_diagnose_symbol` **الإنتاجيّ** لا مقارنةً حسابيّةً منّي."""
    import Super_stock as S                                      # noqa: PLC0415
    names = [x.strip().upper() for x in
             (syms or os.environ.get("CEIL_PROBE_SYMS") or "RUBI").split(",")
             if x.strip()]
    if not names:
        return 0
    print(f"\n{'─' * 74}\n🔬 مِجَسٌّ تشخيصيّ (خارج الحكم · §⑥-د): "
          f"{' · '.join(names)}\n{'─' * 74}", flush=True)
    try:
        hist = S.download_history(names)
    except Exception as e:                                        # noqa: BLE001
        print(f"  ⛔ تعذّر التحميل ({e}) — تشخيصٌ فلا يُسقط التجربة.")
        return 0
    for sym in names:
        df = hist.get(sym)
        if df is None or len(df) < 60:
            print(f"  ⚪️ {sym}: لا بيانات كافية.")
            continue
        hi52 = float(df["High"].tail(252).max())
        price = float(df["Close"].iloc[-1])
        rat = (hi52 / price) if price > 0 else float("inf")
        drop = (1.0 - price / hi52) * 100.0 if hi52 > 0 else 0.0
        print(f"  📏 {sym}: سعر=${price:.4f} · قمّة52أ=${hi52:,.2f} ⇒ "
              f"**النسبة ×{rat:,.1f}** · الهبوط {drop:.6f}% "
              f"(آخر شمعة {df.index[-1].date()})")
        for arm, cap in ARMS.items():
            need = ratio_needed(cap)
            print(f"     {arm:<4} (سقف {cap:.5f} ⇒ يرفض فوق ×{need:,.0f}): "
                  + ("❌ يُرفَض M2_هبوط_فوق_97" if drop > cap else "✅ يمرّ M2"))
        # 🔒 **حكمُ كلّ ذراعٍ بكودِ الإنتاج نفسِه** — فالمقارنةُ أعلاه استدلالٌ
        #    منّي، وهذي شهادةُ الفارز. والاستعادةُ في `finally` فلا يتسرّب سقفٌ.
        for arm, cap in ARMS.items():
            print(f"  ── تشخيصُ الإنتاج بسقف {arm} ({cap:.5f}) ──")
            _old = S.CONFIG["MAX_DROP_PCT"]
            try:
                S.CONFIG["MAX_DROP_PCT"] = float(cap)
                S._diagnose_symbol(sym, df)
            except Exception as e:                                # noqa: BLE001
                print(f"     ⚠️ تعذّر التشخيص: {e}")
            finally:
                S.CONFIG["MAX_DROP_PCT"] = _old
    return 0


def trades_path(arm: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        f"ceil_trades_{arm}.json")


def snapshot_id() -> dict:
    """🔒 **هويّةُ اللقطة — برهانُ «الميزانيةِ الثابتة» لا دعواها.**

    `frozen_missing` تفحص **وجودَ الملفّ** فقط، و`run_backtest` عند فسادِه
    **لا يسقط** بل يرتدّ إلى تحميلٍ حيّ من ياهو ⇒ مشيٌ على **كون اليوم**
    بأرقامٍ معقولةِ الشكل وحارسُ `rc=4` يمرّ. فتُقرأ الهويّةُ فعلًا
    (‏`as-of` وعددُ الرموز) ويُشترَط تطابقُها في الأذرع الأربع (‏`V7`)."""
    import Super_stock as S                                      # noqa: PLC0415
    p = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    if not p:
        return {"asof": None, "n": None}
    hist, _sp, asof = S.load_frozen_dataset(p)
    return {"asof": (str(asof) if asof else None),
            "n": (len(hist) if hist else 0)}


def run_child(arm: str) -> int:
    import Super_stock as S                                      # noqa: PLC0415
    S.CONFIG["MAX_DROP_PCT"] = float(ARMS[arm])           # **بعد** الاستيراد
    print(f"ARM_EFFECTIVE {arm} MAX_DROP_PCT={S.CONFIG['MAX_DROP_PCT']!r}")
    snap = snapshot_id()
    print(f"SNAP {arm} as-of={snap['asof']} n_symbols={snap['n']}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "cap": S.CONFIG["MAX_DROP_PCT"], "snap": snap,
           "expl": float(S.CONFIG["EXPLOSION_PCT"])}
    out.update(rates(trades))
    # 🔴 **الحسمُ المحفظيّ انتقل إلى الوالد** (‏`V8`): `candidates_from_trades`
    #    يبني محورَ الجلسات **من صفقات الذراع وحدها** ⇒ ذراعٌ بإشاراتٍ أكثر
    #    يصير محورُها **أكثفَ** فتطول مدّةُ إشغال الخانة **بوحدات الفهرس** لنفس
    #    المدى التقويميّ ⇒ ازدحامٌ أشدّ ⇒ `d50` يتحرّك **لسببٍ حسابيٍّ محض**.
    #    العلاجُ `extra_dates` (وسيطٌ **قائمٌ في `replay10` ولا تستعمله أداة**):
    #    الوالدُ يوحّد المحورَ باتّحاد تواريخ الأذرع الأربع. فيكتب الطفلُ صفقاته.
    wf = [t for t in trades if t.get("exit_date")]
    with open(trades_path(arm), "w", encoding="utf-8") as fh:
        json.dump(wf, fh, ensure_ascii=False, default=str)
    out["wf"] = len(wf)
    print("CEIL_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def portfolio(wf_by_arm: dict, expl: float) -> dict:
    """🏦 الحسمُ المحفظيُّ للأذرع **على محورِ جلساتٍ موحَّد** (‏`V8`).

    `extra_dates` = اتّحادُ تواريخ الأذرع الأربع ⇒ **نفسُ الفهرس لكلّها**، فمدّةُ
    إشغال الخانة تُقاس بوحدةٍ واحدة ولا يصنع الفرقَ اختلافُ كثافة المحور."""
    import replay10 as RP                                        # noqa: PLC0415
    dates = set()
    for rows in wf_by_arm.values():
        for t in rows:
            if t.get("date"):
                dates.add(str(t["date"]))
            if t.get("exit_date"):
                dates.add(str(t["exit_date"]))
    out = {}
    for arm, rows in wf_by_arm.items():
        if not rows:
            out[arm] = {"taken": None, "d50": None}
            continue
        cands, idx, oc = RP.candidates_from_trades(rows, extra_dates=sorted(dates))
        res = RP.replay(cands, outcome_of=oc, ranker=RP.rank_live,
                        sessions=range(0, len(idx)))
        taken = res["taken"]
        rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]

        def _d(thr, _tk=taken):
            n = 0
            for c in _tk:
                p = c.payload
                if p.get("mg_outcome") in (None, "no_fill"):
                    continue
                try:
                    if float(p.get("mg_pre_stop") or 0.0) >= thr:
                        n += 1
                except (TypeError, ValueError):
                    pass
            return n
        # 🔴 **`no_fill` داخل المأخوذين يُطبَع** — لأن `r_unit` تُرجع **0.0R** لغير
        #    المُعبَّأة (اختيارٌ موثَّقٌ في `replay10`: الخانةُ استُهلكت)، والأساسُ
        #    **سالب** ⇒ كلُّ اسمٍ جديدٍ لا يُعبَّأ **يرفع** المتوسطَ نحو الصفر.
        #    ⇒ المعيار (ج) قد يمرّ **بآليةٍ لا بحافّة**، والشاهدُ هذا العدّاد.
        #    **والمقياسُ المسجَّل لا يُبدَّل** (تحريكُ هدف) — يُعرَض معه فقط.
        nf = sum(1 for c in taken if (c.payload or {}).get("mg_outcome") == "no_fill"
                 or (c.payload or {}).get("outcome") == "no_fill")
        out[arm] = {"taken": len(taken), "rejected_cap": res["rejected_cap"],
                    "d50": _d(expl), "d100": _d(100.0), "axis": len(idx),
                    "taken_no_fill": nf,
                    "per_trade": (round(sum(rs) / len(taken), 4) if taken else 0.0)}
    return out


def _live_capacity() -> int:
    """السعةُ الحيّة **من `replay10` نفسِها** التي يستعملها الطفلُ في الحسم —
    لا رقمٌ يدويّ (وهي مربوطةٌ بـ`WATCHLIST_SIZE` بقفل `REPLAY10🔒`)."""
    import replay10 as _rp                                        # noqa: PLC0415
    return int(_rp.CAPACITY)


def _mark(v) -> str:
    """‏✅ عبَر · ⛔ يُسقط · **ℹ️ يُعلَن ولا يُسقط** (‏`None`) — علامتان لثلاث
    حالاتٍ تكذب (درسُ `ST10`)."""
    return "ℹ️" if v is None else ("✅" if v else "⛔")


def validity(res: dict, hits: dict, year: str) -> tuple[bool, list]:
    """§⑤ — الشروطُ تُقرأ **قبل** أيّ تفسير. تُرجع (سليم، أسطر).

    🔴 **وتمييزٌ حاسمٌ اتُّخذ قبل أيّ رقم (‏§⑤-ب من التسجيل):** ما هو **بنيويّ**
    يُسقِط، وما ليس بنيويًّا **يُعلَن ولا يُسقِط** — لأن `backtest_symbol` يقفز
    `i += fwd` بعد كلّ صفقة، فالأذرعُ **ليست متداخلة**: قبولٌ أبكر في ذراعٍ أوسع
    **يبتلع** نافذةً كاملة فقد تنقص إشاراتُها. ⇒ رتابةُ الإشارات ورتابةُ العدّاد
    **ليستا خاصّيتين بنيويّتين**، وجعلُهما بوّابةً قاطعةً كان **يُسقط تشغيلةً
    سليمة** = حارسٌ يمنع الصحيح، وهو **قفلٌ مكسورٌ لا أشدّ**."""
    order = list(ARMS)                       # الأساس ثم الأوسعُ تدرّجًا
    lines, ok = [], True

    caps = [res[a]["cap"] for a in order]
    c1 = len({round(c, 9) for c in caps}) == len(order)
    lines.append(("V1", c1, "القيمُ النافذة أربعٌ متمايزة: "
                  + " · ".join(f"{a}={res[a]['cap']:.5f}" for a in order)))

    # `V2` **حارسُ الـno-op — بشقِّه البنيويّ وحده**: بلا سقفٍ (`C3`) يستحيل
    #  رياضيًّا أن تقع رفضةُ سقفٍ (‏`drop < 100` لأن `price > 0`) ⇒ **صفرٌ
    #  بالضبط**؛ وبالسقف النافذ (`C0`) يجب أن يرفض شيئًا وإلّا فالجدارُ خامد.
    c2 = bool(hits[order[-1]] == 0 and hits[BASE_ARM] > 0)
    lines.append(("V2", c2, "العلمُ فعّال (بنيويّ): `C3`=صفر و`C0`>صفر — "
                  + " · ".join(f"{a}={hits[a]}" for a in order)))

    c4 = all(res[a].get("taken") is not None and res[a].get("d50") is not None
             for a in order)
    lines.append(("V4", c4, "المقياسُ الحاكم محسوبٌ لا غائب: "
                  + " · ".join(f"{a}.d50={res[a].get('d50')}" for a in order)))

    # `V7` **هويّةُ اللقطة** — برهانُ «الميزانيةِ الثابتة»: نفسُ `as-of` ونفسُ
    #  عددِ الرموز في الأربع (ملفٌّ تالفٌ يرتدّ لتحميلٍ حيّ **بلا سقوط**).
    snaps = {a: (res[a].get("snap") or {}) for a in order}
    ids = {(s.get("asof"), s.get("n")) for s in snaps.values()}
    c7 = len(ids) == 1 and all(s.get("n") for s in snaps.values())
    lines.append(("V7", c7, "هويّةُ اللقطة واحدةٌ في الأربع (ميزانيةٌ ثابتة): "
                  + " · ".join(f"{a}={snaps[a].get('asof')}/{snaps[a].get('n')}"
                               for a in order)))

    # `V8` **محورُ الجلسات موحَّد** — وإلّا تحرّك `d50` بكثافةِ المحور لا بالسقف.
    ax = {res[a].get("axis") for a in order}
    c8 = len(ax) == 1 and None not in ax
    lines.append(("V8", c8, f"محورُ الجلسات موحَّدٌ للأربع: {sorted(x for x in ax)}"))

    # ℹ️ **رصدٌ يُعلَن ولا يُسقط** (غيرُ بنيويّ — انظر docstring):
    mono_h = all(hits[order[i]] >= hits[order[i + 1]] for i in range(len(order) - 1))
    lines.append(("R1", None if mono_h else None,
                  ("رتابةُ العدّاد ✔" if mono_h else "🔎 **العدّادُ غيرُ رتيب**")
                  + " (رصدٌ لا بوّابة — `i += fwd` يجعل الأذرعَ غيرَ متداخلة): "
                  + " ≥ ".join(f"{a}={hits[a]}" for a in order)))
    sig = [res[a]["signals"] for a in order]
    mono_s = all(sig[i] <= sig[i + 1] for i in range(len(sig) - 1))
    lines.append(("R2", None,
                  ("رتابةُ الإشارات ✔" if mono_s else "🔎 **الإشاراتُ غيرُ رتيبة**")
                  + " (رصدٌ لا بوّابة): "
                  + " ≤ ".join(f"{a}={res[a]['signals']}" for a in order)))

    # `V3` فحصُ التكامل — **بت-بت بلا تأجيل** لأن السعتين متساويتان (15).
    #  🔴 ولو اختلفتا يومًا: يُعلَن ويُطبَع الرقمان ولا يُمرَّر صامتًا.
    cap_live = int(_live_capacity())
    ref = {a: INTEGRITY[a][year] for a in INTEGRITY if year in INTEGRITY[a]}
    got = {a: res[a].get("d50") for a in ref}
    side = " · ".join(f"{a}: مقيس={got[a]} منشور={ref[a]}" for a in sorted(ref))
    if not ref:
        c3 = False
        lines.append(("V3", c3, "فحصُ التكامل — **سنةٌ غير مرجعية** (تُرفَض عمدًا)"))
    elif cap_live == PUB_CAP:
        bad = [f"{a}:{got[a]}≠{ref[a]}" for a in ref if got[a] != ref[a]]
        c3 = not bad
        lines.append(("V3", c3, f"فحصُ التكامل بت-بت (سعة {cap_live}) — {side}"
                      + (f" ⇒ خرق: {' · '.join(bad)}" if bad else "")))
    else:
        c3 = True
        lines.append(("V3", c3, f"فحصُ التكامل **مؤجَّلٌ ومُعلَن**: السعةُ الحيّة "
                      f"{cap_live} ≠ سعةُ النشر {PUB_CAP} ⇒ المقارنةُ عبر سعتين "
                      f"باطلة والحكمُ **داخل التشغيلة**. للسجلّ — " + side))

    for _t, _o, _w in lines:
        if _o is None:                       # ℹ️ رصدٌ يُعلَن ولا يُسقط
            continue
        ok = ok and _o
    return ok, lines


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 78}\n🧱⛰️ T-CEILING — سلّمُ سقف الانهيار · السنة {year}"
          f"\n{'=' * 78}", flush=True)
    _fz = frozen_missing()
    if _fz:
        print(f"⛔ لقطةُ PIT مفقودة ({_fz}) — لا تشغيلَ على كون اليوم (§④).")
        return 4
    res, hits = {}, {}
    for arm in ARMS:
        print(f"\n──── الذراع {arm} (سقف {ARMS[arm]:.5f} ⇒ يرفض فوق "
              f"×{ratio_needed(ARMS[arm]):,.0f}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env={**dict(os.environ), **child_env()})
        blob = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob)
        for ln in blob.splitlines():
            if not ln.startswith("CEIL_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob.splitlines() if x.startswith("CEIL_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("CEIL_JSON:", 1)[1])

    # 🏦 الحسمُ المحفظيّ **في الوالد على محورٍ موحَّد** (‏`V8`).
    wf_by_arm = {}
    for arm in ARMS:
        try:
            with open(trades_path(arm), encoding="utf-8") as fh:
                wf_by_arm[arm] = json.load(fh)
        except Exception as e:                                    # noqa: BLE001
            print(f"⛔ تعذّر قراءة صفقات {arm}: {e} — لا حكم.")
            return 2
    port = portfolio(wf_by_arm, float(res[BASE_ARM].get("expl") or 50.0))
    for arm in ARMS:
        res[arm].update(port.get(arm) or {})

    ok, lines = validity(res, hits, year)
    globals()["_LAST_GATE"] = lines        # لإعادةِ الطبع آخرًا
    print("\n🚧 بوّابةُ الصلاحية (‏§⑤ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why in lines:
        print(f"  {tag} {_mark(good)} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return 3

    print(f"\n📊 النتيجة (سعة {_live_capacity()} · rank_live · السنة {year}):")
    base = res[BASE_ARM]
    for arm in ARMS:
        r = res[arm]
        print(f"  {arm:<4}: إشارات={r['signals']:<5} · محسومة={r['decided']:<5} · "
              f"غير_مُعبّأة={r['no_fill']:<4} · "
              f"دقة={r['win_rate']}% ({r['wins']}✅/{r['losses']}🛑) · "
              f"مأخوذة={r['taken']:<4} (منها بلا تعبئة={r.get('taken_no_fill')}) · "
              f"d50={r['d50']:<3} (d100={r['d100']:<3}) · "
              f"R/صفقة={r['per_trade']} · مرفوض بالسعة={r.get('rejected_cap')} · "
              f"عدّادُ السقف={hits[arm]}")
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
            parts.append(
                f"الإشارات {100.0 * r['signals'] / base['signals'] - 100:+.2f}%")
        print(f"  {arm:<4}: " + " · ".join(parts))
    print("\n⚠️ **حدودُ §⑨ قائمةٌ وتُقرأ مع الأرقام:** هذي تقيس «كم يُكلّف "
          "**قبولُ** أثر التقسيم» لا «كم يُكلّف **تصحيحُه**» (‏التصحيحُ `R1` "
          "أغلقه المالك) · وانحيازُ بقاء · وبلا افتر · والمُرتِّبُ عند الصدفة "
          "بسعة 15 ⇒ **‏±3 داخل الضجيج** · و«يُقبَل مرشّحًا» ≠ «يصل المالك» · "
          "و`RUBI` **تشخيصٌ لا معيار** (‏§⑥-د).")
    print("⚠️ **وثلاثةُ قيودٍ أضافها نقدٌ خصوميّ قبل الأرقام:** ① `M13`/`M14` "
          "**لا تعملان في الباكتيست** (‏`scan_market` وحدها تُطبّقهما) ⇒ داخلٌ "
          "جديدٌ منهارٌ قد تحذفه `M14` حيًّا · ② `r_unit` تُرجع **0.0R لغير "
          "المُعبَّأة** والأساسُ سالب ⇒ كلُّ اسمٍ لا يُعبَّأ **يرفع** المتوسط "
          "نحو الصفر ⇒ المعيار (ج) قد يمرّ **بآليةٍ لا بحافّة** (والعدّادُ "
          "«منها بلا تعبئة» أعلاه هو الشاهد) · ③ الداخلون الجدد (هبوطٌ فوق "
          "‏99.95%) **يتجنّبون نقصَ `M2` اللين تلقائيًّا** (‏`MIN_DROP_PCT`="
          "96.92) فليسوا عيّنةً عشوائيّةً من المرشّحين.")
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
    # 🔴 **الحكمُ يُعاد طبعُه آخرًا:** مُخرَجُ المِجَسّ طويلٌ فيدفن سطرَ سببِ
    #    السقوط خارج ذيلِ السجلّ (وقع فعلًا في `T-BASE-475`: ثلاثُ تشغيلاتٍ
    #    رجعت `rc=3` **بلا سببٍ مقروء**).
    print(f"\n{'=' * 78}\n🏁 رمزُ الخروج: {_rc}"
          + ("  ✅ البوّابةُ عبرت" if _rc == 0
             else "  ⛔ **بوّابةُ الصلاحية سقطت**" if _rc == 3
             else "  ⛔ لقطةُ PIT مفقودة" if _rc == 4
             else "  ⛔ ذراعٌ سقطت (rc≠0) — لا حكم")
          + f"\n{'=' * 78}")
    # 🐞 وإعادةُ الطبع كانت تستعمل ثنائيّةً فتطبع **‏⛔ على الرصد `ℹ️`** — علامتان
    #    لثلاث حالاتٍ تكذب (درسُ `ST10`)، وقد وقعت فعلًا في قنارية 2026.
    for _t, _o, _w in (_LAST_GATE or []):
        print(f"  {_t} {_mark(_o)} {_w}")
    sys.exit(_rc)
