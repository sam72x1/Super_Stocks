#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎯📌 `T-ANCHOR` — الإرساء على **المستوى المُختبَر** (‏`anchor_prereg.md`).

**السؤال (§①):** هل إرساءُ الدفعات والوقف على **مستوًى مُختبَرٍ صامد**
(‏`tested_level` — «‏1.75 ضربها مرّتين ولا كسرها» `IMG_0451`) بدل **أدنى قاعِ
النافذة المتحرّك** (`pivot`) يحسّن التسليم؟ الشاهدُ الحيّ `BBLG`: رُشِّح في
اليوم الذي صنع فيه قاعَه ودفعاتُه على قاع اليوم نفسِه.

**الأذرع (§②) — ثلاثةٌ ولا رابعة، بميزانيةٍ ثابتة في تشغيلةٍ واحدة:**
`A0` الأساس (‏`pivot`) · `B1` مستوًى مُختبَرٌ **وإلّا ارتدادٌ لـ`pivot`** ·
`B2` مستوًى مُختبَرٌ **أو رفضٌ** باسمٍ مُسمًّى.
⛔ **ولا ذراعَ لشرط «الصمود 3 جلسات»**: قِيس في `T-STABILITY` **وفشل** (‏−13
منفجرًا/3 سنوات)، و«ولا كسرها» مستوفًى بنيويًّا في `tested_level`.
**متغيّرٌ واحد: المِرساة.** وأرقامُ `tested_level` **كما هي** (‏30/0.015/2) —
صفرُ معايرةٍ هنا (مقفولٌ `AN6`).

🔒 **صفر مسٍّ بالإنتاج:** العلمُ `BT_ANCHOR` مطفأٌ افتراضيًّا ⇒ الفارزُ **بت-بت**
(قفلٌ سلوكيّ `AN1`)، وكلُّ ذراعٍ في **عمليةٍ منفصلة** تضبط `CONFIG` بعد الاستيراد.
🧩 **وإعادةُ استعمالٍ لا بناء:** نفسُ هيكل `stability_arms.py` حرفيًّا (المُرتِّبُ
والسعةُ من `replay10` · `child_env` · بوّابةُ الصلاحية ثلاثيّةُ الحالة · إعادةُ
طبع الحكم آخرًا) — فلا يصير عندنا محرّكا قياسٍ مختلفان.
⚠️ **و`V3` خرقُها متوقَّعٌ بالبناء** بعد دمج `rrtruth` (تصريحٌ مؤرَّخ في التسجيل
قبل أوّل تشغيلة): تُعلَن ℹ️ «مقامٌ جديد» ولا تُسقط، والمقارنةُ بين الأذرع قائمة.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# الترتيبُ مقصود: الأساسُ أوّلًا ثم الأشدُّ تدرّجًا (يُستعمل في حرّاس الرتابة).
ARMS: dict[str, str] = {"A0": "", "B1": "tested", "B2": "tested_strict"}
BASE_ARM = "A0"
JUDGE_ARM = "B1"                 # §④: إن عبَرت الاثنتان تُفضَّل الأقلُّ قصًّا
#           — **مكتوبٌ قبل الأرقام** فلا تُختار الذراعُ بعديًّا.
# عدّادُ الرفض في توزيع رفض الإنتاج (‏`B2` وحدَها تُنتجه · `B1` ترتدّ ولا ترفض).
GATE_KEYS = ("M_لا_مستوى_مختبر",)
# 🔴 السعةُ التي قِيست عندها أرقامُ `INTEGRITY` — **وتُطابق الحيّة 15** بقرار المالك
#    2026-08-12 ⇒ فحصُ التكامل **نافذٌ لا مؤجَّل** (نفسُ منطق `base475_prereg §⑧`).
PUB_CAP = 15
# §⑤-V3 مِرساةُ التكامل: `A0` = الإنتاج (سقفُ القاعدة 120 بقرار المالك) = ذراعُ
# `B120` في `base475_result.md §①` **عند سعة 15** ⇒ 2024:25 · 2025:26 · 2026:15.
# ⚠️ ولا تُستعمل أرقامُ `base2_result.md` (‏25/18/10) — تلك **عند سعة 10** ومقارنةُ
#    سعتين باطلة (‏`base475_result.md §④-3` ينصّ عليها حرفيًّا).
INTEGRITY = {"A0": {"2024": 25, "2025": 26, "2026": 15}}
_LAST_GATE: list = []            # أسطرُ البوّابة — تُعاد طباعتُها آخرًا


