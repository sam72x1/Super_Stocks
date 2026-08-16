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
    """عدّادُ جدار السقف من **توزيع رفض الإنتاج نفسِه** (‏`V2`).
    صيغتُه: «‏   1. M2_هبوط_فوق_97 = 18220 (31.0%)». غيابُ المفتاح ⇒ 0 —
    **وهو بعينه ما يشترطه `V2` عند `C3`** (بلا سقفٍ ⇒ صفرُ رفضاتِ سقف)."""
    return sum(int(m.group(1)) for m in
               re.finditer(re.escape(GATE_KEY) + r"[^=\n]*=\s*(\d+)", text or ""))


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


def run_child(arm: str) -> int:
    import replay10 as RP                                        # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    S.CONFIG["MAX_DROP_PCT"] = float(ARMS[arm])           # **بعد** الاستيراد
    print(f"ARM_EFFECTIVE {arm} MAX_DROP_PCT={S.CONFIG['MAX_DROP_PCT']!r}")
    trades = S.run_backtest() or []
    out = {"arm": arm, "year": (os.environ.get("BACKTEST_YEAR") or "?"),
           "cap": S.CONFIG["MAX_DROP_PCT"]}
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
    print("CEIL_JSON: " + json.dumps(out, ensure_ascii=False))
    return 0


def _live_capacity() -> int:
    """السعةُ الحيّة **من `replay10` نفسِها** التي يستعملها الطفلُ في الحسم —
    لا رقمٌ يدويّ (وهي مربوطةٌ بـ`WATCHLIST_SIZE` بقفل `REPLAY10🔒`)."""
    import replay10 as _rp                                        # noqa: PLC0415
    return int(_rp.CAPACITY)


def validity(res: dict, hits: dict, year: str) -> tuple[bool, list]:
    """§⑤ — خمسةُ شروطٍ تُقرأ **قبل** أيّ تفسير. تُرجع (سليم، أسطر)."""
    order = list(ARMS)                       # الأساس ثم الأوسعُ تدرّجًا
    lines, ok = [], True

    caps = [res[a]["cap"] for a in order]
    c1 = len({round(c, 9) for c in caps}) == len(order)
    lines.append(("V1", c1, "القيمُ النافذة أربعٌ متمايزة: "
                  + " · ".join(f"{a}={res[a]['cap']:.5f}" for a in order)))

    # `V2` **حارسُ الـno-op**: السقفُ الأوسعُ يرفض **أقلّ** ⇒ العدّادُ يتناقص
    #  رتيبًا · **و`C3` (بلا سقف) صفرٌ بالضبط** وإلّا فالعلمُ لم يعمل.
    mono = all(hits[order[i]] >= hits[order[i + 1]] for i in range(len(order) - 1))
    c2 = bool(mono and hits[order[-1]] == 0 and hits[BASE_ARM] > 0)
    lines.append(("V2", c2, "العلمُ فعّال — العدّادُ يتناقص و`C3`=صفر: "
                  + " ≥ ".join(f"{a}={hits[a]}" for a in order)))

    c4 = all(res[a].get("taken") is not None and res[a].get("d50") is not None
             for a in order)
    lines.append(("V4", c4, "المقياسُ الحاكم محسوبٌ لا غائب: "
                  + " · ".join(f"{a}.d50={res[a].get('d50')}" for a in order)))

    sig = [res[a]["signals"] for a in order]
    c5 = all(sig[i] <= sig[i + 1] for i in range(len(sig) - 1))
    lines.append(("V5", c5, "الإشاراتُ رتيبةٌ تصاعديًّا: "
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

    ok, lines = validity(res, hits, year)
    globals()["_LAST_GATE"] = lines        # لإعادةِ الطبع آخرًا
    print("\n🚧 بوّابةُ الصلاحية (‏§⑤ — تُقرأ قبل أيّ تفسير):")
    for tag, good, why in lines:
        print(f"  {tag} {'✅' if good else '⛔'} {why}")
    if not ok:
        print("⛔ **بوّابةُ الصلاحية سقطت ⇒ لا تُفسَّر النتيجة.**")
        return 3

    print(f"\n📊 النتيجة (سعة {_live_capacity()} · rank_live · السنة {year}):")
    base = res[BASE_ARM]
    for arm in ARMS:
        r = res[arm]
        print(f"  {arm:<4}: إشارات={r['signals']:<5} · محسومة={r['decided']:<5} · "
              f"دقة={r['win_rate']}% ({r['wins']}✅/{r['losses']}🛑) · "
              f"مأخوذة={r['taken']:<4} · d50={r['d50']:<3} (d100={r['d100']:<3}) · "
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
    for _t, _o, _w in (_LAST_GATE or []):
        print(f"  {_t} {'✅' if _o else '⛔'} {_w}")
    sys.exit(_rc)