def _mark(v) -> str:
    """‏✅ عبَر · ⛔ يُسقط · **ℹ️ يُعلَن ولا يُسقط** (‏`None`) — فلا يُقرأ المُعلَنُ
    نجاحًا ولا سقوطًا. (درسُ «سطرُ عرضٍ يكذب»: علامتان لثلاث حالاتٍ تكذب.)"""
    return "ℹ️" if v is None else ("✅" if v else "⛔")


def frozen_missing() -> str:
    """§⑩ خروج **4** — تُرجع المسارَ المفقود أو `""`.

    🔴 **ولماذا يُوقِف:** بلا اللقطة يمضي الباكتيست على **كون اليوم** ⇒ مجتمعٌ آخر
    وانحيازُ بقاءٍ أوسع، **ومِرساةُ `V3` بلا معنًى — بصمتٍ تام** (نظيرُ «اللقطةُ
    تدهس `symbols`» و«العلمُ الميّت»). **دالّةٌ نقيّةٌ لتُقفَل في الاتّجاهين:**
    المفقودُ يُوقِف · **والموجودُ لا يُوقِف** — فحارسٌ يمنع الصحيحَ **قفلٌ مكسور**
    لا حارسٌ أشدّ (درسُ `FF4`/`FF5`). مقفولٌ `ST11`."""
    p = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    return p if (p and not os.path.exists(p)) else ""


def child_env() -> dict:
    """أعلامُ الباكتيست — **بلا هذي لا يُحسَب `d50` ولا `R`** (‏`V4`؛ عيبٌ مقيس
    أسقط ثلاثَ تشغيلاتٍ لـ`T-CHASE` وطبع «‏+0» فقُرئ «لا فرق»). ولا علمَ يفترق
    بين الأذرع: الفرقُ **اسمُ الذراع** وحده."""
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
    """عدّادُ بوّابتَي الثبات من **توزيع رفض الإنتاج نفسِه** (‏`V2`).
    صيغتُه: «‏   1. M_ثبات_لم_يكتمل = 18220 (31.0%)». غيابٌ ⇒ 0."""
    n = 0
    for key in GATE_KEYS:
        n += sum(int(m.group(1)) for m in
                 re.finditer(re.escape(key) + r"[^=\n]*=\s*(\d+)", text or ""))
    return n


def probe(syms: str = None) -> int:
    """🔬 مِجَسٌّ تشخيصيّ **خارج الحكم** — يحسم الحارس (د): هل يُرفَض `BBLG`؟

    يُشغّل `_diagnose_symbol` **الإنتاجيّة** لكلّ ذراع (لا مقارنةً حسابيّةً منّي)،
    ويطبع `bars_after`/`held` صراحةً فيُقرأ السببُ لا الحكمُ وحده."""
    import Super_stock as S                                      # noqa: PLC0415
    names = [x.strip().upper() for x in
             (syms or os.environ.get("ANCH_PROBE_SYMS") or "BBLG").split(",")
             if x.strip()]
    if not names:
        return 0
    print(f"\n{'─' * 74}\n🔬 مِجَسٌّ تشخيصيّ (خارج الحكم · الحارس د): "
          f"{' · '.join(names)}\n{'─' * 74}", flush=True)
    try:
        hist = S.download_history(names)
    except Exception as e:                                        # noqa: BLE001
        print(f"  ⛔ تعذّر التحميل ({e}) — تشخيصٌ فلا يُسقط التجربة.")
        return 0
    for sym in names:
        df = hist.get(sym)
        if df is None or len(df) < 30:
            print(f"  ⚪️ {sym}: لا بيانات كافية.")
            continue
        _tl = S.tested_level(df)
        print(f"  📏 {sym}: مستوًى مُختبَر={_tl} (آخر شمعة {df.index[-1].date()}) "
              f"— الحارس (د) يشترط أن ترفضه `B2` فعلًا")
        for arm, val in ARMS.items():
            print(f"  ── تشخيصُ الإنتاج بالذراع {arm} ({val or 'الأساس'}) ──")
            _old = S.CONFIG.get("BT_ANCHOR")
            try:
                S.CONFIG["BT_ANCHOR"] = val
                S._diagnose_symbol(sym, df)
            except Exception as e:                                # noqa: BLE001
                print(f"     ⚠️ تعذّر التشخيص: {e}")
            finally:
                S.CONFIG["BT_ANCHOR"] = _old
    return 0


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    S.CONFIG["BT_ANCHOR"] = ARMS[arm]                  # **بعد** الاستيراد
    _p = __import__("inspect").signature(S.tested_level).parameters
    print(f"ARM_EFFECTIVE {arm} BT_ANCHOR={S.CONFIG['BT_ANCHOR']!r} "
          f"tested_level(lookback={_p['lookback'].default}, "
          f"tol={_p['tol'].default}, min_touches={_p['min_touches'].default})")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "gate": S.CONFIG["BT_ANCHOR"]}
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
    print("ANCH_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def _live_capacity() -> int:
    """السعةُ الحيّة **من `replay10` نفسِها** التي يستعملها الطفلُ في الحسم."""
    import replay10 as _rp                                        # noqa: PLC0415
    return int(_rp.CAPACITY)


def validity(res: dict, hits: dict, year: str) -> tuple[bool, list]:
    """§⑥ — شروطٌ تُقرأ **قبل** أيّ تفسير. تُرجع (سليم، أسطر).

    ⚖️ **وثلاثةُ أحكامٍ لا اثنان:** `True` عبَر · `False` **يُسقط** (خروج 3) ·
    و**`None` = «يُعلَن ولا يُسقط»** — وهي حالةُ `V3` وحدها بنصّ التسجيل §⑥.
    🔴 **ولماذا `V3` لا تُسقط:** صلاحيةُ الحكم قائمةٌ على المقارنة **الداخلية**
    (‏§③ ميزانيةٌ ثابتة: نفسُ اللقطة والسنة والمُرتِّب والسعة في تشغيلةٍ واحدة)،
    والمِرساةُ المنشورة **فحصُ محرّكٍ خارجيّ** — فسقوطُها يُبطل **المقارنةَ
    بالمنشور** لا المقارنةَ بين الأذرع. ⇒ تُعلَن بصوتٍ عالٍ وتُوسَم النتيجةُ
    «مقامٌ جديد»، ولا تُدفَن ولا تقتل التجربة."""
    order = list(ARMS)
    lines, ok = [], True

    # V1 · القيمُ النافذةُ متمايزةٌ ومطبوعة (وإلّا فالأذرعُ نسخةٌ واحدة = no-op)
    vals = [res[a]["gate"] for a in order]
    c1 = len(set(vals)) == len(order)
    lines.append(("V1", c1, "القيمُ النافذةُ ثلاثٌ متمايزة: "
                  + " · ".join(f"{a}={res[a]['gate']!r}" for a in order)))

    # V2 · العدّادُ يشتعل تدرّجًا — **كاشفُ الـno-op** (درسُ `BT_CANDLE`)
    # ‏`B1` ترتدّ لـ`pivot` فلا ترفض ⇒ عدّادُها صفر · و`B2` وحدَها ترفض.
    c2 = (hits[BASE_ARM] == 0 and hits["B1"] == 0 and hits["B2"] > 0)
    lines.append(("V2", c2, "عدّادُ الرفض يشتعل في `B2` وحدَها (‏A0=0 · B1=0 · B2>0): "
                  + " · ".join(f"{a}={hits[a]}" for a in order)))

    # V2ب · الإشاراتُ رتيبةٌ تنازليًّا (الأشدُّ لا يُنتج أكثر)
    sig = [res[a]["signals"] for a in order]
    c2b = all(sig[i] >= sig[i + 1] for i in range(len(sig) - 1))
    lines.append(("V2ب", c2b, "الإشاراتُ رتيبةٌ تنازليًّا: "
                  + " ≥ ".join(f"{a}={res[a]['signals']}" for a in order)))

    # V4 · المقياسُ الحاكم محسوبٌ لا غائب (بلا `child_env` يخرج None و«+0» كاذب)
    c4 = all(res[a].get("taken") is not None and res[a].get("d50") is not None
             for a in order)
    lines.append(("V4", c4, "المقياسُ الحاكم محسوبٌ لا غائب: "
                  + " · ".join(f"{a}.d50={res[a].get('d50')}" for a in order)))

    # V3 · فحصُ التكامل — **يُعلَن ولا يُسقط** (‏`None`)، ولا يُمرَّر صامتًا أبدًا
    cap_live = int(_live_capacity())
    ref = {a: INTEGRITY[a][year] for a in INTEGRITY if year in INTEGRITY[a]}
    got = {a: res[a].get("d50") for a in ref}
    side = " · ".join(f"{a}: مقيس={got[a]} منشور={ref[a]}" for a in sorted(ref))
    if not ref:
        lines.append(("V3", None, "فحصُ التكامل — **سنةٌ غير مرجعية**: لا مِرساةَ "
                      "منشورة ⇒ **مقامٌ جديد يُعلَن** ولا يُقارَن بالمنشور"))
    elif cap_live != PUB_CAP:
        lines.append(("V3", None, f"فحصُ التكامل **مؤجَّلٌ ومُعلَن**: السعةُ الحيّة "
                      f"{cap_live} ≠ سعةُ النشر {PUB_CAP} ⇒ المقارنةُ عبر سعتين "
                      f"باطلة والحكمُ **داخل التشغيلة**. للسجلّ — " + side))
    else:
        bad = [f"{a}:{got[a]}≠{ref[a]}" for a in ref if got[a] != ref[a]]
        lines.append(("V3", (True if not bad else None),
                      f"فحصُ التكامل بت-بت (سعة {cap_live}) — {side}"
                      + (f" ⇒ 🔴 **خرقٌ: {' · '.join(bad)} ⇒ مقامٌ جديد** — "
                         "المقارنةُ بالمنشور باطلةٌ والمقارنةُ بين الأذرع قائمة"
                         if bad else "")))

    for _t, _o, _w in lines:
        if _o is not None:                       # `None` = يُعلَن ولا يُسقط
            ok = ok and _o
    return ok, lines


def run_parent() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    print(f"\n{'=' * 78}\n🧱🕯️ T-ANCHOR — الإرساء على المستوى المُختبَر · السنة {year}"
          f"\n{'=' * 78}", flush=True)
    _fz = frozen_missing()
    if _fz:
        print(f"⛔ **اللقطةُ المجمَّدة مفقودة**: {_fz!r} غيرُ موجود ⇒ الباكتيست كان "
              "سيمضي على كون اليوم بمجتمعٍ آخر **بصمت** ⇒ توقّفٌ صريح (خروج 4).")
        return 4
    res, hits = {}, {}
    for arm, val in ARMS.items():
        print(f"\n──── الذراع {arm} ({val or 'الأساس — pivot المتحرّك'}) ────", flush=True)
        p = subprocess.run([sys.executable, os.path.abspath(__file__),
                            "--child", arm], capture_output=True, text=True,
                           env={**dict(os.environ), **child_env()})
        blob = (p.stdout or "") + "\n" + (p.stderr or "")
        hits[arm] = gate_hits(blob)
        for ln in blob.splitlines():
            if not ln.startswith("ANCH_JSON:"):
                print(f"  [{arm}] {ln}")
        rows = [x for x in blob.splitlines() if x.startswith("ANCH_JSON:")]
        if p.returncode != 0 or not rows:
            print(f"⛔ الذراع {arm} سقطت (rc={p.returncode}) — لا حكم.")
            return 2
        res[arm] = json.loads(rows[-1].split("ANCH_JSON:", 1)[1])

    ok, lines = validity(res, hits, year)
    globals()["_LAST_GATE"] = lines
    print("\n🚧 بوّابةُ الصلاحية (‏§⑥ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why in lines:
        print(f"  {tag} {_mark(good)} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return 3

    _anchored = all(g is True for t, g, _ in lines if t == "V3")
    print(f"\n📊 النتيجة (سعة {_live_capacity()} · rank_live · السنة {year}"
          + ("" if _anchored else " · ⚠️ **مقامٌ جديد** — لا تُقارَن بالمنشور")
          + "):")
    base = res[BASE_ARM]
    for arm in ARMS:
        r = res[arm]
        print(f"  {arm:<3}: إشارات={r['signals']:<5} · محسومة={r['decided']:<5} · "
              f"دقة={r['win_rate']}% ({r['wins']}✅/{r['losses']}🛑) · "
              f"مأخوذة={r['taken']:<4} · d50={r['d50']:<3} (d100={r['d100']:<3}) · "
              f"R/صفقة={r['per_trade']} · مرفوض بالسعة={r.get('rejected_cap')} · "
              f"عدّاد={hits[arm]}")
    print("\n🧭 الفرق عن الأساس (‏والحاكمةُ `B1` بنصّ §④):")
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
            parts.append(f"الإشارات "
                         f"{100.0 * r['signals'] / base['signals'] - 100:+.1f}%")
        mark = " 🥇 الحاكمة" if arm == JUDGE_ARM else ""
        print(f"  {arm:<3}: " + " · ".join(parts) + mark)
    print("\n⚠️ **تجربةُ كلفةٍ لا حافّة (§⑧):** «لم يُكلّف» ليست «ربّح» · والحكمُ "
          "يلزمه السنواتُ الثلاث والحرّاسَ الأربعة (‏د: يرفض BBLG — بالمِجَسّ) · "
          "والقراءةُ (ج) **مجمَّعةٌ** بنصّ التسجيل · وحدودُ §⑧ قائمة (انحياز بقاء · "
          "تشويه تقسيمات · بلا افتر · والمُرتِّب عند الصدفة).")
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
    # 🔴 **الحكمُ يُعاد طبعُه آخرًا** (درسُ `T-BASE-475`: مُخرَجُ المِجَسّ الطويل
    #    دفنَ سطرَ سببِ السقوط خارج ذيلِ السجلّ فرجعت ثلاثُ تشغيلاتٍ بلا سببٍ مقروء).
    print(f"\n{'=' * 78}\n🏁 رمزُ الخروج: {_rc}"
          + ("  ✅ البوّابةُ عبرت" if _rc == 0
             else "  ⛔ **بوّابةُ الصلاحية سقطت**" if _rc == 3
             else "  ⛔ **لقطةٌ مفقودة**" if _rc == 4
             else "  ⛔ ذراعٌ سقطت (rc≠0) — لا حكم")
          + f"\n{'=' * 78}")
    for _t, _o, _w in (_LAST_GATE or []):
        print(f"  {_t} {_mark(_o)} {_w}")
    sys.exit(_rc)
